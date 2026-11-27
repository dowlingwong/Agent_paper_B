"""Tests for the D.3 G1 campaign chunk record/layout unit (synthetic, CPU only)."""
from __future__ import annotations

import json
import shutil

import pytest

from r1.c3.d3.campaign_chunk import (
    CHUNK_SCHEMA,
    ChunkSpec,
    ChunkStop,
    check_hardware,
    run_chunk,
    sha256sums,
)
from r1.c3.d3.snapshots import SnapshotRecorder, sha256_json, wrap
from r1.harness import import_harness

HARNESS = import_harness()

from autoresearch.control_plane.budget import ComputeBudget  # noqa: E402
from autoresearch.control_plane.controller import ControlDecision  # noqa: E402
from autoresearch.manager.base import ManagerProposal  # noqa: E402
from autoresearch.nodes.registry import load_registered_node  # noqa: E402
from autoresearch.worker.base import WorkerResult  # noqa: E402

NODE = "digits_mlp"
SYMBOL = "LEARNING_RATE_INIT"
SOURCE = {"path": "docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_20261126.md",
          "sha256": "4b95798659c13feeef02af02504d68f138e40cdaf056ded0b89a09fbcc4e3a23"}


class ToggleBackend:
    mode = "toggle_backend"
    deterministic = True

    def propose_next_trial(self, status, memory_context, node_spec):
        current = str(getattr(status, "current_constants", {}).get(SYMBOL, "0.001"))
        new = "0.002" if current != "0.002" else "0.001"
        return ManagerProposal(
            manager_mode=self.mode, proposal_summary=f"{SYMBOL} {current} -> {new}",
            proposal_rationale="", target_files=tuple(node_spec.editable_paths),
            objective="toggle", extra={"structured_edit": {"type": "python_constant", "path": "train.py",
                                                           "symbol": SYMBOL, "old": current, "new": new}})


class Worker:
    mode = "chunk_fixture_worker"

    def __init__(self, root):
        self.node_root = root

    def run_trial(self, proposal, node_spec, budget_index):
        path = self.node_root / "train.py"
        text = path.read_text()
        edit = (proposal.extra or {}).get("structured_edit") or {}
        if edit:
            text = text.replace(f"{SYMBOL} = {edit.get('old')}", f"{SYMBOL} = {edit.get('new')}")
            path.write_text(text)
        return WorkerResult(self.mode, ("train.py",), True, {"val_score": 0.9}, "log", "diff", "b", "a")


class Continue:
    version = "continue/v1"

    def decide(self, view, mask):
        return ControlDecision("continue", {}, self.version, view.input_hash())


def _factory(spec, seed, cdir, recorder):
    node = cdir / "node"
    shutil.copytree(HARNESS / "nodes" / NODE, node, ignore=shutil.ignore_patterns("__pycache__"))
    kwargs = wrap({
        "node_spec": load_registered_node(NODE, repo_root=HARNESS),
        "campaign_id": spec.instance_id(seed),
        "budget": spec.W,
        "manager_mode": "baseline_manager",
        "memory_mode": "none",
        "records_path": cdir / "ledger.jsonl",
        "worker": Worker(node),
        "proposal_backend": ToggleBackend(),
        "controller": Continue(),
        "compute_budget": ComputeBudget(max_worker_runs=spec.W, max_llm_calls=spec.llm_cap),
    }, recorder)
    return kwargs, "worker_runs"


def _spec(**kw):
    base = dict(stage="a", arm="A0", node=NODE, repetition=0, instance_seeds=tuple(range(6201, 6219)),
                W=20, llm_cap=80, launcher="ssh", host="TASL-2", campaign_model_source=SOURCE)
    base.update(kw)
    return ChunkSpec(**base)


def _manifest(spec):
    return {"campaign_model": "NVIDIA RTX 4090", "proposer_model": "gemma4_31b",
            "campaign_model_source_sha256": sha256_json(dict(spec.campaign_model_source))}


def _observed():
    return {"model": "NVIDIA RTX 4090", "proposer_model": "gemma4_31b", "memory_check": "pass",
            "lease": True, "gpu_uuid": "GPU-test", "driver": "test", "memory_total": 24564,
            "memory_free": 24000, "other_processes_start": 0, "other_processes_end": 0,
            "request": "test", "scope": "test", "environment_freeze": "test",
            "host_class": "test", "lease_path": "/tmp/test.lock", "chunk_start_utc": "2026-11-27T00:00:00Z"}


