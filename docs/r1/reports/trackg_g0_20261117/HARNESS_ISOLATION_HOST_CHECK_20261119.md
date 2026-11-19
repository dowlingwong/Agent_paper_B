# Ada host isolation check for R1-HARNESS-ISOLATION (19 November 2026)

**Status: STOP for the host-condition gate of the accepted harness unit `68cdd1a` on Ada `ucrtasl`.**
Five of the seven §3 host conditions pass (non-root uid, unprivileged user+mount+PID+network namespaces,
Yama `ptrace_scope`, a delegated cgroup v2 subtree with `cgroup.kill`, and the run interpreters' `sys.path` hard
check). **Condition 6 fails**: the unit's own worker-sandbox probe is refused on this host, so no isolated run can
start and no run record with `effective: true` exists. Condition 7 (GPU smoke / CUDA IPC across the PID namespace)
therefore could not be exercised. **No GPU was used, no Track G U2/census/T1 run was started, nothing was
committed or pushed, no existing worktree was overwritten or moved, and TASL-7/TASL-2 were not touched.**
ENGINEERING_ONLY; AI-assisted.

Two concrete defects in the accepted core are recorded below with reproduction: (A) the sandbox's bind-remount
drops the source mount's locked `nodev`/`noexec` flags, so the recursive bind of `/sys` cannot be remounted
read-only as uid 1030; (B) with (A) fixed in a scratch copy, the node-env interpreters
(`envs/torch312/bin/python`, `envs/jax312/bin/python`) fail at the worker's PID-1 `execve` because the recreated
venv `bin/python` symlink targets uv's unversioned `cpython-3.12-linux-x86_64-gnu` alias directory, which the
runner does not bind (only its realpath `…cpython-3.12.16…` is bound). `/usr/bin/python3` and the real uv binary
do pass (A) alone, and a scratch-copy smoke with `/usr/bin/python3` produces `effective: true, waivers {}` —
i.e. the rest of the host is sufficient once the core is fixed and reviewed.

## Authority and inputs

- PLAN rows **R1-HARNESS-ISOLATION** and **R1-TRACKG-PORT-DECISIONS (4)** (main `50176481`), as consumed by
  `docs/r1/reports/HARNESS_ISOLATION_20261117.md` §3 (host conditions and waivers), §5 (limits) and
  `docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md` §1 (branches), §2 (how nodes run), §7 (steps for the
  experiment agent).
- Reviews: `docs/r1/reviews/HARNESS_ISOLATION_REVIEW_20261117.md` — round 8 **ACCEPTED**, code
  `68cdd1ae2d46d2494ed6fbe69d7dd5693b5c643e`, report `06692ecc` + wording fix `80b7cb92`;
  `docs/r1/reviews/TRACKG_PORT_ISOLATION_REVIEW_20261117.md` — accepted commits
  `061d638edc91254477d699b3be89e40625cc99ec` (MLGym), `0aae2f68376a5665ce1869e835906615b7e08ecc` (MLAgentBench),
  `5d3dccccf1790203212d2e0aa96c969f7c703fdc` (autoresearch, with the GPU-smoke condition), report `660f27a2` +
  wording `b82f9e01`.
- Mac ops worktree `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/ops-tasl-20261116`, published
  main fetched as `origin/main = de3de54fd22dcdd86215be0924307e36a64ed08b`.
- Ada workspace `/home/dowling/r1_trackg_20261117`; harness repo `autoresearch_harness`
  (`https://github.com/dowlingwong/autoresearch_harness`), paper repo `Agent_paper_B_main_50176481`
  (`git@github.com:dowlingwong/Agent_paper_B.git`).

## Branch / worktree records (Ada)

New sibling worktrees were created; the accepted U0/U3 worktrees were not overwritten. Fetches:
`git fetch --prune origin "+refs/heads/*:refs/remotes/origin/*"` in both repos (no local isolation branch existed
before; the four harness branches were fetched new, tips match the review records exactly).

