# ndev

A bundle of six skills, declared as the `ndev` plugin in `.claude-plugin/marketplace.json` at the repo root. Each subfolder is one skill.

Phased workflow, human-gated. Each phase's artifact anchors the next, under `.ndev/`:

- `nstart/` — frame the cycle → `brief.md`
- `nlearn/` — discovery investigation → `discovery.md`
- `ndesign/` — boundaries, skeletons, decisions → `design.md`
- `nplan/` — break the design into slices → `plan.md` + `tasks/`
- `nbuild/` — one task slice with tests (takes a task file)
- `nreview/` — correctness + readability verdict on the slice

```text
nstart → nlearn ⇄ ndesign → nplan → nbuild → nreview
```

Each artifact has one writer. Two exceptions: `questions.md`, a shared ledger that any phase appends to, and task files, shared by section: `nplan` writes the task, `nbuild` its Evidence, `nreview` its Review, and the user owns its acceptance line. Status follows the lifecycle below.

**Learning first.** The agent and the user both learn before anyone designs or decides. `nlearn` validates assumptions with spikes and walks the user through its findings; the user can add facts of their own (`Source: user`) and rule on risks that no spike can check. `ndesign` sends every untested assumption back to `nlearn`.

**Control.** The user owns the design and decides how much to delegate. `brief.md` § Control is an optional seed; when it is empty, every gate applies and the agent makes no design choice. In any phase, at any time, the user can delegate one decision, a step, or a whole phase, or waive a gate. Each phase records the change where it applies: on a `Decided by` line, an `Approved:` line, or a task's Evidence entry.

**Traceability.** Items carry IDs that are never reused:

- `O1` objective, in `brief.md`
- `Q1` question, in `questions.md`
- `F1` finding, in `discovery.md`
- `D1` decision, in `design.md`
- `T01` task, in `tasks/task-01-<slug>.md`

Downstream items cite the IDs they rest on (`Serves: O1`, `Evidence: F3`, `Implements: D2`). A replaced item keeps its ID and is marked `Superseded by <ID>: <reason>`, never deleted. Every gated section records `Approved: user` or `Approved: agent (delegated: <scope>)`.

**Questions ledger.** Any phase appends to `questions.md`, with the next free number:

```markdown
- [ ] Q3: <question> (from <phase>/<user|agent>, for <phase|user>)
```

`from` records who asked, `for` who must answer. The phase where the question is answered ticks it and points to the answer: `- [x] Q3: … → F4`. The answer's `Source` or `Decided by` line records who answered.

**Task status.** Lives only in the task file: `pending` → `done` (`nbuild`) → `pass` | `fail` (`nreview`) → `accepted` (optional, user or delegated agent). On `fail`, `nbuild` builds again and sets `done`. Builds and reviews append entries to the task file, so the history stays. The user can overrule a verdict, with a reason.

**Skipping phases.** Every phase is optional. Each skill uses whatever upstream artifacts exist and asks the user for what is missing. `nstart` suggests which phases to skip and the user decides; the brief records both. `nplan` without a design is limited to work that changes no contract.

**Backtracking.** When a phase finds a gap that belongs upstream (e.g. `nplan` finds a missing contract), it stops, records the gap in `questions.md` with the artifacts the rerun may make stale (`stale: plan.md, T03`), and names the phase to rerun. The user decides.
