"""D.3 controllers that ``RuleController`` does not cover (pre-declaration revision 4, §5, §12). AI-assisted (Claude).

ENGINEERING_ONLY until a signed D.3 note cites the reviewed unit.  Nothing here reads a label, an evaluation value
or a test partition; a controller sees only the harness ``ControlView`` of its own campaign.

Source of every arm definition: ``docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md`` revision 4 (branch
``mac-d3-predecl-r4-20261127``), §5 and its table "The rule layer per arm".  The arm list, W, the LLM-call cap and the
rule-layer arms are read from the pinned analysis script ``r1/c3/d3_analysis.py`` so that controller and analysis can
never disagree (one source of truth; nothing here changes that script).

**The rule-layer switch (§5; §13 item 21, an open author item).**  ``D3_RULE_LAYER`` maps every D.3 arm to whether its
rule layer is on.  It is derived from ``d3_analysis.RULE_LAYER_ARMS``: on for A0R, A2 and the D.3b arms, **off** for
A0, A1, FIXR3, EGATE and LADDER (revision 4's built and recommended option).  If the author chooses another option,
``RULE_LAYER_ARMS`` in the pinned script changes (a [sha] item) and this table follows it without a code change here;
the controllers below take ``rule_layer`` explicitly and refuse a value that differs from the table
(``check_rule_layer``), so no campaign can run a rule layer the analysis would refuse (``rule_skips`` > 0).

Units in this module (each its own reviewed tier-E unit):

* **A0R** (§5.1b, R1-D3-DECOMP; gap G11): ``RuleLayerController`` with ``rule_layer=True`` — at E1 a proposal the
  rule layer marks as a detectable no-op or a duplicate is skipped and charged no run (``skip_reason``
  ``rule_noop`` / ``rule_duplicate``, one line in memory, R1-SKIP-DISPLAY); every other proposal is executed once and
  kept iff Delta_hat > 0 (harness keep rule ``default/v1``); no screen, no forecast, no verify.  The rule layer is the
  same test as A2's: ``r1.c3.features.featurize_view`` on the harness ``ControlView`` and its ``noop`` / ``duplicate``
  flags, checked in the order ``RuleController`` checks them (no-op first).
"""
from __future__ import annotations

from typing import Any

from r1.c3 import d3_analysis as D3
from r1.c3.control import SKIP_DISPLAY, c3_budgets
from r1.c3.features import FEATURIZER_VERSION, NodeContext, featurize_view, features_hash
from r1.harness import import_harness

import_harness()

from autoresearch.control_plane.action_versions import (  # noqa: E402
    KEEP_RULE_DEFAULT, NEW_CAMPAIGN_VERIFY_SPLIT_POLICY, VERIFY_RESPONSE_MEAN, ActionVersions)
from autoresearch.control_plane.controller import ControlDecision  # noqa: E402

D3_ARMS = D3.ARMS_D3A + D3.ARMS_D3B_WITH_A6
# §5 "The rule layer per arm"; §13 item 21 (open): from the pinned script, never typed twice.
D3_RULE_LAYER = {arm: arm in D3.RULE_LAYER_ARMS for arm in D3_ARMS}
D3_W = D3.W                       # 20 worker runs per campaign, every arm (§2)
D3_LLM_CALL_CAP = D3.LLM_CALL_CAP  # 80 per campaign, every arm (§3); trial budget = the cap (c3_budgets)

RULE_LAYER_CONTROLLER_VERSION = "d3_rule_layer/v1"


def check_rule_layer(arm: str, rule_layer: bool) -> bool:
    """Refuse a rule-layer setting that differs from the declared one for ``arm`` (§5; §13 item 21)."""
    if arm not in D3_RULE_LAYER:
        raise ValueError(f"not a D.3 arm: {arm!r}")
    if bool(rule_layer) is not D3_RULE_LAYER[arm]:
        raise ValueError(f"arm {arm}: rule_layer={bool(rule_layer)} differs from the declared "
                         f"{D3_RULE_LAYER[arm]} (d3_analysis.RULE_LAYER_ARMS; pre-declaration §5, §13 item 21)")
    return bool(rule_layer)


