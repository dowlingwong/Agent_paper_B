"""Track P losses (spec §6.1, §6.3; RUNBOOK Track P 1.3). ENGINEERING_ONLY; AI-assisted (Claude).

All belief losses take bin *probabilities* p [N, 12] (bin 0 = inert/no-op, bins 1..11 ordered in z), so they serve
both head forms (softmax-12 and cumulative-11, spec §2.3) — the wrapper turns its logits into p.

RPS (the bounded proper score of spec §0.2 / §6.1), one definition shared with ``metrics.rps``:

    RPS(p, y) = 1/2 * [ (p_0 - y_0)^2  +  (1 - y_0) * 1/10 * sum_{k=1}^{10} (Q_k - R_k)^2 ]

with Q, R the cumulative distributions of the non-inert parts renormalised, q = p[1:]/(1 - p_0), r = y[1:]/(1 - y_0)
(R_11 = Q_11 = 1, so the sum stops at 10). The first term is the bin-0 Brier score; the second the ranked probability
score of the ordered bins 1-11, weighted by the label's non-inert mass (it vanishes for an inert label, so mass placed
on early vs late bins is not penalised asymmetrically there). Each term is proper (the weight depends on the label
only), so the sum is proper; RPS is in [0, 1].
"""
from __future__ import annotations

import torch
import torch.nn.functional as F

N_BINS = 12
EPS = 1e-8


def softmax_probs(logits: torch.Tensor) -> torch.Tensor:
    """Softmax-12 head: probabilities from belief logits [N, 12]."""
    return torch.softmax(logits.float(), dim=-1)


def _conditional(p: torch.Tensor) -> torch.Tensor:
    rest = p[..., 1:]
    return rest / rest.sum(dim=-1, keepdim=True).clamp_min(EPS)


def rps(p: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    """Per-row RPS [N] (module docstring)."""
    p, y = p.float(), y.float()
    brier0 = (p[..., 0] - y[..., 0]) ** 2
    Q = torch.cumsum(_conditional(p), dim=-1)[..., :-1]
    R = torch.cumsum(_conditional(y), dim=-1)[..., :-1]
    ordinal = ((Q - R) ** 2).mean(dim=-1)
    return 0.5 * (brier0 + (1.0 - y[..., 0]) * ordinal)


def soft_ce(p: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
    """Per-row soft-label cross-entropy -sum_k y_k log p_k [N] (log score; Stage S only, never in an RL reward)."""
    return -(y.float() * torch.log(p.float().clamp_min(EPS))).sum(dim=-1)


def stage_s_loss(p: torch.Tensor, y: torch.Tensor, ce: bool = True) -> torch.Tensor:
    """L_S = mean RPS + mean CE (spec §6.1); ``ce=False`` gives RPS only."""
    loss = rps(p, y).mean()
    return loss + soft_ce(p, y).mean() if ce else loss


def action_loss(action_logit: torch.Tensor, u: torch.Tensor) -> torch.Tensor:
    """Cost-sensitive BCE for the action head (spec §6.3): target 1[u > 0], weight |u|; mean over rows.

    Its minimiser in pi = P(execute) maximises E[pi * u]. ``u`` in whatever unit the caller fixes for a run (metric
    units, or u / sigma_node to pool nodes); the unit is the caller's to record.
    """
    u = u.float()
    target = (u > 0).float()
    return (u.abs() * F.binary_cross_entropy_with_logits(action_logit.float(), target, reduction="none")).mean()


def rule_value(p: torch.Tensor, v: torch.Tensor) -> torch.Tensor:
    """Bin-level shortcut V(p) = sum_k p_k v_k (spec §3.5, R-A3 only); v [12] or [N, 12]."""
    return (p.float() * v.float()).sum(dim=-1)


def smoothed_rule_loss(p: torch.Tensor, y: torch.Tensor, u: torch.Tensor, v: torch.Tensor, g,
                       tau: float, lam: float) -> torch.Tensor:
    """R-A3 ablation (spec §6.3): mean[ RPS(p, y) - lam * a_tau(p) * u ], a_tau(p) = sigmoid((V(p) - g) / tau)."""
    a = torch.sigmoid((rule_value(p, v) - torch.as_tensor(g, dtype=torch.float32)) / tau)
    return (rps(p, y) - lam * a * u.float()).mean()
