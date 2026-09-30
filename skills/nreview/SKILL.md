---
name: nreview
description: Review the current ndev slice for correctness and readability, with a Pass/Fail verdict.
disable-model-invocation: true
---

Audit the current slice against its task file, its design contracts, and its diff. Record the verdict and report revisions; leave fixes to `nbuild`. The verdict informs the user; the user can overrule it and decides acceptance.

## Inputs

- The git diff and the current `.ndev/tasks/task-NN-<slug>.md`, with its Evidence and earlier Review entries. If no task file exists, ask the user for the slice's scope.
- The `.ndev/design.md` sections and decisions the task names under `Implements:`, when they exist.
- `.ndev/brief.md` § Control, when it exists.

## Steps

### 1. Fix the scope

Review only this slice.

Done when every changed file is mapped to the task scope, and out-of-scope changes are flagged.

### 2. Apply every rule below

Apply the full Correctness and Readability sets. Decide a Pass/Fail verdict with blocking revisions, and name the phase each revision belongs to.

Done when every rule has been applied and the verdict names its blocking revisions, or states there are none.

### 3. Record the verdict

Append the verdict to the task file's Review section using the format below, and set `Status: pass` or `Status: fail`. Report it to the user.

Done when the task file holds the new Review entry and its status matches the verdict.

## Correctness

- Code matches the design contracts the task implements; deviations are named.
- Edge cases and failure modes in scope are handled; unhandled state transitions are named.
- Tests assert invariants through public interfaces; superficial or tautological assertions are named.
- The latest Evidence entry records a passing run of the acceptance command.
- No regressions in the touched area.

## Readability & Docs

- Types are explicit and docstrings match current signatures.
- Complex logic explains its reasoning at its site, not just what the code does.
- Public contract changes update project docs (README, design notes, or architectural notes).

## Acceptance

Acceptance belongs to the user. Only on the user's explicit word, set `Status: accepted` and fill `Accepted by: user`. When the user has delegated acceptance, in § Control or during the run, fill `Accepted by: agent (delegated: <scope>)` instead. Accepting after a `fail` overrules that verdict: add `Overruled by user: <reason>` under its Review entry; only the user can overrule.

## Backtrack

Revisions that `nbuild` can fix within the task stay in the verdict. For the triggers below, also append each gap to `.ndev/questions.md` as `- [ ] Q<n>: <gap> (from nreview/<user|agent>, for <phase>) stale: <artifacts or none>`, listing the downstream artifacts that rerun may make stale. The user decides.

- The code follows the contract, but the contract itself is flawed: `ndesign`.
- The slice cannot pass without work outside its scope: `nplan`.
- The code or a dependency contradicts a finding in discovery: `nlearn`.

## Verdict format

```markdown
### Review <n>: Pass|Fail

- Reviewed by: agent | user

Blocking revisions:
1. <file:line — what fails and what to change> (nbuild|nplan|ndesign|nlearn)
2. ...
```
