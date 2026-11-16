"""Runner and ladder table (build runbook P4; revised after review round 1): ``python -m paperc.runner [world ...]``.

AI-assisted (Claude, chat session, 16 Nov 2026). ENGINEERING_ONLY.

``run`` runs a policy on an E-SYN world for a set of instances and returns the paired campaign values Y (the exact
value of the final configuration minus y0, not the audited terminal value: on E-SYN the true value is known),
optionally with the ``spt_transition/v1`` rows. Recorded campaigns use instances 0 .. 9999 (instance seeds
50000 + i, the P2 registry's Paper C block); the tuning and test campaigns of the ladder are index ranges under
the E-SYN root key (``policies.DEV_BASE`` + i, ``policies.TEST_BASE`` + i; claimed in the registry) and are not
recorded, which is a declared deviation from the runbook's wording. Every rung and reference row is additionally
run on ``N_RECORDS`` recorded campaigns that must pass ``check_campaign`` with the registry and propensity replay.

``build_world`` tunes every rung on the world's dev campaigns (``policies`` docstring: equal budgets), evaluates
rungs and references on ``N_TEST`` paired test campaigns, and reports per row the test value, mean runs, gain over
N1, gap to the P3 oracle member (a family-best lower bound, which a rung may beat), the dev value and dev gain over
N1 with its standard error, and the tuning charge. ``main`` writes ``paperC/esyn/ladder_table_v1.json`` with a
code fingerprint (also stamped on every world) and the fingerprint of the oracle table it read.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from paperc import policies as L
from paperc import schema as S
from paperc import seeds as SD
from paperc.esyn import dp, sim, table as OT
from paperc.esyn import policies as EP
from paperc.esyn.extra import WORLDS

PKG = Path(__file__).resolve().parent
OUT = PKG.parents[1] / "esyn" / "ladder_table_v1.json"
LADDER_SCHEMA = "paperc_ladder_table/v2"
N_TEST = 10_000
N_RECORDS = 3
Z95 = 1.959963984540054


def code_sha256() -> str:
    files = [PKG / "policies.py", PKG / "runner.py", PKG / "schema.py", PKG / "seeds.py",
             PKG.parents[1] / "seeds" / "registry_v1.json", *(OT.PKG / s for s in OT.SOURCES)]
    h = hashlib.sha256()
    for f in files:
        h.update(f.name.encode() + b"\0" + f.read_bytes())
    return h.hexdigest()


def run(world, policy, instances, *, record: bool = False):
    """(Y per campaign, runs used per campaign, rows)."""
    res = [sim.run_campaign(world, policy, i, record=record) for i in instances]
    return (np.array([r.Y for r in res]), np.array([r.runs_used for r in res]),
            [row for r in res for row in r.rows])


def paired(a: np.ndarray, b: np.ndarray) -> dict:
    d = a - b
    return {"diff": float(d.mean()), "half_width": Z95 * float(np.std(d, ddof=1)) / math.sqrt(len(d)),
            "share_differing": float(np.mean(d != 0))}


def tune_rungs(world):
    """Every rung tuned on dev; returns (policies, facts per row, dev cache, tuners)."""
    cache = L.DevCache(world)
    dev = cache.instances
    pols, facts, tuners = {"N0": L.N0()}, {}, {}

    def tuner(key):
        tuners[key] = L.Tuner(cache)
        return tuners[key]
    pols["N1"] = L.tune_static(tuner("N1"))
    pols["N2"] = L.tune_static(tuner("N2"), h_fixed=0.0)
    pols["N3"], facts["N3"] = L.tune_n3(tuner("N3"), world)
    pols["N2b"], facts["N2b"] = L.fit_n2b(world, L.dev_trace(world, dev), tuner("N2b"))
    pols["N4"], facts["N4"] = L.fit_n4(world, L.dev_trace(world, dev, wide=True), dev)
    pols["margin"] = L.tune_from_coarse(tuner("margin"), lambda x: L.BudgetMargin(max(x[0], 0.0), x[1], x[2]),
                                        [0.0], [0.002])
    if "verify" in world.epochs:
        s = world.base.sigma_cmp
        pols["sprt"] = L.tune_from_coarse(
            tuner("sprt"), lambda x: L.SPRT(max(x[0], 0.0), x[1], max(x[2], 1e-5), min(max(x[3], 0.01), 0.45)),
            [s / 2, 0.1], [s / 4, 0.05])
        pols["race"] = L.tune_from_coarse(tuner("race"), lambda x: L.Race(max(x[0], 0.0), x[1], max(x[2], 0.0)),
                                          [1.0], [0.5])
        pols["kg"] = L.tune_from_coarse(tuner("kg"), lambda x: L.KGVerify(max(x[0], 0.0), x[1], max(x[2], 0.0)),
                                        [0.0001], [0.0001])
    pols["rawkeep"] = L.tune_from_coarse(tuner("rawkeep"), lambda x: L.RawKeep(max(x[0], 0.0), x[1]), [], [])
    pols["shrink"] = L.tune_from_coarse(tuner("shrink"), lambda x: L.ShrinkRefit(max(x[0], 0.0), x[1], max(x[2], 0.0)),
                                        [1.0], [0.5])
    for k, t in tuners.items():
        facts.setdefault(k, {})
        facts[k].update({"charged": len(t.charged), "budget": t.budget})
    facts["N2b"]["dev_fit"] = "head weights fitted on the dev trace (not counted as candidates)"
    facts["N4"]["dev_fit"] = "law estimated on the dev trace with W = llm_cap (no candidates)"
    return pols, facts, cache


def build_world(name: str) -> dict:
    w = WORLDS[name]
    t0 = time.time()
    pols, facts, cache = tune_rungs(w)
    otab = json.loads(OT.OUT.read_text())
    oracle_name = otab["worlds"][name]["oracle"]["selection"]["best_member"]
    test = range(L.TEST_BASE, L.TEST_BASE + N_TEST)
    refs = {"oracle": OT.policy_from_name(oracle_name, w)}
    if not dp.inapplicable_reasons(w):
        refs["dp"] = EP.Threshold(dp.solve(w).table)
    res = {k: run(w, p, test)[:2] for k, p in {**pols, **refs}.items()}
    # random references: q calibrated on the test block to the matched row's mean runs (runs are not outcomes)
    n1 = pols["N1"]
    refs["random_N1"] = L.calibrate_q(w, n1.h, float(res["N1"][1].mean()), test)
    if name == "budget":
        refs["random_N4"] = L.calibrate_q(w, 0.0, float(res["N4"][1].mean()), test)
    for k in ("random_N1", "random_N4"):
        if k in refs:
            res[k] = run(w, refs[k], test)[:2]
    allp = {**pols, **refs}
    reg = SD.Registry.load()
    rows_out = {}
    for k, p in allp.items():
        _, _, recs = run(w, p, range(N_RECORDS), record=True)
        dev_vals = cache.values(p) if k not in ("oracle", "dp") and not k.startswith("random") else None
        d_dev = (dev_vals - cache.values(n1)) if dev_vals is not None else None
        rows_out[k] = {
            "kind": "reference" if k in refs or k in ("rawkeep", "shrink") else "rung",
            "policy": p.name, "policy_sha": getattr(p, "sha", None),
            "value": float(res[k][0].mean()), "mean_runs": float(res[k][1].mean()),
            "vs_N1": paired(res[k][0], res["N1"][0]), "gap_to_oracle": paired(res["oracle"][0], res[k][0]),
            "vs_dp": paired(res[k][0], res["dp"][0]) if "dp" in res else None,
            "dev_value": float(dev_vals.mean()) if dev_vals is not None else None,
            "dev_vs_N1": ({"diff": float(d_dev.mean()), "se": float(np.std(d_dev, ddof=1) / math.sqrt(len(d_dev)))}
                          if d_dev is not None else None),
            "tuning": facts.get(k),
            "record_violations": len(S.check_campaign(recs, registry=reg, behaviour=sim.behaviour_for(p)))}
    return {"world": name, "test": [test.start, test.stop], "dev": [cache.instances.start, cache.instances.stop],
            "dev_ranges_run": sorted(cache.runs), "rows": rows_out, "oracle_member": oracle_name,
            "code_sha256": code_sha256(), "seconds": round(time.time() - t0, 1)}


def main(argv=None) -> Path:
    names = (argv if argv is not None else sys.argv[1:]) or list(WORLDS)
    tab = {"schema": LADDER_SCHEMA, "label": "ENGINEERING_ONLY", "code_sha256": code_sha256(),
           "oracle_table_sha256": json.loads(OT.OUT.read_text())["code_sha256"], "n_test": N_TEST,
           "n_dev": L.N_DEV, "tune_budget": L.TUNE_BUDGET, "worlds": {}}
    with Pool(2) as pool:
        for r in pool.imap_unordered(build_world, names):
            tab["worlds"][r["world"]] = r
            g = {k: f"{v['vs_N1']['diff']:+.5f}" for k, v in r["rows"].items()}
            print(r["world"], g, f"[{r['seconds']} s]", flush=True)
    if set(names) != set(WORLDS) and OUT.exists():
        old = json.loads(OUT.read_text())
        old["worlds"].update(tab["worlds"])
        tab["worlds"] = old["worlds"]
    OUT.write_text(json.dumps(tab, indent=1, sort_keys=True) + "\n")
    return OUT


if __name__ == "__main__":
    print(main())
