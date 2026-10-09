"""Tests for the nwork support: the bundled record checker, the nwork checks, install, and prompts.

Run from ``evals/``: ``python3 -m unittest discover -s tests -t . -v``
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness import checks, records
from harness.agent import make_home
from harness.cases import BUNDLE, NWORK, PHASES, SKILL_DIRS, SKILLS_ROOT, WRITABLE, load_cases
from harness.checks import DEFAULT_CHECKS, NWORK_DEFAULT_CHECKS, RunContext, default_checks, run_checks
from harness.fixtures import diff_trees, materialize
from harness.judge import FORMAT_HELP, MODE_HELP, NWORK_MODE_HELP
from harness.runner import Config, user_prompt
from tests.test_checks import _case

EXAMPLE = SKILLS_ROOT / "ndev-next" / "examples" / "resumable-import" / "snapshots"
ITEMS = ".ndev/items"


def _nwork_case(**overrides: object):
    """A minimal nwork case."""
    return _case(**{"skill": NWORK, "state": "nwork-working", **overrides})


class _NworkTreeTest(unittest.TestCase):
    """Base: before and after trees of an nwork state, and helpers to edit the after tree."""

    state = "nwork-working"

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.before = root / "before"
        self.after = root / "after"
        materialize(self.state, self.before)
        materialize(self.state, self.after)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def path(self, name: str) -> Path:
        """Path of the record file ``name`` (or of ``now.md``) in the after tree."""
        return self.after / ".ndev" / name if name == "now.md" else self.after / ITEMS / name

    def edit(self, name: str, old: str, new: str) -> None:
        """Replace ``old`` with ``new`` once in a record (or ``now.md``) of the after tree."""
        text = self.path(name).read_text()
        self.assertIn(old, text, f"{name}: {old!r} not found")
        self.path(name).write_text(text.replace(old, new, 1))

    def check(self, name: str, mode: str = "delegated", messages: list[str] | None = None, **params) -> tuple:
        """Run check ``name`` on the trees and return ``(passed, evidence)``."""
        ctx = RunContext(
            case=_nwork_case(mode=mode), config="with_skill", before=self.before, after=self.after,
            changes=diff_trees(self.before, self.after), messages=messages or ["Use the nwork skill."],
        )
        fn, _ = checks.CHECKS[name]

        return fn(ctx, **params)


class ExampleSnapshotsTest(unittest.TestCase):
    """The worked example's snapshots follow the record specification."""

    def test_snapshots_are_valid(self) -> None:
        snapshots = sorted(p for p in EXAMPLE.iterdir() if p.is_dir())
        self.assertEqual(len(snapshots), 3)
        for snap in snapshots:
            with self.subTest(snapshot=snap.name):
                recs = records.load_records(snap)
                self.assertTrue(recs)
                self.assertEqual(records.format_problems(recs), [])
                self.assertEqual(records.link_problems(recs), [])
                self.assertEqual(records.section_problems(recs), [])
                self.assertEqual(records.now_problems(snap, recs), [])

    def test_ids_are_preserved_across_snapshots(self) -> None:
        snapshots = sorted(p for p in EXAMPLE.iterdir() if p.is_dir())
        for old, new in zip(snapshots, snapshots[1:]):
            before = {r.filename for r in records.load_records(old)}
            after = {r.filename for r in records.load_records(new)}
            self.assertLessEqual(before, after, f"{old.name} -> {new.name}")

    def test_revised_snapshot_marks_revalidation(self) -> None:
        recs = {r.id: r for r in records.load_records(EXAMPLE / "02-revised")}
        self.assertEqual(recs["F1"].status, "refuted")
        self.assertEqual(recs["T2"].validity, "needs-revalidation")
        self.assertNotIn("T2", records.eligible(recs.values()))


