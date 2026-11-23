#!/usr/bin/env python3
"""The declared test of R1-SCREEN-MEASURE (tier E): computes exactly the pre-declared statistic and refuses anything else.

AI-assisted (Claude, subagent, 23 Nov 2026). DRAFT; not signed; not reviewed.
Pre-declaration: ``docs/r1/authorizations/SCREEN_MEASURE_PREDECLARATION_DRAFT_20261123.md`` §5.

Input: one run directory written by ``r1.noise.screen_measure`` (``manifest.json`` and ``runs.jsonl``). Nothing else
is read except the pinned design inputs (``screen_design.build_design``).

Statistic, per node (no pooling across nodes):
* errors are centred per configuration over the seeds (a no-op inside a correlation; stated for clarity);
* per triple (g, p, c) = (c0, c_i, c_ij), the sample partial correlation corr(c, g | p) over the common seeds;
* a triple is not eligible (fixed on the full sample) if a member has zero spread, if |corr(g, p)| >= 0.999 or
  |corr(p, c)| >= 0.999, or if two members have identical value vectors;
* the node estimate is the equal-weight mean of the partials of its eligible **primary** triples (design:
  p -> c link not near-duplicate);
* interval: 95 % percentile bootstrap over **seeds**, all configurations of the node resampled jointly (every
  triple shares c0 and most share a parent, so triples are not independent; seeds are), B = 2,000, generator seed
  20261123; a resample in which an eligible triple's partial is undefined drops that triple from that resample;
* verdict: SHARED if the interval lies entirely above 0.1, NO_SHARED if entirely below 0.1, otherwise
  INCONCLUSIVE; NOT_TESTED if the node has no eligible primary triple or fewer than 108 complete seeds.
* decision (R1-SCREEN-MEASURE): any decision node SHARED -> propose the seventh D.3a arm of R1-D3-CHOICES (1) before
  the D.3 pre-declaration is signed; otherwise R1-THEORY-RHO (2) is final. Per-node 95 % intervals, no
  multiplicity correction in the decision; a Bonferroni reading (99.375 % intervals, 8 nodes) is reported beside it.

Failures (pre-declared): a configuration with failed or non-finite runs at more than 6 of the 120 seeds is dropped
with its triples (c0 dropped -> NOT_TESTED); otherwise the failing seeds are dropped for the whole node.

Secondary (reported, never decisive): all eligible triples of the node (near-duplicate links included); the
eligible triples split by the realised corr(p, c) < 0.95 / >= 0.95; the seven-node (PRE-WDBC) reading.

Run: ``python -m r1.noise.screen_analysis RUN_DIR --out <json>`` (``--engineering`` for stub or dry-run tables).
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np

from r1.noise import screen_design as sd

SCHEMA_RUN = "r1_screen_measure_run/v1"
SCHEMA_OUT = "r1_screen_measure_analysis/v1"
THRESHOLD = 0.1
LEVEL = 0.95
BONFERRONI_LEVEL = 1 - (1 - LEVEL) / len(sd.T0_NODES)     # 0.99375
NEAR_SINGULAR = 0.999
N_BOOT = 2000
BOOT_SEED = 20261123
MAX_FAILED_SEEDS_PER_CONFIG = 6                          # 5 % of 120
MIN_COMPLETE_SEEDS = 108                                 # 90 % of 120
VERDICTS = ("SHARED", "NO_SHARED", "INCONCLUSIVE", "NOT_TESTED")
ROW_KEYS = frozenset({"node", "config", "condition", "seed", "metric", "success", "failure", "edit_applied",
                      "values_before", "values_after", "wall_seconds"})
_FORBIDDEN_PARTS = ("r1_sealed", "sealed", "label_block", "evaluation_block", "test_block")
_EVIDENCE_MARKERS = ("evidence_completion.json", "evidence_binding.json", "label_block.jsonl",
                     "evaluation_block.jsonl")


class AnalysisRefused(ValueError):
    pass


# ---------------------------------------------------------------------------------------------------- statistics

def triple_partial(g, p, c, near_singular: float = NEAR_SINGULAR) -> tuple[float | None, str]:
    """Sample partial correlation corr(c, g | p) and the reason (``ok`` or why the triple is not eligible)."""
    g, p, c = (np.asarray(x, float) for x in (g, p, c))
    if not (len(g) == len(p) == len(c)) or len(g) < 4:
        return None, "too_few_seeds"
    if not (np.all(np.isfinite(g)) and np.all(np.isfinite(p)) and np.all(np.isfinite(c))):
        return None, "non_finite"
    if np.array_equal(g, p) or np.array_equal(p, c) or np.array_equal(g, c):
        return None, "identical_members"
    m = np.vstack([g, p, c])
    m = m - m.mean(axis=1, keepdims=True)                 # per-configuration centring
    norms = np.sqrt((m * m).sum(axis=1))
    if np.any(norms <= 0):
        return None, "zero_spread"
    r = (m @ m.T) / np.outer(norms, norms)
    r_gp, r_pc, r_gc = r[0, 1], r[1, 2], r[0, 2]
    if abs(r_gp) >= near_singular or abs(r_pc) >= near_singular:
        return None, "near_singular"
    return float((r_gc - r_gp * r_pc) / math.sqrt((1 - r_gp ** 2) * (1 - r_pc ** 2))), "ok"


def _corr_matrix(x: np.ndarray) -> np.ndarray:
    x = x - x.mean(axis=1, keepdims=True)
    n = np.sqrt((x * x).sum(axis=1))
    with np.errstate(invalid="ignore", divide="ignore"):
        return (x @ x.T) / np.outer(n, n)


def _partials_from_corr(r: np.ndarray, idx: np.ndarray) -> np.ndarray:
    """idx: T x 3 rows (g, p, c) into r; NaN where undefined or near-singular."""
    gp, pc, gc = r[idx[:, 0], idx[:, 1]], r[idx[:, 1], idx[:, 2]], r[idx[:, 0], idx[:, 2]]
    with np.errstate(invalid="ignore", divide="ignore"):
        out = (gc - gp * pc) / np.sqrt((1 - gp ** 2) * (1 - pc ** 2))
    bad = ~np.isfinite(out) | (np.abs(gp) >= NEAR_SINGULAR) | (np.abs(pc) >= NEAR_SINGULAR)
    out[bad] = np.nan
    return out


def decide(lo: float, hi: float, threshold: float = THRESHOLD) -> str:
    if not (math.isfinite(lo) and math.isfinite(hi)):
        return "INCONCLUSIVE"
    if lo > threshold:
        return "SHARED"
    if hi < threshold:
        return "NO_SHARED"
    return "INCONCLUSIVE"


def seed_bootstrap(matrix: np.ndarray, idx: np.ndarray, n_boot: int = N_BOOT, seed: int = BOOT_SEED,
                   levels=(LEVEL,)) -> tuple[dict, int]:
    """Percentile intervals of the mean partial, resampling seeds jointly for every configuration.

    matrix: configs x K; idx: eligible triples as rows of indices. Returns {level: (lo, hi)} and the number of
    (resample, triple) cells dropped because the partial was undefined in that resample."""
    k = matrix.shape[1]
    rng = np.random.default_rng(seed)
    means, dropped = [], 0
    for _ in range(n_boot):
        s = rng.integers(0, k, size=k)
        vals = _partials_from_corr(_corr_matrix(matrix[:, s]), idx)
        dropped += int(np.isnan(vals).sum())
        if np.any(np.isfinite(vals)):
            means.append(float(np.nanmean(vals)))
    out = {}
    for level in levels:
        if not means:
            out[level] = (float("nan"), float("nan"))
            continue
        a = (1 - level) / 2
        lo, hi = np.quantile(means, [a, 1 - a])
        out[level] = (float(lo), float(hi))
    return out, dropped


def node_test(values: dict, triples: list[dict], n_boot: int = N_BOOT, seed: int = BOOT_SEED,
              primary_only: bool = True, levels=(LEVEL, BONFERRONI_LEVEL)) -> dict:
    """values: config id -> vector over the node's complete seeds. triples: design triples (dicts with g, p, c)."""
    sel = [t for t in triples if (t["primary"] or not primary_only) and all(t[m] in values for m in "gpc")]
    reasons, eligible, per_triple = Counter(), [], []
    for t in sel:
        v, why = triple_partial(values[t["g"]], values[t["p"]], values[t["c"]])
        reasons[why] += 1
        per_triple.append({"id": t["id"], "partial": v, "reason": why, "primary": t["primary"]})
        if v is not None:
            eligible.append(t)
    n_seeds = len(next(iter(values.values()))) if values else 0
    res = {"n_selected": len(sel), "n_eligible": len(eligible), "reasons": dict(reasons), "triples": per_triple,
           "n_seeds": n_seeds}
    if not eligible or n_seeds < MIN_COMPLETE_SEEDS:
        res.update({"estimate": None, "intervals": {}, "verdict": "NOT_TESTED", "verdict_bonferroni": "NOT_TESTED",
                    "bootstrap_dropped_cells": 0})
        return res
    order = sorted({t[m] for t in eligible for m in "gpc"})
    pos = {c: i for i, c in enumerate(order)}
    matrix = np.array([np.asarray(values[c], float) for c in order])
    idx = np.array([[pos[t["g"]], pos[t["p"]], pos[t["c"]]] for t in eligible])
    est = float(np.mean([p["partial"] for p in per_triple if p["partial"] is not None]))
    iv, dropped = seed_bootstrap(matrix, idx, n_boot=n_boot, seed=seed, levels=levels)
    res.update({"estimate": est, "intervals": {f"{lv:.5f}": list(iv[lv]) for lv in levels},
                "verdict": decide(*iv[LEVEL]) if LEVEL in iv else None,
                "verdict_bonferroni": decide(*iv[BONFERRONI_LEVEL]) if BONFERRONI_LEVEL in iv else None,
                "bootstrap_dropped_cells": dropped})
    return res


