"""D.3 per-arm ENGINEERING smoke on one GPU host (task ``compute/20261127-27``).

ENGINEERING_ONLY.  This driver runs one campaign per D.3a arm on one reserved
smoke instance seed, with the real G1 adapter (node spec, ``gemma4_31b``
manager and worker), the real G1 snapshot/record writers and the real G6 audit
code path.  It never writes an outcome table and never reads a label,
evaluation or test partition.

Two limits are deliberate and are reported rather than worked around:

* ``campaign_chunk.ChunkSpec.from_launch`` binds a *deployment* chunk to 18
  instance seeds (6201-6218).  A smoke has one instance per arm; the frozen
  design gives it the reserved smoke seed 6301.  The chunk core is seed-
  agnostic, so this driver constructs a ``ChunkSpec`` directly and calls the
  same ``run_chunk`` the launchers call.  ``run_smoke`` refuses any seed other
  than 6301/6302.
* The signed D.3 pre-declaration fixes the engineering smoke to
  ``openml_climate`` and says it is never audited for Y, while task
  ``compute/20261127-27`` asks for one instance per arm and a G6 audit.  This
  driver therefore labels every output ``ENGINEERING_ONLY`` and records the
  design deviation in ``smoke.json``; the G6 output is an engineering check of
  the audit machinery, never a Y row for an outcome table, and the G7 table
  step refuses rather than fabricate a table the pinned analysis cannot accept.

Commands::

    AR_HARNESS_ROOT=<9bb41680 checkout> python -m r1.scripts.d3_smoke_engineering \
        run   --manifest M --observed O --out OUT --repo-root . --node digits_mlp
    ... audit --out OUT --sigma-node S --harness-root H
    ... table --out OUT --predeclaration P

``--harness-root`` is passed to the G1 factories; the top-level harness import
reads ``AR_HARNESS_ROOT``, so set it in the environment as above.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Mapping

from r1.c3.d3 import adapter as A
from r1.c3.d3 import assemble as AS
from r1.c3.d3.audit import AuditStop, Cache, audit_chunk, harness_runner
from r1.c3.d3.campaign_chunk import ChunkSpec, ChunkStop, _sample_compute_apps, run_chunk
from r1.harness import harness_commit

DESIGN_NODE = "openml_climate"          # the design's smoke node
SMOKE_NODE = "digits_mlp"               # this host has no OpenML cache; deviation recorded
ENGINEERING_NODES = ("openml_climate", "digits_mlp")
SMOKE_SEEDS = (6301, 6302)
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
    if int(seed) not in SMOKE_SEEDS:
        raise A.AdapterStop(f"the engineering smoke uses only seeds {SMOKE_SEEDS}, not {seed}")
    if node not in ENGINEERING_NODES:
        raise A.AdapterStop(f"the engineering smoke uses only {ENGINEERING_NODES}, not {node!r}")
    source = dict(manifest.raw["campaign_model_source"])
    return ChunkSpec(
        stage="a", arm=arm, node=node, repetition=0, instance_seeds=(int(seed),),
        W=A.W, llm_cap=A.LLM_CAP, launcher="direct",
        host=str(observed.get("host") or "TASL-2"),
        campaign_model_source=source,
        notes={"engineering_only": True, "task": "compute/20261127-27", "run_id": run_id,
               "smoke_seed": int(seed), "smoke_arms": list(SMOKE_ARMS),
               "design_node": DESIGN_NODE,
               "design_deviation": None if node == DESIGN_NODE else f"ran on {node}, not {DESIGN_NODE}"},
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
    A.load_manifest(payload, repo_root=root, check_files=True)
    _write_json(out, payload)
    return payload



def _verify_record(path: str | Path) -> dict[str, Any]:
    """Read a record written by ``_write_json`` and verify its self-hash."""
    payload = _read_json(path)
    claimed = payload.pop("record_sha256", None)
    text = json.dumps(payload, indent=1, sort_keys=True, allow_nan=False, default=str) + "\n"
    actual = hashlib.sha256(text.encode()).hexdigest()
    if claimed != actual:
        raise AuditStop(f"{path}: record_sha256 {claimed!r} does not hash the record ({actual})")
    return payload


def _validate_smoke(root: Path) -> dict[str, Any]:
    """Refuse a stale/edited smoke record or any campaign that is not the reserved smoke seed."""
    record = _verify_record(root / "smoke.json")
    if record.get("engineering_only") is not True:
        raise AuditStop("the smoke record is not labelled engineering_only")
    if int(record.get("seed", -1)) not in SMOKE_SEEDS:
        raise AuditStop(f"the smoke record seed {record.get('seed')!r} is not a smoke seed")
    if str(record.get("node")) not in ENGINEERING_NODES:
        raise AuditStop(f"the smoke record node {record.get('node')!r} is not an engineering node")
    if str(record.get("stage")) != "a":
        raise AuditStop("the smoke record is not stage a")
    sigma = record.get("sigma_node")
    if sigma is not None and not float(sigma) > 0:
        raise AuditStop("the smoke record's sigma_node is not positive")
    for arm, chunk_dir in sorted((record.get("chunks") or {}).items()):
        chunk = Path(chunk_dir)
        chunk_record = _read_json(chunk / "chunk.json")
        if chunk_record.get("stage") != "a" or chunk_record.get("arm") != arm:
            raise AuditStop(f"{chunk}: chunk stage/arm differ from smoke.json")
        if chunk_record.get("node") != record["node"] or int(chunk_record.get("W", -1)) != A.W or \
                int(chunk_record.get("llm_cap", -1)) != A.LLM_CAP:
            raise AuditStop(f"{chunk}: chunk node/W/LLM cap differ from the smoke declaration")
        if (chunk_record.get("notes") or {}).get("engineering_only") is not True:
            raise AuditStop(f"{chunk}: chunk is not labelled engineering_only")
        wanted = f"{record['node']}__s{int(record['seed'])}"
        if chunk_record.get("instances") != [wanted]:
            raise AuditStop(f"{chunk}: chunk instances {chunk_record.get('instances')!r} are not [{wanted!r}]")
        for camp in sorted((chunk / "campaigns").glob("*/campaign.json")):
            payload = _read_json(camp)
            if payload.get("stage") != "a" or payload.get("arm") != arm:
                raise AuditStop(f"{camp}: campaign stage/arm differ from smoke.json")
            if payload.get("node") != record["node"] or int(payload.get("instance_seed", -1)) not in SMOKE_SEEDS:
                raise AuditStop(f"{camp}: campaign node/seed are not the reserved smoke values")
    return record

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
    actual = harness_commit(Path(harness_root)) if harness_root else harness_commit()
    A.check_harness(manifest, actual)
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
        "sigma_node": float(constants.noise[node]["sigma_node"]),
        "harness_commit": manifest.harness_commit,
        "harness_actual": actual,
        "design_node": DESIGN_NODE,
        "design_deviation": None if node == DESIGN_NODE else f"ran on {node}, not {DESIGN_NODE}",
        "design_note": ("The signed smoke fixes openml_climate and says it is never audited for Y; "
                        "the task card asks for one instance per arm and a G6 audit. Every output here "
                        "is ENGINEERING_ONLY and is not evidence."),
    }
    record["record_sha256"] = _write_json(root / "smoke.json", record)
    return record


def _expected_worker() -> dict[str, Any]:
    """The worker identity G6's append guard requires, from the same ``python3`` it probes."""
    command = shutil.which("python3", path=os.environ.get("PATH"))
    if not command:
        raise AuditStop("python3 is not on PATH for the audit worker")
    code = """import hashlib, importlib.metadata as m, json, os, sys
p={}
for d in m.distributions():
 n=(d.metadata.get('Name') or '').lower().replace('_','-')
 if not n or n in p: raise ValueError('duplicate or missing package name')
 p[n]=d.version
v={n:m.version(n) for n in ('scikit-learn','numpy','scipy','pandas')}
print(json.dumps({'worker_python':sys.executable,'worker_python_realpath':os.path.realpath(sys.executable),
 'prefix':sys.prefix,'base_prefix':sys.base_prefix,'versions':v,
 'package_list_sha256':hashlib.sha256(json.dumps(p,sort_keys=True,separators=(',',':')).encode()).hexdigest()}))
"""
    try:
        observed = json.loads(subprocess.check_output([command, "-B", "-c", code], text=True, timeout=30))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise AuditStop(f"the audit worker probe failed: {exc}") from exc
    if observed.get("prefix") == observed.get("base_prefix"):
        raise AuditStop("the audit worker runs in a base environment, not a venv")
    return {
        "worker_python": observed["worker_python"],
        "worker_python_realpath": observed["worker_python_realpath"],
        "worker_prefix": observed["prefix"],
        "worker_versions": observed["versions"],
        "package_list_sha256": observed["package_list_sha256"],
    }

