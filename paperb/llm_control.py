"""L12: the LLM self-control arm, a side query on a forked context (BUILD_RUNBOOK L12, PLAN §5 arm 1).

At each decision epoch the controller asks the manager model, in a separate
call, which control action to take. The query contains:
- the manager-visible information (node, metric and direction, current best,
  the proposal summary and rationale, the provisional result at E2, a short
  ledger narrative), all rebuilt from the harness ``ControlView``;
- the masked action menu;
- the remaining budget.

The model must answer with JSON ``{"action": ..., "scores": {action: score}}``.

Guarantees:
- **Forked context.** The query is built from a copy of the view. Nothing is
  written to the manager, its prompt or the ledger, and the manager object is
  never touched.
- **Charged.** Every call is reported as ``ControlDecision.llm_calls = 1``, and
  the harness charges it to the LLM-call cap (harness L12 change). When the cap
  is exhausted the controller makes no call and continues.
- **Fail-safe.** A malformed reply, an unknown action or an action the mask
  rules out becomes ``continue``. The reason is kept in ``self.log``.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable

from r1.harness import import_harness

import_harness()

from autoresearch.control_plane.controller import ControlDecision  # noqa: E402

ACTION_HELP = {
    "continue": "do nothing; the default rule applies",
    "skip": "do not run this proposal (saves one worker run)",
    "revise": "ask the manager to revise the proposal once (costs one LLM call)",
    "verify": "re-run candidate and incumbent at fresh seeds before deciding (costs 2r worker runs)",
    "demote": "revert the last unverified keep",
    "stop": "end the campaign now and return the unspent budget",
}


def _call(llm: Any, prompt: str) -> str:
    if callable(llm) and not hasattr(llm, "invoke"):
        return str(llm(prompt))
    reply = llm.invoke(prompt)
    return str(getattr(reply, "content", reply))


def build_side_prompt(view: Any, mask: dict[str, bool], *, max_ledger: int = 8) -> str:
    payload = view.canonical_payload()  # a fresh dict: the view itself is never modified
    node = payload["node"]
    lines = [
        "You are advising the control plane of an automated ML experiment campaign.",
        "You do NOT propose edits. You choose one control action for the current decision point.",
        "",
        f"Node: {node['name']}; metric {node['metric_name']} ({node['metric_direction']}).",
        f"Decision epoch: {payload['epoch']} (E0 = before a proposal, E1 = after a proposal, before running it, "
        f"E2 = after the metric, before the keep/discard decision).",
        f"Trial index: {payload['budget_index']}. Current best: {payload['current_best']}.",
        f"Budget: {json.dumps(payload['budget'], sort_keys=True, default=str)}",
    ]
    if payload.get("proposal"):
        lines.append(f"Proposal: {json.dumps(payload['proposal'], sort_keys=True, default=str)}")
    if payload.get("provisional"):
        lines.append(f"Provisional result: {json.dumps(payload['provisional'], sort_keys=True, default=str)}")
    ledger = payload.get("ledger_prefix") or []
    if ledger:
        lines.append(f"Last {min(len(ledger), max_ledger)} trials (oldest first):")
        for rec in ledger[-max_ledger:]:
            lines.append("  " + json.dumps(rec, sort_keys=True, default=str))
    allowed = [a for a, ok in mask.items() if ok]
    lines += ["", "Allowed actions:"]
    lines += [f"  {a}: {ACTION_HELP.get(a, '')}" for a in allowed]
    lines += ["", 'Reply with JSON only: {"action": "<one allowed action>", "scores": {"<action>": <expected gain>}}']
    return "\n".join(lines)


@dataclass
class LLMSelfController:
    llm: Any
    version: str = "llm_self/v1"
    log: list[dict] = field(default_factory=list)
    prompt_builder: Callable[[Any, dict[str, bool]], str] = build_side_prompt
    # Track H review F5 (26 Oct): epochs the controller acts at.  ``None`` (default) is the
    # historical L12 behaviour (every epoch); the C3 comparison uses ("E1", "E2"), the epochs of
    # ``r1.c3.control.RuleController``.  At any other epoch it continues without a call.
    epochs: tuple[str, ...] | None = None

    def _llm_calls_left(self, view: Any) -> int | None:
        budget = getattr(view, "budget", {}) or {}
        left = budget.get("llm_calls_remaining")  # the harness budget view (ComputeBudget.remaining())
        return None if left is None else int(left)

    def decide(self, view: Any, mask: dict[str, bool]) -> ControlDecision:
        if self.epochs is not None and view.epoch not in self.epochs:
            self.log.append({"epoch": view.epoch, "reason": "epoch_not_controlled", "llm_calls": 0})
            return ControlDecision("continue", {}, self.version, view.input_hash(), 0)
        allowed = [a for a, ok in mask.items() if ok]
        if allowed == ["continue"] or not allowed:
            self.log.append({"epoch": view.epoch, "reason": "only_continue_feasible", "llm_calls": 0})
            return ControlDecision("continue", {}, self.version, view.input_hash(), 0)
        left = self._llm_calls_left(view)
        if left is not None and left <= 0:
            self.log.append({"epoch": view.epoch, "reason": "llm_cap_exhausted", "llm_calls": 0})
            return ControlDecision("continue", {}, self.version, view.input_hash(), 0)
        prompt = self.prompt_builder(view, mask)
        try:
            raw = _call(self.llm, prompt)
        except Exception as exc:  # noqa: BLE001 - a failed call is charged and falls back
            self.log.append({"epoch": view.epoch, "reason": f"llm_error: {exc!r}", "llm_calls": 1})
            return ControlDecision("continue", {}, self.version, view.input_hash(), 1)
        action, scores, reason = "continue", {}, "ok"
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        try:
            data = json.loads(match.group(0)) if match else None
            if not isinstance(data, dict):
                raise ValueError("no JSON object")
            proposed = str(data.get("action", "")).strip().lower()
            raw_scores = data.get("scores") or {}
            if not isinstance(raw_scores, dict):
                raise ValueError("scores is not an object")
            scores = {str(k): float(v) for k, v in raw_scores.items()
                      if str(k) in mask and isinstance(v, (int, float)) and not isinstance(v, bool)}
            if proposed in allowed:
                action = proposed
            else:
                reason = f"action_not_allowed:{proposed}"
        except Exception as exc:  # noqa: BLE001 - any malformed reply falls back to continue (L14 finding 1)
            reason = f"parse_failure: {exc}"
            scores = {}
        self.log.append({"epoch": view.epoch, "reason": reason, "llm_calls": 1, "action": action,
                         "prompt_chars": len(prompt), "reply_chars": len(raw)})
        return ControlDecision(action, scores, self.version, view.input_hash(), 1)
