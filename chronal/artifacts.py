"""Portable experiment bundles, integrity checks and independent ledger replay."""

import csv
import hashlib
import json
import platform
import shutil
import tempfile
from pathlib import Path

import numpy as np

from . import __version__
from .data import load_csv, write_csv
from .engine import ExecutionConfig
from .evaluation import (
    ResearchConfig,
    baseline_spec,
    choose_candidate,
    evaluate_region,
    paired_block_interval,
    stress_suite,
)
from .spec import StrategySpec, load_specs, strict_json


def dump(path, value):
    Path(path).write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )


def read(path):
    return strict_json(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def code_fingerprint():
    root = Path(__file__).parent
    digest = hashlib.sha256()
    for path in sorted(root.glob("*.py")):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def file_map(folder):
    root = Path(folder)
    files = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"bundle contains a symbolic link: {path.name}")
        if path.is_file() and path != root / "manifest.json":
            files[path.relative_to(root).as_posix()] = sha(path)
    return files


def seal(folder, *, parent_hash=None):
    dump(
        Path(folder) / "manifest.json",
        {"schema_version": 1, "files": file_map(folder), "parent_plan_sha256": parent_hash},
    )


def verify_files(folder):
    folder = Path(folder)
    manifest_path = folder / "manifest.json"
    if manifest_path.is_symlink():
        raise ValueError("manifest must not be a symbolic link")
    expected = read(manifest_path)
    if expected["files"] != file_map(folder):
        raise ValueError(f"bundle content changed or files are missing: {folder.name}")
    return expected


class FreshDirectory:
    """Commit a complete directory by rename; retain existing valid outputs."""

    def __init__(self, destination):
        self.destination = Path(destination).absolute()
        self.temporary = None

    def __enter__(self):
        if self.destination.exists() or self.destination.is_symlink():
            raise ValueError(f"destination exists; choose a fresh directory: {self.destination}")
        self.destination.parent.mkdir(parents=True, exist_ok=True)
        self.temporary = Path(tempfile.mkdtemp(prefix=".chronal-", dir=self.destination.parent))
        return self.temporary

    def __exit__(self, kind, value, traceback):
        if kind is None:
            # Refuse a destination created concurrently instead of replacing it.
            if self.destination.exists() or self.destination.is_symlink():
                shutil.rmtree(self.temporary)
                raise ValueError(f"destination appeared during the run: {self.destination}")
            self.temporary.rename(self.destination)
        elif self.temporary and self.temporary.exists():
            shutil.rmtree(self.temporary)


def make_plan(data, specs, research, execution, destination):
    start, holdout_start = research.boundaries(len(data.close))
    if any(s.name == "equal" and s != baseline_spec() for s in specs):
        raise ValueError("the reserved equal baseline must match the built-in risk-matched baseline")
    if not any(s.name == "equal" for s in specs):
        specs = [baseline_spec(), *specs]
    if not 2 <= len(specs) <= 16 or len({s.name for s in specs}) != len(specs):
        raise ValueError("need 1–15 uniquely named candidates plus the baseline")
    if any(s.lookback >= research.train_size - research.gap - 3 for s in specs):
        raise ValueError("lookback is too long for the first training window")
    with FreshDirectory(destination) as folder:
        write_csv(data, folder / "input.csv")
        dump(folder / "metadata.json", dict(data.metadata))
        dump(folder / "candidates.json", [s.to_dict() for s in specs])
        plan = {
            "schema_version": 1,
            "chronal_version": __version__,
            "code_sha256": code_fingerprint(),
            "data_fingerprint": data.fingerprint,
            "input_sha256": sha(folder / "input.csv"),
            "metadata_sha256": sha(folder / "metadata.json"),
            "candidate_sha256": sha(folder / "candidates.json"),
            "research": research.to_dict(),
            "execution": execution.to_dict(),
            "development_start": start,
            "holdout_start": holdout_start,
            "sessions": len(data.close),
            "assets": list(data.assets),
            "selection_rule": "highest development zero-risk-free-rate Sharpe; lexical tie break; undefined ranks last",
            "registered_candidates": len(specs) - 1,
            "environment": {"python": platform.python_version(), "numpy": np.__version__},
            "limitations": [
                "Local hashes detect changes relative to a manifest; they are not signatures or independent timestamps.",
                "The operator can inspect the input CSV or create another run. This is an explicit holdout boundary, not a tamper-proof vault.",
                "Candidate count covers this plan only. External and previous manual trials are not discovered automatically.",
                "Timestamp declarations and data provenance are supplied by the importer, not certified by Chronal.",
            ],
        }
        dump(folder / "plan.json", plan)
        seal(folder)
    return plan


