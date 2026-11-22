#!/usr/bin/env python3
"""Direct ancestor-descendant test of the screening (Markov) property on CPU nodes. ENGINEERING_ONLY.

AI-assisted (Claude, subagent, 22 Nov 2026). PLAN rows R1-D3-CHOICES (1) and R1-THEORY-RHO (5). Design and
decision rule: ``docs/r1/reports/SCREENING_TEST_20261122.md`` §2, committed before any audit value was read.

Property under test. T4 Proposition 9 (corollary) and T2 Proposition 4(a) assume that, given the history, a
candidate's error depends on it only through the incumbent's error (eps | e ~ N(rho e, sigma_c^2)). Along one
lineage g -> p -> c (g an ancestor of p, p an ancestor of c), evaluated on common seeds, that kernel makes the errors
a Gaussian Markov chain, so the partial correlation corr(e_c, e_g | e_p) is zero whatever the number of edits per
link. A component u shared by every configuration evaluated at a seed (e = u + w, w Markov along the lineage) makes
it positive: with corr(g, p) = s + (1 - s) r1, corr(p, c) = s + (1 - s) r2, corr(g, c) = s + (1 - s) r1 r2
(``shared_lineage_partial``).

Statistic (per node).
* Errors are centred per configuration: each configuration's values are centred by their own mean over the common
  seeds (removing the configuration's true value), so a triple's correlations are the ordinary sample correlations
  over its seeds.
* Per triple, the sample partial correlation corr(c, g | p). A triple is not eligible if any member has zero spread,
  if |corr(g, p)| >= 0.999 or |corr(p, c)| >= 0.999 (partial undefined), or if two members have identical value
  vectors (the same configuration, e.g. a revisit; the lineage is then degenerate).
* Pooled over a node's eligible triples with equal weights (the mean of the per-triple partials).
* Interval: percentile bootstrap, 2,000 resamples, generator seed 20261122. Track S (``tracks``): clusters are
  instances (each instance has its own audit seeds), resampled with replacement with all their triples. E1b
  (``e1b``): every configuration of a node shares the same six audit seeds, so the seeds are resampled jointly.
* Decision (Track S primary only): ``SHARED`` if the 95 % interval lies above 0.1; ``NO_SHARED`` if it lies below
  0.1; otherwise ``INCONCLUSIVE``.

Sources (read-only; the report's §1 says why each may be read):
* Track S S0.5 (``results/r1/tracks/<node>/s05_*``): per root, the S0.5b truncated incumbents I_8, I_10, I_12, I_20
  of one campaign ledger, audited on the instance's five S0.5 audit seeds (``s05b_truncated.jsonl``), preceded by the
  start configuration c0 audited on the same seeds (``audit_runs.jsonl``; c0 is the one configuration hash audited
  on every primary instance). Incumbents change only on keeps, so the chain is one lineage.
* E1b (``results/r1/pilot/E1b_*``): per instance, c0 (``audits/<inst>__c0.json``) and the snapshot incumbents I_4,
  I_8, I_12 (a leaf of that snapshot with no keep after it ends at the snapshot incumbent), plus branch triples
  (ancestor, I_b, F) for each distinct final incumbent F of a leaf of snapshot b with keeps.

Subcommands:
  design  -- metadata only (decisions, truncation trial counts, configuration hashes; no audit value): the chain
             structure and the power simulation under the kernel and shared-component models.
  run     -- the test.
Run: python -m r1.noise.screening_test design|run --out <json>
"""
from __future__ import annotations

import argparse
import glob
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from r1.harness import REPO

SCHEMA = "r1_screening_test/v1"
LABEL = "ENGINEERING_ONLY"
NEAR_SINGULAR = 0.999
THRESHOLD = 0.1
LEVEL = 0.95
N_BOOT = 2000
RNG_SEED = 20261122
TRACKS_DIRS = {"digits_mlp": "results/r1/tracks/digits_mlp/s05_t7_20261113",
               "tabular_mlp": "results/r1/tracks/tabular_mlp/s05_t7_20261114"}
