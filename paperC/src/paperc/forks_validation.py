"""Validation of the fork design and go/no-go statistics on E-SYN (build runbook P6, step 4):
``python -m paperc.forks_validation`` -> ``esyn/fork_validation_v1.json`` and
``docs/reports/FORK_VALIDATION_20261116.md``.

AI-assisted (Claude, chat session, 16 Nov 2026). ENGINEERING_ONLY. E-SYN results are implementation checks, never
evidence about the real loop.

Set-up in every world: behaviour = the world's tuned N1 (committed ladder table); continuation policies = [N1, N0];
r = 2 replicates (plan §6 SPT-3); design q_uniform = 0.15, q_oversample = 0.5, near bands 0.1 sigma_cmp around N1's
own g and h; 40 roots per simulated collection.

* **A. Null coverage** (``strict_null``, ``N_A`` independent collections on disjoint instances): tau^2_hat of the
  continuation difference ``d`` (true value 0 for every state, see ``paperc.forks``), pooled and per continuation
  policy, with 95 % cluster-bootstrap intervals; coverage of 0. The total difference ``q`` is reported alongside.
* **B. Oracle populations** (every world; ``N_OR`` roots on instances 9000+; every eligible decision forked with
  ``R_OR`` replicates per continuation policy): the population mean and tau^2 of ``q`` and ``d`` (tau2_point on the
  full table: unbiased, its own error reported). Then ``N_DESIGN`` redraws of the selection on the same roots, using
  replicates 1-2 only (the design's r = 2): Horvitz-Thompson, Hajek and unweighted means against (i) the population
  mean of the same replicate-1-2 differences (exact design-unbiasedness) and (ii) the oracle mean. And, for
  ``N_LEAK`` redraws, the cross-fitted N6 value against the oracle value of the same fitted pi' on the same held-out
  forks (no leakage: mean difference 0).
  The 100 redraws share one realisation of the replicate noise, so the leakage mean is tested with the standard
  error of that noise: mean = sum_j c_j e_j with e_j = q_bar(1-2) - q_bar(3-R) of state j and c_j its average
  signed weight over the redraws; s.e. = sqrt(sum_j c_j^2 v_j), v_j = sum_c s_jc^2 (1 / (2 C^2) + 1 / (C^2 (R - 2))).
  (An exact structural test of cross-fitting is in ``tests/test_forks_p6.py``.)
* **P. Population tau^2** (every world; ``N_POP`` roots on instances 8000+, every eligible decision forked, r = 2):
  tau^2 of ``d`` and ``q`` over the population of eligible states, precise enough to serve as the truth for coverage
  (its sampling error is about sqrt(40 / N_POP) of one collection's).
* **C. Fresh roots** (every world, ``N_C`` collections on disjoint instances): tau^2 intervals for ``d`` and ``q``;
  share whose lower bound is above 0 (detection); coverage of the population tau^2 from P (unconditional: P uses
  other roots); the N6 value with its interval. **C2** repeats the tau^2 part with ``N_ROOTS_BIG`` roots per
  collection in the worlds where 40 roots rarely detect (sample size).
"""
from __future__ import annotations

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

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "esyn" / "fork_validation_v1.json"
REPORT = ROOT / "docs" / "reports" / "FORK_VALIDATION_20261116.md"
N_ROOTS, N_A, N_C = 40, 200, 40
N_OR, R_OR, OR_BASE = 60, 16, 9000
N_DESIGN, N_LEAK = 500, 100
N_POP, POP_BASE = 400, 8000
N_ROOTS_BIG, N_C2 = 160, 20
C2_WORLDS = ("budget", "shared_error", "eval_allocation", "information")
B_TAU, B_N6 = 300, 200
Q_UNIFORM, Q_OVERSAMPLE, BAND = 0.15, 0.5, 0.1
WORLD_ORDER = ("strict_null", "budget", "interaction", "shared_error", "eval_allocation", "information",
               "keep_feedback")


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
        return {k: _clean(v) for k, v in x.items() if k != "act"}
    if isinstance(x, (list, tuple)):
        return [_clean(v) for v in x]
    if isinstance(x, (np.floating, float)):
        return None if not math.isfinite(float(x)) else float(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    return x


# ---------------------------------------------------------------- one simulated collection (A and C)

def one_collection(args) -> dict:
    world, s, n_roots, base, with_n6 = (*args, N_ROOTS, 0, True)[:5] if len(args) == 2 else args
    w, beh, conts, design = setup(world)
    ft = F.collect(w, beh, range(base + s * n_roots, base + (s + 1) * n_roots), design, conts, reps=2)
    out = {"sim": s, "n_roots": n_roots, "n_forks": len(ft), "n_eligible": sum(ft.n_eligible.values()),
           "near_share": float(ft.near.mean()) if len(ft) else None}
    for tg in ("d", "q"):
        out[f"tau2_{tg}"] = F.tau2(ft, tg, B=B_TAU, seed=(s, 0))
        for c in range(len(conts)):
            out[f"tau2_{tg}_c{c}"] = F.tau2(ft, tg, cont=c, B=B_TAU, seed=(s, 1 + c))
    out["means_q"] = F.fork_means(ft, "q")
    if with_n6:
        out["n6"] = F.n6_value(ft, B=B_N6, seed=(s, 9))
    return _clean(out)


def population(world: str) -> dict:
    t0 = time.time()
    w, beh, conts, design = setup(world)
    full = F.collect(w, beh, range(POP_BASE, POP_BASE + N_POP), design, conts, reps=2, select_all=True)
    out = {"world": world, "n_roots": N_POP, "n_states": len(full)}
    for tg in ("q", "d"):
        t = F.tau2(full, tg, B=B_TAU, seed=(WORLD_ORDER.index(world), 8))
        out[tg] = {"tau2": t["tau2"], "ci": t["ci"], "between": t["between"], "mean_se2": t["mean_se2"]}
    out["seconds"] = round(time.time() - t0, 1)
    return _clean(out)


# ---------------------------------------------------------------- oracle population (B)

def oracle(world: str) -> dict:
    t0 = time.time()
    w, beh, conts, design = setup(world)
    inst = range(OR_BASE, OR_BASE + N_OR)
    full = F.collect(w, beh, inst, design, conts, reps=R_OR, select_all=True)
    pop = {}
    for tg in ("q", "d"):
        dbar, se2 = F.fork_diffs(full, tg)
        pt = F.tau2_point(dbar, se2, np.ones(len(dbar)))
        boot = F.tau2(full, tg, B=B_TAU, seed=(WORLD_ORDER.index(world), 7))
        pop[tg] = {"mean": float(dbar.mean()), "mean_se_reps": float(np.sqrt(se2.mean() / len(dbar))),
                   "tau2": pt["tau2"], "tau2_ci": boot["ci"], "between": pt["between"], "mean_se2": pt["mean_se2"],
                   "sd_state": float(np.sqrt(max(pt["tau2"], 0.0)))}
    # design redraws on the same roots, replicates 1-2
    roots = {i: sim.run_campaign(w, beh, i, record=True).rows for i in inst}
    key = {(int(full.instance[j]), full.fork_id[j]): j for j in range(len(full))}
    q12, d12 = full.q[:, :, :2].mean(axis=(1, 2)), full.d[:, :, :2].mean(axis=(1, 2))
    qtrue = full.q[:, :, 2:].mean(axis=(1, 2))      # replicates 3..R_OR: independent of the estimate's 1-2
    N = sum(full.n_eligible.values())
    est = {k: [] for k in ("ht_q", "hajek_q", "unw_q", "ht_d", "hajek_d", "unw_d", "n_sel")}
    leak = []
    cj = np.zeros(len(full))                         # average signed weight of each state in the leakage mean
    for rep in range(N_DESIGN):
        d = F.Design(**{**design.__dict__, "design_rep": rep + 1})
        sel, ps = [], []
        for i, rows in roots.items():
            for fp in F.select_forks(w, i, rows, d):
                sel.append(key[(i, fp.fork_id)])
                ps.append(fp.design.p_select)
        sel, wt = np.asarray(sel), 1.0 / np.asarray(ps)
        for tg, v in (("q", q12), ("d", d12)):
            est[f"ht_{tg}"].append(float((wt * v[sel]).sum() / N))
            est[f"hajek_{tg}"].append(float((wt * v[sel]).sum() / wt.sum()))
            est[f"unw_{tg}"].append(float(v[sel].mean()))
        est["n_sel"].append(len(sel))
        if rep < N_LEAK:
            sub = full.subset(sel)
            sub.p_select = np.asarray(ps)
            sub.q = sub.q[:, :, :2]
            sub.d = sub.d[:, :, :2]
            sub.reps = 2
            rng = np.random.default_rng([F.ANALYSIS_KEY, 3, rep])
            e = F.n6_point(sub, np.arange(len(sub)), sub.instance, folds=5, alpha=1.0, min_train=10, rng=rng,
                           qbar=sub.q.mean(axis=(1, 2)))
            b = sub.b_act
            true_gain = (e["act"] != b) * np.where(e["act"], 1.0, -1.0) * qtrue[sel]
            leak.append(e["per_decision"] - float((wt * true_gain).sum() / wt.sum()))
            np.add.at(cj, sel, (e["act"] != b) * np.where(e["act"], 1.0, -1.0) * wt / wt.sum() / N_LEAK)
    des = {}
    for tg, v in (("q", q12), ("d", d12)):
        target12 = float(v.mean())
        for kind in ("ht", "hajek", "unw"):
            x = np.asarray(est[f"{kind}_{tg}"])
            mc = float(x.std(ddof=1) / np.sqrt(len(x)))
            # replicate noise: the population mean of the 1-2 differences (4 of the 2 R_OR cells) and the oracle mean
            se_or = math.sqrt(mc ** 2 + (R_OR / 2 + 1) * pop[tg]["mean_se_reps"] ** 2)
            des[f"{kind}_{tg}"] = {"mean": float(x.mean()), "mc_se": mc, "bias_vs_pop12": float(x.mean() - target12),
                                   "z_vs_pop12": float((x.mean() - target12) / mc),
                                   "bias_vs_oracle": float(x.mean() - pop[tg]["mean"]),
                                   "z_vs_oracle": float((x.mean() - pop[tg]["mean"]) / se_or)}
        des[f"pop12_{tg}"] = target12
    leak = np.asarray(leak)
    C_, R_ = full.q.shape[1], full.q.shape[2]
    e_j = q12 - qtrue
    v_j = full.q.var(axis=2, ddof=1).sum(axis=1) * (1 / (2 * C_ ** 2) + 1 / (C_ ** 2 * (R_ - 2)))
    leak_se = float(np.sqrt((cj ** 2 * v_j).sum()))
    return _clean({"world": world, "n_roots": N_OR, "reps": R_OR, "n_states": len(full), "n_eligible": N,
                   "population": pop, "design": des, "mean_selected": float(np.mean(est["n_sel"])),
                   "n6_leak": {"mean": float(leak.mean()), "linear_mean": float((cj * e_j).sum()),
                               "se_replicate_noise": leak_se, "z": float(leak.mean() / leak_se) if leak_se > 0 else None,
                               "mc_se_redraws_only": float(leak.std(ddof=1) / np.sqrt(len(leak))), "n": len(leak)},
                   "seconds": round(time.time() - t0, 1)})


# ---------------------------------------------------------------- summaries

def _prop(x) -> dict:
    x = np.asarray(x, float)
    p, n = float(x.mean()), len(x)
    return {"p": p, "n": n, "mc_se": float(math.sqrt(max(p * (1 - p), 1e-12) / n))}


def _raw(x: dict) -> dict:
    """Compact per-collection record: [estimate, lower, upper] per tau^2 statistic and for the N6 value."""
    out = {"sim": x["sim"], "n_roots": x["n_roots"], "n_forks": x["n_forks"]}
    for k, v in x.items():
        if k.startswith("tau2_"):
            out[k] = [v["tau2"], *(v["ci"] or (None, None))]
    if "n6" in x:
        out["n6"] = [x["n6"]["per_decision"], *x["n6"].get("ci_per_decision", (None, None))]
    return out


def summarise(world: str, sims: list[dict], pop: dict) -> dict:
    out = {"n_sims": len(sims), "forks_mean": float(np.mean([s["n_forks"] for s in sims])),
           "eligible_mean": float(np.mean([s["n_eligible"] for s in sims]))}
    for tg in ("d", "q"):
        true = pop[tg]["tau2"]
        for suf in ("", "_c0", "_c1"):
            k = f"tau2_{tg}{suf}"
            est = np.array([s[k]["tau2"] for s in sims])
            ci = [s[k]["ci"] for s in sims]
            sd = float(est.std(ddof=1))
            boot_se = float(np.mean([(hi - lo) / 3.92 for lo, hi in ci]))
            out[k] = {"mean": float(est.mean()), "mc_se": sd / np.sqrt(len(est)), "sd": sd, "mean_boot_se": boot_se,
                      "boot_se_ratio": boot_se / sd if sd > 0 else None,
                      "cover_0": _prop([lo <= 0 <= hi for lo, hi in ci]),
                      "detect": _prop([lo > 0 for lo, _ in ci])}
            if suf == "":
                out[k]["cover_pop"] = _prop([lo <= true <= hi for lo, hi in ci])
                out[k]["pop_tau2"] = true
                out[k]["bias_z_vs_pop"] = float((est.mean() - true) /
                                                math.hypot(est.std(ddof=1) / np.sqrt(len(est)),
                                                           (pop[tg]["ci"][1] - pop[tg]["ci"][0]) / 3.92))
                n_roots = sims[0].get("n_roots", N_ROOTS)
                # roots for 80 % power of "lower bound > 0" (two-sided 95 %), from the observed sd: n (2.8 sd / tau^2)^2
                out[k]["roots_80"] = float(n_roots * (2.8 * sd / true) ** 2) if true > 0 else None
    n6 = [s["n6"] for s in sims if "n6" in s]
    if not n6:
        return out
    out["n6"] = {"per_decision_mean": float(np.mean([v["per_decision"] for v in n6])),
                 "per_campaign_mean": float(np.mean([v["per_campaign"] for v in n6])),
                 "flip_rate_mean": float(np.mean([v["flip_rate"] for v in n6])),
                 "ci_above_0": _prop([v["ci_per_decision"][0] > 0 for v in n6]),
                 "ci_below_0": _prop([v["ci_per_decision"][1] < 0 for v in n6])}
    return out


def _f(x, d=2) -> str:
    return "—" if x is None else f"{x:.{d}f}"


def _pc(pr) -> str:
    return f"{pr['p']:.3f} ± {1.96 * pr['mc_se']:.3f}"


def markdown(res: dict) -> str:
    L = ["# Fork design and go/no-go statistics: validation on E-SYN", "",
         "ENGINEERING_ONLY. Generated by `python -m paperc.forks_validation` (build runbook P6, step 4); data in "
         "`esyn/fork_validation_v1.json`. E-SYN results are implementation checks, not evidence about the real loop.",
         "",
         f"Set-up: behaviour = each world's tuned N1; continuation policies N1 and N0; r = 2; design q_uniform = "
         f"{Q_UNIFORM}, q_oversample = {Q_OVERSAMPLE}, near bands {BAND} sigma_cmp around N1's g and h; {N_ROOTS} roots per "
         f"collection. Intervals: 95 % percentile cluster bootstrap over roots (B = {B_TAU} for tau^2, {B_N6} with "
         "refitting for N6). Proportions carry ± 1.96 Monte Carlo s.e. Units: raw metric; tau^2 in squared raw units, "
         "tau = sqrt(tau^2) also in units of sigma_cmp.", "",
         "`d` is the continuation difference (the total fork difference minus the forked candidate's own increment "
         "if kept); `q` is the total fork Q difference. Which one carries the go/no-go floor is the author's "
         "pre-declaration choice (see `paperc.forks`).", ""]
    a, pops = res["fresh"]["strict_null"], res["population"]
    L += ["## A. Null world: coverage of tau^2 = 0 for `d`", "",
          f"`strict_null`, {a['n_sims']} independent collections (mean {a['forks_mean']:.0f} forks of "
          f"{a['eligible_mean']:.0f} eligible decisions each). The true tau^2 of `d` is 0 for every state.", "",
          "| Statistic | Mean tau^2_hat (× 1e-6) | MC s.e. (× 1e-6) | Coverage of 0 | Lower bound > 0 | "
          "bootstrap s.e. / sd across collections |", "|---|---|---|---|---|---|"]
    for k, lab in (("tau2_d", "d, pooled"), ("tau2_d_c0", "d, continuation N1"), ("tau2_d_c1", "d, continuation N0"),
                   ("tau2_q", "q, pooled")):
        v = a[k]
        L.append(f"| {lab} | {v['mean'] * 1e6:.3f} | {v['mc_se'] * 1e6:.3f} | {_pc(v['cover_0'])} | "
                 f"{_pc(v['detect'])} | {_f(v['boot_se_ratio'])} |")
    L += ["", "## B. Design-unbiasedness against the oracle, and N6 cross-fitting", "",
          f"{N_OR} roots per world, every eligible decision forked with {R_OR} replicates per continuation policy. "
          f"Mean over {N_DESIGN} selection redraws of the HT / Hajek / unweighted means of the replicate-1-2 "
          "differences: z of the bias against the population mean of the same differences (selection error only), "
          "and z against the oracle mean (replicate noise of both population means added). N6: the cross-fitted "
          f"estimate (replicates 1-2) minus the value of the same pi' on the same forks under replicates 3-{R_OR}, "
          f"averaged over {N_LEAK} redraws, with the standard error of the shared replicate noise.", "",
          "| World | States | mean q (× 1e-3) | HT z (q) | Hajek z (q) | unweighted z (q) | HT vs oracle z (q) | "
          "HT z (d) | Hajek z (d) | unweighted z (d) | N6 estimate − oracle (× 1e-5) | z |", "|" + "---|" * 12]
    for wname in WORLD_ORDER:
        o = res["oracle"][wname]
        de, lk = o["design"], o["n6_leak"]
        L.append(f"| {wname} | {o['n_states']} | {o['population']['q']['mean'] * 1e3:.3f} | "
                 f"{de['ht_q']['z_vs_pop12']:+.2f} | {de['hajek_q']['z_vs_pop12']:+.2f} | "
                 f"{de['unw_q']['z_vs_pop12']:+.1f} | {de['ht_q']['z_vs_oracle']:+.2f} | "
                 f"{de['ht_d']['z_vs_pop12']:+.2f} | {de['hajek_d']['z_vs_pop12']:+.2f} | "
                 f"{de['unw_d']['z_vs_pop12']:+.1f} | {lk['mean'] * 1e5:+.2f} | {_f(lk['z'])} |")
    L += ["", "## P. Population tau^2 (the truth for coverage)", "",
          f"{N_POP} roots per world (instances {POP_BASE}+), every eligible decision forked, r = 2.", "",
          "| World | States | tau_d / sigma | tau^2_d (× 1e-6) [95 % CI] | tau_q / sigma | tau^2_q (× 1e-6) [95 % CI] |",
          "|---|---|---|---|---|---|"]
    for wname in WORLD_ORDER:
        pp, sg = pops[wname], WORLDS[wname].base.sigma_cmp
        cell = lambda t: f"{t['tau2'] * 1e6:.3f} [{t['ci'][0] * 1e6:.3f}, {t['ci'][1] * 1e6:.3f}]"   # noqa: E731
        L.append(f"| {wname} | {pp['n_states']} | {math.sqrt(max(pp['d']['tau2'], 0)) / sg:.3f} | {cell(pp['d'])} | "
                 f"{math.sqrt(max(pp['q']['tau2'], 0)) / sg:.3f} | {cell(pp['q'])} |")
    L += ["", "## C. Fresh roots: detection, coverage of the population tau^2, N6", "",
          f"{N_C} independent collections of {N_ROOTS} roots per channel world (null: the {a['n_sims']} collections of "
          "A). Bias z: mean tau^2_hat against the population value, with both errors.", "",
          "| World | Forks / collection | d: detect | d: covers pop. | d: bias z | d: boot s.e. / sd | d: roots for 80 % "
          "power | q: detect | q: covers pop. | q: bias z | q: boot s.e. / sd | N6 per decision (× 1e-4) | "
          "N6 per campaign (× 1e-3) | N6 CI > 0 | N6 CI < 0 | flip rate |", "|" + "---|" * 16]
    for wname in WORLD_ORDER:
        c = res["fresh"][wname]
        r80 = c["tau2_d"]["roots_80"]
        L.append(f"| {wname} | {c['forks_mean']:.0f} | {_pc(c['tau2_d']['detect'])} | {_pc(c['tau2_d']['cover_pop'])} | "
                 f"{c['tau2_d']['bias_z_vs_pop']:+.2f} | {_f(c['tau2_d']['boot_se_ratio'])} | "
                 f"{'—' if r80 is None else f'{r80:,.0f}'} | {_pc(c['tau2_q']['detect'])} | "
                 f"{_pc(c['tau2_q']['cover_pop'])} | {c['tau2_q']['bias_z_vs_pop']:+.2f} | "
                 f"{_f(c['tau2_q']['boot_se_ratio'])} | "
                 f"{c['n6']['per_decision_mean'] * 1e4:+.3f} | {c['n6']['per_campaign_mean'] * 1e3:+.3f} | "
                 f"{_pc(c['n6']['ci_above_0'])} | {_pc(c['n6']['ci_below_0'])} | {c['n6']['flip_rate_mean']:.3f} |")
    L += ["", f"### C2. Sample size: {N_ROOTS_BIG} roots per collection", "",
          f"{N_C2} collections per world, tau^2 only.", "",
          "| World | Forks / collection | d: detect | d: covers pop. | d: bias z | d: boot s.e. / sd | d: roots for 80 % "
          "power |", "|---|---|---|---|---|---|---|"]
    for wname in C2_WORLDS:
        c = res["fresh_big"][wname]
        r80 = c["tau2_d"]["roots_80"]
        L.append(f"| {wname} | {c['forks_mean']:.0f} | {_pc(c['tau2_d']['detect'])} | "
                 f"{_pc(c['tau2_d']['cover_pop'])} | {c['tau2_d']['bias_z_vs_pop']:+.2f} | "
                 f"{_f(c['tau2_d']['boot_se_ratio'])} | {'—' if r80 is None else f'{r80:,.0f}'} |")
    L += ["", "Notes. *bootstrap s.e. / sd*: the mean bootstrap standard error (interval width / 3.92) over the sd of "
          "tau^2_hat across the independent collections; below 1, the intervals are too narrow. The s.e. of a "
          "variance estimate depends on fourth moments, which 40 clusters estimate poorly when the fork differences "
          "are heavy-tailed. *Roots for 80 % power*: n x (2.8 sd / tau^2_pop)^2 with n the roots per collection (40, or "
          f"{N_ROOTS_BIG} in C2), from the observed sd and the "
          "population tau^2 of P (rough: both are uncertain, and the sd is taken to scale as 1 / sqrt(roots)). "
          "The population values in P carry the same fourth-moment problem, so coverage against them is approximate.",
          ""]
    return "\n".join(L) + "\n"


def main(argv=None) -> Path:
    t0 = time.time()
    with Pool(2) as pool:
        orc = dict(zip(WORLD_ORDER, pool.map(oracle, WORLD_ORDER)))
        pops = dict(zip(WORLD_ORDER, pool.map(population, WORLD_ORDER)))
        fresh = {w: pool.map(one_collection, [(w, s) for s in range(N_A if w == "strict_null" else N_C)])
                 for w in WORLD_ORDER}
        big = {w: pool.map(one_collection, [(w, s, N_ROOTS_BIG, 2000, False) for s in range(N_C2)])
               for w in C2_WORLDS}
    res = {"schema": "paperc_fork_validation/v1", "label": "ENGINEERING_ONLY",
           "constants": {"N_ROOTS": N_ROOTS, "N_A": N_A, "N_C": N_C, "N_OR": N_OR, "R_OR": R_OR, "N_DESIGN": N_DESIGN,
                         "N_LEAK": N_LEAK, "N_POP": N_POP, "N_ROOTS_BIG": N_ROOTS_BIG, "N_C2": N_C2, "B_TAU": B_TAU,
                         "B_N6": B_N6, "Q_UNIFORM": Q_UNIFORM, "Q_OVERSAMPLE": Q_OVERSAMPLE, "BAND": BAND},
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
