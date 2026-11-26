# TASL-2 AR-pin host-check binding review — harness pin `2d09f9a9`, R1-G1B-AR-PY option A (22 November 2026)

**Reviewer.** Fresh independent reviewer (`ar-pin-binding-reviewer`), delegated by the lead; no involvement in
writing the procedure, the run scripts, the binding record or its captures. Read-only: the only file written is
this review. No edit/commit/push/delete, no probe/pytest/torch execution, no GPU workload, no
HTCondor/deepthought/TASL-7 action. TASL-2 was inspected with read-only `ssh -o BatchMode=yes portal_zhixu`
commands (`ls`, `stat`, `readlink`, `sha256sum`, `sha256sum -c`, `du`, `find`, `git rev-parse/status/log/ls-remote`,
`nvidia-smi` queries, `grep`/`sed`/`cat`), and the two run-root checkouts and the venv were not re-tested or
re-run. My only writes on TASL-2 were transient `/tmp` verification redirects (`/tmp/rev_cap_verify.txt`,
`/tmp/rev_repoint_verify.txt`, `/tmp/a1v.txt`, `/tmp/a2v.txt`, `/tmp/rd.txt`); nothing under the run roots, the
two checkouts, the venv, the T1 `data`/`runs`/`sealed_g1b` trees or any repo was written, and the checkouts'
`.git/index` mtimes are unchanged (`harness_ar` `2026-11-22 02:42:04 PST`; seven-node `2026-11-21 01:54:31 PST`).
The interpreter/`python -V`/`uv pip freeze` results are established statically from the live symlink
chain + file hashes plus the recorded evidence, not by re-executing them (re-execution would be a run).

**Object under review.**

- Binding record `docs/r1/reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_AR_PIN_BINDING_20261122.md` —
  163 lines, 17,405 B, sha256 `5ac4b4361a1c00df6ba7605d350c7472717f892f2b6f9fd311fa5b0f496a5309`; untracked
  (`??`) in `ops-tasl-20261116` (HEAD `b93d8c88`, `3c3f822a` an ancestor), as the record says.
- Its sibling captures `TASL2_ISOLATION_HOST_CHECK_AR_PIN_BINDING_20261122_captures/` — **101 files** (100
  listed + `SHA256SUMS`), `SHA256SUMS` sha256
  `1e8c6e67c014415ba28276734a6b1f6bdfd909abf702216a45a63708279441d1`; `shasum -a 256 -c` **rc 0** on the Mac.
  The host copy has the **same** `SHA256SUMS` sha and `sha256sum -c` **rc 0**; the out-of-set
  `.../rerun_after_ar_py_optionA_20261122/SHA256SUMS.sha256` records that same value. The 100 listed file names
  are exactly the 100 files present (no missing/extra entries). Content total is **358,750 B**
  (100 hashed files 349,614 + `SHA256SUMS` 9,136); the record's 387,422 B is `du -sb` (see m1).
- Procedure `docs/r1/reports/g1b_ar_20261122/TASL2_AR_PIN_HOST_CHECK_PROCEDURE_20261122.md` — 194 lines, sha256
  `9c32bca35be057b27b752aeeeb7f39c3154c3875bd66f08efdb31a049c30d881`; HARNESS_ISOLATION §3 — sha256
  `ac3d5cd0abc262efe8d0552770336ef49dc9cd48cd41704c722ed85c08a5473f`; AR spec
  `sweep2/t1_tasl/g1b_tasl_ar_spec.json` — sha256 `784d661a00633658323e77884dbce76fbc5943489612338639946430529bbd3a`,
  `hosts.TASL-2.isolation_host_check.record` = the record path, `sha256` still `TODO`; `env_decision.authority`
  still `TODO`, `paper.commit` still `TODO` (the record says so).
- Host evidence roots re-read live:
  `/home/dowling/r1_engineering/tasl2_ar_pin_hostcheck_20261122/rerun_after_ar_py_optionA_20261122/` and the
  repoint root `/home/dowling/r1_engineering/tasl2_ar_pin_py315_repoint_20261122/`.
- Authority as the record states: R1-G1B-NOTE2-DECISIONS (NOTE2-AR A: the third note is signed only once "a
  TASL-2 host check at that pin passes"); the run premise is the lead's **R1-G1B-AR-PY option-A** fix (given in
  this delegation). Method = the 21 Nov record's seven conditions and orchestration.

