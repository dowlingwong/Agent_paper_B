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
  leaves per arm x repetition, A/A leaves, audits. ``synthetic`` runs the synthetic control nodes (rev.-7 world
  nodes run in ``synthetic``, ``tune`` and ``campaign``; ``--synthetic-params`` gives variant / strength).
* ``tune`` (S0.7) — policy strings on dev instances (tuning seed block), every configuration on the same
  paired instances; ``--tune-grid static|dynamic`` adds the declared stage (``tuning_grid``, see Tune below);
  ``--jobs FILE`` gives an explicit list of (policy, instance subset, rep) jobs (e.g. successive halving).
* ``campaign`` (S3e) — every ``--policy`` x ``--rep`` on every fresh instance. The placebos (final review MINOR 1, 8):
  ``--placebo-policy m* --exact-placebo-n 10`` runs m* twice at rep 0 on the first 10 instances FIRST (a mismatch
  is a STOP before anything else runs); ``--descriptive-placebo-n 15`` runs m* at rep 1 on the first 15
  instances. ``--rep-instances n`` restricts repetitions other than 0 to the first n instances (e.g. the S0.5
  10-instance repetition subset).
* ``python -m r1.tracks.collect assemble --node N --out DIR --dev <tune out-dirs> --campaign <campaign out-dirs>
  [--fork <S3 / synthetic out-dirs>]`` — the analysis node directory (``dev_roots.jsonl``,
  ``campaign_roots.jsonl``, ``roots.jsonl`` + ``leaves.jsonl``), with checks and ``assemble.json``.

Policies: ``a2u`` (A2-U at g0), ``a2``, ``static:g,h``, ``dynamic:g0,b_budget,b_info,h0,h_budget,r1bar,taubar,r2bar``
(or its 5-value form), ``pi_prime:<model_file>``. Static and dynamic strings are positional, raw metric units,
and recorded in the analysis branch's spelling (``canonical_policy`` = ``analyze.policy_string``); the matched
static is a plain ``static:`` string. Execute uses ">=" and keep ">" in every policy (rev. 7.1 m9).

Tune (rev. 7, D2): ``--tune-grid static`` runs the 15 statics (g in {0, .05, .1, .2, .4} x h in {-.25, 0, .25}
sigma; ``--tune-g-extension`` adds g = .8) on 20 paired dev instances; ``--tune-grid dynamic --m-star static:g,h
--centres-from <static-stage roots.jsonl>`` runs the four fixed members (budget x1 sigma, info x0.5, keep+ / keep-
x0.5 sigma) centred at m*'s eligible-decision means on 40 paired dev instances. Both stages use instances
0, 1, ... of the tune seed block, so the members' first 20 instances are the statics' 20 (same instance ids).

Seeds (all declared below and recorded in the manifest):
* instance blocks per phase (bounds checked; review m4);
* audit blocks per phase (review B1): S0.4, S0.5 (calibration and S0.5b), tune (S0.7), S3 (S3a), campaign
  (S3e, used by no other phase), synthetic, fixture; pairwise disjoint and disjoint from the instance blocks;
  audit seeds are PER INSTANCE (final review MAJOR 1): instance i of a phase is audited on
  base + i * 20 + k, k < K (``instance_audit_seeds``), shared by every policy and repetition on that instance,
  for real and synthetic nodes alike;
* repetitions (final review MAJOR 2): a campaign's ``rep`` is its D26 repetition; 0 is the primary, 1 the
  descriptive placebo's second repetition (the analysis uses the same convention); fork leaves use
  REP_BASE + 1, 2, ...;
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
import dataclasses
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
from autoresearch.manager.langgraph_manager import manager_seed  # noqa: E402
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
# Audit seeds are PER INSTANCE (final review MAJOR 1, coordinator decision): instance i of a phase (i = its
# seed minus the phase's instance-block start) is audited on seeds base + i * AUDIT_STRIDE + k, k < K, from the
# phase's own audit block; every policy and repetition on that instance shares them (pairing kept), and no two
# instances share a seed, so a recurring configuration does not carry one fixed audit error across the sample.
# Real and synthetic nodes use the same rule.
AUDIT_STRIDE = 20                                   # max K
AUDIT_BLOCK_CAPACITY = 100_000
AUDIT_SEED_BASES = {"S0.4": 100_000, "S0.5": 200_000, "tune": 300_000, "S3": 400_000, "campaign": 500_000,
                    "synthetic": 600_000, "fixture": 700_000}
AUDIT_SEED_BLOCKS = {name: range(base, base + AUDIT_BLOCK_CAPACITY) for name, base in AUDIT_SEED_BASES.items()}
PHASE_AUDIT_BLOCK = {"S0.4": "S0.4", "S0.5": "S0.5", "S0.5b": "S0.5", "tune": "tune", "S3": "S3",
                     "campaign": "campaign", "synthetic": "synthetic", "fixture": "fixture"}
DEV_K = 5                                           # S0.4 dev rows, K = 5
SELECTION_SEED = 35001
REP_BASE = 100                                    # leaf repetition r -> D26 repetition REP_BASE + r
CHANNEL_FRACTION = 1.0 / 3.0
A2_FRACTION_DEFAULT = 0.0                        # descriptive A2 roots: none in any Track S phase (ops review)
DEFAULT_LLM_CAP = 40
DEFAULT_K = 5
DEFAULT_MAX_RETRIES = 2
G_UNITS = 0.1                                     # declared g = 0.1 sigma_node unless --g (C3 convention)
# sigma_node (median paired sd Delta-hat), runbook §1 B2 (NOISE_FLOOR_COMMON_20261022); a prior file overrides.
SIGMA_NODE_DEFAULTS = {"digits_mlp": 0.0066, "tabular_mlp": 0.0019}
PHASES = ("S0.4", "fit_prior", "set_obs_inflation", "liveness", "S0.5", "S0.5b", "S3", "synthetic", "tune",
          "campaign")
LATER_PHASES = ("S0.5b", "S3", "synthetic", "tune", "campaign")   # obs_inflation must match the prior file's
BLAS_VARS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
DEFAULT_WORK = os.environ.get("R1_TMP", "/tmp/r1_tracks")
DEFAULT_MAX_TRANSPORT_FAILURES = 3
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


def audit_rule(phase: str, k: int) -> dict:
    """The phase's per-instance audit-seed rule (recorded in the manifest)."""
    block = PHASE_AUDIT_BLOCK[phase]
    if not 1 <= k <= AUDIT_STRIDE:
        raise SystemExit(f"--k-audit must lie in 1..{AUDIT_STRIDE}")
    return {"block": block, "base": AUDIT_SEED_BASES[block], "stride": AUDIT_STRIDE, "K": int(k),
            "instance_block": list(INSTANCE_SEED_BLOCKS[block]),
            "rule": "seed = base + (instance_seed - instance_block[0]) * stride + k, k < K"}


def instance_audit_seeds(phase: str, instance_seed: int, k: int) -> tuple[int, ...]:
    """The K audit seeds of one instance of a phase (shared by every policy and repetition on it)."""
    r = audit_rule(phase, k)
    lo, hi = r["instance_block"]
    if not lo <= int(instance_seed) < hi:
        raise ValueError(f"instance seed {instance_seed} is outside the {r['block']} instance block [{lo}, {hi})")
    first = r["base"] + (int(instance_seed) - lo) * AUDIT_STRIDE
    return tuple(range(first, first + int(k)))


# ---------------------------------------------------------------------------
# JSONL with crash tolerance (review M5, m8)
# ---------------------------------------------------------------------------

def _text(path: Path) -> str:
    if str(path).endswith(".gz"):
        import gzip
        with gzip.open(path, "rt") as fh:
            return fh.read()
    return path.read_text()


