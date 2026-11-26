"""G.1b on the TASL pair (R1-T1-HOST-TASL): T1 GPU-node noise floors as direct host runs on two RTX 4090 hosts.

ENGINEERING_ONLY; AI-assisted (Claude). Replaces the HTCondor job of ``sweep2/g1b/`` (the harness isolation does not
work inside the HTCondor container on NEMO2 H200; Ada is occupied). The D21 protocol, the edit list, the seed blocks,
the unisolated-run gate and the D21 rule are unchanged and come from ``sweep2/g1b/g1b_lib.py``; what changes is where
and how one node runs:

* **Hosts.** TASL-2 and TASL-7, one RTX 4090 each (one GPU model for the whole table). Each node is assigned to one
  host (``nodes[].host``); a host runs its nodes one after another. ``mlgym_houseprice`` is CPU-only (no GPU, its own
  cpuset).
* **The isolated census runner.** A node job runs inside a delegated user scope started by ``t1_tasl_node.sh g1b``
  (``systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0``, as the census smokes), with
  ``AR_TEST_CGROUP_PARENT`` set to that scope; the engine (``autoresearch.trackg.noise_floor``) runs every run through
  ``WorkingCopyRunner`` under the harness isolation and refuses any record that is not ``effective: true`` with empty
  waivers and exceptions. The GPU is named by its full UUID (``--gpu-uuid``), resolved against ``nvidia-smi -L``.
* **The GPU lease.** The job holds an exclusive ``flock`` on the host's lease file (``~/r1_locks/gpu0.lock``) for its
  whole duration; a busy lease is a STOP (not a wait). Before and after every part, ``nvidia-smi`` must show no
  compute process of another owner on the leased GPU (the no-shared-card rule); otherwise STOP.
* **Host checks before any run.** Host name, GPU UUID and model, non-root uid, Yama ``ptrace_scope`` >= 1, the
  delegated scope (``memory.max`` 8 GiB, ``memory.swap.max`` 0, ``cgroup.kill``), the CPU affinity equal to the node's
  declared cpus, the harness checkout at the pinned commit and clean, the node environment's ``uv pip freeze`` equal
  to the census freeze, the node's data manifest equal to the census (after the node's own ``setup_command``). At
  launch, each host's harness-isolation host check report (``hosts[].isolation_host_check``; R1-T1-HOST-TASL's
  precondition) must be on published ``main`` with its declared sha256 and the lines ``host_check_host: <hostname>``,
  ``host_check_harness_commit: <pin>``, ``host_check_items: 1-7 PASS`` and ``host_check_verdict: PASS``.
* **Attempts.** The lease and every host check run before anything is written for the node; a refusal there goes to
  ``<run_id>/_refusals/`` and uses up nothing. A job then creates ``<run_id>/<node>/attempt-N/``. Only an attempt that
  ended in an infrastructure STOP may be followed by another; a complete attempt, or a node or timing STOP (the
  author's), ends the node. ``assemble`` takes one sealed attempt per node and lists the unused infrastructure
  attempts.
* **Timeouts and timing.** The engine's timeout is 3 x the declared basis (``timeout_decision.basis``: the census B1
  baseline time, or the slowest executed census record of the node among its baseline and declared-edit records
  B1, B2, E1-E4, smoke records excluded; R1-G1B-TIMEOUT). The census was measured on the
  RTX 6000 Ada; its times are used for the projection only as an estimate (x ``estimate.ratio_4090_over_ada``). **A run
  that reaches the declared timeout on the 4090 is a STOP** (``stop_class: timing``), not a divergent row: the chunk
  carries ``stop_on_timeout`` (harness ``c025f89a``), so the engine stops right after the first timeout row, and the
  author decides. The job records, per part, the 4090/Ada ratio of the baseline runs.
* **Outputs.** Per attempt, as the HTCondor job (``out/``, ``job_record.json`` of schema ``g1b_tasl_job_record/1``,
  ``out.tar``, ``SHA256SUMS``), then ``seal`` copies them under the host's sealed root without overwrite and writes a
  receipt binding the record and the wrapper log; ``assemble`` joins one sealed attempt per node of both hosts and
  ``summarise`` applies the D21 rule
  (``g1b_lib.summarise``: the pinned ``e1_report`` rule, double-checked).
* **Launch.** ``launch`` needs the author-signed note ``docs/r1/authorizations/g1b_t1_tasl_<YYYYMMDD>.md`` on published
  ``main`` (P1–P6 PASS, binding the paper commit and the spec sha256), both keys (``--enable`` and
  ``G1B_TASL_ENABLE_REAL=1``), and the TASL launch binding (``verify_launch_tasl``) with the PLAN rows of
  ``PLAN_ROWS`` plus the decisions' rows. ``g1b_lib.verify_launch`` (S2-C5) cannot be met by a note on main that names
  the launch commit (the launch commit would have to descend from the main that names it), so the TASL binding launches
  from a published checkout (an ancestor of the freshly fetched ``origin/main``) holding the signed spec, and requires
  the note's ``paper_commit`` to be an ancestor whose tree equals the checkout's outside ``docs/`` and that spec file.
  The note must name the spec's run_id and harness commit. A node on TASL-7 also needs the note's ``P7`` (the
  R1-T1-TASL-ENV cross-host check) to read PASS.
* **Cap.** R1-G1B-CAP: the projection in GPU-h (GPU nodes only; the CPU node is reported in core-hours) must not exceed
  100 GPU-h; the projection at the sensitivity ratio is reported beside it.
* **The autoresearch-only spec** (schema ``g1b_tasl_ar_job/v1``; R1-G1B-NOTE2-DECISIONS NOTE2-AR A).
  ``autoresearch_fixedtokens`` joins G.1b under a third note with its own spec (``g1b_tasl_ar_spec.json``):
  - its own run_id, not the seven-node run's nor derived from it;
  - TASL-2 only (its census host);
  - its own harness pin in a second checkout (``hosts.TASL-2.harness_dir`` apart from the seven-node one), with
    that host's check at that pin;
  - the AR census environment ``ar-cond7a`` (Python 3.12.15, freeze ``sweep2/g1b/env/ar-cond7a.freeze.txt``), with
    the PLAN row that admits it named in ``env_decision.authority`` at launch;
  - its own assembly and summary schemas (``g1b_tasl_ar_assembly/1``, ``g1b_tasl_ar_summary/1``): its noise floor
    joins the seven nodes' table by node, never inside their assembly;
  - one shared R1-G1B-CAP: its projection plus the seven-node spec's plus the cross-check's declared hours.
  It launches under ``docs/r1/authorizations/g1b_ar_t1_tasl_<YYYYMMDD>.md`` (``check_note_ar``; ``check-note-ar
  --draft`` before signature). The seven-node spec is validated and run exactly as before, except that it now refuses
  ``autoresearch_fixedtokens`` (it may join only under its own spec).
* **The node-expansion spec** (schema ``g1b_tasl_x_job/v1``; R1-T1-NODE-EXPANSION). The four expansion candidates
  (``mlgym_titanic``, ``mlgym_metamaze``, ``gc7rc_etth1``, ``gc7rc_forestcover``) on TASL-2, each at its own reviewed
  kit pin in its own checkout, each CPU node on its CPU set under a CPU-set lease, in its census environment
  (torch312, or MetaMaze's venv_jax compared with ``pip freeze``), with its census times binding run_seconds and the
  timeout basis; a node not on the harness's CPU-only list at its pin is admitted by the in-process override its
  census used (``X_ENGINE_OVERRIDE``). A node's CPU set is its census set or, where the census set contains TASL-2
  CPUs 8-11, a replacement set of the same size under R1-TASL2-CPU (``cpu_replacement``): no CPU set of this kind may
  contain 8-11. Its own cap (40 GPU-h), assembly and summary. It launches under
  ``docs/r1/authorizations/g1b_x_t1_tasl_<YYYYMMDD>.md`` (``check_note_x``; ``check-note-x --draft`` before
  publication), published by the coordinating chat under the row, with a per-node gate (``check_gate_x``: the host
  check at the node's own pin, and the environment row, the review or the replacement set's fixed-seed determinism
  check the spec requires). The seven-node and autoresearch kinds are unchanged.
"""
from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import math
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / "g1b"))
import g1b_lib as L  # noqa: E402

SCHEMA = "g1b_tasl_job/v1"
RECORD_SCHEMA = "g1b_tasl_job_record/1"
RECEIPT_SCHEMA = "g1b_tasl_seal_receipt/1"
ASSEMBLY_SCHEMA = "g1b_tasl_assembly/1"
SUMMARY_SCHEMA = "g1b_tasl_summary/1"
ENGINEERING_ONLY = "ENGINEERING_ONLY"
GPU_MODEL = "NVIDIA GeForce RTX 4090"
HOSTS = ("TASL-2", "TASL-7")
CPU_ONLY_NODES = ("mlgym_houseprice",)
T1_NODES = ("mlab_cifar10", "mlab_imdb", "mlab_ogbn_arxiv", "mlgym_cifar10", "mlgym_fmnist",
            "mlgym_breakout_minatar", "mlgym_houseprice")       # the seven passed census rows (U4, 20 Nov)
T1_NODES_LATER = ("autoresearch_fixedtokens",)                   # after its U2 (R1-TRACKG-AR-U2-TASL2)
MEMORY_MAX = 8589934592                                          # the census scope: MemoryMax=8G, MemorySwapMax=0
TIMEOUT_BASES = {"census_baseline_x3": "run_seconds", "census_slowest_x3": "slowest_census_seconds"}
PLAN_ROWS = ("R1-T1-HOST-TASL", "R1-TRACKG-G3-EARLY", "R1-G1B-CAP", "R1-G1B-EDITS", "R1-G1B-TIMEOUT")
ENABLE_ENV = "G1B_TASL_ENABLE_REAL"
NOTE_DIR = "docs/r1/authorizations"
NOTE_NAME = re.compile(r"^g1b_t1_tasl_\d{8}\.md$")
ROW_ID = re.compile(r"^R1-[A-Z0-9][A-Z0-9-]*[A-Z0-9]")

# The autoresearch-only G.1b spec (R1-G1B-NOTE2-DECISIONS, NOTE2-AR A): autoresearch_fixedtokens joins G.1b under a
# third note with its own spec, run_id, harness pin (a second harness checkout on TASL-2), environment, assembly and
# summary. The schema selects the kind; the seven-node spec (schema SCHEMA) is validated and run exactly as before.
AR_SCHEMA = "g1b_tasl_ar_job/v1"
AR_ASSEMBLY_SCHEMA = "g1b_tasl_ar_assembly/1"
AR_SUMMARY_SCHEMA = "g1b_tasl_ar_summary/1"
AR_HOSTS = ("TASL-2",)                       # the AR census host (R1-TRACKG-AR-U2-TASL2); TASL-2 runs its workers
AR_ENV = "ar-cond7a"
AR_PYTHON = "3.12.15"                        # the AR census environment (U2 on TASL-2, freeze 11def6ad…)
AR_NOTE_NAME = re.compile(r"^g1b_ar_t1_tasl_\d{8}\.md$")
AR_RULE = "R1-G1B-NOTE2-DECISIONS"
AR_PLAN_ROWS = PLAN_ROWS + ("R1-T1-TASL-ENV", "R1-TRACKG-AR-U2-TASL2", AR_RULE)
AR_HARNESS_PIN = "2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe"   # the pin R1-G1B-NOTE2-DECISIONS names
AR_RUN_PREFIX = "g1b-ar-"                    # apart from g1b-tasl-* (seven nodes, cross-check) and g4-tasl-*
AR_RULE_TEXT = re.compile(r"^R1-G1B-NOTE2-DECISIONS(?![A-Za-z0-9-])")
SEVEN_SPEC_REL = "sweep2/t1_tasl/g1b_tasl_spec.json"   # the signed seven-node spec: the AR spec must not share its run or checkout
CROSSCHECK_GPU_HOURS_MAX = 10.0

# The T1 node-expansion G.1b spec (R1-T1-NODE-EXPANSION; schema g1b_tasl_x_job/v1). The expansion candidates come
# from four separately reviewed harness kits, each at its own harness commit, and their U2 censuses ran CPU-only on
# TASL-2, each on its own CPU set. So this kind adds, beside the seven-node and autoresearch kinds (both unchanged):
# - a harness pin and checkout per node (nodes[].harness), its TASL-2 host check at that pin cited in the note's gate;
# - CPU nodes with their CPU set (identical or disjoint between nodes) and a CPU-set lease, so two nodes on one
#   CPU set run one after another; GPU nodes as before (host cpus, GPU lease);
# - R1-TASL2-CPU (26 Nov 2026): no CPU set of this kind contains TASL-2 CPUs 8-11; a node whose census ran on a set
#   containing them runs on a replacement set of the same size (nodes[].cpu_replacement: one of the CPU groups the
#   TASL-2 CPU stability record passed), and its gate needs that set's fixed-seed determinism check record on main;
# - per node, how the harness engine admits a CPU chunk: "harness_list" (the kit lists the node in the harness's
#   CPU_ONLY_NODES) or "census_override" (the kit does not; the engine is started with the node added to that list
#   in-process for that one chunk, the mechanism every CPU-only U2 census of these kits used; no harness file changes);
# - the census environment of each node: torch312 (uv pip freeze, as before) or venv_jax (MetaMaze's census venv,
#   compared with pip freeze, as its census recorded it);
# - the census times per record (B1, B2, E1-E4), which bind run_seconds (B1) and the timeout basis (the slowest);
# - per-node launch gates in the note (gate_<node>: PASS/PENDING): the host check at the node's pin and, where the
#   spec requires them, the PLAN row admitting the node's environment and an independent review;
# - its own cap (40 GPU-h, R1-T1-NODE-EXPANSION), note (g1b_x_t1_tasl_<date>.md, published by the coordinating chat
#   under that row), assembly and summary.
X_SCHEMA = "g1b_tasl_x_job/v1"
X_ASSEMBLY_SCHEMA = "g1b_tasl_x_assembly/1"
X_SUMMARY_SCHEMA = "g1b_tasl_x_summary/1"
X_RULE = "R1-T1-NODE-EXPANSION"
X_NODES = ("mlgym_titanic", "mlgym_metamaze", "gc7rc_etth1", "gc7rc_forestcover")
X_HOSTS = ("TASL-2",)                        # the census host of all four (U2 on TASL-2, 25 Nov 2026)
X_RUN_PREFIX = "g1b-x-"
X_NOTE_NAME = re.compile(r"^g1b_x_t1_tasl_\d{8}\.md$")
X_CAP_GPU_HOURS = 40.0                       # R1-T1-NODE-EXPANSION: G.1b expansion cap
X_PLAN_ROWS = PLAN_ROWS + ("R1-T1-TASL-ENV", X_RULE, "R1-T1-D21-SCOPE", "R1-G5-EXPANSION-JOIN", "R1-TASL2-CPU")
X_ENVS = {"torch312": "uv", "venv_jax": "pip"}   # environment -> the freeze tool its census used
X_GATES = ("host_check", "env_row", "review", "cpu_determinism")
X_CENSUS_KEYS = ("B1", "B2", "E1", "E2", "E3", "E4")
X_CPU_ONLY = ("harness_list", "census_override")
X_PUBLICATION_TEXT = "coordinating chat publishes the new G.1b spec and note"
X_REVIEW_RECORD = "docs/r1/reviews/G1B_EXPANSION_REVIEW_20261126.md"   # this unit's independent review record
# The sentence the PLAN row of decision EXP-ENV (option A) must contain, verbatim, for MetaMaze's environment gate.
X_ENV_ROW_TEXT = "venv_jax is admitted as the census environment of mlgym_metamaze for its G.1b on TASL-2"
# R1-TASL2-CPU: no R1 job on TASL-2 uses CPUs 8-11 (physical P-cores 4 and 5, the two 6.1 GHz favoured cores, which
# failed 3 of 3 runs of the MetaMaze determinism stress); a census set containing any of them is replaced by a set of
# the same size that avoids them and passes a fixed-seed determinism check before its first use.
X_CPU_ROW = "R1-TASL2-CPU"
X_EXCLUDED_CPUS = frozenset({8, 9, 10, 11})
X_STABILITY_RECORD = "docs/r1/reports/tasl_chain_20261122/TASL2_CPU_STABILITY_20261125.md"
X_STABLE_SETS = ("0-3", "4-7", "12-15")      # the CPU groups that record passed 3 of 3, bitwise identical
X_DETERMINISM_LINES = ("host", "node", "cpus", "harness_commit", "runs", "result_channel_sha256", "baseline_seconds",
                       "verdict")             # the record's column-0 lines determinism_check_<key>: <value>
