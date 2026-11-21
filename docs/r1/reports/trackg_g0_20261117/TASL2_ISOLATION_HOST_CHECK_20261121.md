# TASL-2 host isolation check for R1-HARNESS-ISOLATION §3 (21 November 2026)

**Status: host-gate PASS for the seven listed preconditions (GO for the autoresearch kit smoke / U2 setup on TASL-2); the gate binds fixed tree 7330338 (contains 68cdd1a + 5403392e; bare 68cdd1a lacks the fixes).**
subject to independent review of this report and its captures.** ENGINEERING_ONLY; AI-assisted
(DeepSeek Harness agent, `tasl2-hostchecker`, delegated by the lead for author-signed R1-TRACKG-AR-U2-TASL2).

The seven conditions of `docs/r1/reports/HARNESS_ISOLATION_20261117.md` §3 were checked in one orchestrated
session on TASL-2 (01:33:55Z–01:34:17Z) with **no waiver**: unprivileged user+mount+PID+network(+cgroup)
namespaces with a real tmpfs mount, Yama `ptrace_scope`, a delegated cgroup v2 subtree with `cgroup.kill`, the
non-root + interpreter `sys.path` hard check, a real sandboxed smoke with `effective: true`, a GPU smoke with the
sandbox on (`effective: true`, `waivers {}`, `exceptions []`, no CUDA error), and a clean end state with no
leftovers. The unit's own isolation test file also passes in a delegated scope (27 passed, 1 root-only skip).

Nothing was set up or run from the autoresearch kit, no U2/T1 run was started, nothing was committed or pushed,
no pre-existing host work was deleted or moved aside, and TASL-7, the Track P attempt-1 archive and
HTCondor/deepthought were not touched. (Only the operator's own preliminary capture directory, created in this
session, was rotated aside inside the new run root.) The Track P `~/r1_locks/gpu0.lock` was taken with `flock` for the two seconds of the GPU smoke only; the
lease log was not written.

## Authority and inputs

- Task authority: author-signed **R1-TRACKG-AR-U2-TASL2** (not in committed PLAN at this review time; reaches main after the sweep-2 launch), delegated by the lead; scope = HARNESS_ISOLATION §3
  host checks on TASL-2 only, STOP if any condition fails, do not set up/run the autoresearch kit/U2.
