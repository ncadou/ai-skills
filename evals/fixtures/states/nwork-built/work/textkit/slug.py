"""URL slugs."""

import re

from textkit.core import strip_accents

__all__ = ["slugify"]

_SEPARATORS = re.compile(r"[^a-z0-9]+")


def slugify(text: str, max_length: int | None = None) -> str:
    """Turn ``text`` into a lowercase ASCII, hyphen-separated URL slug.

    :param text: Text to turn into a slug.
    :param max_length: Longest slug allowed; ``None`` means no limit.
    :return: A non-empty slug that matches ``[a-z0-9]+(-[a-z0-9]+)*``
        and is at most ``max_length`` characters long.
    :raises TypeError: When ``text`` is not a ``str``, or ``max_length`` is
        neither ``None`` nor an ``int``.
    :raises ValueError: When ``max_length`` is less than 1, or the slug is
        empty (message: ``"slug is empty"``).
    """
    if not isinstance(text, str):
        raise TypeError(f"expected str, got {type(text).__name__}")

    if max_length is not None:
        if not isinstance(max_length, int):
            raise TypeError(f"expected int or None, got {type(max_length).__name__}")

        if max_length < 1:
            raise ValueError("max_length must be at least 1")

    # D1: letters with no decomposition (ß, Cyrillic, ...) become separators.
    slug = _SEPARATORS.sub("-", strip_accents(text).lower()).strip("-")
    if not slug:
        raise ValueError("slug is empty")

    if max_length is not None and len(slug) > max_length:
        slug = _cut(slug, max_length)

    return slug


def _cut(slug: str, max_length: int) -> str:
    """Cut ``slug`` to ``max_length`` at the last hyphen, keeping whole words (D2).

    When the first word alone is longer than ``max_length``, hard-cut it.
    """
    # A hyphen right after the limit means the limit already ends a word.
    if slug[max_length] == "-":
        return slug[:max_length]

    head = slug[:max_length]
    boundary = head.rfind("-")
    if boundary == -1:
        return head

    return head[:boundary]
