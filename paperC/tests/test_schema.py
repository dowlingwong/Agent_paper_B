"""Runbook P1: the spt_transition/v1 schema and its checks (plan §4.1-§4.2; review round 1 fixes)."""
import copy
import json
import math
from pathlib import Path

import pytest

from paperc import schema as S

SCHEMA_FILE = Path(__file__).resolve().parents[1] / "schemas" / "spt_transition_v1.json"
AUDIT = [10_000_000, 10_000_004]


# ---------------------------------------------------------------- valid synthetic campaigns (test-only generator)

def _row(step, *, epoch, action, st, out, W=4, cap=6, branch=(), fork=None, campaign="c1", seed=50001,
         rule=None, forced=False, end=None, terminal=None):
    rule_forced = rule is not None and rule.startswith("rule_")
    state = {"proposal_hash": f"p{step}", "proposal_ref": None, "candidate_hash": None, "duplicate": False,
             "noop": False, "eligible": not rule_forced, "rule_forced": rule_forced, "key_seen": False,
             "incumbent_hash": "i0", "incumbent_recorded": 0.50, "incumbent_obs": 1,
             "candidate_delta_hat": None, "candidate_divergent": False, "candidate_invalid": False,
             "candidate_obs": 0,
             "runs_used": 0, "runs_left": W, "calls_used": 0, "calls_left": cap, "slots_left": cap,
             "keeps_so_far": 0, "prior_skips": 0, "sigma_node": 0.01, "noise_source": "C1", "history_ref": None,
             "forecasts": {"a3": {"pi": 0.0, "mu": 0.0, "tau": 0.02, "sigma": 0.01, "v_star": 0.008,
                                  "m_hat": None, "g": 0.001}}}
    state.update(st)
    state["runs_left"] = W - state["runs_used"]
    state["calls_left"] = cap - state["calls_used"]
    outcome = {"runs_consumed": 0, "calls_consumed": 0, "next_incumbent_hash": state["incumbent_hash"],
               "delta_hat": None, "divergent": False, "kept": None}
    outcome.update(out)
    policy = {"policy": "static:0.1,0", "policy_sha": None, "action_prob": 1.0}
    if forced:
        policy.update(action_prob=None, behaviour_action="execute", behaviour_prob=1.0)
    return {
        "schema": S.SCHEMA,
        "identity": {"node": "syn_null", "suite": "E-SYN", "tier": "E-SYN", "instance_id": f"syn_null:{seed}",
                     "campaign_id": campaign, "step_index": step, "epoch": epoch, "branch_path": list(branch),
                     "root_id": campaign, "fork_id": branch[0].split(":")[0] if branch else None},
        "env": {"proposer_model": "scripted", "manager_gguf_sha256": None, "thinking": "n/a", "W": W,
                "llm_cap": cap, "memory_mode": "none", "skip_display": "one_line", "edit_schema": "synthetic",
                "run_budget": "synthetic", "constants": {"g": 0.001}},
        "policy": policy,
        "seeds": {"instance_seed": seed, "manager_rep": 0, "worker_seed": None, "audit_seed_block": list(AUDIT)},
        "state": state,
        "action": {"action": action, "forced": forced,
                   "rule": rule if rule else ("fork_arm" if forced else "policy")},
        "outcome": outcome,
        "provenance": {"host": "cloud", "gpu": None, "harness_commit": None, "paper_commit": None,
                       "llama_build": None, "cache_prompt": None, "phase": "P1", "label": "FIXTURE"},
        "fork": fork,
        "episode_end": end,
        "terminal": terminal,
    }


TERM = {"y_terminal": 0.52, "y_terminal_per_seed": [0.51, 0.53], "audit_seeds": [10_000_000, 10_000_001],
        "y_start": 0.50}


