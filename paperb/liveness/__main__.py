"""CLI for the D28 liveness check (P4/P5).

Offline (existing ledgers)::

    python -m r1.liveness --offline <ledgers-dir-or-file> --out <dir>

Run (short campaigns through the collector's code path; 1-2 instances, W=10,
no branching)::

    python -m r1.liveness --run --nodes digits_mlp openml_ionosphere \\
        --manager scripted --memory-mode none --out results/r1/engineering/liveness_scripted_<UTC>

ENGINEERING_ONLY.  AI-assisted (BUILD_BATCH3, P4).
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

from r1.harness import REPO, harness_commit
from r1.liveness.check import evaluate_ledger_paths, write_reports

DEFAULT_RUN_NODES = ["digits_mlp", "tabular_mlp", "openml_breast_w", "openml_ionosphere", "openml_wdbc", "openml_credit_approval", "openml_sonar", "openml_blood_transfusion"]  # D21 pool, 22 Oct


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def run_campaigns(args) -> Path:
    from r1.headroom import e1b_collect as collect
    from r1.scripts.dryrun_guard import validate_dryrun
    dryrun = validate_dryrun()
    if args.runs != 10 and not dryrun:
        raise RuntimeError('STOP: liveness runs are fixed at 10 outside DRYRUN')

    stamp = _stamp()
    out = Path(args.out) if args.out else (
        REPO / "results" / "r1" / "engineering" / f"liveness_{args.manager}_{stamp}"
    )
    work = Path(args.work) / f"liveness_{stamp}"
    if dryrun:
        root = Path(os.environ['R1_DRYRUN_ROOT']).resolve()
        if not out.resolve().is_relative_to(root) or not work.resolve().is_relative_to(root):
            raise RuntimeError('STOP: DRYRUN liveness output/work escapes the temporary directory')
    if getattr(args, 'extra_manifest', None) and out.exists() and any(out.iterdir()):
        raise RuntimeError('STOP: managed liveness output already exists and is not empty')
    out.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    manager = collect.MANAGER if args.manager == "scripted" else {
        **collect.MANAGER, "kind": "langgraph",
    }
    model = getattr(args, "manager_model", None)
    if model is not None:  # RUNBOOK A.10: e.g. llamacpp/<alias> for the batch's llama-server
        if args.manager != "langgraph":
            raise RuntimeError("STOP: --manager-model needs --manager langgraph")
        manager = {**manager, "model": collect.check_manager_model(model)}
    schema = getattr(args, 'proposal_schema', None)
    if schema is not None:
        if args.manager != 'langgraph' or not str(manager.get('model', '')).startswith('llamacpp/'):
            raise RuntimeError('STOP: proposal schema requires the llama.cpp LangGraph manager')
        manager = {**manager, 'proposal_schema': schema}
    if getattr(args, "transport_max_attempts", None) is not None:
        # Bounded LLM transport retry (19 Oct); absent means one attempt (historical).
        manager = {**manager, "transport_max_attempts": int(args.transport_max_attempts)}
    manifest = {
        "schema": "r1.liveness_run/1", "label": "DRYRUN" if dryrun else "ENGINEERING_ONLY", "started_utc": stamp,
        "harness": {"root": str(collect.HARNESS), **harness_commit(collect.HARNESS)},
        "manager": manager, "manager_kind": args.manager, "memory_mode": args.memory_mode or "none",
        "seed_policy": collect.seed_policy(args.manager, manager.get("model")),
        "nodes": list(args.nodes), "instances": args.instances, "runs": args.runs, "branching": False,
        "host": {"platform": platform.platform(), "python": platform.python_version()},
        "work": str(work), "campaigns": [],
    }
    extra = getattr(args, "extra_manifest", None)
    if extra:
        extra = json.loads(extra)
        if not isinstance(extra, dict) or set(extra) & set(manifest):
            raise RuntimeError("STOP: liveness extra manifest must be an object without existing keys")
        manifest.update(extra)
    # Persist provenance before the first campaign; the final write updates it.
    initial_manifest = out / "manifest.initial.tmp"
    if (out / "manifest.json").exists():
        raise RuntimeError('STOP: liveness manifest already exists')
    with initial_manifest.open("x", encoding="utf-8") as f:
        f.write(json.dumps(manifest, indent=2) + "\n")
    initial_manifest.replace(out / "manifest.json")
    t0 = time.time()
    for node in manifest["nodes"]:
        for k in range(manifest["instances"]):
            summary = collect.run_root(
                node=node, k=k, work=str(work), runs=manifest["runs"], indices=[],
                manager=manager, memory_mode=manifest["memory_mode"], out_dir=str(out),
            )
            source = work / "roots" / summary["instance"] / "root_trials.jsonl"
            target_dir = out / "ledgers" / summary["instance"]
            target_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target_dir / "root_trials.jsonl")
            events = work / "roots" / summary["instance"] / "root_events.jsonl"
            if events.exists():
                # D28 revised criterion 2: edit_novelty events are the primary
                # novelty source; keep them beside the trial ledger.
                shutil.copy2(events, target_dir / "root_events.jsonl")
            manifest["campaigns"].append({"instance": summary["instance"], "node": node,
                                          "seed": summary["seed"]})
    manifest["elapsed_seconds"] = round(time.time() - t0, 1)
    manifest["finished_utc"] = _stamp()
    final_manifest = out / "manifest.final.tmp"
    with final_manifest.open("x", encoding="utf-8") as f:
        f.write(json.dumps(manifest, indent=2) + "\n")
    final_manifest.replace(out / "manifest.json")
    report = evaluate_ledger_paths(
        [out / "ledgers"], generated_utc=manifest["finished_utc"], manager_kind=args.manager,
        memory_mode=manifest["memory_mode"],
    )
    if dryrun:
        report["label"] = "DRYRUN"
    report["run_manifest"] = "manifest.json"
    write_reports(report, out)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--offline", default=None, help="ledger file or directory to check")
    parser.add_argument("--run", action="store_true", help="run short campaigns before checking")
    parser.add_argument("--nodes", nargs="+", default=DEFAULT_RUN_NODES)
    parser.add_argument("--instances", type=int, default=2)
    parser.add_argument("--runs", type=int, default=10, help="fixed at 10 outside guarded DRYRUN")
    parser.add_argument("--manager", choices=["scripted", "langgraph"], default="scripted")
    parser.add_argument("--memory-mode", default=None,
                        choices=["none", "append_only_summary", "append_only_summary_with_rationale"])
    parser.add_argument("--transport-max-attempts", type=int, default=None,
                        help="bounded LLM transport retry (manager field; absent = 1 attempt)")
    parser.add_argument("--manager-model", default=None,
                        help="langgraph manager model id (default ollama/qwen2.5-coder:7b); llamacpp/<alias> "
                             "for a llama-server (RUNBOOK A.10)")
    parser.add_argument('--proposal-schema', choices=['manager_proposal/v1'], default=None)
    parser.add_argument('--extra-manifest', default=None,
                        help='JSON object merged into the initial manifest; existing keys cannot be overridden')
    parser.add_argument("--out", default=None)
    parser.add_argument("--work", default="/tmp/r1_liveness")
    args = parser.parse_args()

    if args.run:
        out = run_campaigns(args)
        print(json.dumps({"out": str(out)}))
        return 0
    if not args.offline:
        parser.error("one of --offline or --run is required")
    report = evaluate_ledger_paths([args.offline])
    if args.out:
        write_reports(report, args.out)
    print(json.dumps({node: ("PASS" if v["pass"] else "FAIL") for node, v in report["nodes"].items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
