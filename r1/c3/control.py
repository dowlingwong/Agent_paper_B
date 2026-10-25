"""Online C3 control through the harness ``Controller.decide`` (RUNBOOK Track H.3, H.6, H.7).

ENGINEERING_ONLY; AI-assisted (Claude).  Nothing here is evidence.

``RuleController(prior, node_ctx, ...)`` is the one controller of every C3 arm
A1-A6; the arms differ only in the ``PriorModel`` passed in (C3_DESIGN §1, §5):

* **E1** (post-proposal, pre-execution).  The proposal's features come from
  ``r1.c3.features.featurize_view`` on the harness ``ControlView`` (the same
  function the offline table uses, H.2).  With the rule layer (A2 and above)
  a no-op or a duplicate is skipped first, logged as a rule skip
  (``skip_reason`` ``rule_noop`` / ``rule_duplicate``) and no forecast is made.
  Otherwise the prior's forecast gives (pi, mu, tau); T4 Proposition 8
  (``rules.execute``: execute iff (1 - pi) V(t*; mu, tau, sigma) >= g) decides
  skip (``prior_no_gain``) or continue.
* **E2** (keep).  The campaign runs keep rule ``bayes_threshold/v1`` with
  ``keep_prior=controller.keep_prior``: the forecast cached at E1 for this trial
  is served as the ``KeepPrior`` (mu, tau, sigma), so E1 and E2 use one
  forecast.  Only when the executed proposal differs from the one forecast at
  E1 (the hybrid's revise, or a resumed trial) is it forecast again, and that is
  recorded.
* Every E1 decision event records the bin probabilities, pi, mu, tau, sigma,
  t*, V, g, execute, the prior version and digest, the featurizer version and
  the features hash (``ControlDecision.detail``).
* Accounting (H.6): an A4 forecast is one LLM call, returned in
  ``ControlDecision.llm_calls`` and charged to the campaign's LLM-call cap; when
  the cap is exhausted no call is made and the fallback (A1) prior answers.
  Sidecar forecasts (A5/A6) cost compute only; latency is descriptive.  A
  sidecar failure answers with the fallback prior and is logged as a
  ``prior_unavailable`` event.

Units: sigma (the comparison noise of the edit's kind, ``sigma_cmp``) and g
are in metric units; g defaults to ``G_PRIMARY`` (0.1) x sigma_node, the
declared run price (PLAN §10, g (22 Oct)).

Direct-action arms through the same ``decide()`` (H.7): ``AWRDirectController``
(the existing ``r1.baselines.policies.AWRMLP`` acting on E1 continue/skip from
the same features) and ``r1.llm_control.LLMSelfController`` (unchanged).  The
hybrid is ``RuleController(..., hybrid_revise=True, revision_budget=n)``:
**proposal, not an adopted definition** — the prior decides whether (execute
vs not, and the keep threshold); when the rule would skip and ``revise`` is
feasible in the mask and within the revision budget, the controller requests
``revise`` instead of ``skip``; otherwise it skips.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Any, Mapping

import numpy as np

from r1.c3 import rules
from r1.c3.arms import TAU_FLOOR_Z
from r1.c3.features import FEATURES, FEATURIZER_VERSION, NodeContext, featurize_view, features_hash
from r1.c3.labels import INERT, MIDPOINTS
from r1.c3.offline_eval import G_PRIMARY
from r1.c3.prior_model import Forecast, proposal_row
from r1.harness import import_harness

import_harness()

from autoresearch.control_plane.action_versions import KEEP_RULE_BAYES, ActionVersions, KeepPrior  # noqa: E402
from autoresearch.control_plane.controller import ControlDecision  # noqa: E402
from autoresearch.memory.summarizer import SKIP_DISPLAY_ONE_LINE  # noqa: E402

RULE_CONTROLLER_VERSION = "rule_controller/v1"
# R1-SKIP-DISPLAY (PLAN §10, decided 25 Oct 2026): every campaign under a C3 controller shows a
# control-plane skip as one line without a metric, and its manifest records the display version.
SKIP_DISPLAY = SKIP_DISPLAY_ONE_LINE
HYBRID_VERSION = "rule_controller_hybrid/v1"
AWR_DIRECT_VERSION = "awr_direct/v1"


def edit_kind(edit: Mapping | None) -> str:
    """``structural`` for model_type edits, else ``local`` (``dataset.row_of``)."""
    return "structural" if (edit or {}).get("symbol") == "model_type" else "local"


def _proposal_key(proposal: Any) -> str:
    extra = (proposal.get("extra") if isinstance(proposal, dict) else getattr(proposal, "extra", None)) or {}
    summary = proposal.get("proposal_summary") if isinstance(proposal, dict) else getattr(proposal, "proposal_summary", "")
    return hashlib.sha256(json.dumps({"edit": extra.get("structured_edit"), "summary": summary},
                                     sort_keys=True, default=str).encode()).hexdigest()


def _llm_calls_left(view: Any) -> int | None:
    left = (getattr(view, "budget", None) or {}).get("llm_calls_remaining")
    return None if left is None else int(left)


def _f(x) -> float | None:
    x = float(x)
    return x if math.isfinite(x) else None


@dataclass
class _Plan:
    key: str
    features_hash: str | None
    kind: str
    forecast: Forecast | None
    pi: float | None = None
    mu: float | None = None
    tau: float | None = None
    sigma: float | None = None


class RuleController:
    """The C3 rule controller (see the module docstring).  ``prior`` is any ``PriorModel``."""

    deterministic = True

    def __init__(self, prior, node_ctx: NodeContext, *, sigma_node: float | None = None, tau_node: float | None = None,
                 g: float | None = None, sigma_cmp: Mapping[str, float] | None = None, fallback=None,
                 rule_layer: bool | None = None, greedy_bin: bool = False, hybrid_revise: bool = False,
                 revision_budget: int | None = None) -> None:
        self.prior, self.ctx = prior, node_ctx
        self.sigma_node = float(node_ctx.sigma_node if sigma_node is None else sigma_node)
        if not math.isclose(self.sigma_node, node_ctx.sigma_node):
            raise ValueError("sigma_node must equal node_ctx.sigma_node (the featurizer standardises with it)")
        self.g = float(G_PRIMARY * self.sigma_node if g is None else g)
        self.sigma_cmp = {"local": self.sigma_node, "structural": self.sigma_node, **dict(sigma_cmp or {})}
        self.fallback = fallback
        self.rule_layer = bool(getattr(prior, "rule_layer", True) if rule_layer is None else rule_layer)
        self.greedy_bin, self.tau_node = bool(greedy_bin), tau_node
        if self.greedy_bin and not (tau_node and tau_node > 0):
            raise ValueError("greedy_bin (A6 deployment: mu = sigma mid(b), tau = tau_node) needs tau_node > 0")
        if hybrid_revise and (revision_budget is None or revision_budget < 0):
            raise ValueError("the hybrid needs an explicit revision_budget >= 0")
        self.hybrid_revise, self.revision_budget = bool(hybrid_revise), revision_budget
        self.revisions_requested = 0
        base = HYBRID_VERSION if self.hybrid_revise else RULE_CONTROLLER_VERSION
        self.version = f"{base}[{prior.version}]"
        self._plans: dict[int, _Plan] = {}
        self._pending: dict[str, Any] = {"events": [], "llm_calls": 0, "detail": {}}
        self.log: list[dict] = []

    # ---- campaign wiring -------------------------------------------------
    def campaign_kwargs(self, **versions: str) -> dict:
        """``run_real_campaign`` kwargs: this controller, keep rule ``bayes_threshold/v1``, the keep prior,
        and the decided skip display ``one_line/v1`` (R1-SKIP-DISPLAY)."""
        return {"controller": self, "keep_prior": self.keep_prior, "skip_display": SKIP_DISPLAY,
                "action_versions": ActionVersions.new_campaign(keep_rule=KEEP_RULE_BAYES, **versions)}

    # ---- forecasting -----------------------------------------------------
    def _forecast(self, row: dict, view: Any) -> Forecast:
        need = int(getattr(self.prior, "llm_calls_per_forecast", 0))
        left = _llm_calls_left(view)
        if need and left is not None and left < need:
            if self.fallback is None:
                raise RuntimeError("LLM-call cap exhausted and no fallback prior")
            fb = self.fallback.forecast(row)
            return Forecast(probs=fb.probs, version=self.prior.version, digest=self.prior.digest,
                            latency_s=fb.latency_s, llm_calls=0, fallback="llm_cap_exhausted",
                            info={"fallback_version": fb.version, "fallback_digest": fb.digest})
        return self.prior.forecast(row)

    def _moments(self, f: Forecast, sigma: float) -> tuple[float, float, float]:
        if self.greedy_bin:  # A6 deployment (C3_DESIGN §5): the mode bin's midpoint, tau from dev
            b = int(np.argmax(f.probs))
            pi = 1.0 if b == INERT else 0.0
            mu = 0.0 if b == INERT else float(MIDPOINTS[b - 1]) * self.sigma_node
            return pi, mu, float(self.tau_node)
        return f.moments(self.sigma_node, TAU_FLOOR_Z)

    def _plan(self, view: Any) -> tuple[_Plan | None, Any, dict]:
        """Features and (lazily) the forecast of the view's proposal."""
        key = _proposal_key(view.proposal)
        try:
            res = featurize_view(view, self.ctx)
        except Exception as exc:  # noqa: BLE001 - a proposal we cannot featurise runs under the default
            return None, None, {"reason": f"featurize_failed: {exc!r}"[:300]}
        if res is None:
            return _Plan(key=key, features_hash=None, kind=edit_kind(_edit_of(view.proposal)), forecast=None), None, \
                {"reason": "no_features"}
        return _Plan(key=key, features_hash=features_hash(res.features), kind=edit_kind(res.edit), forecast=None), res, {}

    def _fill(self, plan: _Plan, res, view: Any) -> dict:
        row = proposal_row(self.ctx.node, res.features, res.edit)
        f = self._forecast(row, view)
        sigma = float(self.sigma_cmp[plan.kind])
        pi, mu, tau = self._moments(f, sigma)
        plan.forecast, plan.pi, plan.mu, plan.tau, plan.sigma = f, pi, mu, tau, sigma
        t_star = float(rules.bayes_threshold(mu, tau, sigma))
        v_star = float(rules.proposal_value(pi, mu, tau, sigma))
        execute = bool(rules.execute(pi, mu, tau, sigma, self.g))
        return {"prior_version": f.version, "prior_digest": f.digest, "probs": list(f.probs),
                "pi": pi, "mu": mu, "tau": tau, "sigma": sigma, "sigma_node": self.sigma_node,
                "t_star": _f(t_star), "V": _f(v_star), "g": self.g, "execute": execute,
                "latency_s": f.latency_s, "llm_calls": int(f.llm_calls), "fallback": f.fallback,
                **({"sidecar_compute_s": f.info["sidecar_compute_s"]} if "sidecar_compute_s" in f.info else {}),
                **({"fallback_version": f.info["fallback_version"]} if "fallback_version" in f.info else {})}

    @staticmethod
    def _events(f: Forecast | None, budget_index: int) -> tuple:
        if f is not None and f.fallback and f.fallback.startswith("prior_unavailable"):
            return (("prior_unavailable", {"budget_index": budget_index, "reason": f.fallback,
                                           "prior_version": f.version, "fallback_version": f.info.get("fallback_version"),
                                           "error": f.info.get("error")}),)
        return ()

    # ---- the harness Controller interface --------------------------------
    def decide(self, view: Any, mask: dict[str, bool]) -> ControlDecision:
        if view.epoch == "E1" and view.proposal is not None:
            return self._decide_e1(view, mask)
        if view.epoch == "E2":
            pending, self._pending = self._pending, {"events": [], "llm_calls": 0, "detail": {}}
            return ControlDecision("continue", {}, self.version, view.input_hash(), int(pending["llm_calls"]),
                                   detail=dict(pending["detail"]), events=tuple(pending["events"]))
        return ControlDecision("continue", {}, self.version, view.input_hash())

    def _skip_or(self, mask: dict[str, bool], reason: str) -> tuple[str, dict]:
        """The action for a proposal the rules would not execute."""
        if (self.hybrid_revise and mask.get("revise", False)
                and self.revisions_requested < int(self.revision_budget or 0)):
            self.revisions_requested += 1
            return "revise", {"rule_decision": reason, "hybrid": "revise_instead_of_skip"}
        if mask.get("skip", False):
            return "skip", {"skip_reason": reason}
        return "continue", {"rule_decision": reason, "skip_infeasible": True}

    def _decide_e1(self, view: Any, mask: dict[str, bool]) -> ControlDecision:
        b = int(view.budget_index)
        plan, res, note = self._plan(view)
        base = {"controller": self.version, "featurizer": FEATURIZER_VERSION}
        if plan is None or res is None:
            if plan is not None:
                self._plans[b] = plan
            detail = {**base, **note}
            self.log.append({"budget_index": b, **detail})
            return ControlDecision("continue", {}, self.version, view.input_hash(), detail=detail)
        self._plans[b] = plan
        base["features_hash"] = plan.features_hash
        if self.rule_layer and (res.noop or res.duplicate):
            reason = "rule_noop" if res.noop else "rule_duplicate"
            action, extra = self._skip_or(mask, reason)
            detail = {**base, "rule": {"noop": res.noop, "duplicate": res.duplicate}, **extra}
            self.log.append({"budget_index": b, "action": action, **detail})
            return ControlDecision(action, {}, self.version, view.input_hash(), detail=detail)
        numbers = self._fill(plan, res, view)
        detail = {**base, "rule": {"noop": res.noop, "duplicate": res.duplicate}, **numbers}
        if numbers["execute"]:
            action = "continue"
        else:
            action, extra = self._skip_or(mask, "prior_no_gain")
            detail.update(extra)
        scores = {"V": numbers["V"] if numbers["V"] is not None else 0.0, "g": self.g}
        self.log.append({"budget_index": b, "action": action, **detail})
        return ControlDecision(action, scores, self.version, view.input_hash(), int(plan.forecast.llm_calls),
                               detail=detail, events=self._events(plan.forecast, b))

    # ---- E2: the keep prior (KeepPriorProvider) ----------------------------
    def keep_prior(self, view: Any) -> KeepPrior:
        b = int(view.budget_index)
        plan = self._plans.get(b)
        key = _proposal_key(view.proposal)
        origin = "e1_forecast"
        if plan is None or plan.key != key or (plan.forecast is None and plan.features_hash is not None):
            origin = "e2_forecast" if plan is None or plan.key != key else "e2_forecast_after_rule_decision"
            plan, res, note = self._plan(view)
            if plan is not None and res is not None:
                numbers = self._fill(plan, res, view)
                self._pending["llm_calls"] += int(plan.forecast.llm_calls)
                self._pending["events"].extend(self._events(plan.forecast, b))
                self._pending["detail"] = {"keep_prior_origin": origin, "features_hash": plan.features_hash,
                                           **numbers}
                self._plans[b] = plan
            else:
                self._pending["detail"] = {"keep_prior_origin": origin, **note}
        if plan is None or plan.forecast is None:
            # No features (first trial or no incumbent metric): the rule keeps the first valid metric
            # without using the prior (decide_trial_bayes_threshold), so any valid prior serves.
            sigma = float(self.sigma_cmp[plan.kind if plan else "local"])
            return KeepPrior(mu=0.0, tau=self.sigma_node, sigma=sigma, source=f"c3:{self.version}:no_features")
        return KeepPrior(mu=plan.mu, tau=plan.tau, sigma=plan.sigma,
                         source=f"c3:{plan.forecast.version}:{plan.forecast.digest[:16]}:{origin}")


