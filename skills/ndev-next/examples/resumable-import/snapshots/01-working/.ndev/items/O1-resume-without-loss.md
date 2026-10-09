# O1: Resume an interrupted import without losing or duplicating rows

Status: active
Validity: current
Topics: recovery

## Outcome

After a crash or a kill, running `orderload import <file>` again on the same file finishes the import. Every source row is in the store exactly once.

## Out of scope

Several imports running in parallel into the same store prefix.

## History

- 2026-03-02: created as active. From the user's request: "If an import dies halfway, I want to rerun it and end up with every order exactly once."
