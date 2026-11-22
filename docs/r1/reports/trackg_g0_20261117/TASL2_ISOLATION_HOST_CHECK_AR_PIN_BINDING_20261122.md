# TASL-2 harness-isolation host-check binding at harness pin `2d09f9a9` for the autoresearch G.1b spec (22 November 2026)

**Status: PASS — binding record for `R1-T1-HOST-TASL` at the autoresearch G.1b harness pin.** It is the launch
record the AR spec `sweep2/t1_tasl/g1b_tasl_ar_spec.json` names at `hosts.TASL-2.isolation_host_check.record`.
ENGINEERING_ONLY; AI-assisted (DeepSeek Harness agent `ar-pin-hostcheck-r2`, delegated by the lead). The lead
commits it to published `main` and fills its sha256 into the spec (written uncommitted on the Mac ops worktree
`ops-tasl-20261116`, baseline `3c3f822a` merged in ops; no push).

host_check_host: TASL-2
host_check_harness_commit: 2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe
host_check_items: 1-7 PASS
host_check_verdict: PASS

## What this binds

The seven host conditions of `docs/r1/reports/HARNESS_ISOLATION_20261117.md` §3 were re-checked **at the
autoresearch G.1b harness pin** on TASL-2 in one orchestrated session (recorded run
2026-11-22T14:56:17Z–14:56:45Z UTC; unprivileged host uid/euid 1008, no sudo), and all seven passed with no
waiver. The same session covers procedure §1–§4: the second harness checkout at the pin, the node pins, the
`ar-cond7a` environment (Python 3.12.15, frozen shape, read-only) and the T1 data layout of
`autoresearch_fixedtokens`. It is **the rerun after the authorised R1-G1B-AR-PY option-A fix** of `ar-cond7a`
(see "Why this is a rerun" below): the earlier 22 Nov attempt stopped at procedure §3.3 because the venv
resolved to Python 3.12.16.

- Host: `TASL-2` (zhixu portal), Ubuntu 22.04.5 LTS, kernel `6.8.0-149-generic`, cgroup v2
  (`nsdelegate,memory_recursiveprot`), NVIDIA driver `535.309.01`; euid 1008; `/` **352.5 GiB free** (≥ 20 GiB
  stop threshold).
- Harness checkout: `/home/dowling/r1_tracks/t1_tasl/harness_ar`, detached at
  `2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe` (branch `mac-trackg-t1-ar-20261121`; GitHub `ls-remote` resolves
  to the pin), `c025f89aeafc2199bf3487b4bcaa16678273c702` an ancestor (rc 0),
  `git status --porcelain --untracked-files=all` **empty** before §4 and, after §4, its only untracked entry is
  `nodes/autoresearch_fixedtokens/data` (absolute symlink to the data root). No commit, no stash.
