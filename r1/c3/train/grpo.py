"""Track P Stage R-B: GRPO pieces (spec TRACK_P_POST_TRAINING.md §6.4, PLAN R1-RB-GRPO). ENGINEERING_ONLY; AI-assisted.

Implemented exactly as §6.4 fixes them (28 Oct, R1-RB-GRPO):

* **group** of G completions per context (G = 8; 16 if memory allows);
* **reward** r = -RPS(p, y_train) + lambda_a * 1[action = exec] * clip(u, -u_max, u_max) - 0.5 * 1[format violation]
  (``rb_reward``). RPS is the bounded proper score of ``losses.rps``; the reward never contains a log score (§0.2).
  ``u_max`` is the 99th percentile of |u| on the training rows (``u_max_from_train``; the spec says "the 99th
  percentile on train"; |u| is the reading used here, so the clip is symmetric as written);
* **advantage (primary)**: leave-one-out, no std normalisation, A_i = r_i - (1/(G-1)) sum_{j != i} r_j
  (``loo_advantages``); **sensitivity**: (r_i - mean_G r) / std_G r with the population std, and A = 0 for a group
  whose rewards are all equal (``std_advantages``). One sequence-level advantage per completion, applied to every
  sampled token of that completion, **no per-length normalisation**;
* **update**: PPO-style clipped surrogate per sampled token, rho = pi_theta / pi_old, eps = 0.2,
  L = -E[min(rho A, clip(rho, 1 - eps, 1 + eps) A)], summed over a completion's sampled tokens and averaged over
  completions (no per-length normalisation); 2 update epochs per sampled batch, pi_old refreshed after each batch
  (``ppo_update``);
* **KL**: beta * KL(pi_theta || pi_ref) with the k3 estimator per sampled token,
  k3 = exp(log pi_ref - log pi_theta) - (log pi_ref - log pi_theta) - 1, aggregated like the surrogate;
  beta in {0, 0.02};
* **monitors** (every step): share of zero-advantage groups, share of clipped tokens, mean per-token KL to pi_ref.

The GRPO estimator check of §6.3 (on R-A1, Bernoulli execute, G = 8, 256 prompts, 64 resamples, cosine >= 0.95
against the exact gradient of L_action) is ``estimator_check``.

The numpy functions carry the arithmetic and need no torch; the torch functions (``clipped_surrogate``, ``k3_kl``,
``grpo_loss``, ``ppo_update``) are the training path and import torch lazily.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import numpy as np

GROUP_SIZE = 8
CLIP_EPS = 0.2
UPDATE_EPOCHS = 2
BETAS = (0.0, 0.02)
FORMAT_PENALTY = 0.5
ANALYSIS_MAX_TOKENS = 256
LORA_RANK = 16
LR_RANGE = (1e-6, 5e-6)
MAX_STEPS = 500


# ------------------------------------------------------------------ rewards and advantages (numpy)

def u_max_from_train(u_train) -> float:
    u = np.abs(np.asarray(u_train, dtype=float))
    if u.size == 0 or not np.all(np.isfinite(u)):
        raise ValueError("u_train must be a nonempty finite array")
    return float(np.percentile(u, 99))


def rb_reward(rps, executed, u, *, u_max: float, format_violation, lambda_a: float) -> np.ndarray:
    """r = -RPS + lambda_a * 1[exec] * clip(u, -u_max, u_max) - 0.5 * 1[format violation] (elementwise)."""
    rps = np.asarray(rps, dtype=float)
    if np.any((rps < 0) | (rps > 1)):
        raise ValueError("RPS must lie in [0, 1]")
    if not (u_max >= 0 and np.isfinite(u_max)):
        raise ValueError("u_max must be finite and nonnegative")
    ex = np.asarray(executed, dtype=bool).astype(float)
    fv = np.asarray(format_violation, dtype=bool).astype(float)
    uc = np.clip(np.asarray(u, dtype=float), -u_max, u_max)
    return -rps + lambda_a * ex * uc - FORMAT_PENALTY * fv


def _groups(r) -> np.ndarray:
    r = np.asarray(r, dtype=float)
    if r.ndim < 1 or r.shape[-1] < 2:
        raise ValueError("rewards must have a group axis of size >= 2 (last axis)")
    return r


def loo_advantages(r) -> np.ndarray:
    """Primary advantage: A_i = r_i - mean of the other G - 1 rewards in the group (last axis)."""
    r = _groups(r)
    g = r.shape[-1]
    return r - (r.sum(axis=-1, keepdims=True) - r) / (g - 1)


def std_advantages(r) -> np.ndarray:
    """Sensitivity: (r_i - mean_G r) / std_G r (population std); 0 for a group with all-equal rewards."""
    r = _groups(r)
    mean = r.mean(axis=-1, keepdims=True)
    std = r.std(axis=-1, keepdims=True)
    out = np.zeros_like(r)
    nz = np.broadcast_to(std > 0, r.shape)
    np.divide(r - mean, np.broadcast_to(std, r.shape), out=out, where=nz)
    return out


def zero_advantage_share(r) -> float:
    r = _groups(r).reshape(-1, np.asarray(r).shape[-1])
    return float(np.mean(np.all(r == r[:, :1], axis=1)))


def np_clipped_surrogate(logp_new, logp_old, adv, mask, eps: float = CLIP_EPS) -> tuple[float, float]:
    """Reference arithmetic: (loss, clipped-token share). Arrays [C, T]; adv [C]; mask [C, T] of 0/1."""
    logp_new, logp_old, mask = (np.asarray(x, dtype=float) for x in (logp_new, logp_old, mask))
    adv = np.asarray(adv, dtype=float)[:, None]
    rho = np.exp(logp_new - logp_old)
    unclipped, clipped = rho * adv, np.clip(rho, 1 - eps, 1 + eps) * adv
    per_token = -np.minimum(unclipped, clipped) * mask
    loss = per_token.sum(axis=1).mean()
    clip_share = float(((np.abs(rho - 1) > eps) * mask).sum() / max(mask.sum(), 1.0))
    return float(loss), clip_share


def np_k3(logp_new, logp_ref, mask) -> tuple[float, float]:
    """(aggregated k3 KL as in the surrogate, mean per-token k3)."""
    d = np.asarray(logp_ref, dtype=float) - np.asarray(logp_new, dtype=float)
    mask = np.asarray(mask, dtype=float)
    k3 = (np.exp(d) - d - 1.0) * mask
    return float(k3.sum(axis=1).mean()), float(k3.sum() / max(mask.sum(), 1.0))


# ------------------------------------------------------------------ the §6.3 estimator check (numpy)

def estimator_check(logits, u, *, group: int = GROUP_SIZE, resamples: int = 64, seed: int = 0,
                    advantage: str = "loo") -> dict[str, Any]:
    """GRPO estimator check on R-A1 (spec §6.3).

    pi = sigmoid(logit) per prompt; execute ~ Bernoulli(pi); reward r = u * execute; advantage per group. The GRPO
    loss gradient with respect to the logits is -(1/G) sum_i A_i (a_i - pi) (d log p(a)/d logit = a - pi), averaged
    over ``resamples`` independent group draws; the exact gradient of L_action = -pi u is -u pi (1 - pi).
    Returns the cosine between the two over the prompt vector (spec: >= 0.95 for 256 prompts, G = 8, 64 resamples).
    """
    z = np.asarray(logits, dtype=float)
    u = np.asarray(u, dtype=float)
    if z.shape != u.shape or z.ndim != 1:
        raise ValueError("logits and u must be 1-D arrays of the same length")
    rng = np.random.default_rng(seed)
    pi = 1.0 / (1.0 + np.exp(-z))
    exact = -u * pi * (1.0 - pi)
    adv_fn = loo_advantages if advantage == "loo" else std_advantages
    est = np.zeros_like(z)
    for _ in range(resamples):
        a = (rng.random((len(z), group)) < pi[:, None]).astype(float)
        adv = adv_fn(u[:, None] * a)
        est += -(adv * (a - pi[:, None])).mean(axis=1)
    est /= resamples
    cosine = float(est @ exact / (np.linalg.norm(est) * np.linalg.norm(exact)))
    return {"cosine": cosine, "passes": cosine >= 0.95, "prompts": len(z), "group": group,
            "resamples": resamples, "advantage": advantage}


# ------------------------------------------------------------------ torch training path

def clipped_surrogate(logp_new, logp_old, adv, mask, eps: float = CLIP_EPS):
    """Torch version of ``np_clipped_surrogate``: returns (loss tensor, clipped-token share float)."""
    import torch
    rho = torch.exp(logp_new - logp_old.detach())
    a = adv.detach()[:, None]
    per_token = -torch.minimum(rho * a, torch.clamp(rho, 1 - eps, 1 + eps) * a) * mask
    clip_share = float((((rho - 1).abs() > eps).float() * mask).sum() / mask.sum().clamp_min(1.0))
    return per_token.sum(dim=1).mean(), clip_share


def k3_kl(logp_new, logp_ref, mask):
    """Torch k3 KL to the reference policy: (aggregated tensor, mean per-token float)."""
    import torch
    d = logp_ref.detach() - logp_new
    k3 = (torch.exp(d) - d - 1.0) * mask
    return k3.sum(dim=1).mean(), float(k3.sum() / mask.sum().clamp_min(1.0))


def grpo_loss(logp_new, logp_old, logp_ref, adv, mask, *, beta: float, eps: float = CLIP_EPS):
    """Surrogate + beta * k3 KL; returns (loss, monitors)."""
    if beta not in BETAS:
        raise ValueError(f"beta must be one of {BETAS} (spec §6.4)")
    surrogate, clip_share = clipped_surrogate(logp_new, logp_old, adv, mask, eps)
    kl, mean_kl = k3_kl(logp_new, logp_ref, mask)
    return surrogate + beta * kl, {"clip_share": clip_share, "mean_kl": mean_kl, "surrogate": float(surrogate)}


@dataclass
class SampledBatch:
    """One sampled batch: completions [C, T] (token ids), mask [C, T], rewards [contexts, G]."""
    contexts: Any
    tokens: Any
    mask: Any
    rewards: np.ndarray
    logp_ref: Any


def ppo_update(logp_fn: Callable[[Any, Any], Any], params, optimizer, batch: SampledBatch, *, beta: float,
               epochs: int = UPDATE_EPOCHS, advantage: str = "loo") -> list[dict[str, Any]]:
    """Two (``epochs``) clipped-surrogate updates on one sampled batch; pi_old is fixed at the batch's start.

    ``logp_fn(contexts, tokens)`` returns per-token log-probabilities [C, T] under the current parameters.
    Rewards are [contexts, G] with completions ordered context-major, so completion c belongs to context c // G.
    """
    import torch
    adv_np = (loo_advantages if advantage == "loo" else std_advantages)(batch.rewards).reshape(-1)
    adv = torch.as_tensor(adv_np, dtype=torch.float32)
    with torch.no_grad():
        logp_old = logp_fn(batch.contexts, batch.tokens).detach()
    out = []
    for epoch in range(epochs):
        logp_new = logp_fn(batch.contexts, batch.tokens)
        loss, mon = grpo_loss(logp_new, logp_old, batch.logp_ref, adv, batch.mask, beta=beta)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        out.append({"epoch": epoch, "loss": float(loss), **mon,
                    "zero_advantage_share": zero_advantage_share(batch.rewards)})
    return out


# ------------------------------------------------------------------ R-B on the reasoning wrapper (§6.4)

def sampled_analysis_mask(out: dict, closed) -> Any:
    """Mask over ``out['analysis_token_logprob']`` of the tokens the policy sampled: the analysis text, plus the closing
    tag when ``closed`` (the policy sampled ``</analysis>``). Needs ``analysis_text_tokens`` and
    ``analysis_close_tokens`` from the wrapper's ``forward``."""
    import torch
    for key in ("analysis_text_tokens", "analysis_close_tokens"):
        if key not in out:
            raise ValueError(f"the policy's forward must return {key} (sampled-token mask of the PPO sequence)")
    base = out["analysis_token_mask"]
    n_tok = out["analysis_text_tokens"].long() + torch.as_tensor(
        [bool(c) for c in closed], device=base.device).long() * out["analysis_close_tokens"].long()
    cols = torch.arange(base.shape[1], device=base.device)[None, :]
    mask = (cols < n_tok[:, None]).to(base.dtype) * base
    if not torch.equal(mask.sum(dim=1), n_tok.to(base.dtype).clamp(max=base.shape[1])):
        raise ValueError("sampled analysis tokens exceed the scored span")
    return mask


