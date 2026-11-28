# Local round close — 28 November 2026

Published main `2a58f7ac5147dad1259914593901ccb226a147f9`, coordinator
`bbc5b59a2a6d9ad2e6a9668fcae1013c158de281`, Compute `b4d2a588b2ca919337ffad92db4775b3944cfa33`,
Writer `c016d33f8543796b59c5745b315d9c5c917f13a5`. Local fetched the queue after each handoff.
The current batch has no further runnable Local card.

- `local/20261128-15`, Titanic and MetaMaze clean launch bases `88edb84f` and `4ee43037`.
  Fresh review ACCEPTED for desk delivery. Strict checks pass at K = 10 and the actual launch
  verifier passes with separate coordinator merges simulated. The unsigned candidates await the
  author and coordinator's launch-base disposition and publication. [Exact pins and checks](20261128-15-g5-clean-launch-bases.md)
- `local/20261128-14`, ETTh1 draft `5e924f81`, independent review `f352248a` ACCEPTED.
  Focused synthetic tests 36 PASS. The actual binder passed with the review blob supplied. The
  official draft check stops at the unpublished review. [Review handoff and STOP](20261128-14-g5-etth1-draft-stop.md)
- Houseprice CPU-set work was already complete. The published record at `065f25c5` and `d173ceb3`
  shows PASS for three bit-identical attempts on CPUs 0–7 within 9.486 s. Run
  `paperB_cpuset_20261128T001400Z` / `tasl2-cpuset-mlgym_houseprice-20261128` is closed.
  [Reviewed rerun handoff](20261127-27-houseprice-two-attempts.md#compute-handoff)

| Lane | State and next check |
|---|---|
| Local | Idle pending publication of the ETTh1 review, the approved 1GC notes and the Forest Cover host receipt. G.5 shared-repeat monitor implementation waits on `R1-G5-SHARED-REPEAT`. The additional audit-host path remains parked. |
| Primary G.5, author → coordinator → Compute | `compute/20261128-18`, `c3_t1_labels_20261128`, STOP before submission. Clean candidate `2178bc6e` awaits the G.5 launch-base decision. No campaign job ID. |
| MLGym G.5, author → coordinator → Compute | `c3_t1_labels_20261128_addendum_1` and `_2` await signing and clean-base publication, actual ancestry/strict checks and a live job/lease recheck. No campaign job IDs. |
| 1GC G.5, Compute and coordinator | ETTh1 `c3_t1_labels_20261128_addendum_3` awaits review publication, official draft check and approval. The ETTh1 licence line remains due before a label table cites it. Forest Cover awaits exact C1–7 receipt for `compute/20261128-20` at `3f7b09fe`, CPU 4–7. No job ID recorded for the Forest Cover check. |
| P.4 Ada, author → Local | `trackp-p4-p1-20261122-a` P5 timing PASS. P3 needs the project signature over the reviewed one-file spec `befb58c8` on parent `0b465954`. Local then fills P3 and finishes review. No training job ID. |
| D.3, Compute and coordinator | P7 runs `d3a-p7-exact-20261128-c` and `-d` closed. D.3a production awaits manifest/image disposition, endpoint-to-card proof, fresh run ID, review and P9. Previous batch `760158.0` is gone. Last ETP L40S and TOpAS A100 checks had `Start=false`. Recheck exact request matching and any replacement ID. |
| Paper C and Writer | CPU work awaits runtime, cache and authorization bindings. E-INT awaits signed census spec and Ada lease. Writer awaits released evidence. The gate remains sealed pending G.5, train/dev release, proof and consumer checks, arms freeze and explicit test release. |

Compute's 15:00Z report shows no Paper B job queued or running. It checked TASL-2 and HTCondor directly.
TASL-7 and Ada were last sampled in the preceding round. The held Condor IDs `5045947.0`,
`5045949.0` and `5045952.0` belong to Paper A. [Compute ledger](https://github.com/dowlingwong/Agent_paper_B/blob/b4d2a588/reports/20261128-36-round-status.md)

Decided alone to use the writable nested Git checkout because the assigned linked checkout cannot write
its shared metadata. The pre-existing project edits stayed in the assigned checkout. Local submitted
zero jobs and accessed no sealed partitions.