def test_one_chunk_writes_layout_records_and_sums(tmp_path):
    spec = _spec()
    out = tmp_path / "chunk"
    summary = run_chunk(spec, out, _factory, manifest=_manifest(spec), observed=_observed())
    assert summary["campaigns"] == 18
    assert summary["worker_runs"] == 18 * 20
    chunk = json.loads((out / "chunk.json").read_text())
    assert chunk["schema"] == CHUNK_SCHEMA
    assert chunk["launcher"] == "ssh" and chunk["W"] == 20 and chunk["llm_cap"] == 80
    first = out / "campaigns" / f"{NODE}__s6201"
    assert (first / "campaign.json").is_file()
    assert (first / "ledger.jsonl").is_file()
    assert (first / "runs.jsonl").is_file()
    assert (first / "summary.json").is_file()
    assert (first / "snapshots" / "w5.json").is_file()
    assert (first / "snapshots" / "final.json").is_file()
    assert (first / "SHA256SUMS").is_file()
    camp = json.loads((first / "campaign.json").read_text())
    assert camp["record_name"] == f"a__A0__{NODE}__s6201__r0"
    assert camp["campaign_id"] == f"{NODE}__s6201"
    cs = json.loads((first / "summary.json").read_text())
    from r1.c3.d3_outcome_table import SUMMARY_KEYS
    assert set(cs) == SUMMARY_KEYS and cs["schema"] == "r1_d3_campaign_summary/v1"
    assert cs["worker_runs"] == 20 and cs["status"] == "complete"
    assert camp["ended_on"] == "worker_runs"
    assert chunk["gpu_model"] == "NVIDIA RTX 4090"
    assert chunk["memory_check"] == "pass"
    assert chunk["proposer_check"] == "pass" and chunk["model_check"] == "pass"
    assert chunk["campaign_model"] == "NVIDIA RTX 4090" and chunk["status"] == "complete"
    # The outer sums verifies every entry.
    for line in (out / "SHA256SUMS").read_text().splitlines():
        digest, rel = line.split("  ", 1)
        assert sha256sums_file(out / rel) == digest


def sha256sums_file(path):
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_existing_output_is_refused(tmp_path):
    out = tmp_path / "chunk"
    out.mkdir()
    with pytest.raises(ChunkStop):
        run_chunk(_spec(), out, _factory, manifest=_manifest(_spec()), observed=_observed())


def test_signed_values_are_enforced():
    with pytest.raises(ChunkStop):
        ChunkSpec.from_launch({"schema": "r1_d3_launch/v1", "stage": "a", "arm": "A2", "node": NODE,
                               "repetition": 0, "instance_seeds": list(range(6201, 6219)), "W": 19,
                               "llm_cap": 80, "launcher": "ssh", "host": "TASL-2",
                               "campaign_model_source": SOURCE})
    with pytest.raises(ChunkStop):
        ChunkSpec.from_launch({"schema": "r1_d3_launch/v1", "stage": "a", "arm": "A2", "node": NODE,
                               "repetition": 0, "instance_seeds": [6201, 6202], "W": 20,
                               "llm_cap": 80, "launcher": "ssh", "host": "TASL-2",
                               "campaign_model_source": SOURCE})


def test_hardware_refusals():
    spec = _spec()
    manifest = {"campaign_model": "NVIDIA RTX 4090", "proposer_model": "gemma4_31b"}
    good = {"model": "NVIDIA RTX 4090", "proposer_model": "gemma4_31b", "memory_check": "pass",
            "lease": True}
    check_hardware(spec, good, manifest)
    with pytest.raises(ChunkStop):
        check_hardware(spec, {**good, "model": "NVIDIA RTX 6000 Ada Generation"}, manifest)
    with pytest.raises(ChunkStop):
        check_hardware(spec, {**good, "proposer_model": "other"}, manifest)
    with pytest.raises(ChunkStop):
        check_hardware(spec, {**good, "memory_check": "fail"}, manifest)
    with pytest.raises(ChunkStop):
        check_hardware(spec, {**good, "lease": False}, manifest)
    with pytest.raises(ChunkStop):
        check_hardware(spec, {**good, "lease": None}, manifest)
    with pytest.raises(ChunkStop):
        check_hardware(spec, {**good, "model": ""}, manifest)
    with pytest.raises(ChunkStop):
        check_hardware(spec, good, {"campaign_model": "NVIDIA RTX 4090"})


