#!/usr/bin/env python3
"""Positive control of PLAN R1-CONTROLS-ROW. SUPPORT, tier S; AI-assisted (Claude, subagent); reviewed once, re-checked (ACCEPTED).

Question: for each T0 node covered by the accepted 22 Oct E1 runs (R1-E1-PILOT-ACCEPT) and each of its five E1
single edits, how likely is a K-seed fresh-seed audit to detect the edit, whose effect is known from the 30 joint
seeds? The audit statistic and the detection readings are defined in
``docs/r1/reports/CONTROLS_POSITIVE_20261123.md`` §1:

- per seed s: d_s = m(c0 + e, s) - m(c0, s) on joint seeds (train seed = split seed = s), the pairing of
  ``r1/c3/audit.py`` ``paired``;
- the audit reads mean_K and sd_K (ddof = 1) of K paired differences; direction = sign of the 30-seed mean (0 -> +);
- R-0: direction * mean_K > 0;
- R-delta: direction * mean_K > delta_n (D18, ``r1.c3.dataset.noise_table``);
- R-t: direction * mean_K / (sd_K / sqrt(K)) > t_{1 - alpha, K - 1}, alpha = 0.05 (sd_K = 0: detected iff
  direction * mean_K > 0);
- R-delta-t: R-delta and R-t.

K = 10 is Y (D.3) and the full audit; K = 5 is the training label (and, identically under this resampling, the
evaluation value). Detection probabilities come from subsets of K of the 30 joint seeds drawn without replacement:
every subset when there are at most ``EXHAUSTIVE_MAX`` of them (K = 5: C(30, 5) = 142,506), otherwise ``--draws``
uniform random subsets from PCG64 with a fixed seed (K = 10), shared by every node and edit. Analytic normal (and
noncentral-t) approximations are reported beside them: "super" uses sd/sqrt(K), the variance of a fresh-seed audit;
"fpc" multiplies it by the finite-population factor (N - K)/N, the variance of the resampling scheme itself.

Reads only ``runs.jsonl``, ``edits.json`` and ``summary.json`` of the accepted run, each checked against its
sha256, and the pinned T0 noise source's sha256-checked ``summary.json`` for the reference delta_n of
PRE-DELTA. Refuses ``r1_sealed`` paths. Writes ``controls_positive.json`` and ``tables.md``.

Usage: python -m r1.noise.controls_positive [--out DIR] [--draws N] [--seed S]
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np
from scipy import stats

from r1.c3.analysis_guard import refuse_sealed
from r1.harness import REPO

SCHEMA = "r1.controls_positive/1"
RUN_DIR = "results/r1/pilot/E1_20261022T214606Z"
RUN_SHA256 = {  # accepted by R1-E1-PILOT-ACCEPT; summary.json is also the D28 source's common_summary pin
    "runs.jsonl": "03aa9ee1231a59f38422c58733e7f4ac059df7d2014076485d0f907a0c0d5a22",
    "edits.json": "a37adfa3ffbfb7847f3e03fee061760172af7923d453c6c0649bbf730df6a7f6",
    "summary.json": "eabc2f5c05b08cf900ab988838e41dc7f8db35a4131f4b57e72514e0e5513793",
}
PINNED_NOISE = "results/r1/noise/D28_REPAIR_20261027/summary.json"  # preregistration PRE-DELTA
PINNED_NOISE_SHA256 = "3d12ce058c584d862b683bf9e0c79b8c1f7609343c7b62b839c00c4a83c34310"
DEFAULT_OUT = "results/r1/engineering/controls_positive_20261123"

# gate.T0_NODES (r1/c3/gate.py v3.1), copied so this module imports nothing from the gate; a test checks equality.
T0_NODES = ("digits_mlp", "openml_breast_w", "openml_climate", "openml_credit_approval",
            "openml_ionosphere", "openml_sonar", "openml_wdbc", "tabular_mlp")
# R1-D28-REPAIR (PLAN §10, 27 Oct): new start configurations after the 22 Oct run; the pinned noise source takes
# these three nodes from the repair re-measurement, not from the 22 Oct run.
REPAIRED = ("openml_breast_w", "openml_sonar", "openml_wdbc")
JOINT_SEEDS = tuple(range(3001, 3031))
KS = (10, 5)
ALPHA = 0.05
DRAWS = 200_000
SEED = 20261123
EXHAUSTIVE_MAX = 1_000_000
CHECK_SEED_OFFSET = 1000  # the K-exhaustive Monte Carlo check draws with default_rng(seed + 1000 + K)
READINGS = ("R0", "Rdelta", "Rt", "Rdelta_t")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def check_inputs(run_dir: Path, expected: dict | None = RUN_SHA256) -> dict:
    out = {}
    for name in ("runs.jsonl", "edits.json", "summary.json"):
        p = run_dir / name
        refuse_sealed(p)
        out[name] = sha256(p)
        if expected is not None and out[name] != expected[name]:
            raise ValueError(f"{p}: sha256 {out[name]} is not the accepted {expected[name]}")
    return out


def load_joint(run_dir: Path, nodes, seeds=JOINT_SEEDS) -> dict:
    """{node: {config: {seed: metric}}} for the joint condition; every run must have succeeded."""
    out = {n: {} for n in nodes}
    with open(run_dir / "runs.jsonl", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            r = json.loads(line)
            if r["node"] not in out or r["condition"] != "joint":
                continue
            if r["train_seed"] != r["split_seed"]:
                raise ValueError(f"joint run with train seed {r['train_seed']} != split seed {r['split_seed']}")
            if not r.get("success") or r.get("metric") is None:
                raise ValueError(f"{r['node']} {r['config']} seed {r['train_seed']}: failed run")
            cfg = out[r["node"]].setdefault(r["config"], {})
            s = int(r["train_seed"])
            if s in cfg:
                raise ValueError(f"{r['node']} {r['config']} seed {s}: duplicate joint run")
            cfg[s] = float(r["metric"])
    for node, cfgs in out.items():
        for c, runs in cfgs.items():
            if tuple(sorted(runs)) != tuple(seeds):
                raise ValueError(f"{node} {c}: joint seeds are not exactly {seeds[0]}..{seeds[-1]}")
    return out


def paired_differences(cfgs: dict, cfg: str) -> np.ndarray:
    """d_s = m(cfg, s) - m(c0, s) in seed order (candidate minus incumbent, as ``audit.paired``)."""
    base, cand = cfgs["c0"], cfgs[cfg]
    if set(base) != set(cand):
        raise ValueError(f"{cfg}: seeds differ from c0")
    return np.array([cand[s] - base[s] for s in sorted(base)], dtype=float)


def effect(d: np.ndarray) -> dict:
    sd = float(np.std(d, ddof=1))
    return {"n": int(d.size), "mean": float(d.mean()), "sd": sd, "se": sd / math.sqrt(d.size)}


def direction_of(mean: float) -> int:
    return -1 if mean < 0 else 1


def classify(mean: float, se: float, delta_n: float) -> str:
    """'above' if |mean| - 2 se > delta_n, 'below' if |mean| + 2 se < delta_n, else 'near'."""
    a = abs(mean)
    if a - 2 * se > delta_n:
        return "above"
    if a + 2 * se < delta_n:
        return "below"
    return "near"


def all_subsets(n: int, k: int) -> np.ndarray:
    return np.array(list(itertools.combinations(range(n), k)), dtype=np.int16)


def random_subsets(n: int, k: int, draws: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)  # PCG64
    idx = np.argsort(rng.random((draws, n)), axis=1)[:, :k]
    return np.sort(idx, axis=1).astype(np.int16)


def subsets_for(n: int, k: int, draws: int, seed: int) -> tuple[np.ndarray, str]:
    if math.comb(n, k) <= EXHAUSTIVE_MAX:
        return all_subsets(n, k), "exhaustive"
    return random_subsets(n, k, draws, seed), "monte_carlo"


def t_crit(k: int, alpha: float = ALPHA) -> float:
    return float(stats.t.ppf(1.0 - alpha, k - 1))


def subset_statistics(d: np.ndarray, subsets: np.ndarray, direction: int) -> tuple[np.ndarray, np.ndarray]:
    """Oriented mean_K and one-sample t of each subset (sd_K = 0: t = +-inf by the sign of the mean, 0 if 0)."""
    x = direction * d[subsets]
    k = subsets.shape[1]
    m = x.mean(axis=1)
    sd = x.std(axis=1, ddof=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.where(sd > 0, m / (sd / math.sqrt(k)), np.sign(m) * np.inf)
    t = np.where((sd == 0) & (m == 0), 0.0, t)
    return m, t


def detection(d: np.ndarray, subsets: np.ndarray, delta_n: float, direction: int, method: str,
              alpha: float = ALPHA) -> dict:
    k = subsets.shape[1]
    m, t = subset_statistics(d, subsets, direction)
    hits = {"R0": m > 0, "Rdelta": m > delta_n, "Rt": t > t_crit(k, alpha)}
    hits["Rdelta_t"] = hits["Rdelta"] & hits["Rt"]
    n = int(subsets.shape[0])
    out = {"k": k, "subsets": n, "method": method}
    for r in READINGS:
        p = float(hits[r].mean())
        out[r] = {"p": p, "mc_error": math.sqrt(p * (1 - p) / n) if method == "monte_carlo" else 0.0}
    return out


def _phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0))) if math.isfinite(x) else (1.0 if x > 0 else 0.0)


def _z(num: float, den: float) -> float:
    if den > 0:
        return num / den
    return math.inf if num > 0 else (-math.inf if num < 0 else 0.0)


def analytic(eff: dict, delta_n: float, k: int, n_pop: int, alpha: float = ALPHA) -> dict:
    """Normal approximations at the plug-in effect (oriented by its sign); R-t by the noncentral t."""
    m = direction_of(eff["mean"]) * eff["mean"]
    se_k = eff["sd"] / math.sqrt(k)
    se_fpc = se_k * math.sqrt((n_pop - k) / n_pop)
    out = {
        "R0_super": _phi(_z(m, se_k)), "R0_fpc": _phi(_z(m, se_fpc)),
        "Rdelta_super": _phi(_z(m - delta_n, se_k)), "Rdelta_fpc": _phi(_z(m - delta_n, se_fpc)),
        "Rdelta_super_at_mean_minus_2se": _phi(_z(m - 2 * eff["se"] - delta_n, se_k)),
        "Rdelta_super_at_mean_plus_2se": _phi(_z(m + 2 * eff["se"] - delta_n, se_k)),
    }
    if se_k > 0:
        out["Rt_super_nct"] = float(stats.nct.sf(t_crit(k, alpha), k - 1, m / se_k))
    else:
        out["Rt_super_nct"] = 1.0 if m > 0 else 0.0
    return out


def monte_carlo_check(cases: list, k: int, draws: int, seed: int) -> dict | None:
    """Re-estimate exhaustively enumerated cells by Monte Carlo (``draws`` subsets, default_rng(seed + 1000 + K)).

    ``cases``: (paired differences, delta_n, direction, exhaustive detection) per edit. Returns, per reading, the
    largest |Monte Carlo - exhaustive| and the largest such difference in Monte Carlo standard errors (cells with
    a nonzero error only); None when the K cells were themselves drawn by Monte Carlo.
    """
    if not cases or cases[0][3]["method"] != "exhaustive":
        return None
    sub = random_subsets(len(cases[0][0]), k, draws, seed + CHECK_SEED_OFFSET + k)
    out = {"k": k, "draws": draws, "rng": f"numpy PCG64 default_rng(seed + {CHECK_SEED_OFFSET} + K)", "cells": len(cases)}
    for r in READINGS:
        diffs, zs = [], []
        for d, dn, sgn, ex in cases:
            mc = detection(d, sub, dn, sgn, "monte_carlo")[r]
            diffs.append(abs(mc["p"] - ex[r]["p"]))
            if mc["mc_error"] > 0:
                zs.append(diffs[-1] / mc["mc_error"])
        out[r] = {"max_abs_difference": max(diffs), "max_difference_in_mc_errors": max(zs) if zs else None}
    return out


def node_noise(summary_path: Path) -> dict:
    from r1.c3.dataset import noise_table
    return noise_table(summary_path)


def run(run_dir: Path, out: Path | None, draws: int = DRAWS, seed: int = SEED, ks=KS,
        expected_sha=RUN_SHA256, pinned_noise: Path | None = None, nodes=T0_NODES) -> dict:
    refuse_sealed(run_dir, out)
    shas = check_inputs(run_dir, expected_sha)
    edits = json.loads((run_dir / "edits.json").read_text())
    summary = json.loads((run_dir / "summary.json").read_text())
    covered = [n for n in nodes if n in edits]
    noise = node_noise(run_dir / "summary.json")
    pinned = {}
    if pinned_noise is not None:
        refuse_sealed(pinned_noise)
        got = sha256(pinned_noise)
        if got != PINNED_NOISE_SHA256:
            raise ValueError(f"{pinned_noise}: sha256 {got} is not the pinned {PINNED_NOISE_SHA256}")
        pinned = node_noise(pinned_noise)
    joint = load_joint(run_dir, covered)
    n_pop = len(JOINT_SEEDS)
    subsets = {k: subsets_for(n_pop, k, draws, seed + k) for k in ks}
    check_cases = {k: [] for k in ks}
    result = {
        "schema": SCHEMA, "plan_row": "R1-CONTROLS-ROW", "label": "SUPPORT", "tier": "S",
        "reviewed": "once: docs/r1/reviews/CONTROLS_POSITIVE_REVIEW_20261123.md (ACCEPT WITH MINOR); one correction round",
        "ai_assisted": "Claude (subagent)", "date": "2026-11-23",
        "inputs": {"run_dir": RUN_DIR if run_dir.resolve() == (REPO / RUN_DIR).resolve() else str(run_dir),
                   "sha256": shas,
                   "pinned_noise": ({"path": PINNED_NOISE, "sha256": PINNED_NOISE_SHA256}
                                    if pinned_noise is not None else None),
                   "script_sha256": sha256(Path(__file__))},
        "parameters": {"joint_seeds": [JOINT_SEEDS[0], JOINT_SEEDS[-1]], "n_seeds": n_pop, "ks": list(ks),
                       "alpha_one_sided": ALPHA, "t_crit": {str(k): t_crit(k) for k in ks},
                       "draws": draws, "rng": "numpy PCG64 default_rng(seed + K)", "seed": seed,
                       "mc_error": "sqrt(p (1 - p) / subsets) for Monte Carlo cells, 0 for exhaustive cells; a Monte "
                                   "Carlo cell with p = 0 or 1 has a 95 % bound of 3 / subsets (rule of three)",
                       "subsets": {str(k): {"method": subsets[k][1], "count": int(subsets[k][0].shape[0])}
                                   for k in ks}},
        "readings": {"R0": "direction * mean_K > 0",
                     "Rdelta": "direction * mean_K > delta_n",
                     "Rt": "direction * mean_K / (sd_K / sqrt(K)) > t_{0.95, K-1}; sd_K = 0: direction * mean_K > 0",
                     "Rdelta_t": "Rdelta and Rt",
                     "direction": "sign of the 30-seed mean paired difference, 0 counted as +"},
        "nodes": {}, "not_determined": {},
    }
    for node in nodes:
        if node not in covered:
            result["not_determined"][node] = "not in the accepted 22 Oct E1 run (no joint seeds for this node)"
            continue
        dn = noise[node]["delta_n"]
        entry = {"start_configuration": "pre_repair" if node in REPAIRED else "current",
                 "delta_n": dn, "sigma_node": noise[node]["sigma_node"],
                 "delta_n_pinned": pinned.get(node, {}).get("delta_n"),
                 "sigma_node_pinned": pinned.get(node, {}).get("sigma_node"), "edits": []}
        sum_edits = {e["edit"]: e for e in summary["nodes"][node]["edits"]}
        for i, ed in enumerate(edits[node], start=1):
            cfg = f"c{i}"
            label = f"{ed['symbol']} {ed['old']} -> {ed['new']}"
            d = paired_differences(joint[node], cfg)
            eff = effect(d)
            ref = sum_edits[label]
            if abs(ref["delta_hat_J"] - eff["mean"]) > 1e-12 or abs(ref["sd_joint"] - eff["sd"]) > 1e-12:
                raise ValueError(f"{node} {label}: recomputed effect differs from summary.json")
            sgn = direction_of(eff["mean"])
            rec = {"config": cfg, "edit": label, **eff, "direction": sgn,
                   "kind": "improvement" if eff["mean"] > 0 else ("harm" if eff["mean"] < 0 else "zero"),
                   "vs_delta_n": classify(eff["mean"], eff["se"], dn),
                   "effect_over_delta_n": abs(eff["mean"]) / dn,
                   "detection": {}, "analytic": {}}
            for k in ks:
                rec["detection"][str(k)] = detection(d, subsets[k][0], dn, sgn, subsets[k][1])
                rec["analytic"][str(k)] = analytic(eff, dn, k, n_pop)
                if entry["delta_n_pinned"] is not None and entry["delta_n_pinned"] != dn:
                    rec["detection"][str(k)]["Rdelta_at_pinned_delta_n"] = detection(
                        d, subsets[k][0], entry["delta_n_pinned"], sgn, subsets[k][1])["Rdelta"]
            for k in ks:
                check_cases[k].append((d, dn, sgn, rec["detection"][str(k)]))
            entry["edits"].append(rec)
        result["nodes"][node] = entry
    result["summary"] = summarise(result, ks)
    result["checks"] = {f"monte_carlo_vs_exhaustive_K{k}": monte_carlo_check(check_cases[k], k, draws, seed)
                        for k in ks if subsets[k][1] == "exhaustive"}
    result["max_mc_error"] = max_mc_error(result)
    if out is not None:
        out.mkdir(parents=True, exist_ok=True)
        (out / "controls_positive.json").write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
        (out / "tables.md").write_text(tables(result, ks))
    return result


def summarise(result: dict, ks) -> dict:
    """Detection by effect class: count, min, median and max over edits, per K and reading."""
    groups: dict[str, list] = {}
    for node, entry in result["nodes"].items():
        for e in entry["edits"]:
            for key in (f"{e['vs_delta_n']}", f"{e['vs_delta_n']}, {e['kind']}",
                        f"{e['vs_delta_n']}, {entry['start_configuration']}",
                        f"{e['vs_delta_n']}, {e['kind']}, {entry['start_configuration']}"):
                groups.setdefault(key, []).append(e)
    out = {}
    for key, es in sorted(groups.items()):
        out[key] = {"n_edits": len(es)}
        for k in ks:
            for r in READINGS:
                ps = [e["detection"][str(k)][r]["p"] for e in es]
                out[key][f"K{k}_{r}"] = {"min": min(ps), "median": float(np.median(ps)), "max": max(ps)}
    return out


def _f(x: float, nd: int = 4) -> str:
    return f"{x:.{nd}f}"


def _p(det: dict) -> str:
    return f"{det['p']:.3f}"


def max_mc_error(result: dict) -> float:
    errs = [d[r]["mc_error"] for entry in result["nodes"].values() for e in entry["edits"]
            for d in e["detection"].values() for r in READINGS]
    return max(errs) if errs else 0.0


def tables(result: dict, ks) -> str:
    lines = ["# Positive control (R1-CONTROLS-ROW): tables generated by `r1/noise/controls_positive.py`", "",
             f"SUPPORT, tier S; AI-assisted (Claude, subagent); reviewed once (ACCEPT WITH MINOR), corrected in one "
             f"round, re-checked (ACCEPTED). Inputs: `{result['inputs']['run_dir']}` "
             f"(runs.jsonl sha256 `{result['inputs']['sha256']['runs.jsonl'][:12]}…`).", "",
             f"Detection probabilities: K = 10 from {result['parameters']['subsets']['10']['count']:,} random subsets "
             f"(largest Monte Carlo standard error over all cells: {max_mc_error(result):.4f}; per-cell errors in the "
             "JSON); K = 5 over all subsets (exact for the resampling scheme). Direction = sign of the 30-seed mean. "
             "Class: above / below if the ±2 se interval of the 30-seed mean lies above / below δ_n, near otherwise.",
             "",
             "Table C: the groups 'class' and 'class, kind' pool the current-start rows with the pre-repair rows "
             "of openml_breast_w, openml_sonar and openml_wdbc, whose start configuration the sweeps no longer use; "
             "groups that name a start configuration (current / pre_repair) separate them.",
             ""]
    for key, chk in result.get("checks", {}).items():
        if chk:
            worst = max(READINGS, key=lambda r: chk[r]["max_abs_difference"])
            lines += [f"Check `{key}`: the exhaustive K = {chk['k']} cells re-estimated from {chk['draws']:,} random "
                      f"subsets differ by at most {chk[worst]['max_abs_difference']:.4f} (reading {worst}); largest "
                      "difference in Monte Carlo standard errors per reading: "
                      + ", ".join(f"{r} {chk[r]['max_difference_in_mc_errors']:.2f}" for r in READINGS) + ".", ""]
    head = ("| Node | start config | Edit | Δ̂ (30 seeds) ± se | δ_n | class | "
            "K=10 R-δ | K=10 R-t | K=10 R-δt | K=10 R-0 | K=5 R-δ | K=5 R-t | K=5 R-δt | K=5 R-0 |")
    lines += ["## Table A — detection probability per node and edit", "", head, "|" + "---|" * 14]
    for node, entry in result["nodes"].items():
        for e in entry["edits"]:
            d10, d5 = e["detection"]["10"], e["detection"]["5"]
            lines.append(
                f"| `{node}` | {entry['start_configuration']} | {e['edit']} | {e['mean']:+.4f} ± {e['se']:.4f} | "
                f"{entry['delta_n']:.4f} | {e['vs_delta_n']} | {_p(d10['Rdelta'])} | {_p(d10['Rt'])} | "
                f"{_p(d10['Rdelta_t'])} | {_p(d10['R0'])} | {_p(d5['Rdelta'])} | {_p(d5['Rt'])} | "
                f"{_p(d5['Rdelta_t'])} | {_p(d5['R0'])} |")
    lines += ["", "## Table B — analytic check (plug-in effect): R-δ normal, super-population and finite-population; "
              "R-t noncentral t; R-δ at Δ̂ ∓ 2 se", "",
              "| Node | Edit | K | R-δ resampled | R-δ normal fpc | R-δ normal super | R-δ super at Δ̂−2se … Δ̂+2se | "
              "R-t resampled | R-t nct super |", "|---|---|---|---|---|---|---|---|---|"]
    for node, entry in result["nodes"].items():
        for e in entry["edits"]:
            for k in ks:
                a, d = e["analytic"][str(k)], e["detection"][str(k)]
                lo, hi = a["Rdelta_super_at_mean_minus_2se"], a["Rdelta_super_at_mean_plus_2se"]
                lines.append(f"| `{node}` | {e['edit']} | {k} | {_p(d['Rdelta'])} | {a['Rdelta_fpc']:.3f} | "
                             f"{a['Rdelta_super']:.3f} | {lo:.3f} … {hi:.3f} | {_p(d['Rt'])} | "
                             f"{a['Rt_super_nct']:.3f} |")
    lines += ["", "## Table C — summary by class (min / median / max detection probability over edits)", "",
              "| Class | edits | " + " | ".join(f"K={k} {r}" for k in ks for r in ("Rdelta", "Rt", "Rdelta_t")) + " |",
              "|---|---|" + "---|" * (len(ks) * 3)]
    for key, s in result["summary"].items():
        cells = [f"{s[f'K{k}_{r}']['min']:.3f} / {s[f'K{k}_{r}']['median']:.3f} / {s[f'K{k}_{r}']['max']:.3f}"
                 for k in ks for r in ("Rdelta", "Rt", "Rdelta_t")]
        lines.append(f"| {key} | {s['n_edits']} | " + " | ".join(cells) + " |")
    lines += ["", "## Nodes not determined", ""]
    for node, why in result["not_determined"].items():
        lines.append(f"- `{node}`: {why}")
    lines += ["", "## δ_n: 22 Oct summary vs the pinned T0 noise source (PRE-DELTA)", "",
              "| Node | start config | δ_n (22 Oct) | δ_n (pinned) | σ_node (22 Oct) | σ_node (pinned) |",
              "|---|---|---|---|---|---|"]
    for node, entry in result["nodes"].items():
        dp, sp = entry["delta_n_pinned"], entry["sigma_node_pinned"]
        lines.append(f"| `{node}` | {entry['start_configuration']} | {entry['delta_n']:.5f} | "
                     f"{'–' if dp is None else f'{dp:.5f}'} | {entry['sigma_node']:.5f} | "
                     f"{'–' if sp is None else f'{sp:.5f}'} |")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run-dir", default=str(REPO / RUN_DIR))
    ap.add_argument("--out", default=str(REPO / DEFAULT_OUT))
    ap.add_argument("--draws", type=int, default=DRAWS)
    ap.add_argument("--seed", type=int, default=SEED)
    a = ap.parse_args(argv)
    res = run(Path(a.run_dir), Path(a.out), draws=a.draws, seed=a.seed, pinned_noise=REPO / PINNED_NOISE)
    print(json.dumps({"nodes": list(res["nodes"]), "not_determined": list(res["not_determined"]),
                      "out": a.out}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