def decision(verdicts: dict, nodes=sd.DECISION_NODES) -> str:
    return ("PROPOSE_SEVENTH_D3A_ARM" if any(verdicts.get(n) == "SHARED" for n in nodes)
            else "R1_THEORY_RHO_2_FINAL")


# ---------------------------------------------------------------------------------------------------- input checks

def refuse_path(path: Path) -> Path:
    path = Path(path)
    from r1.c3.analysis_guard import refuse_sealed
    try:
        refuse_sealed(path)
    except RuntimeError:
        raise AnalysisRefused("r1_sealed paths are never inputs") from None
    for part in path.resolve().parts:
        if any(f in part.lower() for f in _FORBIDDEN_PARTS):
            raise AnalysisRefused(f"refused path component {part!r} (sealed, label, evaluation or test data)")
    for parent in (path.resolve(), *path.resolve().parents):
        for marker in _EVIDENCE_MARKERS:
            if (parent / marker).exists():
                raise AnalysisRefused(f"{path} lies in an evidence audit directory ({marker})")
    return path


def load_run(run_dir: Path, engineering: bool, repo: Path | None = None) -> tuple[dict, list[dict], dict]:
    run_dir = refuse_path(Path(run_dir))
    manifest = json.loads(refuse_path(run_dir / "manifest.json").read_text())
    if manifest.get("schema") != SCHEMA_RUN:
        raise AnalysisRefused(f"manifest schema must be {SCHEMA_RUN!r}")
    design = sd.build_design(repo or sd.REPO)
    if manifest.get("design_sha256") != sd.design_sha256(design):
        raise AnalysisRefused("the run's design differs from the pinned design")
    if manifest.get("run_id") != sd.RUN_ID:
        raise AnalysisRefused(f"run_id must be {sd.RUN_ID!r}")
    label = manifest.get("label")
    if engineering:
        if label != "ENGINEERING_ONLY":
            raise AnalysisRefused("--engineering reads ENGINEERING_ONLY tables only")
    elif label != "EVIDENCE" or manifest.get("stub"):
        raise AnalysisRefused("the evidence analysis reads only an EVIDENCE table from the harness (no stub)")
    if list(manifest.get("seeds", [])) != list(sd.SEED_BLOCK):
        raise AnalysisRefused("the run's seeds are not exactly the declared block 3301-3420")
    if manifest.get("stop"):
        raise AnalysisRefused(f"the run ended in a STOP ({manifest['stop']}); a STOP is reported, not analysed")
    rows = []
    for line in refuse_path(run_dir / "runs.jsonl").read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            if set(row) != ROW_KEYS:
                raise AnalysisRefused(f"run row keys must be exactly {sorted(ROW_KEYS)}")
            rows.append(row)
    return manifest, rows, design


