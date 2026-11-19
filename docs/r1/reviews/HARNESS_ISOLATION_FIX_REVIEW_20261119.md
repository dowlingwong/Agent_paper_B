# R1-HARNESS-ISOLATION fix review — core `5403392` (19 November 2026)

**Reviewer:** independent reviewer (`iso-reviewer`), delegated by the coordinator after the Ada host-check STOP.
Read-only: no code edit, no commit, no push, no GPU/U2/census run, no deletion, no HTCondor/deepthought. The
only writes were this file and temporary directories under `/tmp` on Ada for verification runs (removed
afterwards); no evidence file was modified.

**Verdict: ACCEPTED.** The two fixes are correct, minimal and fail-closed, do not relax the sandbox, and
condition 6 is independently reproduced on Ada for all three interpreters with no waivers. Condition 7 is
**BLOCKED by a host/driver namespace limitation, not by fixes A/B**, and the report says so; it is not a reason
to reject this unit. Acceptance carries record/process conditions C1–C4 below (no code changes required).
Findings are MINOR only; there are no BLOCKING or MAJOR findings.

---

## Authority and scope

- Published paper main `de3de54fd22dcdd86215be0924307e36a64ed08b` (`git -C .claude-worktrees/ops-tasl-20261116
  rev-parse origin/main`), carrying `docs/r1/reports/HARNESS_ISOLATION_20261117.md` §3 (host conditions and
  waivers, conditions 6/7) and §5.5 (CUDA IPC under the PID namespace, item 5), and
  `docs/r1/reviews/HARNESS_ISOLATION_REVIEW_20261117.md` round 8 **ACCEPTED**, core
  `68cdd1ae2d46d2494ed6fbe69d7dd5693b5c643e` (verified in the file at `origin/main`).
- PLAN row **R1-HARNESS-ISOLATION** (no T1 label run, no RL training before an independently reviewed isolation
  unit).
- Host-check STOP report `docs/r1/reports/trackg_g0_20261117/HARNESS_ISOLATION_HOST_CHECK_20261119.md`, sha256
  `6a7005098659e56c103d2f74e76f65979cbf39a1b46e24c3e3e168e38cda97d7`, and its captures (75/75 entries verify
  with `sha256sum -c SHA256SUMS` when run from the captures directory; `captures/pytest_isolation_deselect.txt`
  indeed records `14 failed, 9 passed, 1 skipped, 1 deselected` for `68cdd1a` on Ada).
- Fix unit reviewed: branch `mac-harness-isolation-fix-20261119`, base `68cdd1a`, tip
  `5403392e94cb59d732f45d6702fc857531ad8fd5` (one commit after the base), in Ada worktree
  `/home/dowling/r1_trackg_20261117/harness_iso_fix_20261119` and Mac clone
  `.claude-worktrees/harness_iso_fix_20261119/repo` (same tree; both clean).
- Fix report `docs/r1/reports/trackg_g0_20261117/HARNESS_ISOLATION_FIX_20261119.md`, sha256
  `a3a81293632ff1067b8136d09682c50d66de5c0b044994161a9bff29200ebb4f`.
- Ada evidence `/home/dowling/r1_engineering/iso_fix_20261119/`, `SHA256SUMS` sha256
  `c0e01cdca83723b6caa2ea52f0d5f88e0271e2ca0987e149f9958a81697f82f9`, 174 listed files, 2.1 MB (175 files
  including `SHA256SUMS`).

## Checks, commands and results

### 1. Branch, scope and integrity

| Check | Result |
|---|---|
| `git rev-parse 68cdd1a` / `5403392` | `68cdd1ae2d46…` / `5403392e94cb…`; single commit on the branch after the base; parent of `5403392` is `68cdd1a` |
| `git diff --numstat 68cdd1a..5403392` | exactly 3 files: `ar_isolated.py` **47/3**, `runner.py` 34/0, `tests/trackg/test_trackg_isolation.py` 73/0 → **+154/−3** total |
| `git show --name-status 5403392` | `M` only for those three files; no other change, no deletion |
| Fix diff vs evidence `git/fix_68cdd1a_to_5403392.diff` | `diff` byte-identical; sha256 `0e27a6c38a36…` as reported |
| Pushes | no `origin/mac-harness-isolation-fix-20261119` in the Mac clone or on Ada; the branch exists only locally on Ada and as the `ada/…` fetch ref in the workspace clone |
| Accepted worktrees | `harness_iso_core` = `68cdd1a`, `harness_iso_{ar,mlab,mlgym}` = `5d3dccc / 0aae2f6 / 061d638`, all `git status` clean; kit branches unchanged |
| Ada fix worktree | HEAD `5403392`, clean before and after the review runs |

