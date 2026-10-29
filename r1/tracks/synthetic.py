"""Synthetic control nodes of Track S: P1, P2 (positive controls) and N0 (null). Runbook rev. 3, §4; rev. 7.

Rev. 7 (default): every node name is a world of the analysis simulator (``WorldNode``, mechanism in
``r1.tracks.worlds``; N0, P0, P1, P2+ = ``synthetic_P2p``, P2- = ``synthetic_P2m``, variants diffuse /
concentrated, ``strength`` the S0.6 value), run through the real harness loop; see the end of this module and
IMPLEMENTATION_NOTES "Rev. 7 / 7.1 alignment". The rev.-6 log-linear nodes described below remain available with
``params={"mechanism": "loglinear", ...}`` for engineering tests only; they are not declared controls.

AI-assisted (Claude, 29 Oct 2026). ENGINEERING_ONLY. Parameters are constructor
arguments; their values are to be set by simulation of the primary estimand in the
Track S regime and declared in S0.6 (runbook §4, mi-6). The defaults below only make
the nodes runnable in tests; they are not declared values.

Every synthetic node runs through the real harness loop and the same collector as the
real nodes: the editable surface is the ``digits_mlp`` node's ``train.py`` (so snapshots,
restores and the C3 featurizer's replay work unchanged), with a paper-side worker that
computes the metric from a known law instead of training, and a scripted manager (no
prompt, no LLM seed; runbook §4 "What the scripted manager does not test").

Law (``LogLinearLaw``), on the float keys ALPHA and LEARNING_RATE_INIT:
    Y_true(config) = base + sum_k theta_k * log(v_k / v0_k)
so an edit that multiplies key k by exp(step) has the true increment theta_k * step,
whatever the incumbent (no edit-edit interaction). A run of an edited configuration
reports Y_true + offset, with
    offset_candidate = offset_incumbent + sd(step) * eps_run      (incumbent_error=False)
    offset_candidate = sd(step) * eps_run                          (incumbent_error=True)
eps_run ~ N(0, 1) fresh per run (keyed by the campaign seed and the trial index, so all
arms of a fork share it), sd(step) = sigma_run + kappa |step|. With
``incumbent_error=False`` every Delta_hat = Delta + sd * eps_run exactly (no shared
incumbent error); the incumbent's offset is carried in a comment line of ``train.py``
(ignored by every configuration parser, restored with the incumbent on a non-keep).

Nodes (rev.-6 amendment 3). Every node has a ``gain`` knob, the planted size of its channel's effect (the
best-member oracle gain is a monotone function of it; the value declared for S0.6 is calibrated by simulation,
runbook §4 mi-6), and a ``variant``: ``diffuse`` (Gaussian draws) or ``concentrated`` (a zero-mean two-point law
with the same sd, the large value with probability q, plus a small jitter: rare large effects).

* **N0** (zero oracle gain): non-binding W (the run's W must not bind), independent proposal values fixed in
  advance (key and step from the instance seed and the trial index only), theta known: no information, no
  feedback. ``gain`` must be 0; ``spread`` is the sd of the values.
* **P0** (budget channel): independent proposal values that the controller can observe (review M3): four
  (key, sign) groups with known distinct means (theta_ALPHA = +1, theta_LR = -1; group means
  ``group_means`` x ``gain``; within-group sd ``within`` x ``gain``) and a per-group A2-U prior, so V* varies
  across proposals; run at a binding W. ``diffuse``: the four groups equally likely; ``concentrated``: the
  best group (mean ``conc_best`` x gain) with probability q, otherwise one of two slightly negative groups.
* **P1** (Prop. 10(c), information): a probe edit (step alpha) and a later large edit (step beta) on the SAME
  key share the instance's latent theta (sd ``gain``): Delta_1 = alpha theta, Delta_2 = beta theta; noise sd
  sigma_run + kappa |step|. Filler edits on the other key are iid.
* **P2p / P2m** (Prop. 10(b), budget-dependent keep feedback, both signs): a trigger edit at a trial drawn per
  instance uniformly in [``trigger_min``, ``trigger_max``] (review M3: so r at the trigger varies);
  if it is kept (visible to the manager as the incumbent's value of the trigger key), every later proposal's
  mean step moves by +gain (P2p) or -gain (P2m) (concentrated: a fraction q of later proposals moves by
  +-gain/q). The value of keeping grows with the proposals left, hence with the budget.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from r1.c3.features import apply_edit, parsed_metric
from r1.diagnostics.di_test import configuration
from r1.harness import import_harness
from r1.tracks.a2u import A2UPrior, KindPrior

HARNESS = import_harness()

from autoresearch.manager.base import ManagerProposal  # noqa: E402
from autoresearch.worker.base import WorkerResult  # noqa: E402

SURFACE = "digits_mlp"
FLOAT_KEYS = ("ALPHA", "LEARNING_RATE_INIT")
OFFSET_TAG = "# tracks-recorded-offset:"
_OFFSET_RE = re.compile(r"^# tracks-recorded-offset: (\S+)\s*$", re.MULTILINE)
SYNTHETIC_NODES = ("synthetic_P0", "synthetic_P1", "synthetic_P2p", "synthetic_P2m", "synthetic_N0")
VARIANTS = ("diffuse", "concentrated")


def surface_start_files() -> dict[str, str]:
    return {"train.py": (HARNESS / "nodes" / SURFACE / "train.py").read_text()}


def start_values() -> dict[str, float]:
    cfg = configuration(surface_start_files())
    return {k: float(cfg[k]) for k in FLOAT_KEYS}


def read_offset(text: str) -> float:
    m = _OFFSET_RE.search(text)
    return float(m.group(1)) if m else 0.0


def set_offset(text: str, offset: float) -> str:
    line = f"{OFFSET_TAG} {float(offset)!r}"
    if _OFFSET_RE.search(text):
        return _OFFSET_RE.sub(line, text)
    return text.rstrip("\n") + "\n" + line + "\n"


def _cfg_hash(cfg: dict) -> int:
    return int(hashlib.sha256(json.dumps(cfg, sort_keys=True, default=str).encode()).hexdigest()[:8], 16)


@dataclass(frozen=True)
class LogLinearLaw:
    salt: int                         # instance seed
    theta: dict                       # key -> theta_k
    base: float = 0.9
    sigma_run: float = 0.005
    kappa: float = 0.0
    incumbent_error: bool = False
    sigma_audit: float = 0.0
    start: dict = field(default_factory=start_values)

    def y_true(self, cfg: dict) -> float:
        return float(self.base + sum(float(t) * math.log(float(cfg[k]) / float(self.start[k]))
                                     for k, t in self.theta.items()))

    def run_sd(self, step: float | None) -> float:
        return float(self.sigma_run + self.kappa * abs(step or 0.0))

    def eps(self, campaign_seed: int, budget_index: int) -> float:
        return float(np.random.default_rng([int(self.salt), int(campaign_seed), int(budget_index), 17]).standard_normal())

    def audit(self, cfg: dict, seed: int) -> float:
        if self.sigma_audit == 0:
            return self.y_true(cfg)
        z = np.random.default_rng([int(self.salt), int(seed), _cfg_hash(cfg), 29]).standard_normal()
        return float(self.y_true(cfg) + self.sigma_audit * z)


class SyntheticWorker:
    """Harness ``Worker`` with the ``LogLinearLaw`` (no subprocess); seeded re-runs for completeness."""

    mode = "tracks_synthetic_worker"

    def __init__(self, node_root: str | Path, law: LogLinearLaw, *, train_seed: int, split_seed: int | None = None) -> None:
        self.node_root = Path(node_root).resolve()
        self.law = law
        self._train_seed, self._split_seed = int(train_seed), split_seed
        self.runs = 0

    def _result(self, metric: float | None, failure: str | None = None) -> WorkerResult:
        return WorkerResult(worker_mode=self.mode, changed_files=("train.py",) if metric is not None else (),
                            success=metric is not None,
                            parsed_metrics={} if metric is None else {"val_score": float(metric)},
                            raw_log_ref="", patch_ref="synthetic.diff", git_commit_before="", git_commit_after="",
                            failure_message=failure)

    def run_trial(self, proposal, node_spec, budget_index):
        self.runs += 1
        path = self.node_root / "train.py"
        text = path.read_text()
        old_cfg = configuration({"train.py": text})
        edit = (proposal.extra or {}).get("structured_edit")
        step = None
        if edit:
            try:
                text = apply_edit({"train.py": text}, edit)["train.py"]
            except ValueError as exc:
                return self._result(None, f"edit failed: {exc}")
            key = edit["symbol"]
            new_cfg = configuration({"train.py": text})
            try:
                step = math.log(float(new_cfg[key]) / float(old_cfg[key]))
            except (TypeError, ValueError, ZeroDivisionError):
                step = None
        cfg = configuration({"train.py": text})
        noise = self.law.run_sd(step) * self.law.eps(self._train_seed, budget_index)
        offset = noise if self.law.incumbent_error else read_offset(text) + noise
        path.write_text(set_offset(text, offset))
        return self._result(self.law.y_true(cfg) + offset)

    def run_trial_at_seed(self, proposal, node_spec, budget_index, *, train_seed, split_seed=None):
        self.runs += 1
        cfg = configuration({"train.py": (self.node_root / "train.py").read_text()})
        z = np.random.default_rng([int(self.law.salt), int(train_seed), int(budget_index), 23]).standard_normal()
        return self._result(self.law.y_true(cfg) + self.law.sigma_run * float(z))


class _ScriptedSteps:
    """Scripted manager base: one multiplicative edit per trial, ``plan(status) -> (key, step)``."""

    deterministic = True

    def __init__(self, node: str, seed: int, repetition: int) -> None:
        self.node, self.seed, self.repetition = node, int(seed), int(repetition)
        self.mode = f"scripted_{node}"
        self.start = start_values()

    def plan(self, status) -> tuple[str, float]:  # pragma: no cover - abstract
        raise NotImplementedError

    def propose_next_trial(self, status, memory_context, node_spec) -> ManagerProposal:
        key, step = self.plan(status)
        old = str(status.current_constants[key])
        new = repr(float(old) * math.exp(float(step)))
        path = node_spec.editable_paths[0]
        return ManagerProposal(
            manager_mode=self.mode, proposal_summary=f"{key} {old} -> {new}",
            proposal_rationale=f"Scripted {self.node} proposal (Track S synthetic control).",
            target_files=tuple(node_spec.editable_paths),
            objective=f"Change {key} from {old} to {new} in {path} and keep all other hyperparameters unchanged.",
            extra={"structured_edit": {"type": "python_constant", "path": path, "symbol": key, "old": old, "new": new},
                   "scripted": {"node": self.node, "seed": self.seed, "repetition": self.repetition,
                                "step": float(step)}})


def draw_step(rng: np.random.Generator, mean: float, spread: float, variant: str, q: float) -> float:
    """One step: ``diffuse`` N(mean, spread^2); ``concentrated`` mean + a zero-mean two-point law with sd spread
    (+spread sqrt((1-q)/q) with probability q, else -spread sqrt(q/(1-q))) + N(0, (0.1 spread)^2) jitter."""
    if variant == "diffuse":
        return float(rng.normal(mean, spread))
    if variant != "concentrated":
        raise ValueError(f"variant must be one of {VARIANTS}")
    big = rng.random() < q
    jump = spread * (math.sqrt((1 - q) / q) if big else -math.sqrt(q / (1 - q)))
    return float(mean + jump + rng.normal(0.0, 0.1 * spread))


class IidManager(_ScriptedSteps):
    """N0 and P0: independent values fixed in advance (no repetition, no status input)."""

    def __init__(self, node: str, seed: int, repetition: int, *, mu_step: float, spread: float, variant: str,
                 q: float) -> None:
        super().__init__(node, seed, repetition)
        self.mu_step, self.spread, self.variant, self.q = float(mu_step), float(spread), variant, float(q)

    def plan(self, status):
        rng = np.random.default_rng([self.seed, int(status.budget_index), 101])
        key = FLOAT_KEYS[int(rng.integers(len(FLOAT_KEYS)))]
        return key, draw_step(rng, self.mu_step, self.spread, self.variant, self.q)


P0_GROUPS = (("ALPHA", "+"), ("LEARNING_RATE_INIT", "-"), ("ALPHA", "-"), ("LEARNING_RATE_INIT", "+"))
P0_THETA = {"ALPHA": 1.0, "LEARNING_RATE_INIT": -1.0}


def p0_groups(p: dict) -> list[dict]:
    """The P0 groups: key, sign, mean increment, within-group sd and draw probability."""
    gain, q = float(p["gain"]), float(p.get("q", 0.1))
    if p.get("variant", "diffuse") == "diffuse":
        groups = P0_GROUPS
        means, probs = [float(m) * gain for m in p.get("group_means", (1.5, 0.5, -0.5, -1.5))], [0.25] * 4
    else:  # the rare best group (ALPHA+) and two slightly negative groups (ALPHA-, LR+)
        groups = (P0_GROUPS[0], P0_GROUPS[2], P0_GROUPS[3])
        neg = float(p.get("conc_rest", -0.25)) * gain
        means, probs = [float(p.get("conc_best", 3.0)) * gain, neg, neg], [q, (1 - q) / 2, (1 - q) / 2]
    w = float(p.get("within", 0.2)) * gain
    out = []
    for (key, sign), m, pr in zip(groups, means, probs):
        if (m / P0_THETA[key] > 0) != (sign == "+"):
            raise ValueError(f"P0 group {key}{sign}: mean {m} is incompatible with the step sign")
        out.append({"key": key, "sign": sign, "mean": m, "sd": w, "p": pr})
    return out


class P0Manager(_ScriptedSteps):
    """P0: a group drawn per trial (fixed in advance), increment N(mean, sd^2) kept on the group's sign."""

    def __init__(self, seed: int, repetition: int, *, groups: list[dict]) -> None:
        super().__init__("synthetic_P0", seed, repetition)
        self.groups = groups

    def plan(self, status):
        rng = np.random.default_rng([self.seed, int(status.budget_index), 109])
        g = self.groups[int(rng.choice(len(self.groups), p=[x["p"] for x in self.groups]))]
        delta = float(rng.normal(g["mean"], g["sd"]))
        theta = P0_THETA[g["key"]]
        if (delta / theta > 0) != (g["sign"] == "+"):
            delta = g["mean"]  # keep the step on the group's sign (rare when sd << |mean|)
        return g["key"], delta / theta


