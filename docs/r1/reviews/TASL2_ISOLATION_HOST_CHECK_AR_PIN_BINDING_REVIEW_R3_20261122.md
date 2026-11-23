# TASL-2 AR-pin host-check binding review R3 (final delta) — corrected record, 22 November 2026

**Reviewer.** Fresh independent delta reviewer (`ar-pin-binding-reviewer-r3`), delegated by the lead; no involvement
in writing the procedure, the run scripts, the binding record, its corrections, its captures or the prior reviews.
Read-only: the only file written by this review is this review. No edit/commit/push/delete of any repo or host
artefact; no probe/pytest/torch execution; no GPU workload or lease; no HTCondor/deepthought/TASL-7 action. TASL-2 was
inspected with read-only `ssh -o BatchMode=yes portal_zhixu` commands (`stat`, `sha256sum`, `sha256sum -c`, `find`,
`readlink`, `ls`, `cat`); the checkouts, venv and run roots were not re-run or re-tested. Published-main state was
checked read-only with `git ls-remote` and read-only GitHub REST/raw requests; nothing was fetched into the repository.
Three transient rc-capture redirects were created — local `/tmp/r3_caps_check.txt`, and on TASL-2 `/tmp/r3v.txt` and
`/tmp/r3repoint.txt` (both `sha256sum -c` listings); nothing under any run root, checkout, venv, T1
`data`/`runs`/`sealed_g1b`, `~/r1_locks` or any repo was written, and the lock file was not opened by this review.

**Object under review.**

- Binding record `docs/r1/reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_AR_PIN_BINDING_20261122.md` —
  **185 lines, 19,557 B, sha256 `992b21461fa9d4737f857f0c959e74223330a622d6c67d29d3e0385b0780d4fa`**
  (mtime `2026-11-22T16:21:37+01:00` = `15:21:37Z`); untracked (`??`) in `ops-tasl-20261116` (HEAD `b93d8c88`,
  `3c3f822a` an ancestor), as the record says, and not on published `main`.
- Prior review `docs/r1/reviews/TASL2_ISOLATION_HOST_CHECK_AR_PIN_BINDING_REVIEW_R2_20261122.md` — **216 lines,
  20,831 B, sha256 `0b2c8c8f09500c13f7dc12d101cb76ba9a151b1533fbcd4753bdd2615dd6705c`**; R2 reviewed the record at
  **184 lines, 19,281 B, sha256 `173929d4…`**. The prior bytes are not retained in the worktree (the file is edited in
  place), so the delta was established from R2's quoted pre-fix text plus the current text; the **+276 B / +1 line**
  delta is accounted for by exactly the three edited regions (taskset clause, `gpu0.lock` sentence, AR-PY/STOP
  sentence), and every measured value below is unchanged.
- Captures `TASL2_ISOLATION_HOST_CHECK_AR_PIN_BINDING_20261122_captures/` — **byte-unchanged**: 101 files (100 hashed
  + `SHA256SUMS`), `SHA256SUMS` sha256
  `1e8c6e67c014415ba28276734a6b1f6bdfd909abf702216a45a63708279441d1`; local `shasum -a 256 -c` **rc 0, 100/100 OK**;
  TASL-2 `sha256sum -c` **rc 0, 100/100 OK** (locale displays `成功`); **358,750 B content**; TASL-2 `du -sb` =
  **387,422 B**; newest captured file `step_results.txt` mtime `06:56:45.942 PST` is earlier than `SHA256SUMS`
  `06:56:45.948 PST`; the out-of-set `.../rerun_after_ar_py_optionA_20261122/SHA256SUMS.sha256` contains
  `1e8c6e67…  SHA256SUMS`.
- AR spec `sweep2/t1_tasl/g1b_tasl_ar_spec.json` — sha256
  `784d661a00633658323e77884dbce76fbc5943489612338639946430529bbd3a` (unchanged); its
  `hosts.TASL-2.isolation_host_check.record` is the record path above; `sha256` still `TODO`; `env_decision.authority`
  still `TODO`; `paper.commit` still `TODO`.
- Host evidence roots re-read read-only: the run root
  `/home/dowling/r1_engineering/tasl2_ar_pin_hostcheck_20261122/rerun_after_ar_py_optionA_20261122/`, the repoint
  root `/home/dowling/r1_engineering/tasl2_ar_pin_py315_repoint_20261122/`, the venv and the two checkouts.