def read_jsonl(path: Path) -> list[dict]:
    """Rows of a JSONL file (or ``.jsonl.gz``; ``x.jsonl`` falls back to ``x.jsonl.gz``); a truncated
    (unparsable) LAST line is ignored, a corrupt earlier line raises."""
    path = Path(path)
    if not path.exists() and Path(str(path) + ".gz").exists():
        path = Path(str(path) + ".gz")
    if not path.exists():
        return []
    lines = [line for line in _text(path).splitlines() if line.strip()]
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

    def files_after(self, rows: list[dict], start: dict[str, str], seed: int, upto: int) -> dict[str, str]:
        return config_after(rows, start, upto)

    def candidate_files(self, inc_files: dict[str, str], proposal, seed: int, runs_used: int) -> dict[str, str]:
        return apply_edit(inc_files, proposal.extra["structured_edit"])

    def manager(self, seed: int, repetition: int, seed_key: str | None = None, fork_trial: int | None = None):
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

    @property
    def world(self) -> bool:
        return bool(getattr(self.node, "synthetic_world", False))

    def bind(self, *, W: int, llm_cap: int) -> None:
        """World nodes take the run's W and LLM cap (their trial horizon and the P2 budget fraction)."""
        if self.world:
            self.node = self.node.bind(W=W, llm_cap=llm_cap)

    def leaf_worker(self, into: Path, snapshot):
        if self.world:  # the world worker counts the campaign's runs from the snapshot's count on
            return self.node.worker(into, int(snapshot.train_seed),
                                    runs0=int(snapshot.compute_budget_state.get("worker_runs", 0)))
        return self.node.worker(into, int(snapshot.train_seed))

    def manager(self, seed: int, repetition: int, seed_key: str | None = None, fork_trial: int | None = None):
        if self.world:
            return self.node.manager(seed, repetition, fork_trial=fork_trial)
        return self.node.manager(seed, repetition)  # scripted: keyed by the instance seed

    def files_after(self, rows: list[dict], start: dict[str, str], seed: int, upto: int) -> dict[str, str]:
        if self.world:
            return self.node.files_after(rows, start, seed, upto)
        return config_after(rows, start, upto)

    def candidate_files(self, inc_files: dict[str, str], proposal, seed: int, runs_used: int) -> dict[str, str]:
        if self.world:
            return self.node.candidate_files(inc_files, proposal, seed, runs_used)
        return apply_edit(inc_files, proposal.extra["structured_edit"])

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
        # A world node's value is carried by its file text (true value, offset, keep log), not by the
        # configuration alone: key its audits on the text.
        h = cfg_hash(files) if not getattr(self.adapter, "world", False) else \
            "text:" + hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()[:16]
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

def fmt_num(x: float) -> str:
    """Number format of policy strings (the analysis branch's ``analyze.fmt_num``)."""
    return format(round(float(x), 9) + 0.0, ".9g")


def policy_string(kind: str, params) -> str:
    """``static:g,h`` or ``dynamic:g0,b_budget,b_info,h0,h_budget[,r1bar,taubar,r2bar]`` (``analyze.policy_string``)."""
    ok = (kind == "static" and len(params) == 2) or (kind == "dynamic" and len(params) in (5, 8))
    if not ok:
        raise ValueError(f"bad policy {kind}{tuple(params)}")
    return f"{kind}:" + ",".join(fmt_num(p) for p in params)


def parse_policy(policy: str) -> tuple[str, tuple[float, ...]]:
    """Positional static / dynamic strings (rev. 7, as ``analyze.parse_policy``). The rev.-6 key=value forms and
    ``matched_static:`` are refused: the matched static is the static string ``static:g_eff,h_eff``."""
    if policy.startswith("matched_static:"):
        raise ValueError(f"{policy!r}: the matched static is a plain static policy, static:g,h (rev. 7)")
    kind, rest = policy.split(":", 1)
    if "=" in rest:
        raise ValueError(f"{policy!r}: policy strings are positional since rev. 7 "
                         "(static:g,h | dynamic:g0,b_budget,b_info,h0,h_budget,r1bar,taubar,r2bar)")
    try:
        vals = tuple(float(x) for x in rest.split(","))
    except ValueError as exc:
        raise ValueError(f"bad policy string {policy!r}") from exc
    if not ((kind == "static" and len(vals) == 2) or (kind == "dynamic" and len(vals) in (5, 8))) \
            or not all(math.isfinite(v) for v in vals):
        raise ValueError(f"bad policy string {policy!r}")
    return kind, vals


def canonical_policy(policy: str) -> str:
    """The analysis spelling of a static / dynamic string (other policies unchanged), so records match it."""
    if policy.startswith(("static:", "dynamic:", "matched_static:")):
        return policy_string(*parse_policy(policy))
    return policy


def as_dynamic(policy: str) -> tuple[float, ...]:
    """8-tuple (g0, b_budget, b_info, h0, h_budget, r1bar, taubar, r2bar) of a static or dynamic string."""
    kind, v = parse_policy(policy)
    if kind == "static":
        return (v[0], 0.0, 0.0, v[1], 0.0, 0.0, 0.0, 0.0)
    return v if len(v) == 8 else v + (0.0, 0.0, 0.0)


def policy_controller(policy: str, prior, ctx, *, g0: float, obs_inflation: float = 1.0, W: int | None = None):
    """Named policies (module docstring)."""
    if policy == "a2u":
        return a2u.A2UController(prior, ctx, g=g0, obs_inflation=obs_inflation, W=W)
    if policy == "a2":
        return a2u.A2UController(prior, ctx, g=g0, update=False, obs_inflation=obs_inflation, W=W)
    if policy.startswith(("static:", "dynamic:", "matched_static:")):
        name = canonical_policy(policy)
        g, bb, bi, h, hb, r1, tb, r2 = as_dynamic(name)
        if name.startswith("static:"):
            return a2u.A2UController.static_price(prior, ctx, g, e2_offset=h, obs_inflation=obs_inflation, W=W,
                                                  policy_name=name)
        return a2u.A2UController.dynamic(prior, ctx, g0=g, b_budget=bb, b_info=bi, h0=h, h_budget=hb, r1_bar=r1,
                                         tau_bar=tb, r2_bar=r2, obs_inflation=obs_inflation, W=W, policy_name=name)
    if policy.startswith("pi_prime:"):
        model, sha = a2u.load_score_model(policy[len("pi_prime:"):])
        return a2u.A2UController(prior, ctx, g=g0, score_fn=model, obs_inflation=obs_inflation, W=W,
                                 policy_name=f"pi_prime:{sha[:12]}")
    raise ValueError(f"unknown or unimplemented policy {policy!r} (budget_dp / probe_first are not implemented)")


def policy_family(policy: str) -> str:
    return policy.split(":", 1)[0]


def _policy_tag(policy: str) -> str:
    return hashlib.sha256(policy.encode()).hexdigest()[:8]


# Rev. 7 (D2) tuning declaration, in sigma units (the analysis branch's ``FamilyDecl`` defaults).
TUNE_G = (0.0, 0.05, 0.1, 0.2, 0.4)   # g = 0 = execute every non-rule proposal; 5 x 3 = 15 statics
TUNE_G_EXTENSION = (0.8,)             # the one edge extension (``--tune-g-extension``)
TUNE_H = (-0.25, 0.0, 0.25)
# The four fixed single-channel members anchored at m* (no magnitude grids): b_budget = +1 sigma,
# b_info = +0.5 (dimensionless, x tau_pred), h_budget = +-0.5 sigma; names as ``FamilyDecl.members``.
DYNAMIC_MEMBERS = {"budget×1": ("budget", 1.0), "info×0.5": ("info", 0.5), "keep+×0.5": ("keep+", 0.5),
                   "keep-×0.5": ("keep-", 0.5)}
TUNE_N_STATIC = 20    # paired dev instances of the static stage (instances 0..19 of the tune block)
TUNE_N_MEMBERS = 40   # paired dev instances of the member stage (0..39: the first 20 are the statics' instances)


def static_grid(sigma: float, extend: bool = False) -> list[str]:
    gs = TUNE_G + (TUNE_G_EXTENSION if extend else ())
    return [policy_string("static", (g * sigma, h * sigma)) for g in gs for h in TUNE_H]


def extension_grid(sigma: float) -> list[str]:
    """The g = 0.8 edge extension alone (3 statics; ``analyze.FamilyDecl.extension_configs``)."""
    return [policy_string("static", (g * sigma, h * sigma)) for g in TUNE_G_EXTENSION for h in TUNE_H]


def member_policies(m_star: str, sigma: float, centres: dict | None = None) -> dict[str, str]:
    """The four members anchored at m* = static:g*,h* and centred at ``centres`` (r1bar, taubar, r2bar)."""
    kind, (g, h) = parse_policy(m_star)
    if kind != "static":
        raise ValueError("m* must be a static policy string")
    c = centres or {"r1bar": 0.0, "taubar": 0.0, "r2bar": 0.0}
    cc = (float(c["r1bar"]), float(c["taubar"]), float(c["r2bar"]))
    out = {}
    for name, (ch, u) in DYNAMIC_MEMBERS.items():
        p = {"budget": (g, u * sigma, 0.0, h, 0.0), "info": (g, 0.0, u, h, 0.0),
             "keep+": (g, 0.0, 0.0, h, u * sigma), "keep-": (g, 0.0, 0.0, h, -u * sigma)}[ch]
        out[name] = policy_string("dynamic", p + cc)
    return out


