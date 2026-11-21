"""G0 host check: real sandboxed isolated smoke with the core unit's own fixture and runner (no waivers).

Run inside a delegated cgroup (systemd-run --user --scope -p Delegate=yes); AR_TEST_CGROUP_PARENT must name a
writable cgroup v2 directory in that subtree. The run record is written by the unit's runner itself.
"""
import json
import os
import sys
import time
from pathlib import Path

REPO = Path("/home/dowling/r1_trackg_20261117/harness_iso_core")
BASE = Path("/home/dowling/r1_trackg_20261117/host_check_g0_20261119")
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tests" / "trackg"))

from isolated_fixture import isolated_spec_mapping, make_isolated_node  # noqa: E402
from autoresearch.trackg.node_template import TrackGNodeSpec  # noqa: E402
from autoresearch.trackg.runner import ResourceLimits, WorkingCopyRunner  # noqa: E402


def main() -> int:
    cg = os.environ.get("AR_TEST_CGROUP_PARENT")
    if not cg:
        print("AR_TEST_CGROUP_PARENT is not set", file=sys.stderr)
        return 2
    tag = os.environ.get("AR_HOSTCHECK_TAG", "default")
    shared_dev_shm = os.environ.get("AR_HOSTCHECK_SHARED_DEV_SHM") == "1"
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    work = BASE / "work" / f"{tag}_{stamp}"
    work.mkdir(parents=True)
    node = make_isolated_node(work, "ok")
    iso_block = {"entry": "parent.py", "args": ["{budget}"], "env": {"FAKE_NODE": "1"}}
    if shared_dev_shm:
        iso_block["shared_dev_shm"] = True
    spec = TrackGNodeSpec.from_mapping(isolated_spec_mapping(isolation=iso_block))
    waivers = {}
    if os.environ.get("AR_HOSTCHECK_NO_WORKER_SANDBOX") == "1":
        waivers["no_worker_sandbox"] = "G0 diagnostic control: the host refuses the sandbox (see sandbox check)"
    limits = ResourceLimits(uncapped_reason="G0 host-check smoke, no CPU/memory cap", measured_run_seconds=20.0,
                            kill_grace_seconds=3.0, cgroup_parent=cg, isolation_waivers=waivers)
    runner = WorkingCopyRunner(spec, node, BASE / "records")
    result = runner.run(f"g0_{tag}_{stamp}", limits)
    iso = {k: v for k, v in result.record["isolation"].items() if k != "_verified_log"}
    out = {"tag": tag, "run_dir": str(result.run_dir), "outcome": result.record["outcome"],
           "isolation": iso, "record_path": str(result.run_dir / "run_record.json"),
           "result_channel": (result.run_dir / "result_channel.txt").read_text(),
           "run_log_tail": (result.run_dir / "run.log").read_text().splitlines()[-4:]}
    print(json.dumps(out, indent=2, sort_keys=True, default=str))
    if os.environ.get("AR_HOSTCHECK_NO_WORKER_SANDBOX") == "1":
        return 0 if iso.get("waivers") == {"no_worker_sandbox": "G0 diagnostic control: the host refuses the "
                                           "sandbox (see sandbox check)"} and iso.get("effective") is False else 1
    if shared_dev_shm:
        return 0 if iso.get("exceptions") == ["shared_dev_shm"] and iso.get("effective") is False else 1
    return 0 if iso.get("effective") is True and not iso.get("waivers") else 1


if __name__ == "__main__":
    sys.exit(main())
