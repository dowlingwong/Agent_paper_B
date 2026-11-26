#!/usr/bin/env python3
"""Tables for the common 30-seed E1 run over ten nodes, 22 Oct 2026 (PILOT; AI-assisted, Claude).

PLAN §10, rows "D21 rule (22 Oct)", "D21 uniform application (22 Oct)", "D21 pool (22 Oct)" and
"D21 common measurement (22 Oct)"; D18 for delta_n.

Reads only run data (runs.jsonl / edits.json / manifest.json) of this run, of the 12 Oct E1 and of
the 22 Oct credit_approval/diabetes re-measurement, and reuses r1.noise.e1_report.summarise unchanged
for every per-node and per-edit statistic. The adopted D21 rule is applied here (function d21_adopted),
not e1_report's "proposal" labels: e1_report's third label "more seeds needed" is not part of the
adopted rule, and e1_report does not check the fixed seed count of 30.

Usage (from the paper repo root):
  python results/r1/pilot/E1_<UTC>/make_tables.py results/r1/pilot/E1_<UTC>
Writes compare.json and compare_tables.md into the run directory. Output holds no absolute or
temporary paths, so a re-run is byte-identical.
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

PILOT = ROOT / "results" / "r1" / "pilot"
E1_DIR = PILOT / "E1_20261012T145353Z"                 # original E1, 10 seeds, Python 3.11.16, sklearn not recorded
REM_DIR = PILOT / "E1_remeasure_20261022T100942Z"      # 22 Oct re-measurement, 30 seeds, sklearn 1.9.1
NODES = ["digits_mlp", "tabular_mlp", "openml_breast_w", "openml_ionosphere", "openml_wdbc",
         "openml_credit_approval", "openml_credit_g", "openml_sonar", "openml_blood_transfusion", "openml_qsar_biodeg"]
E1_COVERED = ["digits_mlp", "tabular_mlp", "openml_breast_w", "openml_ionosphere", "openml_wdbc", "openml_credit_approval"]
REM_NODE = "openml_credit_approval"
N_SEEDS_RULE = 30                                      # PLAN: "30 seeds per condition", fixed for every node
POOL_TARGET = 8                                        # PLAN D21 / Node pool: at least 8 qualifying nodes
SEED_BASE = {"train": 1001, "split": 2001, "joint": 3001}
B_BOOT = 2000


def delta_n(median_sd: float) -> float:
    """D18: delta_n = max(0.002, 0.25 x median paired sd(Delta-hat))."""
    return max(0.002, 0.25 * median_sd) if not math.isnan(median_sd) else float("nan")


def load(run_dir: Path) -> list[dict]:
    return [json.loads(l) for l in (run_dir / "runs.jsonl").read_text().splitlines() if l.strip()]


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
            i = seed_index(json.loads(line))
            if i is None or keep(i):
                fh.write(line + "\n")
    return d


def seed_counts(rows, node, n_cfg) -> dict[str, int]:
    """Minimum, over configs c0..c_n, of the number of successful seeds per condition."""
    c = defaultdict(set)
    for r in rows:
        if r["node"] == node and r["success"] and r["metric"] is not None and r["condition"] in SEED_BASE:
            c[(r["config"], r["condition"])].add((r["train_seed"], r["split_seed"]))
    return {cond: min(len(c[(f"c{k}", cond)]) for k in range(n_cfg + 1)) for cond in SEED_BASE}


def d21_adopted(info: dict, counts: dict[str, int]) -> dict:
    """PLAN §10 "D21 rule (22 Oct)", applied as written.

    Noise node iff (30 seeds per condition) and (>= 2 material edits: resolved |D| > 2 se and |D| >= 0.002)
    and (mean plug-in P(wrong) over those edits >= 0.10) and (sigma_joint > 0). Two outcomes only.
    """
    s = info["summary"]
    seeds_ok = all(counts[c] == N_SEEDS_RULE for c in SEED_BASE)
    crit = {
        "seeds_30_per_condition": seeds_ok,
        "n_material_ge_2": s["n_material"] >= MIN_EDITS,
        "mean_p_wrong_ge_0.10": (not math.isnan(s["mean_p_model_material"])) and s["mean_p_model_material"] >= QUALIFY_P,
        "sigma_joint_gt_0": info["sigma_joint"] > 0,
    }
    return {"qualifies": all(crit.values()), "criteria": crit}


def sd_ci(sd: float, n: int) -> tuple[float, float]:
    """95 % chi-square interval for a Gaussian sd from n draws."""
    if n < 2 or math.isnan(sd):
        return (float("nan"), float("nan"))
    return (sd * math.sqrt((n - 1) / stats.chi2.ppf(0.975, n - 1)), sd * math.sqrt((n - 1) / stats.chi2.ppf(0.025, n - 1)))


def joint_D(rows, node: str, n_cfg: int) -> np.ndarray:
    """Paired joint differences D[edit, seed] = m(c_k, s) - m(c0, s), seeds common to all configs."""
    by = defaultdict(dict)
    for r in rows:
        if r["node"] == node and r["success"] and r["metric"] is not None and r["condition"] == "joint":
            by[r["config"]][r["train_seed"]] = float(r["metric"])
    seeds = sorted(set.intersection(*(set(by[f"c{k}"]) for k in range(n_cfg + 1))))
    M = np.array([[by[f"c{k}"][s] for s in seeds] for k in range(n_cfg + 1)])
    return M[1:] - M[0], M[0]


def rule_from_d(D: np.ndarray, base: np.ndarray) -> tuple[bool, int, float]:
    """Independent re-implementation of the adopted rule's effect criteria on joint differences."""
    n = D.shape[1]
    ps = []
    for d in D:
        delta, sd = d.mean(), d.std(ddof=1)
        se = sd / math.sqrt(n)
        resolved = abs(delta) > 2 * se if se > 0 else delta != 0
        if resolved and abs(delta) >= MIN_EFFECT:
            ps.append(_phi(-abs(delta) / sd) if sd > 0 else 0.0)
    mean_p = float(np.mean(ps)) if ps else float("nan")
    return (len(ps) >= MIN_EDITS and mean_p >= QUALIFY_P and base.std(ddof=1) > 0), len(ps), mean_p


