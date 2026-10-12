#!/usr/bin/env python3
"""Analyse an E1b run: build the sibling table, score every arm, report headroom (PILOT).

Usage: python -m r1.headroom.e1b_analyze results/r1/pilot/E1b_<stamp> [--md <tables.md>]
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from r1.baselines.evaluate import evaluate_arms
from r1.branch.table import build_table
from r1.headroom.e1b_collect import build_records
from r1.theory.acceptance import NodeNoise, bayes_threshold, run_price, verify_voi


def _f(x, nd=4):
    return "–" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:+.{nd}f}" if isinstance(x, float) else str(x)


def analyse(out: Path, n_boot: int = 2000) -> dict:
    records, points = build_records(out)
    table = build_table(records)
    manifest = json.loads((out / "manifest.json").read_text())
    result = {"label": manifest.get("label", "PILOT"), "n_records": len(records), "n_points": len(table),
              "n_instances": len(set(table.instances.tolist())), "per_node": {}}
    nodes = sorted({p["features"]["node"] for p in table.projections})
    for node in nodes + ["ALL"]:
        rows = np.array([i for i, p in enumerate(table.projections) if node == "ALL" or p["features"]["node"] == node])
        sub = build_table([r for r in records if node == "ALL" or r.node == node])
        rep = evaluate_arms(sub, n_boot=n_boot)
        v, c = sub.col("verify"), sub.col("continue")
        both = ~np.isnan(sub.value[:, v]) & ~np.isnan(sub.value[:, c])
        adv = sub.value[both, v] - sub.value[both, c]
        result["per_node"][node] = {
            "n_points": len(sub), "n_instances": rep.boot.n_instances,
            "estimates": rep.boot.estimates, "ci": rep.boot.ci,
            "contrasts": rep.boot.contrasts, "contrast_ci": rep.boot.contrast_ci,
            "verify_rate": rep.verify_rate, "best_simple": rep.best_simple,
            "headroom_naive": rep.headroom_naive, "headroom_leafsplit": rep.headroom_leafsplit,
            "mean_verify_minus_continue": float(adv.mean()) if adv.size else float("nan"),
            "share_points_verify_changes_leaf": float(np.mean(adv != 0)) if adv.size else float("nan"),
            "mean_cost": {a: float(np.nanmean(sub.cost[:, sub.col(a)])) for a in ("continue", "verify")},
        }
    (out / "analysis.json").write_text(json.dumps(result, indent=1, default=lambda o: list(o) if isinstance(o, tuple) else str(o)))
    return result


def markdown(result: dict) -> str:
    lines = []
    for node, r in result["per_node"].items():
        lines.append(f"### {node}: {r['n_points']} decision points, {r['n_instances']} instances")
        lines.append("")
        nan2 = (float("nan"), float("nan"))
        ls = r["contrast_ci"].get("oracle_leafsplit - " + r["best_simple"], nan2)
        nv = r["contrast_ci"].get("oracle_naive - " + r["best_simple"], nan2)
        lines.append(f"- best simple baseline: `{r['best_simple']}`. Headroom bracket (true oracle headroom lies between, in expectation): "
                     f"leaf-split oracle {_f(r['headroom_leafsplit'])} [{_f(ls[0])}, {_f(ls[1])}] (biased down); "
                     f"naive oracle {_f(r['headroom_naive'])} [{_f(nv[0])}, {_f(nv[1])}] (biased up; its upper bound is conservative)")
        lines.append(f"- mean leaf difference verify − continue: {_f(r['mean_verify_minus_continue'])}; share of points where verify changed the leaf value: {r['share_points_verify_changes_leaf']:.2f}")
        lines.append(f"- mean worker runs per branch: continue {r['mean_cost']['continue']:.1f}, verify {r['mean_cost']['verify']:.1f} (same compute budget; verify's runs replace later trials)")
        lines.append("")
        lines.append("| Arm | value (mean Y) | 95% CI | vs rho | 95% CI | verify rate |")
        lines.append("|---|---|---|---|---|---|")
        for arm, est in r["estimates"].items():
            ci = r["ci"].get(arm, (float("nan"),) * 2)
            con = r["contrasts"].get(f"{arm} - rho")
            cci = r["contrast_ci"].get(f"{arm} - rho", (float("nan"),) * 2)
            lines.append(f"| `{arm}` | {_f(est)} | [{_f(ci[0])}, {_f(ci[1])}] | {_f(con) if con is not None else '–'} | "
                         f"[{_f(cci[0])}, {_f(cci[1])}] | {r['verify_rate'].get(arm, float('nan')):.2f} |"
                         if arm in r["verify_rate"] else
                         f"| `{arm}` | {_f(est)} | [{_f(ci[0])}, {_f(ci[1])}] | {_f(con) if con is not None else '–'} | [{_f(cci[0])}, {_f(cci[1])}] | – |")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--md", default=None)
    ap.add_argument("--n-boot", type=int, default=2000)
    args = ap.parse_args()
    out = Path(args.run_dir)
    result = analyse(out, args.n_boot)
    md = markdown(result)
    (out / "tables.md").write_text(md + "\n")
    if args.md:
        Path(args.md).write_text(md + "\n")
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