def _audit_one(args: tuple[str, str, float, str, dict[str, Any]]) -> dict[str, Any]:
    chunk_dir, audit_dir, sigma, harness_root, expected = args
    if harness_root:
        os.environ["AR_HARNESS_ROOT"] = harness_root
    tmp = Path(audit_dir) / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    cache = Cache(Path(audit_dir) / "cache.jsonl")
    try:
        rows = audit_chunk(chunk_dir, audit_dir, sigma_node=sigma,
                           runner=harness_runner(tmp, expected_worker=expected), cache=cache)
    finally:
        for path in tmp.rglob("*"):
            if path.is_file():
                path.unlink()
        for path in sorted(tmp.rglob("*"), reverse=True):
            if path.is_dir():
                path.rmdir()
        tmp.rmdir()
    return {"chunk": chunk_dir, "audit": audit_dir, "campaigns": len(rows)}


def audit_smoke(*, out: str, sigma_node: float | None, harness_root: str | None, jobs: int = 4,
                manifest_path: str | None = None, repo_root: str | None = None) -> dict[str, Any]:
    root = Path(out)
    smoke = _validate_smoke(root)
    if (root / "audits").exists():
        raise AuditStop(f"refusing an existing audit root {root / 'audits'}")
    if smoke.get("sigma_node") is not None:
        declared_sigma = float(smoke["sigma_node"])
        sigma_source = "smoke.json"
    else:
        if not manifest_path:
            raise AuditStop("the smoke record has no sigma_node; pass --manifest to derive it from the constants")
        manifest = A.load_manifest(manifest_path, repo_root=repo_root)
        constants = A.load_constants(manifest, repo_root=repo_root)
        declared_sigma = float(constants.noise[smoke["node"]]["sigma_node"])
        sigma_source = "constants"
    if sigma_node is not None and abs(float(sigma_node) - declared_sigma) > 1e-12:
        raise AuditStop(f"sigma_node {sigma_node} differs from the declared {declared_sigma}")
    if not declared_sigma > 0:
        raise AuditStop("sigma_node must be positive")
    chunks = smoke["chunks"]
    expected = _expected_worker()
    tasks = []
    for arm, chunk_dir in sorted(chunks.items()):
        audit_dir = str(root / "audits" / arm)
        tasks.append((chunk_dir, audit_dir, declared_sigma, harness_root, expected))
    results = []
    with ProcessPoolExecutor(max_workers=max(1, int(jobs))) as pool:
        futures = {pool.submit(_audit_one, task): task for task in tasks}
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda r: r["audit"])
    record = {"schema": "r1_d3_smoke_audit/v1", "engineering_only": True,
              "task": "compute/20261127-27", "results": results,
              "expected_worker": expected, "sigma_node": declared_sigma,
              "sigma_source": sigma_source,
              "note": "Engineering check of the G6 audit path; these rows are not Y evidence and "
                      "never enter an outcome table."}
    record["record_sha256"] = _write_json(root / "audit.json", record)
    return record


