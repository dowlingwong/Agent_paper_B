"""R1-T1-HOST-H200: the accepted unit's own worker-sandbox probe (host condition §3 row 3 / experiment-agent
item 6) and the hard ``sys.path`` check (§3 last row, no waiver).

Runs ``isolation.worker_sandbox_available()`` -- the exact call the accepted runner makes before it writes an
isolated run record -- for one interpreter and one accepted core revision.  A refusal here on the accepted
revision is the host refusing the sandbox; on the as-instructed ``68cdd1a`` revision it reproduces the known
pre-fix defects (review defect A: bind remount drops locked nodev/noexec).

Writes one JSON per (revision, interpreter); rc 0 iff the probe says ok.
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--interpreter", default=sys.executable)
    parser.add_argument("--revision", default="unknown")
    parser.add_argument("--tag", default="sandbox")
    parser.add_argument("--base", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    base = Path(args.base) / f"sandbox_{args.tag}_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}_{os.getpid()}"
    base.mkdir(parents=True)
    result: dict = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "revision": args.revision, "repo": args.repo,
        "interpreter": args.interpreter, "interpreter_realpath": os.path.realpath(args.interpreter),
        "interpreter_is_symlink": os.path.islink(args.interpreter),
        "euid": os.geteuid(), "tag": args.tag,
    }
    try:
        sys.path.insert(0, os.path.join(args.repo, "src"))
        sys.path.insert(0, os.path.join(args.repo, "tests", "trackg"))
        from autoresearch.trackg import isolation  # noqa: E402
        from autoresearch.trackg.node_template import TrackGNodeSpec  # noqa: E402
        from autoresearch.trackg.runner import RunnerError, WorkingCopyRunner, _interpreter_paths  # noqa: E402
        from isolated_fixture import isolated_spec_mapping, make_isolated_node  # noqa: E402

        result["ptrace_scope"] = isolation.ptrace_scope()
        result["interpreter_paths"] = [str(p) for p in _interpreter_paths(args.interpreter)]

        node = make_isolated_node(base, "ok")
        spec = TrackGNodeSpec.from_mapping(isolated_spec_mapping())
        runner = WorkingCopyRunner(spec, node, base / "runs")
        run_dir = base / "run"
        run_dir.mkdir()
        work = run_dir / "work"
        work.mkdir()
        try:
            cfg = runner._sandbox_config(run_dir, work, args.interpreter)
            result["sys_path_hard_check"] = {"ok": True}
            result["worker_sandbox"] = {
                "ro": cfg["ro"], "ro_flat": cfg["ro_flat"], "rw": cfg["rw"], "dev": cfg["dev"],
                "shared_dev_shm": cfg["shared_dev_shm"],
                "ro_entries_pointing_home_or_runs": [p for p in cfg["ro"]
                                                     if str(base) in p or p.startswith(os.environ.get("HOME", "/nonexistent"))],
            }
        except RunnerError as error:
            result["sys_path_hard_check"] = {"ok": False, "error": str(error)}
            result["ok"] = False
            lib_iso.write_json(args.out, result)
            print(json.dumps({"revision": args.revision, "interpreter": args.interpreter,
                              "sandbox_ok": False, "sys_path_hard_check": result["sys_path_hard_check"]}))
            return 1
        ok, why = isolation.worker_sandbox_available(args.interpreter, cfg, run_dir / "_sandbox_probe")
        result["sandbox_probe"] = {"ok": bool(ok), "why": why}
        result["ok"] = bool(ok)
    except Exception:  # noqa: BLE001
        result["ok"] = False
        result["error"] = traceback.format_exc()
    lib_iso.write_json(args.out, result)
    print(json.dumps({"revision": args.revision, "interpreter": args.interpreter,
                      "sandbox_ok": result.get("sandbox_probe", {}).get("ok"),
                      "why": result.get("sandbox_probe", {}).get("why"),
                      "sys_path_hard_check": result.get("sys_path_hard_check")}, default=str))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
