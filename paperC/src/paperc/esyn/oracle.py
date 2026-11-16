"""Certified oracle gains on E-SYN worlds (build runbook P3, step 5; revised after review round 1), after Track S
``oracle.certify``.

AI-assisted (Claude, chat session, 16 Nov 2026). ENGINEERING_ONLY.

1. **Selection block** (instances ``SELECT_BASE`` + i). The best static rule is found on the static grid, extended
   until it is interior (``families.extend_static_grid``). Then the world's member family is searched by
   coordinate ascent (``families`` docstring), with its grids extended at non-natural edges. The evaluated member
   is the best member that decides differently from the best static on at least one selection campaign.
2. **Reference gain** delta_Y is **declared before evaluation**: the exact DP gain where a DP exists (budget world),
   else the world's ``reference_gain`` (Track S's 0.5 sigma, here 0.5 sigma_cmp). The tolerance is tol x delta_Y,
   an absolute precision as in Track S; the strict null uses the same tolerance. (Round 1 used the selection-block
   gain, which is selection-biased; review P3 finding 2.)
3. **Evaluation block** (``EVAL_BASE`` + i, disjoint). A pilot of ``n_pilot`` paired campaigns gives the sd of
   D = Y_member - Y_static; n = ceil(1.1 (z sd / tol)^2); if the half-width still exceeds the target, n is re-sized
   from all draws so far, at most ``MAX_ROUNDS`` times. ``pass`` means: the 95 % half-width of the evaluated
   member's gain is at most tol x delta_Y and n_max was not reached. The output also gives hw / gain.

**Deviation from Track S:** Track S checked the half-width of every member; this certifies one member (the
selection winner) per world, and the gain is a lower bound on what the family, and any better policy, attains.
"""
from __future__ import annotations

import math

import numpy as np

from paperc.esyn import families as F
from paperc.esyn.extra import ESynWorld
from paperc.esyn.sim import EVAL_BASE, SELECT_BASE, campaign_values

Z95 = 1.959963984540054
SAFETY = 1.1          # margin on the pilot-based size
MAX_ROUNDS = 3        # resizing rounds after the pilot (each from the sd of all draws so far)
MAX_EXTEND = 6        # grid extensions per search step
ORACLE_SCHEMA = "paperc_esyn_oracle/v2"


class OracleToleranceError(RuntimeError):
    pass


class _Sel:
    """Selection-block values, cached by policy name."""

    def __init__(self, world: ESynWorld, n: int):
        self.world, self.inst, self.v = world, range(SELECT_BASE, SELECT_BASE + n), {}

    def __call__(self, pol) -> np.ndarray:
        if pol.name not in self.v:
            self.v[pol.name] = campaign_values(self.world, pol, self.inst)
        return self.v[pol.name]

    def mean(self, pol) -> float:
        return float(self(pol).mean())


def search_static(sel: _Sel, g_grid=F.G0, h_grid=F.H0):
    g, h = list(g_grid), list(h_grid)
    for _ in range(MAX_EXTEND + 1):
        cands = F.statics(g, h)
        best = max(cands, key=sel.mean)
        g, h, ext = F.extend_static_grid(g, h, best)
        if not ext:
            break
    return best, g, h


def search_members(sel: _Sel, fam: F.Family, best_static, g_grid: list, h_grid: list):
    """Coordinate ascent over (channel parameter, (g, h)); returns the evaluated member, all members, facts."""
    base = sel(best_static)
    distinct = lambda p: bool(np.any(sel(p) != base))            # noqa: E731
    members: dict[str, object] = {}

    def ev(p):
        members[p.name] = p
        return sel.mean(p)

    if fam.kind == "schedule":
        return _search_schedule(sel, fam, best_static, g_grid, h_grid, distinct, ev, members)
    if not fam.search_gh:
        for prm in fam.params:
            ev(fam.build(None, None, prm))
        elig = [p for p in members.values() if distinct(p)]
        best = max(elig, key=sel.mean) if elig else None
        return best, members, {"param": None, "param_interior": True, "gh_interior": True, "rounds": 0}
    g, h = best_static.g, best_static.h
    params = list(fam.params)
    best_prm, gh_interior, prm_interior, rounds = None, True, True, 0
    for rounds in range(1, 5):
        # A: channel parameter at (g, h), extended at non-natural edges
        for _ in range(MAX_EXTEND + 1):
            for prm in params:
                ev(fam.build(g, h, prm))
            ok = [prm for prm in params if distinct(fam.build(g, h, prm))]
            if not ok:
                break
            best_prm = max(ok, key=lambda prm: sel.mean(fam.build(g, h, prm)))
            new = [x for x in fam.extend(params, best_prm) if x not in params]
            if not new:
                break
            params += new
        if best_prm is None:
            break
        prm_interior = not [x for x in fam.extend(params, best_prm) if x not in params]
        # B: (g, h) neighbourhood at the best parameter, grids extended at their edges
        start = (g, h)
        for _ in range(MAX_EXTEND + 1):
            cand = [(gg, hh) for gg in F.near(g_grid, g) for hh in F.near(h_grid, h)]
            for gg, hh in cand:
                ev(fam.build(gg, hh, best_prm))
            g, h = max(cand, key=lambda x: sel.mean(fam.build(x[0], x[1], best_prm)))
            g_grid, h_grid, ext = F.extend_static_grid(g_grid, h_grid, type(best_static)(g, h))
            if not ext:
                break
        gh_interior = F.static_interior(g_grid, h_grid, type(best_static)(g, h))
        if (g, h) == start:
            break
    elig = [p for p in members.values() if distinct(p)]
    best = max(elig, key=sel.mean) if elig else None
    return best, members, {"param": repr(best_prm), "param_interior": prm_interior, "gh_interior": gh_interior,
                           "rounds": rounds, "params_searched": [repr(x) for x in params]}


def _search_schedule(sel, fam, best_static, g_grid, h_grid, distinct, ev, members):
    """Coordinate descent over the 9 thresholds of ``policies.Schedule``, from the best static."""
    from paperc.esyn import policies as P
    tau_split = fam.params[0]
    gs, hs = [best_static.g] * 6, [best_static.h] * 3
    cur = P.Schedule(tuple(gs), tuple(hs), tau_split)
    best_v = ev(cur)
    passes = 0
    for passes in range(1, 4):
        improved = False
        for i in range(9):
            for _ in range(MAX_EXTEND + 1):
                grid = g_grid if i < 6 else h_grid
                for x in grid:
                    trial_g, trial_h = list(cur.gs), list(cur.hs)
                    if i < 6:
                        trial_g[i] = x
                    else:
                        trial_h[i - 6] = x
                    p = P.Schedule(tuple(trial_g), tuple(trial_h), tau_split)
                    v = ev(p)
                    if v > best_v + 1e-15:
                        cur, best_v, improved = p, v, True
                x_best = cur.gs[i] if i < 6 else cur.hs[i - 6]
                probe = type(best_static)(x_best if i < 6 else g_grid[1], x_best if i >= 6 else h_grid[1])
                g_grid, h_grid, ext = F.extend_static_grid(g_grid, h_grid, probe)
                if not ext:
                    break
        if not improved:
            break
    edge = lambda x, grid, natural_low=False: (x == grid[-1]) or (x == grid[0] and not natural_low)   # noqa: E731
    interior = not any(edge(x, g_grid, x <= F.G_NATURAL_LOW) for x in cur.gs) and not any(edge(x, h_grid)
                                                                                          for x in cur.hs)
    elig = [p for p in members.values() if distinct(p)]
    best = max(elig, key=sel.mean) if elig else None
    return best, members, {"param": f"tau_split={tau_split}", "param_interior": True, "gh_interior": interior,
                           "rounds": passes}


def certify(world: ESynWorld, family: F.Family | list | None = None, *, delta_Y: float | None = None, tol: float = 0.05,
            n_select: int = 2000, n_pilot: int = 1000, n_max: int = 400_000, strict: bool = True,
            statics: list | None = None, members: list | None = None) -> dict:
    """Certify the oracle gain of ``world`` (see the module docstring). ``statics`` / ``members`` (explicit lists)
    replace the grid search, for small tests."""
    if n_select > EVAL_BASE - SELECT_BASE or n_max > EVAL_BASE - SELECT_BASE:
        raise ValueError("blocks hold 10^6 instances each")
    sel = _Sel(world, n_select)
    if statics is not None:
        best_static, g_grid, h_grid = max(statics, key=sel.mean), [], []
        static_ok = True
    else:
        best_static, g_grid, h_grid = search_static(sel)
        static_ok = F.static_interior(g_grid, h_grid, best_static)
    if members is not None:
        base = sel(best_static)
        elig = [p for p in members if np.any(sel(p) != base)]
        best_member = max(elig, key=sel.mean) if elig else None
        facts = {"param": None, "param_interior": True, "gh_interior": True, "rounds": 0}
        evaluated = {p.name: p for p in members}
    else:
        fams = family if isinstance(family, list) else ([family] if family is not None else F.families(world))
        found = [(fam.name,) + search_members(sel, fam, best_static, list(g_grid), list(h_grid)) for fam in fams]
        evaluated = {k: p for _, _, mem, _ in found for k, p in mem.items()}
        hits = [(name, b, fct) for name, b, _, fct in found if b is not None]
        best_name, best_member, facts = max(hits, key=lambda x: sel.mean(x[1])) if hits else (None, None, {})
        facts = {**facts, "family": best_name,
                 "families": {name: {"best": b.name if b is not None else None,
                                     "gain": (sel.mean(b) - sel.mean(best_static)) if b is not None else None,
                                     **{k: fct[k] for k in ("param_interior", "gh_interior")}}
                              for name, b, _, fct in found}}
    if best_member is None:
        raise ValueError(f"{world.name}: no member decides differently from the best static")
    ref = float(delta_Y) if delta_Y is not None else world.reference_gain
    ref_source = "declared (DP gain)" if delta_Y is not None else "declared (0.5 sigma_cmp)"
    target = tol * abs(ref)
    sel_gain = sel.mean(best_member) - sel.mean(best_static)
    dsel = sel(best_member) - sel(best_static)

    def ys(policy, n0, n1):
        return campaign_values(world, policy, range(EVAL_BASE + n0, EVAL_BASE + n1))

    base = ys(best_static, 0, n_pilot)
    mem = ys(best_member, 0, n_pilot)
    n, capped, rounds = n_pilot, False, 0
    while True:
        dlt = mem - base
        sd = float(np.std(dlt, ddof=1))
        hw = Z95 * sd / math.sqrt(n)
        if hw <= target or rounds == MAX_ROUNDS:
            break
        n_need = math.ceil(SAFETY * (Z95 * sd / target) ** 2)
        if n_need <= n:
            n_need = n + n_pilot
        capped = n_need > n_max
        n_new = min(n_need, n_max)
        if n_new <= n:
            break
        base = np.concatenate([base, ys(best_static, n, n_new)])
        mem = np.concatenate([mem, ys(best_member, n, n_new)])
        n, rounds = n_new, rounds + 1
    gain = float(dlt.mean())
    out = {
        "schema": ORACLE_SCHEMA, "label": "ENGINEERING_ONLY", "world": world.name, "channel": world.channel,
        "gain_sign_declared": world.gain_sign, "W": world.W, "llm_cap": world.llm_cap,
        "selection": {"instances": [SELECT_BASE, SELECT_BASE + n_select], "best_static": best_static.name,
                      "best_static_value": sel.mean(best_static), "static_grid": {"g": g_grid, "h": h_grid},
                      "static_interior": static_ok, "best_member": best_member.name,
                      "best_member_value": sel.mean(best_member), "gain": sel_gain,
                      "gain_se": float(np.std(dsel, ddof=1) / math.sqrt(n_select)),
                      "n_members": len(evaluated), "member_search": facts},
        "reference_gain": ref, "reference_source": ref_source, "tolerance": target,
        "evaluation": {"instances": [EVAL_BASE, EVAL_BASE + n], "n": n, "resizing_rounds": rounds,
                       "static_value": float(base.mean()), "member_value": float(mem.mean()),
                       "static_sd": float(np.std(base, ddof=1)), "member_sd": float(np.std(mem, ddof=1))},
        "gain": gain, "half_width": hw, "hw_over_gain": (hw / abs(gain)) if gain else None,
        "pass": (not capped) and hw <= target,
    }
    if strict and not out["pass"]:
        raise OracleToleranceError(f"{world.name}: half-width {hw:.3g} vs tolerance {target:.3g} at n = {n}"
                                   + (" (n_max reached)" if capped else ""))
    return out
