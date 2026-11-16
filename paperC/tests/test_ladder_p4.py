"""Runbook P4: policy interface, non-RL ladder, B18 comparators, runner and ladder table (revised after review 1)."""
import json
import math
from pathlib import Path

import numpy as np
import pytest

from paperc import policies as L
from paperc import runner as R
from paperc import schema as S
from paperc import seeds as SD
from paperc.esyn import dp, extra as X, policies as EP, sim, table as OT

REG = SD.Registry.load()
LADDER = Path(__file__).resolve().parents[1] / "esyn" / "ladder_table_v1.json"


# ---------------------------------------------------------------- interface and records

def _head():
    return L.LearnedHead((0.1, 1.0, 0.0, 0.2), (0.0, 1.0, 0.5), 0.0, 0.0066)


ALL = [L.N0(), L.TrackSDynamic(0.001, 0.002, 0.1, -0.001, 0.002, 0.0, 0.004, 0.0), L.RandomExec(0.6, -0.001),
       L.SPRT(0.0, -0.001, 0.003), L.Race(0.0, -0.001, 1.0), L.KGVerify(0.0, -0.001, 0.0001),
       L.BudgetMargin(0.0, -0.001, 0.002), _head(), L.RawKeep(0.0, -0.001),
       L.LawDP.fit([0.5, 0.5], [0.0005, 0.002], 0.55, -0.0005, 40, 8)]


def test_interface():
    for p in ALL:
        assert isinstance(p.name, str) and p.version == L.VERSION and callable(p.act)
        assert isinstance(p.stochastic, bool)


@pytest.mark.parametrize("name", sorted(X.WORLDS))
def test_every_row_writes_valid_records(name):
    w = X.WORLDS[name]
    for p in ALL:
        if isinstance(p, L.LawDP) and p.W != w.W:
            p = L.LawDP.fit(list(p.probs), list(p.values), p.p_rule, p.first_gain, w.llm_cap, w.W)
        for i in range(3):
            r = sim.run_campaign(w, p, i, record=True)
            assert r.Y == sim.run_campaign(w, p, i).Y
            v = S.check_campaign(r.rows, registry=REG, behaviour=sim.behaviour_for(p))
            assert v == [], (p.name, v[:2])
            if getattr(p, "sha", None):
                assert all(row["policy"]["policy_sha"] == p.sha for row in r.rows)


def test_no_rung_reads_the_raw_increment():
    """One belief for every arm (review P4 finding 3): only N0 and the RawKeep reference read delta_hat at E2."""
    base = {"epoch": "E2", "W": 40, "llm_cap": 40, "v_star": 0.001, "tau": 0.004, "sigma": 0.0066, "bonus": 0.0,
            "runs_left": 20, "slots_left": 20, "calls_left": 20, "incumbent_obs": 1, "candidate_obs": 1,
            "keeps_so_far": 1, "incumbent_hash": "c0", "key_seen": False, "candidates": [], "m_hat": 0.0005}
    for p in ALL:
        if isinstance(p, (L.N0, L.RawKeep)):
            continue
        a1 = p.act({**base, "candidate_delta_hat": -0.05})[0]
        a2 = p.act({**base, "candidate_delta_hat": +0.05})[0]
        assert a1 == a2, p.name


def test_stochastic_replay_uses_the_logged_key():
    w = X.WORLDS["budget"]
    p = L.RandomExec(0.3)
    r = sim.run_campaign(w, p, 5, record=True)
    e1 = [row for row in r.rows if row["identity"]["epoch"] == "E1" and not row["state"]["rule_forced"]]
    assert e1 and all(row["policy"]["eps_seed"] == sim.EPS_KEY for row in e1)
    assert {row["policy"]["action_prob"] for row in e1} <= {0.3, 0.7}
    assert S.check_campaign(r.rows, behaviour=sim.behaviour_for(p)) == []
    other = json.loads(json.dumps(r.rows))
    for row in other:
        row["policy"]["eps_seed"] = 60_999 if row["policy"]["eps_seed"] else None
    assert any(v.check == "propensity" for v in S.check_campaign(other, behaviour=sim.behaviour_for(p)))
    missing = json.loads(json.dumps(r.rows))
    for row in missing:
        row["policy"]["eps_seed"] = None
    msgs = [v.message for v in S.check_campaign(missing, behaviour=sim.behaviour_for(p))]
    assert any("randomised row" in m for m in msgs)


