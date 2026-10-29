#!/usr/bin/env python3
"""Track S collector: dev campaigns, roots, forks, leaves, audits (runbook rev. 3 §2-§6, rev.-4 amendments).

AI-assisted (Claude, 29 Oct 2026). ENGINEERING_ONLY until a Track S authorization exists; nothing this
collector writes is evidence unless the phase's authorization note says so. One process, serial
(one manager call at a time), resumable per root and per leaf, time-boxed by ``--deadline``.

Phases (``--phase``):

* ``S0.4`` — dev campaigns: every non-rule proposal executed (``ExecuteNonRuleController``) at a
  non-binding W (= the LLM cap; amendment 7), and every executed non-rule proposal (trial >= 2)
  audited at the K = 5 dev seeds (candidate vs incumbent, common seeds). Writes ``s04_rows.jsonl``.
* ``fit_prior`` — fit A2-U's prior from ``s04_rows.jsonl`` (``a2u.fit_prior``); writes
  ``a2u_prior.json`` and prints its sha256.
* ``S0.5b`` — post-processing of an S0.5 output (rev. 6.1 amendment 3): for every root and every W in
  ``--truncate-W``, the incumbent of the root ledger truncated at W worker runs (``truncate_at_W``) is
  audited at the K audit seeds; writes ``s05b_truncated.jsonl``. Valid for budget-blind roots (A2-U).
* ``S0.5`` / ``S3`` / ``synthetic`` — roots under A2-U at the pilot price g0 (amendment 2), fork
  selection, leaves per arm x repetition, A/A leaves, audits. ``synthetic`` runs the synthetic
  control nodes (``--node synthetic_P0|P1|P2p|P2m|N0``) with their scripted managers.
* ``tune`` — the policy-tuning phase (rev.-5 amendment 4, rev.-6 amendment 2): a list of policy strings,
  every configuration on the same paired dev instances (the Track S tuning seed block, disjoint from the
  fresh instances; ``--instances``, 20, 40 after a resize), RootRecords with ``policy``. ``--tune-grid``
  adds the declared grid in units of sigma_cmp,vary (``--sigma-cmp-vary``): static g in {0.05, 0.1, 0.2, 0.4}
  (rev. 6.1; ``--tune-g-extension`` adds 0.8) x h in {-0.25, 0, +0.25}; dynamic members at m*'s (g, h) (``--m-star g,h``, sigma units): budget
  (b_budget = +1), info (b_info = +0.5, dimensionless: it multiplies tau_pred), keep+ (h_budget = +0.5),
  keep- (h_budget = -0.5) (``tuning_grid``).
* ``campaign`` (S3e) — full campaigns on fresh instances under named policies (``--policy``, repeatable),
  every policy on every instance: ``a2u`` (the root rule at g0), ``static:g=<x>,e2off=<y>``,
  ``dynamic:g0=..,b_budget=..,b_info=..,h0=..,h_budget=..`` (the primary candidate family),
  ``matched_static:g=<g_eff>,h=<h_eff>`` (the secondary "matched static" rule; the static rule at those
  values), ``pi_prime:<model_file>`` (secondary). ``--rep`` sets the LLM repetition.

Instance-level seed key (rev.-5 amendment 2): every campaign of one instance (root, A2 root, leaves,
tune/campaign policies) runs under the same harness campaign id and manager ``seed_key``, so it shares
the D26 LLM seeds at the same repetition and the worker, verify and audit seeds; the policy is recorded
in ``RootRecord.policy`` and the root id. E2 verify is off for every Track S policy (declared; the
``--e2-verify`` flag refuses).

Roots and fork selection (§6 S3a). An E1 decision is eligible iff it has features (trial >= 2 with an
incumbent metric), is neither a no-op nor a duplicate, and has a snapshot; an E2 decision iff the trial
was executed, is valid and was eligible at E1. Each eligible decision is drawn independently (Poisson
sampling, so inclusion probabilities are exact): uniform with p_u = min(1, forks / n_eligible(root)),
and, if near the threshold (|V* - g0| <= b at E1, |m_hat| <= b at E2), with p_near; p_select =
1 - (1 - p_u)(1 - p_near 1{near}). A random third of the selected E1 forks (Bernoulli 1/3) gets the
channel arms; a fraction ``--aa-fraction`` gets an A/A leaf. All draws are keyed by
(SELECTION_SEED, fork id), so a resumed run selects the same forks. Every selected fork's controller
decision is rebuilt from its snapshot and compared with the root's (STOP on a mismatch).

Leaves: E1 arms skip, execute (+ ghost, ctrl_only on channel forks); E2 arms keep, discard; each with
repetitions r = 1..R at D26 repetition REP_BASE + r (different LLM seeds; the root is repetition 0).
A/A leaves (arm "aa", rep 0) take the myopic action with the root's repetition and must reproduce the
root (``LeafRecord.aa_reproduced``). Continuations run under an identically built A2-U (stateless).

Audits: every audit uses the same K seeds of the Track S audit block (common seeds), cached per
(node, instance salt, configuration, seed) in ``audit_runs.jsonl``. ``immediate_measured`` =
1{fork trial kept in the leaf} x (mean audit of the kept configuration - mean audit of the branch's
incumbent at the fork) over those seeds (amendment 4).

Outputs in ``--out``: ``roots.jsonl``, ``leaves.jsonl``, ``forks.jsonl``, ``manifest.json``
(``r1.tracks.schema``), ``audit_runs.jsonl``, ``failures/``. Scratch (snapshots, workspaces) in ``--work``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from r1.harness import REPO, harness_commit, import_harness

HARNESS = import_harness()

from autoresearch.control_plane.budget import BudgetState, ComputeBudget  # noqa: E402
from autoresearch.control_plane.campaign import _budget_view, run_real_campaign  # noqa: E402
from autoresearch.control_plane.controller import build_control_view  # noqa: E402
from autoresearch.control_plane.snapshot import (ArmOverride, capture_snapshot, read_snapshot,  # noqa: E402
                                                 resume_campaign, write_snapshot)
from autoresearch.memory.append_store import TrialAppendStore  # noqa: E402
from autoresearch.memory.event_store import CampaignEventStore  # noqa: E402
from autoresearch.memory.schemas import TrialDecision  # noqa: E402
from autoresearch.nodes.registry import load_registered_node  # noqa: E402
from autoresearch.worker.local_worker import LocalWorker  # noqa: E402

from r1.c3.features import NodeContext, apply_edit, replay_campaign  # noqa: E402
from r1.diagnostics.di_test import configuration  # noqa: E402
from r1.tracks import a2u  # noqa: E402
from r1.tracks.schema import (TRACKS_LEAF_SCHEMA, TRACKS_ROOT_SCHEMA, Forecast, LeafRecord, Provenance,  # noqa: E402
                              RootRecord, Selection, to_dict)
from r1.tracks.synthetic import SYNTHETIC_NODES, synthetic_node  # noqa: E402

MANIFEST_SCHEMA = "tracks_manifest/v1"
# ---- the Track S seed block (declared constants) ---------------------------------------------
# Disjoint blocks: S0.4 dev 30000-30249, tune (dev) 30250-30499, S0.5 30500-30999, S3 31000-31999,
# campaign (fresh instances, S3e) 32000-32999, synthetic 36000-36999, fixtures 39000+.
INSTANCE_SEED_BASE = {"S0.4": 30000, "tune": 30250, "S0.5": 30500, "S3": 31000, "campaign": 32000,
                      "synthetic": 36000, "fixture": 39000}
DEV_AUDIT_SEEDS = tuple(range(33001, 33006))     # S0.4 dev block, K = 5
AUDIT_SEEDS = tuple(range(34001, 34021))         # Track S audit block; the first K are used
SELECTION_SEED = 35001
REP_BASE = 100                                    # leaf repetition r -> D26 repetition REP_BASE + r
CHANNEL_FRACTION = 1.0 / 3.0
A2_FRACTION_DEFAULT = 0.2                        # descriptive A2 roots (S3 only)
DEFAULT_LLM_CAP = 40
DEFAULT_REPS = 2
DEFAULT_K = 5
G_UNITS = 0.1                                     # declared g = 0.1 sigma_node unless --g (C3 convention)
# sigma_node (median paired sd Delta-hat), runbook §1 B2 (NOISE_FLOOR_COMMON_20261022); a prior file overrides.
SIGMA_NODE_DEFAULTS = {"digits_mlp": 0.0066, "tabular_mlp": 0.0019}
PHASES = ("S0.4", "fit_prior", "S0.5", "S0.5b", "S3", "synthetic", "tune", "campaign")
POLICY_PHASES = ("tune", "campaign")
E1_LEAF_ARMS = ("skip", "execute")
E1_CHANNEL_ARMS = ("ghost", "ctrl_only")
E2_LEAF_ARMS = ("keep", "discard")


class Stop(RuntimeError):
    """A runbook §10 STOP condition (never retried automatically)."""


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _u(*parts) -> np.ndarray:
    """Four uniforms keyed by (SELECTION_SEED, parts) — deterministic across sessions."""
    h = int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:12], 16)
    return np.random.default_rng([SELECTION_SEED, h]).random(4)


def cfg_hash(files: dict[str, str]) -> str:
    return hashlib.sha256(json.dumps(configuration(files), sort_keys=True, default=str).encode()).hexdigest()[:20]


def read_jsonl(path: Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def append_jsonl(path: Path, row: dict) -> None:
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str) + "\n")


def failure_details(exc: BaseException, stage: str) -> dict:
    return {"error_class": f"{type(exc).__module__}.{type(exc).__qualname__}", "error_message": str(exc),
            "traceback": "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
            "failed_utc": utc(), "failure_stage": stage}


# ---------------------------------------------------------------------------
# Node adapters
# ---------------------------------------------------------------------------

class RealNode:
    """A harness node (LocalWorker, the node's own benchmark, r1.c3.audit runs)."""

    synthetic = False

    def __init__(self, name: str, manager_cfg: dict) -> None:
        self.name = self.surface = name
        self.spec = load_registered_node(name, repo_root=HARNESS)
        self.manager_cfg = manager_cfg

    def start_files(self) -> dict[str, str]:
        return {p: (HARNESS / "nodes" / self.name / p).read_text() for p in self.spec.editable_paths}

    def copy(self, dest: Path) -> Path:
        from r1.headroom.e1b_collect import _node_copy
        return _node_copy(self.name, dest)

    def worker(self, node_dir: Path, seed: int, art: Path):
        return LocalWorker(node_root=node_dir, artifact_dir=art, train_seed=seed, split_seed=seed)

    def leaf_worker(self, into: Path, snapshot):
        return None  # restore_snapshot rebuilds the LocalWorker with the snapshot's seeds

    def manager(self, seed: int, repetition: int, seed_key: str | None = None):
        cfg = self.manager_cfg
        if cfg.get("kind") == "langgraph":
            from autoresearch.manager.langgraph_manager import LangGraphManager
            from r1.headroom.e1b_collect import transport_policy
            return LangGraphManager(model=cfg["model"], temperature=float(cfg["temperature"]), repetition=repetition,
                                    transport_retry=transport_policy(cfg), seed_key=seed_key,
                                    **({"proposal_schema": cfg["proposal_schema"]} if cfg.get("proposal_schema") else {}))
        from r1.headroom.e1b_collect import make_manager
        return make_manager(self.name, seed, repetition, cfg)  # the scripted stand-in (keyed by the instance seed)

    def audit(self, salt: int, files: dict[str, str], seeds, work: Path) -> list[float | None]:
        from r1.c3.audit import run_config
        work.mkdir(parents=True, exist_ok=True)
        return [r["metric"] for r in run_config(self.name, files, list(seeds), str(work))]

    def default_sigma_node(self) -> float | None:
        return SIGMA_NODE_DEFAULTS.get(self.name)


class SynthNode:
    """A synthetic control node (``r1.tracks.synthetic``) on the digits_mlp editable surface."""

    synthetic = True

    def __init__(self, name: str, params: dict | None) -> None:
        self.node = synthetic_node(name, params)
        self.name, self.surface = name, self.node.surface
        self.spec = load_registered_node(self.surface, repo_root=HARNESS)

    def start_files(self) -> dict[str, str]:
        return {p: (HARNESS / "nodes" / self.surface / p).read_text() for p in self.spec.editable_paths}

    def copy(self, dest: Path) -> Path:
        shutil.copytree(HARNESS / "nodes" / self.surface, dest,
                        ignore=shutil.ignore_patterns("__pycache__", ".autoresearch_artifacts", "artifacts"))
        return dest

    def worker(self, node_dir: Path, seed: int, art: Path):
        return self.node.worker(node_dir, seed)

    def leaf_worker(self, into: Path, snapshot):
        return self.node.worker(into, int(snapshot.train_seed))

    def manager(self, seed: int, repetition: int, seed_key: str | None = None):
        return self.node.manager(seed, repetition)  # scripted: keyed by the instance seed

    def audit(self, salt: int, files: dict[str, str], seeds, work: Path) -> list[float | None]:
        return self.node.audit(salt, files, seeds)

    def default_sigma_node(self) -> float | None:
        return self.node.sigma_node


def make_adapter(node: str, manager_cfg: dict, synthetic_params: dict | None):
    if node in SYNTHETIC_NODES:
        return SynthNode(node, synthetic_params)
    return RealNode(node, manager_cfg)


# ---------------------------------------------------------------------------
# Audit cache
# ---------------------------------------------------------------------------

class AuditCache:
    def __init__(self, path: Path, adapter, work: Path) -> None:
        self.path, self.adapter, self.work = Path(path), adapter, Path(work)
        self.rows: dict[tuple, float | None] = {}
        for r in read_jsonl(self.path):
            self.rows[(r["node"], int(r["salt"]), r["config_hash"], int(r["seed"]))] = r["metric"]
        self.runs = 0

    def metrics(self, salt: int, files: dict[str, str], seeds) -> list[float | None]:
        salt = int(salt) if self.adapter.synthetic else 0  # real-node audits do not depend on the instance
        h = cfg_hash(files)
        missing = [s for s in seeds if (self.adapter.name, salt, h, int(s)) not in self.rows]
        if missing:
            values = self.adapter.audit(salt, files, missing, self.work / "audit_tmp")
            self.runs += len(missing)
            for s, v in zip(missing, values):
                self.rows[(self.adapter.name, salt, h, int(s))] = v
                append_jsonl(self.path, {"node": self.adapter.name, "salt": salt, "config_hash": h, "seed": int(s),
                                         "metric": v})
        return [self.rows[(self.adapter.name, salt, h, int(s))] for s in seeds]


def _mean(values) -> float | None:
    v = [x for x in values if x is not None]
    return float(np.mean(v)) if v and len(v) == len(values) else None


def paired_increment(cand: list, inc: list) -> float | None:
    d = [c - i for c, i in zip(cand, inc) if c is not None and i is not None]
    return float(np.mean(d)) if d and len(d) == len(cand) else None


# ---------------------------------------------------------------------------
# Run context
# ---------------------------------------------------------------------------

@dataclass
class Run:
    args: Any
    adapter: Any
    out: Path
    work: Path
    manifest: dict
    prior: a2u.A2UPrior | None
    prior_sha: str
    sigma_node: float
    g_declared: float
    g0: float
    provenance: Provenance
    audits: AuditCache
    t0: float

    @property
    def W(self) -> int:
        return int(self.manifest["W"])

    @property
    def cap(self) -> int:
        return int(self.manifest["llm_cap"])

    @property
    def seeds(self) -> tuple:
        return tuple(self.manifest["audit_seeds"])

    def time_left(self) -> bool:
        return time.time() - self.t0 < float(self.args.deadline)

    def node_ctx(self) -> NodeContext:
        return NodeContext(node=self.adapter.surface, start_files=self.adapter.start_files(),
                           sigma_node=self.sigma_node, runs_total=self.W,
                           memory_mode=self.manifest["memory_mode"])

    def controller(self, policy: str | None = None):
        """The root / continuation controller (A2-U at g0), or a named S3e policy."""
        ctx = self.node_ctx()
        lam = float(self.manifest.get("obs_inflation", 1.0))
        if self.manifest["phase"] == "S0.4":
            return a2u.ExecuteNonRuleController(self.prior, ctx, obs_inflation=lam)
        return policy_controller(policy or "a2u", self.prior, ctx, g0=self.g0, obs_inflation=lam, W=self.W)


def _kv(policy: str, prefix: str, allowed: set, required: set) -> dict:
    kv = dict(item.split("=", 1) for item in policy[len(prefix):].split(",") if item)
    if set(kv) - allowed or required - set(kv):
        raise ValueError(f"{prefix[:-1]} policy takes {sorted(allowed)} (required {sorted(required)}), got {policy!r}")
    return {k: float(v) for k, v in kv.items()}


def policy_controller(policy: str, prior, ctx, *, g0: float, obs_inflation: float = 1.0, W: int | None = None):
    """Named policies: ``a2u``, ``a2`` (no update), ``static:g=<x>,e2off=<y>``,
    ``dynamic:g0=..,b_budget=..,b_info=..,h0=..,h_budget=..``, ``pi_prime:<model_file>``."""
    if policy == "a2u":
        return a2u.A2UController(prior, ctx, g=g0, obs_inflation=obs_inflation, W=W)
    if policy == "a2":
        return a2u.A2UController(prior, ctx, g=g0, update=False, obs_inflation=obs_inflation, W=W)
    if policy.startswith("static:"):
        kv = _kv(policy, "static:", {"g", "e2off"}, {"g"})
        return a2u.A2UController.static_price(prior, ctx, kv["g"], e2_offset=kv.get("e2off", 0.0),
                                              obs_inflation=obs_inflation, W=W, policy_name=policy)
    if policy.startswith("matched_static:"):
        kv = _kv(policy, "matched_static:", {"g", "h"}, {"g", "h"})
        return a2u.A2UController.static_price(prior, ctx, kv["g"], e2_offset=kv["h"], obs_inflation=obs_inflation,
                                              W=W, policy_name=policy)
    if policy.startswith("dynamic:"):
        kv = _kv(policy, "dynamic:", {"g0", "b_budget", "b_info", "h0", "h_budget"}, {"g0"})
        return a2u.A2UController.dynamic(prior, ctx, **kv, obs_inflation=obs_inflation, W=W, policy_name=policy)
    if policy.startswith("pi_prime:"):
        model, sha = a2u.RidgeScore.load(policy[len("pi_prime:"):])
        return a2u.A2UController(prior, ctx, g=g0, score_fn=model, obs_inflation=obs_inflation, W=W,
                                 policy_name=f"pi_prime:{sha[:12]}")
    raise ValueError(f"unknown or unimplemented policy {policy!r} (budget_dp / probe_first are not implemented)")


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------

def _git(repo: Path, *args) -> str:
    try:
        return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:  # noqa: BLE001 - provenance is best effort, recorded as unknown
        return "unknown"


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def gpu_label(explicit: str | None) -> str:
    if explicit:
        return explicit
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], capture_output=True,
                             text=True, timeout=10)
        names = [line.strip() for line in out.stdout.splitlines() if line.strip()]
        return "; ".join(names) if out.returncode == 0 and names else "none"
    except Exception:  # noqa: BLE001
        return "none"


