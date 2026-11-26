#!/usr/bin/env python3
"""TASL-2 CPU stability stress driver - ONE baseline census run of MetaMaze at the full 2,000,000 steps.

Read-only CPU stability check (Raptor Lake hypothesis) for the reviewed MetaMaze kit
`mac-trackg-mountaincar-20261125` @ aa354485bff6b5746c48ddadcb50d92e9c6f3645 on TASL-2.

This driver runs exactly the baseline step of the reviewed census command
(`tests/trackg/port_smoke_gpu` -> `port_support.run_smoke` -> `run_smoke_campaign`): the kit's own
`run_smoke_campaign()` is called with an EMPTY proposal list, so it runs only its first run,
`s000_baseline` (seeds 8001/8001, full 2M-step budget, real pinned data, isolation, limits), and nothing
else.  The reviewed `check_baseline_log()` is then applied to the run's log and result channel.  No
repository file is changed; the kit is only imported.  One invocation per (CPU group, repeat); the
launcher runs 4 groups x 3 repeats sequentially.

Also verified/recorded per run: git pin, committed/deployed pins, data manifest and all 9 data files,
`venv_jax` freeze, interpreter binding, cgroup memory limit (8G, swap 0), affinity, ptrace scope,
CUDA_VISIBLE_DEVICES, and the run's process/exit/signal/wall/log/channel/metric facts.

ENGINEERING_ONLY: no GPU, no GPU lease, no system change, no deletion, no push.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import platform
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

HOME = Path.home()
ENV = HOME / "r1_trackg_20261125/venv_jax"
ENV_BIN = ENV / "bin"
H = HOME / "r1_trackg_20261125/harness_metamaze"
BASE = HOME / "r1_engineering/metamaze_20261125/tasl2_cpu_stability_20261125"

NODE = "mlgym_metamaze"
SPEC_REL = "third_party/mlgym/configs/trackg/nodes/mlgym_metamaze.yaml"
NODE_REL = "third_party/mlgym/nodes/mlgym_metamaze"
BRANCH = "mac-trackg-mountaincar-20261125"
PIN = "aa354485bff6b5746c48ddadcb50d92e9c6f3645"
BASE_COMMIT = "c025f89aeafc2199bf3487b4bcaa16678273c702"
EQ = {
    "node_spec_sha256": "d97bb182a6469cc4381262960bccf58eec984996cb9a8cd89c39083b4679dbb9",
    "spec_raw_sha256": "d46dee59960f6959587e822c9dd663864006d2b48d7e5a67a2f7022f21cb3c59",
    "committed_pin_sha256": "759d6bf0562a3a9334982b30b3e23c80f222c828e44847b66e743102c87d03db",
    "deployed_pin_sha256": "1eaaeac351280e16295eae0f50212f352b1aa0c4c3d26a410b58bb0c3bf9ecb7",
    "edits_manifest_sha256": "6de5741f7107d9f924a3686fce85f6509ed7fb0c47ee7cc2c9fc16732d66f0b2",
    "data_manifest_sha256": "e233819526e8214bb898c4f9dd76a8c30be7b0dcabd710b60efb815e99c38000",
    "node_ar_isolated_sha256": "37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610",
    "master_ar_isolated_sha256": "37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610",
}
FREEZE_SHA = "630ed6e1b823e0e2183c64ffb09bebd9994f755f518db2867ee538f388f5fdd9"
DATA_ROOT_PREFIX = str(HOME / "r1_engineering/metamaze_20261125/data")
PROVISIONAL_TIMEOUT = 900.0
MEMORY_MAX = 8589934592  # MemoryMax=8G
TRAIN_SEED = 8001
SPLIT_SEED = 8001


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_argv(argv: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True)


def git(*args: str) -> str:
    res = run_argv(["git", *args])
    assert res.returncode == 0, f"git {' '.join(args)} rc={res.returncode}: {res.stderr[-500:]}"
    return res.stdout.strip()


def cgroup_dir() -> Path:
    text = Path("/proc/self/cgroup").read_text().strip()
    assert text.startswith("0::"), f"not a unified cgroup v2 hierarchy: {text}"
    return Path("/sys/fs/cgroup") / text.split("::", 1)[1].lstrip("/")


def read_text_or_none(path: Path) -> str | None:
    try:
        return path.read_text().strip()
    except OSError:
        return None


def cpus_of(text: str) -> tuple[int, ...]:
    out: list[int] = []
    for part in text.split(","):
        lo, _, hi = part.partition("-")
        out += list(range(int(lo), int(hi or lo) + 1))
    return tuple(out)


# --------------------------------------------------------------------------- binding verification

def verify_binding(cpus: tuple[int, ...]) -> dict:
    """The reviewed census bindings, re-verified in the run scope (same checks as the accepted launches)."""
    os.chdir(H)
    sys.path.insert(0, str(H))
    sys.path.insert(0, str(H / "src"))
    from autoresearch.trackg import isolation
    from autoresearch.trackg.node_template import load_trackg_node_spec
    from autoresearch.trackg.noise_floor import committed_view, frozen_pin_sha256, sha256_file as nf_sha

    info: dict = {}
    info["cwd"] = os.getcwd()
    info["hostname"] = socket.gethostname()
    info["kernel"] = platform.release()
    info["platform"] = platform.platform()
    info["python"] = sys.version
    info["python_executable"] = sys.executable
    info["uid"] = os.geteuid()
    info["loadavg"] = list(os.getloadavg())
    info["affinity"] = sorted(os.sched_getaffinity(0))
    info["cpu_affinity_matches_group"] = info["affinity"] == sorted(cpus)
    info["cgroup"] = str(cgroup_dir())
    scope = cgroup_dir()
    info["memory_max"] = read_text_or_none(scope / "memory.max")
    info["memory_swap_max"] = read_text_or_none(scope / "memory.swap.max")
    info["controllers"] = read_text_or_none(scope / "cgroup.controllers")
    info["cgroup_subtree_control_before"] = read_text_or_none(scope / "cgroup.subtree_control")
    info["ptrace_scope"] = read_text_or_none(Path("/proc/sys/kernel/yama/ptrace_scope"))
    info["cuda_visible_devices"] = os.environ.get("CUDA_VISIBLE_DEVICES", "<unset>")
    info["path"] = os.environ.get("PATH")
    info["virtual_env"] = os.environ.get("VIRTUAL_ENV")
    info["pythonhashseed"] = os.environ.get("PYTHONHASHSEED", "<unset>")
    info["ar_test_cgroup_parent_launch_env"] = os.environ.get("AR_TEST_CGROUP_PARENT", "<unset>")
    info["python3_which"] = shutil.which("python3")
    info["torch_importable"] = importlib.util.find_spec("torch") is not None
    info["jax_metadata"] = {m: _meta_version(m) for m in
                            ("jax", "jaxlib", "flax", "optax", "gymnax", "tensorflow_probability", "dotmap", "numpy")}

    # --- the checks the accepted launches made (fail loudly = no run consumed)
    assert Path(sys.executable).resolve() == Path(os.path.realpath(ENV_BIN / "python")), sys.executable
    assert info["python3_which"] is not None and \
        Path(info["python3_which"]).resolve() == Path(sys.executable).resolve(), info["python3_which"]
    assert info["cpu_affinity_matches_group"], (info["affinity"], cpus)
    assert info["memory_max"] == str(MEMORY_MAX), info["memory_max"]
    assert info["memory_swap_max"] == "0", info["memory_swap_max"]
    assert info["ptrace_scope"] == "1", info["ptrace_scope"]
    assert info["cuda_visible_devices"] == "", info["cuda_visible_devices"]
    assert info["torch_importable"] is False, "STOP: torch importable in the pinned JAX env"
    assert info["ar_test_cgroup_parent_launch_env"] == "<unset>", "STOP: driver must set AR_TEST_CGROUP_PARENT"

    # git binding at the reviewed pin
    info["git"] = {
        "head": git("rev-parse", "HEAD"),
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "status_porcelain": git("status", "--porcelain").splitlines(),
        "base_commit_is_ancestor": run_argv(["git", "merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"]).returncode == 0,
    }
    assert info["git"]["head"] == PIN, f"STOP: HEAD {info['git']['head']} != reviewed pin {PIN}"
    assert info["git"]["branch"] == BRANCH, info["git"]["branch"]
    assert info["git"]["status_porcelain"] in ([], ["?? " + NODE_REL + "/data"]), \
        f"STOP: worktree changed at the pin: {info['git']['status_porcelain']}"

    # pins recomputed from the committed tree with the kit's own helpers
    spec_path = H / SPEC_REL
    spec = load_trackg_node_spec(spec_path)
    node_dir = H / NODE_REL
    pin = isolation.frozen_file_hashes(node_dir, spec.frozen_paths)
    committed = committed_view(pin)
    master = H / "src/autoresearch/trackg/node_lib/ar_isolated.py"
    pins = {
        "node": spec.name,
        "run_budget": {"kind": spec.run_budget.kind, "value": spec.run_budget.value},
        "node_spec_sha256": spec.raw_sha256,
        "spec_raw_sha256": nf_sha(spec_path),
        "committed_pin_sha256": frozen_pin_sha256(committed),
        "deployed_pin_sha256": frozen_pin_sha256(pin),
        "edits_manifest_sha256": nf_sha(node_dir / "representative_edits/manifest.json"),
        "data_manifest_sha256": nf_sha(node_dir / "data/data_manifest.json"),
        "node_ar_isolated_sha256": nf_sha(node_dir / "ar_isolated.py"),
        "master_ar_isolated_sha256": nf_sha(master),
        "data_link": os.readlink(node_dir / "data"),
        "frozen_files": committed,
    }
    info["pins"] = pins
    for key, expected in EQ.items():
        assert pins[key] == expected, f"STOP: {key} {pins[key]} != accepted {expected}"
    assert pins["run_budget"] == {"kind": "steps", "value": 2000000}, pins["run_budget"]
    assert len(committed) == 18, len(committed)

    # data: pinned, read-only snapshot outside the repository; every file re-hashed
    data_root = node_dir / "data"
    assert data_root.is_symlink() and not str(data_root.resolve()).startswith(str(H)), data_root
    manifest = json.loads((data_root / "data_manifest.json").read_text())
    assert manifest.get("schema") == "trackg_node_data/v1" and manifest.get("node") == NODE
    assert len(manifest["files"]) == 9, sorted(manifest["files"])
    files = {}
    for name, meta in sorted(manifest["files"].items()):
        path = data_root / name
        got = sha256_file(path)
        files[name] = {"sha256": got, "match": got == meta["sha256"] and path.stat().st_size == meta["bytes"]}
    assert all(item["match"] for item in files.values()), \
        "STOP: pinned snapshot file changed: " + repr({n: f for n, f in files.items() if not f["match"]})
    resolved = data_root.resolve()
    info["data"] = {
        "root": str(resolved),
        "root_in_expected_tree": str(resolved).startswith(DATA_ROOT_PREFIX),
        "root_mode": oct(resolved.stat().st_mode),
        "manifest_sha256": sha256_file(data_root / "data_manifest.json"),
        "files": files,
        "files_all_match": all(item["match"] for item in files.values()),
        "read_only": all(not ((resolved if p is None else data_root / p).stat().st_mode & 0o222)
                         for p in [None] + list(manifest["files"])),
    }
    assert info["data"]["root_in_expected_tree"], info["data"]["root"]
    assert info["data"]["manifest_sha256"] == EQ["data_manifest_sha256"], "STOP: data manifest changed"
    assert info["data"]["files_all_match"] and info["data"]["read_only"], "STOP: data not pinned/read-only"

    # environment freeze
    freeze = run_argv([sys.executable, "-m", "pip", "freeze"])
    assert freeze.returncode == 0, freeze.stderr[-800:]
    freeze_text = freeze.stdout
    info["env"] = {
        "freeze_packages": len([ln for ln in freeze_text.splitlines() if "==" in ln]),
        "freeze_sha256": sha256_bytes(freeze_text.encode()),
        "freeze_expected_sha256": FREEZE_SHA,
        "torch_absent": not info["torch_importable"],
    }
    assert info["env"]["freeze_sha256"] == FREEZE_SHA, "STOP: venv_jax freeze differs from the accepted freeze"

    # delegate the run cgroups under this scope (the reviewed isolation needs a writable cgroup parent)
    ctl = scope / "cgroup.subtree_control"
    current = ""
    try:
        current = ctl.read_text().strip()
        want = [c for c in ("memory", "pids") if c not in current.split()]
        if want:
            ctl.write_text(" ".join("+" + c for c in want) + "\n")
        info["cgroup_subtree_control_after"] = ctl.read_text().strip()
        info["cgroup_subtree_control_error"] = None
    except OSError as error:  # what the accepted launches hit too (EBUSY); not a waiver, only accounting
        info["cgroup_subtree_control_after"] = current
        info["cgroup_subtree_control_error"] = f"{type(error).__name__}: {error}"
    assert os.access(scope / "cgroup.procs", os.W_OK), f"STOP: scope cgroup {scope} not writable"
    os.environ["AR_TEST_CGROUP_PARENT"] = str(scope)
    info["ar_test_cgroup_parent"] = str(scope)
    info["spec"] = {"name": spec.name, "raw_sha256": spec.raw_sha256,
                    "editable_paths": list(spec.editable_paths), "workers": {"dataloader_workers": spec.workers.dataloader_workers,
                                                                            "threads": spec.workers.threads}}
    return info


def _meta_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


# --------------------------------------------------------------------------- the one baseline run

def run_baseline(cpus: tuple[int, ...], runs_root: Path, external_limit: str,
                 dryrun_steps: int | None = None) -> tuple[dict, Path]:
    os.chdir(H)
    sys.path.insert(0, str(H))
    sys.path.insert(0, str(H / "src"))
    from tests.trackg import port_support as ps

    # dryrun_steps is used ONLY for the one pre-flight driver validation (reduced budget, not a census run)
    spec = ps.load(NODE) if dryrun_steps is None else ps.reduced_spec(NODE, dryrun_steps)
    work = ps.node_dir(NODE)
    lim = ps.limits(PROVISIONAL_TIMEOUT, cpu_list=cpus, external_limit=external_limit)
    # the reviewed census campaign with NO proposals = only its own s000_baseline run
    records = ps.run_smoke_campaign(spec, work, runs_root, [], lim, train_seed=TRAIN_SEED, split_seed=SPLIT_SEED)
    assert len(records) == 1 and records[0]["run_id"] == "s000_baseline", [r["run_id"] for r in records]
    run_dir = Path(runs_root).resolve() / "s000_baseline"
    rec = json.loads((run_dir / "run_record.json").read_text())
    return rec, run_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--group", required=True, help="CPU list, e.g. 0-3 or 8-11")
    parser.add_argument("--repeat", required=True, type=int)
    parser.add_argument("--runs-root", required=True, type=Path, help="must not exist yet")
    parser.add_argument("--out", required=True, type=Path, help="result JSON")
    parser.add_argument("--dryrun-steps", type=int, default=None,
                        help="VALIDATION ONLY: reduced step budget to exercise the driver code path once; "
                             "never used for the 12 census baseline runs")
    args = parser.parse_args(argv)
    cpus = cpus_of(args.group)
    result: dict = {"schema": "tasl2_cpu_stability_run/v1", "group": args.group, "cpus": list(cpus),
                    "repeat": args.repeat, "utc_start": now()}
    t0 = time.time()
    try:
        binding = verify_binding(cpus)
        result["binding"] = binding
        unit = Path(binding["cgroup"]).name
        external_limit = (f"systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 "
                          f"(unit {unit}; memory.max={binding['memory_max']}; memory.swap.max={binding['memory_swap_max']})")
        result["external_limit"] = external_limit
        runs_root = Path(args.runs_root)
        assert not runs_root.exists(), f"STOP: runs root {runs_root} already exists"
        rec, run_dir = run_baseline(cpus, runs_root, external_limit, args.dryrun_steps)
        result["run"] = collect_run(run_dir, rec, runs_root)
    except BaseException as error:  # never lose the record of a failure (a crash of the kit must be reported)
        import traceback
        result["driver_error"] = f"{type(error).__name__}: {error}"
        result["driver_traceback"] = traceback.format_exc()
        result["utc_end"] = now()
        result["wall_seconds"] = round(time.time() - t0, 3)
        result["verdict"] = "DRIVER_FAILED"
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n")
        raise
    result["utc_end"] = now()
    result["wall_seconds"] = round(time.time() - t0, 3)
    run = result["run"]
    ok = (run["outcome"].get("kind") == "ok" and run["process"].get("returncode") == 0
          and run["baseline_check"]["ok"])
    result["verdict"] = ("PASS" if ok else "CRASH_OR_FAIL")
    if args.dryrun_steps is not None:
        result["verdict"] = "VALIDATION_" + result["verdict"]
        result["dryrun_steps"] = args.dryrun_steps
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"group": args.group, "repeat": args.repeat, "verdict": result["verdict"],
                      "outcome": run["outcome"], "returncode": run["process"].get("returncode"),
                      "signal": run.get("signal"), "elapsed_s": run.get("elapsed_seconds_info_only"),
                      "wall_s": result["wall_seconds"], "val_return": run.get("val_return"),
                      "sealed_test_return": run.get("sealed_test_return"),
                      "log_sha256": run.get("log_sha256"), "channel_sha256": run.get("channel_sha256")},
                     sort_keys=True))
    return 0


def collect_run(run_dir: Path, rec: dict, runs_root: Path) -> dict:
    log_bytes = (run_dir / "run.log").read_bytes() if (run_dir / "run.log").exists() else b""
    channel_path = run_dir / "result_channel.txt"
    channel_bytes = channel_path.read_bytes() if channel_path.exists() else b""
    log_text = log_bytes.decode("utf-8", "replace")
    channel_text = channel_bytes.decode("utf-8", "replace")
    proc = rec.get("process") or {}
    rc = proc.get("returncode")
    sig_name = None
    if isinstance(rc, int) and rc < 0:
        try:
            sig_name = signal.Signals(-rc).name
        except ValueError:
            sig_name = f"signal{-rc}"
    import re
    steps = [int(m.group(1)) for m in re.finditer(r"^AR_STEPS env_steps=(\d+)$", log_text, re.MULTILINE)]
    metric_lines = re.findall(r"^AR_METRIC (\S+)$", channel_text, re.MULTILINE)
    test_lines = re.findall(r"^AR_TEST (\S+)$", channel_text, re.MULTILINE)
    outcome = rec.get("outcome") or {}
    val = outcome.get("value") if isinstance(outcome, dict) else None
    sealed = (rec.get("sealed") or {}).get("test_return")
    baseline_check: dict = {"ok": False, "error": None}
    try:
        from tests.trackg import port_support as ps
        from autoresearch.trackg.node_template import load_trackg_node_spec
        spec = load_trackg_node_spec(H / SPEC_REL)
        ps.check_baseline_log(spec, log_text, channel_text)
        baseline_check = {"ok": True, "error": None}
    except BaseException as error:
        baseline_check = {"ok": False, "error": f"{type(error).__name__}: {error}"}
    scope_peak = read_text_or_none(cgroup_dir() / "memory.peak")
    return {
        "run_id": rec.get("run_id"),
        "runs_root": str(Path(runs_root).resolve()),
        "run_dir": str(run_dir.resolve()),
        "record_path": str((run_dir / "run_record.json").resolve()),
        "executed": rec.get("executed"),
        "process": proc,
        "exit_code": rc,
        "signal": sig_name,
        "signal_number": (-rc if isinstance(rc, int) and rc < 0 else None),
        "timed_out": proc.get("timed_out"),
        "killed_with": proc.get("killed_with"),
        "leftover_processes_killed": proc.get("leftover_processes_killed"),
        "elapsed_seconds_info_only": rec.get("elapsed_seconds_info_only"),
        "outcome": rec.get("outcome"),
        "val_return": val,
        "sealed_test_return": sealed,
        "command": rec.get("command"),
        "seeds": rec.get("seeds"),
        "run_budget": rec.get("run_budget"),
        "node_spec_sha256": rec.get("node_spec_sha256"),
        "frozen_pin_sha256": rec.get("frozen_pin_sha256"),
        "incumbent_code_state_sha256": rec.get("incumbent_code_state_sha256"),
        "code_state_sha256": rec.get("code_state_sha256"),
        "determinism": rec.get("determinism"),
        "log_sha256": sha256_bytes(log_bytes),
        "log_bytes": len(log_bytes),
        "log_lines": log_text.count("\n"),
        "log_record_sha256": rec.get("log_sha256"),
        "log_sha256_matches_record": sha256_bytes(log_bytes) == rec.get("log_sha256"),
        "channel_sha256": sha256_bytes(channel_bytes),
        "channel_bytes": len(channel_bytes),
        "channel_text": channel_text,
        "channel_metric_lines": metric_lines,
        "channel_test_lines": test_lines,
        "channel_present": channel_path.exists(),
        "steps_max": max(steps) if steps else None,
        "steps_full_budget": bool(steps) and max(steps) >= 2000000,
        "log_has_worker_exit_0": "AR_WORKER exit=0" in log_text,
        "log_tail": log_text.splitlines()[-8:],
        "isolation": {k: rec.get("isolation", {}).get(k) for k in
                      ("effective", "waivers", "exceptions", "frozen_files_checked", "frozen_files_changed",
                       "arbitrary_syscalls_blocked", "cgroup")},
        "baseline_check": baseline_check,
        "scope_memory_peak_bytes": int(scope_peak) if scope_peak and scope_peak.strip().isdigit() else None,
    }


if __name__ == "__main__":
    sys.exit(main())
