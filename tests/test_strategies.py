import unittest
from dataclasses import replace

import numpy as np

from chronal.data import MarketData, make_demo
from chronal.spec import StrategySpec
from chronal.strategies import FEATURE_NAMES, fit_diagnostics, generate_targets


def rising_panel(sessions=100):
    dates = np.datetime64("2020-01-01T14:30", "us") + np.arange(sessions) * np.timedelta64(1, "D")
    closes = 100 * np.exp(np.arange(sessions)[:, None] * np.array([0.001, 0.002, 0.003, -0.001]))
    opens = closes / 1.0002
    closed = dates + np.timedelta64(6, "h")
    return MarketData(
        ("A", "B", "C", "D"),
        dates,
        closed,
        np.broadcast_to(closed[:, None], closes.shape),
        opens,
        np.maximum(opens, closes) * 1.01,
        np.minimum(opens, closes) / 1.01,
        closes,
        np.full(closes.shape, 1e6),
        {"synthetic": "true"},
    )


def alter_suffix(data, start, multiplier=3):
    changes = {}
    factors = np.ones(data.close.shape)
    factors[start:] = multiplier
    for name in ("open", "high", "low", "close"):
        changes[name] = getattr(data, name) * factors
    return replace(data, **changes)


class StrategyTests(unittest.TestCase):
    def test_momentum_top_k_differs_from_all_positive_trend(self):
        data = rising_panel()
        momentum = generate_targets(
            data,
            StrategySpec(
                "mom", "momentum", lookback=10, rebalance_every=1, top_k=1, max_weight=1, target_vol=1
            ),
        )
        trend = generate_targets(
            data,
            StrategySpec(
                "trend", "trend", lookback=10, rebalance_every=1, top_k=1, max_weight=1, target_vol=1
            ),
        )
        np.testing.assert_allclose(momentum[20], [0, 0, 1, 0])
        np.testing.assert_allclose(trend[20], [1 / 3, 1 / 3, 1 / 3, 0])

    def test_first_lookback_rebalance_and_cash_after_position_caps(self):
        data = rising_panel()
        spec = StrategySpec(
            "equal", "equal_weight", lookback=10, rebalance_every=3, max_weight=0.1, target_vol=1
        )
        targets = generate_targets(data, spec)
        self.assertTrue(np.isnan(targets[:12]).all())
        np.testing.assert_allclose(targets[12], [0.1] * 4)
        self.assertAlmostEqual(targets[12].sum(), 0.4)
        self.assertTrue(np.isnan(targets[13]).all())

    def test_no_positive_momentum_means_explicit_cash_decision(self):
        data = rising_panel()
        close = 100 * np.exp(-np.arange(100)[:, None] * np.array([0.001, 0.002, 0.003, 0.004]))
        data = replace(data, open=close, close=close, high=close * 1.01, low=close / 1.01)
        targets = generate_targets(data, StrategySpec("mom", "momentum", lookback=10, rebalance_every=1))
        np.testing.assert_array_equal(targets[20], np.zeros(4))

    def test_unavailable_current_or_historic_bar_skips_whole_decision(self):
        data = rising_panel()
        available = data.available_at.copy()
        available[20, 1] = data.close_time[30]
        delayed = replace(data, available_at=available)
        targets = generate_targets(
            delayed, StrategySpec("equal", "equal_weight", lookback=10, rebalance_every=1, target_vol=1)
        )
        self.assertTrue(np.isfinite(targets[19]).all())
        self.assertTrue(np.isnan(targets[20:30]).all())
        self.assertTrue(np.isfinite(targets[30]).all())

    def test_non_ml_prefix_and_future_suffix_invariance(self):
        data = make_demo(sessions=120)
        changed = alter_suffix(data, 80)
        for kind in ("equal_weight", "momentum", "trend"):
            spec = StrategySpec(kind, kind, lookback=10, rebalance_every=1)
            original = generate_targets(data, spec)
            with self.subTest(kind=kind):
                np.testing.assert_allclose(
                    original[:80], generate_targets(changed, spec)[:80], equal_nan=True
                )
                np.testing.assert_allclose(
                    original[:80], generate_targets(data.subset(80), spec), equal_nan=True
                )

    def test_caps_cash_and_shrunk_covariance_volatility_bound(self):
        data = make_demo(sessions=100)
        spec = StrategySpec(
            "equal", "equal_weight", lookback=10, rebalance_every=1, max_weight=0.17, target_vol=0.015
        )
        targets = generate_targets(data, spec)
        self.assertTrue(np.all(targets[10:] >= 0))
        self.assertTrue(np.all(targets[10:] <= spec.max_weight + 1e-12))
        self.assertTrue(np.all(targets[10:].sum(axis=1) <= 1 + 1e-12))
        for t in range(10, 100):
            close = data.close[t - 10 : t + 1]
            returns = close[1:] / close[:-1] - 1
            sample = np.cov(returns, rowvar=False, ddof=1)
            covariance = 0.8 * sample + 0.2 * np.diag(np.diag(sample))
            measured = np.sqrt(targets[t] @ covariance @ targets[t] * 252)
            self.assertLessEqual(measured, spec.target_vol + 1e-12)
        self.assertTrue(np.any(targets[10:].sum(axis=1) < 0.68 - 1e-6))

    def test_ridge_requires_training_and_emits_no_prefit_decisions(self):
        data = make_demo(sessions=100)
        spec = StrategySpec("ridge", "ridge", lookback=10, rebalance_every=1)
        for boundary in (None, True, 5, 101):
            with self.subTest(boundary=boundary), self.assertRaises(ValueError):
                generate_targets(data, spec, boundary)
        result = generate_targets(data, spec, 60)
        self.assertTrue(np.isnan(result[:60]).all())
        self.assertTrue(np.isfinite(result[60:]).all())

    def test_ridge_label_endpoints_and_training_only_scaler(self):
        data = make_demo(sessions=120)
        spec = StrategySpec("ridge", "ridge", lookback=10)
        diag = fit_diagnostics(data, spec, 60)
        self.assertEqual(max(diag["training_label_end_indices"]), 59)
        self.assertEqual(min(diag["training_feature_indices"]), 10)
        self.assertEqual(max(diag["training_feature_indices"]), 57)
        self.assertEqual(diag["sample_count"], 48 * 4)
        self.assertEqual(len(diag["feature_names"]), len(FEATURE_NAMES))
        # Independently compute first-feature training mean. A full-sample
        # normalizer would include the deliberately extreme suffix below.
        expected = np.array([data.close[k] / data.close[k - 1] - 1 for k in range(10, 58)]).mean()
        self.assertAlmostEqual(diag["feature_mean"][0], expected, places=15)
        changed = alter_suffix(data, 60, 1000)
        self.assertEqual(diag, fit_diagnostics(changed, spec, 60))
        self.assertEqual(diag, fit_diagnostics(data.subset(60), spec, 60))

    def test_unavailable_training_labels_are_excluded(self):
        data = make_demo(sessions=100)
        spec = StrategySpec("ridge", "ridge", lookback=10)
        availability = data.available_at.copy()
        availability[59] = data.close_time[65]
        diag = fit_diagnostics(replace(data, available_at=availability), spec, 60)
        self.assertLess(max(diag["training_label_end_indices"]), 59)
        self.assertEqual(diag["sample_count"], 47 * 4)

    def test_ridge_future_suffix_and_prefix_invariance(self):
        data = make_demo(sessions=120)
        spec = StrategySpec("ridge", "ridge", lookback=10, rebalance_every=1)
        original = generate_targets(data, spec, 60)
        changed = alter_suffix(data, 90)
        np.testing.assert_allclose(original[:90], generate_targets(changed, spec, 60)[:90], equal_nan=True)
        np.testing.assert_allclose(original[:90], generate_targets(data.subset(90), spec, 60), equal_nan=True)
        self.assertTrue(np.all(original[60:] >= 0))
        self.assertTrue(np.all(original[60:] <= spec.max_weight + 1e-12))

    def test_single_asset_covariance_supported(self):
        data = make_demo(sessions=40)
        one = MarketData(
            ("ONE",),
            data.open_time,
            data.close_time,
            data.available_at[:, :1],
            data.open[:, :1],
            data.high[:, :1],
            data.low[:, :1],
            data.close[:, :1],
            data.volume[:, :1],
            dict(data.metadata),
        )
        targets = generate_targets(one, StrategySpec("equal", "equal_weight", lookback=10, rebalance_every=1))
        self.assertEqual(targets.shape, (40, 1))
        self.assertTrue(np.isfinite(targets[10:]).all())


if __name__ == "__main__":
    unittest.main()
