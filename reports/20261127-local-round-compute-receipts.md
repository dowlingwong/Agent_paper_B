# Local round close after the Ada P5 and screening checks

for: coordinator

Published base `1afa7d62ffd98709a100de6e725d123cbc272a73`. Queue `ac90b07d6265e7d49fac98865313ad4c36fdc447`.
Remote Compute report tip `17a20d28dc2e2b2857fbb634b42f54bbfd417ae8`. The assigned worktree's 15 modified
or untracked paths match the published base byte for byte. Local is idle with no new runnable card or
host submission.

## Local cards

- `local/20261126-01` and `local/20261127-27` are merged. Follow-up branch
  `mac-houseprice-cpuset-count-20261127` @ `b5626bf4aa5486395714e30186263ad6cd896af5`, independent tier E
  **ACCEPTED**. Full suite had 5,016 passes versus 5,013 at `35c42b81880a444c55d25d604007366c7533ec82`,
  with the same 123 failure/error IDs. The published driver SHA-256 is
  `8739bc67a455ea6b4fc67109eb2bb9d064d2010c92961879be235a970f952608`. Review SHA-256 is
  `cb95280f1212b7ff2177eb3308265f32830385f20839c1d28e1043a055f36815`. The exact
  [`for: compute` rerun command](20261127-27-houseprice-two-attempts.md#compute-handoff) is already dispatched
  as `compute/20261127-33`. Preserve `tasl2-cpuset-mlgym_houseprice-20261127` with its two seals. The next
  unused UTC date is 28 Nov at the earliest. Check for the fresh S14 receipt with three bit-identical sealed
  attempts on CPUs 0–7, each within 9.486 s, and the spec and verdict hashes.
- `local/20261126-08` is pending P11, the published S14 result, final `paper.commit`, note check and tier-E
  review. `compute/20261127-32` attempted launch validation with the published template. I reproduced
  `STOP: run_id must be c3_t1_labels_<YYYYMMDD>` (exit 2) using the published validator and spec from
  `1afa7d62`. With the conditional render spec from `mac-g5-sd-render-20261127` @
  `bc968b3e945f2cd9c0db3056145facceaae0dc58` the same command exits 2 with
  `STOP: paper.commit must be a full 40-hex commit`. The render spec SHA-256 is
  `85c2f6208cf4e6f7b5395658f47fba1a2c212331d168585178807fdae36fc2c7`. The correction card
  `compute/20261127-08` directs P11 to the engineering smoke path from `main-t1-g5-smoke-20261124`
  and sends individual commands that refuse without a published note to the coordinator for disposition.
- `local/20261127-29` and `-30` have their draft, PRE-SPLIT and switch merges. The binding tip `93915fec`
  has tier-E **ACCEPTED** review, with 4,717 passes versus 4,694 at `f43823da` and the same 170
  failure/error IDs. All four G.1b nodes passed under `g1b-x-tasl-20261126-a`. Expansion note fills wait
  for the D6 copy (`compute/20261127-36`), author P10 declarations, per-node pins and strict checks.
  Compute identified that the copy needs an expansion variant for the assembly outside `sealed_g1b`.
  The existing [copy handoff](20261127-29-g5-expansion-relcopy.md) lists the source and three expected digests.
  Shared-card repeat work and additional audit hosts await their decisions.

## Host jobs and dependencies

- **Ada P5 `compute/20261127-29` and `-33`.** The pushed record at `28e451ea12d948c3ca542de2e6747952ed43dd3d`
  and independent review at `be396f102d57ec5d418250eee9d82bc93894766a` supersede the earlier E0 PID check.
  The smoke passed with bound kernels on card 0. E0 run `p5_20261127_b/e0e` finished and the equivalence check
  STOPped. RPS was 25.86% below the TASL-7 reference against a 10% tolerance and the recipes differ at
  R1-E0-HEADFIT. Comparison SHA-256 `7d3b9f8721e586615ba9992d0cbc3c56a20f52b11cb534aebb021e390aa5a5d4`.
  The reviewer accepted the record. The phase-1 `ada_smoke_e0` line waits for author disposition and an accepted
  equivalence check with the timing carry-forward.
- **Screening `compute/20261127-35`.** The Compute pane reports eight preserved infrastructure scenes and
  zero failed rows across those scenes. Latest `SMEAS_EVIDENCE_20261127T2125Z` stopped at 21:26:05 UTC with
  444 of 10,164 runs written and 3.01 free cores. The observed manifest SHA-256 is
  `61f3822e4109286e57982b3c60152c5a81b914fac85a4ce1b6c1e1e3b7301d18`. The remote `coord/compute` still
  carries the earlier STOP as of this check. Look for a fresh strict-preflight receipt and stamp under
  R1-SCREEN-COTENANCY-INFRA. D.3 step (8) waits for the screening result. HTCondor preflight IDs `760148`,
  `760149` and `760152` were removed unmatched. An eligible L40S or A100 match is pending.
- **Paper C.** E-INT `compute/20261127-28` awaits an eligible Ada card and the staged smoke under Paper B
  priority. The CPU measurements await the operator pins and signed notes.

Decided alone to verify the worktree bytes, ancestry, published hashes and the two launch validator refusals.
The linked worktree's Git metadata refused writes, so fetch and this status report use temporary Git metadata.
Host status comes from the pushed branches and the local Compute pane. The validations ran on a scratch export
of published code. The full suites and reviews above are existing delivery evidence.
