"""Runbook P1: the spt_transition/v1 schema and its mechanical checks (plan §4.1-§4.2)."""
import copy
import json
from pathlib import Path

import pytest

from paperc import schema as S

SCHEMA_FILE = Path(__file__).resolve().parents[1] / "schemas" / "spt_transition_v1.json"


# ---------------------------------------------------------------- valid synthetic campaigns (test-only generator)

def _row(step, *, epoch, action, runs_used, calls_used, inc, next_inc, W=4, cap=6, branch=(), fork=None,
         campaign="c1", rule_forced=False, runs_consumed=0, calls_consumed=1, kept=None, delta=None,
         end=None, terminal=None, seed=50001):
    return {
        "schema": S.SCHEMA,
        "identity": {"node": "syn_null", "suite": "E-SYN", "tier": "E-SYN", "instance_id": f"syn_null:{seed}",
                     "campaign_id": campaign, "step_index": step, "epoch": epoch, "branch_path": list(branch),
                     "root_id": campaign, "fork_id": None if not branch else "f1"},
        "env": {"proposer_model": "scripted", "proposer_gguf_sha256": None, "thinking": "n/a", "W": W,
                "llm_cap": cap, "memory_mode": "none", "skip_display": "one_line", "edit_schema": "synthetic",
                "run_budget": "synthetic", "constants": {"g": 0.1}},
        "policy": {"policy": "static:0.1,0", "policy_sha": None, "action_prob": 1.0},
        "seeds": {"instance_seed": seed, "manager_rep": 0, "worker_seed": None, "audit_seed_block": [1000000, 1000004]},
        "state": {"proposal_hash": f"p{step}", "proposal_ref": None, "duplicate": rule_forced, "noop": False,
                  "eligible": not rule_forced, "rule_forced": rule_forced, "incumbent_hash": inc,
                  "runs_used": runs_used, "runs_left": W - runs_used, "calls_used": calls_used,
                  "calls_left": cap - calls_used, "slots_left": cap - calls_used, "keeps_so_far": 0,
                  "skips_so_far": 0, "sigma_node": 0.01, "noise_source": "C1", "history_ref": None,
                  "forecasts": {"a3": {"pi": 0.0, "mu": 0.0, "tau": 0.02, "sigma": 0.01, "v_star": 0.008,
                                       "m_hat": None}}},
        "action": {"action": action, "forced": False,
                   "rule": "rule_duplicate" if rule_forced else "policy"},
        "outcome": {"runs_consumed": runs_consumed, "calls_consumed": calls_consumed,
                    "next_incumbent_hash": next_inc, "delta_hat": delta, "kept": kept},
        "provenance": {"host": "cloud", "gpu": None, "harness_commit": None, "paper_commit": None,
                       "llama_build": None, "cache_prompt": None, "phase": "P1", "label": "FIXTURE"},
        "fork": fork,
        "episode_end": end,
        "terminal": terminal,
    }


def valid_campaign(campaign="c1", seed=50001):
    """Root trajectory: E1 execute -> E2 keep -> E1 skip (rule duplicate) -> E1 execute -> E2 discard (end at W)."""
    term = {"y_terminal": 0.52, "y_terminal_per_seed": [0.51, 0.53], "audit_seeds": [1000000, 1000001],
            "y_start": 0.50}
    k = dict(campaign=campaign, seed=seed)
    return [
        _row(0, epoch="E1", action="execute", runs_used=0, calls_used=0, inc="i0", next_inc="i0",
             runs_consumed=1, calls_consumed=1, delta=0.02, **k),
        _row(1, epoch="E2", action="keep", runs_used=1, calls_used=1, inc="i0", next_inc="i1",
             calls_consumed=0, kept=True, **k),
        _row(2, epoch="E1", action="skip", runs_used=1, calls_used=1, inc="i1", next_inc="i1",
             rule_forced=True, **k),
        _row(3, epoch="E1", action="execute", runs_used=1, calls_used=2, inc="i1", next_inc="i1",
             runs_consumed=3, calls_consumed=1, delta=-0.01, **k),
        _row(4, epoch="E2", action="discard", runs_used=4, calls_used=3, inc="i1", next_inc="i1",
             calls_consumed=0, kept=False, end={"kind": "terminated", "reason": "W"}, terminal=term, **k),
    ]


