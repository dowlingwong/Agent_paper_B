# The fold-analysis module of the sweep-2 C3 analysis (PRE-SECONDARY A)

Prepared by the Mac-desk agent (Claude), AI-assisted, 21 Nov 2026, for the signed preregistration
(`docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md`, R1-SWEEP2-PREREG) §9 and PRE-SECONDARY A. It read no table,
label or evaluation value; the tests use synthetic records (the gate runs are skipped unless NumPy is 2.4.4).

- **Module:** `r1/c3/fold_analysis.py`. Tests: `r1/tests/test_fold_analysis.py`.
- **Leave-one-suite-out:** per suite of `gate.SUITES`, the gate's statistics (IQM, PoI, intervals) over that suite's T1 nodes
  with the fold's arms. It STOPs before any statistic if a suite has no labelled T1 node (R1-BX-D8-CONFIRM).
- **Leave-one-node-out within T0:** per node of the primary T0 set, its gap closed and PoI with the fold's arms.
- **Secondary recomputes:** g = 0.05 and 0.2 σ_node, and per memory mode.
- **How:** each fold's input comes from the accepted gate-input builder on the fold's node subset, with the fold arms'
  predictions as A3/A5 and the subset's declared T0 set (empty for a suite fold), and is evaluated by `gate.evaluate`
  (gate v3.1, with its pins and D8 check). A node's values on a subset equal those of the full build (tested). The output
  keeps the gate's statistics and drops its decision fields (verdict, first-ranked arm, Holm rank and pass flags,
  practical-size flag); it is marked `descriptive: true`.

## Readings the coordinating chat should confirm

1. **A2 and the oracle are not fold arms.** A2 keeps PRE-A2 C's constants from the node's own dev label block, and the oracle
   its label-block belief; a fold changes only A3 and A5 ("fold arms retrained without that suite/node").
2. **Population and g.** Folds use the PRE-DUP primary test population and g = 0.1 σ_node.
3. **Leave-one-node-out node set.** It runs over the primary T0 set of the arms-frozen record (seven, or eight after an 8/8
   C3b rerun).
4. **"Labelled T1 node"** means a node of the frozen T1 set that the builder supplies (PRE-T1: at least one train and one dev
   instance).
5. **Gate STOPs inside folds.** A gate STOP inside a fold (for example no IQM-eligible node) is reported for that fold. It is
   not a STOP of the analysis; the only analysis-level STOP is leave-one-suite-out's declared one.
6. **Per-mode runs.** T1 nodes enter only the per-mode run of their declared mode(s) (G5-MEM).
7. **Interval levels.** The descriptive output keeps the gate's lower bounds at the level the gate computed them (97.5 % or
   95 % by its Holm ranking), and records that level.
8. **Fold arm selection.** Fold arms are selected by PRE-SELECT on the fold's dev instances in the arms pipeline; this module
   takes their predictions as given.
