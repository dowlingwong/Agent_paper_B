"""Scripted-campaign fixtures for the Track H controller tests (no LLM, no model). AI-assisted (Claude)."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from r1.c3.features import NodeContext, apply_edit
from r1.harness import import_harness

HARNESS = import_harness()

from autoresearch.control_plane.campaign import run_real_campaign  # noqa: E402
from autoresearch.control_plane.controller import ControlDecision  # noqa: E402
from autoresearch.manager.base import ManagerProposal  # noqa: E402
from autoresearch.memory.append_store import TrialAppendStore  # noqa: E402
from autoresearch.memory.event_store import CampaignEventStore  # noqa: E402
from autoresearch.nodes.registry import load_registered_node  # noqa: E402
from autoresearch.worker.base import WorkerResult  # noqa: E402

NODE = "digits_mlp"


def config_metric(text: str, scale: float = 0.01) -> float:
    """A deterministic metric of the configuration text (bit-exact replays)."""
    h = int(hashlib.sha256(text.encode()).hexdigest()[:8], 16)
    return round(0.9 + scale * ((h % 13) - 6) / 6.0, 6)


class ConfigMetricWorker:
    """Applies the structured edit to the node copy and returns ``config_metric`` of the result."""

    mode = "config_metric_worker"

    def __init__(self, node_root: Path, scale: float = 0.01) -> None:
        self.node_root, self.scale, self.runs = Path(node_root), scale, 0

    def run_trial(self, proposal, node_spec, budget_index):
        self.runs += 1
        path = self.node_root / "train.py"
        edit = (proposal.extra or {}).get("structured_edit")
        files = {"train.py": path.read_text()}
        if edit:
            files = apply_edit(files, edit)
            path.write_text(files["train.py"])
        return WorkerResult(worker_mode=self.mode, changed_files=("train.py",), success=True,
                            parsed_metrics={"val_score": config_metric(files["train.py"], self.scale)},
                            raw_log_ref="fake.log", patch_ref="fake.diff", git_commit_before="b",
                            git_commit_after="a")


class SeededConfigMetricWorker(ConfigMetricWorker):
    """Adds seeded re-runs (verify): the configuration's metric plus a deterministic seed effect."""

    def run_trial_at_seed(self, proposal, node_spec, budget_index, *, train_seed, split_seed=None):
        self.runs += 1
        text = (self.node_root / "train.py").read_text()
        h = int(hashlib.sha256(f"{text}|{train_seed}|{split_seed}".encode()).hexdigest()[:8], 16)
        metric = round(config_metric(text, self.scale) + self.scale * ((h % 9) - 4) / 8.0, 6)
        return WorkerResult(worker_mode=self.mode, changed_files=(), success=True,
                            parsed_metrics={"val_score": metric}, raw_log_ref="fake.log", patch_ref="",
                            git_commit_before="b", git_commit_after="b")


class SequenceBackend:
    """Proposes a fixed sequence of (symbol, old, new) edits."""

    mode = "sequence_backend"
    deterministic = True

    def __init__(self, edits) -> None:
        self.edits, self.n = list(edits), 0

    def propose_next_trial(self, status, memory_context, node_spec):
        sym, old, new = self.edits[self.n % len(self.edits)]
        self.n += 1
        return ManagerProposal(manager_mode=self.mode, proposal_summary=f"{sym} {old} -> {new}", proposal_rationale="",
                               target_files=tuple(node_spec.editable_paths), objective=f"Change {sym}.",
                               extra={"structured_edit": {"type": "python_constant", "path": "train.py",
                                                          "symbol": sym, "old": old, "new": new}})


class IndexPolicyReference:
    """The C2 index policy without the learned-prior machinery: one constant E1 decision for every
    proposal that has features (trial >= 2 with an incumbent metric) and a constant ``KeepPrior`` at E2."""

    version = "index_reference/v1"
    deterministic = True

    def __init__(self, execute: bool) -> None:
        self.execute = execute

    def decide(self, view, mask):
        if (view.epoch == "E1" and not self.execute and view.budget_index >= 2 and view.current_best is not None
                and mask.get("skip")):
            return ControlDecision("skip", {}, self.version, view.input_hash())
        return ControlDecision("continue", {}, self.version, view.input_hash())


def node_context(sigma_node: float, runs: int = 20, memory_mode: str = "none") -> NodeContext:
    return NodeContext(node=NODE, start_files={"train.py": (HARNESS / "nodes" / NODE / "train.py").read_text()},
                       sigma_node=sigma_node, runs_total=runs, memory_mode=memory_mode)


def run_campaign(tmp: Path, backend, *, budget: int, memory_mode: str = "none", scale: float = 0.01,
                 seeded: bool = False, **kwargs):
    spec = load_registered_node(NODE, repo_root=HARNESS)
    node = Path(tmp) / "node"
    shutil.copytree(HARNESS / "nodes" / NODE, node, ignore=shutil.ignore_patterns("__pycache__"))
    worker = (SeededConfigMetricWorker if seeded else ConfigMetricWorker)(node, scale)
    run_real_campaign(node_spec=spec, campaign_id="h3", budget=budget, manager_mode="baseline_manager",
                      memory_mode=memory_mode, records_path=Path(tmp) / "trials.jsonl", worker=worker,
                      proposal_backend=backend, event_store=CampaignEventStore(Path(tmp) / "events.jsonl"), **kwargs)
    records = TrialAppendStore(Path(tmp) / "trials.jsonl").read_all()
    events = [json.loads(line) for line in (Path(tmp) / "events.jsonl").read_text().splitlines()]
    rows = [json.loads(line) for line in (Path(tmp) / "trials.jsonl").read_text().splitlines()]
    return records, events, rows, worker