Diff-reading confirms the change is confined to the mount-flag derivation / remount call sites, the interpreter
allow-list construction, and three new tests. Nothing touches `effective`/record construction, the result
channel, log verification, frozen-file hashing or the cgroup code, so the frozen/log/result/cgroup guarantees
are not weakened (existing tests for them also still pass unchanged).

### 2. Fix A — mount-flag derivation (code review)

`src/autoresearch/trackg/node_lib/ar_isolated.py`

- `_mount_flags_from_mountinfo` (lines 180–199) parses field 5 (mount point) and field 6 (per-mount options) of
  the pre-separator part of each `mountinfo` line, keeps the **longest matching mount point**, and maps only
  `nosuid/nodev/noexec` (correct `MS_*` values at line 155/177). Prefix matching uses `point.rstrip("/") + "/"`,
  so `/sysfoo` cannot match `/sys`; `/` is handled.
- `_source_mount_flags` (202–209) returns `0` on `OSError`, i.e. a degraded host degrades to the previous
  behaviour, which **refuses** the run on a host with locked flags (the observed Ada EPERM), so it is
  fail-closed rather than fail-open.
- `_bind_remount_flags` (212–215) is `BIND|REMOUNT|NOSUID|locked|(RDONLY if requested)`. This is the kernel's
  requirement for a bind mount made in a user namespace: every `MNT_LOCK_*` flag of the source must be
  repeated, and adding `nosuid`/`nodev`/`noexec` where the source lacks them is permitted hardening.