X_RULE_TEXT = re.compile(r"^R1-T1-NODE-EXPANSION(?![A-Za-z0-9-])")
# The engine started with the chunk's node added to the harness's CPU-only list, in this process only (the census
# drivers of the three kits did the same); the chunk file must name that node.
X_ENGINE_OVERRIDE = (
    "import json, sys\n"
    "import autoresearch.trackg.noise_floor as nf\n"
    "node = sys.argv.pop(1)\n"
    "chunk = sys.argv[sys.argv.index('--chunk') + 1]\n"
    "if json.load(open(chunk))['node'] != node:\n"
    "    sys.exit('STOP: the chunk names another node than the CPU-only override')\n"
    "nf.CPU_ONLY_NODES = frozenset(nf.CPU_ONLY_NODES) | {node}\n"
    "sys.exit(nf.main(sys.argv[1:]))\n")


def is_ar(spec: dict) -> bool:
    return spec.get("schema") == AR_SCHEMA


def is_x(spec: dict) -> bool:
    return spec.get("schema") == X_SCHEMA


def spec_hosts(spec: dict) -> tuple[str, ...]:
    return AR_HOSTS if is_ar(spec) else X_HOSTS if is_x(spec) else HOSTS


def node_harness_commit(spec: dict, node: dict) -> str:
    """The harness pin a node runs at: its own (expansion kind) or the spec's."""
    return node["harness"]["commit"] if is_x(spec) else spec["harness"]["commit"]


def node_harness_dir(spec: dict, node: dict) -> str:
    return node["harness"]["dir"] if is_x(spec) else spec["hosts"][node["host"]]["harness_dir"]


def cpu_lease_path(spec: dict, node: dict) -> str:
    """The CPU-set lease of an expansion CPU node: nodes on the same CPU set run one after another."""
    return "~/r1_locks/cpus-" + node_cpus(spec, node).replace(",", "_") + ".lock"


def node_lease(spec: dict, node: dict) -> str | None:
    if node["device"] == "gpu":
        return spec["hosts"][node["host"]]["lease"]
    return cpu_lease_path(spec, node) if is_x(spec) else None

Stop = L.Stop
NodeStop = L.NodeStop


class TimingStop(Stop):
    """A run reached the declared timeout on the 4090: the census timing does not carry over; the author decides."""


# =============================================================================================== spec
def load_spec(path: Path) -> dict:
    return json.loads(Path(path).read_text())


def runs_per_node(n_edits: int) -> int:
    return L.runs_per_node(n_edits)


def timeout_basis(spec: dict, node: dict) -> float:
    return float(node[TIMEOUT_BASES[spec["timeout_decision"]["basis"]]])


def node_estimate_seconds(spec: dict, node: dict, ratio: float) -> float:
    est = spec["estimate"]
    return runs_per_node(node["n_edits"]) * float(node["run_seconds"]) * ratio + float(est["setup_estimate_s"])


def node_wall_limit(spec: dict, node: dict) -> int:
    """The job deadline: the estimate at the sensitivity ratio x the wall factor, plus the setup reserve."""
    est = spec["estimate"]
    runs = runs_per_node(node["n_edits"]) * float(node["run_seconds"]) * float(est["ratio_sensitivity"])
    return int(math.ceil(runs * float(est["node_wall_factor"]) + float(est["setup_reserve_s"])))


def x_hours_by_record(spec: dict, node: dict, ratio: float) -> float:
    """The expansion estimate from each census record: 92 runs per configuration, c0 at the mean of B1 and B2, cK at
    EK, plus setup (the run_seconds estimate counts every run at B1, which is low for a node with a heavier edit)."""
    per = L.runs_per_node(node["n_edits"]) // (node["n_edits"] + 1)
    t = node["census_seconds"]
    total = per * ((float(t["B1"]) + float(t["B2"])) / 2 + sum(float(t[f"E{k}"]) for k in range(1, node["n_edits"] + 1)))
    return (total * ratio + float(spec["estimate"]["setup_estimate_s"])) / 3600.0


def projection(spec: dict) -> dict:
    est = spec["estimate"]
    out = {}
    for label, ratio in (("estimate", float(est["ratio_4090_over_ada"])), ("sensitivity", float(est["ratio_sensitivity"]))):
        per_node, per_host = {}, {h: 0.0 for h in spec_hosts(spec)}
        for node in spec["nodes"]:
            hours = node_estimate_seconds(spec, node, ratio) / 3600.0
            per_node[node["node"]] = {"runs": runs_per_node(node["n_edits"]), "device": node["device"],
                                      "host": node["host"], "hours": round(hours, 3)}
            if node["device"] == "gpu":
                per_host[node["host"]] += hours       # the CPU-only node runs beside them on its own cpuset
        gpu = sum(v["hours"] for v in per_node.values() if v["device"] == "gpu")
        cpu = sum(v["hours"] for v in per_node.values() if v["device"] == "cpu")
        out[label] = {"ratio_4090_over_ada": ratio, "per_node": per_node,
                      "per_host_gpu_wall_hours": {h: round(v, 3) for h, v in per_host.items()},
                      "total_gpu_hours": round(gpu, 3), "cpu_node_hours": round(cpu, 3),
                      "cpu_core_hours": round(cpu * len(_cpus(spec, "cpu")), 3) if cpu else 0.0}
        if is_x(spec):      # several CPU nodes on their own sets: core-hours per node; the by-record estimate
            for node in spec["nodes"]:
                entry = per_node[node["node"]]
                if node["device"] == "cpu":
                    entry["cpus"] = node_cpus(spec, node)
                entry["hours_by_record"] = round(x_hours_by_record(spec, node, ratio), 3)
            out[label]["cpu_core_hours"] = round(sum(
                per_node[n["node"]]["hours"] * len(cpu_list(node_cpus(spec, n)))
                for n in spec["nodes"] if n["device"] == "cpu"), 3)
            out[label]["cpu_node_hours_by_record"] = round(sum(
                per_node[n["node"]]["hours_by_record"] for n in spec["nodes"] if n["device"] == "cpu"), 3)
    out["cap_total_gpu_hours"] = spec["caps"]["max_total_gpu_hours"]
    out["within_cap"] = out["estimate"]["total_gpu_hours"] <= out["cap_total_gpu_hours"]
    out["sensitivity_within_cap"] = out["sensitivity"]["total_gpu_hours"] <= out["cap_total_gpu_hours"]
    return out


def node_cpus(spec: dict, node: dict) -> str:
    """The node's CPU affinity: its own ``cpus`` (the CPU-only node, so it can run beside a GPU node) or its host's."""
    return node.get("cpus") or spec["hosts"][node["host"]]["cpus"]


def _cpus(spec: dict, device: str) -> list[int]:
    for node in spec["nodes"]:
        if node["device"] == device:
            return cpu_list(node_cpus(spec, node))
    return []


def cpu_list(text: str) -> list[int]:
    out = []
    for part in str(text).split(","):
        if "-" in part:
            lo, hi = part.split("-")
            out += list(range(int(lo), int(hi) + 1))
        elif part.strip():
            out.append(int(part))
    if not out or len(set(out)) != len(out) or min(out) < 0:
        raise Stop(f"STOP: bad cpu list {text!r}")
    return out


def _abs(value, name: str) -> str:
    if not isinstance(value, str) or not value.startswith("/") or ".." in Path(value).parts:
        raise Stop(f"STOP: {name} must be an absolute path without '..'")
    return value


def validate_spec(spec: dict, *, launch: bool = False) -> dict:
    """Fail-closed validation; ``launch=True`` refuses every placeholder and needs the decisions' authorities."""
    allow = not launch
    if spec.get("schema") not in (SCHEMA, AR_SCHEMA, X_SCHEMA) or spec.get("label") != ENGINEERING_ONLY:
        raise Stop(f"STOP: spec must be {SCHEMA} (or the autoresearch-only {AR_SCHEMA}, or the node-expansion "
                   f"{X_SCHEMA}), ENGINEERING_ONLY")
    ar = is_ar(spec)
    x = is_x(spec)
    hosts_rule = spec_hosts(spec)
    run_id = spec.get("run_id")
    if not isinstance(run_id, str) or not L.SAFE.fullmatch(run_id) or run_id in (".", ".."):
        raise Stop("STOP: run_id must be a safe path component")
    for key, repo in (("paper", L.PAPER_REPO), ("harness", L.HARNESS_REPO)):
        block = spec.get(key) or {}
        if block.get("repo") != repo:
            raise Stop(f"STOP: {key}.repo must be {repo}")
        if x and key == "harness":       # the expansion kind pins the harness per node (nodes[].harness)
            if "commit" in block:
                raise Stop("STOP: the node-expansion spec pins the harness per node (nodes[].harness), not harness.commit")
            continue
        L._commit(block.get("commit"), f"{key}.commit", allow_placeholder=allow)
    if spec.get("gpu_model") != GPU_MODEL:
        raise Stop(f"STOP: gpu_model must be {GPU_MODEL} (R1-T1-HOST-TASL: one GPU model for the table)")
    m = spec.get("measurement") or {}
    want = {"seeds_per_condition": L.SEEDS_PER_CONDITION, "seed_bases": L.SEED_BASES, "split_policy": L.SPLIT_POLICY,
            "workers": 1, "timeout_factor": L.TIMEOUT_FACTOR, "isolation_gate": "effective:true, waivers {}, exceptions []",
            "timeout_on_4090": "STOP"}
    for key, value in want.items():
        if m.get(key) != value:
            raise Stop(f"STOP: measurement.{key} must be {value!r} (fixed)")
    caps = spec.get("caps") or {}
    if not isinstance(caps.get("max_total_gpu_hours"), (int, float)) or \
            not 0 < caps["max_total_gpu_hours"] <= L.CAP_TOTAL_GPU_HOURS:
        raise Stop(f"STOP: caps.max_total_gpu_hours must be in (0, {L.CAP_TOTAL_GPU_HOURS}] (R1-G1B-CAP)")
    if x and (caps["max_total_gpu_hours"] > X_CAP_GPU_HOURS or not X_RULE_TEXT.match(str(caps.get("authority", "")))):
        raise Stop(f"STOP: caps.max_total_gpu_hours must be at most {X_CAP_GPU_HOURS:g} with caps.authority {X_RULE} "
                   "(the G.1b expansion cap)")
    est = spec.get("estimate") or {}
    for key, lo, hi in (("ratio_4090_over_ada", 0.5, 3.0), ("ratio_sensitivity", 0.5, 4.0), ("setup_estimate_s", 0, 7200),
                        ("setup_reserve_s", 600, 14400), ("node_wall_factor", 1.5, 4.0)):
        v = est.get(key)
        if not isinstance(v, (int, float)) or isinstance(v, bool) or not lo <= v <= hi:
            raise Stop(f"STOP: estimate.{key} must be in [{lo}, {hi}]")
    if est["ratio_sensitivity"] < est["ratio_4090_over_ada"]:
        raise Stop("STOP: estimate.ratio_sensitivity must be at least the estimate ratio")
    envs = spec.get("envs") or {}
    if ar:
        if set(envs) != {AR_ENV}:
            raise Stop(f"STOP: envs must be exactly {AR_ENV} (the AR census environment, R1-TRACKG-AR-U2-TASL2)")
    elif x:
        if not envs or set(envs) - set(X_ENVS):
            raise Stop(f"STOP: envs must be among {sorted(X_ENVS)} (the expansion census environments)")
        for name, env in envs.items():
            if env.get("freeze_tool") != X_ENVS[name]:
                raise Stop(f"STOP: envs.{name}.freeze_tool must be {X_ENVS[name]} (the tool its census froze with)")
    elif not envs or set(envs) - {"torch312", "jax312"}:
        raise Stop("STOP: envs must be torch312 and/or jax312 (the census environments)")
    for name, env in envs.items():
        want_python = AR_PYTHON if ar else "3.12.16"
        if env.get("python") != want_python:
            raise Stop(f"STOP: envs.{name}.python must be {want_python} (the census Python)")
        L._sha(env.get("sha256"), f"envs.{name}.sha256", allow_placeholder=False)
        freeze = HERE.parent / "g1b" / env.get("freeze", "")
        if not freeze.is_file() or L._sha_file(freeze) != env["sha256"]:
            raise Stop(f"STOP: envs.{name}.freeze must be the committed census freeze with that sha256")
    hosts = spec.get("hosts") or {}
    if set(hosts) != set(hosts_rule):
        raise Stop(f"STOP: hosts must be exactly {hosts_rule} (R1-T1-HOST-TASL"
                   f"{'; the AR census host, R1-TRACKG-AR-U2-TASL2' if ar else ''})")
    for h, host in hosts.items():
        for key in ("hostname", "gpu_uuid"):
            if not isinstance(host.get(key), str) or not host[key] or (launch and L._placeholder(host[key])):
                raise Stop(f"STOP: hosts.{h}.{key} must be set (the operator fills it from the host)")
        if not L._placeholder(host["gpu_uuid"]) and not re.fullmatch(r"GPU-[0-9a-f-]{36}", host["gpu_uuid"]):
            raise Stop(f"STOP: hosts.{h}.gpu_uuid must be a full GPU UUID")
        for key in ("base", "data_root", "runs_root", "sealed_root", "uv") + (() if x else ("harness_dir",)):
            _abs(host.get(key), f"hosts.{h}.{key}")
        if x and "harness_dir" in host:
            raise Stop(f"STOP: hosts.{h}.harness_dir: the node-expansion spec has one checkout per node "
                       "(nodes[].harness.dir)")
        if host["data_root"] != host["base"].rstrip("/") + "/data":
            raise Stop(f"STOP: hosts.{h}.data_root must be <base>/data (g1b_lib.run_setup writes the node data there)")
        if host.get("lease") != "~/r1_locks/gpu0.lock":
            raise Stop(f"STOP: hosts.{h}.lease must be ~/r1_locks/gpu0.lock (the GPU lease of the hosts)")
        cpu_list(host.get("cpus", ""))
        bins = host.get("env_python") or {}
        for name, path in bins.items():
            if name not in envs:
                raise Stop(f"STOP: hosts.{h}.env_python names an undeclared environment {name}")
            _abs(path, f"hosts.{h}.env_python.{name}")
        if x:      # the host check is at each node's own pin: cited by the node's gate in the note
            if "isolation_host_check" in host:
                raise Stop(f"STOP: hosts.{h}.isolation_host_check: in the node-expansion spec the host check at each "
                           "node's pin is cited by that node's gate in the note")
            continue
        check = host.get("isolation_host_check") or {}
        if not isinstance(check.get("record"), str) or not check["record"]:
            raise Stop(f"STOP: hosts.{h}.isolation_host_check.record must name the host check report")
        L._sha(check.get("sha256"), f"hosts.{h}.isolation_host_check.sha256", allow_placeholder=allow)
    decision = spec.get("edit_count") or {}
    n_edits = decision.get("n_edits_per_node")
    if type(n_edits) is not int or not 3 <= n_edits <= 5 or decision.get("runs_per_node") != runs_per_node(n_edits):
        raise Stop("STOP: edit_count.n_edits_per_node (3-5) and runs_per_node = (n+1) x 92 must agree")
    tdec = spec.get("timeout_decision") or {}
    if tdec.get("basis") not in TIMEOUT_BASES:
        raise Stop(f"STOP: timeout_decision.basis must be one of {sorted(TIMEOUT_BASES)} (R1-G1B-TIMEOUT)")
    hdec = spec.get("host_decision") or {}
    for key, row, dec in (("edit_count", "R1-G1B-EDITS", decision), ("timeout_decision", "R1-G1B-TIMEOUT", tdec),
                          ("host_decision", "R1-T1-TASL-ENV", hdec)):
        if launch and not (isinstance(dec.get("authority"), str) and dec["authority"].startswith(row)):
            raise Stop(f"STOP: {key}.authority must name the PLAN row {row} before launch")
    nodes = spec.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise Stop("STOP: nodes must be a non-empty list")
    names = [n.get("node") for n in nodes]
    if len(set(names)) != len(names):
        raise Stop("STOP: a node is listed twice")
    if ar:
        if set(names) != set(T1_NODES_LATER):
            raise Stop(f"STOP: the autoresearch-only spec measures exactly {list(T1_NODES_LATER)} ({AR_RULE}, NOTE2-AR A)")
    elif x:
        if set(names) - set(X_NODES):
            raise Stop(f"STOP: {sorted(set(names) - set(X_NODES))} are not {X_RULE} candidates ({list(X_NODES)})")
    else:
        unknown = set(names) - set(T1_NODES)
        if unknown & set(T1_NODES_LATER):
            raise Stop(f"STOP: {sorted(unknown & set(T1_NODES_LATER))} joins G.1b only under its own spec "
                       f"({AR_SCHEMA}; {AR_RULE}, NOTE2-AR A)")
        if unknown:
            raise Stop(f"STOP: {sorted(unknown)} are not T1 nodes")
        missing = set(T1_NODES) - set(names)
        if missing:
            raise Stop(f"STOP: the seven passed census nodes must all be measured (D21 uniform); missing {sorted(missing)}")
    for node in nodes:
        name = node["node"]
        for key in ("spec_path", "node_dir"):
            value = node.get(key)
            if not isinstance(value, str) or value.startswith("/") or ".." in Path(value).parts:
                raise Stop(f"STOP: {name}.{key} must be a relative path inside the harness checkout")
        for key in ("node_spec_sha256", "committed_pin_sha256", "edits_manifest_sha256"):
            L._sha(node.get(key), f"{name}.{key}", allow_placeholder=False)
        if "data_manifest_sha256" not in node:
            raise Stop(f"STOP: {name}.data_manifest_sha256 must be the census value (null for a node without data)")
        if node["data_manifest_sha256"] is not None:
            L._sha(node["data_manifest_sha256"], f"{name}.data_manifest_sha256", allow_placeholder=False)
        if node.get("n_edits") != n_edits:
            raise Stop(f"STOP: {name} has {node.get('n_edits')} declared edits; every node uses {n_edits} (uniform)")
        for key in ("run_seconds", "slowest_census_seconds"):
            v = node.get(key)
            if not isinstance(v, (int, float)) or isinstance(v, bool) or not 0 < v <= L.RUN_SECONDS_CEILING:
                raise Stop(f"STOP: {name}.{key} (census, RTX 6000 Ada) must be in (0, {L.RUN_SECONDS_CEILING}]")
        if node["slowest_census_seconds"] < node["run_seconds"]:
            raise Stop(f"STOP: {name}.slowest_census_seconds is below the baseline time")
        if node.get("host") not in hosts_rule:
            raise Stop(f"STOP: {name}.host must be one of {hosts_rule}")
        if x:
            if node.get("device") not in ("cpu", "gpu"):
                raise Stop(f"STOP: {name}.device must be cpu or gpu (as its census ran)")
        else:
            want_device = "cpu" if name in CPU_ONLY_NODES else "gpu"
            if node.get("device") != want_device:
                raise Stop(f"STOP: {name}.device must be {want_device}")
        if node.get("env") not in envs or node["env"] not in (hosts[node["host"]].get("env_python") or {}):
            raise Stop(f"STOP: {name}.env must be a declared environment present on {node['host']}")
        if not isinstance(node.get("census_record"), str) or not node["census_record"]:
            raise Stop(f"STOP: {name}.census_record must name the census U2 record")
        if x:
            validate_x_node(spec, node)
        elif "cpus" in node:
            own = set(cpu_list(node["cpus"]))
            if node["device"] != "cpu":
                raise Stop(f"STOP: {name}.cpus: only the CPU-only node has its own cpuset")
            if own & set(cpu_list(hosts[node["host"]]["cpus"])):
                raise Stop(f"STOP: {name}.cpus overlaps the cpus of {node['host']}'s GPU jobs")
    census = spec.get("census") or {}
    L._commit(census.get("commit"), "census.commit", allow_placeholder=False)
    if x:
        validate_x(spec, launch=launch)
    else:
        L._sha(census.get("report_sha256"), "census.report_sha256", allow_placeholder=False)
    proj = projection(spec)
    if not proj["within_cap"]:
        raise Stop(f"STOP: projected {proj['estimate']['total_gpu_hours']} GPU-h exceeds the R1-G1B-CAP "
                   f"{proj['cap_total_gpu_hours']} GPU-h: author STOP")
    if ar:
        proj["g1b_shared_cap"] = validate_ar(spec, proj, launch=launch)
    return {"spec": spec, "run_id": run_id, "projection": proj, "n_edits": n_edits}