- **Published `main` (new fact in this review).** The worktree's `origin/main` ref is **stale at `3c3f822a`**; the
  actual remote `main` is **`52f4e3e5`** (`git ls-remote`), the commit `docs(r1): R1-G1B-AR-PY (option A)`
  (parent `3c3f822a`, `docs/r1/PLAN.md` +6: the `R1-G1B-AR-PY` table row; its commit message records the author's
  chat signature, 22 Nov 15:40 CET), pushed **`2026-11-22T14:40:43Z`** (GitHub push event) — about 41 minutes before
  the record's last edit. See R3-M1.

**Verdict: NOT ACCEPTED for record sha `992b2146…` as a commit/citation candidate: one new MAJOR (the R2 AR-PY
publication fix — "the AR-PY row is not yet on published main" — is false; published `main` already carries the
author-signed `R1-G1B-AR-PY` row as `52f4e3e5`), plus two MINOR residuals (helper-affinity wording; the AR-ENV row
wording on line 163).** The C1–C7/§1–§4 evidence, the captures, the byte basis, the measured values and the four
`host_check_*` lines are verified and **unchanged**; **no re-run of the §3 condition checks is required**. The blocker
is one record-text sentence (plus one sentence of the same paragraph) and a re-hash: the sha to fill into
`hosts.TASL-2.isolation_host_check.sha256` is the sha of the corrected file, **not `992b2146…`**.

## 1. The delta — what changed vs the R2-reviewed record

| Region (lines) | R2 item | Change now in the record | Result |
|---|---|---|---|
| 152–157 (taskset paragraph) | R-M1 (residual of R1-M1/C1) | the false trailing clause ("…the other non-GPU steps (all checks, the supplementary pytest), as the procedure requires") is deleted; replaced by "`taskset -c 16-31` was used for data staging and `run_all.sh`'s other non-GPU checks; the captured supplementary pytest itself ran unpinned, as stated above." | **PASS in substance** — the record now states twice that the pytest had no `taskset` and ran unpinned, matching `captures/pytest_isolation.json` (`cmd:` = `systemd-run … bash -c …` with **no** `taskset`, then `27 passed, 1 skipped in 14.64s`, rc 0) and `run_all.sh:356–359`. Residual wording: R3-m1. |
| 177–179 (`gpu0.lock`) | R-m1 (residual of R1-m3/C2) | the bullet now states the actual state change: "`gpu0.lock` (0 B) has mtime 2026-11-22T14:58:52Z, an end-of-work lease probe after the captured 14:56:44Z post-check, not a job lease; no lease-log write" | **PASS** — verified on TASL-2 (see §3). |
| 180–185 (authority paragraph) | R-m2 (residual of R1-m4/C3) | added "…(the AR-PY row is not yet on published main; it is to be published with this record)" and "…are on branch `ops-t1-ar-pin-20261122` @ `9090650b`, not main" | **STOP-branch citation PASS; AR-PY publication claim FAIL — see R3-M1.** |

No other text changed: the title/status/`host_check_*` block, the "Why this is a rerun" section, the §1–§4 and C1–C7
PASS tables and the §"Capture evidence"/state sections are the R2-reviewed text, and the "+276 B / +1 line" delta is
consistent with only those three edits. **No measured claim or capture changed.**

## 2. R2 fixes — item-by-item delta verification

