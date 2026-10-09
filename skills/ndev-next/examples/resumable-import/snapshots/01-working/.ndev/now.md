# Now: orderload resumable import

Format: ndev-next/1
Updated: 2026-03-02

## Goal

A rerun of an interrupted import finishes it with every row stored once ([O1](items/O1-resume-without-loss.md)), and the user sees progress ([O2](items/O2-show-progress.md)).

## Direction

Each batch commits all or nothing with a marker key, and a rerun resumes at the first uncommitted batch ([P2](items/P2-idempotent-batches.md), [D1](items/D1-checkpoint-key.md)). A changed source file is an exception to that rule ([D2](items/D2-refuse-changed-source.md)). Progress is one line on stderr ([D3](items/D3-progress-line.md)).

## Implemented and verified

None.

## Needs you

- [D2](items/D2-refuse-changed-source.md): what a rerun does when the source file changed. Recommended: refuse, and require `--restart`.

## Eligible work

- [T2](items/T2-resume-from-checkpoint.md): resume from the checkpoint. Built, acceptance passes; ready to review.
- [T1](items/T1-progress-line.md): progress line. Ready to build.

## Next

Review [T2](items/T2-resume-from-checkpoint.md): it carries the objective in focus.

## Working agreement

[P1](items/P1-working-agreement.md): focus recovery; detail brief. Reserved for you: user-visible behavior, and any choice that risks lost or duplicate rows.