def _seven_spec_file() -> Path:
    return REPO_ROOT / SEVEN_SPEC_REL


def validate_ar(spec: dict, proj: dict, *, launch: bool) -> dict:
    """The autoresearch-only spec's own rules (R1-G1B-NOTE2-DECISIONS, NOTE2-AR A), on top of the shared ones:

    - its own run_id, in its own namespace ``g1b-ar-…``: not the signed seven-node spec's, nor derived from it (the
      cross-check's ``<run_id>-…``), nor G.4's ``g4-tasl-…`` (all share TASL-2's ``runs_root``);
    - its own harness pin, the one the row names (``2d09f9a9``), in a second checkout on TASL-2: neither equal to,
      inside, nor above the seven-node checkout; no host path of the spec inside either checkout, and neither
      checkout inside its data, runs or sealed root;
    - the timeout basis of R1-G1B-TIMEOUT (``census_slowest_x3``);
    - the census on the same GPU model as the table (U2 ran on TASL-2's RTX 4090), so the estimate ratio is 1.0;
    - the decisions it runs under: ``note_rule`` cites R1-G1B-NOTE2-DECISIONS; at launch ``env_decision.authority``
      names the PLAN row that admits the AR census environment (R1-T1-TASL-ENV names torch312/jax312 only);
    - R1-G1B-CAP is one cap for G.1b: this projection + the signed seven-node spec's (recomputed from the bound file)
      + the declared cross-check hours must stay within it (and within the spec's own cap, if lower)."""
    seven_ref = spec.get("seven_node_spec") or {}
    if seven_ref.get("path") != SEVEN_SPEC_REL:
        raise Stop(f"STOP: seven_node_spec.path must be {SEVEN_SPEC_REL}")
    seven_file = _seven_spec_file()
    if not seven_file.is_file() or L._sha_file(seven_file) != seven_ref.get("sha256"):
        raise Stop("STOP: the seven-node spec differs from the one the AR spec binds (the signed spec)")
    seven = load_spec(seven_file)
    if seven_ref.get("run_id") != seven["run_id"]:
        raise Stop(f"STOP: seven_node_spec.run_id must be the signed spec's {seven['run_id']}")
    if spec["run_id"] == seven["run_id"] or spec["run_id"].startswith(seven["run_id"] + "-") or \
            not spec["run_id"].startswith(AR_RUN_PREFIX):
        raise Stop(f"STOP: run_id must be the AR spec's own ({AR_RUN_PREFIX}…), not the seven-node run "
                   f"{seven['run_id']} or derived from it")
    if spec["harness"]["commit"] == seven["harness"]["commit"] or \
            (spec["harness"]["commit"] != AR_HARNESS_PIN and not (not launch and L._placeholder(spec["harness"]["commit"]))):
        raise Stop(f"STOP: harness.commit must be the AR pin {AR_HARNESS_PIN} that R1-G1B-NOTE2-DECISIONS names")
    if spec["timeout_decision"]["basis"] != "census_slowest_x3":
        raise Stop("STOP: timeout_decision.basis must be census_slowest_x3 (R1-G1B-TIMEOUT)")
    if spec["paper"]["repo"] != seven["paper"]["repo"] or spec["harness"]["repo"] != seven["harness"]["repo"]:
        raise Stop("STOP: the AR spec must use the same paper and harness repositories as the seven-node spec")
    for h in AR_HOSTS:
        mine = Path(spec["hosts"][h]["harness_dir"])
        theirs = Path(seven["hosts"][h]["harness_dir"])
        if mine == theirs or theirs in mine.parents or mine in theirs.parents:
            raise Stop(f"STOP: hosts.{h}.harness_dir must be a second checkout, apart from the seven-node one {theirs}")
        host = spec["hosts"][h]
        paths = {k: Path(host[k]) for k in ("base", "data_root", "runs_root", "sealed_root", "uv")}
        paths.update({f"env_python.{k}": Path(v) for k, v in (host.get("env_python") or {}).items()})
        for key, p in paths.items():
            for checkout in (mine, theirs):
                if p == checkout or checkout in p.parents:
                    raise Stop(f"STOP: hosts.{h}.{key} lies inside the harness checkout {checkout}")
        for key in ("data_root", "runs_root", "sealed_root"):
            for checkout in (mine, theirs):
                if paths[key] in checkout.parents:
                    raise Stop(f"STOP: the harness checkout {checkout} lies inside hosts.{h}.{key}")
        if spec["hosts"][h]["hostname"] != seven["hosts"][h]["hostname"] and not L._placeholder(spec["hosts"][h]["hostname"]):
            raise Stop(f"STOP: hosts.{h}.hostname differs from the seven-node spec's")
        if spec["hosts"][h]["gpu_uuid"] != seven["hosts"][h]["gpu_uuid"] and not L._placeholder(spec["hosts"][h]["gpu_uuid"]):
            raise Stop(f"STOP: hosts.{h}.gpu_uuid differs from the seven-node spec's (one card per host)")
    est = spec["estimate"]
    if est.get("census_gpu_model") != GPU_MODEL or est["ratio_4090_over_ada"] != 1.0:
        raise Stop(f"STOP: estimate.census_gpu_model must be {GPU_MODEL} with ratio 1.0 (the AR census ran on TASL-2)")
    if not AR_RULE_TEXT.match(str(spec.get("note_rule", ""))):
        raise Stop(f"STOP: note_rule must cite {AR_RULE} (NOTE2-AR A)")
    env_row = str((spec.get("env_decision") or {}).get("authority", ""))
    if launch:
        m = ROW_ID.match(env_row)
        if not m:
            raise Stop("STOP: env_decision.authority must name the PLAN row admitting the AR census environment before "
                       "launch")
        if m.group(0) in AR_PLAN_ROWS:
            raise Stop(f"STOP: env_decision.authority {m.group(0)} is a row the launch already requires; it must be the "
                       "row that admits ar-cond7a (decision AR-ENV)")
    cap = spec["caps"]
    xc = cap.get("crosscheck_gpu_hours")
    if not isinstance(xc, (int, float)) or isinstance(xc, bool) or not 0 < xc <= CROSSCHECK_GPU_HOURS_MAX:
        raise Stop(f"STOP: caps.crosscheck_gpu_hours must be in (0, {CROSSCHECK_GPU_HOURS_MAX}] (R1-G1B-NOTE2-DECISIONS)")
    seven_proj = projection(seven)
    shared = {}
    for label in ("estimate", "sensitivity"):
        shared[label] = round(proj[label]["total_gpu_hours"] + seven_proj[label]["total_gpu_hours"] + float(xc), 3)
    limit = min(float(cap["max_total_gpu_hours"]), L.CAP_TOTAL_GPU_HOURS)
    if shared["estimate"] > limit:
        raise Stop(f"STOP: G.1b together ({shared['estimate']} GPU-h: this spec, the seven-node spec and the cross-check) "
                   f"exceeds the cap {limit} GPU-h (R1-G1B-CAP; the spec's caps.max_total_gpu_hours): author STOP")
    return {"cap_total_gpu_hours": limit, "this_spec": proj["estimate"]["total_gpu_hours"],
            "seven_node_spec": seven_proj["estimate"]["total_gpu_hours"], "crosscheck": float(xc),
            "total_estimate": shared["estimate"], "total_sensitivity": shared["sensitivity"],
            "sensitivity_within_cap": shared["sensitivity"] <= limit,
            "env_decision": env_row or None}


def validate_x_node(spec: dict, node: dict) -> None:
    """One node of the node-expansion spec (R1-T1-NODE-EXPANSION): its own harness pin and checkout, its census
    times (which bind run_seconds and the timeout basis), its CPU set (its census set, or its R1-TASL2-CPU replacement:
    never one containing CPUs 8-11), how the engine admits its CPU chunk, its census record on main, and the gates its
    launch needs."""
    name = node["node"]
    hz = node.get("harness") or {}
    L._commit(hz.get("commit"), f"{name}.harness.commit", allow_placeholder=False)
    if not isinstance(hz.get("branch"), str) or not hz["branch"]:
        raise Stop(f"STOP: {name}.harness.branch must name the reviewed kit branch")
    _abs(hz.get("dir"), f"{name}.harness.dir")
    times = node.get("census_seconds") or {}
    if sorted(times) != sorted(X_CENSUS_KEYS):
        raise Stop(f"STOP: {name}.census_seconds must hold exactly the census records {list(X_CENSUS_KEYS)}")
    for key, v in times.items():
        if not isinstance(v, (int, float)) or isinstance(v, bool) or not 0 < v <= L.RUN_SECONDS_CEILING:
            raise Stop(f"STOP: {name}.census_seconds.{key} must be in (0, {L.RUN_SECONDS_CEILING}]")
    if node["run_seconds"] != times["B1"] or node["slowest_census_seconds"] != max(times.values()):
        raise Stop(f"STOP: {name}: run_seconds must be the census B1 and slowest_census_seconds the slowest census "
                   "record (R1-G1B-TIMEOUT)")
    L._sha(node.get("census_record_sha256"), f"{name}.census_record_sha256", allow_placeholder=False)
    if not node["census_record"].startswith("docs/r1/reports/") or ".." in Path(node["census_record"]).parts:
        raise Stop(f"STOP: {name}.census_record must be a report under docs/r1/reports/")
    if node["device"] == "cpu":
        cpu_list(node.get("cpus", ""))
        if node.get("cpu_only") not in X_CPU_ONLY:
            raise Stop(f"STOP: {name}.cpu_only must be one of {X_CPU_ONLY} (how the engine admits its CPU chunk)")
    elif "cpus" in node or "cpu_only" in node:
        raise Stop(f"STOP: {name}: a GPU node runs on the host's cpus (no cpus, no cpu_only)")
    gates = node.get("gate_requires")
    if not isinstance(gates, list) or "host_check" not in gates or set(gates) - set(X_GATES) or \
            len(set(gates)) != len(gates):
        raise Stop(f"STOP: {name}.gate_requires must list host_check and only {X_GATES}")
    if "max_attempts" in node:
        raise Stop(f"STOP: {name}.max_attempts: this kind has no attempt cap (the CPUs 8-11 rule was dropped under "
                   f"{X_CPU_ROW}: no node runs there)")
    validate_x_cpu_set(node)
    if "review" in gates and not node.get("cpu_census_conditions"):
        raise Stop(f"STOP: {name}: a node gated on the CPU-census review carries its conditions (cpu_census_conditions)")
    if node["env"] != "torch312" and "env_row" not in gates:
        raise Stop(f"STOP: {name} runs in {node['env']}, which R1-T1-TASL-ENV does not name: its gate needs env_row")


X_REPLACEMENT_KEYS = ("authority", "census_cpus", "stability_record", "determinism_check")
X_DETERMINISM_KEYS = ("record", "runs", "census_baseline_result_channel_sha256")


