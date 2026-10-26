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


# ---------------------------------------------------------------- E0 protocol v2 (author, 26 Oct; R1-E0-PROTOCOL)

E0_V2 = "trackp_e0/v2"


def rows_of_items(items: list[dict], target: str) -> list[dict]:
    return [{"prompt": E.prompt_from_dict(it["prompt"]), "y": torch.tensor(it[target], dtype=torch.float32),
             "item": it} for it in items]


@torch.no_grad()
def states(model, prompts, batch_size: int = 16) -> torch.Tensor:
    """Readout states [N, d] (float32, on the model's device) in eval mode: the frozen-backbone features."""
    model.eval()
    return torch.cat([model(prompts[i:i + batch_size], return_state=True)["state"]
                      for i in range(0, len(prompts), batch_size)])


def mean_rps(p: np.ndarray, rows: list[dict]) -> float:
    y = torch.stack([r["y"] for r in rows])
    return float(L.rps(torch.tensor(p, dtype=torch.float32), y).mean())


def fit_head_lbfgs(head: torch.nn.Module, tr: torch.Tensor, ytr: torch.Tensor, va: torch.Tensor,
                   yva: torch.Tensor, *, max_outer: int = 500, tol: float = 1e-9) -> dict:
    """R1-E0-HEADFIT: the frozen-backbone head fit, descriptive only. Full-batch L-BFGS (strong-Wolfe line search) of
    the train RPS on cached features, on CPU in float64, until the loss changes by less than ``tol`` (relative)
    twice in a row with the L-BFGS history reset in between (or the gradient vanishes); the fitted head is copied back
    into ``head``."""
    import copy
    work = copy.deepcopy(head).to("cpu", torch.float64)
    work.train()
    X, Y = tr.detach().to("cpu", torch.float64), ytr.detach().to("cpu", torch.float64)
    make = lambda: torch.optim.LBFGS(work.parameters(), lr=1.0, max_iter=100, history_size=50,  # noqa: E731
                                     tolerance_grad=1e-10, tolerance_change=1e-14, line_search_fn="strong_wolfe")
    opt = make()

    def closure():
        opt.zero_grad(set_to_none=True)
        loss = L.rps(torch.softmax(work(X), -1), Y).mean()
        loss.backward()
        return loss
    # Converged when an outer step (up to 100 L-BFGS iterations) improves the loss by less than ``tol`` (relative)
    # twice in a row with the history reset in between: a stalled line search is not taken for convergence.
    prev, losses, converged, restarts, fresh = None, [], False, 0, True
    for it in range(max_outer):
        loss = float(opt.step(closure).detach())
        losses.append(loss)
        gnorm = float(torch.sqrt(sum((p.grad ** 2).sum() for p in work.parameters() if p.grad is not None)))
        stalled = prev is not None and prev - loss <= tol * max(abs(prev), 1e-12)
        if gnorm < 1e-12 or (stalled and fresh):
            converged = True
            break
        if stalled:
            opt, fresh, restarts = make(), True, restarts + 1
        else:
            fresh = False
        prev = loss
    with torch.no_grad():
        work.eval()
        v = float(L.rps(torch.softmax(work(va.detach().to("cpu", torch.float64)), -1),
                        yva.detach().to("cpu", torch.float64)).mean())
    head.load_state_dict({k: t.to(dtype=p.dtype) for (k, t), p in zip(work.state_dict().items(),
                                                                     head.state_dict().values())})
    head.eval()
    return {"method": "full-batch L-BFGS (strong Wolfe), CPU float64", "outer_iterations": it + 1,
            "restarts": restarts, "converged": converged, "train_rps": losses[-1], "val_rps": v, "grad_norm": gnorm}