class RuleLayerController:
    """E1: the rule layer only (if on); E2: always continue.  Keep rule ``default/v1``; no prior, no verify.

    With ``rule_layer=True`` and ``arm="A0R"`` this is arm A0R.  With ``rule_layer=False`` every decision is
    ``continue``, which reproduces the ``ContinueController`` campaign (arm A0's decisions) while still logging the
    rule-layer flags it would have used, so the mechanism counts (``duplicates_proposed``) can be read from the
    events of every arm.
    """

    deterministic = True

    def __init__(self, node_ctx: NodeContext, *, arm: str, rule_layer: bool) -> None:
        self.ctx, self.arm = node_ctx, arm
        self.rule_layer = check_rule_layer(arm, rule_layer)
        self.version = f"{RULE_LAYER_CONTROLLER_VERSION}[{arm}]"
        self.log: list[dict] = []

    # ---- campaign wiring -------------------------------------------------
    def campaign_kwargs(self, *, W: int = D3_W, llm_cap: int = D3_LLM_CALL_CAP, trials: int | None = None,
                        **versions: str) -> dict:
        """``run_real_campaign`` kwargs: this controller, keep rule ``default/v1`` (Delta_hat > 0) without a keep
        prior, the skip display ``one_line/v1`` (R1-SKIP-DISPLAY), split policy ``vary``, and ``c3_budgets(W, cap)``
        (W worker runs and the LLM-call cap bind, the trial budget does not; D.3 §2 uses W = 20, cap = 80)."""
        for key in ("keep_rule", "verify_response"):
            if key in versions:
                raise ValueError(f"{self.arm}: {key} is fixed by the arm definition (§5)")
        return {"controller": self, "skip_display": SKIP_DISPLAY,
                "action_versions": ActionVersions.new_campaign(**{
                    "keep_rule": KEEP_RULE_DEFAULT, "verify_response": VERIFY_RESPONSE_MEAN,
                    "verify_split_policy": NEW_CAMPAIGN_VERIFY_SPLIT_POLICY, **versions}),
                **c3_budgets(W, llm_cap, trials)}

    # ---- the harness Controller interface --------------------------------
    def decide(self, view: Any, mask: dict[str, bool]) -> ControlDecision:
        if view.epoch == "E1" and view.proposal is not None:
            return self._decide_e1(view, mask)
        return ControlDecision("continue", {}, self.version, view.input_hash())

    def _decide_e1(self, view: Any, mask: dict[str, bool]) -> ControlDecision:
        b = int(view.budget_index)
        base = {"controller": self.version, "featurizer": FEATURIZER_VERSION, "rule_layer": self.rule_layer}
        try:
            res = featurize_view(view, self.ctx)
        except Exception as exc:  # noqa: BLE001 - as RuleController: a proposal we cannot featurise runs
            res, base["reason"] = None, f"featurize_failed: {exc!r}"[:300]
        if res is None:
            base.setdefault("reason", "no_features")  # first trial or no incumbent metric: no rule applies
            self.log.append({"budget_index": b, "action": "continue", **base})
            return ControlDecision("continue", {}, self.version, view.input_hash(), detail=base)
        detail = {**base, "features_hash": features_hash(res.features),
                  "rule": {"noop": bool(res.noop), "duplicate": bool(res.duplicate)}}
        action = "continue"
        if self.rule_layer and (res.noop or res.duplicate):
            reason = "rule_noop" if res.noop else "rule_duplicate"
            if mask.get("skip", False):
                action, detail["skip_reason"] = "skip", reason
            else:  # as RuleController._skip_or without the hybrid: an infeasible skip runs the proposal
                detail.update({"rule_decision": reason, "skip_infeasible": True})
        self.log.append({"budget_index": b, "action": action, **detail})
        return ControlDecision(action, {}, self.version, view.input_hash(), detail=detail)



def a0r_controller(node_ctx: NodeContext) -> RuleLayerController:
    """Arm A0R (§5.1b): the rule layer with the default keep rule; no screen, no verify."""
    return RuleLayerController(node_ctx, arm="A0R", rule_layer=D3_RULE_LAYER["A0R"])
