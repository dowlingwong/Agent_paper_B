"""T2: closed forms for incremental acceptance under noise, and the index policies.

Model (docs/r1/theory/T2_DERIVATIONS.md, §1). One trial at decision epoch E2:

- the proposal's true increment is Delta ~ N(mu0, tau^2) (the proposal law, per node);
- the campaign observes Delta_hat = Delta + e, e ~ N(0, sigma_d^2), where
  sigma_d^2 = sigma_t^2 + sigma_s^2 splits into a training-seed part and a split-seed part;
- verify(r) observes r paired fresh differences. Under the ``"vary"`` split
  policy each is Delta + xi_i with xi_i ~ N(0, sigma_t^2 + sigma_s^2); under
  ``"fixed"`` each is Delta + e_s + xi_i with xi_i ~ N(0, sigma_t^2), where e_s
  is the split part of the campaign's own error (the split is not resampled).

Everything is exact linear-Gaussian algebra; nothing is fitted here.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

SQRT2 = math.sqrt(2.0)


def Phi(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / SQRT2))


def phi(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def psi(z: float) -> float:
    """KG kernel psi(z) = phi(z) - z * Phi(-z) for z >= 0 (Frazier et al. 2008)."""
    z = abs(z)
    return phi(z) - z * Phi(-z)


@dataclass(frozen=True)
class NodeNoise:
    """Per-node noise and proposal-law parameters (from E1 and from campaign history)."""

    mu0: float       # mean true increment of a proposal
    tau: float       # sd of true increments
    sigma_t: float   # sd of one paired comparison from the training seed
    sigma_s: float   # sd of one paired comparison from the split seed

    @property
    def sigma_d(self) -> float:
        return math.hypot(self.sigma_t, self.sigma_s)


# ---------------------------------------------------------------------------
# Proposition 1: one-step value of a threshold rule
# ---------------------------------------------------------------------------

def error_rate(delta: float, sigma_d: float) -> float:
    """P(default rule decides the wrong sign) for a fixed true increment (T1 H1)."""
    if sigma_d <= 0:
        return 0.0 if delta != 0 else 0.5
    return Phi(-abs(delta) / sigma_d)


def threshold_value(t: float, nn: NodeNoise) -> float:
    """V(t) = E[Delta * 1{Delta_hat > t}] under the prior (one trial, keep iff Delta_hat > t)."""
    s = math.hypot(nn.tau, nn.sigma_d)
    if s == 0:
        return max(nn.mu0, 0.0) if nn.mu0 > t else 0.0
    z = (t - nn.mu0) / s
    return nn.mu0 * Phi(-z) + (nn.tau ** 2 / s) * phi(z)


def bayes_threshold(nn: NodeNoise) -> float:
    """t* = -mu0 * sigma_d^2 / tau^2: keep iff the posterior mean of Delta is positive."""
    if nn.tau == 0:
        return math.inf if nn.mu0 <= 0 else -math.inf
    return -nn.mu0 * nn.sigma_d ** 2 / nn.tau ** 2


def posterior(delta_hat: float, nn: NodeNoise) -> tuple[float, float]:
    """Posterior mean and variance of Delta after the campaign's single comparison."""
    if nn.tau == 0:
        return nn.mu0, 0.0
    if nn.sigma_d == 0:
        return delta_hat, 0.0
    v = 1.0 / (1.0 / nn.tau ** 2 + 1.0 / nn.sigma_d ** 2)
    m = v * (nn.mu0 / nn.tau ** 2 + delta_hat / nn.sigma_d ** 2)
    return m, v


# ---------------------------------------------------------------------------
# Propositions 2-3: value of information of verify(r)
# ---------------------------------------------------------------------------

def _joint_cov(nn: NodeNoise, r: int, policy: str) -> tuple[np.ndarray, np.ndarray]:
    """Mean and covariance of (Delta, Delta_hat, Dbar) under the prior."""
    t2, s2, tau2 = nn.sigma_t ** 2, nn.sigma_s ** 2, nn.tau ** 2
    mean = np.array([nn.mu0, nn.mu0, nn.mu0])
    if policy == "vary":
        var_dbar = tau2 + (t2 + s2) / r
        cov_hat_dbar = tau2
    elif policy == "fixed":
        var_dbar = tau2 + s2 + t2 / r
        cov_hat_dbar = tau2 + s2          # the split error e_s is shared with Delta_hat
    else:
        raise ValueError(f"unknown split policy {policy!r}")
    cov = np.array([
        [tau2, tau2, tau2],
        [tau2, tau2 + t2 + s2, cov_hat_dbar],
        [tau2, cov_hat_dbar, var_dbar],
    ])
    return mean, cov


