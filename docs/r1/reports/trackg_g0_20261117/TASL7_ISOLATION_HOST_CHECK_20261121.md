# TASL-7 host isolation check for R1-HARNESS-ISOLATION §3 (21 November 2026)

**Status: host-gate PASS for the seven listed preconditions (GO for the isolated proposer/server smoke on TASL-7); the gate binds fixed tree 7330338 (contains 68cdd1a + 5403392e; bare 68cdd1a is not a valid baseline). **C6 is the GPU-in-sandbox prerequisite, not §3 item 7 CUDA IPC: CUDA IPC across the PID namespace is UNTESTED and §5 item 5 remains open; no cuda_share/cuda_open node may start on the strength of this record.**
subject to independent review of this report and its captures.** ENGINEERING_ONLY; AI-assisted (DeepSeek
Harness agent, `tasl7-hostchecker`, delegated by the lead for author-signed R1-T1-HOST-TASL in the
R1-TRACKG-AR-U2-TASL2 context). The proposer llama-server was **not** started in this task.

The seven conditions of `docs/r1/reports/HARNESS_ISOLATION_20261117.md` §3 were checked in one orchestrated
session on TASL-7 (`2026-11-21T01:59:12Z`–`02:00:19Z`, 67 s) with **no waiver**: unprivileged
user+mount+PID+network(+cgroup) namespaces with a real tmpfs mount, Yama `ptrace_scope`, a delegated cgroup v2
subtree with `cgroup.kill`, the non-root + interpreter `sys.path` hard check, a real sandboxed smoke with
`effective: true`, a GPU smoke with the sandbox on (`effective: true`, `waivers {}`, `exceptions []`, no CUDA
error), and a clean end state with no leftovers and the Track P attempt-1 archive and lease log provably
untouched (pre/post stat + full-content sha256). The unit's own isolation test file also passes in a delegated
scope (27 passed, 1 root-only skip).

Nothing was started from the autoresearch kit, no proposer or U2/T1 run was started, nothing was committed or
pushed, no pre-existing host work was deleted or moved aside, and TASL-2, the Track P attempt-1 archive/EVIDENCE
and lease log, HTCondor/deepthought, and the paused Track P were not touched. The Track P
`~/r1_locks/gpu0.lock` was taken with `flock` for the two seconds of the GPU smoke only; neither lease log was
written. (Only the operator's own first-orchestration capture directory, created in this session, was rotated
aside inside the new run root — see "Deviations".)

## Authority and inputs

- Task authority: author-signed **R1-T1-HOST-TASL**, in the **R1-TRACKG-AR-U2-TASL2** context, delegated by the
  lead; scope = HARNESS_ISOLATION §3 host checks on TASL-7 only, STOP if any condition fails, preserve the
  attempt-1 archive and lease log, no deletion, no push, no proposer llama-server start.
