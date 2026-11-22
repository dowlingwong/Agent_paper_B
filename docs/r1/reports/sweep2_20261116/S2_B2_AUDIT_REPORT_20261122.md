# Sweep-2 B.2 audit — complete attempt 3 (R1-SWEEP2-B2-RETRY option A), 22 November 2026

**EVIDENCE audit. Labels stay sealed under R1-BX-D8-CONFIRM; this report contains no label or evaluation values.**
Authority: the addendum `docs/r1/authorizations/c3_sweep2_b2_addendum_20261122.md` (approved, sha256
`2e5a6a6dc8286c734759e010cc43a5c5a5df252b471b278811f4fd1646fd7d50`), R1-SWEEP2-B2-GO, R1-SWEEP2-B2-DECISIONS
and R1-SWEEP2-B2-RETRY option A. Code checkout exactly `db7f344d6ac372737444db5ab036d370543ea65f` (clean), published
main at start `52f4e3e5…`; harness `6adf3859de66c4814fcf376eed59880fbd8eeaf7`.

## Design

- Sweep-2 batch `s2ev-20261119-a`: 2,500 eligible, 2,512 duplicates, 0 no-ops; 1,064 unique configurations.
- K = 10; label seeds 7001–7005, evaluation seeds 7006–7010; 16 workers; host deepthought, CPUs only.
- Interpreter `/ceph/dwong/r1_prepare_20261025/venv/bin/python3`; `OMP_NUM_THREADS=MKL_NUM_THREADS=OPENBLAS_NUM_THREADS=NUMEXPR_NUM_THREADS=1`
  (recorded in `cotenancy.log`).
- New scratch `/tmp/r1_c3_audit_EVIDENCE_20261122T164726Z`, new output
  `results/r1/evidence/C3_audit_EVIDENCE_20261122T164726Z`; no resume. `--deadline 21600`.
- Pre-launch load1 12.25 → 27.75 free cores; during the run the once-per-minute cotenancy log has **34 samples,
  minimum 13.05 free cores (≥10)**; audit worker CPU sum stayed ~8–16 cores (thread pinning held).

## Result

- **PASS**: 10,640 seed runs = 1,064 × 10; all success, finite metric, `changed_files=false`; 0 bad runs, 0 non-finite.
- label block 2,500 rows; evaluation block 2,500 rows; counts by kind equal the plan (2,500/2,512/0).
- `evidence_completion.json` schema `r1.c3_audit_completion/4`, source `sweep2`; hashes:
  runs `cf57bf7e…`, label block `9ab3cb26…`, evaluation block `1e3a0e7a…`, plan `4479b1dd…`, index `b4697c49…`,
  proposals `379b17ca…`, configs `de6d63b5…`, addendum `2e5a6a6d…`; all recomputed and equal.
- Wall: launch 16:47:26Z → completion 18:20:09Z = **5,563 s** (within 21,600 s); no STOP.
- Harness equivalence record: audit harness 6adf3859 vs sweep-2 pin a3fedbbd; the listed paths
  (`nodes`, `configs`, `harness`, `uv.lock`, `src/autoresearch/worker`, `src/autoresearch/nodes`,
  `src/autoresearch/common`, `src/autoresearch/manager/base.py`) have `diff: empty`; the 8 changed-elsewhere files are
  recorded in `environment.json`.
- Sealed copy `/ceph/srv/dwong/paperb/sweep2_audit/s2ev-20261119-a_20261122T164726Z/`; `SHA256SUMS` verifies;
  `AUDIT_SEAL.json` sha256 `55fdb2252588c8e2ec1392e480b5862227c2337ed105d11fea111c6d0a2c3eb5` (tree/SHA256SUMS
  digest `a9da0aae…`; completion sha `f751681f…`).

## Attempts 1 and 2 (disclosed, seed results unused)

- Attempt 1 (`C3_audit_EVIDENCE_20261122T103401Z`) stopped immediately on a worker-interpreter mismatch: launched
  with `venv/bin/python` while the worker probe resolves `venv/bin/python3`. `STOP.json` sha256
  `54bbea1038a56cc2d5025be0547a895d58aa140311b1a51f2dfe8ed3f872ed31`; no seed result used.
- Attempt 2 (`C3_audit_EVIDENCE_20261122T103708Z`) started but was operator-stopped after 45 min for a co-tenancy
  breach: BLAS/OpenMP threads were not pinned and the 16 workers drove the host load to 112–135. Record
  `STOP_OPERATOR.txt`; output SHA256SUMS sha256 `022b22725cec34cb0822d8f70212d521af1cf166388eafd568d05ccec9a6cc33`;
  no seed result used. Both directories are retained unchanged.

## Status

Independent review of this run: pending (branch `ops-s2-audit-20261122`). Labels remain sealed; the label tables may
be consumed only after the author signs the sweep-2 release row. No U4/U5 or other training was started.
