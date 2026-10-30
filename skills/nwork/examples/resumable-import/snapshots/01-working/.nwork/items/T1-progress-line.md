# T1: Progress line

Status: pending
Validity: current
Topics: progress
Depends on: [D3](D3-progress-line.md)
Serves: [O2](O2-show-progress.md)

## Scope

`orderload/progress.py` (new), its call site in `orderload/importer.py`, and `tests/test_progress.py` (new).

## Expected behavior

- After each committed batch, stderr shows `imported <done> / <total> rows (<pct>%)`, rewritten in place on a terminal and appended otherwise.
- On Ctrl-C or an error, the last stderr line is `stopped at <done> / <total> rows (<pct>%); rerun to resume`.
- The counts come from the rows that the importer reports as committed, so they do not depend on how batches commit.

## Acceptance

`pytest tests/test_progress.py`

## Latest build

None yet.

## Latest review

None yet.

## History

- 2026-03-02: created as pending.
