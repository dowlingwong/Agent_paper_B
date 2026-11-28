# Compute round status — 28 November 2026, 07:58 UTC

Round base `origin/main` `8fbad26a`; queue read at `coord/coordinator` `11d09dd` (STATE dated 09:00 CET).
Resumed the P7 round's next checks and took the first runnable card, the recurring
`experiment/20261126-02` resource sample with `cluster/20261126-03` pool watch. Read-only; no job was
submitted, no lease was taken, no request edited, no sealed/test/label value read.

## Result

No runnable evidence or code card is left in the compute queue. The two execution cards still open are
blocked on host conditions that I re-read this round:

| Card | Check at 07:56–07:57Z | State |
|---|---|---|
| `compute/20261128-12` item 1 — P11 four TASL-7 scenarios | TASL-7 RTX 4090: one foreign compute process, 8,402 MiB (restarted at 07:57:24Z); 15,563 MiB free; `gpu0.lock` free | **blocked** — the reviewed G.5 code refuses to start its server beside foreign compute (R1-CARD-SHARE (5)); nothing killed, no workaround |
| `compute/20261128-03` (= `-12`) — D.3 HTCondor preflight | `c03-001-175` A100: 8 free GPUs but `Start = false`, `WithinResourceLimits = error`; no startable ETP L40S advertised; `condor_q` has only two `friemer` jobs, no `dwong` job | **no submit** — submit only when a matched slot says `Start = true`; no job id exists for this attempt |
| `compute/20261127-28` — Paper C E-INT census | Ada card 2 empty (48,427 MiB free) | **blocked** — the census draft still says "after a launch card and signed authorization"; no signed spec/cap/token budget yet |
| `compute/20261127-33` item 2 / P.4 P5 rerun | Ada card 2 empty; P.4 route on Ada | **blocked** — author's E0 criterion decision (`AUTHOR.md`, sheet `P4_E0_CRITERION_SHEET_20261128.md`) |
| `compute/20261126-06` — G.5 campaigns | TASL-2 and TASL-7 leases free / one foreign on TASL-7 | **blocked** — G.5 note not published (needs the P11 record and final render) |

## Resource samples (`experiment/20261126-02`)

| Host | CPUs / RAM | GPU | Driver | Disk | Occupancy |
|---|---|---|---|---|---|
| TASL-7 | 24 logical; 62 GiB (11 GiB free, 47 GiB cache) | RTX 4090, 24,564 MiB | 580.178.04 | 292 GiB free of 1.9 T (84 % used) | 8,510 MiB used, 15,563 MiB free; **one foreign compute process 8,402 MiB** (`jiachenl` Python, restarted 07:57:24Z; `tianyu` Codex shells idle). Our `gpu0.lock` free. |
| TASL-2 | 32 logical; 62 GiB | RTX 4090, 24,564 MiB | 535.309.01 | 336 GiB free of 1.9 T (82 % used) | 353 MiB display, 23,830 MiB free, no compute app; all four CPU-set locks (`0-3`, `4-7`, `12-15`, `16-31`) free |
| Ada (`ucrtasl`, `zli538`) | 96 logical; 503 GiB | 8 × RTX 6000 Ada, 49,140 MiB each | 545.23.08 | `/data1` 2.0 T free of 7.0 T (71 % used) | **card 2 empty (48,427 MiB free)**; cards 0, 1, 3, 4, 5, 6, 7 held by other users' processes (5 MiB–33.7 GiB); load 20.8 |
| deepthought | 40 logical; 503 GiB (453 GiB available) | 4 × GTX TITAN X, 12,288 MiB | — | `/work` 904 G free of 1.3 T; `/ceph` 332 T free of 1.4 P | load 4.34; card 1 has a foreign 4,189 MiB process; cards 0, 2, 3 ≈ 653 MiB each; no Paper B process |
| deepthought2 | 128 logical; 1,006 GiB (940 GiB available) | 2 × L40S, 46,068 MiB | — | same ETP mounts | load 5.40; GPU 0: 16,668 MiB used / 28,800 MiB free; GPU 1: 3 MiB used / 45,465 MiB free |

The values are snapshots, not reservations. COMPUTE.md's Ada CPU count can be updated from *to verify* to
96 logical CPUs / 503 GiB; nothing else in the card changed materially.

## Pool watch (`cluster/20261126-03`)

- `c03-001-175.gridka.de` (A100): partitionable slot Unclaimed/Idle, 8 GPUs free, but `Start = false` and
  `WithinResourceLimits = error`; not startable.
- No startable ETP L40S and no H200/H100 advertised. `c03-001-159` (V100S) and `c03-001-167`/`-179` carry
  foreign loads; no NEMO2 GPU of any model is back.
- `condor_q`: only `760040.0` and `760103.0` (`friemer`, running). No `dwong` job; the stale probes stay
  removed/withdrawn. No request changed.
- Job `760065` (P.4 H200) remains withdrawn; P.4 stays on the direct Ada route.

## Branches and records

- Report branch only: `coord/compute` (this file). No deliverable branch is needed for a read-only sample.
- Previous P7 deliverables remain where reported: `compute-d3a-p7-20261128` @ `3c12db25` (substantive
  `b730ee9b`), review `compute-d3a-p7-20261128-review` @ `b86e8966` (R2 ACCEPTED, R3 clean); merged
  `main` `8fbad26a`.
- P11 record remains `docs/r1/reports/g5_p11_engineering_20261128_rerun/` @
  `compute-g5-p11-matrix-rerun-20261128` `f963b1bb` (partial; four scenarios not yet run).

## What happens next (next round, in order)

1. Re-read TASL-7. When the card has no foreign compute, run `-determinism`, `-restart`, `-tar`,
   `-closeserver` from the clean `f7dc4945` checkout (specs for stamp `20261128T033600Z` are already under
   `~/r1_engineering/g5-p11`), append them to the P11 record, regenerate `SHA256SUMS`, then request one fresh
   review of the complete item table.
2. Re-read `condor_status` for `c03-001-175` and any ETP L40S; submit the D.3 preflight only on `Start = true`.
3. `local/20261128-08` (D.3a note fill and launch binding) then the author's P9 signature; no D.3 campaign
   before that note and its checks.
4. The G.5 campaigns wait on the published note; P.4 phase 1 waits on the author's E0 criterion; the E-INT
   census waits on a signed launch card/spec.

Rows (g) acknowledged: free placement and leases were used, no request was edited, no wall-clock limit
decided anything, and no sealed/test/label value was read.

Decided alone: to report the read-only samples without reserving any host, and to attempt no P11 scenario
while the reviewed lease check refuses the shared TASL-7 card.
