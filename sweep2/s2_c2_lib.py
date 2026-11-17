#!/usr/bin/env python3
"""S2-C2 sweep-2 HTCondor job wrapper + sealing step (ENGINEERING until P1-P7; reviewed dry-run JDL).

One job == one (node, memory mode) chunk of sweep-2 root campaigns. The container job writes only into its
HTCondor sandbox; HTCondor transfers `out/`, `work/`, `job_record.json`, `SHA256SUMS` back to the submit host and
the reviewed `seal` step copies them into the sealed `/ceph/srv/dwong/paperb/sweep2/<run_id>/` path (NEMO2 slots
do not advertise ProvidesEtpCeph - verified 16 Nov 2026 - so a NEMO2 job cannot write /ceph directly).

The wrapper validates the spec fail-closed, takes the table label only from the transferred authorization note (or
ENGINEERING_ONLY), verifies the frozen image identity, records host/GPU/CPU/driver, fetches the pinned GGUF with a
streaming sha256, starts an owned llama-server with the exam flags, checks full offload, runs the harness root
campaigns via r1.headroom.e1b_collect (llamacpp manager), records the job record and stops the server. Raw labels
are written sealed and never read here.
"""
from __future__ import annotations

import argparse
import hashlib
import math
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

SCHEMA = "s2_c2_job/v1"
SEALED_ROOT = Path("/ceph/srv/dwong/paperb/sweep2")
CLOUD_SITE = "BwForCluster-Nemo2"
GPU_MODEL = "NVIDIA L40S"  # historical; sweep 2 now accepts any GPU with >=24 GB VRAM and CC >= 7.0
GPU_MIN_MEMORY_MB = 24576
GPU_MIN_CAPABILITY = 7.0
MIN_CPUS = 16
CPU_FAMILY = 6
CPU_MODEL_NUMBER = 207
CPU_MODEL_CONTAINS = "INTEL(R) XEON(R) PLATINUM 8562Y+"
CTX = 32768
NGL = 999
NP = 1
NOISE_PATH = "results/r1/noise/D28_REPAIR_20261027/summary.json"
NOISE_SHA = "3d12ce058c584d862b683bf9e0c79b8c1f7609343c7b62b839c00c4a83c34310"
LIVENESS_NODES = ("digits_mlp", "tabular_mlp", "openml_breast_w", "openml_ionosphere",
                  "openml_wdbc", "openml_credit_approval", "openml_sonar", "openml_climate")
MIN_LIVE_NODES = 8
MAX_PARSE_FAILURE_RATE = 0.2
# Sweep-1 worker-success baseline per (node, memory mode), computed from the frozen sweep-1 corpus on main
# (results/r1/evidence/C3_sweep_{append_only_summary_20261027T154834Z,none_20261027T224356Z}/
# provenance/ledgers/roots/*/root_trials.jsonl). `skipped` = record has worker_skipped:true (the worker never
# ran; proposal_precondition_failed) and is excluded from the worker denominator on both sides.
SWEEP1_WORKER_BASELINE = {
    ("digits_mlp", "append_only_summary"): {"worker_trials": 360, "successes": 360, "skipped": 38, "failures": 0, "runtime_errors": 0, "invalid_config": 0},
    ("digits_mlp", "none"): {"worker_trials": 360, "successes": 360, "skipped": 0, "failures": 0, "runtime_errors": 0, "invalid_config": 0},
    ("openml_breast_w", "append_only_summary"): {"worker_trials": 360, "successes": 318, "skipped": 0, "failures": 42, "runtime_errors": 0, "invalid_config": 42},
    ("openml_breast_w", "none"): {"worker_trials": 360, "successes": 360, "skipped": 0, "failures": 0, "runtime_errors": 0, "invalid_config": 0},
    ("openml_climate", "append_only_summary"): {"worker_trials": 360, "successes": 273, "skipped": 0, "failures": 87, "runtime_errors": 0, "invalid_config": 87},
    ("openml_climate", "none"): {"worker_trials": 360, "successes": 298, "skipped": 0, "failures": 62, "runtime_errors": 0, "invalid_config": 62},
    ("openml_credit_approval", "append_only_summary"): {"worker_trials": 360, "successes": 339, "skipped": 0, "failures": 21, "runtime_errors": 0, "invalid_config": 21},
    ("openml_credit_approval", "none"): {"worker_trials": 360, "successes": 333, "skipped": 0, "failures": 27, "runtime_errors": 0, "invalid_config": 27},
    ("openml_ionosphere", "append_only_summary"): {"worker_trials": 360, "successes": 249, "skipped": 0, "failures": 111, "runtime_errors": 0, "invalid_config": 111},
    ("openml_ionosphere", "none"): {"worker_trials": 360, "successes": 301, "skipped": 0, "failures": 59, "runtime_errors": 0, "invalid_config": 59},
    ("openml_sonar", "append_only_summary"): {"worker_trials": 360, "successes": 327, "skipped": 0, "failures": 33, "runtime_errors": 0, "invalid_config": 33},
    ("openml_sonar", "none"): {"worker_trials": 360, "successes": 360, "skipped": 0, "failures": 0, "runtime_errors": 0, "invalid_config": 0},
    ("openml_wdbc", "append_only_summary"): {"worker_trials": 360, "successes": 329, "skipped": 4, "failures": 31, "runtime_errors": 0, "invalid_config": 31},
    ("openml_wdbc", "none"): {"worker_trials": 360, "successes": 360, "skipped": 0, "failures": 0, "runtime_errors": 0, "invalid_config": 0},
    ("tabular_mlp", "append_only_summary"): {"worker_trials": 360, "successes": 360, "skipped": 11, "failures": 0, "runtime_errors": 0, "invalid_config": 0},
    ("tabular_mlp", "none"): {"worker_trials": 360, "successes": 360, "skipped": 0, "failures": 0, "runtime_errors": 0, "invalid_config": 0},
}
WORKER_FAILURE_MARGIN = 0.05
WORKER_BINOMIAL_ALPHA = 0.01
NON_NUMERIC_DIFFERENCES = ["--no-webui (UI only, not numeric)", "-lv 4 (log verbosity, not numeric)"]
B2_HARNESS = "a3fedbbd44309b3fdf99d853ad841b9ec2c299e2"
EXAM_THINKING_KWARGS = '{"enable_thinking":false}'  # byte-identical to the exam invocation (no extra spaces)
SHA = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
SAFE = re.compile(r"^[A-Za-z0-9_.-]+$")
CONTROL = re.compile(r"[\x00-\x1f\x7f]")


class Stop(RuntimeError):
    pass


# ------------------------------------------------------------------ spec
def load_spec(path: Path) -> dict:
    data = json.loads(Path(path).read_text())
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise Stop(f"STOP: spec schema must be {SCHEMA}")
    return data


def _get(d, *keys):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            raise Stop(f"STOP: spec missing {'.'.join(keys)}")
        cur = cur[k]
    return cur


def _text(v, name, pattern=None):
    if not isinstance(v, str) or not v or CONTROL.search(v):
        raise Stop(f"STOP: {name} must be a nonempty single-line string")
    if pattern and not pattern.fullmatch(v):
        raise Stop(f"STOP: {name} has the wrong form")
    return v


