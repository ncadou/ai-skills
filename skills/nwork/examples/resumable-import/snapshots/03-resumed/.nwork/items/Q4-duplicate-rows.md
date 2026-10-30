# Q4: Can a retried batch store rows twice?

Status: resolved
Validity: current
Topics: recovery

## Question

The store gives each new row its own ID, so writing a row again creates a second copy. Can a rerun write a batch again, and is a duplicate ever acceptable?

## Who answers

user: the answer sets what the import guarantees, and the working agreement reserves that choice.

## History

- 2026-03-02: created as open.
- 2026-03-02: resolved. Answered together with two other crash questions by one recovery policy that the user adopted.
