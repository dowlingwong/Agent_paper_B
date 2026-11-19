# R1-HARNESS-ISOLATION: core sandbox fix for the Ada host check (19 November 2026)

**Status: condition 6 is now PASS on Ada for the unit's own probe/smoke, with no waivers; condition 7 (CUDA IPC
across the worker's PID namespace) was exercised for the first time and is BLOCKED by a driver-level
namespace limitation, not by the sandbox code.** The two defects recorded in
`HARNESS_ISOLATION_HOST_CHECK_20261119.md` are fixed on a new core branch from the accepted unit `68cdd1a`:
(A) a bind remount now keeps the source mount's locked `nosuid/nodev/noexec` flags, derived from
`/proc/self/mountinfo`; (B) the sandbox now binds the whole symlink chain of the run interpreter, so a uv
venv's `bin/python -> …/cpython-3.12-linux-x86_64-gnu -> …/cpython-3.12.16-…` alias resolves at the worker's
PID-1 `execve`. The fix is committed locally only (new branch `mac-harness-isolation-fix-20261119`
@ `5403392e94cb59d732f45d6702fc857531ad8fd5`, base `68cdd1a`); **nothing was pushed**, no kit branch was
modified, and TASL-7/TASL-2/HTCondor/deepthought, the existing worktrees and other users were not touched.
ENGINEERING_ONLY; AI-assisted.

## Authority and inputs

- `docs/r1/reports/HARNESS_ISOLATION_20261117.md` §3 (host conditions, waivers) and §5.5 (CUDA IPC across the
  PID namespace) on published paper main `de3de54f`; review `docs/r1/reviews/HARNESS_ISOLATION_REVIEW_20261117.md`
  round 8 ACCEPTED, code `68cdd1ae2d46d2494ed6fbe69d7dd5693b5c643e` (base
  `717ad835df32bbe1047d032fb5bb8dde5384a258`, branch `mac-harness-isolation-20261117`).
- `docs/r1/reports/trackg_g0_20261117/HARNESS_ISOLATION_HOST_CHECK_20261119.md` + `_captures/` — the Ada
  refusal, root causes A and B, and the scratch-copy diagnostic this fix implements.
- `docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md` §1/§2/§7 and the three kit branches
  `mac-trackg-iso-{ar,mlab,mlgym}-20261117` (read-only inspection below).
- Mac harness repo `/Users/wongdowling/Documents/autoresearch_harness` (origin
  `https://github.com/dowlingwong/autoresearch_harness`); Ada workspace `/home/dowling/r1_trackg_20261117`.

## Branches and worktrees

| Purpose | Repo / dir | Branch | Base | Tip (full sha) | Dirty |
|---|---|---|---|---|---|
| core fix, Ada | `/home/dowling/r1_trackg_20261117/harness_iso_fix_20261119` | `mac-harness-isolation-fix-20261119` | `68cdd1a` | `5403392e94cb59d732f45d6702fc857531ad8fd5` | clean |
| core fix, Mac (session workspace) | `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/harness_iso_fix_20261119/repo` | `mac-harness-isolation-fix-20261119` | `68cdd1a` | `5403392e94cb59d732f45d6702fc857531ad8fd5` | clean |

The Mac harness checkout itself is outside this session's writable workspace, so the Mac side of the branch
is a fresh clone under the session workspace (`.git` of `/Users/wongdowling/Documents/autoresearch_harness`
cannot be written here: `cannot open '.git/FETCH_HEAD': Operation not permitted`); the Ada worktree is a new
sibling worktree made with `git worktree add … 68cdd1a`. The commit was made once on Ada and fetched into the
workspace clone over ssh, so both carry the **same** sha. The accepted worktrees
(`harness_iso_core` @ `68cdd1a`, `harness_iso_{ar,mlab,mlgym}`, `harness_ar/mlab/mlgym`, the two paper
worktrees) were not modified. Nothing was pushed.

Commit: `5403392e94cb59d732f45d6702fc857531ad8fd5` — *trackg isolation, Ada host-check fixes: keep locked
bind mount flags; bind the interpreter symlink chain* (3 files, +154/−3:
`src/autoresearch/trackg/node_lib/ar_isolated.py` +47/−3, `src/autoresearch/trackg/runner.py` +34,
`tests/trackg/test_trackg_isolation.py` +73). Full diff in
`/home/dowling/r1_engineering/iso_fix_20261119/git/fix_68cdd1a_to_5403392.diff`
(sha256 `0e27a6c3…`).

## Fix A — bind/remount keeps the source mount's locked flags