def validate_spec(spec: dict) -> dict:
    run_id = _text(_get(spec, "run_id"), "run_id", SAFE)
    _text(_get(spec, "chunk_id"), "chunk_id", SAFE)
    kind = spec.get("kind", "chunk")
    if kind not in ("chunk", "liveness"):
        raise Stop("STOP: kind must be chunk or liveness")
    image = _get(spec, "image")
    digest = _text(_get(image, "digest"), "image.digest")
    if not re.fullmatch(r"ghcr\.io/[a-z0-9._/-]+@sha256:[0-9a-f]{64}", digest):
        raise Stop("STOP: image.digest must be a ghcr image pinned by sha256 digest")
    markers = _get(image, "versions_markers")
    if not isinstance(markers, dict) or not markers:
        raise Stop("STOP: image.versions_markers must be a nonempty object")
    for k, v in markers.items():
        _text(k, "image.versions_markers key"); _text(v, f"image.versions_markers[{k}]")
    _text(_get(image, "llama_server_sha256"), "image.llama_server_sha256", SHA)

    paper = _get(spec, "paper")
    _text(_get(paper, "repo"), "paper.repo")
    _text(_get(paper, "commit"), "paper.commit", COMMIT)
    if type(paper.get("evidence_ready")) is not bool:
        raise Stop("STOP: paper.evidence_ready must be a boolean")
    harness = _get(spec, "harness")
    _text(_get(harness, "repo"), "harness.repo")
    harness_commit = _text(_get(harness, "commit"), "harness.commit", COMMIT)
    if harness_commit != B2_HARNESS:
        raise Stop(f"STOP: sweep-2 must reproduce the B2 harness {B2_HARNESS} (M1); got {harness_commit}")
    if not isinstance(harness.get("exception_reason"), str):
        raise Stop("STOP: harness.exception_reason must be a string (empty when the B2 pin is used)")

    model = _get(spec, "model")
    url = _text(_get(model, "url"), "model.url")
    if not url.startswith("https://huggingface.co/"):
        raise Stop("STOP: model.url must be the pinned HuggingFace URL")
    _text(_get(model, "sha256"), "model.sha256", SHA)
    if type(model.get("size")) is not int or model["size"] <= 0:
        raise Stop("STOP: model.size must be a positive integer")
    _text(_get(model, "alias"), "model.alias", SAFE)
    prov = _get(model, "provenance")
    for key in ("registry_doc", "revision", "file"):
        _text(_get(prov, key), f"model.provenance.{key}")
    if not SHA.fullmatch(str(_get(prov, "registry_sha256"))):
        raise Stop("STOP: model.provenance.registry_sha256 must be a sha256")

    server = _get(spec, "server")
    _text(_get(server, "binary"), "server.binary")
    for key in ("ctx", "n_gpu_layers", "port"):
        v = _get(server, key)
        if type(v) is not int or v <= 0:
            raise Stop(f"STOP: server.{key} must be a positive integer")
    extra = _get(server, "extra_args")
    if not isinstance(extra, list) or not all(isinstance(a, str) and not CONTROL.search(a) for a in extra):
        raise Stop("STOP: server.extra_args must be a list of single-line strings")
    if "$" in " ".join(extra):
        raise Stop("STOP: '$' in server.extra_args is refused")
    _text(_get(server, "expected_build"), "server.expected_build")
    allowed = {"--jinja", "--chat-template-kwargs", "--cache-type-k", "--cache-type-v", "--no-webui"}
    for i, a in enumerate(extra):
        if a.startswith("-") and a not in allowed:
            raise Stop(f"STOP: server.extra_args flag {a!r} is not part of the exam setting")
    for flag, value in (("--jinja", None), ("--cache-type-k", "q8_0"), ("--cache-type-v", "q8_0"),
                        ("--chat-template-kwargs", None)):
        if flag not in extra:
            raise Stop(f"STOP: exam server flags require {flag} in server.extra_args")
        if value is not None and extra[extra.index(flag) + 1] != value:
            raise Stop(f"STOP: {flag} must be {value}")
    raw_kwargs = extra[extra.index("--chat-template-kwargs") + 1]
    if raw_kwargs != EXAM_THINKING_KWARGS:
        raise Stop(f"STOP: --chat-template-kwargs must be byte-identical to the exam invocation "
                   f"{EXAM_THINKING_KWARGS!r} (got {raw_kwargs!r}; disclosure is not a substitute)")
    try:
        json.loads(raw_kwargs)
    except json.JSONDecodeError:
        raise Stop("STOP: --chat-template-kwargs value must be JSON") from None
    if server["ctx"] != CTX:
        raise Stop(f"STOP: ctx must be {CTX} (R1-SWEEP2-SETTINGS; the exam setting is 32,768)")
    if server["n_gpu_layers"] != NGL:
        raise Stop(f"STOP: n_gpu_layers must be {NGL} (R1-SWEEP2-SETTINGS, exam setting)")

    col = _get(spec, "collector")
    _text(_get(col, "node"), "collector.node", SAFE)
    if _get(col, "memory_mode") not in ("append_only_summary", "none"):
        raise Stop("STOP: memory_mode must be append_only_summary or none")
    for key in ("instances", "runs", "workers", "transport_max_attempts"):
        v = _get(col, key)
        if type(v) is not int or v <= 0:
            raise Stop(f"STOP: collector.{key} must be a positive integer")
    if col["runs"] != 20:
        raise Stop("STOP: W = 20 worker runs is fixed (sweep-1 collection)")
    if _get(col, "node") not in LIVENESS_NODES:
        raise Stop("STOP: collector.node must be one of the eight sweep-1 nodes")
    if col.get("split") != "c3_labels":
        raise Stop("STOP: collector.split must be c3_labels (sweep-1 split)")
    pilot = spec.get("pilot", False)
    if type(pilot) is not bool:
        raise Stop("STOP: pilot must be a boolean")
    if pilot:
        if col["instances"] != 2:
            raise Stop("STOP: the timing pilot runs 2 instances (S2-C4)")
    elif col["instances"] != 18:
        raise Stop("STOP: chunk jobs use the 18 sweep-1 instances (liveness uses 2)")
    if col["workers"] != MIN_CPUS:
        raise Stop(f"STOP: collector.workers must be {MIN_CPUS} (one per pinned CPU class core)")
    if _get(col, "proposal_schema") != "manager_proposal/v1":
        raise Stop("STOP: proposal_schema must be manager_proposal/v1 for the pick")
    if _get(col, "verify_split_policy") != "vary":
        raise Stop("STOP: verify_split_policy must be vary")

    req = _get(spec, "requirements")
    # R1-SWEEP2-ANY-GPU: no GPU-model/site pin; require VRAM >= 24 GB and compute capability >= 7.0.
    if _get(req, "gpu_min_memory_mb") != GPU_MIN_MEMORY_MB:
        raise Stop(f"STOP: requirements.gpu_min_memory_mb must be {GPU_MIN_MEMORY_MB} (24 GB floor)")
    if float(_get(req, "gpu_min_capability")) != GPU_MIN_CAPABILITY:
        raise Stop(f"STOP: requirements.gpu_min_capability must be {GPU_MIN_CAPABILITY}")
    for key in ("gpu_device_name",):
        if key in req:
            raise Stop(f"STOP: requirements.{key} is no longer pinned (any GPU meeting VRAM/CC)")
    if _get(req, "arch") != "X86_64" or _get(req, "opsys") != "LINUX":
        raise Stop("STOP: requirements pin Arch=X86_64 and OpSys=LINUX")
    if _get(req, "min_cpus") != MIN_CPUS:
        raise Stop(f"STOP: min_cpus must equal {MIN_CPUS} (pinned CPU class)")
    # R1-SWEEP-HOST-L40S-SITES: requirements pin the GPU model (L40S), not the site; both CPU models are allowed
    # and recorded/disclosed at run time. A site/CPU pin here would be a stale requirement.
    for key in ("cloud_site", "cpu_family", "cpu_model_number", "cpu_model_contains", "machine_regex"):
        if key in req:
            raise Stop(f"STOP: requirements.{key} is no longer pinned (GPU model only; sites/CPU disclosed at run time)")
    if "requires_etp_ceph" in req:
        raise Stop("STOP: NEMO2 slots do not advertise ProvidesEtpCeph; outputs transfer to the submit host and are sealed there")
    if kind == "chunk":
        noise = _get(spec, "noise_source")
        if _get(noise, "path") != NOISE_PATH or _get(noise, "sha256") != NOISE_SHA:
            raise Stop(f"STOP: noise_source must be the pinned D28 summary {NOISE_PATH} sha256 {NOISE_SHA}")
    live = _get(spec, "liveness")
    if list(_get(live, "nodes")) != list(LIVENESS_NODES):
        raise Stop("STOP: liveness.nodes must be the eight sweep-1 nodes")
    if _get(live, "instances") != 2 or _get(live, "runs") != 10:
        raise Stop("STOP: liveness instances=2, runs=10 (sweep-1 D28 liveness)")
    if _get(live, "memory_mode") != "append_only_summary":
        raise Stop("STOP: liveness memory_mode must be append_only_summary")
    if _get(live, "min_live_nodes") != MIN_LIVE_NODES:
        raise Stop(f"STOP: liveness.min_live_nodes must be {MIN_LIVE_NODES}")
    if _get(live, "max_parse_failure_rate") != MAX_PARSE_FAILURE_RATE:
        raise Stop(f"STOP: liveness.max_parse_failure_rate must be {MAX_PARSE_FAILURE_RATE}")

    wall = spec.get("walltime_s")
    if type(wall) is not int or not 3600 <= wall <= 86400:
        raise Stop("STOP: walltime_s must be an integer in [3600, 86400]")
    measured = spec.get("layout_measured_chunk_s")
    if measured is not None:
        if type(measured) not in (int, float) or measured <= 0:
            raise Stop("STOP: layout_measured_chunk_s must be positive")
        want = math.ceil(1.5 * measured)
        if wall != want:
            raise Stop(f"STOP: walltime_s must be 1.5x the re-measured chunk ({measured} s -> {want} s); got {wall}")
    for key, floor in (("request_disk_kb", 30314084), ("request_memory_mb", 10853)):
        v = spec.get(key)
        if type(v) is not int or v < floor or v > 100000000:
            raise Stop(f"STOP: {key} must be an integer >= {floor} (measured S2-C4 peak) and <= 1e8")

    label = resolve_label(spec)
    if label == "EVIDENCE" and paper["evidence_ready"] is not True:
        raise Stop("STOP: EVIDENCE requires paper.evidence_ready = true (the S2-M2 integration commit on main)")
    return {"run_id": run_id, "label": label, "kind": kind, "spec": spec}


