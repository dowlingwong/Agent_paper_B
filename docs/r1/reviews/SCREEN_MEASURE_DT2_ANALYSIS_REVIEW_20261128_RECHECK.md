# Re-check — deepthought2 screening measurement analysis (28 Nov 2026)

**Verdict: ACCEPTED**

Re-check of the findings in `SCREEN_MEASURE_DT2_ANALYSIS_REVIEW_20261128.md` against the new
deliverable tip `52f43df7d1b10ee76dc64467d773c7765e27eb66` (one commit after `fa0707da`, no amend
or force-push). Verified in a fresh worktree created detached at that tip.

## What changed

`git diff fa0707da 52f43df7` touches exactly two paths, both in
`docs/r1/reports/screen_measure_20261128/dt2/`:

- `SCREEN_MEASURE_DT2_20261128.md` (8 insertions, 5 deletions);
- `SHA256SUMS` (one line: the report's new hash `34f5a2dd…`).

The other seven captured files are byte-identical to `fa0707da`:

| File | sha256 (unchanged) |
|---|---|
| `analysis.json` | `6c72535eae0673cb19853ca6130090369c2e5a2daacdc09f7989251aaaafdb41` |
| `analysis.log` | `59f2f64355749ea4b9414c5905bc90242f7b00c109a281184d5f210b6f623747` |
| `manifest.json` | `da2419a5293399db5842161abeac1a04253c2366ace909e680840a23f153364e` |
| `design.json` | `29396f5bb4dee22a0937b7587c7a5708a75570706075284bbfb9f4721f8085d0` |
| `lineage_runs.jsonl` | `c0863b6fa866d06ba8e2e63b6ef4e3b63c5170fb713a83783554bc08cd7f579a` |
| `worker_runtime.jsonl` | `86252da31b66132e62f970561f5798e15157e93ad595e59d716fa4982b80023e` |
| `cotenancy.log` | `10dc1ac7e9400c69e1557bab9df2315cc1dba3b30f825d09035039312601db74` |

No run, manifest, lineage, runtime or analysis data changed.

## Findings re-checked

1. **Threshold — fixed.** The report now reads “`threshold` 0.1, `level` 0.95,
   `bonferroni_level` 0.975; `n_boot` 2,000, `boot_seed` 20261123”. This matches
   `analysis.json` exactly (`threshold` 0.1, `level` 0.95, `bonferroni_level` 0.975,
   `n_boot` 2000, `boot_seed` 20261123). The earlier contradiction (0.975 as a decision
   threshold would have implied `NO_SHARED`) is gone.

2. **Elapsed — fixed.** The report now gives the `started_utc`/`finished_utc` span
   00:26:06 → 00:51:29Z (1,523 s) separately from `manifest.elapsed_seconds` 1,468.2 s and
   states that the latter is the measurement loop after preflight. This matches the code:
   `execute()` starts its `t0` after preflight, while `started_utc` is stamped before it (the
   first co-tenancy sample is 00:27:01). The ~55 s difference is accounted for.

3. **Checkout/run-directory stamp — addressed.** The report now identifies
   `SMEAS_EVIDENCE_20261128T001405Z` as the checkout/worktree name and states
   `manifest.started_utc` is `20261128T002606Z`. The distinction between the shell stamp and
   the measurement start is explicit; the preserved-directory claim is no longer presented as
   manifest-attested data.

## Result unchanged

`analysis.json`, `manifest.json` and `lineage_runs.jsonl` are byte-identical to the reviewed
tip, so the prior independent reproduction still applies. The record continues to report:

- `digits_mlp` and `openml_climate`: `INCONCLUSIVE` (both 95 % intervals contain 0; both point
  estimates below the 0.1 decision threshold and both high bounds above it);
- the other six nodes: `NOT_TESTED` by design;
- `decision = decision_seven_nodes = decision_bonferroni = R1_THEORY_RHO_2_FINAL`;
- no `SHARED` node and no seventh D.3a arm claim;
- no positive-effect over-claim.

`SHA256SUMS` verifies 8/8 listed files at this tip.

## Residual observations

- The word “stamp” is still used for both the common suffix and the run-directory name; the
  added sentence makes the meaning unambiguous, so this is cosmetic only.
- The checkout/worktree name remains a launch-shell fact rather than a manifest field; it is
  now explicitly labelled as such, which is adequate for this record.
- Optional: `analysis.log` is the command's printed summary, not a full console transcript; the
  committed `analysis.json` plus `SHA256SUMS` bind the analysis, so no change is required.

The corrected record is internally consistent, the data and analysis are unchanged, and the
`INCONCLUSIVE` / `NOT_TESTED` / `R1_THEORY_RHO_2_FINAL` result stands.
