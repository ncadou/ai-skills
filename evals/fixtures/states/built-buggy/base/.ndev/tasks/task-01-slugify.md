# T01: slugify function

Status: done

Serves: O1

Implements: `design.md` § Interfaces & Skeletons › slug module, D1, D2, D3

## Scope

- Create `textkit/slug.py`
- Edit `textkit/__init__.py` (export `slugify`)
- Create `tests/test_slug.py`
- Edit `README.md` (document `slugify`)

## Acceptance

Test command: `python3 -m unittest tests.test_slug -v`

Expected behavior: every row of the contract table in `design.md` § slug module holds; `TypeError` and `ValueError` are raised as the docstring states; the existing tests still pass.

## Evidence

Written by `nbuild`: one entry per build.

### Build 1

- Command: `python3 -m unittest tests.test_slug -v`
- Run by: agent
- Result: pass
- Output: Ran 4 tests in 0.000s OK
- Choices: hard cut at `max_length` for simplicity (agent)

## Review

Written by `nreview`: one entry per review.

Accepted by:
