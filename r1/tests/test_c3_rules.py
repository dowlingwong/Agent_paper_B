"""C3 rules: T4 closed forms vs Monte Carlo. ENGINEERING_ONLY; AI-assisted (Claude)."""
import numpy as np
import pytest

from r1.c3 import rules

CASES = [(0.0, 1.0, 1.0), (-0.5, 0.8, 1.2), (0.3, 0.5, 2.0), (-0.012, 0.01, 0.0075)]


def mc_value(t, mu, tau, sigma, pi=0.0, n=1_000_000, seed=0):
    rng = np.random.default_rng(seed)
    d = rng.normal(mu, tau, n)
    dh = d + rng.normal(0, sigma, n)
    inert = rng.random(n) < pi
    d = np.where(inert, 0.0, d)
    dh = np.where(inert, 0.0, dh)
    return float(np.mean(d * (dh > t))), float(np.std(d * (dh > t)) / np.sqrt(n))


@pytest.mark.parametrize("mu,tau,sigma", CASES)
def test_value_matches_monte_carlo(mu, tau, sigma):
    for t in (-1.0 * tau, 0.0, rules.bayes_threshold(mu, tau, sigma), 0.7 * tau):
        v, se = mc_value(t, mu, tau, sigma)
        assert abs(rules.value(t, mu, tau, sigma) - v) < 5 * se + 1e-12


@pytest.mark.parametrize("mu,tau,sigma", CASES)
def test_bayes_threshold_maximises_value(mu, tau, sigma):
    ts = float(rules.bayes_threshold(mu, tau, sigma))
    grid = ts + np.linspace(-3, 3, 601) * np.hypot(tau, sigma)
    vals = rules.value(grid, mu, tau, sigma)
    assert rules.value(ts, mu, tau, sigma) >= vals.max() - 1e-12


def test_proposal_value_with_inert_mass_matches_mc():
    mu, tau, sigma, pi = -0.2, 1.0, 0.8, 0.3
    ts = rules.bayes_threshold(mu, tau, sigma)
    # keep on inert (Delta_hat = 0) is irrelevant: Delta = 0 there
    v, se = mc_value(ts, mu, tau, sigma, pi=pi)
    assert abs(rules.proposal_value(pi, mu, tau, sigma) - v) < 5 * se


@pytest.mark.parametrize("mu,tau,sigma", CASES)
def test_prop7_gap_identity_and_bounds(mu, tau, sigma):
    pi = 0.25
    for tt in (0.0, -0.5 * tau, 0.9 * tau):
        exact = rules.gap_exact(tt, pi, mu, tau, sigma)
        direct = rules.proposal_value(pi, mu, tau, sigma) - (1 - pi) * rules.value(tt, mu, tau, sigma)
        assert exact == pytest.approx(direct, rel=1e-7, abs=1e-14)
        lo, up = rules.gap_bounds(tt, pi, mu, tau, sigma)
        assert lo - 1e-15 <= exact <= up + 1e-15


def test_prop7_gap_monte_carlo():
    mu, tau, sigma, pi, tt = -0.5, 0.8, 1.2, 0.0, 0.0
    rng = np.random.default_rng(3)
    n = 2_000_000
    d = rng.normal(mu, tau, n)
    dh = d + rng.normal(0, sigma, n)
    ts = rules.bayes_threshold(mu, tau, sigma)
    diff = d * (dh > ts) - d * (dh > tt)
    assert abs(rules.gap_exact(tt, pi, mu, tau, sigma) - diff.mean()) < 5 * diff.std() / np.sqrt(n)


def test_prop7_approx_close_for_small_error():
    mu, tau, sigma = -0.2, 1.0, 1.0
    ts = float(rules.bayes_threshold(mu, tau, sigma))
    tt = ts + 0.01
    assert rules.gap_approx(tt, 0, mu, tau, sigma) == pytest.approx(rules.gap_exact(tt, 0, mu, tau, sigma), rel=0.02)


def test_prop8_screening_rule_and_term():
    mu, tau, sigma, pi = -0.3, 0.5, 1.0, 0.2
    vstar = float(rules.proposal_value(pi, mu, tau, sigma))
    for g in (0.0, vstar / 2, vstar * 2):
        assert bool(rules.execute(pi, mu, tau, sigma, g)) == (vstar >= g)
        # gain over always-execute = max(V*-g,0) - (V*-g)
        assert rules.screening_term(pi, mu, tau, sigma, g) == pytest.approx(max(vstar - g, 0) - (vstar - g))
    # inert proposals are never worth a run at g > 0 (Corollary 8a)
    assert not rules.execute(1.0, mu, tau, sigma, 1e-9)


def test_decide_keep_requires_execute():
    ex, kp = rules.decide(np.array([0.0, 1.0]), np.zeros(2), np.ones(2), np.ones(2), 0.1, np.array([5.0, 5.0]))
    assert ex.tolist() == [True, False] and kp.tolist() == [True, False]


def test_tau_must_be_positive():
    with pytest.raises(ValueError):
        rules.bayes_threshold(0.0, 0.0, 1.0)
