# Q3: What does slugify-lines print for a line with no slug?

Status: open
Validity: current
Topics: cli, batch, errors

## Question

`slugify` raises `ValueError("slug is empty")` for a line such as `!!!` or `Привет` ([D3](D3-empty-slug-error.md)). What does `slugify-lines` print for such a line, on stdout and on stderr?

## Who answers

user: command-line users see the output, and [P1](P1-working-agreement.md) reserves user-visible command-line behavior.

## History

- 2026-10-06: created as open.
