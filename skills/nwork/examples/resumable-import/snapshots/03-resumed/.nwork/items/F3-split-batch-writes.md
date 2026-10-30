# F3: The store client splits batch writes above 100 items

Status: verified
Validity: current
Topics: storage, recovery
Serves: [O1](O1-resume-without-loss.md)

## Claim

The Kestrel client sends a batch write of more than 100 items as several requests of at most 100 items each. The store commits each request on its own. The condition applies only to the request that holds the marker key, which is the last one.

## Evidence

Illustrative evidence: this example is fictional.

- Checked: the client source; then the spike of [F1](F1-atomic-batch-writes.md), changed to 500 rows plus the marker, killed during the write, 20 trials.
- Source: `kestrel/batch.py:88` in client 4.2 (`MAX_ITEMS_PER_REQUEST = 100`, a loop over the chunks); the spike output.
- Observed: 7 trials stored part of the batch without its marker: 100, 200, 300, or 400 rows. A rerun then wrote those rows again, so they were stored twice.

## History

- 2026-03-03: created as verified. Found during the review of T2: the review asked why the acceptance tests use 10-row batches.