def _edit_of(proposal: Any):
    extra = (proposal.get("extra") if isinstance(proposal, dict) else getattr(proposal, "extra", None)) or {}
    return extra.get("structured_edit")


# ---------------------------------------------------------------------------
# H.7: a direct-action arm (AWR-MLP) through the same decide()
# ---------------------------------------------------------------------------

def feature_vector(features: Mapping[str, Any]) -> np.ndarray:
    """FEATURES as floats, NaN -> 0 (the AWR-MLP input)."""
    x = np.array([float(features[c]) for c in FEATURES], float)
    return np.nan_to_num(x, nan=0.0)


def fit_awr_direct(rows, g_units: float = G_PRIMARY, **awr_kwargs):
    """Fit ``AWRMLP`` on labelled table rows: action 0 = execute (rho keep), action 1 = skip.

    Value of execute = Delta_true * 1{Delta_hat > 0} - g (the default keep rule
    rho; a direct-action arm has no prior), value of skip = 0.  ``rows`` are
    assembled rows (``offline_eval.assemble``) with ``delta_true``; train them
    on label-seed values only (``env.OfflineBanditEnv`` convention).
    """
    from r1.baselines.policies import AWRMLP
    X = np.array([feature_vector(r["features"]) for r in rows])
    g = g_units * np.array([r["sigma_node"] for r in rows])
    ex = np.array([r["delta_true"] * (r["delta_hat"] > 0) for r in rows]) - g
    values = np.c_[ex, np.zeros(len(rows))]
    return AWRMLP(**awr_kwargs).fit(X, values)