def valid_campaign(campaign="c1", seed=50001):
    """Root: E1 execute c0 -> E2 keep -> E1 rule-duplicate skip -> E1 execute c2 -> E2 discard (ends at W = 4)."""
    k = dict(campaign=campaign, seed=seed)
    return [
        _row(0, epoch="E1", action="execute", st={"candidate_hash": "c0"},
             out={"runs_consumed": 1, "calls_consumed": 1, "delta_hat": 0.02}, **k),
        _row(1, epoch="E2", action="keep",
             st={"candidate_hash": "c0", "runs_used": 1, "calls_used": 1, "slots_left": 5,
                 "candidate_delta_hat": 0.02, "candidate_obs": 1,
                 "forecasts": {"a3": {"pi": 0.0, "mu": 0.0, "tau": 0.02, "sigma": 0.01, "v_star": 0.008,
                                      "m_hat": 0.015, "g": 0.001}}},
             out={"next_incumbent_hash": "c0", "kept": True}, **k),
        _row(2, epoch="E1", action="skip", rule="rule_duplicate",
             st={"candidate_hash": "c0", "duplicate": True, "incumbent_hash": "c0", "incumbent_recorded": 0.52,
                 "runs_used": 1, "calls_used": 1, "slots_left": 5, "keeps_so_far": 1, "key_seen": True},
             out={"calls_consumed": 1}, **k),
        _row(3, epoch="E1", action="execute",
             st={"candidate_hash": "c2", "incumbent_hash": "c0", "incumbent_recorded": 0.52, "runs_used": 1,
                 "calls_used": 2, "slots_left": 4, "keeps_so_far": 1, "prior_skips": 1},
             out={"runs_consumed": 3, "calls_consumed": 1, "delta_hat": -0.01}, **k),
        _row(4, epoch="E2", action="discard",
             st={"candidate_hash": "c2", "incumbent_hash": "c0", "incumbent_recorded": 0.52, "runs_used": 4,
                 "calls_used": 3, "slots_left": 3, "keeps_so_far": 1, "prior_skips": 1,
                 "candidate_delta_hat": -0.01, "candidate_obs": 1},
             out={"kept": False}, end={"kind": "terminated", "reason": "W"}, terminal=copy.deepcopy(TERM), **k),
    ]


FORK = {"selection_rule": "both", "q_uniform": 0.2, "q_oversample": 0.5, "near_threshold": True,
        "uniform": True, "oversample": True, "p_select": 1 - 0.8 * 0.5, "channel_arms": False, "replicate": 1}


def fork_continuation():
    """Fork of the root at step 3 (forced skip of c2), then an execute; truncated by infrastructure."""
    b = ("f3:skip:r1",)
    return [
        _row(3, epoch="E1", action="skip", forced=True, branch=b, fork=copy.deepcopy(FORK),
             st={"candidate_hash": "c2", "incumbent_hash": "c0", "incumbent_recorded": 0.52, "runs_used": 1,
                 "calls_used": 2, "slots_left": 4, "keeps_so_far": 1, "prior_skips": 1},
             out={"calls_consumed": 1}),
        _row(4, epoch="E1", action="execute", branch=b, fork=copy.deepcopy(FORK),
             st={"candidate_hash": "c3", "incumbent_hash": "c0", "incumbent_recorded": 0.52, "runs_used": 1,
                 "calls_used": 3, "slots_left": 3, "keeps_so_far": 1, "prior_skips": 2},
             out={"runs_consumed": 1, "calls_consumed": 1, "delta_hat": 0.0},
             end={"kind": "truncated", "reason": "infrastructure"}),
    ]


def checks_of(viol):
    return sorted({v.check for v in viol})


def _only(viol, check):
    assert checks_of(viol) == [check], viol


# ---------------------------------------------------------------- valid data passes

def test_valid_campaign_has_no_violation():
    rows = valid_campaign() + fork_continuation()
    for r in rows:
        assert S.validate(r) == [], S.validate(r)
    assert S.check_campaign(rows) == []


def test_round_trip():
    for r in valid_campaign():
        t = S.from_dict(r)
        assert S.from_dict(json.loads(json.dumps(S.to_dict(t)))) == t


def test_final_select_row_is_valid():
    rows = valid_campaign()
    rows[-1]["episode_end"] = rows[-1]["terminal"] = None
    fin = _row(5, epoch="final", action="select",
               st={"candidate_hash": None, "incumbent_hash": "c0", "incumbent_recorded": 0.52, "runs_used": 4,
                   "calls_used": 3, "slots_left": 3, "keeps_so_far": 1, "prior_skips": 1},
               out={"next_incumbent_hash": "c0"}, end={"kind": "terminated", "reason": "W"},
               terminal=copy.deepcopy(TERM))
    fin["action"]["selected"] = "c0"
    assert S.check_campaign(rows + [fin]) == []


# ---------------------------------------------------------------- MAJOR fixes (review round 1)

