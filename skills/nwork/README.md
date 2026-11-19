# nwork

A development workflow in one skill, `nwork`. It is an alternative to the phased [`ndev`](../ndev/README.md) bundle, and keeps its state apart, under `.nwork/`. It:

- keeps a clear, current view of the project state;
- lets the user navigate by topic and level of detail;
- asks about governing principles before individual cases;
- delegates choices within an explicit working agreement;
- starts work that is understood well enough, before the whole project is resolved;
- polishes reviewed work in rounds, with fresh eyes, until it meets a bar that the project sets;
- resumes correctly from the files, in a fresh session.

The user invokes `nwork` explicitly. One agent moves among discovery, design, implementation, review, and polish, and the conversation steers it after that.

## Layout

```text
nwork/
├── README.md
├── SKILL.md                 # the operating skill
├── references/
│   └── records.md           # record format nwork/1
├── scripts/
│   └── check_records.py     # record checker (Python 3, standard library)
└── examples/
    └── resumable-import/    # worked example: three snapshots of .nwork/
```

The skill needs `SKILL.md`, `references/`, and `scripts/` at run time. The example is documentation only.

## Using `nwork`

Invoke `nwork` with a request, or with nothing to continue. Then talk to it as usual.

| You want to | Say |
|---|---|
| Start | `/nwork` and what you want done. The agent proposes objectives, a working agreement, and the questions it already knows for you, in one message, and waits. |
| Continue | `/nwork`, or `/nwork` and the next thing to do. The agent takes the next action from `.nwork/now.md`. |
| Change focus or detail | "Today I'd rather look at progress", "more detail from now on". Only the presentation changes. |
| Delegate or reserve | "You decide the naming", "check with me on error messages". Recorded with your words in the working agreement. |
| Revise | Report a new fact, or change a decision. The agent marks what depends on it for revalidation. |
| Polish | Nothing: polish starts when every slice of an objective passes review. Or "polish O1", "polish each slice from now on", "raise the bar: only nits may remain", "also check the error messages". |
| Resume | `/nwork` in a fresh session. The agent reads the files, checks them against the code, and reports what changed since your last words. |
| See a topic | "Show me everything about recovery." Rendered in the conversation; nothing is stored. |

Each invocation runs one loop: orient from the files, reconcile them with the code, choose a bounded work packet, work, update the records and check them with the bundled script (`python3`; without it, the agent checks by hand and says so), and report. The agent stops when the packet is done, when a choice reserved for you blocks everything left, or at an effort limit you set.

With the Claude Code plugin, the skill is `/nwork:nwork`.

## Records

State lives under `.nwork/` in the project: `now.md`, a one-screen current-state view, and `items/`, one Markdown record per objective (`O`), question (`Q`), finding (`F`), decision (`D`), policy (`P`), or work slice (`T`). The records are the authority; `now.md` only summarises them and links to them. P1 is the working agreement: focus, authority, detail, and polish. See [`references/records.md`](references/records.md).

`nwork` reads only `.nwork/`, so a project can also hold `ndev` artifacts under `.ndev/`. If `.nwork/` holds something other than `nwork/1` records, `nwork` stops and lets you decide.

## Polish

Review checks one slice against its record. Polish then looks at the whole objective, by default, in rounds. In each round, sub-agents with a fresh context look for regressions and audit the tests (low-value, missing, unable to fail, misnamed, flaky, or passing on logic that makes no sense). The agent checks each finding, fixes what its authority allows, and asks you about the rest. It stops at the bar, at a round limit, or when the rounds stop making progress. Acceptance waits for it.

The defaults: unit `objective`, bar `major` (only minor findings and nits may remain), lenses `regressions` and `tests`, limit 3 rounds. To change them for a project, add a section to its `AGENTS.md`; the agent copies it into P1 at Start, and your words can change it later:

```markdown
## nwork polish

- Unit: slice
- Bar: minor
- Lenses: regressions, tests, error messages follow docs/errors.md
- Limit: 5 rounds
```

## Example

[`examples/resumable-import/`](examples/resumable-import/README.md) follows a fictional project through three snapshots: several questions reduced to a policy, an exception kept apart, a finding that forces revalidation, and a return in a fresh session.

## Status

| Phase | Deliverable | State |
|---|---|---|
| 1 | Worked example and record specification | done |
| 2 | The `nwork` skill | done |
| 3 | Eval harness support | done |
| 4 | Behavioral evaluation | done: [assessment](../../evals/nwork-phase-4-assessment.md) |
| 4b | Narrower revalidation rule | done: [addendum](../../evals/nwork-phase-4-assessment.md#addendum-phase-4b-the-narrower-revalidation-rule) |
| 5 | One real pilot | done: see the pilot plan, Phase 5 outcome |
