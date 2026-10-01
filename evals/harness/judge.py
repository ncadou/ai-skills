"""LLM judge: grade a run against a case's plain-language expectations.

The judge sees the conversation, the changed files, the ``.ndev/`` artifacts,
and the code diff, and answers in JSON. It runs through the tool-less
``evaluator`` agent, so everything it needs is inlined in the prompt.

In simulated mode the judge also grades ``FIDELITY``: whether the simulated
user kept to its script. That result has kind ``fidelity``; it says whether
the run is a fair test, and never counts toward the skill's pass rate.
"""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

from harness.agent import EVALUATOR_AGENT, make_home, run_turn
from harness.cases import Case
from harness.checks import CheckResult

__all__ = ["FIDELITY", "MODE_HELP", "judge_run"]

PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "judge.md").read_text()
MODE_HELP = {
    "gate": "The user gave no approval and delegated nothing, so the agent should stop at its first gate and wait.",
    "delegated": "The user delegated the gates (in the prompt or in brief.md § Control), or the skill has none, "
    "so the agent could finish in one turn.",
    "simulated": "A simulated user answered the agent over several turns, following a script.",
}
FIDELITY = (
    "The simulated user (every USER message after the first) kept to its script: it invented no requirement, "
    "answer, or preference the script does not give, asked for no work the script does not ask for, and approved "
    "or delegated no more than the script allows. Neutral replies to questions the script does not cover ('no "
    "preference', 'take your recommendation') are allowed, and so is ending a turn late. Grade the USER messages "
    "only, not the agent."
)
_LIMITS = {"conversation": 60_000, "files": 60_000, "diff": 30_000}


def judge_run(case: Case, run_dir: Path, model: str, timeout_s: int = 600) -> list[CheckResult]:
    """Ask ``model`` to grade ``case.judge`` against the run in ``run_dir``.

    :param case: The case; its ``judge`` list holds the expectations.
    :param run_dir: A finished run folder (see ``harness.runner``).
    :param model: ``provider/model`` id of the judge.
    :param timeout_s: Wall-clock limit per judge call.
    :return: One result per expectation, then the ``fidelity`` result in
        simulated mode. When the judge fails twice, every expectation fails
        with the reason as evidence, and fidelity is unknown (``None``).
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
        for _ in range(2):
            turn = run_turn(prompt, workdir=scratch, home=home, model=model, agent=EVALUATOR_AGENT, timeout_s=timeout_s)
            if not turn.ok:
                reason = f"judge call failed (exit {turn.returncode}): {turn.stderr[-300:]}"
                continue

            try:
                return _parse("\n".join(turn.texts), expected)
            except ValueError as exc:
                reason = f"unparseable judge answer: {exc}"

    return [
        CheckResult(text=t, passed=None if t == FIDELITY else False, evidence=reason, kind=_kind(t))
        for t in expected
    ]


def _prompt(case: Case, run_dir: Path, expected: list[str]) -> str:
    """Fill the judge template from the run folder."""
    after = run_dir / "after"
    changes = json.loads((run_dir / "changes.json").read_text())
    ndev = sorted(p for p in (after / ".ndev").rglob("*") if p.is_file()) if (after / ".ndev").is_dir() else []
    files = "\n\n".join(f"--- {p.relative_to(after)} ---\n{p.read_text(errors='replace')}" for p in ndev)
    diff_path = run_dir / "final.diff"

    return PROMPT.format(
        skill=case.skill,
        description=case.description,
        mode=case.mode,
        mode_help=MODE_HELP[case.mode],
        script=case.user_script or "(not simulated)",
        conversation=_cap((run_dir / "conversation.md").read_text(), "conversation"),
        changes="\n".join(f"- {k}: {', '.join(v) or 'none'}" for k, v in changes.items()),
        files=_cap(files or "(no .ndev files)", "files"),
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
