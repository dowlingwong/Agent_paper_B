# Compute round status — 28 November 2026, 02:00 CET (`coord/compute` @ this commit)

Round base `origin/main` `a98d2eff`; `main` is now `7716cfce` (it merged the E0 and D6-copy records while this round
ran). Queue read at `coord/coordinator` `a06dfc3f`. No compute job is still running.

## Finished and delivered

| Task | Result | Branch @ tip | Review |
|---|---|---|---|
| `compute/20261128-02` push reports | fast-forward `17a20d28..ebb7354b` on `origin/coord/compute`; checked with `ls-remote` | — | — |
| `compute/20261128-04` HTCondor cleanup | 759624/759625 removed after the Idle/owner/command check; 760065 recorded as withdrawn; no other job touched | `compute-htcondor-cleanup-20261128` @ `459d10c0` | docs only, coordinator check |
| `compute/20261128-03` D.3 preflight | **no submit**: `c03-001-175` (7 free A100) has `Start = false`; ETP L40S also `Start = false`; exact expressions captured | `compute-d3-preflight-20261128` @ `db8eb526` | report-only |
| `compute/20261127-33` houseprice CPU-set | **PASS**: 3 sealed deterministic attempts, 3.810/3.858/3.848 s vs 9.486 s; record `2447e436…` | `compute-houseprice-cpuset-20261128` @ `e1a16d59` | `…-review` @ `280d846e`, **ACCEPTED** (`ac6eac6d…`) |
| `compute/20261127-32` P11 host tests | gate-blocked remainder: `seal-*/close-server/server-span` all refused with `STOP: run_id must be c3_t1_labels_<YYYYMMDD>`; recorded | `compute-g5-p11-refusals-20261128` @ `dec84350` | `…-review` @ `be56676c`, **ACCEPTED** (`d8e4e559…`) — but the disposition is now superseded (see below) |
| `compute/20261127-38` deepthought screening stop | eight scenes sealed, 0 failed, last 444/10,164; no analysis | `compute-screen-dt-stop-20261128` @ `b7cc5f70` | inventory only |
| `compute/20261127-36` / `-07` expansion D6 copy | **delivered**: 1,840 rows; summary `67355b66…`, assembly `b4c90ec6…`, runs `c23dec91…` all equal the source | `compute-relcopy-x-20261128` @ `c70fed2c` | `…-review` @ `c257c58f`, **ACCEPTED, no findings** (`4b7ef4e8…`) |
| `compute/20261128-01` TASL-7 E0 same-code | **STOP: not equivalent** — width +0.002179 and mean −0.001491 pass; RPS 1.1638e-4 vs Ada 1.4384e-4 = **−19.09 %** (tol 10 %) | `compute-p5-tasl7-e0-20261128` @ `391c12bc` | `…-review` @ `7b1c697e`, **ACCEPTED** (`f14321d3…`); on `main` `7716cfce` |
| `compute/20261128-06` screening deepthought2 | **complete**: 10,164/10,164, 0 failed, 1,468.2 s; `digits_mlp`/`openml_climate` INCONCLUSIVE, six NOT_TESTED; `R1_THEORY_RHO_2_FINAL`, no SHARED | `compute-screen-dt2-20261128` @ `52f43df7` | `…-review` @ `69399f09`, **ACCEPTED** (`69779214…`) |
| `compute/20261127-02` item 2 survey redaction | already fixed on `origin/compute-resource-survey-20261126` @ `58e6bbeb`; no `vla` left in the survey captures; ready to merge | survey branch | coordinator merge |

All deliverables were pushed to their own branches; nothing was force-pushed or amended. Captures ignored by
`.gitignore` (`.out`, `.log`, `*.jsonl`) were force-added unchanged where they are part of the record.

## Running / idle now

- **No job of ours is running.** TASL-2, TASL-7, deepthought2 and Ada are idle; the TASL leases and the screening
  scratch were released. Ada card 0 was left free by the P5 run; P.4 stays on the direct Ada route (author).
- Screening run directory and the eight deepthought scenes are preserved in place; nothing was resumed.

## Waiting / blocked

| Card | Waits for | Owner |
|---|---|---|
| `compute/20261128-05` item 1 / P11 remaining items (C2, C4, C5, C6, C9, C10 hours, C11 chunk side, C14, C15 pre-run, C16) | **the coordinator withdrew "checked at publication"**: `local/20261128-02` must supply the G.5 P11 engineering smoke path; then compute runs the items and gets a fresh review | local, then compute |
| `compute/20261128-01` E0 repeatability | author decision on AUTHOR.md: A (repeatability first, recommended), B (accept the difference), C (drop E0) — blocks the P.4 phase-1 note and A5 SFT | author |
| `compute/20261127-12`/`-03` D.3 batch preflight | a startable ETP L40S/TOpAS A100; `c03-001-175` still `Start=false`; re-read each round | compute |
| `compute/20261127-33` item 2 Ada P5 rerun | the E0 repeatability decision and a reviewed reference | author / compute |
| `compute/20261127-28` E-INT census | signed census spec/authorization and smoke; yields to Paper B | author / design |
| `compute/20261126-06` G.5 campaigns | G.5 note published (after the houseprice record and P11 review) | coordinator |
| `compute/20261126-07` P.4 phase-1 jobs | E0 repeatability decision and the phase-1 note | author / coordinator |
| `local/20261128-03` P10 kurtosis table / expansion P10 | local's table, then the expansion P10 step uses the accepted D6 copy | local |
| `compute/20261127-16` G1 next units | 6c replicate driver → G1 adapter at harness `9bb41680` (`verify_seed_base=20000`) → G6; a code unit, not started this round | compute |
| `compute/20261126-02` / `cluster/20261126-02` D.3 runner and G6 audit | per-arm smoke once rev 4 freezes | compute |
| `compute/20261126-03` rows (g) | acknowledged: free placement/shared cards used, no request edited, no wall-clock limit decided anything | — |

## Next-round checks, in order

1. Screening review is accepted; the coordinator publishes the analysis record and routes
   `R1_THEORY_RHO_2_FINAL` (D.3 step (8) on rev 4 per the note). Re-read `condor_status -pool
   c03-001-140.gridka.de` for `c03-001-175`; submit the D.3 preflight only when `Start` is true.
2. P11: take `local/20261128-02` when published, run the engineering smoke items, update the P11 record and get a
   fresh review.
3. E0: take the author's repeatability choice; if A, one repeat per host at this code/config/seed with the rule
   declared first; if B, the phase-1 note records the difference; if C, drop E0 and keep the smoke.
4. Remaining ready code: `compute/20261127-16` (6c replicate driver, then G1 adapter at `9bb41680`, then G6).
5. Idle hosts: deepthought2 free; TASL pair free; Ada free for Paper B first.

Round decided alone: host/card placement (TASL-7 for E0, deepthought2 for screening, TASL-2 for the CPU checks),
the force-add of ignored capture files, and stopping the deepthought screening retries; no tolerance, note, seed or
request was changed.
