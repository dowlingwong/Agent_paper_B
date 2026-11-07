# Overnight questions and STOPs — 7 November 2026

AI-assisted (Codex). This is an open list, not author decisions or an authorization. The author is asleep; do not wait for an answer. The user's 7 November prompt records Q1, the fixed Q2 rule, conditional B1 approval and scoped host authority in PLAN §10; those are not re-asked here. The earlier independent question list remains `MAC_OVERNIGHT_QUESTIONS_20261105.md`, except where the 7 November decisions resolve its Q0–Q2.

## M4 ordering versus non-shared parallel work

**Context.** The 7 November prompt asks for M4's non-shared pieces in parallel but says not to start them if they conflict with `MAC_LOCAL_RUNBOOK_20261104.md` §M4. That runbook says M4 starts after M3 is accepted and rebased on its accepted commit; M3 remains not accepted. The non-shared pieces would not edit `r1/scripts/c3_label_sweep.py`, but that does not by itself remove the ordering rule.

**Options.** (A) Keep M4 on hold until M3 is accepted. (B) Explicitly amend the ordering to permit the named non-shared M4 pieces, retaining independent reviews and all phase/host gates. (C) Specify another order.

**Recommendation.** A until the author chooses an amendment; continue M3 and B1 independently. No DTQ host measurement is inferred by either the draft or silence.

**Paste-ready answer.** `M4 ordering: keep M4 on hold until M3 is accepted.`

## TASL-7 host ownership

**Context.** The 7 November read-only census saw no listed GPU compute app, but `trks_watch` and several other-user agent processes were present. Whether any agent/operator holds the host is not established by that snapshot (`TASL7_READONLY_CENSUS_20261107.md`). The author prohibits touching a host held by another agent/operator, and a fresh preflight and reviewed handover remain required even if the host is free.

**Options.** (A) Identify the current operator/ownership through existing records or a later author-provided handover. (B) Defer host work until ownership is established.

**Recommendation.** B until A is resolved. Do not interrupt or signal any existing process.

**Paste-ready answer.** `TASL-7: I will provide the current operator/host handover; keep host execution on hold until then.`

## B1 approved-note ordering

**Context.** The 7 November prompt §0.3 says to set `approved: true` only when every listed condition holds. Condition 3 already requires a committed, independently reviewed HEAD containing the approved note, and condition 5 requires the real author gate to pass on that HEAD. The gate itself refuses a note unless `approved` is true. Thus, read literally, those conditions cannot all precede setting the field. A synthetic gate or precomputed hash does not satisfy the stated committed-HEAD requirements.

**Options.** (A) After Q2, tests, host checks and the handover procedure are ready, permit committing the approved note as a candidate; independently review that exact HEAD and run its real gate/preflight, then launch only after all listed conditions, including handover, hold. (B) Specify a different order. (C) Keep `approved: false` and defer.

**Recommendation.** A if the author intends this ordering. Until the author clarifies, keep `approved: false`; no simulated pass or elapsed time substitutes for the real final checkout review and gate.

**Paste-ready answer.** `B1 note order: after the other prerequisites are ready, commit the approved note as a candidate; independently review that exact HEAD and run its real author gate and preflight, then launch only when every listed condition and handover is satisfied.`

## Other open decisions

The remaining Q3–Q24 in `MAC_OVERNIGHT_QUESTIONS_20261105.md` remain open unless an author row expressly resolves them. B2 ranking work does not authorize B2; its author note and instance count remain future decisions. If another distinct decision is needed, add its context, options, recommendation and paste-ready response here, with the exact unblock owner and effort in the morning report.
