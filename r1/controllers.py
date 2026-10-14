"""Harness controllers built from R1 arms (for deployment runs).

``IndexController`` deploys an E2 trigger arm (e.g. the KG-style index) inside
a live harness campaign. It reads only the harness ``ControlView`` (the
candidate's provisional metric, ``current_best`` and the budget) plus the
node's development constants, and it only ever chooses continue or verify.

``NoOpSkipController`` is the PLAN §5 doom-loop-skip arm (D27b): at E1 it
skips a proposal whose effective edited configuration equals the incumbent's
or one already evaluated.  Marked ``NOOP_SKIP_ARM_NOTE``: the E1b pilot table
records only E2 continue/verify, so this E1 arm cannot be scored offline until
E1 branch data exists.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from r1.harness import import_harness

import_harness()

from autoresearch.control_plane.controller import ControlDecision  # noqa: E402
from autoresearch.manager.hyperparam_edits import (  # noqa: E402
    build_effective_config,
    constants_after_edit,
)

NOOP_SKIP_ARM_NOTE = (
    "needs E1 branch data for offline scoring: the E1b sibling table records "
    "E2 continue/verify leaves only"
)


def _decision_value(record: object) -> str:
    decision = getattr(record, "decision", None)
    return str(getattr(decision, "value", decision))


def _freeze(config: dict) -> tuple:
    return tuple(sorted((str(k), str(v)) for k, v in config.items()))


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


@dataclass
class NoOpSkipController:
    """D27b E1 skip arm: skip a no-op or duplicate edit before its worker run.

    The controller is constructed with the start configuration's constants and
    tracks the incumbent's effective config across trials from the controller's
    own E1 decisions and the ledger prefix (kept trials apply their structured
    edit; skipped trials evaluate nothing).  If a kept trial's edit was not
    seen by this controller (e.g. a resumed campaign) the controller stops
    skipping, because the incumbent config is then unknown.
    """

    start_constants: dict
    version: str = "noop_skip/v1"
    deterministic: bool = True
    _constants: dict = field(init=False, repr=False)
    _effective: dict = field(init=False, repr=False)
    _seen: set = field(init=False, repr=False)
    _pending: dict = field(init=False, repr=False)
    _applied: set = field(init=False, repr=False)
    _unknown_keep: bool = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._constants = dict(self.start_constants)
        self._effective = build_effective_config(self._constants)
        self._seen = set()
        self._pending = {}
        self._applied = set()
        self._unknown_keep = False

    def decide(self, view, mask) -> ControlDecision:
        if view.epoch != "E1" or view.proposal is None:
            return ControlDecision("continue", {}, self.version, view.input_hash())
        self._advance(view.ledger_prefix)
        edit = (view.proposal.extra or {}).get("structured_edit")
        if not isinstance(edit, dict) or not edit.get("symbol"):
            return ControlDecision("continue", {}, self.version, view.input_hash())
        self._pending[view.budget_index] = dict(edit)
        if self._unknown_keep:
            return ControlDecision("continue", {}, self.version, view.input_hash())
        candidate = build_effective_config(
            constants_after_edit(self._constants, symbol=str(edit["symbol"]),
                                 new_value=str(edit.get("new", edit.get("new_value", ""))))
        )
        key = _freeze(candidate)
        equals_incumbent = key == _freeze(self._effective)
        seen_before = key in self._seen
        scores = {"config_equals_incumbent": float(equals_incumbent),
                  "config_seen_before": float(seen_before)}
        if mask.get("skip", False) and (equals_incumbent or seen_before):
            return ControlDecision("skip", scores, self.version, view.input_hash())
        return ControlDecision("continue", scores, self.version, view.input_hash())

    def _advance(self, ledger_prefix) -> None:
        for record in ledger_prefix:
            index = getattr(record, "budget_index", None)
            if index is None or index in self._applied:
                continue
            self._applied.add(index)
            edit = self._pending.get(index)
            if edit is None:
                if _decision_value(record) == "kept":
                    self._unknown_keep = True
                continue
            decision = _decision_value(record)
            if decision == "skipped":
                continue
            candidate_constants = constants_after_edit(
                self._constants, symbol=str(edit["symbol"]),
                new_value=str(edit.get("new", edit.get("new_value", "")))
            )
            self._seen.add(_freeze(build_effective_config(candidate_constants)))
            if decision == "kept":
                self._constants = candidate_constants
                self._effective = build_effective_config(candidate_constants)
