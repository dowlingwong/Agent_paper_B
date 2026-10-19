"""T4 closed forms used by every C3 arm (ENGINEERING_ONLY; AI-assisted (Claude)).

Notation (T4 §0): s^2 = tau^2 + sigma^2, z = (t - mu)/s,
V(t; mu, tau, sigma) = mu Phi(-z) + (tau^2/s) phi(z)  -- value E[Delta 1{Delta_hat > t}]
for Delta ~ N(mu, tau^2), Delta_hat = Delta + N(0, sigma^2).

- Proposition 6: t* = -mu sigma^2 / tau^2, keep iff Delta_hat > t*;
  per-proposal value V* = (1 - pi) V(t*).
- Proposition 7: gap of an arbitrary threshold t~ (exact integral and bounds).
- Proposition 8: execute iff V* >= g; screening gain (g - V*)^+.

All functions are vectorised over numpy arrays.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.stats import norm

SQRT_2PI = math.sqrt(2.0 * math.pi)


def _s(tau, sigma):
    return np.sqrt(np.asarray(tau, float) ** 2 + np.asarray(sigma, float) ** 2)


def value(t, mu, tau, sigma):
    """T2 Proposition 1 value V(t; mu, tau, sigma) = E[Delta * 1{Delta_hat > t}]."""
    t, mu, tau, sigma = (np.asarray(x, float) for x in (t, mu, tau, sigma))
    s = _s(tau, sigma)
    z = (t - mu) / s
    return mu * norm.sf(z) + (tau ** 2 / s) * norm.pdf(z)


def bayes_threshold(mu, tau, sigma):
    """Proposition 6 threshold t* = -mu sigma^2 / tau^2 (tau > 0 required)."""
    mu, tau, sigma = (np.asarray(x, float) for x in (mu, tau, sigma))
    if np.any(tau <= 0):
        raise ValueError("tau must be positive")
    return -mu * sigma ** 2 / tau ** 2


def proposal_value(pi, mu, tau, sigma):
    """Proposition 6 maximal value V* = (1 - pi) V(t*; mu, tau, sigma)."""
    pi = np.asarray(pi, float)
    return (1.0 - pi) * value(bayes_threshold(mu, tau, sigma), mu, tau, sigma)


def execute(pi, mu, tau, sigma, g):
    """Proposition 8 screening rule: execute iff V* >= g."""
    return proposal_value(pi, mu, tau, sigma) >= np.asarray(g, float)


def keep(delta_hat, mu, tau, sigma):
    """Proposition 6 acceptance rule: keep iff Delta_hat > t*."""
    return np.asarray(delta_hat, float) > bayes_threshold(mu, tau, sigma)


def screening_term(pi, mu, tau, sigma, g):
    """Proposition 8 per-proposal screening gain (g - V*)^+ over always-execute."""
    return np.maximum(np.asarray(g, float) - proposal_value(pi, mu, tau, sigma), 0.0)


def gap_exact(t_tilde, pi, mu, tau, sigma):
    """Proposition 7 identity: V* - (1-pi) V(t~) =
    (1-pi)(tau^2/s^2) |int_{t~}^{t*} f(u)(t* - u) du|, f = N(mu, s^2) density.

    Closed form of the integral over [a, b]:
    (t* - mu)[Phi((b-mu)/s) - Phi((a-mu)/s)] + s^2 [f(b) - f(a)].
    """
    t_tilde, pi, mu, tau, sigma = (np.asarray(x, float) for x in (t_tilde, pi, mu, tau, sigma))
    s = _s(tau, sigma)
    ts = bayes_threshold(mu, tau, sigma)
    a, b = t_tilde, ts
    f = lambda u: norm.pdf(u, loc=mu, scale=s)  # noqa: E731
    integral = (ts - mu) * (norm.cdf((b - mu) / s) - norm.cdf((a - mu) / s)) + s ** 2 * (f(b) - f(a))
    return (1.0 - pi) * (tau ** 2 / s ** 2) * np.abs(integral)


def gap_bounds(t_tilde, pi, mu, tau, sigma):
    """Proposition 7 bounds (lower, upper) on the gap."""
    t_tilde, pi, mu, tau, sigma = (np.asarray(x, float) for x in (t_tilde, pi, mu, tau, sigma))
    s = _s(tau, sigma)
    ts = bayes_threshold(mu, tau, sigma)
    d2 = (ts - t_tilde) ** 2
    # min of a unimodal density on an interval is attained at an endpoint
    fmin = np.minimum(norm.pdf(ts, loc=mu, scale=s), norm.pdf(t_tilde, loc=mu, scale=s))
    lower = (1.0 - pi) * (tau ** 2 / (2 * s ** 2)) * fmin * d2
    upper = (1.0 - pi) * tau ** 2 * d2 / (2 * SQRT_2PI * s ** 3)
    return lower, upper


def gap_approx(t_tilde, pi, mu, tau, sigma):
    """Second-order approximation (1-pi) tau^2 f(t*) (t* - t~)^2 / (2 s^2)."""
    t_tilde, pi, mu, tau, sigma = (np.asarray(x, float) for x in (t_tilde, pi, mu, tau, sigma))
    s = _s(tau, sigma)
    ts = bayes_threshold(mu, tau, sigma)
    return (1.0 - pi) * tau ** 2 * norm.pdf(ts, loc=mu, scale=s) * (ts - t_tilde) ** 2 / (2 * s ** 2)


def decide(pi, mu, tau, sigma, g, delta_hat, inert=None):
    """Plug-in decisions (execute, keep) for arrays of proposals.

    keep is only possible when executed. ``inert`` (optional) is informational:
    on an inert proposal the logged Delta_hat is 0 and keep is evaluated with
    the same rule (its true value is 0 either way).
    """
    ex = execute(pi, mu, tau, sigma, g)
    kp = ex & keep(delta_hat, mu, tau, sigma)
    return ex, kp
