"""Build the E-SYN oracle table (build runbook P3, "done when"): ``python -m paperc.esyn.table``.

AI-assisted (Claude, chat session, 16 Nov 2026). ENGINEERING_ONLY. Writes ``paperC/esyn/oracle_table_v1.json``:
per world the certified oracle gain of the best member over the best static rule (``oracle.certify``), and for
DP worlds the exact DP value and the exact value of the selected static rule. Runtime: minutes on one CPU.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from paperc.esyn import dp, families
from paperc.esyn.extra import WORLDS
from paperc.esyn.oracle import certify

OUT = Path(__file__).resolve().parents[3] / "esyn" / "oracle_table_v1.json"
TABLE_SCHEMA = "paperc_esyn_oracle_table/v1"


def build(names=None, *, tol: float = 0.05, n_select: int = 2000, n_pilot: int = 1000, n_max: int = 200_000) -> dict:
    out = {"schema": TABLE_SCHEMA, "label": "ENGINEERING_ONLY", "tol": tol, "n_select": n_select, "n_pilot": n_pilot,
           "n_max": n_max, "worlds": {}}
    for name in names or list(WORLDS):
        w = WORLDS[name]
        t0 = time.time()
        rec = {"world": w.to_dict()}
        delta = None
        if not dp.applicable(w):
            sol = dp.solve(w)
            rec["dp_value"] = sol.value
            statics = families.statics(w)
            rec["dp_static_values"] = {s.name: dp.static_value(w, s.g) for s in statics if s.h == 0.0}
            if w.channel == "budget":
                delta = sol.value - max(rec["dp_static_values"].values())
            rec["dp_gain_over_best_static"] = sol.value - max(rec["dp_static_values"].values())
        res = certify(w, families.statics(w), lambda best, w=w: families.members(w, best), delta_Y=delta, tol=tol,
                      n_select=n_select, n_pilot=n_pilot, n_max=n_max, strict=False)
        rec["oracle"] = res
        if "dp_static_values" in rec:
            bs = res["selection"]["best_static"]
            rec["dp_gain_over_selected_static"] = (rec["dp_value"] - rec["dp_static_values"][bs]
                                                   if bs in rec["dp_static_values"] else None)
        rec["seconds"] = round(time.time() - t0, 1)
        out["worlds"][name] = rec
        print(f"{name}: gain {res['gain']:+.6f} ± {res['half_width']:.6f} (tolerance {res['tolerance']:.6f}, "
              f"n {res['evaluation']['n']}, pass {res['pass']}) [{rec['seconds']} s]", flush=True)
    return out


def main(argv=None) -> Path:
    names = (argv if argv is not None else sys.argv[1:]) or None
    tab = build(names)
    if names:                                   # partial rebuild: merge into the committed table
        old = json.loads(OUT.read_text()) if OUT.exists() else {"worlds": {}}
        old["worlds"].update(tab["worlds"])
        tab = {**tab, "worlds": old["worlds"]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(tab, indent=1, sort_keys=True) + "\n")
    return OUT


if __name__ == "__main__":
    print(main())
