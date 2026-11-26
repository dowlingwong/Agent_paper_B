"""D24/P1: the collector takes memory_mode from the manifest, and branch
continuations inherit the root's memory mode from the snapshot.

AI-assisted (BUILD_BATCH3, P1); ENGINEERING_ONLY.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from r1.headroom import e1b_collect as collect

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _interpreter_on_path(monkeypatch):
    """The node's run_command is ``python3 train.py``; run it with the test
    interpreter (the harness venv, which has numpy/sklearn) rather than
    whatever python3 the shell PATH exposes."""
    monkeypatch.setenv("PATH", str(Path(sys.executable).parent) + os.pathsep + os.environ["PATH"])


def _records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _root(tmp_path: Path, memory_mode: str | None, runs: int = 3, points=(2,)):
    args = dict(node="lr_synthetic", k=0, work=str(tmp_path / "work"), runs=runs, indices=list(points))
    if memory_mode is not None:
        args["memory_mode"] = memory_mode
    summary = collect.run_root(**args)
    ledger = tmp_path / "work" / "roots" / summary["instance"] / "root_trials.jsonl"
    return summary, _records(ledger)


def test_missing_memory_mode_means_none(tmp_path):
    _, records = _root(tmp_path, memory_mode=None)
    assert records
    assert {r["memory_mode"] for r in records} == {"none"}


def test_manifest_memory_mode_is_used_by_the_root(tmp_path):
    _, records = _root(tmp_path, memory_mode="append_only_summary")
    assert {r["memory_mode"] for r in records} == {"append_only_summary"}


def test_branch_continuation_inherits_the_root_memory_mode(tmp_path):
    summary, _ = _root(tmp_path, memory_mode="append_only_summary")
    snaps = sorted((tmp_path / "work" / "roots" / summary["instance"] / "snapshots").glob("E2_*"))
    assert snaps, "no E2 snapshot written"
    snap = collect.read_snapshot(str(snaps[0]))
    assert snap.memory_mode == "append_only_summary"
    result = collect.resume_campaign(snap, tmp_path / "branch", first_action="continue", horizon=1)
    branch_records = _records(Path(result.restored.records_path))
    assert branch_records
    assert {r["memory_mode"] for r in branch_records} == {"append_only_summary"}


def test_seed_policy_is_recorded_per_manager_kind():
    assert collect.seed_policy("langgraph")["kind"] == "ollama_seed"
    assert collect.seed_policy("scripted")["kind"] == "numpy_pcg64"


def test_langgraph_manager_carries_the_branch_repetition():
    manager = collect.make_manager(
        "lr_synthetic", 101, 2,
        {"kind": "langgraph", "model": "qwen2.5-coder:7b", "temperature": 0.2},
    )
    assert getattr(manager, "_repetition") == 2
