"""Score every E2 trigger arm on a sibling table with leave-one-instance-out cross-fitting.

For each held-out instance, every arm is fitted and its cutoff tuned on the
other instances only, then applied to the held-out instance.  Out-of-fold
choices from all folds are pooled and evaluated with the instance-cluster
bootstrap (shared draws).

Headroom (RUNBOOK 0.4b / 1.5) is bracketed by two oracles (L14 review, finding 3):
- ``oracle_naive`` picks the best action by the same leaves it is scored on. It
  is biased *upward* (the winner's curse), so its upper confidence bound is a
  conservative upper bound on the true oracle headroom;
- ``oracle_leafsplit`` picks on even-numbered leaves and scores on odd ones. It
  is unbiased for that noisy one-leaf rule but biased *downward* as an
  estimate of oracle headroom, strongly so with R = 2.
The true headroom lies in between, in expectation.  The best simple baseline is
selected in-sample and then held fixed in the bootstrap; the interval ignores
that selection.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from r1.baselines.policies import (
    AWRMLP, TUNING_BUDGET, KGIndex, RidgeAdvantage, design, score_always, score_heuristic, score_margin, score_rho,
)
from r1.branch.bootstrap import BootstrapResult, cluster_bootstrap
from r1.branch.matching import ArmDescriptor, matching_report
from r1.branch.table import SiblingTable

SIMPLE_ARMS = ("rho", "always_verify", "margin_threshold", "kg_index")
FIXED_ARMS = {"rho": math.inf, "always_verify": -math.inf}
E2_ACTIONS = ("continue", "verify")


def _cutoffs(scores: np.ndarray) -> np.ndarray:
    finite = scores[np.isfinite(scores)]
    qs = np.quantile(finite, np.linspace(0, 1, TUNING_BUDGET - 2)) if finite.size else np.array([])
    return np.unique(np.r_[-np.inf, qs, np.inf])[:TUNING_BUDGET]


def _apply(table: SiblingTable, rows: np.ndarray, scores: np.ndarray, c: float) -> np.ndarray:
    v, cont = table.col("verify"), table.col("continue")
    choose = (scores > c) & table.feasible[rows, v]
    return np.where(choose, v, cont)


def _value(table: SiblingTable, rows: np.ndarray, cols: np.ndarray) -> float:
    vals = table.value[rows, cols]
    vals = vals[~np.isnan(vals)]
    return float(vals.mean()) if vals.size else -math.inf


def _tune(table: SiblingTable, rows: np.ndarray, scores: np.ndarray) -> float:
    best_c, best_v = math.inf, -math.inf
    for c in _cutoffs(scores)[::-1]:  # ties go to the fewest interventions (largest cutoff first)
        v = _value(table, rows, _apply(table, rows, scores, c))
        if v > best_v + 1e-15:
            best_c, best_v = c, v
    return best_c


def _scores(arm: str, table: SiblingTable, train: np.ndarray, rows: np.ndarray, seed: int) -> np.ndarray:
    projs = table.projections
    if arm == "rho":
        return np.array([score_rho(projs[i]) for i in rows])
    if arm == "always_verify":
        return np.array([score_always(projs[i]) for i in rows])
    if arm == "margin_threshold":
        return np.array([score_margin(projs[i]) for i in rows])
    if arm == "harness_heuristic":
        return np.array([score_heuristic(projs[i]) for i in rows])
    if arm == "kg_index":
        kg = KGIndex().fit([projs[i] for i in train])
        return np.array([kg.score(projs[i]) for i in rows])
    v, c = table.col("verify"), table.col("continue")
    X = np.array([design(projs[i]) for i in train])
    Xr = np.array([design(projs[i]) for i in rows])
    if arm == "ridge_advantage":
        ok = ~np.isnan(table.value[train, v]) & ~np.isnan(table.value[train, c]) & table.feasible[train, v]
        if ok.sum() < 3:
            return np.full(len(rows), -np.inf)
        model = RidgeAdvantage().fit(X[ok], table.value[train, v][ok] - table.value[train, c][ok])
        return model.score(Xr)
    if arm == "awr_mlp":
        vals = table.value[train][:, [c, v]].copy()
        vals[:, 1] = np.where(table.feasible[train, v] & ~np.isnan(vals[:, 1]), vals[:, 1], -1.0)
        ok = ~np.isnan(vals[:, 0])
        if ok.sum() < 3:
            return np.full(len(rows), -np.inf)
        model = AWRMLP(seed=seed).fit(X[ok], vals[ok])
        return model.proba(Xr)[:, 1]
    raise ValueError(f"unknown arm {arm!r}")


@dataclass
class HeadroomReport:
    arms: list[str]
    choices: dict[str, np.ndarray]
    verify_rate: dict[str, float]
    boot: BootstrapResult
    headroom_naive: float
    headroom_leafsplit: float | None
    best_simple: str
    matching: dict


def oracle_columns(table: SiblingTable) -> tuple[np.ndarray, np.ndarray | None, np.ndarray | None]:
    """Naive oracle columns; leaf-split oracle columns and their held-out value matrix (None without 2+ leaves)."""
    cols = np.where(np.isnan(table.value), -np.inf, table.value)
    cols[~table.feasible] = -np.inf
    naive = cols.argmax(axis=1)
    n, a = table.value.shape
    choose = np.full((n, a), -np.inf)
    held = np.full((n, a), np.nan)
    have_all = True
    for i, reps in enumerate(table.leaf_values):
        for action, ys in reps.items():
            j = table.col(action)
            if len(ys) < 2:
                have_all = False
                continue
            if table.feasible[i, j]:
                choose[i, j] = float(np.mean(ys[0::2]))
                held[i, j] = float(np.mean(ys[1::2]))
    if not have_all:
        return naive, None, None
    return naive, choose.argmax(axis=1), held


def evaluate_arms(table: SiblingTable, *, arms: tuple[str, ...] = (
        "rho", "always_verify", "random_matched", "margin_threshold", "harness_heuristic", "kg_index",
        "ridge_advantage", "awr_mlp"), n_boot: int = 2000, seed: int = 20261012,
        info_set: str = "Z_e2_v1", dev_set: str = "loio") -> HeadroomReport:
    instances = sorted(set(table.instances.tolist()))
    if len(instances) < 2:
        raise ValueError("cross-fitting needs at least two instances")
    n = len(table)
    choices = {arm: np.full(n, table.col("continue")) for arm in arms if arm != "random_matched"}
    for k, inst in enumerate(instances):
        test = np.flatnonzero(table.instances == inst)
        train = np.flatnonzero(table.instances != inst)
        for arm in choices:
            if arm in FIXED_ARMS:  # fixed schedules are not tuned
                c = FIXED_ARMS[arm]
            else:
                c = _tune(table, train, _scores(arm, table, train, train, seed + k))
            choices[arm][test] = _apply(table, test, _scores(arm, table, train, test, seed + k), c)
    v = table.col("verify")
    rate = {arm: float(np.mean(cols == v)) for arm, cols in choices.items()}
    if "random_matched" in arms:
        rng = np.random.default_rng(seed)
        learned = [rate[a] for a in ("ridge_advantage", "awr_mlp", "kg_index", "margin_threshold") if a in rate]
        q = max(learned) if learned else 0.5  # matched to the most interventionist tuned arm (finding 12)
        pick = (rng.random(n) < q) & table.feasible[:, v]
        choices["random_matched"] = np.where(pick, v, table.col("continue"))
        rate["random_matched"] = float(np.mean(pick))
    naive, cf, held = oracle_columns(table)
    choices["oracle_naive"] = naive
    values = {}
    if cf is not None:
        choices["oracle_leafsplit"] = cf
        values["oracle_leafsplit"] = held
    simple = [a for a in SIMPLE_ARMS if a in choices]
    point = {a: _value(table, np.arange(n), choices[a]) for a in simple}
    best_simple = max(simple, key=lambda a: point[a])
    contrasts = [(a, "rho") for a in choices if a != "rho"] + [("oracle_naive", best_simple)]
    if cf is not None:
        contrasts.append(("oracle_leafsplit", best_simple))
    boot = cluster_bootstrap(table, choices, contrasts=contrasts, n_boot=n_boot, seed=seed, values=values)
    descriptors = [ArmDescriptor(a, a, info_set, "verify_iff_score_gt_c", None, None, None, TUNING_BUDGET, dev_set)
                   for a in arms if a not in ("rho", "always_verify", "random_matched")]
    report = matching_report(descriptors) if descriptors else {"matched": True}
    return HeadroomReport(list(choices), choices, rate, boot,
                          boot.contrasts[f"oracle_naive - {best_simple}"],
                          boot.contrasts.get(f"oracle_leafsplit - {best_simple}"), best_simple, report)
