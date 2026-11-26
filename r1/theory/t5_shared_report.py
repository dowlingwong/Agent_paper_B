#!/usr/bin/env python3
"""T5 re-run with the shared-component noise model on digits_mlp (ENGINEERING_ONLY; AI-assisted (Claude, subagent)).

Model-based numbers, not measurements. PLAN row R1-THEORY-RHO (4). Usage:

    python -m r1.theory.t5_shared_report --out results/r1/engineering/T5_shared_<stamp> [--quick]

What it runs. Every T5 part that uses the ``record`` noise model on a digits scenario (main gains, Proposition
7, 8, 9, 10, predictor quality, and the E1b-style DI branch study at the digits scale) is re-run with the
same part name, hence the same seeds, policies, W and N, for these noise models ("tokens"):

- ``iid`` and ``record``: T5 as published (reproduction check against results/r1/engineering/T5_20261019T004918Z);
- ``recordctl:<s>``: the record model with the structural rho raised to s (the marginal correlations of the
  shared model at that s; isolates the shared component from the change in structural paired sd);
- ``shared:<s>``: the shared-component model (``simulate_t4.shared_correlations``) at share s.

It also adds two new quantities: the threshold correction for a selected incumbent (``part_ecorr``; oracle
known-error rule and a feasible keep-count table rule against the deployed t*), and the kernel-free inequality
of P09 section 4 on every keep (``kfree`` in every simulate output).

T5's part functions (``r1.theory.t5_report``) are reused unchanged; this module replaces the module-level
``scenario`` factory of ``t5_report`` by ``scenario_x``, which understands the extra tokens and falls back to
the original factory for ``iid`` / ``record``.
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
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from r1.theory import t5_report as R
from r1.theory.simulate_t4 import (BranchStudy, Policy, Scenario, branch_stats, branch_study, di_flag_rate,
                                   effective_rho, fit_constants, paired, shared_correlations, shared_rho_w,
                                   shared_share_for_partial, simulate, tune)

OLD_T5 = Path("results/r1/engineering/T5_20261019T004918Z")
DIG = R.DIGITS

# --------------------------------------------------------------------------------------------
# Calibration (digits_mlp; rho per kind and sigma from T5's digits scenario)
# --------------------------------------------------------------------------------------------
P_TARGET, P_LO, P_HI = 0.37, 0.24, 0.51          # E1 check: +0.37 [+0.24, +0.51] (check_kernel_e1_output.txt)
P_MAX_LOCAL = DIG.rho_local / (1 + DIG.rho_local)  # largest sibling partial reachable at rho_local (s = rho_local)
S_MID = shared_share_for_partial(P_TARGET, DIG.rho_local)
S_LO = shared_share_for_partial(P_LO, DIG.rho_local)
S_HI = DIG.rho_local if P_HI > P_MAX_LOCAL else shared_share_for_partial(P_HI, DIG.rho_local)
S_T5 = DIG.rho_struct                               # largest s at which both kinds keep T5's rho exactly

TOKENS = ["iid", "record", f"recordctl:{S_MID:.4f}", f"shared:{S_T5:.4f}", f"shared:{S_LO:.4f}",
          f"shared:{S_MID:.4f}", f"shared:{S_HI:.4f}"]
RECORDLIKE = TOKENS[1:]


def token_label(tok: str) -> str:
    if tok in ("iid", "record"):
        return tok
    kind, s = tok.split(":")
    s = float(s)
    if kind == "recordctl":
        return f"record, ϱ_struct={s:.2f}"
    p = shared_correlations(DIG.rho_local, DIG.rho_local, s)["sibling_partial"]
    return f"shared s={s:.2f} (p={p:.2f})"


_orig_scenario = R.scenario


def scenario_x(name: str, noise: str = "iid", prop: str = "stationary", kappa: float = 0.3, types=None) -> Scenario:
    """t5_report.scenario plus the tokens ``shared:<s>`` and ``recordctl:<s>``."""
    if ":" not in noise:
        return _orig_scenario(name, noise, prop, kappa, types)
    kind, s = noise.split(":")
    s = float(s)
    base = _orig_scenario(name, "record", prop, kappa, types)
    label = f"{name}/{noise}/{prop}" + (f"(k={kappa})" if prop == "dimret" else "")
    if kind == "shared":
        return replace(base, name=label, noise="shared", shared_share=s)
    if kind == "recordctl":
        node = replace(base.node, rho_local=max(base.node.rho_local, s), rho_struct=max(base.node.rho_struct, s))
        return replace(base, name=label, node=node)
    raise ValueError(noise)


R.scenario = scenario_x          # T5's part functions now accept the extra tokens


def calibration_part(ctx, name):
    rows = []
    for s in sorted({S_T5, S_LO, S_MID, S_HI}):
        rows.append({"s": s, "local_local": shared_correlations(DIG.rho_local, DIG.rho_local, s),
                     "local_struct": shared_correlations(DIG.rho_local, DIG.rho_struct, s),
                     "struct_struct": shared_correlations(DIG.rho_struct, DIG.rho_struct, s),
                     "rho_w_local": float(shared_rho_w(DIG.rho_local, s)),
                     "rho_w_struct": float(shared_rho_w(DIG.rho_struct, s)),
                     "rho_eff_struct": float(effective_rho(DIG.rho_struct, s)),
                     "paired_sd_struct": DIG.sigma * math.sqrt(2 * (1 - float(effective_rho(DIG.rho_struct, s))))})
    # simulator check: no keeps (threshold far up), so the calls' candidates are siblings of the initial config
    sims = []
    for s in (S_MID, S_T5):
        scn = scenario_x("digits_on", f"shared:{s:.4f}")
        loc = replace(scn, types=tuple(replace(t, kind="local") for t in scn.types if t.pi < 1))
        r = simulate(loc, Policy("nokeep", prior="zero", rules=False, theta0=1e6), 3, 3, 200000, 777, trace=3)
        tr = r["_trace"]
        par, a, b = tr[0, 0], tr[0, 1], tr[1, 1]
        C = np.corrcoef(np.stack([par, a, b]))
        part = (C[1, 2] - C[0, 1] * C[0, 2]) / math.sqrt((1 - C[0, 1] ** 2) * (1 - C[0, 2] ** 2))
        sims.append({"s": s, "sim_corr_parent_child": float(C[0, 1]), "sim_sibling_partial": float(part),
                     "theory": shared_correlations(DIG.rho_local, DIG.rho_local, s), "campaigns": 200000})
    # E1 digits_mlp marginal correlations corr(edit, c0) as printed (2 decimals) in check_kernel_e1_output.txt:
    # the largest s compatible with all five is their minimum; mean model partial over the 10 sibling pairs there
    e1 = [0.77, 0.82, 0.60, 0.71, 0.86]
    pairs = [(a, b) for i, a in enumerate(e1) for b in e1[i + 1:]]
    e1_rows = [{"s": s, "mean_sibling_partial": float(np.mean([shared_correlations(a, b, s)["sibling_partial"]
                                                                for a, b in pairs]))} for s in (0.3, 0.5, min(e1))]
    return {"E1_corr_edit_c0": e1, "E1_pattern": e1_rows,
            "P_target": P_TARGET, "P_interval": [P_LO, P_HI], "P_max_local": P_MAX_LOCAL, "S_MID": S_MID,
            "S_LO": S_LO, "S_HI": S_HI, "S_T5": S_T5, "node": DIG.__dict__, "rows": rows, "sim_check": sims,
            "tokens": TOKENS}


# --------------------------------------------------------------------------------------------
# Parts that T5 hard-codes for (record, iid): re-implemented with a token list (same logic and seeds)
# --------------------------------------------------------------------------------------------

def part_p9x(ctx, name, scn_name, tokens):
    seed, dev = R.seeds(name)
    out = {"rows": [], "display": []}
    W, N = 40, 80
    for noise in tokens:
        for prop in ("stationary", "dimret", "memory", "memory_debiased"):
            scn = scenario_x(scn_name, noise, prop)
            for pol in (Policy("rho", prior="zero", rules=False), Policy("oracle_threshold", prior="oracle")):
                r = simulate(scn, pol, W, N, ctx.M, seed)
                out["rows"].append({"noise": noise, "scenario": scn.name, "policy": pol.name,
                                    **r.get("p9_summary", {}), "p9_by_keep": r["p9_by_keep"], "kfree": r["kfree"],
                                    "record_bias_end": r["record_bias_end"][0],
                                    "debiased_bias_end": r["debiased_bias_end"][0],
                                    "gain": r["gain"][0], "gain_se": r["gain"][1], "bold_share": r["bold_share"],
                                    "false_keep_rate": r["false_keep_rate"]})
        harm = tuple(replace(t, mu=t.mu - 1.2 * t.tau) if t.bold else t for t in R.TYPES[scn_name])
        for bold_lab, types in (("as calibrated", None), ("harmful bold", harm)):
            for pol in (Policy("rho", prior="zero", rules=False), Policy("oracle_threshold", prior="oracle")):
                a = simulate(scenario_x(scn_name, noise, "memory_debiased", types=types), pol, W, N, ctx.M, seed)
                b = simulate(scenario_x(scn_name, noise, "memory", types=types), pol, W, N, ctx.M, seed)
                d, se = paired(a, b)
                out["display"].append({"noise": noise, "bold": bold_lab, "policy": pol.name,
                                       "debiased_minus_raw": d, "se": se,
                                       "gain_raw": b["gain"][0], "gain_debiased": a["gain"][0],
                                       "bold_raw": b["bold_share"], "bold_debiased": a["bold_share"]})
    return out


def part_p10x(ctx, name, scn_name, W, tokens):
    seed, dev = R.seeds(name)
    N = W
    grid = {"theta0": [-0.4, -0.2, 0.0, 0.2, 0.4, 0.7, 1.0], "theta1": [-0.4, 0.0, 0.4, 0.8, 1.2]}
    out = {"W": W, "N": N, "rows": []}
    cases = [c for c in R.P10_CASES if c[0] == "iid"]
    for tok in tokens:
        if tok == "iid":
            continue
        cases += [(tok, prop, kappa, label.replace("record", token_label(tok)) if tok != "record" else label)
                  for noise, prop, kappa, label in R.P10_CASES if noise == "record"]
    for noise, prop, kappa, label in cases:
        scn = scenario_x(scn_name, noise, prop, kappa)
        best, tab = tune(scn, Policy("lookahead", prior="oracle"), W, N, ctx.Mdev, dev, None, grid)
        my = simulate(scn, Policy("myopic", prior="oracle"), W, N, ctx.Mbig, seed)
        la = simulate(scn, best, W, N, ctx.Mbig, seed)
        d, se = paired(la, my)
        out["rows"].append({"noise": noise, "case": label, "prop": prop, "scenario": scn.name,
                            "theta0": best.theta0, "theta1": best.theta1,
                            "myopic": my["gain"][0], "lookahead": la["gain"][0], "diff": d, "diff_se": se,
                            "diff_dn": d / scn.node.delta_n,
                            "dev_gain_gap": max(t["dev_gain"] for t in tab) -
                            [t for t in tab if t["theta0"] == 0.0 and t["theta1"] == 0.0][0]["dev_gain"]})
    return out


def part_di_x(ctx, name, split, rho, s, feedback=0.0):
    """T5's part_di for the digits homogeneous study; s = None is T5's kernel (record) model. With s, the shared
    model is run as the kernel branch study at the per-configuration kernel coefficients r_w(rho, s) (local) and
    r_w(min(rho, 0.5), s) (structural): u is common to both branches of an instance and to both runs of every
    comparison, so it cancels in every comparison, contrast and distance the study computes, and the per-run sd of
    the per-configuration part follows from the paired sds as in T5."""
    seed, _ = R.seeds(name)
    cfg = R.DI_STUDIES["digits"]
    rs = min(rho, 0.5)
    if s is None:
        rk, rsk = rho, None
    else:
        rk, rsk = float(shared_rho_w(rho, s)), float(shared_rho_w(rs, s))
    bs = BranchStudy("digits/hom", R.di_types("digits", "hom"), cfg["sigma_t_d"], cfg["sigma_s_d"], rho=rk,
                     rho_struct=rsk, split=split,
                     feedback_shift=feedback * math.hypot(cfg["sigma_t_d"], cfg["sigma_s_d"]))
    br = branch_study(bs, ctx.n_branch, seed)
    st = branch_stats(br)
    fr = di_flag_rate(br, 6, 199 if ctx.quick else 499, seed + 1)
    return {"study": bs.name, "split": split, "rho": rho, "shared_share": s, "rho_w_local": rk,
            "rho_w_struct": rs if rsk is None else rsk,
            "sibling_partial_local": None if s is None else shared_correlations(rho, rho, s)["sibling_partial"],
            "feedback_shift_sd": feedback, "n_inst": ctx.n_branch, "population": st, "small_studies": fr}


def _fit_table(ktab: np.ndarray, min_n: int = 200) -> tuple:
    cnt, sx, sxx = ktab
    m, v = [], []
    last_m, last_v = 0.0, 0.0
    for k in range(cnt.size):
        if cnt[k] >= min_n:
            last_m = sx[k] / cnt[k]
            last_v = max(sxx[k] / cnt[k] - last_m ** 2, 0.0)
        m.append(float(last_m))
        v.append(float(last_v))
    return tuple(m), tuple(v)


def part_ecorr(ctx, name, scn_name, W, tokens):
    """Value of correcting the Bayes threshold for a selected incumbent: deployed t* (none) vs a feasible
    keep-count table rule (table, fitted on development runs by two fixed-point passes) vs the oracle that knows the
    incumbent's inherited error (known; an upper bound on any correction based on the history)."""
    seed, dev = R.seeds(name)
    N = 2 * W
    out = {"scenario": scn_name, "W": W, "N": N, "rows": []}
    for tok in tokens:
        scn = scenario_x(scn_name, tok)
        const = fit_constants(scn, W, N, ctx.Mdev, dev + 1)
        for bname, base in (("oracle_threshold", Policy("oracle_threshold", prior="oracle")),
                            ("A2", Policy("A2", prior="rules"))):
            r0 = simulate(scn, base, W, N, ctx.M, seed, const)
            row = {"noise": tok, "base": bname, "none": _summ(r0, scn)}
            if tok != "iid":
                tab = simulate(scn, base, W, N, ctx.Mdev, dev + 2, const)["_ktab"]
                pol_t = base
                for _ in range(2):
                    m, v = _fit_table(tab)
                    pol_t = replace(base, name=bname + "+table", ecorr="table", ecorr_m=m, ecorr_v=v)
                    tab = simulate(scn, pol_t, W, N, ctx.Mdev, dev + 2, const)["_ktab"]
                m, v = _fit_table(tab)
                pol_t = replace(base, name=bname + "+table", ecorr="table", ecorr_m=m, ecorr_v=v)
                rt = simulate(scn, pol_t, W, N, ctx.M, seed, const)
                rk = simulate(scn, replace(base, name=bname + "+known", ecorr="known"), W, N, ctx.M, seed, const)
                row["table"] = _summ(rt, scn)
                row["known"] = _summ(rk, scn)
                row["table_m"], row["table_v"] = list(m), list(v)
                for lab, rr in (("table", rt), ("known", rk)):
                    d, se = paired(rr, r0)
                    row[f"{lab}_minus_none"] = d
                    row[f"{lab}_minus_none_se"] = se
                    row[f"{lab}_minus_none_dn"] = d / scn.node.delta_n
            out["rows"].append(row)
    return out