def llama_build(args) -> str:
    if args.llama_build:
        return args.llama_build
    if args.llama_server_bin:
        try:
            out = subprocess.run([args.llama_server_bin, "--version"], capture_output=True, text=True, timeout=30)
            line = [l for l in (out.stdout + out.stderr).splitlines() if l.startswith("version:")]
            return line[0].strip() if line else "unknown"
        except Exception:  # noqa: BLE001
            return "unknown"
    return "none"


def cpu_census() -> dict:
    try:
        load = os.getloadavg()
    except OSError:
        load = (math.nan,) * 3
    return {"cpus": os.cpu_count(), "loadavg": list(load), "platform": platform.platform(),
            "python": platform.python_version()}


# ---------------------------------------------------------------------------
# Roots
# ---------------------------------------------------------------------------

class AllSnapshots:
    """Snapshot hook: every E1 and E2 snapshot of a root, under ``<dir>/E1_b003`` etc."""

    def __init__(self, out_dir: Path) -> None:
        self.out_dir, self.written = Path(out_dir), {}

    def __call__(self, context) -> None:
        if context.epoch not in ("E1", "E2"):
            return
        target = self.out_dir / f"{context.epoch}_b{context.budget_index:03d}"
        write_snapshot(capture_snapshot(context), target)
        self.written[(context.epoch, int(context.budget_index))] = str(target)


