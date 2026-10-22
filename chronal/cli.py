"""Command-line workflows. Every output destination is explicit and local."""

import argparse
import json
import sys
import time
from pathlib import Path

from .artifacts import make_plan, read, run_development, run_holdout, verify_bundle
from .data import load_csv, make_demo
from .engine import ExecutionConfig
from .evaluation import ResearchConfig
from .spec import default_specs, load_specs


def parser():
    p = argparse.ArgumentParser(
        prog="chronal", description="Replayable investment research. No live execution."
    )
    commands = p.add_subparsers(dest="command", required=True)
    demo = commands.add_parser(
        "demo", help="run the synthetic end-to-end demonstration, including its holdout"
    )
    demo.add_argument("--out", required=True, type=Path)
    demo.add_argument("--seed", type=int, default=17)
    demo.add_argument("--sessions", type=int, default=756)
    plan = commands.add_parser("plan", help="freeze dataset, candidates, source and evaluation rules")
    plan.add_argument("--data", required=True, type=Path)
    plan.add_argument(
        "--metadata", required=True, type=Path, help="JSON object mapping provenance fields to strings"
    )
    plan.add_argument("--specs", type=Path, help="JSON candidate list; default five built-in specifications")
    plan.add_argument("--out", required=True, type=Path)
    for field, default in [
        ("train-size", 252),
        ("test-size", 63),
        ("holdout-size", 126),
        ("gap", 2),
        ("seed", 17),
    ]:
        plan.add_argument("--" + field, type=int, default=default)
    for field, default in [
        ("initial-cash", 100000.0),
        ("commission-bps", 5.0),
        ("spread-bps", 4.0),
        ("slippage-bps", 3.0),
        ("max-participation", 0.01),
        ("drawdown-stop", 0.25),
    ]:
        plan.add_argument("--" + field, type=float, default=default)
    plan.add_argument("--delay-sessions", type=int, default=0)
    for name, help_text in [
        ("research", "evaluate development folds and freeze the selected candidate"),
        ("holdout", "open the final holdout once for the frozen candidate and baseline"),
    ]:
        sub = commands.add_parser(name, help=help_text)
        sub.add_argument("run", type=Path)
    verify = commands.add_parser(
        "verify", help="verify a portfolio run or synthetic study, with optional full numerical replay"
    )
    verify.add_argument("run", type=Path)
    verify.add_argument(
        "--replay", action="store_true", help="also recompute models, simulations and study replications"
    )
    validate = commands.add_parser("validate", help="validate a CSV without modifying it")
    validate.add_argument("--data", required=True, type=Path)
    validate.add_argument("--metadata", type=Path)
    specs = commands.add_parser("specs", help="print the bounded built-in strategy specifications")
    specs.add_argument("--validate", type=Path, help="validate a supplied candidate file instead")
    study = commands.add_parser("study", help="run a reproducible multi-seed synthetic selection study")
    study.add_argument("--out", required=True, type=Path)
    study.add_argument("--replications", type=int, default=12)
    study.add_argument("--first-seed", type=int, default=100)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    started = time.perf_counter()
    try:
        if args.command == "demo":
            data = make_demo(seed=args.seed, sessions=args.sessions)
            make_plan(data, default_specs(), ResearchConfig(seed=args.seed), ExecutionConfig(), args.out)
            dev = run_development(args.out)
            holdout = run_holdout(args.out)
            result = {
                "run": str(args.out.absolute()),
                "synthetic": True,
                "selected": dev["winner"],
                "development_report": str((args.out / "development" / "report.html").absolute()),
                "holdout_report": str((args.out / "holdout" / "report.html").absolute()),
                "holdout_return": holdout["results"][dev["winner"]]["metrics"]["total_return"],
                "verification": verify_bundle(args.out, replay=True),
            }
        elif args.command == "plan":
            data = load_csv(args.data, metadata=read(args.metadata))
            specs = load_specs(args.specs) if args.specs else default_specs()
            research = ResearchConfig(
                **{key: getattr(args, key) for key in ResearchConfig.__dataclass_fields__}
            )
            execution = ExecutionConfig(
                **{key: getattr(args, key) for key in ExecutionConfig.__dataclass_fields__}
            )
            result = make_plan(data, specs, research, execution, args.out)
        elif args.command in ("research", "holdout"):
            payload = run_development(args.run) if args.command == "research" else run_holdout(args.run)
            folder = "development" if args.command == "research" else "holdout"
            result = {
                "stage": payload["stage"],
                "selected": payload["winner"],
                "report": str((args.run / folder / "report.html").absolute()),
                "metrics": {name: value["metrics"] for name, value in payload["results"].items()},
            }
        elif args.command == "verify":
            result = verify_bundle(args.run, replay=args.replay)
        elif args.command == "validate":
            data = load_csv(args.data, metadata=read(args.metadata) if args.metadata else {})
            result = {
                "valid": True,
                "sessions": len(data.close),
                "assets": list(data.assets),
                "fingerprint": data.fingerprint,
            }
        elif args.command == "specs":
            specs = load_specs(args.validate) if args.validate else default_specs()
            result = [spec.to_dict() for spec in specs]
        else:
            from .study import run_study

            result = run_study(args.out, replications=args.replications, first_seed=args.first_seed)
        if isinstance(result, dict):
            result["elapsed_seconds"] = round(time.perf_counter() - started, 3)
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0
    except (ValueError, TypeError, KeyError, OSError, ArithmeticError) as error:
        print(f"chronal: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