def test_m1_divergent_candidate_cannot_be_kept():
    rows = valid_campaign()
    rows[0]["outcome"].update(delta_hat=None, divergent=True)
    rows[1]["state"].update(candidate_delta_hat=None, candidate_divergent=True)
    assert checks_of(S.check_campaign(rows)) == ["epoch_sequence", "outcome"]
    # the row rule alone catches it on the first row of an E2 fork (no execute in the trajectory)
    rows[1]["identity"].update(branch_path=["f1:keep:r1"], fork_id="f1")
    rows[1]["fork"] = copy.deepcopy(FORK)
    rows[1]["action"]["forced"] = True
    rows[1]["action"]["rule"] = "fork_arm"
    rows[1]["policy"].update(action_prob=None, behaviour_action="discard", behaviour_prob=1.0)
    rows[1]["episode_end"] = {"kind": "truncated", "reason": "host"}
    assert "outcome" in checks_of(S.check_campaign([rows[1]]))
    # discarding it (rule_divergent) is valid; the incumbent then stays i0
    rows = valid_campaign()[:2]
    rows[0]["outcome"].update(delta_hat=None, divergent=True)
    rows[1]["state"].update(candidate_delta_hat=None, candidate_divergent=True, rule_forced=True, eligible=False)
    rows[1]["action"].update(action="discard", rule="rule_divergent")
    rows[1]["outcome"].update(kept=False, next_incumbent_hash="i0")
    rows[1]["episode_end"] = {"kind": "truncated", "reason": "host"}
    assert S.check_campaign(rows) == []


def test_m2_m_hat_at_e1_is_a_future_value():
    rows = valid_campaign()
    rows[0]["state"]["forecasts"]["a3"]["m_hat"] = 0.01
    _only(S.check_campaign(rows), "no_future")


def test_m2_candidate_result_at_e1_is_a_future_value():
    rows = valid_campaign()
    rows[3]["state"].update(candidate_delta_hat=-0.01, candidate_obs=1)
    _only(S.check_campaign(rows), "no_future")


def test_m3_consumption_beyond_what_is_left():
    rows = valid_campaign()
    rows[4]["outcome"]["calls_consumed"] = 4        # calls_left is 3 on the last row
    _only(S.check_campaign(rows), "budget")


def test_m3_root_starts_at_zero():
    rows = valid_campaign()
    for r in rows:
        r["state"]["calls_used"] += 1
        r["state"]["calls_left"] -= 1
    _only(S.check_campaign(rows), "budget")


def test_m3_fork_starts_from_parent_counters():
    rows = valid_campaign() + fork_continuation()
    for r in rows[5:]:
        r["state"]["runs_used"] -= 1
        r["state"]["runs_left"] += 1
    _only(S.check_campaign(rows), "budget")


def test_m4_execute_cannot_change_the_incumbent():
    rows = valid_campaign()
    rows[3]["outcome"]["next_incumbent_hash"] = "c2"
    rows[4]["state"]["incumbent_hash"] = "c2"
    rows[4]["outcome"]["next_incumbent_hash"] = "c2"
    _only(S.check_campaign(rows), "next_state")


def test_m4_keep_must_change_the_incumbent():
    rows = valid_campaign()
    rows[1]["outcome"]["next_incumbent_hash"] = "i0"
    for r in rows[2:]:
        r["state"]["incumbent_hash"] = "i0"
        r["outcome"]["next_incumbent_hash"] = "i0"
    _only(S.check_campaign(rows), "next_state")


def test_m4_last_row_discard_with_changed_incumbent():
    rows = valid_campaign()
    rows[4]["outcome"]["next_incumbent_hash"] = "c2"
    _only(S.check_campaign(rows), "next_state")


def test_m4_fork_starts_from_parent_incumbent():
    rows = valid_campaign() + fork_continuation()
    for r in rows[5:]:
        r["state"]["incumbent_hash"] = "i0"
        r["outcome"]["next_incumbent_hash"] = "i0"
    _only(S.check_campaign(rows), "next_state")


@pytest.mark.parametrize("reason", ["infrastructure", "policy_stop"])
def test_m5_terminated_with_a_truncation_reason_or_stop(reason):
    rows = valid_campaign()
    rows[-1]["episode_end"]["reason"] = reason
    _only(S.check_campaign(rows), "terminal")


def test_m5_free_text_reason_is_rejected():
    r = valid_campaign()[-1]
    r["episode_end"]["reason"] = "divergence"
    assert any("reason" in e for e in S.validate(r))


