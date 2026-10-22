"""Chronological model fitting and cash-continuous out-of-sample evaluation."""

import math
from dataclasses import asdict, dataclass, replace

import numpy as np

from .engine import simulate
from .spec import StrategySpec, integer
from .strategies import fit_diagnostics, generate_targets


@dataclass(frozen=True)
class ResearchConfig:
    train_size: int = 252
    test_size: int = 63
    holdout_size: int = 126
    gap: int = 2
    seed: int = 17

    def __post_init__(self):
        integer(self.train_size, "train_size", 100, 100000)
        integer(self.test_size, "test_size", 10, 100000)
        integer(self.holdout_size, "holdout_size", 20, 100000)
        integer(self.gap, "gap", 2, 252)
        integer(self.seed, "seed", 0, 2**32 - 1)

    def to_dict(self):
        return asdict(self)

    def boundaries(self, sessions):
        end = sessions - self.holdout_size
        start = self.train_size + self.gap
        if end - start < self.test_size * 2:
            raise ValueError(
                "need at least two development test blocks before the holdout; add data or reduce windows"
            )
        return start, end


def folds(start, stop, config):
    """Each fit excludes `gap` observations preceding the first test session."""
    return [
        {
            "train_start": 0,
            "train_end": begin - config.gap,
            "test_start": begin,
            "test_end": min(begin + config.test_size, stop),
        }
        for begin in range(start, stop, config.test_size)
    ]


def returns(equity, initial_cash):
    values = np.asarray([initial_cash, *equity], dtype=float)
    if values.ndim != 1 or len(values) < 2 or np.any(~np.isfinite(values)) or np.any(values <= 0):
        raise ValueError("equity must be a nonempty finite positive path")
    return values[1:] / values[:-1] - 1.0


def metrics(equity, initial_cash, *, total_fees=0.0, total_notional=0.0):
    """Simple returns, geometric NAV growth, initial capital included in drawdown."""
    r = returns(equity, initial_cash)
    path = np.asarray([initial_cash, *equity], dtype=float)
    sd = float(np.std(r, ddof=1)) if len(r) > 1 else 0.0
    mean = float(np.mean(r))
    sharpe = mean / sd * math.sqrt(252) if sd > 1e-12 else None
    count = max(1, math.ceil(len(r) * 0.05))
    return {
        "sessions": len(r),
        "total_return": float(path[-1] / initial_cash - 1),
        "cagr": float((path[-1] / initial_cash) ** (252 / len(r)) - 1),
        "annual_volatility": sd * math.sqrt(252),
        "sharpe_zero_rf": sharpe,
        "max_drawdown": float(np.min(path / np.maximum.accumulate(path) - 1)),
        "historical_cvar_95": float(np.mean(np.sort(r)[:count])),
        "fees": float(total_fees),
        "traded_notional": float(total_notional),
        "turnover_per_session": float(total_notional / initial_cash / len(r)),
    }


def paired_block_interval(a, b, initial_cash, *, seed=17, samples=500, block=10):
    """Conditional, circular moving-block bootstrap of mean daily excess return.

    The fitted paths are held fixed. This is descriptive resampling, not a
    selection-adjusted test or a predictive interval for a future portfolio.
    """
    if len(a) != len(b):
        raise ValueError("paired return paths must have the same session count")
    integer(samples, "samples", 2, 100000)
    integer(block, "block", 1, 100000)
    integer(seed, "seed", 0, 2**32 - 1)
    difference = returns(a, initial_cash) - returns(b, initial_cash)
    block = min(block, len(difference))
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, len(difference), size=(samples, math.ceil(len(difference) / block)))
    indices = (starts[..., None] + np.arange(block)) % len(difference)
    means = difference[indices.reshape(samples, -1)[:, : len(difference)]].mean(axis=1)
    return {
        "method": "paired circular moving-block bootstrap; fixed paths; descriptive only",
        "metric": "mean_daily_excess_return",
        "estimate": float(difference.mean()),
        "lower_95": float(np.quantile(means, 0.025)),
        "upper_95": float(np.quantile(means, 0.975)),
        "block_sessions": block,
        "resamples": samples,
        "seed": seed,
        "selection_adjusted": False,
    }


