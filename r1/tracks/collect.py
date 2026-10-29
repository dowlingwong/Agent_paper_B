#!/usr/bin/env python3
"""Track S collector: dev campaigns, roots, forks, leaves, audits (runbook rev. 3 §2-§6, amendments to rev. 7).

AI-assisted (Claude, 29 Oct 2026). ENGINEERING_ONLY until a Track S authorization exists; nothing this
collector writes is evidence unless the phase's authorization note says so. One process, serial (one
manager call at a time), resumable per root and per leaf, time-boxed by ``--deadline``.

Phases (``--phase``):

* ``S0.4`` — dev campaigns: every non-rule proposal executed (``ExecuteNonRuleController``) at a non-binding
  W (= the LLM cap), every executed non-rule proposal (trial >= 2) audited on the S0.4 audit block (K = 5).
  Writes ``s04_rows.jsonl``.
* ``fit_prior`` — fit A2-U's prior from ``s04_rows.jsonl``; writes ``a2u_prior.json`` and prints its sha256.
* ``S0.5`` — pilot: primary roots under ``--root-policy`` (forked as in S3), extra roots for every
  ``--policy`` x ``--rep`` pair (paired with the primary on the same seed key, no forks), and the calibration
  audits (review M6): every executed non-rule proposal of a primary root is audited on the S0.5 audit block
  and written with its A2-U 80 % predictive interval and ``n_group`` stratum to ``s05_calibration.jsonl``.
* ``S0.5b`` — the incumbent of every S0.5 root ledger truncated at each ``--truncate-W`` (``truncate_at_W``),
  audited on the S0.5 audit block; ``s05b_truncated.jsonl``. Refuses roots whose policy reads the budget.
* ``S3`` / ``synthetic`` — roots and continuations under ``--root-policy`` (m*, review M1), fork selection,
  leaves per arm x repetition, A/A leaves, audits. ``synthetic`` runs the synthetic control nodes.
* ``tune`` (S0.7) — policy strings on dev instances (tuning seed block), every configuration on the same
  paired instances; ``--tune-grid static|dynamic|magnitude|all`` adds the declared grids (``tuning_grid``);
  ``--jobs FILE`` gives an explicit list of (policy, instance subset, rep) jobs (e.g. successive halving).
* ``campaign`` (S3e) — every ``--policy`` x ``--rep`` on every fresh instance.

Policies: ``a2u`` (A2-U at g0), ``a2``, ``static:g=..,e2off=..``, ``matched_static:g=..,h=..``,
``dynamic:g0=..,b_budget=..,b_info=..,h0=..,h_budget=..,r_bar=..,tau_bar=..`` (rev. 7 centred terms),
``pi_prime:<model_file>``.

Seeds (all declared below and recorded in the manifest):
* instance blocks per phase (bounds checked; review m4);
* audit blocks per phase (review B1): S0.4, S0.5 (calibration and S0.5b), tune (S0.7), S3 (S3a), campaign
  (S3e, used by no other phase), synthetic, fixture; pairwise disjoint and disjoint from the instance blocks;
* the campaign id and LLM seed key of every campaign is (node, instance seed) only (review M2), so all
  policies and repetitions of an instance share the D26 seeds at the same repetition and the worker, verify
  and audit seeds; root ids carry the phase, policy and repetition.

Fork selection (§6 S3a): eligible decisions are drawn independently (exact inclusion probabilities):
uniform with p_u = min(1, forks / n_eligible(root)); near-threshold with p_near when |margin| <= b, where the
margin is the decision's distance to the root policy's own threshold (E1: V* (+ bonus) - threshold;
E2: m_hat - h). Channel arms on a Bernoulli third of E1 forks, A/A on ``--aa-fraction``; every selected fork's
decision is rebuilt from its snapshot (STOP on a mismatch). Leaves: r = ``--reps`` repetitions on channel
forks and ``--reps-ordinary`` elsewhere (review m1). An A/A mismatch is a STOP (review m2).

Resume (review M5): forks are deduplicated on fork_id and appended before their root, whose line is the
commit marker; a failed unit is logged in ``failed_units.jsonl`` (never as done) and retried on later sessions
up to ``--max-retries``; a truncated last line of any JSONL file is tolerated and repaired before appending.

Outputs in ``--out``: ``roots.jsonl``, ``leaves.jsonl``, ``forks.jsonl``, ``manifest.json``
(``r1.tracks.schema``), ``audit_runs.jsonl``, ``failed_units.jsonl``, ``failures/``. Scratch in ``--work``.
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
from autoresearch.memory.event_store import CampaignEventStore  # noqa: E402
from autoresearch.nodes.registry import load_registered_node  # noqa: E402
from autoresearch.worker.local_worker import LocalWorker  # noqa: E402

from r1.c3.features import NodeContext, apply_edit, replay_campaign  # noqa: E402
from r1.diagnostics.di_test import configuration  # noqa: E402
from r1.tracks import a2u  # noqa: E402
from r1.tracks.schema import (TRACKS_LEAF_SCHEMA, TRACKS_ROOT_SCHEMA, Forecast, LeafRecord, Provenance,  # noqa: E402
                              RootRecord, Selection, to_dict)
from r1.tracks.synthetic import SYNTHETIC_NODES, synthetic_node  # noqa: E402

MANIFEST_SCHEMA = "tracks_manifest/v2"
# ---- the Track S seed blocks (declared constants) ---------------------------------------------
INSTANCE_SEED_BLOCKS = {"S0.4": (30000, 30250), "tune": (30250, 30500), "S0.5": (30500, 31000),
                        "S3": (31000, 32000), "campaign": (32000, 33000), "synthetic": (36000, 37000),
                        "fixture": (39000, 40000)}
_AUDIT_BLOCK_SIZE = 20
AUDIT_SEED_BLOCKS = {name: tuple(range(start, start + _AUDIT_BLOCK_SIZE)) for name, start in (
    ("S0.4", 33001), ("S0.5", 33101), ("tune", 33201), ("S3", 33301), ("campaign", 33401),
    ("synthetic", 33501), ("fixture", 33601))}
PHASE_AUDIT_BLOCK = {"S0.4": "S0.4", "S0.5": "S0.5", "S0.5b": "S0.5", "tune": "tune", "S3": "S3",
                     "campaign": "campaign", "synthetic": "synthetic"}
DEV_AUDIT_SEEDS = AUDIT_SEED_BLOCKS["S0.4"][:5]   # S0.4 dev rows, K = 5
SELECTION_SEED = 35001
REP_BASE = 100                                    # leaf repetition r -> D26 repetition REP_BASE + r
CHANNEL_FRACTION = 1.0 / 3.0
A2_FRACTION_DEFAULT = 0.2                        # descriptive A2 roots (S3 only)
DEFAULT_LLM_CAP = 40
DEFAULT_K = 5
DEFAULT_MAX_RETRIES = 2
G_UNITS = 0.1                                     # declared g = 0.1 sigma_node unless --g (C3 convention)
# sigma_node (median paired sd Delta-hat), runbook §1 B2 (NOISE_FLOOR_COMMON_20261022); a prior file overrides.
SIGMA_NODE_DEFAULTS = {"digits_mlp": 0.0066, "tabular_mlp": 0.0019}
PHASES = ("S0.4", "fit_prior", "S0.5", "S0.5b", "S3", "synthetic", "tune", "campaign")
POLICY_PHASES = ("tune", "campaign")
FORK_PHASES = ("S0.5", "S3", "synthetic")
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


def audit_seeds_for(phase: str, k: int) -> tuple[str, tuple]:
    block = PHASE_AUDIT_BLOCK[phase]
    if not 1 <= k <= _AUDIT_BLOCK_SIZE:
        raise SystemExit(f"--k-audit must lie in 1..{_AUDIT_BLOCK_SIZE}")
    return block, AUDIT_SEED_BLOCKS[block][:k]


# ---------------------------------------------------------------------------
# JSONL with crash tolerance (review M5, m8)
# ---------------------------------------------------------------------------

def read_jsonl(path: Path) -> list[dict]:
    """Rows of a JSONL file; a truncated (unparsable) LAST line is ignored, a corrupt earlier line raises."""
    path = Path(path)
    if not path.exists():
        return []
    lines = [line for line in path.read_text().splitlines() if line.strip()]
    out = []
    for i, line in enumerate(lines):
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            if i == len(lines) - 1:
                break
            raise
    return out


def _repair_tail(path: Path) -> None:
    """Drop a partial last line (a crash mid-write) so the next append starts on a fresh line."""
    if not path.exists() or path.stat().st_size == 0:
        return
    data = path.read_bytes()
    if data.endswith(b"\n"):
        return
    cut = data.rfind(b"\n")
    path.write_bytes(data[: cut + 1] if cut >= 0 else b"")


def append_jsonl(path: Path, row: dict) -> None:
    path = Path(path)
    _repair_tail(path)
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
# Policies
# ---------------------------------------------------------------------------

def _kv(policy: str, prefix: str, allowed: set, required: set) -> dict:
    kv = dict(item.split("=", 1) for item in policy[len(prefix):].split(",") if item)
    if set(kv) - allowed or required - set(kv):
        raise ValueError(f"{prefix[:-1]} policy takes {sorted(allowed)} (required {sorted(required)}), got {policy!r}")
    return {k: float(v) for k, v in kv.items()}


def policy_controller(policy: str, prior, ctx, *, g0: float, obs_inflation: float = 1.0, W: int | None = None):
    """Named policies (module docstring)."""
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
        kv = _kv(policy, "dynamic:", {"g0", "b_budget", "b_info", "h0", "h_budget", "r_bar", "tau_bar"}, {"g0"})
        return a2u.A2UController.dynamic(prior, ctx, **kv, obs_inflation=obs_inflation, W=W, policy_name=policy)
    if policy.startswith("pi_prime:"):
        model, sha = a2u.RidgeScore.load(policy[len("pi_prime:"):])
        return a2u.A2UController(prior, ctx, g=g0, score_fn=model, obs_inflation=obs_inflation, W=W,
                                 policy_name=f"pi_prime:{sha[:12]}")
    raise ValueError(f"unknown or unimplemented policy {policy!r} (budget_dp / probe_first are not implemented)")


def policy_family(policy: str) -> str:
    return policy.split(":", 1)[0]


def _policy_tag(policy: str) -> str:
    return hashlib.sha256(policy.encode()).hexdigest()[:8]


TUNE_G = (0.0, 0.05, 0.1, 0.2, 0.4)   # rev. 7 (a): g = 0 = execute every non-rule proposal; 5 x 3 = 15 static
TUNE_G_EXTENSION = (0.8,)             # optional (``--tune-g-extension``)
TUNE_H = (-0.25, 0.0, 0.25)
DYNAMIC_MEMBERS = {"budget": {"b_budget": 1.0}, "info": {"b_info": 0.5}, "keep+": {"h_budget": 0.5},
                   "keep-": {"h_budget": -0.5}}
# rev. 7 (c): the magnitude grid per channel (b_budget, h_budget in sigma units; b_info dimensionless).
MAGNITUDE_GRID = {"budget": [{"b_budget": v} for v in (0.5, 1.0, 2.0)],
                  "info": [{"b_info": v} for v in (0.25, 0.5, 1.0)],
                  "keep": [{"h_budget": s * v} for v in (0.25, 0.5, 1.0) for s in (1.0, -1.0)]}


def _dynamic_string(g: float, h: float, member: dict, s: float, r_bar: float, tau_bar: float) -> str:
    parts = {"g0": g * s, "h0": h * s, **{k: (v if k == "b_info" else v * s) for k, v in member.items()}}
    if r_bar:
        parts["r_bar"] = r_bar
    if tau_bar:
        parts["tau_bar"] = tau_bar
    return "dynamic:" + ",".join(f"{k}={v:.10g}" for k, v in parts.items())


def tuning_grid(stage: str, sigma_cmp_vary: float, m_star: tuple[float, float] | None = None,
                extend: bool = False, r_bar: float = 0.0, tau_bar: float = 0.0) -> list[str]:
    """Declared tuning grids as policy strings, in units of sigma_cmp,vary (values to 10 s.f.).

    ``static``: g x h; ``dynamic``: the four members at m*'s (g, h); ``magnitude``: the per-channel magnitude
    grid at m* (rev. 7 c); ``all``: static + dynamic. r_bar / tau_bar centre the dynamic terms (rev. 7 b)."""
    s = float(sigma_cmp_vary)
    out: list[str] = []
    if stage not in ("static", "dynamic", "magnitude", "all"):
        raise ValueError(f"unknown tuning stage {stage!r}")
    if stage in ("static", "all"):
        gs = TUNE_G + (TUNE_G_EXTENSION if extend else ())
        out += [f"static:g={g * s:.10g},e2off={h * s:.10g}" for g in gs for h in TUNE_H]
    if stage in ("dynamic", "magnitude", "all"):
        if m_star is None:
            raise ValueError("the dynamic and magnitude stages need m*'s (g, h)")
        g, h = m_star
        members = list(DYNAMIC_MEMBERS.values()) if stage != "magnitude" else \
            [m for grid in MAGNITUDE_GRID.values() for m in grid]
        out += [_dynamic_string(g, h, m, s, r_bar, tau_bar) for m in members]
    return out


def load_jobs(path: str) -> list[dict]:
    """Explicit tune jobs: a JSON list of {"policy": str, "instances": [k, ...], "rep": int (default 0)}."""
    jobs = json.loads(Path(path).read_text())
    if not isinstance(jobs, list) or not all(isinstance(j, dict) and "policy" in j and "instances" in j for j in jobs):
        raise SystemExit("--jobs must be a JSON list of {policy, instances[, rep]} objects")
    return [{"policy": str(j["policy"]), "instances": [int(k) for k in j["instances"]], "rep": int(j.get("rep", 0))}
            for j in jobs]


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

    @property
    def root_policy(self) -> str:
        return str(self.manifest.get("root_policy") or "a2u")

    def time_left(self) -> bool:
        return time.time() - self.t0 < float(self.args.deadline)

    def node_ctx(self) -> NodeContext:
        return NodeContext(node=self.adapter.surface, start_files=self.adapter.start_files(),
                           sigma_node=self.sigma_node, runs_total=self.W,
                           memory_mode=self.manifest["memory_mode"])

    def controller(self, policy: str | None = None):
        """The root / continuation controller (``--root-policy``), or a named policy."""
        ctx = self.node_ctx()
        lam = float(self.manifest.get("obs_inflation", 1.0))
        if self.manifest["phase"] == "S0.4":
            return a2u.ExecuteNonRuleController(self.prior, ctx, obs_inflation=lam)
        return policy_controller(policy or self.root_policy, self.prior, ctx, g0=self.g0, obs_inflation=lam, W=self.W)


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------

def _git(repo: Path, *args) -> str:
    try:
        return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:  # noqa: BLE001 - provenance is best effort, recorded as unknown
        return "unknown"


def _git_dirty(repo: Path) -> bool | None:
    try:
        out = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=repo, capture_output=True,
                             text=True, check=True).stdout
        return bool(out.strip())
    except Exception:  # noqa: BLE001
        return None


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


def _prov(run: Run, controller) -> Provenance:
    return Provenance(**{**to_dict(run.provenance), "controller_version": controller.version})


# ---------------------------------------------------------------------------
# Failure bookkeeping (review M5)
# ---------------------------------------------------------------------------

def _write_failure(out: Path, kind: str, ident: str, payload: dict) -> None:
    target = out / "failures" / f"{kind}__{ident}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target = target.with_name(target.stem + f"__{time.time_ns()}.json")
    target.write_text(json.dumps(payload, indent=2) + "\n")


def failed_attempts(out: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in read_jsonl(out / "failed_units.jsonl"):
        counts[r["unit"]] = counts.get(r["unit"], 0) + 1
    return counts


def log_failed_unit(out: Path, unit: str, kind: str, details: dict) -> None:
    append_jsonl(out / "failed_units.jsonl", {"unit": unit, "kind": kind, "utc": utc(),
                                              "error_class": details.get("error_class"),
                                              "error_message": details.get("error_message")})


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


def seed_key_for(node: str, seed: int) -> str:
    """Harness campaign id and LLM seed key of an instance: (node, instance seed) only (review M2)."""
    return f"tracks_{node}__s{seed}"


def root_id_for(run: Run, seed: int, variant: str = "") -> str:
    tag = run.manifest["phase"].replace(".", "")
    return f"tracks_{tag}_{run.adapter.name}__s{seed}{variant}"


def root_variant(policy: str | None, rep: int, *, primary: bool) -> str:
    if primary:
        return ""
    if policy == "a2":
        return "__A2"
    return f"__{_policy_tag(policy or 'a2u')}_r{rep}"


def w_binds(runs: int, W: int, trials: int, trial_cap: int) -> bool:
    """W binds iff the campaign used its W runs while proposals remained (review m5)."""
    return runs >= W and trials < trial_cap


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
                        "index_value": d.get("v_star"), "margin": d.get("margin"), "eligible": eligible,
                        "skip_reason": d.get("skip_reason"), "detail": d})
        e2 = ev.get("E2")
        if e2 is not None:
            d = e2.get("detail") or {}
            e1_ok = bool(((ev.get("E1") or {}).get("detail") or {}).get("eligible"))
            eligible = bool(d.get("eligible")) and e1_ok and row.get("validity_status") == "valid" \
                and ("E2", b) in snapshots
            out.append({"index": b, "epoch": "E2", "action": "keep" if row["decision"] == "kept" else "discard",
                        "index_value": d.get("m_hat"), "margin": d.get("margin"), "eligible": eligible, "detail": d})
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


def _llm_calls(events: list[dict]) -> int:
    return sum(1 for e in events if e.get("event_type") == "llm_call"
               and (e.get("payload") or {}).get("purpose") != "self_forecast")


def run_root(run: Run, k: int, *, policy: str | None, rep: int, primary: bool) -> dict:
    """One campaign of instance k (``primary``: the forked root of a fork phase). Raises on failure."""
    adapter = run.adapter
    seed = instance_seed(run, k)
    cid = seed_key_for(adapter.name, seed)
    root_id = root_id_for(run, seed, root_variant(policy, rep, primary=primary))
    root_dir = run.work / "roots" / root_id
    if root_dir.exists():
        shutil.rmtree(root_dir)  # an interrupted root is re-run whole, never patched
    root_dir.mkdir(parents=True)
    node_dir = adapter.copy(root_dir / "node")
    worker = adapter.worker(node_dir, seed, root_dir / "art")
    controller = run.controller(policy)
    snaps = AllSnapshots(root_dir / "snapshots") if (run.manifest["phase"] in FORK_PHASES and primary) else None
    manager = adapter.manager(seed, rep, seed_key=cid)
    kwargs = controller.campaign_kwargs(W=run.W, llm_cap=run.cap, skip_display=run.manifest["skip_display"])
    run_real_campaign(
        node_spec=adapter.spec, campaign_id=cid, manager_mode=getattr(manager, "mode", "manager"),
        memory_mode=run.manifest["memory_mode"], records_path=root_dir / "root_trials.jsonl", worker=worker,
        proposal_backend=manager, snapshot_hook=snaps, event_store=CampaignEventStore(root_dir / "root_events.jsonl"),
        **kwargs)
    rows = read_jsonl(root_dir / "root_trials.jsonl")
    events = read_jsonl(root_dir / "root_events.jsonl")
    decisions = decisions_from(rows, events, snaps.written if snaps else {})
    start = adapter.start_files()
    y_start = _mean(run.audits.metrics(seed, start, run.seeds))
    y1 = _mean(run.audits.metrics(seed, config_after(rows, start, 1), run.seeds)) if rows else None
    final = _workspace_files(adapter, node_dir)
    y_seeds = run.audits.metrics(seed, final, run.seeds)
    runs_used = worker_runs_of(rows, events)
    rec = RootRecord(schema=TRACKS_ROOT_SCHEMA, node=adapter.name, instance_id=f"{adapter.name}__s{seed}",
                     root_id=root_id, W=run.W, llm_cap=run.cap, y_start=y_start, y_after_trial1=y1,
                     y_terminal=_mean(y_seeds),
                     eligible_e1=sum(1 for d in decisions if d["epoch"] == "E1" and d["eligible"]),
                     eligible_e2=sum(1 for d in decisions if d["epoch"] == "E2" and d["eligible"]),
                     binding=w_binds(runs_used, run.W, len(rows), int(kwargs["budget"])), runs_used=runs_used,
                     llm_calls=_llm_calls(events),
                     decisions=[{k_: v for k_, v in d.items() if k_ != "detail"} for d in decisions],
                     provenance=_prov(run, controller), policy=policy or run.root_policy, rep=int(rep))
    out = to_dict(rec)
    out["_snapshots"] = {f"{e}_b{b:03d}": p for (e, b), p in (snaps.written.items() if snaps else ())}
    out["_y_terminal_per_seed"] = y_seeds
    out["_seed"] = seed
    if run.manifest["phase"] == "S0.4":
        dev_rows(run, rows, seed, cid)
    if run.manifest["phase"] == "S0.5" and primary and run.manifest.get("calibration", True):
        calibration_rows(run, rows, seed, cid, root_id, controller)
    return out


def truncate_at_W(rows: list[dict], W: int) -> tuple[list[dict], bool]:
    """The ledger prefix a campaign at budget W would have written, and whether W binds there.

    Trials are kept while fewer than W worker runs were used before them (the loop's stopping rule); a trial
    whose own run is the W-th is included. W binds iff the W runs were used while trials remained."""
    out, runs = [], 0
    for r in rows:
        if runs >= W:
            return out, True
        out.append(r)
        runs += worker_runs_of([r], [])
    return out, False


def s05b_phase(args) -> int:
    out, work = Path(args.out), Path(args.work)
    manifest = json.loads((out / "manifest.json").read_text())
    if manifest["phase"] != "S0.5":
        raise SystemExit("S0.5b post-processes an S0.5 output directory")
    adapter = make_adapter(manifest["node"], manifest.get("manager") or {}, manifest.get("synthetic_params"))
    audits = AuditCache(out / "audit_runs.jsonl", adapter, work)
    seeds = tuple(manifest["audit_seeds"])  # the S0.5 audit block
    prior = a2u.A2UPrior.load(manifest["prior_path"]) if manifest.get("prior_path") else \
        (adapter.node.prior() if adapter.synthetic else None)
    ctx = NodeContext(node=adapter.surface, start_files=adapter.start_files(), sigma_node=manifest["sigma_node"],
                      runs_total=int(manifest["W"]), memory_mode=manifest["memory_mode"])
    Ws = [int(w) for w in str(args.truncate_W).split(",")]
    done = {(r["root_id"], r["W"]) for r in read_jsonl(out / "s05b_truncated.jsonl")}
    start = adapter.start_files()
    n = 0
    for root in read_jsonl(out / "roots.jsonl"):
        if root.get("status") != "ok":
            continue
        if prior is not None and a2u.reads_budget(policy_controller(root["policy"], prior, ctx, g0=manifest["g0"],
                                                                    W=int(manifest["W"]))):
            raise SystemExit(f"S0.5b refuses {root['root_id']}: its policy {root['policy']!r} reads the budget, so a "
                             "truncated ledger is not what a campaign at a smaller W would have done")
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


def worker_runs_of(rows: list[dict], events: list[dict]) -> int:
    """Worker runs a ledger segment spent: executed trials (not precondition failures) + verify re-runs."""
    runs = 0
    for r in rows:
        if r.get("decision") == "skipped" or str(r.get("worker_mode", "")).endswith("_precheck"):
            continue
        runs += 1
        v = ((r.get("extra") or {}).get("control") or {}).get("verify")
        if v:
            runs += 2 * int(v.get("r", 2))
    return runs


# ---------------------------------------------------------------------------
# S0.4 dev rows and S0.5 calibration audits
# ---------------------------------------------------------------------------

def _audited_proposals(run: Run, rows: list[dict], cid: str, source: str):
    proposals, _ = replay_campaign(rows, run.adapter.start_files(), run.adapter.surface, cid, source,
                                   run.manifest["memory_mode"], run.W, run.sigma_node, check=False)
    return [p for p in proposals if not p.outcome["noop"] and not p.outcome["duplicate"]]


def _paired(cand: list, inc: list) -> tuple[float | None, float | None, int]:
    d = [c - i for c, i in zip(cand, inc) if c is not None and i is not None]
    return (float(np.mean(d)) if d else None, float(np.std(d, ddof=1) / np.sqrt(len(d))) if len(d) > 1 else None, len(d))


def dev_rows(run: Run, rows: list[dict], seed: int, cid: str) -> None:
    """Audit every executed non-rule proposal of a dev campaign on the S0.4 block (candidate vs incumbent)."""
    from r1.c3.control import edit_kind
    for p in _audited_proposals(run, rows, cid, "tracks_S0.4"):
        da, se, k = _paired(run.audits.metrics(seed, p.candidate_files, DEV_AUDIT_SEEDS),
                            run.audits.metrics(seed, p.incumbent_files, DEV_AUDIT_SEEDS))
        append_jsonl(run.out / "s04_rows.jsonl", {
            "node": run.adapter.name, "instance": cid, "budget_index": p.budget_index,
            "key": p.edit.get("symbol"), "sign": a2u.sign_of(p.features.get("direction")),
            "kind": edit_kind(p.edit), "delta_hat": p.outcome["delta_hat"], "delta_audit": da, "se": se, "k": k,
            "seeds": list(DEV_AUDIT_SEEDS)})


def calibration_rows(run: Run, rows: list[dict], seed: int, cid: str, root_id: str, controller) -> None:
    """S0.5 calibration input (review M6): each executed non-rule proposal of a primary S0.5 root, audited on
    the S0.5 block (never the S0.4 training block), with the root controller's 80 % predictive interval of its
    audited Delta (widened by the audit's se) and its ``n_group`` stratum."""
    props = {p.budget_index: p for p in _audited_proposals(run, rows, cid, "tracks_S0.5")}
    audited, ses = {}, {}
    for b, p in props.items():
        da, se, _ = _paired(run.audits.metrics(seed, p.candidate_files, run.seeds),
                            run.audits.metrics(seed, p.incumbent_files, run.seeds))
        audited[b], ses[b] = da, se
    for iv in a2u.predictive_intervals(rows, controller, level=0.8, audit_se=ses):
        b = iv["budget_index"]
        if b not in props:
            continue
        da = audited[b]
        append_jsonl(run.out / "s05_calibration.jsonl", {
            "root_id": root_id, "instance": cid, **iv, "delta_audit": da, "se": ses[b],
            "covered": None if da is None else bool(iv["lo"] <= da <= iv["hi"]), "audit_seeds": list(run.seeds)})


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


def fork_state(run: Run, snap, epoch: str, controller) -> tuple[dict, Forecast, str]:
    """State features, forecast and the rebuilt root-policy action of a fork, from its snapshot alone."""
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

    Valid only for budget-blind root policies (A2-U, static): a campaign at a smaller W follows the same
    trajectory until its W-th run. Prefer S0.5b, which also checks that proposals remained."""
    ok = [r for r in roots if r.get("status") == "ok"]
    if any(int(r["W"]) < max(Ws) for r in ok):
        raise ValueError("binding shares need roots run at W >= max(Ws)")
    return {int(W): (float(np.mean([r["runs_used"] >= W for r in ok])) if ok else None) for W in Ws}


def is_near(margin: float | None, band: float | None) -> bool:
    """The near-threshold band, centred on the root policy's own threshold (review M1)."""
    return band is not None and margin is not None and abs(float(margin)) <= float(band)


def select_forks(run: Run, root: dict) -> list[dict]:
    """Poisson-sample the eligible decisions of a primary root; rebuild-check every selected fork."""
    eligible = [d for d in root["decisions"] if d["eligible"]]
    n = len(eligible)
    p_u = min(1.0, float(run.manifest["forks"]) / n) if n else 0.0
    band, p_near = run.manifest.get("near_band"), float(run.manifest.get("p_near", 0.0))
    forks = []
    controller = run.controller()
    for d in eligible:
        fork_id = f"{root['root_id']}__{d['epoch']}_b{d['index']:03d}"
        near = is_near(d.get("margin"), band)
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
                      **draw, "near": bool(near), "margin": d.get("margin"), "myopic_action": d["action"],
                      "skip_reason": d.get("skip_reason"), "state": state, "forecast": to_dict(forecast)})
    return forks


