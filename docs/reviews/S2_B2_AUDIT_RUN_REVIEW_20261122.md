# Independent review — sweep-2 B.2 EVIDENCE audit, complete attempt 3 (22 November 2026)

Reviewer: `reviewer-s2-audit-run`, independent and read-only. I did not write any reviewed unit, did not
run the audit or any of its gates, and did not run a job. This file is the **only** write. deepthought and
ceph were accessed read-only over ssh (`ls`, `stat`, `find`, `sha256sum -c`, `git rev-parse/status/diff/show`,
`tar -cf -` to download): nothing on deepthought or ceph was created, modified or deleted, no job was
started or stopped. Hashing, JSON parsing, plan regeneration and block recomputation were done on downloaded
copies under `/tmp` with the bundled Python 3.12 + NumPy 2.3.5. Label/evaluation rows were read only to
recompute the two blocks; no label or evaluation value is published in this file. Review date
2026-11-22 (Europe/Berlin).

**Reviewed unit.**
Output `/work/dwong/s2_audit_20261122/paper/results/r1/evidence/C3_audit_EVIDENCE_20261122T164726Z/`
(12 top-level files + 1,064 `seed_journals`; `SHA256SUMS` sha256 `a9da0aae…`, `AUDIT_SEAL.json` sha256
`55fdb225…`, `evidence_completion.json` sha256 `f751681f…`); sealed copy
`/ceph/srv/dwong/paperb/sweep2_audit/s2ev-20261119-a_20261122T164726Z/` (1,076 files, same digests); logs
`paper/cotenancy_20261122T164726Z.log` (sha256 `b35e5092…`) and `paper/audit_20261122T164726Z.log` (4,242,851 B;
only worker lines plus the final summary JSON). Report draft: branch **`ops-s2-audit-20261122` @
`c4a04a04d4dbab84278e906fddd923543ddf48f9`** (parent published main `52f4e3e5`; **not pushed**), one commit
adding 8 files under `docs/r1/reports/sweep2_20261116/` (`S2_B2_AUDIT_REPORT_20261122.md`, sha256 `71410cc9…`,
plus `s2_b2_audit_20261122/{SHA256SUMS,AUDIT_SEAL.json,environment.json,evidence_completion.json,resources.json,ATTEMPT1_STOP.json,ATTEMPT2_STOP_OPERATOR.txt}`).
Authority at run time: published main `52f4e3e5…`, addendum
`docs/r1/authorizations/c3_sweep2_b2_addendum_20261122.md` sha256 `2e5a6a6d…` (bytes unchanged at the current
remote main `c870179d…`), `R1-SWEEP2-B2-GO` exactly one author row, `R1-SWEEP2-B2-DECISIONS`, and
`R1-SWEEP2-B2-RETRY` (commit `c870179d`, see D1). Code pin `db7f344d…` (detached; `r1/` clean; ancestor of
published main), harness `6adf3859…`, batch/table pins `b4697c…`/`82c760…`/`379b17ca…`/`de6d63b5…`.

## Bottom line

**The audit PASS is supported.** Every pass-rule condition and every item (1)–(5) of the operator's checklist
is confirmed independently, including a bit-exact recomputation of both role blocks from `runs.jsonl`. The
sealed evidence, the harness equivalence, the environment/e1 basis, the co-tenancy record and the
attempts-1/2 disclosure all hold. A re-run is not needed.

**The report draft cannot be pushed as it stands.** Two blockers: the wall time/completion instant are
reported one hour late (B1), and the report package's own `SHA256SUMS` cannot verify because it lists
`cotenancy.log`, which is not in the commit (B2; also its self-line is bogus), together with one required
disclosure about the publication time of `R1-SWEEP2-B2-RETRY` (D1) and four minors. All are report-package
fixes; none changes the run's PASS.

## Checks against the operator's list (1)–(6)

### (1) Completion / pass rule — PASS

