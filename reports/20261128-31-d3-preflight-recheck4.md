# compute/20261128-03 — D.3 HTCondor preflight, fourth read: still no startable A100/L40S

**Result: not submitted. `c03-001-175` advertises 8 A100 with `Start = false`; `deepthought2` advertises its
L40S again (2 GPUs) but also `Start = false`. Nothing was worked around; no request was edited; no job id.**

- Task `compute/20261128-03` (= `compute/20261127-12`), PLAN R1-P4-D3-GPU-PREFLIGHT (2), ENGINEERING_ONLY.
- Read-only at `2026-11-28T12:59:30Z` from `deepthought`.
- Branch `compute-d3-preflight-recheck4-20261128` @ `b2fb053987a8585b2ff4aec40c5141d37b5bc507`.
- Record `docs/r1/reports/d3_preflight_20261128_recheck4/D3_HTCONDOR_PREFLIGHT_RECHECK4_20261128.md`
  sha256 `6b7578c68e6e76b1c9814b854d29cd7441b8272f3e57a15d5ec53929b71fdb4f`; `SHA256SUMS` binds the reads.

| Machine | Device | GPUs | `Start` |
|---|---|---:|---|
| `slot1@c03-001-175` (TOpAS) | A100 | 8 | **false** |
| `slot1_16@c03-001-175` | A100 | 8 | false (Claimed Busy) |
| `slot1@deepthought2` (ETP) | L40S | 2 | false |
| `slot1@deepthought` | TITAN X | 4 | false |
| NEMO2 `g4401` slots | — | 1 + 4 | false |

`condor_q -pool c03-001-140.gridka.de -all` lists one running job, `friemer` `760040.0`; no `dwong` job is
queued. No other job was touched. The change from recheck 3 is that `deepthought2` is advertised again; it is
still not startable.

Container digest, in-container GPU validation and input hashes remain unverified on the batch route. P.4 stays
on the direct Ada path. Next: re-read both routes; submit only on a matched slot with `Start = true`.

Decided alone: the read time, the two named routes only, and no submission.
