# Q4: Does a line with no slug stop slugify-lines?

Status: open
Validity: current
Topics: cli, batch, errors

## Question

When one line has no slug, does `slugify-lines` stop there, or go on with the next lines? And what exit code does it end with?

## Who answers

user: scripts depend on the exit code, and [P1](P1-working-agreement.md) reserves exit codes.

## History

- 2026-10-06: created as open.
