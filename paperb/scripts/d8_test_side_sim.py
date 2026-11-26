"""D8-TEST (author, 15 Nov): test-side STOP variants of the D8 gate, with train+dev eligibility and fixed splits.

Synthetic Monte Carlo only; no label, table or seed of the project is read. AI-assisted (Claude).
Run in the harness uv.lock environment (NumPy 2.4.4, Python 3.13; D8-Q3b).

Extends ``d8_eligibility_alternatives_sim.py`` (accepted at 82923797) from P(STOP) alone to the whole gate read, so that
a test-side rule that STOPs less can be compared on what it does to the gate's verdict. Model (declared; report
``docs/r1/reports/M11_D8_TEST_SIDE_20261115.md``):

* per node and instance, d = U_oracle - U_A2 = mu + e and a = U_arm - U_A2 = g * mu + h, with e, h independent, sd 1
  (normal; left-skewed e and h as a sensitivity, same shape as the 14 Nov simulations); mu is the ceiling gap in units of
  the per-instance sd, g the arm's true gap closed; all nodes share mu and g;
* layout T0 = 8 nodes x 18 instances; T1 = 10 nodes x 12 or x 6 instances; fixed splits train : dev : test
  P2 = 1/2 : 1/6 : 1/3 (recommended 14 Nov) and P3 = 1/3 : 1/6 : 1/2 (more test instances at the same totals);
* eligibility R1: paired z of d on train + dev instances >= z_min (3, and 6), delta_n non-binding (as on 14 Nov);
* gate read as in ``r1/c3/gate.py`` for the first-ranked arm: per eligible node gap closed G = mean(a) / mean(d) on the
  test instances; IQM across eligible nodes (the gate's fractional 25 %-75 % trimmed mean); PoI = mean over all nodes
  of the share of test instances with a > 0; node-stratified bootstrap with one shared index draw per node; pass iff
  the 97.5 % lower bound of the IQM is > 0 and of the PoI is > 0.5;
* test-side variants (the D8-TEST options):
    V0  current:   STOP if an eligible node's point test denominator mean(d) <= 0, or any of its 2,000 resampled
                   denominators is <= 0;
    V1  point:     STOP only on a nonpositive point denominator; a resample in which any eligible node's denominator is
                   <= 0 counts as IQM* = -inf (it can only lower the bound: conservative, nothing is dropped);
    V1n point:     as V1, but only that node's G* is set to -inf, and the IQM's trimming may discard it;
    V2  tier:      each node's gap is divided by its tier's pooled denominator (mean over the tier's eligible nodes of
                   mean(d)); STOP if a tier's point or any resampled pooled denominator is <= 0;
* the gate also STOPs when no node is eligible.

Outputs per scenario: P(STOP), split into P(no node eligible) and the test-side part; P(pass); P(pass | read).
"""
from __future__ import annotations

import argparse
import json
import math
import sys

import numpy as np

SEED = 20261115
N_BOOT = 2000
LEVEL = 0.975
SPLITS = {"P2 1/2:1/6:1/3": (3, 1, 2), "P3 1/3:1/6:1/2": (2, 1, 3)}     # train : dev : test
LAYOUTS = {"T1 x 12": {"T0": (8, 18), "T1": (10, 12)}, "T1 x 6": {"T0": (8, 18), "T1": (10, 6)}}
MUS = (0.5, 1.0, 1.5, 2.0)
GS = (0.0, 0.3)
ZMINS = (3.0, 6.0)
VARIANTS = ("V0", "V1", "V1n", "V2")
NEG = -1e12    # stands for -inf (0 * -inf and quantiles over -inf would give nan); far below any real gap


def split_sizes(n, prop):
    tot = sum(prop)
    test = round(n * prop[2] / tot)
    dev = round(n * prop[1] / tot)
    return n - dev - test, dev, test


def draw(rng, dist, size):
    if dist == "normal":
        return rng.standard_normal(size)
    if dist == "left_skewed":
        mean, sd = math.exp(0.5), math.sqrt((math.e - 1.0) * math.e)
        return -(rng.lognormal(0.0, 1.0, size) - mean) / sd
    raise ValueError(dist)


