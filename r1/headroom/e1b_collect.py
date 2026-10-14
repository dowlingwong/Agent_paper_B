#!/usr/bin/env python3
"""E1b pilot headroom pre-check: collect a small E2 sibling table (RUNBOOK 0.4b; label PILOT).

Phases, all resumable and time-boxed (``--deadline``):

A. Root campaigns. One per instance (node, seed). The harness runs them with
   the default controller, a hard compute budget of W worker runs, verify
   r = 2 under the decided ``"fixed"`` split policy, and a scripted proposer
   (repetition 0). Instance seeds set the campaign's own training and split
   seeds. A snapshot hook writes an E2 snapshot at the chosen budget indices
   when the candidate is valid.
B. Branches. For each snapshot, each feasible E2 action in {continue, verify}
   and repetitions 1..R: restore with ``resume_campaign``, force the action,
   and continue under the default rule until the compute budget is spent,
   with the proposer at that repetition.
C. Audit. The final incumbent of every leaf, and the start configuration c0 of
   every instance, run at K common fresh joint seeds. Y = mean audit(final) -
   mean audit(c0), in metric units (all metrics here lie in [0, 1]).

Output under ``results/r1/pilot/E1b_<UTC>/``: ``records.jsonl`` (r1_branch_v1
records), ``points.json`` (decision-point features), ``manifest.json``.
Scratch work goes under ``--work`` (outside the repo).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from r1.harness import REPO, harness_commit, import_harness

HARNESS = import_harness()

from autoresearch.control_plane.budget import ComputeBudget  # noqa: E402
from autoresearch.control_plane.campaign import run_real_campaign  # noqa: E402
from autoresearch.control_plane.snapshot import capture_snapshot, read_snapshot, resume_campaign, write_snapshot  # noqa: E402
from autoresearch.manager.base import ManagerProposal  # noqa: E402
from autoresearch.memory.event_store import CampaignEventStore  # noqa: E402
from autoresearch.nodes.registry import load_registered_node  # noqa: E402
from autoresearch.worker.local_worker import LocalWorker  # noqa: E402

from r1.branch.schema import R1_BRANCH_SCHEMA, BranchRecord, Leaf, record_to_dict  # noqa: E402
from r1.headroom.scripted_manager import ScriptedRandomManager  # noqa: E402

MANAGER = {"kind": "scripted", "model": "ollama/qwen2.5-coder:7b", "temperature": 0.2}


def make_manager(node: str, seed: int, repetition: int, manifest_manager: dict | None = None):
    """Scripted stand-in (default) or the pinned LangGraph/Ollama manager (``--manager langgraph``, Mac only)."""
    cfg = manifest_manager or MANAGER
    if cfg.get("kind") == "langgraph":
        from autoresearch.manager.langgraph_manager import LangGraphManager
        # D26: the branch repetition enters the deterministic per-call Ollama seed.
        return LangGraphManager(model=cfg["model"], temperature=float(cfg["temperature"]),
                                repetition=repetition)
    return ScriptedRandomManager(node, seed=seed, repetition=repetition)


def seed_policy(manager_kind: str) -> dict:
    """The manifest's record of how proposer sampling is seeded (D26)."""
    if manager_kind == "langgraph":
        return {"kind": "ollama_seed", "temperature": 0.2,
                "derivation": "manager_seed(campaign_id, budget_index, repetition, revision_attempt)"}
    return {"kind": "numpy_pcg64",
            "derivation": "default_rng([instance_seed, repetition, budget_index])"}


PILOT_DATA_CACHE = "experiments/r1/pilot/L8_20261009T152916Z/nodes/{node}/data_cache"
AUDIT_SEED_BASE = 5001
VERIFY_R = 2


def _node_copy(node: str, dest: Path) -> Path:
    shutil.copytree(HARNESS / "nodes" / node, dest, ignore=shutil.ignore_patterns("__pycache__", ".autoresearch_artifacts"))
    if node.startswith("openml_") and not (dest / "data_cache").exists():
        cache = HARNESS / PILOT_DATA_CACHE.format(node=node)
        if cache.exists():
            shutil.copytree(cache, dest / "data_cache")
    return dest


def _instance_seed(node: str, k: int) -> int:
    return 100 + 10 * k + (sum(map(ord, node)) % 7)


