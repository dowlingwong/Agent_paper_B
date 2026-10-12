#!/usr/bin/env python3
"""Run the authorized L12 live ENGINEERING_ONLY smoke on a Deepthought host."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shutil
import sys
from urllib.request import urlopen

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from r1.harness import harness_commit, import_harness

HARNESS = import_harness()
from autoresearch.control_plane.budget import ComputeBudget
from autoresearch.control_plane.campaign import run_real_campaign
from autoresearch.llm.langchain_client import _build_chat_model
from autoresearch.llm.providers import resolve_llm_config
from autoresearch.memory.event_store import CampaignEventStore
from autoresearch.nodes.registry import load_registered_node
from autoresearch.worker.local_worker import LocalWorker
from r1.headroom.scripted_manager import ScriptedRandomManager
from r1.llm_control import LLMSelfController

MODEL = "qwen2.5-coder:7b"
DIGEST = "dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364"


class ObservedController(LLMSelfController):
    """Observe the harness counters alongside each decision for reconciliation."""

    def __init__(self, llm):
        super().__init__(llm)
        self.accounting = []

    def decide(self, view, mask):
        decision = super().decide(view, mask)
        self.accounting.append({"epoch": view.epoch, "budget_before": dict(view.budget),
                                "charged_calls": decision.llm_calls})
        return decision


class CountedWorker(LocalWorker):
    """Seeded re-runs delegate to run_trial, so this counts each execution once."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.executions = 0

    def run_trial(self, proposal, node_spec, budget_index):
        self.executions += 1
        return super().run_trial(proposal, node_spec, budget_index)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    if platform.node().split(".")[0] not in {"deepthought2", "deepthought"}:
        raise RuntimeError("R1-COMPUTE: this live smoke must run on an author-approved Deepthought host")
    base = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    if base not in {"http://127.0.0.1:11434", "http://localhost:11434"}:
        raise RuntimeError("Only the dedicated loopback Ollama instance is permitted")
    with urlopen(base + "/api/tags", timeout=15) as response:
        tags = json.load(response)
    model = next((m for m in tags["models"] if m["name"] == MODEL), None)
    if model is None or model["digest"] != DIGEST:
        raise RuntimeError("STOP: manager model digest does not match author pin")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = args.out or REPO / "results/r1/engineering" / f"L12_live_{stamp}"
    out.mkdir(parents=True, exist_ok=False)
    (out / "README.md").write_text("# ENGINEERING_ONLY\n\nL12 live plumbing smoke. Not evidence.\n")
    shutil.copytree(HARNESS / "nodes/digits_mlp", out / "node",
                    ignore=shutil.ignore_patterns("__pycache__", "artifacts"))
    controller = ObservedController(_build_chat_model(resolve_llm_config("ollama/" + MODEL), 0.2))
    worker = CountedWorker(node_root=out / "node", artifact_dir=out / "artifacts",
                           train_seed=101, split_seed=101)
    events = CampaignEventStore(out / "events.jsonl")
    run_real_campaign(node_spec=load_registered_node("digits_mlp", repo_root=HARNESS),
                      campaign_id="l12_live_" + stamp, budget=40, manager_mode="baseline_manager",
                      memory_mode="none", records_path=out / "trials.jsonl", worker=worker,
                      proposal_backend=ScriptedRandomManager("digits_mlp", seed=101, repetition=0),
                      controller=controller, event_store=events,
                      compute_budget=ComputeBudget(max_worker_runs=10, max_llm_calls=12))
    (out / "controller_log.json").write_text(json.dumps(controller.log, indent=2) + "\n")
    (out / "accounting.json").write_text(json.dumps(controller.accounting, indent=2) + "\n")
    decisions = [e.payload for e in events.read_all() if e.event_type == "control_decision"]
    logs = controller.log
    charged = max((r["budget_before"]["llm_calls_used"] + r["charged_calls"]
                   for r in controller.accounting), default=0)
    queries = sum(r["llm_calls"] for r in logs)
    summary = {"label": "ENGINEERING_ONLY", "utc": stamp, "host": platform.node(),
               "harness": harness_commit(HARNESS), "model": MODEL, "digest": model["digest"],
               "side_queries": queries,
               "queried_action_distribution": dict(Counter(r.get("action", "continue") for r in logs if r["llm_calls"])),
               "decision_action_distribution": dict(Counter(e["action"] for e in decisions)),
               "parse_failures": sum(r["reason"].startswith("parse_failure") for r in logs),
               "disallowed_actions": sum(r["reason"].startswith("action_not_allowed") for r in logs),
               "call_errors": sum(r["reason"].startswith("llm_error") for r in logs),
               "control_events": len(decisions),
               "missing_llm_calls": sum("llm_calls" not in e for e in decisions),
               "event_llm_calls_sum": sum(e.get("llm_calls", 0) for e in decisions),
               "charged_llm_calls": charged, "actual_worker_runs": worker.executions,
               "caps": {"worker_runs": 10, "llm_calls": 12}}
    summary["accepted"] = (summary["missing_llm_calls"] == 0 and len(decisions) == len(controller.accounting)
                           and summary["event_llm_calls_sum"] == charged == queries
                           and charged <= 12 and worker.executions <= 10)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"out": str(out), **summary}, indent=2))
    if not summary["accepted"]:
        raise RuntimeError("STOP: L12 counters or caps do not reconcile; output preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
