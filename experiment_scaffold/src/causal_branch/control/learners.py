"""Matched linear decision-score classes for CPU engineering fixtures.

All fits use the same ridge objective and fixed regularisation (one candidate,
no data-driven tuning). Fractional repetition means remain fractional. Risk and
advantage have one fitted head; action value has two outcome heads, whose
contrast is in the same linear decision class. Head count and fit budget are
reported explicitly; these scores are not calibrated probabilities.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np


def _feature_matrix(rows, names):
    if not rows or any(set(r) != set(names) for r in rows):
        raise ValueError('empty rows or feature registry mismatch')
    x = np.array([[r[n] for n in names]+[1.] for r in rows], dtype=float)
    if not np.isfinite(x).all():
        raise ValueError('features must be finite')
    return x


@dataclass
class _Ridge:
    l2: float = .01
    def fit(self, x, y):
        y = np.asarray(y, dtype=float)
        if y.shape != (len(x),) or not np.isfinite(y).all() or self.l2 <= 0:
            raise ValueError('unaligned/nonfinite labels or invalid regularisation')
        self.w = np.linalg.solve(x.T @ x + self.l2*np.eye(x.shape[1]), x.T @ y)
        self.n_rows = len(y)
        return self
    def predict(self, x):
        if not hasattr(self, 'w'):
            raise RuntimeError('learner must be fitted')
        return x @ self.w


class OutcomeRiskLearner:
    """Failure-risk score (secondary when U is primary)."""

    name = 'risk'
    def __init__(self, l2=.01):
        self.features = []
        self.model = _Ridge(l2)
    def fit(self, rows, successes):
        if any(not 0 <= v <= 1 for v in successes):
            raise ValueError('outcome means must be in [0,1]')
        self.features = sorted(rows[0]) if rows else []
        self.model.fit(_feature_matrix(rows, self.features), successes)
        return self
    def predict(self, rows):
        return 1.-self.model.predict(_feature_matrix(rows, self.features))


class UtilityDeficitLearner(OutcomeRiskLearner):
    """Utility-deficit score.

    With U primary this is the fair risk-style comparator: it ranks by the
    deficit ``1 - E[U^0 | W]`` rather than by a binary failure probability. The
    binary failure-risk learner is the secondary score.
    """

    name = 'deficit'


class FailureRiskLearner(OutcomeRiskLearner):
    """Secondary binary failure-risk score; not the primary U comparator."""

    name = 'failure_risk'


class AdvantageLearner(OutcomeRiskLearner):
    name = 'advantage'
    def fit(self, rows, advantages):
        if any(not -1 <= v <= 1 for v in advantages):
            raise ValueError('contrasts must be in [-1,1]')
        self.features = sorted(rows[0]) if rows else []
        self.model.fit(_feature_matrix(rows,self.features),advantages)
        return self
    def predict(self, rows):
        return self.model.predict(_feature_matrix(rows,self.features))


class ActionValueLearner:
    name = 'action_value'
    def __init__(self,l2=.01):
        self.l2 = l2
        self.features = []
        self.by_action = {}
    def fit(self, rows, actions, successes):
        if not len(rows) == len(actions) == len(successes) or set(actions) != {'g0','gv'}:
            raise ValueError('feature/action/label alignment or action support error')
        if any(not 0 <= v <= 1 for v in successes):
            raise ValueError('outcome means must be in [0,1]')
        self.features = sorted(rows[0]) if rows else []
        x = _feature_matrix(rows,self.features)
        self.by_action = {}
        for action in ('g0','gv'):
            idx = np.array([a == action for a in actions])
            self.by_action[action] = _Ridge(self.l2).fit(x[idx],np.asarray(successes)[idx])
        return self
    def predict(self,rows,actions):
        if len(rows) != len(actions) or not set(actions) <= set(self.by_action):
            raise ValueError('unaligned actions or action without fitted support')
        x = _feature_matrix(rows,self.features)
        return np.array([self.by_action[a].predict(x[i:i+1])[0] for i,a in enumerate(actions)])


def matching_report(learners):
    """Inspect fitted dimensions, features, regularisation and per-head data budget."""
    details = {}
    for learner in learners:
        heads = list(learner.by_action.values()) if isinstance(learner, ActionValueLearner) else [learner.model]
        details[learner.name] = dict(features=learner.features,
            family=sorted({type(h).__name__ for h in heads}),
            decision_parameters=sorted({len(h.w) for h in heads}),
            regularisation=sorted({h.l2 for h in heads}),
            training_units_per_head=sorted({h.n_rows for h in heads}),
            tuning_candidates=1, fitted_heads=len(heads))
    fields = ('features','family','decision_parameters','regularisation','training_units_per_head','tuning_candidates')
    same = {f: all(d[f] == next(iter(details.values()))[f] for d in details.values()) for f in fields}
    return dict(matched_decision_class=all(same.values()), checks=same, learners=details,
                limitation='Action value fits two outcome heads; others fit one. Raw fit work is not equal; the linear contrast class and one fixed tuning candidate are matched.')