- `docs/r1/reports/HARNESS_ISOLATION_20261117.md` §3 (host conditions and waivers), §5 (remaining limits,
  including item 5 "CUDA IPC under the PID namespace is untested"); `docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md`
  (the port kit's GPU-smoke condition).
- Ada precedent: `docs/r1/reports/trackg_g0_20261117/HARNESS_ISOLATION_HOST_CHECK_20261119.md` and its
  `_captures/scripts/probe_userns.py`, `probe_smoke.py` (Mac ops worktree `ops-tasl-20261116`). The two Ada
  originals are preserved unmodified in the captures under `scripts/ada_originals/`; all other probes are
  adaptations to the TASL-2 worktree, run root and interpreters.
- TASL-2 harness **worktree** `/home/dowling/r1_trackp/harness_cond7a_20261121` @
  `73303380197477df971e865440d0ae11135fe1b3` (detached, clean; `remotes/origin/mac-trackg-iso-ar-cond7a-20261120`).
  `git merge-base --is-ancestor` verifies this tree contains **both** the accepted isolation core
  `68cdd1ae2d46d2494ed6fbe69d7dd5693b5c643e` **and** the accepted Ada host-check fix
  `5403392e` ("keep locked bind mount flags; bind the interpreter symlink chain", merged by `2e65922`). This
  matters for review: the Ada §3 STOP was partly defects A (bind-remount flags) and B (uv venv symlink chain),
  fixed in `5403392e`; this check is on a tree that contains the fix.
- Base repo `/home/dowling/r1_trackp/autoresearch_harness` @ `897d83c8efa364ec2fdd37288241cc42e01d7274`
  (branch `trackp-20261026`, clean) — the git main repo of the worktree; it does not itself carry
  `src/autoresearch/trackg` on that branch, so the worktree is the code tree used.
- `trackp-gpu` venv `/home/dowling/r1_trackp/venvs/trackp-gpu/bin/python`: Python 3.12.15 (uv 0.13.5), torch
  2.6.0+cu124 (CUDA 12.4, `cuda.is_available()=True`), numpy 2.4.4, pytest 9.0.3. System `/usr/bin/python3` is
  3.10.12. `pyvenv.cfg` `home = /home/dowling/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu/bin` (inside
  `$HOME`); see C4 — this does **not** trip the unit's hard check.
- Run root (new): `/home/dowling/r1_engineering/tasl2_hostcheck_20261121/` with `scripts/`, `captures/`,
  `records/`, `work/`. Raw captures were fetched to this report's sibling
  `TASL2_ISOLATION_HOST_CHECK_20261121_captures/` (60 files, 480 KiB; `SHA256SUMS` covers 59 files,
  `sha256 = 0d0b590be35577409e75ec35a9ffb3f7a33d0e3c025eaba1eda4c606d4353f09`, verified locally with
  `shasum -a 256 -c SHA256SUMS`).
- Non-authorities deliberately not touched: TASL-7, Track P attempt-1 archive
  `/home/dowling/r1_trackp/runs/p3a_operator_20261027` (stat before/after: mtime `2026-11-17 15:42:26 -0800`,
  size 4096 dir, unchanged), the live Track P lease log, HTCondor/deepthought, Paper A (TASL-2 has no Paper A
  meaning; only the GPU is shared).

## Host

`TASL-2` (zhixu portal), Linux `6.8.0-149-generic #149~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Wed Oct 28 20:58:45
UTC 2026 x86_64`, Ubuntu 22.04.5 LTS, boot id `86c613a9-b90c-48be-9bd5-a0f99c940dae`; uid/euid `1008(dowling)`,
gid 1008, groups `1008` only, non-root, no sudo used; 32 CPUs; `MemTotal 65 543 252 kB`; `/` (and `/home`) on
`/dev/nvme0n1p2`, **368.7 GiB free** at check time; GPU 0 = NVIDIA GeForce RTX 4090 24 564 MiB, driver
`535.309.01`, UUID `GPU-4d623e76-7587-ee15-a633-46f60d220d94`, 353 MiB used by the desktop (no compute apps),
0 % utilisation; `/sys/fs/cgroup` = `cgroup2 rw,nosuid,nodev,noexec,relatime,nsdelegate,memory_recursiveprot`.
All commands over `ssh -o BatchMode=yes portal_zhixu`; report times UTC (TASL-2's local clock is PST, UTC−8).

Tool versions: bash 5.1.16; systemd 249 (249.11-0ubuntu3.23), user manager `running`; `systemd-run`,
`systemctl --user`, `flock`/`unshare` (util-linux 2.37.2) present; `/usr/bin/python3` 3.10.12; `trackp-gpu`
3.12.15 / torch 2.6.0+cu124 / numpy 2.4.4 / pytest 9.0.3.

## §3 conditions

| # | Condition (HARNESS_ISOLATION §3) | Result | Key evidence (capture) |
|---|---|---|---|
| C1 | unprivileged user namespaces with mount, PID and network (and cgroup) namespaces usable by the run uid | **PASS** | `unshare(CLONE_NEWUSER\|CLONE_NEWNS\|CLONE_NEWPID\|CLONE_NEWNET\|CLONE_NEWCGROUP)` rc 0 for both interpreters; uid 1008→0 map; child is PID 1 of a new PID namespace; real tmpfs mount rc 0 + write ok (`c1_userns_venv.json`, `c1_userns_syspy.json`) |
| C2 | Yama `ptrace_scope` ≥ 1 | **PASS** | `kernel.yama.ptrace_scope=1`, `yama` in `lockdown,capability,landlock,yama,apparmor`; parent→child attach ok, unrelated same-uid sibling attach `EPERM` (`c2_ptrace.json`) |
| C3 | delegated cgroup v2 subtree the uid can write, with `cgroup.kill` | **PASS** | scope `run-ra8dc…scope`; `memory.max=8589934592`; `memory.swap.max=0`; `cgroup.kill` exists; `cgroup.procs` writable; owner uid 1008; `nsdelegate` true; unit `RunCgroup` create→join pid→`cgroup.kill`→`empty_after:true` (child rc −9)→remove (`c3_cgroup.json/.txt`) |
| C4 | the run is not root; the run interpreter's `sys.path` holds no home dir, runs tree or ancestor (hard `RunnerError`, no waiver) | **PASS** | euid 1008; unit `WorkingCopyRunner._sandbox_config` passes for `/usr/bin/python3` **and** `trackp-gpu` venv; `broad_entries=[]`; `worker_sandbox_available=True` for both; no venv-home failure (`c4_interp.json/.txt`) |
| C5 | a real sandboxed smoke whose record shows `effective: true` | **PASS** | record: `effective:true`, `waivers {}`, `exceptions []`, `euid 1008`, `ptrace_scope 1`, `nsdelegate true`, `log_intact true`, `parent_traced_by null`, `parent_dumpable_at_accept false`, cgroup removed; outcome `ok` 1.0 (`c5_smoke.json`, `records/g0_smoke/`; the g0 record directory is now included in the captures) |
| C6 | GPU smoke with the sandbox on (GPU-in-sandbox prerequisite; not §3 item 7 CUDA IPC) | **PASS** | GPU by UUID (`CUDA_VISIBLE_DEVICES=GPU-4d623e76-…`); `effective:true`, `waivers {}`, `exceptions []`; worker PID 1 in new user/mount/PID namespaces allocated+synchronised a CUDA tensor: `tensor_sum 4096.0` (expected), matmul ok, 33.6 MB allocated, `cuda_available true`, no CUDA error; metric written; cgroup removed (`c6_gpu_smoke.json`, `records/gpu_smoke/`) |
| C7 | end state: GPU before/after, no leftovers, disk, host/kernel, tool versions | **PASS** | GPU identical before/after (353 MiB, no compute apps, 0 %); no leftover processes/cgroups/tmp dirs/`/dev/shm`; 368.7 GiB free; repo `7330338` clean; attempt-1 archive untouched (`c7_final.json/.txt`) |

Supplementary, not a §3 host condition: the unit's own `tests/trackg/test_trackg_isolation.py` in a delegated
scope: **27 passed, 1 skipped in 15.83 s** (`pytest_isolation.json`, `logs/pytest_isolation.log`). The skip is
the root-only `test_unprivileged_end_to_end` (`@pytest.mark.skipif(not ROOT, reason="needs root to drop to uid
65534 and delegate a cgroup")`). The `timeout factor 3` row of §3 is satisfied by the unit default and was not
waived (`ResourceLimits.timeout_factor = 3.0` in both smoke records).

## How the check ran

One orchestrated session from `/home/dowling/r1_engineering/tasl2_hostcheck_20261121`:

```
bash scripts/run_checks.sh        # writes captures/, SUMMARY.json/txt, SHA256SUMS
```

`run_checks.sh` exports `XDG_RUNTIME_DIR=/run/user/1008` and `DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1008/bus`
(needed for `systemd-run --user` over ssh), sets `PYTHONDONTWRITEBYTECODE=1` so the harness worktree stays
clean, and captures each step's stdout in `captures/logs/`. The exact per-condition commands and raw results
follow; every command is reproduced verbatim in `captures/scripts/run_checks.sh` and the individual probes.

### C1 — unprivileged user+mount+PID+network(+cgroup) namespaces

```
$VENV scripts/probe_userns.py --out captures/c1_userns_venv.json      # 3.12.15
/usr/bin/python3 scripts/probe_userns.py --out captures/c1_userns_syspy.json  # 3.10.12
```

The probe mirrors the launcher (`ar_isolated`) rather than the `unshare(1)` CLI: it calls
`prctl(PR_SET_DUMPABLE)`, then one `unshare()` with
`CLONE_NEWUSER|CLONE_NEWNS|CLONE_NEWPID|CLONE_NEWNET|CLONE_NEWCGROUP` (`flags 0x72020000`), writes
`setgroups=deny`, `uid_map 0 <uid> 1`, `gid_map 0 <gid> 1`, records every `/proc/self/ns/*` inode, mounts a
real `tmpfs` (mounted uid/gid 1008) and writes a file into it, then forks a child that is **PID 1** of the
new PID namespace.

Result (identical shape for both interpreters): `unshare_rc 0`, `unshare_errno 0`, `mapped_uid_in_new_userns 0`,
`mapped_gid_in_new_userns 0`, `tmpfs_mount_rc 0`, `tmpfs_mounted true`, `tmpfs_writable "userns mount ok"`,
`pid_namespace_child {pid: 1, ppid: 0, uid: 0, new_pid_namespace: true}`. Example: caller `user:[4026531837]`
→ child `user:[4026533002]`, `mnt:[4026531841]→mnt:[4026533143]`, `net:[4026531840]→net:[4026533146]`,
`cgroup:[4026531835]→cgroup:[4026533145]`, child pid ns `pid:[4026533144]`. The `userns_only` control (a user
namespace with no mapping, so no mount capability) is recorded alongside and is expected to be non-mounting;
the mapped probes above are the condition.

Host support: `kernel.unprivileged_userns_clone=1`, `user.max_user_namespaces=254738`,
`kernel.apparmor_restrict_unprivileged_userns=0` (the Ubuntu AppArmor userns restriction is off), LSM includes `apparmor`.

### C2 — Yama `ptrace_scope` ≥ 1

```
$VENV scripts/probe_ptrace.py --out captures/c2_ptrace.json
```

`ptrace_scope_raw "1"`, `ptrace_scope 1`, `lsm "lockdown,capability,landlock,yama,apparmor"`,
`yama_in_lsm true`. Functional probes: `parent_attach_child {ok: true, why: ok}`,
`parent_detach_child {ok: true}`, `unrelated_sibling_attach {ok: false, errno: 1, why: "Operation not permitted"}`
— i.e. same-uid but non-ancestor tracing is denied by Yama, while the parent still has ptrace. All helper
processes are SIGKILLed and reaped before exit.

### C3 — delegated cgroup v2 subtree with `cgroup.kill`

```
systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- \
  $VENV scripts/probe_cgroup.py --repo $REPO --out captures/c3_cgroup.json --text captures/c3_cgroup.txt
```

`c3_cgroup.txt` (verbatim, values):

```
scope=/sys/fs/cgroup/user.slice/user-1008.slice/user@1008.service/app.slice/run-ra8dc2a89e2ab46578e10580914a66817.scope
memory.max=8589934592
memory.swap.max=0
cgroup.kill_exists=True
cgroup.procs_writable=True
owner_uid=1008 euid=1008
nsdelegate=True
mountinfo=['34 25 0:29 / /sys/fs/cgroup rw,nosuid,nodev,noexec,relatime shared:9 - cgroup2 cgroup2 rw,nsdelegate,memory_recursiveprot']
runcgroup={"path": ".../run-ra8dc...scope/ar_hostcheck_1907935_1907935_575940959", "migration_possible": true,
 "processes_before": [1907936], "populated_before": true,
 "kill": {"method": "cgroup.kill", "processes_before": 1, "empty_after": true},
 "child_returncode": -9, "populated_after": false, "kill_method": "cgroup.kill", "empty_after": true, "removed": true}
checks={"cgroup_kill_exists": true, "kill_method_cgroup_kill": true, "memory_max_8g": true,
        "memory_swap_max_0": true, "nsdelegate": true, "owner_is_caller": true,
        "procs_writable": true, "runcgroup_kill": true, "scope_unit": true}
```

The `RunCgroup` create/move/kill/remove probe is the unit's own code (`isolation.RunCgroup`), not a shell
imitation; the run cgroup was removed. Note the cgroup parent is a **short-lived** `systemd-run --user --scope`
created per command with `Delegate=yes`; the session's own `session-*.scope` is not writable as a parent. The
kit smoke and U2 must likewise use a delegated scope (or point `AR_TEST_CGROUP_PARENT` at a live delegated
directory).

### C4 — non-root euid and the interpreter `sys.path` hard check

```
$VENV scripts/probe_interp.py --repo $REPO --base $BASE \
  --out captures/c4_interp.json --text captures/c4_interp.txt
```

The probe calls the unit's own `WorkingCopyRunner._sandbox_config` for both interpreters (the hard `RunnerError`
path, no waiver) and then the unit's own `isolation.worker_sandbox_available`. `c4_interp.txt`:

```
euid=1008 non_root=True
--- system_py3: /usr/bin/python3
  version=3.10.12 executable=/usr/bin/python3
  sys_path=['/usr/lib/python310.zip', '/usr/lib/python3.10', '/usr/lib/python3.10/lib-dynload',
            '/usr/local/lib/python3.10/dist-packages', '/usr/lib/python3/dist-packages']
  broad_entries=[]   sandbox_config_ok=True sandbox_available=True
--- venv_trackp_gpu: /home/dowling/r1_trackp/venvs/trackp-gpu/bin/python
  version=3.12.15 executable=/home/dowling/r1_trackp/venvs/trackp-gpu/bin/python
  sys_path=['/home/dowling/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu/lib/python312.zip',
            '/home/dowling/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu/lib/python3.12',
            '/home/dowling/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu/lib/python3.12/lib-dynload',
            '/home/dowling/r1_trackp/venvs/trackp-gpu/lib/python3.12/site-packages']
  broad_entries=[]   sandbox_config_ok=True sandbox_available=True
condition_4_pass=True venv_check_pass=True
```

**The venv's home path did not fail the check** and no waiver was needed: the uv base prefix and the venv live
*under* `$HOME` (`/home/dowling/...`), which the unit binds read-only into the worker by design; the hard rule
rejects the home directory itself, the runs tree, or an **ancestor** of either (`broad_entries=[]`). The uv
alias directory `/home/dowling/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu` in `sys.path` is exactly
the path that broke the Ada check (Ada defect B); on this tree the accepted fix `5403392e` binds the whole
symlink chain and the sandbox works for both interpreters.

### C5 — real sandboxed smoke, `effective: true`

```
systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c \
  'CG=$(cut -d: -f3 /proc/self/cgroup); export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG; \
   exec $VENV scripts/probe_smoke.py --repo $REPO --base $BASE \
     --out captures/c5_smoke.json --tag g0_smoke --interpreter $VENV'
```

The probe is the Ada G0 `probe_smoke.py` adapted to this worktree/base: it uses the unit's own
`tests/trackg/isolated_fixture` node and `WorkingCopyRunner`, no waivers. Record
(`records/g0_smoke_20261121T013357Z/run_record.json`, copied to `captures/records/g0_smoke/`):

```
effective: true        waivers: {}        exceptions: []
euid: 1008             ptrace_scope: 1    nsdelegate: true
log_intact: true       frozen_files_checked: 3
parent_traced_by: null parent_dumpable_at_accept: false
outcome: {kind: ok, value: 1.0}
isolation.cgroup.kill: {method: cgroup.kill, processes_before: 0, empty_after: true, ...}; removed: true
result_channel: "val_accuracy: 1.0000\ntest_accuracy: 0.4242\n"
```

The run dir on TASL-2 is under
`/home/dowling/r1_engineering/tasl2_hostcheck_20261121/records/g0_smoke_20261121T013357Z/`; the record,
`run.log`, `result_channel.txt` and `gpu_report.json` (for C6) are copied into the captures. This is the
end-to-end check of conditions C1–C4.

### C6 — GPU smoke with the sandbox on

```
# run_checks.sh: preflight (no compute apps, no Track X marker), then
#   flock -w 180 9  on ~/r1_locks/gpu0.lock, then
systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c \
  'CG=$(cut -d: -f3 /proc/self/cgroup); export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG; \
   exec $VENV scripts/probe_gpu.py --repo $REPO --base $BASE \
     --out captures/c6_gpu_smoke.json --tag gpu_smoke'
#   then flock -u 9 and the after-state capture
```

The node is the unit's `tests/trackg/isolated_fixture` (frozen `parent.py`/`worker.py` + editable `train.py`);
in a temporary copy of the node, the **editable** `train.py` was replaced by one whose `train()` allocates and
synchronises a small CUDA tensor with torch (`torch.arange(64, device="cuda:0")*2+1`, a 16×16 matmul,
`torch.cuda.synchronize()`), writes `gpu_report.json` into the working copy and prints `GPU_PROBE {...}` to the
run log. The frozen parent computes the metric from the worker's predictions and writes `val_accuracy`, as
usual. The node does **not** set `shared_dev_shm` and no waiver is given.

`c6_gpu_smoke.json` (`records/gpu_smoke_20261121T013358Z/`):

```
checks: {outcome_ok, effective_true, waivers_empty, exceptions_empty, worker_sandbox_present,
         gpu_report_written, gpu_ran_in_worker, gpu_tensor_sum_correct, worker_pid1,
         run_log_has_gpu_probe, no_cuda_error_text, metric_written, cgroup_removed,
         gpu_env_by_uuid} = all true
effective: true   waivers: {}   exceptions: []
gpu_uuid: GPU-4d623e76-7587-ee15-a633-46f60d220d94
environment_applied: CUDA_VISIBLE_DEVICES = GPU-4d623e76-7587-ee15-a633-46f60d220d94
                     CUDA_DEVICE_ORDER = PCI_BUS_ID
gpu_report: {pid: 1, ppid: 0, uid: 0, cuda_available: true, device_count: 1,
             device_name: "NVIDIA GeForce RTX 4090", capability: [8, 9],
             tensor_sum: 4096.0, expected_sum: 4096.0, tensor_sum_ok: true,
             matmul_value: 16.0, matmul_ok: true, cuda_initialized: true,
             memory_allocated_bytes: 33556992,
             ns_pid: "pid:[4026533002]", ns_user: "user:[4026533000]", ns_mnt: "mnt:[4026533001]",
             dev_shm: [], ok: true}
outcome: {kind: ok, value: 1.0}; result_channel: "val_accuracy: 1.0000\ntest_accuracy: 0.4242\n"
```

So CUDA ran in the sandboxed worker (PID 1 of its own user/mount/PID namespaces; private `/dev/shm` empty),
the parent wrote the metric, and there was no CUDA error. The GPU was idle before and after (no compute apps),
and the documented exclusive lease was taken:

```
gpu_lease_status.txt:
  lease_file=/home/dowling/r1_locks/gpu0.lock
  lease_mode=flock-exclusive, fd 9, no lease-log write
  acquired_utc=2026-11-21T01:33:58Z
  released_utc=2026-11-21T01:34:00Z rc=0
```

**Implementation finding (for the kit/U2 operator, not a host failure).** The runner exports
`CUDA_VISIBLE_DEVICES=",".join(limits.gpu_uuids)`; a run with the default empty `gpu_uuids` therefore exports
`CUDA_VISIBLE_DEVICES=""`, which hides every GPU from CUDA (the first diagnostic attempt saw `cuInit rc 100
"no CUDA-capable device is detected"` while NVML still saw one device). The accepted way to name a GPU is by
UUID — `ResourceLimits(gpu_uuids=("GPU-4d623e76-…",))`, exactly what `tests/trackg/port_smoke_gpu.py
--gpu-uuid` does. With the UUID, C6 passes with `effective: true` and no exception. The autoresearch kit's node
already uses this mechanism (`--gpu-uuid`), and its option-A result path is the CPU `memfd` buffer, not CUDA IPC,
with `shared_dev_shm: false`, so `effective: true` is achievable for AR runs on TASL-2.

**Scope of C6 / §5.5.** This smoke exercises CUDA device allocation and synchronisation inside the sandboxed
worker, not CUDA IPC between the parent and the worker. `HARNESS_ISOLATION_20261117.md` §5 item 5 ("CUDA IPC
under the PID namespace is untested") therefore remains open; the AR kit's option-A path does not need CUDA
IPC, but any node that uses `cuda_share`/`cuda_open` is still uncovered by this host check. That is a
disclosure for the independent reviewer, not a failed condition.

### C7 — end state

```
$VENV scripts/probe_final.py --repo $REPO --base $BASE --captures $CAP \
  --out captures/c7_final.json --text captures/c7_final.txt --gpu-before captures/c6_gpu_smoke.json
```

`no_leftovers: true` with all six buckets empty (`run_related_processes`, `sleep_leftovers`,
`cgroup_hostcheck_dirs`, `cgroup_run_dirs`, `tmp_g0_userns_dirs`, `dev_shm`). GPU before = after
(`0, GPU-4d623e76-…, 535.309.01, 24564 MiB, 353 MiB, 23830 MiB, 0 %`; compute apps `""`; desktop-owned 353 MiB
is pre-existing). Disk unchanged at **368.7 GiB free**. Host/kernel/tool versions as above. Harness worktree
still clean at `7330338` (`## HEAD（非分支）`); no new commits. Attempt-1 archive
`/home/dowling/r1_trackp/runs/p3a_operator_20261027` exists with unchanged mtime
`2026-11-17 15:42:26 -0800`; the live Track P lease log was not written (flock only). Track X evidence marker
absent.

## Findings for independent review

1. **Code version used.** TASL-2 was checked on worktree `7330338`, which contains the accepted core
   `68cdd1a` **and** the accepted Ada host-check fix `5403392e`. The Ada §3 STOP was caused by defects A/B in
   bare `68cdd1a`; if the gate's wording fixes the expected commit at bare `68cdd1a`, the reviewer must say so,
   because on bare `68cdd1a` (without `5403392e`) the sandbox refuses the Ada host and would very likely refuse
   TASL-2 at the same bind-remount / uv-alias-symlink points. The result here is: the fixed tree passes all
   conditions on TASL-2.
2. **GPU by UUID.** See C6: `gpu_uuids` must be set (the kit smoke does); an empty tuple hides the GPU rather
   than failing loudly, so the U2 operator must not omit `--gpu-uuid`.
3. **Delegated scope is per command.** C3/C5/C6 ran inside fresh
   `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0` scopes; the kit smoke and U2
   must provide `AR_TEST_CGROUP_PARENT` from a live delegated cgroup (or wrap each run in such a scope). The
   session scope is not a writable parent.
4. **CUDA IPC remains untested** (C6 scope note above; §5 item 5). AR option A does not need it.
5. **No waivers were used anywhere**; `timeout factor 3` is the unit default and was not waived.
6. **No host state was modified** beyond the new run root `/home/dowling/r1_engineering/tasl2_hostcheck_20261121/`
   (plus transient scopes/cgroups/tmp dirs that were removed; the operator's own preliminary capture directory
   was rotated to `captures_preliminary_20261121T013128Z/` inside that new root). No deletion or move-aside of
   pre-existing work, no push, no commit; the report and captures are uncommitted in the Mac ops worktree.

## STOP / GO

No §3 condition failed, so there is **no STOP**: the host-condition gate for TASL-2 is **PASS**, and the
autoresearch kit smoke / U2 setup on TASL-2 **may proceed after independent review of this report and its
captures**. Had any condition failed, the recommendation would be **STOP: do not set up or run the autoresearch
kit / U2 on TASL-2**; the C1–C6 records above would then be the exact blocker evidence.

## Captures

Sibling directory `TASL2_ISOLATION_HOST_CHECK_20261121_captures/` (also on TASL-2 at
`/home/dowling/r1_engineering/tasl2_hostcheck_20261121/captures/`), 60 files, 480 KiB:

- `SUMMARY.json`, `SUMMARY.txt` — PASS/FAIL table and this verdict (machine-readable in `SUMMARY.json`).
- `host.json`, `host_facts.txt`, `gpu_state_before.txt`, `gpu_state_after.txt` — host/kernel/uid/cgroup/sysctl/
  disk/GPU/tool facts, repo tips (`7330338`, base `897d83c` on `trackp-20261026`), limits.
- `c1_userns_venv.json`, `c1_userns_syspy.json`, `c2_ptrace.json`, `c3_cgroup.json`/`.txt`,
  `c4_interp.json`/`.txt`, `c5_smoke.json`, `c6_gpu_smoke.json`, `c7_final.json`/`.txt` — the seven conditions.
- `pytest_isolation.json`, `logs/pytest_isolation.log` — 27 passed, 1 skipped (root-only).
- `gpu_lease_status.txt`, `gpu_compute_apps_{pre,post}_gpu_smoke.txt`, `gpu_compute_apps_{before,after}_all.txt`
  — exclusive-GPU lease and idle-state evidence.
- `records/gpu_smoke/` — `run_record.json`, `run.log`, `result_channel.txt`, `gpu_report.json` for the GPU run.
- `logs/` — every probe's stdout/stderr and the orchestrator log (`run_checks.log`).
- `scripts/` — all probes, `run_checks.sh`, `summarize.py`, and the unmodified Ada originals
  (`ada_originals/probe_userns.py`, `ada_originals/probe_smoke.py`) plus the exact unit files used
  (`unit_isolation.py`, `unit_runner.py`, `unit_ar_isolated.py`, `unit_isolated_fixture.py`).
- `SHA256SUMS` — sha256 of every file except itself; `SHA256SUMS` sha256 itself
  `0d0b590be35577409e75ec35a9ffb3f7a33d0e3c025eaba1eda4c606d4353f09`. Verify with:

```
cd TASL2_ISOLATION_HOST_CHECK_20261121_captures && sha256sum -c SHA256SUMS      # Linux
cd TASL2_ISOLATION_HOST_CHECK_20261121_captures && shasum -a 256 -c SHA256SUMS  # macOS
```

**AI-assisted: DeepSeek Harness agent (`tasl2-hostchecker`), 21 Nov 2026. ENGINEERING_ONLY; uncommitted.**
