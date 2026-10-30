# O3: normalize_whitespace can keep line breaks

Status: active
Validity: current
Topics: whitespace

## Outcome

`textkit.normalize_whitespace(text, keep_newlines=False)` can normalize each line on its own and keep the line breaks, for multi-line text such as addresses.

## Out of scope

- Any change to the `normalize` command.
- Any change to the default behavior of `normalize_whitespace`.

## History

- 2026-10-06: created as active, from the user's request.
