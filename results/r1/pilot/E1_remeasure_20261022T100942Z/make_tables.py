#!/usr/bin/env python3
"""Comparison tables for the 22 Oct 30-seed noise re-measurement (PILOT; AI-assisted, Claude).

Reads only run data (runs.jsonl / edits.json) and reuses r1.noise.e1_report.summarise
unchanged, so every rule (material edit, P(wrong), proposed D21 rule) is E1's.

Usage (from the paper repo root):
  python results/r1/pilot/E1_remeasure_<UTC>/make_tables.py results/r1/pilot/E1_remeasure_<UTC>
Writes compare.json and compare_tables.md into the run directory.
"""
from __future__ import annotations

import json
import math
import shutil
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from r1.noise.e1_report import MIN_EDITS, MIN_EFFECT, QUALIFY_P, _phi, summarise  # noqa: E402

E1_DIR = ROOT / "results" / "r1" / "pilot" / "E1_20261012T145353Z"
D21_NODES = ["digits_mlp", "tabular_mlp", "openml_breast_w", "openml_ionosphere", "openml_wdbc"]
NEW_NODES = ["openml_credit_approval", "openml_diabetes"]
SEED_BASE = {"train": 1001, "split": 2001, "joint": 3001}
B_BOOT = 2000


def delta_n(median_sd: float) -> float:
    """D18: delta_n = max(0.002, 0.25 x median paired sd(Delta-hat))."""
    return max(0.002, 0.25 * median_sd) if not math.isnan(median_sd) else float("nan")


def seed_index(row) -> int | None:
    cond = row["condition"]
    if cond in ("default", "default_repeat"):
        return None
    seed = row["train_seed"] if cond in ("train", "joint") else row["split_seed"]
    return seed - SEED_BASE[cond]


def subset_dir(run_dir: Path, keep, tmp: Path, name: str) -> Path:
    """Copy of the run dir holding only rows whose seed index passes keep() (default rows always kept)."""
    d = tmp / name
    d.mkdir()
    shutil.copy(run_dir / "edits.json", d / "edits.json")
    with open(d / "runs.jsonl", "w") as fh:
        for line in (run_dir / "runs.jsonl").read_text().splitlines():
            row = json.loads(line)
            i = seed_index(row)
            if i is None or keep(i):
                fh.write(line + "\n")
    return d


def sd_ci(sd: float, n: int) -> tuple[float, float]:
    """95 % chi-square interval for a Gaussian sd from n draws."""
    if n < 2 or math.isnan(sd):
        return (float("nan"), float("nan"))
    lo = sd * math.sqrt((n - 1) / stats.chi2.ppf(0.975, n - 1))
    hi = sd * math.sqrt((n - 1) / stats.chi2.ppf(0.025, n - 1))
    return lo, hi


def joint_matrix(run_dir: Path, node: str, n_cfg: int):
    """metric[config, joint seed] for c0..c_n_cfg, plus the default-seed metrics."""
    rows = [json.loads(l) for l in (run_dir / "runs.jsonl").read_text().splitlines() if l.strip()]
    by = defaultdict(dict)
    default = {}
    for r in rows:
        if r["node"] != node or not r["success"] or r["metric"] is None:
            continue
        if r["condition"] == "joint":
            by[r["config"]][r["train_seed"]] = float(r["metric"])
        elif r["condition"] == "default":
            default[r["config"]] = float(r["metric"])
    seeds = sorted(set.intersection(*(set(by[f"c{k}"]) for k in range(n_cfg + 1))))
    return np.array([[by[f"c{k}"][s] for s in seeds] for k in range(n_cfg + 1)]), default


def qualify_from_d(D: np.ndarray) -> tuple[bool, int, float]:
    """E1's proposed D21 rule on paired joint differences D[edit, seed]."""
    n = D.shape[1]
    ps = []
    for d in D:
        delta, sd = d.mean(), d.std(ddof=1)
        se = sd / math.sqrt(n)
        resolved = abs(delta) > 2 * se if se > 0 else delta != 0
        if resolved and abs(delta) >= MIN_EFFECT:
            ps.append(_phi(-abs(delta) / sd) if sd > 0 else 0.0)
    mean_p = float(np.mean(ps)) if ps else float("nan")
    return (len(ps) >= MIN_EDITS and mean_p >= QUALIFY_P), len(ps), mean_p