`ar_isolated.py` adds three small pure helpers and uses them in `_sandbox_preexec.bind()` and in the final
read-only root remount:

- `_mount_flags_from_mountinfo(lines, path)` — parses `/proc/self/mountinfo` (field 5 mount point, field 6
  per-mount options), takes the longest matching mount point, and returns `NOSUID|NODEV|NOEXEC` for it;
- `_source_mount_flags(path)` — the same from the live mount table (0 if it cannot be read, so a degraded
  environment behaves as before);
- `_bind_remount_flags(locked, read_only)` — `BIND|REMOUNT|NOSUID` plus every *locked* source flag, plus
  `RDONLY` when the bind is read-only.

`bind()` now remounts with `_bind_remount_flags(_source_mount_flags(src), read_only)` instead of a fixed
`BIND|REMOUNT|NOSUID|RDONLY`, and the final root remount derives its flags from `/` (the root tmpfs, mounted
`nosuid,nodev`) so it no longer silently clears `nodev`. This is exactly the scratch-copy change the host
check proved sufficient for `/sys`, with the flag derivation made a reviewable function and the root remount
handled consistently.

## Fix B — the interpreter's symlink chain is bound

`runner.py` adds `_symlink_chain(path)`: it walks the path component by component, appends every symlink on the
way to the real file, and re-resolves through absolute or relative targets (bounded to 40 links). `_sandbox_config`
now applies it to the queried `sys.executable` (and to the `interpreter` argument when it is absolute) and adds
the links to the read-only allow-list before the existing home/runs-tree safety check, so the sandbox recreates
them (`ar_isolated.bind()` recreates a symlink, it does not follow it). For a uv venv this adds the unversioned
`…/cpython-3.12-linux-x86_64-gnu` alias directory (a symlink to the versioned installation whose
`bin/python3.12` and `lib/python3.12` are already bound through `sys.executable` realpath / `sys.base_prefix` /
`sys.path`), so PID 1 can exec `sys.executable` inside the sandbox.

## Regression tests (in `tests/trackg/test_trackg_isolation.py`)

- `test_bind_remount_keeps_the_locked_mount_flags_of_the_source_mount` — synthetic mount table with
  `/sys rw,nosuid,nodev,noexec` and a `/sys/fs/cgroup` submount: parsing, longest-match, the exact
  `RDONLY|NOSUID|NODEV|NOEXEC` remount flags and the plain-mount `nosuid`-only case.
- `test_source_mount_flags_agree_with_the_live_mount_table` — Linux-only: the parsed `/sys` flags equal the
  flags in the live `/proc/self/mountinfo` entry.
- `test_the_sandbox_binds_every_symlink_of_the_interpreter_chain` — a uv-style
  `venv/bin/python -> …/cpython-3.12-linux-x86_64-gnu -> …/cpython-3.12.16-…` chain: `_symlink_chain` returns
  exactly `[venv python, unversioned alias]` and `_sandbox_config` puts both on the read-only list.
- The existing tests are unchanged. On Ada the whole file is **27 passed, 1 skipped** (the root-only
  uid-65534 test), against **14 failed / 9 passed / 1 skipped** on `68cdd1a` (host check capture
  `pytest_isolation_deselect.txt`); the previously hanging
  `test_elapsed_time_beyond_the_timeout…` now passes.

## Ada evidence (host: `ucrtasl`, Linux 5.15.0-151, uid 1030, 96 CPUs, `/sys` = `rw,nosuid,nodev,noexec,relatime`)

Everything was run as uid 1030 over `ssh experiment_zhixu`; no root/sudo, no waiver was given anywhere.
Commands were run from the fix worktree with the node env interpreter
(`envs/torch312/bin/python`), under `systemd-run --user --scope -p Delegate=yes` with
`AR_TEST_CGROUP_PARENT` pointing at the delegated scope (and, for the GPU probe, `-p MemoryMax=8G
-p MemorySwapMax=0`). Run root: `/home/dowling/r1_engineering/iso_fix_20261119/` (2.1 MB, 174 files,
`SHA256SUMS` = `c0e01cdca83723b6caa2ea52f0d5f88e0271e2ca0987e149f9958a81697f82f9`).

### Condition 6 — the unit's own probe passes for all three interpreters

`probe_sandbox_unit_fix.py` is the host check's probe (`isolation.worker_sandbox_available` on the unit's
`_sandbox_config`); result JSON `{ok: true, why: "ok"}`:

| interpreter | probe | alias bound in `ro` |
|---|---|---|
| `/usr/bin/python3` | **ok** (was EPERM at read-only `/sys`) | n/a |
| `envs/torch312/bin/python` | **ok** (was PID-1 execve ENOENT) | `…/uv/python/cpython-3.12-linux-x86_64-gnu` |
| `envs/jax312/bin/python` | **ok** (was PID-1 execve ENOENT) | `…/uv/python/cpython-3.12-linux-x86_64-gnu` |

Files: `probes/probe_sandbox_{py3,torch312,jax312}.json` (sha256 `411c5f67…`, `14271db3…`, `7799af00…`).

### Condition 6 — real no-waiver smoke records (`effective: true, waivers {}, exceptions []`)

`probe_smoke_fix.py` runs the unit's own isolated fixture through `WorkingCopyRunner` with
`isolation_waivers={}`, a real delegated cgroup and the requested run interpreter:

| record | interpreter in `argv` | outcome | effective | waivers | exceptions | cgroup killed/removed | record sha256 |
|---|---|---|---|---|---|---|---|
| `records/iso_fix_systempy_20261119T011351Z_2635008` | `/usr/bin/python3` | ok 1.0 | **true** | `{}` | `[]` | `cgroup.kill`, empty, removed | `b8ffd861…` |
| `records/iso_fix_torch312_20261119T011352Z_2635032` | `envs/torch312/bin/python` | ok 1.0 | **true** | `{}` | `[]` | `cgroup.kill`, empty, removed | `49af513d…` |
| `records/iso_fix_jax312_20261119T011355Z_2635191` | `envs/jax312/bin/python` | ok 1.0 | **true** | `{}` | `[]` | `cgroup.kill`, empty, removed | `53e651c2…` |

All three records: `euid 1030`, `ptrace_scope 1`, `nsdelegate true`, `log_intact true`,
`frozen_files_checked 3`, `result_channel_sha256 4ffec570…` (the honest metric `val_accuracy 1.0` +
`test_accuracy 0.4242`), `parent_traced_by null`, `parent_dumpable_at_accept false`. The torch312/jax312
record's `worker_sandbox.ro` contains the venv `bin/python` and the uv alias. Full summary:
`smoke/smoke_records_summary.json`; logs `smoke/smoke_{systempy,torch312,jax312}.log`. This is the
`effective: true` record condition 6 requires, for the node environments, with no waivers.

### Test suite on Ada

```
systemd-run --user --scope -p Delegate=yes -- bash -c '
  CG=$(cut -d: -f3 /proc/self/cgroup); export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG
  …/envs/torch312/bin/python -m pytest tests/trackg/test_trackg_isolation.py -q -p no:cacheprovider'
→ 27 passed, 1 skipped in 23.21s
```
(`pytest/isolation_full.txt`, sha256 `a6d09571…`; the three new regression tests plus the two node-library
tests also pass standalone: `regression_tests.txt`, `5 passed`.)

## Condition 7 — GPU smoke: exercised, and blocked by a driver namespace limitation

