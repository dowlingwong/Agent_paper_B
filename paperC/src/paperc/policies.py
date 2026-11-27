"""Policy interface and the non-RL ladder (build runbook P4; plan §7.0–§7.1) with B18's sequential-testing
comparators (reframe §3). Revised after review round 1.

AI-assisted (Claude, chat session, 16 Nov 2026). ENGINEERING_ONLY.

**Interface** (``Policy``; amendment of the runbook's ``act(state, rng) -> (action, prob)``, recorded in
BUILD_RUNBOOK P4): ``name``, ``version``, ``stochastic`` and ``act(obs) -> (action, probability, selected)``. ``obs``
is the decision-time view of a ``spt_transition/v1`` state (``paperc.esyn.sim.obs_from_state``); ``selected`` names
the configuration on ``final`` rows. Instead of an ``rng`` object, a stochastic policy reads ``obs["u"]``, a
uniform keyed by the row's logged ``eps_seed``, the world, the campaign and the step (``sim.decision_uniform``), so
``check_campaign`` can replay it from the record. Policies whose parameters do not fit in their name expose ``sha``,
logged as ``policy_sha``.

**One belief for every arm** (plan §7.0). Every rung reads the same forecasts (the world's A2-U keyed belief computed
by the simulator: V*, tau, m_hat) and decision-time features that are not forecaster inputs (budget position,
slots, keeps). No rung's **keep decision** reads the raw observed increment, which would let it refit the belief's
shrinkage; the one exception is N0, Paper B's default rule (keep iff the observed increment is positive), the
declared floor. SPRT and racing read the mean increment at the **verify** epoch, as their test statistic; their keep
decision uses m_hat. Two reference rows measure belief refits: ``ShrinkRefit`` (a static rule keeping on
a + min(lambda k, 1) (delta_hat - a), lambda tuned: lambda = 1 is the belief's m_hat, a large lambda the raw
increment) and its no-shrinkage corner ``RawKeep``.

**Ladder** (plan §7.1):

* N0: execute every eligible proposal; keep iff the observed increment is positive;
* N1: static thresholds (g, h) on the common belief;
* N2: the myopic one-step rule (keep iff m_hat > 0), g tuned;
* N2b: single-step learned heads on belief outputs only: E2 keep by a cost-sensitive logistic head on [1, m_hat]
  (label: true increment > 0, weight |increment|); E1 by a least-squares head on [1, V*, tau] predicting the
  immediate kept gain under that E2 head, with its cut tuned on dev. No budget features: with them, a cut tuned on
  terminal value turns the head into a budget rule whose slope is set by single-step labels (P4 review R2-1);
* N3: Track S's dynamic family (``r1/tracks/a2u.py`` @ ``fab88fc``): E1 execute iff
  V* + b_info (tau - tau_bar) >= g0 - b_budget (r - r1_bar); E2 keep iff m_hat > h0 - h_budget (r - r2_bar), with
  r = runs_left / W - proposals_left / llm_cap and Track S's centring: r1_bar and tau_bar are the mean r and tau of
  the eligible E1 dev decisions, and r2_bar the mean r of the eligible E2 dev decisions, of the reference static
  rule (Track S: its tuned static m*; here the best coarse static, the common start of every tuned rung);
* N4: the budget DP (stochastic knapsack) on the V* law, rule share and first-trial gain estimated from dev
  campaigns (``LawDP``; keep iff m_hat > 0);
* references: the P3 oracle member; ``RandomExec`` (execute with probability q, keep with the matched rung's h),
  q calibrated on the test block to the matched rung's mean runs (run counts are not outcomes); ``ShrinkRefit`` and
  ``RawKeep``; the exact DP where it applies.

**B18 comparators** (worlds with a verify epoch): ``SPRT`` (verify while the log-likelihood ratio of +delta against
-delta for the mean increment lies between +-log((1 - alpha) / alpha)), ``Race`` (verify while the z-interval of
the mean increment contains h), ``KGVerify`` (verify iff the one-step knowledge gradient is at least c); all keep
iff m_hat > h. ``BudgetMargin`` (keep iff m_hat > h0 + c x runs used / W) applies everywhere. Not implemented: OCBA
(for one candidate against one incumbent it allocates between the two; its natural use here would be the final
selection) and a re-audit comparator.

**Tuning** (plan §7.0: a declared, equal budget). Every tuned rung (N1, N2, N3, margin, B18, ``RawKeep``) gets at
most ``TUNE_BUDGET`` candidate policies, counted per rung, each on the same ``N_DEV`` dev campaigns (instances
``DEV_BASE`` + i): first the same coarse grid of static rules (charged to every rung; N2 only its h = 0 column),
then coordinate search over the rung's own parameters from the best coarse static, until the budget is spent or the
steps vanish. A move is accepted only if its paired dev improvement exceeds one standard error (this does not stop
every noise move: in the strict null N1 and N3 still move off the Bayes rule; P4 review R2-3). Dev values are
shared across rungs as a cache; the charge is per rung. N2b's head fits and N4's law use the same dev campaigns and
are recorded as dev fits. Test campaigns (``TEST_BASE`` + i) are never used for tuning.
"""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from itertools import product
from statistics import NormalDist
from typing import Callable, Protocol

