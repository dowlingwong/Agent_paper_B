"""R1-T1-HOST-TASL host-condition check: host/kernel/tool/GPU facts (condition 7 inputs).

Read-only.  Writes one JSON document; no GPU work, no cgroup work, no writes outside --out/--text.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import socket
import subprocess
import time
import uuid
from pathlib import Path


def read(path: str, limit: int = 200_000) -> str:
    try:
        return Path(path).read_text(errors="replace")[:limit]
    except OSError as error:
        return f"<unreadable: {error}>"


def run(cmd: list[str], timeout: float = 60.0) -> dict:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {"cmd": cmd, "rc": out.returncode, "stdout": out.stdout.strip()[:20_000],
                "stderr": out.stderr.strip()[:20_000]}
    except (OSError, subprocess.SubprocessError) as error:
        return {"cmd": cmd, "rc": None, "error": f"{type(error).__name__}: {error}"}


def sysctl(name: str) -> dict:
    path = "/proc/sys/" + name.replace(".", "/")
    value = read(path).strip()
    return {"name": name, "path": path, "value": value,
            "ok": not value.startswith("<unreadable")}


def disk(path: str) -> dict:
    try:
        usage = shutil.disk_usage(path)
        return {"path": path, "total_bytes": usage.total, "used_bytes": usage.used,
                "free_bytes": usage.free, "free_gib": round(usage.free / 2**30, 1)}
    except OSError as error:
        return {"path": path, "error": str(error)}


def gpu_state() -> dict:
    return {
        "nvidia_smi_L": run(["nvidia-smi", "-L"]),
        "nvidia_smi_query": run(["nvidia-smi", "--query-gpu=index,name,uuid,driver_version,"
                                 "memory.total,memory.used,memory.free,utilization.gpu,"
                                 "temperature.gpu,pstate", "--format=csv,noheader"]),
        "compute_apps": run(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,process_name,used_memory",
                             "--format=csv,noheader"]),
        "devices": sorted(p for p in os.listdir("/dev") if p.startswith("nvidia")) if os.path.isdir("/dev") else [],
        "driver_version_proc": read("/proc/driver/nvidia/version").strip(),
        "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "NVIDIA_VISIBLE_DEVICES": os.environ.get("NVIDIA_VISIBLE_DEVICES"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--text", default="")
    args = ap.parse_args()
    repo = Path(args.repo)
    venv_python = Path("/home/dowling/r1_tracks/t1_tasl/envs/torch312/bin/python")

    facts = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "local_time": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "hostname": socket.gethostname(),
        "fqdn": socket.getfqdn(),
        "uname": platform.uname()._asdict(),
        "os_release": read("/etc/os-release"),
        "uid": os.getuid(), "euid": os.geteuid(), "gid": os.getgid(), "groups": os.getgroups(),
        "user": run(["id"]),
        "home": os.environ.get("HOME"),
        "cwd": os.getcwd(),
        "boot_id": read("/proc/sys/kernel/random/boot_id").strip(),
        "cpu_count": os.cpu_count(),
        "meminfo_head": "\n".join(read("/proc/meminfo").splitlines()[:4]),
        "uptime": read("/proc/uptime").strip(),
        "lsm": read("/sys/kernel/security/lsm").strip(),
        "sysctls": {name: sysctl(name) for name in (
            "kernel.unprivileged_userns_clone",
            "kernel.apparmor_restrict_unprivileged_userns",
            "user.max_user_namespaces",
            "kernel.yama.ptrace_scope",
            "kernel.unprivileged_bpf_disabled",
            "kernel.kptr_restrict",
            "kernel.dmesg_restrict",
            "fs.protected_hardlinks",
            "fs.protected_symlinks",
        )},
        "cgroup": {
            "fs_type": run(["stat", "-fc", "%T", "/sys/fs/cgroup"]),
            "self": read("/proc/self/cgroup").strip(),
            "mountinfo": [line for line in read("/proc/self/mountinfo").splitlines()
                          if " /sys/fs/cgroup " in line][:3],
            "root_controllers": read("/sys/fs/cgroup/cgroup.controllers").strip(),
            "root_subtree_control": read("/sys/fs/cgroup/cgroup.subtree_control").strip(),
            "user_slice": [line for line in read("/proc/self/cgroup").splitlines()],
            f"user_{os.geteuid()}_slice_exists": os.path.isdir(
                f"/sys/fs/cgroup/user.slice/user-{os.geteuid()}.slice"),
            f"user_{os.geteuid()}_service_exists": os.path.isdir(
                f"/sys/fs/cgroup/user.slice/user-{os.geteuid()}.slice/user@{os.geteuid()}.service"),
        },
        "disk": {p: disk(p) for p in ("/", "/home", "/home/dowling", args.base)},
        "gpu": gpu_state(),
        "tools": {
            "bash": run(["bash", "--version"]),
            "systemd": run(["systemd", "--version"]),
            "systemd_run": run(["systemd-run", "--version"]),
            "systemctl_user_running": run(["systemctl", "--user", "is-system-running"]),
            "unshare": run(["unshare", "--version"]),
            "flock": run(["flock", "--version"]),
            "python3": run(["/usr/bin/python3", "-VV"]),
            "venv_python": run([str(venv_python), "-VV"]),
            "venv_python_executable": run([str(venv_python), "-c",
                                           "import sys; print(sys.executable)"]),
            "venv_torch": run([str(venv_python), "-c",
                               "import torch,sys; print('torch',torch.__version__,'cuda',"
                               "torch.version.cuda,'available',torch.cuda.is_available(),"
                               "sys.executable)"]),
            "nvcc": run(["nvcc", "--version"]),
            "git": run(["git", "--version"]),
        },
        "repo": {
            "path": str(repo),
            "head": run(["git", "-C", str(repo), "rev-parse", "HEAD"]),
            "describe": run(["git", "-C", str(repo), "describe", "--all", "--always"]),
            "status_short": run(["git", "-C", str(repo), "status", "--short", "--branch"]),
            "log_head": run(["git", "-C", str(repo), "log", "--oneline", "-5"]),
            "worktree_list": run(["git", "-C", str(repo), "worktree", "list"]),
            "base_repo": {
                "path": "/home/dowling/r1_trackp/autoresearch_harness",
                "head": run(["git", "-C", "/home/dowling/r1_trackp/autoresearch_harness",
                             "rev-parse", "HEAD"]),
                "branch": run(["git", "-C", "/home/dowling/r1_trackp/autoresearch_harness",
                               "branch", "--show-current"]),
            },
        },
        "env_selected": {k: v for k, v in sorted(os.environ.items())
                         if k.startswith(("AR_", "CUDA", "NVIDIA", "PYTHON", "HOME", "PATH",
                                          "XDG_", "DBUS_", "TMPDIR", "LANG"))},
        "limits": run(["bash", "-lc", "ulimit -a"]),
        "trackp_lease": {
            "r1_locks": read("/home/dowling/r1_locks") if os.path.isdir("/home/dowling/r1_locks")
            else "<absent>",
            "gpu0_lock_exists": os.path.exists("/home/dowling/r1_locks/gpu0.lock"),
            "trackx_marker_exists": os.path.exists("/home/dowling/r1_locks/trackx_evidence.active"),
        },
        "util": {"uuid": str(uuid.uuid4())},
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(facts, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if args.text:
        Path(args.text).write_text(
            f"stamp={facts['utc']} host={facts['hostname']} euid={facts['euid']} user={facts['user'].get('stdout')}\n"
            f"uname={facts['uname'].get('sysname')} {facts['uname'].get('release')} {facts['uname'].get('machine')}\n"
            f"os-release:\n{facts['os_release']}\n"
            f"lsm={facts['lsm']}\n"
            + "".join(f"{k}={v['value']}\n" for k, v in facts["sysctls"].items()) +
            f"cgroup_fs={facts['cgroup']['fs_type'].get('stdout')}\n"
            f"cgroup_self={facts['cgroup']['self']}\n"
            f"cgroup_mount={facts['cgroup']['mountinfo']}\n"
            f"disk={json.dumps(facts['disk'])}\n"
            f"gpu_L={facts['gpu']['nvidia_smi_L'].get('stdout')}\n"
            f"gpu_compute_apps={facts['gpu']['compute_apps'].get('stdout')!r}\n"
            f"nv_driver={facts['gpu']['driver_version_proc']}\n"
            f"repo_head={facts['repo']['head'].get('stdout')}\n"
            f"repo_status={facts['repo']['status_short'].get('stdout')}\n"
            f"python3={facts['tools']['python3'].get('stdout')}\n"
            f"venv_python={facts['tools']['venv_python'].get('stdout')}\n"
            f"venv_torch={facts['tools']['venv_torch'].get('stdout')}\n"
            f"systemd_run={facts['tools']['systemd_run'].get('stdout')}\n",
            encoding="utf-8")
    print(json.dumps({"ok": True, "out": str(out), "hostname": facts["hostname"],
                      "euid": facts["euid"], "repo_head": facts["repo"]["head"].get("stdout")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
