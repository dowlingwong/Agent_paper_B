"""D25 correction (review F1): the live scripted campaign sequence is unchanged.

The earlier golden (``test_scripted_golden.py``) replays the manager directly and
bypasses the campaign's ``_manager_status``; this golden runs the real campaign
path (``run_real_campaign`` with the scripted stand-in and an always-keep
worker) so a status-side change that alters the proposer's inputs is caught.

Generated from the pre-change harness (9c4902d) with the scripted manager.

AI-assisted (BUILD_BATCH3, correction round); ENGINEERING_ONLY.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml

from r1.harness import import_harness

HARNESS = import_harness()

from autoresearch.control_plane.campaign import run_real_campaign  # noqa: E402
from autoresearch.memory.append_store import TrialAppendStore  # noqa: E402
from autoresearch.nodes.registry import load_registered_node  # noqa: E402
from autoresearch.worker.base import WorkerResult  # noqa: E402

from r1.headroom.scripted_manager import ScriptedRandomManager  # noqa: E402

GOLDEN = Path(__file__).resolve().parent / "data" / "scripted_live_golden_E1b_seeds.json"


class _AlwaysKeepWorker:
    mode = "live_golden_worker"

    def __init__(self, root: Path) -> None:
        self.node_root = Path(root)
        self.i = 0

    def run_trial(self, proposal, node_spec, budget_index):
        edit = (proposal.extra or {}).get("structured_edit") or {}
        config = yaml.safe_load((self.node_root / "config.yaml").read_text())
        if edit:
            value = edit["new"]
            if value == "null":
                value = None
            old = config.get(edit["symbol"])
            if isinstance(old, (int, float)) and not isinstance(old, bool):
                value = float(value) if ("." in str(value) or "e" in str(value).lower()) else int(float(value))
            config[edit["symbol"]] = value
            (self.node_root / "config.yaml").write_text(yaml.safe_dump(config))
        self.i += 1
        return WorkerResult(
            worker_mode=self.mode, changed_files=("config.yaml",), success=True,
            parsed_metrics={node_spec.metric_name: 0.90 + 0.001 * self.i * self.i},
            raw_log_ref="", patch_ref="fake.diff", git_commit_before="b", git_commit_after="a",
        )


def _campaign(tmp: Path, node: str, seed: int, repetition: int, budget: int = 10) -> list[str]:
    spec = load_registered_node(node, repo_root=HARNESS)
    tmp.mkdir()  # Each scenario has an exclusive fixture directory, retained after the test.
    root = tmp / "node"
    shutil.copytree(HARNESS / "nodes" / node, root,
                    ignore=shutil.ignore_patterns("__pycache__", "data_cache"))
    worker = _AlwaysKeepWorker(root)
    manager = ScriptedRandomManager(node, seed=seed, repetition=repetition)
    run_real_campaign(
        node_spec=spec, campaign_id="live-golden", budget=budget, manager_mode="baseline_manager",
        memory_mode="none", records_path=tmp / "trials.jsonl", worker=worker,
        proposal_backend=manager,
    )
    records = TrialAppendStore(tmp / "trials.jsonl").read_all()
    return [record.proposal_summary for record in records]


def test_live_campaign_sequences_match_the_pre_change_golden(tmp_path):
    golden = json.loads(GOLDEN.read_text())
    assert str(golden["harness_commit"]).startswith("9c4902d")
    mismatches = []
    for index, (scenario, expected) in enumerate(golden["scenarios"].items()):
        node, rest = scenario.split("__s")
        seed, rep = (int(part) for part in rest.split("__r"))
        actual = _campaign(tmp_path / f"case_{index}", node, seed, rep)
        if actual != expected:
            mismatches.append((scenario, expected, actual))
    assert not mismatches, f"live scripted sequence changed: {mismatches}"