class E2Recorder:
    """Snapshot hook: write an E2 snapshot at each chosen budget index whose candidate is valid."""

    def __init__(self, out_dir: Path, indices: set[int]) -> None:
        self.out_dir, self.indices, self.written = out_dir, indices, []

    def __call__(self, context) -> None:
        if context.epoch != "E2" or context.budget_index not in self.indices:
            return
        wr = context.worker_result
        if wr is None or not wr.success or context.current_best is None:
            return
        snap = capture_snapshot(context)
        target = self.out_dir / f"E2_b{context.budget_index:03d}"
        write_snapshot(snap, target)
        self.written.append(str(target))


# ---------------------------------------------------------------------------
# Phase A
# ---------------------------------------------------------------------------

def run_root(node: str, k: int, work: str, runs: int, indices: list[int], manager: dict | None = None,
             split_policy: str = "fixed", memory_mode: str = "none") -> dict:
    """Run one root campaign.  ``memory_mode`` comes from the manifest (D24); a manifest
    without the field means ``none`` (historical runs)."""
    seed = _instance_seed(node, k)
    inst = f"{node}__s{seed}"
    root = Path(work) / "roots" / inst
    if root.exists():
        shutil.rmtree(root)
    node_dir = _node_copy(node, root / "node")
    spec = load_registered_node(node, repo_root=HARNESS)
    worker = LocalWorker(node_root=node_dir, artifact_dir=root / "art", train_seed=seed, split_seed=seed)
    recorder = E2Recorder(root / "snapshots", set(indices))
    run_real_campaign(
        node_spec=spec, campaign_id=inst, budget=runs * 2, manager_mode="baseline_manager",
        memory_mode=memory_mode,
        records_path=root / "root_trials.jsonl", worker=worker,
        proposal_backend=make_manager(node, seed, 0, manager),
        compute_budget=ComputeBudget(max_worker_runs=runs), verify_runs=VERIFY_R,
        verify_split_policy=split_policy, snapshot_hook=recorder,
        # D28 revised criterion 2: persist the campaign event stream so the
        # liveness check can score active-key novelty from edit_novelty events
        # instead of replaying structured edits.
        event_store=CampaignEventStore(root / "root_events.jsonl"),
    )
    return {"instance": inst, "node": node, "seed": seed, "snapshots": recorder.written,
            "start_files": {p: (HARNESS / "nodes" / node / p).read_text() for p in spec.editable_paths}}


# ---------------------------------------------------------------------------
# Phase B + C
# ---------------------------------------------------------------------------

def _audit(node: str, files: dict[str, str], seeds: list[int], work: Path) -> list[float | None]:
    spec = load_registered_node(node, repo_root=HARNESS)
    d = work / ("audit_" + hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()[:16] + f"_{os.getpid()}")
    if d.exists():
        shutil.rmtree(d)
    node_dir = _node_copy(node, d)
    for rel, text in files.items():
        (node_dir / rel).write_text(text)
    worker = LocalWorker(node_root=node_dir, artifact_dir=d / "art")
    noedit = ManagerProposal(manager_mode="audit", proposal_summary="audit", proposal_rationale="",
                             target_files=spec.editable_paths, objective="Audit run; no change.")
    out = []
    for i, s in enumerate(seeds):
        res = worker.run_trial_at_seed(noedit, spec, i + 1, train_seed=s, split_seed=s)
        out.append(res.parsed_metrics.get(spec.metric_name) if res.success else None)
    shutil.rmtree(d, ignore_errors=True)
    return out


def audit_start(node: str, inst: str, start_files: dict[str, str], k_audit: int, work: str, out_dir: str) -> dict:
    path = Path(out_dir) / "audits" / f"{inst}__c0.json"
    seeds = [AUDIT_SEED_BASE + i for i in range(k_audit)]
    vals = _audit(node, start_files, seeds, Path(work))
    payload = {"instance": inst, "seeds": seeds, "metrics": vals}
    path.write_text(json.dumps(payload))
    return payload


