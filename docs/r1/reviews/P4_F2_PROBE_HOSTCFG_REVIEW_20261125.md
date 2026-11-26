Reviewed base: origin/main `912a7e027`; accepted at `c1cf9695d` (code `3546d2cb`), post-acceptance follow-ups confirmed at `5e8a1df0a` (code `8146e9fa`)

# Independent review record — P.4 phase 1 under R1-P4-TESTPLAN-DECISIONS: the F2 runner change (P4-F2 A), the H200 SFT probe mode with its GPU-hour charge against the 40 GPU-h cap (P4-PROBE A, P4-PROBECAP A), the host-config fill hook and the F5 test changes

**Unit.** On `mac-trackp-p4-f2-probe-20261125`: `r1/c3/train/p4_phase1.py`, `r1/scripts/htcondor/trackp_p4/` (`p4_lib.py`, `p4_render_jdl.py`,
`p4_switch.py`, `p4_spec.json`, new `p4_probe.sh`, `p4_probe_spec.json`, `p4_fill_host_config.py`), `r1/tests/test_trackp_p4_runner.py`,
`r1/tests/test_trackp_sft.py` (one assertion), the phase-1 note draft (`approved: false`), the report
`docs/r1/reports/trackp_p4_runner_20261122/P4_F2_PROBE_HOSTCFG_20261125.md`, dated status markers in the cluster test plan and a dated section
in the runner report. Authority: R1-P4-TESTPLAN-DECISIONS (P4-F2 A, P4-PROBE A, P4-PROBECAP A), R1-C3-SWEEP1-LABELS-FROZEN; the queue of
25 Nov 2026 (12:43), item 2.

**Process.** One independent reviewer for all rounds, read-only, synthetic data only, no label, evaluation, sealed or secrets file opened,
scratch moved to its `_to_delete/`. F2, probe safety, F3/F4, the fill hook and F5 were sound from round 1; every round's findings were in
the probe's GPU-hour accounting and probe selection: round 1 the charge was a snapshot and submissions were unrecorded; round 2 the wall-clock
charge exceeded what the launch check re-derived; round 3 a probe attempt sealed into a recorded run deadlocked the launch; round 4 the new
"lowest-numbered attempt" rule let seal order choose the probe run; round 5 accepted with three minors and two nits, fixed and confirmed.

**Full suite** (author, default options, lightgbm absent, one run at a time): base `912a7e02` 58 failed, 3972 passed, 197 skipped, 3 errors;
code tip `8146e9fa` 58 failed, 4028 passed, 197 skipped, 3 errors; `FULLSUITE_BASE_912a7e02.txt` = `FULLSUITE_F2_PROBE_TIP_R5.txt` (61 entries,
the standard list).

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `51860ca3` | NOT ACCEPTED (M1 charge snapshot, M2 unrecorded submissions; minors 1–6) |
| 2 | `1d51c578` | NOT ACCEPTED (R2-M1 wall-clock gap; R2-m1, R2-m2) |
| 3 | `4706de7d` | NOT ACCEPTED (R3-M1 launch deadlock; R3-m1 charge file unbound) |
| 4 | `04541704` | NOT ACCEPTED (R4-M1 seal order chose the probe run) |
| 5 | `c1cf9695` | ACCEPTED (three minors, two nits) |
| 6 | `5e8a1df0` | CONFIRMED |

**Open items for the author** (report §6, §7): P4-T1CHARGE (A: add T1's RemoteWallClockTime to the probe charge, the reviewer's
recommendation, `probe-record --t1-wallclock`; B: leave it out, as built); P4-EXTRAPROBE (A as built: the record uses the first STOP-free attempt
by submission order and lists extras, charged; B: any extra refuses the record); a killed probe attempt is charged its 7200 s walltime or its
RemoteWallClockTime, whichever is larger; signing the note ratifies the F2 binding through `label_table_binding:`. Before the probe: T1 (F3),
the v2.2 run-record review (F8), the host-config fill commit (T3) with `p4_fill_host_config.py`.

## Round 1 (`51860ca3`)

