"""T5: campaign simulator for the T4 theory (ENGINEERING_ONLY; model-based numbers, not measurements).

AI-assisted (Claude). Checks the T4 statements (docs/r1/theory/T4_FEEDBACK_PROPOSER.md) at campaign
level, with heterogeneous proposal types and feedback proposers:

- Proposition 7 (value of a per-proposal threshold over a constant one: exact gap and bounds);
- Proposition 8 (screening before execution: gain E(g - V*)^+);
- Proposition 9 (record bias after a keep, inverse-Mills formula, for every proposer);
- Proposition 10 (myopic vs a simple lookahead family, under DI and DI-violating proposers);
- the record-reference artefact of incumbent-relative DI contrasts and the selection bias of the
  verify-mean value proxy (``branch_study``);
- the headroom of oracle-prior control over rules + constant prior (A2).

Model of one campaign (vectorised over M campaigns):

- a proposal has a type k drawn from the proposer's mixture; type k has (pi_k, mu_k, tau_k) and an edit
  kind (local / structural) that sets the CRN correlation rho and hence the paired comparison noise
  sigma_d = sigma * sqrt(2 (1 - rho)). Inert proposals (duplicates, inactive keys) have Delta = 0 and,
  on a bit-exact node, Delta_hat = 0 exactly;
- noise model ``iid``: Delta_hat = Delta + sigma_d z (T4 assumption A2); the displayed record moves by
  Delta_hat on a keep;
- noise model ``record``: every configuration has a recorded error e = e_s + e_t (split-seed and
  training-seed parts). A local edit of the incumbent has e_c = rho e_inc + sigma sqrt(1 - rho^2) xi
  (per component), Delta_hat = Delta + e_c - e_inc, and a keep makes e_c the new record error
  (T4 section 5). Here the record channel makes future Delta_hat depend on the keep decision;
- noise model ``shared`` (added 22 Nov 2026): e(c) = u + w(c), u shared by every configuration of a campaign,
  w(c) with the ``record`` kernel at coefficient r_w = (rho - s) / (1 - s), so that the marginal parent-child
  correlation is still rho but the parent no longer screens off its children (see "Shared-component noise
  model" below and docs/r1/theory/T5_SHARED_NOISE_20261122.md);
- run budget W (executions) and LLM-call cap N (proposals); a skip costs a call but no run.

Proposers: ``stationary`` (DI holds under ``iid``), ``dimret`` (mu falls by kappa per unit of true gain),
``memory`` (the share of bold structural edits rises with the displayed gain B - B_0) and
``memory_debiased`` (the same law reading the run-free posterior display B~ of T4 section 5).

Policies emit (pi_hat, mu_hat, tau_hat) per proposal and apply T4 Propositions 6 and 8 to them; see
``Policy``. Final true gain is J(c_T) - J(c_0) under the additive model.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

import numpy as np
from scipy.special import erfcx, ndtr

SQ2PI = math.sqrt(2.0 * math.pi)


# ---------------------------------------------------------------------------
# Closed forms (T2 Proposition 1, T4 Propositions 6-9), vectorised
# ---------------------------------------------------------------------------

def npdf(x):
    x = np.asarray(x, dtype=float)
    return np.exp(-0.5 * x * x) / SQ2PI


def mills(a):
    """Inverse Mills ratio lambda(a) = phi(a) / Phi(-a), numerically stable."""
    a = np.asarray(a, dtype=float)
    return math.sqrt(2.0 / math.pi) / erfcx(a / math.sqrt(2.0))


def value(t, mu, tau, sig):
    """V(t; mu, tau, sigma) = E[Delta 1{Delta_hat > t}] for Delta ~ N(mu, tau^2), noise sd sigma."""
    s = np.sqrt(np.asarray(tau, float) ** 2 + np.asarray(sig, float) ** 2)
    z = (t - mu) / s
    return mu * ndtr(-z) + (np.asarray(tau, float) ** 2 / s) * npdf(z)


def t_star(mu, tau, sig):
    """Per-proposal Bayes threshold t* = -mu sigma^2 / tau^2 (T4 Proposition 6)."""
    return -np.asarray(mu, float) * np.asarray(sig, float) ** 2 / np.asarray(tau, float) ** 2


def v_star(pi, mu, tau, sig):
    """V*_n = (1 - pi) V(t*; mu, tau, sigma)."""
    return (1.0 - np.asarray(pi, float)) * value(t_star(mu, tau, sig), mu, tau, sig)


def gap_exact(tt, mu, tau, sig, pi=0.0):
    """T4 Proposition 7 identity: (1 - pi) (tau^2/s^2) * oriented int_{tt}^{t*} f(u) (t* - u) du."""
    mu = np.asarray(mu, float)
    tau = np.asarray(tau, float)
    s = np.sqrt(tau ** 2 + np.asarray(sig, float) ** 2)
    ts = t_star(mu, tau, sig)
    za, zb = (tt - mu) / s, (ts - mu) / s
    integral = (ts - mu) * (ndtr(zb) - ndtr(za)) + s * (npdf(zb) - npdf(za))
    return (1.0 - np.asarray(pi, float)) * tau ** 2 / s ** 2 * integral


def gap_bounds(tt, mu, tau, sig, pi=0.0):
    """T4 Proposition 7 lower and upper bounds on the gap."""
    mu = np.asarray(mu, float)
    tau = np.asarray(tau, float)
    s = np.sqrt(tau ** 2 + np.asarray(sig, float) ** 2)
    ts = t_star(mu, tau, sig)
    d2 = (ts - tt) ** 2
    fmin = np.minimum(npdf((tt - mu) / s), npdf((ts - mu) / s)) / s   # unimodal density: min at an endpoint
    w = 1.0 - np.asarray(pi, float)
    lower = w * tau ** 2 / (2 * s ** 2) * fmin * d2
    upper = w * tau ** 2 * d2 / (2 * SQ2PI * s ** 3)
    return lower, upper


def record_bias_formula(e, delta, rho, sigma_c, t=0.0):
    """T4 Proposition 9, generalised to a threshold t: E[e' | keep] = rho e + sigma_c lambda(a),
    a = ((1 - rho) e - Delta + t) / sigma_c. (t = 0 is the rule rho of the Proposition.)"""
    a = ((1.0 - rho) * e - delta + t) / sigma_c
    return rho * e + sigma_c * mills(a)


def prop10b_loss(alpha: float, beta: float, tau: float = 1.0) -> float:
    """T4 Proposition 10(b) example: value of keeping minus value of myopic discarding."""
    keep = -alpha + beta * float(ndtr(beta / tau)) + tau * float(npdf(beta / tau))
    myopic = tau * float(npdf(0.0))
    return keep - myopic


# ---------------------------------------------------------------------------
# Shared-component noise model (noise "shared"; added 22 Nov 2026, AI-assisted (Claude, subagent))
# ---------------------------------------------------------------------------
# Construction. Within one campaign every configuration c has recorded error e(c) = u + w(c):
#   - u ~ N(0, s sigma^2) is drawn once per campaign and shared by every configuration (common random
#     numbers: the same split and training seeds for every run of the campaign);
#   - w(c) is the per-configuration part, total variance (1 - s) sigma^2, with T5's split / training
#     structure (split share f of the variance) and T5's parent -> child kernel applied per component:
#     w(child) = r w(parent) + sqrt(1 - r^2) * fresh, with the kernel coefficient r = r_w(rho, s).
# The marginal correlation of a child with its (unselected) parent is s + (1 - s) r. Choosing
#   r_w(rho, s) = (rho - s) / (1 - s)
# makes it equal to the record model's rho, so per-run sd sigma, the paired sd sigma sqrt(2 (1 - rho)) and
# every comparison against an unselected incumbent are the same as in ``record``. This needs s <= rho; for an
# edit kind with rho < s the kernel coefficient is set to 0 (fresh per-configuration part) and that kind's
# marginal correlation becomes s (> rho), i.e. its paired sd falls; ``effective_rho`` returns max(rho, s),
# which is what the policies are told.
# Two siblings a, b of the same parent (kernel coefficients r_a, r_b) have corr s + (1 - s) r_a r_b; given
# the parent their partial correlation is s (1 - rho_a)(1 - rho_b) / ((1 - s) sqrt((1 - rho_a^2)(1 - rho_b^2)))
# when both kinds are feasible. In ``record`` (s = 0) it is 0: the parent screens off its children (the
# Markov / kernel property T4 Proposition 9 uses); with s > 0 it is positive, as on digits_mlp in E1.
# u cancels in every comparison Delta_hat = Delta + w(cand) - w(inc), so a keep selects on w only, and after
# a keep the law of the next candidate's error given the record's error e = u + w is no longer N(rho e, .).
# With s = 0 the code path draws exactly the same numbers as ``record`` (u comes from a separate generator).

def shared_rho_w(rho, s: float):
    """Kernel coefficient of the per-configuration part: (rho - s) / (1 - s), floored at 0 (rho < s)."""
    if not 0.0 <= s < 1.0:
        raise ValueError("shared share s must be in [0, 1)")
    return np.maximum((np.asarray(rho, float) - s) / (1.0 - s), 0.0)


def effective_rho(rho, s: float):
    """Marginal parent-child correlation of the shared model: s + (1 - s) r_w = max(rho, s)."""
    return s + (1.0 - s) * shared_rho_w(rho, s)


def shared_correlations(rho_a: float, rho_b: float, s: float) -> dict:
    """For the shared model with share s and two edit kinds of target correlations rho_a, rho_b, computed from
    the generative parameters (s, r_a, r_b): (i) the marginal parent-child correlations, (ii) the correlation of
    two siblings (one of each kind, children of the same parent) and their partial correlation given the parent;
    also the closed form of the partial correlation (valid when rho_a, rho_b >= s)."""
    ra, rb = float(shared_rho_w(rho_a, s)), float(shared_rho_w(rho_b, s))
    ca, cb = s + (1 - s) * ra, s + (1 - s) * rb          # Var = 1: Cov(parent, child) = Var(u) + r Var(w)
    cab = s + (1 - s) * ra * rb                          # Cov(child a, child b) = Var(u) + r_a r_b Var(w)
    part = (cab - ca * cb) / math.sqrt((1 - ca ** 2) * (1 - cb ** 2))
    closed = s * (1 - rho_a) * (1 - rho_b) / ((1 - s) * math.sqrt((1 - rho_a ** 2) * (1 - rho_b ** 2))) \
        if s < 1 else float("nan")
    return {"s": s, "r_w_a": ra, "r_w_b": rb, "marginal_parent_child_a": ca, "marginal_parent_child_b": cb,
            "sibling_corr": cab, "sibling_partial": part, "sibling_partial_closed_form": closed,
            "feasible": bool(rho_a >= s and rho_b >= s)}


def shared_share_for_partial(p: float, rho: float) -> float:
    """Share s at which two siblings of the same kind (target correlation rho) have partial correlation p
    given their parent: inverts p = s (1 - rho) / ((1 - s)(1 + rho)). The largest reachable p is rho / (1 + rho),
    at s = rho (kernel coefficient 0: the pure shared-factor model of P09 section 4); above it, ValueError."""
    if p > rho / (1 + rho) + 1e-12:
        raise ValueError(f"partial correlation {p} not reachable at rho = {rho} (max {rho / (1 + rho):.4f})")
    return p * (1 + rho) / (p * (1 + rho) + (1 - rho))


# ---------------------------------------------------------------------------
# Scenario objects
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PType:
    name: str
    weight: float
    mu: float
    tau: float
    pi: float = 0.0           # P(inert | type); pi = 1 is a rule-detectable duplicate / inactive edit
    kind: str = "local"       # local | structural
    bold: bool = False        # the memory-reading proposer shifts mass toward bold types
    rho: float | None = None  # per-type CRN correlation (overrides the node / study default; e.g. ~1 for tweaks)


@dataclass(frozen=True)
class Node:
    name: str
    sigma: float              # per-run sd of the metric
    rho_local: float
    rho_struct: float
    split_share: float = 0.6  # share of the comparison variance due to the split seed

    def rho(self, kind: str) -> float:
        return self.rho_local if kind == "local" else self.rho_struct

    def sigma_d(self, kind: str) -> float:
        return self.sigma * math.sqrt(2.0 * (1.0 - self.rho(kind)))

    @property
    def paired_sd(self) -> float:
        return self.sigma_d("local")

    @property
    def delta_n(self) -> float:
        """D18 effect size delta_n = max(0.002, 0.25 x paired sd)."""
        return max(0.002, 0.25 * self.paired_sd)


@dataclass(frozen=True)
class Proposer:
    kind: str = "stationary"  # stationary | dimret | memory | memory_debiased
    kappa: float = 0.0        # dimret: mu falls by kappa per unit of true gain
    bold_max: float = 0.6     # memory: bold share of the non-inert mass at a high displayed gain
    trigger: float = 0.015    # memory: displayed gain at which the shift is half way (metric units)
    width: float = 0.004      # memory: logistic width (metric units)


@dataclass(frozen=True)
class Scenario:
    name: str
    node: Node
    types: tuple
    proposer: Proposer = Proposer()
    noise: str = "iid"        # iid | record | shared
    shared_share: float = 0.0  # noise "shared" only: s = Var(u) / sigma^2 (see shared_correlations)

    def with_(self, **kw) -> "Scenario":
        return replace(self, **kw)


def reweight(types: tuple, inert_share: float | None = None, dispersion: float | None = None) -> tuple:
    """Rescale the inert share and/or the dispersion of non-inert type means about their weighted mean."""
    ts = list(types)
    if inert_share is not None:
        w_in = sum(t.weight for t in ts if t.pi >= 1)
        w_ni = sum(t.weight for t in ts if t.pi < 1)
        ts = [replace(t, weight=(t.weight / w_in * inert_share if t.pi >= 1 else t.weight / w_ni * (1 - inert_share)))
              for t in ts]
    if dispersion is not None:
        ni = [t for t in ts if t.pi < 1]
        m = sum(t.weight * t.mu for t in ni) / sum(t.weight for t in ni)
        ts = [replace(t, mu=m + dispersion * (t.mu - m)) if t.pi < 1 else t for t in ts]
    return tuple(ts)


def type_summary(types: tuple) -> dict:
    """Analytic summary of a stationary mixture: inert share, P(Delta > 0 | informative), moments."""
    w = np.array([t.weight for t in types], float)
    w = w / w.sum()
    pi = np.array([t.pi for t in types])
    mu = np.array([t.mu for t in types])
    tau = np.array([t.tau for t in types])
    ni = w * (1 - pi)
    ni = ni / ni.sum()
    m = float((ni * mu).sum())
    v_mu = float((ni * (mu - m) ** 2).sum())
    t2 = float((ni * tau ** 2).sum())
    p_pos = float((ni * ndtr(mu / np.maximum(tau, 1e-12))).sum())
    return {"inert_share": float((w * pi).sum()), "p_improve_informative": p_pos, "mu_bar": m,
            "sd_type_means": math.sqrt(v_mu), "tau_within_rms": math.sqrt(t2), "tau_pooled": math.sqrt(v_mu + t2)}


# ---------------------------------------------------------------------------
# Policies
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Policy:
    """A control-plane policy: a prior source plus T4's rules.

    prior: ``zero`` (rule rho: t = 0, no screening), ``const`` (A1: one (pi, mu, tau) per node),
    ``rules`` (A2: pi = 1 on rule-detectable types, constant (mu, tau) on the rest), ``oracle``
    (true per-proposal law), ``calibrated`` (a calibrated predictor that sees mu_n + noise),
    ``noisy`` (an uncalibrated predictor: mu_hat = m + mu_scale (mu_n - m) + noise,
    tau_hat = tau_scale tau_n).
    """

    name: str
    prior: str = "oracle"
    rules: bool = True        # skip rule-detectable inert types (Corollary 8a)
    screen: bool = False      # E1 screening at price g (Proposition 8)
    g: float = 0.0
    theta0: float = 0.0       # threshold shift sigma_d (theta0 + theta1 * remaining-budget fraction)
    theta1: float = 0.0
    noise_sd: float = 0.0     # predictor noise on mu (metric units)
    mu_scale: float = 1.0
    tau_scale: float = 1.0
    # Threshold correction for a selected incumbent (record / shared noise only; added 22 Nov 2026).
    # ``none``: T4 Proposition 6 as deployed (t* with the paired sd). ``known``: oracle that knows the
    # inherited part x of the incumbent's error (record: x = e; shared: x = w(inc)); Delta_hat given x is
    # N(Delta - (1 - r) x, s_f^2), so the Bayes threshold is -(1 - r) x + t*(mu, tau, s_f), with r the
    # parent-child kernel coefficient of the inherited part and s_f the sd of the fresh noise. ``table``: a
    # feasible coarse version that replaces x by E[x | k] and adds (1 - r)^2 Var(x | k) to s_f^2, k = number of
    # keeps so far (P06 section 4.1, t**), with the tables (ecorr_m, ecorr_v) estimated on development runs.
    ecorr: str = "none"
    ecorr_m: tuple = ()
    ecorr_v: tuple = ()


@dataclass(frozen=True)
class Constants:
    """Dev-estimated node constants (A1 / A2) and moments for the calibrated predictor."""

    pi_all: float
    mu_all: float
    tau_all: float
    pi_r: float
    mu_r: float
    tau_r: float
    m_bar: float
    v_mu: float
    tau2_w: float

    def to_dict(self) -> dict:
        return dict(self.__dict__)


# ---------------------------------------------------------------------------
# Campaign simulator
# ---------------------------------------------------------------------------

@dataclass
class _Arr:
    mu: np.ndarray
    tau: np.ndarray
    pi: np.ndarray
    rho: np.ndarray
    sigd: np.ndarray
    bold: np.ndarray
    rule: np.ndarray
    w: np.ndarray
    rho_w: np.ndarray | None = None   # noise "shared": kernel coefficient of the per-configuration part


def _arrays(scn: Scenario) -> _Arr:
    ts = scn.types
    w = np.array([t.weight for t in ts], float)
    rho = np.array([scn.node.rho(t.kind) if t.rho is None else t.rho for t in ts])
    if scn.noise == "shared":
        rho_w = shared_rho_w(rho, scn.shared_share)
        rho = effective_rho(rho, scn.shared_share)      # marginal correlation the policies are told
        return _Arr(mu=np.array([t.mu for t in ts]), tau=np.array([max(t.tau, 1e-9) for t in ts]),
                    pi=np.array([t.pi for t in ts]), rho=rho,
                    sigd=scn.node.sigma * np.sqrt(2.0 * (1.0 - rho)), bold=np.array([t.bold for t in ts]),
                    rule=np.array([t.pi >= 1 for t in ts]), w=w / w.sum(), rho_w=rho_w)
    return _Arr(mu=np.array([t.mu for t in ts]), tau=np.array([max(t.tau, 1e-9) for t in ts]),
                pi=np.array([t.pi for t in ts]), rho=rho,
                sigd=scn.node.sigma * np.sqrt(2.0 * (1.0 - rho)), bold=np.array([t.bold for t in ts]),
                rule=np.array([t.pi >= 1 for t in ts]), w=w / w.sum())


def _type_weights(A: _Arr, prop: Proposer, G: np.ndarray) -> np.ndarray:
    """(M, T) mixture weights of the memory proposer given the displayed gain G."""
    w = A.w
    inert = A.pi >= 1
    m_ni = w[~inert].sum()
    b0 = w[A.bold].sum() / m_ni
    frac = 1.0 / (1.0 + np.exp(-(G - prop.trigger) / prop.width))
    b = b0 + (max(prop.bold_max, b0) - b0) * frac                     # bold share of non-inert mass
    out = np.empty((G.size, w.size))
    for k in range(w.size):
        if inert[k]:
            out[:, k] = w[k]
        elif A.bold[k]:
            out[:, k] = w[k] / (b0 * m_ni) * b * m_ni
        else:
            out[:, k] = w[k] / ((1 - b0) * m_ni) * (1 - b) * m_ni
    return out


def simulate(scn: Scenario, pol: Policy, W: int, N: int, M: int, seed: int, const: Constants | None = None,
             ref: tuple | None = None, g_eval: float | None = None, collect: bool = False,
             trace: int = 0) -> dict:
    """Simulate M campaigns. Common random numbers: call c of campaign m uses the same draws for every
    policy, so policy contrasts at the same seed are paired.

    trace: if > 0, return under "_trace" the incumbent's and the candidate's total recorded errors of the
    first ``trace`` calls (arrays (calls, M)), for checking the noise model's correlation structure.

    ref = (mu_ref, tau_ref, shift): reference constant threshold t~_n = -mu_ref sigma_n^2 / tau_ref^2 +
    shift * sigma_n, for which the Proposition 7 gap and bounds are summed over executed proposals.
    g_eval: price used for the Lagrangian objective and for sum (g - V*)^+ (default pol.g).
    """
    A = _arrays(scn)
    node, prop = scn.node, scn.proposer
    rng = np.random.default_rng(seed)
    T = A.w.size
    cum0 = np.cumsum(A.w)
    ge = pol.g if g_eval is None else g_eval
    if pol.prior in ("const", "rules", "calibrated", "noisy") and const is None:
        raise ValueError("this prior needs dev-estimated Constants")
    f = node.split_share
    sig_s_run, sig_t_run = node.sigma * math.sqrt(f), node.sigma * math.sqrt(1 - f)
    shared = scn.noise == "shared"
    if scn.noise not in ("iid", "record", "shared"):
        raise ValueError(scn.noise)
    if pol.ecorr not in ("none", "known", "table"):
        raise ValueError(pol.ecorr)
    s_sh = scn.shared_share if shared else 0.0
    if shared:
        # (es, et) hold the per-configuration part w (split / training components), variance (1 - s) sigma^2;
        # u is the campaign-shared part, from a separate generator so that the main stream is unchanged.
        ksh = math.sqrt(1.0 - s_sh)
        sig_s_run, sig_t_run = sig_s_run * ksh, sig_t_run * ksh
        u_sh = math.sqrt(s_sh) * node.sigma * np.random.default_rng([seed, 0x5A]).standard_normal(M)
    else:
        u_sh = np.zeros(M)

    J = np.zeros(M)
    es = rng.normal(0, sig_s_run, M)
    et = rng.normal(0, sig_t_run, M)
    if scn.noise == "iid":
        es = np.zeros(M)
        et = np.zeros(M)
    e0 = es + et
    # kernel coefficient r of the inherited part and fresh comparison sd s_f per type (for ecorr)
    r_inh = A.rho_w if shared else A.rho
    sig_fresh = node.sigma * math.sqrt(1.0 - s_sh) * np.sqrt(1.0 - r_inh ** 2)
    KT = 16
    ktab = np.zeros((3, KT))               # count, sum x, sum x^2 of the inherited part x by keeps so far
    kfree = {"keeps": 0, "viol_general": 0, "min_margin_general": float("inf"), "keeps_t_nonneg": 0,
             "viol_p09": 0, "keeps_t_neg": 0, "viol_p09_t_neg": 0, "null_keeps_t_nonneg": 0,
             "null_viol_rise": 0}
    p9x = {"first": [0, 0.0, 0.0], "later": [0, 0.0, 0.0]}   # n, sum residual, sum residual^2 (record / shared)
    t_sum = np.zeros(2)                    # sum of thresholds and count, executed non-inert proposals
    tr = [] if trace else None
    Bt = np.zeros(M)                       # debiased displayed gain B~ - B~_0
    runs = np.zeros(M, int)
    n_keep = np.zeros(M)
    n_false = np.zeros(M)
    n_exec = np.zeros(M)
    n_calls = np.zeros(M)
    n_bold = np.zeros(M)
    n_skip_learned = np.zeros(M)
    lag = np.zeros(M)
    pos = np.zeros(M)
    pos_r = np.zeros(M)
    gap = np.zeros(M)
    gap_lo = np.zeros(M)
    gap_hi = np.zeros(M)
    p9 = {"n": 0, "obs": 0.0, "pred": 0.0, "res": 0.0, "res2": 0.0, "null_n": 0, "null_rise": 0.0,
          "null_pred_rise": 0.0}
    col = [] if collect else None

    for c in range(N):
        u_type, u_inert = rng.random(M), rng.random(M)
        z_delta, z_s, z_t, z_pred = rng.standard_normal(M), rng.standard_normal(M), rng.standard_normal(M), \
            rng.standard_normal(M)
        act = runs < W
        if not act.any():
            break
        frac_rem = 1.0 - runs / W
        # proposer
        if prop.kind in ("memory", "memory_debiased"):
            G = (J + es + et - e0) if prop.kind == "memory" else Bt
            wts = _type_weights(A, prop, G)
            cum = np.cumsum(wts, axis=1)
            typ = np.minimum((u_type[:, None] > cum).sum(axis=1), T - 1)
        else:
            typ = np.minimum(np.searchsorted(cum0, u_type, side="right"), T - 1)
        mu_n = A.mu[typ].copy()
        if prop.kind == "dimret":
            mu_n = mu_n - prop.kappa * J
        tau_n, pi_n, rho_n, sig_n = A.tau[typ], A.pi[typ], A.rho[typ], A.sigd[typ]
        rule_n = A.rule[typ]
        inert = u_inert < pi_n
        delta = np.where(inert, 0.0, mu_n + tau_n * z_delta)
        # policy prior
        p = pol.prior
        if p == "zero":
            pih, muh, tauh = np.where(rule_n, 1.0, 0.0), mu_n, tau_n
        elif p == "const":
            pih, muh, tauh = np.full(M, const.pi_all), np.full(M, const.mu_all), np.full(M, const.tau_all)
        elif p == "rules":
            pih = np.where(rule_n, 1.0, const.pi_r)
            muh, tauh = np.full(M, const.mu_r), np.full(M, const.tau_r)
        elif p == "oracle":
            pih, muh, tauh = pi_n, mu_n, tau_n
        elif p == "calibrated":
            sd2 = pol.noise_sd ** 2
            kap = const.v_mu / (const.v_mu + sd2) if const.v_mu + sd2 > 0 else 1.0
            sig_obs = mu_n + pol.noise_sd * z_pred
            muh = const.m_bar + kap * (sig_obs - const.m_bar)
            tauh = np.sqrt(kap * tau_n ** 2 + (1 - kap) * (const.tau2_w + const.v_mu))
            pih = np.where(rule_n, 1.0, np.where(pi_n >= 1, 1.0, pi_n))
        elif p == "noisy":
            muh = const.m_bar + pol.mu_scale * (mu_n - const.m_bar) + pol.noise_sd * z_pred
            tauh = pol.tau_scale * tau_n
            pih = np.where(rule_n, 1.0, pi_n)
        else:
            raise ValueError(p)
        if p == "zero":
            t_b = np.zeros(M)
        else:
            t_b = t_star(muh, tauh, sig_n)
        if pol.ecorr != "none" and p != "zero" and scn.noise != "iid":
            r_n, sf_n = r_inh[typ], sig_fresh[typ]
            if pol.ecorr == "known":
                xm, xv = es + et, 0.0
            else:
                kk = np.minimum(n_keep.astype(int), len(pol.ecorr_m) - 1)
                xm, xv = np.asarray(pol.ecorr_m)[kk], np.asarray(pol.ecorr_v)[kk]
            t_b = -(1.0 - r_n) * xm + t_star(muh, tauh, np.sqrt(sf_n ** 2 + (1.0 - r_n) ** 2 * xv))
        t = t_b + sig_n * (pol.theta0 + pol.theta1 * frac_rem)
        execute = act.copy()
        if pol.rules:
            execute &= ~rule_n
        if pol.screen and p != "zero":
            vh = (1.0 - pih) * value(t_b, muh, tauh, sig_n)
            skip_l = execute & (vh < pol.g)
            n_skip_learned += skip_l
            execute &= ~skip_l
        # observation
        if scn.noise == "iid":
            dhat = delta + sig_n * z_s
            es_c, et_c = es, et
        elif shared:
            rw_n = A.rho_w[typ]
            cr = np.sqrt(1 - rw_n ** 2)
            es_c = rw_n * es + cr * sig_s_run * z_s
            et_c = rw_n * et + cr * sig_t_run * z_t
            dhat = delta + (es_c + et_c) - (es + et)          # u cancels
        else:
            cr = np.sqrt(1 - rho_n ** 2)
            es_c = rho_n * es + cr * sig_s_run * z_s
            et_c = rho_n * et + cr * sig_t_run * z_t
            dhat = delta + (es_c + et_c) - (es + et)
        dhat = np.where(inert, 0.0, dhat)
        keep = execute & ~inert & (dhat > t)
        if trace and c < trace:
            tr.append(np.stack([u_sh + es + et, u_sh + es_c + et_c, inert.astype(float), typ.astype(float)]))
        exn = execute & ~inert
        t_sum += (float(t[exn].sum()), float(exn.sum()))
        if scn.noise != "iid":
            kk = np.minimum(n_keep[exn].astype(int), KT - 1)
            x = (es + et)[exn]
            ktab[0] += np.bincount(kk, minlength=KT)
            ktab[1] += np.bincount(kk, weights=x, minlength=KT)
            ktab[2] += np.bincount(kk, weights=x * x, minlength=KT)
        # kernel-free inequality of P09 section 4 (every keep, every error law): e' > e - Delta + t, in particular
        # e' > e - Delta under the default rule (t = 0) and e' > e at a null keep with t >= 0
        if keep.any():
            if scn.noise == "iid":
                e_o = (es + et)[keep]
                e_n = e_o + (dhat - delta)[keep]
            else:
                e_o = (u_sh + es + et)[keep]
                e_n = (u_sh + es_c + et_c)[keep]
            dk, tk = delta[keep], t[keep]
            marg = (e_n - (e_o - dk)) - tk
            tol = 1e-12
            kfree["keeps"] += int(keep.sum())
            kfree["viol_general"] += int((marg <= -tol).sum())
            kfree["min_margin_general"] = min(kfree["min_margin_general"], float(marg.min()))
            nn = tk >= 0
            kfree["keeps_t_nonneg"] += int(nn.sum())
            kfree["viol_p09"] += int(((e_n <= e_o - dk - tol) & nn).sum())
            kfree["keeps_t_neg"] += int((~nn).sum())
            kfree["viol_p09_t_neg"] += int(((e_n <= e_o - dk - tol) & ~nn).sum())
            nul = nn & (dk <= 0)
            kfree["null_keeps_t_nonneg"] += int(nul.sum())
            kfree["null_viol_rise"] += int(((e_n <= e_o - tol) & nul).sum())
        # Proposition 9 bookkeeping (record model; keeps of non-inert proposals)
        if scn.noise == "record" and keep.any():
            e_old = (es + et)[keep]
            e_new = (es_c + et_c)[keep]
            sc = node.sigma * np.sqrt(1 - rho_n[keep] ** 2)
            pred = record_bias_formula(e_old, delta[keep], rho_n[keep], sc, t[keep])
            res = e_new - pred
            p9["n"] += int(keep.sum())
            p9["obs"] += float(e_new.sum())
            p9["pred"] += float(pred.sum())
            p9["res"] += float(res.sum())
            p9["res2"] += float((res ** 2).sum())
            nul = delta[keep] <= 0
            p9["null_n"] += int(nul.sum())
            p9["null_rise"] += float((e_new - e_old)[nul].sum())
            p9["null_pred_rise"] += float((pred - e_old)[nul].sum())
        elif shared and keep.any():
            # T4 Proposition 9's formula with the marginal rho (kernel assumed): not true by construction here
            e_old = (u_sh + es + et)[keep]
            e_new = (u_sh + es_c + et_c)[keep]
            sc = node.sigma * np.sqrt(1 - rho_n[keep] ** 2)
            pred = record_bias_formula(e_old, delta[keep], rho_n[keep], sc, t[keep])
            res = e_new - pred
            p9["n"] += int(keep.sum())
            p9["obs"] += float(e_new.sum())
            p9["pred"] += float(pred.sum())
            p9["res"] += float(res.sum())
            p9["res2"] += float((res ** 2).sum())
            nul = delta[keep] <= 0
            p9["null_n"] += int(nul.sum())
            p9["null_rise"] += float((e_new - e_old)[nul].sum())
            p9["null_pred_rise"] += float((pred - e_old)[nul].sum())
        elif scn.noise == "iid" and keep.any():
            # record increment bias E[Delta_hat - Delta | keep] = sigma_d lambda((t - Delta)/sigma_d)
            obs = (dhat - delta)[keep]
            pred = sig_n[keep] * mills((t[keep] - delta[keep]) / sig_n[keep])
            res = obs - pred
            p9["n"] += int(keep.sum())
            p9["obs"] += float(obs.sum())
            p9["pred"] += float(pred.sum())
            p9["res"] += float(res.sum())
            p9["res2"] += float((res ** 2).sum())
            nul = delta[keep] <= 0
            p9["null_n"] += int(nul.sum())
            p9["null_rise"] += float(obs[nul].sum())
            p9["null_pred_rise"] += float(pred[nul].sum())
        if scn.noise != "iid" and keep.any():
            e_old = (u_sh + es + et)[keep]
            e_new = (u_sh + es_c + et_c)[keep]
            sc = node.sigma * np.sqrt(1 - rho_n[keep] ** 2)
            res = e_new - record_bias_formula(e_old, delta[keep], rho_n[keep], sc, t[keep])
            first = n_keep[keep] == 0
            for lab, msk in (("first", first), ("later", ~first)):
                p9x[lab][0] += int(msk.sum())
                p9x[lab][1] += float(res[msk].sum())
                p9x[lab][2] += float((res[msk] ** 2).sum())
        # Proposition 7 and 8 bookkeeping (true law)
        vs = np.where(pi_n >= 1, 0.0, v_star(np.minimum(pi_n, 0.999999), mu_n, tau_n, sig_n))
        pp = np.maximum(ge - vs, 0.0)
        pos += np.where(act, pp, 0.0)
        pos_r += np.where(act & ~rule_n, pp, 0.0)
        if ref is not None:
            tt = -ref[0] * sig_n ** 2 / ref[1] ** 2 + ref[2] * sig_n
            ex = execute & (pi_n < 1)
            gp = gap_exact(tt, mu_n, tau_n, sig_n, np.minimum(pi_n, 0.999999))
            lo, hi = gap_bounds(tt, mu_n, tau_n, sig_n, np.minimum(pi_n, 0.999999))
            gap += np.where(ex, gp, 0.0)
            gap_lo += np.where(ex, lo, 0.0)
            gap_hi += np.where(ex, hi, 0.0)
        if collect:
            sel = act
            col.append(np.stack([typ[sel], inert[sel], delta[sel], mu_n[sel], tau_n[sel], rule_n[sel]], axis=1))
        # state update
        post = mu_n + tau_n ** 2 / (tau_n ** 2 + sig_n ** 2) * (dhat - mu_n)
        Bt += np.where(keep, post, 0.0)
        J += np.where(keep, delta, 0.0)
        if scn.noise == "iid":
            es = es + np.where(keep, dhat - delta, 0.0)
        else:                              # record and shared: the candidate's parts become the record's
            es = np.where(keep, es_c, es)
            et = np.where(keep, et_c, et)
        runs += execute
        n_exec += execute
        n_calls += act
        n_keep += keep
        n_false += keep & (delta <= 0)
        n_bold += act & A.bold[typ]
        lag += np.where(keep, delta, 0.0) - ge * execute

    def ms(x):
        return float(np.mean(x)), float(np.std(x, ddof=1) / math.sqrt(len(x)))

    out = {"policy": pol.name, "scenario": scn.name, "W": W, "N": N, "M": M, "seed": seed,
           "gain": ms(J), "runs": float(runs.mean()), "calls": float(n_calls.mean()), "keeps": float(n_keep.mean()),
           "false_keep_rate": float(n_false.sum() / max(n_keep.sum(), 1)), "exec": float(n_exec.mean()),
           "skips_learned": float(n_skip_learned.mean()), "bold_share": float(n_bold.sum() / max(n_calls.sum(), 1)),
           "record_bias_end": ms(es + et - e0), "debiased_bias_end": ms(Bt - J),
           "lagrangian": ms(lag), "pos_part": ms(pos), "pos_part_nonrule": ms(pos_r),
           "gap": ms(gap), "gap_lo": ms(gap_lo), "gap_hi": ms(gap_hi), "p9": p9,
           "_J": J, "_lag": lag, "_gap": gap, "_pos": pos, "_pos_r": pos_r}
    if p9["n"] > 1:
        n = p9["n"]
        mres = p9["res"] / n
        out["p9_summary"] = {"keeps": n, "mean_observed": p9["obs"] / n, "mean_formula": p9["pred"] / n,
                             "mean_residual": mres,
                             "se_residual": math.sqrt(max(p9["res2"] / n - mres ** 2, 0) / n),
                             "null_keeps": p9["null_n"],
                             "null_mean_rise": p9["null_rise"] / max(p9["null_n"], 1),
                             "null_mean_rise_formula": p9["null_pred_rise"] / max(p9["null_n"], 1)}
    if collect:
        out["_collect"] = np.concatenate(col, axis=0) if col else np.zeros((0, 6))
    # added 22 Nov 2026 (new keys only; existing keys and values unchanged)
    out["kfree"] = kfree
    out["mean_threshold_executed"] = t_sum[0] / max(t_sum[1], 1.0)
    out["_ktab"] = ktab
    p9s = {}
    for lab, (n, sr, sr2) in p9x.items():
        if n > 1:
            m = sr / n
            p9s[lab] = {"keeps": n, "mean_residual": m, "se_residual": math.sqrt(max(sr2 / n - m * m, 0) / n)}
    out["p9_by_keep"] = p9s
    if trace:
        out["_trace"] = np.stack(tr, axis=0) if tr else np.zeros((0, 4, M))
    return out


def public(res: dict) -> dict:
    """Drop the per-campaign arrays before writing JSON."""
    return {k: v for k, v in res.items() if not k.startswith("_")}


def paired(a: dict, b: dict, key: str = "_J") -> tuple:
    """Mean and s.e. of the per-campaign difference a - b (same seed: common random numbers)."""
    d = a[key] - b[key]
    return float(d.mean()), float(d.std(ddof=1) / math.sqrt(d.size))


def fit_constants(scn: Scenario, W: int, N: int, M: int, seed: int) -> Constants:
    """Dev-estimate A1/A2 constants and calibrated-predictor moments from campaigns under rule rho."""
    r = simulate(scn, Policy("rho", prior="zero", rules=False), W, N, M, seed, collect=True)
    C = r["_collect"]
    inert = C[:, 1] > 0.5
    rule = C[:, 5] > 0.5
    delta, mu_n, tau_n = C[:, 2], C[:, 3], C[:, 4]
    d_all = delta[~inert]
    nr = ~rule
    d_r = delta[nr & ~inert]
    m_r = mu_n[nr & ~inert]
    return Constants(pi_all=float(inert.mean()), mu_all=float(d_all.mean()), tau_all=float(d_all.std()),
                     pi_r=float(inert[nr].mean()) if nr.any() else 0.0, mu_r=float(d_r.mean()),
                     tau_r=float(d_r.std()), m_bar=float(m_r.mean()), v_mu=float(m_r.var()),
                     tau2_w=float((tau_n[nr & ~inert] ** 2).mean()))


def tune(scn: Scenario, pol: Policy, W: int, N: int, M: int, seed: int, const: Constants | None,
         grid: dict) -> tuple:
    """Grid-search policy fields on development campaigns; returns (best policy, table of dev gains)."""
    keys = list(grid)
    best, best_v, table = pol, -np.inf, []
    for vals in np.array(np.meshgrid(*[grid[k] for k in keys], indexing="ij")).reshape(len(keys), -1).T:
        cand = replace(pol, **{k: float(v) for k, v in zip(keys, vals)})
        v = simulate(scn, cand, W, N, M, seed, const)["gain"][0]
        table.append({**{k: float(x) for k, x in zip(keys, vals)}, "dev_gain": v})
        if v > best_v + 1e-12:
            best, best_v = cand, v
    return best, table


# ---------------------------------------------------------------------------
# Branch study: E1b-style continue vs verify forks (DI-test artefact, value-proxy selection bias)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BranchStudy:
    name: str
    types: tuple
    sigma_t_d: float          # paired training-seed sd of one comparison
    sigma_s_d: float          # paired split-seed sd of one comparison
    rho: float = 0.8          # CRN correlation of a local edit's error with its incumbent's
    rho_struct: float | None = None   # structural edits (default min(rho, 0.5)); PType.rho overrides both
    W: int = 20
    points: tuple = (4, 8, 12)
    r: int = 2
    split: str = "fixed"      # fixed | vary
    q_rep: float = 0.95       # P(a branch repetition reuses the shared proposal draw) - decoding noise
    feedback_shift: float = 0.0   # DI-violating control: mu shift of the next 3 proposals after a kept point

    @property
    def sigma_d(self) -> float:
        return math.hypot(self.sigma_t_d, self.sigma_s_d)


def _draw_props(rng, shape, A_w):
    return {"u": rng.random(shape), "ui": rng.random(shape), "zd": rng.standard_normal(shape),
            "zs": rng.standard_normal(shape), "zt": rng.standard_normal(shape)}


def branch_study(bs: BranchStudy, n_inst: int, seed: int) -> dict:
    """Simulate n_inst root campaigns under rule rho with a stationary proposer (DI holds for the
    proposer), fork at each point into continue / verify(r) x 2 repetitions, and return per point
    arrays (instance, point) needed for the DI contrasts and the value residual."""
    rng = np.random.default_rng(seed)
    ts = bs.types
    w = np.array([t.weight for t in ts], float)
    w /= w.sum()
    cum = np.cumsum(w)
    mu_t = np.array([t.mu for t in ts])
    tau_t = np.array([t.tau for t in ts])
    pi_t = np.array([t.pi for t in ts])
    rs = min(bs.rho, 0.5) if bs.rho_struct is None else bs.rho_struct
    rho_t = np.array([(t.rho if t.rho is not None else (bs.rho if t.kind == "local" else rs)) for t in ts])
    k = 2 * (1 - bs.rho)
    s_s, s_t = bs.sigma_s_d / math.sqrt(k), bs.sigma_t_d / math.sqrt(k)   # per-run component sds (local edits)

    def propose(d, n):
        typ = np.minimum(np.searchsorted(cum, d["u"], side="right"), len(ts) - 1)
        inert = d["ui"] < pi_t[typ]
        delta = np.where(inert, 0.0, mu_t[typ] + tau_t[typ] * d["zd"])
        return typ, inert, delta

    n = n_inst
    J = np.zeros(n)
    es, et = rng.normal(0, s_s, n), rng.normal(0, s_t, n)
    P = len(bs.points)
    pts = {key: np.zeros((n, P)) for key in ("J", "es", "et", "delta", "inert", "ecs", "ect", "dhat", "rho")}
    pmax = max(bs.points)
    for i in range(1, pmax + 1):
        d = _draw_props(rng, n, w)
        typ, inert, delta = propose(d, n)
        rk = rho_t[typ]
        cr = np.sqrt(1 - rk ** 2)
        ecs, ect = rk * es + cr * s_s * d["zs"], rk * et + cr * s_t * d["zt"]
        dhat = np.where(inert, 0.0, delta + ecs + ect - es - et)
        if i in bs.points:
            j = bs.points.index(i)
            for key, val in (("J", J), ("es", es), ("et", et), ("delta", delta), ("inert", inert), ("ecs", ecs),
                             ("ect", ect), ("dhat", dhat), ("rho", rk)):
                pts[key][:, j] = val
        keep = (~inert) & (dhat > 0)
        J = np.where(keep, J + delta, J)
        es, et = np.where(keep, ecs, es), np.where(keep, ect, et)

    out = {"points": list(bs.points), "n_inst": n}
    # decisions at the point
    keep_c = (pts["inert"] < 0.5) & (pts["dhat"] > 0)
    zv = rng.standard_normal((n, P))
    eta_s = (pts["ecs"] - pts["es"])
    pair = np.sqrt(2 * (1 - pts["rho"]))                 # paired-noise factor of the point's edit
    if bs.split == "fixed":
        dbar = pts["delta"] + eta_s + s_t * pair / math.sqrt(bs.r) * zv
    else:
        dbar = pts["delta"] + math.hypot(s_s, s_t) * pair / math.sqrt(bs.r) * zv
    dbar = np.where(pts["inert"] > 0.5, 0.0, dbar)
    keep_v = (pts["inert"] < 0.5) & (dbar > 0)
    out.update(keep_c=keep_c, keep_v=keep_v, dbar=dbar, delta=pts["delta"], dhat=pts["dhat"])

    # continuation: 2 actions x 2 repetitions; draws shared with prob q_rep (decoding noise otherwise)
    L = bs.W - min(bs.points)
    shared = _draw_props(rng, (n, P, L), w)
    res = {}
    for a, act in enumerate(("c", "v")):
        kp = keep_c if act == "c" else keep_v
        for rep in (1, 2):
            own = _draw_props(rng, (n, P, L), w)
            use = rng.random((n, P, L)) < bs.q_rep
            d = {key: np.where(use, shared[key], own[key]) for key in shared}
            Jb = np.where(kp, pts["J"] + pts["delta"], pts["J"])
            esb = np.where(kp, pts["ecs"], pts["es"])
            etb = np.where(kp, pts["ect"], pts["et"])
            rec0 = Jb + esb + etb
            length = np.array([bs.W - p - (2 * bs.r if act == "v" else 0) for p in bs.points])
            dh_hist = np.zeros((n, P, 3))
            ab_hist = np.zeros((n, P, 3))
            tv_hist = np.zeros((n, P, 3))
            ti_hist = np.zeros((n, P, 3))
            for jj in range(L):
                live = jj < length[None, :]
                typ, inert, delta = propose({key: d[key][:, :, jj] for key in d}, None)
                if bs.feedback_shift:
                    delta = np.where(inert, 0.0, delta + np.where(kp & (jj < 3), bs.feedback_shift, 0.0))
                rk = rho_t[typ]
                cr = np.sqrt(1 - rk ** 2)
                ecs = rk * esb + cr * s_s * d["zs"][:, :, jj]
                ect = rk * etb + cr * s_t * d["zt"][:, :, jj]
                dh = np.where(inert, 0.0, delta + ecs + ect - esb - etb)
                absm = np.where(inert, Jb + esb + etb, Jb + delta + ecs + ect)
                if jj < 3:
                    dh_hist[:, :, jj] = dh
                    ab_hist[:, :, jj] = absm
                    tv_hist[:, :, jj] = Jb + delta          # true value of the candidate (what a fresh audit estimates)
                    ti_hist[:, :, jj] = delta               # audited increment over the branch's own incumbent
                keep = live & (~inert) & (dh > 0)
                Jb = np.where(keep, Jb + delta, Jb)
                esb, etb = np.where(keep, ecs, esb), np.where(keep, ect, etb)
            res[(act, rep)] = {"Y": Jb, "rec0": rec0, "dh1": dh_hist[:, :, 0], "dh3": dh_hist.mean(axis=2),
                               "ab1": ab_hist[:, :, 0], "ab3": ab_hist.mean(axis=2),
                               "tv1": tv_hist[:, :, 0], "tv3": tv_hist.mean(axis=2),
                               "ti1": ti_hist[:, :, 0], "ti3": ti_hist.mean(axis=2)}
    out["branches"] = res
    return out


def branch_stats(br: dict, idx: np.ndarray | None = None) -> dict:
    """DI contrasts and the value residual from a branch_study output (optionally on a subset of
    instances idx). Mirrors r1/diagnostics/di_test.py: point-level, repetitions averaged first."""
    sel = slice(None) if idx is None else idx
    kc, kv = br["keep_c"][sel], br["keep_v"][sel]
    ch = kc != kv
    prom = (~kc) & kv
    dem = kc & (~kv)
    B = br["branches"]
    g = lambda a, r, key: B[(a, r)][key][sel]
    out = {"n_points": int(ch.size), "changed": int(ch.sum()), "promotions": int(prom.sum()),
           "demotions": int(dem.sum())}
    # signed shifts and distances
    for key in ("rec0", "dh1", "dh3", "ab1", "ab3", "tv1", "tv3", "ti1", "ti3"):
        v = (g("v", 1, key) + g("v", 2, key)) / 2
        c = (g("c", 1, key) + g("c", 2, key)) / 2
        out[f"signed_{key}_changed"] = float((v - c)[ch].mean()) if ch.any() else float("nan")
        out[f"signed_{key}_promotion"] = float((v - c)[prom].mean()) if prom.any() else float("nan")
        out[f"signed_{key}_unchanged"] = float((v - c)[~ch].mean()) if (~ch).any() else float("nan")
        if key == "rec0":
            continue
        cross = (np.abs(g("v", 1, key) - g("c", 1, key)) + np.abs(g("v", 2, key) - g("c", 2, key))) / 2
        null = (np.abs(g("c", 1, key) - g("c", 2, key)) + np.abs(g("v", 1, key) - g("v", 2, key))) / 2
        if ch.any() and (~ch).any():
            out[f"D_changed_{key}"] = float(cross[ch].mean())
            out[f"D_null_changed_{key}"] = float(null[ch].mean())
            out[f"D_unchanged_{key}"] = float(cross[~ch].mean())
            out[f"excess_null_{key}"] = out[f"D_changed_{key}"] - out[f"D_null_changed_{key}"]
            out[f"excess_unch_{key}"] = out[f"D_changed_{key}"] - out[f"D_unchanged_{key}"]
    # value residual
    Ydiff = (g("v", 1, "Y") + g("v", 2, "Y")) / 2 - (g("c", 1, "Y") + g("c", 2, "Y")) / 2
    dbar, delta = br["dbar"][sel], br["delta"][sel]
    bc = np.zeros_like(Ydiff)
    for j in range(Ydiff.shape[1]):
        u = ~ch[:, j]
        bc[:, j] = Ydiff[u, j].mean() if u.any() else 0.0
    proxy = np.where(prom, dbar, -dbar)
    imm = np.where(prom, delta, -delta)
    if ch.any():
        out["audit_diff"] = float(Ydiff[ch].mean())
        out["immediate_proxy"] = float(proxy[ch].mean())
        out["immediate_true"] = float(imm[ch].mean())
        out["budget_correction"] = float(bc[ch].mean())
        out["residual"] = float((Ydiff - proxy - bc)[ch].mean())
        out["residual_oracle_immediate"] = float((Ydiff - imm - bc)[ch].mean())
        out["proxy_bias"] = float((proxy - imm)[ch].mean())
        out["dbar_given_promotion"] = float(dbar[prom].mean()) if prom.any() else float("nan")
        out["delta_given_promotion"] = float(delta[prom].mean()) if prom.any() else float("nan")
        out["neg_dbar_given_demotion"] = float(-dbar[dem].mean()) if dem.any() else float("nan")
        out["rate_promotion"] = float(prom.mean())
        out["rate_demotion"] = float(dem.mean())
    return out


def di_flag_rate(br: dict, n_study: int, n_perm: int, seed: int,
                 keys=("dh1", "dh3", "ab1", "ab3", "tv1", "tv3", "ti1", "ti3")) -> dict:
    """Split simulated instances into studies of n_study instances and apply the (simplified) combined
    DI criterion of the 19 Oct reports: both excesses > 0 and both one-sided permutation p < 0.05
    (labels permuted across points; no bootstrap interval, no Holm). Also returns the distribution of
    the value-residual estimate across studies."""
    rng = np.random.default_rng(seed)
    n = br["keep_c"].shape[0]
    n_rep = n // n_study
    flags = {k: 0 for k in keys}
    valid = 0
    resid = []
    B = br["branches"]
    for s in range(n_rep):
        idx = np.arange(s * n_study, (s + 1) * n_study)
        kc, kv = br["keep_c"][idx].ravel(), br["keep_v"][idx].ravel()
        ch = kc != kv
        if ch.sum() < 1 or (~ch).sum() < 2:
            continue
        valid += 1
        st = branch_stats(br, idx)
        if "residual" in st:
            resid.append(st["residual"])
        perms = np.argsort(rng.random((n_perm, ch.size)), axis=1)
        lab = ch[perms]                                     # permuted changed labels
        nch = ch.sum()
        for key in keys:
            g = lambda a, r: B[(a, r)][key][idx].ravel()
            cross = (np.abs(g("v", 1) - g("c", 1)) + np.abs(g("v", 2) - g("c", 2))) / 2
            null = (np.abs(g("c", 1) - g("c", 2)) + np.abs(g("v", 1) - g("v", 2))) / 2
            ex_null = (cross - null)[ch].mean()
            ex_unch = cross[ch].mean() - cross[~ch].mean()
            pn = ((lab * (cross - null)).sum(1) / nch)
            pu = (lab * cross).sum(1) / nch - ((~lab) * cross).sum(1) / (~lab).sum(1)
            p_null = (1 + (pn >= ex_null).sum()) / (n_perm + 1)
            p_unch = (1 + (pu >= ex_unch).sum()) / (n_perm + 1)
            if ex_null > 0 and ex_unch > 0 and p_null < 0.05 and p_unch < 0.05:
                flags[key] += 1
    resid = np.array(resid)
    return {"n_study_instances": n_study, "studies": valid,
            "flag_rate": {k: flags[k] / max(valid, 1) for k in keys},
            "residual_mean": float(resid.mean()) if resid.size else float("nan"),
            "residual_sd": float(resid.std(ddof=1)) if resid.size > 1 else float("nan"),
            "residual_q05_q50_q95": [float(np.quantile(resid, q)) for q in (0.05, 0.5, 0.95)] if resid.size else [],
            "frac_residual_le_obs_tabular": float((resid <= -0.00122155).mean()) if resid.size else float("nan")}
