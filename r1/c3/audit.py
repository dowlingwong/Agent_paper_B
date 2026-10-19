"""Fresh-seed audits of proposals on CPU (C3_DESIGN §4). ENGINEERING_ONLY; AI-assisted (Claude).

A proposal is audited by running its candidate and its incumbent configuration
on K common fresh *joint* seeds (train seed = split seed = s, as E1's ``joint``
condition and the E1b leaf audits do), giving per-seed paired differences,
Delta_audit = mean and se = sd / sqrt(K). Default seeds 7001..7006 are disjoint
from campaign seeds (100..280), E1 seeds (1001+, 2001+, 3001+) and the E1b leaf
audit seeds (5001..5006).

Each configuration is run through the harness ``LocalWorker.run_trial_at_seed``
with a no-edit proposal on an isolated copy of the node whose editable files are
overwritten with the configuration's texts: the mechanism of
``r1.headroom.e1b_collect._audit`` / ``r1.noise.e1_noise_floor.run_one``.

Cache: ``runs.jsonl`` rows keyed by (node, config hash, seed); every run is
written as soon as it finishes, so an interrupted call resumes where it stopped.

CLI (time-boxed, resumable):
  python -m r1.c3.audit run --plan DIR/plan.jsonl --configs DIR/configs.json --out DIR \
      --workers 4 --deadline 150
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from pathlib import Path

import numpy as np

DEFAULT_SEEDS = tuple(range(7001, 7007))
PILOT_DATA_CACHE = "experiments/r1/pilot/L8_20261009T152916Z/nodes/{node}/data_cache"


def run_config(node: str, files: dict[str, str], seeds: list[int], tmp: str) -> list[dict]:
    """Run one configuration at the given joint seeds (subprocess-safe)."""
    from r1.harness import import_harness
    harness = import_harness()
    from autoresearch.manager.base import ManagerProposal
    from autoresearch.nodes.registry import load_registered_node
    from autoresearch.worker.local_worker import LocalWorker

    spec = load_registered_node(node, repo_root=harness)
    work = Path(tempfile.mkdtemp(prefix=f"c3a_{node}_", dir=tmp))
    out = []
    try:
        node_dir = work / node
        shutil.copytree(harness / "nodes" / node, node_dir,
                        ignore=shutil.ignore_patterns("__pycache__", ".autoresearch_artifacts"))
        if node.startswith("openml_") and not (node_dir / "data_cache").exists():
            cache = harness / PILOT_DATA_CACHE.format(node=node)
            if cache.exists():
                shutil.copytree(cache, node_dir / "data_cache")
        for rel, text in files.items():
            if rel not in spec.editable_paths:
                raise ValueError(f"{rel} is not editable on {node}")
            (node_dir / rel).write_text(text, encoding="utf-8")
        worker = LocalWorker(node_root=node_dir, artifact_dir=work / "art", timeout_seconds=600)
        noedit = ManagerProposal(manager_mode="c3_audit", proposal_summary="audit", proposal_rationale="",
                                 target_files=spec.editable_paths, objective="Audit run; no change.")
        for i, s in enumerate(seeds):
            t0 = time.perf_counter()
            res = worker.run_trial_at_seed(noedit, spec, i + 1, train_seed=s, split_seed=s)
            out.append({"seed": s, "success": bool(res.success), "failure": res.failure_message,
                        "metric": res.parsed_metrics.get(spec.metric_name) if res.success else None,
                        "changed_files": bool(res.changed_files),
                        "wall_seconds": round(time.perf_counter() - t0, 4)})
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return out


class RunCache:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.rows: dict[tuple, dict] = {}
        if self.path.exists():
            for line in self.path.read_text().splitlines():
                if line.strip():
                    r = json.loads(line)
                    self.rows[(r["node"], r["config_hash"], int(r["seed"]))] = r

    def get(self, node, h, seed):
        return self.rows.get((node, h, int(seed)))

    def add(self, rows: list[dict]):
        with open(self.path, "a", encoding="utf-8") as fh:
            for r in rows:
                self.rows[(r["node"], r["config_hash"], int(r["seed"]))] = r
                fh.write(json.dumps(r) + "\n")


def paired(cand: list[float | None], inc: list[float | None]) -> dict:
    """Delta_audit and se from per-seed metrics (failed seeds dropped pairwise)."""
    d = [c - i for c, i in zip(cand, inc) if c is not None and i is not None]
    if not d:
        return {"delta_audit": None, "se": None, "k": 0}
    d = np.asarray(d, float)
    se = float(d.std(ddof=1) / np.sqrt(len(d))) if len(d) > 1 else None
    return {"delta_audit": float(d.mean()), "se": se, "k": int(len(d)), "sd": float(d.std(ddof=1)) if len(d) > 1 else None}


def audit_results(plan: list[dict], cache: RunCache, seeds=DEFAULT_SEEDS) -> list[dict]:
    """Assemble per-proposal audit results for plan rows whose runs are all cached."""
    out = []
    for p in plan:
        rc = [cache.get(p["node"], p["candidate_hash"], s) for s in seeds]
        ri = [cache.get(p["node"], p["incumbent_hash"], s) for s in seeds]
        if any(r is None for r in rc + ri):
            continue
        cm, im = [r["metric"] for r in rc], [r["metric"] for r in ri]
        out.append({"proposal_id": p["proposal_id"], "node": p["node"], "reason": p.get("reason"),
                    "candidate_hash": p["candidate_hash"], "incumbent_hash": p["incumbent_hash"],
                    "seeds": list(seeds), "candidate_metrics": cm, "incumbent_metrics": im,
                    "wall_seconds": sum(r["wall_seconds"] for r in rc + ri), **paired(cm, im)})
    return out


def run_plan(plan: list[dict], configs: dict, out: Path, seeds=DEFAULT_SEEDS, workers: int = 4,
             deadline: float = 150.0, tmp: str | None = None) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    cache = RunCache(out / "runs.jsonl")
    tmp = tmp or tempfile.mkdtemp(prefix="c3_audit_tmp_")
    Path(tmp).mkdir(parents=True, exist_ok=True)
    jobs, queued = [], set()
    for p in plan:
        for h in (p["candidate_hash"], p["incumbent_hash"]):
            missing = [s for s in seeds if cache.get(p["node"], h, s) is None]
            if missing and (p["node"], h) not in queued:
                queued.add((p["node"], h))
                jobs.append((p["node"], h, missing))
    t0, done = time.time(), 0
    with ProcessPoolExecutor(max_workers=workers) as pool:
        pending = {}
        while (jobs or pending):
            while jobs and len(pending) < workers and time.time() - t0 < deadline:
                node, h, missing = jobs.pop(0)
                fut = pool.submit(run_config, node, configs[h]["files"], missing, tmp)
                pending[fut] = (node, h)
            if not pending:
                break
            finished, _ = wait(list(pending), return_when=FIRST_COMPLETED, timeout=5)
            for fut in finished:
                node, h = pending.pop(fut)
                rows = [{"node": node, "config_hash": h, **r} for r in fut.result()]
                cache.add(rows)
                done += 1
    shutil.rmtree(tmp, ignore_errors=True)
    results = audit_results(plan, cache, seeds)
    return {"configs_run_this_call": done, "configs_remaining": len(jobs),
            "proposals_complete": len(results), "proposals_planned": len(plan),
            "elapsed_seconds": round(time.time() - t0, 1)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--plan", required=True)
    r.add_argument("--configs", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2)))
    r.add_argument("--deadline", type=float, default=150.0)
    r.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_SEEDS))
    c = sub.add_parser("collect")
    c.add_argument("--plan", required=True)
    c.add_argument("--out", required=True)
    c.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_SEEDS))
    args = ap.parse_args(argv)
    plan = [json.loads(x) for x in Path(args.plan).read_text().splitlines() if x.strip()]
    if args.cmd == "run":
        configs = json.loads(Path(args.configs).read_text())
        status = run_plan(plan, configs, Path(args.out), tuple(args.seeds), args.workers, args.deadline)
        print(json.dumps(status))
    else:
        res = audit_results(plan, RunCache(Path(args.out) / "runs.jsonl"), tuple(args.seeds))
        (Path(args.out) / "audits.jsonl").write_text("".join(json.dumps(x) + "\n" for x in res))
        print(json.dumps({"audited": len(res), "planned": len(plan)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
