"""Build the C3 proposal table from root ledgers (C3_DESIGN §3-4). ENGINEERING_ONLY; AI-assisted (Claude).

Sources (roots only; no branch ledgers):
- ``dt4``      results/r1/pilot/E1b_20261013T151857Z            (memory none, W = 20)
- ``rerun2A``  results/r1/pilot/E1b_rerun2_A_PARTIAL_memory_on_20261014 (memory on, W = 20; PARTIAL)
- ``liveness`` results/r1/engineering/liveness_llm_20261014T140742Z    (memory on, W = 10)

Usage:
  python -m r1.c3.dataset build --out DIR
  python -m r1.c3.dataset plan  --table DIR [--quota rerun2A:tabular_mlp:70 ...] [--di]

``build`` writes DIR/proposals.jsonl (features, logged Delta_hat, decision, inert
flag, instance, node, memory mode, config hashes), DIR/configs.json (file texts
by hash) and DIR/build.json (sources, replay checks, noise table). ``plan``
writes DIR/plan.jsonl: a seeded random audit sample of non-inert proposals per
(source, node) stratum, plus (``--di``) the DI-changed candidates.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import subprocess
from pathlib import Path

import numpy as np

from r1.c3.features import (NODE_INFO, Proposal, configuration, files_hash, normalise_files, read_jsonl,
                            replay_campaign)
from r1.harness import REPO, harness_root

E1_SUMMARY = "results/r1/pilot/E1_20261012T145353Z/summary.json"
SOURCES = {
    "dt4": {"dir": "results/r1/pilot/E1b_20261013T151857Z", "ledgers": "provenance/ledgers/roots/*/root_trials.jsonl*",
            "runs": 20, "memory_mode": "none"},
    "rerun2A": {"dir": "results/r1/pilot/E1b_rerun2_A_PARTIAL_memory_on_20261014",
                "ledgers": "provenance/ledgers/roots/*/root_trials.jsonl*", "runs": 20,
                "memory_mode": "append_only_summary"},
    "liveness": {"dir": "results/r1/engineering/liveness_llm_20261014T140742Z", "ledgers": "ledgers/*/root_trials.jsonl",
                 "runs": 10, "memory_mode": "append_only_summary"},
}
# Decision-changed E2 points of the DI analyses (docs/r1/reports/
# DI_TEST_MEMORY_ON_PARTIAL_20261019_tables.md, "Decision audit"): the root trial
# at budget index b is the candidate; it was compared against the E2 incumbent.
DI_CHANGED = {
    "rerun2A": [("tabular_mlp__s102", 12, "promotion"), ("tabular_mlp__s112", 8, "promotion"),
                ("tabular_mlp__s112", 12, "promotion"), ("tabular_mlp__s122", 12, "demotion"),
                ("tabular_mlp__s132", 8, "promotion"), ("tabular_mlp__s152", 8, "promotion"),
                ("tabular_mlp__s152", 12, "promotion"), ("tabular_mlp__s182", 4, "demotion"),
                ("tabular_mlp__s182", 8, "promotion"), ("tabular_mlp__s202", 4, "demotion"),
                ("tabular_mlp__s232", 4, "demotion"), ("tabular_mlp__s252", 8, "promotion"),
                ("tabular_mlp__s252", 12, "promotion")],
    "dt4": [("digits_mlp__s104", 8, "promotion"), ("digits_mlp__s104", 12, "promotion"),
            ("digits_mlp__s114", 8, "promotion"), ("digits_mlp__s134", 8, "promotion"),
            ("digits_mlp__s144", 4, "promotion"), ("digits_mlp__s144", 8, "promotion")],
}
DEFAULT_QUOTA = {("rerun2A", "tabular_mlp"): 70, ("rerun2A", "openml_breast_w"): 54, ("dt4", "digits_mlp"): 26}
PLAN_SEED = 20261019


def noise_table(summary_path: Path | str = REPO / E1_SUMMARY) -> dict:
    """Per-node noise constants from the E1 summary.

    sigma_node: median sd_joint over material edits (the e1b ``sigma_d`` definition);
    used to standardise z = Delta / sigma_node.
    sigma_local / sigma_structural: median sd_joint over local / model_type edits
    (comparison noise per edit kind, T4 (A2)); MLP nodes have only local edits and
    use sigma_node.
    delta_n (D18): max(0.002, 0.25 x median paired sd over all E1 edits).

    Nodes in NODE_INFO that the summary does not cover (e.g. the 22 Oct pool
    extension before its E1 run) get no entry, so any later use of them fails
    loudly with a KeyError instead of being given invented constants.
    """
    s = json.loads(Path(summary_path).read_text())
    out = {}
    for node in (n for n in NODE_INFO if n in s["nodes"]):
        edits = [e for e in s["nodes"][node]["edits"] if "sd_joint" in e]
        mats = [e for e in edits if e.get("material")] or edits
        sig = float(np.median([e["sd_joint"] for e in mats]))
        struct = [e["sd_joint"] for e in edits if e["edit"].startswith("model_type")]
        local = [e["sd_joint"] for e in edits if not e["edit"].startswith("model_type")]
        med_all = float(np.median([e["sd_joint"] for e in edits]))
        fam = NODE_INFO[node]["family"]
        out[node] = {"sigma_node": sig,
                     "sigma_local": float(np.median(local)) if fam == "openml" and local else sig,
                     "sigma_structural": float(np.median(struct)) if fam == "openml" and struct else sig,
                     "median_sd_all": med_all, "delta_n": max(0.002, 0.25 * med_all)}
    return out


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def _start_files(src_dir: Path, inst: str, node: str) -> dict:
    rj = src_dir / "roots" / f"{inst}.json"
    if rj.exists():
        return json.loads(rj.read_text())["start_files"]
    # liveness runs store no start files; same harness commit (411c605) -> node files.
    path = "train.py" if NODE_INFO[node]["family"] == "mlp" else "config.yaml"
    return {path: (harness_root() / "nodes" / node / path).read_text()}


def build(out: Path, sources=tuple(SOURCES)) -> dict:
    noise = noise_table()
    out.mkdir(parents=True, exist_ok=True)
    rows, configs, checks = [], {}, {}
    for name in sources:
        src = SOURCES[name]
        d = REPO / src["dir"]
        for f in sorted(glob.glob(str(d / src["ledgers"]))):
            inst = Path(f).parent.name
            node = inst.split("__s")[0]
            props, ch = replay_campaign(read_jsonl(Path(f)), _start_files(d, inst, node), node, inst, name,
                                        src["memory_mode"], src["runs"], noise[node]["sigma_node"])
            checks[f"{name}:{inst}"] = ch
            for p in props:
                configs[p.candidate_hash] = {"node": node, "files": p.candidate_files}
                configs[p.incumbent_hash] = {"node": node, "files": p.incumbent_files}
                rows.append(row_of(p, noise))
    with open(out / "proposals.jsonl", "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    (out / "configs.json").write_text(json.dumps(configs))
    tot = {k: sum(c[k] for c in checks.values()) for k in next(iter(checks.values()))}
    meta = {"label": "ENGINEERING_ONLY", "ai_assisted": "AI-assisted (Claude)", "commit": git_head(),
            "sources": {k: SOURCES[k] for k in sources}, "noise": noise, "replay_checks_total": tot,
            "replay_checks": checks, "n_proposals": len(rows), "n_configs": len(configs)}
    (out / "build.json").write_text(json.dumps(meta, indent=1))
    return meta


def row_of(p: Proposal, noise: dict) -> dict:
    key = p.edit.get("symbol")
    kind = "structural" if key == "model_type" else "local"
    sigma = noise[p.node]["sigma_structural" if kind == "structural" else "sigma_local"]
    return {"proposal_id": p.proposal_id, "instance": p.instance, "instance_seed": p.instance_seed,
            "node": p.node, "source": p.source, "memory_mode": p.memory_mode, "budget_index": p.budget_index,
            "edit": p.edit, "edit_kind": kind, "sigma_node": noise[p.node]["sigma_node"], "sigma_cmp": sigma,
            "features": p.features, **p.outcome,
            "candidate_hash": p.candidate_hash, "incumbent_hash": p.incumbent_hash}


def load_table(table_dir: Path) -> list[dict]:
    return [json.loads(x) for x in (Path(table_dir) / "proposals.jsonl").read_text().splitlines() if x.strip()]


def di_candidates(rows: list[dict]) -> list[dict]:
    """Locate the DI-changed candidates and check them against the E2 snapshots."""
    by_id = {r["proposal_id"]: r for r in rows}
    found = []
    for source, pts in DI_CHANGED.items():
        sdir = REPO / SOURCES[source]["dir"]
        for inst, b, direction in pts:
            pid = f"{source}:{inst}:t{b:03d}"
            r = by_id[pid]
            want = "discarded" if direction == "promotion" else "kept"
            if r["decision"] != want:
                raise ValueError(f"{pid}: root decision {r['decision']} inconsistent with {direction}")
            snap = sdir / "provenance" / "snapshots" / inst / f"E2_b{b:03d}"
            man = json.loads((snap / "manifest.json").read_text())
            snap_inc = configuration(normalise_files({p: (snap / "incumbent" / p).read_text() for p in man["editable_paths"]}))
            found.append({**r, "di_direction": direction, "snapshot_incumbent_config": snap_inc})
    return found


def plan(table_dir: Path, quota: dict, include_di: bool, seed: int = PLAN_SEED) -> list[dict]:
    rows = load_table(table_dir)
    configs = json.loads((Path(table_dir) / "configs.json").read_text())
    rng = np.random.default_rng(seed)
    chosen: dict[str, dict] = {}
    for (source, node), n in quota.items():
        pool = sorted([r for r in rows if r["source"] == source and r["node"] == node and not r.get("rule_skip", r["inert"])],
                      key=lambda r: r["proposal_id"])
        idx = rng.permutation(len(pool))[:n]
        for i in sorted(idx):
            r = pool[i]
            chosen[r["proposal_id"]] = {"proposal_id": r["proposal_id"], "node": node, "reason": "random",
                                        "candidate_hash": r["candidate_hash"], "incumbent_hash": r["incumbent_hash"]}
    if include_di:
        for r in di_candidates(rows):
            inc_cfg = configuration(configs[r["incumbent_hash"]]["files"])
            if inc_cfg != r["snapshot_incumbent_config"]:
                raise ValueError(f"{r['proposal_id']}: replayed incumbent differs from E2 snapshot")
            if r["proposal_id"] in chosen:
                chosen[r["proposal_id"]]["reason"] = "random+di"
            else:
                chosen[r["proposal_id"]] = {"proposal_id": r["proposal_id"], "node": r["node"], "reason": "di",
                                            "candidate_hash": r["candidate_hash"], "incumbent_hash": r["incumbent_hash"]}
            chosen[r["proposal_id"]]["di_direction"] = r["di_direction"]
            chosen[r["proposal_id"]]["di_inert"] = r["inert"]
            chosen[r["proposal_id"]]["di_duplicate"] = r.get("duplicate")
    return list(chosen.values())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--out", required=True)
    b.add_argument("--sources", nargs="+", default=list(SOURCES))
    p = sub.add_parser("plan")
    p.add_argument("--table", required=True)
    p.add_argument("--out", default=None)
    p.add_argument("--quota", nargs="*", default=None, help="source:node:n entries")
    p.add_argument("--di", action="store_true")
    args = ap.parse_args(argv)
    if args.cmd == "build":
        meta = build(Path(args.out), tuple(args.sources))
        print(json.dumps({"n_proposals": meta["n_proposals"], "checks": meta["replay_checks_total"]}))
    else:
        quota = DEFAULT_QUOTA if args.quota is None else {
            (q.split(":")[0], q.split(":")[1]): int(q.split(":")[2]) for q in args.quota}
        rows = plan(Path(args.table), quota, args.di)
        out = Path(args.out) if args.out else Path(args.table) / "plan.jsonl"
        out.write_text("".join(json.dumps(r) + "\n" for r in rows))
        print(json.dumps({"planned": len(rows), "di": sum("di" in r["reason"] for r in rows)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
