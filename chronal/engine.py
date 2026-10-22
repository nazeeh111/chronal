"""Auditable daily cash simulation with explicit causal execution assumptions.

Decisions observed at a session close execute at a later session open. Capacity
uses the signal session's known volume and the fill session's *realized* volume.
The latter is an ex-post daily proxy, not liquidity observable at the open.
Unfilled orders expire after that open. There is no real-money execution path.
"""

from __future__ import annotations

import math
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from numbers import Integral, Real
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from .data import MarketData


def _number(name: str, value: object) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite real number")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{name} must be a finite real number")
    return value


@dataclass(frozen=True)
class ExecutionConfig:
    initial_cash: float = 100000.0
    commission_bps: float = 5.0
    spread_bps: float = 4.0
    slippage_bps: float = 3.0
    max_participation: float = 0.01
    delay_sessions: int = 0
    drawdown_stop: float = 0.25

    def __post_init__(self) -> None:
        for name in (
            "initial_cash",
            "commission_bps",
            "spread_bps",
            "slippage_bps",
            "max_participation",
            "drawdown_stop",
        ):
            object.__setattr__(self, name, _number(name, getattr(self, name)))
        if self.initial_cash <= 0:
            raise ValueError("initial_cash must be positive")
        if not 0 <= self.commission_bps < 10000:
            raise ValueError("commission_bps must be in [0, 10000)")
        if self.spread_bps < 0 or self.slippage_bps < 0:
            raise ValueError("spread_bps and slippage_bps must be nonnegative")
        if self.spread_bps / 2 + self.slippage_bps >= 10000:
            raise ValueError("half-spread plus slippage must be below 10000 bps")
        if not 0 < self.max_participation <= 1:
            raise ValueError("max_participation must be in (0, 1]")
        if not 0 < self.drawdown_stop <= 1:
            raise ValueError("drawdown_stop must be in (0, 1]")
        if (
            isinstance(self.delay_sessions, (bool, np.bool_))
            or not isinstance(self.delay_sessions, Integral)
            or self.delay_sessions < 0
        ):
            raise ValueError("delay_sessions must be a nonnegative integer")
        object.__setattr__(self, "delay_sessions", int(self.delay_sessions))

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Simulation:
    indices: list[int]
    equity: list[float]
    cash: list[float]
    positions: list[list[float]]
    fills: list[dict]
    events: list[dict]
    initial_cash: float
    total_fees: float
    total_notional: float
    intents: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Return an independent JSON-native representation of the ledger."""
        return deepcopy(asdict(self))


def _targets(value: object, shape: tuple[int, int]) -> np.ndarray:
    raw = np.asarray(value)
    if raw.dtype.kind not in "iuf" or raw.shape != shape:
        raise ValueError(f"targets must be a numeric array with shape {shape}")
    weights = np.array(raw, dtype=float, copy=True)
    missing = np.isnan(weights)
    if np.any(missing.any(axis=1) != missing.all(axis=1)):
        raise ValueError("target rows must be entirely finite or entirely NaN")
    finite_indices = np.flatnonzero(~missing.all(axis=1))
    finite_rows = weights[finite_indices]
    if not np.all(np.isfinite(finite_rows)):
        raise ValueError("targets must contain only finite weights or all-NaN rows")
    if np.any(finite_rows < 0) or np.any(finite_rows > 1):
        raise ValueError("target weights must be in [0, 1]")
    for index, row in zip(finite_indices, finite_rows):
        total = math.fsum(float(w) for w in row)
        if total > 1 + 1e-12:
            raise ValueError("target weights must sum to at most 1")
        # Remove harmless rounding excess so the feasible set remains exact.
        if total > 1:
            weights[index] /= total
    return weights


def _timestamp(value: np.datetime64) -> str:
    return str(np.datetime_as_string(value, unit="us", timezone="UTC"))


def simulate(
    data: MarketData,
    targets: object,
    config: ExecutionConfig = ExecutionConfig(),
    *,
    start: int = 1,
    stop: int | None = None,
) -> Simulation:
    """Replay long-only target weights in ``[start, stop)``.

    A target at close ``t`` is eligible at open ``t+1+delay_sessions``.
    An all-NaN row keeps the existing book. Targets are sized from open NAV;
    sells precede proportionally cash-scaled buys, including commissions.
    Current-session volume limits fills only as an ex-post capacity proxy.
    Close NAV is reported ex post. Risk highwater and drawdown use only actual
    historical equity snapshots whose complete mark row is published by the
    current close. A trigger latches permanent liquidation attempts beginning
    at the next open, subject to the same capacity constraints.
    """
    if not isinstance(config, ExecutionConfig):
        raise ValueError("config must be an ExecutionConfig")
    n, asset_count = data.open.shape
    weights = _targets(targets, (n, asset_count))
    stop = n if stop is None else stop
    for name, value in (("start", start), ("stop", stop)):
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
            raise ValueError(f"{name} must be an integer session index")
    start, stop = int(start), int(stop)
    if not 1 <= start < stop <= n:
        raise ValueError("require 1 <= start < stop <= number of sessions")

    cash = config.initial_cash
    positions = np.zeros(asset_count, dtype=float)
    result = Simulation([], [], [], [], [], [], cash, 0.0, 0.0)
    highwater = cash
    pending_marks: list[tuple[int, float, np.datetime64]] = []
    latest_observed_mark: tuple[int, float] | None = None
    stopped_at: int | None = None
    cost_fraction = (config.spread_bps / 2 + config.slippage_bps) / 10000
    commission_fraction = config.commission_bps / 10000
    cash_tolerance = max(1.0, cash) * 1e-12

    def event(index: int, kind: str, **details: object) -> None:
        result.events.append({"index": index, "type": kind, "details": details})

    for index in range(start, stop):
        reference = data.open[index]
        nav = cash + math.fsum(float(q * p) for q, p in zip(positions, reference))
        if not math.isfinite(nav) or nav < 0:
            raise ValueError("nonfinite or negative open portfolio value")
        signal = index - 1 - config.delay_sessions
        risk = stopped_at is not None
        eligible = False
        known_volume = np.zeros(asset_count, dtype=float)

        if risk:
            target = np.zeros(asset_count, dtype=float)
            eligible = bool(np.any(positions > 0))
            if eligible:
                event(index, "risk_liquidation", triggered_at=stopped_at)
            # Risk decisions use the latest completed observation actually
            # published before this open, independently for each asset.
            for asset in range(asset_count):
                known = np.flatnonzero(
                    (data.available_at[:index, asset] <= data.open_time[index])
                    & (data.close_time[:index] < data.open_time[index])
                )
                if known.size:
                    known_volume[asset] = data.volume[int(known[-1]), asset]
        elif signal >= 0 and not np.isnan(weights[signal]).all():
            target = weights[signal]
            if np.all(data.available_at[signal] <= data.close_time[signal]):
                known_volume = data.volume[signal]
                eligible = True
            else:
                event(index, "unavailable_signal", signal_index=signal)

        if eligible:
            desired = target * nav / reference
            if not np.all(np.isfinite(desired)):
                raise ValueError("nonfinite target quantity")
            delta = desired - positions
            capacity = config.max_participation * np.minimum(known_volume, data.volume[index])
            requested = np.abs(delta)
            quantities = np.minimum(requested, capacity)
            # Observe requests before execution without altering sizing/accounting.
            session_intents = {}
            for asset in range(asset_count):
                if delta[asset] == 0:
                    continue
                intent = {
                    "index": index,
                    "asset": data.assets[asset],
                    "kind": "risk" if risk else "normal",
                    "signal_index": None if risk else signal,
                    "signal_time": None if risk else _timestamp(data.close_time[signal]),
                    "requested_quantity": float(delta[asset]),
                    "capacity_limit": float(capacity[asset]),
                    "capacity_allowed_quantity": math.copysign(float(quantities[asset]), float(delta[asset])),
                    "cash_scaled_quantity": None,
                    "filled_quantity": 0.0,
                    "expired_quantity": 0.0,
                    "cash_scale": None,
                    "reasons": ["volume_capacity"] if requested[asset] > capacity[asset] else [],
                }
                session_intents[asset] = intent
                result.intents.append(intent)
            for asset in range(asset_count):
                if requested[asset] > capacity[asset]:
                    event(
                        index,
                        "zero_capacity" if capacity[asset] == 0 else "partial_capacity",
                        asset=data.assets[asset],
                        requested_quantity=float(delta[asset]),
                        capacity=float(capacity[asset]),
                        unfilled_quantity=float(requested[asset] - capacity[asset]),
                        signal_index=None if risk else signal,
                    )

            def fill(asset: int, quantity: float) -> None:
                nonlocal cash
                if quantity == 0:
                    return
                price = float(reference[asset] * (1 + math.copysign(cost_fraction, quantity)))
                notional = abs(quantity) * price
                fee = notional * commission_fraction
                change = -quantity * price - fee
                new_cash = math.fsum((cash, change))
                if not all(math.isfinite(v) for v in (price, notional, fee, new_cash)):
                    raise ValueError("nonfinite fill accounting")
                if new_cash < -cash_tolerance:
                    raise ArithmeticError("fill would produce negative cash")
                cash = max(0.0, new_cash)
                positions[asset] += quantity
                if positions[asset] < 0:
                    raise ArithmeticError("fill would create a short position")
                result.fills.append(
                    {
                        "index": index,
                        "asset": data.assets[asset],
                        "quantity": float(quantity),
                        "price": price,
                        "reference_price": float(reference[asset]),
                        "commission": float(fee),
                        "signal_index": None if risk else signal,
                        "signal_time": None if risk else _timestamp(data.close_time[signal]),
                        "fill_time": _timestamp(data.open_time[index]),
                        "cash_after": float(cash),
                    }
                )
                session_intents[asset]["filled_quantity"] += float(quantity)
                result.total_fees += fee
                result.total_notional += notional

            # Sell first, releasing proceeds into the same cash account.
            for asset in range(asset_count):
                if delta[asset] < 0:
                    if quantities[asset] > positions[asset]:
                        session_intents[asset]["reasons"].append("inventory_roundoff")
                    fill(asset, -min(float(quantities[asset]), float(positions[asset])))
            buys = np.where(delta > 0, quantities, 0.0)
            unit_cost = reference * (1 + cost_fraction) * (1 + commission_fraction)
            required = math.fsum(float(q * cost) for q, cost in zip(buys, unit_cost))
            if not math.isfinite(required):
                raise ValueError("nonfinite buy cash requirement")
            scale = min(1.0, cash / required) if required > 0 else 1.0
            if scale < 1:
                event(
                    index,
                    "insufficient_cash",
                    requested_cash=required,
                    available_cash=float(cash),
                    proportional_scale=float(scale),
                )
            for asset, intent in session_intents.items():
                if delta[asset] > 0:
                    intent["cash_scale"] = float(scale)
                    intent["cash_scaled_quantity"] = float(buys[asset] * scale)
                    if scale < 1 and buys[asset] > 0:
                        intent["reasons"].append("cash_limit")
                else:
                    intent["cash_scaled_quantity"] = intent["capacity_allowed_quantity"]
            for asset in range(asset_count):
                quantity = float(buys[asset] * scale)
                if quantity > 0:
                    # Last-bit roundoff must never create an overdraft.
                    quantity = min(quantity, cash / float(unit_cost[asset]))
                    fill(asset, quantity)
            for intent in session_intents.values():
                intent["expired_quantity"] = intent["requested_quantity"] - intent["filled_quantity"]
                intent["outcome"] = (
                    "blocked"
                    if intent["filled_quantity"] == 0
                    else "filled"
                    if intent["expired_quantity"] == 0
                    else "partial"
                )

        equity = cash + math.fsum(float(q * p) for q, p in zip(positions, data.close[index]))
        if not math.isfinite(equity) or equity < 0:
            raise ValueError("nonfinite or negative close portfolio value")
        result.indices.append(index)
        result.equity.append(float(equity))
        result.cash.append(float(cash))
        result.positions.append([float(q) for q in positions])

        # Marks are snapshots of the book that actually existed at each close.
        # Late publication cannot retroactively change decisions or reconstruct
        # old equity from today's holdings. Process newly published snapshots
        # in chronological row order, including older delayed peaks.
        ready_at = np.max(data.available_at[index])
        pending_marks.append((index, equity, ready_at))
        waiting: list[tuple[int, float, np.datetime64]] = []
        for mark_index, mark_equity, available_at in pending_marks:
            if available_at <= data.close_time[index]:
                highwater = max(highwater, mark_equity)
                if latest_observed_mark is None or mark_index > latest_observed_mark[0]:
                    latest_observed_mark = (mark_index, mark_equity)
            else:
                waiting.append((mark_index, mark_equity, available_at))
        pending_marks = waiting
        if ready_at > data.close_time[index]:
            event(
                index,
                "risk_mark_unavailable",
                mark_index=index,
                latest_available_index=None if latest_observed_mark is None else latest_observed_mark[0],
                available_after=_timestamp(ready_at),
            )
        if stopped_at is None and latest_observed_mark is not None:
            mark_index, observed_equity = latest_observed_mark
            drawdown = max(0.0, 1 - observed_equity / highwater)
            if drawdown + 1e-12 >= config.drawdown_stop:
                stopped_at = index
                event(
                    index,
                    "drawdown_stop",
                    drawdown=float(drawdown),
                    equity=float(observed_equity),
                    highwater=float(highwater),
                    mark_index=mark_index,
                    mark_time=_timestamp(data.close_time[mark_index]),
                )

    return result
