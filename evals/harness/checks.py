"""Deterministic checks on one run: artifacts, ledger, approvals, files touched.

Each check takes a ``RunContext`` plus its parameters from ``evals.json`` and
returns ``(passed, evidence)``. ``passed`` is ``None`` when the check does not
apply (for example ``skill_loaded`` in a no-skill baseline); such results are
left out of the pass rate.

Every case gets ``DEFAULT_CHECKS`` first; its own ``checks`` follow.
"""

from __future__ import annotations

import fnmatch
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from harness.cases import SKILLS, SKILLS_DIR, Case
from harness.fixtures import HIDDEN, Changes

__all__ = [
    "CHECKS",
    "DEFAULT_CHECKS",
    "CheckResult",
    "RunContext",
    "approval_values",
    "id_definitions",
    "run_checks",
    "template_patterns",
]

Result = tuple[bool | None, str]

PHASES = "|".join(SKILLS)
QUESTION_LINE = re.compile(
    rf"^- \[(?P<tick>[ x])\] (?P<id>Q\d+): (?P<text>.+?) "
    rf"\(from (?P<src>{PHASES})/(?P<who>user|agent), for (?P<for>{PHASES}|user)\)"
    rf"(?P<stale> stale: .+?)?(?P<answer> → .+)?$"
)
# Lines that define an ID, per artifact kind.
ID_DEFINITIONS = {
    "brief.md": re.compile(r"^- (O\d+):", re.M),
    "questions.md": re.compile(r"^- \[[ x]\] (Q\d+):", re.M),
    "discovery.md": re.compile(r"^### (F\d+):", re.M),
    "design.md": re.compile(r"^### (D\d+):", re.M),
}
TASK_ID = re.compile(r"^# (T\d+):", re.M)
TASK_FILE = re.compile(r"task-(\d+)-[^/]+\.md$")
APPROVAL = re.compile(r"(?i)\b(approved|decided by|accepted by):[ \t]*(.*)$", re.M)
VALID_APPROVAL = re.compile(r"^(user|agent \(delegated: [^)]+\))$")
INLINE_CODE = re.compile(r"`[^`\n]*`")
NOT_YET = re.compile(r"(?i)^(pending|none|not yet|n/a|tbd|—|-)(\W|$)")
DEFAULT_CHECKS = (
    {"check": "skill_loaded"},
    {"check": "only_touched"},
    {"check": "approvals"},
    {"check": "questions_format"},
    {"check": "ids_unique"},
    {"check": "ids_preserved"},
)


@dataclass
class RunContext:
    """Everything a check may look at for one finished run."""

    case: Case
    config: str
    before: Path
    after: Path
    changes: Changes
    turns: list[list[dict]] = field(default_factory=list)
    texts: list[str] = field(default_factory=list)

    def read(self, rel: str, *, before: bool = False) -> str | None:
        """Return the text of ``rel`` after (or before) the run, or ``None`` when absent."""
        path = (self.before if before else self.after) / rel
        return path.read_text(errors="replace") if path.is_file() else None

    def glob(self, pattern: str, *, before: bool = False) -> list[str]:
        """Relative paths of files matching ``pattern`` after (or before) the run."""
        root = self.before if before else self.after
        return sorted(p.relative_to(root).as_posix() for p in root.glob(pattern) if p.is_file())


@dataclass
class CheckResult:
    """One graded expectation, in the ``grading.json`` shape."""

    text: str
    passed: bool | None
    evidence: str
    kind: str = "script"


def run_checks(ctx: RunContext) -> list[CheckResult]:
    """Run the default checks, then the case's own checks.

    :param ctx: The finished run.
    :return: One result per check, in order.
    """
    results = []
    for spec in (*DEFAULT_CHECKS, *ctx.case.checks):
        params = {k: v for k, v in spec.items() if k not in ("check", "label")}
        fn, label = CHECKS[spec["check"]]
        text = spec.get("label") or label.format(**{"case": ctx.case, **params})
        try:
            passed, evidence = fn(ctx, **params)
        except Exception as exc:  # noqa: BLE001 - a broken check must not stop grading
            passed, evidence = False, f"check crashed: {exc!r}"

        results.append(CheckResult(text=text, passed=passed, evidence=evidence))

    return results


CHECKS: dict[str, tuple[Callable[..., Result], str]] = {}


def _check(name: str, label: str) -> Callable[[Callable[..., Result]], Callable[..., Result]]:
    """Register a check under ``name``; ``label`` is formatted with its parameters."""

    def register(fn: Callable[..., Result]) -> Callable[..., Result]:
        CHECKS[name] = (fn, label)
        return fn

    return register


# Default checks