def instance_seed(run: Run, k: int) -> int:
    return int(run.manifest["seed_base"]) + int(k)


def campaign_id_for(run: Run, seed: int, variant: str = "") -> str:
    tag = run.manifest["phase"].replace(".", "")
    return f"tracks_{tag}{variant}_{run.adapter.name}__s{seed}"


def _events(path: Path) -> list[dict]:
    return read_jsonl(path)


def decisions_from(rows: list[dict], events: list[dict], snapshots: dict) -> list[dict]:
    """Per-trial E1/E2 decisions of a campaign from its ledger and ``control_decision`` events."""
    by_trial: dict[int, dict] = {}
    for e in events:
        if e.get("event_type") != "control_decision":
            continue
        b = int(str(e["trial_id"]).rsplit("-trial-", 1)[1])
        by_trial.setdefault(b, {})[e["payload"]["epoch"]] = e["payload"]
    out = []
    for row in rows:
        b = int(row["budget_index"])
        ev = by_trial.get(b, {})
        e1 = ev.get("E1")
        if e1 is not None:
            d = e1.get("detail") or {}
            eligible = bool(d.get("eligible")) and b >= 2 and ("E1", b) in snapshots
            out.append({"index": b, "epoch": "E1", "action": "skip" if e1["action"] == "skip" else "execute",
                        "index_value": d.get("v_star"), "eligible": eligible, "skip_reason": d.get("skip_reason"),
                        "detail": d})
        e2 = ev.get("E2")
        if e2 is not None:
            d = e2.get("detail") or {}
            e1_ok = bool(((ev.get("E1") or {}).get("detail") or {}).get("eligible"))
            eligible = bool(d.get("eligible")) and e1_ok and row.get("validity_status") == "valid" \
                and ("E2", b) in snapshots
            out.append({"index": b, "epoch": "E2", "action": "keep" if row["decision"] == "kept" else "discard",
                        "index_value": d.get("m_hat"), "eligible": eligible, "detail": d})
    return out


def config_after(rows: list[dict], start_files: dict[str, str], upto: int) -> dict[str, str]:
    """Incumbent editable files after trial ``upto`` (kept edits replayed as the worker applies them)."""
    files = dict(start_files)
    for row in rows:
        if int(row["budget_index"]) > upto:
            break
        edit = ((row.get("extra") or {}).get("manager") or {}).get("structured_edit")
        if row["decision"] == "kept" and edit:
            files = apply_edit(files, edit)
    return files


def _workspace_files(adapter, node_dir: Path) -> dict[str, str]:
    return {p: (node_dir / p).read_text() for p in adapter.spec.editable_paths}