def decision_centres(decisions: list[dict]) -> dict:
    """r1bar, taubar over eligible E1 decisions and r2bar over eligible E2 decisions (``analyze.decision_centres``)."""
    e1 = [d for d in decisions if d.get("eligible") and d["epoch"] == "E1"]
    e2 = [d for d in decisions if d.get("eligible") and d["epoch"] == "E2"]
    if any(d.get("r") is None for d in e1 + e2):
        raise ValueError("decision_centres: a decision lacks r")
    r1 = float(np.mean([float(d["r"]) for d in e1])) if e1 else 0.0
    tb = float(np.mean([float(d["tau_pred"]) for d in e1 if d.get("tau_pred") is not None])) if e1 else 0.0
    r2 = float(np.mean([float(d["r"]) for d in e2])) if e2 else r1
    return {"r1bar": r1, "taubar": tb, "r2bar": r2, "n_E1": len(e1), "n_E2": len(e2)}


def centres_from_roots(path: str, m_star: str) -> dict:
    """Centres from m*'s dev roots (the static-stage ``roots.jsonl``)."""
    m_star = canonical_policy(m_star)
    decs = [d for r in read_jsonl(Path(path)) if r.get("policy") == m_star for d in (r.get("decisions") or [])
            if d.get("eligible")]
    if not decs:
        raise SystemExit(f"--centres-from {path}: no eligible decisions of {m_star}")
    return decision_centres(decs)


def tuning_grid(stage: str, sigma: float, m_star: str | None = None, extend: bool = False,
                centres: dict | None = None) -> list[str]:
    """Declared tuning configurations (raw units; ``sigma`` = the node's sigma unit).

    ``static``: the 15 statics g x h (+3 with ``extend``); ``dynamic``: the four centred members at m*."""
    if stage == "static":
        return static_grid(sigma, extend)
    if stage == "dynamic":
        if m_star is None:
            raise ValueError("the dynamic stage needs m* (a static policy string)")
        return list(member_policies(m_star, sigma, centres).values())
    raise ValueError(f"unknown tuning stage {stage!r} (rev. 7: static | dynamic)")


def resolve_m_star(value: str | None, sigma: float | None) -> str | None:
    """--m-star: ``static:g,h`` (raw units) or ``g,h`` in sigma units; returned as the canonical static string."""
    if not value:
        return None
    if value.startswith("static:"):
        return canonical_policy(value)
    g, h = (float(x) for x in value.split(","))
    return policy_string("static", (g * float(sigma), h * float(sigma)))


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

    def seeds(self, instance_seed: int) -> tuple:
        """This phase's audit seeds of one instance (``instance_audit_seeds``)."""
        return instance_audit_seeds(self.manifest["phase"], int(instance_seed), int(self.manifest["K"]))

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


def root_variant(policy: str | None, rep: int, *, primary: bool, dup: bool = False) -> str:
    """Root-id suffix; ``dup``: the exact placebo's second run of the same (policy, rep) on an instance."""
    if primary:
        return ""
    if policy == "a2":
        return "__A2"
    return f"__{_policy_tag(policy or 'a2u')}_r{rep}" + ("_dup" if dup else "")


def w_binds(runs: int, W: int, trials: int, trial_cap: int) -> bool:
    """W binds iff the campaign used its W runs while proposals remained (review m5)."""
    return runs >= W and trials < trial_cap


def decisions_from(rows: list[dict], events: list[dict], snapshots: dict | None) -> list[dict]:
    """Per-trial E1/E2 decisions of a campaign from its ledger and ``control_decision`` events.

    ``snapshots``: the forked root's snapshots (a fork-eligible decision needs one); ``None`` for campaigns that
    are not forked (tune / campaign / extra roots), whose eligibility is the controller's alone."""
    snap_ok = (lambda key: True) if snapshots is None else (lambda key: key in snapshots)
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
            eligible = bool(d.get("eligible")) and b >= 2 and snap_ok(("E1", b))
            out.append({"index": b, "epoch": "E1", "action": "skip" if e1["action"] == "skip" else "execute",
                        "index_value": d.get("v_star"), "margin": d.get("margin"), "eligible": eligible,
                        "r": d.get("r"), "tau_pred": d.get("tau_pred"),
                        "skip_reason": d.get("skip_reason"), "detail": d})
        e2 = ev.get("E2")
        if e2 is not None:
            d = e2.get("detail") or {}
            e1_ok = bool(((ev.get("E1") or {}).get("detail") or {}).get("eligible"))
            eligible = bool(d.get("eligible")) and e1_ok and row.get("validity_status") == "valid" \
                and snap_ok(("E2", b))
            action = {"kept": "keep", "discarded": "discard"}.get(row["decision"], str(row["decision"]))
            out.append({"index": b, "epoch": "E2", "action": action,
                        "index_value": d.get("m_hat"), "margin": d.get("margin"), "eligible": eligible,
                        "r": d.get("r"), "tau_pred": d.get("tau_pred"), "detail": d})
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


