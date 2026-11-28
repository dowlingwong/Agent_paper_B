# D.3 HTCondor single-GPU preflight — re-check, still no startable A100 / L40S

Task `compute/20261128-03` (= `compute/20261127-12`), PLAN **R1-P4-D3-GPU-PREFLIGHT (2)**, ENGINEERING_ONLY.
Base `origin/main` `3013ddf0`. Read-only scheduler check on the deepthought submit host; **no job was submitted
and no request was edited**.

## Result

The two named classes still cannot start the intended single-GPU request:

| Machine | Device | Free GPUs | `State` / `Activity` | `Start` | `Requirements` | `WithinResourceLimits` |
|---|---|---:|---|---|---|---|
| `c03-001-175` (TOpAS, schedd `c03-001-140`) | A100-PCIE-40GB | 7 of 8 | Unclaimed / Idle | **false** | **false** (`Start && (WithinResourceLimits)`) | error (undefined) |
| `deepthought2` (ETP, collector `f03-001-140-e`) | L40S | 1 of 2 | Unclaimed / Idle | **false** | **false** | error (undefined) |

The other TOpAS A100s advertise no free GPU: `c03-001-167` and `c03-001-179` each show `GPUs = 0` on the
partitionable slot; `c03-001-159` is the V100S class and is not the named class. No ETP H200/H100 is advertised
by the collector. Exact captures and expressions are in `captures/`.

Because `Start = false`, no request can be matched on the 7-free-GPU A100 `c03-001-175` or on the free L40S
without an operator changing the start policy. No request was edited to get a slot.

## Active jobs (checked before any submission)

`condor_q -nobatch` at `2026-11-28T01:32:04Z`: one job of account `dwong` is running, `760158.0`, from the
**R2 sparse-sk** project (`/work/dwong/r2_sparse_sk/.../lucid_torch_job.sh`, `RequestCpus = 4`,
`RequestMemory = 32000`, `RemoteHost = slot1_4@c03-001-179.gridka.de`, started 27 Nov 14:00). It is not a Paper B
job and was not touched; it occupies the A100 host that already advertises `GPUs = 0`. The stale probes
`759624`/`759625` and the withdrawn `760065` remain absent from the queue.

## Unverified

- Container digest, in-container GPU validation, input staging and in-container input hashes remain unverified on
  the batch route because no job matched. Nothing about the container is asserted here.
- The P.4 route stays on the direct Ada path (author, 28 Nov); this preflight gates only the D.3 batch route.

## Next check

Re-read `condor_status -pool c03-001-140.gridka.de` for `c03-001-175` and the ETP collector for the L40S each
round. Submit only when a matched slot advertises `Start = true`; keep the TOpAS input staging by HTCondor file
transfer and the in-container hash check for that job.

Decided alone: only the host/time of the read-only check; no scheduler state was changed.