def test_knowledge_gradient_closed_form():
    rng = np.random.default_rng(1)
    for m, h, A, s, s2 in ((0.0, 0.0, 2e-5, 0.0066, 0.0047), (0.002, -0.001, 1e-5, 0.005, 0.004)):
        v1, v2 = A * s * s / (A + s * s), A * s2 * s2 / (A + s2 * s2)
        mprime = m + math.sqrt(v1 - v2) * rng.standard_normal(400_000)
        mc = float(np.mean(np.maximum(mprime, h)) - max(m, h))
        assert L.knowledge_gradient(m, h, A, s, s2) == pytest.approx(mc, rel=0.03, abs=2e-6)
    assert L.knowledge_gradient(0.0, 0.0, 1e-5, 0.005, 0.005) == 0.0


def test_budget_position():
    obs = {"epoch": "E1", "runs_left": 6, "W": 10, "slots_left": 20, "llm_cap": 40}
    assert L.budget_position(obs) == pytest.approx(0.6 - 0.5)
    assert L.budget_position({**obs, "epoch": "E2", "slots_left": 19}) == pytest.approx(0.1)


def test_seed_claims():
    vals = [c["value"] for c in REG.claims]
    assert len(vals) == len(set(vals))
    by = {c["name"]: c for c in REG.claims}
    assert by["esyn_decision_uniforms"]["value"] == sim.EPS_KEY
    rng = by["esyn_rng_root"]["index_ranges"]
    assert rng["p4_dev"][0] == L.DEV_BASE and rng["p4_test"][0] == L.TEST_BASE
    assert rng["p3_selection"][0] == sim.SELECT_BASE and rng["p3_decomposition"][0] == sim.DECOMP_BASE


# ---------------------------------------------------------------- runbook tests

def test_n2_is_the_dp_policy_in_the_null():
    w = X.WORLDS["strict_null"]
    n2 = L.tune_static(L.Tuner(L.DevCache(w)), h_fixed=0.0)
    dpol = EP.Threshold(dp.solve(w).table)
    for i in range(L.TEST_BASE, L.TEST_BASE + 300):
        a, b = sim.run_campaign(w, n2, i), sim.run_campaign(w, dpol, i)
        assert a.decisions == b.decisions and a.Y == b.Y


def test_n4_matches_the_exact_dp_in_the_budget_world():
    w = X.WORLDS["budget"]
    dev = range(L.DEV_BASE, L.DEV_BASE + L.N_DEV)
    n4, _ = L.fit_n4(w, L.dev_trace(w, dev, wide=True), dev)
    exact = EP.Threshold(dp.solve(w).table)
    test = range(L.TEST_BASE, L.TEST_BASE + 5000)
    d = sim.campaign_values(w, n4, test) - sim.campaign_values(w, exact, test)
    gain = dp.solve(w).value - max(dp.static_value(w, g) for g in dp.size_law(w).v)
    assert abs(d.mean()) <= 1.96 * d.std(ddof=1) / math.sqrt(len(d)) + 0.05 * gain


