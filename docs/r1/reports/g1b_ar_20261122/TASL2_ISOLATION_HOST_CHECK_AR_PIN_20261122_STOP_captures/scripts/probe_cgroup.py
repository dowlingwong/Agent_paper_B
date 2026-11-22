"""R1-TRACKG-AR-U2-TASL2 condition 3: delegated cgroup v2 subtree with cgroup.kill.

Run by ``run_checks.sh`` inside
  ``systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0``
so the facts below describe the exact delegated scope the smoke/GPU runs will use.

Records: the scope cgroup path, memory.max (expected 8589934592), memory.swap.max (expected 0),
cgroup.kill existence, nsdelegate, ownership and writability; then runs the *unit's own*
``isolation.RunCgroup.create -> join a live process -> cgroup.kill -> remove`` probe.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

EXPECTED_MEMORY_MAX = "8589934592"
EXPECTED_SWAP_MAX = "0"


def read(path: str, limit: int = 200_000) -> str:
    try:
        return Path(path).read_text(errors="replace")[:limit]
    except OSError as error:
        return f"<unreadable: {error}>"


def self_cgroup_path() -> str:
    for line in read("/proc/self/cgroup").splitlines():
        parts = line.split(":", 2)
        if len(parts) == 3 and parts[0] == "0":
            rel = parts[2].strip()
            return "/sys/fs/cgroup" + rel if rel else "/sys/fs/cgroup"
    raise SystemExit("no cgroup v2 line in /proc/self/cgroup")


def dir_facts(path: str) -> dict:
    out = {"path": path, "exists": os.path.isdir(path)}
    if not out["exists"]:
        return out
    for name in ("cgroup.controllers", "cgroup.subtree_control", "cgroup.procs", "cgroup.kill",
                 "cgroup.events", "cgroup.type", "memory.max", "memory.swap.max",
                 "memory.current", "memory.peak"):
        target = os.path.join(path, name)
        exists = os.path.exists(target)
        out[name] = {"exists": exists,
                     "value": read(target).strip() if exists else None,
                     "readable": os.access(target, os.R_OK) if exists else None,
                     "writable": os.access(target, os.W_OK) if exists else None}
    try:
        out["owner_uid"] = os.stat(path).st_uid
        out["mode"] = oct(os.stat(path).st_mode & 0o777)
    except OSError:
        pass
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--text", default="")
    args = ap.parse_args()

    path = self_cgroup_path()
    result: dict = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "euid": os.geteuid(),
        "self_cgroup": read("/proc/self/cgroup").strip(),
        "cgroup_path": path,
        "is_scope": os.path.basename(path).startswith("run-") and path.endswith(".scope"),
        "mountinfo": [line.strip() for line in read("/proc/self/mountinfo").splitlines()
                      if " /sys/fs/cgroup " in line][:3],
        "dir": dir_facts(path),
        "expected": {"memory.max": EXPECTED_MEMORY_MAX, "memory.swap.max": EXPECTED_SWAP_MAX,
                     "cgroup.kill": "exists"},
        "runcgroup_probe": None,
    }
    big = result["dir"]
    result["checks"] = {
        "memory_max_8g": big.get("memory.max", {}).get("value") == EXPECTED_MEMORY_MAX,
        "memory_swap_max_0": big.get("memory.swap.max", {}).get("value") == EXPECTED_SWAP_MAX,
        "cgroup_kill_exists": bool(big.get("cgroup.kill", {}).get("exists")),
        "procs_writable": bool(big.get("cgroup.procs", {}).get("writable")),
        "owner_is_caller": big.get("owner_uid") == os.geteuid(),
        "scope_unit": bool(result["is_scope"]),
    }

    sys.path.insert(0, os.path.join(args.repo, "src"))
    try:
        from autoresearch.trackg import isolation  # noqa: E402
        result["nsdelegate"] = isolation.cgroup2_nsdelegate(path)
        result["checks"]["nsdelegate"] = bool(result["nsdelegate"])
        cg = isolation.RunCgroup.create(path, f"hostcheck_{os.getpid()}")
        record = {"path": str(cg.path), "migration_possible": cg.migration_possible}
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"],
                                 preexec_fn=isolation.join_cgroup_preexec(cg))
        try:
            time.sleep(0.5)
            before = cg.procs()
            record["processes_before"] = before
            record["populated_before"] = cg.populated()
            record["kill"] = cg.kill(grace=5.0)
            try:
                child.wait(timeout=5)
                record["child_returncode"] = child.returncode
            except subprocess.TimeoutExpired:
                child.kill()
                record["child_returncode"] = None
            record["populated_after"] = cg.populated()
            record["kill_method"] = record["kill"].get("method")
            record["empty_after"] = record["kill"].get("empty_after")
            record["removed"] = cg.remove()
        finally:
            try:
                cg.kill(grace=1.0)
                cg.remove()
            except Exception:  # noqa: BLE001
                pass
        result["runcgroup_probe"] = record
        result["checks"]["runcgroup_kill"] = bool(record.get("processes_before")
                                                  and record.get("empty_after")
                                                  and record.get("removed"))
        result["checks"]["kill_method_cgroup_kill"] = record.get("kill_method") == "cgroup.kill"
    except Exception:  # noqa: BLE001
        result["runcgroup_probe"] = {"error": traceback.format_exc()}
        result["checks"]["runcgroup_kill"] = False
        result["checks"]["kill_method_cgroup_kill"] = False

    result["condition_3_pass"] = all(result["checks"].values())
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if args.text:
        Path(args.text).write_text(
            f"scope={result['cgroup_path']}\n"
            f"memory.max={big.get('memory.max', {}).get('value')}\n"
            f"memory.swap.max={big.get('memory.swap.max', {}).get('value')}\n"
            f"cgroup.kill_exists={big.get('cgroup.kill', {}).get('exists')}\n"
            f"cgroup.procs_writable={big.get('cgroup.procs', {}).get('writable')}\n"
            f"owner_uid={big.get('owner_uid')} euid={result['euid']}\n"
            f"nsdelegate={result.get('nsdelegate')}\n"
            f"mountinfo={result['mountinfo']}\n"
            f"runcgroup={json.dumps(result['runcgroup_probe'], default=str)}\n"
            f"checks={json.dumps(result['checks'], sort_keys=True)}\n",
            encoding="utf-8")
    print("RESULT " + json.dumps({"condition_3_pass": result["condition_3_pass"],
                                  "checks": result["checks"],
                                  "runcgroup": result["runcgroup_probe"]}, default=str))
    return 0 if result["condition_3_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
