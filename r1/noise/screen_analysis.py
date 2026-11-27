#!/usr/bin/env python3
"""The declared test of R1-SCREEN-MEASURE (tier E): computes exactly the pre-declared statistic and refuses anything else.

AI-assisted (Claude, subagent, 23 Nov 2026). DRAFT; not signed; not reviewed.
Pre-declaration: ``docs/r1/authorizations/SCREEN_MEASURE_PREDECLARATION_DRAFT_20261123.md`` §6.

Input: one run directory written by ``r1.noise.screen_measure`` (``manifest.json`` and ``lineage_runs.jsonl``).
Nothing else is read except the pinned design inputs (``screen_design.build_design``).

Statistic, per node (no pooling across nodes):
* each configuration's metric vector over the node's complete seeds is centred by its own mean (this removes the
  configuration's true value; inside a correlation it is a no-op, stated for clarity);
* per triple (g, p, c) = (c0, c_i, c_ij), the sample partial correlation corr(c, g | p) over the common seeds;
* a triple is not eligible (fixed on the full sample) if a member has zero spread, if |corr(g, p)| >= 0.999 or
  |corr(p, c)| >= 0.999, or if two members have identical value vectors;
* the node estimate is the equal-weight mean of the partials of its eligible **primary** triples (design: neither
  link near-duplicate);
* interval: 95 % percentile bootstrap over **seeds**, every configuration of the node resampled jointly with the same
  seed indices (all triples share c0, parents are shared by up to four triples and children by two, so triples are
  dependent; the seed is the independent unit), B = 2,000, generator ``numpy.random.default_rng(20261123)``; in a
  resample, an eligible triple whose partial is undefined or near-singular is left out of that resample's mean, and a
  resample in which every eligible triple is undefined is left out of the interval (both numbers are reported:
  ``bootstrap_dropped_cells``, ``bootstrap_empty_resamples``);
* verdict: SHARED if the interval lies entirely above 0.1, NO_SHARED if entirely below 0.1, otherwise INCONCLUSIVE;
  NOT_TESTED if the design gives the node no primary triple, if no primary triple is eligible, or if fewer than 108
  complete seeds remain.
* decision (R1-SCREEN-MEASURE): any decision node SHARED -> propose the seventh D.3a arm of R1-D3-CHOICES (1) before
  the D.3 pre-declaration is signed; otherwise R1-THEORY-RHO (2) is final. Per-node 95 % intervals decide; the
  Bonferroni reading over the testable nodes of the design (1 - 0.05 / m) is reported beside it, never decisive.

Failures (pre-declared): a configuration with failed or non-finite runs at more than 6 of the 120 seeds is dropped
with its triples (c0 dropped -> NOT_TESTED); otherwise the failing seeds are dropped for the whole node.

Refusals added after the independent review (AI-assisted (Claude, subagent, 23 Nov 2026); review
``docs/r1/reviews/SCREEN_MEASURE_PREDECL_REVIEW_20261123.md``): the run table's sha256 must equal the manifest's
``runs_sha256`` (M2); in evidence mode the manifest must also carry the preflight record, harness ``6adf3859`` clean and
``edit_sets`` ``equal`` on every T0 node (M2); and two configurations of a node with bit-identical metric vectors over
the node's complete seeds are a STOP (M3: the child-exclusion rule rests on the D25 activity map, and a child equal to
a single edit would turn a lineage into a sibling triple, whose partial is not 0 under the kernel).

Secondary (reported, never decisive): all eligible triples of the node (near-duplicate links included); the triples
of the superseded p -> c-only rule; the eligible triples split by the realised corr(g, p) and corr(p, c) (both
< 0.95 against the rest); the seven-node (PRE-WDBC) decision.

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

SCHEMA_RUN = "r1_screen_measure_run/v2"
SCHEMA_OUT = "r1_screen_measure_analysis/v2"
RUNS_FILE = "lineage_runs.jsonl"
HARNESS_COMMIT = "6adf3859de66c4814fcf376eed59880fbd8eeaf7"   # the B.2 audit harness (R1-SWEEP2-B2-GO)
THRESHOLD = 0.1
LEVEL = 0.95
NEAR_SINGULAR = 0.999
N_BOOT = 2000
BOOT_SEED = 20261123
BOOT_CHUNK = 250                                         # resamples per vectorised block (memory only; no effect)
MAX_FAILED_SEEDS_PER_CONFIG = 6                          # 5 % of 120
MIN_COMPLETE_SEEDS = 108                                 # 90 % of 120
REALISED_SPLIT = 0.95
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
    """Sample partial correlation corr(c, g | p) and the reason (``ok`` or why the triple is not eligible).

    Same rule as ``r1/noise/screening_test.py`` ``triple_partial`` (branch mac-screening-test-20261122)."""
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


def _corr(a, b) -> float:
    a, b = np.asarray(a, float) - np.mean(a), np.asarray(b, float) - np.mean(b)
    den = math.sqrt(float((a * a).sum() * (b * b).sum()))
    return float((a * b).sum() / den) if den > 0 else float("nan")


def _batch_partials(x: np.ndarray, idx: np.ndarray) -> np.ndarray:
    """x: R x C x K resampled values; idx: T x 3 (g, p, c) rows. Returns R x T partials, NaN where undefined."""
    x = x - x.mean(axis=2, keepdims=True)
    n = np.sqrt((x * x).sum(axis=2))                                    # R x C
    with np.errstate(invalid="ignore", divide="ignore"):
        r = np.einsum("rck,rdk->rcd", x, x) / (n[:, :, None] * n[:, None, :])
        gp, pc, gc = r[:, idx[:, 0], idx[:, 1]], r[:, idx[:, 1], idx[:, 2]], r[:, idx[:, 0], idx[:, 2]]
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
                   levels=(LEVEL,)) -> tuple[dict, int, int]:
    """Percentile intervals of the mean partial, resampling seeds jointly for every configuration.

    matrix: configs x K; idx: eligible triples as rows of indices. Returns {level: (lo, hi)}, the number of
    (resample, triple) cells left out because the partial was undefined in that resample, and the number of resamples
    in which every eligible triple was undefined (those resamples have no mean and are left out of the interval, so it
    is then taken over fewer than ``n_boot`` means; review N5). The seed indices of all resamples are drawn in one
    call, so the result does not depend on ``BOOT_CHUNK``."""
    k = matrix.shape[1]
    draws = np.random.default_rng(seed).integers(0, k, size=(n_boot, k))
    means, dropped, empty = [], 0, 0
    for a in range(0, n_boot, BOOT_CHUNK):
        block = draws[a:a + BOOT_CHUNK]
        vals = _batch_partials(np.transpose(matrix[:, block], (1, 0, 2)), idx)
        dropped += int(np.isnan(vals).sum())
        ok = np.isfinite(vals).any(axis=1)
        empty += int((~ok).sum())
        with np.errstate(invalid="ignore"):
            means.extend(np.nanmean(vals[ok], axis=1).tolist())
    out = {}
    for level in levels:
        if not means:
            out[level] = (float("nan"), float("nan"))
            continue
        q = (1 - level) / 2
        lo, hi = np.quantile(means, [q, 1 - q])
        out[level] = (float(lo), float(hi))
    return out, dropped, empty


def node_test(values: dict, triples: list[dict], n_boot: int = N_BOOT, seed: int = BOOT_SEED,
              select: str = "primary", levels=(LEVEL,)) -> dict:
    """values: config id -> vector over the node's complete seeds; triples: the design triples of the node.

    select: ``primary`` (the declared test), ``all`` or ``pc_only_rule`` (secondary readings)."""
    if select not in ("primary", "all", "pc_only_rule"):
        raise AnalysisRefused(f"unknown triple selection {select!r}")
    declared = [t for t in triples if select == "all" or t[select]]
    sel = [t for t in declared if all(t[m] in values for m in "gpc")]
    reasons, eligible, per_triple = Counter(), [], []
    for t in sel:
        v, why = triple_partial(values[t["g"]], values[t["p"]], values[t["c"]])
        reasons[why] += 1
        per_triple.append({"id": t["id"], "partial": v, "reason": why, "primary": t["primary"],
                           "realised_r_gp": _corr(values[t["g"]], values[t["p"]]),
                           "realised_r_pc": _corr(values[t["p"]], values[t["c"]])})
        if v is not None:
            eligible.append(t)
    n_seeds = len(next(iter(values.values()))) if values else 0
    res = {"selection": select, "n_declared": len(declared), "n_selected": len(sel), "n_eligible": len(eligible),
           "reasons": dict(reasons), "triples": per_triple, "n_seeds": n_seeds}
    why_not = ("no_triple_in_design" if not declared else "no_eligible_triple" if not eligible
               else f"fewer_than_{MIN_COMPLETE_SEEDS}_complete_seeds" if n_seeds < MIN_COMPLETE_SEEDS else None)
    if why_not:
        res.update({"estimate": None, "intervals": {}, "verdict": "NOT_TESTED", "not_tested_reason": why_not,
                    "verdicts_by_level": {f"{lv:.5f}": "NOT_TESTED" for lv in levels}, "bootstrap_dropped_cells": 0,
                    "bootstrap_empty_resamples": 0})
        return res
    order = sorted({t[m] for t in eligible for m in "gpc"})
    pos = {c: i for i, c in enumerate(order)}
    matrix = np.array([np.asarray(values[c], float) for c in order])
    idx = np.array([[pos[t["g"]], pos[t["p"]], pos[t["c"]]] for t in eligible])
    est = float(np.mean([p["partial"] for p in per_triple if p["partial"] is not None]))
    iv, dropped, empty = seed_bootstrap(matrix, idx, n_boot=n_boot, seed=seed, levels=levels)
    res.update({"estimate": est, "intervals": {f"{lv:.5f}": list(iv[lv]) for lv in levels},
                "verdict": decide(*iv[levels[0]]), "not_tested_reason": None,
                "verdicts_by_level": {f"{lv:.5f}": decide(*iv[lv]) for lv in levels},
                "bootstrap_dropped_cells": dropped, "bootstrap_empty_resamples": empty})
    return res


def decision(verdicts: dict, nodes=sd.DECISION_NODES) -> str:
    return ("PROPOSE_SEVENTH_D3A_ARM" if any(verdicts.get(n) == "SHARED" for n in nodes)
            else "R1_THEORY_RHO_2_FINAL")


def bonferroni_level(design: dict) -> float:
    m = len(design["testable_nodes"])
    return 1 - (1 - LEVEL) / m if m else LEVEL


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
    elif label != "EVIDENCE" or manifest.get("stub") is not False:
        raise AnalysisRefused("the evidence analysis reads only an EVIDENCE table from the harness (no stub)")
    if list(manifest.get("seeds", [])) != list(sd.SEED_BLOCK):
        raise AnalysisRefused("the run's seeds are not exactly the declared block 3301-3420")
    if manifest.get("stop"):
        raise AnalysisRefused(f"the run ended in a STOP ({manifest['stop']}); a STOP is reported, not analysed")
    if not engineering:                                    # review M2: the evidence run's own launch record
        harness = manifest.get("harness") or {}
        edit_sets = manifest.get("edit_sets") or {}
        if not isinstance(manifest.get("preflight"), dict) or not manifest["preflight"]:
            raise AnalysisRefused("the evidence manifest carries no preflight record")
        if harness.get("commit") != HARNESS_COMMIT or harness.get("dirty") is not False:
            raise AnalysisRefused(f"the evidence manifest's harness is not {HARNESS_COMMIT}, clean")
        if set(edit_sets) != set(sd.T0_NODES) or any(v != "equal" for v in edit_sets.values()):
            raise AnalysisRefused("the evidence manifest's edit_sets are not 'equal' on every T0 node")
    runs_path = refuse_path(run_dir / RUNS_FILE)
    want = manifest.get("runs_sha256")                     # review M2: the table is the one the runner wrote
    if not want or sd.sha256_file(runs_path) != want:
        raise AnalysisRefused("the run table's sha256 is missing from the manifest or differs from runs_sha256")
    rows = []
    for line in runs_path.read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            if set(row) != ROW_KEYS:
                raise AnalysisRefused(f"run row keys must be exactly {sorted(ROW_KEYS)}")
            rows.append(row)
    return manifest, rows, design


def _norm(v) -> str:
    v = str(v).strip().strip("\"'")
    return "null" if v.lower() in {"none", "null", "~"} else v


def table(rows: list[dict], design: dict) -> dict:
    """Validate coverage, edits and determinism; return node -> config -> seed -> metric (None for a failed run)."""
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
        node = design["nodes"][r["node"]]
        cfg = node["configs"][r["config"]]
        ok = bool(r["success"]) and r["metric"] is not None and math.isfinite(float(r["metric"]))
        if ok and cfg["edits"]:
            if r["edit_applied"] is not True:
                raise AnalysisRefused(f"STOP: edit not applied for {r['node']} {r['config']} seed {r['seed']}")
            after = {k: _norm(v) for k, v in (r["values_after"] or {}).items()}
            if any(after.get(k) != _norm(v) for k, v in cfg["overrides"].items()):
                raise AnalysisRefused(f"STOP: edit not verified for {r['node']} {r['config']} seed {r['seed']}")
        if r["condition"] == "repeat":
            repeats[(r["node"], r["config"])] = float(r["metric"]) if ok else None
            continue
        out[r["node"]][r["config"]][r["seed"]] = float(r["metric"]) if ok else None
    for (n, c), v in repeats.items():
        if v is None or out[n][c][sd.SEED_BLOCK[0]] is None:      # the runner STOPs on this (review M1)
            raise AnalysisRefused(f"STOP: determinism unverifiable for {n} {c}: a run at seed {sd.SEED_BLOCK[0]} failed")
        if v != out[n][c][sd.SEED_BLOCK[0]]:
            raise AnalysisRefused(f"STOP: determinism check failed for {n} {c} at seed {sd.SEED_BLOCK[0]}")
    return out


def identical_configs(values: dict) -> list[list[str]]:
    """Pairs of configurations whose metric vectors over the node's complete seeds are bit-identical (review M3)."""
    ids = sorted(values)
    return [[a, b] for i, a in enumerate(ids) for b in ids[i + 1:]
            if np.array_equal(np.asarray(values[a], float), np.asarray(values[b], float))]