class CheckerScriptTest(unittest.TestCase):
    """The checker bundled in nwork/scripts/ runs from a copy of nwork/ alone."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        # A copy of the skill folder alone, as an install makes it.
        self.script = shutil.copytree(SKILL_DIRS[NWORK], tmp / NWORK) / "scripts" / "check_records.py"
        self.project = shutil.copytree(EXAMPLE / "03-resumed", tmp / "project")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_script(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
        """Run the copied script with ``args``; ``-I`` keeps the harness off its path."""
        return subprocess.run([sys.executable, "-I", str(self.script), *args], cwd=cwd,
                              capture_output=True, text=True, timeout=60)

    def test_valid_records(self) -> None:
        result = self.run_script(str(self.project))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "ok: 20 records\n")

    def test_root_defaults_to_current_folder(self) -> None:
        result = self.run_script(cwd=self.project)
        self.assertEqual((result.returncode, result.stdout), (0, "ok: 20 records\n"))

    def test_reports_each_problem(self) -> None:
        t1 = self.project / ITEMS / "T1-progress-line.md"
        t1.write_text(t1.read_text().replace("Validity: current", "Validity: stale", 1))
        (self.project / ".ndev" / "now.md").write_text(
            (self.project / ".ndev" / "now.md").read_text() + "\nSee [T9](items/T9-missing.md).\n")
        result = self.run_script(str(self.project))
        self.assertEqual(result.returncode, 1)
        lines = result.stdout.splitlines()
        self.assertTrue(any("T1-progress-line.md: validity 'stale'" in line for line in lines), lines)
        self.assertTrue(any("now.md: link [T9](items/T9-missing.md) does not resolve" in line for line in lines),
                        lines)
        self.assertFalse(any(line.startswith("ok:") for line in lines))

    def test_matches_the_harness(self) -> None:
        (self.project / ".ndev" / "now.md").write_text("# Now: x\n")
        result = self.run_script(str(self.project))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout.splitlines(), records.problems(self.project))

    def test_without_ndev_folder(self) -> None:
        empty = Path(self._tmp.name) / "empty"
        empty.mkdir()
        result = self.run_script(str(empty))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("no .ndev/ folder", result.stderr)

    def test_harness_loads_the_bundled_copy(self) -> None:
        self.assertEqual(records.SCRIPT, SKILL_DIRS[NWORK] / "scripts" / "check_records.py")
        self.assertEqual(Path(records.load_records.__code__.co_filename), records.SCRIPT)
        self.assertFalse((records.SCRIPT.parent / "__pycache__").exists(), "loading must not write bytecode")


class RecordsFormatTest(_NworkTreeTest):
    """records_format: filenames, IDs, metadata, statuses, validity values."""

    def test_fixture_is_valid(self) -> None:
        self.assertTrue(self.check("records_format")[0])

    def test_duplicate_id(self) -> None:
        shutil.copy(self.path("D1-non-ascii-separators.md"), self.path("D1-copy.md"))
        passed, evidence = self.check("records_format")
        self.assertFalse(passed)
        self.assertIn("also defined by", evidence)

    def test_filename_must_match_id(self) -> None:
        self.path("D2-cut-at-last-hyphen.md").rename(self.path("D9-cut-at-last-hyphen.md"))
        self.assertFalse(self.check("records_format")[0])

    def test_padded_id_and_bad_slug(self) -> None:
        self.path("T1-slugify-function.md").rename(self.path("T01-Slugify.md"))
        passed, evidence = self.check("records_format")
        self.assertFalse(passed)
        self.assertIn("filename is not", evidence)

    def test_status_must_fit_type(self) -> None:
        self.edit("F1-accent-helper.md", "Status: verified", "Status: decided")
        self.assertFalse(self.check("records_format")[0])

    def test_bad_validity(self) -> None:
        self.edit("T1-slugify-function.md", "Validity: current", "Validity: stale")
        self.assertFalse(self.check("records_format")[0])

    def test_missing_topics(self) -> None:
        self.edit("O1-slugify-function.md", "Topics: slugify\n", "")
        passed, evidence = self.check("records_format")
        self.assertFalse(passed)
        self.assertIn("missing Topics", evidence)

    def test_metadata_order_and_unknown_key(self) -> None:
        self.edit("T1-slugify-function.md", "Status: pending\nValidity: current", "Validity: current\nStatus: pending")
        self.assertIn("metadata order", self.check("records_format")[1])
        self.edit("O2-slugify-command.md", "Topics: cli", "Topics: cli\nOwner: me")
        self.assertIn("Owner: me", self.check("records_format")[1])

    def test_title_line(self) -> None:
        self.edit("O1-slugify-function.md", "# O1: A slugify function", "# A slugify function")
        self.assertFalse(self.check("records_format")[0])


class RecordsLinksTest(_NworkTreeTest):
    """records_links: relationships, replacement links, dependencies of current items."""

    def test_fixture_is_valid(self) -> None:
        self.assertTrue(self.check("records_links")[0])

    def test_broken_link(self) -> None:
        self.edit("T1-slugify-function.md", "[D2](D2-cut-at-last-hyphen.md)", "[D2](D2-cut.md)")
        passed, evidence = self.check("records_links")
        self.assertFalse(passed)
        self.assertIn("does not resolve", evidence)

    def test_link_to_missing_record(self) -> None:
        self.edit("T1-slugify-function.md", "## Scope\n", "## Scope\n\nSee [F9](F9-nothing.md).\n")
        self.assertFalse(self.check("records_links")[0])

    def test_links_in_code_are_quotes(self) -> None:
        self.edit("T1-slugify-function.md", "## Scope\n", "## Scope\n\nFormat: `[F9](F9-nothing.md)`.\n")
        self.assertTrue(self.check("records_links")[0])

    def test_relationship_holds_only_links(self) -> None:
        self.edit("T2-slugify-command.md", "Serves: [O2](O2-slugify-command.md)", "Serves: O2")
        self.assertFalse(self.check("records_links")[0])

    def test_superseded_needs_replacement_link(self) -> None:
        self.edit("D2-cut-at-last-hyphen.md", "Validity: current", "Validity: superseded")
        self.assertFalse(self.check("records_links")[0])

    def test_replacement_link_needs_superseded(self) -> None:
        self.edit("D2-cut-at-last-hyphen.md", "Serves: [O1](O1-slugify-function.md)",
                  "Serves: [O1](O1-slugify-function.md)\nSuperseded by: [D3](D3-empty-slug-error.md)")
        self.assertFalse(self.check("records_links")[0])

    def test_valid_replacement(self) -> None:
        self.edit("D2-cut-at-last-hyphen.md", "Validity: current\nTopics: slugify\nServes: [O1](O1-slugify-function.md)",
                  "Validity: superseded\nTopics: slugify\nServes: [O1](O1-slugify-function.md)\n"
                  "Superseded by: [D3](D3-empty-slug-error.md)")
        # T1 still depends on the superseded D2 while current: that alone fails.
        passed, evidence = self.check("records_links")
        self.assertFalse(passed)
        self.assertIn("depends on D2", evidence)
        # Marked for revalidation, with its own dependant T2, it passes.
        self.edit("T1-slugify-function.md", "Validity: current", "Validity: needs-revalidation")
        self.edit("T2-slugify-command.md", "Validity: current", "Validity: needs-revalidation")
        self.assertTrue(*self.check("records_links"))

    def test_current_item_on_refuted_finding(self) -> None:
        self.edit("F1-accent-helper.md", "Status: verified", "Status: refuted")
        passed, evidence = self.check("records_links")
        self.assertFalse(passed)
        self.assertIn("D1-non-ascii-separators.md: current, but depends on F1", evidence)


class RecordsPreservedTest(_NworkTreeTest):
    """records_preserved: no record is deleted or renamed."""

    def test_new_record_is_fine(self) -> None:
        shutil.copy(self.path("Q1-non-ascii-letters.md"), self.path("Q2-other.md"))
        self.assertTrue(self.check("records_preserved")[0])

    def test_deleted_record(self) -> None:
        self.path("Q1-non-ascii-letters.md").unlink()
        self.assertFalse(self.check("records_preserved")[0])

    def test_renamed_record(self) -> None:
        self.path("Q1-non-ascii-letters.md").rename(self.path("Q1-letters.md"))
        self.assertFalse(self.check("records_preserved")[0])


class NowViewTest(_NworkTreeTest):
    """now_view and the now.md case checks."""

    def test_fixture_is_valid(self) -> None:
        self.assertTrue(self.check("now_view")[0])

    def test_format_line(self) -> None:
        self.edit("now.md", "Format: ndev-next/1", "Format: ndev")
        self.assertFalse(self.check("now_view")[0])

    def test_section_order(self) -> None:
        self.edit("now.md", "## Needs you", "## Blockers")
        self.assertFalse(self.check("now_view")[0])

    def test_link_must_point_into_items(self) -> None:
        self.edit("now.md", "(items/T1-slugify-function.md)", "(T1-slugify-function.md)")
        self.assertIn("does not resolve", self.check("now_view")[1])

    def test_eligible_excludes_revalidation(self) -> None:
        self.edit("T1-slugify-function.md", "Validity: current", "Validity: needs-revalidation")
        self.edit("now.md", "## Needs you", "## Under revalidation\n\n- [T1](items/T1-slugify-function.md): x\n\n## Needs you")
        passed, evidence = self.check("now_view")
        self.assertFalse(passed)
        self.assertIn("Eligible work lists T1", evidence)

    def test_eligible_excludes_unsettled_dependency(self) -> None:
        self.edit("now.md", "## Next", "- [T2](items/T2-slugify-command.md): the command.\n\n## Next")
        self.assertIn("Eligible work lists T2", self.check("now_view")[1])

    def test_under_revalidation_must_match_records(self) -> None:
        self.edit("D2-cut-at-last-hyphen.md", "Validity: current", "Validity: needs-revalidation")
        self.assertFalse(self.check("now_view")[0])

    def test_no_superseded_item_listed(self) -> None:
        self.edit("D4-cli-error-output.md", "Serves: [O2](O2-slugify-command.md)",
                  "Serves: [O2](O2-slugify-command.md)\nSuperseded by: [D3](D3-empty-slug-error.md)")
        self.edit("D4-cli-error-output.md", "Validity: current", "Validity: superseded")
        self.assertIn("lists superseded D4", self.check("now_view")[1])

    def test_implemented_and_verified_needs_pass(self) -> None:
        self.edit("now.md", "## Implemented and verified\n\nNone.",
                  "## Implemented and verified\n\n- [T1](items/T1-slugify-function.md): done.")
        self.assertIn("Implemented and verified lists T1", self.check("now_view")[1])

    def test_missing_now(self) -> None:
        self.path("now.md").unlink()
        self.assertFalse(self.check("now_view")[0])

    def test_not_applicable_without_records(self) -> None:
        shutil.rmtree(self.after / ".ndev")
        self.assertIsNone(self.check("now_view")[0])
        self.assertIsNone(self.check("records_format")[0])

    def test_eligible_complete(self) -> None:
        self.assertTrue(self.check("now_eligible_complete")[0])
        self.edit("now.md", "- [T1](items/T1-slugify-function.md): the `slugify` function, with its tests.\n", "None.\n")
        self.assertFalse(self.check("now_eligible_complete")[0])
        self.assertTrue(self.check("now_eligible_complete", blocked=["T1"])[0])

    def test_now_lists(self) -> None:
        self.assertTrue(self.check("now_lists", section="Needs you", ids=["D4"], absent=["T1"])[0])
        self.assertFalse(self.check("now_lists", section="Eligible work", ids=["T2"])[0])

    def test_record(self) -> None:
        self.assertTrue(self.check("record", id="T1", status=["pending", "pass"], validity="current")[0])
        self.assertFalse(self.check("record", id="T1", status="pass")[0])
        self.assertFalse(self.check("record", id="T9")[0])

    def test_section_unchanged(self) -> None:
        params = {"id": "P1", "section": "Authority"}
        self.assertTrue(self.check("section_unchanged", **params)[0])
        self.edit("P1-working-agreement.md", "Delegated to the agent:\n", "Delegated to the agent:\n\n")
        self.edit("P1-working-agreement.md", "- errors: what", "- cli: what")
        self.assertTrue(self.check("section_unchanged", **params)[0], "whitespace and other sections")
        self.edit("P1-working-agreement.md", "- Changing a decided contract.\n", "")
        self.assertIn("now reads", self.check("section_unchanged", **params)[1])
        self.assertFalse(self.check("section_unchanged", id="P1", section="Powers")[0])
        self.assertFalse(self.check("section_unchanged", id="P9", section="Authority")[0])


class SectionsTest(_NworkTreeTest):
    """records_sections: type-specific sections."""

    def test_fixture_is_valid(self) -> None:
        self.assertTrue(self.check("records_sections")[0])

    def test_history_last(self) -> None:
        self.edit("O1-slugify-function.md", "## History", "## Notes\n\nx\n\n## History")
        self.assertFalse(self.check("records_sections")[0])
        self.edit("O2-slugify-command.md", "## History", "## Log")
        self.assertIn("History", self.check("records_sections")[1])

    def test_decided_needs_choice(self) -> None:
        self.edit("D3-empty-slug-error.md", "## Choice", "## Picked")
        self.assertFalse(self.check("records_sections")[0])

    def test_working_agreement_sections(self) -> None:
        self.edit("P1-working-agreement.md", "## Established by", "## Agreed")
        self.assertIn("P1-working-agreement.md", self.check("records_sections")[1])

    def test_policy_sections(self) -> None:
        body = "# P2: One line out per line in\n\nStatus: proposed\nValidity: current\nTopics: cli\n\n{}\n## History\n\n- x\n"
        full = "## Rule\n\nx\n\n## Scope\n\nx\n\n## Options\n\nx\n\n## Rationale\n\nx\n\n## Evidence\n\nx\n\n## Adopted by\n\nx\n"
        self.path("P2-one-line.md").write_text(body.format(full))
        self.assertTrue(self.check("records_sections")[0], "Options and Evidence are allowed")
        self.path("P2-one-line.md").write_text(body.format(full.replace("## Options\n\nx\n\n", "").replace("## Evidence\n\nx\n\n", "")))
        self.assertTrue(self.check("records_sections")[0], "and optional")
        self.path("P2-one-line.md").write_text(body.format(full.replace("## Scope\n\nx\n\n", "")))
        self.assertIn("missing ['Scope']", self.check("records_sections")[1])


class AttributionsTest(_NworkTreeTest):
    """attributions: quotes come from the user, delegations from an active working agreement."""

    PROMPT = "Use the nwork skill. For D4, go with exit code 2 and the textkit: error: prefix."

    def _decide_d4(self, value: str) -> None:
        self.edit("D4-cli-error-output.md", "Status: proposed", "Status: decided")
        self.edit("D4-cli-error-output.md",
                  "pending: reserved for user ([P1](P1-working-agreement.md) § Authority: user-visible command-line behavior)",
                  value)

    def test_fixture_has_no_new_claim(self) -> None:
        self.assertTrue(self.check("attributions", mode="gate")[0])

    def test_user_quote_from_prompt(self) -> None:
        self._decide_d4('user (2026-10-13): "go with exit code 2 and the textkit: error: prefix"')
        self.assertTrue(self.check("attributions", messages=[self.PROMPT])[0])

    def test_user_quote_with_ellipsis_and_curly_quotes(self) -> None:
        self._decide_d4("user (2026-10-13): “For D4, go with exit code 2 … prefix.”")
        self.assertTrue(self.check("attributions", messages=[self.PROMPT])[0])

    def test_invented_quote(self) -> None:
        self._decide_d4('user (2026-10-13): "exit code 1 is fine"')
        passed, evidence = self.check("attributions", messages=[self.PROMPT])
        self.assertFalse(passed)
        self.assertIn("no user message contains", evidence)

    def test_gate_rejects_user_claim(self) -> None:
        self._decide_d4('user (2026-10-13): "go with exit code 2"')
        self.assertFalse(self.check("attributions", mode="gate", messages=[self.PROMPT])[0])

    def test_agent_claim_needs_active_working_agreement(self) -> None:
        clause = "agent (delegated: [P1](P1-working-agreement.md) § Authority: internal naming)"
        self._decide_d4(clause)
        self.assertTrue(self.check("attributions", mode="gate")[0])
        self.edit("P1-working-agreement.md", "Status: active", "Status: proposed")
        self.assertIn("is proposed", self.check("attributions")[1])

    def test_agent_claim_must_cite_working_agreement(self) -> None:
        self._decide_d4("agent (delegated: [P2](P2-nothing.md) § Authority: everything)")
        self.assertIn("does not cite the working agreement", self.check("attributions")[1])

    def test_agent_claim_in_gate_needs_prior_agreement(self) -> None:
        self.edit("P1-working-agreement.md", "Status: active", "Status: proposed")
        shutil.copytree(self.after / ".ndev", self.before / ".ndev", dirs_exist_ok=True)
        self.edit("P1-working-agreement.md", "Status: proposed", "Status: active")
        self.edit("P1-working-agreement.md", "## History", '- 2026-10-13, user: "Use the nwork skill."\n\n## History')
        self._decide_d4("agent (delegated: [P1](P1-working-agreement.md) § Authority: internal naming)")
        passed, evidence = self.check("attributions", mode="gate")
        self.assertFalse(passed)
        self.assertIn("authority granted in a run with no user answer", evidence)

    def test_malformed_agent_value(self) -> None:
        self._decide_d4("agent")
        self.assertIn("is not a user", self.check("attributions")[1])

    def test_unquoted_user_value(self) -> None:
        self._decide_d4("user")
        self.assertIn("is not a user", self.check("attributions")[1])

    def test_accepted_by(self) -> None:
        self.edit("T1-slugify-function.md", "## Latest review\n\nNone yet.",
                  '## Latest review\n\n- Verdict: pass\n- Accepted by: user (2026-10-13): "ship it"')
        self.assertFalse(self.check("attributions", messages=["Looks good."])[0])
        self.assertTrue(self.check("attributions", messages=["Looks good, ship it."])[0])

    def test_authority_change_needs_established_by(self) -> None:
        self.edit("P1-working-agreement.md", "- Accepting a slice.\n", "")
        passed, evidence = self.check("attributions")
        self.assertFalse(passed)
        self.assertIn("authority set or changed", evidence)

    def test_authority_change_quoting_user(self) -> None:
        message = "You can accept slices yourself from now on."
        self.edit("P1-working-agreement.md", "- Accepting a slice.\n", "")
        self.edit("P1-working-agreement.md", "\n\n## History", f'\n- 2026-10-13, user: "{message}"\n\n## History')
        self.assertTrue(self.check("attributions", messages=["Use the nwork skill.", message])[0])
        self.assertFalse(self.check("attributions", messages=["Use the nwork skill."])[0])
        self.assertFalse(self.check("attributions", mode="gate", messages=[message])[0])

    def test_focus_change_needs_no_new_quote(self) -> None:
        self.edit("P1-working-agreement.md", "- errors: what", "- naming: what")
        self.assertTrue(self.check("attributions")[0])


class AcceptanceHoldsTest(_NworkTreeTest):
    """acceptance_holds runs the slices' own acceptance commands."""

    state = "nwork-built"

    def test_built_slice_passes(self) -> None:
        passed, evidence = self.check("acceptance_holds")
        self.assertTrue(passed, evidence)
        self.assertIn("T1", evidence)

    def test_broken_code_fails(self) -> None:
        slug = self.after / "textkit" / "slug.py"
        slug.write_text(slug.read_text().replace('raise ValueError("slug is empty")', 'return ""'))
        self.assertFalse(self.check("acceptance_holds", ids=["T1"])[0])

    def test_unbuilt_slice_fails_when_named(self) -> None:
        self.assertFalse(self.check("acceptance_holds", ids=["T2"])[0])

    def test_not_applicable_when_nothing_claims_to_work(self) -> None:
        self.edit("T1-slugify-function.md", "Status: implemented", "Status: pending")
        self.assertIsNone(self.check("acceptance_holds")[0])


