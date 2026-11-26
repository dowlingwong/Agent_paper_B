"""D8-PASS (author, 16 Nov): search for a pass rule calibrated under every D8-SKEW scenario, with V1n, train+dev
z >= 3 and split P3 (R1-BX-D8-V3-A items 1-3).

Synthetic Monte Carlo only; no label, table or seed of the project is read. AI-assisted (Claude). Model, candidates,
metrics and the decision rule are declared in docs/r1/proposals/M11_D8_PASS_DECLARATION_20261116.md (committed before
this script). The generator helpers are imported from d8_skew_sim.py; the per-node draw order is the same.

Candidates (each with the gate's PoI conjunct):
  b2   studentized bootstrap lower bound of the gap-closed IQM (D8-SKEW's b2, unchanged);
  c    node-equal mean of a, Welch-Satterthwaite Student-t (D8-SKEW's c, unchanged);
  c1   node-equal mean of a, node-stratified bootstrap-t;            (c')
  cJ   node-equal mean of a, Johnson's skewness-corrected t;         (c''J)
  cSR  stratified Wilcoxon signed-rank, van Elteren weights.         (c''SR)
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from multiprocessing import Pool

import numpy as np
from scipy import stats

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from d8_skew_sim import BIG, LEVEL, N_BOOT, NEG, ZMIN, iqm_sorted, iqm_weights, lower, noise, split_sizes  # noqa: E402

SEED = 20261118
SPLIT = ("P3 1/3:1/6:1/2", (2, 1, 3))
LAYOUTS = {"T1 x 12": {"T0": (8, 18), "T1": (10, 12)}, "T1 x 6": {"T0": (8, 18), "T1": (10, 6)}}
PRIMARY, SECONDARY = "T1 x 12", "T1 x 6"
MUS = (0.5, 1.0, 1.5, 2.0)
GS = (0.0, 0.3)
RULES = ("b2", "c", "c1", "cJ", "cSR")
LABEL = {"b2": "(b2) studentized IQM", "c": "(c) stratified t", "c1": "(c') stratified bootstrap-t",
         "cJ": "(c''J) Johnson t", "cSR": "(c''SR) stratified signed-rank"}
CONDITIONS = [("normal", "hom"), ("normal", "het"), ("left_skewed", "hom"), ("left_skewed", "het"),
              ("t3", "hom"), ("t3", "het")]
THRESH_ARM, THRESH_TWO, TIE = 0.035, 0.065, 0.02
Z975 = float(stats.norm.ppf(LEVEL))


def node_se(av, dv, Gv):
    n = av.shape[-1]
    va = av.var(axis=-1, ddof=1)
    vd = dv.var(axis=-1, ddof=1)
    cv = ((av - av.mean(axis=-1, keepdims=True)) * (dv - dv.mean(axis=-1, keepdims=True))).sum(axis=-1) / (n - 1)
    num = np.maximum(va + Gv ** 2 * vd - 2 * Gv * cv, 0.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.sqrt(num / (n * dv.mean(axis=-1) ** 2))


def rule_b2(elig, arm, w, dmean, d_b, bad):
    amean = np.array([x["a"][arm].mean() for x in elig])
    a_b = np.stack([x["a"][arm][x["idx"]].mean(axis=1) for x in elig], axis=1)
    G = amean / dmean
    theta = float(iqm_sorted(G, w))
    with np.errstate(divide="ignore", invalid="ignore"):
        G_b = np.where(bad, NEG, a_b / d_b)
    iq_b = iqm_sorted(G_b, w)
    se_pt = np.array([node_se(x["a"][arm], x["d"], G[j]) for j, x in enumerate(elig)])
    se_hat = float(np.sqrt(np.sum((w * se_pt[np.argsort(G)]) ** 2)))
    se_b = np.empty_like(G_b)
    for j, x in enumerate(elig):
        ab, db = x["a"][arm][x["idx"]], x["d"][x["idx"]]
        with np.errstate(divide="ignore", invalid="ignore"):
            gb = np.where(db.mean(axis=1) > 0, ab.mean(axis=1) / db.mean(axis=1), 0.0)
        se_b[:, j] = node_se(ab, db, gb)
    se_iq_b = np.sqrt(np.sum((w * np.take_along_axis(se_b, np.argsort(G_b, axis=1), axis=1)) ** 2, axis=1))
    with np.errstate(divide="ignore", invalid="ignore"):
        tstar = (iq_b - theta) / se_iq_b
    tstar = np.where(bad.any(axis=1) | ~(se_iq_b > 0) | ~np.isfinite(tstar), BIG, tstar)
    qt = float(np.quantile(tstar, LEVEL, method="linear"))
    return (theta - qt * se_hat) > 0 if se_hat > 0 else theta > 0


def numerator_rules(elig, arm):
    k = len(elig)
    vals = [x["a"][arm] for x in elig]
    n_j = np.array([len(v) for v in vals], float)
    means = np.array([v.mean() for v in vals])
    s2 = np.array([v.var(ddof=1) for v in vals])
    theta = float(means.mean())
    var_terms = s2 / (k ** 2 * n_j)
    se = math.sqrt(float(var_terms.sum()))
    out = {}
    if se > 0:
        df = float(var_terms.sum() ** 2 / np.sum(var_terms ** 2 / (n_j - 1)))
        tq = float(stats.t.ppf(LEVEL, df))
        out["c"] = theta - tq * se > 0
        # (c'') Johnson: stratified third cumulant of theta-hat
        m3 = np.array([len(v) * np.sum((v - v.mean()) ** 3) / ((len(v) - 1) * (len(v) - 2)) for v in vals])
        kappa3 = float(np.sum(m3 / (k ** 3 * n_j ** 2)))
        gamma = kappa3 / se ** 3
        T = theta / se
        out["cJ"] = (T + gamma / 6.0 + gamma * T * T / 3.0) > tq
    else:
        out["c"] = out["cJ"] = theta > 0
    # (c') bootstrap-t, same resample indices
    mb = np.stack([v[x["idx"]].mean(axis=1) for v, x in zip(vals, elig)], axis=1)          # (B, k)
    vb = np.stack([v[x["idx"]].var(axis=1, ddof=1) for v, x in zip(vals, elig)], axis=1)
    th_b = mb.mean(axis=1)
    se_b = np.sqrt(np.sum(vb / (k ** 2 * n_j), axis=1))
    with np.errstate(divide="ignore", invalid="ignore"):
        tstar = (th_b - theta) / se_b
    tstar = np.where(~(se_b > 0) | ~np.isfinite(tstar), BIG, tstar)
    if se > 0:
        out["c1"] = theta - float(np.quantile(tstar, LEVEL, method="linear")) * se > 0
    else:
        out["c1"] = theta > 0
    # (c''SR) stratified signed-rank, van Elteren weights
    num = den = 0.0
    for v in vals:
        n = len(v)
        r = stats.rankdata(np.abs(v))
        W = float(np.sum(np.sign(v) * r))
        num += W / (n + 1)
        den += n * (n + 1) * (2 * n + 1) / 6.0 / (n + 1) ** 2
    out["cSR"] = (num / math.sqrt(den)) > Z975 if den > 0 else False
    return out


def one_rep(rng, dist, het, mu, g, tiers, sizes):
    nodes = []
    for t, (m, _n) in tiers.items():
        n_tr, n_dev, n_te = sizes[t]
        for _ in range(m):
            mu_j = mu * (rng.uniform(0.5, 1.5) if het == "het" else 1.0)
            dtd = mu_j + noise(rng, dist, n_tr + n_dev)
            sd = dtd.std(ddof=1)
            z = dtd.mean() / (sd / math.sqrt(len(dtd))) if sd > 0 else (math.inf if dtd.mean() > 0 else -math.inf)
            d = mu_j + noise(rng, dist, n_te)
            c = noise(rng, dist, n_te)
            a = [g * mu_j + math.sqrt(0.5) * c + math.sqrt(0.5) * noise(rng, dist, n_te) for _ in range(2)]
            idx = rng.integers(0, n_te, size=(N_BOOT, n_te))
            nodes.append({"tier": t, "elig": z >= ZMIN, "d": d, "a": a, "idx": idx})
    out = {r: {"status": None, "pass": [False, False], "prim": [False, False]} for r in RULES}
    elig = [x for x in nodes if x["elig"]]
    if not elig:
        for r in RULES:
            out[r]["status"] = "no_eligible"
        return out
    dmean = np.array([x["d"].mean() for x in elig])
    if np.any(dmean <= 0):
        for r in RULES:
            out[r]["status"] = "stop"
        return out
    for r in RULES:
        out[r]["status"] = "read"
    w = iqm_weights(len(elig))
    d_b = np.stack([x["d"][x["idx"]].mean(axis=1) for x in elig], axis=1)
    bad = d_b <= 0
    for arm in range(2):
        poi = lower(np.mean([(x["a"][arm][x["idx"]] > 0).mean(axis=1) for x in nodes], axis=0)) > 0.5
        prim = numerator_rules(elig, arm)
        prim["b2"] = rule_b2(elig, arm, w, dmean, d_b, bad)
        for r in RULES:
            out[r]["prim"][arm] = bool(prim[r])
            out[r]["pass"][arm] = bool(prim[r] and poi)
    return out


def run_condition(args):
    ci, dist, het, reps = args
    rng = np.random.Generator(np.random.PCG64(SEED + ci))
    rows = []
    for layout, tiers in LAYOUTS.items():
        sizes = {t: split_sizes(n, SPLIT[1]) for t, (_m, n) in tiers.items()}
        for mu in MUS:
            for g in GS:
                acc = {r: {"no_eligible": 0, "stop": 0, "read": 0, "arm1": 0, "any": 0, "prim_arm1": 0, "prim_any": 0}
                       for r in RULES}
                for _ in range(reps):
                    o = one_rep(rng, dist, het, mu, g, tiers, sizes)
                    for r in RULES:
                        x = o[r]
                        acc[r][x["status"]] += 1
                        acc[r]["arm1"] += x["pass"][0]
                        acc[r]["any"] += x["pass"][0] or x["pass"][1]
                        acc[r]["prim_arm1"] += x["prim"][0]
                        acc[r]["prim_any"] += x["prim"][0] or x["prim"][1]
                for r in RULES:
                    a = acc[r]
                    rows.append({"dist": dist, "mu_structure": het, "layout": layout, "split": SPLIT[0],
                                 "sizes": sizes, "mu": mu, "g": g, "rule": r, "reps": reps,
                                 "p_no_eligible": a["no_eligible"] / reps, "p_test_stop": a["stop"] / reps,
                                 "p_pass_arm": a["arm1"] / reps, "p_pass_two_arm": a["any"] / reps,
                                 "p_primary_arm": a["prim_arm1"] / reps, "p_primary_two_arm": a["prim_any"] / reps})
    return rows


def evaluate(rows):
    """The declared decision rule (declaration section 4)."""
    res = {}
    for r in RULES:
        info = {}
        for layout in (PRIMARY, SECONDARY):
            null = [x for x in rows if x["rule"] == r and x["layout"] == layout and x["g"] == 0.0]
            exc = [{"dist": x["dist"], "mu_structure": x["mu_structure"], "mu": x["mu"], "arm": x["p_pass_arm"],
                    "two_arm": x["p_pass_two_arm"]} for x in null if x["p_pass_arm"] > THRESH_ARM]
            two = [{"dist": x["dist"], "mu_structure": x["mu_structure"], "mu": x["mu"], "two_arm": x["p_pass_two_arm"]}
                   for x in null if x["p_pass_two_arm"] > THRESH_TWO]
            info[layout] = {"calibrated": not exc, "exceedances": exc, "two_arm_flags": two,
                            "max_arm": max(x["p_pass_arm"] for x in null),
                            "max_two_arm": max(x["p_pass_two_arm"] for x in null)}
        pw = [x for x in rows if x["rule"] == r and x["layout"] == PRIMARY and x["g"] == 0.3 and x["mu"] >= 1.0]
        info["mean_two_arm_power_mu_ge_1"] = float(np.mean([x["p_pass_two_arm"] for x in pw]))
        info["mean_arm_power_mu_ge_1"] = float(np.mean([x["p_pass_arm"] for x in pw]))
        allpw = [x for x in rows if x["rule"] == r and x["layout"] == PRIMARY and x["g"] == 0.3]
        info["mean_two_arm_power_all_mu"] = float(np.mean([x["p_pass_two_arm"] for x in allpw]))
        res[r] = info
    cal = [r for r in RULES if res[r][PRIMARY]["calibrated"]]
    if not cal:
        return {"by_rule": res, "calibrated": [], "recommended": None, "floor_p3": None,
                "fallback": "c (no rule calibrated; disclose its false-pass)"}
    both = [r for r in cal if res[r][SECONDARY]["calibrated"]]
    group = both or cal
    best = max(res[r]["mean_two_arm_power_mu_ge_1"] for r in group)
    near = [r for r in group if best - res[r]["mean_two_arm_power_mu_ge_1"] <= TIE]
    rec = min(near, key=lambda r: (res[r][PRIMARY]["max_arm"], -res[r]["mean_two_arm_power_mu_ge_1"]))
    floor = {"T0": 9, "T1": 3} if res[rec][SECONDARY]["calibrated"] else {"T0": 9, "T1": 6}
    return {"by_rule": res, "calibrated": cal, "calibrated_both_layouts": both, "recommended": rec,
            "tie_set": near, "floor_p3": floor}


def markdown(rows, ev):
    out = []
    for layout in (PRIMARY, SECONDARY):
        out += [f"## {layout} (P3)", ""]
        for dist, het in CONDITIONS:
            out += [f"### {dist}, {het}", "",
                    "| rule | false-pass arm / two-arm at mu 0.5, 1, 1.5, 2 | primary-only arm | two-arm power at g=0.3 | P(stop) at g=0 |",
                    "|---|---|---|---|---|"]
            for r in RULES:
                sel = lambda g: sorted((x for x in rows if x["rule"] == r and x["layout"] == layout and x["dist"] == dist
                                        and x["mu_structure"] == het and x["g"] == g), key=lambda x: x["mu"])
                n0, n3 = sel(0.0), sel(0.3)
                out.append(f"| {LABEL[r]} | " + " · ".join(f"{x['p_pass_arm']:.3f}/{x['p_pass_two_arm']:.3f}" for x in n0)
                           + " | " + " · ".join(f"{x['p_primary_arm']:.3f}" for x in n0)
                           + " | " + " · ".join(f"{x['p_pass_two_arm']:.2f}" for x in n3)
                           + " | " + " · ".join(f"{x['p_no_eligible'] + x['p_test_stop']:.2f}" for x in n0) + " |")
            out.append("")
    out += ["## Declared decision rule", "", "```", json.dumps(ev, indent=1), "```"]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--reps", type=int, default=400)
    ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)
    with Pool(a.procs) as pool:
        parts = pool.map(run_condition, [(i, d, h, a.reps) for i, (d, h) in enumerate(CONDITIONS)])
    rows = [x for p in parts for x in p]
    ev = evaluate(rows)
    print(markdown(rows, ev))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"declaration": "docs/r1/proposals/M11_D8_PASS_DECLARATION_20261116.md", "seed_base": SEED,
                       "reps": a.reps, "n_boot": N_BOOT, "python": sys.version.split()[0], "numpy": np.__version__,
                       "scipy": __import__("scipy").__version__, "rows": rows, "evaluation": ev}, fh, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