class P1Manager(_ScriptedSteps):
    def __init__(self, seed: int, repetition: int, *, probe_key: str, probe_trial: int, big_trial: int,
                 alpha: float, beta: float, filler_mu: float, filler_sd: float) -> None:
        super().__init__("synthetic_P1", seed, repetition)
        self.probe_key, self.probe_trial, self.big_trial = probe_key, int(probe_trial), int(big_trial)
        self.alpha, self.beta, self.filler_mu, self.filler_sd = float(alpha), float(beta), float(filler_mu), float(filler_sd)
        self.other = [k for k in FLOAT_KEYS if k != probe_key][0]

    def plan(self, status):
        b = int(status.budget_index)
        if b == self.probe_trial:
            return self.probe_key, self.alpha
        if b == self.big_trial:
            return self.probe_key, self.beta
        rng = np.random.default_rng([self.seed, self.repetition, b, 103])
        return self.other, float(rng.normal(self.filler_mu, self.filler_sd))


class P2Manager(_ScriptedSteps):
    def __init__(self, node: str, seed: int, repetition: int, *, sign: float, trigger_key: str, trigger_trial: int,
                 trigger_step: float, mu_base: float, gain: float, sd_step: float, variant: str, q: float) -> None:
        super().__init__(node, seed, repetition)
        self.sign, self.trigger_key, self.trigger_trial = float(sign), trigger_key, int(trigger_trial)
        self.trigger_step, self.mu_base, self.gain, self.sd_step = float(trigger_step), float(mu_base), float(gain), float(sd_step)
        self.variant, self.q = variant, float(q)
        self.other = [k for k in FLOAT_KEYS if k != trigger_key][0]

    def trigger_kept(self, status) -> bool:
        """The incumbent shown to the manager carries the trigger edit (its key left the start value)."""
        return not math.isclose(float(status.current_constants[self.trigger_key]), self.start[self.trigger_key],
                                rel_tol=1e-12)

    def plan(self, status):
        b = int(status.budget_index)
        if b == self.trigger_trial:
            return self.trigger_key, self.trigger_step
        rng = np.random.default_rng([self.seed, self.repetition, b, 107])
        shift = 0.0
        if self.trigger_kept(status):
            if self.variant == "diffuse":
                shift = self.sign * self.gain
            elif rng.random() < self.q:
                shift = self.sign * self.gain / self.q
        return self.other, float(rng.normal(self.mu_base + shift, self.sd_step))