def iqm_weights(k):
    """Weights of r1/c3/gate._node_iqm for k sorted values (quarter units), divided by 2k."""
    w = np.array([max(0, min(4 * (i + 1), 3 * k) - max(4 * i, k)) for i in range(k)], float)
    return w / (2 * k)


def iqm_rows(x):
    """IQM of each row of x (values may be NEG)."""
    k = x.shape[-1]
    return np.sort(x, axis=-1) @ iqm_weights(k)


def lower(boot):
    return float(np.quantile(boot, 1 - LEVEL, method="linear"))


def one_rep(rng, dist, mu, g, tiers, sizes, zmin):
    """One synthetic gate read; returns the outcome of each variant: 'no_eligible', 'stop', 'pass' or 'fail'."""
    nodes = []
    for t, (m, _n) in tiers.items():
        n_tr, n_dev, n_te = sizes[t]
        for _ in range(m):
            dtd = mu + draw(rng, dist, n_tr + n_dev)
            sd = dtd.std(ddof=1)
            z = dtd.mean() / (sd / math.sqrt(len(dtd))) if sd > 0 else (math.inf if dtd.mean() > 0 else -math.inf)
            d = mu + draw(rng, dist, n_te)
            a = g * mu + draw(rng, dist, n_te)
            idx = rng.integers(0, n_te, size=(N_BOOT, n_te))
            nodes.append({"tier": t, "elig": z >= zmin, "d": d.mean(), "a": a.mean(), "win": float(np.mean(a > 0)),
                          "d_b": d[idx].mean(axis=1), "a_b": a[idx].mean(axis=1), "win_b": (a[idx] > 0).mean(axis=1)})
    elig = [x for x in nodes if x["elig"]]
    if not elig:
        return {v: "no_eligible" for v in VARIANTS}
    poi_b = np.mean([x["win_b"] for x in nodes], axis=0)
    poi_ok = lower(poi_b) > 0.5
    d_pt = np.array([x["d"] for x in elig])
    a_pt = np.array([x["a"] for x in elig])
    d_b = np.stack([x["d_b"] for x in elig], axis=1)        # (N_BOOT, k)
    a_b = np.stack([x["a_b"] for x in elig], axis=1)
    out = {}
    # V0, V1, V1n: per-node denominators
    point_bad = bool(np.any(d_pt <= 0))
    boot_bad = d_b <= 0
    if point_bad or boot_bad.any():
        out["V0"] = "stop"
    if point_bad:
        out["V1"] = out["V1n"] = "stop"
    if len(out) < 3:
        with np.errstate(divide="ignore", invalid="ignore"):
            g_b = np.where(boot_bad, NEG, a_b / d_b)
        if "V0" not in out:
            out["V0"] = "pass" if lower(iqm_rows(g_b)) > 0 and poi_ok else "fail"
        if "V1" not in out:
            iq = iqm_rows(g_b)
            iq = np.where(boot_bad.any(axis=1), NEG, iq)          # the whole resample counts as failing
            out["V1"] = "pass" if lower(iq) > 0 and poi_ok else "fail"
            out["V1n"] = "pass" if lower(iqm_rows(g_b)) > 0 and poi_ok else "fail"   # NEG node may be trimmed"
    # V2: tier-pooled denominators
    tiers_e = sorted({x["tier"] for x in elig})
    col = {t: [i for i, x in enumerate(elig) if x["tier"] == t] for t in tiers_e}
    dt_pt = {t: d_pt[col[t]].mean() for t in tiers_e}
    dt_b = {t: d_b[:, col[t]].mean(axis=1) for t in tiers_e}
    if any(dt_pt[t] <= 0 or np.any(dt_b[t] <= 0) for t in tiers_e):
        out["V2"] = "stop"
    else:
        den_b = np.empty_like(d_b)
        for t in tiers_e:
            den_b[:, col[t]] = dt_b[t][:, None]
        out["V2"] = "pass" if lower(iqm_rows(a_b / den_b)) > 0 and poi_ok else "fail"
    return out