**Verdict: ACCEPTED, with conditions C1–C4 (C1–C3 are record/capture text corrections; C4 is the ordinary
commit/sha step; no re-run of the §3 condition checks is required).** 0 BLOCKING, 1 MAJOR (record-only: a §0
`taskset` compliance statement the captures contradict for the supplementary pytest), 5 MINOR. The four
`host_check_*` lines are exact, unique and at column 0; the C1–C7 PASS verdict and the §1–§4 claims reproduce
from the captures and the live host; the option-A repoint is independently verified before/after. The record
correctly scopes PASS to **this rerun** and states it is **not** a launch authorization; §3 item 7 CUDA IPC is
untested and disclosed.

## 1. The four gate lines — exact, unique, column 0

`check_host_record` (`sweep2/t1_tasl/g1b_tasl.py:734`) reads the record bytes from published `main`, compares
`sha256` to the spec, then matches `^(host_check_[a-z_]+):\s*(.*?)\s*$` per line, rejects duplicates, and wants
`{host: spec_host.hostname, harness_commit: spec.harness.commit, items: "1-7 PASS", verdict: "PASS"}`. Emulated
against the record and `sweep2/t1_tasl/g1b_tasl_ar_spec.json`:

| Line in record | Value | Expected | OK |
|---|---|---|---|
| `host_check_host: TASL-2` (line 9) | `TASL-2` | spec `hosts.TASL-2.hostname` = `TASL-2` | yes |
| `host_check_harness_commit: 2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe` (line 10) | the pin | spec `harness.commit` = `2d09f9a9…`, procedure §6 | yes |
| `host_check_items: 1-7 PASS` (line 11) | `1-7 PASS` | procedure §6 / `check_host_record` | yes |
| `host_check_verdict: PASS` (line 12) | `PASS` | `check_host_record` | yes |

Each appears **exactly once**, all four at **column 0**, outside any list/code block, no duplicates, no extra
`host_check_*` line anywhere in the file (the only other `host_check` text is the prose `hosts.TASL-2.
isolation_host_check.*` on lines 4 and 158, which the regex does not match). The record's own sha256 matches the
task declaration. As delivered the gate cannot pass yet — the record is not on published `main` and the spec's
`sha256` is `TODO` — exactly the workflow the record states (lead commits, then fills the sha). This is expected
and, as the record itself says, not a launch authorization.

## 2. §1–§4 at the pin — independently verified

- **§1 harness_ar** (`/home/dowling/r1_tracks/t1_tasl/harness_ar`): live `HEAD` =
  `2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe`, detached (`symbolic-ref` rc 1), `git status --porcelain
  --untracked-files=all` = only `?? nodes/autoresearch_fixedtokens/data`, one worktree, no stash; origin
  `https://github.com/dowlingwong/autoresearch_harness.git`; GitHub `git ls-remote … mac-trackg-t1-ar-20261121`
  still returns exactly the pin; captured `merge-base --is-ancestor c025f89a HEAD` = rc 0. The record is
  transparent that the clone was made by the earlier (pre-repoint) 22 Nov attempt of the same procedure and
  "re-verified afresh" — the four §1 requirements are recorded and re-reproduce.
- **§1 seven-node** (`/home/dowling/r1_tracks/t1_tasl/harness`): live `HEAD` =
  `c025f89aeafc2199bf3487b4bcaa16678273c702`, detached, tracked tree clean, four pre-existing untracked `data`
  symlinks with mtimes `2026-11-21 14:52:56 / 02:32:55 / 14:42:49 / 19:25:23 PST` (not created by this run).
