# Brief: slugify

## Request

> Add a `slugify` function to textkit that turns titles into URL slugs, with an optional maximum length. Also expose it on the command line, like `normalize`.

## Objectives

- O1: `textkit.slugify(text, max_length=None)` turns a title into a lowercase ASCII, hyphen-separated URL slug, and can cap its length.
- O2: `python3 -m textkit slugify <text> [--max-length N]` prints the slug.

Approved: user

## Non-goals

- No third-party dependencies.
- No transliteration of non-Latin scripts (Cyrillic, CJK, ...).
- No change to the existing `normalize` command.

Approved: user

## Approach (provisional)

1. Reuse the existing accent handling in `textkit/core.py` to build `slugify` (serves: O1)
2. Add a `slugify` subcommand next to `normalize` in `textkit/__main__.py` (serves: O2)
3. Unit tests for both, in the existing `unittest` style (serves: O1, O2)

Approved: user

## Phases

- nlearn: run — the accent helper and the CLI wiring need checking (suggested: run; decided by: user)
- ndesign: run — truncation and empty-result behavior are open choices (suggested: run; decided by: user)
- nplan: run — two slices, library then CLI (suggested: run; decided by: user)
- nbuild: run
- nreview: run — each slice gets a verdict (suggested: run; decided by: user)

## Control

- ndesign decisions: agent decides
- ndesign gates: gate waived
