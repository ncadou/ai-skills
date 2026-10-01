"""Tests for textkit.slug."""

import unittest

from textkit import slugify


class SlugifyTest(unittest.TestCase):
    """slugify basics."""

    def test_punctuation_and_case(self) -> None:
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_accents(self) -> None:
        self.assertEqual(slugify("Crème Brûlée"), "creme-brulee")

    def test_max_length(self) -> None:
        result = slugify("hello world foo", max_length=13)
        self.assertIsInstance(result, str)
        self.assertLessEqual(len(result), 13)

    def test_type_error(self) -> None:
        with self.assertRaises(TypeError):
            slugify(3)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
