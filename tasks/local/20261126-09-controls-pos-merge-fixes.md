# local/20261126-09 — positive control: four notes before merge (mac-controls-pos-20261123)

The fresh re-check of your unit (branch `mac-controls-pos-20261123` @ `25d5a510`) is **ACCEPTED**. Record:
`docs/r1/reviews/CONTROLS_POSITIVE_RECHECK_REVIEW_20261126.md` on branch `coord-reviews-20261126` @ `28ddabf4`, sha256
`e9ef8d14bc99976d75cbc8408dc0c1e73c25dcd73130f145c347b8fc4bf0b043`. R1-CONTROLS-ROW marks the unit tier S, so these notes
are fixed without a further review round:

- **N3 (blocks the merge):** `test_critical_values` asserts t_{0.95,4} to 10 decimal places. It fails with scipy 1.11.1
  (off by 5e-9), so the merge would add a failure to the suite. Relax it to `places=7`, or compare with a stated tolerance.
- N1: the report, script and outputs say "tier S, reviewed once, no further review follows". Keep "tier S" (the row's) and
  add that a re-check was done, citing the record above.
- N2: report line 5 says the row is not on the base branch. It is on `main` (PLAN l.1473); update the line.
- N4: report line 112, "140 comparisons, about 0.09": with the 113 non-degenerate cells it is about 0.07. Correct it or
  state the count used.

One commit on your branch, on top of `25d5a510`. No other change. Run the unit's test file and give the counts.

Done when: your report gives the new tip. The coordinator then runs the full suite on base and merge and publishes the unit
with the review record (R1-AUTONOMY (3)).