def run_root(run: Run, k: int, *, policy: str | None = None, variant: str = "", repetition: int = 0) -> dict:
    """One root (or S3e policy) campaign; returns the RootRecord dict (status 'failed' on error)."""
    adapter = run.adapter
    seed = instance_seed(run, k)
    cid = campaign_id_for(run, seed)              # harness campaign id = the instance's seed key
    root_id = campaign_id_for(run, seed, variant)  # unique per policy
    root_dir = run.work / "roots" / root_id
    if root_dir.exists():
        shutil.rmtree(root_dir)  # an interrupted root is re-run whole, never patched
    root_dir.mkdir(parents=True)
    node_dir = adapter.copy(root_dir / "node")
    worker = adapter.worker(node_dir, seed, root_dir / "art")
    controller = run.controller(policy)
    snaps = AllSnapshots(root_dir / "snapshots") if run.manifest["phase"] in ("S0.5", "S3", "synthetic") \
        and not variant else None
    manager = adapter.manager(seed, repetition, seed_key=cid)
    base = dict(schema=TRACKS_ROOT_SCHEMA, node=adapter.name, instance_id=f"{adapter.name}__s{seed}", root_id=root_id,
                W=run.W, llm_cap=run.cap, provenance=_prov(run, controller), policy=policy or "a2u:g0")
    try:
        run_real_campaign(
            node_spec=adapter.spec, campaign_id=cid, manager_mode=getattr(manager, "mode", "manager"),
            memory_mode=run.manifest["memory_mode"], records_path=root_dir / "root_trials.jsonl", worker=worker,
            proposal_backend=manager, snapshot_hook=snaps,
            event_store=CampaignEventStore(root_dir / "root_events.jsonl"),
            **controller.campaign_kwargs(W=run.W, llm_cap=run.cap, skip_display=run.manifest["skip_display"]))
        rows = read_jsonl(root_dir / "root_trials.jsonl")
        events = _events(root_dir / "root_events.jsonl")
        decisions = decisions_from(rows, events, snaps.written if snaps else {})
        start = adapter.start_files()
        y_start = _mean(run.audits.metrics(seed, start, run.seeds))
        y1 = _mean(run.audits.metrics(seed, config_after(rows, start, 1), run.seeds)) if rows else None
        final = _workspace_files(adapter, node_dir)
        y_seeds = run.audits.metrics(seed, final, run.seeds)
        runs_used = worker_runs_of(rows, events)
        llm_calls = sum(1 for e in events if e.get("event_type") == "llm_call"
                        and (e.get("payload") or {}).get("purpose") != "self_forecast")
        rec = RootRecord(**base, y_start=y_start, y_after_trial1=y1, y_terminal=_mean(y_seeds),
                         eligible_e1=sum(1 for d in decisions if d["epoch"] == "E1" and d["eligible"]),
                         eligible_e2=sum(1 for d in decisions if d["epoch"] == "E2" and d["eligible"]),
                         binding=runs_used >= run.W, runs_used=runs_used, llm_calls=llm_calls,
                         decisions=[{k_: v for k_, v in d.items() if k_ != "detail"} for d in decisions])
        out = to_dict(rec)
        out["_snapshots"] = {f"{e}_b{b:03d}": p for (e, b), p in (snaps.written.items() if snaps else ())}
        out["_decision_details"] = {f"{d['epoch']}_b{d['index']:03d}": d["detail"] for d in decisions}
        out["_y_terminal_per_seed"] = y_seeds
        out["_seed"] = seed
        if run.manifest["phase"] == "S0.4":
            dev_rows(run, rows, seed, cid)
        return out
    except Exception as exc:  # noqa: BLE001 - a failed root is an integrity status, never a utility
        details = failure_details(exc, "root_campaign")
        _write_failure(run.out, "root", root_id, details)
        rec = RootRecord(**base, y_start=None, y_after_trial1=None, y_terminal=None, eligible_e1=0, eligible_e2=0,
                         binding=False, runs_used=0, llm_calls=0, status="failed", error=details["error_message"])
        return {**to_dict(rec), "_seed": seed}


def truncate_at_W(rows: list[dict], W: int) -> tuple[list[dict], bool]:
    """The ledger prefix a campaign at budget W would have written, and whether W binds.

    Trials are kept while fewer than W worker runs were used before them (the loop's stopping rule); a trial
    whose own run is the W-th is included. Valid for a root whose controller does not read the budget."""
    out, runs = [], 0
    for r in rows:
        if runs >= W:
            return out, True
        out.append(r)
        runs += worker_runs_of([r], [])
    return out, runs >= W


def s05b_phase(args) -> int:
    out, work = Path(args.out), Path(args.work)
    manifest = json.loads((out / "manifest.json").read_text())
    adapter = make_adapter(manifest["node"], manifest.get("manager") or {}, manifest.get("synthetic_params"))
    audits = AuditCache(out / "audit_runs.jsonl", adapter, work)
    seeds = tuple(manifest["audit_seeds"])
    Ws = [int(w) for w in str(args.truncate_W).split(",")]
    done = {(r["root_id"], r["W"]) for r in read_jsonl(out / "s05b_truncated.jsonl")}
    start = adapter.start_files()
    n = 0
    for root in read_jsonl(out / "roots.jsonl"):
        if root.get("status") != "ok":
            continue
        rows = read_jsonl(work / "roots" / root["root_id"] / "root_trials.jsonl")
        seed = int(root["instance_id"].rsplit("__s", 1)[1])
        for W in Ws:
            if (root["root_id"], W) in done:
                continue
            if W > int(root["W"]):
                raise SystemExit(f"cannot truncate a W={root['W']} root at W={W}")
            prefix, binding = truncate_at_W(rows, W)
            files = config_after(prefix, start, int(prefix[-1]["budget_index"])) if prefix else start
            ys = audits.metrics(seed, files, seeds)
            append_jsonl(out / "s05b_truncated.jsonl", {
                "root_id": root["root_id"], "instance_id": root["instance_id"], "W": W, "binding": binding,
                "trials": len(prefix), "runs_used": worker_runs_of(prefix, []), "y_terminal": _mean(ys),
                "y_terminal_per_seed": ys, "audit_seeds": list(seeds), "label": manifest.get("label")})
            n += 1
    print(json.dumps({"out": str(out), "truncated_audits": n}))
    return 0


def worker_runs_of(rows: list[dict], events: list[dict], first_run_before: bool = False) -> int:
    """Worker runs a ledger segment spent: executed trials (not precondition failures) + verify re-runs."""
    runs = 0
    for i, r in enumerate(rows):
        if r.get("decision") == "skipped":
            continue
        if str(r.get("worker_mode", "")).endswith("_precheck"):
            continue
        if not (first_run_before and i == 0):
            runs += 1
        v = ((r.get("extra") or {}).get("control") or {}).get("verify")
        if v:
            runs += 2 * int(v.get("r", 2))
    return runs


def _write_failure(out: Path, kind: str, ident: str, payload: dict) -> None:
    target = out / "failures" / f"{kind}__{ident}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target = target.with_name(target.stem + f"__{time.time_ns()}.json")
    target.write_text(json.dumps(payload, indent=2) + "\n")


def _prov(run: Run, controller) -> Provenance:
    p = run.provenance
    return Provenance(**{**to_dict(p), "controller_version": controller.version})


# ---------------------------------------------------------------------------
# S0.4 dev rows
# ---------------------------------------------------------------------------

def dev_rows(run: Run, rows: list[dict], seed: int, cid: str) -> None:
    """Audit every executed non-rule proposal of a dev campaign at the dev seeds (candidate vs incumbent)."""
    proposals, _ = replay_campaign(rows, run.adapter.start_files(), run.adapter.surface, cid, "tracks_S0.4",
                                   run.manifest["memory_mode"], run.W, run.sigma_node, check=False)
    from r1.c3.control import edit_kind
    for p in proposals:
        if p.outcome["noop"] or p.outcome["duplicate"]:
            continue
        cand = run.audits.metrics(seed, p.candidate_files, DEV_AUDIT_SEEDS)
        inc = run.audits.metrics(seed, p.incumbent_files, DEV_AUDIT_SEEDS)
        d = [c - i for c, i in zip(cand, inc) if c is not None and i is not None]
        append_jsonl(run.out / "s04_rows.jsonl", {
            "node": run.adapter.name, "instance": cid, "budget_index": p.budget_index,
            "key": p.edit.get("symbol"), "sign": a2u.sign_of(p.features.get("direction")),
            "kind": edit_kind(p.edit), "delta_hat": p.outcome["delta_hat"],
            "delta_audit": float(np.mean(d)) if d else None,
            "se": float(np.std(d, ddof=1) / np.sqrt(len(d))) if len(d) > 1 else None, "k": len(d),
            "seeds": list(DEV_AUDIT_SEEDS)})


# ---------------------------------------------------------------------------
# Fork selection
# ---------------------------------------------------------------------------

