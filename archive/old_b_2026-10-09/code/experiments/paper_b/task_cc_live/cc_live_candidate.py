"""F8: the exact executable candidate, the fit tool and the frozen verifier.

The fit tool returns the candidate it actually evaluated (a decision stump), not
a description.  The verifier checks consistency against visible development
diagnostics and replaces the candidate only on a **strict** visible improvement;
ties leave it unchanged.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json

import numpy as np


@dataclass(frozen=True)
class Stump:
    feature: int
    threshold: float
    direction: int  # +1: predict 1 when x > threshold; -1: predict 1 when x <= threshold

    def predict(self, x: np.ndarray) -> np.ndarray:
        column = np.asarray(x, dtype=float)[:, self.feature]
        above = column > self.threshold
        return ((above == (self.direction == 1))).astype(int)

    def to_json(self) -> str:
        return json.dumps(asdict(self), sort_keys=True)


def accuracy(candidate: Stump, x: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean(candidate.predict(x) == np.asarray(y)))


def fit_stump(x: np.ndarray, y: np.ndarray, *, max_candidates: int = 32,
              feature_indices=None) -> Stump:
    """Return the exact executable candidate the fit tool evaluated."""

    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=int)
    features = list(range(x.shape[1])) if feature_indices is None else list(feature_indices)
    best = None
    best_acc = -1.0
    for feature in features:
        column = x[:, feature]
        thresholds = np.unique(column)
        if len(thresholds) > max_candidates:
            picks = np.linspace(0, len(thresholds) - 1, max_candidates).astype(int)
            thresholds = thresholds[picks]
        for threshold in thresholds:
            for direction in (1, -1):
                candidate = Stump(feature, float(threshold), direction)
                acc = accuracy(candidate, x, y)
                if acc > best_acc:  # deterministic: first best wins
                    best, best_acc = candidate, acc
    if best is None:
        raise ValueError("no candidate evaluated")
    return best


def verifier(candidate: Stump, x_dev: np.ndarray, y_dev: np.ndarray, *,
             feature_indices=None, max_candidates: int = 32) -> Stump:
    """Frozen response rule: replace only on a strict visible improvement."""

    diagnostic = fit_stump(x_dev, y_dev, max_candidates=max_candidates,
                           feature_indices=feature_indices)
    if accuracy(diagnostic, x_dev, y_dev) > accuracy(candidate, x_dev, y_dev):
        return diagnostic
    return candidate
