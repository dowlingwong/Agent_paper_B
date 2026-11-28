# Compute round status — 28 November 2026, 14:25 UTC

Round base `origin/main` `66aa4e10`; queue `coord/coordinator` `216f33ea`. Two units this round: P.4 P3/P5
(`compute/20261128-19`) and the G.5 expansion host checks (`compute/20261128-20`, two of four nodes). No evidence
campaign ran; no job ID is open for compute.

## Delivered

| Task | Result | Branch @ tip | Review |
|---|---|---|---|
| `compute/20261128-19` — P.4 P3 signature, P5 timing | **P3 STOP** (no project SSH signing identity on any host reached); **P5 PASS**: four 50-step timing probes on Ada card 2 with in-process kernel capture; all four fast kernels, total 0.3233 GPU-h | `compute-p4-p5-timing-20261128` @ `902ef2c67c2d7f487b951fefde6e0dc9e5cfa02f` | `8a5316f1`, **ACCEPTED WITH MINORS** |
| `compute/20261128-20` — G.5 expansion host checks | Titanic **PASS** 1-7 at `d2ce4701`; MetaMaze **PASS** 1-7 at `3f92d3c3`; ETTh1/Forest blocked on Local | `compute-g5-expansion-isolation-titanic-20261128` @ `af191d0119976aeb2f47762f31ab11003d477e33` | Titanic `b07ae34d`, MetaMaze `9f930de3`, both **ACCEPTED WITH MINORS** |

Records/hashes: P5 record `P4_P5_TIMING_20261128.md` (43/43 capture sums); Titanic host record
`3d76372d…` (32/32); MetaMaze host record `80581d24…` (32/32). The review minors are documentation-only and the
reviewed records are left byte-identical (the count line says 31 capture files where the set has 32; the shas bind
the actual set). Full details in reports `20261128-32` and `20261128-33`.

## Blocked / pending

| Card | Waits for | Owner | Job id |
|---|---|---|---|
| `compute/20261128-18` G.5 launch | author's **"G.5 启动 A"** (merge `compute-g5-launch-base-20261128` @ `2178bc6e`, then launch from its tip, not the merge) | author → coordinator → compute | none |
| `compute/20261128-20` ETTh1 / Forest Cover | Local's per-node handoffs (full suite at `6fc553df` / `3f7b09fe`, tier E); worktrees, run roots, data links and patched node rows are prepared | local → compute | none |
| `compute/20261127-28` E-INT census | published `docs/r1/authorizations/paperc_eint_census_20261127.md` (absent) and a signed spec | author/design → compute | none |
| D.3 batch proposer preflight (`compute/20261128-03`) | a `Start=true` ETP L40S or TOpAS A100 on the exact request; the 14:09Z read showed the ETP L40S still `Start=false`, and recheck 4 (12:59Z) remains the current A100 record (`c03-001-175`, `Start=false`); no `dwong` job | compute, re-read each round | none |
| P.4 phase-1 note | author signing `befb58c8`; Local's P3 fill and P5 carry-forward; final tier-E review | author/local | none |

## Hosts at 14:09–14:12Z

| Host | State |
|---|---|
| TASL-2 | idle after the two host checks; RTX 4090 353 MiB / 0 %, no Paper B process; load ~0.1 |
| TASL-7 | idle; RTX 4090 44 MiB / 0 %, no Paper B process |
| Ada | card 2 empty (5 MiB, 49,140 MiB); cards 0,1,3–7 held by other users; no Paper B process |
| deepthought / deepthought2 | no `dwong` HTCondor job; no startable A100/L40S |

## End of round

No runnable compute card is left. Next round checks, in order: (1) the author's G.5 launch reply and the
coordinator's merge of `compute-g5-launch-base-20261128`; (2) Local's ETTh1/Forest Cover handoffs, then run those
two host checks; (3) `condor_status` for a startable A100/L40S and the exact request; (4) the E-INT authorization
note and a free Ada card; (5) any new P.4 unit after the signature. The recurring host/pool sample continues.

**Rows (g) acknowledged:** free placement and the card/CPU-set leases were used only for the named checks and
reads; no request was edited to get a slot; no wall-clock limit decided anything; no sealed/test/label value was
read; no other user's process was touched.

Decided alone: the two-node order (Titanic then MetaMaze as their handoffs arrived), new worktrees and run roots at
the exact pins, the manual timing capture with a `PYTHONPATH` hook rather than a new formal probe id, and stopping
P3 rather than signing with a non-project key. No signed value, spec, seed or request was changed.
