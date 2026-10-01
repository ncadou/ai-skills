# T01: strip_accents helper

Status: accepted

Serves: O1

Implements: none

## Scope

- `textkit/core.py`
- `tests/test_core.py`

## Acceptance

Test command: `python3 -m unittest tests.test_core -v`

Expected behavior: `strip_accents("Crème Brûlée") == "Creme Brulee"`; letters with no decomposition pass through.

## Evidence

### Build 1

- Command: `python3 -m unittest tests.test_core -v`
- Run by: agent
- Result: pass
- Output: Ran 5 tests in 0.001s OK

## Review

### Review 1: Pass

- Reviewed by: agent

Blocking revisions:
none

Accepted by: user
