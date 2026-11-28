# Paper B writer round — 28 November 2026

**Writer idle.** Research base `f7dc4945f63e09d1a7b66207bbbc43f76997aa29`, queue
`a041e1f77801862cadb92afd5c37fbc206a2d2a8`, and standalone manuscript main and research pin
`c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`. The five assigned Writer cards are published. The next
handoff, the result tables in runbook §3 item 4, awaits a Writer task ID and released campaign or gate results.
[Manuscript revision](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)

| Task ID | Research delivery branch and tip | Recorded review |
|---|---|---|
| `writer/20261126-01` and `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | ACCEPT WITH MINOR, corrections applied. The title and eight-page trim had no separate recorded review. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | ACCEPT WITH MINOR, corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | Independent re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | Independent re-check ACCEPTED. |

Paper B asks which control decisions give a search campaign a better final configuration at the same budget.
The Sweep 1 replay found 3,274 repeated configurations among 4,999 proposals. That count motivates testing
whether skipping repeats makes better use of the budget. D.3 pairs arms on the same fresh instances with caps
of 20 worker runs and 80 manager calls. It audits the final configuration against the start on ten fresh seeds.
A0R versus A0 estimates the gain from skipping repeats and detectable no-ops. A2 versus A0R estimates what the
noise-aware rule adds. A3 and A5 versus A2 estimate what their forecasts add. The paired effects, intervals and
declared Holm decisions will determine which campaign claims the data support. The offline gate separately tests
one-step decisions on logged proposals against A2.
[Sweep 1 replay](https://github.com/dowlingwong/Agent_paper_B/blob/f7dc4945/docs/r1/reports/MAC_M3_DRYRUNS_20261104.md)
· [Claim-to-table sheet](https://github.com/dowlingwong/Agent_paper_B/blob/f7dc4945/docs/r1/proposals/PAPER_B_CLAIM_TABLE_SHEET_20261126.md)

## Build and review checks

| Preview | README build exit | Final main-text page | Total pages | Rebuilt PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `4f22f096545e21f2fcc1256253efc5ef5d01a6c704316cf90ce9a64da96ebeb5` |
| Gate pass | 0 | 8 | 43 | `a8c691a8b6cb2638a6195987cbadbb73eb3fb244004ec596584cec7ad4bf7b30` |

Full extracted text and the renders of pages 1 and 8 match the corresponding published pre-migration PDFs.
Pages 1 and 8 were inspected. Both drafts begin references on page 8. Each build logged nine existing overfull
boxes and no unresolved citations, unresolved references or duplicate labels. `FinalPaper` exited 12 at the
unset gate-outcome switch. Campaign effects and intervals, gate verdict and effects, full C1 audit rates,
realised T1 scope, evidence bindings and unresolved citation details remain pending. This round verified the
published pin and produced a coordination report. There is no new manuscript task branch or review verdict.

| Published record | Verified SHA-256 |
|---|---|
| Claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Frozen D.3 rev 4 | `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745` |
| D.3 step (8) binding review | `59539fe482da5c28fa1cc1e8cc62c6187b79bdef3153fe505025a0dc7485a7f4` |
| P11 engineering STOP re-check | `ffafd52d789a8a4ad93279ff27befb2b7aa12542689cbf8d37e646531520e7b0` |
| P11 host repair review | `169ad247b69f9371bcc59332cccb9557ab81c02dc8850a4f52032d05aaf4a9e2` |

## Dependencies and recorded jobs

- **G.5 and gate.** P11 matrix `g5-p11-20261128T014000Z` stopped on the synthetic baseline and close-CLI
  defects. Its accepted STOP record `ba02dc21` and the accepted repair `2f110e26` are published. The coordinator
  reissued the matrix as `compute/20261128-10` on `f7dc4945`, with no fresh stamp or job ID in the fetched reports.
  Check for the new TASL-2/TASL-7 receipts and independent P11 coverage review. Local `20261126-08` then binds
  and renders the final G.5 note for review and coordinator publication. The gate also needs completed labels,
  the train/dev release, reviewed consumer and preregistration bindings, frozen arms, proof checks and explicit
  test release.
  [Reissued P11 card](https://github.com/dowlingwong/Agent_paper_B/blob/a041e1f77801862cadb92afd5c37fbc206a2d2a8/tasks/compute/20261128-10-p11-matrix-rerun.md)
- **D.3.** Screening `SMEAS_EVIDENCE_20261128T001405Z` finished 10,164 of 10,164 with zero failures and zero
  SHARED decisions. The declared disposition released step (8), and its hash bindings are published. The
  preflight `compute/20261128-03` / `-12` found `Start=false` on both the TOpAS A100 and ETP L40S and submitted
  no job. Prior attempts `760148`, `760149`, `760152`, `759624` and `759625` are closed. Check for a startable
  slot and fresh preflight ID, then the coordinator's `openml_climate` per-arm smoke card for seeds 6301–6302
  and the signed campaign authorizations. D.3b also needs frozen arms.
  [Screening result](https://github.com/dowlingwong/Agent_paper_B/blob/f7dc4945/docs/r1/reports/screen_measure_20261128/dt2/SCREEN_MEASURE_DT2_20261128.md)
- **P.4 and A5.** The Ada repeat `p5_e0_rep_20261128_ada/e0e` (PID `3548655`) finished inside the existing
  RPS tolerance. TASL-7 `p5_e0_rep_20261128_tasl7/e0e` (PID `2431912`) finished outside it. The author owns the
  E0 criterion decision before the phase-1 note and A5 SFT. H200 request `760065` was withdrawn. Paper C E-INT
  `compute/20261127-28` awaits its bound census authorization, staged inputs, an eligible Ada lease and smoke.
  [Author queue](https://github.com/dowlingwong/Agent_paper_B/blob/a041e1f77801862cadb92afd5c37fbc206a2d2a8/AUTHOR.md)
- **Running elsewhere.** The last host receipt at 02:55–02:56 UTC found no active Paper B job. HTCondor
  `760158.0` was active for R2. The coordinator reissued P11 after that observation. Its new ledger entry is the
  first job to check next round.
  [Compute receipt](https://github.com/dowlingwong/Agent_paper_B/blob/3b9a1b817acf8ce27397ab11e9ac74d747a37e09/reports/20261128-15-round-status.md)

Decided alone to preserve all 15 modified paths in the assigned worktree after confirming their contents match
published research main. The linked Git metadata refused the fetch write, so fetch and this report used
writable scratch metadata. Both builds used a scratch export of the clean manuscript pin. Writer submitted no
jobs and opened no sealed partitions. Next round checks the queue and signed release records, then starts the
first assigned result update on a standalone manuscript task branch and obtains a fresh review of both builds.
The coordinator publishes the manuscript and advances the research pin.