def test_manifest_source_mismatch_is_refused(tmp_path):
    spec = _spec()
    manifest = dict(_manifest(spec), campaign_model_source_sha256="0" * 64)
    with pytest.raises(ChunkStop):
        run_chunk(spec, tmp_path / "chunk", _factory, manifest=manifest, observed=_observed())


def test_manifest_source_key_is_required(tmp_path):
    spec = _spec()
    manifest = dict(_manifest(spec))
    manifest.pop("campaign_model_source_sha256")
    with pytest.raises(ChunkStop):
        run_chunk(spec, tmp_path / "chunk", _factory, manifest=manifest, observed=_observed())


def test_w_zero_final_uses_start_config(tmp_path):
    rec = SnapshotRecorder(out_dir=tmp_path, stage="a", arm="A0", node=NODE, repetition=0, instance_id="x")
    rec.start_config = {"train.py": "x = 1\n"}
    digest = rec.write_final(w_final=0, ended_on="no_fundable_candidate")
    snap = json.loads((tmp_path / "snapshots" / "final.json").read_text())
    assert snap["w"] == 0 and snap["worker_runs"] == 0 and snap["final"] is True
    assert snap["incumbent_config"] == {"train.py": "x = 1\n"}
    assert len(digest) == 64


def _replicate_factory():
    from r1.c3.d3.replicate_campaign import ReplicateUnit
    from r1.c3.d3.snapshots import config_sha256
    from r1.c3.d3_replicate import Fixr3Engine

    def factory(spec, seed, cdir, recorder):
        def propose(step_index, incumbent_config, llm_calls):
            return step_index

        def validate(proposal):
            contents = {"train.py": f"X = {proposal}\n"}
            return contents, config_sha256(contents)

        def run_trial(proposal, config, train_seed, j, budget_index):
            return True, 0.5 + 0.01 * j, 0.0

        return ReplicateUnit(engine=Fixr3Engine(seed), propose=propose, validate=validate,
                             run_trial=run_trial, start_config={"train.py": "X = -1\n"})
    return factory


def test_replicate_chunk_writes_the_same_layout(tmp_path):
    spec = _spec(arm="FIXR3")
    out = tmp_path / "chunk"
    summary = run_chunk(spec, out, manifest=_manifest(spec), observed=_observed(),
                        replicate_factory=_replicate_factory())
    assert summary["campaigns"] == 18
    assert summary["campaign_kind"] == "replicate"
    assert summary["worker_runs"] == 18 * 18
    chunk = json.loads((out / "chunk.json").read_text())
    assert chunk["campaign_kind"] == "replicate" and chunk["arm"] == "FIXR3"
    first = out / "campaigns" / f"{NODE}__s6201"
    camp = json.loads((first / "campaign.json").read_text())
    assert camp["campaign_kind"] == "replicate"
    assert camp["record_name"] == f"a__FIXR3__{NODE}__s6201__r0"
    assert (first / "ledger.jsonl").is_file() and (first / "runs.jsonl").is_file()
    assert (first / "events.jsonl").is_file()
    ledger = [json.loads(line) for line in (first / "ledger.jsonl").read_text().splitlines()]
    assert ledger and all("replicates" in row["extra"]["control"] for row in ledger)
    assert (first / "snapshots" / "w5.json").is_file()
    assert (first / "snapshots" / "final.json").is_file()
    assert not (first / "snapshots" / "w20.json").exists()
    assert (first / "SHA256SUMS").is_file()


def test_replicate_factory_and_harness_factory_are_exclusive(tmp_path):
    spec = _spec()
    with pytest.raises(ChunkStop):
        run_chunk(spec, tmp_path / "chunk", _factory, manifest=_manifest(spec), observed=_observed(),
                  replicate_factory=_replicate_factory())