- `evidence_completion.json` is schema **`r1.c3_audit_completion/4`**, `source: sweep2`, with exactly the 22
  keys the writer at `db7f344d` emits, and no extra or d4b/contingency/partial field anywhere in the records.
  Every bound digest recomputes from the retained bytes: addendum `2e5a6a6d…`, authorization
  `349e502b…` (published `authorizations/c3_sweep2_20261119.md` at `52f4e3e5`), index `b4697c49…`,
  extract `82c76052…`, build `bbb2a95c…`, proposals `379b17ca…`, configs `de6d63b5…`, plan `4479b1dd…`,
  label block `9ab3cb26…`, evaluation block `1e3a0e7a…`, runs `cf57bf7e…`, environment `8aed5ca9…`,
  resources `be5c66ac…`.
- Counts recomputed from the host table `proposals.jsonl` with the code's own rule (explicit `noop`/
  `duplicate` row fields): **0 no-ops, 2,512 duplicates, 2,500 eligible** (5,012 rows) — equal to the
  completion, binding and addendum. The eligible partition regenerates the committed `plan.jsonl`
  byte-equivalently (2,500 rows), and the plan has **1,064 unique (node, config) pairs**, hence 10,640
  planned seed runs.
- `runs.jsonl` = **10,640 rows = 1,064 × 10**; seeds exactly 7001–7010 for every pair; **all**
  `success: true`, `failure: null`, `changed_files: false`, finite metric; one single `worker_runtime`
  record for all 10,640 runs, and it equals the approved venv (`/ceph/dwong/r1_prepare_20261025/venv/bin/python3`,
  `prefix != base_prefix`, versions scikit-learn 1.8.0 / NumPy 2.4.4 / SciPy 1.17.1 / pandas 3.0.3,
  package list `a089bbf1…`). The audit log contains exactly 10,640 `run_command finished` lines, 0 failures,
  0 tracebacks/STOP lines.
- Label block 2,500 rows (`label_kind: audit`, seeds 7001–7005) and evaluation block 2,500 rows (seeds
  7006–7010); both id sets equal the plan ids exactly; `k_label` 5, `sigma_node` from the table row. **Both
  blocks were recomputed from `runs.jsonl` + `proposals.jsonl`** with the reviewed algorithm (paired
  candidate−incumbent per seed, mean and sample sd/√5): **2,500/2,500 rows equal bit-for-bit, maximum
  absolute difference 0.0** (not merely within tolerance).
- No `STOP.json` in the output or in the sealed copy (13 entries in the output = 12 files + `seed_journals`;
  1,076 files sealed = 12 + 1,064 journals). No d4b contingency path exists at code pin `db7f344d`.
- `AUDIT_SEAL.json`: counts 0/2,512/2,500, runs 10,640, labels 2,500, evaluations 2,500, nonfinite 0,
  bad_runs 0; `sha256sums_sha256`/`tree_sha256` `a9da0aae…` = sha256 of the output `SHA256SUMS`;
  completion `f751681f…`; `sealed_utc` 2026-11-22T17:25:03Z, consistent with the ceph copy mtime.

### (2) Environment / harness — PASS

- Paper checkout `/work/dwong/s2_audit_20261122/paper`: `HEAD` exactly
  `db7f344d6ac372737444db5ab036d370543ea65f`, detached, `git status --porcelain --untracked-files=all -- r1`
  empty, no ignored executable file under `r1/`, `origin/main` = `52f4e3e5…` = the `published_main` recorded
  at start, code commit an ancestor of it. The only untracked paths are the three attempt PID files and the
  three attempt output directories.
- `environment.json` binds the reviewed unit and e1 basis correctly: review
  `docs/r1/reviews/S2_AUDIT_UNIT_REVIEW_20261121.md` sha256 `1d1ac629…` (verified bytes at `52f4e3e5`; has the
  standalone `Code-Commit: db7f344d…` and `Verdict: ACCEPTED`); precondition-2 review sha256 `9aafa1f2…`
  (`Verdict: ACCEPTED`, four pins).
- e1 basis (R1-B2-GO B6 (a)): `environment_checks_at_start` equals the e1 replay pins exactly (Python
  3.13.15 build string, prefix, wrapper target `venv/bin/python`, package-list `c09242ac…`, newest dist-info
  `2026-10-26T22:09:12.359336+00:00`); the six pinned e1 file sha256s equal the bytes at e1 commit
  `52992b22`; e1 summary is PASS 16/16 at tolerance 0 with no STOP; the e1 review's last line is
  `VERDICT: ACCEPTED`; the six OpenML cache digests equal the e1 post-run record.
