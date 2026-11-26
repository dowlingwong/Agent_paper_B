#!/usr/bin/env python3
"""Post-hoc descriptions and power records for the screening test. ENGINEERING_ONLY; POST HOC; not pre-specified.

AI-assisted (Claude, subagent, 22 Nov 2026), written in the correction round after the independent review
``docs/r1/reviews/SCREENING_TEST_REVIEW_20261122.md`` (MINOR 2, 3, 5). Nothing here changes the pre-specified
statistic or decision of ``screening_test.py``; the splits below were chosen after the results were seen.

1. ``splits``: the primary Track S triples split by the p-c link correlation (< 0.95: p and c clearly differ;
   >= 0.95: near-duplicate link) and by whether the triple starts at c0.
2. ``power_report_call``: the exact call behind report §4.2's first power table (independent three-element lineages
   from a shared c0; shared members not modelled), re-run and recorded.
3. ``power_option_a``: the power of Option A with its real overlap: c0, the five E1 digits edits and the nine
   children c0 + e_i + e_j (distinct symbols), every triple (c0, c0 + e_i, c_ij) and (c0, c0 + e_j, c_ij), all on
   common seeds. The null needs both triples of a child to be screened at once, so w has the symbol-Hamming kernel
   corr(a, b) = r^d(a, b) (d = number of symbols at different levels), which makes every such partial zero; the
   alternative adds a shared component u: Sigma = s J + (1 - s) K_w, r = r_w(0.82, s).
Run: python -m r1.noise.screening_posthoc --out results/r1/engineering/screening_test_20261122/posthoc.json
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import numpy as np

from r1.harness import REPO
from r1.noise import screening_test as st

# digits_mlp E1 edits (results/r1/pilot/E1_20261022T214606Z/edits.json): (symbol, new level)
DIGITS_EDITS = (("LEARNING_RATE_INIT", "0.002"), ("MAX_ITER", "80"), ("HIDDEN_UNITS", "16"),
                ("HIDDEN_UNITS", "64"), ("BATCH_SIZE", "32"))


def splits() -> dict:
    out = {}
    for node, rel in st.TRACKS_DIRS.items():
        d = REPO / rel
        c0 = st.identify_c0(d)
        rows = []
        for inst, item in st.load_tracks(d, c0).items():
            for ch in item["chains"]:
                for i, j, k in st.chain_triples(len(ch)):
                    v, _ = st.triple_partial(ch[i], ch[j], ch[k])
                    if v is not None:
                        rows.append({"partial": v, "r_pc": st._corr(ch[j], ch[k]), "r_gp": st._corr(ch[i], ch[j]),
                                     "starts_at_c0": c0 is not None and i == 0})

        def grp(sel):
            vals = [r["partial"] for r in rows if sel(r)]
            return {"n": len(vals), "mean_partial": float(np.mean(vals)) if vals else None}

        out[node] = {"all": grp(lambda r: True),
                     "r_pc_lt_0.95": grp(lambda r: r["r_pc"] < 0.95),
                     "r_pc_ge_0.95": grp(lambda r: r["r_pc"] >= 0.95),
                     "starts_at_c0": grp(lambda r: r["starts_at_c0"]),
                     "later_incumbents_only": grp(lambda r: not r["starts_at_c0"])}
    return out


def option_a_configs():
    """c0, the singles and the children of distinct symbols, as {symbol: level} maps; triples as index tuples."""
    configs = [{}] + [{s: v} for s, v in DIGITS_EDITS]
    triples = []
    for a, b in itertools.combinations(range(len(DIGITS_EDITS)), 2):
        (sa, va), (sb, vb) = DIGITS_EDITS[a], DIGITS_EDITS[b]
        if sa == sb:
            continue
        configs.append({sa: va, sb: vb})
        child = len(configs) - 1
        triples += [(0, 1 + a, child), (0, 1 + b, child)]
    return configs, triples


def option_a_cov(configs, s: float, rho: float = st.POWER_RHO) -> np.ndarray:
    r = st.link_coefficient(rho, s)
    n = len(configs)
    K = np.empty((n, n))
    for x in range(n):
        for y in range(n):
            syms = set(configs[x]) | set(configs[y])
            d = sum(configs[x].get(z) != configs[y].get(z) for z in syms)
            K[x, y] = r ** d
    return s * np.ones((n, n)) + (1 - s) * K


def power_option_a(k: int, s: float, nsim: int = 200, n_boot: int = 500, seed: int = st.RNG_SEED) -> dict:
    configs, triples = option_a_configs()
    cov = option_a_cov(configs, s)
    L = np.linalg.cholesky(cov + 1e-12 * np.eye(len(configs)))
    rng = np.random.default_rng(seed + 11 + int(round(s * 1e4)))
    counts, ests = {"SHARED": 0, "NO_SHARED": 0, "INCONCLUSIVE": 0}, []
    for i in range(nsim):
        E = L @ rng.normal(size=(len(configs), k)) + rng.normal(0, 3, (len(configs), 1))
        tr = [(E[a], E[b], E[c]) for a, b, c in triples]
        vals = [v for v, _ in (st.triple_partial(*t) for t in tr) if v is not None]
        lo, hi = st.seed_bootstrap(tr, n_boot=n_boot, seed=seed + i)
        counts[st.decide(lo, hi)] += 1
        ests.append(float(np.mean(vals)) if vals else float("nan"))
    r = st.link_coefficient(st.POWER_RHO, s)
    return {"s": s, "k": k, "nsim": nsim, "n_boot": n_boot, "n_configs": len(configs), "n_triples": len(triples),
            "population_partial": st.shared_lineage_partial(s, r, r) if s < 1 else None,
            "mean_estimate": float(np.nanmean(ests)),
            **{"p_" + key.lower(): v / nsim for key, v in counts.items()}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    res = {"schema": "r1_screening_posthoc/v1", "label": st.LABEL, "post_hoc": True, "reviewed": False,
           "splits": splits(), "power_report_call": {}, "power_option_a": {}}
    for k in (60, 30):
        for name, s in st.POWER_SHARES.items():
            call = f"power_e1b([3]*18, {k}, {s}, nsim=100, n_boot=300)"
            res["power_report_call"][f"k={k} {name}"] = {"call": call,
                                                         **st.power_e1b([3] * 18, k, s, nsim=100, n_boot=300)}
            res["power_option_a"][f"k={k} {name}"] = power_option_a(k, s)
    Path(args.out).write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(json.dumps(res, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
