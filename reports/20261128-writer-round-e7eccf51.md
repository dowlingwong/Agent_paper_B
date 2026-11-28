# Paper B writer round after the D.3a launch-binding STOP

The Writer queue is idle at research main `8fbad26ac68236bbf47d2f099851a906cb4f8427` and coordinator `11d09ddffaaa7f26341a5d8ae16d8b434790efe0`. All five writer cards are on published research main by ancestry. The next item, runbook §3 item 4, awaits a result release and a writer card. The standalone manuscript main and the research submodule both point to `c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`. [Writer queue](https://github.com/dowlingwong/Agent_paper_B/blob/11d09ddf/STATE.md#writer) · [Manuscript](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)

| Completed task | Research delivery branch @ tip | Recorded review |
|---|---|---|
| `writer/20261126-01` and `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | Restructure re-check ACCEPT WITH MINOR, corrections applied. The later title and eight-page trim had no separate review. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | ACCEPT WITH MINOR, corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | Independent re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | Independent re-check ACCEPTED. |

## Question, measurement and claim

Which control decisions produce a better final configuration under the same budget? In the Sweep 1 replay, 3,274 of 4,999 proposals repeated a configuration already evaluated. This establishes how often proposals repeated in that replay. D.3 pairs arms on fresh campaign instances and gives each campaign 20 worker runs and 80 manager calls. Ten fresh audit seeds measure the final configuration's improvement over the starting configuration, scaled by the node's noise level. A0R minus A0 measures what skipping duplicates and detectable no-ops adds. A2 minus A0R measures what the noise-aware rule adds with those skips in both arms. A3 and A5 versus A2 measure what their forecasts add. The released paired estimates, intervals and declared tests will determine which gains the paper can claim. The offline gate separately tests whether those forecasts improve one-step decisions on logged proposals. [Replay record](https://github.com/dowlingwong/Agent_paper_B/blob/8fbad26a/docs/r1/reports/MAC_M3_DRYRUNS_20261104.md) · [Claim-to-table sheet](https://github.com/dowlingwong/Agent_paper_B/blob/8fbad26a/docs/r1/proposals/PAPER_B_CLAIM_TABLE_SHEET_20261126.md) · [Frozen D.3 rev 4](https://github.com/dowlingwong/Agent_paper_B/blob/8fbad26a/docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md)

The gate and D.3 estimates, intervals and decisions, full C1 audit rates, realised T1 scope and evidence bindings remain placeholders. The abstract, anonymous companion citation and unresolved SGM author metadata retain their existing draft markings.

## Draft verification

| Draft | Build exit | Last main-text page | Total PDF pages | Built PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `605862ed8640a3f57d2d1bdf97a8720f46c5d96744fdd538051f4d7f4e12c72e` |
| Gate-pass preview | 0 | 8 | 43 | `bdcf349c90fd4130ceb71c558393f3ee96b907feaee3a99d8b4b2e7a6621ae63` |

Both README builds passed from the pinned sources. Pages 1 and 8 were rendered and inspected in both drafts. The references start on page 8. Each final draft log has nine existing overfull boxes and zero undefined references, undefined citations or duplicate labels. The `FinalPaper` smoke returned 12 at the unset gate switch. This round verified an existing published draft, so the recorded reviews apply to the earlier deliveries and there is no new manuscript review or task-branch tip.

| Verified record | SHA-256 |
|---|---|
| Claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Frozen D.3 rev 4 | `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745` |
| Published D.3a P7 receipt | `a73ea6359afd5789ecf2853cf66ca0b25cfe6263eb7da82b56ca0423267d2d72` |
| Local D.3a launch-binding STOP report | `89f4366b458d89a536cbd00ea9bf0194519224a9a9e968e563ca05bd64835aca` |

## Pending work and next checks

- **D.3a launch binding.** Local `20261128-08` published its unsigned note branch `local-20261128-08-d3a-note-fill` @ `feb3c132526e3614b13ec0c6a629ae1c4038d961`. Independent tier-E review accepted the blocked handoff. The published P7 run IDs `d3a-p7-20261128-c` and `-d` are complete. The worker gate passed at 33/271 (12.18%). The smoke used context 8,192 and has no explicit q8_0 K/V settings. Frozen rev 4 specifies context 32,768 and q8_0 K/V. Check for a coordinator-routed exact-runtime verification and a fresh recorded ID. Then check the launch commit and run ID, P10/P11 at that commit, independent review, author P9 and publication. There are zero D.3a evidence campaigns. D.3b separately needs frozen arms and its own authorization. [Local STOP](https://github.com/dowlingwong/Agent_paper_B/blob/e7eccf51/reports/20261128-08-d3a-note-fill-stop.md) · [P7 receipt](https://github.com/dowlingwong/Agent_paper_B/blob/8fbad26a/docs/r1/reports/d3a_p7_20261128/D3A_P7_20261128.md)
- **G.5 and offline gate.** P11 matrix `g5-p11-20261128T033600Z` is partial. `compute/20261128-12` needs the TASL-7 determinism, restart, tar and close-server scenarios on an empty card under the reviewed guard. Then Local needs an accepted two-host record and final `paper.commit` to render the G.5 note for publication. The gate depends on completed G.5 labels, train/dev release, reviewed consumer and preregistration bindings, proof checks, arms freeze and explicit test release. [Compute status](https://github.com/dowlingwong/Agent_paper_B/blob/ece384d9/reports/20261128-23-round-status.md) · [Local dependencies](https://github.com/dowlingwong/Agent_paper_B/blob/e7eccf51/reports/20261128-08-d3a-note-fill-stop.md#round-close)
- **Compute status.** The latest Compute snapshot at 07:56–07:57 UTC recorded zero active Paper B jobs. TASL-7 had foreign compute and `760158.0` had left the HTCondor queue. Check for a startable ETP L40S or TOpAS A100 before the preflight retry. The P.4 E0 repeat IDs `p5_e0_rep_20261128_ada/e0e` and `p5_e0_rep_20261128_tasl7/e0e` are complete. P.4 phase 1 and A5 SFT wait for the author’s E0 criterion and the phase-1 note. [Compute status](https://github.com/dowlingwong/Agent_paper_B/blob/ece384d9/reports/20261128-23-round-status.md) · [Author queue](https://github.com/dowlingwong/Agent_paper_B/blob/11d09ddf/AUTHOR.md)
- **Writer next.** Fetch for a result-table card and explicit releases, fill the authorised cells on a standalone manuscript task branch, then build both drafts and obtain fresh review. The coordinator publishes the revision and advances the research pin. [Runbook §3](https://github.com/dowlingwong/Agent_paper_B/blob/8fbad26a/docs/r1/runbooks/AUTOML_AS_DAC_NEXT_PHASE_20261126.md#3-paper-b-manuscript-and-results)

Decided alone to preserve all 15 pre-existing worktree changes after verifying their bytes match published main and to use writable temporary Git metadata after the linked worktree refused a fetch write. A temporary archive supplied the pinned manuscript build. No manuscript edits, job submissions or sealed-partition reads occurred.
