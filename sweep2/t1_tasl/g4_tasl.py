"""G.4 T1 pilot on the TASL pair (R1-T1-HOST-TASL): worker on TASL-2, proposer llama-server on TASL-7 over Tailscale.

ENGINEERING_ONLY; AI-assisted (Claude). Replaces the HTCondor job of ``sweep2/g4/`` (one job carrying both the server
and the worker on NEMO2 H200). The pilot itself is unchanged (R1-TRACKG-G3-EARLY: ``mlab_cifar10``, ``mlgym_fmnist``
and ``autoresearch_fixedtokens``, or ``mlgym_breakout_minatar`` while autoresearch is not ready; 3 instances x W = 20
manager calls; ``manager_proposal/v2-diff``; completion cap 4,096; temperature 0.2; ``cache_prompt: false``; seeds
4001-4099); what changes is where the two halves run:

* **Proposer (``serve``, on TASL-7).** Holds TASL-7's GPU lease (``~/r1_locks/gpu0.lock``) for its whole life, checks
  that no other compute process is on the GPU, checks the llama-server binary, its whole build directory (a sha256
  manifest: the executable and its shared libraries) and ``ldd`` resolution, and the pinned GGUF by sha256, starts
  ``llama-server`` with the exam settings (``-c 32768 -ngl 999 -np 1 --jinja --chat-template-kwargs
  {"enable_thinking":false} --cache-type-k q8_0 --cache-type-v q8_0 --no-webui``) bound to the Tailscale address of
  the spec, and writes ``server_record.json`` (argv, binary and model sha256, ``--version`` build line, GPU, start
  time). While it serves, G.1b cannot use TASL-7's GPU (the lease).
* **Worker (``run-node``, on TASL-2).** The host checks of G.1b (``g1b_tasl``: host, RTX 4090 by full UUID, lease,
  ptrace_scope, the delegated scope, harness at the pin and clean, the census freeze, the node's data), then the
  server identity over Tailscale: ``/health`` ok and ``/props`` (context 32,768, one slot, the expected build, the
  pinned GGUF file name), equal before and after the pilot, and the copied ``server_record.json`` agreeing with the
  spec. A latency probe (``/health`` round trips) runs before and after; per-call latency (the pilot's
  ``wall_seconds`` per manager call) is reported as median, p95 and max. Then ``python -m
  autoresearch.trackg.pilot_g4 run --gpu-uuid <TASL-2 UUID>``. Started by ``t1_tasl_node.sh g4`` (the census scope,
  the CPU affinity, a fresh log). As in G.1b, the lease and every check run before anything is written for the node
  (a refusal goes to ``<run_id>/_refusals/``), then ``<node>/attempt-N/``; only an infrastructure STOP may be
  followed by another attempt, and at launch TASL-2's host check report must be on published ``main`` and PASS.
* **Launch.** ``serve`` (``serve_launch``) and ``run-node`` (``launch``) each need the author-signed note
  ``docs/r1/authorizations/g4_t1_tasl_<YYYYMMDD>.md`` on published ``main`` (P1-P5 PASS; binding the paper commit, the
  spec sha256, the spec's run_id and its harness commit; P3 citing a signed G.1b note, worded per decision G4-ORDER;
  P4's review files on main; no ``<…>`` placeholder left), both keys (``--enable`` and ``G4_TASL_ENABLE_REAL=1``),
  the import-source check, and the TASL launch binding ``g1b_tasl.verify_launch_tasl`` with ``PLAN_ROWS`` (decision
  G4-LB: R1-G1B-TASL-DECISIONS LB A applied to G.4; launch from a published checkout, at or after the commit that
  publishes the note and the spec, whose code equals the note's ``paper_commit`` outside ``docs/`` and the spec).
  ``g1b_lib.verify_launch`` is not used: a note on main naming the launch commit cannot meet it. ``serve`` writes
  nothing for the run before the lease is held and its checks pass (a refusal goes to ``<run_id>/_refusals/``), so a
  refused server can be started again; each started server has its own ``<run_id>/server-N/``.
* **Timing.** The pilot's timeout is 3 x the declared G.1b timeout basis (R1-G1B-TIMEOUT; the same basis for the
  whole T1 table). A pilot run median on the 4090 above that basis is a STOP (``stop_class: timing``).
* **Dates.** ``dates`` recomputes R1-BX-D14 with ``g4_lib.recompute_dates`` from the sealed TASL summaries, with **one
  concurrent worker slot** (TASL-2's GPU; TASL-7's GPU serves the proposer for the whole G.5 table), the seven passed
  census nodes (``mlgym_houseprice`` joins under R1-TRACKG-G3-EARLY: its U2 passed in the U4 census), and the ratio
  relabelled as RTX 4090 over the census (RTX 6000 Ada).
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tarfile
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "g4"))
import g1b_tasl as G  # noqa: E402
import g4_lib  # noqa: E402

L = G.L
Stop, NodeStop, TimingStop = G.Stop, G.NodeStop, G.TimingStop
SCHEMA = "g4_tasl_pilot/v1"
RECORD_SCHEMA = "g4_tasl_job_record/1"
SERVER_RECORD_SCHEMA = "g4_tasl_server_record/1"
RECEIPT_SCHEMA = "g4_tasl_seal_receipt/1"
ENGINEERING_ONLY = G.ENGINEERING_ONLY
GPU_MODEL = G.GPU_MODEL
WORKER_HOST, PROPOSER_HOST = "TASL-2", "TASL-7"
MODEL = g4_lib.MODEL
W, MAX_TOKENS, TEMPERATURE, MEMORY_MODES = g4_lib.W, g4_lib.MAX_TOKENS, g4_lib.TEMPERATURE, g4_lib.MEMORY_MODES
CORE_NODES, THIRD_NODE = g4_lib.CORE_NODES, g4_lib.THIRD_NODE
CAP_PILOT_GPU_HOURS = g4_lib.CAP_PILOT_GPU_HOURS
CTX = 32768
SERVER_ARGS = ["-c", str(CTX), "-ngl", "999", "-np", "1", "--jinja", "--chat-template-kwargs",
               '{"enable_thinking":false}', "--cache-type-k", "q8_0", "--cache-type-v", "q8_0", "--no-webui"]
TAILSCALE_HOST = re.compile(r"^(100\.(6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}|[a-z0-9-]+\.[a-z0-9-]+\.ts\.net)$")
PROBES = 20
PLAN_ROWS = ("R1-T1-HOST-TASL", "R1-TRACKG-G3-EARLY", "R1-G1B-TIMEOUT", "R1-T1-TASL-ENV")
ENABLE_ENV = "G4_TASL_ENABLE_REAL"
NOTE_DIR = "docs/r1/authorizations"
NOTE_NAME = re.compile(r"^g4_t1_tasl_\d{8}\.md$")


# =============================================================================================== spec
def load_spec(path: Path) -> dict:
    return json.loads(Path(path).read_text())


def g1b_spec() -> dict:
    return json.loads((HERE / "g1b_tasl_spec.json").read_text())


def timeout_basis(spec: dict, node: dict) -> float:
    return float(node[G.TIMEOUT_BASES[spec["timeout_decision"]["basis"]]])


def walltime(spec: dict, node: dict) -> int:
    pilot, layout = spec["pilot"], spec["layout"]
    calls = len(pilot["instances"]) * (pilot["budget"] + 1)
    return int(layout["startup_reserve_s"]) + int(math.ceil(
        calls * (float(node["run_seconds"]) + float(layout["llm_seconds_estimate"])) * 1.5))


def projection(spec: dict) -> dict:
    """GPU-hours of the pilot: the worker GPU for the campaign time, and the proposer GPU for the same span."""
    pilot, layout = spec["pilot"], spec["layout"]
    per = {}
    for node in spec["nodes"]:
        calls = len(pilot["instances"]) * (pilot["budget"] + 1)
        span_h = (calls * (float(node["run_seconds"]) + float(layout["llm_seconds_estimate"]))
                  + float(layout["startup_estimate_s"])) / 3600.0
        per[node["node"]] = {"campaign_steps": calls, "span_hours": round(span_h, 3),
                             "gpu_hours": round(2 * span_h, 3), "deadline_s": walltime(spec, node)}
    return {"per_node": per, "total_gpu_hours": round(sum(v["gpu_hours"] for v in per.values()), 3),
            "gpu_hours_basis": "worker GPU (TASL-2) + proposer GPU (TASL-7) over each node's span",
            "proposals_total": len(spec["nodes"]) * len(pilot["instances"]) * pilot["budget"]}


def server_url_parts(url: str) -> tuple[str, int]:
    u = urllib.parse.urlsplit(url or "")
    if u.scheme != "http" or not u.hostname or not u.port or u.path not in ("", "/") or u.query or u.username:
        raise Stop("STOP: proposer.server_url must be http://<tailscale address>:<port>")
    if not TAILSCALE_HOST.fullmatch(u.hostname):
        raise Stop("STOP: proposer.server_url must use a Tailscale address (100.64.0.0/10 or <name>.<tailnet>.ts.net)")
    return u.hostname, u.port


def validate_spec(spec: dict, *, launch: bool = False) -> dict:
    allow = not launch
    if spec.get("schema") != SCHEMA or spec.get("label") != ENGINEERING_ONLY:
        raise Stop(f"STOP: spec must be {SCHEMA}, ENGINEERING_ONLY")
    run_id = spec.get("run_id")
    if not isinstance(run_id, str) or not L.SAFE.fullmatch(run_id) or run_id in (".", ".."):
        raise Stop("STOP: run_id must be a safe path component")
    g1b = g1b_spec()
    for key, repo in (("paper", L.PAPER_REPO), ("harness", L.HARNESS_REPO)):
        if (spec.get(key) or {}).get("repo") != repo:
            raise Stop(f"STOP: {key}.repo must be {repo}")
        L._commit((spec.get(key) or {}).get("commit"), f"{key}.commit", allow_placeholder=allow)
    if spec["harness"]["commit"] != g1b["harness"]["commit"] or spec.get("envs") != g1b["envs"]:
        raise Stop("STOP: harness.commit and envs must equal g1b_tasl_spec.json (one harness pin for the T1 table)")
    if spec.get("gpu_model") != GPU_MODEL:
        raise Stop(f"STOP: gpu_model must be {GPU_MODEL} (one GPU model for the table)")
    if spec.get("model") != MODEL:
        raise Stop("STOP: model must be the pinned gemma4_31b GGUF (R1-EXAM-X7 pick)")
    if (spec.get("timeout_decision") or {}).get("basis") != g1b["timeout_decision"]["basis"]:
        raise Stop("STOP: timeout_decision.basis must equal the G.1b basis (R1-G1B-TIMEOUT, one basis per table)")
    worker = spec.get("worker") or {}
    if worker.get("host") != WORKER_HOST:
        raise Stop("STOP: worker.host must be TASL-2 (R1-T1-HOST-TASL)")
    shim = {"hosts": {WORKER_HOST: worker}}
    for key in ("hostname", "gpu_uuid"):
        if not isinstance(worker.get(key), str) or not worker[key] or (launch and L._placeholder(worker[key])):
            raise Stop(f"STOP: worker.{key} must be set")
    if not L._placeholder(worker["gpu_uuid"]) and not re.fullmatch(r"GPU-[0-9a-f-]{36}", worker["gpu_uuid"]):
        raise Stop("STOP: worker.gpu_uuid must be a full GPU UUID")
    for key in ("base", "harness_dir", "runs_root", "sealed_root", "uv"):
        G._abs(worker.get(key), f"worker.{key}")
    if worker.get("lease") != "~/r1_locks/gpu0.lock":
        raise Stop("STOP: worker.lease must be ~/r1_locks/gpu0.lock")
    G.cpu_list(worker.get("cpus", ""))
    check = worker.get("isolation_host_check") or {}
    L._sha(check.get("sha256"), "worker.isolation_host_check.sha256", allow_placeholder=allow)
    if worker.get("hostname") != g1b["hosts"][WORKER_HOST]["hostname"] or \
            worker.get("gpu_uuid") != g1b["hosts"][WORKER_HOST]["gpu_uuid"]:
        raise Stop("STOP: the worker is TASL-2 with the RTX 4090 of g1b_tasl_spec.json (one GPU model for the table)")
    prop = spec.get("proposer") or {}
    if prop.get("host") != PROPOSER_HOST:
        raise Stop("STOP: proposer.host must be TASL-7 (R1-T1-HOST-TASL)")
    for key in ("hostname", "gpu_uuid", "server_url", "binary_sha256", "expected_build", "tailscale_address"):
        if not isinstance(prop.get(key), str) or not prop[key] or (launch and L._placeholder(prop[key])):
            raise Stop(f"STOP: proposer.{key} must be set")
    if not L._placeholder(prop["server_url"]):
        host, _ = server_url_parts(prop["server_url"])
        if host != prop["tailscale_address"]:
            raise Stop("STOP: proposer.server_url must use proposer.tailscale_address")
    L._sha(prop["binary_sha256"], "proposer.binary_sha256", allow_placeholder=allow)
    L._sha(prop.get("bin_dir_manifest_sha256"), "proposer.bin_dir_manifest_sha256", allow_placeholder=allow)
    if not L._placeholder(prop["expected_build"]):
        props_build(prop["expected_build"])
    for key in ("binary", "model_path", "run_dir"):
        G._abs(prop.get(key), f"proposer.{key}")
    if Path(prop["model_path"]).name != Path(urllib.parse.urlsplit(MODEL["url"]).path).name:
        raise Stop("STOP: proposer.model_path must keep the pinned GGUF file name")
    if prop.get("lease") != "~/r1_locks/gpu0.lock":
        raise Stop("STOP: proposer.lease must be ~/r1_locks/gpu0.lock (the server holds TASL-7's GPU)")
    if prop.get("args") != SERVER_ARGS:
        raise Stop(f"STOP: proposer.args must be the exam settings {SERVER_ARGS}")
    pilot = spec.get("pilot") or {}
    if pilot.get("proposal_schema") != "manager_proposal/v2-diff" or pilot.get("cache_prompt") is not False:
        raise Stop("STOP: pilot.proposal_schema must be manager_proposal/v2-diff and cache_prompt false")
    for key, want in (("budget", W), ("max_tokens", MAX_TOKENS), ("temperature", TEMPERATURE)):
        if pilot.get(key) != want:
            raise Stop(f"STOP: pilot.{key} must be {want}")
    if pilot.get("memory_mode") not in MEMORY_MODES:
        raise Stop(f"STOP: pilot.memory_mode must be one of {MEMORY_MODES}")
    instances = pilot.get("instances")
    if not isinstance(instances, list) or len(instances) != 3:
        raise Stop("STOP: the pilot has three campaign instances per node")
    triples = set()
    for inst in instances:
        if not isinstance(inst, dict) or set(inst) != {"train_seed", "split_seed", "manager_seed"}:
            raise Stop("STOP: a pilot instance has exactly train_seed, split_seed and manager_seed")
        if any(type(inst[k]) is not int or not 4001 <= inst[k] <= 4099 for k in inst):
            raise Stop("STOP: pilot seeds must be in the pilot block 4001-4099")
        triples.add(tuple(inst.values()))
    if len(triples) != 3:
        raise Stop("STOP: pilot instances must have distinct seed triples")
    nodes = spec.get("nodes")
    if not isinstance(nodes, list) or len(nodes) != 3:
        raise Stop("STOP: the pilot has exactly three nodes")
    names = [n.get("node") for n in nodes]
    if names[:2] != list(CORE_NODES) or names[2] not in THIRD_NODE:
        raise Stop(f"STOP: pilot nodes must be {CORE_NODES} + one of {THIRD_NODE} (R1-TRACKG-G3-EARLY)")
    if names[2] == "mlgym_breakout_minatar" and not str(spec.get("third_node_reason", "")).strip():
        raise Stop("STOP: Breakout replaces autoresearch only with third_node_reason (autoresearch not ready)")
    g1b_nodes = {n["node"]: n for n in g1b["nodes"]}
    for node in nodes:
        ref = g1b_nodes.get(node["node"])
        if ref is None:
            raise Stop(f"STOP: {node['node']} is not in g1b_tasl_spec.json (its noise floor comes first)")
        for key in ("spec_path", "node_dir", "node_spec_sha256", "committed_pin_sha256", "data_manifest_sha256",
                    "run_seconds", "slowest_census_seconds", "env", "census_record"):
            if node.get(key) != ref.get(key):
                raise Stop(f"STOP: {node['node']}.{key} differs from g1b_tasl_spec.json")
        if node["env"] not in (worker.get("env_python") or {}):
            raise Stop(f"STOP: {node['node']} needs {node['env']} on TASL-2 (worker.env_python)")
        G._abs(worker["env_python"][node["env"]], f"worker.env_python.{node['env']}")
    layout = spec.get("layout") or {}
    for key, lo, hi in (("startup_reserve_s", 600, 7200), ("startup_estimate_s", 60, 7200),
                        ("llm_seconds_estimate", 5, 600)):
        if type(layout.get(key)) is not int or not lo <= layout[key] <= hi:
            raise Stop(f"STOP: layout.{key} must be an integer in [{lo}, {hi}]")
    cap = (spec.get("caps") or {}).get("max_total_gpu_hours")
    if not isinstance(cap, (int, float)) or not 0 < cap <= CAP_PILOT_GPU_HOURS:
        raise Stop(f"STOP: caps.max_total_gpu_hours must be in (0, {CAP_PILOT_GPU_HOURS}]")
    proj = projection(spec)
    if proj["total_gpu_hours"] > cap:
        raise Stop(f"STOP: the pilot projects {proj['total_gpu_hours']} GPU-h > cap {cap}")
    if launch:
        for key, row in (("timeout_decision", "R1-G1B-TIMEOUT"), ("host_decision", "R1-T1-TASL-ENV")):
            if not str((spec.get(key) or {}).get("authority", "")).startswith(row):
                raise Stop(f"STOP: {key}.authority must name the PLAN row {row} before launch")
    return {"spec": spec, "run_id": run_id, "projection": proj, "shim": shim}


def node_entry(spec: dict, name: str) -> dict:
    for node in spec["nodes"]:
        if node["node"] == name:
            return node
    raise Stop(f"STOP: {name} is not a pilot node")


def worker_shim(spec: dict) -> dict:
    """The worker in the shape the shared host checks of ``g1b_tasl`` read."""
    return {"hosts": {WORKER_HOST: spec["worker"]}, "harness": spec["harness"], "envs": spec["envs"]}


def pilot_file(spec: dict, node: dict, *, interpreter: str, cgroup_parent: str) -> dict:
    p = spec["pilot"]
    return {"schema": "trackg_g4_pilot/v1", "label": ENGINEERING_ONLY, "node": node["node"],
            "spec_path": node["spec_path"], "node_dir": node["node_dir"],
            "node_spec_sha256": node["node_spec_sha256"], "committed_pin_sha256": node["committed_pin_sha256"],
            "data_manifest_sha256": node["data_manifest_sha256"],
            "proposal_schema": "manager_proposal/v2-diff", "extra_payload": {"cache_prompt": False},
            "budget": p["budget"], "instances": [{"instance": i, **inst} for i, inst in enumerate(p["instances"], 1)],
            "measured_run_seconds": timeout_basis(spec, node), "base_url": spec["proposer"]["server_url"],
            "model": MODEL["alias"], "max_tokens": p["max_tokens"], "temperature": p["temperature"],
            "memory_mode": p["memory_mode"], "cgroup_parent": cgroup_parent, "interpreter": interpreter,
            "memory_limit": f"external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 "
                            f"(delegated scope {cgroup_parent})", "isolation_waivers": {}}


# =============================================================================================== proposer (TASL-7)
def server_argv(spec: dict, port: int) -> list[str]:
    prop = spec["proposer"]
    return [prop["binary"], "-m", prop["model_path"], "--alias", MODEL["alias"], *SERVER_ARGS,
            "--host", prop["tailscale_address"], "--port", str(port)]


def _sha_stream(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 24), b""):
            h.update(block)
    return h.hexdigest()


LLAMA_LIBS = re.compile(r"^\s*(lib(?:llama|ggml|mtmd)[^\s]*)\s+=>\s+(\S+)")


def ldd_outside(lines: list[str], bin_dir: Path) -> list[str]:
    """The llama.cpp libraries (libllama*, libggml*, libmtmd*) that ldd resolves outside the build directory."""
    out = []
    root = Path(bin_dir).resolve()
    for line in lines:
        m = LLAMA_LIBS.match(line)
        if m and Path(m.group(2)).resolve().parent != root:
            out.append(f"{m.group(1)} => {m.group(2)}")
    return out


def bin_manifest(bin_dir: Path) -> tuple[str, str]:
    """A manifest of the llama-server build directory (the executable and the shared libraries it loads, e.g.
    libggml-cuda.so): one line per entry, sorted, "<sha256>  <name>" for a regular file and "link  <name> -> <target>"
    for a symlink; returns (text, sha256 of the text). Subdirectories are refused."""
    lines = []
    for p in sorted(Path(bin_dir).iterdir(), key=lambda q: q.name):
        if p.is_symlink():
            lines.append(f"link  {p.name} -> {os.readlink(p)}")
        elif p.is_file():
            lines.append(f"{_sha_stream(p)}  {p.name}")
        else:
            raise Stop(f"STOP: {p} in the llama-server build directory is not a regular file or symlink")
    text = "\n".join(lines) + "\n"
    return text, hashlib.sha256(text.encode()).hexdigest()


def server_attempt(run_root: Path) -> Path:
    """The next ``server-N`` directory under the run's proposer root, created (never reused)."""
    run_root = Path(run_root)
    run_root.mkdir(parents=True, exist_ok=True)
    taken = [int(p.name.split("-", 1)[1]) for p in run_root.glob("server-*") if p.name.split("-", 1)[1].isdigit()]
    d = run_root / f"server-{(max(taken) + 1) if taken else 1}"
    d.mkdir(exist_ok=False)
    return d