- **§2 pin**: re-hashed on the host: `configs/trackg/nodes/autoresearch_fixedtokens.yaml` =
  `5bdce00ac51718de8547ce2d065c0e5ae83f26406ff9404f01ac42b0e2b866e7`,
  `nodes/autoresearch_fixedtokens/representative_edits/manifest.json` =
  `55f2666a3d09aaedb8b8552aef00f8a9c27b84f1bd7df24d886904dad581e5c7`; captured `raw_sha256` =
  `5c1bdf3d84c0721818adc239186ac30ffa2c2bb3b6b373e56b236e47cbd61192` (canonical parsed-YAML hash; matches the AR
  spec's declared `node_spec_sha256`), committed file pin =
  `147f0d35d40df54b5902260f07bf25043f515dbc0066991ab05e3b8c64eda0fc`, 20 frozen entries, data link absent at the
  capture. All four match procedure §2.
- **§4 data** (`/home/dowling/r1_tracks/t1_tasl/data/autoresearch_fixedtokens`): live manifest sha256 =
  `ab7186d2b6fba9037283a59de9f071c317a98e4f43806368663d6d9e398faf51`,
  **13 files**, HF revision `915333b4f8b8684f39aeaafea600fea6f43fb703` (prefix `915333b`), `du -sh` = **963M**,
  dir/manifest modes 500/400; node link is the absolute symlink to that directory; the checkout's only untracked
  entry is `nodes/autoresearch_fixedtokens/data`; `prepare_data.py` rc 0 at 14:56:22Z (re-check/re-link of the
  data staged by moved-aside attempt 2 — see §6 below). The record discloses that the download/tokenizer ran in
  attempt 2 (`14:53:03Z–14:54:52Z`, 11 shards, tokenizer 19.0 s, manifest written last) and that the recorded
  attempt re-ran the idempotent re-check; the attempt-2 `step4_prepare_data.log` on the host confirms those times
  and numbers.

## 3. R1-G1B-AR-PY option A — the repoint, verified before/after

The premise (the reason for the rerun) checks out against three independent sources: the pre-repoint STOP
captures, the lead's repoint-evidence root, and the live venv.

- **Before** (`TASL2_ISOLATION_HOST_CHECK_AR_PIN_20261122_STOP_captures/`, sha256 `00f2a9cb…`,
  `shasum -c` rc 0): `env_check` shows `readlink_f … cpython-3.12.16-linux-x86_64-gnu/bin/python3.12`,
  `python 3.12.16 (main, Oct 26 2026, 14:08:45)`, `uv pip freeze` stderr "Using Python 3.12.16 environment";
  `python_drift_evidence.txt` shows `bin/python -> …/cpython-3.12-linux-x86_64-gnu/bin/python3.12`,
  `python3 -> python`, `python3.12 -> python`, and the unversioned alias pointing at `cpython-3.12.16`.
- **The fix** (`/home/dowling/r1_engineering/tasl2_ar_pin_py315_repoint_20261122/`): `SHA256SUMS` sha256
  `58d287273c3f6047344d9ad23fd3319995b7789093d65a76c03c4c2c3f6580aa`, `sha256sum -c` **rc 0**;
  `captures/symlinks_before.txt` (mtime `2026-11-22 06:41:49.211 PST`) shows the 3.12.16 alias chain and
  `before_python=Python 3.12.16`; `captures/symlinks_after.txt` (`… .310 PST`) shows all three direct targets
  `…/cpython-3.12.15-linux-x86_64-gnu/bin/python3.12`, `after_python=Python 3.12.15`,
  `interpreter_sha256=0a97d28d…`, `interpreter_bytes=31027176`, `freeze_lines=122`; the venv's three symlinks
  carry mtimes `2026-11-22 06:41:49.212–.213 PST` = 14:41:49Z, the time the record states.
- **After / live**: `readlink bin/python = bin/python3 = bin/python3.12 =
  /home/dowling/.local/share/uv/python/cpython-3.12.15-linux-x86_64-gnu/bin/python3.12` (all direct), resolved
  interpreter sha256 `0a97d28d3635c7dfd143de6d00b09c0cb382249c020b28ee33fb4002db1efb9c`, size **31,027,176 B**;
  `pyvenv.cfg` sha256 `2f05da0a6007dae90f35f8fb2284f859ac6ccae7b92dd3c58d5652e68338cf42`, mtime `2026-10-25
  20:48:24 PST`; `python -V` recorded as `Python 3.12.15` (venv_evidence before and after; `sys.version`
  `3.12.15 (main, Oct 21 2026…)`, `base_prefix` …`cpython-3.12.15`); `uv pip freeze` raw 122 lines, sha256
  `11def6ade60a81eeb43856652048d74a43fd588a7c7c7ccbf98af817cb82fef1`, **byte-identical** to the committed
  `sweep2/g1b/env/ar-cond7a.freeze.txt` (same sha on `origin/main`, 122 lines); torch `2.6.0+cu124`, CUDA 12.4.
- **No other venv change**: `find` over the live venv for entries modified from the repoint window onwards lists
  only the `bin/` directory and the three symlinks; `pyvenv.cfg` and every other venv entry predate the repoint
  (Oct 25), and the before/after snapshots (`venv_unchanged.json`, `unchanged=true`) are identical in every
  recorded field. The recorded check itself wrote nothing into the venv (nothing newer than 06:41:49 in it).

The record's before/after table (targets, resolved interpreter, sha/size, `python -V`, freeze, `pyvenv.cfg`,
torch) is accurate. One wording consequence worth carrying (m4): the AR census venv is no longer literally
"unchanged" — three `bin` symlinks were re-pointed; the record discloses this, but any AR-ENV/PLAN text that
calls the venv "unchanged" should carry the same disclosure.

