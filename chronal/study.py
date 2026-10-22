"""An engineering study of selection fragility, not a market-performance benchmark."""

import csv
import platform
import tempfile
from pathlib import Path

import numpy as np

from .artifacts import FreshDirectory, _compare, code_fingerprint, dump, read, seal, verify_files
from .data import make_demo
from .engine import ExecutionConfig
from .evaluation import ResearchConfig, baseline_spec, choose_candidate, evaluate_region, stress_suite
from .spec import default_specs, integer


def run_study(destination, *, replications=12, first_seed=100):
    integer(replications, "replications", 2, 64)
    integer(first_seed, "first_seed", 0, 2**32 - 65)
    research, execution = ResearchConfig(), ExecutionConfig()
    specs = default_specs()
    with FreshDirectory(destination) as folder:
        registration = {
            "question": "How does the development-selected candidate compare with a fixed baseline on unseen synthetic sessions?",
            "hypothesis_status": "prospective engineering demonstration; not an alpha or novelty claim",
            "seeds": list(range(first_seed, first_seed + replications)),
            "sessions": 756,
            "research": research.to_dict(),
            "execution": execution.to_dict(),
            "candidates": [spec.to_dict() for spec in specs],
            "code_sha256": code_fingerprint(),
            "environment": {"python": platform.python_version(), "numpy": np.__version__},
            "primary_observation": "selected minus baseline total return on holdout; descriptive across fixed synthetic generator seeds",
            "limitations": "Not real markets. Replications share one hand-designed generator. No external timestamp or search-history enforcement.",
        }
        # Save the recipe before observing any results. No adaptive seed selection.
        dump(folder / "registration.json", registration)
        rows = []
        for seed in registration["seeds"]:
            data = make_demo(seed=seed)
            start, boundary = research.boundaries(len(data.close))
            dev_data = data.subset(boundary)
            development = evaluate_region(dev_data, specs, research, execution, start, boundary)
            name = choose_candidate(development)
            winner = next(spec for spec in specs if spec.name == name)
            holdout = evaluate_region(
                data, [baseline_spec(), winner], research, execution, boundary, len(data.close)
            )
            stress = stress_suite(dev_data, winner, research, execution, start, boundary)
            rows.append(
                {
                    "seed": seed,
                    "data_fingerprint": data.fingerprint,
                    "selected": name,
                    "development_excess_total_return": development[name]["metrics"]["total_return"]
                    - development["equal"]["metrics"]["total_return"],
                    "holdout_excess_total_return": holdout[name]["metrics"]["total_return"]
                    - holdout["equal"]["metrics"]["total_return"],
                    "development_return": development[name]["metrics"]["total_return"],
                    "holdout_return": holdout[name]["metrics"]["total_return"],
                    "holdout_baseline_return": holdout["equal"]["metrics"]["total_return"],
                    "holdout_max_drawdown": holdout[name]["metrics"]["max_drawdown"],
                    "double_cost_development_return": stress["double_cost"]["metrics"]["total_return"],
                    "delayed_development_return": stress["one_session_delay"]["metrics"]["total_return"],
                }
            )
        excess = np.array([row["holdout_excess_total_return"] for row in rows])
        result = {
            "registration": registration,
            "observations": rows,
            "summary": {
                "replications": replications,
                "positive_holdout_excess_count": int(np.sum(excess > 0)),
                "mean_holdout_excess_total_return": float(excess.mean()),
                "sd_holdout_excess_total_return": float(excess.std(ddof=1)),
                "minimum_holdout_excess_total_return": float(excess.min()),
                "maximum_holdout_excess_total_return": float(excess.max()),
                "interpretation": "Descriptive simulation outcomes, not statistical proof of an investable edge.",
            },
        }
        dump(folder / "results.json", result)
        with (folder / "observations.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        seal(folder)
    return result["summary"]


def verify_study(root, *, replay=False):
    """Verify a study with the same public command used for portfolio runs."""
    root = Path(root)
    verify_files(root)
    registration = read(root / "registration.json")
    results = read(root / "results.json")
    if registration != results["registration"]:
        raise ValueError("study results do not match their registered recipe")
    if registration["code_sha256"] != code_fingerprint():
        raise ValueError("package source differs from the registered study")
    seeds = registration["seeds"]
    integer(len(seeds), "replications", 2, 64)
    integer(seeds[0], "first_seed", 0, 2**32 - 65)
    if seeds != list(range(seeds[0], seeds[0] + len(seeds))):
        raise ValueError("study seeds must match the consecutive registered replication range")
    if [row["seed"] for row in results["observations"]] != seeds:
        raise ValueError("study observations do not match the registered seeds")
    if results["summary"]["replications"] != len(seeds):
        raise ValueError("study summary replication count is inconsistent")
    if replay:
        with tempfile.TemporaryDirectory(prefix="chronal-study-replay-") as temporary:
            fresh = Path(temporary) / "replication"
            run_study(fresh, replications=len(seeds), first_seed=seeds[0])
            actual = read(fresh / "results.json")
            # Preserve environment provenance, while permitting numeric replay
            # across compatible Python/NumPy versions rather than requiring
            # their version strings to match.
            actual["registration"]["environment"] = registration["environment"]
            _compare(actual, results)
            if (fresh / "observations.csv").read_text() != (root / "observations.csv").read_text():
                # Compare parsed numeric records through JSON above. CSV spelling
                # is platform dependent, but its cells must agree numerically.
                with (root / "observations.csv").open(newline="") as handle:
                    recorded = list(csv.DictReader(handle))
                with (fresh / "observations.csv").open(newline="") as handle:
                    computed = list(csv.DictReader(handle))
                if len(recorded) != len(computed):
                    raise ValueError("study CSV row count differs on replay")
                for a, b in zip(recorded, computed, strict=True):
                    if set(a) != set(b):
                        raise ValueError("study CSV fields differ on replay")
                    for key in a:
                        try:
                            _compare(float(a[key]), float(b[key]))
                        except ValueError:
                            if a[key] != b[key]:
                                raise ValueError("study CSV values differ on replay") from None
    return {
        "valid": True,
        "kind": "synthetic_selection_study",
        "replications": len(seeds),
        "replayed": replay,
        "code_sha256": registration["code_sha256"],
    }
