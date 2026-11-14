"""D8 eligibility alternatives (author, 14 Nov): dev z >= 6 vs (i) train+dev z vs (ii) a sigma_node threshold.

Synthetic Monte Carlo only; no label, table or seed of the project is read. AI-assisted (Claude).
Run in the harness uv.lock environment (NumPy 2.4.4, Python 3.13; author's D8-Q3b answer).

Model (declared; docs/r1/reports/M11_D8_ELIGIBILITY_ALTERNATIVES_20261114.md):

* per node, paired per-instance differences d = oracle - A2 with true mean mu and sd 1 (mu is in units of the
  per-instance sd); train, dev and test instances independent; normal or left-skewed d (as in
  d8_stop_probability_sim.py);
* layout: tier T0 = 8 nodes x 18 instances (RUNBOOK B.1/B.1b); tier T1 = 10 nodes x 12 instances (TRACK_G G.5,
  "about 12 campaigns per T1 node") or x 6 (each instance in both memory modes);
* a split assigns each node's instances to train / dev / test in fixed proportions (Q4 option (d));
* eligibility rules (delta_n assumed non-binding):
    R0  current gate:  dev z = mean / (sd(ddof 1) / sqrt(n_dev)) >= 6 on the dev instances;
    R1  (i):   the same paired z on train + dev instances (test untouched) >= z_min;
    R2  (ii):  a sigma_node threshold: z_sigma = mean * sqrt(n) / sigma_node >= c, with sigma_node the D21 noise floor
               taken as known (not estimated from the few instances); sigma_node = r x (per-instance sd of d), r a
               sensitivity (the ratio is not known yet); on dev only (R2-dev) or on train + dev (R2-trdev);
* an eligible node STOPs the gate if its point test mean or any of 2,000 bootstrap test means is <= 0 (as in
  r1/c3/gate.py); the gate also STOPs when no node is eligible;
* per-node probabilities are Monte Carlo estimates; scenario figures combine them exactly (nodes independent):
    P(STOP) = 1 - [prod_j (1 - e_j s_j) - prod_j (1 - e_j)],   excluded share = 1 - mean_j e_j,
    P(T1 kept) = 1 - prod_{j in T1} (1 - e_j)  (at least one T1 node in the IQM).
"""
from __future__ import annotations

import argparse
import json
import math
import sys

import numpy as np

SEED = 20261114
N_BOOT = 2000
SPLITS = {"P1 1/3:1/3:1/3": (1, 1, 1), "P2 1/2:1/6:1/3": (3, 1, 2)}   # train : dev : test
LAYOUTS = {"T1 x 12": {"T0": (8, 18), "T1": (10, 12)}, "T1 x 6": {"T0": (8, 18), "T1": (10, 6)}}
MUS = (0.25, 0.5, 1.0, 1.5, 2.0)
RULES = ("R0 dev z>=6", "R1 trdev z>=6", "R1 trdev z>=3", "R2-dev c=3 r=1", "R2-trdev c=3 r=1",
         "R2-trdev c=3 r=0.5", "R2-trdev c=3 r=2", "R2-trdev c=6 r=1")


def split_sizes(n: int, prop) -> tuple[int, int, int]:
    """Largest-remainder split of n instances in proportion ``prop`` (train, dev, test); test rounded first."""
    tot = sum(prop)
    test = round(n * prop[2] / tot)
    dev = round(n * prop[1] / tot)
    return n - dev - test, dev, test


def draw(rng, dist, mu, size):
    if dist == "normal":
        return mu + rng.standard_normal(size)
    if dist == "left_skewed":
        mean, sd = math.exp(0.5), math.sqrt((math.e - 1.0) * math.e)
        return mu - (rng.lognormal(0.0, 1.0, size) - mean) / sd
    raise ValueError(dist)


