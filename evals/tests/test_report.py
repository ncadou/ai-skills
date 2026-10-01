"""Tests for harness.report."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from harness.report import build_report, deltas


class DeltasTest(unittest.TestCase):
    """Deltas pair like with like."""

    def test_single_model(self) -> None:
        self.assertEqual(deltas(["with_skill", "no_skill"]), [("with_skill", "no_skill")])

    def test_two_models_with_baseline(self) -> None:
        configs = ["with_skill@a", "no_skill@a", "with_skill@b", "no_skill@b"]
        self.assertEqual(
            deltas(configs),
            [("with_skill@a", "no_skill@a"), ("with_skill@b", "no_skill@b"), ("with_skill@a", "with_skill@b")],
        )


class OffScriptTest(unittest.TestCase):
    """Off-script runs are left out of pass rates and listed in the notes."""

    def test_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            iteration = Path(tmp)
            for n, (rate, off) in enumerate([(1.0, False), (0.0, True)], 1):
                run = iteration / "nbuild-x" / "with_skill" / f"run-{n}"
                run.mkdir(parents=True)
                (run / "metrics.json").write_text(json.dumps({
                    "case": "nbuild-x", "skill": "nbuild", "config": "with_skill", "ended": "done",
                    "tokens": 10, "cost": 0, "duration_s": 1,
                }))
                (run / "grading.json").write_text(json.dumps({
                    "expectations": [{"text": "t", "passed": rate == 1.0, "evidence": "", "kind": "script"}],
                    "summary": {"pass_rate": rate, "off_script": off},
                }))

            data = build_report(iteration)

        stats = data["totals"]["with_skill"]
        self.assertEqual((stats["runs"], stats["off_script"], stats["pass_rate"]), (2, 1, 1.0))
        self.assertTrue(any(n.startswith("off script") for n in data["notes"]))


if __name__ == "__main__":
    unittest.main()
