"""L10 tests: every baseline runs on the fixture, cross-fitting is by instance, matching passes."""
from __future__ import annotations

import numpy as np
import pytest

from r1.baselines.evaluate import evaluate_arms, oracle_columns
from r1.baselines.fixture import synthetic_table
from r1.baselines.responses import PaceStyleGate, RacingRule


def test_all_arms_run_and_match():
    t = synthetic_table(n_instances=8, points_per_instance=8, seed=1)
    rep = evaluate_arms(t, n_boot=200)
    for arm in ("rho", "always_verify", "random_matched", "margin_threshold", "harness_heuristic", "kg_index",
                "ridge_advantage", "awr_mlp", "oracle_naive", "oracle_leafsplit"):
        assert arm in rep.choices
        assert np.isfinite(rep.boot.estimates[arm])
    assert rep.matching["matched"]
    assert rep.verify_rate["rho"] == 0.0 and rep.verify_rate["always_verify"] == 1.0


def test_oracles_dominate_and_leafsplit_is_less_optimistic():
    t = synthetic_table(n_instances=15, points_per_instance=12, seed=2)
    rep = evaluate_arms(t, n_boot=200)
    est = rep.boot.estimates
    assert est["oracle_naive"] >= max(est[a] for a in ("rho", "always_verify", "margin_threshold", "kg_index")) - 1e-12
    assert rep.headroom_leafsplit <= rep.headroom_naive + 1e-12


def test_verify_helps_near_the_boundary_when_cheap():
    # noisy comparisons, cheap verification: the margin rule and the KG index should beat rho
    t = synthetic_table(n_instances=20, points_per_instance=15, mu0=-0.002, tau=0.008, sigma_t=0.006,
                        sigma_s=0.006, run_cost=0.0, seed=3)
    rep = evaluate_arms(t, n_boot=200)
    est = rep.boot.estimates
    assert est["margin_threshold"] > est["rho"]


def test_kg_index_rarely_verifies_at_e1_scale():
    # the KG index never sees run_cost directly; at E1-scale noise its stationary run price exceeds the VoI
    t = synthetic_table(n_instances=10, points_per_instance=10, seed=4)
    rep = evaluate_arms(t, n_boot=100)
    assert rep.verify_rate["kg_index"] < 0.2


def test_oracle_leafsplit_needs_two_leaves():
    t = synthetic_table(n_instances=3, points_per_instance=2, reps=1, seed=5)
    naive, cf, held = oracle_columns(t)
    assert cf is None and held is None and len(naive) == len(t)


def test_pace_gate_controls_false_commits_under_the_null():
    rng = np.random.default_rng(0)
    gate = PaceStyleGate(alpha=0.1, clip=0.05, max_pairs=8)
    commits = sum(gate.decide(list(rng.normal(0.0, 0.02, 8)))[0] == "commit" for _ in range(4000))
    assert commits / 4000 <= 0.1
    # power: with a strong effect and 16 pairs the gate commits most of the time; with 8 pairs at
    # alpha = 0.1 it is conservative (wealth grows at most 1.5x per pair), which is a real property
    strong = PaceStyleGate(alpha=0.1, clip=0.025, max_pairs=16)
    hits = sum(strong.decide(list(rng.normal(0.02, 0.005, 16)))[0] == "commit" for _ in range(500))
    assert hits / 500 > 0.5


def test_racing_rule_stops_early_on_clear_cases():
    race = RacingRule()
    assert race.decide([0.05, 0.051, 0.049]) == ("commit", 2)
    assert race.decide([-0.05, -0.051])[0] == "reject"