def prune_snapshots(root: dict, keep: set[str]) -> None:
    for path in root.get("_snapshots", {}).values():
        if path not in keep and Path(path).exists():
            shutil.rmtree(path, ignore_errors=True)


# ---------------------------------------------------------------------------
# Leaves
# ---------------------------------------------------------------------------

def leaf_arms(fork: dict, reps: int, reps_ordinary: int | None = None) -> list[tuple[str, int]]:
    """Arms x repetitions of a fork: ``reps`` on channel forks, ``reps_ordinary`` elsewhere (review m1)."""
    channel = fork["epoch"] == "E1" and fork["selection"]["channel_arms"]
    arms = list(E1_LEAF_ARMS) if fork["epoch"] == "E1" else list(E2_LEAF_ARMS)
    if channel:
        arms += list(E1_CHANNEL_ARMS)
    r = reps if (channel or reps_ordinary is None) else reps_ordinary
    out = [(arm, i) for arm in arms for i in range(1, r + 1)]
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
        try:
            step = math.log(float(edit["new"]) / float(edit["old"]))
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            step = None
        d = details.get(int(r["budget_index"]), {})
        out.append({"key": edit.get("symbol"), "value": edit.get("new"), "step": step,
                    "duplicate": bool(d.get("duplicate")), "noop": bool(d.get("noop"))})
    return out


