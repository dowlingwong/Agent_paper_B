# TASL-2 AR-pin host-check binding review R2 (delta) — corrected record, 22 November 2026

**Reviewer.** Fresh independent delta reviewer (`ar-pin-binding-reviewer-r2`), delegated by the lead; no involvement
in writing the procedure, the run scripts, the binding record, its corrections or its captures. Read-only: the only
file written by this review is this review. No edit/commit/push/delete of any repo or host artefact; no
probe/pytest/torch execution; no GPU workload or lease; no HTCondor/deepthought/TASL-7 action. TASL-2 was inspected
with read-only `ssh -o BatchMode=yes portal_zhixu` commands (`ls`, `stat`, `readlink`, `sha256sum`, `sha256sum -c`,
`du`, `find`, `git rev-parse/status`, `cat`/`head`/`grep`); the two checkouts, the venv and the run roots were not
re-tested or re-run. One host-side side effect is disclosed: two transient rc-capture redirects on TASL-2,
`/tmp/none` (0 B) and `/tmp/nonexistent_rc_check` (3,380 B, a `sha256sum -c` listing), created at 07:14 PST; nothing
under any run root, checkout, venv, T1 `data`/`runs`/`sealed_g1b`, `~/r1_locks` or any repo was written, and the lock
file was not opened by this review.

**Object under review.**

- Binding record `docs/r1/reports/trackg_g0_20261117/TASL2_ISOLATION_HOST_CHECK_AR_PIN_BINDING_20261122.md` —
  **184 lines, 19,281 B, sha256 `173929d483107a5278a525369993c830eea1d7e0d66d97c57952a592d490336c`**; untracked
  (`??`) in `ops-tasl-20261116` (HEAD `b93d8c88`, `3c3f822a` an ancestor), as the record says. The reviewed version
  was 163 lines, 17,405 B, sha256 `5ac4b4361a1c00df6ba7605d350c7472717f892f2b6f9fd311fa5b0f496a5309` (the prior
  bytes are not retained in the worktree — the file was edited in place — so the delta was established from the R1
  review's quoted pre-correction text plus the current text; the capture set is byte-unchanged).
- Prior review `docs/r1/reviews/TASL2_ISOLATION_HOST_CHECK_AR_PIN_BINDING_REVIEW_20261122.md` — 288 lines,
  sha256 `55ac5e5d8edead4eeb83cd23e477d1643b72a0e4bd2f540b9e25d9b40734f846` (R1: ACCEPTED with conditions C1–C4;
  1 MAJOR M1, 5 MINOR m1–m5). R1's conditions map to: C1 = M1 (taskset text); C2 = m1 (byte basis), m2 (attempt-1
  digest disclosure), m3 (`work/` + lease-lock exception); C3 = m4 (R1-G1B-AR-PY citation, AR-ENV "unchanged"
  nuance); C4 = the commit/sha gate step.
- Sibling captures `TASL2_ISOLATION_HOST_CHECK_AR_PIN_BINDING_20261122_captures/` — **unchanged**: 101 files (100
  listed + `SHA256SUMS`), `SHA256SUMS` sha256
  `1e8c6e67c014415ba28276734a6b1f6bdfd909abf702216a45a63708279441d1`; local `shasum -a 256 -c` **rc 0**, TASL-2
  `sha256sum -c` **rc 0**; **358,750 B content** (100 hashed 349,614 + `SHA256SUMS` 9,136); TASL-2 `du -sb` =
  **387,422 B**; `SHA256SUMS` mtime `06:56:45.948 PST` is later than the newest captured file
  (`step_results.txt`, `06:56:45.942 PST`); the out-of-set `.../rerun_after_ar_py_optionA_20261122/SHA256SUMS.sha256`
  contains `1e8c6e67…  SHA256SUMS` (its own file sha `4f69e459…`).
- The AR spec `sweep2/t1_tasl/g1b_tasl_ar_spec.json` — sha256
  `784d661a00633658323e77884dbce76fbc5943489612338639946430529bbd3a` (unchanged); `hosts.TASL-2.isolation_host_check`
  names the record with `sha256` still `TODO`; `env_decision.authority` still `TODO`; `paper.commit` still `TODO`.
- Host evidence roots re-read: the run root
  `/home/dowling/r1_engineering/tasl2_ar_pin_hostcheck_20261122/rerun_after_ar_py_optionA_20261122/`, the repoint
  root `/home/dowling/r1_engineering/tasl2_ar_pin_py315_repoint_20261122/`, the venv, both checkouts, the T1 data
  dir and both moved-aside attempts under `_to_delete/`.

