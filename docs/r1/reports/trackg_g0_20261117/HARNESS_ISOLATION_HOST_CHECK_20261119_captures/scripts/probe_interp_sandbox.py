"""G0 host check: the run interpreters' sys.path against the runner's hard refusal, and the sandbox allow-list.

The runner refuses (hard RunnerError, no waiver) when an interpreter's sys.path holds the home directory, the runs
tree, or an ancestor of either. This probe calls the unit's own WorkingCopyRunner._sandbox_config() and
_interpreter_paths() for each interpreter the labels will use, and prints the exact sys.path/sys.prefix values.
"""
import json
import sys
import tempfile
import time
from pathlib import Path

REPO = Path("/home/dowling/r1_trackg_20261117/harness_iso_core")
BASE = Path("/home/dowling/r1_trackg_20261117/host_check_g0_20261119")
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tests" / "trackg"))

from isolated_fixture import isolated_spec_mapping, make_isolated_node  # noqa: E402
from autoresearch.trackg.node_template import TrackGNodeSpec  # noqa: E402
from autoresearch.trackg.runner import ResourceLimits, WorkingCopyRunner, _interpreter_paths  # noqa: E402

INTERPRETERS = [
    "/usr/bin/python3",
    "/home/dowling/r1_trackg_20261117/envs/torch312/bin/python",
    "/home/dowling/r1_trackg_20261117/envs/jax312/bin/python",
]


def main() -> int:
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    work_base = BASE / "work" / f"interp_{stamp}"
    work_base.mkdir(parents=True)
    node = make_isolated_node(work_base, "ok")
    spec = TrackGNodeSpec.from_mapping(isolated_spec_mapping())
    runs_root = BASE / "records"
    runner = WorkingCopyRunner(spec, node, runs_root)
    results = {}
    rc = 0
    for interpreter in INTERPRETERS:
        entry = {"interpreter": interpreter}
        entry["interpreter_real"] = str(Path(interpreter).resolve())
        try:
            paths = _interpreter_paths(interpreter)
            entry["resolved_paths"] = [str(p) for p in paths]
            q = __import__("subprocess").run([interpreter, "-s", "-c", "import json, sys, os; print(json.dumps({'executable': os.path.realpath(sys.executable), 'prefix': sys.prefix, 'base_prefix': sys.base_prefix, 'sys_path': sys.path}))"], capture_output=True, text=True, timeout=60, cwd="/")
            entry["raw"] = json.loads(q.stdout.strip().splitlines()[-1])
            # the unit's own sandbox-config builder runs the hard PYTHONPATH/sys.path check here
            run_dir = work_base / ("run_" + Path(interpreter).name + "_" + str(len(results)))
            run_dir.mkdir()
            work = run_dir / "work"
            work.mkdir()
            cfg = runner._sandbox_config(run_dir, work, interpreter)
            entry["sandbox_check"] = "passed"
            entry["sandbox_ro"] = cfg["ro"]
            entry["sandbox_ro_in_rw"] = cfg["ro_in_rw"]
            entry["sandbox_rw"] = cfg["rw"]
        except Exception as error:  # noqa: BLE001 - report the unit's refusal verbatim
            entry["sandbox_check"] = f"REFUSED {type(error).__name__}: {error}"
            rc = 1
        results[interpreter] = entry
    home = Path("/home/dowling")
    runs = BASE / "records"
    out = {"home": str(home), "runs_root": str(runs),
           "hard_error_condition": "sys.path entry == '/', HOME or runs_root, or an ancestor of HOME/runs_root",
           "interpreters": results}
    print(json.dumps(out, indent=2, sort_keys=True, default=str))
    return rc


if __name__ == "__main__":
    sys.exit(main())
