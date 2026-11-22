"""TASL-2 AR-pin host check: host/kernel/tool/GPU/repo facts (HARNESS_ISOLATION section 3 item 7 inputs).

Read-only.  Writes one JSON document + a text summary; no GPU work, no cgroup work, no writes outside
--out/--text.
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
from pathlib import Path

PIN = "2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe"
SEVEN_PIN = "c025f89aeafc2199bf3487b4bcaa16678273c702"
VENV = "/home/dowling/r1_trackp/venvs/ar-cond7a/bin/python"
UV = "/home/dowling/.local/bin/uv"
GPU_UUID = "GPU-4d623e76-7587-ee15-a633-46f60d220d94"


def read(path: str, limit: int = 200_000) -> str:
    try:
        return Path(path).read_text(errors="replace")[:limit]
    except OSError as error:
        return f"<unreadable: {error}>"


def run(cmd: list[str], timeout: float = 60.0) -> dict:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {"cmd": cmd, "rc": out.returncode, "stdout": out.stdout.strip()[:40_000],
                "stderr": out.stderr.strip()[:10_000]}
    except (OSError, subprocess.SubprocessError) as error:
        return {"cmd": cmd, "rc": None, "error": f"{type(error).__name__}: {error}"}


def sysctl(name: str) -> dict:
    path = "/proc/sys/" + name.replace(".", "/")
    value = read(path).strip()
    return {"name": name, "path": path, "value": value, "ok": not value.startswith("<unreadable")}


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
        "driver_version_proc": read("/proc/driver/nvidia/version").strip(),
        "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "NVIDIA_VISIBLE_DEVICES": os.environ.get("NVIDIA_VISIBLE_DEVICES"),
    }


def repo_state(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {"path": path, "exists": False}
    return {
        "path": path, "exists": True,
        "head": run(["git", "-C", path, "rev-parse", "HEAD"]),
        "symbolic_ref_rc": run(["git", "-C", path, "symbolic-ref", "-q", "HEAD"])["rc"],
        "status_porcelain": run(["git", "-C", path, "status", "--porcelain"]),
        "status_porcelain_untracked_all": run(["git", "-C", path, "status", "--porcelain",
                                               "--untracked-files=all"]),
        "stash": run(["git", "-C", path, "stash", "list"]),
        "remote_origin": run(["git", "-C", path, "remote", "-v"]),
        "log_oneline_3": run(["git", "-C", path, "log", "--oneline", "-3"]),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--seven", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--text", default="")
    args = ap.parse_args()

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
            "user_1008_slice_exists": os.path.isdir("/sys/fs/cgroup/user.slice/user-1008.slice"),
            "user_1008_service_exists": os.path.isdir(
                "/sys/fs/cgroup/user.slice/user-1008.slice/user@1008.service"),
        },
        "disk": {p: disk(p) for p in ("/", "/home", "/home/dowling", args.base)},
        "gpu": gpu_state(),
        "gpu_expected_uuid": GPU_UUID,
        "tools": {
            "bash": run(["bash", "--version"]),
            "systemd": run(["systemd", "--version"]),
            "systemd_run": run(["systemd-run", "--version"]),
            "systemctl_user_running": run(["systemctl", "--user", "is-system-running"]),
            "unshare": run(["unshare", "--version"]),
            "flock": run(["flock", "--version"]),
            "python3": run(["/usr/bin/python3", "-VV"]),
            "uv": run([UV, "--version"]),
            "uv_python_find_3_12_15": run([UV, "python", "find", "3.12.15"]),
            "uv_python_find_3_12_16": run([UV, "python", "find", "3.12.16"]),
            "ar_cond7a_python_vv": run([VENV, "-VV"]),
            "ar_cond7a_python_version": run([VENV, "-c", "import sys; print(sys.version)"]),
            "ar_cond7a_executable": run([VENV, "-c", "import sys,os; print(sys.executable); "
                                                     "print(os.path.realpath(sys.executable))"]),
            "ar_cond7a_torch": run([VENV, "-c", "import torch; print(torch.__version__, "
                                                "torch.version.cuda, torch.cuda.is_available())"]),
            "ar_cond7a_symlink_chain": run(["readlink", "-f", VENV]),
            "nvcc": run(["nvcc", "--version"]),
            "git": run(["git", "--version"]),
        },
        "repos": {"harness_ar": repo_state(args.repo), "seven_node": repo_state(args.seven)},
        "expected": {"harness_ar_head": PIN, "seven_node_head": SEVEN_PIN},
        "repo_pin_matches": {},
        "t1_tasl_data": {"path": "/home/dowling/r1_tracks/t1_tasl/data",
                         "listing": sorted(os.listdir("/home/dowling/r1_tracks/t1_tasl/data"))
                         if os.path.isdir("/home/dowling/r1_tracks/t1_tasl/data") else "<absent>",
                         "ar_data_exists": os.path.lexists(
                             "/home/dowling/r1_tracks/t1_tasl/data/autoresearch_fixedtokens")},
        "t1_tasl_root": {"listing": sorted(os.listdir("/home/dowling/r1_tracks/t1_tasl"))
                         if os.path.isdir("/home/dowling/r1_tracks/t1_tasl") else "<absent>"},
        "lease": {
            "r1_locks_listing": run(["ls", "-la", "/home/dowling/r1_locks"])["stdout"],
            "gpu0_lock_exists": os.path.exists("/home/dowling/r1_locks/gpu0.lock"),
            "trackx_marker_exists": os.path.exists("/home/dowling/r1_locks/trackx_evidence.active"),
        },
        "attempt1_archive": {
            "root": "/home/dowling/r1_trackp/runs/p3a_operator_20261027",
            "stat": run(["stat", "-c", "%n %y %s", "/home/dowling/r1_trackp/runs/p3a_operator_20261027"]),
        },
        "trackp_lease_log": {
            "path": "/home/dowling/r1_trackp/runs/_attempt1_gpu_lease_log.jsonl",
            "stat": run(["stat", "-c", "%n %y %s",
                         "/home/dowling/r1_trackp/runs/_attempt1_gpu_lease_log.jsonl"]),
        },
        "running_jobs": run(["ps", "-u", str(os.getuid()), "-o", "pid,etime,cmd", "--no-headers"]),
        "env_selected": {k: v for k, v in sorted(os.environ.items())
                         if k.startswith(("AR_", "CUDA", "NVIDIA", "PYTHON", "HOME", "PATH",
                                          "XDG_", "DBUS_", "TMPDIR", "LANG", "HF_"))},
        "limits": run(["bash", "-lc", "ulimit -a"]),
    }
    for key in ("harness_ar", "seven_node"):
        state = facts["repos"][key]
        want = facts["expected"][f"{key}_head"]
        head = (state.get("head") or {}).get("stdout") if state.get("exists") else None
        facts["repo_pin_matches"][key] = {"expected": want, "head": head, "match": head == want}

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(facts, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if args.text:
        ts = facts["tools"]
        h = facts["repos"]["harness_ar"]
        s = facts["repos"]["seven_node"]
        Path(args.text).write_text(
            f"stamp={facts['utc']} local={facts['local_time']} host={facts['hostname']} "
            f"euid={facts['euid']} user={facts['user'].get('stdout')}\n"
            f"uname={facts['uname'].get('sysname')} {facts['uname'].get('release')} "
            f"{facts['uname'].get('machine')}\n"
            f"os-release:\n{facts['os_release']}\n"
            f"lsm={facts['lsm']}\n"
            + "".join(f"{k}={v['value']}\n" for k, v in facts["sysctls"].items()) +
            f"cgroup_fs={facts['cgroup']['fs_type'].get('stdout')}\n"
            f"cgroup_self={facts['cgroup']['self']}\n"
            f"cgroup_mount={facts['cgroup']['mountinfo']}\n"
            f"disk={json.dumps(facts['disk'])}\n"
            f"gpu_L={facts['gpu']['nvidia_smi_L'].get('stdout')}\n"
            f"gpu_compute_apps={facts['gpu']['compute_apps'].get('stdout')!r} "
            f"rc={facts['gpu']['compute_apps'].get('rc')}\n"
            f"nv_driver={facts['gpu']['driver_version_proc']}\n"
            f"uv={ts['uv'].get('stdout')}\n"
            f"python3={ts['python3'].get('stdout')}\n"
            f"ar_cond7a_python={ts['ar_cond7a_python_version'].get('stdout')}\n"
            f"ar_cond7a_executable={ts['ar_cond7a_executable'].get('stdout')}\n"
            f"ar_cond7a_torch={ts['ar_cond7a_torch'].get('stdout')}\n"
            f"harness_ar_head={(h.get('head') or {}).get('stdout')}\n"
            + ("harness_ar_status:\n" + ((h.get('status_porcelain') or {}).get('stdout') or '') + "\n"
               if h.get('exists') else "harness_ar: ABSENT\n") +
            f"seven_node_head={(s.get('head') or {}).get('stdout')}\n"
            + ("seven_node_status:\n" + ((s.get('status_porcelain') or {}).get('stdout') or '') + "\n"
               if s.get('exists') else "seven_node: ABSENT\n") +
            f"t1_tasl_data={json.dumps(facts['t1_tasl_data'])}\n"
            f"lease={json.dumps(facts['lease'])}\n"
            f"attempt1={json.dumps(facts['attempt1_archive'])}\n"
            f"trackp_lease_log={json.dumps(facts['trackp_lease_log'])}\n"
            f"systemd_run={ts['systemd_run'].get('stdout')}\n",
            encoding="utf-8")
    print(json.dumps({"ok": True, "out": str(out), "hostname": facts["hostname"],
                      "euid": facts["euid"], "repo_pin_matches": facts["repo_pin_matches"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
