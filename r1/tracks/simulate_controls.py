"""Fast simulator of the Track S regime: S0.6 synthetic calibration, and fixtures for ``analyze.py``.

AI-assisted (Claude, 29 Oct 2026). Output records are labelled ``FIXTURE`` (phase ``synthetic`` / ``dev_tuning``
/ ``campaign``): they are not the synthetic control nodes run through the real collector (runbook §4), and
nothing here is evidence. Every default is illustrative until S0.5/S0.7 fix the regime (see ``match_noise``).

Campaign model (raw metric units, digits-like scale): ``llm_cap`` trials; a share ``p_rule`` of proposals is
rule-detectable and ineligible; trial 1 is never rule-detectable and is executed and kept
without comparison (as in the harness and the collector's worlds.py). A proposal edits key j with size s; true increment
δ = s·(θ_j − offset) + η; measured Δ̂ = δ + ε. Increments add to the incumbent. Base controller A2-U: per-key
conjugate normal posterior on θ_j; V̂* = E[max(m̂, 0)]; τ_pred = predictive sd of δ. Campaign Y = true incumbent
+ audit noise + σ_campaign noise (matched to the pilot σ_D or the dev between-configuration sd).

Worlds: N0 (NF + NI, fresh keys, non-binding W); B0 (as N0 at a binding W); P0 budget, P1 information,
P2± keep feedback (VARIANTS, each diffuse / concentrated, strength calibrated so that the best member's oracle
gain equals δ_Y). Fork leaves (``simulate``): E1 skip / execute / ghost / ctrl_only and E2 keep / discard arms
at r = 2 repetitions with common random numbers. ``planted_forks``: fork-level generator with planted channel
effects for analysis tests. S0.6 (``s06_node``): N0 false-positive rate and oracle check, calibration of every P
variant, power with the one resize, P(correct selection), P(route B | positive control).
"""
from __future__ import annotations

import argparse
import json
import math
import zlib
from dataclasses import asdict, dataclass, field, fields, replace
from pathlib import Path
from typing import Callable, Sequence

import numpy as np

from r1.tracks import analyze as A
from r1.tracks.schema import (
    STATE_FEATURES,
    TRACKS_LEAF_SCHEMA,
    TRACKS_ROOT_SCHEMA,
    Forecast,
    LeafRecord,
    Provenance,
    RootRecord,
    Selection,
)

SIM_HOST = "sim-cpu"
_SQRT2 = math.sqrt(2.0)
_SQRT2PI = math.sqrt(2.0 * math.pi)


def sim_provenance(label: str = "FIXTURE", host: str = SIM_HOST) -> Provenance:
    return Provenance(host=host, gpu="none", harness_commit="none", paper_commit="none", manager_gguf_sha256="none",
                      llama_build="none", controller_version="a2u-sim/v1", prior_sha256="none", phase="synthetic",
                      label=label)


@dataclass
class Regime:
    W: int = 10
    llm_cap: int = 40
    p_rule: float = 0.55
    n_instances: int = 30
    forks_per_instance: float = 20.0
    p_over: float = 0.5
    band_e1: float = 0.0004
    band_e2: float = 0.002
    channel_share: float = 1.0 / 3.0
    K_audit: int = 5
    sigma_audit: float = 0.004
    sigma_term: float = 0.0
    sigma_campaign: float = 0.0     # extra per-campaign terminal noise (campaign phase), calibrates σ_D
    g: float = 0.00066


@dataclass
class World:
    kind: str = "N0"
    strength: float = 0.0
    mu0: float = -0.0005
    tau0: float = 0.004
    sigma_eta: float = 0.002
    sigma_cmp: float = 0.0066
    size_filler: float = 1.0
    size_sd: float = 0.6
    size_probe: float = 1.0
    probe_offset: float = 1.5      # probe mean is −probe_offset·τθ (in units of size·θ)
    p_probe: float = 0.25
    n_follow: int = 2
    sigma_probe: float | None = None  # P1: measurement sd of the probe kind (None -> sigma_cmp)
    sigma_follow: float | None = None  # P1: measurement sd of the follow-up kind (None -> sigma_cmp)
    follow_offset: float = 0.0         # P1: follow-up mean is size·(θ − follow_offset·τθ)
    probe_max_trial: int = 40          # P1: probes are proposed only up to this trial
    n_keys: int = 0                    # > 0: proposals edit one of n_keys recurring keys (shared θ per key)
    fb_early_bf: float | None = None   # P2: budget-fraction cut of the feedback law (see Sim.fb_scale)
    fb_shape: str = "const"            # P2: "const" | "step" | "linear" | "r_linear" | "r_step" (Sim.fb_scale)
    fb_sign: float = 1.0               # P2+ (+1) / P2− (−1) for the r_* shapes
    fb_r_cut: float | None = None      # r_step cut on r = runs remaining fraction
    p_big: float = 0.0                 # P0 (rev 6): share of "big" proposals (size × (1 + strength))
    trend_shape: str | None = None     # P0 (rev 7): "linear" | "early_window" drift of the θ mean over trials
    trend_window: int = 8              # P0 concentrated: length of the early window
    trend_late: float = 0.0            # P0 concentrated: θ shift after the window, in units of strength
    inst_prule_spread: float = 0.0     # P0 (rev-7 attempt, kept): instance-level rule-skip share spread
    inst_busy_p: float = 0.0           # P0 concentrated (rev 7): share of "busy" instances
    inst_busy_drop: float = 0.0        # P0 concentrated: their rule-skip share is p_rule − drop
    fb_accum: bool = False             # P2: shifts of keeps in the window add up (rev 7 P2−)
    lag_min: int = 2
    lag_max: int = 5
    fb_len: int = 3
    y0: float = 0.90

    def __post_init__(self):
        if self.kind not in ("N0", "B0", "P0", "P1", "P2"):
            raise ValueError(f"unknown world {self.kind}")


# P1 world family found by the 29 Oct exploratory scan (ANALYSIS_NOTES.md §P1): a precise early probe with a
# low one-step value, followed by two large, noisy follow-ups on the same key. Under a binding W a probe's
# information has to beat the shadow price of its run; the milder variants tried first did not.
P1_DEFAULTS = dict(sigma_probe=0.0005, sigma_eta=0.001, size_sd=0.3, lag_min=3, lag_max=10, follow_offset=0.5,
                   probe_offset=1.0, n_follow=2, sigma_follow=0.05, mu0=0.0005, p_probe=0.8, probe_max_trial=16)
DEFAULT_WORLD_KW = {"P1": P1_DEFAULTS}

# Revision-6 control variants (best member's oracle gain calibrated to δ_Y by ``calibrate_strength``):
#   P0 (budget): binding W, NF + NI, heterogeneous proposal values, so the best execute threshold depends on the
#     runs remaining. concentrated: 10 % "big" proposals (size × (1 + strength)); diffuse: size_sd = 0.3 + strength.
#   P1 (information, Prop. 10(c)): fillers on 3 recurring keys; probes open fresh keys (high τ_pred, low one-step
#     value, precise result) and schedule two large follow-ups on the probe's key; strength = follow-up size.
#     concentrated: p_probe 0.25; diffuse: p_probe 0.8.
#   P2+ / P2− (keep feedback, Prop. 10(b)): a keep shifts the θ mean of the next fb_len proposals by
#     ± strength × scale(r). diffuse: scale = r, 6 trials; concentrated: scale = 1{r > 0.7}, 10 trials.
VARIANTS = {
    # P0 (rev 7): proposal quality drifts over the campaign (θ mean + strength·f(t), unknown to A2-U's prior) at a
    # binding W: runs spent while they are plentiful (early) buy good proposals, runs spent late buy poor ones, so a
    # threshold that is lenient while runs are plentiful and strict when they are scarce beats any static one.
    # diffuse: f = 1 − 2t/T; concentrated: f = 1 for the first 8 trials, else 0. (Pure across-campaign budget
    # heterogeneity, the first rev-7 attempt, gave ≤ 0.2 δ_Y even for the unrestricted schedule.)
    ("P0", "concentrated"): dict(trend_shape="early_window", trend_window=8),
    ("P0", "diffuse"): dict(trend_shape="linear"),
    ("P1", "concentrated"): dict(P1_DEFAULTS, n_keys=3, p_probe=0.25),
    ("P1", "diffuse"): dict(P1_DEFAULTS, n_keys=3, p_probe=0.8),
    ("P2+", "diffuse"): dict(fb_shape="r_linear", fb_sign=1.0, fb_len=6),
    ("P2+", "concentrated"): dict(fb_shape="r_step", fb_sign=1.0, fb_r_cut=0.7, fb_len=10),
    # P2− (rev 7): a keep made while runs are plentiful lowers the θ mean of every later proposal (cumulative,
    # rest of the campaign); late keeps are harmless. diffuse: scale r; concentrated: scale 1{r > 0.7}.
    ("P2-", "diffuse"): dict(fb_shape="r_linear", fb_sign=-1.0, fb_len=40, fb_accum=True),
    ("P2-", "concentrated"): dict(fb_shape="r_step", fb_sign=-1.0, fb_r_cut=0.7, fb_len=40, fb_accum=True),
}
CAL_GRIDS = {"P0": (0.001, 0.002, 0.003, 0.004, 0.006, 0.008, 0.012), "P1": (2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 16.0, 20.0),
             "P2+": (0.002, 0.004, 0.006, 0.008, 0.01, 0.012, 0.016, 0.02),
             "P2-": (0.002, 0.004, 0.006, 0.008, 0.01, 0.012, 0.016, 0.02)}


