"""E-SYN policies (build runbook P3): static rules and channel-specific families for the certified oracle.

AI-assisted (Claude, chat session, 16 Nov 2026). ENGINEERING_ONLY.

All policies are deterministic (probability 1.0) and read only ``sim.obs_from_state`` fields, so that
``check_campaign`` can replay them. Execute uses ">=", keep uses ">" (Track S runbook rev. 7.1).

* ``Static(g, h)``: Paper B's rule class. E1 execute iff V* >= g; E2 keep iff m_hat > h; never verify or re-audit;
  the final selection keeps the incumbent. Its best member on a selection block is the **best static rule**, the
  baseline of every oracle gain.
* ``Threshold(table, h)``: E1 execute iff V* >= table[(slots_left, runs_left)] (the budget DP's policy).
* ``Dynamic(g, h, b_info, tau_bar, b_keep, b_novel, tau_cut)``: E1 execute iff
  V* + b_info (tau - tau_bar) + b_novel [key not seen and tau < tau_cut] >= g; E2 keep iff
  m_hat > h - b_keep runs_left / W (information and keep-feedback channels; ``b_novel`` is the key-novelty term
  Track S's analysis notes propose, because a tau bonus also rewards P1's large, noisy follow-ups; ``tau_cut``
  keeps the novelty bonus off those follow-ups, whose keys are also unseen when their probe was skipped).
* ``InteractionAware(g, h, beta)``: E2 keep iff m_hat + beta bonus > h, where bonus is the complement value of the
  ``privileged:interaction`` forecast, computed from the **true** interaction matrix (an oracle member with
  privileged world knowledge; ``privileged = True``).
* ``EvalAlloc(g, h, verify_band, verify_max, reaudit_max, final)``: verify while candidate_obs < verify_max and
  |m_hat - h| < verify_band sigma; re-audit while incumbent_obs < reaudit_max; final ``incumbent`` or ``best``
  (highest recorded value among kept configurations with at least two measurements, else the incumbent).
"""
from __future__ import annotations

from dataclasses import dataclass, field


def _myopic(obs: dict, g: float, h: float) -> tuple[str, float, str | None]:
    ep = obs["epoch"]
    if ep == "E1":
        return ("execute" if obs["v_star"] >= g else "skip"), 1.0, None
    if ep == "E2":
        return ("keep" if obs["m_hat"] > h else "discard"), 1.0, None
    if ep == "verify":
        return "no_verify", 1.0, None
    if ep == "reaudit":
        return "no_reaudit", 1.0, None
    if ep == "final":
        return "select", 1.0, obs["incumbent_hash"]
    raise ValueError(ep)


@dataclass(frozen=True)
class Static:
    g: float
    h: float = 0.0

    @property
    def name(self) -> str:
        return f"static:{self.g:.6g},{self.h:.6g}"

    def act(self, obs: dict):
        return _myopic(obs, self.g, self.h)


@dataclass(frozen=True)
class Threshold:
    table: dict = field(hash=False, compare=False)
    h: float = 0.0
    label: str = "dp"

    @property
    def name(self) -> str:
        return self.label

    def act(self, obs: dict):
        if obs["epoch"] == "E1":
            thr = self.table[(obs["slots_left"], obs["runs_left"])]
            return ("execute" if obs["v_star"] >= thr else "skip"), 1.0, None
        return _myopic(obs, 0.0, self.h)


@dataclass(frozen=True)
class Dynamic:
    g: float
    h: float = 0.0
    b_info: float = 0.0
    tau_bar: float = 0.0
    b_keep: float = 0.0
    b_novel: float = 0.0
    tau_cut: float = float("inf")

    @property
    def name(self) -> str:
        return (f"dynamic:{self.g:.6g},{self.h:.6g},{self.b_info:.6g},{self.tau_bar:.6g},{self.b_keep:.6g},"
                f"{self.b_novel:.6g},{self.tau_cut:.6g}")

    def act(self, obs: dict):
        ep = obs["epoch"]
        if ep == "E1":
            score = obs["v_star"] + self.b_info * (obs["tau"] - self.tau_bar) \
                + (self.b_novel if (not obs["key_seen"] and obs["tau"] < self.tau_cut) else 0.0)
            return ("execute" if score >= self.g else "skip"), 1.0, None
        if ep == "E2":
            thr = self.h - self.b_keep * obs["runs_left"] / obs["W"]
            return ("keep" if obs["m_hat"] > thr else "discard"), 1.0, None
        return _myopic(obs, self.g, self.h)


