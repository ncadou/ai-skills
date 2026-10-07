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

**Focus.** § Control can list focus topics, in the user's words (`- focus: naming — public names of modules, types, functions, CLI flags`). Focus applies from `nlearn` on:

- Each gated item carries `Concern: <topic> | other`. When in doubt, the item is in focus.
- An item in focus passes its gate as usual.
- An `other` item is delegated: the agent decides it and records `agent (delegated: outside focus)`.
- Each gate shows the in-focus items in full, then a digest of the delegated items since the last gate, one line each. The user can pull any item back into focus.
- A step with no item in focus does not stop. Its digest goes to the next gate, or to the end of the phase.
- `nbuild` and `nreview` only flag choices that fall under a focus topic and that the design does not state.

Other § Control lines and the user's own words override focus, in both directions (`agent decides`, `user decides`). With no focus topic, the gates work as described under Control.

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

`from` records who asked, `for` who must answer. Backtrack questions add `stale: <artifacts or none>` at the end. Each entry is one line in exactly this format, with no added notes: details belong in the artifact that answers it.

The phase where the question is answered ticks it and appends a pointer to the answer, keeping the rest of the line as written:

```markdown
- [x] Q3: <question> (from nstart/agent, for nlearn) → F4
```

The answer's `Source` or `Decided by` line records who answered. When the user declines a question `for user` ("no preference", "you decide"), tick it with a pointer to a new question, and append that question for the phase that will settle it:

```markdown
- [x] Q3: <question> (from nstart/agent, for user) → Q7
- [ ] Q7: <question> (from nstart/agent, for ndesign)
```

**Task status.** Lives only in the task file: `pending` → `done` (`nbuild`) → `pass` | `fail` (`nreview`) → `accepted` (optional, user or delegated agent). On `fail`, `nbuild` builds again and sets `done`; when the user asks `nreview` for the fixes in the same session, it hands off to `nbuild` explicitly, then reviews again. Builds and reviews append entries to the task file, so the history stays. The user can overrule a verdict, with a reason.

**Skipping phases.** Every phase is optional. Each skill uses whatever upstream artifacts exist and asks the user for what is missing. `nstart` suggests which phases to skip and the user decides; the brief records both. `nplan` without a design is limited to work that changes no contract.

**Backtracking.** When a phase finds a gap that belongs upstream (e.g. `nplan` finds a missing contract), it stops, records the gap in `questions.md` with the artifacts the rerun may make stale (`stale: plan.md, T03`), and names the phase to rerun. The user decides.