def make_world(kind: str, strength: float = 0.0, variant: str | None = None, **kw) -> World:
    if variant is not None:
        base = dict(VARIANTS[(kind, variant)])
        return World(kind=kind.rstrip("+-"), strength=strength, **{**base, **kw})
    return World(kind=kind, strength=strength, **{**DEFAULT_WORLD_KW.get(kind, {}), **kw})


# --------------------------------------------------------------------------------------------- policies
class A2UPolicy:
    """Myopic A2-U at a static run price g: execute iff V̂* ≥ g; keep iff m̂ > 0."""

    def __init__(self, g: float):
        self.g = float(g)
        self.name = f"a2u_g:{self.g:.6g}"

    def e1(self, f: dict) -> bool:
        return f["index_value"] >= self.g

    def e2(self, f: dict) -> bool:
        return f["index_value"] > 0


class LinearPolicy:
    """Fast evaluator of a serialised ``tracks_policy/v1`` model (π′ or m̃); equals ``analyze.policy_act``."""

    def __init__(self, pol: dict, name: str | None = None):
        self.pol = pol
        self.name = name or f"{pol['kind']}:{A.policy_sha256(pol)[:16]}"
        p = len(pol["features"])
        coef = np.asarray(pol["coef"], float)
        st = pol["standardization"]
        self.par = {}
        for ep, j in (("E1", 0), ("E2", 1)):
            key = ep if pol["interactions"] == "epoch" else "all"
            if key not in st or ep not in pol["trained_epochs"]:
                continue
            mean = np.asarray(st[key]["mean"], float)
            sd = np.asarray([np.inf if x is None else x for x in st[key]["sd"]], float)
            if pol["interactions"] == "epoch":
                b = coef[2 + j * p: 2 + (j + 1) * p]
            else:
                b = coef[2:2 + p]
            self.par[ep] = (coef[j] - pol["thresholds"][ep], mean, b / sd)

    def score(self, f: dict, ep: str) -> float:
        c0, mean, b = self.par[ep]
        x = np.fromiter((f[k] for k in self.pol["features"]), float, len(self.pol["features"]))
        return float(c0 + ((x - mean) * b).sum())

    def e1(self, f: dict) -> bool:
        # an epoch the model was not trained on falls back to A2-U's myopic rule at g = 0 (documented)
        return self.score(f, "E1") > 0 if "E1" in self.par else f["index_value"] >= 0

    def e2(self, f: dict) -> bool:
        return self.score(f, "E2") > 0 if "E2" in self.par else f["index_value"] > 0


# --------------------------------------------------------------------------------------------- A2-U
def v_star(a: float, A_: float, sigma_cmp: float) -> float:
    """E[max(m̂, 0)], m̂ ~ N(a, v), v = A²/(A + σ_cmp²) (preposterior variance of the posterior mean)."""
    v = A_ * A_ / (A_ + sigma_cmp ** 2)
    sv = math.sqrt(v)
    z = a / sv
    return a * 0.5 * (1.0 + math.erf(z / _SQRT2)) + sv * math.exp(-0.5 * z * z) / _SQRT2PI


@dataclass
class State:
    t: int = 1
    runs_used: int = 0
    keeps: int = 0
    prior_skips: int = 0
    y_true: float = 0.0
    post: dict = field(default_factory=dict)
    executed_keys: set = field(default_factory=set)
    pending: list = field(default_factory=list)   # (due_trial, key, size)
    keep_trials: list = field(default_factory=list)

    def copy(self) -> "State":
        return State(self.t, self.runs_used, self.keeps, self.prior_skips, self.y_true, dict(self.post),
                     set(self.executed_keys), list(self.pending), list(self.keep_trials))


class Stream:
    """Manager + worker randomness for one campaign path (root, or one repetition of one fork)."""

    def __init__(self, rng: np.random.Generator, n: int):
        self.u_rule = rng.random(n + 2)
        self.u_kind = rng.random(n + 2)
        self.lag = rng.random(n + 2)
        self.eta = rng.standard_normal(n + 2)
        self.eps = rng.standard_normal(n + 2)
        self.z_size = rng.standard_normal(n + 2)