def table(rows: list[dict], design: dict) -> dict:
    """Validate coverage and determinism; return node -> config -> seed -> metric (None for a failed run)."""
    expected = {(n, c, "seed", s) for n, v in design["nodes"].items() for c in v["configs"] for s in sd.SEED_BLOCK}
    expected |= {(n, c, "repeat", sd.SEED_BLOCK[0]) for n, v in design["nodes"].items() for c in v["configs"]}
    got = Counter((r["node"], r["config"], r["condition"], r["seed"]) for r in rows)
    if any(k not in expected for k in got):
        raise AnalysisRefused("the table holds a run outside the declared design (node, configuration, seed)")
    if any(n > 1 for n in got.values()):
        raise AnalysisRefused("a declared run appears twice")
    if set(got) != expected:
        raise AnalysisRefused(f"the table misses {len(expected - set(got))} declared runs")
    out = {n: {c: {} for c in v["configs"]} for n, v in design["nodes"].items()}
    repeats = {}
    for r in rows:
        ok = bool(r["success"]) and r["metric"] is not None and math.isfinite(float(r["metric"]))
        if r["condition"] == "repeat":
            repeats[(r["node"], r["config"])] = float(r["metric"]) if ok else None
            continue
        if design["nodes"][r["node"]]["configs"][r["config"]]["edits"] and r["edit_applied"] is not True:
            raise AnalysisRefused(f"STOP: edit not applied for {r['node']} {r['config']} seed {r['seed']}")
        out[r["node"]][r["config"]][r["seed"]] = float(r["metric"]) if ok else None
    for (n, c), v in repeats.items():
        if v is None or out[n][c][sd.SEED_BLOCK[0]] is None or v != out[n][c][sd.SEED_BLOCK[0]]:
            raise AnalysisRefused(f"STOP: determinism check failed for {n} {c} at seed {sd.SEED_BLOCK[0]}")
    return out


