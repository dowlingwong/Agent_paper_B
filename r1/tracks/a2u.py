"""A2-U: the Bayes-updating myopic base controller of Track S (runbook rev. 3 §3, as amended for rev. 4).

AI-assisted (Claude, 29 Oct 2026). ENGINEERING_ONLY until a Track S authorization exists.
Not the deployed C3 rule, and stated as such (runbook §3, §10).

Hierarchical normal model (per campaign, raw metric units, direction-adjusted Delta):

* groups j = (edit key, sign of the step) (rev.-4 amendment MA-1); the sign is the
  featurizer's ``direction`` (+1 / -1; categorical or non-numeric edits form the
  group "0");
* group mean m_j ~ N(mu0, tau0^2), (mu0, tau0) the node prior of the edit kind
  (``r1.c3.control.edit_kind``) fitted on the S0.4 dev campaigns (``fit_prior``);
* a single proposal in group j has increment Delta ~ N(m_j, tau_w^2) (tau_w the
  within-group sd) and Delta_hat = Delta + N(0, sigma_cmp^2);
* every executed, non-rule Delta_hat earlier in the campaign is an observation of
  m_j with variance lambda * (sigma_cmp^2 + tau_w^2), lambda >= 1 a declared
  inflation for within-incumbent-spell correlation (constructor ``obs_inflation``,
  default 1.0); the conjugate update gives the posterior (mu_n, tau_n) of m_j;
* the forecast of a new proposal is the **predictive** law
  Delta ~ N(mu_n, tau_n^2 + tau_w^2) (never tau_n alone).

With tau_w = 0 and lambda = 1 this is the runbook rev.-3 §3 statement. ``fit_prior``
sets tau0^2 = tau_A2^2 - tau_w^2 so that the forecast before any observation equals
A2's node prior; ``within_key="none"`` pins tau_w = 0.

Decisions (T4 Propositions 6 and 8 through ``r1.c3.rules``):

* E1: no-ops and duplicates are rule-skipped as in A2 (the C3 featurizer's replay),
  ``skip_reason`` ``rule_noop`` / ``rule_duplicate``; otherwise execute iff
  (1 - pi) V(t*; mu_n, tau, sigma_cmp) >= g, pi = 0, tau the predictive sd; else
  skip with ``prior_no_gain``.
* E2: keep by the Bayes threshold with the updated predictive law: the harness keep
  rule ``bayes_threshold/v1`` with this controller's ``keep_prior``. No verify.

No hidden state: every decision is a function of the ``ControlView`` and the
constructor arguments, so a controller rebuilt at a fork decides as the root's did.
``log`` is a record only.

Policies on the same machinery (one class):

* ``A2UController(prior, ctx, g=g0)``: the root / continuation controller at the
  pilot price g0 (rev.-4 amendment 2; the declared g is recorded separately);
* the dynamic threshold family (rev. 7, positional as the analysis branch's ``analyze.policy_string``)
  ``dynamic:g0,b_budget,b_info,h0,h_budget,r1bar,taubar,r2bar`` (or the 5-value form, zero centres), with
  r = runs_left / W - proposals_left / N_cap (worker runs; proposals incl. the current one):
  E1 execute iff V*_n + b_info (tau_pred,n - taubar) >= g0 - b_budget (r - r1bar); E2 keep iff
  m_hat_n > h0 - h_budget (r - r2bar) (h_budget of either sign). r1bar, taubar are m*'s mean r and
  tau_pred over its eligible E1 dev decisions, r2bar its mean r over eligible E2 decisions;
* ``static_price(prior, ctx, g_hat, e2_offset=y)``: m_g-hat and ``static:<x>,<y>``
  (E1 execute iff V* >= x, E2 keep iff m_hat > y): exactly the dynamic family with
  b_budget = b_info = h_budget = 0, whatever the centres;
* operators (rev. 7.1 m9), every policy: execute uses ">=" and keep uses ">" (``static:0,h`` executes
  every non-rule proposal, V* = 0 included); ties otherwise have probability zero;
* ``c_hat=fn``: pi' of §3, execute iff V* + C(s) > 0, keep iff m_hat + C(s) > 0;
* ``score_fn=fn``: ``pi_prime:<model_file>`` (secondary), execute iff f(s_E1) > 0, keep iff
  f(s_E2) > 0 (``RidgeScore`` loads f from JSON); its features include the A2-U index and the
  budget terms (``POLICY_EXTRA_FEATURES``), so it nests the static and dynamic rules (up to ties);
* ``update=False``: A2 (constant per node and kind; descriptive only).

``fn(state)`` receives the pre-declared ``schema.STATE_FEATURES``, ``epoch`` ("E1"/"E2")
and ``POLICY_EXTRA_FEATURES``; ``runs_left``, ``budget_fraction`` and ``budget_gap`` are
worker-run quantities (harness ``ComputeBudget.remaining``), never the trial-indexed
``budget_frac_left`` of ``r1.c3.features``. A non-default keep score h(m_hat) is passed to the harness as
the Bayes threshold of a shifted keep prior; this is exact when h is affine and
increasing in m_hat (checked at three points; otherwise the controller refuses).
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np
from scipy.stats import norm

from r1.c3 import rules
from r1.c3.arms import TAU_FLOOR_Z, RulesPrior
from r1.c3.control import c3_budgets, edit_kind
from r1.c3.features import (NodeContext, ReplayError, ReplayProposal, ReplayView, _LedgerState, _as_row,
                            _proposal_edit, _row_edit, active_projection, parsed_metric)
from r1.c3.labels import moments, soft_label
from r1.diagnostics.di_test import configuration
from r1.harness import import_harness
from r1.tracks.schema import STATE_FEATURES

import_harness()

from autoresearch.control_plane.action_versions import KEEP_RULE_BAYES, ActionVersions, KeepPrior  # noqa: E402
from autoresearch.control_plane.controller import ControlDecision  # noqa: E402
from autoresearch.memory.summarizer import SKIP_DISPLAY_ONE_LINE, check_skip_display  # noqa: E402

A2U_VERSION = "a2u/v2"
PI_PRIME_VERSION = "a2u_pi_prime/v2"
SCORE_POLICY_VERSION = "a2u_score/v2"
EXECUTE_NON_RULE_VERSION = "execute_non_rule/v2"
PRIOR_SCHEMA = "tracks_a2u_prior/v2"
SCORE_MODEL_SCHEMA = "tracks_score_model/v1"
KINDS = ("local", "structural")
KEYED_MODEL = "keyed_size/v1"  # prior.meta["model"] of the synthetic worlds (``_keyed_forecast``)
# Extra policy inputs (not schema state features): r of the dynamic family and the predictive sd tau_pred.
POLICY_EXTRA_FEATURES = ("budget_gap", "tau_pred")
SKIP_DISPLAY = SKIP_DISPLAY_ONE_LINE  # the deployed display (R1-SKIP-DISPLAY); runbook §4 settings


# ---------------------------------------------------------------------------
# The prior file (S0.4)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class KindPrior:
    mu0: float          # prior mean of a group mean
    tau0: float         # prior sd of a group mean (> 0)
    sigma_cmp: float    # comparison noise of one Delta_hat (> 0)
    tau_w: float = 0.0  # within-group sd of single proposals (>= 0)

    def __post_init__(self) -> None:
        for name in ("mu0", "tau0", "sigma_cmp", "tau_w"):
            if not math.isfinite(float(getattr(self, name))):
                raise ValueError(f"KindPrior.{name} must be finite")
        if self.tau0 <= 0 or self.sigma_cmp <= 0 or self.tau_w < 0:
            raise ValueError("KindPrior needs tau0, sigma_cmp > 0 and tau_w >= 0")


@dataclass(frozen=True)
class A2UPrior:
    node: str
    sigma_node: float
    kinds: dict          # kind -> KindPrior
    meta: dict = field(default_factory=dict)
    # Optional per-group priors "KEY|sign" -> KindPrior (e.g. the synthetic P0 world, whose groups have known
    # distinct means so that V* varies across proposals). Empty for fitted priors; then the kind prior serves.
    groups: dict = field(default_factory=dict)

    def for_group(self, kind: str, key: str | None, sign: str) -> KindPrior:
        return self.groups.get(f"{key}|{sign}") or self.kind(kind)

    def kind(self, kind: str) -> KindPrior:
        if kind in self.kinds:
            return self.kinds[kind]
        if "local" in self.kinds:  # a kind never fitted falls back to the local prior (flagged in the detail)
            return self.kinds["local"]
        raise KeyError(f"prior has no kind {kind!r}")

    def to_payload(self) -> dict:
        payload = {"schema": PRIOR_SCHEMA, "node": self.node, "sigma_node": float(self.sigma_node),
                   "kinds": {k: asdict(v) for k, v in sorted(self.kinds.items())}, "meta": self.meta}
        if self.groups:
            payload["groups"] = {k: asdict(v) for k, v in sorted(self.groups.items())}
        return payload

    def canonical_bytes(self) -> bytes:
        return (json.dumps(self.to_payload(), sort_keys=True, indent=1) + "\n").encode("utf-8")

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    def save(self, path: str | Path) -> str:
        """Write the canonical file; returns its sha256 (the hash of the file's bytes)."""
        Path(path).write_bytes(self.canonical_bytes())
        return self.sha256

    @classmethod
    def from_payload(cls, payload: Mapping) -> "A2UPrior":
        if payload.get("schema") != PRIOR_SCHEMA:
            raise ValueError(f"not an A2-U prior ({payload.get('schema')!r})")
        return cls(node=str(payload["node"]), sigma_node=float(payload["sigma_node"]),
                   kinds={k: KindPrior(**v) for k, v in payload["kinds"].items()}, meta=dict(payload.get("meta") or {}),
                   groups={k: KindPrior(**v) for k, v in (payload.get("groups") or {}).items()})

    @classmethod
    def load(cls, path: str | Path, expect_sha256: str | None = None) -> "A2UPrior":
        data = Path(path).read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        if expect_sha256 is not None and sha != expect_sha256:
            raise ValueError(f"prior file {path} has sha256 {sha}, expected {expect_sha256}")
        prior = cls.from_payload(json.loads(data))
        if prior.sha256 != sha:
            raise ValueError(f"prior file {path} is not in canonical form (re-save it with A2UPrior.save)")
        return prior


def sign_of(direction) -> str:
    """Group sign from the featurizer's ``direction`` (+1 / -1; anything else is "0")."""
    try:
        d = float(direction)
    except (TypeError, ValueError):
        return "0"
    return "+" if d > 0 else "-" if d < 0 else "0"


def fit_prior(rows: list[Mapping], node: str, sigma_node: float, *, k_label: int,
              within_key: str = "estimated", sources: Mapping | None = None, min_rows: int = 5) -> A2UPrior:
    """Fit A2-U's prior from S0.4 audited dev rows (ENGINEERING_ONLY; never quoted as a result).

    ``rows``: executed, non-rule proposals (trial >= 2), each
    ``{"instance", "key", "sign", "kind", "delta_hat", "delta_audit", "se"}`` in raw metric units.

    * (mu_A2, tau_A2) per kind: A2's node prior, ``r1.c3.arms.RulesPrior`` on the ``pooled_node``
      soft labels of ``delta_audit`` (weight 1), moments with the arms' tau floor;
    * sigma_cmp^2 = mean (Delta_hat - Delta_audit)^2 - mean se^2, floored at (0.1 sigma_node)^2;
    * tau_w^2 = pooled within-(instance, key, sign) variance of Delta_audit - mean se^2, floored at 0
      (``within_key="none"``: 0); tau0^2 = max(tau_A2^2 - tau_w^2, (TAU_FLOOR_Z sigma_node)^2).
    """
    if within_key not in ("estimated", "none"):
        raise ValueError("within_key must be 'estimated' or 'none'")
    floor = TAU_FLOOR_Z * sigma_node
    kinds: dict[str, KindPrior] = {}
    stats: dict[str, dict] = {}
    for kind in KINDS:
        rs = [r for r in rows if r["kind"] == kind and r.get("delta_audit") is not None]
        if len(rs) < min_rows:
            continue
        lab = [{"node": f"{node}:{kind}", "noop": False, "duplicate": False, "weight": 1.0,
                "soft": soft_label(float(r["delta_audit"]), None, sigma_node, sigma_mode="pooled_node",
                                   k_label=k_label)} for r in rs]
        probs = RulesPrior().fit(lab).by_node[f"{node}:{kind}"]
        _, mu_a2, tau_a2 = (float(x) for x in moments(probs, sigma_node, tau_floor_z=TAU_FLOOR_Z))
        se2 = float(np.mean([float(r["se"]) ** 2 if r.get("se") is not None else 0.0 for r in rs]))
        resid = [float(r["delta_hat"]) - float(r["delta_audit"]) for r in rs if r.get("delta_hat") is not None]
        s_cmp2 = max(float(np.mean(np.square(resid))) - se2 if resid else 0.0, (0.1 * sigma_node) ** 2)
        tw2 = 0.0
        if within_key == "estimated":
            groups: dict[tuple, list[float]] = defaultdict(list)
            for r in rs:
                groups[(r["instance"], r["key"], r.get("sign", "0"))].append(float(r["delta_audit"]))
            ss = sum(float(np.sum((np.asarray(g) - np.mean(g)) ** 2)) for g in groups.values() if len(g) > 1)
            dof = sum(len(g) - 1 for g in groups.values() if len(g) > 1)
            tw2 = max(ss / dof - se2, 0.0) if dof > 0 else 0.0
        tau0 = math.sqrt(max(tau_a2 ** 2 - tw2, floor ** 2))
        kinds[kind] = KindPrior(mu0=mu_a2, tau0=tau0, sigma_cmp=math.sqrt(s_cmp2), tau_w=math.sqrt(tw2))
        stats[kind] = {"rows": len(rs), "mu_a2": mu_a2, "tau_a2": tau_a2, "mean_se2": se2,
                       "instances": len({r["instance"] for r in rs})}
    if not kinds:
        raise ValueError(f"no kind has >= {min_rows} audited rows")
    meta = {"label": "ENGINEERING_ONLY", "fit": "fit_prior/v2", "within_key": within_key, "k_label": int(k_label),
            "groups": "(key, sign of step)", "tau_floor_z": TAU_FLOOR_Z, "stats": stats, "sources": dict(sources or {})}
    return A2UPrior(node=node, sigma_node=float(sigma_node), kinds=kinds, meta=meta)


# ---------------------------------------------------------------------------
# The group update
# ---------------------------------------------------------------------------

def group_posterior(kp: KindPrior, deltas, obs_inflation: float = 1.0) -> tuple[float, float]:
    """Posterior (mu_n, tau_n) of a group mean from executed Delta_hat (obs var lambda (sigma^2 + tau_w^2))."""
    d = [float(x) for x in deltas]
    obs_var = float(obs_inflation) * (kp.sigma_cmp ** 2 + kp.tau_w ** 2)
    prec = 1.0 / kp.tau0 ** 2 + len(d) / obs_var
    var = 1.0 / prec
    mu = var * (kp.mu0 / kp.tau0 ** 2 + sum(d) / obs_var)
    return mu, math.sqrt(var)


def posterior_mean(delta_hat: float, mu: float, tau: float, sigma: float) -> float:
    """m_hat = E[Delta | Delta_hat] for Delta ~ N(mu, tau^2), Delta_hat = Delta + N(0, sigma^2)."""
    return (tau ** 2 * float(delta_hat) + sigma ** 2 * mu) / (tau ** 2 + sigma ** 2)


STALE_PROPOSAL = "stale_proposal"


class StaleProposalError(ReplayError):
    """The view's own proposal does not apply to the replayed incumbent (R1-TRACKS-A2U-STALE).

    The harness rejects such a proposal as ``PROPOSAL_PRECONDITION_FAILED`` (an invalid trial, no worker
    run) but still calls the controller for that trial; ``replay`` raises this subclass only for the current
    proposal, so an inconsistent ledger prefix still raises a plain ``ReplayError``."""


def _proj_sha(projection: str) -> str:
    return hashlib.sha256(projection.encode()).hexdigest()[:16]


@dataclass
class Replay:
    """What A2-U reads from a ledger prefix (``replay``)."""

    deltas: dict            # (key, sign) -> executed non-rule Delta_hat, in order
    first_eval: dict        # active projection -> budget index of its first evaluation
    keeps: int              # kept trials (trial 1 counted)
    skips: int              # skipped trials (E1 skips of any reason)
    executed_keys: set      # keys of every executed trial with a metric (trial 1 included)
    current: Any            # features.FeatureResult of the view's proposal, or None


def replay(view, ctx: NodeContext) -> Replay:
    """One pass over the view's ledger prefix with the C3 featurizer's replay (``features._LedgerState``)."""
    b_now = int(view.budget_index)
    state = _LedgerState(ctx)
    deltas: dict[tuple, list[float]] = defaultdict(list)
    first_eval: dict[str, int] = {}
    keeps = skips = 0
    last_keep = 0
    executed_keys: set[str] = set()
    for record in view.ledger_prefix:
        row = _as_row(record)
        b = int(row["budget_index"])
        if b >= b_now:
            raise ValueError(f"ledger prefix holds trial {b} at or after trial {b_now}")
        decision = row.get("decision")
        if decision == "skipped":
            skips += 1
        metric = parsed_metric(row)
        edit = _row_edit(row)
        if decision != "skipped" and metric is not None:
            res = state.featurize(edit, b, row.get("current_best_before")) if edit else None
            if res is not None and not res.noop and not res.duplicate and row.get("delta_vs_best") is not None:
                deltas[(edit["symbol"], sign_of(res.features.get("direction")))].append(float(row["delta_vs_best"]))
            if edit:
                executed_keys.add(edit["symbol"])
            _, cand_cfg = state.candidate(edit, b)
            first_eval.setdefault(active_projection(cand_cfg, ctx.node), b)
            if row.get("current_best_before") is not None:
                first_eval.setdefault(active_projection(state.cur_cfg, ctx.node), last_keep)
        if decision == "kept":
            keeps += 1
            last_keep = b
        state.observe(row)
    current = None
    if view.proposal is not None:
        try:
            current = state.featurize(_proposal_edit(view.proposal), b_now, view.current_best)
        except ReplayError as exc:
            raise StaleProposalError(str(exc)) from exc
    return Replay(deltas=dict(deltas), first_eval=first_eval, keeps=keeps, skips=skips,
                  executed_keys=executed_keys, current=current)


def _runs(view, W: int | None) -> tuple[int, int]:
    """(worker runs used, worker-run cap) from the harness budget view (``ComputeBudget.remaining``)."""
    budget = getattr(view, "budget", None) or {}
    used = int(budget.get("worker_runs_used", 0) or 0)
    left = budget.get("worker_runs_remaining")
    total = (used + int(left)) if left is not None else W
    if total is None:
        raise ValueError("the view's budget has no worker-run cap and no W was given")
    return used, int(total)


def state_features(view, rep: Replay, *, key: str | None, index_value: float | None, W: int | None = None) -> dict:
    """The pre-declared state features of a decision (``schema.STATE_FEATURES``; worker-run budget)."""
    used, total = _runs(view, W)
    state = {
        "budget_fraction": used / total if total else 0.0,
        "runs_left": float(total - used),
        "trial_index": float(view.budget_index),
        "key_seen": float(bool(key) and key in rep.executed_keys),
        "prior_skips": float(rep.skips),
        "keeps_so_far": float(rep.keeps),
        "index_value": float(index_value) if index_value is not None else math.nan,
    }
    assert tuple(state) == STATE_FEATURES
    return state


def budget_gap(view, W: int | None = None) -> float:
    """r = runs_left / W - proposals_left / N_cap (worker runs; proposals including the current one).

    proposals_left = min(trials_remaining, llm_calls_remaining + 1) (the current trial is not yet consumed and
    its manager call is already charged) and N_cap = min(trial budget, LLM cap): with an LLM manager both count
    proposals; a scripted (deterministic) manager makes no counted call and the trial budget (= the cap under
    ``c3_budgets``) counts them."""
    used, total = _runs(view, W)
    budget = getattr(view, "budget", None) or {}
    left_t, total_t = budget.get("trials_remaining"), budget.get("trials_total")
    left_l, used_l = budget.get("llm_calls_remaining"), budget.get("llm_calls_used", 0)
    lefts = [int(x) for x in (left_t, None if left_l is None else int(left_l) + 1) if x is not None]
    caps = [int(x) for x in (total_t, (int(left_l) + int(used_l or 0)) if left_l is not None else None) if x is not None]
    if not lefts or not caps:
        raise ValueError("the view's budget has no proposal cap (trials or LLM calls)")
    return (total - used) / total - min(lefts) / min(caps)


def policy_state(view, rep: Replay, fc: dict, *, epoch: str, index_value: float | None, W: int | None = None) -> dict:
    """What a policy function sees: ``epoch``, ``STATE_FEATURES`` and ``POLICY_EXTRA_FEATURES``."""
    state = {"epoch": epoch, **state_features(view, rep, key=fc["key"], index_value=index_value, W=W)}
    state["budget_gap"] = budget_gap(view, W)
    state["tau_pred"] = fc["tau"]
    return state


def _f(x) -> float | None:
    x = float(x)
    return x if math.isfinite(x) else None


# ---------------------------------------------------------------------------
# Score models (S3e ``pi_prime:<model_file>``)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RidgeScore:
    """f(s) = intercept + sum_j coef_j s_j + coef_e2 1{epoch = E2}, over STATE_FEATURES + POLICY_EXTRA_FEATURES.

    File (JSON): {"schema": "tracks_score_model/v1", "intercept": a, "coef": {feature: b, ..., "e2": c},
    "meta": {...}}; missing coefficients are 0; NaN state values count as 0."""

    intercept: float
    coef: dict
    meta: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        unknown = set(self.coef) - set(STATE_FEATURES) - set(POLICY_EXTRA_FEATURES) - {"e2"}
        if unknown:
            raise ValueError(f"unknown score-model features {sorted(unknown)}")

    def __call__(self, state: Mapping) -> float:
        total = float(self.intercept) + float(self.coef.get("e2", 0.0)) * float(state.get("epoch") == "E2")
        for name in STATE_FEATURES + POLICY_EXTRA_FEATURES:
            v = float(state.get(name, 0.0))
            total += float(self.coef.get(name, 0.0)) * (0.0 if math.isnan(v) else v)
        return total

    @classmethod
    def load(cls, path: str | Path) -> tuple["RidgeScore", str]:
        data = Path(path).read_bytes()
        payload = json.loads(data)
        if payload.get("schema") != SCORE_MODEL_SCHEMA:
            raise ValueError(f"not a Track S score model ({payload.get('schema')!r})")
        return cls(float(payload["intercept"]), dict(payload["coef"]), dict(payload.get("meta") or {})), \
            hashlib.sha256(data).hexdigest()


POLICY_FILE_SCHEMA = "tracks_policy/v1"   # the analysis' π′ / m̃ export (``analyze.write_policy``)


@dataclass(frozen=True)
class PolicyFileScore:
    """π′ from the analysis' ``tracks_policy/v1`` file (final review MINOR 2): score(s) = the ridge model's output
    minus the epoch's threshold, exactly ``analyze.policy_score`` (act iff > 0). An epoch the model was not trained
    on falls back to A2-U's myopic rule at g = 0 (score = the index value), as the analysis simulator's
    ``LinearPolicy``."""

    policy: dict

    def __post_init__(self) -> None:
        if self.policy.get("schema") != POLICY_FILE_SCHEMA or list(self.policy.get("features", [])) != list(STATE_FEATURES):
            raise ValueError("not a tracks_policy/v1 file with the schema's STATE_FEATURES order")

    def __call__(self, state: Mapping) -> float:
        from r1.tracks import analyze
        epoch = state["epoch"]
        if epoch not in self.policy.get("trained_epochs", []):
            return float(state["index_value"])
        return float(analyze.policy_score(self.policy, state, epoch))


def load_score_model(path: str | Path):
    """(score function, sha256 of the file bytes) of ``pi_prime:<file>``: ``tracks_policy/v1`` (the analysis'
    export) or ``tracks_score_model/v1`` (``RidgeScore``)."""
    data = Path(path).read_bytes()
    payload = json.loads(data)
    sha = hashlib.sha256(data).hexdigest()
    if payload.get("schema") == POLICY_FILE_SCHEMA:
        return PolicyFileScore(payload), sha
    if payload.get("schema") == SCORE_MODEL_SCHEMA:
        return RidgeScore(float(payload["intercept"]), dict(payload["coef"]), dict(payload.get("meta") or {})), sha
    raise ValueError(f"{path}: not a Track S policy file ({payload.get('schema')!r})")


# ---------------------------------------------------------------------------
# The controller
# ---------------------------------------------------------------------------

def world_block(obj) -> dict | None:
    """The ``extra.scripted.world`` block of a proposal (object or dict) or of a ledger row (``extra.manager``)."""
    if obj is None:
        return None
    extra = obj.get("extra") if isinstance(obj, dict) else getattr(obj, "extra", None)
    extra = extra or {}
    if "manager" in extra and isinstance(extra["manager"], dict):
        extra = extra["manager"]
    return ((extra.get("scripted") or {}).get("world")) or None


class A2UController:
    """A2-U and the policies built on it (module docstring). Harness ``Controller`` + ``keep_prior``."""

    deterministic = True

    def __init__(self, prior: A2UPrior, node_ctx: NodeContext, *, g: float | None = None, update: bool = True,
                 obs_inflation: float = 1.0, c_hat: Callable[[dict], float] | None = None,
                 score_fn: Callable[[dict], float] | None = None, h0: float = 0.0, b_budget: float = 0.0,
                 b_info: float = 0.0, h_budget: float = 0.0, r1_bar: float = 0.0, tau_bar: float = 0.0,
                 r2_bar: float = 0.0, W: int | None = None, g_units: float = 0.1,
                 policy_name: str | None = None) -> None:
        if not math.isclose(prior.sigma_node, node_ctx.sigma_node, rel_tol=1e-9):
            raise ValueError("prior.sigma_node must equal node_ctx.sigma_node")
        if obs_inflation < 1.0 and not math.isclose(obs_inflation, 1.0):
            raise ValueError("obs_inflation must be >= 1")
        if c_hat is not None and score_fn is not None:
            raise ValueError("give c_hat (pi') or score_fn (a full score), not both")
        if (c_hat is not None or score_fn is not None) and (h0 or b_budget or b_info or h_budget or r1_bar or tau_bar
                                                            or r2_bar):
            raise ValueError("the dynamic-threshold parameters do not combine with c_hat / score_fn")
        self.prior, self.ctx = prior, node_ctx
        self.g = float(g_units * prior.sigma_node if g is None else g)
        self.update, self.obs_inflation = bool(update), float(obs_inflation)
        self.c_hat, self.score_fn, self.W = c_hat, score_fn, W
        self.h0, self.b_budget, self.b_info, self.h_budget = float(h0), float(b_budget), float(b_info), float(h_budget)
        # rev. 7 centring (0 = uncentred): r1_bar, tau_bar at E1 and r2_bar at E2 (m*'s dev decision means)
        self.r1_bar, self.tau_bar, self.r2_bar = float(r1_bar), float(tau_bar), float(r2_bar)
        self.policy_name = policy_name  # recorded by the collector; not part of the version, so two policies
        # with identical rules (e.g. static and dynamic with zero slopes) have identical records
        base = SCORE_POLICY_VERSION if score_fn is not None else PI_PRIME_VERSION if c_hat is not None else A2U_VERSION
        tags = [f"prior={prior.sha256[:12]}", f"g={self.g:.6g}"]
        tags += [] if update else ["no_update"]
        tags += [] if self.obs_inflation == 1.0 else [f"lambda={self.obs_inflation:g}"]
        for name in ("h0", "b_budget", "b_info", "h_budget", "r1_bar", "tau_bar", "r2_bar"):
            tags += [] if getattr(self, name) == 0.0 else [f"{name}={getattr(self, name):g}"]
        self.version = f"{base}[{','.join(tags)}]"
        self.log: list[dict] = []  # record only; never read by a decision
        self.forecast_reason: str | None = None  # why the last forecast was None (STALE_PROPOSAL or None)

    @classmethod
    def static_price(cls, prior: A2UPrior, node_ctx: NodeContext, g_hat: float, *, e2_offset: float = 0.0,
                     **kwargs) -> "A2UController":
        """m_g-hat / ``static:g=<x>,e2off=<y>``: execute iff V* >= x, keep iff m_hat > y."""
        return cls(prior, node_ctx, g=float(g_hat), h0=float(e2_offset), **kwargs)

    @classmethod
    def dynamic(cls, prior: A2UPrior, node_ctx: NodeContext, *, g0: float, b_budget: float = 0.0,
                b_info: float = 0.0, h0: float = 0.0, h_budget: float = 0.0, r1_bar: float = 0.0,
                tau_bar: float = 0.0, r2_bar: float = 0.0, **kwargs) -> "A2UController":
        """``dynamic:g0,b_budget,b_info,h0,h_budget,r1bar,taubar,r2bar`` (module docstring); zero slopes give
        ``static_price(g0, e2_offset=h0)`` exactly, whatever the centres."""
        return cls(prior, node_ctx, g=float(g0), b_budget=b_budget, b_info=b_info, h0=h0, h_budget=h_budget,
                   r1_bar=r1_bar, tau_bar=tau_bar, r2_bar=r2_bar, **kwargs)

    @property
    def default_keep(self) -> bool:
        return self.c_hat is None and self.score_fn is None and self.h0 == 0.0 and self.h_budget == 0.0

    @property
    def dynamic_e1(self) -> bool:
        return self.b_budget != 0.0 or self.b_info != 0.0

    # ---- campaign wiring -------------------------------------------------
    def campaign_kwargs(self, *, W: int, llm_cap: int, trials: int | None = None,
                        skip_display: str = SKIP_DISPLAY) -> dict:
        """``run_real_campaign`` kwargs: this controller, keep rule ``bayes_threshold/v1`` with this
        controller's keep prior, split ``"vary"``, the skip display, and ``c3_budgets(W, llm_cap)``."""
        check_skip_display(skip_display)
        return {"controller": self, "keep_prior": self.keep_prior, "skip_display": skip_display,
                "action_versions": ActionVersions.new_campaign(keep_rule=KEEP_RULE_BAYES),
                **c3_budgets(W, llm_cap, trials)}

    # ---- forecasting -----------------------------------------------------
    def forecast(self, view) -> dict | None:
        """The predictive forecast of the view's proposal from the view alone; ``None`` without features.

        A current proposal that does not apply to the replayed incumbent (a stale edit) gives ``None`` with
        ``self.forecast_reason = STALE_PROPOSAL``; any other replay error still raises."""
        self.forecast_reason = None
        try:
            rep = replay(view, self.ctx)
        except StaleProposalError:
            self.forecast_reason = STALE_PROPOSAL
            return None
        res = rep.current
        if res is None:
            return None
        if self.keyed:
            return self._keyed_forecast(view, rep, res)
        edit = res.edit
        key = edit.get("symbol") if edit else None
        group = (key, sign_of(res.features.get("direction")))
        kind = edit_kind(edit)
        kp = self.prior.for_group(kind, key, group[1])
        obs = rep.deltas.get(group, []) if (self.update and key) else []
        mu_n, tau_n = group_posterior(kp, obs, self.obs_inflation)
        tau = math.sqrt(tau_n ** 2 + kp.tau_w ** 2)   # predictive sd (rev.-4 MA-1)
        sigma = kp.sigma_cmp
        t_star = float(rules.bayes_threshold(mu_n, tau, sigma))
        v_star = float(rules.proposal_value(0.0, mu_n, tau, sigma))
        cand_proj = active_projection(configuration(res.candidate_files), self.ctx.node)
        return {"rep": rep, "res": res, "key": key, "sign": group[1], "kind": kind,
                "kind_fallback": kind not in self.prior.kinds, "n_group": len(obs), "pi": 0.0,
                "mu": mu_n, "tau_n": tau_n, "tau_w": kp.tau_w, "tau": tau, "sigma": sigma,
                "t_star": t_star, "v_star": v_star, "noop": bool(res.noop), "duplicate": bool(res.duplicate),
                "duplicate_of": rep.first_eval.get(cand_proj) if res.duplicate else None,
                "candidate_projection_sha": _proj_sha(cand_proj)}

    @property
    def keyed(self) -> bool:
        return self.prior.meta.get("model") == KEYED_MODEL

    def _keyed_forecast(self, view, rep: "Replay", res) -> dict:
        """Keyed mode (``KEYED_MODEL``, the synthetic worlds of ``r1.tracks.worlds``): the proposal names its
        world key, size, offset and edit kind (``extra.scripted.world``); per key a conjugate normal posterior on
        theta from N(mu0, tau0^2) is updated by every earlier executed trial on that key (delta_hat = the metric
        minus the incumbent's, or minus the known start value y0 at trial 1), and the forecast is
        a = size (mu - offset), A = size^2 var + sigma_eta^2 (mu = a, tau = tau_pred = sqrt(A), sigma by kind)."""
        from r1.tracks import worlds
        meta = self.prior.meta["world"]
        prior_post = (float(meta["mu0"]), float(meta["tau0"]) ** 2)
        blk = world_block(view.proposal)
        posts: dict[int, tuple[float, float]] = {}
        counts: dict[int, int] = defaultdict(int)
        if self.update:
            for record in view.ledger_prefix:
                row = _as_row(record)
                b = world_block(row)
                metric = parsed_metric(row)
                if b is None or b.get("kind") == worlds.RULE or metric is None or row.get("decision") == "skipped":
                    continue
                if row.get("current_best_before") is None:
                    dhat = float(metric) - float(meta["y0"])
                elif row.get("delta_vs_best") is not None:
                    dhat = float(row["delta_vs_best"])
                else:
                    continue
                k = int(b["key"])
                posts[k] = worlds.key_update(posts.get(k, prior_post), float(b["size"]), dhat, float(b["off"]),
                                             float(meta["sigma_eta"]), worlds.sig_from_meta(meta, b["kind"]))
                counts[k] += 1
        rule = blk is None or blk.get("kind") == worlds.RULE
        k = -1 if rule else int(blk["key"])
        kind = "filler" if rule else str(blk["kind"])
        size, off = (1.0, 0.0) if rule else (float(blk["size"]), float(blk["off"]))
        post = posts.get(k, prior_post)
        a, A_ = worlds.key_forecast(post, size, off, float(meta["sigma_eta"]))
        tau = math.sqrt(A_)
        sigma = worlds.sig_from_meta(meta, kind)
        cand_proj = active_projection(configuration(res.candidate_files), self.ctx.node)
        return {"rep": rep, "res": res, "key": f"w{k}", "sign": kind, "kind": "local", "kind_fallback": False,
                "n_group": counts.get(k, 0), "pi": 0.0, "mu": a, "tau_n": abs(size) * math.sqrt(post[1]),
                "tau_w": float(meta["sigma_eta"]), "tau": tau, "sigma": sigma,
                "t_star": float(rules.bayes_threshold(a, tau, sigma)),
                "v_star": float(rules.proposal_value(0.0, a, tau, sigma)),
                "noop": bool(res.noop) or rule, "duplicate": bool(res.duplicate) and not rule,
                "duplicate_of": rep.first_eval.get(cand_proj) if (res.duplicate and not rule) else None,
                "candidate_projection_sha": _proj_sha(cand_proj)}

    def _r(self, view) -> float | None:
        try:
            return float(budget_gap(view, self.W))
        except (ValueError, TypeError, ZeroDivisionError):
            return None

    @staticmethod
    def _numbers(fc: dict) -> dict:
        return {k: (_f(fc[k]) if isinstance(fc[k], float) else fc[k]) for k in
                ("key", "sign", "kind", "kind_fallback", "n_group", "pi", "mu", "tau_n", "tau_w", "tau", "sigma",
                 "t_star", "v_star", "noop", "duplicate", "duplicate_of", "candidate_projection_sha")}

    # ---- the harness Controller interface --------------------------------
    def decide(self, view, mask: dict) -> ControlDecision:
        if view.epoch == "E1" and view.proposal is not None:
            return self._decide_e1(view, mask)
        if view.epoch == "E2":
            return ControlDecision("continue", {}, self.version, view.input_hash(), detail=self._e2_detail(view))
        return ControlDecision("continue", {}, self.version, view.input_hash())

    @staticmethod
    def _skip(mask, reason: str) -> tuple[str, dict]:
        if mask.get("skip", False):
            return "skip", {"skip_reason": reason}
        return "continue", {"rule_decision": reason, "skip_infeasible": True}

    def _decide_e1(self, view, mask) -> ControlDecision:
        b = int(view.budget_index)
        base = {"controller": self.version, "epoch": "E1"}
        fc = self.forecast(view)
        if fc is None:
            detail = {**base, "reason": self.forecast_reason or "no_features", "eligible": False}
            self.log.append({"budget_index": b, "action": "continue", **detail})
            return ControlDecision("continue", {}, self.version, view.input_hash(), detail=detail)
        # r and tau_pred of every decision are recorded (the analysis' decision_centres / threshold_act inputs).
        detail = {**base, **self._numbers(fc), "g": self.g, "r": self._r(view), "tau_pred": _f(fc["tau"])}
        if fc["noop"] or fc["duplicate"]:
            action, extra = self._skip(mask, "rule_noop" if fc["noop"] else "rule_duplicate")
            detail.update(extra, eligible=False)
            self.log.append({"budget_index": b, "action": action, **detail})
            return ControlDecision(action, {}, self.version, view.input_hash(), detail=detail)
        if self.c_hat is not None or self.score_fn is not None:
            state = policy_state(view, fc["rep"], fc, epoch="E1", index_value=fc["v_star"], W=self.W)
            score = float(self.score_fn(state)) if self.score_fn is not None else fc["v_star"] + float(self.c_hat(state))
            execute = score > 0
            margin = score
            detail.update(score=score, state=state)
        elif self.dynamic_e1:
            gap = budget_gap(view, self.W)
            bonus = self.b_info * (fc["tau"] - self.tau_bar)
            threshold = self.g - self.b_budget * (gap - self.r1_bar)
            execute = fc["v_star"] + bonus >= threshold
            margin = fc["v_star"] + bonus - threshold
            detail.update(budget_gap=gap, info_bonus=bonus, e1_threshold=threshold)
        else:
            execute = static_execute(fc["mu"], fc["tau"], fc["sigma"], self.g)
            margin = fc["v_star"] - self.g
        # ``margin``: the decision's distance to its own threshold (>= 0 executes); the collector's
        # near-threshold band is |margin| <= b, so it is centred on the policy's threshold (review M1).
        detail.update(execute=bool(execute), eligible=True, margin=_f(margin))
        if execute:
            action = "continue"
        else:
            action, extra = self._skip(mask, "prior_no_gain")
            detail.update(extra)
        self.log.append({"budget_index": b, "action": action, **detail})
        return ControlDecision(action, {"V": fc["v_star"], "g": self.g}, self.version, view.input_hash(), detail=detail)

    def _e2_detail(self, view) -> dict:
        prov = view.provisional
        delta_hat = getattr(prov, "delta_vs_best", None)
        detail: dict = {"controller": self.version, "epoch": "E2",
                        "decision": getattr(getattr(prov, "decision", None), "value", None)}
        # An invalid trial (no comparison) is not eligible whatever its proposal; checked before the forecast,
        # so a stale proposal the harness rejected cannot reach the replay (R1-TRACKS-A2U-STALE).
        if delta_hat is None:
            return {**detail, "reason": "no_features_or_no_comparison", "eligible": False}
        fc = self.forecast(view)
        if fc is None:
            return {**detail, "reason": self.forecast_reason or "no_features_or_no_comparison", "eligible": False}
        m_hat = posterior_mean(delta_hat, fc["mu"], fc["tau"], fc["sigma"])
        # The policy's keep threshold on the m_hat scale (0 for the plain Bayes keep, h for static e2off = h, ...);
        # margin = m_hat - h is what the collector's E2 band |m_hat - h| <= b uses (review M1).
        threshold = self.keep_prior(view).threshold
        m_thr = posterior_mean(threshold, fc["mu"], fc["tau"], fc["sigma"])
        detail.update(self._numbers(fc), delta_hat=float(delta_hat), m_hat=m_hat, keep_threshold_m=_f(m_thr),
                      margin=_f(m_hat - m_thr), eligible=True, r=self._r(view), tau_pred=_f(fc["tau"]))
        return detail

    # ---- E2: the keep prior (KeepPriorProvider) ----------------------------
    def _keep_score(self, view, fc: dict) -> Callable[[float], float]:
        """h(m_hat): keep iff h(m_hat) > 0 (the policy's E2 rule)."""
        if self.score_fn is None and self.c_hat is None:
            threshold = self.h0 - (self.h_budget * (budget_gap(view, self.W) - self.r2_bar) if self.h_budget != 0.0 else 0.0)
            return lambda m: m - threshold
        rep, W = fc["rep"], self.W

        def h(m: float) -> float:
            state = policy_state(view, rep, fc, epoch="E2", index_value=m, W=W)
            return float(self.score_fn(state)) if self.score_fn is not None else m + float(self.c_hat(state))
        return h

    def keep_prior(self, view) -> KeepPrior:
        fc = self.forecast(view)
        if fc is None:
            # First trial / no incumbent metric: the rule keeps the first valid metric without the prior.
            kp = self.prior.kind("local")
            return KeepPrior(mu=0.0, tau=self.prior.sigma_node, sigma=kp.sigma_cmp, source=f"{self.version}:no_features")
        mu, tau, sigma = fc["mu"], fc["tau"], fc["sigma"]
        source = f"{self.version}:group={fc['key']}{fc['sign']}:n={fc['n_group']}"
        if self.default_keep:
            return KeepPrior(mu=mu, tau=tau, sigma=sigma, source=source)
        return encoded_keep_prior(self._keep_score(view, fc), mu, tau, sigma, source)


def encoded_keep_prior(h: Callable[[float], float], mu: float, tau: float, sigma: float, source: str) -> KeepPrior:
    """The keep prior whose Bayes threshold implements "keep iff h(m_hat(Delta_hat)) > 0".

    m_hat is affine increasing in Delta_hat; for h affine increasing in m_hat the rule is Delta_hat > t' = -A/B,
    served as the threshold of a prior with mu' = -t' tau^2 / sigma^2 (checked at three points; refused otherwise).
    """
    m_of = lambda d: posterior_mean(d, mu, tau, sigma)  # noqa: E731
    a, b1, b2 = h(m_of(0.0)), h(m_of(sigma)), h(m_of(-sigma))
    slope = (b1 - a) / sigma
    if not math.isclose(b2, a - slope * sigma, rel_tol=1e-9, abs_tol=1e-12):
        raise ValueError("the policy's E2 keep score is not affine in m_hat; it cannot be served as a threshold")
    if slope <= 0:
        raise ValueError("the policy's E2 keep score does not increase with m_hat; refused (see IMPLEMENTATION_NOTES)")
    t_prime = -a / slope
    mu_prime = -t_prime * tau ** 2 / sigma ** 2
    return KeepPrior(mu=mu_prime, tau=tau, sigma=sigma, source=f"{source}:keep_threshold={t_prime:.6g}")


def static_execute(mu: float, tau: float, sigma: float, g: float) -> bool:
    """The static E1 rule: execute iff V*(mu, tau, sigma) >= g (Prop. 8, pi = 0).

    g = 0 executes every non-rule proposal (rev. 7 a): V* >= 0 holds exactly in theory; the explicit branch
    keeps floating-point rounding of V* for very negative mu from turning it into a skip."""
    if g == 0.0:
        return True
    return bool(rules.execute(0.0, mu, tau, sigma, g))


def reads_budget(controller: "A2UController") -> bool:
    """True when the controller's decisions depend on the budget (then a root ledger cannot be truncated at a
    smaller W as if it had been run there; S0.5b refuses such roots)."""
    return bool(controller.b_budget or controller.h_budget or controller.score_fn is not None
                or controller.c_hat is not None)


class ExecuteNonRuleController(A2UController):
    """S0.4 dev campaigns: rule skips as A2-U, every other proposal executed.

    ``prior=None``: keep by the harness default rule (Delta_hat > 0); with an A2-U prior: by A2-U's Bayes
    threshold."""

    def __init__(self, prior: A2UPrior | None, node_ctx: NodeContext, **kwargs) -> None:
        self._has_prior = prior is not None
        if prior is None:
            s = node_ctx.sigma_node
            prior = A2UPrior(node=node_ctx.node, sigma_node=s, kinds={"local": KindPrior(0.0, s, s, 0.0)},
                             meta={"placeholder": "no prior: forecasts unused, keep rule default/v1"})
        super().__init__(prior, node_ctx, g=-math.inf, **kwargs)
        self.version = f"{EXECUTE_NON_RULE_VERSION}[" + (f"prior={prior.sha256[:12]}" if self._has_prior else "no_prior") + "]"

    def campaign_kwargs(self, *, W: int, llm_cap: int, trials: int | None = None,
                        skip_display: str = SKIP_DISPLAY) -> dict:
        if self._has_prior:
            return super().campaign_kwargs(W=W, llm_cap=llm_cap, trials=trials, skip_display=skip_display)
        check_skip_display(skip_display)
        return {"controller": self, "skip_display": skip_display,
                "action_versions": ActionVersions.new_campaign(), **c3_budgets(W, llm_cap, trials)}


# ---------------------------------------------------------------------------
# Calibration (S0.5 coverage gate input)
# ---------------------------------------------------------------------------

def predictive_intervals(ledger, controller: A2UController, *, level: float = 0.8,
                         audit_se: Mapping[int, float] | None = None) -> list[dict]:
    """The ``level`` predictive interval of the audited Delta of every executed, non-rule proposal of a ledger.

    For trial b the forecast uses only trials < b (the controller's own predictive law
    N(mu_n, tau_n^2 + tau_w^2)); ``audit_se[b]`` (the audit's standard error) widens it by the audit noise.
    Rows: {budget_index, key, sign, mu, sd, lo, hi}."""
    rows = [_as_row(r) for r in ledger]
    z = float(norm.ppf(0.5 + level / 2.0))
    out = []
    for i, row in enumerate(rows):
        edit = _row_edit(row)
        if row.get("decision") == "skipped" or parsed_metric(row) is None or not edit:
            continue
        b = int(row["budget_index"])
        view = ReplayView(budget_index=b, ledger_prefix=tuple(rows[:i]), current_best=row.get("current_best_before"),
                          proposal=ReplayProposal(extra={"structured_edit": edit}))
        fc = controller.forecast(view)
        if fc is None or fc["noop"] or fc["duplicate"]:
            continue
        se = float((audit_se or {}).get(b, 0.0) or 0.0)
        sd = math.sqrt(fc["tau"] ** 2 + se ** 2)
        out.append({"budget_index": b, "key": fc["key"], "sign": fc["sign"], "n_group": fc["n_group"],
                    "stratum": n_group_stratum(fc["n_group"]), "mu": fc["mu"], "sd": sd,
                    "lo": fc["mu"] - z * sd, "hi": fc["mu"] + z * sd, "level": level})
    return out


def n_group_stratum(n: int) -> str:
    """Calibration strata by the group's executed observations before the proposal: 0, 1-2, >= 3."""
    return "0" if n == 0 else "1-2" if n <= 2 else ">=3"


def coverage(intervals: list[dict], audited: Mapping[int, float]) -> dict:
    """Share of intervals that contain the audited Delta (``audited``: budget index -> Delta_audit)."""
    pairs = [(iv.get("stratum"), float(iv["lo"] <= audited[iv["budget_index"]] <= iv["hi"])) for iv in intervals
             if audited.get(iv["budget_index"]) is not None]
    hits = [h for _, h in pairs]
    strata = {}
    for name in sorted({st for st, _ in pairs if st is not None}):
        hs = [h for st, h in pairs if st == name]
        strata[name] = {"n": len(hs), "coverage": float(np.mean(hs))}
    return {"n": len(hits), "coverage": float(np.mean(hits)) if hits else None,
            "level": intervals[0]["level"] if intervals else None, "by_stratum": strata}
