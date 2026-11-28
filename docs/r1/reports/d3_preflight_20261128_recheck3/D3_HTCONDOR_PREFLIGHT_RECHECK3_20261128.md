# D.3 HTCondor preflight re-check (third read) — no startable A100 or L40S

Task `compute/20261128-03` (= `compute/20261127-12`), PLAN R1-P4-D3-GPU-PREFLIGHT (2). ENGINEERING_ONLY.
Read-only at `2026-11-28T04:40:33Z` from the submit host `deepthought`. No request was edited and no job was
submitted.

**Result: not submitted.** The only advertised A100 machine `c03-001-175` still has `Start = false`; the ETP
`deepthought2` L40S is not advertised in the pool at this read.

| Machine | Device | Free GPUs | `Start` | `Requirements` |
|---|---|---:|---|---|
| `c03-001-175` (TOpAS) | A100-PCIE-40GB | 8 advertised | **false** | `Start && (WithinResourceLimits)`; `WithinResourceLimits` evaluates to an error |
| `deepthought2` (ETP) | L40S | — | — | machine not advertised (`condor_status` returns no name matching `deepthought`) |

`c03-001-159` is V100S; `c03-001-167` and `c03-001-179` advertise no free A100. No H200 or H100 is advertised.

## Active jobs checked before anything else

`condor_q -pool c03-001-140.gridka.de -all` lists two jobs, both owned by `friemer` (`760040.0`, `760103.0`,
JobStatus 2 = Running). No `dwong` job is queued on this view; the earlier `760158.0` (R2 sparse-sk project) is no
longer in the queue. No other job was touched.

## Captures

- `condor_status_slot175_long.txt` — `condor_status -long slot1@c03-001-175.gridka.de` plus the read time.
- `condor_status_gpu_ads.txt` — `condor_status -constraint "TotalGpus > 0" -af Name Start Requirements Cpus TotalGpus`.
- `condor_q_all.txt` — `condor_q -all -af ClusterId ProcId Owner JobStatus Cmd`.
- `condor_status_deepthought2.txt` — the name scan for the ETP L40S machine.
- `SHA256SUMS` binds the four captures.

Container digest, in-container GPU validation and input hashes remain unverified on the batch route. The P.4
probe stays on the direct Ada path. The next read should submit only when a matched slot for the exact request
says `Start = true`.

Decided alone: to re-read the pool at this round, to capture the two named routes only, and to submit nothing
because neither route is startable.
