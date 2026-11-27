# Round status — 27 Nov 2026, 06:06–08:55 UTC

`origin/main` moved `91cfd48a` → `ebc28ec0` (the P.4 probe record and its review were merged; the G1 final-snapshot
code is not yet merged). `origin/coord/compute` before this report: `d0d6f8af`; this report closes the round.
No evidence run, no campaign, no server and no label/evaluation read in this round.

## Finished

| Task | Result | Branch / tip | Review |
|---|---|---|---|
| `compute/20261127-02` item 2 — survey redaction | **PASS** | `compute-resource-survey-20261126` @ `58e6bbeb` (report `20261127-15`) | the coordinator's state notes it merged (`909fdc59`); no further action |
| `compute/20261127-19` — Ada P.4 probe | **0.8B PASS; 4B OOM STOP (author)** | `compute-p4-ada-probe-20261127` @ `4e51adef` (report `20261127-16`) | `compute-p4-ada-probe-review-20261127` @ `60958144`, **ACCEPTED**; merged `ebc28ec0` |
| `compute/20261127-20` — D.3 G1 final snapshots | **PASS** | `compute-d3-g1-final-20261127` @ `ff244366` (report `20261127-17`) | `compute-d3-g1-final-review-20261127` @ `d5acf3ab`, **ACCEPTED**; ready to merge |

The probe's 4B decision (H200 route or a micro-batch/checkpointing change) is with the author; nothing was run for it.
The G1 unit changes only `snapshots.py`, `campaign_chunk.py` and its test; G6/G7/analysis bytes stand.

## Running elsewhere

- **Expansion G.1b `compute/20261126-10`:** ETTh1 sealed (460/460, 00:34Z) and MetaMaze sealed (460/460, 06:36Z).
  Forest Cover is at **279/460** and Titanic at **236/460** (08:53Z), TASL-2 pids **106573** (cpus 4-7) and **106578**
  (cpus 12-15), both `S+`. They need seals, then `assemble` and `summarise`. No STOP so far; no GPU use (CPU-only).
- **TASL-2 GPU** free (353 MiB used, no compute process); **TASL-7 GPU** free (44 MiB); **Ada** cards 0/2/6/7 empty,
  1/3/4/5 shared by another user (33.7 GB each); deepthought 544 CPU slots + 1 L40S + 1 TITAN X advertised, 10/12
  HTCondor jobs running (none of ours for Paper B; the pre-existing H200 request was removed with T1).

## Blocked / waiting

- **`compute/20261127-15` houseprice CPU-set check:** MetaMaze (0-3) is sealed; **waiting for Forest Cover (4-7) to
  seal**. Titanic (12-15) does not block it (different set). Then rerun `run_cpuset_check.sh` with a new capture
  directory; no lease taken while Forest Cover runs.
- **G.5 P11 TASL-2 items (`compute/20261127-05`):** need the 0-7 leases; 4-7 is held by Forest Cover. TASL-7 items
  are already done.
- **D.3 HTCondor preflight (`compute/20261127-12`):** still no match (deepthought2 L40S `Start = false`; no TOpAS
  A100 advertised). No request edited.
- **G.5 campaigns (`compute/20261126-06`):** blocked on the published G.5 note; the render/paper.commit/P11 path is
  with the local worker and the author.
- **D.3 per-arm smoke (`compute/20261126-09`):** waits for the G1 merge (this unit) and the frozen revision 4.
- **D.3 launcher outside HTCondor (`compute/20261126-02`, queue item 4):** ready, not started; the next round should
  take it after the G1 merge unless the coordinator issues a narrower card first.

## Next round checks

1. `ssh tasl2 'ps -p 106573,106578'`; on each exit read the node log, seal the attempt, and when all four are sealed
   run `assemble` and `summarise` with the note's spec.
2. After Forest Cover seals, rerun houseprice with a new capture directory; then the P11 TASL-2 items.
3. Watch `condor_status` for a runnable L40S/A100; do not edit the request.
4. After `compute/20261127-20` is merged, the local worker repeats revision 4 step (5) (`local/20261127-16`).
5. The author's 4B choice gates any Ada P.4 training/phase-1 note change.

**Task ids this report covers:** compute/20261127-02 (item 2), -19, -20. **Reports:** `20261127-15`, `-16`, `-17`,
`-18` on `coord/compute`. **Coordinator action:** merge `compute-d3-g1-final-20261127` @ `ff244366` and
`compute-d3-g1-final-review-20261127` @ `d5acf3ab` after its checks.