> ## Round 1, `51860ca3` (on `912a7e02`): NOT ACCEPTED
>
> Two MAJOR findings, both in the probe cap accounting; nothing BLOCKING. F2, probe safety, F3/F4, the fill hook and F5 are sound.
>
> ### Confirmed
> - Tests one file at a time: `test_trackp_p4_runner` 119, `test_trackp_sft` 35, `test_trackp_sft_test_eval` 48, `test_trackp_p3` 23 passed. Full-suite lists byte-identical (61 lines).
> - F2 matches A3: `check_receipt_table` calls `arms_freeze.require_feat_one` with `train-a3`'s arguments (`arms_freeze.py:1198`); identity file sha256 `039b8360…53df` = A3 `SHA256SUMS:45` and `RUN_I.md` command 1; the join uses A3's `load_traindev`, `load_table_rows`, `training_rows`, same `p3_split`, `t1=None`; only duplicates and test rows are skipped, every other mismatch is an `ArmsFreezeError`; STOP messages carry ids only. `LabelBlockSource` tolerates the v2 receipt table.
> - Only callers: `inputs` (step 5) and the render's `check_inputs`; no path accepts a v3-pin receipt (S9 holds). Pins `cdae9c3f`, `d0048567`, `f06e37a9`, `6a6327a3` bind; the published receipt passes with the real pins; freeze record, PLAN, `arms_freeze.py`, configs untouched.
> - Adversarial synthetic checks refused: v3-pin receipt, no `inputs`, table = sealed table, other table, missing/symlinked/modified identity file; filled probe spec at launch strength, launch spec at probe strength, launch spec with a probe block; template deviations (steps 51, extra key, run id, sft sha, layout, arms, filled `caps.probe_gpu_hours`). `ceil_hundredth` correct.
> - F3: NEMO2 record `i3_identity.txt:54-55` shows full `GPU-…` UUIDs, so `visible_devices` checks the form seen.
> - Fill hook: 19 `EXPECTED` paths = `run.placeholders`; local paths forced to `models/<key>`; `hf_home`/`models_dir`/`runs_dir` forcing correct; round-trip reproduces the committed file byte for byte.
> - `verify_launch_p4` unchanged is correct per §5.1 and §6 steps 4 and 9. Records: `approved: false`, new fields rendered, no cluster result claimed; the `RUN_I.md` disclosure accurate and acceptable.
>
> ### MAJOR
> - **M1.** The probe charge is a snapshot: `check_cap` (`p4_switch.py:282`), `charged_hours` (`p4_lib.py:1322-1343`) and `assemble` (`p4_lib.py:1416`) use only `caps.probe_gpu_hours`, bound to the hand-written note line, not to the sealed tree. Probe attempts sealed after `probe-record`, or a line typed lower, are never charged (demonstrated: 2.4 charged while `probe_charges` showed 4.3). Fix: compute `ceil_hundredth(probe_charges(sealed_root)["total"])` in `check_cap` and `assemble` and STOP if it exceeds the spec value; add a test.
> - **M2.** A probe submission is recorded nowhere (`p4_render_jdl.py:202` `stage_probe`; `p4_lib.py:1141` `probe_charges`): a held/removed probe job never sealed is omitted from P. Fix: `stage_probe` appends to `<sealed_root>/<probe run id>/_submissions.jsonl`; `charged_hours` prices pending entries at `probe.walltime_s`; `probe-record` refuses while anything is pending; runbook: one `condor_submit` per stage directory.
>
> ### minor
> 1. `p4_lib.py:1081`: GPU-hours counted from Python start; container start, pull, transfer omitted; killed-attempt charge assumes exactly `RequestWalltime`. Fix: `probe-record` takes `condor_history` wall times and charges the larger per attempt.
> 2. `p4_lib.py:1260` `seal` cannot tell a killed probe from a killed P.4 job (charged 1.745 h instead of 2 h; offsets the P.4 ledger count). Fix: check the `p4_run.log` header against the spec kind, or a mode marker.
> 3. F5 filled-state test (`test_trackp_p4_runner.py:1487-1524`, `_placeholder_host_config` :2014) checks only the 19 values; a fill that also changes another key passes. Fix: restore the 19 placeholders (full original `causal_conv1d` text) and assert sha256 = `18f18cfc…`.
> 4. `stage_probe` has no pre-submit binding (checkout `p4_lib.py`/template vs `paper.commit`, `host_config.sha256`, `paper.commit` on `origin/main`); the job catches each only after it starts, and the STOP attempt is charged.
> 5. `p4_render_jdl.py:168` `render_probe` copies `render()`'s fixed lines; derive or test equality.
> 6. Test-plan status note says "the text below is unchanged" though F1, F2, F5, F7 got inline markers; reword.
>
> ### nit
> `p4_switch.py:147` several `probe_gpu_hours:` values pass if one matches; `probe_run_summary` (`p4_lib.py:971`) does not check lr/seed/train keys; note draft lines 61 and 100 wording ("non-inert, non-duplicate train/dev row"); fill-hook `_paths` ambiguity check can never fail; report §5 step 6 should say the filled probe spec copy goes under `docs/`; per-attempt rounding to 4 decimals before the ceiling (negligible); `p4_probe.sh` not bound to the clone.
>
> ### Author decision points
> T1 not charged: recommend adding T1's `RemoteWallClockTime` to P (author decides). 7200 s per killed attempt fine (see minor 1). Forced `hf`/`models`/`out`: agree. Signing ratifies the binding: fine. All probe runs summed: agree. STOP classes: fine.

