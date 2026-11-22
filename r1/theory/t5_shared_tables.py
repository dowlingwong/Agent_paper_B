#!/usr/bin/env python3
"""Tables for the T5 shared-noise re-run (ENGINEERING_ONLY; AI-assisted (Claude, subagent)). Model-based numbers.

    python -m r1.theory.t5_shared_tables --out results/r1/engineering/T5_shared_20261122

Reads <out>/parts/*.json written by r1.theory.t5_shared_report, writes <out>/tables.md and
<out>/reproduction.json (record / iid parts compared with the published T5 parts, same seeds).
Units: 10^-3 metric unless a column says δ_n (δ_n = 0.002 on digits_mlp).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from r1.theory import t5_shared_report as S

TOK = S.TOKENS
LAB = {t: S.token_label(t) for t in TOK}


def f3(x, nd=2):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    return f"{1000 * x:+.{nd}f}"


def load(out: Path) -> dict:
    return {p.stem: json.loads(p.read_text()) for p in sorted((out / "parts").glob("*.json"))}


def part_for(P, base, tok):
    if tok == "iid":
        return P.get(base.replace("_record", "_iid"))
    return P.get(f"{base}__{S._tokname(tok)}")


def header(cols):
    return ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]


# --------------------------------------------------------------------------------------------

def t_calibration(P):
    c = P["calibration"]
    L = ["## S0. Calibration (digits_mlp: σ = 0.0125, ϱ local / structural = 0.82 / 0.55, split share 0.59)", "",
         f"Target sibling partial correlation (local siblings given their parent) {c['P_target']}, interval "
         f"{c['P_interval'][0]}–{c['P_interval'][1]}; the largest value reachable at ϱ_local = 0.82 is "
         f"{c['P_max_local']:.4f} (s = ϱ_local).", ""]
    L += header(["s", "r_w local / structural", "marginal ϱ local / structural", "paired sd structural (10⁻³)",
                 "sibling partial: local–local / local–structural / structural–structural", "T5 ϱ kept for both kinds?"])
    for r in c["rows"]:
        L.append(f"| {r['s']:.4f} | {r['rho_w_local']:.4f} / {r['rho_w_struct']:.4f} | "
                 f"{r['local_local']['marginal_parent_child_a']:.3f} / {r['rho_eff_struct']:.3f} | {1000 * r['paired_sd_struct']:.2f} | "
                 f"{r['local_local']['sibling_partial']:.3f} / {r['local_struct']['sibling_partial']:.3f} / "
                 f"{r['struct_struct']['sibling_partial']:.3f} | {'yes' if r['local_struct']['feasible'] else 'no (structural ϱ → s)'} |")
    L += ["", "E1 pattern (corr(edit, c0) = " + ", ".join(f"{x:.2f}" for x in c["E1_corr_edit_c0"]) +
          " on digits_mlp): mean model sibling partial over the 10 pairs at s = " +
          ", ".join(f"{r['s']:.2f}: {r['mean_sibling_partial']:.3f}" for r in c["E1_pattern"]) +
          f" (s = {min(c['E1_corr_edit_c0']):.2f} is the largest s compatible with all five)."]
    L += ["", "Simulator check (`simulate(..., trace=)`, 200,000 campaigns, local edits only, no keeps; siblings = "
          "candidates of calls 1 and 2):", ""]
    L += header(["s", "corr(parent, child): sim / theory", "sibling partial: sim / theory"])
    for r in c["sim_check"]:
        L.append(f"| {r['s']:.4f} | {r['sim_corr_parent_child']:.4f} / {r['theory']['marginal_parent_child_a']:.4f} | "
                 f"{r['sim_sibling_partial']:.4f} / {r['theory']['sibling_partial']:.4f} |")
    return L


def t_main(P):
    L = ["", "## S1. Campaign gain and policy contrasts (T5 T2; stationary proposer, N = 2W)", "",
         "Contrast rows are paired (same seed) for record-like columns; iid uses T5's iid seeds. "
         "'oracle+scr − A2+scr' is in δ_n.", ""]
    rows = [("ρ (default)", lambda R: R["rho"]["gain"]), ("A1", lambda R: R["A1"]["gain"]),
            ("A2", lambda R: R["A2"]["gain"]), ("A2+screen", lambda R: R["A2+screen"]["gain"]),
            ("oracle threshold", lambda R: R["oracle_threshold"]["gain"]),
            ("oracle thr.+screen", lambda R: R["oracle"]["gain"]),
            ("A1 − ρ", lambda R: R["A1"]["vs_A2"] - R["rho"]["vs_A2"]),
            ("A2 − ρ", lambda R: -R["rho"]["vs_A2"]),
            ("oracle thr. − A2", lambda R: R["oracle_threshold"]["vs_A2"]),
            ("false-keep rate ρ / A2", None)]
    for scn in ("digits_on", "digits_off"):
        for W in (20, 40):
            base = f"main_{scn}_record_W{W}"
            L += ["", f"**{scn}, W = {W}**", ""] + header(["quantity"] + [LAB[t] for t in TOK])
            parts = [part_for(P, base, t) for t in TOK]
            for lab, fn in rows:
                if fn is None:
                    L.append(f"| {lab} | " + " | ".join(
                        f"{p['rows']['rho']['false_keep_rate']:.3f} / {p['rows']['A2']['false_keep_rate']:.3f}" for p in parts) + " |")
                    continue
                L.append(f"| {lab} | " + " | ".join(f3(fn(p["rows"])) for p in parts) + " |")
            L.append("| A2 − ρ s.e. | " + " | ".join(f"{1000 * p['rows']['rho']['vs_A2_se']:.2f}" for p in parts) + " |")
            dn = []
            for p in parts:
                R = p["rows"]
                dn.append(f"{(R['oracle']['vs_A2'] - R['A2+screen']['vs_A2']) / 0.002:+.2f}")
            L.append("| oracle+scr − A2+scr (δ_n) | " + " | ".join(dn) + " |")
    return L


def t_a1rho(P):
    L = ["", "**S1b. Paired contrasts with the default rule (recomputed with the S1 seeds and constants; ± paired s.e.)**", ""]
    L += header(["cell", "contrast"] + [LAB[t] for t in TOK])
    for scn in ("digits_on", "digits_off"):
        for W in (20, 40):
            p = P[f"a1rho_{scn}_W{W}__all"]
            rr = [[x for x in p["rows"] if x["noise"] == t][0] for t in TOK]
            for key, lab in (("A1_minus_rho", "A1 − ρ"), ("A2_minus_rho", "A2 − ρ")):
                L.append(f"| {scn}, W = {W} | {lab} | " + " | ".join(
                    f"{f3(r[key])} ± {1000 * r[key + '_se']:.2f}" for r in rr) + " |")
    return L


def t_p7(P):
    L = ["", "## S2. Proposition 7: per-proposal vs constant threshold (T5 T3; W = 20)", ""]
    for scn, prop in (("digits_on", "stationary"), ("digits_on", "dimret"), ("digits_on", "memory"),
                      ("digits_off", "stationary")):
        base = f"p7_{scn}_record_{prop}_W20"
        parts = [part_for(P, base, t) for t in TOK]
        L += ["", f"**{scn}, {prop}**", ""] + header(["quantity"] + [LAB[t] for t in TOK])
        mm = [p["moment-matched constant t~"] for p in parts]
        dv = [p["dev-tuned constant t~"] for p in parts]
        L.append("| moment-matched: realised | " + " | ".join(f"{f3(r['realised'])} ± {1000 * r['realised_se']:.3f}" for r in mm) + " |")
        L.append("| moment-matched: Σ exact gap | " + " | ".join(f3(r['predicted_sum_gap']) for r in mm) + " |")
        L.append("| moment-matched: realised / predicted | " + " | ".join(f"{r['realised_over_predicted']:.2f}" for r in mm) + " |")
        L.append("| dev-tuned shift (σ_d) | " + " | ".join(f"{p['A2_tuned_shift']:+.1f}" for p in parts) + " |")
        L.append("| dev-tuned: realised | " + " | ".join(f"{f3(r['realised'])} ± {1000 * r['realised_se']:.3f}" for r in dv) + " |")
        L.append("| dev-tuned: realised / predicted | " + " | ".join(f"{r['realised_over_predicted']:.2f}" for r in dv) + " |")
    return L


def t_p8(P):
    base = "p8_digits_on_record"
    parts = [part_for(P, base, t) for t in TOK]
    L = ["", "## S3. Proposition 8: screening (T5 T4; digits_on)", ""] + header(["quantity"] + [LAB[t] for t in TOK])
    for gm in (0.5, 1.0, 2.0):
        for layer in ("total (vs always execute)", "learned layer (vs rules)"):
            cells = []
            for p in parts:
                r = [x for x in p["lagrangian"] if x["g_multiple_of_tuned"] == gm and x["layer"] == layer][0]
                cells.append(f"{f3(r['realised'])} / {f3(r['predicted'])}")
            L.append(f"| Lagrangian g×{gm:g}, {layer}: realised / Σ(g − V*)⁺ | " + " | ".join(cells) + " |")
    for W in (20, 40):
        cells = []
        for p in parts:
            r = [x for x in p["hard_budget"] if x["W"] == W][0]
            cells.append(f"{f3(r['realised_gain'])} ± {1000 * r['realised_se']:.3f} (g {1000 * r['g_tuned']:.3f})")
        L.append(f"| hard budget W = {W}: gain of learned screening | " + " | ".join(cells) + " |")
    return L


def t_p9(P):
    p = P["p9_digits_on__all"]
    rows = p["rows"]
    L = ["", "## S4. Proposition 9: record bias after keeps (T5 T5; digits_on, W = 40, N = 80)", "",
         "Residual = observed new record error e′ − T4 formula ϱe + σ_c λ(a) with the marginal ϱ (record-like "
         "columns); iid: Δ̂ − Δ at a keep vs σ_d λ((t − Δ)/σ_d). 'first' = first keep of a campaign (record not "
         "yet selected), 'later' = later keeps.", ""]
    props = ("stationary", "dimret", "memory", "memory_debiased")
    for title, fn in (
            ("residual, all keeps (± s.e.)", lambda r: f"{f3(r.get('mean_residual'), 3)} ± {1000 * r.get('se_residual', float('nan')):.3f}"),
            ("residual, first keep", lambda r: f3(r["p9_by_keep"].get("first", {}).get("mean_residual"), 3) if r["p9_by_keep"] else "–"),
            ("residual, later keeps", lambda r: f3(r["p9_by_keep"].get("later", {}).get("mean_residual"), 3) if r["p9_by_keep"] else "–"),
            ("mean observed e′ / formula", lambda r: f"{f3(r.get('mean_observed'))} / {f3(r.get('mean_formula'))}"),
            ("null keeps: mean rise / formula", lambda r: f"{f3(r.get('null_mean_rise'))} / {f3(r.get('null_mean_rise_formula'))}"),
            ("record bias at end", lambda r: f3(r["record_bias_end"])),
            ("gain", lambda r: f3(r["gain"])),
            ("false-keep rate", lambda r: f"{r['false_keep_rate']:.3f}")):
        L += ["", f"**{title}**", ""] + header(["proposer / policy"] + [LAB[t] for t in TOK])
        for prop in props:
            for pol in ("rho", "oracle_threshold"):
                cells = []
                for t in TOK:
                    r = [x for x in rows if x["noise"] == t and x["scenario"].split("/")[2].split("(")[0] == prop and x["policy"] == pol][0]
                    cells.append(fn(r))
                L.append(f"| {prop} / {pol} | " + " | ".join(cells) + " |")
    # kernel-free inequality, all p9 rows + ecorr runs
    L += ["", "**Kernel-free inequality (P09 §4) on every keep: e′ > e − Δ + t (all rules); e′ > e − Δ (keeps with t ≥ 0, "
          "includes every keep of rule ρ); e′ > e at a null keep with t ≥ 0. Counts over the 8 rows above.**", ""]
    L += header(["noise", "keeps", "violations e′ > e − Δ + t", "min margin (10⁻³)", "keeps with t ≥ 0 / violations of e′ > e − Δ",
                 "keeps with t < 0 / of which e′ ≤ e − Δ", "null keeps (t ≥ 0) / violations of e′ > e"])
    for t in TOK:
        rr = [x for x in rows if x["noise"] == t]
        k = {key: sum(x["kfree"][key] for x in rr) for key in ("keeps", "viol_general", "keeps_t_nonneg", "viol_p09",
                                                                 "keeps_t_neg", "viol_p09_t_neg", "null_keeps_t_nonneg",
                                                                 "null_viol_rise")}
        mm = min(x["kfree"]["min_margin_general"] for x in rr if x["kfree"]["min_margin_general"] is not None)
        L.append(f"| {LAB[t]} | {k['keeps']} | {k['viol_general']} | {1000 * mm:.2e} | {k['keeps_t_nonneg']} / {k['viol_p09']} | "
                 f"{k['keeps_t_neg']} / {k['viol_p09_t_neg']} | {k['null_keeps_t_nonneg']} / {k['null_viol_rise']} |")
    L += ["", "**Route D: debiased − raw display, memory-reading proposer (W = 40)**", ""]
    L += header(["bold edits / policy"] + [LAB[t] for t in TOK])
    for bold in ("as calibrated", "harmful bold"):
        for pol in ("rho", "oracle_threshold"):
            cells = []
            for t in TOK:
                r = [x for x in p["display"] if x["noise"] == t and x["bold"] == bold and x["policy"] == pol][0]
                cells.append(f"{f3(r['debiased_minus_raw'])} ± {1000 * r['se']:.3f}")
            L.append(f"| {bold} / {pol} | " + " | ".join(cells) + " |")
    return L


def t_p10(P):
    L = ["", "## S5. Proposition 10: lookahead − myopic (T5 T6; digits_on, oracle prior, rules, N = W), δ_n per campaign "
         "(tuned (θ0, θ1) in brackets)", ""]
    props = [("stationary", "channel only"), ("memory", "+ memory (raw B)"), ("memory_debiased", "+ memory (debiased B~)")]
    for W in (20, 40):
        p = P[f"p10_digits_on_W{W}__all"]
        L += ["", f"**W = {W}**", ""] + header(["case"] + [LAB[t] for t in TOK[1:]])
        for prop, lab in props:
            cells = []
            for t in TOK[1:]:
                r = [x for x in p["rows"] if x["noise"] == t and x["prop"] == prop][0]
                cells.append(f"{r['diff_dn']:+.2f} ({r['theta0']:+.1f}, {r['theta1']:+.1f})")
            L.append(f"| {lab} | " + " | ".join(cells) + " |")
        iid = [x for x in p["rows"] if x["noise"] == "iid"]
        L.append("")
        L.append("iid cases (unchanged from T5): " + "; ".join(f"{x['case']}: {x['diff_dn']:+.2f}" for x in iid))
    return L


def t_di(P):
    L = ["", "## S6. DI-test artefact and value-proxy selection bias (T5 T7; digits homogeneous study, W = 20)", "",
         "Shared rows are the kernel branch study at the per-configuration kernel coefficient r_w (u cancels in every "
         "contrast). Signed shifts verify − continue at changed points; flag rate = small studies of 6 instances.", ""]
    L += header(["cell", "s / r_w loc, str / p_loc", "P(prom) / P(dem)", "record shift", "Δ̂ 1 / 3", "abs 1 / 3", "tv 1 / 3",
                 "ti 1 / 3", "flag Δ̂1 · abs1 · tv1 · ti1", "proxy bias", "expected residual", "bias / proxy"])
    for split in ("fixed", "vary"):
        for rho in (0.8, 0.5):
            nm = f"di_digits_hom_{split}_rho{rho}"
            for suf in ("record", "shared_t5", "shared_lo", "shared_mid", "shared_hi", "shared_max"):
                p = P.get(f"{nm}__{suf}")
                if p is None:
                    continue
                L.append(_di_row(p, f"{split}, ϱ={rho}, {suf}"))
    for suf in ("record", "shared_max"):
        p = P.get(f"di_digits_hom_fixed_rho0.5_feedback__{suf}")
        if p is not None:
            L.append(_di_row(p, f"fixed, ϱ=0.5, feedback +0.5 σ_d, {suf}"))
    return L


def _di_row(p, lab):
    s = p["population"]
    fr = p["small_studies"]["flag_rate"]
    sh = "–" if p["shared_share"] is None else f"{p['shared_share']:.3f}"
    pp = "0" if p["sibling_partial_local"] is None else f"{p['sibling_partial_local']:.2f}"
    return (f"| {lab} | {sh} / {p['rho_w_local']:.3f}, {p['rho_w_struct']:.3f} / {pp} | "
            f"{s['rate_promotion']:.3f} / {s['rate_demotion']:.3f} | {f3(s['signed_rec0_changed'])} | "
            + " | ".join(f"{f3(s[f'signed_{o}1_changed'])} / {f3(s[f'signed_{o}3_changed'])}" for o in ("dh", "ab", "tv", "ti"))
            + " | " + " · ".join(f"{fr[o + '1']:.2f}" for o in ("dh", "ab", "tv", "ti"))
            + f" | {f3(s['proxy_bias'])} | {f3(s['residual'])} | {s['proxy_bias'] / s['immediate_proxy']:.2f} |")


def t_pred(P):
    base = "predictor_digits_on_record_W20"
    parts = [part_for(P, base, t) for t in TOK]
    L = ["", "## S7. Predictor quality (T5 T9; digits_on, W = 20): gain vs A2+screen, δ_n", ""]
    L += header(["predictor"] + [LAB[t] for t in TOK])
    for i, r0 in enumerate(parts[1]["rows"]):
        L.append(f"| {r0['predictor']} | " + " | ".join(f"{p['rows'][i]['vs_A2screen_dn']:+.2f}" for p in parts) + " |")
    return L


def t_ecorr(P):
    L = ["", "## S8. Threshold correction for a selected incumbent (new; N = 2W, no screening)", "",
         "none = deployed t* = −μσ_d²/τ²; table = feasible t** with E/Var of the inherited error given the number of keeps "
         "so far (fitted on development runs); known = oracle knowing the incumbent's inherited error (upper bound on any "
         "history-based correction). Gains in 10⁻³ (contrasts paired, ± s.e.) and δ_n.", ""]
    for scn in ("digits_on", "digits_off"):
        for W in (20, 40):
            p = P[f"ecorr_{scn}_W{W}__all"]
            for base in ("oracle_threshold", "A2"):
                L += ["", f"**{scn}, W = {W}, base {base}**", ""] + header(["quantity"] + [LAB[t] for t in TOK])
                rr = [[x for x in p["rows"] if x["noise"] == t and x["base"] == base][0] for t in TOK]
                L.append("| gain, t* (none) | " + " | ".join(f3(r["none"]["gain"]) for r in rr) + " |")
                for lab in ("table", "known"):
                    L.append(f"| {lab} − none | " + " | ".join(
                        "–" if lab not in r else f"{f3(r[f'{lab}_minus_none'])} ± {1000 * r[f'{lab}_minus_none_se']:.3f}" for r in rr) + " |")
                    L.append(f"| {lab} − none (δ_n) | " + " | ".join(
                        "–" if lab not in r else f"{r[f'{lab}_minus_none_dn']:+.2f}" for r in rr) + " |")
                L.append("| mean threshold, executed (none / known) | " + " | ".join(
                    f"{f3(r['none']['mean_threshold_executed'])} / {f3(r['known']['mean_threshold_executed']) if 'known' in r else '–'}" for r in rr) + " |")
                L.append("| keeps (none / known) | " + " | ".join(
                    f"{r['none']['keeps']:.2f} / {r['known']['keeps']:.2f}" if "known" in r else f"{r['none']['keeps']:.2f} / –" for r in rr) + " |")
                L.append("| false-keep rate (none / known) | " + " | ".join(
                    f"{r['none']['false_keep_rate']:.3f} / {r['known']['false_keep_rate']:.3f}" if "known" in r else f"{r['none']['false_keep_rate']:.3f} / –" for r in rr) + " |")
    return L


# --------------------------------------------------------------------------------------------

def reproduction(P) -> dict:
    """Compare re-run record / iid parts with the published T5 parts (same names, same seeds)."""
    old_dir = S.OLD_T5 / "parts"
    out = {}

    def cmp(a, b, path, diffs):
        if isinstance(a, dict):
            for k in b:
                if k.startswith("_"):
                    continue
                if k not in a:
                    diffs.append((path + "/" + k, "missing"))
                    continue
                cmp(a[k], b[k], path + "/" + k, diffs)
        elif isinstance(a, list) and isinstance(b, list):
            for i, (x, y) in enumerate(zip(a, b)):
                cmp(x, y, f"{path}[{i}]", diffs)
        elif a != b:
            if isinstance(a, float) and isinstance(b, float):
                diffs.append((path, abs(a - b) / max(abs(b), 1e-300)))
            else:
                diffs.append((path, f"{a} vs {b}"))

    for name, p in P.items():
        if name.startswith("di_") and name.endswith("__record"):
            old_name = name[:-len("__record")]
            a, b = p["population"], None
            f = old_dir / f"{old_name}.json"
            if f.exists():
                b = json.loads(f.read_text())["population"]
        elif name.endswith("__record") or (("_iid" in name) and "__" not in name):
            old_name = name.split("__")[0]
            f = old_dir / f"{old_name}.json"
            if not f.exists():
                continue
            a, b = p, json.loads(f.read_text())
        else:
            continue
        if b is None:
            continue
        diffs = []
        cmp(a, b, "", diffs)
        out[name] = {"compared_with": old_name, "n_diffs": len(diffs),
                     "max_rel_diff": max([d[1] for d in diffs if isinstance(d[1], float)], default=0.0),
                     "non_float_diffs": [d for d in diffs if not isinstance(d[1], float)][:5],
                     "diff_paths": sorted({d[0].split("[")[0] if "[" in d[0] else d[0] for d in diffs})[:8]}
    # p9: compare the record and iid rows with T5's p9 rows
    p9 = P.get("p9_digits_on__all")
    f = old_dir / "p9_digits_on.json"
    if p9 and f.exists():
        old = json.loads(f.read_text())
        diffs = []
        for r in old["rows"]:
            m = [x for x in p9["rows"] if x["scenario"] == r["scenario"] and x["policy"] == r["policy"]][0]
            cmp(m, r, f"p9/{r['scenario']}/{r['policy']}", diffs)
        for r in old["display"]:
            m = [x for x in p9["display"] if x["noise"] == r["noise"] and x["bold"] == r["bold"] and x["policy"] == r["policy"]][0]
            cmp(m, r, f"p9display/{r['noise']}/{r['bold']}/{r['policy']}", diffs)
        out["p9_digits_on__all"] = {"n_diffs": len(diffs), "max_rel_diff": max([d[1] for d in diffs if isinstance(d[1], float)], default=0.0),
                                    "non_float_diffs": [d for d in diffs if not isinstance(d[1], float)][:5],
                                    "diff_paths": sorted({d[0].rsplit("/", 1)[-1] for d in diffs})}
    for W in (20, 40):
        p = P.get(f"p10_digits_on_W{W}__all")
        f = old_dir / f"p10_digits_on_W{W}.json"
        if p and f.exists():
            old = json.loads(f.read_text())
            diffs = []
            for r in old["rows"]:
                m = [x for x in p["rows"] if x["scenario"] == r["scenario"] and x["case"] == r["case"]][0]
                cmp(m, r, f"p10/{r['case']}", diffs)
            out[f"p10_digits_on_W{W}__all"] = {"n_diffs": len(diffs), "max_rel_diff": max([d[1] for d in diffs if isinstance(d[1], float)], default=0.0),
                                               "non_float_diffs": [d for d in diffs if not isinstance(d[1], float)][:5]}
    return out


def build(P) -> str:
    L = ["# T5 shared-noise re-run: tables (generated; ENGINEERING_ONLY, model-based, AI-assisted (Claude, subagent))", "",
         "Columns: " + "; ".join(f"`{t}` = {LAB[t]}" for t in TOK) + ". p = partial correlation of two local siblings "
         "given their parent. Units 10⁻³ metric unless noted.", ""]
    for fn in (t_calibration, t_main, t_a1rho, t_p7, t_p8, t_p9, t_p10, t_di, t_pred, t_ecorr):
        L += fn(P)
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    out = Path(args.out)
    P = load(out)
    (out / "tables.md").write_text(build(P))
    (out / "reproduction.json").write_text(json.dumps(reproduction(P), indent=1) + "\n")
    print("tables.md and reproduction.json written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
