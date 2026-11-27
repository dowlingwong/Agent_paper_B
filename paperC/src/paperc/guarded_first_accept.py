"""Fail-closed start measurement and ledger replay for Paper C measurement (b)."""

from __future__ import annotations

import math


def metric(value, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite metric")
    return float(value)


def run_guarded(*, measure_start, run_campaign, **campaign_kwargs):
    """Pass the start score through the harness's initial incumbent API once."""
    if "initial_current_best" in campaign_kwargs:
        raise ValueError("the initial incumbent metric must come from the start measurement")
    start = metric(measure_start(), "start")
    return start, run_campaign(initial_current_best=start, **campaign_kwargs)


def verify_keeps(rows: list[dict], start_metric: float) -> list[int]:
    """Verify every decision against the current incumbent, including trial one."""
    incumbent = metric(start_metric, "start")
    keeps = []
    for expected, row in enumerate(rows, 1):
        if row.get("budget_index") != expected:
            raise ValueError(f"expected trial index {expected}")
        if row.get("current_best_before") != incumbent:
            raise ValueError(f"trial {expected} was compared with another incumbent")
        value = (row.get("parsed_metrics") or {}).get("val_score")
        decision = row.get("decision")
        if decision in ("failed_invalid", "skipped"):
            continue
        value = metric(value, f"trial {expected}")
        if decision != ("kept" if value > incumbent else "discarded"):
            raise ValueError(f"trial {expected} violates strict improvement")
        if decision == "kept":
            keeps.append(expected)
            incumbent = value
    if not rows:
        raise ValueError("empty campaign ledger")
    return keeps
