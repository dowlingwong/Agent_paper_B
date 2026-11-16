"""Runbook P4: policy interface, non-RL ladder, B18 comparators, runner and ladder table."""
import json
import math
from pathlib import Path

import numpy as np
import pytest

from paperc import policies as L
from paperc import runner as R
from paperc import schema as S
from paperc import seeds as SD
from paperc.esyn import dp, extra as X, policies as EP, sim

REG = SD.Registry.load()
LADDER = Path(__file__).resolve().parents[1] / "esyn" / "ladder_table_v1.json"


# ---------------------------------------------------------------- interface and records

ALL = [L.N0(), L.TrackSDynamic(0.001, 0.002, 0.1, -0.001, 0.002), L.RandomExec(0.6), L.SPRT(0.0, -0.001, 0.003),
       L.Race(0.0, -0.001, 1.0), L.KGVerify(0.0, -0.001, 0.0001), L.BudgetMargin(0.0, -0.001, 0.002),
       L.LearnedHead((0.1, 1.0, 0.0), (0.0, 1.0, 1.0), 0.0, 0.0066)]


def test_interface():
    for p in ALL:
        assert isinstance(p.name, str) and p.version == L.VERSION and callable(p.act)


@pytest.mark.parametrize("name", sorted(X.WORLDS))
def test_every_rung_writes_valid_records(name):
    w = X.WORLDS[name]
    for p in ALL:
        for i in range(3):
            r = sim.run_campaign(w, p, i, record=True)
            assert r.Y == sim.run_campaign(w, p, i).Y
            v = S.check_campaign(r.rows, registry=REG, behaviour=sim.behaviour_for(p))
            assert v == [], (p.name, v[:2])


def test_stochastic_rows_log_probabilities_and_replay():
    w = X.WORLDS["budget"]
    p = L.RandomExec(0.3)
    r = sim.run_campaign(w, p, 5, record=True)
    e1 = [row for row in r.rows if row["identity"]["epoch"] == "E1" and not row["state"]["rule_forced"]]
    assert e1 and all(row["policy"]["eps_seed"] == sim.EPS_KEY for row in e1)
    assert {row["policy"]["action_prob"] for row in e1} <= {0.3, 0.7}
    # replaying a different q is caught
    v = S.check_campaign(r.rows, behaviour=sim.behaviour_for(L.RandomExec(0.31)))
    assert v and {x.check for x in v} == {"propensity"}


def test_knowledge_gradient():
    assert L.knowledge_gradient(0.0, 0.0, 1e-5, 0.005, 0.005) == 0.0          # no variance reduction, no value
    kg_near = L.knowledge_gradient(0.0, 0.0, 2e-5, 0.0066, 0.0047)
    kg_far = L.knowledge_gradient(0.01, 0.0, 2e-5, 0.0066, 0.0047)
    assert kg_near > kg_far > 0                                                # value is largest at the margin


def test_track_s_gap_definition():
    obs = {"epoch": "E1", "runs_left": 6, "W": 10, "slots_left": 20, "llm_cap": 40}
    assert L.TrackSDynamic.gap(obs) == pytest.approx(0.6 - 0.5)
    assert L.TrackSDynamic.gap({**obs, "epoch": "E2", "slots_left": 19}) == pytest.approx(0.1)


# ---------------------------------------------------------------- runbook tests

def test_n2_is_the_dp_policy_in_the_null():
    w = X.WORLDS["strict_null"]
    t = L.Tuner(w)
    n2, _ = L.tune_static(t, h_fixed=0.0)
    dpol = EP.Threshold(dp.solve(w).table)
    for i in range(L.TEST_BASE, L.TEST_BASE + 300):
        a, b = sim.run_campaign(w, n2, i), sim.run_campaign(w, dpol, i)
        assert a.decisions == b.decisions and a.Y == b.Y


def test_n4_matches_the_exact_dp_in_the_budget_world():
    w = X.WORLDS["budget"]
    dev = range(L.DEV_BASE, L.DEV_BASE + L.N_DEV)
    n4 = L.fit_n4(w, L.dev_trace(w, dev), dev)
    exact = EP.Threshold(dp.solve(w).table)
    test = range(L.TEST_BASE, L.TEST_BASE + 5000)
    d = sim.campaign_values(w, n4, test) - sim.campaign_values(w, exact, test)
    gain = dp.solve(w).value - max(dp.static_value(w, g) for g in dp.size_law(w).v)   # exact DP gain over static
    hw = 1.96 * d.std(ddof=1) / math.sqrt(len(d))
    assert abs(d.mean()) <= hw + 0.05 * gain             # N4 is within 5 % of the DP gain (plus sampling error)


def test_tuning_never_touches_test_seeds():
    w = X.WORLDS["budget"]
    t = L.Tuner(w)
    L.tune_static(t)
    assert t.seen_instances and max(t.seen_instances) <= L.DEV_BASE + L.N_DEV < L.TEST_BASE
    assert len(t.cache) <= L.TUNE_BUDGET
    with pytest.raises(L.BudgetExceeded):
        tiny = L.Tuner(w, range(L.DEV_BASE, L.DEV_BASE + 10), budget=1)
        tiny.value(EP.Static(0.0, 0.0))
        tiny.value(EP.Static(0.001, 0.0))


# ---------------------------------------------------------------- ladder table (committed)

@pytest.fixture(scope="module")
def ladder():
    return json.loads(LADDER.read_text())


def test_ladder_is_current(ladder):
    assert ladder["code_sha256"] == R.code_sha256(), "rebuild with python -m paperc.runner"
    assert set(ladder["worlds"]) == set(X.WORLDS)


@pytest.mark.parametrize("name", sorted(X.WORLDS))
def test_ladder_rows(ladder, name):
    rec = ladder["worlds"][name]
    rungs = rec["rungs"]
    assert {"N0", "N1", "N2", "N2b", "N3", "N4", "random", "oracle", "margin"} <= set(rungs)
    if X.WORLDS[name].comparison == "config":
        assert {"sprt", "race", "kg"} <= set(rungs)
    assert all(r["record_violations"] == 0 for r in rungs.values())
    for k, f in rec["tuning"].items():
        if isinstance(f, dict) and "instances" in f:
            assert f["instances"], f"{k}: tuning instances not recorded"
            assert f["candidates_evaluated"] <= f["budget"] and max(f["instances"]) < L.TEST_BASE
    assert rungs["N1"]["vs_N1"]["diff"] == 0.0


def test_ladder_null_and_budget_facts(ladder):
    null = ladder["worlds"]["strict_null"]["rungs"]
    for k, r in null.items():                       # nothing beats N1 by more than its interval in the null
        assert r["vs_N1"]["diff"] <= r["vs_N1"]["half_width"] + 1e-4, k
    bud = ladder["worlds"]["budget"]["rungs"]
    assert bud["N4"]["vs_N1"]["diff"] - bud["N4"]["vs_N1"]["half_width"] > 0     # the DP rung beats N1
