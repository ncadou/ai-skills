# Now: textkit slugify

Format: ndev-next/1
Updated: 2026-10-06

## Goal

A `slugify` function turns titles into URL slugs ([O1](items/O1-slugify-function.md)), the command line exposes it ([O2](items/O2-slugify-command.md)), and `normalize_whitespace` can keep line breaks ([O3](items/O3-keep-newlines.md)).

## Direction

`slugify` reuses `strip_accents` and treats every other non-alphanumeric character as a separator ([D1](items/D1-non-ascii-separators.md)). `max_length` cuts at the last hyphen ([D2](items/D2-cut-at-last-hyphen.md)), and an empty slug raises `ValueError` ([D3](items/D3-empty-slug-error.md)). The command is one more argparse subcommand ([F2](items/F2-cli-subcommands.md)). `keep_newlines` normalizes each line on its own ([D5](items/D5-per-line-normalization.md)).

## Implemented and verified

- [T1](items/T1-slugify-function.md): the `slugify` function; review passed on 2026-10-06. Waits for your acceptance.

## Needs you

- [D4](items/D4-cli-error-output.md): how the command reports an empty slug. Recommended: `textkit: error: <message>` on stderr, exit code 2.
- [T1](items/T1-slugify-function.md): accept the slugify function, or name what to change.

## Eligible work

- [T3](items/T3-keep-newlines.md): the `keep_newlines` option, with its tests.

## Next

Build [T3](items/T3-keep-newlines.md). [T2](items/T2-slugify-command.md) waits for D4.

## Working agreement

[P1](items/P1-working-agreement.md): focus errors; detail brief. Reserved for you: what command-line users see, changes to decided contracts, and accepting slices.
