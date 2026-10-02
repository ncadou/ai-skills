"""Tests for harness.checks and the fixture states.

Run from ``evals/``: ``python3 -m unittest discover -s tests -t . -v``
"""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from harness import checks
from harness.cases import SKILLS_DIR, Case, load_cases
from harness.checks import RunContext, approval_values, run_checks, template_patterns
from harness.fixtures import diff_trees, list_states, materialize

# Template name and artifact glob, per skill.
TEMPLATES = {
    "nstart": ("Brief template", ".ndev/brief.md"),
    "nlearn": ("Discovery template", ".ndev/discovery.md"),
    "ndesign": ("Design template", ".ndev/design.md"),
    "nplan": ("Plan template", ".ndev/plan.md"),
}


def _case(**overrides: object) -> Case:
    """Build a minimal case."""
    fields = dict(id="t", skill="nstart", description="", state="empty", mode="delegated", prompt="p")
    fields.update(overrides)

    return Case(**fields)  # type: ignore[arg-type]


class _TreeTest(unittest.TestCase):
    """Base: a before tree and an after tree, both from a state."""

    state = "briefed"

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.before = root / "before"
        self.after = root / "after"
        materialize(self.state, self.before)
        materialize(self.state, self.after)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, rel: str, text: str) -> None:
        """Write ``text`` to ``rel`` in the after tree."""
        path = self.after / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def run_one(self, spec: dict, case: Case | None = None, config: str = "with_skill") -> checks.CheckResult:
        """Run one check spec and return its result."""
        ctx = RunContext(
            case=case or _case(),
            config=config,
            before=self.before,
            after=self.after,
            changes=diff_trees(self.before, self.after),
        )
        fn, label = checks.CHECKS[spec["check"]]
        params = {k: v for k, v in spec.items() if k != "check"}
        passed, evidence = fn(ctx, **params)

        return checks.CheckResult(text=label, passed=passed, evidence=evidence)


class ApprovalsTest(_TreeTest):
    """New approval lines must match the mode."""

    def _brief_with(self, line: str) -> None:
        text = (self.before / ".ndev/brief.md").read_text()
        self.write(".ndev/brief.md", text + f"\n{line}\n")

    def test_existing_approvals_are_not_new(self) -> None:
        self.assertTrue(self.run_one({"check": "approvals"}, _case(mode="gate")).passed)

    def test_gate_rejects_any_new_approval(self) -> None:
        self._brief_with("Approved: agent (delegated: all gates)")
        self.assertFalse(self.run_one({"check": "approvals"}, _case(mode="gate")).passed)

    def test_delegated_rejects_user(self) -> None:
        self._brief_with("Approved: user")
        self.assertFalse(self.run_one({"check": "approvals"}, _case(mode="delegated")).passed)

    def test_delegated_accepts_named_delegation(self) -> None:
        self._brief_with("Approved: agent (delegated: whole phase, per prompt)")
        self.assertTrue(self.run_one({"check": "approvals"}, _case(mode="delegated")).passed)

    def test_template_placeholder_is_invalid(self) -> None:
        self._brief_with("Approved: user | agent (delegated: <scope>)")
        # "user | agent ..." normalizes to "user", which delegated mode rejects.
        self.assertFalse(self.run_one({"check": "approvals"}, _case(mode="delegated")).passed)
        self._brief_with("Approved: yes")
        self.assertFalse(self.run_one({"check": "approvals"}, _case(mode="simulated")).passed)

    def test_value_parsing(self) -> None:
        text = "- nlearn: run (suggested: run; decided by: agent (delegated: phases))\nAccepted by:\n"
        self.assertEqual(approval_values(text), [("decided by", "agent (delegated: phases)")])

    def test_quotes_and_pending_are_not_claims(self) -> None:
        text = "All decisions record `Decided by: user`.\nApproved: pending\nApproved: none yet\n"
        self.assertEqual(approval_values(text), [])


class OnlyTouchedTest(_TreeTest):
    """Writes outside the skill's artifacts fail."""

    def test_allowed_write(self) -> None:
        self.write(".ndev/questions.md", "# Questions\n")
        self.assertTrue(self.run_one({"check": "only_touched"}).passed)

    def test_code_write_fails_for_nstart(self) -> None:
        self.write("textkit/slug.py", "x = 1\n")
        self.assertFalse(self.run_one({"check": "only_touched"}).passed)

    def test_caches_are_ignored(self) -> None:
        self.write("textkit/__pycache__/core.cpython-313.pyc", "")
        self.assertTrue(self.run_one({"check": "only_touched"}).passed)


