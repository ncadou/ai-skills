# T3: The keep_newlines option

Status: pending
Validity: current
Topics: whitespace
Depends on: [D5](D5-per-line-normalization.md)
Serves: [O3](O3-keep-newlines.md)

## Scope

`textkit/core.py` (`normalize_whitespace`), `tests/test_core.py`, and `README.md` (document the option).

## Expected behavior

| Call | Result |
| --- | --- |
| `normalize_whitespace("a  b\n  c ", keep_newlines=True)` | `"a b\nc"` |
| `normalize_whitespace("a\r\nb", keep_newlines=True)` | `"a\nb"` |
| `normalize_whitespace("a\n\n b", keep_newlines=True)` | `"a\n\nb"` |
| `normalize_whitespace("a\nb")` | `"a b"` |
| `normalize_whitespace(3, keep_newlines=True)` | `TypeError` |

The existing tests still pass.

## Acceptance

`python3 -m unittest tests.test_core -v`

## Latest build

None yet.

## Latest review

None yet.

## History

- 2026-10-06: created as pending.