TRACKS_PRIMARY = ("a2u", 0)          # (policy, rep): the primary root of each instance
TRUNCATE_W = (8, 10, 12, 20)
E1B_GLOB = "results/r1/pilot/E1b_*"
E1B_POINTS = (4, 8, 12)
# digits_mlp calibration of T5_SHARED_NOISE_20261122 (local edits): marginal link correlation 0.82; the shares that
# give an E1-type sibling partial of 0.24 (lower end) and 0.37 (point estimate); s = 0 is the kernel model.
POWER_RHO = 0.82
POWER_SHARES = {"kernel s=0": 0.0, "shared s=0.7082 (p=0.24)": 0.7082, "shared s=0.7891 (p=0.37)": 0.7891}
POWER_NSIM = 500


# ------------------------------------------------------------------------------------------------ statistics

def _corr(a: np.ndarray, b: np.ndarray) -> float | None:
    a = a - a.mean()
    b = b - b.mean()
    da, db = float(np.sqrt((a * a).sum())), float(np.sqrt((b * b).sum()))
    if da <= 0 or db <= 0:
        return None
    return float((a * b).sum() / (da * db))


def triple_partial(g, p, c, near_singular: float = NEAR_SINGULAR) -> tuple[float | None, str]:
    """Sample partial correlation corr(c, g | p) over common seeds, per-configuration centred.

    Returns (value, reason); value is None for an ineligible triple, with the reason."""
    g, p, c = (np.asarray(x, float) for x in (g, p, c))
    if not (len(g) == len(p) == len(c)) or len(g) < 4:
        return None, "too_few_seeds"
    if not (np.all(np.isfinite(g)) and np.all(np.isfinite(p)) and np.all(np.isfinite(c))):
        return None, "non_finite"
    if np.array_equal(g, p) or np.array_equal(p, c) or np.array_equal(g, c):
        return None, "identical_members"
    r_gp, r_pc, r_gc = _corr(g, p), _corr(p, c), _corr(g, c)
    if r_gp is None or r_pc is None or r_gc is None:
        return None, "zero_spread"
    if abs(r_gp) >= near_singular or abs(r_pc) >= near_singular:
        return None, "near_singular"
    return (r_gc - r_gp * r_pc) / math.sqrt((1 - r_gp ** 2) * (1 - r_pc ** 2)), "ok"


def shared_lineage_partial(s: float, r1: float, r2: float) -> float:
    """Population corr(c, g | p) under e = u + w (shared share s; w Markov with link coefficients r1, r2)."""
    gp, pc, gc = s + (1 - s) * r1, s + (1 - s) * r2, s + (1 - s) * r1 * r2
    return (gc - gp * pc) / math.sqrt((1 - gp ** 2) * (1 - pc ** 2))


def link_coefficient(rho: float, s: float) -> float:
    """r_w with s + (1 - s) r_w = rho (T5_SHARED_NOISE §1); 0 if s >= rho."""
    return max(0.0, (rho - s) / (1 - s)) if s < 1 else 0.0


def decide(lo: float, hi: float, threshold: float = THRESHOLD) -> str:
    if not (math.isfinite(lo) and math.isfinite(hi)):
        return "INCONCLUSIVE"
    if lo > threshold:
        return "SHARED"
    if hi < threshold:
        return "NO_SHARED"
    return "INCONCLUSIVE"


def dedupe_consecutive(chain: list) -> list:
    """Drop elements whose value vector equals the previous element's (an unchanged incumbent)."""
    out = []
    for v in chain:
        if not out or not np.array_equal(np.asarray(out[-1], float), np.asarray(v, float)):
            out.append(v)
    return out


def chain_triples(n: int, mode: str = "consecutive") -> list[tuple[int, int, int]]:
    if mode == "consecutive":
        return [(k, k + 1, k + 2) for k in range(n - 2)]
    if mode == "all":
        return [(i, j, k) for i in range(n) for j in range(i + 1, n) for k in range(j + 1, n)]
    raise ValueError(mode)


def cluster_partials(clusters: dict, mode: str = "consecutive") -> tuple[dict, Counter]:
    """clusters: id -> list of (triples) where each item is either a chain (list of vectors) under key 'chains' or
    explicit triples under key 'triples'. Returns id -> list of eligible partials, and the reason counts."""
    out, reasons = {}, Counter()
    for cid, item in clusters.items():
        vals = []
        triples = list(item.get("triples", []))
        for chain in item.get("chains", []):
            triples += [(chain[i], chain[j], chain[k]) for i, j, k in chain_triples(len(chain), mode)]
        for g, p, c in triples:
            v, why = triple_partial(g, p, c)
            reasons[why] += 1
            if v is not None:
                vals.append(v)
        out[cid] = vals
    return out, reasons