def fork_continuation():
    fork = {"selection_rule": "both", "q_uniform": 0.2, "q_oversample": 0.5, "near_threshold": True,
            "in_uniform": True, "in_oversample": True, "p_select": 1 - 0.8 * 0.5, "channel_arms": False,
            "replicate": 1}
    rows = [
        _row(3, epoch="E1", action="skip", runs_used=1, calls_used=2, inc="i1", next_inc="i1",
             branch=("f1:skip:r1",), fork=fork),
        _row(4, epoch="E1", action="execute", runs_used=1, calls_used=3, inc="i1", next_inc="i1",
             branch=("f1:skip:r1",), fork=fork, runs_consumed=1, delta=0.0,
             end={"kind": "truncated", "reason": "infrastructure"}),
    ]
    rows[0]["action"].update(forced=True, rule="fork_arm")
    return rows


def checks_of(viol):
    return sorted({v.check for v in viol})


# ---------------------------------------------------------------- valid data passes

def test_valid_campaign_has_no_violation():
    rows = valid_campaign() + fork_continuation()
    for r in rows:
        assert S.validate(r) == []
    assert S.check_campaign(rows) == []


def test_round_trip():
    for r in valid_campaign():
        t = S.from_dict(r)
        assert S.to_dict(t) == json.loads(json.dumps(S.to_dict(t)))
        assert S.from_dict(S.to_dict(t)) == t


# ---------------------------------------------------------------- each check has one corruption only it catches

def _only(viol, check):
    assert checks_of(viol) == [check], viol


def test_budget_runs():
    rows = valid_campaign()
    rows[3]["state"]["runs_used"] = 2       # does not follow from row 2, and breaks used + left == W
    _only(S.check_campaign(rows), "budget")


def test_budget_calls_conservation_only():
    rows = valid_campaign()
    rows[1]["state"]["calls_left"] = 4      # used + left != cap; the sequence is unchanged
    _only(S.check_campaign(rows), "budget")


def test_contiguous():
    rows = valid_campaign()
    del rows[2]                             # gap; repair the counters and hashes so only contiguity fails
    rows[2]["state"]["calls_used"] = 1
    rows[2]["state"]["calls_left"] = 5
    rows[2]["state"]["slots_left"] = 5
    rows[2]["outcome"]["calls_consumed"] = 2
    _only(S.check_campaign(rows), "contiguous")


def test_contiguous_root_starts_at_zero():
    rows = valid_campaign()
    for r in rows:
        r["identity"]["step_index"] += 1
    _only(S.check_campaign(rows), "contiguous")


def test_terminal_missing():
    rows = valid_campaign()
    rows[-1]["terminal"] = None
    _only(S.check_campaign(rows), "terminal")


def test_terminal_on_truncated():
    rows = fork_continuation()
    rows[-1]["terminal"] = copy.deepcopy(valid_campaign()[-1]["terminal"])
    _only(S.check_campaign(rows), "terminal")


def test_episode_end_missing():
    rows = fork_continuation()
    rows[-1]["episode_end"] = None
    _only(S.check_campaign(rows), "terminal")


def test_next_state():
    rows = valid_campaign()
    rows[2]["state"]["incumbent_hash"] = "i0"
    rows[1]["outcome"]["next_incumbent_hash"] = "i1"   # unchanged; row 2 now disagrees with it
    _only(S.check_campaign(rows), "next_state")


def test_propensity():
    rows = valid_campaign()

    def behaviour(t):
        if t.identity.step_index == 3:
            return "skip", 1.0
        return t.action.action, t.policy.action_prob

    _only(S.check_campaign(rows, behaviour=behaviour), "propensity")


