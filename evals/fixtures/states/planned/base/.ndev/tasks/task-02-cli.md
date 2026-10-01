# T02: slugify subcommand

Status: pending

Serves: O2

Implements: `design.md` § Interfaces & Skeletons › slugify subcommand, D3

## Scope

- Edit `textkit/__main__.py`
- Edit `tests/test_core.py` (CLI tests)

## Acceptance

Test command: `python3 -m unittest tests.test_core -v`

Expected behavior: `python3 -m textkit slugify "Hello, World!"` prints `hello-world` and exits 0; `--max-length 5` cuts per D2; an empty slug prints `textkit: error: slug is empty` to stderr and exits 2.

## Evidence

Written by `nbuild`: one entry per build.

## Review

Written by `nreview`: one entry per review.

Accepted by:
