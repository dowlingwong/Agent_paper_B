"""Matched two-checkpoint controllers and total-work accounting (B4).

All controllers act on one shared information set and tuning protocol and
receive the same *allowed* verifier-call and total-work budgets.  Realized use
is reported separately; unspent capacity stays unspent.  The regimes are the
three complete regimes on one original root: verify-now, continue-then-verify-
at-2 (with continue fallback), and never.

Nothing here is scientific evidence.  These are engineering fixtures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math

import numpy as np

REGIMES = ("now", "later", "never")


class BudgetError(ValueError):
    """A controller violates the matched-budget contract."""


# --------------------------------------------------------------------------
# Budgets and the cost ledger
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Budget:
    """Allowed verifier calls and allowed total work for one controller."""

    allowed_verifier_calls: int
    allowed_work: float

    def __post_init__(self) -> None:
        if self.allowed_verifier_calls < 0:
            raise BudgetError("allowed verifier calls must be nonnegative")
        if not math.isfinite(self.allowed_work) or self.allowed_work < 0:
            raise BudgetError("allowed work must be finite and nonnegative")


@dataclass(frozen=True)
class LeafCost:
    """Per-leaf cost ledger.  All channels are separate and nonnegative."""

    prefix: float = 0.0
    continuation_ckpt2: float = 0.0
    verifier_overhead: float = 0.0
    failed_attempts: float = 0.0
    storage: float = 0.0

    def channels(self) -> dict[str, float]:
        return {
            "prefix": self.prefix,
            "continuation_ckpt2": self.continuation_ckpt2,
            "verifier_overhead": self.verifier_overhead,
            "failed_attempts": self.failed_attempts,
            "storage": self.storage,
        }

    def total(self) -> float:
        return float(sum(self.channels().values()))


def allowed_tree_budget(n_original_roots: int, q: float, work_per_call: float) -> Budget:
    """The registered original-root tree budget: ``floor(q * N_original)`` calls.

    This is *not* the one-step ``ceil(q * n_feasible)`` convention; the two
    denominators are never exchanged.
    """

    if not isinstance(n_original_roots, int) or isinstance(n_original_roots, bool) or n_original_roots < 1:
        raise BudgetError("n_original_roots must be a positive integer")
    if not 0.0 < q <= 1.0:
        raise BudgetError("capacity q must lie in (0,1]")
    calls = int(math.floor(q * n_original_roots))
    return Budget(calls, calls * float(work_per_call))


def assert_matched_allowed_budgets(allowed: dict[str, Budget]) -> None:
    """Budget matching requires the *same allowed* verifier and total-work budgets."""

    if len(allowed) < 1:
        raise BudgetError("no controllers supplied")
    distinct = {(b.allowed_verifier_calls, b.allowed_work) for b in allowed.values()}
    if len(distinct) != 1:
        raise BudgetError(
            "budget matching requires equal allowed verifier-call and total-work "
            f"budgets; got {sorted(distinct)}"
        )


@dataclass
class BudgetReport:
    allowed: Budget
    realized_calls: int
    realized_work: float

    def __post_init__(self) -> None:
        if self.realized_calls < 0 or self.realized_work < 0:
            raise BudgetError("realized use must be nonnegative")
        if self.realized_calls > self.allowed.allowed_verifier_calls:
            raise BudgetError("realized verifier calls exceed the allowed budget")
        if self.realized_work > self.allowed.allowed_work + 1e-12:
            raise BudgetError("realized work exceeds the allowed budget")

    @property
    def unspent_calls(self) -> int:
        return self.allowed.allowed_verifier_calls - self.realized_calls

    @property
    def unspent_work(self) -> float:
        return self.allowed.allowed_work - self.realized_work


# --------------------------------------------------------------------------
# Controllers
# --------------------------------------------------------------------------


@dataclass
class FrozenReserveVOI:
    """Constant-reserve scheduler (ablation only).

    Reserve the single verification for checkpoint 2 unless the checkpoint-1
    value estimate exceeds a constant reserve threshold fixed on development
    data.  At checkpoint 2 the verification is used only when the checkpoint-2
    score exceeds ``c2``; reaching checkpoint 2 is not by itself a reason to
    verify.  Controllers never consume a replay allowance.
    """

    reserve_threshold: float
    c2: float = 0.0

    def choose(self, adv1: float, adv2: float, *, reached2: bool,
               budget_remaining: int = 1) -> str:
        if budget_remaining < 1:
            return "never"
        if adv1 > self.reserve_threshold:
            return "now"
        if reached2 and adv2 > self.c2:
            return "later"
        return "never"


@dataclass
class RepeatedMyopic:
    """Apply the one-step advantage rule at each checkpoint while budget remains."""

    c1: float = 0.0
    c2: float = 0.0

    def choose(self, adv1: float, adv2: float, *, reached2: bool,
               budget_remaining: int = 1) -> str:
        if budget_remaining < 1:
            return "never"
        if adv1 > self.c1:
            return "now"
        if reached2 and adv2 > self.c2:
            return "later"
        return "never"


@dataclass
class FixedRegime:
    regime: str

    def __post_init__(self) -> None:
        if self.regime not in REGIMES:
            raise BudgetError(f"unknown fixed regime {self.regime!r}")

    def choose(self, adv1: float, adv2: float, *, reached2: bool,
               budget_remaining: int = 1) -> str:
        if self.regime == "never" or budget_remaining < 1:
            return "never"
        if self.regime == "later" and not reached2:
            return "never"
        return self.regime


# --------------------------------------------------------------------------
# The CINC-style one-step random-forest witness
# --------------------------------------------------------------------------


@dataclass
class RFWitness:
    """One-step random-forest witness: 200 trees, depth 6, per-tree penalty.

    This follows the nearest prior's stated configuration (200-tree, depth-6
    random forests) and adds a per-tree uncertainty penalty to the predicted
    probability.  It uses scikit-learn's implementation; the deviation from the
    paper's likely implementation is documented: the penalty is expressed as a
    z-multiple of the across-tree standard deviation rather than an unspecified
    interval width.
    """

    n_estimators: int = 200
    max_depth: int = 6
    penalty_multiplier: float = 1.0
    seed: int = 20260927

    def fit(self, rows, labels):
        try:
            from sklearn.ensemble import RandomForestClassifier
        except ImportError as exc:  # pragma: no cover - environment guard
            raise BudgetError(
                "scikit-learn is required for the RF witness; install the pinned "
                "CPU wheel from requirements.lock"
            ) from exc
        x = np.asarray([[r[n] for n in sorted(rows[0])] for r in rows], dtype=float)
        y = np.asarray(labels)
        self._features = sorted(rows[0])
        self.model = RandomForestClassifier(
            n_estimators=self.n_estimators, max_depth=self.max_depth,
            random_state=self.seed,
        ).fit(x, y)
        return self

    def predict(self, rows):
        if not hasattr(self, "model"):
            raise BudgetError("RF witness must be fitted")
        x = np.asarray([[r[n] for n in self._features] for r in rows], dtype=float)
        per_tree = np.stack([tree.predict_proba(x)[:, 1] for tree in self.model.estimators_])
        return per_tree.mean(axis=0) - self.penalty_multiplier * per_tree.std(axis=0)


def ridge_equivalence_gap(adv_scores, value_difference) -> float:
    """Return the max abs gap between the advantage learner and value difference.

    Ridge is affine in the response with identical designs, so this must be at
    most ``1e-12``; the comparison is an implementation equivalence check, not a
    hypothesis.
    """

    adv = np.asarray(adv_scores, dtype=float)
    diff = np.asarray(value_difference, dtype=float)
    if adv.shape != diff.shape:
        raise BudgetError("advantage and value-difference shapes differ")
    return float(np.max(np.abs(adv - diff)))


def assert_ridge_equivalence(adv_scores, value_difference, tol: float = 1e-12) -> float:
    gap = ridge_equivalence_gap(adv_scores, value_difference)
    if gap > tol:
        raise BudgetError(
            f"ridge advantage/action-value equivalence violated: gap {gap:.3e} > {tol:.1e}"
        )
    return gap
