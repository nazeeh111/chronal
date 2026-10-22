"""Validated daily panels with explicit information availability and local fixtures."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import MappingProxyType

import numpy as np

CSV_COLUMNS = ("asset", "open_time", "close_time", "available_at", "open", "high", "low", "close", "volume")
_STAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})$")


def _readonly(values, dtype, *, temporal=False):
    source = np.asarray(values)
    if temporal:
        if source.dtype.kind != "M":
            raise ValueError("time arrays must contain NumPy datetime64 values normalized to UTC")
    elif source.dtype.kind not in "fiu":
        raise ValueError("OHLCV arrays must contain real numeric values")
    converted = np.array(source, dtype=dtype, order="C", copy=True)
    if temporal and not np.array_equal(source, converted.astype(source.dtype)):
        raise ValueError("timestamps must be exactly representable as UTC microseconds")
    # Immutable backing bytes also prevent callers from re-enabling write access.
    return np.frombuffer(converted.tobytes(), dtype=converted.dtype).reshape(converted.shape)


@dataclass(frozen=True)
class MarketData:
    """Synchronized unadjusted OHLCV data; timestamp arrays use UTC microseconds.

    A bar becomes observable only at ``available_at``. No filling, resampling,
    corporate-action adjustment or universe selection happens in this class.
    """

    assets: tuple[str, ...]
    open_time: np.ndarray
    close_time: np.ndarray
    available_at: np.ndarray
    open: np.ndarray
    high: np.ndarray
    low: np.ndarray
    close: np.ndarray
    volume: np.ndarray
    metadata: Mapping[str, str]

    def __post_init__(self):
        assets = tuple(self.assets)
        if not assets or any(
            not isinstance(a, str) or not 1 <= len(a) <= 64 or not a.isprintable() or not a.strip()
            for a in assets
        ):
            raise ValueError("assets must be nonempty printable strings of at most 64 characters")
        if len(set(assets)) != len(assets):
            raise ValueError("asset identifiers must be unique")
        object.__setattr__(self, "assets", assets)
        for name in ("open_time", "close_time", "available_at"):
            object.__setattr__(self, name, _readonly(getattr(self, name), "datetime64[us]", temporal=True))
        for name in ("open", "high", "low", "close", "volume"):
            object.__setattr__(self, name, _readonly(getattr(self, name), "<f8"))
        if self.open_time.ndim != 1 or self.open_time.size < 3:
            raise ValueError("at least three synchronized sessions are required")
        t, a = self.open_time.size, len(assets)
        if self.close_time.shape != (t,) or self.available_at.shape != (t, a):
            raise ValueError("time arrays must have shapes (sessions,) and (sessions, assets)")
        for name in ("open", "high", "low", "close", "volume"):
            values = getattr(self, name)
            if values.shape != (t, a) or not np.all(np.isfinite(values)):
                raise ValueError(f"{name} must be a finite (sessions, assets) array")
            invalid = np.any(values < 0) if name == "volume" else np.any(values <= 0)
            if invalid:
                raise ValueError(f"{name} contains invalid nonpositive prices or negative volume")
        if any(np.any(np.isnat(getattr(self, name))) for name in ("open_time", "close_time", "available_at")):
            raise ValueError("timestamps cannot be NaT")
        # CSV parsing and calendar diagnostics use ISO years supported by
        # Python's datetime. Reject wider NumPy years before locking a panel
        # that could not be read back from its own portable CSV export.
        for name in ("open_time", "close_time", "available_at"):
            stamps = getattr(self, name)
            if np.any(stamps < np.datetime64("0001-01-01", "us")) or np.any(
                stamps >= np.datetime64("10000-01-01", "us")
            ):
                raise ValueError("timestamps must use supported calendar years 0001 through 9999")
        if np.any(self.close_time <= self.open_time) or np.any(self.open_time[1:] <= self.close_time[:-1]):
            raise ValueError("sessions must increase strictly and cannot overlap")
        if np.any(self.available_at < self.close_time[:, None]):
            raise ValueError("a complete OHLCV bar cannot be available before its close")
        if (
            np.any(self.high < np.maximum(self.open, self.close))
            or np.any(self.low > np.minimum(self.open, self.close))
            or np.any(self.high < self.low)
        ):
            raise ValueError("OHLC high/low values are inconsistent")
        if not isinstance(self.metadata, Mapping) or any(
            not isinstance(k, str) or not isinstance(v, str) for k, v in self.metadata.items()
        ):
            raise ValueError("metadata must map strings to strings")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def fingerprint(self) -> str:
        """Stable semantic digest independent of CSV spelling or native byte order."""
        h = hashlib.sha256()
        h.update(
            json.dumps(
                {"schema": 1, "assets": self.assets, "metadata": dict(self.metadata)},
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode()
        )
        for name in ("open_time", "close_time", "available_at", "open", "high", "low", "close", "volume"):
            values = getattr(self, name)
            h.update(name.encode() + b"\0")
            h.update(json.dumps(values.shape).encode() + b"\0")
            if values.dtype.kind == "M":
                canonical = values.astype("datetime64[us]").astype("<i8")
            else:
                canonical = np.array(values, dtype="<f8", copy=True)
                canonical[canonical == 0] = 0.0  # normalize signed zero
            h.update(canonical.tobytes(order="C"))
        return h.hexdigest()

    def subset(self, stop: int) -> MarketData:
        if type(stop) is not int or not 3 <= stop <= len(self.open_time):
            raise ValueError("subset stop must retain between three and all sessions")
        return MarketData(
            self.assets,
            self.open_time[:stop],
            self.close_time[:stop],
            self.available_at[:stop],
            self.open[:stop],
            self.high[:stop],
            self.low[:stop],
            self.close[:stop],
            self.volume[:stop],
            dict(self.metadata),
        )


def _parse_timestamp(value: str) -> np.datetime64:
    if not isinstance(value, str) or not _STAMP.fullmatch(value):
        raise ValueError("timestamps require ISO 8601 seconds and an explicit UTC offset or Z")
    try:
        instant = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
        # NumPy datetime64 is timezone-free; normalize before removing the annotation.
        return np.datetime64(instant.replace(tzinfo=None), "us")
    except (ValueError, OverflowError) as error:
        raise ValueError(f"invalid timestamp: {value!r}") from error


def load_csv(path, metadata: Mapping[str, str] | None = None) -> MarketData:
    """Load an explicit rectangular panel; reject ambiguity instead of filling it."""
    records = {}
    assets = []
    session_closes = {}
    with Path(path).open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if (
            reader.fieldnames is None
            or len(reader.fieldnames) != len(CSV_COLUMNS)
            or set(reader.fieldnames) != set(CSV_COLUMNS)
        ):
            raise ValueError(f"CSV columns must be exactly {', '.join(CSV_COLUMNS)}")
        for line, row in enumerate(reader, 2):
            try:
                if None in row or any(v is None or v == "" for v in row.values()):
                    raise ValueError("missing or extra CSV fields")
                asset = row["asset"]
                opened = _parse_timestamp(row["open_time"])
                closed = _parse_timestamp(row["close_time"])
                available = _parse_timestamp(row["available_at"])
                key = (opened, asset)
                if key in records:
                    raise ValueError("duplicate asset/session row")
                if opened in session_closes and session_closes[opened] != closed:
                    raise ValueError("assets must share the same session close")
                session_closes[opened] = closed
                if asset not in assets:
                    assets.append(asset)
                records[key] = (available, *(float(row[name]) for name in CSV_COLUMNS[4:]))
            except (TypeError, ValueError, OverflowError) as error:
                raise ValueError(f"CSV row {line}: {error}") from error
    sessions = sorted(session_closes)
    if len(records) != len(sessions) * len(assets):
        raise ValueError("CSV must contain every asset in every session; no missing bars are filled")
    if not sessions or not assets:
        raise ValueError("CSV has no observations")
    panel = [[records[(t, a)] for a in assets] for t in sessions]
    available_at = np.array([[r[0] for r in day] for day in panel], dtype="datetime64[us]")
    values = [np.array([[r[j] for r in day] for day in panel], dtype=float) for j in range(1, 6)]
    return MarketData(
        tuple(assets),
        np.array(sessions, dtype="datetime64[us]"),
        np.array([session_closes[t] for t in sessions], dtype="datetime64[us]"),
        available_at,
        *values,
        dict(metadata or {}),
    )


def _format_time(value: np.datetime64) -> str:
    return np.datetime_as_string(value, unit="us") + "Z"


def write_csv(data: MarketData, path) -> None:
    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(CSV_COLUMNS)
        for t in range(len(data.open_time)):
            for j, asset in enumerate(data.assets):
                writer.writerow(
                    (
                        asset,
                        _format_time(data.open_time[t]),
                        _format_time(data.close_time[t]),
                        _format_time(data.available_at[t, j]),
                        *(repr(float(getattr(data, name)[t, j])) for name in CSV_COLUMNS[4:]),
                    )
                )


def make_demo(seed: int = 17, sessions: int = 756) -> MarketData:
    """Four fictional assets with correlated regimes, gaps and finite daily volume.

    This generator has no exchange-holiday calendar and its behavior does not
    imply attainable financial performance. Its RNG never changes global state.
    """
    if type(seed) is not int or seed < 0 or type(sessions) is not int or sessions < 3:
        raise ValueError("seed must be nonnegative and sessions must be an integer >= 3")
    rng = np.random.default_rng(seed)
    dates = []
    day = datetime(2018, 1, 2, 14, 30)
    while len(dates) < sessions:
        if day.weekday() < 5:
            dates.append(day)
        day += timedelta(days=1)
    opened = np.array(dates, dtype="datetime64[us]")
    closed = opened + np.timedelta64(390, "m")
    opens = np.empty((sessions, 4))
    closes = np.empty_like(opens)
    highs = np.empty_like(opens)
    lows = np.empty_like(opens)
    volumes = np.empty_like(opens)
    previous = np.array([70.0, 90.0, 110.0, 130.0])
    regime = 0
    drifts = np.array(
        [
            [0.0005, 0.0002, -0.0001, 0.0003],
            [-0.0008, 0.0001, 0.0004, -0.0005],
            [0.0002, -0.0002, 0.0001, 0.0006],
        ]
    )
    for t in range(sessions):
        if rng.random() < 1 / 65:
            regime = int(rng.integers(0, 3))
        shock = rng.normal(0, 0.007 if regime != 1 else 0.015)
        opens[t] = previous * np.exp(rng.normal(0, 0.003, 4))
        closes[t] = opens[t] * np.exp(drifts[regime] + shock + rng.normal(0, 0.008, 4))
        excursion = np.abs(rng.normal(0.005, 0.003, 4))
        highs[t] = np.maximum(opens[t], closes[t]) * (1 + excursion)
        lows[t] = np.minimum(opens[t], closes[t]) / (1 + excursion)
        volumes[t] = rng.lognormal(np.log(1_000_000), 0.4, size=4)
        previous = closes[t]
    metadata = {
        "source": "Chronal deterministic synthetic fixture",
        "synthetic": "true",
        "seed": str(seed),
        "universe": "fixed fictional assets; no membership selection or survivorship claim",
        "prices": "unadjusted synthetic prices; no corporate actions or dividends",
        "calendar": "weekday-only UTC sessions; no real exchange holiday calendar",
        "availability": "all complete bars available at their recorded close",
    }
    return MarketData(
        ("SYN_A", "SYN_B", "SYN_C", "SYN_D"),
        opened,
        closed,
        np.broadcast_to(closed[:, None], opens.shape),
        opens,
        highs,
        lows,
        closes,
        volumes,
        metadata,
    )
