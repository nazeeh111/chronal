import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from chronal.artifacts import (
    FreshDirectory,
    check_ledger,
    dump,
    make_plan,
    open_plan,
    read,
    run_development,
    run_holdout,
    seal,
    sha,
    verify_bundle,
)
from chronal.cli import main
from chronal.data import make_demo
from chronal.engine import ExecutionConfig
from chronal.evaluation import ResearchConfig
from chronal.spec import StrategySpec, load_specs, strict_json


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "run"
        self.data = make_demo(seed=31, sessions=303)
        self.specs = [StrategySpec("momentum", "momentum"), StrategySpec("ml", "ridge")]
        self.research = ResearchConfig(train_size=100, test_size=30, holdout_size=60)
        self.execution = ExecutionConfig()

    def plan(self, data=None, root=None):
        return make_plan(
            self.data if data is None else data,
            self.specs,
            self.research,
            self.execution,
            self.root if root is None else root,
        )

    def test_complete_workflow_and_full_replay(self):
        self.plan()
        dev = run_development(self.root)
        self.assertFalse((self.root / "holdout").exists())
        packet = read(self.root / "development" / "ai-review-packet.json")
        self.assertNotIn("holdout", packet.get("candidate_metrics", {}))
        self.assertEqual(len(dev["dates"]), 243)
        holdout = run_holdout(self.root)
        self.assertEqual(set(holdout["results"]), {"equal", dev["winner"]})
        self.assertEqual(verify_bundle(self.root, replay=True)["replayed"], ["development", "holdout"])
        with self.assertRaises(ValueError):
            run_holdout(self.root)

    def test_holdout_prices_cannot_change_development_selection_or_models(self):
        self.plan()
        first = run_development(self.root)
        values = {}
        for name in ("open", "high", "low", "close"):
            value = getattr(self.data, name).copy()
            value[243:] *= 4.0
            values[name] = value
        changed = replace(self.data, **values)
        other = Path(self.temp.name) / "other"
        self.plan(changed, other)
        second = run_development(other)
        self.assertNotEqual(first["plan"]["data_fingerprint"], second["plan"]["data_fingerprint"])
        self.assertEqual(first["results"], second["results"])
        self.assertEqual(first["winner"], second["winner"])
        self.assertEqual(first["uncertainty"], second["uncertainty"])

    def test_input_tampering_detected_and_source_mismatch_rejected(self):
        self.plan()
        with patch("chronal.artifacts.code_fingerprint", return_value="wrong"):
            with self.assertRaisesRegex(ValueError, "source differs"):
                open_plan(self.root)
        with (self.root / "input.csv").open("a") as handle:
            handle.write("\n")
        with self.assertRaisesRegex(ValueError, "plan input changed"):
            verify_bundle(self.root)

    def test_report_and_missing_or_added_files_detected(self):
        self.plan()
        run_development(self.root)
        report = self.root / "development" / "report.html"
        report.write_text(report.read_text() + "edited")
        with self.assertRaisesRegex(ValueError, "bundle content changed"):
            verify_bundle(self.root)

    def test_independent_ledger_check_rejects_inconsistent_cash_and_nav(self):
        self.plan()
        payload = run_development(self.root)
        sim = payload["results"]["equal"]["simulation"]
        check_ledger(self.data, sim)
        sim["equity"][0] += 1
        with self.assertRaisesRegex(ValueError, "equity does not reconcile"):
            check_ledger(self.data, sim)

    def test_failure_does_not_publish_partial_directory_or_replace_valid_work(self):
        target = Path(self.temp.name) / "fresh"
        with self.assertRaises(RuntimeError), FreshDirectory(target) as temporary:
            (temporary / "partial.txt").write_text("partial")
            raise RuntimeError("experiment failed")
        self.assertFalse(target.exists())
        target.mkdir()
        (target / "valuable.txt").write_text("preserved")
        with self.assertRaises(ValueError), FreshDirectory(target):
            pass
        self.assertEqual((target / "valuable.txt").read_text(), "preserved")

    def test_symlinked_result_rejected(self):
        self.plan()
        run_development(self.root)
        folder = self.root / "development"
        (folder / "link.txt").symlink_to(folder / "results.json")
        with self.assertRaisesRegex(ValueError, "symbolic link"):
            verify_bundle(self.root)

    def test_fresh_directory_preserves_dangling_destination_links(self):
        missing = Path(self.temp.name) / "missing"
        self.root.symlink_to(missing, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "destination exists"), FreshDirectory(self.root):
            pass
        self.assertTrue(self.root.is_symlink())
        self.assertEqual(self.root.readlink(), missing)
        self.root.unlink()
        with self.assertRaisesRegex(ValueError, "destination appeared"), FreshDirectory(self.root) as fresh:
            (fresh / "partial.txt").write_text("temporary output")
            self.root.symlink_to(missing, target_is_directory=True)
        self.assertTrue(self.root.is_symlink())
        self.assertEqual(self.root.readlink(), missing)
        self.assertFalse(fresh.exists())
        self.assertFalse(missing.exists())

    def test_proposals_reject_executable_fields_nonfinite_duplicate_and_bool_values(self):
        path = Path(self.temp.name) / "specs.json"
        invalid = [
            '[{"name":"a","kind":"momentum","code":"import os"}]',
            '[{"name":"a","kind":"momentum","max_weight":NaN}]',
            '[{"name":"a","kind":"momentum","lookback":true}]',
            '[{"name":"a","name":"b","kind":"momentum"}]',
            '[{"name":"a","kind":"momentum"},{"name":"a","kind":"trend"}]',
            '[{"name":"<script>","kind":"momentum"}]',
        ]
        for text in invalid:
            path.write_text(text)
            with self.subTest(text=text), self.assertRaises(ValueError):
                load_specs(path)
        with self.assertRaises(ValueError):
            strict_json('{"x":Infinity}')

    def test_json_rejects_overflowing_numbers_before_schema_validation(self):
        # JSON exponents can overflow without spelling an Infinity constant.
        # This boundary is shared by plans, results and study records, not
        # only bounded strategy fields that have their own numeric validation.
        for literal in ("1e309", "-1e309", "1.7976931348623159e308"):
            with self.subTest(literal=literal), self.assertRaisesRegex(ValueError, "non-finite JSON number"):
                strict_json('{"nested":[' + literal + "]}")
        self.assertEqual(
            strict_json('{"large":1e308,"small":-1e-308,"integer":9007199254740993}'),
            {"large": 1e308, "small": -1e-308, "integer": 9007199254740993},
        )

    def test_reserved_baseline_cannot_be_redefined(self):
        self.specs.append(StrategySpec("equal", "ridge"))
        with self.assertRaisesRegex(ValueError, "reserved equal"):
            self.plan()

    def test_resealed_selection_cannot_replace_development_winner(self):
        self.plan()
        payload = run_development(self.root)
        other = next(spec for spec in self.specs if spec.name != payload["winner"])
        selection = read(self.root / "development" / "selection.json")
        selection["strategy"] = other.to_dict()
        dump(self.root / "development" / "selection.json", selection)
        seal(self.root / "development", parent_hash=sha(self.root / "plan.json"))
        with self.assertRaisesRegex(ValueError, "frozen selection"):
            verify_bundle(self.root, replay=True)
        with self.assertRaisesRegex(ValueError, "frozen selection"):
            run_holdout(self.root)

    def test_resealed_false_dates_cannot_change_report_chronology(self):
        self.plan()
        payload = run_development(self.root)
        payload["dates"] = [
            (datetime(1900, 1, 1, tzinfo=timezone.utc) + timedelta(days=i)).isoformat()
            for i in range(len(payload["dates"]))
        ]
        from chronal.report import render_report

        folder = self.root / "development"
        dump(folder / "results.json", payload)
        (folder / "report.html").write_text(render_report(payload))
        seal(folder, parent_hash=sha(self.root / "plan.json"))
        with self.assertRaisesRegex(ValueError, "dates, assets or provenance"):
            verify_bundle(self.root, replay=True)

    def test_resealed_csv_cannot_diverge_from_the_financial_record(self):
        self.plan()
        run_development(self.root)
        folder = self.root / "development"
        for name in ("equity.csv", "fills.csv"):
            original = (folder / name).read_bytes()
            (folder / name).write_text("fabricated CSV")
            seal(folder, parent_hash=sha(self.root / "plan.json"))
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "CSV export"):
                verify_bundle(self.root, replay=True)
            (folder / name).write_bytes(original)
            seal(folder, parent_hash=sha(self.root / "plan.json"))

    def test_unsupported_stress_does_not_destroy_a_valid_base_experiment(self):
        self.execution = replace(self.execution, commission_bps=6000.0)
        self.plan()
        payload = run_development(self.root)
        self.assertEqual(payload["stress"]["double_cost"]["status"], "unavailable")
        self.assertIn("commission_bps", payload["stress"]["double_cost"]["reason"])
        self.assertEqual(payload["stress"]["one_session_delay"]["status"], "complete")
        self.assertEqual(verify_bundle(self.root, replay=True)["replayed"], ["development"])

    def test_bad_csv_cli_fails_cleanly(self):
        self.assertEqual(main(["validate", "--data", str(self.root / "missing.csv")]), 2)


if __name__ == "__main__":
    unittest.main()