def open_plan(folder):
    root = Path(folder)
    if root.is_symlink() or (root / "manifest.json").is_symlink():
        raise ValueError("plan paths must not be symbolic links")
    # Root manifest intentionally covers only lock files, not later result directories.
    manifest = read(root / "manifest.json")
    expected_names = {"input.csv", "metadata.json", "candidates.json", "plan.json"}
    if set(manifest["files"]) != expected_names:
        raise ValueError("invalid plan manifest")
    for name, digest in manifest["files"].items():
        path = root / name
        if path.is_symlink() or sha(path) != digest:
            raise ValueError(f"plan input changed: {name}")
    plan = read(root / "plan.json")
    if plan["code_sha256"] != code_fingerprint():
        raise ValueError(
            "package source differs from the locked plan; retain the original source or create a fresh plan"
        )
    data = load_csv(root / "input.csv", metadata=read(root / "metadata.json"))
    if data.fingerprint != plan["data_fingerprint"]:
        raise ValueError("semantic data fingerprint mismatch")
    specs = load_specs(root / "candidates.json")
    return plan, data, specs, ResearchConfig(**plan["research"]), ExecutionConfig(**plan["execution"])


def validated_selection(root, plan, specs):
    """Verify the selection's semantics, beyond its content hash."""
    root = Path(root)
    selection = read(root / "development" / "selection.json")
    payload = read(root / "development" / "results.json")
    if selection["plan_sha256"] != sha(root / "plan.json") or payload["plan"] != plan:
        raise ValueError("selection or results belong to a different plan")
    expected = choose_candidate(payload["results"])
    registry = {spec.name: spec for spec in specs}
    if (
        payload["stage"] != "development"
        or payload["winner"] != expected
        or selection["strategy"] != registry[expected].to_dict()
        or selection["selection_rule"] != plan["selection_rule"]
    ):
        raise ValueError(
            "frozen selection does not match the development selection rule and registered specification"
        )
    if set(payload["results"]) != set(registry):
        raise ValueError("development candidate registry does not match the plan")
    for name, value in payload["results"].items():
        if value["spec"] != registry[name].to_dict():
            raise ValueError("evaluated candidate differs from its registered specification")
    return registry[expected]