- Call sites: `bind()` uses it at line 276 (replacing the fixed `BIND|REMOUNT|NOSUID|RDONLY`), and the final
  read-only root remount derives from `/` at lines 335–338 (previously it hard-coded `RDONLY|NOSUID`, silently
  clearing the root tmpfs's `nodev`). `/sys` without `nosuid,nodev,noexec` on Ada would EPERM; with the derived
  flags it matches the flag matrix in the host-check capture that succeeded.
- Security direction: the only flag changes are **additions** (`nosuid` on writable binds, source `nodev`/
  `noexec`, `nodev` on the root remount) or exact preservation. No path is un-remounted, no flag is cleared,
  and the entry/`ro_flat` allow-list logic is untouched. Recursive binds still remount only the top mount
  (report residual risk 4, unchanged behaviour, fail-closed if a locked flag were dropped).

### 3. Fix B — interpreter symlink-chain binding (code review)

`src/autoresearch/trackg/runner.py`

- `_symlink_chain` (578–602) walks the path component by component, appends the **outermost** symlink first,
  resolves absolute and relative targets, joins the not-yet-consumed components, normalises, and is bounded at
  40 iterations (a loop cannot spin; the kernel would refuse it anyway). It only ever returns **symlink paths**
  on the way to the interpreter; it never returns a target directory, so binding a returned link only recreates
  a symlink inside the sandbox (no host content is mounted, no new directory tree is exposed).
- `_sandbox_config` (422–428) adds the chain for the queried `sys.executable` (`interp[1]`) and for an absolute
  `interpreter` argument, **before** the existing home/runs-root `broad` safety check (429–434), so the new
  entries are subject to the same rejection rule. It relies on the existing realpath/`sys.prefix`/
  `sys.base_prefix`/`sys.path` entries for the content, and the sandbox's `bind()` recreates the links.
- Fail-closed: if a chain target is not otherwise bound, PID 1's `execve` gets ENOENT and the run is refused
  (report residual risk 5). No path inside the sandbox can escape: symlink targets resolve inside the new root
  only.
- A uv venv produces exactly the intended chain: `envs/torch312/bin/python -> …/cpython-3.12-linux-x86_64-gnu
  -> …/cpython-3.12.16-…/bin/python3.12`; the alias directory is added as a symlink and the versioned
  installation is bound through `sys.executable` realpath / `sys.base_prefix`. Confirmed live in the Ada probe
  JSON and in the reproduced smoke.

### 4. Tests (Ada, in a delegated cgroup, `-p no:cacheprovider`, no bytecode writes)

Commands run from `/home/dowling/r1_trackg_20261117/harness_iso_fix_20261119`:

```
systemd-run --user --scope -p Delegate=yes -- bash -c '
  CG=$(cut -d: -f3 /proc/self/cgroup); export AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG
  …/envs/torch312/bin/python -m pytest tests/trackg/test_trackg_isolation.py -q -p no:cacheprovider'
```

- Full file: **27 passed, 1 skipped in 22.41 s** (independently repeated: 27 passed, 1 skipped in 22.75 s). The
  one skip is the pre-existing root-only uid-65534 test (`test_trackg_isolation.py:506`, reason
  "needs root to drop to uid 65534 and delegate a cgroup"); the new live-`/proc` test (line 428) **runs** on
  Ada. Matches the report's `pytest/isolation_full.txt` (sha256 `a6d09571…`).
- The three new tests pass and are meaningful: `test_bind_remount_keeps_the_locked_mount_flags_of_the_source_mount`
  (399) checks exact remount flags, longest-match (`/sys/fs/cgroup` submount) and the plain-mount `nosuid` case;
  `test_source_mount_flags_agree_with_the_live_mount_table` (429) compares the parser with an independent parse
  of the live `/sys` entry; `test_the_sandbox_binds_every_symlink_of_the_interpreter_chain` (443) builds a
  uv-style relative-symlink chain and asserts both the chain and its presence in `_sandbox_config()["ro"]`. All
  three fail on `68cdd1a` (the helpers do not exist), so they are genuine regression tests.
- No test was weakened or skipped: the diff adds 73 lines and removes none; old test names are a strict subset
  of the current names (25 → 28 tests); the new `/proc` skip is the only new conditional and is justified.
- The report's "3 new + 2 node-library tests standalone, 5 passed" reproduces exactly (`5 passed, 23
  deselected`).
- macOS (this reviewer, workspace clone, harness venv): `2 passed, 1 skipped` for the three new tests; the
  skipped one is the Linux-`/proc` test, matching report residual risk 7.

### 5. Ada evidence and condition 6

`SHA256SUMS` verifies (174/174, `sha256sum -c` rc 0 from the evidence root); hashes in the report match:
`pytest/isolation_full.txt` `a6d09571…`, `probes/probe_sandbox_{py3,torch312,jax312}.json`
`411c5f67…/14271db3…/7799af00…`, records `b8ffd861…/49af513d…/53e651c2…`, GPU record `d448a859…`.

- **Smoke records (report §Condition 6):** the three `records/iso_fix_{systempy,torch312,jax312}_…`
  `run_record.json` files each show `outcome {kind: ok, value: 1.0}`, `effective: true`, `waivers: {}`,
  `exceptions: []`, `euid 1030`, `ptrace_scope 1`, `nsdelegate true`, `log_intact true`,
  `frozen_files_checked 3`, `result_channel_sha256 4ffec570…` (result text `val_accuracy: 1.0000` /
  `test_accuracy: 0.4242`), a real delegated `cgroup.kill` (`empty_after: true`) with the cgroup removed, and
  `parent_traced_by: null` / `parent_dumpable_at_accept: false`. `argv` names `/usr/bin/python3`,
  `envs/torch312/bin/python`, `envs/jax312/bin/python`. The torch312/jax312 `worker_sandbox.ro` contains the
  venv `bin/python` **and** the uv alias, and `smoke/*/work/ar_isolated.py` is byte-identical to the new master
  (`37d99ab0…`), so the records were produced by the fix, not the old unit.
- **Independent reproduction (this review).** I re-ran the unit's own probe
  `isolation.worker_sandbox_available(runner._sandbox_config(...))` in fresh `/tmp` directories: **all three
  `ok: true`** (`/usr/bin/python3`; `envs/torch312` and `envs/jax312` with the uv alias in `ro`). I also re-ran
  the no-waiver fixture smoke for all three interpreters under a fresh delegated scope: all three produced
  `effective: true`, `waivers {}`, `exceptions []`, `outcome ok 1.0`, `sandboxed true`, `cgroup.kill`
  empty/removed, `log_intact true`, and the same `result_channel_sha256 4ffec570…`. **Condition 6 is PASS**
  independently of the submitted captures.
- Host facts re-checked live: `ucrtasl`, Linux `5.15.0-151-generic`, uid 1030, 96 CPUs, `/sys` =
  `rw,nosuid,nodev,noexec,relatime`; no leftover scopes or run processes (only `init.scope`). The three
  interpreter versions are 3.10.12 / 3.12.16 / 3.12.16 as claimed.

### 6. Condition 7 — CUDA IPC across the worker namespace (assessment)

The GPU smoke's run record is `divergent / nonzero_exit`, `effective: false`, `exceptions:
["shared_dev_shm"]`, `shared_dev_shm: true`, `worker_sandbox` present, cgroup killed/removed, and the worker
error is `RuntimeError: CUDA error: invalid resource handle` at `ar_isolated.cuda_open` (`_new_shared_cuda`).
The report states this as **BLOCKED, exercised, not a defect of fixes A/B**, and gives the consequence for
autoresearch. I independently assess the controls as convincing:

- plain consumer, same torch env, same producer tensor: `cuda_open` **works** after `torch.cuda.init()`
  (`gpu/cuda_ipc_matrix.log`, values `0.0…10.5`, `values_ok: true`);
- plain consumer without CUDA init: consumer **segfaults** in `_new_shared_cuda` — the `cuda_open` latent init
  bug is real and correctly described as out of the A/B scope;
- `unshare -U -r -f` (user namespace only, **same** PID namespace): **invalid resource handle** — so the user
  namespace alone breaks it, before the sandbox's mount/PID/capability specifics;
- `unshare -U -r -p -f`: CUDA context creation fails (error 304 / "OS call failed") — no IPC even possible;
- `unshare -U -r -m -p --mount-proc -f` (the sandbox shape): invalid resource handle, also for an opener forked
  below PID 1.
The plain-process success and the user-namespace-only failure reproduce without any of the A/B code, so
attributing the block to the driver/CUDA namespace architecture (driver 545.23.08 confirmed live;
torch 2.6.0+cu124 in the records/determinism shim) rather than to the mount-flag or interpreter-binding changes
is correct. The report does **not** claim condition 7 pass; it records the consequence (autoresearch GPU path
must move arrays over the socket/CPU buffer or use a documented non-PID-namespace GPU mode with a waiver) and
the latent `cuda_open` bug. That is the required disclosure. No fix is required for condition 7 as a platform
limitation, but the consequence is a hard pre-condition for deploying the autoresearch node (condition C3).

### 7. Kit-side update plan

Independently verified against the code and the three kit branches (`origin/mac-trackg-iso-{ar,mlab,mlgym}-20261117`
at `5d3dccc / 0aae2f6 / 061d638`):

- kits' `src/` and `tests/trackg/test_trackg_isolation.py` are byte-identical to `68cdd1a` (`git diff … -- src
  tests/trackg/test_trackg_isolation.py` empty) → `git merge 5403392` is content-clean; `git merge-tree
  --write-tree 5403392 <kit tip>` returns rc 0 for all three.
- every node copy equals the old master `371c2032…` (all 8 verified) and the new master is `37d99ab0…`;
  `tests/trackg/port_support.py::check_isolated` asserts exactly that byte equality, so the "copy master over
  the 8 node copies" step is the right one.
- I recomputed the frozen pin from each node root (old) and from a copy with **only** `ar_isolated.py` replaced
  by the new master, using the kit's own spec and `frozen_file_hashes`: **all 8 old and new pins match the
  report's table exactly**, and `changed == ["ar_isolated.py"]` for every node (so "only `ar_isolated.py`
  changes among the frozen files" is right).
- the node-spec comments name the isolation branch, not a sha, so no YAML pin edit is needed (checked ar/mlab/
  mlgym specs).
The plan (merge core, copy master, recompute/commit pins, rerun per-node smoke) therefore matches the code. The
specific "check_static tests 3/9/12 passed" counts in the supplementary `kit_update_verification.md` were not
reproduced by this review (they are a secondary note; the underlying facts above were verified).

### 8. Report accuracy cross-check

Every evidence path/hash/claim in `HARNESS_ISOLATION_FIX_20261119.md` was checked against the worktree and the
captures. Verified: commit sha/base/branch, report and evidence hashes, branch/cleanliness table, probe hashes,
record hashes and all record fields, test counts, `regression_tests.txt`, `SHA256SUMS`/file count/size, the GPU
gate/co-tenancy facts, `memory_method: external`, driver/torch versions, kit tips/copies/pins, and the
"nothing pushed / accepted worktrees untouched" statements. Two inaccuracies and one under-specified residual
risk remain (findings below); none affects the code verdict.

## Findings

### BLOCKING

None.

### MAJOR

None.

### MINOR

- **R-1 — per-file diff arithmetic wrong in the report.** `HARNESS_ISOLATION_FIX_20261119.md:45` says
  `ar_isolated.py` `+50/−2`; `git diff --numstat 68cdd1a..5403392` is **47 insertions / 3 deletions**
  (`runner.py` 34/0, tests 73/0). The total `+154/−3` at line 44 is correct; only the per-file split is wrong
  (the 50 is the combined changed-line column of `git show --stat`). No code impact; correct the record.
- **R-2 — one condition-7 control row and one evidence path are unsupported.** `HARNESS_ISOLATION_FIX_20261119.md:173`
  claims the stock `torch.multiprocessing` CUDA-tensor queue control "works (sum 42.0)", and line 272 lists
  `gpu/cuda_ipc_{diag,control,matrix,ns_controls}.log`. The evidence directory has
  `gpu/cuda_ipc_{control,matrix,ns_controls}.log` but **no `cuda_ipc_diag.log`**; `grep -rn 'STOCK_IPC_OK'` over
  the whole evidence tree finds only the script `evidence_scripts/cuda_ipc_diag.py`, never its output. The
  condition-7 conclusion is still fully supported by `gpu/cuda_ipc_matrix.log` (plain/init ok; userns/PID-ns
  failures) and `gpu/cuda_ipc_ns_controls.log`, so this does not change the verdict, but the report must either
  capture the diag output (stock queue, expected sum 42.0) or drop the parenthesised number and the
  `cuda_ipc_diag.log` from the evidence index (cite the matrix plain/init row instead).
- **R-3 — the new tests do not cover the fix's call sites.** The new tests exercise
  `_mount_flags_from_mountinfo`/`_bind_remount_flags` in isolation (`tests/trackg/test_trackg_isolation.py:399`),
  the live `/sys` parse (`:429`) and the symlink chain/`ro` insertion (`:443`), but none asserts that
  `_sandbox_preexec.bind()` actually uses `_bind_remount_flags(_source_mount_flags(src))`
  (`ar_isolated.py:276`) or that the root remount uses the derived flags (`ar_isolated.py:335-338`). A later
  edit that reverted only the call sites while keeping the helpers would leave these tests green on non-Ada
  hosts; the Ada host check / per-node smoke remains the end-to-end catch. Recommend a call-site assertion (or
  an explicit note that the Ada re-run is the regression) before this is relied on as the only gate.
- **R-4 — residual-risk note misses stacked mounts at one mount point.** `ar_isolated.py:195` keeps the first
  entry with the longest mount point (`len(point) > len(best)`); for two mounts stacked at the same path the
  lower entry wins although `realpath`/bind resolve the top one. The flags are then wrong, which fails closed
  (EPERM if a locked flag is dropped) and cannot relax isolation, but the report's residual risk 3
  (`HARNESS_ISOLATION_FIX_20261119.md:250`) lists only octal escaping/spaces. Add this case (or prefer the
  last/upper entry) as a follow-up note.

## Conditions

- **C1 (record, before committing the report).** Apply R-1 and R-2 (correct the per-file split; make every
  evidence path in the index exist — capture the `cuda_ipc_diag.py` output or remove the claim/path), then
  re-hash the report and commit it. R-3/R-4 may be handled as follow-up notes or a small test addition; they do
  not block acceptance of the code.
- **C2 (kit update).** Proceed with the verified plan — merge core `5403392` into `mac-trackg-iso-{ar,mlab,mlgym}-20261117`,
  copy the new master `37d99ab0…` over the 8 node copies, commit the recomputed `frozen_pin_sha256` values in
  the census — and rerun each per-node smoke on Ada with the fixed core. The branch stays local/unpushed until
  that is done; no kit YAML pin change is needed.
- **C3 (condition 7 / autoresearch).** The host-gate record must keep condition 7 as **BLOCKED / NOT PASS**
  (the report does), and the §3 gate must not be reported as fully passed. No autoresearch GPU run (and no GPU
  node that needs CUDA IPC across the namespace) may be started until the logits transfer design decision is
  recorded (socket/CPU buffer, or a documented non-PID-namespace GPU mode with its waiver) and `cuda_open`'s
  missing `torch.cuda.init()` is fixed in that same reviewed change; without init a fresh consumer segfaults,
  and with a user namespace the IPC open fails on this host/driver.
- **C4 (spec text).** Correct `docs/r1/reports/HARNESS_ISOLATION_20261117.md` §5.5 (and §3 item 7) on the paper
  repo to record that CUDA IPC does not cross a user namespace on this host/driver, so the host-condition text
  no longer implies the GPU smoke can exercise §5.5 on Ada unchanged. The fix report leaves this as "should be
  corrected"; it should be an owned follow-up rather than only a residual risk.

## Residual risks confirmed

The report's residual risks are the right ones and are consistent with the code and evidence: mountinfo
escaping/spaces not unescaped (R-4 above adds stacked mounts), recursive binds remount only the top mount,
the symlink-chain fix fails closed if a target is not otherwise bound, condition 7 blocked by the namespace
architecture, `cuda_open` init bug open, kit pins change, and the mountinfo live test self-skips off Linux.
No additional security relaxation was found: every flag change adds or preserves `nosuid/nodev/noexec`, the
allow-list safety check still applies to the added entries, and nothing outside the sandbox's read-only
allow-list is mounted.

## Verdict

**ACCEPTED** for the fix unit `5403392e94cb59d732f45d6702fc857531ad8fd5` (fixes A and B), with MINOR findings
R-1/R-2 to be corrected in the report before it is committed and conditions C1–C4. Condition 6 is PASS and was
independently reproduced on Ada; condition 7 remains BLOCKED by a platform limitation, correctly disclosed,
and is a hard pre-condition for the autoresearch GPU path, not a defect of this unit.

---

### Reviewer's command record (all on 19 Nov 2026, Europe/Berlin)

- `git -C .claude-worktrees/harness_iso_fix_20261119/repo diff|numstat|show 68cdd1a..5403392`; `git rev-list
  --count`; `git branch -r --contains`; `git merge-tree --write-tree` for the three kits.
- Ada (`ssh -o BatchMode=yes experiment_zhixu …`): fix worktree `rev-parse`/`status`; full
  `pytest tests/trackg/test_trackg_isolation.py` twice in a delegated scope (27 passed, 1 skipped); the
  regression subset (5 passed); unit probe re-run for `/usr/bin/python3`, `envs/torch312`, `envs/jax312` (all
  `ok: true`); no-waiver fixture smoke re-run for all three (`effective: true`, `waivers {}`, `exceptions []`,
  `ok 1.0`, cgroup.kill, result sha `4ffec570…`); `sha256sum -c SHA256SUMS` (174/174); run-record field dump;
  all 8 kit old/new pin recomputations; live `/sys`, `nproc`, uid, kernel, `nvidia-smi` driver version; process
  and scope leftovers check.
- Mac: `pytest tests/trackg/test_trackg_isolation.py -k …` in the workspace clone (`2 passed, 1 skipped`);
  fix/stop report and captures `sha256sum`; reads of the spec, the round-8 review and the host-check captures.
