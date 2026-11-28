# compute/20261128-03 — D.3 HTCondor preflight, third re-check: still no startable A100/L40S

**Result: not submitted. `c03-001-175` advertises 8 A100 but `Start = false`; the ETP `deepthought2` L40S is
not advertised at this read. Nothing was worked around; no request was edited.**

- Task: `compute/20261128-03` (= `compute/20261127-12`), PLAN R1-P4-D3-GPU-PREFLIGHT (2), ENGINEERING_ONLY.
- Read-only at `2026-11-28T04:40:33Z` from `deepthought`; no job id exists for this attempt.
- Branch `compute-d3-preflight-recheck3-20261128` @ `36a852955387e14246a6fb260b7c6ddb49f9e454`.
- Record `docs/r1/reports/d3_preflight_20261128_recheck3/D3_HTCONDOR_PREFLIGHT_RECHECK3_20261128.md`,
  sha256 `e4d478218a75ebc36d38715073f99c5fc77ed03f12221a50cf14e69072afbbbb`; `SHA256SUMS` binds four captures.

| Machine | Device | Free GPUs | `Start` | `Requirements` |
|---|---|---:|---|---|
| `c03-001-175` (TOpAS) | A100-PCIE-40GB | 8 advertised | **false** | `Start && (WithinResourceLimits)`; `WithinResourceLimits` evaluates to an error |
| `deepthought2` (ETP) | L40S | — | — | machine not advertised |

`c03-001-159` is V100S; `c03-001-167` and `c03-001-179` advertise no free A100; no H200/H100 is advertised.
`condor_q -all` shows two running jobs owned by `friemer` (`760040.0`, `760103.0`); no `dwong` job is queued and
`760158.0` is no longer present. No job was touched.

Container digest, in-container GPU validation and input hashes remain unverified on the batch route; the P.4
probe stays on the direct Ada path. Next: re-read the two named routes each round and submit only on a matched
slot with `Start = true`.

Decided alone: the read time and stopping at the two named routes; no request change and no submission.
