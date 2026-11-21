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


def projection(spec: dict) -> dict:
    est = spec["estimate"]
    out = {}
    for label, ratio in (("estimate", float(est["ratio_4090_over_ada"])), ("sensitivity", float(est["ratio_sensitivity"]))):
        per_node, per_host = {}, {h: 0.0 for h in HOSTS}
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
    if spec.get("schema") != SCHEMA or spec.get("label") != ENGINEERING_ONLY:
        raise Stop(f"STOP: spec must be {SCHEMA}, ENGINEERING_ONLY")
    run_id = spec.get("run_id")
    if not isinstance(run_id, str) or not L.SAFE.fullmatch(run_id) or run_id in (".", ".."):
        raise Stop("STOP: run_id must be a safe path component")
    for key, repo in (("paper", L.PAPER_REPO), ("harness", L.HARNESS_REPO)):
        block = spec.get(key) or {}
        if block.get("repo") != repo:
            raise Stop(f"STOP: {key}.repo must be {repo}")
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
    est = spec.get("estimate") or {}
    for key, lo, hi in (("ratio_4090_over_ada", 0.5, 3.0), ("ratio_sensitivity", 0.5, 4.0), ("setup_estimate_s", 0, 7200),
                        ("setup_reserve_s", 600, 14400), ("node_wall_factor", 1.5, 4.0)):
        v = est.get(key)
        if not isinstance(v, (int, float)) or isinstance(v, bool) or not lo <= v <= hi:
            raise Stop(f"STOP: estimate.{key} must be in [{lo}, {hi}]")
    if est["ratio_sensitivity"] < est["ratio_4090_over_ada"]:
        raise Stop("STOP: estimate.ratio_sensitivity must be at least the estimate ratio")
    envs = spec.get("envs") or {}
    if not envs or set(envs) - {"torch312", "jax312"}:
        raise Stop("STOP: envs must be torch312 and/or jax312 (the census environments)")
    for name, env in envs.items():
        if env.get("python") != "3.12.16":
            raise Stop(f"STOP: envs.{name}.python must be 3.12.16 (the census Python)")
        L._sha(env.get("sha256"), f"envs.{name}.sha256", allow_placeholder=False)
        freeze = HERE.parent / "g1b" / env.get("freeze", "")
        if not freeze.is_file() or L._sha_file(freeze) != env["sha256"]:
            raise Stop(f"STOP: envs.{name}.freeze must be the committed census freeze with that sha256")
    hosts = spec.get("hosts") or {}
    if set(hosts) != set(HOSTS):
        raise Stop(f"STOP: hosts must be exactly {HOSTS} (R1-T1-HOST-TASL)")
    for h, host in hosts.items():
        for key in ("hostname", "gpu_uuid"):
            if not isinstance(host.get(key), str) or not host[key] or (launch and L._placeholder(host[key])):
                raise Stop(f"STOP: hosts.{h}.{key} must be set (the operator fills it from the host)")
        if not L._placeholder(host["gpu_uuid"]) and not re.fullmatch(r"GPU-[0-9a-f-]{36}", host["gpu_uuid"]):
            raise Stop(f"STOP: hosts.{h}.gpu_uuid must be a full GPU UUID")
        for key in ("base", "harness_dir", "data_root", "runs_root", "sealed_root", "uv"):
            _abs(host.get(key), f"hosts.{h}.{key}")
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
    unknown = set(names) - set(T1_NODES) - set(T1_NODES_LATER)
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
        if node.get("host") not in HOSTS:
            raise Stop(f"STOP: {name}.host must be one of {HOSTS}")
        want_device = "cpu" if name in CPU_ONLY_NODES else "gpu"
        if node.get("device") != want_device:
            raise Stop(f"STOP: {name}.device must be {want_device}")
        if node.get("env") not in envs or node["env"] not in (hosts[node["host"]].get("env_python") or {}):
            raise Stop(f"STOP: {name}.env must be a declared environment present on {node['host']}")
        if not isinstance(node.get("census_record"), str) or not node["census_record"]:
            raise Stop(f"STOP: {name}.census_record must name the census U2 record")
        if "cpus" in node:
            own = set(cpu_list(node["cpus"]))
            if node["device"] != "cpu":
                raise Stop(f"STOP: {name}.cpus: only the CPU-only node has its own cpuset")
            if own & set(cpu_list(hosts[node["host"]]["cpus"])):
                raise Stop(f"STOP: {name}.cpus overlaps the cpus of {node['host']}'s GPU jobs")
    census = spec.get("census") or {}
    L._commit(census.get("commit"), "census.commit", allow_placeholder=False)
    L._sha(census.get("report_sha256"), "census.report_sha256", allow_placeholder=False)
    proj = projection(spec)
    if not proj["within_cap"]:
        raise Stop(f"STOP: projected {proj['estimate']['total_gpu_hours']} GPU-h exceeds the R1-G1B-CAP "
                   f"{proj['cap_total_gpu_hours']} GPU-h: author STOP")
    return {"spec": spec, "run_id": run_id, "projection": proj, "n_edits": n_edits}


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