Gate and safety first: `r1/scripts/paper_a_status.py --config r1/scripts/configs/paper_a_status_ada.json`
returned `verdict: clear_finished`, `paper_a_live_waiting_for_card: false`, `paper_a_processes: []`
(`gpu/paper_a_status.json`). GPU 2 was picked after a live check (`nvidia-smi` compute-apps): index 2
`GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154`, 49,140 MiB total, **5 MiB used, 48,427 MiB free, 0 % util, no
compute app** (GPUs 0,1,3,4,5,7 carry other users' jobs and were not touched). The whole probe ran under
`systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0`, i.e. an enforced cgroup
memory cap recorded as `memory_method: external`; it used one 8-float CUDA tensor on that card, no Track G
U2/census run. GPU 2 returned to 5 MiB / 0 % after the probe; no compute app was added or removed (other users' jobs ran on their own cards throughout)
(`gpu/gpu_state_before.json`, `gpu/gpu_inventory_after.txt`, `gpu/gpu_compute_apps_after.txt`).

The tiny isolated node (`parent.py` makes the tensor, `iso.cuda_share()`; frozen worker entry — PID 1 of the
sandbox — opens it with `iso.cuda_open()`) ran sandboxed (cgroup created/killed, `worker_sandbox` present,
`shared_dev_shm: true` so `exceptions == ["shared_dev_shm"]` by the authors' design). The CUDA IPC open failed
in the worker:

```
RuntimeError: CUDA error: invalid resource handle
  at ar_isolated.py: cuda_open -> torch.UntypedStorage._new_shared_cuda(...)
```
Run record `records/iso_fix_gpu_20261119T011515Z_2643968/run_record.json` (sha256 `d448a859…`), outcome
`divergent / nonzero_exit`; log `gpu/probe_gpu_smoke.log`.

Diagnosis (all on the same idle GPU 2, same user, same tensor code; `gpu/cuda_ipc_*.log`):

| control | consumer namespace | result |
|---|---|---|
| stock `torch.multiprocessing` CUDA-tensor queue | ordinary process | **works** in the ordinary-process control; its stdout was not captured (see `gpu/cuda_ipc_matrix.log` / `ns_controls.log`) — the conclusion rests on those captured controls, not this row |
| `ar_isolated.cuda_share` → `cuda_open`, plain process | none | **works**, but only after `torch.cuda.init()`; **without it the consumer segfaults** in `_new_shared_cuda` (latent helper bug, below) |
| `unshare -U -r -f` (new user namespace only) | same PID namespace | **invalid resource handle** |
| `unshare -U -r -p -f` | new user+PID namespace, host `/proc` | CUDA context creation fails: `cudaGetDeviceCount … Error 304: OS call failed …` |
| `unshare -U -r -m -p --mount-proc -f` (the sandbox's namespace shape) | new user+mount+PID namespace, fresh `/proc` | **invalid resource handle**, also for an opener forked below PID 1 (PID 2) |

Conclusion: on this host/driver, `cudaIpcOpenMemHandle` fails whenever the consumer runs in a new **user
namespace** (the sandbox always needs one for unprivileged PID/mount namespaces; this is how you run as a
mapped root and drop capabilities), and CUDA cannot even initialize in some PID-namespace shapes. This is a
driver/CUDA limitation of the namespace architecture, **not** a mount-flag or interpreter-binding defect of the
unit — the same fix-core sandbox works for every CPU run above. Consequences: the core §5.5 statement that
the kits' GPU smoke exercises CUDA IPC across the PID namespace cannot hold on Ada; the autoresearch node's
"worker returns logits to the parent over CUDA IPC, `shared_dev_shm` exception" design must be changed
(e.g. return arrays over the existing socket/CPU buffer, or run the GPU worker without the PID-namespace
sandbox under a recorded waiver) before that node's GPU smoke can pass. A separate latent defect was also
found: `cuda_open` must initialize CUDA (`torch.cuda.init()`) before `_new_shared_cuda`, otherwise a fresh
consumer process segfaults instead of raising; it is **not** patched here (outside the A/B scope — a separate
reviewed change should decide it together with the CUDA-IPC design).

## Kit-side update required (inspected only — no kit branch modified)

`mac-trackg-iso-{ar,mlab,mlgym}-20261117` do not touch `src/` or `tests/trackg/test_trackg_isolation.py`
(byte-identical to `68cdd1a`), and every node copy of the frozen master `ar_isolated.py` is byte-identical to
the old master (`371c2032…`; new master `37d99ab0…`). `tests/trackg/port_support.py::check_isolated` asserts
each node copy equals `src/autoresearch/trackg/node_lib/ar_isolated.py` and `check_static` asserts the copies
agree across a port, so the update is:

1. merge core `5403392` into each kit branch — verified **clean in all three** in throwaway worktrees
   (automatic merge; no conflicts);
2. copy the new master byte-identically over each node copy:
   `ar`: `nodes/autoresearch_fixedtokens/ar_isolated.py` (1);
   `mlab`: `nodes/mlab_{cifar10,imdb,ogbn_arxiv}/ar_isolated.py` (3);
   `mlgym`: `third_party/mlgym/nodes/mlgym_{breakout_minatar,cifar10,fmnist,houseprice}/ar_isolated.py` (4);
3. recompute/commit each node's `frozen_pin_sha256` (only `ar_isolated.py` changes among the frozen files):

| kit | node | old pin | new pin |
|---|---|---|---|
| ar | autoresearch_fixedtokens | `b8482875…` | `b5f0ec2f…` |
| mlab | mlab_cifar10 | `b85990cb…` | `1f047ad7…` |
| mlab | mlab_imdb | `080fc88d…` | `4b1019a6…` |
| mlab | mlab_ogbn_arxiv | `a75f717d…` | `bd71fdf4…` |
| mlgym | mlgym_breakout_minatar | `d37f92ae…` | `cec562e6…` |
| mlgym | mlgym_cifar10 | `dd149c3f…` | `2d7e533b…` |
| mlgym | mlgym_fmnist | `977f666c…` | `eb60107e…` |
| mlgym | mlgym_houseprice | `4cc1f964…` | `88d359f2…` |

(full 64-hex values and the read-only verification in
`/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/harness_iso_fix_20261119/kit_analysis.json` and
`kit_update_verification.md`). Verification in the throwaway worktrees: before step 2, `port_support.check_isolated`
fails with `ar_isolated.py differs from the harness master`; after step 2 and the merge,
`pytest tests/trackg/test_port_*.py -k "test_static or test_manifest_complete or test_frozen_path_edit_refused"`
passes — ar **3 passed**, mlab **9 passed**, mlgym **12 passed** — and all eight recomputed pins match the
table. No kit commit was made, no kit branch was pushed or modified. The kit node-spec comments name the
isolation branch (not a sha), so no YAML pin needs editing; the per-node smoke must be rerun on Ada at update
time (the smoke passes `interpreter=sys.executable`, which is exactly what fix B addresses).

## Integrity of this work

No push, no force push, no deletion, no branch rewrite of any existing branch. The accepted worktrees were
not modified (`git status` clean; new sibling worktree + workspace clone only). The kit branches were read
from `origin` and exercised only in detached scratch checkouts that were removed afterwards. No TASL-7/TASL-2/
HTCondor/deepthought interaction; no Track G U2/census/GPU-kit run was started; no other user's GPU or process
was touched (only the idle GPU 2, with an 8 GiB enforced cgroup memory cap, and it returned to idle); no
root/sudo was used. On Ada all processes/scopes from these checks are gone (`pgrep` finds none; only
`init.scope` remains). The report and kit-verification notes are untracked files for the root agent to review
and commit; the code commit exists only locally on the two worktrees above. The original Mac harness checkout
was not writable from this session (workspace-only sandbox), which is why the Mac copy of the branch lives in
the session-workspace clone instead.

## Residual risks and what remains

1. **Condition 7 is blocked by CUDA IPC not crossing a user namespace on this driver/host.** The autoresearch
   node's GPU path (and the "shared_dev_shm" exception rationale) needs a design decision: CPU/socket transfer
   of logits, or a documented non-PID-namespace GPU mode with the appropriate waiver. The core §5.5 wording
   should be corrected accordingly.
2. **`cuda_open` has a latent init bug** (segfault if the consumer has not initialized CUDA); to be fixed with
   (1), not in this A/B commit.
3. **Mount-flag parsing** assumes mountinfo fields 5/6 (octal-escaped pathnames are not unescaped; spaces in a
   mount point are not handled). Not exercised by this host's paths; a possible follow-up.
4. **Recursive binds remount only the top mount** (unchanged behaviour): submounts under a `ro` path keep the
   flags they had. With the locked flags preserved this is no longer a remount failure, but a future hardening
   item if a node's read-only tree can contain writable submounts.
5. **Fix B is a general symlink-chain binding, not a sandbox of the chain**: a chain that leaves the allowed
   set through a target that is not otherwise bound would still fail (it fails closed, with ENOENT at PID 1).
6. **Kit pins change**: the census must commit the new `frozen_pin_sha256` values above; measured baseline
   times/metrics should not move (only sandbox/mount and interpreter binding changed), but each kit's per-node
   smoke must be rerun when the kit branches are updated.
7. The regression tests were run on this Ada host and (the pure ones) on macOS; the mountinfo live-table test
   self-skips outside Linux.

## Evidence index (Ada, `/home/dowling/r1_engineering/iso_fix_20261119/`; `SHA256SUMS` = `c0e01cdc…`)

- `git/commit_sha.txt` (`5403392e…`), `git/commit_show.txt`, `git/fix_68cdd1a_to_5403392.diff`, `git/status_clean.txt`.
- `pytest/isolation_full.txt` (27 passed, 1 skipped), `regression_tests.txt`.
- `probes/probe_sandbox_{py3,torch312,jax312}.json` — condition 6 probe, all `ok: true`.
- `smoke/smoke_{systempy,torch312,jax312}.log`, `smoke/smoke_records_summary.json`, and the four run
  directories under `records/` (`run_record.json` + `run.log` + `result_channel.txt` + code/work copies).
- `gpu/` — `paper_a_status.json`, `gpu_state_before.json`, `gpu_inventory_after.txt`,
  `gpu_compute_apps_after.txt`, `probe_gpu_smoke.{log,json}`, the failing GPU run record, and the controls
  `cuda_ipc_{control,matrix,ns_controls}.log`.
- `evidence_scripts/` — every probe/control script used (`probe_sandbox_unit_fix.py`, `probe_smoke_fix.py`,
  `probe_gpu_smoke_fix.py`, `cuda_ipc_*.py`).
- `SHA256SUMS` — sha256 of all 174 evidence files (plus itself hashed above).
