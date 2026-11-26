# The fold-analysis module of the sweep-2 C3 analysis (PRE-SECONDARY A)

Prepared by the Mac-desk agent (Claude), AI-assisted, 21 Nov 2026, for the signed preregistration
(`docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md`, R1-SWEEP2-PREREG) §9 and PRE-SECONDARY A. It read no table,
label or evaluation value; the tests use synthetic records (the statistics tests run only under NumPy 2.4.4).

- **Module:** `r1/c3/fold_analysis.py`. Tests: `r1/tests/test_fold_analysis.py`. Output schema `r1_c3_fold_statistics/v1`.
- **Leave-one-suite-out:** per suite of `gate.SUITES`, the IQM and PoI over that suite's labelled T1 nodes with the fold's
  arms. The labelled T1 nodes are the T1 nodes of the §4 step-6 primary gate input (the gate's own
  `t1_suites_without_labelled_node` notion). It STOPs before any statistic if a suite has none (R1-BX-D8-CONFIRM).
- **Leave-one-node-out within T0:** per node of the primary input's declared T0 set, its gap closed and PoI with the fold's
  arms.
- **Secondary recomputes:** g = 0.05 and 0.2 σ_node, and per memory mode.
- **How:**
  - Each fold input comes from the accepted gate-input builder on the fold's node subset, with the fold arms' predictions
    as A3/A5.
  - Every fold node's instances, A2 and oracle blocks are checked equal to the primary input's. This binds each fold to the
    step-6 input and its validation.
  - All fold inputs are built and checked before any statistic is computed. Each fold node's `delta_n`, suite and tier must
    also match the primary input's. The primary input must declare the arms-frozen record's T0 set (`primary_t0`), so the
    PRE-WDBC sensitivity input cannot stand in for it, and it must pass the gate's own input validation.
  - Errors: `FoldStop` is only leave-one-suite-out's declared STOP. Every other refusal is a `FoldInputError` (an input
    refusal under §4: fixed and the run repeated).
  - When the IQM is undefined, the per-node fields of the gate's validation and the node counts are still reported; otherwise
    the gate's `tier_descriptive` is reported too.
  - Statistics come from gate v3.1's own functions (`_validate`, `_point`, `_bootstrap`, `_lower_iqm`, `_lower_poi`,
    `_node_poi`), after its D8 check and NumPy pin. There is no Holm step and no verdict.

## Readings the coordinating chat should confirm

1. **A2 and the oracle are not fold arms.** A2 keeps PRE-A2 C's constants from the node's own dev label block, and the oracle
   its label-block belief; a fold changes only A3 and A5. (The gate's ARMS are A3 and A5; PRE-POOL applies to A3 and A5; A2
   cannot be refitted without its own node except through a pooled fallback, which PRE-A2 C excludes.)
2. **Population and g.** Folds use the PRE-DUP primary test population and g = 0.1 σ_node.
3. **Leave-one-node-out node set.** It runs over the primary input's T0 set (seven, or eight after an 8/8 C3b rerun). An
   openml_wdbc fold could be added as a sensitivity row if wanted.
4. **"Labelled T1 node"** means a T1 node of the step-6 primary gate input.
5. **Per-mode runs.** T1 nodes enter only the per-mode run of their declared mode(s) (G5-MEM).
6. **Fold arm selection.** Fold arms are selected by PRE-SELECT on the fold's dev instances, meaning the dev instances of the
   fold's training nodes, in the arms pipeline; this module takes their predictions as given.

## Proposed author decisions (implemented as recommended, pending confirmation)

**FOLD-POI — a fold whose IQM is undefined** (no IQM-eligible node, or a nonpositive test denominator on an eligible node;
both are gate STOPs). PRE-SECONDARY A asks for "the IQM and PoI over that suite's nodes". With 4 + 2 T1 train/dev instances,
a fold without an eligible node is plausible.
- **A (recommended, implemented):** report the fold's STOP for the IQM and the fold's PoI. The gate's PoI is defined over
  all supplied nodes whatever their eligibility (`gate._node_poi`), so it remains descriptive information.
- **B:** a STOP per fold with nothing reported for that fold.

**FOLD-LEVELS — interval levels in descriptive output.** The gate computes lower bounds at 97.5 % for its first-ranked arm and
95 % for the second (Holm). Keeping those levels would expose the ranking and let the verdict be rebuilt.
- **A (recommended, implemented):** both arms' lower bounds (IQM and PoI) at both declared levels, 97.5 % and 95 %, with no
  ranking and no pass flag.
- **B:** both arms at one fixed level (97.5 %).
- **C:** the gate's Holm-dependent levels (not recommended: it is a verdict in all but name).
