# Independent review — sweep-1 B.2 EVIDENCE audit PASS (19 November 2026)

Reviewer: `reviewer-b2-audit`, independent and read-only (did not write the reviewed unit, did not
run the audit or its gates, and did not read any secret). This file is the **only** write; it is
uncommitted. No execution of the audit, no job, no `ceph`/deepthought write, no git write, no commit,
push, branch or ref change. Review date 2026-11-19 (Europe/Berlin).

**Reviewed unit.** Branch **`ops-b2-audit-20261119` @ `42f13cc07aa2493aac28ff93b3e7acb0534faa78`**
(report commit `f77e5ba9d022409a40c452158c1d84db59d71977`, base published `main`
`de3de54fd22dcdd86215be0924307e36a64ed08b`), report directory
`docs/r1/reports/b2_audit_20261119/` (16 files), against authority `origin/main` @ `de3de54f`,
`docs/r1/authorizations/c3_b2_addendum_20261117.md`, PLAN rows R1-B2-GO / R1-B2-ADDENDUM /
R1-B2-ADDENDUM-FIX / R1-B2-PIN-FIX2, `docs/r1/reviews/B2_PACKAGE_ORIGIN_REVIEW_20261118.md`,
`docs/r1/reviews/E2_CODE_UNIT_REVIEW_20261117.md`, and the e1 replay report/review
(`ops-e1-replay-amend-20261117` @ `52992b22`, `E1_AMEND_RUN_REVIEW_20261117.md`).

**Method.** The target commit is not present in the local clone, so the branch tree was obtained from
the published repository (codeload of the exact commit; the commit graph was read from the GitHub API
and from the retained `report_repo` clone on deepthought). The retained evidence was inspected over
ssh **read-only** (`ls`/`stat`/`find`/`sha256sum`/`cat`; no writes, no jobs, no git commands in the
18 Nov STOP directory). All hashing, JSON parsing and block recomputation was done on downloaded
copies under `/tmp` with the bundled Python 3.12 + numpy; the audit code itself was not executed. The
read-only `git status`/`rev-parse` inspection of the retained 19 Nov checkout updated only that
checkout's `.git/` **directory** mtime (2026-11-19T00:57Z); its `.git/index` mtime (00:27:38Z) and
all file contents are unchanged, and no reviewed artifact depends on it.

## Bottom line

The **PASS is supported**. The branch is built exactly as stated (report commit on top of published
`main`; 13 report files, then 3 explicitly re-added gitignored block/log files), the checkout and
docs overlay are byte-exact, the host table carries the frozen dry-run counts and hashes, the four
pass-rule conditions hold, the `r1.c3_audit_completion/3` record binds every hash, the two role blocks
equal an independent recomputation from `runs.jsonl` **exactly**, the environment basis is the
published e1 replay (16/16, tolerance 0), the resource floors and deadline were respected, the 18 Nov
STOP directory is preserved (only its `.git/` directory mtime differs), and the disclosures are
present. I found **no blocker and no major finding**; four minors are recorded below (one wrong
timestamp in a preservation note, one un-derived co-tenancy figure, one unexplained package-list hash
duality, and one implicit rather than explicit "no labels read" statement). None changes the verdict.

## Checks against the operator's list (1)–(10)

### (1) Main review acceptance lines; addendum binding; pin ancestor of main

- `docs/r1/reviews/B2_PACKAGE_ORIGIN_REVIEW_20261118.md` on `de3de54f` (sha256
  `dd31b3d627a20caeb3cd620a1e32f4b10b45c37b31383090f4c412e81bc75bf3`) has standalone
  `Code-Commit: ab79b4ce0e427d09e5d5b718e98882c8fbcb6e74` and `Verdict: ACCEPTED` lines (its closing
  acceptance, not a quoted earlier round). The E2 review's own standalone acceptance is
  `Code-Commit: 435513d2486cca21c514a3fa74bbcd5c1210c160` / `Verdict: ACCEPTED` (lines 330–331),
  i.e. the commit the addendum says the standalone E2 line accepts.