@dataclass
class SyntheticNode:
    """A synthetic control node: its law per instance, its scripted manager and its (known) A2-U prior."""

    name: str
    params: dict
    surface: str = SURFACE

    def __post_init__(self) -> None:
        p = self.params
        if p.get("variant", "diffuse") not in VARIANTS:
            raise ValueError(f"variant must be one of {VARIANTS}")
        if self.name == "synthetic_N0" and float(p.get("gain", 0.0)) != 0.0:
            raise ValueError("N0 has zero oracle gain by construction; gain must be 0 (use spread for the values)")

    @property
    def sigma_node(self) -> float:
        return float(self.params["sigma_run"])

    def law(self, seed: int) -> LogLinearLaw:
        p = self.params
        common = dict(salt=int(seed), base=float(p.get("base", 0.9)), sigma_run=float(p["sigma_run"]),
                      kappa=float(p.get("kappa", 0.0)), incumbent_error=bool(p.get("incumbent_error", False)),
                      sigma_audit=float(p.get("sigma_audit", 0.0)))
        if self.name == "synthetic_N0":
            return LogLinearLaw(theta={k: 1.0 for k in FLOAT_KEYS}, **common)
        if self.name == "synthetic_P0":
            return LogLinearLaw(theta=dict(P0_THETA), **common)
        if self.name == "synthetic_P1":
            rng = np.random.default_rng([int(seed), 211])
            th = draw_step(rng, float(p["theta_mean"]), float(p["gain"]), p.get("variant", "diffuse"), float(p.get("q", 0.1)))
            other = [k for k in FLOAT_KEYS if k != p["probe_key"]][0]
            return LogLinearLaw(theta={p["probe_key"]: th, other: 1.0}, **common)
        other = [k for k in FLOAT_KEYS if k != p["trigger_key"]][0]
        return LogLinearLaw(theta={p["trigger_key"]: float(p["theta_trigger"]), other: 1.0}, **common)

    def manager(self, seed: int, repetition: int):
        p = self.params
        variant, q = p.get("variant", "diffuse"), float(p.get("q", 0.1))
        if self.name == "synthetic_N0":
            return IidManager(self.name, seed, repetition, mu_step=p["mu_step"], spread=p["spread"], variant=variant, q=q)
        if self.name == "synthetic_P0":
            return P0Manager(seed, repetition, groups=p0_groups(p))
        if self.name == "synthetic_P1":
            return P1Manager(seed, repetition, probe_key=p["probe_key"], probe_trial=p["probe_trial"],
                             big_trial=p["big_trial"], alpha=p["alpha"], beta=p["beta"],
                             filler_mu=p["filler_mu"], filler_sd=p["filler_sd"])
        return P2Manager(self.name, seed, repetition, sign=+1.0 if self.name == "synthetic_P2p" else -1.0,
                         trigger_key=p["trigger_key"], trigger_trial=self.trigger_trial(seed),
                         trigger_step=p["trigger_step"], mu_base=p["mu_base"], gain=p["gain"], sd_step=p["sd_step"],
                         variant=variant, q=q)

    def trigger_trial(self, seed: int) -> int:
        """P2: the instance's trigger trial, uniform in [trigger_min, trigger_max] (``trigger_trial`` pins it)."""
        p = self.params
        if p.get("trigger_trial") is not None:
            return int(p["trigger_trial"])
        lo, hi = int(p["trigger_min"]), int(p["trigger_max"])
        return int(np.random.default_rng([int(seed), 223]).integers(lo, hi + 1))

    def worker(self, node_root: Path, seed: int) -> SyntheticWorker:
        return SyntheticWorker(node_root, self.law(seed), train_seed=seed, split_seed=seed)

    def audit(self, seed_instance: int, files: dict[str, str], seeds) -> list[float]:
        law = self.law(seed_instance)
        cfg = configuration(files)
        return [law.audit(cfg, s) for s in seeds]

    def prior(self) -> A2UPrior:
        """The A2-U prior for the node (``params["prior"]`` when given, else a default from the law)."""
        p = self.params
        s = float(p["sigma_run"])
        if p.get("prior"):
            kp = KindPrior(**p["prior"])
        elif self.name == "synthetic_N0":
            # Independent values N(mu_step, spread^2) (same sd in both variants): no shared group mean.
            kp = KindPrior(mu0=float(p["mu_step"]), tau0=1e-6 * s, sigma_cmp=s, tau_w=max(float(p["spread"]), 1e-9))
        elif self.name == "synthetic_P0":
            groups = p0_groups(p)
            kp = KindPrior(mu0=float(np.dot([g["p"] for g in groups], [g["mean"] for g in groups])), tau0=1e-6 * s,
                           sigma_cmp=s, tau_w=max(float(np.std([g["mean"] for g in groups])), 1e-9))
            group_priors = {f"{g['key']}|{g['sign']}": KindPrior(mu0=g["mean"], tau0=1e-6 * s, sigma_cmp=s,
                                                                 tau_w=max(g["sd"], 1e-9)) for g in groups}
            return A2UPrior(node=SURFACE, sigma_node=s, kinds={"local": kp}, groups=group_priors,
                            meta={"label": "SYNTHETIC", "node": self.name, "params": json.loads(json.dumps(p))})
        elif self.name == "synthetic_P1":
            kp = KindPrior(mu0=float(p["filler_mu"]), tau0=max(abs(float(p["alpha"])) * float(p["gain"]), 1e-9),
                           sigma_cmp=s, tau_w=float(p["filler_sd"]))
        else:
            kp = KindPrior(mu0=float(p["mu_base"]), tau0=max(float(p["sd_step"]), 1e-9), sigma_cmp=s, tau_w=0.0)
        return A2UPrior(node=SURFACE, sigma_node=s, kinds={"local": kp},
                        meta={"label": "SYNTHETIC", "node": self.name, "params": json.loads(json.dumps(p))})

    def describe(self) -> dict:
        return {"name": self.name, "surface": self.surface, "params": json.loads(json.dumps(self.params))}


