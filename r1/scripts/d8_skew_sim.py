"""D8-SKEW (author, 15 Nov): calibration and power of four pass rules for the D8 gate under normal, left-skewed and
heavy-tailed data, with homogeneous or heterogeneous per-node mu.

Synthetic Monte Carlo only; no label, table or seed of the project is read. AI-assisted (Claude). Model, rules,
metrics and the "calibrated" decision rule are declared in docs/r1/proposals/M11_D8_SKEW_DECLARATION_20261115.md
(committed before any run). Environment: the harness uv.lock versions (Python 3.13, NumPy 2.4.4, SciPy 1.17.1).

Rules (each with V1n test side, R1 z >= 3 eligibility, and the gate's PoI conjunct):
  a    IQM of per-node ratio of means, percentile bootstrap;
  b1   same IQM, BCa (stratified jackknife acceleration);
  b2   same IQM, studentized bootstrap (delta-method se);
  c    numerator test: node-equal mean of a over eligible nodes, Welch-Satterthwaite Student-t;
  d    IQM of mean(a_j) / tier-pooled mean(d), point STOP on the tier denominator.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from multiprocessing import Pool

import numpy as np
from scipy import stats

SEED = 20261117
N_BOOT = 2000
LEVEL = 0.975
Z_ALPHA = stats.norm.ppf(1 - LEVEL)
SPLITS = {"P2 1/2:1/6:1/3": (3, 1, 2), "P3 1/3:1/6:1/2": (2, 1, 3)}
LAYOUTS = {"T1 x 12": {"T0": (8, 18), "T1": (10, 12)}, "T1 x 6": {"T0": (8, 18), "T1": (10, 6)}}
MUS = (0.5, 1.0, 1.5, 2.0)
GS = (0.0, 0.3)
ZMIN = 3.0
RULES = ("a", "b1", "b2", "c", "d")
NEG = -1e12
BIG = 1e12
CONDITIONS = [("normal", "hom"), ("normal", "het"), ("left_skewed", "hom"), ("left_skewed", "het"),
              ("t3", "hom"), ("t3", "het")]


def split_sizes(n, prop):
    tot = sum(prop)
    test = round(n * prop[2] / tot)
    dev = round(n * prop[1] / tot)
    return n - dev - test, dev, test


def noise(rng, dist, size):
    if dist == "normal":
        return rng.standard_normal(size)
    if dist == "left_skewed":
        mean, sd = math.exp(0.5), math.sqrt((math.e - 1.0) * math.e)
        return -(rng.lognormal(0.0, 1.0, size) - mean) / sd
    if dist == "t3":
        return rng.standard_t(3, size) / math.sqrt(3.0)
    raise ValueError(dist)


def iqm_weights(k):
    w = np.array([max(0, min(4 * (i + 1), 3 * k) - max(4 * i, k)) for i in range(k)], float)
    return w / (2 * k)


def lower(x):
    return float(np.quantile(x, 1 - LEVEL, method="linear"))


def iqm_sorted(x, w):
    return np.sort(x, axis=-1) @ w


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
    out = {r: {"status": None, "pass": [False, False], "prim": [False, False], "bca_fail": False} for r in RULES}
    elig = [x for x in nodes if x["elig"]]
    if not elig:
        for r in RULES:
            out[r]["status"] = "no_eligible"
        return out
    k = len(elig)
    w = iqm_weights(k)
    # PoI per arm (all nodes)
    poi_ok = []
    for arm in range(2):
        poi_b = np.mean([(x["a"][arm][x["idx"]] > 0).mean(axis=1) for x in nodes], axis=0)
        poi_ok.append(lower(poi_b) > 0.5)
    dmean = np.array([x["d"].mean() for x in elig])
    d_b = np.stack([x["d"][x["idx"]].mean(axis=1) for x in elig], axis=1)        # (B, k)
    node_stop = bool(np.any(dmean <= 0))
    tiers_e = sorted({x["tier"] for x in elig})
    col = {t: [i for i, x in enumerate(elig) if x["tier"] == t] for t in tiers_e}
    dT = {t: dmean[col[t]].mean() for t in tiers_e}
    tier_stop = any(dT[t] <= 0 for t in tiers_e)
    for r in ("a", "b1", "b2", "c"):
        out[r]["status"] = "stop" if node_stop else "read"
    out["d"]["status"] = "stop" if tier_stop else "read"
    for arm in range(2):
        amean = np.array([x["a"][arm].mean() for x in elig])
        a_b = np.stack([x["a"][arm][x["idx"]].mean(axis=1) for x in elig], axis=1)
        if not node_stop:
            G = amean / dmean
            theta = float(iqm_sorted(G, w))
            bad = d_b <= 0
            with np.errstate(divide="ignore", invalid="ignore"):
                G_b = np.where(bad, NEG, a_b / d_b)
            iq_b = iqm_sorted(G_b, w)
            prim = {}
            # (a) percentile
            prim["a"] = lower(iq_b) > 0
            # (b1) BCa
            p = (np.sum(iq_b < theta) + 0.5 * np.sum(iq_b == theta)) / N_BOOT
            bca_ok = 0.0 < p < 1.0
            lb = None
            if bca_ok:
                z0 = stats.norm.ppf(p)
                jack = []
                for j, x in enumerate(elig):
                    n = len(x["d"])
                    d_loo = (x["d"].sum() - x["d"]) / (n - 1)
                    a_loo = (x["a"][arm].sum() - x["a"][arm]) / (n - 1)
                    if np.any(d_loo <= 0):
                        bca_ok = False
                        break
                    Gm = np.tile(G, (n, 1))
                    Gm[:, j] = a_loo / d_loo
                    jack.append(iqm_sorted(Gm, w))
                if bca_ok:
                    th = np.concatenate(jack)
                    dev = th.mean() - th
                    ss = float(np.sum(dev ** 2))
                    acc = float(np.sum(dev ** 3)) / (6.0 * ss ** 1.5) if ss > 0 else math.nan
                    zz = z0 + Z_ALPHA
                    denom = 1.0 - acc * zz
                    if not (math.isfinite(z0) and math.isfinite(acc)) or denom <= 0:
                        bca_ok = False
                    else:
                        q = float(stats.norm.cdf(z0 + zz / denom))
                        lb = float(np.quantile(iq_b, q, method="linear"))
            prim["b1"] = bool(bca_ok and lb is not None and lb > 0)
            out["b1"]["bca_fail"] = out["b1"]["bca_fail"] or not bca_ok
            # (b2) studentized
            def node_se(av, dv, Gv):
                n = av.shape[-1]
                va = av.var(axis=-1, ddof=1)
                vd = dv.var(axis=-1, ddof=1)
                cv = ((av - av.mean(axis=-1, keepdims=True)) * (dv - dv.mean(axis=-1, keepdims=True))).sum(axis=-1) / (n - 1)
                num = np.maximum(va + Gv ** 2 * vd - 2 * Gv * cv, 0.0)
                with np.errstate(divide="ignore", invalid="ignore"):
                    return np.sqrt(num / (n * dv.mean(axis=-1) ** 2))
            se_pt = np.array([node_se(x["a"][arm], x["d"], G[j]) for j, x in enumerate(elig)])
            order = np.argsort(G)
            se_hat = float(np.sqrt(np.sum((w * se_pt[order]) ** 2)))
            se_b = np.empty_like(G_b)
            for j, x in enumerate(elig):
                ab = x["a"][arm][x["idx"]]
                db = x["d"][x["idx"]]
                with np.errstate(divide="ignore", invalid="ignore"):
                    gb = np.where(db.mean(axis=1) > 0, ab.mean(axis=1) / db.mean(axis=1), 0.0)
                se_b[:, j] = node_se(ab, db, gb)
            ordb = np.argsort(G_b, axis=1)
            se_sorted = np.take_along_axis(se_b, ordb, axis=1)
            se_iq_b = np.sqrt(np.sum((w * se_sorted) ** 2, axis=1))
            with np.errstate(divide="ignore", invalid="ignore"):
                tstar = (iq_b - theta) / se_iq_b
            tstar = np.where(bad.any(axis=1) | ~(se_iq_b > 0) | ~np.isfinite(tstar), BIG, tstar)
            qt = float(np.quantile(tstar, LEVEL, method="linear"))
            prim["b2"] = (theta - qt * se_hat) > 0 if se_hat > 0 else theta > 0
            # (c) numerator, Welch-Satterthwaite t
            n_j = np.array([len(x["a"][arm]) for x in elig], float)
            s2 = np.array([x["a"][arm].var(ddof=1) for x in elig])
            abar = float(amean.mean())
            v = s2 / (k ** 2 * n_j)
            se_c = math.sqrt(float(v.sum()))
            if se_c > 0:
                df = float(v.sum() ** 2 / np.sum(v ** 2 / (n_j - 1)))
                prim["c"] = abar - stats.t.ppf(LEVEL, df) * se_c > 0
            else:
                prim["c"] = abar > 0
            for r in ("a", "b1", "b2", "c"):
                out[r]["prim"][arm] = bool(prim[r])
                out[r]["pass"][arm] = bool(prim[r] and poi_ok[arm])
        if not tier_stop:
            den = np.empty(k)
            den_b = np.empty_like(d_b)
            for t in tiers_e:
                den[col[t]] = dT[t]
                den_b[:, col[t]] = d_b[:, col[t]].mean(axis=1)[:, None]
            with np.errstate(divide="ignore", invalid="ignore"):
                Gd_b = np.where(den_b <= 0, NEG, a_b / den_b)
            pd = lower(iqm_sorted(Gd_b, w)) > 0
            out["d"]["prim"][arm] = bool(pd)
            out["d"]["pass"][arm] = bool(pd and poi_ok[arm])
    return out


def run_condition(args):
    ci, dist, het, layouts, reps = args
    rng = np.random.Generator(np.random.PCG64(SEED + ci))
    rows = []
    for layout in layouts:
        tiers = LAYOUTS[layout]
        for split, prop in SPLITS.items():
            sizes = {t: split_sizes(n, prop) for t, (_m, n) in tiers.items()}
            for mu in MUS:
                for g in GS:
                    acc = {r: {"no_eligible": 0, "stop": 0, "read": 0, "arm1": 0, "any": 0, "prim_arm1": 0,
                               "prim_any": 0, "bca_fail": 0} for r in RULES}
                    for _ in range(reps):
                        o = one_rep(rng, dist, het, mu, g, tiers, sizes)
                        for r in RULES:
                            x = o[r]
                            acc[r][x["status"]] += 1
                            acc[r]["arm1"] += x["pass"][0]
                            acc[r]["any"] += x["pass"][0] or x["pass"][1]
                            acc[r]["prim_arm1"] += x["prim"][0]
                            acc[r]["prim_any"] += x["prim"][0] or x["prim"][1]
                            acc[r]["bca_fail"] += x["bca_fail"] and x["status"] == "read"
                    for r in RULES:
                        a = acc[r]
                        rows.append({"dist": dist, "mu_structure": het, "layout": layout, "split": split, "sizes": sizes,
                                     "mu": mu, "g": g, "rule": r, "reps": reps,
                                     "p_no_eligible": a["no_eligible"] / reps, "p_test_stop": a["stop"] / reps,
                                     "p_stop": (a["no_eligible"] + a["stop"]) / reps,
                                     "p_pass_arm": a["arm1"] / reps, "p_pass_two_arm": a["any"] / reps,
                                     "p_primary_arm": a["prim_arm1"] / reps, "p_primary_two_arm": a["prim_any"] / reps,
                                     "bca_fail_share_of_read": (a["bca_fail"] / a["read"]) if (r == "b1" and a["read"]) else None})
    return rows


def evaluate(rows):
    """The declared decision rule (declaration §4)."""
    res = {}
    for r in RULES:
        per_cond = {}
        for dist, het in CONDITIONS:
            sub = [x for x in rows if x["rule"] == r and x["dist"] == dist and x["mu_structure"] == het
                   and x["layout"] == "T1 x 12" and x["g"] == 0.0]
            exc = [{"split": x["split"], "mu": x["mu"], "arm": x["p_pass_arm"], "two_arm": x["p_pass_two_arm"]}
                   for x in sub if x["p_pass_arm"] > 0.035 or x["p_pass_two_arm"] > 0.065]
            per_cond[f"{dist}/{het}"] = {"calibrated": not exc, "exceedances": exc,
                                         "max_arm": max(x["p_pass_arm"] for x in sub),
                                         "max_two_arm": max(x["p_pass_two_arm"] for x in sub)}
        pw = [x["p_pass_two_arm"] for x in rows if x["rule"] == r and x["layout"] == "T1 x 12" and x["g"] == 0.3
              and x["mu"] >= 1.0]
        sec = [x for x in rows if x["rule"] == r and x["layout"] == "T1 x 6" and x["g"] == 0.0]
        res[r] = {"calibrated": all(v["calibrated"] for v in per_cond.values()), "conditions": per_cond,
                  "mean_two_arm_power_mu_ge_1": sum(pw) / len(pw),
                  "secondary_T1x6_exceedances": [{"split": x["split"], "mu": x["mu"], "arm": x["p_pass_arm"],
                                                   "two_arm": x["p_pass_two_arm"]} for x in sec
                                                  if x["p_pass_arm"] > 0.035 or x["p_pass_two_arm"] > 0.065]}
    order = ("c", "a", "d", "b2", "b1")
    cal = [r for r in RULES if res[r]["calibrated"]]
    rec = None
    if cal:
        best = max(res[r]["mean_two_arm_power_mu_ge_1"] for r in cal)
        near = [r for r in cal if res[r]["mean_two_arm_power_mu_ge_1"] >= best - 0.02]
        rec = min(near, key=order.index)
    return {"by_rule": res, "calibrated_rules": cal, "recommended": rec}


def markdown(rows):
    out = []
    for dist, het in CONDITIONS:
        for layout in (["T1 x 12", "T1 x 6"] if (dist, het) == ("normal", "hom") else ["T1 x 12"]):
            for split in SPLITS:
                sub = [x for x in rows if (x["dist"], x["mu_structure"], x["layout"], x["split"]) == (dist, het, layout, split)]
                if not sub:
                    continue
                out += ["", f"**{dist}, mu {het}, {layout}, split {split}** — cells: false pass at g = 0 per arm / two-arm "
                        "(primary bound alone, per arm) ; power at g = 0.3 per arm / two-arm ; P(STOP) at g = 0.3", "",
                        "| rule | " + " | ".join(f"mu = {m:g}" for m in MUS) + " |", "|---" * (1 + len(MUS)) + "|"]
                for r in RULES:
                    cells = []
                    for mu in MUS:
                        z = next(x for x in sub if x["rule"] == r and x["mu"] == mu and x["g"] == 0.0)
                        p = next(x for x in sub if x["rule"] == r and x["mu"] == mu and x["g"] == 0.3)
                        cells.append(f"{z['p_pass_arm']:.3f} / {z['p_pass_two_arm']:.3f} ({z['p_primary_arm']:.3f}) ; "
                                     f"{p['p_pass_arm']:.2f} / {p['p_pass_two_arm']:.2f} ; {p['p_stop']:.2f}")
                    out.append(f"| {r} | " + " | ".join(cells) + " |")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--reps", type=int, default=400)
    ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)
    jobs = [(i, dist, het, (["T1 x 12", "T1 x 6"] if (dist, het) == ("normal", "hom") else ["T1 x 12"]), a.reps)
            for i, (dist, het) in enumerate(CONDITIONS)]
    with Pool(a.procs) as pool:
        parts = pool.map(run_condition, jobs)
    rows = [x for p in parts for x in p]
    ev = evaluate(rows)
    res = {"seed_base": SEED, "reps": a.reps, "n_boot": N_BOOT, "level": LEVEL, "zmin": ZMIN, "numpy": np.__version__,
           "scipy": __import__("scipy").__version__, "python": sys.version.split()[0], "conditions": CONDITIONS,
           "evaluation": ev, "scenarios": rows}
    print(markdown(rows))
    print("\n```\n" + json.dumps(ev, indent=1) + "\n```")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=1, sort_keys=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
