# F4: A batch write of at most 100 items stores all of them or none

Status: verified
Validity: current
Topics: storage, recovery
Depends on: [F3](F3-split-batch-writes.md)
Serves: [O1](O1-resume-without-loss.md)
Answers: [Q5](Q5-atomic-batch-limit.md)

## Claim

A Kestrel batch write of at most 100 items goes out as one request, and the store commits it all or nothing, with its condition. Above 100 items, [F3](F3-split-batch-writes.md) applies.

## Evidence

Illustrative evidence: this example is fictional.

- Checked: the spike of [F3](F3-split-batch-writes.md) with 99 rows plus the marker, killed at a random point during the write, 50 trials. Then a full import of `samples/orders-large.csv` (200,000 rows) at 99 and at 500 rows per batch.
- Source: the spike output and the import timings, against a local Kestrel server, client 4.2.
- Observed: 31 trials stored all 100 items; 19 stored none; none stored part of a batch. The import took 8% longer at 99 rows per batch (71 s against 66 s).

## History

- 2026-03-05: created as verified.