# Defaults: runnable placeholders only (to be replaced by the simulated, declared values; runbook §4 mi-6).
_P2 = {"trigger_key": "LEARNING_RATE_INIT", "trigger_trial": None, "trigger_min": 2, "trigger_max": 12,
       "trigger_step": 0.1, "theta_trigger": -0.01,
       "mu_base": -0.002, "gain": 0.005, "sd_step": 0.004, "sigma_run": 0.003, "variant": "diffuse", "q": 0.1}
DEFAULT_PARAMS = {
    "synthetic_N0": {"mu_step": 0.0, "spread": 0.01, "gain": 0.0, "sigma_run": 0.005, "variant": "diffuse", "q": 0.1},
    "synthetic_P0": {"gain": 0.004, "group_means": [1.5, 0.5, -0.5, -1.5], "within": 0.2, "conc_best": 3.0,
                     "conc_rest": -0.25, "sigma_run": 0.003, "variant": "diffuse", "q": 0.1},
    "synthetic_P1": {"probe_key": "LEARNING_RATE_INIT", "probe_trial": 2, "big_trial": 6, "alpha": 0.1,
                     "beta": 1.0, "theta_mean": 0.0, "gain": 0.05, "kappa": 0.01, "sigma_run": 0.002,
                     "filler_mu": -0.002, "filler_sd": 0.004, "variant": "diffuse", "q": 0.1},
    "synthetic_P2p": dict(_P2),
    "synthetic_P2m": dict(_P2),
}


