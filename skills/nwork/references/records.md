# Records: format `nwork/1`

Project state lives under `.nwork/`:

```text
.nwork/
├── now.md      current-state view: summaries and links
└── items/      one record per item that can be revised on its own
```

The records in `items/` are the authority. `now.md` only summarises them and links to them. When `now.md` and a record disagree, the record wins: repair `now.md`.

## When to create a record

Create a record for information that can be revised on its own: an objective, a meaningful open question, a finding, a decision, a policy, or a work slice. Put routine implementation details in the code or in the work slice that contains them.

Do not create a question for something you can check now. Check it, then record the finding.

## IDs and filenames

| Prefix | Meaning |
|---|---|
| `O` | Objective |
| `Q` | Meaningful unresolved question |
| `F` | Finding |
| `D` | Decision |
| `P` | Scoped policy, including the working agreement |
| `T` | Work slice |

- An ID is the prefix and a number with no padding: `O1`, `T12`.
- Each prefix has its own sequence. The next ID is the highest existing number for that prefix plus one, superseded records included.
- IDs are unique. Never reuse or renumber an ID, and never delete a record.
- The filename is `<ID>-<slug>.md` in `.nwork/items/`. The slug is lowercase words joined by hyphens. Keep the filename when the title changes, so links still resolve.

## Record layout

```markdown
# F7: Conditional-write behavior

Status: verified
Validity: current
Topics: storage, recovery
Depends on: [F2](F2-store-client.md)
Serves: [O1](O1-resume-without-loss.md)
Answers: [Q3](Q3-retry-duplicates.md)

## Claim

The store rejects a conditional write when the key exists.

## Evidence

What was checked, the source, and the observed result.

## History

- 2026-03-02: created as verified. Spike run against the local store.
```

- The first line is `# <ID>: <title>`. The ID matches the filename.
- The metadata block comes directly after the title, one `Key: value` per line, in this order: `Status`, `Validity`, `Topics`, `Depends on`, `Serves`, `Answers`, `Superseded by`.
- `Status`, `Validity`, and `Topics` are required. Write a relationship line only when it applies; never leave one empty.
- `Topics` is a comma-separated list of short lowercase topics. Reuse the topics that existing records use; the working agreement's Focus refers to them.
- The type-specific sections follow (see below). `## History` is always the last section.

## Status and validity

**Status** is where the item is in its own lifecycle. **Validity** is whether its basis still holds. They change independently: a work slice can stay `implemented` while its governing assumptions need revalidation.

| Type | Statuses |
|---|---|
| Objective | `active`, `complete`, `cancelled` |
| Question | `open`, `resolved` |
| Finding | `unverified`, `verified`, `refuted` |
| Decision | `proposed`, `decided` |
| Policy | `proposed`, `active` |
| Work slice | `pending`, `in-progress`, `implemented`, `pass`, `fail`, `accepted` |

| Validity | Meaning |
|---|---|
| `current` | The basis holds, as far as the records show. |
| `needs-revalidation` | Something this item relies on changed or was challenged. Reassess the item before relying on it. This does not say the item is wrong. |
| `superseded` | Another item replaces this one. `Superseded by` is required. Keep the record for its history. |

A refuted finding keeps its record and stays `current`: the refutation holds. The items that rely on it need revalidation. When a corrected finding replaces it, mark it `superseded`.

## Relationships

| Label | Written on | Points to |
|---|---|---|
| `Depends on` | an item that relies on prerequisites | the findings, decisions, policies, or slices it relies on |
| `Serves` | an item that contributes to objectives | the objectives |
| `Answers` | an item that resolves questions | the questions |
| `Superseded by` | an obsolete item | its replacement |

- Each value is a comma-separated list of links `[<ID>](<filename>)`, with nothing else on the line.
- Write each relationship once, on the item that depends, serves, answers, or is replaced. To find the reverse direction, search the records for the link, for example `grep -l '\[P2\](' .nwork/items/*.md`.
- Every link resolves to an existing record.
- `Superseded by` is present if and only if `Validity: superseded`.
- An item that is `current` must not depend on a superseded item, on one that needs revalidation, or on a refuted finding. When that happens, revalidate the item, or mark it `needs-revalidation`.

## Type-specific sections