**Verdict: NOT ACCEPTED for record sha `173929d4…` as a commit/citation candidate — the C1 taskset correction is
incomplete (one MAJOR record-text residual), with two MINOR residual disclosures.** The set of corrections is
otherwise accurate (byte basis, attempt-1 digest, `work/`, AR-ENV repoint wording), the C1–C7 PASS evidence and the
four `host_check_*` lines are accepted, and **no re-run of the §3 condition checks is required**. The blocking fix is
a text edit (the taskset sentence; the two MINOR corrections are also text-only); the record then needs re-hashing,
and **the sha to fill into the spec is the sha of the corrected file, not `173929d4…`**.

## 1. C1–C4 corrections — delta verification

| Correction (record lines) | Claim | Delta verification | Status |
|---|---|---|---|
| C1 (line 122 and 171) | capture-set figure is 358,750 B content; 387,422 B is the `du -sb` figure | TASL-2: 101 files, **358,750 B** content, `du -sb` **387,422**; local `shasum -c` rc 0; host `sha256sum -c` rc 0; 100 listed names = 100 present files (+`SHA256SUMS`). The "allocation" label is loose (`du -sb` is the apparent total, incl. seven 4,096-byte directory entries; `du -s` is the allocated figure), but the basis is now correct and unambiguous. | **PASS** |
| C1/C2 (lines 152–158 and 172–174) | the record no longer claims every Python step was pinned; the supplementary pytest had no `taskset` and the helpers ran on default affinity | **FAIL — the main-body sentence the correction was to remove is still there**, and it asserts the opposite of the inserted disclosure; see **R-M1**. The bold insertion itself is true: `captures/scripts/run_all.sh:356–359` runs `systemd-run … bash -c '… exec timeout 900 "$VENV" -m pytest …'` with no `taskset`, and `captures/logs/pytest_isolation.log` records that command and `27 passed, 1 skipped in 14.64 s` rc 0. | **FAIL** |
| C2 (lines 175–177) | the moved-aside attempt-1 capture set has the same pre-final-append digest defect as attempt 2; both under `_to_delete/` and outside the binding set | TASL-2 `_to_delete/attempt1_false_stop_gate_bug_20261122T145213Z/captures`: `SHA256SUMS` sha `7153eb84c9da…`, `sha256sum -c` **rc 1** with **only** `./step_results.txt` failing (listed `323d5ea9…`, present `0636c95c…`); `SHA256SUMS` mtime `06:52:18.053`, `step_results.txt` `06:52:18.058` — a final append after the digest. attempt 2 (`6ccc7c30c895…`, 100 listed, `06:55:16.983`/`.988`) fails the same single file the same way. Both are outside the 101-file binding capture set. The pre-correction text described only attempt 2's digest defect; attempt 1 was described only by the false-stop gate bug. | **PASS** |
| C3 (lines 178–179) | run-root list also contains `work/`; the `gpu0.lock` lease was opened/closed during C6 (no lease-log write); GPU state shows no compute apps | `work/` confirmed: `work/committed/ar-cond7a.freeze.txt` sha `11def6ad…`, 122 lines; `work/ar_pin_smoke_20261122T145623Z/`, `work/ar_pin_gpu_smoke_20261122T145626Z/`. The C6 lease capture reproduces (`14:56:26Z`→`14:56:28Z` rc 0, no lease-log write; the Track P lease log is still `2026-11-17 15:42:35…`). **But** the host lock file's mtime is `2026-11-22 06:58:52.391 PST` = **14:58:52Z**, after the run window (14:56:17–14:56:45Z) and after the captured 14:56:44Z post-check; the correction does not state this state change (R1-m3 asked for it). `gpu_state_before/after` do show no compute apps. | **PARTIAL** |
| C4 (lines 180–183) | record made under author-signed R1-G1B-AR-PY option A, which amends R1-G1B-AR-ENV; AR-ENV is not "unchanged": three `bin/python*` symlinks re-pointed, freeze `11def6ad…` and `pyvenv.cfg` unchanged; STOP record + repoint evidence (`SHA256SUMS 58d28727…`) are the audit trail | Live venv reproduces: all three `bin/python*` are direct links to `…/cpython-3.12.15-linux-x86_64-gnu/bin/python3.12`; interpreter sha `0a97d28d…`, 31,027,176 B; `pyvenv.cfg` sha `2f05da0a…`; freeze `11def6ad…` (122 lines); repoint root `SHA256SUMS` sha `58d28727…`. The AR-ENV "not unchanged" wording is correct. **But** no R1-G1B-AR-PY decision artefact exists in the worktree or on published `main` (only R1-G1B-AR-ENV, commit `587e4e07`, author-signed 22 Nov 11:18 CET); and the launch artefacts still say "unchanged" — see **R-m2**. | **PARTIAL** |

