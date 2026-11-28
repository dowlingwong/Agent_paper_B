# Compute round status — 28 November 2026, 03:20 CET

Round base `origin/main` `914e1cf9`; queue read at `coord/coordinator` `381c1bf2`. No compute job is running.

## Finished and delivered

| Task | Result | Branch @ tip | Review |
|---|---|---|---|
| `compute/20261128-03` D.3 HTCondor preflight re-check | **No submit**: `c03-001-175` A100 (7 free) and the ETP L40S (1 free) both `Start = false`; exact expressions captured; `760158` (R2 sparse-sk) untouched | `compute-d3-preflight-recheck-20261128` @ `c5e2df4a` | report-only; merged `914e1cf9` |
| `compute/20261128-08` E0 repeatability | **Ada within tolerance** (RPS +9.66 %); **TASL-7 not** (RPS +26.13 %); cross-host first pair no (+23.60 %), repeat pair yes (+7.46 %); neither bit-identical; 1.1008 GPU-h | `compute-p5-e0-repeat-20261128` @ `2cd0bd88` | `…-review` @ `ca1c1cf8`, **ACCEPTED** (`6c16e18b…`) |
| `compute/20261128-09` G.5 P11 matrix | **STOP**: both campaigns `STOP 6 baseline_failed` from the kit step-line/harness mismatch; `close-attempt`/`close-server` self-scan refusal; server/probe/seal passed | `compute-g5-p11-matrix-20261128` @ `ba02dc21` | `…-review` @ `e6126a65`, **ACCEPTED** (`ffafd52d…`; minors applied) |

- E0 record: `docs/r1/reports/trackp_p5_e0_repeat_20261128/E0_REPEAT_20261128.md`; `SHA256SUMS` 51/51 OK. Tests:
  the archived comparator run on the four report pairs (values reproduce), plus byte checks of the npy arrays.
- P11 record: `docs/r1/reports/g5_p11_engineering_20261128/G5_P11_ENGINEERING_20261128.md`; `SHA256SUMS` 50/50 OK.
  No code change; the two defects are in the reviewed engineering path.
- All deliverables were pushed to their own branches; nothing force-pushed or amended. Captures ignored by
  `.gitignore` were force-added unchanged where they are part of the record.

## Running / idle now

- **No job of ours is running.** TASL-2 GPU 353 MiB / 0 % (display only), TASL-7 44 MiB / 0 %, Ada card 0 5 MiB / 0 %
  and card 1 belongs to another user; all our GPU leases are free. deepthought2 is idle after the screening run.
- HTCondor: `760158.0` (owner `dwong`, R2 sparse-sk project, 4 CPUs / 32 GB, `slot1_4@c03-001-179`) is still running;
  it is not a Paper B job and was not touched. 3 jobs are running for all users on the schedd; the two D.3 probes
  remain removed.
- P11 scenes are preserved under `~/r1_engineering/g5-p11` on both TASL hosts; the E0 run directories are preserved.
  The TASL-7 proposer was stopped cleanly; the separate `-closeserver` scene has no `server_end.json` by design.

## Waiting / blocked

| Card | Waits for | Owner |
|---|---|---|
| `compute/20261128-09` P11 matrix | local fix of the kit step-line interface and `processes_mentioning` self-exclusion; then a fresh card and a new review | local, then compute |
| `compute/20261128-08` E0 criterion | author decision on the repeat evidence; no criterion change proposed by compute | author |
| `compute/20261126-07` P.4 phase-1 jobs, A5 SFT | the E0 decision and the phase-1 note | author / coordinator |
| `compute/20261128-03` / `compute/20261127-12` D.3 batch preflight | a startable ETP L40S/TOpAS A100 (`Start = true`); re-read each round | compute |
| `compute/20261126-06` G.5 campaigns | published G.5 note; reviewed P11 coverage and render first | coordinator |
| `compute/20261127-03` P11 evidence table / copy verdict | P11 fix and matrix rerun | compute |
| `compute/20261127-28` E-INT census | signed census spec/authorization and smoke; yields to Paper B | author / design |
| `compute/20261126-02` / `cluster/20261126-02` D.3 runner and audit | per-arm smoke once rev 4 freezes; D.3 smoke has its own signed-design STOP on record | coordinator |
| `compute/20261126-11` survey redaction | already fixed on `compute-resource-survey-20261126` @ `58e6bbeb`; coordinator merge | coordinator |

**G1/G6:** the adapter (`ac01717e`), G6 audit (`0716ed8d`) and the 6c replicate driver (`478c3348`) are already
merged; no unit remains on `compute/20261127-16`. **Rows (g) acknowledged:** free placement and shared cards were
used, no request was edited to get a slot, and no wall-clock limit decided anything.

## Next-round checks, in order

1. Take the P11 review and the coordinator's fix card; rerun the matrix from the fixed code, fresh IDs, after the
   E0 card is free. Do not record P11 until the reviewed host record exists.
2. Take the author's E0 decision; if A, one accepted repeatability basis; if the criterion changes, the coordinator
   publishes it first. The phase-1 note and A5 SFT stay gated until then.
3. Re-read `condor_status -pool c03-001-140.gridka.de` for `c03-001-175` and the ETP collector for the L40S; submit
   only when a matched slot says `Start = true`.
4. Idle hosts: TASL-2, TASL-7, Ada card 0 and deepthought2 are free for Paper B first.

Round decided alone: host/card placement (TASL-2 worker, TASL-7 proposer, Ada/TASL-7 E0 repeats), fresh run
directories, and stopping the P11 line once both nodes recorded the node STOP; no tolerance, note, seed or request
was changed.
