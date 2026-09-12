---
name: nbuild
description: Build one ndev task slice with tests, from .ndev/tasks/.
argument-hint: "task file, e.g. task-01-slug"
disable-model-invocation: true
---

Build exactly one slice. Implement only the named task file; leave the next slice and the verdict to `nreview`.

## Steps

### 1. Load the slice

Read the named `.ndev/tasks/task-NN-<slug>.md` and the matching section of `.ndev/spec.md`. If the task is ambiguous, ask the user which file to build.

Done when one task file is loaded and its scope bounds the run.

### 2. Write tests with the slice

Add or update unit tests before or alongside the implementation. Cover the task's expected behavior plus its failure modes. Document non-obvious reasoning in docstrings and inline comments.

Done when the code matches the task scope and every non-obvious choice is documented at its site.

### 3. Verify and close the slice

Run the task file's stated acceptance command. Paste the actual result. On green, set `Status: done` in the task file and check it off in `.ndev/spec.md`.

Done when the acceptance command passes by observed output and the task file reads `Status: done`.

Task file format is defined by `nplan`; consume it as written.
