# Sweep-2 B.2 audit — STOP report, 22 November 2026

**ENGINEERING_ONLY. No label/evaluation file was written; labels stay sealed.** The audit did not complete. Two attempts
were made from the reviewed code checkout at `db7f344d` (paper HEAD), with published main `3c3f822a`, the addendum
`c3_sweep2_b2_addendum_20261122.md` (approved on main, sha256 `2e5a6a6d…`) and the reviewed batch/table (pins
`b4697c…`, `82c760…`, `379b17ca…`, `de6d63b5…`).

## Attempt 1 — immediate STOP (worker interpreter mismatch)

- command launched with the venv's `python` binary; the worker probe resolves `python3` to `venv/bin/python3`, so the
  code's requirement `worker_python` equals `venv/bin/python` failed before any seed run.
- output: `results/r1/evidence/C3_audit_EVIDENCE_20261122T103401Z/`; `STOP.json` sha256
  **`54bbea1038a56cc2d5025be0547a895d58aa140311b1a51f2dfe8ed3f872ed31`**; no seed block/completion.
- the attempt is retained; no resume.

## Attempt 2 — operator STOP on a co-tenancy breach

- relaunched with `venv/bin/python3`; the environment/harness/pins checks passed and seed runs began.
- **The launch environment did not pin BLAS/OpenMP threads** (`OMP_NUM_THREADS`, `MKL_NUM_THREADS`,
  `OPENBLAS_NUM_THREADS` were not set to 1 as in the e1 basis). The 16 audit workers then used most of the 40 cores:
  `load average` rose from 1.07 at launch to **112–135**, so the addendum's co-tenancy protocol ("16 workers, at least
  10 of 40 cores free; a breach during the run is a STOP") was violated. Throughput collapsed (~784 rows / 84 configs
  in 45 min vs the 52.5 min full-run projection).
- The operator stopped the run at 2026-11-22T12:25Z before the 10,800 s deadline to avoid monopolising the host. The
  output directory `results/r1/evidence/C3_audit_EVIDENCE_20261122T103708Z/` is retained (784 run rows, 84 seed
  journals, no `evidence_completion.json`, no code-written `STOP.json`); the operator record is `STOP_OPERATOR.txt`
  with `SHA256SUMS` sha256 **`022b22725cec34cb0822d8f70212d521af1cf166388eafd568d05ccec9a6cc33`**. No resume.

## What is needed

1. Author decision on a new audit attempt/addendum (a STOP is retained; the addendum's deadline and no-resume rule
   stand). A corrected launch must export `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1` (as in the e1
   environment basis) so the 16 workers leave at least 10 of 40 cores free, and must monitor co-tenancy during the run.
2. The 52.5 min projection in the addendum came from the sweep-1 B.2 throughput (4,660 runs / 23 min) and does not
   describe the sweep-2 mix; with the threads pinned the run still needs a realistic deadline. This is a planning
   correction for the author/addendum, not a threshold change.

## Related

- Image v2.1: I3 job 759920 PASS (v2.1 GPU digest, H200); I2 job 759919 still waits for a disk-capable
  `ProvidesETPResources` slot. Staged Track P H200 smoke/E0 have not been run.
- No branch/worktree/image tag/file was deleted; the sealed tree was only read.