# ---------------------------------------------------------------------------
# Rev. 7: the analysis simulator's worlds on the real pipeline (``r1.tracks.worlds``)
# ---------------------------------------------------------------------------

NODE_WORLDS = {"synthetic_N0": "N0", "synthetic_P0": "P0", "synthetic_P1": "P1", "synthetic_P2p": "P2+",
               "synthetic_P2m": "P2-"}
WORLD_EDIT_KEY = "ALPHA"     # the surface constant every world edit changes (to a value unique to the trial)
WORLD_EDIT_STEP = 1e-3       # ALPHA_t = ALPHA_start x exp(1e-3 t): no edit is a no-op or a duplicate
WORLD_STREAM_TAG = 7000      # stream seed of (instance, repetition): [world_seed, instance, 7000, repetition]
TRUE_Y_TAG = "# tracks-true-y:"
KEEP_LOG_TAG = "# tracks-keep-log:"
WORLD_PARAMS = ("mechanism", "variant", "strength", "world_seed", "llm_cap", "p_rule", "sigma_audit", "W", "world")


def _get_tag(text: str, tag: str) -> str | None:
    m = re.search(r"^" + re.escape(tag) + r" (.+?)\s*$", text, re.MULTILINE)
    return m.group(1) if m else None


def _set_tag(text: str, tag: str, value: str) -> str:
    line = f"{tag} {value}"
    pat = re.compile(r"^" + re.escape(tag) + r" .*$", re.MULTILINE)
    if pat.search(text):
        return pat.sub(lambda _: line, text)
    return text.rstrip("\n") + "\n" + line + "\n"