class Sim:
    def __init__(self, world: World, regime: Regime, seed: int):
        self.w, self.r, self.seed = world, regime, seed
        self.W = regime.llm_cap if world.kind == "N0" else regime.W
        self.a2u = A2UPolicy(regime.g)
        self.dlog = None
        self._mult = 1.0
        self._prule = regime.p_rule

    # ---- model pieces
    def theta(self, theta_tab: np.ndarray, key: int, t: int, st: State) -> float:
        th = theta_tab[key]
        if self.w.kind == "P0" and self.w.trend_shape:
            x = t / self.r.llm_cap
            if self.w.trend_shape == "linear":          # good early, poor late
                th += self.w.strength * (1.0 - 2.0 * x)
            elif self.w.trend_shape == "early_window":  # a short early window of very good proposals
                th += self.w.strength if t <= self.w.trend_window else self.w.trend_late * self.w.strength
        if self.w.kind == "P2":
            recent = [sc for (k, sc) in st.keep_trials if t - self.w.fb_len <= k < t]
            if recent:
                th += self.w.strength * (sum(recent) if self.w.fb_accum else recent[-1])
        return th

    def fb_scale(self, bf: float) -> float:
        """P2: how a keep made at budget fraction bf shifts the later proposal law (sign and size)."""
        w = self.w
        if w.fb_shape == "const":
            return 1.0 if (w.fb_early_bf is None or bf < w.fb_early_bf) else 0.0
        if w.fb_shape == "step":   # helpful early, harmful late
            return 1.0 if bf < (w.fb_early_bf if w.fb_early_bf is not None else 0.5) else -1.0
        if w.fb_shape == "linear":
            return 1.0 - 2.0 * bf
        if w.fb_shape == "r_linear":   # revision 6: P2± diffuse, scale = sign · r (r = runs remaining fraction)
            return w.fb_sign * (1.0 - bf)
        if w.fb_shape == "r_step":     # revision 6: P2± concentrated, scale = sign · 1{r > cut}
            return w.fb_sign * (1.0 if (1.0 - bf) > (w.fb_r_cut if w.fb_r_cut is not None else 0.7) else 0.0)
        raise ValueError(w.fb_shape)

    def propose(self, st: State, t: int, s: Stream):
        """None (rule-detectable) or (key, size, offset, kind); δ = size·(θ_key − offset) + η.

        Keys are the trial index of the proposal that created them. In P1 a probe (edit kind "probe", known
        offset ``probe_offset``·τθ: low one-step value, but informative about θ) schedules ``n_follow``
        follow-up edits of size ``strength`` on the same key at increasing lags.
        """
        w = self.w
        if w.kind == "P1":
            due = [p for p in st.pending if p[0] <= t]
            if due:
                p = min(due)
                st.pending.remove(p)
                return (p[1], p[2], w.follow_offset * w.tau0, "follow")
        if t != 1 and s.u_rule[t] < self._prule:   # trial 1 is never rule-detectable (harness / collector port)
            return None
        if w.kind == "P1" and t <= w.probe_max_trial and s.u_kind[t] < w.p_probe:
            due = t
            for i in range(w.n_follow):
                due += w.lag_min + int(((s.lag[t] * (i + 3.7)) % 1.0) * (w.lag_max - w.lag_min + 1))
                if due <= self.r.llm_cap:
                    st.pending.append((due, t, w.strength))
            return (t, w.size_probe, w.probe_offset * w.tau0, "probe")
        key = (self.r.llm_cap + 2 + int(s.u_kind[t] * w.n_keys)) if w.n_keys > 0 else t
        size = w.size_filler * math.exp(w.size_sd * s.z_size[t]) * self._mult
        if w.kind == "P0" and w.p_big > 0 and s.lag[t] < w.p_big:
            size *= 1.0 + w.strength
        return (key, size, 0.0, "filler")

    def sig(self, kind: str) -> float:
        """Measurement sd by edit kind (known to the controller): probe / follow-up kinds may differ (P1)."""
        if kind == "probe" and self.w.sigma_probe is not None:
            return self.w.sigma_probe
        if kind == "follow" and self.w.sigma_follow is not None:
            return self.w.sigma_follow
        return self.w.sigma_cmp

    def forecast(self, st: State, key: int, size: float, off: float = 0.0, kind: str = "filler"):
        mu, var = st.post.get(key, (self.w.mu0, self.w.tau0 ** 2))
        a = size * (mu - off)
        A_ = size * size * var + self.w.sigma_eta ** 2
        return a, A_, v_star(a, A_, self.sig(kind))

    def m_hat(self, a, A_, dhat, kind: str = "filler"):
        return a + A_ / (A_ + self.sig(kind) ** 2) * (dhat - a)

    def update(self, st: State, key: int, size: float, dhat: float, off: float = 0.0, kind: str = "filler"):
        """Conjugate normal update of θ_key from Δ̂ + size·offset = size·θ + (η + ε)."""
        mu, var = st.post.get(key, (self.w.mu0, self.w.tau0 ** 2))
        nv = self.w.sigma_eta ** 2 + self.sig(kind) ** 2
        prec = 1.0 / var + size * size / nv
        st.post[key] = ((mu / var + size * (dhat + size * off) / nv) / prec, 1.0 / prec)
        st.executed_keys.add(key)

    def keep(self, st: State, delta: float, t: int):
        st.y_true += delta
        st.keeps += 1
        if t >= 2:  # trial 1 is kept without comparison; it carries no feedback signal (P2)
            sc = self.fb_scale(st.runs_used / self.W) if self.w.kind == "P2" else 1.0
            if sc != 0.0:
                st.keep_trials.append((t, sc))

    # ---- one trial under a policy (default: A2-U at the declared price g)
    def trial(self, st: State, t: int, s: Stream, theta_tab, log: list | None, policy=None):
        policy = policy or self.a2u
        self._mult = float(theta_tab[-1])
        self._prule = float(theta_tab[-2])
        prop = self.propose(st, t, s)
        rec = {"t": t, "rule": prop is None, "pending_after": list(st.pending)}
        if prop is None:
            if log is not None:
                log.append(rec)
            return
        key, size, off, kind = prop
        delta = size * (self.theta(theta_tab, key, t, st) - off) + self.w.sigma_eta * s.eta[t]
        eps = self.sig(kind) * s.eps[t]
        a, A_, vs = self.forecast(st, key, size, off, kind)
        runs_left = self.W - st.runs_used
        e1_elig = t >= 2 and runs_left > 0
        f1 = self.features(st, t, key, vs) if e1_elig else None
        if f1 is not None:
            f1["tau_pred"] = math.sqrt(A_)
        rec.update(key=key, size=size, off=off, kind=kind, delta=delta, eps=eps, v_star=vs, a=a, A=A_,
                   e1_eligible=e1_elig, state_e1=f1)
        if t == 1:
            st.runs_used += 1
            self.update(st, key, size, delta + eps, off, kind)
            self.keep(st, delta, t)
            rec.update(executed=True, kept=True)
        elif e1_elig and policy.e1(f1):
            st.runs_used += 1
            dhat = delta + eps
            mh = self.m_hat(a, A_, dhat, kind)
            f2 = self.features(st, t, key, mh, pre_update_key_seen=key in st.executed_keys)
            rec.update(executed=True, dhat=dhat, m_hat=mh, e2_eligible=True, state_e2=f2)
            self.update(st, key, size, dhat, off, kind)
            if log is not None:
                rec["snap_e2"] = st.copy()
            if policy.e2(f2):
                self.keep(st, delta, t)
                rec["kept"] = True
        else:
            if e1_elig:
                st.prior_skips += 1
            rec["executed"] = False
        if log is not None:
            log.append(rec)
        if self.dlog is not None and t >= 2:
            if e1_elig:
                self.dlog.append({"index": t, "epoch": "E1", "eligible": True, "index_value": vs,
                                  "budget_fraction": f1["budget_fraction"], "r": f1["r"], "tau_pred": f1["tau_pred"],
                                  "action": "execute" if rec.get("executed") else "skip"})
            if rec.get("e2_eligible"):
                self.dlog.append({"index": t, "epoch": "E2", "eligible": True, "index_value": rec["m_hat"],
                                  "budget_fraction": rec["state_e2"]["budget_fraction"], "r": rec["state_e2"]["r"],
                                  "action": "keep" if rec.get("kept") else "discard"})

    def features(self, st: State, t: int, key: int, index_value: float, pre_update_key_seen=None) -> dict:
        seen = (key in st.executed_keys) if pre_update_key_seen is None else pre_update_key_seen
        cap = self.r.llm_cap
        return {"budget_fraction": st.runs_used / self.W, "runs_left": float(self.W - st.runs_used),
                "trial_index": float(t), "key_seen": float(seen), "prior_skips": float(st.prior_skips),
                "keeps_so_far": float(st.keeps), "index_value": float(index_value),
                # runbook rev 7: r = runs_left/W − proposals_left/N_cap, proposals_left including the current one
                "r": (self.W - st.runs_used) / self.W - (cap - t + 1) / cap}

    # ---- root campaign
    def run_root(self, inst: int, theta_tab):
        st = State(y_true=self.w.y0)
        s = Stream(np.random.default_rng([self.seed, inst, 0]), self.r.llm_cap)
        log = []
        for t in range(1, self.r.llm_cap + 1):
            snap = st.copy()
            n_before = len(log)
            self.trial(st, t, s, theta_tab, log)
            log[n_before]["snap_e1"] = snap
        return st, log

    # ---- one whole campaign under a policy (campaign phase)
    def run_campaign(self, theta_tab, policy, stream_seed, noise_rng: np.random.Generator | None,
                     noiseless: bool = False, decisions: list | None = None) -> float:
        st = State(y_true=self.w.y0)
        s = Stream(np.random.default_rng(stream_seed), self.r.llm_cap)
        self.dlog = decisions
        try:
            for t in range(1, self.r.llm_cap + 1):
                self.trial(st, t, s, theta_tab, None, policy)
        finally:
            self.dlog = None
        if noiseless:
            return float(st.y_true)
        aud = self.r.sigma_audit * noise_rng.standard_normal(self.r.K_audit)
        return float(st.y_true + aud.mean() + self.r.sigma_campaign * noise_rng.standard_normal())

    # ---- continuation of one leaf
    def run_leaf(self, snap: State, fork: dict, epoch: str, arm: str, s: Stream, theta_tab, audit_rng):
        st = snap.copy()
        t = fork["t"]
        runs0 = st.runs_used
        keeps0 = st.keeps
        kept_at_fork = False
        delta = fork["delta"]
        if epoch == "E1":
            # the fork trial's proposal is the root's; P1 pending entries created by it are restored below
            st.pending = list(fork["pending_after"])  # manager plan after proposing the fork trial (P1)
            if arm == "skip":
                st.prior_skips += 1
            else:
                st.runs_used += 1
                dhat = delta + fork["eps"]
                if arm in ("execute", "ctrl_only"):
                    mh = self.m_hat(fork["a"], fork["A"], dhat, fork["kind"])
                    self.update(st, fork["key"], fork["size"], dhat, fork["off"], fork["kind"])
                    if arm == "execute" and mh > 0:
                        self.keep(st, delta, t)
                        kept_at_fork = True
        else:  # E2: snapshot is after the run and the controller update, before the keep decision
            if arm == "keep":
                self.keep(st, delta, t)
                kept_at_fork = True
        for tt in range(t + 1, self.r.llm_cap + 1):
            self.trial(st, tt, s, theta_tab, None)
        K = self.r.K_audit
        per_seed = st.y_true + self.r.sigma_audit * audit_rng.standard_normal(K)
        term = self.r.sigma_term * audit_rng.standard_normal()
        per_seed = per_seed + term
        imm = (delta + float(np.mean(self.r.sigma_audit * audit_rng.standard_normal(K)))) if kept_at_fork else 0.0
        return {"y_terminal": float(np.mean(per_seed)), "per_seed": [float(x) for x in per_seed],
                "immediate": float(imm), "runs_used": st.runs_used - runs0, "keeps_after": st.keeps - keeps0,
                "binding": st.runs_used >= self.W, "llm_calls": self.r.llm_cap - t + 1}


def theta_table(world: World, regime: Regime, seed: int, inst: int) -> np.ndarray:
    """The node's latent θ per key for one instance (shared by roots, leaves and campaigns of that instance)."""
    rng = np.random.default_rng([seed, inst, 99])
    tab = world.mu0 + world.tau0 * rng.standard_normal(regime.llm_cap + 4 + max(world.n_keys, 0))
    # last two slots: the instance's proposal-size multiplier and rule-skip share (P0 revision 7)
    u, v = rng.random(), rng.random()
    tab[-1] = 1.0
    tab[-2] = regime.p_rule
    if world.inst_prule_spread > 0:      # diffuse: p_rule_i ~ U(p_rule − spread, p_rule + spread)
        tab[-2] = min(0.95, max(0.0, regime.p_rule + world.inst_prule_spread * (2 * v - 1)))
    elif world.inst_busy_p > 0:          # concentrated: a share of "busy" instances with many eligible proposals
        tab[-2] = max(0.0, regime.p_rule - world.inst_busy_drop) if u < world.inst_busy_p else regime.p_rule
    return tab


def _p_uniform(near: np.ndarray, target: float, p_over: float) -> float:
    lo, hi = 0.0, 1.0
    for _ in range(60):
        p = 0.5 * (lo + hi)
        e = np.where(near, p + (1 - p) * p_over, p).sum()
        lo, hi = (p, hi) if e < target else (lo, p)
    return 0.5 * (lo + hi)


