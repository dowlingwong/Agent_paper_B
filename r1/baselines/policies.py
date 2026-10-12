"""E2 trigger policies scored on the sibling table (BUILD_RUNBOOK L10).

Every policy maps a learner projection to a *score* for verify; the shared
spending rule turns scores into actions: verify iff score > c and verify is
feasible.  Each arm tunes its own c on development instances from the same grid
size (``TUNING_BUDGET``), which ``matching_report`` checks.

Projection features used (all pre-treatment, built by the E1b collector):
``delta_hat`` (candidate metric minus current_best), ``sigma_d`` (node paired
noise from E1, a development constant), ``sigma_t`` / ``sigma_s`` (its
training/split parts), ``remaining_runs``, ``budget_index``, ``n_keeps``,
``repeated_bad`` (harness heuristic flag), ``r`` (verify pairs).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from r1.theory.acceptance import NodeNoise, default_rule_value, frozen_response_value, run_price, verify_voi

TUNING_BUDGET = 21  # candidate cutoffs per arm


def feat(p: dict, key: str, default: float = 0.0) -> float:
    v = p["features"].get(key, default)
    return float(default if v is None else v)


# ----- rule scores -------------------------------------------------------------

def score_rho(p: dict) -> float:
    return -math.inf


def score_always(p: dict) -> float:
    return math.inf


def score_margin(p: dict) -> float:
    """Noise-aware threshold in its D4-compatible form: verify when the margin is small in noise units."""
    s = feat(p, "sigma_d", 0.0)
    if s <= 0:
        return -math.inf
    return -abs(feat(p, "delta_hat")) / s


def score_heuristic(p: dict) -> float:
    """Harness heuristic: doom-loop / repeated-bad flag (an E1 skip rule; at E2 it can only trigger verify)."""
    return 1.0 if feat(p, "repeated_bad") > 0 else -1.0


# ----- KG-style index (T2, Proposition 5) ----------------------------------------

@dataclass
class KGIndex:
    """KG-style E2 index with (mu0, tau, g) fitted on development projections.

    ``response="frozen"`` (default; L14 finding 5) prices the action the harness
    actually executes: the frozen response keep iff Dbar > 0 under the
    campaign's split policy (feature ``split_policy``, default ``fixed``):
        score = [E(Delta 1{Dbar>0} | Delta_hat) - E(Delta 1{Delta_hat>0} | Delta_hat)] / (2r) - g.
    ``response="bayes"`` is the T2 Proposition 2 value of information with the
    Bayes response, an upper bound on what any response rule could gain.
    """

    by_node: dict = field(default_factory=dict)
    response: str = "frozen"

    def fit(self, projections: list[dict]) -> "KGIndex":
        groups: dict[str, list[dict]] = {}
        for p in projections:
            groups.setdefault(p["features"].get("node", "?"), []).append(p)
        for node, ps in groups.items():
            dh = np.array([feat(p, "delta_hat") for p in ps])
            st, ss = feat(ps[0], "sigma_t"), feat(ps[0], "sigma_s")
            sd2 = st ** 2 + ss ** 2
            tau = math.sqrt(max(float(np.var(dh)) - sd2, 1e-12)) if dh.size > 1 else math.sqrt(sd2)
            nn = NodeNoise(mu0=float(np.mean(dh)) if dh.size else 0.0, tau=tau, sigma_t=st, sigma_s=ss)
            self.by_node[node] = (nn, run_price(nn))
        return self

    def score(self, p: dict) -> float:
        node = p["features"].get("node", "?")
        if node not in self.by_node:
            return -math.inf
        nn, g = self.by_node[node]
        r = int(feat(p, "r", 2))
        policy = str(p["features"].get("split_policy", "fixed"))
        dh = feat(p, "delta_hat")
        if self.response == "bayes":
            gain = verify_voi(dh, nn, r, policy)
        else:
            gain = frozen_response_value(dh, nn, r, policy) - default_rule_value(dh, nn)
        return gain / (2 * r) - g


# ----- learned baselines -----------------------------------------------------------

FEATURES = ("delta_hat_z", "abs_delta_hat_z", "positive", "remaining_frac", "n_keeps", "budget_index")


def design(p: dict) -> np.ndarray:
    s = max(feat(p, "sigma_d", 1.0), 1e-9)
    dh = feat(p, "delta_hat")
    total = max(feat(p, "total_runs", 1.0), 1.0)
    return np.array([dh / s, abs(dh) / s, 1.0 if dh > 0 else 0.0,
                     feat(p, "remaining_runs") / total, feat(p, "n_keeps"), feat(p, "budget_index")], dtype=float)


@dataclass
class RidgeAdvantage:
    """Ridge regression of the full-information advantage V(verify) - V(continue) on the design."""

    l2: float = 1.0
    w: np.ndarray | None = None
    mu: np.ndarray | None = None
    sd: np.ndarray | None = None

    def fit(self, X: np.ndarray, adv: np.ndarray) -> "RidgeAdvantage":
        self.mu, self.sd = X.mean(0), X.std(0) + 1e-9
        Z = np.c_[np.ones(len(X)), (X - self.mu) / self.sd]
        A = Z.T @ Z + self.l2 * np.eye(Z.shape[1])
        A[0, 0] -= self.l2
        self.w = np.linalg.solve(A, Z.T @ adv)
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        Z = np.c_[np.ones(len(X)), (X - self.mu) / self.sd]
        return Z @ self.w


@dataclass
class AWRMLP:
    """AWR-style controller in the spirit of Harness-MDP (arXiv 2607.05458): a one-hidden-layer
    numpy MLP trained by advantage-weighted regression on logged (state, action) pairs.

    With a full-information table every action is logged at every point, so the
    weighted log-likelihood is sum_a exp(A(s, a) / beta) log pi(a | s), with
    A(s, a) = V(s, a) - max_a V(s, a). Labels are full-information branch values;
    this is the offline-RL baseline of PLAN §5, not a reproduction of Harness-MDP.
    """

    hidden: int = 16
    beta: float = 0.01
    l2: float = 1e-3
    lr: float = 0.05
    epochs: int = 400
    seed: int = 0
    params: dict | None = None
    mu: np.ndarray | None = None
    sd: np.ndarray | None = None

    def fit(self, X: np.ndarray, values: np.ndarray) -> "AWRMLP":
        rng = np.random.default_rng(self.seed)
        self.mu, self.sd = X.mean(0), X.std(0) + 1e-9
        Z = (X - self.mu) / self.sd
        adv = values - values.max(axis=1, keepdims=True)
        w = np.exp(np.clip(adv / self.beta, -50, 0))
        w = w / w.sum(axis=1, keepdims=True)
        d, h, k = Z.shape[1], self.hidden, values.shape[1]
        P = {"W1": rng.normal(0, 1 / math.sqrt(d), (d, h)), "b1": np.zeros(h),
             "W2": rng.normal(0, 1 / math.sqrt(h), (h, k)), "b2": np.zeros(k)}
        for _ in range(self.epochs):
            H = np.tanh(Z @ P["W1"] + P["b1"])
            logits = H @ P["W2"] + P["b2"]
            logits -= logits.max(1, keepdims=True)
            prob = np.exp(logits) / np.exp(logits).sum(1, keepdims=True)
            g_logits = (prob - w) / len(Z)
            gW2 = H.T @ g_logits + self.l2 * P["W2"]
            gb2 = g_logits.sum(0)
            gH = g_logits @ P["W2"].T * (1 - H ** 2)
            gW1 = Z.T @ gH + self.l2 * P["W1"]
            gb1 = gH.sum(0)
            for key, g in (("W1", gW1), ("b1", gb1), ("W2", gW2), ("b2", gb2)):
                P[key] -= self.lr * g
        self.params = P
        return self

    def proba(self, X: np.ndarray) -> np.ndarray:
        P = self.params
        Z = (X - self.mu) / self.sd
        logits = np.tanh(Z @ P["W1"] + P["b1"]) @ P["W2"] + P["b2"]
        logits -= logits.max(1, keepdims=True)
        e = np.exp(logits)
        return e / e.sum(1, keepdims=True)
