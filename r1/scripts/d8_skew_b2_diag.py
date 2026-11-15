"""D8-SKEW, POST HOC diagnostic of rule (b2) (written after the declared run and its independent review).

Not a declared rule, not part of the declared decision rule. AI-assisted (Claude). Synthetic Monte Carlo only.

Question (review finding F1): does (b2) meet the false-pass thresholds because the studentized interval is
calibrated, or because of its declared convention that a resample with any eligible node mean(d*) <= 0 gets
t* = +inf? With 2000 resamples, the convention forces the bound to -inf (an automatic arm fail) whenever more than
2.5 % of resamples are such "bad" resamples.

Per scenario and arm 1 this reports:
  auto_fail    share of read reps in which the convention alone makes (b2) fail (bad share > 1 - LEVEL);
  bad_median   median share of bad resamples over read reps;
  declared     (b2) as declared (with PoI), per arm and two-arm: should agree with sim_output.json within MC error;
  drop_bad     (b2) with bad resamples dropped instead of set to +inf (quantile over the rest; fail if none left).

Model, sizes, eligibility, V1n test side and PoI are those of d8_skew_sim.py (imported). Seed 20261217 + scenario
index (not the declared run's seeds).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import d8_skew_sim as S  # noqa: E402

DIAG_SEED = 20261217
SCEN = [(dist, "hom", "T1 x 12", split, mu, g) for dist, g in (("left_skewed", 0.0), ("normal", 0.0),
                                                               ("normal", 0.3), ("left_skewed", 0.3))
        for split in S.SPLITS for mu in S.MUS]


def node_se(av, dv, Gv):
    n = av.shape[-1]
    va = av.var(axis=-1, ddof=1)
    vd = dv.var(axis=-1, ddof=1)
    cv = ((av - av.mean(axis=-1, keepdims=True)) * (dv - dv.mean(axis=-1, keepdims=True))).sum(axis=-1) / (n - 1)
    num = np.maximum(va + Gv ** 2 * vd - 2 * Gv * cv, 0.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.sqrt(num / (n * dv.mean(axis=-1) ** 2))


def one_rep(rng, dist, het, mu, g, tiers, sizes):
    nodes = []
    for t, (m, _n) in tiers.items():
        n_tr, n_dev, n_te = sizes[t]
        for _ in range(m):
            mu_j = mu * (rng.uniform(0.5, 1.5) if het == "het" else 1.0)
            dtd = mu_j + S.noise(rng, dist, n_tr + n_dev)
            sd = dtd.std(ddof=1)
            z = dtd.mean() / (sd / math.sqrt(len(dtd))) if sd > 0 else (math.inf if dtd.mean() > 0 else -math.inf)
            d = mu_j + S.noise(rng, dist, n_te)
            c = S.noise(rng, dist, n_te)
            a = [g * mu_j + math.sqrt(0.5) * c + math.sqrt(0.5) * S.noise(rng, dist, n_te) for _ in range(2)]
            idx = rng.integers(0, n_te, size=(S.N_BOOT, n_te))
            nodes.append({"elig": z >= S.ZMIN, "d": d, "a": a, "idx": idx})
    elig = [x for x in nodes if x["elig"]]
    if not elig:
        return None
    dmean = np.array([x["d"].mean() for x in elig])
    if np.any(dmean <= 0):
        return None                                   # V1n point STOP: not a read rep
    k = len(elig)
    w = S.iqm_weights(k)
    d_b = np.stack([x["d"][x["idx"]].mean(axis=1) for x in elig], axis=1)
    bad = (d_b <= 0).any(axis=1)
    res = {"bad_share": float(bad.mean()), "declared": [False, False], "drop_bad": [False, False]}
    for arm in range(2):
        poi = S.lower(np.mean([(x["a"][arm][x["idx"]] > 0).mean(axis=1) for x in nodes], axis=0)) > 0.5
        amean = np.array([x["a"][arm].mean() for x in elig])
        a_b = np.stack([x["a"][arm][x["idx"]].mean(axis=1) for x in elig], axis=1)
        G = amean / dmean
        theta = float(S.iqm_sorted(G, w))
        with np.errstate(divide="ignore", invalid="ignore"):
            G_b = np.where(d_b <= 0, S.NEG, a_b / d_b)
        iq_b = S.iqm_sorted(G_b, w)
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
        invalid = bad | ~(se_iq_b > 0) | ~np.isfinite(tstar)
        if se_hat > 0:
            q_dec = float(np.quantile(np.where(invalid, S.BIG, tstar), S.LEVEL, method="linear"))
            dec = theta - q_dec * se_hat > 0
            if (~invalid).any():
                q_drop = float(np.quantile(tstar[~invalid], S.LEVEL, method="linear"))
                drop = theta - q_drop * se_hat > 0
            else:
                drop = False
        else:
            dec = drop = theta > 0
        res["declared"][arm] = bool(dec and poi)
        res["drop_bad"][arm] = bool(drop and poi)
    return res


def run(args):
    i, (dist, het, layout, split, mu, g), reps = args
    rng = np.random.Generator(np.random.PCG64(DIAG_SEED + i))
    tiers = S.LAYOUTS[layout]
    sizes = {t: S.split_sizes(n, S.SPLITS[split]) for t, (_m, n) in tiers.items()}
    out = [one_rep(rng, dist, het, mu, g, tiers, sizes) for _ in range(reps)]
    rd = [o for o in out if o is not None]
    f = lambda key, two: sum((o[key][0] or o[key][1]) if two else o[key][0] for o in rd) / reps
    return {"dist": dist, "mu_structure": het, "layout": layout, "split": split, "mu": mu, "g": g, "reps": reps,
            "p_read": len(rd) / reps,
            "auto_fail_share_of_read": (sum(o["bad_share"] > 1 - S.LEVEL for o in rd) / len(rd)) if rd else None,
            "bad_share_median": float(np.median([o["bad_share"] for o in rd])) if rd else None,
            "declared_arm": f("declared", False), "declared_two_arm": f("declared", True),
            "drop_bad_arm": f("drop_bad", False), "drop_bad_two_arm": f("drop_bad", True)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--reps", type=int, default=400)
    ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)
    with Pool(a.procs) as pool:
        rows = pool.map(run, [(i, s, a.reps) for i, s in enumerate(SCEN)])
    print("| noise | g | split | mu | P(read) | auto-fail share of read | median bad share | declared arm / two-arm "
          "| drop-bad arm / two-arm |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['dist']} | {r['g']:g} | {r['split'][:2]} | {r['mu']:g} | {r['p_read']:.2f} | "
              f"{r['auto_fail_share_of_read']:.2f} | {r['bad_share_median']:.3f} | "
              f"{r['declared_arm']:.3f} / {r['declared_two_arm']:.3f} | {r['drop_bad_arm']:.3f} / {r['drop_bad_two_arm']:.3f} |")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"seed_base": DIAG_SEED, "reps": a.reps, "numpy": np.__version__,
                       "scipy": __import__("scipy").__version__, "python": sys.version.split()[0], "rows": rows},
                      fh, indent=1, sort_keys=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