def table_check(*, out: str, predeclaration: str, noise_summary: str | None) -> dict[str, Any]:
    """Try G7's row builder on the seven real smoke rows; report, never fabricate, a table."""
    root = Path(out)
    smoke = _validate_smoke(root)
    arms = tuple(smoke["arms"])
    summaries = AS.load_summaries(root / "chunks" / arm for arm in arms)
    audits = AS.load_audits(root / "audits" / arm for arm in arms)
    from r1.c3 import d3_analysis as D3
    from r1.c3 import d3_outcome_table as T
    by = T._audits_by_campaign(audits)
    rows, failures = [], []
    for summary in summaries:
        try:
            cid = T._check_summary(summary, "D.3a")
        except Exception as exc:  # noqa: BLE001 - a refusal is the result, not a table
            failures.append({"campaign_id": None, "arm": summary.get("arm"), "error": str(exc)})
            continue
        try:
            rows.append(T.build_row("D.3a", summary, by.get(cid)))
        except Exception as exc:  # noqa: BLE001 - a refusal is the result, not a table
            failures.append({"campaign_id": cid, "arm": summary.get("arm"), "error": str(exc)})
    if failures:
        record = {"schema": "r1_d3_smoke_table/v1", "engineering_only": True,
                  "status": "REFUSED", "task": "compute/20261127-27",
                  "failures": failures,
                  "reason": ("G7.build_row refused the smoke rows; the first refusal is: "
                             + failures[0]["error"]),
                  "predeclaration": predeclaration,
                  "noise_summary": noise_summary}
        record["record_sha256"] = _write_json(root / "table.json", record)
        return record
    record = {"schema": "r1_d3_smoke_table/v1", "engineering_only": True,
              "status": "ROWS_PASS", "task": "compute/20261127-27", "rows": rows,
              "note": "The seven real smoke rows pass G7.build_row. No stage table is written: the "
                      "pinned analysis requires the full declared design and the signed smoke is not "
                      "an outcome design."}
    record["record_sha256"] = _write_json(root / "table.json", record)
    return record


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
    a.add_argument("--sigma-node", type=float, default=None)
    a.add_argument("--harness-root", default=None)
    a.add_argument("--jobs", type=int, default=4)
    a.add_argument("--manifest", default=None)
    a.add_argument("--repo-root", default=None)
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
    try:
        if args.cmd == "run":
            print(json.dumps(run_smoke(manifest_path=args.manifest, observed_path=args.observed,
                                       out=args.out, harness_root=args.harness_root,
                                       repo_root=args.repo_root, node=args.node, seed=args.seed,
                                       arms=tuple(args.arms), run_id=args.run_id), sort_keys=True))
        elif args.cmd == "audit":
            print(json.dumps(audit_smoke(out=args.out, sigma_node=args.sigma_node,
                                        harness_root=args.harness_root, jobs=args.jobs,
                                        manifest_path=args.manifest, repo_root=args.repo_root), sort_keys=True))
        elif args.cmd == "table":
            print(json.dumps(table_check(out=args.out, predeclaration=args.predeclaration,
                                         noise_summary=args.noise_summary), sort_keys=True))
        else:
            print(json.dumps(write_manifest(out=args.out, campaign_model=args.campaign_model,
                                            proposer_sha256=args.proposer_sha256, base_url=args.base_url,
                                            repo_root=args.repo_root, predeclaration=args.predeclaration,
                                            constants=args.constants, noise=args.noise, split=args.split,
                                            campaign_model_source=args.campaign_model_source), sort_keys=True))
    except (A.AdapterStop, ChunkStop, AuditStop) as exc:
        print(f"STOP: {exc}", flush=True)
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
