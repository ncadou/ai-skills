# D3: Show progress as one line on stderr

Status: decided
Validity: current
Topics: progress, cli
Serves: [O2](O2-show-progress.md)

## Options

- One line on stderr, `imported 1,500 / 10,000 rows (15%)`, rewritten in place on a terminal and appended otherwise.
- A JSON progress file next to the source file.

## Choice

The stderr line. When the import stops early, its last line is `stopped at 1,500 / 10,000 rows (15%); rerun to resume`.

## Rationale

The user follows imports in a terminal, and a line leaves no file to clean up.

## Evidence

None needed: a preference.

## Decided by

user (2026-03-02): "The stderr line. And say how far it got when it stops."

## History

- 2026-03-02: created as proposed; reserved for the user (user-visible behavior).
- 2026-03-02: decided by the user.