def harness_checkout(spec: dict, host_name: str, git=_sh) -> dict:
    root = spec["hosts"][host_name]["harness_dir"]
    head = git(["git", "-C", root, "rev-parse", "HEAD"]).stdout.strip()
    if head != spec["harness"]["commit"]:
        raise Stop(f"STOP: the harness checkout {root} is at {head!r}, not the pin {spec['harness']['commit']}")
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
    got = sh([host["uv"], "pip", "freeze", "--python", python])
    if got.returncode != 0:
        raise Stop(f"STOP: uv pip freeze failed for {python}: {got.stderr.strip()[:200]}")
    have = L.compare_freeze(got.stdout, freeze.read_text(), node["env"])
    version = sh([python, "-c", "import sys; print(sys.version.split()[0])"]).stdout.strip()
    if version != spec["envs"][node["env"]]["python"]:
        raise Stop(f"STOP: {python} is Python {version}, not {spec['envs'][node['env']]['python']}")
    return {"name": node["env"], "python": python, "python_version": version,
            "freeze_sha256": spec["envs"][node["env"]]["sha256"], "packages": len(have)}


@contextlib.contextmanager
def gpu_lease(path: str):
    """An exclusive, non-blocking flock on the host's lease file for the whole job; a busy lease is a STOP."""
    lease = Path(os.path.expanduser(path))
    lease.parent.mkdir(parents=True, exist_ok=True)
    fh = lease.open("a+")
    try:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Stop(f"STOP: the GPU lease {lease} is held by another job (no shared card)") from None
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
                         f"the 4090 ({timeouts[:3]}): the census timing does not carry over (author decides)")
    walls = sorted(float(r["wall_seconds"]) for r in rows if r.get("config") == "c0" and r.get("wall_seconds"))
    median = walls[len(walls) // 2] if walls else None
    return {"part": part, "c0_median_wall_s": median,
            "ratio_4090_over_ada": round(median / float(node["run_seconds"]), 4) if median else None,
            "max_wall_s": max((float(r["wall_seconds"]) for r in rows if r.get("wall_seconds")), default=None)}


def preflight(spec: dict, node: dict, smi=_sh) -> dict:
    """Every host check that needs no output directory (run under the lease, before an attempt is created)."""
    host_name = node["host"]
    gpu = None if node["device"] == "cpu" else spec["hosts"][host_name]["gpu_uuid"]
    out = {"host": host_identity(spec, host_name), "affinity": check_affinity(spec, node),
           "gpu": gpu_check(spec, host_name, smi) if gpu else {"device": "cpu"},
           "foreign_before": check_no_foreign(gpu, "before the job", smi),
           "ptrace_scope": ptrace_scope(), "cgroup": scope_cgroup(), "harness": harness_checkout(spec, host_name),
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
                    "spec_sha256": L._sha_file(spec_path), "harness_commit": spec["harness"]["commit"],
                    "device": node["device"], "parts": [], "timing": [], "foreign_checks": [], "stop": None,
                    "stop_class": None, "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
                    "node_log": node_log,
                    "timeout_basis": {"decision": spec["timeout_decision"]["basis"],
                                      "seconds": timeout_basis(spec, node), "timeout_s": 3 * timeout_basis(spec, node)},
                    "output_use": "ENGINEERING_ONLY G.1b noise floor (D21) on the TASL pair; no labels read",
                    "deadline_s": node_wall_limit(spec, node),
                    "projection": loaded["projection"]["estimate"]["per_node"][node_name]}
    deadline = started + node_wall_limit(spec, node)
    lease_cm = gpu_lease(host["lease"]) if gpu else contextlib.nullcontext({"lease": None})
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
            harness = Path(host["harness_dir"])
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
                chunk = chunk_file(spec, node, part, interpreter=host["env_python"][node["env"]],
                                   cgroup_parent=record["cgroup"]["cgroup_parent"], deadline=deadline)
                chunk_path = out / f"chunk_{part[0]}.json"
                chunk_path.write_text(json.dumps(chunk, indent=1) + "\n")
                remaining = int(deadline - time.time())
                if remaining < 60:
                    raise Stop(f"STOP: the node deadline was reached before part {part[0]}")
                argv = [host["env_python"][node["env"]], "-m", "autoresearch.trackg.noise_floor", "--chunk",
                        str(chunk_path), "--harness-root", str(harness), "--out", str(out / part[0])]
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
                                     "timing does not carry over to the 4090 (author decides)")
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
            ("harness_commit", record.get("harness_commit") == spec["harness"]["commit"]),
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
    manifest = {"schema": ASSEMBLY_SCHEMA, "run_id": spec["run_id"], "jobs": jobs,
                "spec_json_sha256": hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest(),
                "runs_sha256": L._sha_file(dest / "runs.jsonl")}
    (dest / "ASSEMBLY.json").write_text(json.dumps(manifest, indent=1) + "\n")
    return manifest


