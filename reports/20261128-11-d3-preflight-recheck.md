# compute/20261128-03 — D.3 HTCondor preflight re-check: still no startable A100/L40S

**Result: not submitted. Both named routes still advertise `Start = false`: `c03-001-175` has 7 free A100 but
`Requirements = false` (`Start && (WithinResourceLimits)`, `WithinResourceLimits` undefined); the ETP L40S on
deepthought2 has 1 free GPU and the same `Start = false`. Exact expressions captured; nothing worked around.**

- Task: `compute/20261128-03` (= `compute/20261127-12`), PLAN R1-P4-D3-GPU-PREFLIGHT (2), ENGINEERING_ONLY.
- Base `origin/main` `3013ddf0`; branch `compute-d3-preflight-recheck-20261128` @
  `c5e2df4ab1c07431bbfde5d99d5254f831fa16a7`.
- Record: `docs/r1/reports/d3_preflight_20261128_recheck/D3_HTCONDOR_PREFLIGHT_RECHECK_20261128.md` sha256
  `5d44af0518095a5b660997bb3bbdc32b586f979bfee4017417c34e0626aa08eb`; `SHA256SUMS` binds seven captures. Read-only
  check at `2026-11-28T01:32:01Z`.
- No job id exists for this attempt. No existing request was edited.

| Machine | Device | Free GPUs | `Start` | `Requirements` |
|---|---|---:|---|---|
| `c03-001-175` (TOpAS) | A100-PCIE-40GB | 7 of 8 | **false** | false (`WithinResourceLimits` undefined) |
| `deepthought2` (ETP) | L40S | 1 of 2 | **false** | false |

`c03-001-167` and `c03-001-179` advertise 0 free A100; `c03-001-159` is V100S. No H200/H100 is advertised.

**Active job checked before anything else:** `760158.0` (account `dwong`, R2 sparse-sk project,
`/work/dwong/r2_sparse_sk/.../lucid_torch_job.sh`, `RequestCpus = 4`, `RequestMemory = 32000`,
`slot1_4@c03-001-179`) is running; it is not a Paper B job and was not touched. The stale probes 759624/759625 remain
removed and 760065 withdrawn.

Container digest, in-container GPU validation and input hashes remain unverified on the batch route. P.4 stays on the
direct Ada path. Next: re-read `condor_status` each round and submit only when a matched slot says `Start = true`.
