# O3: A batch slugify command

Status: active
Validity: current
Topics: cli, batch

## Outcome

`python3 -m textkit slugify-lines [--max-length N]` reads titles from stdin, one per line, and prints their slugs to stdout, so that scripts can slugify a whole file in one call.

## Out of scope

- Reading from files named on the command line.
- Any change to the existing `normalize` command, or to `slugify` itself.

## History

- 2026-10-06: created as active, from the user's request.
