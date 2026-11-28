#!/usr/bin/env python3
"""Fresh-run E0 cross-host criterion (R1-P4-E0-CRITERION, option A).

Usage:
  python compare_e0_fresh.py ADA1 ADA2 TASL1 TASL2

Reads only the four fresh `report.json` files.  The two slope criteria are checked for every
Ada-versus-TASL-7 pair (absolute 0.05).  The RPS criterion is the absolute difference of the two
host means of `lora.test.rps` (limit 3.04e-5).  Exit 0 when both parts hold.
ENGINEERING_ONLY.
"""
from __future__ import annotations

import json
import sys

SLOPE_ABS = 0.05
RPS_ABS = 3.04e-5
SLOPES = ("width_slope_vs_label", "mean_slope_vs_label")


def load(path: str) -> dict:
    d = json.load(open(path, encoding="utf-8"))
    return d["lora"]["test"]


def main(argv: list[str]) -> int:
    if len(argv) != 5:
        print(__doc__, file=sys.stderr)
        return 2
    ada = [load(argv[1]), load(argv[2])]
    tasl = [load(argv[3]), load(argv[4])]
    rows = []
    for i, a in enumerate(ada, 1):
        for j, t in enumerate(tasl, 1):
            row = {"ada_run": i, "tasl7_run": j, "checks": []}
            for metric in SLOPES:
                delta = t[metric] - a[metric]
                row["checks"].append({
                    "metric": metric, "ada": a[metric], "tasl7": t[metric],
                    "delta": delta, "tol_abs": SLOPE_ABS, "pass": abs(delta) <= SLOPE_ABS,
                })
            row["pass"] = all(c["pass"] for c in row["checks"])
            rows.append(row)
    ada_mean = sum(a["rps"] for a in ada) / len(ada)
    tasl_mean = sum(t["rps"] for t in tasl) / len(tasl)
    rps_delta = abs(ada_mean - tasl_mean)
    rps = {
        "ada_runs": [a["rps"] for a in ada],
        "tasl7_runs": [t["rps"] for t in tasl],
        "ada_mean": ada_mean, "tasl7_mean": tasl_mean,
        "abs_delta": rps_delta, "tol_abs": RPS_ABS, "pass": rps_delta <= RPS_ABS,
    }
    out = {
        "schema": "r1_p4_e0_fresh_compare/v1",
        "engineering_only": True,
        "criterion": "R1-P4-E0-CRITERION option A",
        "slope_pairs": rows,
        "slopes_pass": all(r["pass"] for r in rows),
        "rps": rps,
        "equivalent": bool(all(r["pass"] for r in rows) and rps["pass"]),
    }
    json.dump(out, sys.stdout, indent=1, sort_keys=True)
    print()
    return 0 if out["equivalent"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
