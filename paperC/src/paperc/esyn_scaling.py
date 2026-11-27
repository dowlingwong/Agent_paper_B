"""E-SYN data-scaling curve for the P8 learners, and the E-SYN headroom table. ENGINEERING_ONLY.

AI-assisted (Claude, chat session, 22 Nov 2026). Not evidence, not an author decision.

Question: P8 (``learner_validation``) trained the three learners on 4,096 logged roots of the short budget world
and found the two offline-RL learners (R0 fitted Q iteration, R1 IQL) below the best static rule. Is that a
property of the learners in this world, or of the training size? This module repeats P8 at nested training
sizes and reports where each learner sits between N1, the best static rule and the exact DP.

Design, fixed before the run:

- world, baseline N1, logging mixture, support roots, dev and test ranges: exactly P8's;
- sizes: 256 ... 8,192 roots. Recorded campaigns are limited to instances 0 .. 9999 by the seed registry
  (``sim.MAX_RECORDED``), and P8's support roots take 768 of them, so 9,232 roots is the most this world can
  log without a new registry block. Draw 0 is nested: the first n roots of P8's range(4096), then the unused
  roots in ``EXTRA``. Further independent draws take disjoint slices of the roots above the support range
  wherever a slice of that size fits (three draws up to 2,048 roots, two at 4,096, one at 8,192);
- grids: P8's three settings per method, plus one larger setting for R0 and one longer-trained, wider setting
  for R1 (``EXTENDED``), because a fixed small model cannot use more data. N6 keeps P8's grid;
- selection: highest mean paired dev gain over N1, ties in grid order, done twice: within P8's grid and within
  the extended grid. The selected setting is refitted for P8's three fit seeds and tested once on P8's test
  roots. Test values of unselected settings are stored as diagnostics and are never used for selection;
- the P7/P8 support gate is *recorded* for every cell and not enforced: the curve must show what happens below
  the gate. A row whose gate status is not "meets thresholds" is not a deployable policy under P8's rules;
- reproduction check: draw 0 at n = 4096 within P8's grid must select P8's settings; the report states whether
  the test gains equal P8's stored values.

The headroom table is assembled from the stored P3 oracle table and P4 ladder table (no new simulation) plus the
exact short-budget references computed here.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import math
import multiprocessing
from pathlib import Path
import sys
import time

import numpy as np

from paperc import forks, learner_validation as lv, learners, ope, ope_validation
from paperc.esyn import dp, sim
from paperc.esyn import policies as esyn_policies

PKG = Path(__file__).resolve().parent
ROOT = PKG.parents[1]
OUT = ROOT / "esyn" / "scaling_v1.json"
REPORT = ROOT / "docs" / "reports" / "ESYN_SCALING_HEADROOM_20261122.md"
ORACLE_TABLE = ROOT / "esyn" / "oracle_table_v1.json"
LADDER_TABLE = ROOT / "esyn" / "ladder_table_v1.json"
P8_TABLE = ROOT / "esyn" / "learner_validation_v1.json"
SOURCES = (PKG / "esyn_scaling.py", *lv.SOURCES)

SIZES = (256, 512, 1024, 2048, 4096, 8192)
EXTRA = (*range(lv.TRAIN.stop, lv.SCREEN.start), *range(lv.SCREEN.stop, sim.MAX_RECORDED))
DRAW_POOL = range(lv.SCREEN.stop, sim.MAX_RECORDED)
N_DRAWS = 3
CHUNK = 256
EXTENDED = {
    "N6": lv.GRIDS["N6"],
    "R0": (*lv.GRIDS["R0"], learners.FQIConfig(63, 128)),
    "R1": (*lv.GRIDS["R1"], learners.IQLConfig(0.9, 16.0, width=64, critic_steps=12_800, actor_steps=4_800)),
}
N_P8 = {m: len(g) for m, g in lv.GRIDS.items()}
OK = "meets thresholds"
#: P4 ladder rows grouped for the headroom table. One-step rules decide each proposal on its own forecast;
#: the hand-built sequential rules read the campaign state (budget left, earlier measurements).
ONE_STEP = ("N2", "N2b", "margin", "shrink", "rawkeep")
SEQUENTIAL = ("N3", "N4", "kg", "race", "sprt")

_CELL: dict = {}


def code_sha256():
    h = hashlib.sha256()
    for path in SOURCES:
        h.update(path.name.encode() + b"\0" + path.read_bytes())
    return h.hexdigest()


def draw_roots(draw: int, n: int) -> list[int]:
    """Root instances of training draw ``draw`` at size ``n`` (draw 0 is nested across all sizes)."""
    if draw == 0:
        roots = [*lv.TRAIN, *EXTRA][:n]
    else:
        roots = list(DRAW_POOL[(draw - 1) * n:draw * n])
    if len(roots) != n:
        raise ValueError(f"draw {draw} has no {n} unused roots")
    return roots


def has_draw(draw: int, n: int) -> bool:
    return n <= len(lv.TRAIN) + len(EXTRA) if draw == 0 else draw * n <= len(DRAW_POOL)


def _check_ranges():
    held_out = set(lv.SCREEN) | set(lv.DEV) | set(lv.TEST)
    for n in SIZES:
        draws = [set(draw_roots(d, n)) for d in range(N_DRAWS) if has_draw(d, n)]
        if any(s & held_out for s in draws):
            raise ValueError("training roots must be disjoint from support, dev and test roots")
        if any(a & b for i, a in enumerate(draws[1:], 1) for b in draws[1:i]):
            raise ValueError("independent draws of one size must be disjoint")
        if n <= len(lv.TRAIN) and any(draws[0] & s for s in draws[1:]):
            raise ValueError("independent draws must be disjoint from draw 0 up to P8's size")


def _collect_chunk(instances):
    """Records and N6 fork labels of one chunk of roots (run in a worker process)."""
    world, base, mixture = _CELL["world"], _CELL["base"], _CELL["mixture"]
    _, records = lv.collect_roots(world, mixture, instances)
    design = forks.Design(q_uniform=lv.FORK_RATE, q_oversample=0.0, band_e1=0.0, band_e2=0.0, g=base.g, h=base.h)
    labels = {}
    for cid, (instance, member, rows) in records.items():
        labels[cid] = [(int(point.step), point.epoch,
                        float(forks.fork_cells(world, member, instance, point, [base], lv.FORK_REPS)[0].mean()))
                       for point in forks.select_forks(world, instance, rows, design)]
    return [(instance, cid, rows, labels[cid]) for cid, (instance, _, rows) in records.items()]


def collect(instances, workers=2):
    """instance -> (campaign id, root rows, fork labels), collected in chunks by forked workers."""
    chunks = [instances[i:i + CHUNK] for i in range(0, len(instances), CHUNK)]
    out = {}
    with multiprocessing.get_context("fork").Pool(workers) as pool:
        for k, part in enumerate(pool.imap(_collect_chunk, chunks)):
            for instance, cid, rows, labels in part:
                out[instance] = (cid, rows, labels)
            if (k + 1) % 16 == 0:
                print(f"  collected {len(out)} / {len(instances)} roots", flush=True)
    return out


def build(store, instances, mixture):
    """OPE batch and aligned N6 fork labels for the given roots."""
    batch = ope.load_campaigns([r for i in instances for r in store[i][1]], mixture)
    labels = {store[i][0]: store[i][2] for i in instances}
    indices, differences = [], []
    for cid, offset in zip(batch.ids, batch.starts):
        for step, epoch, diff in labels[cid]:
            idx = int(offset + step)
            if not batch.eligible[idx] or batch.obs[idx]["epoch"] != epoch:
                raise ValueError("fork lost alignment with its mixture root")
            indices.append(idx)
            differences.append(diff)
    return batch, learners.ForkTraining(np.asarray(indices, dtype=int), np.asarray(differences))


def _fit(method, config, rep):
    c = _CELL
    scale, seed = c["world"].base.sigma_cmp, lv._seed(c["world"], rep)
    if method == "N6":
        return learners.fit_n6(c["train"], c["forks"], config, scale=scale)
    fitter = {"R0": learners.fit_r0, "R1": learners.fit_r1}[method]
    return fitter(c["train"], config, scale=scale, seed=seed, shaped=True)


def _evaluate(policy, instances):
    return sim.campaign_values(_CELL["world"], policy, instances)


def run_method(method):
    """All settings of one method on the current cell: dev selection in both grids, three seeds, one test."""
    c = _CELL
    gap = c["gap"]
    rows, first = [], {}
    for idx, config in enumerate(EXTENDED[method]):
        row = {"candidate": idx, "config": asdict(config), "in_p8_grid": idx < N_P8[method]}
        t0 = time.time()
        try:
            policy = _fit(method, config, 0)
            row["dev_gain"] = float(np.mean(_evaluate(policy, lv.DEV) - c["dev_base"]))
            test = _evaluate(policy, lv.TEST)
            row["test_gain_seed0"] = float(np.mean(test - c["test_base"]))
            first[idx] = (policy, test)
        except ValueError as error:
            row["dev_gain"], row["error"] = None, str(error)
        row["seconds"] = round(time.time() - t0, 2)
        rows.append(row)
    result = {"method": method, "candidates": rows, "selected": {}}
    done = {}
    for grid, limit in (("p8", N_P8[method]), ("extended", len(EXTENDED[method]))):
        scored = [(r["dev_gain"], -r["candidate"]) for r in rows[:limit] if r["dev_gain"] is not None]
        if not scored:
            result["selected"][grid] = {"status": "insufficient data"}
            continue
        idx = -max(scored)[1]
        if idx not in done:
            policy, test = first[idx]
            returns, names = [test], [policy.name]
            for rep in range(1, lv.N_FIT):
                other = _fit(method, EXTENDED[method][idx], rep)
                returns.append(_evaluate(other, lv.TEST))
                names.append(other.name)
            returns = np.asarray(returns)
            gains = returns - c["test_base"]
            summary = lv._paired(gains.mean(axis=0))
            check = ope.support_diagnostics(c["train"], c["screen"], policy.probabilities_on(c["screen"]),
                                            ope_validation.cluster,
                                            train_target_p=policy.probabilities_on(c["train"]))
            summary.update({
                "status": "evaluated", "candidate": idx, "config": rows[idx]["config"], "policy_ids": names,
                "gain_share": summary["mean"] / gap, "share_ci": [x / gap for x in summary["ci"]],
                "fit_mean_gains": np.mean(gains, axis=1).tolist(),
                "vs_best_static": lv._paired(returns.mean(axis=0) - c["static_test"]),
                "candidate_support": check["status"],
                "candidate_zero_propensity_rows": check["zero_propensity_target_rows"],
            })
            done[idx] = summary
        result["selected"][grid] = done[idx]
    return result


def _child(conn, method):
    import torch

    torch.set_num_threads(1)
    try:
        conn.send(run_method(method))
    except BaseException as error:  # the parent re-raises
        conn.send({"method": method, "fatal": repr(error)})
    finally:
        conn.close()


def run_cell(n, draw, train, fork_data):
    """One training set: support receipt, then R1 in a forked child while R0 and N6 run here."""
    c = _CELL
    c.update(train=train, forks=fork_data)
    prefit = learners.prefit_support(train, c["screen"], ope_validation.cluster)
    cell = {"n_roots": n, "draw": draw, "rows": len(train.obs), "eligible_rows": int(train.eligible.sum()),
            "fork_points": len(fork_data.indices),
            "prefit": {"status": prefit["status"], "ess": prefit["ess"],
                       "action_shortfalls": prefit["action_shortfalls"],
                       "missing_stage_actions": prefit["missing_stage_actions"]},
            "methods": {}}
    ctx = multiprocessing.get_context("fork")
    parent, child = ctx.Pipe(duplex=False)
    proc = ctx.Process(target=_child, args=(child, "R1"))
    proc.start()
    child.close()
    for method in ("R0", "N6"):
        cell["methods"][method] = run_method(method)
    answer = parent.recv()
    proc.join()
    if "fatal" in answer:
        raise RuntimeError(f"R1 child failed: {answer['fatal']}")
    cell["methods"]["R1"] = answer
    return cell


def headroom():
    """Per stored E-SYN world: N1, the oracle member, and what the hand-built rungs already take of the gap."""
    oracle = json.loads(ORACLE_TABLE.read_text())
    ladder = json.loads(LADDER_TABLE.read_text())
    out = {"sources": {"oracle_table_sha256": hashlib.sha256(ORACLE_TABLE.read_bytes()).hexdigest(),
                       "ladder_table_sha256": hashlib.sha256(LADDER_TABLE.read_bytes()).hexdigest()},
           "n_test": ladder["n_test"], "worlds": {}}
    for name, entry in ladder["worlds"].items():
        rows = entry["rows"]
        world = oracle["worlds"][name]["world"]
        sigma = world["base"]["sigma_cmp"]
        gap = rows["N1"]["gap_to_oracle"]
        clear = gap["diff"] > 2 * gap["half_width"]

        def best(group):
            present = [k for k in group if k in rows]
            if not present:
                return None
            k = max(present, key=lambda r: rows[r]["value"])
            return {"rung": k, "policy": rows[k]["policy"], "vs_n1": rows[k]["vs_N1"]["diff"],
                    "vs_n1_half_width": rows[k]["vs_N1"]["half_width"],
                    "share": rows[k]["vs_N1"]["diff"] / gap["diff"] if clear else None,
                    "left": rows[k]["gap_to_oracle"]["diff"],
                    "left_half_width": rows[k]["gap_to_oracle"]["half_width"]}

        one, seq = best(ONE_STEP), best(SEQUENTIAL)
        top = max((x for x in (one, seq) if x), key=lambda x: x["vs_n1"])
        out["worlds"][name] = {
            "channel": world["channel"], "W": world["W"], "llm_cap": world["regime"]["llm_cap"],
            "sigma_cmp": sigma, "oracle_member": entry["oracle_member"],
            "exact_dp": oracle["worlds"][name].get("dp_value"),
            "n1_value": rows["N1"]["value"], "n0_vs_n1": rows["N0"]["vs_N1"]["diff"],
            "gap": gap["diff"], "gap_half_width": gap["half_width"], "gap_over_sigma": gap["diff"] / sigma,
            "gap_clear": bool(clear), "one_step": one, "sequential": seq,
            "left": top["left"], "left_half_width": top["left_half_width"],
            "left_over_sigma": top["left"] / sigma,
            "left_clear": bool(top["left"] > 2 * top["left_half_width"]),
            "oracle_exceeded": bool(top["left"] < -top["left_half_width"]),
        }
    return out


def benchmark(sizes=SIZES, draws=N_DRAWS, cache: Path | None = None):
    """``cache``: a scratch JSON of finished cells, so an interrupted run resumes (not a result file)."""
    import torch

    torch.set_num_threads(1)
    _check_ranges()
    world, base, mixture = lv.setup()
    law = dp.size_law(world)
    thresholds = (*law.v, max(law.v) + 1.0)
    best_g = max(thresholds, key=lambda g: dp.static_value(world, g))
    best_static = dp.static_value(world, best_g)
    solution = dp.solve(world)
    oracle = esyn_policies.Threshold(solution.table)
    n1 = ope_validation.exact_policy_value(world, base)
    gap = solution.value - n1
    _CELL.update(world=world, base=base, mixture=mixture, gap=gap)

    plan = [(d, n) for d in range(draws) for n in sizes if has_draw(d, n) and (d == 0 or n <= len(lv.TRAIN))]
    need = sorted({i for d, n in plan for i in draw_roots(d, n)})
    print(f"scaling: collecting {len(need)} training roots and {len(lv.SCREEN)} support roots", flush=True)
    t0 = time.time()
    store = collect(need)
    screen_store = collect(list(lv.SCREEN))
    screen, _ = build(screen_store, list(lv.SCREEN), mixture)
    print(f"scaling: collection took {time.time() - t0:.0f} s", flush=True)

    dev_base = _evaluate(base, lv.DEV)
    test_base = _evaluate(base, lv.TEST)
    static_test = _evaluate(esyn_policies.Static(best_g, 0.0), lv.TEST)
    dp_test = lv._paired(_evaluate(oracle, lv.TEST) - test_base)
    static_paired = lv._paired(static_test - test_base)
    _CELL.update(screen=screen, dev_base=dev_base, test_base=test_base, static_test=static_test)

    cells = []
    sha = code_sha256()
    saved = json.loads(cache.read_text()) if cache and cache.exists() else {}
    saved = saved.get("cells", {}) if saved.get("code_sha256") == sha else {}
    for d, n in plan:
        t0 = time.time()
        if f"{d}/{n}" in saved:
            cell = saved[f"{d}/{n}"]
        else:
            train, fork_data = build(store, draw_roots(d, n), mixture)
            cell = run_cell(n, d, train, fork_data)
            cell["seconds"] = round(time.time() - t0, 1)
            saved[f"{d}/{n}"] = cell
            if cache:
                cache.write_text(json.dumps({"code_sha256": sha, "cells": saved}, allow_nan=False))
        cells.append(cell)
        line = ", ".join(
            f"{m} {cell['methods'][m]['selected']['extended'].get('gain_share', float('nan')):.3f}"
            for m in ("N6", "R0", "R1"))
        print(f"scaling: draw {d} n {n}: prefit {cell['prefit']['status']}; share of gap: {line} "
              f"({cell['seconds']} s)", flush=True)

    return {
        "schema": "paperc_esyn_scaling/v1", "label": "ENGINEERING_ONLY", "code_sha256": code_sha256(),
        "design": {
            "world": world.name, "slots": world.llm_cap, "runs": world.W, "sizes": list(sizes), "draws": draws,
            "train_draw0": [[lv.TRAIN.start, lv.TRAIN.stop], [lv.TRAIN.stop, lv.SCREEN.start],
                            [lv.SCREEN.stop, sim.MAX_RECORDED]],
            "train_other_draws": {"pool": [DRAW_POOL.start, DRAW_POOL.stop], "slice": "pool[(d-1)n : dn]"},
            "max_recorded_roots": sim.MAX_RECORDED,
            "screen": [lv.SCREEN.start, lv.SCREEN.stop], "dev": [lv.DEV.start, lv.DEV.stop],
            "test": [lv.TEST.start, lv.TEST.stop], "fit_count": lv.N_FIT,
            "grids": {m: [asdict(c) for c in g] for m, g in EXTENDED.items()}, "p8_grid_sizes": N_P8,
            "support_gate": "recorded, not enforced", "threads": 1,
            "versions": {"torch": torch.__version__, "lightgbm": __import__("lightgbm").__version__,
                         "numpy": np.__version__},
        },
        "reference": {"N1": n1, "DP": solution.value, "best_static_bayes_keep": best_static,
                      "best_static_threshold": best_g, "gap": gap,
                      "static_share_exact": (best_static - n1) / gap,
                      "dp_paired_check": dp_test, "static_paired_check": static_paired},
        "cells": cells,
        "headroom": headroom(),
    }


# ---------------------------------------------------------------------------------------------------------------
# report


def _cell(result, n, draw):
    for cell in result["cells"]:
        if cell["n_roots"] == n and cell["draw"] == draw:
            return cell
    return None


def _pct(x):
    return "—" if x is None else f"{100 * x:.1f}%"


def _settings(config):
    return ", ".join(f"{k}={v:g}" for k, v in config.items())


def reproduction(result):
    """Compare draw 0, n = 4096, P8 grid with the stored P8 table."""
    cell = _cell(result, len(lv.TRAIN), 0)
    if cell is None or not P8_TABLE.exists():
        return None
    stored = json.loads(P8_TABLE.read_text())
    out = {"rows_equal": cell["rows"] == stored["training"]["rows"],
           "fork_points_equal": cell["fork_points"] == stored["training"]["fork_points"], "methods": {}}
    for method, row in stored["methods"].items():
        now = cell["methods"][method]["selected"]["p8"]
        out["methods"][method] = {
            "same_setting": now.get("candidate") == row["selected"],
            "same_policies": now.get("policy_ids") == row.get("policy_ids"),
            "p8_gain": row["test"]["mean"], "gain": now.get("mean"),
            "difference": None if now.get("mean") is None else now["mean"] - row["test"]["mean"],
        }
    return out


def markdown(result):
    d, ref = result["design"], result["reference"]
    gap = ref["gap"]
    sizes = d["sizes"]
    lines = [
        "# E-SYN: learner data-scaling curve and headroom table", "",
        "**AI-assisted (Claude, chat session, 22 Nov 2026). ENGINEERING_ONLY. Not evidence, not an author "
        "decision.** Generated by `python -m paperc.esyn_scaling`; data in `paperC/esyn/scaling_v1.json`.", "",
        "## 1. Question", "",
        "P8 (`LEARNER_VALIDATION_20261117.md`) trained N6, R0 and R1 on 4,096 logged roots of the short budget "
        "world. Both offline-RL learners ended below the best static rule. This report asks whether that is a "
        "matter of training size, and how much room each E-SYN world leaves above simple rules.", "",
        "## 2. Design (fixed before the run)", "",
        f"- **World and data:** P8's short budget world ({d['slots']} slots, {d['runs']} runs), P8's N1 baseline, "
        "logging mixture, support roots, dev roots and test roots.",
        f"- **Sizes:** {', '.join(f'{n:,}' for n in sizes)} training roots. Draw 0 is nested: it starts with P8's "
        "roots and adds unused ones above 4,096. Further draws use separate root slices where one fits: three "
        "draws up to 2,048 roots, two at 4,096, one at 8,192.",
        f"- **Largest size:** the seed registry limits recorded campaigns to instances 0 … "
        f"{d['max_recorded_roots'] - 1:,}, and the support roots take 768 of them. 8,192 roots is therefore the "
        "largest power of two this world can log. A longer curve needs a new registry block.",
        "- **Settings:** P8's three settings per method. R0 gets one larger setting (63 leaves, 128 rounds). "
        "R1 gets one wider, longer-trained setting (width 64, 12,800 critic steps, 4,800 actor steps). "
        "N6 keeps P8's grid.",
        "- **Selection:** highest mean paired dev gain over N1, ties in grid order. Selection is done within "
        "P8's grid and, separately, within the extended grid. The selected setting is refitted for three fit "
        "seeds and tested once.",
        "- **Support gate:** recorded for every training set and every selected policy, but not enforced. "
        "A row marked *below gate* is not a deployable policy under P8's rules.",
        "- **Test statistic:** mean paired gain over N1 on the 6,000 test roots, averaged over three fit seeds. "
        "The interval covers test-root variation given the fitted policies. It does not cover the training draw; "
        "the draw-to-draw range in §4 shows that part.", "",
        "## 3. Reference values (exact)", "",
        f"N1 {ref['N1']:.8f}; best static rule {ref['best_static_bayes_keep']:.8f}; DP {ref['DP']:.8f}. "
        f"The N1-to-DP gap is {gap:.8f}. The best static rule takes {_pct(ref['static_share_exact'])} of that gap, "
        f"so a learner has {_pct(1 - ref['static_share_exact'])} of the gap left to win over it.", "",
        f"On the test roots, paired simulation gives DP − N1 = {ref['dp_paired_check']['mean']:.8f} "
        f"(s.e. {ref['dp_paired_check']['se']:.8f}) and static − N1 = {ref['static_paired_check']['mean']:.8f} "
        f"(s.e. {ref['static_paired_check']['se']:.8f}). The shares below divide by the exact gap, as P8 does. "
        f"On these test roots the best static rule therefore reads {_pct(ref['static_paired_check']['mean'] / gap)} "
        "of the exact gap; compare the learners with that number, or use the paired column.", "",
        "## 4. Scaling curve", "",
        "Share of the exact N1-to-DP gap recovered on the test roots, extended grid, draw 0 "
        "(95% interval over test roots). “vs static” is the paired difference to the best static rule in units "
        "of 10⁻⁵, with its 95% interval.", "",
        "| Training roots | Logged decisions | Support gate | N6 share | N6 vs static | R0 share | R0 vs static | "
        "R1 share | R1 vs static |",
        "|---:|---:|---|---:|---:|---:|---:|---:|---:|",
    ]

    def share(sel):
        if sel.get("status") != "evaluated":
            return "no fit", "—"
        lo, hi = sel["share_ci"]
        v = sel["vs_best_static"]
        return (f"{_pct(sel['gain_share'])} [{100 * lo:.0f}, {100 * hi:.0f}]",
                f"{1e5 * v['mean']:+.1f} [{1e5 * v['ci'][0]:+.1f}, {1e5 * v['ci'][1]:+.1f}]")

    for n in sizes:
        cell = _cell(result, n, 0)
        if cell is None:
            continue
        gate = "passes" if cell["prefit"]["status"] == OK else "below gate"
        cols = [x for m in ("N6", "R0", "R1") for x in share(cell["methods"][m]["selected"]["extended"])]
        lines.append(f"| {n:,} | {cell['rows']:,} | {gate} | " + " | ".join(cols) + " |")

    lines += ["", "Selected settings (extended grid, draw 0) and the candidate-policy support check:", "",
              "| Training roots | R0 setting | R0 policy support | R1 setting | R1 policy support | N6 setting |",
              "|---:|---|---|---|---|---|"]
    for n in sizes:
        cell = _cell(result, n, 0)
        if cell is None:
            continue
        cols = []
        for m in ("R0", "R1", "N6"):
            sel = cell["methods"][m]["selected"]["extended"]
            if sel.get("status") != "evaluated":
                cols += ["—"] if m == "N6" else ["—", "—"]
                continue
            cfg = sel["config"]
            if m == "R0":
                text = f"{cfg['leaves']} leaves, {cfg['rounds']} rounds"
            elif m == "R1":
                text = (f"τ={cfg['expectile']:g}, β={cfg['inverse_temperature']:g}, width {cfg['width']}, "
                        f"{cfg['critic_steps']:,} steps")
            else:
                text = f"α={cfg['alpha']:g}"
            cols.append(text)
            if m != "N6":
                cols.append("passes" if sel["candidate_support"] == OK else "below gate")
        lines.append(f"| {n:,} | " + " | ".join(cols) + " |")

    lines += ["", "Draw-to-draw range of the share (extended grid; minimum – maximum over the available draws):", "",
              "| Training roots | Draws | Gate passes in | N6 | R0 | R1 |", "|---:|---:|---:|---:|---:|---:|"]
    for n in sizes:
        cells = [c for c in result["cells"] if c["n_roots"] == n]
        if len(cells) < 2:
            continue
        cols = []
        for m in ("N6", "R0", "R1"):
            vals = [c["methods"][m]["selected"]["extended"].get("gain_share") for c in cells]
            vals = [v for v in vals if v is not None]
            cols.append(f"{_pct(min(vals))} – {_pct(max(vals))}" if vals else "—")
        passes = sum(c["prefit"]["status"] == OK for c in cells)
        lines.append(f"| {n:,} | {len(cells)} | {passes} | " + " | ".join(cols) + " |")

    lines += ["", "P8 grid only (draw 0), for comparison with P8:", "",
              "| Training roots | R0 share | R0 setting | R1 share | R1 setting |", "|---:|---:|---|---:|---|"]
    for n in sizes:
        cell = _cell(result, n, 0)
        if cell is None:
            continue
        cols = []
        for m in ("R0", "R1"):
            sel = cell["methods"][m]["selected"]["p8"]
            if sel.get("status") != "evaluated":
                cols += ["—", "—"]
                continue
            cols += [_pct(sel["gain_share"]), _settings({k: v for k, v in sel["config"].items()
                                                         if k in ("leaves", "rounds", "expectile",
                                                                  "inverse_temperature")})]
        lines.append(f"| {n:,} | " + " | ".join(cols) + " |")

    rep = reproduction(result)
    lines += ["", "## 5. Reproduction of P8", ""]
    if rep is None:
        lines.append("Not run: the 4,096-root cell or the stored P8 table is missing.")
    else:
        lines.append(f"At 4,096 roots (draw 0, P8 grid) the training batch has the same number of logged "
                     f"decisions as P8: **{'yes' if rep['rows_equal'] else 'no'}**; the same number of fork "
                     f"points: **{'yes' if rep['fork_points_equal'] else 'no'}**.")
        lines += ["", "| Method | Same setting selected | Same fitted policies | P8 gain | This run | Difference |",
                  "|---|---|---|---:|---:|---:|"]
        for m, r in rep["methods"].items():
            lines.append(f"| {m} | {'yes' if r['same_setting'] else 'no'} | "
                         f"{'yes' if r['same_policies'] else 'no'} | {r['p8_gain']:+.8f} | "
                         f"{r['gain']:+.8f} | {r['difference']:+.2e} |")
        v = d["versions"]
        lines += ["", f"Library versions of this run: torch {v['torch']}, LightGBM {v['lightgbm']}, "
                      f"NumPy {v['numpy']}. P8 did not store its versions, so a difference in a fitted policy "
                      "can come from the library version."]

    h = result["headroom"]
    lines += [
        "", "## 6. Headroom table (stored P3 and P4 tables, no new simulation)", "",
        f"Each world's P4 ladder was tested on {h['n_test']:,} common roots. The gap is oracle member − N1, "
        "where N1 is the static rule tuned on dev roots. Two groups of hand-built rows are compared with it:", "",
        f"- **one-step rules** ({', '.join(ONE_STEP)}): each proposal is decided on its own forecast;",
        f"- **hand-built sequential rules** ({', '.join(SEQUENTIAL)}): they read the campaign state, such as "
        "the budget left or earlier measurements of the same configuration.", "",
        "“Left” is what remains between the best hand-built row and the oracle member, with its 95% half-width. "
        "It is the room a learned policy could win over rules written by hand. σ is the world's comparison "
        "noise.", "",
        "| World | Gap, 10⁻³ | Gap / σ | Best one-step rule: share of gap | Best sequential rule: share of gap | "
        "Left, 10⁻³ | Left / σ | Room for a learner |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]

    def group(x):
        return "—" if x is None else f"{x['rung']}: {_pct(x['share'])}"

    for name, w in h["worlds"].items():
        if not w["gap_clear"]:
            verdict = "none (no gap)"
        elif w["oracle_exceeded"]:
            verdict = "none shown (a hand-built rule beats the oracle member)"
        elif w["left_clear"]:
            verdict = "yes"
        else:
            verdict = "not resolved"
        lines.append(
            f"| {name} | {1e3 * w['gap']:.3f} ± {1e3 * w['gap_half_width']:.3f} | {w['gap_over_sigma']:.2f} | "
            f"{group(w['one_step'])} | {group(w['sequential'])} | "
            f"{1e3 * w['left']:.3f} ± {1e3 * w['left_half_width']:.3f} | {w['left_over_sigma']:.2f} | {verdict} |")
    left = ref["DP"] - ref["best_static_bayes_keep"]
    lines += [
        f"| p8_short_budget (exact; §4's world) | {1e3 * gap:.3f} | {gap / _sigma_short():.2f} | "
        f"static threshold: {_pct(ref['static_share_exact'])} | not run | {1e3 * left:.3f} | "
        f"{left / _sigma_short():.2f} | {_pct(1 - ref['static_share_exact'])} of the gap |",
        "", "Reading rules for this table:", "",
        "- The oracle member is the best member of a declared family, except in the two budget worlds and "
        "strict_null, where an exact DP exists. Elsewhere “left” is a lower bound on the true room, and a "
        "hand-built rule tuned on dev roots can exceed the oracle member.",
        "- A share is shown only where the gap exceeds twice its half-width.",
        "- “Room for a learner” is “yes” where “left” exceeds twice its half-width. The intervals are not "
        "corrected for the number of rows read.",
        "- The table says how much room exists. It does not say that R0, R1 or N6 can take it: those learners "
        "act on E1 and E2 only, and the worlds with room need actions they do not have (re-measure, re-audit) "
        "or state they do not see (which keys interact).", "",
    ]
    return "\n".join(lines)


def _sigma_short():
    world, _, _ = lv.setup()
    return world.base.sigma_cmp


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--report-only" in argv:
        result = json.loads(OUT.read_text())
    else:
        cache = Path(argv[argv.index("--cache") + 1]) if "--cache" in argv else None
        result = benchmark(cache=cache)
        OUT.write_text(json.dumps(result, indent=1, allow_nan=False) + "\n")
    REPORT.write_text(markdown(result))
    return REPORT


if __name__ == "__main__":
    print(main())
