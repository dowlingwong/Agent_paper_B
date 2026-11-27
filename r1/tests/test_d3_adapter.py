"""Synthetic CPU tests for the D.3 G1 real adapter (no GPU, no server, no label)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from r1.c3.d3 import adapter as A
from r1.c3.d3.campaign_chunk import ChunkSpec, run_chunk
from r1.harness import harness_root

HARNESS = Path(harness_root())
REPO = A.REPO
CONSTANTS = "docs/r1/reports/d3_g2_20261127/d3_constants.json"
NOISE = "results/r1/noise/D28_REPAIR_20261027/summary.json"
PREDECL = "docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md"
SPLIT = "r1/c3/splits/c3_p3_split_v1.json"
NODE = "digits_mlp"
SYMBOL = "LEARNING_RATE_INIT"


def _sha(path: str) -> str:
    return hashlib.sha256((REPO / path).read_bytes()).hexdigest()


def manifest_dict(**overrides):
    m = {
        "schema": A.SCHEMA, "stage": "a", "campaign_model": "NVIDIA GeForce RTX 4090",
        "campaign_model_source": {"path": "docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_20261126.md",
                                  "sha256": "b" * 64},
        "proposer": {"model": "gemma4_31b", "alias": "gemma4_31b", "base_url": "http://127.0.0.1:8095/v1",
                     "model_sha256": "a" * 64, "schema": "manager_proposal/v1", "temperature": 0.2,
                     "thinking": False},
        "harness_commit": A.HARNESS_PIN,
        "constants": {"path": CONSTANTS, "sha256": _sha(CONSTANTS)},
        "noise": {"path": NOISE, "sha256": _sha(NOISE)},
        "predeclaration": {"path": PREDECL, "sha256": _sha(PREDECL)},
        "split": {"path": SPLIT, "sha256": _sha(SPLIT)},
        "W": 20, "llm_cap": 80, "trial_budget": 80, "memory_mode": "append_only_summary",
        "verify_runs": 2, "verify_seed_base": 20000, "verify_split_policy": "vary",
        "nodes": list(A.D3_NODES), "arms": list(A.D3A_ARMS),
    }
    m.update(overrides)
    return m


def load_manifest(**overrides) -> A.Manifest:
    return A.load_manifest(manifest_dict(**overrides))


class ToggleManager:
    """Deterministic stand-in: one bounded edit, no LLM call, no network."""

    mode = "adapter_fixture_manager"
    deterministic = True

    def propose_next_trial(self, status, memory_context, node_spec):
        from autoresearch.manager.base import ManagerProposal
        current = str(dict(status.current_constants).get(SYMBOL, "0.001"))
        new = "0.01" if current != "0.01" else "0.001"
        return ManagerProposal(
            manager_mode=self.mode, proposal_summary=f"{SYMBOL} {current} -> {new}",
            proposal_rationale="", target_files=tuple(node_spec.editable_paths), objective="toggle",
            extra={"structured_edit": {"type": "python_constant", "path": "train.py", "symbol": SYMBOL,
                                       "old": current, "new": new}},
        )


class FakeWorker:
    mode = "adapter_fixture_worker"

    def __init__(self, root=None, seed=0):
        self.node_root = root
        self.seed = seed
        self.calls = 0

    def run_trial(self, proposal, node_spec, budget_index):
        from autoresearch.worker.base import WorkerResult
        self.calls += 1
        return WorkerResult(self.mode, tuple(node_spec.editable_paths), True, {"val_score": 0.9 + 0.001 * self.calls},
                            "log", "diff", "b", "a")

    def run_trial_at_seed(self, proposal, node_spec, budget_index, *, train_seed, split_seed):
        return self.run_trial(proposal, node_spec, budget_index)


def _factory(manifest, *, worker_cls=FakeWorker):
    constants = A.load_constants(manifest)
    return A.make_campaign_factory(
        manifest, constants, harness=HARNESS, apply_env=False,
        manager_factory=lambda m, seed, rep: ToggleManager(),
        worker_factory=lambda node, seed: worker_cls(node, seed),
    )


def _spec(arm="A0", **kw):
    base = dict(stage="a", arm=arm, node=NODE, repetition=0, instance_seeds=tuple(range(6201, 6219)),
                W=20, llm_cap=80, launcher="ssh", host="TASL-2",
                campaign_model_source=manifest_dict()["campaign_model_source"])
    base.update(kw)
    return ChunkSpec(**base)


def _observed(manifest):
    return {"model": manifest.campaign_model, "proposer_model": manifest.proposer_model,
            "memory_check": "pass", "lease": True, "gpu_uuid": "GPU-test", "driver": "test",
            "memory_total": 24564, "memory_free": 24000, "other_processes_start": 0,
            "other_processes_end": 0, "request": "test", "scope": "test", "environment_freeze": "test",
            "host_class": "test", "lease_path": "/tmp/test.lock",
            "chunk_start_utc": "2026-11-27T00:00:00Z"}


# --------------------------------------------------------------------------- manifest

def test_manifest_refuses_each_declared_value():
    for field, value, needle in (
        ("W", 19, "W = 20"), ("llm_cap", 79, "cap"), ("trial_budget", 79, "trial budget"),
        ("memory_mode", "none", "memory_mode"), ("verify_runs", 1, "verify_runs"),
        ("verify_seed_base", 1000, "verify_seed_base"), ("verify_split_policy", "fixed", "verify_split_policy"),
        ("harness_commit", "0" * 40, "harness"),
        ("schema", "other/v1", "schema"),
    ):
        with pytest.raises(A.AdapterStop):
            load_manifest(**{field: value})


def test_manifest_refuses_a_changed_proposer_and_stage_arms():
    bad = manifest_dict()
    bad["proposer"] = dict(bad["proposer"], model="qwen2.5-coder:7b")
    with pytest.raises(A.AdapterStop):
        A.load_manifest(bad)
    bad = manifest_dict()
    bad["proposer"] = dict(bad["proposer"], thinking=True)
    with pytest.raises(A.AdapterStop):
        A.load_manifest(bad)
    with pytest.raises(A.AdapterStop):
        load_manifest(arms=list(A.D3B_ARMS))
    with pytest.raises(A.AdapterStop):
        load_manifest(stage="b", arms=list(A.D3A_ARMS))


def test_manifest_refuses_a_pin_mismatch_and_a_data_file():
    bad = manifest_dict()
    bad["constants"] = dict(bad["constants"], sha256="0" * 64)
    with pytest.raises(A.AdapterStop):
        A.load_manifest(bad)
    with pytest.raises(A.AdapterStop):
        A.load_manifest(manifest_dict(predeclaration={"path": "labels.jsonl", "sha256": "0" * 64}))


def test_apply_proposer_environment_sets_and_refuses_a_conflict(monkeypatch):
    m = load_manifest()
    monkeypatch.delenv("LLAMACPP_BASE_URL", raising=False)
    A.apply_proposer_environment(m)
    assert __import__("os").environ["LLAMACPP_BASE_URL"] == m.proposer_base_url
    monkeypatch.setenv("LLAMACPP_BASE_URL", "http://127.0.0.1:9999/v1")
    with pytest.raises(A.AdapterStop):
        A.apply_proposer_environment(m)


# --------------------------------------------------------------------------- constants and arms

def test_constants_vectors_are_the_file_vectors_bitwise():
    m = load_manifest()
    c = A.load_constants(m)
    raw = json.loads((REPO / CONSTANTS).read_text())
    for arm in ("A1", "A2"):
        for node in m.nodes:
            assert list(c.vectors[arm][node]) == raw["nodes"][node][arm]
    for node in m.nodes:
        assert c.noise[node]["sigma_node"] == raw["nodes"][node]["sigma_node"]
        assert c.ladder[node]["c"] == raw["nodes"][node]["LADDER"]["c"]


def test_constants_refuse_a_changed_sigma_or_node_set(tmp_path):
    m = load_manifest()
    raw = json.loads((REPO / CONSTANTS).read_text())
    raw["nodes"]["digits_mlp"]["sigma_node"] = 0.123
    p = tmp_path / "d3_constants.json"
    p.write_text(json.dumps(raw))
    bad = A.Manifest(**{**m.__dict__, "constants": A.Pin(str(p), hashlib.sha256(p.read_bytes()).hexdigest())})
    with pytest.raises(A.AdapterStop):
        A.load_constants(bad)


def test_controller_selection_and_refusals():
    m = load_manifest()
    c = A.load_constants(m)
    spec = A.load_registered_node(NODE, repo_root=HARNESS)
    ctx = A.node_context(NODE, HARNESS / "nodes" / NODE, spec, c)
    kinds = {arm: type(A.build_controller(arm, ctx, c)).__name__ for arm in A.HARNESS_ARMS}
    assert kinds == {"A0": "ContinueController", "A0R": "RuleLayerController", "A1": "RuleController",
                     "A2": "RuleController", "LADDER": "LadderController"}
    for arm in A.REPLICATE_ARMS + A.LEARNED_ARMS:
        with pytest.raises(A.AdapterStop):
            A.build_controller(arm, ctx, c)
    for arm in A.HARNESS_ARMS:
        kw = A.campaign_kwargs(arm, A.build_controller(arm, ctx, c))
        assert kw["verify_runs"] == 2 and kw["verify_seed_base"] == 20000
        assert kw["compute_budget"].max_worker_runs == 20 and kw["compute_budget"].max_llm_calls == 80
        assert kw["budget"] == 80


def test_openml_node_without_a_cache_is_refused(tmp_path):
    spec = A.load_registered_node("openml_breast_w", repo_root=HARNESS)
    with pytest.raises(A.AdapterStop):
        A.prepare_node_dir("openml_breast_w", tmp_path / "node", spec=spec, harness=HARNESS,
                           data_cache_root=None)


# --------------------------------------------------------------------------- whole campaigns (synthetic)

def test_harness_chunk_runs_eighteen_a0_campaigns_and_resolves_ended_on(tmp_path):
    m = load_manifest()
    out = tmp_path / "chunk"
    summary = run_chunk(_spec(), out, _factory(m), manifest=m.chunk_manifest(), observed=_observed(m))
    assert summary["campaigns"] == 18
    assert summary["worker_runs"] == 18 * 20
    assert summary["ended_on"] == {"worker_runs": 18}
    first = out / "campaigns" / f"{NODE}__s6201"
    camp = json.loads((first / "campaign.json").read_text())
    assert camp["ended_on"] == "worker_runs"
    assert (first / "snapshots" / "w5.json").is_file()
    assert (first / "snapshots" / "final.json").is_file()
    assert (out / "SHA256SUMS").is_file()


def _replicate_factory(m, *, manager_cls=ToggleManager):
    constants = A.load_constants(m)
    workers = []

    def make_worker(node, seed):
        worker = FakeWorker(node, seed)
        workers.append(worker)
        return worker

    factory = A.make_replicate_factory(
        m, constants, harness=HARNESS, apply_env=False,
        manager_factory=lambda mm, seed, rep: manager_cls(),
        worker_factory=make_worker,
    )
    return factory, workers


def test_replicate_chunk_runs_fixr3_and_uses_table_ended_on(tmp_path):
    m = load_manifest()
    factory, workers = _replicate_factory(m)
    spec = _spec(arm="FIXR3")
    summary = run_chunk(spec, tmp_path / "chunk", replicate_factory=factory,
                        manifest=m.chunk_manifest(), observed=_observed(m))
    assert summary["campaigns"] == 18
    # 3 seeded runs per step: six complete steps (18 runs); the seventh cannot be funded.
    assert summary["ended_on"] == {"no_fundable_candidate": 18}
    assert len(workers) == 18 and sum(w.calls for w in workers) == 18 * 18
    first = tmp_path / "chunk" / "campaigns" / f"{NODE}__s6201"
    rows = [json.loads(line)["record"] for line in (first / "runs.jsonl").read_text().splitlines()]
    assert len(rows) == 18 and all(row["success"] for row in rows)
    assert {row["j"] for row in rows} == {0, 1, 2}
    final = json.loads((first / "snapshots" / "final.json").read_text())
    assert final["w"] == 18 and final["ended_on"] == "no_fundable_candidate"


def test_replicate_egate_runs_without_an_incumbent_metric(tmp_path):
    m = load_manifest()
    factory, workers = _replicate_factory(m)
    spec = _spec(arm="EGATE")
    summary = run_chunk(spec, tmp_path / "chunk", replicate_factory=factory,
                        manifest=m.chunk_manifest(), observed=_observed(m))
    assert summary["campaigns"] == 18
    assert sum(w.calls for w in workers) > 0
    first = tmp_path / "chunk" / "campaigns" / f"{NODE}__s6201"
    rows = [json.loads(line)["record"] for line in (first / "runs.jsonl").read_text().splitlines()]
    assert rows and all(row["success"] for row in rows)
    assert 1 <= summary["worker_runs"] // 18 <= 20


class BadPathManager(ToggleManager):
    def propose_next_trial(self, status, memory_context, node_spec):
        from autoresearch.manager.base import ManagerProposal
        return ManagerProposal(
            manager_mode=self.mode, proposal_summary="out of scope", proposal_rationale="",
            target_files=("benchmark.py",), objective="bad",
            extra={"structured_edit": {"type": "python_constant", "path": "benchmark.py",
                                       "symbol": SYMBOL, "old": "0.001", "new": "0.01"}},
        )


def test_replicate_validation_rejects_an_out_of_scope_edit(tmp_path):
    m = load_manifest()
    factory, workers = _replicate_factory(m, manager_cls=BadPathManager)
    spec = _spec(arm="FIXR3")
    summary = run_chunk(spec, tmp_path / "chunk", replicate_factory=factory,
                        manifest=m.chunk_manifest(), observed=_observed(m))
    # Every proposal is a control-plane rejection: its LLM call is charged, no worker run is.
    assert summary["worker_runs"] == 0
    assert summary["ended_on"] == {"llm_call_cap": 18}
    assert sum(w.calls for w in workers) == 0


def test_learned_seam_accepts_a_supplied_a3_prior_but_never_a6():
    from r1.c3.prior_model import FixedPrior
    m = load_manifest()
    c = A.load_constants(m)
    spec = A.load_registered_node(NODE, repo_root=HARNESS)
    ctx = A.node_context(NODE, HARNESS / "nodes" / NODE, spec, c)
    prior = FixedPrior([1.0 / 12.0] * 12, name="A3")
    ctl = A.build_controller("A3", ctx, c, learned={"A3": A.LearnedArm("A3", prior)})
    assert type(ctl).__name__ == "RuleController"
    with pytest.raises(A.AdapterStop):
        A.build_controller("A6", ctx, c, learned={"A6": A.LearnedArm("A6", prior)})