def complete_values(node_table: dict) -> tuple[dict, dict]:
    """Apply the failure rule; return config -> vector over the node's complete seeds, and a record."""
    dropped_cfg = {c: sum(v is None for v in seeds.values()) for c, seeds in node_table.items()}
    dropped_cfg = {c: n for c, n in dropped_cfg.items() if n > MAX_FAILED_SEEDS_PER_CONFIG}
    kept = {c: s for c, s in node_table.items() if c not in dropped_cfg}
    bad_seeds = sorted({s for seeds in kept.values() for s, v in seeds.items() if v is None})
    seeds = [s for s in sd.SEED_BLOCK if s not in bad_seeds]
    values = {c: [kept[c][s] for s in seeds] for c in kept} if "c0" in kept else {}
    return values, {"dropped_configs": dropped_cfg, "dropped_seeds": bad_seeds, "n_complete_seeds": len(seeds),
                    "c0_dropped": "c0" not in kept}


def realised_split(primary_and_rest: dict) -> dict:
    """Secondary: mean partial of eligible triples with realised corr(g, p) and corr(p, c) both < 0.95, and of the rest."""
    rows = [t for t in primary_and_rest.get("triples", []) if t["partial"] is not None]
    lo = [t["partial"] for t in rows if t["realised_r_gp"] < REALISED_SPLIT and t["realised_r_pc"] < REALISED_SPLIT]
    hi = [t["partial"] for t in rows if not (t["realised_r_gp"] < REALISED_SPLIT and t["realised_r_pc"] < REALISED_SPLIT)]
    return {"both_links_lt_0.95": {"n": len(lo), "mean_partial": float(np.mean(lo)) if lo else None},
            "a_link_ge_0.95": {"n": len(hi), "mean_partial": float(np.mean(hi)) if hi else None}}


