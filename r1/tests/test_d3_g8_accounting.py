"""D.3 gap G8: run accounting (pre-declaration revision 4 §5 "Run accounting", §3.1). Synthetic only.

AI-assisted (Claude).
"""
from __future__ import annotations

import json

import pytest

from r1.c3 import accounting as A
from r1.c3 import d3_analysis as D3


def _write(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return path


def _trial(b, mode="w", replicates=None, verify=None):
    control = {}
    if replicates is not None:
        control["replicates"] = replicates
    if verify is not None:
        control["verify"] = verify
    return {"budget_index": b, "worker_mode": mode, "extra": {"control": control}}


def _rep(role, j, charged=True, success=True, seed=None):
    return {"role": role, "j": j, "seed": 6500 + j if seed is None else seed, "success": success, "charged": charged}


def _usage(tmp_path, rows, events=(), deterministic=False):
    return A.campaign_usage(_write(tmp_path / "trials.jsonl", rows), _write(tmp_path / "events.jsonl", list(events)),
                            arm="FIXR3", instance="digits_mlp__s6201", information_set="s", worker_run_cap=20,
                            llm_call_cap=80, manager_deterministic=deterministic)


def test_replicate_runs_are_counted_and_reused_incumbent_runs_are_not(tmp_path):
    rows = [_trial(1, replicates=[_rep("candidate", 1), _rep("candidate", 2)]),            # first trial: 3 runs
            _trial(2, replicates=[_rep("candidate", 1), _rep("candidate", 2, success=False)]),  # failed at j = 2
            _trial(3, mode="control_plane"),                                                # skip: no run
            _trial(4, mode="w_precheck"),                                                   # precheck: no run
            _trial(5, replicates=[_rep("candidate", 1), _rep("incumbent", 1, charged=False),
                                  _rep("incumbent", 2, charged=True)]),
            _trial(6, verify={"r": 2})]
    u = _usage(tmp_path, rows)
    assert (u.replicate_runs, u.replicate_runs_reused) == (6, 1)
    assert u.worker_runs == 4 + 6 + 4  # four trial runs, six charged replicates, one verify of 2 r = 4


def test_reissued_llm_calls_never_count_against_the_cap(tmp_path):
    events = [{"event_type": "proposal_created", "payload": {}},
              {"event_type": A.LLM_CALL_REISSUED_EVENT, "payload": {"reason": "no_progress"}},
              {"event_type": A.LLM_CALL_REISSUED_EVENT, "payload": {"reason": "no_progress"}},
              {"event_type": "proposal_created", "payload": {}}]
    u = _usage(tmp_path, [_trial(1), _trial(2)], events)
    assert u.llm_calls == 2 and u.reissued_llm_calls == 2


@pytest.mark.parametrize("bad,match", [
    ([_rep("judge", 1)], "role"),
    ([{**_rep("candidate", 1), "j": True}], "integer"),
    ([_rep("candidate", 10)], "0..9"),
    ([{**_rep("candidate", 1), "charged": 1}], "boolean"),
    ([_rep("candidate", 0)], "trial's own run"),
    ([_rep("candidate", 1, charged=False)], "always charged"),
    ([_rep("incumbent", 1), _rep("incumbent", 1, charged=False)], "twice"),
    ("x", "must be a list"),
])
def test_malformed_replicate_entries_are_refused(tmp_path, bad, match):
    with pytest.raises(ValueError, match=match):
        _usage(tmp_path, [_trial(1, replicates=bad)])


def test_replicates_on_a_trial_whose_worker_did_not_run_are_refused(tmp_path):
    with pytest.raises(ValueError, match="did not run"):
        _usage(tmp_path, [_trial(1, mode="control_plane", replicates=[_rep("candidate", 1)])])


def test_usage_without_replicates_is_unchanged(tmp_path):
    u = _usage(tmp_path, [_trial(1), _trial(2, verify={"r": 2}), _trial(3, mode="control_plane")])
    assert (u.worker_runs, u.replicate_runs, u.replicate_runs_reused, u.reissued_llm_calls) == (6, 0, 0, 0)


def test_counter_charges_singly_refuses_unfundable_steps_and_stops_over_w():
    seen = []
    c = A.ChargedRunCounter(W=5, on_charge=lambda run: seen.append(run.w))
    c.require(3)
    for j in range(3):
        c.charge(kind="replicate" if j else "trial", role="candidate", seed=6201 if j == 0 else 6500 + j,
                 config_sha256="c1", success=True, j=j, metric=0.9)
    assert (c.used, c.left, seen) == (3, 2, [1, 2, 3])
    assert c.can_fund(2) and not c.can_fund(3)
    with pytest.raises(A.UnfundableStep):
        c.require(3)
    assert c.used == 3  # the refused step charged nothing
    c.charge(kind="verify", role="candidate", seed=1, config_sha256="c1", success=True, metric=0.9)
    c.charge(kind="verify", role="incumbent", seed=1, config_sha256="c0", success=False)
    with pytest.raises(A.OverBudget):
        c.charge(kind="trial", role="candidate", seed=6201, config_sha256="c2", success=True, metric=0.9)
    assert seen == [1, 2, 3, 4, 5]


def test_counter_snapshot_hook_sees_every_budget_point_exactly():
    points = []
    c = A.ChargedRunCounter(W=D3.W, on_charge=lambda run: points.append(run.w) if run.w in D3.BUDGET_POINTS else None)
    for k in range(D3.W):
        c.charge(kind="trial", role="candidate", seed=6201, config_sha256=f"c{k}", success=True, metric=0.5)
    assert points == list(D3.BUDGET_POINTS)


def test_counter_lookup_returns_failed_runs_too_and_validates_inputs():
    c = A.ChargedRunCounter(W=4)
    c.charge(kind="replicate", role="incumbent", seed=6501, config_sha256="c0", success=False, j=1)
    assert c.lookup("c0", 6501).success is False and c.lookup("c0", 6502) is None
    with pytest.raises(ValueError, match="kind"):
        c.charge(kind="audit", role="candidate", seed=1, config_sha256="x", success=True, metric=1.0)
    with pytest.raises(ValueError, match="role"):
        c.charge(kind="trial", role="judge", seed=1, config_sha256="x", success=True, metric=1.0)
    with pytest.raises(ValueError, match="finite"):
        c.charge(kind="trial", role="candidate", seed=1, config_sha256="x", success=True, metric=float("nan"))
    with pytest.raises(ValueError, match="records its metric"):
        c.charge(kind="trial", role="candidate", seed=1, config_sha256="x", success=True)
    with pytest.raises(ValueError):
        A.ChargedRunCounter(W=0)
    with pytest.raises(ValueError):
        c.can_fund(-1)


@pytest.mark.parametrize("runs,calls,arm,unfundable,expect", [
    (20, 30, "A0", False, "worker_runs"),
    (20, 80, "A2", False, "worker_runs"),        # at W the table says worker_runs even at the cap
    (12, 80, "A2", False, "llm_call_cap"),
    (18, 80, "FIXR3", True, "llm_call_cap"),     # at the cap, never no_fundable_candidate
    (18, 7, "FIXR3", True, "no_fundable_candidate"),
    (15, 9, "EGATE", True, "no_fundable_candidate"),
])
def test_table_ended_on_follows_the_pinned_analysis(runs, calls, arm, unfundable, expect):
    got = A.table_ended_on(worker_runs=runs, llm_calls=calls, arm=arm, unfundable=unfundable)
    assert got == expect
    row = {"worker_runs": runs, "llm_calls": calls, "ended_on": got, "arm": arm}
    D3._check_ended_on("row 0", row, "D.3a")  # the analysis accepts it


def test_table_ended_on_refusals():
    with pytest.raises(A.OverBudget):
        A.table_ended_on(worker_runs=21, llm_calls=5, arm="A0")
    with pytest.raises(A.OverBudget):
        A.table_ended_on(worker_runs=3, llm_calls=81, arm="A0")
    with pytest.raises(ValueError, match="not ended"):
        A.table_ended_on(worker_runs=18, llm_calls=7, arm="A0", unfundable=True)  # only FIXR3/EGATE
    with pytest.raises(ValueError, match="not ended"):
        A.table_ended_on(worker_runs=5, llm_calls=7, arm="FIXR3")


@pytest.mark.parametrize("cause,card,expect", [
    ("host_kill", None, "infrastructure"), ("walltime", None, "infrastructure"),
    ("no_progress", None, "infrastructure"), ("invalid_config", None, "proposal"),
    ("admitted_runtime_error", None, "proposal"),
    ("budget_hit", (0, 0), "proposal"),          # T0 budget hit with no other process on the card
    ("budget_hit", (1, 0), "infrastructure"), ("oom", (0, 2), "infrastructure"), ("oom", (0, 0), "proposal"),
])
def test_failure_classification_is_the_rows_literal_condition(cause, card, expect):
    assert A.classify_worker_failure(cause, card_other_processes=card) == expect


def test_cpu_sharing_switch_is_off_as_built_and_the_alternative_needs_a_record():
    assert A.CPU_SHARING_IS_INFRASTRUCTURE is False  # §13 item 31, as built
    assert A.classify_worker_failure("budget_hit", card_other_processes=(0, 0),
                                     host_other_processes=(3, 3)) == "proposal"
    assert A.classify_worker_failure("budget_hit", card_other_processes=(0, 0), host_other_processes=(3, 0),
                                     cpu_sharing_is_infrastructure=True) == "infrastructure"
    with pytest.raises(ValueError, match="host's other compute processes"):
        A.classify_worker_failure("budget_hit", card_other_processes=(0, 0), cpu_sharing_is_infrastructure=True)


@pytest.mark.parametrize("card", [None, (0,), (None, 0), (-1, 0), (True, 0)])
def test_unknown_card_record_is_refused(card):
    with pytest.raises(ValueError):
        A.classify_worker_failure("oom", card_other_processes=card)


def test_unknown_cause_is_refused():
    with pytest.raises(ValueError, match="unknown failure cause"):
        A.classify_worker_failure("runtime_error")
