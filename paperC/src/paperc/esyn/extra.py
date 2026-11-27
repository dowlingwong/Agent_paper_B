"""Paper C's E-SYN worlds (build runbook P3, step 3; plan §5; reframe §2 A, BUILD_LIST B17).

AI-assisted (Claude, chat session, 16 Nov 2026). ENGINEERING_ONLY. Synthetic worlds are implementation checks and
oracle gaps, never evidence about the real loop (plan §5).

Every world wraps a Track S world mechanism (``paperc.esyn.worlds``, the pinned port: proposal law, theta table,
keyed increments, P1 probes / follow-ups, P2 keep feedback) and adds, as declared data:

* ``channel``: the channel that is on (``none`` for the strict null) and ``gain_sign``, the declared sign of the
  oracle gain over the best static rule (+1, or 0 for the strict null);
* ``sizes`` / ``size_probs``: a discrete size law (the budget world, so that the exact DP applies);
* ``interaction``: a symmetric pairwise matrix M over the recurring keys. The first kept edit of key j adds
  sum_{i in S} M[i][j] to the incumbent, where S is the set of keys with a kept edit (incumbent interaction);
* ``comparison``: ``increment`` (Track S: delta_hat = delta + sig(kind) eps, independent across comparisons) or
  ``config`` (each run measures a configuration with sd sigma_cmp / sqrt(2); the loop compares a candidate's mean
  measurement with the incumbent's recorded mean, so the incumbent's recorded error is shared by every later
  comparison until a re-audit: the shared-incumbent-error case of the T4 revision);
* ``epochs``: the decision epochs offered (``E1``, ``E2`` and, for evaluation control, ``verify``, ``reaudit``,
  ``final``), with ``max_obs`` measurements per configuration at most.

Units are raw metric units, as in Track S.
"""
from __future__ import annotations

import zlib
from dataclasses import asdict, dataclass, field

from paperc.esyn import worlds as WD

CHANNELS = ("none", "budget", "information", "keep_feedback", "interaction", "shared_error", "eval_allocation")
EPOCHS = ("E1", "E2", "verify", "reaudit", "final")


@dataclass(frozen=True)
class ESynWorld:
    name: str
    channel: str
    gain_sign: int
    base: WD.World
    regime: WD.Regime = field(default_factory=WD.Regime)
    W: int = 40
    run_cost: int = 1
    sizes: tuple[float, ...] = ()
    size_probs: tuple[float, ...] = ()
    interaction: tuple[tuple[float, ...], ...] = ()
    comparison: str = "increment"
    epochs: tuple[str, ...] = ("E1", "E2")
    max_obs: int = 3
    n_audit: int = 5
    delta_ref: float | None = None      # declared reference gain for the oracle tolerance; None: 0.5 sigma_cmp
    note: str = ""

    def __post_init__(self) -> None:
        if self.channel not in CHANNELS:
            raise ValueError(f"unknown channel {self.channel!r}")
        if self.gain_sign not in (0, 1):
            raise ValueError("gain_sign is 0 (strict null) or +1")
        if (self.channel == "none") != (self.gain_sign == 0):
            raise ValueError("gain_sign 0 exactly for the strict null")
        if self.comparison not in ("increment", "config"):
            raise ValueError(self.comparison)
        if not set(self.epochs) <= set(EPOCHS) or not {"E1", "E2"} <= set(self.epochs):
            raise ValueError(f"epochs {self.epochs}")
        if {"verify", "reaudit", "final"} & set(self.epochs) and self.comparison != "config":
            raise ValueError("evaluation-control epochs need comparison='config' (repeated measurements)")
        if len(self.sizes) != len(self.size_probs) or (self.sizes and abs(sum(self.size_probs) - 1.0) > 1e-12):
            raise ValueError("sizes and size_probs must have equal length and probabilities sum to 1")
        if self.interaction:
            n = self.base.n_keys
            if n <= 0 or len(self.interaction) != n or any(len(r) != n for r in self.interaction):
                raise ValueError("interaction must be n_keys x n_keys over recurring keys")
            if any(self.interaction[i][j] != self.interaction[j][i] for i in range(n) for j in range(n)):
                raise ValueError("interaction must be symmetric")
            if self.base.kind == "P1":
                raise ValueError("interaction is defined on recurring filler keys; not with P1 probes / follow-ups")
        if self.max_obs < 1 or self.W < 1 or self.run_cost != 1:
            raise ValueError("max_obs >= 1, W >= 1, run_cost == 1")

    @property
    def llm_cap(self) -> int:
        return self.regime.llm_cap

    @property
    def sigma_meas(self) -> float:
        """Config mode: sd of one measurement of a configuration (one paired comparison has sd sigma_cmp)."""
        return self.base.sigma_cmp / 2 ** 0.5

    @property
    def reference_gain(self) -> float:
        """Declared reference gain delta_Y for the 5 % oracle tolerance: Track S's 0.5 sigma (sigma_cmp here)."""
        return self.delta_ref if self.delta_ref is not None else 0.5 * self.base.sigma_cmp

    @property
    def code(self) -> int:
        """Stable integer for RNG keys."""
        return zlib.crc32(self.name.encode()) & 0xFFFF

    def to_dict(self) -> dict:
        d = asdict(self)
        d["base"] = self.base.to_dict()
        return d