- Harness `/ceph/dwong/r1_prepare_20261025/…/autoresearch_harness`: `HEAD` `6adf3859…`, tracked-clean;
  17 untracked files = exactly the 16 OpenML cache files + `paper/tables/artifact_completeness_report.txt`
  (the e1 record); `git diff --name-only 6adf3859 a3fedbbd` over the eight listed paths
  (`nodes`, `configs`, `harness`, `uv.lock`, `src/autoresearch/{worker,nodes,common}`, `manager/base.py`) is
  **empty**, and the 8 files changed elsewhere are exactly the ones recorded in `environment.json`.
  `uv.lock` sha256 `dd42d018…`.
- The addendum pins equal the artefacts actually used (`b4697c…`, `82c760…`, `379b17ca…`, `de6d63b5…`),
  the batch sealed tree `/ceph/srv/dwong/paperb/sweep2/s2ev-20261119-a` is readable, and the addendum reads
  `approved: true` with the full 64-hex pins.

### (3) Resources / co-tenancy / deadline — PASS (report wall time wrong: B1)

- `resources.json`: 16 workers, 40 CPUs, new scratch under `/tmp`, scratch free 102,174,126,080 B (≥ 16 GiB),
  Ceph free ≈ 344 TB (≥ 50 GiB), file headroom ≥ 966,017 (≥ 2,000), unique configs 1,064, planned runs
  10,640, `operator_deadline_seconds` 21,600 with `operator_deadline_is_protocol_budget: false` (the RETRY
  row's operator timeout, not a protocol budget).
- `resource_monitor.jsonl`: 61 live samples 16:48:46Z–17:20:07Z (every 30 s), no floor breach.
- Co-tenancy: `cotenancy.log` records `OMP/MKL/OPENBLAS/NUMEXPR_NUM_THREADS=1`, the launch interpreter
  `venv/bin/python3`, pre-launch load1 12.25 (free 27.75) and **33** once-per-minute samples
  16:47:26Z–17:19:28Z plus `monitor_done_utc=17:20:28Z audit_exit=0`. Free cores = 40 − load1: **minimum
  13.05 (at 16:59:27Z), maximum 27.75; no sample below 10**. Audit-worker CPU sum after the ramp is
  5.28–14.73 cores (two leading 0 samples; mean 9.89 cores), consistent with thread pinning. Same
  "40 − load1" convention as the accepted e1 and sweep-1 B.2 reviews.
- **Actual wall: launch 16:47:26Z → completion 17:20:09Z = 1,963 s (32 min 43 s)**, well inside the
  21,600 s operator deadline (and inside the original 10,800 s addendum deadline). This is corroborated
  three ways: `evidence_completion.json` mtime 2026-11-22 18:20:09.166 +0100 = 17:20:09Z; audit log last
  worker line 18:20:08 +0100 = 17:20:08Z; Σ run `wall_seconds` = 27,431.6 s / 16 workers ≈ 1,714.5 s plus
  setup/verification. The report's "completion 18:20:09Z = 5,563 s" is the server's **local** 18:20:09 read
  as UTC — exactly +3,600 s (B1).

### (4) Attempts 1/2 disclosed and unused — PASS

- Attempt 1 `C3_audit_EVIDENCE_20261122T103401Z` exists and is unmodified: its own `SHA256SUMS` verifies for
  every listed file except the self-line convention; `STOP.json` sha256 **`54bbea10…`** matches the report;
  empty `seed_journals`, no blocks, no completion. Attempt 2 `…T103708Z` is likewise unmodified (`SHA256SUMS`
  self-verifies except the self-line): `runs.jsonl` sha256 `87f37476…` (784 rows), `STOP_OPERATOR.txt`
  sha256 `2be3194…` (operator stop record; load 98.17/115.91/130.12 at 11:25:15Z), and its `SHA256SUMS`
  sha256 is **`022b2272…`**, all matching the report/STOP report.
- The report discloses both attempts, both STOP hashes and "no seed result used" for each; the published
  STOP report (`ops-s2-audit-stop-20261122` @ `28290172`) carries their full retained records.
- The attempt-3 output is a genuinely fresh run: new output directory (created 16:48:46Z) and new scratch
  `/tmp/r1_c3_audit_EVIDENCE_20261122T164726Z`; fresh `runs.jsonl` (`cf57bf7e…` ≠ attempt-2 `87f37476…`);
  all 1,064 seed journals were written **during this run** (mtimes 16:49:42Z–17:20:08Z) and their names are
  exactly `sha256(json.dumps([node, config_hash]))` — 1,064/1,064 present, 0 extra, 0 missing. Where an
  attempt-2 journal has the same deterministic name, its content differs from the attempt-3 journal (e.g.
  `01ab9f0f…`: attempt 2 `6d18e512…` vs attempt 3 `95257967…`), which is what a fresh execution produces.
  `evidence_run` at `db7f344d` has no resume path and refuses an existing output/scratch directory, and the
  completion binds only this run's files.

### (5) Labels sealed — PASS

- The report and the committed package contain **no label or evaluation values**: the report only states
  counts, seeds, hashes and a PASS; `environment.json`, `evidence_completion.json`, `resources.json` and
  `AUDIT_SEAL.json` contain only digests/counts. The label/evaluation blocks and the block-bearing evidence
  `SHA256SUMS` are not committed.
- Sealed copy: work and ceph copies have the same `SHA256SUMS` (`a9da0aae…`) and `AUDIT_SEAL.json`
  (`55fdb225…`); `sha256sum -c` passes for **all 1,074 entries** (10 of the 12 top-level files + 1,064
  journals) in both the output and the ceph copy. The two files not listed are `SHA256SUMS` itself and
  `AUDIT_SEAL.json`; the seal binds the sums digest and the completion digest, and both were verified.
  The report's cited `tree_sha256`, completion sha and seal sha all match. This review verified
  structural/count/hash properties; it publishes no label content.

### (6) Report readiness — two blockers

- Proposed path/branch: `docs/r1/reports/sweep2_20261116/S2_B2_AUDIT_REPORT_20261122.md` plus
  `s2_b2_audit_20261122/` on branch `ops-s2-audit-20261122` @ `c4a04a04…`; the commit is exactly the base
  `52f4e3e5` plus those 8 files and nothing else, and the branch is not yet pushed. The current remote main
  is `c870179d…` (see D1). Counts, divergences (none), harness/environment records and the attached
  copies are correct: the committed `environment.json`, `evidence_completion.json`, `resources.json` and
  `AUDIT_SEAL.json` are byte-identical to the output files, and `ATTEMPT1_STOP.json`/`ATTEMPT2_STOP_OPERATOR.txt`
  hash to the retained attempt files.
- **B1** and **B2** below must be fixed; **D1** must be disclosed; four minors are listed.

## Findings

### Blockers (must be fixed before the report is pushed)

- **B1 — wall time/completion instant wrong by +3,600 s.** The report says "launch 16:47:26Z → completion
  18:20:09Z = 5,563 s". The completion is **2026-11-22T17:20:09Z** and the wall is **1,963 s**
  (32 min 43 s) (evidence in (3)). The "within 21,600 s" conclusion still holds a fortiori, but an archived
  EVIDENCE report must not carry this number, and the same figure should not propagate to STATUS/PLAN rows.
- **B2 — the report package's `SHA256SUMS` does not verify as committed.** It lists 7 non-self entries
  (`ATTEMPT1_STOP.json`, `ATTEMPT2_STOP_OPERATOR.txt`, `AUDIT_SEAL.json`, `cotenancy.log`, `environment.json`,
  `evidence_completion.json`, `resources.json`) plus a self-line. `cotenancy.log` (correct hash
  `b35e5092…`) is **not** in commit `c4a04a04`: the report subdirectory holds only 6 of those 7 files plus
  `SHA256SUMS` (`*.log` is gitignored, so a plain `git add` silently skipped it). In addition the
  `SHA256SUMS` self-line carries the empty-file hash `e3b0c442…`, which can never match the non-empty file.
  As a result `sha256sum -c` in the report directory fails twice for a reviewer (missing file + self-line).
  Fix: `git add -f` the cotenancy log into `s2_b2_audit_20261122/` and drop the self-line (the evidence
  `SHA256SUMS` convention omits itself); the B.2 sweep-1 report did the same force-add of its gitignored
  `cotenancy.log`.

### Required disclosure (must be added before the report is pushed)

- **D1 — `R1-SWEEP2-B2-RETRY` was published after this attempt had started.** The row is commit
  `c870179d` (parent `52f4e3e5`, only `docs/r1/PLAN.md` +6 lines), author/committer date
  **2026-11-22T17:48:55+01:00 = 16:48:55Z**. The attempt launched at **16:47:26Z**, the audit's authority/
  environment check recorded `published_main = 52f4e3e5` at 16:48:31Z, and the first seed run logged at
  16:48:47Z. The four launch corrections the row records were all complied with (interpreter `venv/bin/python3`;
  the four thread variables = 1; once-per-minute co-tenancy recording with the ≥10-free STOP; operator
  deadline 21,600 s), and the row is on main now, but the report's Authority line cites it without noting
  that the run's recorded published main (`52f4e3e5`) predates it. The report must either disclose the row's
  publication instant (and that the audit's guarded authority was the addendum + `R1-SWEEP2-B2-GO` at
  `52f4e3e5`), or the lead must record that the author's option-A decision was taken before launch. The
  report branch is based on `52f4e3e5`, so the row it cites is only on main, not in the branch.

### Minors

- **m1** — "34 samples" in the co-tenancy log: there are **33** one-minute samples (16:47:26Z–17:19:28Z;
  the 34th line matching `load1=` is the `pre_launch_load1` header) plus `monitor_done_utc=17:20:28Z`.
  Coverage of the run is complete, so only the count is off.
- **m2** — "audit worker CPU sum stayed ~8–16 cores": observed range after ramp is **5.28–14.73 cores**
  (two leading 0 samples, mean 9.89); "≈5–15 cores" would be accurate.
- **m3** — attempt 2 is described as operator-stopped "after 45 min"; the retained record gives launch
  10:37Z and operator stop 11:25:15Z = **48 min** (the "45 min" figure comes from the STOP report's run-phase
  wording). State the window or both figures.
- **m4** — the Status section still says "Independent review of this run: pending (branch
  `ops-s2-audit-20261122`)". After this review it must cite `docs/r1/reviews/S2_B2_AUDIT_RUN_REVIEW_20261122.md`
  and its verdict; that file must be added to the branch, and after the B1/B2/D1 fixes the same file should
  carry the round-2 confirmation (as the Q1/Q3 review did with its §6), otherwise the branch states a review
  state that is no longer true. (The review is a report-file fix; no re-run is involved.)

