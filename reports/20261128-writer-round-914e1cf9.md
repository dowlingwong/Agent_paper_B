# Paper B writer round — 28 November 2026

Writer is idle. Research base `914e1cf90fcc1a87dd2a59cc4984842281438eeb`, queue
`381c1bf23fb2d69c7adcbfcf894b60e1a45286e7`, and standalone [manuscript main and research pin](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)
`c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`. The five existing writer cards are published. The next results-table
card (runbook §3 item 4) awaits a task ID and released results.

| Task ID | Delivered branch and tip | Publication | Recorded review |
|---|---|---|---|
| `writer/20261126-01` and `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | `6bc4f0df` | ACCEPT WITH MINOR, corrected. Title and trim had no separate review. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | `4490a0a9` | ACCEPT WITH MINOR, corrected. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | `03a352d9` | Independent re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | `e153df24` | Independent re-check ACCEPTED. |

Paper B asks which control decisions improve a search campaign's final configuration at the same budget. The
Sweep 1 replay found 3,274 repeats among 4,999 proposals, which motivates testing whether skipping repeats
improves the final result. D.3 pairs arms on fresh instances at caps of 20 worker runs and 80 manager calls.
Each final configuration is compared with its start on ten fresh seeds. A0R versus A0 tests what skipping repeats
and detectable no-ops adds. A2 versus A0R tests what the noise-aware rule adds. A3 and A5 versus A2 test what
the learned forecasts add. The paired effect estimates, intervals and declared Holm decisions set the campaign
claims. The preregistered offline read separately measures immediate decisions on logged proposals against A2.
[Sweep 1 replay](https://github.com/dowlingwong/Agent_paper_B/blob/914e1cf9/docs/r1/reports/MAC_M3_DRYRUNS_20261104.md) ·
[Claim-to-table sheet](https://github.com/dowlingwong/Agent_paper_B/blob/914e1cf9/docs/r1/proposals/PAPER_B_CLAIM_TABLE_SHEET_20261126.md)

## Draft checks

| Draft | Build exit | Last main-text page | Total pages | Rebuilt PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass preview | 0 | 8 | 44 | `8bad8df22d2326376a4508741f1a391d5ca2bc6f4bac78255b43345f56a0733b` |
| Gate-pass preview | 0 | 8 | 43 | `1590ed83a503eb01222c28fac2b76b0033f7d9d5c7719539124b3fc62c0c450a` |

Both README `latexmk` builds passed. Each page's extracted text and 100 dpi render matched the published
pre-migration PDF. Visual inspection confirmed that the limitations end and references start on page 8 in both.
Each final log showed nine overfull warnings and zero unresolved references, citations or duplicate labels.
The final-build guard exited 12 at the unset gate switch. Campaign effects and intervals, gate verdict and effects,
full C1 audit rates, realised T1 scope, evidence bindings and the author-approved anonymous reference remain
placeholders. This round verified the published pin, with no new manuscript revision for independent review.

## Jobs and dependencies

- **D.3 batch preflight, `compute/20261128-03`.** Published re-check `c5e2df4a` found `Start=false` for the ETP
  L40S and TOpAS A100 and submitted nothing. At 01:32 UTC, the only running job on that account in the queue
  was `760158.0` for R2. Check for a startable slot and a new Paper B job ID. The earlier screening
  `SMEAS_EVIDENCE_20261128T001405Z` completed 10,164/10,164 with zero failures and no SHARED verdict.
  `R1_THEORY_RHO_2_FINAL` releases the rev 4 step (8) bindings (`local/20261128-04`). The per-arm smoke
  and stage-specific launch notes still precede D.3. D.3b also needs the frozen arms.
  [Published preflight](https://github.com/dowlingwong/Agent_paper_B/blob/914e1cf9/docs/r1/reports/d3_preflight_20261128_recheck/D3_HTCONDOR_PREFLIGHT_RECHECK_20261128.md)
- **G.5 P11 matrix, `compute/20261128-09`.** Compute branch `compute-g5-p11-matrix-20261128` @
  `0a7488182038b319c5d09e247c185c9646bd2136` reports an engineering STOP at
  `g5-p11-20261128T014000Z`. Both synthetic baselines stopped before proposals. The kit's step line reaches
  the result channel while the pinned parser looks in the run log. The closure commands also count their own
  process. The primary proposer was stopped and its lease released. The STOP is awaiting independent review
  and publication. Check for Local's reviewed fixes, coordinator reissue and fresh matrix IDs. The G.5 note
  still needs P11 coverage, the final binding, rendering and review. Expansion P10 is signed and addendum
  fills are with Local (`local/20261128-05`). The offline read still needs G.5 labels, train/dev release, the
  bound consumers, frozen arms, proof checks and explicit test release.
  [Compute task-branch STOP](https://github.com/dowlingwong/Agent_paper_B/blob/0a7488182038b319c5d09e247c185c9646bd2136/docs/r1/reports/g5_p11_engineering_20261128/G5_P11_ENGINEERING_20261128.md)
- **P.4 E0 repeats, `compute/20261128-08`.** Last queue snapshot reported both running on 28 Nov around
  02:40 CET. Ada card 0 PID `3548655` and TASL-7 `p5_e0_rep_20261128_tasl7` PID `2431912`.
  Their outcomes were pending in the fetched handoffs. Check the two receipts and review before the P.4
  phase-1 note and A5 SFT. Paper C E-INT `compute/20261127-28` still awaits its bound authorization,
  eligible Ada lease and smoke receipt.
  [Queue snapshot](https://github.com/dowlingwong/Agent_paper_B/blob/381c1bf23fb2d69c7adcbfcf894b60e1a45286e7/STATE.md)

SHA-256 of the published preflight record is
`5d44af0518095a5b660997bb3bbdc32b586f979bfee4017417c34e0626aa08eb`.
SHA-256 of the Compute P11 task-branch STOP record is
`efaa8c219de0d79827c043e58a2ba462a083bf53a5982ed0879e5e89354f3755`.
The `914e1cf9` round used engineering summaries and released records. Writer submitted zero jobs and opened zero
sealed partitions. The next round checks the queue and releases, then uses a standalone manuscript task branch
for approved estimates and intervals, both builds and fresh review. The coordinator publishes and updates the pin.

Decided alone to preserve all 15 modified paths in the assigned worktree after verifying that each matches
published main byte for byte. The linked Git metadata denied the fetch write, so this round used a writable
temporary research clone for fetch and reporting, and a clean temporary clone of the published manuscript pin
for verification.