- `docs/r1/reports/HARNESS_ISOLATION_20261117.md` §3 (host conditions and waivers), §5 (remaining limits,
  including item 5 "CUDA IPC under the PID namespace is untested"); `docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md`
  (the port kit's GPU-smoke condition).
- Precedents: Ada G0 host check `docs/r1/reports/trackg_g0_20261117/HARNESS_ISOLATION_HOST_CHECK_20261119.md`
  (STOP: defects A and B of bare `68cdd1a`) and the TASL-2 host check
  `docs/r1/reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_20261121.md`. The probe suite was adapted
  from the Ada G0 originals (Mac ops worktree `ops-tasl-20261116`,
  `HARNESS_ISOLATION_HOST_CHECK_20261119_captures/scripts/probe_userns.py`, `probe_smoke.py`, preserved in the
  TASL-2 captures) and from the TASL-2 adaptations, then ported to this TASL-7 worktree, uid 1011, run root,
  GPU UUID and attempt-1 lease-log paths.
- TASL-7 harness **worktree** `/home/dowling/r1_trackp/harness_cond7a_20261121_t7` @
  `73303380197477df971e865440d0ae11135fe1b3` (detached, clean; created for this task; the option-A branch
  `mac-trackg-iso-ar-cond7a-20261120` was fetched from origin into
  `refs/remotes/origin/mac-trackg-iso-ar-cond7a-20261120`, no push). `git merge-base --is-ancestor` verifies
  this tree contains **both** the accepted isolation core
  `68cdd1ae2d46d2494ed6fbe69d7dd5693b5c643e` **and** the accepted Ada host-check fix `5403392e` ("keep locked
  bind mount flags; bind the interpreter symlink chain"). This matters for review: the Ada §3 STOP was partly
  defects A (bind-remount flags) and B (uv venv symlink chain), fixed in `5403392e`; this check is on a tree
  that contains the fix.
- Base repo `/home/dowling/r1_trackp/autoresearch_harness` @ `897d83c8efa364ec2fdd37288241cc42e01d7274`
  (branch `trackp-20261026`, clean) — the git main repo of the worktree; it does not itself carry
  `src/autoresearch/trackg` on that branch, so the worktree is the code tree used.
- `trackp-gpu` venv `/home/dowling/r1_trackp/venvs/trackp-gpu/bin/python`: Python 3.12.15, torch 2.6.0+cu124
  (CUDA 12.4, `cuda.is_available()=True`). System `/usr/bin/python3` is 3.10.12. The venv `sys.path` holds the
  uv alias directory `/home/dowling/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu` under `$HOME`; see C4
  — this does **not** trip the unit's hard check on the fixed tree.
- Run root (new): `/home/dowling/r1_engineering/tasl7_hostcheck_20261121/` with `scripts/`, `captures/`,
  `records/`, `work/`, plus `captures_precheck_run1_20261121T015718Z/` (the first orchestration, preserved, not
  deleted). Raw captures were fetched to this report's sibling
  `TASL7_ISOLATION_HOST_CHECK_20261121_captures/` (86 files, 1.2 MiB; `SHA256SUMS` covers 85 files,
  `sha256 = b0897d28ec2500d4d6f1ca510dba25daaad7653d058a871adf3f3e3456c56956`, verified both on TASL-7 and
  locally with `shasum -a 256 -c SHA256SUMS`).
- Non-authorities deliberately not touched: TASL-2 (any host/unit), the Track P attempt-1 archive
  `/home/dowling/r1_trackp/runs/p3a_operator_20261027` and its `EVIDENCE`, both attempt-1 lease-log candidates
  `/home/dowling/r1_locks/trackp_evidence.log` and `/home/dowling/r1_trackp/runs/gpu_lease_log.jsonl`,
  HTCondor/deepthought, and the paused Track P (no lease-log write; `flock` only, for ~2 s).

## Host

`TASL-7` (`ssh -o BatchMode=yes tasl7`), Linux `6.8.0-149-generic #149~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Wed
Oct 28 20:58:45 UTC 2026 x86_64`, Ubuntu 22.04.5 LTS (jammy), boot id
`713ca10b-ec21-413c-b61f-30da4a7b1e96`; uid/euid `1011(dowling)`, gid 1011, groups `1011` only, non-root, no
sudo used; 24 CPUs; `MemTotal 65 537 124 kB`; `/` (and `/home`) on `/dev/nvme0n1p2`, **514.0 GiB free**
(551 899 877 376 bytes) at check time; GPU 0 = NVIDIA GeForce RTX 4090 24 564 MiB, driver `580.178.04` (NVRM
`580.178.04`, Tue Jul 7 12:38:21 UTC 2026), UUID `GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1`, 44 MiB used,
0 % utilisation, **no compute apps** before, during or after; `/sys/fs/cgroup` =
`cgroup2 rw,nosuid,nodev,noexec,relatime,nsdelegate,memory_recursiveprot`. All commands over `ssh -o
BatchMode=yes tasl7`; TASL-7's local clock is PST (UTC−8), report times UTC.

Relevant sysctls: `kernel.yama.ptrace_scope=1`, `kernel.unprivileged_userns_clone=1`,
`user.max_user_namespaces=255164`, `kernel.apparmor_restrict_unprivileged_userns=0` (the Ubuntu AppArmor userns
restriction is off), `kernel.unprivileged_bpf_disabled=2`, `kernel.kptr_restrict=1`, `kernel.dmesg_restrict=1`,
`fs.protected_hardlinks=1`, `fs.protected_symlinks=1`; LSM `lockdown,capability,landlock,yama,apparmor`.

Tool versions: bash 5.1.16; systemd 249 (249.11-0ubuntu3.23), user manager `running`; `systemd-run`,
`systemctl --user`, `flock`/`unshare` (util-linux 2.37.2), `timeout`, `sha256sum`, `nvidia-smi` present;
`/usr/bin/python3` 3.10.12; `trackp-gpu` 3.12.15 / torch 2.6.0+cu124 (CUDA 12.4, available true); git 2.34.1.

## §3 conditions

| # | Condition (HARNESS_ISOLATION §3) | Result | Key evidence (capture) |
|---|---|---|---|
| C1 | unprivileged user namespaces with mount, PID and network (and cgroup) namespaces usable by the run uid | **PASS** | `unshare(CLONE_NEWUSER\|CLONE_NEWNS\|CLONE_NEWPID\|CLONE_NEWNET\|CLONE_NEWCGROUP)` (`0x72020000`) rc 0 for both interpreters; uid 1011→0 map; child is PID 1 of a new PID namespace; real tmpfs mount rc 0 + write ok (`c1_userns_venv.json`, `c1_userns_syspy.json`) |
| C2 | Yama `ptrace_scope` ≥ 1 | **PASS** | `kernel.yama.ptrace_scope=1`, `yama` in `lockdown,capability,landlock,yama,apparmor`; parent→child attach ok, unrelated same-uid sibling attach `EPERM` errno 1 (`c2_ptrace.json`) |
| C3 | delegated cgroup v2 subtree the uid can write, with `cgroup.kill` | **PASS** | scope `run-rc56f1…scope`; `memory.max=8589934592`; `memory.swap.max=0`; `cgroup.kill` exists; `cgroup.procs` writable; owner uid 1011; `nsdelegate` true; unit `RunCgroup` create→join pid→`cgroup.kill`→`empty_after:true` (child rc −9)→remove (`c3_cgroup.json/.txt`) |
| C4 | the run is not root; the run interpreter's `sys.path` holds no home dir, runs tree or ancestor (hard `RunnerError`, no waiver) | **PASS** | euid 1011; unit `WorkingCopyRunner._sandbox_config` passes for `/usr/bin/python3` **and** `trackp-gpu` venv; `broad_entries=[]`; `worker_sandbox_available=True` for both; no venv-home failure (`c4_interp.json/.txt`) |
| C5 | a real sandboxed smoke whose record shows `effective: true` | **PASS** | record: `effective:true`, `waivers {}`, `exceptions []`, `euid 1011`, `ptrace_scope 1`, `nsdelegate true`, `log_intact true`, `parent_traced_by null`, `parent_dumpable_at_accept false`, cgroup removed; outcome `ok` 1.0 (`c5_smoke.json`, `records/g0_smoke/`) |
| C6 | GPU smoke with the sandbox on (GPU-in-sandbox prerequisite; not §3 item 7 CUDA IPC) | **PASS** | GPU by UUID (`CUDA_VISIBLE_DEVICES=GPU-ab72fb4a-…`); `effective:true`, `waivers {}`, `exceptions []`; worker PID 1 in new user/mount/PID namespaces allocated+synchronised a CUDA tensor: `tensor_sum 4096.0` (expected), 16×16 matmul ok, 33.6 MB allocated, `cuda_available true`, no CUDA error; metric written; cgroup removed (`c6_gpu_smoke.json`, `records/gpu_smoke/`) |
| C7 | end state: GPU before/after, no leftovers, worktree clean, disk, attempt-1 archive/lease untouched | **PASS** | GPU identical before/after (44 MiB, no compute apps, 0 %); no leftover processes/cgroups/tmp dirs; worktree `7330338` clean; 514.0 GiB free; attempt-1 archive + lease logs stat-identical pre/post (contents not content-hashed; archive content hash recorded) (`tree_sha256 299237d0…`, `content_sha256 af7ede86…`) (`c7_final.json/.txt`, `attempt1_compare.json/.txt`) |

Supplementary, not a §3 host condition: the unit's own `tests/trackg/test_trackg_isolation.py` in a delegated
scope: **27 passed, 1 skipped in 14.89 s** (`pytest_isolation.json`, `logs/pytest_isolation.log`). The skip is
the root-only `test_unprivileged_end_to_end` (`@pytest.mark.skipif(not ROOT, reason="needs root to drop to uid
65534 and delegate a cgroup")`). The `timeout factor 3` row of §3 is satisfied by the unit default and was not
waived (`ResourceLimits.timeout_factor = 3.0` in both smoke records).

## How the check ran

One orchestrated session from `/home/dowling/r1_engineering/tasl7_hostcheck_20261121`:

```
bash scripts/run_checks.sh        # writes captures/, SUMMARY.json/txt, SHA256SUMS
```

`run_checks.sh` exports `XDG_RUNTIME_DIR=/run/user/1011` and
`DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1011/bus` (needed for `systemd-run --user` over ssh), sets
`PYTHONDONTWRITEBYTECODE=1` (and passes it into every `systemd-run` scope with `-E`) so the harness worktree
stays clean, and captures each step's stdout in `captures/logs/`. The exact per-condition commands and raw
results follow; every command is reproduced verbatim in `captures/scripts/run_checks.sh` and the individual
probes, and the orchestrator's own stdout is `captures/logs/run_checks.log`.

### C1 — unprivileged user+mount+PID+network(+cgroup) namespaces

```
$VENV scripts/probe_userns.py --out captures/c1_userns_venv.json      # 3.12.15
/usr/bin/python3 scripts/probe_userns.py --out captures/c1_userns_syspy.json  # 3.10.12
```

The probe mirrors the launcher (`ar_isolated`) rather than the `unshare(1)` CLI: it calls
`prctl(PR_SET_DUMPABLE)`, then one `unshare()` with
`CLONE_NEWUSER|CLONE_NEWNS|CLONE_NEWPID|CLONE_NEWNET|CLONE_NEWCGROUP` (`flags 0x72020000`), writes
`setgroups=deny`, `uid_map 0 <uid> 1`, `gid_map 0 <gid> 1`, records every `/proc/self/ns/*` inode, mounts a
real `tmpfs` and writes a file into it, then forks a child that is **PID 1** of the new PID namespace.

Result (identical shape for both interpreters): `unshare_rc 0`, `unshare_errno 0`,
`mapped_uid_in_new_userns 0`, `mapped_gid_in_new_userns 0`, `tmpfs_mount_rc 0`, `tmpfs_mounted true`,
`tmpfs_writable "userns mount ok"`, `pid_namespace_child {pid: 1, ppid: 0, uid: 0, new_pid_namespace: true}`.
Example: caller `user:[4026531837]` → child `user:[4026532927]`, `mnt:[4026531841]→mnt:[4026532999]`,
`net:[4026531840]→net:[4026533002]`, `cgroup:[4026531835]→cgroup:[4026533001]`, child pid ns
`pid:[4026533000]`. The mountinfo line shows the real tmpfs:
`/tmp/g0_userns_179652 rw,nosuid,nodev,relatime - tmpfs tmpfs rw,size=16384k,mode=755,uid=1011,gid=1011`.
The `userns_only` control (a user namespace with no mapping, so no mount capability) is recorded alongside and
is expected to be non-mounting (`tmpfs_mount_result "Operation not permitted"`); the mapped probes above are
the condition.

Host support: `kernel.unprivileged_userns_clone=1`, `user.max_user_namespaces=255164`,
`kernel.apparmor_restrict_unprivileged_userns=0` (the Ubuntu AppArmor userns restriction is off), LSM includes
`apparmor`. TASL-7 runs Ubuntu 22.04 with the HWE 6.8 kernel, so the Ubuntu 24.04 AppArmor caveat of §3 does
not bite here.

### C2 — Yama `ptrace_scope` ≥ 1

```
$VENV scripts/probe_ptrace.py --out captures/c2_ptrace.json
```

`ptrace_scope_raw "1"`, `ptrace_scope 1`, `lsm "lockdown,capability,landlock,yama,apparmor"`,
`yama_in_lsm true`. Functional probes: `parent_attach_child {ok: true, why: ok}`,
`parent_detach_child {ok: true}`, `unrelated_sibling_attach {ok: false, errno: 1, why: "Operation not
permitted"}` — i.e. same-uid but non-ancestor tracing is denied by Yama, while the parent still has ptrace. All
helper processes are SIGKILLed and reaped before exit.

### C3 — delegated cgroup v2 subtree with `cgroup.kill`

```
systemd-run --user --scope -E PYTHONDONTWRITEBYTECODE=1 \
  -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- \
  $VENV scripts/probe_cgroup.py --repo $REPO --out captures/c3_cgroup.json --text captures/c3_cgroup.txt
```

`c3_cgroup.txt` (verbatim, values):

```
scope=/sys/fs/cgroup/user.slice/user-1011.slice/user@1011.service/app.slice/run-rc56f114050c946059d8835cd12c3ed0d.scope
memory.max=8589934592
memory.swap.max=0
cgroup.kill_exists=True
cgroup.procs_writable=True
owner_uid=1011 euid=1011
nsdelegate=True
mountinfo=['34 25 0:29 / /sys/fs/cgroup rw,nosuid,nodev,noexec,relatime shared:9 - cgroup2 cgroup2 rw,nsdelegate,memory_recursiveprot']
runcgroup={"path": ".../run-rc56f114050c946059d8835cd12c3ed0d.scope/ar_hostcheck_179675_179675_288754554",
 "migration_possible": true, "processes_before": [179677], "populated_before": true,
 "kill": {"method": "cgroup.kill", "processes_before": 1, "empty_after": true},
 "child_returncode": -9, "populated_after": false, "kill_method": "cgroup.kill", "empty_after": true,
 "removed": true}
checks={"cgroup_kill_exists": true, "kill_method_cgroup_kill": true, "memory_max_8g": true,
        "memory_swap_max_0": true, "nsdelegate": true, "owner_is_caller": true,
        "procs_writable": true, "runcgroup_kill": true, "scope_unit": true}
```

The `RunCgroup` create/move/kill/remove probe is the unit's own code (`isolation.RunCgroup`), not a shell
imitation; the run cgroup was removed. Note the cgroup parent is a **short-lived** `systemd-run --user --scope`
created per command with `Delegate=yes`; the session's own `session-*.scope` is not a writable parent. The kit
smoke and the proposer smoke must likewise use a delegated scope (or point `AR_TEST_CGROUP_PARENT` at a live
delegated directory).

### C4 — non-root euid and the interpreter `sys.path` hard check

```
$VENV scripts/probe_interp.py --repo $REPO --base $BASE \
  --out captures/c4_interp.json --text captures/c4_interp.txt
```

The probe calls the unit's own `WorkingCopyRunner._sandbox_config` for both interpreters (the hard
`RunnerError` path, no waiver) and then the unit's own `isolation.worker_sandbox_available`. `c4_interp.txt`:

```
euid=1011 non_root=True
home=/home/dowling runs_root=/home/dowling/r1_engineering/tasl7_hostcheck_20261121/interp_check_.../runs
--- system_py3: /usr/bin/python3
  version=3.10.12 executable=/usr/bin/python3
  sys_path=['/usr/lib/python310.zip', '/usr/lib/python3.10', '/usr/lib/python3.10/lib-dynload',
            '/usr/local/lib/python3.10/dist-packages', '/usr/lib/python3/dist-packages']
  broad_entries=[]   sandbox_config_ok=True sandbox_available=True
--- venv_trackp_gpu: /home/dowling/r1_trackp/venvs/trackp-gpu/bin/python
  version=3.12.15 executable=/home/dowling/r1_trackp/venvs/trackp-gpu/bin/python
  sys_path=['/home/dowling/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu/lib/python312.zip',
            '/home/dowling/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu/lib/python3.12',
            '/home/dowling/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu/lib/python3.12/lib-dynload',
            '/home/dowling/r1_trackp/venvs/trackp-gpu/lib/python3.12/site-packages']
  broad_entries=[]   sandbox_config_ok=True sandbox_available=True
condition_4_pass=True venv_check_pass=True
```

**The venv's home path did not fail the check** and no waiver was needed: the uv base prefix and the venv live
*under* `$HOME` (`/home/dowling/...`), which the unit binds read-only into the worker by design; the hard rule
rejects the home directory itself, the runs tree, or an **ancestor** of either (`broad_entries=[]`). The uv
versioned directory `/home/dowling/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu` is in `sys.path` (the unversioned uv alias is not); the check is exactly
the path that broke the Ada check (Ada defect B); on this tree the accepted fix `5403392e` binds the whole
symlink chain and the sandbox works for both interpreters.

### C5 — real sandboxed smoke, `effective: true`

```
systemd-run --user --scope -E PYTHONDONTWRITEBYTECODE=1 \
  -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c \
  'export PYTHONDONTWRITEBYTECODE=1; CG=$(cut -d: -f3 /proc/self/cgroup); \
   export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG; \
   exec $VENV scripts/probe_smoke.py --repo $REPO --base $BASE \
     --out captures/c5_smoke.json --tag g0_smoke --interpreter $VENV'
```

The probe is the Ada G0 `probe_smoke.py` adapted to this worktree/base: it uses the unit's own
`tests/trackg/isolated_fixture` node and `WorkingCopyRunner`, no waivers. Record
(`records/g0_smoke_20261121T015936Z/run_record.json`, copied to `captures/records/g0_smoke/`):

```
effective: true        waivers: {}        exceptions: []
euid: 1011             ptrace_scope: 1    nsdelegate: true
log_intact: true       frozen_files_checked: 3
parent_traced_by: null parent_dumpable_at_accept: false
outcome: {kind: ok, value: 1.0}
isolation.cgroup: {kill: {method: cgroup.kill, empty_after: true, orphans_killed: 0,
                          parent_traced_by: null, processes_before: 0, session_sweep_killed: false},
                   migration_possible: true, removed: true}
result_channel: "val_accuracy: 1.0000\ntest_accuracy: 0.4242\n"
```

The run dir on TASL-7 is
`/home/dowling/r1_engineering/tasl7_hostcheck_20261121/records/g0_smoke_20261121T015936Z/`; the record,
`run.log` and `result_channel.txt` are copied into the captures. This is the end-to-end check of conditions
C1–C4.

### C6 — GPU smoke with the sandbox on

```
# run_checks.sh: preflight (no compute apps, no Track X marker), then
#   flock -w 180 9  on ~/r1_locks/gpu0.lock, then
systemd-run --user --scope -E PYTHONDONTWRITEBYTECODE=1 \
  -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c \
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

`c6_gpu_smoke.json` (`records/gpu_smoke_20261121T015938Z/`):

```
checks: {outcome_ok, effective_true, waivers_empty, exceptions_empty, worker_sandbox_present,
         gpu_report_written, gpu_ran_in_worker, gpu_tensor_sum_correct, worker_pid1,
         run_log_has_gpu_probe, no_cuda_error_text, metric_written, cgroup_removed,
         gpu_env_by_uuid} = all true
effective: true   waivers: {}   exceptions: []
gpu_uuid: GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1
environment_applied: CUDA_VISIBLE_DEVICES = GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1
                     CUDA_DEVICE_ORDER = PCI_BUS_ID
gpu_report: {pid: 1, ppid: 0, uid: 0, cuda_available: true, device_count: 1,
             device_name: "NVIDIA GeForce RTX 4090", capability: [8, 9],
             tensor_sum: 4096.0, expected_sum: 4096.0, tensor_sum_ok: true,
             matmul_shape: [16, 16], matmul_value: 16.0, matmul_ok: true,
             cuda_initialized: true, memory_allocated_bytes: 33556992,
             ns_pid: "pid:[4026532927]", ns_user: "user:[4026532925]", ns_mnt: "mnt:[4026532926]",
             dev_shm: [], ok: true}
outcome: {kind: ok, value: 1.0}; result_channel: "val_accuracy: 1.0000\ntest_accuracy: 0.4242\n"
command: ["/home/dowling/r1_trackp/venvs/trackp-gpu/bin/python", "-s", "parent.py", "5"]
```

So CUDA ran in the sandboxed worker (PID 1 of its own user/mount/PID namespaces; private `/dev/shm` empty),
the parent wrote the metric, and there was no CUDA error. The GPU was idle before and after (44 MiB used,
0 %, no compute apps), and the documented exclusive lease was taken:

```
gpu_lease_status.txt:
  lease_file=/home/dowling/r1_locks/gpu0.lock
  lease_mode=flock-exclusive, fd 9, no lease-log write
  acquired_utc=2026-11-21T01:59:38Z
  released_utc=2026-11-21T01:59:40Z rc=0
```

**Implementation finding (for the proposer/kit operator, not a host failure).** The runner exports
`CUDA_VISIBLE_DEVICES=",".join(limits.gpu_uuids)`; a run with the default empty `gpu_uuids` therefore exports
`CUDA_VISIBLE_DEVICES=""`, which hides every GPU from CUDA while NVML still sees one device. The accepted way
to name a GPU is by UUID — `ResourceLimits(gpu_uuids=("GPU-ab72fb4a-…",))`, exactly what
`tests/trackg/port_smoke_gpu.py --gpu-uuid` does and what the kit node uses. With the UUID, C6 passes with
`effective: true` and no exception.

**Scope of C6 / §5.5.** This smoke exercises CUDA device allocation and synchronisation inside the sandboxed
worker, not CUDA IPC between the parent and the worker. `HARNESS_ISOLATION_20261117.md` §5 item 5 ("CUDA IPC
under the PID namespace is untested") therefore **remains open**; the AR option-A result path is the CPU
`memfd` buffer, not CUDA IPC, with `shared_dev_shm: false`, so `effective: true` is achievable for AR runs on
TASL-7. Any node that uses `cuda_share`/`cuda_open` is still uncovered by this host check: that is a disclosure
for the independent reviewer, not a failed condition.

### C7 — end state

```
$VENV scripts/probe_final.py --repo $REPO --base $BASE --captures $CAP \
  --out captures/c7_final.json --text captures/c7_final.txt --gpu-before captures/c6_gpu_smoke.json
```

`no_leftovers: true` with all five checked buckets empty (`run_related_processes`, `sleep_leftovers`,
`cgroup_hostcheck_dirs`, `cgroup_run_dirs`, `tmp_g0_userns_dirs`). `/dev/shm` holds 15 **pre-existing** objects
(owners root and `jiachenl`, mtimes 17 and 19 November 2026) that were already present before this session and
are identical in the first-orchestration capture; the sandboxed worker's own `/dev/shm` was empty in both
smokes (`gpu_report.dev_shm: []`). GPU before = after (`44 MiB` used, 24 029 MiB free, 0 %; compute apps `""`).
Disk unchanged at **514.0 GiB free**. Host/kernel/tool versions as above. Harness worktree still clean at
`7330338` (`## HEAD (no branch)`); no new commits.

**Attempt-1 archive and lease log untouched.** A read-only pre/post fingerprint was taken over
`/home/dowling/r1_trackp/runs/p3a_operator_20261027` (including `EVIDENCE` and `journal.jsonl`) and both
lease-log candidates, and compared (`attempt1_compare.json/.txt`):

```
attempt1_archive=/home/dowling/r1_trackp/runs/p3a_operator_20261027
identical=True differences=none
entries=1040 files=724 bytes=11925743308
tree_sha256=299237d06012f42b13cff4b476b2167bec55fa2c2463f056567f986ff7e1e003
content_sha256=af7ede86da7abbe36ff4ec35ef2029ce4e6233afd5fbe4f49e14684c4d16e965
```

The stat lines for the archive root (mtime `2026-10-27 06:35:30.703943745 -0700`, inode 56889763), `EVIDENCE`
(mtime `2026-10-28 03:00:06.409893328 -0700`, inode 56890010), `journal.jsonl` (28 967 bytes, mtime
`2026-10-28 18:25:17.625318511 -0700`, inode 56889764), `/home/dowling/r1_locks/trackp_evidence.log`
(76 bytes, mtime `2026-11-18 17:18:00.997157747 -0800`, inode 56265500) and
`/home/dowling/r1_trackp/runs/gpu_lease_log.jsonl` (58 863 bytes, mtime `2026-11-18 17:17:59.543236151 -0800`,
inode 56783856) are **identical before and after**, as are the full metadata tree hash and the full-content
aggregate hash of all 724 files (11.9 GB). The fingerprint reads metadata and content only; atime is
deliberately excluded from the hash (a read may update it under `relatime`), and no file in the archive or the
lease logs was written, moved, renamed or deleted.

## Deviations / operator notes

1. **Two orchestrations.** The first run (`2026-11-21T01:57:18Z`–`01:58:27Z`) passed all seven conditions, but
   its comparison script read the `stat`/`nentries`/`nfiles`/`bytes` manifests with the wrong filename suffix
   and compared them as empty strings (the two cryptographic hashes — tree and content — did compare
   identically). The script was fixed and the **whole orchestration was re-run** at
   `2026-11-21T01:59:12Z`–`02:00:19Z`; that second run is the authoritative capture in this bundle. The first
   run's captures are preserved un-deleted on TASL-7 at
   `captures_precheck_run1_20261121T015718Z/` and locally as the sibling
   `TASL7_ISOLATION_HOST_CHECK_20261121_run1_precheck_20261121T015718Z/`.
2. **Attempt-1 lease log identity.** The task names "the attempt-1 lease log" without a path; two candidates
   exist on TASL-7 (`r1_locks/trackp_evidence.log` and `runs/gpu_lease_log.jsonl`), so **both** were
   fingerprinted and neither was written. The GPU smoke takes `~/r1_locks/gpu0.lock` by `flock` only and never
   writes a lease log.
3. **`SHA256SUMS` ordering.** `logs/summarize.log` and the bundle README were finalised before the last
   `SHA256SUMS` regeneration (the earlier TASL-2 ordering appended the sums self-hash after hashing, which made
   one line fail verification); the bundle here verifies cleanly, including the README and
   `logs/run_checks.log`.
4. **Run root and rotation.** Only the new run root `/home/dowling/r1_engineering/tasl7_hostcheck_20261121/`
   was created; the operator's own first-orchestration capture directory was moved aside inside it (no
   deletion of any pre-existing host work).

