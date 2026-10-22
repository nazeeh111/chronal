"""Observed ledger diagnostics for a report, without inferred asset price marks."""

import math
from numbers import Integral

import numpy as np


def ledger_diagnostics(simulation, assets):
    """Describe end-of-session cash, share inventory and observed fill activity.

    Weights use marked NAV as denominator, not initial capital. At zero NAV,
    cash/invested weights are None. Invested value is NAV minus cash; asset
    weights/concentration cannot be reconstructed from share counts alone.
    Commission is explicit cash fees; traded notional is absolute filled
    quantity times adverse fill price. Neither includes an inferred impact
    model. This is display analysis, not a substitute for bundle verification.
    """
    if (
        not isinstance(assets, (list, tuple))
        or not assets
        or any(not isinstance(asset, str) or not asset for asset in assets)
        or len(set(assets)) != len(assets)
    ):
        raise ValueError("assets must contain unique nonempty names")
    indices = simulation["indices"]
    if (
        not isinstance(indices, (list, tuple))
        or not indices
        or any(isinstance(i, (bool, np.bool_)) or not isinstance(i, Integral) or i < 0 for i in indices)
        or any(a >= b for a, b in zip(indices, indices[1:]))
    ):
        raise ValueError("session indices must be strictly increasing nonnegative integers")
    count = len(indices)

    def numbers(key, shape):
        raw = np.asarray(simulation[key])
        if raw.dtype.kind not in "iuf" or raw.shape != shape:
            raise ValueError(f"{key} has invalid numeric shape")
        values = raw.astype(float)
        if np.any(~np.isfinite(values)) or np.any(values < 0):
            raise ValueError(f"{key} must be finite and nonnegative")
        return values

    equity = numbers("equity", (count,))
    cash = numbers("cash", (count,))
    shares = numbers("positions", (count, len(assets)))
    tolerance = np.maximum(1.0, equity) * 1e-10
    if np.any(cash > equity + tolerance):
        raise ValueError("cash exceeds marked NAV in a long-only ledger")
    slots = {int(index): slot for slot, index in enumerate(indices)}
    activity = [{"fill_count": 0, "traded_notional": 0.0, "commission": 0.0} for _ in indices]
    for fill in simulation["fills"]:
        index = fill["index"]
        if isinstance(index, (bool, np.bool_)) or not isinstance(index, Integral) or index not in slots:
            raise ValueError("fill index is outside marked sessions")
        if fill["asset"] not in assets:
            raise ValueError("fill asset is outside the declared universe")
        values = []
        for key in ("quantity", "price", "commission"):
            value = fill[key]
            if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, float, np.number)):
                raise ValueError("fill values must be finite numbers")
            value = float(value)
            if not math.isfinite(value):
                raise ValueError("fill values must be finite numbers")
            values.append(value)
        quantity, price, commission = values
        if quantity == 0 or price <= 0 or commission < 0:
            raise ValueError("fill quantity, price or commission is invalid")
        row = activity[slots[index]]
        row["fill_count"] += 1
        row["traded_notional"] += abs(quantity) * price
        row["commission"] += commission
        if not math.isfinite(row["traded_notional"]) or not math.isfinite(row["commission"]):
            raise ValueError("fill totals overflow")
    cumulative = 0.0
    sessions = []
    for slot, index in enumerate(indices):
        cumulative += activity[slot]["commission"]
        if not math.isfinite(cumulative):
            raise ValueError("cumulative commission overflows")
        nav = float(equity[slot])
        cash_value = min(float(cash[slot]), nav)  # Round-off tolerance only.
        sessions.append(
            {
                "index": int(index),
                "cash_weight": cash_value / nav if nav > 0 else None,
                "invested_weight": (nav - cash_value) / nav if nav > 0 else None,
                "invested_value": nav - cash_value,
                "active_positions": int(np.count_nonzero(shares[slot] > 0)),
                "cumulative_commission": cumulative,
                **activity[slot],
            }
        )
    return {
        "sessions": sessions,
        "terminal_holdings": [
            {"asset": asset, "shares": float(quantity)} for asset, quantity in zip(assets, shares[-1])
        ],
    }
