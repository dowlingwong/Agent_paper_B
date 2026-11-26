#!/usr/bin/env python3
"""U2 preflight for the reviewed MLGym Titanic kit ``mlgym_titanic`` (TASL-2, CPU-only).

Read-only: binds the branch/pin, recomputes every accepted pin from the committed tree with the
kit's own helpers, re-checks the data root / link / read-only bits / file hashes, re-checks the
pinned ``torch312`` freeze, records the host/cgroup/affinity/CPU-only registration and the GPU +
lease state, and writes the capture set into ``$BASE/raw``.  It executes **no** smoke run.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

HOME = Path.home()
H = Path("/home/dowling/r1_trackp/wt/titanic-20261125")
NODE = "mlgym_titanic"
NODE_DIR = H / "third_party/mlgym/nodes/mlgym_titanic"
SPEC_PATH = H / "third_party/mlgym/configs/trackg/nodes/mlgym_titanic.yaml"
DATA_ROOT = Path("/home/dowling/r1_engineering/titanic_20261125/data")
BASE = Path(os.environ.get("U2_BASE",
                          "/home/dowling/r1_engineering/titanic_20261125/u2_census_smoke_20261125"))
RAW = BASE / "raw"
PY = "/home/dowling/r1_tracks/t1_tasl/envs/torch312/bin/python"
UV = str(HOME / ".local/bin/uv")

PIN = "3a67042ba7e4211feb9681524f3879643c8cf635"
BASE_COMMIT = "c025f89aeafc2199bf3487b4bcaa16678273c702"
BRANCH = "mac-trackg-titanic-20261125"
FREEZE_SHA = "d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42"
EQ = {
    "node_spec_sha256": "059fd0d50059b4627382979fc9064a9f223f79e06b616eba195eefbb3f3380c1",
    "spec_raw_sha256": "08876175e02d498b10680d3c35b5969b731404c513ec3fffc858374fa484ddac",
    "committed_pin_sha256": "0368a73d86f9cf8d695fe39cc6e4f3aa54f4c882c95ab66ddc146b519af80086",
    "deployed_pin_sha256": "4c0399d9ab516a72943c0ce17f2c070e8da8219ea7777a7c8e2c7fce58ecd107",
    "edits_manifest_sha256": "fd464c6e1bfc1ab13aded048e1feba97b2844f8fe537f3b0b8eaf1ae3e4a9bce",
    "data_manifest_sha256": "c8ccedd0eb620fb0d049fef377e3ae29f6c0ff5c04184b9335d5a419821769e4",
    "node_ar_isolated_sha256": "37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610",
    "master_ar_isolated_sha256": "37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610",
}
DATA_PINS = {
    "train.csv": ("4a437fde05fe5264e1701a7387ac6fb75393772ba38bb2c9c566405af5af4bd7", 60302),
    "test.csv": ("5c78320a80dc159b35c408363be46a5d93f078183d539db75ee42a796d6a4e95", 28210),
    "ground_truth.csv": ("af6609cdf1dad0b699bd3414c13e999b2c2f651972f0938254a835985d584306", 2839),
}


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(argv: list[str], cwd: str | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True, cwd=cwd, env=env)


def git(*args: str) -> str:
    res = run(["git", *args], cwd=str(H))
    assert res.returncode == 0, f"git {' '.join(args)} rc={res.returncode}: {res.stderr[-500:]}"
    return res.stdout.strip()


def cgroup_dir() -> Path:
    text = Path("/proc/self/cgroup").read_text().strip()
    assert text.startswith("0::"), text
    return Path("/sys/fs/cgroup") / text.split("::", 1)[1].lstrip("/")


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    os.chdir(H)
    sys.path.insert(0, str(H))
    sys.path.insert(0, str(H / "src"))
    pre: dict = {"utc": now(), "host": socket.gethostname(), "kernel": platform.release(),
                 "machine": platform.machine(), "uid": os.geteuid(),
                 "python": sys.version, "python_executable": sys.executable,
                 "loadavg": os.getloadavg(), "affinity": sorted(os.sched_getaffinity(0)),
                 "cgroup": str(cgroup_dir()),
                 "ptrace_scope": Path("/proc/sys/kernel/yama/ptrace_scope").read_text().strip(),
                 "systemd_version": run(["systemd-run", "--version"]).stdout.splitlines()[0],
                 "launch_env": {k: os.environ.get(k) for k in
                                ("PATH", "VIRTUAL_ENV", "PYTHONPATH", "CUDA_VISIBLE_DEVICES",
                                 "PYTHONDONTWRITEBYTECODE", "AR_TEST_CGROUP_PARENT",
                                 "AR_TRACKG_DATA_ROOT")},
                 "python3_resolved": shutil.which("python3")}

    # ---- git binding
    status = git("status", "--porcelain").splitlines()
    head = git("rev-parse", "HEAD")
    name = git("rev-parse", "--abbrev-ref", "HEAD")
    pre["git"] = {
        "head": head, "branch": name, "status_porcelain": status,
        "base_commit_is_ancestor": run(["git", "merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"],
                                       cwd=str(H)).returncode == 0,
        "diffstat_vs_base": git("diff", "--stat", BASE_COMMIT, "HEAD").splitlines()[-1],
        "diff_name_status_vs_base": git("diff", "--name-status", BASE_COMMIT, "HEAD").splitlines(),
        "data_in_committed_tree": [ln for ln in git("ls-tree", "-r", "--name-only", "HEAD").splitlines()
                                   if ln.startswith("third_party/mlgym/nodes/mlgym_titanic/")
                                   and (ln.endswith(".csv") or ln.endswith("data_manifest.json"))],
    }
    assert head == PIN, f"STOP: HEAD {head} != reviewed pin {PIN}"
    assert name == BRANCH, pre["git"]["branch"]
    assert pre["git"]["base_commit_is_ancestor"], "STOP: base commit is not an ancestor"
    assert pre["git"]["data_in_committed_tree"] == [], pre["git"]["data_in_committed_tree"]
    expected_status = ["?? third_party/mlgym/nodes/mlgym_titanic/data"]
    data_link_statuses = {"?? third_party/mlgym/nodes/mlgym_titanic/data",
                          "?? third_party/mlgym/nodes/mlgym_titanic/data/"}
    assert status in ([], expected_status) or all(ln in data_link_statuses for ln in status), \
        f"STOP: worktree status {status} != expected setup link only"

    # ---- pins, recomputed from the deployed tree with the kit's own frozen-pin helpers
    from autoresearch.trackg import isolation
    from autoresearch.trackg.node_template import load_trackg_node_spec
    from autoresearch.trackg.noise_floor import committed_view, frozen_pin_sha256, sha256_file as nf_sha

    spec = load_trackg_node_spec(SPEC_PATH)
    pin = isolation.frozen_file_hashes(NODE_DIR, spec.frozen_paths)
    committed = committed_view(pin)
    data_link = NODE_DIR / "data"
    assert data_link.is_symlink(), "STOP: the setup data link is missing"
    pins = {
        "node": NODE,
        "spec_path": "third_party/mlgym/configs/trackg/nodes/mlgym_titanic.yaml",
        "node_dir": "third_party/mlgym/nodes/mlgym_titanic",
        "run_budget": {"kind": spec.run_budget.kind, "value": spec.run_budget.value},
        "node_spec_sha256": spec.raw_sha256,
        "spec_raw_sha256": nf_sha(SPEC_PATH),
        "committed_pin_sha256": frozen_pin_sha256(committed),
        "deployed_pin_sha256": frozen_pin_sha256(pin),
        "edits_manifest_sha256": nf_sha(NODE_DIR / "representative_edits/manifest.json"),
        "data_manifest_sha256": nf_sha(data_link / "data_manifest.json"),
        "node_ar_isolated_sha256": nf_sha(NODE_DIR / "ar_isolated.py"),
        "master_ar_isolated_sha256": nf_sha(H / "src/autoresearch/trackg/node_lib/ar_isolated.py"),
        "data_link": os.readlink(data_link),
        "frozen_entries": len(pin),
        "frozen_files": pin,
    }
    pre["pins"] = pins
    for key, expected in EQ.items():
        assert pins[key] == expected, f"STOP: {key} {pins[key]} != accepted {expected}"
    assert pins["run_budget"] == {"kind": "steps", "value": 150000}, pins["run_budget"]
    assert pins["data_link"] == str(DATA_ROOT / "mlgym_titanic"), pins["data_link"]

    # ---- data: read-only, outside the repository, pinned hashes
    data = {
        "root": str(data_link.resolve()),
        "root_mode": oct(data_link.resolve().stat().st_mode),
        "outside_repo": not str(data_link.resolve()).startswith(str(H)),
        "manifest_schema": json.loads((data_link / "data_manifest.json").read_text()).get("schema"),
        "files": {},
        "read_only": all(not p.stat().st_mode & 0o222 for p in [data_link.resolve(), *[data_link / n for n in DATA_PINS]]),
        "root_bytes": int(run(["du", "-sb", str(data_link.resolve())]).stdout.split()[0]),
    }
    for fname, (sha, size) in DATA_PINS.items():
        data["files"][fname] = {"sha256": sha256_file(data_link / fname),
                                "bytes": (data_link / fname).stat().st_size,
                                "mode": oct((data_link / fname).stat().st_mode)}
    pre["data"] = data
    assert data["outside_repo"], "STOP: data root is inside the repository"
    assert data["read_only"], "STOP: the data root is writable"
    for fname, (sha, size) in DATA_PINS.items():
        got = data["files"][fname]
        assert got["sha256"] == sha and got["bytes"] == size, (fname, got)

    # ---- environment: pinned torch312 freeze
    import numpy
    import torch
    freeze = run([UV, "pip", "freeze", "--python", sys.executable])
    assert freeze.returncode == 0, freeze.stderr[-800:]
    freeze_text = freeze.stdout
    pre["env"] = {
        "freeze_packages": len([ln for ln in freeze_text.splitlines() if "==" in ln]),
        "freeze_sha256": hashlib.sha256(freeze_text.encode()).hexdigest(),
        "freeze_expected_sha256": FREEZE_SHA,
        "uv": run([UV, "--version"]).stdout.strip(),
        "python": sys.version.split()[0],
        "torch": torch.__version__,
        "cuda_available_plain": bool(torch.cuda.is_available()),
        "cuda_device_count_plain": int(torch.cuda.device_count()),
        "numpy": numpy.__version__,
        "pandas": __import__("pandas").__version__,
    }
    assert pre["env"]["freeze_sha256"] == FREEZE_SHA, "STOP: torch312 freeze differs from the accepted freeze"
    # The census smoke runs with CUDA_VISIBLE_DEVICES="" in the scope; verify that hides the GPU.
    hidden = run([sys.executable, "-c", "import torch; print(int(torch.cuda.device_count()))"],
                 env=dict(os.environ, CUDA_VISIBLE_DEVICES=""))
    assert hidden.returncode == 0 and hidden.stdout.strip() == "0", \
        f"STOP: CUDA_VISIBLE_DEVICES='' still exposes a GPU: {hidden.stdout!r} {hidden.stderr[-400:]}"
    pre["env"]["cuda_device_count_hidden"] = int(hidden.stdout.strip())

    # ---- CPU-only registration + the node's SMOKE entry (in the pinned env, subprocess)
    code = (
        "import json, sys\n"
        "from tests.trackg import port_smoke_gpu as p\n"
        "from tests.trackg import test_port_mlgym as t\n"
        "entry = t.SMOKE['mlgym_titanic']\n"
        "print(json.dumps({'cpu_only_nodes': sorted(p.CPU_ONLY_NODES),\n"
        "  'in_cpu_only': 'mlgym_titanic' in p.CPU_ONLY_NODES,\n"
        "  'torch_node': entry.get('torch_node'),\n"
        "  'divergent': sorted(entry.get('divergent', set())),\n"
        "  'has_make': entry.get('make') is not None,\n"
        "  'budget': entry.get('budget')}))\n")
    env = dict(os.environ, PYTHONPATH="src", PYTHONDONTWRITEBYTECODE="1")
    reg = run([PY, "-c", code], cwd=str(H), env=env)
    assert reg.returncode == 0, f"STOP: cannot load the smoke entry: {reg.stdout[-800:]}{reg.stderr[-800:]}"
    pre["smoke_entry"] = json.loads(reg.stdout.strip().splitlines()[-1])
    assert pre["smoke_entry"]["in_cpu_only"] is True, pre["smoke_entry"]
    assert pre["smoke_entry"]["torch_node"] is True and pre["smoke_entry"]["has_make"] is True

    # ---- GPU and lease state: record, and assert no GPU is visible / no lease held
    gpu = run(["nvidia-smi", "--query-gpu=uuid,name,driver_version,memory.total,memory.used,utilization.gpu",
               "--format=csv,noheader"])
    apps = run(["nvidia-smi", "--query-compute-apps=pid,process_name,used_memory", "--format=csv,noheader"])
    lease = HOME / "r1_locks/gpu0.lock"
    locks = run(["lslocks"]).stdout
    pre["gpu"] = {
        "nvidia_smi_rc": gpu.returncode,
        "gpus": gpu.stdout.strip().splitlines(),
        "compute_apps": apps.stdout.strip().splitlines() if apps.returncode == 0 else None,
        "lease_lock_file": str(lease) if lease.exists() else None,
        "lease_lock_stat": {"bytes": lease.stat().st_size, "mtime": lease.stat().st_mtime} if lease.exists() else None,
        "lease_held": any("gpu0.lock" in ln for ln in locks.splitlines()),
    }
    assert pre["gpu"]["lease_held"] is False, "STOP: a GPU lease is held"

    # ---- cgroup / CPU / disk basics
    scope = cgroup_dir()
    pre["cgroup_limits"] = {
        "memory_max": (scope / "memory.max").read_text().strip(),
        "memory_swap_max": (scope / "memory.swap.max").read_text().strip(),
        "controllers": (scope / "cgroup.controllers").read_text().strip(),
        "subtree_control": (scope / "cgroup.subtree_control").read_text().strip(),
        "procs": len((scope / "cgroup.procs").read_text().split()),
    }
    pre["cpu"] = {"nproc": os.cpu_count(), "loadavg": os.getloadavg()}
    pre["disk"] = {"home_avail_bytes": int(run(["df", "-B1", "--output=avail", str(HOME)]).stdout.strip().splitlines()[-1]),
                   "runs_root_exists": (BASE / "runs").exists()}
    assert (BASE / "runs").exists() is False, "STOP: runs root already exists (one smoke only, no retry)"

    # ---- write the capture set
    (RAW / "torch312.freeze.txt").write_text(freeze_text)
    (RAW / "preflight.json").write_text(json.dumps(pre, indent=2, sort_keys=True) + "\n")
    (RAW / "pins.json").write_text(json.dumps(pins, indent=2, sort_keys=True) + "\n")
    (RAW / "data_manifest.json").write_text((data_link / "data_manifest.json").read_text())
    (RAW / "edits_manifest.json").write_text((NODE_DIR / "representative_edits/manifest.json").read_text())
    (RAW / "mlgym_titanic.yaml").write_text(SPEC_PATH.read_text())
    (RAW / "git_head.txt").write_text(f"branch: {name}\nhead: {head}\nbase: {BASE_COMMIT}\n")
    (RAW / "git_status.txt").write_text("\n".join(status) + "\n")
    (RAW / "git_diffstat_vs_base.txt").write_text(
        "\n".join(pre["git"]["diff_name_status_vs_base"]) + "\n" + pre["git"]["diffstat_vs_base"] + "\n")
    (RAW / "env.txt").write_text(
        f"=== {pre['utc']}\nhostname: {socket.gethostname()}\nplatform: {platform.platform()}\n"
        f"python: {sys.version} ({sys.executable})\ntorch: {torch.__version__} numpy: {numpy.__version__}\n"
        f"cuda_available_plain: {torch.cuda.is_available()} cuda_device_count_plain: "
        f"{torch.cuda.device_count()} cuda_device_count_with_CUDA_VISIBLE_DEVICES_empty: "
        f"{pre['env']['cuda_device_count_hidden']}\n"
        f"CUDA_VISIBLE_DEVICES: {pre['launch_env']['CUDA_VISIBLE_DEVICES']!r}\n"
        f"freeze_sha256: {pre['env']['freeze_sha256']} ({pre['env']['freeze_packages']} packages)\n"
        f"cgroup: {pre['cgroup']} memory.max={pre['cgroup_limits']['memory_max']} "
        f"memory.swap.max={pre['cgroup_limits']['memory_swap_max']}\n"
        f"affinity: {pre['affinity']}\nptrace_scope: {pre['ptrace_scope']}\n"
        f"systemd: {pre['systemd_version']}\nbranch: {name} head: {head}\n"
        f"git status: {status}\n"
        f"smoke_entry: {json.dumps(pre['smoke_entry'], sort_keys=True)}\n"
        f"data: {json.dumps(data['files'], sort_keys=True)} (root {data['root']}, read_only {data['read_only']})\n")
    gpu_text = (f"utc: {pre['utc']}\nCUDA_VISIBLE_DEVICES: {pre['launch_env']['CUDA_VISIBLE_DEVICES']!r}\n"
                f"torch.cuda.device_count_plain: {torch.cuda.device_count()} "
                f"cuda_available_plain: {torch.cuda.is_available()} "
                f"cuda_device_count_with_CUDA_VISIBLE_DEVICES_empty: "
                f"{pre['env']['cuda_device_count_hidden']}\n"
                f"nvidia-smi query rc={pre['gpu']['nvidia_smi_rc']}:\n")
    if pre["gpu"]["gpus"]:
        gpu_text += pre["gpu"]["gpus"][0] + "\n"
    gpu_text += (f"compute apps:\n{apps.stdout.strip()}\n"
                 f"lease gpu0.lock: {pre['gpu']['lease_lock_stat']} held={pre['gpu']['lease_held']}\n")
    (RAW / "gpu_state_pre.txt").write_text(gpu_text)

    print("PREFLIGHT_PASS " + json.dumps({
        "utc": pre["utc"], "head": head, "branch": name,
        "committed_pin": pins["committed_pin_sha256"][:16], "deployed_pin": pins["deployed_pin_sha256"][:16],
        "node_spec": pins["node_spec_sha256"][:16], "data_manifest": pins["data_manifest_sha256"][:16],
        "freeze": pre["env"]["freeze_sha256"][:16], "cuda_count_hidden": pre["env"]["cuda_device_count_hidden"],
        "cgroup": pre["cgroup"], "affinity": pre["affinity"][:2] + ["..."] + pre["affinity"][-1:],
        "loadavg": pre["loadavg"], "smoke_entry": pre["smoke_entry"]["cpu_only_nodes"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as exc:
        print(f"PREFLIGHT_STOP: {exc}")
        sys.exit(2)
