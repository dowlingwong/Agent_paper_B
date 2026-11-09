# B1 restart hand-off for the experiment agent (9 Nov 2026)

**Status.** AI-assisted (Claude, Mac-local overnight agent, `prompts/MAC_OVERNIGHT_RUNBOOK_20261109.md` §1 step 5). The Mac-local agent prepared the R4 fix and the configuration re-pin and had them independently reviewed (`reviews/B1_R4_REVIEW_20261109.md`, three rounds, verdict **accepted** at `ddcf0eaf`). It did **not** set `approved: true`, run the author gate or launch anything. Plan: `proposals/B1_STOP_DIAGNOSIS_PLAN_20261108.md` §§4–5 (branch `docs/b1-stop-diagnosis-08nov`, also on `mac-b1-diag-20261109-c`).

## 0. Precondition — read first

This hand-off is **armed only when all of these hold**; otherwise do nothing and report:

1. The diagnosis capture from `proposals/B1_DIAGNOSIS_HANDOFF_20261109.md` (branch `mac-b1-diag-20261109-c`) has been turned into `reports/B1_STOP_DIAGNOSIS_<date>.md`, a freshly spawned independent reviewer has accepted that report, and it classifies the STOP as **class D with H1 supported** (the two random anchors cannot be ordered): check the report's class and its H1 line yourself. Do not rely on any summary field such as `r4_applicable_under_A1` alone.
2. Its D7 line is **PASS**: the 7B duplicate rate lies inside the pinned interval [0.42386590667728663, 0.5800007633587785] (the gate's exact values, from `job.authority_config`). If the report's D7 label and a check against these exact bounds disagree, go to the author.
3. PLAN §10 row `R1-EXAM-B1-ANCHOR-R4` is committed on the checkout you restart from (it is on `mac-b1-r4-20261109`).

Not covered, go to the author and do not use this branch: class D resting on H2 alone (metric or orientation), class P, UNCLASSIFIED, or any D7 FAIL. Class E (engineering defect) needs its own fix on `mac-b1-fix-20261109` and its own hand-off.

## 1. The fix and the checkout

- Branch `mac-b1-r4-20261109`, based on `mac-b1-20261107` @ `b06f8a91` (= frozen B1 checkout `68357d3d` plus documentation-only commits).
- `fb57c6a4`: `r1/scripts/exam_runner.py::anchor_gate` no longer raises on `difference_lower ≤ 0`; it records the comparison with `scripted_minus_random_role = descriptive_only (R1-EXAM-B1-ANCHOR-R4; ordering STOP removed post hoc)` in `batch_state.json`. The 7B duplicate-rate STOP and every other STOP are unchanged. Test: `r1/tests/test_exam_b1_batch_verify.py::test_real_anchor_gate_checks_paired_discrimination_and_reference`.
- `4542360e`: `r1/scripts/configs/exam_b1_v2.json` `paper_commit` moves from `f2eccd77` to `fb57c6a4` (one line). The runtime and launcher code-commit guards compare the protected exam paths against `paper_commit`; from `fb57c6a4` to the branch tip that diff is empty, and from `f2eccd77` only `exam_runner.py` differs (`r1/c3/audit.py` and `r1/scripts/b1_host_preflight.py` unchanged). Rule SHA, harness commit `a3fedbb`, value grids, duplicate-rate interval, seeds, nodes and budgets are untouched.
- `746b8019`, `ddcf0eaf`: documentation (PLAN §10 row, RUNBOOK X.3 and PORTAL_EXAM_RUNBOOK Phase 5 notes, appendix draft `reports/B1_GATE_AMENDMENT_DRAFT_20261109.md`, extra tests).
- **Reviewed base:** the commit on `mac-b1-r4-20261109` that records the accepted review of this hand-off in `reviews/B1_R4_REVIEW_20261109.md` (its Status line names the accepted rounds): `git log -1 --format=%H -- docs/r1/reviews/B1_R4_REVIEW_20261109.md`. Its SHA is also given in `reports/MAC_OVERNIGHT_REPORT_20261110.md`. Check that the remote branch tip equals that SHA and that `git diff --name-only ddcf0eaf <base>` lists only `docs/` files. **Any commit after the base must be independently reviewed again before use.**
- **Run HEAD (the exact checkout):** one new commit on top of the reviewed base, on a new branch `ops-b1-restart-<YYYYMMDD>` that you push (no force) to the Paper B remote, as in the 6835 precedent (`68357d3d`, "Update B1 candidate note inventory status"). It changes **only the prose** of `docs/r1/authorizations/trackx_b1_20261105.md`: name the R4 restart, the stopped run `6835_20261108_a`, the reviewed base commit and this hand-off; the JSON bindings stay byte-identical. That commit is the HEAD that gets the exact-HEAD review and the real author gate, whose first four hex give the run ID, and whose SHA you report back. The note inherited unchanged from `68357d3d` refers to run 6835 and must not be used as is.
- Fetch: `mac-b1-r4-20261109` and `mac-b1-diag-20261109-c` are not on the remote yet (the overnight agent had no push credentials); the author pushes them from the Mac in the morning. Use only the remote copies, with these commit SHAs.

## 2. Restart conditions (plan §5), in order

1. Diagnosis report and fix each accepted by a freshly spawned independent agent (§0 and §1).
2. The author's choice is in PLAN §10 (`R1-EXAM-B1-ANCHOR-R4`, on this branch). Line A1 of the 9 Nov runbook §0.4 orders the rerun after review; no further author message is needed for the `paper_commit` re-pin, which is part of the fix (the row says so).
3. **Exact new checkout:** create the run-HEAD note commit of §1 (the `approved: true` candidate ordering of R1-EXAM-B1-NOTE-ORDER-07NOV); have that HEAD independently reviewed; check it out clean on TASL-7; run the real author gate on it.
4. Fresh TASL-7 read-only occupancy check, host preflight (`proposals/B1_FINAL_HOST_PREFLIGHT_INVOCATION_20261108.md`) and handover (`proposals/B1_TASL7_O2_EXECUTABLE_DRAFT_20261107.md` with its command boundary `reports/B1_TASL7_HANDOVER_COMMAND_BOUNDARY_20261107.md`), re-reviewed for the new HEAD and run ID; STATUS published on `mac-b1-20261107` as R1-EXAM-B1-STATUS-FEATURE-07NOV requires; no preemption of other users' work (R1-TASL7-AGENT-OCCUPANCY-07NOV).
   **Track P marker transition.** Run 6835's `~/r1_locks/trackx_evidence.active` (dev 66306, inode 56261609, SHA-256 `092023e4…a1af`) is still present, and `b1_o2_marker.py create` uses exclusive create, so a new handover fails while it exists. The STOP report's "do not retire the marker" protects the stopped scene until a restart is authorized; the restart that line A1 orders needs the marker for the new run. Procedure: confirm the P.3a safe pause **before** `retire` (if it cannot be confirmed, do not retire, and STOP); keep Track P paused throughout; retire the old marker with `b1_o2_marker.py retire` and its recorded creation receipt (the reviewed tool renames it into `~/r1_locks/_to_delete/` with `renameat2`, nothing is deleted); keep the old receipt and the retirement receipt with the run-6835 evidence; then create the new marker in the new handover and keep its receipt. If the old marker does not match its receipt, STOP and report. The PLAN row records that A1 covers this transition.
5. **New run ID and fresh output tree.** Run ID `⟨first four hex of the new checkout⟩_⟨UTC start date YYYYMMDD⟩_b`, output tree `/home/dowling/exam-x/work/b1_<run ID>`. Nothing else of run `6835_20261108_a` is moved, overwritten or deleted (R1-EXAM-B1-NO-DELETION-07NOV); its Track P marker is only retired as in step 4, with both receipts kept.
6. Any further STOP in the new run is preserved and reported, not retried.

B2, X.7 and sweep 2 remain separately gated.

## 3. After the run

The B1 report shows the three anchors descriptively next to the candidates and reads `scripted_minus_random` from `batch_state.json` (it is not in `b1_summary_verified`). The appendix draft's ⟨…⟩ fields are filled from the diagnosis report and this run.

## 4. What to send back

The run ID, the checkout SHA you started, the review of that HEAD, the author-gate receipt, the preflight and handover receipts, and the first monitor capture — the same set as for `6835_20261108_a`.