class DefaultsTest(unittest.TestCase):
    """Each format gets its own defaults; the ndev phases keep their original ones."""

    LEGACY_DEFAULTS = (
        {"check": "skill_loaded"},
        {"check": "only_touched"},
        {"check": "approvals"},
        {"check": "questions_format"},
        {"check": "ids_unique"},
        {"check": "ids_preserved"},
    )
    LEGACY_WRITABLE = {
        "nstart": (".ndev/brief.md", ".ndev/questions.md"),
        "nlearn": (".ndev/discovery.md", ".ndev/questions.md", ".ndev/scratch/*"),
        "ndesign": (".ndev/design.md", ".ndev/questions.md"),
        "nplan": (".ndev/plan.md", ".ndev/tasks/*", ".ndev/questions.md"),
        "nbuild": ("textkit/*", "tests/*", "README.md", ".ndev/questions.md"),
        "nreview": (".ndev/questions.md",),
    }

    def test_legacy_defaults_unchanged(self) -> None:
        self.assertEqual(DEFAULT_CHECKS, self.LEGACY_DEFAULTS)
        for case in load_cases(skills=list(PHASES)):
            self.assertIs(default_checks(case), DEFAULT_CHECKS, case.id)
            self.assertEqual(WRITABLE[case.skill], self.LEGACY_WRITABLE[case.skill])

    def test_nwork_defaults(self) -> None:
        names = [c["check"] for c in NWORK_DEFAULT_CHECKS]
        self.assertEqual(names[:2], ["skill_loaded", "only_touched"])
        self.assertNotIn("questions_format", names)
        for case in load_cases(skills=[NWORK]):
            self.assertIs(default_checks(case), NWORK_DEFAULT_CHECKS)
            self.assertEqual(case.bundle, "ndev-next")

    def test_run_checks_uses_case_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "tree"
            materialize("nwork-working", tree)
            for case, expected in ((_case(), DEFAULT_CHECKS), (_nwork_case(), NWORK_DEFAULT_CHECKS)):
                ctx = RunContext(case=case, config="with_skill", before=tree, after=tree,
                                 changes=diff_trees(tree, tree))
                texts = [r.text for r in run_checks(ctx)]
                self.assertEqual(len(texts), len(expected))
                self.assertEqual(texts[2], checks.CHECKS[expected[2]["check"]][1].format(case=case))

    def test_nwork_writable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            before, after = Path(tmp) / "before", Path(tmp) / "after"
            materialize("nwork-working", before)
            materialize("nwork-working", after)
            (after / ITEMS / "F3-new.md").write_text("x")
            (after / "textkit" / "slug.py").write_text("x")
            ctx = RunContext(case=_nwork_case(), config="with_skill", before=before, after=after,
                             changes=diff_trees(before, after))
            self.assertTrue(checks.CHECKS["only_touched"][0](ctx)[0])
            (after / ".ndev" / "brief.md").write_text("x")
            ctx.changes = diff_trees(before, after)
            self.assertFalse(checks.CHECKS["only_touched"][0](ctx)[0])

    def test_cases_load_for_both_formats(self) -> None:
        skills = {c.skill for c in load_cases()}
        self.assertLessEqual(set(PHASES) | {NWORK}, skills)


