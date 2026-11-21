# TASL-7 isolation host check bound to the T1 harness pin c025f89a (21 November 2026)

**Status: PASS for the seven HARNESS_ISOLATION_20261117 §3 host conditions at the T1 pin
`c025f89aeafc2199bf3487b4bcaa16678273c702` (`mac-trackg-t1-tasl-20261121`), with no waiver and no exception —
this is the host-gate record the G.1b/G.4 launch precondition (R1-T1-HOST-TASL, `T1_TASL_PLAN.md` §2) asks for.
ENGINEERING_ONLY; AI-assisted (DeepSeek Harness agent, `tasl7-t1-prep`, delegated by the lead for author-signed
R1-T1-HOST-TASL in the R1-TRACKG-AR-U2-TASL2 context). Subject to independent review of this report and its
captures. Nothing was committed or pushed.**

The seven conditions were re-run on the same host configuration as the reviewed TASL-7 check
(`TASL7_ISOLATION_HOST_CHECK_20261121.md`, sha256
`2b703226e6aec430df24b3333ed002940023c99aa8d535392e117aa4b40f2abf`, review ACCEPTED with report-text conditions
C1–C4) but on the **T1 pin**, with the T1 environments (`torch312`, `jax312` from the census freezes) and the
`jax312` GPU prerequisite. One orchestrated session, `2026-11-21T10:08:38Z`–`10:09:58Z` (80 s), run root
`/home/dowling/r1_tracks/t1_tasl/`.

Machine-read launch lines (each appears once in this report; `g1b_tasl.check_host_record` reads them):

```
host_check_host: TASL-7
host_check_harness_commit: c025f89aeafc2199bf3487b4bcaa16678273c702
host_check_items: 1-7 PASS
host_check_verdict: PASS
```