def test_m5_terminated_at_W_with_runs_left():
    rows = valid_campaign()[:2]
    rows[-1]["episode_end"] = {"kind": "terminated", "reason": "W"}
    rows[-1]["terminal"] = copy.deepcopy(TERM)
    _only(S.check_campaign(rows), "terminal")


def test_m6_forced_rows_carry_no_propensity():
    rows = valid_campaign() + fork_continuation()
    rows[5]["policy"]["action_prob"] = 1.0
    _only(S.check_campaign(rows), "propensity")
    rows = valid_campaign() + fork_continuation()
    rows[5]["policy"]["behaviour_action"] = None
    _only(S.check_campaign(rows), "propensity")


# ---------------------------------------------------------------- the other checks, one corruption each

def test_budget_chain():
    rows = valid_campaign()
    rows[3]["state"]["runs_used"] = 2
    rows[3]["state"]["runs_left"] = 2
    _only(S.check_campaign(rows), "budget")


def test_budget_conservation():
    rows = valid_campaign()
    rows[1]["state"]["calls_left"] = 4
    _only(S.check_campaign(rows), "budget")


def test_contiguous():
    rows = valid_campaign()
    for r in rows[3:]:
        r["identity"]["step_index"] += 1
    _only(S.check_campaign(rows), "contiguous")


def test_terminal_missing_and_on_truncated():
    rows = valid_campaign()
    rows[-1]["terminal"] = None
    _only(S.check_campaign(rows), "terminal")
    rows = fork_continuation()
    rows[-1]["terminal"] = copy.deepcopy(TERM)
    _only(S.check_campaign(rows), "terminal")
    rows = fork_continuation()
    rows[-1]["episode_end"] = None
    _only(S.check_campaign(rows), "terminal")


def test_propensity_replay_on_a_decision_view():
    seen = []

    def behaviour(view):
        seen.append(view)
        assert not hasattr(view, "action") and not hasattr(view, "outcome")
        if view.identity.step_index == 3:
            return "skip", 1.0
        if view.identity.epoch == "E1":
            return "execute", 1.0
        return ("keep" if view.state.candidate_delta_hat > 0 else "discard"), 1.0

    _only(S.check_campaign(valid_campaign(), behaviour=behaviour), "propensity")
    assert all(isinstance(v, S.DecisionView) for v in seen)
    assert 2 not in [v.identity.step_index for v in seen]          # rule-forced row not replayed


@pytest.mark.parametrize("prob", [float("nan"), None, "1.0"])
def test_propensity_rejects_invalid_probabilities(prob):
    rows = valid_campaign()[:1]
    rows[0]["episode_end"] = {"kind": "truncated", "reason": "host"}
    _only(S.check_campaign(rows, behaviour=lambda v: ("execute", prob)), "propensity")


def test_design_weight():
    rows = fork_continuation()
    for r in rows:
        r["fork"]["p_select"] = 0.5
    _only(S.check_campaign(rows), "design_weight")
    rows = fork_continuation()
    for r in rows:
        r["fork"].update(selection_rule="uniform", near_threshold=False, oversample=True, p_select=0.2)
    _only(S.check_campaign(rows), "design_weight")


@pytest.mark.parametrize("name", ["y_terminal", "audit_value", "future_delta", "immediate_measured", "next_keep"])
def test_no_future_names(name):
    rows = valid_campaign()
    rows[1]["state"][name] = 0.5
    _only(S.check_campaign(rows), "no_future")


class _Reg:
    def paper_b_block(self, node, seed):
        return "paper_b" if 7001 <= seed < 7011 else None


@pytest.mark.parametrize("where", ["instance", "worker", "eps", "audit_block"])
def test_seed_fields_against_registry(where):
    rows = valid_campaign()
    for r in rows:
        if where == "instance":
            r["seeds"]["instance_seed"] = 7005
            r["identity"]["instance_id"] = "syn_null:7005"
        elif where == "worker":
            r["seeds"]["worker_seed"] = 7003
        elif where == "audit_block":
            r["seeds"]["audit_seed_block"] = [7001, 7004]
            if r["terminal"]:
                r["terminal"]["audit_seeds"] = [7001, 7002]
    if where == "eps":
        rows[0]["policy"].update(eps=0.1, eps_seed=7002, action_prob=0.95)
    _only(S.check_campaign(rows, registry=_Reg()), "seed")
    assert S.check_campaign(valid_campaign(), registry=_Reg()) == []


