# Now: orderload resumable import

Format: ndev-next/1
Updated: 2026-03-03

## Goal

A rerun of an interrupted import finishes it with every row stored once ([O1](items/O1-resume-without-loss.md)), and the user sees progress ([O2](items/O2-show-progress.md)).

## Direction

The recovery rule's guarantee stands, but its mechanism is in doubt: the store client splits batches above 100 items, so a crash can store part of a batch ([F3](items/F3-split-batch-writes.md)). Next, measure the size that stays all or nothing ([Q5](items/Q5-atomic-batch-limit.md)). Progress is one line on stderr ([D3](items/D3-progress-line.md)).

## Implemented and verified

None.

## Under revalidation

- [P2](items/P2-idempotent-batches.md): one marker per batch, resume at the first uncommitted batch. Its basis was refuted by [F3](items/F3-split-batch-writes.md).
- [D1](items/D1-checkpoint-key.md): the checkpoint key. Depends on P2.
- [T2](items/T2-resume-from-checkpoint.md): resume from the checkpoint. Built and its tests passed on 2026-03-02, but they used 10-row batches; that result no longer counts.

## Needs you

- [D2](items/D2-refuse-changed-source.md): what a rerun does when the source file changed. Recommended: refuse, and require `--restart`.

## Eligible work

- [T1](items/T1-progress-line.md): progress line. Ready to build; it does not depend on how batches commit.

## Next

Investigate [Q5](items/Q5-atomic-batch-limit.md) with a spike. If a capped batch stays all or nothing, replace the mechanism within the same guarantee; otherwise the guarantee itself comes back to you.

## Working agreement

[P1](items/P1-working-agreement.md): focus recovery; detail brief. Reserved for you: user-visible behavior, and any choice that risks lost or duplicate rows.
