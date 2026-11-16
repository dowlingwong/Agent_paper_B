"""B2 instance count by the pre-declared rule ``docs/r1/proposals/B2_POWER_PLAN_RULE_20261114.md``.

ENGINEERING_ONLY; AI-assisted (Claude, Mac agent). Reads the B1 batch manifests (``b1_manifests.json``, sha checked),
builds the root-level final-Y proxy (mean of the last audited proposal's ``incumbent_metrics``) for every B1
thinking-off root of a registry candidate, pools the within-candidate between-instance variance per node, takes the
one-sided 80 % chi-square upper limit, and returns n_j = the smallest n >= 2 with t_{0.975,n-1} sqrt(k V_j / n) <=
sigma_node_j (k = 1 for one finalist, 2 for two or more), n = max_j n_j, and the cap status (n > 10 is a STOP for the
author; never clipped).

Usage: python r1/scripts/b2_power_plan.py --manifests <b1_manifests.json> --manifests-sha256 <sha>
       --e1-summary results/r1/pilot/E1_20261022T214606Z/summary.json --finalists gemma4_31b [--nodes ...]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np
from scipy.stats import chi2, t as student_t

CAP = 10
UCL_LEVEL = 0.80          # one-sided chi-square UCL
ALPHA = 0.05              # two-sided 95 % CI
H_IN_SIGMA_NODE = 1.0     # target half-width = 1 x sigma_node
NAMESPACE_MAX = 89        # instance seeds 9011..9099


def sha(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sigma_node(e1_summary: dict, node: str) -> float:
    """r1.c3.dataset.node_noise: median sd_joint over the node's material edits (all edits if none is material)."""
    edits = [e for e in e1_summary["nodes"][node]["edits"] if "sd_joint" in e]
    mats = [e for e in edits if e.get("material")] or edits
    return float(np.median([e["sd_joint"] for e in mats]))


def _trial(pid: str) -> int:
    m = re.search(r":t(\d+)$", pid)
    if not m:
        raise ValueError(f"proposal id without trial index: {pid}")
    return int(m.group(1))


def root_proxies(manifests: list[dict]) -> tuple[dict, dict]:
    """{(candidate, node): {instance: Y_r}} over thinking-off roots of registry candidates; and exclusion counts."""
    cells: dict[tuple[str, str], dict[str, float]] = {}
    excluded: dict[str, int] = {}
    for m in manifests:
        if m.get("role") != "candidate":
            continue
        roots = {}
        for p in m["audited_proposals"]:
            if p["mode"] != "off":
                continue
            key = (p["node"], p["instance_id"])
            if key not in roots or _trial(p["proposal_id"]) > _trial(roots[key]["proposal_id"]):
                roots[key] = p
        expected = [r for r in m.get("root_manifests", []) if "/b1/off/" in r]
        for path in expected:
            inst = Path(path).parent.name
            node = inst.split("__s")[0]
            if (node, inst) not in roots:
                excluded[node] = excluded.get(node, 0) + 1
        for (node, inst), p in roots.items():
            vals = [float(v) for v in p["incumbent_metrics"]]
            if len(vals) != 4 or not all(math.isfinite(v) for v in vals):
                raise ValueError(f"{m['candidate']} {inst}: incomplete incumbent metrics")
            cells.setdefault((m["candidate"], node), {})[inst] = sum(vals) / len(vals)
    return cells, excluded


def pooled_variance(cells: dict, node: str) -> dict:
    num = 0.0
    dof = 0
    roots = 0
    for (cand, n), ys in sorted(cells.items()):
        if n != node:
            continue
        roots += len(ys)
        if len(ys) >= 2:
            num += (len(ys) - 1) * float(np.var(list(ys.values()), ddof=1))
            dof += len(ys) - 1
    if dof == 0:
        raise ValueError(f"node {node}: no cell with two instances")
    v_hat = num / dof
    return {"roots": roots, "dof": dof, "V_hat": v_hat, "sd_hat": math.sqrt(v_hat),
            "V_ucl": v_hat * dof / float(chi2.ppf(1 - UCL_LEVEL, dof)),
            "sd_ucl": math.sqrt(v_hat * dof / float(chi2.ppf(1 - UCL_LEVEL, dof)))}


def n_required(V: float, h: float, k: int, n_max: int = 1000) -> int | None:
    for n in range(2, n_max + 1):
        if float(student_t.ppf(1 - ALPHA / 2, n - 1)) * math.sqrt(k * V / n) <= h:
            return n
    return None


def plan(manifests: list[dict], e1: dict, nodes: list[str], finalists: list[str]) -> dict:
    cells, excluded = root_proxies(manifests)
    k = 1 if len(finalists) == 1 else 2
    per = {}
    for node in nodes:
        pv = pooled_variance(cells, node)
        sig = sigma_node(e1, node)
        h = H_IN_SIGMA_NODE * sig
        nj = n_required(pv["V_ucl"], h, k)
        per[node] = {**pv, "excluded_roots_without_audit": excluded.get(node, 0), "sigma_node": sig, "h": h, "n_j": nj}
    ns = [v["n_j"] for v in per.values()]
    n = None if any(x is None for x in ns) else max(ns)
    status = "within_cap" if n is not None and n <= CAP else "STOP_author_decides"
    return {"rule": "docs/r1/proposals/B2_POWER_PLAN_RULE_20261114.md", "finalists": finalists, "k": k,
            "alpha": ALPHA, "ucl_level": UCL_LEVEL, "h_in_sigma_node": H_IN_SIGMA_NODE, "cap": CAP,
            "nodes": per, "n": n, "cap_status": status,
            "b2_instances_per_node": n if status == "within_cap" else None,
            "note": "n > cap is a STOP for the author and is never clipped" if status != "within_cap" else None}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifests", type=Path, required=True)
    ap.add_argument("--manifests-sha256", required=True)
    ap.add_argument("--e1-summary", type=Path, required=True)
    ap.add_argument("--finalists", nargs="+", required=True)
    ap.add_argument("--nodes", nargs="+", default=["digits_mlp", "openml_credit_approval", "openml_ionosphere"])
    a = ap.parse_args(argv)
    actual = sha(a.manifests)
    if actual != a.manifests_sha256:
        raise SystemExit(f"STOP: manifests sha256 {actual} != {a.manifests_sha256}")
    data = json.loads(a.manifests.read_text())
    if data.get("label") != "EXAM" or any(m.get("phase") != "b1" or m.get("status") != "COMPLETE" for m in data["manifests"]):
        raise SystemExit("STOP: complete EXAM B1 manifests required")
    out = plan(data["manifests"], json.loads(a.e1_summary.read_text()), a.nodes, a.finalists)
    out.update(manifests_sha256=actual, e1_summary_sha256=sha(a.e1_summary), script_sha256=sha(__file__),
               label="ENGINEERING_ONLY")
    print(json.dumps(out, indent=1, sort_keys=True))
    return 0 if out["cap_status"] == "within_cap" else 3


if __name__ == "__main__":
    raise SystemExit(main())
