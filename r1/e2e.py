#!/usr/bin/env python3
"""L13: one-command end-to-end engineering run (ENGINEERING_ONLY; never a result).

Steps, all on one noisy CPU node (``digits_mlp``):
1. two short root campaigns with E2 snapshot hooks (scripted proposer);
2. continue / verify branches at one E2 point per root, two repetitions each, with audits;
3. the r1_branch_v1 sibling table;
4. every L10 arm scored with leave-one-instance-out cross-fitting and the
   instance bootstrap. The KG index stands in for the configurator, which is
   deferred under R1-GATE-FIRST;
5. a short deployment: one fresh campaign under the KG ``IndexController``
   and one under the default controller, at the same compute budget;
6. the analysis tables.

Output: ``results/r1/engineering/E2E_<UTC>/`` with an ``ENGINEERING_ONLY`` banner.
Usage: ``make r1-e2e`` or ``python -m r1.e2e``.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from r1.harness import REPO, harness_commit, import_harness

HARNESS = import_harness()

from autoresearch.control_plane.budget import ComputeBudget  # noqa: E402
from autoresearch.control_plane.campaign import run_real_campaign  # noqa: E402
from autoresearch.control_plane.controller import ContinueController  # noqa: E402
from autoresearch.memory.append_store import TrialAppendStore  # noqa: E402
from autoresearch.nodes.registry import load_registered_node  # noqa: E402
from autoresearch.worker.local_worker import LocalWorker  # noqa: E402

from r1.baselines.policies import KGIndex  # noqa: E402
from r1.controllers import IndexController  # noqa: E402
from r1.headroom import e1b_collect  # noqa: E402
from r1.headroom.e1b_analyze import analyse, markdown  # noqa: E402
from r1.headroom.scripted_manager import ScriptedRandomManager  # noqa: E402

NODE = "digits_mlp"
BANNER = "ENGINEERING_ONLY — end-to-end plumbing check (L13). Not evidence; numbers are not results."


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    final = REPO / "results" / "r1" / "engineering" / f"E2E_{stamp}"
    work = Path(tempfile.mkdtemp(prefix="r1_e2e_"))
    # 1-2: roots, branches, audits (reusing the E1b collector at a tiny size)
    final.parent.mkdir(parents=True, exist_ok=True)
    sys.argv = ["e1b_collect", "--nodes", NODE, "--instances", "2", "--runs", "8", "--points", "3", "--reps", "2",
                "--audit-seeds", "2", "--work", str(work / "w"), "--workers", "4", "--out", str(final),
                "--label", "ENGINEERING_ONLY", "--split", "engineering"]
    e1b_collect.main()
    for _ in range(10):
        sys.argv = ["e1b_collect", "--resume", str(final), "--workers", "4"]
        e1b_collect.main()
        man = json.loads((final / "manifest.json").read_text())
        if man["sessions"][-1]["jobs_before"] == 0:
            break
    # 3-4: table, arms, bootstrap
    result = analyse(final, n_boot=300)
    # 5: short deployment, KG index vs default, same compute budget
    records = [json.loads(l) for l in (final / "records.jsonl").read_text().splitlines()]
    projections = [{"features": r["features"], "mask": r["mask"], "epoch": r["epoch"]} for r in records]
    kg = KGIndex().fit(projections)
    noise = json.loads((final / "manifest.json").read_text())["noise"][NODE]
    spec = load_registered_node(NODE, repo_root=HARNESS)
    deploy = {}
    for name, controller in (("default", ContinueController()),
                             ("kg_index", IndexController(kg.score, 0.0, NODE, noise, total_runs=8))):
        d = work / f"deploy_{name}"
        shutil.copytree(HARNESS / "nodes" / NODE, d / "node")
        run_real_campaign(node_spec=spec, campaign_id=f"e2e_{name}", budget=16, manager_mode="baseline_manager",
                          memory_mode="none", records_path=d / "trials.jsonl",
                          worker=LocalWorker(node_root=d / "node", artifact_dir=d / "art", train_seed=999, split_seed=999),
                          proposal_backend=ScriptedRandomManager(NODE, seed=999, repetition=0),
                          controller=controller, compute_budget=ComputeBudget(max_worker_runs=8))
        recs = TrialAppendStore(d / "trials.jsonl").read_all()
        deploy[name] = {"trials": len(recs), "kept": sum(1 for r in recs if r.decision.value == "kept"),
                        "verifies": sum(1 for r in recs if (r.extra.get("control") or {}).get("verify"))}
    # 6: report
    summary = {"label": "ENGINEERING_ONLY", "banner": BANNER, "utc": stamp,
               "harness": {"root": str(HARNESS), **harness_commit(HARNESS)},
               "table": {"points": result["n_points"], "instances": result["n_instances"]}, "deployment": deploy}
    (final / "E2E_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
    (final / "README.md").write_text(f"# {BANNER}\n\n```\n{json.dumps(summary, indent=2)}\n```\n\n" + markdown(result) + "\n")
    shutil.rmtree(work, ignore_errors=True)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
