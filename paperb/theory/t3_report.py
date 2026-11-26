#!/usr/bin/env python3
"""T3 runner: simulate the governed loop under the T2 model and write tables (ENGINEERING_ONLY).

Usage: python -m r1.theory.t3_report --out results/r1/engineering/T3_<stamp> [--campaigns 3000]
"""
from __future__ import annotations

import argparse
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from r1.theory.simulate import SimConfig, simulate

# Parameters at the scale E1 measured on digits_mlp: per-run sigma about 0.0125, local-edit rho
# about 0.8 (0.5 for structural edits), and typical true edit sizes 0.005-0.013 (tau 0.006-0.012).
SCENARIOS = [
    ("CRN, stationary proposals", dict(regime="crn", rho=0.8, mu0=0.0, tau=0.009, kappa=0.0)),
    ("CRN, harmful proposals", dict(regime="crn", rho=0.8, mu0=-0.006, tau=0.009, kappa=0.0)),
    ("CRN, diminishing returns", dict(regime="crn", rho=0.8, mu0=0.002, tau=0.006, kappa=0.4)),
    ("CRN, structural edits (rho 0.5)", dict(regime="crn", rho=0.5, mu0=-0.004, tau=0.012, kappa=0.0)),
    ("fresh draws, stationary", dict(regime="fresh", rho=0.0, mu0=0.0, tau=0.009, kappa=0.0)),
    ("fresh draws, harmful proposals", dict(regime="fresh", rho=0.0, mu0=-0.006, tau=0.009, kappa=0.0)),
    ("fresh draws, diminishing returns", dict(regime="fresh", rho=0.0, mu0=0.002, tau=0.006, kappa=0.4)),
]
POLICIES = ("rho", "always", "margin", "kg")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--campaigns", type=int, default=3000)
    ap.add_argument("--runs", type=int, default=40)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, kw in SCENARIOS:
        res = {p: simulate(SimConfig(policy=p, runs=args.runs, seed=args.seed, **kw), n_campaigns=args.campaigns)
               for p in POLICIES}
        acc = np.array(res["rho"]["acceptance_of_true_improvements_by_trial"], dtype=float)
        rows.append({"scenario": name, "config": kw, "results": res,
                     "acceptance_rho_windows": [float(np.nanmean(acc[:5])), float(np.nanmean(acc[5:15])),
                                                float(np.nanmean(acc[15:30]))]})
    lines = ["| Scenario | ρ (never verify) | always verify | margin-triggered | KG index | false-keep rate under ρ | record bias at end under ρ | acceptance of true improvements under ρ, trials 1–5 / 6–15 / 16–30 |",
             "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        cells = []
        for p in POLICIES:
            x = r["results"][p]
            cells.append(f"{1000 * x['mean_final']:+.1f} ± {1000 * x['se_final']:.1f} (v {x['mean_verifies']:.1f})")
        rho = r["results"]["rho"]
        a = r["acceptance_rho_windows"]
        lines.append(f"| {r['scenario']} | " + " | ".join(cells) +
                     f" | {rho['false_keep_rate']:.2f} | {1000 * rho['mean_record_bias_end']:+.1f} | {a[0]:.2f} / {a[1]:.2f} / {a[2]:.2f} |")
    table = "\n".join(lines)
    manifest = {"label": "ENGINEERING_ONLY", "utc": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
                "campaigns": args.campaigns, "runs": args.runs, "seed": args.seed,
                "host": {"platform": platform.platform(), "python": platform.python_version()},
                "units": "final true gain J(c_T) - J(c_0) in 1e-3 metric units; v = mean verifies per campaign"}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (out / "results.json").write_text(json.dumps(rows, indent=1) + "\n")
    (out / "table.md").write_text(table + "\n")
    print(table)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
