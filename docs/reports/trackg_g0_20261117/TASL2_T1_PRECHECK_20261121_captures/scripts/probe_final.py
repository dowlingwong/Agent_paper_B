"""R1-T1-HOST-TASL TASL-2 condition 7 (HARNESS_ISOLATION §3 item 7): end state — GPU before/after, no
leftovers, disk, host, versions.

Read-only.  Also hashes every capture file and writes ``SHA256SUMS`` for the capture directory (the report's
sibling ``_captures/SHA256SUMS`` is a copy of it).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def run(cmd: list[str], timeout: float = 60.0) -> dict:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {"cmd": cmd, "rc": out.returncode, "stdout": out.stdout.strip()[:40000],
                "stderr": out.stderr.strip()[:8000]}
    except (OSError, subprocess.SubprocessError) as error:
        return {"cmd": cmd, "rc": None, "error": f"{type(error).__name__}: {error}"}


def read(path: str, limit: int = 200_000) -> str:
    try:
        return Path(path).read_text(errors="replace")[:limit]
    except OSError as error:
        return f"<unreadable: {error}>"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def disk(path: str) -> dict:
    try:
        usage = shutil.disk_usage(path)
        return {"path": path, "total_bytes": usage.total, "free_bytes": usage.free,
                "free_gib": round(usage.free / 2**30, 1)}
    except OSError as error:
        return {"path": path, "error": str(error)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--captures", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--text", default="")
    ap.add_argument("--sums", default="")
    ap.add_argument("--gpu-before", default="", help="JSON file from probe_gpu with gpu_before")
    args = ap.parse_args()
    repo, base, captures = Path(args.repo), Path(args.base), Path(args.captures)

    # leftover processes: anything that names our run root, the probe scripts, the fake node, or a stray sleep.
    # Exclude ourselves and our ancestor chain (this probe and the run_checks.sh shell legitimately name the run
    # root), and any other probe_final process line.
    ancestors: set[int] = set()
    current = os.getpid()
    for _ in range(40):
        ancestors.add(current)
        try:
            stat_line = Path(f"/proc/{current}/stat").read_text()
            current = int(stat_line.rsplit(")", 1)[1].split()[1])
        except (OSError, IndexError, ValueError):
            break
        if current <= 1:
            break
    ps = run(["ps", "-u", str(os.getuid()), "-o", "pid,ppid,etime,stat,cmd", "--no-headers"])

    def own_line(line: str) -> bool:
        try:
            pid = int(line.split()[0])
        except (IndexError, ValueError):
            return True
        return pid in ancestors or "probe_final.py" in line

    leftovers = [line for line in ps.get("stdout", "").splitlines()
                 if not own_line(line) and any(token in line for token in
                        ("t1_precheck", "tasl2_t1_precheck", "probe_userns", "probe_cgroup",
                         "probe_interp", "probe_smoke", "probe_gpu", "probe_jax", "probe_env",
                         "probe_cpu_gpu", "isolated_fixture", "g0_userns_", "ar_sandbox",
                         "fake_isolated", "cpu_houseprice_like", "gpu_node_like"))]
    sleep_leftovers = [line for line in ps.get("stdout", "").splitlines()
                       if "sleep 30" in line or "sleep(30)" in line]
    cgroup_leftovers = [str(p) for p in Path("/sys/fs/cgroup").rglob("hostcheck_*")]
    cgroup_leftovers += [str(p) for p in Path("/sys/fs/cgroup").rglob("t1pre_*")]
    run_cgroup_leftovers = [str(p) for p in Path("/sys/fs/cgroup").rglob("*_20261*")]
    tmp_leftovers = sorted(str(p) for p in Path("/tmp").glob("g0_userns_*"))
    shm = sorted(os.listdir("/dev/shm")) if os.path.isdir("/dev/shm") else []

    gpu_before = {}
    if args.gpu_before and Path(args.gpu_before).exists():
        try:
            gpu_before = json.loads(Path(args.gpu_before).read_text()).get("gpu_before", {})
        except ValueError:
            gpu_before = {}

    result: dict = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": {"hostname": os.uname().nodename, "uname": read("/proc/version").strip(),
                 "kernel_release": os.uname().release, "boot_id": read(
                     "/proc/sys/kernel/random/boot_id").strip(),
                 "os_release": read("/etc/os-release")},
        "euid": os.geteuid(),
        "gpu_after": {
            "nvidia_smi_query": run(["nvidia-smi", "--query-gpu=index,uuid,driver_version,memory.total,"
                                     "memory.used,memory.free,utilization.gpu", "--format=csv,noheader"]),
            "compute_apps": run(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,process_name,used_memory",
                                 "--format=csv,noheader"]),
            "nvidia_smi_L": run(["nvidia-smi", "-L"]),
            "nv_driver": read("/proc/driver/nvidia/version").strip(),
        },
        "gpu_before": gpu_before,
        "leftovers": {
            "run_related_processes": leftovers,
            "sleep_leftovers": sleep_leftovers,
            "cgroup_hostcheck_dirs": cgroup_leftovers,
            "cgroup_run_dirs": run_cgroup_leftovers,
            "tmp_g0_userns_dirs": tmp_leftovers,
            "dev_shm": shm,
        },
        "disk": {p: disk(p) for p in ("/", "/home", "/home/dowling", str(base))},
        "tools": {
            "bash": run(["bash", "--version"]),
            "systemd": run(["systemd", "--version"]),
            "python3": run(["/usr/bin/python3", "-VV"]),
            "venv_torch312_python": run(["/home/dowling/r1_tracks/t1_tasl/envs/torch312/bin/python", "-VV"]),
            "venv_torch312_torch": run(["/home/dowling/r1_tracks/t1_tasl/envs/torch312/bin/python", "-c",
                                       "import torch;print(torch.__version__, torch.version.cuda, "
                                       "torch.cuda.is_available())"]),
            "venv_jax312_python": run(["/home/dowling/r1_tracks/t1_tasl/envs/jax312/bin/python", "-VV"]),
            "venv_jax312_jax": run(["/home/dowling/r1_tracks/t1_tasl/envs/jax312/bin/python", "-c",
                                   "import jax;print(jax.__version__, jax.default_backend(), "
                                   "jax.devices())"]),
            "uv": run(["/home/dowling/.local/bin/uv", "--version"]),
            "flock": run(["flock", "--version"]),
            "unshare": run(["unshare", "--version"]),
        },
        "repo": {
            "head": run(["git", "-C", str(repo), "rev-parse", "HEAD"]),
            "status_short": run(["git", "-C", str(repo), "status", "--short", "--branch"]),
            "status_porcelain": run(["git", "-C", str(repo), "status", "--porcelain"]),
            "expected_pin": "c025f89aeafc2199bf3487b4bcaa16678273c702",
        },
        "attempt1_archive": {
            "root": "/home/dowling/r1_trackp/runs/p3a_operator_20261027",
            "exists": os.path.isdir("/home/dowling/r1_trackp/runs/p3a_operator_20261027"),
            "stat": run(["stat", "-c", "%n %y %s", "/home/dowling/r1_trackp/runs/p3a_operator_20261027"])
            if os.path.isdir("/home/dowling/r1_trackp/runs/p3a_operator_20261027") else None,
        },
        "trackp_lease_log": {
            "path": "/home/dowling/r1_trackp/runs/_attempt1_gpu_lease_log.jsonl",
            "exists": os.path.exists(
                "/home/dowling/r1_trackp/runs/_attempt1_gpu_lease_log.jsonl"),
            "stat": run(["stat", "-c", "%n %y %s",
                         "/home/dowling/r1_trackp/runs/_attempt1_gpu_lease_log.jsonl"])
            if os.path.exists("/home/dowling/r1_trackp/runs/_attempt1_gpu_lease_log.jsonl") else None,
        },
        "records_tree": run(["find", str(base / "records"), "-maxdepth", "2", "-type", "d"]),
        "t1_tasl_tree": run(["find", "/home/dowling/r1_tracks/t1_tasl", "-maxdepth", "2", "-type", "d"]),
        "work_tree": run(["find", str(base / "work"), "-maxdepth", "2", "-type", "d"]),
    }
    result["no_leftovers"] = not (leftovers or sleep_leftovers or cgroup_leftovers
                                  or run_cgroup_leftovers or tmp_leftovers)
    # compare GPU idle state with the pre-GPU snapshot when we have it
    before_used = None
    try:
        before_used = int((gpu_before.get("nvidia_smi_query", {}).get("stdout", "0,,, ,,0,0,0")
                           .split(",")[4]).strip())
    except (ValueError, IndexError):
        before_used = None
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

    sums_lines = []
    for path in sorted(captures.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS":
            sums_lines.append(f"{sha256(path)}  {path.relative_to(captures)}")
    sums_text = "\n".join(sums_lines) + "\n"
    if args.sums:
        Path(args.sums).write_text(sums_text, encoding="utf-8")
    result["sha256sums"] = {"file": args.sums, "count": len(sums_lines)}
    out.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

    if args.text:
        Path(args.text).write_text(
            f"utc={result['utc']} host={result['host']['hostname']} kernel={result['host']['kernel_release']}\n"
            f"gpu_after={json.dumps(result['gpu_after'], default=str)}\n"
            f"gpu_before={json.dumps(gpu_before, default=str)}\n"
            f"no_leftovers={result['no_leftovers']} leftovers={json.dumps(result['leftovers'], default=str)}\n"
            f"disk={json.dumps(result['disk'], default=str)}\n"
            f"repo_head={result['repo']['head'].get('stdout')} status={result['repo']['status_short'].get('stdout')}\n"
            f"attempt1_archive={json.dumps(result['attempt1_archive'], default=str)}\n"
            f"tools={json.dumps({k: v.get('stdout') for k, v in result['tools'].items()}, default=str)}\n"
            f"sha256sums={args.sums} count={len(sums_lines)}\n",
            encoding="utf-8")
    print("RESULT " + json.dumps({"no_leftovers": result["no_leftovers"],
                                  "gpu_after": result["gpu_after"]["nvidia_smi_query"].get("stdout"),
                                  "compute_apps": result["gpu_after"]["compute_apps"].get("stdout"),
                                  "sha256_count": len(sums_lines),
                                  "leftover_counts": {k: len(v) for k, v in result["leftovers"].items()}},
                                 default=str))
    return 0 if result["no_leftovers"] else 1


if __name__ == "__main__":
    sys.exit(main())
