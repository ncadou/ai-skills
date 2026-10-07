---
name: nbuild
description: Build one ndev task slice with tests, from .ndev/tasks/.
argument-hint: "task file, e.g. task-01-slug"
disable-model-invocation: true
---

Build exactly one slice. Implement only the named task file; leave the next slice and the verdict to `nreview`.

Implementation choices below the design contracts are yours, unless `.ndev/brief.md` § Control or the user reserves them; then ask before you choose. Only the user changes this, at any time and in their own words; record each change in the build's Evidence entry.

When § Control lists focus topics, flag each choice you make that falls under a focus topic and that the design does not state: for example a new public name, or the wording of an error message. Make the choice, record it in the Evidence entry's `Choices` with `Concern: <topic>`, and list it in your report. A flag does not stop the build; a choice reserved for the user still goes to the user first.

## Inputs

- The named `.ndev/tasks/task-NN-<slug>.md`. If the name is ambiguous, ask the user which file to build. If no task file exists, ask the user for the scope and an acceptance command, and confirm they want to build without a plan.
- The `.ndev/design.md` sections and decisions the task names under `Implements:`. When the design was skipped, the task file is the whole contract.
- When the task's status is `fail`: its latest Review entry. The revisions tagged `nbuild` are in scope for this run.
- `.ndev/brief.md` § Control, when it exists.

## Steps

### 1. Load the slice

Read the task file and the design sections it implements.

Done when one task file is loaded and its scope bounds the run.

### 2. Write tests with the slice

Add or update unit tests before or alongside the implementation. Cover the task's expected behavior plus its failure modes. Implement the contracts exactly as the design states them. Document non-obvious reasoning in docstrings and inline comments.

Done when the code matches the task scope and its contracts, and every non-obvious choice is documented at its site.

### 3. Verify and close the slice

Run the task file's stated acceptance command. Append an entry to the task file's Evidence section with the actual result of the run that closes the slice, or of the last run before a Backtrack, using the format below. On green, set `Status: done` in the task file.

Done when the acceptance command passes by observed output, the Evidence entry is written, and the task file reads `Status: done`.

## Backtrack

When a trigger below fires, stop. Append each gap to `.ndev/questions.md` as `- [ ] Q<n>: <gap> (from nbuild/<user|agent>, for <phase>) stale: <artifacts or none>`, listing the downstream artifacts that rerun may make stale. Each ledger entry is one line in exactly the format shown, with no added notes; details go in the artifact that answers it. Name the phase for the user to run. Leave the contract unchanged; the user decides.

- A contract is wrong or cannot be implemented as written: `ndesign`.
- The task's scope, dependencies, or acceptance command are wrong or unrunnable: `nplan`.
- A dependency behaves differently from what discovery recorded: `nlearn`.

## Evidence entry format

```markdown
### Build <n>

- Command: `<acceptance command>`
- Run by: agent | user
- Result: pass | fail
- Output: <excerpt of the actual output>
- Choices: <notable implementation choices, each with who made it, and `Concern: <topic>` when it falls under a focus topic> (when any)
```

Task file format is defined by `nplan`; consume it as written.
