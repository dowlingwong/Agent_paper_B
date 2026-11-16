"""Validation of the fork design and go/no-go statistics on E-SYN (build runbook P6, step 4):
``python -m paperc.forks_validation`` -> ``esyn/fork_validation_v1.json`` and
``docs/reports/FORK_VALIDATION_20261116.md`` (``--report-only`` rewrites the markdown from the JSON).

AI-assisted (Claude, chat session, 16 Nov 2026; revised after review round 1). ENGINEERING_ONLY. E-SYN results are
implementation checks, never evidence about the real loop.

Set-up in every world: behaviour = the world's tuned N1 (committed ladder table); continuation policies = [N1, N0]
(static thresholds on the belief, so the null property of ``d`` applies, see ``paperc.forks``); r = 2 replicates
(plan §6 SPT-3); design q_uniform = 0.15, q_oversample = 0.5, near bands 0.1 sigma_cmp around N1's own g and h; 40
roots per simulated collection. Instance ranges per world are disjoint between parts: A / C collections 0+,
C2 2000+, population P 8000-9599, oracle roots B 9600-9659.

* **A. Null coverage** (``strict_null``, ``N_A`` collections): tau^2_hat of the continuation difference ``d`` (true
  value 0 for every state under these continuation policies), pooled, per epoch and per continuation policy;
  coverage of 0. The total difference ``q`` alongside.
* **B. Oracle roots** (``N_OR`` roots, every eligible decision forked with ``R_OR`` replicates per continuation
  policy). ``N_DESIGN`` redraws of the selection, using replicates 1-2 (the design's r = 2): HT, Hajek and unweighted
  means against the population mean of the same replicate-1-2 differences (exact design-unbiasedness; selection error
  only), and HT against the mean of the independent replicates 3-R (a check that replicates are seeded alike; z with
  the replicate noise of both means). N6 cross-fitting on ``N_LEAK`` redraws: the estimate on replicates 1-2 minus
  the value of the same cross-fitted decisions on the same forks under replicates 3-R; the redraws share one
  realisation of the replicate noise, so the mean is tested with that noise's standard error, sqrt(sum_j c_j^2 v_j),
  c_j the average signed weight of state j and v_j = sum_c s_jc^2 (1 / (2 C^2) + 1 / (C^2 (R - 2))).
* **P. Population** (``N_POP`` roots, every eligible decision forked, r = 2): tau^2 of ``d`` (pooled and per epoch)
  and of ``q``, the truth for coverage; tau^2_d of four disjoint 400-root blocks (precision); and the evaluation
  states for the N6 truth: the population value of each collection's fitted rules (``forks.rule_gain``).
* **C. Fresh roots** (every world, ``N_C`` collections; null: the collections of A): tau^2 detection (lower bound >
  0) and coverage of the population value, pooled and per epoch; the bootstrap s.e. against the sd across
  collections; roots for 80 % power; the N6 value with coverage of (i) the fixed-decision interval for the population
  value of the collection's own fitted rules and (ii) the refitting interval for the expected value of the procedure
  (the mean of (i)'s truths over collections). **C2**: tau^2 with ``N_ROOTS_BIG`` roots per collection in the worlds
  where 40 roots rarely detect.
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

from paperc import forks as F
from paperc import policies as P
from paperc.esyn import policies as EP, sim
from paperc.esyn.extra import WORLDS
from paperc.runner import OUT as LADDER

PKG = Path(__file__).resolve().parent
ROOT = PKG.parents[1]
OUT = ROOT / "esyn" / "fork_validation_v1.json"
REPORT = ROOT / "docs" / "reports" / "FORK_VALIDATION_20261116.md"
N_ROOTS, N_A, N_C = 40, 200, 40
N_OR, R_OR, OR_BASE = 60, 16, 9600
N_DESIGN, N_LEAK = 500, 100
N_POP, POP_BASE = 1600, 8000
N_ROOTS_BIG, N_C2, C2_BASE = 160, 20, 2000
C2_WORLDS = ("budget", "shared_error", "eval_allocation", "information")
B_TAU, B_N6 = 300, 200
Q_UNIFORM, Q_OVERSAMPLE, BAND = 0.15, 0.5, 0.1
WORLD_ORDER = ("strict_null", "budget", "interaction", "shared_error", "eval_allocation", "information",
               "keep_feedback")
SOURCES = (PKG / "forks.py", PKG / "forks_validation.py", PKG / "policies.py", PKG / "esyn" / "sim.py",
           PKG / "esyn" / "worlds.py", PKG / "esyn" / "extra.py", PKG / "esyn" / "policies.py", LADDER)
TAU_KEYS = ("tau2_d", "tau2_d_c0", "tau2_d_c1", "tau2_d_E1", "tau2_d_E2", "tau2_q")


def code_sha256() -> str:
    h = hashlib.sha256()
    for f in SOURCES:
        h.update(f.name.encode() + b"\0" + f.read_bytes())
    return h.hexdigest()


def setup(world: str):
    lad = json.loads(LADDER.read_text())
    w = WORLDS[world]
    beh = EP.from_name(lad["worlds"][world]["rows"]["N1"]["policy"])
    s = w.base.sigma_cmp
    design = F.Design(q_uniform=Q_UNIFORM, q_oversample=Q_OVERSAMPLE, band_e1=BAND * s, band_e2=BAND * s,
                      g=beh.g, h=beh.h)
    return w, beh, [beh, P.N0()], design


def _clean(x):
    if isinstance(x, dict):
        return {k: _clean(v) for k, v in x.items() if k not in ("act", "fit", "gain", "fold_row", "models")}
    if isinstance(x, (list, tuple)):
        return [_clean(v) for v in x]
    if isinstance(x, (np.floating, float)):
        return None if not math.isfinite(float(x)) else float(x)
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.bool_):
        return bool(x)
    return x


def _tau_set(ft, s: int) -> dict:
    out = {}
    for tg in ("d", "q"):
        out[f"tau2_{tg}"] = F.tau2(ft, tg, B=B_TAU, seed=(s, 0))
    for c in (0, 1):
        out[f"tau2_d_c{c}"] = F.tau2(ft, "d", cont=c, B=B_TAU, seed=(s, 1 + c))
    for ep in ("E1", "E2"):
        out[f"tau2_d_{ep}"] = F.tau2(ft, "d", epoch=ep, B=B_TAU, seed=(s, 5 + (ep == "E2")))
    return out


# ---------------------------------------------------------------- population (P): truth for coverage

def population(world: str) -> dict:
    t0 = time.time()
    w, beh, conts, design = setup(world)
    full = F.collect(w, beh, range(POP_BASE, POP_BASE + N_POP), design, conts, reps=2, select_all=True)
    out = {"world": world, "n_roots": N_POP, "n_states": len(full),
           "n_states_epoch": {ep: int(len(full.epoch_rows(ep))) for ep in ("E1", "E2")}}
    k = WORLD_ORDER.index(world)
    for j, (key, tg, ep) in enumerate((("q", "q", None), ("d", "d", None), ("d_E1", "d", "E1"), ("d_E2", "d", "E2"))):
        t = F.tau2(full, tg, epoch=ep, B=B_TAU, seed=(k, 8, j))
        out[key] = {"tau2": t["tau2"], "ci": t["ci"], "between": t["between"], "mean_se2": t["mean_se2"]}
    blocks = []
    for b in range(N_POP // 400):
        lo = POP_BASE + 400 * b
        sub = full.subset(np.flatnonzero((full.instance >= lo) & (full.instance < lo + 400)))
        blocks.append(F.tau2_point(*F.fork_diffs(sub, "d"), sub.w)["tau2"])
    out["d"]["blocks_400"] = blocks
    qbar = full.q.mean(axis=(1, 2))
    arrays = {"roots": N_POP}
    for ep in ("E1", "E2"):
        r = full.epoch_rows(ep)
        arrays[ep] = (F._feature_matrix(full, r, ep), full.b_act[r].copy(), qbar[r].copy())
    out["seconds"] = round(time.time() - t0, 1)
    return {"summary": _clean(out), "arrays": arrays}


# ---------------------------------------------------------------- one simulated collection (A, C, C2)

_POP: dict = {}


def _init(pop_arrays: dict) -> None:
    _POP.update(pop_arrays)


def one_collection(args) -> dict:
    world, s, n_roots, base, with_n6 = args
    w, beh, conts, design = setup(world)
    ft = F.collect(w, beh, range(base + s * n_roots, base + (s + 1) * n_roots), design, conts, reps=2)
    out = {"sim": s, "n_roots": n_roots, "n_forks": len(ft), "n_eligible": ft.eligible(),
           "near_share": float(ft.near.mean()) if len(ft) else None, **_tau_set(ft, s)}
    if with_n6:
        v = F.n6_value(ft, B=B_N6, seed=(s, 9))
        pa = _POP[world]
        truth_dec, truth_camp = F.rule_gain(v["fit"], {ep: pa[ep][0] for ep in ("E1", "E2")},
                                            {ep: pa[ep][1] for ep in ("E1", "E2")},
                                            {**{ep: pa[ep][2] for ep in ("E1", "E2")}, "roots": pa["roots"]})
        v["truth_per_decision"], v["truth_per_campaign"] = truth_dec, truth_camp
        out["n6"] = v
    return _clean(out)


# ---------------------------------------------------------------- oracle roots (B)

def oracle(world: str) -> dict:
    t0 = time.time()
    w, beh, conts, design = setup(world)
    inst = range(OR_BASE, OR_BASE + N_OR)
    full = F.collect(w, beh, inst, design, conts, reps=R_OR, select_all=True)
    C_, R_ = full.q.shape[1], full.q.shape[2]
    roots = {i: sim.run_campaign(w, beh, i, record=True).rows for i in inst}
    key = {(int(full.instance[j]), full.fork_id[j]): j for j in range(len(full))}
    m12 = {tg: getattr(full, tg)[:, :, :2].mean(axis=(1, 2)) for tg in ("q", "d")}
    m3r = {tg: getattr(full, tg)[:, :, 2:].mean(axis=(1, 2)) for tg in ("q", "d")}
    vj = {tg: getattr(full, tg).var(axis=2, ddof=1).sum(axis=1) * (1 / (2 * C_ ** 2) + 1 / (C_ ** 2 * (R_ - 2)))
          for tg in ("q", "d")}
    N, n = full.eligible(), len(full)
    est = {k: [] for k in ("ht_q", "hajek_q", "unw_q", "ht_d", "hajek_d", "unw_d", "n_sel")}
    leak, cj = [], np.zeros(n)
    for rep in range(N_DESIGN):
        d = F.Design(**{**design.__dict__, "design_rep": rep + 1})
        sel, ps = [], []
        for i, rows in roots.items():
            for fp in F.select_forks(w, i, rows, d):
                sel.append(key[(i, fp.fork_id)])
                ps.append(fp.design.p_select)
        sel, wt = np.asarray(sel), 1.0 / np.asarray(ps)
        for tg in ("q", "d"):
            v = m12[tg]
            est[f"ht_{tg}"].append(float((wt * v[sel]).sum() / N))
            est[f"hajek_{tg}"].append(float((wt * v[sel]).sum() / wt.sum()))
            est[f"unw_{tg}"].append(float(v[sel].mean()))
        est["n_sel"].append(len(sel))
        if rep < N_LEAK:
            sub = full.subset(sel)
            sub.p_select, sub.q, sub.d, sub.reps = np.asarray(ps), sub.q[:, :, :2], sub.d[:, :, :2], 2
            e = F.n6_point(sub, np.arange(len(sub)), sub.instance, folds=5, alpha=1.0, min_train=10,
                           rng=np.random.default_rng([F.ANALYSIS_KEY, 3, rep]), qbar=sub.q.mean(axis=(1, 2)))
            sign = (e["act"] != sub.b_act) * np.where(e["act"], 1.0, -1.0)
            leak.append(e["per_decision"] - float((wt * sign * m3r["q"][sel]).sum() / wt.sum()))
            np.add.at(cj, sel, sign * wt / wt.sum() / N_LEAK)
    des = {}
    for tg in ("q", "d"):
        target12, target3r = float(m12[tg].mean()), float(m3r[tg].mean())
        rep_var = float(vj[tg].sum() / n ** 2)          # var of (pop mean of reps 1-2) - (pop mean of reps 3-R)
        for kind in ("ht", "hajek", "unw"):
            x = np.asarray(est[f"{kind}_{tg}"])
            mc = float(x.std(ddof=1) / np.sqrt(len(x)))
            des[f"{kind}_{tg}"] = {"mean": float(x.mean()), "mc_se": mc, "bias_vs_pop12": float(x.mean() - target12),
                                   "z_vs_pop12": float((x.mean() - target12) / mc),
                                   "diff_vs_reps3R": float(x.mean() - target3r),
                                   "z_vs_reps3R": float((x.mean() - target3r) / math.sqrt(mc ** 2 + rep_var))}
        des[f"pop12_{tg}"], des[f"reps3R_{tg}"] = target12, target3r
    e_j = m12["q"] - m3r["q"]
    leak = np.asarray(leak)
    leak_se = float(np.sqrt((cj ** 2 * vj["q"]).sum()))
    return _clean({"world": world, "n_roots": N_OR, "reps": R_OR, "n_states": n, "n_eligible": N,
                   "population_mean": {"q": float(full.q.mean()), "d": float(full.d.mean())}, "design": des,
                   "mean_selected": float(np.mean(est["n_sel"])),
                   "n6_leak": {"mean": float(leak.mean()), "linear_mean": float((cj * e_j).sum()),
                               "se_replicate_noise": leak_se, "z": float(leak.mean() / leak_se) if leak_se > 0 else None,
                               "n": len(leak)},
                   "seconds": round(time.time() - t0, 1)})


# ---------------------------------------------------------------- summaries

def _prop(x) -> dict:
    x = np.asarray(x, float)
    p, n = float(x.mean()), len(x)
    return {"p": p, "n": n, "mc_se": float(math.sqrt(max(p * (1 - p), 1e-12) / n))}


def _raw(x: dict) -> dict:
    """Compact per-collection record: [estimate, lower, upper] per tau^2 statistic; N6 estimates, intervals, truths."""
    out = {"sim": x["sim"], "n_roots": x["n_roots"], "n_forks": x["n_forks"]}
    for k in TAU_KEYS:
        out[k] = [x[k]["tau2"], *(x[k]["ci"] or (None, None))]
    if "n6" in x:
        v = x["n6"]
        out["n6"] = {"est": v["per_decision"], "ci_refit": v.get("ci_refit_per_decision"),
                     "ci_fixed": v.get("ci_fixed_per_decision"),
                     "truth": v["truth_per_decision"], "est_campaign": v["per_campaign"],
                     "ci_refit_campaign": v.get("ci_refit_per_campaign"), "truth_campaign": v["truth_per_campaign"],
                     "flip_rate": v["flip_rate"]}
    return out


def summarise(world: str, sims: list[dict], pop: dict) -> dict:
    out = {"n_sims": len(sims), "forks_mean": float(np.mean([s["n_forks"] for s in sims])),
           "eligible_mean": float(np.mean([s["n_eligible"] for s in sims]))}
    for k in TAU_KEYS:
        est = np.array([s[k]["tau2"] for s in sims])
        ci = [s[k]["ci"] for s in sims]
        sd = float(est.std(ddof=1))
        boot_se = float(np.mean([(hi - lo) / 3.92 for lo, hi in ci]))
        out[k] = {"mean": float(est.mean()), "mc_se": sd / np.sqrt(len(est)), "sd": sd, "mean_boot_se": boot_se,
                  "boot_se_ratio": boot_se / sd if sd > 0 else None,
                  "cover_0": _prop([lo <= 0 <= hi for lo, hi in ci]), "detect": _prop([lo > 0 for lo, _ in ci])}
        pk = k.removeprefix("tau2_")
        if pk in pop:
            true = pop[pk]["tau2"]
            pse = (pop[pk]["ci"][1] - pop[pk]["ci"][0]) / 3.92
            blocks = pop[pk].get("blocks_400")
            bse = float(np.std(blocks, ddof=1) / np.sqrt(len(blocks))) if blocks else None
            out[k].update({"pop_tau2": true, "cover_pop": _prop([lo <= true <= hi for lo, hi in ci]),
                           "bias_z_vs_pop": float((est.mean() - true) / math.hypot(sd / np.sqrt(len(est)), pse)),
                           "bias_z_block_se": (float((est.mean() - true) / math.hypot(sd / np.sqrt(len(est)), bse))
                                               if bse else None),
                           "roots_80": float(sims[0]["n_roots"] * (2.8 * sd / true) ** 2) if true > 0 else None})
    n6 = [s["n6"] for s in sims if "n6" in s]
    if not n6:
        return out
    est = np.array([v["per_decision"] for v in n6])
    truth = np.array([v["truth_per_decision"] for v in n6])
    proc = float(truth.mean())
    cir = [v["ci_refit_per_decision"] for v in n6]
    cif = [v["ci_fixed_per_decision"] for v in n6]
    diff = est - truth
    out["n6"] = {"per_decision_mean": float(est.mean()), "per_decision_sd": float(est.std(ddof=1)),
                 "truth_mean": proc, "truth_sd": float(truth.std(ddof=1)),
                 "bias_z": float(diff.mean() / (diff.std(ddof=1) / np.sqrt(len(diff)))),
                 "per_campaign_mean": float(np.mean([v["per_campaign"] for v in n6])),
                 "truth_campaign_mean": float(np.mean([v["truth_per_campaign"] for v in n6])),
                 "flip_rate_mean": float(np.mean([v["flip_rate"] for v in n6])),
                 "cover_refit_truth": _prop([lo <= t <= hi for (lo, hi), t in zip(cir, truth)]),
                 "cover_refit_procedure": _prop([lo <= proc <= hi for lo, hi in cir]),
                 "cover_fixed_truth": _prop([lo <= t <= hi for (lo, hi), t in zip(cif, truth)]),
                 "sd_err": float(diff.std(ddof=1)),
                 "fixed_se_over_sd_err": float(np.mean([(hi - lo) / 3.92 for lo, hi in cif]) / diff.std(ddof=1)),
                 "refit_se_over_sd_err": float(np.mean([(hi - lo) / 3.92 for lo, hi in cir]) / diff.std(ddof=1)),
                 "refit_centre_minus_est_sd": float(np.mean([(lo + hi) / 2 - e for (lo, hi), e in zip(cir, est)])
                                                    / est.std(ddof=1)),
                 "ci_above_0": _prop([lo > 0 for lo, _ in cir]), "ci_below_0": _prop([hi < 0 for _, hi in cir]),
                 "truth_above_0": _prop(truth > 0)}
    return out


def _f(x, d=2) -> str:
    return "—" if x is None else f"{x:.{d}f}"


def _pc(pr) -> str:
    return f"{pr['p']:.3f} ± {1.96 * pr['mc_se']:.3f}"


def _r80(x) -> str:
    return "—" if x is None else f"{x:,.0f}"


def markdown(res: dict) -> str:
    L = ["# Fork design and go/no-go statistics: validation on E-SYN", "",
         "ENGINEERING_ONLY. Generated by `python -m paperc.forks_validation` (build runbook P6, step 4; revised after "
         "review round 1); data in `esyn/fork_validation_v1.json` (code fingerprint checked by the tests). E-SYN "
         "results are implementation checks, not evidence about the real loop.", "",
         f"Set-up: behaviour = each world's tuned N1; continuation policies N1 and N0 (static thresholds on the "
         f"belief); r = 2; design q_uniform = {Q_UNIFORM}, q_oversample = {Q_OVERSAMPLE}, near bands {BAND} sigma_cmp "
         f"around N1's g and h; {N_ROOTS} roots per collection. Measurement noise after a fork is independent per arm "
         "(a departure from Track S's analysis simulator, see `paperc.esyn.sim`): within-fork variances, precision and "
         f"power are conditional on it. Intervals: 95 % percentile cluster bootstrap over roots (B = {B_TAU} for "
         f"tau^2, {B_N6} for N6). Proportions carry ± 1.96 Monte Carlo s.e. Units: raw metric; tau = sqrt(tau^2) also "
         "in units of sigma_cmp.", "",
         "`d` is the continuation difference (the total fork difference minus the forked candidate's own increment "
         "if kept); `q` is the total fork Q difference. Which one carries the go/no-go floor is the author's "
         "pre-declaration choice (see `paperc.forks`). Pooled tau^2 includes the difference between the E1 and E2 "
         "mean differences; per-epoch values do not.", ""]
    a, pops = res["fresh"]["strict_null"], res["population"]
    L += ["## A. Null world: coverage of tau^2 = 0 for `d`", "",
          f"`strict_null`, {a['n_sims']} independent collections (mean {a['forks_mean']:.0f} forks of "
          f"{a['eligible_mean']:.0f} eligible decisions each). With continuation policies that ignore the arms' "
          "bookkeeping (here N1 and N0), the true d is 0 for every state; a budget-aware continuation would break "
          "this.", "",
          "| Statistic | Mean tau^2_hat (× 1e-6) | MC s.e. (× 1e-6) | Coverage of 0 | Lower bound > 0 | "
          "bootstrap s.e. / sd |", "|---|---|---|---|---|---|"]
    for k, lab in (("tau2_d", "d, pooled"), ("tau2_d_E1", "d, E1 forks"), ("tau2_d_E2", "d, E2 forks"),
                   ("tau2_d_c0", "d, continuation N1"), ("tau2_d_c1", "d, continuation N0"), ("tau2_q", "q, pooled")):
        v = a[k]
        L.append(f"| {lab} | {v['mean'] * 1e6:.3f} | {v['mc_se'] * 1e6:.3f} | {_pc(v['cover_0'])} | "
                 f"{_pc(v['detect'])} | {_f(v['boot_se_ratio'])} |")
    L += ["", "## B. Design-unbiasedness and N6 cross-fitting on oracle roots", "",
          f"{N_OR} roots per world, every eligible decision forked with {R_OR} replicates per continuation policy. "
          f"Over {N_DESIGN} selection redraws: z of the HT / Hajek / unweighted means of the replicate-1-2 differences "
          "against the population mean of the same differences (selection error only: the design-unbiasedness "
          "check), and of HT against the mean of replicates 3-R (independent replicates: a check that replicates are "
          "seeded alike). N6: estimate minus the value of the same cross-fitted decisions on the same forks under "
          f"replicates 3-{R_OR}, mean over {N_LEAK} redraws, z with the standard error of the shared replicate noise.", "",
          "| World | States | HT z (q) | Hajek z (q) | unweighted z (q) | HT vs reps 3-R z (q) | HT z (d) | "
          "Hajek z (d) | unweighted z (d) | HT vs reps 3-R z (d) | N6 estimate − value (× 1e-5) | z |",
          "|" + "---|" * 12]
    for wname in WORLD_ORDER:
        o = res["oracle"][wname]
        de, lk = o["design"], o["n6_leak"]
        L.append(f"| {wname} | {o['n_states']} | {de['ht_q']['z_vs_pop12']:+.2f} | {de['hajek_q']['z_vs_pop12']:+.2f} | "
                 f"{de['unw_q']['z_vs_pop12']:+.1f} | {de['ht_q']['z_vs_reps3R']:+.2f} | "
                 f"{de['ht_d']['z_vs_pop12']:+.2f} | {de['hajek_d']['z_vs_pop12']:+.2f} | "
                 f"{de['unw_d']['z_vs_pop12']:+.1f} | {de['ht_d']['z_vs_reps3R']:+.2f} | {lk['mean'] * 1e5:+.2f} | "
                 f"{_f(lk['z'])} |")
    L += ["", "## P. Population tau^2 (the truth for coverage)", "",
          f"{N_POP} roots per world (instances {POP_BASE}+), every eligible decision forked, r = 2. The last column "
          "gives tau^2_d for disjoint 400-root blocks to show how the population estimate varies across root samples.", "",
          "| World | States | tau_d / sigma | tau^2_d (× 1e-6) [95 % CI] | tau^2_d E1 | tau^2_d E2 | tau_q / sigma | "
          "tau^2_q (× 1e-6) [95 % CI] | tau^2_d of 400-root blocks |", "|" + "---|" * 9]
    for wname in WORLD_ORDER:
        pp, sg = pops[wname], WORLDS[wname].base.sigma_cmp
        cell = lambda t: f"{t['tau2'] * 1e6:.3f} [{t['ci'][0] * 1e6:.3f}, {t['ci'][1] * 1e6:.3f}]"   # noqa: E731
        L.append(f"| {wname} | {pp['n_states']} | {math.sqrt(max(pp['d']['tau2'], 0)) / sg:.3f} | {cell(pp['d'])} | "
                 f"{pp['d_E1']['tau2'] * 1e6:.3f} | {pp['d_E2']['tau2'] * 1e6:.3f} | "
                 f"{math.sqrt(max(pp['q']['tau2'], 0)) / sg:.3f} | {cell(pp['q'])} | "
                 f"{', '.join(f'{x * 1e6:.2f}' for x in pp['d']['blocks_400'])} |")
    L += ["", "## C. Fresh roots: tau^2 detection and coverage", "",
          f"{N_C} independent collections of {N_ROOTS} roots per channel world (null: the {a['n_sims']} collections of "
          "A). *covers pop.*: the interval contains the population value of P. *bias z*: mean tau^2_hat against the "
          "population value, with the population's bootstrap s.e.; *(block s.e.)*: with the s.e. from the spread of its "
          "400-root blocks instead. *boot s.e. / sd*: mean bootstrap "
          "standard error (interval width / 3.92) over the sd of tau^2_hat across collections (below 1: intervals "
          "too narrow). *roots for 80 %*: n (2.8 sd / tau^2_pop)^2, n the roots per collection.", "",
          "| World | Forks | d: detect | d: covers pop. | d: bias z | d: bias z (block s.e.) | d: boot s.e. / sd | "
          "d: roots for 80 % | d E1: detect | d E2: detect | q: detect | q: covers pop. | q: boot s.e. / sd |",
          "|" + "---|" * 13]
    for wname in WORLD_ORDER:
        c = res["fresh"][wname]
        L.append(f"| {wname} | {c['forks_mean']:.0f} | {_pc(c['tau2_d']['detect'])} | {_pc(c['tau2_d']['cover_pop'])} | "
                 f"{c['tau2_d']['bias_z_vs_pop']:+.2f} | {_f(c['tau2_d']['bias_z_block_se'])} | "
                 f"{_f(c['tau2_d']['boot_se_ratio'])} | "
                 f"{_r80(c['tau2_d']['roots_80'])} | {_pc(c['tau2_d_E1']['detect'])} | {_pc(c['tau2_d_E2']['detect'])} | "
                 f"{_pc(c['tau2_q']['detect'])} | {_pc(c['tau2_q']['cover_pop'])} | {_f(c['tau2_q']['boot_se_ratio'])} |")
    L += ["", f"### C2. Sample size: {N_ROOTS_BIG} roots per collection", "", f"{N_C2} collections per world, tau^2 only.",
          "", "| World | Forks | d: detect | d: covers pop. | d: bias z | d: bias z (block s.e.) | d: boot s.e. / sd | "
          "d: roots for 80 % |", "|---|---|---|---|---|---|---|---|"]
    for wname in C2_WORLDS:
        c = res["fresh_big"][wname]
        L.append(f"| {wname} | {c['forks_mean']:.0f} | {_pc(c['tau2_d']['detect'])} | {_pc(c['tau2_d']['cover_pop'])} | "
                 f"{c['tau2_d']['bias_z_vs_pop']:+.2f} | {_f(c['tau2_d']['bias_z_block_se'])} | "
                 f"{_f(c['tau2_d']['boot_se_ratio'])} | {_r80(c['tau2_d']['roots_80'])} |")
    L += ["", "## C (N6). The cross-fitted value of the N6 improvement step", "",
          "Per eligible decision: the gain of deviating from the behaviour at one decision as pi' says and then "
          "following the continuation policies (per campaign: the HT total of these one-decision gains per root, not "
          "the value of running pi' for a whole campaign). *Truth*: the population value (P's states) of each "
          "collection's own fitted rules; *procedure*: the mean truth over collections. *Refit* (primary): refitting "
          "bootstrap, copies of a root share its fold. *Fixed*: cross-fitted decisions held fixed. *s.e. / sd(err)*: "
          "mean bootstrap s.e. over the sd of (estimate − truth) across collections. CI > 0 / < 0 refer to the primary "
          "interval.", "",
          "| World | Estimate (× 1e-4) | Truth (× 1e-4) | Bias z | Refit: covers truth | Refit: covers procedure | "
          "Refit s.e. / sd(err) | Fixed: covers truth | Fixed s.e. / sd(err) | CI > 0 | CI < 0 | Truth > 0 | flip rate |",
          "|" + "---|" * 13]
    for wname in WORLD_ORDER:
        v = res["fresh"][wname]["n6"]
        L.append(f"| {wname} | {v['per_decision_mean'] * 1e4:+.3f} | {v['truth_mean'] * 1e4:+.3f} | {v['bias_z']:+.2f} | "
                 f"{_pc(v['cover_refit_truth'])} | {_pc(v['cover_refit_procedure'])} | {v['refit_se_over_sd_err']:.2f} | "
                 f"{_pc(v['cover_fixed_truth'])} | {v['fixed_se_over_sd_err']:.2f} | "
                 f"{_pc(v['ci_above_0'])} | {_pc(v['ci_below_0'])} | {_pc(v['truth_above_0'])} | "
                 f"{v['flip_rate_mean']:.3f} |")
    L += ["", "## Limitations", ""] + limitations(res) + [""]
    return "\n".join(L) + "\n"


def limitations(res: dict) -> list[str]:
    fr, pops = res["fresh"], res["population"]
    big = res["fresh_big"]
    rd = [fr[w]["tau2_d"]["boot_se_ratio"] for w in WORLD_ORDER] + [big[w]["tau2_d"]["boot_se_ratio"] for w in C2_WORLDS]
    rq = [fr[w]["tau2_q"]["boot_se_ratio"] for w in WORLD_ORDER]
    blocks = pops["shared_error"]["d"]["blocks_400"]
    q_null = pops["strict_null"]["q"]["tau2"]
    q_others = [pops[w]["q"]["tau2"] for w in WORLD_ORDER[1:]]
    n6_neg = [w for w in WORLD_ORDER if fr[w]["n6"]["per_decision_mean"] < 0]
    det6 = max(fr[w]["n6"]["ci_above_0"]["p"] for w in WORLD_ORDER)
    cf = [fr[w]["n6"]["cover_fixed_truth"]["p"] for w in WORLD_ORDER]
    cr = [fr[w]["n6"]["cover_refit_truth"]["p"] for w in WORLD_ORDER]
    crp = [fr[w]["n6"]["cover_refit_procedure"]["p"] for w in WORLD_ORDER]
    shared_error = big["shared_error"]["tau2_d"]
    refit_centres = [fr[w]["n6"]["refit_centre_minus_est_sd"] for w in WORLD_ORDER]
    return [
        f"- **Interval width.** The tau^2 intervals are too narrow by up to {100 * (1 - min(rd)):.0f} % for `d` and "
        f"{100 * (1 - min(rq)):.0f} % for `q` (bootstrap s.e. / sd across collections; ratios {min(rd):.2f}-"
        f"{max(rd):.2f} and {min(rq):.2f}-{max(rq):.2f}). The s.e. of a variance estimate depends on fourth moments, "
        "which 40 clusters estimate poorly when fork differences are heavy-tailed.",
        f"- **Precision of population values.** Disjoint 400-root blocks give tau^2_d = "
        f"{', '.join(f'{x * 1e6:.2f}' for x in blocks)} (× 1e-6) in `shared_error`. Round 1 used 400 roots for "
        f"the population reference. P now uses {N_POP} roots for coverage, bias and power calculations. In C2, "
        f"`shared_error` coverage is {shared_error['cover_pop']['p']:.2f}. Its bias z is "
        f"{shared_error['bias_z_vs_pop']:+.2f} using the population bootstrap s.e. and "
        f"{_f(shared_error['bias_z_block_se'])} using the block s.e. The latter is estimated from four blocks. "
        "The round-1 same-root probe found agreement with each block's reference value under design resampling.",
        "- **Power.** Detecting heterogeneity in `d` needs roughly the 'roots for 80 %' column: a few dozen roots where "
        "tau_d is large (interaction, keep_feedback), hundreds to thousands where it is small (budget, shared_error, "
        "eval_allocation) or heavy-tailed (information). The figures are conditional on the independent-noise "
        "convention and on the design above.",
        f"- **q does not separate the null world.** Population tau^2_q is {q_null * 1e6:.1f} × 1e-6 in `strict_null` "
        f"and {min(q_others) * 1e6:.1f}-{max(q_others) * 1e6:.1f} × 1e-6 in the channel worlds; its lower bound "
        f"exceeds 0 in {100 * fr['strict_null']['tau2_q']['detect']['p']:.0f} % of null collections. At these "
        "settings `q` heterogeneity is dominated by the one-step value.",
        f"- **N6 at 40 roots.** The primary refit interval is entirely above zero in at most "
        f"{100 * det6:.1f} % of collections in any world. The mean point estimate is negative in {len(n6_neg)} of 7 "
        f"worlds ({', '.join(n6_neg) or 'none'}).",
        f"- **N6 intervals.** The refit interval covers each collection's own truth in {min(cr):.3f}-{max(cr):.3f} "
        f"and the procedure value in {min(crp):.3f}-{max(crp):.3f} of collections across worlds. Mean refit interval "
        f"centres minus the estimate range from {min(refit_centres):+.2f} to {max(refit_centres):+.2f} estimate "
        f"s.d. The fixed-decision interval covers the fitted-rule truth in {min(cf):.3f}-{max(cf):.3f} "
        "of collections. Holding each fold's fitted rule fixed omits variation from its training sample.",
        "- **Not covered here.** There is no path yet from logged records (root and fork rows with audited terminals, "
        "no noise-free increment) to a `ForkTable`, so the statistics cannot yet run on SPT-1 records (B11). Fork "
        "ids are unique for llm_cap < 1000.",
    ]


def main(argv=None) -> Path:
    t0 = time.time()
    with Pool(2) as pool:
        orc = dict(zip(WORLD_ORDER, pool.map(oracle, WORLD_ORDER)))
        popres = dict(zip(WORLD_ORDER, pool.map(population, WORLD_ORDER)))
    pops = {k: v["summary"] for k, v in popres.items()}
    arrays = {k: v["arrays"] for k, v in popres.items()}
    with Pool(2, initializer=_init, initargs=(arrays,)) as pool:
        fresh = {w: pool.map(one_collection, [(w, s, N_ROOTS, 0, True)
                                              for s in range(N_A if w == "strict_null" else N_C)])
                 for w in WORLD_ORDER}
        big = {w: pool.map(one_collection, [(w, s, N_ROOTS_BIG, C2_BASE, False) for s in range(N_C2)])
               for w in C2_WORLDS}
    res = {"schema": "paperc_fork_validation/v2", "label": "ENGINEERING_ONLY", "code_sha256": code_sha256(),
           "constants": {"N_ROOTS": N_ROOTS, "N_A": N_A, "N_C": N_C, "N_OR": N_OR, "R_OR": R_OR, "OR_BASE": OR_BASE,
                         "N_DESIGN": N_DESIGN, "N_LEAK": N_LEAK, "N_POP": N_POP, "POP_BASE": POP_BASE,
                         "N_ROOTS_BIG": N_ROOTS_BIG, "N_C2": N_C2, "C2_BASE": C2_BASE, "B_TAU": B_TAU, "B_N6": B_N6,
                         "Q_UNIFORM": Q_UNIFORM, "Q_OVERSAMPLE": Q_OVERSAMPLE, "BAND": BAND},
           "oracle": orc, "population": pops,
           "fresh": {k: summarise(k, v, pops[k]) for k, v in fresh.items()},
           "fresh_big": {k: summarise(k, v, pops[k]) for k, v in big.items()},
           "raw": {"fresh": {k: [_raw(x) for x in v] for k, v in fresh.items()},
                   "fresh_big": {k: [_raw(x) for x in v] for k, v in big.items()}},
           "seconds": round(time.time() - t0, 1)}
    OUT.write_text(json.dumps(_clean(res), indent=1, allow_nan=False) + "\n")
    REPORT.write_text(markdown(res))
    return REPORT


def report_only() -> Path:
    """Rewrite the markdown from the committed JSON (no simulation)."""
    REPORT.write_text(markdown(json.loads(OUT.read_text())))
    return REPORT


if __name__ == "__main__":
    print(report_only() if "--report-only" in sys.argv[1:] else main(sys.argv[1:]))
