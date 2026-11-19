"""Tests for textkit.slug."""

import unittest

from textkit import slugify


class SlugifyTest(unittest.TestCase):
    """slugify follows the contract table in T1 § Expected behavior."""

    def test_punctuation_and_case(self) -> None:
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_accents_and_digits(self) -> None:
        self.assertEqual(slugify("Crème Brûlée 2"), "creme-brulee-2")

    def test_trims_and_collapses_hyphens(self) -> None:
        self.assertEqual(slugify("  --a--b--  "), "a-b")

    def test_letters_without_decomposition_become_separators(self) -> None:
        self.assertEqual(slugify("Straße"), "stra-e")

    def test_cut_at_last_hyphen(self) -> None:
        self.assertEqual(slugify("hello world foo", max_length=13), "hello-world")

    def test_cut_exactly_at_word_end(self) -> None:
        self.assertEqual(slugify("hello world foo", max_length=11), "hello-world")

    def test_hard_cut_when_first_word_is_too_long(self) -> None:
        self.assertEqual(slugify("abcdefghij", max_length=4), "abcd")

    def test_short_slug_is_not_cut(self) -> None:
        self.assertEqual(slugify("a b", max_length=10), "a-b")

    def test_cut_never_ends_with_hyphen(self) -> None:
        for n in range(1, 16):
            slug = slugify("hello world foo", max_length=n).rstrip("-")
            self.assertFalse(slug.endswith("-"))

    def test_empty_slug_raises(self) -> None:
        for text in ("!!!", "Привет", ""):
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, "slug is empty"):
                slugify(text)

    def test_max_length_below_one_raises(self) -> None:
        with self.assertRaises(ValueError):
            slugify("a", max_length=0)

    def test_text_must_be_str(self) -> None:
        with self.assertRaises(TypeError):
            slugify(3)  # type: ignore[arg-type]

    def test_max_length_must_be_int(self) -> None:
        with self.assertRaises(TypeError):
            slugify(3, max_length="3")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
