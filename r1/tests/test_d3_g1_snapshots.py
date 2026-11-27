"""Tests for the D.3 G1 charged-run snapshot contract (synthetic, CPU only)."""
from __future__ import annotations

import json
import shutil
from dataclasses import replace

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
    sha256_json,
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
    recorder._worker = kwargs["worker"]
    recorder._node_spec = kwargs["node_spec"]
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


def test_final_is_live_at_w20_and_never_aliases_the_pre_decision_snapshot(tmp_path):
    recorder = _run(tmp_path, VerifyOnce(at=99), W=20)
    assert recorder.count == 20
    digest = recorder.write_final_live(
        w_final=20, ended_on="worker_runs", worker=recorder._worker, node_spec=recorder._node_spec,
        ledger_path=tmp_path / "campaign" / "ledger.jsonl",
    )
    snap = _load(tmp_path, "final.json")
    assert snap["final"] is True and snap["ended"] is True
    assert snap["ended_on"] == "worker_runs"
    assert "alias_of" not in snap
    w20 = _load(tmp_path, "w20.json")
    assert w20["config_sha256"] == snap["config_sha256"]
    pre = _load(tmp_path, "w20_pre.json")
    assert pre["pre_decision"] is True and pre["superseded_by"] == "final.json"
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
                                "llm_calls": 0, "pending_action": None, "controller_calls_at_e1": 0})()
    rec.start_config = {}
    rec.count = 4
    rec.note_decision("E1", "continue")
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


class StatefulController(VerifyOnce):
    """A controller with a decision counter exposed through snapshot_state()."""

    def __init__(self, at: int) -> None:
        super().__init__(at)
        self.n = 0

    def snapshot_state(self):
        return {"n": self.n}

    def decide(self, view, mask):
        self.n += 1
        return super().decide(view, mask)


def test_verify_snapshots_keep_the_e1_controller_state(tmp_path):
    _run(tmp_path, StatefulController(at=2), W=20)
    verify5 = _load(tmp_path, "w5.json")
    assert verify5["run_kind"] == "verify"
    assert verify5["pending_action"] == "verify"

    class Expected:
        def snapshot_state(self):
            return {"n": 4}

    # Trial 2's E1 hook is the fourth decision (E0, trial 1 E1/E2, trial 2 E1); the
    # verify block must carry that E1 value, not the E2 state n=5.
    assert verify5["controller_state_sha256"] == controller_state_sha256(Expected())


def test_hook_parity_is_checked_at_every_hook():
    rec = SnapshotRecorder(out_dir="/tmp/unused", stage="a", arm="A0", node=NODE,
                           repetition=0, instance_id="x")
    with pytest.raises(SnapshotParityStop):
        rec.observe_budget(type("B", (), {"worker_runs": 7, "llm_calls": 0})(), where="hook E1")


def test_controller_repr_fallback_is_refused():
    class Weird:
        pass

    class C:
        version = "c/v1"
        _plans = {}
        log = [Weird()]

    with pytest.raises(SnapshotStop):
        controller_state_sha256(C())


# ---------------------------------------------------------------------------
class _ScriptedManager(ToggleBackend):
    deterministic = False


class _ImprovingWorker(ConfigMetricWorker):
    """Apply fixture edits and report a strictly improving synthetic metric."""

    def run_trial(self, proposal, node_spec, budget_index):
        result = super().run_trial(proposal, node_spec, budget_index)
        return replace(result, parsed_metrics={"val_score": 0.50 + 0.01 * self.runs})


