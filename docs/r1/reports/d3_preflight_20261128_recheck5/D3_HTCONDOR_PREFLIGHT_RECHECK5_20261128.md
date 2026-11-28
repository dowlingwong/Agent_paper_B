# compute/20261128-03 — D.3 HTCondor preflight, fifth read: still no startable A100/L40S

**Result: not submitted. Every advertised GPU slot on the two named routes has `Start = false`; no request was
edited and no job id was created.** New since recheck 4: NEMO2's `g4401` advertises GPUs again (one 4-GPU slot with
4 free in `Claimed/Retiring`, plus unclaimed/`Drained` slots), but none of its slots is startable either.

- Task `compute/20261128-03` (= `compute/20261127-12`), PLAN R1-P4-D3-GPU-PREFLIGHT (2), ENGINEERING_ONLY.
- Read-only at `2026-11-28T17:42:05Z`–`17:42:09Z` from `deepthought2`; no submission from either pool.
- Round base `origin/main` `7cd65cfa`; queue `coord/coordinator` `52fb6892`.
- Captures: `condor_read.txt`, `stamp_utc.txt`, `stamp_end_utc.txt`, bound by `SHA256SUMS`.

## Slots read

| Machine (pool) | Device | GPUs / free | State / Activity | `Start` | `WithinResourceLimits` |
|---|---|---:|---|---|---|
| `c03-001-175` (TOpAS) | A100 | 8 / 8 | Unclaimed / Idle | **false** | — |
| `c03-001-175` (TOpAS) | A100 | 8 / 0 | Claimed / Busy | false | — |
| `g4401.nemo.privat` (NEMO2) | — | 4 / 4 | Claimed / Retiring | **false** | error |
| `g4401.nemo.privat` (NEMO2) | — | 4 / 0 | Unclaimed / Idle | false | error |
| `g4401.nemo.privat` (NEMO2) | — | 1 / 1 | Unclaimed / Idle | false | error |
| `g4401.nemo.privat` (NEMO2) | — | 1 / 1 | Drained / Idle | false | — |
| `deepthought2.etp.kit.edu` (ETP) | L40S | 2 / 1 | Unclaimed / Idle | **false** | error |
| `deepthought.etp.kit.edu` (ETP) | TITAN X | 4 / 2 | Unclaimed / Idle | false | error |

Exact expressions read from the ETP collector (`condor_status -af … Start Requirements WithinResourceLimits`):
every GPU slot above with `Start = false` also has `Requirements = false` and `WithinResourceLimits = error`. The
`c03-001-175` slots read `Start = false` from the TOpAS collector (`c03-001-140.gridka.de`).

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
R1-HOST-FREE for work not bound by a signed note (AUTHOR.md records the route as open, no new row required).

Decided alone: the read time, the two named routes only, and no submission. No request, pin, input or note was
changed.

**AI-assisted: DeepSeek compute agent, 28 Nov 2026. ENGINEERING_ONLY.**
