"""Policy interface and the non-RL ladder (build runbook P4; plan §7.0–§7.1) with B18's sequential-testing
comparators (reframe §3).

AI-assisted (Claude, chat session, 16 Nov 2026). ENGINEERING_ONLY.

**Interface.** A policy has ``name``, ``version`` and ``act(obs) -> (action, probability, selected)``. ``obs`` is the
decision-time view built from a ``spt_transition/v1`` state (``paperc.esyn.sim.obs_from_state``); a stochastic
policy (``stochastic = True``) also reads ``obs["u"]``, a replayable uniform (``sim.decision_uniform``), which plays
the role of the runbook's ``rng``. ``check_campaign`` replays every policy below.

**One belief for every arm** (plan §7.0): every rung reads the same forecasts, the world's own A2-U keyed belief
computed by the simulator; no rung refits it.

**Ladder** (plan §7.1):

* N0: execute every eligible proposal; keep iff the observed increment is positive (Paper B's default keep);
* N1: static thresholds (g, h) on the common belief, tuned on dev campaigns (``tune_static``);
* N2: the myopic one-step rule (keep iff m_hat > 0), g tuned on dev;
* N2b: a single-step learned action head: E2 keep by a cost-sensitive logistic head on per-proposal outcomes
  (label: true increment > 0, weight |increment|); E1 by a least-squares head predicting the immediate kept gain,
  with its cut c tuned on dev. Labels come from dev campaigns run under N0's execute-all with the Bayes keep;
* N3: Track S's dynamic threshold family (``r1/tracks/a2u.py`` @ ``fab88fc``: E1 execute iff
  V* + b_info (tau - tau_bar) >= g0 - b_budget (r - r1_bar); E2 keep iff m_hat > h0 - h_budget (r - r2_bar), with
  r = runs_left / W - proposals_left / llm_cap), tuned on dev by coordinate descent;
* N4: the budget DP (stochastic knapsack) on the V* law, rule share and first-trial gain estimated from dev
  campaigns (``dp.solve_law``); keep iff m_hat > 0. In the budget world it approximates the exact DP of P3;
* references: the P3 oracle member, and ``RandomExec``, which executes each eligible proposal with probability q
  (keep iff m_hat > 0), q tuned on dev so that its mean runs used match N1's.

**B18 comparators** (config worlds, where repeated measurements exist; elsewhere they reduce to static rules):
``SPRT`` (verify while the log-likelihood ratio of +delta against -delta for the increment's mean lies between
+-log((1 - alpha) / alpha); keep iff the mean exceeds h), ``Race`` (verify while the z-interval of the mean contains
h), ``KGVerify`` (verify iff the one-step knowledge gradient of one more measurement is at least c) and
``BudgetMargin`` (keep iff m_hat > h0 + c x runs used / W). OCBA is not implemented: for one candidate against one
incumbent it allocates measurements between the two, which needs an incumbent re-measurement inside the verify
decision; the simulator offers re-audit only after a keep.

**Tuning budget** (plan §7.0, equal for every tuned rung): at most ``TUNE_BUDGET`` candidate policies, each on the
same ``N_DEV`` dev campaigns (instances ``DEV_BASE`` + i). Test campaigns (``TEST_BASE`` + i) are never used for
tuning; ``Tuner`` records every instance it evaluates.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from itertools import product
from statistics import NormalDist
from typing import Callable

import numpy as np
from scipy.optimize import minimize

from paperc.esyn import dp, sim
from paperc.esyn import policies as EP
from paperc.esyn.extra import ESynWorld

VERSION = "p4/v1"
DEV_BASE = 4_000_000
TEST_BASE = 5_000_000
N_DEV = 1000
TUNE_BUDGET = 60
_N = NormalDist()


# ---------------------------------------------------------------- rungs

def _rest(obs, g, h):
    return EP._myopic(obs, g, h)


@dataclass(frozen=True)
class N0:
    version = VERSION

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
class TrackSDynamic:
    """N3: Track S's dynamic family (module docstring). At E2 the current proposal still counts as left."""
    g0: float
    b_budget: float = 0.0
    b_info: float = 0.0
    h0: float = 0.0
    h_budget: float = 0.0
    r1_bar: float = 0.0
    tau_bar: float = 0.0
    r2_bar: float = 0.0
    version = VERSION

    @property
    def name(self) -> str:
        return "n3:" + ",".join(f"{x:.6g}" for x in (self.g0, self.b_budget, self.b_info, self.h0, self.h_budget,
                                                     self.r1_bar, self.tau_bar, self.r2_bar))

    @staticmethod
    def gap(obs) -> float:
        left = obs["slots_left"] if obs["epoch"] == "E1" else obs["slots_left"] + 1
        return obs["runs_left"] / obs["W"] - left / obs["llm_cap"]

    def act(self, obs):
        ep = obs["epoch"]
        if ep == "E1":
            score = obs["v_star"] + self.b_info * (obs["tau"] - self.tau_bar)
            thr = self.g0 - self.b_budget * (self.gap(obs) - self.r1_bar)
            return ("execute" if score >= thr else "skip"), 1.0, None
        if ep == "E2":
            thr = self.h0 - self.h_budget * (self.gap(obs) - self.r2_bar)
            return ("keep" if obs["m_hat"] > thr else "discard"), 1.0, None
        return _rest(obs, self.g0, self.h0)


