"""X.7(c) appendix: C3 premises against proposer strength, from existing B1/B2 data (S2-M5).

AI-assisted (Claude). Declared in docs/r1/proposals/X7C_APPENDIX_DECLARATION_20261116.md before this script existed.
Reads only the files given on the command line (extracted read-only from the refs named in the declaration).

Quantities per row (thinking-off roots only):
  mu_hat  mean delta_audit over audited off proposals (checked against the B1 analysis);
  Q1      rule-skippable share = sum_r (trials_r - audited_r) / sum_r trials_r;
  Q2      sd(delta_audit, ddof=1) over audited off proposals (pooled; per-node sd descriptive);
  Q3      Brier score of p_delta_positive vs 1[delta_audit > 0] (log score secondary).
Paired cluster bootstrap over instance ids, B = 10,000, numpy.random.default_rng(20261116), percentile intervals.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

SEED = 20261116
B = 10_000
FINALIST = "gemma4_31b"
ANCHORS = ("random_valid", "scripted", "qwen25_coder_7b")
QUANTS = ("Q1", "Q2", "Q3")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def usage_trials(path: Path) -> dict:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| `"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        parts = cells[0].strip("`").split("/")
        if len(parts) != 4:
            continue
        cand, phase, mode, inst = parts
        if phase != "b1":
            raise SystemExit(f"STOP: unexpected phase in usage table: {cells[0]}")
        key = (cand, mode, inst)
        if key in out:
            raise SystemExit(f"STOP: duplicate usage row {key}")
        out[key] = int(cells[2])
    return out


def row_data(props: list[dict], trials: dict[str, int]) -> dict:
    """Per-cluster arrays for one row: cluster -> (trials, deltas, forecasts)."""
    clusters = {}
    for inst, t in trials.items():
        clusters[inst] = {"trials": t, "delta": [], "node": [], "p": [], "pd": []}
    for r in props:
        c = clusters.get(r["instance_id"])
        if c is None:
            raise SystemExit(f"STOP: audited proposal on an instance without a trial count: {r['instance_id']}")
        c["delta"].append(float(r["delta_audit"]))
        c["node"].append(r["node"])
        if r.get("p_delta_positive") is not None:
            p = float(r["p_delta_positive"])
            if not 0.0 <= p <= 1.0:
                raise SystemExit("STOP: forecast outside [0, 1]")
            c["p"].append(p)
            c["pd"].append(float(r["delta_audit"]))
    for c in clusters.values():
        if len(c["delta"]) > c["trials"]:
            raise SystemExit("STOP: more audited proposals than trials on a root")
    return clusters


def quantities(clusters: dict, ids: list[str]) -> dict:
    trials = sum(clusters[i]["trials"] for i in ids)
    deltas = [d for i in ids for d in clusters[i]["delta"]]
    audited = len(deltas)
    q1 = (trials - audited) / trials if trials else math.nan
    q2 = float(np.std(deltas, ddof=1)) if audited > 1 else math.nan
    ps = [p for i in ids for p in clusters[i]["p"]]
    pd = [d for i in ids for d in clusters[i]["pd"]]
    if ps:
        y = np.array([d > 0 for d in pd], float)
        p = np.array(ps)
        q3 = float(np.mean((p - y) ** 2))
        pc = np.clip(p, 1e-12, 1 - 1e-12)
        log = float(np.mean(np.where(y == 1, np.log(pc), np.log(1 - pc))))
    else:
        q3 = log = math.nan
    mu = float(np.mean(deltas)) if deltas else math.nan
    return {"Q1": q1, "Q2": q2, "Q3": q3, "log_score": log, "mu_hat": mu, "trials": trials, "audited": audited,
            "forecasts": len(ps)}


def per_node_sd(clusters: dict) -> dict:
    by = {}
    for c in clusters.values():
        for d, n in zip(c["delta"], c["node"]):
            by.setdefault(n, []).append(d)
    return {n: (float(np.std(v, ddof=1)) if len(v) > 1 else None) for n, v in sorted(by.items())}


def interval(values: np.ndarray, level: float) -> tuple[float, float, int]:
    ok = values[np.isfinite(values)]
    a = (1 - level) / 2
    lo, hi = np.quantile(ok, [a, 1 - a], method="linear")
    return float(lo), float(hi), int(values.size - ok.size)


def bootstrap(rows: dict[str, dict], ids: list[str], rng) -> dict[str, dict[str, np.ndarray]]:
    draws = {name: {q: np.empty(B) for q in ("Q1", "Q2", "Q3", "mu_hat")} for name in rows}
    n = len(ids)
    for b in range(B):
        sample = [ids[k] for k in rng.integers(0, n, n)]
        for name, cl in rows.items():
            q = quantities(cl, sample)
            for k in draws[name]:
                draws[name][k][b] = q[k]
    return draws


def spearman(x, y) -> float | None:
    pairs = [(a, b) for a, b in zip(x, y) if a is not None and b is not None and math.isfinite(a) and math.isfinite(b)]
    if len(pairs) < 3:
        return None
    xs, ys = zip(*pairs)
    rx = np.argsort(np.argsort(xs)).astype(float)
    ry = np.argsort(np.argsort(ys)).astype(float)
    return float(np.corrcoef(rx, ry)[0, 1])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--b1-manifests", type=Path, required=True)
    ap.add_argument("--b1-usage", type=Path, required=True)
    ap.add_argument("--b1-analysis", type=Path, required=True)
    ap.add_argument("--b2-manifests", type=Path, required=True)
    ap.add_argument("--b2-roots", type=Path, required=True, help="dir holding <instance>/campaign_manifest.json")
    ap.add_argument("--json", type=Path, required=True)
    a = ap.parse_args(argv)

    b1 = json.loads(a.b1_manifests.read_text())["manifests"]
    analysis = {r["candidate"]: r for r in json.loads(a.b1_analysis.read_text())["rows"]}
    usage = usage_trials(a.b1_usage)
    rows, meta = {}, {}
    ids_ref = None
    for m in b1:
        name = m["candidate"]
        if m.get("execution_label") != "EVIDENCE" or m.get("phase") != "b1" or m.get("status") != "COMPLETE":
            raise SystemExit(f"STOP: {name} is not a complete EVIDENCE B1 manifest")
        off_trials = {inst: t for (c, mode, inst), t in usage.items() if c == name and mode == "off"}
        all_trials = sum(t for (c, _m, _i), t in usage.items() if c == name)
        if len(off_trials) != 12:
            raise SystemExit(f"STOP: {name} has {len(off_trials)} off roots in the usage table")
        if all_trials != m["diagnostics"]["trials"]:
            raise SystemExit(f"STOP: {name} usage trials {all_trials} != manifest trials {m['diagnostics']['trials']}")
        ids = sorted(off_trials)
        ids_ref = ids_ref or ids
        if ids != ids_ref:
            raise SystemExit("STOP: rows do not share the same 12 instance ids")
        props = [r for r in m["audited_proposals"] if r["mode"] == "off"]
        rows[name] = row_data(props, off_trials)
        point = quantities(rows[name], ids)
        ref = analysis[name]
        if not math.isclose(point["mu_hat"], ref["mu_hat"], abs_tol=1e-12):
            raise SystemExit(f"STOP: {name} mu_hat {point['mu_hat']} != analysis {ref['mu_hat']}")
        meta[name] = {"role": m["role"], "point": point, "per_node_sd": per_node_sd(rows[name]),
                      "forecast_coverage": point["forecasts"] / point["audited"] if point["audited"] else None,
                      "analysis_mu_interval": [ref["cluster_interval"]["lower"], ref["cluster_interval"]["upper"]]}

    rng = np.random.default_rng(SEED)
    draws = bootstrap(rows, ids_ref, rng)
    for name in rows:
        meta[name]["ci95"] = {q: interval(draws[name][q], 0.95)[:2] for q in ("Q1", "Q2", "Q3", "mu_hat")
                              if np.isfinite(draws[name][q]).any()}

    comparisons = []
    level_b = 1 - 0.05 / 7
    for anchor in ANCHORS:
        for q in QUANTS:
            pf, pa = meta[FINALIST]["point"][q], meta[anchor]["point"][q]
            if not (math.isfinite(pf) and math.isfinite(pa)):
                continue
            diff = draws[FINALIST][q] - draws[anchor][q]
            lo, hi, nan = interval(diff, 0.95)
            blo, bhi, _ = interval(diff, level_b)
            comparisons.append({"anchor": anchor, "quantity": q, "finalist": pf, "anchor_value": pa,
                                "difference": pf - pa, "ci95": [lo, hi], "nan_resamples": nan,
                                "differs_beyond_ci": bool(lo > 0 or hi < 0),
                                "ci_bonferroni_7": [blo, bhi], "differs_bonferroni_7": bool(blo > 0 or bhi < 0)})
    if len(comparisons) != 7:
        raise SystemExit(f"STOP: expected 7 comparisons, got {len(comparisons)}")
    decision = "null" if not any(c["differs_beyond_ci"] for c in comparisons) else "differences"

    names = list(rows)
    mus = [meta[n]["point"]["mu_hat"] for n in names]
    rho = {q: spearman([meta[n]["point"][q] for n in names], mus) for q in QUANTS}

    # B2 replication (finalist only)
    b2 = json.loads(a.b2_manifests.read_text())["manifests"]
    if len(b2) != 1 or b2[0]["candidate"] != FINALIST:
        raise SystemExit("STOP: B2 manifests are not the single finalist")
    b2_trials, b2_root_sha = {}, {}
    for d in sorted(a.b2_roots.iterdir()):
        f = d / "campaign_manifest.json"
        rm = json.loads(f.read_text())
        if rm.get("mode") != "off" or rm.get("candidate") != FINALIST or rm.get("execution_label") != "EVIDENCE":
            raise SystemExit(f"STOP: unexpected B2 root manifest {f}")
        inst = f"{rm['node']}__s{rm['instance_seed']}"
        b2_trials[inst] = int(rm["diagnostics"]["trials"])
        b2_root_sha[inst] = sha(f)
    if len(b2_trials) != 12:
        raise SystemExit("STOP: B2 needs 12 off roots")
    b2_props = [r for r in b2[0]["audited_proposals"] if r["mode"] == "off"]
    b2_rows = {FINALIST: row_data(b2_props, b2_trials)}
    b2_ids = sorted(b2_trials)
    b2_point = quantities(b2_rows[FINALIST], b2_ids)
    b2_draws = bootstrap(b2_rows, b2_ids, np.random.default_rng(SEED))
    b2_ci = {q: interval(b2_draws[FINALIST][q], 0.95)[:2] for q in ("Q1", "Q2", "Q3", "mu_hat")}

    res = {"declaration": "docs/r1/proposals/X7C_APPENDIX_DECLARATION_20261116.md", "seed": SEED, "resamples": B,
           "python": sys.version.split()[0], "numpy": np.__version__,
           "inputs": {"b1_manifests": sha(a.b1_manifests), "b1_usage": sha(a.b1_usage),
                      "b1_analysis": sha(a.b1_analysis), "b2_manifests": sha(a.b2_manifests),
                      "b2_root_manifests": b2_root_sha},
           "instance_ids_b1": ids_ref, "rows": meta, "comparisons": comparisons, "decision": decision,
           "spearman_vs_mu_hat": rho,
           "b2_replication": {"instance_ids": b2_ids, "point": b2_point, "ci95": b2_ci,
                              "per_node_sd": per_node_sd(b2_rows[FINALIST]),
                              "audit_seeds_k": sorted({len(r["audit_seeds"]) for r in b2_props})}}
    a.json.write_text(json.dumps(res, indent=1, sort_keys=True), encoding="utf-8")

    def f(x, nd=4):
        return "–" if x is None or (isinstance(x, float) and not math.isfinite(x)) else f"{x:.{nd}f}"
    out = ["## Comparisons for the null decision (finalist gemma4_31b − anchor; 95 % paired cluster bootstrap)", "",
           "| anchor | quantity | finalist | anchor | difference | 95 % CI | beyond CI | Bonferroni(7) CI |",
           "|---|---|---|---|---|---|---|---|"]
    for c in comparisons:
        out.append(f"| {c['anchor']} | {c['quantity']} | {f(c['finalist'])} | {f(c['anchor_value'])} | {f(c['difference'])} | "
                   f"[{f(c['ci95'][0])}, {f(c['ci95'][1])}] | {'yes' if c['differs_beyond_ci'] else 'no'} | "
                   f"[{f(c['ci_bonferroni_7'][0])}, {f(c['ci_bonferroni_7'][1])}] |")
    out += ["", f"**Decision by the declared rule: {decision}.**", "",
            "## All B1 rows, ordered by mu_hat (thinking off; 95 % cluster intervals)", "",
            "| row | role | mu_hat [CI] | Q1 skip share [CI] | Q2 sd [CI] | Q3 Brier [CI] | log score | forecast coverage | audited / trials |",
            "|---|---|---|---|---|---|---|---|---|"]
    for n in sorted(names, key=lambda n: meta[n]["point"]["mu_hat"], reverse=True):
        p, ci = meta[n]["point"], meta[n]["ci95"]
        def c(q, nd=4):
            return f"{f(p[q], nd)} [{f(ci[q][0], nd)}, {f(ci[q][1], nd)}]" if q in ci and math.isfinite(p[q]) else "–"
        out.append(f"| {n} | {meta[n]['role']} | {c('mu_hat', 5)} | {c('Q1', 3)} | {c('Q2')} | {c('Q3', 3)} | "
                   f"{f(p['log_score'], 3)} | {f(meta[n]['forecast_coverage'], 2)} | {p['audited']} / {p['trials']} |")
    out += ["", "Spearman rho with mu_hat across rows (descriptive): " +
            ", ".join(f"{q} {f(rho[q], 2)}" for q in QUANTS), "",
            "## B2 replication (gemma4_31b, thinking off, s9011-s9014; K = 10 audits)", "",
            "| quantity | B1 | B2 [95 % CI] |", "|---|---|---|"]
    for q, nd in (("mu_hat", 5), ("Q1", 3), ("Q2", 4), ("Q3", 3)):
        out.append(f"| {q} | {f(meta[FINALIST]['point'][q], nd)} | {f(b2_point[q], nd)} [{f(b2_ci[q][0], nd)}, {f(b2_ci[q][1], nd)}] |")
    out += ["", "Per-node sd (Q2 secondary): B1 finalist " + json.dumps(meta[FINALIST]["per_node_sd"]) +
            "; B2 " + json.dumps(per_node_sd(b2_rows[FINALIST]))]
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
