# Q4: Does --version win over a subcommand?

Status: open
Validity: current
Topics: cli, version

## Question

In `python3 -m textkit --version normalize "a  b"`, does the command print the version and stop, run `normalize`, or report a usage error?

## Who answers

user: command-line users see the result, and [P1](P1-working-agreement.md) reserves user-visible command-line behavior.

## History

- 2026-10-06: created as open.
