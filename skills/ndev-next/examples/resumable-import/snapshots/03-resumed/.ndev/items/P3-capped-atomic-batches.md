# P3: Commit each batch of at most 100 items once; resume at the first uncommitted batch

Status: active
Validity: current
Topics: recovery
Depends on: [F4](F4-atomic-batch-size.md)
Serves: [O1](O1-resume-without-loss.md)
Answers: [Q1](Q1-in-flight-batch.md), [Q2](Q2-restart-point.md), [Q4](Q4-duplicate-rows.md)

## Rule

Guarantee: a rerun on the same source file loses no row and stores no row twice. Unchanged from [P2](P2-idempotent-batches.md).

Mechanism:

- A batch holds at most 99 rows, so that the batch write, with its marker, stays within one request of 100 items.
- Each batch goes to the store as one batch write that also creates the marker key `imports/<import-id>/batches/<n>`, on the condition that the marker does not exist.
- When the condition fails, the batch was already committed: skip it.
- A rerun resumes at the first batch that has no marker.

## Scope

Interrupted imports of an unchanged source file, for [O1](O1-resume-without-loss.md).

## Exceptions

- The source file changed between runs. Batch numbers then point to different rows ([F2](F2-positional-rows.md)), so this rule cannot apply. Kept apart as [Q3](Q3-changed-source.md).

## Rationale

The guarantee of [P2](P2-idempotent-batches.md) holds only for writes that the store commits all or nothing. [F4](F4-atomic-batch-size.md) shows that writes of at most 100 items do. Capping the batch keeps the guarantee, at a cost of about 8% in import time.

## Adopted by

agent (delegated: [P1](P1-working-agreement.md) § Authority: recovery mechanics that keep the guarantees of a policy the user adopted, including replacing such a policy with one that keeps the same guarantees)

## History

- 2026-03-05: created as active, to replace P2 after its basis was refuted. Same guarantee, capped batch size.