def _errs(mut):
    rows = valid_campaign()
    mut(rows)
    return checks_of(S.check_campaign(rows))


def test_outcome_rules():
    assert _errs(lambda r: r[2]["outcome"].update(delta_hat=0.1)) == ["outcome"]           # skip with a result
    assert "outcome" in _errs(lambda r: r[0]["outcome"].update(delta_hat=None))           # execute, no result
    assert "outcome" in _errs(lambda r: r[2]["outcome"].update(runs_consumed=1))          # skip consuming a run
    assert _errs(lambda r: r[4]["outcome"].update(immediate_measured=0.01)) == ["outcome"]  # on a discard


def test_epoch_sequence_rules():
    rows = valid_campaign()
    rows[1]["state"]["candidate_delta_hat"] = 0.05     # E2 state does not carry the execute's result
    _only(S.check_campaign(rows), "epoch_sequence")
    rows = valid_campaign()
    rows[3]["identity"]["epoch"] = "reaudit"            # reaudit in place of the execute: E2 without execute
    rows[3]["action"]["action"] = "reaudit"
    assert "epoch_sequence" in checks_of(S.check_campaign(rows))


def test_constant_within_trajectory():
    rows = valid_campaign()
    rows[3]["env"]["llm_cap"] = 7
    rows[3]["state"]["calls_left"] = 5
    assert "constant" in checks_of(S.check_campaign(rows))
    rows = fork_continuation()
    for r in rows:
        r["fork"]["replicate"] = 0
    _only(S.check_campaign(rows), "constant")
    rows = fork_continuation()
    for r in rows:
        r["identity"]["fork_id"] = None
    _only(S.check_campaign(rows), "constant")


def test_counters():
    rows = valid_campaign()
    rows[2]["state"]["keeps_so_far"] = 0
    _only(S.check_campaign(rows), "counters")
    rows = valid_campaign()
    for r in rows[3:]:
        r["state"]["prior_skips"] = 0
    _only(S.check_campaign(rows), "counters")


def test_flags():
    for mut in (lambda r: r["state"].update(eligible=False),                              # neither flag
                lambda r: r["state"].update(duplicate=True),                              # duplicate not forced
                lambda r: r["action"].update(rule="rule_noop")):                         # rule_* on a policy row
        r = valid_campaign()[0]
        mut(r)
        assert S.validate(r)


# ---------------------------------------------------------------- robustness and row-level validation

@pytest.mark.parametrize("bad", [None, "row", 3, ["x"]])
def test_non_object_rows_do_not_raise(bad):
    assert S.validate(bad) == ["row: expected an object"]
    assert checks_of(S.check_campaign([bad])) == ["schema"]


def test_negative_and_wrong_types():
    r = valid_campaign()[0]
    r["identity"]["step_index"] = -1
    r["state"]["runs_used"] = 1.5
    r["provenance"]["label"] = "RESULT"
    errs = S.validate(r)
    assert any("step_index: must be >= 0" in e for e in errs)
    assert any("runs_used: expected int" in e for e in errs)
    assert any("label" in e for e in errs)


def test_nan_and_missing_and_unknown():
    r = valid_campaign()[0]
    r["state"]["sigma_node"] = math.nan
    del r["seeds"]["instance_seed"]
    r["outcome"]["extra"] = 1
    errs = S.validate(r)
    assert any("not finite" in e for e in errs)
    assert any("instance_seed: missing" in e for e in errs)
    assert any("extra: unknown" in e for e in errs)


def test_eps_needs_seed_and_terminal_rules():
    r = valid_campaign()[0]
    r["policy"].update(eps=0.1, action_prob=0.95)
    assert any("eps_seed" in e for e in S.validate(r))
    r = valid_campaign()[-1]
    r["terminal"]["y_terminal"] = 0.6
    assert any("mean over audit seeds" in e for e in S.validate(r))
    r = valid_campaign()[-1]
    r["terminal"]["audit_seeds"] = [10_000_000, 9_000_000]
    assert any("audit block" in e for e in S.validate(r))


# ---------------------------------------------------------------- JSON schema

def test_json_schema_file_is_current():
    assert SCHEMA_FILE.exists(), "run: python -m paperc.schema_export"
    assert json.loads(SCHEMA_FILE.read_text()) == S.to_json_schema()


