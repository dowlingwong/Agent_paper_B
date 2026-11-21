"""R1-T1-HOST-H200 host condition §3 row 6 (experiment-agent item 6): a real sandboxed isolated smoke through
the accepted unit's own fixture and ``WorkingCopyRunner``, with an explicit run interpreter and a run cgroup.

Default: **no waivers** (the condition is met only if the record says ``effective: true, waivers {}``).  With
``--diag-waivers no_cgroup[,ptrace_scope][,root]`` the probe records the labelled diagnostic waivers instead --
used only to show whether the sandbox/pivot_root mechanics work when a host condition fails; such a run is
reported as a diagnostic and is never effective.

Writes JSON + copies the run artifacts under ``--out``.  rc: 0 = ran and effective+ok; 1 = ran but not
effective; 2 = refused (no record).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
import traceback
from pathlib import Path

import lib_iso

DIAG_REASONS = {
    "no_cgroup": "diagnostic-only host check: no writable delegated cgroup v2 subtree in this HTCondor container "
                 "(condition C1 FAIL); the run is NOT effective",
    "ptrace_scope": "diagnostic-only host check: Yama ptrace_scope < 1 in this HTCondor container "
                    "(condition C4 FAIL); the run is NOT effective",
    "root": "diagnostic-only host check: the container job runs as root (condition C2 FAIL); the run is NOT "
            "effective",
}


def copy_run_artifacts(run_dir: Path, out_dir: Path, tag: str) -> list[str]:
    target = out_dir / "records" / tag
    target.mkdir(parents=True, exist_ok=True)
    copied = []
    for name in ("run_record.json", "run.log", "result_channel.txt", "determinism_shim.json"):
        source = run_dir / name
        if source.exists():
            shutil.copy2(source, target / name)
            copied.append(str(target / name))
    return copied


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--interpreter", default=sys.executable)
    parser.add_argument("--revision", default="unknown")
    parser.add_argument("--tag", default="smoke")
    parser.add_argument("--base", required=True)
    parser.add_argument("--cgroup-parent", default=os.environ.get("AR_TEST_CGROUP_PARENT", ""))
    parser.add_argument("--diag-waivers", default="",
                        help="diagnostic only: comma list among no_cgroup,ptrace_scope,root")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out_dir = Path(args.out).parent
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    diag = [name.strip() for name in args.diag_waivers.split(",") if name.strip()]
    result: dict = {
        "utc": stamp, "revision": args.revision, "repo": args.repo, "interpreter": args.interpreter,
        "tag": args.tag, "euid": os.geteuid(), "cgroup_parent": args.cgroup_parent or None,
        "diagnostic_waivers": diag,
    }
    if not args.cgroup_parent and "no_cgroup" not in diag:
        result["refused"] = True
        result["refusal_reason"] = ("no writable delegated cgroup v2 parent was found (host condition C1 FAIL); "
                                    "an isolated run with no waivers needs limits.cgroup_parent")
        lib_iso.write_json(args.out, result)
        print(json.dumps({"tag": args.tag, "refused": True, "reason": result["refusal_reason"]}))
        return 2
    base = Path(args.base) / f"smoke_{args.tag}_{stamp}_{os.getpid()}"
    base.mkdir(parents=True)
    try:
        sys.path.insert(0, os.path.join(args.repo, "src"))
        sys.path.insert(0, os.path.join(args.repo, "tests", "trackg"))
        from autoresearch.trackg.node_template import TrackGNodeSpec  # noqa: E402
        from autoresearch.trackg.runner import RunnerError, ResourceLimits, WorkingCopyRunner  # noqa: E402
        from isolated_fixture import isolated_spec_mapping, make_isolated_node  # noqa: E402

        node = make_isolated_node(base, "ok")
        spec = TrackGNodeSpec.from_mapping(isolated_spec_mapping())
        runner = WorkingCopyRunner(spec, node, base / "runs")
        waivers = {name: DIAG_REASONS[name] for name in diag if name in DIAG_REASONS}
        limits = ResourceLimits(
            uncapped_reason="host-check fixture: CPU/memory caps are not needed for the 5-step fake node",
            measured_run_seconds=20.0, kill_grace_seconds=3.0,
            cgroup_parent=args.cgroup_parent or None, isolation_waivers=waivers)
        try:
            run = runner.run(f"h200_{args.tag}_{stamp}", limits, interpreter=args.interpreter)
        except RunnerError as error:
            result["refused"] = True
            result["refusal_reason"] = str(error)
            lib_iso.write_json(args.out, result)
            print(json.dumps({"tag": args.tag, "refused": True, "reason": str(error)}))
            return 2
        result["refused"] = False
        isolation = {k: v for k, v in run.record["isolation"].items() if k != "_verified_log"}
        result.update({
            "run_dir": str(run.run_dir), "record": run.record, "isolation": isolation,
            "outcome": run.record.get("outcome"),
            "result_channel": (run.run_dir / "result_channel.txt").read_text(errors="replace")
            if (run.run_dir / "result_channel.txt").exists() else None,
        })
        result["artifacts"] = copy_run_artifacts(run.run_dir, out_dir, args.tag)
        effective = (isolation.get("effective") is True and isolation.get("waivers") == {}
                     and isolation.get("exceptions") == [] and isolation.get("worker_sandbox") is not None
                     and (run.record.get("outcome") or {}).get("kind") == "ok")
        result["condition_pass"] = bool(effective)
        result["sandbox_ran"] = isolation.get("worker_sandbox") is not None
    except Exception:  # noqa: BLE001
        result["error"] = traceback.format_exc()
        result["condition_pass"] = False
    lib_iso.write_json(args.out, result)
    print(json.dumps({"tag": args.tag, "refused": result.get("refused", False),
                      "outcome": result.get("outcome"),
                      "effective": (result.get("isolation") or {}).get("effective"),
                      "waivers": (result.get("isolation") or {}).get("waivers"),
                      "exceptions": (result.get("isolation") or {}).get("exceptions"),
                      "sandbox_ran": result.get("sandbox_ran"),
                      "condition_pass": result.get("condition_pass")}, default=str))
    if result.get("refused"):
        return 2
    return 0 if result.get("condition_pass") else 1


if __name__ == "__main__":
    sys.exit(main())
