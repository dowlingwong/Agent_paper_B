# The gate-input builder of the sweep-2 C3 analysis (§3, PRE-MEM C, PRE-DUP A, PRE-DIV A)

Prepared by the Mac-desk agent (Claude), AI-assisted, 21 Nov 2026, for the signed preregistration
(`docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md`, R1-SWEEP2-PREREG) §9. It read no table, label or
evaluation value; the tests use synthetic records only, and their expected utilities are computed by hand with
`labels`/`rules`, without the builder's code.

- **Module:** `r1/c3/gate_input_builder.py` (sha256 in the review record; that value is the preregistration's
  `gate_input_builder_sha256`). Tests: `r1/tests/test_gate_input_builder.py`.
- **Output:** `r1_d8_gate_input/v3.1` for gate v3.1, checked with the gate's own input validation, plus a report
  of counts (no values). `runs(..., primary_t0=...)` returns the three gate inputs of §4 step 6: primary (the T0 set
  of the arms-frozen record: the seven C3b nodes, or all eight if the C3b rerun gives 8/8), PRE-DUP secondary (same T0
  set, full test population) and PRE-WDBC sensitivity (all eight, PRE-DUP primary; flagged when it equals the
  primary). `build(..., g_units=0.05 | 0.2)` and `build(..., modes=(mode,))` give the descriptive g and per-mode runs
  of PRE-SECONDARY.
- **Inputs:** the records of `sweep2` (T0 gate source), `g5` (T1 gate source) and `sweep1` (T0 repeat keys only,
  required for T0) as the release step's partition reader returns them after the test release row; the frozen arms'
  A3 and A5 predictions per proposal; δ_n / σ_node per node. The builder opens only the pinned P3 split file; the
  access lock is the reader's (PRE-STAGE A, unit 3).
- **Definitions** (module docstring; each quoted from §3 or the decisions): offline_eval's weights (all 1 on the
  complete evidence population, which the builder enforces) and `skip_credited_at_g` accounting with the rule layer;
  A2 = `RulesPrior` on the dev label block (PRE-A2 C); oracle from the same proposal's label block,
  s = σ_node/√k_label; Δ_true from the evaluation block; PRE-DIV A; PRE-DUP A; PRE-MEM C; P3 blocks from the split
  file; seed sets checked per tier (§6).

## Readings the coordinating chat should confirm (none changes a signed decision; each is stated in the code)

1. **A2's fit set** is the full dev label block of the gate sources (PRE-A2 C reads "the dev instances' label block";
   PRE-DUP's primary dev population is stated for selection, PRE-SELECT, not for A2's constants). A supplied node with
   no labelled non-inert dev proposal has no A1 constant and is refused (no pooled cross-node fallback).
2. **PRE-MEM C's fallback** applies only where the text puts it: in the test block of the PRE-DUP primary run, when
   PRE-DUP leaves a mode of an instance without proposals. Anywhere else an instance with rows but a declared mode
   without rows is refused; every fallback and left-out instance is reported.
3. **The PRE-WDBC sensitivity run** uses the PRE-DUP primary population (it differs from the primary only in the T0
   node set).
4. **A3 and A5** are used as their frozen arms output them, with only §3's rule layer added (a no-op gets the inert
   belief; within-campaign duplicates are not executed). A5's own decision layer (any inert-mass handling,
   calibration) is part of the frozen arm and recorded in the arms-frozen record; the builder does not alter it.
5. **A label-divergent proposal** (R1-BX-PROPOSED-CONFIRM REVISIONS (c): no belief bin, action target u = −g) is never
   executed by the oracle.
6. **A T1 node** of the frozen set with no rows, without a train or dev instance (PRE-T1), or without a test instance
   left in a run is not supplied in that run and is reported. A declared T0 node without a train, dev or test
   instance is an input refusal.
7. **Population:** campaign trials without a parsed metric are not table rows (`features.replay_campaign`), so U
   averages over the table's proposals, as `offline_eval`. The evidence population is complete: a gate-source
   non-inert, non-duplicate proposal without its label or evaluation row, or a label row with an `audit_reason`, is
   refused rather than dropped.
8. **Evaluation divergence** is read from `divergent_seeds` with `k_evaluation` (both or neither). The existing evidence
   writer (`audit.evidence_blocks`) admits only complete 5 + 5 audits; a sweep-2 or G.5 writer that admits divergent
   seeds must emit both fields (with `delta_evaluation` over the remaining seeds, or null when more than half
   diverge) — a condition for that authorization.
9. **PRE-DUP drops no-ops and within-campaign duplicates too** when their key repeats (the text: "test proposals whose
   key occurs …"); their r is 0 for every series, but dropping them changes the instance's denominator.

## Conditions that are author matters if they occur (input refusals that no fix can remove)

- PRE-DUP empties a declared T0 node's test block (every test instance left out).
- A supplied node has no labelled non-inert dev proposal (no A1 constant under PRE-A2 C).
