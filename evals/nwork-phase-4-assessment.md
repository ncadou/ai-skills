# nwork: Phase 4 assessment

Behavioral evaluation of the experimental `nwork` skill (now `skills/nwork/`), Phase 4 of `ndev-next-pilot-plan.md`. Date: 2026-10-13. Paths and names are updated to the current layout: records under `.nwork/`, format `nwork/1`.

## Setup

- Agent: `ssnc-prod/zai-org/GLM-5.3-Flash` (the cheaper model). Simulated user: the same model. Judge: `ssnc-prod-claude/us.anthropic.claude-opus-5-5`. No `opencode/` model was used; each `iteration.json` confirms it.
- Six cases in `nwork/evals.json`, one per behavior. See [README § nwork](README.md#nwork) for the cases and states.
- Baseline: `no_skill` has the same prompt and fixture, but no skill installed. It still sees the existing `.nwork/` records and copies their format, so it scores well on format checks. Compare the behavior, not only the totals.
- Transcripts and grades are in `evals-workspace/` (gitignored). Each link below goes to a `conversation.md`. `grading.json` in the same folder gives the evidence for each check.

| Iteration | What ran | Skill version |
|---|---|---|
| `nwork-1` | Stopped early | Invalid: the skill could not read `references/records.md` (see [Fixes](#fixes)) |
| `nwork-2` | 6 cases × skill and baseline, 1 run | After the harness fix; before the skill fixes |
| `nwork-3` | 6 cases × skill and baseline, 2 runs | Fixes 1 and 2. Runs that were retried after rate limits (HTTP 429) also had fix 3 |
| `nwork-4` | 4 cases, skill only, 2 runs | Fixes 1 to 3, and a first wording of fix 4; `working-tree.diff` in the folder |
| `nwork-5` | 2 cases, skill only, 2 runs | All fixes (the final skill); `skills.diff` in the folder |

## Results

The final results come from the latest iteration that ran each case. The baseline results come from `nwork-3`.

| Behavior | Case | Skill | Baseline | Observed |
|---|---|---|---|---|
| Principle compression | `nwork-principles` | 0.93 (18/21, 21/21) | 0.38 | Q2 to Q4 got one proposed policy with its effect shown on example input, and the reader-stops-early case was kept apart. One run also moved blank lines (Q2) out of the rule, as an exception. The baseline asked four questions and listed every option. |
| Contradiction | `nwork-contradiction` | 0.96 (21/23, 23/23) | 0.61 | The agent checked the claim with its own spike. D1, T1, and T2 became `needs-revalidation` and kept their statuses. T3 stayed eligible. D1 went to the user. The baseline left D1, T1, and T2 `current`. |
| Local readiness | `nwork-local-readiness` | 1.00 (19/19 ×2) | 0.78 | T1 was built, verified, and reviewed. D4 and T2 were not touched. The hidden contract check passed. The baseline invented statuses (`built`, `ready`). |
| Cold resume | `nwork-cold-resume` | 1.00 (16/16 ×2) | 0.60 | The agent found that `now.md` was stale and rebuilt it from the records. It reported what changed since the user's last words, what needs the user, and one next action. The baseline believed `now.md` and reported T1 as verified. |
| Authority vs. focus | `nwork-focus-shift` | 1.00 (18/18 ×2) | 0.82 | Focus and detail changed, but Authority did not. The agent asked whether "I don't care about the errors" also delegates D4. The baseline did not ask. |
| Brief quality | `nwork-brief-quality` | 0.94 (15/17, 17/17) | 0.81 | The agent ran the acceptance command again, so the fail rests on today's output, not on the recorded pass. The reports were 50 to 70 words. One run left T1's status at `implemented`, and its report did not mention the stale build. The baseline did not record the fail and did not mention D4. |

Representative transcripts:

- Principles: [skill, clean](../evals-workspace/nwork-4/nwork-principles/with_skill/run-2/conversation.md), [skill, Q2 split off](../evals-workspace/nwork-4/nwork-principles/with_skill/run-1/conversation.md), [baseline](../evals-workspace/nwork-3/nwork-principles/no_skill/run-1/conversation.md).
- Contradiction: [skill, before fix 1](../evals-workspace/nwork-2/nwork-contradiction/with_skill/run-1/conversation.md) (the agent revalidated the user's D1 itself), [skill, final](../evals-workspace/nwork-5/nwork-contradiction/with_skill/run-2/conversation.md), [baseline](../evals-workspace/nwork-3/nwork-contradiction/no_skill/run-2/conversation.md).
- Readiness: [skill](../evals-workspace/nwork-3/nwork-local-readiness/with_skill/run-1/conversation.md), [baseline](../evals-workspace/nwork-3/nwork-local-readiness/no_skill/run-1/conversation.md).
- Resume: [skill](../evals-workspace/nwork-5/nwork-cold-resume/with_skill/run-1/conversation.md), [baseline](../evals-workspace/nwork-3/nwork-cold-resume/no_skill/run-2/conversation.md).
- Focus: [skill](../evals-workspace/nwork-3/nwork-focus-shift/with_skill/run-1/conversation.md), [baseline](../evals-workspace/nwork-3/nwork-focus-shift/no_skill/run-2/conversation.md).
- Brief: [skill, clean](../evals-workspace/nwork-4/nwork-brief-quality/with_skill/run-2/conversation.md), [skill, status slip](../evals-workspace/nwork-4/nwork-brief-quality/with_skill/run-1/conversation.md), [baseline](../evals-workspace/nwork-3/nwork-brief-quality/no_skill/run-1/conversation.md).

## Fixes

Each failure below was traced to its cause before the fix.

| # | Failure | Cause | Fix |
|---|---|---|---|
| H | The skill never read `records.md` (`nwork-1`) | Harness: `external_directory: deny` also blocked the installed skill folder | `harness/agent.py` allows the skills folder only, and a unit test covers it. Phase 3 had installed the references, but no test showed that the agent could read them. |
| C | No contradiction in the contradiction case (`nwork-1`, agent: "nothing contradicts the records") | Case: F1's claim was compatible with the report | F1 now claims every Latin letter with a diacritic becomes plain |
| 1 | The agent revalidated D1, a user decision, and kept T1 "verified" (`nwork-2`) | Skill: it did not say who may revalidate | Revalidating is a choice under P1. A user's or reserved choice waits for the user, and so do its dependants (SKILL.md § Revision, records.md § Revision step 5). After the fix, 6 of 6 runs passed this. |
| 1 | A "just the verdict" report dropped D4 (`nwork-2`) | Skill: the list of parts that every report keeps did not say that it holds against a user request for less | It holds "even when the user asks for less". After the fix, 3 of 4 runs kept D4. |
| 2 | The principles case was weak: duplicates fit a "stateless" rule. The script let the user accept slices | Case | Q5 is now "the reader stops early". The prompt says that nothing gets built, and the script defers everything else |
| 2 | Expectations were too strict: a quote of the test output, and `final_asks` | Case | The expectations were relaxed to "the observed result", and `final_asks` was removed. The judge grades that question. |
| 3 | One approval covered both the principle and its exception (`nwork-3`, 2 of 2 runs) | Skill: "end with one question" conflicted with "keep an exception apart" | Ask about each exception separately. An answer about the principle does not settle it. |
| 3 | `now.md` linked the superseded F1 in a sentence (`nwork-3`, 2 of 2 runs) | Spec: "Never list" was ambiguous | Changed to "Never link a superseded item, not even in a sentence". |
| 3 | Policies had `Options` and `Evidence` sections (`nwork-3`, 2 of 2 runs) | Spec conflict: SKILL.md says to keep a principle's options and evidence in the records, but records.md gave policies no such sections | records.md now allows optional `Options` and `Evidence` sections in a policy, and the harness agrees. **This changes the record format (an amendment): see the plan.** |
| 4 | The next action listed several actions (cold resume, `nwork-3` and `nwork-4`, 4 of 4 runs). After a first wording (`nwork-4`), the contradiction reports left out T3 (2 of 2 runs) | Skill: it did not say what goes in the next action and what goes elsewhere | The next action is one step. Other choices and ready work go in their own parts, and a revision report names the work that stays eligible. In `nwork-5`, 2 of 2 resume runs gave one next action, and 2 of 2 contradiction reports named T3. |

## Measures

| Measure | Skill | Baseline |
|---|---|---|
| User turns, simulated case | 2 to 3 | 2 to 3 |
| Choices put to the user, principles case | 1 governing rule, plus 1 or 2 exceptions | 4 questions, 11 options |
| Final report: words (lines) | Brief case 52 to 70 (2). Status reports 176 to 386 (5 to 18) | 35 to 435 |
| Verification as observed | Every built or reviewed slice cites a command it ran in the session. One brief report did not mention the stale build | The baseline reran the tests, but did not record the fail |
| Resume accuracy | 6 of 6 runs (`nwork-3` to `nwork-5`) rebuilt the stale `now.md`, named D6 and D4, and named the revalidation | 0 of 2 runs repaired the stale `now.md` |
| Record churn per run: records new/changed, `.nwork` lines | Contradiction 1–3 new and 5–8 changed, 57–109 lines. Principles 2–4 new, 118–165 lines. Others 1–2 changed, 10–19 lines | Contradiction 30–39 lines |
| Tokens (mean), duration (mean), `nwork-3` | 495k, 363 s | 267k, 308 s |
| Cost | Not reported: the provider returns $0 | Same |

Churn is real but bounded. Most of it is one History line on each dependant, and those lines repeat the trigger in each record. The principles case costs the most: 0.8 to 1.2 million tokens, and 8 to 14 minutes on the cheaper model.

## Remaining variability

These failures come from the model, not from unclear instructions. The rule for each one is explicit, and other runs follow it.

- Record state slips, about 1 run in 4: `Status` left at `implemented` beside a `fail` verdict; a `now.md` section dropped (`Working agreement` or `Implemented and verified`); `Under revalidation` incomplete; `Adopted by` written in a decision; a required section missing. The default checks catch each one.
- Judgment varies within the rules. One principles run made blank lines an exception. One contradiction report narrowed T1's lost assurance to "stroke-letter input".
- The cold-resume and focus results each rest on 2 runs. More runs would make them firmer.
- `nwork-local-readiness` and `nwork-focus-shift` last ran in `nwork-3`, before fix 4. Fix 4 changes only how a report presents the next action.

No core authority failure remains in the final runs: no unattributed user decision, no delegation that the user did not give, and no reserved choice settled by the agent.

## Proposed follow-ups

- Bundle the `nwork/1` record checks as a script in `nwork/` (from `harness/records.py`), and have Maintain state run it. Most of the remaining slips are mechanical, so a script would catch them. It adds a runtime dependency on Python.
- The skill tool loads all of SKILL.md (now 176 lines). Every section that a case exercises shows up in some transcript, and most fixes went to `Revision` and `Reporting`. No case covers `Start`, from an empty `.nwork/`; Phase 5 covers it.
- `attributions` matched every quote in these runs: no agent paraphrased the user.

## Addendum: Phase 4b, the narrower revalidation rule

Date: 2026-10-14. Same models as above; `iteration.json` of `nwork-6` confirms them.

Fix 1 made every decision or policy of the user wait for the user after a challenge, even when its wording still fit. Phase 4b narrows it (SKILL.md § Revision, records.md § Revision step 5): the agent may revalidate such an item when the new evidence leaves its stated rationale, and its consequences as the user saw them, unchanged. Otherwise it waits for the user. The test: "If you would need to ask whether the user still accepts it, it is not revalidated."

New case `nwork-revalidate-unaffected`, on the new state `nwork-revalidating`: an earlier session marked D1, D3, D4, T1, and T2 for revalidation because of F3 (Greek, Japanese, and Arabic titles raise `slug is empty`), and stopped. D1's rationale already says that non-Latin letters become separators, and D3's choice already names `Привет`, so nothing the user accepted changes.

| Case | Runs (`nwork-6`) | Observed |
|---|---|---|
| `nwork-contradiction` | 23/23, 23/23 | Unchanged by the narrower rule: D1's premise is refuted, and D1 went to the user in both runs (one run as a proposed replacement, D6). The agent did not take "the wording still fits" as "nothing changed". |
| `nwork-revalidate-unaffected` | 26/27, 26/27 | In both runs, the agent revalidated D1 and D3 itself, kept their `Decided by`, wrote a History line that gives the reason, restored D4, T1, and T2, and reran T1's acceptance. It did not put D1 or D3 to the user. |

Transcripts: [revalidate, run 1](../evals-workspace/nwork-6/nwork-revalidate-unaffected/with_skill/run-1/conversation.md), [revalidate, run 2](../evals-workspace/nwork-6/nwork-revalidate-unaffected/with_skill/run-2/conversation.md), [contradiction, run 1](../evals-workspace/nwork-6/nwork-contradiction/with_skill/run-1/conversation.md), [contradiction, run 2](../evals-workspace/nwork-6/nwork-contradiction/with_skill/run-2/conversation.md).

The two failures are slips by the model against explicit rules, not effects of the new rule:

- Run 1 kept `Under revalidation` in `now.md`, with "Nothing needs revalidation". records.md says to omit the section. `now_view` caught it.
- Run 2 claimed that "`git log` shows no code change since the 2026-10-06 build". The work tree has one commit, and T1's code is uncommitted, so `git log` cannot show this. The run did rerun T1's acceptance, which is the real basis. The judge caught it. The same report also gave two next actions.

Run 1 also called its own judgment an assumption, and offered the user a way to override it. That is a report, not a question.

Tokens and duration: `nwork-revalidate-unaffected` 292k and 516k tokens, 251 s and 289 s; `nwork-contradiction` 844k and 1,224k tokens, 546 s and 516 s.
