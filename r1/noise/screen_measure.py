#!/usr/bin/env python3
"""Runner of the direct screening measurement R1-SCREEN-MEASURE (tier E): c0, the five E1 single edits and the
two-edit children of ``screen_design`` on every T0 node, each at the 120 fresh joint seeds 3301-3420.

AI-assisted (Claude, subagent, 23 Nov 2026). DRAFT; not signed; not reviewed.
Pre-declaration: ``docs/r1/authorizations/SCREEN_MEASURE_PREDECLARATION_DRAFT_20261123.md``.

Harness path. Every run reuses ``r1.noise.e1_noise_floor`` (imported only when a harness run is made, so ``plan``,
``--stub`` and the tests need no harness): a fresh node copy (``_prepare_node``), the harness
``LocalWorker.run_trial_at_seed`` with an E1 edit proposal (``_edit_proposal``), at train seed = split seed = s.
The harness worker applies one "Change X from A to B" directive per trial (``_parse_change_directive``), so a child
c0 + e_i + e_j is made by writing e_i into the node copy first, with ``r1.c3.features.apply_edit`` (the harness
worker's edit rule, stale-value check included), then passing e_j to the harness as in E1. c0 and the singles run
exactly as in E1. ``e1_noise_floor.py`` itself is not changed.

Modes:
  plan                      the run list (no harness, no run);
  run --stub                synthetic metrics from a Gaussian model (no harness; dry runs and tests only;
                            label ENGINEERING_ONLY);
  run --engineering-smoke   harness runs at the engineering smoke seed 999 only (label ENGINEERING_ONLY), to check
                            that every edit is applied and verified before the review accepts the unit;
  run --evidence            the measurement (label EVIDENCE): only with the signed note, on deepthought, under the
                            conditions of R1-SWEEP2-B2-GO (checked by ``preflight_evidence``).

STOP rules (the run stops submitting, finishes the runs in flight, writes the manifest with the reason and exits 3;
a STOPped run is reported, never resumed or patched): a determinism mismatch (a configuration's repeat at seed 3301
differs from its first run); an edit not applied by the harness, a pre-applied edit not in the node copy, or a
harness-applied edit not read back from the node copy; the harness's E1 edit set differing from the declared one;
more than 1 % of the planned runs failed (no metric or non-finite); a worker-runtime probe mismatch; the deadline.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import shutil
import tempfile
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from r1.harness import REPO
from r1.noise import screen_design as sd

SCHEMA_RUN = "r1_screen_measure_run/v1"
EVIDENCE_OUT_ROOT = "results/r1/screen_measure"
SMOKE_SEED = 999                     # r1/e2e.py engineering smoke seed (a reserved engineering namespace)
FAILURE_STOP_FRACTION = 0.01
DEFAULT_WORKERS = 16                 # R1-B2-GO / the B.2 addenda: 16 workers, at least 10 of 40 cores free
FREE_CORES = 10
HARNESS_COMMIT = "6adf3859de66c4814fcf376eed59880fbd8eeaf7"   # the B.2 audit harness (R1-SWEEP2-B2-GO)
CODE_FILES = ("r1/noise/screen_design.py", "r1/noise/screen_measure.py", "r1/noise/screen_analysis.py",
              "r1/noise/screen_seeds.py", "r1/noise/e1_noise_floor.py")


class RunStop(RuntimeError):
    pass


def _norm(v) -> str:
    v = str(v).strip().strip("\"'")
    return "null" if v.lower() in {"none", "null", "~"} else v


# ---------------------------------------------------------------------------------------------------- plan

def plan(design: dict, seeds=sd.SEED_BLOCK) -> list[dict]:
    """Every run: per configuration one run per seed, plus one repeat at the first seed. Repeats and first-seed runs
    come first, so the determinism check STOPs early."""
    first, rest = [], []
    for node, v in design["nodes"].items():
        for cid, cfg in v["configs"].items():
            edits = [{k: v["edits"][i - 1][k] for k in ("symbol", "old", "new")} for i in cfg["edits"]]
            job = {"node": node, "config": cid, "edits": edits}
            first.append({**job, "condition": "seed", "seed": seeds[0]})
            first.append({**job, "condition": "repeat", "seed": seeds[0]})
            rest += [{**job, "condition": "seed", "seed": s} for s in seeds[1:]]
    return first + rest


# ---------------------------------------------------------------------------------------------------- stub

def stub_covariance(design_node: dict, s: float) -> tuple[list[str], np.ndarray]:
    """Product (symmetric-difference) kernel over the declared edits with the pinned rho_joint, plus a shared share s:
    Sigma = s J + (1 - s) K_w, K_w[a, b] = prod over edits in exactly one of a, b of r_w(e), r_w = max(0, (rho - s)/(1 - s)).
    Under s = 0 every design triple has population partial 0 (the kernel)."""
    ids = list(design_node["configs"])
    rho = [min(float(e["rho_joint"]), 0.99999) for e in design_node["edits"]]
    rw = [max(0.0, (r - s) / (1 - s)) for r in rho]
    sets = [set(design_node["configs"][c]["edits"]) for c in ids]
    n = len(ids)
    K = np.ones((n, n))
    for a in range(n):
        for b in range(n):
            for e in sets[a] ^ sets[b]:
                K[a, b] *= rw[e - 1]
    return ids, s * np.ones((n, n)) + (1 - s) * K


def stub_runner(design: dict, s: float = 0.0, scale: float = 0.01):
    """A deterministic synthetic run function: the value of (node, config, seed) does not depend on run order."""
    chol = {}
    for node, v in design["nodes"].items():
        ids, cov = stub_covariance(v, s)
        chol[node] = (ids, np.linalg.cholesky(cov + 1e-10 * np.eye(len(ids))))

    def run(job: dict, _tmp: str) -> dict:
        ids, L = chol[job["node"]]
        key = int(hashlib.sha256(f"{job['node']}|{job['seed']}".encode()).hexdigest()[:12], 16)
        z = np.random.default_rng(key).normal(size=len(ids))
        k = ids.index(job["config"])
        metric = 0.9 + 0.001 * k + scale * float(L[k] @ z)
        values = {e["symbol"]: e["new"] for e in job["edits"]}
        return {"node": job["node"], "config": job["config"], "condition": job["condition"], "seed": job["seed"],
                "metric": round(metric, 12), "success": True, "failure": None,
                "edit_applied": True if job["edits"] else None,
                "values_before": values, "values_after": values, "wall_seconds": 0.0}
    return run


# ---------------------------------------------------------------------------------------------------- harness run

def _edit_path(node_dir: Path, spec, symbol: str) -> str:
    import re
    hits = [rel for rel in spec.editable_paths
            if re.search(rf"^{re.escape(symbol)}\s*[=:]", (node_dir / rel).read_text(encoding="utf-8"), re.MULTILINE)]
    if len(hits) != 1:
        raise RunStop(f"STOP: {symbol} is assigned in {len(hits)} editable files")
    return hits[0]


def run_one_lineage(job: dict, out_tmp: str, runtime_expected: dict | None = None) -> dict:
    """One isolated harness run of a configuration with 0, 1 or 2 edits (subprocess-safe)."""
    from r1.c3.features import apply_edit
    from r1.noise import e1_noise_floor as e1          # imports the harness

    node, edits, seed = job["node"], job["edits"], int(job["seed"])
    spec = e1.load_registered_node(node, repo_root=e1.HARNESS)
    work = Path(tempfile.mkdtemp(prefix=f"smeas_{node}_{job['config']}_", dir=out_tmp))
    try:
        node_dir = e1._prepare_node(node, work)
        for e in edits[:-1]:                              # pre-applied edits (children only)
            rel = _edit_path(node_dir, spec, e["symbol"])
            text = (node_dir / rel).read_text(encoding="utf-8")
            new = apply_edit({rel: text}, {"path": rel, "symbol": e["symbol"], "old": e["old"], "new": e["new"]})
            (node_dir / rel).write_text(new[rel], encoding="utf-8")
        before = e1.current_values(node_dir, spec)
        for e in edits[:-1]:
            if _norm(before.get(e["symbol"])) != _norm(e["new"]):
                raise RunStop(f"STOP: pre-applied edit {e['symbol']} not in the node copy")
        probe = None
        if runtime_expected is not None:
            from autoresearch.worker.seeds import seed_environment
            from r1.c3.audit import worker_runtime
            probe = worker_runtime(runtime_expected, spec.run_command, seed_environment(seed, seed))
        worker = e1.LocalWorker(node_root=node_dir, artifact_dir=work / "art", timeout_seconds=600)
        last = edits[-1] if edits else None
        t0 = time.perf_counter()
        result = worker.run_trial_at_seed(e1._edit_proposal(spec, last), spec, 1, train_seed=seed, split_seed=seed)
        wall = round(time.perf_counter() - t0, 4)
        after = e1.current_values(node_dir, spec)
        metric = result.parsed_metrics.get(spec.metric_name) if result.success else None
        row = {"node": node, "config": job["config"], "condition": job["condition"], "seed": seed,
               "metric": metric, "success": bool(result.success), "failure": result.failure_message,
               "edit_applied": bool(result.changed_files) if last else None,
               "values_before": before, "values_after": after, "wall_seconds": wall}
        if probe is not None:
            row["_worker_runtime"] = probe
        return row
    finally:
        shutil.rmtree(work, ignore_errors=True)


# ---------------------------------------------------------------------------------------------------- checks

def check_row(row: dict, job: dict, design: dict) -> str | None:
    """The per-run STOP checks; returns a STOP reason or None."""
    if job["edits"]:
        if row["edit_applied"] is not True:
            return f"edit_not_applied {row['node']} {row['config']} seed {row['seed']}"
        intended = {e["symbol"]: _norm(e["new"]) for e in job["edits"]}
        after = {k: _norm(v) for k, v in (row.get("values_after") or {}).items()}
        if any(after.get(k) != v for k, v in intended.items()):
            return f"edit_not_verified {row['node']} {row['config']} seed {row['seed']}"
    return None


def check_edit_sets(design: dict, tmp: str) -> dict:
    """The harness's E1 edit set (``e1_noise_floor.candidate_edits``) must equal the declared one, node by node."""
    from r1.noise import e1_noise_floor as e1
    out = {}
    for node, v in design["nodes"].items():
        spec = e1.load_registered_node(node, repo_root=e1.HARNESS)
        probe = Path(tempfile.mkdtemp(dir=tmp))
        try:
            got = e1.candidate_edits(node, e1._prepare_node(node, probe), spec)
        finally:
            shutil.rmtree(probe, ignore_errors=True)
        want = [{k: e[k] for k in ("symbol", "old", "new")} for e in v["edits"]]
        if got != want:
            raise RunStop(f"STOP: {node}: harness E1 edits {got} differ from the declared {want}")
        out[node] = "equal"
    return out