def _snapshot_view(snap, node_spec, *, epoch: str):
    return build_control_view(
        epoch=epoch, budget_index=snap.budget_index, ledger_prefix=list(snap.ledger_prefix),
        current_best=snap.current_best, incumbent_stack_depth=len(snap.incumbent_stack),
        proposal=snap.proposal, provisional=snap.provisional if epoch == "E2" else None,
        budget=_budget_view(BudgetState(total_trials=snap.budget_total, consumed_trials=snap.budget_consumed),
                            ComputeBudget(**{k: snap.compute_budget_state.get(k) for k in (
                                "max_worker_runs", "max_worker_seconds", "max_llm_calls")},
                                          worker_runs=int(snap.compute_budget_state.get("worker_runs", 0)),
                                          worker_seconds=float(snap.compute_budget_state.get("worker_seconds", 0.0)),
                                          llm_calls=int(snap.compute_budget_state.get("llm_calls", 0)))),
        node=node_spec)


def fork_state(run: Run, snap, epoch: str, controller) -> tuple[dict, Forecast, str | None]:
    """State features, forecast and the rebuilt myopic action of a fork, from its snapshot alone."""
    view = _snapshot_view(snap, run.adapter.spec, epoch=epoch)
    fc = controller.forecast(view)
    if fc is None:
        raise Stop(f"fork at {epoch} b{snap.budget_index} has no forecast")
    m_hat = None
    if epoch == "E2":
        dh = snap.provisional.delta_vs_best
        m_hat = a2u.posterior_mean(dh, fc["mu"], fc["tau"], fc["sigma"]) if dh is not None else None
    index_value = fc["v_star"] if epoch == "E1" else m_hat
    state = a2u.state_features(view, fc["rep"], key=fc["key"], index_value=index_value, W=run.W)
    forecast = Forecast(pi=fc["pi"], mu=fc["mu"], tau=fc["tau"], sigma=fc["sigma"], v_star=fc["v_star"],
                        m_hat=m_hat, g=controller.g)
    if epoch == "E1":
        decision = controller.decide(view, {"continue": True, "skip": True})
        rebuilt = "skip" if decision.action == "skip" else "execute"
    else:
        prior = controller.keep_prior(view)
        dh = snap.provisional.delta_vs_best
        rebuilt = "keep" if dh is not None and dh > prior.threshold else "discard"
    return state, forecast, rebuilt


def selection_draw(fork_id: str, *, epoch: str, p_u: float, near: bool, p_near: float,
                   aa_fraction: float) -> dict | None:
    """The Poisson-sampling draw of one eligible decision (``None`` = not selected).

    uniform iff u0 < p_u; oversample iff near and u1 < p_near; p_select = 1 - (1 - p_u)(1 - p_near 1{near});
    channel arms (E1 only) iff u2 < 1/3; A/A iff u3 < aa_fraction. u = ``_u(fork_id)``."""
    u = _u(fork_id)
    uni, over = bool(u[0] < p_u), bool(near and u[1] < p_near)
    if not (uni or over):
        return None
    return {"selection": {"uniform": uni, "oversample": over,
                          "p_select": 1.0 - (1.0 - p_u) * (1.0 - (p_near if near else 0.0)),
                          "channel_arms": bool(epoch == "E1" and u[2] < CHANNEL_FRACTION)},
            "aa": bool(u[3] < aa_fraction)}


def binding_shares(roots: list[dict], Ws=(8, 10, 12, 20)) -> dict:
    """S0.5 (ii): share of root campaigns in which W would bind, from roots run at W >= max(Ws).

    Valid because A2-U's decisions do not read the budget: a campaign at a smaller W follows the same
    trajectory until its W-th run, so W binds iff the large-W root used >= W runs."""
    ok = [r for r in roots if r.get("status") == "ok"]
    if any(int(r["W"]) < max(Ws) for r in ok):
        raise ValueError("binding shares need roots run at W >= max(Ws)")
    return {int(W): (float(np.mean([r["runs_used"] >= W for r in ok])) if ok else None) for W in Ws}


def select_forks(run: Run, root: dict) -> list[dict]:
    """Poisson-sample the eligible decisions of a root (module docstring); writes forks.jsonl rows."""
    eligible = [d for d in root["decisions"] if d["eligible"]]
    n = len(eligible)
    p_u = min(1.0, float(run.manifest["forks"]) / n) if n else 0.0
    band, p_near = run.manifest.get("near_band"), float(run.manifest.get("p_near", 0.0))
    forks = []
    controller = run.controller()
    for d in eligible:
        fork_id = f"{root['root_id']}__{d['epoch']}_b{d['index']:03d}"
        iv = d.get("index_value")
        near = band is not None and iv is not None and (
            abs(iv - run.g0) <= float(band) if d["epoch"] == "E1" else abs(iv) <= float(band))
        draw = selection_draw(fork_id, epoch=d["epoch"], p_u=p_u, near=near, p_near=p_near,
                              aa_fraction=float(run.manifest.get("aa_fraction", 0.0)))
        if draw is None:
            continue
        snap_dir = root["_snapshots"][f"{d['epoch']}_b{d['index']:03d}"]
        snap = read_snapshot(snap_dir)
        state, forecast, rebuilt = fork_state(run, snap, d["epoch"], controller)
        if rebuilt != d["action"]:
            _write_failure(run.out, "rebuild", fork_id, {"root_action": d["action"], "rebuilt": rebuilt})
            raise Stop(f"STOP (runbook §10): controller rebuild differs from the root at {fork_id}: "
                       f"root {d['action']!r}, rebuilt {rebuilt!r}")
        forks.append({"fork_id": fork_id, "root_id": root["root_id"], "instance_id": root["instance_id"],
                      "seed": root["_seed"], "epoch": d["epoch"], "index": d["index"], "snapshot_dir": snap_dir,
                      **draw, "near": bool(near), "myopic_action": d["action"], "skip_reason": d.get("skip_reason"),
                      "state": state, "forecast": to_dict(forecast)})
    return forks


def prune_snapshots(root: dict, keep: set[str]) -> None:
    for path in root.get("_snapshots", {}).values():
        if path not in keep and Path(path).exists():
            shutil.rmtree(path, ignore_errors=True)


# ---------------------------------------------------------------------------
# Leaves
# ---------------------------------------------------------------------------

def leaf_arms(fork: dict, reps: int) -> list[tuple[str, int]]:
    arms = list(E1_LEAF_ARMS) if fork["epoch"] == "E1" else list(E2_LEAF_ARMS)
    if fork["epoch"] == "E1" and fork["selection"]["channel_arms"]:
        arms += list(E1_CHANNEL_ARMS)
    out = [(arm, r) for arm in arms for r in range(1, reps + 1)]
    if fork["aa"]:
        out.append(("aa", 0))
    return out


def _override(fork: dict, arm: str) -> tuple[ArmOverride | None, str | None]:
    """(arm override, first_action) of a leaf. A/A: the myopic action (no override at E2 and for an execute)."""
    if arm == "aa":
        if fork["epoch"] == "E1" and fork["myopic_action"] == "skip":
            return ArmOverride("skip", skip_reason=fork.get("skip_reason")), None
        return None, "continue"
    if arm == "skip":
        return ArmOverride("skip", skip_reason="prior_no_gain"), None
    return ArmOverride(arm), None


def _signature(rows: list[dict]) -> list[tuple]:
    return [(int(r["budget_index"]), r["decision"], r["proposal_summary"],
             json.dumps(r.get("parsed_metrics") or {}, sort_keys=True)) for r in rows]


def _e1_details(events: list[dict]) -> dict[int, dict]:
    out = {}
    for e in events:
        if e.get("event_type") == "control_decision" and e["payload"].get("epoch") == "E1":
            out[int(str(e["trial_id"]).rsplit("-trial-", 1)[1])] = e["payload"].get("detail") or {}
    return out


def _next_proposals(after: list[dict], details: dict[int, dict]) -> list[dict]:
    out = []
    for r in after[:3]:
        edit = ((r.get("extra") or {}).get("manager") or {}).get("structured_edit") or {}
        step = None
        try:
            step = math.log(float(edit["new"]) / float(edit["old"]))
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            step = None
        d = details.get(int(r["budget_index"]), {})
        out.append({"key": edit.get("symbol"), "value": edit.get("new"), "step": step,
                    "duplicate": bool(d.get("duplicate")), "noop": bool(d.get("noop"))})
    return out


