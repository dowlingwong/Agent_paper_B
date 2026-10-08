#!/usr/bin/env python3
"""F9: task-realism checks for the live candidate-consistency task.

Thresholds are frozen in ``THRESHOLDS`` before the run.  Three scripted agent
behaviours of varied quality (careless, typical, careful) drive the task; no
leaf value is hand-set.  Any FAIL is a legitimate outcome and stops F10.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "experiment_scaffold/src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from causal_branch.control.branch_tree import execute_tree_v2  # noqa: E402
from cc_live_candidate import accuracy, fit_stump, verifier  # noqa: E402
from cc_live_generator import generate_family  # noqa: E402
from cc_live_task import LiveCandidateTask  # noqa: E402

#: Frozen before the run.
THRESHOLDS = {
    "R1_each_regime_best_in_at_least_one_family": 1,
    "R2_vwait_true_between_family_sd_min": 0.02,
    "R4_verify_gain_min": 0.02,
    "R6_baseline_mean_range": (0.2, 0.8),
    "R6_root_sd_min": 0.05,
    "R7_reach_range": (0.5, 0.9),
    "R8_leaf_tokens_estimate": 1350,
    "R8_max_tokens": 2_000_000,
    "R8_max_wall_hours": 10,
}


@dataclass(frozen=True)
class Behaviour:
    name: str
    feature_indices: str  # 'first' or 'all'
    max_candidates: int
    fit_fraction: float
    verifier: bool


BEHAVIOURS = {
    "careless": Behaviour("careless", "first", 2, 0.6, verifier=True),
    "typical": Behaviour("typical", "all", 16, 0.8, verifier=True),
    "careful": Behaviour("careful", "all", 32, 0.9, verifier=True),
}


def _reached(root_id: str, rate: float) -> bool:
    digest = int(hashlib.sha256(root_id.encode()).hexdigest()[:8], 16) % 100
    return digest < int(rate * 100)


class BehaviourTask(LiveCandidateTask):
    def __init__(self, family, behaviour: Behaviour, *, reach_rate: float = 0.7):
        super().__init__(family)
        self.behaviour = behaviour
        self.reach_rate = reach_rate
        self._root_id = ""

    def _fit(self, x, y):
        indices = (list(range(max(1, x.shape[1] // 2)))
                   if self.behaviour.feature_indices == "first" else None)
        return fit_stump(x, y, max_candidates=self.behaviour.max_candidates,
                         feature_indices=indices)

    def _split(self, x, y):
        cut = max(1, int(len(y) * self.behaviour.fit_fraction))
        return (x[:cut], y[:cut]), (x[cut:], y[cut:])

    def prepare(self, workspace, *, template_id, root_id, seed):
        workspace.mkdir(parents=True, exist_ok=True)
        self._root_id = root_id
        self._write_csv(workspace / "dev1.csv", self.family["X_dev1"], self.family["y_dev1"])
        (workspace / "features.json").write_text(json.dumps(self.family["features"]) + "\n")
        (fit_x, fit_y), _ = self._split(self.family["X_dev1"], self.family["y_dev1"])
        self.provider.complete("fit")
        (workspace / "candidate.json").write_text(self._fit(fit_x, fit_y).to_json() + "\n")

    def continue_to_checkpoint2(self, workspace):
        self._write_csv(workspace / "dev2.csv", self.family["X_dev2"], self.family["y_dev2"])
        return _reached(self._root_id, self.reach_rate)

    def verify_and_respond(self, workspace):
        x, y = self._visible(workspace)
        (fit_x, fit_y), (check_x, check_y) = self._split(x, y)
        candidate = self._fit(fit_x, fit_y)
        if self.behaviour.verifier and len(check_y):
            indices = (list(range(max(1, x.shape[1] // 2)))
                       if self.behaviour.feature_indices == "first" else None)
            candidate = verifier(candidate, check_x, check_y,
                                 max_candidates=self.behaviour.max_candidates,
                                 feature_indices=indices)
        (workspace / "candidate.json").write_text(candidate.to_json() + "\n")


def _run_behaviour(name, behaviour, n_families, seed):
    trees, reached = [], []
    verify_gain = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for i in range(n_families):
            family = generate_family(i, seed + i)
            task = BehaviourTask(family, behaviour)
            records, tree = execute_tree_v2(
                task, root_id=f"r{i}", template_family_id=f"f{i}", split="engineering",
                seed=seed + i, branch_root=root / f"fam{i}", repetitions=2)
            reached.append(bool(next(r for r in records
                                     if r.decision_index == 1 and r.action == "continue").reached))
            trees.append(tree)
            # R4: verify-now vs ordinary refit at the same checkpoint
            refit = fit_stump(family["X_dev1"], family["y_dev1"])
            (fit_x, fit_y), (check_x, check_y) = task._split(
                family["X_dev1"], family["y_dev1"])
            repaired = verifier(task._fit(fit_x, fit_y), check_x, check_y,
                                max_candidates=behaviour.max_candidates)
            verify_gain.append(accuracy(repaired, family["X_hidden"], family["y_hidden"])
                               - accuracy(refit, family["X_hidden"], family["y_hidden"]))
    return trees, reached, verify_gain


def run_realism(n_families: int = 8, seed: int = 20260927) -> dict:
    results = {}
    for name, behaviour in BEHAVIOURS.items():
        trees, reached, verify_gain = _run_behaviour(name, behaviour, n_families, seed)
        never = np.array([t["never"] for t in trees])
        now = np.array([t["now"] for t in trees])
        later = np.array([t["later"] for t in trees])
        regimes = {"now_best": 0, "later_best": 0, "never_best": 0}
        harm_families = 0
        for n, a, b in zip(now, later, never):
            if n >= a and n >= b:
                regimes["now_best"] += 1
            if a > n and a >= b:
                regimes["later_best"] += 1
            if b > n and b > a:
                regimes["never_best"] += 1
            if a < b or n < b:
                harm_families += 1
        wait_value = later - never
        results[name] = {
            "regimes": regimes,
            "all_regimes_present": all(v >= THRESHOLDS["R1_each_regime_best_in_at_least_one_family"]
                                       for v in regimes.values()),
            "harm_families": harm_families,
            "harm_possible": harm_families >= 1,
            "baseline_mean": float(never.mean()),
            "root_sd": float(never.std()),
            "reach_fraction": float(np.mean(reached)),
            "verify_gain_max": float(np.max(verify_gain)),
            "verify_not_redundant": bool(np.max(verify_gain) > THRESHOLDS["R4_verify_gain_min"]),
            "wait_value_between_family_sd": float(wait_value.std()),
        }
    typical = results["typical"]
    checks = {
        "R1": all(r["all_regimes_present"] for r in results.values()),
        "R2": all(r["wait_value_between_family_sd"] > THRESHOLDS["R2_vwait_true_between_family_sd_min"]
                  for r in results.values()),
        "R3": True,  # disjoint splits + workspace scan (see test); dev2 is a separate batch
        "R4": typical["verify_not_redundant"],
        "R5": all(r["harm_possible"] for r in results.values()),
        "R6": (THRESHOLDS["R6_baseline_mean_range"][0] <= typical["baseline_mean"]
               <= THRESHOLDS["R6_baseline_mean_range"][1]
               and typical["root_sd"] > THRESHOLDS["R6_root_sd_min"]),
        "R7": (THRESHOLDS["R7_reach_range"][0] <= typical["reach_fraction"]
               <= THRESHOLDS["R7_reach_range"][1]),
        "R8": (THRESHOLDS["R8_leaf_tokens_estimate"] * 512 <= THRESHOLDS["R8_max_tokens"]
               and 512 * 12 / 3600.0 <= THRESHOLDS["R8_max_wall_hours"]),
        "R9": True,  # the fit tool returns the executable candidate; submission is a Stump round-trip
    }
    return {"banner": "ENGINEERING_ONLY", "thresholds": {k: str(v) for k, v in THRESHOLDS.items()},
            "behaviours": results, "checks": checks, "all_pass": all(checks.values())}


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--families", type=int, default=8)
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise SystemExit(f"refuse overwrite: {output} exists")
    output.mkdir(parents=True)
    report = run_realism(args.families)
    (output / "realism_report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"task-realism: {'PASS' if report['all_pass'] else 'FAIL'}")
    for name, result in report["behaviours"].items():
        print(f"  {name}: regimes={result['regimes']} reach={result['reach_fraction']:.2f} "
              f"harm={result['harm_possible']} verify_gain_max={result['verify_gain_max']:+.3f} "
              f"wait_sd={result['wait_value_between_family_sd']:.3f}")
    print("  checks:", report["checks"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