def _key_block(text: str) -> dict:
    import re
    fields = {}
    for line in text.splitlines():
        m = re.match(r"^([a-z0-9_]+): (.*)$", line)
        if m:
            if m.group(1) in fields:
                raise RunStop(f"STOP: note field {m.group(1)} appears twice")
            fields[m.group(1)] = m.group(2).strip()
    return fields


def code_pins(repo: Path = REPO) -> dict:
    return {rel: sd.sha256_file(Path(repo) / rel) for rel in CODE_FILES}


def preflight_evidence(args, design: dict) -> dict:
    """Every precondition of the authorization note that code can check (R1-SWEEP2-B2-GO conditions included)."""
    import subprocess
    from r1.c3 import audit
    from r1.noise import screen_seeds
    root = Path(args.paper_root).resolve()
    note_rel = args.note
    if not note_rel or Path(note_rel).is_absolute() or not note_rel.startswith("docs/r1/authorizations/"):
        raise RunStop("STOP: --note must be a repository-relative path under docs/r1/authorizations/")
    published = subprocess.run(["git", "-C", str(root), "show", f"origin/main:{note_rel}"], capture_output=True)
    if published.returncode or published.stdout != (root / note_rel).read_bytes():
        raise RunStop("STOP: the note is not byte-identical on origin/main (B1 (a))")
    note = _key_block(published.stdout.decode("utf-8"))
    if any("<" in v for v in note.values()):
        raise RunStop("STOP: a note field still holds a placeholder")
    want = {"approved": "true", "label": "EVIDENCE", "run_id": sd.RUN_ID, "design_sha256": sd.design_sha256(design),
            "seed_block": "3301-3420", "harness_commit": HARNESS_COMMIT, "code_commit": args.code_commit,
            "code_review": args.code_review}
    want.update({f"sha256_{Path(k).stem}": v for k, v in code_pins(root).items()})
    bad = sorted(k for k, v in want.items() if note.get(k) != v)
    if bad:
        raise RunStop(f"STOP: note fields differ from the run: {bad}")
    pre = note.get("predeclaration", "")
    pre_path, _, pre_sha = pre.partition(" sha256 ")
    if not pre_path or sd.sha256_file(root / pre_path.strip()) != pre_sha.strip():
        raise RunStop("STOP: the pre-declaration's sha256 differs from the note's")
    provenance = audit.evidence_paper_provenance(root, args.code_commit, args.code_review)
    environment = audit.evidence_environment(root)               # B6 (a), B4 (a) basis, host, harness 6adf3859
    equivalence = audit.sweep2_harness_equivalence(Path(os.environ["AR_HARNESS_ROOT"]))
    seeds = screen_seeds.check_block(sd.SEED_BLOCK)
    load = os.getloadavg()[0]
    cpus = os.cpu_count() or 0
    if cpus - load < args.workers + FREE_CORES:
        raise RunStop(f"STOP: {cpus} cores, load {load:.1f}: fewer than {args.workers} + {FREE_CORES} free")
    return {"note": note_rel, "provenance": provenance, "environment": environment, "harness_equivalence": equivalence,
            "seed_check": seeds, "cores": cpus, "load_at_start": load}