def bootstrap(run_dir: Path, node: str, n_edits: int, rng) -> dict:
    M, _ = joint_matrix(run_dir, node, n_edits)
    D = M[1:] - M[0]
    n = D.shape[1]
    q, nm, mp = [], [], []
    for _ in range(B_BOOT):
        idx = rng.integers(0, n, n)
        ok, k, p = qualify_from_d(D[:, idx])
        q.append(ok); nm.append(k); mp.append(p)
    mp = np.array(mp)
    fin = mp[~np.isnan(mp)]
    return {
        "n_seeds": n, "B": B_BOOT, "p_qualifies": float(np.mean(q)),
        "n_material_dist": {str(k): float(np.mean(np.array(nm) == k)) for k in range(n_edits + 1)},
        "mean_p_wrong_q05_q50_q95": [float(np.quantile(fin, x)) for x in (0.05, 0.5, 0.95)] if fin.size else None,
    }


def reproducibility(old: Path, new: Path, nodes) -> dict:
    key = lambda r: (r["node"], r["config"], r["condition"], r["train_seed"], r["split_seed"])
    O = {key(r): r["metric"] for r in map(json.loads, (old / "runs.jsonl").read_text().splitlines()) if r["node"] in nodes}
    out = defaultdict(lambda: {"identical": 0, "different": 0})
    for r in map(json.loads, (new / "runs.jsonl").read_text().splitlines()):
        k = key(r)
        if k in O:
            out[f"{r['node']}:{r['config']}"]["identical" if O[k] == r["metric"] else "different"] += 1
    return dict(out)


def f(x, nd=4):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    if isinstance(x, bool):
        return "yes" if x else "no"
    return f"{x:.{nd}f}"


def verdict(info) -> str:
    p = info["proposal"]
    return "qualifies" if p["qualifies_D21"] else ("more seeds needed" if p["needs_more_seeds"] else "does not qualify")


def node_row(label, node, info, n):
    s = info["summary"]
    lo, hi = sd_ci(info["sigma_split"], n)
    return (f"| `{node}` | {label} | {f(info['sigma_train'])} | {f(info['sigma_split'])} [{f(lo)}, {f(hi)}] | {f(info['sigma_joint'])} | "
            f"{f(s['median_sd_joint'])} | {f(delta_n(s['median_sd_joint']))} | {s['n_material']} / {s['n_resolved']} / {s['n_edits']} | "
            f"{f(s['mean_p_model_material'], 2)} | {f(s['regret_share_material'], 2)} | {s['campaign_wrong']}/{s['n_resolved']} | "
            f"{f(s['median_train_to_joint_ratio'], 2)} | {verdict(info)} | `{info['proposal']['split_policy']}` |")


