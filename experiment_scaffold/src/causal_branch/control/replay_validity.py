"""Population-scoped replay-discrepancy allowance (RUNBOOK §12.2).

This module implements the *population* use of the replay allowance.  A fixed
policy's population lower bound loses at most ``2p`` under a declared joint
discrepancy event of probability at most ``p``.  The allowance is applied to
fixed policies only; selecting among a policy family uses *simultaneous*
population bounds and abstains if none qualifies.

A global ``p`` does **not** justify a pointwise gate ``LCB(w) - 2p`` applied per
checkpoint, and the binary ``R=1`` sharper endpoint is not applied to continuous
``U``.  The functions here refuse any call shaped like a per-checkpoint /
pointwise gate (for example an array-valued ``w`` input).  See RUNBOOK §12.2 and
B_DECISIONS_20260927.md for the scope.

No model calls or scientific evidence are involved.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from causal_branch.control.bounds import (
    DEFAULT_CONTRAST_RANGE,
    one_sided_lcb as _shared_lcb,
)

#: Accepted provenance for a replay allowance.  ``sensitivity_assumption`` is a
#: declared working assumption; ``validated_evidence`` requires bound evidence.
PROVENANCE_KINDS = ("sensitivity_assumption", "validated_evidence")


class ReplayValidityError(ValueError):
    """A replay-allowance request violates the population scope (RUNBOOK §12.2)."""


def _require_scalar(value, name: str) -> float:
    if isinstance(value, (list, tuple, np.ndarray)):
        raise ReplayValidityError(
            f"{name} must be a scalar for a fixed policy; an array-valued input "
            "is a per-checkpoint/pointwise gate, which RUNBOOK §12.2 refuses. A "
            "global p does not justify LCB(w) - 2p."
        )
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:  # pragma: no cover - defensive
        raise ReplayValidityError(f"{name} must be a finite scalar") from exc
    if not math.isfinite(out):
        raise ReplayValidityError(f"{name} must be finite")
    return out


def _require_probability(value, name: str) -> float:
    out = _require_scalar(value, name)
    if not 0.0 <= out <= 1.0:
        raise ReplayValidityError(f"{name} must lie in [0, 1]")
    return out


def population_lower_bound(
    policy_gain_lcb,
    p,
    *,
    contrast_range: tuple[float, float] = DEFAULT_CONTRAST_RANGE,
) -> float:
    """Population lower bound ``lcb - 2p`` for a **fixed** policy.

    ``policy_gain_lcb`` is a scalar sampling lower bound on the intended
    population gain of one fixed policy.  The returned bound is clipped to the
    declared contrast range.  An array-valued ``policy_gain_lcb`` is refused.
    """

    lcb = _require_scalar(policy_gain_lcb, "policy_gain_lcb")
    prob = _require_probability(p, "p")
    low, high = contrast_range
    if not low <= high:
        raise ReplayValidityError("contrast_range must be ordered")
    return max(low, min(high, lcb - 2.0 * prob))


def population_contrast_lower_bound(
    policy_gain_lcb,
    p_path,
    *,
    m: int,
    contrast_range: tuple[float, float] = DEFAULT_CONTRAST_RANGE,
) -> float:
    """Population bound ``lcb - 2 * m * p_path`` for a batch-allocated contrast.

    Under shared batch allocation a discrepancy at one root can change the
    realized regime of up to ``m`` roots (the derived displacement constant), so
    the per-root ``2p`` tax becomes ``2 * m * p_path`` (design §7).  ``p_path``
    bounds the probability of a discrepancy anywhere on a root's path.
    """

    lcb = _require_scalar(policy_gain_lcb, "policy_gain_lcb")
    prob = _require_probability(p_path, "p_path")
    m = _require_multiplier(m)
    low, high = contrast_range
    if not low <= high:
        raise ReplayValidityError("contrast_range must be ordered")
    return max(low, min(high, lcb - 2.0 * m * prob))


def _require_multiplier(m) -> int:
    if isinstance(m, bool) or not isinstance(m, int) or m < 1:
        raise ReplayValidityError("m must be a positive integer")
    return m


def _sampling_lcb(values: np.ndarray, per_member_alpha: float,
                  contrast_range: tuple[float, float] = DEFAULT_CONTRAST_RANGE) -> float:
    """Sampling lower bound using the shared width-from-range radius (F3)."""

    try:
        return _shared_lcb(values, per_member_alpha, contrast_range=contrast_range)
    except ValueError as exc:
        raise ReplayValidityError(str(exc)) from exc


def simultaneous_family_bounds(
    family_gains: dict[str, np.ndarray],
    alpha: float,
    p,
    *,
    contrast_range: tuple[float, float] = DEFAULT_CONTRAST_RANGE,
) -> tuple[dict[str, float], dict[str, float]]:
    """Simultaneous population lower bounds over a finite frozen policy family.

    ``family_gains`` maps each policy name to a 1-D array of independent-unit
    paired gains.  A Bonferroni allocation divides ``alpha`` by the family size;
    the one-sided Hoeffding width is derived from ``contrast_range`` (default
    width 2).  Each member's lower bound is then shifted by ``2p``.  The function
    returns ``(qualifying, all_bounds)``; ``qualifying`` is empty when no member
    clears zero, and the caller abstains.
    """

    if not isinstance(family_gains, dict) or not family_gains:
        raise ReplayValidityError("family_gains must be a non-empty mapping")
    prob = _require_probability(p, "p")
    if not 0.0 < alpha < 1.0:
        raise ReplayValidityError("alpha must lie in (0,1)")
    per_member_alpha = alpha / len(family_gains)
    bounds = {
        name: population_lower_bound(
            _sampling_lcb(values, per_member_alpha, contrast_range), prob,
            contrast_range=contrast_range,
        )
        for name, values in family_gains.items()
    }
    qualifying = {name: bound for name, bound in bounds.items() if bound > 0.0}
    return qualifying, bounds


def p_grid_report(
    family_gains: dict[str, np.ndarray],
    grid,
    *,
    alpha: float = 0.05,
    contrast_range: tuple[float, float] = DEFAULT_CONTRAST_RANGE,
    m: int = 1,
    checkpoints: int = 1,
) -> dict[str, float | None]:
    """Largest surviving ``p`` per policy conclusion.

    Selection is simultaneous over the family (Bonferroni: ``alpha`` is divided
    by the family size here, so callers pass the family-wise ``alpha``).
    ``contrast_range`` fixes the Hoeffding width (default 2).

    Each grid value ``p`` is a per-checkpoint allowance.  With ``checkpoints=2``
    the path allowance is the union bound ``min(1, p1 + p2)`` with
    ``p1 = p2 = p``; the conclusion survives when ``lcb - 2 * m * p_path > 0``.
    The defaults (``m=1``, ``checkpoints=1``) are the fixed-policy, per-root
    ``2p`` rule.  Returns ``None`` for a conclusion that does not survive
    ``p = 0``.
    """

    if not isinstance(family_gains, dict) or not family_gains:
        raise ReplayValidityError("family_gains must be a non-empty mapping")
    grid = sorted(float(p) for p in grid)
    if any(not 0.0 <= p <= 1.0 for p in grid):
        raise ReplayValidityError("the p grid must lie in [0,1]")
    m = _require_multiplier(m)
    if checkpoints not in (1, 2):
        raise ReplayValidityError("checkpoints must be 1 or 2")
    per_member_alpha = alpha / len(family_gains)
    out: dict[str, float | None] = {}
    for name, values in family_gains.items():
        sampling = _sampling_lcb(values, per_member_alpha, contrast_range)
        surviving = []
        for p in grid:
            if checkpoints == 2:
                allowance = CheckpointAllowance(p, "sensitivity_assumption")
                p_path = path_allowance(allowance, allowance)
            else:
                p_path = p
            if population_contrast_lower_bound(sampling, p_path, m=m,
                                               contrast_range=contrast_range) > 0.0:
                surviving.append(p)
        out[name] = max(surviving) if surviving else None
    return out


@dataclass(frozen=True)
class CheckpointAllowance:
    """One checkpoint's allowance and its provenance."""

    p: float | None
    provenance_kind: str | None


