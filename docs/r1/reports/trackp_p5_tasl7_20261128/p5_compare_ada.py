"""Ada RTX 6000 host-equivalence check: compare one E0 v2 DRYRUN report with the TASL-7 reference.

Adapted from docs/r1/reports/trackp_h200_20261118/stages/e0_h200/compare.py, whose reference.json is the
byte-identical TASL-7 `run/report.json` (review TRACKP_H200_E0_PRE_SUBMIT_REVIEW_20261118). The tolerances are
the same pre-declared three criteria. Usage: python compare_ada.py <reference report.json> <ada report.json>.
Exit 0 = equivalent, 1 = a miss (STOP for the author).
"""
import json
import sys

ABS = {"width_slope_vs_label": 0.05, "mean_slope": 0.05}
REL = {"rps": 0.10}
DESCRIPTIVE = ["width_slope", "width_ratio", "rps_interp", "rps_extrap", "mean_slope_vs_label",
               "label_width_slope_vs_s", "label_mean_slope_vs_m", "n"]


def main(reference_path, ada_path):
    p, t = json.load(open(reference_path)), json.load(open(ada_path))
    pt, tt = p["lora"]["test"], t["lora"]["test"]
    rows = []
    for k, tol in ABS.items():
        d = tt[k] - pt[k]
        rows.append({"metric": k, "reference": pt[k], "ada": tt[k], "delta": d, "tol_abs": tol,
                     "pass": abs(d) <= tol})
    for k, tol in REL.items():
        r = abs(tt[k] - pt[k]) / abs(pt[k])
        rows.append({"metric": k, "reference": pt[k], "ada": tt[k], "rel_diff": r, "tol_rel": tol,
                     "pass": r <= tol})
    ok = all(r["pass"] for r in rows)
    desc = {k: {"reference": pt.get(k), "ada": tt.get(k)} for k in DESCRIPTIVE}
    for blk in ("head_fit", "lora"):
        for k in ("best_step", "stopped_at", "early_stopped"):
            desc[f"{blk}.{k}"] = {"reference": p[blk].get(k), "ada": t[blk].get(k)}
    desc["head_fit.test"] = {"reference": p["head_fit"]["test"], "ada": t["head_fit"]["test"]}
    json.dump({"equivalent": ok, "criteria": rows, "descriptive": desc, "comparator": "TASL-7 reference",
               "candidate": "Ada RTX 6000 Ada Generation (sm_89)"}, sys.stdout, indent=1, sort_keys=True)
    print()
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
