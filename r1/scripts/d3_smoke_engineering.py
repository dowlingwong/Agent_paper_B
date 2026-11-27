"""D.3 per-arm ENGINEERING smoke on one GPU host (task ``compute/20261127-27``).

ENGINEERING_ONLY.  This driver runs one campaign per D.3a arm on one instance
seed, with the real G1 adapter (node spec, ``gemma4_31b`` manager and worker),
the real G1 snapshot/record writers and the real G6 audit.  It never writes an
outcome table from the smoke rows and never reads a label, evaluation or test
partition.

Why this is a separate entry point: ``campaign_chunk.ChunkSpec.from_launch``
binds a *deployment* chunk to 18 instance seeds (6201-6218).  A smoke has one
instance per arm; the frozen design gives it the reserved smoke seed 6301.  The
chunk core itself is seed-agnostic, so this driver constructs a ``ChunkSpec``
directly and calls the same ``run_chunk`` the launchers call.  No campaign
logic is duplicated.

The G6 audit seed block for a smoke instance is defined in ``audit.py`` as
6391-6400 (6301) / 6401-6410 (6302); it is a separate block from every
deployment block.  The smoke output is labelled ``ENGINEERING_ONLY`` and is
never an outcome.

Commands::

    python -m r1.scripts.d3_smoke_engineering run   --manifest M --observed O --out OUT ...
    python -m r1.scripts.d3_smoke_engineering audit --out OUT --harness-root H ...
    python -m r1.scripts.d3_smoke_engineering table --out OUT --predeclaration P ...

The ``table`` command first checks the G7 row builder on the seven real
campaigns, then repeats those rows across the declared design only to exercise
the pinned analysis's full-coverage validator (``ENGINEERING_ONLY``; the
repeated rows are labelled as such in the table record and are not evidence).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Mapping

from r1.c3.d3 import adapter as A
from r1.c3.d3 import assemble as AS
from r1.c3.d3.audit import Cache, audit_chunk, harness_runner
from r1.c3.d3.campaign_chunk import ChunkSpec, _sample_compute_apps, run_chunk

SMOKE_NODE = "digits_mlp"
SMOKE_SEED = 6301
SMOKE_ARMS = ("A0", "A0R", "A1", "A2", "FIXR3", "EGATE", "LADDER")
RUN_ID = "d3-smoke-engineering-20261127-a"


def _read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, payload: Mapping[str, Any]) -> str:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=1, sort_keys=True, allow_nan=False, default=str) + "\n"
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)
    return hashlib.sha256(text.encode()).hexdigest()


def _spec(arm: str, *, node: str, seed: int, manifest: A.Manifest, observed: Mapping[str, Any],
          run_id: str) -> ChunkSpec:
    source = dict(manifest.raw["campaign_model_source"])
    return ChunkSpec(
        stage="a", arm=arm, node=node, repetition=0, instance_seeds=(int(seed),),
        W=A.W, llm_cap=A.LLM_CAP, launcher="ssh", host=str(observed.get("host") or "TASL-2"),
        campaign_model_source=source,
        notes={"engineering_only": True, "task": "compute/20261127-27", "run_id": run_id,
               "smoke_seed": int(seed), "smoke_arms": list(SMOKE_ARMS)},
    )


def write_manifest(*, out: str, campaign_model: str, proposer_sha256: str, base_url: str,
                   repo_root: str, predeclaration: str, constants: str, noise: str, split: str,
                   campaign_model_source: str) -> dict[str, Any]:
    root = Path(repo_root)

    def sha(rel: str) -> str:
        return hashlib.sha256((root / rel).read_bytes()).hexdigest()

    payload = {
        "schema": A.SCHEMA, "stage": "a", "campaign_model": campaign_model,
        "campaign_model_source": {"path": campaign_model_source, "sha256": sha(campaign_model_source)},
        "proposer": {"model": "gemma4_31b", "alias": "gemma4_31b", "base_url": base_url,
                     "model_sha256": proposer_sha256, "schema": A.PROPOSAL_SCHEMA,
                     "temperature": A.PROPOSER_TEMPERATURE, "thinking": False},
        "harness_commit": A.HARNESS_PIN,
        "constants": {"path": constants, "sha256": sha(constants)},
        "noise": {"path": noise, "sha256": sha(noise)},
        "predeclaration": {"path": predeclaration, "sha256": sha(predeclaration)},
        "split": {"path": split, "sha256": sha(split)},
        "W": A.W, "llm_cap": A.LLM_CAP, "trial_budget": A.TRIAL_BUDGET,
        "memory_mode": A.MEMORY_MODE, "verify_runs": A.VERIFY_RUNS,
        "verify_seed_base": A.VERIFY_SEED_BASE, "verify_split_policy": A.VERIFY_SPLIT_POLICY,
        "nodes": list(A.D3_NODES), "arms": list(A.D3A_ARMS),
    }
    # Load it before writing: a typo is refused here, not at launch.
    A.load_manifest(payload, repo_root=root, check_files=True)
    _write_json(out, payload)
    return payload


def run_smoke(*, manifest_path: str, observed_path: str, out: str, harness_root: str | None,
              repo_root: str | None, node: str, seed: int, arms: tuple[str, ...],
              run_id: str) -> dict[str, Any]:
    manifest = A.load_manifest(manifest_path, repo_root=repo_root)
    constants = A.load_constants(manifest, repo_root=repo_root)
    observed = _read_json(observed_path)
    if str(observed.get("model") or "") != manifest.campaign_model:
        raise A.AdapterStop(f"observed GPU {observed.get('model')!r} differs from the manifest's "
                            f"{manifest.campaign_model!r}")
    if str(observed.get("proposer_model") or "") != manifest.proposer_model:
        raise A.AdapterStop("observed proposer differs from the manifest")
    if observed.get("memory_check") != "pass" or observed.get("lease") is not True:
        raise A.AdapterStop("the observed record must show memory_check=pass and lease=true")
    root = Path(out)
    if root.exists():
        raise A.AdapterStop(f"refusing an existing smoke root {root}")
    root.mkdir(parents=True)
    chunk_manifest = manifest.chunk_manifest()
    end_sampler = None
    if observed.get("gpu_uuid"):
        end_sampler = lambda: _sample_compute_apps(str(observed["gpu_uuid"]))
    chunks: dict[str, str] = {}
    for arm in arms:
        if arm not in A.ALL_ARMS:
            raise A.AdapterStop(f"unknown arm {arm!r}")
        if arm in A.LEARNED_ARMS:
            raise A.AdapterStop(f"{arm} needs a frozen learned artefact; the smoke refuses it")
        spec = _spec(arm, node=node, seed=seed, manifest=manifest, observed=observed, run_id=run_id)
        chunk_dir = root / "chunks" / arm
        if arm in A.REPLICATE_ARMS:
            factory = A.make_replicate_factory(manifest, constants, harness=harness_root)
            summary = run_chunk(spec, chunk_dir, replicate_factory=factory, manifest=chunk_manifest,
                                observed=observed, end_sampler=end_sampler)
        else:
            factory = A.make_campaign_factory(manifest, constants, harness=harness_root)
            summary = run_chunk(spec, chunk_dir, factory, manifest=chunk_manifest,
                                observed=observed, end_sampler=end_sampler)
        if summary["campaigns"] != 1:
            raise A.AdapterStop(f"{arm}: expected one smoke campaign, got {summary['campaigns']}")
        chunks[arm] = str(chunk_dir)
    record = {
        "schema": "r1_d3_smoke/v1", "engineering_only": True, "task": "compute/20261127-27",
        "run_id": run_id, "stage": "a", "node": node, "seed": int(seed), "arms": list(arms),
        "chunks": chunks, "observed": dict(observed),
        "manifest_sha256": hashlib.sha256(Path(manifest_path).read_bytes()).hexdigest(),
        "harness_commit": manifest.harness_commit,
    }
    record["record_sha256"] = _write_json(root / "smoke.json", record)
    return record


def _audit_one(args: tuple[str, str, float, str, str | None]) -> dict[str, Any]:
    chunk_dir, audit_dir, sigma, harness_root, repo_root = args
    if harness_root:
        os.environ["AR_HARNESS_ROOT"] = harness_root
    tmp = Path(audit_dir) / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    cache = Cache(Path(audit_dir) / "cache.jsonl")
    try:
        rows = audit_chunk(chunk_dir, audit_dir, sigma_node=sigma, runner=harness_runner(tmp), cache=cache)
    finally:
        for path in tmp.rglob("*"):
            if path.is_file():
                path.unlink()
        for path in sorted(tmp.rglob("*"), reverse=True):
            if path.is_dir():
                path.rmdir()
        tmp.rmdir()
    return {"chunk": chunk_dir, "audit": audit_dir, "campaigns": len(rows)}


def audit_smoke(*, out: str, sigma_node: float, harness_root: str | None, repo_root: str | None,
                jobs: int = 7) -> dict[str, Any]:
    root = Path(out)
    smoke = _read_json(root / "smoke.json")
    chunks = smoke["chunks"]
    tasks = []
    for arm, chunk_dir in sorted(chunks.items()):
        audit_dir = str(root / "audits" / arm)
        tasks.append((chunk_dir, audit_dir, float(sigma_node), harness_root, repo_root))
    results = []
    with ProcessPoolExecutor(max_workers=max(1, int(jobs))) as pool:
        futures = {pool.submit(_audit_one, task): task for task in tasks}
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda r: r["audit"])
    record = {"schema": "r1_d3_smoke_audit/v1", "engineering_only": True,
              "task": "compute/20261127-27", "results": results}
    record["record_sha256"] = _write_json(root / "audit.json", record)
    return record


def _g7_rows(root: Path) -> tuple[list[dict], list[dict]]:
    summaries = AS.load_summaries(root / "chunks" / arm for arm in SMOKE_ARMS)
    audits = AS.load_audits(root / "audits" / arm for arm in SMOKE_ARMS)
    from r1.c3 import d3_outcome_table as T
    by = T._audits_by_campaign(audits)
    rows = [T.build_row("D.3a", s, by.get(T._check_summary(s, "D.3a"))) for s in summaries]
    return summaries, rows


def build_table(*, out: str, predeclaration: str, noise_summary: str | None) -> dict[str, Any]:
    root = Path(out)
    summaries, rows = _g7_rows(root)
    # 1) The seven real rows pass G7's per-row builder.
    from r1.c3 import d3_outcome_table as T
    direct = {"schema": "r1_d3_smoke_rows/v1", "engineering_only": True, "rows": rows,
              "row_count": len(rows)}
    _write_json(root / "g7_rows_real.json", direct)
    # 2) The pinned analysis requires the full declared design.  Repeat the seven real
    #    rows across the declared design only to exercise its validator and analysis;
    #    every repeated row is marked engineering_only in the record, never evidence.
    from r1.c3 import d3_analysis as D3
    expanded = []
    for node in D3.NODES:
        for seed in D3.INSTANCE_SEEDS:
            for arm in D3.ARMS_D3A:
                base = next(r for r in rows if r["arm"] == arm)
                r = dict(base)
                r["node"], r["instance_seed"] = node, seed
                r["instance_id"] = D3.instance_id(node, seed)
                r["campaign_id"] = D3.campaign_id("D.3a", arm, node, seed, 0)
                expanded.append(r)
    table = {"schema": D3.SCHEMA, "stage": "D.3a",
             "predeclaration_sha256": hashlib.sha256(Path(predeclaration).read_bytes()).hexdigest(),
             "noise_source_sha256": D3.NOISE_SOURCE_SHA256,
             "sigma_node": _sigma_from(noise_summary), "arms": list(D3.ARMS_D3A),
             "a6_entered": None, "repetitions": D3.REPETITIONS, "rows": expanded}
    D3.validate_table(table, "D.3a")
    T.write_table(table, root / "d3_smoke_exercise_table.json")
    report = D3.analyse(table, d3b_not_run="not_started")
    _write_json(root / "d3_smoke_exercise_report.json", report)
    record = {"schema": "r1_d3_smoke_table/v1", "engineering_only": True,
              "real_rows": len(rows), "expanded_rows": len(expanded),
              "exercise_table": "d3_smoke_exercise_table.json",
              "exercise_report": "d3_smoke_exercise_report.json",
              "note": "The seven real smoke rows are validated by G7.build_row. The expanded "
                      "table repeats those rows across the declared design only so the pinned "
                      "analysis's coverage validator can be exercised; repeated rows are not evidence."}
    record["record_sha256"] = _write_json(root / "table.json", record)
    return record


def _sigma_from(noise_summary: str | None) -> dict[str, float]:
    from r1.c3 import d3_analysis as D3
    from r1.c3.dataset import noise_table
    path = D3.refuse_input_path(Path(noise_summary) if noise_summary else D3.NOISE_SOURCE_PATH)
    table = noise_table(path)
    return {node: float(table[node]["sigma_node"]) for node in D3.NODES}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="D.3 per-arm ENGINEERING smoke")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--manifest", required=True)
    r.add_argument("--observed", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--harness-root", default=None)
    r.add_argument("--repo-root", default=None)
    r.add_argument("--node", default=SMOKE_NODE)
    r.add_argument("--seed", type=int, default=SMOKE_SEED)
    r.add_argument("--arms", nargs="+", default=list(SMOKE_ARMS))
    r.add_argument("--run-id", default=RUN_ID)
    a = sub.add_parser("audit")
    a.add_argument("--out", required=True)
    a.add_argument("--sigma-node", type=float, required=True)
    a.add_argument("--harness-root", default=None)
    a.add_argument("--repo-root", default=None)
    a.add_argument("--jobs", type=int, default=7)
    t = sub.add_parser("table")
    t.add_argument("--out", required=True)
    t.add_argument("--predeclaration", required=True)
    t.add_argument("--noise-summary", default=None)
    m = sub.add_parser("manifest")
    m.add_argument("--out", required=True)
    m.add_argument("--campaign-model", required=True)
    m.add_argument("--proposer-sha256", required=True)
    m.add_argument("--base-url", default="http://127.0.0.1:8095/v1")
    m.add_argument("--repo-root", required=True)
    m.add_argument("--predeclaration",
                   default="docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md")
    m.add_argument("--constants", default="docs/r1/reports/d3_g2_20261127/d3_constants.json")
    m.add_argument("--noise", default="results/r1/noise/D28_REPAIR_20261027/summary.json")
    m.add_argument("--split", default="r1/c3/splits/c3_p3_split_v1.json")
    m.add_argument("--campaign-model-source",
                   default="docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_REV6_LAUNCHERS_20261126.md")
    args = ap.parse_args(argv)
    if args.cmd == "run":
        print(json.dumps(run_smoke(manifest_path=args.manifest, observed_path=args.observed,
                                   out=args.out, harness_root=args.harness_root,
                                   repo_root=args.repo_root, node=args.node, seed=args.seed,
                                   arms=tuple(args.arms), run_id=args.run_id), sort_keys=True))
    elif args.cmd == "audit":
        print(json.dumps(audit_smoke(out=args.out, sigma_node=args.sigma_node,
                                     harness_root=args.harness_root, repo_root=args.repo_root,
                                     jobs=args.jobs), sort_keys=True))
    elif args.cmd == "table":
        print(json.dumps(build_table(out=args.out, predeclaration=args.predeclaration,
                                     noise_summary=args.noise_summary), sort_keys=True))
    else:
        print(json.dumps(write_manifest(out=args.out, campaign_model=args.campaign_model,
                                        proposer_sha256=args.proposer_sha256, base_url=args.base_url,
                                        repo_root=args.repo_root, predeclaration=args.predeclaration,
                                        constants=args.constants, noise=args.noise, split=args.split,
                                        campaign_model_source=args.campaign_model_source), sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
