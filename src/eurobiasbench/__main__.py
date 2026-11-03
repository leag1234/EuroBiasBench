"""EuroBiasBench command line interface."""
from __future__ import annotations

import argparse
import json

from .core import load_dataset, validate_dataset
from .pipeline import run
from .reporting import report


def main() -> None:
    parser = argparse.ArgumentParser(prog="eurobiasbench")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("validate", help="Check dataset schema")
    check.add_argument("--dataset", default=None)
    check.add_argument("--pilot", action="store_true")
    runner = commands.add_parser("run", help="Run a synthetic or live evaluation")
    runner.add_argument("--mode", choices=("mock", "live"), default="mock")
    runner.add_argument("--dataset", default=None)
    runner.add_argument("--models", default="config/models.toml")
    runner.add_argument("--judges", default="config/judges.toml")
    runner.add_argument("--output", default="results/pilot")
    runner.add_argument("--repeats", type=int, default=3)
    runner.add_argument("--limit", type=int, default=None)
    reporting = commands.add_parser("report", help="Build descriptive report and audit queue")
    reporting.add_argument("--input", default="results/pilot")
    reporting.add_argument("--audit-fraction", type=float, default=0.1)
    args = parser.parse_args()
    if args.command == "validate":
        cases, digest = load_dataset(args.dataset)
        validate_dataset(cases, pilot=args.pilot)
        print(json.dumps({"valid": True, "cases": len(cases), "sha256": digest}, indent=2))
    elif args.command == "run":
        print(json.dumps(run(
            mode=args.mode, dataset_path=args.dataset, models_path=args.models,
            judges_path=args.judges, output=args.output, repeats=args.repeats, limit=args.limit,
        ), indent=2))
    else:
        print(json.dumps(report(args.input, audit_fraction=args.audit_fraction), indent=2))


if __name__ == "__main__":
    main()
