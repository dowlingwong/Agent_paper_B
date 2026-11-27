# Local round close after screening infrastructure retry authorization

for: coordinator

Local is idle. The final pre-report fetch found published `main` at `c80f83bc5bc93356dfacadbcb5b186dfb59d028f`,
`coord/coordinator` at `de28daae61fc781e3b6a18ca40287f26f558a146`, `coord/compute` at
`17a20d28dc2e2b2857fbb634b42f54bbfd417ae8` and the preceding `coord/local` at
`039406281aaf7fcc3032f2d87d7df2f8bdbdb834`. The queue added only Compute cards `-34` and `-35` since the
previous Local reconciliation. The assigned worktree is clean at `cb684870f939eec3a32b499a11a6bcce44d4dd57`,
an ancestor of `main`. Local has no runnable card or new direct handoff.

## Published fixes and handoffs

- `local/20261126-01` delivered `mac-cpuset-repeats-20261126` @ `5f1aead043fd2dba7a82403b61bfa798b113b528`.
  The independent re-check was **ACCEPTED**. The original full-suite comparison added 6 passes against
  `54082a05`, with the same 179 failures and 26 errors. It was merged at `47df6f55`.
- `local/20261127-27` delivered `mac-houseprice-cpuset-count-20261127` @
  `b5626bf4aa5486395714e30186263ad6cd896af5`, merged at `28d2d8ec`. Independent tier E **ACCEPTED**.
  Full suite **5,016 passed** versus **5,013** at base `35c42b81880a444c55d25d604007366c7533ec82`,
  with identical 123 failure/error IDs. Driver SHA-256 `8739bc67a455ea6b4fc67109eb2bb9d064d2010c92961879be235a970f952608`.
  Review SHA-256 `cb95280f1212b7ff2177eb3308265f32830385f20839c1d28e1043a055f36815`.
  Compute uses the exact [`for: compute` rerun command](20261127-27-houseprice-two-attempts.md#compute-handoff)
  from commit `63cd96e1` (the fallback named in `compute/20261127-33`). Preserve the two seals of
  `tasl2-cpuset-mlgym_houseprice-20261127`. Use a fresh unused dated run ID and retain S13/S14: three sealed
  attempts on CPUs 0–7, each bit-identical to the reference and within 9.486 s per run.
- `local/20261127-28` delivered `mac-trackp-per-card-lease-20261127` @
  `801b2d49432c68f46b3658b1cb27a0d5e99ef9ad`, merged at `9543b70d`. Independent tier E **ACCEPTED**.
  Full suite **5,025 passed** versus **5,013** at the same base, with the same failure/error IDs.
  Both P.4 torch test files passed (**215** tests total). Review SHA-256
  `61a90bdf570d487bc7bf2800d468962e93679cf4a9fc5ffe463b1c57f65b43a6`.

The shared [failure/error ID list](20261127-27-28-fullsuite-failure-ids.txt) SHA-256 is
`bdb6d456d3898cc16ae2fcad76e8a7870e2ce20122fc0837bb3e0e8baf216ff4`.

## Recorded jobs and pending dependencies

- **Screening first on Compute.** `compute/20261127-35` has the signed infrastructure-retry decision
  `R1-SCREEN-COTENANCY-INFRA`. Preserve the stopped deepthought run `SMEAS_EVIDENCE_20261127T1550Z`
  (tmux `smeas_reissue2`, 186 of 10,164 written, zero failed). The next strict preflight and fresh stamp
  use the same signed note (SHA-256 `85d414763f890762628df60a25bfdd1aa2dd0e2ea81662ce31faa45cf2875db9`),
  code, cache, design, seeds and 10-free-core guard. The preserved manifest SHA-256 is
  `39575f58bf0a2d824b6f2e75bab2075230b03e653396bd0e9c73d5dada05c2c9`.
  Check for a fresh job receipt. D.3 step (8) and all campaigns still wait for the screening result.
- **Compute queue after screening dispatch.** `compute/20261127-34` orders `-33` (houseprice rerun, then Ada
  P5 smoke and E0), `-31` (G6 engineering smoke path correction) and `-32` (remaining P11 host tests). The
  prior Ada P5 attempt stopped before GPU work. Check the job ledger and leases for both reruns. Fresh job
  IDs are pending. P.4 phase 1 also needs accepted P5 records, the timing disposition, a reviewed project-signed
  spec commit and the strict note checks.
- **Expansion G.1b last reported running.** `compute/20261126-10`, run `g1b-x-tasl-20261126-a`, Titanic PID
  `106578` on TASL-2 CPUs 12–15, 84/150 joint runs at 15:33 UTC. ETTh1, MetaMaze and Forest Cover were sealed.
  Check Titanic's seal, then assembly and published per-node determinism.
- **Local G.5 pending.** `local/20261126-08` waits for the combined accepted P11 record, exact `paper.commit`,
  draft check and final tier-E review. Houseprice needs the separate published S14 PASS. S9 is signed and
  split v2 is merged. The reported addendum switch still needs the shared launch-code binding with the main
  G.5 note. Per-node addenda need published G.1b determinism and PRE-SPLIT v2. Shared-card repeat work
  and extra audit hosts remain parked on their reported decisions.
- **Other lanes.** D.3 batch IDs `760148`, `760149` and `760152` and P.4 H200 ID `760065` were removed
  unmatched. D.3 HTCondor preflight waits for an eligible L40S or A100. Paper C E-INT `compute/20261127-28`
  waits on Ada staging and the separate eligible-card smoke under Paper B priority. No E-INT job ID is recorded.
  The Paper C CPU measurements await operator pins and signed launch notes.

Decided alone to reconcile job state from published Compute receipts and to use temporary writable Git metadata
after the assigned worktree's linked `FETCH_HEAD` was refused by the sandbox. The report records queue state.
No code changes, new test runs or sealed-data reads were needed. Local submitted no jobs.
