# local/20261127-30 unit 2 — G.5 expansion launch and release binding

for: coordinator

Base `f43823dad358a25608fe27013221eba9aaa7d385`.
Branch `mac-g5-expansion-binding-20261127` @ `93915feca1baafa444eeb49585de093085a0a66d`.
Reviewed implementation `0f365fac2209811ab846659d106f0655a9e0c172`. Independent tier-E re-check
**ACCEPTED**. Review `docs/r1/reviews/G5_EXPANSION_BINDING_REVIEW_20261127.md`,
SHA-256 `8c398d2e614c79f38d2cd876a78cf4661704f188513f6a25288d2041c1aef836`.

Each addendum can bind a separate published code commit, approved note, spec digest and run ID.
The worker inherits the main note's K, campaign settings and guard rules, uses the published
node's census environment, CPU set and run budget, and takes the main worker slot and S13
leases. MetaMaze, ETTh1 and Forest Cover use the scoped CPU-only engine admission from their
G.1b kits. Attempts, plans, proposer spans and seals bind the exact addendum. Under the signed
v2 release rows, MLGym joins the main table and gate-noise record. The two 1GC nodes have
separate descriptive outputs. The standard eight-node launch keeps its own pin.

## Verification and hashes

- Independent targeted addendum, seal and assembly tests: **67 passed**, with
  `COPYFILE_DISABLE=1` and fresh `TMPDIR`. The synthetic fixtures cover portable published
  note and spec binding, a changed launch tree, missing/stopped G.1b receipts, incompatible
  CPUs, wrong split, archive mutation and the separate 1GC route. The four published G.1b seals
  also pass the raw and canonical digest checks.
- The four scratch kit merge trees carry the same G.5 engine files as `cbf7a003`: Titanic
  `dff4c0ced1e81753d1f7341352c15f8a92bdf7a0`, MetaMaze
  `f421de0396bd16acdbe1a0b61e1897de34d890f6`, ETTh1
  `e53b68c46000d8b7ff183d29a799fb8f6264d150`, Forest Cover
  `0f1b4452e3d4df750438c0272084de608ba38bdf`. These are tree checks. Deployment pins still
  require the per-node review and host check.
- The serial full `r1/tests` comparison used Python 3.11.5, pytest 7.4.0,
  harness `9bb416805175149eb87b71f28d77530572aa4bce`, no LightGBM, and a fresh
  `TMPDIR` for each run. Command `python -m pytest -q -p no:cacheprovider -rfE
  --continue-on-collection-errors r1/tests`. Base had **4,694 passed**, candidate tip
  **4,717 passed**. Each had 143 failures, 27 errors and 168 skips. All 170
  FAILED/ERROR IDs match, with **zero new failures or errors**. This desk comparator
  used the available conda Python without torch. Several legacy tests depend on
  Linux or macOS tar settings. The independent focused run used the no-xattr tar
  setting. [Exact shared failure and error IDs](20261127-30b-full-suite-ids.txt),
  SHA-256 `3771032d2b7bcd14852da852ebcff69eff8e1af38aa25474eaf9ff61347ae1fb`.
- Addendum checker SHA-256 `ba51ae12cfa3c7815852c05a27200324ef5672c214c977b6d5d77c2eea4688f9`.
  Switch SHA-256 `800575983aa4cd0141244b719a2a71243cd8318eb8db67835475b97ac395ac51`.
  Job SHA-256 `a9b9d10f8379ba705728ec7b0c58a89cce5c2b51cac365860e508dc839a22962`.
  Seal SHA-256 `73ed8e53c1b3a45b615009b00cf454e417b6681755e71048f57edb76b29a979a`.
  Assembly SHA-256 `56e7d09dbeb868df7c41f8e90387eccc0a5ffe4a5662658a8bf5b20a8c9a423c`.
  Noise SHA-256 `dd0148210919c647ddd5b5aee5c4a7eaa8cc42a8f6768545a663d9c2740624e5`.
  Deployment template SHA-256 `c1a76d5dc84de3440df4406b25bba0959135bb3b1ae9a5ebabf02a4c1b066b9c`.
  Split v2 SHA-256 `4dd46796e50ec188b5f89ebc8f4c04e6ab60a5056f124538936dd1bb5d6ae53a`.

## Next

- Coordinator publishes the accepted PRE-SPLIT amendment from the separate unit 1 report and
  routes this reviewed code. The eight-node G.5 note proceeds when its own P11, houseprice,
  `paper.commit`, strict checks and final review are ready.
- `compute/20261127-36` supplies and reviews the expansion D6 copy. It has the expected
  SHA-256 values and no new G.1b job is needed. Once this copy is published, derive the
  four-node excess-kurtosis table for the author's P10 declarations, then fill the separate
  per-node spec pins and notes using the reviewed template. Each filled addendum needs its
  own accepted review and strict check before launch. The signed v2 train/dev and test rows
  still govern the later assembly.

Decided alone to derive CPU deployment from the exact published G.1b spec and reuse the main
job, seal and assembly paths with per-addendum bindings. No host job was submitted, no sealed
partition was opened, and no author or publication fields were set. The assigned worktree was
used for edits with writable Git metadata in a scratch directory.

## Queue and jobs

Final queue fetch saw `coord/coordinator` `d2924d54171a0757fc5f656ed9557c732a0aa04f`
and `coord/compute` `17a20d28dc2e2b2857fbb634b42f54bbfd417ae8`. The coordinator
updated state for the unit 1 publication. The Local task list has no new card.

The coordinator published unit 1 on `main` `a5a149016dd3b913976146f14677524e4d534919`.
The real `split_v2_amendment` check passed in a clean published checkout and returned
SHA-256 `970d3e45b5177f0d9f6668e9495905e1878a4ffa8eab3d73c4df6b9292a3bea7`.
The frozen preregistration and both splits still have the original bytes.

- **Local idle after this handoff.** G.5's base render `local/20261126-08` awaits the combined
  accepted P11 record, the houseprice S14 PASS and the final paper pin, strict checks and
  independent review. Expansion note fills await the D6 copy, the author P10 row and reviewed
  harness and host checks. The G.5 shared-card repeat list and extra audit-host units await
  their author decisions.
- **Screening** `compute/20261127-35` awaits a fresh job receipt after strict preflight.
  Preserve stopped `SMEAS_EVIDENCE_20261127T1550Z` (186/10,164, tmux `smeas_reissue2`).
  D.3 step (8) remains held for screening. Earlier pool IDs `760148`, `760149` and `760152`
  were removed unmatched. A new eligible L40S or A100 preflight is pending.
- **Houseprice and Ada P5** `compute/20261127-33`. The houseprice fix is merged and its exact
  [rerun command](20261127-27-houseprice-two-attempts.md#compute-handoff) is already routed
  `for: compute`. The prior `tasl2-cpuset-mlgym_houseprice-20261127` retains two seals.
  Check for a fresh three-attempt S14 result on CPUs 0–7 within 9.486 s. Ada P5 E0 was last
  observed in Compute's pane as PID `1621896`, run `p5_20261127_b`. Check Compute's final
  accepted receipt and the timing record before the P.4 phase-1 publication. Remaining
  G.5 P11 host items are `compute/20261127-32`.
- **Expansion G.1b complete.** `g1b-x-tasl-20261126-a` sealed all four nodes with determinism PASS.
  Last Titanic PID `106578` finished. The D6 copy is `compute/20261127-36`.
- **Paper C.** E-INT `compute/20261127-28` awaits the staged Ada smoke and an eligible leased card.
  CPU measurements await their operator pins and signed notes.
