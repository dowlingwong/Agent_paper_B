"""Shared Track P training loop (spec §4, §6.1; RUNBOOK Track P 1.6). ENGINEERING_ONLY; AI-assisted (Claude).

One PyTorch loop for every wrapper (no TRL). A run directory holds:

* ``ckpt/step_<n>/`` — adapter + heads (``model.save``), ``trainer_state.pt`` (optimizer, scheduler, RNG, step) and
  ``COMPLETE`` written last (a checkpoint without it is ignored on resume);
* ``metrics.jsonl`` — one line per optimizer step and per evaluation;
* ``manifest.json`` — written by ``r1/scripts/trackp.py`` (``run_manifest``).

Checkpoints are written every ¼ epoch (spec §6.1 "evaluation every ¼ epoch") and at the end. Resume loads the
latest complete checkpoint and continues at the next step; the data order is a pure function of (seed, epoch), so
no completed step is repeated and an interrupted run ends with the same parameters as an uninterrupted one (CPU,
deterministic kernels).
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import shutil
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Sequence

import numpy as np
import torch

CHECKPOINT_FRACTION = 0.25


@dataclass
class TrainConfig:
    seed: int = 0
    epochs: float = 1.0
    max_steps: int | None = None       # caps the schedule (spikes, E0's 200 LoRA steps, E3's 300 steps)
    batch_size: int = 8
    grad_accum: int = 2                # effective batch = batch_size * grad_accum (spec §6.1: 16)
    lr: float = 1e-4                   # adapter lr (spec §4: 2e-5 from a released adapter, 1e-4 fresh LoRA)
    head_lr: float = 1e-3              # new heads
    warmup_frac: float = 0.05
    weight_decay: float = 0.0
    max_grad_norm: float = 1.0
    eval_every_frac: float = 0.25
    checkpoint_every_frac: float = CHECKPOINT_FRACTION
    extra: dict = field(default_factory=dict)

    def digest(self) -> str:
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed % 2**32)
    torch.manual_seed(seed)


def epoch_order(n: int, seed: int, epoch: int) -> np.ndarray:
    """Example order of one epoch: a pure function of (seed, epoch), so resume reproduces it."""
    return np.random.default_rng([seed, epoch]).permutation(n)


def _rng_state() -> dict:
    return {"python": random.getstate(), "numpy": np.random.get_state(), "torch": torch.get_rng_state()}


def _set_rng_state(state: dict) -> None:
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    torch.set_rng_state(state["torch"])


def sha256_file(path: Path | str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cosine_lambda(total: int, warmup: int) -> Callable[[int], float]:
    def f(step: int) -> float:
        if step < warmup:
            return (step + 1) / max(1, warmup)
        progress = (step - warmup) / max(1, total - warmup)
        return 0.5 * (1.0 + math.cos(math.pi * min(1.0, progress)))
    return f


class Trainer:
    """``model``: a DecisionModel (``types.py``); ``loss_fn(out, batch_rows) -> scalar tensor``; ``rows``: training
    examples, each a dict with at least ``"prompt"`` (a DecisionPrompt) — targets stay in the row for ``loss_fn``;
    ``evaluate(model) -> dict`` (optional) runs every ``eval_every_frac`` epoch and at the end.

    ``head_params``: parameters trained at ``head_lr`` (new heads); every other trainable parameter takes ``lr``.
    ``stop_after``: test hook — stop (without a final checkpoint) after this many optimizer steps, as a kill would.
    """

    def __init__(self, model, rows: Sequence[dict], loss_fn, cfg: TrainConfig, run_dir: Path | str, *,
                 head_params: Sequence[torch.nn.Parameter] = (), evaluate: Callable | None = None,
                 log: Callable[[str], None] = print, purpose: str = "train") -> None:
        from r1.c3.train.run import guard_rows
        # evaluation-seed columns (7006-7010) never reach training (RUNBOOK Track P §0)
        self.model, self.rows, self.loss_fn, self.cfg = model, guard_rows(rows, purpose=purpose), loss_fn, cfg
        self.run_dir = Path(run_dir)
        self.evaluate, self.log = evaluate, log
        head_ids = {id(p) for p in head_params}
        params = [p for p in model.trainable_parameters() if p.requires_grad]
        groups = [{"params": [p for p in params if id(p) not in head_ids], "lr": cfg.lr},
                  {"params": [p for p in params if id(p) in head_ids], "lr": cfg.head_lr}]
        groups = [g for g in groups if g["params"]]
        if not groups:
            raise ValueError("model has no trainable parameters")
        self.opt = torch.optim.AdamW(groups, weight_decay=cfg.weight_decay)
        self.batches_per_epoch = max(1, math.ceil(len(self.rows) / cfg.batch_size))
        self.steps_per_epoch = max(1, math.ceil(self.batches_per_epoch / cfg.grad_accum))
        total = math.ceil(self.steps_per_epoch * cfg.epochs)
        self.total_steps = min(total, cfg.max_steps) if cfg.max_steps else total
        self.sched = torch.optim.lr_scheduler.LambdaLR(
            self.opt, cosine_lambda(self.total_steps, int(cfg.warmup_frac * self.total_steps)))
        self.ckpt_every = max(1, round(self.steps_per_epoch * cfg.checkpoint_every_frac))
        self.eval_every = max(1, round(self.steps_per_epoch * cfg.eval_every_frac))
        self.step = 0

    # ------------------------------------------------------------------ checkpoints
    def _ckpt_dir(self, step: int) -> Path:
        return self.run_dir / "ckpt" / f"step_{step:07d}"

    def latest_checkpoint(self) -> Path | None:
        root = self.run_dir / "ckpt"
        done = sorted(p for p in root.glob("step_*") if (p / "COMPLETE").is_file()) if root.is_dir() else []
        return done[-1] if done else None

    def save_checkpoint(self) -> Path:
        d = self._ckpt_dir(self.step)
        tmp = d.with_name(d.name + ".tmp")
        shutil.rmtree(tmp, ignore_errors=True)
        tmp.mkdir(parents=True)
        record = self.model.save(tmp / "model")
        torch.save({"step": self.step, "opt": self.opt.state_dict(), "sched": self.sched.state_dict(),
                    "rng": _rng_state(), "cfg_digest": self.cfg.digest()}, tmp / "trainer_state.pt")
        files = {"trainer_state.pt": sha256_file(tmp / "trainer_state.pt"), **record.get("files", {})}
        (tmp / "COMPLETE").write_text(json.dumps({"step": self.step, "sha256": files}, sort_keys=True))
        shutil.rmtree(d, ignore_errors=True)
        tmp.rename(d)
        return d

    def resume(self) -> int:
        """Load the latest complete checkpoint (if any); returns the step it ends at."""
        d = self.latest_checkpoint()
        if d is None:
            return 0
        done = json.loads((d / "COMPLETE").read_text())
        if sha256_file(d / "trainer_state.pt") != done["sha256"]["trainer_state.pt"]:
            raise RuntimeError(f"STOP: {d}/trainer_state.pt does not match its recorded sha256")
        self.model.load(d / "model")
        state = torch.load(d / "trainer_state.pt", map_location="cpu", weights_only=False)
        if state["cfg_digest"] != self.cfg.digest():
            raise RuntimeError("STOP: resume with a different training config")
        self.opt.load_state_dict(state["opt"])
        self.sched.load_state_dict(state["sched"])
        _set_rng_state(state["rng"])
        self.step = int(state["step"])
        self._truncate_metrics(self.step)
        self.log(f"resumed from {d} at step {self.step}")
        return self.step

    # ------------------------------------------------------------------ loop
    def _batches_for_step(self, step: int) -> list[list[dict]]:
        """The micro-batches of optimizer step ``step`` (0-based), from the (seed, epoch) order."""
        out = []
        for micro in range(self.cfg.grad_accum):
            b = step * self.cfg.grad_accum + micro                      # global micro-batch index
            epoch, i = divmod(b, self.batches_per_epoch)
            order = epoch_order(len(self.rows), self.cfg.seed, epoch)
            idx = order[i * self.cfg.batch_size:(i + 1) * self.cfg.batch_size]
            if len(idx):
                out.append([self.rows[j] for j in idx])
        return out

    def _truncate_metrics(self, step: int) -> None:
        """Drop records of steps after the resumed checkpoint (they are recomputed), so each step is logged once."""
        path = self.run_dir / "metrics.jsonl"
        if not path.is_file():
            return
        keep = [ln for ln in path.read_text().splitlines() if ln.strip() and json.loads(ln).get("step", 0) <= step]
        path.write_text("".join(ln + "\n" for ln in keep))

    def _write(self, record: dict) -> None:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        with open(self.run_dir / "metrics.jsonl", "a") as fh:
            fh.write(json.dumps(record, sort_keys=True, default=float) + "\n")

    def train(self, stop_after: int | None = None) -> dict:
        self.resume()
        self.model.train() if hasattr(self.model, "train") else None
        start = self.step
        while self.step < self.total_steps:
            if stop_after is not None and self.step - start >= stop_after:
                return {"stopped_at": self.step, "completed": False}
            t0 = time.perf_counter()
            self.opt.zero_grad(set_to_none=True)
            micro = self._batches_for_step(self.step)
            total_loss = 0.0
            for batch in micro:
                out = self.model.forward([r["prompt"] for r in batch])
                loss = self.loss_fn(out, batch) / len(micro)
                if not torch.isfinite(loss):
                    raise RuntimeError(f"STOP: non-finite loss at step {self.step}")
                loss.backward()
                total_loss += float(loss.detach())
            params = [p for g in self.opt.param_groups for p in g["params"]]
            gnorm = float(torch.nn.utils.clip_grad_norm_(params, self.cfg.max_grad_norm))
            self.opt.step()
            self.sched.step()
            self.step += 1
            self._write({"kind": "step", "step": self.step, "loss": total_loss, "grad_norm": gnorm,
                         "lr": self.sched.get_last_lr()[0], "step_s": time.perf_counter() - t0})
            last = self.step == self.total_steps
            if self.evaluate is not None and (self.step % self.eval_every == 0 or last):
                self._write({"kind": "eval", "step": self.step, **self.evaluate(self.model)})
                self.model.train() if hasattr(self.model, "train") else None
            if self.step % self.ckpt_every == 0 or last:
                self.save_checkpoint()
        return {"stopped_at": self.step, "completed": True, "checkpoint": str(self.latest_checkpoint())}
