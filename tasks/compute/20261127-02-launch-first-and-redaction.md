# compute/20261127-02 — two corrections: launch the expansion first; one name left in the survey

1. **Order.** `compute/20261126-10` (launch the four expansion nodes) is item 1 of your queue in `STATE.md`, and it is the only
   item with a time bound (start before 30 Nov 20:33 CET so the published note's `cutoff` line has no case). Your reports since
   23:41 cover the redaction and the TASL-7/pool samples, and your pane shows the D.3 design revision. No launch is reported.
   **Finish the step you are on, then launch before anything else**, and report each node's start. If you already launched and
   did not report, report now. Then continue in the STATE order: `compute/20261127-01` (houseprice CPU-set run), then D.3.
2. **Redaction.** `compute-resource-survey-20261126` @ `f60a2225`: `docs/r1/reports/COMPUTE_RESOURCE_SURVEY_20261126_captures/Ada.txt`
   lines 49–62 still show another user's name in the truncated `ps` user column (`vla-rea+`). Replace it with the same label as in
   the report, check every capture for truncated forms (any prefix of each name), and give the new tip and hashes. The branch
   merges after that.
