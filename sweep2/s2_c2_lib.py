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
GPU_MODEL = "NVIDIA L40S"
MACHINE_REGEX = r"^g36[0-9]{2}\.nemo\.privat$"
MIN_CPUS = 16
B2_HARNESS = "a3fedbbd44309b3fdf99d853ad841b9ec2c299e2"
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
    for flag, value in (("--jinja", None), ("--cache-type-k", "q8_0"), ("--cache-type-v", "q8_0"),
                        ("--chat-template-kwargs", None)):
        if flag not in extra:
            raise Stop(f"STOP: exam server flags require {flag} in server.extra_args")
        if value is not None and extra[extra.index(flag) + 1] != value:
            raise Stop(f"STOP: {flag} must be {value}")
    if "enable_thinking" not in extra[extra.index("--chat-template-kwargs") + 1]:
        raise Stop("STOP: --chat-template-kwargs must disable thinking")
    if server["ctx"] != 16384:
        raise Stop("STOP: ctx must be 16384 (exam setting)")

    col = _get(spec, "collector")
    _text(_get(col, "node"), "collector.node", SAFE)
    if _get(col, "memory_mode") not in ("append_only_summary", "none"):
        raise Stop("STOP: memory_mode must be append_only_summary or none")
    for key in ("instances", "runs", "workers", "transport_max_attempts"):
        v = _get(col, key)
        if type(v) is not int or v <= 0:
            raise Stop(f"STOP: collector.{key} must be a positive integer")
    if col["runs"] != 20:
        raise Stop("STOP: W = 20 worker runs is fixed (C3_DESIGN section 4)")
    if col["workers"] != MIN_CPUS:
        raise Stop(f"STOP: collector.workers must be {MIN_CPUS} (one per pinned CPU class core)")
    if _get(col, "proposal_schema") != "manager_proposal/v1":
        raise Stop("STOP: proposal_schema must be manager_proposal/v1 for the pick")
    if _get(col, "verify_split_policy") != "vary":
        raise Stop("STOP: verify_split_policy must be vary")

    req = _get(spec, "requirements")
    if _get(req, "cloud_site") != CLOUD_SITE:
        raise Stop(f"STOP: sweep-2 GPU jobs run on {CLOUD_SITE} only")
    if _get(req, "gpu_device_name") != GPU_MODEL:
        raise Stop(f"STOP: requirements pin the GPU model to {GPU_MODEL}")
    if _get(req, "machine_regex") != MACHINE_REGEX:
        raise Stop("STOP: machine_regex must equal the pinned CPU-class constant")
    if _get(req, "min_cpus") != MIN_CPUS:
        raise Stop(f"STOP: min_cpus must equal {MIN_CPUS} (pinned CPU class)")
    if "requires_etp_ceph" in req:
        raise Stop("STOP: NEMO2 slots do not advertise ProvidesEtpCeph; outputs transfer to the submit host and are sealed there")

    wall = spec.get("walltime_s")
    if type(wall) is not int or not 3600 <= wall <= 86400:
        raise Stop("STOP: walltime_s must be an integer in [3600, 86400]")

    label = resolve_label(spec)
    if label == "EVIDENCE" and paper["evidence_ready"] is not True:
        raise Stop("STOP: EVIDENCE requires paper.evidence_ready = true (the S2-M2 integration commit on main)")
    cpu_pin = req.get("cpu_model_contains")
    if label == "EVIDENCE" and not (isinstance(cpu_pin, str) and cpu_pin.strip()):
        raise Stop("STOP: EVIDENCE requires a non-empty requirements.cpu_model_contains (measured by S2-C4)")
    return {"run_id": run_id, "label": label, "spec": spec}


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
    if not re.fullmatch(MACHINE_REGEX, name) and not re.fullmatch(MACHINE_REGEX, fqdn):
        raise Stop(f"STOP: landed on host {fqdn!r} outside the pinned CPU-class machine regex")
    cpus = os.cpu_count() or 0
    if cpus < MIN_CPUS:
        raise Stop(f"STOP: landed with {cpus} CPUs, below the pinned class {MIN_CPUS}")
    return {"hostname": name, "fqdn": fqdn, "logical_cpus": cpus}


def _torch_python() -> str:
    p = Path("/opt/r1/envs/trackp/bin/python")
    return str(p if p.is_file() else sys.executable)


