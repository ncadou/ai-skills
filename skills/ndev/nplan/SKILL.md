---
name: nplan
description: Break the ndev design into task slices, producing .ndev/plan.md and .ndev/tasks/.
disable-model-invocation: true
---

Break the design into tasks. Produce only `.ndev/plan.md`, `.ndev/tasks/`, and entries in `.ndev/questions.md`; leave design to `ndesign` and code to `nbuild`. Take every contract from `.ndev/design.md` as written.

The user approves the plan. Follow `.ndev/brief.md` § Control when it exists. The user can delegate the plan or waive its gate at any time; record it on the plan's `Approved:` line. Only the user creates a delegation, in § Control or in their own words; every other approval you record is `user`.

When § Control lists focus topics, tag the plan `Concern: <topic> | other`: does slicing, build order, or acceptance touch a focus topic? When in doubt, use the topic. A plan in focus passes its gate as written. A plan tagged `other` records `Approved: agent (delegated: outside focus)` and does not stop: when `plan.md` is written, report a digest of the slices, one line each with its dependencies and acceptance command. The user can pull the plan back to the gate. Other § Control lines and the user's own words override focus. With no focus topic, the gate applies as written.

## Inputs

- `.ndev/design.md`: the contracts to slice, with decisions (`D<n>`). If it is missing, work from `.ndev/brief.md`, `.ndev/discovery.md`, and the user, but only for work that adds or changes no boundary or contract; otherwise backtrack to `ndesign`.
- `.ndev/brief.md`: objectives (`O<n>`) and § Control.
- `.ndev/questions.md`: every open question marked `for nplan` is in scope for this run, and so is every question marked `for user` that the user answers here. Tick each one and append the pointer to its answer, keeping the rest of the line as written: `- [x] Q<n>: <question> (from <phase>/<user|agent>, for <nplan|user>) → T<NN>`, or `→ plan § <section>`. When the user declines a question `for user` ("no preference", "you decide"), tick it `→ Q<new>` and append `Q<new>` for the phase that will settle it. Each ledger entry is one line in exactly the format shown, with no added notes; details go in the artifact that answers it.
- Existing `.ndev/plan.md`: revise it in place. Read each task's status from its task file, and leave every task whose status is `done`, `pass`, or `accepted` unchanged. Keep a replaced task file and add `Superseded by T<NN>: <reason>` under its status.

## Steps

### 1. Check the design is complete

Trace every objective to the decisions, components, and skeletons that deliver it, and record the trace in `plan.md` § Traceability. Each trace that ends in a missing or ambiguous contract is a gap, and so is each decision without a `Decided by` line. Every component in design § Architecture must have a skeleton in § Interfaces & Skeletons; a component without one is a gap, even when the trace reaches it. With no design, confirm with the user that the work adds or changes no contract.

Done when every objective traces to design contracts (or the user confirmed none are needed), every decision has an owner, and the trace is recorded, or the run has stopped on a Backtrack.

### 2. Slice into tasks

Decompose the design into numbered, independent, testable slices. Write one file per slice at `.ndev/tasks/task-NN-<slug>.md` using the task template below; its ID is `T<NN>`, matching the file number. Index the tasks in `.ndev/plan.md` in build order, with their dependencies. Status lives only in the task files. When a slice needs a type, signature, or boundary that the design lacks, record it as a gap and backtrack.

Done when every skeleton in `.ndev/design.md` is covered by at least one task, and every task has the objectives it serves, files to touch, the design sections and decisions it implements, a runnable acceptance command, and expected behavior, with nothing shared unwritten between files.

### 3. Get the plan approved

Present the slices, their size, build order, dependencies, and acceptance commands. The user approves, changes, or delegates them.

Done when the user approves the plan, or has delegated its gate (§ Control, their own words, or a plan outside focus), and `plan.md` records it on its `Approved:` line.

## Backtrack

When a trigger below fires, stop. Append each gap to `.ndev/questions.md` as `- [ ] Q<n>: <gap> (from nplan/<user|agent>, for <phase>) stale: <artifacts or none>`, listing the downstream artifacts that rerun may make stale. Name the phase for the user to run. The user decides.

- A contract is missing, ambiguous, or too coarse to slice: `ndesign`.
- A decision records no `Decided by`: `ndesign`.
- A slice depends on behavior nobody has verified: `nlearn`.

## Plan template

```markdown
# Plan: <topic>

## Traceability

- O1 → D<n>, …; <component>, …; T01, T02

## Tasks

- T01 `tasks/task-01-<slug>.md` — <title> (depends on: none)
- T02 `tasks/task-02-<slug>.md` — <title> (depends on: T01)

Status lives in each task file.

Concern: <topic> | other (when § Control lists focus topics)

Approved: user | agent (delegated: <scope>)
```

## Task template

```markdown
# T01: <title>

Status: pending

Serves: O<n>, …

Implements: `design.md` § <section>, D<n>, …; or `none` when the design was skipped.

## Scope

Files to create or edit.

## Acceptance

Test command: `<exact command, e.g. pytest tests/test_feature.py -k test_happy_path>`

Expected behavior:

## Evidence

Written by `nbuild`: one entry per build.

## Review

Written by `nreview`: one entry per review.

Accepted by:
```

The task template is canonical here; `nbuild` and `nreview` consume these files as written. Status moves `pending` → `done` (`nbuild`) → `pass` | `fail` (`nreview`) → `accepted` (optional). The user owns `accepted` and `Accepted by:`: they set it directly, ask the agent to, or delegate acceptance.
