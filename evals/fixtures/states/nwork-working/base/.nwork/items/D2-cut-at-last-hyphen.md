# D2: max_length cuts at the last hyphen

Status: decided
Validity: current
Topics: slugify
Serves: [O1](O1-slugify-function.md)

## Options

- Hard cut at `max_length`. Simple, but can split a word and end with a hyphen.
- Cut at the last hyphen within `max_length`. Keeps whole words.

## Choice

Cut at the last hyphen within `max_length`. When the first word alone is longer than `max_length`, hard-cut that word. A slug never ends with a hyphen.

## Rationale

Readable slugs; the hard cut only applies when no whole word fits.

## Evidence

Contract rows in [T1](T1-slugify-function.md) § Expected behavior.

## Decided by

user (2026-10-05): "Keep whole words when you cut; hard-cut only a single word that is too long."

## History

- 2026-10-05: created as proposed.
- 2026-10-05: decided by the user.
