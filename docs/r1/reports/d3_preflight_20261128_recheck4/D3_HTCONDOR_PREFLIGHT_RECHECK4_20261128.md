# D.3 HTCondor preflight re-check (fourth read) — still no startable A100 or L40S

Task `compute/20261128-03` (= `compute/20261127-12`), PLAN R1-P4-D3-GPU-PREFLIGHT (2). ENGINEERING_ONLY.
Read-only at `2026-11-28T12:59:30Z` from the submit host `deepthought`. No request was edited and no job was
submitted.

**Result: not submitted.** `c03-001-175` still advertises 8 A100 with `Start = false`; the ETP
`deepthought2` L40S is advertised again (2 GPUs) but with `Start = false`. The TITAN X slots and the NEMO2
GPUs also read `Start = false`.

| Machine | Device | Free GPUs | `Start` | Note |
|---|---|---:|---|---|
| `slot1@c03-001-175` (TOpAS) | A100 | 8 | **false** | `Requirements = Start && (WithinResourceLimits)` |
| `slot1_16@c03-001-175` (TOpAS) | A100 | 8 | false | Claimed Busy |
| `slot1@deepthought2` (ETP) | L40S | 2 | false | advertised again, unlike recheck 3 |
| `slot1@deepthought` (ETP) | TITAN X | 4 | false | — |
| `slot1@nemo2_gpu-…g4401` | — | 1 | false | — |
| `slot1@nemo2_gpu-…g4401` | — | 4 | false | — |

No H200 or H100 is advertised. `condor_q -pool c03-001-140.gridka.de -all` lists one running job, owned by
`friemer` (`760040.0`, JobStatus 2); no `dwong` job is queued on either view. No other job was touched.

## Captures

`condor_reads.txt` holds the four reads (slot-175 long form; the TOpAS GPU ads; `condor_q -all`; the ETP GPU
ads), and `read_time.txt` the read time. `SHA256SUMS` binds them and this record.

Container digest, in-container GPU validation and input hashes remain unverified on the batch route. The P.4
probe stays on the direct Ada path. The next read should submit only when a matched slot for the exact request
says `Start = true`.

Decided alone: to re-read both named routes at this round, to capture them without changing anything, and to
submit nothing because neither route is startable.
