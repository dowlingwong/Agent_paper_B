# B1 restart hand-off for the experiment agent (9 Nov 2026)

**Status.** AI-assisted (Claude, Mac-local overnight agent, `prompts/MAC_OVERNIGHT_RUNBOOK_20261109.md` §1 step 5). The Mac-local agent prepared the R4 fix and the configuration re-pin and had them independently reviewed (`reviews/B1_R4_REVIEW_20261109.md`, three rounds, verdict **accepted** at `ddcf0eaf`). It did **not** set `approved: true`, run the author gate or launch anything. Plan: `proposals/B1_STOP_DIAGNOSIS_PLAN_20261108.md` §§4–5 (branch `docs/b1-stop-diagnosis-08nov`, also on `mac-b1-diag-20261109-c`).

## 0. Precondition — read first

This hand-off is **armed only when all of these hold**; otherwise do nothing and report:

1. The diagnosis capture from `proposals/B1_DIAGNOSIS_HANDOFF_20261109.md` (branch `mac-b1-diag-20261109-c`) has been turned into `reports/B1_STOP_DIAGNOSIS_<date>.md`, a freshly spawned independent reviewer has accepted that report, and it classifies the STOP as **class D with H1 supported** (the two random anchors cannot be ordered).
2. Its D7 line is **PASS**: the 7B duplicate rate lies inside the pinned interval [0.42386590667728663, 0.5800007633587785] (the gate's exact values; 0.4239–0.5800 rounded).
3. PLAN §10 row `R1-EXAM-B1-ANCHOR-R4` is committed on the checkout you restart from (it is on `mac-b1-r4-20261109`).

Not covered, go to the author and do not use this branch: class D resting on H2 alone (metric or orientation), class P, UNCLASSIFIED, or any D7 FAIL. Class E (engineering defect) needs its own fix on `mac-b1-fix-20261109` and its own hand-off.

## 1. The fix and the checkout

- Branch `mac-b1-r4-20261109`, based on `mac-b1-20261107` @ `b06f8a91` (= frozen B1 checkout `68357d3d` plus documentation-only commits).
- `fb57c6a4`: `r1/scripts/exam_runner.py::anchor_gate` no longer raises on `difference_lower ≤ 0`; it records the comparison with `scripted_minus_random_role = descriptive_only (R1-EXAM-B1-ANCHOR-R4; ordering STOP removed post hoc)` in `batch_state.json`. The 7B duplicate-rate STOP and every other STOP are unchanged. Test: `r1/tests/test_exam_b1_batch_verify.py::test_real_anchor_gate_checks_paired_discrimination_and_reference`.
- `4542360e`: `r1/scripts/configs/exam_b1_v2.json` `paper_commit` moves from `f2eccd77` to `fb57c6a4` (one line). The runtime and launcher code-commit guards compare the protected exam paths against `paper_commit`; from `fb57c6a4` to the branch tip that diff is empty, and from `f2eccd77` only `exam_runner.py` differs (`r1/c3/audit.py` and `r1/scripts/b1_host_preflight.py` unchanged). Rule SHA, harness commit `a3fedbb`, value grids, duplicate-rate interval, seeds, nodes and budgets are untouched.
- `746b8019`, `ddcf0eaf`: documentation (PLAN §10 row, RUNBOOK X.3 and PORTAL_EXAM_RUNBOOK Phase 5 notes, appendix draft `reports/B1_GATE_AMENDMENT_DRAFT_20261109.md`, extra tests).
- **Exact checkout to restart from:** the branch commit that adds this file (`git log -1 --format=%H -- docs/r1/proposals/B1_RESTART_HANDOFF_20261109.md` on `mac-b1-r4-20261109`). It adds only this hand-off and the review record on top of the accepted `ddcf0eaf`; check that `git diff --name-only ddcf0eaf <checkout>` lists only `docs/` files. Any later commit on the branch must be reviewed again before use.

## 2. Restart conditions (plan §5), in order

1. Diagnosis report and fix each accepted by a freshly spawned independent agent (§0 and §1).
2. The author's choice is in PLAN §10 (`R1-EXAM-B1-ANCHOR-R4`, on this branch). Line A1 of the 9 Nov runbook §0.4 orders the rerun after review; no further author message is needed for the `paper_commit` re-pin, which is part of the fix (the row says so).
3. **Exact new checkout:** check out the commit of §1 on TASL-7, clean; commit the authorization note re-bound to that HEAD as the `approved: true` candidate (R1-EXAM-B1-NOTE-ORDER-07NOV); have that HEAD independently reviewed; run the real author gate on it.
4. Fresh TASL-7 read-only occupancy check, preflight and handover as for run `6835_20261108_a`; no preemption of other users' work (R1-TASL7-AGENT-OCCUPANCY-07NOV).
5. **New run ID and fresh output tree.** Run ID `⟨first four hex of the new checkout⟩_⟨UTC start date YYYYMMDD⟩_b`, output tree `/home/dowling/exam-x/work/b1_<run ID>`. Nothing of run `6835_20261108_a` is moved, overwritten or deleted (R1-EXAM-B1-NO-DELETION-07NOV); its Track P marker handling stays as recorded in the STOP report.
6. Any further STOP in the new run is preserved and reported, not retried.

B2, X.7 and sweep 2 remain separately gated.

## 3. After the run

The B1 report shows the three anchors descriptively next to the candidates and reads `scripted_minus_random` from `batch_state.json` (it is not in `b1_summary_verified`). The appendix draft's ⟨…⟩ fields are filled from the diagnosis report and this run.

## 4. What to send back

The run ID, the checkout SHA you started, the review of that HEAD, the author-gate receipt, the preflight and handover receipts, and the first monitor capture — the same set as for `6835_20261108_a`.
