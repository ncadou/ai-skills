"""Spike: how does strip_accents treat accented, unaccented, and non-Latin text?"""

from textkit import strip_accents

print(repr(strip_accents("Crème Brûlée")), repr(strip_accents("ß")), repr(strip_accents("Привет")), repr(strip_accents("ﬁ")))