def run_leaf(run: Run, fork: dict, arm: str, rep: int, root_rows: list[dict]) -> dict:
    adapter = run.adapter
    snap = read_snapshot(fork["snapshot_dir"])
    leaf_id = f"{fork['fork_id']}__{arm}__r{rep}"
    into = run.work / "leaves" / leaf_id
    if into.exists():
        shutil.rmtree(into)
    repetition = 0 if arm == "aa" else REP_BASE + rep
    controller = run.controller()
    override, first_action = _override(fork, arm)
    selection = Selection(**fork["selection"])
    forecast = Forecast(**fork["forecast"])
    base = dict(schema=TRACKS_LEAF_SCHEMA, node=adapter.name, instance_id=fork["instance_id"],
                root_id=fork["root_id"], fork_id=fork["fork_id"], epoch=fork["epoch"],
                fork_trial_index=int(fork["index"]), arm=arm, rep=rep, llm_seed_base=repetition,
                myopic_action=fork["myopic_action"], selection=selection, state=fork["state"], forecast=forecast,
                audit_seeds=list(run.seeds), provenance=_prov(run, controller), policy="a2u:g0")
    try:
        result = resume_campaign(
            snap, into, arm=override, first_action=first_action, policy=controller,
            horizon=max(snap.budget_total - snap.budget_consumed - 1, 0), worker=adapter.leaf_worker(into, snap),
            manager=adapter.manager(int(fork["seed"]), repetition, seed_key=snap.campaign_id),
            keep_prior=controller.keep_prior)
        rows = read_jsonl(result.restored.records_path)
        events = read_jsonl(result.restored.events_path)
        new = rows[len(snap.ledger_prefix):]
        first, after = new[0], new[1:]
        details = _e1_details(events)
        seed = int(fork["seed"])
        final = _workspace_files(adapter, into)
        y_seeds = run.audits.metrics(seed, final, run.seeds)
        immediate = 0.0
        if first["decision"] == "kept":
            inc_files = {k: v.decode() for k, v in snap.incumbent_files.items() if v is not None}
            if fork["epoch"] == "E2":
                cand_files = {k: v.decode() for k, v in snap.editable_files.items() if v is not None}
            else:
                cand_files = apply_edit(inc_files, snap.proposal.extra["structured_edit"])
            immediate = paired_increment(run.audits.metrics(seed, cand_files, run.seeds),
                                         run.audits.metrics(seed, inc_files, run.seeds))
        e2 = fork["epoch"] == "E2"
        # Runs after the fork, the fork trial's own run included (at E2 it was spent before the snapshot).
        runs_before = int(snap.compute_budget_state.get("worker_runs", 0)) - (1 if e2 else 0)
        runs_used = worker_runs_of(new, events)
        shadow = result.shadow_record
        if shadow is not None and not str(shadow.worker_mode).endswith("_precheck"):
            runs_used += 1
        llm_calls = sum(1 for e in events if e.get("event_type") == "llm_call"
                        and (e.get("payload") or {}).get("purpose") != "self_forecast")
        dup_due = sum(1 for b, d in details.items() if b > int(fork["index"])
                      and d.get("skip_reason") == "rule_duplicate" and d.get("duplicate_of") == int(fork["index"]))
        aa_ok = None
        if arm == "aa":
            root_after = [r for r in root_rows if int(r["budget_index"]) >= int(fork["index"])]
            aa_ok = _signature(new) == _signature(root_after)
        rec = LeafRecord(**base, immediate_measured=float(immediate) if immediate is not None else math.nan,
                         y_terminal=_mean(y_seeds), y_terminal_per_seed=y_seeds, runs_used=runs_used,
                         llm_calls=llm_calls, keeps_after=sum(1 for r in after if r["decision"] == "kept"),
                         binding=runs_before + runs_used >= run.W, nf_c_events=0, dup_filtered_due_to_fork=dup_due,
                         next_proposals=_next_proposals(after, details), aa_reproduced=aa_ok)
        _slim_leaf_dir(into)
        if arm == "aa" and not aa_ok:
            _write_failure(run.out, "aa", leaf_id, {"leaf": _signature(new), "root": _signature(
                [r for r in root_rows if int(r["budget_index"]) >= int(fork["index"])])})
        return to_dict(rec)
    except Stop:
        raise
    except Exception as exc:  # noqa: BLE001 - a failed leaf is an integrity status
        details = failure_details(exc, "leaf")
        _write_failure(run.out, "leaf", leaf_id, details)
        rec = LeafRecord(**base, immediate_measured=math.nan, y_terminal=None, y_terminal_per_seed=[], runs_used=0,
                         llm_calls=0, keeps_after=0, binding=False, nf_c_events=0, dup_filtered_due_to_fork=0,
                         next_proposals=[], status="failed", error=details["error_message"])
        return to_dict(rec)


def _slim_leaf_dir(into: Path) -> None:
    """Keep the leaf's ledger, events and shadow (provenance audits); drop the node copy."""
    keep = {"branch_trials.jsonl", "branch_events.jsonl", "branch_shadow.jsonl"}
    for child in into.iterdir():
        if child.name in keep:
            continue
        if child.is_dir():
            shutil.rmtree(child, ignore_errors=True)
        else:
            child.unlink()


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

MANIFEST_KEYS = ("phase", "node", "W", "llm_cap", "instances", "forks", "near_band", "p_near", "aa_fraction",
                 "reps", "K", "audit_seeds", "seed_base", "memory_mode", "skip_display", "g_declared", "g0",
                 "prior_sha256", "manager", "obs_inflation", "a2_fraction", "policies", "rep", "synthetic_params")


def build_manifest(args, adapter, prior_sha: str, sigma_node: float, g_declared: float, g0: float) -> dict:
    phase = args.phase
    W = args.W if args.W is not None else (args.llm_cap if phase == "S0.4" else None)
    if W is None:
        raise SystemExit("--W is required for this phase (S0.4 defaults to the LLM cap: non-binding)")
    k = int(args.k_audit)
    return {
        "schema": MANIFEST_SCHEMA, "label": args.label, "phase": phase, "node": adapter.name, "W": int(W),
        "llm_cap": int(args.llm_cap), "instances": int(args.instances), "forks": float(args.forks),
        "near_band": args.near_band, "p_near": float(args.p_near), "aa_fraction": float(args.aa_fraction),
        "reps": int(args.reps), "K": k, "audit_seeds": list(AUDIT_SEEDS[:k]),
        "dev_audit_seeds": list(DEV_AUDIT_SEEDS),
        "seed_base": int(args.seed_base if args.seed_base is not None else INSTANCE_SEED_BASE[phase]),
        "selection_seed": SELECTION_SEED, "rep_base": REP_BASE, "channel_fraction": CHANNEL_FRACTION,
        "memory_mode": args.memory_mode, "skip_display": args.skip_display,
        "g_declared": g_declared, "g0": g0, "sigma_node": sigma_node, "prior_sha256": prior_sha,
        "prior_path": args.prior, "manager": manager_cfg(args), "obs_inflation": float(args.obs_inflation),
        "a2_fraction": float(args.a2_fraction if args.a2_fraction is not None else
                             (A2_FRACTION_DEFAULT if phase == "S3" else 0.0)),
        "policies": list(args.policy or []), "rep": int(args.rep), "e2_verify": False,
        "synthetic_params": json.loads(args.synthetic_params) if args.synthetic_params else None,
        "host": args.host_label, "created_utc": utc(), "sessions": [],
    }


def manager_cfg(args) -> dict:
    if args.node in SYNTHETIC_NODES:
        return {"kind": "scripted_synthetic"}
    if args.manager == "llamacpp":
        if not args.manager_model or not args.manager_model.startswith("llamacpp/"):
            raise SystemExit("--manager llamacpp needs --manager-model llamacpp/<alias> (LLAMACPP_BASE_URL set)")
        cfg = {"kind": "langgraph", "model": args.manager_model, "temperature": 0.2,
               "transport_max_attempts": int(args.transport_max_attempts)}
        if args.proposal_schema:
            cfg["proposal_schema"] = args.proposal_schema
        return cfg
    return {"kind": "scripted", "model": "scripted_random", "temperature": 0.2}


