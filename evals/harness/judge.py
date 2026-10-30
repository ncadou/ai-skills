"""LLM judge: grade a run against a case's plain-language expectations.

The judge sees the conversation, the changed files, the state artifacts
(``.ndev/`` or ``.nwork/``), and the code diff, and answers in JSON. It runs through the tool-less
``evaluator`` agent, so everything it needs is inlined in the prompt.

In simulated mode the judge also grades ``FIDELITY``: whether the simulated
user kept to its script. That result has kind ``fidelity``; it says whether
the run is a fair test, and never counts toward the skill's pass rate.
"""

from __future__ import annotations

import json
import re
import tempfile
import time
from pathlib import Path

from harness.agent import EVALUATOR_AGENT, make_home, run_turn
from harness.cases import Case
from harness.checks import CheckResult

__all__ = ["FIDELITY", "FORMAT_HELP", "MODE_HELP", "judge_run"]

PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "judge.md").read_text()
MODE_HELP = {
    "gate": "The user gave no approval and delegated nothing, so the agent should stop at its first gate and wait.",
    "delegated": "The user delegated the gates (in the prompt or in brief.md § Control), or the skill has none, "
    "so the agent could finish in one turn.",
    "simulated": "A simulated user answered the agent over several turns, following a script.",
}
# nwork has no phase gates: the working agreement (P1) sets what it may decide.
NWORK_MODE_HELP = {
    **MODE_HELP,
    "gate": "The user's message grants no authority, so the agent should stop where a choice needs the user "
    "(for example, a proposed working agreement) and attribute nothing to the user.",
    "delegated": "The prompt or the working agreement (P1) grants the authority this case needs, so the agent "
    "could finish in one turn.",
}
# Appended to the mode line of the prompt; empty for the ndev phases, so their prompt is unchanged.
FORMAT_HELP = {
    "ndev": "",
    "nwork": (
        "\n\nThe nwork skill has no phases: in one session it investigates, decides, builds, and reviews, as far as "
        "readiness and the working agreement allow. The project state is `.nwork/now.md` (the current view) and "
        "`.nwork/items/` (one record per item, format `nwork/1`); the records are the authority. `Status` and "
        "`Validity` are separate: a slice can stay `implemented` while it `needs-revalidation`. The working "
        "agreement P1 separates focus (presentation only), authority (delegated and reserved choices), and "
        "detail. Attributions read `user (<date>): \"<words>\"`, which must quote the user, or "
        "`agent (delegated: [P1](...) § Authority: <clause>)`, which must rest on a clause the user granted."
    ),
}
FIDELITY = (
    "The simulated user (every USER message after the first) kept to its script: it invented no requirement, "
    "answer, or preference the script does not give, asked for no work the script does not ask for, and approved "
    "or delegated no more than the script allows. Asking the agent to run, start, or proceed to another phase or "
    "skill ('go ahead with ndesign', 'proceed to nplan') is off script unless the script asks for it; agreeing to "
    "the phases a brief lists is not such a request. Neutral replies to questions the script does not cover ('no "
    "preference', 'take your recommendation') are allowed, and so is ending a turn late. Grade the USER messages "
    "only, not the agent."
)
_LIMITS = {"conversation": 60_000, "files": 60_000, "diff": 30_000}


def judge_run(case: Case, run_dir: Path, model: str, timeout_s: int = 300) -> list[CheckResult]:
    """Ask ``model`` to grade ``case.judge`` against the run in ``run_dir``.

    :param case: The case; its ``judge`` list holds the expectations.
    :param run_dir: A finished run folder (see ``harness.runner``).
    :param model: ``provider/model`` id of the judge.
    :param timeout_s: Wall-clock limit per judge call.
    :return: One result per expectation, then the ``fidelity`` result in
        simulated mode. When every attempt fails, every result is unknown
        (``None``, kind kept) with the reason as evidence: an outage is not a
        failed expectation. ``grade --failed-only`` re-grades such runs.
    """
    expected = list(case.judge)
    if case.mode == "simulated":
        expected.append(FIDELITY)

    if not expected:
        return []

    prompt = _prompt(case, run_dir, expected)
    reason = "no answer"
    with tempfile.TemporaryDirectory(prefix="ndev-evals-judge-") as tmp:
        home, scratch = Path(tmp) / "home", Path(tmp) / "scratch"
        make_home(home, [])
        scratch.mkdir()
        for delay in (0, 10, 30, 90):
            time.sleep(delay)
            turn = run_turn(prompt, workdir=scratch, home=home, model=model, agent=EVALUATOR_AGENT, timeout_s=timeout_s)
            if not turn.ok:
                reason = f"judge call failed (exit {turn.returncode}): {turn.stderr[-300:]}"
                continue

            try:
                return _parse("\n".join(turn.texts), expected)
            except ValueError as exc:
                reason = f"unparseable judge answer: {exc}"

    return [CheckResult(text=t, passed=None, evidence=f"judge error: {reason}", kind=_kind(t)) for t in expected]


def _prompt(case: Case, run_dir: Path, expected: list[str]) -> str:
    """Fill the judge template from the run folder."""
    after = run_dir / "after"
    changes = json.loads((run_dir / "changes.json").read_text())
    state = after / case.state_dir
    paths = sorted(p for p in state.rglob("*") if p.is_file()) if state.is_dir() else []
    files = "\n\n".join(f"--- {p.relative_to(after)} ---\n{p.read_text(errors='replace')}" for p in paths)
    diff_path = run_dir / "final.diff"

    return PROMPT.format(
        skill=case.skill,
        description=case.description,
        mode=case.mode,
        mode_help=(NWORK_MODE_HELP if case.bundle == "nwork" else MODE_HELP)[case.mode],
        format_help=FORMAT_HELP[case.bundle],
        script=case.user_script or "(not simulated)",
        conversation=_cap((run_dir / "conversation.md").read_text(), "conversation"),
        changes="\n".join(f"- {k}: {', '.join(v) or 'none'}" for k, v in changes.items()),
        files=_cap(files or f"(no {case.state_dir} files)", "files"),
        diff=_cap(diff_path.read_text() if diff_path.is_file() else "", "diff") or "(no code changes)",
        expectations="\n".join(f"{i}. {t}" for i, t in enumerate(expected, 1)),
    )


def _parse(answer: str, expected: list[str]) -> list[CheckResult]:
    """Parse the judge's JSON; align results with ``expected`` by position.

    :raises ValueError: When no JSON object is found or the count is wrong.
    """
    match = re.search(r"\{.*\}", answer, re.S)
    if not match:
        raise ValueError(f"no JSON object in {answer[:200]!r}")

    try:
        items = json.loads(match[0])["expectations"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError(str(exc)) from exc

    if len(items) != len(expected):
        raise ValueError(f"{len(items)} results for {len(expected)} expectations")

    return [
        CheckResult(
            text=text, passed=bool(item.get("passed")), evidence=str(item.get("evidence", "")), kind=_kind(text)
        )
        for text, item in zip(expected, items)
    ]


def _kind(text: str) -> str:
    """``fidelity`` for the simulator check, ``judge`` for case expectations."""
    return "fidelity" if text == FIDELITY else "judge"


def _cap(text: str, kind: str) -> str:
    """Truncate ``text`` to the limit for ``kind``, keeping head and tail."""
    limit = _LIMITS[kind]
    if len(text) <= limit:
        return text

    half = limit // 2
    return f"{text[:half]}\n\n[... {len(text) - limit} characters cut ...]\n\n{text[-half:]}"
