"""Execute and grade runs: one case, one configuration, one repetition each.

Run folder layout (``<iteration>/<case id>/<config>/run-<n>/``):

- ``before/``, ``after/``: the fixture tree before and after (no ``.git``);
- ``turns/turn-<n>.jsonl``: raw ``opencode run --format json`` events;
- ``messages.json``: the user message of each turn (prompt, then simulated replies);
- ``conversation.md``: readable transcript (messages, tool calls, command output);
- ``changes.json``: created, modified, deleted paths;
- ``final.diff``: code diff against the base commit (``.ndev/`` left out);
- ``metrics.json``: turns, tokens, cost, duration, tool calls, how it ended;
- ``grading.json``: script and judge results (written by ``grade_run``).

Configurations: ``with_skill`` installs the working-tree skills; ``no_skill``
installs none; ``rev-<sha>`` installs every skill under ``skills/`` at a git revision.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import traceback
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from harness.agent import EVALUATOR_AGENT, TurnResult, make_home, run_turn
from harness.cases import SKILLS_DIR, Case
from harness.checks import RunContext, run_checks
from harness.fixtures import copy_tree, diff_trees, materialize
from harness.judge import judge_run

__all__ = ["Config", "Settings", "execute_run", "grade_run", "load_context", "rev_config"]

USER_PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "simulated_user.md").read_text()
DONE = "<<DONE>>"
TMP_ROOT = Path(tempfile.gettempdir()) / "ndev-evals"


@dataclass(frozen=True)
class Config:
    """A configuration: skills (``skills_dir``; ``None``: no skill) and, optionally, the agent model.

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

    @property
    def skills(self) -> list[Path]:
        """Skill folders to install."""
        if self.skills_dir is None:
            return []

        # Any depth: older revisions keep skills at skills/<name>/, newer at skills/ndev/<name>/.
        return sorted(p.parent for p in self.skills_dir.rglob("SKILL.md"))


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
    repo = SKILLS_DIR.parent.parent
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
    tmp = Path(tempfile.mkdtemp(prefix=f"{case.id}-", dir=TMP_ROOT))
    work, home = tmp / "work", tmp / "home"
    turns: list[TurnResult] = []
    messages: list[str] = []
    ended = "error"
    error = ""
    try:
        materialize(case.state, work)
        base = _git(work, "rev-parse", "HEAD").strip()
        copy_tree(work, run_dir / "before")
        make_home(home, config.skills)

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

            reply = _simulated_user(case, messages, turns, tmp, settings)
            if reply is None:
                ended = "done"
                break

            prompt = reply

        copy_tree(work, run_dir / "after")
        _git(work, "add", "-A")
        diff = _git(work, "diff", "--cached", "--no-color", base, "--", ".", ":(exclude).ndev")
        (run_dir / "final.diff").write_text(diff)
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
    if judge_model and (run_dir / "after").is_dir():
        results += judge_run(case, run_dir, judge_model)

    # Fidelity grades the simulated user, not the skill: keep it out of the score.
    graded = [r for r in results if r.passed is not None and r.kind != "fidelity"]
    fidelity = [r.passed for r in results if r.kind == "fidelity"]
    passed = sum(1 for r in graded if r.passed)
    grading = {
        "expectations": [vars(r) for r in results],
        "summary": {
            "passed": passed,
            "failed": len(graded) - passed,
            "total": len(graded),
            "pass_rate": round(passed / len(graded), 4) if graded else 0.0,
            "off_script": None if not fidelity or fidelity[0] is None else not fidelity[0],
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

    return RunContext(
        case=case, config=config_label, before=run_dir / "before", after=run_dir / "after",
        changes=changes, turns=turns, texts=texts,
    )


def _simulated_user(case: Case, messages: list[str], turns: list[TurnResult], tmp: Path, settings: Settings) -> str | None:
    """Ask the user model for the next message; ``None`` when it is done (or fails)."""
    conversation = "\n\n".join(
        f"USER:\n{m}\n\nAGENT:\n{chr(10).join(t.texts) or '(no text)'}" for m, t in zip(messages, turns)
    )
    home, scratch = tmp / "user-home", tmp / "user-scratch"
    if not home.exists():
        make_home(home, [])
        scratch.mkdir()

    turn = run_turn(
        USER_PROMPT.format(script=case.user_script, conversation=conversation),
        workdir=scratch, home=home, model=settings.user_model, agent=EVALUATOR_AGENT, timeout_s=300,
    )
    reply = "\n".join(turn.texts).strip()
    if not turn.ok or not reply or DONE in reply:
        return None

    return reply


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
