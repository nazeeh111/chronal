import unittest

import numpy as np

from chronal.data import make_demo
from chronal.engine import ExecutionConfig
from chronal.evaluation import (
    ResearchConfig,
    choose_candidate,
    evaluate_region,
    folds,
    metrics,
    paired_block_interval,
    region_targets,
)
from chronal.spec import StrategySpec


class EvaluationTests(unittest.TestCase):
    def test_metrics_hand_calculated_including_initial_loss(self):
        m = metrics([90.0, 99.0, 79.2], 100.0)
        self.assertAlmostEqual(m["total_return"], -0.208)
        self.assertAlmostEqual(m["max_drawdown"], -0.208)
        self.assertAlmostEqual(m["historical_cvar_95"], -0.2)
        r = np.array([-0.1, 0.1, -0.2])
        self.assertAlmostEqual(m["sharpe_zero_rf"], r.mean() / r.std(ddof=1) * np.sqrt(252))

    def test_constant_and_short_paths_keep_undefined_sharpe_explicit(self):
        self.assertIsNone(metrics([100.0, 100.0], 100.0)["sharpe_zero_rf"])
        self.assertIsNone(metrics([99.0], 100.0)["sharpe_zero_rf"])
        for path in ([], [np.nan], [np.inf], [0.0], [-1.0]):
            with self.subTest(path=path), self.assertRaises(ValueError):
                metrics(path, 100.0)

    def test_time_windows_are_contiguous_and_purged(self):
        config = ResearchConfig(train_size=100, test_size=30, holdout_size=60, gap=3)
        start, end = config.boundaries(303)
        blocks = folds(start, end, config)
        self.assertEqual((start, end), (103, 243))
        self.assertEqual(
            [i for f in blocks for i in range(f["test_start"], f["test_end"])], list(range(start, end))
        )
        self.assertTrue(all(f["train_end"] == f["test_start"] - 3 for f in blocks))
        with self.assertRaises(ValueError):
            config.boundaries(150)
        for kwargs in ({"gap": 1}, {"train_size": True}, {"seed": -1}):
            with self.assertRaises(ValueError):
                ResearchConfig(**kwargs)

    def test_fit_diagnostics_prove_label_endpoints_before_each_cutoff(self):
        data = make_demo(sessions=303)
        config = ResearchConfig(train_size=100, test_size=30, holdout_size=60)
        start, stop = config.boundaries(303)
        _, records = region_targets(
            data.subset(stop), StrategySpec("ml", "ridge"), folds(start, stop, config)
        )
        for record in records:
            model = record["model"]
            self.assertLess(max(model["training_label_end_indices"]), record["train_end"])
            self.assertLess(record["train_end"], record["first_decision_session"])
            self.assertEqual(len(model["feature_names"]), len(model["coefficients"]))

    def test_cash_and_holdings_do_not_reset_at_refit_boundaries(self):
        data = make_demo(sessions=303)
        config = ResearchConfig(train_size=100, test_size=30, holdout_size=60)
        start, stop = config.boundaries(303)
        spec = StrategySpec("baseline", "equal_weight")
        result = evaluate_region(data.subset(stop), [spec], config, ExecutionConfig(), start, stop)[spec.name]
        sim = result["simulation"]
        for fold in result["folds"][1:]:
            at = fold["test_start"] - start
            expected = sim["equity"][fold["test_end"] - start - 1] / sim["equity"][at - 1] - 1
            self.assertAlmostEqual(fold["total_return"], expected)
            self.assertGreater(sum(sim["positions"][at]), 0)
        self.assertAlmostEqual(sum(f["fees"] for f in result["folds"]), result["metrics"]["fees"])
        self.assertAlmostEqual(
            sum(f["traded_notional"] for f in result["folds"]), result["metrics"]["traded_notional"]
        )

    def test_selection_has_fixed_tie_break_and_baseline_is_ineligible(self):
        def row(sharpe):
            return {"metrics": {"sharpe_zero_rf": sharpe}}

        self.assertEqual(choose_candidate({"equal": row(99), "b": row(1), "a": row(1), "c": row(None)}), "a")
        with self.assertRaises(ValueError):
            choose_candidate({"equal": row(99)})

    def test_paired_resampling_keeps_alignment_and_local_rng(self):
        a, b = [101.0, 99.0, 102.0, 104.0], [101.0, 99.0, 102.0, 104.0]
        np.random.seed(124)
        state = np.random.get_state()
        result = paired_block_interval(a, b, 100.0)
        self.assertEqual(result["estimate"], 0.0)
        self.assertEqual(result["lower_95"], 0.0)
        self.assertEqual(result["upper_95"], 0.0)
        self.assertFalse(result["selection_adjusted"])
        np.testing.assert_equal(state, np.random.get_state())

    def test_paired_resampling_rejects_broadcastable_misalignment(self):
        with self.assertRaisesRegex(ValueError, "same session count"):
            paired_block_interval([110.0], [101.0, 102.0, 103.0], 100.0)
        for kwargs in ({"samples": 0}, {"block": 0}, {"samples": True}, {"seed": -1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                paired_block_interval([101.0, 102.0], [100.0, 101.0], 100.0, **kwargs)


if __name__ == "__main__":
    unittest.main()
