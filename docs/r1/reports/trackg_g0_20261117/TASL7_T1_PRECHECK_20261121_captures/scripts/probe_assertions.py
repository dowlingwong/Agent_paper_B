"""R1-T1-HOST-TASL: the binding assertions of the G.1b plan §6 host check at harness pin c025f89a.

Read-only.  This is the machine-checked form of the report's ``host_check_*`` lines: the host is TASL-7, the
harness checkout is the pin and clean, the GPU is the named full UUID with no resident compute process, the
run is non-root, Yama ``ptrace_scope >= 1``, the census freezes are the expected bytes, the disk has room,
and there is no ``LD_LIBRARY_PATH``/``LD_PRELOAD`` in the environment the nodes are started from.

Writes only ``--out``/``--text``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

BASE = Path("/home/dowling/r1_tracks/t1_tasl")
HOST = "TASL-7"
PIN = "c025f89aeafc2199bf3487b4bcaa16678273c702"
PIN_TREE = "fa1526f44c79f9c5dcb6b84ed281814045b7add5"
PIN_BRANCH = "mac-trackg-t1-tasl-20261121"
MUST_CONTAIN = ("68cdd1ae2d46d2494ed6fbe69d7dd5693b5c643e",
                "5403392e94cb59d732f45d6702fc857531ad8fd5")
GPU_UUID = "GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1"
GPU_MODEL = "NVIDIA GeForce RTX 4090"
FREEZE_SHA = {
    "torch312": "d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42",
    "jax312": "80a455c6f46042aa245356050f965a303cf1e1e85f125acc9d6cbde7c08dcac1",
}
LEAKY = ("LD_LIBRARY_PATH", "LD_PRELOAD", "LD_AUDIT")
MIN_FREE_GIB = 100.0


def run(cmd: list[str], timeout: float = 120.0) -> dict:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {"cmd": cmd, "rc": out.returncode, "stdout": out.stdout, "stderr": out.stderr[-4000:]}
    except (OSError, subprocess.SubprocessError) as error:
        return {"cmd": cmd, "rc": None, "stdout": "", "stderr": f"{type(error).__name__}: {error}"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def disk(path: Path) -> dict:
    try:
        usage = shutil.disk_usage(path)
        return {"path": str(path), "total_bytes": usage.total, "free_bytes": usage.free,
                "free_gib": round(usage.free / 2**30, 1)}
    except OSError as error:
        return {"path": str(path), "error": str(error)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=str(BASE))
    ap.add_argument("--host", default=HOST)
    ap.add_argument("--pin", default=PIN)
    ap.add_argument("--pin-tree", default=PIN_TREE)
    ap.add_argument("--gpu-uuid", default=GPU_UUID)
    ap.add_argument("--out", required=True)
    ap.add_argument("--text", default="")
    args = ap.parse_args()
    base = Path(args.base)
    repo = base / "harness"
    facts: dict = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "hostname": os.uname().nodename, "euid": os.geteuid(),
                   "base": str(base), "repo": str(repo), "ld_vars": {k: os.environ.get(k) for k in LEAKY},
                   "disks": {p: disk(Path(p)) for p in ("/", "/home", str(base))},
                   "gpu": {
                       "nvidia_smi_L": run(["nvidia-smi", "-L"]),
                       "nvidia_smi_query": run(["nvidia-smi", "--query-gpu=index,name,uuid,driver_version,"
                                                "memory.total,memory.used,utilization.gpu,temperature.gpu",
                                                "--format=csv,noheader"]),
                       "compute_apps": run(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,"
                                            "process_name,used_memory", "--format=csv,noheader"]),
                       "driver_version": Path("/proc/driver/nvidia/version").read_text(errors="replace")
                       if Path("/proc/driver/nvidia/version").exists() else None,
                   },
                   "ptrace": run(["bash", "-c", "cat /proc/sys/kernel/yama/ptrace_scope"]),
                   "sysctls": {name: run(["bash", "-c", f"cat /proc/sys/{name.replace('.', '/')}"])
                               for name in ("kernel.yama.ptrace_scope",
                                            "kernel.unprivileged_userns_clone",
                                            "kernel.apparmor_restrict_unprivileged_userns",
                                            "user.max_user_namespaces")},
                   "cgroup": {
                       "fs_type": run(["stat", "-fc", "%T", "/sys/fs/cgroup"]),
                       "mountinfo": run(["bash", "-c",
                                        "grep ' /sys/fs/cgroup ' /proc/self/mountinfo | head -3"]),
                       "root_controllers": run(["bash", "-c", "cat /sys/fs/cgroup/cgroup.controllers"]),
                       "user_slice_exists": os.path.isdir(f"/sys/fs/cgroup/user.slice/user-{os.geteuid()}.slice"),
                   },
                   "repo": {
                       "head": run(["git", "-C", str(repo), "rev-parse", "HEAD"]),
                       "tree": run(["git", "-C", str(repo), "rev-parse", "HEAD^{tree}"]),
                       "status_porcelain": run(["git", "-C", str(repo), "status", "--porcelain"]),
                       "branch": run(["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"]),
                       "log_head": run(["git", "-C", str(repo), "log", "--oneline", "-6"]),
                       "ancestry": {c: run(["git", "-C", str(repo), "merge-base", "--is-ancestor", c,
                                            args.pin]) for c in MUST_CONTAIN},
                   },
                   "freezes": {}, "uv": {},
                   }
    # freezes (file bytes only; the installed set is probe_envs.py's job)
    for name, expected in FREEZE_SHA.items():
        path = base / "base" / f"{name}.freeze.txt"
        facts["freezes"][name] = {"path": str(path), "exists": path.exists(),
                                  "expected_sha256": expected,
                                  "sha256": sha256(path) if path.exists() else None}
    uv = "/home/dowling/.local/bin/uv"
    facts["uv"] = {"path": uv, "exists": os.path.exists(uv),
                   "version": run([uv, "--version"]) if os.path.exists(uv) else None,
                   "python_find": run([uv, "python", "find", "3.12.16"]) if os.path.exists(uv) else None}
    # the GPU UUID from nvidia-smi -L (full UUID, not an index)
    smi_lines = [ln.strip() for ln in (facts["gpu"]["nvidia_smi_L"].get("stdout") or "").splitlines() if ln.strip()]
    uuids = [ln.split("UUID: ")[-1].strip().rstrip(")") for ln in smi_lines] if smi_lines else []
    query = [ln.strip() for ln in (facts["gpu"]["nvidia_smi_query"].get("stdout") or "").splitlines() if ln.strip()]
    names = [q.split(",")[1].strip() for q in query if len(q.split(",")) > 1] if query else []
    apps = (facts["gpu"]["compute_apps"].get("stdout") or "").strip()
    try:
        ptrace_scope = int((facts["ptrace"].get("stdout") or "").strip())
    except ValueError:
        ptrace_scope = None
    head = (facts["repo"]["head"].get("stdout") or "").strip()
    tree = (facts["repo"]["tree"].get("stdout") or "").strip()
    status = (facts["repo"]["status_porcelain"].get("stdout") or "").strip()
    branch = (facts["repo"]["branch"].get("stdout") or "").strip()
    ancestry = {c: (v.get("rc") == 0) for c, v in facts["repo"]["ancestry"].items()}
    checks = {
        "host_is_TASL7": os.uname().nodename == args.host,
        "non_root": os.geteuid() != 0,
        "gpu_full_uuid_expected": uuids == [args.gpu_uuid],
        "gpu_model_rtx4090": names == [GPU_MODEL],
        "no_resident_compute_process": apps == "",
        "ptrace_scope_ge_1": bool(ptrace_scope is not None and ptrace_scope >= 1),
        "harness_head_is_pin": head == args.pin,
        "harness_tree_is_pin_tree": tree == args.pin_tree,
        "harness_clean": status == "",
        "harness_detached": branch == "HEAD",
        "harness_contains_isolation_core": ancestry.get(MUST_CONTAIN[0], False),
        "harness_contains_ada_fix": ancestry.get(MUST_CONTAIN[1], False),
        "cgroup2_mounted": (facts["cgroup"]["fs_type"].get("stdout") or "").strip() in ("cgroup2", "cgroup2fs"),
        "cgroup_nsdelegate": "nsdelegate" in (facts["cgroup"]["mountinfo"].get("stdout") or ""),
        "user_slice_exists": bool(facts["cgroup"]["user_slice_exists"]),
        "freezes_are_expected_bytes": all(v["sha256"] == v["expected_sha256"]
                                          for v in facts["freezes"].values()),
        "ld_vars_empty": all(not os.environ.get(k) for k in LEAKY),
        "uv_013_6": "0.13.6" in (facts["uv"]["version"] or {}).get("stdout", "") if facts["uv"]["version"] else False,
        "uv_python_3_12_16": "3.12.16" in (facts["uv"]["python_find"].get("stdout") or ""),
        "disk_free_ge_100_gib": all(v.get("free_gib", 0) >= MIN_FREE_GIB for v in facts["disks"].values()),
    }
    facts["checks"] = checks
    facts["condition_assertions_pass"] = all(checks.values())
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(facts, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if args.text:
        lines = [f"utc={facts['utc']} hostname={facts['hostname']} euid={facts['euid']}",
                 f"nvidia-smi_L={facts['gpu']['nvidia_smi_L'].get('stdout', '').strip()}",
                 f"gpu_uuids={uuids}",
                 f"gpu_model={names}",
                 f"compute_apps={(apps or '<empty>')!r}",
                 f"ptrace_scope={ptrace_scope}",
                 f"harness_head={head} tree={tree} branch={branch} status_clean={status == ''}",
                 f"ancestry={ancestry}",
                 f"freezes={json.dumps(facts['freezes'], sort_keys=True)}",
                 f"ld_vars={facts['ld_vars']}",
                 f"disks={json.dumps(facts['disks'], sort_keys=True)}",
                 f"cgroup_fs={(facts['cgroup']['fs_type'].get('stdout') or '').strip()} "
                 f"nsdelegate={'nsdelegate' in (facts['cgroup']['mountinfo'].get('stdout') or '')}"] + \
                [f"{k}={v}" for k, v in checks.items()] + \
                [f"condition_assertions_pass={facts['condition_assertions_pass']}"]
        Path(args.text).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("RESULT " + json.dumps({"condition_assertions_pass": facts["condition_assertions_pass"],
                                  "checks": checks, "gpu_uuids": uuids, "apps": apps,
                                  "head": head}, default=str))
    return 0 if facts["condition_assertions_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
