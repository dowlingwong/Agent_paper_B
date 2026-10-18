"""F4: two-phase hard-budget allocator."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiment_scaffold/src"))

from hypothesis import given, settings, strategies as st  # noqa: E402
from causal_branch.control.allocator import (  # noqa: E402
    AllocatorError,
    AllocatorParams,
    AllocatorRoot,
    allocate,
    budget_for,
    tie_break_hash,
)


def _root(rid, s1, s2=0.0, reached2=True, feasible1=True, feasible2=True, terminated=False):
    return AllocatorRoot(root_id=rid, s1=s1, s2=s2, reached2=reached2,
                         feasible1=feasible1, feasible2=feasible2, terminated=terminated)


class TestAllocator(unittest.TestCase):
    def test_budget_is_floor_q_n(self):
        self.assertEqual(budget_for(10), 2)
        self.assertEqual(budget_for(3), 0)
        self.assertEqual(budget_for(0), 0)

    def test_phase1_exhaustion(self):
        roots = [_root(f"r{i}", 1.0) for i in range(5)]
        result = allocate(roots, budget=2, params=AllocatorParams(c1=0.0, c2=0.0, reserve=0))
        self.assertEqual(result.realized_calls, 2)
        self.assertEqual(result.unspent_calls, 0)
        self.assertEqual(sum(r == "now" for r in result.regimes.values()), 2)

    def test_reserve_larger_than_phase2_demand(self):
        roots = [_root(f"r{i}", 1.0, s2=1.0) for i in range(10)]
        # R = B reserves everything for phase 2; only one root qualifies there.
        params = AllocatorParams(c1=0.0, c2=0.5, reserve=3)
        result = allocate(roots, budget=3, params=params)
        self.assertEqual(result.realized_calls, 3)  # phase-2 then uses remaining
        self.assertEqual(result.unspent_calls, 0)

    def test_reserve_with_no_phase2_demand_stays_unspent(self):
        roots = [_root(f"r{i}", 1.0, reached2=False) for i in range(6)]
        params = AllocatorParams(c1=0.0, c2=0.0, reserve=3)
        result = allocate(roots, budget=3, params=params)
        self.assertEqual(result.realized_calls, 0)  # R=B, no phase-2 roots
        self.assertEqual(result.unspent_calls, 3)

    def test_ties_are_deterministic_by_hash(self):
        roots = [_root("b", 0.5), _root("a", 0.5), _root("c", 0.5)]
        params = AllocatorParams(c1=0.0, c2=0.0, reserve=0)
        first = allocate(roots, budget=1, params=params).verified
        second = allocate(list(reversed(roots)), budget=1, params=params).verified
        self.assertEqual(first, second)
        expected = min(roots, key=lambda r: tie_break_hash(r.root_id)).root_id
        self.assertEqual(first, [expected])

    def test_all_infeasible(self):
        roots = [_root(f"r{i}", 5.0, feasible1=False) for i in range(4)]
        result = allocate(roots, budget=2, params=AllocatorParams(0.0, 0.0, 0))
        self.assertEqual(result.realized_calls, 0)
        self.assertEqual(set(result.regimes.values()), {"never"})

    def test_no_root_reaches_checkpoint2(self):
        roots = [_root(f"r{i}", 1.0, reached2=False) for i in range(5)]
        params = AllocatorParams(c1=0.0, c2=0.0, reserve=1)
        result = allocate(roots, budget=3, params=params)
        self.assertEqual(result.realized_calls, 2)  # phase 1 up to B - R
        self.assertEqual(result.unspent_calls, 1)
        self.assertNotIn("later", result.regimes.values())

    def test_budget_zero(self):
        roots = [_root(f"r{i}", 1.0) for i in range(4)]
        result = allocate(roots, budget=0, params=AllocatorParams(0.0, 0.0, 0))
        self.assertEqual(result.realized_calls, 0)
        self.assertEqual(result.work, 0.0)

    def test_no_double_verification(self):
        roots = [_root("a", 1.0, s2=1.0), _root("b", 0.5, s2=1.0)]
        params = AllocatorParams(c1=0.0, c2=0.0, reserve=1)
        result = allocate(roots, budget=2, params=params)
        self.assertEqual(len(result.verified), len(set(result.verified)))
        self.assertLessEqual(result.realized_calls, 2)

    def test_early_terminated_never_verified_later(self):
        roots = [_root("a", 0.0, s2=5.0, terminated=True)]
        result = allocate(roots, budget=1, params=AllocatorParams(c1=0.0, c2=0.0, reserve=1))
        self.assertEqual(result.regimes["a"], "never")

    def test_determinism(self):
        roots = [_root(f"r{i}", float(i % 3), s2=float((i + 1) % 3)) for i in range(12)]
        params = AllocatorParams(c1=0.5, c2=0.5, reserve=1)
        a = allocate(roots, budget=3, params=params)
        b = allocate(roots, budget=3, params=params)
        self.assertEqual(a.regimes, b.regimes)
        self.assertEqual(a.verified, b.verified)

    @settings(max_examples=200, deadline=None)
    @given(
        raw=st.lists(
            st.tuples(st.floats(-2, 2, allow_nan=False), st.floats(-2, 2, allow_nan=False),
                      st.booleans(), st.booleans(), st.booleans(), st.booleans()),
            min_size=0, max_size=12,
        ),
        budget=st.integers(0, 6),
        reserve=st.integers(0, 6),
    )
    def test_property_hard_budget(self, raw, budget, reserve):
        roots = [
            _root(f"r{i}", s1, s2, reached2=r2, feasible1=f1, feasible2=f2, terminated=term)
            for i, (s1, s2, f1, f2, r2, term) in enumerate(raw)
        ]
        result = allocate(roots, budget=budget,
                          params=AllocatorParams(c1=0.0, c2=0.0, reserve=reserve))
        self.assertLessEqual(result.realized_calls, budget)
        self.assertEqual(len(result.verified), len(set(result.verified)))
        for root in roots:
            regime = result.regimes[root.root_id]
            self.assertIn(regime, {"now", "later", "never"})
            if not (root.feasible1 and root.s1 > 0.0):
                self.assertNotEqual(regime, "now")
            if regime == "later":
                self.assertTrue(root.reached2 and root.feasible2 and not root.terminated)


class TestBudgetEnforcement(unittest.TestCase):
    """B2: with q given, the allocator enforces B = floor(q * N) itself."""

    def test_matching_budget_accepted(self):
        roots = [AllocatorRoot(root_id=f"r{i}", s1=float(i)) for i in range(8)]
        result = allocate(roots, budget=2, params=AllocatorParams(0.0, 0.0), q=0.25)
        self.assertEqual(result.budget, 2)

    def test_mismatched_budget_refused(self):
        roots = [AllocatorRoot(root_id=f"r{i}", s1=float(i)) for i in range(8)]
        for budget in (1, 3, 8):
            with self.assertRaisesRegex(AllocatorError, "floor"):
                allocate(roots, budget=budget,
                                   params=AllocatorParams(0.0, 0.0), q=0.25)


if __name__ == "__main__":
    unittest.main()
