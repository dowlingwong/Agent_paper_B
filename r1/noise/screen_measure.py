#!/usr/bin/env python3
"""Runner of the direct screening measurement R1-SCREEN-MEASURE (tier E): c0, the five E1 single edits and the
two-edit children of ``screen_design`` on every T0 node, each at the 120 fresh joint seeds 3301-3420.

AI-assisted (Claude, subagent, 23 Nov 2026; data caches: Claude, 26 Nov 2026). DRAFT; not signed.
Pre-declaration: ``docs/r1/authorizations/SCREEN_MEASURE_PREDECLARATION_DRAFT_20261123.md``.

Harness path. Every run reuses ``r1.noise.e1_noise_floor`` (imported only when a harness run is made, so ``plan``,
``--stub`` and the tests need no harness): a fresh node copy (``_prepare_node``), the harness
``LocalWorker.run_trial_at_seed`` with an E1 edit proposal (``_edit_proposal``), at train seed = split seed = s.
The harness worker applies one "Change X from A to B" directive per trial, so a child c0 + e_i + e_j is made by
writing e_i into the node copy first, with ``r1.c3.features.apply_edit`` (the harness worker's edit rule, stale-value
check included), then passing e_j to the harness as in E1. c0 and the singles run exactly as in E1.
``e1_noise_floor.py`` itself is not changed.

Modes:
  plan                      the run list (no harness, no run);
  run --stub                synthetic metrics from the model of ``screen_power`` (no harness; dry runs and tests
                            only; label ENGINEERING_ONLY);
  run --engineering-smoke   harness runs at the engineering smoke seed 999 only (label ENGINEERING_ONLY), to check
                            that every configuration runs and every edit is applied and verified;
  run --evidence            the measurement (label EVIDENCE): only with the signed note on published main, on
                            the signed host, with the R1-SWEEP2-B2-GO environment checks
                            and the deepthought2 placement in R1-SCREEN-DEEPTHOUGHT2.

STOP rules (the run stops submitting, lets the runs in flight finish, writes the manifest with the reason and exits 3;
a STOPped run is reported, never resumed or patched): a determinism mismatch (a configuration's repeat at seed 3301
differs from its first run); a failed run (no metric or non-finite) at seed 3301, first run or repeat, which leaves the
determinism check unverifiable (``determinism_unverifiable``); an edit not applied by the harness, a pre-applied edit
not in the node copy, a declared value not read back after the run, or any other symbol changed by the run; more than
1 % of the planned runs failed; a run raising an exception; a worker-runtime probe failure or mismatch (recorded as
``worker_runtime``); a co-tenancy breach (fewer than 10 cores left to other users). No deadline: R1-NO-TIMEOUT (1)
withdraws the deadline option of this measurement (local/20261126-07); a run that makes no progress is ended by the
operator as an infrastructure failure. The harness worker's 600 s per-run budget stays (R1-NO-TIMEOUT (2)). A STOP before launch
(a note field, a precondition, the harness's E1 edit set differing from the declared one, the output or scratch
directory existing) raises before the output directory is created: exit status 1 and no manifest.

The engineering smoke also lists, in its manifest (``identity_flags``), every configuration whose seed-999 metric is
bit-identical to that of c0 or of one of its single-edit parents (review M3: one seed cannot prove a difference, but
an identity is a strong signal that an edit is inert). A flag is not a STOP; it goes to the reviewer and the author.

Changes after the independent review (AI-assisted (Claude, subagent, 23 Nov 2026);
``docs/r1/reviews/SCREEN_MEASURE_PREDECL_REVIEW_20261123.md``): M1 ``determinism_unverifiable``; M3 ``identity_flags``;
N2 ``worker_runtime``; N6 the manifest's ``seeds`` are the seeds actually planned (999 for the smoke).

Data identity (local/20261126-02, after the 26 Nov smoke STOP ``determinism_unverifiable openml_breast_w c5 seed 999``).
The OpenML nodes read their dataset through ``fetch_openml(data_home=<node>/data_cache)``. The harness commits no cache
(only placeholders) and ``_prepare_node``'s fallback, the pilot cache under the harness's ignored ``experiments/``, is
absent from a fresh harness worktree, so every run of the smoke downloaded its dataset from openml.org (16 at a time) and
the data were pinned by nothing. ``data-cache --out DIR`` now builds the caches once, one node at a time, through the
pinned node's loader with the worker's python3 (then repeats the load offline to verify the cache; nothing kept but
the cache), checks the downloaded ARFF's (identified by content) decompressed sha256 against the pilot cache's where the pilot had the node
(``PILOT_ARFF_SHA256``), and writes ``DIR/MANIFEST.json`` (per file the stored and decompressed sha256, per node and in
total a tree sha256). ``run --engineering-smoke`` and ``run --evidence`` require ``--data-cache DIR``: the manifest must
match the files and name exactly the design's OpenML nodes; every run gets a copy of its node's cache (replacing any
fallback copy), and a run that leaves the cache different (a download, a change) is the STOP ``data_cache``. The
evidence note carries ``data_cache_sha256`` (the total tree sha256). A failed run's log tail (and the harness's failure
category) goes to ``failed_runs.jsonl`` beside the runs (the 26 Nov failure left no log: the scratch copy is removed).
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import json
import math
import os
import platform
import re
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from r1.harness import REPO
from r1.noise import screen_analysis as sa
from r1.noise import screen_design as sd

SCHEMA_RUN = sa.SCHEMA_RUN
RUNS_FILE = sa.RUNS_FILE
EVIDENCE_OUT_ROOT = "results/r1/screen_measure"
EVIDENCE_TMP_PREFIX = "r1_smeas_EVIDENCE_"
SMOKE_SEED = 999                     # r1/e2e.py engineering smoke seed (a reserved engineering namespace)
FAILURE_STOP_FRACTION = 0.01
MAX_WORKERS = 16                     # R1-B2-GO / the B.2 addenda: 16 workers
DEEPTHOUGHT2_WORKERS = 64             # R1-SCREEN-DEEPTHOUGHT2: CPU only, at most 64 CPUs
DEEPTHOUGHT2_RULING = "R1-SCREEN-DEEPTHOUGHT2"
FREE_CORES = 10                      # ... with at least 10 of the host's cores left to other users
COTENANCY_SAMPLE_SECONDS = 60.0
HARNESS_COMMIT = sa.HARNESS_COMMIT   # 6adf3859..., the B.2 audit harness (R1-SWEEP2-B2-GO); checked again by the analysis
PHASE = "r1_screen_measure"
START_RULING = "R1-SCREEN-MEASURE"
DATA_CACHE_SCHEMA = "r1_screen_measure_data_cache/1"
DATA_CACHE_MANIFEST = "MANIFEST.json"
FAILED_RUNS_FILE = "failed_runs.jsonl"
FAILURE_LOG_TAIL = 4000               # characters of a failed run's log kept in failed_runs.jsonl
# Decompressed sha256 of each pilot-cache ARFF (harness experiments/r1/pilot/L8_20261009T152916Z, the E1 pilot's data);
# a freshly built cache of these nodes must hold the same data. openml_climate and openml_sonar had no pilot cache.
PILOT_ARFF_SHA256 = {
    "openml_breast_w": "cb44e7f62f4a962881147264e5f985eacc13256712e7a4b9d1731ced05f3ee9b",
    "openml_credit_approval": "ae8e5eadb70e187885ddc6defb7f3e4afa726aa472ac63ebf5e387f0a8467891",
    "openml_ionosphere": "bcbf8c656fe9a44a87df76003b9b2b6b36bfc52c01f0e316014cebbce9ccb701",
    "openml_wdbc": "e850cb4cc32dacf29d3fa639d0029cb45582d4838a62322e7b3fbac1b8452f1d",
}
CODE_FILES = ("r1/noise/screen_design.py", "r1/noise/screen_measure.py", "r1/noise/screen_analysis.py",
              "r1/noise/screen_seeds.py", "r1/noise/screen_power.py", "r1/noise/e1_noise_floor.py")


class RunStop(RuntimeError):
    pass


class DataCacheStop(RuntimeError):
    """A run's dataset cache was not the declared one (changed since launch, or after the run: a download or a
    change). Carries the run's log tail (review M2), in ``args`` so that it survives the process pool."""

    def __init__(self, message: str, log_tail: str = ""):
        super().__init__(message, log_tail)

    def __str__(self) -> str:
        return str(self.args[0])

    @property
    def log_tail(self) -> str:
        return str(self.args[1]) if len(self.args) > 1 else ""


