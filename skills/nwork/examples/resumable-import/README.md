# Example: resumable import

A worked example of the `nwork/1` records ([specification](../../references/records.md)).

**This example is fictional.** `orderload`, the Kestrel store and its client, the files, and every measurement are invented. Each finding labels its evidence as illustrative.

## Scenario

`orderload import <file>` reads an orders CSV and writes it to a key-value store in batches of 500 rows. The user asks:

> If an import dies halfway, I want to rerun it and end up with every order exactly once. And show me how far along it is.

## Snapshots

Each snapshot is the `.nwork/` tree at one point. Start with its `now.md`, then follow the links.

| Snapshot | Date | State |
|---|---|---|
| [`01-working`](snapshots/01-working/.nwork/now.md) | 2026-03-02 | A recovery policy is adopted, one exception waits for the user, and the resume slice is built. |
| [`02-revised`](snapshots/02-revised/.nwork/now.md) | 2026-03-03 | A new finding challenges the policy. Its dependants need revalidation; the progress slice stays eligible. |
| [`03-resumed`](snapshots/03-resumed/.nwork/now.md) | 2026-03-10 | A replacement policy is in place. A fresh session reads the files and finds one next action. |

What the example shows, and where:

| Behavior | Where to look |
|---|---|
| A current-state landing page | `now.md` in each snapshot |
| Several recovery questions reduced to one governing policy | Q1, Q2, Q4 and P2 in `01-working` |
| A concrete exception that gets separate treatment | Q3, F2, and D2 in `01-working` |
| A new finding that challenges the policy | F3 in `02-revised` |
| Affected decisions and work marked for revalidation | F1, P2, D1, T2 in `02-revised` |
| Independent work that stays eligible | T1 in `02-revised` |
| A return without the earlier conversation | `03-resumed`, and [Return](#return-2026-03-10) below |
| Focus changes the presentation, not the authority | P1 in `03-resumed`, and [Focus and authority](#focus-and-authority) below |

## Transitions

### Start to `01-working`

**Working agreement.** Before it asks anything else, the agent proposes one combined agreement: focus, authority, and detail, with a recommendation. The user replies: "You handle the mechanics. Check with me on anything users will see, or anything that could lose or duplicate rows. I mostly care about recovery. Keep it short." [P1](snapshots/01-working/.nwork/items/P1-working-agreement.md) quotes that reply as the source of every delegation.

**Principle first.** Four questions come up about crashes (Q1 to Q4). The agent checks the store's behavior first ([F1](snapshots/01-working/.nwork/items/F1-atomic-batch-writes.md)), because a question about evidence calls for investigation. Then it groups the questions, and asks one question about the principle instead of four separate ones:

> Q1, Q2, and Q4 have one answer. I recommend this rule: each batch commits once, all or nothing, with a marker key; a rerun resumes at the first batch without a marker.
>
> Effect: a crash costs the work on one batch, never a row, and a rerun needs nothing from you.
>
> One case falls outside the rule: the source file changed between runs (Q3). Batch numbers then point to other rows (F2), so it needs its own choice. It comes next.
>
> Adopt the rule?

The user adopts it, and the rule becomes [P2](snapshots/01-working/.nwork/items/P2-idempotent-batches.md). Its `Exceptions` section points to Q3. The changed-source case becomes [D2](snapshots/01-working/.nwork/items/D2-refuse-changed-source.md): proposed, with a recommendation, and reserved for the user, because it is user-visible and can lose rows. The user decides the progress format ([D3](snapshots/01-working/.nwork/items/D3-progress-line.md)) right away, but leaves D2 for later.

**Delegated choices.** The agent decides the checkpoint key ([D1](snapshots/01-working/.nwork/items/D1-checkpoint-key.md)) alone, and names the clause of P1 that allows it.

**Local readiness.** [T2](snapshots/01-working/.nwork/items/T2-resume-from-checkpoint.md) is built while D2 is still open, because T2 does not depend on D2. [T3](snapshots/01-working/.nwork/items/T3-source-change-guard.md) depends on D2, so it waits.

### `01-working` to `02-revised`

The review of T2 asks why the tests use 10-row batches. A larger spike shows that the client splits writes above 100 items, and that a crash can store part of a batch: [F3](snapshots/02-revised/.nwork/items/F3-split-batch-writes.md).

The agent follows the links from the changed item to its dependants:

```text
F3 refutes F1 ─▶ P2 (depends on F1) ─▶ D1 (depends on P2) ─▶ T2 (depends on P2, D1)
```

- [F1](snapshots/02-revised/.nwork/items/F1-atomic-batch-writes.md) becomes `refuted`. Its validity stays `current`: the refutation holds.
- [P2](snapshots/02-revised/.nwork/items/P2-idempotent-batches.md), [D1](snapshots/02-revised/.nwork/items/D1-checkpoint-key.md), and [T2](snapshots/02-revised/.nwork/items/T2-resume-from-checkpoint.md) become `needs-revalidation`. Their statuses stay as they were: P2 is still `active`, and T2 is still `implemented`. T2 keeps its build entry of 2026-03-02, and its History says that result no longer counts as assurance. The review stops without a verdict.
- D2, T3, D3, and [T1](snapshots/02-revised/.nwork/items/T1-progress-line.md) do not depend on F1, so they keep `current`. T1 is still eligible.
- "What batch size is safe?" is a question about evidence, so it becomes [Q5](snapshots/02-revised/.nwork/items/Q5-atomic-batch-limit.md) for investigation, not for the user.

`now.md` is updated before the report, and gains an `Under revalidation` section.

### `02-revised` to `03-resumed`

On 2026-03-05, the agent investigates Q5. [F4](snapshots/03-resumed/.nwork/items/F4-atomic-batch-size.md) shows that writes of at most 100 items stay all or nothing, at a cost of about 8% in import time. F4 supersedes F1.

[P3](snapshots/03-resumed/.nwork/items/P3-capped-atomic-batches.md) caps batches at 99 rows and keeps the guarantee of P2 word for word. Because the guarantee does not change, P1 delegates this replacement, and P3's `Adopted by` names that clause. [P2](snapshots/03-resumed/.nwork/items/P2-idempotent-batches.md) keeps its file and its History, with `Validity: superseded` and a link to P3.

[D1](snapshots/03-resumed/.nwork/items/D1-checkpoint-key.md) is revalidated against P3: the choice holds, so it now depends on P3 and is `current` again. [T1](snapshots/03-resumed/.nwork/items/T1-progress-line.md) is built and passes review. The session ends before the agent revalidates [T2](snapshots/03-resumed/.nwork/items/T2-resume-from-checkpoint.md). T2's History records the rework it expects.

### Return, 2026-03-10

A new session starts with no earlier conversation. The user writes: "Where are we? Today I'd rather look at the progress side."

1. **Orient.** The agent reads `now.md`, P1, and the records that `now.md` links to.
2. **Reconcile.** The agent checks the claims in `now.md` against the records and the code:
   - `now.md`, as the last session left it, still listed D1 under revalidation. The D1 record says that D1 was revalidated on 2026-03-05, so the record wins, and the agent repairs `now.md`.
   - It runs T1's acceptance command again: 5 passed.
   - `orderload/batches.py:12` still sets `BATCH_SIZE = 500`, which confirms that T2 does not meet P3.
3. **Focus.** The agent changes only the `Focus` section of P1, and adds the user's words to `Established by`. Authority and detail do not change.
4. **Report**, briefly, with focus on progress:

> **Progress (your focus):** the progress line is done. It is built, reviewed, and passes its tests again today (`pytest tests/test_progress.py`: 5 passed). [T1]
>
> **Needs you:** what a rerun does when the source file changed. I recommend refusing, and asking for `--restart`. [D2]
>
> **Changed since you last looked:** large batch writes can be stored in part, so I capped batches at 99 rows. The guarantee is the same, and imports take about 8% longer [P3, F4]. The resume code still uses 500-row batches. Its earlier passing tests no longer count. [T2]
>
> **Next:** rework the resume code for the cap, then test it at the real batch size.

## Focus and authority

On-request views are rendered in the conversation from the records. They are not stored. Here is the same `03-resumed` state, rendered twice in brief detail.

With focus on **recovery**:

> **Recovery (your focus):** batches are capped at 99 rows [P3]. Writes above 100 items can be stored in part [F3]; at 99 rows plus the marker, 50 killed writes stored all or nothing [F4]. That replaces the uncapped rule [P2], with the same guarantee, and about 8% slower imports. The checkpoint design still holds [D1]. The resume code still sends 500-row batches, so its earlier test result no longer counts [T2].
>
> **Needs you:** a changed source file. I recommend refusing, and asking for `--restart`. [D2]
>
> **Also:** the progress line is done. [T1]
>
> **Next:** rework the resume code for the cap, then test it at the real batch size.

With focus on **progress**: the report under [Return](#return-2026-03-10).

In both views, the following parts stay the same:

- P1 § Authority. The agent replaced P2 with P3 under delegation, whatever the focus was. Taking recovery out of focus revokes nothing, and putting progress in focus delegates nothing.
- The item that needs the user, D2, even though D2 is outside the progress focus. Brief detail keeps consequential blockers and contradictions.
- The next action.

Focus changes only the order of the report and the depth of each part.
