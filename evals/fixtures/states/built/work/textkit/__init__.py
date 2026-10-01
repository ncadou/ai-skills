"""Small, dependency-free text utilities."""

from textkit.core import normalize_whitespace, strip_accents
from textkit.slug import slugify

__all__ = ["normalize_whitespace", "slugify", "strip_accents"]
