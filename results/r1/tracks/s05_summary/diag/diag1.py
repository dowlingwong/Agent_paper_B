"""S0.5 digits diagnostic 1 (descriptive): why a2u and static:0.00198,0 decide identically."""
import json, sys, collections, statistics as st
import numpy as np
d = sys.argv[1]
man = json.load(open(f"{d}/manifest.json"))
R = [json.loads(l) for l in open(f"{d}/roots.jsonl")]
g = float(man["g0"]); sig = float(man["sigma_node"]); thr_static = 0.00198; W = int(man["W"])
band = 0.5 * sig
out = {"g_a2u": g, "threshold_static": thr_static, "sigma_node": sig, "band_half_width": band, "W": W,
       "llm_cap": man["llm_cap"]}
per = []
vstar = []; reasons = collections.Counter()
for r in R:
    if int(r.get("rep", 0)) != 0:
        continue
    dec = r["decisions"]; e1 = [x for x in dec if x["epoch"] == "E1"]
    ex = sum(x["action"] == "execute" for x in e1); sk = sum(x["action"] == "skip" for x in e1)
    rs = collections.Counter(x.get("skip_reason") for x in e1 if x["action"] == "skip")
    per.append({"policy": r["policy"], "instance": r["instance_id"], "e1": len(e1), "execute": ex, "skip": sk,
                "skip_reasons": dict(rs), "runs_used": r["runs_used"], "llm_calls": r["llm_calls"],
                "binding": r["binding"], "budget_exhausted_worker": r["runs_used"] >= W,
                "llm_cap_reached": r["llm_calls"] >= man["llm_cap"]})
    if r["policy"] == "a2u":
        reasons.update(rs)
        for x in e1:
            if x.get("eligible") and x.get("index_value") is not None:
                vstar.append(float(x["index_value"]))
v = np.array(vstar)
gap = v - g
def q(a): return {k: float(np.quantile(a, p)) for k, p in (("min", 0), ("p05", .05), ("p25", .25), ("median", .5), ("p75", .75), ("p95", .95), ("max", 1))}
out["a2u_eligible_E1_decisions"] = int(len(v))
out["a2u_skip_reasons"] = dict(reasons)
out["Vstar_minus_g"] = q(gap)
out["Vstar_minus_static_threshold"] = q(v - thr_static)
out["n_between_thresholds"] = int(((v >= g) & (v < thr_static)).sum())
out["n_within_band_of_g"] = int((np.abs(v - g) <= band).sum())
out["n_within_band_of_static"] = int((np.abs(v - thr_static) <= band).sum())
out["n_below_g"] = int((v < g).sum())
agg = collections.defaultdict(lambda: collections.Counter())
for p in per:
    a = agg[p["policy"]]
    a["instances"] += 1; a["e1"] += p["e1"]; a["execute"] += p["execute"]; a["skip"] += p["skip"]
    a["worker_budget_exhausted"] += p["budget_exhausted_worker"]; a["llm_cap_reached"] += p["llm_cap_reached"]
    a["binding_W40"] += bool(p["binding"])
out["by_policy"] = {k: dict(v) for k, v in agg.items()}
out["runs_used_range"] = {pol: [min(p["runs_used"] for p in per if p["policy"] == pol), max(p["runs_used"] for p in per if p["policy"] == pol)] for pol in agg}
out["per_instance"] = per
json.dump(out, sys.stdout, indent=1)
