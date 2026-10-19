"""C3 prior arms A1-A3 (C3_DESIGN §5). ENGINEERING_ONLY; AI-assisted (Claude).

Every arm maps a proposal row to a 12-bin distribution over z = Delta/sigma_node
(bin 0 = inert) and hence to (pi, mu, tau) via ``labels.moments``. The decisions
come from ``rules`` only, so arms differ only in the prior.

- A0  rho: execute everything, keep iff Delta_hat > 0 (reference, no prior).
- A1  constant prior per node (C2 index policy, D23): the weighted mean soft
      label of the node's training proposals, inert ones included.
- A2  A1 + rules (D25/D27, T4 Corollary 8a): pi = 1 on rule-detectable inert
      proposals (active projection equals the incumbent's or was evaluated
      before); otherwise pi = 0 and the node's mean non-inert soft label.
- A3  LightGBM multiclass on the 12 bins, trained with soft labels by
      sample-weight expansion; the same rule override as A2 is applied (rules
      are free, so H1 = A3 - A2 isolates the learned part).

Training rows carry a ``weight`` (inverse audit-sampling probability within a
(source, node) stratum; 1 for inert rows) and a ``soft`` label (12-vector).
For an unseen node (leave-one-node-out) A1/A2 fall back to the pooled z-scale
constants of the training nodes.
"""
from __future__ import annotations

import numpy as np

from r1.c3.features import FEATURES, CAT_FEATURES
from r1.c3.labels import INERT, N_BINS, moments

TAU_FLOOR_Z = 0.15  # floor on tau in z units: the narrowest interior bin half-width


def is_noop(row: dict) -> bool:
    """Active projection equals the incumbent's: Delta = 0 exactly."""
    if "noop" in row:
        return bool(row["noop"])
    return bool(row["features"]["active_equals_incumbent"])


def is_duplicate(row: dict) -> bool:
    """Repeat of an earlier evaluated non-incumbent configuration: result known, Delta != 0 in general."""
    if "duplicate" in row:
        return bool(row["duplicate"])
    return bool(not is_noop(row) and row["features"]["active_seen_before"])


def rule_skip(row: dict) -> bool:
    """Rule layer (A2 and above): skip no-ops and duplicates before execution."""
    return is_noop(row) or is_duplicate(row)


rule_inert = rule_skip  # backward-compatible alias (pre-19 Oct name)


def _labelled(rows):
    return [r for r in rows if r.get("soft") is not None]


def _wmean(P, w):
    w = np.asarray(w, float)
    return (np.asarray(P) * w[:, None]).sum(0) / max(w.sum(), 1e-12)


class ConstantPrior:
    name = "A1"

    def fit(self, rows):
        rows = _labelled(rows)
        P = np.array([r["soft"] for r in rows])
        w = np.array([r["weight"] for r in rows])
        self.pooled = _wmean(P, w)
        self.by_node = {}
        for node in {r["node"] for r in rows}:
            idx = [i for i, r in enumerate(rows) if r["node"] == node]
            self.by_node[node] = _wmean(P[idx], w[idx])
        return self

    def predict(self, rows):
        return np.array([self.by_node.get(r["node"], self.pooled) for r in rows])


class RulesPrior:
    name = "A2"

    def fit(self, rows):
        non = [r for r in _labelled(rows) if not rule_skip(r)]
        P = np.array([r["soft"] for r in non])
        w = np.array([r["weight"] for r in non])
        self.pooled = self._noninert(_wmean(P, w))
        self.by_node = {}
        for node in {r["node"] for r in non}:
            idx = [i for i, r in enumerate(non) if r["node"] == node]
            self.by_node[node] = self._noninert(_wmean(P[idx], w[idx]))
        return self

    @staticmethod
    def _noninert(p):
        p = np.array(p, float)
        p[INERT] = 0.0
        return p / p.sum()

    def predict(self, rows):
        out = []
        for r in rows:
            if is_noop(r):
                p = np.zeros(N_BINS)
                p[INERT] = 1.0
            else:  # duplicates: forced skip in the decision layer; prediction unused there
                p = self.by_node.get(r["node"], self.pooled)
            out.append(p)
        return np.array(out)


def feature_matrix(rows, drop=()):
    cols = [c for c in FEATURES if c not in drop]
    X = np.array([[float(r["features"][c]) for c in cols] for r in rows], dtype=float)
    return X, cols


class LGBMPrior:
    name = "A3"

    def __init__(self, params=None, rounds: int = 80, drop=(), seed: int = 0):
        self.params = {"objective": "multiclass", "num_class": N_BINS, "learning_rate": 0.05,
                       "num_leaves": 4, "min_data_in_leaf": 5, "min_sum_hessian_in_leaf": 1e-3,
                       "lambda_l2": 1.0, "feature_fraction": 0.9, "bagging_fraction": 1.0,
                       "verbose": -1, "num_threads": 1, "deterministic": True, "seed": seed,
                       **(params or {})}
        self.rounds, self.drop = rounds, tuple(drop)

    def fit(self, rows):
        import lightgbm as lgb
        rows = _labelled(rows)
        X, self.cols = feature_matrix(rows, self.drop)
        xs, ys, ws = [], [], []
        for i, r in enumerate(rows):
            for b, pb in enumerate(r["soft"]):
                if pb > 1e-4:
                    xs.append(X[i]); ys.append(b); ws.append(pb * r["weight"])
        ws = np.asarray(ws)
        ws = ws * len(ws) / ws.sum()
        cats = [self.cols.index(c) for c in CAT_FEATURES if c in self.cols]
        data = lgb.Dataset(np.array(xs), label=np.array(ys), weight=ws, categorical_feature=cats,
                           free_raw_data=False, params={"verbose": -1})
        self.model = lgb.train(self.params, data, num_boost_round=self.rounds)
        return self

    def predict_raw(self, rows):
        X, _ = feature_matrix(rows, self.drop)
        return self.model.predict(X)

    def predict(self, rows):
        P = self.predict_raw(rows)
        out = []
        for r, p in zip(rows, P):
            if is_noop(r):
                q = np.zeros(N_BINS)
                q[INERT] = 1.0
            else:
                q = np.array(p, float)
                q[INERT] = 0.0
                q = q / q.sum()
            out.append(q)
        return np.array(out)


def prior_moments(P, rows):
    """(pi, mu, tau) in metric units from bin distributions, with the tau floor."""
    sig = np.array([r["sigma_node"] for r in rows])
    return moments(P, sig, tau_floor_z=TAU_FLOOR_Z)


ARMS = {"A1": ConstantPrior, "A2": RulesPrior, "A3": LGBMPrior}
