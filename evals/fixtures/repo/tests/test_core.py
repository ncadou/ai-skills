"""Tests for textkit.core and the CLI."""

import contextlib
import io
import unittest

from textkit import normalize_whitespace, strip_accents
from textkit.__main__ import main


class NormalizeWhitespaceTest(unittest.TestCase):
    """normalize_whitespace collapses and trims."""

    def test_collapses_and_trims(self) -> None:
        self.assertEqual(normalize_whitespace("  a \t b\n"), "a b")

    def test_rejects_non_str(self) -> None:
        with self.assertRaises(TypeError):
            normalize_whitespace(3)  # type: ignore[arg-type]


class StripAccentsTest(unittest.TestCase):
    """strip_accents removes combining marks only."""

    def test_latin(self) -> None:
        self.assertEqual(strip_accents("Crème Brûlée"), "Creme Brulee")

    def test_no_decomposition_passes_through(self) -> None:
        self.assertEqual(strip_accents("ß"), "ß")


class CliTest(unittest.TestCase):
    """The CLI dispatches subcommands."""

    def test_normalize(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["normalize", "  a   b "])
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue(), "a b\n")


if __name__ == "__main__":
    unittest.main()
