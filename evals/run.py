#!/usr/bin/env python3
"""Run, grade, and report the ndev skill evals. See evals/README.md.

Examples::

    python3 evals/run.py list
    python3 evals/run.py run --skill nbuild --runs 1
    python3 evals/run.py run --baseline HEAD~1          # compare with an older version
    python3 evals/run.py run --also-model opencode/glm-5.3-flash   # compare agent models
    python3 evals/run.py grade evals-workspace/iteration-1
    python3 evals/run.py report evals-workspace/iteration-1
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness.cases import SKILLS, SKILLS_DIR, Case, load_cases  # noqa: E402
from harness.report import build_report  # noqa: E402
from harness.runner import FAILED, Config, Settings, execute_run, grade_run, rev_config  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
WORKSPACE = REPO / "evals-workspace"
DEFAULT_MODEL = os.environ.get("EVALS_MODEL", "opencode/claude-opus-5-5")
DEFAULT_CHEAP_MODEL = os.environ.get("EVALS_CHEAP_MODEL", "opencode/glm-5.3-flash")


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and dispatch to a subcommand."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    listing = sub.add_parser("list", help="list cases")
    _filters(listing)

    run = sub.add_parser("run", help="run cases, grade them, and write the report")
    _filters(run)
    run.add_argument("--runs", type=int, default=3, help="repetitions per case and config (default: 3)")
    run.add_argument("--baseline", help="also run a baseline: 'no-skill', or a git revision of skills/ndev")
    run.add_argument("--model", default=DEFAULT_MODEL, help=f"agent model (default: {DEFAULT_MODEL})")
    run.add_argument("--also-model", action="append", default=[],
                     help="run every config with this agent model too (repeatable)")
    run.add_argument("--user-model", default=DEFAULT_CHEAP_MODEL, help=f"simulated user (default: {DEFAULT_CHEAP_MODEL})")
    run.add_argument("--judge-model", default=DEFAULT_CHEAP_MODEL, help=f"LLM judge (default: {DEFAULT_CHEAP_MODEL})")
    run.add_argument("--no-judge", action="store_true", help="script checks only")
    run.add_argument("--jobs", type=int, default=4, help="parallel runs (default: 4)")
    run.add_argument("--timeout", type=int, default=1200, help="seconds per agent turn (default: 1200)")
    run.add_argument("--name", help="iteration folder name (default: next iteration-<n>)")
    run.add_argument("--keep-tmp", action="store_true", help="keep the /tmp work trees and homes")
    run.add_argument("--dry-run", action="store_true", help="print the planned runs and exit")
    run.add_argument("--retry-failed", action="store_true",
                     help="also redo runs that ended in error, timeout, or user_error")

    grade = sub.add_parser("grade", help="re-grade an iteration (for example after editing checks)")
    grade.add_argument("iteration", type=Path)
    grade.add_argument("--judge-model", default=DEFAULT_CHEAP_MODEL)
    grade.add_argument("--no-judge", action="store_true")
    grade.add_argument("--jobs", type=int, default=4)
    grade.add_argument("--failed-only", action="store_true", help="only runs whose judge call failed, or ungraded runs")

    report = sub.add_parser("report", help="rebuild benchmark.json and benchmark.md")
    report.add_argument("iteration", type=Path)

    args = parser.parse_args(argv)
    if args.command == "list":
        return _list(load_cases(args.skill, args.case, args.tag))

    if args.command == "run":
        return _run(args)

    if args.command == "grade":
        return _grade(args.iteration, None if args.no_judge else args.judge_model, args.jobs, args.failed_only)

    build_report(args.iteration.resolve())
    print(f"report: {args.iteration / 'benchmark.md'}")

    return 0


def _filters(parser: argparse.ArgumentParser) -> None:
    """Add the --skill and --case filters."""
    parser.add_argument("--skill", action="append", choices=SKILLS, help="only this skill (repeatable)")
    parser.add_argument("--case", action="append", help="only this case id (repeatable)")
    parser.add_argument("--tag", action="append", help="only cases with this tag, e.g. messy (repeatable)")


def _list(cases: list[Case]) -> int:
    """Print one line per case."""
    for case in cases:
        tags = f" [{', '.join(case.tags)}]" if case.tags else ""
        print(f"{case.id:32} {case.mode:9} {case.state:20} {case.description}{tags}")

    return 0


def _run(args: argparse.Namespace) -> int:
    """Run every selected case under every config, then grade and report."""
    cases = load_cases(args.skill, args.case, args.tag)
    iteration = (WORKSPACE / (args.name or _next_iteration())).resolve()
    kinds = [Config("with_skill", SKILLS_DIR)]
    if args.baseline == "no-skill":
        kinds.append(Config("no_skill", None))
    elif args.baseline:
        kinds.append(rev_config(args.baseline, iteration / "_skills"))

    models = [args.model, *args.also_model]
    configs = kinds if len(models) == 1 else [
        Config(f"{kind.label}@{_short_model(model)}", kind.skills_dir, model)
        for model in models
        for kind in kinds
    ]

    plan = [
        (case, config, iteration / case.id / config.label / f"run-{n}")
        for case in cases
        for config in configs
        for n in range(1, args.runs + 1)
    ]
    todo = [p for p in plan if not (p[2] / "metrics.json").is_file() or (args.retry_failed and _failed(p[2]))]
    print(f"{iteration}: {len(plan)} runs planned, {len(plan) - len(todo)} already done")
    if args.dry_run:
        for case, config, run_dir in todo:
            print(f"  {case.id} [{config.label}] {run_dir.name}")

        return 0

    iteration.mkdir(parents=True, exist_ok=True)
    judge = None if args.no_judge else args.judge_model
    (iteration / "iteration.json").write_text(json.dumps(_meta(args, configs, judge), indent=2))
    settings = Settings(
        model=args.model, user_model=args.user_model, judge_model=judge,
        timeout_s=args.timeout, keep_tmp=args.keep_tmp,
    )

    def job(case: Case, config: Config, run_dir: Path) -> str:
        if run_dir.exists():
            shutil.rmtree(run_dir)  # a failed run being redone: start clean

        metrics = execute_run(case, config, run_dir, settings)
        grading = grade_run(case, config.label, run_dir, judge)
        summary = grading["summary"]

        return (f"{case.id} [{config.label}] {run_dir.name}: {summary['passed']}/{summary['total']} "
                f"({metrics['ended']}, {metrics['duration_s']:.0f}s, {metrics['tokens']:,} tokens)")

    _parallel(job, todo, args.jobs)
    build_report(iteration)
    print(f"report: {iteration / 'benchmark.md'}")

    return 0


def _grade(iteration: Path, judge: str | None, jobs: int, failed_only: bool = False) -> int:
    """Re-grade the runs of an iteration (all, or only failed gradings), then rebuild the report."""
    iteration = iteration.resolve()
    by_id = {c.id: c for c in load_cases()}
    todo = []
    for metrics_path in sorted(iteration.glob("*/*/run-*/metrics.json")):
        metrics = json.loads(metrics_path.read_text())
        if metrics["case"] not in by_id:
            print(f"skip {metrics_path.parent}: case {metrics['case']!r} no longer exists")
            continue

        grading = metrics_path.parent / "grading.json"
        if failed_only and grading.is_file() and not json.loads(grading.read_text())["summary"].get("judge_error"):
            continue

        todo.append((by_id[metrics["case"]], metrics["config"], metrics_path.parent))

    def job(case: Case, config: str, run_dir: Path) -> str:
        summary = grade_run(case, config, run_dir, judge)["summary"]
        return f"{case.id} [{config}] {run_dir.name}: {summary['passed']}/{summary['total']}"

    _parallel(job, todo, jobs)
    build_report(iteration)
    print(f"report: {iteration / 'benchmark.md'}")

    return 0


def _parallel(job, items: list[tuple], jobs: int) -> None:
    """Run ``job(*item)`` for every item on a thread pool, printing each result."""
    with ThreadPoolExecutor(max_workers=max(1, jobs)) as pool:
        futures = {pool.submit(job, *item): item for item in items}
        for done, future in enumerate(as_completed(futures), 1):
            try:
                line = future.result()
            except Exception as exc:  # noqa: BLE001 - report and keep going
                line = f"{futures[future][0].id}: FAILED {exc!r}"

            print(f"[{done}/{len(items)}] {line}", flush=True)


def _failed(run_dir: Path) -> bool:
    """True when a finished run ended in an infrastructure failure."""
    return json.loads((run_dir / "metrics.json").read_text())["ended"] in FAILED


def _short_model(model: str) -> str:
    """Label part for ``model``: its last path segment, without a region and vendor prefix."""
    name = model.split("/")[-1].lower()

    return re.sub(r"^(?:[a-z]{2,6}\.)?(?:anthropic|amazon|meta|google|mistral|cohere)\.", "", name)


def _next_iteration() -> str:
    """Name of the next ``iteration-<n>`` folder."""
    numbers = [int(p.name.split("-")[1]) for p in WORKSPACE.glob("iteration-*") if p.name.split("-")[1].isdigit()]
    return f"iteration-{max(numbers, default=0) + 1}"


def _meta(args: argparse.Namespace, configs: list[Config], judge: str | None) -> dict:
    """Describe the iteration for the report."""
    def git(*cmd: str) -> str:
        return subprocess.run(["git", *cmd], cwd=REPO, capture_output=True, text=True).stdout.strip()

    return {
        "started": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_rev": git("rev-parse", "--short", "HEAD"),
        "git_dirty": bool(git("status", "--porcelain", "--", "skills")),
        "model": args.model,
        "also_models": args.also_model,
        "user_model": args.user_model,
        "judge_model": judge,
        "runs": args.runs,
        "configs": {c.label: c.model or args.model for c in configs},
    }


if __name__ == "__main__":
    sys.exit(main())
