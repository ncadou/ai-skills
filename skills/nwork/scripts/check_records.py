"""Parse and validate ``nwork/1`` records: ``.nwork/now.md`` and ``.nwork/items/``.

Usage: ``python3 check_records.py [ROOT]``, where ``ROOT`` (default: the
current folder) holds ``.nwork/``. It prints each problem on its own line and
exits 1, or prints ``ok: <n> records`` and exits 0. It exits 2 when ``ROOT``
has no ``.nwork/``. Standard library only.

The specification is ``../references/records.md``. Each ``*_problems``
function returns a list of readable problems; an empty list means the rule
holds. The eval harness loads this file (``evals/harness/records.py``) and
wraps these functions in its checks, so this is the only copy of the rules.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

__all__ = [
    "FORMAT_LINE",
    "Record",
    "eligible",
    "format_problems",
    "link_problems",
    "load_records",
    "main",
    "now_listed",
    "now_problems",
    "problems",
    "section_problems",
]

FORMAT_LINE = "Format: nwork/1"
STATUSES = {
    "O": ("active", "complete", "cancelled"),
    "Q": ("open", "resolved"),
    "F": ("unverified", "verified", "refuted"),
    "D": ("proposed", "decided"),
    "P": ("proposed", "active"),
    "T": ("pending", "in-progress", "implemented", "pass", "fail", "accepted"),
}
VALIDITIES = ("current", "needs-revalidation", "superseded")
METADATA = ("Status", "Validity", "Topics", "Depends on", "Serves", "Answers", "Superseded by")
RELATIONSHIPS = METADATA[3:]
REQUIRED = METADATA[:3]
# Statuses that settle a dependency (records.md § now.md, Eligible work).
SETTLED = ("verified", "decided", "active", "pass", "accepted")
READY = ("pending", "in-progress", "fail", "implemented")
VERIFIED = ("pass", "accepted")
# Sections per kind, in order, and those that may be left out.
SECTIONS = {
    "O": ("Outcome", "Out of scope"),
    "Q": ("Question", "Who answers"),
    "F": ("Claim", "Evidence"),
    "D": ("Options", "Recommendation", "Choice", "Rationale", "Evidence", "Decided by"),
    "P": ("Rule", "Scope", "Exceptions", "Options", "Rationale", "Evidence", "Adopted by"),
    "WA": ("Scope", "Focus", "Authority", "Detail", "Established by"),
    "T": ("Scope", "Expected behavior", "Acceptance", "Latest build", "Latest review"),
}
OPTIONAL = ("Out of scope", "Options", "Recommendation", "Choice", "Exceptions")
# A policy may rest on a shared rationale alone, so its Evidence is optional.
OPTIONAL_BY_KIND = {"P": ("Evidence",)}
NOW_SECTIONS = (
    "Goal", "Direction", "Implemented and verified", "Under revalidation",
    "Needs you", "Eligible work", "Next", "Working agreement",
)
FILENAME = re.compile(r"^(?P<id>[OQFDPT][1-9]\d*)-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
TITLE = re.compile(r"^# (?P<id>[OQFDPT][1-9]\d*): (?P<title>\S.*)$")
LINK = re.compile(r"\[(?P<id>[OQFDPT]\d+)\]\((?P<target>[^)\s]+)\)")
_FENCE = re.compile(r"^```.*?^```[ \t]*$", re.M | re.S)
_INLINE_CODE = re.compile(r"`[^`\n]*`")


@dataclass
class Record:
    """One parsed record file of ``.nwork/items/``."""

    filename: str
    text: str
    id: str | None = None
    title: str = ""
    meta: dict[str, str] = field(default_factory=dict)
    meta_problems: list[str] = field(default_factory=list)
    sections: dict[str, str] = field(default_factory=dict)

    @property
    def kind(self) -> str:
        """The ID prefix, or ``WA`` for the working agreement."""
        if self.id and self.id[0] == "P" and self.title == "Working agreement":
            return "WA"

        return self.id[0] if self.id else "?"

    @property
    def status(self) -> str | None:
        """The ``Status`` value."""
        return self.meta.get("Status")

    @property
    def validity(self) -> str | None:
        """The ``Validity`` value."""
        return self.meta.get("Validity")

    def links(self, key: str) -> list[str]:
        """IDs linked from relationship line ``key``."""
        return [m["id"] for m in LINK.finditer(self.meta.get(key, ""))]


def main(argv: list[str] | None = None) -> int:
    """Check ``<ROOT>/.nwork/``, print the result, and return the exit status.

    :param argv: The command-line arguments; ``sys.argv[1:]`` when ``None``.
    :return: 0 when no problem is found, 1 when some are, 2 without ``.nwork/``.
    """
    parser = argparse.ArgumentParser(description="Check the nwork/1 records under ROOT/.nwork/.")
    parser.add_argument("root", nargs="?", default=".", type=Path, help="folder that holds .nwork/ (default: .)")
    root = parser.parse_args(argv).root
    if not (root / ".nwork").is_dir():
        print(f"no .nwork/ folder under {root}", file=sys.stderr)
        return 2

    found = problems(root)
    for problem in found:
        print(problem)

    if found:
        return 1

    print(f"ok: {len(load_records(root))} records")

    return 0


def problems(root: Path) -> list[str]:
    """Every problem that the checks of this module find under ``<root>/.nwork/``.

    :param root: The work tree.
    :return: The problems of the records, then those of ``now.md``.
    """
    recs = load_records(root)

    return format_problems(recs) + link_problems(recs) + section_problems(recs) + now_problems(root, recs)


def load_records(root: Path) -> list[Record]:
    """Parse every ``*.md`` file of ``<root>/.nwork/items/``, sorted by filename.

    :param root: The work tree.
    :return: The records; an empty list when there is no ``items/`` folder.
    """
    items = root / ".nwork" / "items"
    if not items.is_dir():
        return []

    return [_parse(p.name, p.read_text(errors="replace")) for p in sorted(items.glob("*.md"))]


def format_problems(records: list[Record]) -> list[str]:
    """Filenames, IDs, titles, metadata keys and order, statuses, and validity values."""
    problems = []
    seen: dict[str, str] = {}
    for rec in records:
        name = FILENAME.match(rec.filename)
        if not name:
            problems.append(f"{rec.filename}: filename is not <ID>-<slug>.md")

        if rec.id is None:
            problems.append(f"{rec.filename}: first line is not '# <ID>: <title>'")
            continue

        if name and name["id"] != rec.id:
            problems.append(f"{rec.filename}: title ID {rec.id} does not match the filename")

        if rec.id in seen:
            problems.append(f"{rec.filename}: ID {rec.id} also defined by {seen[rec.id]}")

        seen.setdefault(rec.id, rec.filename)
        problems += [f"{rec.filename}: {p}" for p in rec.meta_problems]
        problems += [f"{rec.filename}: missing {k}" for k in REQUIRED if not rec.meta.get(k)]
        if rec.status and rec.status not in STATUSES[rec.id[0]]:
            problems.append(f"{rec.filename}: status {rec.status!r} not in {STATUSES[rec.id[0]]}")

        if rec.validity and rec.validity not in VALIDITIES:
            problems.append(f"{rec.filename}: validity {rec.validity!r} not in {VALIDITIES}")

    return problems


def link_problems(records: list[Record]) -> list[str]:
    """Relationship syntax, link targets, replacement links, and dependencies of current items."""
    by_id = {r.id: r for r in records if r.id}
    problems = []
    for rec in records:
        if rec.id is None:
            continue

        where = rec.filename
        for key in RELATIONSHIPS:
            value = rec.meta.get(key)
            if value is None:
                continue

            parts = [p.strip() for p in value.split(",")]
            bad = [p for p in parts if not LINK.fullmatch(p)]
            if bad or not parts:
                problems.append(f"{where}: {key} must hold only links [<ID>](<file>), got {bad or value!r}")

        for match in LINK.finditer(_strip_code(rec.text)):
            target = by_id.get(match["id"])
            if target is None or target.filename != match["target"]:
                problems.append(f"{where}: link [{match['id']}]({match['target']}) does not resolve")

        replaced_by = rec.links("Superseded by")
        if (rec.validity == "superseded") != bool(replaced_by):
            problems.append(f"{where}: 'Superseded by' must be present exactly when validity is superseded")

        if rec.id in replaced_by:
            problems.append(f"{where}: superseded by itself")

        if rec.validity == "current":
            for dep in rec.links("Depends on"):
                target = by_id.get(dep)
                if target and (target.validity != "current" or target.status == "refuted"):
                    problems.append(
                        f"{where}: current, but depends on {dep} ({target.status}, {target.validity})"
                    )

    return problems


def section_problems(records: list[Record]) -> list[str]:
    """Type-specific sections: allowed, required, in order, and ``History`` last."""
    problems = []
    for rec in records:
        if rec.id is None:
            continue

        names = list(rec.sections)
        if not names or names[-1] != "History":
            problems.append(f"{rec.filename}: '## History' is not the last section")

        allowed = SECTIONS[rec.kind]
        body = [n for n in names if n != "History"]
        unknown = [n for n in body if n not in allowed]
        optional = OPTIONAL + OPTIONAL_BY_KIND.get(rec.kind, ())
        missing = [n for n in allowed if n not in optional and n not in body]
        ordered = sorted(body, key=lambda n: allowed.index(n) if n in allowed else len(allowed))
        if rec.kind == "D":
            missing += [n for n, s in (("Choice", "decided"), ("Recommendation", "proposed"))
                        if rec.status == s and n not in body]

        if unknown or missing or body != ordered:
            problems.append(f"{rec.filename}: sections {body}; unknown {unknown}, missing {missing}")

    return problems


def now_problems(root: Path, records: list[Record]) -> list[str]:
    """Check ``now.md`` against records.md § now.md and against the records.

    Checks the format line, the sections and their order, that every link
    resolves and none points to a superseded record, that ``Under revalidation``
    lists exactly the records that need revalidation, and that every item listed
    under ``Implemented and verified`` and ``Eligible work`` belongs there. It
    does not check that ``Eligible work`` is complete: a reserved choice can
    block a slice without a link (see ``eligible``).
    """
    path = root / ".nwork" / "now.md"
    if not path.is_file():
        return [".nwork/now.md is missing"]

    text = path.read_text(errors="replace")
    lines = text.splitlines()
    by_id = {r.id: r for r in records if r.id}
    problems = []
    if not lines or not lines[0].startswith("# Now: "):
        problems.append("now.md: first line is not '# Now: <project>'")

    if len(lines) < 3 or lines[2] != FORMAT_LINE:
        problems.append(f"now.md: the line after the title is not {FORMAT_LINE!r}")

    sections = _sections(text)
    names = list(sections)
    reval = {r.id for r in records if r.validity == "needs-revalidation"}
    expected = [n for n in NOW_SECTIONS if n != "Under revalidation" or reval]
    if names != expected:
        problems.append(f"now.md: sections {names}, expected {expected}")

    for match in LINK.finditer(_strip_code(text)):
        target = by_id.get(match["id"])
        if target is None or match["target"] != f"items/{target.filename}":
            problems.append(f"now.md: link [{match['id']}]({match['target']}) does not resolve")
        elif target.validity == "superseded":
            problems.append(f"now.md: lists superseded {match['id']}")

    listed = set(now_listed(text, "Under revalidation"))
    if listed != reval:
        problems.append(f"now.md: Under revalidation lists {sorted(listed)}, records need {sorted(reval)}")

    for rid in now_listed(text, "Implemented and verified"):
        rec = by_id.get(rid)
        if rec and (rec.id[0] != "T" or rec.status not in VERIFIED or rec.validity != "current"):
            problems.append(f"now.md: Implemented and verified lists {rid} ({rec.status}, {rec.validity})")

    ready = eligible(records)
    for rid in now_listed(text, "Eligible work"):
        if rid in by_id and rid not in ready:
            rec = by_id[rid]
            problems.append(f"now.md: Eligible work lists {rid} ({rec.status}, {rec.validity}), which is not eligible")

    return problems


def now_listed(text: str, section: str) -> list[str]:
    """IDs that lead a bullet (``- [<ID>](...)``) in ``section`` of a ``now.md`` text."""
    body = _sections(text).get(section, "")

    return [m["id"] for line in body.splitlines() if (m := re.match(r"^- " + LINK.pattern, line))]


def eligible(records: list[Record]) -> set[str]:
    """Slices that the records alone show as eligible.

    A slice is eligible when its status is ready (build or review), it is
    ``current``, and each dependency is ``current`` and settled. A choice
    reserved for the user that the slice does not link to is invisible here.
    """
    by_id = {r.id: r for r in records if r.id}

    def settled(dep: str) -> bool:
        target = by_id.get(dep)
        return bool(target) and target.validity == "current" and target.status in SETTLED

    return {
        r.id
        for r in records
        if r.id and r.id[0] == "T" and r.status in READY and r.validity == "current"
        and all(settled(d) for d in r.links("Depends on"))
    }


def _parse(filename: str, text: str) -> Record:
    """Parse one record; problems with its metadata block go to ``meta_problems``."""
    rec = Record(filename=filename, text=text)
    lines = text.splitlines()
    title = TITLE.match(lines[0]) if lines else None
    if not title:
        return rec

    rec.id, rec.title = title["id"], title["title"].strip()
    if len(lines) < 2 or lines[1] != "":
        rec.meta_problems.append("no blank line after the title")

    keys = []
    for line in lines[2:]:
        if not line.strip():
            break

        key, sep, value = line.partition(": ")
        if not sep or key not in METADATA:
            rec.meta_problems.append(f"metadata line {line!r} is not one of {METADATA}")
            continue

        if key in rec.meta:
            rec.meta_problems.append(f"{key} given twice")

        keys.append(key)
        rec.meta[key] = value.strip()

    if keys != sorted(keys, key=METADATA.index):
        rec.meta_problems.append(f"metadata order {keys}, expected the order {METADATA}")

    rec.sections = _sections(text)

    return rec


def _sections(text: str) -> dict[str, str]:
    """Map each ``## `` heading outside code fences to its body."""
    sections: dict[str, str] = {}
    current = None
    body: list[str] = []
    for line in _FENCE.sub("", text).splitlines():
        if line.startswith("## "):
            if current is not None:
                sections[current] = "\n".join(body).strip()

            current, body = line[3:].strip(), []
        elif current is not None:
            body.append(line)

    if current is not None:
        sections[current] = "\n".join(body).strip()

    return sections


def _strip_code(text: str) -> str:
    """Remove fenced blocks and inline code, which quote links rather than make them."""
    return _INLINE_CODE.sub("", _FENCE.sub("", text))


if __name__ == "__main__":
    sys.exit(main())