def validate_x_cpu_set(node: dict) -> None:
    """R1-TASL2-CPU for one node: its CPU set never contains TASL-2 CPUs 8-11. A node whose census set contains them
    carries ``cpu_replacement``: the census set (which contains 8-11), the row, the stability record on this checkout by
    sha256, and the fixed-seed determinism check its new set passes before its first use (the record the gate reads,
    two runs, and the census baseline's result-channel sha256 that both runs must reproduce). The new set has the census
    set's size and is one of the CPU groups the stability record passed; the node's gate requires ``cpu_determinism``.
    A node on its census set has no ``cpu_replacement`` and no ``cpu_determinism`` gate."""
    name = node["node"]
    rep = node.get("cpu_replacement")
    gates = node.get("gate_requires") or []
    if node["device"] != "cpu":
        if rep is not None or "cpu_determinism" in gates:
            raise Stop(f"STOP: {name}: cpu_replacement and the cpu_determinism gate belong to a CPU node")
        return
    cpus = cpu_list(node["cpus"])
    bad = sorted(set(cpus) & X_EXCLUDED_CPUS)
    if bad:
        raise Stop(f"STOP: {name}.cpus {node['cpus']} contains TASL-2 CPUs {bad}: no R1 job on TASL-2 uses CPUs 8-11 "
                   f"({X_CPU_ROW}); the node needs a replacement set of the same size (cpu_replacement)")
    if rep is None:
        if "cpu_determinism" in gates:
            raise Stop(f"STOP: {name}: the cpu_determinism gate belongs to a replacement CPU set (cpu_replacement)")
        return
    if not isinstance(rep, dict) or sorted(set(rep) - {"comment"}) != sorted(X_REPLACEMENT_KEYS):
        raise Stop(f"STOP: {name}.cpu_replacement must hold exactly {list(X_REPLACEMENT_KEYS)} (and a comment)")
    if rep["authority"] != X_CPU_ROW:
        raise Stop(f"STOP: {name}.cpu_replacement.authority must be {X_CPU_ROW}")
    census = cpu_list(rep["census_cpus"])
    if not set(census) & X_EXCLUDED_CPUS:
        raise Stop(f"STOP: {name}.cpu_replacement: only a census set containing CPUs 8-11 is replaced ({X_CPU_ROW}); "
                   f"{rep['census_cpus']} is not one")
    if len(census) != len(cpus):
        raise Stop(f"STOP: {name}.cpu_replacement: the replacement set {node['cpus']} must have the census set's size "
                   f"({len(census)} CPUs, {rep['census_cpus']}; {X_CPU_ROW})")
    if node["cpus"] not in X_STABLE_SETS:
        raise Stop(f"STOP: {name}.cpus {node['cpus']}: a replacement set must be one of the CPU groups the TASL-2 CPU "
                   f"stability record passed ({', '.join(X_STABLE_SETS)})")
    rec = rep["stability_record"] if isinstance(rep["stability_record"], dict) else {}
    if rec.get("path") != X_STABILITY_RECORD:
        raise Stop(f"STOP: {name}.cpu_replacement.stability_record.path must be {X_STABILITY_RECORD}")
    L._sha(rec.get("sha256"), f"{name}.cpu_replacement.stability_record.sha256", allow_placeholder=False)
    f = REPO_ROOT / X_STABILITY_RECORD
    if not f.is_file() or L._sha_file(f) != rec["sha256"]:
        raise Stop(f"STOP: {name}.cpu_replacement.stability_record.sha256 is not the sha256 of {X_STABILITY_RECORD} "
                   "in this checkout")
    chk = rep["determinism_check"] if isinstance(rep["determinism_check"], dict) else {}
    if sorted(set(chk) - {"comment"}) != sorted(X_DETERMINISM_KEYS):
        raise Stop(f"STOP: {name}.cpu_replacement.determinism_check must hold exactly {list(X_DETERMINISM_KEYS)}")
    path = chk["record"]
    if not isinstance(path, str) or not path.startswith("docs/r1/reports/") or ".." in Path(path).parts or \
            not path.endswith(f"_{node['cpus']}.md"):
        raise Stop(f"STOP: {name}.cpu_replacement.determinism_check.record must be a report under docs/r1/reports/ "
                   f"whose name ends in _{node['cpus']}.md")
    if chk["runs"] != 2:
        raise Stop(f"STOP: {name}.cpu_replacement.determinism_check.runs must be 2 (the census baseline twice)")
    L._sha(chk["census_baseline_result_channel_sha256"],
           f"{name}.cpu_replacement.determinism_check.census_baseline_result_channel_sha256", allow_placeholder=False)
    if "cpu_determinism" not in gates:
        raise Stop(f"STOP: {name} runs on a replacement CPU set: its gate needs cpu_determinism (the set's fixed-seed "
                   f"determinism check before its first use, {X_CPU_ROW})")


def node_census_cpus(node: dict) -> str | None:
    """The CPU set a CPU node's census ran on: its replacement's census set, or its own set."""
    return (node.get("cpu_replacement") or {}).get("census_cpus") or node.get("cpus")


def validate_x(spec: dict, *, launch: bool) -> None:
    """The node-expansion spec as a whole: its own run namespace, the census merge on main, checkouts apart per pin,
    CPU sets identical or disjoint (and apart from the host's GPU-job cpus when the spec has a GPU node), the census
    on TASL-2 itself (estimate ratio 1.0), the publication rule."""
    run_id = spec["run_id"]
    for path in (SEVEN_SPEC_REL, "sweep2/t1_tasl/g1b_tasl_ar_spec.json"):
        other = REPO_ROOT / path
        if other.is_file() and run_id == load_spec(other).get("run_id"):
            raise Stop(f"STOP: run_id must be the expansion spec's own, not {path}'s")
    if not run_id.startswith(X_RUN_PREFIX):
        raise Stop(f"STOP: run_id must be the expansion spec's own ({X_RUN_PREFIX}…)")
    if not X_RULE_TEXT.match(str(spec.get("note_rule", ""))):
        raise Stop(f"STOP: note_rule must cite {X_RULE}")
    if spec["timeout_decision"]["basis"] != "census_slowest_x3":
        raise Stop("STOP: timeout_decision.basis must be census_slowest_x3 (R1-G1B-TIMEOUT)")
    if spec.get("review_record") != X_REVIEW_RECORD:
        raise Stop(f"STOP: review_record must be {X_REVIEW_RECORD} (this unit's independent review, which P4 and the "
                   "review gates cite)")
    pre = spec.get("cpu_preflight") or {}
    sec, mx = pre.get("seconds"), pre.get("max_busy")
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (sec, mx)) or \
            not 2 <= sec <= 30 or not 0 < mx <= 0.5:
        raise Stop("STOP: cpu_preflight must give seconds in [2, 30] and max_busy in (0, 0.5] (the CPU-set preflight)")
    est = spec["estimate"]
    if est.get("census_host") not in X_HOSTS or est["ratio_4090_over_ada"] != 1.0:
        raise Stop("STOP: estimate.census_host must be TASL-2 with ratio 1.0 (the censuses ran on TASL-2 itself)")
    dirs: dict[str, str] = {}
    for node in spec["nodes"]:
        commit, d = node["harness"]["commit"], node["harness"]["dir"]
        if dirs.get(d, commit) != commit:
            raise Stop(f"STOP: {d} is the checkout of two harness pins")
        dirs[d] = commit
    paths = sorted(Path(d) for d in dirs)
    host = spec["hosts"][X_HOSTS[0]]
    if set(cpu_list(host.get("cpus", ""))) & X_EXCLUDED_CPUS:
        raise Stop(f"STOP: hosts.{X_HOSTS[0]}.cpus {host.get('cpus')} contains CPUs 8-11: no R1 job on TASL-2 uses them "
                   f"({X_CPU_ROW})")
    roots = [Path(host[k]) for k in ("data_root", "runs_root", "sealed_root")]
    for i, a in enumerate(paths):
        for b in paths[i + 1:]:
            if a in b.parents:
                raise Stop(f"STOP: the checkout {b} lies inside the checkout {a}")
        for r in roots:
            if a == r or a in r.parents or r in a.parents:
                raise Stop(f"STOP: the checkout {a} and the root {r} overlap")
    records = [n["cpu_replacement"]["determinism_check"]["record"] for n in spec["nodes"] if n.get("cpu_replacement")]
    if len(records) != len(set(records)):
        raise Stop("STOP: two replacement CPU sets name one determinism check record")
    sets = {n["node"]: set(cpu_list(n["cpus"])) for n in spec["nodes"] if n["device"] == "cpu"}
    names = sorted(sets)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if sets[a] & sets[b] and sets[a] != sets[b]:
                raise Stop(f"STOP: the CPU sets of {a} and {b} overlap without being equal (equal sets run one after "
                           "another under the CPU-set lease)")
    if any(n["device"] == "gpu" for n in spec["nodes"]):
        gpu_cpus = set(cpu_list(host["cpus"]))
        for name, own in sets.items():
            if own & gpu_cpus:
                raise Stop(f"STOP: {name}.cpus overlaps the cpus of the host's GPU jobs")


def node_entry(spec: dict, name: str) -> dict:
    for node in spec["nodes"]:
        if node["node"] == name:
            return node
    raise Stop(f"STOP: {name} is not in the spec")


def chunk_file(spec: dict, node: dict, part: tuple, *, interpreter: str, cgroup_parent: str, deadline: float) -> dict:
    chunk = L.chunk_file(spec, node, part, interpreter=interpreter, cgroup_parent=cgroup_parent, deadline=deadline,
                         memory_limit=f"external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 "
                                      f"(delegated scope {cgroup_parent})")
    chunk["measured_run_seconds"] = timeout_basis(spec, node)      # the engine's timeout = 3 x this basis
    chunk["device"] = node["device"]
    chunk["stop_on_timeout"] = True       # the first run that reaches the timeout stops the chunk (timing STOP)
    return chunk


# =============================================================================================== host checks
def _sh(argv, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True, timeout=kw.pop("timeout", 600), **kw)


def host_identity(spec: dict, host_name: str) -> dict:
    host = spec["hosts"][host_name]
    got = socket.gethostname()
    if got != host["hostname"]:
        raise Stop(f"STOP: this is {got!r}, the spec assigns the node to {host_name} ({host['hostname']!r})")
    if os.geteuid() == 0:
        raise Stop("STOP: runs as root; isolated runs need a non-root uid (no root waiver)")
    return {"host": host_name, "hostname": got, "uid": os.getuid(), "kernel": os.uname().release,
            "affinity": sorted(os.sched_getaffinity(0))}


def gpu_check(spec: dict, host_name: str, smi=_sh) -> dict:
    want = spec["hosts"][host_name]["gpu_uuid"]
    res = smi(["nvidia-smi", "--query-gpu=uuid,name,driver_version,memory.total", "--format=csv,noheader"])
    if res.returncode != 0:
        raise Stop(f"STOP: nvidia-smi failed: {res.stderr.strip()[:200]}")
    gpus = {r[0]: r for r in ([x.strip() for x in line.split(",")] for line in res.stdout.splitlines() if line.strip())}
    if want not in gpus:
        raise Stop(f"STOP: the leased GPU {want} is not on this host ({sorted(gpus)})")
    if gpus[want][1] != GPU_MODEL:
        raise Stop(f"STOP: {want} is {gpus[want][1]}, not {GPU_MODEL} (one GPU model for the table)")
    return {"uuid": want, "name": gpus[want][1], "driver": gpus[want][2], "memory_total": gpus[want][3]}


