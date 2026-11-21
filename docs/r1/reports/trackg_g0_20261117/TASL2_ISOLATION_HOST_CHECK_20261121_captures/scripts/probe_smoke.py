"""R1-TRACKG-AR-U2-TASL2 condition 5: a real sandboxed isolated smoke whose record shows effective: true.

Adapted from the Ada G0 capture ``probe_smoke.py`` to the TASL-2 worktree and host-check root:
  REPO = /home/dowling/r1_trackp/harness_cond7a_20261121  (7330338, contains the accepted core 68cdd1a + the
          accepted Ada host-check fix 5403392e)
  BASE = /home/dowling/r1_engineering/tasl2_hostcheck_20261121

Run inside ``systemd-run --user --scope -p Delegate=yes``; ``AR_TEST_CGROUP_PARENT`` must name the writable
cgroup v2 directory of that subtree.  No waivers: the run must be ``effective: true`` with ``waivers {}`` and
``exceptions []``.  The record is the unit's own runner output.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

REPO = Path("/home/dowling/r1_trackp/harness_cond7a_20261121")
BASE = Path("/home/dowling/r1_engineering/tasl2_hostcheck_20261121")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(REPO))
    ap.add_argument("--base", default=str(BASE))
    ap.add_argument("--out", default="")
    ap.add_argument("--tag", default="g0_smoke")
    ap.add_argument("--interpreter", default=sys.executable)
    args = ap.parse_args()
    repo, base = Path(args.repo), Path(args.base)
    cg = os.environ.get("AR_TEST_CGROUP_PARENT")
    if not cg:
        print("AR_TEST_CGROUP_PARENT is not set", file=sys.stderr)
        return 2
    sys.path.insert(0, str(repo / "src"))
    sys.path.insert(0, str(repo / "tests" / "trackg"))

    from isolated_fixture import isolated_spec_mapping, make_isolated_node  # noqa: E402
    from autoresearch.trackg.node_template import TrackGNodeSpec  # noqa: E402
    from autoresearch.trackg.runner import ResourceLimits, WorkingCopyRunner  # noqa: E402

    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    work = base / "work" / f"{args.tag}_{stamp}"
    work.mkdir(parents=True)
    node = make_isolated_node(work, "ok")
    iso_block = {"entry": "parent.py", "args": ["{budget}"], "env": {"FAKE_NODE": "1"}}
    spec = TrackGNodeSpec.from_mapping(isolated_spec_mapping(isolation=iso_block))
    waivers: dict = {}
    limits = ResourceLimits(uncapped_reason="TASL-2 host-check smoke: CPU/memory uncapped, one fake node",
                            measured_run_seconds=20.0, kill_grace_seconds=3.0,
                            cgroup_parent=cg, isolation_waivers=waivers)
    runner = WorkingCopyRunner(spec, node, base / "records")
    result = runner.run(f"{args.tag}_{stamp}", limits, interpreter=args.interpreter)
    iso = {k: v for k, v in result.record["isolation"].items() if k != "_verified_log"}
    out = {"tag": args.tag, "utc": stamp, "repo": str(repo), "base": str(base),
           "interpreter": args.interpreter, "cgroup_parent": cg,
           "run_dir": str(result.run_dir), "outcome": result.record["outcome"],
           "isolation": iso, "record_path": str(result.run_dir / "run_record.json"),
           "result_channel": (result.run_dir / "result_channel.txt").read_text(),
           "run_log_tail": (result.run_dir / "run.log").read_text().splitlines()[-8:]}
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(out, indent=2, sort_keys=True, default=str) + "\n",
                                  encoding="utf-8")
    print(json.dumps(out, indent=2, sort_keys=True, default=str))
    condition = bool(iso.get("effective") is True and not iso.get("waivers")
                     and not iso.get("exceptions") and iso.get("worker_sandbox") is not None
                     and result.record["outcome"].get("kind") == "ok")
    print("CONDITION_5_PASS " + json.dumps({"condition_5_pass": condition}))
    return 0 if condition else 1


if __name__ == "__main__":
    sys.exit(main())
