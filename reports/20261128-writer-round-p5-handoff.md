# Paper B writer round — drafts verified, result tables waiting for release

- Research base: `dbce0316e1ffae94d0b6525a6eb5746dd7f8c907`. Coordinator queue: `a064fd47b96d070ec3e0dba5f2add37e133c8f13`. Incoming writer report tip: `d507bb0f3c482f149e28d9c98a95dd49bce1baec`.
- Tasks reconciled in queue order: `writer/20261126-01` with `writer/20261126-02` (restructure and shared-card, retry and sequencing disclosures) delivered at `writer-20261126-01-manuscript-restructure` @ `e360d425`, with an accepted-with-minors restructure re-check and the later trim recorded separately. `writer/20261126-03` delivered at `writer-20261126-03-claim-table-sheet` @ `acf7d37b` (accepted with minors, corrected). These deliveries are on research main. [Restructure and -02](20261126-01-manuscript-restructure.md) · [Eight-page trim](20261127-01-title-and-trim.md) · [Claim sheet delivery](20261126-03-claim-table-sheet.md)
- `writer/20261127-01` and `writer/20261127-02` are published (`e8dc1e36` and `e3af70a4`, respectively, with accepted reviews recorded). Both are represented in the published manuscript import. [Sources and rows](20261127-01-sources-and-27nov-rows.md) · [Codex edits](20261127-02-codex-manuscript-edits.md)
- The standalone [manuscript repository](https://github.com/dowlingwong/paper_B_manuscript) was clean on main at the published `papers/manuscript` pin `c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`. Both previews build. This round has no runnable writer card, manuscript diff or new manuscript review. The next result-table card waits on released evidence.
- Local has delivered the accepted D.3a P5 accounting unit for publication. The latest batch preflight still has no startable slot. The writer submitted zero jobs and read zero sealed partitions. [Local handoff](https://github.com/dowlingwong/Agent_paper_B/blob/25157781/reports/20261128-07-d3-evidence-accounting.md) · [Compute re-check](https://github.com/dowlingwong/Agent_paper_B/blob/b72b1aa8/reports/20261128-16-d3-preflight-recheck3.md)

## Question, measurement and claim

Which decisions leave an automated search with a better final configuration at the same budget? In the released Sweep 1 replay, 3,274 of 4,999 proposals repeated a configuration already evaluated. That count establishes how common repeats were in that replay and motivates testing whether skipping them improves campaign outcomes. D.3 pairs campaigns on the same instances, caps each at 20 worker runs and 80 manager calls, and remeasures the final improvement over the starting configuration on ten fresh seeds. A0R − A0 tests skipping repeats and detectable no-ops. A2 − A0R tests the added value of the noise-aware rule. A3 and A5 against A2 test the benefit of using proposal-level forecasts. The released paired estimates, intervals and declared Holm decisions will determine which benefits the paper can claim. The separate offline gate tests the immediate decisions made on logged proposals, and its verdict is still pending. [Sweep 1 replay](https://github.com/dowlingwong/Agent_paper_B/blob/dbce0316/docs/r1/reports/MAC_M3_DRYRUNS_20261104.md) · [Claim-to-table sheet](https://github.com/dowlingwong/Agent_paper_B/blob/dbce0316/docs/r1/proposals/PAPER_B_CLAIM_TABLE_SHEET_20261126.md)

The signed screening run completed 10,164 of 10,164 runs, with zero failures and zero SHARED decisions. That result fixed `R1_THEORY_RHO_2_FINAL` and cleared the D.3 step (8) binding. Campaign outcomes and gate effects still have placeholders, along with the full C1 audit rates, realised T1 scope, per-run evidence bindings and pending citation details. The signed expansion P10 methods update is available for the next relevant manuscript card: MetaMaze uses Student-t with five degrees of freedom, and Titanic, ETTh1 and Forest Cover use Gaussian targets. [Screening record](https://github.com/dowlingwong/Agent_paper_B/blob/dbce0316/docs/r1/reports/screen_measure_20261128/dt2/SCREEN_MEASURE_DT2_20261128.md) · [PLAN §10](https://github.com/dowlingwong/Agent_paper_B/blob/dbce0316/docs/r1/PLAN.md#10-open-decisions)

## Draft verification

| Preview | Build exit | Last main-text page | Total pages | Rebuilt PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `9000b29f3f0ec116528d15cb1e3e8dbe0abec1f6d93307ef4e571fcf403a2173` |
| Gate pass | 0 | 8 | 43 | `975ce9fa3498ffaad48c0ca55b9a48854924ec44505f4728c280dec53b4acfb4` |

Built both README variants with `latexmk`. Full extracted text and the 100-dpi renders of pages 1 and 8 match the published pre-migration PDFs. Visually checked those pages in both previews. References begin on page 8. Each final build log has nine existing overfull box warnings and no undefined references, undefined citations or duplicate labels. `FinalPaper` exits 12 at the unset gate switch. `git diff --check` passed for this report. These are manuscript preview checks. The manuscript review verdicts above are the recorded delivery verdicts.

| Bound record | SHA-256 |
|---|---|
| Published claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Frozen D.3 rev 4 | `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745` |
| Published D.3a readiness inventory | `4e25701f1fa9e8df159361c3f2f73548689252620dfe131a34c05b35e19e9b0a` |
| Published screening record | `34f5a2dd04aacefd1ddeb29227038eb8602b8d4c94d73066ba1e3a1f41dca198` |
| P5 R2 review, ACCEPTED, per Local handoff | `f9c4a9cd33bf1bae50a092572c6a15e7cb1e739da724290ca29818631552eaa7` |

## Dependencies for the next round

| Lane | Last recorded state and next check |
|---|---|
| Writer | Idle. Fetch the queue and look for a result release or a new writer card. Fill released fields on a standalone manuscript task branch, rebuild both drafts and obtain the required review. The coordinator publishes reviewed changes and advances the pin. |
| D.3a | Local `20261128-07` delivered P5 on `local-20261128-07-d3-evidence-accounting` @ `bb3f2e8e388322dbe4ceaa786a13889255c51baa`, independent tier-E R2 ACCEPTED. The coordinator owns publication. Compute `20261128-11` follows the P11 matrix receipt with the GPU layout, P7 seven-arm smoke on `openml_climate` seeds 6301 and 6302, live proposer-to-device verification and P8 deepthought audit checks. Check its job IDs and reviewed records, then the actual launch bindings, P10/P11 re-checks and P9 author signature. D.3b also needs frozen arms and its own authorization. |
| G.5 and gate | Compute `20261128-10` owns the P11 matrix rerun on TASL-2/TASL-7. `g5-p11-20261128T014000Z` is the retained STOP. The fetched reports carry no fresh rerun ID or stamp. Check its ledger and accepted host coverage first, then Local `20261126-08` for the final render and publication. The gate also needs collected labels, train/dev release, reviewed consumer and preregistration bindings, arms freeze, proof checks and explicit test release. |
| P.4 and A5 | Ada E0 repeat `p5_e0_rep_20261128_ada/e0e` (PID `3548655`) and TASL-7 repeat `p5_e0_rep_20261128_tasl7/e0e` (PID `2431912`) are closed. The author owns the E0 criterion decision before the phase-1 note and A5 SFT. |
| Jobs elsewhere | Compute's direct-host snapshot at 02:55–02:56 UTC recorded idle Paper B hosts. At the separate 04:40:33 UTC batch check, TOpAS A100 `c03-001-175` had `Start=false`, the ETP L40S had no ad, and no `dwong` job was queued. R2 `760158.0` was no longer listed. Older IDs `760148`, `760149`, `760152`, `759624`, `759625` and `760065` are closed. No current Paper B execution elsewhere was verified. Recheck Compute's rerun and smoke ledgers before any new submission. |

Decided alone to preserve the assigned checkout's 15 modified paths after confirming they match current published research main byte for byte. Its linked Git directory denied the fetch write, so this round used writable scratch Git metadata for the queue and the clean standalone checkout for the builds. The only delivery is this coordination report.
