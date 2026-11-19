# F1: strip_accents makes accented Latin letters plain

Status: verified
Validity: current
Topics: slugify
Serves: [O1](O1-slugify-function.md)

## Claim

`textkit.core.strip_accents` turns a Latin letter with an accent or a cedilla into its plain ASCII letter. Letters with no decomposition pass through unchanged: letters with a stroke (`Ł`, `Ø`, `đ`), `ß`, `æ`, `œ`, `þ`, and the letters of non-Latin scripts, such as Cyrillic.

## Evidence

- Checked: `textkit/core.py` (`strip_accents`: NFKD, then drop combining marks), and a spike.
- Source: `python3 -c 'from textkit import strip_accents as s; print(repr(s("Crème Brûlée")), repr(s("Łódź Øre")), repr(s("ß")), repr(s("Привет")))'`
- Observed: `'Creme Brulee' 'Łodz Øre' 'ß' 'Привет'`

## History

- 2026-10-05: created as verified.
