# D3: An empty slug raises ValueError

Status: decided
Validity: needs-revalidation
Topics: slugify, errors
Serves: [O1](O1-slugify-function.md)

## Options

- Return `""`. Silent: callers can build broken URLs.
- Raise `ValueError("slug is empty")`. Explicit.

## Choice

Raise `ValueError("slug is empty")` when nothing is left after cleaning, for example for `"!!!"` or `"Привет"`. A `max_length` below 1 also raises `ValueError`.

## Rationale

An empty slug is never a usable URL part; the caller must decide what to do.

## Evidence

[F1](F1-accent-helper.md): non-Latin text has nothing left after cleaning.

## Decided by

user (2026-10-05): "An empty slug is an error. Raise ValueError."

## History

- 2026-10-05: created as proposed.
- 2026-10-05: decided by the user.
- 2026-10-07: needs revalidation: [F3](F3-other-scripts.md) is new evidence on the titles that give an empty slug. Not reassessed yet.