def part_a1rho(ctx, name, scn_name, W, tokens):
    """Paired s.e. of A1 - rho and A2 - rho for the S1 cells (T5's part_main does not store it). Same seeds and the
    same dev-fitted constants as part_main: iid uses the T5 iid part's seeds, the other tokens the record part's."""
    N = 2 * W
    out = {"scenario": scn_name, "W": W, "rows": []}
    for tok in tokens:
        nm = name.replace("_record_", "_iid_") if tok == "iid" else name
        seed, dev = R.seeds(nm)
        scn = scenario_x(scn_name, tok)
        const = fit_constants(scn, W, N, ctx.Mdev, dev + 1)
        rr = {k: simulate(scn, p, W, N, ctx.M, seed, const) for k, p in
              (("rho", Policy("rho", prior="zero", rules=False)), ("A1", Policy("A1", prior="const", rules=False)),
               ("A2", Policy("A2", prior="rules")))}
        d1, se1 = paired(rr["A1"], rr["rho"])
        d2, se2 = paired(rr["A2"], rr["rho"])
        out["rows"].append({"noise": tok, "seed_part": nm, "A1_minus_rho": d1, "A1_minus_rho_se": se1,
                            "A2_minus_rho": d2, "A2_minus_rho_se": se2})
    return out


def _summ(r: dict, scn: Scenario) -> dict:
    return {"gain": r["gain"][0], "se": r["gain"][1], "gain_dn": r["gain"][0] / scn.node.delta_n,
            "keeps": r["keeps"], "false_keep_rate": r["false_keep_rate"], "runs": r["runs"],
            "mean_threshold_executed": r["mean_threshold_executed"], "kfree": r["kfree"],
            "record_bias_end": r["record_bias_end"][0]}


