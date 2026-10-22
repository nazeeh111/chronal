"""Analytical scenarios for the actual daily simulator, without remote data."""

import json
import math
import unittest

import numpy as np

from chronal.data import MarketData
from chronal.engine import ExecutionConfig, simulate


def market(opens, closes=None, volumes=None, late=None):
    opening = np.array(opens, dtype=float)
    if opening.ndim == 1:
        opening = opening[:, None]
    closing = opening.copy() if closes is None else np.array(closes, dtype=float).reshape(opening.shape)
    t, assets = opening.shape
    days = np.datetime64("2020-01-01", "us") + np.arange(t) * np.timedelta64(1, "D")
    open_time = days + np.timedelta64(9, "h")
    close_time = days + np.timedelta64(16, "h")
    available = np.repeat(close_time[:, None], assets, axis=1)
    if late:
        for row, asset, hours in late:
            available[row, asset] += np.timedelta64(hours, "h")
    return MarketData(
        assets=tuple(f"ASSET_{a}" for a in range(assets)),
        open_time=open_time,
        close_time=close_time,
        available_at=available,
        open=opening,
        high=np.maximum(opening, closing) * 1.01,
        low=np.minimum(opening, closing) * 0.99,
        close=closing,
        volume=np.full((t, assets), 10000.0)
        if volumes is None
        else np.array(volumes, dtype=float).reshape(opening.shape),
        metadata={"source": "analytical synthetic fixture", "corporate_actions": "none"},
    )


def config(**changes):
    args = dict(
        initial_cash=1000.0,
        commission_bps=0.0,
        spread_bps=0.0,
        slippage_bps=0.0,
        max_participation=1.0,
        drawdown_stop=1.0,
    )
    args.update(changes)
    return ExecutionConfig(**args)


