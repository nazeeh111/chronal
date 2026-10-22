import copy
import json
import unittest

from chronal.ledger import ledger_diagnostics


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.sim = {
            "indices": [4, 5, 7],
            "equity": [100, 120, 110],
            "cash": [100, 20, 10],
            "positions": [[0, 0], [5, 10], [4, 10]],
            "fills": [
                {"index": 5, "asset": "A", "quantity": 5, "price": 10, "commission": 1},
                {"index": 5, "asset": "B", "quantity": 10, "price": 3, "commission": 2},
                {"index": 7, "asset": "A", "quantity": -1, "price": 12, "commission": 0.5},
            ],
        }

    def test_hand_calculated_inventory_activity_and_cash(self):
        before = copy.deepcopy(self.sim)
        result = ledger_diagnostics(self.sim, ["A", "B"])
        first, second, last = result["sessions"]
        self.assertEqual(first["cash_weight"], 1)
        self.assertEqual(first["active_positions"], 0)
        self.assertEqual(second["fill_count"], 2)
        self.assertEqual(second["traded_notional"], 80)
        self.assertEqual(second["commission"], 3)
        self.assertAlmostEqual(second["invested_weight"], 100 / 120)
        self.assertAlmostEqual(last["cash_weight"], 10 / 110)
        self.assertEqual(last["traded_notional"], 12)
        self.assertEqual(last["cumulative_commission"], 3.5)
        self.assertEqual(
            result["terminal_holdings"], [{"asset": "A", "shares": 4}, {"asset": "B", "shares": 10}]
        )
        self.assertEqual(self.sim, before)
        json.dumps(result, allow_nan=False)

    def test_zero_nav_has_no_defined_weights(self):
        result = ledger_diagnostics(
            {"indices": [0], "equity": [0], "cash": [0], "positions": [[0]], "fills": []}, ["A"]
        )
        self.assertIsNone(result["sessions"][0]["cash_weight"])
        self.assertIsNone(result["sessions"][0]["invested_weight"])
        self.assertEqual(result["sessions"][0]["invested_value"], 0)

    def test_reject_misalignment_invalid_inventory_and_universe(self):
        cases = [
            ("indices", [4, 4, 7]),
            ("indices", [True, 5, 7]),
            ("cash", [100]),
            ("cash", [101, 20, 10]),
            ("equity", [100, float("inf"), 110]),
            ("positions", [[0, 0], [-1, 1], [1, 1]]),
            ("positions", [[0], [1], [1]]),
        ]
        for key, value in cases:
            sim = copy.deepcopy(self.sim)
            sim[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                ledger_diagnostics(sim, ["A", "B"])
        for assets in ([], ["A", "A"], ["A", ""], [1, "B"]):
            with self.subTest(assets=assets), self.assertRaises(ValueError):
                ledger_diagnostics(self.sim, assets)

    def test_reject_invalid_fills(self):
        for key, value in (
            ("index", True),
            ("index", 6),
            ("asset", "C"),
            ("quantity", 0),
            ("quantity", "5"),
            ("price", -1),
            ("commission", -1),
            ("price", float("nan")),
        ):
            sim = copy.deepcopy(self.sim)
            sim["fills"][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                ledger_diagnostics(sim, ["A", "B"])