## 4. C1–C7 at the pin, supplementary test and AST scan — verified

All captures reproduce; each condition's PASS is supported, with no waiver.

| # | Verification |
|---|---|
| C1 | `c1_userns_ar_cond7a.json` / `c1_userns_syspy.json`: `unshare` flags `0x72020000` rc 0 / errno 0 for the **ar-cond7a** (3.12.15) and `/usr/bin/python3` (3.10.12) interpreters; uid 1008→0 and gid→0 mapped; real tmpfs mount rc 0/writable; child `pid 1 ppid 0`, new PID namespace; host sysctls (`unprivileged_userns_clone=1`, apparmor restriction 0) in `host_facts` |
| C2 | `c2_ptrace.json`: `ptrace_scope 1`, `yama` in LSM; parent→child attach/detach ok; unrelated same-uid sibling attach **EPERM** (errno 1); children reaped |
| C3 | `c3_cgroup.json/.txt`: delegated scope, `memory.max=8589934592`, `memory.swap.max=0`, `cgroup.kill` exists, `cgroup.procs` writable, owner uid 1008, `nsdelegate=True`; the pin's `isolation.RunCgroup` create→join→`cgroup.kill`→empty→removed, child returncode −9 |
| C4 | `c4_interp.json/.txt`: euid 1008; `WorkingCopyRunner._sandbox_config` passes for ar-cond7a (3.12.15) and `/usr/bin/python3`; `broad_entries=[]`, `worker_sandbox_available=True` for both; no home/runs/ancestor entry |
| C5 | `c5_smoke.json` (and copied host record `ar_pin_smoke_20261122T145623Z/`, whose `run_record.json`/`run.log`/`result_channel.txt` hashes are byte-identical to `records/ar_pin_smoke/`): `effective:true`, `waivers {}`, `exceptions []`, euid 1008, `ptrace_scope 1`, `nsdelegate true`, `log_intact true`, `parent_traced_by null`, `parent_dumpable_at_accept false`, cgroup removed; outcome ok 1.0; `val_accuracy: 1.0000` |
| C6 | `c6_gpu_smoke.json`: GPU by full UUID `GPU-4d623e76-7587-ee15-a633-46f60d220d94` (only GPU; `CUDA_VISIBLE_DEVICES` set to the full UUID); worker `pid 1 ppid 0` in new user/mnt/pid namespaces, `euid/uid 0`; `tensor_sum 4096.0`, matmul `16.0`, `memory_allocated_bytes 33556992`, torch `2.6.0+cu124`/CUDA `12.4`, no CUDA error; `effective:true`, `waivers {}`, `exceptions []`, cgroup removed; `dev_shm []`, `shared_dev_shm false`; lease `flock` acquired 14:56:26Z / released 14:56:28Z rc 0, **no lease-log write**, compute apps empty pre/post |
| C7 | `c7_final.json/.txt`: GPU identical before/after (`353 MiB`, 0 %, no compute apps, driver `535.309.01`), `no_leftovers true` (six buckets empty), disk **352.5 GiB** free, harness_ar at the pin with only the §4 `data` link untracked, seven-node at `c025f89a` tracked-clean; attempt-1 archive and lease log `stat`-only and unchanged (`2026-11-17 15:42:26.390938519` / `15:42:35.402938959 PST`, re-stat now identical) |