def pooled(partials: dict) -> tuple[float, int]:
    allv = [v for vals in partials.values() for v in vals]
    return (float(np.mean(allv)) if allv else float("nan")), len(allv)


def cluster_bootstrap(partials: dict, n_boot: int = N_BOOT, seed: int = RNG_SEED,
                      level: float = LEVEL) -> tuple[float, float]:
    """Percentile interval of the pooled mean, resampling clusters with all their triples."""
    ids = sorted(k for k, v in partials.items() if v)
    if len(ids) < 2:
        return float("nan"), float("nan")
    sums = np.array([float(np.sum(partials[k])) for k in ids])
    cnts = np.array([len(partials[k]) for k in ids], float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(ids), size=(n_boot, len(ids)))
    means = sums[idx].sum(axis=1) / cnts[idx].sum(axis=1)
    a = (1 - level) / 2
    lo, hi = np.quantile(means, [a, 1 - a])
    return float(lo), float(hi)


def seed_bootstrap(triples: list, n_boot: int = N_BOOT, seed: int = RNG_SEED,
                   level: float = LEVEL) -> tuple[float, float]:
    """Percentile interval of the pooled mean when every triple shares the same seeds (resampled jointly).

    A resample whose triple is ineligible (e.g. a member with zero spread) drops that triple from that resample."""
    if not triples:
        return float("nan"), float("nan")
    k = len(triples[0][0])
    arr = np.array([[np.asarray(x, float) for x in t] for t in triples])  # T x 3 x K
    rng = np.random.default_rng(seed)
    means = []
    for _ in range(n_boot):
        idx = rng.integers(0, k, size=k)
        vals = [v for v, _ in (triple_partial(t[0][idx], t[1][idx], t[2][idx]) for t in arr) if v is not None]
        if vals:
            means.append(float(np.mean(vals)))
    if not means:
        return float("nan"), float("nan")
    a = (1 - level) / 2
    lo, hi = np.quantile(means, [a, 1 - a])
    return float(lo), float(hi)


def summarise(partials: dict, reasons: Counter, bootstrap: str = "cluster", triples=None) -> dict:
    est, n = pooled(partials)
    if bootstrap == "cluster":
        lo, hi = cluster_bootstrap(partials)
    else:
        lo, hi = seed_bootstrap(triples or [])
    return {"estimate": est, "lo": lo, "hi": hi, "n_triples": n,
            "n_clusters": sum(1 for v in partials.values() if v), "reasons": dict(reasons),
            "decision": decide(lo, hi)}


# ------------------------------------------------------------------------------------------------ simulation

def simulate_chain(n: int, k: int, s: float, rho: float, rng, means=None, u=None, w0=None) -> np.ndarray:
    """n configurations along one lineage at k common seeds under e = mu + u + w (unit total variance).

    u ~ N(0, s) per seed, shared by every configuration; w Markov with link coefficient r_w(rho, s)."""
    r = link_coefficient(rho, s)
    u = rng.normal(0.0, math.sqrt(s), k) if u is None else u
    w = rng.normal(0.0, math.sqrt(1 - s), k) if w0 is None else w0
    rows = []
    for i in range(n):
        if i:
            w = r * w + math.sqrt(1 - r * r) * rng.normal(0.0, math.sqrt(1 - s), k)
        rows.append((0.0 if means is None else means[i]) + u + w)
    return np.array(rows)