def run_leaf(snapshot_dir: str, inst: str, node: str, action: str, rep: int, seed: int, k_audit: int,
             work: str, out_dir: str, manager: dict | None = None) -> dict:
    snap = read_snapshot(snapshot_dir)
    leaf_id = f"{inst}__b{snap.budget_index:03d}__{action}__r{rep}"
    into = Path(work) / "branches" / leaf_id
    if into.exists():
        shutil.rmtree(into)
    t0 = time.perf_counter()
    status, err = "ok", None
    try:
        result = resume_campaign(snap, into, first_action=action, horizon=200,
                                 manager=make_manager(node, seed, rep, manager))
        executed = (result.first_record.extra.get("control", {}) or {}).get("action") if result.first_record else None
        records = [json.loads(l) for l in result.restored.records_path.read_text().splitlines() if l.strip()]
        new = records[len(snap.ledger_prefix):]
        runs = 0
        for idx, r in enumerate(new):
            if r.get("decision") == "skipped":
                continue
            if idx > 0:  # the captured trial's own run was spent before the snapshot
                runs += 1
            v = ((r.get("extra") or {}).get("control") or {}).get("verify")
            if v:
                runs += 2 * int(v.get("r", VERIFY_R))
        spec = load_registered_node(node, repo_root=HARNESS)
        final_files = {p: (into / p).read_text() for p in spec.editable_paths}
        seeds = [AUDIT_SEED_BASE + i for i in range(k_audit)]
        audit = _audit(node, final_files, seeds, Path(work))
        n_keeps = sum(1 for r in new if r.get("decision") == "kept")
    except Exception as exc:  # noqa: BLE001 - a failed leaf is an integrity status, never a utility
        status, err, executed, runs, audit, n_keeps, final_files = "collection_failure", repr(exc), None, 0, [], 0, {}
    payload = {"leaf_id": leaf_id, "instance": inst, "node": node, "budget_index": snap.budget_index,
               "action": action, "repetition": rep, "executed_action": executed, "integrity": status,
               "error": err, "cost_worker_runs": runs, "n_keeps_after": n_keeps, "audit_metrics": audit,
               "final_files_hash": hashlib.sha256(json.dumps(final_files, sort_keys=True).encode()).hexdigest()[:16],
               "wall_seconds": round(time.perf_counter() - t0, 2)}
    (Path(out_dir) / "leaves" / f"{leaf_id}.json").write_text(json.dumps(payload))
    # Preserve branch ledgers and events for manager/proposal provenance audits.
    return payload


def point_features(snapshot_dir: str, node: str, noise: dict, runs_total: int) -> dict:
    snap = read_snapshot(snapshot_dir)
    spec = load_registered_node(node, repo_root=HARNESS)
    metric = snap.worker_result.parsed_metrics.get(spec.metric_name)
    remaining = runs_total - int(snap.compute_budget_state.get("worker_runs", 0))
    n_keeps = sum(1 for r in snap.ledger_prefix if getattr(r.decision, "value", r.decision) == "kept")
    sign = -1.0 if spec.metric_direction == "minimize" else 1.0
    feats = {"node": node, "delta_hat": sign * float(metric - snap.current_best), "sigma_d": noise["sigma_d"],
             "sigma_t": noise["sigma_t"], "sigma_s": noise["sigma_s"], "remaining_runs": float(remaining),
             "total_runs": float(runs_total), "budget_index": float(snap.budget_index), "n_keeps": float(n_keeps),
             "repeated_bad": 0.0, "r": float(VERIFY_R), "split_policy": snap.verify_split_policy}
    mask = {"continue": True, "verify": bool(remaining >= 2 * VERIFY_R)}
    return {"features": feats, "mask": mask, "snapshot_hash": snap.layer_hashes.get("editable", "") or
            hashlib.sha256(snapshot_dir.encode()).hexdigest()[:16], "budget_index": snap.budget_index}


