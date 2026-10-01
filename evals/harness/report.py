"""Aggregate graded runs into ``benchmark.json`` and ``benchmark.md``.

Per case and configuration: pass rate (mean ± sample stddev over runs),
tokens, cost, and duration. Configuration labels read ``<skills>[@<model>]``.

Deltas compare like with like:

- the skill against each baseline, with the same agent model;
- the primary agent model against each other model, both with the skill.

Runs where the simulated user went off script (fidelity failed) are left out
of the pass rates and listed in the notes: they say nothing about the skill.

Analyst notes on the expectations themselves, over the fair runs:

- flaky: passes in some runs of a configuration but not others;
- non-discriminating: passes in every run with the skill and with a baseline
  (same model), so it measures nothing about the skill;
- always failing with the skill: a skill gap, a fixture flaw, or a wrong check.
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from pathlib import Path

__all__ = ["build_report", "deltas"]


def build_report(iteration: Path) -> dict:
    """Read every ``grading.json`` and ``metrics.json`` under ``iteration`` and write the report.

    :param iteration: Iteration folder.
    :return: The benchmark data written to ``benchmark.json``.
    """
    runs = _load(iteration)
    meta = json.loads((iteration / "iteration.json").read_text()) if (iteration / "iteration.json").is_file() else {}
    configs = _order({r["config"] for r in runs}, meta)
    pairs = deltas(configs)
    cases = sorted({(r["skill_order"], r["case"]) for r in runs})

    def stats_for(selected: list[dict]) -> dict:
        return {c: _stats([r for r in selected if r["config"] == c]) for c in configs}

    table = []
    for _, case in cases:
        mine = [r for r in runs if r["case"] == case]
        table.append({"case": case, "skill": mine[0]["skill"], "configs": stats_for(mine)})

    skills = dict.fromkeys(r["skill"] for r in sorted(runs, key=lambda r: r["skill_order"]))
    data = {
        "iteration": iteration.name,
        "meta": meta,
        "configs": configs,
        "deltas": pairs,
        "totals": stats_for(runs),
        "per_skill": {s: stats_for([r for r in runs if r["skill"] == s]) for s in skills},
        "cases": table,
        "notes": _notes(runs, pairs),
    }
    (iteration / "benchmark.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))
    (iteration / "benchmark.md").write_text(_markdown(data))

    return data


def deltas(configs: list[str]) -> list[tuple[str, str]]:
    """Pairs ``(a, b)`` worth comparing, as ``a − b``.

    :param configs: Labels, primary configuration first.
    :return: Skill vs each baseline per model, then primary model vs each other model.
    """
    parsed = [(c, *_split(c)) for c in configs]
    models = list(dict.fromkeys(m for _, _, m in parsed))
    pairs = []
    for model in models:
        skill = next((c for c, k, m in parsed if m == model and k == "with_skill"), None)
        if skill:
            pairs += [(skill, c) for c, k, m in parsed if m == model and k != "with_skill"]

    primary = next((c for c, k, m in parsed if m == models[0] and k == "with_skill"), None)
    if primary:
        pairs += [(primary, c) for c, k, m in parsed if m != models[0] and k == "with_skill"]

    return pairs


def _split(label: str) -> tuple[str, str]:
    """``(kind, model)`` of a configuration label; model is ``""`` when absent."""
    kind, _, model = label.partition("@")

    return kind, model


def _order(labels: set[str], meta: dict) -> list[str]:
    """Primary model first (the order in ``iteration.json``), then with_skill first."""
    known = list(meta.get("configs") or [])
    rank = {label: i for i, label in enumerate(known)}

    return sorted(labels, key=lambda c: (rank.get(c, len(known)), _split(c)[0] != "with_skill", c))


def _load(iteration: Path) -> list[dict]:
    """One record per graded run."""
    from harness.cases import SKILLS

    runs = []
    for grading_path in sorted(iteration.glob("*/*/run-*/grading.json")):
        run_dir = grading_path.parent
        metrics = json.loads((run_dir / "metrics.json").read_text())
        grading = json.loads(grading_path.read_text())
        skill = metrics["skill"]
        runs.append(
            {
                "case": metrics["case"],
                "skill": skill,
                "skill_order": (SKILLS.index(skill) if skill in SKILLS else 99, metrics["case"]),
                "config": metrics["config"],
                "run": run_dir.name,
                "ended": metrics["ended"],
                "pass_rate": grading["summary"]["pass_rate"],
                "off_script": bool(grading["summary"].get("off_script")),
                "tokens": metrics["tokens"],
                "cost": metrics["cost"],
                "duration_s": metrics["duration_s"],
                "expectations": grading["expectations"],
            }
        )

    return runs


def _stats(runs: list[dict]) -> dict:
    """Pass rate over fair runs (mean, stddev); mean tokens, cost, duration over all runs."""
    if not runs:
        return {}

    rates = [r["pass_rate"] for r in runs if not r["off_script"]]

    return {
        "runs": len(runs),
        "off_script": len(runs) - len(rates),
        "pass_rate": round(statistics.fmean(rates), 3) if rates else None,
        "stddev": round(statistics.stdev(rates), 3) if len(rates) > 1 else 0.0,
        "tokens": round(statistics.fmean(r["tokens"] for r in runs)),
        "cost": round(statistics.fmean(r["cost"] for r in runs), 4),
        "duration_s": round(statistics.fmean(r["duration_s"] for r in runs), 1),
        "errors": sum(1 for r in runs if r["ended"] in ("error", "timeout")),
    }


def _notes(runs: list[dict], pairs: list[tuple[str, str]]) -> list[str]:
    """Analyst notes: off-script and failed runs, then flaky, always-failing, and non-discriminating checks."""
    notes = [f"off script (excluded): {r['case']} [{r['config']}] {r['run']}" for r in runs if r["off_script"]]
    notes += [f"run {r['ended']}: {r['case']} [{r['config']}] {r['run']}" for r in runs if r["ended"] in ("error", "timeout")]

    outcomes: dict[tuple[str, str, str], list[bool]] = defaultdict(list)
    for run in runs:
        if run["off_script"]:
            continue

        for exp in run["expectations"]:
            if exp["passed"] is not None and exp.get("kind") != "fidelity":
                outcomes[(run["case"], run["config"], exp["text"])].append(bool(exp["passed"]))

    for (case, config, text), results in sorted(outcomes.items()):
        if len(results) > 1 and 0 < sum(results) < len(results):
            notes.append(f"flaky: {case} [{config}] {sum(results)}/{len(results)}: {text}")

        if _split(config)[0] == "with_skill" and not any(results):
            notes.append(f"always fails with skill: {case} [{config}]: {text}")

    for skill, baseline in pairs:
        if _split(skill)[1] != _split(baseline)[1]:
            continue  # model comparison: both have the skill, so "discriminating" means nothing here

        for (case, config, text), results in sorted(outcomes.items()):
            other = outcomes.get((case, baseline, text))
            if config == skill and all(results) and other and all(other):
                notes.append(f"non-discriminating vs {baseline}: {case}: {text}")

    return notes


def _markdown(data: dict) -> str:
    """Render the benchmark as Markdown tables."""
    configs, pairs, meta = data["configs"], data["deltas"], data["meta"]
    lines = [f"# Benchmark: {data['iteration']}", ""]
    if meta:
        models = meta.get("configs") if isinstance(meta.get("configs"), dict) else {}
        lines += [
            f"- Agent: `{meta.get('model')}`"
            + "".join(f", `{m}`" for m in meta.get("also_models") or [])
            + f"; simulated user: `{meta.get('user_model')}`; judge: `{meta.get('judge_model') or 'off'}`",
            f"- Skills: `{meta.get('git_rev')}`{' (dirty)' if meta.get('git_dirty') else ''}; "
            f"runs per case: {meta.get('runs')}",
        ]
        lines += [f"- `{label}`: `{model}`" for label, model in models.items() if "@" in label]
        lines.append("")

    def cell(stats: dict) -> str:
        if not stats:
            return "—"

        off = f" ({stats['off_script']} off-script)" if stats["off_script"] else ""
        if stats["pass_rate"] is None:
            return f"—{off}"

        return f"{stats['pass_rate']:.2f} ± {stats['stddev']:.2f}{off}"

    def delta_cells(row: dict) -> str:
        out = []
        for a, b in pairs:
            ra, rb = row.get(a) or {}, row.get(b) or {}
            ok = ra.get("pass_rate") is not None and rb.get("pass_rate") is not None
            out.append(f"{ra['pass_rate'] - rb['pass_rate']:+.2f}" if ok else "—")

        return "".join(f" | {c}" for c in out)

    def header(first: str) -> list[str]:
        cols = [first, *configs, *(f"Δ {a} − {b}" for a, b in pairs)]
        return ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]

    lines += ["## Totals", "", *header("")]
    lines.append("| pass rate | " + " | ".join(cell(data["totals"][c]) for c in configs) + delta_cells(data["totals"]) + " |")
    for key, fmt in (("tokens", "{:,}"), ("cost", "${:.2f}"), ("duration_s", "{:.0f}s")):
        values = " | ".join(fmt.format(data["totals"][c][key]) for c in configs)
        lines.append(f"| {key} (mean) | {values}" + " | " * len(pairs) + " |")

    lines += ["", "## Per skill", "", *header("skill")]
    for skill, row in data["per_skill"].items():
        lines.append(f"| {skill} | " + " | ".join(cell(row.get(c, {})) for c in configs) + delta_cells(row) + " |")

    lines += ["", "## Per case", "", *header("case")]
    for row in data["cases"]:
        stats = row["configs"]
        lines.append(f"| {row['case']} | " + " | ".join(cell(stats.get(c, {})) for c in configs) + delta_cells(stats) + " |")

    lines += ["", "## Notes", ""]
    lines += [f"- {n}" for n in data["notes"]] or ["- none"]

    return "\n".join(lines) + "\n"
