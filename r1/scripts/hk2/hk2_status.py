#!/usr/bin/env python3
"""Poll only the current user's Slurm jobs and update the GPU ledger.

AI-assisted draft; independent review required before use. Both queries are
serialized with submission and rate-limited to one round per 60 seconds.
"""
import argparse
from pathlib import Path
import sys

import hk2_common as c


def update_ledger(config, outstanding, accounted):
    directory = c.records_dir(config)
    # This engineering path copies back to results/r1/trackg/hk2/gpu_ledger.csv
    # on the Mac, per the runbook's normal engineering-only copy-back.
    path = c.expand_path(str(config["values"]["results_root"])) / "engineering" / "gpu_ledger.csv"
    rows = c.read_ledger(path)
    phases = c.submission_phases(directory)
    jobs = {}
    for job in accounted:
        jid = str(job["job_id"])
        if jid in jobs:
            raise c.Hk2Error("duplicate sacct job ID: " + jid)
        jobs[jid] = job
    live = {str(job["job_id"]): job for job in outstanding}
    for jid in sorted(set(jobs) | set(live)):
        job = jobs.get(jid, {})
        active = live.get(jid, {})
        state = str(active.get("state", job.get("state", ""))).split()[0].split("+")[0]
        gpus = int(active.get("gpus", job.get("gpus", 0)))
        elapsed = int(job.get("elapsed_s", 0))
        old = rows.get(jid, {})
        rows[jid] = {"job_id": jid, "name": str(active.get("name", job.get("name", ""))),
                     "phase": phases.get(jid, old.get("phase", "")),
                     "partition": str(active.get("partition", job.get("partition", ""))),
                     "gpus": str(gpus), "elapsed_s": str(elapsed),
                     "allocation_gpu_h": format(c.gpu_hours(elapsed, gpus), ".8f"),
                     "end_state": state, "expected_end": "yes" if state in c.EXPECTED_END_STATES else "no",
                     "resubmit": "never" if state == "DEADLINE" else ""}
    c.write_ledger(path, rows)
    return path, rows


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=c.DEFAULT_CONFIG)
    args = p.parse_args(argv)
    try:
        config = c.load_config(args.config)
        directory = c.records_dir(config)
        with c.QueryLock(directory / "query.lock"):
            live, accounted = c.query_snapshot(config)
            path, rows = update_ledger(config, live, accounted)
            print("ledger=" + str(path))
            print("jobs=" + str(len(rows)))
            print("proposed_config=" + ",".join(config["proposed"]))
        return 0
    except (c.Hk2Error, OSError, ValueError) as exc:
        print("STOP: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