@dataclass
class AWRDirectController:
    """E1 continue/skip chosen directly by an AWR-MLP on the shared features (no prior, keep rule rho)."""

    model: Any
    node_ctx: NodeContext
    version: str = AWR_DIRECT_VERSION
    deterministic: bool = True
    log: list = field(default_factory=list)

    def decide(self, view: Any, mask: dict[str, bool]) -> ControlDecision:
        if view.epoch != "E1" or view.proposal is None:
            return ControlDecision("continue", {}, self.version, view.input_hash())
        try:
            res = featurize_view(view, self.node_ctx)
        except Exception as exc:  # noqa: BLE001
            return ControlDecision("continue", {}, self.version, view.input_hash(),
                                   detail={"reason": f"featurize_failed: {exc!r}"[:300]})
        if res is None:
            return ControlDecision("continue", {}, self.version, view.input_hash(), detail={"reason": "no_features"})
        p = self.model.proba(feature_vector(res.features)[None, :])[0]
        action = "skip" if p[1] > p[0] and mask.get("skip", False) else "continue"
        detail = {"featurizer": FEATURIZER_VERSION, "features_hash": features_hash(res.features),
                  "p_execute": float(p[0]), "p_skip": float(p[1]),
                  **({"skip_reason": "awr_direct"} if action == "skip" else {})}
        self.log.append({"budget_index": int(view.budget_index), "action": action, **detail})
        return ControlDecision(action, {"execute": float(p[0]), "skip": float(p[1])}, self.version,
                               view.input_hash(), detail=detail)


def declare_skip_display(manifest: dict, display: str = SKIP_DISPLAY) -> str:
    """Record the skip display in a campaign manifest (H.4); refuses to overwrite a different value.

    A manifest without the field means the historical display; such campaigns
    had no control-plane skips (PLAN §10, R1-SKIP-DISPLAY).
    """
    from autoresearch.memory.summarizer import check_skip_display
    check_skip_display(display)
    if "skip_display" in manifest and manifest["skip_display"] != display:
        raise ValueError(f"manifest already declares skip_display={manifest['skip_display']!r}")
    manifest["skip_display"] = display
    return display
