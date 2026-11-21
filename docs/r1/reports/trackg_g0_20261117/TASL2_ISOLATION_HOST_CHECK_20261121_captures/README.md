# TASL-2 isolation host-check captures — 21 November 2026

R1-TRACKG-AR-U2-TASL2, TASL-2 host check of `docs/r1/reports/HARNESS_ISOLATION_20261117.md` §3 (host conditions)
plus a real sandboxed GPU smoke. ENGINEERING_ONLY; independent review required before any autorsearch kit / U2 use.

- Host: TASL-2 (`ssh portal_zhixu`), uid 1008 `dowling` (non-root), Linux 6.8.0-149-generic,
  RTX 4090 24 GB, driver 535.309.01.
- Harness worktree: `/home/dowling/r1_trackp/harness_cond7a_20261121` @ `7330338` (detached, clean),
  which contains the accepted isolation core `68cdd1a` and the accepted Ada host-check fix `5403392e`.
- Run root: `/home/dowling/r1_engineering/tasl2_hostcheck_20261121/` (new; nothing deleted or moved aside;
  no push, no commit; TASL-7 / attempt-1 archive / HTCondor untouched).
- Session: `2026-11-21T01:34:17Z` (one orchestrated `scripts/run_checks.sh` run; `logs/run_checks.log`).

## Files

| Path | What it is |
|---|---|
| `SUMMARY.json`, `SUMMARY.txt` | machine/human PASS/FAIL table and the STOP/GO verdict |
| `host.json`, `host_facts.txt` | host/kernel/OS/uid/cgroup/sysctl/disk/GPU/tool versions, repo tips (`c7` input) |
| `gpu_state_before.txt`, `gpu_state_after.txt` | full `nvidia-smi` before and after the check |
| `gpu_compute_apps_before_all.txt`, `..._after_all.txt` | `--query-compute-apps` (must be empty) |
| `c1_userns_venv.json`, `c1_userns_syspy.json` | condition 1: the launcher's real `unshare(user\|mnt\|pid\|net\|cgroup)` flags, uid→0 map, PID-1 child, real tmpfs mount, for the `trackp-gpu` venv and `/usr/bin/python3` |
| `c2_ptrace.json` | condition 2: Yama `ptrace_scope=1`, yama in LSM, functional attach/deny probes |
| `c3_cgroup.json`, `c3_cgroup.txt` | condition 3: `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0` facts + the unit's own `RunCgroup` create/kill/remove probe |
| `c4_interp.json`, `c4_interp.txt` | condition 4: non-root euid and the unit's hard `_sandbox_config` `sys.path` check for both interpreters (plus `worker_sandbox_available`) |
| `c5_smoke.json` | condition 5: sandboxed isolated smoke record with `effective:true`, `waivers {}`, `exceptions []` |
| `c6_gpu_smoke.json` | condition 6: GPU smoke under the sandbox (editable `train.py` allocates/synchronises a CUDA tensor in the worker), `effective:true`, `waivers {}`, `exceptions []`, GPU by UUID |
| `c7_final.json`, `c7_final.txt` | condition 7: GPU before/after, no leftovers (processes, cgroups, /tmp, /dev/shm), disk, host/kernel, tool versions, repo state |
| `pytest_isolation.json`, `logs/pytest_isolation.log` | supplementary: the unit's own `tests/trackg/test_trackg_isolation.py` in a delegated scope (27 passed, 1 skipped) |
| `gpu_lease_status.txt`, `gpu_compute_apps_pre_gpu_smoke.txt`, `..._post...` | exclusive-GPU lease (flock only, no lease-log write) and the compute-app preflight |
| `records/gpu_smoke/` | copies of the GPU run's `run_record.json`, `run.log`, `result_channel.txt`, `gpu_report.json` |
| `scripts/` | every probe, the orchestrator, the summariser, and the two unmodified Ada originals (`ada_originals/`); `unit_*.py` are the exact unit files used |
| `SHA256SUMS` | sha256 of every file in this directory except itself |

## Read this first

- **C6 can only see the GPU by UUID.** The runner's `ResourceLimits.gpu_uuids` becomes
  `CUDA_VISIBLE_DEVICES`; with the default empty tuple it exports `CUDA_VISIBLE_DEVICES=""`, which hides every
  GPU from torch. The accepted probe therefore passes
  `gpu_uuids=("GPU-4d623e76-7587-ee15-a633-46f60d220d94",)` — the same UUID-by-argument path the port smoke uses
  (`tests/trackg/port_smoke_gpu.py --gpu-uuid`). The first attempt without it is recorded in
  `c6_gpu_smoke.json` diagnostics history only in this bundle's `SUMMARY` prose, not as a host failure.
- **C3 scope is short-lived.** The delegated `run-*.scope` used by C3/C5/C6 is created per command with
  `systemd-run --user --scope -p Delegate=yes`; the kit smoke and U2 must do the same (or point
  `AR_TEST_CGROUP_PARENT` at a live delegated directory). The session's own `session-*.scope` is not a
  writable cgroup parent.
- No waiver was used anywhere; `timeout factor 3` is the unit default and was not waived.
