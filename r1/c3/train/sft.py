"""Track P Stage S (SFT, A5) runner: belief only (spec §6.1; R1-TRACKP-SFT-DEV). ENGINEERING_ONLY; AI-assisted (Claude).

``run_stage_s(model, train, val, run_dir, protocol, ...)`` trains one configuration (one adapter lr, one seed) on the
rows of ``sft_data.load_sft_data``:

* loss L_S = RPS + CE on the soft label (``losses.stage_s_loss``); ``loss: "ce"`` is the spec §6.1 CE-only
  ablation, ``loss: "rps"`` an extra RPS-only variant;
* the shared loop ``trainer.Trainer``: AdamW, cosine with 5 % warm-up, effective batch 16 (micro-batch x grad
  accumulation), at most 5 epochs, evaluation every 1/4 epoch, early stopping on val RPS with patience 2, the best
  checkpoint (not the last) loaded back at the end;
* eval hook (``val_metrics``) on the validation instances' training labels (seeds 7001–7005) only: RPS, RPS skill
  against the training base rate, NLL (soft-label cross-entropy), all-bins and top-1 ECE, the PIT histogram, mean
  predictive sd and mean label sd and their ratio — the spec §4 run log minus the decision-utility and action terms,
  which need the action target (Stage R-A);
* post-hoc temperature scaling (R1-TEMPERATURE): one scalar T fitted on val by soft-label cross-entropy
  (``metrics.fit_temperature``) on the selected checkpoint; val metrics are reported before and after scaling and T
  is saved next to the best checkpoint (``best/temperature.json``).

Nothing here sees test instances or evaluation seeds: the data directory holds no test rows, and ``Trainer`` runs
``run.guard_rows`` on the training rows. ``select_lr(run_dirs)`` picks, among the runs of one lr grid, the lr with the
lowest mean best val RPS over seeds (spec §4, R1-LR-GRID); it requires one data directory and one protocol across the
runs and distinct seeds (three per lr), and carries the data's label status — under R1-TRACKP-SFT-DEV no output of
this module is used for selection.

The training-config digest includes the data directory's ``sft_data.json`` sha256, so resuming a run directory on
other data STOPs (``Trainer.resume``). ``max_steps`` / ``eval_every_steps`` overrides are recorded as a protocol
deviation in the report. The starting model is evaluated (step 0) and is a best-checkpoint candidate (inherited from
the shared loop); the report records the selected step.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import torch

from r1.c3.train import losses as L
from r1.c3.train import metrics as M
from r1.c3.train.trainer import Trainer, TrainConfig

SFT_REPORT_SCHEMA = "trackp_sft_report/v1"
DEFAULT_PROTOCOL = {"loss": "rps+ce", "effective_batch": 16, "micro_batch": 8, "max_epochs": 5,
                    "warmup_frac": 0.05, "eval_every_frac": 0.25, "patience": 2, "lr_grid": [1e-5, 3e-5, 1e-4],
                    "head_lr": 1e-3, "token_lr": 1e-4, "temperature_scaling": True}


LOSSES = ("rps+ce", "ce", "rps")


def stage_s_loss_fn(kind: str = "rps+ce"):
    if kind not in LOSSES:
        raise ValueError(f"unknown Stage S loss {kind!r}")

    def loss(out: dict, batch: Sequence[dict]) -> torch.Tensor:
        logits = out["belief_logits"]
        y = torch.stack([r["y"] for r in batch]).to(logits.device)
        p = L.softmax_probs(logits)
        if kind == "ce":
            return L.soft_ce(p, y).mean()
        return L.stage_s_loss(p, y, ce=kind == "rps+ce")
    return loss


@torch.no_grad()
def predict_logits(model, prompts, batch_size: int = 16) -> np.ndarray:
    was_training = getattr(model, "training", False)
    model.eval() if hasattr(model, "eval") else None
    out = []
    for i in range(0, len(prompts), batch_size):
        out.append(model.forward(list(prompts[i:i + batch_size]))["belief_logits"].float().cpu().numpy())
    if was_training:
        model.train()
    return np.concatenate(out) if out else np.zeros((0, 12))


def _softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


def val_metrics(probs: np.ndarray, y: np.ndarray, base: np.ndarray, prefix: str = "val_") -> dict:
    """The belief metrics of one evaluation (module docstring); ``base``: training base-rate forecast."""
    nll = float(-(y * np.log(np.clip(probs, 1e-12, None))).sum(axis=-1).mean())
    keep = (1.0 - y[:, 0]) > 1e-9
    out = {"rps": M.mean_rps(probs, y), "rps_skill": M.rps_skill(probs, y, base), "nll": nll,
           "ece_all_bins": M.ece_all_bins(probs, y), "ece_top1": M.ece_top1(probs, y),
           "pit_histogram": [float(v) for v in M.pit_histogram(probs, y)],
           "mean_pred_sd": float(M.predictive_sd(probs[keep]).mean()) if keep.any() else float("nan"),
           "mean_label_sd": float(M.predictive_sd(y[keep]).mean()) if keep.any() else float("nan"),
           "width_ratio": M.width_ratio(probs, y) if keep.any() else float("nan")}
    return {prefix + k: v for k, v in out.items()}


def micro_batching(protocol: Mapping) -> tuple[int, int]:
    eff, micro = int(protocol["effective_batch"]), int(protocol["micro_batch"])
    if micro < 1 or eff % micro:
        raise ValueError(f"micro batch {micro} does not divide the effective batch {eff}")
    return micro, eff // micro


def run_stage_s(model, train: Sequence[dict], val: Sequence[dict], run_dir: Path | str, protocol: Mapping, *,
                lr: float, seed: int, head_params=(), token_params=(), max_steps: int | None = None,
                eval_every_steps: int | None = None, data_sha256: str | None = None, label_status: str | None = None,
                log=print) -> dict:
    """Train one Stage S configuration; returns the report (module docstring)."""
    protocol = {**DEFAULT_PROTOCOL, **protocol}
    if float(lr) not in [float(x) for x in protocol["lr_grid"]]:
        raise ValueError(f"lr {lr} is not on the grid {protocol['lr_grid']} (R1-LR-GRID)")
    if protocol["loss"] not in LOSSES:
        raise ValueError(f"unknown Stage S loss {protocol['loss']!r}")
    run_dir = Path(run_dir)
    micro, accum = micro_batching(protocol)
    y_train = np.stack([r["y"].numpy() for r in train])
    y_val = np.stack([r["y"].numpy() for r in val])
    base = M.base_rate(y_train)
    val_prompts = [r["prompt"] for r in val]

    def evaluate(m) -> dict:
        return val_metrics(_softmax(predict_logits(m, val_prompts)), y_val, base)

    cfg = TrainConfig(seed=seed, epochs=float(protocol["max_epochs"]), max_steps=max_steps, batch_size=micro,
                      grad_accum=accum, lr=float(lr), head_lr=float(protocol["head_lr"]),
                      token_lr=float(protocol["token_lr"]), warmup_frac=float(protocol["warmup_frac"]),
                      eval_every_frac=float(protocol["eval_every_frac"]), eval_every_steps=eval_every_steps,
                      early_stop_patience=int(protocol["patience"]), early_stop_metric="val_rps",
                      keep_checkpoints=1, extra={"sft_data_sha256": data_sha256})
    trainer = Trainer(model, train, stage_s_loss_fn(protocol["loss"]), cfg, run_dir,
                      head_params=head_params, token_params=token_params, evaluate=evaluate, log=log)
    res = trainer.train()
    logits = predict_logits(model, val_prompts)
    report = {"schema": SFT_REPORT_SCHEMA, "lr": float(lr), "seed": int(seed), "protocol": protocol,
              "data_sha256": data_sha256, "label_status": label_status,
              "protocol_deviation": {k: v for k, v in (("max_steps", max_steps), ("eval_every_steps", eval_every_steps))
                                     if v is not None} or None,
              "train_config_sha256": cfg.digest(), "n_train": len(train), "n_val": len(val),
              "steps_per_epoch": trainer.steps_per_epoch, "total_steps": trainer.total_steps, "train": res,
              "selected": evaluate(model)}
    if protocol["temperature_scaling"]:
        T = M.fit_temperature(logits, y_val)
        report["temperature"] = T
        report["selected_temperature_scaled"] = val_metrics(_softmax(logits / T), y_val, base)
        (run_dir / "best").mkdir(parents=True, exist_ok=True)
        (run_dir / "best" / "temperature.json").write_text(json.dumps({"temperature": T, "fitted_on": "val",
                                                                       "objective": "soft-label CE"}) + "\n")
    np.save(run_dir / "pred_val_logits.npy", logits)
    (run_dir / "sft_report.json").write_text(json.dumps(report, indent=1, sort_keys=True, default=float) + "\n")
    return report


def select_lr(run_dirs: Sequence[Path | str], *, seeds_per_lr: int = 3) -> dict:
    """Among Stage S runs of one grid: the lr with the lowest mean best val RPS over its seeds (module docstring)."""
    reports = [json.loads((Path(d) / "sft_report.json").read_text()) for d in run_dirs]
    if not reports:
        raise ValueError("no runs")
    for key in ("data_sha256", "protocol", "label_status"):
        if len({json.dumps(r.get(key), sort_keys=True) for r in reports}) != 1:
            raise ValueError(f"runs differ in {key}; one grid uses one data directory and one protocol")
    if any(r.get("protocol_deviation") for r in reports):
        raise ValueError("a run deviates from the protocol (max_steps / eval_every_steps); not a grid run")
    by_lr: dict[float, dict[int, float]] = {}
    for r in reports:
        seeds = by_lr.setdefault(float(r["lr"]), {})
        if int(r["seed"]) in seeds:
            raise ValueError(f"lr {r['lr']}: seed {r['seed']} appears twice")
        seeds[int(r["seed"])] = float(r["train"]["best_value"])
    grid = sorted(float(x) for x in (reports[0].get("protocol") or {}).get("lr_grid") or [])
    if not grid:
        raise ValueError("the runs' protocol has no lr_grid; cannot check that the whole grid was run")
    if sorted(by_lr) != grid:
        raise ValueError(f"the runs cover lrs {sorted(by_lr)}, not the whole grid {grid}")
    counts = {lr: len(v) for lr, v in by_lr.items()}
    if set(counts.values()) != {seeds_per_lr}:
        raise ValueError(f"each lr needs {seeds_per_lr} distinct seeds (spec §4): {counts}")
    means = {lr: float(np.mean(list(v.values()))) for lr, v in by_lr.items()}
    best = min(means, key=lambda k: (means[k], k))
    return {"selected_lr": best, "mean_best_val_rps": means, "runs": [str(d) for d in run_dirs],
            "data_sha256": reports[0].get("data_sha256"), "label_status": reports[0].get("label_status")}
