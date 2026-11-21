"""R1-T1-HOST-H200 condition C1: a cgroup v2 parent the run's uid can write, with cgroup.kill.

Uses the accepted harness's own ``isolation.RunCgroup`` (create -> move a live process in -> cgroup.kill ->
remove) on every plausible parent and records the exact failure of each.  If one works, its path is written to
``cgroup_parent.txt`` for the smoke probes.  No waivers; a failure here is the host condition failing.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path

import lib_iso


def cgroup_self_path() -> str | None:
    for line in lib_iso.read_text("/proc/self/cgroup").splitlines():
        parts = line.split(":", 2)
        if len(parts) == 3 and parts[0] == "0":
            rel = parts[2].strip("/")
            return os.path.join("/sys/fs/cgroup", rel) if rel else "/sys/fs/cgroup"
    return None


def candidate_parents() -> list[dict]:
    out: list[dict] = []
    env = os.environ.get("AR_TEST_CGROUP_PARENT")
    if env:
        out.append({"path": env, "source": "env AR_TEST_CGROUP_PARENT"})
    own = cgroup_self_path()
    if own:
        out.append({"path": own, "source": "own cgroup from /proc/self/cgroup"})
        parent = os.path.dirname(own)
        if parent != own:
            out.append({"path": parent, "source": "parent of own cgroup"})
    out.append({"path": "/sys/fs/cgroup", "source": "cgroup v2 root"})
    for extra in ("/sys/fs/cgroup/user.slice",
                  f"/sys/fs/cgroup/user.slice/user-{os.getuid()}.slice",
                  f"/sys/fs/cgroup/user.slice/user-{os.getuid()}.slice/user@{os.getuid()}.service"):
        out.append({"path": extra, "source": "systemd user delegation path"})
    seen, unique = set(), []
    for entry in out:
        if entry["path"] not in seen:
            seen.add(entry["path"])
            unique.append(entry)
    return unique


def dir_facts(path: str) -> dict:
    out = {"path": path, "exists": os.path.isdir(path)}
    if not out["exists"]:
        return out
    for name in ("cgroup.controllers", "cgroup.subtree_control", "cgroup.procs", "cgroup.kill",
                 "cgroup.events", "cgroup.type", "memory.max", "memory.current"):
        target = os.path.join(path, name)
        out[name] = {"exists": os.path.exists(target), "writable": os.access(target, os.W_OK)
                     if os.path.exists(target) else None,
                     "readable": os.access(target, os.R_OK) if os.path.exists(target) else None}
    try:
        out["owner_uid"] = os.stat(path).st_uid
    except OSError:
        pass
    try:
        out["cgroup_procs"] = lib_iso.read_text(os.path.join(path, "cgroup.procs")).split()[:20]
    except Exception:  # noqa: BLE001
        pass
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="harness repo (accepted core) whose RunCgroup is used")
    parser.add_argument("--base", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--parent-out", required=True)
    args = parser.parse_args()

    result: dict = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "euid": os.geteuid(),
        "proc_self_cgroup": lib_iso.read_text("/proc/self/cgroup"),
        "cgroup_mount": [line for line in lib_iso.read_text("/proc/self/mountinfo").splitlines()
                         if " /sys/fs/cgroup" in line][:6],
        "cgroup_v2_root": dir_facts("/sys/fs/cgroup"),
        "candidates": [],
        "chosen": None,
    }
    sys.path.insert(0, os.path.join(args.repo, "src"))
    try:
        from autoresearch.trackg import isolation  # noqa: E402
    except Exception:  # noqa: BLE001
        result["error"] = traceback.format_exc()
        lib_iso.write_json(args.out, result)
        Path(args.parent_out).write_text("")
        return 2

    result["cgroup2_nsdelegate_root"] = isolation.cgroup2_nsdelegate("/sys/fs/cgroup")
    record = None
    for entry in candidate_parents():
        item = {"candidate": entry, "dir": dir_facts(entry["path"])}
        try:
            cg = isolation.RunCgroup.create(entry["path"], f"hostcheck_{os.getpid()}")
        except Exception as error:  # noqa: BLE001
            item["create"] = {"ok": False, "error": str(error)}
            result["candidates"].append(item)
            continue
        item["create"] = {"ok": True, "path": str(cg.path), "migration_possible": cg.migration_possible}

        # Move a live process in, then cgroup.kill it: the accepted unit's own cgroup record.
        import subprocess
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"],
                                 preexec_fn=isolation.join_cgroup_preexec(cg))
        try:
            time.sleep(0.3)
            before = cg.procs()
            kill = cg.kill(grace=5.0)
            try:
                child.wait(timeout=5)
                child_rc = child.returncode
            except subprocess.TimeoutExpired:
                child.kill()
                child_rc = None
            item["record"] = {"cgroup": str(cg.path), "migration_possible": cg.migration_possible,
                              "processes_before": len(before), "kill": kill, "child_rc": child_rc,
                              "empty_after": kill.get("empty_after")}
            item["removed"] = cg.remove()
            item["ok"] = bool(item["record"]["processes_before"] >= 1
                              and item["record"]["kill"].get("empty_after") and item["removed"])
        except Exception as error:  # noqa: BLE001
            item["record_error"] = f"{type(error).__name__}: {error}"
            try:
                cg.kill(grace=1.0)
                cg.remove()
            except Exception:  # noqa: BLE001
                pass
            item["ok"] = False
        result["candidates"].append(item)
        if item.get("ok"):
            result["chosen"] = {"parent": entry["path"], "record": item["record"],
                                "migration_possible": cg.migration_possible}
            record = item
            break

    result["condition_C1_pass"] = bool(result["chosen"])
    if not result["condition_C1_pass"]:
        reasons = [{"path": c["candidate"]["path"], "error": c.get("create", {}).get("error")
                    or c.get("record_error") or "create/record failed"} for c in result["candidates"]]
        result["failure_reasons"] = reasons
    Path(args.parent_out).write_text((result["chosen"]["parent"] + "\n") if result["chosen"] else "")
    lib_iso.write_json(args.out, result)
    print(json.dumps({"C1_cgroup_pass": result["condition_C1_pass"],
                      "chosen": result["chosen"]["parent"] if result["chosen"] else None,
                      "failure_reasons": result.get("failure_reasons")}, default=str))
    return 0 if result["condition_C1_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
