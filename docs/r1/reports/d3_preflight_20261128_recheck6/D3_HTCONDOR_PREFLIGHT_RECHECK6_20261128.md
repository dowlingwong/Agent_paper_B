# compute/20261128-03 — D.3 HTCondor preflight, sixth read: still no startable A100/L40S

**Result: not submitted. Every GPU slot on the two named routes reads `Start = false`; no request was edited and no
job id was created.** The TOpAS A100 host `c03-001-175` now advertises a single eight-GPU partitionable slot with
176 CPUs, and NEMO2's `g4401` advertises an unclaimed four-GPU slot, but both still refuse jobs at the machine start
policy (`Requirements = false`, `WithinResourceLimits = error`).

- Task `compute/20261128-03` (= `compute/20261127-12`), PLAN R1-P4-D3-GPU-PREFLIGHT (2), ENGINEERING_ONLY.
- Read-only at `2026-11-28T18:16:04Z` from `deepthought2`; no submission from either pool. The immediately preceding
  observation at `18:15:17Z` showed the same `Start = false` values.
- Round base `origin/main` `f532176f`; queue `coord/coordinator` `8aec575a`.
- Captures: `condor_read.txt`, `stamp_utc.txt`, `stamp_end_utc.txt`, bound by `SHA256SUMS`.

## Slots read

| Machine (pool) | Device | Total GPUs / slot GPUs | CPUs | State / Activity | `Start` | `Requirements` | `WithinResourceLimits` |
|---|---|---:|---:|---|---|---|---|
| `c03-001-175` (TOpAS) | A100 | 8 / 8 | 176 | Unclaimed / Idle | **false** | false | error |
| `c03-001-175` (TOpAS), dynamic | A100 | 8 / 0 | 16 | Claimed / Busy | false | false | error |
| `g4401.nemo.privat` (NEMO2) | — | 4 / 4 | 48 | Unclaimed / Idle | **false** | false | error |
| `g4401.nemo.privat` (NEMO2) | — | 4 / 4 | 16 | Claimed / Retiring | **false** | false | error |
| `g4401.nemo.privat` (NEMO2) | — | 1 / 1 | 16 | Drained / Idle | false | undefined | undefined |
| `deepthought2.etp.kit.edu` (ETP) | L40S | 2 / 1 | 32 | Unclaimed / Idle | **false** | false | error |
| `deepthought.etp.kit.edu` (ETP) | TITAN X | 4 / 2 | 10 | Unclaimed / Idle | false | false | error |

Exact expressions were read from the ETP collector (`condor_status -pool f03-001-140-e.gridka.de -constraint
'TotalGPUs > 0' -af …`) and from the TOpAS collector (`condor_status -pool c03-001-140.gridka.de`). The two
`c03-001-175` slots read `Start = false` on the TOpAS collector; the other TOpAS GPU slots read `Start = undefined`
with `Requirements = error` (no usable start expression) or `false`. No slot on either named route is startable.

## Queue

`condor_q -submitter dwong` on the ETP collector lists only the three held Paper A probes from 22 Nov —
`5045947.0`, `5045949.0`, `5045952.0` (all `JobStatus 5` with their recorded hold reasons). The TOpAS collector lists
no `dwong` job. No Paper B job is queued or running, and the three held ids were not touched.

## What is unverified

The candidate container digest, in-container GPU validation and staged input hashes remain unverified on the batch
route: no startable slot exists to run them. The direct Ada route is unaffected (P.4 stays on Ada; see
`compute/20261128-19`). Pending the author's P3 signature, P.4 phase 1 remains blocked at its note, not here.

## What happens next

Re-read both collectors next round; submit only on a matched slot with `Start = true`, with the pinned container and
the inputs and hashes checked inside the job. If no slot opens, D.3's proposer may run on Ada or the TASL pair under
R1-HOST-FREE for work not bound by a signed note (`AUTHOR.md` records the route as open, no new row required).

Decided alone: the read time, the two named routes only, and no submission. No request, pin, input or note was
changed.

**AI-assisted: DeepSeek compute agent, 28 Nov 2026. ENGINEERING_ONLY.**
