"""Small shared helpers for the R1-T1-HOST-H200 isolation host check (ENGINEERING_ONLY).

No repo imports here: the probe scripts import the accepted harness from the unpacked repos themselves.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import time
import traceback
from pathlib import Path


def utc_stamp() -> str:
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())


def read_text(path: str | Path, limit: int = 200000) -> str:
    try:
        return Path(path).read_text(errors="replace")[:limit]
    except OSError as error:
        return f"<unreadable: {error}>"


def write_json(path: str | Path, payload) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    tmp.replace(path)


def run(cmd: list[str], timeout: float = 120.0, **kw) -> dict:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, **kw)
        return {"cmd": cmd, "rc": out.returncode, "stdout": out.stdout[-20000:], "stderr": out.stderr[-20000:]}
    except (OSError, subprocess.SubprocessError) as error:
        return {"cmd": cmd, "rc": None, "error": f"{type(error).__name__}: {error}"}


def read_sysctl(name: str) -> dict:
    path = "/proc/sys/" + name.replace(".", "/")
    try:
        value = Path(path).read_text().strip()
        return {"name": name, "path": path, "value": value, "ok": True}
    except OSError as error:
        return {"name": name, "path": path, "value": None, "ok": False, "error": str(error)}


def mountinfo_lines(only: tuple[str, ...] = ()) -> list[str]:
    text = read_text("/proc/self/mountinfo")
    lines = text.splitlines()
    if not only:
        return lines
    return [line for line in lines if any(f" {p} " in line or line.split(" ")[4].startswith(p) for p in only)]


def host_facts() -> dict:
    uname = run(["uname", "-a"])
    facts = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hostname": socket.gethostname(),
        "fqdn": socket.getfqdn(),
        "uname": uname.get("stdout", "").strip(),
        "euid": os.geteuid(),
        "uid": os.getuid(),
        "gid": os.getgid(),
        "groups": os.getgroups(),
        "home": os.environ.get("HOME"),
        "cwd": os.getcwd(),
        "python": {
            "executable": __import__("sys").executable,
            "version": __import__("sys").version,
        },
        "os_release": read_text("/etc/os-release"),
        "container": {
            "APPTAINER_CONTAINER": os.environ.get("APPTAINER_CONTAINER"),
            "SINGULARITY_CONTAINER": os.environ.get("SINGULARITY_CONTAINER"),
            "SINGULARITY_NAME": os.environ.get("SINGULARITY_NAME"),
            "APPTAINER_NAME": os.environ.get("APPTAINER_NAME"),
            "conmon": os.environ.get("container"),
            ".dockerenv": os.path.exists("/.dockerenv"),
            ".singularity.d": os.path.isdir("/.singularity.d"),
            "pid1_comm": read_text("/proc/1/comm").strip() if os.path.exists("/proc/1/comm") else None,
        },
        "sysctls": {name: read_sysctl(name) for name in (
            "user.max_user_namespaces",
            "kernel.unprivileged_userns_clone",
            "kernel.apparmor_restrict_unprivileged_userns",
            "kernel.yama.ptrace_scope",
            "kernel.unprivileged_bpf_disabled",
            "kernel.kptr_restrict",
        )},
        "lsm": read_text("/sys/kernel/security/lsm").strip() if os.path.exists("/sys/kernel/security/lsm") else None,
        "cgroup_self": read_text("/proc/self/cgroup").strip(),
        "cgroup_fs": {
            "exists": os.path.isdir("/sys/fs/cgroup"),
            "controllers": read_text("/sys/fs/cgroup/cgroup.controllers").strip()
            if os.path.exists("/sys/fs/cgroup/cgroup.controllers") else None,
            "subtree_control": read_text("/sys/fs/cgroup/cgroup.subtree_control").strip()
            if os.path.exists("/sys/fs/cgroup/cgroup.subtree_control") else None,
            "nsdelegate_mount": [line for line in mountinfo_lines() if " /sys/fs/cgroup " in line][:3],
            "writable": os.access("/sys/fs/cgroup", os.W_OK),
        },
        "mounts": {
            "sysfs": [line for line in mountinfo_lines() if " /sys " in line][:4],
            "cgroup": [line for line in mountinfo_lines() if " /sys/fs/cgroup" in line][:6],
            "dev_shm": [line for line in mountinfo_lines() if " /dev/shm " in line][:2],
            "proc": [line for line in mountinfo_lines() if " /proc " in line][:2],
        },
        "gpu": {
            "nvidia_devices": sorted(p for p in os.listdir("/dev") if p.startswith("nvidia")) if os.path.isdir("/dev") else [],
            "driver_version": read_text("/proc/driver/nvidia/version").strip()
            if os.path.exists("/proc/driver/nvidia/version") else None,
            "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "NVIDIA_VISIBLE_DEVICES": os.environ.get("NVIDIA_VISIBLE_DEVICES"),
            "nvidia_smi_L": run(["nvidia-smi", "-L"], timeout=30),
        },
        "image": {
            "VERSIONS_txt": read_text("/opt/r1/VERSIONS.txt"),
            "LLAMA_SERVER_SHA256": read_text("/opt/r1/LLAMA_SERVER_SHA256").strip()
            if os.path.exists("/opt/r1/LLAMA_SERVER_SHA256") else None,
            "LLAMA_CPP_COMMIT": read_text("/opt/r1/LLAMA_CPP_COMMIT").strip()
            if os.path.exists("/opt/r1/LLAMA_CPP_COMMIT") else None,
        },
        "env_selected": {k: v for k, v in sorted(os.environ.items())
                         if k.startswith(("AR_", "_CONDOR", "CONDOR", "CUDA", "NVIDIA", "APPTAINER",
                                           "SINGULARITY", "PYTHON", "HOME", "PATH", "OMP_", "MKL_", "TMPDIR"))},
        "job_ad": read_text(os.environ.get("_CONDOR_JOB_AD", ""), limit=60000),
    }
    return facts


def guarded(name: str) -> dict:
    """Decorator-ish helper used by main(): returns a JSON-safe exception record."""
    return {"probe": name, "error": "unhandled exception", "traceback": traceback.format_exc()}
