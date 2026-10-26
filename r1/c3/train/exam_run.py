"""P.3a runners: E0 aleatoric pass-through and E6 architecture probes (spec §5.5–5.6). ENGINEERING_ONLY; AI-assisted (Claude).

``e0(model, ...)``: (1) frozen-backbone head fit — only the readout heads train (``model.heads``; for the bin-token
family also its new token rows, which are its readout), (2) then LoRA steps with everything trainable, on the soft
(or, for the contrast run, hard argmax) targets of the committed E0 set; metrics and pass on the held-out cells
(``exam_synthetic.e0_metrics`` / ``e0_pass``). ``probes(model, ...)``: A3, A4 on every model; A5 on the bin-token
family (spec: "BinTokenWrapper"); A1/A2 only where the model packs (``model.packing``), else recorded as not
applicable. Evidence runs need the P.3a authorization note; the CLI enforces it.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import torch

from r1.c3.train import exam_synthetic as E
from r1.c3.train import losses as L
from r1.c3.train.trainer import Trainer, TrainConfig, seed_everything


def e0_rows(split: str, target: str) -> list[dict]:
    return [{"prompt": E.prompt_from_dict(it["prompt"]), "y": torch.tensor(it[target], dtype=torch.float32), "item": it}
            for it in E.load() if it["split"] == split]


def belief_loss(out: dict, batch: list[dict]) -> torch.Tensor:
    y = torch.stack([r["y"] for r in batch]).to(out["belief_logits"].device)
    return L.rps(L.softmax_probs(out["belief_logits"]), y).mean()


def head_parameters(model) -> list[torch.nn.Parameter]:
    params = [p for p in model.heads.parameters()]
    if getattr(model, "family", "") in ("qwen_control", "qwen_reason"):
        params += [p for n, p in model.named_parameters() if "trainable_tokens" in n]
    return params


@torch.no_grad()
def predict(model, prompts, batch_size: int = 16) -> np.ndarray:
    model.eval()
    out = []
    for i in range(0, len(prompts), batch_size):
        lg = model(prompts[i:i + batch_size])["belief_logits"]
        out.append(torch.softmax(lg.float(), -1).cpu().numpy())
    return np.concatenate(out)


def _freeze_all_but(model, keep: list[torch.nn.Parameter]) -> dict:
    keep_ids = {id(p) for p in keep}
    state = {}
    for p in model.trainable_parameters():
        state[id(p)] = p
        p.requires_grad_(id(p) in keep_ids)
    return state


def e0(model, run_dir: Path | str, *, target: str = "y_soft", head_steps: int = 200, lora_steps: int = 200,
       batch_size: int = 8, seed: int = 0, n_train: int | None = None, n_test: int | None = None,
       lr: float = 1e-4, head_lr: float = 1e-3) -> dict:
    run_dir = Path(run_dir)
    seed_everything(seed)
    train = e0_rows("train", target)[:n_train]
    test = e0_rows("test", target)[:n_test]
    from r1.c3.train.model import new_head_parameters
    trainable = list(model.trainable_parameters())
    heads = head_parameters(model)          # trained in step (1); new ones at head_lr, released ones at lr
    new = new_head_parameters(model)
    # (1) frozen backbone: heads only
    _freeze_all_but(model, heads)
    cfg1 = TrainConfig(seed=seed, epochs=1e9, max_steps=head_steps, batch_size=batch_size, grad_accum=1, lr=lr,
                       head_lr=head_lr)
    Trainer(model, train, belief_loss, cfg1, run_dir / "head_fit", head_params=new).train()
    p_head = predict(model, [r["prompt"] for r in test])
    # (2) LoRA steps: everything trainable again
    for p in trainable:
        p.requires_grad_(True)
    cfg2 = TrainConfig(seed=seed + 1, epochs=1e9, max_steps=lora_steps, batch_size=batch_size, grad_accum=1, lr=lr,
                       head_lr=head_lr)
    Trainer(model, train, belief_loss, cfg2, run_dir / "lora", head_params=new).train()
    p_lora = predict(model, [r["prompt"] for r in test])
    items = [r["item"] for r in test]
    m_head, m_lora = E.e0_metrics(p_head, items), E.e0_metrics(p_lora, items)
    np.save(run_dir / "pred_test_lora.npy", p_lora)
    return {"target": target, "n_train": len(train), "n_test": len(test), "head_fit": m_head, "lora": m_lora,
            "pass": E.e0_pass(m_lora) if target == "y_soft" else None}


def probes(model, run_dir: Path | str, *, n: int = 32, seed: int = 0) -> dict:
    """E6 on a (trained) model. Sizes reduced by ``n`` for dry runs; the evidence run uses the spec defaults."""
    run_dir = Path(run_dir)
    tok = model.tok
    out: dict = {}
    # A3 history-length robustness (prompts over the model's context: recorded as the wrapper handled them)
    a3 = E.a3_probe(tok, n=n, seed=E.SEED)
    rps = {}
    for length, prompts in a3["prompts"].items():
        try:
            p = predict(model, prompts)
            rps[length] = L.rps(torch.tensor(p), torch.tensor(np.array(a3["targets"]), dtype=torch.float32)).numpy()
        except Exception as exc:  # e.g. Kev's strict state limit: recorded, not hidden
            out.setdefault("A3_errors", {})[str(length)] = f"{type(exc).__name__}: {exc}"[:300]
    out["A3"] = E.a3_pass(rps) if 0 in rps and len(rps) > 1 else {"pass": None, "reason": "not all lengths ran"}
    # A4 width monotonicity
    a4 = E.a4_probe(n=n)
    std = [E.belief_moments(predict(model, row))[1] for row in a4]
    out["A4"] = E.a4_pass(np.array(std))
    # A5 slot bias: bin-token family only; listing order via the wrapper's bin_order, canonical options
    if getattr(model, "family", "") in ("qwen_control", "qwen_reason"):
        from dataclasses import replace
        from r1.c3.train.types import BIN_OPTIONS
        keep = list(model.bin_order)
        beliefs = []
        try:
            for row in E.a5_probe(n=n):
                per = []
                for p in row:
                    model.bin_order = list(p.meta["option_perm"])
                    per.append(predict(model, [replace(p, options=BIN_OPTIONS)])[0])
                beliefs.append(per)
        finally:
            model.bin_order = keep
        out["A5"] = E.a5_pass(np.array(beliefs))
    else:
        out["A5"] = {"pass": None, "reason": "A5 applies to BinTokenWrapper only (spec §5.6)"}
    # A1/A2 only for packed models
    if getattr(model, "packing", False):
        with torch.no_grad():
            model.eval()
            a1 = [E.a1_pass(model(s["alone"])["belief_logits"].float().numpy(),
                            model(s["packed"])["belief_logits"][:1].float().numpy()) for s in E.a1_probe(n_states=n)]
            out["A1"] = {"max_abs": max(r["max_abs"] for r in a1), "pass": all(r["pass"] for r in a1)}
            a2 = [E.a2_pass([model(pk)["belief_logits"].float().numpy() for pk in s["packed"]], s["orders"])
                  for s in E.a2_probe(n_states=n)]
            out["A2"] = {"max_abs": max(r["max_abs"] for r in a2), "pass": all(r["pass"] for r in a2)}
    else:
        out["A1"] = out["A2"] = {"pass": None, "reason": "model does not pack (spec §5.6: packed models only)"}
    return out