| Purpose | Branch | Base | Tip (full sha) | Dir on Ada | Dirty | Relationship |
|---|---|---|---|---|---|---|
| core harness | `mac-harness-isolation-20261117` | `717ad835df32bbe1047d032fb5bb8dde5384a258` | `68cdd1ae2d46d2494ed6fbe69d7dd5693b5c643e` | `harness_iso_core` | clean | 8 commits ahead of base; `src/` = accepted core |
| MLGym kit | `mac-trackg-iso-mlgym-20261117` | U3 `334c89ce0e036022cd1f993830a84809092ca44c` | `061d638edc91254477d699b3be89e40625cc99ec` | `harness_iso_mlgym` | clean | 24 ahead of U3 base; contains `68cdd1a`; `git diff 68cdd1a -- src` empty |
| MLAgentBench kit | `mac-trackg-iso-mlab-20261117` | U3 `8596a0ec730b4924e031adf90cb0c38a9a897399` | `0aae2f68376a5665ce1869e835906615b7e08ecc` | `harness_iso_mlab` | clean | 20 ahead; contains `68cdd1a`; `src` diff empty |
| autoresearch kit | `mac-trackg-iso-ar-20261117` | U3 `08d065077d40087114452697d5d596e66a0578be` | `5d3dccccf1790203212d2e0aa96c969f7c703fdc` | `harness_iso_ar` | clean | 23 ahead; contains `68cdd1a`; `src` diff empty |
| paper report | `mac-harness-isolation-report-20261117` | paper `origin/main de3de54f…` | `6655214e399c6548c71e680c50f457e956be6f63` | `paper_harness_isolation_report` | clean | fetched new; contains the accepted report/review |

Existing worktrees left untouched: harness `autoresearch_harness` @ `717ad83` (branch
`r1-local-trackg-v2-20261114`), `harness_ar` @ `08d0650`, `harness_mlab` @ `8596a0e`, `harness_mlgym` @
`334c89c` (all detached, clean), paper `Agent_paper_B_main_16185b0b` @ `16185b0b`, `Agent_paper_B_main_50176481`
@ `50176481` (its pre-existing ` M r1/scripts/configs/paper_a_status_ada.json` is unrelated and was not touched),
`/home/dowling/Agent_paper_B` @ `17b7394e`. Nothing was moved aside or deleted. Run root for this check:
`/home/dowling/r1_trackg_20261117/host_check_g0_20261119/` (new).

## Host

`ucrtasl`; Linux `5.15.0-151-generic #161-Ubuntu SMP Tue Jul 22 14:25:40 UTC 2025 x86_64`; uid `1030(dowling)`,
gid `1030(dowling)`, groups `44(video),109(render)`; `HOME=/home/dowling`; no root and no sudo used. 96 CPUs; 503 GiB
RAM; 71 GiB free on `/` (96 % used) at check time. All commands were run over
`ssh -o BatchMode=yes experiment_zhixu …`; captures are in the sibling
`HARNESS_ISOLATION_HOST_CHECK_20261119_captures/` directory (`SHA256SUMS` there).

## §3 conditions, one by one