@_check("skill_loaded", "The agent loaded the {case.skill} skill with the skill tool")
def _skill_loaded(ctx: RunContext) -> Result:
    """Pass when a ``skill`` tool call named the case's skill."""
    if ctx.config.split("@")[0] == "no_skill":
        return None, "not applicable: no skill installed"

    names = [
        (e["part"].get("state") or {}).get("input", {}).get("name")
        for turn in ctx.turns
        for e in turn
        if e.get("type") == "tool_use" and e.get("part", {}).get("tool") == "skill"
    ]
    return ctx.case.skill in names, f"skill tool calls: {names or 'none'}"


@_check("only_touched", "Only allowed files changed ({case.skill}: produce only its artifacts)")
def _only_touched(ctx: RunContext, allow: list[str] | None = None) -> Result:
    """Pass when every changed path matches the case's writable globs (plus ``allow``)."""
    globs = ctx.case.writable + tuple(allow or ())
    bad = [p for p in ctx.changes.all if not any(fnmatch.fnmatch(p, g) for g in globs)]
    if bad:
        return False, f"outside {list(globs)}: {bad}"

    return True, f"changed: {ctx.changes.all or 'nothing'}"


@_check("approvals", "Approval, decision, and acceptance lines are truthful for {case.mode} mode")
def _approvals(ctx: RunContext) -> Result:
    """Check new ``Approved:``/``Decided by:``/``Accepted by:`` lines against the mode.

    - gate: no new line at all, since nobody approved anything;
    - delegated: only ``agent (delegated: <scope>)``, since the user never answered;
    - simulated: ``user`` or ``agent (delegated: <scope>)``.
    """
    new = []
    for rel in ctx.glob(".ndev/**/*.md"):
        before = Counter(approval_values(ctx.read(rel, before=True) or ""))
        after = Counter(approval_values(ctx.read(rel) or ""))
        new += [(rel, marker, value) for (marker, value) in (after - before).elements()]

    problems = []
    for rel, marker, value in new:
        if ctx.case.mode == "gate":
            problems.append(f"{rel}: '{marker}: {value}' written without any user turn")
        elif not VALID_APPROVAL.match(value):
            problems.append(f"{rel}: '{marker}: {value}' is not 'user' or 'agent (delegated: <scope>)'")
        elif ctx.case.mode == "delegated" and value == "user":
            problems.append(f"{rel}: '{marker}: user' but the user never answered")

    if problems:
        return False, "; ".join(problems)

    return True, f"{len(new)} new line(s): {[f'{m}: {v}' for _, m, v in new] or 'none'}"


@_check("questions_format", "Every questions.md entry follows the ledger format")
def _questions_format(ctx: RunContext) -> Result:
    """Pass when every ``- [`` line in questions.md parses, and ticked ones point to an answer."""
    text = ctx.read(".ndev/questions.md")
    if text is None:
        return None, "no questions.md"

    bad = []
    for line in text.splitlines():
        if not line.startswith("- ["):
            continue

        match = QUESTION_LINE.match(line)
        if not match:
            bad.append(line)
        elif match["tick"] == "x" and not match["answer"]:
            bad.append(f"{line}  (ticked without '→ <answer>')")

    return not bad, "; ".join(bad) if bad else "all entries parse"


@_check("ids_unique", "IDs are well formed and never defined twice")
def _ids_unique(ctx: RunContext) -> Result:
    """Pass when no artifact defines an ID twice, and each task file's ID matches its number."""
    problems = []
    for rel, ids in id_definitions(ctx.after).items():
        dupes = [i for i, n in Counter(ids).items() if n > 1]
        if dupes:
            problems.append(f"{rel}: {dupes} defined twice")

    for rel in ctx.glob(".ndev/tasks/*.md"):
        number = TASK_FILE.search(rel)
        ids = TASK_ID.findall(ctx.read(rel) or "")
        if number and ids != [f"T{int(number[1]):02d}"]:
            problems.append(f"{rel}: title ids {ids}, expected T{int(number[1]):02d}")

    return not problems, "; ".join(problems) if problems else "ok"


@_check("ids_preserved", "No ID defined before the run was deleted")
def _ids_preserved(ctx: RunContext) -> Result:
    """Pass when every ID defined before the run is still defined after it."""
    before = {i for ids in id_definitions(ctx.before).values() for i in ids}
    after = {i for ids in id_definitions(ctx.after).values() for i in ids}
    missing = sorted(before - after)

    return not missing, f"missing: {missing}" if missing else f"{len(before)} kept"


# Case checks


@_check("file_exists", "{path} exists")
def _file_exists(ctx: RunContext, path: str) -> Result:
    """Pass when at least one file matches glob ``path``."""
    found = ctx.glob(path)
    return bool(found), f"found: {found or 'none'}"


@_check("file_absent", "{path} does not exist")
def _file_absent(ctx: RunContext, path: str) -> Result:
    """Pass when no file matches glob ``path``."""
    found = ctx.glob(path)
    return not found, f"found: {found}" if found else "absent"