def node_noise(e1_summary: Path, node: str) -> dict:
    """Paired-comparison noise of a node from E1 (development constants).

    sigma_d is the median *joint* sd of the paired difference over material
    edits. E1 shows sd_joint^2 < sd_train^2 + sd_split^2 on these nodes (the two
    seed effects are not additive), so hypot(sd_train, sd_split) would overstate
    it (L14 finding 14). sigma_t and sigma_s keep their measured ratio and are
    rescaled so that hypot(sigma_t, sigma_s) = sigma_d.
    """
    info = json.loads(Path(e1_summary).read_text())["nodes"][node]
    mats = [e for e in info["edits"] if e.get("material")] or [e for e in info["edits"] if "sd_joint" in e]
    sd = float(np.median([e["sd_joint"] for e in mats]))
    st = float(np.median([e["sd_train"] for e in mats]))
    ss = float(np.median([e["sd_split"] for e in mats]))
    scale = sd / float(np.hypot(st, ss)) if np.hypot(st, ss) > 0 else 0.0
    return {"sigma_t": st * scale, "sigma_s": ss * scale, "sigma_d": sd, "source": str(e1_summary),
            "definition": "median sd_joint; components rescaled (v2)"}


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nodes", nargs="+", default=["digits_mlp", "openml_ionosphere"])
    ap.add_argument("--instances", type=int, default=6)
    ap.add_argument("--runs", type=int, default=20, help="compute budget W (worker runs) per campaign")
    ap.add_argument("--points", type=int, nargs="+", default=[4, 8, 12], help="E2 budget indices to branch")
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--audit-seeds", type=int, default=6)
    ap.add_argument("--e1-summary", default=None, help="E1 summary.json for node noise (dev constants)")
    ap.add_argument("--resume", default=None)
    ap.add_argument("--verify-split-policy", choices=["fixed", "vary"], default="fixed",
                    help='"fixed" is the 9 Oct author decision; "vary" is a sensitivity run (T2 Proposition 3)')
    ap.add_argument("--label", default="PILOT")
    ap.add_argument("--split", default="pilot")
    ap.add_argument("--manager", choices=["scripted", "langgraph"], default="scripted",
                    help="langgraph = the pinned local qwen2.5-coder:7b via Ollama (run natively on the Mac)")
    ap.add_argument("--memory-mode", choices=["none", "append_only_summary", "append_only_summary_with_rationale"],
                    default=None, help="manager memory mode (D24); a manifest without the field means none")
    ap.add_argument("--arm", choices=["A", "B", "C"], default=None,
                    help="rerun-2 arm label (R1-E1B-RERUN2; manifest field)")
    ap.add_argument("--arm-role", choices=["primary", "contrast", "reference"], default=None,
                    help="rerun-2 arm role (R1-E1B-RERUN2; manifest field)")
    ap.add_argument("--out", default=None, help="output dir for a new run (default results/r1/pilot/E1b_<UTC>)")
    ap.add_argument("--work", default=os.environ.get("R1_TMP", "/tmp/r1_e1b"))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--deadline", type=float, default=1e9)
    args = ap.parse_args()

    if args.resume:
        out = Path(args.resume)
        manifest = json.loads((out / "manifest.json").read_text())
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out = Path(args.out) if args.out else REPO / "results" / "r1" / "pilot" / f"E1b_{stamp}"
        out.mkdir(parents=True)
        e1 = Path(args.e1_summary) if args.e1_summary else max((REPO / "results/r1/pilot").glob("E1_*/summary.json"))
        manifest = {"schema": "r1.e1b_headroom/1", "label": args.label, "split": args.split, "started_utc": stamp,
                    "harness": {"root": str(HARNESS), **harness_commit(HARNESS)},
                    "manager_backend": ("scripted_random (stand-in; VM cannot reach Ollama)" if args.manager == "scripted"
                                        else "langgraph qwen2.5-coder:7b (Ollama; pinned digest dae161e2...)"),
                    "manager": {**MANAGER, "kind": args.manager},
                    "memory_mode": args.memory_mode or "none",
                    "arm": args.arm,
                    "arm_role": args.arm_role,
                    "seed_policy": seed_policy(args.manager),
                    "nodes": args.nodes, "instances": args.instances, "runs": args.runs, "points": args.points,
                    "reps": args.reps, "audit_seeds": args.audit_seeds, "verify_r": VERIFY_R,
                    "verify_split_policy": args.verify_split_policy,
                    "noise": {n: node_noise(e1, n) for n in args.nodes},
                    "host": {"platform": platform.platform(), "python": platform.python_version()},
                    "work": args.work, "sessions": []}
    for sub in ("leaves", "audits", "roots"):
        (out / sub).mkdir(exist_ok=True)
    work = Path(manifest["work"])
    work.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    session = {"start_utc": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"), "done": 0}

    jobs = []  # (kind, args)
    for node in manifest["nodes"]:
        for k in range(manifest["instances"]):
            inst = f"{node}__s{_instance_seed(node, k)}"
            root_json = out / "roots" / f"{inst}.json"
            if not root_json.exists():
                jobs.append(("root", (node, k, str(work), manifest["runs"], manifest["points"], manifest.get("manager"),
                                      str(manifest.get("verify_split_policy", "fixed")).split(" ")[0],
                                      str(manifest.get("memory_mode", "none")))))
                continue
            root = json.loads(root_json.read_text())
            if not (out / "audits" / f"{inst}__c0.json").exists():
                jobs.append(("audit0", (node, inst, root["start_files"], manifest["audit_seeds"], str(work), str(out))))
            for snap_dir in root["snapshots"]:
                if not Path(snap_dir).exists():
                    continue
                pf = point_features(snap_dir, node, manifest["noise"][node], manifest["runs"])
                actions = ["continue"] + (["verify"] if pf["mask"]["verify"] else [])
                for action in actions:
                    for rep in range(1, manifest["reps"] + 1):
                        leaf_id = f"{inst}__b{pf['budget_index']:03d}__{action}__r{rep}"
                        if not (out / "leaves" / f"{leaf_id}.json").exists():
                            jobs.append(("leaf", (snap_dir, inst, node, action, rep, root["seed"],
                                                  manifest["audit_seeds"], str(work), str(out), manifest.get("manager"))))
    pending = {}
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        queue = list(jobs)
        while queue or pending:
            while queue and len(pending) < args.workers and time.time() - t0 < args.deadline:
                kind, a = queue.pop(0)
                fn = {"root": run_root, "audit0": audit_start, "leaf": run_leaf}[kind]
                pending[pool.submit(fn, *a)] = kind
            if not pending:
                break
            done = [f for f in pending if f.done()]
            if not done:
                time.sleep(0.1)
                continue
            for f in done:
                kind = pending.pop(f)
                res = f.result()
                if kind == "root":
                    (out / "roots" / f"{res['instance']}.json").write_text(json.dumps(res))
                session["done"] += 1
    session.update({"jobs_before": len(jobs), "elapsed_seconds": round(time.time() - t0, 1)})
    manifest["sessions"].append(session)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"out": str(out), **session}))
    return 0


