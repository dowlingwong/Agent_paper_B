# Paper B Writer round, 28 November 2026

**Writer idle.** Research base `f7dc4945f63e09d1a7b66207bbbc43f76997aa29`, coordinator queue
`ae3105eea81a875832f17b3658eb35143fea4ab9`, and standalone manuscript main and research pin
`c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`. All five Writer cards are published. The next Writer
delivery is the runbook §3 result-table update. It awaits a task ID and released results. See the
[manuscript pin](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5).

| Task ID | Research delivery branch and exact tip | Recorded review |
|---|---|---|
| `writer/20261126-01` and `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | Restructure ACCEPT WITH MINOR, corrections applied. The title and trim follow-up had no separate review. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | ACCEPT WITH MINOR, corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | Independent re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | Independent re-check ACCEPTED. |

Which control decisions improve the final configuration at the same budget? In the Sweep 1 replay, 3,274
of 4,999 proposals repeated configurations already evaluated. That count motivates the test of whether
skipping repeats improves the campaign outcome. D.3 starts each arm from the same configuration on matched
instances, caps it at 20 worker runs and 80 manager calls, and compares the final configuration with the start
on ten fresh seeds. A0R versus A0 measures the effect of skipping repeats and detectable no-ops. A2 versus
A0R measures what the noise-aware rule adds. A3 and A5 versus A2 measure what their forecasts add. The paired
effects, intervals and declared Holm decisions determine which campaign claims are supported. The offline gate
separately tests one-step decision utility on logged proposals. See the
[Sweep 1 replay](https://github.com/dowlingwong/Agent_paper_B/blob/f7dc4945/docs/r1/reports/MAC_M3_DRYRUNS_20261104.md)
and [claim-to-table sheet](https://github.com/dowlingwong/Agent_paper_B/blob/f7dc4945/docs/r1/proposals/PAPER_B_CLAIM_TABLE_SHEET_20261126.md).

## Build and review checks

| Draft preview | Build exit | Last main-text page | Total pages | Rebuilt PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `e6da09bc1c9dde4e01abc59fcb1654ec3f26cee2f5c4b4c95ed10863b6118a7e` |
| Gate pass | 0 | 8 | 43 | `e987c82183df2723f583250fbfaa393eb0f44af142b924189474d4fedb9c13cb` |

Both README builds matched the published pre-migration PDFs page for page in extracted text and 100 dpi renders.
References begin on page 8 in both previews. Both logs contain nine existing overfull boxes and zero unresolved
citations, unresolved references or duplicate labels. The `FinalPaper` build exited 12 at the unset gate switch.
Ancestry checks and `git diff --check` passed. The campaign contrasts and intervals, gate verdict and effects,
full C1 audit rates, realised T1 scope, evidence bindings and pending reference details still have placeholders.
The table above records existing reviews. This round verifies the published pin and reports queue status.

| Published record | Verified SHA-256 |
|---|---|
| Claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Restructure re-check | `55444e2222bf99b8af0597e98920dcca23b6c89350dd814df1252cc416ca4d96` |
| Frozen D.3 rev 4 | `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745` |
| D.3 step (8) binding review | `59539fe482da5c28fa1cc1e8cc62c6187b79bdef3153fe505025a0dc7485a7f4` |
| P11 host repair review | `169ad247b69f9371bcc59332cccb9557ab81c02dc8850a4f52032d05aaf4a9e2` |

## Next checks

- **D.3.** Screening `SMEAS_EVIDENCE_20261128T001405Z` completed 10,164 of 10,164 with zero failures
  and zero SHARED decisions. The step (8) binding is published. The queue now assigns Local
  `local/20261128-06` to inventory P1–P8 and the GPU and walltime fields for the D.3a note. Check that handoff,
  a startable GPU for the Compute preflight, and the coordinator's per-arm smoke card for
  `openml_climate` seeds 6301–6302. Compute saw `Start=false` on the TOpAS A100 and ETP L40S and submitted
  no new job under `compute/20261128-03` / `-12`. Prior IDs `760148`, `760149`, `760152`, `759624`
  and `759625` are closed. The campaign notes still need their approvals. D.3b also needs frozen arms.
  [Local readiness card](https://github.com/dowlingwong/Agent_paper_B/blob/ae3105ee/tasks/local/20261128-06-d3a-readiness.md)
- **G.5 and gate.** The engineering matrix `g5-p11-20261128T014000Z` stopped on the synthetic baseline
  and close-CLI defects. The accepted STOP record `ba02dc21` and repair `2f110e26` are published. Check
  `compute/20261128-10` for a fresh TASL-2/TASL-7 stamp, job IDs and independently reviewed coverage.
  Local `20261126-08` then binds and renders the final G.5 note for review and coordinator publication.
  The gate still requires completed labels, train/dev release, reviewed consumer and preregistration
  bindings, frozen arms, proof checks and explicit test release.
  [Matrix rerun card](https://github.com/dowlingwong/Agent_paper_B/blob/ae3105ee/tasks/compute/20261128-10-p11-matrix-rerun.md)
- **P.4 and A5.** Same-code repeats `p5_e0_rep_20261128_ada/e0e` (PID `3548655`) and
  `p5_e0_rep_20261128_tasl7/e0e` (PID `2431912`) are complete. The author owns the E0 criterion
  decision before the Ada phase-1 note and A5 SFT. Request `760065` was withdrawn. Paper C E-INT
  `compute/20261127-28` awaits the bound census authorization, staged inputs, an eligible lease and smoke.
  [Author queue](https://github.com/dowlingwong/Agent_paper_B/blob/ae3105ee/AUTHOR.md)
- **Jobs elsewhere.** The latest host receipt at 02:55–02:56 UTC recorded no active Paper B job. HTCondor
  `760158.0` was active for R2. The P11 rerun was dispatched after that observation, with no new run ID
  in the fetched reports. Check the P11 ledger first.
  [Compute receipt](https://github.com/dowlingwong/Agent_paper_B/blob/3b9a1b81/reports/20261128-15-round-status.md)

Decided alone to preserve the 15 modified paths in the assigned worktree after verifying they match published
main. The linked Git metadata refused the fetch write, so fetch and this report used writable scratch metadata.
The builds used a clean scratch export of the standalone manuscript pin. Writer submitted no jobs, opened no
sealed partitions and made no new manuscript revision. Next round checks the queue and signed release receipts,
then takes the first assigned result update on a standalone manuscript task branch and gets its required review.
The coordinator publishes the manuscript and advances the research pin.