- Addendum on `de3de54f`, sha256
  `e9deba6334014feae805cd468727fbeb44cc9aaf786d34f2ff180ee4c4d69709`, contains `R1-B2-GO`,
  `ab79b4ce0e427d09e5d5b718e98882c8fbcb6e74`, `6adf3859de66c4814fcf376eed59880fbd8eeaf7` and
  `K = 10`. Its header records the two corrections (ADDENDUM-FIX, PIN-FIX2) and the pre-worker STOP
  that PIN-FIX2 supersedes.
- `ab79b4ce` is an ancestor of published `main` `de3de54f` (`merge-base --is-ancestor` PASS). The
  PIN-FIX2 delta from `435513d2` is exactly the two docstring-only package markers
  (`r1/scripts/__init__.py`, `r1/diagnostics/__init__.py`, +1 line each) and the regression test
  (`r1/tests/test_c3_evidence_guards.py`, +25 lines), via commits `2c861988` + `ab79b4ce`; nothing
  else.
- Branch ancestry: `42f13cc0` → `f77e5ba9` → `de3de54f`; the remote
  `refs/heads/ops-b2-audit-20261119` is `42f13cc0`; `origin/main` is still `de3de54f` (the branch is
  two report commits ahead and not merged). `f77e5ba9` adds 13 report files, `42f13cc0` adds the
  three explicitly re-added gitignored artifacts (`label_block.jsonl`, `evaluation_block.jsonl`,
  `cotenancy.log`); no other paths change. Both commits are timestamped after the run
  (00:53:05Z / 00:53:38Z vs run end 00:50:22Z).

### (2) Detached checkout at the pin; `r1/` clean; docs byte-identical to `main`

- The attempt's `paper` is a fresh clone of `https://github.com/dowlingwong/Agent_paper_B.git`
  (reflog: clone 00:23:12Z, checkout `ab79b4ce` 00:23:25Z), detached (no symbolic HEAD), `HEAD` =
  `ab79b4ce`, `origin/main` = `de3de54f` = live remote.
- `r1/` is clean: `git status --porcelain --untracked-files=all -- r1` is empty, and the only tracked
  differences are the expected staged `docs/` overlay (37 entries, add/modify) plus the untracked
  audit output directory.
- The `docs/` overlay is byte-identical to published `main` `de3de54f`: a full SHA-256 manifest of
  all **1,893** files under `docs/` matches the `de3de54f` tree exactly, and the branch tree equals
  that tree plus the 16 report files only.
- The `PLAN.md` freeze is consistent: `main` is still `de3de54f`; the pins record the same main at
  launch and at the completion check.

### (3) Host table: counts and hashes from the frozen index

- `table/proposals.jsonl` = **b713c42338c42cea6991ee8ac8e598183fc79c22aeef6a2e8539c7f971dd57c4** and
  `table/configs.json` = **b585b72758668a17c65b842c204e3c08253ee6c7af92c34c9a8bc8b4a53882df**, the
  frozen dry-run values (`MAC_M3_DRYRUNS_20261104.md` §2); `table/build.json` =
  `c14a68aec5ce8e408923930b63ba057503f14bd82b6e1f077879c3deb03a48ee`, with `label: EVIDENCE`,
  `commit: ab79b4ce…`, the same `table_sha256`, the classification/index hashes, 4,999 proposals and
  302 distinct configurations.
- Recomputed from `proposals.jsonl` with the code's own rule (explicit `noop`/`duplicate` row
  fields): **0 no-ops, 3,274 duplicates, 1,725 eligible**, 4,999 total; **466 unique
  (node, configuration) pairs** (302 distinct configuration hashes, as the dry run states; 466 is the
  node/configuration pair count the addendum budgets). The build's replay record is 5,813 rows →
  4,999 proposals, 0 zero-delta and 0 repeat-metric violations, 526 skipped invalid.
- The preserved 18 Nov table (same frozen corpus, `build.json` `commit: 435513d2`) carries the same
  `proposals.jsonl`/`configs.json` hashes, so the 19 Nov table was genuinely rebuilt at the new pin.
- I did not re-run `build-sweep` (no execution); its full source replay PASS at run time is retained
  in `preflight_diagnosis.json`, and the host bytes equal the published frozen hashes, which is the
  substantive claim.

