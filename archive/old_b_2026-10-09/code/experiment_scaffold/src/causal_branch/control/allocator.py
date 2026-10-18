"""Shared two-phase hard-budget allocator (F4, design §5).

Every controller uses this allocator.  Controllers differ only in their scores
``s1`` and ``s2``, their cutoffs ``c1`` and ``c2``, and their reservation ``R``.
The allocator never reads a replay allowance, leaf outcomes or hidden data.

- ``B = floor(q * N)`` verifier calls total, at most one per root.
- **Phase 1** ranks feasible roots by ``s1``, descending (ties by a declared
  outcome-blind hash of the root id), and verifies the top roots with
 
  ``s1 > c1`` up to ``B - R``.
- **Phase 2** ranks reached, unverified, feasible roots by ``s2`` and verifies
  the top roots with ``s2 > c2`` until capacity is exhausted.
- Infeasible roots fall back to continue; early-terminated roots never enter
  phase 2; unspent capacity stays unspent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import math

REGIMES = ("now", "later", "never")


class AllocatorError(ValueError):
    """An allocation request violates the hard-budget contract."""


@dataclass(frozen=True)
class AllocatorRoot:
    root_id: str
    s1: float
    s2: float = 0.0
    feasible1: bool = True
    feasible2: bool = True
    reached2: bool = False
    terminated: bool = False
    family: str = ""
    split: str = ""


@dataclass(frozen=True)
class AllocatorParams:
    c1: float
    c2: float
    reserve: int = 0

    def __post_init__(self) -> None:
        if self.reserve < 0:
            raise AllocatorError("reserve must be nonnegative")


@dataclass
class AllocationResult:
    regimes: dict[str, str]
    verified: list[str]
    realized_calls: int
    unspent_calls: int
    work: float
    budget: int


def budget_for(n_roots: int, q: float = 0.25) -> int:
    """``floor(q * N)`` original-root tree budget."""

    if not isinstance(n_roots, int) or isinstance(n_roots, bool) or n_roots < 0:
        raise AllocatorError("n_roots must be a nonnegative integer")
    if not 0.0 < q <= 1.0:
        raise AllocatorError("q must lie in (0,1]")
    return int(math.floor(q * n_roots))


def tie_break_hash(root_id: str) -> str:
    """Declared outcome-blind tie-break: a hash of the root id only."""

    return hashlib.sha256(root_id.encode("utf-8")).hexdigest()


def allocate(
    roots: list[AllocatorRoot],
    *,
    budget: int,
    params: AllocatorParams,
    work_per_call: float = 1.0,
    q: float | None = None,
) -> AllocationResult:
    """Run the two-phase allocation.

    With ``q`` given, the allocator itself enforces the hard budget
    ``budget == floor(q * N)`` for this batch (review B2).  With ``q=None`` any
    nonnegative integer budget is accepted, and the caller is responsible for
    passing ``budget_for(len(roots), q)``; the evaluation harness always
    passes ``q``.
    """

    if not isinstance(budget, int) or isinstance(budget, bool) or budget < 0:
        raise AllocatorError("budget must be a nonnegative integer")
    if q is not None and budget != budget_for(len(roots), q):
        raise AllocatorError(
            f"budget {budget} != floor(q * N) = {budget_for(len(roots), q)} "
            f"for q={q} and N={len(roots)}")
    if len({r.root_id for r in roots}) != len(roots):
        raise AllocatorError("duplicate root ids")
    regimes: dict[str, str] = {}
    verified: list[str] = []

    # Phase 1: feasible roots by s1, descending, up to B - R.
    eligible1 = [r for r in roots if r.feasible1]
    ranked1 = sorted(eligible1, key=lambda r: (-r.s1, tie_break_hash(r.root_id)))
    capacity1 = max(0, budget - params.reserve)
    for root in ranked1:
        if len(verified) >= capacity1:
            break
        if root.s1 > params.c1:
            regimes[root.root_id] = "now"
            verified.append(root.root_id)
        else:
            break  # descending: the remainder cannot exceed c1

    # Phase 2: reached, unverified, feasible roots by s2, until exhausted.
    remaining = budget - len(verified)
    verified_set = set(verified)
    eligible2 = [
        r for r in roots
        if r.reached2 and not r.terminated and r.feasible2
        and r.root_id not in verified_set
    ]
    ranked2 = sorted(eligible2, key=lambda r: (-r.s2, tie_break_hash(r.root_id)))
    used2 = 0
    for root in ranked2:
        if used2 >= remaining:
            break
        if root.s2 > params.c2:
            regimes[root.root_id] = "later"
            verified.append(root.root_id)
            used2 += 1
        else:
            break

    for root in roots:
        regimes.setdefault(root.root_id, "never")

    realized = len(verified)
    if realized > budget:
        raise AllocatorError("realized verifier calls exceed the budget")
    if len(set(verified)) != realized:
        raise AllocatorError("a root was verified twice")
    return AllocationResult(
        regimes=regimes,
        verified=verified,
        realized_calls=realized,
        unspent_calls=budget - realized,
        work=realized * float(work_per_call),
        budget=budget,
    )
