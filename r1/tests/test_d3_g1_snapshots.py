"""Tests for the D.3 G1 charged-run snapshot contract (synthetic, CPU only)."""
from __future__ import annotations

import json
import shutil

import pytest

from r1.c3.d3.snapshots import (
    ParityBudget,
    SNAPSHOT_SCHEMA,
    SNAPSHOT_WS,
    CountingWorker,
    RecordingController,
    SnapshotParityStop,
    SnapshotRecorder,
    SnapshotStop,
    config_sha256,
    controller_state_sha256,
    wrap,
)
from r1.harness import import_harness

HARNESS = import_harness()

from autoresearch.control_plane.campaign import run_real_campaign  # noqa: E402
from autoresearch.control_plane.controller import ControlDecision  # noqa: E402
from autoresearch.memory.append_store import TrialAppendStore  # noqa: E402
from autoresearch.nodes.registry import load_registered_node  # noqa: E402

from r1.tests.c3_campaign_fixtures import (  # noqa: E402
    ConfigMetricWorker,
    SeededConfigMetricWorker,
)

NODE = "digits_mlp"
SYMBOL = "LEARNING_RATE_INIT"


class ToggleBackend:
    """A deterministic manager that always proposes a valid toggle of one constant."""

    mode = "toggle_backend"
    deterministic = True

    def propose_next_trial(self, status, memory_context, node_spec):
        from autoresearch.manager.base import ManagerProposal

        current = str(getattr(status, "current_constants", {}).get(SYMBOL, "0.001"))
        new = "0.002" if current != "0.002" else "0.001"
        return ManagerProposal(
            manager_mode=self.mode,
            proposal_summary=f"{SYMBOL} {current} -> {new}",
            proposal_rationale="",
            target_files=tuple(node_spec.editable_paths),
            objective="toggle a valid constant",
            extra={"structured_edit": {"type": "python_constant", "path": "train.py",
                                       "symbol": SYMBOL, "old": current, "new": new}},
        )


class VerifyOnce:
    version = "verify_once/v1"

    def __init__(self, at: int) -> None:
        self.at = at

    def decide(self, view, mask):
        if view.epoch == "E2" and view.budget_index == self.at and mask.get("verify"):
            return ControlDecision("verify", {}, self.version, view.input_hash())
        return ControlDecision("continue", {}, self.version, view.input_hash())


class SkipAt:
    version = "skip_at/v1"

    def __init__(self, at: int) -> None:
        self.at = at

    def decide(self, view, mask):
        if view.epoch == "E1" and view.budget_index == self.at and mask.get("skip"):
            return ControlDecision("skip", {}, self.version, view.input_hash())
        return ControlDecision("continue", {}, self.version, view.input_hash())


def _node_copy(tmp):
    node = tmp / "node"
    shutil.copytree(HARNESS / "nodes" / NODE, node, ignore=shutil.ignore_patterns("__pycache__"))
    return node


def _run(tmp, controller, *, W=20, cap=80, seeded=True):
    spec = load_registered_node(NODE, repo_root=HARNESS)
    node = _node_copy(tmp)
    worker = (SeededConfigMetricWorker if seeded else ConfigMetricWorker)(node)
    recorder = SnapshotRecorder(out_dir=tmp / "campaign", stage="a", arm="A2", node=NODE,
                                repetition=0, instance_id=f"{NODE}__s6201")
    kwargs = wrap({
        "node_spec": spec,
        "campaign_id": f"{NODE}__s6201",
        "budget": W,
        "manager_mode": "baseline_manager",
        "memory_mode": "none",
        "records_path": tmp / "campaign" / "ledger.jsonl",
        "worker": worker,
        "proposal_backend": ToggleBackend(),
        "controller": controller,
        "compute_budget": ParityBudget(max_worker_runs=W, max_llm_calls=cap, recorder=recorder),
        "verify_runs": 2,
        "verify_split_policy": "vary",
    }, recorder)
    run_real_campaign(**kwargs)
    return recorder


def _load(tmp, name):
    return json.loads((tmp / "campaign" / "snapshots" / name).read_text())


def test_exact_w_snapshots_include_a_verify_block(tmp_path):
    recorder = _run(tmp_path, VerifyOnce(at=2), W=20)
    # 20 charged runs: 20 main + 4 verify cannot both fit; the budget stops at w=20.
    assert recorder.count == 20
    assert recorder._last_budget.worker_runs == 20
    for w in SNAPSHOT_WS:
        assert (tmp_path / "campaign" / "snapshots" / f"w{w}.json").is_file(), w
    for w in SNAPSHOT_WS:
        snap = _load(tmp_path, f"w{w}.json")
        assert snap["schema"] == SNAPSHOT_SCHEMA
        assert snap["w"] == snap["w_actual"] == snap["worker_runs"] == w
        assert snap["ended"] is False
        assert "train.py" in snap["incumbent_config"]
        assert len(snap["config_sha256"]) == 64
        assert len(snap["controller_state_sha256"]) == 64
        assert snap["llm_calls_basis"] == "budget_observed_at_run"
    # The verify block runs at w = 3..6 in this trace (main at 1,2 then 4 verify runs);
    # w=5 is reached by a seeded run, which is recorded as run_kind=verify.
    assert _load(tmp_path, "w5.json")["run_kind"] == "verify"
    for w in (10, 15, 20):
        assert _load(tmp_path, f"w{w}.json")["run_kind"] == "main"
    assert len(TrialAppendStore(tmp_path / "campaign" / "ledger.jsonl").read_all()) == 16  # 16 main + 4 verify = 20 runs


