# Paper B writer round — 28 November 2026

Writer is idle. Research base `dbce0316e1ffae94d0b6525a6eb5746dd7f8c907`, coordinator queue
`a064fd47b96d070ec3e0dba5f2add37e133c8f13`, and standalone manuscript main and research pin
`c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`. The five assigned Writer cards are published.
Runbook §3 item 4 awaits released results and a Writer task ID.
[Manuscript revision](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)

| Task ID | Published delivery branch and tip | Recorded review |
|---|---|---|
| `writer/20261126-01` with `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | ACCEPT WITH MINOR, corrections applied. No separate review is recorded for the title and eight-page trim. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | ACCEPT WITH MINOR, corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | Independent re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | Independent re-check ACCEPTED. |

Which control decisions leave a search with a better final configuration at the same budget? In Sweep 1,
3,274 of 4,999 replayed proposals repeated a configuration already evaluated. That tally motivates the
D.3 test of skipping repeats. D.3 pairs campaigns on the same starting configurations and instances,
with caps of 20 worker runs and 80 manager calls. It measures the improvement from start to finish
on ten fresh seeds. A0R versus A0 measures the effect of skipping repeats and detectable no-ops.
A2 versus A0R measures the added effect of the noise-aware rule. A3 and A5 versus A2 measure what
proposal-level forecasts add. The paired estimates, intervals and declared Holm decisions determine
which of those campaign claims the data support. The offline gate tests one-step decisions on logged proposals.
[Sweep 1 replay](https://github.com/dowlingwong/Agent_paper_B/blob/dbce0316/docs/r1/reports/MAC_M3_DRYRUNS_20261104.md)
· [Claim-to-table sheet](https://github.com/dowlingwong/Agent_paper_B/blob/dbce0316/docs/r1/proposals/PAPER_B_CLAIM_TABLE_SHEET_20261126.md)

## Draft verification

| Preview | Build exit | Last main-text page | Total pages | Rebuilt PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `0f372009924a0d49e8a75af9bb85cb597fec3e4a3ff5f95315da773f1d003625` |
| Gate pass | 0 | 8 | 43 | `ac48ad0beb9f9aba3ba619dc212bbc796c47bdd0c977e49c6457b2045297f5d6` |

Full extracted text and the 100 dpi renders of pages 1 and 8 match the published pre-migration PDFs.
I inspected both pages in each preview. References start on page 8. Both logs have nine existing
overfull box warnings and no undefined citations, undefined references or duplicate labels.
`FinalPaper` exited 12 at the unset gate switch. Ancestry and `git diff --check` passed.
Campaign effects and intervals, gate verdict and effects, full C1 audit rates, realised T1 scope, evidence
bindings and pending citation details still have placeholders. This status round has no new manuscript
revision or review verdict.

| Published record | Verified SHA-256 |
|---|---|
| Claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Frozen D.3 rev 4 | `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745` |
| Accepted D.3 step (8) binding review | `59539fe482da5c28fa1cc1e8cc62c6187b79bdef3153fe505025a0dc7485a7f4` |
| Published D.3a readiness inventory | `4e25701f1fa9e8df159361c3f2f73548689252620dfe131a34c05b35e19e9b0a` |
| Independent D.3a readiness review, ACCEPTED | `f10a16136cb8c81e486a53bef1309f6160b40efe79bd28869a4db5f7cbff5171` |
| Accepted P11 host repair review | `169ad247b69f9371bcc59332cccb9557ab81c02dc8850a4f52032d05aaf4a9e2` |

## Next checks

- **D.3.** Screening `SMEAS_EVIDENCE_20261128T001405Z` completed 10,164 of 10,164 with zero
  failures and zero SHARED decisions. Step (8) is bound. The published readiness inventory supplies
  P1–P4 and P6. Local `20261128-07` owns P5 actual proposer GPU seconds and retry counts. After
  the P11 rerun receipt, Compute `20261128-11` reports a measured GPU layout, runs the prescribed
  seven-arm `openml_climate` smoke at seeds 6301–6302 on each intended model, and checks the
  deepthought audit host. Check its new job IDs and reviews, then the launch-commit checks and
  D.3a signature. D.3b also needs frozen arms and its own authorization.
  [Readiness inventory](https://github.com/dowlingwong/Agent_paper_B/blob/dbce0316/docs/r1/reports/D3A_READINESS_20261128.md)
  · [Compute card](https://github.com/dowlingwong/Agent_paper_B/blob/a064fd47/tasks/compute/20261128-11-d3a-p7-p8.md)
- **G.5 and gate.** Compute `20261128-10` was reissued on the published repair. Check for a fresh
  TASL-2/TASL-7 P11 matrix stamp, job IDs and accepted coverage. `g5-p11-20261128T014000Z` is the
  previous STOP. Local `20261126-08` then binds and renders the final G.5 note for review and
  publication. The gate also needs collected labels, train/dev release, reviewed consumer and
  preregistration bindings, the frozen arms, proof checks and explicit test release.
  [P11 rerun card](https://github.com/dowlingwong/Agent_paper_B/blob/a064fd47/tasks/compute/20261128-10-p11-matrix-rerun.md)
- **P.4 and A5.** The Ada repeat `p5_e0_rep_20261128_ada/e0e` (PID `3548655`) and TASL-7 repeat
  `p5_e0_rep_20261128_tasl7/e0e` (PID `2431912`) are closed. The author owns the E0 criterion decision
  before the Ada phase-1 note and A5 SFT. Paper C E-INT still needs its bound census instructions,
  staged inputs, Ada lease and smoke receipt.
  [Author queue](https://github.com/dowlingwong/Agent_paper_B/blob/a064fd47/AUTHOR.md)
- **Jobs elsewhere.** The latest Compute host receipt at 02:55–02:56 UTC recorded no active Paper B
  job. HTCondor `760158.0` belonged to R2. The ETP L40S and TOpAS A100 had `Start=false`, and no
  new D.3 preflight was submitted. Older IDs `760148`, `760149`, `760152`, `759624`, `759625` and
  `760065` are closed. The P11 rerun was reissued after that receipt and has no new job ID in the
  fetched reports. Check its ledger and the P7 layout handoff first.
  [Compute receipt](https://github.com/dowlingwong/Agent_paper_B/blob/3b9a1b81/reports/20261128-15-round-status.md)

Decided alone to preserve the 15 modified paths in the assigned checkout after confirming that each
matches current published research main byte for byte. The linked Git directory denied the fetch write.
I fetched the queue in writable scratch Git metadata and rebuilt a clean archive of the published manuscript
pin. Writer submitted no jobs and opened no sealed partitions. On the next ready result card, use a
standalone task branch, fill only the released fields, rebuild both drafts and obtain the required review.
The coordinator publishes the reviewed manuscript and advances the research pin.