class InstallTest(unittest.TestCase):
    """A run installs only the bundle of its case's skill, with bundled references."""

    def test_working_tree_bundles(self) -> None:
        config = Config("with_skill", SKILLS_ROOT)
        self.assertEqual(config.skills_for(NWORK), [SKILL_DIRS[NWORK]])
        self.assertEqual(config.skills_for("nbuild"), sorted(SKILL_DIRS[s] for s in PHASES))
        self.assertEqual(Config("no_skill", None).skills_for(NWORK), [])

    def test_references_are_installed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            make_home(home, Config("with_skill", SKILLS_ROOT).skills_for(NWORK))
            installed = home / ".config" / "opencode" / "skills"
            self.assertEqual(sorted(p.name for p in installed.iterdir()), [NWORK])
            self.assertTrue((installed / NWORK / "references" / "records.md").is_file())
            self.assertTrue((installed / NWORK / "scripts" / "check_records.py").is_file())
            # Every relative link of the installed SKILL.md and references resolves inside the installed folder.
            for doc in (installed / NWORK).rglob("*.md"):
                text = re.sub(r"^```.*?^```", "", doc.read_text(), flags=re.M | re.S)
                text = re.sub(r"`[^`\n]*`", "", text)
                for target in re.findall(r"\]\(((?!#|https?:)[^)#\s]+)", text):
                    self.assertTrue((doc.parent / target).is_file(), f"{doc.name}: {target}")

    def test_installed_skills_are_reachable(self) -> None:
        # external_directory: deny once also blocked the installed references/ (Phase 4, nwork-1).
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            make_home(home, [])
            config = json.loads((home / ".config" / "opencode" / "opencode.json").read_text())
            rules = list(config["permission"]["external_directory"].items())
            self.assertEqual(rules[0], ("*", "deny"))
            self.assertEqual(rules[-1], (f"{home}/.config/opencode/skills/*", "allow"))

    def test_old_flat_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skills"
            for name in (*PHASES, "other"):
                (root / name).mkdir(parents=True)
                (root / name / "SKILL.md").write_text("x")
            config = Config("rev-abc", root)
            self.assertEqual([p.name for p in config.skills_for("nplan")], sorted(PHASES))
            self.assertEqual(config.skills_for(NWORK), [])

    def test_bundle_map(self) -> None:
        self.assertEqual({BUNDLE[s] for s in PHASES}, {"ndev"})
        self.assertEqual(BUNDLE[NWORK], "ndev-next")
        for skill, folder in SKILL_DIRS.items():
            self.assertTrue((folder / "SKILL.md").is_file(), skill)


class PromptsTest(unittest.TestCase):
    """Simulated-user and judge context per format; the ndev wording is unchanged."""

    def test_simulated_user_scope_rule(self) -> None:
        legacy = user_prompt(_case(skill="nbuild", user_script="s"), "c")
        self.assertIn("- This test covers only the `nbuild` phase. Never ask the agent", legacy)
        nwork = user_prompt(_nwork_case(user_script="s"), "c")
        self.assertIn("This test covers the `nwork` skill", nwork)
        self.assertNotIn("phase. Never ask", nwork)
        for text in (legacy, nwork):
            self.assertNotIn("{", text.replace("{{", ""))

    def test_judge_context(self) -> None:
        self.assertEqual(FORMAT_HELP["ndev"], "")
        self.assertIn("ndev-next/1", FORMAT_HELP["ndev-next"])
        self.assertEqual(NWORK_MODE_HELP["simulated"], MODE_HELP["simulated"])
        self.assertNotEqual(NWORK_MODE_HELP["gate"], MODE_HELP["gate"])


if __name__ == "__main__":
    unittest.main()