def test_propensity_ignores_rule_forced_rows():
    rows = valid_campaign()
    calls = []

    def behaviour(t):
        calls.append(t.identity.step_index)
        return t.action.action, t.policy.action_prob

    assert S.check_campaign(rows, behaviour=behaviour) == []
    assert 2 not in calls


def test_design_weight_p_select():
    rows = fork_continuation()
    for r in rows:
        r["fork"]["p_select"] = 0.5
    _only(S.check_campaign(rows), "design_weight")


def test_design_weight_flags():
    rows = fork_continuation()
    for r in rows:
        r["fork"].update(selection_rule="uniform", near_threshold=False, in_oversample=False, p_select=0.2)
        r["fork"]["in_oversample"] = True       # flag says oversample although not near and rule is uniform
    _only(S.check_campaign(rows), "design_weight")


@pytest.mark.parametrize("name", ["y_terminal", "audit_value", "future_delta", "immediate_measured", "next_keep"])
def test_no_future(name):
    rows = valid_campaign()
    rows[1]["state"][name] = 0.5
    viol = S.check_campaign(rows)
    assert "no_future" in checks_of(viol)
    assert set(checks_of(viol)) <= {"no_future", "contiguous", "next_state", "budget"}  # row 1 is dropped


def test_no_future_static():
    assert S.state_field_violations(f.name for f in S.fields(S.State)) == []
    assert S.state_field_violations(["audit_seed_value", "y_true"]) == ["audit_seed_value", "y_true"]


class _Reg:
    def paper_b_block(self, node, seed):
        return "tracks_instances_30500_31000" if 30500 <= seed < 31000 else None


def test_seed_registry():
    rows = valid_campaign(seed=30510)
    _only(S.check_campaign(rows, registry=_Reg()), "seed")
    assert S.check_campaign(valid_campaign(), registry=_Reg()) == []


# ---------------------------------------------------------------- row-level validation

def test_divergent_row():
    r = valid_campaign()[0]
    r["outcome"].update(divergent=True)          # delta_hat 0.02 is still set
    assert any("divergent" in e for e in S.validate(r))
    r["outcome"]["delta_hat"] = None
    assert S.validate(r) == []


def test_action_epoch_mismatch():
    r = valid_campaign()[0]
    r["action"]["action"] = "keep"
    assert any("not allowed in epoch" in e for e in S.validate(r))


def test_rule_forced_not_eligible():
    r = valid_campaign()[2]
    r["state"]["eligible"] = True
    assert any("rule-forced" in e for e in S.validate(r))


def test_types_and_vocabulary():
    r = valid_campaign()[0]
    r["state"]["runs_used"] = 1.5
    r["provenance"]["label"] = "RESULT"
    errs = S.validate(r)
    assert any("runs_used: expected int" in e for e in errs)
    assert any("label" in e for e in errs)


def test_missing_and_unknown_fields():
    r = valid_campaign()[0]
    del r["seeds"]["instance_seed"]
    r["outcome"]["extra"] = 1
    errs = S.validate(r)
    assert any("instance_seed: missing" in e for e in errs)
    assert any("extra: unknown" in e for e in errs)


def test_eps_needs_seed():
    r = valid_campaign()[0]
    r["policy"].update(eps=0.1, action_prob=0.95)
    assert any("eps_seed" in e for e in S.validate(r))


def test_terminal_mean_and_audit_block():
    r = valid_campaign()[-1]
    r["terminal"]["y_terminal"] = 0.6
    assert any("mean over audit seeds" in e for e in S.validate(r))
    r = valid_campaign()[-1]
    r["terminal"]["audit_seeds"] = [1000000, 900000]
    assert any("audit block" in e for e in S.validate(r))


def test_final_epoch_needs_selected():
    r = valid_campaign()[-1]
    r["identity"]["epoch"] = "final"
    r["action"]["action"] = "select"
    r["outcome"]["kept"] = None
    assert any("selected" in e for e in S.validate(r))
    r["action"]["selected"] = "i1"
    assert S.validate(r) == []


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
    bad = valid_campaign()[0]
    del bad["state"]["incumbent_hash"]
    assert list(v.iter_errors(bad))