# ---------------------------------------------------------------- the registry

_FILLER = dict(size_sd=0.6)

WORLDS: dict[str, ESynWorld] = {}


def _add(w: ESynWorld) -> None:
    WORLDS[w.name] = w


_add(ESynWorld(
    name="strict_null", channel="none", gain_sign=0, base=WD.make_world("N0"), W=40,
    sizes=(0.4, 1.0, 2.5), size_probs=(0.3, 0.5, 0.2),
    note="fresh keys, non-binding W, independent comparisons: the myopic Bayes rule is optimal"))
_add(ESynWorld(
    name="budget", channel="budget", gain_sign=1, base=WD.make_world("N0"), W=8,
    sizes=(0.4, 1.0, 2.5), size_probs=(0.3, 0.5, 0.2),
    note="as strict_null with W = 8 of about 18 executable proposals: budget opportunity cost; exact DP"))
_add(ESynWorld(
    name="interaction", channel="interaction", gain_sign=1, base=WD.make_world("N0", n_keys=4), W=40,
    interaction=((0.0, 0.012, 0.0, 0.0), (0.012, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 0.012), (0.0, 0.0, 0.012, 0.0)),
    note="four recurring keys; pairs (0,1) and (2,3) are complements: keeping the first of a pair enables the other"))
_add(ESynWorld(
    name="shared_error", channel="shared_error", gain_sign=1, base=WD.make_world("N0"), W=60,
    comparison="config", epochs=("E1", "E2", "reaudit"),
    note="config measurements: a kept candidate's recorded value carries its (selected) measurement error into "
         "every later comparison until a re-audit; W non-binding, so a re-audit costs no proposal"))
_add(ESynWorld(
    name="eval_allocation", channel="eval_allocation", gain_sign=1, base=WD.make_world("N0"), W=40,
    comparison="config", epochs=("E1", "E2", "verify", "reaudit", "final"),
    note="verify (re-measure the candidate), re-audit (re-measure the incumbent) and final selection among the "
         "kept configurations, under the shared-error measurement model; W = 40 leaves room for some extra "
         "measurements (at W = 24 none pays for its run)"))
_add(ESynWorld(
    name="information", channel="information", gain_sign=1, base=WD.make_world("P1", variant="diffuse", strength=16.0),
    W=10, note="Track S P1-diffuse at strength 16 (the follow-up size; Track S ANALYSIS_NOTES section 5.1 grid), W 10: "
               "probes open keys whose follow-ups are large (information channel)"))
_add(ESynWorld(
    name="keep_feedback", channel="keep_feedback", gain_sign=1,
    base=WD.make_world("P2+", variant="diffuse", strength=0.012), W=10,
    note="Track S P2+-diffuse at strength 0.012, W 10 (Track S ANALYSIS_NOTES section 5.1 grid): an early keep "
         "raises the theta mean of later proposals (keep-feedback channel)"))