def simulate(world: World, regime: Regime, seed: int = 1, *, label: str = "FIXTURE", host: str = SIM_HOST,
             node: str | None = None, meta: dict | None = None) -> tuple[list[LeafRecord], list[RootRecord]]:
    """Simulate roots and fork leaves. ``meta`` (optional) is filled with {fork_id: edit kind} for diagnostics."""
    sim = Sim(world, regime, seed)
    node = node or f"synthetic_{world.kind}"
    prov = sim_provenance(label, host)
    roots_out, cands = [], []
    thetas = {}
    for inst in range(regime.n_instances):
        theta_tab = theta_table(world, regime, seed, inst)
        thetas[inst] = theta_tab
        st, log = sim.run_root(inst, theta_tab)
        e1n = e2n = 0
        decisions = []
        for k, rec in enumerate(log):
            if rec.get("rule"):
                decisions.append({"index": rec["t"], "epoch": "E1", "action": "rule_skip", "index_value": None,
                                  "eligible": False})
                continue
            if rec.get("e1_eligible"):
                e1n += 1
                near = abs(rec["v_star"] - regime.g) <= regime.band_e1
                cands.append((inst, rec, "E1", near))
            decisions.append({"index": rec["t"], "epoch": "E1", "action": "execute" if rec.get("executed") else "skip",
                              "index_value": rec["v_star"], "eligible": bool(rec.get("e1_eligible"))})
            if rec.get("e2_eligible"):
                e2n += 1
                near = abs(rec["m_hat"]) <= regime.band_e2
                cands.append((inst, rec, "E2", near))
                decisions.append({"index": rec["t"], "epoch": "E2", "action": "keep" if rec.get("kept") else "discard",
                                  "index_value": rec["m_hat"], "eligible": True})
        roots_out.append(RootRecord(
            schema=TRACKS_ROOT_SCHEMA, node=node, instance_id=f"i{inst:03d}", root_id=f"r{inst:03d}", W=sim.W,
            llm_cap=regime.llm_cap, y_start=world.y0, y_after_trial1=None, y_terminal=float(st.y_true),
            eligible_e1=e1n, eligible_e2=e2n, binding=st.runs_used >= sim.W, runs_used=st.runs_used,
            llm_calls=regime.llm_cap, decisions=decisions, provenance=prov))
    near = np.array([c[3] for c in cands])
    target = regime.forks_per_instance * regime.n_instances
    p_u = _p_uniform(near, target, regime.p_over) if len(cands) > target else 1.0
    sel_rng = np.random.default_rng([seed, 7])
    leaves = []
    for fidx, (inst, rec, epoch, nr) in enumerate(cands):
        u1, u2, u3 = sel_rng.random(3)
        uni = u1 < p_u
        over = bool(nr and u2 < regime.p_over)
        if not (uni or over):
            continue
        p_sel = p_u + (1 - p_u) * regime.p_over if nr else p_u
        chan = bool(epoch == "E1" and u3 < regime.channel_share)
        sel = Selection(uniform=bool(uni), oversample=over, p_select=float(min(1.0, p_sel)), channel_arms=chan)
        fork_id = f"{node}/i{inst:03d}/t{rec['t']:02d}/{epoch}"
        if meta is not None:
            meta[fork_id] = rec["kind"]
        if epoch == "E1":
            arms = ["skip", "execute"] + (["ghost", "ctrl_only"] if chan else [])
            snap = rec["snap_e1"]
            state = rec["state_e1"]
            fc = Forecast(pi=0.0, mu=rec["a"], tau=math.sqrt(rec["A"]), sigma=world.sigma_cmp, v_star=rec["v_star"],
                          m_hat=None, g=regime.g)
            myo = "execute" if rec.get("executed") else "skip"
        else:
            arms = ["keep", "discard"]
            snap = rec["snap_e2"]
            state = rec["state_e2"]
            fc = Forecast(pi=0.0, mu=rec["a"], tau=math.sqrt(rec["A"]), sigma=world.sigma_cmp, v_star=rec["v_star"],
                          m_hat=rec["m_hat"], g=regime.g)
            myo = "keep" if rec.get("kept") else "discard"
        for rep in (1, 2):
            s = Stream(np.random.default_rng([seed, inst, 1000 + fidx, rep]), regime.llm_cap)
            for ai, arm in enumerate(arms):
                audit_rng = np.random.default_rng([seed, inst, 1000 + fidx, rep, 50 + ai])
                out = sim.run_leaf(snap, rec, epoch, arm, s, thetas[inst], audit_rng)
                leaves.append(LeafRecord(
                    schema=TRACKS_LEAF_SCHEMA, node=node, instance_id=f"i{inst:03d}", root_id=f"r{inst:03d}",
                    fork_id=fork_id, epoch=epoch, fork_trial_index=rec["t"], arm=arm, rep=rep,
                    llm_seed_base=int(seed * 1000 + rep), myopic_action=myo, selection=sel,
                    state={k: state[k] for k in STATE_FEATURES},
                    forecast=fc, immediate_measured=out["immediate"], y_terminal=out["y_terminal"],
                    y_terminal_per_seed=out["per_seed"], audit_seeds=list(range(regime.K_audit)),
                    runs_used=out["runs_used"], llm_calls=out["llm_calls"], keeps_after=out["keeps_after"],
                    binding=bool(out["binding"]), nf_c_events=0, dup_filtered_due_to_fork=0, next_proposals=[],
                    provenance=prov))
    return leaves, roots_out


# --------------------------------------------------------------------------------------------- planted generator
def planted_forks(*, n_instances: int = 40, forks_per_instance: int = 15, share_e1: float = 0.7,
                  budget: Callable[[dict], float] | float = 0.0, info: Callable[[dict], float] | float = 0.0,
                  feedback: Callable[[dict], float] | float = 0.0, e2_keep: Callable[[dict], float] | float = 0.0,
                  sigma: float = 0.003, index_bias: Callable[[dict, str], float] | float = 0.0,
                  channel_share: float = 1.0 / 3.0, g: float = 0.0005, seed: int = 0, node: str = "planted",
                  label: str = "FIXTURE", host: str = SIM_HOST) -> list[LeafRecord]:
    """Fork-level generator with planted channel effects (no campaign dynamics), for analysis tests.

    E1 continuations: C_skip = c0, C_ghost = c0 − B(s), C_ctrl = c0 − B(s) + I(s), C_exec = C_ctrl + F(s);
    E2: C_keep − C_discard = K(s). ``index_bias`` plants a one-step miscalibration: the true immediate
    increment is the forecast plus the bias (it enters y_terminal and immediate_measured, not C).
    """
    f = lambda v: (v if callable(v) else (lambda s, _c=v: _c))  # noqa: E731
    B, I, F, K = f(budget), f(info), f(feedback), f(e2_keep)
    bias = index_bias if callable(index_bias) else (lambda s, ep, _c=index_bias: _c)
    rng = np.random.default_rng(seed)
    prov = sim_provenance(label, host)
    leaves = []
    for inst in range(n_instances):
        for k in range(forks_per_instance):
            e1 = rng.random() < share_e1
            W = 10
            used = int(rng.integers(1, W))
            state = {"budget_fraction": used / W, "runs_left": float(W - used), "trial_index": float(rng.integers(2, 41)),
                     "key_seen": float(rng.random() < 0.3), "prior_skips": float(rng.integers(0, 8)),
                     "keeps_so_far": float(rng.integers(1, 6)), "index_value": 0.0}
            idx = float(abs(rng.normal(0.0008, 0.0008))) if e1 else float(rng.normal(0.0, 0.002))
            state["index_value"] = idx
            p_sel = 0.5 if rng.random() < 0.5 else 1.0
            chan = bool(e1 and rng.random() < channel_share)
            sel = Selection(uniform=True, oversample=p_sel < 1.0, p_select=p_sel, channel_arms=chan)
            ep = "E1" if e1 else "E2"
            fc = Forecast(pi=0.0, mu=None, tau=None, sigma=None, v_star=idx if e1 else 0.001,
                          m_hat=None if e1 else idx, g=g)
            myo = ("execute" if idx >= g else "skip") if e1 else ("keep" if idx > 0 else "discard")
            imm_true = idx + bias(state, ep)
            for rep in (1, 2):
                c0 = rng.normal(0.0, sigma)
                if e1:
                    cont = {"skip": c0, "ghost": c0 - B(state), "ctrl_only": c0 - B(state) + I(state),
                            "execute": c0 - B(state) + I(state) + F(state)}
                    arms = ["skip", "execute"] + (["ghost", "ctrl_only"] if chan else [])
                    act = "execute"
                else:
                    cont = {"discard": c0, "keep": c0 + K(state)}
                    arms = ["keep", "discard"]
                    act = "keep"
                for arm in arms:
                    c = cont[arm] + rng.normal(0.0, sigma)
                    imm = imm_true + rng.normal(0.0, 0.001) if arm == act else 0.0
                    y = 0.9 + imm + c
                    leaves.append(LeafRecord(
                        schema=TRACKS_LEAF_SCHEMA, node=node, instance_id=f"i{inst:03d}", root_id=f"r{inst:03d}",
                        fork_id=f"{node}/i{inst:03d}/f{k:02d}", epoch=ep, fork_trial_index=int(state["trial_index"]),
                        arm=arm, rep=rep, llm_seed_base=rep, myopic_action=myo, selection=sel, state=dict(state),
                        forecast=fc, immediate_measured=float(imm), y_terminal=float(y), y_terminal_per_seed=[float(y)],
                        audit_seeds=[0], runs_used=0, llm_calls=0, keeps_after=0, binding=False, nf_c_events=0,
                        dup_filtered_due_to_fork=0, next_proposals=[], provenance=prov))
    return leaves


