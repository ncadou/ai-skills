# D5: keep_newlines normalizes each line on its own

Status: decided
Validity: current
Topics: whitespace
Serves: [O3](O3-keep-newlines.md)

## Options

- Normalize each line on its own, and join the lines with `\n`. Blank lines stay, as empty lines.
- Also collapse runs of blank lines into one. Shorter output, but the line count changes.

## Choice

With `keep_newlines=True`, split the text into lines (`str.splitlines`, so `\r\n` and `\r` count as line breaks), normalize each line as `normalize_whitespace` does, and join them with `\n`. Blank lines stay, as empty lines. The default, `keep_newlines=False`, is unchanged.

## Rationale

Callers that keep line breaks usually care about the lines themselves; collapsing blank lines would be a second, separate feature.

## Evidence

`textkit/core.py`: `normalize_whitespace` already collapses each run of `\s` and trims; per line, that gives the wanted result.

## Decided by

user (2026-10-06): "Each line on its own, keep the blank lines."

## History

- 2026-10-06: created as proposed.
- 2026-10-06: decided by the user.