@pytest.mark.parametrize("max_calls,ended_on", [(80, "worker_runs"), (7, "llm_call_cap")])
def test_final_is_the_live_last_keep_at_w_and_an_early_cap(tmp_path, max_calls, ended_on):
    """Revision 4 step (5) finding 1: a keep on the final trial must reach final.json.

    At W the pre-decision w20 record is preserved as w20_pre.json and w20.json is
    canonicalised from the post-decision final; at an early call cap the final carries the
    terminating keep.
    """
    spec = load_registered_node(NODE, repo_root=HARNESS)
    node = _node_copy(tmp_path)
    campaign = tmp_path / "campaign"
    records_path = campaign / "ledger.jsonl"
    rec = SnapshotRecorder(campaign, "a", "A0", NODE, 0, f"{NODE}__s6201")
    worker = _ImprovingWorker(node)
    kwargs = wrap({
        "node_spec": spec,
        "campaign_id": rec.instance_id,
        "budget": 20,
        "manager_mode": "baseline_manager",
        "memory_mode": "append_only_summary",
        "records_path": records_path,
        "worker": worker,
        "proposal_backend": _ScriptedManager(),
        "controller": VerifyOnce(at=99),
        "compute_budget": ParityBudget(max_worker_runs=20, max_llm_calls=max_calls, recorder=rec),
        "verify_runs": 2,
        "verify_split_policy": "vary",
    }, rec)
    run_real_campaign(**kwargs)
    rec.write_final_live(w_final=rec.count, ended_on=ended_on, worker=kwargs["worker"],
                         node_spec=kwargs["node_spec"], ledger_path=records_path)
    rows = TrialAppendStore(records_path).read_all()
    final = _load(tmp_path, "final.json")
    expected = config_sha256({path: (node / path).read_text() for path in final["incumbent_config"]})
    last = rows[-1]
    decision = getattr(last.decision, "value", last.decision)
    assert rec.count == (max_calls if max_calls < 20 else 20)
    assert str(decision).lower() in {"keep", "kept"}
    assert final["config_sha256"] == expected
    assert final["last_kept_trial_index"] == last.budget_index
    if rec.count == 20:
        w20 = _load(tmp_path, "w20.json")
        pre = _load(tmp_path, "w20_pre.json")
        assert w20["config_sha256"] == final["config_sha256"]
        assert pre["pre_decision"] is True and pre["config_sha256"] != final["config_sha256"]


# Replicate-arm recorder callbacks: begin_step / on_charge / write_final_from_state
# ---------------------------------------------------------------------------

def test_replicate_step_snapshots_carry_pending_and_step_state(tmp_path):
    from r1.c3.accounting import ChargedRunCounter

    rec = SnapshotRecorder(out_dir=tmp_path / "campaign", stage="a", arm="FIXR3", node=NODE,
                           repetition=0, instance_id="x")
    start = {"train.py": "LR = 0.001\n"}
    incumbent = {"train.py": "LR = 0.002\n"}
    state = {"arm": "FIXR3", "version": "d3_fixr3/v1", "steps": 2, "incumbent": "a" * 64}
    rec.begin_step(trial_id="t2", incumbent_config=incumbent, start_config=start, state=state,
                   last_kept_trial_index=3, llm_calls=7, step_index=2, pending_action="fixr3_step")
    counter = ChargedRunCounter(W=20, on_charge=rec.on_charge)
    for j in range(5):
        rec.set_pending(step=2, j=j, candidate_metrics=[0.1] * (j + 1),
                        incumbent_metrics=[0.2] * (j + 1), diffs=[-0.1] * (j + 1))
        counter.charge(kind="trial" if j == 0 else "replicate", role="candidate", seed=6201 + j,
                       config_sha256="b" * 64, success=True, j=j, metric=0.1)
    snap = _load(tmp_path, "w5.json")
    assert snap["w"] == snap["worker_runs"] == 5
    assert snap["step_index"] == 2 and snap["trial_id"] == "t2"
    assert snap["pending_action"] == "fixr3_step"
    assert snap["last_kept_trial_index"] == 3 and snap["llm_calls"] == 7
    assert snap["incumbent_config"] == incumbent
    assert snap["config_sha256"] == config_sha256(incumbent)
    assert snap["controller_state_sha256"] == sha256_json(state)
    assert snap["pending"] == {"step": 2, "j": 4, "candidate_metrics": [0.1] * 5,
                               "incumbent_metrics": [0.2] * 5, "diffs": [-0.1] * 5}
    assert rec.count == 5 and counter.used == 5


