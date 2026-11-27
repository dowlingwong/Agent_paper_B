# Local round close — 27 November 2026

Local is idle. The final fetch found published main at `ebc28ec073e75adea472af96316d93cea78736fe`,
`coord/coordinator` at `cf599e6851eb76ce724292cc3569c8176b46d375`, `coord/compute` at
`b4b335272c68042396346f198ec095ed1049fbaf`, and the preceding `coord/local` at
`80fa82037532ceb5dea8f241843d6ec3871e21b6`. The assigned checkout is clean at
`cb684870f939eec3a32b499a11a6bcce44d4dd57`, an ancestor of main. This update supersedes the Compute
status in [the previous local round report](20261127-local-round-0925.md).

## Local tasks

- **`local/20261126-01`, complete.** Base `54082a05`, delivery `mac-cpuset-repeats-20261126` @
  `5f1aead043fd2dba7a82403b61bfa798b113b528`, merged `47df6f55`. Independent re-check **ACCEPTED**.
  The full suite had 3,918 passes at base and 3,924 at tested tip `0c1a9b7f`, with the same 179 failures and
  26 errors. Failing-ID list SHA-256 `1c21757ae349800dca867b1a08e5a5e7c3301de4021e75b7448421b2afac70f2`.
  The exact rerun command is in [the accepted `for: compute` handoff](20261126-01-cpuset-fix.md).
  The signed S14 criterion is three sealed attempts on CPUs 0–7, each bit-identical to the sealed G.1b
  reference and within 9.486 s per run. Compute owns the rerun under `compute/20261127-15`.
- **`local/20261127-16` / `local/20261127-08`, pending.** Step-(5) STOP branch
  `mac-d3-r4-step5-20261127` @ `9aeebd6ae8c5e0a7ce9f82fa65dc8ce5606116f8` remains the current Local
  record. The full tier-E verdict was **NOT ACCEPTED** and the binding-only diff was **ACCEPTED**.
  Compute's repair `compute-d3-g1-final-20261127` @ `ff244366b7168a210a302b37deda5438f83c9e6e`
  has an independent **ACCEPTED** re-check at `d5acf3ab2cdff98cdd6c0e2760f427ebf88df891`.
  Review SHA-256 `90ef2d1fde5ba1390a8edabd3d1d5e8aa868cb25502580b58de8558eb09633d7`.
  Compute reported 161 focused passes plus 18 subtests and identical sets of 120 failing/error IDs
  across its full suite. The reviewer saw 117 failing/error IDs, all present at base. The fix is absent
  from published main. After the coordinator merges it, repeat the pinned checks, full tier-E step (5)
  and the diff-only re-check on the resulting main commit. Keep rev 4 unfrozen pending these checks
  and the separate screening disposition.
- **`local/20261127-12`, delivered.** The note at `b2360a7a` is independently **ACCEPTED** for
  signature, with a passing draft check and 82 focused tests at its exact code pin. Note SHA-256
  `c622ccb5c7781b18639edfbb23ad299820b04e996d95487e73ef8d3da2bd8831`. It awaits the author signature and
  coordinator publication, then Compute's strict preflight and measurement.
- **G.5 final render and addenda, pending.** The accepted conditional render `bc968b3e` awaits combined
  P11 on the TASL pair, final `paper.commit`, the draft check and final tier-E review. The coordinator
  publishes and runs the strict check. The S9 split v2 is on main, SHA-256
  `4dd46796e50ec188b5f89ebc8f4c04e6ab60a5056f124538936dd1bb5d6ae53a`. The switch awaits the shared
  launch-code binding. Real addenda also need published per-node G.1b determinism PASS and the
  published split amendment. The 1GC results have a separate reporting path. Shared-card repeat and
  extra audit-host work remain parked on their recorded decisions.
- The HPO reference is merged at `c025ee24`. Paper C consolidation awaits author confirmation of
  its historical PLAN rows.

## Recorded Compute activity

- **Expansion G.1b, `compute/20261126-10`.** Run `g1b-x-tasl-20261126-a` on TASL-2. ETTh1 and
  MetaMaze are sealed (460/460 each, 00:34 and 06:36 UTC). At the 08:53 UTC sample Forest Cover was
  279/460, PID `106573` on CPUs 4–7, and Titanic was 236/460, PID `106578` on CPUs 12–15. Next
  check their seals, then assembly and per-node determinism. Forest Cover holds the remaining lease
  needed by the houseprice rerun and the pending TASL-2 P11 items (`compute/20261127-05` and `-08`).
  The previous houseprice helper wait created no run root. Titanic uses a separate CPU set.
- **P.4 Ada probe, `compute/20261127-19` / `-21`.** Both 0.8B arms passed. Both 4B arms hit the
  arm STOP at micro-batch 8 on empty 48 GB cards. The probe ended and charged 2.1603 GPU-h. The
  accepted record is published at `ebc28ec0`. H200 job `760065` was removed with zero wall time.
  The 4B route awaits the author.
- **D.3 HTCondor preflight, `compute/20261127-12`.** Removed jobs `760148`, `760149` and `760152`
  produced no match. Compute watches for a runnable ETP L40S or TOpAS A100 and checks the pinned
  inputs inside the matched job. The per-arm smoke waits on the runner and rev 4 prerequisites.

Decided alone: used the latest Compute receipt for job state, verified the reported branches and the
applicable hashes in Git, and kept the queue pending at the published prerequisites. Temporary writable
Git metadata provided the fetch and this report. No code changed, no new suite or evidence job ran, and
no sealed data was read.