## Findings for independent review

1. **Code version used.** TASL-7 was checked on worktree `7330338`, which contains the accepted core
   `68cdd1a` **and** the accepted Ada host-check fix `5403392e`. The Ada §3 STOP was caused by defects A/B in
   bare `68cdd1a`; if the gate's wording fixes the expected commit at bare `68cdd1a`, the reviewer must say so,
   because on bare `68cdd1a` the sandbox refuses the Ada host and would very likely refuse TASL-7 at the same
   bind-remount / uv-alias-symlink points. The result here is: the fixed tree passes all conditions on TASL-7.
2. **GPU by UUID.** See C6: `gpu_uuids` must be set (the kit smoke does); an empty tuple hides the GPU rather
   than failing loudly, so the proposer smoke must not omit `--gpu-uuid`.
3. **Delegated scope is per command.** C3/C5/C6 ran inside fresh
   `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0` scopes; the proposer smoke
   must provide `AR_TEST_CGROUP_PARENT` from a live delegated cgroup (or wrap each run in such a scope). The
   session scope is not a writable parent.
4. **CUDA IPC remains untested** (C6 scope note above; §5 item 5). AR option A does not need it; the proposer
   unit should keep to the CPU memfd path and `shared_dev_shm: false` for `effective: true`.
5. **No waivers were used anywhere**; `timeout factor 3` is the unit default and was not waived.
6. **No host state was modified** beyond the new run root (plus transient scopes/cgroups/tmp dirs that were
   removed by the probes themselves). No deletion or move-aside of pre-existing work, no push, no commit; the
   report and captures are uncommitted in the Mac ops worktree `ops-tasl-20261116`.
