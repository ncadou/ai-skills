---
name: nstart
description: Frame one ndev cycle, producing .ndev/brief.md with the request, objectives, non-goals, a provisional approach, phases, and optional control.
disable-model-invocation: true
---

Frame one ndev cycle. Produce only `.ndev/brief.md` and entries in `.ndev/questions.md`; leave investigation to `nlearn`, design to `ndesign`, and tasks to `nplan`.

The user decides the brief. Steps 1 to 4 each end at a gate: present your proposal, then stop and wait for the user's answer before the next step. Write `.ndev/brief.md` in step 5, once every gate has passed. A step skips its gate only when the user delegates it. Only the user creates a delegation, in their own words; record it as `agent (delegated: <scope>)` on the section's `Approved:` line, and record each agreement as `user`.

## Inputs

- The user's request. Nothing upstream is required.
- Existing `.ndev/` artifacts from an earlier cycle: ask the user whether to keep, archive, or delete them before writing.
- Existing `.ndev/brief.md` for this cycle: revise it in place. Mark a replaced objective `Superseded by O<n>: <reason>` instead of deleting it.
- `.ndev/questions.md`: resolve every open question marked `for nstart`, and every question marked `for user` that the user answers here. Tick each one and append the pointer to its answer, keeping the rest of the line as written: `- [x] Q<n>: <question> (from <phase>/<user|agent>, for <nstart|user>) → O<n>`, or `→ brief § <section>`. When the user declines a question `for user` ("no preference", "you decide"), tick it `→ Q<new>` and append `Q<new>` for the phase that will settle it. Each ledger entry is one line in exactly the format shown, with no added notes; details go in the artifact that answers it.

## Steps

### 1. Record the request and fix the scope

Record the user's request in their own words, or quote its key lines. Confirm objectives and explicit non-goals with the user. Number objectives `O1`, `O2`, …; never reuse a number.

Done when the request is recorded, objectives and non-goals are written down, and the user agrees.

### 2. Sketch a provisional approach

Outline the approach at the level of areas and steps, without tasks or signatures. Mark it provisional: discovery and design may overturn it. Each step cites the objectives it serves.

Done when every objective is cited by at least one step of the approach, and the user agrees with the approach.

### 3. Record unknowns and phases

Append every unknown to `.ndev/questions.md` as `- [ ] Q<n>: <question> (from nstart/<user|agent>, for <phase|user>)`, with the next free number. Route to `user` what only the user can answer: preferences, constraints, priorities. Suggest which phases this work needs (`nlearn`, `ndesign`, `nplan`, `nbuild`, `nreview`), with a one-line reason for each skip. The suggestion is advisory; the user decides. Record both, one line per phase, as in the template. Answers to questions go in `brief.md`; the ledger only points to them.

Done when every unknown is in `.ndev/questions.md`, and every phase is marked run or skip with a reason, your suggestion, and the user's decision.

### 4. Offer a control seed

Ask the user once whether to set a Control section: what the agent may decide alone, and which gates to waive. An empty answer is fine: then every gate applies and the agent makes no design choice. The seed does not limit the user; they can change delegation in any phase, at any time.

Done when the user has set Control, or declined.

### 5. Write `.ndev/brief.md`

Write the artifact using the template below. Report the suggested next phase; the human runs it.

Done when `.ndev/brief.md` exists and every section except Control is filled.

## Brief template

```markdown
# Brief: <topic>

## Request

The user's request, in their own words.

## Objectives

- O1: <what this cycle must achieve>

Approved: user | agent (delegated: <scope>)

## Non-goals

What this cycle leaves out.

Approved: user | agent (delegated: <scope>)

## Approach (provisional)

1. <area or step> (serves: O1)

Approved: user | agent (delegated: <scope>)

## Phases

- nlearn: run|skip — <reason> (suggested: run|skip; decided by: user | agent (delegated: <scope>))
- ndesign: run|skip — <reason> (suggested: run|skip; decided by: user | agent (delegated: <scope>))
- nplan: run|skip — <reason> (suggested: run|skip; decided by: user | agent (delegated: <scope>))
- nbuild: run
- nreview: run|skip — <reason> (suggested: run|skip; decided by: user | agent (delegated: <scope>))

## Control

Optional. Empty: every gate applies and the agent makes no design choice.

- <scope>: agent decides | gate waived
```
