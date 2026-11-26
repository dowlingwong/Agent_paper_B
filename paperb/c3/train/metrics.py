"""Track P evaluation metrics (spec §4, §5.4, §7.1; RUNBOOK Track P 1.3). ENGINEERING_ONLY; AI-assisted (Claude).

numpy, vectorised over rows; p, y are [N, 12] bin distributions (bin 0 inert, bins 1..11 ordered in z), y the soft
labels. Definitions:

- ``rps``: the RPS of ``losses`` (bin-0 Brier + label-weighted ordinal RPS over bins 1-11, in [0, 1]).
- ``rps_skill`` = 1 - mean RPS(model) / mean RPS(base rate); the base-rate forecast is the (weighted) mean y of the
  training portion, passed in by the caller (spec §5.4).
- ``ece_all_bins``: every (p_ik, y_ik) pair of every row and bin is one forecast; pairs are grouped into equal-width
  confidence bins on p; ECE = sum_b (n_b / n) |mean p - mean y| in each group (soft y = observed frequency).
- ``ece_top1``: the same over the argmax bin of each row only (confidence p_ik*, outcome y_ik*). Reported alongside
  the all-bins value because top-1 alone can look good while the distribution has collapsed (spec §7.1).
- ``pit_histogram``: expected randomised PIT of the ordered bins 1-11 under the soft label. With F the forecast CDF of
  the non-inert part (renormalised), an outcome in bin k gives PIT ~ U(F_{k-1}, F_k); the outcome is drawn from the
  label's non-inert part r. The histogram (density over ``n`` equal bins) is computed in closed form, each row
  weighted by its non-inert label mass 1 - y_0. Calibrated forecasts give a flat histogram (density 1).
  ``pit_values`` gives randomised PIT values for realised z draws instead.
- ``width_ratio`` = mean predictive sd / mean label sd, sd over the bin midpoints (``labels.MIDPOINTS``, tails at +-4)
  of the renormalised non-inert part, in z units; rows whose label is (numerically) all inert are excluded. ~1 is
  right, << 1 is collapse.
- ``disagreement_rate``: share of rows where the action head's execute decision differs from rule(belief).
- ``fit_temperature`` / ``apply_temperature``: post-hoc temperature scaling of belief logits, one scalar T fitted on
  dev by minimising the soft-label cross-entropy (golden-section search in log T over [0.05, 20]); the same
  procedure for every model, Kev included (its built-in pointer temperature stays 1; R1-TEMPERATURE, 26 Oct).

RPS normalisation (R1-RPS-NORM, 26 Oct): the ordinal part is (1/(K-1)) sum_k (Q_k - R_k)^2 over the K = 11 ordered
bins 1-11 (10 cumulative terms), on the non-inert parts; with the bin-0 Brier term,
RPS = 0.5 * (Brier_0 + (1 - y_0) * ordinal), in [0, 1].
"""
from __future__ import annotations

import numpy as np

from r1.c3.labels import EDGES, MIDPOINTS

EPS = 1e-8


def _arr(x) -> np.ndarray:
    return np.asarray(x, float)


def _conditional(p: np.ndarray) -> np.ndarray:
    rest = p[..., 1:]
    return rest / np.maximum(rest.sum(axis=-1, keepdims=True), EPS)


def _weights(w, n: int) -> np.ndarray:
    return np.ones(n) if w is None else _arr(w)


def rps(p, y) -> np.ndarray:
    p, y = _arr(p), _arr(y)
    brier0 = (p[..., 0] - y[..., 0]) ** 2
    Q = np.cumsum(_conditional(p), axis=-1)[..., :-1]
    R = np.cumsum(_conditional(y), axis=-1)[..., :-1]
    return 0.5 * (brier0 + (1.0 - y[..., 0]) * ((Q - R) ** 2).mean(axis=-1))


def mean_rps(p, y, w=None) -> float:
    r = rps(p, y)
    return float(np.average(r, weights=_weights(w, len(r))))


def base_rate(y_train, w=None) -> np.ndarray:
    """Base-rate forecast: the (weighted) mean training label."""
    y_train = _arr(y_train)
    return np.average(y_train, axis=0, weights=_weights(w, len(y_train)))


def rps_skill(p, y, base, w=None) -> float:
    p, y = _arr(p), _arr(y)
    b = np.broadcast_to(_arr(base), p.shape)
    return 1.0 - mean_rps(p, y, w) / mean_rps(b, y, w)


def _ece(conf: np.ndarray, out: np.ndarray, n_bins: int) -> float:
    idx = np.clip((conf * n_bins).astype(int), 0, n_bins - 1)
    total = 0.0
    for b in range(n_bins):
        m = idx == b
        if m.any():
            total += m.sum() * abs(conf[m].mean() - out[m].mean())
    return float(total / len(conf))


