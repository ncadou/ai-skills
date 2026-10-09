# Now: orderload resumable import

Format: ndev-next/1
Updated: 2026-03-10

## Goal

A rerun of an interrupted import finishes it with every row stored once ([O1](items/O1-resume-without-loss.md)), and the user sees progress ([O2](items/O2-show-progress.md)).

## Direction

Each batch of at most 99 rows commits all or nothing with a marker key, and a rerun resumes at the first uncommitted batch ([P3](items/P3-capped-atomic-batches.md), [D1](items/D1-checkpoint-key.md)). The cap keeps the original guarantee after large batch writes proved splittable ([F4](items/F4-atomic-batch-size.md)). A changed source file is an exception to that rule ([D2](items/D2-refuse-changed-source.md)). Progress is one line on stderr ([D3](items/D3-progress-line.md)).

## Implemented and verified

- [T1](items/T1-progress-line.md): progress line. Acceptance passes; review passed.

## Under revalidation

- [T2](items/T2-resume-from-checkpoint.md): resume from the checkpoint. Its code sends 500-row batches, so it does not meet [P3](items/P3-capped-atomic-batches.md). Its passing tests of 2026-03-02 no longer count.

## Needs you

- [D2](items/D2-refuse-changed-source.md): what a rerun does when the source file changed. Recommended: refuse, and require `--restart`.

## Eligible work

None. T2 needs revalidation first; [T3](items/T3-source-change-guard.md) waits for D2.

## Next

Revalidate [T2](items/T2-resume-from-checkpoint.md) against [P3](items/P3-capped-atomic-batches.md): cap batches at 99 rows, then run its acceptance at the production batch size.

## Working agreement

[P1](items/P1-working-agreement.md): focus progress; detail brief. Reserved for you: user-visible behavior, and any choice that risks lost or duplicate rows.
