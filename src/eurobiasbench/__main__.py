"""EuroBiasBench command line interface."""
from __future__ import annotations

import argparse
import json
import sys

from .core import load_dataset, validate_dataset
from .pipeline import preflight, run
from .reporting import report


def _run_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--mode", choices=("mock", "live"), default="mock")
    parser.add_argument("--dataset", default=None)
    parser.add_argument("--models", default="config/models.toml")
    parser.add_argument("--judges", default="config/judges.toml")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--limit", type=int, default=None)


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "discover":
        from .discovery import cli
        cli(sys.argv[2:])
        return
    parser = argparse.ArgumentParser(prog="eurobiasbench")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("validate", help="Check dataset schema")
    check.add_argument("--dataset", default=None)
    check.add_argument("--pilot", action="store_true")
    plan = commands.add_parser("preflight", help="Check configs and compute calls, without network requests")
    _run_args(plan)
    runner = commands.add_parser("run", help="Run a synthetic or live evaluation")
    _run_args(runner)
    runner.add_argument("--output", default="results/pilot")
    runner.add_argument("--resume", action="store_true", help="Continue an interrupted identical run")
    reporting = commands.add_parser("report", help="Build descriptive report and audit queue")
    reporting.add_argument("--input", default="results/pilot")
    reporting.add_argument("--audit-fraction", type=float, default=0.1)
    args = parser.parse_args()
    if args.command == "validate":
        cases, digest = load_dataset(args.dataset)
        validate_dataset(cases, pilot=args.pilot)
        output = {"valid": True, "cases": len(cases), "sha256": digest}
    elif args.command == "preflight":
        output = preflight(
            mode=args.mode, dataset_path=args.dataset, models_path=args.models,
            judges_path=args.judges, repeats=args.repeats, limit=args.limit,
        )
    elif args.command == "run":
        output = run(
            mode=args.mode, dataset_path=args.dataset, models_path=args.models,
            judges_path=args.judges, output=args.output, repeats=args.repeats,
            limit=args.limit, resume=args.resume,
        )
    else:
        output = report(args.input, audit_fraction=args.audit_fraction)
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