# --------------------------------------------------------------------------------------------- campaign records
def make_campaign_root(node: str, inst: str, policy: str, rep: int, y: float, *, W: int, llm_cap: int,
                       label: str = "FIXTURE", host: str = SIM_HOST, phase: str = "campaign",
                       suffix: str = "") -> RootRecord:
    """A campaign-phase RootRecord carrying ``policy`` and ``rep`` (attributes while schema.py lacks the fields)."""
    prov = replace(sim_provenance(label, host), phase=phase)
    kw = dict(schema=TRACKS_ROOT_SCHEMA, node=node, instance_id=inst,
              root_id=f"{inst}/{policy}/rep{rep}{('/' + suffix) if suffix else ''}", W=W,
              llm_cap=llm_cap, y_start=None, y_after_trial1=None, y_terminal=float(y), eligible_e1=0, eligible_e2=0,
              binding=False, runs_used=0, llm_calls=llm_cap, decisions=[], provenance=prov)
    names = {f.name for f in fields(RootRecord)}
    extra = {"policy": policy, "rep": rep}
    kw.update({k: v for k, v in extra.items() if k in names})
    r = RootRecord(**kw)
    for k, v in extra.items():
        if k not in names:
            object.__setattr__(r, k, v)
    return r


def campaign_roots_from_values(node: str, values: dict[str, list[float]], *, label: str = "FIXTURE",
                               host: str = SIM_HOST) -> list[RootRecord]:
    """values: policy -> per-instance Y (instance k = f"c{k:04d}")."""
    out = []
    for pol, ys in values.items():
        for k, y in enumerate(ys):
            out.append(make_campaign_root(node, f"c{k:04d}", pol, 1, y, W=10, llm_cap=40, label=label, host=host))
    return out


# --------------------------------------------------------------------------------------------- threshold families
class ThresholdPolicy:
    """``static:g,h`` / ``dynamic:g0,b_budget,b_info,h0,h_budget`` with revision-6 semantics (``analyze``)."""

    def __init__(self, s: str):
        self.name = s
        self.p = A.as_dynamic(s)

    def e1(self, f: dict) -> bool:   # execute uses ≥ (runbook rev 7.1)
        g0, bb, bi, _, _, r1, tb, _ = self.p
        return f["index_value"] + bi * (f["tau_pred"] - tb) >= g0 - bb * (f["r"] - r1)

    def e2(self, f: dict) -> bool:   # keep uses >
        _, _, _, h0, hb, _, _, r2 = self.p
        return f["index_value"] > h0 - hb * (f["r"] - r2)


@dataclass
class Plan:
    """One node's S0.6 plan (illustrative defaults until S0.5/S0.7; see ``match_noise``)."""
    delta_Y: float = 0.0033
    sigma_node: float = 0.0066
    sigma_D: float = 0.008                 # pilot sd of campaign-level paired differences (S0.5b)
    m_pairs: int = 20
    n_campaign: int | None = None          # fresh instances; None -> campaign_n(σ_D,UCL, δ_Y) capped at n_max
    n_max: int = 300
    n_dev: int = 20                        # D2: static stage, 15 configurations × 20 paired dev instances
    n_dev_members: int = 40                # D2: 4 members × 40 paired dev instances
    alpha: float = 0.05

    @property
    def n_planned(self) -> int:
        return self.n_campaign or A.campaign_n(A.sigma_D_ucl(self.sigma_D, self.m_pairs), self.delta_Y)

    @property
    def n(self) -> int:
        """S3e n: min(n_planned, n_max); a capped node runs at n_max (MDE reported)."""
        return min(self.n_planned, self.n_max)


def sigma_campaign_for(sigma_D: float, regime: Regime) -> float:
    """Per-campaign noise so that sd(D) ≈ σ_D when two policies agree: σ_D² ≈ 2(σ_aud²/K + σ_c²)."""
    return float(math.sqrt(max(0.0, sigma_D ** 2 / 2 - regime.sigma_audit ** 2 / regime.K_audit)))


def dev_between_config_sd(world: World, regime: Regime, plan: Plan, seed: int = 77) -> float:
    """Mean over static-grid configuration pairs of sd_i(Y_c(i) − Y_c'(i)) on paired dev instances."""
    sim = Sim(world, regime, seed)
    cfgs = A.FamilyDecl().static_configs(plan.sigma_node)
    Y = np.array([[sim.run_campaign(theta_table(world, regime, seed, i), ThresholdPolicy(c), [seed, i, 5000],
                                    np.random.default_rng([seed, i, zlib.crc32(c.encode())]))
                   for i in range(max(plan.n_dev, 20))] for c in cfgs])
    sds = [np.std(Y[a] - Y[b], ddof=1) for a in range(len(cfgs)) for b in range(a + 1, len(cfgs))]
    return float(np.mean(sds))


def pilot_between_policy_sd(world: World, regime: Regime, plan: Plan, *, n_inst: int = 40, seed: int = 78) -> float:
    """The S0.5 pilot's between-policy sd: sd over instances of Y(A2-U at g = 0.1 σ) − Y(A2-U at g = 0.3 σ), each
    instance run under both prices at W = cap (pilot regime), paired by instance."""
    reg = replace(regime, W=regime.llm_cap)
    sim = Sim(world, reg, seed)
    a, b = A2UPolicy(0.1 * plan.sigma_node), A2UPolicy(0.3 * plan.sigma_node)
    D = [sim.run_campaign(theta_table(world, reg, seed, i), a, [seed, i, 5100], np.random.default_rng([seed, i, 1]))
         - sim.run_campaign(theta_table(world, reg, seed, i), b, [seed, i, 5100], np.random.default_rng([seed, i, 2]))
         for i in range(n_inst)]
    return float(np.std(D, ddof=1))


def _bisect_sigma_campaign(regime: Regime, target: float, measure) -> float:
    lo, hi = 0.0, max(0.05, 4 * target)
    for _ in range(18):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if measure(replace(regime, sigma_campaign=mid)) < target else (lo, mid)
    return 0.5 * (lo + hi)


def match_noise(regime: Regime, plan: Plan, *, sigma_D: float | None = None, pilot_D: list[float] | None = None,
                between_policy_sd: float | None = None, dev_between_sd: float | None = None,
                sigma_d: float | None = None, world: World | None = None) -> tuple[Regime, dict]:
    """Set the simulator's campaign noise σ_campaign from measured values (runbook rev 7.1 S0.6), in order of
    precedence: dev_between_sd (the S0.7 dev between-configuration sd; the post-S0.7 re-run), between_policy_sd
    (the S0.5 pilot's between-policy sd: the first S0.6 run), sigma_D / pilot_D (campaign-level paired differences
    via ``sigma_campaign_for``). sigma_d: rep-averaged fork ΔQ sd -> σ_term (fork leaves)."""
    rec: dict = {}
    w = world or make_world("N0")
    if pilot_D is not None:
        sigma_D = float(np.std(pilot_D, ddof=1))
        rec["m_pairs"] = len(pilot_D)
    if dev_between_sd is not None:
        regime = replace(regime, sigma_campaign=_bisect_sigma_campaign(
            regime, dev_between_sd, lambda reg: dev_between_config_sd(w, reg, plan)))
        rec["matched_to"] = "dev between-configuration sd (post-S0.7 re-run)"
        rec["dev_between_sd"] = dev_between_sd
    elif between_policy_sd is not None:
        regime = replace(regime, sigma_campaign=_bisect_sigma_campaign(
            regime, between_policy_sd, lambda reg: pilot_between_policy_sd(w, reg, plan)))
        rec["matched_to"] = "S0.5 pilot between-policy sd"
        rec["between_policy_sd"] = between_policy_sd
    elif sigma_D is not None:
        regime = replace(regime, sigma_campaign=sigma_campaign_for(sigma_D, regime))
        rec["matched_to"] = "campaign-level σ_D"
        rec["sigma_D"] = sigma_D
    if sigma_d is not None:
        regime = replace(regime, sigma_term=calibrate_sigma_term(w, regime, sigma_d))
        rec["sigma_d"] = sigma_d
    rec.update(sigma_campaign=regime.sigma_campaign, sigma_term=regime.sigma_term)
    return regime, rec


def calibrate_sigma_term(world: World, regime: Regime, sigma_d_target: float, seed: int = 11) -> float:
    """σ_term so that the sd of rep-averaged fork ΔQ matches ``sigma_d_target`` (adds σ_term² to its variance)."""
    lv, rt = simulate(world, replace(regime, sigma_term=0.0), seed, node="calib")
    ft = A.build_fork_table("calib", lv, rt)
    base = float(np.sqrt(np.cov(ft.qbar, aweights=ft.w)))
    return float(math.sqrt(max(0.0, sigma_d_target ** 2 - base ** 2)))


def sim_predeclaration(node: str, plan: Plan, *, seed: int = 20261029, families: A.FamilyDecl | None = None,
                       tuning: dict | None = None) -> A.Predeclaration:
    # in the simulator the grid unit σ_cmp,vary equals plan.sigma_node
    nd = A.NodeDecl(node, "primary", plan.delta_Y, sigma_node=plan.sigma_node,
                    sizing=A.SizingDecl(A.sigma_D_ucl(plan.sigma_D, plan.m_pairs), plan.n_max),
                    sigma_cmp_vary=plan.sigma_node)
    return A.Predeclaration(nodes={node: nd}, primary_nodes=[node], seed=seed, alpha=plan.alpha,
                            fallback_active=True, winners_curse_splits=50, families=families or A.FamilyDecl(),
                            tuning=tuning or {"procedure": "argmax", "n_dev": plan.n_dev_members})