def test_final_alias_at_w20(tmp_path):
    recorder = _run(tmp_path, VerifyOnce(at=99), W=20)
    assert recorder.count == 20
    digest = recorder.write_final(w_final=20, ended_on="worker_runs")
    snap = _load(tmp_path, "final.json")
    assert snap["final"] is True and snap["ended"] is True
    assert snap["ended_on"] == "worker_runs"
    assert snap["alias_of"] == "w20.json"
    assert snap["alias_sha256"] == recorder.snapshot_hashes()["w20.json"]
    assert len(digest) == 64


def test_skip_charges_no_worker_run(tmp_path):
    # W=6 with a skip at trial 2: six decisions, five worker runs, one snapshot at w=5.
    recorder = _run(tmp_path, SkipAt(at=2), W=6, cap=80)
    assert recorder.count == 5
    assert recorder._last_budget.worker_runs == 5
    assert sorted(recorder.snapshot_hashes()) == ["w5.json"]
    assert _load(tmp_path, "w5.json")["worker_runs"] == 5


def test_parity_stop_on_block_charge():
    rec = SnapshotRecorder(out_dir="/tmp/unused", stage="a", arm="A0", node=NODE,
                           repetition=0, instance_id="x")
    rec.note_run("main", "test")
    with pytest.raises(SnapshotParityStop):
        rec.check_parity(2, where="test")  # wrapper counted 1, budget says 2


def test_parity_budget_fails_closed_without_a_wrapper_count():
    rec = SnapshotRecorder(out_dir="/tmp/unused", stage="a", arm="A0", node=NODE,
                           repetition=0, instance_id="x")
    budget = ParityBudget(max_worker_runs=20, recorder=rec)
    # A harness charge with no matching wrapper run is exactly the block-charge failure.
    with pytest.raises(SnapshotParityStop):
        budget.consume_worker_run(0.1)


def test_snapshot_refuses_overwrite(tmp_path):
    rec = SnapshotRecorder(out_dir=tmp_path, stage="a", arm="A0", node=NODE,
                           repetition=0, instance_id="x")
    # A snapshot needs E1 state; a minimal fake keeps the failure about the file.
    rec._trial = type("T", (), {"trial_id": "t", "incumbent_config": {}, "config_sha256": "0" * 64,
                                "controller_state_sha256": "0" * 64, "last_kept_trial_index": None,
                                "llm_calls": 0, "pending_action": None})()
    rec.start_config = {}
    rec.count = 4
    rec.note_run("main", "test")
    assert (tmp_path / "snapshots" / "w5.json").is_file()
    with pytest.raises(SnapshotStop):
        rec._write_snapshot(5, run_kind="main", where="test")


def test_controller_state_hash_is_deterministic_and_sensitive():
    class C:
        version = "c/v1"
        _plans = {}
        log = []

    c = C()
    a = controller_state_sha256(c)
    assert a == controller_state_sha256(c)
    c.log.append({"x": 1})
    assert controller_state_sha256(c) != a


def test_config_hash_ignores_volatile_formatting():
    assert config_sha256({"train.py": "a = 1\n"}) == config_sha256({"train.py": "a = 1\n"})
    assert config_sha256({"train.py": "a = 1\n"}) != config_sha256({"train.py": "a = 2\n"})


def test_counting_worker_exposes_seed_only_when_supported(tmp_path):
    node = _node_copy(tmp_path)
    rec = SnapshotRecorder(out_dir=tmp_path, stage="a", arm="A0", node=NODE,
                           repetition=0, instance_id="x")
    plain = CountingWorker(ConfigMetricWorker(node), rec)
    seeded = CountingWorker(SeededConfigMetricWorker(node), rec)
    assert not hasattr(plain, "run_trial_at_seed")
    assert hasattr(seeded, "run_trial_at_seed")


def test_recording_controller_reports_action(tmp_path):
    rec = SnapshotRecorder(out_dir=tmp_path, stage="a", arm="A0", node=NODE,
                           repetition=0, instance_id="x")
    view = type("V", (), {"epoch": "E1", "input_hash": lambda self: "h"})()
    ctl = RecordingController(VerifyOnce(at=1), rec)
    ctl.decide(view, {})
    assert rec._controller_calls == 1