# --------------------------------------------------------------------------------------------
# Part list (part file name = "<T5 part name>__<token>"; the T5 part name sets the seeds)
# --------------------------------------------------------------------------------------------

def _tokname(tok: str) -> str:
    return tok.replace(":", "_")


def parts_list():
    L = [("calibration", calibration_part, ())]
    for s in ("digits_on", "digits_off"):
        for W in (20, 40):
            L.append((f"main_{s}_iid_W{W}", R.part_main, (s, "iid", W), f"main_{s}_iid_W{W}"))
            for tok in RECORDLIKE:
                L.append((f"main_{s}_record_W{W}__{_tokname(tok)}", R.part_main, (s, tok, W), f"main_{s}_record_W{W}"))
    for s, props in (("digits_on", ("stationary", "dimret", "memory")), ("digits_off", ("stationary",))):
        for prop in props:
            L.append((f"p7_{s}_iid_{prop}_W20", R.part_p7, (s, "iid", prop, 20), f"p7_{s}_iid_{prop}_W20"))
            for tok in RECORDLIKE:
                L.append((f"p7_{s}_record_{prop}_W20__{_tokname(tok)}", R.part_p7, (s, tok, prop, 20),
                          f"p7_{s}_record_{prop}_W20"))
    L.append(("p8_digits_on_iid", R.part_p8, ("digits_on", "iid"), "p8_digits_on_iid"))
    for tok in RECORDLIKE:
        L.append((f"p8_digits_on_record__{_tokname(tok)}", R.part_p8, ("digits_on", tok), "p8_digits_on_record"))
    L.append(("p9_digits_on__all", part_p9x, ("digits_on", TOKENS), "p9_digits_on"))
    for W in (20, 40):
        L.append((f"p10_digits_on_W{W}__all", part_p10x, ("digits_on", W, TOKENS), f"p10_digits_on_W{W}"))
    L.append(("predictor_digits_on_iid_W20", R.part_predictor, ("digits_on", "iid", 20), "predictor_digits_on_iid_W20"))
    for tok in RECORDLIKE:
        L.append((f"predictor_digits_on_record_W20__{_tokname(tok)}", R.part_predictor, ("digits_on", tok, 20),
                  "predictor_digits_on_record_W20"))
    # DI branch study at the digits scale; rho = 0.8 is T5's digits-like cell (s from the same partial targets)
    s8 = {"mid": shared_share_for_partial(P_TARGET, 0.8), "lo": shared_share_for_partial(P_LO, 0.8), "hi": 0.8,
          "t5": 0.5}
    for split in ("fixed", "vary"):
        nm = f"di_digits_hom_{split}_rho0.8"
        L.append((nm + "__record", part_di_x, (split, 0.8, None), nm))
        for lab, s in s8.items():
            L.append((f"{nm}__shared_{lab}", part_di_x, (split, 0.8, s), nm))
        nm5 = f"di_digits_hom_{split}_rho0.5"
        L.append((nm5 + "__record", part_di_x, (split, 0.5, None), nm5))
        L.append((nm5 + "__shared_max", part_di_x, (split, 0.5, 0.5), nm5))
    nmf = "di_digits_hom_fixed_rho0.5_feedback"
    L.append((nmf + "__record", part_di_x, ("fixed", 0.5, None, 0.5), nmf))
    L.append((nmf + "__shared_max", part_di_x, ("fixed", 0.5, 0.5, 0.5), nmf))
    for s in ("digits_on", "digits_off"):
        for W in (20, 40):
            L.append((f"ecorr_{s}_W{W}__all", part_ecorr, (s, W, TOKENS), f"ecorr_{s}_W{W}"))
    for s in ("digits_on", "digits_off"):
        for W in (20, 40):
            L.append((f"a1rho_{s}_W{W}__all", part_a1rho, (s, W, TOKENS), f"main_{s}_record_W{W}"))
    return [(x[0], x[1], x[2], x[3] if len(x) > 3 else x[0]) for x in L]