# ------------------------------------------------------------------ label
def resolve_label(spec: dict) -> str:
    """Table label from the transferred authorization note only (never an index label; R1-SWEEP1-CLASSIFY)."""
    src = spec.get("label_source")
    if not isinstance(src, dict):
        raise Stop("STOP: label_source must be an object")
    if "sweep_index_label" in src or "index_label" in src:
        raise Stop("STOP: an index label may not select the table label (R1-SWEEP1-CLASSIFY defect)")
    auth = src.get("authorization")
    if auth is None:
        return "ENGINEERING_ONLY"
    name = _text(auth, "label_source.authorization", SAFE)
    sha = _text(_get(src, "authorization_sha256"), "label_source.authorization_sha256", SHA)
    path = Path(name)
    if path.is_absolute() or ".." in path.parts:
        raise Stop("STOP: label_source.authorization must be a job-relative file name")
    if not path.is_file():
        raise Stop("STOP: authorization note missing from the job sandbox (must be in transfer_input_files)")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != sha:
        raise Stop("STOP: authorization note sha256 mismatch")
    text = data.decode("utf-8", "replace")
    if not re.search(r"^approved:\s*true\s*$", text, re.M):
        raise Stop("STOP: authorization note is not approved")
    if _get(spec, "run_id") not in text:
        raise Stop("STOP: authorization note does not name this run id")
    if not re.search(r"label:\s*EVIDENCE\b", text):
        raise Stop("STOP: authorization note does not carry label EVIDENCE")
    return "EVIDENCE"


# ------------------------------------------------------------------ image / host / GPU / CPU
def site_identity(host: dict) -> dict:
    """R1-SWEEP-HOST-L40S-SITES: record the site/node; requirements no longer pin the site."""
    fqdn = str(host.get("fqdn") or host.get("hostname") or "")
    if fqdn.endswith(".nemo.privat"):
        site = "BwForCluster-Nemo2"
    elif fqdn.endswith("etp.kit.edu"):
        site = "portal"
    else:
        site = "unknown"
    return {"site": site, "fqdn": fqdn}


def image_identity(spec: dict) -> dict:
    versions = Path("/opt/r1/VERSIONS.txt")
    if not versions.is_file():
        raise Stop("STOP: /opt/r1/VERSIONS.txt missing (not the frozen image)")
    text = versions.read_text()
    for key, value in spec["image"]["versions_markers"].items():
        if not re.search(rf"^{re.escape(key)}={re.escape(value)}$", text, re.M):
            raise Stop(f"STOP: image identity marker {key}={value} missing")
    binary = Path(spec["server"]["binary"])
    if not binary.is_file():
        raise Stop(f"STOP: llama-server binary {binary} missing")
    got = hashlib.sha256(binary.read_bytes()).hexdigest()
    if got != spec["image"]["llama_server_sha256"]:
        raise Stop("STOP: llama-server binary sha256 differs from the frozen image pin")
    return {"versions_sha256": hashlib.sha256(versions.read_bytes()).hexdigest(),
            "llama_server_sha256": got, "spec_digest": spec["image"]["digest"]}


def host_identity() -> dict:
    name = socket.gethostname()
    try:
        fqdn = socket.getfqdn(name)
    except OSError:
        fqdn = name
    cpus = os.cpu_count() or 0
    if cpus < MIN_CPUS:
        raise Stop(f"STOP: landed with {cpus} CPUs, below the pinned class {MIN_CPUS}")
    return {"hostname": name, "fqdn": fqdn, "logical_cpus": cpus}


