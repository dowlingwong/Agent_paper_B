"""Tests for the D.3 G1 replicate-arm loop (FIXR3/EGATE), synthetic and CPU only."""
from __future__ import annotations

import json

import pytest

from r1.c3.d3.replicate_campaign import ReplicateStop, ReplicateUnit, projection, run_replicate_campaign
from r1.c3.d3.snapshots import SnapshotRecorder, config_sha256, sha256_json
from r1.c3.d3_replicate import EgateEngine, Fixr3Engine, RunOutcome
from r1.harness import import_harness

import_harness()

NODE = "digits_mlp"
INSTANCE = "digits_mlp__s6201"


def _load(cdir, name):
    return json.loads((cdir / "snapshots" / name).read_text())


def _unit(engine, *, metric=0.5, fail_at=None):
    state = {"n": 0}

    def propose(step_index, incumbent_config, llm_calls):
        return {"step": step_index, "llm_calls": llm_calls}

    def validate(proposal):
        contents = {"train.py": f"X = {proposal['step']}\n"}
        return contents, config_sha256(contents)

    def run_trial(proposal, config, seed, j, budget_index):
        state["n"] += 1
        if fail_at is not None and state["n"] == fail_at:
            raise RuntimeError("synthetic worker failure")
        return True, float(metric) + 0.01 * j, 0.01

    return ReplicateUnit(engine=engine, propose=propose, validate=validate, run_trial=run_trial,
                         start_config={"train.py": "X = -1\n"})


def test_fixr3_replicate_campaign_writes_exact_w_and_a_separate_final(tmp_path):
    cdir = tmp_path / "campaign"
    rec = SnapshotRecorder(out_dir=cdir, stage="a", arm="FIXR3", node=NODE,
                           repetition=0, instance_id=INSTANCE)
    unit = _unit(Fixr3Engine(6201))
    summary = run_replicate_campaign(instance_id=INSTANCE, repetition=0, unit=unit,
                                     recorder=rec, stage="a", node=NODE)
    # 3 runs per step, 20 runs: six complete steps (18) and the seventh cannot be funded.
    assert summary["worker_runs"] == 18
    assert summary["ended_on"] == "no_fundable_candidate"
    assert summary["proposal_calls"] == summary["llm_calls"] == 7
    assert len(summary["steps"]) == 6
    assert len(summary["attempts"]) == 18
    assert (cdir / "snapshots" / "w5.json").is_file()
    assert (cdir / "snapshots" / "w15.json").is_file()
    assert not (cdir / "snapshots" / "w20.json").exists()
    w5 = _load(cdir, "w5.json")
    assert w5["w"] == 5 and w5["pending_action"] == "fixr3_step"
    assert w5["step_index"] == 1 and w5["trial_id"] == f"{INSTANCE}__t1"
    assert "pending" in w5 and w5["pending"]["step"] == 1
    final = _load(cdir, "final.json")
    assert final["final"] is True and final["w"] == 18
    assert final["ended_on"] == "no_fundable_candidate"
    assert "alias_of" not in final
    # The first step is kept without a test; later steps with zero variance are discarded.
    assert final["incumbent_config"] == {"train.py": "X = 0\n"}
    assert final["config_sha256"] == config_sha256({"train.py": "X = 0\n"})
    from r1.c3.accounting import ChargedRunCounter
    assert final["controller_state_sha256"] == sha256_json(projection(unit.engine, ChargedRunCounter(W=20)))


def test_egate_replicate_campaign_runs_pairs_and_reuses_incumbent(tmp_path):
    cdir = tmp_path / "campaign"
    rec = SnapshotRecorder(out_dir=cdir, stage="a", arm="EGATE", node=NODE,
                           repetition=0, instance_id=INSTANCE)
    # A rising metric makes the gate commit early, so every step runs at least one pair.
    unit = _unit(EgateEngine(6201), metric=0.5)
    calls = {"n": 0}
    inner = unit.run_trial

    def rising(proposal, config, seed, j, budget_index):
        calls["n"] += 1
        ok, metric, seconds = inner(proposal, config, seed, j, budget_index)
        return ok, metric + 0.2 * calls["n"], seconds

    unit.run_trial = rising
    summary = run_replicate_campaign(instance_id=INSTANCE, repetition=0, unit=unit,
                                     recorder=rec, stage="a", node=NODE)
    assert summary["ended_on"] in ("worker_runs", "no_fundable_candidate")
    assert summary["worker_runs"] <= 20
    assert (cdir / "snapshots" / "final.json").is_file()
    # No incumbent run is charged twice at the same seed within a step: the engine either
    # charges a fresh pair or records the existing run as reused.
    for step in summary["steps"]:
        seen = set()
        for entry in step["replicates"]:
            key = (entry["role"], entry["j"])
            assert key not in seen
            seen.add(key)


def test_worker_failure_is_charged_and_recorded(tmp_path):
    cdir = tmp_path / "campaign"
    rec = SnapshotRecorder(out_dir=cdir, stage="a", arm="FIXR3", node=NODE,
                           repetition=0, instance_id=INSTANCE)
    unit = _unit(Fixr3Engine(6201), fail_at=2)
    summary = run_replicate_campaign(instance_id=INSTANCE, repetition=0, unit=unit,
                                     recorder=rec, stage="a", node=NODE)
    assert summary["steps"][0]["decision"] == "failed_invalid"
    assert summary["attempts"][1]["success"] is False
    assert summary["attempts"][1]["cause"].startswith("RuntimeError")
    # The failed replicate is charged; the campaign then continues to W.
    assert summary["worker_runs"] == 20


def test_projection_refuses_an_unknown_arm():
    class E:
        arm = "A0"
        version = "v"
        instance_seed = 6201
        steps = 0
        incumbent = None
        seeds = ()

    class C:
        def lookup(self, *a):
            return None

    with pytest.raises(ReplicateStop):
        projection(E(), C())


def test_replicate_binds_the_declared_budget(tmp_path):
    rec = SnapshotRecorder(out_dir=tmp_path, stage="a", arm="FIXR3", node=NODE,
                           repetition=0, instance_id=INSTANCE)
    with pytest.raises(ReplicateStop):
        run_replicate_campaign(instance_id=INSTANCE, repetition=0, unit=_unit(Fixr3Engine(6201)),
                               recorder=rec, W=19)