class EngineTests(unittest.TestCase):
    def assert_ledger(self, data, result):
        cash = result.initial_cash
        shares = np.zeros(len(data.assets))
        fee_total = 0.0
        notional_total = 0.0
        fills = iter(result.fills)
        pending = next(fills, None)
        for slot, index in enumerate(result.indices):
            while pending is not None and pending["index"] == index:
                asset = data.assets.index(pending["asset"])
                q, price, fee = pending["quantity"], pending["price"], pending["commission"]
                cash -= q * price + fee
                shares[asset] += q
                fee_total += fee
                notional_total += abs(q) * price
                self.assertAlmostEqual(cash, pending["cash_after"], places=9)
                self.assertGreaterEqual(pending["cash_after"], 0)
                self.assertGreaterEqual(shares[asset], 0)
                pending = next(fills, None)
            self.assertAlmostEqual(cash, result.cash[slot], places=9)
            np.testing.assert_allclose(shares, result.positions[slot], atol=1e-12)
            self.assertAlmostEqual(cash + float(shares @ data.close[index]), result.equity[slot], places=8)
        self.assertIsNone(pending)
        self.assertAlmostEqual(fee_total, result.total_fees, places=10)
        self.assertAlmostEqual(notional_total, result.total_notional, places=8)

    def test_constant_prices_and_no_terminal_liquidation(self):
        data = market([100, 100, 100, 100])
        result = simulate(data, [[1], [math.nan], [math.nan], [0]], config())
        self.assertEqual(result.equity, [1000.0, 1000.0, 1000.0])
        self.assertEqual(len(result.fills), 1)
        self.assertEqual(result.positions[-1], [10.0])
        self.assertEqual(result.cash[-1], 0.0)
        self.assertEqual(result.fills[0]["signal_index"], 0)
        self.assertEqual(result.fills[0]["index"], 1)
        self.assert_ledger(data, result)

    def test_held_positions_keep_overnight_gaps(self):
        data = market([100, 100, 200, 180], [100, 100, 210, 180])
        result = simulate(data, [[1], [math.nan], [math.nan], [math.nan]], config())
        np.testing.assert_allclose(result.equity, [1000, 2100, 1800])
        self.assertEqual(result.positions[-1], [10.0])
        self.assert_ledger(data, result)

    def test_sells_release_shared_cash_before_buys(self):
        data = market([[100, 100]] * 4)
        targets = [[1, 0], [0, 1], [math.nan, math.nan], [math.nan, math.nan]]
        result = simulate(data, targets, config())
        switch = [fill for fill in result.fills if fill["index"] == 2]
        self.assertEqual([fill["quantity"] for fill in switch], [-10.0, 10.0])
        self.assertEqual([fill["asset"] for fill in switch], ["ASSET_0", "ASSET_1"])
        self.assertEqual(result.positions[-1], [0.0, 10.0])
        self.assert_ledger(data, result)

    def test_buy_scaling_preserves_relative_allocations_and_charges_fees(self):
        data = market([[100, 100]] * 3)
        result = simulate(
            data,
            [[0.5, 0.5], [math.nan, math.nan], [math.nan, math.nan]],
            config(commission_bps=100, spread_bps=20, slippage_bps=20),
        )
        execution = 100 * 1.003
        quantity = 1000 / (2 * execution * 1.01)
        np.testing.assert_allclose(result.positions[0], [quantity, quantity])
        self.assertAlmostEqual(result.total_fees, 1000 * 0.01 / 1.01)
        self.assertAlmostEqual(result.equity[0], 2 * quantity * 100)
        self.assertAlmostEqual(result.cash[0], 0.0)
        self.assertEqual(result.fills[0]["price"], execution)
        self.assertTrue(any(event["type"] == "insufficient_cash" for event in result.events))
        self.assert_ledger(data, result)

    def test_round_trip_adverse_prices_and_fee_costs(self):
        data = market([100] * 4)
        result = simulate(
            data,
            [[1], [0], [math.nan], [math.nan]],
            config(commission_bps=10, spread_bps=20, slippage_bps=10),
        )
        buy_price, sell_price = 100.2, 99.8
        shares = 1000 / (buy_price * 1.001)
        expected_cash = shares * sell_price * 0.999
        self.assertAlmostEqual(result.equity[-1], expected_cash)
        self.assertAlmostEqual(result.total_fees, shares * (buy_price + sell_price) * 0.001)
        self.assertEqual(result.positions[-1], [0.0])
        self.assert_ledger(data, result)

    def test_partial_capacity_expires_without_retry_on_nan(self):
        data = market([100] * 4, volumes=[100, 20, 100, 100])
        result = simulate(data, [[1], [math.nan], [math.nan], [math.nan]], config(max_participation=0.1))
        self.assertEqual(result.positions[-1], [2.0])
        self.assertEqual(len(result.fills), 1)
        self.assertEqual(result.cash[-1], 800.0)
        self.assertTrue(any(event["type"] == "partial_capacity" for event in result.events))
        self.assert_ledger(data, result)

    def test_zero_current_or_signal_volume_prevents_fill(self):
        for volume in ([0, 100, 100], [100, 0, 100]):
            with self.subTest(volume=volume):
                data = market([100] * 3, volumes=volume)
                result = simulate(data, [[1], [math.nan], [math.nan]], config())
                self.assertEqual(result.fills, [])
                self.assertEqual(result.equity, [1000.0, 1000.0])
                self.assertTrue(any(event["type"] == "zero_capacity" for event in result.events))

    def test_delay_uses_signal_session_volume(self):
        data = market([100] * 4, volumes=[5, 0, 100, 100])
        result = simulate(data, [[1], [math.nan], [math.nan], [math.nan]], config(delay_sessions=1))
        self.assertEqual(len(result.fills), 1)
        self.assertEqual(result.fills[0]["index"], 2)
        self.assertEqual(result.fills[0]["signal_index"], 0)
        self.assertEqual(result.fills[0]["quantity"], 5.0)
        self.assert_ledger(data, result)

    def test_unavailable_signal_is_rejected_even_if_known_by_delayed_fill(self):
        data = market([100] * 4, late=[(0, 0, 1)])
        result = simulate(data, [[1], [math.nan], [math.nan], [math.nan]], config(delay_sessions=1))
        self.assertEqual(result.fills, [])
        self.assertEqual(result.events[0]["type"], "unavailable_signal")

    def test_risk_latches_then_flattens_subject_to_capacity(self):
        data = market([100, 100, 70, 70, 200, 200], volumes=[10000, 10000, 10000, 3, 10000, 10000])
        result = simulate(data, [[1]] * 6, config(drawdown_stop=0.2))
        triggers = [e for e in result.events if e["type"] == "drawdown_stop"]
        self.assertEqual(len(triggers), 1)
        self.assertEqual(triggers[0]["index"], 2)
        risk_fills = [f for f in result.fills if f["signal_index"] is None]
        self.assertEqual([f["index"] for f in risk_fills], [3, 4, 5])
        self.assertEqual([f["quantity"] for f in risk_fills], [-3.0, -3.0, -4.0])
        self.assertEqual(result.positions[-1], [0.0])
        self.assertTrue(all(f["quantity"] < 0 for f in result.fills if f["index"] > 2))
        self.assert_ledger(data, result)

    def test_risk_falls_back_to_last_volume_known_before_open(self):
        data = market(
            [100, 100, 70, 70, 70],
            closes=[100, 70, 70, 70, 70],
            volumes=[10000, 10000, 0, 4, 10000],
            late=[(2, 0, 48)],
        )
        result = simulate(
            data, [[1], [math.nan], [math.nan], [math.nan], [math.nan]], config(drawdown_stop=0.2)
        )
        risk_fills = [f for f in result.fills if f["signal_index"] is None]
        self.assertEqual([f["quantity"] for f in risk_fills], [-4.0, -4.0])
        self.assertEqual(result.positions[-1], [2.0])
        self.assert_ledger(data, result)

    def test_late_mark_cannot_trigger_risk_before_publication(self):
        runs = []
        for delayed_close in (70, 90):
            data = market(
                [100] * 6,
                [100, 100, delayed_close, 100, 100, 100],
                late=[(2, 0, 48), (3, 0, 48), (4, 0, 48), (5, 0, 48)],
            )
            result = simulate(
                data,
                [[1], [math.nan], [math.nan], [math.nan], [math.nan], [math.nan]],
                config(drawdown_stop=0.2),
            )
            triggers = [e for e in result.events if e["type"] == "drawdown_stop"]
            self.assertTrue(all(e["index"] >= 4 for e in triggers))
            self.assertTrue(
                any(e["type"] == "risk_mark_unavailable" and e["index"] == 2 for e in result.events)
            )
            self.assertEqual(result.fills[0]["index"], 1)
            if delayed_close == 70:
                self.assertEqual(triggers[0]["index"], 4)
                self.assertEqual(triggers[0]["details"]["mark_index"], 2)
                self.assertEqual(result.fills[-1]["index"], 5)
            else:
                self.assertEqual(triggers, [])
            self.assert_ledger(data, result)
            runs.append(result)
        # Changing a hidden close changes the reported ex-post NAV, but no
        # decision, fill, or risk event before that mark's publication.
        self.assertNotEqual(runs[0].equity[1], runs[1].equity[1])
        self.assertEqual(
            [e for e in runs[0].events if e["index"] < 4], [e for e in runs[1].events if e["index"] < 4]
        )
        self.assertEqual(
            [f for f in runs[0].fills if f["index"] < 4], [f for f in runs[1].fills if f["index"] < 4]
        )

    def test_late_peak_uses_historical_equity_after_holdings_change(self):
        data = market([100] * 6, [100, 100, 200, 100, 100, 100], late=[(2, 0, 48)])
        targets = [[1], [math.nan], [math.nan], [0], [math.nan], [math.nan]]
        result = simulate(data, targets, config(drawdown_stop=0.3))
        triggers = [e for e in result.events if e["type"] == "drawdown_stop"]
        self.assertEqual(len(triggers), 1)
        self.assertEqual(triggers[0]["index"], 4)
        self.assertEqual(triggers[0]["details"]["highwater"], 2000.0)
        self.assertEqual(triggers[0]["details"]["equity"], 1000.0)
        self.assertEqual(result.positions[3], [0.0])
        self.assert_ledger(data, result)

    def test_invalid_targets_rejected_before_any_replay(self):
        data = market([[100, 100]] * 3)
        invalid = (
            [[1, 0], [math.nan, 0], [0, 0]],
            [[1, 0], [math.inf, 0], [0, 0]],
            [[1, 0], [-0.1, 0], [0, 0]],
            [[1, 0], [0.6, 0.6], [0, 0]],
            [[1, 0]],
            [["1", "0"]] * 3,
        )
        for target in invalid:
            with self.subTest(target=target), self.assertRaises(ValueError):
                simulate(data, target, config())

    def test_config_validation(self):
        for key, value in (
            ("initial_cash", 0),
            ("initial_cash", True),
            ("initial_cash", math.inf),
            ("commission_bps", -1),
            ("commission_bps", 10000),
            ("spread_bps", -1),
            ("slippage_bps", 10000),
            ("max_participation", 0),
            ("max_participation", 1.1),
            ("delay_sessions", 0.5),
            ("delay_sessions", True),
            ("drawdown_stop", 0),
            ("drawdown_stop", math.nan),
        ):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                ExecutionConfig(**{key: value})

    def test_prefix_does_not_change_past_fills_or_marks(self):
        data = market([100, 100, 110, 90, 150, 125])
        targets = np.array([[0.5], [0.8], [0.2], [0.4], [0.7], [math.nan]])
        full = simulate(data, targets, config())
        prefix = simulate(data.subset(4), targets[:4], config())
        self.assertEqual(prefix.equity, full.equity[:3])
        self.assertEqual(prefix.fills, [f for f in full.fills if f["index"] < 4])
        json.dumps(full.to_dict(), allow_nan=False)
        exported = full.to_dict()
        exported["fills"].clear()
        self.assertGreater(len(full.fills), 0)

    def test_subrange_starts_fresh_and_has_no_prior_positions(self):
        data = market([100, 100, 500, 500])
        result = simulate(data, [[1], [0.5], [math.nan], [math.nan]], config(), start=2)
        self.assertEqual(result.indices, [2, 3])
        self.assertEqual(result.positions[-1], [1.0])
        self.assertEqual(result.equity, [1000.0, 1000.0])
        self.assert_ledger(data, result)


if __name__ == "__main__":
    unittest.main()