| # | Condition (core report §3) | Result | Evidence |
|---|---|---|---|
| 1 | unprivileged user namespaces with mount, PID, network usable by the run uid | **PASS** | `kernel.unprivileged_userns_clone=1`; `/proc/sys/user/max_user_namespaces=2062220`; `kernel.apparmor_restrict_unprivileged_userns` absent (AppArmor enabled `Y`, LSM `lockdown,capability,landlock,yama,apparmor`); a real probe that calls the launcher's single `unshare(CLONE_NEWUSER|CLONE_NEWNS|CLONE_NEWPID|CLONE_NEWNET|CLONE_NEWCGROUP)` succeeds, maps uid 1030→0, and mounts a tmpfs in the new mount namespace. A second probe (`unshare -U -r -m -f`) succeeds with the same root construction up to `/sys`. |
| 2 | Yama `ptrace_scope` ≥ 1 | **PASS** | `/proc/sys/kernel/yama/ptrace_scope = 1`; `yama` is in `/sys/kernel/security/lsm`. |
| 3 | delegated cgroup v2 subtree the uid can write, with `cgroup.kill` | **PASS** | `/sys/fs/cgroup` is `cgroup2 rw,nosuid,nodev,noexec,relatime,nsdelegate,memory_recursiveprot`; the systemd user manager cgroup `user.slice/user-1030.slice/user@1030.service` is owned by `dowling`, `cgroup.subtree_control = memory pids`, `cgroup.procs` writable, `cgroup.kill` present; `systemd-run --user --scope -p Delegate=yes` gives a scope with writable `cgroup.procs`/`cgroup.subtree_control` and child-cgroup creation; the unit's own `RunCgroup.create` in that scope moved a live process in, `cgroup.kill` killed it (`empty_after: true`, process `-9`), and removed the cgroup. |
| 4 | the run is not root | **PASS** | `euid=1030`; the runner's own root refusal is the code path used, and the control run's record carries `euid: 1030`. |
| 5 | the run interpreter's `sys.path` holds no home directory, runs tree or ancestor of either (hard `RunnerError`, no waiver) | **PASS** | the unit's own `WorkingCopyRunner._sandbox_config()` check passes for `/usr/bin/python3` (3.10.12), `envs/torch312/bin/python` (3.12.16) and `envs/jax312/bin/python` (3.12.16). Note the interpreters' installation lives under `/home/dowling/.local/share/uv/…` and `/home/dowling/r1_trackg_20261117/envs/…`, so those subtrees are bound read-only into the worker by design; no home-root, runs-tree or ancestor entry is present. |
| 6 | a real sandboxed smoke whose record shows `effective: true` | **STOP** | see below: the unit's own `worker_sandbox_available()` refuses the host; no isolated run starts, so no record exists. |
| 7 | GPU smoke with the sandbox on exercising CUDA IPC across the PID namespace (§5.5) | **BLOCKED / NOT TESTED** | cannot start because of condition 6; no GPU was used (Paper A gate and co-tenancy checked anyway). |

### Condition 6 — the concrete failure

Command (the unit's own smoke path; the fixture node and runner are the unit's `tests/trackg` fixture and
`WorkingCopyRunner`, run inside a delegated cgroup so the cgroup condition is satisfied):

```
systemd-run --user --scope -p Delegate=yes -- bash -c \
  'CG=$(cut -d: -f3 /proc/self/cgroup); export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG; \
   /home/dowling/r1_trackg_20261117/envs/torch312/bin/python \
   /home/dowling/r1_trackg_20261117/host_check_g0_20261119/scripts/probe_smoke.py'
```

Result (captured in `captures/probe_smoke.json`, `pytest_targeted.txt`):

```
autoresearch.trackg.runner.RunnerError: this host refuses the worker sandbox
(AR_ERROR isolation: worker sandbox setup failed at read-only /sys:
 PermissionError(1, 'remount: Operation not permitted')); give the no_worker_sandbox waiver
to run without it (then the run is not isolated)
```

The unit's own probe (`isolation.worker_sandbox_available`) reproduces the same message for `/usr/bin/python3`
and for the `envs/torch312` interpreter (`captures/probe_sandbox_unit_py3.json`,
`probe_sandbox_unit_torch312.json`). **No `run_record.json` is written for a refused run**; the run directory
`records/g0_core_smoke_20261119T002605Z/` holds only `_ar_shim/`, `_root/`, `_sandbox_probe/`, `code/`
and `work/`.

The unit's own `tests/trackg/test_trackg_isolation.py` on Ada, inside a delegated cgroup:

- full file: after 12 tests (5 passed, 7 failed) it **hung** in
  `test_elapsed_time_beyond_the_timeout_is_a_timeout_even_after_a_normal_exit`: the test's helper shell waits for
  `started.txt` that the refused run never creates, and the test blocks in `helper.wait()`; it was killed after
  ~15 minutes (`captures/pytest_isolation_full.txt` = `pytest_isolation_full_hung_20261119.txt`, `...FFFFFF.F.`).
