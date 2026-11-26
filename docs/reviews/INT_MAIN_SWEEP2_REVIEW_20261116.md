Reviewed base: 0a8ce27c0c0f858890c2c615a565b71483ecca0d

# S2-M2 integration branch int-main-sweep2-20261116 — independent review record (16 November 2026)

Branch `int-main-sweep2-20261116` from `main` @ `60ec768e`. Unit: the four `--no-ff` merges (mac-int `a15300ca`, M3 + IT-1 `129317d1`, D8 v2 `e3c0921e`, author line `fd275c53`), the `d3ce0d52` code re-application, `HARNESS_PIN_C3` → `a3fedbb`, and the report `reports/INT_MAIN_SWEEP2_20261116.md` with its failure lists. Sweep-2 work plan unit S2-M2; the review scope is the sweep-2 path. One freshly spawned independent reviewer agent (AI-assisted, Claude), two rounds.
- Round 1 (`870b4928`): REVISE. The git work and the merge resolutions were verified as correct, including the `audit.py` resolution, which a probe checked 4/4. 1 MAJOR: the report overstated what `main` would hold for sweep 2. The B.2 rules are sweep-1 code, so sweep-2 audits and table builds are not runnable from this `main`, and more pushes will follow. 6 MINOR.
- Round 2 (`0a8ce27c`): ACCEPT. Two optional nits are left as is:
  - the commit and file counts mix bases: 920 commits and 1,141 files up to `bc164b2e`, plus the report commits;
  - it is the S2-C2 spec, not the wrapper, that sets `paper.evidence_ready`.

**Pushing to `main` is the author's decision.** Nothing was pushed.

Accepted commit (round 2, last): 0a8ce27c0c0f858890c2c615a565b71483ecca0d

The round texts are reproduced unchanged below.

---

# Independent review: S2-M2 integration branch `int-main-sweep2-20261116` (round 1)

- Reviewer: independent (did not write the work). Scope: the sweep-2 path only (runbook §2 S2-M2).
- Reviewed base: `870b4928cb4149a0898a9287f188cedd7bffe8bb` (HEAD of /tmp/pb/wt/int2), from `gh/main` @ `60ec768e`.
- Authority: `gh/author-sweephost-20261116` @ `fd275c53`. Work plan: `gh/docs/runbooks-16nov`, runbook §1 P2 and §2 S2-M2.
- Read-only. No commits, no worktrees added, no files written in existing worktrees. Only targeted tests were run.
  The one probe file is `/tmp/pb/rev_s2m2/t_m3_path.py`, kept outside the repo.

## VERDICT: REVISE

The git work is correct. Every merge resolution checks out: provenance holds, PLAN is the author's byte for byte, no
change from either side is lost, the `audit.py` merge keeps both behaviours, and every test claim checks against the
logs. One MAJOR finding is left, and it is about the report only: the report does not say what this push does and
does not give sweep 2. No code change is needed.

## Findings

### 1. MAJOR: the report overstates what main will hold for sweep 2's B.2 path, and leaves out that more pushes to main will be needed (report §1 table, §4)

The §1 table lists "B.2 rules R1-SWEEP1-CLASSIFY / R1-B2-DECOUPLE … in this branch via merge 2" as a sweep-2 need that
is met. As code, those rules exist only for sweep 1, and their EVIDENCE entry point is blocked whatever the input:

- `r1/c3/audit.py` `evidence_run` starts with `_require_task_native_runtime_attestation()`. That function raises
  unconditionally (`'STOP: actual task-native runtime attestation is not implemented'`, around l. 769–773). The same
  STOP is in the consumption path. This is already known (`reports/M11_SWEEP2_READER_INVENTORY_20261108.md` l. 8 and
  10, and its review), but the S2-M2 report does not carry it forward.
- `evidence_plan` → `r1/c3/dataset.py` `evidence_classification` (l. 267–300) accepts only `decision_id ==
  'R1-SWEEP1-CLASSIFY'`, authorization `docs/r1/authorizations/c3_sweep1_20261027.md`, index
  `results/r1/pilot/C3_sweep_index_20261028T033315Z.json`, and the sweep-1 launch pins.