**Item-7 scope, stated up front (reviewer condition, same as the reviewed report's M1/C1).** Item 7 of §3 is a GPU
smoke with the sandbox on that exercises CUDA IPC across the PID namespace (§5 item 5). This run's C6 is a real
GPU-in-the-sandbox pass — CUDA allocation and synchronisation inside the sandboxed worker (PID 1 of new
user/mount/PID namespaces), `effective: true`, no waiver — but it does **not** exercise CUDA IPC, which remains
**UNTESTED** and §5 item 5 remains **open**. The operating set this record is valid for is AR option A (CPU
`memfd` result channel, `shared_dev_shm: false`, which every G.1b/G.4 T1 node uses). **No node using
`cuda_share`/`cuda_open` may start on the strength of this record.** "1-7 PASS" is the T1 launch-schema value
required by `T1_TASL_PLAN.md` §2 and `g1b_tasl.check_host_record`; read it with that item-7 limit.

## Authority and inputs

- Task authority: author-signed **R1-T1-HOST-TASL** (reaching published `main` at `d47d1008` via
  `author-decisions-20261121`), delegated by the lead; scope = the seven §3 host conditions on TASL-7 at the T1
  pin, no waiver, no proposer/G.4 run in this task, no deletion, no push.
- `T1_TASL_PLAN.md` (`sweep2/t1_tasl/`, sha256
  `fc5606ae75fa486a45af98d1ec848c0ae4ee342d55359024a5184046f0f2867c`) §2 (the `host_check_*` launch
  precondition) and §6 (host tests).
- `docs/r1/reports/HARNESS_ISOLATION_20261117.md` (sha256
  `ac3d5cd0abc262efe8d0552770336ef49dc9cd48cd41704c722ed85c08a5473f`) §3 (the seven host conditions and their
  waivers) and §5 (remaining limits, item 5 CUDA IPC untested). The isolation core is the accepted
  `68cdd1ae2d46d2494ed6fbe69d7dd5693b5c643e` and the accepted Ada host-check fix
  `5403392e94cb59d732f45d6702fc857531ad8fd5`.
- Original TASL-7 check being bound: `docs/r1/reports/trackg_g0_20261117/TASL7_ISOLATION_HOST_CHECK_20261121.md`,
  sha256 `2b703226e6aec430df24b3333ed002940023c99aa8d535392e117aa4b40f2abf` (it ran at fixed tree `7330338`),
  reviewed in `docs/r1/reviews/TASL7_ISOLATION_HOST_CHECK_REVIEW_20261121.md`, sha256
  `18e261cd3641d3ec370599c8f38131862ef8c3e5e1b92659f08c984202fa15d5`.
- Harness worktree (new, this task): `/home/dowling/r1_tracks/t1_tasl/harness`, detached at
  `c025f89aeafc2199bf3487b4bcaa16678273c702`, tree `fa1526f44c79f9c5dcb6b84ed281814045b7add5`, clean, cloned with
  `--branch mac-trackg-t1-tasl-20261121 --single-branch` from
  `https://github.com/dowlingwong/autoresearch_harness.git`. `git merge-base --is-ancestor` verifies the pin
  contains both `68cdd1a` and `5403392e`; its `log` is `c025f89` ← `af48080` ← `6843847` ← `a69c8ef` ← `b574706`
  (the G.1b/G.4 pin). This is the tree every probe below imported.
- Run root: `/home/dowling/r1_tracks/t1_tasl/` (`scripts/`, `captures/`, `records/`, `work/`, `logs/`). The
  session is `bash scripts/run_checks_t1.sh`, whose stdout is `logs/run_checks_t1_final.log`; the capture set and
  its SHA256SUMS are described at the end.
- Not touched, by construction: TASL-2 (no ssh to it in this task), the Track P attempt-1 archive
  `/home/dowling/r1_trackp/runs/p3a_operator_20261027` and its EVIDENCE, both attempt-1 lease-log candidates
  `/home/dowling/r1_locks/trackp_evidence.log` and `/home/dowling/r1_trackp/runs/gpu_lease_log.jsonl`, the paused
  Track P, and HTCondor/deepthought. No file was deleted or moved aside; nothing was committed or pushed.

## The binding: same host, same boot, T1 pin

The original check ran at `2026-11-21T01:59:12Z`–`02:00:19Z`; this one at `10:08:38Z`–`10:09:58Z` **on the same
boot**: `/proc/sys/kernel/random/boot_id` is
`713ca10b-ec21-413c-b61f-30da4a7b1e96` in both. So no host update or reboot sits between the reviewed record and
this binding; what changes is the tree (fixed `7330338` → T1 pin `c025f89a`) and the run environments
(`trackp-gpu` 3.12.15 → the T1 census envs, 3.12.16). Everything the seven conditions test is unchanged on the
host, and the pin is new.

Host (from `c0_assertions.json`, `host.json`, `host_facts.txt`):

- `TASL-7`, uid/euid `1011(dowling)`, gid 1011, non-root, no sudo used. Linux `6.8.0-149-generic #149~22.04.1-Ubuntu
  SMP PREEMPT_DYNAMIC`, Ubuntu 22.04.5 LTS (jammy), 24 CPUs, `MemTotal 65537124 kB` (avail ≈ 63 337 492 kB).
- GPU 0 = NVIDIA GeForce RTX 4090, 24 564 MiB, driver `NVRM 580.178.04` (Tue Jul 7 12:38:21 UTC 2026), UUID
  **`GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`** (full UUID from `nvidia-smi -L`), 44 MiB used, 0 %, **no
  resident compute process** before the session (`c0_assertions.json`, `gpu_compute_apps_before_all.txt`).
- `/sys/fs/cgroup` = `cgroup2 rw,nosuid,nodev,noexec,relatime,nsdelegate,memory_recursiveprot`; user manager
  `running`; PTY/cwd: `/home/dowling`; `/` `/home` `/home/dowling/r1_tracks/t1_tasl` on `/dev/nvme0n1p2`,
  **507.2 GiB free** (544 562 548 736 B) at check time.
- Sysctls: `kernel.yama.ptrace_scope=1`, `kernel.unprivileged_userns_clone=1`,
  `kernel.apparmor_restrict_unprivileged_userns=0`, `user.max_user_namespaces=255164`; LSM
  `lockdown,capability,landlock,yama,apparmor`.
- Environment: **no `LD_LIBRARY_PATH` / `LD_PRELOAD` / `LD_AUDIT`** in the session or in any probe's environment;
  each interpreter's `sys.path` is captured in `c4_interp.json`. The T1 envs are on the uv-managed CPython
  `/home/dowling/.local/share/uv/python/cpython-3.12.16-linux-x86_64-gnu/` (see the T1 precheck report,
  `TASL7_T1_PRECHECK_20261121.md`, for the uv/python/freeze records).

## The seven §3 conditions

| # | Condition (HARNESS_ISOLATION §3) | Result | Key evidence (capture) |
|---|---|---|---|
| 1 | unprivileged user namespaces with mount, PID and network (and cgroup) namespaces usable by the run uid, real tmpfs mount | **PASS** | `probe_userns.py` for `torch312` and `/usr/bin/python3`: single `unshare(CLONE_NEWUSER\|CLONE_NEWNS\|CLONE_NEWPID\|CLONE_NEWNET\|CLONE_NEWCGROUP)` (`0x72020000`) rc 0, uid/gid map 0, real tmpfs mounted and written, child is PID 1 of a new PID namespace (`c1_userns_venv.json`, `c1_userns_syspy.json`) |
| 2 | Yama `ptrace_scope` ≥ 1 | **PASS** | `ptrace_scope=1`, `yama` in the LSM list, parent→child attach ok, same-uid unrelated sibling attach `EPERM` errno 1 (`c2_ptrace.json`) |
| 3 | delegated cgroup v2 subtree the uid can write, with `cgroup.kill`, 8 GiB memory and 0 swap (the census scope) | **PASS** | `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0`: scope `run-rb0b48f7…scope`, `memory.max=8589934592`, `memory.swap.max=0`, `cgroup.kill` exists, `cgroup.procs` writable, owner uid 1011, `nsdelegate true`; the unit's own `isolation.RunCgroup.create → join a live child → cgroup.kill → remove`: `processes_before [226982]`, `kill_method cgroup.kill`, child rc −9, `empty_after true`, `removed true` (`c3_cgroup.json/.txt`) |
| 4 | the run is not root | **PASS** | euid 1011, non-root, groups 1011 only, no sudo (`c4_interp.json`: `euid_check_pass true`) |
| 5 | the run interpreter's `sys.path` holds no home directory, runs tree or ancestor of either (hard `RunnerError`, no waiver) | **PASS** | the unit's own `WorkingCopyRunner._sandbox_config` called for `/usr/bin/python3` (3.10.12), `torch312` (3.12.16) and `jax312` (3.12.16): `broad_entries []`, `sandbox_config_ok true`, `isolation.worker_sandbox_available true` for all three; no hard-check error (`c4_interp.json/.txt`) |
| 6 | a real sandboxed smoke whose record shows `effective: true` | **PASS** | `records/g0_smoke_20261121T100905Z/run_record.json` (copied to `records/g0_smoke/`): `effective true`, `waivers {}`, `exceptions []`, euid 1011, ptrace_scope 1, nsdelegate true, `log_intact true`, `parent_traced_by null`, `parent_dumpable_at_accept false`, `frozen_files_checked 3`, outcome `{kind ok, value 1.0}`, cgroup killed via `cgroup.kill` and removed; result channel `val_accuracy: 1.0000` / `test_accuracy: 0.4242` (`c5_smoke.json`) |
| 7 | GPU smoke with the sandbox on (GPU-in-sandbox prerequisite; CUDA IPC across the PID namespace **not** exercised — §5.5 open, see the scope note above) | **PASS for the AR option-A operating set** | `records/gpu_smoke_20261121T100908Z/run_record.json`: `effective true`, `waivers {}`, `exceptions []`; worker **PID 1**, uid 0 in its own user/mount/PID namespaces (`pid:[4026532927]`, `user:[4026532925]`, `mnt:[4026532926]`), private empty `/dev/shm`; RTX 4090 via `CUDA_VISIBLE_DEVICES=GPU-ab72fb4a-…`; `tensor_sum 4096.0` (expected), 16×16 matmul 16.0, 33 556 992 B allocated, `cuda_initialized true`, no CUDA error text; metric written; 14/14 checks true; cgroup removed (`c6_gpu_smoke.json`) |
| — | end state (not a §3 item; the STOP checks) | **PASS** | GPU identical before/after (44 MiB, 0 %, **no compute apps**, 44 MiB 24 029 MiB free after); no leftover run processes, cgroups or tmp dirs; worktree at the pin and clean; disk 507.2 GiB free; Track P attempt-1 archive and lease logs stat/content identical pre/post (see "Preservation") (`c7_final.json/.txt`) |

Supplementary, not a §3 item: the unit's own `tests/trackg/test_trackg_isolation.py` in a delegated scope:
**27 passed, 1 skipped** (`pytest_isolation.json`; the skip is the root-only unprivileged end-to-end test). The
`timeout_factor` row of §3 is satisfied by the unit default 3.0 and was not waived (`c5_smoke.json` record:
`timeout_seconds 60 (3 × measured 20 s)`).

## How the check ran

One session in `/home/dowling/r1_tracks/t1_tasl`:

```
bash scripts/run_checks_t1.sh     # writes captures/, SUMMARY.json/txt, SHA256SUMS, scripts/
```

`run_checks_t1.sh` exports `XDG_RUNTIME_DIR=/run/user/1011` and
`DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1011/bus` (systemd `--user` over ssh), sets
`PYTHONDONTWRITEBYTECODE=1` (also passed into every `systemd-run --user --scope` with `-E`; the worktree stays
clean), and takes `run_root`/`repo`/`venv` from the T1 layout. Step results (`captures/step_results.txt`):
`envs`, `assertions`, `archive_before`, `host_facts`, C1 (2 interpreters), C2, C3, C4 (3 interpreters), C5, C6,
`c6b_jax_gpu` (as configured — FAIL, see the precheck report's J1a), `c6b_jax_gpu_xla_cuda_dir` (PASS, J1b),
`bind_test` (G.4 precondition, PASS), `pytest_isolation`, `archive_after`, `archive_compare`, `c7_final`,
`summarize` — all rc 0 except the deliberately-recorded J1a. The exact per-condition commands, probes and
orchestrator are in `captures/scripts/` (plus the unit files they import, `unit_isolation.py`,
`unit_runner.py`, `unit_ar_isolated.py`, `unit_isolated_fixture.py`).

Probes are the reviewed TASL-7 ones adapted to the T1 layout (paths, three interpreters, T1 envs), with three
new probes: `probe_envs.py` (uv/Python/freeze binding), `probe_assertions.py` (the machine-checked binding lines)
and `probe_jax_gpu.py` (jax312 GPU, two variants). The GPU and jax probes each take the host's documented
exclusive lease `~/r1_locks/gpu0.lock` with `flock` (no lease-log write), hold it only for their few seconds, and
record the lease status and a before/after fingerprint of the lease file and both lease-log candidates
(`gpu_lease_status.txt`, `jax_gpu_fixed_lease_status.txt`, `*_leaselogs_{before,after,diff}.txt`). A second
non-blocking `flock` from another process returns busy in every case (`second_flock_rc=1`), so the lease is
exclusive, not advisory.

## Preservation and end state

- **Track P attempt-1 archive** `/home/dowling/r1_trackp/runs/p3a_operator_20261027` (with `EVIDENCE`): read-only
  fingerprint before and after the session — **identical**, `differences=none`, 1040 entries, 724 files,
  11 925 743 308 B, metadata tree sha256
  `299237d06012f42b13cff4b476b2167bec55fa2c2463f056567f986ff7e1e003`, content sha256
  `af7ede86da7abbe36ff4ec35ef2029ce4e6233afd5fbe4f49e14684c4d16e965`
  (`attempt1_compare.json/.txt`, `attempt1_{before,after}.*`).
- **Attempt-1 lease-log candidates**: stat identical before/after (size, mtime, ctime, inode):
  `trackp_evidence.log` 76 B inode 56 265 500 sha256
  `2e762c16c255634342f055d8e9647b6491724e3850ee0ce857b1bcece6842793` (mtime 18 Nov 2026);
  `gpu_lease_log.jsonl` 58 863 B inode 56 783 856 sha256
  `e97e03d2a191009b266f3292a24191c5f9b793e8010d870801f5c07405298818` (mtime 17–18 Nov 2026). Neither was
  written by this session; the only lease file touched is `gpu0.lock` itself (see deviations).
- **No leftovers**: zero run-related processes, zero sleep leftovers, zero hostcheck/run cgroups, zero tmp
  `g0_userns_*` dirs; `/dev/shm` holds the same 15 pre-existing objects (owners root/jiachenl, 17–19 Nov) that
  were there before; GPU idle and empty after (`c7_final.json`).
- **No deletion, no move-aside, no commit, no push**; TASL-2, HTCondor/deepthought and the paused Track P were
  not touched.

## Deviations and disclosures

1. **`gpu0.lock` mtime/ctime touched by the first GPU probes.** The first two GPU runs (the C6 smoke and the
   first jax312 run) opened the lock file with `exec 9>…` (O_TRUNC), which refreshes mtime/ctime of the 0-byte
   lock file without changing its content, size or inode (`e3b0c442…`, 0 B, inode 56 251 186 before and after).
   No lease log was written; the scripts were then changed to append-mode open (`exec 9>>…`), and all later runs
   show a byte-identical before/after fingerprint (`lease_logs_unchanged=YES`). The official `g4_tasl.py` opens
   the lease with `a+`, so the launch path does not truncate it. Disclosed because the host-check rule is "no
   write to the lease log", and a reviewer may want the mtime fact.
2. **`jax312` freeze byte order.** The installed `jax312` environment's `uv pip freeze` is the same 68-line
   multiset as the census freeze (`freeze_sorted_equal true`; the G.1b job's own `g1b_lib.compare_freeze` is a
   sorted comparison) but not byte-identical: `uv 0.13.6` orders `opt-einsum` before `optax`, the census file has
   `optax` first. The set and versions are identical; this is a sort-order difference only, disclosed in
   `c0_envs.json` (`freeze_byte_diff`) and in the precheck report.
3. **`captures/scripts/run_checks_t1.sh`** is the post-run copy with one ordering fix (SHA256SUMS is now the last
   write under `captures/`; the digest goes to stdout instead of into a captured log). The executed version was
   identical except for those two lines; the mismatch it caused in the first bundle draft was fixed by
   re-computing `SHA256SUMS` as the last write.
4. The two probes that failed *as configured* on this host (`c6b_jax_gpu`, J1a) are kept in the bundle as
   evidence and are not part of the seven §3 items; the jax312 GPU prerequisite passes with the documented
   `--xla_gpu_cuda_data_dir=/usr/local/cuda-12.2` host adaptation (`c6b_jax_gpu_xla_cuda_dir.json`). That
   adaptation, and its consequence for the G.1b `mlgym_breakout_minatar` node, is written up in
   `TASL7_T1_PRECHECK_20261121.md` as a launch precondition needing the author's environment row.

## Captures

Sibling bundle `TASL7_T1_PRECHECK_20261121_captures/` (this T1 precheck's single capture bundle; the binding is
part of the same session): **170 files, 1.7 MiB**, `SHA256SUMS` sha256
**`19c4f6574782ace3ac24a6ff2754fd77858b07000cd169d3fdf05eccd11d3e8a`**, covering 170 files. Verified on TASL-7
and locally with `sha256sum -c SHA256SUMS` (170/170 OK). The bundle holds `SUMMARY.json/.txt`,
`step_results.txt`, every probe JSON/text, the copied unit run records (`records/g0_smoke/`,
`records/gpu_smoke/`), the lease/lease-log fingerprints, the proposer captures (`proposer/`), the bind test
(`bind_test/`) and the exact scripts (`scripts/`). Host run root:
`/home/dowling/r1_tracks/t1_tasl/` (captures also live there under `captures/`).

## Verification for the reviewer

```
# on the Mac ops worktree (this report's directory)
shasum -a 256 -c TASL7_T1_PRECHECK_20261121_captures/SHA256SUMS      # 170/170 OK
# on TASL-7 (read-only)
git -C /home/dowling/r1_tracks/t1_tasl/harness rev-parse HEAD         # c025f89a…
git -C /home/dowling/r1_tracks/t1_tasl/harness status --porcelain      # empty
nvidia-smi -L                                                         # GPU-ab72fb4a-…
cat /home/dowling/r1_tracks/t1_tasl/captures/SUMMARY.txt
```

Limits for the operator: this record is for TASL-7 only and for the AR option-A operating set; it does not
cover CUDA IPC (§5.5), a node with `shared_dev_shm: true`, or any TASL-2 condition. The G.1b/G.4 launch still
needs the precheck's two open preconditions resolved (jax312 XLA flag on TASL-7; the G.4 `server_url` client
address `.50`) and both keys, and TASL-2's own binding report on published `main`.