def eligible_prob(rng, dist, mu, rule, n_tr, n_dev, reps):
    if rule.startswith("R0"):
        n, kind, thr, r = n_dev, "t", 6.0, None
    elif rule.startswith("R1"):
        n, kind, thr, r = n_tr + n_dev, "t", float(rule.split(">=")[1]), None
    else:
        parts = dict(p.split("=") for p in rule.split()[1:])
        n = n_dev if rule.startswith("R2-dev") else n_tr + n_dev
        kind, thr, r = "sigma", float(parts["c"]), float(parts["r"])
    if n < 1 or (kind == "t" and n < 2):
        return 0.0
    d = draw(rng, dist, mu, (reps, n))
    m = d.mean(axis=1)
    if kind == "t":
        sd = d.std(axis=1, ddof=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            z = np.where(sd > 0, m / (sd / math.sqrt(n)), np.where(m > 0, np.inf, -np.inf))
    else:
        z = m * math.sqrt(n) / r
    return float(np.mean(z >= thr))


def test_stop_prob(rng, dist, mu, n_test, reps):
    if n_test < 1:
        return 1.0
    stops = 0
    for _ in range(reps):
        d = draw(rng, dist, mu, n_test)
        if not d.mean() > 0:
            stops += 1
            continue
        idx = rng.integers(0, n_test, size=(N_BOOT, n_test))
        if np.any(~(d[idx].mean(axis=1) > 0)):
            stops += 1
    return stops / reps


def run(reps_e, reps_s, dists=("normal", "left_skewed"), seed=SEED):
    rng = np.random.Generator(np.random.PCG64(seed))
    e_cache, s_cache = {}, {}

    def e(dist, mu, rule, n_tr, n_dev):
        k = (dist, mu, rule, n_tr, n_dev)
        if k not in e_cache:
            e_cache[k] = eligible_prob(rng, dist, mu, rule, n_tr, n_dev, reps_e)
        return e_cache[k]

    def s(dist, mu, n_test):
        k = (dist, mu, n_test)
        if k not in s_cache:
            s_cache[k] = test_stop_prob(rng, dist, mu, n_test, reps_s)
        return s_cache[k]

    rows = []
    for layout, tiers in LAYOUTS.items():
        for split, prop in SPLITS.items():
            sizes = {t: split_sizes(n, prop) for t, (_m, n) in tiers.items()}
            for dist in dists:
                for mu in MUS:
                    for rule in RULES:
                        nodes = []
                        for t, (m, _n) in tiers.items():
                            n_tr, n_dev, n_test = sizes[t]
                            nodes += [(t, e(dist, mu, rule, n_tr, n_dev), s(dist, mu, n_test))] * m
                        no_elig = math.prod(1 - ej for _, ej, _ in nodes)
                        reads = math.prod(1 - ej * sj for _, ej, sj in nodes) - no_elig
                        t1 = [ej for t, ej, _ in nodes if t == "T1"]
                        rows.append({"layout": layout, "split": split, "sizes": sizes, "dist": dist, "mu": mu,
                                     "rule": rule, "p_stop": 1 - reads, "p_no_eligible": no_elig,
                                     "excluded_share": 1 - sum(ej for _, ej, _ in nodes) / len(nodes),
                                     "excluded_share_T0": 1 - sum(ej for t, ej, _ in nodes if t == "T0") / 8,
                                     "excluded_share_T1": 1 - sum(t1) / len(t1),
                                     "p_t1_kept": 1 - math.prod(1 - ej for ej in t1)})
    per_node_e = {"|".join(map(str, k)): v for k, v in e_cache.items()}
    per_node_s = {"|".join(map(str, k)): v for k, v in s_cache.items()}
    return {"seed": seed, "reps_eligibility": reps_e, "reps_test_stop": reps_s, "n_boot": N_BOOT,
            "numpy": np.__version__, "python": sys.version.split()[0], "splits": SPLITS,
            "layouts": {k: {t: list(v) for t, v in d.items()} for k, d in LAYOUTS.items()},
            "per_node_eligibility": per_node_e, "per_node_test_stop": per_node_s, "scenarios": rows}


def markdown(res, dist="normal"):
    out = []
    for layout in LAYOUTS:
        for split in SPLITS:
            sub = [r for r in res["scenarios"] if r["layout"] == layout and r["split"] == split and r["dist"] == dist]
            if not sub:
                continue
            sz = sub[0]["sizes"]
            out += ["", f"**{dist}, {layout}, split {split}** — instances train/dev/test: "
                        f"T0 {'/'.join(map(str, sz['T0']))}, T1 {'/'.join(map(str, sz['T1']))}. "
                        "Cells: P(STOP) / excluded share (T0, T1) / P(T1 kept).", "",
                    "| rule | " + " | ".join(f"mu = {m:g}" for m in MUS) + " |", "|---" * (1 + len(MUS)) + "|"]
            for rule in RULES:
                cells = []
                for mu in MUS:
                    r = next(x for x in sub if x["rule"] == rule and x["mu"] == mu)
                    cells.append(f"{r['p_stop']:.2f} / {r['excluded_share_T0']:.2f}, {r['excluded_share_T1']:.2f} "
                                 f"/ {r['p_t1_kept']:.2f}")
                out.append(f"| {rule} | " + " | ".join(cells) + " |")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--reps-eligibility", type=int, default=20000)
    ap.add_argument("--reps-test-stop", type=int, default=2000)
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)
    res = run(a.reps_eligibility, a.reps_test_stop)
    for dist in ("normal", "left_skewed"):
        print(markdown(res, dist))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=1, sort_keys=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
