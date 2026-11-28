# Screening measurement on deepthought2 — complete, analysis INCONCLUSIVE (28 Nov 2026)

Task `compute/20261128-06` under **R1-SCREEN-DEEPTHOUGHT2**, third re-issue
(`docs/r1/authorizations/screen_measure_20261127_reissue_3.md`, approved, sha256 `55779a6c…`), code
`a7c2f8fb7b90b3237e61672c6b48112365dcdb24`, review `SCREEN_MEASURE_DEEPTHOUGHT2_REVIEW_20261128.md`.

**Result: the measurement completed all 10,164 planned runs with 0 failures and no STOP. The pre-declared analysis
returns `INCONCLUSIVE` for the two testable nodes (`digits_mlp`, `openml_climate`); the other six are `NOT_TESTED` by
design. Decision: `R1_THEORY_RHO_2_FINAL` (also under the seven-node and Bonferroni readings). No `SHARED` decision
node, so the note's "otherwise R1-THEORY-RHO (2) is final and D.3 step (8) proceeds on rev 4" branch applies.**

- **Host:** deepthought2, CPU only, 64 workers on logical CPUs 0-63.
- **Run id:** `smeas-20261123-a`; stamp `SMEAS_EVIDENCE_20261128T001405Z`; checkout
  `paper_dt2_20261128T001405Z` at `a7c2f8fb`; run directory
  `results/r1/screen_measure/SMEAS_EVIDENCE_20261128T001405Z` (preserved). The stamp is the checkout/worktree
  name; `manifest.started_utc` is `20261128T002606Z`, i.e. the measurement started after the worktree checkout
  and preflight.
- **Launch / finish:** `2026-11-28T00:26:06Z` / `00:51:29Z` (1,523 s span); manifest `elapsed_seconds`
  **1,468.2 s (24 min 28 s)**, the measurement loop after preflight.
- **Counts:** planned 10,164 / written 10,164 / failed 0; `stop: null`. Co-tenancy guard ok at every 60 s sample
  (last `free_for_others 119.97`, `our_workers 63`).
- **Environment:** manifest `host.python 3.13.15`, e1 replay batch env; data cache tree
  `3843b53cddca6c32f00f5a1eeb96f34a78ca2871720900f4e6b8c0f724130d07`; harness/edit-set checks pass in the
  manifest.
- **No test/evaluation label was read:** the runs are T0 engineering configurations; the analysis reads the
  lineage table only.

## Per-node analysis

| Node | Primary triples | Estimate | 95 % CI | 97.5 % CI | Verdict |
|---|---:|---:|---|---|---|
| `digits_mlp` | 18 | 0.08158 | [−0.00836, 0.17268] | [−0.01764, 0.18492] | **INCONCLUSIVE** |
| `openml_climate` | 2 | 0.05962 | [−0.09447, 0.21440] | [−0.11874, 0.23965] | **INCONCLUSIVE** |
| `openml_breast_w`, `openml_credit_approval`, `openml_ionosphere`, `openml_sonar`, `openml_wdbc`, `tabular_mlp` | — | — | — | — | `NOT_TESTED` (by design) |

- `threshold` 0.1, `level` 0.95, `bonferroni_level` 0.975; `n_boot` 2,000, `boot_seed` 20261123; no bootstrap
  dropouts on the primary estimator (`bootstrap_dropped_cells: 0` for both nodes).
- `verdicts_bonferroni` is identical; `decision = decision_seven_nodes = decision_bonferroni =
  R1_THEORY_RHO_2_FINAL`.
- `digits_mlp` complete seeds 120/120; `openml_climate` 120/120; no dropped configurations or seeds.

## Files (this directory)

`analysis.json` sha256 `6c72535eae0673cb19853ca6130090369c2e5a2daacdc09f7989251aaaafdb41`,
`manifest.json` `da2419a5293399db5842161abeac1a04253c2366ace909e680840a23f153364e`,
`design.json` `29396f5bb4dee22a0937b7587c7a5708a75570706075284bbfb9f4721f8085d0` (equals the note's design),
`cotenancy.log` `10dc1ac7e9400c69e1557bab9df2315cc1dba3b30f825d09035039312601db74`,
`lineage_runs.jsonl` `c0863b6fa866d06ba8e2e63b6ef4e3b63c5170fb713a83783554bc08cd7f579a` (10,164 rows; equals the
manifest's `runs_sha256`),
`worker_runtime.jsonl` `86252da31b66132e62f970561f5798e15157e93ad595e59d716fa4982b80023e`,
`analysis.log` (the analysis console receipt). `SHA256SUMS` binds them.

Decided alone: none beyond running the published command and the note's analysis command; the old scenes and the
deepthought attempts stay untouched, nothing was resumed, and no tolerance or seed was changed.