def power_tracks(chain_lengths: dict, k: int, s: float, rho: float = POWER_RHO, nsim: int = POWER_NSIM,
                 seed: int = RNG_SEED, n_boot: int = N_BOOT) -> dict:
    """Decision frequencies when each instance carries one lineage of the given length on its own k seeds."""
    rng = np.random.default_rng(seed + int(round(s * 1e4)))
    out, ests = Counter(), []
    for i in range(nsim):
        clusters = {cid: {"chains": [list(simulate_chain(n, k, s, rho, rng, means=rng.normal(0, 3, n)))]}
                    for cid, n in chain_lengths.items() if n >= 3}
        parts, _ = cluster_partials(clusters)
        est, _ = pooled(parts)
        lo, hi = cluster_bootstrap(parts, n_boot=n_boot, seed=seed + i)
        out[decide(lo, hi)] += 1
        ests.append(est)
    return {"s": s, "rho": rho, "k": k, "nsim": nsim, "n_instances_with_triple": sum(1 for n in chain_lengths.values() if n >= 3),
            "n_triples": sum(max(n - 2, 0) for n in chain_lengths.values()),
            "mean_estimate": float(np.nanmean(ests)), "sd_estimate": float(np.nanstd(ests)),
            "p_shared": out["SHARED"] / nsim, "p_no_shared": out["NO_SHARED"] / nsim,
            "p_inconclusive": out["INCONCLUSIVE"] / nsim}


def power_e1b(structure: list, k: int, s: float, rho: float = POWER_RHO, nsim: int = 50,
              seed: int = RNG_SEED, n_boot: int = 200) -> dict:
    """E1b: one node's instances share the seeds and c0. structure: per instance, its chain length (c0 first)."""
    rng = np.random.default_rng(seed + 7 + int(round(s * 1e4)))
    out, ests = Counter(), []
    for i in range(nsim):
        u = rng.normal(0.0, math.sqrt(s), k)
        w0 = rng.normal(0.0, math.sqrt(1 - s), k)
        triples = []
        for n in structure:
            if n < 3:
                continue
            ch = simulate_chain(n, k, s, rho, rng, means=rng.normal(0, 3, n), u=u, w0=w0)
            triples += [(ch[a], ch[b], ch[c]) for a, b, c in chain_triples(n)]
        vals = [v for v, _ in (triple_partial(*t) for t in triples) if v is not None]
        lo, hi = seed_bootstrap(triples, n_boot=n_boot, seed=seed + i)
        out[decide(lo, hi)] += 1
        ests.append(float(np.mean(vals)) if vals else float("nan"))
    return {"s": s, "k": k, "nsim": nsim, "n_triples": sum(max(n - 2, 0) for n in structure),
            "mean_estimate": float(np.nanmean(ests)), "p_shared": out["SHARED"] / nsim,
            "p_no_shared": out["NO_SHARED"] / nsim, "p_inconclusive": out["INCONCLUSIVE"] / nsim}


# ------------------------------------------------------------------------------------------------ loaders

def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def _refuse_protected(path: Path) -> None:
    """Fail closed on anything the release locks or the sealed-tree guard protect (report §1)."""
    from r1.c3.analysis_guard import refuse_sealed
    refuse_sealed(path)
    for parent in (Path(path), *Path(path).parents):
        for marker in ("evidence_completion.json", "evidence_binding.json", "label_block.jsonl",
                       "evaluation_block.jsonl"):
            if (parent / marker).exists():
                raise RuntimeError(f"STOP: {path} lies in an evidence audit directory")
        if parent == REPO:
            break


def _primary_roots(d: Path) -> list[dict]:
    pol, rep = TRACKS_PRIMARY
    return [r for r in _jsonl(d / "roots.jsonl")
            if r.get("status") == "ok" and r.get("policy") == pol and int(r.get("rep", 0)) == rep]


def _instance_seeds(d: Path) -> dict:
    """instance_id -> its audit seeds (from the truncation records' metadata)."""
    seeds = {}
    for r in _jsonl(d / "s05b_truncated.jsonl"):
        seeds.setdefault(r["instance_id"], tuple(int(x) for x in r["audit_seeds"]))
    return seeds