def test_tuning_never_runs_test_campaigns(monkeypatch):
    """Instrumented (review P4 finding 8): every campaign run while tuning all rungs lies in the dev block."""
    seen = []
    real = sim.run_campaign

    def spy(world, policy, instance, **kw):
        seen.append(int(instance))
        return real(world, policy, instance, **kw)
    monkeypatch.setattr(sim, "run_campaign", spy)
    monkeypatch.setattr(L, "N_DEV", 25)
    pols, facts, cache = R.tune_rungs(X.WORLDS["eval_allocation"])
    assert seen and min(seen) >= L.DEV_BASE and max(seen) < L.DEV_BASE + 25
    assert {"N1", "N2", "N2b", "N3", "N4", "margin", "sprt", "race", "kg", "rawkeep"} <= set(pols)
    for k, f in facts.items():
        if "charged" in f:
            assert f["charged"] <= f["budget"] == L.TUNE_BUDGET, k


def test_every_tuned_rung_is_charged_the_coarse_grid():
    w = X.WORLDS["budget"]
    cache = L.DevCache(w, range(L.DEV_BASE, L.DEV_BASE + 30))
    t1, t3 = L.Tuner(cache), L.Tuner(cache)
    L.tune_static(t1)
    L.tune_n3(t3, w)
    coarse = {EP.Static(g, h).name for g in L.COARSE_G for h in L.COARSE_H}
    assert coarse <= set(t1.charged) and coarse <= set(t3.charged)        # warm starts are paid for
    with pytest.raises(L.BudgetExceeded):
        tiny = L.Tuner(cache, budget=1)
        tiny.arr(EP.Static(0.0, 0.0))
        tiny.arr(EP.Static(0.001, 0.0))


# ---------------------------------------------------------------- ladder table (committed)

@pytest.fixture(scope="module")
def ladder():
    return json.loads(LADDER.read_text())


def test_ladder_is_current(ladder):
    assert ladder["code_sha256"] == R.code_sha256(), "rebuild with python -m paperc.runner"
    otab = json.loads(OT.OUT.read_text())
    assert ladder["oracle_table_sha256"] == otab["code_sha256"]
    assert set(ladder["worlds"]) == set(X.WORLDS)
    for name, rec in ladder["worlds"].items():
        assert rec["code_sha256"] == ladder["code_sha256"], name
        assert rec["oracle_member"] == otab["worlds"][name]["oracle"]["selection"]["best_member"], name


@pytest.mark.parametrize("name", sorted(X.WORLDS))
def test_ladder_rows(ladder, name):
    rec = ladder["worlds"][name]
    rows = rec["rows"]
    need = {"N0", "N1", "N2", "N2b", "N3", "N4", "margin", "rawkeep", "oracle", "random_N1"}
    if "verify" in X.WORLDS[name].epochs:
        need |= {"sprt", "race", "kg"}
    else:
        assert not {"sprt", "race", "kg"} & set(rows)          # no verify epoch: no sequential-test rows
    assert need <= set(rows)
    assert all(r["record_violations"] == 0 for r in rows.values())
    assert all(hi <= L.TEST_BASE for _, hi in rec["dev_ranges_run"])
    for k, r in rows.items():
        t = r["tuning"] or {}
        if "charged" in t:
            assert t["charged"] <= t["budget"] == L.TUNE_BUDGET, k
    assert rows["N1"]["vs_N1"]["diff"] == 0.0


def test_null_no_row_beats_the_exact_bayes_rule(ladder):
    """In the strict null the exact DP is the Bayes rule; no row may beat it beyond its 95 % interval."""
    for k, r in ladder["worlds"]["strict_null"]["rows"].items():
        assert r["vs_dp"]["diff"] <= r["vs_dp"]["half_width"] + 1e-12, k


def test_budget_world_dp_rungs(ladder):
    rows = ladder["worlds"]["budget"]["rows"]
    assert rows["N4"]["vs_N1"]["diff"] - rows["N4"]["vs_N1"]["half_width"] > 0
    w = X.WORLDS["budget"]
    gain = dp.solve(w).value - max(dp.static_value(w, g) for g in dp.size_law(w).v)
    assert abs(rows["N4"]["vs_dp"]["diff"]) <= rows["N4"]["vs_dp"]["half_width"] + 0.05 * gain