import numpy as np
from scipy.optimize import minimize

from paperc.esyn import dp, sim
from paperc.esyn import policies as EP
from paperc.esyn.extra import ESynWorld

VERSION = "p4/v2"
DEV_BASE = 4_000_000
TEST_BASE = 5_000_000
N_DEV = 1000
TUNE_BUDGET = 80
COARSE_G = (0.0, 0.0005, 0.001, 0.0015, 0.002, 0.003)
COARSE_H = (-0.004, -0.002, -0.001, 0.0, 0.001)
_N = NormalDist()


class Policy(Protocol):
    name: str
    version: str

    def act(self, obs: dict) -> tuple[str, float, str | None]:
        """(action, probability of that action, selected hash on final rows); see the module docstring."""


def _rest(obs, g, h):
    return EP._myopic(obs, g, h)


def _sha(*parts) -> str:
    return hashlib.sha256(repr(parts).encode()).hexdigest()[:16]


def budget_position(obs) -> float:
    """Track S's r = runs_left / W - proposals_left / llm_cap (the current proposal counts as left at E2)."""
    left = obs["slots_left"] if obs["epoch"] == "E1" else obs["slots_left"] + 1
    return obs["runs_left"] / obs["W"] - left / obs["llm_cap"]


# ---------------------------------------------------------------- rungs and references

@dataclass(frozen=True)
class N0:
    version = VERSION
    stochastic = False

    @property
    def name(self) -> str:
        return "n0"

    def act(self, obs):
        ep = obs["epoch"]
        if ep == "E1":
            return "execute", 1.0, None
        if ep == "E2":
            return ("keep" if obs["candidate_delta_hat"] > 0 else "discard"), 1.0, None
        return _rest(obs, 0.0, 0.0)


@dataclass(frozen=True)
class RawKeep:
    """Reference row (not a rung): a static rule that keeps on the raw observed increment, i.e. refits the belief."""
    g: float
    h: float
    version = VERSION
    stochastic = False

    @property
    def name(self) -> str:
        return f"rawkeep:{self.g!r},{self.h!r}"

    def act(self, obs):
        if obs["epoch"] == "E2":
            return ("keep" if obs["candidate_delta_hat"] > self.h else "discard"), 1.0, None
        return _rest(obs, self.g, self.h)


@dataclass(frozen=True)
class ShrinkRefit:
    """Reference row (not a rung): keep on a + min(lam k, 1) (delta_hat - a), where k = A / (A + s^2) is the
    belief's shrinkage and a its prior mean (recovered from m_hat = a + k (delta_hat - a)); lam = 1 reproduces the
    belief's m_hat, lam >= 1 / k the raw increment."""
    g: float
    h: float
    lam: float
    version = VERSION
    stochastic = False

    @property
    def name(self) -> str:
        return f"shrink:{self.g!r},{self.h!r},{self.lam!r}"

    def act(self, obs):
        if obs["epoch"] == "E2":
            t2, s2 = obs["tau"] ** 2, obs["sigma"] ** 2
            k = t2 / (t2 + s2)
            m, d = obs["m_hat"], obs["candidate_delta_hat"]
            a = (m - k * d) / (1.0 - k)
            stat = a + min(self.lam * k, 1.0) * (d - a)
            return ("keep" if stat > self.h else "discard"), 1.0, None
        return _rest(obs, self.g, self.h)


