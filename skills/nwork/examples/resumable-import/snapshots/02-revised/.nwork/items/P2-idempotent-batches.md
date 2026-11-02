# P2: Commit each batch once; resume at the first uncommitted batch

Status: active
Validity: needs-revalidation
Topics: recovery
Depends on: [F1](F1-atomic-batch-writes.md)
Serves: [O1](O1-resume-without-loss.md)
Answers: [Q1](Q1-in-flight-batch.md), [Q2](Q2-restart-point.md), [Q4](Q4-duplicate-rows.md)

## Rule

Guarantee: a rerun on the same source file loses no row and stores no row twice.

Mechanism:

- Each batch goes to the store as one batch write that also creates the marker key `imports/<import-id>/batches/<n>`, on the condition that the marker does not exist.
- When the condition fails, the batch was already committed: skip it.
- A rerun resumes at the first batch that has no marker.

## Scope

Interrupted imports of an unchanged source file, for [O1](O1-resume-without-loss.md).

## Governs

Each other way that an import of an unchanged source file can stop part-way, which no question asks about yet. For example:

- the store times out, or refuses a request, in the middle of a batch;
- a rerun that itself dies, so that a third run resumes after two partial ones.

The agent settles how each such case resumes without asking, by this rule.

## Exceptions

- The source file changed between runs. Batch numbers then point to different rows ([F2](F2-positional-rows.md)), so this rule cannot apply. Kept apart as [Q3](Q3-changed-source.md).

## Rationale

One rule answers the three crash questions. The batch in flight was stored with its marker, or not at all ([F1](F1-atomic-batch-writes.md)). So resuming at the first missing marker neither skips nor repeats rows.

## Adopted by

user (2026-03-02): "Yes, that rule works. Go with it."

## History

- 2026-03-02: created as proposed, as one principle for Q1, Q2, and Q4, with the changed-source case shown as an exception.
- 2026-03-02: active, adopted by the user.
- 2026-03-03: needs revalidation. The mechanism rests on [F1](F1-atomic-batch-writes.md), which [F3](F3-split-batch-writes.md) refutes for batches above 100 items. The guarantee is unchanged; the mechanism may not deliver it.
