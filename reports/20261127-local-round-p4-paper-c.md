# Local round close — 27 November 2026

Published main `cd9af2af8dc2d327b77ea41f1052c9e8c39d2021`. Coordinator `799b4f31b6ac2ec7202781b4206f5accff296770`. Latest recorded Compute state
`461fdec79c3a4fcc1816207e7a73936dada94fa1`. The assigned checkout is restored to its original clean
`cb684870f939eec3a32b499a11a6bcce44d4dd57`. Writable Git metadata in temporary storage
handled fetches and branch/report commits because the linked metadata is read-only.

## Local desk

- `local/20261127-18` — accepted and pushed at `585ed0d0`. Full-suite failure IDs are identical to base. The exact empty-card Ada re-probe is ready for the coordinator merge and Compute.
  [Task report](20261127-18-p4-4b-checkpointing.md).
- `local/20261127-19` — independent pre-signature handoffs for
  [Sweep 1 incumbent audits](20261127-19a-paperc-sweep1-audits.md) and
  [guarded first acceptance](20261127-19b-paperc-guarded-first-accept.md).
  Operator pins and author launch decisions remain pending. The guarded unit needs the
  proposer, exact run/call budgets and published worker seed extension.
- `local/20261127-20` — [E-INT desk preparation](20261127-20-paperc-eint-census-prep.md)
  reviewed. Start with a signed smoke card on an empty GPU after Paper B's critical work.
- `local/20261126-01` — houseprice procedure accepted and merged `47df6f55`. The original
  [exact Compute handoff](20261126-01-cpuset-fix.md) remains current. S14 still requires
  three sealed attempts on CPUs 0–7, bit-identical to the G.1b reference and within
  9.486 s each.
- `local/20261127-08/-16/-17` — D.3 revision 4 stays unfrozen. The production integration
  `compute/20261127-23` @ `1bd7f3d6d724a9d2653fd06807e639a5ef4f4129` awaits accepted
  review and publication. The separately reviewed G1 launchers are on main at `cd9af2af`. Repeat step (5) on the integration merge. The screening
  disposition still precedes freeze and smoke.
- `local/20261126-08` and `local/20261127-09` — G.5 render waits on reviewed combined P11,
  exact `paper.commit`, draft check and final tier-E review. `local/20261126-12` and
  `local/20261127-03` unit 2 wait on the shared launch-code binding, published per-node G.1b
  determinism and split amendment. The shared-card repeat/monitor and added audit-host
  units wait on their recorded decisions.

## Latest Compute receipts and next checks

- **Running elsewhere** — `compute/20261126-10`, `g1b-x-tasl-20261126-a`. Latest receipt at
  11:40 UTC recorded TASL-2 PID `106573` for Forest Cover on CPUs 4–7, in the joint part
  with 79 run files. Titanic was at 109/150 split runs on CPUs 12–15, PID `106578`.
  ETTh1 and MetaMaze were sealed. Compute checks both exits and seals, then assembles
  and publishes the per-node determinism results.
- **Waiting for a lease** — houseprice rerun `compute/20261127-15`. The waiter was
  stopped after 28 minutes with no run root. Retry after Forest Cover frees CPUs 4–7.
  Combined P11 `compute/20261127-05` with `-08` also waits on TASL-2 access and the
  coordinator's valid pre-run spec/note sequencing. TASL-7's host check is accepted.
- **Stopped** — screening evidence `compute/20261127-22`, scene
  `SMEAS_EVIDENCE_20261127T1032Z`, 0/10,164 worker runs. Record on main `6cf3ca70`.
  The author has the `python` versus `python3` decision. Under the recommended option,
  the coordinator routes the one-line authorization amendment for a screening re-check
  and signature. Then Compute starts a new attempt.
- **Idle/no match** — D.3 HTCondor preflight `compute/20261127-12`. Prior jobs
  `760148`, `760149`, `760152` were removed. The L40S/TOpAS A100 routes have no
  reported match. The known idle `759624/759625` belong to other jobs. Check the
  exact scheduler request and approved direct fallback after the necessary review.
- **Pending dispatch** — P.4 synthetic 4B re-probe `trackp-p4-probe-20261127-b`.
  Check the published merge, Compute priority, empty Ada lease and submission ledger
  before staging. The old H200 job `760065` was removed with zero wall time.
  Its T1 charge is included once.

The local round is idle after the post-task queue fetch. Compute states above come
from committed receipts. Local submitted no jobs and opened no sealed partitions.