## 2. The four `host_check_*` lines — exact, unique, unchanged

`check_host_record` (`sweep2/t1_tasl/g1b_tasl.py:734`) reads the record from published `main`, compares the declared
`sha256`, then applies `^(host_check_[a-z_]+):\s*(.*?)\s*$` per line and rejects duplicates. Emulated over the current
record and `sweep2/t1_tasl/g1b_tasl_ar_spec.json`:

| Line | Value | Expected | OK |
|---|---|---|---|
| `host_check_host: TASL-2` (line 9) | `TASL-2` | spec `hosts.TASL-2.hostname` = `TASL-2` | yes |
| `host_check_harness_commit: 2d09f9a9871160fc8f34bcc25b1aa37b1c0c81fe` (line 10) | the pin | spec `harness.commit` = `2d09f9a9…` | yes |
| `host_check_items: 1-7 PASS` (line 11) | `1-7 PASS` | gate / procedure §6 | yes |
| `host_check_verdict: PASS` (line 12) | `PASS` | gate | yes |

Each appears **exactly once**, at **column 0**, outside any code block; the regex finds exactly these four lines and
no duplicate. The values are **unchanged** from R1. The gate cannot pass yet — the record is not on published `main`
and the spec's `sha256` is `TODO` — exactly the workflow the record states (lead commits, then fills the sha). This
review verifies content/evidence, not that the gate already passes.

## 3. No changed measured claims, no changed captures

- **Captures unchanged**: same `SHA256SUMS` sha `1e8c6e67…` (R1 recorded the same), same 101 files, same 358,750 B
  content, `shasum -c`/`sha256sum -c` rc 0 on both machines, same "nothing written after the digest" property.
- **Measured claims unchanged** (diffed against R1's verified values and re-spot-checked live): euid 1008; C1 flags
  `0x72020000`; `memory.max=8589934592`, swap 0; `broad_entries=[]`; smokes `effective:true` / `waivers {}` /
  `exceptions []`, `val_accuracy 1.0000`; C6 `tensor_sum 4096.0`, matmul `16.0`, 33,556,992 B; GPU 353 MiB / 0 % /
  no compute apps; disk 352.5 GiB; lease `14:56:26`/`14:56:28Z`; pytest 27/1/14.64 s; AST hashes `58d80b52…`/
  `65a4927c…`; freeze 122 lines `11def6ad…`; pyvenv `2f05da0a…`; interpreter `0a97d28d…`/31,027,176 B; node pins
  `5bdce00a…`/`5c1bdf3d…`/`147f0d35…`/`55f2666a…`; data manifest `ab7186d2…`, 13 files, revision `915333b4…`,
  963 MiB, modes 500/400, absolute node link; checkouts `2d09f9a9…`/`c025f89a…` with only the expected untracked
  `data` links; attempt-1 archive/lease-log stat mtimes `2026-11-17 15:42:26`/`15:42:35`.
- The only changed numeric text is the C1 byte basis (358,750 B content vs 387,422 B `du -sb`), which is correct.
- Lines 9–12 and their values are unchanged (see §2).

## 4. New MAJOR/BLOCKING check

- **No new BLOCKING.**
- **No new MAJOR** introduced by the corrections themselves (the byte basis, attempt-1 digest, `work/` and AR-ENV
  repoint wording are right); the one MAJOR below is the **prior M1 correction not fully applied**, not a new class.
- Two MINOR residuals of R1-m3/R1-m4 remain (below); neither affects the C1–C7 PASS evidence or the four gate lines.

## Findings

### BLOCKING

None.

### MAJOR

- **R-M1 (record text; residual of R1-M1/C1) — the taskset correction is incomplete and the record now contradicts
  itself.** Lines 152–158 read: "`PYTHONDONTWRITEBYTECODE=1` was used for every Python step. `run_all.sh` invoked the
  non-GPU checks under `taskset -c 16-31`; **the captured supplementary pytest command itself did not carry
  `taskset`** and helper inline Python likewise ran with the delegated scope's default affinity. No T1 job was
  running, so this is a procedure-literal deviation, not a C1–C7 failure. **`taskset -c 16-31` was used for data
  staging and the other non-GPU steps (all checks, the supplementary pytest), as the procedure requires**; no probe
  wrote `__pycache__` …" (bold in the last sentence added here for emphasis; it is plain text in the record.) That
  last sentence is the pre-correction claim the review's condition C1 was to remove, and it is reinforced by the
  "C1/C2 (taskset)" bullet's assertion that "the record no longer claims every Python step was pinned". The
  captured pytest command has
  no `taskset` (`run_all.sh:356–359`, `logs/pytest_isolation.log`), and the inline helpers (`run_all.sh` lines 57,
  97, 333, 361, 433, 459) are likewise unpinned and run in the **top-level orchestration shell, not inside a
  delegated scope** (so "the delegated scope's default affinity" is not even the right room for the helpers; the
  pytest is the only one inside a delegated scope). As committed, the record both discloses and denies the same
  procedure-literal deviation. Impact on the host evidence is nil (the pytest is supplementary; no T1 job was
  running; C1–C7 were not affected), but a record that is cited as host evidence may not contain a false compliance
  sentence, and this is exactly the R1 condition C1. **Fix:** delete the trailing "`taskset -c 16-31` was used for
  data staging and the other non-GPU steps (all checks, the supplementary pytest), as the procedure requires"
  clause and replace it with the actual invocation, e.g. "`taskset -c 16-31` was used for data staging and the
  §1–§4/C1–C5/C7 steps; the supplementary pytest and the inline helper Python ran without `taskset` (pytest inside
  its delegated scope, helpers in the orchestration shell), on the default affinity — a disclosed deviation". Then
  re-hash; **do not** fill `173929d4…` into the spec. No re-run needed.

### MINOR

- **R-m1 (record text; residual of R1-m3/C2) — the `gpu0.lock` state change is still not stated accurately.** The
  correction says "the `gpu0.lock` lease was opened/closed during C6 (no lease-log write)". The captured C6 lease
  is real (`14:56:26Z`→`14:56:28Z`, no lease-log write), but on the host now
  `~/r1_locks/gpu0.lock` is size 0 with mtime/ctime `2026-11-22 06:58:52.391498381 PST` = **14:58:52Z**, i.e.
  after the recorded run window and after the captured `14:56:44Z` post-check; no other file in
  `r1_engineering`/`r1_tracks`/`r1_locks` changed in that minute. That is the expected outside-run-root state change
  R1-m3 asked to state (the `exec 9>…` lease probes truncate the 0-byte lock). **Fix:** state the actual last-open
  time/actor (the end-of-work lease probe) as the one expected out-of-run-root exception, keeping "no lease-log
  write, 0-byte lock, no compute apps" — or explain it as the end re-derivation's lease check. No host-evidence
  impact.
- **R-m2 (audit trail; residual of R1-m4/C3) — the "author-signed R1-G1B-AR-PY" authority is asserted without an
  artefact, and the AR-ENV "unchanged" wording survives in the launch materials.** The correction (lines 180–183)
  claims "the author-signed **R1-G1B-AR-PY option A**, which amends R1-G1B-AR-ENV", but no R1-G1B-AR-PY row/record
  exists in the worktree or on published `main` (grep over `docs/`, `sweep2/`; `git log --all`); the only published
  author signature relevant to this environment decision is **R1-G1B-AR-ENV** (PLAN row, commit `587e4e07`, author
  signed in chat 22 Nov 11:18 CET, published on `origin/main`). Also, the AR-ENV "unchanged" wording is still live in
  the launch materials — the spec
  `env_python_comment` ("the AR census venv in place, unchanged", `g1b_tasl_ar_spec.json:81`) and the note 3 draft
  ("unchanged and used read-only", `G1B_AR_T1_TASL_NOTE3_DRAFT_20261122.md:114`) — so the record's correction says
  AR-ENV is not unchanged while the artefacts it leads to still say it is. Finally the record's "the earlier STOP
  record … part of this record's audit trail" refers to files that are **not on `origin/main`** (STOP report +
  review + captures are commit `9090650b` on `origin/ops-t1-ar-pin-20261122`; untracked in this worktree). **Fix:**
  cite the actual R1-G1B-AR-PY sign-off (chat reference or commit) or name it as the lead's authorization under the
  delegation while noting R1-G1B-AR-ENV's published signature; carry the three-symlink repoint into the spec
  `env_python_comment` and note 3 draft before they are signed/re-issued; publish the cited STOP record and review
  on `main` together with the binding record (or the audit-trail references dangle). Relatedly, line 164's "the
  PLAN environment row (AR-ENV) … still required" should name the **AR-PY amendment row** explicitly, since
  R1-G1B-AR-ENV itself is already published (`587e4e07`).

### Observations (no action required for the verdict beyond the above)

