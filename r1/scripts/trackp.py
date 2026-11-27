"""Track P command line (RUNBOOK Track P 1.6). ENGINEERING_ONLY; AI-assisted (Claude).

Subcommands: ``spike`` (P.0), ``toy`` (P.1/P.2 toy batch), ``e0``, ``e0-select`` and ``probes`` (P.3a; E0 protocol
v2 of 26 Oct), ``exam`` (P.3b analysis
with the frozen rule), ``sft`` (P.4), ``a6`` (P.5), ``rb`` (P.6). Every run writes ``manifest.json`` (base
revision, adapter/heads sha256, data-manifest hash, seed, git commits of both repos, GPU-lease log, evidence label).

Stage S readiness (R1-TRACKP-SFT-DEV, ENGINEERING_ONLY): ``sft-data`` builds the SFT data directory from a
``c3_features/v3`` table, its sweep ledgers (``trackp_prompt/v2`` prompts) and a label source (an audit's
``label_block.jsonl``, seeds 7001-7005, or ``synthetic``); ``sft-dev`` trains one Stage S configuration on it
(``r1.c3.train.sft``); ``sft-select`` picks the lr of one grid by val RPS. ``sft`` (P.4) stays "not yet" here: its
evidence preconditions belong to a later unit. The protocol is ``configs/trackp_sft.json``; the host config (``--config``) supplies
bases, GPU and micro-batch: ``trackp_portal.json`` (TASL-2 / TASL-7) or ``trackp_htcondor_v2.json`` (HTCondor GPU,
image v2).

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
    python r1/scripts/trackp.py sft-data --table T --sweep INDEX --paper-root P --classification C \
        --labels B2/label_block.jsonl --run-dir ~/r1_trackp/runs/sft_data/sweep1_v3
    python r1/scripts/trackp.py sft-dev --data ~/r1_trackp/runs/sft_data/sweep1_v3/data --base kev-0.8b --lr 3e-5 \
        --seed 0 --run-dir ~/r1_trackp/runs/sft_dev/kev-0.8b_lr3e-5_s0
    python r1/scripts/trackp.py sft-dev --data D --tiny --family hashbag --lr 1e-4 --allow-placeholders --run-dir /tmp/s
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
DEFAULT_SFT_CONFIG = REPO / "r1" / "scripts" / "configs" / "trackp_sft.json"
SFT_DEV_LABELS = ("ENGINEERING_ONLY", "DRYRUN")
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
    if args.tiny and args.family == "hashbag":
        make = lambda: tiny.build_hashbag(seed=args.seed)  # noqa: E731
        m = make()
        return m, None, make, {"tiny": "hashbag", "note": "CPU hash-bag stand-in; not a pool model"}
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
    # An exclusive HTCondor GPU slot has no Track X schedule to read (no origin/main STATUS.md in the job): the host
    # config says so with "lease": "htcondor_slot"; the flock and the foreign-process check still apply. A card leased
    # outside the job by the P.4 direct launcher (p4_direct.py, R1-HOST-FREE) is the same case: "direct_gpu_lease";
    # that card can be shared (R1-CARD-SHARE (1)). The launcher checks free memory and records other processes.
    # Standalone GPU checks on an Ada config request an empty-card lease with --gpu in the same host lock directory.
    direct = args.cfg.get("lease") == "direct_gpu_lease"
    status_text = "" if args.cfg.get("lease") == "htcondor_slot" or direct else None
    gpu = getattr(args, "gpu", None)
    lock_path = Path(args.cfg["gpu"]["lock_path"]).expanduser()
    if direct:
        outer_gpu = os.environ.get("P4_LEASED_GPU_UUID")
        if outer_gpu:
            if gpu is not None or os.environ.get("CUDA_VISIBLE_DEVICES") != outer_gpu:
                raise R.TrackPStop("a P.4 direct job must use its outer card lease")
        elif gpu is None:
            raise R.TrackPStop("select an empty card with --gpu for a standalone Track P job")
        else:
            lock_path = Path(args.cfg["direct"]["lock_dir"]).expanduser() / R.LOCK_PATH.name
    with R.gpu_lease(f"trackp {args.cmd} {args.base}", run_log=lease_log, status_text=status_text,
                     check_processes=not direct or gpu is not None, gpu=gpu, lock_path=lock_path,
                     log_path=Path(os.path.expanduser(args.cfg["runs_dir"])) / "gpu_lease_log.jsonl") as lease:
        R.check_environment(args.cfg)      # R1-ENV-PIN, before loading the model on the bound device
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
    """E0 protocol v2 (R1-E0-PROTOCOL): one (stage, variant, target, lr) per run; ``e0-select`` picks the lr from the
    screen runs; the final run (R1-E0-BUDGET) uses the final budget. ``--steps`` caps a short DRYRUN only."""
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
        bud = e0c[args.stage]
        rep = X.e0_v2(model, args.run_dir, variant=args.variant, target="y_hard" if args.hard else "y_soft", lr=lr,
                      head_lr=cfg["head_lr"], token_lr=cfg.get("token_lr"),
                      max_steps=args.steps or bud["max_steps"], eval_every=args.eval_every or bud["eval_every"],
                      patience=bud["patience"], batch_size=e0c["batch_size"], seed=args.seed,
                      n_train=args.examples, n_val=args.n_val, n_test=args.n_test, stage=args.stage,
                      # the descriptive L-BFGS head fit (~30 min CPU on 0.8B features) once per base: final soft run
                      head_fit=args.stage == "final" and not args.hard)
        rep["budget_override"] = {"steps": args.steps, "eval_every": args.eval_every} \
            if (args.steps or args.eval_every) else None
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
        if rep.get("stage") != "screen":
            raise R.TrackPStop(f"e0-select reads lr-screen runs only; {d} is stage {rep.get('stage')!r}")
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


def _sft_config(args) -> dict:
    sft_cfg = json.loads(Path(args.sft_config).read_text())
    if sft_cfg.get("schema") != "trackp_sft_config/v1":
        raise R.TrackPStop(f"{args.sft_config}: not a Track P SFT config")
    return sft_cfg


def _tokenizers(args):
    if args.tokenizers == "pool":
        from r1.c3.train import serialize as S
        return S.pool_tokenizers(), "pool"
    if args.labels != "synthetic":
        raise R.TrackPStop("--tokenizers whitespace is for synthetic dry runs only; real labels use the pool")

    class _Whitespace:
        def __call__(self, text, add_special_tokens=False):
            return {"input_ids": text.split()}
    return {"whitespace": _Whitespace()}, "whitespace (dry run)"


def cmd_sft_data(args, cfg) -> dict:
    """R1-TRACKP-SFT-DEV: the SFT data directory (``r1.c3.train.sft_data``) under ``<run-dir>/data``."""
    from r1.c3 import dataset as D
    from r1.c3.train import sft_data as SD
    if _evidence(args) != "ENGINEERING_ONLY":
        raise R.TrackPStop("sft-data writes ENGINEERING_ONLY data only (R1-TRACKP-SFT-DEV)")
    for opt in ("table", "sweep", "labels"):
        if not getattr(args, opt):
            raise R.TrackPStop(f"sft-data needs --{opt}")
    if args.tokenizers != "pool" and args.labels != "synthetic":
        raise R.TrackPStop("--tokenizers whitespace is for synthetic dry runs only; real labels use the pool")
    sft_cfg = _sft_config(args)
    if args.table_pin == "none":
        if args.labels != "synthetic":
            raise R.TrackPStop("an unpinned table is for synthetic dry runs only")
        pins, pin_record, universe = {}, None, None
    else:
        if args.table_pin not in sft_cfg["tables"]:
            raise R.TrackPStop(f"unknown --table-pin {args.table_pin!r}; known: {sorted(sft_cfg['tables'])}")
        pin_record = sft_cfg["tables"][args.table_pin]
        pins = pin_record["sha256"]
        if pin_record.get("classification") and not args.classification:
            raise R.TrackPStop(f"table pin {args.table_pin} names a classification sidecar; pass --classification")
        if dict(sft_cfg["splits"].get("split_file") or {}) != SD.SIGNED_SPLIT_FILE:
            raise R.TrackPStop("a pinned table is built only on the signed P3 split file (PRE-SPLIT A): the SFT "
                               "config's splits.split_file must be it")
        universe = None                    # the P3 split file's instances of the table's nodes (build_sft_data)
    # the sweep first: its resolution carries the R1-BX-D8 check for a sweep-2 index; then the table (guarded), then
    # the labels, bound to the same index and classification
    inputs = D.sweep_replay_inputs(args.sweep, paper_root=args.paper_root, classification=args.classification)
    index_sha = D._sha256(Path(inputs["index_path"]))
    class_sha = D._sha256(Path(args.classification)) if args.classification else None
    rows, files = SD.load_table(args.table, pins)
    if args.labels == "synthetic":
        source = SD.SyntheticLabelSource(rows, seed=args.seed)
    else:
        source = SD.LabelBlockSource(args.labels, sweep=args.label_sweep, freeze=args.label_freeze,
                                     index_sha256=index_sha, classification_sha256=class_sha)
    wanted = {r["proposal_id"] for r in source.label_records()}
    toks, tok_name = _tokenizers(args)
    max_tokens = int(sft_cfg["prompt"]["max_tokens"])
    prompts = SD.sweep_prompts(inputs, tokenizers=toks, wanted=wanted, max_tokens=max_tokens)
    out = Path(args.run_dir) / "data"
    split_cfg = {k: v for k, v in sft_cfg["splits"].items()
                 if k not in ("universe", "comment", "cross_split_duplicates_comment")}
    if args.table_pin == "none":       # an unpinned synthetic dry run: its instances are not the design's, so the
        split_cfg.pop("split_file", None)    # salt split of the dry runs; P3 binds every pinned (real) table
    manifest = SD.build_sft_data(
        rows, source, prompts, out, split_cfg=split_cfg,
        universe=universe,
        table_record={"path": str(Path(args.table).resolve()), "sha256": files, "pin": args.table_pin,
                      "pin_record": pin_record},
        prompt_record={"sweep_index": {"path": str(inputs["index_path"]), "sha256": index_sha},
                       "classification": None if not args.classification else
                       {"path": str(args.classification), "sha256": class_sha},
                       "tokenizers": tok_name, "max_tokens": max_tokens, "replayed": len(prompts)})
    digest = SD.sha256_file(out / "sft_data.json")
    return {"report": {"data_dir": str(out), "sft_data_sha256": digest, "counts": manifest["counts"],
                       "labels": manifest["labels"]["kind"]},
            "base": {}, "model_files": {}, "lease": [], "data": [{"sft_data_sha256": digest}]}


def _stage_s(args, cfg) -> dict:
    from r1.c3.train import sft as SFT
    from r1.c3.train import sft_data as SD
    from r1.c3.train.model import new_head_parameters, token_row_parameters
    if not args.data:
        raise R.TrackPStop(f"{args.cmd} needs --data (an sft-data directory)")
    if args.lr is None:
        raise R.TrackPStop(f"{args.cmd} needs --lr (one value of the grid; R1-LR-GRID)")
    sft_cfg = _sft_config(args)
    train, val, val_seen, dm = SD.load_sft_data(args.data, secondary=True)
    host = cfg.get("sft") or {}
    same = {"effective_batch": "effective_batch", "max_epochs": "max_epochs", "warmup_frac": "warmup_frac",
            "eval_every_frac": "eval_every_frac", "patience": "patience", "seeds": "seeds"}
    for key, value in host.items():   # one source of truth: the host config may set the micro-batch only
        if key in ("micro_batch", "comment"):
            continue
        if key not in same or sft_cfg["train"].get(same[key]) != value:
            raise R.TrackPStop(f"host config sft.{key} = {value!r} disagrees with {args.sft_config} "
                               f"(train.{same.get(key, key)} = {sft_cfg['train'].get(same.get(key, key))!r})")
    protocol = {**{k: v for k, v in sft_cfg["train"].items() if k != "comment"},
                "micro_batch": int(host.get("micro_batch", sft_cfg["train"]["micro_batch"]))}
    if args.tiny:
        protocol["micro_batch"] = sft_cfg["train"]["micro_batch"]
    lease_log: list = []
    with _lease(args, lease_log):
        seed_everything(args.seed)          # before the model exists: LoRA and new-head init follow the seed
        model, tok, make, base = _build(args, cfg)
        if args.p4_gradient_checkpointing:
            model.enable_gradient_checkpointing()
            protocol["gradient_checkpointing"] = True
        heads = new_head_parameters(model) if hasattr(model, "heads") else []
        tokens = token_row_parameters(model)
        data_sha = SD.sha256_file(Path(args.data) / "sft_data.json")
        rep = SFT.run_stage_s(model, train, val, Path(args.run_dir) / "stage_s", protocol, lr=args.lr,
                              seed=args.seed, head_params=heads, token_params=tokens, max_steps=args.steps,
                              eval_every_steps=args.eval_every, data_sha256=data_sha,
                              label_status=dm["label_status"], val_secondary=val_seen,
                              duplicate_policy=dm["cross_split_duplicates"])
    best = Path(args.run_dir) / "stage_s" / "best" / "record.json"
    files = json.loads(best.read_text()).get("files", {}) if best.is_file() else {}
    rep["data"] = {"dir": str(Path(args.data).resolve()), "sft_data_sha256": SD.sha256_file(Path(args.data) / "sft_data.json"),
                   "label_status": dm["label_status"], "labels": dm["labels"].get("kind")}
    return {"report": rep, "base": base, "model_files": files, "lease": lease_log,
            "data": [{"sft_data_sha256": rep["data"]["sft_data_sha256"], "rows_sha256": dm["rows_sha256"]}]}


def cmd_sft_dev(args, cfg) -> dict:
    """R1-TRACKP-SFT-DEV: one Stage S configuration, ENGINEERING_ONLY (DRYRUN with --tiny)."""
    if _evidence(args) not in SFT_DEV_LABELS:
        raise R.TrackPStop("sft-dev is ENGINEERING_ONLY (R1-TRACKP-SFT-DEV); P.4 evidence runs are a later unit")
    if args.p4_gradient_checkpointing and (args.tiny or args.base not in ("kev-4b", "qwen3.5-4b-base")):
        raise R.TrackPStop("P.4 gradient checkpointing requires kev-4b or qwen3.5-4b-base (R1-P4-4B-CHECKPOINT)")
    return _stage_s(args, cfg)


def cmd_sft_select(args, cfg) -> dict:
    from r1.c3.train import sft as SFT
    if not args.runs:
        raise R.TrackPStop("sft-select needs --runs")
    # local/20261127-02: a missing or unreadable run is a protocol STOP (rc 2) before any read by select_lr, not a
    # FileNotFoundError (rc 1, infrastructure); the placeholder config used to stop earlier and hid this
    bad = []
    for r in args.runs:
        rep_path = Path(r) / "stage_s" / "sft_report.json"
        try:
            if not rep_path.is_file():
                raise OSError("not a file")
            if not isinstance(json.loads(rep_path.read_text(encoding="utf-8")), dict):
                raise ValueError("not a JSON object")
        except (OSError, ValueError) as exc:
            bad.append(f"{rep_path} ({type(exc).__name__}: {exc})")
    if bad:
        raise R.TrackPStop(f"sft-select: run report missing or unreadable: {'; '.join(bad)}")
    rep = SFT.select_lr([Path(r) / "stage_s" for r in args.runs])
    print(f"label status of the compared runs: {rep['label_status']}", file=sys.stderr)
    return {"report": rep, "base": {}, "model_files": {}, "lease": [], "data": [rep]}


def cmd_not_yet(args, cfg) -> dict:
    raise R.TrackPStop(f"{args.cmd}: {NOT_YET[args.cmd]}")


NOT_YET = {
    "sft": "P.4 Stage S evidence runs are not enabled in this unit (R1-TRACKP-SFT-DEV is readiness only): they need "
           "sweep-2 labels, a pinned table, pool tokenizers, a separate verify_evidence_completion record and "
           "docs/r1/authorizations/trackp_p4_<date>.md, checked by a later unit; use sft-dev for ENGINEERING runs",
    "a6": "P.5 (Phase 9) runs only after B.7 passes, with the H.8 amendment and its authorization note",
    "rb": "P.6 (Phase 9) runs only after B.7 passes, with its authorization note",
}


def _sft_errors(fn):
    """Refusals of the SFT commands are STOPs (exit 2), not tracebacks: data-builder and value errors, malformed
    JSON, missing keys, and the loop's own "STOP:" RuntimeErrors (resume with another config, D8, r1_sealed)."""
    def wrapped(args, cfg):
        try:
            return fn(args, cfg)
        except R.TrackPStop:
            raise
        except (ValueError, KeyError) as exc:      # SFTDataError and json.JSONDecodeError are ValueErrors
            raise R.TrackPStop(f"{type(exc).__name__}: {exc}") from exc
        except RuntimeError as exc:
            if str(exc).startswith("STOP"):
                raise R.TrackPStop(str(exc)) from exc
            raise
    wrapped.__doc__ = fn.__doc__
    return wrapped