### (4) `verify_evidence_completion` recomputation, schema `/3`, block equality

- `evidence_completion.json` is schema **`r1.c3_audit_completion/3`**, label EVIDENCE, with all 21
  expected keys and no extras. I recomputed every bound digest from the retained files
  (authorization, addendum, classification, index, build/proposals/configs, plan, label block,
  evaluation block, runs, environment, resources); all match.
- I recomputed both role blocks from `runs.jsonl` myself with the reviewed algorithm (paired
  per-seed candidate−incumbent differences; seeds 7001–7005 for `delta_label`/`se_label`; 7006–7010
  for `delta_evaluation`/`se_evaluation`; mean and sample sd/√5; `sigma_node` from the table row):
  **1,725 label rows and 1,725 evaluation rows are equal to the recomputation as parsed JSON, value
  for value** (not merely within tolerance). Label ids and evaluation ids are unique, cover exactly
  the plan/eligible set, and carry only `audit` labels with the label/evaluation seed split.
- The retained `verification_summary.json` (00:51:19Z) is the real consumption pass: it records
  `verify_evidence_completion` PASS at schema `/3`, blocks recomputed from raw runs, all completion
  hashes true, worker-runtime limitation carried, and `STOP.json`/`audits.jsonl` absent. Its output
  hashes equal the output files, and its seed-journal manifest recomputes to
  `85d9b6b25dec2167e51603e90602a6ecc737dbe3bae648a1a77d2faa7792288e`.

### (5) `runs.jsonl`: 4,660 = 466 × 10 exact seeds; validity; worker runtime; no STOP

- **4,660 rows, 466 configurations**, key set exactly the 466 plan pairs × seeds **7001–7010**; no
  duplicate keys; every configuration has exactly the ten default seeds.
- Every row: `success: true`, `changed_files: false`, finite numeric metric; each row carries a
  `worker_runtime` record whose `worker_python`, `prefix`, `versions`, `package_list_sha256`,
  `worker_python_realpath`, `worker_command_python` equal the approved environment (and
  `prefix != base_prefix`). `wall_seconds` sum 18,381.8 s.
- 466 durable seed journals hold 4,660 fsynced lines, one per run, with the same
  (node, config, seed) multiset as `runs.jsonl` and names equal to the hashed `[node, config]`
  identity; journal mtimes span **00:29:29Z–00:50:20Z**, matching `pins.json`.
- No `STOP.json` and no legacy `audits.jsonl` in the output; `PASS.json` records exit code 0 and the
  four pass-rule booleans; the launch is one session (00:27:38Z–00:50:22Z) with one `START`/`END` in
  `audit_stdout.log`, one output directory and one scratch directory.

### (6) Counts, labels, evaluations and environment basis

- Counts: 4,999 proposals / 1,725 eligible / 3,274 duplicates / 0 no-ops / 466 pairs / 4,660 runs /
  1,725 label rows (all `audit`) / 1,725 evaluation rows. `counts.json`, `evidence_binding.json`,
  `PASS.json`, `pins.json` and `evidence_completion.json` agree with the recomputation and with the
  addendum's expected population.
- Label block seeds are exactly 7001–7005 and evaluation block seeds exactly 7006–7010; the
  evaluation values are not present in the label block and vice versa; seeds 7006–7010 are used only
  in the evaluation block (raw runs necessarily execute them, but no label/decision uses them). The
  table, plan and runs carry no `soft`/label field, so no pre-existing label value was read.
- Environment basis: R1-B2-GO **B6 (a)**; the published e1 replay at `52992b22`, review
  `E1_AMEND_RUN_REVIEW_20261117.md` ACCEPTED, is **16/16 at tolerance 0 with no STOP under
  R1-E1-OPENML-AMEND**; the six pinned e1 file hashes match the bytes at `52992b22`; the audit-start
  current-environment checks equal the replay's recorded build/prefix/wrapper-target/canonical package
  list (`c09242ac…`)/newest dist-info mtime. Harness `6adf3859…` tracked-clean, `uv.lock`
  `dd42d018…`, Python 3.13.15, sklearn 1.8.0, NumPy 2.4.4, pandas 3.0.3, SciPy 1.17.1, and the six
  OpenML cache tree digests equal the e1 post-run record.