- same file with that one test deselected: **14 failed, 9 passed, 1 skipped, 1 deselected in 4.31 s**
  (`captures/pytest_isolation_deselect.txt`); every failure is the same `RunnerError` above. The skipped test is
  the root-only uid-65534 test.

### Root cause A (accepted code, reproducible): the bind remount drops locked `nodev`/`noexec`

`/sys` on Ada is `sysfs rw,nosuid,nodev,noexec,relatime` (10 submounts below it). The sandbox
(`src/autoresearch/trackg/node_lib/ar_isolated.py`, `_sandbox_preexec.bind()`) does a recursive bind and then
remounts with `_MS_BIND | _MS_REMOUNT | _MS_NOSUID | _MS_RDONLY`, i.e. it drops `MS_NODEV` and `MS_NOEXEC`.
In a user namespace those flags are locked on the inherited mount, and the kernel answers **EPERM**. Flag-by-flag
in a new user+mount namespace with uid 1030 mapped to 0 (`captures/probe_remount_flags.txt`):

| remount flags (all with `MS_BIND|MS_REMOUNT`) | result |
|---|---|
| `RDONLY|NOSUID` (the unit's flags) | EPERM |
| `RDONLY|NOSUID|NODEV` | EPERM |
| `RDONLY|NOSUID|NODEV|NOEXEC` | ok |
| the host mount's own `RDONLY|NOSUID|NODEV|NOEXEC|RELATIME` | ok |

`/usr`, `/etc`, … do not carry locked `nodev`/`noexec`, which is why the failure is reported at the `/sys`
step (the first `ro_flat` path). This is not AppArmor: the sysctl is absent, `unshare` itself succeeds, and the
same sequence with the flags preserved succeeds under `unshare -U -r -m -f`
(`captures/mounts_after_unshare1_exec.txt`, `mounts_after_unshare1_fork.txt`).

### Root cause B (scratch-copy diagnostic only): uv-venv interpreter symlinks

On a **scratch copy** `/tmp/ada_iso_fixcheck` (not an accepted worktree, nothing in the repo was edited), with only
the bind-remount changed to preserve the source mount's locked `nosuid/nodev/noexec` flags, the unit's own probe
becomes:

| interpreter | `worker_sandbox_available` |
|---|---|
| `/usr/bin/python3` (3.10.12) | **ok** (`captures/fixcheck/fixcheck_systempy.json`) |
| real uv binary `/home/dowling/.local/share/uv/python/cpython-3.12.16-linux-x86_64-gnu/bin/python3.12` | **ok** (`fixcheck_real_uv_python.json`) |
| `/home/dowling/r1_trackg_20261117/envs/torch312/bin/python` | `PID 1 failed at execve …/envs/torch312/bin/python: FileNotFoundError(2)` (`fixcheck_venv_torch312.json`) |
| `/home/dowling/r1_trackg_20261117/envs/jax312/bin/python` | same `FileNotFoundError(2)` (`fixcheck_venv_jax312.json`) |

The venv `bin/python` is a symlink to
`/home/dowling/.local/share/uv/python/cpython-3.12-linux-x86_64-gnu/bin/python3.12`, and that unversioned path is
a symlink to `…cpython-3.12.16-linux-x86_64-gnu`. The sandbox recreates the venv symlink with its absolute target,
but only the 3.12.16 realpath is bound, so the target does not exist inside the new root. The kit smoke
(`tests/trackg/port_support.py::run_smoke`) uses `interpreter=sys.executable`, i.e. exactly this venv path, so this
is a second, independent blocker for the per-node smoke and for the GPU smoke. It needs its own reviewed fix
(e.g. bind every symlink target/realpath, or require a run interpreter path whose symlink chain is inside the
bound set); it is **not** to be worked around by starting the run as `/usr/bin/python3`, which would not be the
node's environment.

The same scratch copy with `/usr/bin/python3` runs the unit's smoke end to end and writes a record with
`outcome: ok 1.0`, `effective: true`, `waivers: {}`, `exceptions: []`, `euid: 1030`, `ptrace_scope: 1`,
`nsdelegate: true`, `log_intact: true`, `frozen_files_checked: 3`, cgroup created/killed/removed
(`records/g0_scratch_fix_systempy_20261119T005346Z/`, `captures/fixcheck/`). **This is diagnostic evidence that the
host is otherwise sufficient; it is not the accepted unit and does not satisfy condition 6.**

### Control run (accepted unit, `no_worker_sandbox` waiver): everything except the sandbox works

With the `no_worker_sandbox` waiver (clearly recorded, `effective: false`), the same fixture runs to `ok 1.0`
through the accepted `68cdd1a` runner: record `records/g0_control_no_sandbox_waiver_20261119T004808Z/`
(sha256 `42938ac380e3db291133ea12b596cefa7e99060e2288050ce8423d0dd3a2bc4c`): `euid 1030`, `ptrace_scope 1`,
`nsdelegate true`, `log_intact true`, result-channel sha256
`4ffec570b33e852a82e6d95b1e209a6246365a8a8bb8aedf969c2a05ea1117c0`, cgroup `cgroup.kill` with `empty_after: true`,
`removed: true`; `migration_possible: true` (the delegated scope's `cgroup.procs` is uid-writable — the core's
recorded caveat, not a new finding). This rules out the cgroup, uid, ptrace, log and result-channel mechanics as
causes: the sandbox setup alone refuses the host.

### Condition 7 — GPU smoke

`port_smoke_gpu.py` runs through `WorkingCopyRunner` with the worker sandbox; on Ada it would refuse at condition 6
(before any run cgroup or GPU is touched), and after root cause A it would hit root cause B via the node-env
interpreter. It was therefore **not started**; no CUDA context was created and no GPU memory was allocated. For the
record, the co-tenancy/gate state at check time (`captures/paper_a_status.json`, `host_facts.txt`,
`gpu_compute_apps_live_wrapper.txt`):

- 8 × `NVIDIA RTX 6000 Ada Generation`, driver 545.23.08, CUDA 12.3. GPU 2 and GPU 6 idle (5 MiB / 49,140 MiB,
  0 % util); GPUs 0, 1, 3, 4, 5, 7 busy with **other users'** jobs (`jzhan744`: 506530/278975; `hongkun+`:
  3562953/3562958/3562962/3562969). A GPU smoke on an idle card would not have disturbed them.
