"""Track P command line (RUNBOOK Track P 1.6). ENGINEERING_ONLY; AI-assisted (Claude).

Subcommands: ``spike`` (P.0), ``toy`` (P.1/P.2 toy batch), ``e0``, ``e0-select`` and ``probes`` (P.3a; E0 protocol
v2 of 26 Oct), ``exam`` (P.3b analysis
with the frozen rule), ``sft`` (P.4), ``a6`` (P.5), ``rb`` (P.6). Every run writes ``manifest.json`` (base
revision, adapter/heads sha256, data-manifest hash, seed, git commits of both repos, GPU-lease log, evidence label).

Rules enforced here:
* the config may hold no ``TODO_VERIFY_ON_HOST`` value (``--check-config`` lists them; ``--tiny`` dry runs on tiny
  random-weight models on CPU may pass ``--allow-placeholders``, real runs never);
* GPU work runs under the GPU lease (``r1.c3.train.run.gpu_lease``; R1-PORTAL-SCHEDULE); ``--tiny`` runs on CPU;
* evaluation subcommands (P.3a ``e0``/``probes``, P.3b ``exam``, P.4–P.6) need their authorization note
  ``docs/r1/authorizations/trackp_<phase>_<date>.md`` for every run not labelled DRYRUN (``--tiny`` is always
  DRYRUN; ``--evidence DRYRUN`` on a real base is the one-model dry run);
* evaluation-seed columns are refused before the P.4 final evaluation (``run.guard_rows``).

Examples::

    python r1/scripts/trackp.py --check-config --allow-placeholders
    python r1/scripts/trackp.py spike --tiny --family kev --allow-placeholders --run-dir /tmp/x
    python r1/scripts/trackp.py spike --base kev-0.8b --run-dir ~/r1_trackp/runs/p0/kev-0.8b
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from r1.c3.train import run as R  # noqa: E402
from r1.c3.train.trainer import seed_everything  # noqa: E402

DEFAULT_CONFIG = REPO / "r1" / "scripts" / "configs" / "trackp_portal.json"
PHASE_OF = {"e0": "p3a", "e0-select": "p3a", "probes": "p3a", "exam": "p3b", "sft": "p4", "a6": "p5", "rb": "p6"}


def _write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n")


def _evidence(args) -> str:
    if args.tiny:
        return "DRYRUN"
    return args.evidence


def _require_authorization(args) -> None:
    phase = PHASE_OF.get(args.cmd)
    if phase and _evidence(args) != "DRYRUN" and R.authorization_note(phase) is None:
        raise R.TrackPStop(f"{args.cmd} ({_evidence(args)}) needs docs/r1/authorizations/trackp_{phase}_<date>.md; "
                           "only DRYRUN runs go without it")


def _build(args, cfg: dict):
    """(model, tokenizer, rebuild, base record)."""
    import torch
    from r1.c3.train import model as M
    from r1.c3.train import tiny
    if args.tiny:
        work = Path(args.run_dir) / "_tiny"
        make = lambda: tiny.build_tiny(args.family, work, head_form=args.head_form, seed=args.seed)  # noqa: E731
        m = make()
        return m, m.tok, make, {"tiny": args.family, "note": "random-weight stand-in; not a pool model"}
    spec = cfg["bases"][args.base]
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    if dev != "cuda":
        raise R.TrackPStop("no CUDA device: a real-base run on CPU is a CPU fallback (STOP)")
    dtype = getattr(torch, cfg["gpu"]["dtype"])
    fam = spec["family"]

    def make():
        if fam == "kev":
            return M.build_model("kev", spec["local_path"], base_name=spec["base_repo"],
                                 base_revision=spec["base_revision"], init_from=spec.get("adapter_local_path"),
                                 head_form=args.head_form, dtype=dtype, device=dev, attn="sdpa")
        if fam == "laya":
            return M.build_model("laya", spec["local_path"], head_form=args.head_form, device=dev)
        return M.build_model(fam, spec["local_path"], head_form=args.head_form, dtype=dtype, device=dev)
    m = make()
    base = {k: spec.get(k) for k in ("family", "base_repo", "base_revision", "adapter_repo", "adapter_revision")}
    return m, m.tok, make, base


@contextlib.contextmanager
def _lease(args, lease_log: list):
    if args.tiny:
        yield None
        return
    with R.gpu_lease(f"trackp {args.cmd} {args.base}", run_log=lease_log,
                     lock_path=Path(os.path.expanduser(args.cfg["gpu"]["lock_path"])),
                     log_path=Path(os.path.expanduser(args.cfg["runs_dir"])) / "gpu_lease_log.jsonl") as lease:
        yield lease


def cmd_spike(args, cfg) -> dict:
    from r1.c3.train import spike as S
    lease_log: list = []
    with _lease(args, lease_log):
        seed_everything(args.seed)          # before the model exists: LoRA and new-head init follow the seed
        model, tok, make, base = _build(args, cfg)
        sp = cfg["spike"]
        rep = S.spike(model, args.run_dir, tok=tok, toy_examples=args.examples or sp["toy_examples"],
                      steps=args.steps or sp["steps"], batch_size=sp["batch_size"], seed=args.seed,
                      measure=not args.no_measure, rebuild=make,
                      grad_ckpt=bool(cfg["gpu"].get("gradient_checkpointing")) and not args.tiny,
                      lr=1e-4 if args.tiny else cfg["bases"][args.base]["lr"], head_lr=cfg["head_lr"])
    return {"report": rep, "base": base, "model_files": rep["saved_sha256"], "lease": lease_log,
            "data": S.toy_rows(args.examples or sp["toy_examples"])}


def cmd_toy(args, cfg) -> dict:
    from r1.c3.train import spike as S
    from r1.c3.train.trainer import Trainer, TrainConfig
    lease_log: list = []
    tb = cfg["toy_batch"]
    with _lease(args, lease_log):
        seed_everything(args.seed)          # before the model exists: LoRA and new-head init follow the seed
        model, tok, make, base = _build(args, cfg)
        seed_everything(args.seed)
        rows = S.toy_rows(args.examples or tb["examples"], offset=100)
        steps = args.steps or tb["steps"]
        from r1.c3.train.model import new_head_parameters
        if cfg["gpu"].get("gradient_checkpointing") and not args.tiny:
            model.enable_gradient_checkpointing()   # spec §4
        lr = 1e-4 if args.tiny else cfg["bases"][args.base]["lr"]
        before = S.batch_losses(model, rows)   # the whole fixed batch, eval mode (deterministic)
        tr = Trainer(model, rows, S.sft_loss, TrainConfig(seed=args.seed, epochs=1e9, max_steps=steps, batch_size=8,
                                                          grad_accum=1, lr=lr, head_lr=cfg["head_lr"]),
                     Path(args.run_dir) / "toy", head_params=new_head_parameters(model))
        res = tr.train()
        after = S.batch_losses(model, rows)
        losses = [r["loss"] for r in S._read_metrics(Path(args.run_dir) / "toy")]
        batch = [r["prompt"] for r in rows[:8]]
        b0, a0 = S.probs(model, batch)
        rec = model.save(Path(args.run_dir) / "saved")
        model.to("cpu")                      # never two copies on the card
        import torch
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        fresh = make()
        fresh.load(Path(args.run_dir) / "saved")
        b1, a1 = S.probs(fresh, batch)
    import torch
    rep = {**res, "loss_first_step": losses[0], "loss_last_step": losses[-1], "batch_loss_before": before,
           "batch_loss_after": after, "lr": lr, "head_lr": cfg["head_lr"],
           # P.1/P.2 "loss decreases": the full fixed batch in eval mode, total and each output
           "loss_decreased": after["total"] < before["total"],
           "belief_loss_decreased": after["belief"] < before["belief"],
           "action_loss_decreased": after["action"] < before["action"] if before["action"] else None,
           "reload_identical": bool(torch.equal(b0, b1) and (a0 is None or torch.equal(a0, a1)))}
    return {"report": rep, "base": base, "model_files": rec["files"], "lease": lease_log, "data": rows}


def cmd_e0(args, cfg) -> dict:
    """E0 protocol v2 (R1-E0-PROTOCOL): one (variant, target, lr) per run; ``e0-select`` picks the lr."""
    from r1.c3.train import exam_run as X
    from r1.c3.train import exam_synthetic as E
    lease_log: list = []
    e0c = cfg["e0"]
    lr = args.lr if args.lr is not None else (1e-4 if args.tiny else None)
    if lr is None or (not args.tiny and lr not in cfg["lr_grid"]):
        raise R.TrackPStop(f"e0 needs --lr from the configured grid {cfg['lr_grid']} (R1-LR-GRID)")
    want = "linear12" if args.variant == "fresh" else "softmax12"
    if args.head_form not in (want, "softmax12"):
        raise R.TrackPStop(f"e0 --variant {args.variant} uses head form {want}")
    args.head_form = want
    with _lease(args, lease_log):
        seed_everything(args.seed)          # before the model exists: LoRA and new-head init follow the seed
        model, tok, make, base = _build(args, cfg)
        if cfg["gpu"].get("gradient_checkpointing") and not args.tiny:
            model.enable_gradient_checkpointing()   # spec §4
        rep = X.e0_v2(model, args.run_dir, variant=args.variant, target="y_hard" if args.hard else "y_soft", lr=lr,
                      head_lr=cfg["head_lr"], token_lr=cfg.get("token_lr"),
                      max_steps=args.steps or e0c["max_steps"], eval_every=args.eval_every or e0c["eval_every"],
                      patience=e0c["patience"], batch_size=e0c["batch_size"], seed=args.seed,
                      n_train=args.examples, n_val=args.n_val, n_test=args.n_test)
        files = model.save(Path(args.run_dir) / "saved")["files"]
        if args.with_probes:
            counters = None if args.tiny else _counters(cfg)
            rep["probes"] = X.probes(model, Path(args.run_dir) / "probes", n=args.n_probe, counters=counters)
    return {"report": rep, "base": base, "model_files": files, "lease": lease_log,
            "data": [{"e0_sha256": E.E0_SHA.read_text().split()[0], "val_cells": [list(c) for c in E.VAL_CELLS]}]}


def _counters(cfg):
    from r1.c3.train.budget import pool_counters
    return pool_counters(cfg)


def cmd_e0_select(args, cfg) -> dict:
    """Pick the lr of one (base, variant, target) by the best val RPS over its grid runs (CPU; reads reports)."""
    runs = []
    for d in args.runs:
        rep = json.loads((Path(d) / "report.json").read_text())
        man = json.loads((Path(d) / "manifest.json").read_text())
        runs.append({"run_dir": str(d), "lr": rep["lr"], "variant": rep["variant"], "target": rep["target"],
                     "base": man["base"], "best_val_rps": rep["lora"]["best_value"], "best_step": rep["lora"]["best_step"],
                     "git": man["git"]["paper"]["commit"]})
    keys = {(json.dumps(r["base"], sort_keys=True), r["variant"], r["target"]) for r in runs}
    if len(keys) != 1:
        raise R.TrackPStop(f"e0-select needs runs of one base, variant and target; got {sorted(keys)}")
    if sorted(r["lr"] for r in runs) != sorted(cfg["lr_grid"]):
        raise R.TrackPStop(f"e0-select needs exactly one run per grid lr {cfg['lr_grid']}")
    best = min(runs, key=lambda r: r["best_val_rps"])
    return {"report": {"selected": best, "runs": runs, "criterion": "lowest best val RPS (R1-LR-GRID)"},
            "base": runs[0]["base"], "model_files": {}, "lease": [], "data": runs}


def cmd_probes(args, cfg) -> dict:
    from r1.c3.train import exam_run as X
    lease_log: list = []
    with _lease(args, lease_log):
        seed_everything(args.seed)          # before the model exists: LoRA and new-head init follow the seed
        model, tok, make, base = _build(args, cfg)
        if args.load:
            model.load(Path(args.load))
        counters = _counters(cfg) if args.budget and not args.tiny else None
        rep = X.probes(model, args.run_dir, n=args.n_probe, counters=counters)
    return {"report": rep, "base": base, "model_files": {}, "lease": lease_log, "data": []}


def cmd_exam(args, cfg) -> dict:
    from r1.c3.train import exam_analyze as A
    results = json.loads(Path(args.results).read_text())
    rep = A.analyze(results)
    return {"report": rep, "base": {}, "model_files": {}, "lease": [], "data": [results]}


def cmd_not_yet(args, cfg) -> dict:
    raise R.TrackPStop(f"{args.cmd}: {NOT_YET[args.cmd]}")


NOT_YET = {
    "sft": "P.4 (Phase 8) needs the full B.2 label table and docs/r1/authorizations/trackp_p4_<date>.md; the training "
           "loop is r1.c3.train.trainer with losses.stage_s_loss; the label-table reader is written in Phase 6",
    "a6": "P.5 (Phase 9) runs only after B.7 passes, with the H.8 amendment and its authorization note",
    "rb": "P.6 (Phase 9) runs only after B.7 passes, with its authorization note",
}
COMMANDS = {"spike": cmd_spike, "toy": cmd_toy, "e0": cmd_e0, "e0-select": cmd_e0_select, "probes": cmd_probes,
            "exam": cmd_exam,
            "sft": cmd_not_yet, "a6": cmd_not_yet, "rb": cmd_not_yet}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    ap.add_argument("--check-config", action="store_true")
    ap.add_argument("--allow-placeholders", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    for name in COMMANDS:
        p = sub.add_parser(name)
        p.add_argument("--run-dir", required=name not in ("sft", "a6", "rb"))
        p.add_argument("--base", help="a key of config['bases']")
        p.add_argument("--tiny", action="store_true", help="tiny random-weight stand-in on CPU (DRYRUN)")
        p.add_argument("--family", help="with --tiny: kev | laya | startlux | qwen_control | qwen_reason")
        p.add_argument("--head-form", default="softmax12", choices=("softmax12", "cumulative11", "linear12"))
        p.add_argument("--evidence", default="ENGINEERING_ONLY", choices=R.EVIDENCE_LABELS)
        p.add_argument("--seed", type=int, default=0)
        p.add_argument("--steps", type=int)
        p.add_argument("--examples", type=int)
        p.add_argument("--n-test", type=int)
        p.add_argument("--n-probe", type=int, default=32)
        p.add_argument("--hard", action="store_true", help="e0: hard-label contrast run")
        p.add_argument("--variant", default="fresh", choices=("fresh", "native"),
                       help="e0: fresh LayerNorm + linear belief head (linear12) or the family's native readout")
        p.add_argument("--lr", type=float, help="e0: adapter lr, one of config lr_grid")
        p.add_argument("--eval-every", type=int)
        p.add_argument("--n-val", type=int)
        p.add_argument("--runs", nargs="+", help="e0-select: the run directories of one grid")
        p.add_argument("--budget", action="store_true", help="probes: A3 v2 (pool budget fractions)")
        p.add_argument("--with-probes", action="store_true", help="e0: run E6 on the trained model")
        p.add_argument("--load", help="probes: a saved adapter+heads directory")
        p.add_argument("--no-measure", action="store_true", help="spike: skip the 1,024-token timing")
        p.add_argument("--results", help="exam: the exam results JSON")
        p.add_argument("--allow-placeholders", action="store_true")
    args = ap.parse_args(argv)
    try:
        allow = args.allow_placeholders
        if args.check_config:
            cfg = R.load_config(args.config, allow_placeholders=True)
            left = R.placeholders(cfg)
            print(json.dumps({"config": args.config, "placeholders": left, "sha256": R.config_digest(cfg)}, indent=1))
            return 0 if (not left or allow) else 1
        if not args.cmd:
            ap.error("a subcommand is required")
        if allow and not args.tiny:
            raise R.TrackPStop("--allow-placeholders is for --tiny dry runs only")
        if args.tiny and not args.family:
            ap.error("--tiny needs --family")
        if not args.tiny and args.cmd in ("spike", "toy", "e0", "probes") and not args.base:
            ap.error("--base is required")
        if args.tiny:
            os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
        cfg = R.load_config(args.config, allow_placeholders=allow)
        args.cfg = cfg
        _require_authorization(args)
        res = COMMANDS[args.cmd](args, cfg)
        run_dir = Path(args.run_dir)
        manifest = R.run_manifest(subcommand=args.cmd, evidence=_evidence(args), cfg=cfg, seed=args.seed,
                                  base=res["base"], model_files=res["model_files"],
                                  data_hash=R.data_manifest_hash(res["data"]), lease_log=res["lease"],
                                  extra={"argv": sys.argv[1:] if argv is None else list(argv),
                                         "head_form": args.head_form})
        _write_json(run_dir / "report.json", res["report"])
        _write_json(run_dir / "manifest.json", manifest)
        print(json.dumps({"run_dir": str(run_dir), "report": res["report"]}, indent=1, default=str)[:4000])
        return 0
    except R.TrackPStop as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
