# local/20261128-17 — Forest Cover clean launch base

for: coordinator

- **Desk delivery.** Published base `c3a484055f717865e4e6826833e405af41771013`, queue
  `73fc54e2bc28c9cb9ef5d771702b1061e20a2753`. Branch
  `local-20261128-17-g5-launch-base-forestcover` @ `f96069d0df2633a35402dd5dc85abf1f8885a6b3`
  descends from reviewed delivery `9825ee84a9eb28e20be076a4caffbd4f9d1dbb40`.
  Run `c3_t1_labels_20261128_addendum_4` pins paper `f532176f3f0241909c9fb8df63a58e6fbefaefbd`.
- **Exact bytes and scope.** The two changed paths relative to the reviewed delivery copy the
  main-approved note verbatim and add the launch-base record. The note and spec match published
  main byte for byte. The candidate and the paper pin are identical outside `docs/` and this
  node's spec. The task changes documentation only, so the checks below cover the delivery.
- **Checks.** Strict `check-note` (K = 10), `validate --launch`, import-source and whitespace
  checks passed. The live candidate check stops at publication ancestry as expected. The same
  `verify_launch_tasl` passes with the advertised and resolved main and its PLAN read pointed at
  the local two-parent merge `45d328573601e7a57cba8f904de6e0c0b771be82`. That merge adds only
  the launch-base record relative to `c3a48405`. The unmodified guard also passes from published
  `c3a48405` itself.
- **Review.** Fresh independent tier-E review **ACCEPTED for desk delivery**. Review branch
  `local-20261128-17-g5-forestcover-launch-base-review` @ `800c8ad6748dc6db4dccc095ccb6aec1fdd15ef7`.
  [Independent review](https://github.com/dowlingwong/Agent_paper_B/blob/800c8ad6748dc6db4dccc095ccb6aec1fdd15ef7/docs/r1/reviews/G5_ADDENDUM_FORESTCOVER_LAUNCH_BASE_REVIEW_20261128.md)
- **Launch STOP.** The candidate and published tip are unsigned. The project's SSH-signing
  condition is in Local SOUL and PLAN §10 `R1-G1B-TASL-DECISIONS` LB A, invoked by the
  primary G.5 note. The runtime guard checks ancestry and tree content. The coordinator records
  the signing and publication disposition after the author's G.5 launch-base choice. Compute
  then fetches and checks the selected exact checkout, strict note, run ledger and both TASL
  hosts' leases before submission. No campaign job ID is recorded.

| Object | SHA-256 |
|---|---|
| Published Forest Cover note | `085126933b9cc013f159d76ba7010f9d11acaf9252704554eabea6f8923f0e12` |
| Forest Cover spec | `2834327aac53e5172cef3dce4aafd4f646903c0c3f4af7dc86adfbc7551b1a78` |
| Launch-base record | `060beba8643713414d16e41526e7d1e14ca3a3f3c19483a54ecded4d30d78a90` |
| Independent review | `c4f4bdfa44de0a3ad5f96df6057c3fcec34ed6b817ab9ccba41a6786024ccc72` |

This completes the desk follow-up to `local/20261128-16`, whose approval and strict check
were published at `c3a48405`. Decided alone to reproduce the coordinator merge locally and
keep the independent review on a separate branch to retain the two-path candidate diff.
The linked Git directory denied writes to `FETCH_HEAD`, so this round used the existing
writable nested Git repository inside the assigned workspace and preserved the existing
checkout changes. Local submitted zero jobs and opened zero sealed partitions.

## Round close

Local is idle. The post-delivery fetch found main and queue at the same tips cited above, Compute
at `1aa500bae3001761ecea114d71281acf64fa4d2b` and Writer at
`007bc2feabc9847506c692fe69b9c8df0322f0f9`. The delivery reports resolve the older ready markings
for the rows (g) inventory, HPO-REF implementation and revision-4 freeze. No additional Local card is
runnable. Writer is idle pending released evidence and a results-table assignment.
[Writer status](https://github.com/dowlingwong/Agent_paper_B/blob/007bc2feabc9847506c692fe69b9c8df0322f0f9/reports/20261128-writer-round-4ceb5099.md)

Compute's 18:49–18:52 UTC sample recorded no active Paper B job on TASL-2, TASL-7, Ada,
deepthought, deepthought2 or HTCondor. Held HTCondor IDs `5045947.0`, `5045949.0` and
`5045952.0` are Paper A. [Compute ledger](https://github.com/dowlingwong/Agent_paper_B/blob/1aa500bae3001761ecea114d71281acf64fa4d2b/reports/20261128-40-round-status.md)

| Lane | State and next check |
|---|---|
| Primary G.5 and addenda 1–4 | Ready for the author's launch-base decision, then coordinator signing and publication disposition. Candidate tips `2178bc6e`, `88edb84f`, `4ee43037`, `e9441f03`, `f96069d0`. Compute `20261128-18` checks exact publication and launch bindings, live leases and prior run IDs. No campaign job IDs. |
| Houseprice `local/20261126-01`, `local/20261127-27` | Closed. `tasl2-cpuset-mlgym_houseprice-20261128` passed all three signed attempts at CPUs 0–7, bit-identical to the reference and each within 9.486 s. Checkout `paperB_cpuset_20261128T001400Z`. [Exact reviewed rerun handoff](20261127-27-houseprice-two-attempts.md#compute-handoff) · [PASS receipt](https://github.com/dowlingwong/Agent_paper_B/blob/1aa500bae3001761ecea114d71281acf64fa4d2b/reports/20261128-04-houseprice-cpuset-pass.md) |
| Ada P.4 `local/20261128-13` | P5 timing PASS. P3 awaits the author's project signature over `befb58c8`'s exact spec bytes on parent `0b465954`. Then Local fills P3 and obtains final review. No phase-1 job ID. |
| D.3a and batch | P7 engineering runs `d3a-p7-exact-20261128-c` and `-d` are closed. Production needs the manifest, image or environment binding, endpoint-to-card proof, fresh run ID, P10/P11 and P9. Old batch `760158.0` left the queue. ETP L40S and TOpAS A100 last advertised `Start=false`. Compute `20261128-21` schedules the next pool check at or after 21:16:04 UTC. |
| Other dependencies | G.5 shared repeat and extra audit hosts await their recorded dispositions. Paper C CPU measurements await operator pins and author authorization, and E-INT awaits its signed spec and a fitting lease. The offline gate awaits G.5 labels, release and consumer checks, proof checks, arms freeze and explicit test release. |