def test_replicate_on_charge_refuses_a_skipped_charge(tmp_path):
    from r1.c3.accounting import ChargedRun

    rec = SnapshotRecorder(out_dir=tmp_path / "campaign", stage="a", arm="EGATE", node=NODE,
                           repetition=0, instance_id="x")
    rec.begin_step(trial_id="t1", incumbent_config={"train.py": "x\n"}, start_config={"train.py": "x\n"},
                   state={"arm": "EGATE"}, last_kept_trial_index=None, llm_calls=1, step_index=0)
    with pytest.raises(SnapshotParityStop):
        rec.on_charge(ChargedRun(w=2, kind="replicate", role="candidate", seed=6201,
                                 config_sha256="c" * 64, success=True, j=1, metric=0.1))


def test_replicate_final_is_separate_from_w20_and_carries_the_last_keep(tmp_path):
    from r1.c3.accounting import ChargedRunCounter

    rec = SnapshotRecorder(out_dir=tmp_path / "campaign", stage="a", arm="EGATE", node=NODE,
                           repetition=0, instance_id="x")
    start = {"train.py": "x = 1\n"}
    pre = {"train.py": "x = 2\n"}
    post = {"train.py": "x = 3\n"}
    rec.begin_step(trial_id="t4", incumbent_config=pre, start_config=start, state={"steps": 4},
                   last_kept_trial_index=3, llm_calls=9, step_index=4, pending_action="egate_pair")
    counter = ChargedRunCounter(W=20, on_charge=rec.on_charge)
    while counter.left:
        counter.charge(kind="trial" if counter.used == 0 else "replicate", role="candidate",
                       seed=6201, config_sha256="d" * 64, success=True,
                       j=0 if counter.used == 0 else 1, metric=0.1)
    digest = rec.write_final_from_state(w_final=20, ended_on="worker_runs", incumbent_config=post,
                                        state={"steps": 5}, last_kept_trial_index=4, llm_calls=10,
                                        trial_id="t4", step_index=4)
    snap = _load(tmp_path, "final.json")
    assert len(digest) == 64
    assert snap["final"] is True and snap["ended_on"] == "worker_runs"
    assert snap["incumbent_config"] == post
    assert snap["config_sha256"] == config_sha256(post)
    assert snap["last_kept_trial_index"] == 4
    assert "alias_of" not in snap
    assert snap["controller_state_sha256"] == sha256_json({"steps": 5})
    # The final governs at W: the canonical w20 carries the post-decision config, and the
    # pre-decision record is preserved separately for replay.
    assert _load(tmp_path, "w20.json")["incumbent_config"] == post
    assert _load(tmp_path, "w20.json")["config_sha256"] == config_sha256(post)
    assert _load(tmp_path, "w20.json")["canonical_final"] == "final.json"
    pre_record = _load(tmp_path, "w20_pre.json")
    assert pre_record["incumbent_config"] == pre
    assert pre_record["pre_decision"] is True and pre_record["superseded_by"] == "final.json"


def test_w_zero_final_refuses_a_non_cap_end(tmp_path):
    rec = SnapshotRecorder(out_dir=tmp_path / "campaign", stage="a", arm="EGATE", node=NODE,
                           repetition=0, instance_id="x")
    with pytest.raises(SnapshotStop):
        rec.write_final_from_state(w_final=0, ended_on="worker_runs", incumbent_config={"x": "y"},
                                   state={"steps": 0}, last_kept_trial_index=None, llm_calls=0)


def test_replicate_final_requires_the_recorded_w(tmp_path):
    rec = SnapshotRecorder(out_dir=tmp_path / "campaign", stage="a", arm="EGATE", node=NODE,
                           repetition=0, instance_id="x")
    rec.count = 3
    with pytest.raises(SnapshotParityStop):
        rec.write_final_from_state(w_final=20, ended_on="worker_runs", incumbent_config={"x": "y"},
                                   state={"steps": 1}, last_kept_trial_index=None, llm_calls=1)