def serve(spec_path: Path, *, smi=G._sh, popen=subprocess.Popen, sha=_sha_stream, manifest=bin_manifest,
          wait=True) -> dict:
    """On TASL-7: under the GPU lease, check the binary and the GGUF, start llama-server with the exam settings on the
    Tailscale address, write server_record.json, and serve until stopped (SIGTERM/SIGINT); the record's end fields are
    written on exit.

    Nothing is created for the run before the lease is held and every check has passed: a refusal is written under
    ``<run_dir>/<run_id>/_refusals/`` and the STOP stands, so a later ``serve`` can start once the cause is gone (a busy
    lease, a foreign process). A started server gets a new ``<run_dir>/<run_id>/server-N/`` with its record and log."""
    spec = load_spec(spec_path)
    validate_spec(spec, launch=True)
    prop = spec["proposer"]
    if socket.gethostname() != prop["hostname"]:
        raise Stop(f"STOP: this is not {PROPOSER_HOST} ({prop['hostname']!r})")
    _, port = server_url_parts(prop["server_url"])
    run_root = Path(prop["run_dir"]) / spec["run_id"]
    record: dict = {"schema": SERVER_RECORD_SCHEMA, "label": ENGINEERING_ONLY, "run_id": spec["run_id"],
                    "host": PROPOSER_HOST, "hostname": socket.gethostname(), "server_url": prop["server_url"],
                    "spec_sha256": L._sha_file(spec_path)}
    try:
        with G.gpu_lease(prop["lease"]) as held:
            record["lease"] = held
            server_env = {k: v for k, v in os.environ.items() if k not in ("LD_LIBRARY_PATH", "LD_PRELOAD")}
            shim = {"hosts": {PROPOSER_HOST: prop}}
            record["gpu"] = G.gpu_check(shim, PROPOSER_HOST, smi)
            record["foreign_before"] = G.check_no_foreign(prop["gpu_uuid"], "before the server", smi)
            record["binary_sha256"] = sha(Path(prop["binary"]))
            if record["binary_sha256"] != prop["binary_sha256"]:
                raise Stop("STOP: llama-server sha256 differs from proposer.binary_sha256")
            manifest_text, record["bin_dir_manifest_sha256"] = manifest(Path(prop["binary"]).parent)
            if record["bin_dir_manifest_sha256"] != prop["bin_dir_manifest_sha256"]:
                raise Stop("STOP: the llama-server build directory differs from proposer.bin_dir_manifest_sha256")
            ldd = smi(["ldd", prop["binary"]], env=server_env)
            record["ldd"] = (ldd.stdout or "").splitlines()
            if ldd.returncode != 0 or any("not found" in line for line in record["ldd"]):
                raise Stop("STOP: ldd cannot resolve every library of llama-server")
            record["ldd_outside_bin_dir"] = ldd_outside(record["ldd"], Path(prop["binary"]).parent)
            if record["ldd_outside_bin_dir"]:
                raise Stop(f"STOP: llama.cpp libraries resolve outside the manifested build directory: "
                           f"{record['ldd_outside_bin_dir']}")
            record["server_env"] = {"LD_LIBRARY_PATH": None, "LD_PRELOAD": None,
                                    "CUDA_VISIBLE_DEVICES": server_env.get("CUDA_VISIBLE_DEVICES"),
                                    "PATH": server_env.get("PATH")}
            record["model_sha256"] = sha(Path(prop["model_path"]))
            if record["model_sha256"] != MODEL["sha256"]:
                raise Stop("STOP: the GGUF sha256 differs from the pinned gemma4_31b model")
            version = smi([prop["binary"], "--version"], env=server_env)
            record["build"] = next((ln.strip() for ln in (version.stdout + version.stderr).splitlines()
                                    if ln.startswith("version:")), None)
            if record["build"] != f"version: {prop['expected_build']}":
                raise Stop(f"STOP: llama-server build {record['build']!r} is not {prop['expected_build']!r}")
            record["argv"] = server_argv(spec, port)
            run_dir = server_attempt(run_root)           # every check passed: the first thing written for the run
            record["server_dir"] = str(run_dir)
            (run_dir / "bin_manifest.txt").write_text(manifest_text)
            log = (run_dir / "llama-server.log").open("x")
            proc = popen(record["argv"], stdout=log, stderr=subprocess.STDOUT, start_new_session=True, env=server_env)
            record.update(pid=proc.pid, started_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
            (run_dir / "server_record.json").write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")
            if not wait:
                return record
            stopping = {"signal": None}
            for sig in (signal.SIGTERM, signal.SIGINT):
                signal.signal(sig, lambda s, f: stopping.update(signal=s) or proc.terminate())
            rc = proc.wait()
            log.close()
    except Stop as exc:
        if "server_dir" not in record:
            G.write_refusal(run_root, "proposer", str(exc), record)
        raise
    except Exception as exc:  # noqa: BLE001 - any failure before the server starts is a refusal, then a STOP
        if "server_dir" in record:
            raise
        message = f"STOP: the proposer server could not be started: {type(exc).__name__}: {exc}"
        G.write_refusal(run_root, "proposer", message, record)
        raise Stop(message) from exc
    end = {"stopped_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "server_rc": rc,
           "stop_signal": stopping["signal"], "server_record_sha256": L._sha_file(run_dir / "server_record.json"),
           "server_log_sha256": L._sha_file(run_dir / "llama-server.log")}
    (run_dir / "server_end.json").write_text(json.dumps(end, indent=1) + "\n")
    return record | end


# =============================================================================================== worker (TASL-2)
def _get(url: str, timeout: float = 10.0) -> tuple[int, bytes]:
    with urllib.request.urlopen(url, timeout=timeout) as r:  # noqa: S310 - declared Tailscale http URL
        return r.status, r.read()


VERSION_LINE = re.compile(r"^(?P<version>\S+) \(build (?P<build>\d+), commit (?P<commit>[0-9a-f]{7,40})\)$")


def props_build(expected_build: str) -> str:
    """The ``/props`` ``build_info`` of a llama-server whose ``--version`` line is ``version: <expected_build>``:
    llama.cpp writes ``b<build number>-<commit>`` there (e.g. ``0.7.0-dev (build 1, commit 620d222)`` -> ``b1-620d222``)."""
    m = VERSION_LINE.fullmatch(expected_build or "")
    if not m:
        raise Stop(f"STOP: proposer.expected_build {expected_build!r} is not '<version> (build N, commit C)'")
    return f"b{m.group('build')}-{m.group('commit')}"


def server_identity(spec: dict, get=_get) -> dict:
    """/health ok and /props: context 32,768, one slot, the expected build (in its /props form) and the pinned GGUF
    file name."""
    base = spec["proposer"]["server_url"].rstrip("/")
    status, body = get(base + "/health")
    if status != 200 or json.loads(body or b"{}").get("status") != "ok":
        raise Stop(f"STOP: the proposer /health is not ok ({status})")
    status, body = get(base + "/props")
    if status != 200:
        raise Stop(f"STOP: the proposer /props answered {status}")
    props = json.loads(body)
    settings = props.get("default_generation_settings") or {}
    got = {"n_ctx": settings.get("n_ctx", props.get("n_ctx")), "total_slots": props.get("total_slots"),
           "build_info": props.get("build_info"), "model_file": Path(str(props.get("model_path", ""))).name}
    want = {"n_ctx": CTX, "total_slots": 1, "build_info": props_build(spec["proposer"]["expected_build"]),
            "model_file": Path(spec["proposer"]["model_path"]).name}
    bad = {k: (got[k], want[k]) for k in want if got[k] != want[k]}
    if bad:
        raise Stop(f"STOP: the proposer /props differ from the declared server: {bad}")
    return got


def latency_probe(spec: dict, n: int = PROBES, get=_get, clock=time.monotonic) -> dict:
    base = spec["proposer"]["server_url"].rstrip("/")
    times = []
    for _ in range(n):
        t0 = clock()
        status, _ = get(base + "/health")
        if status != 200:
            raise Stop(f"STOP: a latency probe got {status}")
        times.append(clock() - t0)
    times.sort()
    return {"n": n, "median_ms": round(1000 * times[n // 2], 2), "p95_ms": round(1000 * times[int(0.95 * (n - 1))], 2),
            "max_ms": round(1000 * times[-1], 2)}


def check_server_record(spec: dict, raw: bytes, spec_sha256: str) -> dict:
    """The server_record.json copied from TASL-7 agrees with the spec (run, URL, argv, binary, model, build, GPU)."""
    rec = json.loads(raw)
    prop = spec["proposer"]
    _, port = server_url_parts(prop["server_url"])
    want = {"schema": SERVER_RECORD_SCHEMA, "run_id": spec["run_id"], "host": PROPOSER_HOST,
            "hostname": prop["hostname"], "server_url": prop["server_url"], "spec_sha256": spec_sha256,
            "binary_sha256": prop["binary_sha256"], "bin_dir_manifest_sha256": prop["bin_dir_manifest_sha256"],
            "model_sha256": MODEL["sha256"],
            "build": f"version: {prop['expected_build']}", "argv": server_argv(spec, port)}
    bad = [k for k, v in want.items() if rec.get(k) != v]
    if bad or (rec.get("gpu") or {}).get("uuid") != prop["gpu_uuid"] or (rec.get("gpu") or {}).get("name") != GPU_MODEL:
        raise Stop(f"STOP: server_record.json does not match the spec: {bad or ['gpu']}")
    return {"sha256": hashlib.sha256(raw).hexdigest(), "pid": rec.get("pid"), "started_utc": rec.get("started_utc")}


def call_latency(pilot_dir: Path) -> dict:
    """Per-call latency over every manager call of the node (the pilot's ``wall_seconds``)."""
    secs = []
    for ledger in sorted(Path(pilot_dir).glob("instance_*/campaign_ledger.jsonl")):
        for line in ledger.read_text().splitlines():
            if line.strip():
                call = json.loads(line).get("manager_call") or {}
                value = (call.get("usage") or {}).get("wall_seconds")
                if isinstance(value, (int, float)):
                    secs.append(float(value))
    secs.sort()
    if not secs:
        return {"n": 0}
    return {"n": len(secs), "median_s": secs[len(secs) // 2], "p95_s": secs[int(0.95 * (len(secs) - 1))],
            "max_s": secs[-1], "total_s": round(sum(secs), 1)}


def run_node_job(spec_path: Path, node_name: str, server_record: Path, *, smi=G._sh, engine=subprocess.run,
                 setup=L.run_setup, get=_get, node_log: str | None = None) -> dict:
    """The worker on TASL-2 for one pilot node. Preflight under the lease (host checks, affinity, the server record and
    the server identity) before anything is written for the node; a refusal goes to ``<run_id>/_refusals/``. Then a new
    ``<node>/attempt-N/`` (only after an infrastructure STOP may another attempt follow)."""
    started = time.time()
    spec = load_spec(spec_path)
    loaded = validate_spec(spec, launch=True)
    node = node_entry(spec, node_name)
    worker = spec["worker"]
    shim = worker_shim(spec)
    run_root = Path(worker["runs_root"]) / spec["run_id"]
    record: dict = {"schema": RECORD_SCHEMA, "label": ENGINEERING_ONLY, "node": node_name, "run_id": spec["run_id"],
                    "spec_sha256": L._sha_file(spec_path), "harness_commit": spec["harness"]["commit"],
                    "stop": None, "stop_class": None, "foreign_checks": [],
                    "node_log": node_log or os.environ.get("G4_TASL_NODE_LOG"),
                    "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
                    "projection": loaded["projection"]["per_node"][node_name],
                    "timeout_basis": {"decision": spec["timeout_decision"]["basis"],
                                      "seconds": timeout_basis(spec, node), "timeout_s": 3 * timeout_basis(spec, node)},
                    "output_use": "ENGINEERING_ONLY G.4 pilot measurements on the TASL pair; proposals are not labels"}
    deadline = started + walltime(spec, node)
    lease_cm = G.gpu_lease(worker["lease"])
    try:
        record["lease"] = lease_cm.__enter__()
    except Stop as exc:
        G.write_refusal(run_root, node_name, str(exc), record)
        raise
    except Exception as exc:  # noqa: BLE001 - e.g. the lease directory cannot be made
        message = f"STOP: unexpected {type(exc).__name__} taking the lease: {exc}"
        G.write_refusal(run_root, node_name, message, record)
        raise Stop(message) from exc
    try:
        try:
            record["host"] = G.host_identity(shim, WORKER_HOST)
            record["affinity"] = G.check_affinity(shim, {"host": WORKER_HOST})
            record["gpu"] = G.gpu_check(shim, WORKER_HOST, smi)
            record["foreign_checks"].append(G.check_no_foreign(worker["gpu_uuid"], "before the job", smi))
            record["ptrace_scope"] = G.ptrace_scope()
            record["cgroup"] = G.scope_cgroup()
            record["harness"] = G.harness_checkout(shim, WORKER_HOST)
            record["environment"] = G.environment(shim, WORKER_HOST, node)
            raw = Path(server_record).read_bytes()
            record["server_record"] = check_server_record(spec, raw, record["spec_sha256"])
            record["server_props_before"] = server_identity(spec, get)
            record["latency_probe_before"] = latency_probe(spec, get=get)
            record["attempt"], job_dir = G.next_attempt(run_root / node_name)
        except Stop as exc:
            G.write_refusal(run_root, node_name, str(exc), record)
            raise
        except Exception as exc:  # noqa: BLE001 - a crash in a check is a refusal with a record
            message = f"STOP: unexpected {type(exc).__name__} before the run: {exc}"
            G.write_refusal(run_root, node_name, message, record)
            raise Stop(message) from exc
        (job_dir / "server_record.json").write_bytes(raw)
        out = job_dir / "out"
        out.mkdir()
        try:
            harness = Path(worker["harness_dir"])
            python = worker["env_python"][node["env"]]
            os.environ["PATH"] = f"{Path(python).parent}:{os.environ.get('PATH', '')}"
            for key, value in (worker.get("extra_env") or {}).items():
                os.environ[key] = value
            record["data"] = setup(harness, node, Path(worker["base"]), out)
            pilot = pilot_file(spec, node, interpreter=python, cgroup_parent=record["cgroup"]["cgroup_parent"])
            (out / "pilot.json").write_text(json.dumps(pilot, indent=1) + "\n")
            record["foreign_checks"].append(G.check_no_foreign(worker["gpu_uuid"], "before the pilot", smi))
            remaining = int(deadline - time.time())
            if remaining < 60:
                raise Stop("STOP: the node deadline was reached before the pilot engine started")
            env = dict(os.environ, PYTHONPATH=str(harness / "src"), PYTHONDONTWRITEBYTECODE="1",
                       AR_TRACKG_DATA_ROOT=record["data"]["data_root"], CUDA_VISIBLE_DEVICES="")
            for name in ("NVIDIA_VISIBLE_DEVICES", "_CONDOR_AssignedGPUs"):
                env.pop(name, None)
            argv = [python, "-m", "autoresearch.trackg.pilot_g4", "run", "--pilot", str(out / "pilot.json"),
                    "--harness-root", str(harness), "--out", str(out / "pilot"), "--gpu-uuid", worker["gpu_uuid"]]
            try:
                res = engine(argv, cwd=harness, env=env, capture_output=True, text=True, timeout=remaining)
            except subprocess.TimeoutExpired as exc:
                (out / "pilot_engine.log").write_text(f"{L._text(exc.stdout)}\n--- stderr ---\n{L._text(exc.stderr)}")
                raise Stop("STOP: the pilot engine reached the node deadline; partial outputs kept") from None
            (out / "pilot_engine.log").write_text(res.stdout + "\n--- stderr ---\n" + res.stderr)
            record["foreign_checks"].append(G.check_no_foreign(worker["gpu_uuid"], "after the pilot", smi))
            record["server_props_after"] = server_identity(spec, get)
            if record["server_props_after"] != record["server_props_before"]:
                raise Stop("STOP: the proposer /props changed during the pilot")
            record["latency_probe_after"] = latency_probe(spec, get=get)
            record["call_latency"] = call_latency(out / "pilot")
            summary_path = out / "pilot" / "pilot_summary.json"
            summary = json.loads(summary_path.read_text()) if summary_path.is_file() else None
            record["summary"] = summary
            if res.returncode != 0:
                raise Stop(f"STOP: the pilot engine exited {res.returncode}; see out/pilot/pilot_record.json")
            fit = (summary or {}).get("fit") or {}
            if fit.get("cache_prompt_false_on_every_call") is not True:
                raise Stop("STOP: a recorded request lacked cache_prompt: false")
            run_median = ((summary or {}).get("seconds") or {}).get("run_median")
            if isinstance(run_median, (int, float)) and run_median > timeout_basis(spec, node):
                raise TimingStop(f"STOP: the pilot run median {run_median} s on the 4090 exceeds the declared timeout "
                                 f"basis {timeout_basis(spec, node)} s (R1-G1B-TIMEOUT): the author decides")
            if fit.get("all_fit_ctx") is False:
                raise NodeStop("STOP: a prompt plus the completion cap exceeds the 32,768 context")
            if not ((summary or {}).get("diff_liveness") or {}).get("ran_of_valid"):
                raise NodeStop("STOP: diff liveness 0 on a T1 pilot node (R1-BX-PROPOSED-CONFIRM D4: the author decides)")
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
        L._write_sums(job_dir, ("out.tar", "job_record.json", "server_record.json"))
    finally:
        lease_cm.__exit__(None, None, None)
    if record["stop"]:
        raise Stop(record["stop"])
    return record


# =============================================================================================== seal / read / dates
def seal(job_dir: Path, spec: dict, node_name: str, *, server_end: Path | None = None,
         server_log: Path | None = None) -> dict:
    """Verify, copy to <worker sealed_root>/<run_id>/<node>/ (no overwrite) and write a receipt binding the job record,
    the server record, and (when given) TASL-7's server_end.json and llama-server.log."""
    src = Path(job_dir).resolve()
    record = json.loads((src / "job_record.json").read_text())
    if record.get("label") != ENGINEERING_ONLY or record.get("run_id") != spec["run_id"] or record.get("node") != node_name:
        raise Stop("STOP: the job record does not match the run/node or is not ENGINEERING_ONLY")
    if (record.get("gpu") or {}).get("name") != GPU_MODEL or (record.get("host") or {}).get("host") != WORKER_HOST:
        raise Stop("STOP: the job record lacks the TASL-2 RTX 4090 identity")
    if subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=src, capture_output=True).returncode != 0:
        raise Stop("STOP: SHA256SUMS verification failed")
    if src.name != f"attempt-{record.get('attempt')}":
        raise Stop("STOP: the job directory is not the attempt its record names")
    target = Path(spec["worker"]["sealed_root"]) / spec["run_id"] / node_name / src.name
    if target.exists() or any(p.is_symlink() for p in [target, *target.parents] if p.exists()):
        raise Stop(f"STOP: sealed target {target} exists or has a symlink component; no overwrite")
    target.mkdir(parents=True, mode=0o700)
    for name in ("out.tar", "job_record.json", "SHA256SUMS", "server_record.json"):
        if (src / name).is_file():
            shutil.copy2(src / name, target / name)
    logs_dir = (Path(spec["worker"]["runs_root"]) / spec["run_id"] / "_logs").resolve()
    node_log = record.get("node_log")
    if node_log and Path(node_log).is_file() and Path(node_log).resolve().parent == logs_dir:
        shutil.copy2(node_log, target / "node.log")
    for path, name in ((server_end, "server_end.json"), (server_log, "llama-server.log")):
        if path is not None and Path(path).is_file():
            shutil.copy2(path, target / name)
    receipt = {"schema": RECEIPT_SCHEMA, "run_id": spec["run_id"], "node": node_name, "attempt": record.get("attempt"),
               "sealed_path": str(target),
               "stop": record.get("stop"), "stop_class": record.get("stop_class"),
               **{f"{n.replace('-', '_').replace('.', '_')}_sha256": L._sha_file(target / n) if (target / n).is_file()
                  else None for n in ("job_record.json", "server_record.json", "server_end.json", "llama-server.log",
                                      "node.log")},
               "sealed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    (target / "SEAL_RECEIPT.json").write_text(json.dumps(receipt, indent=1) + "\n")
    return receipt


def read_sealed_summary(sealed: Path, spec: dict, spec_file_sha256: str) -> dict:
    sealed = Path(sealed)
    if not (sealed / "SEAL_RECEIPT.json").is_file():
        raise Stop(f"STOP: {sealed} has no SEAL_RECEIPT.json")
    if subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=sealed, capture_output=True).returncode != 0:
        raise Stop(f"STOP: {sealed} does not verify against its SHA256SUMS")
    record = json.loads((sealed / "job_record.json").read_text())
    receipt = json.loads((sealed / "SEAL_RECEIPT.json").read_text())
    problems = [k for k, ok in (
        ("receipt", receipt.get("job_record_json_sha256") == L._sha_file(sealed / "job_record.json")),
        ("run_id", record.get("run_id") == spec["run_id"]), ("spec_sha256", record.get("spec_sha256") == spec_file_sha256),
        ("harness_commit", record.get("harness_commit") == spec["harness"]["commit"]),
        ("gpu", (record.get("gpu") or {}).get("name") == GPU_MODEL),
        ("host", (record.get("host") or {}).get("host") == WORKER_HOST),
        ("server_record", (record.get("server_record") or {}).get("sha256") == receipt.get("server_record_json_sha256")),
        ("stop", record.get("stop") is None)) if not ok]
    if problems:
        raise Stop(f"STOP: {sealed} cannot feed the recompute: {problems}")
    with tarfile.open(sealed / "out.tar") as tar:
        try:
            member = tar.extractfile("out/pilot/pilot_summary.json")
        except KeyError:
            member = None
        if member is None:
            raise Stop(f"STOP: {sealed}/out.tar has no out/pilot/pilot_summary.json")
        summary = json.loads(member.read())
    return g4_lib.check_summary(summary, record["node"])


def recompute_dates(summaries: dict[str, dict], params: dict, *, today: date) -> dict:
    """``g4_lib.recompute_dates`` for the TASL pair: one concurrent worker slot, the 4090 relabelling."""
    if params.get("concurrent_h200_slots") != 1:
        raise Stop("STOP: the TASL pair has one concurrent G.5 worker slot (TASL-2; TASL-7 serves the proposer)")
    if params.get("gpu_model") != GPU_MODEL:
        raise Stop(f"STOP: the dates params must declare gpu_model {GPU_MODEL}")
    out = g4_lib.recompute_dates(summaries, params, today=today)
    ratio = out.pop("h200_over_census_run_ratio")
    for key in ("g5_requested_slot_hours", "g5_slot_cap", "g5_slots_within_cap"):   # HTCondor walltime requests
        out.pop(key, None)
    for by_k in out["g5_by_K"].values():
        by_k.pop("requested_slot_hours", None)
        for row in by_k["per_node"].values():
            row.pop("requested_slot_hours", None)
    out.update(rtx4090_over_census_run_ratio=ratio, gpu_model=GPU_MODEL, concurrent_worker_slots=1,
               basis=("measured (G.4 pilot: worker TASL-2 RTX 4090, proposer TASL-7)" if summaries
                      else out["basis"]),
               ratio_basis="median over pilot nodes of (pilot run median, edited runs included, on the RTX 4090) / "
                           "(census B1 baseline time on the RTX 6000 Ada)",
               slot_hours_note="direct host runs request no scheduler slot-hours; the cap is on worker GPU-hours",
               gpu_hours_note="worker GPU-hours on TASL-2; the proposer GPU on TASL-7 is held for the same span "
                              "(double for GPU-hours of both cards)")
    return out


# =============================================================================================== launch / CLI
PLACEHOLDER = re.compile(r"<[^>]*>")
REVIEW_PATH = re.compile(r"docs/r1/reviews/[A-Za-z0-9_.\-/]+\.md")


def check_note(note_path: Path, spec_path: Path, paper_commit: str, *, on_main, spec: dict | None = None,
               read_main=None) -> dict:
    """The author-signed G.4 note: on published main, named g4_t1_tasl_<date>.md, approved true, ENGINEERING_ONLY,
    binding the paper commit and the spec sha256 (and, given the spec, its run_id and the bare harness commit:
    R1-T1-TASL-ENV "harness at the commit the signed note names"), P1-P5 PASS with their citations (P1 the TASL-2 host
    check and R1-T1-HOST-TASL, P2 R1-TRACKG-G3-EARLY, P3 a signed G.1b note, worded per decision G4-ORDER, P4 the
    review files, P5 R1-T1-TASL-ENV). No field may hold a template placeholder (``<…>``); given ``read_main``, every
    review file P4 names must be on origin/main."""
    note_path = Path(note_path)
    if note_path.parent.as_posix().split("/")[-3:] != NOTE_DIR.split("/") or not NOTE_NAME.fullmatch(note_path.name):
        raise Stop(f"STOP: the note must be {NOTE_DIR}/g4_t1_tasl_<YYYYMMDD>.md")
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
    unfilled = sorted(k for k, v in fields.items() if PLACEHOLDER.search(v))
    if unfilled:
        raise Stop(f"STOP: note fields not filled (a <...> placeholder): {unfilled}")
    for key, value in {"approved": "true", "label": ENGINEERING_ONLY, "labels_read": "none",
                       "paper_commit": paper_commit, "spec_sha256": L._sha_file(spec_path)}.items():
        if fields.get(key) != value:
            raise Stop(f"STOP: note field {key} must be {value!r}")
    cites = {"P1": "R1-T1-HOST-TASL", "P2": "R1-TRACKG-G3-EARLY", "P3": "g1b_t1_tasl_", "P4": "docs/r1/reviews/",
             "P5": "R1-T1-TASL-ENV"}
    for key, cite in cites.items():
        if not fields.get(key, "").upper().startswith(("PASS — ", "PASS - ")) or cite not in fields[key]:
            raise Stop(f"STOP: {key} must be PASS and cite {cite}")
    if spec is not None:
        for key, value in (("run_id", spec["run_id"]), ("harness_commit", spec["harness"]["commit"])):
            if fields.get(key) != value:       # R1-T1-TASL-ENV: "harness at the commit the signed note names"
                raise Stop(f"STOP: note field {key} must be {value!r} (the spec's)")
    if read_main is not None:
        reviews = REVIEW_PATH.findall(fields["P4"])
        missing = [r for r in reviews if not read_main(r)]
        if not reviews or missing:
            raise Stop(f"STOP: P4 must name review files on origin/main (missing: {missing or 'none named'})")
    return fields


IMPORT_SOURCES = {"g1b_tasl": "sweep2/t1_tasl/g1b_tasl.py", "g1b_lib": "sweep2/g1b/g1b_lib.py",
                  "g4_lib": "sweep2/g4/g4_lib.py", "s2_c2_lib": "sweep2/s2_c2_lib.py"}


def check_import_sources(repo: Path = None) -> dict:
    """The modules this script imports from the checkout are the reviewed source files, not a shadow found earlier on
    ``sys.path`` (a sourceless ``.pyc`` in ``sweep2/g4`` is ignored by git and would be imported first)."""
    repo = Path(repo or REPO_ROOT).resolve()
    out = {}
    for name, rel in IMPORT_SOURCES.items():
        mod = sys.modules.get(name)
        if mod is None:
            continue
        got = Path(getattr(mod, "__file__", "") or "").resolve()
        if got != repo / rel:
            raise Stop(f"STOP: module {name} was imported from {got}, not the reviewed {rel}")
        out[name] = rel
    return out


def _note_on_main(rel: str, raw: bytes) -> bool:
    res = subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"origin/main:{rel}"], capture_output=True)
    return res.returncode == 0 and res.stdout == raw


def _binding(spec_path: Path, launch_binding):
    """The TASL launch binding ``g1b_tasl.verify_launch_tasl`` (decision G4-LB: R1-G1B-TASL-DECISIONS LB A applied to
    G.4), after the import-source check: ``g1b_lib.verify_launch`` cannot be met by a note on main that names the
    launch commit."""
    def bind(repo, s, r):
        imports = check_import_sources(repo)            # first: no shadowed module's code runs as the binding
        return {**G.verify_launch_tasl(repo, s, r, spec_path=spec_path), "imports": imports}
    return launch_binding or bind


def serve_launch(spec_path: Path, note_path: Path, *, enable: bool, on_main=_note_on_main, launch_binding=None,
                 server=None, read_main=G._read_main) -> dict:
    """``serve`` behind the same gate as ``run-node``: the signed note (with the spec's run_id and harness commit),
    both keys, and the TASL launch binding, before the GPU lease is taken."""
    spec = load_spec(spec_path)
    validate_spec(spec, launch=True)
    check_note(note_path, spec_path, spec["paper"]["commit"], on_main=on_main, spec=spec, read_main=read_main)
    if not enable or os.environ.get(ENABLE_ENV) != "1":
        raise Stop(f"STOP: the proposer server is disabled (needs --enable AND {ENABLE_ENV}=1)")
    binding = _binding(spec_path, launch_binding)(REPO_ROOT, spec, PLAN_ROWS)
    return (server or serve)(spec_path) | {"launch": binding}


def launch(spec_path: Path, note_path: Path, node_name: str, server_record: Path, *, enable: bool,
           on_main=_note_on_main, launch_binding=None, runner=None, read_main=G._read_main) -> dict:
    spec = load_spec(spec_path)
    validate_spec(spec, launch=True)
    fields = check_note(note_path, spec_path, spec["paper"]["commit"], on_main=on_main, spec=spec,
                        read_main=read_main)
    if not enable or os.environ.get(ENABLE_ENV) != "1":
        raise Stop(f"STOP: real G.4 runs are disabled (needs --enable AND {ENABLE_ENV}=1)")
    check = G.check_host_record(spec["worker"], spec["harness"]["commit"], read_main)   # R1-T1-HOST-TASL
    if check["record"] not in fields["P1"]:
        raise Stop(f"STOP: P1 must cite TASL-2's host check report {check['record']}")
    binding = _binding(spec_path, launch_binding)(REPO_ROOT, spec, PLAN_ROWS)
    return (runner or run_node_job)(spec_path, node_name, server_record) | {"launch": binding}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate"); v.add_argument("spec"); v.add_argument("--launch", action="store_true")
    s = sub.add_parser("serve"); s.add_argument("spec"); s.add_argument("--note", required=True)
    s.add_argument("--enable", action="store_true")
    r = sub.add_parser("run-node"); r.add_argument("spec"); r.add_argument("--node", required=True)
    r.add_argument("--server-record", required=True); r.add_argument("--note", required=True)
    r.add_argument("--enable", action="store_true")
    c = sub.add_parser("cpus"); c.add_argument("spec"); c.add_argument("--node", required=True)
    bm = sub.add_parser("bin-manifest"); bm.add_argument("bin_dir")
    ca = sub.add_parser("close-attempt"); ca.add_argument("spec"); ca.add_argument("attempt_dir")
    ca.add_argument("--node", required=True); ca.add_argument("--reason", required=True)
    g = sub.add_parser("logdir"); g.add_argument("spec"); g.add_argument("--node", required=True)
    z = sub.add_parser("seal"); z.add_argument("job_dir"); z.add_argument("spec"); z.add_argument("--node", required=True)
    z.add_argument("--server-end"); z.add_argument("--server-log")
    d = sub.add_parser("dates"); d.add_argument("spec"); d.add_argument("params"); d.add_argument("sealed", nargs="*")
    d.add_argument("--today", required=True)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "validate":
            loaded = validate_spec(load_spec(Path(a.spec)), launch=a.launch)
            print(json.dumps({"ok": True, "run_id": loaded["run_id"], "projection": loaded["projection"]}, indent=1))
        elif a.cmd == "close-attempt":
            spec = load_spec(Path(a.spec))
            node_entry(spec, a.node)
            expected = Path(spec["worker"]["runs_root"]) / spec["run_id"] / a.node
            if Path(a.attempt_dir).resolve().parent != expected.resolve():
                raise Stop(f"STOP: {a.attempt_dir} is not an attempt of {a.node} in this run")
            print(json.dumps(G.close_attempt(Path(a.attempt_dir), a.reason, lease=spec["worker"]["lease"]), indent=1))
        elif a.cmd == "bin-manifest":
            text, digest = bin_manifest(Path(a.bin_dir))
            print(text + f"manifest_sha256: {digest}")
        elif a.cmd in ("cpus", "logdir"):
            spec = load_spec(Path(a.spec))
            validate_spec(spec)
            node_entry(spec, a.node)
            print(spec["worker"]["cpus"] if a.cmd == "cpus" else
                  str(Path(spec["worker"]["runs_root"]) / spec["run_id"] / "_logs"))
        elif a.cmd == "serve":
            print(json.dumps(serve_launch(Path(a.spec), Path(a.note), enable=a.enable), indent=1, default=str))
        elif a.cmd == "run-node":
            rec = launch(Path(a.spec), Path(a.note), a.node, Path(a.server_record), enable=a.enable)
            print(json.dumps({"ok": True, "node": a.node, "summary": rec.get("summary")}, indent=1, default=str))
        elif a.cmd == "seal":
            print(json.dumps(seal(Path(a.job_dir), load_spec(Path(a.spec)), a.node,
                                  server_end=a.server_end and Path(a.server_end),
                                  server_log=a.server_log and Path(a.server_log)), indent=1))
        else:
            spec = load_spec(Path(a.spec))
            sha = L._sha_file(Path(a.spec))
            summaries = {}
            for sealed in a.sealed:
                s = read_sealed_summary(Path(sealed), spec, sha)
                if s["node"] in summaries:
                    raise Stop(f"STOP: two sealed attempts given for {s['node']}")
                summaries[s["node"]] = s
            params = json.loads(Path(a.params).read_text())
            print(json.dumps(recompute_dates(summaries, params, today=date.fromisoformat(a.today)), indent=1,
                             default=str))
    except Stop as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
