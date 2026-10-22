"""Execution evidence derived from recorded fills and events, never inferred orders."""

import math
from numbers import Integral, Real

from .ledger import ledger_diagnostics


def execution_diagnostics(simulation, assets):
    """Join evidence by global session index and measure explicit fill costs.

    ``adverse_fill_cost`` is signed quantity times (fill minus reference price).
    Adding commission measures recorded execution friction in currency, not the
    counterfactual portfolio return without costs. No signal targets/order book
    are reconstructed: absence of fills does not identify an idle strategy or rejection.
    Current engine intent records expose actual eligible deltas; older ledgers
    without intents remain supported with empty intent joins.
    Event ordinals and fill ordinals refer to the original, zero-based arrays.
    Ordinary signal delays count index differences; risk liquidation has no
    ordinary signal and is counted separately. Close NAV is an ex-post mark.
    """
    ledger = ledger_diagnostics(simulation, assets)
    rows = {}
    for marked in ledger["sessions"]:
        index = marked["index"]
        rows[index] = {
            "index": index,
            "fill_ordinals": [],
            "intent_ordinals": [],
            "intent_outcomes": {},
            "event_ordinals": [],
            "event_counts": {},
            "adverse_fill_cost": 0.0,
            "commission": marked["commission"],
            "normal_fill_delays_sessions": [],
            "risk_fill_count": 0,
        }
    for ordinal, event in enumerate(simulation["events"]):
        index = event["index"]
        if isinstance(index, bool) or not isinstance(index, Integral) or index not in rows:
            raise ValueError("event index is outside marked sessions")
        kind = event["type"]
        if not isinstance(kind, str) or not kind:
            raise ValueError("event type must be a nonempty string")
        row = rows[index]
        row["event_ordinals"].append(ordinal)
        row["event_counts"][kind] = row["event_counts"].get(kind, 0) + 1
    for ordinal, fill in enumerate(simulation["fills"]):
        row = rows[fill["index"]]
        reference = fill["reference_price"]
        if isinstance(reference, bool) or not isinstance(reference, Real):
            raise ValueError("fill reference price must be finite and positive")
        if not math.isfinite(reference) or reference <= 0:
            raise ValueError("fill reference price must be finite and positive")
        cost = float(fill["quantity"] * (fill["price"] - reference))
        if not math.isfinite(cost) or cost < 0:
            raise ValueError("fill must have finite nonnegative adverse execution cost")
        row["adverse_fill_cost"] += cost
        row["fill_ordinals"].append(ordinal)
        signal = fill["signal_index"]
        if signal is None:
            row["risk_fill_count"] += 1
        elif isinstance(signal, bool) or not isinstance(signal, Integral) or not 0 <= signal < fill["index"]:
            raise ValueError("ordinary fill signal must precede fill session")
        else:
            row["normal_fill_delays_sessions"].append(int(fill["index"] - signal))
    for ordinal, intent in enumerate(simulation.get("intents", [])):
        index = intent["index"]
        if isinstance(index, bool) or not isinstance(index, Integral) or index not in rows:
            raise ValueError("intent index is outside marked sessions")
        if intent["asset"] not in assets or intent["outcome"] not in {"filled", "partial", "blocked"}:
            raise ValueError("intent asset or outcome is invalid")
        row = rows[index]
        row["intent_ordinals"].append(ordinal)
        outcome = intent["outcome"]
        row["intent_outcomes"][outcome] = row["intent_outcomes"].get(outcome, 0) + 1
    sessions = list(rows.values())
    for row in sessions:
        row["explicit_execution_cost"] = row["adverse_fill_cost"] + row["commission"]
        if not math.isfinite(row["explicit_execution_cost"]):
            raise ValueError("execution cost overflows")
        row["evidence_status"] = (
            "recorded_fills_and_events"
            if row["fill_ordinals"] and row["event_ordinals"]
            else "recorded_fills"
            if row["fill_ordinals"]
            else "recorded_events"
            if row["event_ordinals"]
            else "no_recorded_execution_evidence"
        )
    totals = {
        key: math.fsum(row[key] for row in sessions)
        for key in ("adverse_fill_cost", "commission", "explicit_execution_cost")
    }
    totals["intent_count"] = len(simulation.get("intents", []))
    totals["fill_count"] = len(simulation["fills"])
    totals["event_count"] = len(simulation["events"])
    totals["risk_fill_count"] = sum(row["risk_fill_count"] for row in sessions)
    return {"sessions": sessions, "totals": totals}
