# D4: How the slugify command reports an empty slug

Status: proposed
Validity: needs-revalidation
Topics: cli, errors
Depends on: [D3](D3-empty-slug-error.md)
Serves: [O2](O2-slugify-command.md)

## Options

- Print `textkit: error: <message>` to stderr and exit with code 2, like argparse usage errors.
- Print the message alone to stderr and exit with code 1.

## Recommendation

`textkit: error: <message>` on stderr, exit code 2: one format and one code for every input error the command reports.

## Rationale

Scripts can tell input errors from success by the exit code, which matches argparse's own, and the message has the same shape as argparse's.

## Evidence

- Checked: an argparse usage error of the existing command.
- Source: `python3 -m textkit normalize`, with no argument.
- Observed: `usage: textkit normalize [-h] text` and `textkit normalize: error: the following arguments are required: text` on stderr; exit code 2.

## Decided by

pending: reserved for user ([P1](P1-working-agreement.md) § Authority: user-visible command-line behavior)

## History

- 2026-10-05: created as proposed. Reserved for the user: command-line users see it.
- 2026-10-07: needs revalidation: it depends on [D3](D3-empty-slug-error.md), which needs revalidation after [F3](F3-other-scripts.md).