def bootstrap(rows, node: str, n_edits: int, rng) -> dict:
    """Joint seeds resampled with replacement, paired across configs. Reported, not decisive (PLAN)."""
    D, base = joint_D(rows, node, n_edits)
    n = D.shape[1]
    q, nm, mp = [], [], []
    for _ in range(B_BOOT):
        idx = rng.integers(0, n, n)
        ok, k, p = rule_from_d(D[:, idx], base[idx])
        q.append(ok); nm.append(k); mp.append(p)
    mp = np.array(mp)
    fin = mp[~np.isnan(mp)]
    return {"n_seeds": n, "B": B_BOOT, "p_qualifies": float(np.mean(q)),
            "n_material_dist": {str(k): float(np.mean(np.array(nm) == k)) for k in range(n_edits + 1)},
            "mean_p_wrong_q05_q50_q95": [float(np.quantile(fin, x)) for x in (0.05, 0.5, 0.95)] if fin.size else None}


def reproducibility(old_rows, new_rows, nodes) -> dict:
    key = lambda r: (r["node"], r["config"], r["condition"], r["train_seed"], r["split_seed"])
    O = {key(r): r["metric"] for r in old_rows if r["node"] in nodes}
    out = defaultdict(lambda: {"identical": 0, "different": 0})
    for r in new_rows:
        k = key(r)
        if k in O:
            out[f"{r['node']}:{r['config']}"]["identical" if O[k] == r["metric"] else "different"] += 1
    return {k: out[k] for k in sorted(out)}


def f(x, nd=4):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    if isinstance(x, bool):
        return "yes" if x else "no"
    return f"{x:.{nd}f}"


def ci(sd, n):
    lo, hi = sd_ci(sd, n)
    return f"{f(sd)} [{f(lo)}, {f(hi)}]"


