# F2: CLI subcommands are argparse subparsers with a handler

Status: verified
Validity: current
Topics: cli
Serves: [O2](O2-slugify-command.md)

## Claim

`textkit/__main__.py` registers each subcommand with `commands.add_parser(...)` and `set_defaults(handler=...)`. The handler returns the exit code. A new subcommand needs no change to `normalize`.

## Evidence

- Checked: `textkit/__main__.py`, and `tests/test_core.py` (`CliTest`).
- Source: `textkit/__main__.py` (`main`, `_normalize`).
- Observed: `main` returns `args.handler(args)`; `_normalize` prints and returns 0.

## History

- 2026-10-05: created as verified.
