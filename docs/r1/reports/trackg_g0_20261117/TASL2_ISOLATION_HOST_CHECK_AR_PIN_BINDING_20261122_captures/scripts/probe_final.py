"""TASL-2 AR-pin host check, condition 7 (HARNESS_ISOLATION section 3 item 7): end state at harness pin
2d09f9a9 -- GPU before/after, no leftovers in the six buckets, disk, host, versions, the two checkouts, the
attempt-1 archive (stat only) and the ar-cond7a interpreter evidence.

Read-only apart from its own JSON/text outputs.  The GPU "before" snapshot comes from the C6 probe
(``--gpu-before``); the "after" snapshot is taken here.
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

PIN = "2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe"
SEVEN_PIN = "c025f89aeafc2199bf3487b4bcaa16678273c702"
AR_PY = "/home/dowling/r1_trackp/venvs/ar-cond7a/bin/python"
DATA_ROOT = "/home/dowling/r1_tracks/t1_tasl/data/autoresearch_fixedtokens"
AR_NODE = "nodes/autoresearch_fixedtokens"


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


def repo_state(repo: str) -> dict:
    return {
        "path": repo,
        "head": run(["git", "-C", repo, "rev-parse", "HEAD"]),
        "symbolic_ref_rc": run(["git", "-C", repo, "symbolic-ref", "-q", "HEAD"])["rc"],
        "status_porcelain": run(["git", "-C", repo, "status", "--porcelain"]),
        "status_porcelain_untracked_all": run(["git", "-C", repo, "status",
                                               "--porcelain", "--untracked-files=all"]),
        "stash": run(["git", "-C", repo, "stash", "list"]),
        "log_oneline_2": run(["git", "-C", repo, "log", "--oneline", "-2"]),
    }


def _freeze_sha256(venv_python: str) -> str | None:
    """sha256 of the raw (unstripped) ``uv pip freeze`` stdout, as env_check.py compares it."""
    try:
        out = subprocess.run(["/home/dowling/.local/bin/uv", "pip", "freeze", "--python", venv_python],
                             capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.SubprocessError):
        return None
    return hashlib.sha256(out.stdout.encode("utf-8")).hexdigest() if out.returncode == 0 else None


def interpreter_evidence() -> dict:
    """The ar-cond7a interpreter's target chain and binary digest (read-only)."""
    venv_python = AR_PY
    links = {}
    for name in ("python", "python3", "python3.12"):
        path = Path("/home/dowling/r1_trackp/venvs/ar-cond7a/bin") / name
        links[name] = {"readlink": os.readlink(path) if path.is_symlink() else None,
                       "resolved": str(path.resolve()),
                       "exists": path.exists()}
    resolved = Path(venv_python).resolve()
    return {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "links": links,
        "pyvenv_cfg": read("/home/dowling/r1_trackp/venvs/ar-cond7a/pyvenv.cfg"),
        "resolved_interpreter": str(resolved),
        "interpreter_sha256": sha256(resolved) if resolved.is_file() else None,
        "interpreter_bytes": resolved.stat().st_size if resolved.is_file() else None,
        "version": run([venv_python, "-V"]).get("stdout"),
        "freeze_sha256": _freeze_sha256(venv_python),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--seven", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--captures", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--text", default="")
    ap.add_argument("--gpu-before", default="", help="JSON file from probe_gpu with gpu_before")
    args = ap.parse_args()
    repo, seven, base, captures = Path(args.repo), Path(args.seven), Path(args.base), Path(args.captures)

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

    leftover_tokens = ("tasl2_ar_pin", "ar_pin_hostcheck", "probe_userns", "probe_cgroup",
                       "probe_interp", "probe_smoke", "probe_gpu", "probe_host", "env_check",
                       "node_pins", "isolated_fixture", "ar_sandbox", "fake_isolated",
                       "gpu_probe", "c6_gpu")
    leftovers = [line for line in ps.get("stdout", "").splitlines()
                 if not own_line(line) and any(token in line for token in leftover_tokens)]
    sleep_leftovers = [line for line in ps.get("stdout", "").splitlines()
                       if "sleep 30" in line or "sleep(30)" in line]
    def safe_rglob(pattern: str) -> list[str]:
        try:
            return [str(p) for p in Path("/sys/fs/cgroup").rglob(pattern)]
        except OSError as error:
            return [f"<rglob error: {error}>"]

    cgroup_leftovers = safe_rglob("hostcheck_*") + safe_rglob("tasl2_ar_*")
    run_cgroup_leftovers = safe_rglob("*_20261*")
    tmp_leftovers = sorted(str(p) for p in Path("/tmp").glob("g0_userns_*"))
    shm = sorted(os.listdir("/dev/shm")) if os.path.isdir("/dev/shm") else []

    gpu_before = {}
    if args.gpu_before and Path(args.gpu_before).exists():
        try:
            gpu_before = json.loads(Path(args.gpu_before).read_text()).get("gpu_before", {})
        except ValueError:
            gpu_before = {}

    ar_state, seven_state = repo_state(str(repo)), repo_state(str(seven))
    data_manifest = Path(DATA_ROOT) / "data_manifest.json"
    data_link = repo / AR_NODE / "data"
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
            "ar_cond7a_python": run([AR_PY, "-VV"]),
            "ar_cond7a_version": run([AR_PY, "-c", "import sys; print(sys.version)"]),
            "ar_cond7a_torch": run([AR_PY, "-c",
                                    "import torch; print(torch.__version__, torch.version.cuda, "
                                    "torch.cuda.is_available())"]),
            "uv": run(["/home/dowling/.local/bin/uv", "--version"]),
            "flock": run(["flock", "--version"]),
            "unshare": run(["unshare", "--version"]),
        },
        "interpreter_evidence": interpreter_evidence(),
        "repo": ar_state,
        "seven_node": seven_state,
        "expected": {"harness_ar_head": PIN, "seven_node_head": SEVEN_PIN},
        "data": {
            "root": DATA_ROOT,
            "exists": Path(DATA_ROOT).is_dir(),
            "manifest": str(data_manifest),
            "manifest_sha256": sha256(data_manifest) if data_manifest.is_file() else None,
            "link": {
                "path": str(data_link),
                "is_symlink": data_link.is_symlink(),
                "readlink": os.readlink(data_link) if data_link.is_symlink() else None,
                "resolves_to": str(data_link.resolve()) if data_link.exists() else None,
            },
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
        "records_tree": run(["find", str(base / "records"), "-maxdepth", "2", "-type", "d"]),
        "t1_tasl_tree": run(["find", "/home/dowling/r1_tracks/t1_tasl", "-maxdepth", "2", "-type", "d"]),
        "work_tree": run(["find", str(base / "work"), "-maxdepth", "2", "-type", "d"]),
    }
    result["no_leftovers"] = not (leftovers or sleep_leftovers or cgroup_leftovers
                                  or run_cgroup_leftovers or tmp_leftovers)
    ar_head = (ar_state["head"] or {}).get("stdout")
    seven_head = (seven_state["head"] or {}).get("stdout")
    result["repo_checks"] = {
        "harness_ar_head_matches_pin": ar_head == PIN,
        "seven_node_head_matches_pin": seven_head == SEVEN_PIN,
        "harness_ar_untracked_all": (ar_state["status_porcelain_untracked_all"] or {}).get("stdout"),
        "seven_node_status": (seven_state["status_porcelain"] or {}).get("stdout"),
        "seven_node_untracked_all": (seven_state["status_porcelain_untracked_all"] or {}).get("stdout"),
        "data_link_is_only_untracked": ((ar_state["status_porcelain_untracked_all"] or {})
                                        .get("stdout") or "").strip() == f"?? {AR_NODE}/data",
    }
    result["condition_7_pass"] = bool(
        result["no_leftovers"] and result["repo_checks"]["harness_ar_head_matches_pin"]
        and result["repo_checks"]["seven_node_head_matches_pin"]
        and result["repo_checks"]["data_link_is_only_untracked"])

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if args.text:
        ie = result["interpreter_evidence"]
        Path(args.text).write_text(
            f"utc={result['utc']} host={result['host']['hostname']} kernel={result['host']['kernel_release']}\n"
            f"gpu_after={json.dumps(result['gpu_after'], default=str)}\n"
            f"gpu_before={json.dumps(gpu_before, default=str)}\n"
            f"no_leftovers={result['no_leftovers']} leftovers={json.dumps(result['leftovers'], default=str)}\n"
            f"disk={json.dumps(result['disk'], default=str)}\n"
            f"harness_ar_head={ar_head} matches_pin={result['repo_checks']['harness_ar_head_matches_pin']}\n"
            f"harness_ar_status_untracked_all={result['repo_checks']['harness_ar_untracked_all']!r}\n"
            f"seven_node_head={seven_head} matches_pin={result['repo_checks']['seven_node_head_matches_pin']}\n"
            f"seven_node_status={result['repo_checks']['seven_node_status']!r}\n"
            f"seven_node_untracked_all={result['repo_checks']['seven_node_untracked_all']!r}\n"
            f"data_link_is_only_untracked={result['repo_checks']['data_link_is_only_untracked']}\n"
            f"data_manifest_sha256={result['data']['manifest_sha256']}\n"
            f"interpreter={ie['resolved_interpreter']} sha256={ie['interpreter_sha256']} "
            f"bytes={ie['interpreter_bytes']} version={ie['version']} freeze_sha256={ie['freeze_sha256']}\n"
            f"interpreter_links={json.dumps(ie['links'], default=str)}\n"
            f"attempt1_archive={json.dumps(result['attempt1_archive'], default=str)}\n"
            f"trackp_lease_log={json.dumps(result['trackp_lease_log'], default=str)}\n"
            f"tools={json.dumps({k: v.get('stdout') for k, v in result['tools'].items()}, default=str)}\n"
            f"condition_7_pass={result['condition_7_pass']}\n",
            encoding="utf-8")
    print("RESULT " + json.dumps({"no_leftovers": result["no_leftovers"],
                                  "gpu_after": result["gpu_after"]["nvidia_smi_query"].get("stdout"),
                                  "compute_apps": result["gpu_after"]["compute_apps"].get("stdout"),
                                  "repo_checks": result["repo_checks"],
                                  "interpreter_evidence": {
                                      "resolved": result["interpreter_evidence"]["resolved_interpreter"],
                                      "sha256": result["interpreter_evidence"]["interpreter_sha256"],
                                      "bytes": result["interpreter_evidence"]["interpreter_bytes"],
                                      "version": result["interpreter_evidence"]["version"],
                                      "freeze_sha256": result["interpreter_evidence"]["freeze_sha256"]},
                                  "condition_7_pass": result["condition_7_pass"],
                                  "leftover_counts": {k: len(v) for k, v in result["leftovers"].items()}},
                                 default=str))
    return 0 if result["condition_7_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
