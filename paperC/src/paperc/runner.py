"""Runner and ladder table (build runbook P4): ``python -m paperc.runner [world ...]``.

AI-assisted (Claude, chat session, 16 Nov 2026). ENGINEERING_ONLY.

``run`` runs a policy on an E-SYN world for a set of instances and returns the paired campaign values, optionally
with the ``spt_transition/v1`` rows (recorded instances 0 .. 9999 = instance seeds 50000 + i, the P2 registry's
Paper C block). ``build_world`` tunes every rung of the ladder on the world's dev campaigns
(``policies.DEV_BASE`` + i, n = 1,000, budget ``policies.TUNE_BUDGET`` candidates per rung), evaluates them on
``N_TEST`` paired test campaigns (``policies.TEST_BASE`` + i), and reports each rung's gain over N1 and its gap to
the P3 oracle member, with 95 % intervals, plus a ``check_campaign`` pass (registry and replay) on recorded
campaigns of every rung. ``main`` writes ``paperC/esyn/ladder_table_v1.json`` with a code fingerprint.
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
from paperc.esyn import sim, table as OT
from paperc.esyn.extra import WORLDS

OUT = Path(__file__).resolve().parents[2] / "esyn" / "ladder_table_v1.json"
LADDER_SCHEMA = "paperc_ladder_table/v1"
N_TEST = 10_000
N_RECORDS = 3
Z95 = 1.959963984540054
CONFIG_ONLY = ("sprt", "race", "kg")


def code_sha256() -> str:
    h = hashlib.sha256()
    for f in (Path(L.__file__), Path(__file__), *(OT.PKG / s for s in OT.SOURCES)):
        h.update(f.name.encode() + b"\0" + f.read_bytes())
    return h.hexdigest()


def run(world, policy, instances, *, record: bool = False):
    if record:
        res = [sim.run_campaign(world, policy, i, record=True) for i in instances]
        return np.array([r.Y for r in res]), [row for r in res for row in r.rows]
    return sim.campaign_values(world, policy, instances), []


def paired(a: np.ndarray, b: np.ndarray) -> dict:
    d = a - b
    return {"diff": float(d.mean()), "half_width": Z95 * float(np.std(d, ddof=1)) / math.sqrt(len(d)),
            "share_differing": float(np.mean(d != 0))}


def tune_rungs(world) -> tuple[dict, dict]:
    """Every rung, tuned on dev; returns (policies by rung, tuning facts)."""
    dev = range(L.DEV_BASE, L.DEV_BASE + L.N_DEV)
    pols, facts = {"N0": L.N0()}, {}

    def tuner():
        return L.Tuner(world, dev)
    t1 = tuner()
    pols["N1"], _ = L.tune_static(t1)
    t2 = tuner()
    pols["N2"], _ = L.tune_static(t2, h_fixed=0.0)
    trace = L.dev_trace(world, dev)
    t2b = tuner()
    pols["N2b"] = L.fit_n2b(world, trace, t2b)
    t3 = tuner()
    pols["N3"], _ = L.tune_n3(t3, pols["N1"])
    pols["N4"] = L.fit_n4(world, trace, dev)
    n1_runs = float(np.mean([sim.run_campaign(world, pols["N1"], i).runs_used for i in dev]))
    tr = tuner()
    pols["random"] = L.tune_random(tr, n1_runs, lambda q: float(np.mean(
        [sim.run_campaign(world, L.RandomExec(q), i).runs_used for i in dev])))
    tunes = {"N1": t1, "N2": t2, "N2b": t2b, "N3": t3, "random": tr}
    n1 = pols["N1"]
    tb = tuner()
    pols["margin"], _, _ = L.coordinate_search(tb, lambda x: L.BudgetMargin(max(x[0], 0.0), x[1], x[2]),
                                               [n1.g, n1.h, 0.0], [0.0005, 0.001, 0.002])
    tunes["margin"] = tb
    if world.comparison == "config":
        s = world.base.sigma_cmp
        for key, make, x0, steps in (
                ("sprt", lambda x: L.SPRT(max(x[0], 0.0), x[1], max(x[2], 1e-5), min(max(x[3], 0.01), 0.45)),
                 [n1.g, n1.h, s / 2, 0.1], [0.0005, 0.001, s / 4, 0.05]),
                ("race", lambda x: L.Race(max(x[0], 0.0), x[1], max(x[2], 0.0)), [n1.g, n1.h, 1.0],
                 [0.0005, 0.001, 0.5]),
                ("kg", lambda x: L.KGVerify(max(x[0], 0.0), x[1], max(x[2], 0.0)), [n1.g, n1.h, 0.0001],
                 [0.0005, 0.001, 0.0001])):
            t = tuner()
            pols[key], _, _ = L.coordinate_search(t, make, x0, steps)
            tunes[key] = t
    for k, t in tunes.items():
        facts[k] = {"candidates_evaluated": len(t.cache), "budget": t.budget,
                    "instances": sorted(t.seen_instances)}
    facts["dev"] = [dev.start, dev.stop]
    facts["N1_mean_runs_dev"] = n1_runs
    return pols, facts


def build_world(name: str) -> dict:
    w = WORLDS[name]
    t0 = time.time()
    pols, facts = tune_rungs(w)
    otab = json.loads(OT.OUT.read_text())
    oracle_name = otab["worlds"][name]["oracle"]["selection"]["best_member"]
    pols["oracle"] = OT.policy_from_name(oracle_name, w)
    test = range(L.TEST_BASE, L.TEST_BASE + N_TEST)
    vals = {k: run(w, p, test)[0] for k, p in pols.items()}
    reg = SD.Registry.load()
    viol = {}
    for k, p in pols.items():
        _, rows = run(w, p, range(N_RECORDS), record=True)
        viol[k] = len(S.check_campaign(rows, registry=reg, behaviour=sim.behaviour_for(p)))
    out = {"world": name, "test": [test.start, test.stop], "tuning": facts,
           "rungs": {k: {"policy": p.name, "value": float(vals[k].mean()),
                         "vs_N1": paired(vals[k], vals["N1"]), "gap_to_oracle": paired(vals["oracle"], vals[k]),
                         "mean_runs": None, "record_violations": viol[k]} for k, p in pols.items()},
           "oracle_member": oracle_name, "seconds": None}
    for k, p in pols.items():
        out["rungs"][k]["mean_runs"] = float(np.mean([sim.run_campaign(w, p, i).runs_used
                                                     for i in range(L.TEST_BASE, L.TEST_BASE + 1000)]))
    out["seconds"] = round(time.time() - t0, 1)
    return out


def main(argv=None) -> Path:
    names = (argv if argv is not None else sys.argv[1:]) or list(WORLDS)
    tab = {"schema": LADDER_SCHEMA, "label": "ENGINEERING_ONLY", "code_sha256": code_sha256(),
           "oracle_table_sha256": json.loads(OT.OUT.read_text())["code_sha256"], "n_test": N_TEST,
           "n_dev": L.N_DEV, "tune_budget": L.TUNE_BUDGET, "worlds": {}}
    with Pool(2) as pool:
        for r in pool.imap_unordered(build_world, names):
            tab["worlds"][r["world"]] = r
            g = {k: f"{v['vs_N1']['diff']:+.5f}" for k, v in r["rungs"].items()}
            print(r["world"], g, f"[{r['seconds']} s]", flush=True)
    if set(names) != set(WORLDS) and OUT.exists():
        old = json.loads(OUT.read_text())
        old["worlds"].update(tab["worlds"])
        tab["worlds"] = old["worlds"]
    OUT.write_text(json.dumps(tab, indent=1, sort_keys=True) + "\n")
    return OUT


if __name__ == "__main__":
    print(main())
