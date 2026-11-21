# The gate-input builder of the sweep-2 C3 analysis (§3, PRE-MEM C, PRE-DUP A, PRE-DIV A)

Prepared by the Mac-desk agent (Claude), AI-assisted, 21 Nov 2026, for the signed preregistration
(`docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md`, R1-SWEEP2-PREREG) §9. It read no table, label or
evaluation value; the tests use synthetic records only.

- **Module:** `r1/c3/gate_input_builder.py` (sha256 in the review record; that value is the preregistration's
  `gate_input_builder_sha256`). Tests: `r1/tests/test_gate_input_builder.py`.
- **Output:** `r1_d8_gate_input/v3.1` for gate v3.1, checked with the gate's own input validation, plus a report
  of counts (no values). `runs()` returns the three gate inputs of §4 step 6: primary (the seven C3b T0 nodes,
  PRE-DUP primary test population), PRE-DUP secondary (seven nodes, full test population), PRE-WDBC sensitivity (all
  eight, PRE-DUP primary). `build(..., g_units=0.05 | 0.2)` and `build(..., modes=(mode,))` give the descriptive
  g and per-mode runs of PRE-SECONDARY.
- **Inputs:** records of each source (table rows, label-block rows, evaluation-block rows) as the release step's
  partition reader returns them after the test release row, the frozen arms' A3 and A5 predictions per proposal, and
  δ_n / σ_node per node. The builder opens only the pinned P3 split file; the access lock is the reader's (PRE-STAGE A,
  unit 3).
- **Definitions** (module docstring; each quoted from §3 or the decisions): offline_eval's weights and
  `skip_credited_at_g` accounting with the rule layer; A2 = `RulesPrior` on the dev label block (PRE-A2 C); oracle
  from the same proposal's label block, s = σ_node/√k_label; Δ_true from the evaluation block; PRE-DIV A;
  PRE-DUP A; PRE-MEM C; P3 blocks from the split file; seed sets checked per tier (§6).

## Readings the coordinating chat should confirm (none changes a signed decision; each is stated in the code)

1. **A2's fit set** is the full dev label block of the gate sources (PRE-A2 C reads "the dev instances' label block";
   PRE-DUP's primary dev population is stated for selection, PRE-SELECT, not for A2's constants).
2. **PRE-MEM C fallback** is applied in every block whenever a mode has no positive-weight proposal in that block's
   population (in sweep 2 every campaign has proposals, so outside PRE-DUP it does not occur); every fallback is
   reported.
3. **The PRE-WDBC sensitivity run** uses the PRE-DUP primary population (it differs from the primary only in the T0
   node set).
4. **A5's predictions** get the same rule override as A3 (no-op → inert; otherwise no inert mass), so every gate
   series has the rule layer of §3 ("the same rule layer and g as the arms").
5. **A label-divergent proposal** (R1-BX-PROPOSED-CONFIRM REVISIONS (c): no belief bin, action target u = −g) is never
   executed by the oracle.
6. **A T1 node** with no test instance left in a run is not supplied in that run and is reported; a declared T0 node
   without a train, dev or test instance is an input refusal.
7. **Population:** campaign trials without a parsed metric are not table rows (`features.replay_campaign`), so U
   averages over the table's proposals, as `offline_eval`.
8. **Evaluation divergence** is read from a `divergent_seeds` field of the evaluation row. The existing evidence writer
   (`audit.evidence_blocks`) admits only complete 5 + 5 audits, so no sweep-1 evidence row diverges; a sweep-2 B.2
   writer that admits divergent seeds must emit this field (with `delta_evaluation` over the remaining seeds, or null
   when more than half diverge) — a condition for that authorization.
