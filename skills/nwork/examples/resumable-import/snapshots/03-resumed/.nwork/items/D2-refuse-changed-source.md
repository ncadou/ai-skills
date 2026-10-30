# D2: Refuse to resume when the source file changed

Status: proposed
Validity: current
Topics: recovery, cli
Depends on: [F2](F2-positional-rows.md)
Serves: [O1](O1-resume-without-loss.md)
Answers: [Q3](Q3-changed-source.md)

## Options

- Refuse. Record the file's SHA-256 at the first run. When it differs at a rerun, exit with code 3 and print `source changed since import <id> started; rerun with --restart to import from the beginning`. Nothing is lost or duplicated without the user knowing.
- Resume anyway. Batch numbers now point to different rows ([F2](F2-positional-rows.md)), so rows can be skipped or stored twice, silently.
- Restart automatically: delete the rows of the import and start again. No user action, but a large import starts over, and stored rows are deleted, without warning.

## Recommendation

Refuse. It is the only option that never loses or duplicates rows without telling the user.

## Rationale

The recovery policy holds only while batch numbers point to the same rows. A changed file breaks that, so it needs its own rule, not an extension of that policy.

## Evidence

[F2](F2-positional-rows.md): rows have no stable ID.

## Decided by

pending: reserved for user ([P1](P1-working-agreement.md) § Authority: user-visible behavior; any choice that risks losing or duplicating rows)

## History

- 2026-03-02: created as proposed, with a recommendation.