def main() -> int:
    run_dir = Path(sys.argv[1]).resolve()
    rng = np.random.default_rng(20261022)
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        S = {
            "E1 (10 seeds, 12 Oct)": (summarise(E1_DIR), 10),
            "new, seeds 1–10 (= E1 seeds)": (summarise(subset_dir(run_dir, lambda i: i < 10, tmp, "first10")), 10),
            "new, seeds 11–30 (independent)": (summarise(subset_dir(run_dir, lambda i: i >= 10, tmp, "last20")), 20),
            "new, all 30 seeds": (summarise(run_dir), 30),
        }
        # Record machine-independent provenance (no absolute or temporary paths), so re-runs are byte-identical.
        prov = {"E1 (10 seeds, 12 Oct)": E1_DIR.name,
                "new, seeds 1–10 (= E1 seeds)": f"{run_dir.name} (seed indices 0–9)",
                "new, seeds 11–30 (independent)": f"{run_dir.name} (seed indices 10–29)",
                "new, all 30 seeds": run_dir.name}
        for k, (res, _) in S.items():
            if isinstance(res, dict) and "run_dir" in res:
                res["run_dir"] = prov[k]
    edits = json.loads((run_dir / "edits.json").read_text())
    boot = {
        "E1 (10 seeds)": {n: bootstrap(E1_DIR, n, len(edits[n]), rng) for n in NEW_NODES},
        "new (30 seeds)": {n: bootstrap(run_dir, n, len(edits[n]), rng) for n in NEW_NODES},
    }
    e1 = S["E1 (10 seeds, 12 Oct)"][0]
    new30 = S["new, all 30 seeds"][0]

    hdr = ("| Node | data | σ_train | σ_split [95 % CI] | σ_joint | median sd(Δ̂) | δ_n (D18) | material / resolved / all | "
           "mean P(wrong), material | regret share | campaign-seed wrong | sd_train/sd_joint | D21 (E1 rule) | split policy (E1 rule) |")
    sep = "|" + "---|" * 14
    md = ["### Table 1 — re-measured nodes: E1 vs. the 30-seed re-measurement", "", hdr, sep]
    for node in NEW_NODES:
        for label, (summ, n) in S.items():
            md.append(node_row(label, node, summ["nodes"][node], n))
    md += ["", "σ values: sd of the baseline c0 metric over the seeds of one condition; CI is the Gaussian chi-square interval. "
           f"P(wrong) selection cap Φ(−2/√n): n=10 → {f(_phi(-2/math.sqrt(10)),2)}, n=20 → {f(_phi(-2/math.sqrt(20)),2)}, n=30 → {f(_phi(-2/math.sqrt(30)),2)}.", ""]

    md += ["### Table 2 — per-edit, E1 (10 seeds) vs. new (30 seeds)", "",
           "| Node | Edit | Δ̂_J ± 2se, E1 | Δ̂_J ± 2se, 30 | sd(Δ̂) joint, E1 → 30 | sd split, E1 → 30 | sd train, E1 → 30 | P(wrong), E1 → 30 | material, E1 → 30 | regret |Δ̂|·P, 30 |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for node in NEW_NODES:
        for a, b in zip(e1["nodes"][node]["edits"], new30["nodes"][node]["edits"]):
            md.append(f"| `{node}` | {b['edit']} | {f(a['delta_hat_J'])} ± {f(2*a['se'])} | {f(b['delta_hat_J'])} ± {f(2*b['se'])} | "
                      f"{f(a['sd_joint'])} → {f(b['sd_joint'])} | {f(a['sd_split'])} → {f(b['sd_split'])} | {f(a['sd_train'])} → {f(b['sd_train'])} | "
                      f"{f(a['p_model'],2)} → {f(b['p_model'],2)} | {f(a['material'])} → {f(b['material'])} | {f(b['decision_regret'])} |")
    md.append("")

    md += ["### Table 3 — bootstrap stability of the proposed D21 verdict (joint seeds resampled, paired across configs)", "",
           "| Node | data | seeds | P(qualifies) | P(#material = 0/1/2/3+) | mean P(wrong) over material, 5 / 50 / 95 % |", "|---|---|---|---|---|---|"]
    for label, bd in boot.items():
        for node, b in bd.items():
            dist = b["n_material_dist"]
            three = sum(v for k, v in dist.items() if int(k) >= 3)
            q = b["mean_p_wrong_q05_q50_q95"]
            md.append(f"| `{node}` | {label} | {b['n_seeds']} | {f(b['p_qualifies'],2)} | {f(dist['0'],2)} / {f(dist['1'],2)} / {f(dist['2'],2)} / {f(three,2)} | "
                      f"{' / '.join(f(x,2) for x in q) if q else '–'} |")
    md.append("")

    md += ["### Table 4 — side by side with the five D21 nodes (E1, 10 seeds) and δ_n per D18", "",
           "| Node | seeds | σ_train | σ_split | σ_joint | median sd(Δ̂) | δ_n | material / all | mean P(wrong), material | regret share | sd_train/sd_joint | D21 (E1 rule) |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for node, summ, n in [(x, e1, 10) for x in D21_NODES] + [(x, new30, 30) for x in NEW_NODES]:
        info = summ["nodes"][node]; s = info["summary"]
        md.append(f"| `{node}` | {n} | {f(info['sigma_train'])} | {f(info['sigma_split'])} | {f(info['sigma_joint'])} | {f(s['median_sd_joint'])} | "
                  f"{f(delta_n(s['median_sd_joint']))} | {s['n_material']} / {s['n_edits']} | {f(s['mean_p_model_material'],2)} | "
                  f"{f(s['regret_share_material'],2)} | {f(s['median_train_to_joint_ratio'],2)} | {verdict(info)} |")
    md += ["", "δ_n uses D18 as written: median over all of a node's edits of the joint paired sd(Δ̂) (the E1 'median sd(Δ̂)' column).", ""]

    repro = reproducibility(E1_DIR, run_dir, NEW_NODES)
    md += ["### Table 5 — bit-reproducibility of E1's runs (same node, config, condition and seeds)", "",
           "| Node:config | identical | different |", "|---|---|---|"]
    for k in sorted(repro):
        md.append(f"| `{k}` | {repro[k]['identical']} | {repro[k]['different']} |")
    md.append("")

    out = {"label": "PILOT", "ai_assisted": "Claude", "run_dir": str(run_dir.relative_to(ROOT)),
           "summaries": {k: v[0] for k, v in S.items()}, "bootstrap": boot, "reproducibility_vs_E1": repro,
           "delta_n": {node: delta_n(summ["nodes"][node]["summary"]["median_sd_joint"])
                       for node, summ in [(x, e1) for x in D21_NODES] + [(x, new30) for x in NEW_NODES]}}
    (run_dir / "compare.json").write_text(json.dumps(out, indent=2, default=str) + "\n")
    (run_dir / "compare_tables.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