- **Supplementary pytest**: `logs/pytest_isolation.log` — delegated `systemd-run --user --scope -p Delegate=yes
  -p MemoryMax=8G -p MemorySwapMax=0`, ar-cond7a interpreter, `PYTHONDONTWRITEBYTECODE=1`, `timeout 900`:
  `27 passed, 1 skipped` in 14.64 s, rc 0. The skip is the root-only
  `test_unprivileged_end_to_end_forgery_through_proc_fails` (`tests/trackg/test_trackg_isolation.py:506`,
  `skipif(not ROOT)`; the other `skipif` needs `/proc`, which exists; the cgroup runtime skips are not
  triggered). Matches the record. **But the pytest command carries no `taskset`** — see M1.
- **AST CUDA-IPC scan** (`ast_cuda_ipc_scan.py/.json/.txt`, real `ast.walk` of every `Call`/`Name`/`Attribute`):
  `run_fixed_budget.py` sha256 `58d80b5224ac5e3981f60ac7b7e251a8c97eaf31d0a88a4e8811e920699a33ed`,
  `ar_worker.py` sha256 `65a4927c54a566baa5efd7c26104e66eeb96ccfd6eddf92b59766b70d75613eb` (both re-hashed live on
  the host, equal), **0 call hits / 0 non-call references** in both. `ar_isolated.py` is context only: it keeps
  `cuda_share`/`cuda_open` definitions and the `_new_shared_cuda` call inside `cuda_open`; a live grep over the
  node dir shows no call sites outside `ar_isolated.py`, so the option-A path does not use CUDA IPC. §3 item 7
  itself remains untested on TASL-2 — the record states this caveat and that AR option A does not need it.

## 5. Captures, provenance and end state

- The capture set verifies byte-for-byte (`shasum -c` rc 0 Mac, `sha256sum -c` rc 0 TASL-2, same
  `SHA256SUMS` sha). The listed set equals the present set; `SHA256SUMS` mtime `06:56:45.948 PST` is later than
  every captured file (latest `step_results.txt` `.942`), so nothing inside `captures/` was written after the
  digest, as the record says; the digest's own sha is outside the set (`SHA256SUMS.sha256`, same value).
- The run root's `scripts/` is byte-identical to `captures/scripts/` (`diff -r` rc 0; `run_all.sh` sha
  `e3d6204a88d1d66951183c82597717e1d37bd4fba54ddda228ac9c2c7ea259fa` both), so the "orchestration … verbatim in
  the capture set's `scripts/run_all.sh`" claim holds. `work/committed/ar-cond7a.freeze.txt` (used by
  `env_check`) has sha `11def6ad…`, 122 lines, matching the committed freeze.
- The captured smoke records are byte-identical to the host record dirs (run_record/run.log/result_channel for
  both smokes; `gpu_report.json` matches the C6 probe output). The two records are fixture nodes
  (`fake_isolated`, `tasl2_gpu_smoke`); no `autoresearch_fixedtokens` job ran.
- End state re-checked live: GPU present, no compute apps; the T1 `runs/` and `sealed_g1b/` trees show no write
  since before the session; seven-node/checkouts clean as above. The record's "no deletion / moved aside"
  disclosure is corroborated: `.../tasl2_ar_pin_hostcheck_20261122/_to_delete/` holds
  `attempt1_false_stop_gate_bug_20261122T145213Z` (gate mis-read `python_3_12_15` at the top level instead of
  `checks.python_3_12_15`; its §3 host evidence was PASS) and `attempt2_pass_capture_selfhash_bug_20261122T145258Z`
  (all conditions PASS, data staged; its digest fails on `step_results.txt` appended after hashing);
  `.../t1_tasl/_to_delete/harness_ar_autoresearch_fixedtokens_data_link_attempt2_20261122T145258Z` is the moved
  aside attempt-2 data link. Both moved-aside attempt summaries match the record's description (attempt 2
  `verdict=PASS`).
- **Scope/overclaim**: the record says PASS only for this rerun (status line + dates + §"Why this is a rerun"),
  says it is host evidence and **not** a launch authorization, keeps the §3 item 7 caveat, and leaves the spec's
  sha/`env_decision.authority` unfilled. No G.1b/cross-check/G.4/AR job is claimed or evidenced; the GPU was used
  only by C6; nothing committed/pushed. These are accurate.