@dataclass(frozen=True)
class LearnedHead:
    """N2b: single-step heads (module docstring). Features are scaled by the world's sigma_cmp."""
    w_e1: tuple            # least squares: predicted immediate kept gain from [1, V*/s, tau/s]
    w_e2: tuple            # logistic: P(increment > 0) from [1, m_hat/s, delta_hat/s]
    c: float               # E1 cut on the predicted gain (raw units)
    scale: float
    version = VERSION

    @property
    def name(self) -> str:
        return "n2b:" + ",".join(f"{x:.4g}" for x in self.w_e1 + self.w_e2 + (self.c,))

    def act(self, obs):
        ep, s = obs["epoch"], self.scale
        if ep == "E1":
            x = np.array([1.0, obs["v_star"] / s, obs["tau"] / s])
            return ("execute" if float(np.dot(self.w_e1, x)) * s >= self.c else "skip"), 1.0, None
        if ep == "E2":
            x = np.array([1.0, obs["m_hat"] / s, obs["candidate_delta_hat"] / s])
            return ("keep" if float(np.dot(self.w_e2, x)) > 0 else "discard"), 1.0, None
        return _rest(obs, 0.0, 0.0)


@dataclass(frozen=True)
class RandomExec:
    q: float
    stochastic = True
    version = VERSION

    @property
    def name(self) -> str:
        return f"random:{self.q:.6g}"

    def act(self, obs):
        ep = obs["epoch"]
        if ep == "E1":
            return ("execute", self.q, None) if obs["u"] < self.q else ("skip", 1.0 - self.q, None)
        return _rest(obs, 0.0, 0.0)


@dataclass(frozen=True)
class SPRT:
    g: float
    h: float
    delta: float          # alternative: increment = h +- delta
    alpha: float = 0.1
    max_obs: int = 3
    version = VERSION

    @property
    def name(self) -> str:
        return f"sprt:{self.g:.6g},{self.h:.6g},{self.delta:.6g},{self.alpha:.6g},{self.max_obs}"

    def act(self, obs):
        ep = obs["epoch"]
        if ep == "verify":
            llr = 2.0 * self.delta * (obs["candidate_delta_hat"] - self.h) / obs["sigma"] ** 2
            bound = math.log((1.0 - self.alpha) / self.alpha)
            go = abs(llr) < bound and obs["candidate_obs"] < self.max_obs
            return ("verify" if go else "no_verify"), 1.0, None
        if ep == "E2":
            return ("keep" if obs["candidate_delta_hat"] > self.h else "discard"), 1.0, None
        return _rest(obs, self.g, self.h)