class WorkerRuntimeStop(RuntimeError):
    """The per-run worker-runtime probe (R1-B2-GO B4 (a)) failed or did not match: its own STOP reason (review N2)."""


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

def stub_runner(design: dict, s: float = 0.0, scale: float = 0.01):
    """A deterministic synthetic run function from ``screen_power.lineage_covariance`` (shared share s): the value of
    (node, config, seed) does not depend on run order. ENGINEERING_ONLY."""
    from r1.noise.screen_power import lineage_covariance
    chol = {}
    for node, v in design["nodes"].items():
        ids, cov = lineage_covariance(v, s)
        chol[node] = (ids, np.linalg.cholesky(cov + 1e-10 * np.eye(len(ids))))

    def run(job: dict, _tmp: str) -> dict:
        ids, L = chol[job["node"]]
        key = int(hashlib.sha256(f"{job['node']}|{job['seed']}".encode()).hexdigest()[:12], 16)
        z = np.random.default_rng(key).normal(size=len(ids))
        k = ids.index(job["config"])
        metric = 0.9 + 0.001 * k + scale * float(L[k] @ z)
        base = {e["symbol"]: e["old"] for e in design["nodes"][job["node"]]["edits"]}
        before = {**base, **{e["symbol"]: e["new"] for e in job["edits"][:-1]}}
        after = {**before, **({job["edits"][-1]["symbol"]: job["edits"][-1]["new"]} if job["edits"] else {})}
        return {"node": job["node"], "config": job["config"], "condition": job["condition"], "seed": job["seed"],
                "metric": round(metric, 12), "success": True, "failure": None,
                "edit_applied": True if job["edits"] else None,
                "values_before": before, "values_after": after, "wall_seconds": 0.0}
    return run


# ---------------------------------------------------------------------------------------------------- harness run

def _edit_path(node_dir: Path, spec, symbol: str) -> str:
    hits = [rel for rel in spec.editable_paths
            if re.search(rf"^{re.escape(symbol)}\s*[=:]", (node_dir / rel).read_text(encoding="utf-8"), re.MULTILINE)]
    if len(hits) != 1:
        raise RunStop(f"STOP: {symbol} is assigned in {len(hits)} editable files")
    return hits[0]


# ---------------------------------------------------------------------------------------------------- data cache