def rb_group_step(policy, ref_policy, prompts, y_train, u, optimizer, *, u_max: float, lambda_a: float, beta: float,
                  group: int = GROUP_SIZE, seed: int = 0, epochs: int = UPDATE_EPOCHS, advantage: str = "loo",
                  temperature: float = 1.0) -> dict[str, Any]:
    """One R-B batch on a ``ReasonThenBinWrapper``-like policy (``generate`` + ``forward(batch, analyses)``).

    For each prompt: G analyses are sampled (``policy.generate``), each completion's action is sampled from
    sigmoid(action_logit) (the ``<exec>``/``<skip>`` token), and the reward is ``rb_reward`` with the belief read
    (not sampled) at the read-out position. A completion whose analysis the policy did not close itself (EOS or the
    256-token cap before ``</analysis>``; ``policy.last_generated_closed``) is a format violation. The PPO sequence of a
    completion is its **sampled** tokens only: the analysis text, plus the closing tag when the policy sampled it
    (never the tag that ``segments`` appends to an unclosed span, nor the trailing newline), plus its action token. The
    belief logits additionally get the exact RPS gradient (mean over completions). pi_old and the reference
    log-probabilities are fixed at the batch's start; ``epochs`` updates follow. The policy runs in eval mode for the
    whole step (dropout, e.g. LoRA dropout, off), so sampling, pi_old and pi_theta use the same deterministic network;
    the previous train/eval mode is restored at the end.

    Known approximation: the analysis is decoded to text and re-encoded by ``forward``; where the tokenizer does not
    round-trip, the scored tokens differ from the sampled ids.
    ``y_train`` [N, 12] and ``u`` [N] come from the label distribution (never one seed draw).
    """
    import torch
    from r1.c3.train.losses import rps, softmax_probs
    n = len(prompts)
    batch = [p for p in prompts for _ in range(group)]
    was_training = bool(getattr(policy, "training", False))
    if hasattr(policy, "eval"):
        policy.eval()
    analyses, closed = [], []
    for j in range(group):
        analyses.append(policy.generate(list(prompts), temperature=temperature, seed=seed * 1000 + j))
        counts = getattr(policy, "last_generated_tokens", None)
        if counts is None or len(counts) != n:
            raise ValueError("the policy must record last_generated_tokens for every generated analysis")
        shut = getattr(policy, "last_generated_closed", None)
        if shut is None or len(shut) != n:
            raise ValueError("the policy must record last_generated_closed for every generated analysis")
        closed.append([bool(c) for c in shut])
    analyses = [analyses[j][i] for i in range(n) for j in range(group)]
    closed_flat = [closed[j][i] for i in range(n) for j in range(group)]
    # format violation: the policy did not close the span itself (EOS or the 256-token cap came first)
    violation = ~np.array(closed_flat)
    y = torch.as_tensor(np.repeat(np.asarray(y_train, dtype=float), group, axis=0), dtype=torch.float32)
    uu = np.repeat(np.asarray(u, dtype=float), group)
    gen = torch.Generator().manual_seed(seed)

    def sequence_logp(model, actions=None):
        out = model.forward(batch, analyses)
        a_logit = out["action_logit"]
        if actions is None:
            actions = torch.bernoulli(torch.sigmoid(a_logit.detach()), generator=gen)
        a_lp = torch.where(actions > 0, torch.nn.functional.logsigmoid(a_logit),
                           torch.nn.functional.logsigmoid(-a_logit))
        sampled = sampled_analysis_mask(out, closed_flat)
        lp = torch.cat([out["analysis_token_logprob"], a_lp[:, None]], dim=1)
        mask = torch.cat([sampled, torch.ones_like(a_lp)[:, None]], dim=1)
        return out, actions, lp, mask

    with torch.no_grad():
        out0, actions, lp_old, mask = sequence_logp(policy)
        _, _, lp_ref, _ = sequence_logp(ref_policy, actions)
        rps0 = rps(softmax_probs(out0["belief_logits"]), y).numpy()
    rewards = rb_reward(np.clip(rps0, 0.0, 1.0), actions.numpy() > 0, uu, u_max=u_max,
                        format_violation=violation, lambda_a=lambda_a).reshape(n, group)
    adv = torch.as_tensor((loo_advantages if advantage == "loo" else std_advantages)(rewards).reshape(-1),
                          dtype=torch.float32)
    history = []
    for epoch in range(epochs):
        out, _, lp_new, _ = sequence_logp(policy, actions)
        loss_pg, mon = grpo_loss(lp_new, lp_old, lp_ref, adv, mask, beta=beta)
        loss_belief = rps(softmax_probs(out["belief_logits"]), y).mean()
        loss = loss_pg + loss_belief
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        history.append({"epoch": epoch, "loss": float(loss), "belief_rps": float(loss_belief), **mon})
    if was_training and hasattr(policy, "train"):
        policy.train()
    return {"rewards": rewards, "zero_advantage_share": zero_advantage_share(rewards),
            "format_violations": int(violation.sum()), "updates": history}
