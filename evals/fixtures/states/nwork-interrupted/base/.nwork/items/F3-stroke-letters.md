# F3: Latin letters with strokes and ligatures do not decompose

Status: verified
Validity: current
Topics: slugify

## Claim

`strip_accents` removes combining marks only. Latin letters with a stroke (`ł`, `ø`, `đ`) and ligatures (`æ`, `œ`) have no decomposition, so they pass through, and `slugify` turns them into separators: `Łódź` becomes `odz`, and `Smørrebrød` becomes `sm-rrebr-d`.

## Evidence

- Checked: the user's report, user (2026-10-07): "A colleague says Polish names come out broken: Łódź becomes odz." Then a spike on the built code.
- Source: `python3 -c 'from textkit import slugify, strip_accents as s; [print(repr(t), repr(s(t)), repr(slugify(t))) for t in ["Łódź", "Smørrebrød", "Đorđe", "Kraków"]]'`
- Observed: `'Łódź' 'Łodz' 'odz'`, `'Smørrebrød' 'Smørrebrød' 'sm-rrebr-d'`, `'Đorđe' 'Đorđe' 'or-e'`, `'Kraków' 'Krakow' 'krakow'`

## History

- 2026-10-07: created as verified, from the user's report and the spike.
