"""Causal target proposals and a train-only, transparent ridge baseline.

Targets describe decisions at a session's close. The simulator owns fills at
later opens, fees, capacity and cash accounting. No strategy sees future labels.
"""

from __future__ import annotations

import numpy as np

from .data import MarketData
from .spec import StrategySpec

FEATURE_NAMES = (
    "return_1",
    "momentum_5",
    "momentum_lookback",
    "volatility_lookback",
    "close_to_mean",
    "overnight_return",
)
FEATURE_FORMULA = (
    "At close k: close[k]/close[k-1]-1; close[k]/close[k-5]-1; "
    "close[k]/close[k-L]-1; sample std of L trailing close returns; "
    "close[k]/mean(close[k-L:k+1])-1; open[k]/close[k-1]-1. "
    "One pooled model across assets; scaler and centered ridge fit on training examples only."
)


def _known_history(data: MarketData, t: int, lookback: int) -> bool:
    return bool(np.all(data.available_at[t - lookback : t + 1] <= data.close_time[t]))


def _returns(data: MarketData, t: int, lookback: int) -> np.ndarray:
    prices = data.close[t - lookback : t + 1]
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        returns = prices[1:] / prices[:-1] - 1
    if not np.all(np.isfinite(returns)):
        raise ValueError("price ratios exceed finite numeric range")
    return returns


def _features(data: MarketData, k: int, lookback: int) -> np.ndarray:
    """One feature row per asset using only bars through k."""
    returns = _returns(data, k, lookback)
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        values = np.column_stack(
            (
                returns[-1],
                data.close[k] / data.close[k - 5] - 1,
                data.close[k] / data.close[k - lookback] - 1,
                returns.std(axis=0, ddof=1),
                data.close[k] / data.close[k - lookback : k + 1].mean(axis=0) - 1,
                data.open[k] / data.close[k - 1] - 1,
            )
        )
    if not np.all(np.isfinite(values)):
        raise ValueError("features exceed finite numeric range")
    return values


def _fit(data: MarketData, spec: StrategySpec, train_end: int | None):
    if type(train_end) is not int or not spec.lookback + 3 <= train_end <= len(data.open_time):
        raise ValueError("ridge requires an exclusive train_end after its feature and label warmup")
    cutoff = data.close_time[train_end - 1]
    xs, ys, feature_indices, label_indices = [], [], [], []
    for k in range(spec.lookback, train_end - 2):
        if not _known_history(data, k, spec.lookback):
            continue
        # Complete source bars for both open prices must have arrived by fit time.
        if np.any(data.available_at[k + 1 : k + 3] > cutoff):
            continue
        x = _features(data, k, spec.lookback)
        with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
            y = data.open[k + 2] / data.open[k + 1] - 1
        if not np.all(np.isfinite(y)):
            raise ValueError("ridge labels exceed finite numeric range")
        xs.extend(x)
        ys.extend(y)
        feature_indices.extend([k] * len(data.assets))
        label_indices.extend([k + 2] * len(data.assets))
    if len(xs) < len(FEATURE_NAMES) + 2:
        raise ValueError("not enough available training examples for ridge (need at least eight)")
    x, y = np.asarray(xs), np.asarray(ys)
    mean, scale = x.mean(axis=0), x.std(axis=0)
    scale = np.where(scale > 1e-12, scale, 1.0)
    standardized = (x - mean) / scale
    intercept = float(y.mean())
    coefficients = np.linalg.solve(
        standardized.T @ standardized + spec.ridge_alpha * np.eye(x.shape[1]),
        standardized.T @ (y - intercept),
    )
    if not np.all(np.isfinite(coefficients)):
        raise ValueError("ridge fit produced non-finite coefficients")
    diagnostics = {
        "kind": "ridge",
        "train_end": train_end,
        "fit_cutoff": np.datetime_as_string(cutoff, unit="us") + "Z",
        "feature_formula": FEATURE_FORMULA,
        "feature_names": list(FEATURE_NAMES),
        "label_formula": "open[k+2]/open[k+1]-1; only k+2 < exclusive train_end",
        "sample_count": len(y),
        "training_feature_indices": feature_indices,
        "training_label_end_indices": label_indices,
        "feature_mean": mean.tolist(),
        "feature_scale": scale.tolist(),
        "coefficients": coefficients.tolist(),
        "intercept": intercept,
        "ridge_alpha": spec.ridge_alpha,
        "interpretation": "Regression estimates are uncalibrated research scores, not return guarantees.",
    }
    return mean, scale, coefficients, intercept, diagnostics


def fit_diagnostics(data: MarketData, spec: StrategySpec, train_end: int | None) -> dict:
    """Expose the exact train-only model state, feature formula and label endpoints."""
    if spec.kind != "ridge":
        return {"kind": spec.kind, "fitted": False}
    return _fit(data, spec, train_end)[-1]


def _risk_scale(weights: np.ndarray, returns: np.ndarray, target_vol: float) -> np.ndarray:
    sample = np.atleast_2d(np.cov(returns, rowvar=False, ddof=1))
    covariance = 0.8 * sample + 0.2 * np.diag(np.diag(sample))
    variance = float(weights @ covariance @ weights) * 252
    if not np.isfinite(variance):
        raise ValueError("estimated portfolio variance must be finite")
    volatility = np.sqrt(max(variance, 0.0))
    if volatility > target_vol:
        weights = weights * (target_vol / volatility)
    return weights


def generate_targets(data: MarketData, spec: StrategySpec, train_end: int | None = None) -> np.ndarray:
    """Long-only, capped targets; all-NaN means no new decision.

    Momentum selects the top-k positive trailing returns. Trend holds every
    asset with positive trailing momentum. Ridge uses the top-k positive model
    scores and emits no decisions before its exclusive training boundary.
    Volatility scaling only reduces the proposed exposure, leaving cash.
    """
    if not isinstance(data, MarketData) or not isinstance(spec, StrategySpec):
        raise ValueError("generate_targets requires MarketData and StrategySpec")
    t_count, asset_count = data.close.shape
    targets = np.full((t_count, asset_count), np.nan)
    fitted = _fit(data, spec, train_end) if spec.kind == "ridge" else None
    start = max(spec.lookback, train_end if spec.kind == "ridge" else spec.lookback)
    for t in range(start, t_count):
        if t % spec.rebalance_every or not _known_history(data, t, spec.lookback):
            continue
        returns = _returns(data, t, spec.lookback)
        if spec.kind == "equal_weight":
            selected = np.arange(asset_count)
        else:
            if spec.kind == "ridge":
                mean, scale, coefficients, intercept, _ = fitted
                scores = ((_features(data, t, spec.lookback) - mean) / scale) @ coefficients + intercept
            else:
                scores = data.close[t] / data.close[t - spec.lookback] - 1
            if not np.all(np.isfinite(scores)):
                raise ValueError("strategy scores must be finite")
            positive = np.flatnonzero(scores > 0)
            selected = (
                positive
                if spec.kind == "trend"
                else positive[np.argsort(-scores[positive], kind="stable")[: spec.top_k]]
            )
        weights = np.zeros(asset_count)
        if len(selected):
            weights[selected] = min(1 / len(selected), spec.max_weight)
            weights = _risk_scale(weights, returns, spec.target_vol)
        targets[t] = weights
    return targets