7. **Track P stayed paused**: the attempt-1 archive and lease log are provably untouched (C7), and no Track P
   run, lease-log write, or HTCondor/deepthought action occurred.

## STOP / GO

No §3 condition failed, so there is **no STOP**: the host-condition gate for TASL-7 is **PASS**, and the
**isolated proposer/server smoke on TASL-7 may proceed after independent review of this report and its
captures** — with a delegated per-command scope, `AR_TEST_CGROUP_PARENT` set, the GPU named by the UUID above,
`shared_dev_shm: false`, and no CUDA-IPC requirement. This report does not itself start the proposer
llama-server; that remains the separate following unit. Had any condition failed, the recommendation would be
**STOP: do not run the isolated proposer/server smoke on TASL-7**; the C1–C7 records above would then be the
exact blocker evidence.

## Captures

Sibling directory `TASL7_ISOLATION_HOST_CHECK_20261121_captures/` (also on TASL-7 at
`/home/dowling/r1_engineering/tasl7_hostcheck_20261121/captures/`), **86 files, 1.2 MiB**:

- `SUMMARY.json`, `SUMMARY.txt` — PASS/FAIL table and this verdict (machine-readable in `SUMMARY.json`).
- `host.json`, `host_facts.txt`, `gpu_state_before.txt`, `gpu_state_after.txt` — host/kernel/uid/cgroup/sysctl/
  disk/GPU/tool facts, repo tips (`7330338`, base `897d83c` on `trackp-20261026`).
