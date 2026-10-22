"""Constrained strategy hypotheses are data, never executable model output."""

import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path


def integer(value, name, lower, upper):
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be an integer in [{lower}, {upper}]")


def number(value, name, lower, upper):
    if type(value) not in (int, float) or not math.isfinite(value) or not lower <= value <= upper:
        raise ValueError(f"{name} must be finite and in [{lower}, {upper}]")


@dataclass(frozen=True)
class StrategySpec:
    name: str
    kind: str
    lookback: int = 20
    top_k: int = 2
    rebalance_every: int = 5
    max_weight: float = 0.5
    target_vol: float = 0.12
    ridge_alpha: float = 10.0

    def __post_init__(self):
        if not isinstance(self.name, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", self.name):
            raise ValueError("name must be a lowercase slug of 1–64 characters")
        if self.kind not in ("equal_weight", "momentum", "trend", "ridge"):
            raise ValueError("kind must be equal_weight, momentum, trend or ridge")
        integer(self.lookback, "lookback", 5, 252)
        integer(self.top_k, "top_k", 1, 100)
        integer(self.rebalance_every, "rebalance_every", 1, 63)
        number(self.max_weight, "max_weight", 0.001, 1.0)
        number(self.target_vol, "target_vol", 0.001, 1.0)
        number(self.ridge_alpha, "ridge_alpha", 0.001, 1e6)

    def to_dict(self):
        return asdict(self)


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON field: {key}")
            result[key] = value
        return result

    def reject(value):
        raise ValueError(f"non-finite JSON constant: {value}")

    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError(f"non-finite JSON number: {value}")
        return number

    return json.loads(text, object_pairs_hook=pairs, parse_constant=reject, parse_float=finite_float)


def load_specs(path):
    raw = strict_json(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not 1 <= len(raw) <= 16:
        raise ValueError("supply a JSON list of 1–16 strategy specifications")
    specs = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("each strategy specification must be an object")
        try:
            specs.append(StrategySpec(**item))
        except TypeError as error:
            raise ValueError(f"invalid strategy fields: {error}") from error
    if len({spec.name for spec in specs}) != len(specs):
        raise ValueError("strategy names must be unique")
    return specs


def default_specs():
    return [
        StrategySpec("equal", "equal_weight", top_k=100),
        StrategySpec("momentum20", "momentum"),
        StrategySpec("momentum60", "momentum", lookback=60),
        StrategySpec("trend60", "trend", lookback=60, top_k=100),
        StrategySpec("ridge20", "ridge"),
    ]