- The completion and verify records hash `c3_sweep1_20261027.md` (`audit.py` l. 857 and 889).
- `original_sweep_environment` requires batch `r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw`.

So S2-C7 (B.2 audits of sweep 2) and a sweep-2 table build cannot run from this `main`. They need reviewed new code
(binding to the sweep-2 authorization and classification, plus a real task-native attestation) and then another push
to `main`.

The sweep-2 collection code is also unchanged by this branch. `r1/headroom/` (including `e1b_collect.py`, which
S2-C2 calls), `r1/branch/`, `r1/liveness/`, `r1/baselines/`, `r1/theory/`, `r1/harness.py` and
`r1/scripts/dryrun_guard.py` are byte-identical between `60ec768e` and the tip (`git diff --stat 60ec768e 870b4928
-- …` is empty). For the collection path, the push therefore adds authority (PLAN rows, the registry document, the
pin file) and not code.

This bears on the author's push decision. Each push to `main` moves the `_verify_published` authority (see 5). The
author may want to push once, or to know that at least two more pushes follow: the S2-C2/S2-C5 wrapper, and the
sweep-2 B.2 audit binding plus attestation.

**Fix (report only).** Add a short paragraph to §1 or §4, "What this push does and does not enable for sweep 2":
- (a) PLAN authority, the pick registry document, the harness pin file and the D8 gate and lock code on published
  `main`;
- (b) collection code identical to `60ec768e`, so S2-C3 and S2-C4 run at paper `60ec768e` stay representative of the
  collector;
- (c) sweep-2 B.2 audits and table builds not runnable from this `main` (the attestation STOP already existed; sweep-1
  bindings), with the follow-up pushes to `main` that are foreseen.

Also qualify the §1 row: "B.2 rules: code for sweep 1; EVIDENCE entry still at the attestation STOP".

### 2. MINOR: the HARNESS_PIN_C3 change has side effects that are not disclosed (`bc164b2e`; report §1 row 8)

No sweep-2 code reads `r1/scripts/HARNESS_PIN_C3`; S2-C2 checks its own `B2_HARNESS`. The file is read by
`c3_label_sweep.py` and `c3_sweep_dryrun.py`.

- `c3_label_sweep.py` `check_heads` (l. 984–993) requires harness HEAD == pin (now `a3fedbb`).
- Its non-EVIDENCE deepthought path also requires `DEEPTHOUGHT_AUTHORIZED_PINS['harness_commit'] == 6adf385`
  (l. 159–164, 1224–1227).
- A real deepthought ENGINEERING run of the old runner therefore always STOPs from now on.
- The deepthought dry run now uses `a3fedbb`.

This is consistent with R1-SWEEP-HOST-HTC (sweep 1 stays frozen, sweeps run as HTCondor jobs) and with the author's
choice. Say it in the report: "the pin is for record and consistency; S2-C2 enforces the pin itself; the deepthought
runner becomes fail-closed".

### 3. MINOR: dropping M3's `rmtree` has an operational consequence, and the merged M3 branch has no unit test (`f0d02cbf`, `r1/c3/audit.py` `run_config`)

The resolution is correct as code. The reviewer checked this with a probe (`/tmp/pb/rev_s2m2/t_m3_path.py`, 4 passed;
see "Verified"). The report states the behaviour change.

It does not state the consequence for EVIDENCE. Each config's work directory (node copy, data cache, `art/`) now stays
under the dedicated scratch. Two things must therefore be sized for the whole audit, not for in-flight configs only:
`--required-scratch-bytes` and the live floor in `monitor_evidence_resources` (free ≥ required). Otherwise the audit
reaches a resource STOP partway through. This matters for S2-C7's job disk request.

Neither line has a unit test of `run_config(..., stop_on_failure=True, journal, journal_identity)`. The tests cover
only `worker_runtime` and use fakes for `run_config`. Add one sentence to §2 and §4, and propose a regression test like
the probe for a later unit.

### 4. MINOR: main will carry records that cite files missing from main (report §1, §4)

- R1-B2-REPAIR-SCOPE-ACK cites `reviews/IT2_9BAB3D6F_FIVE_FILES_REVIEW_20261114.md`. That review is on
  `mac-answers-20261114` @ `e7f89096`, which is not an ancestor. The report's line "acknowledged … (IT-2 review
  accepted)" rests on it.
