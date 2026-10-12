"""The sibling table: per decision point, the value and cost of each action.

Original-population rules (carried over from the old route, PLAN §8):
- every decision point stays in the population, whatever the action outcomes;
- if all leaves of an action failed, its value at that point is *undefined*;
  a policy that picks it there is counted as undefined, never imputed as zero;
- a policy that picks an infeasible action falls back to ``continue``, and the
  fallback is counted.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from r1.branch.schema import ACTIONS, BranchRecord, learner_projection, validate_sibling_sets

ACTION_ORDER = ("continue", "skip", "revise", "verify", "demote", "stop")


@dataclass
class SiblingTable:
    points: list[tuple]                          # decision points, sorted
    instances: np.ndarray                        # instance id per point (the cluster unit)
    value: np.ndarray                            # [n_points, n_actions] mean Y over ok leaves; nan if undefined
    leaf_values: list[dict[str, list[float]]]    # per point: action -> leaf Ys (for cross-fitting)
    cost: np.ndarray                             # [n_points, n_actions] mean worker runs
    feasible: np.ndarray                         # [n_points, n_actions] bool
    projections: list[dict]                      # learner-visible views
    actions: tuple[str, ...] = ACTION_ORDER
    meta: dict = field(default_factory=dict)

    def col(self, action: str) -> int:
        return self.actions.index(action)

    def __len__(self) -> int:
        return len(self.points)


def build_table(records: list[BranchRecord]) -> SiblingTable:
    groups = validate_sibling_sets(records)
    points = sorted(groups, key=lambda p: (p[0], p[1], p[2], p[3]))
    n, a = len(points), len(ACTION_ORDER)
    value = np.full((n, a), np.nan)
    cost = np.full((n, a), np.nan)
    feasible = np.zeros((n, a), dtype=bool)
    leaf_values, projections = [], []
    for i, point in enumerate(points):
        sibs = groups[point]
        for j, action in enumerate(ACTION_ORDER):
            feasible[i, j] = bool(sibs[0].mask.get(action, False))
        reps: dict[str, list[float]] = {}
        for record in sibs:
            if record.executed_action and record.executed_action != record.action:
                # the harness rejected the forced action; its leaves belong to another action (L14 finding 8)
                continue
            j = ACTION_ORDER.index(record.action)
            ok = [float(leaf.outcome_y) for leaf in record.leaves if leaf.integrity == "ok"]
            reps[record.action] = ok
            value[i, j] = float(np.mean(ok)) if ok else np.nan
            cost[i, j] = float(np.mean([leaf.cost_worker_runs for leaf in record.leaves]))
        # a feasible action that was never branched is treated as not observed (infeasible for evaluation)
        for j, action in enumerate(ACTION_ORDER):
            if action not in reps:
                feasible[i, j] = False
        leaf_values.append(reps)
        projections.append(learner_projection(sibs[0]))
    instances = np.array([p[0] for p in points])
    return SiblingTable(points, instances, value, leaf_values, cost, feasible, projections)


@dataclass
class PolicyValue:
    name: str
    value: float          # mean Y over defined decision points
    mean_cost: float      # mean worker runs of the chosen branches
    n_points: int
    n_undefined: int
    n_fallback: int
    action_counts: dict[str, int]


def choices_to_columns(table: SiblingTable, choices: list[str]) -> tuple[np.ndarray, int]:
    """Map policy choices to table columns; an infeasible choice falls back to ``continue``."""
    cols, fallback = [], 0
    cont = table.col("continue")
    for i, action in enumerate(choices):
        if action not in ACTIONS:
            raise ValueError(f"unknown action {action!r}")
        j = table.col(action)
        if not table.feasible[i, j]:
            fallback += 1
            j = cont
        cols.append(j)
    return np.array(cols, dtype=int), fallback


def evaluate_columns(table: SiblingTable, name: str, cols: np.ndarray, fallback: int = 0,
                     rows: np.ndarray | None = None) -> PolicyValue:
    rows = np.arange(len(table)) if rows is None else rows
    vals = table.value[rows, cols]
    costs = table.cost[rows, cols]
    defined = ~np.isnan(vals)
    counts: dict[str, int] = {}
    for j in cols:
        counts[table.actions[j]] = counts.get(table.actions[j], 0) + 1
    return PolicyValue(name, float(np.mean(vals[defined])) if defined.any() else float("nan"),
                       float(np.mean(costs[defined])) if defined.any() else float("nan"),
                       len(cols), int((~defined).sum()), fallback, counts)


def evaluate_choices(table: SiblingTable, name: str, choices: list[str]) -> PolicyValue:
    if len(choices) != len(table):
        raise ValueError("one choice per decision point")
    cols, fallback = choices_to_columns(table, choices)
    return evaluate_columns(table, name, cols, fallback)


def run_policy(table: SiblingTable, policy: Callable[[dict], str]) -> list[str]:
    """Run a policy on the learner projections only; it never sees table values."""
    return [policy(p) for p in table.projections]
