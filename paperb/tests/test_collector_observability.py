"""Collector observability (rerun-2 STOP diagnosis follow-up, 19 Oct 2026).

Failed leaves and campaigns persist the error class, traceback and UTC
timestamp (and the transport-attempt log when the harness attached one)
before any collection gate raises.  ENGINEERING_ONLY; AI-assisted (Claude).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from r1.headroom import e1b_collect


def _runner_error():
    from ollama import ResponseError
    exc = ResponseError("llama runner process no longer running: -1 ")
    exc.llm_call_attempts = [{"attempt": i, "error_class": "runner_terminated"} for i in (1, 2, 3)]
    exc.llm_call_seed = 1234
    return exc


def _parse_utc(text):
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%S.%fZ")


def test_failed_leaf_persists_class_traceback_and_time(tmp_path, monkeypatch):
    out = tmp_path / "out"
    (out / "leaves").mkdir(parents=True)
    monkeypatch.setattr(e1b_collect, "read_snapshot", lambda d: SimpleNamespace(budget_index=4, ledger_prefix=()))

    def boom(*args, **kwargs):
        raise _runner_error()

    monkeypatch.setattr(e1b_collect, "resume_campaign", boom)
    payload = e1b_collect.run_leaf("snap", "n__s1", "digits_mlp", "continue", 1, 1, 2, str(tmp_path / "w"), str(out))
    saved = json.loads((out / "leaves" / "n__s1__b004__continue__r1.json").read_text())
    assert saved == payload
    # historical fields unchanged
    assert saved["integrity"] == "collection_failure"
    assert saved["error"] == repr(_runner_error())
    assert saved["cost_worker_runs"] == 0
    # new observability fields
    assert saved["error_class"] == "ollama._types.ResponseError"
    assert "llama runner process no longer running" in saved["traceback"]
    assert "Traceback (most recent call last)" in saved["traceback"]
    _parse_utc(saved["failed_utc"])
    assert saved["failure_stage"] == "resume_campaign"
    assert len(saved["transport_attempts"]) == 3 and saved["llm_seed"] == 1234
    assert saved["partial_records"] == 0


def test_successful_leaf_has_no_new_fields(tmp_path, monkeypatch):
    out = tmp_path / "out"
    (out / "leaves").mkdir(parents=True)
    into_root = tmp_path / "w" / "branches" / "n__s1__b004__verify__r1"
    monkeypatch.setattr(e1b_collect, "read_snapshot", lambda d: SimpleNamespace(budget_index=4, ledger_prefix=()))

    def fake_resume(snap, into, **kwargs):
        Path(into).mkdir(parents=True)
        (Path(into) / "train.py").write_text("X = 1\n")
        records = Path(into) / "branch_trials.jsonl"
        records.write_text(json.dumps({"decision": "kept", "extra": {"control": {"action": "verify"}}}) + "\n")
        first = SimpleNamespace(extra={"control": {"action": "verify"}})
        return SimpleNamespace(first_record=first, restored=SimpleNamespace(records_path=records))

    monkeypatch.setattr(e1b_collect, "resume_campaign", fake_resume)
    monkeypatch.setattr(e1b_collect, "load_registered_node",
                        lambda node, repo_root=None: SimpleNamespace(editable_paths=("train.py",)))
    monkeypatch.setattr(e1b_collect, "_audit", lambda node, files, seeds, work: [0.9 for _ in seeds])
    payload = e1b_collect.run_leaf("snap", "n__s1", "digits_mlp", "verify", 1, 1, 2, str(tmp_path / "w"), str(out))
    assert into_root.exists()
    assert payload["integrity"] == "ok"
    assert not {"error_class", "traceback", "failed_utc", "failure_stage"} & set(payload)


def test_failed_root_is_persisted_before_it_propagates(tmp_path, monkeypatch):
    out = tmp_path / "out"

    def boom(*args, **kwargs):
        raise _runner_error()

    monkeypatch.setattr(e1b_collect, "_run_root", boom)
    with pytest.raises(Exception, match="llama runner"):
        e1b_collect.run_root("digits_mlp", 0, str(tmp_path / "w"), 20, [], None, "vary", "none", str(out))
    inst = f"digits_mlp__s{e1b_collect._instance_seed('digits_mlp', 0)}"
    saved = json.loads((out / "failures" / f"root__{inst}.json").read_text())
    assert saved["integrity"] == "collection_failure"
    assert saved["failure_stage"] == "root_campaign"
    assert "Traceback" in saved["traceback"]
    _parse_utc(saved["failed_utc"])
    assert saved["transport_attempts"][0]["error_class"] == "runner_terminated"


def test_root_without_out_dir_keeps_the_old_signature(tmp_path, monkeypatch):
    monkeypatch.setattr(e1b_collect, "_run_root", lambda *a, **k: {"instance": "x"})
    assert e1b_collect.run_root("digits_mlp", 0, str(tmp_path), 20, [], None) == {"instance": "x"}


def test_shared_collect_writes_failures_before_the_gate(tmp_path, monkeypatch):
    from r1.tests.test_ada_e1b_rerun2 import _load_runner

    runner = _load_runner(tmp_path, monkeypatch)
    out = tmp_path / "arm"
    (out / "leaves").mkdir(parents=True)
    leaves = [
        {"leaf_id": "a", "action": "continue", "integrity": "ok", "audit_metrics": [0.9]},
        {"leaf_id": "b", "action": "verify", "integrity": "collection_failure", "audit_metrics": [],
         "error": "ResponseError('x')"},
    ]
    for leaf in leaves:
        (out / "leaves" / f"{leaf['leaf_id']}.json").write_text(json.dumps(leaf))
    (out / "manifest.json").write_text(json.dumps({"sessions": [{"jobs_before": 0}], "manager": {"kind": "scripted"}}))
    monkeypatch.setattr(runner, "cmd", lambda *a, **k: None)
    monkeypatch.setattr(runner, "check_gpu", lambda: None)
    with pytest.raises(RuntimeError, match="collection failures"):
        runner.collect(out, tmp_path / "work", [], ["digits_mlp"], manager="scripted")
    written = json.loads((out / "collection_failures.json").read_text())
    assert written["n_failures"] == 1
    assert written["failures"][0]["leaf_id"] == "b"
    assert written["failures"][0]["failed_utc"] is None  # old-format leaf: no invented time


def test_roots_only_collection_declares_new_campaign_versions(tmp_path):
    """CPU, scripted proposer: roots-only layout with the PLAN new-campaign declaration."""
    import os
    import subprocess
    import sys

    repo = Path(__file__).resolve().parents[2]
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(repo), os.environ.get("PYTHONPATH", "")]))
    out = tmp_path / "out"
    subprocess.run([sys.executable, "-m", "r1.headroom.e1b_collect", "--roots-only", "--points", "--reps", "0",
                    "--audit-seeds", "0", "--nodes", "digits_mlp", "--instances", "1", "--runs", "2",
                    "--verify-split-policy", "vary", "--new-campaign-versions", "--root-failures", "record",
                    "--label", "ENGINEERING_ONLY", "--split", "engineering", "--out", str(out),
                    "--work", str(tmp_path / "work"), "--workers", "1"],
                   cwd=repo, env=env, check=True, capture_output=True, timeout=150)
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["roots_only"] is True and manifest["verify_split_policy"] == "vary"
    assert manifest["action_versions"]["verify_failed"] == "original_stands/v1"
    assert not list((out / "leaves").iterdir()) and not list((out / "audits").iterdir())
    root = json.loads(next((out / "roots").glob("*.json")).read_text())
    assert root["snapshots"] == []
    ledger = tmp_path / "work" / "roots" / root["instance"] / "root_trials.jsonl"
    assert len(ledger.read_text().splitlines()) == 2


def test_roots_only_refuses_branch_arguments():
    import subprocess
    import sys

    repo = Path(__file__).resolve().parents[2]
    done = subprocess.run([sys.executable, "-m", "r1.headroom.e1b_collect", "--roots-only", "--reps", "2"],
                          cwd=repo, capture_output=True, text=True, timeout=60)
    assert done.returncode != 0 and "--roots-only" in done.stderr