def csv_exports(folder, data, results):
    with (folder / "equity.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["strategy", "close_time", "equity", "cash"])
        for name in sorted(results):
            result = results[name]
            sim = result["simulation"]
            for index, equity, cash in zip(sim["indices"], sim["equity"], sim["cash"]):
                writer.writerow([name, str(data.close_time[index]) + "Z", equity, cash])
    with (folder / "fills.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = [
            "strategy",
            "index",
            "asset",
            "quantity",
            "price",
            "reference_price",
            "commission",
            "signal_index",
            "signal_time",
            "fill_time",
            "cash_after",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for name in sorted(results):
            result = results[name]
            for fill in result["simulation"]["fills"]:
                writer.writerow({"strategy": name, **fill})


def write_region(folder, plan, data, results, *, stage, winner, uncertainty, stress):
    from .report import render_report

    payload = {
        "schema_version": 1,
        "stage": stage,
        "dataset": dict(data.metadata),
        "assets": list(data.assets),
        "plan": plan,
        "winner": winner,
        "results": results,
        "uncertainty": uncertainty,
        "stress": stress,
        "dates": [str(value) + "Z" for value in data.close_time],
    }
    dump(folder / "results.json", payload)
    csv_exports(folder, data, results)
    (folder / "report.html").write_text(render_report(payload), encoding="utf-8")
    return payload


def run_development(root):
    root = Path(root)
    plan, data, specs, research, execution = open_plan(root)
    # Strictly truncate the evaluation input before the holdout.
    data = data.subset(plan["holdout_start"])
    start, stop = plan["development_start"], plan["holdout_start"]
    with FreshDirectory(root / "development") as folder:
        results = evaluate_region(data, specs, research, execution, start, stop)
        winner = choose_candidate(results)
        candidate = next(s for s in specs if s.name == winner)
        uncertainty = paired_block_interval(
            results[winner]["simulation"]["equity"],
            results["equal"]["simulation"]["equity"],
            execution.initial_cash,
            seed=research.seed,
        )
        stress = stress_suite(data, candidate, research, execution, start, stop)
        payload = write_region(
            folder,
            plan,
            data,
            results,
            stage="development",
            winner=winner,
            uncertainty=uncertainty,
            stress=stress,
        )
        dump(
            folder / "selection.json",
            {
                "strategy": candidate.to_dict(),
                "plan_sha256": sha(root / "plan.json"),
                "selection_rule": plan["selection_rule"],
            },
        )
        packet = {
            "purpose": "Critique development evidence and propose bounded hypotheses for a NEW plan.",
            "instructions": [
                "Do not claim historical predictive skill from this synthetic demonstration.",
                "Consider cash, risk, turnover, selection bias and the equal baseline.",
                "Do not request credentials, call paid APIs or generate executable strategy code.",
                "Return a JSON list of StrategySpec objects. Hypotheses need a fresh chronological test.",
                "Holdout observations and holdout results are excluded from this packet.",
            ],
            "development_range": [str(data.close_time[start]), str(data.close_time[stop - 1])],
            "data_metadata": dict(data.metadata),
            "plan_sha256": sha(root / "plan.json"),
            "candidate_metrics": {name: value["metrics"] for name, value in results.items()},
            "candidate_specs": [s.to_dict() for s in specs],
            "selected_candidate": winner,
            "stress": stress,
            "conditional_uncertainty": uncertainty,
            "allowed_kinds": ["equal_weight", "momentum", "trend", "ridge"],
            "fields": StrategySpec("example", "momentum").to_dict(),
            "provenance_note": "Record the model, date, prompt and unedited response alongside a new candidate file.",
        }
        dump(folder / "ai-review-packet.json", packet)
        seal(folder, parent_hash=sha(root / "plan.json"))
    return payload


def run_holdout(root):
    root = Path(root)
    plan, data, specs, research, execution = open_plan(root)
    # Recompute development evidence before accepting the frozen selection.
    verify_bundle(root, replay=True)
    manifest = verify_files(root / "development")
    if manifest["parent_plan_sha256"] != sha(root / "plan.json"):
        raise ValueError("development results belong to a different plan")
    candidate = validated_selection(root, plan, specs)
    start, stop = plan["holdout_start"], len(data.close)
    with FreshDirectory(root / "holdout") as folder:
        results = evaluate_region(data, [baseline_spec(), candidate], research, execution, start, stop)
        uncertainty = paired_block_interval(
            results[candidate.name]["simulation"]["equity"],
            results["equal"]["simulation"]["equity"],
            execution.initial_cash,
            seed=research.seed,
        )
        payload = write_region(
            folder,
            plan,
            data,
            results,
            stage="holdout",
            winner=candidate.name,
            uncertainty=uncertainty,
            stress={},
        )
        seal(folder, parent_hash=sha(root / "plan.json"))
    return payload


def check_ledger(data, simulation):
    """Reconstruct cash, quantities and equity from fills, without the simulator."""
    cash = simulation["initial_cash"]
    quantity = np.zeros(len(data.assets))
    by_index = {}
    total_fees = 0.0
    notional = 0.0
    for fill in simulation["fills"]:
        by_index.setdefault(fill["index"], []).append(fill)
    if set(by_index) - set(simulation["indices"]):
        raise ValueError("fill outside reported sessions")
    for index, equity, reported_cash, holdings in zip(
        simulation["indices"], simulation["equity"], simulation["cash"], simulation["positions"], strict=True
    ):
        for fill in by_index.get(index, []):
            a = data.assets.index(fill["asset"])
            cash -= fill["quantity"] * fill["price"] + fill["commission"]
            quantity[a] += fill["quantity"]
            total_fees += fill["commission"]
            notional += abs(fill["quantity"] * fill["price"])
            if not np.isclose(cash, fill["cash_after"], rtol=1e-10, atol=1e-6):
                raise ValueError("fill cash does not reconcile")
            if cash < -1e-6 or np.any(quantity < -1e-8):
                raise ValueError("ledger has negative cash or a short position")
            if fill["signal_index"] is not None and fill["signal_index"] >= index:
                raise ValueError("fill precedes its eligible session")
        expected = cash + float(quantity @ data.close[index])
        if not np.isclose(expected, equity, rtol=1e-10, atol=1e-6):
            raise ValueError("marked equity does not reconcile")
        if not np.isclose(cash, reported_cash, rtol=1e-10, atol=1e-6) or not np.allclose(quantity, holdings):
            raise ValueError("portfolio snapshot does not reconcile")
    if not np.isclose(total_fees, simulation["total_fees"]) or not np.isclose(
        notional, simulation["total_notional"]
    ):
        raise ValueError("aggregate trading costs or notional do not reconcile")


def verify_bundle(root, *, replay=False):
    root = Path(root)
    if (root / "registration.json").exists() and not (root / "plan.json").exists():
        from .study import verify_study

        return verify_study(root, replay=replay)
    plan, data, specs, research, execution = open_plan(root)
    checked = []
    for stage in ("development", "holdout"):
        folder = root / stage
        if not folder.exists():
            continue
        manifest = verify_files(folder)
        if manifest["parent_plan_sha256"] != sha(root / "plan.json"):
            raise ValueError(f"{stage} plan link mismatch")
        payload = read(folder / "results.json")
        candidate = validated_selection(root, plan, specs)
        if payload["plan"] != plan or payload["stage"] != stage or payload["winner"] != candidate.name:
            raise ValueError("result stage, plan or winner does not match the frozen selection")
        region_data = data.subset(plan["holdout_start"]) if stage == "development" else data
        if (
            payload["dates"] != [str(value) + "Z" for value in region_data.close_time]
            or payload["assets"] != list(data.assets)
            or payload["dataset"] != dict(data.metadata)
        ):
            raise ValueError("report dates, assets or provenance differ from locked data")
        from .report import render_report

        if (folder / "report.html").read_text(encoding="utf-8") != render_report(payload):
            raise ValueError("report does not match the result record")
        for value in payload["results"].values():
            check_ledger(data, value["simulation"])
        with tempfile.TemporaryDirectory(prefix="chronal-csv-check-") as temporary:
            regenerated = Path(temporary)
            csv_exports(regenerated, region_data, payload["results"])
            for name in ("equity.csv", "fills.csv"):
                if (regenerated / name).read_text() != (folder / name).read_text():
                    raise ValueError(f"CSV export does not match its result ledger: {name}")
        if replay:
            subset = data.subset(plan["holdout_start"]) if stage == "development" else data
            start = plan["development_start"] if stage == "development" else plan["holdout_start"]
            selected = (
                specs
                if stage == "development"
                else [
                    baseline_spec(),
                    StrategySpec(**read(root / "development" / "selection.json")["strategy"]),
                ]
            )
            actual = evaluate_region(subset, selected, research, execution, start, len(subset.close))
            _compare(actual, payload["results"])
            if stage == "development" and choose_candidate(actual) != candidate.name:
                raise ValueError("replayed selection differs")
            interval = paired_block_interval(
                actual[candidate.name]["simulation"]["equity"],
                actual["equal"]["simulation"]["equity"],
                execution.initial_cash,
                seed=research.seed,
            )
            _compare(interval, payload["uncertainty"])
            stress = (
                stress_suite(subset, candidate, research, execution, start, len(subset.close))
                if stage == "development"
                else {}
            )
            _compare(stress, payload["stress"])
        checked.append(stage)
    return {
        "valid": True,
        "ledger_checked": checked,
        "replayed": checked if replay else [],
        "code_sha256": plan["code_sha256"],
        "data_fingerprint": data.fingerprint,
    }


def _compare(actual, expected):
    if isinstance(expected, dict):
        if set(actual) != set(expected):
            raise ValueError("replay fields differ")
        for key in expected:
            _compare(actual[key], expected[key])
    elif isinstance(expected, list):
        if len(actual) != len(expected):
            raise ValueError("replay lengths differ")
        for a, b in zip(actual, expected):
            _compare(a, b)
    elif isinstance(expected, (int, float)):
        if not np.isclose(actual, expected, rtol=1e-10, atol=1e-8):
            raise ValueError("replayed values differ")
    elif actual != expected:
        raise ValueError("replayed values differ")
