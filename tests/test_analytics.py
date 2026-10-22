import json
import math
import unittest

import numpy as np

from chronal.analytics import portfolio_diagnostics
from chronal.evaluation import metrics


class AnalyticsTests(unittest.TestCase):
    def test_hand_calculation_and_initial_capital(self):
        result = portfolio_diagnostics(
            [90, 99, 79.2], 100, ["2024-01-29", "2024-01-30", "2024-02-01"], [100, 101, 110]
        )
        np.testing.assert_allclose(result["daily_returns"], [-0.1, 0.1, -0.2])
        self.assertAlmostEqual(result["monthly_returns"][0]["return"], -0.01)
        self.assertAlmostEqual(result["monthly_returns"][1]["return"], -0.2)
        self.assertEqual([x["month"] for x in result["monthly_returns"]], ["2024-01", "2024-02"])
        self.assertAlmostEqual(result["ulcer_index"], math.sqrt((0.1**2 + 0.01**2 + 0.208**2) / 3))
        self.assertAlmostEqual(result["baseline_excess_total_return"], -0.308)
        self.assertEqual(result["historical_cvar_95"], metrics([90, 99, 79.2], 100)["historical_cvar_95"])
        self.assertEqual(result["longest_underwater_sessions"], 3)
        self.assertEqual(result["drawdown_episodes"][0]["peak_index"], 0)
        self.assertEqual(result["drawdown_episodes"][0]["trough_index"], 3)
        self.assertIsNone(result["drawdown_episodes"][0]["recovery_index"])
        json.dumps(result, allow_nan=False)

    def test_recovered_and_open_episodes_and_equal_peak_reset(self):
        result = portfolio_diagnostics(
            [100, 90, 80, 100, 110, 99, 105],
            100,
            [f"2024-01-{day:02d}" for day in range(1, 8)],
            [100] * 7,
        )
        first, second = result["drawdown_episodes"]
        self.assertEqual((first["peak_index"], first["trough_index"], first["recovery_index"]), (1, 3, 4))
        self.assertEqual(first["underwater_sessions"], 2)
        self.assertEqual(
            (second["peak_index"], second["trough_index"], second["recovery_index"]), (5, 6, None)
        )
        self.assertEqual(second["underwater_sessions"], 2)
        self.assertEqual(result["longest_underwater_sessions"], 2)

    def test_flat_and_single_session(self):
        for values, dates in (([100], ["2024-01-01"]), ([100, 100], ["2024-01-01", "2024-01-02"])):
            with self.subTest(values=values):
                result = portfolio_diagnostics(values, 100, dates, values)
                self.assertEqual(result["drawdown_episodes"], [])
                self.assertEqual(result["ulcer_index"], 0)
                self.assertEqual(result["longest_underwater_sessions"], 0)
                self.assertEqual(result["baseline_excess_total_return"], 0)

    def test_tail_count_ceil_and_year_boundary(self):
        daily = np.array([-0.1, -0.2] + [0.01] * 19)
        values = 100 * np.cumprod(1 + daily)
        dates = ["2023-12-31T23:00:00Z"] + [f"2024-01-{day:02d}T00:00:00+00:00" for day in range(1, 21)]
        result = portfolio_diagnostics(values, 100, dates, [100] * 21)
        self.assertAlmostEqual(result["historical_cvar_95"], -0.15)
        self.assertEqual(result["historical_tail_count"], 2)
        self.assertEqual([x["month"] for x in result["monthly_returns"]], ["2023-12", "2024-01"])
        compounded = math.prod(1 + x["return"] for x in result["monthly_returns"]) - 1
        self.assertAlmostEqual(compounded, values[-1] / 100 - 1)

    def test_reject_invalid_paths_capital_and_alignment(self):
        for values in ([], [0], [-1], [np.nan], [np.inf], [[100]], [True], ["100"]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                portfolio_diagnostics(values, 100, ["2024-01-01"], [100])
            with self.subTest(baseline=values), self.assertRaises(ValueError):
                portfolio_diagnostics([100], 100, ["2024-01-01"], values)
        for capital in (0, -1, np.nan, np.inf, True, "100", None):
            with self.subTest(capital=capital), self.assertRaises(ValueError):
                portfolio_diagnostics([100], capital, ["2024-01-01"], [100])
        with self.assertRaises(ValueError):
            portfolio_diagnostics([100, 101], 100, ["2024-01-01"], [100])

    def test_reject_invalid_dates_and_nonfinite_derived_return(self):
        for dates in (
            ["2024-01-01", "2024-01-01"],
            ["2024-01-02", "2024-01-01"],
            ["2024-01-01", "2024-02-30"],
            ["2024-01-01", "2024-02-01T00:00:00"],
            ["2024-01-01", "2024-02-01T00:00:00+01:00"],
            ["2024-01-01", 1],
            None,
        ):
            with self.subTest(dates=dates), self.assertRaises(ValueError):
                portfolio_diagnostics([100, 101], 100, dates, [100, 100])
        with self.assertRaises(ValueError):
            portfolio_diagnostics([1e308], 1e-308, ["2024-01-01"], [100])
