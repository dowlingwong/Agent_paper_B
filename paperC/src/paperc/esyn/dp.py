"""Exact dynamic programme for the E-SYN budget world (build runbook P3, step 4).

AI-assisted (Claude, chat session, 16 Nov 2026). ENGINEERING_ONLY.

Applies to worlds whose decision state is finite: fresh keys (so the key posterior is always the prior), Track S
kind N0 without trend, a discrete size law, independent comparisons (``comparison='increment'``), epochs E1 / E2
only, and no per-instance rule-share spread. Then a non-rule proposal of size s has the forecast
a_s = s mu0, A_s = s^2 tau0^2 + sigma_eta^2, and executing it followed by the Bayes keep (m_hat > 0) gains
V*_s = E[max(m_hat, 0)] in expectation (the model is correct, so E[delta 1{m_hat > 0}] = E[m_hat 1{m_hat > 0}]).

State at slot t (t = 2 .. llm_cap): w runs left. Slot 1 is never rule-detectable and is executed and kept
(expected gain sum_s pi_s a_s). With rule share p:

    V_{N+1}(w) = 0,  V_t(0) = 0,
    V_t(w) = p V_{t+1}(w) + (1 - p) sum_s pi_s max(V*_s + V_{t+1}(w - 1), V_{t+1}(w)),

and the optimal E1 rule executes iff V*_s >= V_{t+1}(w) - V_{t+1}(w - 1) (ties execute, as the simulator's ">=").
The value of the campaign, E[Y], is sum_s pi_s a_s + V_2(W - 1). ``static_value`` evaluates a constant threshold
g by the same recursion.
"""
from __future__ import annotations

from dataclasses import dataclass

from paperc.esyn import worlds as WD
from paperc.esyn.extra import ESynWorld


@dataclass(frozen=True)
class SizeLaw:
    probs: tuple[float, ...]
    a: tuple[float, ...]          # prior mean increment per size
    v: tuple[float, ...]          # V* per size


def applicable(world: ESynWorld) -> list[str]:
    b = world.base
    why = []
    if b.kind != "N0" or b.n_keys != 0:
        why.append("needs kind N0 with fresh keys")
    if not world.sizes:
        why.append("needs a discrete size law")
    if world.comparison != "increment" or set(world.epochs) != {"E1", "E2"}:
        why.append("needs independent comparisons and epochs E1 / E2 only")
    if b.inst_prule_spread or b.inst_busy_p or b.trend_shape:
        why.append("needs a constant rule share and no trend")
    return why


def size_law(world: ESynWorld) -> SizeLaw:
    why = applicable(world)
    if why:
        raise ValueError(f"DP not applicable to {world.name}: {why}")
    b = world.base
    a, v = [], []
    for s in world.sizes:
        aa, AA = WD.key_forecast((b.mu0, b.tau0 ** 2), s, 0.0, b.sigma_eta)
        a.append(aa)
        v.append(WD.v_star(aa, AA, b.sig("filler")))
    return SizeLaw(tuple(world.size_probs), tuple(a), tuple(v))


@dataclass
class DPResult:
    value: float                              # E[Y] under the optimal policy
    table: dict[tuple[int, int], float]       # (slots_left, runs_left) at an E1 row -> execute threshold on V*
    V: dict[tuple[int, int], float]           # (t, w) -> value-to-go from slot t with w runs left


def solve(world: ESynWorld) -> DPResult:
    law = size_law(world)
    N, W, p = world.llm_cap, world.W, world.regime.p_rule
    V: dict[tuple[int, int], float] = {(N + 1, w): 0.0 for w in range(W + 1)}
    table: dict[tuple[int, int], float] = {}
    for t in range(N, 1, -1):
        V[(t, 0)] = 0.0
        for w in range(1, W + 1):
            thr = V[(t + 1, w)] - V[(t + 1, w - 1)]
            table[(N - t + 1, w)] = thr
            cont = sum(q * max(v + V[(t + 1, w - 1)], V[(t + 1, w)]) for q, v in zip(law.probs, law.v))
            V[(t, w)] = p * V[(t + 1, w)] + (1.0 - p) * cont
    value = sum(q * a for q, a in zip(law.probs, law.a)) + V[(2, W - 1)]
    return DPResult(value=value, table=table, V=V)


def static_value(world: ESynWorld, g: float) -> float:
    """E[Y] of the static rule 'execute iff V* >= g, keep iff m_hat > 0' (exact, by the same recursion)."""
    law = size_law(world)
    N, W, p = world.llm_cap, world.W, world.regime.p_rule
    nxt = [0.0] * (W + 1)
    for t in range(N, 1, -1):
        cur = [0.0] * (W + 1)
        for w in range(1, W + 1):
            cont = sum(q * ((v + nxt[w - 1]) if v >= g else nxt[w]) for q, v in zip(law.probs, law.v))
            cur[w] = p * nxt[w] + (1.0 - p) * cont
        nxt = cur
    return sum(q * a for q, a in zip(law.probs, law.a)) + nxt[W - 1]
