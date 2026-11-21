# Captures: R1-T1-HOST-H200 harness-isolation host check on NEMO2 H200 (21 November 2026)

Sibling of `T1_H200_ISOLATION_CHECK_20261121.md`. ENGINEERING_ONLY; no T1 labels, no sweep-2 change.

- `out_759828/` — the transferred `out/` of HTCondor job **759828.0** exactly as produced on
  `g4402.nemo.privat` (slot `slot1_3@nemo2_gpu-131c50fcda@g4402`, one NVIDIA H200 `GPU-c483223d`), in the v2 GPU
  image `ghcr.io/dowlingwong/r1-htc-gpu@sha256:b1144ece…`:
  - `isolation_check.json` — the aggregate verdict (FAIL: C1, C4, C7, C8)
  - `host.json` — host facts and the conditions that need no sandbox (euid, ptrace_scope, timeout factor, image)
  - `userns.json` — the standalone user/mount/PID/network-namespace + `pivot_root` probe and the sandbox
    bind-remount flag probe
  - `cgroup.json`, `cgroup_parent.txt` — the cgroup v2 delegation probe (`RunCgroup.create` on every candidate)
  - `container_facts.txt` — container/image/GPU/cgroup facts captured inside the job
  - `sandbox_{old_68cdd1a,fix_5403392e}_{harness,trackp,usr}.json` — the unit's own `worker_sandbox_available`
    probe by revision and interpreter, with the `sys.path` hard check
  - `smoke_*.json` — the real isolated-fixture smokes (no-waiver refusals and the labelled diagnostic run that
    STOPs at the accept)
  - `gpu_smoke_diag.json` — the GPU smoke attempt (plain-process CUDA IPC control passes; the sandboxed run
    STOPs at the accept before CUDA IPC)
  - `pytest_isolation.json`, `logs/pytest_isolation.log` — the unit's own isolation test subset
  - `logs/` — stdout/stderr of every step; `step_results.txt` — the per-step return codes
  - `SHA256SUMS` — the job's own hashes; `isolation_h200.{out,err,log}` — HTCondor stdout/stderr/user log
- `payload/` — every script that ran (`run_checks.sh`, `lib_iso.py`, the `probe_*.py` scripts, `aggregate.py`)
  and `payload_sha256.txt` with the payload-tarball and JDL hashes.
- `jobs/` — `isolation_h200.jdl` (the single submitted H200 job); the CPU-only drafts and submissions that the
  site's GPU-node `Start` policy made impossible — `isolation_h200_cpu_759829.jdl`, the corrected
  `isolation_h200_cpu_759830.jdl` (both cancelled before starting) and the earlier draft
  `isolation_h200_cpu.jdl`; `isolation_l40s_supp.jdl`, an unused different-site idea kept for the record; and
  the pre/post job ads for 759828 (`job_ad_759828_{pre,post}.txt`).
- `harness_repo/repo_tips.txt` — `autoresearch_harness` branch tips and the accepted tree hashes used.
- `SHA256SUMS` — hashes of every file in this directory (it does not hash itself; the report is hashed
  separately with the commit).

Timeline (UTC): submitted 2026-11-21T00:33:38Z, started 01:08:58Z, ended 01:16:26Z (448 s, exit 0, one start).

No retry was made. The sweep-2 jobs were not modified; the job waited at priority 0 behind them and used one GPU
for its own 448 s run.
