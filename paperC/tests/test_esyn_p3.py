"""Runbook P3: E-SYN worlds, simulator, exact DP and certified oracle (steps 3-6)."""
import dataclasses
import json
import math
from pathlib import Path

import numpy as np
import pytest

from paperc import schema as S
from paperc import seeds as SD
from paperc.esyn import dp, extra as X, families as F, policies as P, sim, worlds as WD
from paperc.esyn.oracle import OracleToleranceError, certify

TABLE = Path(__file__).resolve().parents[1] / "esyn" / "oracle_table_v1.json"
REG = SD.Registry.load()


# ---------------------------------------------------------------- worlds declare their channel as data

def test_worlds_declare_channel_and_sign():
    assert {"strict_null", "budget", "interaction", "shared_error", "eval_allocation"} <= set(X.WORLDS)
    for w in X.WORLDS.values():
        assert w.channel in X.CHANNELS and w.gain_sign in (0, 1)
        assert (w.channel == "none") == (w.gain_sign == 0)
        json.dumps(w.to_dict())


def test_world_validation():
    base = WD.make_world("N0")
    with pytest.raises(ValueError):
        X.ESynWorld(name="x", channel="none", gain_sign=1, base=base)
    with pytest.raises(ValueError):
        X.ESynWorld(name="x", channel="budget", gain_sign=1, base=base, epochs=("E1", "E2", "verify"))
    with pytest.raises(ValueError):
        X.ESynWorld(name="x", channel="interaction", gain_sign=1, base=WD.make_world("N0", n_keys=2),
                    interaction=((0.0, 1.0), (0.0, 0.0)))
    with pytest.raises(ValueError):
        X.ESynWorld(name="x", channel="budget", gain_sign=1, base=base, sizes=(1.0,), size_probs=(0.5,))


# ---------------------------------------------------------------- records (P1) and replay

POLICIES = [P.Static(0.0, 0.0), P.Static(0.001, -0.001), P.EvalAlloc(0.0, -0.001, 1.0, 2, 2, "best"),
            P.InteractionAware(0.0, 0.0, 0.5), P.Dynamic(0.0005, -0.001, 0.1, 0.004, 0.004, 0.002, 0.01)]


@pytest.mark.parametrize("name", sorted(X.WORLDS))
def test_campaigns_write_valid_records(name):
    w = X.WORLDS[name]
    epochs = set()
    for pol in POLICIES:
        for i in range(4):
            r = sim.run_campaign(w, pol, i, record=True)
            f = sim.run_campaign(w, pol, i)
            assert r.Y == f.Y and r.decisions == f.decisions        # fast path == recorded path
            v = S.check_campaign(r.rows, registry=REG, behaviour=sim.behaviour_for(pol))
            assert v == [], v[:3]
            assert r.rows[-1]["episode_end"]["reason"] == r.end_reason
            epochs |= {row["identity"]["epoch"] for row in r.rows}
    assert epochs == set(w.epochs)                                  # every offered epoch occurs


def test_replay_detects_a_different_policy():
    w = X.WORLDS["budget"]
    r = sim.run_campaign(w, P.Static(0.0, 0.0), 1, record=True)
    v = S.check_campaign(r.rows, behaviour=sim.behaviour_for(P.Static(0.003, 0.0)))
    assert v and {x.check for x in v} == {"propensity"}


def test_terminal_and_seeds():
    w = X.WORLDS["eval_allocation"]
    r = sim.run_campaign(w, P.EvalAlloc(0.0, 0.0, 1.0, 2, 2, "best"), 7, record=True)
    last = r.rows[-1]
    assert last["identity"]["epoch"] == "final" and last["state"]["candidates"]
    tm = last["terminal"]
    assert len(tm["audit_seeds"]) == w.n_audit and abs(np.mean(tm["y_terminal_per_seed"]) - tm["y_terminal"]) < 1e-12
    assert last["seeds"]["instance_seed"] == sim.INSTANCE_BASE + 7
    assert r.rows[0]["identity"]["campaign_id"].startswith("pc-")


def test_mechanisms():
    # interaction: the complement of a kept key adds M to a later partner's increment
    w = X.WORLDS["interaction"]
    assert w.interaction[0][1] > 0 and w.interaction[0][2] == 0
    # config worlds: re-audit changes the incumbent record only through reaudit rows
    w = X.WORLDS["shared_error"]
    r = sim.run_campaign(w, P.EvalAlloc(0.0, 0.0, 0.0, 1, 3, "incumbent"), 3, record=True)
    obs = [row["state"]["incumbent_obs"] for row in r.rows]
    assert max(obs) == 3
    # trial 1 is executed and kept by rule
    assert [r.rows[i]["action"]["rule"] for i in (0, 1)] == ["rule_first_trial"] * 2