def _file_sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _content(path: Path) -> bytes:
    """The file's content, gunzipped when it is a .gz (the stored gzip header carries a time stamp)."""
    import gzip
    path = Path(path)
    data = path.read_bytes()
    if path.name.endswith(".gz"):
        try:
            data = gzip.decompress(data)
        except (OSError, EOFError) as exc:
            raise RunStop(f"STOP: {path} is not a gzip file ({exc})") from None
    return data


def _content_sha(path: Path) -> str:
    return hashlib.sha256(_content(path)).hexdigest()


def is_arff(data: bytes) -> bool:
    """Identify ARFF by its first nonblank, non-comment line. OpenML download paths depend on the dataset URL."""
    for raw in data[:65536].splitlines():
        line = raw.strip()
        if not line or line.startswith(b"%"):
            continue
        return line.lower().startswith(b"@relation")
    return False


def cache_tree(cache: Path) -> dict:
    """Every regular file under a node's cache: {relative path: {"sha256", "content_sha256", "arff"}} (``arff``: the
    decompressed content is an ARFF file, ``is_arff``); a symlink is refused."""
    cache = Path(cache)
    if not cache.is_dir():
        raise RunStop(f"STOP: {cache} is not a directory")
    out = {}
    for f in sorted(cache.rglob("*")):
        if f.is_symlink():
            raise RunStop(f"STOP: {f} is a symlink")
        if f.is_file():
            data = _content(f)
            out[f.relative_to(cache).as_posix()] = {"sha256": _file_sha(f),
                                                     "content_sha256": hashlib.sha256(data).hexdigest(),
                                                     "arff": is_arff(data)}
    return out


