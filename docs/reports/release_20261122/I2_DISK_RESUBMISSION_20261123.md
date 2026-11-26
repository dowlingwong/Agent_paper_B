# I2 request_disk change and resubmission (R1-TRACKP-I2-DISK), 23 November 2026

ENGINEERING_ONLY. I2 v2.1 CPU image check only; no Track P training.

## Change (reviewed, only request_disk)

- Before: `request_disk = 30000000` (sha256 `afa811bc…`).
- After: `request_disk = 2000000` (sha256 `89fdc6af…`); diff is exactly one line
  (`I2_probe_disk.diff`); image digest `c152c329…`, executable/arguments/transfer inputs,
  walltime 3600, `RequestCPUs=2`, `RequestMemory=8000`, `requirements = TARGET.ProvidesETPResources` and
  `queue 1` unchanged.
- Independent JDL-diff review: `docs/r1/reviews/I2_DISK_CHANGE_REVIEW_20261123.md` (ACCEPTED; sha256
  `c2147fea…`); author row R1-TRACKP-I2-DISK on main `3522e59b`.
- Rationale (main report `reports/release_20261122/I2_WAIT_20261122.md`): measured I2 v2 sandbox `DiskUsage≈30 kB`,
  `ImageSize≈50 MB`, `/work` output ≈13 MB; 2,000,000 kB (≈1.91 GiB) is >30× the measured footprint and expands the
  candidate ETP slot set from 37 to ~97–192 depending on the sample.

## Jobs

- Removed old **759919** (idle, `RequestDisk=30000000`).
- Resubmitted from the reviewed JDL: **cluster 759982** (`RequestDisk=2000000`, same CPU image digest);
  submitted 2026-11-23 ~09:24Z from deepthought.
- Watcher `watcher3.sh` (PID 148151) now waits for 759982 and the already-passed I3 759920; on I2 PASS it submits the
  staged Track P H200 smoke then E0. I2 checks, image, pool and staged units are unchanged.

## Status

I2 759982 is queued with 2 GB disk; no GPU work starts until it passes. Labels/evaluation remain sealed.