# ---------------------------------------------------------------- exact DP

@pytest.mark.parametrize("name", ["budget", "strict_null"])
def test_dp_matches_simulation(name):
    w = X.WORLDS[name]
    sol = dp.solve(w)
    n = 8000
    ys = sim.campaign_values(w, P.Threshold(sol.table), range(sim.EVAL_BASE, sim.EVAL_BASE + n))
    assert abs(ys.mean() - sol.value) < 4 * ys.std() / math.sqrt(n)
    for g in (0.0, dp.size_law(w).v[1]):
        ys = sim.campaign_values(w, P.Static(g, 0.0), range(sim.EVAL_BASE, sim.EVAL_BASE + n))
        assert abs(ys.mean() - dp.static_value(w, g)) < 4 * ys.std() / math.sqrt(n)


def test_dp_dominates_statics_and_null_gain_is_zero():
    for name in ("budget", "strict_null"):
        w = X.WORLDS[name]
        v = dp.solve(w).value
        stat = [dp.static_value(w, g) for g in np.linspace(0, 0.004, 41)] + \
               [dp.static_value(w, g) for g in dp.size_law(w).v]
        assert v >= max(stat) - 1e-15
        if name == "strict_null":
            assert abs(v - max(stat)) < 1e-15          # non-binding W: the DP is the static rule g = 0
        else:
            assert v - max(stat) > 0.001               # binding W: a planted budget gain


def test_dp_not_applicable_elsewhere():
    for name in ("interaction", "shared_error", "eval_allocation", "information", "keep_feedback"):
        assert dp.applicable(X.WORLDS[name])


# ---------------------------------------------------------------- certified oracle (committed table)

@pytest.fixture(scope="module")
def table():
    return json.loads(TABLE.read_text())


UNCERTIFIED = {"information": "positive, but 5 % precision is out of reach: P1's size-16 follow-ups make campaign "
                              "values so noisy that n_max = 200,000 gives a half-width of about 25 % of the gain"}


def test_table_covers_every_world(table):
    assert set(table["worlds"]) == set(X.WORLDS)
    for name, rec in table["worlds"].items():
        assert rec["world"] == json.loads(json.dumps(X.WORLDS[name].to_dict())), f"{name}: table is stale"


def test_null_gain_is_zero_within_tolerance(table):
    o = table["worlds"]["strict_null"]["oracle"]
    assert o["pass"] and o["planted_source"] == "floor"
    assert abs(o["gain"]) <= o["tolerance"] + o["half_width"]
    assert o["gain"] + o["half_width"] <= o["tolerance"]           # no member beats the static rule
    sel = o["selection"]                                            # ... including those that decide differently
    assert sel["n_distinct"] > 0
    assert sel["best_distinct_gain"] <= o["tolerance"] + 2 * sel["best_distinct_se"]


CHANNEL_WORLDS = ["budget", "interaction", "shared_error", "eval_allocation", "keep_feedback", "information"]


@pytest.mark.parametrize("name", CHANNEL_WORLDS)
def test_channel_gain_is_positive(table, name):
    o = table["worlds"][name]["oracle"]
    assert X.WORLDS[name].gain_sign == 1
    assert o["gain"] - o["half_width"] > 0                          # the sign is as declared


@pytest.mark.parametrize("name", CHANNEL_WORLDS)
def test_channel_gain_is_certified(table, name):
    if name in UNCERTIFIED:
        pytest.xfail(UNCERTIFIED[name])
    o = table["worlds"][name]["oracle"]
    assert o["pass"] and o["half_width"] <= o["tolerance"]


def test_dp_and_oracle_agree_on_budget(table):
    rec = table["worlds"]["budget"]
    o = rec["oracle"]
    exact = rec["dp_gain_over_selected_static"]
    assert exact is not None and abs(o["gain"] - exact) <= o["half_width"] + o["tolerance"]
    assert abs(o["evaluation"]["member_value"] - rec["dp_value"]) < 4 * o["half_width"] + o["tolerance"]


def test_certify_fails_when_n_max_is_too_small():
    w = X.WORLDS["budget"]
    sol = dp.solve(w)
    with pytest.raises(OracleToleranceError):
        certify(w, [P.Static(0.001, 0.0)], [P.Threshold(sol.table)], delta_Y=0.002, n_select=50, n_pilot=50,
                n_max=60)
