"""S0.5 digits diagnostic 2b (descriptive, offline): the two-parameter recalibration of diag2.py at lam = 1 exactly
(the run's own obs_inflation, the smallest value the code and the runbook allow; lam = 1 is not a point of diag2's
grid), on a fine log grid of the prior scale c in [1, 1000] (700 points), both variants, evaluated in sample on the
S0.5 calibration rows.  The model, the S0.4/S0.5 item construction and the evaluation are copied verbatim from
diag2.py (between its argument line and its decomposition section)."""
import json, math, sys, collections
import numpy as np
from scipy.stats import norm

prior_path, s04_path, s05_path = sys.argv[1:4]
P = json.load(open(prior_path)); kp = P["kinds"]["local"]
MU0, TAU0, SIG, TW = kp["mu0"], kp["tau0"], kp["sigma_cmp"], kp["tau_w"]
LAM0 = float(P["meta"]["obs_inflation"])
Z = float(norm.ppf(0.9))
STR = lambda n: "0" if n == 0 else "1-2" if n <= 2 else ">=3"

def post(n, sd_sum, tau0, tw, lam):
    obs_var = lam * (SIG ** 2 + tw ** 2)
    var = 1.0 / (1.0 / tau0 ** 2 + n / obs_var)
    return var * (MU0 / tau0 ** 2 + sd_sum / obs_var), var

def scaled(c, variant):
    return (c * TAU0, c * TW) if variant == "both" else (c * TAU0, TW)

# ---- S0.4: sequential replay -------------------------------------------------------------------------------
s04 = [json.loads(l) for l in open(s04_path)]
s04.sort(key=lambda r: (r["instance"], int(r["budget_index"])))
s04_items = []   # (n, sum_before, se, delta_audit)
hist = collections.defaultdict(list)
for r in s04:
    g = (r["instance"], r["key"], r["sign"])
    obs = hist[g]
    s04_items.append((len(obs), float(sum(obs)), float(r["se"] or 0.0), float(r["delta_audit"])))
    if r.get("delta_hat") is not None:
        obs.append(float(r["delta_hat"]))

# ---- S0.5: recover the group sums from the recorded forecasts ------------------------------------------------
s05 = [json.loads(l) for l in open(s05_path)]
s05_items = []; sd_err = 0.0
for r in s05:
    n = int(r["n_group"]); se = float(r["se"] or 0.0)
    obs_var = LAM0 * (SIG ** 2 + TW ** 2)
    var = 1.0 / (1.0 / TAU0 ** 2 + n / obs_var)
    ssum = obs_var * (float(r["mu"]) / var - MU0 / TAU0 ** 2)
    sd_err = max(sd_err, abs(math.sqrt(var + TW ** 2 + se ** 2) - float(r["sd"])))
    s05_items.append((n, ssum, se, float(r["delta_audit"])))

def evaluate(items, c, lam, variant):
    tau0, tw = scaled(c, variant)
    ll = 0.0; cov = collections.defaultdict(list)
    for n, ssum, se, d in items:
        mu, var = post(n, ssum, tau0, tw, lam)
        sd = math.sqrt(var + tw ** 2 + se ** 2)
        ll += norm.logpdf(d, mu, sd)
        cov[STR(n)].append(abs(d - mu) <= Z * sd)
    allc = [x for v in cov.values() for x in v]
    by = {k: {"n": len(v), "coverage": float(np.mean(v))} for k, v in sorted(cov.items())}
    by["overall"] = {"n": len(allc), "coverage": float(np.mean(allc))}
    return ll, by

def gate(by, min_n=20):
    return all(0.70 <= v["coverage"] <= 0.90 for k, v in by.items() if v["n"] >= min_n)

def worst(by, min_n=20):
    return max(abs(v["coverage"] - 0.80) for v in by.values() if v["n"] >= min_n)


cs = np.exp(np.linspace(math.log(1.0), math.log(1000.0), 700))
out = {"lam": 1.0, "c_grid": [1.0, 1000.0, 700], "tau0_run": TAU0, "sigma_node_note": "tau0_run = 0.15 sigma_node"}
for variant in ("both", "tau0_only"):
    passing = []; best = None
    for c in cs:
        _, by5 = evaluate(s05_items, c, 1.0, variant)
        if gate(by5): passing.append((float(c), {k: v["coverage"] for k, v in by5.items()}))
        if best is None or worst(by5) < best[0]: best = (worst(by5), float(c), by5)
    out[variant] = {"passing_count": len(passing),
                    "passing_c_range": [passing[0][0], passing[-1][0]] if passing else None,
                    "passing": passing,
                    "best": {"worst_stratum_error": best[0], "c": best[1], "s05": best[2], "gate_pass": gate(best[2])}}
json.dump(out, sys.stdout, indent=1)