- `r1/scripts/paper_a_status.py --config r1/scripts/configs/paper_a_status_ada.json`: `verdict: clear_finished`,
  `paper_a_live_waiting_for_card: false`, `compute_apps: 6`, `unidentified_apps: 0`, `paper_a_processes: []`,
  rc 0. So co-tenancy/Paper A is **not** the blocker; the sandbox is.

Consequence: **CUDA IPC across the PID namespace (core §5.5) and the autoresearch B1 expandable-segments fix are
still untested.** The autoresearch GPU smoke remains a precondition for that node, and it cannot pass until both
core defects are fixed and reviewed.

## Waivers and exceptions

None were granted or used for the requested checks; the accepted unit refused rather than run with a waiver. The
only waiver anywhere in these captures is the deliberately labelled diagnostic control above
(`no_worker_sandbox`, record stored with `effective: false`). No `shared_dev_shm` run was attempted (no GPU run).
The accepted unit's record fields were checked in the control record: `waivers` and `exceptions` are exactly as the
code documents them; `effective` is true only with no waiver, no exception, a non-root uid, a cgroup and the
sandbox.

## What remains before any per-node U2

1. **Fix the core (defect A)**: `bind()`'s remount must preserve the source mount's locked flags
   (`nosuid`/`nodev`/`noexec` from `/proc/self/mountinfo` or equivalent), not a fixed subset. This is a frozen file
   (`ar_isolated.py`) in all four branches, so it needs a new commit, an independent review round, a new accepted
   sha, and byte-identical updates of the node copies in the three kit branches (`tests/.../ar_isolated.py` and
   every node's copy), plus fresh `frozen_pin_sha256` values.
2. **Fix the core (defect B)**: make the sandbox able to exec the node-env interpreter (`envs/torch312`,
   `envs/jax312` under `uv`): bind the symlink target(s)/realpath chain, or specify a supported interpreter path.
   Review it with A; both are observable only on a **non-root** host with these venvs.
3. **Re-run this host check** on Ada after the fixes: the unit's own `worker_sandbox_available` must pass for
   each node interpreter, and a smoke record must show `effective: true, waivers {}, exceptions []`.
4. **Then** §7 step 2 (per-node `setup_command`, `AR_TRACKG_DATA_ROOT` outside the repository, `data_manifest.json`
   sha256 recorded; House Prices still needs the user's Kaggle `train.csv`) and §7 step 3 (`port_smoke_gpu.py` per
   node with its own environment, `--gpu-uuid`, `--cpus`, `--memory-limit`, `--runs-root` outside the repository,
   `AR_TEST_CGROUP_PARENT` delegated; check **every** run record: `isolation.waivers` empty and `effective` true,
   except autoresearch where `effective` is false by design and `exceptions == ["shared_dev_shm"]`; refuse any
   `synthetic` marker). The census commits each node's `frozen_pin_sha256` and measured baseline time.
5. **autoresearch GPU smoke** (CUDA IPC across the PID namespace, B1) must pass before that node is used.
6. Author decisions still open from core §5 (labels readable on disk except Breakout; `shared_dev_shm` exception
   for autoresearch; infrastructure-log class in RL; census committing the frozen pin) are untouched by this check.

## Integrity of this check

No commits and no pushes were made on either host; the report and captures are untracked files in the Mac ops
worktree for the root agent to review/commit. No file in any repository was edited or deleted (the only code change
is in the `/tmp/ada_iso_fixcheck` scratch copy used for diagnosis). No process or cgroup from this check is left
behind (scopes checked: only `init.scope`). No GPU job, no HTCondor/deepthought interaction, no T1/U2/census run,
no deletion, no force push.

## Capture index (sibling `HARNESS_ISOLATION_HOST_CHECK_20261119_captures/`)

- `captures/host_facts.txt` — host, sysctls, cgroup, systemd, `/sys` flags, GPU inventory.
- `captures/probe_userns.txt`, `probe_remount_flags.txt`, `mounts_after_unshare1_*.txt` — conditions 1 and A.
- `captures/probe_cgroup.txt` — condition 3 with the unit's own `RunCgroup`.
- `captures/probe_interp_sandbox.json` — condition 5 for all three interpreters.
- `captures/probe_sandbox_unit_py3.json`, `probe_sandbox_unit_torch312.json` — condition 6 refusal.
- `captures/probe_smoke.json`, `pytest_targeted.txt` — condition 6 through the runner and its own test.
- `captures/pytest_isolation_deselect.txt` — 14 failed / 9 passed / 1 skipped / 1 deselected; the 14 failures.
- `captures/pytest_isolation_full.txt` (= `…_hung…`) — the hang at test 13 after 5 passed / 7 failed.
- `captures/probe_smoke_control_no_sandbox.json` — the labelled control run.
- `captures/paper_a_status.json`, `gpu_compute_apps_live_wrapper.txt` — condition 7 co-tenancy/gate evidence.
- `captures/fixcheck/` — scratch-copy diagnosis: preserve-flags probe results, PID-1 execve failures, the minimal
  diff, and the diagnostic `effective: true` smoke record.
- `records/` — the exact run directories cited above; `scripts/` — every probe used; `SHA256SUMS` — hashes of all.
