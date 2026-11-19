"""G0 root-cause confirmation: run the unit's own worker_sandbox_available() against a scratch copy of the
harness whose ar_isolated.bind() remount flags include MS_NODEV|MS_NOEXEC (the only change). This checks that
the /sys remount EPERM is the whole cause of the Ada sandbox refusal. It does NOT touch any accepted worktree.
"""
import json
import os
import sys
import time
from pathlib import Path

REPO = Path("/tmp/ada_iso_fixcheck")
BASE = Path("/home/dowling/r1_trackg_20261117/host_check_g0_20261119")
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tests" / "trackg"))

from autoresearch.trackg import isolation  # noqa: E402
from isolated_fixture import isolated_spec_mapping, make_isolated_node  # noqa: E402
from autoresearch.trackg.node_template import TrackGNodeSpec  # noqa: E402
from autoresearch.trackg.runner import WorkingCopyRunner  # noqa: E402


def main() -> int:
    interp = sys.argv[1] if len(sys.argv) > 1 else "/usr/bin/python3"
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + f"_{os.getpid()}"
    base = BASE / "work" / f"fixcheck_{stamp}"
    base.mkdir(parents=True)
    node = make_isolated_node(base, "ok")
    spec = TrackGNodeSpec.from_mapping(isolated_spec_mapping())
    runner = WorkingCopyRunner(spec, node, BASE / "records")
    run_dir = base / "run"
    run_dir.mkdir()
    work = run_dir / "work"
    work.mkdir()
    cfg = runner._sandbox_config(run_dir, work, interp)
    ok, why = isolation.worker_sandbox_available(interp, cfg, run_dir / "_sandbox_probe")
    print(json.dumps({"repo": str(REPO), "interpreter": interp, "euid": os.geteuid(), "ok": ok, "why": why},
                     indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