- **O1 — correction labels do not map to R1's condition numbers.** The record labels the byte-figure fix "C1" (R1:
  C2/m1), the taskset fix "C1/C2" (R1: C1/M1), the attempt-1 disclosure "C2" (R1: C2/m2), the run-root/lease text
  "C3" (R1: C2/m3) and the authority wording "C4" (R1: C3/m4). Label them by the R1 finding IDs (M1, m1–m4) so the
  correction log maps cleanly to the review it answers.
- **O2 — "du -sb allocation" is loose wording** (`du -sb` is the apparent-size total; `du -s` is the allocated
  figure; 387,422 = 358,750 content + 7 × 4,096 directory entries). The record already attributes the number to
  `du -sb`, so this is cosmetic.

## Conditions

- **RC1 (record text, blocking the verdict).** Replace the false trailing taskset clause per R-M1 and re-hash the
  record; the corrected sha is the one to fill into `hosts.TASL-2.isolation_host_check.sha256` — **do not fill
  `173929d4…`**. No re-run of C1–C7 is required.
- **RC2 (record text).** State the `gpu0.lock` actual state change per R-m1 as the expected out-of-run-root
  exception (0-byte lock, no lease-log write, no compute apps).
- **RC3 (audit trail / launch materials).** Per R-m2: cite the R1-G1B-AR-PY sign-off (or name the lead's
  authorization and note R1-G1B-AR-ENV `587e4e07`), update the spec `env_python_comment` and note 3 draft
  "unchanged" wording, name the AR-PY amendment row in line 164, and publish the quoted STOP record + review with
  the binding record.
- **RC4 (gate, not a host-evidence defect).** After RC1–RC3: commit the corrected record to published `main`, fill
  the new record sha in the spec and `env_decision.authority` (the gate `check_env_row` needs the PLAN row naming
  `ar-cond7a`; R1-G1B-AR-ENV satisfies that), and re-run the launch precondition/`check_host_record`. The C1–C7 PASS
  evidence stands as reviewed; §3 item 7 (CUDA IPC) remains **untested** on TASL-2 and AR option A uses no CUDA IPC;
  this record remains host evidence, **not** a launch authorization.

## Verdict

**NOT ACCEPTED** for the final record sha `173929d483107a5278a525369993c830eea1d7e0d66d97c57952a592d490336c` as a
commit/citation candidate: the C1 taskset correction is incomplete — the pre-correction claim is still present and
contradicts the inserted disclosure and the captures (R-M1, MAJOR, record-only), with two MINOR residuals (R-m1
`gpu0.lock` state change; R-m2 AR-PY/AR-ENV/STOP audit trail). The previous review's other corrections are
substantively right (C1 byte basis, C2 attempt-1 digest, C3 `work/`, C4 AR-ENV repoint wording), the capture set is
byte-unchanged and verifies on both machines, no measured claim changed, the four `host_check_*` lines are exact,
unique, column-0 and unchanged, and the C1–C7 PASS evidence and the §1–§4 binding data reproduce from the captures
and the live host — so **no re-run of the host checks is needed**. Fix the sentence, re-hash, and use the corrected
sha in the spec; after RC1–RC3 the record can be committed and cited.

---

### Reviewer's command record (22 Nov 2026, Europe/Berlin / TASL-2 PST)

- Mac (read-only): `shasum -a 256` of the record, prior review, procedure, `HARNESS_ISOLATION_20261117.md`,
  committed freeze, STOP report; `wc -l/-c`; `shasum -a 256 -c SHA256SUMS` in the captures dir (100/100 OK);
  file-count/byte totals; gate emulation (Python regex + spec) over the record; capture-name set comparison;
  reads of the record, prior review, run_all.sh invocation/lease sections, pytest log/json, lease pre/post and C6/C7
  captures, `SUMMARY.txt`, `step_results.txt` of both moved-aside attempts, `git log/show/merge-base` for the
  R1-G1B-AR-ENV and STOP commits, PLAN/note3/spec wording greps.
- TASL-2 (`ssh -o BatchMode=yes portal_zhixu`, read-only): `ls`/`stat`/`readlink`/`sha256sum` on the run root,
  `work/`, `SHA256SUMS.sha256`, `SHA256SUMS` (verify rc 0), `du -sb`, `gpu0.lock`, the venv links/interpreter/
  `pyvenv.cfg`, the data manifest and modes, the node link, the checkouts' `rev-parse`/`status`, `_to_delete`
  attempt digests (both rc 1 on `step_results.txt` only) and their mtimes, attempt-1 env/venv evidence, attempt
  summaries, `r1_locks`/lease log/archive stats, `find` for files changed around the lock mtime, plus the two
  transient `/tmp` rc-capture redirects disclosed above. No probe, pytest, smoke, CUDA call or kit/U2 job was run on
  any host; the GPU lease was not taken.
