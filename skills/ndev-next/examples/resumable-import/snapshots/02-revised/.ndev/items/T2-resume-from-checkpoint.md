# T2: Resume from the checkpoint

Status: implemented
Validity: needs-revalidation
Topics: recovery
Depends on: [P2](P2-idempotent-batches.md), [D1](D1-checkpoint-key.md)
Serves: [O1](O1-resume-without-loss.md)

## Scope

`orderload/importer.py`, `orderload/checkpoint.py` (new), and `tests/test_resume.py` (new).

## Expected behavior

- Each batch is written with its marker, on the condition of [P2](P2-idempotent-batches.md). When the condition fails, the importer skips the batch.
- A rerun reads the checkpoint ([D1](D1-checkpoint-key.md)) and resumes at the next batch.
- After a kill at any point and a rerun, every source row is in the store exactly once.

## Acceptance

`pytest tests/test_resume.py`

## Latest build

- Date: 2026-03-02
- Command: `pytest tests/test_resume.py`
- Observed: 6 passed. Illustrative: this example is fictional. The tests set the batch size to 10 rows, to keep them fast.
- Basis: [P2](P2-idempotent-batches.md), [D1](D1-checkpoint-key.md), [F1](F1-atomic-batch-writes.md)

## Latest review

- Date: 2026-03-03
- Verdict: none. The review stopped because its basis changed: [F3](F3-split-batch-writes.md) shows that the production batch size, 500 rows, can be stored in part. The code matches its expected behavior; the tests use 10-row batches and so do not reach the split.

## History

- 2026-03-02: created as pending.
- 2026-03-02: implemented. Acceptance command passed.
- 2026-03-03: needs revalidation: it depends on [P2](P2-idempotent-batches.md) and [D1](D1-checkpoint-key.md), which need revalidation after [F3](F3-split-batch-writes.md). The build result of 2026-03-02 rests on the refuted [F1](F1-atomic-batch-writes.md) and no longer counts as assurance.