- The **B4 (a)** limitation ("the probe does not attest the task process itself") is present in
  `environment.json` and `evidence_completion.json`, and `environment.json`/the completion record
  carry the three e1 section-9 disclosures (amended dataset identity, batch `.venv` wrappers to the
  shared venv, bounded 16-evaluation replay scope).

### (7) Checksums, artifacts and 18 Nov STOP preservation

- `SHA256SUMS` verifies **14/14** listed report files; `OUTPUT_SHA256SUMS` verifies **476/476**
  output files (10 metadata + 466 journals). The report's block/completion/environment/resources/
  binding copies are byte-identical to the authoritative output, and the committed report directory
  is byte-identical to the retained `report_files/`.
- Authoritative output
  (`paper/results/r1/evidence/C3_audit_EVIDENCE_20261119T002306Z`) and the attempt's `output/` copy
  are hash-identical for all ten metadata files; the attempt directory retains the checkout, host
  table, preflight, logs, `START.json`, report files and full output copy.
- Preserved 18 Nov pre-worker STOP directory
  `/ceph/srv/dwong/paperb/b2-435513d2-20261118T012807Z.veDjse`: all 11,281 files still carry 18 Nov
  mtimes (none newer than 19 Nov), the table's `proposals.jsonl`/`configs.json` carry the frozen
  hashes, `HEAD` is the old pin `435513d2`, `.git/index` was not rewritten (18 Nov mtime), and the
  retained `preflight_diagnosis.json` is byte-identical (sha256 `698a1a30…`) to the published 18 Nov
  preflight record. No directory other than `paper/.git/` changed on 19 Nov, which is consistent with
  "nothing deleted".

### (8) Co-tenancy, resources and deadline

- Workers **16** (authorized maximum, below the 40 CPUs); resources record 40 CPUs, scratch required
  16 GiB vs **117,761,064,960** bytes free on local XFS (not ceph), and the Ceph file-count headroom
  1,500,000 − 433,784 = 1,066,216 ≥ operator reserve 2,000 ≥ estimate 478; all **43** live monitor
  samples keep scratch, Ceph free space (≥ 50 GiB; observed ≈ 372 TB) and the file reserve.
- Deadline 10,800 s is recorded as an operator timeout, not a protocol budget; actual wall time
  1,364 s (00:27:38Z–00:50:22Z).
- Co-tenancy immediately before launch: 1-min load 15.39 on 40 CPUs ⇒ ≈24.61 free, floor 10, PASS
  (same `40 − load` convention as the independently accepted e1 review). Runtime total-load samples
  (29.72, 30.45, 32.46, 30.60, 30.60, 30.71, 28.64) include the audit's own 16 workers; subtracting
  them gives other-user load ≈12.64–16.46 and **23.54–27.36 cores left free**, above the floor; at
  completion the load was 15.19 ⇒ ≈24.81 free. The runtime sentence in the addendum is phrased in
  terms of *other users' load*, so no STOP is triggered (see MINOR-2 for the presentation gap).

### (9) Full pass rule and STOP state

- Every eligible proposal has 10 successful, finite, unchanged-file seed runs for its candidate and
  its incumbent (runs key set = plan pairs × seeds) — PASS.
- Both role blocks are written and equal the raw-run recomputation — PASS.
- The `/3` completion record binds all hashes, the addendum, the environment basis and the
  worker-runtime limitation — PASS.
- The counts by kind equal the plan's — PASS.
- No STOP rule triggered: no guard failure (all ten preflight gates `pass: true`), the host table
  equals the frozen counts/hashes, no failed/missing/non-finite/file-changing seed run, deadline not
  reached, no resource floor reached, no interruption, no dropped proposal or seed, and 7006–7010
  used only in the evaluation block. No retry and no resume: one attempt, new scratch and output
  paths, and the 18 Nov STOP directory untouched.

### (10) Honesty and disclosures

- The 18 Nov STOP `.git`-mtime disclosure is present (a read-only `git status` side effect; index not
  rewritten) — the stated clock value is wrong (MINOR-1), the substance is correct.