| Type | Sections, in order |
|---|---|
| Objective | `Outcome`; `Out of scope` when any |
| Question | `Question`; `Who answers`: `investigation` or `user`, with a reason |
| Finding | `Claim`; `Evidence`: what was checked, the source, and the observed result |
| Decision | `Options` when compared; `Recommendation` while proposed; `Choice` once decided; `Rationale`; `Evidence`; `Decided by` |
| Policy | `Rule`; `Scope`; `Exceptions` when any; `Options` when compared; `Rationale`; `Evidence` when any; `Adopted by` |
| Working agreement | see [Working agreement](#working-agreement) |
| Work slice | `Scope`; `Expected behavior`; `Acceptance`; `Latest build`; `Latest review` |

Evidence records what was observed, never what was expected. Name the source: a file path, a command and its output, a document, or `user` with their words. A finding that rests on an assumption stays `unverified` until something checks it, or until the user accepts it under the working agreement; record which.

A work slice:

- `Acceptance` holds one runnable command that checks the expected behavior.
- `Latest build` records the date, the command that was run, the observed result, and `Basis:`, the IDs the build relied on. Keep the entry when the basis changes, so that earlier results stay distinct from current assurance. Older builds move to History as one line each.
- `Latest review` records the date, the verdict (`pass` or `fail`), the reasons, and `Accepted by` once accepted. A review that stops because its basis changed records no verdict, and says why.
- Write `None yet.` in `Latest build` or `Latest review` before the first entry.

## Attribution

`Decided by`, `Adopted by`, and `Accepted by` take one of these values:

- `user (<date>): "<the user's words>"`
- `agent (delegated: [P1](P1-working-agreement.md) § Authority: <delegated item>)`
- `pending: reserved for user ([P1](P1-working-agreement.md) § Authority: <reserved item>)`, while the choice waits for the user

Only a user instruction creates a delegation. Quote it in the working agreement's `Established by`.

## Working agreement

The working agreement is a policy titled `Working agreement`, scoped to the current objectives. Its sections:

- `Scope`: links to the objectives it covers.
- `Focus`: the topics the user wants to examine, each with a line on what it covers. Focus changes presentation only.
- `Authority`: two lists, `Delegated to the agent` and `Reserved for the user`.
- `Detail`: `brief`, `normal`, or `deep`. The default is `brief`.
- `Established by`: the user's instructions that set the agreement, quoted with dates.

A change of focus or detail edits those sections only. It does not create or revoke authority. A change of authority needs the user's words, quoted in `Established by`.

## Revision

When evidence or a decision changes:

1. Update the changed item: its status or validity, and a History line with the reason.
2. When a new item replaces it, set `Superseded by` and `Validity: superseded` on the old item. Do not delete it.
3. Find the dependants: search for links to the changed item, then for links to each dependant, transitively.
4. Mark each affected dependant `needs-revalidation`, with a History line that names the trigger. Leave its status as it is.
5. Revalidate before affected work proceeds. Record the outcome in History: still valid against the new basis (restore `current` and update its links), revised, or superseded. Revalidating is a choice under the working agreement. You may revalidate an item that the user decided or adopted, or one that the agreement reserves, when the new evidence leaves its stated rationale, and its consequences as the user saw them, unchanged: the History line says what was checked and why both still hold. Its status and attribution stay as they are. When the evidence refutes a premise of the rationale, or adds a consequence that the user did not see, the item needs the user's words, or a clause of the agreement that delegates exactly that. If you would need to ask whether the user still accepts it, it is not revalidated.
6. Update `now.md`.

## `now.md`

```markdown
# Now: <project>

Format: nwork/1
Updated: <YYYY-MM-DD>

## Goal

<one or two lines>; [O1](items/O1-<slug>.md), …

## Direction

<the current approach, in two or three lines, with links to the governing policies and decisions>

## Implemented and verified

- [T1](items/T1-<slug>.md): <one line>

## Under revalidation

- [P2](items/P2-<slug>.md): <one line>, challenged by [F3](items/F3-<slug>.md)

## Needs you

- [D2](items/D2-<slug>.md): <the choice, and the recommendation>

## Eligible work

- [T4](items/T4-<slug>.md): <one line>

## Next

<one recommended action, with its links>

## Working agreement

[P1](items/P1-working-agreement.md): focus <topics>; detail <level>.
```

- The second line after the title is exactly `Format: nwork/1`.
- Write one line per item: a link and a summary. Details stay in the records. Aim for about one screen.
- Write `None.` in an empty section. Omit `Under revalidation` when nothing needs revalidation.
- Never link a superseded item, not even in a sentence. Link its replacement instead.
- `Implemented and verified` lists only work slices with status `pass` or `accepted` and validity `current`.
- `Needs you` lists choices reserved for the user, questions that only the user can answer, and contradictions that the agent cannot resolve within its authority.
- `Eligible work` lists only work slices that can proceed now: status `pending`, `in-progress`, or `fail` (ready to build) or `implemented` (ready to review); validity `current`; every dependency `current` and settled (`verified`, `decided`, `active`, `pass`, or `accepted`); and no choice reserved for the user still pending.
