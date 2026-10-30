# T3: Guard against a changed source file

Status: pending
Validity: current
Topics: recovery, cli
Depends on: [D2](D2-refuse-changed-source.md)
Serves: [O1](O1-resume-without-loss.md)

## Scope

`orderload/importer.py`, `orderload/cli.py`, and `tests/test_source_change.py` (new).

## Expected behavior

As [D2](D2-refuse-changed-source.md) decides. Not ready: that choice waits for the user.

## Acceptance

`pytest tests/test_source_change.py`

## Latest build

None yet.

## Latest review

None yet.

## History

- 2026-03-02: created as pending, blocked by a choice reserved for the user.