## Findings

### BLOCKING

None.

### MAJOR

- **M1 (record-only) — the §0 `taskset` compliance claim is contradicted by the captures for the supplementary
  pytest.** The record says "`taskset -c 16-31` and `PYTHONDONTWRITEBYTECODE=1` were used for every non-GPU
  Python step (data staging, all checks, the supplementary pytest), as the procedure requires". The captured
  `scripts/run_all.sh:356–359` and `logs/pytest_isolation.log` show the pytest was launched as `systemd-run
  --user --scope … -- bash -c '… exec timeout 900 "$VENV" -m pytest …'` with **no `taskset`**, so it ran with
  the scope's default CPU affinity (all CPUs) instead of `16-31`; the small orchestration helper Python calls
  (`json_flag`, c5 record copy, `venv_unchanged`, pytest-count parse, final verdict read) are likewise unpinned.
  The `PYTHONDONTWRITEBYTECODE=1` half is true (exported globally; no `__pycache__` appeared in the venv or the
  two checkouts). Every other non-GPU step — data staging, §2/§3 checks, C1–C5, C7, AST, summarize — **is**
  under `taskset` in the logs; C6 is GPU and exempt. Impact: **none on C1–C7 or the four gate lines** (the pytest
  is supplementary), and no T1 job was running (pre-existing `running_jobs` empty, GPU lease free,
  `runs/`/`sealed_g1b/` untouched); but the sentence is inaccurate and §0 was not literally met for the
  supplementary step. Fix the text (state the actual invocation and, if desired, re-run the pytest under
  `taskset -c 16-31` and regenerate the capture set) before the record is committed/cited.

### MINOR

- **m1 — "387,422 B" is apparent size, not content.** The capture set is 101 files; `du -sb` = 387,422 B because
  it counts seven 4,096-byte directory entries (101 file bytes = **358,750**; 100 hashed = 349,614 +
  `SHA256SUMS` 9,136). Same class as the 21 Nov review m6 — cite "101 files; 358,750 B of content (`du -sb`
  387,422 B)" or state the basis.
- **m2 — moved-aside attempt 1's capture set is also digest-invalid, but only attempt 2's is described that
  way.** attempt1 `SHA256SUMS` sha `7153eb84c9da397bf24df4c528d91d4a85c78f916c7daa81b1aed0c2544d1f79` (external
  digest matches) fails on `step_results.txt`; attempt2 `6ccc7c30…` fails the same way — the same
  append-after-digest defect, not only attempt2's. Both correctly sit outside the binding set; extend the
  disclosure so "not reportable" is stated for both.
- **m3 — run-root/state description is incomplete.** The §"Capture evidence" lines list the run root as
  `scripts/, captures/, logs/, records/`, but the run root also holds `work/` (including the
  `committed/ar-cond7a.freeze.txt` used by the check) and the out-of-set `SHA256SUMS.sha256` (the latter is
  described elsewhere). Also, the expected out-of-run-root state change from the lease — the truncating open of
  `~/r1_locks/gpu0.lock` (mtime now `2026-11-22 06:58:52 PST`, the post-session lease use) — is not listed;
  state it as the one expected exception (as the 21 Nov review m3 asked).
- **m4 — the R1-G1B-AR-PY authority is asserted, not cited.** The record calls the fix "the lead's **authorised**
  R1-G1B-AR-PY option-A fix", but no R1-G1B-AR-PY decision record exists in this tree (the procedure and spec
  reference AR-ENV; the earlier STOP report listed options without taking one; only the "STOP review" is
  present). The delegation here states option A as given, so this is an audit-trail gap rather than an
  evidence defect: cite the decision/commit in the record, and carry the three-symlink repoint into AR-ENV/PLAN
  wording that says the census venv is "unchanged".
- **m5 — two procedure-literal deviations are handled implicitly.** §1's "make a separate clone" was not
  repeated (the clone was made by the earlier attempt; the record says so and re-verifies the four required
  facts), and §4's prepare_data was invoked by absolute path from the run root rather than from the node
  directory. Both outcomes are independently verified (HEAD/clean/ancestor; manifest/link/13 files), so there is
  no effect; note them explicitly or keep the current disclosure.