def summarise(run_dir: Path, spec: dict, paper_root: Path) -> dict:
    """The D21 verdicts (``g1b_lib.summarise``: exact coverage, the gate, determinism, the pinned e1_report rule and its
    independent double check), relabelled for the TASL table with the hosts and the 4090 timing per node."""
    summary = L.summarise(run_dir, spec, paper_root)
    assembly = json.loads((Path(run_dir) / "ASSEMBLY.json").read_text())
    summary.update(schema=SUMMARY_SCHEMA, gpu_model=GPU_MODEL, hosts={j["node"]: j["host"] for j in assembly["jobs"]},
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


def _note_on_main(rel: str, raw: bytes) -> bool:
    res = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"origin/main:{rel}"], capture_output=True)
    return res.returncode == 0 and res.stdout == raw


def _repo_id(url: str) -> str:
    """owner/name of a GitHub remote, however it is spelled (https, ssh, scp form, with or without .git)."""
    u = url.strip().rstrip("/")
    u = re.sub(r"\.git$", "", u)
    u = re.sub(r"^(?:https?://|ssh://git@|git@)github\.com[:/]", "", u)
    return u.lower()


def verify_launch_tasl(repo: Path, spec: dict, rows: tuple[str, ...], *, spec_path: Path) -> dict:
    """The TASL launch binding. It replaces ``g1b_lib.verify_launch`` here, whose conditions a note on main naming the
    launch commit cannot meet (the launch commit would have to descend from the main that names it).

    - ``origin`` is the spec's paper repository, and ``ls-remote`` equals the local ``origin/main`` (freshly fetched);
    - the checkout is tracked-clean, holds no untracked code file outside ``docs/``, and its ``HEAD`` is published:
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
        url = L._git(repo, "config", "--get", "remote.origin.url").stdout.strip()
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
                               ":(exclude)docs/").stdout.splitlines() if f.endswith((".py", ".sh", ".pth", ".so"))]
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
    if L._git(repo, "diff", "--quiet", commit, head, "--", ".", ":(exclude)docs/", f":(exclude){rel}").returncode:
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
    fields = check_note(note_path, spec_path, spec["paper"]["commit"], on_main=on_main, spec=spec)
    if node_entry(spec, node_name)["host"] == "TASL-7":       # R1-T1-TASL-ENV: the TASL-7 nodes' cross-host check
        p7 = fields.get("P7", "")
        if not p7.upper().startswith(("PASS — ", "PASS - ")) or "R1-T1-TASL-ENV" not in p7:
            raise Stop("STOP: a TASL-7 node needs P7 PASS citing R1-T1-TASL-ENV (the TASL-7 -> TASL-2 cross-host check)")
    if not enable or os.environ.get(ENABLE_ENV) != "1":
        raise Stop(f"STOP: real G.1b runs are disabled (needs --enable AND {ENABLE_ENV}=1)")
    for h in HOSTS:      # R1-T1-HOST-TASL's precondition: G.1b runs workers on both hosts
        check_host_record(spec["hosts"][h], spec["harness"]["commit"], read_main)
    rows = PLAN_ROWS + ("R1-T1-TASL-ENV",)
    binding = (launch_binding or (lambda repo, s, r: verify_launch_tasl(repo, s, r, spec_path=spec_path)))(
        REPO_ROOT, spec, rows)
    return (runner or run_node_job)(spec_path, node_name) | {"launch": binding}


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
            lease = spec["hosts"][node["host"]]["lease"] if node["device"] == "gpu" else None
            print(json.dumps(close_attempt(Path(a.attempt_dir), a.reason, lease=lease), indent=1))
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
