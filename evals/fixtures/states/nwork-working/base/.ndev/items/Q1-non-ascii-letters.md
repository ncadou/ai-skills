# Q1: What becomes of letters that strip_accents leaves alone?

Status: resolved
Validity: current
Topics: slugify

## Question

`ß`, Cyrillic, and CJK letters survive `strip_accents` ([F1](F1-accent-helper.md)). Must `slugify` drop them, keep them, or transliterate them?

## Who answers

user: it sets what slugs look like, and transliteration is out of scope for [O1](O1-slugify-function.md).

## History

- 2026-10-05: created as open.
- 2026-10-05: resolved by a decision of the user.