def world_state(text: str, y0: float) -> tuple[float, float, list]:
    """(true y, recorded offset, keep log) carried by a world node's ``train.py`` (start: y0, 0, [])."""
    ty = _get_tag(text, TRUE_Y_TAG)
    log = _get_tag(text, KEEP_LOG_TAG)
    return (float(ty) if ty is not None else float(y0), read_offset(text),
            [tuple(x) for x in json.loads(log)] if log is not None else [])


class WorldManager:
    """Scripted manager of a world node: the world's proposal law (decision-independent given the stream).

    A rule-detectable proposal is a structured no-op (the harness rejects it before any run, as the C3 rules
    would); every other proposal sets ALPHA to a value unique to the trial and names its world key, size, offset,
    kind and stream in ``extra.scripted.world`` (the controller reads key / size / offset / kind only). A fork
    continuation (``fork_trial``) proposes from the root stream (repetition 0) up to the fork trial and from its
    own repetition's stream after it, as the analysis simulator's ``run_leaf``."""

    deterministic = True

    def __init__(self, node: "WorldNode", seed: int, repetition: int, fork_trial: int | None = None) -> None:
        from r1.tracks import worlds as WD
        self.node, self.seed, self.repetition = node, int(seed), int(repetition)
        self.mode = f"scripted_{node.name}"
        w, rg = node.world(), node.regime()
        tab = WD.theta_table(w, rg, node.world_seed, self.seed)
        root_seed = node.stream_seed(self.seed, 0)
        own_seed = node.stream_seed(self.seed, self.repetition)
        if fork_trial is None or self.repetition == 0:
            segs, self.seg_seeds = WD.Stream(own_seed, rg.llm_cap), [(1, own_seed)]
        else:
            segs = [(1, WD.Stream(root_seed, rg.llm_cap)), (int(fork_trial) + 1, WD.Stream(own_seed, rg.llm_cap))]
            self.seg_seeds = [(1, root_seed), (int(fork_trial) + 1, own_seed)]
        self.sequence = WD.proposal_sequence(w, rg, tab, segs)
        self.start = start_values()

    def stream_of(self, t: int) -> list:
        return [sd for t0, sd in self.seg_seeds if t0 <= t][-1]

    def propose_next_trial(self, status, memory_context, node_spec) -> ManagerProposal:
        t = int(status.budget_index)
        p = self.sequence[t - 1]
        key = WORLD_EDIT_KEY
        old = str(status.current_constants[key])
        new = old if p.rule else repr(float(self.start[key]) * math.exp(WORLD_EDIT_STEP * t))
        path = node_spec.editable_paths[0]
        world = {"t": t, "kind": "rule"} if p.rule else \
            {"t": t, "key": p.key, "size": p.size, "off": p.off, "kind": p.kind, "stream": list(self.stream_of(t))}
        return ManagerProposal(
            manager_mode=self.mode, proposal_summary=f"{self.node.name} t={t} {p.kind}",
            proposal_rationale=f"Scripted {self.node.name} world proposal (Track S synthetic control).",
            target_files=tuple(node_spec.editable_paths),
            objective=f"Change {key} from {old} to {new} in {path} and keep all other hyperparameters unchanged.",
            extra={"structured_edit": {"type": "python_constant", "path": path, "symbol": key, "old": old, "new": new},
                   "scripted": {"node": self.node.name, "seed": self.seed, "repetition": self.repetition,
                                "world": world}})


