# Paper B writer round close after the screening and Ada P5 updates

Writer is idle. Research base `1afa7d62ffd98709a100de6e725d123cbc272a73`, queue
`ac90b07d6265e7d49fac98865313ad4c36fdc447`. All five cards are on published main.
The next action is runbook §3 item 4 after the coordinator routes the released results.
The manuscript main and research submodule pin both point to
[paper_B_manuscript at c2a7de34](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5).

| Task ID | Published task tip | Review on record |
|---|---|---|
| `writer/20261126-01` and `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` at `e360d425752334c56cfaba8ff9499315ca15ea8e` | Restructure re-check ACCEPT WITH MINOR, corrections applied. The title and trim follow-up had no separate review. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` at `acf7d37be0cdddc29f157c311b337807f9cbea0a` | ACCEPT WITH MINOR, corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` at `e8dc1e36a09b61e9410132f23551064f1661e769` | Independent re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` at `e3af70a495816c3d107f013b9ee2c17593600bae` | Independent re-check ACCEPTED. |

The paper asks which control decisions improve the final configuration at a common cap of 20 worker runs
and 80 manager calls. Sweep 1 logged 3,274 repeated configurations among 4,999 proposals. That observation
motivates the duplicate-skip comparison. D.3 pairs fresh campaigns and audits the final gain over the start
on ten fresh seeds. A0R minus A0 measures the effect of skipping repeats and detectable no-ops. A2 minus
A0R measures the gain from adding the noise-aware rule to that layer. Comparing A3 and A5 with A2 tests
whether the forecasts improve the campaign outcome. The measured differences and intervals will support
the claims under the declared decision rules. The offline gate measures one-step decision utility on logged
proposals. Campaign effects and intervals, gate estimates and verdict, full C1 audit rates and realized T1
scope are still placeholders. [Sweep 1 replay](https://github.com/dowlingwong/Agent_paper_B/blob/1afa7d62/docs/r1/reports/MAC_M3_DRYRUNS_20261104.md)

## Draft checks

| Draft | `latexmk` exit | Main text ends | Total pages | Rebuilt PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `afb1d6687fb7c3a843c7cf9365dc9a69781c2c6fe7ac6f0d1d1ad1fd7c40296a` |
| Gate-pass preview | 0 | 8 | 43 | `1d18fd95d1ba21ea3ccba62fe4e7465f14e0b0d4531f27847a7befa3296ba6a8` |

References begin on page 8 in both rendered drafts. Each log has nine existing overfull boxes and
no undefined citations, undefined references or multiply defined labels. The `FinalPaper` guard exits
12 at the unset gate switch. Task ancestry and `git diff --check` passed. This is a verification round,
so the published reviews above apply and there is no new code-suite run.

Verified SHA-256 values are recorded in the [previous round](20261127-writer-round-1afa7d62.md).
This round rechecked the claim sheet, frozen D.3 rev 4, signed PRE-SPLIT v2, the second screening
re-issue, and the tier-E ACCEPTED expansion binding review against those values.

## Blockers and next checks

- **Screening and D.3.** Compute owns `compute/20261127-35`. The latest observed scene
  `SMEAS_EVIDENCE_20261127T2125Z` STOPped with 444/10,164 runs written and zero failed.
  Manifest SHA-256 `61f3822e4109286e57982b3c60152c5a81b914fac85a4ce1b6c1e1e3b7301d18`.
  Check for a fresh stamp and strict preflight under the same signed note and co-tenancy guard.
  D.3 step (8) and campaigns wait for the screening result and any required SHARED decision.
  HTCondor preflight jobs `760148`, `760149` and `760152` were removed unmatched. Check for a matched
  layout, per-arm smoke and campaign authorizations. D.3b also needs frozen arms.
- **G.5.** P11 TASL-2 launch validation refused the unfilled spec. Check the engineering smoke path as
  routed in `compute/20261127-08` and the combined reviewed P11 record for `compute/20261127-32`.
  Houseprice `tasl2-cpuset-mlgym_houseprice-20261127` has two seals. `compute/20261127-33` needs a fresh
  S14 run ID and three accepted seals. The note awaits the P11 and S14 receipts, final binding and review.
  All four expansion G.1b nodes passed under `g1b-x-tasl-20261126-a`. G.5 addenda await the reviewed
  D6 expansion copy path (`compute/20261127-36`), per-node P10 decisions and launch checks.
- **Ada and Paper C.** P5 run `p5_20261127_b/e0e` has ended. The bound-kernel smoke passed, and the
  E0 comparison STOPped on RPS. Recipes differ at R1-E0-HEADFIT. The independent verdict at
  `be396f102d57ec5d418250eee9d82bc93894766a` accepts the record. Its `ada_smoke_e0` line awaits author
  disposition, accepted equivalence and a reviewed timing carry-forward before phase-1 publication.
  E0 comparison SHA-256 `7d3b9f8721e586615ba9992d0cbc3c56a20f52b11cb534aebb021e390aa5a5d4`.
  H200 request `760065` was removed unmatched. E-INT `compute/20261127-28` awaits its smoke and an
  eligible Ada lease. No E-INT ID is recorded.
- **Writer.** The gate is unread. Check G.5 labels, train/dev release, the reviewed target consumers
  and preregistration bindings, trained and calibrated frozen arms, proof checks, and test release.
  C1 awaits its applicable post-freeze release. On a result card, branch from the published manuscript
  pin, bind each result to its released source, rebuild both drafts and get independent review.
  The coordinator publishes the reviewed revision and research pin.

No writer job is active. Latest status is from the fetched Compute branch
`17a20d28dc2e2b2857fbb634b42f54bbfd417ae8` and the newer
[Local reconciliation](https://github.com/dowlingwong/Agent_paper_B/blob/0a7ab16cefa5114e3416057f5d139446b78af793/reports/20261127-local-round-compute-receipts.md).
The latter records the more recent screening receipt and the finished Ada E0 run. Neither was live
at the latest checked report. No evidence job was submitted and no sealed data was accessed this round.

Decided alone to preserve all 15 dirty worktree paths after checking they match published main byte for
byte. The linked worktree's Git metadata denied writes. Fetch and reporting used temporary metadata,
and the builds used a scratch export of the pinned manuscript. The manuscript sources are unchanged.
