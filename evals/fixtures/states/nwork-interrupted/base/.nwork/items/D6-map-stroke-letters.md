# D6: Map Latin letters that do not decompose, before separating

Status: proposed
Validity: current
Topics: slugify
Depends on: [F3](F3-stroke-letters.md)
Serves: [O1](O1-slugify-function.md)

## Options

- Keep [D1](D1-non-ascii-separators.md) as it is: `Łódź` stays `odz`. No change to the code.
- Before separating, map a small built-in table of Latin letters that do not decompose: `ł`→`l`, `ø`→`o`, `đ`→`d`, `ħ`→`h`, `æ`→`ae`, `œ`→`oe`, and their capitals. `Łódź` becomes `lodz`. `ß` and non-Latin scripts stay as D1 says, so `Straße` is still `stra-e`. No dependency.

## Recommendation

Map the table. Latin-script names are the common case for this function, and seven letters cover the ones reported. It changes a decided contract (D1), and T1's tests need two new rows.

## Rationale

D1 was chosen for `ß` and non-Latin scripts, on the belief that every other accented Latin letter becomes plain ([F1](F1-accent-helper.md)). [F3](F3-stroke-letters.md) shows that belief was wrong for letters with strokes and for ligatures.

## Evidence

[F3](F3-stroke-letters.md).

## Decided by

pending: reserved for user ([P1](P1-working-agreement.md) § Authority: changing a decided contract)

## History

- 2026-10-07: created as proposed. Reserved for the user: it changes D1, a decided contract.
