# P1: Working agreement

Status: active
Validity: current
Topics: working-agreement

## Scope

[O1](O1-resume-without-loss.md), [O2](O2-show-progress.md).

## Focus

- recovery: how an interrupted import resumes, and what it guarantees about lost or duplicate rows.

## Authority

Delegated to the agent:

- Internal naming, module layout, and test structure.
- Recovery mechanics (key layout, batch sizing, retry timing) that keep the guarantees of a policy the user adopted. This includes replacing such a policy with one that keeps the same guarantees.

Reserved for the user:

- Adopting a policy that sets new guarantees, or changing what an adopted policy guarantees.
- Any choice that risks losing or duplicating rows.
- User-visible behavior: CLI flags, messages, and exit codes.

## Detail

brief

## Established by

- 2026-03-02, user: "You handle the mechanics. Check with me on anything users will see, or anything that could lose or duplicate rows. I mostly care about recovery. Keep it short."

## History

- 2026-03-02: created as proposed. The agent proposed focus, authority, and detail together, with a recommendation.
- 2026-03-02: active. The user agreed, in the words quoted under Established by.