def _torch_python() -> str:
    p = Path("/opt/r1/envs/trackp/bin/python")
    return str(p if p.is_file() else sys.executable)


def gpu_identity(require_model: str | None = None) -> dict:
    code = ("import json,torch\nok=torch.cuda.is_available()\nout={'cuda_available':ok}\n"
            "if ok:\n p=torch.cuda.get_device_properties(0)\n out.update(name=str(p.name),\n"
            " uuid=(str(getattr(p,'uuid',None)) if getattr(p,'uuid',None) is not None else None),\n"
            " total_memory=int(p.total_memory), major=int(p.major), minor=int(p.minor),\n"
            " count=int(torch.cuda.device_count()))\n"
            "print(json.dumps(out))\n")
    res = subprocess.run([_torch_python(), "-B", "-c", code], capture_output=True, text=True, timeout=180)
    if res.returncode != 0:
        raise Stop(f"STOP: torch GPU query failed: {res.stderr.strip()[:300]}")
    info = json.loads(res.stdout.strip().splitlines()[-1])
    if not info.get("cuda_available"):
        raise Stop("STOP: CUDA unavailable in the job")
    total_bytes = int(info.get("total_memory") or 0)
    major, minor = info.get("major"), info.get("minor")
    if total_bytes < GPU_MIN_MEMORY_MB * 1024 * 1024:
        raise Stop(f"STOP: GPU {info.get('name')!r} has {total_bytes / 1024**3:.1f} GiB VRAM, below the 24 GB floor")
    if major is None or (int(major), int(minor or 0)) < (7, 0):
        raise Stop(f"STOP: GPU {info.get('name')!r} compute capability {major}.{minor} is below 7.0")
    return {"name": info["name"], "uuid": info.get("uuid") or _proc_gpu_uuid(), "driver": _driver_version(),
            "total_memory": total_bytes, "vram_mb": round(total_bytes / 1024**2),
            "compute_capability": [major, minor], "device_count": info.get("count")}


def _proc_gpu_uuid() -> str | None:
    for p in sorted(Path("/proc/driver/nvidia/gpus").glob("*/information")):
        m = re.search(r"^GPU UUID:\s*(\S+)$", p.read_text(errors="replace"), re.M)
        if m:
            return m.group(1)
    return None


def _driver_version() -> str | None:
    p = Path("/proc/driver/nvidia/version")
    if not p.is_file():
        return None
    text = p.read_text(errors="replace")
    for pattern in (r"Kernel Module\s+(\d+\.\d+(?:\.\d+)?)", r"Module[^\n]*?\s(\d+\.\d+\.\d+)\s+Release",
                    r"(\d+\.\d+\.\d+)"):
        m = re.search(pattern, text)
        if m:
            return m.group(1)
    return text.strip().splitlines()[0] if text.strip() else None


def cpu_identity(_unused: str | None = None) -> dict:
    cpuinfo = Path("/proc/cpuinfo")
    if not cpuinfo.is_file():
        raise Stop("STOP: /proc/cpuinfo missing (the job is not running on the batch Linux host)")
    text = cpuinfo.read_text(errors="replace")
    name = re.search(r"^model name\s*:\s*(.+)$", text, re.M)
    fam = re.search(r"^cpu family\s*:\s*(\d+)$", text, re.M)
    num = re.search(r"^model\s*:\s*(\d+)$", text, re.M)
    model = (name.group(1).strip() if name else "unknown")
    family = int(fam.group(1)) if fam else None
    number = int(num.group(1)) if num else None
    cores = len(re.findall(r"^processor\s*:", text, re.M))
    return {"model": model, "cpu_family": family, "cpu_model_number": number, "logical_cpus": cores,
            "recorded_only": True}


# ------------------------------------------------------------------ model / server / collector
def fetch_model(model: dict, dest: Path) -> dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    started = time.time(); h = hashlib.sha256(); size = 0
    with urllib.request.urlopen(model["url"], timeout=120) as resp, dest.open("wb") as fh:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            fh.write(chunk); h.update(chunk); size += len(chunk)
    seconds = time.time() - started
    if size != model["size"]:
        raise Stop(f"STOP: GGUF size {size} != pinned {model['size']}")
    if h.hexdigest() != model["sha256"]:
        raise Stop("STOP: GGUF sha256 mismatch")
    return {"path": str(dest), "size": size, "sha256": h.hexdigest(), "download_seconds": round(seconds, 1)}


MANAGED_FLAGS = {"--host", "--port", "-c", "--ctx-size", "-ngl", "--n-gpu-layers", "-m", "--model", "--alias",
                 "-lv", "--verbose", "-np", "--parallel"}


def build_server_argv(spec: dict, model_path: Path) -> list[str]:
    s = spec["server"]
    if MANAGED_FLAGS & set(s["extra_args"]):
        raise Stop("STOP: server.extra_args may not repeat managed flags")
    argv = [s["binary"], "-m", str(model_path), "--host", "127.0.0.1", "--port", str(s["port"]),
            "-c", str(CTX), "-ngl", str(NGL), "-np", str(NP), "-lv", "4", "--alias", spec["model"]["alias"]]
    return argv + list(s["extra_args"])


OFFLOAD_FULL = re.compile(r"offloaded (\d+)/(\d+) layers to GPU")
OFFLOAD_ANY = re.compile(r"offloaded (\d+)/(\d+)")


def offload_check(log_text: str) -> dict:
    """Full-offload check tolerant of the llama.cpp log wording; STOP if the log proves nothing."""
    cuda = [ln for ln in log_text.splitlines() if re.search(r"CUDA0|CUDA\s*:\s*ARCHS|ggml_cuda", ln)]
    m = OFFLOAD_FULL.search(log_text) or OFFLOAD_ANY.search(log_text)
    if not m:
        raise Stop("STOP: llama-server log has no offload counts; cannot prove full offload (keep the log)")
    done, total = int(m.group(1)), int(m.group(2))
    if done != total or "offloaded 0/" in log_text:
        raise Stop(f"STOP: llama-server is not fully offloaded ({done}/{total})")
    return {"offloaded_layers": done, "total_layers": total, "cuda_lines": cuda[-5:]}


BUILD_LINE = re.compile(r"version:\s*([^\n]+)")


def _parse_build(text: str) -> str:
    mm = BUILD_LINE.search(text)
    return mm.group(1).strip() if mm else ""


def server_build(binary: str) -> str:
    """llama-server prints its version line only for --version, not on startup."""
    try:
        res = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=90)
    except OSError as exc:
        raise Stop(f"STOP: cannot run {binary} --version: {exc}") from None
    if res.returncode != 0:
        raise Stop(f"STOP: {binary} --version failed rc={res.returncode}: {res.stderr.strip()[:300]}")
    build = _parse_build(res.stdout + "\n" + res.stderr)
    if not build:
        raise Stop(f"STOP: {binary} --version printed no version line")
    return build


