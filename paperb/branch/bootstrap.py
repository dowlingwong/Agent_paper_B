"""Cluster bootstrap with shared draws, and the Hoeffding radius (BUILD_RUNBOOK L9).

Ported from the legacy ``evaluate.py`` / ``bounds.py``.  The cluster is the
**instance** (PLAN §5): every decision point of one instance is drawn
together.  All policies share the same draws, so paired contrasts use the same
resample.  Undefined points are excluded per draw and counted, never imputed.

Scope: policies enter as fixed per-point choices.  A policy that is *fitted* on
the table must be cross-fitted by instance before it reaches this function
(``r1.baselines`` does that); refitting inside each draw is not done here.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from r1.branch.table import SiblingTable


@dataclass
class BootstrapResult:
    estimates: dict[str, float]
    ci: dict[str, tuple[float, float]]
    contrasts: dict[str, float]
    contrast_ci: dict[str, tuple[float, float]]
    n_instances: int
    n_points: int
    n_boot: int
    n_degenerate_draws: int


def _value(value: np.ndarray, cols: np.ndarray, rows: np.ndarray) -> float:
    vals = value[rows, cols[rows]]
    vals = vals[~np.isnan(vals)]
    return float(vals.mean()) if vals.size else float("nan")


def cluster_bootstrap(table: SiblingTable, policies: dict[str, np.ndarray], *,
                      contrasts: list[tuple[str, str]] = (), n_boot: int = 2000, seed: int = 20261012,
                      level: float = 0.95, values: dict[str, np.ndarray] | None = None) -> BootstrapResult:
    """``values`` optionally gives a policy its own value matrix (e.g. held-out leaves for a cross-fitted oracle)."""
    values = values or {}
    if not policies:
        raise ValueError("no policies")
    for name, cols in policies.items():
        if len(cols) != len(table):
            raise ValueError(f"policy {name!r} has {len(cols)} choices for {len(table)} points")
    for a, b in contrasts:
        if a not in policies or b not in policies:
            raise ValueError(f"contrast ({a}, {b}) names an unknown policy")
    if isinstance(n_boot, bool) or not isinstance(n_boot, int) or n_boot < 1:
        raise ValueError("n_boot must be a positive int")
    instances = sorted(set(table.instances.tolist()))
    index = {inst: np.flatnonzero(table.instances == inst) for inst in instances}
    all_rows = np.arange(len(table))
    vmat = {name: values.get(name, table.value) for name in policies}
    est = {name: _value(vmat[name], cols, all_rows) for name, cols in policies.items()}
    con = {f"{a} - {b}": est[a] - est[b] for a, b in contrasts}
    rng = np.random.default_rng(seed)
    draws = {name: [] for name in policies}
    cdraws = {f"{a} - {b}": [] for a, b in contrasts}
    degenerate = 0
    for _ in range(n_boot):
        picked = rng.choice(len(instances), size=len(instances), replace=True)
        rows = np.concatenate([index[instances[k]] for k in picked])
        vals = {name: _value(vmat[name], cols, rows) for name, cols in policies.items()}
        if any(math.isnan(v) for v in vals.values()):
            degenerate += 1
            continue
        for name, v in vals.items():
            draws[name].append(v)
        for a, b in contrasts:
            cdraws[f"{a} - {b}"].append(vals[a] - vals[b])
    lo, hi = 100 * (1 - level) / 2, 100 * (1 - (1 - level) / 2)

    def pct(x):
        return (float(np.percentile(x, lo)), float(np.percentile(x, hi))) if x else (float("nan"), float("nan"))

    return BootstrapResult(est, {k: pct(v) for k, v in draws.items()}, con, {k: pct(v) for k, v in cdraws.items()},
                           len(instances), len(table), n_boot, degenerate)


def hoeffding_radius(n: int, alpha: float, *, width: float = 2.0) -> float:
    """One-sided Hoeffding radius ``width * sqrt(log(1/alpha) / (2n))`` (outcome range width; Y in [-1, 1] -> 2)."""
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        raise ValueError("n must be a positive integer")
    if not 0.0 < float(alpha) < 1.0:
        raise ValueError("alpha must lie in (0,1)")
    if not width > 0.0:
        raise ValueError("width must be positive")
    return float(width) * math.sqrt(math.log(1.0 / float(alpha)) / (2.0 * n))
