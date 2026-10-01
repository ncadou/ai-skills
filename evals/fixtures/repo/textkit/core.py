"""Core text helpers."""

import re
import unicodedata

__all__ = ["normalize_whitespace", "strip_accents"]

_WHITESPACE = re.compile(r"\s+")


def normalize_whitespace(text: str) -> str:
    """Collapse every run of whitespace to one space and trim both ends.

    :param text: Text to normalize.
    :return: The normalized text.
    :raises TypeError: When ``text`` is not a string.
    """
    if not isinstance(text, str):
        raise TypeError(f"expected str, got {type(text).__name__}")

    return _WHITESPACE.sub(" ", text).strip()


def strip_accents(text: str) -> str:
    """Remove combining marks, so that accented Latin letters become plain.

    Decompose with NFKD, then drop the combining characters. Letters with no
    decomposition (for example ``ß`` or non-Latin scripts) pass through.

    :param text: Text to strip.
    :return: The text without combining marks.
    :raises TypeError: When ``text`` is not a string.
    """
    if not isinstance(text, str):
        raise TypeError(f"expected str, got {type(text).__name__}")

    decomposed = unicodedata.normalize("NFKD", text)

    return "".join(c for c in decomposed if not unicodedata.combining(c))
