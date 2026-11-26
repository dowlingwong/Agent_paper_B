"""Offline, descriptive: V* of the S0.5 eligible E1 decisions if tau0 were c x the run's tau0 (lam fixed), on the
OBSERVED group histories (the campaigns are not replayed: a different prior would execute different proposals).
Usage: python vstar_counterfactual.py <prior.json> <s05_calibration.jsonl> <g> <c> [<c> ...]
Group sums are recovered from (mu, n_group) and the run prior exactly as in diag2.py; V* is rules.proposal_value
(T4 Prop. 6) written out: t* = -mu sigma^2/tau^2, V* = mu Phi(-z) + tau^2/s phi(z), s^2 = tau^2 + sigma^2."""
import json, math, sys
import numpy as np
from scipy.stats import norm
P = json.load(open(sys.argv[1])); kp = P["kinds"]["local"]
MU0, TAU0, SIG, TW = kp["mu0"], kp["tau0"], kp["sigma_cmp"], kp["tau_w"]; LAM = float(P["meta"]["obs_inflation"])
rows = [json.loads(l) for l in open(sys.argv[2])]; g = float(sys.argv[3]); sig_node = float(P["sigma_node"])
items = []
for r in rows:
    n = int(r["n_group"]); ov = LAM * (SIG ** 2 + TW ** 2); var = 1 / (1 / TAU0 ** 2 + n / ov)
    items.append((n, ov * (float(r["mu"]) / var - MU0 / TAU0 ** 2)))
def vstar(mu, tau):
    s = math.sqrt(tau ** 2 + SIG ** 2); t = -mu * SIG ** 2 / tau ** 2; z = (t - mu) / s
    return mu * norm.sf(z) + tau ** 2 / s * norm.pdf(z)
out = {"g": g, "sigma_node": sig_node, "tau0_run": TAU0, "lam": LAM, "n_rows": len(items), "by_c": {}}
for c in [1.0] + [float(x) for x in sys.argv[4:]]:
    t0 = c * TAU0; vs = []; strata = {"0": [], "1-2": [], ">=3": []}
    for n, ssum in items:
        ov = LAM * (SIG ** 2 + TW ** 2); var = 1 / (1 / t0 ** 2 + n / ov); mu = var * (MU0 / t0 ** 2 + ssum / ov)
        v = vstar(mu, math.sqrt(var + TW ** 2)); vs.append(v)
        strata["0" if n == 0 else "1-2" if n <= 2 else ">=3"].append(v)
    v = np.array(vs)
    out["by_c"][f"{c:g}"] = {"tau0": t0, "tau0_in_sigma_node": t0 / sig_node,
        "Vstar_min_median_max": [float(v.min()), float(np.median(v)), float(v.max())],
        "Vstar_p05_p95_in_sigma_node": [float(np.quantile(v, .05) / sig_node), float(np.quantile(v, .95) / sig_node)],
        "n_below_g": int((v < g).sum()), "n_within_half_sigma_node_of_g": int((abs(v - g) <= 0.5 * sig_node).sum()),
        "below_g_by_stratum": {k: [int((np.array(x) < g).sum()), len(x)] for k, x in strata.items()}}
json.dump(out, sys.stdout, indent=1)
