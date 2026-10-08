"""Allocation rules and conservative selection for Paper B.

Three objects are distinguished:

* :func:`batch_top_q` — batch allocation: choose the top-``q`` fraction of the
  *current* batch among feasible checkpoints using context scores only, with an
  exact count budget.
* :func:`streaming_threshold` — streaming deployment: a threshold fixed on
  development/calibration data; the achieved rate is reported and a budget
  overrun is an outcome, not a hidden correction.
* :class:`ConservativeSelector` — a small policy family with one explicitly
  allocated simultaneous error budget over the family's one-sided bounds.  The
  selected object is a *conservative selection with a one-sided bound*; it is
  not called a certificate, because no selection argument beyond the declared
  family and error allocation is provided here.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from causal_branch.control.bounds import hoeffding_radius


def batch_top_q(scores: np.ndarray, feasible: np.ndarray, q: float) -> np.ndarray:
    """Return the exact top-``q`` selection among feasible units.

    ``scores`` is the context-only score, ``feasible`` the pre-treatment mask,
    and ``q`` the capacity.  The count is ``ceil(q * n_feasible)``; ties are
    broken by index order for determinism.
    """

    if not 0.0 < q <= 1.0:
        raise ValueError("capacity q must lie in (0,1]")
    n_feasible = int(np.sum(feasible))
    k = int(np.ceil(q * n_feasible))
    selected = np.zeros(len(scores), dtype=bool)
    if k == 0:
        return selected
    order = np.argsort(-np.asarray(scores, dtype=float), kind="stable")
    chosen = [i for i in order if feasible[i]][:k]
    selected[chosen] = True
    return selected


def streaming_threshold(scores: np.ndarray, threshold: float, feasible: np.ndarray) -> np.ndarray:
    """Return the threshold selection; the achieved rate is reported, not fixed."""

    return (np.asarray(scores, dtype=float) > float(threshold)) & np.asarray(feasible, dtype=bool)


@dataclass
class ConservativeSelection:
    """Result of the small-family conservative selection."""

    chosen: str | None
    bounds: dict[str, float] = field(default_factory=dict)
    degradation_upper: dict[str, float] = field(default_factory=dict)
    family_size: int = 0
    delta: float = 0.05
    per_endpoint_delta: float = 0.0
    fallback: bool = False
    reason: str = ""


class ConservativeSelector:
    """One-sided selection over a small declared policy family.

    ``gain[policy]`` holds per-template mean gains for the family; the bound is
    a one-sided Hoeffding bound at level ``delta / endpoint_count`` (an explicit
    simultaneous allocation over the family).  A policy qualifies when its
    lower bound is strictly positive and its no-fault degradation upper bound
    is within ``harm_tolerance``.  Otherwise the selector falls back to
    continue.
    """

    def __init__(self, *, delta: float = 0.05, harm_tolerance: float = 0.02, gain_range: float = 2.0) -> None:
        if not 0.0 < delta < 1.0:
            raise ValueError("delta must lie in (0,1)")
        if not gain_range > 0.0:
            raise ValueError("gain_range must be the declared contrast width (default 2 for [-1,1])")
        self.delta = delta
        self.harm_tolerance = harm_tolerance
        self.gain_range = gain_range

    def select(
        self,
        gains: dict[str, np.ndarray],
        no_fault_degradation: dict[str, np.ndarray] | None = None,
    ) -> ConservativeSelection:
        family_size = max(1, len(gains))
        endpoint_count = family_size * (2 if no_fault_degradation is not None else 1)
        per_member_delta = self.delta / endpoint_count
        bounds: dict[str, float] = {}
        degradation_upper: dict[str, float] = {}
        for name, values in gains.items():
            values = np.asarray(values, dtype=float)
            if values.size == 0:
                bounds[name] = float("-inf")
                continue
            mean = float(np.mean(values))
            radius = hoeffding_radius(values.size, per_member_delta, width=self.gain_range)
            bounds[name] = mean - radius
            if no_fault_degradation is not None and name in no_fault_degradation:
                deg = np.asarray(no_fault_degradation[name], dtype=float)
                if deg.size:
                    dmean = float(np.mean(deg))
                    dr = hoeffding_radius(deg.size, per_member_delta, width=self.gain_range)
                    degradation_upper[name] = dmean + dr
        qualifying = {
            name: bound
            for name, bound in bounds.items()
            if bound > 0.0
            and (no_fault_degradation is None or
                 degradation_upper.get(name, float("inf")) <= self.harm_tolerance)
        }
        if not qualifying:
            return ConservativeSelection(
                chosen=None,
                bounds=bounds,
                degradation_upper=degradation_upper,
                family_size=family_size,
                delta=self.delta,
                per_endpoint_delta=per_member_delta,
                fallback=True,
                reason="no family member has a positive lower bound within the harm tolerance",
            )
        chosen = max(qualifying, key=lambda name: qualifying[name])
        return ConservativeSelection(
            chosen=chosen,
            bounds=bounds,
            degradation_upper=degradation_upper,
            family_size=family_size,
            delta=self.delta,
            per_endpoint_delta=per_member_delta,
            fallback=False,
            reason="selected by largest positive one-sided lower bound",
        )
