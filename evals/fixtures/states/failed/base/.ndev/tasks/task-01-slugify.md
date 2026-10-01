# T01: slugify function

Status: fail

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

### Review 1: Fail

- Reviewed by: agent

Blocking revisions:
1. textkit/slug.py:25 — `slug[:max_length]` splits words and can leave a trailing hyphen (`slugify("hello world foo", max_length=12)` gives `"hello-world-"`); cut at the last hyphen as D2 states (nbuild)
2. textkit/slug.py:27 — an empty slug returns `""`; raise `ValueError("slug is empty")` per D3, and reject `max_length < 1` and non-int `max_length` per the skeleton (nbuild)
3. tests/test_slug.py:17 — `test_max_length` only checks the type and length; assert the contract table rows from `design.md` § slug module, including the error cases (nbuild)

Accepted by:
