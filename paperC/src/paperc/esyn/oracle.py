"""Certified oracle gains on E-SYN worlds (build runbook P3, step 5), after Track S ``oracle.certify``.

AI-assisted (Claude, chat session, 16 Nov 2026). ENGINEERING_ONLY.

1. On a **selection block** (instances ``SELECT_BASE`` + i), choose the best static rule (the baseline) and then
   the best member of the world's policy family (which may be built around that static), by mean campaign value Y
   (exact final value, no audit noise).
2. The **planted gain** delta_Y is the declared one when given (the budget world's exact DP gain), else the
   selection-block gain of the chosen member. The strict null (and a channel world without a positive selection
   gain) uses ``floor`` instead (default: the world's sigma_cmp), i.e. an absolute tolerance.
3. On a disjoint **evaluation block** (``EVAL_BASE`` + i), a pilot of ``n_pilot`` paired campaigns gives the sd of
   D = Y_member - Y_static; n = ceil(1.1 (z sd / (tol delta_Y))^2); if the half-width still exceeds the target,
   n is re-sized from the sd of all draws so far, at most ``MAX_ROUNDS`` times. The call fails
   (``OracleToleranceError`` when ``strict``) if n would exceed ``n_max`` or the final 95 % half-width exceeds
   tol x delta_Y.

Both blocks are disjoint from the recorded campaigns (instances 0 .. 9999) and from each other; they only enter
the RNG key ``[60001, world code, instance]`` (Paper C block ``paperc_rng_keys``).
"""
from __future__ import annotations

import math

import numpy as np

from paperc.esyn.extra import ESynWorld
from paperc.esyn.sim import EVAL_BASE, SELECT_BASE, campaign_values

Z95 = 1.959963984540054
SAFETY = 1.1          # margin on the pilot-based size
MAX_ROUNDS = 3        # resizing rounds after the pilot (each from the sd of all draws so far)
ORACLE_SCHEMA = "paperc_esyn_oracle/v1"


class OracleToleranceError(RuntimeError):
    pass


def certify(world: ESynWorld, statics: list, members, *, delta_Y: float | None = None, tol: float = 0.05,
            n_select: int = 2000, n_pilot: int = 1000, n_max: int = 400_000, floor: float | None = None,
            strict: bool = True) -> dict:
    if n_select > EVAL_BASE - SELECT_BASE or n_max > EVAL_BASE - SELECT_BASE:
        raise ValueError("blocks hold 10^6 instances each")
    sel = range(SELECT_BASE, SELECT_BASE + n_select)
    sel_vals = {p.name: campaign_values(world, p, sel) for p in statics}
    best_static = max(statics, key=lambda p: sel_vals[p.name].mean())
    if callable(members):                     # a family built around the best static (``families.members``)
        members = members(best_static)
    sel_vals.update({p.name: campaign_values(world, p, sel) for p in members})
    best_member = max(members, key=lambda p: sel_vals[p.name].mean())
    sel_gain = float(sel_vals[best_member.name].mean() - sel_vals[best_static.name].mean())
    b0 = sel_vals[best_static.name]
    distinct = [m for m in members if np.any(sel_vals[m.name] != b0)]     # members that ever decide differently
    bd = max(distinct, key=lambda p: sel_vals[p.name].mean()) if distinct else None
    dd = sel_vals[bd.name] - b0 if bd is not None else None
    floor = world.base.sigma_cmp if floor is None else floor
    if delta_Y is not None:
        planted, planted_source = float(delta_Y), "declared"
    elif world.gain_sign == 0:
        planted, planted_source = floor, "floor"                      # strict null: absolute tolerance
    elif sel_gain > 0:
        planted, planted_source = sel_gain, "selection"
    else:
        planted, planted_source = floor, "floor (no positive selection gain)"
    target = tol * abs(planted)

    def ys(policy, n0, n1):
        return campaign_values(world, policy, range(EVAL_BASE + n0, EVAL_BASE + n1))

    base = ys(best_static, 0, n_pilot)
    mem = ys(best_member, 0, n_pilot)
    n, capped, rounds = n_pilot, False, 0
    while True:
        dlt = mem - base
        sd = float(np.std(dlt, ddof=1))
        hw = Z95 * sd / math.sqrt(n) if n > 1 else math.inf
        if hw <= target or rounds == MAX_ROUNDS:
            break
        n_need = math.ceil(SAFETY * (Z95 * sd / target) ** 2) if target > 0 else n_max + 1
        if n_need <= n:
            n_need = n + n_pilot
        capped = n_need > n_max
        n_new = min(n_need, n_max)
        if n_new <= n:
            break
        base = np.concatenate([base, ys(best_static, n, n_new)])
        mem = np.concatenate([mem, ys(best_member, n, n_new)])
        n, rounds = n_new, rounds + 1
    out = {
        "schema": ORACLE_SCHEMA, "label": "ENGINEERING_ONLY", "world": world.name, "channel": world.channel,
        "gain_sign_declared": world.gain_sign, "W": world.W, "llm_cap": world.llm_cap,
        "selection": {"instances": [SELECT_BASE, SELECT_BASE + n_select],
                      "values": {k: float(v.mean()) for k, v in sel_vals.items()},
                      "best_static": best_static.name, "best_member": best_member.name, "gain": sel_gain,
                      "n_members": len(members), "n_distinct": len(distinct),
                      "best_distinct": bd.name if bd is not None else None,
                      "best_distinct_gain": float(dd.mean()) if dd is not None else None,
                      "best_distinct_se": float(np.std(dd, ddof=1) / math.sqrt(len(dd))) if dd is not None else None},
        "planted_gain": planted, "planted_source": planted_source, "tolerance": target,
        "evaluation": {"instances": [EVAL_BASE, EVAL_BASE + n], "n": n, "resizing_rounds": rounds,
                       "static_value": float(base.mean()), "member_value": float(mem.mean())},
        "gain": float(dlt.mean()), "half_width": hw,
        "pass": (not capped) and hw <= target,
    }
    if strict and not out["pass"]:
        raise OracleToleranceError(f"{world.name}: half-width {hw:.3g} vs tolerance {target:.3g} at n = {n}"
                                   + (" (n_max reached)" if capped else ""))
    return out
