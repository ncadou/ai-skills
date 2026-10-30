# F3: Greek, Japanese, and Arabic titles give an empty slug

Status: verified
Validity: current
Topics: slugify, errors
Serves: [O1](O1-slugify-function.md)

## Claim

`strip_accents` leaves Greek, Japanese, and Arabic letters unchanged, as it does Cyrillic ([F1](F1-accent-helper.md)). `slugify` turns them into separators, so a title written only in one of these scripts raises `ValueError("slug is empty")`.

## Evidence

- Checked: the user's question, user (2026-10-07): "What do Greek, Japanese, or Arabic titles give?" Then two spikes on the built code.
- Source: `python3 -c 'from textkit import strip_accents as s; [print(repr(t), repr(s(t))) for t in ["ΑΘΗΝΑ", "東京", "القاهرة"]]'`
- Observed: `'ΑΘΗΝΑ' 'ΑΘΗΝΑ'`, `'東京' '東京'`, `'القاهرة' 'القاهرة'`
- Source: `python3 -c "from textkit import slugify; slugify('<title>')"`, once for each of the three titles.
- Observed: `ValueError: slug is empty`, for each of the three.

## History

- 2026-10-07: created as verified, from the user's question and the spikes.