def measured_k_n(roots: list[RootRecord]) -> float:
    return float(np.mean([r.eligible_e1 + r.eligible_e2 for r in roots]))


def _campaign_root(sim, node, inst, c, rep, theta, stream, noise, *, phase, label, host, suffix="", log=False):
    dec = [] if log else None
    y = sim.run_campaign(theta, ThresholdPolicy(c), stream, noise, decisions=dec)
    r = make_campaign_root(node, inst, c, rep, y, W=sim.W, llm_cap=sim.r.llm_cap, label=label, host=host,
                           phase=phase, suffix=suffix)
    if dec:
        r.decisions.extend(dec)
    return r


def run_s3e(world: World, regime: Regime, plan: Plan, seed: int, *, label: str = "FIXTURE",
            host: str = SIM_HOST) -> dict:
    """D2 tuning (15 statics × plan.n_dev paired dev instances, the one edge extension, then the 4 centred members
    anchored at m* × plan.n_dev_members), then fresh campaigns on plan.n instances: π* and m* (rep 1, same seeds),
    the exact placebo (m* again at rep 1, 10 instances), the descriptive placebo (m* at rep 2, 15 instances),
    matched static (all n) and the other members (30 instances)."""
    node = f"synthetic_{world.kind}"
    sim = Sim(world, regime, seed)
    fam = A.FamilyDecl()
    pd = sim_predeclaration(node, plan, seed=seed)
    dev: list[RootRecord] = []

    def run_dev(cfgs, log=False):
        for c in cfgs:
            for i in range(plan.n_dev):
                dev.append(_campaign_root(sim, node, f"d{i:04d}", c, 1, theta_table(world, regime, seed, i),
                                          [seed, i, 5000], np.random.default_rng([seed, i, zlib.crc32(c.encode())]),
                                          phase="dev_tuning", label=label, host=host, log=log))

    run_dev(fam.static_configs(plan.sigma_node), log=True)
    sel = A.selection_report(dev, pd, pd.nodes[node])
    if sel["status"] == "extension_needed":
        run_dev(sel["extension_configs"], log=True)
        sel = A.selection_report(dev, pd, pd.nodes[node])
    while sel["status"] == "members_needed":
        for c, inst in sel["missing_members"]:
            i = int(inst[1:])
            dev.append(_campaign_root(sim, node, inst, c, 1, theta_table(world, regime, seed, i), [seed, i, 5000],
                                      np.random.default_rng([seed, i, zlib.crc32(c.encode())]),
                                      phase="dev_tuning", label=label, host=host, log=True))
        sel = A.selection_report(dev, pd, pd.nodes[node])
    pi_s, m_s, ms = sel["pi_star"], sel["m_star"], sel["matched_static"]["policy"]
    fresh = []
    for k in range(plan.n):
        inst = 100000 + k
        th = theta_table(world, regime, seed, inst)
        runs = [(pi_s, 1, ""), (m_s, 1, "")]
        if k < 15:                       # descriptive placebo: m* at a second LLM repetition on >= 15 instances
            runs.append((m_s, 2, ""))
        if k < 10:                       # exact placebo: m* again at the same repetition on 10 instances
            runs.append((m_s, 1, "dup"))
        if ms not in (pi_s, m_s):        # matched static on all n instances
            runs.append((ms, 1, ""))
        if k < 30:                       # the other channels' members on a declared subset of 30 instances
            runs += [(c, 1, "") for c in sel["members"].values() if c != pi_s]
        for c, rep, suf in runs:
            fresh.append(_campaign_root(sim, node, f"c{k:04d}", c, rep, th, [seed, inst, 6000, rep],
                                        np.random.default_rng([seed, inst, rep, zlib.crc32(c.encode())]),
                                        phase="campaign",
                                        label=label, host=host, suffix=suf))
    res = A.analyze_s3e(node, dev, fresh, pd.nodes[node], pd)
    return {"result": res, "dev_roots": dev, "fresh_roots": fresh}


# --------------------------------------------------------------------------------------------- oracle gains
def oracle_gain(world: World, regime: Regime, plan: Plan, *, n_oracle: int = 10_000, seed: int = 9000,
                family: A.FamilyDecl | None = None, n_centre: int = 400) -> dict:
    """Noiseless large-replication oracle: m*_o = best static (with the edge extension); members anchored at m*_o
    and centred at m*_o's decision means (from n_centre instances); gain = best member − m*_o."""
    sim = Sim(world, regime, seed)
    fam = family or A.FamilyDecl()
    th = [theta_table(world, regime, seed, 400000 + i) for i in range(n_oracle)]

    def ev(c, dec=None, n=n_oracle):
        pol = ThresholdPolicy(c)
        return np.array([sim.run_campaign(th[i], pol, [seed, 400000 + i, 8000], None, noiseless=True,
                                          decisions=dec if (dec is not None and i < n_centre) else None)
                         for i in range(n)])

    stat = {c: ev(c) for c in fam.static_configs(plan.sigma_node)}
    best = max(stat, key=lambda c: (stat[c].mean(), -A.complexity_key(c)[0]))
    extended = False
    if fam.on_upper_edge(best, plan.sigma_node):
        stat.update({c: ev(c) for c in fam.extension_configs(plan.sigma_node)})
        best, extended = max(stat, key=lambda c: stat[c].mean()), True
    dec: list = []
    ev(best, dec, n=min(n_centre, n_oracle))
    centres = A.decision_centres(dec)
    members = fam.members(best, plan.sigma_node, centres)
    mem = {name: ev(c) for name, c in members.items()}
    top = max(mem, key=lambda k: mem[k].mean())
    d = mem[top] - stat[best]
    return {"gain": float(d.mean()), "gain_se": float(d.std(ddof=1) / math.sqrt(n_oracle)), "m_oracle": best,
            "member_oracle": top, "pi_oracle": members[top], "extended": extended, "centres": centres,
            "member_gains": {k: float((v - stat[best]).mean()) for k, v in mem.items()},
            "static_means": {k: float(v.mean()) for k, v in stat.items()}, "n_oracle": n_oracle}


def calibrate_strength(kind: str, variant: str, regime: Regime, plan: Plan, *, grid: Sequence[float],
                       n_cal: int = 600, n_oracle: int = 10_000, tol: float = 0.05, iters: int = 0,
                       refine: int = 6, family: A.FamilyDecl | None = None, world_kw: dict | None = None) -> dict:
    """Fix the best member's oracle gain at δ_Y: scan ``grid`` at n_cal for the first upward crossing (the gain is
    not monotone over the whole range), then bisect that grid bracket at n_oracle (all evaluations share instances
    and seeds) until |gain − δ_Y| ≤ tol·δ_Y or ``refine`` steps are spent. The bracket is re-checked at n_oracle
    and widened to the next grid point if the coarse scan misplaced the crossing."""
    target, trace = plan.delta_Y, []

    def gain(st, n):
        g = oracle_gain(make_world(kind, st, variant, **(world_kw or {})), regime, plan, n_oracle=n, family=family)
        trace.append((st, n, g["gain"], g["gain_se"]))
        return g

    grid = list(grid)
    hit = None
    for j, st in enumerate(grid):
        if gain(st, n_cal)["gain"] >= target:
            hit = j
            break
    if hit is None:
        return {"kind": kind, "variant": variant, "strength": None, "trace": trace, "within_tolerance": False,
                "note": f"no grid strength reached an oracle gain of δ_Y = {target} at n = {n_cal}"}
    j_lo, j_hi = max(0, hit - 1), hit
    g_hi = gain(grid[j_hi], n_oracle)
    while g_hi["gain"] < target and j_hi + 1 < len(grid):
        j_lo, j_hi = j_hi, j_hi + 1
        g_hi = gain(grid[j_hi], n_oracle)
    lo, hi, st, g = grid[j_lo], grid[j_hi], grid[j_hi], g_hi
    for _ in range(refine):
        if abs(g["gain"] - target) <= tol * target or lo == hi:
            break
        mid = 0.5 * (lo + hi)
        gm = gain(mid, n_oracle)
        if abs(gm["gain"] - target) < abs(g["gain"] - target):
            st, g = mid, gm
        lo, hi = (lo, mid) if gm["gain"] >= target else (mid, hi)
    return {"kind": kind, "variant": variant, "strength": st, "oracle": g, "planted_gain": g["gain"],
            "within_tolerance": bool(abs(g["gain"] - target) <= tol * target), "tolerance": tol * target,
            "trace": trace}


# --------------------------------------------------------------------------------------------- replication
def _rate(k: int, n: int) -> dict:
    lo, hi = A.clopper_pearson(k, n)
    return {"k": k, "n": n, "rate": k / n if n else float("nan"), "ci95_clopper_pearson": [lo, hi]}


