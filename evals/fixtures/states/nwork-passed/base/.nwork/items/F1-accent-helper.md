# F1: strip_accents makes accented Latin letters plain

Status: verified
Validity: current
Topics: slugify
Serves: [O1](O1-slugify-function.md)

## Claim

`textkit.core.strip_accents` turns every Latin letter with a diacritic (an accent, a cedilla, a stroke) into its plain ASCII letter. Only `ß` and the letters of non-Latin scripts, such as Cyrillic, pass through unchanged.

## Evidence

- Checked: `textkit/core.py` (`strip_accents`: NFKD, then drop combining marks), and a spike.
- Source: `python3 -c 'from textkit import strip_accents as s; print(repr(s("Crème Brûlée")), repr(s("ß")), repr(s("Привет")))'`
- Observed: `'Creme Brulee' 'ß' 'Привет'`

## History

- 2026-10-05: created as verified.