@dataclass(frozen=True)
class Race:
    g: float
    h: float
    z: float = 1.0
    max_obs: int = 3
    version = VERSION

    @property
    def name(self) -> str:
        return f"race:{self.g:.6g},{self.h:.6g},{self.z:.6g},{self.max_obs}"

    def act(self, obs):
        ep = obs["epoch"]
        if ep == "verify":
            go = abs(obs["candidate_delta_hat"] - self.h) < self.z * obs["sigma"] and obs["candidate_obs"] < self.max_obs
            return ("verify" if go else "no_verify"), 1.0, None
        if ep == "E2":
            return ("keep" if obs["candidate_delta_hat"] > self.h else "discard"), 1.0, None
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

    @property
    def name(self) -> str:
        return f"kg:{self.g:.6g},{self.h:.6g},{self.c:.6g},{self.max_obs}"

    def act(self, obs):
        ep = obs["epoch"]
        if ep == "verify":
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

    @property
    def name(self) -> str:
        return f"margin:{self.g:.6g},{self.h0:.6g},{self.c:.6g}"

    def act(self, obs):
        if obs["epoch"] == "E2":
            thr = self.h0 + self.c * (1.0 - obs["runs_left"] / obs["W"])
            return ("keep" if obs["m_hat"] > thr else "discard"), 1.0, None
        return _rest(obs, self.g, self.h0)


# ---------------------------------------------------------------- tuning under a declared budget

class BudgetExceeded(RuntimeError):
    pass


@dataclass
class Tuner:
    world: ESynWorld
    instances: range = field(default_factory=lambda: range(DEV_BASE, DEV_BASE + N_DEV))
    budget: int = TUNE_BUDGET
    cache: dict = field(default_factory=dict)
    seen_instances: set = field(default_factory=set)

    def value(self, pol) -> float:
        if pol.name not in self.cache:
            if len(self.cache) >= self.budget:
                raise BudgetExceeded(f"tuning budget {self.budget} reached")
            self.seen_instances.update((self.instances.start, self.instances.stop))
            self.cache[pol.name] = float(sim.campaign_values(self.world, pol, self.instances).mean())
        return self.cache[pol.name]

    def best(self, cands):
        out = None
        for p in cands:
            try:
                v = self.value(p)
            except BudgetExceeded:
                break
            if out is None or v > out[1]:
                out = (p, v)
        return out


def coordinate_search(tuner: Tuner, make: Callable, x0: list, steps: list, rounds: int = 6):
    """Coordinate descent with step halving on a parameter vector, within the tuner's budget."""
    x, steps = list(x0), list(steps)
    best = tuner.best([make(x)])
    for _ in range(rounds):
        improved = False
        for i in range(len(x)):
            if steps[i] == 0:
                continue
            for d in (-1, 1):
                y = list(x)
                y[i] = x[i] + d * steps[i]
                r = tuner.best([make(y)])
                if r is not None and r[1] > best[1] + 1e-15:
                    x, best, improved = y, r, True
        if not improved:
            steps = [s / 2 for s in steps]
        if len(tuner.cache) >= tuner.budget:
            break
    return best[0], best[1], x


def tune_static(tuner: Tuner, h_fixed: float | None = None):
    """N1 (h free) or N2 (h fixed): coarse grid, then coordinate refinement with step halving."""
    G = (0.0, 0.0005, 0.001, 0.0015, 0.002, 0.003)
    H = (-0.004, -0.002, -0.001, 0.0, 0.001) if h_fixed is None else (h_fixed,)
    coarse = tuner.best([EP.Static(g, h) for g, h in product(G, H)])
    p0 = coarse[0]
    make = (lambda x: EP.Static(max(x[0], 0.0), x[1])) if h_fixed is None else \
        (lambda x: EP.Static(max(x[0], 0.0), h_fixed))
    pol, v, _ = coordinate_search(tuner, make, [p0.g, p0.h], [0.00025, 0.0005 if h_fixed is None else 0.0])
    return pol, v


def tune_n3(tuner: Tuner, n1: EP.Static):
    make = lambda x: TrackSDynamic(max(x[0], 0.0), x[1], x[2], x[3], x[4], 0.0, 0.004, 0.0)   # noqa: E731
    pol, v, _ = coordinate_search(tuner, make, [n1.g, 0.0, 0.0, n1.h, 0.0], [0.0005, 0.002, 0.1, 0.001, 0.002])
    return pol, v


