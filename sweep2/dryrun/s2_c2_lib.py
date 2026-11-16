#!/usr/bin/env python3
"""S2-C2 sweep-2 HTCondor job wrapper (ENGINEERING until P1-P7; reviewed dry-run JDL).

One job == one (node, memory mode) chunk of sweep-2 root campaigns. Inside the container job this wrapper:
1. validates the job spec (pins, sealed output path, label source);
2. resolves the table label ONLY from the authorization note (or ENGINEERING_ONLY without one) - never from a
   sweep-index label (the R1-SWEEP1-CLASSIFY defect regression is tested);
3. verifies the frozen image identity (/opt/r1/VERSIONS.txt + llama-server binary hash);
4. records and pins the GPU (L40S) / CPU class / driver identity (torch + /proc, no nvidia-smi needed in v1);
5. fetches the pick GGUF and checks size+sha256, starts an owned llama-server with the exam flags, checks full
   offload, runs the harness root campaigns through r1.headroom.e1b_collect (llamacpp manager), records the job
   record, stops the server, writes SHA256SUMS - everything under the sealed /ceph/srv/dwong/paperb/sweep2/<run_id>/
   path. Raw labels are written sealed and never read here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

SCHEMA = "s2_c2_job/v1"
SEALED_ROOT = Path("/ceph/srv/dwong/paperb/sweep2")
CONTROL = re.compile(r"[\x00-\x1f\x7f]")
SHA = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
LABELS = ("ENGINEERING_ONLY", "EVIDENCE")


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
    """Return a normalised job description or raise Stop (fail-closed, before any network/CPU/GPU use)."""
    run_id = _text(_get(spec, "run_id"), "run_id", re.compile(r"^[A-Za-z0-9_.-]+$"))
    _text(_get(spec, "chunk_id"), "chunk_id", re.compile(r"^[A-Za-z0-9_.-]+$"))
    image = _get(spec, "image")
    digest = _text(_get(image, "digest"), "image.digest")
    if not re.fullmatch(r"ghcr\.io/[a-z0-9._/-]+@sha256:[0-9a-f]{64}", digest):
        raise Stop("STOP: image.digest must be a ghcr image pinned by sha256 digest")
    markers = _get(image, "versions_markers")
    if not isinstance(markers, dict) or not markers:
        raise Stop("STOP: image.versions_markers must be a nonempty object")
    for k, v in markers.items():
        _text(k, "image.versions_markers key")
        _text(v, f"image.versions_markers[{k}]")
    _text(_get(image, "llama_server_sha256"), "image.llama_server_sha256", SHA)

    paper = _get(spec, "paper")
    _text(_get(paper, "repo"), "paper.repo")
    _text(_get(paper, "commit"), "paper.commit", COMMIT)
    harness = _get(spec, "harness")
    _text(_get(harness, "repo"), "harness.repo")
    _text(_get(harness, "commit"), "harness.commit", COMMIT)

    model = _get(spec, "model")
    url = _text(_get(model, "url"), "model.url")
    if not url.startswith("https://huggingface.co/"):
        raise Stop("STOP: model.url must be the pinned HuggingFace URL")
    _text(_get(model, "sha256"), "model.sha256", SHA)
    size = _get(model, "size")
    if type(size) is not int or size <= 0:
        raise Stop("STOP: model.size must be a positive integer")
    _text(_get(model, "alias"), "model.alias", re.compile(r"^[A-Za-z0-9_.-]+$"))

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

    col = _get(spec, "collector")
    node = _text(_get(col, "node"), "collector.node", re.compile(r"^[A-Za-z0-9_.-]+$"))
    mode = _get(col, "memory_mode")
    if mode not in ("append_only_summary", "none"):
        raise Stop("STOP: collector.memory_mode must be append_only_summary or none")
    for key in ("instances", "runs", "workers", "transport_max_attempts"):
        v = _get(col, key)
        if type(v) is not int or v <= 0:
            raise Stop(f"STOP: collector.{key} must be a positive integer")
    if col["runs"] != 20:
        raise Stop("STOP: W = 20 worker runs is fixed (C3_DESIGN section 4)")
    _text(_get(col, "proposal_schema"), "collector.proposal_schema")
    if col["proposal_schema"] != "manager_proposal/v1":
        raise Stop("STOP: proposal_schema must be manager_proposal/v1 for the pick")
    _text(_get(col, "verify_split_policy"), "collector.verify_split_policy")
    if col["verify_split_policy"] != "vary":
        raise Stop("STOP: verify_split_policy must be vary")

    req = _get(spec, "requirements")
    if _get(req, "cloud_site") != "BwForCluster-Nemo2":
        raise Stop("STOP: sweep-2 GPU jobs run on NEMO2 only")
    if _get(req, "gpu_device_name") != "NVIDIA L40S":
        raise Stop("STOP: requirements pin the GPU model to NVIDIA L40S")
    machine = _text(_get(req, "machine_regex"), "requirements.machine_regex")
    try:
        re.compile(machine)
    except re.error as exc:
        raise Stop(f"STOP: requirements.machine_regex does not compile: {exc}") from None
    min_cpus = _get(req, "min_cpus")
    if type(min_cpus) is not int or min_cpus <= 0:
        raise Stop("STOP: requirements.min_cpus must be a positive integer")
    if _get(req, "requires_etp_ceph") is not True:
        raise Stop("STOP: sweep-2 jobs must require ETP ceph (sealed output)")

    label = resolve_label(spec)
    out = _get(spec, "output")
    root = Path(_text(_get(out, "root"), "output.root"))
    if not (root == SEALED_ROOT / run_id or SEALED_ROOT / run_id in root.parents):
        raise Stop(f"STOP: output.root must be under the sealed {SEALED_ROOT}/<run_id> path")
    if "r1_sealed" in root.parts:
        raise Stop("STOP: r1_sealed paths are not sweep-2 outputs (they are refused analysis inputs)")
    return {"run_id": run_id, "label": label, "output_root": root, "spec": spec}


# ------------------------------------------------------------------ label
def resolve_label(spec: dict) -> str:
    """The table label comes from the authorization note only; an index label is never used (R1-SWEEP1-CLASSIFY)."""
    src = spec.get("label_source") or {}
    if not isinstance(src, dict):
        raise Stop("STOP: label_source must be an object")
    if "sweep_index_label" in src or "index_label" in src:
        raise Stop("STOP: an index label may not select the table label (R1-SWEEP1-CLASSIFY defect)")
    auth = src.get("authorization")
    if auth is None:
        return "ENGINEERING_ONLY"
    path = Path(_text(auth, "label_source.authorization"))
    sha = _text(_get(src, "authorization_sha256"), "label_source.authorization_sha256", SHA)
    if not path.is_file():
        raise Stop("STOP: authorization note missing")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != sha:
        raise Stop("STOP: authorization note sha256 mismatch")
    text = data.decode("utf-8", "replace")
    if not re.search(r"^approved:\s*true\s*$", text, re.M):
        raise Stop("STOP: authorization note is not approved")
    run_id = _get(spec, "run_id")
    if run_id not in text:
        raise Stop("STOP: authorization note does not name this run id")
    if not re.search(r"label:\s*EVIDENCE\b", text):
        raise Stop("STOP: authorization note does not carry label EVIDENCE")
    return "EVIDENCE"


# ------------------------------------------------------------------ image / GPU / CPU
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
    return {"versions_sha256": hashlib.sha256(versions.read_bytes()).hexdigest(), "llama_server_sha256": got}


def _torch_env_python() -> str:
    p = Path("/opt/r1/envs/trackp/bin/python")
    return str(p if p.is_file() else sys.executable)


def gpu_identity(require_model: str) -> dict:
    code = (
        "import json,torch\n"
        "ok=torch.cuda.is_available()\n"
        "out={'cuda_available':ok}\n"
        "if ok:\n"
        " p=torch.cuda.get_device_properties(0)\n"
        " out.update(name=p.name, uuid=getattr(p,'uuid',None), total_memory=p.total_memory,\n"
        "            major=p.major, minor=p.minor, count=torch.cuda.device_count())\n"
        "print(json.dumps(out))\n"
    )
    res = subprocess.run([_torch_env_python(), "-B", "-c", code], capture_output=True, text=True, timeout=120)
    if res.returncode != 0:
        raise Stop(f"STOP: torch GPU query failed: {res.stderr.strip()[:300]}")
    info = json.loads(res.stdout.strip().splitlines()[-1])
    if not info.get("cuda_available"):
        raise Stop("STOP: CUDA unavailable in the job")
    if require_model not in str(info.get("name", "")):
        raise Stop(f"STOP: GPU {info.get('name')!r} does not match the pinned model {require_model!r}")
    uuid = info.get("uuid") or _proc_gpu_uuid()
    driver = _driver_version()
    return {"name": info["name"], "uuid": uuid, "driver": driver, "total_memory": info.get("total_memory"),
            "compute_capability": [info.get("major"), info.get("minor")], "device_count": info.get("count")}


def _proc_gpu_uuid() -> str | None:
    for p in sorted(Path("/proc/driver/nvidia/gpus").glob("*/information")):
        text = p.read_text(errors="replace")
        m = re.search(r"^GPU UUID:\s*(\S+)$", text, re.M)
        if m:
            return m.group(1)
    return None


def _driver_version() -> str | None:
    for p in (Path("/proc/driver/nvidia/version"),):
        if p.is_file():
            text = p.read_text(errors="replace")
            m = re.search(r"Kernel Module\s+(\S+)\s+(\S+)", text)
            return f"{m.group(1)} {m.group(2)}" if m else text.strip().splitlines()[0]
    return None


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


# ------------------------------------------------------------------ GGUF / server / collector
def fetch_model(model: dict, dest: Path) -> dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    with urllib.request.urlopen(model["url"], timeout=120) as resp, dest.open("wb") as fh:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            fh.write(chunk)
    seconds = time.time() - started
    size = dest.stat().st_size
    if size != model["size"]:
        raise Stop(f"STOP: GGUF size {size} != pinned {model['size']}")
    h = hashlib.sha256(dest.read_bytes()).hexdigest()
    if h != model["sha256"]:
        raise Stop("STOP: GGUF sha256 mismatch")
    return {"path": str(dest), "size": size, "sha256": h, "download_seconds": round(seconds, 1)}


MANAGED_FLAGS = {"--host", "--port", "-c", "--ctx-size", "-ngl", "--n-gpu-layers", "-m", "--model",
                 "--alias", "-lv", "--verbose"}


def build_server_argv(spec: dict, model_path: Path) -> list[str]:
    s = spec["server"]
    if MANAGED_FLAGS & set(s["extra_args"]):
        raise Stop("STOP: server.extra_args may not repeat managed flags")
    argv = [s["binary"], "-m", str(model_path), "--host", "127.0.0.1", "--port", str(s["port"]),
            "-c", str(s["ctx"]), "-ngl", str(s["n_gpu_layers"]), "-lv", "4", "--alias", spec["model"]["alias"]]
    return argv + list(s["extra_args"])


def start_server(spec: dict, model_path: Path, log_path: Path) -> dict:
    argv = build_server_argv(spec, model_path)
    log = log_path.open("wb")
    proc = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    base = f"http://127.0.0.1:{spec['server']['port']}"
    deadline = time.time() + 300
    try:
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
        _stop_process(proc)
        raise Stop(f"STOP: llama-server build {build!r} != pinned {spec['server']['expected_build']!r}")
    offload = re.search(r"offloaded (\d+)/(\d+) layers to GPU", text)
    if not offload or offload.group(1) != offload.group(2):
        _stop_process(proc)
        raise Stop("STOP: llama-server did not report full GPU offload")
    return {"proc": proc, "pid": proc.pid, "argv": argv, "base_url": base + "/v1", "build": build,
            "offloaded_layers": int(offload.group(1)), "total_layers": int(offload.group(2)), "log": str(log_path)}


def _stop_process(proc) -> None:
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
        raise Stop(f"STOP: scratch checkout {dest} already exists; the scratch must be fresh")
    subprocess.run(["git", "init", "-q", str(dest)], check=True)
    subprocess.run(["git", "-C", str(dest), "remote", "add", "origin", repo], check=True)
    subprocess.run(["git", "-C", str(dest), "fetch", "-q", "--depth", "1", "origin", commit], check=True)
    subprocess.run(["git", "-C", str(dest), "checkout", "-q", "FETCH_HEAD"], check=True)
    got = subprocess.check_output(["git", "-C", str(dest), "rev-parse", "HEAD"], text=True).strip()
    if got != commit:
        raise Stop(f"STOP: retrieved commit {got} != pinned {commit}")


def collector_argv(spec: dict, paper: Path, harness: Path, out: Path, work: Path, label: str, resume: bool) -> list[str]:
    c = spec["collector"]
    py = "/opt/r1/envs/harness/bin/python"
    extra = {"c3_label_sweep": {"schema": "r1.c3_label_sweep/1", "memory_mode": c["memory_mode"],
                                "arm_role": "contrast" if c["memory_mode"] == "none" else "primary",
                                "batch": str(Path.cwd()), "label": label, "s2_c2": True,
                                "backend": "llamacpp", "audit": "pending (r1/c3/audit.py)"}}
    argv = [py, "-B", "-m", "r1.headroom.e1b_collect"]
    if resume:
        argv += ["--resume", str(out)]
    argv += ["--manager", "langgraph", "--roots-only", "--points",
            "--reps", "0", "--audit-seeds", "0", "--nodes", c["node"], "--instances", str(c["instances"]),
            "--runs", "20", "--verify-split-policy", c["verify_split_policy"], "--new-campaign-versions",
            "--memory-mode", c["memory_mode"], "--transport-max-attempts", str(c["transport_max_attempts"]),
            "--manager-model", "llamacpp/" + spec["model"]["alias"], "--proposal-schema", c["proposal_schema"],
            "--root-failures", "record", "--extra-manifest", json.dumps(extra), "--workers", str(c["workers"]),
            "--out", str(out), "--work", str(work), "--label", label, "--split", "c3_labels"]
    return argv


def run_job(spec_path: Path, scratch: Path) -> dict:
    spec = validate_spec(load_spec(spec_path))
    label = spec["label"]
    run_dir = spec["output_root"] / spec["spec"]["chunk_id"]
    if run_dir.exists():
        out, work = run_dir / "out", run_dir / "work"
        if not (out / "manifest.json").exists():
            raise Stop(f"STOP: {run_dir} exists without a collector manifest; no overwrite/retry")
        resume = True
    else:
        run_dir.mkdir(parents=True, mode=0o700)
        out, work, resume = run_dir / "out", run_dir / "work", False
    record = {"schema": "s2_c2_job_record/1", "run_id": spec["run_id"], "chunk_id": spec["spec"]["chunk_id"],
              "label": label, "sealed": True, "resume": resume,
              "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    record["image"] = image_identity(spec["spec"])
    record["gpu"] = gpu_identity(spec["spec"]["requirements"]["gpu_device_name"])
    record["cpu"] = cpu_identity(spec["spec"]["requirements"].get("cpu_model_contains"))
    record["model"] = fetch_model(spec["spec"]["model"], scratch / "model.gguf")
    server = start_server(spec["spec"], scratch / "model.gguf", scratch / "llama-server.log")
    try:
        record["server"] = {k: server[k] for k in ("pid", "base_url", "build", "offloaded_layers", "total_layers", "log")}
        paper_dir, harness_dir = scratch / "paper", scratch / "harness"
        clone_at(spec["spec"]["paper"]["repo"], spec["spec"]["paper"]["commit"], paper_dir)
        clone_at(spec["spec"]["harness"]["repo"], spec["spec"]["harness"]["commit"], harness_dir)
        argv = collector_argv(spec["spec"], paper_dir, harness_dir, out, work, label, resume)
        env = dict(os.environ, PYTHONPATH=str(paper_dir), AR_HARNESS_ROOT=str(harness_dir),
                   LLAMACPP_BASE_URL=server["base_url"], OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                   MKL_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")
        started = time.time()
        res = subprocess.run(argv, cwd=paper_dir, env=env, capture_output=True, text=True)
        record["collector"] = {"argv": argv, "returncode": res.returncode,
                               "seconds": round(time.time() - started, 1),
                               "stdout_tail": res.stdout[-4000:], "stderr_tail": res.stderr[-4000:]}
    finally:
        _stop_process(server["proc"])
    record["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    (run_dir / "job_record.json").write_text(json.dumps(record, indent=1) + "\n")
    lines = []
    for p in sorted(run_dir.rglob("*")):
        if p.is_file() and p.name != "SHA256SUMS":
            lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(run_dir)}")
    (run_dir / "SHA256SUMS").write_text("\n".join(lines) + "\n")
    if record["collector"]["returncode"] != 0:
        raise Stop(f"STOP: collector rc={record['collector']['returncode']}; sealed record kept in {run_dir}")
    return record


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate"); v.add_argument("spec")
    r = sub.add_parser("run"); r.add_argument("spec"); r.add_argument("--scratch", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "validate":
        spec = validate_spec(load_spec(Path(a.spec)))
        print(json.dumps({"ok": True, "run_id": spec["run_id"], "label": spec["label"],
                          "sealed_root": str(spec["output_root"])}))
        return 0
    record = run_job(Path(a.spec), Path(a.scratch))
    print(json.dumps({"ok": True, "record": record.get("finished_utc"), "label": record["label"],
                      "gpu": record["gpu"]["name"], "model_sha256": record["model"]["sha256"]}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Stop as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from None
