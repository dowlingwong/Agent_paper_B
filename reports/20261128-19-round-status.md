# Compute round status — 28 November 2026, 05:10 UTC

Round base `origin/main` `f7dc4945` for the P11 matrix and `dbce0316` for P8; queue read at
`coord/coordinator` `8451232a`. No Paper B job is running anywhere.

## Delivered this round

| Task | Result | Branch @ tip | Review |
|---|---|---|---|
| `compute/20261128-10` P11 matrix rerun | **PARTIAL / BLOCKED**: primary `-lease` matrix PASS on both nodes (two campaign waves, all audit chunks, TASL-7 chunk, seals, meter), `-infra` STOP 7 PASS; `-determinism`, `-restart`, `-tar`, `-closeserver` blocked by foreign compute on the TASL-7 card | `compute-g5-p11-matrix-rerun-20261128` @ `f963b1bb` | not requested (record is partial; `SHA256SUMS` 289/289 from a clean checkout) |
| `compute/20261128-11` item 3 P8 | **PASS**: e1 environment and `uv.lock`, harness `9bb41680` path identity, 16-worker co-tenancy (min 34.07 free), D.3a projection 13.1 worker-h / 49 min | `compute-d3a-p8-host-20261128` @ `4fb1fae3` | `compute-d3a-p8-host-20261128-review` @ `5131f204`, **ACCEPTED** (`e7f6adbc…`) after two fix rounds |
| `compute/20261128-03` D.3 preflight | **No submit**: `c03-001-175` A100 `Start = false`, ETP L40S not advertised; no job id | `compute-d3-preflight-recheck3-20261128` @ `36a85295` | report-only |

Key P11 hashes: primary spec `f5365e84…`; server-1 `27174cf7…`; server-2 `5a4e34ee…`; TASL-7 registration
`47807f81…`, `out.tar` `33a47644…`; record `910a1395…`; `SHA256SUMS` `a78f4e7c…`. P8 record `72f2b9bd…`; review
`e7f6adbc…`.

## P11 block — exact dependency

TASL-7 is not empty: `tianyu` Jupyter kernel PID 2599483 (802 MiB, 56 min at 05:09Z) and a `jiachenl` benchmark
(PID 2645354, 6262 MiB) were on the card. The repaired G.5 server refuses to start beside foreign compute:

```
STOP: foreign compute processes on the leased GPU before the server: [{'pid': 2624911, 'used_memory': '386 MiB'}]
(no shared card)
```

`gpu0.lock` is free; the code's own process check is what refuses. Nothing was killed or worked around. The four
scenarios have their specs ready under `~/r1_engineering/g5-p11` with stamp `20261128T033600Z`; they need the
card empty and the same clean `f7dc4945` checkout.

## Hosts and jobs

| Host | State |
|---|---|
| TASL-2 | idle; no compute apps; `gpu0.lock` and CPU locks free |
| TASL-7 | `tianyu` 802 MiB and `jiachenl` 6.2 GiB foreign; our lease free; no Paper B process |
| deepthought | P8 read complete; 40 CPUs; no Paper B job left |
| Ada | not used this round; no P7 layout decision made |
| HTCondor | `c03-001-175` Start false; no `dwong` job; `friemer` has two running jobs (not touched) |

## Next round, in order

1. Read TASL-7 for an empty card. If empty, run the four remaining P11 scenarios from `f7dc4945` (fresh
   directories under the existing stamp or a new one), append to the P11 record, regenerate `SHA256SUMS`, then
   request one fresh review of the complete P11 item table.
2. Take the P7 layout proposal (`compute/20261128-11` item 1) and run the seven-arm smoke on each proposed model
   once P11 is recorded; TASL-2 and Ada are the candidates while TASL-7 is shared.
3. Re-read the HTCondor pool; submit only on `Start = true`.
4. `compute/20261126-06` G.5 campaigns still wait on the published note; `compute/20261127-28` E-INT waits on
   the signed spec and staged data; P.4 waits on the author's E0 criterion; D6 copy waits on `local/20261128-01`.

Rows (g) acknowledged: placement followed fit under R1-HOST-FREE, no request was edited to get a slot, no
wall-clock limit decided anything, and no sealed/test/label value was read.

Decided alone: the P11 host placement and fresh stamp, stopping the primary server for the C11 chunk, the P8
65-second co-tenancy load, and submitting no D.3 batch job while the slots are not startable.
