# Local round close — 27 November 2026

Published base `1afa7d62ffd98709a100de6e725d123cbc272a73`. Queue `ac90b07d6265e7d49fac98865313ad4c36fdc447`.
Compute reports `17a20d28dc2e2b2857fbb634b42f54bbfd417ae8`. Local is idle. The queue has no further runnable local
card. All 15 modified or untracked paths in the assigned worktree match published main byte for byte.
Local launched no job.

## Verified deliveries

- **`local/20261127-30`.** PRE-SPLIT v2, branch tip `486d1150`, independent review **ACCEPTED**, published
  at `a5a14901`. The reported release checker passed. Published amendment SHA-256
  `970d3e45b5177f0d9f6668e9495905e1878a4ffa8eab3d73c4df6b9292a3bea7`.
  The expansion binding tip `93915fec` is merged at `1afa7d62`, independent tier-E re-check **ACCEPTED**.
  The reported suite had 4,717 passes versus 4,694 at base `f43823da`, with the same 170 failure/error IDs.
  Published binding review SHA-256 `8c398d2e614c79f38d2cd876a78cf4661704f188513f6a25288d2041c1aef836`.
  See [unit 1](20261127-30a-presplit-publication-prep.md) and [unit 2](20261127-30b-g5-expansion-binding.md).
- **`local/20261126-01` and `local/20261127-27`.** Both houseprice fixes are published. The follow-up tip
  `b5626bf4` is in `1f1b5d41`, independent tier-E re-check **ACCEPTED**. The reported suite had 5,016 passes
  versus 5,013 at base `35c42b81`, with the same 123 failure/error IDs. Published driver SHA-256
  `8739bc67a455ea6b4fc67109eb2bb9d064d2010c92961879be235a970f952608`.
  Compute has the [exact rerun command](20261127-27-houseprice-two-attempts.md#compute-handoff).
  Preserve `tasl2-cpuset-mlgym_houseprice-20261127` with its two seals. For `compute/20261127-33`,
  check for a fresh S14 receipt with three sealed attempts on CPUs 0–7, bit-identical to the reference,
  each within 9.486 s. No fresh houseprice run ID was seen.

## Next receipts

- **Ada P5, `compute/20261127-33`.** The latest worker-pane poll showed E0 final active as PID `5542`,
  run `p5_20261127_b/e0e` (elapsed 25:43). Check for the final accepted smoke, equivalence and timing
  receipts before the coordinator's phase-1 publication checks.
- **Screening, `compute/20261127-35`.** Check for a fresh strict-preflight receipt and run stamp under
  R1-SCREEN-COTENANCY-INFRA. The stopped `SMEAS_EVIDENCE_20261127T1550Z` (tmux `smeas_reissue2`,
  186 of 10,164 written) is the latest published scene. D.3 step (8) waits for the screening result.
  HTCondor preflight IDs `760148`, `760149` and `760152` were removed unmatched. An eligible L40S or A100
  match is still pending.
- **G.5 base render, `local/20261126-08`.** Waits for the accepted combined P11 record
  (`compute/20261127-32`), the published S14 PASS, the final `paper.commit`, note checks and tier-E review.
  All four expansion G.1b nodes sealed with determinism PASS under `g1b-x-tasl-20261126-a`.
  The expansion addenda wait for the reviewed D6 copy (`compute/20261127-36`), the author P10 declarations
  and each node's pin and strict check. Shared-card repeat work and additional audit hosts await their decisions.
- **Paper C.** `compute/20261127-28` awaits an eligible Ada card and the staged E-INT smoke.
  The CPU measurements remain pending operator pins and signed notes.

Decided alone to check task ancestry, published artifact hashes, the worktree bytes and recorded job IDs.
The sandbox denied a write to the linked worktree's FETCH_HEAD. The fetch and this report use temporary Git
metadata. This is a status reconciliation. The cited tests and reviews are the existing delivery records.