class QuestionsTest(_TreeTest):
    """The questions ledger format."""

    def _questions(self, *lines: str) -> None:
        self.write(".ndev/questions.md", (self.before / ".ndev/questions.md").read_text() + "\n".join(lines) + "\n")

    def test_backtrack_question_with_stale(self) -> None:
        self._questions("- [ ] Q4: The CLI skeleton is missing. (from nstart/agent, for ndesign) stale: plan.md, T02")
        self.assertTrue(self.run_one({"check": "questions_format"}).passed)
        self.assertTrue(self.run_one({"check": "question_added", "for_phase": "ndesign", "stale": True}).passed)
        self.assertFalse(self.run_one({"check": "question_added", "for_phase": "nlearn"}).passed)

    def test_malformed_line_fails(self) -> None:
        self._questions("- [ ] Q4: missing provenance")
        self.assertFalse(self.run_one({"check": "questions_format"}).passed)

    def test_tick_needs_answer(self) -> None:
        self._questions("- [x] Q4: done? (from nstart/user, for nlearn)")
        self.assertFalse(self.run_one({"check": "questions_format"}).passed)

    def test_questions_ticked(self) -> None:
        text = (self.before / ".ndev/questions.md").read_text()
        self.write(".ndev/questions.md", text.replace("- [ ] Q1: ", "- [x] Q1: ").replace("(for nlearn)", ""))
        self.write(
            ".ndev/questions.md",
            re.sub(r"^(- \[x\] Q1: .*)$", r"\1 → F1", (self.after / ".ndev/questions.md").read_text(), flags=re.M),
        )
        self.assertTrue(self.run_one({"check": "questions_ticked", "ids": ["Q1"], "answer": r"F\d"}).passed)
        self.assertFalse(self.run_one({"check": "questions_ticked", "ids": ["Q1", "Q2"]}).passed)


class IdsTest(_TreeTest):
    """IDs are unique and never deleted."""

    def test_duplicate_objective(self) -> None:
        text = (self.before / ".ndev/brief.md").read_text()
        self.write(".ndev/brief.md", text.replace("- O2:", "- O1:"))
        self.assertFalse(self.run_one({"check": "ids_unique"}).passed)
        self.assertFalse(self.run_one({"check": "ids_preserved"}).passed)

    def test_superseded_objective_is_kept(self) -> None:
        text = (self.before / ".ndev/brief.md").read_text()
        self.write(".ndev/brief.md", text.replace("- O2: ", "- O2: Superseded by O3: merged. ") + "\n- O3: x\n")
        self.assertTrue(self.run_one({"check": "ids_preserved"}).passed)


class ToolCallTest(unittest.TestCase):
    """Checks that read the transcript's tool calls."""

    def _ctx(self) -> RunContext:
        events = [
            {"type": "tool_use", "part": {"tool": "skill", "state": {"input": {"name": "nbuild"}}}},
            {"type": "tool_use", "part": {"tool": "bash", "state": {"input": {"command": "python3 spike.py"}}}},
        ]
        tree = Path(tempfile.gettempdir())

        return RunContext(case=_case(skill="nreview"), config="with_skill", before=tree, after=tree,
                          changes=diff_trees(tree / "missing", tree / "missing"), turns=[events])

    def test_no_tool_call(self) -> None:
        fn, _ = checks.CHECKS["no_tool_call"]
        self.assertFalse(fn(self._ctx(), tool="bash", pattern="python")[0])
        self.assertTrue(fn(self._ctx(), tool="bash", pattern="pytest")[0])

    def test_skill_loaded_by_name(self) -> None:
        fn, _ = checks.CHECKS["skill_loaded"]
        self.assertFalse(fn(self._ctx())[0])
        self.assertTrue(fn(self._ctx(), name="nbuild")[0])

    def test_not_written_in_turn(self) -> None:
        fn, _ = checks.CHECKS["not_written_in_turn"]
        write = {"type": "tool_use", "part": {"tool": "write", "state": {"input": {"filePath": "/w/.ndev/brief.md"}}}}
        read = {"type": "tool_use", "part": {"tool": "read", "state": {"input": {"filePath": "/w/.ndev/brief.md"}}}}
        ctx = self._ctx()
        ctx.turns = [[read], [write]]
        self.assertTrue(fn(ctx, turn=1, path=".ndev/brief.md")[0])
        self.assertFalse(fn(ctx, turn=2, path=".ndev/brief.md")[0])
        self.assertTrue(fn(ctx, turn=2, path=".ndev/design.md")[0])


def _skill_call(name: str) -> dict:
    """A ``skill`` tool call event."""
    return {"type": "tool_use", "part": {"tool": "skill", "state": {"input": {"name": name}}}}