def path_allowance(p1: CheckpointAllowance, p2: CheckpointAllowance) -> float:
    """Joint path allowance ``min(1, p1 + p2)`` for a two-checkpoint comparison.

    Refuses when either checkpoint bound lacks a valid provenance kind or a
    declared value.  Independence is **not** assumed: this is a union bound.
    """

    for label, allowance in (("p1", p1), ("p2", p2)):
        if not isinstance(allowance, CheckpointAllowance):
            raise ReplayValidityError(f"{label} must be a CheckpointAllowance")
        if allowance.provenance_kind not in PROVENANCE_KINDS:
            raise ReplayValidityError(
                f"{label} lacks a valid provenance kind "
                f"(accepted: {PROVENANCE_KINDS})"
            )
        if allowance.p is None:
            raise ReplayValidityError(f"{label} has no declared p value")
        if not 0.0 <= float(allowance.p) <= 1.0:
            raise ReplayValidityError(f"{label}.p must lie in [0,1]")
    return min(1.0, float(p1.p) + float(p2.p))


def audit_upper_confidence_bound(n_audits: int, n_misses: int = 0,
                                 confidence: float = 0.95) -> float:
    """One-sided upper confidence bound on the miss probability.

    For zero misses in ``n`` independent audits this is
    ``1 - (1 - confidence)**(1 / n)``.  Real detectors can miss defects, so this
    is optimistic; it bounds a miss rate on the audited defect panel, not the
    natural prevalence of unknown omissions.
    """

    if not isinstance(n_audits, int) or isinstance(n_audits, bool) or n_audits < 1:
        raise ReplayValidityError("n_audits must be a positive integer")
    if not isinstance(n_misses, int) or isinstance(n_misses, bool) or not 0 <= n_misses <= n_audits:
        raise ReplayValidityError("n_misses must be an integer in [0, n_audits]")
    if not 0.0 < confidence < 1.0:
        raise ReplayValidityError("confidence must lie in (0,1)")
    if n_misses > 0:
        # A conservative rule-of-three style bound is not claimed here; the
        # zero-miss form is the documented check.
        raise ReplayValidityError("only the zero-miss upper bound is implemented")
    return 1.0 - (1.0 - confidence) ** (1.0 / n_audits)


def audits_needed_for_bound(p, confidence: float = 0.95) -> int:
    """Zero-miss audits needed for the one-sided bound to reach ``p``."""

    prob = _require_probability(p, "p")
    if not 0.0 < confidence < 1.0:
        raise ReplayValidityError("confidence must lie in (0,1)")
    if prob <= 0.0:
        raise ReplayValidityError("p must be positive")
    return int(math.ceil(math.log(1.0 - confidence) / math.log(1.0 - prob)))