cmd_sft_data, cmd_sft_dev, cmd_sft_select = (_sft_errors(cmd_sft_data), _sft_errors(cmd_sft_dev),
                                             _sft_errors(cmd_sft_select))
COMMANDS = {"spike": cmd_spike, "toy": cmd_toy, "e0": cmd_e0, "e0-select": cmd_e0_select, "probes": cmd_probes,
            "exam": cmd_exam, "sft-data": cmd_sft_data, "sft-dev": cmd_sft_dev, "sft-select": cmd_sft_select,
            "sft": cmd_not_yet, "a6": cmd_not_yet, "rb": cmd_not_yet}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--config", default=str(DEFAULT_CONFIG))
    ap.add_argument("--check-config", action="store_true")
    ap.add_argument("--allow-placeholders", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    for name in COMMANDS:
        p = sub.add_parser(name)
        p.add_argument("--run-dir", required=name not in ("a6", "rb"))
        p.add_argument("--base", help="a key of config['bases']")
        if name in ("spike", "toy", "e0", "probes", "sft-dev"):
            p.add_argument("--gpu", help="empty GPU to lease, by physical index or UUID")
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
        p.add_argument("--stage", default="final", choices=("screen", "final"),
                       help="e0: lr screen (<= 2,000 steps) or the final run at the selected lr (R1-E0-BUDGET)")
        p.add_argument("--eval-every", type=int)
        p.add_argument("--n-val", type=int)
        p.add_argument("--runs", nargs="+", help="e0-select: the run directories of one grid")
        p.add_argument("--budget", action="store_true", help="probes: A3 v2 (pool budget fractions)")
        p.add_argument("--with-probes", action="store_true", help="e0: run E6 on the trained model")
        p.add_argument("--load", help="probes: a saved adapter+heads directory")
        p.add_argument("--no-measure", action="store_true", help="spike: skip the 1,024-token timing")
        p.add_argument("--results", help="exam: the exam results JSON")
        p.add_argument("--allow-placeholders", action="store_true")
        if name.startswith("sft"):
            p.add_argument("--sft-config", default=str(DEFAULT_SFT_CONFIG))
            p.add_argument("--data", help="sft-dev/sft: an sft-data output directory (<run-dir>/data)")
            p.add_argument("--table", help="sft-data: the c3_features/v3 table directory")
            p.add_argument("--table-pin", default="sweep1_v3",
                           help="sft-data: a key of the SFT config's tables (or 'none' with synthetic labels)")
            p.add_argument("--sweep", help="sft-data: the sweep index (or batch directory) the table was built from")
            p.add_argument("--paper-root", help="sft-data: the paper checkout holding the sweep ledgers")
            p.add_argument("--classification", help="sft-data: the sweep's classification sidecar (sweep 1)")
            p.add_argument("--labels", help="sft-data: an audit's label_block.jsonl, or 'synthetic'")
            p.add_argument("--label-sweep", default="sweep1", choices=("sweep1", "sweep2"))
            p.add_argument("--label-freeze", help="sft-data: the label-table freeze record, when it exists")
            p.add_argument("--tokenizers", default="pool", choices=("pool", "whitespace"))
        if name == "sft-dev":
            p.add_argument("--p4-gradient-checkpointing", action="store_true",
                           help="Enable gradient checkpointing for the two P.4 4B arms")
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
        if args.tiny and args.family == "hashbag" and args.cmd != "sft-dev":
            raise R.TrackPStop("--family hashbag is the SFT dry-run stand-in; it serves sft-dev only")
        if not args.tiny and args.cmd in ("spike", "toy", "e0", "probes", "sft-dev") and not args.base:
            ap.error("--base is required")
        if args.tiny:
            os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
        cfg = R.load_config(args.config, allow_placeholders=allow)
        args.cfg = cfg
        _require_authorization(args)
        if args.cmd == "sft-dev" and _evidence(args) not in SFT_DEV_LABELS:   # before any environment check
            raise R.TrackPStop("sft-dev is ENGINEERING_ONLY (R1-TRACKP-SFT-DEV); P.4 evidence runs are a later unit")
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
