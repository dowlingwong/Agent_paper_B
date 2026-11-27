# Local round close — screening re-issue and D.3 step (5)

Local is idle after the post-task fetch. Published main
`e92f3c7389e06347a0ff78f5f68971024133c670`, coordinator queue
`11812b560c5766238d83c64d2dfd6286b1665e24`, Compute receipt
`51dcef4a4cbf8a4f25393bffc7fdeefbfeac0635`. The assigned worktree is clean at
`cb684870f939eec3a32b499a11a6bcce44d4dd57`.

## Local deliveries and pending work

- `local/20261127-21` **ACCEPTED**. Re-issued note and independent review at
  `mac-screen-note-reissue-20261127` @ `2c471ef83a61a04e2264ba61badfabae67b070be`.
  82 focused tests passed, as did the preflight with local fixtures. Coordinator publication
  comes first. Compute then verifies the note and launches a fresh attempt with `python3`.
  See [task report](20261127-21-screen-note-reissue.md).
- `local/20261127-22` **ACCEPTED** for full step (5) and the binding-only diff.
  Review and seven synthetic replays at `mac-d3-r4-step5-third-20261127` @
  `0c691ce8fea74f0d86361d40c0c11315f0103aee`. Local focused checks passed
  181 tests and 18 subtests. The freeze waits for screening disposition and the final
  signature metadata re-check. Reviewed sources for actual retries and proposer GPU time
  remain an evidence-authorization dependency. See [task report](20261127-22-d3-r4-step5-third.md).
- `local/20261126-01` is complete and merged at `47df6f55`. The exact rerun is in the
  [accepted `for: compute` handoff](20261126-01-cpuset-fix.md). S14 requires three sealed
  TASL-2 attempts on CPUs 0–7, bit-identical to the G.1b reference and at most 9.486 seconds each.
- G.5 final render (`local/20261126-08`, `local/20261127-09`) awaits combined P11 and
  the final `paper.commit`, followed by the draft check and final tier-E review. The
  S9 draft template and split v2 already exist. The addendum switch
  (`local/20261126-12`, `local/20261127-03` unit 2) awaits the recorded shared launch-code
  binding with the base G.5 note. Real addenda also require the published split amendment
  and per-node G.1b determinism PASS. Shared-card repeat and additional audit-host work
  await their recorded decisions.
- Paper C measurement drafts and the E-INT desk prep are merged. CPU launches await
  their author decisions and operator pins. E-INT needs a signed development smoke and
  an empty GPU after Paper B's critical work.

## Latest recorded Compute state and next check

| Work | Recorded state and next check |
|---|---|
| Expansion G.1b `compute/20261126-10` | Latest receipt at 11:40 UTC has TASL-2 Forest Cover PID `106573` in joint on CPUs 4–7 and Titanic PID `106578` in split on CPUs 12–15. ETTh1 and MetaMaze are sealed. Compute checks exits and seals, then assembles the four per-node determinism verdicts. |
| Houseprice `compute/20261127-15` and P11 `compute/20261127-05/-08` | The previous houseprice waiter exited without creating a run root. Check `106573` and the 0–3/4–7 leases before rerunning. P11 also needs valid pre-run spec/note sequencing and the remaining TASL-2 checks. |
| Screening `compute/20261127-22` | Prior scene `SMEAS_EVIDENCE_20261127T1032Z` stopped with 0/10,164 runs. Check publication of the re-issued note and the submission ledger, then start a fresh scene under strict preflight. |
| P.4 `compute/20261127-24` | Dispatched for `trackp-p4-probe-20261127-b` on an empty RTX 6000 Ada. Check for an existing receipt, active job and lease first. The prior H200 job `760065` was removed with zero wall time. |
| D.3 HTCondor preflight `compute/20261127-12` | Idle, no eligible L40S or TOpAS A100 match in the recorded check. Jobs `760148`, `760149`, `760152` were removed. Idle `759624/759625` are unrelated. Check the exact request and the approved direct route if needed. Per-arm smoke still waits for freeze and placement checks. |

Compute status is from committed receipts. Local submitted no jobs and opened no sealed
partitions. Temporary writable Git metadata handled fetches and branch/report commits.