def identify_c0(d: Path) -> str | None:
    """The start configuration's hash, from hashes, seeds and file order only (no audit value).

    The S0.5 calibration audits every executed non-rule proposal of a primary root in budget order, candidate first and
    incumbent second (``collect.calibration_rows``), on that instance's own seeds; the first audited proposal's
    incumbent is the start configuration. So, per primary instance, c0 is the second distinct configuration hash in
    file order among the rows on that instance's seeds. All primary instances must give the same hash, and it must
    be audited on all five seeds of every primary instance; otherwise None (c0 is then left out of every chain)."""
    seeds = _instance_seeds(d)
    primary = {r["instance_id"] for r in _primary_roots(d)}
    by_seed = {s: inst for inst, ss in seeds.items() for s in ss}
    order = defaultdict(list)
    have = defaultdict(lambda: defaultdict(set))
    for r in _jsonl(d / "audit_runs.jsonl"):           # only hash, seed and file order are used here
        inst = by_seed.get(int(r["seed"]))
        if inst is None:
            continue
        if r["config_hash"] not in order[inst]:
            order[inst].append(r["config_hash"])
        have[r["config_hash"]][inst].add(int(r["seed"]))
    picks = {order[i][1] if len(order[i]) > 1 else None for i in primary}
    if len(picks) != 1 or None in picks:
        return None
    c0 = picks.pop()
    if not all(set(seeds[i]) <= have[c0].get(i, set()) for i in primary):
        return None
    return c0


def tracks_chain_lengths_meta(d: Path, c0_known: bool) -> dict:
    """Design-time chain lengths from campaign decisions and truncation trial counts only (no audit value)."""
    trials = defaultdict(dict)
    for r in _jsonl(d / "s05b_truncated.jsonl"):
        trials[r["root_id"]][int(r["W"])] = int(r["trials"])
    out = {}
    for root in _primary_roots(d):
        keeps = sorted(int(x["index"]) for x in root["decisions"] if x.get("action") == "keep")
        elems, prev = (1 if c0_known else 0), 0
        for W in TRUNCATE_W:
            t = trials[root["root_id"]].get(W)
            if t is None:
                continue
            changed = any(prev < i <= t for i in keeps)
            if elems == 0 or changed:
                elems += 1
            prev = t
        out[root["instance_id"]] = elems
    return out


def load_tracks(d: Path, c0: str | None, roots_filter=None) -> dict:
    """instance_id -> {'chains': [...]}: per selected root, [c0, I_8, I_10, I_12, I_20] value vectors on the
    instance's audit seeds, consecutive repeats removed and elements with a missing value dropped."""
    for name in ("roots.jsonl", "s05b_truncated.jsonl", "audit_runs.jsonl"):
        _refuse_protected(d / name)
    roots = [r for r in _jsonl(d / "roots.jsonl") if r.get("status") == "ok"]
    if roots_filter is None:
        pol, rep = TRACKS_PRIMARY
        roots = [r for r in roots if r.get("policy") == pol and int(r.get("rep", 0)) == rep]
    else:
        roots = [r for r in roots if roots_filter(r)]
    trunc = defaultdict(dict)
    for r in _jsonl(d / "s05b_truncated.jsonl"):
        trunc[r["root_id"]][int(r["W"])] = r
    runs = {}
    for r in _jsonl(d / "audit_runs.jsonl"):
        runs[(r["config_hash"], int(r["seed"]))] = r["metric"]
    clusters = defaultdict(lambda: {"chains": []})
    seen_chains = defaultdict(set)
    for root in roots:
        rows = trunc[root["root_id"]]
        if not rows:
            continue
        seeds = tuple(int(x) for x in next(iter(rows.values()))["audit_seeds"])
        chain = []
        if c0 is not None:
            chain.append([runs.get((c0, s)) for s in seeds])
        for W in TRUNCATE_W:
            if W in rows:
                if tuple(int(x) for x in rows[W]["audit_seeds"]) != seeds:
                    raise ValueError(f"{root['root_id']}: truncations on different seeds")
                chain.append(rows[W]["y_terminal_per_seed"])
        chain = [np.asarray(v, float) for v in chain if v is not None and all(x is not None for x in v)]
        chain = dedupe_consecutive(chain)
        key = tuple(tuple(v) for v in chain)
        if key in seen_chains[root["instance_id"]]:      # an identical trajectory (e.g. another policy) counts once
            continue
        seen_chains[root["instance_id"]].add(key)
        clusters[root["instance_id"]]["chains"].append(chain)
    return dict(clusters)


def _e1b_dirs() -> list[Path]:
    return sorted(Path(p) for p in glob.glob(str(REPO / E1B_GLOB)) if (Path(p) / "leaves").is_dir())


