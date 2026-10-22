"""Descriptive path diagnostics. All returns/drawdowns are fractions, not percentages.

No statistic here is a forecast or a selection-adjusted performance claim.
"""

import math
from datetime import date, datetime, timezone

import numpy as np

from .evaluation import returns


def _positive_path(values, name):
    try:
        raw = np.asarray(values)
        if raw.dtype.kind not in "iuf" or raw.ndim != 1 or not len(raw):
            raise ValueError
        path = raw.astype(float)
        if np.any(~np.isfinite(path)) or np.any(path <= 0):
            raise ValueError
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be a nonempty finite positive numeric path") from exc
    return path


def _utc_date(value):
    if not isinstance(value, str):
        raise ValueError("dates must contain ISO UTC strings")
    try:
        if len(value) == 10:
            parsed = date.fromisoformat(value)
            if parsed.isoformat() != value:
                raise ValueError
            return datetime.combine(parsed, datetime.min.time(), timezone.utc)
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
            raise ValueError
        return parsed
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("dates must contain ISO calendar dates or explicit UTC timestamps") from exc


def portfolio_diagnostics(equity, initial_cash, dates, baseline_equity):
    """Summarize aligned end-of-session NAVs against an equally funded baseline.

    ``daily_returns`` includes initial cash -> first NAV. ``monthly_returns``
    compounds those returns by the corresponding session's UTC calendar month;
    boundary months may be partial. ``historical_cvar_95`` is the signed mean
    of the worst ceil(5% * sessions) daily observations, matching evaluation's
    historical expected-shortfall convention. ``ulcer_index`` is RMS drawdown
    over observed sessions relative to the running peak including initial cash.

    Episode indices use 0 for initial cash and i+1 for equity[i]. Recovery is
    first NAV at least the prior peak, or None if unrecovered. Duration counts
    strictly underwater observed sessions, excluding the peak and recovery.
    Flat new peaks reset the peak index to the latest equal NAV. ``depth`` is
    a signed drawdown fraction. Baseline excess is the difference between
    terminal total returns, not compounded daily active returns.
    """
    if isinstance(initial_cash, (bool, np.bool_)) or not isinstance(
        initial_cash, (int, float, np.integer, np.floating)
    ):
        raise ValueError("initial_cash must be finite positive numeric capital")
    capital = float(initial_cash)
    if not math.isfinite(capital) or capital <= 0:
        raise ValueError("initial_cash must be finite positive numeric capital")
    path = _positive_path(equity, "equity")
    baseline = _positive_path(baseline_equity, "baseline_equity")
    if isinstance(dates, str):
        raise ValueError("dates must be a sequence aligned with equity")
    try:
        parsed = [_utc_date(value) for value in dates]
    except TypeError as exc:
        raise ValueError("dates must be a sequence aligned with equity") from exc
    if len(path) != len(baseline) or len(path) != len(parsed):
        raise ValueError("equity, dates and baseline_equity must have equal lengths")
    if any(a >= b for a, b in zip(parsed, parsed[1:])):
        raise ValueError("dates must be strictly increasing")
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        daily = returns(path, capital)
        excess = float(path[-1] / capital - baseline[-1] / capital)
    if not np.all(np.isfinite(daily)) or not math.isfinite(excess):
        raise ValueError("capital and equity produce nonfinite returns")
    monthly = {}
    for moment, value in zip(parsed, daily):
        key = moment.strftime("%Y-%m")
        monthly[key] = monthly.get(key, 1.0) * (1.0 + float(value))
    if not all(math.isfinite(value) for value in monthly.values()):
        raise ValueError("monthly compounded returns must be finite")
    full = np.concatenate(([capital], path))
    drawdowns = full / np.maximum.accumulate(full) - 1.0
    episodes = []
    peak = 0
    active = None
    for index in range(1, len(full)):
        if full[index] >= full[peak]:
            if active is not None:
                active["recovery_index"] = index
                episodes.append(active)
                active = None
            peak = index
        else:
            if active is None:
                active = {
                    "peak_index": peak,
                    "trough_index": index,
                    "recovery_index": None,
                    "depth": float(drawdowns[index]),
                    "underwater_sessions": 0,
                }
            active["underwater_sessions"] += 1
            if drawdowns[index] < active["depth"]:
                active["trough_index"] = index
                active["depth"] = float(drawdowns[index])
    if active is not None:
        episodes.append(active)
    count = max(1, math.ceil(len(daily) * 0.05))
    return {
        "daily_returns": daily.tolist(),
        "monthly_returns": [{"month": key, "return": value - 1.0} for key, value in monthly.items()],
        "historical_cvar_95": float(np.mean(np.sort(daily)[:count])),
        "historical_tail_count": count,
        "ulcer_index": float(np.sqrt(np.mean(np.square(drawdowns[1:])))),
        "longest_underwater_sessions": max((e["underwater_sessions"] for e in episodes), default=0),
        "drawdown_episodes": episodes,
        "baseline_excess_total_return": excess,
    }
