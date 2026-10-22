"""Analytical cost and evidence joins without reconstructing absent orders."""

import copy
import math
import unittest

from chronal.engine import simulate
from chronal.execution_diagnostics import execution_diagnostics
from test_engine import config, market


class ExecutionDiagnosticsTests(unittest.TestCase):
    def test_buy_sell_reference_friction_and_global_join(self):
        data = market([100] * 6)
        result = simulate(
            data,
            [[math.nan], [math.nan], [0.5], [0], [math.nan], [math.nan]],
            config(commission_bps=10, spread_bps=10, slippage_bps=5),
            start=3,
        ).to_dict()
        diagnostic = execution_diagnostics(result, data.assets)
        self.assertEqual([r["index"] for r in diagnostic["sessions"]], [3, 4, 5])
        self.assertEqual(diagnostic["sessions"][0]["fill_ordinals"], [0])
        self.assertEqual(diagnostic["sessions"][1]["fill_ordinals"], [1])
        self.assertEqual(diagnostic["sessions"][0]["normal_fill_delays_sessions"], [1])
        # Buy five shares at 100.1, sell five at 99.9: exactly one currency unit friction.
        self.assertAlmostEqual(diagnostic["totals"]["adverse_fill_cost"], 1.0)
        self.assertAlmostEqual(diagnostic["totals"]["commission"], 1.0)
        self.assertAlmostEqual(diagnostic["totals"]["explicit_execution_cost"], 2.0)
        self.assertEqual(diagnostic["sessions"][2]["evidence_status"], "no_recorded_execution_evidence")

    def test_capacity_events_are_observed_and_quantities_not_added_as_cost(self):
        data = market([100] * 4, volumes=[100, 1, 0, 100])
        result = simulate(data, [[1], [1], [math.nan], [math.nan]], config()).to_dict()
        result["events"] = list(reversed(result["events"]))
        diagnostic = execution_diagnostics(result, data.assets)
        self.assertEqual(diagnostic["sessions"][0]["event_counts"], {"partial_capacity": 1})
        self.assertEqual(diagnostic["sessions"][1]["event_counts"], {"zero_capacity": 1})
        for row in diagnostic["sessions"]:
            for ordinal in row["event_ordinals"]:
                self.assertEqual(result["events"][ordinal]["index"], row["index"])
        self.assertEqual(diagnostic["totals"]["explicit_execution_cost"], 0)

    def test_delays_and_risk_have_distinct_evidence(self):
        data = market([100] * 6, closes=[100, 100, 50, 50, 50, 50])
        result = simulate(data, [[1]] * 6, config(drawdown_stop=0.2, delay_sessions=1)).to_dict()
        diagnostic = execution_diagnostics(result, data.assets)
        self.assertEqual(diagnostic["sessions"][1]["normal_fill_delays_sessions"], [2])
        self.assertGreater(diagnostic["totals"]["risk_fill_count"], 0)
        self.assertTrue(any("drawdown_stop" in r["event_counts"] for r in diagnostic["sessions"]))
        self.assertTrue(any("risk_liquidation" in r["event_counts"] for r in diagnostic["sessions"]))

    def test_input_is_unmodified_and_invalid_evidence_rejected(self):
        result = simulate(market([100] * 3), [[1]] * 3, config()).to_dict()
        saved = copy.deepcopy(result)
        execution_diagnostics(result, ["ASSET_0"])
        self.assertEqual(saved, result)
        for edit in ("event", "reference", "signal"):
            with self.subTest(edit=edit):
                bad = copy.deepcopy(result)
                if edit == "event":
                    bad["events"].append({"index": 0, "type": "zero_capacity"})
                elif edit == "reference":
                    bad["fills"][0]["reference_price"] = math.nan
                else:
                    bad["fills"][0]["signal_index"] = bad["fills"][0]["index"]
                with self.assertRaises(ValueError):
                    execution_diagnostics(bad, ["ASSET_0"])


