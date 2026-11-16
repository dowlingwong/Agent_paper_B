"""Build the E-SYN oracle table (build runbook P3, "done when"): ``python -m paperc.esyn.table [world ...]``.

AI-assisted (Claude, chat session, 16 Nov 2026; revised after review round 1). ENGINEERING_ONLY.

Writes ``paperC/esyn/oracle_table_v1.json`` with:

* per world: the certified oracle gain (``oracle.certify``; schema ``paperc_esyn_oracle/v2``) and, for DP worlds,
  the exact DP value and the exact value of every static threshold with h = 0;
* ``decomposition``: the B17 per-action values in the evaluation-allocation world on a third, disjoint block
  (``DECOMP_BASE`` + i, n = 20,000): verify only, re-audit only, both with final = incumbent / best, and final
  selection alone (best minus incumbent at a fixed measurement policy), also at W = 60;
* ``calibration``: the W sweep that motivated the budgets of the config worlds, rerun with the current code on the
  **selection block** (n = 1,000; selection only, no evaluation);
* ``code_sha256``: a fingerprint of the E-SYN sources, which the tests compare with the code (a stale table fails).

Runs the tasks on two processes; about 20 minutes on two CPUs.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import math
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from paperc.esyn import dp, families as F, oracle, policies as P, sim
from paperc.esyn.extra import WORLDS

PKG = Path(__file__).resolve().parent
OUT = PKG.parents[2] / "esyn" / "oracle_table_v1.json"
TABLE_SCHEMA = "paperc_esyn_oracle_table/v2"
SOURCES = ("worlds.py", "extra.py", "sim.py", "policies.py", "families.py", "dp.py", "oracle.py")
TOL, N_SELECT, N_PILOT, N_MAX = 0.05, 2000, 1000, 400_000
N_DECOMP, N_CALIB = 20_000, 1000
CALIBRATION = (("shared_error", 24), ("shared_error", 60), ("eval_allocation", 24), ("eval_allocation", 32),
               ("eval_allocation", 40), ("eval_allocation", 60))


def code_sha256() -> str:
    h = hashlib.sha256()
    for f in SOURCES:
        h.update(f.encode() + b"\0" + (PKG / f).read_bytes())
    return h.hexdigest()


def world_task(name: str) -> dict:
    w = WORLDS[name]
    t0 = time.time()
    rec = {"world": w.to_dict()}
    delta = None
    if not dp.inapplicable_reasons(w):
        sol = dp.solve(w)
        rec["dp_value"] = sol.value
        rec["dp_static_values"] = {P.Static(g, 0.0).name: dp.static_value(w, g)
                                   for g in sorted(set(F.G0) | set(dp.size_law(w).v))}
        rec["dp_gain_over_best_static"] = sol.value - max(rec["dp_static_values"].values())
        if w.channel == "budget":
            delta = rec["dp_gain_over_best_static"]
    res = oracle.certify(w, delta_Y=delta, tol=TOL, n_select=N_SELECT, n_pilot=N_PILOT, n_max=N_MAX, strict=False)
    rec["oracle"] = res
    if w.channel == "none":
        rec["null_family_eval"] = null_family_eval(res)
    if "dp_value" in rec:
        bs = P.from_name(res["selection"]["best_static"])
        rec["dp_selected_static_exact"] = dp.static_value(w, bs.g) if bs.h == 0.0 else None
        rec["dp_gain_over_selected_static"] = (rec["dp_value"] - rec["dp_selected_static_exact"]
                                               if rec["dp_selected_static_exact"] is not None else None)
    rec["seconds"] = round(time.time() - t0, 1)
    return {"kind": "world", "name": name, "rec": rec}


def policy_from_name(name: str):
    """Rebuild a policy from its name (``Static``, ``EvalAlloc``, ``Dynamic``, ``Schedule``)."""
    kind, _, rest = name.partition(":")
    if kind == "dynamic":
        x = [float(v) for v in rest.split(",")]
        return P.Dynamic(*x)
    if kind == "schedule":
        gs, hs, ts = rest.split(";")
        return P.Schedule(tuple(float(v) for v in gs.split(",")), tuple(float(v) for v in hs.split(",")), float(ts))
    return P.from_name(name)


N_NULL_FAMILY = 5000


def null_family_eval(o: dict) -> dict:
    """Strict null: each family's best member against the best static on the evaluation block (n = 5,000), with
    the share of campaigns on which it decides differently (review P3 finding 5)."""
    w = WORLDS["strict_null"]
    s = policy_from_name(o["selection"]["best_static"])
    inst = range(sim.EVAL_BASE, sim.EVAL_BASE + N_NULL_FAMILY)
    out = {}
    for fam, info in o["selection"]["member_search"]["families"].items():
        if info["best"] is not None:
            out[fam] = {"member": info["best"], **_paired(w, policy_from_name(info["best"]), s, inst)}
    return out


def _paired(w, a, b, inst) -> dict:
    va, vb = sim.campaign_values(w, a, inst), sim.campaign_values(w, b, inst)
    d = va - vb
    return {"a": a.name, "b": b.name, "diff": float(d.mean()),
            "half_width": oracle.Z95 * float(np.std(d, ddof=1)) / math.sqrt(len(d)),
            "share_differing": float(np.mean(d != 0))}


def decomposition_task(best_static: str, best_member: str) -> dict:
    """B17 per-action values in eval_allocation, on the decomposition block."""
    w = WORLDS["eval_allocation"]
    s = P.from_name(best_static)
    m = P.from_name(best_member)
    band, vmax, rmax = m.verify_band or 1.0, max(m.verify_max, 2), max(m.reaudit_max, 2)
    inst = range(sim.DECOMP_BASE, sim.DECOMP_BASE + N_DECOMP)
    pols = {"verify_only": P.EvalAlloc(m.g, m.h, band, vmax, 1, "incumbent"),
            "reaudit_only": P.EvalAlloc(m.g, m.h, 0.0, 1, rmax, "incumbent"),
            "both_final_incumbent": P.EvalAlloc(m.g, m.h, band, vmax, rmax, "incumbent"),
            "both_final_best": P.EvalAlloc(m.g, m.h, band, vmax, rmax, "best")}
    out = {"block": [sim.DECOMP_BASE, sim.DECOMP_BASE + N_DECOMP], "best_static": best_static,
           "member_thresholds": [m.g, m.h], "vs_best_static": {}, "W40": {}, "W60": {}}
    for k, p in pols.items():
        out["vs_best_static"][k] = _paired(w, p, s, inst)
    out["W40"]["final_best_minus_incumbent"] = _paired(w, pols["both_final_best"], pols["both_final_incumbent"], inst)
    w60 = dataclasses.replace(w, W=60)
    out["W60"]["final_best_minus_incumbent"] = _paired(
        w60, P.EvalAlloc(m.g, m.h, band, vmax, w.max_obs, "best"),
        P.EvalAlloc(m.g, m.h, band, vmax, w.max_obs, "incumbent"), inst)
    return {"kind": "decomposition", "rec": out}


def calibration_task(name: str, W: int) -> dict:
    w = dataclasses.replace(WORLDS[name], W=W)
    sel = oracle._Sel(w, N_CALIB)
    bs, g, h = oracle.search_static(sel)
    found = [oracle.search_members(sel, fam, bs, list(g), list(h)) for fam in F.families(w)]
    members = {k: p for _, mem, _ in found for k, p in mem.items()}
    hits = [b for b, _, _ in found if b is not None]
    bm = max(hits, key=sel.mean) if hits else None
    d = sel(bm) - sel(bs) if bm is not None else None
    return {"kind": "calibration", "name": name, "W": W,
            "rec": {"world": name, "W": W, "block": [sim.SELECT_BASE, sim.SELECT_BASE + N_CALIB],
                    "best_static": bs.name, "best_member": bm.name if bm is not None else None,
                    "gain": float(d.mean()) if d is not None else None,
                    "gain_se": float(np.std(d, ddof=1) / math.sqrt(N_CALIB)) if d is not None else None,
                    "n_members": len(members)}}


def _run(task):
    kind = task[0]
    if kind == "world":
        return world_task(task[1])
    if kind == "calibration":
        return calibration_task(task[1], task[2])
    if kind == "decomposition":
        return decomposition_task(task[1], task[2])
    raise ValueError(kind)


def build(names=None, processes: int = 2) -> dict:
    names = names or list(WORLDS)
    tasks = [("world", n) for n in names] + ([("calibration", n, W) for n, W in CALIBRATION]
                                              if set(names) == set(WORLDS) else [])
    out = {"schema": TABLE_SCHEMA, "label": "ENGINEERING_ONLY", "code_sha256": code_sha256(), "tol": TOL,
           "n_select": N_SELECT, "n_pilot": N_PILOT, "n_max": N_MAX, "worlds": {}, "calibration": []}
    with Pool(processes) as pool:
        for r in pool.imap_unordered(_run, tasks):
            if r["kind"] == "world":
                out["worlds"][r["name"]] = r["rec"]
                o = r["rec"]["oracle"]
                print(f"{r['name']}: gain {o['gain']:+.6f} ± {o['half_width']:.6f} (tolerance {o['tolerance']:.6f}, "
                      f"n {o['evaluation']['n']}, pass {o['pass']}) [{r['rec']['seconds']} s]", flush=True)
            else:
                out["calibration"].append(r["rec"])
                print(f"calibration {r['name']} W={r['W']}: gain {r['rec']['gain']}", flush=True)
    if "eval_allocation" in out["worlds"]:
        o = out["worlds"]["eval_allocation"]["oracle"]["selection"]
        out["decomposition"] = decomposition_task(o["best_static"], o["best_member"])["rec"]
        print("decomposition done", flush=True)
    out["calibration"].sort(key=lambda r: (r["world"], r["W"]))
    return out


def main(argv=None) -> Path:
    names = (argv if argv is not None else sys.argv[1:]) or None
    tab = build(names)
    if names:                                   # partial rebuild: merge into the committed table
        old = json.loads(OUT.read_text()) if OUT.exists() else {"worlds": {}}
        old["worlds"].update(tab["worlds"])
        tab = {**old, **{k: v for k, v in tab.items() if k not in ("worlds", "calibration")}, "worlds": old["worlds"]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(tab, indent=1, sort_keys=True) + "\n")
    return OUT


if __name__ == "__main__":
    print(main())