def run_root(run: Run, k: int, *, policy: str | None, rep: int, primary: bool, dup: bool = False) -> dict:
    """One campaign of instance k (``primary``: the forked root of a fork phase). Raises on failure."""
    adapter = run.adapter
    seed = instance_seed(run, k)
    cid = seed_key_for(adapter.name, seed)
    root_id = root_id_for(run, seed, root_variant(policy, rep, primary=primary, dup=dup))
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
    decisions = decisions_from(rows, events, snaps.written if snaps else None)
    start = adapter.start_files()
    y_start = _mean(run.audits.metrics(seed, start, run.seeds(seed)))
    y1 = _mean(run.audits.metrics(seed, adapter.files_after(rows, start, seed, 1), run.seeds(seed))) if rows else None
    final = _workspace_files(adapter, node_dir)
    y_seeds = run.audits.metrics(seed, final, run.seeds(seed))
    runs_used = worker_runs_of(rows, events)
    rec = RootRecord(schema=TRACKS_ROOT_SCHEMA, node=adapter.name, instance_id=f"{adapter.name}__s{seed}",
                     root_id=root_id, W=run.W, llm_cap=run.cap, y_start=y_start, y_after_trial1=y1,
                     y_terminal=_mean(y_seeds),
                     eligible_e1=sum(1 for d in decisions if d["epoch"] == "E1" and d["eligible"]),
                     eligible_e2=sum(1 for d in decisions if d["epoch"] == "E2" and d["eligible"]),
                     binding=w_binds(runs_used, run.W, len(rows), int(kwargs["budget"])), runs_used=runs_used,
                     llm_calls=_llm_calls(events),
                     decisions=[{k_: v for k_, v in d.items() if k_ != "detail"} for d in decisions],
                     provenance=_prov(run, controller), policy=policy or run.root_policy, rep=int(rep),
                     llm_seed_base=int(manager_seed(cid, 0, int(rep), 0)))
    out = to_dict(rec)
    out["_snapshots"] = {f"{e}_b{b:03d}": p for (e, b), p in (snaps.written.items() if snaps else ())}
    out["_y_terminal_per_seed"] = y_seeds
    out["_audit_seeds"] = list(run.seeds(seed))
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
    out = Path(args.out)
    manifest = json.loads((out / "manifest.json").read_text())
    if manifest["phase"] != "S0.5":
        raise SystemExit("S0.5b post-processes an S0.5 output directory")
    # The S0.5 work dir holds the campaign ledgers (ops review B3): use the recorded one; never fall back.
    if manifest.get("work"):
        work = Path(manifest["work"])
        if args.work and Path(args.work).resolve() != work.resolve():
            raise SystemExit(f"S0.5b: --work {args.work} differs from the S0.5 work dir {work} recorded in the "
                             "manifest; the ledgers are there")
    elif args.work:
        work = Path(args.work)
    else:
        raise SystemExit("S0.5b: the S0.5 manifest records no work dir; pass the S0.5 --work explicitly")
    adapter = make_adapter(manifest["node"], manifest.get("manager") or {}, manifest.get("synthetic_params"))
    if adapter.synthetic and adapter.world:
        raise SystemExit("S0.5b does not take world synthetic nodes")
    audits = AuditCache(out / "audit_runs.jsonl", adapter, work)
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
        ledger = work / "roots" / root["root_id"] / "root_trials.jsonl"
        rows = read_jsonl(ledger)
        if not rows:
            raise SystemExit(f"S0.5b: the campaign ledger {ledger} is missing or empty; refusing (a truncated "
                             "incumbent cannot be rebuilt without it, and the start configuration is never audited "
                             "in its place)")
        seed = int(root["instance_id"].rsplit("__s", 1)[1])
        seeds = instance_audit_seeds("S0.5b", seed, int(manifest["K"]))  # per instance, the S0.5 audit block
        for W in Ws:
            if (root["root_id"], W) in done:
                continue
            if W > int(root["W"]):
                raise SystemExit(f"cannot truncate a W={root['W']} root at W={W}")
            prefix, binding = truncate_at_W(rows, W)
            if not prefix:
                raise SystemExit(f"S0.5b: {root['root_id']} has no trial before W={W} (ledger {ledger})")
            files = config_after(prefix, start, int(prefix[-1]["budget_index"]))
            ys = audits.metrics(seed, files, seeds)
            append_jsonl(out / "s05b_truncated.jsonl", {
                "root_id": root["root_id"], "instance_id": root["instance_id"], "W": W, "binding": binding,
                "policy": root.get("policy"), "rep": root.get("rep", 0),
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


def _paired_sd(cand: list, inc: list) -> float | None:
    """sd over audit seeds of the paired candidate - incumbent difference (Delta-hat noise under ``vary``)."""
    d = [c - i for c, i in zip(cand, inc) if c is not None and i is not None]
    return float(np.std(d, ddof=1)) if len(d) > 1 else None


def dev_rows(run: Run, rows: list[dict], seed: int, cid: str) -> None:
    """Audit every executed non-rule proposal of a dev campaign on the S0.4 block (candidate vs incumbent)."""
    from r1.c3.control import edit_kind
    for p in _audited_proposals(run, rows, cid, "tracks_S0.4"):
        da, se, k = _paired(run.audits.metrics(seed, p.candidate_files, instance_audit_seeds("S0.4", seed, DEV_K)),
                            run.audits.metrics(seed, p.incumbent_files, instance_audit_seeds("S0.4", seed, DEV_K)))
        append_jsonl(run.out / "s04_rows.jsonl", {
            "node": run.adapter.name, "instance": cid, "budget_index": p.budget_index,
            "key": p.edit.get("symbol"), "sign": a2u.sign_of(p.features.get("direction")),
            "kind": edit_kind(p.edit), "delta_hat": p.outcome["delta_hat"], "delta_audit": da, "se": se, "k": k,
            "seeds": list(instance_audit_seeds("S0.4", seed, DEV_K))})


def calibration_rows(run: Run, rows: list[dict], seed: int, cid: str, root_id: str, controller) -> None:
    """S0.5 calibration input (review M6): each executed non-rule proposal of a primary S0.5 root, audited on
    the S0.5 block (never the S0.4 training block), with the root controller's 80 % predictive interval of its
    audited Delta (widened by the audit's se) and its ``n_group`` stratum."""
    props = {p.budget_index: p for p in _audited_proposals(run, rows, cid, "tracks_S0.5")}
    audited, ses, sds, ks = {}, {}, {}, {}
    for b, p in props.items():
        cand = run.audits.metrics(seed, p.candidate_files, run.seeds(seed))
        inc = run.audits.metrics(seed, p.incumbent_files, run.seeds(seed))
        da, se, k = _paired(cand, inc)
        audited[b], ses[b], sds[b], ks[b] = da, se, _paired_sd(cand, inc), k
    for iv in a2u.predictive_intervals(rows, controller, level=0.8, audit_se=ses):
        b = iv["budget_index"]
        if b not in props:
            continue
        da = audited[b]
        append_jsonl(run.out / "s05_calibration.jsonl", {
            "root_id": root_id, "instance": cid, **iv, "delta_audit": da, "se": ses[b], "sd_paired": sds[b], "k": ks[b],
            "covered": None if da is None else bool(iv["lo"] <= da <= iv["hi"]), "audit_seeds": list(run.seeds(seed))})


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
        manager=adapter.manager(int(fork["seed"]), repetition, seed_key=snap.campaign_id,
                                fork_trial=int(fork["index"])),
        keep_prior=controller.keep_prior)
    rows = read_jsonl(result.restored.records_path)
    events = read_jsonl(result.restored.events_path)
    new = rows[len(snap.ledger_prefix):]
    first, after = new[0], new[1:]
    details = _e1_details(events)
    seed = int(fork["seed"])
    final = _workspace_files(adapter, into)
    y_seeds = run.audits.metrics(seed, final, run.seeds(seed))
    immediate = 0.0
    if first["decision"] == "kept":
        inc_files = {k: v.decode() for k, v in snap.incumbent_files.items() if v is not None}
        if fork["epoch"] == "E2":
            cand_files = {k: v.decode() for k, v in snap.editable_files.items() if v is not None}
        else:
            cand_files = adapter.candidate_files(inc_files, snap.proposal, seed,
                                                 int(snap.compute_budget_state.get("worker_runs", 0)) + 1)
        immediate = paired_increment(run.audits.metrics(seed, cand_files, run.seeds(seed)),
                                     run.audits.metrics(seed, inc_files, run.seeds(seed)))
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
        y_terminal_per_seed=y_seeds, audit_seeds=list(run.seeds(seed)), runs_used=runs_used, llm_calls=_llm_calls(events),
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
                 "aa_fraction", "reps", "reps_ordinary", "K", "audit_block", "audit_rule", "seed_base",
                 "memory_mode", "skip_display", "g_declared", "g0", "prior_sha256", "manager", "obs_inflation",
                 "a2_fraction", "policies", "llm_reps", "rep_instances", "root_policy", "jobs", "calibration",
                 "synthetic_params", "host", "exact_placebo", "descriptive_placebo", "shard", "exact_placebo_only",
                 "work")
LABELS = ("FIXTURE", "ENGINEERING_ONLY", "PILOT", "EVIDENCE")   # the analysis' LABEL_RANK
PRIMARY_REP = 0               # the D26 repetition of every primary campaign (S3e pairs pi* and m* at rep 0)
DESCRIPTIVE_PLACEBO_REP = 1   # the descriptive placebo's second repetition


def build_manifest(args, adapter, prior_sha: str, sigma_node: float, g_declared: float, g0: float) -> dict:
    phase = args.phase
    W = args.W if args.W is not None else (args.llm_cap if phase == "S0.4" else None)
    if W is None:
        raise SystemExit("--W is required for this phase (S0.4 defaults to the LLM cap: non-binding)")
    k = int(args.k_audit)
    rule = audit_rule(phase, k)
    block = rule["block"]
    lo, hi = INSTANCE_SEED_BLOCKS[phase]
    seed_base = int(args.seed_base if args.seed_base is not None else lo)
    jobs = load_jobs(args.jobs) if args.jobs else None
    if jobs:
        jobs = [{**j, "policy": canonical_policy(j["policy"])} for j in jobs]
    n_instances = (max(k_ for j in jobs for k_ in j["instances"]) + 1) if jobs else int(args.instances or 1)
    if not (lo <= seed_base and seed_base + n_instances <= hi):
        raise SystemExit(f"instance seeds {seed_base}..{seed_base + n_instances - 1} leave the {phase} block "
                         f"[{lo}, {hi}) (review m4)")
    return {
        "schema": MANIFEST_SCHEMA, "label": args.label, "phase": phase, "node": adapter.name, "W": int(W),
        "llm_cap": int(args.llm_cap), "instances": n_instances, "forks": float(args.forks),
        "near_band": args.near_band, "p_near": float(args.p_near), "aa_fraction": float(args.aa_fraction),
        "reps": int(args.reps), "reps_ordinary": int(args.reps_ordinary), "K": k, "audit_block": block,
        "audit_rule": rule,
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
        "policies": [canonical_policy(p) for p in (args.policy or [])], "llm_reps": list(args.rep or [0]),
        "rep_instances": args.rep_instances, "exact_placebo": _placebo_decl(args, "exact"),
        "descriptive_placebo": _placebo_decl(args, "descriptive"),
        "root_policy": canonical_policy(args.root_policy), "tune_stage": getattr(args, "tune_grid", None),
        "centres": getattr(args, "centres", None), "jobs": jobs, "calibration": bool(phase == "S0.5" and not args.no_calibration),
        "max_retries": int(args.max_retries), "e2_verify": False,
        "synthetic_params": json.loads(args.synthetic_params) if args.synthetic_params else None,
        "synthetic_node": adapter.node.describe() if adapter.synthetic else None,
        "host": args.host_label, "created_utc": utc(), "sessions": [],
        "shard": args.shard, "exact_placebo_only": bool(args.exact_placebo_only),
        "work": str(Path(args.work).resolve()),
    }