def leaf_unit(fork_id: str, arm: str, rep: int) -> str:
    return f"{fork_id}__{arm}__r{rep}"


def run_leaf(run: Run, fork: dict, arm: str, rep: int, root_rows: list[dict]) -> dict:
    """One leaf; returns its LeafRecord dict. Raises on failure (logged by the session), Stop on A/A mismatch."""
    adapter = run.adapter
    snap = read_snapshot(fork["snapshot_dir"])
    leaf_id = leaf_unit(fork["fork_id"], arm, rep)
    into = run.work / "leaves" / leaf_id
    if into.exists():
        shutil.rmtree(into)
    repetition = 0 if arm == "aa" else REP_BASE + rep
    controller = run.controller()
    override, first_action = _override(fork, arm)
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
    # Runs from the fork trial on, its own run included (at E2 it was spent before the snapshot).
    runs_before = int(snap.compute_budget_state.get("worker_runs", 0)) - (1 if e2 else 0)
    runs_used = worker_runs_of(new, events)
    shadow = result.shadow_record
    if shadow is not None and not str(shadow.worker_mode).endswith("_precheck"):
        runs_used += 1
    dup_due = sum(1 for b, d in details.items() if b > int(fork["index"])
                  and d.get("skip_reason") == "rule_duplicate" and d.get("duplicate_of") == int(fork["index"]))
    aa_ok = None
    if arm == "aa":
        root_after = [r for r in root_rows if int(r["budget_index"]) >= int(fork["index"])]
        aa_ok = _signature(new) == _signature(root_after)
    rec = LeafRecord(
        schema=TRACKS_LEAF_SCHEMA, node=adapter.name, instance_id=fork["instance_id"], root_id=fork["root_id"],
        fork_id=fork["fork_id"], epoch=fork["epoch"], fork_trial_index=int(fork["index"]), arm=arm, rep=rep,
        llm_seed_base=repetition, myopic_action=fork["myopic_action"], selection=Selection(**fork["selection"]),
        state=fork["state"], forecast=Forecast(**fork["forecast"]),
        immediate_measured=float(immediate) if immediate is not None else math.nan, y_terminal=_mean(y_seeds),
        y_terminal_per_seed=y_seeds, audit_seeds=list(run.seeds), runs_used=runs_used, llm_calls=_llm_calls(events),
        keeps_after=sum(1 for r in after if r["decision"] == "kept"),
        binding=w_binds(runs_before + runs_used, run.W, len(rows), int(snap.budget_total)), nf_c_events=0,
        dup_filtered_due_to_fork=dup_due, next_proposals=_next_proposals(after, details),
        provenance=_prov(run, controller), aa_reproduced=aa_ok, policy=run.root_policy)
    _slim_leaf_dir(into)
    out = to_dict(rec)
    if arm == "aa" and not aa_ok:
        _write_failure(run.out, "aa", leaf_id, {"leaf": _signature(new), "root": _signature(
            [r for r in root_rows if int(r["budget_index"]) >= int(fork["index"])])})
        append_jsonl(run.out / "leaves.jsonl", out)
        raise Stop(f"STOP (runbook §10): A/A leaf {leaf_id} does not reproduce its root (review m2)")
    return out


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

