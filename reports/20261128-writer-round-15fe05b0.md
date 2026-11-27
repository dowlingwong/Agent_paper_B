# Paper B writer round at 15fe05b0

Writer is idle. Research base `15fe05b0d0a08ae5c37eb582eb0c3f04d67e0b2a`; coordinator queue
`20837ee4cd4a293bd3d760ca0d4d534d29372c1e`. All five cards under `tasks/writer` have published
deliveries. The result-table handoff (runbook §3 item 4) has no task ID yet and waits for released
evidence. The [standalone manuscript](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)
is at the published research pin `c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`.

| Task ID | Delivered research branch and exact tip | Research merge | Recorded review |
|---|---|---|---|
| `writer/20261126-01` with `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` at `e360d425752334c56cfaba8ff9499315ca15ea8e` | `6bc4f0df` | ACCEPT WITH MINOR, corrections applied. The title and trim follow-up had no separate review. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` at `acf7d37be0cdddc29f157c311b337807f9cbea0a` | `4490a0a9` | ACCEPT WITH MINOR, corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` at `e8dc1e36a09b61e9410132f23551064f1661e769` | `03a352d9` | Independent re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` at `e3af70a495816c3d107f013b9ee2c17593600bae` | `e153df24` | Independent re-check ACCEPTED. |

Which control decisions improve the final configuration at the same budget, and by how much?
In Sweep 1, 3,274 of 4,999 replayed proposals repeated a configuration. That measured frequency
motivates testing a rule that skips repeats and detectable no-ops (A0R versus A0). In D.3 each
arm gets up to 20 worker runs and 80 manager calls on the same instances. An independent audit
measures how much the final configuration improves on the starting one over ten fresh seeds.
A2 versus A0R measures what the noise-aware decision rule adds to the skip rule. A3 and A5 versus
A2 measure what the learned forecasts add. The paired effects, intervals and the declared Holm
decisions will support the campaign claims. The offline gate tests one-step decision utility on
logged proposals. Campaign effects and intervals, the gate verdict and effects, full C1 audit rates,
the realised T1 scope and evidence bindings remain placeholders.
[Sweep 1 replay](https://github.com/dowlingwong/Agent_paper_B/blob/15fe05b0/docs/r1/reports/MAC_M3_DRYRUNS_20261104.md)

## Draft verification at the standalone pin

| Draft | latexmk exit | Last main-text page | Total pages | Rebuilt PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `1982de3b7323915740bbc7b21e57176d57c18c4df5c2975a2ad438f3b1c113ae` |
| Gate-pass preview | 0 | 8 | 43 | `df25a1f4262f096b7683155773a2cd93701717c985c16526c26700ac2abe994c` |

Extracted text and 100 dpi page renders match the archived research PDFs. Pages 1 and 8 in both
builds were inspected. References begin on page 8. Both logs contain nine existing overfull boxes
and zero unresolved citations, references or duplicate labels. The `FinalPaper` guard exits 12
at the unset gate switch. Task ancestry and `git diff --check` passed. The round changed no
manuscript source or code. The review verdicts above apply.

Verified SHA-256 values from published main:

| Record | SHA-256 |
|---|---|
| Claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Frozen D.3 revision 4 | `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745` |
| Signed PRE-SPLIT v2 | `970d3e45b5177f0d9f6668e9495905e1878a4ffa8eab3d73c4df6b9292a3bea7` |
| Screening second re-issue for the former deepthought route | `85d414763f890762628df60a25bfdd1aa2dd0e2ea81662ce31faa45cf2875db9` |
| Accepted G.5 expansion binding re-check | `8c398d2e614c79f38d2cd876a78cf4661704f188513f6a25288d2041c1aef836` |
| Same-code TASL-7 E0 reference configuration pinned by PLAN | `9773547dc286f638792b53b06cc7133d61209c2d9e92cdfd4982a062c1a2c054` |
| Ada P5 `comparison_e0e.json` against the October reference | `7d3b9f8721e586615ba9992d0cbc3c56a20f52b11cb534aebb021e390aa5a5d4` |

## Dependencies and job IDs for the next round

- **Screening and D.3.** Local `20261127-31` owns the deepthought2 runner binding and note re-issue.
  Compute `20261127-38` owns closure of the deepthought retries. The last recorded former-host
  stamp `SMEAS_EVIDENCE_20261127T2125Z` stopped at 444/10,164 with zero failed. Look for the reviewed
  deepthought2 authorization, preflight receipt and fresh stamp. The fetched records give no launch ID
  on deepthought2. D.3 step (8) and campaigns wait for the screening result and any required SHARED
  decision. Preflight IDs `760148`, `760149` and `760152` were removed unmatched. Check
  `compute/20261128-03` for a new HTCondor ID and in-job bindings, then the separate per-arm smoke
  and campaign authorizations. `compute/20261128-04` covers old probes `759624` and `759625`
  and withdrawn H200 request `760065`. Check the cleanup receipt. D.3b also needs frozen arms.
- **Ada P5 and Paper C.** The released `p5_20261127_b/e0e` record has a passing bound-kernel smoke
  and runs per second 25.86% below the October reference against a 10% tolerance. The
  same-code comparison is now authorised. Check `compute/20261128-01` for the TASL-7 run ID,
  equivalence and timing disposition. The phase-1 note and A5 SFT wait for accepted E0 equivalence
  and timing carry-forward. E-INT `compute/20261127-28` waits for an eligible Ada lease and smoke
  receipt. The fetched records give no E-INT run ID.
- **G.5 and the gate.** Check `compute/20261127-32` under `compute/20261128-05` for the engineering
  P11 host checks. Check `compute/20261127-33` for a fresh S14 receipt with three seals
  (`tasl2-cpuset-mlgym_houseprice-20261127` has two). Expansion G.1b is complete under
  `g1b-x-tasl-20261126-a`. The D6 copy (`compute/20261127-36`) waits for the reviewed expansion
  command from `local/20261128-01`. The G.5 launch still needs final bind, render, review and
  publication. The gate remains unread pending labels, train/dev release, reviewed consumers and
  preregistration bindings, frozen calibrated arms, proof checks and an explicit test release.
- **Compute reporting.** The fetched public tip is `17a20d28dc2e2b2857fbb634b42f54bbfd417ae8`.
  The coordinator reports a stalled Compute session and routes the unpublished reports through
  `compute/20261128-02`. Local report branch `coord-compute` at `ebb7354b` was checked for job
  metadata alongside public Local tip `2bb40eb2c62fbda23b4f744362b52ebec8e6bc88`. The status
  above comes from repository receipts and the queue. Live scheduler status remains unverified.
- **Writer.** On the first ready result card, branch from published manuscript main, use the
  signed release and audited extracts, and rebuild both variants for independent review. The
  coordinator publishes the reviewed manuscript and updates the research pin.

Decided alone to preserve the 15 modified paths in the assigned worktree after verifying that each
matches the published pre-migration snapshot byte for byte. The linked Git directory refused the
fetch write, so fetch and reporting used temporary Git metadata. No evidence job was submitted
and no sealed data was opened.
