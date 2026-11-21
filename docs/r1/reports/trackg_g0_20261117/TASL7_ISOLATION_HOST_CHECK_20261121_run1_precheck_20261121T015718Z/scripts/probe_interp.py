"""R1-T1-HOST-TASL condition 4: non-root euid and the unit's own hard ``sys.path`` check.

The unit's check is ``WorkingCopyRunner._sandbox_config`` (runner.py): it refuses a run whose interpreter's
``sys.path`` holds the home directory, the runs tree, or an ancestor of either (hard ``RunnerError``, **no
waiver**).  This probe calls the unit's own code for both interpreters the unit will use:
  * ``/usr/bin/python3`` (system, 3.10.12), and
  * ``trackp-gpu`` venv (``/home/dowling/r1_trackp/venvs/trackp-gpu/bin/python``, 3.12.15, torch 2.6.0+cu124).

It also runs the unit's own ``isolation.worker_sandbox_available`` for each interpreter (the §3 item 1/6
end-to-end sandbox check) and records the exact error if either fails.  A venv ``sys.path`` refusal is a STOP:
the requirement is explicit that it is not waived.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path

SYSTEM_PY = "/usr/bin/python3"
VENV_PY = "/home/dowling/r1_trackp/venvs/trackp-gpu/bin/python"


def interpreter_facts(interpreter: str) -> dict:
    code = ("import json, os, sys; print(json.dumps({'executable': sys.executable, "
            "'realpath': os.path.realpath(sys.executable), 'version': sys.version.split()[0], "
            "'prefix': sys.prefix, 'base_prefix': sys.base_prefix, "
            "'sys_path': [p for p in sys.path if p]}))")
    try:
        out = subprocess.run([interpreter, "-s", "-c", code], capture_output=True, text=True,
                             timeout=60, cwd="/")
        facts = json.loads(out.stdout.strip().splitlines()[-1]) if out.returncode == 0 else {}
        facts["rc"] = out.returncode
        if out.returncode != 0:
            facts["stderr"] = out.stderr[-2000:]
        return facts
    except (OSError, subprocess.SubprocessError, ValueError, IndexError) as error:
        return {"error": f"{type(error).__name__}: {error}"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--text", default="")
    args = ap.parse_args()
    repo = Path(args.repo)
    base = Path(args.base)
    sys.path.insert(0, str(repo / "src"))
    sys.path.insert(0, str(repo / "tests" / "trackg"))

    from autoresearch.trackg import isolation  # noqa: E402
    from autoresearch.trackg.node_template import TrackGNodeSpec  # noqa: E402
    from autoresearch.trackg.runner import RunnerError, WorkingCopyRunner, _interpreter_paths  # noqa: E402
    from isolated_fixture import isolated_spec_mapping, make_isolated_node  # noqa: E402

    result: dict = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "euid": os.geteuid(), "uid": os.getuid(), "is_root": os.geteuid() == 0,
        "home": os.environ.get("HOME"),
        "interpreters": {},
    }

    tmp = Path(tempfile.mkdtemp(dir=str(base), prefix="interp_check_"))
    node = make_isolated_node(tmp / "node", "ok")
    spec = TrackGNodeSpec.from_mapping(isolated_spec_mapping())
    runs_root = tmp / "runs"
    runs_root.mkdir()
    runner = WorkingCopyRunner(spec, node, runs_root)
    result["runs_root"] = str(runs_root)
    result["node_root"] = str(node)

    for tag, interpreter in (("system_py3", SYSTEM_PY), ("venv_trackp_gpu", VENV_PY)):
        item: dict = {"interpreter": interpreter, "exists": os.path.exists(interpreter),
                      "executable": os.access(interpreter, os.X_OK)}
        item["facts"] = interpreter_facts(interpreter) if item["exists"] else {}
        run_dir = runs_root / f"check_{tag}"
        work = run_dir / "work"
        run_dir.mkdir(parents=True)
        try:
            interp = _interpreter_paths(interpreter)
            item["interpreter_paths"] = [str(p) for p in interp]
            home = Path(os.environ.get("HOME", "/nonexistent")).resolve()
            broad = [str(p) for p in interp
                     if p.resolve() in (Path("/"), home, runs_root)
                     or any(p.resolve() in q.parents for q in (home, runs_root))]
            item["broad_entries"] = broad
            config = runner._sandbox_config(run_dir, work, interpreter)
            item["sandbox_config_ok"] = True
            item["sandbox_config_ro_count"] = len(config.get("ro", []))
            item["sandbox_config_ro"] = config.get("ro", [])
            item["sandbox_config_rw"] = config.get("rw", [])
            item["sandbox_config_shared_dev_shm"] = config.get("shared_dev_shm")
            ok, why = isolation.worker_sandbox_available(interpreter, config,
                                                        run_dir / "_sandbox_probe")
            item["sandbox_available"] = ok
            item["sandbox_available_detail"] = why
        except RunnerError as error:
            item["sandbox_config_ok"] = False
            item["hard_check_error"] = str(error)
        except Exception as error:  # noqa: BLE001
            item["sandbox_config_ok"] = False
            item["error"] = f"{type(error).__name__}: {error}"
            item["traceback"] = traceback.format_exc()
        item["condition_pass"] = bool(item.get("sandbox_config_ok"))
        result["interpreters"][tag] = item

    shutil.rmtree(tmp, ignore_errors=True)
    result["condition_4_pass"] = all(v.get("condition_pass") for v in result["interpreters"].values())
    # The venv check is the one the task singles out; record it separately for a hard STOP.
    result["venv_check_pass"] = bool(result["interpreters"]["venv_trackp_gpu"].get("condition_pass"))
    result["euid_check_pass"] = os.geteuid() != 0

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if args.text:
        lines = [f"euid={result['euid']} non_root={result['euid_check_pass']}",
                 f"home={result['home']} runs_root={result['runs_root']}"]
        for tag, item in result["interpreters"].items():
            lines.append(f"--- {tag}: {item['interpreter']}")
            lines.append(f"  version={item.get('facts', {}).get('version')} "
                         f"executable={item.get('facts', {}).get('executable')}")
            lines.append(f"  sys_path={item.get('facts', {}).get('sys_path')}")
            lines.append(f"  broad_entries={item.get('broad_entries')}")
            lines.append(f"  sandbox_config_ok={item.get('sandbox_config_ok')} "
                         f"sandbox_available={item.get('sandbox_available')}")
            if item.get("hard_check_error"):
                lines.append(f"  HARD_CHECK_ERROR={item['hard_check_error']}")
            if item.get("sandbox_available_detail") and item.get("sandbox_available_detail") != "ok":
                lines.append(f"  sandbox_detail={item['sandbox_available_detail']}")
        lines.append(f"condition_4_pass={result['condition_4_pass']} venv_check_pass={result['venv_check_pass']}")
        Path(args.text).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("RESULT " + json.dumps({"condition_4_pass": result["condition_4_pass"],
                                  "venv_check_pass": result["venv_check_pass"],
                                  "euid_check_pass": result["euid_check_pass"],
                                  "interpreters": {k: {"sandbox_config_ok": v.get("sandbox_config_ok"),
                                                       "sandbox_available": v.get("sandbox_available"),
                                                       "hard_check_error": v.get("hard_check_error")}
                                                   for k, v in result["interpreters"].items()}},
                         default=str))
    return 0 if result["condition_4_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