def plan(run: Run) -> dict:
    """What is left to do (used by --dry-run and to drive the session)."""
    m = run.manifest
    roots_done = {r["root_id"] for r in read_jsonl(run.out / "roots.jsonl")}
    forks = read_jsonl(run.out / "forks.jsonl")
    leaves_done = {(l["fork_id"], l["arm"], l["rep"]) for l in read_jsonl(run.out / "leaves.jsonl")}
    roots_todo = []
    for k in range(m["instances"]):
        seed = instance_seed(run, k)
        if m["phase"] in POLICY_PHASES:
            for pol in policies_for_instance(m["phase"], m["policies"], k):
                cid = campaign_id_for(run, seed, "_" + _policy_tag(pol))
                if cid not in roots_done:
                    roots_todo.append((k, pol, cid))
            continue
        cid = campaign_id_for(run, seed)
        if cid not in roots_done:
            roots_todo.append((k, None, cid))
        if m["a2_fraction"] and _u("a2", cid)[0] < m["a2_fraction"]:
            cid2 = campaign_id_for(run, seed, "A2")
            if cid2 not in roots_done:
                roots_todo.append((k, "a2", cid2))
    leaves_todo = [(f["fork_id"], arm, rep) for f in forks for arm, rep in leaf_arms(f, m["reps"])
                   if (f["fork_id"], arm, rep) not in leaves_done]
    return {"roots_todo": roots_todo, "forks_known": len(forks), "leaves_todo": leaves_todo,
            "roots_done": len(roots_done), "leaves_done": len(leaves_done)}


def policy_family(policy: str) -> str:
    return policy.split(":", 1)[0]


def policies_for_instance(phase: str, policies: list[str], k: int) -> list[str]:
    """Every policy on every instance (paired), in the tune and the campaign phase (rev.-6 amendment 2)."""
    return list(policies)


TUNE_G = (0.05, 0.1, 0.2, 0.4)        # rev. 6.1: 4 x 3 = 12 static configurations
TUNE_G_EXTENSION = (0.8,)             # optional (``--tune-g-extension``)
TUNE_H = (-0.25, 0.0, 0.25)
DYNAMIC_MEMBERS = {"budget": {"b_budget": 1.0}, "info": {"b_info": 0.5}, "keep+": {"h_budget": 0.5},
                   "keep-": {"h_budget": -0.5}}


def tuning_grid(stage: str, sigma_cmp_vary: float, m_star: tuple[float, float] | None = None,
                extend: bool = False) -> list[str]:
    """Declared tuning grid (rev.-6 amendment 2) as policy strings, in units of sigma_cmp,vary (values to 10 s.f.).

    ``static``: g x h; ``dynamic``: the four members at m*'s (g, h) (b_info is dimensionless); ``all``: both."""
    s = float(sigma_cmp_vary)
    out: list[str] = []
    if stage in ("static", "all"):
        gs = TUNE_G + (TUNE_G_EXTENSION if extend else ())
        out += [f"static:g={g * s:.10g},e2off={h * s:.10g}" for g in gs for h in TUNE_H]
    if stage in ("dynamic", "all"):
        if m_star is None:
            raise ValueError("the dynamic stage needs m*'s (g, h)")
        g, h = m_star
        for member in DYNAMIC_MEMBERS.values():
            parts = {"g0": g * s, "h0": h * s, **{k: (v if k == "b_info" else v * s) for k, v in member.items()}}
            out.append("dynamic:" + ",".join(f"{k}={v:.10g}" for k, v in parts.items()))
    if stage not in ("static", "dynamic", "all"):
        raise ValueError(f"unknown tuning stage {stage!r}")
    return out


def _policy_tag(policy: str) -> str:
    return hashlib.sha256(policy.encode()).hexdigest()[:8]


def session(run: Run) -> dict:
    m = run.manifest
    todo = plan(run)
    done = {"roots": 0, "forks": 0, "leaves": 0, "deadline_hit": False}
    for k, pol, cid in todo["roots_todo"]:
        if not run.time_left():
            done["deadline_hit"] = True
            break
        variant = "A2" if pol == "a2" else ("_" + _policy_tag(pol) if m["phase"] in POLICY_PHASES else "")
        rep = int(m["rep"]) if m["phase"] in POLICY_PHASES else 0
        root = run_root(run, k, policy=pol, variant=variant, repetition=rep)
        if m["phase"] in ("S0.5", "S3", "synthetic") and pol is None and root.get("status") == "ok":
            forks = select_forks(run, root)
            for f in forks:
                append_jsonl(run.out / "forks.jsonl", f)
            prune_snapshots(root, {f["snapshot_dir"] for f in forks})
            done["forks"] += len(forks)
        append_jsonl(run.out / "roots.jsonl", {k_: v for k_, v in root.items() if not k_.startswith("_")})
        (run.work / "root_meta").mkdir(parents=True, exist_ok=True)
        (run.work / "root_meta" / f"{root['root_id']}.json").write_text(json.dumps(
            {"_y_terminal_per_seed": root.get("_y_terminal_per_seed"), "_seed": root.get("_seed")}))
        done["roots"] += 1
    if m["phase"] in ("S0.5", "S3", "synthetic"):
        todo = plan(run)
        forks = {f["fork_id"]: f for f in read_jsonl(run.out / "forks.jsonl")}
        root_rows_cache: dict[str, list[dict]] = {}
        for fork_id, arm, rep in todo["leaves_todo"]:
            if not run.time_left():
                done["deadline_hit"] = True
                break
            fork = forks[fork_id]
            if fork["root_id"] not in root_rows_cache:
                root_rows_cache[fork["root_id"]] = read_jsonl(run.work / "roots" / fork["root_id"] / "root_trials.jsonl")
            leaf = run_leaf(run, fork, arm, rep, root_rows_cache[fork["root_id"]])
            append_jsonl(run.out / "leaves.jsonl", leaf)
            done["leaves"] += 1
    return done


def resolve_prior(args, adapter) -> tuple[a2u.A2UPrior | None, str, float]:
    """(prior, its sha256, sigma_node)."""
    if args.prior:
        prior = a2u.A2UPrior.load(args.prior, expect_sha256=args.prior_sha256)
        if prior.node != adapter.surface:
            raise SystemExit(f"prior is for {prior.node!r}, the node's surface is {adapter.surface!r}")
        return prior, prior.sha256, prior.sigma_node
    if adapter.synthetic:
        prior = adapter.node.prior()
        return prior, prior.sha256, prior.sigma_node
    sigma = args.sigma_node if args.sigma_node is not None else adapter.default_sigma_node()
    if args.phase != "S0.4":
        raise SystemExit("--prior (the S0.4 prior file) is required for real nodes outside S0.4")
    if sigma is None:
        raise SystemExit("--sigma-node is required for this node")
    return None, "none", float(sigma)


