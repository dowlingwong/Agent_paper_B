"""C3 label bins and soft labels (C3_DESIGN §3-4). ENGINEERING_ONLY; AI-assisted (Claude).

Bin 0 is the exact no-op bin (Delta = 0: the edit leaves the active
configuration unchanged). Bins 1..11 partition z = Delta / sigma_node with
edges -inf, -3, -2, -1, -0.5, -0.15, 0.15, 0.5, 1, 2, 3, +inf.

Duplicates of an earlier evaluated configuration get NO training label: their
result is already known from the ledger and they are handled by the rule layer
(T4 Corollary 8a as revised 19 Oct 2026). They must not be labelled as bin 0.

Soft-label width (R1-SOFT-SIGMA, 26 Oct; Track P spec §3.4). Two versioned modes:
- ``pooled_node`` (v2, the default for new tables): s = sigma_pooled / sqrt(K_label),
  sigma_pooled pooled from the C1 30-seed noise-floor table (``SOFT_SIGMA_SOURCE``);
  in z units s = 1/sqrt(K) when sigma_pooled = sigma_node. Tables built with it record
  ``SOFT_LABEL_VERSIONS["pooled_node"]``.
- ``se_audit`` (v1): the per-proposal audit standard error; kept, selected explicitly,
  to reproduce existing tables (``offline_eval.assemble`` default).
Track P action target (spec §3.5): ``action_target``.
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


SOFT_LABEL_VERSIONS = {"se_audit": "soft_label/v1_se_audit", "pooled_node": "soft_label/v2_pooled_node"}
DEFAULT_SIGMA_MODE = "pooled_node"  # new tables only; reproductions pass sigma_mode="se_audit"
# C1 30-seed noise-floor table the pooled sigma comes from (dataset.E1_SUMMARY; PLAN §10, 22 Oct)
SOFT_SIGMA_SOURCE = {"file": "results/r1/pilot/E1_20261022T214606Z/summary.json",
                     "sha256": "eabc2f5c05b08cf900ab988838e41dc7f8db35a4131f4b57e72514e0e5513793",
                     "pooled_sigma": "dataset.noise_table()[node]['sigma_node'] (median sd_joint over material edits)"}


def soft_label_version(sigma_mode: str | None = None) -> str:
    return SOFT_LABEL_VERSIONS[sigma_mode or DEFAULT_SIGMA_MODE]


def _gaussian_bins(zm: float, zs: float) -> np.ndarray:
    p = np.zeros(N_BINS)
    if zs <= 0:
        p[hard_bin(zm)] = 1.0
        return p
    cdf = norm.cdf((EDGES - zm) / zs)
    p[1:] = np.diff(cdf)
    p = np.clip(p, 0.0, None)
    return p / p.sum()


def soft_label(delta_audit: float | None, se: float | None, sigma_node: float, inert: bool = False, *,
               sigma_mode: str | None = None, k_label: int | None = None,
               sigma_pooled: float | None = None) -> np.ndarray:
    """N(Delta_audit, s^2) integrated over the bins (z scale); inert -> one-hot on bin 0.

    ``sigma_mode="se_audit"`` (v1): s = ``se``. ``"pooled_node"`` (v2, default): s = sigma_pooled / sqrt(k_label),
    sigma_pooled defaulting to ``sigma_node`` (both from the C1 table); ``se`` must then be None, so a v1-style call
    cannot silently change width.
    """
    mode = sigma_mode or DEFAULT_SIGMA_MODE
    if mode not in SOFT_LABEL_VERSIONS:
        raise ValueError(f"unknown sigma_mode {mode!r}")
    if mode == "pooled_node" and se is not None:
        raise ValueError("se given under sigma_mode='pooled_node'; pass sigma_mode='se_audit' to reproduce v1 tables")
    if inert:
        p = np.zeros(N_BINS)
        p[INERT] = 1.0
        return p
    if delta_audit is None or not np.isfinite(delta_audit):
        raise ValueError("non-inert label needs a finite audit value")
    zm = float(delta_audit) / sigma_node
    if mode == "se_audit":
        zs = float(se or 0.0) / sigma_node
    else:
        if k_label is None or int(k_label) < 1:
            raise ValueError("sigma_mode='pooled_node' needs k_label >= 1 (number of label seeds)")
        sp = sigma_node if sigma_pooled is None else float(sigma_pooled)
        if not sp > 0:
            raise ValueError("pooled sigma must be positive")
        zs = sp / np.sqrt(int(k_label)) / sigma_node
    return _gaussian_bins(zm, zs)


def action_target(delta_label, delta_hat, a1_probs, sigma_node, sigma_cmp, g_units: float = 0.1,
                  tau_floor_z: float | None = None):
    """Execution utility u = mean_r(Delta_r keep) - g (spec §3.5), metric units, vectorised.

    ``delta_label``: mean paired Delta over the label seeds (7001-7005 for training, 7006-7010 for evaluation);
    keep = ``rules.keep(delta_hat, mu, tau, sigma_cmp)`` with (mu, tau) the moments of the fixed reference prior
    ``a1_probs`` (A1 constant prior, with the arms' tau floor), so u does not depend on the model being trained;
    g = g_units * sigma_node (0.1, PLAN 22 Oct). keep does not vary over seeds, so mean_r(Delta_r keep) = keep * mean.
    """
    from r1.c3 import rules
    from r1.c3.arms import TAU_FLOOR_Z
    tf = TAU_FLOOR_Z if tau_floor_z is None else tau_floor_z
    sigma_node = np.asarray(sigma_node, float)
    _, mu, tau = moments(a1_probs, sigma_node, tau_floor_z=tf)
    kp = rules.keep(delta_hat, mu, tau, sigma_cmp)
    return np.asarray(delta_label, float) * kp - g_units * sigma_node


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