def region_targets(data, spec, blocks):
    composite = np.full(data.close.shape, np.nan)
    fit_records = []
    for fold in blocks:
        cutoff = fold["train_end"]
        # Prefix data limits what the implementation can read at this fold.
        # Future test bars support sequential feature updates, never the fit.
        prefix = data.subset(fold["test_end"])
        target = generate_targets(prefix, spec, train_end=cutoff)
        lo, hi = fold["test_start"] - 1, fold["test_end"] - 1
        composite[lo:hi] = target[lo:hi]
        fit_records.append(
            {
                **fold,
                "strategy": spec.name,
                "latest_training_label_session_exclusive": cutoff,
                "first_decision_session": lo,
                "model": fit_diagnostics(prefix, spec, cutoff),
            }
        )
    return composite, fit_records


def evaluate_region(data, specs, research, execution, start, stop):
    blocks = folds(start, stop, research)
    result = {}
    for spec in specs:
        targets, fit_records = region_targets(data, spec, blocks)
        simulation = simulate(data, targets, execution, start=start, stop=stop)
        m = metrics(
            simulation.equity,
            simulation.initial_cash,
            total_fees=simulation.total_fees,
            total_notional=simulation.total_notional,
        )
        fold_metrics = []
        for fold in blocks:
            lo, hi = fold["test_start"] - start, fold["test_end"] - start
            capital = simulation.equity[lo - 1] if lo else simulation.initial_cash
            fills = [
                fill for fill in simulation.fills if fold["test_start"] <= fill["index"] < fold["test_end"]
            ]
            fees = math.fsum(fill["commission"] for fill in fills)
            notional = math.fsum(abs(fill["quantity"] * fill["price"]) for fill in fills)
            fold_metrics.append(
                {
                    **fold,
                    **metrics(simulation.equity[lo:hi], capital, total_fees=fees, total_notional=notional),
                }
            )
        result[spec.name] = {
            "spec": spec.to_dict(),
            "metrics": m,
            "folds": fold_metrics,
            "fit_records": fit_records,
            "simulation": simulation.to_dict(),
        }
    return result


def choose_candidate(results):
    """Zero-risk-free-rate Sharpe on development only, lexical tie break."""
    eligible = [(name, value) for name, value in results.items() if name != "equal"]
    if not eligible:
        raise ValueError("include at least one candidate besides the equal baseline")
    # Undefined Sharpe never becomes a spurious zero-risk winner.
    return min(
        eligible,
        key=lambda pair: (
            -(
                pair[1]["metrics"]["sharpe_zero_rf"]
                if pair[1]["metrics"]["sharpe_zero_rf"] is not None
                else -math.inf
            ),
            pair[0],
        ),
    )[0]


def stress_suite(data, winner, research, execution, start, stop):
    scenarios = {
        "double_cost": {
            "commission_bps": execution.commission_bps * 2,
            "spread_bps": execution.spread_bps * 2,
            "slippage_bps": execution.slippage_bps * 2,
        },
        "one_session_delay": {"delay_sessions": execution.delay_sessions + 1},
    }
    result = {}
    for name, changes in scenarios.items():
        try:
            config = replace(execution, **changes)
        except ValueError as error:
            result[name] = {
                "status": "unavailable",
                "reason": str(error),
                "requested_execution": {**execution.to_dict(), **changes},
            }
            continue
        run = evaluate_region(data, [winner], research, config, start, stop)[winner.name]
        result[name] = {"status": "complete", "execution": config.to_dict(), "metrics": run["metrics"]}
    return result


def baseline_spec():
    return StrategySpec("equal", "equal_weight", top_k=100)
