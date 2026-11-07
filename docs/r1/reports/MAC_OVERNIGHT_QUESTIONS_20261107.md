# Overnight questions and STOPs — 7 November 2026

AI-assisted (Codex). This is an open list, not author decisions or an authorization. The original overnight instruction was to continue without waiting for the sleeping author; subsequent replies are recorded below. The user's 7 November prompt records Q1, the fixed Q2 rule, conditional B1 approval and scoped host authority in PLAN §10; those are not re-asked here. The earlier independent question list remains `MAC_OVERNIGHT_QUESTIONS_20261105.md`, except where the 7 November decisions resolve its Q0–Q2.

**7 November approximately 09:31 CET update:** The author answered the note-order question below “允许此顺序” and the no-deletion question “继续严格禁止，先修复”. Both are recorded verbatim in PLAN §10 under `R1-EXAM-B1-NOTE-ORDER-07NOV` and `R1-EXAM-B1-NO-DELETION-07NOV`; their original wording is retained below for context and must not be asked again. The authorization candidate remains false until the other prerequisites are ready. Host ownership and M4 ordering remain open.

## B1 approved-note ordering — answered

The options and recommendation in this section are the historical, pre-answer question; the author has now chosen the order stated in the update above.

**Context.** The 7 November prompt §0.3 says to set `approved: true` only when every listed condition holds. Condition 3 already requires a committed, independently reviewed HEAD containing the approved note, and condition 5 requires the real author gate to pass on that HEAD. The gate itself refuses a note unless `approved` is true. Thus, read literally, those conditions cannot all precede setting the field. A synthetic gate or precomputed hash does not satisfy the stated committed-HEAD requirements.

**Options.** (A) After Q2, tests, host checks and the handover procedure are ready, permit committing the approved note as a candidate; independently review that exact HEAD and run its real gate/preflight, then launch only after all listed conditions, including handover, hold. (B) Specify a different order. (C) Keep `approved: false` and defer.

**Recommendation.** A if the author intends this ordering. Until the author clarifies, keep `approved: false`; no simulated pass or elapsed time substitutes for the real final checkout review and gate.

**Paste-ready answer.** `B1 note order: after the other prerequisites are ready, commit the approved note as a candidate; independently review that exact HEAD and run its real author gate and preflight, then launch only when every listed condition and handover is satisfied.`

## No-deletion rule, tests, and the pinned B1 harness — answered

The options and recommendation in this section are the historical, pre-answer question; the author has now chosen strict no-deletion as stated above.

**Context.** At the historical audited checkout the full Mac suite included deletion of test-created files, and the real-worker determinism test invoked audit cleanup. The audit cleanup removal is now independently accepted on the B1 branch (`5f8b8f93`); the full suite and indirect cleanup remain unresolved. The real B1 path calls the exactly pinned harness `a3fedbb`, whose normal governed-trial path attempts to unlink its pending guard (with a truncation fallback) and can remove editable files when restoring state. The instruction says never delete anything, and separately never delete remote files. The reviewed static audit `docs/r1/reports/MAC_FULL_SUITE_NO_DELETION_AUDIT_20261107.md` and audit-fix review are on feature branch `mac-b1-20261107`; other remediation and review remain in progress. Any change to the author-selected harness pin needs a separate author decision; preserving files in a wrapper must also be reviewed for unchanged scientific and safety behavior.

**Options.** (A) Keep both no-deletion rules and the exact harness pin, and defer B1 unless a reviewed compatible solution is found. (B) Keep the no-deletion rules and authorize a specific reviewed replacement harness pin after its behavior and provenance are available. (C) Specify a narrowly bounded exception for deletion of named newly created temporary or test-owned paths, including whether it applies on remote hosts, while retaining protection of experiment data and STOP scenes. These choices require exact artifacts and independent review; none bypasses the remaining launch conditions.

**Recommendation.** A pending the outcome of the current engineering and independent review. If no compatible solution exists, consider B only after a concrete replacement and its effects are reviewed. Do not infer an exception from permission to test or launch.

**Paste-ready answer.** `No-deletion and B1 harness: retain both no-deletion rules and the exact a3fedbb harness pin; defer B1 until a reviewed compatible solution is available.`

## TASL-7 host ownership

**Context.** The 7 November read-only census saw no listed GPU compute app, but `trks_watch` and several other-user agent processes were present. Whether any agent/operator holds the host is not established by that snapshot (`TASL7_READONLY_CENSUS_20261107.md`). The author prohibits touching a host held by another agent/operator, and a fresh preflight and reviewed handover remain required even if the host is free.

**Options.** (A) Identify the current operator/ownership through existing records or a later author-provided handover. (B) Defer host work until ownership is established.

**Recommendation.** B until A is resolved. Do not interrupt or signal any existing process.

**Paste-ready answer.** `TASL-7: I will provide the current operator/host handover; keep host execution on hold until then.`

## M4 ordering versus non-shared parallel work

**Context.** The 7 November prompt asks for M4's non-shared pieces in parallel but says not to start them if they conflict with `MAC_LOCAL_RUNBOOK_20261104.md` §M4. That runbook says M4 starts after M3 is accepted and rebased on its accepted commit; M3 remains not accepted. The non-shared pieces would not edit `r1/scripts/c3_label_sweep.py`, but that does not by itself remove the ordering rule.

**Options.** (A) Keep M4 on hold until M3 is accepted. (B) Explicitly amend the ordering to permit the named non-shared M4 pieces, retaining independent reviews and all phase/host gates. (C) Specify another order.

**Recommendation.** A until the author chooses an amendment; continue M3 and B1 independently. No DTQ host measurement is inferred by either the draft or silence.

**Paste-ready answer.** `M4 ordering: keep M4 on hold until M3 is accepted.`

## Other open decisions

See the independently reviewed `MAC_AUTHOR_QUESTION_RECONCILIATION_20261107.md` for each prior reply and the remaining scope of Q3–Q24 in `MAC_OVERNIGHT_QUESTIONS_20261105.md`. Do not re-ask choices already made: in particular Q5 retains only the operational denominator, timing and missing-outcome handling questions after the author chose a greater-than-20% STOP. Q17 concerns the later Track S GPU manager, not the decided CPU manager or the deferred repeat. The 7 November prompt states a 20 November 12:00 HoreKa freeze; it does not settle the rest of the Q19 package under §0.6. B2 ranking work does not authorize B2; its author note and instance count remain future decisions. Each remaining question keeps its own prerequisites; if another distinct decision is needed, add context, options, recommendation and paste-ready response, with the exact unblock owner and effort in the morning report.
