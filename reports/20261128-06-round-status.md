# Compute round status — 28 November 2026, 01:30 CET (`coord/compute` @ this commit)

Base `origin/main` `a98d2eff` at round start (later `73524055` published the D6 copy code); queue read at `coord/coordinator` `37a7f03e`.
Worked the STATE order: push reports, TASL-7 E0, D.3 preflight, HTCondor cleanup, houseprice at 01:00 CET, P11,
deepthought stop record, deepthought2 screening launch.

## Finished and delivered

| Task | Result | Branch @ tip | Review |
|---|---|---|---|
| `compute/20261128-02` push reports | fast-forward `17a20d28..ebb7354b` on `origin/coord/compute`; confirmed by `ls-remote` | — | — |
| `compute/20261128-04` HTCondor cleanup | 759624/759625 removed after Idle/owner/command check; 760065 recorded as withdrawn | `compute-htcondor-cleanup-20261128` @ `459d10c0` | docs only, coordinator check |
| `compute/20261128-03` D.3 preflight | **no submit**: `c03-001-175` has 7 free A100 but `Start=false`; ETP L40S also `Start=false`; exact expressions captured | `compute-d3-preflight-20261128` @ `db8eb526` | report-only |
| `compute/20261127-33` houseprice CPU-set | **PASS**, 3 sealed deterministic attempts, 3.810/3.858/3.848 s vs 9.486 s; record `2447e436…` | `compute-houseprice-cpuset-20261128` @ `e1a16d59` | `compute-houseprice-cpuset-20261128-review` @ `280d846e`, **ACCEPTED** (`ac6eac6d…`) |
| `compute/20261127-38` deepthought screening stop | eight scenes sealed, 0 failed, last 444/10,164; no analysis | `compute-screen-dt-stop-20261128` @ `b7cc5f70` | inventory only |
| `compute/20261127-32` P11 host tests | gate-blocked remainder: each seal/server command refused at `STOP: run_id must be c3_t1_labels_<YYYYMMDD>`; recorded as checked at publication | `compute-g5-p11-refusals-20261128` @ `dec84350` | `compute-g5-p11-refusals-20261128-review` @ `be56676c`, **ACCEPTED with two MINOR** (`d8e4e559…`; MINOR-1 applied) |
| `compute/20261127-02` item 2 survey redaction | already fixed on `origin/compute-resource-survey-20261126` @ `58e6bbeb` (no `vla` left in the survey captures); branch is ready to merge | survey branch | coordinator merge |
| `compute/20261127-36` expansion D6 copy | **delivered**: 1,840 rows; summary `67355b66…`, assembly `b4c90ec6…`, runs `c23dec91…` all equal to the source | `compute-relcopy-x-20261128` @ `c70fed2c` | `compute-relcopy-x-20261128-review` @ `c257c58f`, **ACCEPTED, no findings** (`4b7ef4e8…`) |

## Running (report with IDs for the next round)

| Task | What | ID / stamp | State |
|---|---|---|---|
| `compute/20261128-01` TASL-7 E0 same-code reference | `trackp.py e0 --stage final` on paper `c80f83bc`, config `e0_config_ref_tasl7.json`, `--evidence DRYRUN`, seed 0, lr 1e-4, card UUID `GPU-ab72fb4a…` | run `/home/dowling/r1_trackp/runs/p5_e0_ref_20261128/e0e`; lease 00:11:43–00:40:07Z | **STOP: NOT equivalent on RPS** — width +0.002179 (pass), mean −0.001491 (pass), RPS 1.1638e-4 vs Ada 1.4384e-4 = −19.09 % (tol 10 %, fail); record `d4b9f02c…`; review `compute-p5-tasl7-e0-20261128-review` @ `7b1c697e`, **ACCEPTED** (`f14321d3…`) |
| `compute/20261128-06` screening on deepthought2 | third re-issue, code `a7c2f8fb`, cache `3843b53c…`, 64 workers | launch script PID 3697711; checkout `paper_dt2_20261128T001405Z`; OUT `SMEAS_EVIDENCE_20261128T001405Z` | **launched 00:27:01Z**; strict preflight passed (co-tenancy ok, 119.82 cores free); 6,170/10,164 rows at 00:42, 0 failed, guard ok; analysis on completion |

## Blocked / not started

| Card | Waits for |
|---|---|
| `compute/20261127-36` expansion D6 copy | **done** (see above); coordinator publishes the accepted copy |
| `compute/20261127-32` remaining P11 (C2, C4, C5, C9, C14, C16, C10 hours, C11 chunk side) | signed G.5 note + filled spec, or a purpose-built synthetic smoke spec; none fabricated |
| `compute/20261127-33` item 2 Ada P5 rerun | the per-card lease is merged; waits for a decision on the E0 reference (now being produced by `-01`) |
| `compute/20261127-12`/`-03` D.3 batch preflight | a startable ETP L40S/TOpAS A100; re-check `Start` |
| `compute/20261127-28` E-INT census | signed census spec/authorization and smoke; yields to Paper B |
| `compute/20261126-06` G.5 campaigns | G.5 note published after the houseprice record and P11 review; then the launch |
| `compute/20261126-03` rows (g) | acknowledged here: free placement and shared cards were used, no request edited, no wall-clock limit decided anything |

## Queue / next-round checks, in order

1. `compute/20261128-06`: confirm the launch preflight passed and the first progress line; then rows done / 10,164,
   failures, guard status each round. On completion run the analysis exactly as the note says, branch + fresh review.
2. `compute/20261128-01`: when the report exists, run the existing comparator (Ada `e0e` as reference, TASL-7 as
   candidate) with the three pre-declared tolerances; write the record + branch and get a fresh review.
3. `compute/20261127-36`: fetch; run the reviewed expansion copy when `35849909` is on `main`.
4. `compute/20261127-32`: update/review the P11 record only if a synthetic smoke spec is authorized; otherwise the
   note-gated items stay checked at publication.
5. `compute/20261127-12`/`-03`: re-read the TOpAS `Start`; submit only when true.
6. P11 TASL-2 items and the expansion copy do not need GPUs; screening is CPU on deepthought2 and the E0 is GPU on
   TASL-7, so they can run together.