def fit_prior_phase(args) -> int:
    out = Path(args.out)
    rows = [r for r in read_jsonl(out / "s04_rows.jsonl") if r["node"] == args.node]
    adapter = make_adapter(args.node, {"kind": "none"}, json.loads(args.synthetic_params) if args.synthetic_params else None)
    sigma = args.sigma_node if args.sigma_node is not None else adapter.default_sigma_node()
    if sigma is None:
        raise SystemExit("--sigma-node is required")
    src = out / "s04_rows.jsonl"
    prior = a2u.fit_prior(rows, adapter.surface, float(sigma), k_label=len(DEV_AUDIT_SEEDS), within_key=args.within_key,
                          sources={"s04_rows": str(src), "s04_rows_sha256": sha256_file(src)})
    target = Path(args.prior or (out / "a2u_prior.json"))
    sha = prior.save(target)
    print(json.dumps({"prior": str(target), "sha256": sha, "kinds": {k: vars(v) for k, v in prior.kinds.items()}}))
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phase", choices=PHASES, required=True)
    ap.add_argument("--node", required=True, help="digits_mlp | tabular_mlp | synthetic_P0 | synthetic_P1 | synthetic_P2p | synthetic_P2m | synthetic_N0")
    ap.add_argument("--host-label", default="unknown", help='e.g. "TASL-2" (provenance)')
    ap.add_argument("--W", type=int, default=None, help="worker-run budget (S0.4 default: the LLM cap, non-binding)")
    ap.add_argument("--llm-cap", type=int, default=DEFAULT_LLM_CAP)
    ap.add_argument("--instances", type=int, default=1)
    ap.add_argument("--forks", type=float, default=4.0, help="expected uniform forks per root")
    ap.add_argument("--near-band", type=float, default=None, help="b of the near-threshold oversample (raw units)")
    ap.add_argument("--p-near", type=float, default=0.0, help="inclusion probability of a near-threshold decision")
    ap.add_argument("--aa-fraction", type=float, default=0.1)
    ap.add_argument("--reps", type=int, default=DEFAULT_REPS)
    ap.add_argument("--k-audit", type=int, default=DEFAULT_K)
    ap.add_argument("--seed-base", type=int, default=None, help="instance seed base (default: the phase's block)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--work", default=os.environ.get("R1_TMP", "/tmp/r1_tracks"))
    ap.add_argument("--deadline", type=float, default=1e12, help="seconds; no new unit starts after it")
    ap.add_argument("--dry-run", action="store_true", help="print the plan and exit (nothing runs)")
    ap.add_argument("--prior", default=None, help="A2-U prior file (fit_prior: output path)")
    ap.add_argument("--prior-sha256", default=None)
    ap.add_argument("--sigma-node", type=float, default=None)
    ap.add_argument("--g", type=float, default=None, help="declared run price (default 0.1 sigma_node)")
    ap.add_argument("--g0", type=float, default=None, help="pilot price of roots and continuations (default --g)")
    ap.add_argument("--obs-inflation", type=float, default=1.0, help="A2-U observation-variance inflation lambda")
    ap.add_argument("--within-key", choices=["estimated", "none"], default="estimated", help="fit_prior only")
    ap.add_argument("--a2-fraction", type=float, default=None, help="descriptive A2 roots (S3 default 0.2)")
    ap.add_argument("--policy", action="append", default=None, help="tune / campaign phases: a2u | "
                    "static:g=..,e2off=.. | dynamic:g0=..,b_budget=..,b_info=..,h0=..,h_budget=.. | "
                    "pi_prime:<model_file> (repeatable)")
    ap.add_argument("--rep", type=int, default=0, help="tune / campaign phases: LLM repetition")
    ap.add_argument("--tune-grid", choices=["static", "dynamic", "all"], default=None,
                    help="tune phase: add the declared grid (needs --sigma-cmp-vary; dynamic needs --m-star)")
    ap.add_argument("--sigma-cmp-vary", type=float, default=None, help="grid unit sigma_cmp,vary (raw units)")
    ap.add_argument("--tune-g-extension", action="store_true", help="add g = 0.8 to the static grid")
    ap.add_argument("--truncate-W", default=None, help="S0.5b: comma-separated W values (e.g. 8,10,12,20)")
    ap.add_argument("--m-star", default=None, help="g,h of the best static member, in sigma_cmp,vary units")
    ap.add_argument("--e2-verify", action="store_true", help="refused: E2 verify is off for every Track S policy")
    ap.add_argument("--memory-mode", default="append_only_summary")
    ap.add_argument("--skip-display", default=a2u.SKIP_DISPLAY)
    ap.add_argument("--manager", choices=["scripted", "llamacpp"], default="scripted")
    ap.add_argument("--manager-model", default=None)
    ap.add_argument("--proposal-schema", default=None)
    ap.add_argument("--transport-max-attempts", type=int, default=3)
    ap.add_argument("--gguf", default=None, help="manager GGUF path (sha256 computed)")
    ap.add_argument("--gguf-sha256", default=None)
    ap.add_argument("--llama-build", default=None)
    ap.add_argument("--llama-server-bin", default=None)
    ap.add_argument("--gpu", default=None)
    ap.add_argument("--label", default="ENGINEERING_ONLY")
    ap.add_argument("--synthetic-params", default=None, help="JSON object of synthetic node parameters")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.phase == "fit_prior":
        return fit_prior_phase(args)
    if args.phase == "S0.5b":
        if not args.truncate_W:
            raise SystemExit("S0.5b needs --truncate-W W1,W2,...")
        return s05b_phase(args)
    if args.node in SYNTHETIC_NODES and args.phase not in ("synthetic", "S0.4") + POLICY_PHASES:
        raise SystemExit("synthetic nodes run in the 'synthetic', 'S0.4', 'tune' or 'campaign' phase only")
    if args.phase == "synthetic" and args.node not in SYNTHETIC_NODES:
        raise SystemExit("the 'synthetic' phase needs a synthetic node")
    if args.tune_grid:
        if args.phase != "tune" or args.sigma_cmp_vary is None:
            raise SystemExit("--tune-grid needs --phase tune and --sigma-cmp-vary")
        m_star = tuple(float(x) for x in args.m_star.split(",")) if args.m_star else None
        args.policy = list(args.policy or []) + tuning_grid(args.tune_grid, args.sigma_cmp_vary, m_star,
                                                            extend=args.tune_g_extension)
    if args.phase in POLICY_PHASES and not args.policy:
        raise SystemExit(f"the {args.phase} phase needs at least one --policy")
    if args.e2_verify:
        raise SystemExit("E2 verify is declared off for every Track S policy (rev.-5 amendment 3); not available")
    out, work = Path(args.out), Path(args.work)
    synth_params = json.loads(args.synthetic_params) if args.synthetic_params else None
    adapter = make_adapter(args.node, manager_cfg(args), synth_params)
    prior, prior_sha, sigma_node = resolve_prior(args, adapter)
    g_declared = float(args.g if args.g is not None else G_UNITS * sigma_node)
    g0 = float(args.g0 if args.g0 is not None else g_declared)
    manifest = build_manifest(args, adapter, prior_sha, sigma_node, g_declared, g0)
    if (out / "manifest.json").exists():
        old = json.loads((out / "manifest.json").read_text())
        diff = {k: (old.get(k), manifest.get(k)) for k in MANIFEST_KEYS if old.get(k) != manifest.get(k)}
        if diff:
            raise SystemExit(f"refusing to resume {out}: the run parameters differ from its manifest: {diff}")
        manifest = old
    if args.dry_run:
        tmp_run = Run(args, adapter, out, work, manifest, prior, prior_sha, sigma_node, g_declared, g0,
                      None, None, time.time())  # type: ignore[arg-type]
        p = plan(tmp_run) if out.exists() else {"roots_todo": [(k, None, None) for k in range(manifest["instances"])],
                                                "leaves_todo": [], "forks_known": 0}
        print(json.dumps({"dry_run": True, "manifest": {k: manifest[k] for k in MANIFEST_KEYS if k in manifest},
                          "roots_todo": len(p["roots_todo"]), "forks_known": p["forks_known"],
                          "leaves_todo": len(p["leaves_todo"])}, default=str))
        return 0
    out.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    gguf_sha = args.gguf_sha256 or (sha256_file(args.gguf) if args.gguf else "none")
    controller_version = "unknown"
    provenance = Provenance(host=args.host_label, gpu=gpu_label(args.gpu), harness_commit=harness_commit(HARNESS)["commit"],
                            paper_commit=_git(REPO, "rev-parse", "HEAD"), manager_gguf_sha256=gguf_sha,
                            llama_build=llama_build(args), controller_version=controller_version,
                            prior_sha256=prior_sha, phase=args.phase, label=args.label,
                            g_declared=g_declared, g0=g0)
    run = Run(args, adapter, out, work, manifest, prior, prior_sha, sigma_node, g_declared, g0, provenance,
              AuditCache(out / "audit_runs.jsonl", adapter, work), time.time())
    start = utc()
    try:
        done = session(run)
    finally:
        manifest = json.loads((out / "manifest.json").read_text())
        manifest["sessions"].append({"start_utc": start, "end_utc": utc(), "provenance": to_dict(provenance),
                                     "cpu": cpu_census(), "audit_runs": run.audits.runs,
                                     **({"done": done} if "done" in locals() else {"interrupted": True})})
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    print(json.dumps({"out": str(out), **done}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
