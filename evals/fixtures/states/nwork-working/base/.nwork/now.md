# Now: textkit slugify

Format: nwork/1
Updated: 2026-10-05

## Goal

A `slugify` function turns titles into URL slugs ([O1](items/O1-slugify-function.md)), and the command line exposes it ([O2](items/O2-slugify-command.md)).

## Direction

`slugify` reuses `strip_accents` and treats every other non-alphanumeric character as a separator ([D1](items/D1-non-ascii-separators.md)). `max_length` cuts at the last hyphen ([D2](items/D2-cut-at-last-hyphen.md)), and an empty slug raises `ValueError` ([D3](items/D3-empty-slug-error.md)). The command is one more argparse subcommand ([F2](items/F2-cli-subcommands.md)).

## Implemented and verified

None.

## Needs you

- [D4](items/D4-cli-error-output.md): how the command reports an empty slug. Recommended: `textkit: error: <message>` on stderr, exit code 2.

## Eligible work

- [T1](items/T1-slugify-function.md): the `slugify` function, with its tests.

## Next

Build [T1](items/T1-slugify-function.md). [T2](items/T2-slugify-command.md) waits for D4.

## Working agreement

[P1](items/P1-working-agreement.md): focus errors; detail brief. Reserved for you: what command-line users see, changes to decided contracts, and accepting slices.
