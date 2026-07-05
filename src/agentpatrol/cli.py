"""Command-line interface for AgentPatrol.

Uses argparse only (no extra runtime dependency). The standalone scripts in
``scripts/`` delegate to the functions here.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from agentpatrol import build_evaluator, build_runtime
from agentpatrol.database import seed_database
from agentpatrol.tools import DEFAULT_DB_PATH
from agentpatrol.trace import DEFAULT_TRACE_PATH, TraceLogger


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def cmd_seed(db_path: str = DEFAULT_DB_PATH) -> None:
    path = seed_database(db_path)
    print(f"Seeded demo database at {path}")


def cmd_demo(
    task_path: str,
    approve_review: bool = False,
    config_path: str | None = None,
    db_path: str = DEFAULT_DB_PATH,
    trace_path: str = DEFAULT_TRACE_PATH,
) -> str:
    runtime = build_runtime(config_path, db_path=db_path, trace_path=trace_path)
    task = _load_json(task_path)
    report = runtime.run(task, approve_review=approve_review)

    print(f"\nTask: {report.user_task}")
    print(f"Run id: {report.run_id}\n")
    for step in report.steps:
        marker = {
            "allow": "ALLOW ",
            "warn": "WARN  ",
            "review": "REVIEW",
            "block": "BLOCK ",
        }[step.decision.value]
        status = "executed" if step.executed else "skipped"
        print(f"[{marker}] {step.tool_name:<15} {status:<9} {step.reason}")
    print(f"\nSummary: {report.summary}")
    print(f"Trace written to {trace_path} (run id {report.run_id})")
    return report.run_id


def cmd_eval(
    scenarios_path: str = "examples/eval_scenarios.json",
    config_path: str | None = None,
    db_path: str = DEFAULT_DB_PATH,
) -> None:
    evaluator = build_evaluator(config_path, db_path=db_path)
    scenarios = _load_json(scenarios_path)["scenarios"]
    results, metrics = evaluator.run(scenarios)

    print(f"\nEvaluated {metrics.total} scenarios\n")
    print(f"policy_accuracy                 : {metrics.policy_accuracy:.3f}")
    print(f"false_allow_rate                : {metrics.false_allow_rate:.3f}")
    print(f"false_block_rate                : {metrics.false_block_rate:.3f}")
    rp = "n/a" if metrics.review_precision is None else f"{metrics.review_precision:.3f}"
    print(f"review_precision                : {rp}")
    print(f"schema_validation_failure_count : {metrics.schema_validation_failure_count}")
    print(f"average_policy_latency_ms       : {metrics.average_policy_latency_ms:.4f}")

    print("\nby category (correct/total):")
    for category, stats in sorted(metrics.by_category.items()):
        print(f"  {category:<32} {stats['correct']}/{stats['total']}")

    mismatches = [r for r in results if not r.correct]
    if mismatches:
        print("\nmismatches:")
        for r in mismatches:
            print(f"  {r.name}: expected {r.expected.value}, got {r.actual.value}")


def cmd_replay(run_id: str, trace_path: str = DEFAULT_TRACE_PATH) -> None:
    trace = TraceLogger(trace_path).load(run_id)
    if trace is None:
        print(f"No trace found for run id {run_id} in {trace_path}")
        return
    print(f"\nRun {trace.run_id} @ {trace.timestamp}")
    print(f"Task: {trace.user_task}\n")
    for i, step in enumerate(trace.steps, start=1):
        print(f"Step {i}: {step.tool_name} [{step.decision.value}]")
        print(f"    validation : {step.validation_status}")
        print(f"    policy     : {step.policy_name} (risk {step.risk_score:.2f})")
        print(f"    reason     : {step.reason}")
        print(f"    execution  : {step.execution_status}")
        if step.review_approved is not None:
            print(f"    review     : {'approved' if step.review_approved else 'not approved'}")
        if step.output_summary:
            print(f"    output     : {step.output_summary}")
        print(f"    latency_ms : {step.latency_ms:.3f}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="agentpatrol", description="AgentPatrol CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_seed = sub.add_parser("seed", help="seed the demo database")
    p_seed.add_argument("--db", default=DEFAULT_DB_PATH)

    p_demo = sub.add_parser("demo", help="run a task through the runtime")
    p_demo.add_argument("--task", required=True)
    p_demo.add_argument("--approve-review", action="store_true")
    p_demo.add_argument("--config", default=None)
    p_demo.add_argument("--db", default=DEFAULT_DB_PATH)
    p_demo.add_argument("--trace", default=DEFAULT_TRACE_PATH)

    p_eval = sub.add_parser("eval", help="run evaluation scenarios")
    p_eval.add_argument("--scenarios", default="examples/eval_scenarios.json")
    p_eval.add_argument("--config", default=None)
    p_eval.add_argument("--db", default=DEFAULT_DB_PATH)

    p_replay = sub.add_parser("replay", help="print a trace timeline")
    p_replay.add_argument("--run-id", required=True)
    p_replay.add_argument("--trace", default=DEFAULT_TRACE_PATH)

    args = parser.parse_args(argv)
    if args.command == "seed":
        cmd_seed(args.db)
    elif args.command == "demo":
        cmd_demo(args.task, args.approve_review, args.config, args.db, args.trace)
    elif args.command == "eval":
        cmd_eval(args.scenarios, args.config, args.db)
    elif args.command == "replay":
        cmd_replay(args.run_id, args.trace)


if __name__ == "__main__":
    main()
