"""Synthetic E2 sibling table for tests and engineering checks (ENGINEERING_ONLY).

Generated from the T2 Gaussian model:
- each decision point draws Delta ~ N(mu0, tau^2) and Delta_hat = Delta + e;
- the 'continue' leaf is Delta * 1{Delta_hat > 0} + future;
- the 'verify' leaf is Delta * 1{Dbar > 0} - run_cost + future, with Dbar
  drawn under the 'vary' policy.
Here 'future' is shared noise per repetition (common random numbers across
siblings). Values are clipped to [-1, 1].
"""
from __future__ import annotations

import numpy as np

from r1.branch.schema import R1_BRANCH_SCHEMA, BranchRecord, Leaf
from r1.branch.table import SiblingTable, build_table


def synthetic_table(n_instances: int = 12, points_per_instance: int = 10, *, mu0: float = -0.004,
                    tau: float = 0.01, sigma_t: float = 0.005, sigma_s: float = 0.006, r: int = 2,
                    run_cost: float = 0.0005, reps: int = 2, seed: int = 0) -> SiblingTable:
    rng = np.random.default_rng(seed)
    sd = float(np.hypot(sigma_t, sigma_s))
    records = []
    for i in range(n_instances):
        for b in range(1, points_per_instance + 1):
            delta = rng.normal(mu0, tau)
            dhat = delta + rng.normal(0, sd)
            features = {"node": "synthetic", "delta_hat": float(dhat), "sigma_d": sd, "sigma_t": sigma_t,
                        "sigma_s": sigma_s, "remaining_runs": float(40 - b), "total_runs": 40.0,
                        "budget_index": float(b), "n_keeps": float(rng.integers(0, b)), "repeated_bad": 0.0,
                        "r": float(r)}
            mask = {"continue": True, "verify": True}
            future = rng.normal(0, 0.003, reps)
            cont, ver = [], []
            for k in range(reps):
                dbar = delta + rng.normal(0, sd / np.sqrt(r))
                cont.append(Leaf(k, "ok", float(np.clip(delta * (dhat > 0) + future[k], -1, 1)), 1))
                ver.append(Leaf(k, "ok", float(np.clip(delta * (dbar > 0) - run_cost + future[k], -1, 1)), 1 + 2 * r))
            common = dict(schema_version=R1_BRANCH_SCHEMA, instance_id=f"i{i:03d}", node="synthetic",
                          campaign_id="c0", epoch="E2", budget_index=b, split="engineering",
                          harness_commit="fixture", snapshot_hash=f"s{i}_{b}", manager_backend="fixture",
                          horizon=0, features=features, mask=mask)
            records.append(BranchRecord(action="continue", leaves=tuple(cont), **common))
            records.append(BranchRecord(action="verify", leaves=tuple(ver), **common))
    return build_table(records)
