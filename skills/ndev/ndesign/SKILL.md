---
name: ndesign
description: Design the solution from .ndev/discovery.md, producing .ndev/design.md with process, decisions, boundaries, and skeletons.
disable-model-invocation: true
---

Design the solution outside-in: process first, then decisions, boundaries, and skeletons. Produce only `.ndev/design.md` and entries in `.ndev/questions.md`; leave investigation to `nlearn`, tasks to `nplan`, and code to `nbuild`.

The user owns the design. Every step ends at a gate: present the result, write the agreed section to `.ndev/design.md` with its `Approved:` line, and move to the next step only on the user's approval. The agent makes a design choice only when the user delegates it: in `.ndev/brief.md` § Control, or at any time during this run, for one decision, a step, or the whole phase. The user can also waive a gate. Record each delegation the user gave where it applies: on the decision's `Decided by` line, or on the section's `Approved:` line; every other approval you record is `user`. A decision that surfaces in a later step goes through step 2 before you build on it.

## Inputs

- `.ndev/brief.md`: objectives (`O<n>`), non-goals, and § Control. If it is missing, confirm objectives and non-goals with the user.
- `.ndev/discovery.md`: findings (`F<n>`) and candidate conventions. If it is missing, read the touched code directly; every assumption you cannot verify that way becomes a question for `nlearn` (see Backtrack).
- `.ndev/questions.md`: every open question marked `for ndesign` is in scope for this run, and so is every question marked `for user` that the user answers here. Tick each one and append the pointer to its answer, keeping the rest of the line as written: `- [x] Q<n>: <question> (from <phase>/<user|agent>, for <ndesign|user>) → D<n>`, or `→ design § <section>`. When the user declines a question `for user` ("no preference", "you decide"), tick it `→ Q<new>` and append `Q<new>` for the phase that will settle it. Each ledger entry is one line in exactly the format shown, with no added notes; details go in the artifact that answers it.
- Existing `.ndev/design.md`: revise it in place. Keep a replaced decision and mark it `Superseded by D<n>: <reason>`. Every changed section passes its gate again.

## Steps

### 1. Describe the process

Describe the end-to-end process the work takes part in: actors and triggers, the main scenario, failure scenarios, data flow, and state changes. Each scenario cites the objectives it serves. Stay at the level of behavior; components come in step 3.

Done when every objective is cited by at least one scenario, every gap is an open question `for nlearn`, and the user approves the process.

### 2. Surface the decisions

List every design decision the agreed process raises, numbered `D<n>`. Include each candidate convention from discovery whose adoption is open to challenge; a convention that fits without doubt needs no decision, but step 3 still cites it, so the user sees it. For each decision, present the options, their tradeoffs, the evidence (`F<n>` or a codebase citation), and your recommendation. The user chooses, or delegates the decision to you. Evidence supports a choice; the user makes it.

Done when every decision records its recommendation, its choice, and `Decided by`, and the user approves the list.

### 3. Define boundaries

Derive components, their responsibilities, and how they compose from the agreed process and decisions. Each component cites the scenario it serves, the decisions it rests on, and its reference pattern.

Done when every responsibility traces to a scenario, every component cites its reference pattern (`F<n>` or file path) or states that none exists, and the user approves the boundaries.

### 4. Write skeletons

Write types, function signatures, interfaces, schemas, and error contracts as code blocks in `.ndev/design.md`, without logic. Each skeleton names its component and the decisions it implements. Leave the repository untouched. `nplan` takes every contract as written, so the skeletons must be complete.

Done when every boundary has a skeleton, every signature states its parameter types, return type, and failure modes, no question `for ndesign` stays open, and the user approves the skeletons.

## Backtrack

When a trigger below fires, stop. Append each gap to `.ndev/questions.md` as `- [ ] Q<n>: <gap> (from ndesign/<user|agent>, for <phase>) stale: <artifacts or none>`, listing the downstream artifacts that rerun may make stale. Name the phase for the user to run. The user decides.

- The process or a decision rests on an untested assumption about code, a library, or data: `nlearn`. Expect several rounds with `nlearn` on larger work.
- Objectives conflict, or the design cannot meet them within the non-goals: `nstart`.

## Design template

```markdown
# Design: <topic>

## Process

### <scenario>

Serves: O<n>, …

Actors, triggers, steps, failure paths, data flow, state changes.

Approved: user | agent (delegated: <scope>)

## Decisions

### D1: <decision>

- Serves: O<n>; Answers: Q<n> (when any)
- Options: <option — tradeoff>, …
- Evidence: <F<n> or file path>
- Recommendation: <option and reason>
- Choice: <option and reason>
- Decided by: user | agent (delegated: <decision, step, or phase>)
- Superseded by D<n>: <reason> (when replaced)

Approved: user | agent (delegated: <scope>)

## Architecture

### <component>

- Responsibility: <what it does>
- Serves: Process § <scenario>
- Rests on: D<n>, …
- Reference: <F<n> or file path> | none

How the components compose.

Approved: user | agent (delegated: <scope>)

## Interfaces & Skeletons

### <component>

Implements: D<n>, …

Types, signatures, schemas, error contracts. No logic.

Approved: user | agent (delegated: <scope>)
```