- `84471430` cites the trial review `5d8c0274`. Neither `INTEGRATION_TRIAL_20261114.md` nor its review record is on
  the branch.
- R1-W2-3-STOP cites `r1/scripts/w2_runs_total_check.py`, which is absent. R1-EXAM-X7 cites
  `reports/b2_exec_20261115/`, which is absent.
- The featurizer on the tip is still `c3_features/v2` (`r1/c3/features.py` l. 239), because W2 is not merged.

None of this blocks collection; the featurizer and the W2 check matter when tables are built after D8. Either add the
two review records that justify merged code (the IT-2 review; the trial report and review) in a docs-only step, or
list these citations in §4 so the author knows `main` will not be self-contained.

### 5. MINOR: the `_verify_published` consequence of the push is not stated (report §4, "Pushing to main")

`dataset._verify_published` compares the checkout's PLAN bytes with the current published `origin/main`. Its callers
are `evidence_classification`, `original_sweep_environment` and `build_from_sweep`.

After the push:
- Every authority check must run from a checkout at the new `main`. The R1-SWEEP1-CLASSIFY row is byte-identical, so
  sweep-1 consumption keeps working there.
- Records or units pinned to "paper root `main` 60ec768e" cannot be re-verified from that root. This covers the W2 v3
  rebuild, which is already done (`w2-3-rebuild-unit-20261115`), and the S2-C2 example spec.
- Any unit that calls these checks from a `60ec768e` paper root while the push happens will STOP with "origin/main is
  stale" or "differs".

Add one line to §4.

### 6. MINOR (for S2-M3/S2-C2; noted here so the claim is read correctly): the "R1-BX-D8 sealed readers" do not cover S2-C2's sealed root by path

`refuse_sealed` refuses only paths with an `r1_sealed` component (`analysis_guard.py` l. 23–30). S2-C2 writes to
`/ceph/srv/dwong/paperb/sweep2/<run_id>/` and deliberately refuses `r1_sealed`.

For sweep-2 tables, the D8 lock on this branch comes from `guard_table` and `build_from_sweep`: unknown or
non-sweep-1 provenance requires R1-BX-D8-CONFIRM (l. 202–225). It does not come from the path guard. That is
adequate, but the report and the S2-M3 hand-off should not imply that the sealed path itself is refused by the
readers on `main`.

### 7. MINOR (wording)

- "In total 920 commits are added" counts up to `bc164b2e`. With the report commit it is 921.
- `84471430` re-applies the code of `d3ce0d52`. That commit is not an ancestor, by design, because the trial branch is
  not an accepted line. "No … cherry-pick" is true of the accepted lines; say once that `d3ce0d52` is re-applied as
  files.
- Informational: the whole-line merges also bring `_to_delete/c3-recovery-source-data-20261031/` (11 base64 recovery
  files, from mac-int) and a lot of non-sweep-2 content (Track P training, hk2, the exam code) to `main`. This follows
  from the author's `--no-ff` choice; a one-line mention would help the author.

## What I verified

**1. Ancestry and provenance.**
- `a15300ca`, `129317d1` (⊇ `ec6e30a9`), `e3c0921e` (⊇ `da264a40`), `fd275c53` and `60ec768e` are all ancestors of
  `870b4928`.
- Each merge has the stated parents: 103f63f0 = 60ec768e+a15300ca, 793d8de7 = 103f63f0+129317d1, 162e10cb =
  84471430+e3c0921e, f0d02cbf = 162e10cb+fd275c53. 84471430 and bc164b2e are single-parent.
- No squash or rebase. The `gh/*` refs equal the cited SHAs.
- Commit counts are 260, 71, 42 and 541, 920 in total. Files: 1,141 (266 under `r1/`).
- Nothing on `main` is deleted or renamed away: 1,092 A and 58 M versus `60ec768e`. All 872 of main's evidence-path
  renames are present at the tip, and `results/r1/evidence` equals main's.
- Merge 1's tree equals `a15300ca` exactly: mac-int already carried main's last three commits' content.
- The commit messages are accurate.