class FidelityGuardTest(unittest.TestCase):
    """The script-level guard flags a simulated user that asks for another phase."""

    def _guard(self, messages: list[str], turns: list[list[dict]], mode: str = "simulated") -> bool | None:
        tree = Path(tempfile.gettempdir())
        ctx = RunContext(case=_case(skill="ndesign", mode=mode), config="with_skill", before=tree, after=tree,
                         changes=diff_trees(tree / "missing", tree / "missing"), turns=turns, messages=messages)
        result = checks.fidelity_guard(ctx)
        self.assertEqual(result.kind, "fidelity")

        return result.passed

    def test_request_followed_by_load_fails(self) -> None:
        turns = [[_skill_call("ndesign")], [_skill_call("nplan")]]
        self.assertFalse(self._guard(["Use the ndesign skill.", "Approved. Proceed to nplan."], turns))

    def test_mention_without_load_passes(self) -> None:
        turns = [[_skill_call("ndesign")], []]
        self.assertTrue(self._guard(["Use the ndesign skill.", "Approved; nplan can wait."], turns))

    def test_load_without_mention_passes(self) -> None:
        # The agent went ahead on its own: a skill failure, not the user's.
        turns = [[_skill_call("ndesign")], [_skill_call("nplan")]]
        self.assertTrue(self._guard(["Use the ndesign skill.", "Approved."], turns))

    def test_own_skill_and_first_message_are_ignored(self) -> None:
        turns = [[_skill_call("nplan")], [_skill_call("ndesign")]]
        self.assertTrue(self._guard(["Use ndesign, then nplan.", "Go on with ndesign."], turns))

    def test_not_simulated(self) -> None:
        self.assertIsNone(self._guard(["Use the ndesign skill."], [[]], mode="gate"))


class TemplateTest(unittest.TestCase):
    """template_patterns reads the SKILL.md templates."""

    def test_brief_headings(self) -> None:
        patterns = template_patterns((SKILLS_DIR / "nstart/SKILL.md").read_text(), "Brief template")
        self.assertTrue(patterns[0].search("# Brief: slugify"))
        self.assertIn("## Control", [p.pattern.strip("^$").replace("\\s*", "").replace("\\", "") for p in patterns])

    def test_ids_generalize(self) -> None:
        patterns = template_patterns((SKILLS_DIR / "ndesign/SKILL.md").read_text(), "Design template")
        self.assertTrue(any(p.search("### D7: Cut rule") for p in patterns))

    def test_unknown_template(self) -> None:
        with self.assertRaises(ValueError):
            template_patterns("# nothing\n", "Brief template")


class FixtureStatesTest(unittest.TestCase):
    """Every state is valid by the same checks the evals apply."""

    def test_states_pass_format_checks(self) -> None:
        for state in list_states():
            with self.subTest(state=state), tempfile.TemporaryDirectory() as tmp:
                tree = Path(tmp) / "tree"
                materialize(state, tree)
                ctx = RunContext(
                    case=_case(state=state, mode="simulated"),
                    config="with_skill",
                    before=tree,
                    after=tree,
                    changes=diff_trees(tree, tree),
                )
                for result in run_checks(ctx)[2:]:  # skip skill_loaded, only_touched
                    self.assertIsNot(result.passed, False, f"{result.text}: {result.evidence}")

    def test_artifacts_match_templates(self) -> None:
        for state in list_states():
            with self.subTest(state=state), tempfile.TemporaryDirectory() as tmp:
                tree = Path(tmp) / "tree"
                materialize(state, tree)
                for skill, (template, rel) in TEMPLATES.items():
                    if state in ("stale-cycle", "designed-gap") or not (tree / rel).is_file():
                        continue  # stale-cycle skipped design; designed-gap is broken on purpose

                    text = (tree / rel).read_text()
                    for pattern in template_patterns((SKILLS_DIR / skill / "SKILL.md").read_text(), template):
                        self.assertRegex(text, pattern, f"{state}: {rel}")

                for task in (tree / ".ndev/tasks").glob("*.md") if (tree / ".ndev/tasks").is_dir() else ():
                    for pattern in template_patterns((SKILLS_DIR / "nplan/SKILL.md").read_text(), "Task template"):
                        self.assertRegex(task.read_text(), pattern, f"{state}: {task.name}")

    def test_work_overlay_is_uncommitted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "tree"
            materialize("built", tree)
            import subprocess

            status = subprocess.run(["git", "status", "--porcelain"], cwd=tree, capture_output=True, text=True).stdout
            self.assertIn("textkit/slug.py", status)
            self.assertNotIn(".ndev", status)


class CasesTest(unittest.TestCase):
    """Every evals.json file loads and validates."""

    def test_load_all(self) -> None:
        cases = load_cases()
        self.assertTrue(cases)
        for case in cases:
            for spec in case.checks:
                self.assertIn(spec["check"], checks.CHECKS, case.id)


if __name__ == "__main__":
    unittest.main()
