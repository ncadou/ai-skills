---
name: nlearn
description: Discovery investigation producing .ndev/discovery.md with validated assumptions and spikes.
disable-model-invocation: true
---

Run a discovery investigation. Produce only `.ndev/discovery.md`; leave the blueprint to `nplan` and code to `nbuild`.

## Steps

### 1. Fix the scope

Confirm the brief with the user: objectives and explicit non-goals.

Done when objectives and non-goals are written down and the user agrees.

### 2. Map reference patterns

Search the codebase and relevant libraries for existing conventions the work must follow. Cite every claim with a file path.

Done when every touched area names its reference files, or states that none exist.

### 3. Validate assumptions with spikes

List hidden dependencies, data contracts, and failure points. For each ambiguous behavior, run a minimal spike under `/tmp` or `.ndev/scratch/` and log actual output, never assumed output.

Done when every assumption has a validation note and its observed outcome.

### 4. Write `.ndev/discovery.md`

Write the artifact using the template below. Report risks to the user; the human runs `nplan` next.

Done when `.ndev/discovery.md` exists and every section is filled.

## Discovery template

```markdown
# Discovery: <topic>

## Problem & Objectives

Scope, plus explicit non-goals.

## Reference Patterns

Files, conventions, or third-party implementations examined, with paths.

## Assumptions & Validation

Each assumption, how it was tested, and the observed outcome.

## Identified Risks & Spikes

Spike snippets run, edge cases observed, constraints discovered.
```