def run(reps, dists=("normal",), seed=SEED, layouts=LAYOUTS, splits=SPLITS, mus=MUS, gs=GS, zmins=ZMINS):
    rng = np.random.Generator(np.random.PCG64(seed))
    rows = []
    for layout, tiers in layouts.items():
        for split, prop in splits.items():
            sizes = {t: split_sizes(n, prop) for t, (_m, n) in tiers.items()}
            for dist in dists:
                for zmin in zmins:
                    for mu in mus:
                        for g in gs:
                            counts = {v: {"no_eligible": 0, "stop": 0, "pass": 0, "fail": 0} for v in VARIANTS}
                            for _ in range(reps):
                                for v, o in one_rep(rng, dist, mu, g, tiers, sizes, zmin).items():
                                    counts[v][o] += 1
                            for v in VARIANTS:
                                c = counts[v]
                                read = c["pass"] + c["fail"]
                                rows.append({"layout": layout, "split": split, "sizes": sizes, "dist": dist,
                                             "zmin": zmin, "mu": mu, "g": g, "variant": v, "reps": reps,
                                             "p_no_eligible": c["no_eligible"] / reps,
                                             "p_test_stop": c["stop"] / reps,
                                             "p_stop": (c["no_eligible"] + c["stop"]) / reps,
                                             "p_pass": c["pass"] / reps,
                                             "p_pass_given_read": (c["pass"] / read) if read else None})
    return {"seed": seed, "reps": reps, "n_boot": N_BOOT, "level": LEVEL, "numpy": np.__version__,
            "python": sys.version.split()[0], "splits": splits, "variants": VARIANTS,
            "layouts": {k: {t: list(v) for t, v in d.items()} for k, d in layouts.items()}, "scenarios": rows}


def markdown(res, dist="normal"):
    out = []
    keys = sorted({(r["layout"], r["split"], r["zmin"]) for r in res["scenarios"] if r["dist"] == dist},
                  key=lambda k: (list(LAYOUTS).index(k[0]), list(SPLITS).index(k[1]), k[2]))
    for layout, split, zmin in keys:
        sub = [r for r in res["scenarios"] if (r["layout"], r["split"], r["zmin"], r["dist"]) == (layout, split, zmin, dist)]
        sz = sub[0]["sizes"]
        mus = sorted({r["mu"] for r in sub})
        out += ["", f"**{dist}, {layout}, split {split}, R1 z >= {zmin:g}** — train/dev/test T0 "
                    f"{'/'.join(map(str, sz['T0']))}, T1 {'/'.join(map(str, sz['T1']))}. "
                    "Cells: P(STOP) [no-eligible + test-side] / P(pass) at g = 0 / P(pass) at g = 0.3.", "",
                "| variant | " + " | ".join(f"mu = {m:g}" for m in mus) + " |", "|---" * (1 + len(mus)) + "|"]
        for v in VARIANTS:
            cells = []
            for mu in mus:
                r0 = next(x for x in sub if x["variant"] == v and x["mu"] == mu and x["g"] == 0.0)
                r3 = next(x for x in sub if x["variant"] == v and x["mu"] == mu and x["g"] == 0.3)
                cells.append(f"{r3['p_stop']:.2f} [{r3['p_no_eligible']:.2f} + {r3['p_test_stop']:.2f}] / "
                             f"{r0['p_pass']:.3f} / {r3['p_pass']:.2f}")
            out.append(f"| {v} | " + " | ".join(cells) + " |")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--reps", type=int, default=400)
    ap.add_argument("--skewed-reps", type=int, default=0, help="also run left-skewed d and a (P2, T1 x 12 only)")
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)
    res = run(a.reps)
    print(markdown(res))
    if a.skewed_reps:
        sk = run(a.skewed_reps, dists=("left_skewed",), seed=SEED + 1,
                 layouts={"T1 x 12": LAYOUTS["T1 x 12"]}, splits={"P2 1/2:1/6:1/3": SPLITS["P2 1/2:1/6:1/3"]})
        res["skewed"] = sk
        print(markdown(sk, "left_skewed"))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=1, sort_keys=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