| R2 finding | Required | Delta verification | Status |
|---|---|---|---|
| **R-M1** (MAJOR, taskset contradiction) | delete the false compliance clause; state the actual pytest/helper invocation | false clause gone; pytest is now explicitly twice disclosed as unpinned; `pytest_isolation.json`/`run_all.sh` reprove it. The helper half still says "the delegated scope's default affinity", but the helpers run in the **top-level orchestration shell** (`run_all.sh:57, 97, 333, 361, 433, 459`), not inside a delegated scope (only the pytest is inside the `systemd-run` scope) — R3-m1, wording only | **PASS with MINOR residual** |
| **R-m1** (MINOR, `gpu0.lock`) | state the actual last-open time/actor as the one out-of-run-root exception, keeping "no lease-log write / 0-byte lock / no compute apps" | TASL-2: `~/r1_locks/gpu0.lock` size **0**, mtime=ctime `2026-11-22 06:58:52.391498381 -0800` = **`14:58:52Z`**; later than the captured post-run check `14:56:44Z` (`c7_final.json` `interpreter_evidence.utc`); lease log `_attempt1_gpu_lease_log.jsonl` mtime unchanged `2026-11-17 15:42:35.402938959 -0800`; C6 lease capture `14:56:26Z`→`14:56:28Z` rc 0, no lease-log write; `gpu_state_before/after` no compute apps | **PASS** (the "end-of-work lease probe" attribution is an inference outside the capture set, consistent with R1/R2 and disclosed as out-of-run) |
| **R-m2** (MINOR, AR-PY / STOP audit trail) | cite the actual AR-PY sign-off or the lead's authorization, note AR-ENV; name the AR-PY amendment row (R2's line 164) | STOP report + review are in branch `ops-t1-ar-pin-20261122` @ `9090650b` (remote) and not on `main` — the added branch citation is **true**. But the added AR-PY parenthetical is **false**: published `main` already carries `R1-G1B-AR-PY` as `52f4e3e5` (pushed 14:40:43Z, before the record's 15:21:37Z edit); current line 163 (R2's line 164) still says "the PLAN environment row (AR-ENV)" | **FAIL — R3-M1** (the STOP half passes; the AR-PY half fails) |
| RC1–RC3 remainder | byte basis; attempt-1 digest; `work/`; STOP-branch disclosure | byte basis `358,750 B` content vs `387,422 B` `du -sb` present and correct (lines 122, 170; verified on both machines); attempt-1/2 `_to_delete/` digest disclosure unchanged; `work/` noted; STOP branch now cited | **PASS** (byte basis re-verified; no change) |

## 3. Invariants re-verified (delta-only)

### 3.1 Byte basis — PASS

Record lines 122 and 170: **358,750 B content** (100 hashed files 349,614 + `SHA256SUMS` 9,136), with `du -sb`
**387,422 B** correctly labelled as the apparent/`du -sb` figure. TASL-2: 101 files, 7 directories, content sum
**358,750**, `du -sb` **387,422**; local copy identical (`shasum -a 256 -c` rc 0). The "allocation" wording is loose
(`du -s` is the allocated figure) but the basis is unambiguous — as R2 noted, cosmetic only.

### 3.2 Four `host_check_*` lines — PASS, unchanged

`check_host_record` (`sweep2/t1_tasl/g1b_tasl.py:734`) reads the report from published `main`, compares the declared
`sha256`, matches `^(host_check_[a-z_]+):\s*(.*?)\s*$`, rejects duplicates and wants
`{host, harness_commit, items, verdict}`. Emulated over the record and spec:

| Line | Value | Expected | OK |
|---|---|---|---|
| `host_check_host: TASL-2` (line 9) | `TASL-2` | spec `hosts.TASL-2.hostname` = `TASL-2` | yes |
| `host_check_harness_commit: 2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe` (line 10) | the pin | spec `harness.commit` = `2d09f9a9…` | yes |
| `host_check_items: 1-7 PASS` (line 11) | `1-7 PASS` | gate / procedure §6 | yes |
| `host_check_verdict: PASS` (line 12) | `PASS` | gate | yes |

Each appears **exactly once**, at **column 0**; the regex finds exactly these four lines, no duplicates, no extra
`host_check_*` key. Values are **unchanged** from R1/R2. As delivered the gate cannot pass yet (record not on
published `main`, spec `sha256` `TODO`) — the workflow the record states (lead commits, then fills the sha), not a
content defect.

### 3.3 Captures — PASS, unchanged

Same `SHA256SUMS` sha `1e8c6e67…`, 101 files, 358,750 B content, `shasum -c`/`sha256sum -c` rc 0 on both machines,
same "nothing inside `captures/` written after the digest" property (verified by mtimes), same out-of-set
`SHA256SUMS.sha256`. The repoint evidence at `.../tasl2_ar_pin_py315_repoint_20261122/SHA256SUMS` still hashes to
**`58d28727…`** with `sha256sum -c` rc 0, and the live venv links still resolve to
`…/cpython-3.12.15-linux-x86_64-gnu/bin/python3.12` (all three; interpreter `0a97d28d…` / 31,027,176 B,
`pyvenv.cfg` `2f05da0a…`, freeze `11def6ad…` / 122 lines), as the record says.

