"""Track P Stage R-A pieces missing before 14 Nov (spec TRACK_P_POST_TRAINING.md §6.3, §6.4). ENGINEERING_ONLY.

AI-assisted (Claude). No label table, audit or seed is read here.

* ``DetachedActionHead`` — R-A1 (§6.3 table): LayerNorm + Linear (hidden -> 1) on the **stop-gradient** hidden state
  (a LayerNorm before every new head, spec §2.2 and PLAN R1-HEADS-LN), so the action loss never reaches the belief, the
  adapters or the base (the Stage S belief stays frozen). It reads ``out["state"]`` of a wrapper called with
  ``return_state=True`` — the hidden state at the **belief** read-out position — and is trained with ``losses.action_loss``
  (``ra1_loss``). R-A2 (shared) is the wrappers' existing action head, whose loss updates the shared LoRA.
* ``stop_rule`` — the rollback rule for R-A2, R-A3 and R-B (§6.4 "Stop rule"): roll back to the best checkpoint if
  val all-bins ECE rises > 0.02 above Stage S; val RPS worsens by > 1 s.e. while val decision utility has not improved;
  val width ratio < 0.8; or mean predictive entropy falls > 20 % below Stage S within 100 steps. The caller supplies
  the validation metrics (``metrics.ece_all_bins``, ``metrics.width_ratio``, …) and restores the checkpoint.
"""
from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn

from r1.c3.train.losses import action_loss

ECE_RISE = 0.02
WIDTH_RATIO_MIN = 0.8
ENTROPY_DROP = 0.20
ENTROPY_WINDOW_STEPS = 100


class DetachedActionHead(nn.Module):
    """R-A1: LayerNorm(hidden) -> Linear(hidden -> 1) on ``state.detach()``."""

    def __init__(self, hidden: int):
        super().__init__()
        self.norm = nn.LayerNorm(hidden)
        self.linear = nn.Linear(hidden, 1)

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        return self.linear(self.norm(state.detach().float()))[:, 0]


def ra1_loss(head: DetachedActionHead, out: dict, u: torch.Tensor) -> torch.Tensor:
    """Cost-sensitive BCE of the detached head on a wrapper output computed with ``return_state=True``."""
    if out.get("state") is None:
        raise ValueError("R-A1 needs the wrapper's hidden state: call forward(..., return_state=True)")
    return action_loss(head(out["state"]), u)


@dataclass(frozen=True)
class ValMetrics:
    ece_all_bins: float
    rps: float
    rps_se: float
    utility: float
    width_ratio: float
    entropy: float


def stop_rule(stage_s: ValMetrics, current: ValMetrics, *, steps_since_stage_s: int) -> dict:
    """§6.4 rollback rule; ``stage_s`` is the Stage S checkpoint's validation row (its ``rps_se`` is the 1 s.e.)."""
    reasons = []
    if current.ece_all_bins > stage_s.ece_all_bins + ECE_RISE:
        reasons.append("val all-bins ECE rose > 0.02 above Stage S")
    if current.rps > stage_s.rps + stage_s.rps_se and not current.utility > stage_s.utility:
        reasons.append("val RPS worse by > 1 s.e. while val decision utility has not improved")
    if current.width_ratio < WIDTH_RATIO_MIN:
        reasons.append("val width ratio below 0.8")
    if steps_since_stage_s <= ENTROPY_WINDOW_STEPS and current.entropy < (1 - ENTROPY_DROP) * stage_s.entropy:
        reasons.append("mean predictive entropy > 20 % below Stage S within 100 steps")
    return {"rollback": bool(reasons), "reasons": reasons}