def test_json_schema_validates():
    jsonschema = pytest.importorskip("jsonschema")
    js = S.to_json_schema()
    jsonschema.Draft202012Validator.check_schema(js)
    v = jsonschema.Draft202012Validator(js)
    for r in valid_campaign() + fork_continuation():
        assert list(v.iter_errors(r)) == []
    for mut in (lambda r: r["state"].pop("incumbent_hash"), lambda r: r.update(schema="other"),
                lambda r: r["state"].update(runs_used=-1), lambda r: r["policy"].update(action_prob=0),
                lambda r: r["seeds"].update(audit_seed_block=[1, 2, 3])):
        bad = valid_campaign()[0]
        mut(bad)
        assert list(v.iter_errors(bad))
    assert js["$id"].startswith("urn:")


# ---------------------------------------------------------------- review round 2 (minor findings 20-27)

def test_r2_failed_invalid_is_an_outcome_and_must_be_discarded():
    rows = valid_campaign()
    rows[3]["outcome"].update(delta_hat=None, failure_category="runtime_error")
    rows[4]["state"].update(candidate_delta_hat=None, candidate_invalid=True)
    assert S.check_campaign(rows) == []                 # a discarded invalid candidate is valid
    rows[0]["outcome"].update(delta_hat=None, failure_category="syntax_error")
    rows[1]["state"].update(candidate_delta_hat=None, candidate_invalid=True)
    assert "outcome" in checks_of(S.check_campaign(rows))      # ... and cannot be kept
    r = valid_campaign()[0]
    r["outcome"]["failure_category"] = "degraded_metric"       # a worse metric is not a failure
    assert S.validate(r)


def _with_verify(div=False):
    rows = valid_campaign()[:2]
    ver = _row(1, epoch="verify", action="verify",
               st={"candidate_hash": "c0", "runs_used": 1, "calls_used": 1, "slots_left": 5,
                   "candidate_delta_hat": 0.02, "candidate_obs": 1},
               out={"runs_consumed": 1, **({"divergent": True} if div else {"delta_hat": 0.01})})
    rows[1]["identity"]["step_index"] = 2
    rows[1]["state"].update(runs_used=2, runs_left=2, candidate_obs=2, candidate_delta_hat=None if div else 0.015,
                            candidate_divergent=div)
    rows[1]["episode_end"] = {"kind": "truncated", "reason": "host"}
    return [rows[0], ver, rows[1]]


def test_r2_verify_updates_the_latest_measurement():
    rows = _with_verify()
    assert S.check_campaign(rows) == []
    rows = _with_verify(div=True)
    assert "epoch_sequence" in checks_of(S.check_campaign(rows))   # divergent verify, then keep: not allowed
    rows[2]["action"]["action"] = "discard"
    rows[2]["outcome"].update(kept=False, next_incumbent_hash="i0")
    assert S.check_campaign(rows) == []
    rows = _with_verify()
    rows[2]["state"]["candidate_obs"] = 1
    _only(S.check_campaign(rows), "epoch_sequence")


def test_r2_w_termination_respects_run_cost():
    rows = valid_campaign()
    for r in rows:
        r["env"]["constants"]["run_cost"] = 3
    rows[3]["outcome"]["runs_consumed"] = 2              # one run left, an execute costs 3: W is effectively spent
    for r in rows[4:]:
        r["state"]["runs_used"] = 3
        r["state"]["runs_left"] = 1
    assert S.check_campaign(rows) == []


def test_r2_final_selection_must_be_seen():
    rows = valid_campaign()
    rows[-1]["episode_end"] = rows[-1]["terminal"] = None
    fin = _row(5, epoch="final", action="select",
               st={"candidate_hash": None, "incumbent_hash": "c0", "incumbent_recorded": 0.52, "runs_used": 4,
                   "calls_used": 3, "slots_left": 3, "keeps_so_far": 1, "prior_skips": 1},
               out={"next_incumbent_hash": "zz"}, end={"kind": "terminated", "reason": "W"},
               terminal=copy.deepcopy(TERM))
    fin["action"]["selected"] = "zz"
    _only(S.check_campaign(rows + [fin]), "epoch_sequence")


def test_r2_incumbent_record_changes_only_on_keep():
    rows = valid_campaign()
    rows[4]["state"]["incumbent_recorded"] = 0.6
    _only(S.check_campaign(rows), "counters")


def test_r2_root_counters_start_at_zero():
    rows = valid_campaign()
    for r in rows:
        r["state"]["prior_skips"] += 1
    _only(S.check_campaign(rows), "counters")


