# T1: The slugify function

Status: pass
Validity: needs-revalidation
Topics: slugify, errors
Depends on: [F1](F1-accent-helper.md), [D1](D1-non-ascii-separators.md), [D2](D2-cut-at-last-hyphen.md), [D3](D3-empty-slug-error.md)
Serves: [O1](O1-slugify-function.md)

## Scope

`textkit/slug.py` (new), `textkit/__init__.py` (export `slugify`), `tests/test_slug.py` (new), and `README.md` (document `slugify`).

## Expected behavior

`slugify(text: str, max_length: int | None = None) -> str` returns a non-empty slug that matches `[a-z0-9]+(-[a-z0-9]+)*` and is at most `max_length` characters long.

| Call | Result |
| --- | --- |
| `slugify("Hello, World!")` | `"hello-world"` |
| `slugify("Crème Brûlée 2")` | `"creme-brulee-2"` |
| `slugify("  --a--b--  ")` | `"a-b"` |
| `slugify("hello world foo", max_length=13)` | `"hello-world"` |
| `slugify("hello world foo", max_length=11)` | `"hello-world"` |
| `slugify("abcdefghij", max_length=4)` | `"abcd"` |
| `slugify("Straße")` | `"stra-e"` |
| `slugify("!!!")` | `ValueError("slug is empty")` |
| `slugify("Привет")` | `ValueError("slug is empty")` |
| `slugify("a", max_length=0)` | `ValueError` |
| `slugify(3)` | `TypeError` |

The existing tests still pass.

## Acceptance

`python3 -m unittest tests.test_slug -v`

## Latest build

- Date: 2026-10-06
- Command: `python3 -m unittest tests.test_slug -v`
- Observed: `Ran 11 tests in 0.000s` and `OK`. The whole suite, `python3 -m unittest discover -s tests -t .`, ran 16 tests, OK.
- Basis: [F1](F1-accent-helper.md), [D1](D1-non-ascii-separators.md), [D2](D2-cut-at-last-hyphen.md), [D3](D3-empty-slug-error.md)

## Latest review

- Date: 2026-10-06
- Verdict: pass. The changes stay inside the scope. The tests cover every row of the contract table, the empty-slug message, and both type errors, through `textkit.slugify`. `_cut` keeps whole words ([D2](D2-cut-at-last-hyphen.md)) and hard-cuts only a first word that is too long. The whole suite passes: `python3 -m unittest discover -s tests -t .` ran 16 tests, OK. The README documents `slugify`.

## History

- 2026-10-05: created as pending.
- 2026-10-06: in progress.
- 2026-10-06: implemented. Acceptance command passed.
- 2026-10-06: pass, after review.
- 2026-10-07: needs revalidation: it depends on [F1](F1-accent-helper.md), refuted by [F3](F3-stroke-letters.md), and on [D1](D1-non-ascii-separators.md), which needs revalidation. The build and review of 2026-10-06 rest on F1 and no longer count as assurance.