def _placebo_decl(args, kind: str) -> dict | None:
    """Campaign phase: the exact placebo (the policy again at rep 0 on the first n instances; run FIRST, a
    mismatch is a STOP) and the descriptive placebo (the policy at rep 1 on the first n instances)."""
    n = getattr(args, f"{kind}_placebo_n")
    pol = getattr(args, "placebo_policy")
    if not n:
        return None
    if args.phase != "campaign" or not pol:
        raise SystemExit(f"--{kind}-placebo-n needs --phase campaign and --placebo-policy")
    return {"policy": canonical_policy(pol), "instances": int(n),
            "rep": PRIMARY_REP if kind == "exact" else DESCRIPTIVE_PLACEBO_REP}


def manager_cfg(args) -> dict:
    """Synthetic nodes: their scripted manager. Real nodes (ops review M1): ``--manager`` is required; ``scripted``
    only with ``--dry-run`` or label FIXTURE."""
    if args.node in SYNTHETIC_NODES:
        return {"kind": "scripted_synthetic"}
    if args.manager is None:
        raise SystemExit("--manager is required for real nodes (llamacpp | scripted; scripted only with --dry-run "
                         "or --label FIXTURE)")
    if args.manager == "scripted" and not (args.dry_run or args.label == "FIXTURE"):
        raise SystemExit("--manager scripted on a real node needs --dry-run or --label FIXTURE")
    if args.manager == "llamacpp":
        if not args.manager_model or not args.manager_model.startswith("llamacpp/"):
            raise SystemExit("--manager llamacpp needs --manager-model llamacpp/<alias> (LLAMACPP_BASE_URL set)")
        cfg = {"kind": "langgraph", "model": args.manager_model, "temperature": 0.2,
               "transport_max_attempts": int(args.transport_max_attempts),
               # R1-CACHEPROMPT-FALSE (31 Oct 2026): the value the harness sends on every request is
               # recorded here, so a manifest states the setting it ran under.
               "cache_prompt": _manager_cache_prompt()}
        if args.proposal_schema:
            cfg["proposal_schema"] = args.proposal_schema
        return cfg
    return {"kind": "scripted", "model": "scripted_random", "temperature": 0.2}


def _manager_cache_prompt() -> bool:
    """The ``cache_prompt`` the llamacpp provider sends (delegated to the harness so the two cannot drift).

    R1-CACHEPROMPT-FALSE (31 Oct 2026): llama-server's prompt cache makes otherwise identical
    (prompt, seed) calls non-identical; the harness sends ``cache_prompt`` explicitly and this records it.
    """
    from r1.harness import import_harness
    import_harness()
    from autoresearch.llm.providers import llamacpp_cache_prompt
    return llamacpp_cache_prompt()


def _dedupe(rows: list[dict], key: str) -> list[dict]:
    seen, out = set(), []
    for r in rows:
        if r[key] in seen:
            continue
        seen.add(r[key])
        out.append(r)
    return out


def root_jobs(run: Run) -> list[tuple[int, str | None, int, bool, str, bool]]:
    """(instance k, policy, repetition, primary, root_id, dup) of every campaign this run must have, in run
    order. Campaign phase: the exact placebo pairs (policy at rep 0, then its duplicate) run FIRST (final review
    MINOR 8); the descriptive placebo (rep 1) on its instances. ``rep_instances``: repetitions other than 0 run
    on the first n instances only (MINOR 9)."""
    m = run.manifest
    out, seen = [], set()

    def add(k: int, pol: str | None, rep: int, primary: bool, dup: bool = False) -> None:
        rid = root_id_for(run, instance_seed(run, k), root_variant(pol, rep, primary=primary, dup=dup))
        if rid not in seen:
            seen.add(rid)
            out.append((k, pol, rep, primary, rid, dup))

    def rep_ok(k: int, rep: int) -> bool:
        n = m.get("rep_instances")
        return rep == PRIMARY_REP or n is None or k < int(n)

    if m["phase"] in POLICY_PHASES:
        ex, de = m.get("exact_placebo"), m.get("descriptive_placebo")
        if ex:
            for k in range(min(int(ex["instances"]), m["instances"])):
                add(k, ex["policy"], ex["rep"], False)
                add(k, ex["policy"], ex["rep"], False, dup=True)
        if m.get("jobs"):
            for job in m["jobs"]:
                for k in job["instances"]:
                    add(k, job["policy"], job["rep"], False)
        else:
            for k in range(m["instances"]):
                for pol in m["policies"]:
                    for rep in m["llm_reps"]:
                        if rep_ok(k, rep):
                            add(k, pol, rep, False)
        if de:
            for k in range(min(int(de["instances"]), m["instances"])):
                add(k, de["policy"], de["rep"], False)
        return _shard_filter(m, out)
    for k in range(m["instances"]):
        add(k, None, 0, True)
        for pol in m["policies"]:
            for rep in m["llm_reps"]:
                if pol == run.root_policy and rep == 0:
                    continue  # that is the primary root
                if rep_ok(k, rep):
                    add(k, pol, rep, False)
        if m["a2_fraction"] and _u("a2", root_id_for(run, instance_seed(run, k)))[0] < m["a2_fraction"]:
            add(k, "a2", 0, False)
    return _shard_filter(m, out)


def parse_shard(spec: str | None) -> tuple[int, int] | None:
    """``--shard i/k`` -> (i, k), 0 <= i < k; None = unsharded."""
    if not spec:
        return None
    try:
        i, k = (int(x) for x in str(spec).split("/"))
    except ValueError as exc:
        raise SystemExit(f"--shard must be i/k, got {spec!r}") from exc
    if not (k >= 1 and 0 <= i < k):
        raise SystemExit(f"--shard {spec!r}: need 0 <= i < k")
    return i, k


def shard_of(k: int, shards: int) -> int:
    """The deterministic instance -> shard map, identical in every phase: instance index k (seed - seed_base)
    belongs to shard k mod shards."""
    return int(k) % int(shards)


def _shard_filter(m: dict, jobs: list) -> list:
    """Sharding (ops review B2): a shard runs only its instances (index = i mod k). The exact placebo (when
    declared) is run alone by ``--exact-placebo-only`` (no shard) and is excluded from every shard."""
    ex = m.get("exact_placebo")

    def placebo_unit(job) -> bool:
        k, pol, rep = job[0], job[1], job[2]
        return bool(ex) and pol == ex["policy"] and rep == ex["rep"] and k < int(ex["instances"])

    if m.get("exact_placebo_only"):
        if not ex:
            raise SystemExit("--exact-placebo-only needs --placebo-policy and --exact-placebo-n")
        return [j for j in jobs if placebo_unit(j)]
    sh = parse_shard(m.get("shard"))
    if sh is None:
        return jobs
    i, n = sh
    return [j for j in jobs if shard_of(j[0], n) == i and not placebo_unit(j)]


def check_exact_placebo(run: Run, dup_root: dict) -> None:
    """The exact placebo's duplicate must reproduce its original exactly (Y and decisions); else STOP."""
    orig_id = dup_root["root_id"][: -len("_dup")]
    orig = next((r for r in read_jsonl(run.out / "roots.jsonl") if r["root_id"] == orig_id), None)
    if orig is None:
        raise Stop(f"exact placebo {dup_root['root_id']}: its original {orig_id} is missing")
    same = (orig["y_terminal"] == dup_root["y_terminal"] and orig["decisions"] == dup_root["decisions"]
            and orig["runs_used"] == dup_root["runs_used"])
    if not same:
        raise Stop(f"exact placebo mismatch on {orig['instance_id']} ({dup_root['policy']}): "
                   f"Y {orig['y_terminal']!r} vs {dup_root['y_terminal']!r}")


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


def is_transport_error(exc: BaseException) -> bool:
    """A manager-server transport failure (connection refused / reset, timeout, 5xx), by the harness's own
    classifier (``transport_retry.classify_transport_error``) or the standard library's connection errors, anywhere
    in the exception chain."""
    import socket
    import urllib.error
    from autoresearch.llm.transport_retry import classify_transport_error
    seen = set()
    e: BaseException | None = exc
    while e is not None and id(e) not in seen:
        seen.add(id(e))
        if classify_transport_error(e) is not None or isinstance(
                e, (ConnectionError, TimeoutError, socket.timeout, urllib.error.URLError)):
            return True
        e = e.__cause__ or e.__context__
    return False


def server_url() -> str | None:
    return os.environ.get("LLAMACPP_BASE_URL")