def replicate(world: World, regime: Regime, plan: Plan, R: int, seed0: int = 1000, *,
              oracle: dict | None = None) -> dict:
    """R end-to-end replicates (D2 tuning + S3e through ``analyze``); route rates with Clopper–Pearson CIs,
    P(correct member), realised gain, flip rate."""
    outs = []
    for r in range(R):
        res = run_s3e(world, regime, plan, seed0 + r)["result"]
        t = res["test"]
        outs.append({"route": res["route_single_node"], "mean": t["mean"], "lb": t["lb"], "ub": t["ub"],
                     "ci": t["ci_two_sided"], "pi": res["pi_star"], "member": res["selection"]["pi_star_member"],
                     "m": res["m_star"], "flip": res["selection"]["flip"]["flip_rate"],
                     "z": res["placebo_descriptive"].get("z"), "exact": res["placebo_exact"]["status"]})
    kA = sum(o["route"] in ("A", "A-small") for o in outs)
    out = {"world": asdict(world), "plan": asdict(plan) | {"n": plan.n, "n_planned": plan.n_planned}, "R": R,
           "k_A": kA, "route_A_or_A_small": _rate(kA, R),
           "route_A_small": _rate(sum(o["route"] == "A-small" for o in outs), R),
           "no_gain_found": _rate(sum(o["route"] == "no gain found" for o in outs), R),
           "exact_placebo_not_pass": sum(o["exact"] != "pass" for o in outs),
           "placebo_abs_z_gt_3_5": sum(abs(o["z"] or 0) > 3.5 for o in outs),
           "realised_gain_mean_D": float(np.mean([o["mean"] for o in outs])),
           "ub95_mean": float(np.mean([o["ub"] for o in outs])),
           "flip_rate_mean": float(np.mean([o["flip"] or 0 for o in outs])),
           "member_choices": {c: sum(o["member"] == c for o in outs) for c in sorted({o["member"] for o in outs})}}
    if oracle is not None:
        out["p_correct_member"] = _rate(sum(o["member"] == oracle["member_oracle"] for o in outs), R)
        out["p_correct_m_star"] = _rate(sum(o["m"] == oracle["m_oracle"] for o in outs), R)
        out["p_correct_both"] = _rate(sum(o["member"] == oracle["member_oracle"] and o["m"] == oracle["m_oracle"]
                                          for o in outs), R)
    out["runs"] = outs
    return out


S06_CAL_GRIDS = {"P2+": (0.002, 0.004, 0.006, 0.008, 0.01, 0.012, 0.016, 0.02),
                 "P1": (4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 20.0)}


def s06_node(node: str, regime: Regime, plan: Plan, *, R: int = 200, n_cal: int = 600, n_oracle: int = 10_000,
             cache: dict | None = None) -> tuple[dict, dict]:
    """Runbook rev 7.1 S0.6 for one decision node (D2 design, S3e at plan.n): N0 (STOP iff ≥ 19 of 200), P2+ diffuse
    and concentrated at δ_Y, P1-diffuse at 2 δ_Y. Power (Clopper–Pearson), P(correct member), realised gain and the
    achieved oracle gain are reported, not gated; P0, P2− and P1-concentrated are listed as unmeasured.
    ``cache`` may hold earlier calibrations ({(kind, variant): calibration}) so a noise re-run reuses them."""
    rep: dict = {"node": node, "plan": asdict(plan) | {"n": plan.n, "n_planned": plan.n_planned},
                 "regime": asdict(regime), "unmeasured_sensitivity": list(A.S06_UNMEASURED)}
    n0w = make_world("N0")
    n0o = oracle_gain(n0w, regime, plan, n_oracle=n_oracle)
    n0r = replicate(n0w, regime, plan, R, 1000, oracle=n0o)
    rep["N0"] = {k: v for k, v in n0r.items() if k != "runs"} | {
        "oracle": n0o, "oracle_le_0_within_tol": bool(n0o["gain"] <= 0.05 * plan.delta_Y),
        "fp_gate": A.fp_gate(n0r["k_A"], R, alpha=plan.alpha)}
    ctl: dict = {"n": plan.n, "N0": {"R": R, "k_A": n0r["k_A"], "oracle_gain": n0o["gain"]},
                 "unmeasured": list(A.S06_UNMEASURED)}
    cache = cache if cache is not None else {}
    for kind, variant, mult in A.S06_CONTROLS:
        key = (kind, variant)
        if key not in cache:
            cache[key] = calibrate_strength(kind, variant, regime, replace(plan, delta_Y=mult * plan.delta_Y),
                                            grid=S06_CAL_GRIDS[kind], n_cal=n_cal, n_oracle=n_oracle)
        cal = cache[key]
        entry: dict = {"calibration": {k: v for k, v in cal.items() if k != "trace"}, "planted_multiple": mult}
        if cal["strength"] is None:
            best = max(cal["trace"], key=lambda x: x[2]) if cal["trace"] else None
            entry["note"] = "not calibratable at this n / noise; reported as unmeasured"
            entry["max_achieved_oracle_gain"] = ({"strength": best[0], "n": best[1], "gain": best[2],
                                                  "gain_in_target_units": best[2] / (mult * plan.delta_Y)}
                                                 if best else None)
            entry["trace"] = cal["trace"]
            rep[f"{kind}_{variant}"] = entry
            ctl.setdefault(kind, {})[variant] = {"calibrated": False, "planted_multiple": mult,
                                                 "target_gain": mult * plan.delta_Y,
                                                 "max_achieved_oracle_gain": best[2] if best else None}
            continue
        r = replicate(make_world(kind, cal["strength"], variant), regime, plan, R, 5000, oracle=cal["oracle"])
        entry["replication"] = {k: v for k, v in r.items() if k != "runs"}
        entry["power"] = A.power_report(r["k_A"], R)
        rep[f"{kind}_{variant}"] = entry
        ctl.setdefault(kind, {})[variant] = {
            "R": R, "k_A": r["k_A"], "planted_multiple": mult, "target_gain": mult * plan.delta_Y,
            "achieved_oracle_gain": cal["planted_gain"], "planted_gain": cal["planted_gain"],
            "within_tolerance": cal["within_tolerance"], "strength": cal["strength"],
            "p_correct_selection": r["p_correct_member"]["rate"], "realised_gain": r["realised_gain_mean_D"]}
    return rep, ctl


# --------------------------------------------------------------------------------------------- design study (rev. 7)
class SchedulePolicy:
    """Unrestricted-oracle proxy: execute iff V̂* > G[r-tercile][τ-half]; keep iff m̂ > H[r-tercile]
    (r = runs remaining fraction; τ split at ``tau_split``). 9 free thresholds."""

    def __init__(self, G, H, tau_split: float):
        self.G, self.H, self.ts = [list(g) for g in G], list(H), tau_split
        self.name = f"schedule:{G}|{H}"

    @staticmethod
    def rb(f):
        r = 1.0 - f["budget_fraction"]
        return 0 if r > 2 / 3 else (1 if r > 1 / 3 else 2)

    def e1(self, f):
        return f["index_value"] > self.G[self.rb(f)][1 if f["tau_pred"] > self.ts else 0]

    def e2(self, f):
        return f["index_value"] > self.H[self.rb(f)]