def test_r2_behaviour_action_and_replicate():
    rows = valid_campaign() + fork_continuation()
    rows[5]["policy"]["behaviour_action"] = "keep"
    _only(S.check_campaign(rows), "propensity")
    rows = fork_continuation()
    for r in rows:
        r["fork"]["replicate"] = 2
    _only(S.check_campaign(rows), "constant")


def test_r2_audit_range_inside():
    from paperc.seeds import Registry
    reg = Registry.load()
    rows = valid_campaign()
    for r in rows:
        r["seeds"]["audit_seed_block"] = [6000, 8000]      # both ends outside Paper B blocks? 6000 is in e1b audits
        if r["terminal"]:
            r["terminal"]["audit_seeds"] = [6500, 6501]
    assert "seed" in checks_of(S.check_campaign(rows, registry=reg))
    rows = valid_campaign()
    for r in rows:
        r["seeds"]["audit_seed_block"] = [6001, 8000]      # ends at 6001 (free) and 8000 (free), c3 audits inside
        if r["terminal"]:
            r["terminal"]["audit_seeds"] = [6500, 6501]
    _only(S.check_campaign(rows, registry=reg), "seed")


# finding 26: rules without a test in round 2

def test_r2_runs_consumed_beyond_left():
    rows = valid_campaign()
    rows[3]["outcome"]["runs_consumed"] = 4
    assert "budget" in checks_of(S.check_campaign(rows))


def test_r2_llm_cap_ledger():
    rows = valid_campaign()
    rows[-1]["episode_end"]["reason"] = "llm_cap"
    _only(S.check_campaign(rows), "terminal")


def test_r2_slots_left_counter():
    rows = valid_campaign()
    for r in rows[3:]:
        r["state"]["slots_left"] += 1
    _only(S.check_campaign(rows), "counters")


def test_r2_final_only_last():
    rows = valid_campaign()
    mid = copy.deepcopy(rows[2])
    rows[2]["identity"]["epoch"] = "final"
    rows[2]["action"].update(action="select", selected="c0", rule="policy")
    rows[2]["state"].update(rule_forced=False, eligible=True, duplicate=False)
    rows[2]["outcome"]["calls_consumed"] = 0
    assert "epoch_sequence" in checks_of(S.check_campaign(rows))
    del mid


def test_r2_executed_without_e2_at_terminated_end():
    rows = valid_campaign()[:4]
    rows[-1]["episode_end"] = {"kind": "terminated", "reason": "W"}
    rows[-1]["terminal"] = copy.deepcopy(TERM)
    assert "epoch_sequence" in checks_of(S.check_campaign(rows))


def test_r2_candidate_hash_required_and_rule_prob():
    r = valid_campaign()[0]
    r["state"]["candidate_hash"] = None
    assert any("candidate_hash" in e for e in S.validate(r))
    r = valid_campaign()[2]
    r["policy"]["action_prob"] = 0.5
    assert any("1.0 on rule-forced" in e for e in S.validate(r))


def test_p3_final_candidates():
    """B17 (runbook P3): optional State.candidates on final rows; the selection must be one of them."""
    rows = valid_campaign()
    rows[-1]["episode_end"] = rows[-1]["terminal"] = None
    fin = _row(5, epoch="final", action="select",
               st={"candidate_hash": None, "incumbent_hash": "c0", "incumbent_recorded": 0.52, "runs_used": 4,
                   "calls_used": 3, "slots_left": 3, "keeps_so_far": 1, "prior_skips": 1,
                   "candidates": [{"hash": "c0", "recorded": 0.52, "obs": 1}]},
               out={"next_incumbent_hash": "c0"}, end={"kind": "terminated", "reason": "W"},
               terminal=copy.deepcopy(TERM))
    fin["action"]["selected"] = "c0"
    assert S.check_campaign(rows + [fin]) == []
    bad = copy.deepcopy(fin)
    bad["state"]["candidates"] = [{"hash": "c2", "recorded": 0.51, "obs": 1}]
    assert any("not among state.candidates" in m for m in S.validate(bad))
    early = copy.deepcopy(rows[0])
    early["state"]["candidates"] = [{"hash": "c0", "recorded": 0.5, "obs": 1}]
    assert any("only on final rows" in m for m in S.validate(early))
    old = copy.deepcopy(rows[0])
    old["state"].pop("candidates", None)          # rows written before the field remain valid
    assert S.validate(old) == []