## Round 2 (`1d51c578`)

> ## Round 2, `1d51c578` (code `45575c52`): NOT ACCEPTED
>
> One MAJOR left: `--wallclock` raises the recorded charge above what the launch-time check re-derives, and a small later attempt fits in that gap. Every other round-1 finding is fixed and verified; 2 new minors, 3 nits.
>
> ### Verified
> - Tests one file at a time: `test_trackp_p4_runner` 126, `test_trackp_sft` 35, `test_trackp_sft_test_eval` 48, `test_trackp_p3` 23 passed; `FULLSUITE_F2_PROBE_TIP_R1.txt` byte-identical to the base list.
> - M2 fixed (ledger entry only after the checks pass; pending priced at 7200 s; `probe-record` refuses while pending). m1 fixed (required; larger of receipt and wall clock; exact attempt set). m2 fixed (both directions refused; first header wins; pre-header STOP needs confirmation). m3 fixed (`18f18cfc…`). m4 fixed and fails closed offline (no or unreachable origin, stale `origin/main`, unpublished commit, mismatched files, wrong host sha; nothing staged on refusal). m5, m6, nits fixed. The changed killed-job tests still test the same thing. Unknown kind cannot under-charge an attempt with no readable record.
>
> ### MAJOR
> - **R2-M1.** `check_probe_ledger` re-derives from receipts only, while the recorded P uses max(receipt, wall clock) plus optional T1; the difference hides a later small attempt (demonstrated: P 0.60 from a 0.30 h receipt / 0.60 h wall clock; a later 0.25 h attempt re-derives 0.55 ≤ 0.60 and passes; true ≥ 0.85). Fix: `probe-record` writes the charges it used write-once into the sealed tree (e.g. `<sealed_root>/<probe run>/_wallclock.json`, with T1 if charged), sha256 bound in `probe_records.json`; `probe_charges()` applies it by default; test this case.
>
> ### minor
> - **R2-m1.** Unknown kind with a readable record of neither schema charges the record's own `gpu_hours` (0.01 h demonstrated). Fix: charge max(record `gpu_hours`, walltime).
> - **R2-m2.** The documented never-submitted-stage path over-charges (10.46 h for a 4B base in the 8× case). Fix: recognise a probe stage directory (`STAGE_MANIFEST.json`, schema `trackp_p4_probe_stage/1`, mode `probe`) as kind `probe` (2 h), or a dedicated path backed by `condor_history`.
>
> ### nit
> `TimeoutExpired` from `ls-remote`/`git show` not wrapped as a Stop; `stage_probe` appends the ledger after writing the stage (append first or remove on failure); killed-job test comment about empty pre-created files is stale.

## Round 3 (`4706de7d`)

