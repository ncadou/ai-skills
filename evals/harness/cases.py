"""Load and validate eval cases from ``evals/ndev/<skill>/evals.json``.

Two workflow formats are under test, each a bundle folder under ``skills/``:

- ``ndev``: the six phase skills (``PHASES``), with ``.ndev/brief.md`` and
  the other phase artifacts;
- ``ndev-next``: the experimental ``nwork`` skill, with ``.ndev/now.md`` and
  ``.ndev/items/`` (format ``ndev-next/1``).

``BUNDLE`` maps each skill to its bundle. A run installs only the bundle of
its case's skill, since a project uses one format at a time.

File format::

    {
      "skill": "nbuild",
      "cases": [
        {
          "id": "nbuild-happy",               # unique across all skills
          "description": "What this case tests.",
          "state": "planned",                  # fixtures/states/<state>
          "mode": "delegated",                 # gate | delegated | simulated
          "prompt": "Use the nbuild skill on task-01-slugify.",
          "allow": [".ndev/tasks/task-01-*.md"],   # extra writable globs
          "checks": [{"check": "field", "file": "...", "name": "Status", "value": "done"}],
          "judge": ["Plain-language expectation for the LLM judge."],
          "tags": ["messy"],                   # optional, for --tag filters
          "user_script": "simulated mode only: how the user answers",
          "max_turns": 8                       # simulated mode only
        }
      ]
    }

Modes:

- ``gate``: one turn, no delegation. The skill must stop at its first gate
  and record no approval.
- ``delegated``: one turn; the prompt or ``brief.md`` § Control delegates the
  gates (or the skill has none). Approvals must name the delegation.
- ``simulated``: several turns; a simulated user answers from ``user_script``.

For ``nwork``, which has no phase gates, ``gate`` means that the prompt grants
no authority, so the agent must stop where a choice needs the user, and
``delegated`` means that the prompt or the working agreement grants what the
case needs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from harness.fixtures import list_states

__all__ = [
    "BUNDLE",
    "CASES_DIR",
    "MODES",
    "NWORK",
    "PHASES",
    "SKILLS",
    "SKILLS_ROOT",
    "SKILL_DIRS",
    "WRITABLE",
    "Case",
    "load_cases",
]

EVALS_DIR = Path(__file__).resolve().parent.parent
CASES_DIR = EVALS_DIR / "ndev"
SKILLS_ROOT = EVALS_DIR.parent / "skills"
PHASES = ("nstart", "nlearn", "ndesign", "nplan", "nbuild", "nreview")
NWORK = "nwork"
SKILLS = (*PHASES, NWORK)
BUNDLE = {**dict.fromkeys(PHASES, "ndev"), NWORK: "ndev-next"}
SKILL_DIRS = {skill: SKILLS_ROOT / BUNDLE[skill] / skill for skill in SKILLS}
MODES = ("gate", "delegated", "simulated")

# What each skill may write, from its "Produce only ..." line. Cases add to it
# with "allow" (for example the one task file nbuild may edit). nwork does
# every phase's work, so it may write its records and the code.
WRITABLE: dict[str, tuple[str, ...]] = {
    "nstart": (".ndev/brief.md", ".ndev/questions.md"),
    "nlearn": (".ndev/discovery.md", ".ndev/questions.md", ".ndev/scratch/*"),
    "ndesign": (".ndev/design.md", ".ndev/questions.md"),
    "nplan": (".ndev/plan.md", ".ndev/tasks/*", ".ndev/questions.md"),
    "nbuild": ("textkit/*", "tests/*", "README.md", ".ndev/questions.md"),
    "nreview": (".ndev/questions.md",),
    NWORK: (".ndev/now.md", ".ndev/items/*", "textkit/*", "tests/*", "README.md"),
}


@dataclass
class Case:
    """One eval case; see the module docstring for the fields."""

    id: str
    skill: str
    description: str
    state: str
    mode: str
    prompt: str
    allow: list[str] = field(default_factory=list)
    checks: list[dict] = field(default_factory=list)
    judge: list[str] = field(default_factory=list)
    user_script: str = ""
    max_turns: int = 1
    tags: list[str] = field(default_factory=list)

    @property
    def bundle(self) -> str:
        """The skill's bundle, which is also its workflow format: ``ndev`` or ``ndev-next``."""
        return BUNDLE[self.skill]

    @property
    def writable(self) -> tuple[str, ...]:
        """Globs this case may write: the skill's defaults plus ``allow``."""
        return WRITABLE[self.skill] + tuple(self.allow)


def load_cases(
    skills: list[str] | None = None, ids: list[str] | None = None, tags: list[str] | None = None
) -> list[Case]:
    """Load, validate, and filter every case.

    :param skills: Keep only these skills; ``None`` keeps all.
    :param ids: Keep only these case ids; ``None`` keeps all.
    :param tags: Keep only cases with at least one of these tags; ``None`` keeps all.
    :return: Cases in skill order, then file order.
    :raises ValueError: When a case is invalid, or a filter matches nothing.
    """
    states = set(list_states())
    cases: list[Case] = []
    for skill in SKILLS:
        path = CASES_DIR / skill / "evals.json"
        if not path.is_file():
            continue

        data = json.loads(path.read_text())
        if data.get("skill") != skill:
            raise ValueError(f"{path}: skill must be {skill!r}")

        for raw in data["cases"]:
            case = Case(skill=skill, **raw)
            _validate(case, states, path)
            cases.append(case)

    seen: set[str] = set()
    for case in cases:
        if case.id in seen:
            raise ValueError(f"duplicate case id {case.id!r}")

        seen.add(case.id)

    selected = [
        c
        for c in cases
        if (skills is None or c.skill in skills)
        and (ids is None or c.id in ids)
        and (tags is None or set(tags) & set(c.tags))
    ]
    if not selected:
        raise ValueError(f"no case matches skills={skills} ids={ids} tags={tags}")

    return selected


def _validate(case: Case, states: set[str], path: Path) -> None:
    """Raise ``ValueError`` when ``case`` is inconsistent."""
    where = f"{path}: case {case.id!r}"
    if case.state not in states:
        raise ValueError(f"{where}: unknown state {case.state!r}")

    if case.mode not in MODES:
        raise ValueError(f"{where}: mode must be one of {MODES}")

    if case.mode == "simulated":
        if not case.user_script or case.max_turns < 2:
            raise ValueError(f"{where}: simulated mode needs user_script and max_turns >= 2")
    elif case.max_turns != 1 or case.user_script:
        raise ValueError(f"{where}: only simulated mode takes user_script and max_turns")

    from harness.checks import CHECKS  # late import: checks imports this module

    for check in case.checks:
        if check.get("check") not in CHECKS:
            raise ValueError(f"{where}: unknown check {check.get('check')!r}")