def main() -> int:
    run_dir = Path(sys.argv[1]).resolve()
    rng = np.random.default_rng(20261022)
    rows = load(run_dir)
    e1_rows, rem_rows = load(E1_DIR), load(REM_DIR)
    edits = json.loads((run_dir / "edits.json").read_text())
    manifest = json.loads((run_dir / "manifest.json").read_text())
    assert manifest["nodes"] == NODES and int(manifest["seeds_per_condition"]) == N_SEEDS_RULE

    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        new30 = summarise(run_dir)
        first10 = summarise(subset_dir(run_dir, lambda i: i < 10, tmp, "first10"))
        last20 = summarise(subset_dir(run_dir, lambda i: i >= 10, tmp, "last20"))
    e1 = summarise(E1_DIR)
    rem = summarise(REM_DIR)
    prov = {"common_30": run_dir.name, "common_seeds_1_10": f"{run_dir.name} (seed indices 0–9)",
            "common_seeds_11_30": f"{run_dir.name} (seed indices 10–29)", "E1_12oct": E1_DIR.name, "remeasure_22oct": REM_DIR.name}
    S = {"common_30": new30, "common_seeds_1_10": first10, "common_seeds_11_30": last20, "E1_12oct": e1, "remeasure_22oct": rem}
    for k, v in S.items():
        v["run_dir"] = prov[k]

    counts = {n: seed_counts(rows, n, len(edits[n])) for n in NODES}
    verdict = {n: d21_adopted(new30["nodes"][n], counts[n]) for n in NODES}
    recompute = {n: rule_from_d(*joint_D(rows, n, len(edits[n]))) for n in NODES}
    boot = {n: bootstrap(rows, n, len(edits[n]), rng) for n in NODES}
    dn = {n: delta_n(new30["nodes"][n]["summary"]["median_sd_joint"]) for n in NODES}
    lab = lambda q: "**qualifies**" if q else "does not qualify"

    md = []
    # ---------------------------------------------------------------- Table 1
    md += ["### Table 1 — C1 noise-floor table: ten nodes, 30 seeds per condition, adopted D21 rule", "",
           "| Node | seeds train/split/joint | default m | σ_train [95 % CI] | σ_split [95 % CI] | σ_joint [95 % CI] | median sd(Δ̂) | δ_n (D18) | "
           "material / resolved / all | mean P(wrong), material | regret share | campaign-seed wrong | split policy (E1 rule) | "
           "**D21 verdict (adopted rule)** | bootstrap P(qualifies) (not decisive) |",
           "|" + "---|" * 15]
    for n in NODES:
        info, s, c = new30["nodes"][n], new30["nodes"][n]["summary"], counts[n]
        md.append(f"| `{n}` | {c['train']}/{c['split']}/{c['joint']} | {f(info['default_metric'])} | {ci(info['sigma_train'], c['train'])} | "
                  f"{ci(info['sigma_split'], c['split'])} | {ci(info['sigma_joint'], c['joint'])} | {f(s['median_sd_joint'])} | {f(dn[n])} | "
                  f"{s['n_material']} / {s['n_resolved']} / {s['n_edits']} | {f(s['mean_p_model_material'], 3)} | {f(s['regret_share_material'], 2)} | "
                  f"{s['campaign_wrong']}/{s['n_resolved']} | `{info['proposal']['split_policy']}` | {lab(verdict[n]['qualifies'])} | "
                  f"{f(boot[n]['p_qualifies'], 2)} |")
    md += ["", "σ: sd of the baseline c0 metric over the 30 seeds of one condition; CI is the Gaussian chi-square interval. "
           "δ_n = max(0.002, 0.25 × median over all five edits of the joint paired sd(Δ̂)). "
           "Mean P(wrong) is shown to three decimals because two nodes sit within 0.004 of the 0.10 threshold. "
           f"P(wrong) selection cap at n = 30: Φ(−2/√30) = {f(_phi(-2 / math.sqrt(30)), 2)}.", ""]

    # ---------------------------------------------------------------- Table 2
    md += ["### Table 2 — the adopted rule, criterion by criterion, and an independent recomputation", "",
           "| Node | 30 seeds per condition | ≥ 2 material edits | mean P(wrong) ≥ 0.10 | σ_joint > 0 | verdict | "
           "recomputed from raw joint differences (#material, mean P(wrong), verdict) | e1_report label |",
           "|---|---|---|---|---|---|---|---|"]
    for n in NODES:
        cr, info = verdict[n]["criteria"], new30["nodes"][n]
        ok, k, p = recompute[n]
        e1lab = "qualifies" if info["proposal"]["qualifies_D21"] else ("more seeds needed" if info["proposal"]["needs_more_seeds"] else "does not qualify")
        md.append(f"| `{n}` | {f(cr['seeds_30_per_condition'])} | {f(cr['n_material_ge_2'])} | {f(cr['mean_p_wrong_ge_0.10'])} | "
                  f"{f(cr['sigma_joint_gt_0'])} | {lab(verdict[n]['qualifies'])} | {k}, {f(p, 3)}, {'qualifies' if ok else 'does not qualify'} | {e1lab} |")
    md.append("")

    # ---------------------------------------------------------------- Table 3
    md += ["### Table 3 — seed-bootstrap of the rule's outcome (joint seeds resampled, paired across configs; reported, not decisive)", "",
           "| Node | seeds | P(qualifies) | P(#material = 0 / 1 / 2 / 3+) | mean P(wrong) over material, 5 / 50 / 95 % |", "|---|---|---|---|---|"]
    for n in NODES:
        b = boot[n]; dist = b["n_material_dist"]; q = b["mean_p_wrong_q05_q50_q95"]
        three = sum(v for k, v in dist.items() if int(k) >= 3)
        md.append(f"| `{n}` | {b['n_seeds']} | {f(b['p_qualifies'], 2)} | {f(dist['0'], 2)} / {f(dist['1'], 2)} / {f(dist['2'], 2)} / {f(three, 2)} | "
                  f"{' / '.join(f(x, 2) for x in q) if q else '–'} |")
    md += ["", f"B = {B_BOOT} resamples, numpy default_rng(20261022). The bootstrap applies the rule's effect criteria and σ_joint > 0 to each resample.", ""]

    # ---------------------------------------------------------------- Table 4
    md += ["### Table 4 — per-edit rows (30 seeds), with the 12 Oct E1 (10 seeds) where it measured the node", "",
           "| Node | Edit | Δ̂_J ± 2se | material | sd(Δ̂) joint | sd train | sd split | ϱ_joint | P(wrong) | regret \\|Δ̂\\|·P | "
           "12 Oct: Δ̂_J ± 2se | 12 Oct: sd(Δ̂) joint | 12 Oct: P(wrong) | 12 Oct: material |",
           "|" + "---|" * 14]
    for n in NODES:
        old = e1["nodes"].get(n) if n in E1_COVERED else None
        for i, b in enumerate(new30["nodes"][n]["edits"]):
            a = old["edits"][i] if old else None
            assert a is None or a["edit"] == b["edit"]
            olds = (f"{f(a['delta_hat_J'])} ± {f(2 * a['se'])} | {f(a['sd_joint'])} | {f(a['p_model'], 2)} | {f(a['material'])}"
                    if a else "– | – | – | –")
            md.append(f"| `{n}` | {b['edit']} | {f(b['delta_hat_J'])} ± {f(2 * b['se'])} | {f(b['material'])} | {f(b['sd_joint'])} | "
                      f"{f(b['sd_train'])} | {f(b['sd_split'])} | {f(b.get('rho_joint'), 2)} | {f(b['p_model'], 2)} | {f(b['decision_regret'])} | {olds} |")
    md.append("")

    # ---------------------------------------------------------------- Table 5
    md += ["### Table 5 — node level: 12 Oct E1 (10 seeds) vs. this run, for the six nodes E1 measured", "",
           "| Node | data | seeds | σ_train | σ_split | σ_joint | median sd(Δ̂) | δ_n | material / resolved / all | mean P(wrong), material | "
           "effect criteria of the rule met (at the n shown) |", "|" + "---|" * 11]
    rowsets = [("12 Oct E1 (Py 3.11, sklearn unrecorded)", e1, 10), ("this run, seeds 1–10 (= E1's seeds)", first10, 10),
               ("this run, seeds 11–30 (independent)", last20, 20), ("this run, all 30 seeds", new30, 30)]
    for n in E1_COVERED:
        for label, summ, k in rowsets:
            info = summ["nodes"][n]; s = info["summary"]
            crit = s["n_material"] >= MIN_EDITS and not math.isnan(s["mean_p_model_material"]) and s["mean_p_model_material"] >= QUALIFY_P and info["sigma_joint"] > 0
            md.append(f"| `{n}` | {label} | {k} | {f(info['sigma_train'])} | {f(info['sigma_split'])} | {f(info['sigma_joint'])} | "
                      f"{f(s['median_sd_joint'])} | {f(delta_n(s['median_sd_joint']))} | {s['n_material']} / {s['n_resolved']} / {s['n_edits']} | "
                      f"{f(s['mean_p_model_material'], 3)} | {f(crit)} |")
    md += ["", "Only the 30-seed row is a verdict under the adopted rule; the 10- and 20-seed rows show the same criteria at other n for comparison.", ""]

    # ---------------------------------------------------------------- Table 6
    md += ["### Table 6 — `openml_credit_approval`: 22 Oct re-measurement (sklearn 1.9.1) vs. this run (sklearn 1.8.0), same 30 seeds", "",
           "| data | σ_split | σ_joint | median sd(Δ̂) | material / resolved / all | mean P(wrong), material | effect criteria met |",
           "|---|---|---|---|---|---|---|"]
    for label, summ in [("22 Oct re-measurement (venv313: sklearn 1.9.1, numpy 2.5.4)", rem), ("this run (hvenv: sklearn 1.8.0, numpy 2.4.4)", new30)]:
        info = summ["nodes"][REM_NODE]; s = info["summary"]
        crit = s["n_material"] >= MIN_EDITS and not math.isnan(s["mean_p_model_material"]) and s["mean_p_model_material"] >= QUALIFY_P and info["sigma_joint"] > 0
        md.append(f"| {label} | {f(info['sigma_split'])} | {f(info['sigma_joint'])} | {f(s['median_sd_joint'])} | "
                  f"{s['n_material']} / {s['n_resolved']} / {s['n_edits']} | {f(s['mean_p_model_material'], 3)} | {f(crit)} |")
    md += ["", "| Edit | Δ̂_J ± 2se, 22 Oct | Δ̂_J ± 2se, this run | sd(Δ̂) joint, 22 Oct → this run | P(wrong), 22 Oct → this run | material, 22 Oct → this run |",
           "|---|---|---|---|---|---|"]
    for a, b in zip(rem["nodes"][REM_NODE]["edits"], new30["nodes"][REM_NODE]["edits"]):
        assert a["edit"] == b["edit"]
        md.append(f"| {b['edit']} | {f(a['delta_hat_J'])} ± {f(2 * a['se'])} | {f(b['delta_hat_J'])} ± {f(2 * b['se'])} | "
                  f"{f(a['sd_joint'])} → {f(b['sd_joint'])} | {f(a['p_model'], 2)} → {f(b['p_model'], 2)} | {f(a['material'])} → {f(b['material'])} |")
    md.append("")

    # ---------------------------------------------------------------- Table 7
    rep_e1 = reproducibility(e1_rows, rows, E1_COVERED)
    rep_rem = reproducibility(rem_rows, rows, [REM_NODE])
    md += ["### Table 7 — bit-reproducibility of earlier runs at identical node, config, condition and seeds", "",
           "c0–c2 and c5 are the logistic-regression / small-edit configs on OpenML nodes; c3 = random forest, c4 = gradient boosting.", "",
           "| Node:config | vs 12 Oct E1: identical | different | vs 22 Oct re-measurement: identical | different |", "|---|---|---|---|---|"]
    for k in sorted(set(rep_e1) | set(rep_rem)):
        a, b = rep_e1.get(k), rep_rem.get(k)
        md.append(f"| `{k}` | {a['identical'] if a else '–'} | {a['different'] if a else '–'} | {b['identical'] if b else '–'} | {b['different'] if b else '–'} |")
    md.append("")

    # ---------------------------------------------------------------- Table 8
    pool = [n for n in NODES if verdict[n]["qualifies"]]
    md += ["### Table 8 — noise-node pool under the adopted rule", "",
           "| | nodes | count |", "|---|---|---|",
           f"| qualify | {', '.join(f'`{n}`' for n in pool)} | {len(pool)} |",
           f"| do not qualify | {', '.join(f'`{n}`' for n in NODES if n not in pool) or '–'} | {len(NODES) - len(pool)} |",
           f"| PLAN target | ≥ {POOL_TARGET} | {'met' if len(pool) >= POOL_TARGET else 'not met'} |", ""]

    out = {"label": "PILOT", "ai_assisted": "Claude", "run_dir": str(run_dir.relative_to(ROOT)),
           "rule": {"source": "PLAN §10 'D21 rule (22 Oct)'", "N_SEEDS": N_SEEDS_RULE, "MIN_EDITS": MIN_EDITS,
                    "MIN_EFFECT": MIN_EFFECT, "QUALIFY_P": QUALIFY_P, "sigma_joint_gt_0": True},
           "libraries": manifest["host"]["libraries"], "python": manifest["host"]["python"],
           "seed_counts": counts, "verdict_adopted_rule": verdict,
           "recomputed": {n: {"qualifies": r[0], "n_material": r[1], "mean_p_wrong": r[2]} for n, r in recompute.items()},
           "bootstrap": boot, "delta_n": dn, "pool": {"qualifying": pool, "count": len(pool), "target": POOL_TARGET},
           "reproducibility_vs_E1_12oct": rep_e1, "reproducibility_vs_remeasure_22oct": rep_rem, "summaries": S}
    (run_dir / "compare.json").write_text(json.dumps(out, indent=2, default=str) + "\n")
    (run_dir / "compare_tables.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
