"""Offline, descriptive, companion to diag2.py (same set-up, same grid): for each variant,
(1) the S0.4 ties at the minimum worst-stratum coverage error and their S0.5 gate status;
(2) robustness of the S0.4 maximum-likelihood fit: every grid point within 2 log-likelihood units of the S0.4
    maximum, and how many of them pass the S0.5 gate (out of sample).
Usage: python diag2_region.py <prior> <s04_rows.jsonl> <s05_calibration.jsonl>"""
import sys, math, json
src = open(__file__.replace("diag2_region.py", "diag2.py")).read().split("# ---- decomposition at the run's own prior")[0]
exec(compile(src, "diag2.py(set-up)", "exec"))
cs = np.exp(np.linspace(math.log(0.01), math.log(1000.0), 121))
lams = np.exp(np.linspace(math.log(1e-4), math.log(1000.0), 121))
out = {}
for variant in ("both", "tau0_only"):
    pts = [(float(c), float(l), *evaluate(s04_items, c, l, variant)) for c in cs for l in lams]
    llmax = max(p[2] for p in pts); wmin = min(worst(p[3]) for p in pts)
    ties = [p for p in pts if abs(worst(p[3]) - wmin) < 1e-12]
    region = [p for p in pts if p[2] >= llmax - 2.0]
    def s05(p):
        by5 = evaluate(s05_items, p[0], p[1], variant)[1]
        return {"c": p[0], "lam": p[1], "s04_loglik": p[2], "s05": {k: round(v["coverage"], 4) for k, v in by5.items()},
                "s05_gate_pass": gate(by5)}
    t5 = [s05(p) for p in ties]; r5 = [s05(p) for p in region]
    out[variant] = {"s04_max_loglik": llmax, "s04_min_worst_error": wmin,
                    "ties_at_min_worst": {"count": len(t5), "pass_s05": sum(x["s05_gate_pass"] for x in t5),
                                          "c_range": [min(x["c"] for x in t5), max(x["c"] for x in t5)],
                                          "lam_range": [min(x["lam"] for x in t5), max(x["lam"] for x in t5)]},
                    "loglik_region_2": {"count": len(r5), "pass_s05": sum(x["s05_gate_pass"] for x in r5),
                                        "pass_s05_lam_ge_1": sum(x["s05_gate_pass"] and x["lam"] >= 1 for x in r5),
                                        "count_lam_ge_1": sum(x["lam"] >= 1 for x in r5),
                                        "c_range": [min(x["c"] for x in r5), max(x["c"] for x in r5)],
                                        "lam_range": [min(x["lam"] for x in r5), max(x["lam"] for x in r5)],
                                        "points": r5}}
json.dump(out, sys.stdout, indent=1)
