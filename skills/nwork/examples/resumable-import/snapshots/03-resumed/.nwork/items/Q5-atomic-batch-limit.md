# Q5: Up to what size does a batch write store all of its items or none?

Status: resolved
Validity: current
Topics: storage, recovery

## Question

[F3](F3-split-batch-writes.md) shows that a write of 500 items can be stored in part. Is a write of at most 100 items, sent as one request, stored all or nothing?

## Who answers

investigation: a spike can measure it.

## History

- 2026-03-03: created as open, after the finding that large batch writes are split.
- 2026-03-05: resolved by a spike.