def ece_all_bins(p, y, n_bins: int = 10) -> float:
    return _ece(_arr(p).ravel(), _arr(y).ravel(), n_bins)


def ece_top1(p, y, n_bins: int = 10) -> float:
    p, y = _arr(p), _arr(y)
    k = p.argmax(axis=-1)
    rows = np.arange(len(p))
    return _ece(p[rows, k], y[rows, k], n_bins)


def pit_histogram(p, y, n: int = 10) -> np.ndarray:
    """Expected PIT density over ``n`` equal bins on [0, 1] (module docstring)."""
    p, y = _arr(p), _arr(y)
    F = np.concatenate([np.zeros((len(p), 1)), np.cumsum(_conditional(p), axis=-1)], axis=1)  # [N, 12]
    F[:, -1] = 1.0
    r = _conditional(y)
    w = 1.0 - y[:, 0]
    grid = np.linspace(0.0, 1.0, n + 1)
    lo, hi = F[:, :-1], F[:, 1:]                                  # [N, 11] outcome intervals
    width = np.maximum(hi - lo, 1e-12)
    hist = np.zeros(n)
    for j in range(n):
        a, b = grid[j], grid[j + 1]
        overlap = np.clip(np.minimum(hi, b) - np.maximum(lo, a), 0.0, None) / width
        # a zero-width interval (p_k = 0) contributes its point mass to the grid bin holding it
        point = (hi - lo <= 1e-12) & (lo >= a) & ((lo < b) | ((j == n - 1) & (lo <= b)))
        overlap = np.where(hi - lo <= 1e-12, point.astype(float), overlap)
        hist[j] = (w[:, None] * r * overlap).sum()
    return hist / max(w.sum(), EPS) * n


def pit_values(p, z, rng=None) -> np.ndarray:
    """Randomised PIT values of realised standardised increments z under the forecasts' non-inert parts."""
    p, z = _arr(p), _arr(z)
    rng = np.random.default_rng(0) if rng is None else rng
    F = np.concatenate([np.zeros((len(p), 1)), np.cumsum(_conditional(p), axis=-1)], axis=1)
    k = np.clip(np.searchsorted(EDGES, z, side="left") - 1, 0, 10)  # 0-based index of bins 1..11 (labels.hard_bin - 1)
    rows = np.arange(len(p))
    lo, hi = F[rows, k], F[rows, k + 1]
    return lo + rng.uniform(size=len(p)) * (hi - lo)


def predictive_sd(p) -> np.ndarray:
    """sd (z units) of the renormalised non-inert part over the bin midpoints."""
    q = _conditional(_arr(p))
    mu = (q * MIDPOINTS).sum(axis=-1)
    return np.sqrt((q * (MIDPOINTS - mu[..., None]) ** 2).sum(axis=-1))


def width_ratio(p, y) -> float:
    p, y = _arr(p), _arr(y)
    keep = y[:, 0] < 1.0 - 1e-9
    if not keep.any():
        return float("nan")
    return float(predictive_sd(p[keep]).mean() / predictive_sd(y[keep]).mean())


def disagreement_rate(action_execute, rule_execute) -> float:
    a, r = np.asarray(action_execute, bool), np.asarray(rule_execute, bool)
    if a.shape != r.shape:
        raise ValueError("action and rule decisions must have the same shape")
    return float((a != r).mean()) if a.size else float("nan")


def _log_softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(axis=-1, keepdims=True)
    return z - np.log(np.exp(z).sum(axis=-1, keepdims=True))


def apply_temperature(logits, T: float) -> np.ndarray:
    z = _arr(logits) / float(T)
    return np.exp(_log_softmax(z))


def fit_temperature(logits, y, lo: float = 0.05, hi: float = 20.0, iters: int = 80) -> float:
    """Scalar T minimising the mean soft-label cross-entropy of softmax(logits / T) on (dev) rows."""
    z, y = _arr(logits), _arr(y)
    nll = lambda t: float(-(y * _log_softmax(z / np.exp(t))).sum(axis=-1).mean())  # noqa: E731
    a, b = np.log(lo), np.log(hi)
    g = (np.sqrt(5.0) - 1.0) / 2.0
    c, d = b - g * (b - a), a + g * (b - a)
    fc, fd = nll(c), nll(d)
    for _ in range(iters):
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - g * (b - a)
            fc = nll(c)
        else:
            a, c, fc = c, d, fd
            d = a + g * (b - a)
            fd = nll(d)
    return float(np.exp((a + b) / 2.0))