def load_e1b(meta_only: bool = False) -> dict:
    """node -> list of instance records {'chain': [...], 'branches': [(anc_idx, b_idx, F), ...]} (value vectors), or
    with ``meta_only`` the chain lengths from configuration hashes (c0 assumed distinct from I_4)."""
    out = defaultdict(list)
    for d in _e1b_dirs():
        leaves = []
        for f in sorted((d / "leaves").glob("*.json")):
            _refuse_protected(f)
            leaf = json.loads(f.read_text())
            if leaf.get("integrity") == "ok" and leaf.get("audit_metrics"):
                leaves.append(leaf)
        by_inst = defaultdict(list)
        for leaf in leaves:
            by_inst[leaf["instance"]].append(leaf)
        for inst, ls in sorted(by_inst.items()):
            node = ls[0]["node"]
            c0f = d / "audits" / f"{inst}__c0.json"
            if not c0f.exists():
                continue
            snap = {}
            for b in E1B_POINTS:
                zero = [l for l in ls if int(l["budget_index"]) == b and int(l.get("n_keeps_after", -1)) == 0]
                if zero:
                    snap[b] = zero[0]
            if meta_only:   # configuration hashes only; c0 has no recorded hash and is assumed distinct from I_4
                hashes, tags, n_branch = [], [], 0
                for b in E1B_POINTS:
                    if b in snap and (not hashes or hashes[-1] != snap[b]["final_files_hash"]):
                        hashes.append(snap[b]["final_files_hash"]); tags.append(b)
                for b in tags:
                    n_branch += len({l["final_files_hash"] for l in ls if int(l["budget_index"]) == b
                                     and int(l.get("n_keeps_after", 0)) > 0} - set(hashes))
                out[node].append({"source": d.name, "instance": inst, "chain_len": 1 + len(hashes),
                                  "branch_triples": n_branch})
                continue
            c0 = json.loads(c0f.read_text())
            if [int(x) for x in c0["seeds"]] != list(range(5001, 5001 + len(c0["seeds"]))):
                raise ValueError(f"{c0f}: unexpected audit seeds")
            chain_raw = [("c0", c0["metrics"])] + [(b, snap[b]["audit_metrics"]) for b in E1B_POINTS if b in snap]
            chain_raw = [(t, np.asarray(v, float)) for t, v in chain_raw if v and all(x is not None for x in v)]
            chain, tags = [], []
            for t, v in chain_raw:
                if not chain or not np.array_equal(chain[-1], v):
                    chain.append(v); tags.append(t)
            branches = []
            for b in E1B_POINTS:
                if b not in snap or b not in tags:
                    continue
                bi = tags.index(b)
                if bi == 0:
                    continue
                finals = []
                for l in ls:
                    if int(l["budget_index"]) == b and int(l.get("n_keeps_after", 0)) > 0:
                        v = np.asarray(l["audit_metrics"], float)
                        if not any(np.array_equal(v, f) for f in finals):
                            finals.append(v)
                branches += [(bi - 1, bi, f) for f in finals]
            out[node].append({"source": d.name, "instance": inst, "chain": chain, "branches": branches})
    return dict(out)


def e1b_triples(records: list) -> list:
    triples = []
    for rec in records:
        ch = rec["chain"]
        triples += [(ch[i], ch[j], ch[k]) for i, j, k in chain_triples(len(ch))]
        triples += [(ch[a], ch[b], f) for a, b, f in rec["branches"]]
    # identical triples (the same configurations in two sources on the same seeds) count once
    uniq, keys = [], set()
    for t in triples:
        key = tuple(tuple(np.round(np.asarray(x, float), 12)) for x in t)
        if key not in keys:
            keys.add(key); uniq.append(t)
    return uniq


# ------------------------------------------------------------------------------------------------ commands