**2(a). Merge 2.**
- `git diff d317c7db 793d8de7 -- r1` shows only `r1/scripts/c3_audit_dryrun.py` and `r1/tests/test_c3_audit_dryrun.py`,
  which are IT-1's two r1 files.
- Outside `r1/`, the only difference is IT-1's review document.
- `cf155f4a` vs `162e10cb` (r1) differs only by M4's three files, IT-1 and the `d3ce0d52` code.
- `84471430`'s patch is identical to `d3ce0d52`'s code part.

**2(b). `audit.py` resolution.**
- I read the combined diff.
- From the author line, the merged `run_config` keeps: `_copy_audit_node` (validation before the copy; `O_EXCL` and
  `O_NOFOLLOW` creation), `preserve_node_outputs` (the `B1AuditWorker` and `GuardedTrialPath` worker,
  `preserve_node_artifacts`), the `stop_on_invalid` raise, and no deletion. `run_plan`'s `rmtree(tmp)` removal came in
  cleanly from the author side.
- From M3, it keeps the `worker_runtime` probe per seed, the fsync'd journal line per seed, and the `stop_on_failure`
  break without a raise.
- The positional order is `(tmp, stop_on_failure, journal, journal_identity)`, which matches `evidence_run`'s call
  (l. 823). The B1 and exam callers (`r1/exam/campaign.py` l. 52, 295 and 321) pass keywords only and are unaffected.
- The probe was imported from the tip with harness `a3fedbb` and passed 4 of 4. It showed:
  - success gives 3 journal lines, 3 `worker_runtime` records with the expected identity and command, and the work
    directory kept;
  - a failure at seed 2 gives a break after 2 rows, 2 journal lines and no raise;
  - a non-editable file raises `is not editable` before any node copy;
  - the legacy default does not probe.
- The only message change (`"… is not editable on {node}"` → `"… is not editable"`) is not matched by any test or
  caller.
- The probe comes before the preserve step; the two flag sets are never combined by a caller.

**2(c).** `test_scripted_live_golden.py` combines the author line's `tmp_path` fixture with main's `5cffed38`
historical-config replay and the exact SHA assertion. `5cffed38` is in main and not in the author line. The test
passes at the tip.

**2(d).** `git diff fd275c53 870b4928 -- docs/r1/PLAN.md` is empty. Every R1 row id of main, mac-int, M3, D8 v2,
author-x7, author-ack-w23, sweep2-cluster and runbooks-16nov is in it. The `R1-SWEEP1-CLASSIFY` row is byte-identical
to main's.

**2(e). Docs.** A three-way line check against merge base `8311df64` finds no changed line from either side missing
in RUNBOOK.md, PORTAL_EXAM_RUNBOOK.md or STATUS.md. The three add/add records equal the author version.

**3. Needs.**
- The registry entry for `gemma4_31b` (rev `619aca75…`, GGUF sha `2959c1b0…`) and `exam_phase2_20261026/gemma4_31b.json`
  (sha `a04a0346…`) match S2-C2's spec.
- The D8 gate SHA is `02fdbdd2…` and equals `da264a40`.
- The pin is `a3fedbbd…`, equal to S2-C2's `B2_HARNESS`.
- The S2-C2 wrapper is deferred, and that is flagged in §1 and §4, consistent with the author's answer. The S2-M1 gaps
  (noise source, context, gates) are listed.
- `r1/headroom`, `r1/harness`, `r1/exam` and `r1/liveness` are identical between the author line (where S2-C2 was
  developed) and the tip.

**4. Tests.**
- Each `.fail` equals the FAILED ids in its log, and each summary equals the log's last line. The report copies are
  byte-identical to `/tmp/pb/int2_tests`.
- tip ⊆ macint ∪ author: nothing new.
- At the id+message level (first 230 characters), every tip failure line appears verbatim in a parent log, so no
  failure is masked by a new cause.
- Fixed: exactly the 3 author-line tests named in the report. main's 10 ⊆ tip. The two tip runs are identical.
- The per-file breakdown matches.
- Targeted re-run at the tip: 14 files (`test_c3_audit`, `test_audit_preservation`, `test_b1_audit_*` ×3,
  `test_c3_evidence_*` ×6, `test_c3_offline_eval_guard_order`, `test_c3_audit_dryrun`, `test_scripted_live_golden`).
  Result: 93 passed, 1 skipped, 2 failed. The 2 failures are the known D8-confirm STOPs in `test_c3_evidence_guards`,
  which are in macint and in the tip list. The scratch was deleted afterwards.

