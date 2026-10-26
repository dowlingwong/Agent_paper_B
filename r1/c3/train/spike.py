"""P.0 spike (RUNBOOK Track P Phase 3) and P.1/P.2 toy batch (Phase 4) procedures. ENGINEERING_ONLY; AI-assisted (Claude).

``spike(model, ...)``: one 12-option forward; LoRA attached (the wrapper's); a toy SFT on soft targets for both
outputs (belief: RPS + CE; action: cost-sensitive BCE on u); save → reload → identical belief and action
probabilities; sha256 of the saved files; peak VRAM and step time at ~1,024 tokens, batch 8, gradient
checkpointing; tree-packing acceptance (``packing.self_check`` on the backbone; expected to fail on Qwen3.5 hybrids —
recorded, not a failure). Toy data = the first examples of the committed E0 set (synthetic, label-free), action
target u = m (the stated mean, z units).
"""
from __future__ import annotations

import copy
import time
from pathlib import Path

import numpy as np
import torch

from r1.c3.train import exam_synthetic as E
from r1.c3.train import losses as L
from r1.c3.train.trainer import Trainer, TrainConfig, seed_everything
from r1.c3.train.types import DecisionPrompt

PROBE_TOKENS = 1024


def toy_rows(n: int, offset: int = 0) -> list[dict]:
    items = [it for it in E.load() if it["split"] == "train"][offset:offset + n]
    return [{"prompt": E.prompt_from_dict(it["prompt"]), "y": torch.tensor(it["y_soft"], dtype=torch.float32),
             "u": torch.tensor(float(it["m"]))} for it in items]


def sft_loss(out: dict, batch: list[dict]) -> torch.Tensor:
    dev = out["belief_logits"].device
    y = torch.stack([r["y"] for r in batch]).to(dev)
    loss = L.stage_s_loss(L.softmax_probs(out["belief_logits"]), y)
    if out.get("action_logit") is not None:
        loss = loss + L.action_loss(out["action_logit"], torch.stack([r["u"] for r in batch]).to(dev))
    return loss


@torch.no_grad()
def probs(model, batch) -> tuple[torch.Tensor, torch.Tensor | None]:
    model.eval()
    out = model(batch)
    b = torch.softmax(out["belief_logits"].float(), -1).cpu()
    a = torch.sigmoid(out["action_logit"].float()).cpu() if out.get("action_logit") is not None else None
    return b, a


def long_prompt(tok, target: int = PROBE_TOKENS) -> DecisionPrompt:
    """A prompt whose neutral text is ~``target`` tokens under ``tok`` (history lines added until it reaches it)."""
    from r1.c3.train.serialize import count_tokens, render_text
    base = E.prompt_from_dict([it for it in E.load() if it["split"] == "train"][0]["prompt"])
    filler = E.irrelevant_history(tok, target, seed=1)
    lines = []
    for ln in filler:
        p = DecisionPrompt(state=base.state + "\n" + "\n".join(lines + [ln]), proposal=base.proposal)
        if count_tokens(tok, render_text(p)) > target:
            break
        lines.append(ln)
    return DecisionPrompt(state=base.state + "\n" + "\n".join(lines), proposal=base.proposal,
                          meta={"probe_tokens": target})