def cmd_design(args) -> dict:
    out = {"schema": SCHEMA, "label": LABEL, "phase": "design (metadata only; no audit value read)",
           "threshold": THRESHOLD, "level": LEVEL, "n_boot": N_BOOT, "rng_seed": RNG_SEED,
           "near_singular": NEAR_SINGULAR, "power_rho": POWER_RHO, "tracks": {}, "e1b": {}}
    for node, rel in TRACKS_DIRS.items():
        d = REPO / rel
        c0 = identify_c0(d)
        lengths = tracks_chain_lengths_meta(d, c0 is not None)
        k = len(next(iter(_instance_seeds(d).values())))
        rec = {"dir": rel, "c0_identified": c0 is not None, "k": k, "n_instances": len(lengths),
               "chain_length_counts": dict(Counter(lengths.values())),
               "expected_consecutive_triples": sum(max(n - 2, 0) for n in lengths.values()),
               "power": {name: power_tracks(lengths, k, s, nsim=args.nsim) for name, s in POWER_SHARES.items()}}
        out["tracks"][node] = rec
    for node, recs in sorted(load_e1b(meta_only=True).items()):
        lens = [r["chain_len"] for r in recs]
        # power: each branch triple is simulated as one more three-element lineage from the node's shared c0
        structure = lens + [3] * sum(r["branch_triples"] for r in recs)
        out["e1b"][node] = {"n_instances": len(recs), "sources": dict(Counter(r["source"] for r in recs)),
                            "chain_length_counts": dict(Counter(lens)),
                            "chain_triples_upper_bound": sum(max(n - 2, 0) for n in lens),
                            "branch_triples_upper_bound": sum(r["branch_triples"] for r in recs),
                            "power": {name: power_e1b(structure, 6, s)
                                      for name, s in POWER_SHARES.items()}}
    return out


def cmd_run(args) -> dict:
    out = {"schema": SCHEMA, "label": LABEL, "phase": "run", "threshold": THRESHOLD, "level": LEVEL,
           "n_boot": N_BOOT, "rng_seed": RNG_SEED, "near_singular": NEAR_SINGULAR, "tracks": {}, "e1b": {}}
    for node, rel in TRACKS_DIRS.items():
        d = REPO / rel
        c0 = identify_c0(d)
        rec = {"dir": rel, "c0_hash": c0}
        prim = load_tracks(d, c0)
        parts, why = cluster_partials(prim, "consecutive")
        rec["primary"] = summarise(parts, why)
        rec["primary"]["chain_length_counts"] = dict(Counter(len(ch) for v in prim.values() for ch in v["chains"]))
        allp, why_all = cluster_partials(prim, "all")
        rec["secondary_all_triples"] = summarise(allp, why_all)
        reps = load_tracks(d, c0, roots_filter=lambda r: int(r.get("rep", 0)) in (0, 1))
        rp, why_r = cluster_partials(reps, "consecutive")
        rec["secondary_with_rep1_chains"] = summarise(rp, why_r)
        if c0 is not None:
            noc0 = load_tracks(d, None)
            nc, why_n = cluster_partials(noc0, "consecutive")
            rec["secondary_without_c0"] = summarise(nc, why_n)
        # descriptive marginal correlations of the eligible primary triples
        gp, pc, gc = [], [], []
        for v in prim.values():
            for ch in v["chains"]:
                for i, j, k in chain_triples(len(ch)):
                    if triple_partial(ch[i], ch[j], ch[k])[0] is not None:
                        gp.append(_corr(ch[i], ch[j])); pc.append(_corr(ch[j], ch[k])); gc.append(_corr(ch[i], ch[k]))
        rec["primary"]["mean_marginal"] = {"gp": float(np.mean(gp)) if gp else None,
                                           "pc": float(np.mean(pc)) if pc else None,
                                           "gc": float(np.mean(gc)) if gc else None}
        out["tracks"][node] = rec
    for node, recs in sorted(load_e1b().items()):
        triples = e1b_triples(recs)
        vals, why = [], Counter()
        for t in triples:
            v, w = triple_partial(*t)
            why[w] += 1
            if v is not None:
                vals.append(v)
        est = float(np.mean(vals)) if vals else float("nan")
        lo, hi = seed_bootstrap(triples)
        out["e1b"][node] = {"estimate": est, "lo": lo, "hi": hi, "n_triples": len(vals), "reasons": dict(why),
                            "sources": dict(Counter(r["source"] for r in recs)),
                            "descriptive_only": True, "decision_if_it_counted": decide(lo, hi)}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=("design", "run"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--nsim", type=int, default=POWER_NSIM)
    args = ap.parse_args(argv)
    res = cmd_design(args) if args.command == "design" else cmd_run(args)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(json.dumps(res, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
