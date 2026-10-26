"""Track P command line (RUNBOOK Track P 1.6). ENGINEERING_ONLY; AI-assisted (Claude).

Subcommands: ``spike`` (P.0), ``toy`` (P.1/P.2 toy batch), ``e0`` and ``probes`` (P.3a), ``exam`` (P.3b analysis
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

DEFAULT_CONFIG = REPO / "r1" / "scripts" / "configs" / "trackp_portal.json"
PHASE_OF = {"e0": "p3a", "probes": "p3a", "exam": "p3b", "sft": "p4", "a6": "p5", "rb": "p6"}


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
                     lock_path=Path(os.path.expanduser(args.cfg["gpu"]["lock_path"]))) as lease:
        yield lease


def cmd_spike(args, cfg) -> dict:
    from r1.c3.train import spike as S
    lease_log: list = []
    with _lease(args, lease_log):
        model, tok, make, base = _build(args, cfg)
        sp = cfg["spike"]
        rep = S.spike(model, args.run_dir, tok=tok, toy_examples=args.examples or sp["toy_examples"],
                      steps=args.steps or sp["steps"], batch_size=sp["batch_size"], seed=args.seed,
                      measure=not args.no_measure, rebuild=make)
    return {"report": rep, "base": base, "model_files": rep["saved_sha256"], "lease": lease_log,
            "data": S.toy_rows(args.examples or sp["toy_examples"])}


def cmd_toy(args, cfg) -> dict:
    from r1.c3.train import spike as S
    from r1.c3.train.trainer import Trainer, TrainConfig, seed_everything
    lease_log: list = []
    tb = cfg["toy_batch"]
    with _lease(args, lease_log):
        model, tok, make, base = _build(args, cfg)
        seed_everything(args.seed)
        rows = S.toy_rows(args.examples or tb["examples"], offset=100)
        steps = args.steps or tb["steps"]
        tr = Trainer(model, rows, S.sft_loss, TrainConfig(seed=args.seed, epochs=1e9, max_steps=steps, batch_size=8,
                                                          grad_accum=1), Path(args.run_dir) / "toy")
        res = tr.train()
        losses = [r["loss"] for r in S._read_metrics(Path(args.run_dir) / "toy")]
        batch = [r["prompt"] for r in rows[:8]]
        b0, a0 = S.probs(model, batch)
        rec = model.save(Path(args.run_dir) / "saved")
        fresh = make()
        fresh.load(Path(args.run_dir) / "saved")
        b1, a1 = S.probs(fresh, batch)
    import torch
    rep = {**res, "loss_first": losses[0], "loss_last": losses[-1], "loss_decreased": losses[-1] < losses[0],
           "reload_identical": bool(torch.equal(b0, b1) and (a0 is None or torch.equal(a0, a1)))}
    return {"report": rep, "base": base, "model_files": rec["files"], "lease": lease_log, "data": rows}


def cmd_e0(args, cfg) -> dict:
    from r1.c3.train import exam_run as X
    lease_log: list = []
    e0c = cfg["e0"]
    with _lease(args, lease_log):
        model, tok, make, base = _build(args, cfg)
        rep = X.e0(model, args.run_dir, target="y_hard" if args.hard else "y_soft",
                   head_steps=args.steps or e0c["head_fit_steps"], lora_steps=args.steps or e0c["lora_steps"],
                   seed=args.seed, n_train=args.examples, n_test=args.n_test)
        files = model.save(Path(args.run_dir) / "saved")["files"]
        if args.with_probes:
            rep["probes"] = X.probes(model, Path(args.run_dir) / "probes", n=args.n_probe)
    from r1.c3.train import exam_synthetic as E
    return {"report": rep, "base": base, "model_files": files, "lease": lease_log,
            "data": [{"e0_sha256": E.E0_SHA.read_text().split()[0]}]}


def cmd_probes(args, cfg) -> dict:
    from r1.c3.train import exam_run as X
    lease_log: list = []
    with _lease(args, lease_log):
        model, tok, make, base = _build(args, cfg)
        if args.load:
            model.load(Path(args.load))
        rep = X.probes(model, args.run_dir, n=args.n_probe)
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
COMMANDS = {"spike": cmd_spike, "toy": cmd_toy, "e0": cmd_e0, "probes": cmd_probes, "exam": cmd_exam,
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
        p.add_argument("--head-form", default="softmax12", choices=("softmax12", "cumulative11"))
        p.add_argument("--evidence", default="ENGINEERING_ONLY", choices=R.EVIDENCE_LABELS)
        p.add_argument("--seed", type=int, default=0)
        p.add_argument("--steps", type=int)
        p.add_argument("--examples", type=int)
        p.add_argument("--n-test", type=int)
        p.add_argument("--n-probe", type=int, default=32)
        p.add_argument("--hard", action="store_true", help="e0: hard-label contrast run")
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
