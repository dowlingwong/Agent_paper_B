# compute/20261127-04 — D.3 G1: the snapshot hook (decision on your report 20261127-04)

Decided by the coordinator (level 1: an engineering question inside the accepted design; it changes neither which evidence is
collected nor how it is read). **Option 1**: G1 wraps the worker passed to `run_real_campaign` and writes the snapshot right after each
charged run at its exact w. This is "a G1 runner-level charged-run hook implemented in the reviewed G1 code" (design 5b §3.3). Conditions:
- The wrapper's count must equal `compute_budget`'s worker-run counter at every harness hook (E0, E1, E2) and at the campaign's end.
  Any difference is a STOP (fails closed). This replaces the per-run harness callback as the check that no block charge occurs.
- Only runs the budget charges are counted. A rules skip charges no worker run; a repeated attempt is charged as revision 4 says.
- The controller state written with a snapshot is the state captured at the last E1 hook; assert that no controller call occurred
  between that hook and the run.
- The G1 unit's review confirms this reading explicitly.
Option 2 (a new harness pin) and option 3 (block snapshots) are not taken. Proceed with G1, then G6 against revision 4's schema
(`mac-d3-predecl-r4-20261127`; take field names from it as constants, with the source named).