def peak_and_step_time(model, tok, *, batch_size: int = 8, steps: int = 3, grad_ckpt: bool = True) -> dict:
    """Peak VRAM (CUDA only) and mean step time of forward+backward at ~1,024 tokens, batch 8."""
    dev = next(model.parameters()).device
    rec = {"batch_size": batch_size, "probe_tokens": PROBE_TOKENS, "gradient_checkpointing": grad_ckpt}
    if grad_ckpt:
        try:
            model.enable_gradient_checkpointing()
        except Exception as exc:  # recorded, the measurement runs without it
            rec["gradient_checkpointing"] = f"unavailable: {type(exc).__name__}: {exc}"
    p = long_prompt(tok)
    batch = [p] * batch_size
    rows = [{"prompt": p, "y": torch.full((12,), 1 / 12), "u": torch.tensor(0.0)} for _ in batch]
    params = [q for q in model.trainable_parameters()]
    if dev.type == "cuda":
        torch.cuda.reset_peak_memory_stats(dev)
        torch.cuda.synchronize(dev)
    model.train()
    times = []
    for _ in range(steps):
        t0 = time.perf_counter()
        loss = sft_loss(model(batch), rows)
        loss.backward()
        for q in params:
            q.grad = None
        if dev.type == "cuda":
            torch.cuda.synchronize(dev)
        times.append(time.perf_counter() - t0)
    rec["step_time_s"] = float(np.mean(times[1:] if len(times) > 1 else times))
    rec["peak_vram_mib"] = (torch.cuda.max_memory_allocated(dev) / 2**20) if dev.type == "cuda" else None
    return rec


def backbone_of(model):
    """The transformer backbone whose hidden states the readout uses (for the packing self-check), or None."""
    fam = getattr(model, "family", "")
    if fam == "kev":
        return model.kev.lm.get_base_model()
    if fam == "startlux":
        return model.body.get_base_model()
    if fam in ("qwen_control", "qwen_reason"):
        return model.lm.get_base_model().model
    return None  # Laya: encoder packing (state <-> state, branch -> state + own branch) is not implemented


def spike(model, run_dir: Path | str, *, tok=None, toy_examples: int = 100, steps: int = 10, batch_size: int = 8,
          seed: int = 0, measure: bool = True, rebuild=None) -> dict:
    """Run the P.0 spike on ``model``; ``rebuild()`` returns an identically built fresh wrapper for the reload check."""
    from r1.c3.train import packing as P
    run_dir = Path(run_dir)
    seed_everything(seed)
    rep: dict = {"family": model.family, "describe": model.describe()}
    one = toy_rows(1)
    b, a = probs(model, [one[0]["prompt"]])
    rep["forward_one"] = {"belief_shape": list(b.shape), "belief_sum": float(b.sum()),
                          "action": None if a is None else float(a[0])}
    rep["trainable_parameters"] = int(sum(p.numel() for p in model.trainable_parameters()))
    rows = toy_rows(toy_examples)
    cfg = TrainConfig(seed=seed, epochs=1e9, max_steps=steps, batch_size=batch_size, grad_accum=1, lr=1e-4)
    tr = Trainer(model, rows, sft_loss, cfg, run_dir / "toy_sft")
    res = tr.train()
    losses = [r["loss"] for r in _read_metrics(run_dir / "toy_sft")]
    rep["toy_sft"] = {**res, "steps": tr.step, "loss_first": losses[0], "loss_last": losses[-1]}
    batch = [r["prompt"] for r in rows[:8]]
    b0, a0 = probs(model, batch)
    rec = model.save(run_dir / "saved")
    rep["saved_sha256"] = rec["files"]
    if rebuild is not None:
        fresh = rebuild()
        fresh.load(run_dir / "saved")
        b1, a1 = probs(fresh, batch)
        rep["reload_identical"] = bool(torch.equal(b0, b1) and (a0 is None or torch.equal(a0, a1)))
        rep["reload_max_diff"] = float((b0 - b1).abs().max())
        del fresh
    bb = backbone_of(model)
    rep["packing"] = P.self_check(bb) if bb is not None else {
        "ok": False, "reason": "encoder packing not implemented (spec §2.4: little room within 1,024 tokens)",
        "max_diff": None}
    if measure and tok is not None:
        rep["engineering"] = peak_and_step_time(model, tok, batch_size=batch_size)
    return rep


def _read_metrics(run: Path) -> list[dict]:
    import json
    return [json.loads(l) for l in (run / "metrics.jsonl").read_text().splitlines() if '"kind": "step"' in l]
