"""C3 label bins and soft labels (C3_DESIGN §3-4). ENGINEERING_ONLY; AI-assisted (Claude).

Bin 0 is the exact-inert bin. Bins 1..11 partition z = Delta / sigma_node with
edges -inf, -3, -2, -1, -0.5, -0.15, 0.15, 0.5, 1, 2, 3, +inf.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import norm

EDGES = np.array([-np.inf, -3, -2, -1, -0.5, -0.15, 0.15, 0.5, 1, 2, 3, np.inf])
N_BINS = 12  # including the inert bin
INERT = 0
TAIL = 4.0
MIDPOINTS = np.array([-TAIL, -2.5, -1.5, -0.75, -0.325, 0.0, 0.325, 0.75, 1.5, 2.5, TAIL])
BIN_NAMES = ["inert"] + [f"({EDGES[i]:g},{EDGES[i + 1]:g}]" for i in range(11)]


def hard_bin(z: float) -> int:
    """Non-inert bin index (1..11) of a standardised increment."""
    return int(np.searchsorted(EDGES, z, side="left") - 1) + 1 if np.isfinite(z) else (1 if z < 0 else 11)


def soft_label(delta_audit: float | None, se: float | None, sigma_node: float, inert: bool = False) -> np.ndarray:
    """N(Delta_audit, se^2) integrated over the bins (z scale); inert -> one-hot on bin 0."""
    p = np.zeros(N_BINS)
    if inert:
        p[INERT] = 1.0
        return p
    if delta_audit is None or not np.isfinite(delta_audit):
        raise ValueError("non-inert label needs a finite audit value")
    zm = float(delta_audit) / sigma_node
    zs = float(se or 0.0) / sigma_node
    if zs <= 0:
        p[hard_bin(zm)] = 1.0
        return p
    cdf = norm.cdf((EDGES - zm) / zs)
    p[1:] = np.diff(cdf)
    p = np.clip(p, 0.0, None)
    return p / p.sum()


def moments(p, sigma_node, tau_floor_z: float = 0.0):
    """(pi, mu, tau) from bin distribution(s) p (..., 12), rescaled by sigma_node.

    mu and tau are the mean and sd of the non-inert part over the bin midpoints
    (tails at +-4). ``tau_floor_z`` floors tau in z units (0 = none).
    """
    p = np.asarray(p, float)
    sigma_node = np.asarray(sigma_node, float)
    pi = p[..., INERT]
    q = p[..., 1:]
    mass = q.sum(axis=-1, keepdims=True)
    q = np.where(mass > 0, q / np.where(mass > 0, mass, 1.0), 1.0 / 11)
    mu_z = (q * MIDPOINTS).sum(axis=-1)
    var_z = (q * (MIDPOINTS - mu_z[..., None]) ** 2).sum(axis=-1)
    tau_z = np.maximum(np.sqrt(var_z), tau_floor_z)
    return pi, mu_z * sigma_node, tau_z * sigma_node


def prob_positive(p) -> np.ndarray:
    """P(Delta > 0) implied by a bin distribution; the central bin counts half."""
    p = np.asarray(p, float)
    return p[..., 7:].sum(axis=-1) + 0.5 * p[..., 6]


def log_score(p_true, q_pred, eps: float = 1e-12) -> np.ndarray:
    """Soft-label cross-entropy -sum_b p_b log q_b (lower is better)."""
    return -(np.asarray(p_true) * np.log(np.clip(np.asarray(q_pred), eps, 1.0))).sum(axis=-1)
