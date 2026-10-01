# Brief: strip_accents

## Request

> Add a helper to textkit that removes accents from Latin text.

## Objectives

- O1: `textkit.strip_accents(text)` removes combining marks, so that `"Crème"` becomes `"Creme"`.

Approved: user

## Non-goals

- No transliteration of non-Latin scripts.

Approved: user

## Approach (provisional)

1. Add `strip_accents` to `textkit/core.py`, using `unicodedata`, with tests (serves: O1)

Approved: user

## Phases

- nlearn: skip — stdlib behavior is well known (suggested: skip; decided by: user)
- ndesign: skip — one pure function, contract in the task (suggested: skip; decided by: user)
- nplan: run — one slice (suggested: run; decided by: user)
- nbuild: run
- nreview: run — one verdict (suggested: run; decided by: user)

## Control

- nplan gate: gate waived