def foreign_processes(gpu_uuid: str, own_pids: set[int], smi=_sh) -> list[dict]:
    """Compute processes on the leased GPU that are not this job's (the no-shared-card rule)."""
    res = smi(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,used_memory", "--format=csv,noheader"])
    if res.returncode != 0:
        raise Stop(f"STOP: nvidia-smi compute-apps query failed: {res.stderr.strip()[:200]}")
    out = []
    for line in res.stdout.splitlines():
        parts = [x.strip() for x in line.split(",")]
        if len(parts) >= 2 and parts[0] == gpu_uuid and parts[1].isdigit() and int(parts[1]) not in own_pids:
            out.append({"pid": int(parts[1]), "used_memory": parts[2] if len(parts) > 2 else None})
    return out


def check_no_foreign(gpu_uuid: str | None, when: str, smi=_sh) -> dict:
    if gpu_uuid is None:
        return {"when": when, "device": "cpu"}
    foreign = foreign_processes(gpu_uuid, {os.getpid()}, smi)
    if foreign:
        raise Stop(f"STOP: foreign compute processes on the leased GPU {when}: {foreign} (no shared card)")
    return {"when": when, "foreign": []}


def ptrace_scope(path: Path = Path("/proc/sys/kernel/yama/ptrace_scope")) -> int:
    try:
        value = int(path.read_text().strip())
    except (OSError, ValueError):
        raise Stop(f"STOP: {path} unreadable (Yama ptrace_scope must be >= 1)") from None
    if value < 1:
        raise Stop(f"STOP: Yama ptrace_scope is {value}; the harness isolation needs >= 1")
    return value


def scope_cgroup(env=os.environ, delegated=L.delegated_cgroup) -> dict:
    """The delegated scope the wrapper started: AR_TEST_CGROUP_PARENT is this process's own cgroup, with the census
    memory limits and cgroup.kill."""
    own = delegated()
    given = env.get("AR_TEST_CGROUP_PARENT")
    if given != own:
        raise Stop(f"STOP: AR_TEST_CGROUP_PARENT={given!r} is not this job's delegated scope {own!r} "
                   "(start the job with t1_tasl_node.sh)")
    limits = {}
    for name, want in (("memory.max", str(MEMORY_MAX)), ("memory.swap.max", "0")):
        got = (Path(own) / name).read_text().strip()
        if got != want:
            raise Stop(f"STOP: {name} of the scope is {got}, expected {want} (MemoryMax=8G, MemorySwapMax=0)")
        limits[name] = got
    return {"cgroup_parent": own, **limits}


def harness_checkout(spec: dict, host_name: str, git=_sh, node: dict | None = None) -> dict:
    """The harness checkout at its pin and clean: the host's (seven-node, AR kinds) or, given the node of a
    node-expansion spec, that node's own checkout and pin."""
    if node is not None and is_x(spec):
        root, pin = node_harness_dir(spec, node), node_harness_commit(spec, node)
    else:
        root, pin = spec["hosts"][host_name]["harness_dir"], spec["harness"]["commit"]
    head = git(["git", "-C", root, "rev-parse", "HEAD"]).stdout.strip()
    if head != pin:
        raise Stop(f"STOP: the harness checkout {root} is at {head!r}, not the pin {pin}")
    status = git(["git", "-C", root, "status", "--porcelain", "--untracked-files=all"]).stdout.splitlines()
    stray = [line for line in status if not re.fullmatch(r"\?\? (third_party/mlgym/)?nodes/[a-z0-9_]+/data", line.strip())]
    if stray:
        raise Stop(f"STOP: the harness checkout is not clean at the pin (only nodes/<node>/data links allowed): "
                   f"{stray[:5]}")
    return {"dir": root, "commit": head}


def environment(spec: dict, host_name: str, node: dict, sh=_sh) -> dict:
    host = spec["hosts"][host_name]
    python = host["env_python"][node["env"]]
    freeze = HERE.parent / "g1b" / spec["envs"][node["env"]]["freeze"]
    tool = "pip" if is_x(spec) and spec["envs"][node["env"]].get("freeze_tool") == "pip" else "uv pip"
    if tool == "pip":          # as the node's census froze it (MetaMaze's venv_jax: python -m pip freeze)
        got = sh([python, "-m", "pip", "--disable-pip-version-check", "freeze"])
    else:
        got = sh([host["uv"], "pip", "freeze", "--python", python])
    if got.returncode != 0:
        raise Stop(f"STOP: {tool} freeze failed for {python}: {got.stderr.strip()[:200]}")
    have = L.compare_freeze(got.stdout, freeze.read_text(), node["env"])
    version = sh([python, "-c", "import sys; print(sys.version.split()[0])"]).stdout.strip()
    if version != spec["envs"][node["env"]]["python"]:
        raise Stop(f"STOP: {python} is Python {version}, not {spec['envs'][node['env']]['python']}")
    return {"name": node["env"], "python": python, "python_version": version,
            "freeze_sha256": spec["envs"][node["env"]]["sha256"], "packages": len(have)}


@contextlib.contextmanager
def gpu_lease(path: str, what: str = "GPU lease", why: str = "no shared card"):
    """An exclusive, non-blocking flock on the host's lease file for the whole job; a busy lease is a STOP. The
    node-expansion CPU nodes use the same lock for their CPU-set lease (``what``/``why`` name it in the STOP)."""
    lease = Path(os.path.expanduser(path))
    lease.parent.mkdir(parents=True, exist_ok=True)
    fh = lease.open("a+")
    try:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Stop(f"STOP: the {what} {lease} is held by another job ({why})") from None
        yield {"lease": str(lease), "pid": os.getpid()}
    finally:
        with contextlib.suppress(OSError):
            fcntl.flock(fh, fcntl.LOCK_UN)
        fh.close()


# =============================================================================================== attempts, refusals
ATTEMPT = re.compile(r"^attempt-([1-9][0-9]*)$")
NO_RETRY = (None, "node", "timing")     # a complete attempt, or an author STOP: no new attempt of the node


def write_refusal(run_root: Path, node: str, message: str, record: dict) -> Path | None:
    """A refusal before any run: kept under <run_id>/_refusals/, so it never uses up the node's attempt. If the refusal
    itself cannot be written, the original message still reaches stderr and the caller's STOP stands."""
    try:
        return _write_refusal(run_root, node, message, record)
    except Exception as exc:  # noqa: BLE001
        print(f"{message}\n(refusal record not written: {type(exc).__name__}: {exc})", file=sys.stderr)
        return None


def _write_refusal(run_root: Path, node: str, message: str, record: dict) -> Path:
    d = Path(run_root) / "_refusals"
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{node}-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{os.getpid()}-{time.time_ns()}.json"
    with path.open("x") as fh:          # never overwritten
        fh.write(json.dumps({**record, "stop": message, "stop_class": "refused_before_run"}, indent=1,
                            sort_keys=True, default=str) + "\n")
    return path


def attempts(node_root: Path) -> list[tuple[int, Path]]:
    if not Path(node_root).is_dir():
        return []
    out = []
    for p in Path(node_root).iterdir():
        m = ATTEMPT.fullmatch(p.name)
        if not m or p.is_symlink() or not p.is_dir():
            raise Stop(f"STOP: unexpected entry {p} in the node directory")
        out.append((int(m.group(1)), p))
    return sorted(out)


def next_attempt(node_root: Path) -> tuple[int, Path]:
    """The next attempt directory, created; refused when an earlier attempt is complete, ended in an author STOP
    (node or timing), or left no job record."""
    done = attempts(node_root)
    for n, p in done:
        rec_path = p / "job_record.json"
        if not rec_path.is_file():
            raise Stop(f"STOP: {p} has no job record; inspect it before another attempt")
        stop_class = json.loads(rec_path.read_text()).get("stop_class")
        if stop_class in NO_RETRY:
            raise Stop(f"STOP: {p} ended with stop_class {stop_class!r}; no new attempt of this node "
                       "(only an infrastructure STOP may be retried)")
    n = (done[-1][0] + 1) if done else 1
    path = Path(node_root) / f"attempt-{n}"
    path.mkdir(parents=True, exist_ok=False)
    with (path / "attempt.json").open("x") as fh:     # who owns the attempt, for close-attempt
        fh.write(json.dumps({"attempt": n, "pid": os.getpid(), "hostname": socket.gethostname(),
                             "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}) + "\n")
    return n, path


def processes_mentioning(path: Path, proc_root: Path = Path("/proc")) -> list[int]:
    """PIDs whose command line names ``path`` as given, absolute or resolved (an engine left running in the scope has
    ``--chunk <attempt>/out/...`` with the unresolved runs root)."""
    needles = {str(Path(path)).encode(), str(Path(path).absolute()).encode(), str(Path(path).resolve()).encode()}
    out = []
    for d in proc_root.iterdir():
        if d.name.isdigit():
            try:
                cmdline = (d / "cmdline").read_bytes()
                if any(n in cmdline for n in needles):
                    out.append(int(d.name))
            except OSError:
                continue
    return sorted(out)


def close_attempt(attempt_dir: Path, reason: str, *, lease: str | None, alive=None, scan=processes_mentioning) -> dict:
    """Close an attempt that left no job record (the host rebooted, the scope was killed): after checking it is not
    running — same host, its process gone, and the GPU lease free — write a job record with stop_class
    "infrastructure" and the reason, so the next attempt may start. Nothing is deleted."""
    attempt_dir = Path(attempt_dir)
    if not ATTEMPT.fullmatch(attempt_dir.name) or (attempt_dir / "job_record.json").exists():
        raise Stop("STOP: close-attempt needs an attempt directory without a job record")
    if not isinstance(reason, str) or len(reason.strip()) < 10:
        raise Stop("STOP: close-attempt needs a reason (at least 10 characters)")
    running = scan(attempt_dir)
    if running:
        raise Stop(f"STOP: processes {running} still name {attempt_dir} on their command line")
    owner_path = attempt_dir / "attempt.json"
    owner = json.loads(owner_path.read_text()) if owner_path.is_file() else \
        {"attempt": int(ATTEMPT.fullmatch(attempt_dir.name).group(1)), "pid": None,
         "hostname": socket.gethostname(), "note": "no attempt.json (crash between mkdir and its write)"}
    if owner.get("hostname") != socket.gethostname():
        raise Stop(f"STOP: the attempt was started on {owner.get('hostname')!r}; close it there")

    def _alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True
    if owner["pid"] is not None and (alive or _alive)(int(owner["pid"])):
        raise Stop(f"STOP: process {owner['pid']} of the attempt is still alive")
    held = gpu_lease(lease) if lease else contextlib.nullcontext()
    with held:      # a busy lease is a STOP: something still runs on the card
        record = {"schema": RECORD_SCHEMA, "label": ENGINEERING_ONLY, "attempt": owner["attempt"],
                  "stop": f"STOP: closed without a job record: {reason.strip()}", "stop_class": "infrastructure",
                  "closed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "owner": owner}
        with (attempt_dir / "job_record.json").open("x") as fh:
            fh.write(json.dumps(record, indent=1, sort_keys=True) + "\n")
    return record


def check_affinity(spec: dict, node: dict, affinity=None) -> list[int]:
    got = sorted(affinity if affinity is not None else os.sched_getaffinity(0))
    want = cpu_list(node_cpus(spec, node))
    if got != want:
        raise Stop(f"STOP: CPU affinity {got} is not the node's declared cpus {want} (start it with the wrapper)")
    return got


HOST_RECORD_FIELDS = ("host_check_host", "host_check_harness_commit", "host_check_items", "host_check_verdict")


def check_host_record(spec_host: dict, harness_commit: str, read_main) -> dict:
    """R1-T1-HOST-TASL's precondition: the host's harness-isolation check report, on published main, with the declared
    sha256, naming this host and the harness pin, items 1-7 of HARNESS_ISOLATION_20261117 §3 PASS, verdict PASS."""
    check = spec_host.get("isolation_host_check") or {}
    rel = check.get("record", "")
    if L._placeholder(rel) or not rel.startswith("docs/r1/reports/") or ".." in Path(rel).parts:
        raise Stop("STOP: isolation_host_check.record must be a report path under docs/r1/reports/ (no placeholder)")
    raw = read_main(rel)
    if raw is None:
        raise Stop(f"STOP: the host check report {rel} is not on published main")
    if hashlib.sha256(raw).hexdigest() != check.get("sha256"):
        raise Stop(f"STOP: the host check report {rel} differs from its declared sha256")
    fields = {}
    for line in raw.decode("utf-8", "replace").splitlines():
        m = re.match(r"^(host_check_[a-z_]+):\s*(.*?)\s*$", line)
        if m:
            if m.group(1) in fields:
                raise Stop(f"STOP: duplicate {m.group(1)} in {rel}")
            fields[m.group(1)] = m.group(2)
    want = {"host_check_host": spec_host["hostname"], "host_check_harness_commit": harness_commit,
            "host_check_items": "1-7 PASS", "host_check_verdict": "PASS"}
    bad = {k: fields.get(k) for k, v in want.items() if fields.get(k) != v}
    if bad:
        raise Stop(f"STOP: the host check report {rel} does not show a PASS for this host and pin: {bad}")
    return {"record": rel, "sha256": check["sha256"]}


def check_env_row(row: str, read_main) -> str:
    """Decision AR-ENV: the environment row's PLAN line on published main names the AR census environment."""
    plan = (read_main("docs/r1/PLAN.md") or b"").decode("utf-8", "replace")
    lines = [ln for ln in plan.splitlines() if re.match(rf"^\| {re.escape(row)} \|", ln)]
    if len(lines) != 1 or AR_ENV not in lines[0]:
        raise Stop(f"STOP: the PLAN row {row} on published main must exist once and name {AR_ENV} (decision AR-ENV)")
    return lines[0]


def _read_main(rel: str) -> bytes | None:
    res = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"origin/main:{rel}"], capture_output=True)
    return res.stdout if res.returncode == 0 else None


# =============================================================================================== the node job
def timing_check(rows: list[dict], node: dict, part: str) -> dict:
    """Report the 4090/Ada ratio of the part's baseline runs; a timeout row is a STOP (the engine already stops at the
    first one, with stop_on_timeout)."""
    timeouts = [r["run_id"] for r in rows if (r.get("failure") or "").startswith("divergent:timeout")]
    if timeouts:
        raise TimingStop(f"STOP: {node['node']} part {part}: {len(timeouts)} run(s) reached the declared timeout on "
                         f"{_where(node)} ({timeouts[:3]}): the census timing does not carry over (author decides)")
    walls = sorted(float(r["wall_seconds"]) for r in rows if r.get("config") == "c0" and r.get("wall_seconds"))
    median = walls[len(walls) // 2] if walls else None
    return {"part": part, "c0_median_wall_s": median,
            "ratio_4090_over_ada": round(median / float(node["run_seconds"]), 4) if median else None,
            "max_wall_s": max((float(r["wall_seconds"]) for r in rows if r.get("wall_seconds")), default=None)}


def _where(node: dict) -> str:
    """Where a node's runs execute, in STOP messages: the 4090, or a CPU node's CPU set."""
    return f"its CPU set (cpus {node['cpus']})" if node.get("device") == "cpu" and node.get("cpus") \
        else "the 4090"


PROC_STAT = Path("/proc/stat")


def _cpu_times(stat: Path) -> dict[int, tuple[int, int]]:
    """Per CPU: (busy, total) jiffies from /proc/stat (idle and iowait count as not busy)."""
    out = {}
    for line in stat.read_text().splitlines():
        m = re.match(r"^cpu(\d+)\s+(.*)$", line)
        if m:
            v = [int(x) for x in m.group(2).split()]
            idle = v[3] + (v[4] if len(v) > 4 else 0)
            total = sum(v[:8])
            out[int(m.group(1))] = (total - idle, total)
    return out


def cpu_busy_check(spec: dict, node: dict, when: str, *, stat: Path | None = None, sleep=time.sleep) -> dict:
    """Fail-closed CPU-set preflight of a node-expansion CPU node: sample /proc/stat over ``cpu_preflight.seconds`` and
    refuse if any CPU of the node's CPU set was busier than ``cpu_preflight.max_busy`` (another job on the set; the
    G.5 jobs take no CPU lease). Before the attempt a refusal goes to _refusals/ and uses up nothing; before a later
    part it is an infrastructure STOP (a new attempt may follow). The readings are recorded."""
    cfg = spec["cpu_preflight"]
    cpus = cpu_list(node_cpus(spec, node))
    stat = stat or PROC_STAT
    a = _cpu_times(stat)
    sleep(float(cfg["seconds"]))
    b = _cpu_times(stat)
    busy = {}
    for c in cpus:
        if c not in a or c not in b:
            raise Stop(f"STOP: cpu {c} of {node['node']}'s set is not in {stat}")
        dt = b[c][1] - a[c][1]
        busy[c] = round((b[c][0] - a[c][0]) / dt, 4) if dt > 0 else 1.0
    reading = {"when": when, "cpus": node_cpus(spec, node), "seconds": cfg["seconds"], "max_busy": cfg["max_busy"],
               "busy": {str(c): v for c, v in busy.items()},
               "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    over = {c: v for c, v in busy.items() if v > float(cfg["max_busy"])}
    if over:
        raise Stop(f"STOP: CPUs {sorted(over)} of {node['node']}'s CPU set were busy {over} over "
                   f"{cfg['seconds']} s {when} (max {cfg['max_busy']}): another job uses the set; reading {reading}")
    return reading


def preflight(spec: dict, node: dict, smi=_sh) -> dict:
    """Every host check that needs no output directory (run under the lease, before an attempt is created)."""
    host_name = node["host"]
    gpu = None if node["device"] == "cpu" else spec["hosts"][host_name]["gpu_uuid"]
    out = {"host": host_identity(spec, host_name), "affinity": check_affinity(spec, node),
           "gpu": gpu_check(spec, host_name, smi) if gpu else {"device": "cpu"},
           "foreign_before": check_no_foreign(gpu, "before the job", smi),
           "ptrace_scope": ptrace_scope(), "cgroup": scope_cgroup(),
           "harness": harness_checkout(spec, host_name, node=node) if is_x(spec) else harness_checkout(spec, host_name),
           "environment": environment(spec, host_name, node)}
    return out


def run_node_job(spec_path: Path, node_name: str, *, started: float | None = None, smi=_sh,
                 engine=subprocess.run, setup=L.run_setup, node_log: str | None = None) -> dict:
    """One node on its host, inside the delegated scope. Preflight under the lease first; a refusal there goes to
    ``<runs_root>/<run_id>/_refusals/`` and uses up nothing. Then a new ``<node>/attempt-N/`` with out/,
    job_record.json, out.tar and SHA256SUMS. Raises Stop on a STOP. ``stop_class``: None, "node" (determinism),
    "timing" (a 4090 timeout) or "infrastructure" (may be retried as a new attempt)."""
    started = started or time.time()
    spec = load_spec(spec_path)
    loaded = validate_spec(spec, launch=True)
    node = node_entry(spec, node_name)
    host_name = node["host"]
    host = spec["hosts"][host_name]
    run_root = Path(host["runs_root"]) / spec["run_id"]
    gpu = None if node["device"] == "cpu" else host["gpu_uuid"]
    node_log = node_log or os.environ.get("G1B_TASL_NODE_LOG")
    record: dict = {"schema": RECORD_SCHEMA, "label": ENGINEERING_ONLY, "node": node_name, "run_id": spec["run_id"],
                    "spec_sha256": L._sha_file(spec_path), "harness_commit": node_harness_commit(spec, node),
                    "device": node["device"], "parts": [], "timing": [], "foreign_checks": [], "stop": None,
                    "stop_class": None, "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
                    "node_log": node_log,
                    "timeout_basis": {"decision": spec["timeout_decision"]["basis"],
                                      "seconds": timeout_basis(spec, node), "timeout_s": 3 * timeout_basis(spec, node)},
                    "output_use": "ENGINEERING_ONLY G.1b noise floor (D21) on the TASL pair; no labels read",
                    "deadline_s": node_wall_limit(spec, node),
                    "projection": loaded["projection"]["estimate"]["per_node"][node_name]}
    if is_ar(spec):       # the third note's job: its own spec kind and the AR census environment, disclosed
        record.update(spec_schema=AR_SCHEMA, note_rule=spec["note_rule"],
                      env_decision=spec["env_decision"].get("authority"),
                      output_use="ENGINEERING_ONLY G.1b noise floor (D21) of autoresearch_fixedtokens on TASL-2 "
                                 f"under its own spec ({AR_RULE}, NOTE2-AR A); no labels read")
    if is_x(spec):        # the node-expansion job: its own pin, CPU set and engine admission, disclosed
        record.update(spec_schema=X_SCHEMA, note_rule=spec["note_rule"], cpu_only=node.get("cpu_only"),
                      cpus=node.get("cpus"), census_cpus=node_census_cpus(node),
                      cpu_replacement=(node.get("cpu_replacement") or {}).get("authority"),
                      census_record=node["census_record"],
                      output_use=f"ENGINEERING_ONLY G.1b noise floor (D21) of {node_name} on TASL-2 under the "
                                 f"node-expansion spec ({X_RULE}); no labels read")
    deadline = started + node_wall_limit(spec, node)
    lease_path = node_lease(spec, node)
    if lease_path and node["device"] == "cpu":       # an expansion CPU node: its CPU-set lease
        lease_cm = gpu_lease(lease_path, "CPU-set lease", "one expansion node per CPU set")
    else:
        lease_cm = gpu_lease(lease_path) if lease_path else contextlib.nullcontext({"lease": None})
    try:
        lease = lease_cm.__enter__()
    except Stop as exc:
        write_refusal(run_root, node_name, str(exc), record)
        raise
    except Exception as exc:  # noqa: BLE001 - e.g. the lease directory cannot be made
        message = f"STOP: unexpected {type(exc).__name__} taking the lease: {exc}"
        write_refusal(run_root, node_name, message, record)
        raise Stop(message) from exc
    try:
        record["lease"] = lease
        try:
            record.update(preflight(spec, node, smi))
            if is_x(spec):
                record["cpu_preflight"] = [cpu_busy_check(spec, node, "before the attempt")]
            record["attempt"], job_dir = next_attempt(run_root / node_name)
        except Stop as exc:
            write_refusal(run_root, node_name, str(exc), record)
            raise
        except Exception as exc:  # noqa: BLE001 - a crash in a check is a refusal with a record, not a traceback
            message = f"STOP: unexpected {type(exc).__name__} before the run: {exc}"
            write_refusal(run_root, node_name, message, record)
            raise Stop(message) from exc
        record["foreign_checks"].append(record.pop("foreign_before"))
        out = job_dir / "out"
        out.mkdir()
        try:
            harness = Path(node_harness_dir(spec, node))
            env_bin = str(Path(host["env_python"][node["env"]]).parent)
            os.environ["PATH"] = f"{env_bin}:{os.environ.get('PATH', '')}"
            for key, value in (host.get("extra_env") or {}).items():
                os.environ[key] = value
            record["data"] = setup(harness, node, Path(host["base"]), out)
            engine_env = dict(os.environ, PYTHONPATH=str(harness / "src"), PYTHONDONTWRITEBYTECODE="1",
                              AR_TRACKG_DATA_ROOT=record["data"]["data_root"], CUDA_VISIBLE_DEVICES="")
            for name in ("NVIDIA_VISIBLE_DEVICES", "_CONDOR_AssignedGPUs"):
                engine_env.pop(name, None)
            for part in L.PARTS:
                record["foreign_checks"].append(check_no_foreign(gpu, f"before {part[0]}", smi))
                if is_x(spec) and node["device"] == "cpu":
                    record["cpu_preflight"].append(cpu_busy_check(spec, node, f"before {part[0]}"))
                chunk = chunk_file(spec, node, part, interpreter=host["env_python"][node["env"]],
                                   cgroup_parent=record["cgroup"]["cgroup_parent"], deadline=deadline)
                chunk_path = out / f"chunk_{part[0]}.json"
                chunk_path.write_text(json.dumps(chunk, indent=1) + "\n")
                remaining = int(deadline - time.time())
                if remaining < 60:
                    raise Stop(f"STOP: the node deadline was reached before part {part[0]}")
                argv = [host["env_python"][node["env"]], "-m", "autoresearch.trackg.noise_floor", "--chunk",
                        str(chunk_path), "--harness-root", str(harness), "--out", str(out / part[0])]
                if is_x(spec) and node.get("cpu_only") == "census_override":
                    argv[1:3] = ["-c", X_ENGINE_OVERRIDE, node_name]
                if gpu:
                    argv += ["--gpu-uuid", gpu]
                try:
                    res = engine(argv, cwd=harness, env=engine_env, capture_output=True, text=True, timeout=remaining)
                except subprocess.TimeoutExpired as exc:
                    (out / f"engine_{part[0]}.log").write_text(f"{L._text(exc.stdout)}\n--- stderr ---\n"
                                                             f"{L._text(exc.stderr)}")
                    raise Stop(f"STOP: part {part[0]} reached the node deadline; outputs kept") from None
                (out / f"engine_{part[0]}.log").write_text(res.stdout + "\n--- stderr ---\n" + res.stderr)
                cr_path = out / part[0] / "chunk_record.json"
                chunk_record = json.loads(cr_path.read_text()) if cr_path.is_file() else \
                    {"stop": f"engine rc {res.returncode}"}
                record["parts"].append({"part": part[0], "rc": res.returncode,
                                        **{k: chunk_record.get(k) for k in ("expected_runs", "written_rows",
                                                                            "successful_rows", "stop", "stop_kind")}})
                rows = L._rows(out / part[0] / "runs.jsonl") if (out / part[0] / "runs.jsonl").is_file() else []
                if chunk_record.get("stop_kind") == "timeout":
                    raise TimingStop(f"STOP: {node_name} part {part[0]}: {chunk_record.get('stop')} — the census "
                                     f"timing does not carry over to {_where(node)} (author decides)")
                record["timing"].append(timing_check(rows, node, part[0]))
                if res.returncode != 0 or chunk_record.get("stop"):
                    raise Stop(f"STOP: {node_name} part {part[0]}: "
                               f"{chunk_record.get('stop') or 'engine rc ' + str(res.returncode)}")
                record["foreign_checks"].append(check_no_foreign(gpu, f"after {part[0]}", smi))
                if part[0] == "default":
                    record["determinism"] = L.determinism_check(rows)
                    L.default_gate(out)
            record["runs"] = L.merge_parts(out, node)
        except NodeStop as exc:
            record["stop"], record["stop_class"] = str(exc), "node"
        except TimingStop as exc:
            record["stop"], record["stop_class"] = str(exc), "timing"
        except Stop as exc:
            record["stop"], record["stop_class"] = str(exc), "infrastructure"
        except Exception as exc:  # noqa: BLE001 - every failure inside an attempt writes the record and the sums
            record["stop"], record["stop_class"] = f"STOP: unexpected {type(exc).__name__}: {exc}", "infrastructure"
        record["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        (job_dir / "job_record.json").write_text(json.dumps(record, indent=1, sort_keys=True, default=str) + "\n")
        subprocess.run(["tar", "-cf", "out.tar", "out"], cwd=job_dir, check=False)
        L._write_sums(job_dir, ("out.tar", "job_record.json"))
    finally:
        lease_cm.__exit__(None, None, None)
    if record["stop"]:
        raise Stop(record["stop"])
    return record


# =============================================================================================== seal / assemble
def seal(job_dir: Path, spec: dict, node_name: str) -> dict:
    """Verify the attempt's SHA256SUMS and record, copy it to <sealed_root>/<run_id>/<node>/attempt-N/ on the node's
    host (no overwrite) with the wrapper log, and write a receipt binding the record and the log."""
    src = Path(job_dir).resolve()
    node = node_entry(spec, node_name)
    record = json.loads((src / "job_record.json").read_text())
    if record.get("label") != ENGINEERING_ONLY or record.get("run_id") != spec["run_id"] or record.get("node") != node_name:
        raise Stop("STOP: the job record does not match the run/node or is not ENGINEERING_ONLY")
    if src.name != f"attempt-{record.get('attempt')}":
        raise Stop("STOP: the job directory is not the attempt its record names")
    if (record.get("host") or {}).get("host") != node["host"]:
        raise Stop("STOP: the job did not run on the node's assigned host")
    if node["device"] == "gpu" and (record.get("gpu") or {}).get("name") != GPU_MODEL:
        raise Stop("STOP: the job record lacks the RTX 4090 identity")
    if subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=src, capture_output=True).returncode != 0:
        raise Stop("STOP: SHA256SUMS verification failed")
    target = Path(spec["hosts"][node["host"]]["sealed_root"]) / spec["run_id"] / node_name / src.name
    if target.exists() or any(p.is_symlink() for p in [target, *target.parents] if p.exists()):
        raise Stop(f"STOP: sealed target {target} exists or has a symlink component; no overwrite")
    target.mkdir(parents=True, mode=0o700)
    for name in ("out.tar", "job_record.json", "SHA256SUMS"):
        shutil.copy2(src / name, target / name)
    log = record.get("node_log")
    logs_dir = (Path(spec["hosts"][node["host"]]["runs_root"]) / spec["run_id"] / "_logs").resolve()
    if log and Path(log).is_file() and Path(log).resolve().parent == logs_dir:
        shutil.copy2(log, target / "node.log")
    receipt = {"schema": RECEIPT_SCHEMA, "run_id": spec["run_id"], "node": node_name, "host": node["host"],
               "attempt": record.get("attempt"), "sealed_path": str(target), "stop": record.get("stop"),
               "stop_class": record.get("stop_class"),
               "job_record_sha256": L._sha_file(target / "job_record.json"),
               "node_log_sha256": L._sha_file(target / "node.log") if (target / "node.log").is_file() else None,
               "sealed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    (target / "SEAL_RECEIPT.json").write_text(json.dumps(receipt, indent=1) + "\n")
    return receipt


def _assembly_schema(spec: dict) -> str:
    return AR_ASSEMBLY_SCHEMA if is_ar(spec) else X_ASSEMBLY_SCHEMA if is_x(spec) else ASSEMBLY_SCHEMA


def assemble(sealed_dirs: list[Path], spec: dict, dest: Path, spec_file_sha256: str) -> dict:
    """Join one sealed attempt per node of both hosts (each verified against its receipt and sums, this run id and
    spec sha256, its assigned host, the RTX 4090 for GPU nodes, the harness commit, no infrastructure or timing STOP)
    into one run directory in the layout ``g1b_lib.summarise`` reads. The other sealed attempts of each node are listed;
    a sibling attempt that is complete or ended in an author STOP is a STOP (no choosing between attempts)."""
    dest = Path(dest)
    if dest.exists():
        raise Stop(f"STOP: {dest} exists (no overwrite)")
    rows, edits, jobs = [], {}, []
    work = dest / "_unpacked"
    work.mkdir(parents=True)
    for sealed in map(Path, sealed_dirs):
        if not (sealed / "SEAL_RECEIPT.json").is_file():
            raise Stop(f"STOP: {sealed} has no SEAL_RECEIPT.json")
        if subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=sealed, capture_output=True).returncode != 0:
            raise Stop(f"STOP: {sealed} does not verify against its SHA256SUMS")
        record = json.loads((sealed / "job_record.json").read_text())
        receipt = json.loads((sealed / "SEAL_RECEIPT.json").read_text())
        node = node_entry(spec, record.get("node"))
        problems = [k for k, ok in (
            ("receipt", receipt.get("job_record_sha256") == L._sha_file(sealed / "job_record.json")
             and receipt.get("run_id") == spec["run_id"] and receipt.get("node") == record.get("node")
             and receipt.get("host") == node["host"] and receipt.get("attempt") == record.get("attempt")),
            ("spec_sha256", record.get("spec_sha256") == spec_file_sha256),
            ("run_id", record.get("run_id") == spec["run_id"]),
            ("harness_commit", record.get("harness_commit") == node_harness_commit(spec, node)),
            ("host", (record.get("host") or {}).get("host") == node["host"]),
            ("gpu", node["device"] == "cpu" or (record.get("gpu") or {}).get("name") == GPU_MODEL),
            ("stop_class", record.get("stop_class") in (None, "node"))) if not ok]
        if problems:
            raise Stop(f"STOP: {sealed} job record does not match the table: {problems}")
        name = record["node"]
        siblings = []
        for other in sorted(sealed.parent.glob("attempt-*")):
            if other.resolve() == sealed.resolve():
                continue
            other_rec = json.loads((other / "job_record.json").read_text()) if (other / "job_record.json").is_file() \
                else {"stop_class": "unknown"}
            if other_rec.get("stop_class") != "infrastructure":
                raise Stop(f"STOP: {name} has another sealed attempt {other.name} with stop_class "
                           f"{other_rec.get('stop_class')!r}: one attempt per node, chosen by the rule, not by result")
            siblings.append({"attempt": other.name, "stop": other_rec.get("stop")})
        target = work / name
        if target.exists():
            raise Stop(f"STOP: two sealed directories for {name}")
        target.mkdir()
        if subprocess.run(["tar", "-xf", str(sealed / "out.tar"), "-C", str(target)], capture_output=True).returncode:
            raise Stop(f"STOP: cannot unpack {sealed / 'out.tar'}")
        sub = "out/default" if record.get("stop_class") == "node" else "out"
        node_rows = L._rows(target / sub / "runs.jsonl")
        for row in node_rows:
            L.check_row_gate(row)
            if row.get("node") != name:
                raise Stop(f"STOP: a row of {sealed} names node {row.get('node')}")
        rows += node_rows
        edits.update(json.loads((target / sub / "edits.json").read_text()))
        jobs.append({"node": name, "host": node["host"], "attempt": record.get("attempt"), "sealed": str(sealed),
                     "stop_class": record.get("stop_class"), "infrastructure_attempts_not_used": siblings,
                     "job_record_sha256": L._sha_file(sealed / "job_record.json"), "spec_sha256": record.get("spec_sha256"),
                     "gpu_uuid": (record.get("gpu") or {}).get("uuid"), "device": node["device"],
                     "timing": record.get("timing")})
    (dest / "runs.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    (dest / "edits.json").write_text(json.dumps(edits, indent=1) + "\n")
    manifest = {"schema": _assembly_schema(spec), "run_id": spec["run_id"], "jobs": jobs,
                "spec_json_sha256": hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest(),
                "runs_sha256": L._sha_file(dest / "runs.jsonl")}
    (dest / "ASSEMBLY.json").write_text(json.dumps(manifest, indent=1) + "\n")
    return manifest


def summarise(run_dir: Path, spec: dict, paper_root: Path) -> dict:
    """The D21 verdicts (``g1b_lib.summarise``: exact coverage, the gate, determinism, the pinned e1_report rule and its
    independent double check), relabelled for the TASL table with the hosts and the 4090 timing per node."""
    assembly = json.loads((Path(run_dir) / "ASSEMBLY.json").read_text())
    if assembly.get("schema") != _assembly_schema(spec):
        raise Stop("STOP: the assembly is of the other spec kind (seven-node vs autoresearch-only vs node-expansion)")
    summary = L.summarise(run_dir, spec, paper_root)
    if is_ar(spec):       # its own summary, beside (never inside) the seven-node table's
        summary.update(note_rule=spec["note_rule"], env_decision=spec["env_decision"].get("authority"),
                       census_gpu_model=spec["estimate"]["census_gpu_model"])
    if is_x(spec):        # its own summary: each node's floor joins the T1 table by node (R1-T1-NODE-EXPANSION)
        summary.update(note_rule=spec["note_rule"], harness_commits={n["node"]: n["harness"]["commit"]
                                                                     for n in spec["nodes"]})
    summary.update(schema=AR_SUMMARY_SCHEMA if is_ar(spec) else X_SUMMARY_SCHEMA if is_x(spec) else SUMMARY_SCHEMA,
                   gpu_model=GPU_MODEL, hosts={j["node"]: j["host"] for j in assembly["jobs"]},
                   devices={j["node"]: j["device"] for j in assembly["jobs"]},
                   timing_4090={j["node"]: j.get("timing") for j in assembly["jobs"]},
                   timeout_basis=spec["timeout_decision"]["basis"])
    (Path(run_dir) / "summary.json").write_text(json.dumps(summary, indent=1, default=str) + "\n")
    return summary


# =============================================================================================== launch
def check_note(note_path: Path, spec_path: Path, paper_commit: str, *, on_main, spec: dict | None = None) -> dict:
    """The author-signed note: on published main, named g1b_t1_tasl_<date>.md, approved true, ENGINEERING_ONLY, binding
    the paper commit and the spec sha256 (and, given the spec, its run_id and the bare harness commit), P1-P6 PASS (P2
    the TASL-2 host check, P3 the TASL-7 host check, P4 the review file, P5 the edit-count row, P6 the timeout row), and
    citing the host/environment row."""
    if spec is not None and is_ar(spec):
        raise Stop("STOP: an autoresearch-only spec is launched under the third note (check_note_ar)")
    if spec is not None and is_x(spec):
        raise Stop("STOP: a node-expansion spec is launched under its own note (check_note_x)")
    note_path = Path(note_path)
    if note_path.parent.as_posix().split("/")[-3:] != NOTE_DIR.split("/") or not NOTE_NAME.fullmatch(note_path.name):
        raise Stop(f"STOP: the note must be {NOTE_DIR}/g1b_t1_tasl_<YYYYMMDD>.md")
    raw = note_path.read_bytes()
    if not on_main(f"{NOTE_DIR}/{note_path.name}", raw):
        raise Stop("STOP: the note is not committed byte-identically on origin/main")
    fields = {}
    for line in raw.decode().splitlines():
        m = re.match(r"^([A-Za-z0-9_]+)\s*:\s*(.*)$", line)
        if m:
            if m.group(1) in fields:
                raise Stop(f"STOP: duplicate note field {m.group(1)!r}")
            fields[m.group(1)] = m.group(2).strip()
    want = {"approved": "true", "label": ENGINEERING_ONLY, "labels_read": "none", "paper_commit": paper_commit,
            "spec_sha256": L._sha_file(spec_path)}
    for key, value in want.items():
        if fields.get(key) != value:
            raise Stop(f"STOP: note field {key} must be {value!r}")
    for key in ("P1", "P2", "P3", "P4", "P5", "P6"):
        if not fields.get(key, "").upper().startswith(("PASS — ", "PASS - ")):
            raise Stop(f"STOP: {key} is not PASS")
    cites = {"P1": "R1-T1-HOST-TASL", "P4": "docs/r1/reviews/", "P5": "R1-G1B-EDITS", "P6": "R1-G1B-TIMEOUT"}
    for key, cite in cites.items():
        if cite not in fields[key]:
            raise Stop(f"STOP: {key} must cite {cite}")
    if spec is not None:
        for key, value in (("run_id", spec["run_id"]), ("harness_commit", spec["harness"]["commit"])):
            if fields.get(key) != value:       # R1-T1-TASL-ENV: "harness at the commit the signed note names"
                raise Stop(f"STOP: note field {key} must be {value!r} (the spec's)")
        for key, h in (("P2", "TASL-2"), ("P3", "TASL-7")):
            rec = (spec["hosts"][h].get("isolation_host_check") or {}).get("record", "")
            if not rec or rec not in fields[key]:
                raise Stop(f"STOP: {key} must cite {h}'s host check report {rec!r}")
    host_row = fields.get("host_row", "")
    if not host_row.startswith("R1-T1-TASL-ENV"):
        raise Stop("STOP: host_row must cite the host/environment row R1-T1-TASL-ENV")
    return fields


AR_NOTE_CITES = {"P1": ("R1-TRACKG-AR-U2-TASL2",), "P4": ("docs/r1/reviews/",), "P5": ("R1-G1B-EDITS",),
                 "P6": ("R1-G1B-TIMEOUT",), "P8": ("R1-G1B-CAP",)}
AR_NOTE_PASS = ("P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8")


def _note_fields(raw: bytes) -> dict:
    fields = {}
    for line in raw.decode().splitlines():
        m = re.match(r"^([A-Za-z0-9_]+)\s*:\s*(.*)$", line)
        if m:
            if m.group(1) in fields:
                raise Stop(f"STOP: duplicate note field {m.group(1)!r}")
            fields[m.group(1)] = m.group(2).strip()
    return fields


def check_note_ar(note_path: Path, spec_path: Path, *, spec: dict, on_main=None, draft: bool = False) -> dict:
    """The third G.1b note (autoresearch_fixedtokens under its own spec; R1-G1B-NOTE2-DECISIONS NOTE2-AR A): named
    ``g1b_ar_t1_tasl_<date>.md`` under docs/r1/authorizations/, ENGINEERING_ONLY, no labels read, binding the spec's
    paper commit, the spec file's sha256, its run_id and full harness commit; ``note_rule`` citing
    R1-G1B-NOTE2-DECISIONS, ``host_row`` R1-T1-TASL-ENV and ``env_row`` the spec's ``env_decision`` row; P1-P8 PASS:
    P1 the AR census (R1-TRACKG-AR-U2-TASL2), P2 the TASL-2 host check at this harness pin (the spec's record and the
    pin), P3 the independent review of the harness pin (a docs/r1/reviews/ file and the pin), P4 the review of the spec
    support and spec, P5 the edit-count row, P6 the timeout row, P7 the environment row, P8 the shared G.1b cap.
    No field may hold a ``<…>`` placeholder or read PENDING.

    Two recorded steps, as for the second note: ``draft=True`` before signature (the note reads exactly one
    ``approved: false`` line and need not be on main; every other check runs), then strict mode (``approved: true``,
    byte-identical on origin/main), which ``launch`` runs."""
    if not is_ar(spec):
        raise Stop(f"STOP: the third note binds an autoresearch-only spec ({AR_SCHEMA})")
    note_path = Path(note_path)
    if note_path.parent.as_posix().split("/")[-3:] != NOTE_DIR.split("/") or not AR_NOTE_NAME.fullmatch(note_path.name):
        raise Stop(f"STOP: the note must be {NOTE_DIR}/g1b_ar_t1_tasl_<YYYYMMDD>.md")
    raw = note_path.read_bytes()
    approved = [ln for ln in raw.decode().splitlines() if re.match(r"^approved\s*:", ln)]
    if draft:
        if approved != ["approved: false"]:
            raise Stop("STOP: draft mode is for the unsigned note (exactly one line 'approved: false')")
    elif not (on_main or _note_on_main)(f"{NOTE_DIR}/{note_path.name}", raw):
        raise Stop("STOP: the note is not committed byte-identically on origin/main")
    fields = _note_fields(raw)
    env_row = ROW_ID.match(str((spec.get("env_decision") or {}).get("authority", "")))
    if env_row is None or env_row.group(0) in AR_PLAN_ROWS:
        raise Stop("STOP: the spec's env_decision.authority must name the PLAN row admitting the AR environment "
                   "(not a row the launch already requires)")
    want = {"approved": "false" if draft else "true", "label": ENGINEERING_ONLY, "labels_read": "none",
            "paper_commit": spec["paper"]["commit"], "spec_sha256": L._sha_file(spec_path), "run_id": spec["run_id"],
            "harness_commit": spec["harness"]["commit"], "env_row": env_row.group(0)}
    for key, value in want.items():
        if fields.get(key) != value:
            raise Stop(f"STOP: note field {key} must be {value!r}")
    for key, rx in (("note_rule", AR_RULE_TEXT), ("host_row", re.compile(r"^R1-T1-TASL-ENV(?![A-Za-z0-9-])"))):
        if not rx.match(fields.get(key, "")):
            raise Stop(f"STOP: {key} must cite {rx.pattern[1:].split('(')[0]}")
    open_fields = sorted(k for k, v in fields.items() if re.search(r"<[^>]*>", v) or v.upper().startswith("PENDING"))
    if open_fields:
        raise Stop(f"STOP: note fields not filled (placeholder or PENDING): {open_fields}")
    for key in AR_NOTE_PASS:
        if not fields.get(key, "").upper().startswith(("PASS — ", "PASS - ")):
            raise Stop(f"STOP: {key} is not PASS")
    pin = spec["harness"]["commit"][:8]
    record = (spec["hosts"]["TASL-2"].get("isolation_host_check") or {}).get("record", "")
    cites = dict(AR_NOTE_CITES, P2=(record, pin), P3=("docs/r1/reviews/", pin), P7=(env_row.group(0),))
    for key, needles in cites.items():
        for needle in needles:
            if not needle or needle not in fields[key]:
                raise Stop(f"STOP: {key} must cite {needle!r}")
    return fields


X_NOTE_PASS = ("P1", "P2", "P3", "P4", "P5", "P6", "P7")
X_NOTE_DRAFT_OPEN = ("P2", "P4")        # may read PENDING in the unpublished draft (kit c1 dispositions; this unit's review)
X_NOTE_CITES = {"P1": ("R1-T1-HOST-TASL",), "P2": ("docs/r1/reviews/",), "P3": ("docs/r1/reports/",),
                "P4": ("docs/r1/reviews/",), "P5": ("R1-G1B-EDITS",), "P6": ("R1-G1B-TIMEOUT",), "P7": (X_RULE,)}
X_FUNNEL_NAMES = ("MountainCarContinuous", "AG News")
X_GATE_RX = {"host_check": re.compile(r"host check (docs/r1/reports/\S+?\.md) sha256 ([0-9a-f]{64})"),
             "env_row": re.compile(r"env row (R1-[A-Z0-9][A-Z0-9-]*[A-Z0-9])"),
             "review": re.compile(r"review (docs/r1/reviews/\S+?\.md)"),
             "cpu_determinism": re.compile(r"determinism check (docs/r1/reports/\S+?\.md) sha256 ([0-9a-f]{64})")}


def check_review_record(rel: str, spec_sha256: str, read_main, *, node: str | None = None) -> dict:
    """This unit's independent review record on published main (MAJOR-1 of review round 1): the path the spec names,
    one line ``spec_sha256: <this spec's sha256>``, one line ``verdict: ACCEPTED`` (and no other ``verdict:`` line)
    and, given a node, one line ``cpu_census_disposition: <node> ACCEPTED`` (the review accepts that node's CPU census
    as the census of a CPU G.1b). File existence alone is not enough."""
    if rel != X_REVIEW_RECORD:
        raise Stop(f"STOP: the review cited must be this unit's review record {X_REVIEW_RECORD}, not {rel}")
    raw = read_main(rel)
    if raw is None:
        raise Stop(f"STOP: the review record {rel} is not on published main")
    lines = raw.decode("utf-8", "replace").splitlines()
    shas = [ln for ln in lines if re.match(r"^spec_sha256:", ln)]
    verdicts = [ln for ln in lines if re.match(r"^verdict:", ln)]
    if shas != [f"spec_sha256: {spec_sha256}"]:
        raise Stop(f"STOP: the review record {rel} must carry exactly one line 'spec_sha256: {spec_sha256}' (got {shas})")
    if verdicts != ["verdict: ACCEPTED"]:
        raise Stop(f"STOP: the review record {rel} must carry exactly one line 'verdict: ACCEPTED' (got {verdicts})")
    out = {"record": rel, "spec_sha256": spec_sha256, "verdict": "ACCEPTED"}
    if node is not None:
        disp = [ln for ln in lines if re.match(rf"^cpu_census_disposition:\s*{re.escape(node)}\b", ln)]
        if disp != [f"cpu_census_disposition: {node} ACCEPTED"]:
            raise Stop(f"STOP: the review record {rel} must carry exactly one line "
                       f"'cpu_census_disposition: {node} ACCEPTED' (got {disp})")
        out["cpu_census_disposition"] = "ACCEPTED"
    return out


def check_note_x(note_path: Path, spec_path: Path, *, spec: dict, on_main=None, draft: bool = False,
                 read_main=None) -> dict:
    """The node-expansion G.1b note (R1-T1-NODE-EXPANSION): named ``g1b_x_t1_tasl_<date>.md`` under
    docs/r1/authorizations/, ENGINEERING_ONLY, no labels read, binding the spec's paper commit, the spec file's
    sha256 and run_id; ``publication_row`` citing R1-T1-NODE-EXPANSION (the coordinating chat publishes the note once
    it is independently reviewed and its launch checks pass, without a further author decision; no signer field is
    read), ``note_rule`` the same row, ``host_row`` R1-T1-TASL-ENV; one ``node_<node>`` line per spec node naming its
    harness pin, committed pin and edits manifest; one ``gate_<node>`` line per node reading PASS or PENDING (a PENDING
    gate keeps that node from launching, not the note from being published); the ``funnel`` line naming every
    candidate, screened or not; the ``cutoff`` line (2 Dec 2026: G.5 addendum; later: appendix T2); for each node on
    an R1-TASL2-CPU replacement set, one ``determinism_check_<node>`` line naming the row, the set, the check's record
    and the census baseline's result-channel sha256; P1-P7 PASS, with their citations (P2 and P4 may read PENDING in the
    draft only). No field may hold a ``<…>`` placeholder, and no field other than the gates and the draft's P2/P4 may
    read PENDING.

    In strict mode P4 must cite this unit's review record (``review_record``), and that record on published main must
    bind this spec's sha256 with the verdict ACCEPTED (``check_review_record``).

    ``draft=True`` before publication (exactly one line ``approved: false``; the note need not be on main), then
    strict mode (``approved: true``, byte-identical on origin/main), which ``launch`` runs."""
    if not is_x(spec):
        raise Stop(f"STOP: the node-expansion note binds a node-expansion spec ({X_SCHEMA})")
    note_path = Path(note_path)
    if note_path.parent.as_posix().split("/")[-3:] != NOTE_DIR.split("/") or not X_NOTE_NAME.fullmatch(note_path.name):
        raise Stop(f"STOP: the note must be {NOTE_DIR}/g1b_x_t1_tasl_<YYYYMMDD>.md")
    raw = note_path.read_bytes()
    approved = [ln for ln in raw.decode().splitlines() if re.match(r"^approved\s*:", ln)]
    if draft:
        if approved != ["approved: false"]:
            raise Stop("STOP: draft mode is for the unpublished note (exactly one line 'approved: false')")
    elif not (on_main or _note_on_main)(f"{NOTE_DIR}/{note_path.name}", raw):
        raise Stop("STOP: the note is not committed byte-identically on origin/main")
    fields = _note_fields(raw)
    want = {"approved": "false" if draft else "true", "label": ENGINEERING_ONLY, "labels_read": "none",
            "paper_commit": spec["paper"]["commit"], "spec_sha256": L._sha_file(spec_path), "run_id": spec["run_id"]}
    for key, value in want.items():
        if fields.get(key) != value:
            raise Stop(f"STOP: note field {key} must be {value!r}")
    for key, rx in (("publication_row", X_RULE_TEXT), ("note_rule", X_RULE_TEXT),
                    ("host_row", re.compile(r"^R1-T1-TASL-ENV(?![A-Za-z0-9-])"))):
        if not rx.match(fields.get(key, "")):
            raise Stop(f"STOP: {key} must cite {rx.pattern[1:].split('(')[0]}")
    names = [n["node"] for n in spec["nodes"]]
    stray = sorted(k for k in fields if re.match(r"^(node|gate)_", k) and k.split("_", 1)[1] not in names)
    stray += sorted(k for k in fields if k.startswith("determinism_check_") and
                    k[len("determinism_check_"):] not in [n["node"] for n in spec["nodes"] if n.get("cpu_replacement")])
    if stray:
        raise Stop(f"STOP: note lines for nodes not in the spec (or not on a replacement CPU set): {stray}")
    for n in spec["nodes"]:                # R1-TASL2-CPU: the note names each replacement set's determinism check
        if n.get("cpu_replacement"):
            line = fields.get(f"determinism_check_{n['node']}", "")
            for needle in (X_CPU_ROW, f"cpus {n['cpus']}", n["cpu_replacement"]["determinism_check"]["record"],
                           n["cpu_replacement"]["determinism_check"]["census_baseline_result_channel_sha256"]):
                if needle not in line:
                    raise Stop(f"STOP: determinism_check_{n['node']} must name {needle!r} (the replacement set's "
                               f"fixed-seed determinism check, {X_CPU_ROW})")
    open_ok = {f"gate_{n}" for n in names} | (set(X_NOTE_DRAFT_OPEN) if draft else set())
    placeholder = sorted(k for k, v in fields.items() if re.search(r"<[^>]*>", v))
    pending = sorted(k for k, v in fields.items() if v.upper().startswith("PENDING") and k not in open_ok)
    if placeholder or pending:
        raise Stop(f"STOP: note fields not filled (placeholder or PENDING): {placeholder + pending}")
    for key in X_NOTE_PASS:
        value = fields.get(key, "")
        if not value.upper().startswith(("PASS — ", "PASS - ")) and \
                not (key in open_ok and value.upper().startswith(("PENDING — ", "PENDING - "))):
            raise Stop(f"STOP: {key} is not PASS")
        for needle in X_NOTE_CITES[key]:
            if needle not in value:
                raise Stop(f"STOP: {key} must cite {needle!r}")
    for node in spec["nodes"]:
        line = fields.get(f"node_{node['node']}", "")
        for value in (node["harness"]["commit"], node["committed_pin_sha256"], node["edits_manifest_sha256"]):
            if value not in line:
                raise Stop(f"STOP: node_{node['node']} must name its harness pin, committed pin and edits manifest")
        gate = fields.get(f"gate_{node['node']}", "")
        if not gate.upper().startswith(("PASS — ", "PASS - ", "PENDING — ", "PENDING - ")):
            raise Stop(f"STOP: gate_{node['node']} must read PASS or PENDING")
    funnel = fields.get("funnel", "")
    missing = [n for n in X_FUNNEL_NAMES + tuple(X_NODES) if n not in funnel]
    if missing:
        raise Stop(f"STOP: the funnel line must name every candidate, screened or not: missing {missing}")
    cutoff = fields.get("cutoff", "")
    if not all(s in cutoff for s in ("2 Dec 2026 00:00 CET", "finished_utc", "G.5", "T2")):
        raise Stop("STOP: the cutoff line must state the instant 2 Dec 2026 00:00 CET, the finished_utc it is compared "
                   "with, the G.5 addendum and the appendix T2")
    if not draft:
        if X_REVIEW_RECORD not in fields["P4"]:
            raise Stop(f"STOP: P4 must cite this unit's review record {X_REVIEW_RECORD}")
        fields["_p4_review"] = check_review_record(X_REVIEW_RECORD, want["spec_sha256"], read_main or _read_main)
    return fields


def check_gate_x(spec: dict, node: dict, fields: dict, read_main) -> dict:
    """The launch gate of one node of the node-expansion note: PASS, citing what the spec requires for the node —
    the TASL-2 host check at the node's own harness pin (on main, its sha256, host, pin, items 1-7 PASS, verdict PASS);
    the PLAN row on main that admits the node's environment (once, containing the sentence ``X_ENV_ROW_TEXT``
    verbatim); this unit's review record on main accepting the node's CPU census (``check_review_record`` with the
    node's ``cpu_census_disposition`` line and the note's spec sha256); for a node on an R1-TASL2-CPU replacement set,
    that set's fixed-seed determinism check record on main (``check_determinism_record``). Each check fails closed."""
    key = f"gate_{node['node']}"
    gate = fields.get(key, "")
    if not gate.upper().startswith(("PASS — ", "PASS - ")):
        raise Stop(f"STOP: {key} is not PASS: {node['node']} does not launch ({gate[:160]!r})")
    out = {}
    for req in node["gate_requires"]:
        m = X_GATE_RX[req].search(gate)
        if not m:
            raise Stop(f"STOP: {key} must cite its {req.replace('_', ' ')} ({X_GATE_RX[req].pattern})")
        if req == "host_check":
            host = spec["hosts"][node["host"]]
            out[req] = check_host_record({"hostname": host["hostname"],
                                          "isolation_host_check": {"record": m.group(1), "sha256": m.group(2)}},
                                         node_harness_commit(spec, node), read_main)
        elif req == "env_row":
            plan = (read_main("docs/r1/PLAN.md") or b"").decode("utf-8", "replace")
            lines = [ln for ln in plan.splitlines() if re.match(rf"^\| {re.escape(m.group(1))} \|", ln)]
            if len(lines) != 1 or X_ENV_ROW_TEXT not in lines[0]:
                raise Stop(f"STOP: the PLAN row {m.group(1)} on published main must exist once and contain, verbatim, "
                           f"'{X_ENV_ROW_TEXT}'")
            out[req] = m.group(1)
        elif req == "cpu_determinism":
            out[req] = check_determinism_record(spec, node, m.group(1), m.group(2), read_main)
        else:
            out[req] = check_review_record(m.group(1), fields["spec_sha256"], read_main, node=node["node"])
    return out


def check_determinism_record(spec: dict, node: dict, rel: str, sha256: str, read_main) -> dict:
    """R1-TASL2-CPU: the replacement CPU set of a node passed a fixed-seed determinism check before its first use.
    The record is the one the spec names (``cpu_replacement.determinism_check.record``), on published main with the
    sha256 the gate cites, and carries each line ``determinism_check_<key>: <value>`` exactly once at column 0 (a line
    of that key in another casing or with markup is refused): host TASL-2, the node, its replacement set, its harness
    pin, runs 2, the result-channel sha256 both runs produced (equal to each other and to the census baseline's), the
    two baseline wall times (each at most ``estimate.ratio_sensitivity`` x the census B1) and verdict PASS."""
    chk = node["cpu_replacement"]["determinism_check"]
    if rel != chk["record"]:
        raise Stop(f"STOP: {node['node']}'s determinism check must be the record its spec names, {chk['record']}, "
                   f"not {rel}")
    raw = read_main(rel)
    if raw is None:
        raise Stop(f"STOP: the determinism check record {rel} is not on published main")
    if hashlib.sha256(raw).hexdigest() != sha256:
        raise Stop(f"STOP: the determinism check record {rel} differs from the sha256 its gate cites")
    lines = raw.decode("utf-8", "replace").splitlines()
    want = {"host": spec["hosts"][node["host"]]["hostname"], "node": node["node"], "cpus": node["cpus"],
            "harness_commit": node["harness"]["commit"], "runs": str(chk["runs"]),
            "result_channel_sha256": chk["census_baseline_result_channel_sha256"], "verdict": "PASS"}
    got = {}
    for key in X_DETERMINISM_LINES:
        found = [ln for ln in lines if re.match(rf"^\W*determinism_check_{key}\s*:", ln, re.I)]
        if len(found) != 1 or not found[0].startswith(f"determinism_check_{key}: "):
            raise Stop(f"STOP: the determinism check record {rel} must carry exactly one line "
                       f"'determinism_check_{key}: …' at column 0 (got {found})")
        got[key] = found[0][len(f"determinism_check_{key}: "):]
    bad = {k: got[k] for k, v in want.items() if got[k] != v}
    if bad:
        raise Stop(f"STOP: the determinism check record {rel} does not show a PASS for {node['node']} on cpus "
                   f"{node['cpus']} at its pin reproducing its census baseline: {bad} (want {want})")
    bound = float(spec["estimate"]["ratio_sensitivity"]) * float(node["run_seconds"])
    try:
        secs = [float(x) for x in got["baseline_seconds"].split()]
    except ValueError:
        secs = []
    if len(secs) != chk["runs"] or not all(0 < x <= bound for x in secs):
        raise Stop(f"STOP: the determinism check record {rel} must give {chk['runs']} baseline wall times, each in "
                   f"(0, {f'{bound:.4f}'.rstrip('0').rstrip('.')}] s (ratio_sensitivity x the census B1): got "
                   f"{got['baseline_seconds']!r}")
    return {"record": rel, "sha256": sha256, "cpus": node["cpus"], "baseline_seconds": secs, "verdict": "PASS"}


def check_publication_row(read_main) -> str:
    """R1-T1-NODE-EXPANSION on published main lets the coordinating chat publish the spec and note."""
    plan = (read_main("docs/r1/PLAN.md") or b"").decode("utf-8", "replace")
    lines = [ln for ln in plan.splitlines() if re.match(rf"^\| {re.escape(X_RULE)} \|", ln)]
    if len(lines) != 1 or X_PUBLICATION_TEXT not in lines[0]:
        raise Stop(f"STOP: the PLAN row {X_RULE} on published main must exist once and say that the "
                   f"{X_PUBLICATION_TEXT}")
    return X_RULE


def _note_on_main(rel: str, raw: bytes) -> bool:
    res = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"origin/main:{rel}"], capture_output=True)
    return res.returncode == 0 and res.stdout == raw


def _repo_id(url: str) -> str:
    """owner/name of a GitHub remote, however it is spelled (https, ssh, scp form, with or without .git)."""
    u = url.strip().rstrip("/")
    u = re.sub(r"\.git$", "", u)
    u = re.sub(r"^(?:https?://|ssh://git@|git@)github\.com[:/]", "", u)
    return u.lower()


def _origin_url(repo: Path) -> str:
    """The URL git actually uses for ``origin`` (``insteadOf`` rewrites applied)."""
    return L._git(repo, "remote", "get-url", "origin").stdout.strip()


SYS_PATH_DIRS = ("sweep2/t1_tasl", "sweep2/g1b")      # put first on sys.path by g1b_tasl.py: no stray module may sit there
CODE_SUFFIXES = (".py", ".pyc", ".pyo", ".sh", ".pth", ".so")


def verify_launch_tasl(repo: Path, spec: dict, rows: tuple[str, ...], *, spec_path: Path) -> dict:
    """The TASL launch binding. It replaces ``g1b_lib.verify_launch`` here, whose conditions a note on main naming the
    launch commit cannot meet (the launch commit would have to descend from the main that names it).

    - ``origin`` (as git resolves it, ``insteadOf`` applied) is the spec's paper repository, and ``ls-remote`` equals the local ``origin/main`` (freshly fetched);
    - the checkout is tracked-clean, holds no untracked code file outside ``docs/`` (nor an ignored one, such as a
      sourceless ``.pyc``, in the directories the scripts put on ``sys.path``), and its ``HEAD`` is published:
      an ancestor of, or equal to, ``origin/main``. Main may move on after the signature (no code freeze), and a later
      note for the same run (same paper commit and spec) can launch from the same checkout;
    - the spec file given is ``HEAD``'s committed file (the note binds its sha256 separately);
    - the spec's ``paper.commit`` (which the note names) is an ancestor of ``HEAD`` whose tree equals ``HEAD``'s
      outside ``docs/`` and that one spec file: the code, kits, envs, tests and the other specs are the reviewed ones;
    - the PLAN rows are on ``origin/main`` (the note and the host-check records are read from ``origin/main`` by
      ``check_note`` and ``check_host_record``)."""
    commit = (spec.get("paper") or {}).get("commit")
    if not isinstance(commit, str) or not L.COMMIT.fullmatch(commit):
        raise Stop("STOP: the spec must pin the full paper commit")
    want_repo = (spec.get("paper") or {}).get("repo")
    if want_repo:
        url = _origin_url(repo)
        if _repo_id(url) != _repo_id(want_repo):
            raise Stop(f"STOP: origin ({url or 'unset'}) is not the spec's paper repository {want_repo}")
    remote, local = L._git(repo, "ls-remote", "origin", "refs/heads/main"), L._git(repo, "rev-parse", "origin/main")
    if remote.returncode or local.returncode or remote.stdout.split() != [local.stdout.strip(), "refs/heads/main"]:
        raise Stop("STOP: fetch published main before launch; local origin/main differs or could not be verified")
    main = local.stdout.strip()
    head = L._git(repo, "rev-parse", "HEAD").stdout.strip()
    if L._git(repo, "status", "--porcelain", "-uno").stdout:
        raise Stop("STOP: the launch checkout must be tracked-clean")
    stray = [f for f in L._git(repo, "ls-files", "--others", "--exclude-standard", "--", ".",
                               ":(exclude)docs/").stdout.splitlines() if f.endswith(CODE_SUFFIXES)]
    ignored = L._git(repo, "ls-files", "--others", "--ignored", "--exclude-standard", "--",
                     *SYS_PATH_DIRS).stdout.splitlines()       # e.g. a sourceless .pyc beside the scripts
    stray += [f for f in ignored if f.endswith(CODE_SUFFIXES) and "/__pycache__/" not in f]
    if stray:
        raise Stop(f"STOP: untracked code files in the launch checkout: {stray[:5]}")
    if L._git(repo, "merge-base", "--is-ancestor", head, main).returncode:
        raise Stop("STOP: the launch checkout (HEAD) must be published: an ancestor of the freshly fetched origin/main")
    try:
        rel = Path(spec_path).resolve().relative_to(Path(repo).resolve()).as_posix()
    except ValueError:
        raise Stop("STOP: the launch spec must be the spec file committed in the repository") from None
    shown = subprocess.run(["git", "-C", str(repo), "show", f"HEAD:{rel}"], capture_output=True)
    if shown.returncode or shown.stdout != Path(spec_path).read_bytes():
        raise Stop(f"STOP: the launch spec is not the committed {rel} of HEAD")
    if L._git(repo, "merge-base", "--is-ancestor", commit, head).returncode:
        raise Stop("STOP: the paper commit the note names must be an ancestor of the launch checkout")
    if L._git(repo, "diff", "--quiet", commit, head, "--", ".", ":(exclude)docs/", f":(exclude,literal){rel}").returncode:
        raise Stop(f"STOP: the launch checkout differs from the paper commit outside docs/ and {rel}")
    plan = L._git(repo, "show", "origin/main:docs/r1/PLAN.md").stdout
    for row in rows:
        if not re.search(rf"^\| {re.escape(row)} \|", plan, re.M):
            raise Stop(f"STOP: the PLAN row {row} is not on published main")
    return {"paper_commit": commit, "head": head, "main": main, "spec": rel}


def launch(spec_path: Path, note_path: Path, node_name: str, *, enable: bool, on_main=_note_on_main,
           launch_binding=None, runner=None, read_main=_read_main) -> dict:
    spec = load_spec(spec_path)
    validate_spec(spec, launch=True)
    if is_ar(spec):      # the third note (R1-G1B-NOTE2-DECISIONS NOTE2-AR A): its own spec, run, pin and environment
        check_note_ar(note_path, spec_path, spec=spec, on_main=on_main)
        node_entry(spec, node_name)
        env_row = ROW_ID.match(spec["env_decision"]["authority"]).group(0)
        check_env_row(env_row, read_main)
        rows = AR_PLAN_ROWS + (env_row,)
    elif is_x(spec):     # the node-expansion note (R1-T1-NODE-EXPANSION): published under the row, gated per node
        fields = check_note_x(note_path, spec_path, spec=spec, on_main=on_main, read_main=read_main)
        check_publication_row(read_main)
        rows = X_PLAN_ROWS
    else:
        fields = check_note(note_path, spec_path, spec["paper"]["commit"], on_main=on_main, spec=spec)
        if node_entry(spec, node_name)["host"] == "TASL-7":       # R1-T1-TASL-ENV: the TASL-7 nodes' cross-host check
            p7 = fields.get("P7", "")
            if not p7.upper().startswith(("PASS — ", "PASS - ")) or "R1-T1-TASL-ENV" not in p7:
                raise Stop("STOP: a TASL-7 node needs P7 PASS citing R1-T1-TASL-ENV (the TASL-7 -> TASL-2 cross-host check)")
        rows = PLAN_ROWS + ("R1-T1-TASL-ENV",)
    if not enable or os.environ.get(ENABLE_ENV) != "1":
        raise Stop(f"STOP: real G.1b runs are disabled (needs --enable AND {ENABLE_ENV}=1)")
    if is_x(spec):       # the node's gate: its host check at its own pin, and its environment row or review
        gate = check_gate_x(spec, node_entry(spec, node_name), fields, read_main)
    else:
        for h in spec_hosts(spec):      # R1-T1-HOST-TASL's precondition: G.1b runs workers on these hosts
            check_host_record(spec["hosts"][h], spec["harness"]["commit"], read_main)
        gate = None
    binding = (launch_binding or (lambda repo, s, r: verify_launch_tasl(repo, s, r, spec_path=spec_path)))(
        REPO_ROOT, spec, rows)
    return (runner or run_node_job)(spec_path, node_name) | {"launch": binding} | ({"gate": gate} if gate else {})


# =============================================================================================== CLI
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate"); v.add_argument("spec"); v.add_argument("--launch", action="store_true")
    r = sub.add_parser("run-node"); r.add_argument("spec"); r.add_argument("--node", required=True)
    r.add_argument("--note", required=True); r.add_argument("--enable", action="store_true")
    c = sub.add_parser("cpus"); c.add_argument("spec"); c.add_argument("--node", required=True)
    g = sub.add_parser("logdir"); g.add_argument("spec"); g.add_argument("--node", required=True)
    ca = sub.add_parser("close-attempt"); ca.add_argument("spec"); ca.add_argument("attempt_dir")
    ca.add_argument("--node", required=True); ca.add_argument("--reason", required=True)
    z = sub.add_parser("seal"); z.add_argument("job_dir"); z.add_argument("spec"); z.add_argument("--node", required=True)
    asm = sub.add_parser("assemble"); asm.add_argument("spec"); asm.add_argument("dest"); asm.add_argument("sealed", nargs="+")
    s = sub.add_parser("summarise"); s.add_argument("run_dir"); s.add_argument("spec")
    s.add_argument("--paper-root", required=True)
    n3 = sub.add_parser("check-note-ar"); n3.add_argument("spec"); n3.add_argument("--note", required=True)
    n3.add_argument("--draft", action="store_true")
    nx = sub.add_parser("check-note-x"); nx.add_argument("spec"); nx.add_argument("--note", required=True)
    nx.add_argument("--draft", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "validate":
            loaded = validate_spec(load_spec(Path(a.spec)), launch=a.launch)
            print(json.dumps({"ok": True, "run_id": loaded["run_id"], "projection": loaded["projection"]}, indent=1))
        elif a.cmd == "run-node":
            rec = launch(Path(a.spec), Path(a.note), a.node, enable=a.enable)
            print(json.dumps({"ok": True, "node": a.node, "runs": rec.get("runs")}, indent=1))
        elif a.cmd in ("cpus", "logdir"):
            spec = load_spec(Path(a.spec))
            validate_spec(spec)
            node = node_entry(spec, a.node)
            print(node_cpus(spec, node) if a.cmd == "cpus" else
                  str(Path(spec["hosts"][node["host"]]["runs_root"]) / spec["run_id"] / "_logs"))
        elif a.cmd == "close-attempt":
            spec = load_spec(Path(a.spec))
            node = node_entry(spec, a.node)
            expected = Path(spec["hosts"][node["host"]]["runs_root"]) / spec["run_id"] / a.node
            if Path(a.attempt_dir).resolve().parent != expected.resolve():
                raise Stop(f"STOP: {a.attempt_dir} is not an attempt of {a.node} in this run")
            lease = node_lease(spec, node)
            print(json.dumps(close_attempt(Path(a.attempt_dir), a.reason, lease=lease), indent=1))
        elif a.cmd == "check-note-ar":
            spec = load_spec(Path(a.spec))
            validate_spec(spec, launch=True)
            fields = check_note_ar(Path(a.note), Path(a.spec), spec=spec, draft=a.draft)
            print(json.dumps({"ok": True, "mode": "draft" if a.draft else "strict", "run_id": fields["run_id"],
                              "spec_sha256": fields["spec_sha256"]}, indent=1))
        elif a.cmd == "check-note-x":
            spec = load_spec(Path(a.spec))
            validate_spec(spec, launch=True)
            fields = check_note_x(Path(a.note), Path(a.spec), spec=spec, draft=a.draft)
            print(json.dumps({"ok": True, "mode": "draft" if a.draft else "strict", "run_id": fields["run_id"],
                              "spec_sha256": fields["spec_sha256"],
                              "gates": {n["node"]: fields[f"gate_{n['node']}"].split(" ", 1)[0]
                                        for n in spec["nodes"]}}, indent=1))
        elif a.cmd == "seal":
            print(json.dumps(seal(Path(a.job_dir), load_spec(Path(a.spec)), a.node), indent=1))
        elif a.cmd == "assemble":
            print(json.dumps(assemble([Path(x) for x in a.sealed], load_spec(Path(a.spec)), Path(a.dest),
                                      L._sha_file(Path(a.spec))), indent=1))
        else:
            print(json.dumps(summarise(Path(a.run_dir), load_spec(Path(a.spec)), Path(a.paper_root)), indent=1,
                             default=str))
    except Stop as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
