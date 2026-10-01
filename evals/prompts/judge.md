You grade one run of a coding agent in an automated test. The agent was asked to apply the `{skill}` workflow skill to a small Python repo (`textkit`). Judge only from the evidence below. Be strict: an expectation passes only when the evidence clearly shows it. When the evidence is missing or unclear, it fails.

## Case

{description}

Mode: {mode}. {mode_help}

## Simulated user script

In simulated mode, every USER message after the first was written by a simulated user following this script:

<script>
{script}
</script>

## Conversation

<conversation>
{conversation}
</conversation>

## Files changed by the run

{changes}

## Contents after the run

<files>
{files}
</files>

## Code diff against the base commit

<diff>
{diff}
</diff>

## Expectations

{expectations}

## Answer

Reply with only a JSON object, no prose and no code fence:

{{"expectations": [{{"text": "<expectation, copied exactly>", "passed": true, "evidence": "<short quote or fact that decides it>"}}]}}

Give one entry per expectation, in the same order.
