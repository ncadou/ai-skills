# Evals for the ndev skills

Behavior evals for the six `ndev` skills. Each case puts a skill in a known repo state, runs it headless through `opencode run`, and grades the result with script checks plus an LLM judge.

There are no trigger evals: every `ndev` skill sets `disable-model-invocation: true`, so the description never decides whether a skill loads.

## Quick start

```sh
python3 evals/run.py list                          # 32 cases
python3 evals/run.py run --skill nbuild --runs 1   # one skill, one run per case
python3 evals/run.py run --tag messy               # only the messy-user cases
python3 evals/run.py run                           # everything, 3 runs per case
```

Results go to `evals-workspace/iteration-<n>/` (gitignored). Read `benchmark.md` first, then the run folders it points to.

Requirements: Python 3.10+ (stdlib only), `opencode` on `PATH`, and working credentials for the models (see [Models](#models)).

## Compare two versions of the skills

Every change to a skill should beat a baseline, not only pass:

```sh
python3 evals/run.py run --baseline HEAD           # working tree vs last commit
python3 evals/run.py run --baseline no-skill       # working tree vs no skill at all
```

`benchmark.md` then shows both configurations side by side, the Δ, and notes on checks that did not tell the two apart.

## Compare agent models

A skill that works on a strong model can still be too implicit for a weaker one. Run every configuration with a second agent model:

```sh
python3 evals/run.py run --also-model opencode/glm-5.3-flash
python3 evals/run.py run --also-model opencode/glm-5.3-flash --baseline no-skill
```

Labels then read `<skills>@<model>`, for example `with_skill@glm-5.3-flash`. The report compares like with like: the skill against each baseline on the same model, and the primary model (`--model`) against each other model, both with the skill. A check that passes on the primary model but fails on the weaker one usually points to an instruction that needs to be stated outright.

## How a run works

1. **Fixture.** The toy repo `fixtures/repo/` (`textkit`, a small Python package) is copied to `/tmp/ndev-work/run-<random>/work`. Then the case's state is overlaid on it, and it gets its own git repo. The agent sees this path, so it names no case and no mode: a path such as `nstart-simulated-…` once led an agent to treat the run as a test and record delegations nobody gave.
2. **Isolation.** opencode gets a fresh `HOME` holding only the skills under test. Globally installed skills, `AGENTS.md`, plugins, and MCP servers stay out. The config copies your `provider` block and links `auth.json`, so your models still work.
3. **Agent.** `opencode run --format json` gets the case prompt. In `simulated` mode, a second model plays the user and answers from the case's `user_script` until it replies `<<DONE>>` or `max_turns` is reached. Its prompt (`prompts/simulated_user.md`) names the phase under test and forbids asking for another phase.
4. **Grading.** Script checks run on the before and after trees. Then the judge grades the case's `judge` expectations from the transcript, the artifacts, and the diff. In simulated mode, **fidelity** asks whether the simulated user kept to its script. Two results answer it: the judge's verdict, and a script-level guard that fails when a user message after the first names another phase skill and the agent loads that skill in the same turn. When either fails, the run is a broken test, not a skill failure. It is left out of the pass rates and listed in the notes as `off script (excluded)`.

Permissions are all `allow`, except that file tools cannot leave the work tree (`external_directory: deny`). Bash is **not** sandboxed: the agent runs commands as you. The prompts only ever point it at the fixture.

## Layout

```text
evals/
├── run.py                   # CLI: list, run, grade, report
├── harness/                 # fixtures, agent, runner, checks, judge, report
├── prompts/                 # simulated user and judge prompts
├── fixtures/
│   ├── repo/                # the toy textkit repo
│   ├── states/<name>/       # layered .ndev/ states (see below)
│   └── hidden/              # checks the agent never sees (slugify contract)
├── ndev/<skill>/evals.json  # the cases
└── tests/                   # unit tests for checks and fixtures
```

## Cases

Each skill has cases in three modes. The mix matters: gate cases test the core `ndev` promise (the user decides), delegated cases test artifact content, and simulated cases test full conversations.

| Mode | Turns | What passes |
| --- | --- | --- |
| `gate` | 1 | The skill stops at its first gate, asks, and writes no approval. |
| `delegated` | 1 | The prompt or `brief.md` § Control delegates the gates, or the skill has none. Approvals say `agent (delegated: …)`. |
| `simulated` | 2+ | A simulated user answers from a script. Approvals match what the user said. |

Backtrack cases seed a flaw upstream (a design gap, conflicting objectives, an unrunnable acceptance command) and check that the skill stops and logs a question for the right phase.

### Messy-user cases

Real users go off the happy path. Cases tagged `messy` script one specific deviation each, so it is the same in every run and between skill versions:

| Case | The user | The skill must |
| --- | --- | --- |
| `nstart-partial-delegation` | delegates one step (non-goals) | record that delegation on that section only |
| `nlearn-midrun-delegation` | delegates the rest of the phase mid-run | attribute later rulings to the agent, earlier answers to the user |
| `nlearn-defer-question` | declines a question asked of them | tick it `→ Q<new>` and re-open it for the phase that will settle it |
| `ndesign-change-of-mind` | reverses an approved decision | keep it, mark it Superseded, and gate the new one |
| `nplan-reject-then-approve` | rejects the first plan | revise, and record approval only for the revision |
| `nbuild-scope-creep` | asks for the next slice too | build exactly one slice |
| `nreview-overrule` | accepts after a Fail | record `Overruled by user: <reason>` |
| `nreview-chain-request` | asks the reviewer to fix the code | hand off explicitly: load `nbuild`, then review again |

The messiness is in the script, never left to the simulated user model. A weak simulated user makes runs noisy at random; the fidelity check catches that.

### Fixture states

States chain with `extends`, following the ndev lifecycle, so each skill starts right where it enters:

```text
empty
stale-cycle                       leftovers from an earlier, finished cycle
briefed                           nstart done (O1 slugify, O2 CLI)
└── discovered                    nlearn done (F1–F8)
    ├── discovered-q4             + open Q4 for nlearn
    ├── discovered-delegated      + § Control delegates ndesign
    ├── discovered-conflict       + O3 contradicts O1
    ├── designed-gap              design with 2 gaps
    └── designed                  ndesign done (D1–D3, skeletons)
        └── planned               nplan done (T01, T02)
            ├── planned-badcmd    T01 acceptance command cannot run
            └── built             T01 done, correct code (uncommitted)
                ├── passed        T01 pass
                └── built-buggy   T01 done, buggy code, tautological test
                    └── failed    T01 fail, three nbuild revisions
```

A state folder holds `state.json` (`extends`, `description`) and two optional overlays. `base/` is committed as the base commit. `work/` stays uncommitted, so `git diff` shows it; `nreview` reviews that diff.

## Checks

Every case gets these default checks:

- `skill_loaded`: the `skill` tool loaded the case's skill (skipped for `no_skill`).
- `only_touched`: every changed file is one the skill may write (from its "Produce only …" line, plus the case's `allow`).
- `approvals`: new `Approved:`, `Decided by:`, and `Accepted by:` lines are truthful for the mode.
- `questions_format`: every `questions.md` line parses; ticked ones point to an answer.
- `ids_unique`, `ids_preserved`: no ID is defined twice, and none disappears.

Cases add their own checks: `field`, `contains`, `not_contains`, `file_exists`, `file_absent`, `unchanged`, `template_headings` (headings from the SKILL.md template itself), `approvals_min`, `question_added`, `questions_ticked`, `final_asks`, `no_tool_call` (no tool call whose input matches a pattern), `not_written_in_turn` (no file tool wrote a path in a given turn, for example the brief before the user's first reply), and `command_passes` (runs a command on a copy of the final tree, for example the hidden slugify contract check). See `harness/checks.py`.

Prefer a script check when the answer is objective. Use a `judge` expectation for meaning: is the review finding real, does the finding quote real spike output.

## Models

| Role | Default | Flag |
| --- | --- | --- |
| Agent under test | `opencode/claude-opus-5-5` | `--model` |
| Simulated user | `opencode/glm-5.3-flash` | `--user-model` |
| Judge | `opencode/glm-5.3-flash` | `--judge-model`, or `--no-judge` |

A cheap judge is fast but can be wrong. Re-grading the same 62 runs flipped 2% of judge verdicts, all on borderline expectations; script checks never flip. When a judge verdict decides whether an edit ships, re-grade with a stronger model: `python3 evals/run.py grade <iteration> --judge-model <model>`.

The defaults come from the environment: `EVALS_MODEL` overrides the agent model, `EVALS_CHEAP_MODEL` the simulated user and judge. Without them, the table above applies.

## Reading results

- `benchmark.md`: pass rate mean ± stddev per case, skill, and config, plus analyst notes:
  - **flaky**: passes in some runs only. Add runs, or tighten the case.
  - **always fails with skill**: a skill gap, a fixture flaw, or a wrong check. Read the run before you blame the skill.
  - **non-discriminating**: passes with and without the skill, so it measures nothing about the skill.
- `<case>/<config>/run-<n>/`:
  - `conversation.md`: messages, tool calls, and command output;
  - `grading.json`: each check with its evidence;
  - `before/`, `after/`, `final.diff`, `metrics.json`.

Read transcripts, not only scores. Wasted steps and misread rules show up there first.

## Iterating

- `run` skips runs that already have `metrics.json`, so a rerun with the same `--name` resumes.
- After a network or provider outage, `run ... --name <same> --retry-failed` redoes runs that ended in `error`, `timeout`, or `user_error`, and `grade <iteration> --failed-only` re-grades runs whose judge call failed. The simulated user and the judge retry with backoff first. A failed call never counts as a result: it never passes for `<<DONE>>`, and never as a failed expectation. Such runs are left out of the pass rates and listed in the notes.
- After editing checks or judge expectations, re-grade without rerunning the agent: `python3 evals/run.py grade evals-workspace/iteration-<n>`.
- To add a case, add it to `ndev/<skill>/evals.json`. If it needs a new state, add `fixtures/states/<name>/`. Then run the unit tests, which check every state against the same format checks and SKILL.md templates:

  ```sh
  cd evals && python3 -m unittest discover -s tests -t . -v
  ```

## Cost

One full pass is 32 cases × 3 runs = 96 agent runs per configuration, plus simulated-user and judge calls; each `--baseline` or `--also-model` multiplies that. In smoke tests an agent run used 20k–470k tokens and took 30 s–5 min; simulated cases cost the most. Use `--skill`, `--case`, and `--runs 1` while iterating, and `--jobs` to run in parallel (default 4).