def build_records(out: Path) -> tuple[list[BranchRecord], list[dict]]:
    """Assemble r1_branch_v1 records from roots, leaves and start audits."""
    manifest = json.loads((out / "manifest.json").read_text())
    noise = {n: node_noise(Path(v["source"]), n) for n, v in manifest["noise"].items()}  # v2 definition
    records, points = [], []
    for root_json in sorted((out / "roots").glob("*.json")):
        root = json.loads(root_json.read_text())
        inst, node = root["instance"], root["node"]
        a0 = json.loads((out / "audits" / f"{inst}__c0.json").read_text())
        base = [m for m in a0["metrics"] if m is not None]
        if len(base) != len(a0["metrics"]):
            continue
        base_mean = float(np.mean(base))
        for snap_dir in root["snapshots"]:
            pf = point_features(snap_dir, node, noise[node], manifest["runs"])
            points.append({"instance": inst, **pf})
            for action in ("continue", "verify"):
                leaves = []
                for rep in range(1, manifest["reps"] + 1):
                    p = out / "leaves" / f"{inst}__b{pf['budget_index']:03d}__{action}__r{rep}.json"
                    if not p.exists():
                        continue
                    lf = json.loads(p.read_text())
                    ok = lf["integrity"] == "ok" and lf["audit_metrics"] and all(m is not None for m in lf["audit_metrics"])
                    y = float(np.mean(lf["audit_metrics"]) - base_mean) if ok else None
                    leaves.append(Leaf(repetition=rep, integrity="ok" if ok else "collection_failure", outcome_y=y,
                                       cost_worker_runs=int(lf["cost_worker_runs"]),
                                       final_incumbent_hash=lf["final_files_hash"],
                                       audit={"metrics": lf["audit_metrics"], "executed_action": lf["executed_action"]}))
                if leaves:
                    records.append(BranchRecord(
                        schema_version=R1_BRANCH_SCHEMA, instance_id=inst, node=node, campaign_id=inst, epoch="E2",
                        budget_index=int(pf["budget_index"]), action=action, split=str(manifest.get("split", "pilot")),
                        harness_commit=manifest["harness"]["commit"][:12], snapshot_hash=str(pf["snapshot_hash"])[:16],
                        manager_backend=str(manifest.get("manager", {}).get("kind", "scripted")), horizon=200, features=pf["features"], mask=pf["mask"],
                        leaves=tuple(leaves), executed_action=leaves[0].audit.get("executed_action")))
    with open(out / "records.jsonl", "w") as fh:
        for r in records:
            fh.write(json.dumps(record_to_dict(r)) + "\n")
    (out / "points.json").write_text(json.dumps(points, indent=1))
    return records, points


if __name__ == "__main__":
    raise SystemExit(main())