def tune_random(tuner: Tuner, target_runs: float, runs_of: Callable[[float], float]):
    """q such that the mean runs used match ``target_runs`` (bisection on dev; counts against the budget).
    ``runs_of`` must evaluate on ``tuner.instances`` only (the runner passes a closure over the dev block)."""
    lo, hi = 0.0, 1.0
    tuner.seen_instances.update((tuner.instances.start, tuner.instances.stop))   # ``runs_of`` runs dev campaigns
    for _ in range(14):
        q = (lo + hi) / 2
        tuner.cache[f"random-runs:{q:.6g}"] = None
        if len(tuner.cache) > tuner.budget:
            break
        if runs_of(q) < target_runs:
            lo = q
        else:
            hi = q
    return RandomExec(round((lo + hi) / 2, 6))


# ---------------------------------------------------------------- N2b and N4: fitted on dev campaigns

def dev_trace(world: ESynWorld, instances) -> list[dict]:
    """Per-proposal records of dev campaigns under execute-all with the Bayes keep (labels for N2b, law for N4).
    The campaigns run with W = llm_cap so that a binding budget does not hide the later proposals (in P2 worlds the
    keep feedback depends on runs used / W, so the law is an approximation there)."""
    import dataclasses
    out = []
    pol = EP.Static(0.0, 0.0)
    wide = dataclasses.replace(world, W=max(world.W, world.llm_cap))
    for i in instances:
        tr: list = []
        sim.run_campaign(wide, pol, i, trace=tr)
        out += [dict(e, instance=i) for e in tr]
    return out


def fit_n2b(world: ESynWorld, trace: list[dict], tuner: Tuner) -> LearnedHead:
    s = world.base.sigma_cmp
    rows = [e for e in trace if not e["first"] and "m_hat" in e]
    X1 = np.array([[1.0, e["v_star"] / s, e["tau"] / s] for e in rows])
    g1 = np.array([e["delta"] * (e["m_hat"] > 0) for e in rows]) / s
    w1 = np.linalg.lstsq(X1, g1, rcond=None)[0]
    X2 = np.array([[1.0, e["m_hat"] / s, e["dhat"] / s] for e in rows])
    y = np.array([1.0 if e["delta"] > 0 else 0.0 for e in rows])
    wt = np.abs(np.array([e["delta"] for e in rows])) / s

    def nll(w):
        z = X2 @ w
        return float(np.sum(wt * (np.logaddexp(0.0, z) - y * z))) + 1e-6 * float(w @ w)
    w2 = minimize(nll, np.zeros(3), method="BFGS").x
    head = lambda c: LearnedHead(tuple(map(float, w1)), tuple(map(float, w2)), c, s)   # noqa: E731
    best = tuner.best([head(c) for c in (-0.002, -0.001, -0.0005, 0.0, 0.0002, 0.0005, 0.001, 0.0015, 0.002)])
    return best[0]


def fit_n4(world: ESynWorld, trace: list[dict], instances, n_bins: int = 20) -> EP.Threshold:
    v = np.array([e["v_star"] for e in trace if not e["first"] and "v_star" in e])
    qs = np.quantile(v, np.linspace(0, 1, n_bins + 1))
    idx = np.clip(np.searchsorted(qs, v, side="right") - 1, 0, n_bins - 1)
    vals = [float(v[idx == k].mean()) for k in range(n_bins) if np.any(idx == k)]
    probs = [float(np.mean(idx == k)) for k in range(n_bins) if np.any(idx == k)]
    n_slots = len(instances) * (world.llm_cap - 1)
    p_rule = 1.0 - len(v) / n_slots
    first = float(np.mean([e["a"] for e in trace if e["first"] and "a" in e]))
    sol = dp.solve_law(world.llm_cap, world.W, p_rule, probs, vals, first)
    return EP.Threshold(sol.table, label="n4")


__all__ = ["VERSION", "N0", "TrackSDynamic", "LearnedHead", "RandomExec", "SPRT", "Race", "KGVerify",
           "BudgetMargin", "Tuner", "tune_static", "tune_n3", "tune_random", "fit_n2b", "fit_n4", "dev_trace",
           "knowledge_gradient", "DEV_BASE", "TEST_BASE", "N_DEV", "TUNE_BUDGET"]
