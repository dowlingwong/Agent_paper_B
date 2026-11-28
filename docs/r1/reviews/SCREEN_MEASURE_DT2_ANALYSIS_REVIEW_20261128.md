# Independent review — deepthought2 screening measurement analysis (28 Nov 2026)

**Verdict: CHANGES REQUIRED**

Task `compute/20261128-06`; deliverable branch `compute-screen-dt2-20261128`
@ `fa0707dae2f8eed9e8d659616dc7e4967d9b7ae4` (declared base `origin/main` `73524055`).
Third published re-issue `docs/r1/authorizations/screen_measure_20261127_reissue_3.md` (sha256
`55779a6cfeea13cce99989f6e9680a48a96f0fc5fbc4f4476222cf73d767af9b`), code
`a7c2f8fb7b90b3237e61672c6b48112365dcdb24`.

Reviewed from a fresh worktree created detached at the deliverable tip; the branch was then made
from that tip. `origin/main` has since advanced to `7716cfce`; the declared base `73524055` is the
merge-base with the deliverable, and all diffs below use that base.

## What was independently checked

- Diff vs the declared base: exactly the nine files under
  `docs/r1/reports/screen_measure_20261128/dt2/`, no other paths (25,163 insertions).
  `SHA256SUMS` verifies 8/8 listed files (`shasum -a 256 -c` exit 0); the ninth tracked file is
  `SHA256SUMS` itself.
- `manifest.json` run facts, code pins, harness/edit-set/preflight records, data-cache tree.
- `lineage_runs.jsonl` row count, sha256, coverage, failures, determinism repeats, and the M3
  bit-identical-vector check.
- `worker_runtime.jsonl` row count and every row's interpreter/prefix/package identity.
- `analysis.json` schema, fields, per-node estimates/intervals, verdicts and decisions.
- Re-ran the note's analysis command from the same checkout and compared the result and
  `analysis.log`.
- Provenance: note, pre-declaration, code review, environment-basis files, code bytes at
  `a7c2f8fb`; and whether any test/evaluation label can be read.

## Recomputed evidence

### Diff and file bindings

`git diff --name-status 73524055...fa0707da` returns only the nine `A` paths under
`docs/r1/reports/screen_measure_20261128/dt2/`. All eight `SHA256SUMS` entries verify.

| File | sha256 |
|---|---|
| `analysis.json` | `6c72535eae0673cb19853ca6130090369c2e5a2daacdc09f7989251aaaafdb41` |
| `analysis.log` | `59f2f64355749ea4b9414c5905bc90242f7b00c109a281184d5f210b6f623747` |
| `manifest.json` | `da2419a5293399db5842161abeac1a04253c2366ace909e680840a23f153364e` |
| `design.json` | `29396f5bb4dee22a0937b7587c7a5708a75570706075284bbfb9f4721f8085d0` |
| `lineage_runs.jsonl` | `c0863b6fa866d06ba8e2e63b6ef4e3b63c5170fb713a83783554bc08cd7f579a` |
| `worker_runtime.jsonl` | `86252da31b66132e62f970561f5798e15157e93ad595e59d716fa4982b80023e` |
| `cotenancy.log` | `10dc1ac7e9400c69e1557bab9df2315cc1dba3b30f825d09035039312601db74` |
| `SCREEN_MEASURE_DT2_20261128.md` | `510f1c72b359e0c85277e614971bf7758dabfd10b5e6bf7b5aad72fe9bd34450` |