## What I did not check

- I did not execute `build-sweep`, `sweep2_batch.verify`, `audit evidence-run`, or any gate; the table
  rebuild equality and the batch `verify --sealed` are retained run-time PASSes, covered by the accepted
  precondition-2 review and by the run's own guarded code path (the completion was written only after those
  checks, and no `STOP.json` exists). I did not test the numbers of the audit algorithm itself beyond
  recomputing the plan and both blocks and checking the completion/log hashes.
- I did not verify the sweep-2 collection itself or any downstream analysis; the label tables remain sealed
  and unreleased.

## Required corrections before push (summary)

1. Correct the wall time to launch 16:47:26Z → completion 17:20:09Z = 1,963 s (and keep the "within
   21,600 s" statement).
2. Force-add `cotenancy.log` to `docs/r1/reports/sweep2_20261116/s2_b2_audit_20261122/` and remove the
   `SHA256SUMS` self-line so `sha256sum -c` passes for the report directory.
3. Add the D1 disclosure (or the pre-launch decision record), and correct m1/m2/m3 and the Status/review
   citation (m4).
4. Then push/merge; a round-2 confirmation over the corrected commit plus the added review file is enough
   — the audit itself is accepted.

## Round-2 confirmation — fixes at `ops-s2-audit-20261122` @ `7a0ed184` (22 November 2026, 18:35–18:40 CET)

Round 2 re-reviewed the pushed branch tip **`7a0ed1842d1644815fd5b65112dec79e1793bfa7`** (fix commit on top
of merge `86731d55` of current remote main `c870179d`; remote refs: `origin/ops-s2-audit-20261122` =
`7a0ed184`, `origin/main` = `c870179d`). The fix commit's diff against `c870179d` is exactly **10 added
paths and nothing else**: the report `S2_B2_AUDIT_REPORT_20261122.md` (sha256 now `1897998f…`), the 8-file
package under `s2_b2_audit_20261122/` (cotenancy log included), and this review file. Both `52f4e3e5` and
`c870179d` are ancestors of the tip; the branch's `PLAN.md` carries the single `R1-SWEEP2-B2-RETRY` row; the
addendum sha is still `2e5a6a6d…`; no label/evaluation block or label value was added (package files
re-extracted from the commit and checked). Independently re-verified on deepthought (read-only ssh): the
output and ceph copies are unchanged — both `SHA256SUMS` `a9da0aae…` with all 1,074 entries OK,
`AUDIT_SEAL.json` `55fdb225…`, `evidence_completion.json` `f751681f…`, 1,076 files each, no STOP; labels
remain sealed.

- **B1 fixed.** The report now gives launch 16:47:26Z → completion **17:20:09Z = 1,963 s (32 min 43 s)**
  (within 21,600 s); a grep of the report finds no `5,563 s` / `93 min` (or `8–16`, `45 min`, `34 samples`,
  `pending`) text. This matches the round-1 evidence (completion mtime 18:20:09.166+01:00; audit log
  18:20:08+0100; resource monitor 17:20:07Z; Σ run wall 27,431.6 s / 16 ≈ 1,714.5 s + setup).
- **B2 fixed.** `cotenancy.log` is force-added and tracked in the package (sha256 `b35e5092…`, equal to the
  retained log); the package `SHA256SUMS` was regenerated without a self-line (7 entries), and a fresh
  extraction of `7a0ed184` verifies **7/7 `sha256sum -c` OK**. All 7 hashes equal the retained evidence
  (`AUDIT_SEAL.json` `55fdb225…`, `environment.json` `8aed5ca9…`, `evidence_completion.json` `f751681f…`,
  `resources.json` `be5c66ac…`, `ATTEMPT1_STOP.json` `54bbea10…`, `ATTEMPT2_STOP_OPERATOR.txt` `2be3194…`).
- **D1 fixed.** The report carries a Timing disclosure: row `c870179d` authored 16:48:55Z, 89 s after the
  16:47:26Z launch and 8 s after the first seed run 16:48:47Z; the audit recorded `published_main`
  `52f4e3e5` at 16:48:31Z; the row's four corrections were complied with; the row is on current main and in
  the branch. The added sentence that the author's option-A decision predates the launch is the operator's
  assertion (not derivable from the repository); it is recorded as disclosed, which is what round 1 asked
  for.
- **Minors fixed.** 33 one-minute samples, minimum 13.05 free cores, 0 samples below 10; audit-worker CPU
  5.28–14.73 cores (mean 9.89); attempt 2 48 min; Status cites `docs/r1/reviews/S2_B2_AUDIT_RUN_REVIEW_20261122.md`
  and no longer says "pending".
- **Non-blocking note.** The round-1 commit message `c4a04a04` still contains the old "5,563 s" figure in
  the branch history; the report body and the fix commit message carry the corrected number. No action
  needed; noted for transparency.
- **Remaining action on the lead.** The branch at `7a0ed184` still contains the round-1 copy of this review
  file (`c86174e8…`, NOT ACCEPTED). Commit this appended file into the branch so the report's Status line
  points at the current verdict; its updated blob sha256 is stated in the covering message (a file cannot
  carry its own hash). No other change is needed.

Round-2 result: all three required corrections and the four minors are fixed and verified; the audit PASS
is unchanged and needs no re-run. Once this appended review file is committed, the package is
**ready to push/publish**. This round-2 confirmation supersedes the round-1 NOT ACCEPTED.

VERDICT: ACCEPTED
