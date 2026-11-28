# Compute round status — 28 November 2026, 12:10 UTC

Round base `origin/main` `a70c8872` at the start; the queue was re-read after each task. Three units delivered
this round: P7 at the frozen runtime (STOP under rev 4), the complete P11 matrix (all scenarios PASS), and the
four fresh P.4 E0 runs (PASS under the new criterion). The coordinator merged P7 and P11 (`a70c8872`), then E0 (`d9ccf79a`) and the P5 smoke (`c11ce78b`);
all four delivered units now have accepted reviews.

## Delivered this round

| Task | Result | Branch @ tip | Review |
|---|---|---|---|
| `compute/20261128-15` — P7 at `-c 32768` q8_0 K/V | **STOP** under frozen rev 4: server fits (21,977 MiB), 14/14 campaigns, worker gate **50/276 = 18.12 %** vs 12.99 %; published 8k P7 was 33/271 = 12.18 % | `compute-d3a-p7-exact-20261128` @ `d0b3b35c` | `…-review` @ `688028b5`: **ACCEPTED** (re-check: 944/944 captures, 28/28 inner; per-seed corrected 22/138, 28/138). Merged `a70c8872`. The gate is re-read at rev 5 (18.53 %) by the coordinator. |
| `compute/20261128-12` item 1 / `-10` — G.5 P11 complete matrix | **PASS** on the four remaining scenarios: determinism (200/200/10 same outcomes, 0 diffs), restart (STOP 12, 33 s + 27 s servers), tar (`out_clear.tar`, 1,130 files), close-server (closed true, 20 s) | `compute-g5-p11-matrix-complete-20261128` @ `0ce1e664` | `…-review` @ `b186d017`: **ACCEPTED** (420/420 captures; 08:37 refusal explained). Merged `a70c8872`. |
| `compute/20261127-33` item 2 — P5 staged smoke on the per-card lease | **PASS**: Ada card 2, all four kernels bound, bf16 rel err 0.002875, 3,345 MiB, 26 s, 0 foreign | `compute-p5-smoke-percard-20261128` @ `1e8b4aec` | `…-review` @ `f422df34`: **ACCEPTED**; merged `c11ce78b` |
| `compute/20261128-16` — P.4 E0 fresh runs | **PASS**: 4 fresh runs, all slope pairs within 0.05; RPS host means differ by **2.9494e-5** ≤ 3.04e-5; 2.7936 GPU-h | `compute-p4-e0-fresh-20261128` @ `c22ba021` | `…-review` @ `0bd80f7a`: **ACCEPTED** (one minor: TASL-7 within-host absolute spread 4.5e-5 exceeds the cross-host limit; the pass relies on mean cancellation) |

## Hosts and jobs at 12:07–12:08Z

| Host | State |
|---|---|
| TASL-2 | idle; RTX 4090 353 MiB display, 23,830 MiB free; no Paper B process; load 0.31 |
| TASL-7 | idle; RTX 4090 44 MiB, 24,029 MiB free; no Paper B process; load 0.06 |
| Ada | card 2 empty (48,427 MiB free); cards 0,1,3–7 held by other users; no Paper B job |
| deepthought / deepthought2 | no `dwong` Paper B job; deepthought load 5.9, 1 foreign job in `condor_q` |
| HTCondor | no A100/L40S/H200 advertised as startable; no `dwong` job |

No active job ID is recorded for this round: P7, P11 and E0 all completed; no submission was made.

## Blocked / pending

| Card | Waits for | Owner |
|---|---|---|
| `compute/20261128-16` E0 | review **ACCEPTED**; coordinator merge | coordinator |
| `compute/20261127-33` item 2 — P5 smoke | **done**; merged `c11ce78b`; the timing carry-forward is the remaining P.4 phase-1 review item | design / local |
| `compute/20261126-06` — G.5 campaigns | published G.5 note; final render ACCEPTED (`6466e044`), publication held for `local/20261128-11` fixture fix | coordinator / local |
| `compute/20261128-03` — D.3 batch preflight | a `Start=true` ETP L40S / TOpAS A100; none advertised at 12:07Z | compute, re-read each round |
| `compute/20261127-28` — E-INT census | signed census card/spec and a free Ada card; Paper B priority | author / design |
| `compute/20261127-05`/`-08` — G.5 P11 host tests | closed by the complete matrix; nothing remains | — |

Expansion D6 copy, the resource survey and the houseprice CPU-set check remain as recorded; no new compute
work is blocked on the P7/P11 results now that both are merged.

## Next round, in order

1. Read the E0 review; apply any findings and re-check until accepted; then the coordinator can merge it.
2. Take the P5 rerun (`compute/20261127-33` item 2) once E0 is accepted; empty Ada card 2 is available now.
3. Re-read the HTCondor pool for a startable L40S/A100; submit the D.3 preflight only on `Start=true`.
4. G.5 campaigns start only after the published note and its strict check.

**Rows (g) acknowledged:** free placement and the card/CPU-set leases were used, no request was edited to get
a slot, no wall-clock limit decided anything, and no sealed/test/label value was read.

Decided alone: the P7 exact server and fresh work root, the P11 scenario placement and IDs, the E0 card/run
placement and comparator, and the restart/stop decisions recorded in each unit. No signed value was changed.