def e0_v2(model, run_dir: Path | str, *, variant: str = "fresh", target: str = "y_soft", lr: float,
          head_lr: float = 1e-3, token_lr: float | None = None, max_steps: int = 2000, eval_every: int = 100,
          patience: int = 5, batch_size: int = 8, seed: int = 0, n_train: int | None = None,
          n_val: int | None = None, n_test: int | None = None, stage: str = "final") -> dict:
    """E0 v2 for one (variant, target, lr) and ``stage`` ("screen": the lr screen, <= 2,000 steps; "final": the one
    run at the selected lr, cap 6,000, patience 10 — R1-E0-BUDGET; the budget itself comes from the caller).
    ``variant="fresh"``: the model was built with ``head_form="linear12"``; (1) the fresh LayerNorm + linear belief
    head is fitted on cached frozen-backbone states by full-batch L-BFGS on CPU (descriptive only,
    R1-E0-HEADFIT), (2) then LoRA + that head train together. ``variant="native"``: the family's own readout (released head / letter readout / bin
    tokens), zero-shot metrics first, then the LoRA stage. Both stages: early stopping on the validation cells
    (val RPS against the run's own target), at most ``max_steps``, the best checkpoint restored. Metrics on the
    held-out test cells (``e0_metrics_v2``)."""
    from r1.c3.train.model import new_head_parameters, token_row_parameters
    run_dir = Path(run_dir)
    if variant not in ("fresh", "native"):
        raise ValueError("variant is 'fresh' or 'native'")
    if (variant == "fresh") != (model.head_form == "linear12"):
        raise ValueError(f"variant {variant!r} with head_form {model.head_form!r}")
    seed_everything(seed)
    items = E.load()
    tr_items, va_items = E.e0_split(items)
    train = rows_of_items(tr_items, target)[:n_train]
    val = rows_of_items(va_items, target)[:n_val]
    test = rows_of_items([it for it in items if it["split"] == "test"], target)[:n_test]
    test_items = [r["item"] for r in test]
    if stage not in ("screen", "final"):
        raise ValueError("stage is 'screen' or 'final'")
    out: dict = {"protocol": E0_V2, "stage": stage, "variant": variant, "target": target, "lr": lr, "head_lr": head_lr,
                 "token_lr": token_lr, "max_steps": max_steps, "eval_every": eval_every, "patience": patience,
                 "batch_size": batch_size, "n_train": len(train), "n_val": len(val), "n_test": len(test),
                 "val_cells": [list(c) for c in E.VAL_CELLS]}
    if variant == "fresh":
        dev = model.device
        s_tr, s_va, s_te = (states(model, [r["prompt"] for r in rows]) for rows in (train, val, test))
        y = lambda rows: torch.stack([r["y"] for r in rows]).to(dev)  # noqa: E731
        fit = fit_head_lbfgs(model.heads["belief"], s_tr, y(train), s_va, y(val))
        with torch.no_grad():
            p_head = torch.softmax(model.heads["belief"](s_te).float(), -1).cpu().numpy()
        out["head_fit"] = {**fit, "descriptive": True, "test": E.e0_metrics_v2(p_head, test_items, target)}
        run_dir.mkdir(parents=True, exist_ok=True)
        np.save(run_dir / "pred_test_head_fit.npy", p_head)
    else:
        p0 = predict(model, [r["prompt"] for r in test])
        out["zero_shot"] = {"val_rps": mean_rps(predict(model, [r["prompt"] for r in val]), val),
                            "test": E.e0_metrics_v2(p0, test_items, target)}
    # The fresh variant trains the same things on every family (LoRA + the fresh head): the bin-token family's new
    # token rows (its native readout, also present in its prompt) stay frozen at their mean-embedding init.
    frozen = {id(p) for p in token_row_parameters(model)} if variant == "fresh" else set()
    for p in model.trainable_parameters():
        p.requires_grad_(id(p) not in frozen)
    out["frozen_token_rows"] = bool(frozen)

    def evaluate(m) -> dict:
        return {"val_rps": mean_rps(predict(m, [r["prompt"] for r in val]), val)}
    cfg = TrainConfig(seed=seed + 1, epochs=1e9, max_steps=max_steps, batch_size=batch_size, grad_accum=1, lr=lr,
                      head_lr=head_lr, token_lr=token_lr, eval_every_steps=eval_every, early_stop_patience=patience,
                      keep_checkpoints=1)
    res = Trainer(model, train, belief_loss, cfg, run_dir / "lora", head_params=new_head_parameters(model),
                  token_params=[p for p in token_row_parameters(model) if id(p) not in frozen],
                  evaluate=evaluate).train()
    p_lora = predict(model, [r["prompt"] for r in test])
    np.save(run_dir / "pred_test_lora.npy", p_lora)
    out["lora"] = {**res, "test": E.e0_metrics_v2(p_lora, test_items, target)}
    out["pass"] = E.e0_pass_v2(out["lora"]["test"]) if target == "y_soft" else None
    return out


