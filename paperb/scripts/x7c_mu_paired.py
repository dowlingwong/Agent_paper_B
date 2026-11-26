"""Paired B1 mu_hat differences, finalist minus each anchor (post hoc; for the cross-proposer disclosure paragraph).

AI-assisted (Claude). Not part of the declared X.7(c) decision. Uses the X.7(c) appendix's inputs, thinking-off
filter, paired cluster bootstrap and seed (r1/scripts/x7c_appendix.py), so the intervals are those that script would
give for mu_hat differences.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import x7c_appendix as X  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--b1-manifests", type=Path, required=True)
    ap.add_argument("--b1-usage", type=Path, required=True)
    ap.add_argument("--b1-analysis", type=Path, required=True)
    ap.add_argument("--json", type=Path, required=True)
    a = ap.parse_args(argv)
    usage = X.usage_trials(a.b1_usage)
    analysis = {r["candidate"]: r for r in json.loads(a.b1_analysis.read_text())["rows"]}
    rows, ids = {}, None
    for m in json.loads(a.b1_manifests.read_text())["manifests"]:
        name = m["candidate"]
        if name not in (X.FINALIST, *X.ANCHORS):
            continue
        # The appendix's input checks (x7c_appendix.main).
        if m.get("execution_label") != "EVIDENCE" or m.get("phase") != "b1" or m.get("status") != "COMPLETE":
            raise SystemExit(f"STOP: {name} is not a complete EVIDENCE B1 manifest")
        off = {i: t for (c, mode, i), t in usage.items() if c == name and mode == "off"}
        if len(off) != 12:
            raise SystemExit(f"STOP: {name} has {len(off)} off roots in the usage table")
        if sum(t for (c, _m, _i), t in usage.items() if c == name) != m["diagnostics"]["trials"]:
            raise SystemExit(f"STOP: {name} usage trials differ from the manifest")
        ids = ids or sorted(off)
        if sorted(off) != ids:
            raise SystemExit("STOP: rows do not share instance ids")
        rows[name] = X.row_data([r for r in m["audited_proposals"] if r["mode"] == "off"], off)
        mu = X.quantities(rows[name], ids)["mu_hat"]
        if abs(mu - analysis[name]["mu_hat"]) > 1e-12:
            raise SystemExit(f"STOP: {name} mu_hat differs from the B1 analysis")
    draws = X.bootstrap(rows, ids, np.random.default_rng(X.SEED))
    point = {n: X.quantities(cl, ids)["mu_hat"] for n, cl in rows.items()}
    out = {"post_hoc": "not part of the declared X.7(c) decision; computed for the cross-proposer disclosure paragraph",
           "python": sys.version.split()[0], "numpy": np.__version__, "seed": X.SEED, "resamples": X.B, "inputs": {"b1_manifests": X.sha(a.b1_manifests), "b1_usage": X.sha(a.b1_usage),
                      "b1_analysis": X.sha(a.b1_analysis)},
           "mu_hat": point, "differences": {}}
    lines = ["Post hoc (not part of the declared X.7(c) decision): paired B1 mu_hat differences, finalist minus anchor.", "",
             "| anchor | finalist mu_hat | anchor mu_hat | difference | 95 % paired cluster CI |", "|---|---|---|---|---|"]
    for anchor in X.ANCHORS:
        d = draws[X.FINALIST]["mu_hat"] - draws[anchor]["mu_hat"]
        lo, hi, nan = X.interval(d, 0.95)
        diff = point[X.FINALIST] - point[anchor]
        out["differences"][anchor] = {"difference": diff, "ci95": [lo, hi], "nan_resamples": nan,
                                      "excludes_zero": bool(lo > 0 or hi < 0)}
        lines.append(f"| {anchor} | {point[X.FINALIST]:.6f} | {point[anchor]:.6f} | {diff:.6f} | [{lo:.6f}, {hi:.6f}] |")
    a.json.write_text(json.dumps(out, indent=1, sort_keys=True), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
