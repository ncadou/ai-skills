"""URL slugs."""

import re

from textkit.core import strip_accents

__all__ = ["slugify"]

_SEPARATORS = re.compile(r"[^a-z0-9]+")


def slugify(text: str, max_length: int | None = None) -> str:
    """Turn ``text`` into a lowercase ASCII, hyphen-separated URL slug.

    :param text: Text to turn into a slug.
    :param max_length: Longest slug allowed; ``None`` means no limit.
    :return: A slug at most ``max_length`` characters long.
    :raises TypeError: When ``text`` is not a ``str``.
    """
    if not isinstance(text, str):
        raise TypeError(f"expected str, got {type(text).__name__}")

    slug = _SEPARATORS.sub("-", strip_accents(text).lower()).strip("-")
    if max_length is not None:
        slug = slug[:max_length]

    return slug