def _jsonable(o):
    """t5_report._jsonable, plus +-inf -> None (min margin when a cell has no keeps)."""
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    o = R._jsonable(o)
    if isinstance(o, list):
        return [_jsonable(v) for v in o]
    if isinstance(o, float) and math.isinf(o):
        return None
    return o


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--only", default=None)
    args = ap.parse_args(argv)
    out = Path(args.out)
    (out / "parts").mkdir(parents=True, exist_ok=True)
    ctx = R.Ctx(args.quick)
    for name, fn, a, seedname in parts_list():
        path = out / "parts" / f"{name}.json"
        if path.exists() or (args.only and not name.startswith(args.only)):
            continue
        ts = time.time()
        res = fn(ctx, seedname, *a)
        res["_seconds"] = time.time() - ts
        res["_seeds"] = list(R.seeds(seedname))
        res["_seed_part"] = seedname
        path.write_text(json.dumps(_jsonable(res), indent=1) + "\n")
        print(f"{name}: {res['_seconds']:.1f}s", flush=True)
    todo = parts_list()
    missing = [n for n, *_ in todo if not (out / "parts" / f"{n}.json").exists()]
    if missing:
        print(f"PENDING {len(missing)} parts")
        return 0
    try:
        rev = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False).stdout.strip()
    except OSError:
        rev = ""
    src = Path(__file__).resolve().parent
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (src / "simulate_t4.py", src / "t5_report.py", src / "t5_shared_report.py")}
    parts = {n: json.loads((out / "parts" / f"{n}.json").read_text()) for n, *_ in todo}
    manifest = {"label": "ENGINEERING_ONLY", "note": "model-based numbers, not measurements; AI-assisted (Claude, subagent)",
                "utc_written": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"), "base_seed": R.BASE_SEED,
                "quick": args.quick, "M_test": ctx.M, "M_big": ctx.Mbig, "M_dev": ctx.Mdev, "n_branch": ctx.n_branch,
                "tokens": TOKENS, "parts": {n: {"seconds": parts[n]["_seconds"], "seeds": parts[n]["_seeds"],
                                                "seed_part": parts[n]["_seed_part"]} for n in parts},
                "total_part_seconds": sum(parts[n]["_seconds"] for n in parts),
                "git_head_at_write": rev, "source_sha256": hashes,
                "host": {"platform": platform.platform(), "python": platform.python_version(), "numpy": np.__version__}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("ALL PARTS DONE; manifest.json written (tables: python -m r1.theory.t5_shared_tables --out <dir>)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