@_check("unchanged", "Unchanged: {paths}")
def _unchanged(ctx: RunContext, paths: list[str]) -> Result:
    """Pass when no changed path matches any of the globs in ``paths``."""
    hit = [p for p in ctx.changes.all if any(fnmatch.fnmatch(p, g) for g in paths)]
    return not hit, f"changed: {hit}" if hit else "unchanged"


@_check("contains", "{file} matches /{pattern}/")
def _contains(ctx: RunContext, file: str, pattern: str, min: int = 1) -> Result:
    """Pass when every file matching glob ``file`` has at least ``min`` matches of ``pattern``."""
    return _count_matches(ctx, file, pattern, minimum=min, maximum=None)


@_check("not_contains", "{file} does not match /{pattern}/")
def _not_contains(ctx: RunContext, file: str, pattern: str) -> Result:
    """Pass when no file matching glob ``file`` matches ``pattern`` (absent files pass)."""
    files = ctx.glob(file)
    hits = [f for f in files if re.search(pattern, ctx.read(f) or "", re.M)]
    return not hits, f"matched in {hits}" if hits else f"no match in {files or 'no files'}"


@_check("field", "{file}: {name} is {value}")
def _field(ctx: RunContext, file: str, name: str, value: str) -> Result:
    """Pass when the ``<name>: <value>`` line of ``file`` holds ``value`` (first word)."""
    text = ctx.read(file)
    if text is None:
        return False, f"{file} missing"

    match = re.search(rf"^{re.escape(name)}:[ \t]*(\S*)", text, re.M)
    got = match[1] if match else None

    return got == value, f"{name}: {got!r}"


@_check("template_headings", "{file} has every heading of the {template}")
def _template_headings(ctx: RunContext, file: str, template: str, skill: str | None = None) -> Result:
    """Pass when every file matching ``file`` has every heading of a SKILL.md template.

    The template comes from the working-tree skill (the spec), not the version
    under test, so every configuration is graded against the same standard.
    """
    patterns = template_patterns((SKILLS_DIR / (skill or ctx.case.skill) / "SKILL.md").read_text(), template)
    files = ctx.glob(file)
    if not files:
        return False, f"no file matches {file}"

    missing = []
    for rel in files:
        text = ctx.read(rel) or ""
        missing += [f"{rel}: {p.pattern}" for p in patterns if not p.search(text)]

    return not missing, f"missing: {missing}" if missing else f"{len(patterns)} headings in {files}"


@_check("approvals_min", "{file} has at least {count} 'Approved: {value}' line(s)")
def _approvals_min(ctx: RunContext, file: str, count: int, value: str = "any") -> Result:
    """Pass when ``file`` has ``count`` or more ``Approved:`` lines of kind ``value``.

    :param value: ``user``, ``agent`` (any delegation), or ``any``.
    """
    values = [v for m, v in approval_values(ctx.read(file) or "") if m == "approved"]
    kept = [v for v in values if value == "any" or v.split(" ")[0] == value]

    return len(kept) >= count, f"Approved values: {values}"


@_check("question_added", "A new open question for {for_phase} was added to questions.md")
def _question_added(ctx: RunContext, for_phase: str, stale: bool = False) -> Result:
    """Pass when questions.md gained an open question from this skill, for ``for_phase``.

    :param stale: Also require a ``stale:`` list on it.
    """
    old_ids = {m["id"] for m in _questions(ctx.read(".ndev/questions.md", before=True))}
    new = [m for m in _questions(ctx.read(".ndev/questions.md")) if m["id"] not in old_ids]
    hits = [
        m.group(0)
        for m in new
        if m["tick"] == " " and m["for"] == for_phase and m["src"] == ctx.case.skill and (m["stale"] or not stale)
    ]
    return bool(hits), f"matching: {hits}" if hits else f"new questions: {[m.group(0) for m in new] or 'none'}"


@_check("questions_ticked", "{ids} are ticked and point to an answer")
def _questions_ticked(ctx: RunContext, ids: list[str], answer: str = r"\S") -> Result:
    """Pass when every question in ``ids`` is ticked and its ``→`` answer matches ``answer``."""
    found = {m["id"]: m for m in _questions(ctx.read(".ndev/questions.md"))}
    bad = [
        i
        for i in ids
        if i not in found or found[i]["tick"] != "x" or not re.search(answer, found[i]["answer"] or "")
    ]
    return not bad, f"not ticked with a matching answer: {bad}" if bad else "all ticked"


@_check("final_asks", "The last message hands a question back to the user")
def _final_asks(ctx: RunContext) -> Result:
    """Pass when the last assistant text of the last turn contains a question mark."""
    last = ctx.texts[-1] if ctx.texts else ""
    return "?" in last, f"last message ends: {last[-300:]!r}"