def gpu_identity(require_model: str) -> dict:
    code = ("import json,torch\nok=torch.cuda.is_available()\nout={'cuda_available':ok}\n"
            "if ok:\n p=torch.cuda.get_device_properties(0)\n out.update(name=p.name, uuid=getattr(p,'uuid',None),\n"
            " total_memory=p.total_memory, major=p.major, minor=p.minor, count=torch.cuda.device_count())\n"
            "print(json.dumps(out))\n")
    res = subprocess.run([_torch_python(), "-B", "-c", code], capture_output=True, text=True, timeout=180)
    if res.returncode != 0:
        raise Stop(f"STOP: torch GPU query failed: {res.stderr.strip()[:300]}")
    info = json.loads(res.stdout.strip().splitlines()[-1])
    if not info.get("cuda_available"):
        raise Stop("STOP: CUDA unavailable in the job")
    if require_model not in str(info.get("name", "")):
        raise Stop(f"STOP: GPU {info.get('name')!r} does not match the pinned model {require_model!r}")
    return {"name": info["name"], "uuid": info.get("uuid") or _proc_gpu_uuid(), "driver": _driver_version(),
            "total_memory": info.get("total_memory"), "compute_capability": [info.get("major"), info.get("minor")],
            "device_count": info.get("count")}


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
    m = re.search(r"Kernel Module\s+(\d+\.\d+(?:\.\d+)?)", text)
    if m:
        return m.group(1)
    return text.strip().splitlines()[0] if text.strip() else None


def cpu_identity(require_contains: str | None) -> dict:
    cpuinfo = Path("/proc/cpuinfo")
    if not cpuinfo.is_file():
        raise Stop("STOP: /proc/cpuinfo missing (the job is not running on the batch Linux host)")
    text = cpuinfo.read_text(errors="replace")
    m = re.search(r"^model name\s*:\s*(.+)$", text, re.M)
    model = (m.group(1).strip() if m else "unknown")
    cores = len(re.findall(r"^processor\s*:", text, re.M))
    if require_contains is not None and require_contains not in model:
        raise Stop(f"STOP: CPU model {model!r} does not contain the pinned class {require_contains!r}")
    return {"model": model, "logical_cpus": cores, "required_contains": require_contains}


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
                 "-lv", "--verbose"}


def build_server_argv(spec: dict, model_path: Path) -> list[str]:
    s = spec["server"]
    if MANAGED_FLAGS & set(s["extra_args"]):
        raise Stop("STOP: server.extra_args may not repeat managed flags")
    argv = [s["binary"], "-m", str(model_path), "--host", "127.0.0.1", "--port", str(s["port"]),
            "-c", str(s["ctx"]), "-ngl", str(s["n_gpu_layers"]), "-lv", "4", "--alias", spec["model"]["alias"]]
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
    m = re.search(r"version: ([^\n]+)", text)
    build = m.group(1) if m else ""
    if spec["server"]["expected_build"] not in build:
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


def collector_argv(spec: dict, label: str, resume: bool) -> list[str]:
    c = spec["collector"]
    extra = {"c3_label_sweep": {"schema": "r1.c3_label_sweep/1", "memory_mode": c["memory_mode"],
                                "arm_role": "contrast" if c["memory_mode"] == "none" else "primary",
                                "label": label, "s2_c2": True, "backend": "llamacpp",
                                "audit": "pending (r1/c3/audit.py)", "audit_seeds": [7001, 7002, 7003, 7004,
                                7005, 7006, 7007, 7008, 7009, 7010]}}
    argv = ["/opt/r1/envs/harness/bin/python", "-B", "-m", "r1.headroom.e1b_collect"]
    if resume:
        argv += ["--resume", str(Path("out").resolve())]
    deadline = max(600, int(spec["walltime_s"]) - 600)
    argv += ["--deadline", str(deadline), "--manager", "langgraph", "--roots-only", "--points", "--reps", "0", "--audit-seeds", "0",
             "--nodes", c["node"], "--instances", str(c["instances"]), "--runs", "20",
             "--verify-split-policy", c["verify_split_policy"], "--new-campaign-versions",
             "--memory-mode", c["memory_mode"], "--transport-max-attempts", str(c["transport_max_attempts"]),
             "--manager-model", "llamacpp/" + spec["model"]["alias"], "--proposal-schema", c["proposal_schema"],
             "--root-failures", "record", "--extra-manifest", json.dumps(extra), "--workers", str(c["workers"]),
             "--out", str(Path("out").resolve()), "--work", str(Path("work").resolve()),
             "--label", label, "--split", "c3_labels"]
    return argv