def _a3_rps(model, prompts, targets, errors: dict, key) -> np.ndarray | None:
    try:
        p = predict(model, prompts)
        return L.rps(torch.tensor(p), torch.tensor(np.array(targets), dtype=torch.float32)).numpy()
    except Exception as exc:  # e.g. Kev's strict state limit: recorded, not hidden
        errors[str(key)] = f"{type(exc).__name__}: {exc}"[:300]
        return None


def probes(model, run_dir: Path | str, *, n: int = 32, seed: int = 0, counters: dict | None = None) -> dict:
    """E6 on a (trained) model. Sizes reduced by ``n`` for dry runs; the evidence run uses the spec defaults.
    ``counters`` (the pool's input-token counters, ``budget.pool_counters``) selects the v2 A3 (budget fractions of
    the pool's smallest limit; 2k / 8k descriptive); A4 always reports the v2 label reference as well."""
    run_dir = Path(run_dir)
    tok = model.tok
    out: dict = {}
    errors: dict = {}
    if counters is None:
        # A3 v1: 0 / 2k / 8k tokens (prompts over the model's context: recorded as the wrapper handled them)
        a3 = E.a3_probe(tok, n=n, seed=E.SEED)
        rps = {L_: r for L_, pr in a3["prompts"].items()
               if (r := _a3_rps(model, pr, a3["targets"], errors, L_)) is not None}
        out["A3"] = E.a3_pass(rps) if 0 in rps and len(rps) > 1 else {"pass": None, "reason": "not all lengths ran"}
    else:
        a3 = E.a3_probe_budget(counters, n=n, seed=E.SEED)
        rps = {f: r for f, pr in a3["prompts"].items()
               if (r := _a3_rps(model, pr, a3["targets"], errors, f"frac_{f}")) is not None}
        res = E.a3_pass(rps) if 0.0 in rps and len(rps) == len(a3["prompts"]) else \
            {"pass": None, "reason": "not all levels ran"}
        tokens = {str(f): {fam: int(max(t[fam] for t in a3["tokens"][f])) for fam in a3["families"]}
                  for f in a3["prompts"]}
        reached = {str(f): [float(np.min(v)), float(np.mean(v))] for f, v in a3["reached"].items()}
        out["A3"] = {**res, "protocol": "v2_budget", "limit": a3["limit"], "families": a3["families"],
                     "budget_fraction_reached_min_mean": reached,
                     "budget_min_mean_max": [int(min(a3["budget"])), float(np.mean(a3["budget"])),
                                             int(max(a3["budget"]))], "max_tokens_by_level": tokens}
        if getattr(model, "family", "") == "laya":   # Laya cuts what does not fit: must not happen within budget
            out["A3"]["laya_truncated"] = any(model.encode(p)["truncated"] for pr in a3["prompts"].values()
                                              for p in pr)
        # longer levels, descriptive only (R1-A3-BUDGET)
        long = E.a3_probe(tok, n=n, lengths=(0,) + E.A3_DESCRIPTIVE, seed=E.SEED)
        rl = {L_: r for L_, pr in long["prompts"].items()
              if (r := _a3_rps(model, pr, long["targets"], errors, f"descriptive_{L_}")) is not None}
        out["A3_descriptive"] = E.a3_pass(rl) if 0 in rl and len(rl) > 1 else {"ran": sorted(rl)}
        out["A3_descriptive"]["pass"] = None
    if errors:
        out["A3_errors"] = errors
    # A4 width monotonicity (v1 raw criterion and v2 label reference)
    a4 = E.a4_probe(n=n)
    std = np.array([E.belief_moments(predict(model, row))[1] for row in a4])
    out["A4"] = E.a4_pass(std)
    out["A4_v2"] = E.a4_pass_v2(std, E.a4_label_std(n=n))
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
        # R1-CONTROL-READOUT: read on the readout used for selection (the fresh head when built so), descriptive only
        out["A5"] = {**E.a5_pass(np.array(beliefs)), "readout": model.head_form, "descriptive": True}
        out["A5"]["criterion_met"] = out["A5"].pop("pass")
        out["A5"]["pass"] = None
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
