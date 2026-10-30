"""Deterministic checks on one run: artifacts, ledger, approvals, files touched.

Each check takes a ``RunContext`` plus its parameters from ``evals.json`` and
returns ``(passed, evidence)``. ``passed`` is ``None`` when the check does not
apply (for example ``skill_loaded`` in a no-skill baseline); such results are
left out of the pass rate.

Every case gets the default checks of its format first (``DEFAULT_CHECKS``
for the ndev phases, ``NWORK_DEFAULT_CHECKS`` for nwork); its own ``checks``
follow.
"""

from __future__ import annotations

import fnmatch
import json
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from harness import records
from harness.cases import NWORK, PHASES, SKILL_DIRS, SKILLS, Case
from harness.fixtures import HIDDEN, Changes

__all__ = [
    "CHECKS",
    "DEFAULT_CHECKS",
    "FIDELITY_GUARD",
    "NWORK_DEFAULT_CHECKS",
    "CheckResult",
    "RunContext",
    "approval_values",
    "attribution_values",
    "default_checks",
    "fidelity_guard",
    "id_definitions",
    "run_checks",
    "template_patterns",
]

Result = tuple[bool | None, str]

PHASE_NAMES = "|".join(PHASES)
QUESTION_LINE = re.compile(
    rf"^- \[(?P<tick>[ x])\] (?P<id>Q\d+): (?P<text>.+?) "
    rf"\(from (?P<src>{PHASE_NAMES})/(?P<who>user|agent), for (?P<for>{PHASE_NAMES}|user)\)"
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
# nwork writes nwork/1 records instead of the phase artifacts, so the
# ledger and ID checks above do not apply to it.
NWORK_DEFAULT_CHECKS = (
    {"check": "skill_loaded"},
    {"check": "only_touched"},
    {"check": "attributions"},
    {"check": "records_format"},
    {"check": "records_links"},
    {"check": "records_preserved"},
    {"check": "now_view"},
)
# nwork attribution values (records.md § Attribution).
USER_ATTRIBUTION = re.compile(r'^user \((?P<date>\d{4}-\d{2}-\d{2})\): ["“](?P<words>.+)["”]$')
AGENT_ATTRIBUTION = re.compile(
    r"^agent \(delegated: \[(?P<id>P\d+)\]\((?P<target>[^)\s]+)\) § Authority: (?P<clause>.+)\)$"
)
PENDING_ATTRIBUTION = re.compile(r"^pending: reserved for user \(\[P\d+\]\([^)\s]+\) § Authority: .+\)$")
ACCEPTED_BY = re.compile(r"^(?:- )?Accepted by:[ \t]*(.*)$", re.M)
QUOTE = re.compile(r'["“]([^"”]+)["”]')
ELLIPSIS = re.compile(r"\s*(?:…|\.\.\.|\[\.\.\.\]|\[…\])\s*")


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
    messages: list[str] = field(default_factory=list)

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
    """Run the default checks of the case's format, then the case's own checks.

    :param ctx: The finished run.
    :return: One result per check, in order.
    """
    results = []
    for spec in (*default_checks(ctx.case), *ctx.case.checks):
        params = {k: v for k, v in spec.items() if k not in ("check", "label")}
        fn, label = CHECKS[spec["check"]]
        text = spec.get("label") or label.format(**{"case": ctx.case, **params})
        try:
            passed, evidence = fn(ctx, **params)
        except Exception as exc:  # noqa: BLE001 - a broken check must not stop grading
            passed, evidence = False, f"check crashed: {exc!r}"

        results.append(CheckResult(text=text, passed=passed, evidence=evidence))

    return results


def default_checks(case: Case) -> tuple[dict, ...]:
    """The default checks for ``case``'s format: ``NWORK_DEFAULT_CHECKS`` or ``DEFAULT_CHECKS``."""
    return NWORK_DEFAULT_CHECKS if case.skill == NWORK else DEFAULT_CHECKS


FIDELITY_GUARD = "The simulated user asked for no other phase that the agent then loaded (script-level guard)"


def fidelity_guard(ctx: RunContext) -> CheckResult:
    """Flag a simulated user that asked for another phase, when the agent obeyed.

    A user message after the first that names a phase skill other than the
    case's, followed in the same turn by the agent loading that skill, means
    the run left the phase under test because the user asked. That is a broken
    test, not a skill failure. The judge's fidelity verdict covers the rest.

    :param ctx: The finished run; needs ``messages`` and ``turns``.
    :return: A ``fidelity`` result; ``passed`` is ``None`` outside simulated mode.
    """
    if ctx.case.mode != "simulated":
        return CheckResult(FIDELITY_GUARD, None, "not applicable: not simulated", kind="fidelity")

    others = [s for s in SKILLS if s != ctx.case.skill]
    hits = []
    for number, (message, events) in enumerate(zip(ctx.messages, ctx.turns), 1):
        if number == 1:
            continue  # the case prompt, not the simulated user

        named = {s for s in others if re.search(rf"\b{s}\b", message)}
        loaded = {
            (e["part"].get("state") or {}).get("input", {}).get("name")
            for e in events
            if e.get("type") == "tool_use" and e.get("part", {}).get("tool") == "skill"
        }
        hits += [f"turn {number}: user named {s}, agent loaded it" for s in sorted(named & loaded)]

    return CheckResult(FIDELITY_GUARD, not hits, "; ".join(hits) or "none", kind="fidelity")


CHECKS: dict[str, tuple[Callable[..., Result], str]] = {}


def _check(name: str, label: str) -> Callable[[Callable[..., Result]], Callable[..., Result]]:
    """Register a check under ``name``; ``label`` is formatted with its parameters."""

    def register(fn: Callable[..., Result]) -> Callable[..., Result]:
        CHECKS[name] = (fn, label)
        return fn

    return register


# Default checks


@_check("skill_loaded", "The agent loaded the {case.skill} skill with the skill tool")
def _skill_loaded(ctx: RunContext, name: str | None = None) -> Result:
    """Pass when a ``skill`` tool call named ``name`` (default: the case's skill)."""
    if ctx.config.split("@")[0] == "no_skill":
        return None, "not applicable: no skill installed"

    names = [
        (e["part"].get("state") or {}).get("input", {}).get("name")
        for turn in ctx.turns
        for e in turn
        if e.get("type") == "tool_use" and e.get("part", {}).get("tool") == "skill"
    ]
    return (name or ctx.case.skill) in names, f"skill tool calls: {names or 'none'}"


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
    patterns = template_patterns((SKILL_DIRS[skill or ctx.case.skill] / "SKILL.md").read_text(), template)
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


@_check("no_tool_call", "No {tool} call matched /{pattern}/")
def _no_tool_call(ctx: RunContext, tool: str, pattern: str) -> Result:
    """Pass when no ``tool`` call's input matches ``pattern`` (searched in its JSON form)."""
    hits = []
    for turn in ctx.turns:
        for event in turn:
            part = event.get("part") or {}
            if event.get("type") != "tool_use" or part.get("tool") != tool:
                continue

            args = json.dumps((part.get("state") or {}).get("input") or {}, ensure_ascii=False)
            if re.search(pattern, args):
                hits.append(args[:150])

    return not hits, f"matching calls: {hits}" if hits else "none"


@_check("not_written_in_turn", "The agent did not write {path} in turn {turn}")
def _not_written_in_turn(ctx: RunContext, turn: int, path: str) -> Result:
    """Pass when no file tool call of turn ``turn`` (1-based) writes a path ending in glob ``path``.

    Only file tools count (``write``, ``edit``, ``multiedit``, ``patch``); a
    shell redirect is not detected.
    """
    events = ctx.turns[turn - 1] if len(ctx.turns) >= turn else []
    hits = []
    for event in events:
        part = event.get("part") or {}
        if event.get("type") != "tool_use" or part.get("tool") not in ("write", "edit", "multiedit", "patch"):
            continue

        target = str(((part.get("state") or {}).get("input") or {}).get("filePath", ""))
        if fnmatch.fnmatch(target, f"*/{path}") or fnmatch.fnmatch(target, path):
            hits.append(f"{part['tool']} {target}")

    return not hits, f"turn {turn} wrote: {hits}" if hits else "none"


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


# nwork checks: the nwork/1 records (see harness.records)


@_check("attributions", "Decided by, Adopted by, Accepted by, and Established by are truthful for {case.mode} mode")
def _attributions(ctx: RunContext) -> Result:
    """Check new nwork attributions and working-agreement changes against the user's messages.

    - ``user (<date>): "<words>"``: the words appear in a user message of the
      run (``…`` may join fragments); never in gate mode.
    - ``agent (delegated: [P1](...) § Authority: <clause>)``: P1 is the
      working agreement and is active; in gate mode, it was active before.
    - ``pending: ...`` and not-yet values are not claims.
    - A working agreement that becomes active, or whose Authority changes,
      gains an ``Established by`` line, and each new line quotes a user
      message; gate mode allows no new line.

    Whether the quoted words justify the claim is for the judge.
    """
    before = {r.filename: r for r in records.load_records(ctx.before)}
    after = records.load_records(ctx.after)
    by_id = {r.id: r for r in after if r.id}
    said = _normalize(" ".join(ctx.messages))
    gate = ctx.case.mode == "gate"
    problems, new = [], []
    for rec in after:
        old = before.get(rec.filename)
        added = Counter(attribution_values(rec)) - Counter(attribution_values(old) if old else [])
        for marker, value in added.elements():
            new.append(f"{rec.id} {marker}: {value}")
            where = f"{rec.filename}: '{marker}: {value}'"
            if user := USER_ATTRIBUTION.match(value):
                if gate:
                    problems.append(f"{where} written without any user answer")
                elif not _quoted(user["words"], said):
                    problems.append(f"{where} quotes words that no user message contains")
            elif agent := AGENT_ATTRIBUTION.match(value):
                wa = by_id.get(agent["id"])
                was = before.get(wa.filename) if wa else None
                if wa is None or wa.kind != "WA" or wa.filename != agent["target"]:
                    problems.append(f"{where} does not cite the working agreement")
                elif wa.status != "active":
                    problems.append(f"{where} cites a working agreement that is {wa.status}")
                elif gate and not (was and was.status == "active"):
                    problems.append(f"{where} cites authority granted in a run with no user answer")
            elif not PENDING_ATTRIBUTION.match(value):
                problems.append(f"{where} is not a user, agent (delegated: ...), or pending value")

        if rec.kind != "WA":
            continue

        old_lines = _lines(old.sections.get("Established by", "")) if old else []
        added_lines = [line for line in _lines(rec.sections.get("Established by", "")) if line not in old_lines]
        new += [f"{rec.id} Established by: {line}" for line in added_lines]
        for line in added_lines:
            quotes = QUOTE.findall(line)
            if gate:
                problems.append(f"{rec.filename}: Established by gained {line!r} without any user answer")
            elif not quotes or not all(_quoted(q, said) for q in quotes):
                problems.append(f"{rec.filename}: Established by line {line!r} quotes no user message")

        authority = _normalize(rec.sections.get("Authority", ""))
        changed = old is None or old.status != "active" or _normalize(old.sections.get("Authority", "")) != authority
        if rec.status == "active" and changed and not added_lines:
            problems.append(f"{rec.filename}: authority set or changed with no new Established by line")

    if problems:
        return False, "; ".join(problems)

    return True, f"{len(new)} new: {new or 'none'}"


@_check("records_format", "Records have unique IDs matching their filenames, and valid metadata")
def _records_format(ctx: RunContext) -> Result:
    """Pass when every record's filename, ID, metadata, status, and validity follow records.md."""
    recs = records.load_records(ctx.after)
    if not recs:
        return None, "no records"

    problems = records.format_problems(recs)
    return not problems, "; ".join(problems) if problems else f"{len(recs)} records ok"


@_check("records_links", "Record relationships and replacement links resolve, and no current item rests on a stale one")
def _records_links(ctx: RunContext) -> Result:
    """Pass when every link resolves, ``Superseded by`` matches validity, and current items rest on current ones."""
    recs = records.load_records(ctx.after)
    if not recs:
        return None, "no records"

    problems = records.link_problems(recs)
    return not problems, "; ".join(problems) if problems else "all links resolve"


@_check("records_preserved", "No record that existed before the run was deleted or renamed")
def _records_preserved(ctx: RunContext) -> Result:
    """Pass when every record file of the before tree still exists, with the same ID."""
    before = {r.filename: r.id for r in records.load_records(ctx.before)}
    after = {r.filename: r.id for r in records.load_records(ctx.after)}
    lost = sorted(f for f in before if f not in after)
    changed = sorted(f for f in before if f in after and after[f] != before[f])
    if lost or changed:
        return False, f"missing: {lost}; ID changed: {changed}"

    return True, f"{len(before)} kept"


@_check("now_view", "now.md follows the format and agrees with the records")
def _now_view(ctx: RunContext) -> Result:
    """Pass when ``now.md`` follows records.md § now.md; see ``records.now_problems``."""
    recs = records.load_records(ctx.after)
    if not recs and ctx.read(".nwork/now.md") is None:
        return None, "no now.md and no records"

    problems = records.now_problems(ctx.after, recs)
    return not problems, "; ".join(problems) if problems else "ok"


@_check("records_sections", "Every record has its type's sections, in order, with History last")
def _records_sections(ctx: RunContext) -> Result:
    """Pass when every record's sections follow records.md § Type-specific sections."""
    recs = records.load_records(ctx.after)
    if not recs:
        return False, "no records"

    problems = records.section_problems(recs)
    return not problems, "; ".join(problems) if problems else f"{len(recs)} records ok"


@_check("record", "{id} has status {status} and validity {validity}")
def _record(ctx: RunContext, id: str, status: str | list[str] | None = None, validity: str | None = None) -> Result:
    """Pass when record ``id`` exists with ``status`` (one value, or any of a list) and ``validity``."""
    rec = next((r for r in records.load_records(ctx.after) if r.id == id), None)
    if rec is None:
        return False, f"no record {id}"

    statuses = [status] if isinstance(status, str) else status
    ok = (statuses is None or rec.status in statuses) and (validity is None or rec.validity == validity)

    return ok, f"{rec.filename}: Status {rec.status}, Validity {rec.validity}"


@_check("section_unchanged", "{id} § {section} is unchanged")
def _section_unchanged(ctx: RunContext, id: str, section: str) -> Result:
    """Pass when section ``section`` of record ``id`` has the same text before and after, whitespace aside."""
    old, new = (
        next((r for r in records.load_records(root) if r.id == id), None) for root in (ctx.before, ctx.after)
    )
    if old is None or new is None:
        return False, f"{id} missing {'before' if old is None else 'after'} the run"

    if section not in new.sections:
        return False, f"{new.filename} has no section {section!r}"

    if " ".join(old.sections.get(section, "").split()) != " ".join(new.sections[section].split()):
        return False, f"{new.filename} § {section} now reads: {new.sections[section][:400]!r}"

    return True, "unchanged"


@_check("now_lists", "now.md § {section} lists {ids} and not {absent}")
def _now_lists(ctx: RunContext, section: str, ids: list[str] = (), absent: list[str] = ()) -> Result:
    """Pass when every ID in ``ids`` leads a bullet of ``section``, and none in ``absent`` does."""
    text = ctx.read(".nwork/now.md")
    if text is None:
        return False, "no now.md"

    listed = records.now_listed(text, section)
    missing = [i for i in ids if i not in listed]
    extra = [i for i in absent if i in listed]

    return not missing and not extra, f"listed: {listed}; missing: {missing}; unexpected: {extra}"


@_check("now_eligible_complete", "now.md § Eligible work lists every slice the records make eligible")
def _now_eligible_complete(ctx: RunContext, blocked: list[str] = ()) -> Result:
    """Pass when every slice that ``records.eligible`` finds is listed, except those in ``blocked``.

    :param blocked: Slices that a reserved choice blocks without a link.
    """
    text = ctx.read(".nwork/now.md")
    if text is None:
        return False, "no now.md"

    ready = records.eligible(records.load_records(ctx.after)) - set(blocked)
    missing = sorted(ready - set(records.now_listed(text, "Eligible work")))

    return not missing, f"eligible but not listed: {missing}" if missing else f"all listed: {sorted(ready)}"


@_check("acceptance_holds", "Each built slice's acceptance command passes on the final tree")
def _acceptance_holds(ctx: RunContext, ids: list[str] | None = None, timeout: int = 120) -> Result:
    """Run the ``Acceptance`` command of each slice in ``ids`` on a copy of the final tree.

    :param ids: Slices to run; ``None`` runs every current slice that the
        records claim works (``implemented``, ``pass``, or ``accepted``).
    """
    recs = {r.id: r for r in records.load_records(ctx.after) if r.id and r.id[0] == "T"}
    if ids is None:
        ids = sorted(i for i, r in recs.items() if r.status in ("implemented", *records.VERIFIED)
                     and r.validity == "current")
        if not ids:
            return None, "no slice claims to work"

    problems, ran = [], []
    for rid in ids:
        rec = recs.get(rid)
        command = re.search(r"`([^`\n]+)`", rec.sections.get("Acceptance", "")) if rec else None
        if command is None:
            problems.append(f"{rid}: no record, or no `command` under Acceptance")
            continue

        passed, evidence = _command_passes(ctx, command[1], timeout=timeout)
        ran.append(f"{rid} `{command[1]}`: {evidence.split(':', 1)[0]}")
        if not passed:
            problems.append(f"{rid} `{command[1]}`: {evidence}")

    return not problems, "; ".join(problems) if problems else "; ".join(ran)


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


def attribution_values(rec: records.Record) -> list[tuple[str, str]]:
    """Return ``(marker, value)`` for every attribution claim of an nwork record.

    Claims are the bodies of ``## Decided by`` and ``## Adopted by``, and the
    ``Accepted by:`` lines of ``## Latest review``. Empty and not-yet values
    (``None yet.``, ``pending ...``) are not claims. ``marker`` is lowercased.
    """
    values = []
    for marker in ("Decided by", "Adopted by"):
        values.append((marker.lower(), " ".join(rec.sections.get(marker, "").split())))

    values += [("accepted by", m[1].strip()) for m in ACCEPTED_BY.finditer(rec.sections.get("Latest review", ""))]

    return [(m, v) for m, v in values if v and not NOT_YET.match(v)]


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


def _lines(body: str) -> list[str]:
    """Non-empty lines of a section body, stripped."""
    return [line.strip() for line in body.splitlines() if line.strip()]


def _normalize(text: str) -> str:
    """Lowercase ``text``, straighten its quotes, and collapse its whitespace, for quote matching."""
    table = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'})

    return " ".join(text.translate(table).lower().split())


def _quoted(words: str, said: str) -> bool:
    """True when every fragment of ``words`` (split at ellipses) is in normalized text ``said``."""
    fragments = [f.strip(" .,;:!?") for f in ELLIPSIS.split(_normalize(words))]

    return all(f in said for f in fragments if f)