@dataclass(frozen=True)
class InteractionAware:
    """Oracle member: reads the privileged forecast computed from the true interaction matrix."""
    g: float
    h: float = 0.0
    beta: float = 0.5
    privileged = True

    @property
    def name(self) -> str:
        return f"interaction:{self.g:.6g},{self.h:.6g},{self.beta:.6g}"

    def act(self, obs: dict):
        if obs["epoch"] == "E2":
            return ("keep" if obs["m_hat"] + self.beta * obs["bonus"] > self.h else "discard"), 1.0, None
        return _myopic(obs, self.g, self.h)


@dataclass(frozen=True)
class EvalAlloc:
    g: float
    h: float = 0.0
    verify_band: float = 0.0
    verify_max: int = 1
    reaudit_max: int = 1
    final: str = "incumbent"

    @property
    def name(self) -> str:
        return (f"evalloc:{self.g:.6g},{self.h:.6g},{self.verify_band:.6g},{self.verify_max},{self.reaudit_max},"
                f"{self.final}")

    def act(self, obs: dict):
        ep = obs["epoch"]
        if ep == "verify":
            near = abs(obs["m_hat"] - self.h) < self.verify_band * obs["sigma"]
            return ("verify" if near and obs["candidate_obs"] < self.verify_max else "no_verify"), 1.0, None
        if ep == "reaudit":
            return ("reaudit" if obs["incumbent_obs"] < self.reaudit_max else "no_reaudit"), 1.0, None
        if ep == "final":
            if self.final == "best":
                ok = [c for c in obs["candidates"] if c[1] is not None and c[2] >= 2]
                if ok:
                    return "select", 1.0, max(ok, key=lambda c: c[1])[0]
            return "select", 1.0, obs["incumbent_hash"]
        return _myopic(obs, self.g, self.h)


@dataclass(frozen=True)
class Schedule:
    """A 9-threshold schedule after Track S's (ANALYSIS_NOTES section 5.1; not a port): the E1 threshold by budget
    third x tau half, the E2 threshold by budget third. The budget position is r = runs used / W (third
    k = min(floor(3 r), 2)); the tau half is tau >= tau_split, a fixed split. It nests the static rules (all g equal,
    all h equal)."""
    gs: tuple        # 6 execute thresholds, index 2 k + (tau >= tau_split)
    hs: tuple        # 3 keep thresholds, index k
    tau_split: float = 0.02

    @property
    def name(self) -> str:
        return ("schedule:" + ",".join(f"{x:.6g}" for x in self.gs) + ";" + ",".join(f"{x:.6g}" for x in self.hs)
                + f";{self.tau_split:.6g}")

    def act(self, obs: dict):
        r = 1.0 - obs["runs_left"] / obs["W"]
        k = min(int(3 * r), 2)
        ep = obs["epoch"]
        if ep == "E1":
            j = 1 if obs["tau"] >= self.tau_split else 0
            return ("execute" if obs["v_star"] >= self.gs[2 * k + j] else "skip"), 1.0, None
        if ep == "E2":
            return ("keep" if obs["m_hat"] > self.hs[k] else "discard"), 1.0, None
        return _myopic(obs, self.gs[0], self.hs[0])


def from_name(name: str):
    """Rebuild a ``Static`` or ``EvalAlloc`` policy from its name (table post-processing)."""
    kind, _, rest = name.partition(":")
    parts = rest.split(",")
    if kind == "static":
        return Static(float(parts[0]), float(parts[1]))
    if kind == "evalloc":
        return EvalAlloc(float(parts[0]), float(parts[1]), float(parts[2]), int(parts[3]), int(parts[4]), parts[5])
    raise ValueError(f"cannot rebuild {name!r}")
