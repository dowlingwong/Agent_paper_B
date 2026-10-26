"""TASL-7 host-equivalence check: compare one E0 v2 DRYRUN report with the portal's (PREDECLARATION.md).

AI-assisted (Claude). Usage: python compare.py <portal report.json> <tasl7 report.json> > comparison.json
Tolerances are fixed in PREDECLARATION.md before the run; exit 0 = equivalent, 1 = a miss (STOP for the author).
"""
import json
import sys

ABS = {"width_slope_vs_label": 0.05, "mean_slope": 0.05}
REL = {"rps": 0.10}
DESCRIPTIVE = ["width_slope", "width_ratio", "rps_interp", "rps_extrap", "mean_slope_vs_label",
               "label_width_slope_vs_s", "label_mean_slope_vs_m", "n"]


def main(portal_path, tasl7_path):
    p, t = json.load(open(portal_path)), json.load(open(tasl7_path))
    pt, tt = p["lora"]["test"], t["lora"]["test"]
    rows, ok = [], True
    for k, tol in ABS.items():
        d = tt[k] - pt[k]
        rows.append({"metric": k, "portal": pt[k], "tasl7": tt[k], "delta": d, "tol_abs": tol, "pass": abs(d) <= tol})
    for k, tol in REL.items():
        r = abs(tt[k] - pt[k]) / abs(pt[k])
        rows.append({"metric": k, "portal": pt[k], "tasl7": tt[k], "rel_diff": r, "tol_rel": tol, "pass": r <= tol})
    ok = all(r["pass"] for r in rows)
    desc = {k: {"portal": pt.get(k), "tasl7": tt.get(k)} for k in DESCRIPTIVE}
    for blk in ("head_fit", "lora"):
        for k in ("best_step", "stopped_at", "early_stopped"):
            desc[f"{blk}.{k}"] = {"portal": p[blk].get(k), "tasl7": t[blk].get(k)}
    desc["head_fit.test"] = {"portal": p["head_fit"]["test"], "tasl7": t["head_fit"]["test"]}
    json.dump({"equivalent": ok, "criteria": rows, "descriptive": desc}, sys.stdout, indent=1, sort_keys=True)
    print()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
