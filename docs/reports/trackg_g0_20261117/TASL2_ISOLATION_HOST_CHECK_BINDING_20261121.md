# TASL-2 harness-isolation host-check binding at harness pin c025f89a (21 November 2026)

**Status: PASS — binding record for `R1-T1-HOST-TASL` / `sweep2/t1_tasl/T1_TASL_PLAN.md` §2.** ENGINEERING_ONLY;
AI-assisted (DeepSeek Harness agent `tasl2-t1-prep`, delegated by the lead). This file is the launch record the G.1b
spec names at `hosts.TASL-2.isolation_host_check.record`; the lead commits it to published `main` and fills its
sha256 into the spec (written uncommitted on the Mac ops worktree `main_t1_host_reports_20261121`, baseline
`d47d1008`; no push).

host_check_host: TASL-2
host_check_harness_commit: c025f89aeafc2199bf3487b4bcaa16678273c702
host_check_items: 1-7 PASS
host_check_verdict: PASS

## What this binds

The seven host conditions of `docs/r1/reports/HARNESS_ISOLATION_20261117.md` §3 were re-checked **at the G.1b launch
pin** on TASL-2 in one orchestrated session (2026-11-21T10:04:16Z–10:05:42Z UTC; unprivileged host uid 1008,
no sudo) and all seven passed, with no waiver. The same session also covers the in-scope `T1_TASL_PLAN.md` §6
pre-launch items (delegated 8G/swap-0 scope, GPU UUID/no resident compute process, ptrace_scope, non-root, harness
pin clean, census env freezes at Python 3.12.16, CPU-only HousePrice affinity plus CPU/GPU coexistence, jax312 GPU);
the full record with commands, results and captures is the sibling report
[`TASL2_T1_PRECHECK_20261121.md`](TASL2_T1_PRECHECK_20261121.md) and its `_captures/` directory.

- Host: `TASL-2` (zhixu portal), Ubuntu 22.04.5 LTS, kernel `6.8.0-149-generic`, cgroup v2
  (`nsdelegate,memory_recursiveprot`), NVIDIA driver `535.309.01`.
- Harness worktree: `/home/dowling/r1_tracks/t1_tasl/harness`, detached at
  `c025f89aeafc2199bf3487b4bcaa16678273c702` (`origin/mac-trackg-t1-tasl-20261121`), `git status --porcelain`
  empty before and after; no stash, no commit.
- GPU: `GPU 0: NVIDIA GeForce RTX 4090 (UUID: GPU-4d623e76-7587-ee15-a633-46f60d220d94)`,
  `nvidia-smi --query-compute-apps` empty before and after (no resident compute process; 353 MiB desktop
  reservation is pre-existing, utilisation 0 %).
- Run root on TASL-2: `/home/dowling/r1_engineering/tasl2_t1_precheck_20261121/` (`scripts/`, `captures/`,
  `logs/`, `records/`, `env_build/`, `work/`).

## Original host-check report (unchanged, still the first §3 evidence)

- `docs/r1/reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_20261121.md` (21 Nov 2026, checked by agent
  `tasl2-hostchecker` on the fixed tree `7330338` = accepted core `68cdd1a` + accepted Ada fix `5403392e`),
  sha256 `83636c039fcb7d503abb15468cf4588ebd6795588012b44f6d8f79470d7a5bb6`; its captures' `SHA256SUMS`
  sha256 `0d0b590be35577409e75ec35a9ffb3f7a33d0e3c025eaba1eda4c606d4353f09` (60 files, 480 KiB).
- That report's tree is a different commit from the G.1b launch pin. This binding is the same seven conditions
  **at the pin**; it does not replace or re-hash the original report, whose sha256 above is the file still on
  `main` at `aaf2254a`.

## §3 conditions at the pin — PASS table

