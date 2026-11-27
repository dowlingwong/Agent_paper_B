# Local round close — 27 November 2026

Local is idle after the post-task fetch. Published main
`2d88fe1b7bcaa1cb0b157ec48cf3be13255bf536`, coordinator queue
`eff87276da4edbedba0560dc6d474b36541f1c46`, Compute receipt
`b4b335272c68042396346f198ec095ed1049fbaf`, and preceding Local report
`db7ba652c66302ca4def72350c63d4937e0b3a07`. The assigned checkout was clean at
`cb684870f939eec3a32b499a11a6bcce44d4dd57`, an ancestor of main.

## Local queue

| Card | State and next check |
|---|---|
| `local/20261127-17`, `-16`, `-08` | Step (5) repeated. Full tier E **NOT ACCEPTED**, binding-only diff **ACCEPTED**, both terminal repairs **PASS**. [Task STOP](20261127-17-d3-r4-step5-repeat-stop.md), review branch `mac-d3-r4-step5-repeat-20261127` @ `9841e2c0bf3f04460915016327c90c859376ac95`. Coordinator routing is needed for the production G1 summary and G6 keep-audit integration with G7. Repeat step (5) after its reviewed merge. Freeze also waits for screening disposition. |
| `local/20261126-01` | CPU-set procedure accepted and merged at `47df6f55`. The [exact reviewed rerun command](20261126-01-cpuset-fix.md) is already addressed to Compute. S14 still requires three sealed attempts on CPUs 0–7, bit-identical to the reference and within 9.486 s per run. |
| `local/20261127-12` | Screening note ready on Local's side. The coordinator checked the signature candidate at `649c5f02`. Its author list records confirmation and publication pending. Compute's strict check and evidence measurement follow publication. |
| `local/20261126-08` and `local/20261127-09` | G.5 final render waits for reviewed combined P11, exact `paper.commit`, a passing draft check and final tier-E review. The coordinator handles publication and the strict check. |
| `local/20261126-12` and `local/20261127-03` unit 2 | S9 is signed, split v2 is merged, and the reviewed template is published. The switch waits for the recorded shared launch-code binding with the base note. Real addenda also need published per-node G.1b determinism PASS and the published split amendment. |
| Other pending cards | G.5 shared-card repeat and audit-host work await their recorded determinations. The Paper C consolidation awaits confirmation of historical PLAN rows. All earlier independent Local units have a delivery or a parked decision. |

## Compute activity from the latest receipt

- **Expansion G.1b** `compute/20261126-10`, run `g1b-x-tasl-20261126-a`. ETTh1 and MetaMaze
  sealed at 460/460. At 08:53 UTC, Forest Cover was 279/460 on TASL-2 CPUs 4–7, PID `106573`,
  and Titanic was 236/460 on CPUs 12–15, PID `106578`. Check exit, seals, then assembly and
  per-node determinism. Forest Cover's lease blocks the houseprice rerun `compute/20261127-15`
  and pending TASL-2 P11 checks `compute/20261127-05` with `-08`. Titanic's lease is separate.
- **Ada P.4** `compute/20261127-19` / `-21` ended. Both 0.8B probes passed and both 4B probes
  stopped on OOM. H200 job `760065` was removed with zero wall time. The signed 4B checkpointing
  candidate is in `649c5f02` and awaits coordinator publication, then implementation review
  and the synthetic 4B re-probe.
- **D.3 HTCondor** `compute/20261127-12` has no recorded match. Jobs `760148`, `760149` and
  `760152` were removed. Compute checks for an eligible ETP L40S or TOpAS A100. The direct-launcher
  work is in Compute's queue. D.3 per-arm smoke `compute/20261126-09` awaits the runner chain
  and frozen revision 4.

I used a separate writable Git directory for remote fetches and commits because the assigned
checkout's linked Git metadata is read-only. Server state comes from the latest Compute receipt.
No job was submitted and no sealed data was opened.