@dataclass(frozen=True)
class TrackSDynamic:
    """N3: Track S's dynamic family (module docstring)."""
    g0: float
    b_budget: float = 0.0
    b_info: float = 0.0
    h0: float = 0.0
    h_budget: float = 0.0
    r1_bar: float = 0.0
    tau_bar: float = 0.0
    r2_bar: float = 0.0
    version = VERSION
    stochastic = False

    @property
    def name(self) -> str:
        return "n3:" + ",".join(repr(float(x)) for x in (self.g0, self.b_budget, self.b_info, self.h0,
                                                         self.h_budget, self.r1_bar, self.tau_bar, self.r2_bar))

    gap = staticmethod(budget_position)

    def act(self, obs):
        ep = obs["epoch"]
        if ep == "E1":
            score = obs["v_star"] + self.b_info * (obs["tau"] - self.tau_bar)
            thr = self.g0 - self.b_budget * (budget_position(obs) - self.r1_bar)
            return ("execute" if score >= thr else "skip"), 1.0, None
        if ep == "E2":
            thr = self.h0 - self.h_budget * (budget_position(obs) - self.r2_bar)
            return ("keep" if obs["m_hat"] > thr else "discard"), 1.0, None
        return _rest(obs, self.g0, self.h0)


@dataclass(frozen=True)
class LearnedHead:
    """N2b (module docstring). Features scaled by ``scale`` (the world's sigma_cmp)."""
    w_e1: tuple            # [1, V*/s, tau/s] -> predicted immediate kept gain / s
    w_e2: tuple            # [1, m_hat/s] -> logit P(increment > 0)
    c: float               # E1 cut on the predicted gain (raw units)
    scale: float
    version = VERSION
    stochastic = False

    @property
    def name(self) -> str:
        return f"n2b:{self.sha}:{self.c!r}"

    @property
    def sha(self) -> str:
        return _sha(self.w_e1, self.w_e2, self.c, self.scale)

    def act(self, obs):
        ep, s = obs["epoch"], self.scale
        if ep == "E1":
            x = (1.0, obs["v_star"] / s, obs["tau"] / s)
            return ("execute" if sum(a * b for a, b in zip(self.w_e1, x)) * s >= self.c else "skip"), 1.0, None
        if ep == "E2":
            x = (1.0, obs["m_hat"] / s)
            return ("keep" if sum(a * b for a, b in zip(self.w_e2, x)) > 0 else "discard"), 1.0, None
        return _rest(obs, 0.0, 0.0)


@dataclass(frozen=True)
class LawDP:
    """N4: knapsack DP on an estimated V* law (``dp.solve_law``); keep iff m_hat > 0."""
    probs: tuple
    values: tuple
    p_rule: float
    first_gain: float
    N: int
    W: int
    table: dict = field(hash=False, compare=False, default_factory=dict)
    version = VERSION
    stochastic = False

    @classmethod
    def fit(cls, probs, values, p_rule, first_gain, N, W) -> "LawDP":
        sol = dp.solve_law(N, W, p_rule, probs, values, first_gain)
        return cls(tuple(probs), tuple(values), float(p_rule), float(first_gain), N, W, sol.table)

    @property
    def sha(self) -> str:
        return _sha(self.probs, self.values, self.p_rule, self.first_gain, self.N, self.W)

    @property
    def name(self) -> str:
        return f"n4:{self.sha}"

    def act(self, obs):
        if obs["epoch"] == "E1":
            thr = self.table[(obs["slots_left"], obs["runs_left"])]
            return ("execute" if obs["v_star"] >= thr else "skip"), 1.0, None
        return _rest(obs, 0.0, 0.0)


@dataclass(frozen=True)
class RandomExec:
    q: float
    h: float = 0.0
    stochastic = True
    version = VERSION

    @property
    def name(self) -> str:
        return f"random:{self.q!r},{self.h!r}"

    def act(self, obs):
        if obs["epoch"] == "E1":
            return ("execute", self.q, None) if obs["u"] < self.q else ("skip", 1.0 - self.q, None)
        return _rest(obs, 0.0, self.h)


