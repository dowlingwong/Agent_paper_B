"""T2 closed forms checked against Monte Carlo (pytest)."""
from __future__ import annotations

import math

import numpy as np
import pytest

from r1.theory.acceptance import (
    KGIndexPolicy,
    NodeNoise,
    acceptance_probability,
    bayes_threshold,
    default_rule_value,
    error_rate,
    expected_record,
    frozen_response_value,
    posterior,
    preposterior_sd,
    run_price,
    threshold_value,
    verify_voi,
)

NN = NodeNoise(mu0=-0.004, tau=0.01, sigma_t=0.005, sigma_s=0.006)
RNG = np.random.default_rng(20261012)
N = 400_000


def _draw(nn: NodeNoise, n: int = N):
    delta = RNG.normal(nn.mu0, nn.tau, n)
    e_t = RNG.normal(0, nn.sigma_t, n)
    e_s = RNG.normal(0, nn.sigma_s, n)
    return delta, e_t, e_s


def test_error_rate_matches_simulation():
    e = RNG.normal(0, 0.01, N)
    assert abs(np.mean(np.sign(0.006 + e) != 1) - error_rate(0.006, 0.01)) < 3e-3


@pytest.mark.parametrize("t", [-0.01, 0.0, 0.004, 0.012])
def test_threshold_value_matches_simulation(t):
    delta, e_t, e_s = _draw(NN)
    mc = np.mean(delta * ((delta + e_t + e_s) > t))
    assert abs(mc - threshold_value(t, NN)) < 1e-4


def test_bayes_threshold_maximises_value():
    grid = np.linspace(-0.03, 0.05, 4001)
    vals = [threshold_value(t, NN) for t in grid]
    t_best = grid[int(np.argmax(vals))]
    assert abs(t_best - bayes_threshold(NN)) < 1e-4
    assert threshold_value(bayes_threshold(NN), NN) >= threshold_value(0.0, NN)


def test_default_rule_is_bayes_only_when_mu0_is_zero():
    assert bayes_threshold(NodeNoise(0.0, 0.01, 0.005, 0.005)) == 0.0
    assert bayes_threshold(NN) > 0


@pytest.mark.parametrize("policy", ["vary", "fixed"])
@pytest.mark.parametrize("delta_hat", [-0.004, 0.0, 0.003, 0.02])
def test_voi_and_frozen_response_match_simulation(policy, delta_hat):
    r = 2
    m, v = posterior(delta_hat, NN)
    # sample (Delta, e_s) from their joint posterior given Delta_hat
    tau2, t2, s2 = NN.tau ** 2, NN.sigma_t ** 2, NN.sigma_s ** 2
    mean = np.array([NN.mu0, 0.0])
    cov = np.array([[tau2, 0.0], [0.0, s2]])
    c_xy = np.array([tau2, s2])
    var_y = tau2 + t2 + s2
    k = c_xy / var_y
    post_mean = mean + k * (delta_hat - NN.mu0)
    post_cov = cov - np.outer(k, c_xy)
    draws = RNG.multivariate_normal(post_mean, post_cov, N)
    delta, e_s = draws[:, 0], draws[:, 1]
    if policy == "vary":
        dbar = delta + RNG.normal(0, math.sqrt((t2 + s2) / r), N)
    else:
        dbar = delta + e_s + RNG.normal(0, math.sqrt(t2 / r), N)
    # frozen response: keep iff dbar > 0
    mc_frozen = np.mean(delta * (dbar > 0))
    assert abs(mc_frozen - frozen_response_value(delta_hat, NN, r, policy)) < 1.5e-4
    # Bayes response: posterior mean given (Delta_hat, dbar); regress delta on dbar (exact in Gaussian)
    b = np.cov(delta, dbar)[0, 1] / np.var(dbar)
    m2 = m + b * (dbar - dbar.mean())
    mc_voi = np.mean(np.maximum(m2, 0)) - max(m, 0)
    assert abs(mc_voi - verify_voi(delta_hat, NN, r, policy)) < 1.5e-4
    assert abs(np.std(m2) - preposterior_sd(delta_hat, NN, r, policy)) < 2e-4


def test_fixed_split_verify_is_worthless_without_training_noise():
    nn0 = NodeNoise(mu0=-0.004, tau=0.01, sigma_t=1e-9, sigma_s=0.008)
    for dh in (-0.002, 0.0, 0.003):
        assert verify_voi(dh, nn0, 2, "fixed") < 1e-9
        assert verify_voi(dh, nn0, 2, "vary") > 1e-4


def test_voi_decreases_with_margin_and_increases_with_r():
    m0 = bayes_threshold(NN)  # where the posterior mean is zero
    vals = [verify_voi(m0 + d, NN, 2) for d in (0.0, 0.005, 0.01, 0.02)]
    assert all(a >= b for a, b in zip(vals, vals[1:]))
    vr = [verify_voi(m0, NN, r) for r in (1, 2, 4, 8, 16)]
    assert all(a <= b for a, b in zip(vr, vr[1:]))
    gains = np.diff(vr)
    assert gains[-1] < gains[0]  # diminishing returns per doubling


def test_acceptance_probability_matches_simulation():
    sigma, rho, e, delta = 0.01, 0.6, 0.012, 0.004
    u = RNG.normal(0, 1, N)
    eps_c = rho * e + sigma * math.sqrt(1 - rho ** 2) * u
    mc = np.mean(delta + eps_c - e > 0)
    assert abs(mc - acceptance_probability(delta, e, sigma, rho)) < 3e-3


def test_expected_record_matches_simulation():
    for n in (2, 5, 20, 100):
        mc = RNG.normal(0, 1, (50_000, n)).max(axis=1).mean()
        assert abs(mc - expected_record(n)) < 0.01


def test_kg_index_respects_budget_and_price():
    pol = KGIndexPolicy(NN, r=2, g=0.0)
    assert pol.decide(bayes_threshold(NN), remaining_runs=3) == "continue"   # 2r runs needed
    assert pol.decide(bayes_threshold(NN), remaining_runs=10) == "verify"
    expensive = KGIndexPolicy(NN, r=2, g=1.0)
    assert expensive.decide(bayes_threshold(NN), remaining_runs=10) == "continue"
    assert run_price(NN) >= 0
    assert default_rule_value(-0.001, NN) == 0.0
