---
name: nwork
description: Work on a project from its nwork records, within the working agreement. Start, continue, or resume.
argument-hint: "request, or nothing to continue"
disable-model-invocation: true
---

Work on the project as one agent. Investigate, decide, build, and review, in the order that readiness permits. The user steers through the conversation.

The project state is under `.nwork/`, in the format `nwork/1`. **Read [`references/records.md`](references/records.md) before you read or write a record.** It specifies every record, `now.md`, attribution, and the revision procedure. The records are the authority: take the state from the files, not from memory. A fresh session and a continuing one stand on the same footing.

Each date that you write (History, builds, reviews, attributions, `Updated`) is the date of the event. Get it from `date +%F` on the day you write it. Do not take it from the conversation, the session context, or the records: a session can last several days.

## Entry

Look at `.nwork/`:

- No `.nwork/`, or an empty one: do [Start](#start), then the [loop](#operating-loop).
- `.nwork/now.md` reads `Format: nwork/1`: do the loop.
- Other contents: stop. Tell the user that `.nwork/` holds records in another format, which this skill does not migrate. Change nothing; the user decides.

## Start

1. Read the request and the code it touches, enough to propose objectives and a working agreement.
2. Propose, in one message, the objectives (one line each, with what is out of scope) and one combined working agreement: focus, authority, and detail, with your recommendation. Recommend that you decide mechanics that the user can review later, and that the user keep choices that are user-visible, hard to reverse, or that risk data. When the user keeps acceptance, recommend one acceptance per objective rather than one per slice (see [Review](#review)). In the same message, ask each question that you already know the user must answer under the proposed agreement, each with its ID and your recommendation, so that one reply can settle the agreement and the questions.
3. Write the objectives, P1 with `Status: proposed`, each known question as a `proposed` decision or an `open` question, and `now.md` with all of them under `Needs you`. Run the record checker, as [Maintain state](#5-maintain-state) says. Stop and wait.
4. When the user answers, apply their changes, set P1 `active`, and quote their words under `Established by`. Record each answer to a question with the user's words; a question left unanswered stays under `Needs you`.

When the request itself states focus, authority, and detail, skip the proposal and record P1 as `active` from those words. Until P1 is active, only investigate: make no choice, and change no project code.

Done when the objectives and an active P1 exist, and `now.md` links to them.

## Operating loop

Every invocation runs these steps. Write each consequential change to the records when you make it, so that an interrupted session leaves the files true.

### 1. Orient

Read `now.md`, P1, and every record that `now.md` links to or that the request touches. Find related records by `Topics`, and by searching for links (records.md § Relationships).

Done when you can state the goal, the direction, what needs the user, and the eligible work, from the files alone.

### 2. Reconcile

Check each claim that this session will rely on:

- `now.md` against the records and the rules of records.md § `now.md`. When they disagree, the record wins: repair `now.md`.
- Each slice that `now.md` lists as implemented and verified, and each slice that the packet builds on: run its acceptance command again, when it is cheap.
- Each statement about the code that the packet relies on: a constant, a signature, a file.

A result that agrees with the records needs no record; report it. A result that contradicts a record is new evidence: follow [Revision](#revision).

Done when every claim the packet relies on is checked, or named as unchecked in the report, and every discrepancy is repaired or recorded.

### 3. Choose a work packet

The packet is what the user asked for. When the user only asks to continue, it is the `Next` action of `now.md`, and the work that becomes eligible inside it. Say the packet in one line, then start; do not wait.

Readiness is local. A slice that waits for the user does not stop other eligible work.

Done when the packet is stated, and each part of it is eligible or has a named blocker.

### 4. Work

Do the work that each part needs: [investigate](#investigate), [decide](#decide), [build](#build), or [review](#review). Continue until the packet is complete, a choice reserved for the user blocks everything left in it, or an effort limit the user stated is reached. When a reserved choice blocks one part, record it, and continue with the parts that do not depend on it.

Done when one of those three conditions holds.

### 5. Maintain state

Bring the records up to date with this session: statuses, validity, relationships, History lines, and dependants of anything that changed. Then rewrite `now.md` from the records.

Then run the record checker, [`scripts/check_records.py`](scripts/check_records.py), from the project root: `python3 <skill folder>/scripts/check_records.py`, where `<skill folder>` is the folder of this file. It prints `ok: <n> records`, or one problem per line. Fix each problem by the rules of records.md (a `current` item that depends on a stale one calls for [Revision](#revision)), and run it again until it prints `ok`. Exit status 2 means that it found no `.nwork/`: run it from the project root. It does not check that `Eligible work` is complete, or that an attribution is justified: check those yourself.

When `python3` is missing, or the script fails with an error instead of a list of problems, check by hand that every link resolves, `Superseded by` is present exactly on superseded records, and no `current` item depends on an item that is superseded, needs revalidation, or is refuted. The report then says "checker not run", with the reason.

Done when the checker prints `ok`, or the checks by hand hold, and every section of `now.md` follows records.md § `now.md`.

### 6. Report

Report at the detail level of P1, or the level the user asks for: see [Reporting](#reporting). Ask the questions for the user under `Needs you`, grouped as [Questions](#questions) describes.

Done when the report states the result, what needs the user, the remaining uncertainty, and one next action.

## Working agreement

P1 sets three things, kept separate:

- **Focus**: the topics the user wants to examine. Focus changes the presentation only: the order of the report and the depth of each part.
- **Authority**: the choices delegated to you, and the choices reserved for the user. Only the user's words create or revoke a delegation. Quote them under `Established by`.
- **Detail**: `brief`, `normal`, or `deep`. The default is `brief`.

A request about one report ("more detail on that") changes nothing in P1. When the user changes focus or detail for the work ahead, edit only those sections, quote the words under `Established by`, and add a History line that says authority did not change. When the words could also change authority ("I don't care about naming any more"), apply them as focus, and ask whether they also delegate.

When it is not clear whether a choice is delegated, treat it as reserved: propose it, with a recommendation. When several such choices are of one kind, propose one amendment to P1 § Authority instead of asking about each.

P1 covers the objectives in its `Scope`. A new objective is outside it until the user extends it: propose the extension together with the objective.

Each delegated choice names its clause: `agent (delegated: [P1](...) § Authority: <clause>)`. An existing policy applies within its recorded `Scope`. To apply it more widely, record a decision, under the same rules of authority as any other choice.

## Questions

Sort each question that comes up:

- **Evidence**: what the code, a library, data, or a system does. Investigate; do not ask. When no check is possible, record an `unverified` finding, and ask the user to accept it, supply the fact, or leave it open.
- **Preference or reserved tradeoff**: what the user wants, or a choice that P1 reserves. Ask the user.
- **Delegated**: decide it, and record the clause.

Principle first. Before you ask the user:

1. Check the active policies. A question that a policy answers within its scope is not a question.
2. Group the related questions.
3. Find the rationale they share, when one exists.
4. Recommend one governing choice that answers the group: a decision, or a scoped policy with its rule, its scope, and its rationale. See [Policy or decision](#policy-or-decision).
5. Show its effect on representative cases, and each genuine exception. Keep an exception apart, as its own question or decision, instead of stretching the principle to cover it.

Lead with the governing choice, in a few lines, and end with one question about it. Ask about each exception separately, after it: an answer about the principle does not settle an exception. Keep the options and evidence in the records, and give them when the user asks.

Record the governing choice before you ask, as a `proposed` policy or a `proposed` decision, with `Answers` links to the questions it settles. When the user adopts a policy, set it `active`, quote their words under `Adopted by`, and resolve the questions. A decision follows [Decide](#decide).

### Policy or decision

A policy is a standing rule. Inside its scope, it settles later questions without asking the user (step 1 above). So adopting a policy hands you those future cases.

Propose a policy only when you can name cases that it will settle, that no record asks about yet, and that the current objectives make likely. Otherwise, record one decision, even when it answers several questions. When in doubt, record a decision.

Test: when every case that the rule settles is already a question in the records, it is a decision.

When you propose a policy:

- Write the future cases in its `Governs` section, with one or two concrete examples, and one line that says what the user hands to you: "I settle <kind of case> without asking."
- In the proposal, add one line: "Why a policy: it also settles <the future cases> without asking you."

When you cannot write `Governs`, record a decision instead.

## Investigate

Run the smallest check that answers the question: read the code, or run a spike under `/tmp`. Record a finding with what was checked, the source, and the observed output, never the expected output. An assumption stays an `unverified` finding until a check verifies it or the user accepts it; record which. A finding that answers a question gets an `Answers` link, and the question becomes `resolved`.

## Decide

Record a decision for a choice that can be revised on its own; a routine implementation choice goes in the code or its slice. A choice that will also settle cases not asked yet is a policy: see [Policy or decision](#policy-or-decision). Give the decision its options, evidence, and recommendation. Within your authority, choose, and record the clause. Otherwise, leave it `proposed`, list it under `Needs you`, and continue with the work that does not depend on it.

## Build

Build a slice only when it is eligible:

- Its objective and scope are clear.
- Its expected behavior and a runnable acceptance command are written.
- Its dependencies are settled and `current` (records.md § `now.md`, `Eligible work`).
- Each material uncertainty is checked, or accepted within the working agreement.
- No choice reserved for the user is still pending for it.

Set the slice `in-progress`. Write the tests with the code, and cover the expected behavior and its failure modes. Make implementation choices within your authority, and document the non-obvious ones in the code. Run the acceptance command, and record `Latest build` with the observed result and its `Basis`. On a pass, set the slice `implemented`; otherwise it stays `in-progress`, with the failing result recorded. A choice that P1 reserves, or a contract that turns out to be wrong, stops the slice: record it, and continue elsewhere.

## Review

Review a slice that is `implemented`, against its record and its diff. Read the diff again; do not rely on what you remember of the build. Check:

- Every changed file is inside the slice's scope; changes outside it are named.
- The code delivers the expected behavior, and the decisions and policies the slice depends on.
- Edge cases and failure modes in scope are handled.
- The tests assert the behavior through public interfaces, at realistic sizes and inputs. Tautological tests are named.
- The latest build is a passing run of the acceptance command, on the current basis.
- No regression in the touched area.
- Types and docstrings match the code; complex logic explains its reasoning; changed public contracts update the project docs.

Record `Latest review` with the verdict and its reasons, and set `pass` or `fail`. A `fail` names what to change; the next build of the slice handles it. Set `accepted` only on the user's words, or under a delegation of acceptance in P1.

When P1 sets one acceptance per objective, ask for it once, when every slice of the objective has passed review. Work that depends on a slice at `pass` does not wait for its acceptance. List each slice by its ID, with one line on what it delivers and its verdict, so that the user can accept all of them, or add a remark or a change to any one by its ID. Apply the reply to each slice: quote the words that accept it in its `Accepted by`. A remark or a change about one slice applies to that slice only, and a slice that the user asks to change is not accepted.

## Revision

When evidence or a decision changes, follow records.md § Revision, for every changed item:

- A challenge calls for reassessment. It does not make the dependants false: mark them `needs-revalidation`, and keep their status.
- Keep the earlier build and review results in their records, and say in History that they no longer count as assurance.
- Revalidate an affected item before work that relies on it proceeds. Revalidating is a choice under P1 § Authority, like a replacement or a revised choice.
- You may revalidate a finding, or a choice that P1 delegates to you. You may also revalidate a decision or policy that the user made, or one that P1 reserves, when the new evidence leaves its stated rationale, and its consequences as the user saw them, unchanged. Record in History what you checked and why both still hold, and report it. When the evidence refutes a premise of the rationale, or adds a consequence that the user did not see, the item stays `needs-revalidation` until the user confirms or changes it, even when its wording still fits (unless a clause of P1 delegates exactly that). List it under `Needs you`, with your recommendation. Its dependants wait with it. If you would need to ask whether the user still accepts it, it is not revalidated.
- Update `now.md` before you report the new position. The report names the work that the change does not affect, and that stays eligible.

## Reporting

Write in plain language, with record IDs in brackets: `[T2]`. Put the user's focus first. Then, in this order: what needs the user, what changed since the user last looked, and the next action. In a fresh session, what changed is what the History lines record after the user's latest words quoted in the records.

The next action is one step: the one you recommend. Mention other choices and ready work in their own parts, not in the next action.

- **brief**: one to three lines per part.
- **normal**: add the reason and the evidence for each part.
- **deep**: add the options, the evidence in full, and the links.

Every level keeps the following, even when the user asks for less. Shorten each one to a few words if needed, but do not drop it:

- every item under `Needs you`, in focus or not;
- every contradiction, and every result that no longer counts as assurance;
- each assumption that the result rests on, called an assumption;
- each verification as observed: the command and its result, with its date when it is not from this session. Say "not run" for a check that you did not run.

When the user asks for a view of a topic, render it in the conversation from the records. Do not store it.