MANIFEST_KEYS = ("label", "phase", "node", "W", "llm_cap", "instances", "forks", "near_band", "p_near",
                 "aa_fraction", "reps", "reps_ordinary", "K", "audit_block", "audit_seeds", "seed_base",
                 "memory_mode", "skip_display", "g_declared", "g0", "prior_sha256", "manager", "obs_inflation",
                 "a2_fraction", "policies", "llm_reps", "root_policy", "jobs", "calibration", "synthetic_params")


def build_manifest(args, adapter, prior_sha: str, sigma_node: float, g_declared: float, g0: float) -> dict:
    phase = args.phase
    W = args.W if args.W is not None else (args.llm_cap if phase == "S0.4" else None)
    if W is None:
        raise SystemExit("--W is required for this phase (S0.4 defaults to the LLM cap: non-binding)")
    k = int(args.k_audit)
    block, seeds = audit_seeds_for(phase, k)
    lo, hi = INSTANCE_SEED_BLOCKS[phase]
    seed_base = int(args.seed_base if args.seed_base is not None else lo)
    jobs = load_jobs(args.jobs) if args.jobs else None
    n_instances = (max(k_ for j in jobs for k_ in j["instances"]) + 1) if jobs else int(args.instances)
    if not (lo <= seed_base and seed_base + n_instances <= hi):
        raise SystemExit(f"instance seeds {seed_base}..{seed_base + n_instances - 1} leave the {phase} block "
                         f"[{lo}, {hi}) (review m4)")
    return {
        "schema": MANIFEST_SCHEMA, "label": args.label, "phase": phase, "node": adapter.name, "W": int(W),
        "llm_cap": int(args.llm_cap), "instances": n_instances, "forks": float(args.forks),
        "near_band": args.near_band, "p_near": float(args.p_near), "aa_fraction": float(args.aa_fraction),
        "reps": int(args.reps), "reps_ordinary": int(args.reps_ordinary), "K": k, "audit_block": block,
        "audit_seeds": list(seeds), "dev_audit_seeds": list(DEV_AUDIT_SEEDS),
        "seed_base": seed_base, "instance_block": [lo, hi],
        "seed_blocks": {"instances": {p: list(b) for p, b in INSTANCE_SEED_BLOCKS.items()},
                        "audits": {p: [b[0], b[-1]] for p, b in AUDIT_SEED_BLOCKS.items()},
                        "selection": SELECTION_SEED, "rep_base": REP_BASE},
        "selection_seed": SELECTION_SEED, "rep_base": REP_BASE, "channel_fraction": CHANNEL_FRACTION,
        "memory_mode": args.memory_mode, "skip_display": args.skip_display,
        "g_declared": g_declared, "g0": g0, "sigma_node": sigma_node, "prior_sha256": prior_sha,
        "prior_path": args.prior, "manager": manager_cfg(args), "obs_inflation": float(args.obs_inflation),
        "a2_fraction": float(args.a2_fraction if args.a2_fraction is not None else
                             (A2_FRACTION_DEFAULT if phase == "S3" else 0.0)),
        "policies": list(args.policy or []), "llm_reps": list(args.rep or [0]),
        "root_policy": args.root_policy, "jobs": jobs, "calibration": bool(phase == "S0.5" and not args.no_calibration),
        "max_retries": int(args.max_retries), "e2_verify": False,
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


def _dedupe(rows: list[dict], key: str) -> list[dict]:
    seen, out = set(), []
    for r in rows:
        if r[key] in seen:
            continue
        seen.add(r[key])
        out.append(r)
    return out


def root_jobs(run: Run) -> list[tuple[int, str | None, int, bool, str]]:
    """(instance k, policy, repetition, primary, root_id) of every campaign this run must have."""
    m = run.manifest
    out = []

    def add(k: int, pol: str | None, rep: int, primary: bool) -> None:
        rid = root_id_for(run, instance_seed(run, k), root_variant(pol, rep, primary=primary))
        out.append((k, pol, rep, primary, rid))

    if m["phase"] in POLICY_PHASES:
        if m.get("jobs"):
            for job in m["jobs"]:
                for k in job["instances"]:
                    add(k, job["policy"], job["rep"], False)
        else:
            for k in range(m["instances"]):
                for pol in m["policies"]:
                    for rep in m["llm_reps"]:
                        add(k, pol, rep, False)
        return out
    for k in range(m["instances"]):
        add(k, None, 0, True)
        for pol in m["policies"]:
            for rep in m["llm_reps"]:
                if pol == run.root_policy and rep == 0:
                    continue  # that is the primary root
                add(k, pol, rep, False)
        if m["a2_fraction"] and _u("a2", root_id_for(run, instance_seed(run, k)))[0] < m["a2_fraction"]:
            add(k, "a2", 0, False)
    return out


def plan(run: Run) -> dict:
    """What is left to do (used by --dry-run and to drive the session)."""
    m = run.manifest
    roots_done = {r["root_id"] for r in read_jsonl(run.out / "roots.jsonl")}
    forks = _dedupe(read_jsonl(run.out / "forks.jsonl"), "fork_id")
    fork_roots = {f["root_id"] for f in forks}
    leaves_done = {(l["fork_id"], l["arm"], l["rep"]) for l in read_jsonl(run.out / "leaves.jsonl")}
    attempts = failed_attempts(run.out)
    limit = 1 + int(m.get("max_retries", DEFAULT_MAX_RETRIES))
    roots_todo, exhausted = [], []
    for job in root_jobs(run):
        rid = job[4]
        if rid in roots_done:
            continue
        (exhausted if attempts.get(rid, 0) >= limit else roots_todo).append(job)
    leaves_todo = []
    for f in forks:
        if f["root_id"] not in roots_done:
            continue  # the root's commit marker is missing: its forks are re-selected with it
        for arm, rep in leaf_arms(f, m["reps"], m.get("reps_ordinary")):
            if (f["fork_id"], arm, rep) in leaves_done:
                continue
            unit = leaf_unit(f["fork_id"], arm, rep)
            (exhausted if attempts.get(unit, 0) >= limit else leaves_todo).append((f["fork_id"], arm, rep))
    return {"roots_todo": roots_todo, "forks_known": len(forks), "leaves_todo": leaves_todo,
            "roots_done": len(roots_done), "leaves_done": len(leaves_done), "exhausted": exhausted,
            "fork_roots": fork_roots}


def session(run: Run) -> dict:
    m = run.manifest
    todo = plan(run)
    done = {"roots": 0, "forks": 0, "leaves": 0, "failed": 0, "exhausted": len(todo["exhausted"]),
            "deadline_hit": False}
    known_forks = {f["fork_id"] for f in read_jsonl(run.out / "forks.jsonl")}
    for k, pol, rep, primary, rid in todo["roots_todo"]:
        if not run.time_left():
            done["deadline_hit"] = True
            break
        try:
            root = run_root(run, k, policy=pol, rep=rep, primary=primary)
        except Stop:
            raise
        except Exception as exc:  # noqa: BLE001 - logged, never counted as done; retried on resume
            details = failure_details(exc, "root_campaign")
            _write_failure(run.out, "root", rid, details)
            log_failed_unit(run.out, rid, "root", details)
            done["failed"] += 1
            continue
        if m["phase"] in FORK_PHASES and primary:
            forks = select_forks(run, root)
            for f in forks:
                if f["fork_id"] not in known_forks:  # dedupe on fork_id (review M5)
                    append_jsonl(run.out / "forks.jsonl", f)
                    known_forks.add(f["fork_id"])
            prune_snapshots(root, {f["snapshot_dir"] for f in forks})
            done["forks"] += len(forks)
        (run.work / "root_meta").mkdir(parents=True, exist_ok=True)
        (run.work / "root_meta" / f"{root['root_id']}.json").write_text(json.dumps(
            {"_y_terminal_per_seed": root.get("_y_terminal_per_seed"), "_seed": root.get("_seed")}))
        # The root line is the commit marker: written last.
        append_jsonl(run.out / "roots.jsonl", {k_: v for k_, v in root.items() if not k_.startswith("_")})
        done["roots"] += 1
    if m["phase"] in FORK_PHASES:
        todo = plan(run)
        forks = {f["fork_id"]: f for f in _dedupe(read_jsonl(run.out / "forks.jsonl"), "fork_id")}
        root_rows_cache: dict[str, list[dict]] = {}
        for fork_id, arm, rep in todo["leaves_todo"]:
            if not run.time_left():
                done["deadline_hit"] = True
                break
            fork = forks[fork_id]
            if fork["root_id"] not in root_rows_cache:
                root_rows_cache[fork["root_id"]] = read_jsonl(run.work / "roots" / fork["root_id"] / "root_trials.jsonl")
            unit = leaf_unit(fork_id, arm, rep)
            try:
                leaf = run_leaf(run, fork, arm, rep, root_rows_cache[fork["root_id"]])
            except Stop:
                raise
            except Exception as exc:  # noqa: BLE001
                details = failure_details(exc, "leaf")
                _write_failure(run.out, "leaf", unit, details)
                log_failed_unit(run.out, unit, "leaf", details)
                done["failed"] += 1
                continue
            append_jsonl(run.out / "leaves.jsonl", leaf)
            done["leaves"] += 1
    done["exhausted"] = len(plan(run)["exhausted"])
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


def check_llm_provenance(args, cfg: dict) -> None:
    """Real llama.cpp runs need the GGUF sha256, the llama.cpp build and a host label (review m3)."""
    if cfg.get("kind") != "langgraph":
        return
    missing = []
    if not (args.gguf_sha256 or args.gguf):
        missing.append("--gguf or --gguf-sha256")
    if not (args.llama_build or args.llama_server_bin):
        missing.append("--llama-build or --llama-server-bin")
    if args.host_label in (None, "", "unknown"):
        missing.append("--host-label")
    if missing:
        raise SystemExit(f"an LLM run needs provenance: {', '.join(missing)}")


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phase", choices=PHASES, required=True)
    ap.add_argument("--node", required=True,
                    help="digits_mlp | tabular_mlp | synthetic_P0 | synthetic_P1 | synthetic_P2p | synthetic_P2m | synthetic_N0")
    ap.add_argument("--host-label", default="unknown", help='e.g. "TASL-2" (provenance)')
    ap.add_argument("--W", type=int, default=None, help="worker-run budget (S0.4 default: the LLM cap, non-binding)")
    ap.add_argument("--llm-cap", type=int, default=DEFAULT_LLM_CAP)
    ap.add_argument("--instances", type=int, default=1)
    ap.add_argument("--forks", type=float, default=4.0, help="expected uniform forks per root")
    ap.add_argument("--near-band", type=float, default=None,
                    help="b of the near-threshold oversample: |margin to the root policy's threshold| <= b (raw units)")
    ap.add_argument("--p-near", type=float, default=0.0, help="inclusion probability of a near-threshold decision")
    ap.add_argument("--aa-fraction", type=float, default=0.1)
    ap.add_argument("--reps", type=int, default=2, help="LLM repetitions per arm on channel forks")
    ap.add_argument("--reps-ordinary", type=int, default=1, help="LLM repetitions per arm on the other forks")
    ap.add_argument("--k-audit", type=int, default=DEFAULT_K)
    ap.add_argument("--seed-base", type=int, default=None, help="instance seed base (inside the phase's block)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--work", default=os.environ.get("R1_TMP", "/tmp/r1_tracks"))
    ap.add_argument("--deadline", type=float, default=1e12, help="seconds; no new unit starts after it")
    ap.add_argument("--dry-run", action="store_true", help="print the plan and exit (nothing runs)")
    ap.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES,
                    help="failed units are retried on later sessions up to this many times")
    ap.add_argument("--prior", default=None, help="A2-U prior file (fit_prior: output path)")
    ap.add_argument("--prior-sha256", default=None)
    ap.add_argument("--sigma-node", type=float, default=None)
    ap.add_argument("--g", type=float, default=None, help="declared run price (default 0.1 sigma_node)")
    ap.add_argument("--g0", type=float, default=None, help="pilot price of the 'a2u' policy (default --g)")
    ap.add_argument("--root-policy", default="a2u", help="S0.5 / S3 / synthetic: policy of roots, rebuilds and "
                    "continuations (m*), e.g. static:g=..,e2off=..")
    ap.add_argument("--obs-inflation", type=float, default=1.0, help="A2-U observation-variance inflation lambda")
    ap.add_argument("--within-key", choices=["estimated", "none"], default="estimated", help="fit_prior only")
    ap.add_argument("--a2-fraction", type=float, default=None, help="descriptive A2 roots (S3 default 0.2)")
    ap.add_argument("--policy", action="append", default=None, help="tune / campaign / S0.5 extra policies: a2u | "
                    "static:.. | matched_static:.. | dynamic:.. | pi_prime:<model_file> (repeatable)")
    ap.add_argument("--rep", type=int, action="append", default=None,
                    help="LLM repetition(s) of the policy campaigns (repeatable; default 0)")
    ap.add_argument("--jobs", default=None, help="tune: JSON list of {policy, instances, rep} jobs")
    ap.add_argument("--tune-grid", choices=["static", "dynamic", "magnitude", "all"], default=None,
                    help="tune phase: add a declared grid (needs --sigma-cmp-vary; dynamic/magnitude need --m-star)")
    ap.add_argument("--sigma-cmp-vary", type=float, default=None, help="grid unit sigma_cmp,vary (raw units)")
    ap.add_argument("--tune-g-extension", action="store_true", help="add g = 0.8 to the static grid")
    ap.add_argument("--m-star", default=None, help="g,h of the best static member, in sigma_cmp,vary units")
    ap.add_argument("--r-bar", type=float, default=0.0, help="centring of r in the dynamic grids (rev. 7 b)")
    ap.add_argument("--tau-bar", type=float, default=0.0, help="centring of tau_pred in the dynamic grids (rev. 7 b)")
    ap.add_argument("--truncate-W", default=None, help="S0.5b: comma-separated W values (e.g. 8,10,12,20)")
    ap.add_argument("--no-calibration", action="store_true", help="S0.5: skip the calibration audits")
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
    if args.node in SYNTHETIC_NODES and args.phase not in ("synthetic", "S0.4", "S0.5") + POLICY_PHASES:
        raise SystemExit("synthetic nodes run in the 'synthetic', 'S0.4', 'S0.5', 'tune' or 'campaign' phase only")
    if args.phase == "synthetic" and args.node not in SYNTHETIC_NODES:
        raise SystemExit("the 'synthetic' phase needs a synthetic node")
    if args.tune_grid:
        if args.phase != "tune" or args.sigma_cmp_vary is None:
            raise SystemExit("--tune-grid needs --phase tune and --sigma-cmp-vary")
        m_star = tuple(float(x) for x in args.m_star.split(",")) if args.m_star else None
        args.policy = list(args.policy or []) + tuning_grid(args.tune_grid, args.sigma_cmp_vary, m_star,
                                                            extend=args.tune_g_extension, r_bar=args.r_bar,
                                                            tau_bar=args.tau_bar)
    if args.jobs and args.phase != "tune":
        raise SystemExit("--jobs is a tune-phase option")
    if args.phase in POLICY_PHASES and not (args.policy or args.jobs):
        raise SystemExit(f"the {args.phase} phase needs at least one --policy (or --jobs)")
    if args.e2_verify:
        raise SystemExit("E2 verify is declared off for every Track S policy (rev.-5 amendment 3); not available")
    out, work = Path(args.out), Path(args.work)
    synth_params = json.loads(args.synthetic_params) if args.synthetic_params else None
    cfg = manager_cfg(args)
    check_llm_provenance(args, cfg)
    adapter = make_adapter(args.node, cfg, synth_params)
    prior, prior_sha, sigma_node = resolve_prior(args, adapter)
    g_declared = float(args.g if args.g is not None else G_UNITS * sigma_node)
    g0 = float(args.g0 if args.g0 is not None else g_declared)
    manifest = build_manifest(args, adapter, prior_sha, sigma_node, g_declared, g0)
    # Validate every policy string before anything runs.
    ctx = NodeContext(node=adapter.surface, start_files=adapter.start_files(), sigma_node=sigma_node,
                      runs_total=manifest["W"], memory_mode=manifest["memory_mode"])
    if prior is not None:
        for pol in set(manifest["policies"]) | {manifest["root_policy"]} | {j["policy"] for j in manifest["jobs"] or []}:
            policy_controller(pol, prior, ctx, g0=g0, W=manifest["W"])
    if (out / "manifest.json").exists():
        old = json.loads((out / "manifest.json").read_text())
        diff = {k: (old.get(k), manifest.get(k)) for k in MANIFEST_KEYS if old.get(k) != manifest.get(k)}
        if diff:
            raise SystemExit(f"refusing to resume {out}: the run parameters differ from its manifest: {diff}")
        manifest = old
    if args.dry_run:
        tmp_run = Run(args, adapter, out, work, manifest, prior, prior_sha, sigma_node, g_declared, g0,
                      None, None, time.time())  # type: ignore[arg-type]
        p = plan(tmp_run)
        print(json.dumps({"dry_run": True, "manifest": {k: manifest[k] for k in MANIFEST_KEYS if k in manifest},
                          "roots_todo": len(p["roots_todo"]), "forks_known": p["forks_known"],
                          "leaves_todo": len(p["leaves_todo"]), "exhausted": len(p["exhausted"])}, default=str))
        return 0
    out.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    gguf_sha = args.gguf_sha256 or (sha256_file(args.gguf) if args.gguf else "none")
    hc = harness_commit(HARNESS)
    provenance = Provenance(host=args.host_label, gpu=gpu_label(args.gpu), harness_commit=hc["commit"],
                            paper_commit=_git(REPO, "rev-parse", "HEAD"), manager_gguf_sha256=gguf_sha,
                            llama_build=llama_build(args), controller_version="unknown",
                            prior_sha256=prior_sha, phase=args.phase, label=args.label,
                            g_declared=g_declared, g0=g0, harness_dirty=bool(hc.get("dirty")),
                            paper_dirty=_git_dirty(REPO))
    run = Run(args, adapter, out, work, manifest, prior, prior_sha, sigma_node, g_declared, g0, provenance,
              AuditCache(out / "audit_runs.jsonl", adapter, work), time.time())
    start = utc()
    done = None
    try:
        done = session(run)
    finally:
        manifest = json.loads((out / "manifest.json").read_text())
        manifest["sessions"].append({"start_utc": start, "end_utc": utc(), "provenance": to_dict(provenance),
                                     "cpu": cpu_census(), "audit_runs": run.audits.runs,
                                     **({"done": done} if done is not None else {"interrupted": True})})
        (out / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    print(json.dumps({"out": str(out), **done}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