| # | Condition (`HARNESS_ISOLATION_20261117.md` §3) | Result | Key evidence (captures in `TASL2_T1_PRECHECK_20261121_captures/`) |
|---|---|---|---|
| C1 | unprivileged user+mount+PID+network(+cgroup) namespaces usable by the run uid | **PASS** | `unshare(CLONE_NEWUSER\|CLONE_NEWNS\|CLONE_NEWPID\|CLONE_NEWNET\|CLONE_NEWCGROUP)` rc 0 for the torch312 interpreter (3.12.16) and `/usr/bin/python3`; uid 1008→0 map; real tmpfs mount rc 0 and writable; child is PID 1 of the new PID namespace (`c1_userns_venv.json`, `c1_userns_syspy.json`) |
| C2 | Yama `ptrace_scope` ≥ 1 | **PASS** | `kernel.yama.ptrace_scope=1`, `yama` in LSM `lockdown,capability,landlock,yama,apparmor`; parent→child attach ok, unrelated same-uid sibling attach `EPERM` (`c2_ptrace.json`) |
| C3 | delegated cgroup v2 subtree the uid can write, with `cgroup.kill` (census scope 8G / swap 0) | **PASS** | `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0`: `memory.max=8589934592`, `memory.swap.max=0`, `cgroup.kill` exists, `nsdelegate=True`, owner uid 1008; the unit's own `isolation.RunCgroup` create→join pid→`cgroup.kill`→empty→removed (`c3_cgroup.json`/`.txt`) |
| C4 | the run is not root; the run interpreter's `sys.path` holds no home dir, runs tree or ancestor (hard `RunnerError`, no waiver) | **PASS** | host euid 1008; the unit's `WorkingCopyRunner._sandbox_config` passes for `/usr/bin/python3`, `envs/torch312` and `envs/jax312` (both Python 3.12.16): `broad_entries=[]`, `sandbox_config_ok=True`, `isolation.worker_sandbox_available=True` for all three (`c4_interp.json`/`.txt`) |
| C5 | a real sandboxed smoke whose record shows `effective: true` | **PASS** | record `effective: true`, `waivers {}`, `exceptions []`, euid 1008, `ptrace_scope 1`, `nsdelegate true`, `log_intact true`, `parent_traced_by null`, `parent_dumpable_at_accept false`, cgroup removed; outcome ok 1.0 (`c5_smoke.json`; `records/g0_smoke/`) |
| C6 | GPU smoke with the sandbox on (GPU-in-sandbox prerequisite; not §3 item 7 CUDA IPC) | **PASS** | GPU by full UUID `GPU-4d623e76-…`; `effective:true`, `waivers {}`, `exceptions []`; worker PID 1 in new user/mount/PID namespaces allocated+synchronised a CUDA tensor (`tensor_sum 4096.0`, matmul 16.0, 33.6 MB allocated, `cuda_available true`), no CUDA error; metric written; cgroup removed (`c6_gpu_smoke.json`; `records/gpu_smoke/`) |
| C7 | end state: GPU before/after, no leftovers, disk, host/kernel, tool versions | **PASS** | GPU identical before/after (353 MiB, no compute apps, 0 %); all six leftover buckets empty; 354.6 GiB free; harness still clean at `c025f89`; attempt-1 archive and Track P lease log untouched (read-only stat, mtimes 2026-11-17); cgroups/tmp dirs/`/dev/shm` clean (`c7_final.json`/`.txt`) |

Supplementary, not a §3 host condition: the pin's own `tests/trackg/test_trackg_isolation.py` in a delegated scope:
**27 passed, 1 skipped** in 15.30 s (`pytest_isolation.json`, `logs/pytest_isolation.log`; the skip is the root-only
`test_unprivileged_end_to_end`). The `timeout factor 3` row of §3 is satisfied by the unit default and was not
waived (`ResourceLimits.timeout_factor = 3.0` in both smoke records).

## Capture evidence on TASL-2

- Run root: `/home/dowling/r1_engineering/tasl2_t1_precheck_20261121/`; orchestration
  `bash scripts/run_checks.sh` (verbatim in `captures/scripts/run_checks.sh`, per-step stdout/stderr in
  `captures/logs/`, summary in `captures/SUMMARY.{json,txt}`).
- Capture set: **91 files**, `SHA256SUMS` sha256
  `e604aff7f40815e6d17d415296534b773cf781820125a07cd1e98240ae985eaf`; `sha256sum -c SHA256SUMS` rc 0 on TASL-2
  and after fetch (the digest file itself is kept outside the capture set as
  `/home/dowling/r1_engineering/tasl2_t1_precheck_20261121/SHA256SUMS.sha256`).
- Fetched copy in this repo (uncommitted): `TASL2_T1_PRECHECK_20261121_captures/` (same `SHA256SUMS`, verified).

## Scope and non-authorities

Only TASL-2 was used (`ssh -o BatchMode=yes portal_zhixu`); TASL-7 was not contacted. The synthetic loads held the
documented exclusive lease `~/r1_locks/gpu0.lock` with `flock` only for the seconds of the GPU/jax/coexistence
probes (the lease log was not written). No pre-existing host work was deleted or moved aside, nothing was
committed or pushed, and the Track P attempt-1 archive `/home/dowling/r1_trackp/runs/p3a_operator_20261027` and
its lease log `runs/_attempt1_gpu_lease_log.jsonl` were only `stat`-ed (mtimes `2026-11-17 15:42:26` and
`2026-11-17 15:42:35`). HTCondor and deepthought were not touched. This is host evidence, not a launch
authorization: the author's signed note and both keys are still required.

**AI-assisted: DeepSeek Harness agent (`tasl2-t1-prep`), 21 Nov 2026. ENGINEERING_ONLY; uncommitted.**
