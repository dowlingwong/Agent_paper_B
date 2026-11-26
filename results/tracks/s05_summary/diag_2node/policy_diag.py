"""S0.5 two-node diagnostic (descriptive): do a2u and static:<thr>,0 decide identically; V* - g; which budget binds.
Usage: python policy_diag.py <s05_dir> <static_threshold>.  Reads only roots.jsonl, s05b_truncated.jsonl, manifest.json."""
import json, sys, collections
import numpy as np
d, thr_static = sys.argv[1], float(sys.argv[2])
man = json.load(open(f"{d}/manifest.json"))
R = [json.loads(l) for l in open(f"{d}/roots.jsonl")]
T = [json.loads(l) for l in open(f"{d}/s05b_truncated.jsonl")]
g = float(man["g0"]); sig = float(man["sigma_node"]); W = int(man["W"]); cap = int(man["llm_cap"])
band = 0.5 * sig
q = lambda a: {k: float(np.quantile(a, p)) for k, p in (("min", 0), ("p05", .05), ("p25", .25), ("median", .5),
                                                         ("p75", .75), ("p95", .95), ("max", 1))} if len(a) else None
out = {"node": man.get("node"), "g_a2u": g, "threshold_static": thr_static, "sigma_node": sig,
       "band_half_width": band, "W_pilot": W, "llm_cap": cap}
rep0 = [r for r in R if int(r.get("rep", 0)) == 0]
pols = sorted({r["policy"] for r in rep0}); out["policies_rep0"] = pols
by = {(r["policy"], r["instance_id"]): r for r in rep0}
inst = sorted({r["instance_id"] for r in rep0})
seq = lambda r: [(x["epoch"], x["action"], x.get("skip_reason")) for x in r["decisions"]]
same = []; diffs = []
for i in inst:
    a, s = by[(pols[0], i)], by[(pols[1], i)]
    eq = seq(a) == seq(s) and a["runs_used"] == s["runs_used"] and a["y_terminal"] == s["y_terminal"]
    same.append(eq)
    if not eq:
        first = next((k for k, (u, v) in enumerate(zip(seq(a), seq(s))) if u != v), min(len(seq(a)), len(seq(s))))
        diffs.append({"instance": i, "first_diff_index": first, "len": [len(seq(a)), len(seq(s))],
                      "runs_used": [a["runs_used"], s["runs_used"]], "y_terminal": [a["y_terminal"], s["y_terminal"]]})
out["n_instances_rep0"] = len(inst); out["n_identical_instances"] = int(sum(same)); out["differing"] = diffs
# per policy action counts, budgets
agg = {}
for p in pols:
    rr = [r for r in rep0 if r["policy"] == p]
    c = collections.Counter((x["epoch"], x["action"]) for r in rr for x in r["decisions"])
    sk = collections.Counter(x.get("skip_reason") for r in rr for x in r["decisions"] if x["epoch"] == "E1" and x["action"] == "skip")
    e1n = [sum(x["epoch"] == "E1" for x in r["decisions"]) for r in rr]
    ex = [sum(x["epoch"] == "E1" and x["action"] == "execute" for x in r["decisions"]) for r in rr]
    agg[p] = {"actions": {f"{k[0]}:{k[1]}": v for k, v in sorted(c.items())}, "E1_skip_reasons": dict(sk),
              "execute_share_per_instance": [min(e / n for e, n in zip(ex, e1n)), max(e / n for e, n in zip(ex, e1n))],
              "execute_share_total": sum(ex) / sum(e1n),
              "runs_used_range": [min(r["runs_used"] for r in rr), max(r["runs_used"] for r in rr)],
              "worker_budget_exhausted": sum(r["runs_used"] >= W for r in rr),
              "llm_cap_reached": sum(r["llm_calls"] >= cap for r in rr),
              "binding_flag_true": sum(bool(r["binding"]) for r in rr)}
out["by_policy"] = agg
# V* - g over eligible E1 decisions (a2u); margins of each policy
for p in pols:
    rr = [r for r in rep0 if r["policy"] == p]
    e1 = [x for r in rr for x in r["decisions"] if x["epoch"] == "E1" and x.get("eligible") and x.get("index_value") is not None]
    e2 = [x for r in rr for x in r["decisions"] if x["epoch"] == "E2" and x.get("eligible") and x.get("margin") is not None]
    v = np.array([float(x["index_value"]) for x in e1]); m1 = np.array([float(x["margin"]) for x in e1])
    m2 = np.array([float(x["margin"]) for x in e2])
    out.setdefault("margins", {})[p] = {"n_E1_eligible": len(v), "E1_margin": q(m1), "n_E2_eligible": len(m2),
                                        "E2_margin": q(m2), "E2_within_band_of_0": int((np.abs(m2) <= band).sum()),
                                        "E2_margin_negative": int((m2 < 0).sum())}
    if p == "a2u":
        out["a2u_Vstar"] = q(v); out["Vstar_minus_g"] = q(v - g); out["Vstar_minus_static_threshold"] = q(v - thr_static)
        out["n_below_g"] = int((v < g).sum()); out["n_between_thresholds"] = int(((v >= g) & (v < thr_static)).sum())
        out["n_within_band_of_g"] = int((np.abs(v - g) <= band).sum())
        out["n_within_band_of_static"] = int((np.abs(v - thr_static) <= band).sum())
        out["Vstar_minus_g_in_sigma_node"] = q((v - g) / sig)
# truncated W: binding share and policy agreement per W
tw = collections.defaultdict(dict)
for t in T:
    if int(t.get("rep", 0)) == 0:
        tw[int(t["W"])][(t["policy"], t["instance_id"])] = t
trunc = {}
for w, dd in sorted(tw.items()):
    ii = sorted({k[1] for k in dd})
    agree = sum(dd[(pols[0], i)]["y_terminal"] == dd[(pols[1], i)]["y_terminal"] and
                dd[(pols[0], i)]["runs_used"] == dd[(pols[1], i)]["runs_used"] for i in ii)
    trunc[w] = {"rep0_instances": len(ii), "policy_identical_y_and_runs": agree,
                "binding_share_rep0": {p: sum(bool(dd[(p, i)]["binding"]) for i in ii) / len(ii) for p in pols}}
out["truncated"] = trunc
json.dump(out, sys.stdout, indent=1)
