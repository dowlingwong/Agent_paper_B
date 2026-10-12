"""Harness controllers built from R1 arms (for deployment runs).

``IndexController`` deploys an E2 trigger arm (e.g. the KG-style index) inside
a live harness campaign. It reads only the harness ``ControlView`` (the
candidate's provisional metric, ``current_best`` and the budget) plus the
node's development constants, and it only ever chooses continue or verify.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from r1.harness import import_harness

import_harness()

from autoresearch.control_plane.controller import ControlDecision  # noqa: E402


@dataclass
class IndexController:
    score: Callable[[dict], float]     # projection -> score (the same function scored offline)
    cutoff: float
    node: str
    noise: dict                        # sigma_d, sigma_t, sigma_s (development constants from E1)
    total_runs: int
    r: int = 2
    split_policy: str = "fixed"
    version: str = "index/v2"

    def decide(self, view, mask) -> ControlDecision:
        if view.epoch != "E2" or not mask.get("verify", False):
            return ControlDecision("continue", {}, self.version, view.input_hash())
        payload = view.canonical_payload()
        prov = payload.get("provisional") or {}
        metrics = prov.get("parsed_metrics") or {}
        metric_name = payload["node"]["metric_name"]
        if metric_name not in metrics or view.current_best is None:
            return ControlDecision("continue", {}, self.version, view.input_hash())
        remaining = view.budget.get("worker_runs_remaining")
        sign = -1.0 if payload["node"].get("metric_direction") == "minimize" else 1.0
        n_keeps = sum(1 for rec in payload.get("ledger_prefix") or [] if (rec or {}).get("decision") == "kept")
        proj = {"features": {"node": self.node,
                             "delta_hat": sign * (float(metrics[metric_name]) - float(view.current_best)),
                             "sigma_d": self.noise["sigma_d"], "sigma_t": self.noise["sigma_t"],
                             "sigma_s": self.noise["sigma_s"],
                             "remaining_runs": float(remaining if remaining is not None else 0),
                             "total_runs": float(self.total_runs), "budget_index": float(view.budget_index),
                             "n_keeps": float(n_keeps), "repeated_bad": 0.0, "r": float(self.r),
                             "split_policy": self.split_policy},
                "mask": dict(mask), "epoch": "E2"}
        s = float(self.score(proj))
        action = "verify" if s > self.cutoff else "continue"
        return ControlDecision(action, {"verify": s}, self.version, view.input_hash())