- The batch `.venv`-wrapper disclosure is present in §6 and in the completion record's environment
  basis; the worker-runtime **B4 (a)** limitation is present in both machine records and the report;
  the EVIDENCE/label-freeze statement is present ("labels count only after an independent review and
  the author's separate label-table freeze"), and I verified independently that no pre-existing label
  value is read (table/plan/runs carry no label field) — the wording is only implicit (MINOR-4).
- No claim in the report contradicts the retained evidence; the STOP directory is honestly disclosed
  as touched only at its `.git/` directory mtime, and the run is honestly presented as EVIDENCE, not
  as labels.

## Findings

**Blockers: none.**
**Majors: none.**

**MINOR-1 — wrong clock value for the preserved 18 Nov `.git/` directory mtime.** `REPORT.md`
(header and §8) says the only observable difference is the `paper/.git/` directory mtime
"(00:18Z)". Observed now: `2026-11-19T00:52:06Z` (01:52:06 CET), i.e. when the report was being
assembled; 00:18Z was presumably an earlier inspection. The substantive claim is true and verified:
all files keep 18 Nov mtimes, `.git/index` (18 Nov 01:28:40Z) was not rewritten, and no directory
other than `paper/.git/` changed on 19 Nov. Fix: correct the timestamp in the report (or state "an
operator read-only `git status` after the run").

**MINOR-2 — runtime co-tenancy figures are quoted without the derivation.** §3.1 quotes the raw
1-min loads during the run, which include the audit's 16 workers, so a reader applying the report's
own launch metric (`40 − load`) obtains 7.54–11.36 free and would see a floor breach in 4 of 7
samples. The addendum's runtime sentence is about *other users' load*; subtracting the audit's 16
workers gives 23.54–27.36 free, i.e. no STOP. The report should state that derivation explicitly
(and, for symmetry, that the launch check `40 − load` = 24.61 is the e1-reviewed convention). The
same wording ambiguity exists in the launch bullet "if 16 workers would leave fewer than 10 free
cores" (literal `40 − 15.39 − 16 = 8.61`), which is resolved by the R1-B2-GO "leave ≥ 10 cores for
other users" footprint reading (40 − 16 = 24) — worth one clarifying sentence for the author's
label-freeze record.

**MINOR-3 — two package-list hashes are bound without explanation.** The interpreter basis records
the e1 canonical package list `c09242ac…`, while every `worker_runtime` record carries `a089bbf1…`
(the audit's JSON-normalised package-list hash; the two functions canonicalise names differently).
Both bind the same venv transitively (the audit process's canonical hash equals the e1 record, and
the worker probe's JSON hash equals the audit process's JSON hash — enforced by
`validate_worker_records` and the start checks), but the report/records do not say so; a reader could
mistake the mismatch for a contradiction. Fix: one sentence naming the two normalisations.

**MINOR-4 — "no labels read" is implicit.** The report conveys that this is EVIDENCE and that labels
count only after review and the author's label-table freeze, and I verified no label/`soft` value
exists in the table, plan or raw runs (and no label table is read by the code path). An explicit
sentence ("no label table exists yet / was read; all label values here are produced by this audit")
would close the honesty checklist item outright.

**Traceability note (not scored).** The committed `REPORT.md` is 17,365 bytes while the retained
`logs/assemble.log` records 16,967 bytes from `assemble_report.py`; the final report was edited after
that assembly run (the retained template lacks the `.git`-mtime sentence). This is benign for the
evidence — the committed report directory is byte-identical to the retained `report_files/` and to
the branch — but it explains MINOR-1 and means the retained assembly script/log do not reproduce the
committed report bytes.

## What this review did not do

No audit, worker, test, build-sweep or consumption run; no cluster job; no `ceph` or deepthought
write; no git write (no commit, push, branch or ref change); no label table read. All retained-evidence
inspection on deepthought used read-only commands; the only non-content side effect was the updated
`.git/` directory mtime of the retained 19 Nov checkout, disclosed above. Nothing in the reviewed
report depends on that mtime.

VERDICT: ACCEPTED