**5. Report.** Apart from findings 1–7, the statements in §§1–4 check out.

## Required for ACCEPT

Fix finding 1 (a report paragraph). Findings 2–7 are recommended; they can go in the same report edit.

---

# Independent review: S2-M2 integration branch `int-main-sweep2-20261116`, round 2

- **Reviewed base:** `0a8ce27c0c0f858890c2c615a565b71483ecca0d`. This is round 1's base `870b4928` plus two commits,
  `711aec66` and `0a8ce27c`.
- **Rules:** read-only, as in round 1. No tests were run, because no code changed.
- **Round 1:** `/tmp/pb/rev_s2m2/REVIEW_R1.md`.

## VERDICT: ACCEPT

No BLOCKING or MAJOR finding remains.

## Scope of the change

`git diff --quiet 870b4928 0a8ce27c -- . ':!docs/r1/reports/INT_MAIN_SWEEP2_20261116.md'` is clean, so only the
report changed. The code, the tests and the failure lists are as verified in round 1, and the round-1 code findings
still hold.

## Round-1 findings

1. **MAJOR, resolved.**
   - The new §4, "What a push of this branch does and does not enable for sweep 2", makes four points:
     - collection code is byte-identical to `60ec768e` (the modules listed match what I checked);
     - the push adds authority only, so S2-C3 and S2-C4 runs at `60ec768e` stay representative;
     - B.2 audits and table builds are not runnable for sweep 2, for the four reasons (attestation STOP, sweep-1-only
       classification, sweep-1 authorization hash in the completion record, sweep-1 batch environment);
     - at least two more pushes to `main` will follow, and the author can push now or once later.
   - The §1 B.2 row is now marked "sweep-1 code … §4".
2. **MINOR, resolved.** The `HARNESS_PIN_C3` side effects (`check_heads` against `DEEPTHOUGHT_AUTHORIZED_PINS`; the
   dry run) are stated accurately, together with the R1-SWEEP-HOST-HTC context.
3. **MINOR, resolved.** §2 now covers the scratch-bytes and monitor-floor sizing for S2-C7, and the missing
   regression test for the merged `stop_on_failure`/journal branch.
4. **MINOR, resolved.** §4 lists the records that cite files not on the branch. I checked the stated locations:
   - the IT-2 review is on `mac-answers-20261114`;
   - `reports/b2_exec_20261115/` is on `gh/ops-b2-exec-20261115`;
   - the featurizer here is `c3_features/v2`.
5. **MINOR, resolved.** §4 now describes the `_verify_published` window.
6. **MINOR, resolved.** The sealed-root wording is fixed: the lock is `guard_table` / `build_from_sweep` requiring
   R1-BX-D8-CONFIRM, and the path itself is not refused.
7. **MINOR, resolved.** The report now says that `d3ce0d52` was re-applied and is not an ancestor, and that the
   merges bring non-sweep-2 content, including `_to_delete/`. The commit count is stale again; see nit (a).

The old §4 is now §5, and its content is unchanged. No other section points to the old numbering.

## Nits (optional, not required)

a. "921 commits … counting this report's commit: 1,141 files" mixes two bases, and the two round-2 commits make it
   stale again. At `0a8ce27c` the branch has 923 commits and 1,150 files changed versus `60ec768e`; the extra files
   are the report and its failure lists. The 920 commits and 1,141 files up to `bc164b2e` are correct. Either state
   the figures up to `bc164b2e` or say "plus the report commits".
b. §4, item 1: the wrapper does not set `paper.evidence_ready`; the S2-C2 spec does. §5 already says this correctly.

## Verified this round

- HEAD is `0a8ce27c`, and it has exactly two commits on `870b4928`.
- Only the report file changed.
- I checked each new statement in §1, §2 and §4 against the evidence from round 1, and checked the new branch
  locations cited.
- I checked the section numbering and cross-references (§1 → §4; §3 → trial §5; §5 → trial §5a).