def server_healthy(url: str | None, timeout: float = 10.0) -> bool:
    """GET <server>/health (llama-server), else <url>/models; True on HTTP 200."""
    import urllib.request
    if not url:
        return False
    base = url.rstrip("/")
    root = base[:-3] if base.endswith("/v1") else base
    for probe in (root + "/health", base + "/models"):
        try:
            with urllib.request.urlopen(probe, timeout=timeout) as resp:  # noqa: S310 - operator-given local URL
                if resp.status == 200:
                    return True
        except Exception:  # noqa: BLE001 - unhealthy
            continue
    return False


class _Guard:
    """Between units: the stop file (pause), the server health check and the transport circuit breaker."""

    def __init__(self, run: Run, done: dict) -> None:
        a = run.args
        self.run, self.done = run, done
        self.stop_file = getattr(a, "stop_file", None)
        self.llm = (run.manifest.get("manager") or {}).get("kind") == "langgraph"
        self.limit = int(getattr(a, "max_transport_failures", None) or DEFAULT_MAX_TRANSPORT_FAILURES)
        self.wait = float(getattr(a, "health_wait", 5.0) or 0.0)
        self.consecutive = 0

    def proceed(self) -> bool:
        """False: stop the session now (paused, deadline or STOP: server unhealthy; ``done['status']``)."""
        if not self.run.time_left():
            self.done.update(deadline_hit=True, status="deadline")
            return False
        if self.stop_file and Path(self.stop_file).exists():
            self.done["status"] = "paused"
            return False
        if not self.llm:
            return True
        while not server_healthy(server_url()):
            self.consecutive += 1
            if self.consecutive >= self.limit:
                self.done["status"] = "STOP: server unhealthy"
                return False
            time.sleep(self.wait)
        return True

    def failed(self, exc: BaseException) -> bool:
        """True if the failure was a transport failure (the unit is NOT logged: no retry is consumed)."""
        if not is_transport_error(exc):
            self.consecutive = 0
            return False
        self.consecutive += 1
        self.done["transport_failures"] = self.done.get("transport_failures", 0) + 1
        if self.consecutive >= self.limit:
            self.done["status"] = "STOP: server unhealthy"
        return True

    def ok(self) -> None:
        self.consecutive = 0

    @property
    def stopped(self) -> bool:
        return str(self.done.get("status", "")).startswith("STOP")


def session(run: Run) -> dict:
    """Run every unit still to do. ``done['status']``: "complete", "deadline", "paused" (the stop file exists; the
    current unit was finished; not a failure) or "STOP: server unhealthy" (``--max-transport-failures``
    consecutive transport failures or failed health checks; no unit retry is consumed)."""
    m = run.manifest
    todo = plan(run)
    done = {"roots": 0, "forks": 0, "leaves": 0, "failed": 0, "exhausted": len(todo["exhausted"]),
            "deadline_hit": False, "status": "complete"}
    guard = _Guard(run, done)
    known_forks = {f["fork_id"] for f in read_jsonl(run.out / "forks.jsonl")}
    for k, pol, rep, primary, rid, dup in todo["roots_todo"]:
        if not guard.proceed():
            break
        try:
            root = run_root(run, k, policy=pol, rep=rep, primary=primary, dup=dup)
        except Stop:
            raise
        except Exception as exc:  # noqa: BLE001 - logged, never counted as done; retried on resume
            details = failure_details(exc, "root_campaign")
            _write_failure(run.out, "root", rid, details)
            if guard.failed(exc):
                if guard.stopped:
                    break
                continue
            log_failed_unit(run.out, rid, "root", details)
            done["failed"] += 1
            continue
        guard.ok()
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
            {"_y_terminal_per_seed": root.get("_y_terminal_per_seed"), "_audit_seeds": root.get("_audit_seeds"),
             "_seed": root.get("_seed")}))
        # The root line is the commit marker: written last.
        append_jsonl(run.out / "roots.jsonl", {k_: v for k_, v in root.items() if not k_.startswith("_")})
        done["roots"] += 1
        if dup:
            check_exact_placebo(run, root)
    if m["phase"] in FORK_PHASES and done["status"] == "complete":
        todo = plan(run)
        forks = {f["fork_id"]: f for f in _dedupe(read_jsonl(run.out / "forks.jsonl"), "fork_id")}
        root_rows_cache: dict[str, list[dict]] = {}
        for fork_id, arm, rep in todo["leaves_todo"]:
            if not guard.proceed():
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
                if guard.failed(exc):
                    if guard.stopped:
                        break
                    continue
                log_failed_unit(run.out, unit, "leaf", details)
                done["failed"] += 1
                continue
            guard.ok()
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
    prior = a2u.fit_prior(rows, adapter.surface, float(sigma), k_label=DEV_K, within_key=args.within_key,
                          sources={"s04_rows": str(src), "s04_rows_sha256": sha256_file(src)})
    prior = dataclasses.replace(prior, meta={**prior.meta, "obs_inflation": float(args.obs_inflation)})
    target = Path(args.prior or (out / "a2u_prior.json"))
    sha = prior.save(target)
    print(json.dumps({"prior": str(target), "sha256": sha, "kinds": {k: vars(v) for k, v in prior.kinds.items()}}))
    return 0


def set_obs_inflation_phase(args) -> int:
    """A copy of ``--prior`` whose metadata records ``--obs-inflation`` (the S0.5 calibration revision), written
    to ``--prior-out``; every later phase refuses a different lambda."""
    if not args.prior or not args.prior_out:
        raise SystemExit("set_obs_inflation needs --prior IN --prior-out OUT --obs-inflation LAMBDA")
    if float(args.obs_inflation) < 1.0:
        raise SystemExit("--obs-inflation must be >= 1")
    src = a2u.A2UPrior.load(args.prior, expect_sha256=args.prior_sha256)
    new = dataclasses.replace(src, meta={**src.meta, "obs_inflation": float(args.obs_inflation),
                                         "obs_inflation_from_prior_sha256": src.sha256})
    sha = new.save(args.prior_out)
    print(json.dumps({"prior": str(args.prior_out), "sha256": sha, "obs_inflation": float(args.obs_inflation)}))
    return 0


def liveness_phase(args) -> int:
    """D28 liveness (ops review M7) over the ledgers of a Track S out-dir (normally S0.4, which runs the llama.cpp
    manager under Track S settings: memory append_only_summary, split vary): the ``r1.liveness`` criteria, with the
    manager kind and memory mode taken from the out-dir's manifest, written to ``<out>/liveness/``. Exit 3 (STOP)
    if a node fails."""
    from r1.liveness.check import evaluate_ledger_paths, write_reports
    out = Path(args.out)
    man = json.loads((out / "manifest.json").read_text())
    work = Path(man.get("work") or args.work or DEFAULT_WORK)
    roots = [r for r in read_jsonl(out / "roots.jsonl") if r.get("status", "ok") == "ok"]
    dirs = [work / "roots" / r["root_id"] for r in roots]
    missing = [str(d) for d in dirs if not (d / "root_trials.jsonl").exists()]
    if missing or not dirs:
        raise SystemExit(f"liveness: campaign ledgers missing under {work}: {missing[:3] or 'no roots'}")
    kind = "langgraph" if (man.get("manager") or {}).get("kind") == "langgraph" else "scripted"
    report = evaluate_ledger_paths(dirs, manager_kind=kind, memory_mode=man.get("memory_mode"))
    report["source"] = {"out": str(out), "phase": man.get("phase"), "label": man.get("label"), "host": man.get("host")}
    write_reports(report, out / "liveness")
    verdict = {n: ("PASS" if v["pass"] else "FAIL") for n, v in report["nodes"].items()}
    print(json.dumps({"liveness": verdict, "manager_kind": kind, "memory_mode": man.get("memory_mode")}))
    return 0 if all(v == "PASS" for v in verdict.values()) else 3


def check_evidence(args, cfg: dict) -> None:
    """EVIDENCE needs the llama.cpp manager with GGUF sha256, build, server binary and base URL (ops review M1)."""
    if args.label == "EVIDENCE" and cfg.get("kind") != "langgraph":
        raise SystemExit("label EVIDENCE needs --manager llamacpp (with --gguf/--gguf-sha256, --llama-build, "
                         "--llama-server-bin and LLAMACPP_BASE_URL)")


def blas_threads() -> str:
    """Pin the BLAS thread variables to 1 for worker / audit subprocesses unless set (ops review 9); the values."""
    for v in BLAS_VARS:
        os.environ.setdefault(v, "1")
    return ",".join(f"{v}={os.environ[v]}" for v in BLAS_VARS)


