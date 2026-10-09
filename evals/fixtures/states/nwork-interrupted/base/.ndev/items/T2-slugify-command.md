# T2: The slugify command

Status: pending
Validity: needs-revalidation
Topics: cli, errors
Depends on: [F2](F2-cli-subcommands.md), [D4](D4-cli-error-output.md), [T1](T1-slugify-function.md)
Serves: [O2](O2-slugify-command.md)

## Scope

`textkit/__main__.py` (add the `slugify` subcommand), `tests/test_cli_slug.py` (new), and `README.md` (document the command).

## Expected behavior

- `python3 -m textkit slugify "Hello, World!"` prints `hello-world` and exits 0.
- `--max-length N` passes `N` to `slugify`; argparse rejects a non-integer `N`.
- When `slugify` raises `ValueError`, the command reports it as [D4](D4-cli-error-output.md) decides.
- `normalize` is unchanged.

## Acceptance

`python3 -m unittest tests.test_cli_slug -v`

## Latest build

None yet.

## Latest review

None yet.

## History

- 2026-10-05: created as pending. Waits for [D4](D4-cli-error-output.md) and [T1](T1-slugify-function.md).
- 2026-10-07: needs revalidation: it depends on [T1](T1-slugify-function.md), which needs revalidation after [F3](F3-stroke-letters.md).
