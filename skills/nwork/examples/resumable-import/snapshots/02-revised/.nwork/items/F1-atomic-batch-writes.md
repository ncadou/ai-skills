# F1: A conditional batch write stores all of its items or none

Status: refuted
Validity: current
Topics: storage, recovery
Serves: [O1](O1-resume-without-loss.md)

## Claim

A Kestrel batch write with a condition on one key stores every item in the request, or none of them.

## Evidence

Illustrative evidence: this example is fictional.

- Checked: a spike, `/tmp/spike_atomic.py`, sends a batch of 10 rows plus a marker key, on the condition that the marker does not exist. It kills the process at a random point during the write. 20 trials.
- Source: the spike, run against a local Kestrel server, client 4.2.
- Observed: 11 trials stored all 11 items; 9 stored none. No trial stored part of a batch.

## History

- 2026-03-02: created as verified.
- 2026-03-03: refuted by [F3](F3-split-batch-writes.md). The spike tested 10-row batches only; batches above 100 items can be stored in part.