@dataclass(frozen=True)
class SPRT:
    g: float
    h: float
    delta: float          # alternative: increment = h +- delta
    alpha: float = 0.1
    max_obs: int = 3
    version = VERSION
    stochastic = False

    @property
    def name(self) -> str:
        return f"sprt:{self.g!r},{self.h!r},{self.delta!r},{self.alpha!r},{self.max_obs}"

    def act(self, obs):
        if obs["epoch"] == "verify":
            llr = 2.0 * self.delta * (obs["candidate_delta_hat"] - self.h) / obs["sigma"] ** 2
            bound = math.log((1.0 - self.alpha) / self.alpha)
            go = abs(llr) < bound and obs["candidate_obs"] < self.max_obs
            return ("verify" if go else "no_verify"), 1.0, None
        return _rest(obs, self.g, self.h)


@dataclass(frozen=True)
class Race:
    g: float
    h: float
    z: float = 1.0
    max_obs: int = 3
    version = VERSION
    stochastic = False

    @property
    def name(self) -> str:
        return f"race:{self.g!r},{self.h!r},{self.z!r},{self.max_obs}"

    def act(self, obs):
        if obs["epoch"] == "verify":
            go = abs(obs["candidate_delta_hat"] - self.h) < self.z * obs["sigma"] and obs["candidate_obs"] < self.max_obs
            return ("verify" if go else "no_verify"), 1.0, None
        return _rest(obs, self.g, self.h)


def knowledge_gradient(m: float, h: float, A: float, s: float, s_next: float) -> float:
    """One-step KG of a measurement that moves the comparison sd from s to s_next, for the keep decision
    max(m, h) with a normal prior of variance A on the increment."""
    v_now = A * s * s / (A + s * s)
    v_next = A * s_next * s_next / (A + s_next * s_next)
    st = math.sqrt(max(v_now - v_next, 0.0))
    if st == 0.0:
        return 0.0
    z = (m - h) / st
    return st * (z * _N.cdf(z) + math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi) - max(z, 0.0))


@dataclass(frozen=True)
class KGVerify:
    g: float
    h: float
    c: float              # price of one verify run, in value units
    max_obs: int = 3
    version = VERSION
    stochastic = False

    @property
    def name(self) -> str:
        return f"kg:{self.g!r},{self.h!r},{self.c!r},{self.max_obs}"

    def act(self, obs):
        if obs["epoch"] == "verify":
            n_c, n_i, s = obs["candidate_obs"], obs["incumbent_obs"], obs["sigma"]
            inv_i = 1.0 / n_i if n_i else 0.0
            sm2 = s * s / (1.0 / n_c + inv_i)
            s_next = math.sqrt(sm2 * (1.0 / (n_c + 1) + inv_i))
            kg = knowledge_gradient(obs["m_hat"], self.h, obs["tau"] ** 2, s, s_next)
            return ("verify" if kg >= self.c and n_c < self.max_obs else "no_verify"), 1.0, None
        return _rest(obs, self.g, self.h)


@dataclass(frozen=True)
class BudgetMargin:
    g: float
    h0: float
    c: float
    version = VERSION
    stochastic = False

    @property
    def name(self) -> str:
        return f"margin:{self.g!r},{self.h0!r},{self.c!r}"

    def act(self, obs):
        if obs["epoch"] == "E2":
            thr = self.h0 + self.c * (1.0 - obs["runs_left"] / obs["W"])
            return ("keep" if obs["m_hat"] > thr else "discard"), 1.0, None
        return _rest(obs, self.g, self.h0)


# ---------------------------------------------------------------- tuning under an equal, declared budget

class BudgetExceeded(RuntimeError):
    pass


@dataclass
class DevCache:
    """Dev-block campaign values shared by the rungs of one world (computation only; charges are per rung)."""
    world: ESynWorld
    instances: range = field(default_factory=lambda: range(DEV_BASE, DEV_BASE + N_DEV))
    vals: dict = field(default_factory=dict)
    runs: set = field(default_factory=set)        # (start, stop) of every instance range actually run

    def values(self, pol) -> np.ndarray:
        if pol.name not in self.vals:
            self.runs.add((self.instances.start, self.instances.stop))
            self.vals[pol.name] = sim.campaign_values(self.world, pol, self.instances)
        return self.vals[pol.name]


