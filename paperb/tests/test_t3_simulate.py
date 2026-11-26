"""T3 simulator sanity checks (small runs)."""
from __future__ import annotations

import numpy as np

from r1.theory.simulate import SimConfig, simulate


def test_fresh_draws_stall_true_improvements():
    out = simulate(SimConfig(regime="fresh", rho=0.0, policy="rho", runs=30, seed=1), n_campaigns=600)
    acc = np.array(out["acceptance_of_true_improvements_by_trial"], dtype=float)
    assert np.nanmean(acc[:5]) > np.nanmean(acc[15:30]) + 0.1
    assert out["mean_record_bias_end"] > 0


def test_crn_damps_the_stall():
    fresh = simulate(SimConfig(regime="fresh", rho=0.0, policy="rho", runs=30, seed=2), n_campaigns=600)
    crn = simulate(SimConfig(regime="crn", rho=0.8, policy="rho", runs=30, seed=2), n_campaigns=600)
    late = lambda o: np.nanmean(np.array(o["acceptance_of_true_improvements_by_trial"], dtype=float)[15:30])
    assert late(crn) > late(fresh)


def test_verifying_everything_costs_value_when_proposals_are_good():
    rho = simulate(SimConfig(regime="crn", policy="rho", runs=30, seed=3), n_campaigns=600)
    always = simulate(SimConfig(regime="crn", policy="always", runs=30, seed=3), n_campaigns=600)
    assert always["mean_verifies"] > 0
    assert rho["mean_final"] > always["mean_final"]