class IntentEvidenceTests(unittest.TestCase):
    def assert_intents(self, simulation):
        for intent in simulation.intents:
            observed = math.fsum(
                fill["quantity"]
                for fill in simulation.fills
                if (fill["index"], fill["asset"]) == (intent["index"], intent["asset"])
            )
            self.assertEqual(intent["filled_quantity"], observed)
            self.assertEqual(intent["expired_quantity"], intent["requested_quantity"] - observed)
            self.assertLessEqual(abs(observed), abs(intent["capacity_allowed_quantity"]))
            self.assertLessEqual(abs(intent["capacity_allowed_quantity"]), abs(intent["requested_quantity"]))
            self.assertEqual(
                intent["outcome"],
                "blocked" if observed == 0 else "filled" if intent["expired_quantity"] == 0 else "partial",
            )

    def test_capacity_and_expiration_are_per_open(self):
        result = simulate(
            market([100] * 4, volumes=[100, 1, 0, 100]), [[1], [1], [math.nan], [math.nan]], config()
        )
        self.assert_intents(result)
        first, second = result.intents
        self.assertEqual(first["requested_quantity"], 10)
        self.assertEqual(first["capacity_allowed_quantity"], 1)
        self.assertEqual(first["filled_quantity"], 1)
        self.assertEqual(first["expired_quantity"], 9)
        self.assertEqual(second["outcome"], "blocked")
        self.assertEqual(second["reasons"], ["volume_capacity"])
        self.assertEqual(len(result.intents), 2)  # No rolling pending order on final NaN row.

    def test_cash_scaling_and_sell_before_buy_evidence(self):
        result = simulate(
            market([[100, 100]] * 4),
            [[1, 0], [0, 1], [math.nan, math.nan], [math.nan, math.nan]],
            config(commission_bps=100),
        )
        self.assert_intents(result)
        first = result.intents[0]
        self.assertLess(first["cash_scale"], 1)
        self.assertIn("cash_limit", first["reasons"])
        self.assertAlmostEqual(
            first["cash_scaled_quantity"], first["capacity_allowed_quantity"] * first["cash_scale"]
        )
        sales = [i for i in result.intents if i["requested_quantity"] < 0]
        self.assertEqual(sales[0]["cash_scale"], None)
        self.assertEqual(sales[0]["outcome"], "filled")
        session_fills = [f for f in result.fills if f["index"] == 2]
        self.assertLess(session_fills[0]["quantity"], 0)
        self.assertGreater(session_fills[1]["quantity"], 0)

    def test_risk_retry_delay_and_ineligible_rows(self):
        data = market([100] * 6, closes=[100, 100, 50, 50, 50, 50], volumes=[100, 100, 100, 1, 1, 1])
        result = simulate(data, [[1]] * 6, config(drawdown_stop=0.2, delay_sessions=1))
        self.assert_intents(result)
        normal = [i for i in result.intents if i["kind"] == "normal"]
        risk = [i for i in result.intents if i["kind"] == "risk"]
        self.assertEqual(normal[0]["index"] - normal[0]["signal_index"], 2)
        self.assertGreater(len(risk), 1)
        self.assertEqual(len({i["index"] for i in risk}), len(risk))
        self.assertTrue(all(i["signal_time"] is None and i["signal_index"] is None for i in risk))
        late = market([100] * 3, late=[(0, 0, 24)])
        unavailable = simulate(late, [[1], [math.nan], [math.nan]], config())
        self.assertEqual(unavailable.intents, [])
        self.assertEqual(unavailable.events[0]["type"], "unavailable_signal")

    def test_intent_joins_and_predecessor_compatibility(self):
        result = simulate(market([100] * 3), [[1], [math.nan], [math.nan]], config()).to_dict()
        diagnosed = execution_diagnostics(result, ["ASSET_0"])
        self.assertEqual(diagnosed["totals"]["intent_count"], 1)
        self.assertEqual(diagnosed["sessions"][0]["intent_ordinals"], [0])
        self.assertEqual(diagnosed["sessions"][0]["intent_outcomes"], {"filled": 1})
        del result["intents"]
        old = execution_diagnostics(result, ["ASSET_0"])
        self.assertEqual(old["totals"]["intent_count"], 0)
        self.assertEqual(old["sessions"][0]["intent_ordinals"], [])