@_check("command_passes", "`{cmd}` exits {expect} on the final tree")
def _command_passes(ctx: RunContext, cmd: str, expect: int = 0, timeout: int = 120) -> Result:
    """Run ``cmd`` in a copy of the final tree and compare its exit code with ``expect``.

    ``{hidden}`` in ``cmd`` expands to the hidden fixtures folder.
    """
    with tempfile.TemporaryDirectory(prefix="ndev-evals-cmd-") as tmp:
        work = Path(tmp) / "work"
        shutil.copytree(ctx.after, work)
        proc = subprocess.run(
            cmd.format(hidden=HIDDEN),
            shell=True,
            cwd=work,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    output = (proc.stdout + proc.stderr).strip()
    return proc.returncode == expect, f"exit {proc.returncode}: {output[-600:]}"


# Parsing helpers, public for the tests


def approval_values(text: str) -> list[tuple[str, str]]:
    """Return ``(marker, value)`` for every approval claim in ``text``.

    Empty and not-yet values (``pending``, ``none``, ...) are not claims, and
    markers quoted in inline code are ignored.

    ``marker`` is lowercased (``approved``, ``decided by``, ``accepted by``).
    ``value`` is ``user``, ``agent (delegated: ...)`` with its parentheses
    balanced, or the raw rest of the line when it has neither form.
    """
    values = []
    # Inline code quotes a marker (`Decided by: user`) rather than claiming it.
    for match in APPROVAL.finditer(INLINE_CODE.sub("", text)):
        rest = match[2].strip()
        if not rest or NOT_YET.match(rest):
            continue

        values.append((match[1].lower(), _approval_value(rest)))

    return values


def id_definitions(root: Path) -> dict[str, list[str]]:
    """Map each ``.ndev`` artifact under ``root`` to the IDs it defines, in order."""
    result = {}
    ndev = root / ".ndev"
    for name, pattern in ID_DEFINITIONS.items():
        path = ndev / name
        if path.is_file():
            result[f".ndev/{name}"] = pattern.findall(path.read_text(errors="replace"))

    for path in sorted((ndev / "tasks").glob("*.md")) if (ndev / "tasks").is_dir() else ():
        result[path.relative_to(root).as_posix()] = TASK_ID.findall(path.read_text(errors="replace"))

    return result


def template_patterns(skill_md: str, template: str) -> list[re.Pattern[str]]:
    """Turn the headings of a SKILL.md template into line patterns.

    The template is the first fenced block after the ``## <template>`` heading.
    ``<placeholder>`` matches any text, and an ID such as ``D1`` or ``T01``
    matches any number with the same letter.

    :param skill_md: SKILL.md text.
    :param template: Heading text, for example ``"Brief template"``.
    :return: One multiline pattern per heading.
    :raises ValueError: When the template is not found.
    """
    match = re.search(rf"^## {re.escape(template)}\n.*?^```\w*\n(.*?)^```$", skill_md, re.M | re.S)
    if not match:
        raise ValueError(f"template {template!r} not found")

    patterns = []
    for line in match[1].splitlines():
        if not re.match(r"^#{1,6} ", line):
            continue

        parts = re.split(r"(<[^>]+>|\b[OQFDT]\d+\b)", line)
        regex = "".join(
            ".+" if p.startswith("<") else rf"{p[0]}\d+" if re.fullmatch(r"[OQFDT]\d+", p) else re.escape(p)
            for p in parts
            if p
        )
        patterns.append(re.compile(rf"^{regex}\s*$", re.M))

    return patterns


def _approval_value(rest: str) -> str:
    """Normalize the value after an approval marker."""
    if re.match(r"(?i)user\b", rest):
        return "user"

    if rest.startswith("agent (delegated:"):
        depth = 0
        for i, char in enumerate(rest[len("agent "):], start=len("agent ")):
            depth += {"(": 1, ")": -1}.get(char, 0)
            if depth == 0:
                return rest[: i + 1]

    return rest


def _count_matches(ctx: RunContext, file: str, pattern: str, minimum: int, maximum: int | None) -> Result:
    """Check the match count of ``pattern`` in every file matching glob ``file``."""
    files = ctx.glob(file)
    if not files:
        return False, f"no file matches {file}"

    counts = {f: len(re.findall(pattern, ctx.read(f) or "", re.M)) for f in files}
    ok = all(n >= minimum and (maximum is None or n <= maximum) for n in counts.values())

    return ok, f"matches: {counts}"


def _questions(text: str | None) -> list[re.Match[str]]:
    """Parsed question lines of a questions.md text (unparseable lines are skipped)."""
    return [m for line in (text or "").splitlines() if (m := QUESTION_LINE.match(line))]
