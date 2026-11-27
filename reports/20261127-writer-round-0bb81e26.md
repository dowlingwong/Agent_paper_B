# Paper B writer round close at 0bb81e26

Writer is idle. Research base `0bb81e26c6f1d47cdb6dd5da2fb7d1a61fd59043`, queue
`840bc64e8a356d880ee0bd23fcdc44c0f7986a59`. The next item is the result-table handoff
(runbook §3 item 4), which has no writer task ID yet and waits for released evidence. The
[standalone manuscript](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)
matches the research pin `c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`.

| Task ID | Published delivery branch and tip | Research merge | Recorded review |
|---|---|---|---|
| `writer/20261126-01` and `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` at `e360d425752334c56cfaba8ff9499315ca15ea8e` | `6bc4f0df` | ACCEPT WITH MINOR, corrections applied. The title and trim follow-up had no separate review. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` at `acf7d37be0cdddc29f157c311b337807f9cbea0a` | `4490a0a9` | ACCEPT WITH MINOR, corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` at `e8dc1e36a09b61e9410132f23551064f1661e769` | `03a352d9` | Independent re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` at `e3af70a495816c3d107f013b9ee2c17593600bae` | `e153df24` | Independent re-check ACCEPTED. |

At a common cap of 20 worker runs and 80 manager calls, which control decisions improve the final
configuration, and by how much? Sweep 1 found 3,274 repeats among 4,999 replayed proposals. That
observation motivates the A0R versus A0 comparison. D.3 pairs fresh campaigns and measures the final
configuration's improvement over the starting configuration on ten fresh seeds. Comparing A2 with A0R
tests what noise-aware decisions add. Comparing A3 and A5 with A2 tests what the forecasts add. The
paired effects, intervals and declared Holm decisions determine which gain claims the paper can make.
The separate offline gate tests one-step decisions on logged proposals. The campaign effects, gate
verdict and effects, full C1 audit rates, realised T1 scope and evidence bindings remain placeholders.
[Sweep 1 replay](https://github.com/dowlingwong/Agent_paper_B/blob/0bb81e26/docs/r1/reports/MAC_M3_DRYRUNS_20261104.md)

| Fresh draft | `latexmk` exit | Main text ends | Total pages | Rebuilt PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `e1bd3bf04238daa41d9cdd865f48802fff4660ce62e6da8cf2b43cabffc70f44` |
| Gate-pass preview | 0 | 8 | 43 | `92ac0727c31ac1d2dea40239be434317d21061b1f4a1f000e5469706774e7a6a` |

Every page matches the published research snapshot in extracted text and rendered pixels. Pages 1 and 8
were inspected in both drafts. References start on page 8. Each build has the same nine existing overfull
boxes, with no unresolved references or citations and no duplicate labels. The `FinalPaper` check stops
at the unset gate switch (exit 12). Task ancestry and `git diff --check` passed. This verification round
changed no manuscript source or code, so the existing review verdicts apply.

Verified public SHA-256 values:

- Claim-to-table sheet `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7`.
- Frozen D.3 revision 4 `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745`.
- Signed PRE-SPLIT v2 `970d3e45b5177f0d9f6668e9495905e1878a4ffa8eab3d73c4df6b9292a3bea7`.
- Screening's signed second re-issue `85d414763f890762628df60a25bfdd1aa2dd0e2ea81662ce31faa45cf2875db9`, the note for the former deepthought route.
- Accepted G.5 expansion binding re-check `8c398d2e614c79f38d2cd876a78cf4661704f188513f6a25288d2041c1aef836`.

## Next checks

- **Screening and D.3.** R1-SCREEN-DEEPTHOUGHT2 moves screening to CPU-only deepthought2 with at most 64
  CPUs. Local `20261127-31` prepares the reviewed host binding and third re-issue. Compute `20261127-38`
  closes the former deepthought retries after any active attempt ends. The latest observed deepthought
  stamp `SMEAS_EVIDENCE_20261127T2125Z` stopped at 444/10,164 with zero failed. Its reported manifest
  SHA-256 is `61f3822e4109286e57982b3c60152c5a81b914fac85a4ce1b6c1e1e3b7301d18`. No deepthought2 launch
  ID is recorded in the checked refs. Check for the new authorization, strict preflight and fresh stamp.
  D.3 step (8) waits for the screening result and any required SHARED decision. HTCondor IDs `760148`,
  `760149` and `760152` were removed unmatched. Check for an eligible layout, per-arm smoke and
  campaign authorizations. D.3b also needs frozen arms.
- **G.5 and the gate.** Check `compute/20261127-32` for TASL-2 P11 with the `-08` engineering route and
  `compute/20261127-33` for a fresh three-seal S14 receipt. The recorded houseprice scene
  `tasl2-cpuset-mlgym_houseprice-20261127` has two seals. All four expansion nodes passed G.1b under
  `g1b-x-tasl-20261126-a`. Check `compute/20261127-36` for the D6 copy, then per-node P10 and launch
  bindings. The gate is unread and waits for labels, train/dev release, reviewed consumers and
  preregistration bindings, frozen calibrated arms, proof checks and signed test release.
- **Ada P5 and E-INT.** Ada `p5_20261127_b/e0e` ended with the bound-kernel smoke passing and throughput
  25.86% below the old TASL-7 reference against a 10% tolerance. The review at `be396f10` accepts the
  record. The same-code reference row is held in `AUTHOR.md` for a config hash mismatch. The recorded
  config SHA-256 is `9773547dc286f638792b53b06cc7133d61209c2d9e92cdfd4982a062c1a2c054`. Phase 1 and A5
  wait for the reference disposition, accepted E0 equivalence and timing carry-forward. H200 request
  `760065` was removed unmatched. Paper C E-INT (`compute/20261127-28`) waits for an eligible Ada lease
  and smoke receipt. No E-INT run ID is recorded.
- **Writer.** On receipt of a result card, branch from published manuscript main. Use the signed releases
  and audited extracts, including the applicable C1 post-freeze release. Rebuild both drafts for independent
  review. The coordinator publishes the reviewed manuscript and updates the research pin.

Job status is from the fetched coordinator queue, Compute branch `17a20d28dc2e2b2857fbb634b42f54bbfd417ae8`
and Local branch `2bb40eb2c62fbda23b4f744362b52ebec8e6bc88`. No evidence job was submitted and no sealed
data was accessed. Decided alone to keep the 15 changed paths in the assigned worktree, each matching
the published pre-migration snapshot byte for byte. The linked Git directory rejected the fetch write.
Fetch and reporting used temporary Git metadata and the drafts were rebuilt from the pinned standalone checkout.
