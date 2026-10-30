# F2: Source rows have no stable ID

Status: verified
Validity: current
Topics: source, recovery
Serves: [O1](O1-resume-without-loss.md)

## Claim

The orders export has no column that identifies a row. Only its position does: batch `n` is whatever rows sit at that position in the file as read.

## Evidence

Illustrative evidence: this example is fictional.

- Checked: the header and three sample exports in `samples/`, and the batch numbering in `orderload/batches.py`.
- Source: `samples/orders-*.csv`; `orderload/batches.py:12` (`BATCH_SIZE = 500`, batch number from the row offset).
- Observed: `order_ref` repeats for split shipments, 41 times in 10,000 rows. No other column is unique.

## History

- 2026-03-02: created as verified.
