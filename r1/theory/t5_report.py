#!/usr/bin/env python3
"""T5 runner: simulation checks of the T4 theory (ENGINEERING_ONLY; AI-assisted (Claude)).

Model-based numbers, not measurements. Usage:

    python -m r1.theory.t5_report --out results/r1/engineering/T5_<stamp> [--max-seconds S] [--quick]

The run is split into parts; each part is written to <out>/parts/<name>.json and skipped when it
already exists, so an interrupted run resumes where it stopped (``--max-seconds`` stops cleanly
between parts). When every part exists, <out>/tables.md and <out>/manifest.json are (re)written.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import subprocess
import sys
import time
import zlib
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from r1.theory.simulate_t4 import (BranchStudy, Node, Policy, Proposer, PType, Scenario, branch_stats,
                                   branch_study, di_flag_rate, fit_constants, paired, prop10b_loss, public,
                                   reweight, simulate, tune, type_summary)

BASE_SEED = 20261019

# --------------------------------------------------------------------------------------------
# Calibration to pilot scales (PILOT values; see docs/r1/theory/T5_SIMULATION.md, "Setup")
# --------------------------------------------------------------------------------------------
# digits_mlp: per-run sigma 0.0125 (E1); local rho 0.82 -> paired sd 0.0075 (E1b manifest sigma_d);
# structural rho 0.55 -> 0.0119. tabular_mlp: paired sd 0.0046 (rerun-2 manifest); local rho 0.85,
# structural 0.60. Split share of the paired variance: sigma_s^2 / sigma_d^2 from the manifests.
DIGITS = Node("digits_mlp", sigma=0.0125, rho_local=0.82, rho_struct=0.55, split_share=0.59)
TABULAR = Node("tabular_mlp", sigma=0.0084, rho_local=0.85, rho_struct=0.60, split_share=0.65)

TYPES = {
    # memory off: larger duplicate share, better informative proposals
    "digits_off": (PType("duplicate/inert", 0.60, 0.0, 0.0, pi=1.0),
                   PType("batch_size (harmful)", 0.10, -0.012, 0.008),
                   PType("hidden_units (promising)", 0.14, 0.004, 0.005),
                   PType("lr/other (neutral)", 0.09, -0.002, 0.006),
                   PType("structural", 0.07, -0.006, 0.014, kind="structural", bold=True)),
    "digits_on": (PType("duplicate/inert", 0.45, 0.0, 0.0, pi=1.0),
                  PType("batch_size (harmful)", 0.20, -0.012, 0.008),
                  PType("hidden_units (promising)", 0.12, 0.002, 0.005),
                  PType("lr/other (neutral)", 0.11, -0.004, 0.006),
                  PType("structural", 0.12, -0.008, 0.014, kind="structural", bold=True)),
    "tabular_off": (PType("duplicate/inert", 0.70, 0.0, 0.0, pi=1.0),
                    PType("harmful", 0.07, -0.006, 0.005),
                    PType("promising", 0.10, 0.002, 0.003),
                    PType("neutral", 0.08, -0.0015, 0.003),
                    PType("structural", 0.05, -0.004, 0.010, kind="structural", bold=True)),
    "tabular_on": (PType("duplicate/inert", 0.45, 0.0, 0.0, pi=1.0),
                   PType("harmful", 0.15, -0.006, 0.005),
                   PType("promising", 0.12, 0.001, 0.003),
                   PType("neutral", 0.18, -0.0025, 0.003),
                   PType("structural", 0.10, -0.004, 0.010, kind="structural", bold=True)),
}
NODE_OF = {"digits_off": DIGITS, "digits_on": DIGITS, "tabular_off": TABULAR, "tabular_on": TABULAR}


def proposer(kind: str, node: Node, kappa: float = 0.3) -> Proposer:
    sd = node.paired_sd
    return Proposer(kind=kind, kappa=kappa if kind == "dimret" else 0.0, bold_max=0.6, trigger=2 * sd, width=0.5 * sd)


def scenario(name: str, noise: str = "iid", prop: str = "stationary", kappa: float = 0.3, types=None) -> Scenario:
    node = NODE_OF[name]
    return Scenario(f"{name}/{noise}/{prop}" + (f"(k={kappa})" if prop == "dimret" else ""), node,
                    TYPES[name] if types is None else types, proposer(prop, node, kappa), noise)


def g_grid(node: Node) -> list:
    return [node.paired_sd * x for x in (0.0, 0.02, 0.05, 0.08, 0.12, 0.17, 0.25, 0.35, 0.5)]


class Ctx:
    def __init__(self, quick: bool):
        self.quick = quick
        self.M = 4000 if quick else 20000        # test campaigns per cell
        self.Mbig = 8000 if quick else 40000     # for paired identity checks
        self.Mdev = 1500 if quick else 4000      # development campaigns (tuning, constants)
        self.n_branch = 6000 if quick else 30000


def seeds(name: str) -> tuple:
    s = (BASE_SEED + zlib.crc32(name.encode())) % (2 ** 31 - 10000)
    return s, s + 7919          # (test seed, development seed)


def gain_row(res: dict, node: Node) -> dict:
    m, se = res["gain"]
    return {"gain": m, "se": se, "gain_dn": m / node.delta_n, "runs": res["runs"], "calls": res["calls"],
            "keeps": res["keeps"], "false_keep_rate": res["false_keep_rate"], "skips_learned": res["skips_learned"]}


# --------------------------------------------------------------------------------------------
# Parts
# --------------------------------------------------------------------------------------------

def part_calibration(ctx, name):
    rows = {}
    for k in TYPES:
        node = NODE_OF[k]
        rows[k] = {**type_summary(TYPES[k]), "sigma_d_local": node.sigma_d("local"),
                   "sigma_d_structural": node.sigma_d("structural"), "delta_n": node.delta_n,
                   "types": [t.__dict__ for t in TYPES[k]]}
    return {"scenarios": rows,
            "prop10b": {"alpha=0.5,beta=2": prop10b_loss(0.5, 2.0), "alpha=0,beta=2": prop10b_loss(0.0, 2.0),
                        "alpha=1.61,beta=2": prop10b_loss(1.61, 2.0), "alpha=0,beta=4": prop10b_loss(0.0, 4.0)}}


def standard_policies(scn, W, N, ctx, dev_seed, const):
    """rho, A1, A1+screen, A2, A2+screen, oracle threshold, oracle threshold+screen (g tuned on dev)."""
    gg = {"g": g_grid(scn.node)}
    P = {"rho": Policy("rho", prior="zero", rules=False),
         "A1": Policy("A1", prior="const", rules=False),
         "A2": Policy("A2", prior="rules"),
         "oracle_threshold": Policy("oracle_threshold", prior="oracle")}
    tuned = {}
    for nm, base in (("A1+screen", Policy("A1+screen", prior="const", rules=False, screen=True)),
                     ("A2+screen", Policy("A2+screen", prior="rules", screen=True)),
                     ("oracle", Policy("oracle", prior="oracle", screen=True))):
        best, tab = tune(scn, base, W, N, ctx.Mdev, dev_seed, const, gg)
        P[nm] = best
        tuned[nm] = {"g": best.g, "dev": tab}
    return P, tuned


def part_main(ctx, name, scn_name, noise, W):
    scn = scenario(scn_name, noise)
    N = 2 * W
    seed, dev = seeds(name)
    const = fit_constants(scn, W, N, ctx.Mdev, dev + 1)
    P, tuned = standard_policies(scn, W, N, ctx, dev, const)
    res = {k: simulate(scn, p, W, N, ctx.M, seed, const) for k, p in P.items()}
    rows = {k: {**gain_row(r, scn.node), "g": P[k].g} for k, r in res.items()}
    for k in res:
        d, se = paired(res[k], res["A2"])
        rows[k]["vs_A2"] = d
        rows[k]["vs_A2_se"] = se
        rows[k]["vs_A2_dn"] = d / scn.node.delta_n
    return {"scenario": scn.name, "W": W, "N": N, "constants": const.to_dict(), "rows": rows,
            "tuning": {k: v["g"] for k, v in tuned.items()}}


def part_p7(ctx, name, scn_name, noise, prop, W):
    scn = scenario(scn_name, noise, prop)
    N = 2 * W
    seed, dev = seeds(name)
    const = fit_constants(scn, W, N, ctx.Mdev, dev + 1)
    # dev-tuned best constant threshold shift for A2 (stronger constant baseline)
    best, _ = tune(scn, Policy("A2tuned", prior="rules"), W, N, ctx.Mdev, dev,
                   const, {"theta0": [-0.6, -0.4, -0.2, 0.0, 0.2, 0.4, 0.6, 0.9]})
    out = {"scenario": scn.name, "W": W, "N": N, "A2_tuned_shift": best.theta0}
    for label, shift in (("moment-matched constant t~", 0.0), ("dev-tuned constant t~", best.theta0)):
        o = simulate(scn, Policy("oracle_threshold", prior="oracle"), W, N, ctx.Mbig, seed,
                     ref=(const.mu_r, const.tau_r, shift))
        a = simulate(scn, Policy("A2", prior="rules", theta0=shift), W, N, ctx.Mbig, seed, const)
        d, se = paired(o, a)
        out[label] = {"realised": d, "realised_se": se, "predicted_sum_gap": o["gap"][0],
                      "predicted_se": o["gap"][1], "lower_bound": o["gap_lo"][0], "upper_bound": o["gap_hi"][0],
                      "realised_over_predicted": d / o["gap"][0] if o["gap"][0] else float("nan"),
                      "realised_dn": d / scn.node.delta_n, "upper_dn": o["gap_hi"][0] / scn.node.delta_n}
    return out


def part_p8(ctx, name, scn_name, noise):
    scn = scenario(scn_name, noise)
    seed, dev = seeds(name)
    out = {"scenario": scn.name, "lagrangian": [], "hard_budget": []}
    # g tuned on dev for the hard budget W = 20, N = 40 (oracle threshold + screening)
    best20, _ = tune(scn, Policy("oracle", prior="oracle", screen=True), 20, 40, ctx.Mdev, dev, None,
                     {"g": g_grid(scn.node)})
    for gm in (0.5, 1.0, 2.0):
        g = best20.g * gm if best20.g > 0 else scn.node.paired_sd * 0.05 * gm
        Nl = 40
        for layer, rules in (("total (vs always execute)", False), ("learned layer (vs rules)", True)):
            a = simulate(scn, Policy("execute", prior="oracle", rules=rules), Nl, Nl, ctx.Mbig, seed, g_eval=g)
            b = simulate(scn, Policy("screen", prior="oracle", rules=rules, screen=True, g=g), Nl, Nl, ctx.Mbig,
                         seed, g_eval=g)
            d, se = paired(b, a, "_lag")
            pred = a["pos_part"] if not rules else a["pos_part_nonrule"]
            out["lagrangian"].append({"g_multiple_of_tuned": gm, "g": g, "layer": layer, "N": Nl,
                                      "realised": d, "realised_se": se, "predicted": pred[0], "predicted_se": pred[1]})
    for W in (20, 40):
        N = 2 * W
        bestW, _ = tune(scn, Policy("oracle", prior="oracle", screen=True), W, N, ctx.Mdev, dev + W, None,
                        {"g": g_grid(scn.node)})
        a = simulate(scn, Policy("oracle_threshold", prior="oracle"), W, N, ctx.M, seed, g_eval=bestW.g)
        b = simulate(scn, bestW, W, N, ctx.M, seed)
        d, se = paired(b, a)
        out["hard_budget"].append({"W": W, "N": N, "g_tuned": bestW.g, "realised_gain": d, "realised_se": se,
                                   "sum_pos_part_over_screen_run": b["pos_part_nonrule"][0],
                                   "skips_learned": b["skips_learned"], "calls_screen": b["calls"],
                                   "calls_noscreen": a["calls"], "runs_screen": b["runs"]})
    return out


def part_p9(ctx, name, scn_name):
    seed, dev = seeds(name)
    out = {"rows": []}
    W, N = 40, 80
    for noise in ("record", "iid"):
        for prop in ("stationary", "dimret", "memory", "memory_debiased"):
            scn = scenario(scn_name, noise, prop)
            for pol in (Policy("rho", prior="zero", rules=False), Policy("oracle_threshold", prior="oracle")):
                r = simulate(scn, pol, W, N, ctx.M, seed)
                out["rows"].append({"scenario": scn.name, "policy": pol.name, **r.get("p9_summary", {}),
                                    "record_bias_end": r["record_bias_end"][0],
                                    "debiased_bias_end": r["debiased_bias_end"][0],
                                    "gain": r["gain"][0], "gain_se": r["gain"][1], "bold_share": r["bold_share"],
                                    "false_keep_rate": r["false_keep_rate"]})
        # raw vs debiased display for the memory proposer; bold edits as calibrated (positive value under
        # selection) or harmful (mean lowered by 1.2 tau, so that V(0) < 0)
        harm = tuple(replace(t, mu=t.mu - 1.2 * t.tau) if t.bold else t for t in TYPES[scn_name])
        for bold_lab, types in (("as calibrated", None), ("harmful bold", harm)):
            for pol in (Policy("rho", prior="zero", rules=False), Policy("oracle_threshold", prior="oracle")):
                a = simulate(scenario(scn_name, noise, "memory_debiased", types=types), pol, W, N, ctx.M, seed)
                b = simulate(scenario(scn_name, noise, "memory", types=types), pol, W, N, ctx.M, seed)
                d, se = paired(a, b)
                out.setdefault("display", []).append({"noise": noise, "bold": bold_lab, "policy": pol.name,
                                                      "debiased_minus_raw": d, "se": se,
                                                      "gain_raw": b["gain"][0], "gain_debiased": a["gain"][0],
                                                      "bold_raw": b["bold_share"], "bold_debiased": a["bold_share"]})
    return out


P10_CASES = [("iid", "stationary", 0.3, "DI holds"), ("iid", "dimret", 0.3, "diminishing returns k=0.3"),
             ("iid", "dimret", 0.8, "diminishing returns k=0.8"), ("iid", "memory", 0.3, "memory-reading (raw B)"),
             ("iid", "memory_debiased", 0.3, "memory-reading (debiased B~)"),
             ("record", "stationary", 0.3, "record channel only"), ("record", "memory", 0.3, "record + memory (raw B)"),
             ("record", "memory_debiased", 0.3, "record + memory (debiased B~)")]


def part_p10(ctx, name, scn_name, W):
    seed, dev = seeds(name)
    N = W
    grid = {"theta0": [-0.4, -0.2, 0.0, 0.2, 0.4, 0.7, 1.0], "theta1": [-0.4, 0.0, 0.4, 0.8, 1.2]}
    out = {"W": W, "N": N, "rows": []}
    for noise, prop, kappa, label in P10_CASES:
        scn = scenario(scn_name, noise, prop, kappa)
        best, tab = tune(scn, Policy("lookahead", prior="oracle"), W, N, ctx.Mdev, dev, None, grid)
        my = simulate(scn, Policy("myopic", prior="oracle"), W, N, ctx.Mbig, seed)
        la = simulate(scn, best, W, N, ctx.Mbig, seed)
        d, se = paired(la, my)
        out["rows"].append({"case": label, "scenario": scn.name, "theta0": best.theta0, "theta1": best.theta1,
                            "myopic": my["gain"][0], "lookahead": la["gain"][0], "diff": d, "diff_se": se,
                            "diff_dn": d / scn.node.delta_n,
                            "dev_gain_gap": max(t["dev_gain"] for t in tab) -
                            [t for t in tab if t["theta0"] == 0.0 and t["theta1"] == 0.0][0]["dev_gain"]})
    return out


DI_STUDIES = {
    # paired split / training sds from the rerun-2 (tabular) and E1b (digits) manifests; fixed split historically
    "tabular": dict(types="tabular_on", sigma_t_d=0.0027, sigma_s_d=0.0037),
    "digits": dict(types="digits_off", sigma_t_d=0.0043, sigma_s_d=0.0062),
}
DI_INERT = 0.03          # metric-identical share of post-point trials in the 19 Oct tables (0.01-0.03)
NEAR_NULL_W = 0.5        # "near-null" mix: share of tweaks with Delta ~ 0 and rho = 0.995 (tiny paired noise)


def di_types(scale: str, mix: str) -> tuple:
    ts = reweight(TYPES[DI_STUDIES[scale]["types"]], inert_share=DI_INERT)
    if mix == "hom":
        return ts
    ts = tuple(replace(t, weight=t.weight * (1 - NEAR_NULL_W)) if t.pi < 1 else t for t in ts)
    return ts + (PType("near-null tweak", NEAR_NULL_W * (1 - DI_INERT), 0.0, 0.0003, rho=0.995),)


def part_di(ctx, name, scale, split, rho, mix="hom", feedback=0.0, noise_scale=1.0):
    seed, _ = seeds(name)
    cfg = DI_STUDIES[scale]
    bs = BranchStudy(f"{scale}/{mix}", di_types(scale, mix), cfg["sigma_t_d"] * noise_scale,
                     cfg["sigma_s_d"] * noise_scale, rho=rho, split=split,
                     feedback_shift=feedback * math.hypot(cfg["sigma_t_d"], cfg["sigma_s_d"]))
    br = branch_study(bs, ctx.n_branch, seed)
    st = branch_stats(br)
    n_study = 6 if scale == "digits" else 18
    fr = di_flag_rate(br, n_study, 199 if ctx.quick else 499, seed + 1)
    return {"study": bs.name, "split": split, "rho": rho, "mix": mix, "feedback_shift_sd": feedback,
            "noise_scale": noise_scale, "sigma_t_d": bs.sigma_t_d, "sigma_s_d": bs.sigma_s_d, "n_inst": ctx.n_branch,
            "q_rep": bs.q_rep, "population": st, "small_studies": fr}


def part_headroom(ctx, name, base, W, homog_tau=False):
    seed, dev = seeds(name)
    N = 2 * W
    node = NODE_OF[base]
    disp = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0]
    inert = [0.2, 0.4, 0.55, 0.7]
    cells = []
    for s in inert:
        for d in disp:
            types = reweight(TYPES[base], inert_share=s, dispersion=d)
            if homog_tau:          # isolate mean dispersion: one within-type tau, all edits local
                trms = type_summary(TYPES[base])["tau_within_rms"]
                types = tuple(replace(t, tau=trms, kind="local") if t.pi < 1 else t for t in types)
            scn = scenario(base, "iid", types=types)
            const = fit_constants(scn, W, N, ctx.Mdev, dev + 1)
            a2s, _ = tune(scn, Policy("A2+screen", prior="rules", screen=True), W, N, ctx.Mdev, dev, const,
                          {"g": g_grid(node)})
            orc, _ = tune(scn, Policy("oracle", prior="oracle", screen=True), W, N, ctx.Mdev, dev, None,
                          {"g": g_grid(node)})
            Mh = ctx.M // 2
            ra2 = simulate(scn, Policy("A2", prior="rules"), W, N, Mh, seed, const)
            ra2s = simulate(scn, a2s, W, N, Mh, seed, const)
            ro = simulate(scn, orc, W, N, Mh, seed)
            d1, se1 = paired(ro, ra2s)
            d2, se2 = paired(ro, ra2)
            ts = type_summary(types)
            cells.append({"inert_share": s, "dispersion": d, "sd_type_means": ts["sd_type_means"],
                          "sd_type_means_over_sigma_d": ts["sd_type_means"] / node.paired_sd,
                          "p_improve_informative": ts["p_improve_informative"],
                          "A2": ra2["gain"][0], "A2_screen": ra2s["gain"][0], "oracle": ro["gain"][0],
                          "oracle_minus_A2screen": d1, "se1": se1, "oracle_minus_A2": d2, "se2": se2,
                          "gain_dn": d1 / node.delta_n, "gain_dn_vs_A2": d2 / node.delta_n,
                          "g_A2s": a2s.g, "g_oracle": orc.g})
    return {"base": base, "W": W, "N": N, "delta_n": node.delta_n, "homog_tau": homog_tau, "cells": cells}


def part_predictor(ctx, name, scn_name, noise, W):
    seed, dev = seeds(name)
    N = 2 * W
    scn = scenario(scn_name, noise)
    node = scn.node
    const = fit_constants(scn, W, N, ctx.Mdev, dev + 1)
    sdt = math.sqrt(const.v_mu)
    gg = {"g": g_grid(node)}
    a2s, _ = tune(scn, Policy("A2+screen", prior="rules", screen=True), W, N, ctx.Mdev, dev, const, gg)
    base = simulate(scn, a2s, W, N, ctx.M, seed, const)
    rows = []
    specs = [("calibrated", dict(prior="calibrated", noise_sd=x * sdt), f"calibrated, noise {x:g} sd_types")
             for x in (0.0, 0.25, 0.5, 1.0, 2.0, 4.0)]
    specs += [("noisy", dict(prior="noisy", noise_sd=x * sdt), f"raw (uncalibrated), noise {x:g} sd_types")
              for x in (0.5, 1.0, 2.0)]
    specs += [("noisy", dict(prior="noisy", mu_scale=m), f"mu_hat dispersion x{m:g}") for m in (0.0, 0.5, 1.5, 2.0)]
    specs += [("noisy", dict(prior="noisy", tau_scale=k), f"tau_hat x{k:g}") for k in (0.5, 2.0)]
    for kind, kw, label in specs:
        best, _ = tune(scn, Policy(label, screen=True, **kw), W, N, ctx.Mdev, dev, const, gg)
        r = simulate(scn, best, W, N, ctx.M, seed, const)
        d, se = paired(r, base)
        rows.append({"predictor": label, "g": best.g, "gain": r["gain"][0], "vs_A2screen": d, "se": se,
                     "vs_A2screen_dn": d / node.delta_n})
    return {"scenario": scn.name, "W": W, "N": N, "sd_type_means": sdt, "A2_screen_gain": base["gain"][0],
            "rows": rows}


def parts_list():
    L = [("calibration", part_calibration, ())]
    for s in TYPES:
        for noise in ("iid", "record"):
            for W in (20, 40):
                L.append((f"main_{s}_{noise}_W{W}", part_main, (s, noise, W)))
    for s in ("digits_on", "tabular_on", "digits_off", "tabular_off"):
        for noise in ("iid", "record"):
            for prop in ("stationary", "dimret", "memory"):
                if s.endswith("off") and prop != "stationary":
                    continue
                L.append((f"p7_{s}_{noise}_{prop}_W20", part_p7, (s, noise, prop, 20)))
        L.append((f"p7_{s}_iid_stationary_W40", part_p7, (s, "iid", "stationary", 40)))
    for s in ("digits_on", "tabular_on", "digits_off", "tabular_off"):
        L.append((f"p8_{s}_iid", part_p8, (s, "iid")))
    for s in ("digits_on", "tabular_on"):
        L.append((f"p8_{s}_record", part_p8, (s, "record")))
        L.append((f"p9_{s}", part_p9, (s,)))
        for W in (20, 40):
            L.append((f"p10_{s}_W{W}", part_p10, (s, W)))
    for scale, mixes in (("tabular", ("hom", "nearnull")), ("digits", ("hom",))):
        for mix in mixes:
            for split in ("fixed", "vary"):
                for rho in (0.0, 0.5, 0.8):
                    L.append((f"di_{scale}_{mix}_{split}_rho{rho}", part_di, (scale, split, rho, mix)))
    L.append(("di_digits_nearnull_fixed_rho0.5", part_di, ("digits", "fixed", 0.5, "nearnull")))
    L.append(("di_tabular_nearnull_fixed_rho0.5_feedback", part_di, ("tabular", "fixed", 0.5, "nearnull", 0.5)))
    L.append(("di_digits_hom_fixed_rho0.5_feedback", part_di, ("digits", "fixed", 0.5, "hom", 0.5)))
    for ns in (0.5, 2.0):
        L.append((f"di_tabular_hom_fixed_rho0.5_noise{ns}", part_di, ("tabular", "fixed", 0.5, "hom", 0.0, ns)))
    for base in ("digits_on", "tabular_on"):
        for W in (20, 40):
            L.append((f"headroom_{base}_W{W}", part_headroom, (base, W)))
        L.append((f"headroom_{base}_W20_homtau", part_headroom, (base, 20, True)))
    for s in ("digits_on", "tabular_on"):
        for noise in ("iid", "record"):
            L.append((f"predictor_{s}_{noise}_W20", part_predictor, (s, noise, 20)))
        L.append((f"predictor_{s}_iid_W40", part_predictor, (s, "iid", 40)))
    return L


# --------------------------------------------------------------------------------------------
# Tables
# --------------------------------------------------------------------------------------------

def f3(x):
    return f"{1000 * x:+.2f}"


def build_tables(parts: dict) -> str:
    L = ["# T5 tables (generated; ENGINEERING_ONLY, model-based, AI-assisted (Claude))", "",
         "Gains are final true gain J(c_T) − J(c_0) or contrasts, in units of 10⁻³ metric, ± 1 s.e. "
         "'δ_n' columns divide by δ_n = max(0.002, 0.25 × paired sd) (= 0.002 on both calibrated nodes). "
         "N = LLM-call cap.", ""]
    cal = parts["calibration"]["scenarios"]
    L += ["## T1. Calibration", "",
          "| Scenario | inert share | P(Δ>0 \\| informative) | mean μ (informative) | sd of type means | within-type τ (rms) | σ_d local / structural | δ_n |",
          "|---|---|---|---|---|---|---|---|"]
    for k, r in cal.items():
        L.append(f"| {k} | {r['inert_share']:.2f} | {r['p_improve_informative']:.2f} | {f3(r['mu_bar'])} | "
                 f"{1000 * r['sd_type_means']:.2f} | {1000 * r['tau_within_rms']:.2f} | "
                 f"{1000 * r['sigma_d_local']:.2f} / {1000 * r['sigma_d_structural']:.2f} | {1000 * r['delta_n']:.2f} |")
    L += ["", "## T2. Campaign gain by policy (stationary proposer)", "",
          "| Scenario | W | ρ | A1 | A1+screen | A2 | A2+screen | oracle threshold | oracle thr.+screen | oracle+screen − A2 (δ_n) | oracle+screen − A2+screen (δ_n) | runs / calls, oracle+screen |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, p in parts.items():
        if not k.startswith("main_"):
            continue
        R = p["rows"]
        cells = [f"{f3(R[q]['gain'])} ± {1000 * R[q]['se']:.2f}" for q in
                 ("rho", "A1", "A1+screen", "A2", "A2+screen", "oracle_threshold", "oracle")]
        d2 = R["oracle"]["vs_A2_dn"]
        d2s = (R["oracle"]["vs_A2"] - R["A2+screen"]["vs_A2"]) / (R["oracle"]["gain"] / R["oracle"]["gain_dn"])
        L.append(f"| {p['scenario']} | {p['W']} | " + " | ".join(cells) +
                 f" | {d2:+.2f} | {d2s:+.2f} | {R['oracle']['runs']:.1f} / {R['oracle']['calls']:.1f} |")
    L += ["", "## T3. Proposition 7: per-proposal threshold vs constant threshold (same executions)", "",
          "| Scenario | W | constant t~ | realised gain | Σ exact gap (predicted) | realised / predicted | Σ lower bound | Σ upper bound | realised (δ_n) |",
          "|---|---|---|---|---|---|---|---|---|"]
    for k, p in parts.items():
        if not k.startswith("p7_"):
            continue
        for lab in ("moment-matched constant t~", "dev-tuned constant t~"):
            r = p[lab]
            extra = f" (shift {p['A2_tuned_shift']:+.1f} σ_d)" if lab.startswith("dev") else ""
            L.append(f"| {p['scenario']} | {p['W']} | {lab}{extra} | {f3(r['realised'])} ± {1000 * r['realised_se']:.3f} | "
                     f"{f3(r['predicted_sum_gap'])} | {r['realised_over_predicted']:.2f} | {f3(r['lower_bound'])} | "
                     f"{f3(r['upper_bound'])} | {r['realised_dn']:+.2f} |")
    L += ["", "## T4. Proposition 8: screening", "", "Lagrangian check (no binding run budget, N = 40 proposals; J_g = Σ(Δk − g a)):", "",
          "| Scenario | g (× tuned) | layer | realised J_g gain | predicted Σ(g − V*)⁺ |", "|---|---|---|---|---|"]
    for k, p in parts.items():
        if not k.startswith("p8_"):
            continue
        for r in p["lagrangian"]:
            L.append(f"| {p['scenario']} | {1000 * r['g']:.3f} ({r['g_multiple_of_tuned']:g}×) | {r['layer']} | "
                     f"{f3(r['realised'])} ± {1000 * r['realised_se']:.3f} | {f3(r['predicted'])} ± {1000 * r['predicted_se']:.3f} |")
    L += ["", "Hard budget (W runs, N = 2W calls; oracle threshold with vs without learned screening, rules on in both):", "",
          "| Scenario | W | tuned g | realised gain of screening | Σ(g − V*)⁺ over the screening run | learned skips | calls used (screen / no screen) |",
          "|---|---|---|---|---|---|---|"]
    for k, p in parts.items():
        if not k.startswith("p8_"):
            continue
        for r in p["hard_budget"]:
            L.append(f"| {p['scenario']} | {r['W']} | {1000 * r['g_tuned']:.3f} | {f3(r['realised_gain'])} ± {1000 * r['realised_se']:.3f} | "
                     f"{f3(r['sum_pos_part_over_screen_run'])} | {r['skips_learned']:.1f} | {r['calls_screen']:.1f} / {r['calls_noscreen']:.1f} |")
    L += ["", "## T5. Proposition 9: record bias after keeps (W = 40, N = 80)", "",
          "Record model: observed new record error e′ vs ϱe + σ_c λ(a); iid model: Δ̂ − Δ at a keep vs σ_d λ((t − Δ)/σ_d).", "",
          "| Scenario | policy | keeps | mean observed | mean formula | residual ± s.e. | null keeps: mean rise / formula | record bias at end | debiased B~ bias at end | gain | bold share |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, p in parts.items():
        if not k.startswith("p9_"):
            continue
        for r in p["rows"]:
            L.append(f"| {r['scenario']} | {r['policy']} | {r.get('keeps', 0)} | {f3(r.get('mean_observed', float('nan')))} | "
                     f"{f3(r.get('mean_formula', float('nan')))} | {1000 * r.get('mean_residual', float('nan')):+.3f} ± {1000 * r.get('se_residual', float('nan')):.3f} | "
                     f"{f3(r.get('null_mean_rise', float('nan')))} / {f3(r.get('null_mean_rise_formula', float('nan')))} | "
                     f"{f3(r['record_bias_end'])} | {f3(r['debiased_bias_end'])} | {f3(r['gain'])} | {r['bold_share']:.3f} |")
    L += ["", "Raw vs debiased display for the memory-reading proposer (W = 40):", "",
          "| Scenario | noise | bold edits | policy | gain raw / debiased | debiased − raw gain | bold share raw / debiased |", "|---|---|---|---|---|---|---|"]
    for k, p in parts.items():
        if not k.startswith("p9_"):
            continue
        for r in p["display"]:
            L.append(f"| {k[3:]} | {r['noise']} | {r['bold']} | {r['policy']} | {f3(r['gain_raw'])} / {f3(r['gain_debiased'])} | {f3(r['debiased_minus_raw'])} ± {1000 * r['se']:.3f} | "
                     f"{r['bold_raw']:.3f} / {r['bold_debiased']:.3f} |")
    L += ["", "## T6. Proposition 10: myopic vs lookahead threshold family (rules + oracle prior, no screening, N = W)", "",
          "Lookahead family: t = t*_n + σ_d (θ0 + θ1 · remaining-budget fraction), (θ0, θ1) tuned on development campaigns.", "",
          "| Node | W | case | best (θ0, θ1) | myopic gain | lookahead gain | lookahead − myopic (test, paired) | (δ_n) |",
          "|---|---|---|---|---|---|---|---|"]
    for k, p in parts.items():
        if not k.startswith("p10_"):
            continue
        for r in p["rows"]:
            L.append(f"| {r['scenario'].split('/')[0]} | {p['W']} | {r['case']} | ({r['theta0']:+.1f}, {r['theta1']:+.1f}) | "
                     f"{f3(r['myopic'])} | {f3(r['lookahead'])} | {f3(r['diff'])} ± {1000 * r['diff_se']:.3f} | {r['diff_dn']:+.2f} |")
    L += ["", "## T7. DI-test artefact and value-proxy selection bias (E1b-style forks, W = 20, points 4/8/12, verify r = 2, rule ρ, DI-satisfying stationary proposer unless 'feedback' ≠ 0)", "",
          "Outcomes of the next 1 / 3 trials: Δ̂ (relative to the branch's recorded incumbent), abs (recorded metric of the candidate), tv (true value J of the candidate), ti (true increment over the branch's own incumbent, i.e. an audited increment). For the next trial, Δ̂ shift = abs shift − record shift exactly.", "",
          "**T7a. Signed shifts, verify − continue, at changed points (repetitions averaged)**", "",
          "| Study | split | ϱ | feedback | P(prom) / P(dem) | record shift | Δ̂ 1 / 3 | abs 1 / 3 | tv 1 / 3 | ti 1 / 3 |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for k, p in parts.items():
        if not k.startswith("di_"):
            continue
        s = p["population"]
        lab = p["study"] + (f" ×{p['noise_scale']:g} noise" if p["noise_scale"] != 1 else "")
        L.append(f"| {lab} | {p['split']} | {p['rho']} | {p['feedback_shift_sd']:+.1f} σ_d | {s['rate_promotion']:.3f} / {s['rate_demotion']:.3f} | "
                 f"{f3(s['signed_rec0_changed'])} | " + " | ".join(f"{f3(s[f'signed_{o}1_changed'])} / {f3(s[f'signed_{o}3_changed'])}" for o in ("dh", "ab", "tv", "ti")) + " |")
    L += ["", "**T7b. Distance criterion: excess of the changed-point cross-action distance over the paired same-action null (population), abs next-1 distances (observed tabular memory-on: D_changed 2.31, D_null 1.08, D_unchanged 0.55; digits memory-off 6.04 / 4.64 / 1.97), and the rate at which small studies (18 tabular / 6 digits instances × 3 points) meet the simplified combined criterion**", "",
          "| Study | split | ϱ | feedback | abs next-1 D_ch / D_null / D_unch | excess Δ̂ 1 / 3 | abs 1 / 3 | tv 1 / 3 | ti 1 / 3 | flag rate Δ̂ 1/3 · abs 1/3 · tv 1/3 · ti 1/3 |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for k, p in parts.items():
        if not k.startswith("di_"):
            continue
        s = p["population"]
        fr = p["small_studies"]["flag_rate"]
        lab = p["study"] + (f" ×{p['noise_scale']:g} noise" if p["noise_scale"] != 1 else "")
        L.append(f"| {lab} | {p['split']} | {p['rho']} | {p['feedback_shift_sd']:+.1f} σ_d | "
                 f"{1000 * s['D_changed_ab1']:.2f} / {1000 * s['D_null_changed_ab1']:.2f} / {1000 * s['D_unchanged_ab1']:.2f} | "
                 + " | ".join(f"{f3(s[f'excess_null_{o}1'])} / {f3(s[f'excess_null_{o}3'])}" for o in ("dh", "ab", "tv", "ti")) + " | "
                 + " · ".join(f"{fr[o + '1']:.2f} {fr[o + '3']:.2f}" for o in ("dh", "ab", "tv", "ti")) + " |")
    L += ["", "Value residual = audited Y difference − immediate proxy (+D̄ for a promotion, −D̄ for a demotion) − unchanged-point budget correction, averaged over changed points. Observed (19 Oct, memory-on tabular, fixed split): P(prom) 0.167, P(dem) 0.074, E[D̄ | prom] +0.44, E[−D̄ | dem] +1.70, proxy +0.83, residual −1.22 [−2.22, −0.26] (10⁻³).", "",
          "| Study | split | ϱ | feedback | E[D̄ \\| prom] | E[Δ \\| prom] | E[−D̄ \\| dem] | immediate proxy | true immediate | proxy bias | continuation part | **expected residual** | proxy bias / proxy | small studies: mean, sd, [5 %, 95 %], P(≤ −1.22) |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, p in parts.items():
        if not k.startswith("di_"):
            continue
        s = p["population"]
        q = p["small_studies"]
        lab = p["study"] + (f" ×{p['noise_scale']:g} noise" if p["noise_scale"] != 1 else "")
        qq = q["residual_q05_q50_q95"]
        L.append(f"| {lab} | {p['split']} | {p['rho']} | {p['feedback_shift_sd']:+.1f} | {f3(s['dbar_given_promotion'])} | "
                 f"{f3(s['delta_given_promotion'])} | {f3(s['neg_dbar_given_demotion'])} | {f3(s['immediate_proxy'])} | "
                 f"{f3(s['immediate_true'])} | {f3(s['proxy_bias'])} | {f3(s['residual_oracle_immediate'])} | **{f3(s['residual'])}** | "
                 f"{s['proxy_bias'] / s['immediate_proxy']:.2f} | "
                 f"{f3(q['residual_mean'])}, {1000 * q['residual_sd']:.2f}, [{f3(qq[0])}, {f3(qq[2])}], {q['frac_residual_le_obs_tabular']:.2f} |")
    L += ["", "## T8. Headroom map: oracle-prior control (threshold + screening) − A2+screen, in δ_n per campaign (iid noise, stationary proposer, N = 2W)", ""]
    for k, p in parts.items():
        if not k.startswith("headroom_"):
            continue
        cells = p["cells"]
        disp = sorted({c["dispersion"] for c in cells})
        inert = sorted({c["inert_share"] for c in cells})
        sdmap = {c["dispersion"]: c["sd_type_means_over_sigma_d"] for c in cells}
        L += [f"**{p['base']}, W = {p['W']}{', one within-type τ, all edits local' if p.get('homog_tau') else ''}** (columns: dispersion multiplier, with sd of type means / σ_d; ≥ 1.00 means the oracle clears δ_n)", "",
              "| inert share | " + " | ".join(f"×{d:g} ({sdmap[d]:.2f})" for d in disp) + " |",
              "|---|" + "---|" * len(disp)]
        for s in inert:
            row = []
            for d in disp:
                c = [x for x in cells if x["inert_share"] == s and x["dispersion"] == d][0]
                row.append(f"{c['gain_dn']:+.2f}")
            L.append(f"| {s:.2f} | " + " | ".join(row) + " |")
        L.append("")
    L += ["## T9. Gain vs predictor quality (screening g tuned per predictor; contrast vs A2+screen, paired)", "",
          "| Scenario | W | predictor | gain | vs A2+screen | (δ_n) |", "|---|---|---|---|---|---|"]
    for k, p in parts.items():
        if not k.startswith("predictor_"):
            continue
        for r in p["rows"]:
            L.append(f"| {p['scenario']} | {p['W']} | {r['predictor']} | {f3(r['gain'])} | {f3(r['vs_A2screen'])} ± {1000 * r['se']:.3f} | {r['vs_A2screen_dn']:+.2f} |")
    return "\n".join(L) + "\n"


def _jsonable(o):
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return o


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-seconds", type=float, default=float("inf"))
    ap.add_argument("--quick", action="store_true", help="small campaign counts (smoke test)")
    ap.add_argument("--only", default=None, help="run only parts whose name starts with this prefix")
    args = ap.parse_args(argv)
    out = Path(args.out)
    (out / "parts").mkdir(parents=True, exist_ok=True)
    ctx = Ctx(args.quick)
    t0 = time.time()
    todo = parts_list()
    done_all = True
    for name, fn, a in todo:
        path = out / "parts" / f"{name}.json"
        if path.exists():
            continue
        if args.only and not name.startswith(args.only):
            done_all = False
            continue
        if time.time() - t0 > args.max_seconds:
            done_all = False
            break
        ts = time.time()
        res = fn(ctx, name, *a)
        res["_seconds"] = time.time() - ts
        res["_seeds"] = list(seeds(name))
        path.write_text(json.dumps(_jsonable(res), indent=1) + "\n")
        print(f"{name}: {res['_seconds']:.1f}s", flush=True)
    missing = [n for n, _, _ in todo if not (out / "parts" / f"{n}.json").exists()]
    if missing:
        print(f"PENDING {len(missing)} parts (rerun the same command to resume)")
        return 0
    parts = {n: json.loads((out / "parts" / f"{n}.json").read_text()) for n, _, _ in todo}
    (out / "tables.md").write_text(build_tables(parts))
    try:
        rev = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False).stdout.strip()
    except OSError:
        rev = ""
    src = Path(__file__).resolve().parent
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (src / "simulate_t4.py", src / "t5_report.py")}
    manifest = {"label": "ENGINEERING_ONLY", "note": "model-based numbers, not measurements; AI-assisted (Claude)",
                "utc_written": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"), "base_seed": BASE_SEED,
                "quick": args.quick, "M_test": ctx.M, "M_big": ctx.Mbig, "M_dev": ctx.Mdev, "n_branch": ctx.n_branch,
                "parts": {n: {"seconds": parts[n]["_seconds"], "seeds": parts[n]["_seeds"]} for n in parts},
                "total_part_seconds": sum(parts[n]["_seconds"] for n in parts),
                "git_head_at_write": rev, "source_sha256": hashes,
                "host": {"platform": platform.platform(), "python": platform.python_version(),
                         "numpy": np.__version__}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("ALL PARTS DONE; tables.md and manifest.json written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
