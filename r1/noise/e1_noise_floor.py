#!/usr/bin/env python3
"""E1 noise-floor and cost pilot (RUNBOOK 0.4; label PILOT, never a result).

For each node it runs the baseline configuration c0 and up to five typical
single edits c1..c5 under three seed conditions:

- ``train``: training seed varied (S seeds), split seed at the node default;
- ``split``: split seed varied (S seeds), training seed at the node default;
- ``joint``: both varied together (S seeds);

plus the baseline twice at the node's default seeds (determinism check).
Every run goes through the harness ``LocalWorker`` on an isolated copy of the
node directory, so edits, seeds and metric parsing are exactly the harness's.

Output: ``results/r1/pilot/E1_<UTC>/`` with ``runs.jsonl``, ``edits.json`` and
``manifest.json``.  The report is produced by ``e1_report.py``.

Usage:
  python -m r1.noise.e1_noise_floor --nodes digits_mlp tabular_mlp --seeds 10 --workers 4
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from r1.harness import REPO, harness_commit, import_harness

HARNESS = import_harness()

from autoresearch.manager.base import ManagerProposal  # noqa: E402
from autoresearch.nodes.registry import load_registered_node  # noqa: E402
from autoresearch.worker.local_worker import LocalWorker  # noqa: E402

DEFAULT_NODES = (
    "digits_mlp", "tabular_mlp", "lr_synthetic", "mlp_synthetic",
    "openml_breast_w", "openml_credit_approval", "openml_diabetes", "openml_ionosphere",
    "openml_wdbc", "openml_credit_g", "mlagentbench_vectorization",
    # D21 pool extension (22 Oct 2026); need their data caches in nodes/<node>/data_cache
    # (see r1/noise/check_caches.py).
    "openml_sonar", "openml_blood_transfusion", "openml_qsar_biodeg",
)
# Nodes whose metric is timing-based or whose edits are not bounded hyperparameters:
# only baseline noise and determinism are measured.
BASELINE_ONLY = {"mlagentbench_vectorization"}
# OpenML hyperparameters that are active for each model type (inactive ones are no-ops).
OPENML_ACTIVE = {
    "logistic_regression": ("C", "max_iter"),
    "random_forest": ("n_estimators", "max_depth"),
    "gradient_boosting": ("n_estimators", "max_depth", "learning_rate"),
}
SEED_BASE = {"train": 1001, "split": 2001, "joint": 3001}
PILOT_DATA_CACHE = "experiments/r1/pilot/L8_20261009T152916Z/nodes/{node}/data_cache"


def library_versions() -> dict[str, str | None]:
    """Versions of the libraries that determine node metrics (PLAN §10, D21 rule, 22 Oct)."""
    from importlib import metadata
    out = {}
    for name in ("scikit-learn", "numpy", "scipy", "pandas"):
        try:
            out[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            out[name] = None
    return out


# ---------------------------------------------------------------------------
# Edits
# ---------------------------------------------------------------------------

def _fmt(value: float, like: str) -> str:
    if re.fullmatch(r"[-+]?\d+", like.strip()):
        return str(int(round(value)))
    return f"{value:.6g}"


def _clip(symbol: str, value: float, spec) -> float:
    ranges = getattr(spec, "allowed_ranges", None) or {}
    lo_hi = ranges.get(symbol)
    if lo_hi:
        value = min(max(value, float(lo_hi[0])), float(lo_hi[1]))
    return value


def current_values(node_dir: Path, spec) -> dict[str, str]:
    values: dict[str, str] = {}
    for rel in spec.editable_paths:
        text = (node_dir / rel).read_text(encoding="utf-8")
        for symbol in spec.editable_symbols:
            m = re.search(rf"^{re.escape(symbol)}\s*[=:]\s*(.+?)\s*$", text, flags=re.MULTILINE)
            if m:
                values[symbol] = m.group(1).strip().strip("'\"")
    return values


def candidate_edits(node: str, node_dir: Path, spec) -> list[dict[str, str]]:
    values = current_values(node_dir, spec)
    numeric, categorical = [], []
    if node.startswith("openml_"):
        # Fixed, interpretable edit set for the OpenML pool: the active
        # regularisation knob at x0.5 / x2, both model-type switches, and the
        # class-weight switch (allowed values are read from the node config).
        raw = json.loads((HARNESS / "configs" / "nodes" / f"{node}.yaml").read_text())
        allowed = raw.get("allowed_values", {})
        edits: list[dict[str, str]] = []
        old_c = values.get("C")
        if values.get("model_type") == "logistic_regression" and old_c is not None:
            for factor in (0.5, 2.0):
                edits.append({"symbol": "C", "old": old_c, "new": _fmt(_clip("C", float(old_c) * factor, spec), old_c)})
        for option in allowed.get("model_type", []):
            if option != values.get("model_type"):
                edits.append({"symbol": "model_type", "old": values["model_type"], "new": str(option)})
        for option in allowed.get("class_weight", []):
            option_s = "null" if option is None else str(option)
            if option_s != values.get("class_weight"):
                edits.append({"symbol": "class_weight", "old": values["class_weight"], "new": option_s})
                break
        return edits[:5]
    else:
        symbols = [s for s in spec.editable_symbols if s in values]
    for symbol in symbols:
        old = values.get(symbol)
        try:
            old_f = float(old)
        except (TypeError, ValueError):
            continue
        for factor in (0.5, 2.0):
            new = _fmt(_clip(symbol, old_f * factor, spec), old)
            if float(new) != old_f:
                numeric.append({"symbol": symbol, "old": old, "new": new})
    pool = numeric + categorical
    rng = np.random.default_rng(sum(map(ord, node)))  # stable across runs and machines
    order = rng.permutation(len(pool))
    return [pool[i] for i in order[:5]]


# ---------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------

def _prepare_node(node: str, workdir: Path) -> Path:
    node_dir = workdir / node
    shutil.copytree(HARNESS / "nodes" / node, node_dir, ignore=shutil.ignore_patterns("__pycache__", ".autoresearch_artifacts"))
    if node.startswith("openml_") and not (node_dir / "data_cache").exists():
        cache = HARNESS / PILOT_DATA_CACHE.format(node=node)
        if cache.exists():
            shutil.copytree(cache, node_dir / "data_cache")
    return node_dir


def _noedit(spec) -> ManagerProposal:
    return ManagerProposal(manager_mode="e1_pilot", proposal_summary="no edit", proposal_rationale="",
                           target_files=spec.editable_paths, objective="Run the current configuration; no change.")


def _edit_proposal(spec, edit: dict[str, str] | None) -> ManagerProposal:
    if edit is None:
        return _noedit(spec)
    return ManagerProposal(manager_mode="e1_pilot", proposal_summary=f"{edit['symbol']} edit",
                           proposal_rationale="", target_files=spec.editable_paths,
                           objective=f"Change {edit['symbol']} from {edit['old']} to {edit['new']}")


def run_one(node: str, config_id: str, edit: dict[str, str] | None, condition: str,
            train_seed: int | None, split_seed: int | None, out_tmp: str) -> dict:
    """One isolated run: fresh node copy, apply the edit (if any), run at the given seeds."""
    spec = load_registered_node(node, repo_root=HARNESS)
    work = Path(tempfile.mkdtemp(prefix=f"e1_{node}_{config_id}_", dir=out_tmp))
    try:
        node_dir = _prepare_node(node, work)
        worker = LocalWorker(node_root=node_dir, artifact_dir=work / "art", timeout_seconds=600)
        t0 = time.perf_counter()
        result = worker.run_trial_at_seed(_edit_proposal(spec, edit), spec, 1,
                                          train_seed=train_seed, split_seed=split_seed)
        return {
            "node": node, "config": config_id, "condition": condition,
            "train_seed": train_seed, "split_seed": split_seed,
            "metric": result.parsed_metrics.get(spec.metric_name) if result.success else None,
            "success": bool(result.success), "failure": result.failure_message,
            "edit_applied": bool(result.changed_files) if edit is not None else None,
            "wall_seconds": round(time.perf_counter() - t0, 4),
        }
    finally:
        shutil.rmtree(work, ignore_errors=True)


def plan_runs(node: str, config_id: str, n_seeds: int) -> list[tuple[str, int | None, int | None]]:
    runs: list[tuple[str, int | None, int | None]] = [("default", None, None), ("default_repeat", None, None)]
    runs += [("train", SEED_BASE["train"] + s, None) for s in range(n_seeds)]
    runs += [("split", None, SEED_BASE["split"] + s) for s in range(n_seeds)]
    runs += [("joint", SEED_BASE["joint"] + s, SEED_BASE["joint"] + s) for s in range(n_seeds)]
    return runs


def _key(node, config, condition, train_seed, split_seed) -> tuple:
    return (node, config, condition, train_seed, split_seed)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--nodes", nargs="+", default=list(DEFAULT_NODES))
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 0))
    parser.add_argument("--out", default=None)
    parser.add_argument("--tmp", default=os.environ.get("R1_TMP", tempfile.gettempdir()))
    parser.add_argument("--resume", default=None, help="Existing output dir; run only missing rows.")
    parser.add_argument("--deadline", type=float, default=1e9,
                        help="Stop submitting new runs after this many seconds (for time-boxed shells).")
    args = parser.parse_args()

    if args.resume:
        out = Path(args.resume)
        manifest = json.loads((out / "manifest.json").read_text())
        edits_by_node = json.loads((out / "edits.json").read_text())
        nodes = manifest["nodes"]
        n_seeds = int(manifest["seeds_per_condition"])
    else:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out = Path(args.out) if args.out else REPO / "results" / "r1" / "pilot" / f"E1_{stamp}"
        out.mkdir(parents=True, exist_ok=True)
        nodes, n_seeds, edits_by_node = list(args.nodes), args.seeds, {}
        Path(args.tmp).mkdir(parents=True, exist_ok=True)
        for node in nodes:
            spec = load_registered_node(node, repo_root=HARNESS)
            probe = Path(tempfile.mkdtemp(dir=args.tmp))
            edits_by_node[node] = [] if node in BASELINE_ONLY else candidate_edits(node, _prepare_node(node, probe), spec)
            shutil.rmtree(probe, ignore_errors=True)
        manifest = {
            "schema": "r1.e1_noise_floor/2", "label": "PILOT", "started_utc": stamp,
            "harness": {"root": str(HARNESS), **harness_commit(HARNESS)},
            "seeds_per_condition": n_seeds, "seed_bases": SEED_BASE, "nodes": nodes,
            "host": {"platform": platform.platform(), "python": platform.python_version(), "cpus": os.cpu_count(),
                     "libraries": library_versions()},  # PLAN §10 "D21 rule (22 Oct)": versions in every manifest
            "note": "Pilot only; not evidence (RUNBOOK §1 rule 3). Wall times are measured under parallel load.",
            "sessions": [],
        }
        (out / "edits.json").write_text(json.dumps(edits_by_node, indent=2) + "\n")
    Path(args.tmp).mkdir(parents=True, exist_ok=True)

    done = set()
    runs_path = out / "runs.jsonl"
    if runs_path.exists():
        for line in runs_path.read_text().splitlines():
            row = json.loads(line)
            done.add(_key(row["node"], row["config"], row["condition"], row.get("train_seed"), row.get("split_seed")))
    todo = []
    for node in nodes:
        configs = [("c0", None)] + [(f"c{k}", e) for k, e in enumerate(edits_by_node[node], start=1)]
        for config_id, edit in configs:
            for condition, ts, ss in plan_runs(node, config_id, n_seeds):
                if _key(node, config_id, condition, ts, ss) not in done:
                    todo.append((node, config_id, edit, condition, ts, ss))

    t0 = time.time()
    session = {"start_utc": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"), "todo_before": len(todo)}
    written = 0
    with open(runs_path, "a", encoding="utf-8") as fh, ProcessPoolExecutor(max_workers=args.workers) as pool:
        pending = set()
        queue = list(todo)
        while queue or pending:
            while queue and len(pending) < args.workers and time.time() - t0 < args.deadline:
                job = queue.pop(0)
                pending.add(pool.submit(run_one, *job, args.tmp))
            if not pending:
                break
            finished = [f for f in pending if f.done()]
            if not finished:
                time.sleep(0.05)
                continue
            for fut in finished:
                pending.discard(fut)
                fh.write(json.dumps(fut.result()) + "\n")
                written += 1
            fh.flush()
    session.update({"written": written, "remaining": len(todo) - written, "elapsed_seconds": round(time.time() - t0, 1)})
    manifest.setdefault("sessions", []).append(session)
    if len(todo) - written == 0:
        manifest["finished_utc"] = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"out": str(out), **session}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
