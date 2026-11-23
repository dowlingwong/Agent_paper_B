#!/usr/bin/env python3
"""Power and compute of R1-SCREEN-MEASURE (tier E), from the pinned design and measured run times. No harness, no run.

AI-assisted (Claude, subagent, 23 Nov 2026). DRAFT; not signed; not reviewed.
Pre-declaration: ``docs/r1/authorizations/SCREEN_MEASURE_PREDECLARATION_DRAFT_20261123.md`` §7, §8.

``power``: for every testable node of the design, values are simulated for all of the node's configurations jointly at
the 120 seeds from e = mu + u + w: u shared by every configuration at a seed (share s), w with the product kernel over
the declared edits, K_w[a, b] = prod over edits in exactly one of a, b of r_w(e), r_w(e) = max(0, (rho_e - s)/(1 - s)),
rho_e the edit's E1 rho_joint (``screen_design``). Under s = 0 (the kernel of T4 Prop. 9 / T2 Prop. 4(a)) every design
triple has population partial 0. Each replicate is analysed by ``screen_analysis.node_test`` exactly as declared
(primary triples, exclusions, seed bootstrap B = 2,000, threshold 0.1). Scenarios per node: the kernel; the shares at
which the mean population partial of the node's primary triples is 0.10 (the threshold: the test's size there), 0.24
and 0.37 (the two effect sizes of R1-SCREEN-MEASURE's power figures, on the partial scale); the two reference shares
0.7082 and 0.7891 themselves; and the largest share consistent with the node's E1 correlations (s = min rho_e over
the edits of its primary triples; above it the model's marginal correlation of some edit exceeds its measured
rho_joint). Nodes are simulated independently (different data and models; the seeds coincide).

``compute``: the number of harness runs of the design and three measured per-run times: (A) the accepted E1 run of
22 Oct (aarch64 VM, 4 workers), (B) the D28 E1 runs of 27 Oct (deepthought, harness 6adf3859, about 16 concurrent
runs, no runtime probe), (C) the sweep-1 B.2 audit of 19 Nov (deepthought, 16 workers, a runtime probe per run, as
this runner makes), from its review. The deadline follows the sweep-2 B.2 addendum's rule max(10,800 s, 2.5 T).

Run: ``python -m r1.noise.screen_power power --out <json>``; ``python -m r1.noise.screen_power compute --out <json>``.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

from r1.harness import REPO
from r1.noise import screen_analysis as sa
from r1.noise import screen_design as sd

SCHEMA_POWER = "r1_screen_measure_power/v1"
SCHEMA_COMPUTE = "r1_screen_measure_compute/v1"
POWER_SEED = 20261124
POWER_NSIM = 400
TARGET_PARTIALS = (0.10, 0.24, 0.37)
RHO_CAP = 0.99999                     # keeps K_w positive definite when an E1 rho_joint rounds to 1


# ---------------------------------------------------------------------------------------------------- model

def lineage_covariance(design_node: dict, s: float) -> tuple[list[str], np.ndarray]:
    """Unit-variance covariance of the node's configurations: s J + (1 - s) K_w (see module docstring)."""
    ids = list(design_node["configs"])
    rw = [sd.link_coefficient(min(float(e["rho_joint"]), RHO_CAP), s) for e in design_node["edits"]]
    sets = [set(design_node["configs"][c]["edits"]) for c in ids]
    n = len(ids)
    K = np.ones((n, n))
    for a in range(n):
        for b in range(n):
            for e in sets[a] ^ sets[b]:
                K[a, b] *= rw[e - 1]
    return ids, s * np.ones((n, n)) + (1 - s) * K


def population_partials(design_node: dict, s: float) -> dict:
    """Population corr(c, g | p) of every primary triple under the model (exact, from the covariance)."""
    ids, cov = lineage_covariance(design_node, s)
    pos = {c: i for i, c in enumerate(ids)}
    out = {}
    for t in design_node["triples"]:
        if not t["primary"]:
            continue
        g, p, c = pos[t["g"]], pos[t["p"]], pos[t["c"]]
        gp, pc, gc = cov[g, p], cov[p, c], cov[g, c]
        out[t["id"]] = float((gc - gp * pc) / math.sqrt((1 - gp ** 2) * (1 - pc ** 2)))
    return out


def mean_population_partial(design_node: dict, s: float) -> float:
    vals = list(population_partials(design_node, s).values())
    return float(np.mean(vals)) if vals else float("nan")


def consistent_share(design_node: dict) -> float:
    edits = {t[k] for t in design_node["triples"] if t["primary"] for k in ("link_gp_edit", "link_pc_edit")}
    return min(float(design_node["edits"][e - 1]["rho_joint"]) for e in edits)