def check_obs_inflation(args, prior) -> None:
    """Phases after S0.5 run at the prior file's recorded lambda (``fit_prior`` / ``set_obs_inflation``)."""
    if prior is None or args.phase not in LATER_PHASES:
        return
    want = float(prior.meta.get("obs_inflation", 1.0))
    if abs(float(args.obs_inflation) - want) > 1e-12:
        raise SystemExit(f"--obs-inflation {args.obs_inflation} differs from the prior file's recorded {want} "
                         "(set it with fit_prior --obs-inflation or --phase set_obs_inflation)")


def check_llm_provenance(args, cfg: dict) -> None:
    """Real llama.cpp runs need the GGUF sha256, the llama.cpp build and a host label (review m3); "unknown"
    counts as missing (final review)."""
    if cfg.get("kind") != "langgraph":
        return
    missing = []
    if not (args.gguf_sha256 or args.gguf) or str(args.gguf_sha256 or "").lower() == "unknown":
        missing.append("--gguf or --gguf-sha256")
    if not (args.llama_build or args.llama_server_bin) or str(args.llama_build or "").lower() == "unknown":
        missing.append("--llama-build or --llama-server-bin")
    if args.host_label in (None, "", "unknown"):
        missing.append("--host-label")
    if args.label == "EVIDENCE":
        if not args.llama_server_bin:
            missing.append("--llama-server-bin (EVIDENCE)")
        if not server_url():
            missing.append("LLAMACPP_BASE_URL in the environment (EVIDENCE)")
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
    ap.add_argument("--instances", type=int, default=None,
                    help="instances (default 1; tune: 20 for --tune-grid static, 40 for --tune-grid dynamic)")
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
    ap.add_argument("--work", default=None, help=f"scratch / ledger dir (default $R1_TMP or /tmp/r1_tracks); recorded "
                    "in the manifest; S0.5b uses the S0.5 one")
    ap.add_argument("--shard", default=None, help="i/k: run only the instances whose index = i mod k (own --out and "
                    "own LLAMACPP_BASE_URL per shard; the exact placebo is excluded, see --exact-placebo-only)")
    ap.add_argument("--exact-placebo-only", action="store_true",
                    help="campaign: run only the exact-placebo units (m* twice at rep 0), alone, before any shard")
    ap.add_argument("--stop-file", default=None, help="if this file exists between units: finish the current unit "
                    "and exit with status 'paused' (not a failure)")
    ap.add_argument("--max-transport-failures", type=int, default=DEFAULT_MAX_TRANSPORT_FAILURES,
                    help="consecutive transport failures / failed health checks before 'STOP: server unhealthy' "
                    "(no unit retry is consumed)")
    ap.add_argument("--health-wait", type=float, default=5.0, help="seconds between failed health checks")
    ap.add_argument("--prior-out", default=None, help="set_obs_inflation: the new prior file")
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
                    "continuations (m*), e.g. static:<g>,<h>")
    ap.add_argument("--obs-inflation", type=float, default=1.0, help="A2-U observation-variance inflation lambda")
    ap.add_argument("--within-key", choices=["estimated", "none"], default="estimated", help="fit_prior only")
    ap.add_argument("--a2-fraction", type=float, default=None, help="descriptive A2 roots (default 0 in every phase)")
    ap.add_argument("--policy", action="append", default=None, help="tune / campaign / S0.5 extra policies: a2u | "
                    "static:g,h | dynamic:g0,b_budget,b_info,h0,h_budget,r1bar,taubar,r2bar | pi_prime:<model_file> "
                    "(repeatable; raw units, positional as the analysis branch)")
    ap.add_argument("--rep", type=int, action="append", default=None,
                    help="D26 repetition(s) of the policy campaigns (repeatable; default 0). Convention: 0 is the "
                    "primary, 1 the descriptive placebo's second repetition")
    ap.add_argument("--rep-instances", type=int, default=None,
                    help="repetitions other than 0 run on the first n instances only (e.g. the S0.5 10-instance "
                    "repetition subset)")
    ap.add_argument("--placebo-policy", default=None, help="campaign: the placebo policy (m*)")
    ap.add_argument("--exact-placebo-n", type=int, default=0,
                    help="campaign: run --placebo-policy twice at rep 0 on the first n instances, FIRST (STOP on a "
                    "mismatch)")
    ap.add_argument("--descriptive-placebo-n", type=int, default=0,
                    help="campaign: run --placebo-policy at rep 1 on the first n instances")
    ap.add_argument("--jobs", default=None, help="tune: JSON list of {policy, instances, rep} jobs")
    ap.add_argument("--tune-grid", choices=["static", "dynamic"], default=None,
                    help="tune phase (rev. 7 D2): static = the 15 statics on 20 instances; dynamic = the 4 centred "
                    "members at --m-star on 40 instances (the first 20 are the static stage's instances)")
    ap.add_argument("--sigma-cmp-vary", type=float, default=None,
                    help="grid unit (raw units): the node's sigma (the analysis' sigma_node)")
    ap.add_argument("--tune-g-extension", action="store_true", help="add the g = 0.8 edge extension (3 statics)")
    ap.add_argument("--tune-g-extension-only", action="store_true",
                    help="tune: run only the 3 g = 0.8 statics (on the same paired instances; new --out)")
    ap.add_argument("--tune-configs", default=None,
                    help="tune: run only these configurations, 'policy;policy;...' (same paired instances; new --out)")
    ap.add_argument("--m-star", default=None, help="m*: a static policy string static:g,h (raw units), or g,h in "
                    "sigma units")
    ap.add_argument("--centres-from", default=None, help="dynamic stage: roots.jsonl of the static stage; the centres "
                    "are m*'s eligible-decision means (r1bar, taubar over E1; r2bar over E2)")
    ap.add_argument("--r1-bar", type=float, default=None, help="explicit E1 centre of r (instead of --centres-from)")
    ap.add_argument("--tau-bar", type=float, default=None, help="explicit E1 centre of tau_pred")
    ap.add_argument("--r2-bar", type=float, default=None, help="explicit E2 centre of r")
    ap.add_argument("--truncate-W", default=None, help="S0.5b: comma-separated W values (e.g. 8,10,12,20)")
    ap.add_argument("--no-calibration", action="store_true", help="S0.5: skip the calibration audits")
    ap.add_argument("--e2-verify", action="store_true", help="refused: E2 verify is off for every Track S policy")
    ap.add_argument("--memory-mode", default="append_only_summary")
    ap.add_argument("--skip-display", default=a2u.SKIP_DISPLAY)
    ap.add_argument("--manager", choices=["scripted", "llamacpp"], default=None,
                    help="required for real nodes; scripted only with --dry-run or --label FIXTURE")
    ap.add_argument("--manager-model", default=None)
    ap.add_argument("--proposal-schema", default=None)
    ap.add_argument("--transport-max-attempts", type=int, default=3)
    ap.add_argument("--gguf", default=None, help="manager GGUF path (sha256 computed)")
    ap.add_argument("--gguf-sha256", default=None)
    ap.add_argument("--llama-build", default=None)
    ap.add_argument("--llama-server-bin", default=None)
    ap.add_argument("--gpu", default=None)
    ap.add_argument("--label", default="ENGINEERING_ONLY", choices=LABELS)
    ap.add_argument("--synthetic-params", default=None, help="JSON object of synthetic node parameters")
    return ap.parse_args(argv)


ASSEMBLE_SCHEMA = "tracks_assemble/v1"
ASSEMBLE_KINDS = {"dev": (("tune",), "dev_roots.jsonl"), "campaign": (("campaign",), "campaign_roots.jsonl"),
                  "fork": (("S3", "synthetic", "S0.5"), "roots.jsonl")}


