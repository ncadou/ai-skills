# skills

Each subfolder is one skill.

## ndev system

Phased workflow, human-gated. Run in order; each phase's artifact anchors the next:

- `nlearn/` — discovery investigation → `.ndev/discovery.md`
- `nplan/` — architecture blueprint → `.ndev/spec.md` + `.ndev/tasks/`
- `nbuild/` — one task slice with tests (takes a task file)
- `nreview/` — correctness + readability verdict on the slice

Format is decided per-skill for now; no repo-wide standard yet.
