# D1: Find the resume point from a checkpoint key

Status: decided
Validity: needs-revalidation
Topics: recovery
Depends on: [P2](P2-idempotent-batches.md)
Serves: [O1](O1-resume-without-loss.md)

## Options

- List the batch markers at startup and find the first gap. No extra write, but startup time grows with the size of the import.
- Write `imports/<import-id>/checkpoint` after each committed batch, holding the batch number. One extra write per batch, and a constant startup time.

## Choice

The checkpoint key. A rerun reads it and resumes at the next batch. When the crash fell between a batch write and the checkpoint write, the next batch's condition fails, and the import skips it, as [P2](P2-idempotent-batches.md) requires.

## Rationale

Startup time stays constant. Correctness still rests on the markers, not on the checkpoint.

## Evidence

Illustrative evidence: this example is fictional. Against a local Kestrel server, listing 4,000 markers took 6.1 s; reading one key took 3 ms.

## Decided by

agent (delegated: [P1](P1-working-agreement.md) § Authority: recovery mechanics that keep the guarantees of a policy the user adopted)

## History

- 2026-03-02: created as decided.
- 2026-03-03: needs revalidation: it depends on [P2](P2-idempotent-batches.md), which needs revalidation after [F3](F3-split-batch-writes.md).