def solve_share(design_node: dict, target: float, grid: int = 9990) -> float | None:
    """The smallest share s on a 0.0001 grid in [0, 0.999] whose mean population partial reaches *target*."""
    for i in range(grid + 1):
        s = i / 10000
        if mean_population_partial(design_node, s) >= target:
            return s
    return None


def simulate(design_node: dict, s: float, rng, k: int = len(sd.SEED_BLOCK)) -> dict:
    ids, cov = lineage_covariance(design_node, s)
    L = np.linalg.cholesky(cov + 1e-12 * np.eye(len(ids)))
    e = L @ rng.normal(size=(len(ids), k))
    mu = rng.normal(0.9, 0.05, size=(len(ids), 1))           # true values differ; centring removes them
    x = mu + 0.01 * e
    return {c: x[i].tolist() for i, c in enumerate(ids)}


def power_node(design_node: dict, s: float, nsim: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    counts = {v: 0 for v in sa.VERDICTS}
    ests = []
    for i in range(nsim):
        res = sa.node_test(simulate(design_node, s, rng), design_node["triples"], seed=sa.BOOT_SEED + i)
        counts[res["verdict"]] += 1
        if res["estimate"] is not None:
            ests.append(res["estimate"])
    p = {f"p_{v.lower()}": counts[v] / nsim for v in sa.VERDICTS}
    se = {f"mc_se_{v.lower()}": math.sqrt(p[f"p_{v.lower()}"] * (1 - p[f"p_{v.lower()}"]) / nsim) for v in sa.VERDICTS}
    return {"s": s, "nsim": nsim, "rng_seed": seed, "mean_population_partial": mean_population_partial(design_node, s),
            "consistent_with_e1": s <= consistent_share(design_node) + 1e-12,
            "mean_estimate": float(np.mean(ests)) if ests else None,
            "sd_estimate": float(np.std(ests)) if ests else None, **p, **se}


def power(nsim: int = POWER_NSIM, repo: Path = REPO) -> dict:
    design = sd.build_design(repo)
    out = {"schema": SCHEMA_POWER, "label": "ENGINEERING_ONLY", "design_sha256": sd.design_sha256(design),
           "nsim": nsim, "n_boot": sa.N_BOOT, "seeds": len(sd.SEED_BLOCK), "threshold": sa.THRESHOLD,
           "power_seed": POWER_SEED, "nodes": {}, "not_testable": {}}
    for n in sd.T0_NODES:
        node = design["nodes"][n]
        if not node["testable"]:
            out["not_testable"][n] = "no primary triple in the design: NOT_TESTED with probability 1"
            continue
        scen = {"kernel s=0": 0.0}
        for tgt in TARGET_PARTIALS:
            s = solve_share(node, tgt)
            scen[f"mean population partial {tgt:.2f}"] = s
        for s in sd.REFERENCE_SHARES:
            scen[f"reference share s={s}"] = s
        scen["largest share consistent with E1"] = consistent_share(node)
        res = {}
        for j, (name, s) in enumerate(scen.items()):
            if s is None:
                res[name] = {"s": None, "note": "not reachable for s in [0, 0.999]"}
                continue
            t0 = time.time()
            res[name] = power_node(node, s, nsim, POWER_SEED + 1000 * sd.T0_NODES.index(n) + j)
            res[name]["seconds"] = round(time.time() - t0, 1)
            print(n, name, json.dumps({k: res[name][k] for k in ("s", "mean_population_partial", "p_shared",
                                                                  "p_no_shared", "p_inconclusive", "p_not_tested")}),
                  file=sys.stderr, flush=True)
        out["nodes"][n] = {"n_primary_triples": node["n_primary_triples"], "n_configs": node["n_configs"],
                           "consistent_share": consistent_share(node), "scenarios": res}
    # Decision level: P(at least one SHARED among the testable decision nodes), nodes independent.
    names = set.intersection(*(set(v["scenarios"]) for v in out["nodes"].values())) if out["nodes"] else set()
    out["decision_any_shared"] = {}
    for name in sorted(names):
        ps = [v["scenarios"][name].get("p_shared") for v in out["nodes"].values()]
        if all(p is not None for p in ps):
            out["decision_any_shared"][name] = 1 - float(np.prod([1 - p for p in ps]))
    return out


# ---------------------------------------------------------------------------------------------------- compute

E1_RUNS = {   # pinned by sha256 in the noise source's "sources" (D28_REPAIR summary) and checked here
    "A_e1_22oct_aarch64_4workers": ("results/r1/pilot/E1_20261022T214606Z/runs.jsonl",
                                    "03aa9ee1231a59f38422c58733e7f4ac059df7d2014076485d0f907a0c0d5a22"),
    "B_e1_d28_deepthought_16way": ("results/r1/pilot/E1_D28_REPAIR_20261027/runs.jsonl",
                                   "49018a9966b4255f88e8240c3a0a028edefe87fd8982890e988492d034d0e1c4"),
    "B_e1_d28_climate_deepthought_16way": ("results/r1/pilot/E1_D28_CLIMATE_20261027/runs.jsonl",
                                           "b75d5b32e31ec491bc960073508dcecce744d0d638f6a7f19cbd8f204dca34dd"),
}
# docs/r1/reviews/B2_AUDIT_RUN_REVIEW_20261119.md: "4,660 rows" (line 120), "wall_seconds sum 18,381.8 s" (line 125),
# "actual wall time 1,364 s" (lines 179-180); 16 workers (docs/r1/authorizations/c3_b2_addendum_20261117.md).
B2_AUDIT = {"runs": 4660, "wall_seconds_sum": 18381.8, "elapsed_seconds": 1364.0, "workers": 16,
            "source": "docs/r1/reviews/B2_AUDIT_RUN_REVIEW_20261119.md lines 120, 125, 179-180"}
WORKERS = 16
DEADLINE_FLOOR = 10800.0              # docs/r1/authorizations/c3_sweep2_b2_addendum_20261122.md: max(10,800 s, 2.5 T)


def _wall_by_node(rel: str, sha: str, repo: Path) -> dict:
    path = Path(repo) / rel
    if sd.sha256_file(path) != sha:
        raise sd.DesignError(f"STOP: {rel} differs from its pinned sha256")
    by = {}
    for line in path.read_text().splitlines():          # only node and wall_seconds are used
        if line.strip():
            r = json.loads(line)
            by.setdefault(r["node"], []).append(float(r["wall_seconds"]))
    return by


def compute(repo: Path = REPO) -> dict:
    design = sd.build_design(repo)
    runs = {n: v["n_configs"] * (len(sd.SEED_BLOCK) + 1) for n, v in design["nodes"].items()}
    total = sum(runs.values())
    smoke = sum(v["n_configs"] * 2 for v in design["nodes"].values())
    bases = {}
    a = _wall_by_node(*E1_RUNS["A_e1_22oct_aarch64_4workers"], repo)
    b = {**_wall_by_node(*E1_RUNS["B_e1_d28_deepthought_16way"], repo),
         **_wall_by_node(*E1_RUNS["B_e1_d28_climate_deepthought_16way"], repo)}
    for name, by in (("A_e1_22oct_aarch64", a), ("B_e1_d28_deepthought", b)):
        t0 = [n for n in sd.T0_NODES if n in by]
        pooled = float(np.mean([w for n in t0 for w in by[n]]))
        per = {n: (float(np.mean(by[n])) if n in by else pooled) for n in sd.T0_NODES}
        cpu = sum(runs[n] * per[n] for n in sd.T0_NODES)
        bases[name] = {"t0_nodes_measured": t0, "pooled_mean_wall_s": pooled,
                       "mean_wall_s_used": per, "cpu_seconds": cpu, "cpu_hours": cpu / 3600,
                       "elapsed_seconds_at_16_workers": cpu / WORKERS}
    per_run_c = B2_AUDIT["wall_seconds_sum"] / B2_AUDIT["runs"]
    rate_c = B2_AUDIT["runs"] / B2_AUDIT["elapsed_seconds"]
    bases["C_b2_audit_deepthought_with_probe"] = {
        "source": B2_AUDIT["source"], "mean_wall_s": per_run_c, "runs_per_second_at_16_workers": rate_c,
        "cpu_seconds": total * per_run_c, "cpu_hours": total * per_run_c / 3600,
        "elapsed_seconds_at_16_workers": total / rate_c}
    t_max = max(v["elapsed_seconds_at_16_workers"] for v in bases.values())
    return {"schema": SCHEMA_COMPUTE, "label": "ENGINEERING_ONLY", "design_sha256": sd.design_sha256(design),
            "harness_runs_per_node": runs, "harness_runs_total": total,
            "engineering_smoke_runs_seed_999": smoke, "workers": WORKERS, "bases": bases,
            "projection_T_seconds": t_max,
            "deadline_seconds": max(DEADLINE_FLOOR, 2.5 * t_max),
            "deadline_rule": "max(10,800 s, 2.5 T), T the largest of the three projections at 16 workers "
                             "(docs/r1/authorizations/c3_sweep2_b2_addendum_20261122.md)",
            "e1_runs_sha256": {k: v[1] for k, v in E1_RUNS.items()}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("power")
    p.add_argument("--out", required=True)
    p.add_argument("--nsim", type=int, default=POWER_NSIM)
    c = sub.add_parser("compute")
    c.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    res = power(args.nsim) if args.cmd == "power" else compute()
    res["command"] = "python -m r1.noise.screen_power " + " ".join(argv if argv is not None else sys.argv[1:])
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: res[k] for k in res if k in ("decision_any_shared", "harness_runs_total",
                                                       "projection_T_seconds", "deadline_seconds")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
