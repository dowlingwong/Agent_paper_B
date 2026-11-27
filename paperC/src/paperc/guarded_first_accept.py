"""Fail-closed start measurement and ledger replay for Paper C measurement (b)."""

from __future__ import annotations

import math
import json
from pathlib import Path

from r1.c3 import d3_analysis

INSTANCE_SEEDS = {"digits_mlp": tuple(range(62_000, 62_006)),
                  "tabular_mlp": tuple(range(62_006, 62_012))}
AUDIT_START = 10_901_000
MEASUREMENT_A_AUDITS = range(10_900_000, 10_900_720)


def check_reservations(registry_path: Path) -> dict:
    """Check the proposed reserve without treating it as author approval."""
    registry = json.loads(registry_path.read_text())
    proposed = set().union(*INSTANCE_SEEDS.values())
    audit_seeds = set(range(AUDIT_START, AUDIT_START + 10 * len(proposed)))
    used = set().union(*d3_analysis.declared_d3_seeds().values(), d3_analysis.sweep_instance_seed_universe(),
                       range(20010, 20802))
    for b in registry["paper_b"]:
        if any(b["lo"] <= s < b["hi"] for s in proposed | audit_seeds):
            raise ValueError(f"proposed seeds overlap {b['name']}")
    for b in registry["paper_c"]:
        if b["name"] not in ("paperc_audits", "paperc_guarded_first_instances") and any(
                b["lo"] <= s < b["hi"] for s in proposed | audit_seeds):
            raise ValueError(f"proposed seeds overlap {b['name']}")
    for bounds in d3_analysis.RESERVED_SEED_NAMESPACES.values():
        if bounds is not None and any(bounds[0] <= s <= bounds[1] for s in proposed | audit_seeds):
            raise ValueError("proposed seeds overlap a reserved D.3 namespace")
    block = next(b for b in registry["paper_c"] if b["name"] == "paperc_audits")
    if (proposed | audit_seeds) & used or audit_seeds.intersection(MEASUREMENT_A_AUDITS) or \
            not block["lo"] + 10 * 10_000 <= min(audit_seeds) <= max(audit_seeds) < block["hi"]:
        raise ValueError("proposed seeds overlap an audit or D.3 reservation")
    return {"proposed_instances": {node: list(seeds) for node, seeds in INSTANCE_SEEDS.items()},
            "audit_seed_range": [min(audit_seeds), max(audit_seeds)],
            "instance_extension_published": any(b["name"] == "paperc_guarded_first_instances"
                                               and b["lo"] == min(proposed) and b["hi"] == max(proposed) + 1
                                               for b in registry["paper_c"])}

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