## Conditions

- **C1 (record text, before commit/citation).** Correct M1: state the supplementary pytest's actual invocation
  (delegated scope, no `taskset`; `PYTHONDONTWRITEBYTECODE=1` applied) and either disclose that deviation or
  re-run the pytest under `taskset -c 16-31` and regenerate the capture set with a new `SHA256SUMS` (then report
  the new sha). Do not claim "every non-GPU Python step" unless all are pinned. No re-run of C1–C7 is needed.
- **C2 (record/capture text accuracy).** Fix m1 (byte-total basis) and m2 (attempt-1 digest disclosure); add
  `work/` and the lease-lock exception if the record keeps an exhaustive run-root/state list (m3).
- **C3 (audit trail and gate operating conditions).** Cite the R1-G1B-AR-PY option-A authority (m4) and the AR-ENV
  "unchanged" nuance; keep the §3 item 7 CUDA-IPC UNTESTED caveat and the explicit non-authorization language
  (both already present). No node that uses `cuda_share`/`cuda_open` may start on the strength of "1-7 PASS".
- **C4 (gate condition, not a host-evidence defect).** The four lines pass the `check_host_record` parsing test
  now, but the gate will still STOP until (a) the lead commits the record to published `main` and (b) the AR
  spec's `hosts.TASL-2.isolation_host_check.sha256` is set to the committed record sha (both `TODO` now, as the
  record states), and `env_decision.authority` is filled. This review verifies the content/evidence, not that
  the gate already passes.

## Verdict

**ACCEPTED** for the R1-T1-HOST-TASL / NOTE2-AR A host gate at harness pin `2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe`:
the four key lines are exact, unique and column-0; C1–C7 PASS with `effective:true` / `waivers {}` /
`exceptions []` on the smokes; the §1–§4 binding data reproduces from the captures and the live host; the
R1-G1B-AR-PY option-A repoint is independently verified (before 3.12.16 alias → after direct versioned 3.12.15,
interpreter sha/size, freeze 122 lines/`11def6ad…`, no other venv change); the supplementary pytest (27/1) and
CUDA-IPC AST scan (0 hits) are recorded; and the capture set is byte-verified on both machines. The PASS is
correctly scoped to this rerun and is **not** a launch authorization. With conditions C1–C3 as record-text
corrections (C4 is the normal commit/sha step) this record is suitable to commit and cite; M1/m1–m5 do not
undermine the host-check PASS. §3 item 7 (CUDA IPC) remains **untested** on TASL-2; AR option A uses no CUDA IPC.

---

### Reviewer's command record (22 Nov 2026, Europe/Berlin / TASL-2 PST)

- Mac (read-only): `shasum -a 256 -c SHA256SUMS` in the captures dir (100/100 OK; `SHA256SUMS` sha
  `1e8c6e67…`); byte/count totals; sha256/lines of the record, procedure, HARNESS_ISOLATION, AR spec, committed
  freeze; emulation of `check_host_record` (Python, local) over the record + spec; `git status`/`ls-files`/
  `show origin/main:`/`merge-base` in `ops-tasl-20261116`; reads of every capture cited above, `run_all.sh`,
  `run_gpu_smoke.sh`, probes, `summarize.py`, the STOP captures and the two moved-aside attempts' summaries and
  digests.
- TASL-2 (`ssh -o BatchMode=yes portal_zhixu`, read-only): `readlink`/`sha256sum`/`stat` on the venv links,
  interpreter, `pyvenv.cfg`, freeze file, node files and data manifest; `find -newermt` over the venv and the
  two checkouts; `git rev-parse/status/symbolic-ref/log/merge-base/ls-remote/worktree/stash` for
  `harness_ar` and the seven-node checkout; `sha256sum -c` of the run-root captures (rc 0), the repoint evidence
  (rc 0) and both moved-aside attempt sets (rc 1 on `step_results.txt`, as disclosed/expected); `du -sb/sh`,
  `find`/`stat` on the run root, `_to_delete`, `runs/`, `sealed_g1b/`, the attempt-1 archive/lease log,
  `~/r1_locks`; `nvidia-smi -L`/`--query-compute-apps`; `grep`/`sed` on the pin's isolation test and node
  files. No probe, pytest, smoke or kit/U2 job was run on any host.
