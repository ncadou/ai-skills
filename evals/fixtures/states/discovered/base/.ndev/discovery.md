# Discovery: slugify

## Problem & Objectives

Serves O1 (`slugify` function) and O2 (`slugify` CLI subcommand) from `.ndev/brief.md`.

## Reference Patterns

### F1: Accent handling lives in `strip_accents`

- Source: `textkit/core.py` (`strip_accents`: NFKD, then drop combining marks)
- Applies to: `slugify` text cleaning
- Answers: Q1

### F2: CLI subcommands use argparse subparsers with a `handler` default

- Source: `textkit/__main__.py` (`commands.add_parser(...)`, `set_defaults(handler=...)`, handler returns the exit code)
- Applies to: `slugify` subcommand
- Answers: Q2

### F3: Public helpers raise `TypeError` for non-`str` input and document errors with `:raises:`

- Source: `textkit/core.py` (`normalize_whitespace`, `strip_accents`)
- Applies to: `slugify` error contract

### F4: Tests use `unittest`, one `TestCase` per function, in `tests/`

- Source: `tests/test_core.py`; run with `python3 -m unittest discover -s tests -t . -v`
- Applies to: all new tests

## Assumptions & Validation

### F5: `strip_accents` turns accented Latin letters into ASCII

- Source: spike `.ndev/scratch/spike_accents.py`, observed output: `'Creme Brulee' 'ß' 'Привет' 'fi'`
- Status: verified
- Answers: Q1

### F6: Slugs keep digits; an empty result is an error, not an empty string

- Source: user
- Status: verified
- Answers: Q3

## Identified Risks & Spikes

### F7: Letters with no decomposition (`ß`, Cyrillic, CJK) survive `strip_accents` and must be dropped by the slug filter

- Source: spike `.ndev/scratch/spike_accents.py` (`'ß'` and `'Привет'` pass through unchanged)
- Ruling: accepted — by user

### F8: A title made only of such letters yields an empty slug

- Source: edge case derived from F7 (`slugify("Привет")` would have nothing left)
- Ruling: accepted — by user

## Walkthrough

- F1–F8: Approved: user