def start_server(spec: dict, model_path: Path, log_path: Path) -> dict:
    argv = build_server_argv(spec, model_path)
    log = log_path.open("wb")
    proc = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    base = f"http://127.0.0.1:{spec['server']['port']}"
    try:
        deadline = time.time() + 300
        while time.time() < deadline:
            if proc.poll() is not None:
                raise Stop(f"STOP: llama-server exited rc={proc.returncode}")
            try:
                with urllib.request.urlopen(base + "/health", timeout=5) as r:
                    if r.status == 200:
                        break
            except Exception:
                time.sleep(2)
        else:
            raise Stop("STOP: llama-server health did not become ready")
    finally:
        log.close()
    text = log_path.read_text(errors="replace")
    try:
        build = server_build(spec["server"]["binary"])
    except Stop:
        _kill(proc)
        raise
    expected = spec["server"]["expected_build"]
    build_ok = build == expected or build == "version: " + expected or expected.endswith(build)
    if not build_ok:
        _kill(proc)
        raise Stop(f"STOP: llama-server build {build!r} != pinned {spec['server']['expected_build']!r}")
    try:
        off = offload_check(text)
    except Stop:
        _kill(proc)
        raise
    return {"proc": proc, "pid": proc.pid, "argv": argv, "base_url": base + "/v1", "build": build,
            "offloaded_layers": off["offloaded_layers"], "total_layers": off["total_layers"],
            "cuda_lines": off["cuda_lines"], "log": str(log_path)}


def _kill(proc) -> None:
    if proc is None:
        return
    if proc.poll() is None:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        try:
            proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


def clone_at(repo: str, commit: str, dest: Path) -> None:
    if dest.exists():
        raise Stop(f"STOP: scratch checkout {dest} already exists (fresh scratch required)")
    subprocess.run(["git", "init", "-q", str(dest)], check=True)
    subprocess.run(["git", "-C", str(dest), "remote", "add", "origin", repo], check=True)
    subprocess.run(["git", "-C", str(dest), "fetch", "-q", "--depth", "1", "origin", commit], check=True)
    subprocess.run(["git", "-C", str(dest), "checkout", "-q", "FETCH_HEAD"], check=True)
    got = subprocess.check_output(["git", "-C", str(dest), "rev-parse", "HEAD"], text=True).strip()
    if got != commit:
        raise Stop(f"STOP: retrieved commit {got} != pinned {commit}")


def _worker_env(paper_dir: Path, harness_dir: Path) -> dict:
    """Environment for the collector and its worker subprocesses: the harness venv's python3 must be first on
    PATH, otherwise node run_command 'python3 train.py' resolves to the container system Python (no numpy):
    that is exactly the 32k-smoke failure mode (worker success=False, metrics={}, 0.0 s)."""
    env = dict(os.environ, PYTHONPATH=str(paper_dir.resolve()), AR_HARNESS_ROOT=str(harness_dir.resolve()),
               OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
               PYTHONDONTWRITEBYTECODE="1")
    venv_bin = Path("/opt/r1/envs/harness/bin")
    if (venv_bin / "python3").is_file() or (venv_bin / "python").is_file():
        env["PATH"] = f"{venv_bin}:{env.get('PATH', '')}"
    elif (venv_bin / "python").is_file():
        env["PATH"] = f"{venv_bin}:{env.get('PATH', '')}"
    else:
        raise Stop(f"STOP: harness venv bin missing at {venv_bin} (worker python would be the system python)")
    env.pop("LLAMACPP_CACHE_PROMPT", None); env.pop("LLAMACACHE_PROMPT", None)
    return env


def collector_argv(spec: dict, label: str, resume: bool, paper_dir: Path | None = None) -> list[str]:
    c = spec["collector"]
    extra = {"c3_label_sweep": {"schema": "r1.c3_label_sweep/1", "memory_mode": c["memory_mode"],
                                "arm_role": "contrast" if c["memory_mode"] == "none" else "primary",
                                "label": label, "s2_c2": True, "backend": "llamacpp",
                                "noise_source": {"path": spec["noise_source"]["path"],
                                                 "sha256": spec["noise_source"]["sha256"]},
                                "audit": "none (ENGINEERING run: no B.2 audits; audit seeds 7001-7010 are "
                                         "reserved and untouched)",
                                "b2_audits": "none"}}
    argv = ["/opt/r1/envs/harness/bin/python", "-B", "-m", "r1.headroom.e1b_collect"]

    deadline = max(600, int(spec["walltime_s"]) - 600)
    e1 = (Path(paper_dir) if paper_dir else Path("paper")) / spec["noise_source"]["path"]
    argv += ["--deadline", str(deadline), "--e1-summary", str(e1.resolve()),
             "--manager", "langgraph", "--roots-only", "--points", "--reps", "0", "--audit-seeds", "0",
             "--nodes", c["node"], "--instances", str(c["instances"]), "--runs", "20",
             "--verify-split-policy", c["verify_split_policy"], "--new-campaign-versions",
             "--memory-mode", c["memory_mode"], "--transport-max-attempts", str(c["transport_max_attempts"]),
             "--manager-model", "llamacpp/" + spec["model"]["alias"], "--proposal-schema", c["proposal_schema"],
             "--root-failures", "record", "--extra-manifest", json.dumps(extra), "--workers", str(c["workers"]),
             "--out", str(Path("out").resolve()), "--work", str(Path("work").resolve()),
             "--label", label, "--split", "c3_labels"]
    return argv


# ------------------------------------------------------------------ job / seal
def _persist(record: dict, record_path: Path) -> None:
    record_path.write_text(json.dumps(record, indent=1) + "\n")
    _tar_dir(Path("out"), Path("out.tar"))
    _tar_dir(Path("work"), Path("work.tar"))
    _write_sums(Path("."))


