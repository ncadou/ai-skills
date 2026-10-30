# Q5: What does slugify-lines do when its reader stops early?

Status: open
Validity: current
Topics: cli, batch, errors

## Question

In `python3 -m textkit slugify-lines < titles.txt | head -1`, `head` exits after the first line, so the command's later writes to stdout fail. What does `slugify-lines` do then: what does it print on stderr, and which exit code does it end with?

## Who answers

user: command-line users see the result, and [P1](P1-working-agreement.md) reserves messages and exit codes.

## History

- 2026-10-06: created as open.