@dataclass
class Tuner:
    cache: DevCache
    budget: int = TUNE_BUDGET
    charged: list = field(default_factory=list)

    def arr(self, pol) -> np.ndarray:
        if pol.name not in self.charged:
            if len(self.charged) >= self.budget:
                raise BudgetExceeded(f"tuning budget {self.budget} reached")
            self.charged.append(pol.name)
        return self.cache.values(pol)

    def value(self, pol) -> float:
        return float(self.arr(pol).mean())

    @property
    def left(self) -> int:
        return self.budget - len(self.charged)


def better(tuner: Tuner, cand, cur) -> bool:
    """Accept ``cand`` over ``cur`` only if the paired dev improvement exceeds one standard error."""
    d = tuner.arr(cand) - tuner.arr(cur)
    se = float(np.std(d, ddof=1)) / math.sqrt(len(d))
    return float(d.mean()) > se and float(d.mean()) > 0.0


def coarse_static(tuner: Tuner, h_values=COARSE_H) -> EP.Static:
    best = None
    for g, h in product(COARSE_G, h_values):
        p = EP.Static(g, h)
        if best is None or tuner.value(p) > tuner.value(best):
            best = p
    return best


def coordinate_search(tuner: Tuner, make: Callable, x0: list, steps: list, min_frac: float = 1 / 64):
    """Coordinate search with step halving until the budget is spent or every step is below ``min_frac`` of its
    start; moves only on a paired dev improvement above one standard error."""
    x, steps, floor = list(x0), list(steps), [s * min_frac for s in steps]
    cur = make(x)
    try:
        tuner.arr(cur)
        while any(s > f for s, f in zip(steps, floor)):
            moved = False
            for i in range(len(x)):
                if steps[i] <= floor[i]:
                    continue
                for d in (-1, 1):
                    y = list(x)
                    y[i] = x[i] + d * steps[i]
                    cand = make(y)
                    if cand.name == cur.name:
                        continue
                    if better(tuner, cand, cur):
                        x, cur, moved = y, cand, True
                        break
            if not moved:
                steps = [s / 2 for s in steps]
    except BudgetExceeded:
        pass
    return cur, x


def tune_static(tuner: Tuner, h_fixed: float | None = None):
    """N1 (h free) or N2 (h fixed at 0)."""
    p0 = coarse_static(tuner, COARSE_H if h_fixed is None else (h_fixed,))
    if h_fixed is None:
        return coordinate_search(tuner, lambda x: EP.Static(max(x[0], 0.0), x[1]), [p0.g, p0.h],
                                 [0.00025, 0.0005])[0]
    return coordinate_search(tuner, lambda x: EP.Static(max(x[0], 0.0), h_fixed), [p0.g], [0.00025])[0]


def centres(world: ESynWorld, ref, instances) -> tuple[float, float, float]:
    """Track S's centring: mean r and tau of the reference rule's eligible E1 dev decisions, mean r of its eligible
    E2 dev decisions (eligible: decided by the policy, i.e. not rule-forced)."""
    e1, e2 = [], []

    class Rec:
        name = "centres-recorder"

        def act(self, obs):
            if obs["epoch"] == "E1":
                e1.append((budget_position(obs), obs["tau"]))
            elif obs["epoch"] == "E2":
                e2.append(budget_position(obs))
            return ref.act(obs)
    for i in instances:
        sim.run_campaign(world, Rec(), i)
    return float(np.mean([r for r, _ in e1])), float(np.mean([t for _, t in e1])), float(np.mean(e2))


def tune_n3(tuner: Tuner, world: ESynWorld):
    p0 = coarse_static(tuner)
    r1, tb, r2 = centres(world, p0, tuner.cache.instances)
    make = lambda x: TrackSDynamic(max(x[0], 0.0), x[1], x[2], x[3], x[4], r1, tb, r2)   # noqa: E731
    pol, _ = coordinate_search(tuner, make, [p0.g, 0.0, 0.0, p0.h, 0.0], [0.0005, 0.002, 0.1, 0.001, 0.002])
    return pol, {"r1_bar": r1, "tau_bar": tb, "r2_bar": r2, "reference": p0.name}


def tune_from_coarse(tuner: Tuner, make: Callable, extra0: list, extra_steps: list):
    """Margin, B18 and RawKeep: the shared coarse static grid, then coordinate search over (g, h, extras)."""
    p0 = coarse_static(tuner)
    return coordinate_search(tuner, make, [p0.g, p0.h] + extra0, [0.0005, 0.001] + extra_steps)[0]


