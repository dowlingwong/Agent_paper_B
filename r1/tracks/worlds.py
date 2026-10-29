"""Track S synthetic worlds (runbook rev. 7): the analysis simulator's world mechanisms, for the real collector.

AI-assisted (Claude, 29 Oct 2026). ENGINEERING_ONLY. This module re-implements, for the synthetic control
nodes that run through the real harness loop (``r1.tracks.synthetic``), the world model of the analysis
branch's simulator (``r1/tracks/simulate_controls.py``: ``World``, ``VARIANTS``, ``Stream``, ``theta_table``,
``Sim.propose`` / ``theta`` / ``fb_scale`` / ``forecast`` / ``update``). It is a port, not an import: the
collector must not depend on the analysis module. ``r1/tests/test_tracks_worlds.py`` checks that the two agree
exactly (same campaign values and decisions) on the calibrated control worlds.

Campaign model (raw metric units): ``llm_cap`` trials; a share p_rule of proposals is rule-detectable (here: a
structured no-op edit, which the harness rejects before any run); trial 1 is executed and kept. A proposal edits
world key j with size s; its true increment is delta = s (theta_j - offset) + sigma_eta eta, measured as
delta_hat = delta + sig(kind) eps. Increments add to the incumbent. The controller's model (A2-U, keyed mode,
``a2u.KEYED_MODEL``): per key a conjugate normal posterior on theta_j from N(mu0, tau0^2); forecast
a = s (mu_j - offset), A = s^2 var_j + sigma_eta^2; V* = E[max(m_hat, 0)]; tau_pred = sqrt(A).

Worlds: N0 (fresh keys, non-binding W), P0 (theta mean drifts over trials: budget channel), P1 (recurring
filler keys; probes open fresh keys and schedule large follow-ups: information channel), P2+ / P2- (a keep
shifts the theta mean of later proposals by +- strength x scale(r): keep-feedback channel), each P world with
the ``diffuse`` and ``concentrated`` variants of ``VARIANTS``. Calibrated controls (rev. 7): N0, P2+ (both
variants), P1-diffuse; P0 and P2- are implemented but are not controls.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field, fields, replace

import numpy as np

_SQRT2 = math.sqrt(2.0)
_SQRT2PI = math.sqrt(2.0 * math.pi)

WORLD_KINDS = ("N0", "B0", "P0", "P1", "P2")
CONTROL_WORLDS = (("N0", None), ("P2+", "diffuse"), ("P2+", "concentrated"), ("P1", "diffuse"))
RULE = "rule"


@dataclass(frozen=True)
class World:
    """World parameters (field names and defaults as the analysis simulator's ``World``)."""

    kind: str = "N0"
    strength: float = 0.0
    mu0: float = -0.0005
    tau0: float = 0.004
    sigma_eta: float = 0.002
    sigma_cmp: float = 0.0066
    size_filler: float = 1.0
    size_sd: float = 0.6
    size_probe: float = 1.0
    probe_offset: float = 1.5
    p_probe: float = 0.25
    n_follow: int = 2
    sigma_probe: float | None = None
    sigma_follow: float | None = None
    follow_offset: float = 0.0
    probe_max_trial: int = 40
    n_keys: int = 0
    fb_early_bf: float | None = None
    fb_shape: str = "const"
    fb_sign: float = 1.0
    fb_r_cut: float | None = None
    p_big: float = 0.0
    trend_shape: str | None = None
    trend_window: int = 8
    trend_late: float = 0.0
    inst_prule_spread: float = 0.0
    inst_busy_p: float = 0.0
    inst_busy_drop: float = 0.0
    fb_accum: bool = False
    lag_min: int = 2
    lag_max: int = 5
    fb_len: int = 3
    y0: float = 0.90

    def __post_init__(self) -> None:
        if self.kind not in WORLD_KINDS:
            raise ValueError(f"unknown world {self.kind!r}")

    def sig(self, kind: str) -> float:
        """Measurement sd by edit kind (known to the controller)."""
        if kind == "probe" and self.sigma_probe is not None:
            return float(self.sigma_probe)
        if kind == "follow" and self.sigma_follow is not None:
            return float(self.sigma_follow)
        return float(self.sigma_cmp)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Regime:
    """The campaign regime parts the world mechanism needs (analysis ``Regime``)."""

    llm_cap: int = 40
    p_rule: float = 0.55
    sigma_audit: float = 0.004


P1_DEFAULTS = dict(sigma_probe=0.0005, sigma_eta=0.001, size_sd=0.3, lag_min=3, lag_max=10, follow_offset=0.5,
                   probe_offset=1.0, n_follow=2, sigma_follow=0.05, mu0=0.0005, p_probe=0.8, probe_max_trial=16)
DEFAULT_WORLD_KW = {"P1": P1_DEFAULTS}
VARIANTS = {
    ("P0", "concentrated"): dict(trend_shape="early_window", trend_window=8),
    ("P0", "diffuse"): dict(trend_shape="linear"),
    ("P1", "concentrated"): dict(P1_DEFAULTS, n_keys=3, p_probe=0.25),
    ("P1", "diffuse"): dict(P1_DEFAULTS, n_keys=3, p_probe=0.8),
    ("P2+", "diffuse"): dict(fb_shape="r_linear", fb_sign=1.0, fb_len=6),
    ("P2+", "concentrated"): dict(fb_shape="r_step", fb_sign=1.0, fb_r_cut=0.7, fb_len=10),
    ("P2-", "diffuse"): dict(fb_shape="r_linear", fb_sign=-1.0, fb_len=40, fb_accum=True),
    ("P2-", "concentrated"): dict(fb_shape="r_step", fb_sign=-1.0, fb_r_cut=0.7, fb_len=40, fb_accum=True),
}
_WORLD_FIELDS = {f.name for f in fields(World)}


def make_world(kind: str, strength: float = 0.0, variant: str | None = None, **kw) -> World:
    """``make_world`` of the analysis simulator (kind "P2+" / "P2-" with a variant; "N0" without)."""
    bad = set(kw) - _WORLD_FIELDS
    if bad:
        raise ValueError(f"unknown world parameters {sorted(bad)}")
    if variant is not None:
        base = dict(VARIANTS[(kind, variant)])
        return World(kind=kind.rstrip("+-"), strength=float(strength), **{**base, **kw})
    return World(kind=kind, strength=float(strength), **{**DEFAULT_WORLD_KW.get(kind, {}), **kw})


# ---------------------------------------------------------------------------
# Randomness: one stream per campaign path, one theta table per instance
# ---------------------------------------------------------------------------

class Stream:
    """Manager + worker randomness of one campaign path (draw order as the analysis ``Stream``)."""

    def __init__(self, seed, n: int) -> None:
        rng = np.random.default_rng(seed)
        self.u_rule = rng.random(n + 2)
        self.u_kind = rng.random(n + 2)
        self.lag = rng.random(n + 2)
        self.eta = rng.standard_normal(n + 2)
        self.eps = rng.standard_normal(n + 2)
        self.z_size = rng.standard_normal(n + 2)


def theta_table(world: World, regime: Regime, seed: int, inst: int) -> np.ndarray:
    """Latent theta per key of one instance; the last two slots hold the size multiplier and the rule share."""
    rng = np.random.default_rng([int(seed), int(inst), 99])
    tab = world.mu0 + world.tau0 * rng.standard_normal(regime.llm_cap + 4 + max(world.n_keys, 0))
    u, v = rng.random(), rng.random()
    tab[-1] = 1.0
    tab[-2] = regime.p_rule
    if world.inst_prule_spread > 0:
        tab[-2] = min(0.95, max(0.0, regime.p_rule + world.inst_prule_spread * (2 * v - 1)))
    elif world.inst_busy_p > 0:
        tab[-2] = max(0.0, regime.p_rule - world.inst_busy_drop) if u < world.inst_busy_p else regime.p_rule
    return tab


# ---------------------------------------------------------------------------
# The proposal law (decision-independent given the stream)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Proposal:
    t: int
    rule: bool
    key: int = -1
    size: float = 0.0
    off: float = 0.0
    kind: str = RULE


def propose(world: World, regime: Regime, tab: np.ndarray, s: Stream, t: int, pending: list,
            allow_rule: bool = True) -> Proposal:
    """One proposal at trial t (mutates ``pending``, the P1 follow-up plan), as ``Sim.propose``
    (``allow_rule=False``: the rule draw is ignored, see ``proposal_sequence``)."""
    w = world
    if w.kind == "P1":
        due = [p for p in pending if p[0] <= t]
        if due:
            p = min(due)
            pending.remove(p)
            return Proposal(t, False, int(p[1]), float(p[2]), w.follow_offset * w.tau0, "follow")
    if allow_rule and s.u_rule[t] < float(tab[-2]):
        return Proposal(t, True)
    if w.kind == "P1" and t <= w.probe_max_trial and s.u_kind[t] < w.p_probe:
        due = t
        for i in range(w.n_follow):
            due += w.lag_min + int(((s.lag[t] * (i + 3.7)) % 1.0) * (w.lag_max - w.lag_min + 1))
            if due <= regime.llm_cap:
                pending.append((due, t, w.strength))
        return Proposal(t, False, t, float(w.size_probe), w.probe_offset * w.tau0, "probe")
    key = (regime.llm_cap + 2 + int(s.u_kind[t] * w.n_keys)) if w.n_keys > 0 else t
    size = w.size_filler * math.exp(w.size_sd * s.z_size[t]) * float(tab[-1])
    if w.kind == "P0" and w.p_big > 0 and s.lag[t] < w.p_big:
        size *= 1.0 + w.strength
    return Proposal(t, False, int(key), float(size), 0.0, "filler")


def proposal_sequence(world: World, regime: Regime, tab: np.ndarray, streams,
                      first_non_rule: bool = True) -> list[Proposal]:
    """Proposals for t = 1..llm_cap. ``streams`` is one ``Stream`` or a list of (first_t, Stream) segments:
    a fork continuation proposes from the root stream up to the fork trial and from its own stream after
    (the analysis ``run_leaf``: the P1 plan after the fork trial is the root's).

    ``first_non_rule`` (default): trial 1 is never rule-detectable, so that "trial 1 is executed and kept" holds
    as the harness implements it (the first executed trial is kept without comparison: there is no incumbent
    metric before it). The analysis simulator draws the rule share at t = 1 too and then decides its first
    executed trial against y0 by the policy, which the harness cannot do; the two agree exactly on instances
    whose u_rule[1] >= p_rule (IMPLEMENTATION_NOTES, open issue)."""
    segs = [(1, streams)] if isinstance(streams, Stream) else sorted(streams, key=lambda x: x[0])
    pending: list = []
    out = []
    for t in range(1, regime.llm_cap + 1):
        s = [st for t0, st in segs if t0 <= t][-1]
        out.append(propose(world, regime, tab, s, t, pending, allow_rule=not (first_non_rule and t == 1)))
    return out


# ---------------------------------------------------------------------------
# The true increment
# ---------------------------------------------------------------------------

def fb_scale(world: World, bf: float) -> float:
    """P2: how a keep made at worker-run budget fraction bf shifts later proposals (``Sim.fb_scale``)."""
    w = world
    if w.fb_shape == "const":
        return 1.0 if (w.fb_early_bf is None or bf < w.fb_early_bf) else 0.0
    if w.fb_shape == "step":
        return 1.0 if bf < (w.fb_early_bf if w.fb_early_bf is not None else 0.5) else -1.0
    if w.fb_shape == "linear":
        return 1.0 - 2.0 * bf
    if w.fb_shape == "r_linear":
        return w.fb_sign * (1.0 - bf)
    if w.fb_shape == "r_step":
        return w.fb_sign * (1.0 if (1.0 - bf) > (w.fb_r_cut if w.fb_r_cut is not None else 0.7) else 0.0)
    raise ValueError(w.fb_shape)


def keep_log_entry(world: World, t: int, runs_used: int, W: int) -> tuple[int, float] | None:
    """The feedback record of a keep at trial t with ``runs_used`` runs used (incl. this one); None: no record."""
    if t < 2:
        return None  # trial 1 is kept without comparison and carries no feedback
    sc = fb_scale(world, runs_used / W) if world.kind == "P2" else 1.0
    return None if sc == 0.0 else (int(t), float(sc))


def theta(world: World, regime: Regime, tab: np.ndarray, key: int, t: int, keep_log) -> float:
    """theta of a key at trial t given the incumbent's keep log [(t_keep, scale), ...] (``Sim.theta``)."""
    th = tab[key]
    if world.kind == "P0" and world.trend_shape:
        x = t / regime.llm_cap
        if world.trend_shape == "linear":
            th += world.strength * (1.0 - 2.0 * x)
        elif world.trend_shape == "early_window":
            th += world.strength if t <= world.trend_window else world.trend_late * world.strength
    if world.kind == "P2":
        recent = [sc for (k, sc) in keep_log if t - world.fb_len <= k < t]
        if recent:
            th += world.strength * (sum(recent) if world.fb_accum else recent[-1])
    return float(th)


def true_increment(world: World, regime: Regime, tab: np.ndarray, p: Proposal, s: Stream, keep_log) -> float:
    return p.size * (theta(world, regime, tab, p.key, p.t, keep_log) - p.off) + world.sigma_eta * s.eta[p.t]


def measurement_noise(world: World, p: Proposal, s: Stream) -> float:
    return world.sig(p.kind) * s.eps[p.t]


# ---------------------------------------------------------------------------
# The controller's keyed model (used by a2u's keyed mode)
# ---------------------------------------------------------------------------

def key_update(post: tuple[float, float], size: float, dhat: float, off: float, sigma_eta: float,
               sig: float) -> tuple[float, float]:
    """Conjugate update of theta_key from delta_hat + size off = size theta + (eta + eps) (``Sim.update``)."""
    mu, var = post
    nv = sigma_eta ** 2 + sig ** 2
    prec = 1.0 / var + size * size / nv
    return ((mu / var + size * (dhat + size * off) / nv) / prec, 1.0 / prec)


def key_forecast(post: tuple[float, float], size: float, off: float, sigma_eta: float) -> tuple[float, float]:
    """(a, A): predictive mean and variance of delta (``Sim.forecast``)."""
    mu, var = post
    return size * (mu - off), size * size * var + sigma_eta ** 2


def v_star(a: float, A_: float, sigma_cmp: float) -> float:
    """E[max(m_hat, 0)], m_hat ~ N(a, A^2 / (A + sigma^2)) (the analysis simulator's ``v_star``)."""
    v = A_ * A_ / (A_ + sigma_cmp ** 2)
    sv = math.sqrt(v)
    z = a / sv
    return a * 0.5 * (1.0 + math.erf(z / _SQRT2)) + sv * math.exp(-0.5 * z * z) / _SQRT2PI


def world_meta(world: World, regime: Regime) -> dict:
    """What the controller knows about the world (prior and measurement model; never theta or strength)."""
    return {"mu0": world.mu0, "tau0": world.tau0, "sigma_eta": world.sigma_eta, "sigma_cmp": world.sigma_cmp,
            "sigma_probe": world.sigma_probe, "sigma_follow": world.sigma_follow, "y0": world.y0}


def sig_from_meta(meta: dict, kind: str) -> float:
    if kind == "probe" and meta.get("sigma_probe") is not None:
        return float(meta["sigma_probe"])
    if kind == "follow" and meta.get("sigma_follow") is not None:
        return float(meta["sigma_follow"])
    return float(meta["sigma_cmp"])


__all__ = ["World", "Regime", "VARIANTS", "P1_DEFAULTS", "CONTROL_WORLDS", "make_world", "Stream", "theta_table",
           "Proposal", "propose", "proposal_sequence", "fb_scale", "keep_log_entry", "theta", "true_increment",
           "measurement_noise", "key_update", "key_forecast", "v_star", "world_meta", "sig_from_meta", "replace"]