### 3.4 Measured claims — PASS, unchanged (spot-checked from the byte-identical captures)

euid 1008; C1 `unshare` flags `0x72020000` (both interpreters), child `pid 1 ppid 0`, tmpfs mount rc 0/writable,
`pid_namespace_child.ns.pid` new; C2 `ptrace_scope 1`, `yama` in LSM, unrelated sibling attach EPERM (errno 1), children
reaped; C3 `memory.max=8589934592`, `memory.swap.max=0`, `cgroup.kill` writable, owner uid 1008, `nsdelegate=True`,
RunCgroup create→join→kill→empty→removed, child rc −9; C4 euid 1008, `broad_entries=[]`, `sandbox_config_ok` /
worker sandbox available for **ar-cond7a** (3.12.15) and `/usr/bin/python3` (3.10.12); C5 `effective: true`,
`waivers {}`, `exceptions []`, `val_accuracy 1.0000`; C6 `tensor_sum 4096.0`, matmul `16.0`, 33,556,992 B,
torch `2.6.0+cu124`/CUDA `12.4`, GPU 353 MiB / 0 % / no compute apps, lease `14:56:26`→`14:56:28Z`, no lease-log
write; C7 disk 352.5 GiB, `harness_ar` `2d09f9a9…`, seven-node `c025f89a…` with only the four expected untracked
`data` links, attempt-1 archive/lease-log mtimes `2026-11-17 15:42:26`/`15:42:35`; pytest 27/1/14.64 s rc 0 with **no
`taskset`** in its command; AST scan 0 primary call sites, `run_fixed_budget.py` `58d80b52…`, `ar_worker.py`
`65a4927c…`, `ar_isolated.py` helper context only; node pins `5bdce00a…`/`5c1bdf3d…`/`147f0d35…`/`55f2666a…`; data
manifest `ab7186d2…`, 13 files, revision `915333b4…`, read-only modes, absolute node link. No `.pyc` newer than the
run start in the venv or either checkout (so "no probe wrote `__pycache__`" holds; the pre-existing `__pycache__`
dirs date from 20–21 Nov). No T1/G.1b/AR job ran.

### 3.5 Final sha — mechanically the current bytes, but not the sha to fill

`992b2146…` **is** the sha256 of the current record bytes and would be the value the spec takes **if the file were
committed byte-identically**, and the gate would then parse the four lines correctly. It is **not** the sha to fill
now: R3-M1 requires a text correction, which changes the sha. The new sha of the corrected file is the one for
`hosts.TASL-2.isolation_host_check.sha256`.

## 4. Findings

### BLOCKING

None.

### MAJOR