> ## Round 3, `4706de7d` (code `493122fc`): NOT ACCEPTED
>
> One MAJOR: the new STOP on unrecorded probe attempts creates an unclearable launch deadlock; the documented way out does not clear it. Fails closed. Other round-2 fixes verified; 1 minor, 2 nits.
>
> ### Verified
> - Tests one file at a time: `test_trackp_p4_runner` 131, `test_trackp_sft` 35, `test_trackp_sft_test_eval` 48, `test_trackp_p3` 23 passed; `FULLSUITE_F2_PROBE_TIP_R2.txt` byte-identical to the base list.
> - R2-M1 gap closed: charge file applied by default; re-derived = P right after the record; a later attempt is `unrecorded` and `check_probe_ledger` STOPs; pending STOPs; wall clock for a run with a charge file STOPs; T1 twice STOPs; write-once. R2-m1, R2-m2 and nits fixed. Remove-on-failure never deletes a non-empty stage.
>
> ### MAJOR
> - **R3-M1.** A probe attempt sealed into an already-recorded probe run (the template fixes run id X; `stage_probe` does not refuse a run with `_wallclock.json`) can never be recorded: `check_probe_ledger` STOPs; naming X in the wall-clock input STOPs; omitting X leaves it unrecorded and the CLI refuses; the report's recovery ("rebuilt under a new probe run", §5 line 264) does not help (demonstrated). Only exit is hand-editing the sealed tree, and an edit is not detected (R3-m1). Fix: `stage_probe` refuses a run with a charge file; docs say a re-probe needs a new template run id (reviewed commit); add a recovery path (e.g. `probe-charge` writing write-once `_wallclock.<n>.json` for exactly the unrecorded attempts, applied by `probe_charges`, then a rebuilt record); test re-probe-after-record end to end.
>
> ### minor
> - **R3-m1.** Nothing at launch checks the charge file is unchanged: its sha256 is bound only in `probe_records.json`, which nothing binds; `check_probe_ledger` re-reads the live file (demonstrated: zeroed file passes, limited only by the receipt floor). Fix: record prints `p4_probe_charge_file: <run> <sha256>` lines checked by the switch; better, carry them in the spec (`caps.probe_charge_files`) so `check_probe_ledger` STOPs on a changed, missing or unlisted file.
>
> ### nit
> 1. `stage_probe` remove-on-failure removes a pre-existing empty stage directory; a symlinked empty stage directory makes `shutil.rmtree` raise from inside the handler, leaving staged files without a ledger entry (not a Stop). Refuse symlinked `stage_dir`; remove only files this call wrote.
> 2. `probe-record` writes charge files before `probe_records.json`; document the re-run sequence.

## Round 4 (`04541704`)

> ## Round 3 (fixes), `04541704` (code `5562a5cd`): NOT ACCEPTED
>
> One MAJOR, from this round's new rule; the R3 fixes and the whole charge chain are otherwise sound, no under-count found.
>
> ### Verified
> - Tests one file at a time: `test_trackp_p4_runner` 138, `test_trackp_sft` 35, `test_trackp_sft_test_eval` 48, `test_trackp_p3` 23 passed; `FULLSUITE_F2_PROBE_TIP_R3.txt` byte-identical to the base list.
> - Charge chain traced end to end on a synthetic sealed tree (probe → record → `probe-charge` → rebuilt record → spec fill → note → switch → every submission): re-derived = P after the record; a later attempt charged at least its receipt via `_wallclock.1.json`; old spec STOPs (files differ from `caps.probe_charge_files`); listing updated but old P kept STOPs; rebuilt passes; edited/deleted/gapped supplements STOP; symlinked or misnamed files refused; staging into a recorded run refused; switch binds record lines, spec and note exactly; `check_cap` and `assemble` call `check_probe_ledger`. T1 twice STOPs; T1 only at rebuild over-charges, never under. `caps.probe_charge_files` placeholder accepted at default strength, refused at launch; F5 requires the three probe fields filled together.
> - R3-M1 (a)(b)(c) and R3-m1 fixed; nits fixed.
>
> ### MAJOR
> - **R4-M1.** "Lowest-numbered STOP-free attempt" lets the operator pick which probe run of a base the record uses: attempt numbers follow seal order (`p4_lib.py:1597`), and `stage_probe` allows a second stage of the same base while the first is pending (demonstrated: two stages of kev-0.8b, two ledger lines). Submit both, read both job records, seal the preferred one first. Breaks "never chosen by result" and P4-PROBE A's one run per base (chooses `s_per_step_wall`, hence `estimate.hours` and walltimes, and memory headroom). Fix: `stage_probe` refuses a base with a pending submission or a sealed STOP-free attempt in the run; define "first" by submission order (`ClusterId`, falling back to ledger order; refuse when unorderable); list later STOP-free attempts in the record (`extra_stop_free_attempts`); test the two-stage case.
>
> ### nit
> `test_switch_submit_needs_both_keys_the_binding_and_the_first_arm` (~1378): the passing counterfactual is now arithmetic only (not weakened in substance); a ledger line cut mid-write raises `ValueError` rather than a Stop (still fails closed).

