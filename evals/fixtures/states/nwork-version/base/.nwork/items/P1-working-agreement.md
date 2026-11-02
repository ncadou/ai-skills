# P1: Working agreement

Status: active
Validity: current
Topics: working-agreement

## Scope

[O1](O1-slugify-function.md), [O2](O2-slugify-command.md), [O3](O3-version-flag.md).

## Focus

- errors: what callers and command-line users see when the input is bad.

## Authority

Delegated to the agent:

- Internal naming, module layout, and test structure.
- Implementation choices that keep the decided contracts.
- Review verdicts on slices.

Reserved for the user:

- User-visible command-line behavior: arguments, messages, and exit codes.
- Changing a decided contract.
- Accepting a slice.

## Detail

brief

## Established by

- 2026-10-05, user: "You handle the internals and the reviews. Anything a command-line user sees is my call, and I accept the work myself. I care most about the errors. Keep it short."
- 2026-10-06, user: "Add the version flag to the same agreement."

## History

- 2026-10-05: created as proposed. The agent proposed focus, authority, and detail together, with a recommendation.
- 2026-10-05: active. The user agreed, in the words quoted under Established by.
- 2026-10-06: scope extended to [O3](O3-version-flag.md), in the user's words quoted under Established by. Focus, authority, and detail did not change.
