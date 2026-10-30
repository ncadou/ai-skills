"""Execute and grade runs: one case, one configuration, one repetition each.

Run folder layout (``<iteration>/<case id>/<config>/run-<n>/``):

- ``before/``, ``after/``: the fixture tree before and after (no ``.git``);
- ``turns/turn-<n>.jsonl``: raw ``opencode run --format json`` events;
- ``messages.json``: the user message of each turn (prompt, then simulated replies);
- ``conversation.md``: readable transcript (messages, tool calls, command output);
- ``changes.json``: created, modified, deleted paths;
- ``final.diff``: code diff against the base commit (the state folder left out);
- ``metrics.json``: turns, tokens, cost, duration, tool calls, how it ended;
- ``grading.json``: script and judge results (written by ``grade_run``).

Configurations: ``with_skill`` installs the working-tree skills; ``no_skill``
installs none; ``rev-<sha>`` installs the skills under ``skills/`` at a git
revision. Either way, only the bundle of the case's skill is installed: the
ndev phase skills, or nwork with its references.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time
import traceback
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from harness.agent import EVALUATOR_AGENT, TurnResult, make_home, run_turn
from harness.cases import BUNDLE, SKILLS_ROOT, Case
from harness.checks import RunContext, fidelity_guard, run_checks
from harness.fixtures import copy_tree, diff_trees, materialize
from harness.judge import judge_run

__all__ = [
    "FAILED", "Config", "Settings", "execute_run", "grade_run", "load_context", "rev_config", "simulated_reply",
    "user_prompt",
]

USER_PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "simulated_user.md").read_text()
# The simulated user's rule on staying inside the test, per bundle. ndev tests
# one phase; nwork moves between phases by itself, so only the work is bounded.
SCOPE_RULES = {
    "ndev": (
        "This test covers only the `{skill}` phase. Never ask the agent for work the script does not ask for. "
        "In particular, never ask it to run, start, or proceed to another phase or skill (`nstart`, `nlearn`, "
        "`ndesign`, `nplan`, `nbuild`, `nreview`), unless the script tells you to. When the agent suggests or "
        "names a next phase, that is for later: if the script has nothing left for you to say, reply `<<DONE>>`."
    ),
    "nwork": (
        "This test covers the `{skill}` skill, which investigates, decides, builds, and reviews by itself, within "
        "a working agreement. Never ask the agent for work the script does not ask for, and never ask it to use "
        "another skill (`nstart`, `nlearn`, `ndesign`, `nplan`, `nbuild`, `nreview`). Never change what the agent "
        "may decide (focus, authority, or detail) unless the script tells you to. When the agent proposes a next "
        "action that the script does not cover, that is for later: if the script has nothing left for you to say, "
        "reply `<<DONE>>`."
    ),
}
DONE = "<<DONE>>"
# How a run ends when infrastructure failed; such runs are reruns, not results.
FAILED = ("error", "timeout", "user_error")
RETRY_DELAYS_S = (10, 30, 90)


class SimulatedUserError(RuntimeError):
    """The simulated user model failed on every retry."""
# The agent sees this path: keep it free of case ids and of words like "eval" or "simulated".
TMP_ROOT = Path(tempfile.gettempdir()) / "ndev-work"


@dataclass(frozen=True)
class Config:
    """A configuration: skills (``skills_dir``, a ``skills/`` tree; ``None``: no skill) and, optionally, the agent model.

    ``label`` names the run folder. With several agent models it reads
    ``<skills>@<model>``, for example ``with_skill@glm-5.3-flash``.
    """

    label: str
    skills_dir: Path | None
    model: str | None = None

    @property
    def kind(self) -> str:
        """The skills part of the label: ``with_skill``, ``no_skill``, or ``rev-<sha>``."""
        return self.label.split("@")[0]

    def skills_for(self, skill: str) -> list[Path]:
        """Skill folders to install for a case of ``skill``: every skill of its bundle.

        A whole skill folder is installed, so nwork's ``references/`` comes with it.
        """
        if self.skills_dir is None:
            return []

        bundle = BUNDLE[skill]
        names = {s for s, b in BUNDLE.items() if b == bundle}
        # Older revisions keep the skills at skills/<name>/ or skills/ndev-next/nwork/, newer ones at
        # skills/ndev/<name>/ and skills/nwork/.
        root = self.skills_dir / bundle if (self.skills_dir / bundle).is_dir() else self.skills_dir

        return sorted(p.parent for p in root.rglob("SKILL.md") if p.parent.name in names)


@dataclass(frozen=True)
class Settings:
    """Models and limits shared by every run of an iteration."""

    model: str
    user_model: str
    judge_model: str | None
    timeout_s: int = 1200
    keep_tmp: bool = False


def rev_config(rev: str, cache: Path) -> Config:
    """Extract ``skills/`` at git revision ``rev`` into ``cache`` and return its config.

    :param rev: Any git revision.
    :param cache: Folder to extract into.
    :raises subprocess.CalledProcessError: When the revision or path is unknown.
    """
    repo = SKILLS_ROOT.parent
    sha = subprocess.run(
        ["git", "rev-parse", "--short", rev], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()
    dest = cache / sha
    if not dest.is_dir():
        # Extract beside the target, then rename: a failed extraction leaves no half cache.
        partial = cache / f"{sha}.partial"
        shutil.rmtree(partial, ignore_errors=True)
        partial.mkdir(parents=True)
        archive = subprocess.run(
            ["git", "archive", sha, "skills"], cwd=repo, check=True, capture_output=True
        ).stdout
        subprocess.run(["tar", "-x", "-C", str(partial)], input=archive, check=True)
        partial.rename(dest)

    return Config(label=f"rev-{sha}", skills_dir=dest / "skills")


def execute_run(case: Case, config: Config, run_dir: Path, settings: Settings) -> dict:
    """Run ``case`` once under ``config`` and write the run folder.

    :param case: Case to run.
    :param config: Skill configuration.
    :param run_dir: Output folder; created, must not hold ``metrics.json``.
    :param settings: Models and limits.
    :return: The metrics written to ``metrics.json``.
    """
    run_dir.mkdir(parents=True, exist_ok=True)
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="run-", dir=TMP_ROOT))
    work, home = tmp / "work", tmp / "home"
    turns: list[TurnResult] = []
    messages: list[str] = []
    user_log: list[str] = []
    ended = "error"
    error = ""
    try:
        materialize(case.state, work)
        base = _git(work, "rev-parse", "HEAD").strip()
        copy_tree(work, run_dir / "before")
        make_home(home, config.skills_for(case.skill))

        prompt, session = case.prompt, None
        for number in range(1, case.max_turns + 1):
            messages.append(prompt)
            turn = run_turn(prompt, workdir=work, home=home, model=config.model or settings.model,
                            session_id=session, timeout_s=settings.timeout_s)
            turns.append(turn)
            _write_turn(run_dir, number, turn)
            if not turn.ok:
                ended = "timeout" if turn.timed_out else "error"
                error = turn.stderr[-2000:]
                break

            session = turn.session_id
            if case.mode != "simulated":
                ended = "single"
                break

            if number == case.max_turns:
                ended = "max_turns"
                break

            reply = simulated_reply(case, messages, [t.texts for t in turns], tmp, settings.user_model)
            user_log.append(reply)
            if reply == DONE:
                ended = "done"
                break

            prompt = reply

        copy_tree(work, run_dir / "after")
        _git(work, "add", "-A")
        diff = _git(work, "diff", "--cached", "--no-color", base, "--", ".", f":(exclude){case.state_dir}")
        (run_dir / "final.diff").write_text(diff)
    except SimulatedUserError as exc:
        ended, error = "user_error", str(exc)
    except Exception:  # noqa: BLE001 - record the failure, keep the iteration going
        error = traceback.format_exc()
    finally:
        if not settings.keep_tmp:
            shutil.rmtree(tmp, ignore_errors=True)

    changes = diff_trees(run_dir / "before", run_dir / "after")
    (run_dir / "changes.json").write_text(json.dumps(changes, indent=2))
    (run_dir / "messages.json").write_text(json.dumps(messages, indent=2, ensure_ascii=False))
    (run_dir / "conversation.md").write_text(_conversation(messages, [t.events for t in turns], ended))
    tools = Counter(
        e["part"].get("tool") for t in turns for e in t.events if e.get("type") == "tool_use"
    )
    metrics = {
        "case": case.id,
        "skill": case.skill,
        "config": config.label,
        "model": config.model or settings.model,
        "ended": ended,
        "turns": len(turns),
        "user_replies": user_log,
        "tokens": sum(t.tokens for t in turns),
        "cost": round(sum(t.cost for t in turns), 4),
        "duration_s": round(sum(t.duration_s for t in turns), 1),
        "tool_calls": dict(tools),
        "error": error,
        "tmp": str(tmp) if settings.keep_tmp else None,
    }
    (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))

    return metrics


def grade_run(case: Case, config_label: str, run_dir: Path, judge_model: str | None) -> dict:
    """Grade a finished run and write ``grading.json``.

    :param case: The case that ran.
    :param config_label: Configuration label (``with_skill``, ``no_skill``, ``rev-<sha>``).
    :param run_dir: The run folder.
    :param judge_model: Judge model id; ``None`` skips the judge.
    :return: The grading written to ``grading.json``.
    """
    ctx = load_context(case, config_label, run_dir)
    messages_path = run_dir / "messages.json"
    if messages_path.is_file():
        # Re-render, so transcript fixes apply to old runs on re-grade.
        messages = json.loads(messages_path.read_text())
        ended = json.loads((run_dir / "metrics.json").read_text()).get("ended", "")
        (run_dir / "conversation.md").write_text(_conversation(messages, ctx.turns, ended))

    results = run_checks(ctx)
    if case.mode == "simulated":
        results.append(fidelity_guard(ctx))
    if judge_model and (run_dir / "after").is_dir():
        results += judge_run(case, run_dir, judge_model)

    # Fidelity grades the simulated user, not the skill: keep it out of the score.
    # Off script when any fidelity result failed; unknown when one is missing.
    graded = [r for r in results if r.passed is not None and r.kind != "fidelity"]
    fidelity = [r.passed for r in results if r.kind == "fidelity"]
    off_script = True if False in fidelity else None if None in fidelity else False
    passed = sum(1 for r in graded if r.passed)
    grading = {
        "expectations": [vars(r) for r in results],
        "summary": {
            "passed": passed,
            "failed": len(graded) - passed,
            "total": len(graded),
            "pass_rate": round(passed / len(graded), 4) if graded else 0.0,
            "off_script": off_script,
            "judge_error": any(r.evidence.startswith("judge error:") for r in results),
        },
    }
    (run_dir / "grading.json").write_text(json.dumps(grading, indent=2, ensure_ascii=False))

    return grading


def load_context(case: Case, config_label: str, run_dir: Path) -> RunContext:
    """Rebuild the check context of a finished run from its folder."""
    turns = []
    for path in sorted((run_dir / "turns").glob("turn-*.jsonl"), key=lambda p: int(p.stem.split("-")[1])):
        turns.append([json.loads(line) for line in path.read_text().splitlines() if line.strip()])

    texts = []
    for events in turns:
        parts = [e["part"]["text"] for e in events if e.get("type") == "text" and e.get("part", {}).get("text")]
        texts.append(parts[-1] if parts else "")

    changes = diff_trees(run_dir / "before", run_dir / "after")
    messages_path = run_dir / "messages.json"
    messages = json.loads(messages_path.read_text()) if messages_path.is_file() else []

    return RunContext(
        case=case, config=config_label, before=run_dir / "before", after=run_dir / "after",
        changes=changes, turns=turns, texts=texts, messages=messages,
    )


def simulated_reply(case: Case, messages: list[str], texts: list[list[str]], tmp: Path, model: str) -> str:
    """Ask the user model for its next message, retrying on failure.

    :param case: The case; its ``user_script`` drives the reply.
    :param messages: User messages so far, one per agent turn.
    :param texts: Agent text parts, one list per turn.
    :param tmp: Scratch folder for the user model's isolated home.
    :param model: User model id.
    :return: The reply, or exactly ``DONE`` when the user is done.
    :raises SimulatedUserError: When every attempt fails or answers nothing. A
        failed call must never pass for ``DONE``: that would end the run early
        and blame the skill for it.
    """
    conversation = "\n\n".join(
        f"USER:\n{m}\n\nAGENT:\n{chr(10).join(t) or '(no text)'}" for m, t in zip(messages, texts)
    )
    home, scratch = tmp / "user-home", tmp / "user-scratch"
    if not home.exists():
        make_home(home, [])
        scratch.mkdir()

    last = ""
    for delay in (0, *RETRY_DELAYS_S):
        time.sleep(delay)
        turn = run_turn(
            user_prompt(case, conversation),
            workdir=scratch, home=home, model=model, agent=EVALUATOR_AGENT, timeout_s=180,
        )
        reply = "\n".join(turn.texts).strip()
        if turn.ok and reply:
            return DONE if DONE in reply else reply

        last = f"exit {turn.returncode}, timed out {turn.timed_out}: {turn.stderr[-300:]}"

    raise SimulatedUserError(f"simulated user failed {1 + len(RETRY_DELAYS_S)} times; last: {last}")


def user_prompt(case: Case, conversation: str) -> str:
    """Fill the simulated-user template for ``case``, with its bundle's scope rule.

    :param case: The case; its ``user_script`` drives the reply.
    :param conversation: The conversation so far, rendered as text.
    :return: The prompt for the user model.
    """
    return USER_PROMPT.format(
        skill=case.skill,
        script=case.user_script,
        conversation=conversation,
        scope_rule=SCOPE_RULES[case.bundle].format(skill=case.skill),
    )


def _write_turn(run_dir: Path, number: int, turn: TurnResult) -> None:
    """Save the raw events of one turn."""
    folder = run_dir / "turns"
    folder.mkdir(exist_ok=True)
    (folder / f"turn-{number}.jsonl").write_text("".join(json.dumps(e) + "\n" for e in turn.events))


def _conversation(messages: list[str], turns: list[list[dict]], ended: str) -> str:
    """Render messages, texts, tool calls, and command output as Markdown.

    :param ended: How the run ended (see ``metrics.json``); ``done`` adds the
        simulated user's final ``<<DONE>>``, which never reaches the agent.
    """
    out = []
    for number, (message, events) in enumerate(zip(messages, turns), 1):
        out.append(f"## Turn {number}\n\n### User\n\n{message}\n\n### Agent\n")
        for event in events:
            part = event.get("part") or {}
            if event.get("type") == "text" and part.get("text"):
                out.append(part["text"] + "\n")
            elif event.get("type") == "tool_use":
                state = part.get("state") or {}
                status = "" if state.get("status") == "completed" else f" [{state.get('status')}]"
                out.append(f"- tool `{part.get('tool')}`{status}: {_tool_summary(state.get('input') or {})}")
                # Command output is evidence (test runs, spikes); file reads are not.
                if part.get("tool") == "bash" and state.get("output"):
                    output = str(state["output"]).rstrip()
                    if len(output) > 1500:
                        output = f"[... {len(output) - 1500} characters cut ...]\n{output[-1500:]}"
                    out.append("\n  ```text\n" + "\n".join(f"  {line}" for line in output.splitlines()) + "\n  ```\n")

        out.append("")

    if ended == "done":
        out.append(f"## End\n\n### User\n\n{DONE}\n\n(The simulated user ended the run; the agent never saw this.)\n")
    elif ended == "user_error":
        out.append("## End\n\n(The simulated user model failed; the run is incomplete and must be rerun.)\n")
    elif ended == "max_turns":
        out.append("## End\n\n(The run stopped at max_turns before the simulated user ended it.)\n")

    return "\n".join(out)


def _tool_summary(args: dict) -> str:
    """One line describing a tool call's input."""
    for key in ("command", "filePath", "name", "pattern", "url", "description"):
        if key in args:
            return f"{key}={str(args[key])[:200]!r}"

    return json.dumps(args)[:200]


def _git(work: Path, *args: str) -> str:
    """Run git in ``work`` and return stdout."""
    return subprocess.run(
        ["git", "-c", "core.quotepath=false", *args], cwd=work, check=True, capture_output=True, text=True
    ).stdout
