# R1-BX-D8-CONFIRM-V31: the row binding gate v3.1 (DRAFT, approved: false)

**Status: DRAFT for the author's signature. Nothing here is a decision.** Prepared by the Mac-desk agent (Claude),
AI-assisted, 21 Nov 2026, with gate v3.1 (`r1/c3/gate.py` @ `31dab9ef`) for PRE-WDBC option B of the sweep-2
analysis preregistration (`mac-sweep2-prereg-20261121`, accepted revision 4).

## Why a row is needed

R1-S2C3B-WDBC makes the primary sweep-2 analysis the seven T0 nodes that passed S2-C3b, with `openml_wdbc` as a
pre-declared sensitivity row. Gate v3 (`6aa9985c`, sha256 `ffb70d7a…`, bound by R1-BX-D8-CONFIRM) STOPs unless all
eight T0 nodes are supplied, so the primary cannot run on it. Gate v3.1 differs only in that the input declares its T0
node set (a subset of the eight, possibly empty for a leave-one-suite-out fold) and the gate records it; a T0 node
outside the declared set is a STOP in any tier (it cannot be relabelled T1); on all eight
nodes its output is v3's except the gate version, the gate sha256, the schema strings and that field (tested against
the frozen v3 file). Every sweep-2 reader runs `analysis_guard.require_d8_confirmation()`, which requires a PLAN row
naming the **current** gate bytes, so replacing `gate.py` locks every reader until such a row exists.

Gate v3.1: `r1/c3/gate.py` @ `31dab9efb94b7f187ec44cab1bc4a4ad63c1085d`, sha256 `a3f7d002b54829c1fa40b7b18a1e2f4c5327749f20ae3ab7e0751b68c009cf23`.

## Options (recommendation: A)

- **A (recommended): a successor row `R1-BX-D8-CONFIRM-V31`.** The guard of this unit accepts it with the exact text
  below; once it exists, R1-BX-D8-CONFIRM is superseded for the guard (exactly one successor row, matching the current
  gate bytes; the v3 bytes are then no longer authorized). R1-BX-D8-CONFIRM stays in PLAN as written, so the history
  reads in order.
- **B: amend R1-BX-D8-CONFIRM in place** (new commit and sha256 in the same row text). No guard change would be
  needed, but it rewrites an author row's bound values, and the record of what v3 was bound lives only in git.
- **C: PRE-WDBC option A instead** (no v3.1; the primary gate on all eight T0 nodes, the seven-node analysis as a
  descriptive row). Needs an author row amending R1-S2C3B-WDBC; this unit would then not be merged.

## Where it goes

In `docs/r1/PLAN.md` §10, in a table under a dated author-decision heading (e.g. `### 21 November 2026 — author
decisions`) whose header is `| ID | Decision |`, outside any code fence or comment, exactly once. The guard parses
only that shape. It must reach `main` **in the same merge as the gate v3.1 commit**, and that merge must keep the
commit the row names (no squash or rebase; the guard requires it to be an ancestor of `main` holding the same gate
bytes — otherwise regenerate the row with the merged commit), and before any sweep-2 label table
is read (R1-BX-D8). In any interval where `main` has gate v3.1 without this row, every reader that requires D8
confirmation STOPs (sweep-2 tables, tables of unknown provenance, the Track P loaders on them): the lock works as
designed, and three Track P tests that read synthetic unknown-provenance tables through the real guard
(`r1/tests/test_trackp_sft.py`: `test_load_table_pins_and_eval_columns`, `test_sealed_paths_and_sweep_binding_refused`,
`test_cli_dry_run_end_to_end`) fail in that interval. On this branch they fail for that reason only; in a scratch copy
with this row added to PLAN they pass (35/35) and `require_d8_confirmation()` returns.

## Proposed row (A)

| R1-BX-D8-CONFIRM-V31 | Gate code `r1/c3/gate.py` @ `31dab9efb94b7f187ec44cab1bc4a4ad63c1085d`, sha256 `a3f7d002b54829c1fa40b7b18a1e2f4c5327749f20ae3ab7e0751b68c009cf23`, is gate v3.1: it replaces the gate bound by R1-BX-D8-CONFIRM and differs from it only in accepting a declared T0 node set (a subset of the eight T0 nodes, possibly empty), which it records in its output (R1-S2C3B-WDBC). It implements R1-BX-D8 with the numbers confirmed in R1-BX-PROPOSED-CONFIRM (D8); T0 and T1 pooled with tier as a stratum. If only some T1 nodes have labels by B.7, read the gate on T0 plus the available labelled T1 nodes and disclose the node count. For leave-one-suite-out, each suite must have at least one labelled T1 node, otherwise leave-one-suite-out STOPs; the aggregate gate does not STOP on it. Existing preregistration and analysis gates remain in force. Sweep-2 label tables may be analysed from this row on. |

## What the row does not decide

- Which T0 nodes the primary uses: the preregistration (PRE-WDBC B) fixes it as the nodes that passed S2-C3b at the
  launch commit, recorded in the arms-frozen record; the eight-node run is the sensitivity row.
- Anything else in the gate: v3's statistics, pins, STOPs and the analysis lock are unchanged.