# ---------------------------------------------------------------------------------------------------- execute

def execute(out: Path, jobs: list[dict], run_fn, design: dict, manifest: dict, workers: int, deadline: float,
            tmp: str, in_process: bool = False) -> dict:
    planned = len(jobs)
    failures, stop, written = 0, None, 0
    first = {}
    repeat_seeds = {(j["node"], j["config"], j["seed"]) for j in jobs if j["condition"] == "repeat"}
    t0 = time.time()

    def handle(row: dict, job: dict) -> str | None:
        nonlocal failures
        ok = row["success"] and row["metric"] is not None and math.isfinite(float(row["metric"]))
        if not ok:
            failures += 1
            if failures > FAILURE_STOP_FRACTION * planned:
                return f"failure_rate {failures} of {planned} planned runs"
            return None
        reason = check_row(row, job, design)
        if reason:
            return reason
        key = (row["node"], row["config"], row["seed"])
        if key in repeat_seeds:                       # the repeat and the first run at the repeat seed must agree
            if key in first and first[key] != float(row["metric"]):
                return f"determinism {row['node']} {row['config']} seed {row['seed']}"
            first[key] = float(row["metric"])
        return None

    with open(out / "runs.jsonl", "a", encoding="utf-8") as fh:
        def write(row):
            nonlocal written
            probe = row.pop("_worker_runtime", None)
            if probe is not None:
                with open(out / "worker_runtime.jsonl", "a", encoding="utf-8") as pf:
                    pf.write(json.dumps({"node": row["node"], "config": row["config"], "seed": row["seed"],
                                         "condition": row["condition"], **probe}) + "\n")
            fh.write(json.dumps(row, sort_keys=True) + "\n")
            fh.flush()
            written += 1

        if in_process:
            for job in jobs:
                if time.time() - t0 > deadline:
                    stop = "deadline"
                    break
                row = run_fn(job, tmp)
                write(row)
                stop = handle(row, job)
                if stop:
                    break
        else:
            queue = list(jobs)
            with ProcessPoolExecutor(max_workers=workers) as pool:
                pending = {}
                while queue or pending:
                    while stop is None and queue and len(pending) < workers:
                        if time.time() - t0 > deadline:
                            stop = "deadline"
                            break
                        job = queue.pop(0)
                        pending[pool.submit(run_fn, job, tmp)] = job
                    if not pending:
                        break
                    done, _ = wait(list(pending), return_when=FIRST_COMPLETED, timeout=5)
                    for fut in done:
                        job = pending.pop(fut)
                        try:
                            row = fut.result()
                        except Exception as exc:  # noqa: BLE001 - every exception in a run is a STOP, recorded
                            stop = stop or f"run_exception {job['node']} {job['config']} {job['seed']}: {exc}"
                            continue
                        write(row)
                        stop = stop or handle(row, job)
    manifest.update({"finished_utc": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
                     "planned_runs": planned, "written_runs": written, "failed_runs": failures, "stop": stop,
                     "elapsed_seconds": round(time.time() - t0, 1)})
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--out", required=True)
    r = sub.add_parser("run")
    mode = r.add_mutually_exclusive_group(required=True)
    mode.add_argument("--stub", action="store_true")
    mode.add_argument("--engineering-smoke", action="store_true")
    mode.add_argument("--evidence", action="store_true")
    r.add_argument("--out", required=True)
    r.add_argument("--stub-shared", type=float, default=0.0, help="stub only: shared share s of the synthetic model")
    r.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    r.add_argument("--deadline", type=float, default=21600.0)
    r.add_argument("--tmp", default=os.environ.get("R1_TMP", tempfile.gettempdir()))
    r.add_argument("--paper-root", default=str(REPO))
    r.add_argument("--note", default=None)
    r.add_argument("--code-commit", default=None)
    r.add_argument("--code-review", default=None)
    args = ap.parse_args(argv)

    design = sd.build_design()
    if args.cmd == "plan":
        jobs = plan(design)
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"design_sha256": sd.design_sha256(design), "n_runs": len(jobs),
                                              "runs": jobs}, sort_keys=True) + "\n")
        print(json.dumps({"n_runs": len(jobs), "design_sha256": sd.design_sha256(design)}))
        return 0

    out = Path(args.out)
    if out.exists():
        raise SystemExit("STOP: the output directory exists (a run is never resumed)")
    if args.evidence and not str(out.resolve()).startswith(str((Path(args.paper_root) / EVIDENCE_OUT_ROOT).resolve())):
        raise SystemExit(f"STOP: evidence output goes under {EVIDENCE_OUT_ROOT}/")
    if not args.evidence and str(out.resolve()).startswith(str((REPO / EVIDENCE_OUT_ROOT).resolve())):
        raise SystemExit(f"STOP: {EVIDENCE_OUT_ROOT}/ holds evidence runs only")
    Path(args.tmp).mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    manifest = {"schema": SCHEMA_RUN, "run_id": sd.RUN_ID, "design_sha256": sd.design_sha256(design),
                "seeds": list(sd.SEED_BLOCK), "started_utc": stamp, "stub": bool(args.stub),
                "label": "EVIDENCE" if args.evidence else "ENGINEERING_ONLY",
                "host": {"node": platform.node(), "platform": platform.platform(), "python": platform.python_version(),
                         "cpus": os.cpu_count()},
                "code_sha256": code_pins(REPO), "workers": args.workers}
    runtime_expected = None
    if args.stub:
        jobs, run_fn = plan(design), stub_runner(design, s=args.stub_shared)
        manifest["stub_shared"] = args.stub_shared
        manifest["note"] = "Synthetic metrics (no harness); ENGINEERING_ONLY; never a result."
    else:
        from r1.harness import harness_commit
        from r1.noise import e1_noise_floor as e1
        if args.evidence:                             # the note and the environment before anything else
            pre = preflight_evidence(args, design)
            manifest["preflight"] = pre
        manifest["harness"] = {"root": str(e1.HARNESS), **harness_commit(e1.HARNESS)}
        manifest["libraries"] = e1.library_versions()
        manifest["edit_sets"] = check_edit_sets(design, args.tmp)
        if args.evidence:
            runtime_expected = {k: pre["environment"][k] for k in
                                ("worker_python", "worker_prefix", "worker_versions", "package_list_sha256")}
            jobs = plan(design)
        else:
            jobs = plan(design, seeds=(SMOKE_SEED,))
            manifest["seeds_smoke"] = [SMOKE_SEED]
            manifest["note"] = "Engineering smoke at seed 999: edits applied and verified; never a result."
        import functools
        run_fn = functools.partial(_run_with_runtime, runtime_expected=runtime_expected)
    out.mkdir(parents=True)
    (out / "design.json").write_text(json.dumps(design, indent=1, sort_keys=True) + "\n")
    res = execute(out, jobs, run_fn, design, manifest, args.workers, args.deadline, args.tmp, in_process=args.stub)
    print(json.dumps({k: res[k] for k in ("label", "planned_runs", "written_runs", "failed_runs", "stop",
                                          "elapsed_seconds")}))
    return 3 if res["stop"] else 0


def _run_with_runtime(job: dict, tmp: str, runtime_expected: dict | None = None) -> dict:
    return run_one_lineage(job, tmp, runtime_expected)


if __name__ == "__main__":
    raise SystemExit(main())