def complete_values(node_table: dict) -> tuple[dict, dict]:
    """Apply the failure rule; return config -> vector over the node's complete seeds, and a record."""
    dropped_cfg = {c: sum(v is None for v in seeds.values()) for c, seeds in node_table.items()}
    dropped_cfg = {c: n for c, n in dropped_cfg.items() if n > MAX_FAILED_SEEDS_PER_CONFIG}
    kept = {c: s for c, s in node_table.items() if c not in dropped_cfg}
    bad_seeds = sorted({s for seeds in kept.values() for s, v in seeds.items() if v is None})
    seeds = [s for s in sd.SEED_BLOCK if s not in bad_seeds]
    values = {c: [kept[c][s] for s in seeds] for c in kept} if "c0" in kept else {}
    return values, {"dropped_configs": dropped_cfg, "dropped_seeds": bad_seeds, "n_complete_seeds": len(seeds)}


def analyse(run_dir: Path, engineering: bool = False, n_boot: int = N_BOOT, repo: Path | None = None) -> dict:
    if n_boot != N_BOOT and not engineering:
        raise AnalysisRefused("the evidence analysis uses exactly B = 2,000")
    manifest, rows, design = load_run(run_dir, engineering, repo)
    tab = table(rows, design)
    nodes = {}
    for node in sd.T0_NODES:
        values, rec = complete_values(tab[node])
        triples = design["nodes"][node]["triples"]
        prim = node_test(values, triples, n_boot=n_boot) if values else {"verdict": "NOT_TESTED", "estimate": None}
        allt = node_test(values, triples, n_boot=n_boot, primary_only=False, levels=(LEVEL,)) if values else {}
        split = {}
        if values:
            for name, sel in (("realised_r_pc_lt_0.95", lambda r: r < 0.95), ("realised_r_pc_ge_0.95", lambda r: r >= 0.95)):
                vals = []
                for t in triples:
                    if not all(t[m] in values for m in "gpc"):
                        continue
                    v, _ = triple_partial(values[t["g"]], values[t["p"]], values[t["c"]])
                    r_pc = np.corrcoef(values[t["p"]], values[t["c"]])[0, 1] if v is not None else None
                    if v is not None and sel(r_pc):
                        vals.append(v)
                split[name] = {"n": len(vals), "mean_partial": float(np.mean(vals)) if vals else None}
        nodes[node] = {"failures": rec, "primary": prim, "secondary_all_triples": allt, "secondary_realised_split": split}
    verdicts = {n: nodes[n]["primary"]["verdict"] for n in sd.T0_NODES}
    bonf = {n: nodes[n]["primary"].get("verdict_bonferroni", "NOT_TESTED") for n in sd.T0_NODES}
    return {"schema": SCHEMA_OUT, "label": manifest["label"], "run_id": manifest["run_id"],
            "design_sha256": manifest["design_sha256"], "threshold": THRESHOLD, "level": LEVEL, "n_boot": n_boot,
            "boot_seed": BOOT_SEED, "resampling_unit": "seed (all configurations of a node jointly)",
            "verdicts": verdicts, "decision": decision(verdicts),
            "decision_seven_nodes": decision(verdicts, sd.SEVEN_NODES),
            "verdicts_bonferroni": bonf, "decision_bonferroni": decision(bonf), "nodes": nodes}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--out", required=True)
    ap.add_argument("--engineering", action="store_true", help="read an ENGINEERING_ONLY (stub / dry-run) table")
    args = ap.parse_args(argv)
    res = analyse(Path(args.run_dir), engineering=args.engineering)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: res[k] for k in ("label", "verdicts", "decision", "decision_seven_nodes",
                                          "verdicts_bonferroni")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
