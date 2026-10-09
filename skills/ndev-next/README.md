# ndev-next

**Experimental.** A pilot of a successor to the [`ndev`](../ndev/README.md) workflow. It is not yet a replacement: `ndev` stays available, and a project uses one format at a time.

The pilot tests a workflow that:

- keeps a clear, current view of the project state;
- lets the user navigate by topic and level of detail;
- asks about governing principles before individual cases;
- delegates choices within an explicit working agreement;
- starts work that is understood well enough, before the whole project is resolved;
- resumes correctly from the files, in a fresh session.

It is one skill, `nwork`, which the user invokes explicitly. One agent moves among discovery, design, implementation, and review, and the conversation steers it after that.

## Layout

```text
ndev-next/
├── README.md
├── examples/
│   └── resumable-import/    # worked example: three snapshots of .ndev/
└── nwork/
    ├── SKILL.md             # the operating skill
    ├── references/
    │   └── records.md       # record format ndev-next/1
    └── scripts/
        └── check_records.py # record checker (Python 3, standard library)
```

Everything the skill needs at run time is inside `nwork/`. The example is documentation only.

## Using `nwork`

Invoke `nwork` with a request, or with nothing to continue. Then talk to it as usual.

| You want to | Say |
|---|---|
| Start | `/nwork` and what you want done. The agent proposes objectives, a working agreement, and the questions it already knows for you, in one message, and waits. |
| Continue | `/nwork`, or `/nwork` and the next thing to do. The agent takes the next action from `.ndev/now.md`. |
| Change focus or detail | "Today I'd rather look at progress", "more detail from now on". Only the presentation changes. |
| Delegate or reserve | "You decide the naming", "check with me on error messages". Recorded with your words in the working agreement. |
| Revise | Report a new fact, or change a decision. The agent marks what depends on it for revalidation. |
| Resume | `/nwork` in a fresh session. The agent reads the files, checks them against the code, and reports what changed since your last words. |
| See a topic | "Show me everything about recovery." Rendered in the conversation; nothing is stored. |

Each invocation runs one loop: orient from the files, reconcile them with the code, choose a bounded work packet, work, update the records and check them with the bundled script (`python3`; without it, the agent checks by hand and says so), and report. The agent stops when the packet is done, when a choice reserved for you blocks everything left, or at an effort limit you set.

With the Claude Code plugin, the skill is `/ndev-next:nwork`.

## Records

State lives under `.ndev/` in the project: `now.md`, a one-screen current-state view, and `items/`, one Markdown record per objective (`O`), question (`Q`), finding (`F`), decision (`D`), policy (`P`), or work slice (`T`). The records are the authority; `now.md` only summarises them and links to them. P1 is the working agreement: focus, authority, and detail. See [`nwork/references/records.md`](nwork/references/records.md).

A project that already has `ndev` artifacts under `.ndev/` is not migrated: `nwork` stops and lets you decide.

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