def _stop_with_evidence(record: dict, record_path: Path, msg: str) -> None:
    record["stop"] = msg
    record["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _persist(record, record_path)
    raise Stop(msg)


def _binomial_allowed(n: int, p: float, alpha: float) -> int:
    """Largest failure count k with P(X >= k) > alpha for X~Bin(n,p): above it the run is statistically
    inconsistent with the sweep-1 per-(node, mode) failure baseline (small-n control for the 2-instance pilot)."""
    if n <= 0:
        return 0
    from math import comb
    if p <= 0:
        return 0
    if p >= 1:
        return n
    tail = 1.0
    for k in range(n, -1, -1):
        tail = sum(comb(n, j) * p**j * (1 - p)**(n - j) for j in range(k, n + 1))
        if tail > alpha:
            return k
    return 0


def collection_gates(out: Path, work: Path, node: str, instances: int) -> dict:
    """Sweep-1 collection gates (mirrors r1/scripts/c3_label_sweep.py): every outcome is written before a STOP."""
    out, work = Path(out), Path(work)
    manifest = json.loads((out / "manifest.json").read_text())
    expected = int(instances)
    roots = sorted((out / "roots").glob("*.json"))
    failure_dir = out / "failures"
    failures = [json.loads(path.read_text()) for path in sorted(failure_dir.glob("*.json"))] \
        if failure_dir.exists() else []
    calls, failed_calls, parse_failures, summaries, retried = [], [], [], [], []
    for path in sorted((work / "roots").rglob("root_events.jsonl")):
        for line in path.read_text(errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if item.get("event_type") == "llm_call":
                calls.append(item)
                if not (item.get("payload") or {}).get("parse_ok", True):
                    parse_failures.append(item)
                if len((item.get("payload") or {}).get("transport_attempts", [])) > 1:
                    retried.append({"trial_id": item.get("trial_id")})
            elif item.get("event_type") == "llm_call_failed":
                failed_calls.append({"trial_id": item.get("trial_id")})
    worker = {"roots": {}, "trials": 0, "successful": 0, "successful_with_metrics": 0,
              "failures": 0, "runtime_errors": 0, "skipped": 0, "failures_by_category": {}}
    for path in sorted((work / "roots").rglob("root_trials.jsonl")):
        root_name = path.parent.name
        root_trials = root_success = root_metrics = 0
        for line in path.read_text(errors="replace").splitlines():
            if not line.strip():
                continue
            trial = json.loads(line)
            summaries.append(trial.get("proposal_summary") or "")
            root_trials += 1
            if (((trial.get("extra") or {}).get("worker") or {}).get("worker_skipped") is True
                    or trial.get("decision") == "skipped"):
                worker["skipped"] += 1
                continue
            worker["trials"] += 1
            if trial.get("execution_status") == "success":
                root_success += 1; worker["successful"] += 1
                if trial.get("parsed_metrics"):
                    root_metrics += 1; worker["successful_with_metrics"] += 1
            else:
                worker["failures"] += 1
                cat = str(trial.get("failure_category") or "unknown")
                if cat == "runtime_error":
                    worker["runtime_errors"] += 1
                worker["failures_by_category"][cat] = worker["failures_by_category"].get(cat, 0) + 1
        worker["roots"][root_name] = {"trials": root_trials, "successful": root_success,
                                      "successful_with_metrics": root_metrics}
    worker["success_rate"] = round(worker["successful"] / worker["trials"], 6) if worker["trials"] else 0.0
    worker["failure_rate"] = round(1 - worker["success_rate"], 6) if worker["trials"] else 1.0
    check = {"label": manifest.get("label"), "memory_mode": (manifest.get("c3_label_sweep") or {}).get("memory_mode"),
             "node": node, "expected_roots": expected, "roots": len(roots), "root_failures": len(failures),
             "llm_calls": len(calls), "llm_calls_failed": len(failed_calls), "llm_calls_retried": len(retried),
             "parse_failures": len(parse_failures), "manager_kind": (manifest.get("manager") or {}).get("kind"),
             "worker": worker, "written_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    (out / "collection_checks.json").write_text(json.dumps(check, indent=2) + "\n")
    if failures or len(roots) != expected:
        (out / "collection_failures.json").write_text(json.dumps(
            {"n_failures": len(failures), "missing_roots": expected - len(roots), "failures": failures,
             "llm_calls_failed": failed_calls}, indent=2) + "\n")
        raise Stop(f"STOP: {len(failures)} root failures, {len(roots)}/{expected} roots complete")
    if (manifest.get("manager") or {}).get("kind") != "langgraph":
        raise Stop("STOP: sweep manifest is not LLM-backed")
    zero_success = [name for name, stats in worker["roots"].items() if stats["successful"] == 0]
    if zero_success:
        (out / "worker_failure.json").write_text(json.dumps(worker, indent=2) + "\n")
        raise Stop(f"STOP: {len(zero_success)} campaign(s) had zero successful worker runs "
                   f"(e.g. {zero_success[0]}); see out/worker_failure.json")
    if worker["successful_with_metrics"] == 0:
        (out / "worker_failure.json").write_text(json.dumps(worker, indent=2) + "\n")
        raise Stop("STOP: no successful worker run produced metrics (workers ran but training failed)")
    if worker["runtime_errors"] > 0:
        (out / "worker_failure.json").write_text(json.dumps(worker, indent=2) + "\n")
        raise Stop(f"STOP: {worker['runtime_errors']} worker runtime_error(s); sweep-1 had none "
                   "(infrastructure/worker failure)")
    mode = (manifest.get("c3_label_sweep") or {}).get("memory_mode")
    baseline = SWEEP1_WORKER_BASELINE.get((node, mode))
    if baseline is None:
        (out / "worker_failure.json").write_text(json.dumps(worker, indent=2) + "\n")
        raise Stop(f"STOP: no sweep-1 worker baseline for ({node}, {mode})")
    p_base = baseline["failures"] / baseline["worker_trials"] if baseline["worker_trials"] else 0.0
    observed = worker["failures"]
    n = worker["trials"]
    allowed = _binomial_allowed(n, p_base, WORKER_BINOMIAL_ALPHA)
    worker.update({"baseline": baseline, "baseline_failure_rate": round(p_base, 6),
                   "sweep1_success_rate": round(1 - p_base, 6),
                   "threshold_rate": round(p_base + WORKER_FAILURE_MARGIN, 6),
                   "binomial_allowed_failures": allowed})
    if n and worker["failure_rate"] > p_base + WORKER_FAILURE_MARGIN and observed > allowed:
        (out / "worker_failure.json").write_text(json.dumps(worker, indent=2) + "\n")
        raise Stop(f"STOP: worker failure rate {worker['failure_rate']:.3f} exceeds the sweep-1 baseline for "
                   f"{node}/{mode} {p_base:.3f} + {WORKER_FAILURE_MARGIN} (allowed failures <= {allowed})")
    if not calls or not any(not re.fullmatch(r"\w+\s+\S+\s+->\s+\S+", str(x)) for x in summaries):
        raise Stop("STOP: no demonstrated LLM proposals in the root ledgers")
    if len(parse_failures) / len(calls) > MAX_PARSE_FAILURE_RATE:
        (out / "parse_failure_examples.json").write_text(json.dumps(parse_failures[:5], indent=2) + "\n")
        raise Stop(f"STOP: parse failure rate {len(parse_failures)/len(calls):.3f} exceeds {MAX_PARSE_FAILURE_RATE}")
    return check


def _liveness_argv(spec: dict) -> list[str]:
    c = spec["liveness"]
    return ["/opt/r1/envs/harness/bin/python", "-B", "-m", "r1.liveness", "--run", "--manager", "langgraph",
            "--memory-mode", c["memory_mode"], "--nodes", *LIVENESS_NODES, "--instances", str(c["instances"]),
            "--runs", str(c["runs"]), "--transport-max-attempts", str(spec["collector"]["transport_max_attempts"]),
            "--manager-model", "llamacpp/" + spec["model"]["alias"], "--proposal-schema", "manager_proposal/v1",
            "--out", str(Path("out").resolve()), "--work", str(Path("work").resolve())]


def run_liveness(spec_path: Path) -> dict:
    validated = validate_spec(load_spec(spec_path))
    label = validated["label"]; s = validated["spec"]
    out, work, record_path = Path("out"), Path("work"), Path("job_record.json")
    record = {"schema": "s2_c2_job_record/1", "kind": "liveness", "run_id": validated["run_id"],
              "chunk_id": s["chunk_id"], "label": label, "image_digest": s["image"]["digest"],
              "model_sha256": s["model"]["sha256"], "paper_commit": s["paper"]["commit"],
              "harness_commit": s["harness"]["commit"],
              "b2_audits": "none (no B.2 audits; audit seeds 7001-7010 untouched)",
              "output_use": "ENGINEERING: never enters a label table, training or selection",
              "manager_settings": {"ctx": CTX, "np": NP, "ngl": NGL, "thinking": "off", "kv_cache": "q8_0",
                                   "cache_prompt": "false (LLAMACPP_CACHE_PROMPT/LLAMACACHE_PROMPT unset)"},
              "non_numeric_differences": non_numeric_differences(s["server"]["extra_args"]),
              "spec_liveness": s["liveness"],
              "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    record["image"] = image_identity(s)
    record["host"] = host_identity()
    record["gpu"] = gpu_identity()
    record["cpu"] = cpu_identity()
    paper_dir, harness_dir = Path("paper"), Path("harness")
    clone_at(s["paper"]["repo"], s["paper"]["commit"], paper_dir)
    clone_at(s["harness"]["repo"], s["harness"]["commit"], harness_dir)
    record["model"] = fetch_model(s["model"], Path("model.gguf"))
    server = start_server(s, Path("model.gguf"), Path("llama-server.log"))
    try:
        record["server"] = {k: server[k] for k in ("pid", "base_url", "build", "offloaded_layers",
                                                   "total_layers", "cuda_lines", "log")}
        argv = _liveness_argv(s)
        env = _worker_env(paper_dir, harness_dir)
        env["LLAMACPP_BASE_URL"] = server["base_url"]
        started = time.time()
        res = subprocess.run(argv, cwd=str(paper_dir.resolve()), env=env, capture_output=True, text=True)
        record["liveness_run"] = {"argv": argv, "returncode": res.returncode,
                                  "seconds": round(time.time() - started, 1),
                                  "stdout_tail": res.stdout[-4000:], "stderr_tail": res.stderr[-4000:]}
        if res.returncode != 0:
            _kill(server["proc"]); server["proc"] = None
            _stop_with_evidence(record, record_path, f"STOP: r1.liveness rc={res.returncode}; outputs kept")
        report = json.loads((out / "liveness.json").read_text())
        nodes = {n: bool((report.get("nodes", {}).get(n, {}) or {}).get("pass")) for n in LIVENESS_NODES}
        passes = [n for n in LIVENESS_NODES if nodes[n]]
        record["liveness_results"] = {"nodes": nodes, "live_nodes": len(passes), "min_live_nodes": MIN_LIVE_NODES}
        if len(passes) < MIN_LIVE_NODES:
            _kill(server["proc"]); server["proc"] = None
            _stop_with_evidence(record, record_path,
                                f"STOP: only {len(passes)} nodes passed D28 liveness (< {MIN_LIVE_NODES}); author decides")
    finally:
        _kill(server["proc"])
    record["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _persist(record, record_path)
    return record




def run_job(spec_path: Path) -> dict:
    spec = validate_spec(load_spec(spec_path))
    label = spec["label"]; s = spec["spec"]
    out, work = Path("out"), Path("work")
    record_path = Path("job_record.json")
    resume = False
    prior = ((out / "manifest.json").exists()
             or (record_path.is_file() and record_path.stat().st_size > 0)
             or (out.is_dir() and any(out.iterdir()))
             or (work.is_dir() and any(work.iterdir())))
    if prior:
        raise Stop("STOP: no resume path: a prior chunk exists in this sandbox; rerun the whole chunk in a new "
                   "directory (move the old one aside, do not delete) and disclose the rerun")
    record = {"schema": "s2_c2_job_record/1", "run_id": spec["run_id"], "chunk_id": s["chunk_id"], "label": label,
              "resume": False, "rerun_policy": "no resume; killed/non-clean chunk rerun whole in a new dir, old moved aside, disclosed",
              "label_rule": "authorization note only; index labels refused",
              "image_digest": s["image"]["digest"], "model_sha256": s["model"]["sha256"],
              "paper_commit": s["paper"]["commit"], "harness_commit": s["harness"]["commit"],
              "b2_audits": "none (no B.2 audits; audit seeds 7001-7010 untouched)",
              **({"output_use": "ENGINEERING: never enters a label table, training or selection; disclose in the "
                                "sweep-2 report as an engineering run (like the 19 Oct pilot)"}
                 if label == "ENGINEERING_ONLY" else {}),
              "manager_settings": {"temperature": "0.2 (D26 seed; manager-side config)",
                                   "cache_prompt": "false (harness default; LLAMACPP_CACHE_PROMPT/LLAMACACHE_PROMPT unset)",
                                   "thinking": "off (server chat-template-kwargs)",
                                   "kv_cache": "q8_0", "ctx": CTX, "n_gpu_layers": NGL, "np": NP},
              "non_numeric_differences": non_numeric_differences(s["server"]["extra_args"]),
              "level_layout": {"request_walltime_s": s["walltime_s"], "request_disk_kb": s["request_disk_kb"],
                               "request_memory_mb": s["request_memory_mb"]},
              "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    record["image"] = image_identity(s)
    record["host"] = host_identity()
    record["site"] = site_identity(record["host"])
    record["gpu"] = gpu_identity()
    record["cpu"] = cpu_identity()
    record["site_disclosure"] = ("requirements pin the L40S GPU model, not the site (R1-SWEEP-HOST-L40S-SITES); "
                                 "site/node/GPU name/UUID/driver/CPU model recorded per campaign; both CPU models "
                                 "are allowed and disclosed")
    paper_dir, harness_dir = Path("paper"), Path("harness")
    clone_at(s["paper"]["repo"], s["paper"]["commit"], paper_dir)
    clone_at(s["harness"]["repo"], s["harness"]["commit"], harness_dir)
    noise_file = paper_dir / s["noise_source"]["path"]
    if not noise_file.is_file():
        _stop_with_evidence(record, record_path, f"STOP: pinned noise source missing: {s['noise_source']['path']}")
    if hashlib.sha256(noise_file.read_bytes()).hexdigest() != NOISE_SHA:
        _stop_with_evidence(record, record_path, "STOP: pinned noise source sha256 mismatch")
    record["noise_source"] = {"path": s["noise_source"]["path"], "sha256": NOISE_SHA}
    record["model"] = fetch_model(s["model"], Path("model.gguf"))
    server = start_server(s, Path("model.gguf"), Path("llama-server.log"))
    try:
        record["server"] = {k: server[k] for k in ("pid", "base_url", "build", "offloaded_layers",
                                                   "total_layers", "cuda_lines", "log")}
        argv = collector_argv(s, label, resume, paper_dir)
        env = _worker_env(paper_dir, harness_dir)
        env["LLAMACPP_BASE_URL"] = server["base_url"]
        started = time.time()
        res = subprocess.run(argv, cwd=str(paper_dir.resolve()), env=env, capture_output=True, text=True)
        record["collector"] = {"argv": argv, "returncode": res.returncode,
                               "seconds": round(time.time() - started, 1),
                               "stdout_tail": res.stdout[-4000:], "stderr_tail": res.stderr[-4000:]}
    finally:
        _kill(server["proc"])
    if record["collector"]["returncode"] != 0:
        _stop_with_evidence(record, record_path, f"STOP: collector rc={record['collector']['returncode']}; outputs kept")
    record["chunk_wall_s"] = record["collector"]["seconds"]
    if record["chunk_wall_s"] > int(s["walltime_s"]):
        _stop_with_evidence(record, record_path,
                            f"STOP: chunk wall {record['chunk_wall_s']:.1f} s exceeds walltime {s['walltime_s']} s")
    manifest = json.loads((Path("out") / "manifest.json").read_text())
    recorded = (manifest.get("c3_label_sweep") or {}).get("noise_source")
    if recorded != {"path": s["noise_source"]["path"], "sha256": NOISE_SHA}:
        _stop_with_evidence(record, record_path, f"STOP: output manifest noise_source {recorded!r} != the pinned D28 summary")
    noise_manifest = manifest.get("noise") or {}
    if not isinstance(noise_manifest.get(s["collector"]["node"]), dict):
        _stop_with_evidence(record, record_path,
                            f"STOP: output manifest has no derived noise constants for {s['collector']['node']}")
    try:
        record["gates"] = collection_gates(Path("out"), Path("work"), s["collector"]["node"],
                                           int(s["collector"]["instances"]))
    except Stop as exc:
        record["gates"] = {"status": "FAIL", "error": str(exc)}
        _stop_with_evidence(record, record_path, str(exc))
    record["spec_liveness"] = s["liveness"]
    record["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _persist(record, record_path)
    return record


def non_numeric_differences(extra_args: list[str]) -> list[str]:
    diffs = []
    if "--no-webui" in extra_args:
        diffs.append("--no-webui (UI only, not numeric)")
    diffs.append("-lv 4 (log verbosity, not numeric)")
    return diffs


SUMMED_OUTPUTS = ("out.tar", "work.tar", "job_record.json", "llama-server.log")


def _tar_dir(src: Path, tar: Path) -> None:
    if src.is_dir():
        subprocess.run(["tar", "-cf", str(tar), "-C", str(src), "."], check=True)
    else:
        subprocess.run(["tar", "-cf", str(tar), "--files-from", "/dev/null"], check=True)


def _write_sums(root: Path) -> None:
    lines = []
    for name in SUMMED_OUTPUTS:
        p = root / name
        if not p.exists():
            continue
        files = [p] if p.is_file() else [q for q in sorted(p.rglob("*")) if q.is_file()]
        for f in files:
            lines.append(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(root)}")
    (root / "SHA256SUMS").write_text("\n".join(lines) + "\n")


def _sealed_target(run_id: str, chunk_id: str) -> Path:
    for name in (run_id, chunk_id):
        if not SAFE.fullmatch(name) or name in (".", ".."):
            raise Stop(f"STOP: invalid sealed path component {name!r}")
    for part in SEALED_ROOT.parts:
        if part in (".", ".."):
            raise Stop("STOP: sealed root may not contain '.' or '..'")
    if "r1_sealed" in SEALED_ROOT.parts:
        raise Stop("STOP: r1_sealed paths are refused")
    base = (SEALED_ROOT / run_id / chunk_id).resolve()
    want = (SEALED_ROOT / run_id / chunk_id)
    if not (base == want or want in base.parents):
        raise Stop(f"STOP: sealed target {base} is outside {SEALED_ROOT}/<run_id>/<chunk_id>")
    probe = base
    while probe != Path("/"):
        if probe.exists() and probe.is_symlink():
            raise Stop(f"STOP: sealed path component is a symlink: {probe}")
        probe = probe.parent
    return base


def seal(job_output: Path, run_id: str, chunk_id: str) -> dict:
    """Operator-side sealing: verify the transferred job record and copy into the sealed /ceph path (no overwrite)."""
    src = Path(job_output).resolve()
    record = json.loads((src / "job_record.json").read_text())
    if record.get("run_id") != run_id or record.get("chunk_id") != chunk_id:
        raise Stop("STOP: job record does not match the requested run/chunk")
    if record.get("label") not in ("ENGINEERING_ONLY", "EVIDENCE"):
        raise Stop("STOP: job record has an invalid label")
    if not record.get("image_digest", "").startswith("ghcr.io/"):
        raise Stop("STOP: job record has no pinned image digest")
    if not isinstance(record.get("host"), dict) or not record["host"].get("fqdn"):
        raise Stop("STOP: job record has no host identity")
    sums = src / "SHA256SUMS"
    if not sums.is_file():
        raise Stop("STOP: job output has no SHA256SUMS")
    check = subprocess.run(["sha256sum", "-c", "SHA256SUMS"], cwd=str(src), capture_output=True, text=True)
    if check.returncode != 0:
        raise Stop(f"STOP: transferred SHA256SUMS verification failed: {check.stdout[-2000:]}{check.stderr[-2000:]}")
    target = _sealed_target(run_id, chunk_id)
    if target.exists():
        raise Stop(f"STOP: sealed target exists; no overwrite ({target})")
    target.mkdir(parents=True, mode=0o700)
    for name in ("job_record.json", "SHA256SUMS", "llama-server.log"):
        p = src / name
        if p.exists():
            shutil.copy2(p, target / name)
    for name in ("out", "work"):
        tar = src / f"{name}.tar"
        if tar.exists():
            (target / name).mkdir(mode=0o700)
            subprocess.run(["tar", "-xf", str(tar), "-C", str(target / name)], check=True)
    lines = []
    for p in sorted(target.rglob("*")):
        if p.is_file() and p.name != "SHA256SUMS":
            lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(target)}")
    (target / "SHA256SUMS").write_text("\n".join(lines) + "\n")
    receipt = {"schema": "s2_c2_seal_receipt/1", "run_id": run_id, "chunk_id": chunk_id,
               "sealed_path": str(target), "label": record["label"], "image_digest": record["image_digest"],
               "model_sha256": record["model_sha256"], "host": record["host"].get("fqdn"),
               "sealed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    (target / "SEAL_RECEIPT.json").write_text(json.dumps(receipt, indent=1) + "\n")
    return receipt


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate"); v.add_argument("spec")
    r = sub.add_parser("run"); r.add_argument("spec")
    s = sub.add_parser("seal"); s.add_argument("job_output"); s.add_argument("--run-id", required=True)
    s.add_argument("--chunk-id", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "validate":
        spec = validate_spec(load_spec(Path(a.spec)))
        print(json.dumps({"ok": True, "run_id": spec["run_id"], "label": spec["label"]}))
        return 0
    if a.cmd == "run":
        kind = validate_spec(load_spec(Path(a.spec)))["kind"]
        record = run_liveness(Path(a.spec)) if kind == "liveness" else run_job(Path(a.spec))
        print(json.dumps({"ok": True, "label": record["label"], "host": record["host"]["fqdn"],
                          "gpu": record["gpu"]["name"], "model_sha256": record["model"]["sha256"]}))
        return 0
    print(json.dumps(seal(Path(a.job_output), a.run_id, a.chunk_id), indent=1))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Stop as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from None
