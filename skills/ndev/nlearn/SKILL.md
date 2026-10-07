---
name: nlearn
description: Discovery investigation producing .ndev/discovery.md with validated assumptions and spikes.
disable-model-invocation: true
---

Run a discovery investigation, so that both you and the user learn before anyone designs or decides. Produce only `.ndev/discovery.md` and entries in `.ndev/questions.md`; leave design to `ndesign`, tasks to `nplan`, and code to `nbuild`.

Steps 1 and 4 end at a gate: present the result, then stop and wait for the user's answer before the next step. Follow `.ndev/brief.md` § Control when it exists. The user can delegate a step or waive a gate at any time; record it on the `Approved:` line of the section it affects. Only the user creates a delegation, in § Control or in their own words; every other approval you record is `user`.

When § Control lists focus topics, they decide which items stop at a gate. Tag each finding `Concern: <topic> | other`, and classify each question the same way without changing its ledger line; when in doubt, use the topic. Decide each `other` item yourself and record `agent (delegated: outside focus)` on its ruling and its walkthrough line. At each gate, present the in-focus items in full, then a digest of the items you decided since the last gate, one line each. The user can pull any item back; it then passes the gate like an in-focus item. A gate with no item in focus does not stop: carry its digest to the next gate, or report it at the end of the phase. Other § Control lines and the user's own words override focus. Each step's Done line reads with focus applied. With no focus topic, every gate applies as written.

## Inputs

- `.ndev/brief.md`: objectives (`O<n>`) and non-goals. If it is missing, confirm objectives and non-goals with the user.
- `.ndev/questions.md`: every open question marked `for nlearn` is in scope for this run, and so is every question marked `for user` that the user answers here.
- Existing `.ndev/discovery.md`: add to it. Keep earlier findings; mark any that new evidence overturns `Superseded by F<n>: <reason>`.

## Steps

### 1. Fix the questions

List what this run must answer: open questions marked `for nlearn`, plus gaps in the brief's approach. Ask the user what they already know and what they want answered. Append each new question to `.ndev/questions.md` as `- [ ] Q<n>: <question> (from nlearn/<user|agent>, for <phase|user>)`, with the next free number. Each ledger entry is one line in exactly the format shown, with no added notes; details go in the artifact that answers it. With no brief and no open questions, derive the list from the user's request.

Done when every question in scope has an ID, and the user agrees with the list.

### 2. Map reference patterns

Search the codebase and relevant libraries for existing conventions in the touched areas. Record each as a finding `F<n>`, with its file path. A convention is a candidate constraint: `ndesign` decides whether to adopt it.

Done when every touched area names its reference findings, or states that none exist.

### 3. Validate assumptions with spikes

List hidden dependencies, data contracts, and failure points, each as a finding. For each ambiguous behavior, run a minimal spike under `/tmp` or `.ndev/scratch/` and log actual output, never assumed output. When no spike can check an assumption, ask the user: they supply the fact (`Source: user`), rule on the risk, or leave it open as a question.

Done when every assumption has a Source and a Status, and every unverified one has a Ruling or an open question.

### 4. Walk the user through the findings

Present the findings so the user can follow the evidence: what was checked, how, and what it showed. The user can challenge a finding, add facts of their own as findings with `Source: user`, ask new questions, and accept or reject each risk.

Done when the user has reviewed every new finding and ruled on every risk, or has waived this gate.

### 5. Write `.ndev/discovery.md`

Write or extend the artifact using the template below. In `.ndev/questions.md`, tick each question answered and append the pointer to its finding, keeping the rest of the line as written: `- [x] Q<n>: <question> (from <phase>/<user|agent>, for <nlearn|user>) → F<n>`. When the user declines a question `for user` ("no preference", "you decide"), tick it `→ Q<new>` and append `Q<new>` for the phase that will settle it. Report open risks to the user; the human runs the next phase, usually `ndesign`.

Done when every question from step 1 is ticked or still open with a reason, and every section of `.ndev/discovery.md` is filled.

## Backtrack

When a trigger below fires, stop. Append each gap to `.ndev/questions.md` as `- [ ] Q<n>: <gap> (from nlearn/<user|agent>, for <phase>) stale: <artifacts or none>`, listing the downstream artifacts that rerun may make stale. Name the phase for the user to run. The user decides.

- Findings contradict the objectives, or make a non-goal unavoidable: `nstart`.

## Discovery template

```markdown
# Discovery: <topic>

## Problem & Objectives

Cite the objectives by ID from `.ndev/brief.md`. Restate scope and non-goals only when the brief is missing.

## Reference Patterns

### F1: <convention>

- Source: <file path or doc>
- Applies to: <touched area>
- Answers: Q<n> (when any)
- Concern: <topic> | other (when § Control lists focus topics)

## Assumptions & Validation

### F2: <assumption>

- Source: <file path | spike path and observed output | doc | user>
- Status: verified | refuted | unverified | Superseded by F<n>: <reason>
- Ruling (when unverified): accepted | rejected: <reason> — by user | agent (delegated: <scope>)
- Answers: Q<n> (when any)
- Concern: <topic> | other (when § Control lists focus topics)

## Identified Risks & Spikes

### F3: <risk or constraint>

- Source: <spike path and observed output, edge case, or file path>
- Ruling: accepted | rejected: <reason> — by user | agent (delegated: <scope>)
- Concern: <topic> | other (when § Control lists focus topics)

## Walkthrough

- F1–F<n>: Approved: user | agent (delegated: <scope>)

With focus topics, list the findings decided outside focus on their own line.
```