# ---------------------------------------------------------------- N2b and N4: fitted on dev campaigns

def dev_trace(world: ESynWorld, instances, *, wide: bool = False) -> list[dict]:
    """Per-proposal records of dev campaigns under execute-all with the Bayes keep. ``wide`` (N4's law) runs them
    with W = llm_cap so that a binding budget does not hide later proposals (an approximation in worlds whose law
    depends on W: P2 keep feedback through runs used / W, and the posterior states of P1)."""
    import dataclasses
    out = []
    pol = EP.Static(0.0, 0.0)
    w = dataclasses.replace(world, W=max(world.W, world.llm_cap)) if wide else world
    for i in instances:
        tr: list = []
        sim.run_campaign(w, pol, i, trace=tr)
        out += [dict(e, instance=i) for e in tr]
    return out


def fit_n2b(world: ESynWorld, trace: list[dict], tuner: Tuner) -> tuple[LearnedHead, dict]:
    """N2b on the world's own dev trace (``wide=False``): one measurement per execute under the behaviour."""
    s = world.base.sigma_cmp
    rows = [e for e in trace if not e["first"] and "m_hat" in e]
    delta = np.array([e["delta"] for e in rows])
    X2 = np.column_stack([np.ones(len(rows)), [e["m_hat"] / s for e in rows]])
    y, wt = (delta > 0).astype(float), np.abs(delta) / s

    def nll(w):
        z = X2 @ w
        return float(np.sum(wt * (np.logaddexp(0.0, z) - y * z))) + 1e-6 * float(w @ w)
    w2 = minimize(nll, np.zeros(2), method="BFGS").x
    keep = (X2 @ w2) > 0                                         # E1 label: kept gain under N2b's own E2 head
    X1 = np.column_stack([np.ones(len(rows)), [e["v_star"] / s for e in rows], [e["tau"] / s for e in rows]])
    w1 = np.linalg.lstsq(X1, delta * keep / s, rcond=None)[0]
    head = lambda c: LearnedHead(tuple(map(float, w1)), tuple(map(float, w2)), float(c), s)   # noqa: E731
    cur = head(0.0)
    try:
        tuner.arr(cur)
        for c in (-0.002, -0.001, -0.0005, 0.0002, 0.0005, 0.001, 0.0015, 0.002):
            cand = head(c)
            if better(tuner, cand, cur):
                cur = cand
    except BudgetExceeded:
        pass
    pol, _ = coordinate_search(tuner, lambda x: head(x[0]), [cur.c], [0.00025])
    return pol, {"w_e1": list(pol.w_e1), "w_e2": list(pol.w_e2), "c": pol.c, "n_labels": len(rows)}


def fit_n4(world: ESynWorld, trace: list[dict], instances, n_bins: int = 20) -> tuple[LawDP, dict]:
    """N4's law from the ``wide`` dev trace."""
    v = np.array([e["v_star"] for e in trace if not e["first"] and "v_star" in e])
    qs = np.quantile(v, np.linspace(0, 1, n_bins + 1))
    idx = np.clip(np.searchsorted(qs, v, side="right") - 1, 0, n_bins - 1)
    vals = [float(v[idx == k].mean()) for k in range(n_bins) if np.any(idx == k)]
    probs = [float(np.mean(idx == k)) for k in range(n_bins) if np.any(idx == k)]
    p_rule = 1.0 - len(v) / (len(instances) * (world.llm_cap - 1))
    first = float(np.mean([e["a"] for e in trace if e["first"] and "a" in e]))
    pol = LawDP.fit(probs, vals, p_rule, first, world.llm_cap, world.W)
    return pol, {"probs": probs, "values": vals, "p_rule": p_rule, "first_gain": first}


def calibrate_q(world: ESynWorld, h: float, target_runs: float, instances, steps: int = 14) -> RandomExec:
    """q such that ``RandomExec(q, h)`` matches ``target_runs`` mean runs on ``instances`` (bisection)."""
    lo, hi = 0.0, 1.0
    for _ in range(steps):
        q = (lo + hi) / 2
        runs = np.mean([sim.run_campaign(world, RandomExec(q, h), i).runs_used for i in instances])
        lo, hi = (q, hi) if runs < target_runs else (lo, q)
    return RandomExec(round((lo + hi) / 2, 6), h)