def preposterior_sd(delta_hat: float, nn: NodeNoise, r: int, policy: str = "vary") -> float:
    """sd of the change in E[Delta | .] that verify(r) will cause, given Delta_hat (s-tilde in T2)."""
    if r <= 0:
        return 0.0
    _, cov = _joint_cov(nn, r, policy)
    # Var(Delta | Delta_hat) - Var(Delta | Delta_hat, Dbar)
    def cond_var(idx):
        s11 = cov[0, 0]
        s12 = cov[0, idx]
        s22 = cov[np.ix_(idx, idx)]
        if np.allclose(s22, 0):
            return s11
        return float(s11 - s12 @ np.linalg.pinv(s22) @ s12)
    v1 = cond_var([1])
    v2 = cond_var([1, 2])
    return math.sqrt(max(v1 - v2, 0.0))


def verify_voi(delta_hat: float, nn: NodeNoise, r: int, policy: str = "vary") -> float:
    """KG value of information of verify(r), in metric units, with a Bayes response.

    VoI = s~ * psi(|m| / s~), m = E[Delta | Delta_hat], s~ = preposterior_sd.
    """
    m, _ = posterior(delta_hat, nn)
    s = preposterior_sd(delta_hat, nn, r, policy)
    if s == 0:
        return 0.0
    return s * psi(m / s)


def frozen_response_value(delta_hat: float, nn: NodeNoise, r: int, policy: str = "vary") -> float:
    """E[Delta * 1{Dbar > 0} | Delta_hat]: value of verify with the harness's frozen response (keep iff Dbar > 0)."""
    mean, cov = _joint_cov(nn, r, policy)
    # condition (Delta, Dbar) on Delta_hat
    idx_a, idx_b = [0, 2], [1]
    s_ab = cov[np.ix_(idx_a, idx_b)]
    s_bb = cov[np.ix_(idx_b, idx_b)]
    if s_bb[0, 0] == 0:
        cm, cc = mean[idx_a], cov[np.ix_(idx_a, idx_a)]
    else:
        k = s_ab @ np.linalg.inv(s_bb)
        cm = mean[idx_a] + (k @ (np.array([delta_hat]) - mean[idx_b])).ravel()
        cc = cov[np.ix_(idx_a, idx_a)] - k @ s_ab.T
    mu_d, mu_db = cm
    var_db = cc[1, 1]
    cov_d_db = cc[0, 1]
    if var_db <= 0:
        return mu_d if mu_db > 0 else 0.0
    sd = math.sqrt(var_db)
    z = -mu_db / sd
    return mu_d * Phi(-z) + cov_d_db / sd * phi(z)


def default_rule_value(delta_hat: float, nn: NodeNoise) -> float:
    """E[Delta * 1{Delta_hat > 0} | Delta_hat] = m * 1{Delta_hat > 0}."""
    m, _ = posterior(delta_hat, nn)
    return m if delta_hat > 0 else 0.0


# ---------------------------------------------------------------------------
# Proposition 4: incumbent bias and stagnation
# ---------------------------------------------------------------------------

def acceptance_probability(delta: float, incumbent_bias: float, sigma: float, rho: float) -> float:
    """P(keep a true improvement delta | the incumbent's recorded error is e).

    Per-run error eta ~ N(0, sigma^2); the candidate's error has correlation rho
    with the incumbent's (rho = 0: fresh-draw regime; rho > 0: CRN with a local edit):
    P = Phi((delta - (1 - rho) e) / (sigma * sqrt(1 - rho^2))).
    """
    if not -1.0 < rho < 1.0:
        raise ValueError("rho must lie in (-1, 1)")
    return Phi((delta - (1.0 - rho) * incumbent_bias) / (sigma * math.sqrt(1.0 - rho * rho)))


def expected_record(n: int, sigma: float = 1.0) -> float:
    """E[max of n iid N(0, sigma^2)] (numerical; n >= 1). Used for the null-proposal bias."""
    if n < 1:
        raise ValueError("n >= 1")
    if n == 1:
        return 0.0
    x = np.linspace(-8, 8, 16001)
    cdf = 0.5 * (1.0 + np.vectorize(math.erf)(x / SQRT2))
    pdf = np.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)
    return float(sigma * np.trapezoid(x * n * cdf ** (n - 1) * pdf, x))


# ---------------------------------------------------------------------------
# Index policies (D23 candidates)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class KGIndexPolicy:
    """KG-style E2 index: verify iff VoI(Delta_hat) > 2 r * g (run price).

    Implementable under D4 (the keep rule is overridden only by verify's frozen
    response): the index only decides *whether* to verify. ``g`` is the value
    of one worker run spent on a fresh proposal, estimated per node.
    """

    nn: NodeNoise
    r: int = 2
    g: float = 0.0
    policy: str = "vary"

    def decide(self, delta_hat: float, remaining_runs: int) -> str:
        if remaining_runs < 2 * self.r:
            return "continue"
        voi = verify_voi(delta_hat, self.nn, self.r, self.policy)
        return "verify" if voi > 2 * self.r * self.g else "continue"


def run_price(nn: NodeNoise) -> float:
    """Stationary value of one run spent on a fresh proposal under the Bayes threshold (Prop. 5)."""
    return max(threshold_value(bayes_threshold(nn), nn), 0.0)
