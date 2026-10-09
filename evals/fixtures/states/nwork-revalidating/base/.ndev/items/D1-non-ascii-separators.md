# D1: Characters outside a-z and 0-9 become separators

Status: decided
Validity: needs-revalidation
Topics: slugify
Depends on: [F1](F1-accent-helper.md)
Serves: [O1](O1-slugify-function.md)
Answers: [Q1](Q1-non-ascii-letters.md)

## Options

- Reuse `strip_accents`, then treat every character outside `[a-z0-9]` as a separator. No dependency; `ß` and non-Latin letters become separators.
- Add a transliteration library. Better coverage, but [O1](O1-slugify-function.md) excludes dependencies.

## Choice

Reuse `strip_accents`, lowercase, then replace each run of characters outside `[a-z0-9]` with one hyphen, and trim hyphens at both ends. `slugify("Straße")` is `"stra-e"`.

## Rationale

No dependency, and the accent handling is already tested. Only `ß` and non-Latin letters become separators ([F1](F1-accent-helper.md)); the user accepts that loss.

## Evidence

[F1](F1-accent-helper.md).

## Decided by

user (2026-10-05): "Drop anything that isn't a plain letter or digit, Straße can become stra-e."

## History

- 2026-10-05: created as proposed.
- 2026-10-05: decided by the user.
- 2026-10-07: needs revalidation: [F3](F3-other-scripts.md) is new evidence on the letters that this rule turns into separators. Not reassessed yet.