class WorldWorker:
    """Harness ``Worker`` of a world node: delta from the world law, delta_hat = delta + eps exactly.

    The candidate's ``train.py`` carries its true value (incumbent's + delta), its recorded offset (incumbent's +
    eps) and the keep log (incumbent's + this trial's feedback record, used by P2 if the candidate is kept);
    reported metric = true value + offset. ``runs`` counts this campaign's worker runs (a leaf starts from the
    snapshot's count): the P2 feedback scale uses runs_used / W at the keep."""

    mode = "tracks_world_worker"

    def __init__(self, node_root: str | Path, node: "WorldNode", seed: int, *, runs0: int = 0) -> None:
        self.node_root = Path(node_root).resolve()
        self.node, self.seed, self.runs = node, int(seed), int(runs0)
        self._train_seed = self._split_seed = int(seed)  # recorded by harness snapshots (leaf rebuild)

    def run_trial(self, proposal, node_spec, budget_index):
        self.runs += 1
        path = self.node_root / "train.py"
        files = self.node.candidate_files({"train.py": path.read_text()}, proposal, self.seed, self.runs)
        path.write_text(files["train.py"])
        y, off, _ = world_state(files["train.py"], self.node.world().y0)
        return WorkerResult(worker_mode=self.mode, changed_files=("train.py",), success=True,
                            parsed_metrics={"val_score": float(y + off)}, raw_log_ref="", patch_ref="synthetic.diff",
                            git_commit_before="", git_commit_after="", failure_message=None)


