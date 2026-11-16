"""Policy grids for the E-SYN oracle (build runbook P3, step 5; revised after review round 1).

AI-assisted (Claude, chat session, 16 Nov 2026). ENGINEERING_ONLY.

**Static grid** (Paper B's rule class: E1 threshold g on V*, E2 threshold h on m_hat): starts at ``G0`` x ``H0``
and is **extended** by ``oracle.certify`` whenever the best static lies on an edge that is not a natural bound, until
it is interior (review P3 finding 1). g = 0 is a natural lower bound, because V* > 0 (every g <= 0 executes
every proposal); h has no natural bound.

**Member families** (``Family``): a world's channel parameter (a scalar or a discrete option) crossed with the static
thresholds (g, h). ``certify`` searches them by coordinate ascent on the selection block: the channel parameter at
the current (g, h), extended at non-natural edges, then the (g, h) neighbourhood (one grid step each way, the
static grid extended at its edges) at the best parameter, repeated until (g, h) stops moving. Members that make
exactly the best static's decisions on every selection campaign are not eligible as the evaluated member.

* strict_null: ``Dynamic`` with a tau bonus, a budget-dependent keep threshold or a key-novelty bonus (no
  extension: the null has no channel to find), and the ``Schedule``. In the null the exact DP already dominates
  every schedule, so the schedule adds no falsification power; the null result rests on the exact DP and on the
  ``Dynamic`` family's evaluation (``table.null_family_eval``);
* budget: the exact DP policy only (no search);
* interaction: ``InteractionAware`` beta (scalar; halved / doubled at the edges); privileged (knows M);
* shared_error: re-audit count k in {2, ..., max_obs} (natural bounds);
* eval_allocation: (verify band, verify max, re-audit max, final rule), band halved / doubled at its edges;
* information: a 9-threshold ``Schedule`` after Track S's (E1 threshold by budget third x tau half, E2 threshold by
  budget third; budget position = runs used / W; fixed tau split 0.02, which separates P1's size-16 follow-ups),
  searched by coordinate descent from the best static over the static grid values, grids extended at their edges.
  Its gain comes almost entirely from the budget-third dependence (review P3 round 2: about +0.0060 without the tau
  split, +0.0001 with the tau split alone). Round 1's key-novelty member still gains about +0.0010 over the same
  best static (review round 2, 100,000 fresh campaigns); the schedule replaced it because its gain is about six
  times larger.
* keep_feedback: ``Dynamic`` b_keep (scalar; halved / doubled) and the ``Schedule`` (Track S's schedule found a
  larger keep-feedback gain than a single budget term).

Gains found this way are **lower bounds** on the attainable gain (the best member of a small family), except in
the budget world, where the member is the exact optimum. The static grid is extended at its edges with doubling
spacing but never refined near the optimum, so the baseline can be slightly below the best static rule: in
information a finer grid beats the selected static by 0.00022 +- 0.00008 (review round 2), a bias of a few percent
on that gain. A refinement pass is an open item before P4 uses these gains as oracle references.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from typing import Callable

from paperc.esyn import dp
from paperc.esyn import policies as P
from paperc.esyn.extra import ESynWorld

G0 = (0.0, 0.0005, 0.001, 0.0015, 0.002, 0.003)
H0 = (-0.003, -0.002, -0.001, 0.0, 0.001)
G_NATURAL_LOW = 0.0


def statics(g_grid, h_grid) -> list:
    return [P.Static(g, h) for g, h in product(g_grid, h_grid)]


def extend_static_grid(g_grid: list, h_grid: list, best: P.Static) -> tuple[list, list, bool]:
    """Extend the grids beyond any non-natural edge the best static sits on (spacing doubles outward)."""
    g, h, ext = list(g_grid), list(h_grid), False
    if best.g == g[-1]:
        g.append(round(g[-1] + 2 * (g[-1] - g[-2]), 10))
        ext = True
    if best.g == g[0] and g[0] > G_NATURAL_LOW:
        g.insert(0, max(G_NATURAL_LOW, round(g[0] - 2 * (g[1] - g[0]), 10)))
        ext = True
    if best.h == h[0]:
        h.insert(0, round(h[0] - 2 * (h[1] - h[0]), 10))
        ext = True
    if best.h == h[-1]:
        h.append(round(h[-1] + 2 * (h[-1] - h[-2]), 10))
        ext = True
    return g, h, ext


def static_interior(g_grid, h_grid, best: P.Static) -> bool:
    g_ok = best.g != g_grid[-1] and (best.g != g_grid[0] or best.g <= G_NATURAL_LOW)
    h_ok = best.h not in (h_grid[0], h_grid[-1])
    return g_ok and h_ok


def near(grid: list, x: float) -> list:
    i = grid.index(x)
    return grid[max(i - 1, 0): i + 2]


@dataclass
class Family:
    name: str
    build: Callable                       # (g, h, param) -> policy
    params: list                          # initial channel parameters (scalars or option tuples)
    extend: Callable[[list, object], list] = field(default=lambda params, best: [])   # new params at an edge
    search_gh: bool = True                # False: no (g, h) search (the DP member)
    kind: str = "grid"                    # "schedule": coordinate descent over the 9 thresholds of ``Schedule``


def _scalar_extend(floor: float | None = None):
    def ext(params, best):
        vals = sorted(params)
        if best == vals[0]:
            x = vals[0] / 2
            return [] if floor is not None and x < floor else [x]
        if best == vals[-1]:
            return [vals[-1] * 2]
        return []
    return ext


def _evalloc_extend(params, best):
    if best[1] == 1:
        return []
    bands = sorted({p[0] for p in params if p[1] > 1})
    if best[0] == bands[-1]:
        nb = bands[-1] * 2
    elif best[0] == bands[0]:
        nb = bands[0] / 2
    else:
        return []
    rest = sorted({(p[1], p[2], p[3]) for p in params if p[1] > 1})
    return [(nb, v, r, f) for (v, r, f) in rest]


SCHEDULE = Family("schedule", None, [0.02], kind="schedule")


def families(world: ESynWorld) -> list[Family]:
    """All member families searched for ``world``; the oracle takes the best eligible member across them."""
    if world.channel in ("none", "keep_feedback"):
        return [family(world), SCHEDULE]
    return [family(world)]


def family(world: ESynWorld) -> Family:
    c = world.channel
    if c == "budget":
        table = dp.solve(world).table
        return Family("dp", lambda g, h, p: P.Threshold(table), [None], search_gh=False)
    if c == "none":
        return Family("dynamic_null", lambda g, h, p: P.Dynamic(g, h, p[0], 0.004, p[1], p[2], 0.02),
                      [(0.1, 0.0, 0.0), (0.0, 0.002, 0.0), (0.0, 0.0, 0.01)])
    if c == "interaction":
        return Family("interaction_beta", lambda g, h, b: P.InteractionAware(g, h, b), [0.25, 0.5, 1.0],
                      _scalar_extend(floor=0.01))
    if c == "shared_error":
        return Family("reaudit_k", lambda g, h, k: P.EvalAlloc(g, h, 0.0, 1, k, "incumbent"),
                      list(range(2, world.max_obs + 1)))
    if c == "eval_allocation":
        mx = world.max_obs
        opts = [(band, v, r, f) for band, v, r, f in product((0.5, 1.0, 2.0, 4.0), range(2, mx + 1),
                                                             range(1, mx + 1), ("incumbent", "best"))]
        opts += [(1.0, 1, r, f) for r, f in product(range(2, mx + 1), ("incumbent", "best"))]
        return Family("evalloc", lambda g, h, o: P.EvalAlloc(g, h, *o), opts, _evalloc_extend)
    if c == "information":
        return SCHEDULE
    if c == "keep_feedback":
        return Family("keep_budget", lambda g, h, b: P.Dynamic(g, h, 0.0, 0.0, b), [0.002, 0.004, 0.008],
                      _scalar_extend(floor=0.0005))
    raise ValueError(c)