- Seven-node checkout: `/home/dowling/r1_tracks/t1_tasl/harness` still at
  `c025f89aeafc2199bf3487b4bcaa16678273c702`, detached, tracked tree clean and unchanged before/after; it carries
  four **pre-existing untracked `data` symlinks** from the 21 Nov G.1b runs (`mlab_imdb`, `mlab_ogbn_arxiv`,
  `mlgym_fmnist`, `mlgym_houseprice`), not created or changed by this run (disclosed, allowed as "tracked-clean /
  HEAD-unchanged").
- GPU: `GPU-4d623e76-7587-ee15-a633-46f60d220d94`, `nvidia-smi --query-compute-apps` empty before and after
  (353 MiB desktop reservation, 0 %); the documented exclusive lease `~/r1_locks/gpu0.lock` was free before and
  after.
- Run root on TASL-2: `/home/dowling/r1_engineering/tasl2_ar_pin_hostcheck_20261122/rerun_after_ar_py_optionA_20261122/`
  (`scripts/`, `captures/`, `logs/`, `records/`; orchestration `bash scripts/run_all.sh`, verbatim in the capture
  set's `scripts/run_all.sh`).

### Why this is a rerun — the authorised R1-G1B-AR-PY option-A fix of `ar-cond7a`

The earlier 22 Nov attempt of this procedure stopped at §3.3 (STOP report
`docs/r1/reports/g1b_ar_20261122/TASL2_ISOLATION_HOST_CHECK_AR_PIN_20261122_STOP.md` and its review): the venv
`/home/dowling/r1_trackp/venvs/ar-cond7a` is a byte copy of `trackp-gpu` whose `bin/python`, `bin/python3` and
`bin/python3.12` resolved through uv's **unversioned** `cpython-3.12` alias; that alias had been moved to
`cpython-3.12.16` on 21 Nov, so the venv ran **Python 3.12.16** instead of the spec's `envs.ar-cond7a.python =
3.12.15`. The lead's **authorised option-A fix** re-pointed the three venv symlinks at the versioned uv CPython
`/home/dowling/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu/bin/python3.12` at
**2026-11-22T14:41:49Z**. Evidence root on TASL-2:
`/home/dowling/r1_engineering/tasl2_ar_pin_py315_repoint_20261122/` (`captures/symlinks_before.txt`,
`captures/symlinks_after.txt`; `SHA256SUMS` sha256
`58d287273c3f6047344d9ad23fd3319995b7789093d65a76c03c4c2c3f6580aa`, `sha256sum -c` rc 0).
The lead's evidence was fetched and verified in the recorded session (`lead_repoint_evidence/`), and the result was
**independently re-derived read-only** in the same session and again at the end:

| Item | Value (before = after) |
|---|---|
| `bin/python`, `bin/python3`, `bin/python3.12` targets | `…/cpython-3.12.15-linux-x86_64-gnu/bin/python3.12` (all three direct symlinks) |
| resolved interpreter | `/home/dowling/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu/bin/python3.12` |
| interpreter sha256 / size | `0a97d28d3635c7dfd143de6d00b09c0cb382249c020b28ee33fb4002db1efb9c` / 31,027,176 B |
| `python -V` | `Python 3.12.15` |
| `uv pip freeze` (raw) | 122 lines, sha256 `11def6ade60a81eeb43856652048d74a43fd588a7c7c7ccbf98af817cb82fef1` (byte-identical to `sweep2/g1b/env/ar-cond7a.freeze.txt`) |
| `pyvenv.cfg` sha256 | `2f05da0a6007dae90f35f8fb2284f859ac6ccae7b92dd3c58d5652e68338cf42` |
| torch | `2.6.0+cu124`, CUDA `12.4`, `cuda_available=True` |

The venv was **read-only** in this check: nothing was installed, upgraded or copied into it, and the before/after
snapshot is identical in every recorded field (`venv_unchanged.json`: `unchanged=true`).

## §1–§4 at the pin — PASS table

| § | Item | Result | Key evidence (captures) |
|---|---|---|---|
| 1 | Second harness checkout `/home/dowling/r1_tracks/t1_tasl/harness_ar` | **PASS** | separate clone from GitHub made by the earlier 22 Nov attempt of this same procedure, **re-verified afresh**: `HEAD=2d09f9a9…` (matches pin), detached (`symbolic-ref` rc 1), `git status --porcelain --untracked-files=all` empty, `merge-base --is-ancestor c025f89a HEAD` rc 0, `origin/mac-trackg-t1-ar-20261121=2d09f9a9…`, GitHub `ls-remote` exactly the pin, one worktree, no stash (`harness_ar_pin.txt`, `step1_git_ls_remote.txt`) |
| 1 | Seven-node checkout unchanged | **PASS** | `HEAD=c025f89a…` before and after, detached, no stash, tracked tree clean (only the four pre-existing untracked `data` links listed above; not touched) (`seven_node_before.txt`, `seven_node_after_step1.txt`, `seven_node_after.txt`) |
| 2 | Node pins at the pin (ar-cond7a, `PYTHONPATH=harness_ar/src`) | **PASS** | all four exact, 20 frozen entries before the data link: spec file `5bdce00ac51718de8547ce2d065c0e5ae83f26406ff9404f01ac42b0e2b866e7`; spec `raw_sha256` `5c1bdf3d84c0721818adc239186ac30ffa2c2bb3b6b373e56b236e47cbd61192`; committed pin `147f0d35d40df54b5902260f07bf25043f515dbc0066991ab05e3b8c64eda0fc`; `representative_edits/manifest.json` `55f2666a3d09aaedb8b8552aef00f8a9c27b84f1bd7df24d886904dad581e5c7` (`node_pins.json/.txt`) |
| 3 | The environment `ar-cond7a` (spec interpreter, AR-ENV option A) | **PASS** | `uv 0.13.6 (x86_64-unknown-linux-gnu)`; `uv pip freeze` 122 lines, raw sha256 `11def6ade60a81eeb43856652048d74a43fd588a7c7c7ccbf98af817cb82fef1`, **byte-identical** to the committed freeze (raw and sorted); Python 3.12.15; torch 2.6.0+cu124 / CUDA 12.4; read-only; interpreter sha256/size and symlink targets identical before/after (`env_uv.log`, `env_freeze_uv.txt`, `env_check.json/.txt`, `venv_evidence_before/after`, `venv_unchanged.json`) |
| 4 | Data under the T1 layout, staged once | **PASS** | `/home/dowling/r1_tracks/t1_tasl/data/autoresearch_fixedtokens`: `data_manifest.json` sha256 `ab7186d2b6fba9037283a59de9f071c317a98e4f43806368663d6d9e398faf51`, **13 files**, HF revision `915333b4f8b8684f39aeaafea600fea6f43fb703` (prefix `915333b`), 963 MiB, read-only (`data_dir` mode 500, manifest 400); node link is the absolute symlink to that directory; the checkout's only untracked entry is `nodes/autoresearch_fixedtokens/data`; `prepare_data.py` rc 0 with the node's env (`AR_TRACKG_DATA_ROOT`, `HF_HOME`), `AR_DATA manifest_sha256=ab7186d2… files=13` (`logs/step4_prepare_data.log`, `step4_data_check.json/.txt`) |

The dataset itself was downloaded and its tokenizer trained during **attempt 2** of this same procedure on the
same run root (2026-11-22T14:53:03Z–14:54:52Z: 11 shards, tokenizer trained in 19.0 s, manifest written last,
`ab7186d2…`); the recorded attempt re-ran `prepare_data.py` (its documented idempotent re-check/re-link path,
14:56:22Z) and re-verified the manifest and link. `prepare_data.py` never reuses another `--out`.

## §3 conditions at the pin — PASS table (C1–C7)

| # | Condition (`HARNESS_ISOLATION_20261117.md` §3) | Result | Key evidence (captures) |
|---|---|---|---|
| C1 | Unprivileged user, mount, PID, network and cgroup namespaces are usable by the run uid | **PASS** | `unshare(CLONE_NEWUSER\|CLONE_NEWNS\|CLONE_NEWPID\|CLONE_NEWNET\|CLONE_NEWCGROUP)` through the unit's own launcher: rc 0 (flags `0x72020000`) for the **ar-cond7a** interpreter (3.12.15) and for `/usr/bin/python3` (3.10.12); uid 1008 → 0 in the new user namespace; real tmpfs mount rc 0 and writable; child is **PID 1** of the new PID namespace (`c1_userns_ar_cond7a.json`, `c1_userns_syspy.json`) |
| C2 | Yama `ptrace_scope` ≥ 1 | **PASS** | `kernel.yama.ptrace_scope=1`, `yama` in LSM `lockdown,capability,landlock,yama,apparmor`; parent→child attach ok, detach ok, unrelated same-uid sibling attach **EPERM** (errno 1) (`c2_ptrace.json`) |
| C3 | A delegated cgroup v2 subtree the uid can write, with `cgroup.kill` (census scope 8G / swap 0) | **PASS** | `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0`: `memory.max=8589934592`, `memory.swap.max=0`, `cgroup.kill` exists, `cgroup.procs` writable, owner uid 1008, `nsdelegate=True`; the pin's `isolation.RunCgroup` create → join pid → `cgroup.kill` → empty → removed (child rc −9) (`c3_cgroup.json/.txt`) |
| C4 | Not root; the interpreter's `sys.path` holds no home dir, runs tree or ancestor (hard `RunnerError`, no waiver) | **PASS** | host euid 1008; `WorkingCopyRunner._sandbox_config` passes for **ar-cond7a** (3.12.15) and `/usr/bin/python3` (3.10.12): `broad_entries=[]`, `sandbox_config_ok=true`, `isolation.worker_sandbox_available=true` for both (`c4_interp.json/.txt`) |
| C5 | A real sandboxed smoke whose record shows `effective: true` | **PASS** | record `effective: true`, `waivers {}`, `exceptions []`, euid 1008, `ptrace_scope 1`, `nsdelegate true`, `log_intact true`, `parent_traced_by null`, `parent_dumpable_at_accept false`, cgroup removed; outcome ok 1.0; metric `val_accuracy: 1.0000` (`c5_smoke.json`; `records/ar_pin_smoke/`) |
| C6 | A GPU smoke with the sandbox on (not §3 item 7, CUDA IPC) | **PASS** | GPU by full UUID `GPU-4d623e76-7587-ee15-a633-46f60d220d94` (only GPU; `CUDA_VISIBLE_DEVICES` set to the full UUID); the sandboxed worker (PID 1 in new user/mount/PID namespaces) allocated and synchronised a CUDA tensor by the **ar-cond7a** interpreter: `tensor_sum 4096.0` (correct), matmul `16.0` (correct), 33,556,992 B allocated, torch 2.6.0+cu124 / CUDA 12.4, no CUDA error; `effective: true`, `waivers {}`, `exceptions []`, cgroup removed, metric written (`c6_gpu_smoke.json`; `records/ar_pin_gpu_smoke/`). Exclusive `flock ~/r1_locks/gpu0.lock` acquired 14:56:26Z, released 14:56:28Z, **no lease-log write**; no compute process before/after (`c6_gpu_lease_status.txt`, `gpu_compute_apps_pre_c6.txt`/`post_c6.txt` empty) |
| C7 | End state: GPU before/after, no leftovers, disk, the two checkouts, the attempt-1 archive | **PASS** | GPU **identical** before/after (`353 MiB`, utilisation 0 %, no compute apps, same driver); all six leftover buckets empty (run-related processes, sleeps, cgroup `hostcheck_*`/`tasl2_ar_*`, cgroup run dirs, `/tmp/g0_userns_*`, `/dev/shm`); disk 352.5 GiB free; harness_ar at the pin with only the §4 data link untracked; seven-node at `c025f89a` tracked-clean; attempt-1 archive `p3a_operator_20261027` and lease log `_attempt1_gpu_lease_log.jsonl` **stat only**, mtimes unchanged 2026-11-17 15:42:26 / 15:42:35 (`c7_final.json/.txt`, `gpu_state_before/after.txt`, `attempt1_stat_before/after.txt`) |

The `1-7 PASS` value carries the same caveat as on 21 Nov: **§3 item 7 (CUDA IPC) is untested on TASL-2**;
option A of `autoresearch_fixedtokens` uses no CUDA IPC, and the AST scan at the pin confirms it (below).

## Supplementary (not §3 conditions)

- The pin's own `tests/trackg/test_trackg_isolation.py` in a delegated scope (`systemd-run --user --scope
  -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0`), with the `ar-cond7a` interpreter and
  `PYTHONDONTWRITEBYTECODE=1`: **27 passed, 1 skipped, 0 failed** in 14.64 s, rc 0 (`pytest_isolation.json`,
  `logs/pytest_isolation.log`). The skip is the root-only `test_unprivileged_end_to_end_forgery_through_proc_fails`
  (`skipif not ROOT`; the host is unprivileged).
- AST CUDA-IPC scan at the pin (option A), over the exact node files: **no call sites** of
  `cuda_share`/`cuda_open`/`_new_shared_cuda`/`bind_cuda` in `run_fixed_budget.py`
  (sha256 `58d80b52…`) or `ar_worker.py` (sha256 `65a4927c…`); 0 hits, 0 non-call references. Context only:
  `ar_isolated.py` keeps the `cuda_share`/`cuda_open` helper definitions and the `_new_shared_cuda` call inside
  that unused helper, for compatibility; the option-A path does not call them (`ast_cuda_ipc_scan.json/.txt`).

## Capture evidence on TASL-2

- Run root: `/home/dowling/r1_engineering/tasl2_ar_pin_hostcheck_20261122/rerun_after_ar_py_optionA_20261122/`;
  orchestration `bash scripts/run_all.sh` (verbatim in `captures/scripts/run_all.sh`), per-step stdout/stderr in
  `captures/logs/`, summary in `captures/SUMMARY.{json,txt}`.
- Capture set: **101 files** (100 hashed + `SHA256SUMS`), **358,750 B content** (the `du -sb` allocation figure is 387,422 B); `SHA256SUMS` sha256
  **`1e8c6e67c014415ba28276734a6b1f6bdfd909abf702216a45a63708279441d1`**; `sha256sum -c SHA256SUMS` **rc 0** on
  TASL-2 and `shasum -a 256 -c SHA256SUMS` **rc 0** after fetch. The digest file itself is outside the capture set:
  `/home/dowling/r1_engineering/tasl2_ar_pin_hostcheck_20261122/rerun_after_ar_py_optionA_20261122/SHA256SUMS.sha256`
  (same sha256). Nothing inside `captures/` is written after the digest is taken.
- Fetched copy in this repo (uncommitted):
  `docs/r1/reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_AR_PIN_BINDING_20261122_captures/` (same
  `SHA256SUMS`, verified).
- Key files: `SUMMARY.{json,txt}`, `host_facts.*`, `harness_ar_pin*.txt`, `step1_git_ls_remote.txt`,
  `node_pins.*`, `env_check.*`, `env_freeze_uv.txt`, `venv_evidence_before/after.*`, `venv_unchanged.json`,
  `step4_data_check.*`, `c1_userns_*.json`, `c2_ptrace.json`, `c3_cgroup.*`, `c4_interp.*`, `c5_smoke.json`,
  `c6_gpu_smoke.json`, `c6_gpu_lease_status.txt`, `c7_final.*`, `pytest_isolation.json`,
  `ast_cuda_ipc_scan.*`, `lead_repoint_evidence/`, `records/`, `scripts/`, `logs/`.

## State changes, moved-aside artefacts, scope and non-authorities

- **Only TASL-2 was used** (`ssh -o BatchMode=yes portal_zhixu`); **TASL-7, HTCondor and deepthought were not
  contacted**. No G.1b, cross-check, G.4 or AR job was started; no label was read; nothing was committed or pushed.
- **No deletion.** Two earlier attempts of this same procedure (same run root) were moved aside under
  `/home/dowling/r1_engineering/tasl2_ar_pin_hostcheck_20261122/_to_delete/` and are **not** part of this binding's
  capture set: `attempt1_false_stop_gate_bug_20261122T145213Z` (stopped on an orchestration gate that mis-read a
  nested JSON key — its §3 host evidence itself was PASS) and
  `attempt2_pass_capture_selfhash_bug_20261122T145258Z` (all host checks PASS and the data staged; its capture
  digest was taken before a final log append, a self-reference defect, so its capture set was not reportable).
  The §4 `data` symlink created by attempt 2 was likewise moved aside (before the recorded attempt's §1 clean
  check) to `/home/dowling/r1_tracks/t1_tasl/_to_delete/harness_ar_autoresearch_fixedtokens_data_link_attempt2_20261122T145258Z`;
  the recorded attempt's §4 re-created it, pointing at the same data directory.
- The GPU was used **only** by C6: a small CUDA tensor in the sandboxed worker, under the exclusive
  `flock ~/r1_locks/gpu0.lock` for ~2 s; the lease log was not written; the card was never shared and no foreign
  compute ran.
- `PYTHONDONTWRITEBYTECODE=1` was used for every Python step. `run_all.sh` invoked the non-GPU checks under
`taskset -c 16-31`; **the captured supplementary pytest command itself did not carry `taskset`** and helper
inline Python likewise ran with the delegated scope's default affinity. No T1 job was running, so this is a
procedure-literal deviation, not a C1–C7 failure. `taskset -c 16-31` was used for data staging and `run_all.sh`'s other non-GPU checks; the captured
supplementary pytest itself ran unpinned, as stated above. No probe wrote `__pycache__` into the venv or either
checkout.
- The Track P attempt-1 archive `/home/dowling/r1_trackp/runs/p3a_operator_20261027` and its lease log
  `runs/_attempt1_gpu_lease_log.jsonl` were only `stat`-ed (mtimes 2026-11-17 15:42:26 / 15:42:35, unchanged); the
  seven-node `runs/` and `sealed_g1b/` trees were not touched.
- The AR spec's `hosts.TASL-2.isolation_host_check.sha256` is still its unfilled placeholder (the lead fills it
  from this committed record) and `env_decision.authority` is still unfilled; this record is host evidence,
  **not** a launch authorization. The author's signed third note, the PLAN environment row (AR-ENV) and both keys
  are still required before `autoresearch_fixedtokens` runs.

**AI-assisted: DeepSeek Harness agent `ar-pin-hostcheck-r2`, 22 Nov 2026. ENGINEERING_ONLY; uncommitted. PASS.**

## Review-condition corrections (22 Nov, post-review)

- **C1:** the capture-set byte figure is 358,750 B content (387,422 B is `du -sb` allocation).
- **C1/C2 (taskset):** the record no longer claims every Python step was pinned. `run_all.sh` invoked the checks
  under `taskset -c 16-31`; the captured supplementary-pytest command itself has no `taskset` and ran with the
  delegated scope's default affinity. No T1 job was running; C1–C7 are unaffected.
- **C2 (attempt-1 capture):** the moved-aside attempt-1 capture set had the same pre-final-append digest defect as
  attempt-2; both are under `_to_delete/` and are not part of this binding capture set. Only attempt-2's defect was
  disclosed in the first text; this sentence discloses both.
- **C3 (run root):** the run-root list also contains `work/`; `gpu0.lock` (0 B) has mtime 2026-11-22T14:58:52Z, an
  end-of-work lease probe after the captured 14:56:44Z post-check, not a job lease; no lease-log write;
  `gpu_state_before/after` show no compute apps.
- **C4 (authority wording):** this record is made under the author-signed **R1-G1B-AR-PY option A** (main `52f4e3e5`), which amends
  R1-G1B-AR-ENV (the AR-PY row is published on main `52f4e3e5`); the earlier
  STOP record/review are on branch `ops-t1-ar-pin-20261122` @ `9090650b`, not main; the AR-ENV environment is not "unchanged": the three `bin/python*` symlinks were re-pointed to
  the versioned CPython 3.12.15, freeze 11def6ad… and `pyvenv.cfg` unchanged. The earlier STOP record and the
  repoint evidence (`SHA256SUMS 58d28727…`) are part of this record's audit trail. This remains host evidence,
  not a launch authorization; §3 item 7 CUDA-IPC is untested and option A uses none.
