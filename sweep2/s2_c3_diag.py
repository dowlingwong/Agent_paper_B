#!/usr/bin/env python3
"""S2-C3 H200-repeat diagnostic (R1-S2C3-DIAG): compare two H200 runs of the same 12 B2 off roots.

Decision rule (row text, applied exactly):
  sampling uncertainty (continue launch with disclosure) if
    mean |Delta final_y| H200-vs-H200 >= half of the H200-vs-B2 mean, OR any instance |Delta| > 0.02, OR any of the
    three diagnostic rates differs by more than 10 %;
  otherwise (H200-vs-H200 near-identical but both differ from B2) => software-stack difference: STOP and investigate.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s2_c3_compare as cmp  # noqa: E402

H2B_MEAN = 0.0104012  # S2-C3 run 1 vs B2, from S2_C3_RESULTS.md
RATE_KEYS = ("invalid", "duplicates", "noops")


def _instances(paths):
    collected = cmp.collect([Path(p) for p in paths])
    return collected["instances"], collected


def compare(run1_paths, run2_paths, out: Path) -> dict:
    a, _ = _instances(run1_paths)
    b, _ = _instances(run2_paths)
    if set(a) != set(b) or len(a) != 12:
        raise cmp.Stop(f"STOP: instance sets differ or not 12: {sorted(set(a) ^ set(b))}")
    deltas = {inst: abs(float(a[inst]["final_y"]) - float(b[inst]["final_y"])) for inst in sorted(a)}
    mean_abs = sum(deltas.values()) / len(deltas)
    max_abs = max(deltas.values())
    max_inst = max(deltas, key=deltas.get)
    totals_a = {k: sum(int((a[i].get("diagnostics") or {}).get(k, 0)) for i in a) for k in RATE_KEYS}
    totals_b = {k: sum(int((b[i].get("diagnostics") or {}).get(k, 0)) for i in b) for k in RATE_KEYS}
    rate_diffs = {}
    for k in RATE_KEYS:
        ra = totals_a[k] / 240 if 240 else 0
        rb = totals_b[k] / 240 if 240 else 0
        rate_diffs[k] = {"run1_rate": round(ra, 6), "run2_rate": round(rb, 6),
                         "relative_diff": round(abs(rb - ra) / ra, 6) if ra else None}
    sampling_reasons = []
    if mean_abs >= H2B_MEAN / 2:
        sampling_reasons.append(f"mean H2H |Delta| {mean_abs:.6f} >= half of H2B {H2B_MEAN/2:.6f}")
    if max_abs > 0.02:
        sampling_reasons.append(f"instance {max_inst} |Delta| {max_abs:.6f} > 0.02")
    for k, d in rate_diffs.items():
        if d["relative_diff"] is not None and d["relative_diff"] > 0.10:
            sampling_reasons.append(f"{k} rate differs by {d['relative_diff']*100:.1f}% > 10%")
    verdict = "SAMPLING_UNCERTAINTY" if sampling_reasons else "STACK_DIFFERENCE_STOP"
    payload = {"schema": "s2_c3_diag/1", "verdict": verdict, "mean_abs_h2h": round(mean_abs, 7),
               "max_abs_h2h": round(max_abs, 7), "max_instance": max_inst, "mean_abs_h2b": H2B_MEAN,
               "half_h2b": H2B_MEAN / 2, "rate_diffs": rate_diffs, "sampling_reasons": sampling_reasons,
               "per_instance": deltas, "totals_run1": totals_a, "totals_run2": totals_b}
    lines = ["# S2-C3 H200-repeat diagnostic (ENGINEERING_ONLY)", "",
             f"**Verdict: {verdict}**", "",
             f"- mean |Delta final_y| H200-vs-H200 = **{mean_abs:.7f}** (half of H2B mean = {H2B_MEAN/2:.7f})",
             f"- max |Delta| = **{max_abs:.7f}** on {max_inst} (bound 0.02)",
             "- diagnostic rate differences (relative): "
             + ", ".join(f"{k} {v['relative_diff']*100:.1f}%" if v['relative_diff'] is not None else f"{k} n/a"
                         for k, v in rate_diffs.items()),
             "", "## Rule application", "",
             *([f"- {r}" for r in sampling_reasons] or ["- no sampling-uncertainty condition met -> stack difference STOP"]),
             "", "| instance | |Delta| |", "|---|---|",
             *[f"| {i} | {deltas[i]:.7f} |" for i in sorted(deltas)]]
    out.write_text("\n".join(lines) + "\n")
    return payload


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run1", nargs=3)
    ap.add_argument("run2", nargs=3)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    try:
        payload = compare(a.run1, a.run2, Path(a.out))
    except cmp.Stop as exc:
        print(str(exc), file=sys.stderr); return 2
    print(json.dumps({k: payload[k] for k in ("verdict", "mean_abs_h2h", "max_abs_h2h", "sampling_reasons")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
