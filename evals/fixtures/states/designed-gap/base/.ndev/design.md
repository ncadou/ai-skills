# Design: slugify

## Process

### Library call

Serves: O1

- Actor: Python code calling `textkit.slugify(text, max_length=None)`.
- Steps: check types; strip accents with `strip_accents` (F1, F5); lowercase; replace every run of characters outside `[a-z0-9]` with one hyphen; trim hyphens at both ends; when `max_length` is set and the slug is longer, cut it (D2).
- Failure paths: `text` is not a `str` → `TypeError` (F3); `max_length` is less than 1 → `ValueError`; nothing is left after cleaning → `ValueError` (F6, F8, D3).
- Data flow: `str` in, `str` out. No state.

Approved: user

### Command line

Serves: O2

- Actor: a user running `python3 -m textkit slugify <text> [--max-length N]`.
- Steps: argparse parses the arguments (F2); the handler calls `slugify` and prints the slug; exit code 0.
- Failure paths: `slugify` raises `ValueError` → print `textkit: error: <message>` to stderr, exit code 2. A non-integer `--max-length` is rejected by argparse (exit code 2).

Approved: user

## Decisions

### D1: How to handle non-ASCII characters

- Serves: O1
- Options: reuse `strip_accents`, then treat anything outside `[a-z0-9]` as a separator — no dependency, letters with no decomposition become separators; add a transliteration library — better coverage, but breaks the no-dependency non-goal.
- Evidence: F1, F5, F7
- Recommendation: reuse `strip_accents`; it is tested and the non-goals exclude transliteration.
- Choice: reuse `strip_accents`, then treat anything outside `[a-z0-9]` as a separator.
- Decided by: user

### D2: How `max_length` cuts a long slug

- Serves: O1
- Options: hard cut at `max_length` — simple, can split a word and leave a trailing hyphen; cut at the last hyphen within `max_length` — keeps whole words.
- Evidence: F6
- Recommendation: cut at the last hyphen within `max_length`; when the first word alone is longer than `max_length`, hard-cut that word. Never end with a hyphen.
- Choice: as recommended.
- Decided by: user

### D3: What an empty slug does

- Serves: O1, O2
- Options: return `""` — silent, callers can build broken URLs; raise `ValueError` — explicit, matches F6.
- Evidence: F6, F8
- Recommendation: raise `ValueError("slug is empty")`.
- Choice: raise `ValueError("slug is empty")`.

Approved: user

## Architecture

### slug module

- Responsibility: build slugs from text; owns D1, D2, D3.
- Serves: Process § Library call
- Rests on: D1, D2, D3
- Reference: F1, F3 (`textkit/core.py`)

### slugify subcommand

- Responsibility: parse arguments, call `slugify`, print the slug or the error.
- Serves: Process § Command line
- Rests on: D3
- Reference: F2 (`textkit/__main__.py`)

`textkit/slug.py` imports `strip_accents` from `textkit.core`. `textkit/__init__.py` exports `slugify`. `textkit/__main__.py` imports `slugify` from `textkit.slug` and registers the subcommand next to `normalize`.

Approved: user

## Interfaces & Skeletons

### slug module

Implements: D1, D2, D3

```python
# textkit/slug.py
__all__ = ["slugify"]


def slugify(text: str, max_length: int | None = None) -> str:
    """Turn ``text`` into a lowercase ASCII, hyphen-separated URL slug.

    :param text: Text to turn into a slug.
    :param max_length: Longest slug allowed; ``None`` means no limit.
    :return: A non-empty slug that matches ``[a-z0-9]+(-[a-z0-9]+)*``
        and is at most ``max_length`` characters long.
    :raises TypeError: When ``text`` is not a ``str``, or ``max_length`` is
        neither ``None`` nor an ``int``.
    :raises ValueError: When ``max_length`` is less than 1, or the slug is
        empty (message: ``"slug is empty"``).
    """
```

Examples that define the contract:

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

Approved: user