def analyse(run_dir: Path, engineering: bool = False, n_boot: int = N_BOOT, repo: Path | None = None) -> dict:
    if n_boot != N_BOOT and not engineering:
        raise AnalysisRefused("the evidence analysis uses exactly B = 2,000")
    manifest, rows, design = load_run(run_dir, engineering, repo)
    tab = table(rows, design)
    bonf = bonferroni_level(design)
    complete = {node: complete_values(tab[node]) for node in sd.T0_NODES}
    for node, (values, _rec) in complete.items():         # review M3: before any statistic, on every node
        same = identical_configs(values)
        if same:
            raise AnalysisRefused(f"STOP: {node}: configurations {same} have bit-identical metric vectors over the "
                                  "node's complete seeds (an edit is inert; the design's activity map is wrong)")
    nodes = {}
    for node in sd.T0_NODES:
        values, rec = complete[node]
        triples = design["nodes"][node]["triples"]
        if values:
            prim = node_test(values, triples, n_boot=n_boot, levels=(LEVEL, bonf))
            allt = node_test(values, triples, n_boot=n_boot, select="all")
            pconly = node_test(values, triples, n_boot=n_boot, select="pc_only_rule")
            split = realised_split(allt)
        else:
            prim = {"verdict": "NOT_TESTED", "not_tested_reason": "c0_dropped", "estimate": None,
                    "verdicts_by_level": {f"{bonf:.5f}": "NOT_TESTED"}}
            allt, pconly, split = {}, {}, {}
        nodes[node] = {"failures": rec, "primary": prim, "secondary_all_triples": allt,
                       "secondary_pc_only_rule": pconly, "secondary_realised_split": split}
    verdicts = {n: nodes[n]["primary"]["verdict"] for n in sd.T0_NODES}
    verdicts_b = {n: nodes[n]["primary"]["verdicts_by_level"].get(f"{bonf:.5f}", "NOT_TESTED") for n in sd.T0_NODES}
    return {"schema": SCHEMA_OUT, "label": manifest["label"], "run_id": manifest["run_id"],
            "design_sha256": manifest["design_sha256"], "threshold": THRESHOLD, "level": LEVEL, "n_boot": n_boot,
            "boot_seed": BOOT_SEED, "resampling_unit": "seed (every configuration of a node jointly)",
            "testable_nodes": design["testable_nodes"], "verdicts": verdicts, "decision": decision(verdicts),
            "decision_seven_nodes": decision(verdicts, sd.SEVEN_NODES),
            "bonferroni_level": bonf, "verdicts_bonferroni": verdicts_b, "decision_bonferroni": decision(verdicts_b),
            "nodes": nodes}


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
                                          "bonferroni_level", "verdicts_bonferroni")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
