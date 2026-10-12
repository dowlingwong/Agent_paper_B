#!/usr/bin/env python3
"""Summarise an E1 noise-floor run (RUNBOOK 0.4). Output is PILOT, never a result.

Per node and edit k (c_k vs the baseline c0), with paired seeds:

- ``d_s = m(c_k, s) - m(c0, s)`` under each seed condition (train / split / joint);
- ``delta_hat_J``: mean of the joint-condition d_s, the estimate of
  J(c_k) - J(c0); ``se`` is its standard error;
- ``sd_joint`` / ``sd_train`` / ``sd_split``: sd of d_s per condition, i.e. the
  noise of one paired comparison (sigma_Delta in T1);
- ``rho_joint``: correlation of m(c0, s) and m(c_k, s) over joint seeds;
- ``p_model = Phi(-|delta_hat_J| / sd_joint)``: the Gaussian error rate of the
  default keep rule for this edit (T1 H1);
- ``flip_emp``: share of joint seeds whose single-comparison sign disagrees
  with sign(delta_hat_J); only for *resolved* edits (|delta_hat_J| > 2 se);
- ``campaign_wrong``: whether the decision at the node's default seeds (the
  one a campaign actually makes) disagrees with sign(delta_hat_J), resolved
  edits only.

Usage: python -m r1.noise.e1_report results/r1/pilot/E1_<stamp> [--md docs/r1/reports/NOISE_FLOOR_<date>.md]
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

QUALIFY_P = 0.10          # proposed D21 rule: mean error rate of the default rule >= 10 % ...
MIN_EFFECT = 0.002        # ... over resolved edits with |Delta_J| >= 0.002 (metric units) ...
MIN_EDITS = 2             # ... and at least two such edits
VARY_RATIO = 0.5          # proposed: use "vary" when sd_train < 0.5 sd_joint (median over material edits)


def _phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _sd(x) -> float:
    x = np.asarray(x, dtype=float)
    return float(np.std(x, ddof=1)) if x.size > 1 else float("nan")


def summarise(run_dir: Path) -> dict:
    rows = [json.loads(line) for line in (run_dir / "runs.jsonl").read_text().splitlines() if line.strip()]
    edits = json.loads((run_dir / "edits.json").read_text())
    by = defaultdict(dict)  # (node, config, condition) -> seedkey -> metric
    wall = defaultdict(list)
    failures = defaultdict(int)
    for r in rows:
        if not r.get("success") or r.get("metric") is None:
            failures[r["node"]] += 1
            continue
        key = (r.get("train_seed"), r.get("split_seed"))
        by[(r["node"], r["config"], r["condition"])][key] = float(r["metric"])
        wall[r["node"]].append(float(r.get("wall_seconds") or 0.0))

    nodes = {}
    for node, node_edits in edits.items():
        base = {c: by.get((node, "c0", c), {}) for c in ("default", "default_repeat", "train", "split", "joint")}
        if not base["default"]:
            continue
        configs = ["c0"] + [f"c{k}" for k in range(1, len(node_edits) + 1)]
        deterministic = all(
            by.get((node, c, "default"), {}).get((None, None)) == by.get((node, c, "default_repeat"), {}).get((None, None))
            for c in configs if by.get((node, c, "default"))
        )
        info = {
            "default_metric": base["default"].get((None, None)),
            "deterministic_at_fixed_seed": deterministic,
            "sigma_train": _sd(list(base["train"].values())),
            "sigma_split": _sd(list(base["split"].values())),
            "sigma_joint": _sd(list(base["joint"].values())),
            "mean_joint": float(np.mean(list(base["joint"].values()))) if base["joint"] else float("nan"),
            "median_wall_seconds": float(np.median(wall[node])) if wall[node] else float("nan"),
            "failed_runs": failures[node],
            "edits": [],
        }
        for k, edit in enumerate(node_edits, start=1):
            cfg = f"c{k}"
            e = {"edit": f"{edit['symbol']} {edit['old']} -> {edit['new']}"}
            d = {}
            for cond in ("train", "split", "joint"):
                a, b = by.get((node, "c0", cond), {}), by.get((node, cfg, cond), {})
                seeds = sorted(set(a) & set(b), key=str)
                d[cond] = np.array([b[s] - a[s] for s in seeds])
                if cond == "joint" and len(seeds) > 2:
                    xa, xb = np.array([a[s] for s in seeds]), np.array([b[s] for s in seeds])
                    e["rho_joint"] = float(np.corrcoef(xa, xb)[0, 1]) if np.std(xa) > 0 and np.std(xb) > 0 else float("nan")
            dj = d["joint"]
            if dj.size < 3:
                e["status"] = "insufficient runs"
                info["edits"].append(e)
                continue
            delta = float(dj.mean())
            se = _sd(dj) / math.sqrt(dj.size)
            sd_joint = _sd(dj)
            e.update({
                "delta_hat_J": delta, "se": se, "sd_joint": sd_joint,
                "sd_train": _sd(d["train"]), "sd_split": _sd(d["split"]),
                "resolved": bool(abs(delta) > 2 * se) if se > 0 else bool(delta != 0),
                "p_model": _phi(-abs(delta) / sd_joint) if sd_joint > 0 else (0.0 if delta != 0 else float("nan")),
            })
            # expected loss of one default-rule decision, in metric units: |Delta| * P(wrong)
            e["decision_regret"] = abs(delta) * e["p_model"] if not math.isnan(e["p_model"]) else float("nan")
            e["material"] = bool(e["resolved"] and abs(delta) >= MIN_EFFECT)
            if e["resolved"] and delta != 0:
                signs = np.sign(dj)
                e["flip_emp"] = float(np.mean(signs != np.sign(delta)))
                camp_c = by.get((node, cfg, "default"), {}).get((None, None))
                camp_0 = base["default"].get((None, None))
                if camp_c is not None and camp_0 is not None:
                    e["campaign_delta_hat"] = camp_c - camp_0
                    e["campaign_wrong"] = bool(np.sign(camp_c - camp_0) != np.sign(delta))
            info["edits"].append(e)

        resolved = [e for e in info["edits"] if e.get("resolved")]
        material = [e for e in info["edits"] if e.get("material")]
        flips = [e["flip_emp"] for e in resolved if "flip_emp" in e]
        sdj = [e["sd_joint"] for e in info["edits"] if "sd_joint" in e]
        ratio = [e["sd_train"] / e["sd_joint"] for e in material if e["sd_joint"] > 0 and not math.isnan(e["sd_train"])]
        if not ratio and info["sigma_joint"] > 0:  # no material edit: fall back to the baseline's own noise split
            ratio = [info["sigma_train"] / info["sigma_joint"]]
        unresolved_noisy = [e for e in info["edits"] if "sd_joint" in e and not e["resolved"] and e["sd_joint"] >= MIN_EFFECT]
        info["summary"] = {
            "n_edits": len(info["edits"]),
            "n_resolved": len(resolved),
            "n_material": len(material),
            "n_unresolved_noisy": len(unresolved_noisy),
            "median_sd_joint": float(np.median(sdj)) if sdj else float("nan"),
            "mean_flip_emp_resolved": float(np.mean(flips)) if flips else float("nan"),
            "mean_p_model_material": float(np.mean([e["p_model"] for e in material])) if material else float("nan"),
            "regret_share_material": (float(sum(e["decision_regret"] for e in material) / sum(abs(e["delta_hat_J"]) for e in material))
                                       if material else float("nan")),
            "campaign_wrong": sum(1 for e in resolved if e.get("campaign_wrong")),
            "median_train_to_joint_ratio": float(np.median(ratio)) if ratio else float("nan"),
        }
        s_ = info["summary"]
        qualifies = (s_["n_material"] >= MIN_EDITS and s_["mean_p_model_material"] >= QUALIFY_P and info["sigma_joint"] > 0)
        info["proposal"] = {
            "qualifies_D21": bool(qualifies),
            "needs_more_seeds": bool(not qualifies and s_["n_unresolved_noisy"] >= 1),
            "split_policy": ("vary" if (not math.isnan(s_["median_train_to_joint_ratio"]) and s_["median_train_to_joint_ratio"] < VARY_RATIO) else "fixed"),
        }
        nodes[node] = info
    return {"label": "PILOT", "run_dir": str(run_dir), "rules": {"QUALIFY_P": QUALIFY_P, "MIN_EFFECT": MIN_EFFECT, "MIN_EDITS": MIN_EDITS,
            "VARY_RATIO": VARY_RATIO}, "nodes": nodes}


def _f(x, nd=4) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    if isinstance(x, bool):
        return "yes" if x else "no"
    return f"{x:.{nd}f}"


def markdown(summary: dict, manifest: dict) -> str:
    out = []
    out.append("| Node | default m | bit-identical at fixed seed | σ_train | σ_split | σ_joint | median sd(Δ̂) | material / resolved / all edits | mean P(wrong), material | regret share, material | campaign-seed decision wrong | sd_train/sd_joint, material | median s/run | D21 (proposed) | split policy (proposed) |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for node, info in summary["nodes"].items():
        s = info["summary"]
        verdict = "qualifies" if info["proposal"]["qualifies_D21"] else ("more seeds needed" if info["proposal"]["needs_more_seeds"] else "does not qualify")
        out.append(
            f"| `{node}` | {_f(info['default_metric'])} | {_f(info['deterministic_at_fixed_seed'])} | {_f(info['sigma_train'])} | "
            f"{_f(info['sigma_split'])} | {_f(info['sigma_joint'])} | {_f(s['median_sd_joint'])} | "
            f"{s['n_material']} / {s['n_resolved']} / {s['n_edits']} | {_f(s['mean_p_model_material'], 2)} | {_f(s['regret_share_material'], 2)} | "
            f"{s['campaign_wrong']}/{s['n_resolved']} | {_f(s['median_train_to_joint_ratio'], 2)} | {_f(info['median_wall_seconds'], 1)} | "
            f"{verdict} | `{info['proposal']['split_policy']}` |")
    out.append("")
    out.append("### Per-edit rows")
    out.append("")
    out.append("| Node | Edit | Δ̂_J (± 2 se) | material | ϱ_joint | sd(Δ̂) joint | sd train | sd split | P(wrong) | flip rate | campaign Δ̂ | campaign wrong |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for node, info in summary["nodes"].items():
        for e in info["edits"]:
            if "delta_hat_J" not in e:
                out.append(f"| `{node}` | {e['edit']} | {e.get('status','–')} | | | | | | | | | |")
                continue
            out.append(
                f"| `{node}` | {e['edit']} | {_f(e['delta_hat_J'])} ± {_f(2*e['se'])} | {_f(e['material'])} | {_f(e.get('rho_joint'), 2)} | {_f(e['sd_joint'])} | "
                f"{_f(e['sd_train'])} | {_f(e['sd_split'])} | {_f(e['p_model'], 2)} | {_f(e.get('flip_emp'), 2)} | "
                f"{_f(e.get('campaign_delta_hat'))} | {_f(e.get('campaign_wrong')) if 'campaign_wrong' in e else '–'} |")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run_dir")
    parser.add_argument("--md", default=None, help="Write the generated tables to this markdown file.")
    args = parser.parse_args()
    run_dir = Path(args.run_dir)
    summary = summarise(run_dir)
    manifest = json.loads((run_dir / "manifest.json").read_text())
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    tables = markdown(summary, manifest)
    (run_dir / "tables.md").write_text(tables + "\n")
    if args.md:
        Path(args.md).write_text(tables + "\n")
    print(tables)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