def schedule_oracle(world: World, regime: Regime, plan: Plan, *, n_search: int = 400, n_verify: int = 2000,
                    sweeps: int = 2, seed: int = 9100) -> dict:
    """Coordinate-descent search of the 9-threshold schedule from the best static rule (noiseless, common random
    numbers); the gain over the best static is re-measured on n_verify fresh oracle instances."""
    sim = Sim(world, regime, seed)
    sn = plan.sigma_node
    fam = A.FamilyDecl()

    def value(pol, n, off):
        return np.array([sim.run_campaign(theta_table(world, regime, seed, off + i), pol, [seed, off + i, 8100], None,
                                          noiseless=True) for i in range(n)])

    stat = {c: value(ThresholdPolicy(c), n_search, 500000).mean()
            for c in fam.static_configs(sn, extended=True)}
    best = max(stat, key=stat.get)
    g, h = A.parse_policy(best)[1]
    dec: list = []
    sim.run_campaign(theta_table(world, regime, seed, 500000), ThresholdPolicy(best), [seed, 500000, 8100], None,
                     noiseless=True, decisions=dec)
    for i in range(1, 60):
        sim.run_campaign(theta_table(world, regime, seed, 500000 + i), ThresholdPolicy(best), [seed, 500000 + i, 8100],
                         None, noiseless=True, decisions=dec)
    taus = [d["tau_pred"] for d in dec if d["epoch"] == "E1"]
    ts = float(np.median(taus)) if taus else 0.0
    G, H = [[g, g] for _ in range(3)], [h, h, h]
    g_vals = [u * sn for u in (-0.5, -0.25, 0.0, 0.05, 0.1, 0.2, 0.4, 0.8, 1.6)]
    h_vals = [u * sn for u in (-1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0, 2.0, 4.0)]
    cur = value(SchedulePolicy(G, H, ts), n_search, 500000).mean()
    for _ in range(sweeps):
        for k in range(9):
            vals = g_vals if k < 6 else h_vals
            for v in vals:
                G2, H2 = [list(x) for x in G], list(H)
                if k < 6:
                    G2[k // 2][k % 2] = v
                else:
                    H2[k - 6] = v
                y = value(SchedulePolicy(G2, H2, ts), n_search, 500000).mean()
                if y > cur + 1e-12:
                    cur, G, H = y, G2, H2
    a = value(SchedulePolicy(G, H, ts), n_verify, 600000)
    b = value(ThresholdPolicy(best), n_verify, 600000)
    d = a - b
    return {"gain": float(d.mean()), "gain_se": float(d.std(ddof=1) / math.sqrt(n_verify)), "m_oracle": best,
            "G": G, "H": H, "tau_split": ts, "search_gain": float(cur - stat[best]), "n_verify": n_verify}


FAMILIES = {"fixed": A.FamilyDecl(member_units={k: list(v) for k, v in A.FIXED_MEMBER_UNITS.items()}),
            "grid": A.FamilyDecl(member_units={k: list(v) for k, v in A.GRID_MEMBER_UNITS.items()})}
DESIGNS = {  # name: (family, tuning)
    "D1 fixed-4, argmax n=20": ("fixed", {"procedure": "argmax", "n_dev": 20}),
    "D2 fixed-4, argmax n=40": ("fixed", {"procedure": "argmax", "n_dev": 40}),
    "D3 grid-12, argmax n=20": ("grid", {"procedure": "argmax", "n_dev": 20}),
    "D4 grid-12, halving 340": ("grid", {"procedure": "halving", "member_budget": 340}),
    "D5 grid-12, channel-first 20/60": ("grid", {"procedure": "channel_first", "n1": 20, "n2": 60}),
}


def study_replicate(world: World, regime: Regime, plan: Plan, seed: int, designs: dict, oracle: dict | None = None,
                    n_static_dev: int = 20) -> dict:
    """One replicate of tuning + S3e for several designs sharing the static stage, the dev instances and the fresh
    instances (each policy is run once per instance and cached)."""
    sim = Sim(world, regime, seed)
    sn = plan.sigma_node
    fam0 = A.FamilyDecl()
    dev_cache, dec_cache = {}, {}

    def dev_y(c, k):
        if (c, k) not in dev_cache:
            dec = [] if k < n_static_dev else None
            dev_cache[(c, k)] = sim.run_campaign(theta_table(world, regime, seed, k), ThresholdPolicy(c),
                                                 [seed, k, 5000], np.random.default_rng([seed, k, zlib.crc32(c.encode())]),
                                                 decisions=dec)
            if dec is not None:
                dec_cache.setdefault(c, []).extend(dec)
        return dev_cache[(c, k)]

    statics = fam0.static_configs(sn)
    vals = np.array([np.mean([dev_y(c, k) for k in range(n_static_dev)]) for c in statics])
    m_s = statics[A._argmax_simplest(statics, vals)]
    static_campaigns = len(statics) * n_static_dev
    if fam0.on_upper_edge(m_s, sn):
        ext = fam0.extension_configs(sn)
        statics = statics + ext
        vals = np.array([np.mean([dev_y(c, k) for k in range(n_static_dev)]) for c in statics])
        m_s = statics[A._argmax_simplest(statics, vals)]
        static_campaigns += len(ext) * n_static_dev
    centres = A.decision_centres(dec_cache[m_s])
    fresh_cache = {}

    def fresh_y(c, k):
        if (c, k) not in fresh_cache:
            inst = 100000 + k
            fresh_cache[(c, k)] = sim.run_campaign(theta_table(world, regime, seed, inst), ThresholdPolicy(c),
                                                   [seed, inst, 6000, 1],
                                                   np.random.default_rng([seed, inst, 1, zlib.crc32(c.encode())]))
        return fresh_cache[(c, k)]

    m_o = next((o.get("m_oracle") for o in (oracle or {}).values() if isinstance(o, dict)), None)
    out = {"m_star": m_s, "static_campaigns": static_campaigns, "m_star_correct": m_o == m_s, "designs": {}}
    for dname, (fname, tuning) in designs.items():
        members = FAMILIES[fname].members(m_s, sn, centres)
        t = A.tune_members(lambda p, k: dev_y(p, k), members, tuning)
        pi = t["policy"]
        for k in range(n_static_dev):
            dev_y(pi, k)
        flips = []
        for d in dec_cache.get(pi, []):
            st = {"budget_fraction": d["budget_fraction"], "index_value": d["index_value"]}
            flips.append(A.threshold_act(m_s, st, d["epoch"], d.get("tau_pred")) != (d["action"] in ("execute", "keep")))
        D = np.array([fresh_y(pi, k) - fresh_y(m_s, k) for k in range(plan.n)])
        test = A.mean_test(D, alpha=plan.alpha)
        o = (oracle or {}).get(fname)
        out["designs"][dname] = {
            "winner": t["winner"], "campaigns": static_campaigns + t["campaigns"], "mean_D": test["mean"],
            "lb": test["lb"], "ub": test["ub"], "route": A.campaign_route(test, plan.delta_Y),
            "flip": float(np.mean(flips)) if flips else 0.0,
            "correct_member": bool(o is not None and t["winner"] == o["member_oracle"]),
            "correct_both": bool(o is not None and t["winner"] == o["member_oracle"] and m_s == o["m_oracle"])}
    return out


def study_world(world: World, regime: Regime, plan: Plan, R: int, designs: dict, oracle: dict | None,
                seed0: int = 20000) -> dict:
    reps = [study_replicate(world, regime, plan, seed0 + r, designs, oracle) for r in range(R)]
    res = {}
    for d in designs:
        rows = [x["designs"][d] for x in reps]
        kA = sum(r["route"] in ("A", "A-small") for r in rows)
        kB = sum(r["route"] == "B" and r["flip"] >= 0.10 for r in rows)
        kU = sum(r["ub"] < plan.delta_Y for r in rows)
        kF = sum(r["flip"] >= 0.10 for r in rows)
        res[d] = {"R": R, "k_A": kA, "route_A": _rate(kA, R), "P_B": _rate(kB, R), "P_ub_below": _rate(kU, R),
                  "P_flip_ge_10": _rate(kF, R),
                  "P_correct_member": _rate(sum(r["correct_member"] for r in rows), R),
                  "P_correct_both": _rate(sum(r["correct_both"] for r in rows), R),
                  "realised_gain_mean_D": float(np.mean([r["mean_D"] for r in rows])),
                  "campaigns_mean": float(np.mean([r["campaigns"] for r in rows])),
                  "campaigns_max": int(max(r["campaigns"] for r in rows)),
                  "flip_mean": float(np.mean([r["flip"] for r in rows]))}
    res["_m_star_correct"] = _rate(sum(x["m_star_correct"] for x in reps), R)
    return res


def merge_controls(per_node: dict[str, dict], label: str = "FIXTURE") -> dict:
    return {"schema": "tracks_controls/v2", "label": label, "source": "simulate_controls (not the collector)",
            "nodes": per_node}


def write_node(out_dir: Path, leaves=(), roots=(), dev_roots=(), campaign_roots=(), *, manifest: dict | None = None):
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, recs in (("leaves.jsonl", leaves), ("roots.jsonl", roots), ("dev_roots.jsonl", dev_roots),
                       ("campaign_roots.jsonl", campaign_roots)):
        if recs:
            with (out_dir / name).open("w") as fh:
                for rec in recs:
                    fh.write(json.dumps(A.record_to_dict(rec)) + "\n")
    (out_dir / "manifest.json").write_text(json.dumps(manifest or {"label": "FIXTURE", "phase": "synthetic"}, indent=2))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Track S S0.6 synthetic calibration, runbook rev 7.1 (FIXTURE; not evidence)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--node", default="digits_mlp", help="the decision node this S0.6 run is for")
    ap.add_argument("--delta-Y", type=float, default=0.0033)
    ap.add_argument("--sigma-unit", type=float, default=0.0066, help="σ_cmp,vary, the grid unit")
    ap.add_argument("--sigma-D", type=float, default=0.008, help="pilot campaign-level σ_D (S0.5b) for n")
    ap.add_argument("--between-policy-sd", type=float, default=None,
                    help="S0.5 pilot between-policy sd (first S0.6 run)")
    ap.add_argument("--dev-between-sd", type=float, default=None,
                    help="S0.7 dev between-configuration sd (the post-S0.7 re-run)")
    ap.add_argument("--m-pairs", type=int, default=20)
    ap.add_argument("--n-campaign", type=int, default=None, help="final S3e n (default: sizing helper)")
    ap.add_argument("--n-max", type=int, default=300)
    ap.add_argument("--W", type=int, default=10)
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--n-cal", type=int, default=600)
    ap.add_argument("--n-oracle", type=int, default=10_000)
    args = ap.parse_args(argv)
    plan = Plan(delta_Y=args.delta_Y, sigma_node=args.sigma_unit, sigma_D=args.sigma_D, m_pairs=args.m_pairs,
                n_campaign=args.n_campaign, n_max=args.n_max)
    regime, noise = match_noise(Regime(W=args.W), plan, sigma_D=args.sigma_D,
                                between_policy_sd=args.between_policy_sd, dev_between_sd=args.dev_between_sd)
    rep, ctl = s06_node(args.node, regime, plan, R=args.reps, n_cal=args.n_cal, n_oracle=args.n_oracle)
    rep["noise_matching"] = noise
    ctl["noise_matching"] = noise
    args.out.mkdir(parents=True, exist_ok=True)
    tag = "post_s07" if args.dev_between_sd is not None else "pre_s07"
    (args.out / f"controls_{args.node}_{tag}.json").write_text(json.dumps(merge_controls({args.node: ctl}), indent=2,
                                                                          default=A._json_default))
    (args.out / f"s06_report_{args.node}_{tag}.json").write_text(json.dumps(rep, indent=2, default=A._json_default))
    ex = run_s3e(make_world("N0"), regime, plan, seed=777)
    write_node(args.out / "synthetic_N0", dev_roots=ex["dev_roots"], campaign_roots=ex["fresh_roots"])
    print(json.dumps(ctl, default=A._json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
