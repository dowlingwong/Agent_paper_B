# Image v2.1 rerun — submission log (21–22 November 2026, ENGINEERING_ONLY)

Units staged at `/work/dwong/paperb/work/trackp-h200-v21-20261121.R7XUMd/` on `deepthought`, each
the tracked unit with only the container-image digest changed (I3 additionally carries the recorded
L40S→H200 route). Three independent pre-submission reviews: `docs/r1/reviews/TRACKP_V21_UNIT_REVIEWS_20261121.md`
(all ACCEPTED). Scheduler dry-runs: all four JDLs dry-run to `JobUniverse=5` with the v2.1 digests and
the expected requirements.

| Stage | Job | Requirement | State at submission |
| --- | --- | --- | --- |
| I2 v2.1 (cpu `c152c329…`) | 759917.0 | ETP local (`ProvidesETPResources`), 2 CPUs, 8 GB, 30 GB disk | queued (Idle) |
| I3 v2.1 (gpu `31478d99…`) | 759918.0 | NEMO2 H200, 1 GPU, 4 CPUs, 16 GB, 30 GB disk | queued (Idle) |
| H200 smoke v2.1 (gpu `31478d99…`) | not submitted | NEMO2 H200 | held until I2/I3 pass |
| E0 v2.1 (gpu `31478d99…`) | not submitted | NEMO2 H200 | held until the smoke passes |

## Pool blocker (22 Nov 2026, ~00:30 CET)

Both queued jobs stay Idle because the pool has no matching slot:

- **Every NEMO2 slot advertises `START = false`** (site-wide drain/retirement: 53 defined STARTs all
  false, 74 slots `Claimed Retiring`, 9 `Drained`; the L40S nodes are gone and `g4402` is the only
  advertised H200). `condor_q -better-analyze 759918.0`: 32 of 34 slots rejected by job
  requirements, 1 slot rejects because of its own requirements (`START=false`), 1 would match if
  drained, 0 match now.
- **No ETP-local slot meets I2's reviewed request** (2 CPUs, 8 GB, 30 GB disk): unclaimed slots are
  either `START=false` (bms1–3, deepthought, deepthought2, lx88) or too small (mdm1/mdm2 parent
  slots 0 CPUs; ms02 0 CPUs; ms03 3 CPUs but 3.5 GB memory).

The jobs stay queued; they will run if a reviewed slot appears. I2/I3 results, the smoke and E0 are
NOT claimed. No assertion or resource request was relaxed to force a match.
