# T01: slugify function

Status: pending

Serves: O1

Implements: `design.md` § Interfaces & Skeletons › slug module, D1, D2, D3

## Scope

- Create `textkit/slug.py`
- Edit `textkit/__init__.py` (export `slugify`)
- Create `tests/test_slug.py`
- Edit `README.md` (document `slugify`)

## Acceptance

Test command: `make test-slugify`

Expected behavior: every row of the contract table in `design.md` § slug module holds; `TypeError` and `ValueError` are raised as the docstring states; the existing tests still pass.

## Evidence

Written by `nbuild`: one entry per build.

## Review

Written by `nreview`: one entry per review.

Accepted by:
