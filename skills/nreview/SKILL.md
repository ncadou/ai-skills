---
name: nreview
description: Review the current ndev slice for correctness and readability, with a Pass/Fail verdict.
disable-model-invocation: true
---

Audit the current slice against its task file and diff. Report revisions; leave fixes to `nbuild`.

## Steps

### 1. Fix the scope

Inspect the git diff and the current `.ndev/tasks/task-NN-<slug>.md`. Review only this slice.

Done when every changed file is mapped to the task scope, and out-of-scope changes are flagged.

### 2. Apply every rule below

Apply the full Correctness and Readability sets. Report a Pass/Fail verdict with blocking revisions.

Done when every rule has been applied and the verdict names its blocking revisions, or states there are none.

## Correctness

- Edge cases and failure modes in scope are handled; unhandled state transitions are named.
- Tests assert invariants through public interfaces; superficial or tautological assertions are named.
- No regressions in the touched area.

## Readability & Docs

- Types are explicit and docstrings match current signatures.
- Complex logic explains its reasoning at its site, not just what the code does.
- Public contract changes update project docs (README, spec notes, or architectural notes).

## Verdict format

```markdown
## nreview: Pass|Fail — <task file>

Blocking revisions:
1. <file:line — what fails and what to change>
2. ...
```