def assemble(node: str, out: Path, *, dev=(), campaign=(), fork=()) -> dict:
    """Collector out-dirs -> one analysis node directory (final review MINOR 1).

    ``dev``: tune (S0.7) out-dirs (static stage, extension, member stage) -> ``dev_roots.jsonl``;
    ``campaign``: campaign (S3e) out-dirs (pi*, m*, matched static, the exact and descriptive placebos, which
    one run declares with --placebo-policy / --exact-placebo-n / --descriptive-placebo-n, or separate runs at
    rep 0 / rep 1) -> ``campaign_roots.jsonl``; ``fork``: S3 / synthetic out-dirs -> ``roots.jsonl`` and
    ``leaves.jsonl``. Checks every manifest's node and phase, the host (one per node), and that a root id
    occurring in two out-dirs is refused, and that shards of one run (``--shard i/k``) have disjoint instance sets;
    reads ``.jsonl.gz`` too; writes ``assemble.json`` with the sources' sha256, labels and shards."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    report = {"schema": ASSEMBLE_SCHEMA, "node": node, "sources": {}, "outputs": {}, "hosts": set(), "labels": {},
              "shards": {}}
    for kind, dirs in (("dev", dev), ("campaign", campaign), ("fork", fork)):
        if not dirs:
            continue
        if len({str(Path(d).resolve()) for d in dirs}) != len(dirs):
            raise SystemExit(f"assemble: an out-dir is given twice for {kind}")
        phases, target = ASSEMBLE_KINDS[kind]
        roots: dict[str, dict] = {}
        origin: dict[str, str] = {}
        leaves: list[dict] = []
        shard_insts: dict[tuple, dict[str, set]] = {}
        for d in map(Path, dirs):
            man = json.loads(_text(d / "manifest.json") if (d / "manifest.json").exists()
                             else _text(d / "manifest.json.gz"))
            if man["node"] != node:
                raise SystemExit(f"assemble: {d} is node {man['node']!r}, not {node!r}")
            if man["phase"] not in phases:
                raise SystemExit(f"assemble: {d} is phase {man['phase']!r}; {kind} takes {phases}")
            report["hosts"].add(man.get("host"))
            report["labels"].setdefault(kind, set()).add(man.get("label"))
            src = {"phase": man["phase"], "label": man.get("label"), "host": man.get("host"),
                   "shard": man.get("shard"), "exact_placebo_only": man.get("exact_placebo_only", False)}
            for name in ("roots.jsonl", "leaves.jsonl", "roots.jsonl.gz", "leaves.jsonl.gz"):
                if (d / name).exists():
                    src[name] = sha256_file(d / name)
            report["sources"][str(d)] = src
            rows = read_jsonl(d / "roots.jsonl")
            if man.get("shard"):
                # shards of one run (same policies / seeds, different shard): instance sets must be disjoint
                key = (man["phase"], json.dumps(man.get("policies")), man.get("seed_base"),
                       parse_shard(man["shard"])[1])
                shard_insts.setdefault(key, {})[man["shard"]] = {r["instance_id"] for r in rows}
            for r in rows:
                if r["root_id"] in roots:
                    raise SystemExit(f"assemble: root {r['root_id']} occurs in {origin[r['root_id']]} and {d} "
                                     "(duplicate units across out-dirs are refused)")
                roots[r["root_id"]], origin[r["root_id"]] = r, str(d)
            leaves += read_jsonl(d / "leaves.jsonl") if kind == "fork" else []
        for key, by in shard_insts.items():
            names = sorted(by)
            for i, a in enumerate(names):
                for b in names[i + 1:]:
                    if by[a] & by[b]:
                        raise SystemExit(f"assemble: shards {a} and {b} share instances {sorted(by[a] & by[b])[:3]}")
            report["shards"][kind] = names
        path = out / target
        path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in roots.values()))
        report["outputs"][target] = {"n": len(roots), "sha256": sha256_file(path)}
        if kind == "fork":
            lp = out / "leaves.jsonl"
            seen_l: set = set()
            for x in leaves:
                k3 = (x["fork_id"], x["arm"], x["rep"])
                if k3 in seen_l:
                    raise SystemExit(f"assemble: leaf {k3} occurs twice")
                seen_l.add(k3)
            lp.write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in leaves))
            report["outputs"]["leaves.jsonl"] = {"n": len(leaves), "sha256": sha256_file(lp)}
    if len(report["hosts"]) > 1:
        raise SystemExit(f"assemble: node {node} mixes hosts {sorted(map(str, report['hosts']))}")
    report["hosts"] = sorted(map(str, report["hosts"]))
    report["labels"] = {k: sorted(map(str, v)) for k, v in report["labels"].items()}
    (out / "assemble.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def assemble_main(argv) -> int:
    ap = argparse.ArgumentParser(prog="python -m r1.tracks.collect assemble", description=assemble.__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--node", required=True)
    ap.add_argument("--out", required=True, help="the analysis node directory")
    ap.add_argument("--dev", nargs="*", default=[])
    ap.add_argument("--campaign", nargs="*", default=[])
    ap.add_argument("--fork", nargs="*", default=[])
    a = ap.parse_args(argv)
    rep = assemble(a.node, Path(a.out), dev=a.dev, campaign=a.campaign, fork=a.fork)
    print(json.dumps(rep["outputs"]))
    return 0


def main(argv=None) -> int:
    import sys
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "assemble":
        return assemble_main(argv[1:])
    args = parse_args(argv)
    blas = blas_threads()
    if args.phase == "fit_prior":
        return fit_prior_phase(args)
    if args.phase == "set_obs_inflation":
        return set_obs_inflation_phase(args)
    if args.phase == "liveness":
        return liveness_phase(args)
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
        m_star = resolve_m_star(args.m_star, args.sigma_cmp_vary)
        args.centres = None
        if args.tune_grid == "dynamic":
            if m_star is None:
                raise SystemExit("--tune-grid dynamic needs --m-star")
            explicit = (args.r1_bar, args.tau_bar, args.r2_bar)
            if args.centres_from and any(x is not None for x in explicit):
                raise SystemExit("give --centres-from or the explicit centres, not both")
            if args.centres_from:
                args.centres = centres_from_roots(args.centres_from, m_star)
            else:
                args.centres = {"r1bar": float(args.r1_bar or 0.0), "taubar": float(args.tau_bar or 0.0),
                                "r2bar": float(args.r2_bar if args.r2_bar is not None else (args.r1_bar or 0.0))}
        args.policy = list(args.policy or []) + tuning_grid(args.tune_grid, args.sigma_cmp_vary, m_star,
                                                            extend=args.tune_g_extension, centres=args.centres)
        if args.instances is None and not args.jobs:
            args.instances = TUNE_N_STATIC if args.tune_grid == "static" else TUNE_N_MEMBERS
    if args.tune_configs or args.tune_g_extension_only:
        if args.phase != "tune" or args.tune_grid:
            raise SystemExit("--tune-configs / --tune-g-extension-only: --phase tune, without --tune-grid")
        extra = [canonical_policy(p.strip()) for p in (args.tune_configs or "").split(";") if p.strip()]
        if args.tune_g_extension_only:
            if args.sigma_cmp_vary is None:
                raise SystemExit("--tune-g-extension-only needs --sigma-cmp-vary")
            extra += extension_grid(args.sigma_cmp_vary)
        args.policy = list(args.policy or []) + extra
        if args.instances is None and not args.jobs:
            args.instances = TUNE_N_STATIC
    if args.exact_placebo_only and args.shard:
        raise SystemExit("--exact-placebo-only runs alone (no --shard)")
    parse_shard(args.shard)
    if args.work is None:
        args.work = DEFAULT_WORK
    if args.jobs and args.phase != "tune":
        raise SystemExit("--jobs is a tune-phase option")
    if args.phase in POLICY_PHASES and not (args.policy or args.jobs):
        raise SystemExit(f"the {args.phase} phase needs at least one --policy (or --jobs)")
    if args.e2_verify:
        raise SystemExit("E2 verify is declared off for every Track S policy (rev.-5 amendment 3); not available")
    out, work = Path(args.out), Path(args.work)
    synth_params = json.loads(args.synthetic_params) if args.synthetic_params else None
    cfg = manager_cfg(args)
    check_evidence(args, cfg)
    check_llm_provenance(args, cfg)
    adapter = make_adapter(args.node, cfg, synth_params)
    prior, prior_sha, sigma_node = resolve_prior(args, adapter)
    check_obs_inflation(args, prior)
    g_declared = float(args.g if args.g is not None else G_UNITS * sigma_node)
    g0 = float(args.g0 if args.g0 is not None else g_declared)
    manifest = build_manifest(args, adapter, prior_sha, sigma_node, g_declared, g0)
    if adapter.synthetic:
        if adapter.world and args.phase in ("S0.4", "S0.5"):
            raise SystemExit("world synthetic nodes run in the 'synthetic', 'tune' and 'campaign' phases (their "
                             "prior is known; S0.4 / S0.5 replays are for the log-linear test nodes)")
        adapter.bind(W=manifest["W"], llm_cap=manifest["llm_cap"])
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
                            paper_dirty=_git_dirty(REPO), shard=args.shard,
                            server_url=server_url() if cfg.get("kind") == "langgraph" else None,
                            obs_inflation=float(args.obs_inflation), blas_threads=blas)
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
    return 3 if str(done.get("status", "")).startswith("STOP") else 0


if __name__ == "__main__":
    raise SystemExit(main())
