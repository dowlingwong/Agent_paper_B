"""S0.5 digits diagnostic 2 (descriptive, offline; nothing is changed in the model or pins).

Decomposes the 80 % predictive intervals of s05_calibration.jsonl into prior/posterior variance (tau_n^2), the
within-key spread (tau_w^2) and the audit noise (se^2), and evaluates a two-parameter recalibration offline:
prior scale c (multiplies the prior sds tau0 and tau_w; variant 'tau0_only' multiplies tau0 alone) and the
observation-noise inflation lam (multiplies the update's observation variance, as obs_inflation does).
Grid: log grid c in [0.01, 1000] x lam in [1e-4, 1000], 121 x 121.  The code and the runbook allow only lam >= 1, so
the in-sample search also reports the best grid point with lam >= 1; lam = 1 itself is not a grid point, so
``diag2_lambda1.py`` scans lam = 1 exactly.
(c, lam) are fitted on the S0.4 rows the prior was fitted from (sequential replay per instance and (key, sign)
group, executed Delta_hat as the observations), by maximum Gaussian predictive log-likelihood and, separately, by
the smallest worst-stratum coverage error; then tested on the S0.5 calibration rows, whose group sums are
recovered exactly from (mu, n_group) and the prior (conjugate update of a2u.group_posterior).
"""
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

# ---- decomposition at the run's own prior (c = 1, lam = 1) ---------------------------------------------------
dec = collections.defaultdict(lambda: collections.defaultdict(list))
for n, ssum, se, d in s05_items:
    mu, var = post(n, ssum, TAU0, TW, LAM0)
    s = dec[STR(n)]
    s["resid"].append(d - mu); s["tau_n2"].append(var); s["se2"].append(se ** 2)
decomp = {}
for k, s in sorted(dec.items()):
    res = np.array(s["resid"]); tn2 = float(np.mean(s["tau_n2"])); se2 = float(np.mean(s["se2"]))
    pred = tn2 + TW ** 2 + se2
    decomp[k] = {"n": len(res), "mean_residual": float(res.mean()), "sd_residual": float(res.std(ddof=1)),
                 "mean_sq_residual": float(np.mean(res ** 2)), "predicted_var": pred,
                 "ratio_msr_to_predicted": float(np.mean(res ** 2) / pred),
                 "share_tau_n2": tn2 / pred, "share_tau_w2": TW ** 2 / pred, "share_se2": se2 / pred,
                 "bias_sq_share_of_msr": float(res.mean() ** 2 / np.mean(res ** 2))}

cs = np.exp(np.linspace(math.log(0.01), math.log(1000.0), 121))
lams = np.exp(np.linspace(math.log(1e-4), math.log(1000.0), 121))
out = {"prior": {"mu0": MU0, "tau0": TAU0, "tau_w": TW, "sigma_cmp": SIG, "obs_inflation": LAM0},
       "s05_sd_reconstruction_max_abs_error": sd_err, "s04_rows": len(s04_items), "s05_rows": len(s05_items),
       "decomposition_s05_at_run_prior": decomp,
       "baseline": {"s04": evaluate(s04_items, 1.0, 1.0, "both")[1], "s05": evaluate(s05_items, 1.0, 1.0, "both")[1]},
       "grid": {"c": [float(cs[0]), float(cs[-1]), len(cs)], "lam": [float(lams[0]), float(lams[-1]), len(lams)]}}
for variant in ("both", "tau0_only"):
    best_ll = None; best_cov = None; any_pass = []; best_allowed = None
    for c in cs:
        for lam in lams:
            ll4, by4 = evaluate(s04_items, c, lam, variant)
            if best_ll is None or ll4 > best_ll[0]: best_ll = (ll4, c, lam, by4)
            w4 = worst(by4)
            if best_cov is None or w4 < best_cov[0]: best_cov = (w4, c, lam, by4)
            _, by5 = evaluate(s05_items, c, lam, variant)
            if gate(by5): any_pass.append((float(c), float(lam)))
            if lam >= 1.0 and (best_allowed is None or worst(by5) < best_allowed[0]):
                best_allowed = (worst(by5), float(c), float(lam), by5)
    res = {}
    for name, b in (("max_loglik_on_s04", best_ll), ("min_worst_stratum_error_on_s04", best_cov)):
        _, by5 = evaluate(s05_items, b[1], b[2], variant)
        res[name] = {"c": float(b[1]), "lam": float(b[2]), "s04": b[3], "s05_test": by5, "s05_gate_pass": gate(by5)}
    res["s05_grid_points_passing_gate_in_sample"] = {"count": len(any_pass), "of": len(cs) * len(lams),
                                                     "with_lam_ge_1": sum(1 for c, l in any_pass if l >= 1.0),
                                                     "points": any_pass}
    res["s05_in_sample_best_with_lam_ge_1"] = {"worst_stratum_error": best_allowed[0], "c": best_allowed[1],
                                              "lam": best_allowed[2], "s05": best_allowed[3], "gate_pass": gate(best_allowed[3])}
    out[f"recalibration_{variant}"] = res
json.dump(out, sys.stdout, indent=1)