def tree_sha256(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def data_nodes(design: dict, harness: Path) -> list[str]:
    """The design's nodes that read a dataset from openml.org (a ``dataset.json`` in the harness node)."""
    return sorted(n for n in design["nodes"] if (Path(harness) / "nodes" / n / "dataset.json").is_file())


def check_pilot(node: str, files: dict) -> None:
    arffs = [v["content_sha256"] for v in files.values() if v.get("arff") is True]   # by content, not by name
    if len(arffs) != 1:
        raise RunStop(f"STOP: {node}'s cache holds {len(arffs)} ARFF files, not one")
    if node in PILOT_ARFF_SHA256 and arffs[0] != PILOT_ARFF_SHA256[node]:
        raise RunStop(f"STOP: {node}'s dataset differs from the E1 pilot's (decompressed ARFF sha256 {arffs[0]})")


def read_data_cache(root: Path, nodes: list[str]) -> dict:
    """``DIR/MANIFEST.json`` checked against the files: exactly ``nodes``, each tree recomputed and equal, one ARFF per
    node, the pilot's data where the pilot had the node. Returns {"tree_sha256", "nodes": {node: tree sha256}}."""
    root = Path(root)
    try:
        man = json.loads((root / DATA_CACHE_MANIFEST).read_text())
    except (OSError, ValueError) as exc:
        raise RunStop(f"STOP: {root / DATA_CACHE_MANIFEST} is not readable JSON ({exc})") from None
    if not isinstance(man, dict) or not isinstance(man.get("nodes"), dict) or \
            not all(isinstance(v, dict) for v in man["nodes"].values()) or \
            man.get("schema") != DATA_CACHE_SCHEMA or sorted(man["nodes"]) != sorted(nodes):
        raise RunStop(f"STOP: the data-cache manifest must be {DATA_CACHE_SCHEMA} for exactly the nodes {nodes}")
    extra = sorted(p.name for p in root.iterdir() if p.name not in set(nodes) | {DATA_CACHE_MANIFEST})
    if extra:
        raise RunStop(f"STOP: unexpected entries in the data-cache directory: {extra}")
    trees = {}
    for node in nodes:
        files = cache_tree(root / node / "data_cache")
        if files != man["nodes"][node].get("files") or tree_sha256(files) != man["nodes"][node].get("tree_sha256"):
            raise RunStop(f"STOP: {node}'s cache files differ from the data-cache manifest")
        check_pilot(node, files)
        trees[node] = tree_sha256(files)
    if tree_sha256(trees) != man.get("tree_sha256"):
        raise RunStop("STOP: the data-cache manifest's total tree_sha256 is not its nodes'")
    return {"tree_sha256": tree_sha256(trees), "nodes": trees}


def _load_openml_cache(node_dir: Path, *, offline: bool) -> None:
    """Use the pinned benchmark loader in a fresh worker interpreter. The verification load may only use its cache."""
    from autoresearch.worker.seeds import seed_environment

    code = """
import sys

from sklearn.datasets import _openml

def refuse_download(request):
    raise RuntimeError("unexpected OpenML download: " + request.full_url)

if sys.argv[1] == "offline":
    _openml.urlopen = refuse_download

from benchmark import _load_frame

_load_frame()
"""
    try:
        subprocess.run(["python3", "-B", "-c", code, "offline" if offline else "online"], cwd=node_dir,
                       env=seed_environment(SMOKE_SEED, SMOKE_SEED), capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        mode = "offline verification" if offline else "build"
        detail = (exc.stderr or str(exc)).strip() if isinstance(exc, subprocess.CalledProcessError) else str(exc)
        raise RunStop(f"STOP: {node_dir.name}: OpenML cache {mode} failed: {detail[-FAILURE_LOG_TAIL:]}") from None


def build_data_cache(design: dict, out: Path, tmp: str) -> dict:
    """Build each node's cache with its pinned loader and check that a second, offline load leaves it intact."""
    from r1.harness import harness_commit
    from r1.noise import e1_noise_floor as e1
    out = Path(out)
    if out.exists():
        raise RunStop(f"STOP: {out} exists (a data cache is built once, into a new directory)")
    hc = harness_commit(e1.HARNESS)
    if hc.get("commit") != HARNESS_COMMIT or hc.get("dirty"):
        raise RunStop(f"STOP: the harness must be {HARNESS_COMMIT}, clean")
    nodes = data_nodes(design, e1.HARNESS)
    out.mkdir(parents=True)
    man = {"schema": DATA_CACHE_SCHEMA, "label": "ENGINEERING_ONLY", "harness_commit": HARNESS_COMMIT,
           "libraries": e1.library_versions(), "host": platform.node(),
           "created_utc": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"), "nodes": {}}
    for node in nodes:
        work = Path(tempfile.mkdtemp(prefix=f"smeas_cache_{node}_", dir=tmp))
        try:
            node_dir = e1._prepare_node(node, work)
            shutil.rmtree(node_dir / "data_cache", ignore_errors=True)
            (node_dir / "data_cache").mkdir()
            cache = node_dir / "data_cache"
            _load_openml_cache(node_dir, offline=False)
            files = cache_tree(cache)
            check_pilot(node, files)
            _load_openml_cache(node_dir, offline=True)
            if cache_tree(cache) != files:
                raise RunStop(f"STOP: {node}: the offline load changed the OpenML cache")
            shutil.copytree(cache, out / node / "data_cache")
        finally:
            shutil.rmtree(work, ignore_errors=True)
        man["nodes"][node] = {"files": files, "tree_sha256": tree_sha256(files)}
    man["tree_sha256"] = tree_sha256({n: v["tree_sha256"] for n, v in man["nodes"].items()})
    (out / DATA_CACHE_MANIFEST).write_text(json.dumps(man, indent=1, sort_keys=True) + "\n")
    return {"out": str(out), "nodes": nodes, "tree_sha256": man["tree_sha256"]}


def run_one_lineage(job: dict, out_tmp: str, runtime_expected: dict | None = None,
                    data_cache: str | None = None, data_trees: dict | None = None) -> dict:
    """One isolated harness run of a configuration with 0, 1 or 2 edits (subprocess-safe). With ``data_cache`` (the
    checked data-cache directory) an OpenML node runs on a copy of its declared cache and must leave it unchanged."""
    from r1.c3.features import apply_edit
    from r1.noise import e1_noise_floor as e1          # imports the harness

    node, edits, seed = job["node"], job["edits"], int(job["seed"])
    spec = e1.load_registered_node(node, repo_root=e1.HARNESS)
    work = Path(tempfile.mkdtemp(prefix=f"smeas_{node}_{job['config']}_", dir=out_tmp))
    try:
        node_dir = e1._prepare_node(node, work)
        declared = None
        if data_cache is not None and node in (data_trees or {}):    # review M1: against the launch-verified tree
            src = Path(data_cache) / node / "data_cache"
            if not src.is_dir() or tree_sha256(cache_tree(src)) != data_trees[node]:
                raise DataCacheStop(f"{node}'s declared cache is missing or changed since launch")
            declared = data_trees[node]
            shutil.rmtree(node_dir / "data_cache", ignore_errors=True)     # a placeholder or the pilot fallback copy
            shutil.copytree(src, node_dir / "data_cache", symlinks=True)
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
        if runtime_expected is not None:                  # R1-B2-GO B4 (a): the per-run worker-runtime probe
            from autoresearch.worker.seeds import seed_environment
            from r1.c3.audit import worker_runtime
            try:
                probe = worker_runtime(runtime_expected, spec.run_command, seed_environment(seed, seed))
            except Exception as exc:  # noqa: BLE001 - recorded under its own STOP reason (review N2)
                raise WorkerRuntimeStop(str(exc)) from None
        worker = e1.LocalWorker(node_root=node_dir, artifact_dir=work / "art", timeout_seconds=600)
        last = edits[-1] if edits else None
        t0 = time.perf_counter()
        result = worker.run_trial_at_seed(e1._edit_proposal(spec, last), spec, 1, train_seed=seed, split_seed=seed)
        wall = round(time.perf_counter() - t0, 4)
        after = e1.current_values(node_dir, spec)
        if declared is not None and tree_sha256(cache_tree(node_dir / "data_cache")) != declared:
            log = Path(result.raw_log_ref) if result.raw_log_ref else None        # review M2: keep the log
            text = log.read_text(encoding="utf-8", errors="replace") if log and log.is_file() else ""
            raise DataCacheStop(f"{node}'s dataset cache changed during the run (a download or an edit)",
                                text[-FAILURE_LOG_TAIL:])
        metric = result.parsed_metrics.get(spec.metric_name) if result.success else None
        row = {"node": node, "config": job["config"], "condition": job["condition"], "seed": seed,
               "metric": metric, "success": bool(result.success), "failure": result.failure_message,
               "edit_applied": bool(result.changed_files) if last else None,
               "values_before": before, "values_after": after, "wall_seconds": wall}
        if probe is not None:
            row["_worker_runtime"] = probe
        if not result.success:                            # the 26 Nov smoke: keep what the failed run said
            log = Path(result.raw_log_ref) if result.raw_log_ref else None
            text = log.read_text(encoding="utf-8", errors="replace") if log and log.is_file() else ""
            row["_failure_log"] = {"failure_category": (result.extra or {}).get("failure_category"),
                                   "log_tail": text[-FAILURE_LOG_TAIL:]}
        return row
    finally:
        shutil.rmtree(work, ignore_errors=True)


# ---------------------------------------------------------------------------------------------------- checks

def check_row(row: dict, job: dict) -> str | None:
    """The per-run STOP checks on the edit; returns a STOP reason or None."""
    before = {k: _norm(v) for k, v in (row.get("values_before") or {}).items()}
    after = {k: _norm(v) for k, v in (row.get("values_after") or {}).items()}
    last = job["edits"][-1]["symbol"] if job["edits"] else None
    if job["edits"]:
        if row["edit_applied"] is not True:
            return f"edit_not_applied {row['node']} {row['config']} seed {row['seed']}"
        intended = {e["symbol"]: _norm(e["new"]) for e in job["edits"]}
        if any(after.get(k) != v for k, v in intended.items()):
            return f"edit_not_verified {row['node']} {row['config']} seed {row['seed']}"
    if set(before) != set(after) or any(after[k] != before[k] for k in before if k != last):
        return f"undeclared_change {row['node']} {row['config']} seed {row['seed']}"
    return None


def identity_flags(rows: list[dict], design: dict) -> list[dict]:
    """Review M3, engineering smoke: every configuration whose first-run metric is bit-identical to that of c0 or of one
    of its single-edit parents (for a child c_ij: c0, c_i, c_j; for a single: c0). Rows of condition ``seed`` with a
    finite metric only. A flag is not a STOP: one seed cannot prove a difference, but an identity is a strong signal
    that an edit is inert, which would turn a lineage into a sibling triple."""
    first = {}
    for r in rows:
        if r.get("condition") == "seed" and r.get("success") and r.get("metric") is not None \
                and math.isfinite(float(r["metric"])):
            first[(r["node"], r["config"])] = (float(r["metric"]), r["seed"])
    flags = []
    for node, v in design["nodes"].items():
        for cid, cfg in v["configs"].items():
            if cid == "c0" or (node, cid) not in first:
                continue
            parents = ["c0"] + ([f"c{i}" for i in cfg["edits"]] if len(cfg["edits"]) > 1 else [])
            for p in parents:
                if (node, p) in first and first[(node, p)][0] == first[(node, cid)][0]:
                    flags.append({"node": node, "config": cid, "identical_to": p, "seed": first[(node, cid)][1],
                                  "metric": first[(node, cid)][0]})
    return flags


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


def key_block(text: str) -> dict:
    """The fields of the note: ``key: value`` lines inside the one fenced block under the heading ``## Key block``."""
    lines = text.splitlines()
    try:
        start = lines.index("## Key block")
    except ValueError:
        raise RunStop("STOP: the note has no '## Key block' heading") from None
    fences = [i for i in range(start + 1, len(lines)) if lines[i].strip() == "```"]
    if len(fences) < 2:
        raise RunStop("STOP: the note's key block is not one fenced block")
    fields = {}
    for line in lines[fences[0] + 1:fences[1]]:
        m = re.match(r"^([A-Za-z0-9_]+): (.*)$", line)
        if not m:
            if line.strip():
                raise RunStop(f"STOP: a key-block line is not 'key: value': {line[:60]!r}")
            continue
        if m.group(1) in fields:
            raise RunStop(f"STOP: note field {m.group(1)} appears twice")
        fields[m.group(1)] = m.group(2).strip()
    return fields


def code_pins(repo: Path = REPO) -> dict:
    return {rel: sd.sha256_file(Path(repo) / rel) for rel in CODE_FILES}


def cotenancy(workers_running: int, *, host_wide: bool = False) -> dict:
    """The accepted B.2 convention: cores left to other users = cpus - (1-min load - our running workers)."""
    # The deepthought2 launch caps its own affinity. The host's load average still covers the whole machine.
    cpus = os.cpu_count() or 1
    if not host_wide and hasattr(os, "sched_getaffinity"):
        cpus = len(os.sched_getaffinity(0))
    load = os.getloadavg()[0]
    free = cpus - max(0.0, load - workers_running)
    return {"utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "cpus": cpus, "load1": load,
            "our_workers": workers_running, "free_for_others": round(free, 2), "ok": free >= FREE_CORES}


def expected_note(args, design: dict, root: Path) -> dict:
    want = {"approved": "true", "label": "EVIDENCE", "phase": PHASE, "start_ruling": START_RULING,
            "run_id": sd.RUN_ID, "design_sha256": sd.design_sha256(design), "seed_block": "3301-3420",
            "harness_commit": HARNESS_COMMIT, "code_commit": args.code_commit, "code_review": args.code_review,
            "labels_read": "none",
            "data_cache_sha256": args.data_cache_sha256}
    want.update({f"sha256_{Path(k).stem}": v for k, v in code_pins(root).items()})
    return want


def preflight_evidence(args, design: dict) -> dict:
    """Every precondition of the authorization note that code can check (R1-SWEEP2-B2-GO conditions included)."""
    from r1.c3 import audit
    from r1.noise import screen_seeds
    root = Path(args.paper_root).resolve()
    note_rel = args.note
    if not note_rel or Path(note_rel).is_absolute() or ".." in Path(note_rel).parts or \
            not note_rel.startswith("docs/r1/authorizations/"):
        raise RunStop("STOP: --note must be a repository-relative path under docs/r1/authorizations/")
    try:                                   # B1 (a): authority files are read from the published main
        note_bytes = audit._published_bytes(root, note_rel)
        plan_text = audit._published_bytes(root, "docs/r1/PLAN.md").decode("utf-8")
    except ValueError as exc:
        raise RunStop(f"STOP: {exc}") from None
    note = key_block(note_bytes.decode("utf-8"))
    if any("<" in v for v in note.values()):
        raise RunStop("STOP: a note field still holds a placeholder")
    want = expected_note(args, design, root)
    bad = sorted(k for k, v in want.items() if note.get(k) != v)
    if bad:
        raise RunStop(f"STOP: note fields differ from the run: {bad}")
    host = note.get("launch_host", "deepthought")
    if host not in ("deepthought", "deepthought2"):
        raise RunStop(f"STOP: unknown screening launch host {host!r}")
    moved = host == "deepthought2"
    cap = DEEPTHOUGHT2_WORKERS if moved else MAX_WORKERS
    try:
        note_workers = int(note["workers"])
    except (KeyError, ValueError):
        raise RunStop("STOP: the note's workers field is missing or not an integer") from None
    if not 1 <= args.workers <= note_workers <= cap:
        raise RunStop(f"STOP: workers {args.workers} not within 1..note workers ({note_workers}) <= {cap}")
    if moved and args.workers != note_workers:
        raise RunStop("STOP: deepthought2 workers must equal the note's reviewed worker count")
    pre_path, _, pre_sha = note.get("predeclaration", "").partition(" sha256 ")
    try:
        pre_bytes = audit._published_bytes(root, pre_path.strip())
    except ValueError as exc:
        raise RunStop(f"STOP: pre-declaration: {exc}") from None
    if hashlib.sha256(pre_bytes).hexdigest() != pre_sha.strip():
        raise RunStop("STOP: the published pre-declaration's sha256 differs from the note's")
    rows = [line for line in plan_text.splitlines() if line.startswith(f"| {START_RULING} |")]
    if len(rows) != 1 or "deepthought" not in rows[0] or "R1-SWEEP2-B2-GO" not in rows[0]:
        raise RunStop(f"STOP: published PLAN.md must hold exactly one {START_RULING} row naming deepthought and "
                      "R1-SWEEP2-B2-GO")
    if moved:
        move_rows = [line for line in plan_text.splitlines() if line.startswith(f"| {DEEPTHOUGHT2_RULING} |")]
        if len(move_rows) != 1 or "deepthought2" not in move_rows[0]:
            raise RunStop(f"STOP: published PLAN.md must hold exactly one {DEEPTHOUGHT2_RULING} row naming deepthought2")
        if not hasattr(os, "sched_getaffinity"):
            raise RunStop("STOP: deepthought2 CPU affinity could not be verified")
        affinity_cpus = sorted(os.sched_getaffinity(0))
        if not args.workers <= len(affinity_cpus) <= DEEPTHOUGHT2_WORKERS:
            raise RunStop(f"STOP: deepthought2 affinity must cover {args.workers} workers within 64 CPUs")
        if os.environ.get("CUDA_VISIBLE_DEVICES") != "":
            raise RunStop("STOP: deepthought2 requires CUDA_VISIBLE_DEVICES empty")
    provenance = audit.evidence_paper_provenance(root, args.code_commit, args.code_review)
    environment = audit.evidence_environment(root, expected_host=host) if moved else audit.evidence_environment(root)
    equivalence = audit.sweep2_harness_equivalence(Path(os.environ["AR_HARNESS_ROOT"]))
    seeds = screen_seeds.check_block(sd.SEED_BLOCK)
    tmp = Path(args.tmp)
    if tmp.parent.resolve() != Path("/tmp").resolve() or not tmp.name.startswith(EVIDENCE_TMP_PREFIX) or tmp.exists():
        raise RunStop(f"STOP: --tmp must be a new directory /tmp/{EVIDENCE_TMP_PREFIX}<stamp>")
    start = cotenancy(0, host_wide=True) if moved else cotenancy(0)
    if not start["ok"]:
        raise RunStop(f"STOP: co-tenancy before launch: {start}")
    record = {"note": note_rel, "note_sha256": hashlib.sha256(note_bytes).hexdigest(),
            "predeclaration_sha256": pre_sha.strip(), "provenance": provenance, "environment": environment,
            "harness_equivalence": equivalence, "seed_check": seeds, "cotenancy_at_start": start}
    if moved:
        if start["cpus"] - start["load1"] - args.workers < FREE_CORES:
            raise RunStop(f"STOP: deepthought2 lacks capacity for {args.workers} workers and {FREE_CORES} free cores: "
                          f"{start}")
        record.update(launch_host=host, affinity_cpus=affinity_cpus, placement_ruling=DEEPTHOUGHT2_RULING)
    return record


# ---------------------------------------------------------------------------------------------------- execute

def execute(out: Path, jobs: list[dict], run_fn, manifest: dict, workers: int, deadline: float | None, tmp: str,
            in_process: bool = False, monitor: bool = False) -> dict:
    planned = len(jobs)
    failures, stop, written = 0, None, 0
    first = {}
    repeat_keys = {(j["node"], j["config"], j["seed"]) for j in jobs if j["condition"] == "repeat"}
    host_wide = manifest.get("preflight", {}).get("launch_host") == "deepthought2"
    t0 = time.time()
    last_sample = 0.0

    def handle(row: dict, job: dict) -> str | None:
        nonlocal failures
        ok = row["success"] and row["metric"] is not None and math.isfinite(float(row["metric"]))
        key = (job["node"], job["config"], job["seed"])
        if not ok:
            failures += 1
            if key in repeat_keys:                    # review M1: the determinism check can no longer be made
                return f"determinism_unverifiable {job['node']} {job['config']} seed {job['seed']}"
            if failures > FAILURE_STOP_FRACTION * planned:
                return f"failure_rate {failures} of {planned} planned runs"
            return None
        reason = check_row(row, job)
        if reason:
            return reason
        if key in repeat_keys:                        # the repeat and the first run at the repeat seed must agree
            if key in first and first[key] != float(row["metric"]):
                return f"determinism {job['node']} {job['config']} seed {job['seed']}"
            first[key] = float(row["metric"])
        return None

    def exception_stop(job: dict, exc: BaseException) -> str:
        what = "worker_runtime" if isinstance(exc, WorkerRuntimeStop) else \
            "data_cache" if isinstance(exc, DataCacheStop) else "run_exception"              # review N2
        if isinstance(exc, DataCacheStop):                                                  # review M2
            with open(out / FAILED_RUNS_FILE, "a", encoding="utf-8") as ff:
                ff.write(json.dumps({"node": job["node"], "config": job["config"], "seed": job["seed"],
                                     "condition": job["condition"], "failure": f"data_cache: {exc}",
                                     "failure_category": None, "log_tail": exc.log_tail}, sort_keys=True) + "\n")
        return f"{what} {job['node']} {job['config']} {job['seed']}: {exc}"

    def sample(running: int) -> str | None:
        nonlocal last_sample
        if not monitor or time.time() - last_sample < COTENANCY_SAMPLE_SECONDS:
            return None
        last_sample = time.time()
        rec = cotenancy(running, host_wide=True) if host_wide else cotenancy(running)
        with open(out / "cotenancy.log", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
        return None if rec["ok"] else f"cotenancy {rec['free_for_others']} cores left to other users"

    with open(out / RUNS_FILE, "a", encoding="utf-8") as fh:
        def write(row):
            nonlocal written
            probe = row.pop("_worker_runtime", None)
            flog = row.pop("_failure_log", None)
            if flog is not None:
                with open(out / FAILED_RUNS_FILE, "a", encoding="utf-8") as ff:
                    ff.write(json.dumps({"node": row["node"], "config": row["config"], "seed": row["seed"],
                                         "condition": row["condition"], "failure": row["failure"], **flog},
                                        sort_keys=True) + "\n")
            if probe is not None:
                with open(out / "worker_runtime.jsonl", "a", encoding="utf-8") as pf:
                    pf.write(json.dumps({"node": row["node"], "config": row["config"], "seed": row["seed"],
                                         "condition": row["condition"], **probe}, sort_keys=True) + "\n")
            fh.write(json.dumps(row, sort_keys=True) + "\n")
            fh.flush()
            written += 1

        if in_process:
            for job in jobs:
                if deadline is not None and time.time() - t0 > deadline:   # tests only; main passes None
                    stop = "deadline"
                    break
                try:
                    row = run_fn(job, tmp)
                except Exception as exc:  # noqa: BLE001 - every exception in a run is a STOP, recorded
                    stop = exception_stop(job, exc)
                    break
                write(row)
                stop = handle(row, job)
                if stop:
                    break
        else:
            queue = list(jobs)
            with ProcessPoolExecutor(max_workers=workers) as pool:
                pending = {}
                while queue or pending:
                    stop = stop or sample(len(pending))
                    while stop is None and queue and len(pending) < workers:
                        if deadline is not None and time.time() - t0 > deadline:   # tests only; main passes None
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
                            stop = stop or exception_stop(job, exc)
                            continue
                        write(row)
                        stop = stop or handle(row, job)
    manifest.update({"finished_utc": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
                     "planned_runs": planned, "written_runs": written, "failed_runs": failures, "stop": stop,
                     "elapsed_seconds": round(time.time() - t0, 1)})
    if (out / RUNS_FILE).exists():
        manifest["runs_sha256"] = sd.sha256_file(out / RUNS_FILE)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n")
    return manifest


def _run_with_runtime(job: dict, tmp: str, runtime_expected: dict | None = None,
                      data_cache: str | None = None, data_trees: dict | None = None) -> dict:
    return run_one_lineage(job, tmp, runtime_expected, data_cache, data_trees)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--out", required=True)
    dc = sub.add_parser("data-cache", help="build the OpenML nodes' dataset caches once (ENGINEERING_ONLY)")
    dc.add_argument("--out", required=True)
    dc.add_argument("--tmp", default=os.environ.get("R1_TMP", tempfile.gettempdir()))
    r = sub.add_parser("run")
    mode = r.add_mutually_exclusive_group(required=True)
    mode.add_argument("--stub", action="store_true")
    mode.add_argument("--engineering-smoke", action="store_true")
    mode.add_argument("--evidence", action="store_true")
    r.add_argument("--out", required=True)
    r.add_argument("--stub-shared", type=float, default=0.0, help="stub only: shared share s of the synthetic model")
    r.add_argument("--workers", type=int, default=MAX_WORKERS)
    r.add_argument("--tmp", default=os.environ.get("R1_TMP", tempfile.gettempdir()))
    r.add_argument("--paper-root", default=str(REPO))
    r.add_argument("--note", default=None)
    r.add_argument("--code-commit", default=None)
    r.add_argument("--code-review", default=None)
    r.add_argument("--data-cache", default=None, help="the directory data-cache built (required for harness runs)")
    args = ap.parse_args(argv)
    args.data_cache_sha256 = None

    design = sd.build_design()
    if args.cmd == "plan":
        jobs = plan(design)
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps({"design_sha256": sd.design_sha256(design), "n_runs": len(jobs),
                                              "runs": jobs}, sort_keys=True) + "\n")
        print(json.dumps({"n_runs": len(jobs), "design_sha256": sd.design_sha256(design)}))
        return 0
    if args.cmd == "data-cache":
        Path(args.tmp).mkdir(parents=True, exist_ok=True)
        try:
            print(json.dumps(build_data_cache(design, Path(args.out), args.tmp)))
        except RunStop as exc:
            raise SystemExit(str(exc)) from None
        return 0

    out = Path(args.out)
    if out.exists():
        raise SystemExit("STOP: the output directory exists (a run is never resumed)")
    evidence_root = (Path(args.paper_root) / EVIDENCE_OUT_ROOT).resolve()
    if args.evidence and out.resolve().parent != evidence_root:
        raise SystemExit(f"STOP: evidence output is a new directory directly under {EVIDENCE_OUT_ROOT}/")
    if not args.evidence and str(out.resolve()).startswith(str((REPO / EVIDENCE_OUT_ROOT).resolve())):
        raise SystemExit(f"STOP: {EVIDENCE_OUT_ROOT}/ holds evidence runs only")
    cap = DEEPTHOUGHT2_WORKERS if args.evidence else MAX_WORKERS
    if not 1 <= args.workers <= cap:
        raise SystemExit(f"STOP: workers must be 1..{cap}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    manifest = {"schema": SCHEMA_RUN, "run_id": sd.RUN_ID, "design_sha256": sd.design_sha256(design),
                "seeds": list(sd.SEED_BLOCK), "started_utc": stamp, "stub": bool(args.stub),
                "label": "EVIDENCE" if args.evidence else "ENGINEERING_ONLY",
                "host": {"node": platform.node(), "platform": platform.platform(), "python": platform.python_version(),
                         "cpus": os.cpu_count()},
                "code_sha256": code_pins(REPO), "workers": args.workers}
    runtime_expected = None
    if args.stub and args.data_cache:
        raise SystemExit("STOP: --data-cache is for harness runs, not --stub")
    if args.stub:
        jobs, run_fn = plan(design), stub_runner(design, s=args.stub_shared)
        manifest["stub_shared"] = args.stub_shared
        manifest["note"] = "Synthetic metrics (no harness); ENGINEERING_ONLY; never a result."
    else:
        if not args.data_cache:
            raise SystemExit("STOP: --data-cache is required for a harness run (the declared OpenML caches)")
        from r1.noise import e1_noise_floor as e1
        try:
            dcache = read_data_cache(Path(args.data_cache), data_nodes(design, e1.HARNESS))
        except RunStop as exc:
            raise SystemExit(str(exc)) from None
        args.data_cache_sha256 = dcache["tree_sha256"]
        manifest["data_cache"] = {"dir": str(Path(args.data_cache).resolve()), **dcache}
        if args.evidence:                             # the note and the environment before anything else
            pre = preflight_evidence(args, design)
            manifest["preflight"] = pre
        Path(args.tmp).mkdir(parents=True, exist_ok=not args.evidence)
        from r1.harness import harness_commit
        from r1.noise import e1_noise_floor as e1
        manifest["harness"] = {"root": str(e1.HARNESS), **harness_commit(e1.HARNESS)}
        if manifest["harness"].get("commit") != HARNESS_COMMIT or manifest["harness"].get("dirty"):
            raise SystemExit(f"STOP: the harness must be {HARNESS_COMMIT}, clean")
        manifest["libraries"] = e1.library_versions()
        manifest["edit_sets"] = check_edit_sets(design, args.tmp)
        if args.evidence:
            environment = pre["environment"]
            jobs = plan(design)
        else:
            from r1.c3.audit import evidence_environment
            try:
                environment = evidence_environment(Path(args.paper_root).resolve())
            except ValueError as exc:
                raise SystemExit(f"STOP: engineering smoke requires the evidence runtime: {exc}") from None
            jobs = plan(design, seeds=(SMOKE_SEED,))
            manifest["note"] = "Engineering smoke at seed 999: every configuration runs, edits applied and verified; " \
                               "never a result."
        runtime_expected = {k: environment[k] for k in
                            ("worker_python", "worker_prefix", "worker_versions", "package_list_sha256")}
        if args.engineering_smoke:
            manifest["worker_runtime_expected"] = runtime_expected
        run_fn = functools.partial(_run_with_runtime, runtime_expected=runtime_expected,
                                   data_cache=str(Path(args.data_cache).resolve()), data_trees=dcache["nodes"])
    manifest["seeds"] = sorted({j["seed"] for j in jobs})      # review N6: the seeds actually planned (smoke: 999)
    out.mkdir(parents=True)
    (out / "design.json").write_text(json.dumps(design, indent=1, sort_keys=True) + "\n")
    res = execute(out, jobs, run_fn, manifest, args.workers, None, args.tmp, in_process=args.stub,
                  monitor=not args.stub)
    summary = {k: res[k] for k in ("label", "planned_runs", "written_runs", "failed_runs", "stop", "elapsed_seconds")}
    if args.engineering_smoke:                                 # review M3: flags for the reviewer and the author
        rows = [json.loads(x) for x in (out / RUNS_FILE).read_text().splitlines() if x.strip()]
        res["identity_flags"] = identity_flags(rows, design)
        (out / "manifest.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
        summary["identity_flags"] = len(res["identity_flags"])
    print(json.dumps(summary))
    return 3 if res["stop"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
