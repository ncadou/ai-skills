---
name: nplan
description: Architecture blueprint from .ndev/discovery.md, producing .ndev/spec.md and .ndev/tasks/.
disable-model-invocation: true
---

Draw the blueprint. Produce only `.ndev/spec.md` and `.ndev/tasks/`; leave discovery to `nlearn` and code to `nbuild`.

## Steps

### 1. Load discovery

Read `.ndev/discovery.md`. If it is missing, stop and ask the user to run `nlearn` first.

Done when discovery is loaded, or the run has stopped with that prompt.

### 2. Define the blueprint

Define component boundaries, schemas, and skeleton signatures (types, function signatures, interfaces) without full logic.

Done when every new boundary and contract in scope has a skeleton in `.ndev/spec.md`.

### 3. Slice into tasks

Decompose the blueprint into numbered, independent, testable slices. Write one file per slice at `.ndev/tasks/task-NN-<slug>.md` using the task template below, and index them from `.ndev/spec.md`.

Done when every slice has its own task file with files to touch, a runnable acceptance command, and expected behavior, with nothing shared unwritten between files.

## Spec template

```markdown
# Spec: <topic>

## Architecture

Boundaries and how the slices compose.

## Interfaces & Skeletons

Types, signatures, schemas. No logic.

## Tasks

- [ ] `tasks/task-01-<slug>.md`
- [ ] `tasks/task-02-<slug>.md`
```

## Task template

```markdown
# Task NN: <title>

Status: pending

## Scope

Files to create or edit.

## Acceptance

Test command: `<exact command, e.g. pytest tests/test_feature.py -k test_happy_path>`

Expected behavior:
```

The task template is canonical here; `nbuild` consumes these files as written.
