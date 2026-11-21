# TASL-7 isolation host-check captures — 21 November 2026

R1-T1-HOST-TASL / R1-TRACKG-AR-U2-TASL2 context: TASL-7 host check of
`docs/r1/reports/HARNESS_ISOLATION_20261117.md` §3 (host conditions) plus a real sandboxed GPU smoke.
ENGINEERING_ONLY; independent review required before any autoresearch kit / U2 use.

- Host: TASL-7 (`ssh tasl7`), uid/euid 1011 `dowling` (non-root), Linux 6.8.0-149-generic,
  RTX 4090 24 GB, driver 580.178.04, GPU `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`.
- Harness worktree: `/home/dowling/r1_trackp/harness_cond7a_20261121_t7` @ `7330338` (detached, clean),
  which contains the accepted isolation core `68cdd1a` and the accepted Ada host-check fix `5403392e`.
- Run root: `/home/dowling/r1_engineering/tasl7_hostcheck_20261121/` (new; no pre-existing host work deleted
  or moved; no push, no commit; TASL-2 / the Track P attempt-1 archive and lease log / HTCondor and deepthought
  untouched).
- Session: `2026-11-21T01:59:12Z`–`2026-11-21T02:00:19Z` (one orchestrated `scripts/run_checks.sh` run;
  `logs/run_checks.log`). The first orchestration at `01:57:18Z` (before a comparison-script fix) also passed
  all conditions; its captures are preserved on the host only as
  `../captures_precheck_run1_20261121T015718Z/` and in this bundle under `run1_precheck_20261121T015718Z/`.

## Files

| Path | What it is |
|---|---|
| `SUMMARY.json`, `SUMMARY.txt` | machine/human PASS/FAIL table and the STOP/GO verdict |
| `host.json`, `host_facts.txt` | host/kernel/OS/uid/cgroup/sysctl/disk/GPU/tool versions, repo tips (`c7` input) |
| `gpu_state_before.txt`, `gpu_state_after.txt` | full `nvidia-smi` before and after the check |
| `gpu_compute_apps_before_all.txt`, `..._after_all.txt` | `--query-compute-apps` (empty: no compute apps) |
| `c1_userns_venv.json`, `c1_userns_syspy.json` | condition 1: the launcher's real `unshare(user\|mnt\|pid\|net\|cgroup)` flags, uid→0 map, PID-1 child, real tmpfs mount, for the `trackp-gpu` venv and `/usr/bin/python3` |
| `c2_ptrace.json` | condition 2: Yama `ptrace_scope=1`, yama in LSM, functional attach/deny probes |
| `c3_cgroup.json`, `c3_cgroup.txt` | condition 3: `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0` facts + the unit's own `RunCgroup` create/kill/remove probe |
| `c4_interp.json`, `c4_interp.txt` | condition 4: non-root euid and the unit's hard `_sandbox_config` `sys.path` check for both interpreters (plus `worker_sandbox_available`) |
| `c5_smoke.json` | condition 5: sandboxed isolated smoke record with `effective:true`, `waivers {}`, `exceptions []` |
| `c6_gpu_smoke.json` | condition 6: GPU smoke under the sandbox (editable `train.py` allocates/synchronises a CUDA tensor in the worker), `effective:true`, `waivers {}`, `exceptions []`, GPU by UUID |
| `c7_final.json`, `c7_final.txt` | condition 7: GPU before/after, no leftovers (processes, cgroups, /tmp), disk, host/kernel, tool versions, repo state, attempt-1 archive/lease untouched |
| `attempt1_{before,after}.*` | read-only pre/post stat + metadata-tree + full-content sha256 fingerprint of the Track P attempt-1 archive (1040 entries, 724 files, 11 925 743 308 bytes) and the two lease logs |
| `attempt1_compare.json`, `attempt1_compare.txt` | pre/post comparison: `identical=True`, `differences=none` |
| `pytest_isolation.json`, `logs/pytest_isolation.log` | supplementary: the unit's own `tests/trackg/test_trackg_isolation.py` in a delegated scope (27 passed, 1 skipped) |
| `gpu_lease_status.txt`, `gpu_compute_apps_pre_gpu_smoke.txt`, `..._post...` | exclusive-GPU lease (flock only, no lease-log write) and the compute-app preflight |
| `records/gpu_smoke/`, `records/g0_smoke/` | copies of the GPU and CPU smoke runs' `run_record.json`, `run.log`, `result_channel.txt` (+ `gpu_report.json` for the GPU run) |
| `scripts/` | every probe, the orchestrator, the summariser; `unit_*.py` are the exact unit files used at `7330338` |
| `SHA256SUMS` | sha256 of every file in this directory except itself |

`/dev/shm` carries 15 pre-existing objects owned by root and `jiachenl` (mtimes 17 and 19 November), not created
by this session; the sandboxed worker's own `/dev/shm` was empty in both smokes.

## Read this first

- **C6 can only see the GPU by UUID.** The runner's `ResourceLimits.gpu_uuids` becomes
  `CUDA_VISIBLE_DEVICES`; with the default empty tuple it exports `CUDA_VISIBLE_DEVICES=""`, which hides every
  GPU from torch. The smoke passes `gpu_uuids=("GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1",)` — the same
  UUID-by-argument path the port smoke uses (`tests/trackg/port_smoke_gpu.py --gpu-uuid`).
- **C3 scope is short-lived.** The delegated `run-*.scope` used by C3/C5/C6 is created per command with
  `systemd-run --user --scope -p Delegate=yes`; the kit smoke and U2 must do the same (or point
  `AR_TEST_CGROUP_PARENT` at a live delegated directory). The session's own `session-*.scope` is not a
  writable cgroup parent.
- **CUDA IPC under the PID namespace remains untested** (`HARNESS_ISOLATION_20261117.md` §5 item 5): C6 proves
  CUDA device allocation/synchronisation inside the sandboxed worker, not parent↔worker CUDA IPC. The AR
  option-A result path uses the CPU `memfd` buffer, not CUDA IPC, so it does not need it.
- No waiver was used anywhere; `timeout factor 3` is the unit default and was not waived.