- **R3-M1 (record text, NEW in this delta) — the AR-PY publication sentence added by the R2 fix is false.** Lines
  180–182 now read "…the author-signed **R1-G1B-AR-PY option A**, which amends R1-G1B-AR-ENV (**the AR-PY row is not
  yet on published main; it is to be published with this record**)". Published `main` is **`52f4e3e5`**
  (`docs(r1): R1-G1B-AR-PY (option A)`, parent `3c3f822a`; `docs/r1/PLAN.md` +6 — the `R1-G1B-AR-PY` row, "Amends
  R1-G1B-AR-ENV after the TASL-2 AR-pin host-check STOP … Option A: the interpreter symlinks … re-pointed … the host
  check then reruns from §3"), pushed **2026-11-22T14:40:43Z** per the GitHub push event, and its message records the
  author's chat signature (22 Nov 15:40 CET). The record's own last edit is `15:21:37Z` — **41 minutes later** — so
  "not yet on published main" and "to be published with this record" are both wrong. The root cause is the **stale
  local `origin/main` ref (`3c3f822a`)**; R2's premise ("no R1-G1B-AR-PY row/record exists … on published main")
  was based on the same stale ref and is superseded by this remote check. Impact on the host evidence: **none** (the
  authority row really exists and is author-signed, so the audit trail is stronger than the record says), but a record
  about to be committed to published `main` and cited by the spec may not state the opposite of `main`; it is exactly
  the paragraph R2 asked to correct. **Fix:** replace the parenthetical with the actual citation, e.g.
  "(the AR-PY row is on published main as commit `52f4e3e5`, author-signed in chat 22 Nov 15:40 CET)", then re-hash;
  do **not** fill `992b2146…`. No re-run.
- Relatedly (same edit): line 163 (R2's line 164) still says "the PLAN environment row (AR-ENV) … still required", although
  `R1-G1B-AR-ENV` is published (`587e4e07`) and the `R1-G1B-AR-PY` amendment is now published (`52f4e3e5`); name the
  AR-PY amendment row (or state that both PLAN rows are published and only the third-note signature and the two spec
  keys remain). See R3-m2.

### MINOR

- **R3-m1 (record text, residual of R-M1) — the helper affinity is still attributed to the wrong room.** The
  taskset paragraph says the "helper inline Python likewise ran with the **delegated scope's default affinity**".
  The six inline helpers (`run_all.sh:57` `json_flag`, `:97` `$VENV -VV`, `:333` C5 record copy, `:361` pytest-log
  parse, `:433` `venv_unchanged`, `:459` verdict read) run in the **top-level orchestration shell**, not inside a
  delegated scope; only the supplementary pytest is inside the `systemd-run --scope`. The substantive disclosure
  (unpinned; default affinity; a procedure-literal deviation with no C1–C7 impact) remains correct, so this does not
  affect the host evidence — but prefer "helpers in the orchestration shell; pytest inside its delegated scope, on the
  default affinity". The sentence "run_all.sh invoked the non-GPU checks under taskset" followed by the pytest
  exception is also slightly over-broad/ambiguous; "the §1–§4 and C1–C5/C7 probes" is the accurate set. Same edit as
  R3-M1 if the lead wants a clean record.
- **R3-m2 (audit-trail wording) — line 163 (R2's line 164) names the AR-ENV row, not the AR-PY amendment.** With `R1-G1B-AR-PY`
  published (`52f4e3e5`), the record's own statement that the PLAN environment row "(AR-ENV)" is still required is
  stale; name the AR-PY row (which the record itself cites as its authority). Note that R2's request to revise the
  spec `env_python_comment` / note-3 draft "unchanged" wording is **superseded by the published AR-PY decision**,
  which says "the freeze, spec, note and procedure stay unchanged (Python 3.12.15)" — no launch-material edit is
  required on that account.
- **R3-m3 (attribution, no action) — the `gpu0.lock` "end-of-work lease probe" is an inference.** The 0-byte lock's
  mtime/ctime (`14:58:52Z`) is real and post-run, and "no lease-log write / no compute apps / 0 B" reproduce; the
  record's attribution is consistent with R1/R2 and is disclosed as the one out-of-run-root state change. No action.

### Observations (no action required beyond the above)

- **O1** — the correction labels are still "C1/C2/C3/C4" rather than R1's finding IDs (M1, m1–m4), as R2 noted; they
  do not map cleanly to the review they answer.
- **O2** — "`du -sb` allocation figure" is loose (`du -sb` is apparent size; `du -s` is allocation); the number is
  correctly attributed, cosmetic only.
- **O3** — the inserted text was not re-wrapped (lines 155 and 182 are long); cosmetic.
- **O4** — the header's "baseline `3c3f822a` merged in ops" is true of the worktree but `main` is now `52f4e3e5`;
  the lead should **fetch before committing/merging** or the gate's `read_main` will see the stale ref (operational,
  not a record-content defect).
- **O5** — the prior R2 review's statement "no R1-G1B-AR-PY row/record exists … on published main" is itself wrong
  (stale ref); this review's remote check supersedes it. Not the object under review.

## 5. Conditions

- **RC1 (record text, blocks the verdict).** Correct R3-M1 as above (cite `52f4e3e5` / drop the "not yet on published
  main" parenthetical) and re-hash; the corrected sha is the one for
  `hosts.TASL-2.isolation_host_check.sha256` — **do not fill `992b2146…`**. No re-run of C1–C7 is required.
- **RC2 (record text; bundle into the same edit).** Correct the helper-room sentence (R3-m1) and name the AR-PY row on
  line 163 (R3-m2); optionally relabel the correction log by R1 finding IDs (O1). Any of these changes the sha, so do
  them in one edit and re-hash once.
- **RC3 (gate / commit, not a host-evidence defect).** Fetch `origin` first (`main` = `52f4e3e5`, not `3c3f822a`),
  commit the corrected record byte-identically to published `main`, fill the new record sha in the spec and
  `env_decision.authority` (the PLAN rows `R1-G1B-AR-ENV` `587e4e07` and `R1-G1B-AR-PY` `52f4e3e5` both name
  `ar-cond7a`; `check_env_row` accepts the AR-ENV row), then re-run the launch precondition / `check_host_record`.
  The STOP report/review remain branch-only (`ops-t1-ar-pin-20261122` @ `9090650b`) and the record says so; if the
  lead wants the cited audit trail on `main`, publish them with the binding record (R2 RC3/RC4), otherwise the branch
  citation stands.
- **RC4 (scope).** This record remains host evidence, **not** a launch authorization; the third note's signature, the
  spec's `paper.commit` and `env_decision.authority` are still required; §3 item 7 (CUDA IPC) remains **untested** on
  TASL-2 and AR option A uses no CUDA IPC. No re-run of the §3 conditions; the C1–C7 PASS evidence stands as
  reviewed.

## Verdict

**NOT ACCEPTED** for the final record sha `992b21461fa9d4737f857f0c959e74223330a622d6c67d29d3e0385b0780d4fa` as a
commit/citation candidate: one **new MAJOR** (R3-M1 — the "AR-PY row is not yet on published main" sentence is false;
`main` already carries the author-signed `R1-G1B-AR-PY` row as `52f4e3e5`, pushed `14:40:43Z`, 41 min before the
record's last edit), with two MINOR residuals (R3-m1 helper-affinity room; R3-m2 AR-ENV/AR-PY row wording) and one
no-action attribution note (R3-m3). The R2 MAJOR's substantive defect is fixed (no remaining contradiction about the
pytest `taskset`: it is explicitly disclosed as unpinned and the captures agree), the `gpu0.lock` caveat is now stated
and reproduces on the host, the STOP-branch citation is true, the byte basis is **358,750 B** content / **387,422 B**
`du -sb`, the four `host_check_*` lines are exact, unique, column-0 and unchanged, the capture set is byte-unchanged
(`SHA256SUMS` `1e8c6e67…`, 101 files, 358,750 B, verified on both machines), no measured claim or capture changed, and
the C1–C7/§1–§4 evidence reproduces — so **no re-run of the host checks is needed**. Fix the one paragraph (RC1+RC2),
re-hash, and use the corrected sha in the spec; the corrected record can then be committed and cited.

---

### Reviewer's command record (22 Nov 2026, Europe/Berlin / TASL-2 PST)

- Mac (read-only): `shasum -a 256` and `wc -l/-c` of the record, R2 review, spec; `stat` of record/R2 mtimes;
  `shasum -a 256 -c SHA256SUMS` in the captures dir (100/100 OK), file-count/content/`du` comparison; `git status`,
  `git rev-parse HEAD/origin/main`, `git log`, `git ls-tree` of `9090650b`, `git grep` of `AR-PY`/`AR-ENV` on
  `origin/main`, `git ls-remote` of `main` and `ops-t1-ar-pin-20261122`; gate-regex emulation (Python) over the record
  + spec; reads of the record, R2 review, `run_all.sh` (taskset/leases/pytest/helper sections), `pytest_isolation.json`,
  the captures' C1–C7 JSONs and the plain output of the run root.
- Read-only GitHub REST/raw: `commits/main`, the push-events list, the `52f4e3e5` commit detail/patch, and raw
  `main` paths for the binding record (404) and the STOP report (404).
- TASL-2 (`ssh -o BatchMode=yes portal_zhixu`, read-only): `stat`/`ls` of `gpu0.lock`, the lease log and the run root;
  `sha256sum -c SHA256SUMS` (rc 0), `sha256sum SHA256SUMS`, `du -sb`, file count/content sum, newest-mtime vs
  `SHA256SUMS`; the repoint root `SHA256SUMS` (`58d28727…`, verify rc 0) and venv links; `find` for `*.pyc` newer than
  the run start. No probe, pytest, smoke, CUDA call or kit/U2 job was run on any host; the GPU lease was not taken.
