# Expansion G.1b — four nodes sealed; all four join G.5 (`compute/20261126-10`)

**Result: all four expansion nodes completed 460/460 runs, deterministic, and are eligible to join G.5 by
addendum.** D21 reports the funnel values but does not select T1 nodes (R1-T1-D21-SCOPE). No STOP; the run is
CPU-only and used 0 of the 40 GPU-hour cap.

- **Task:** `compute/20261126-10`, runbook §2 order 2B.
- **Deliverable branch:** `compute-expansion-g1b-20261127` @ `50fc9cbc96147ed2dd28ff9826915167810eb292`
  (base `c80f83bc5bc93356dfacadbcb5b186dfb59d028f`). Adds `docs/r1/reports/g1b_x_20261127/`.
- **Review:** `compute-expansion-g1b-review-20261127` @ `618ecaf48d24311407d6a72830ed86331053cd38`;
  round-2 verdict **ACCEPTED**, `docs/r1/reviews/G1B_X_RESULT_REVIEW_20261127_ROUND2.md` sha256
  `346f079c2fdf6960d5d68fd650706920cf0a96e847d13794279f4578d2f3893a`. Round 1 was NOT ACCEPTED on the G.5
  consequence (B1); the branch was corrected in a second commit, not force-pushed.
- **Note / pin:** `docs/r1/authorizations/g1b_x_t1_tasl_20261126.md` sha256 `16d31f48c48b5cffa26c13d988362e36a4e3241a17f15f41a9ad1ad7dd043539`;
  launch checkout `7d0279d8a677582f4f6e5892461bf7138e78fd66`; spec sha256 `d0dce058…cfd238`.

## Sealed attempts and hashes

| Node | Seal receipt sha256 | Job record sha256 |
|---|---|---|
| `mlgym_metamaze` | `897fadbaceef595386554cf4f4aef05dac5cf83cbf1a705264f53cb8f3e5de10` | `e1bc322996c72d2c57d10c4d0d1dadc7cff17ece5f37ecd1aba01f31dc422073` |
| `gc7rc_forestcover` | `2940254a01b7136d76eb2ed310536a7bf92cf5b03b373cffa8408ca285433506` | `6d9a0ad80c18ca00e0adb0865cc902a84b1ed8f38140e76d7fe783d992cdb373` |
| `gc7rc_etth1` | `96dad194c74b5dafb790ea3451cb7c6dd7763efd2c5e28737fe9306dd2bd02d7` | `2c50d59acbf1d224ddbc35927318237be2f4ebdaf76ff7d5cb4632092394aca2` |
| `mlgym_titanic` | `13773f1541b2d84cb5545fb80601babf6e087ae9b535cc50849870c03de00207` | `ac23a7c11603e1ecca9b09116506e5d4973e078ad26cb70060b943556837c0c9` |

Titanic sealed `2026-11-27T18:31:03Z`, `stop: null`; the other three were sealed earlier on 27 Nov. Assembly
`ASSEMBLY.json` `b4c90ec6…`, `runs.jsonl` `c23dec91…`, `edits.json` `5ad8f6ad…`, `summary.json` `67355b66…`.
All four seal receipts are captured on the deliverable branch.

## D21 funnel (reported, not a G.5 selector)

| Node | Material edits | Mean P(wrong) | σ_joint | Deterministic | Qualifies D21 |
|---|---:|---:|---:|---|---|
| `mlgym_metamaze` | 3 / 4 | 0.0244 | 1.5080 | yes | no |
| `gc7rc_forestcover` | 4 / 4 | 0.0499 | 0.001251 | yes | no |
| `gc7rc_etth1` | 3 / 4 | 0.0927 | 0.01106 | yes | no |
| `mlgym_titanic` | 0 / 4 | NaN (no material edit) | 0.02607 | yes | no |

Screening funnel: measured 4, qualified 0, failed determinism 0.

## What happens next

- The coordinator publishes the deliverable and then the G.5 addendum for all four nodes: each completed G.1b
  with determinism PASS (R1-STEP-ORDER (2)(a), R1-T1-D21-SCOPE, R1-G5-S9 (3)). MLGym nodes enter the arms and
  primary gate; 1GC nodes are G.5-labelled but excluded from arms/gate (R1-G5-S9 (2), R1-1GC-FALLBACK).
- No further author decision is needed for the join. R1-STEP-ORDER order 1 is complete on the expansion set.
- Sealed scenes remain at `/home/dowling/r1_tracks/t1_tasl_x/sealed_g1b/g1b-x-tasl-20261126-a/`.

Decided alone: sealed, assembled and summarised after Titanic's exit 0; disclosed four pre-attempt launch
refusals at `22:52:49Z` (exit 2, no attempt created) caused by a local bare `origin`, then the successful
`22:53:26Z` launch. No assertion relaxed, no run resumed.
