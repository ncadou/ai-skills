# Now: textkit slugify

Format: nwork/1
Updated: 2026-10-06

## Goal

A `slugify` function turns titles into URL slugs ([O1](items/O1-slugify-function.md)), the command line exposes it ([O2](items/O2-slugify-command.md)), and a batch command slugifies stdin line by line ([O3](items/O3-batch-command.md)).

## Direction

`slugify` reuses `strip_accents` and treats every other non-alphanumeric character as a separator ([D1](items/D1-non-ascii-separators.md)). `max_length` cuts at the last hyphen ([D2](items/D2-cut-at-last-hyphen.md)), and an empty slug raises `ValueError` ([D3](items/D3-empty-slug-error.md)). The commands are argparse subcommands ([F2](items/F2-cli-subcommands.md)). The batch command's behavior on unusual lines is still open.

## Implemented and verified

None.

## Needs you

- [D4](items/D4-cli-error-output.md): how the command reports an empty slug. Recommended: `textkit: error: <message>` on stderr, exit code 2.
- [Q2](items/Q2-blank-lines.md): what the batch command prints for a blank line.
- [Q3](items/Q3-lines-without-slug.md): what it prints for a line with no slug.
- [Q4](items/Q4-stop-or-continue.md): whether such a line stops it, and its exit code.
- [Q5](items/Q5-reader-stops-early.md): what it does when its reader stops early, as with `| head -1`.

## Eligible work

- [T1](items/T1-slugify-function.md): the `slugify` function, with its tests.

## Next

Settle the batch command's questions, Q2 to Q5, before its slice is written. [T1](items/T1-slugify-function.md) is ready to build; [T2](items/T2-slugify-command.md) waits for D4.

## Working agreement

[P1](items/P1-working-agreement.md): focus errors; detail brief. Reserved for you: what command-line users see, changes to decided contracts, and accepting slices.
