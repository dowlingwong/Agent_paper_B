"""D13 matched-information feature view, CPU preparation only.

AI-assisted (Codex); no embedding model or TabPFN is loaded here. Embeddings are
to be provided by a separately authorized TASL-7 pipeline. PCA fitting is
disabled until training-partition and embedding provenance can be verified.
This module does not read any label table or evaluation label.
"""
from __future__ import annotations

import numpy as np
from sklearn.decomposition import PCA

from r1.c3.features import FEATURES
from r1.c3.labels import EDGES, N_BINS


def bin_regression_cdf(cdf_at_edges, *, inert=False):
    """Integrate a supplied regression CDF over canonical z-bin intervals.

    The provider must evaluate its predictive CDF at EDGES[1:-1]. Inert is
    reserved for a rule-established exact no-op, not a regression class. The
    pinned TabPFN provider and its predictive-distribution API are not wired.
    """
    result = np.zeros(N_BINS, dtype=float)
    if inert:
        result[0] = 1.0
        return result
    cdf = np.asarray(cdf_at_edges, dtype=float)
    if (cdf.shape != (len(EDGES) - 2,) or not np.isfinite(cdf).all() or
            (cdf < 0).any() or (cdf > 1).any() or (np.diff(cdf) < 0).any()):
        raise ValueError('CDF values must be finite, in [0, 1], and nondecreasing at the ten interior edges')
    result[1:] = np.diff(np.concatenate([[0.], cdf, [1.]]))
    return result


class MatchedView:
    def __init__(self, dimensions=16):
        if type(dimensions) is not int or dimensions != 16:
            raise ValueError('D13 fixes PCA to 16 dimensions')
        self.dimensions = dimensions
        self.pca = PCA(n_components=dimensions, svd_solver='full')
        self._fitted = False

    def fit(self, training_rows, training_embeddings):
        """Currently unavailable; no supplied rows or embeddings are consumed."""
        raise RuntimeError('STOP: verified training-partition and embedding provenance not implemented')

    def transform(self, rows, embeddings):
        if not self._fitted:
            raise RuntimeError('PCA must be fitted on training rows')
        rows = list(rows)
        x = np.asarray(embeddings, dtype=float)
        if x.ndim != 2 or x.shape[0] != len(rows) or x.shape[1] != self.pca.n_features_in_ or not np.isfinite(x).all():
            raise ValueError('invalid embedding matrix')
        hand = np.array([[float(row['features'][k]) for k in FEATURES] for row in rows], dtype=float)
        if not np.isfinite(hand).all():
            raise ValueError('invalid hand features')
        return np.concatenate([hand, self.pca.transform(x)], axis=1)

    @staticmethod
    def serialize(values):
        """Kev matched view: numeric features only; free proposal text is never included."""
        row = np.asarray(values, dtype=float)
        if row.ndim != 1 or not np.isfinite(row).all():
            raise ValueError('features must be a finite vector')
        return ' '.join(f'f{i}={x:.17g}' for i, x in enumerate(row))
