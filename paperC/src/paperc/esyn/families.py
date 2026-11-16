"""Policy grids for the E-SYN oracle (build runbook P3, step 5): the static baseline grid and each world's member
family. AI-assisted (Claude, chat session, 16 Nov 2026). ENGINEERING_ONLY.

The static grid is Paper B's rule class (E1 threshold g on V*, E2 threshold h on m_hat). A world's members are
the channel's parameters (never all zero, so no member equals a static rule) crossed with the static thresholds
in the grid neighbourhood of the best static rule (one grid step either way in g and in h); ``certify`` builds
them after choosing the best static on the selection block. The budget world's member is the exact DP policy.
The strict null gets the ``Dynamic`` rules whose inputs exist there (tau bonus, budget-dependent keep threshold,
key novelty), so a positive null gain would expose a simulator or oracle error; its DP collapses exactly to the
static rule (g = 0), which ``test_esyn_p3`` checks by exact computation rather than by simulation.
"""
from __future__ import annotations

from itertools import product

from paperc.esyn import dp
from paperc.esyn import policies as P
from paperc.esyn.extra import ESynWorld

G_GRID = (0.0, 0.0005, 0.001, 0.0015, 0.002, 0.003)
H_GRID = (-0.003, -0.002, -0.001, 0.0, 0.001)


def statics(world: ESynWorld) -> list:
    return [P.Static(g, h) for g, h in product(G_GRID, H_GRID)]


def _near(grid: tuple, x: float) -> tuple:
    i = grid.index(x)
    return grid[max(i - 1, 0): i + 2]


def members(world: ESynWorld, best: P.Static) -> list:
    c = world.channel
    gh = list(product(_near(G_GRID, best.g), _near(H_GRID, best.h)))
    if c == "budget":
        return [P.Threshold(dp.solve(world).table)]
    if c == "none":
        out = [P.Dynamic(g, h, b_info, 0.004, b_keep, b_novel)
                for (g, h), (b_info, b_keep, b_novel) in product(gh, ((0.1, 0.0, 0.0), (0.0, 0.002, 0.0),
                                                                     (0.0, 0.0, 0.001)))]
        return out
    if c == "interaction":
        return [P.InteractionAware(g, h, beta) for (g, h), beta in product(gh, (0.25, 0.5, 1.0))]
    if c == "shared_error":
        return [P.EvalAlloc(g, h, 0.0, 1, k, "incumbent") for (g, h), k in product(gh, (2, 3))]
    if c == "eval_allocation":
        opts = [(band, vmax, rmax, fin) for band, vmax, rmax, fin in product((1.0, 2.0), (1, 2), (1, 2, 3),
                                                                            ("incumbent", "best"))
                if not (vmax == 1 and band != 1.0) and not (vmax == 1 and rmax == 1)]
        return [P.EvalAlloc(g, h, *o) for (g, h), o in product(gh, opts)]
    if c == "information":
        return [P.Dynamic(g, h, 0.0, 0.0, 0.0, b_novel, tau_cut)
                for (g, h), b_novel, tau_cut in product(gh, (0.001, 0.002, 0.004, 0.008), (0.01, 0.02))]
    if c == "keep_feedback":
        return [P.Dynamic(g, h, 0.0, 0.0, b_keep) for (g, h), b_keep in product(gh, (0.001, 0.002, 0.004, 0.008))]
    raise ValueError(c)