@dataclass
class WorldNode:
    """A rev.-7 synthetic control node: an analysis-simulator world (``r1.tracks.worlds``) on the digits_mlp
    surface. ``params``: variant (P worlds: diffuse | concentrated), strength (the declared S0.6 value), world_seed,
    llm_cap and W (bound by the collector to the run's), p_rule, sigma_audit, and ``world`` (World overrides)."""

    name: str
    params: dict
    surface: str = SURFACE
    synthetic_world: bool = True

    def __post_init__(self) -> None:
        from r1.tracks import worlds as WD
        bad = set(self.params) - set(WORLD_PARAMS)
        if bad:
            raise ValueError(f"{self.name}: unknown world-node parameters {sorted(bad)} (legacy nodes: "
                             "mechanism=loglinear)")
        kind = NODE_WORLDS[self.name]
        if kind == "N0":
            if self.params.get("variant") not in (None, "none"):
                raise ValueError("N0 has no variant")
            if float(self.params.get("strength", 0.0)) != 0.0:
                raise ValueError("N0 has zero oracle gain by construction; strength must be 0")
        elif self.params.get("variant", "diffuse") not in VARIANTS:
            raise ValueError(f"variant must be one of {VARIANTS}")
        self.world()  # validates the overrides
        W, cap = self.params.get("W"), self.params.get("llm_cap", 40)
        if kind == "N0" and W is not None and int(W) != int(cap):
            raise ValueError("N0 runs at the non-binding W = llm_cap (analysis simulator)")
        _ = WD

    # ---- the world
    @property
    def kind(self) -> str:
        return NODE_WORLDS[self.name]

    @property
    def variant(self) -> str | None:
        return None if self.kind == "N0" else self.params.get("variant", "diffuse")

    @property
    def world_seed(self) -> int:
        return int(self.params.get("world_seed", 20261029))

    def world(self):
        from r1.tracks import worlds as WD
        return WD.make_world(self.kind, float(self.params.get("strength", 0.0)), self.variant,
                             **dict(self.params.get("world") or {}))

    def regime(self):
        from r1.tracks import worlds as WD
        return WD.Regime(llm_cap=int(self.params.get("llm_cap", 40)), p_rule=float(self.params.get("p_rule", 0.55)),
                         sigma_audit=float(self.params.get("sigma_audit", 0.004)))

    def bind(self, *, W: int, llm_cap: int) -> "WorldNode":
        """The run's W and LLM cap (the world's trial horizon and the P2 budget fraction use them)."""
        if self.params.get("W") is not None and int(self.params["W"]) != int(W):
            raise ValueError(f"{self.name}: params W={self.params['W']} != run W={W}")
        if self.params.get("llm_cap") is not None and int(self.params["llm_cap"]) != int(llm_cap):
            raise ValueError(f"{self.name}: params llm_cap={self.params['llm_cap']} != run cap={llm_cap}")
        p = {**self.params, "W": int(W), "llm_cap": int(llm_cap)}
        return WorldNode(self.name, p)

    def stream_seed(self, seed: int, repetition: int) -> list[int]:
        return [self.world_seed, int(seed), WORLD_STREAM_TAG, int(repetition)]

    @property
    def W(self) -> int:
        if self.params.get("W") is None:
            raise ValueError(f"{self.name}: W is not bound (WorldNode.bind)")
        return int(self.params["W"])

    @property
    def sigma_node(self) -> float:
        return float(self.world().sigma_cmp)

    # ---- the file transform shared by the worker, the oracle and the collector's replays
    def candidate_files(self, inc_files: dict[str, str], proposal, seed: int, runs_used: int) -> dict[str, str]:
        """The candidate's files after a run of ``proposal`` on the incumbent (``runs_used`` incl. this run)."""
        from r1.tracks import worlds as WD
        extra = proposal.get("extra") if isinstance(proposal, dict) else proposal.extra
        edit, blk = extra["structured_edit"], extra["scripted"]["world"]
        if blk.get("kind") == WD.RULE:
            raise ValueError("a rule-detectable world proposal is never run")
        w, rg = self.world(), self.regime()
        text = apply_edit(dict(inc_files), edit)["train.py"]
        y_inc, off_inc, log = world_state(inc_files["train.py"], w.y0)
        tab = WD.theta_table(w, rg, self.world_seed, int(seed))
        s = WD.Stream(blk["stream"], rg.llm_cap)
        p = WD.Proposal(int(blk["t"]), False, int(blk["key"]), float(blk["size"]), float(blk["off"]), blk["kind"])
        delta = WD.true_increment(w, rg, tab, p, s, log)
        eps = WD.measurement_noise(w, p, s)
        entry = WD.keep_log_entry(w, p.t, int(runs_used), self.W)
        text = _set_tag(text, TRUE_Y_TAG, repr(float(y_inc + delta)))
        text = set_offset(text, off_inc + eps)
        text = _set_tag(text, KEEP_LOG_TAG, json.dumps(log + ([list(entry)] if entry else [])))
        return {**inc_files, "train.py": text}

    def files_after(self, rows: list[dict], start_files: dict[str, str], seed: int, upto: int) -> dict[str, str]:
        """Incumbent files after trial ``upto``, replaying the kept trials with the world transform."""
        files, runs = dict(start_files), 0
        for row in rows:
            if int(row["budget_index"]) > upto:
                break
            if parsed_metric(row) is None or row.get("decision") == "skipped":
                continue
            runs += 1
            if row["decision"] == "kept":
                files = self.candidate_files(files, {"extra": (row.get("extra") or {}).get("manager") or {}},
                                             seed, runs)
        return files

    # ---- node interface (as ``SyntheticNode``)
    def manager(self, seed: int, repetition: int, fork_trial: int | None = None) -> WorldManager:
        return WorldManager(self, seed, repetition, fork_trial=fork_trial)

    def worker(self, node_root: Path, seed: int, runs0: int = 0) -> WorldWorker:
        return WorldWorker(node_root, self, seed, runs0=runs0)

    def true_y(self, files: dict[str, str]) -> float:
        return world_state(files["train.py"], self.world().y0)[0]

    def audit(self, seed_instance: int, files: dict[str, str], seeds) -> list[float]:
        y = self.true_y(files)
        sa = self.regime().sigma_audit
        h = int(hashlib.sha256(files["train.py"].encode()).hexdigest()[:8], 16)
        return [float(y + sa * np.random.default_rng([int(seed_instance), int(s), h, 31]).standard_normal())
                for s in seeds]

    def prior(self) -> A2UPrior:
        """The controller's model of the world (keyed mode): the theta prior and the measurement model only."""
        from r1.tracks import worlds as WD
        from r1.tracks.a2u import KEYED_MODEL
        w = self.world()
        kp = KindPrior(mu0=float(w.mu0), tau0=float(w.tau0), sigma_cmp=float(w.sigma_cmp), tau_w=float(w.sigma_eta))
        return A2UPrior(node=SURFACE, sigma_node=float(w.sigma_cmp), kinds={"local": kp},
                        meta={"label": "SYNTHETIC", "node": self.name, "model": KEYED_MODEL,
                              "world": WD.world_meta(w, self.regime())})

    def describe(self) -> dict:
        return {"name": self.name, "surface": self.surface, "mechanism": "world", "world_kind": self.kind,
                "variant": self.variant, "params": json.loads(json.dumps(self.params)),
                "world": self.world().to_dict()}


def synthetic_node(name: str, params: dict | None = None):
    """A synthetic node: the rev.-7 world (``WorldNode``, default) or, with ``mechanism="loglinear"``, the
    rev.-6 log-linear placeholder node (``SyntheticNode``; engineering tests only, not a declared control)."""
    if name not in SYNTHETIC_NODES:
        raise ValueError(f"unknown synthetic node {name!r}; declared: {SYNTHETIC_NODES}")
    params = dict(params or {})
    if params.get("mechanism", "world") == "loglinear":
        params.pop("mechanism")
        merged = {**DEFAULT_PARAMS[name], **params}
        return SyntheticNode(name=name, params=merged)
    params.pop("mechanism", None)
    return WorldNode(name=name, params=params)