# ------------------------------------------------------------------ job / seal
def _check_resume_record(spec: dict, record_path: Path, label: str) -> None:
    old = json.loads(record_path.read_text())
    for key, new in (("label", label), ("image_digest", spec["image"]["digest"]),
                     ("model_sha256", spec["model"]["sha256"]), ("paper_commit", spec["paper"]["commit"]),
                     ("harness_commit", spec["harness"]["commit"])):
        if old.get(key) != new:
            raise Stop(f"STOP: resume pin mismatch for {key}: {old.get(key)!r} != {new!r}")


def _resume_state(out: Path, record_path: Path) -> bool:
    """A collector manifest means resume; a valid non-empty job record means resume; an empty placeholder
    (pre-created by the job entry) is a fresh run; a corrupt record is a STOP."""
    if (out / "manifest.json").is_file():
        return True
    if not record_path.is_file() or record_path.stat().st_size == 0:
        return False
    try:
        old = json.loads(record_path.read_text())
    except json.JSONDecodeError:
        raise Stop("STOP: existing job_record.json is unreadable; preserve the attempt (no overwrite)") from None
    if not isinstance(old, dict) or old.get("schema") != "s2_c2_job_record/1":
        raise Stop("STOP: existing job_record.json is not an S2-C2 record; preserve the attempt")
    return True


def run_job(spec_path: Path) -> dict:
    spec = validate_spec(load_spec(spec_path))
    label = spec["label"]; s = spec["spec"]
    out, work = Path("out"), Path("work")
    record_path = Path("job_record.json")
    resume = _resume_state(out, record_path)
    if resume:
        _check_resume_record(s, record_path, label)
    record = {"schema": "s2_c2_job_record/1", "run_id": spec["run_id"], "chunk_id": s["chunk_id"], "label": label,
              "resume": resume, "label_rule": "authorization note only; index labels refused",
              "image_digest": s["image"]["digest"], "model_sha256": s["model"]["sha256"],
              "paper_commit": s["paper"]["commit"], "harness_commit": s["harness"]["commit"],
              "manager_settings": {"temperature": "0.2 (D26 seed; manager-side config)",
                                   "cache_prompt": "false (harness default; LLAMACPP_CACHE_PROMPT/LLAMACACHE_PROMPT unset)",
                                   "thinking": "off (server chat-template-kwargs)",
                                   "kv_cache": "q8_0", "ctx": 16384},
              "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    record["image"] = image_identity(s)
    record["host"] = host_identity()
    record["gpu"] = gpu_identity(s["requirements"]["gpu_device_name"])
    record["cpu"] = cpu_identity(s["requirements"].get("cpu_model_contains"))
    record["model"] = fetch_model(s["model"], Path("model.gguf"))
    server = start_server(s, Path("model.gguf"), Path("llama-server.log"))
    try:
        record["server"] = {k: server[k] for k in ("pid", "base_url", "build", "offloaded_layers",
                                                   "total_layers", "cuda_lines", "log")}
        paper_dir, harness_dir = Path("paper"), Path("harness")
        clone_at(s["paper"]["repo"], s["paper"]["commit"], paper_dir)
        clone_at(s["harness"]["repo"], s["harness"]["commit"], harness_dir)
        argv = collector_argv(s, label, resume)
        env = dict(os.environ, PYTHONPATH=str(paper_dir.resolve()), AR_HARNESS_ROOT=str(harness_dir.resolve()),
                   LLAMACPP_BASE_URL=server["base_url"], OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                   MKL_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")
        env.pop("LLAMACPP_CACHE_PROMPT", None)
        env.pop("LLAMACACHE_PROMPT", None)
        started = time.time()
        res = subprocess.run(argv, cwd=str(paper_dir.resolve()), env=env, capture_output=True, text=True)
        record["collector"] = {"argv": argv, "returncode": res.returncode,
                               "seconds": round(time.time() - started, 1),
                               "stdout_tail": res.stdout[-4000:], "stderr_tail": res.stderr[-4000:]}
    finally:
        _kill(server["proc"])
    record["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    record_path.write_text(json.dumps(record, indent=1) + "\n")
    _write_sums(Path("."))
    if record["collector"]["returncode"] != 0:
        raise Stop(f"STOP: collector rc={record['collector']['returncode']}; outputs kept for sealing")
    return record


SUMMED_OUTPUTS = ("out", "work", "job_record.json", "llama-server.log")


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
    for name in ("out", "work", "job_record.json", "SHA256SUMS", "llama-server.log"):
        p = src / name
        if p.exists():
            (shutil.copytree if p.is_dir() else shutil.copy2)(p, target / name)
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
        record = run_job(Path(a.spec))
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