`design.json` has raw sha256 `29396f5b…` (the note's `design.json` pin) and canonical
`design_sha256` `bbc98b87d2170ad89ff17a92303ffb440583b74b035d2690a6a2ababeb8d8ec8` (the note's
`design_sha256` pin). Design totals: 84 configurations, 10,080 seed runs + 84 repeats = 10,164;
20 primary triples (18 `digits_mlp`, 2 `openml_climate`); testable nodes exactly those two.

### Manifest

All claimed fields agree:

- `schema` `r1_screen_measure_run/v2`, `run_id` `smeas-20261123-a`, `label` `EVIDENCE`,
  `stub` `false`.
- `planned_runs` 10,164, `written_runs` 10,164, `failed_runs` 0, `stop` null, `workers` 64,
  `elapsed_seconds` 1468.2.
- `started_utc` `20261128T002606Z`, `finished_utc` `20261128T005129Z`; host `deepthought2`,
  cpus 128, Python 3.13.15; libraries NumPy 2.4.4 / pandas 3.0.3 / scikit-learn 1.8.0 /
  SciPy 1.17.1.
- `data_cache.tree_sha256`
  `3843b53cddca6c32f00f5a1eeb96f34a78ca2871720900f4e6b8c0f724130d07`; six per-node cache
  digests present.
- `code_sha256` for the six note-pinned files equals the bytes at `a7c2f8fb` exactly
  (`e1_noise_floor.py a3fa508f…`, `screen_analysis.py a54753e1…`, `screen_design.py 3443c044…`,
  `screen_measure.py ae2d1688…`, `screen_power.py 8775c7ff…`, `screen_seeds.py dff8252b…`).
- `harness.commit` `6adf3859…`, `dirty` false; `preflight.harness_equivalence.diff` `"empty"`;
  `edit_sets` `"equal"` on all eight T0 nodes; preflight carries `affinity_cpus` 0-63,
  `launch_host` `deepthought2`, `placement_ruling` `R1-SCREEN-DEEPTHOUGHT2`.
- `provenance.paper_code_commit` `a7c2f8fb…`, `paper_code_clean` true,
  `review_sha256` `dc7b0d63…` (matches the review file); `preflight.note_sha256` `55779a6c…`
  (matches the re-issue); `predeclaration_sha256` `a380dbf1…` (matches the pre-declaration).
- Six environment-basis files under `docs/r1/reports/e1_replay_20261117/` and
  `docs/r1/reviews/E1_AMEND_RUN_REVIEW_20261117.md` match their recorded sha256 values;
  `52992b22` is an ancestor of the base.

### Lineage and runtime records

`lineage_runs.jsonl`: 10,164 rows, sha256 `c0863b6f…` = manifest `runs_sha256`. Recomputing:

- 10,080 `seed` + 84 `repeat`; 84 configurations (15 on `digits_mlp`, 15 on `tabular_mlp`,
  9 on each other node); every configuration has all 120 seeds 3301-3420.
- Every row `success` true, `failure` null, metric finite; no duplicate
  `(node, config, condition, seed)` keys.
- Every repeat metric equals the same configuration's seed-3301 seed metric (0 mismatches).
- No pair of configurations in any node has bit-identical metric vectors over the 120 seeds, so
  the analysis' M3 STOP is not triggered.
- The row-key set is exactly the ten declared keys; no label/evaluation fields are present.

`worker_runtime.jsonl`: 10,164 rows, every row records prefix
`/ceph/dwong/r1_prepare_20261025/venv`, worker Python `/ceph/dwong/r1_prepare_20261025/venv/bin/python`,
package-list hash `a089bbf1…`, and versions NumPy 2.4.4 / pandas 3.0.3 / scikit-learn 1.8.0 /
SciPy 1.17.1 — the approved batch environment in every record.

### Analysis

`analysis.json` reports `schema` `r1_screen_measure_analysis/v2`, `label` `EVIDENCE`,
`run_id` `smeas-20261123-a`, `design_sha256` `bbc98b87…`, `threshold` **0.1**, `level` 0.95,
`bonferroni_level` 0.975, `n_boot` 2000, `boot_seed` 20261123, resampling unit
“seed (every configuration of a node jointly)”.

| Node | Primary triples | Estimate | 95 % CI | 97.5 % CI | Verdict |
|---|---:|---:|---|---|---|
| `digits_mlp` | 18/18 eligible | 0.0815756168 | [−0.00835935, 0.17268378] | [−0.01764454, 0.18492067] | INCONCLUSIVE |
| `openml_climate` | 2/2 eligible | 0.0596210081 | [−0.09446711, 0.21439771] | [−0.11873877, 0.23964538] | INCONCLUSIVE |
| other six | no primary triple | — | — | — | NOT_TESTED (`no_triple_in_design`) |

Both primary 95 % intervals contain 0, and both point estimates are below the 0.1 decision
threshold while both high bounds are above it; `decide(lo, hi, 0.1)` therefore returns
`INCONCLUSIVE` for both. `bootstrap_dropped_cells` and `bootstrap_empty_resamples` are 0 for
both; both nodes have 120/120 complete seeds and no dropped configurations/seeds. The six
`NOT_TESTED` nodes have 120/120 complete seeds and `no_triple_in_design`.

`verdicts` and `verdicts_bonferroni` are identical; `decision`, `decision_seven_nodes` and
`decision_bonferroni` are all `R1_THEORY_RHO_2_FINAL`; no node is `SHARED` (count 0). The
deliverable correctly does not claim a positive effect or a seventh D.3a arm.

### Reproduction

From the fresh worktree at the deliverable tip (code bytes equal to `a7c2f8fb`), I ran the
declared command:

```
python3 -B -m r1.noise.screen_analysis \
  docs/r1/reports/screen_measure_20261128/dt2 \
  --out <temp>/repro_analysis.json
```

The result is structurally identical to `analysis.json`: every key, verdict, decision, count and
triple matches; the largest float difference is 4.57e-14 (`openml_credit_approval`
secondary interval), attributable to the local interpreter stack (numpy 1.24.3/macOS) versus the
run environment (Python 3.13.15 / numpy 2.4.4). The reproduction's stdout is byte-identical to
`analysis.log`. The analysis therefore is the note's declared command applied to this lineage
table and design.

### Labels, STOP and co-tenancy

`screen_analysis` refuses sealed/label/evaluation/test path components and evidence-audit markers;
it reads only `manifest.json`, `lineage_runs.jsonl` and the pinned T0 design (whose sources are
the D28 noise summary and E1 pilot edit files, all engineering artifacts). No test/evaluation
label is read. There is no STOP (`stop: null`), no `failed_runs.jsonl`, and all 25 co-tenancy
samples are `ok` (last sample `free_for_others` 119.97, `our_workers` 63).

## Findings

1. **Required — the record reports the wrong `threshold`.** `SCREEN_MEASURE_DT2_20261128.md`
   line 33 says “`threshold` 0.975, `level` 0.95”. `analysis.json` actually has
   `threshold: 0.1`, `level: 0.95`, `bonferroni_level: 0.975`. The decisive threshold in
   `screen_analysis.decide()` is 0.1; 0.975 is only the secondary Bonferroni interval level.
   The sentence is materially wrong: if 0.975 were the decision threshold, both high bounds
   (0.17268 and 0.21440) are below it, which would yield `NO_SHARED`, contradicting the
   `INCONCLUSIVE` verdicts in the same report. Replace with
   “`threshold` 0.1, `level` 0.95, `bonferroni_level` 0.975; `n_boot` 2,000, `boot_seed`
   20261123”. No number in the analysis or verdicts changes.

2. **Minor — elapsed time is not the launch-to-finish span.** `elapsed_seconds` 1468.2 is
   measured by `execute()` from its own `t0` after preflight; the `started_utc` → `finished_utc`
   span is 1,523 s (00:26:06 → 00:51:29, 25 min 23 s). The field is quoted correctly from the
   manifest, but the “Launch / finish … elapsed” bullet can be read as saying the whole launch
   took 1,468.2 s. State that 1,468.2 s is the measurement loop and that ~55 s of preflight
   precedes it (first co-tenancy sample 00:27:01), or quote the 1,523 s wall span beside it.

3. **Minor — the launch/checkout stamp is not captured.** The report's stamp and checkout/run
   directory stamp `20261128T001405Z` do not appear in `manifest.json` (whose `started_utc` is
   `20261128T002606Z`), so the “run directory … (preserved)” claim cannot be checked from the
   committed captures alone. Code provenance itself is independently supported by
   `provenance.paper_code_commit` / `paper_code_clean` and the six code hashes; if the stamp is
   to be part of the record, add it to a launch receipt or the manifest (it is not a data defect).

## Assessment

The run, the captures, the code identity, the lineage, the worker-runtime receipts and the
analysis computation are sound. The reported `INCONCLUSIVE` / `NOT_TESTED` verdicts and all three
`R1_THEORY_RHO_2_FINAL` decisions are correct, there is no `SHARED` node, no seventh D.3a arm is
claimed, and no positive effect is over-claimed. The only required change is finding 1, a
correction to the report's statement of the decision threshold; findings 2 and 3 are
clarity/provenance improvements. Once finding 1 is corrected, the record can be accepted.