- `c1_userns_venv.json`, `c1_userns_syspy.json`, `c2_ptrace.json`, `c3_cgroup.json`/`.txt`,
  `c4_interp.json`/`.txt`, `c5_smoke.json`, `c6_gpu_smoke.json`, `c7_final.json`/`.txt` — the seven conditions.
- `attempt1_{before,after}.{stat.txt,tree.txt,tree.sha256,content.txt,content.sha256,nentries.txt,nfiles.txt,bytes.txt,utc.txt}`,
  `attempt1_compare.json`/`.txt` — Track P attempt-1 archive/lease-log pre/post fingerprint and comparison.
- `pytest_isolation.json`, `logs/pytest_isolation.log` — 27 passed, 1 skipped (root-only).
- `gpu_lease_status.txt`, `gpu_compute_apps_{pre,post}_gpu_smoke.txt`, `gpu_compute_apps_{before,after}_all.txt`
  — exclusive-GPU lease and idle-state evidence.
- `records/g0_smoke/`, `records/gpu_smoke/` — `run_record.json`, `run.log`, `result_channel.txt` for both smoke
  runs (+ `gpu_report.json` for the GPU run).
- `logs/` — every probe's stdout/stderr, the orchestrator log (`run_checks.log`) and `summarize.log`.
- `scripts/` — all probes (including the TASL-7 archive fingerprint `fingerprint_attempt1.sh` and comparison
  `compare_attempt1.py`), `run_checks.sh`, `summarize.py`, the adapted `probe_userns.py`/`probe_smoke.py`, and
  the exact unit files used (`unit_isolation.py`, `unit_runner.py`, `unit_ar_isolated.py`,
  `unit_isolated_fixture.py`).
- `SHA256SUMS` — sha256 of every file except itself (85 files); `SHA256SUMS` sha256 itself
  `b0897d28ec2500d4d6f1ca510dba25daaad7653d058a871adf3f3e3456c56956`. Verify with:

```
cd TASL7_ISOLATION_HOST_CHECK_20261121_captures && sha256sum -c SHA256SUMS      # Linux
cd TASL7_ISOLATION_HOST_CHECK_20261121_captures && shasum -a 256 -c SHA256SUMS  # macOS
```

**AI-assisted: DeepSeek Harness agent (`tasl7-hostchecker`), 21 Nov 2026. ENGINEERING_ONLY; uncommitted; no
push.**