## Round 5 (`c1cf9695`)

> ## Round 4 (fixes), `c1cf9695` (code `3546d2cb`): ACCEPTED
>
> R4-M1 is closed: seal order cannot choose which probe run of a base is used, and the rule holds without editing the record or the spec. The R3 recovery path and the charge chain are intact. Three minors (follow-ups), two nits.
>
> ### Verified
> - Tests one file at a time: `test_trackp_p4_runner` 142, `test_trackp_sft` 35, `test_trackp_sft_test_eval` 48, `test_trackp_p3` 23 passed; `FULLSUITE_F2_PROBE_TIP_R4.txt` byte-identical to the base list.
> - (a) `stage_probe` refuses a base with a pending submission or a sealed STOP-free attempt; the only remaining route to two STOP-free attempts is submitting one stage twice. (b) `submission_order`: ClusterId 300 sealed first, 200 second → record uses 200; two schedds → ledger order; the same output sealed twice → STOP. (c) `extra_stop_free_attempts` listed; agree with leaving P4-EXTRAPROBE B unbuilt. Recovery path and `check_probe_ledger` unchanged in substance. Round-4 nits fixed.
>
> ### minor
> 1. The ClusterId used for ordering is not bound to anything the operator cannot edit (`job_record.json` and `SHA256SUMS` are writable before sealing); the `--wallclock` `cluster_id` is never compared with the record's `condor.ClusterId`, so a wall clock pasted against the wrong attempt goes unnoticed. Fix: STOP in `probe_charges` and `supplement_charges` on a mismatch.
> 2. A clean result can be made to look like a killed job (blank record and SUMS, non-empty `out.tar`, log ending "P4 probe container job end … rc=0" → sealed as "no readable job record", re-staging allowed). Fix: `seal` refuses an unreadable record when the log has the wrapper's end line with `rc=0`.
> 3. A missing `GlobalJobId` counts as the same schedd (`_cluster` gives `""`). Require a non-empty schedd before ordering by ClusterId.
>
> ### nit
> - `seal` could refuse a second seal of the same output (same `job_record_sha256` already in the arm).
> - (Pre-existing) the switch binds the probe record's Markdown lines, not `probe_records.json`; worth a sentence in the record's prose.

## Round 6 (`5e8a1df0`)

> ## Confirmation round, `5e8a1df0` (code `8146e9fa`): CONFIRMED
>
> All five round-5 follow-ups are in place; the diff contains nothing beyond them. One nit, no change required.
>
> - `git diff c1cf9695 5e8a1df0`: code only in `p4_lib.py` — `check_cluster` (wall-clock path of `probe_charges`, every charge-file entry, `supplement_charges`); `CLEAN_END`/`clean_exit_logged` and the refusal in `seal`; `_cluster` returns nothing for an empty schedd; the double-seal refusal; `binding_note` in `probe_records.json`. Docs: report §5 step 6 and §7 "Round 5", one runner-report paragraph, the new full-suite list. Tests: `_wc` fixtures carry matching ClusterIds; the double-seal test expects the refusal.
> - Rule 2 does not block genuinely killed or STOPped jobs (no end line → sealed at 2.0 h; `rc=2` sealed; `rc=20` sealed; only `rc=0` with a lost or blank record refused).
> - "Unverifiable" only when the sealed attempt's record has no `condor.ClusterId`; a record with ClusterId 200 STOPs on a missing or 201 wall-clock id; integer 200 matches "200".
> - Rule 3 falls back to the ledger; rule 4 refuses a readable record already sealed in the arm.
> - Tests one file at a time: `test_trackp_p4_runner` 145, `test_trackp_sft` 35, `test_trackp_sft_test_eval` 48, `test_trackp_p3` 23 passed; `FULLSUITE_F2_PROBE_TIP_R5.txt` byte-identical to the base list.
> - nit: a readable probe-schema record with `condor: None` is "unverifiable" rather than refused (arises only outside HTCondor).

---

Code-Commit: 8146e9fa
Verdict: ACCEPTED

Accepted 25 Nov 2026.
