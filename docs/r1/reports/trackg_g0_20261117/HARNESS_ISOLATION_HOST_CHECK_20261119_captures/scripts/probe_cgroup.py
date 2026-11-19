"""G0 host check: delegated cgroup v2 subtree, using the core unit's own RunCgroup API.

Run inside a delegated cgroup (systemd-run --user --scope -p Delegate=yes) so migration into a child cgroup is
permitted by the kernel (common-ancestor cgroup.procs must be writable). AR_TEST_CGROUP_PARENT names the
delegated directory to create the run cgroup under.
"""
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

REPO = Path("/home/dowling/r1_trackg_20261117/harness_iso_core")
sys.path.insert(0, str(REPO / "src"))

from autoresearch.trackg import isolation  # noqa: E402


def main() -> int:
    parent = os.environ.get("AR_TEST_CGROUP_PARENT")
    if not parent:
        print("AR_TEST_CGROUP_PARENT is not set", file=sys.stderr)
        return 2
    parent = Path(parent)
    out = {"parent": str(parent), "parent_owner": parent.stat().st_uid,
           "nsdelegate": isolation.cgroup2_nsdelegate(parent),
           "my_cgroup": Path("/proc/self/cgroup").read_text().strip()}
    cg = isolation.RunCgroup.create(parent, "g0_cgroup_probe")
    out["created"] = str(cg.path)
    out["created_owner"] = cg.path.stat().st_uid
    out["cgroup_kill_file"] = (cg.path / "cgroup.kill").is_file()
    out["procs_writable"] = os.access(cg.path / "cgroup.procs", os.W_OK)
    out["migration_possible"] = cg.migration_possible
    # a real process in the run cgroup, killed with cgroup.kill (the unit's own code path)
    proc = subprocess.Popen(["sleep", "300"])
    procs_file = cg.path / "cgroup.procs"
    moved = None
    try:
        procs_file.write_text(str(proc.pid))
        moved = "ok"
    except OSError as error:
        moved = f"{type(error).__name__}: {error}"
    out["move"] = moved
    out["cgroup_procs_after_move"] = cg.procs()
    out["populated"] = cg.populated()
    out["kill"] = cg.kill(grace=3.0)
    time.sleep(0.1)
    proc.poll()
    out["process_returncode_after_kill"] = proc.returncode
    try:
        proc.kill()
    except OSError:
        pass
    out["removed"] = cg.remove()
    print(json.dumps(out, indent=2, sort_keys=True, default=str))
    ok = (moved == "ok" and out["kill"]["empty_after"] and proc.returncode is not None and out["removed"])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
