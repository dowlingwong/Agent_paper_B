# Paper B writer round, 28 November 2026

Writer is idle at research main `b70cfa01e42ca6fb9a39e4c0f141c4aaf36871da` and coordinator queue
`911e0d93d34bc108d28f0a8f610fffece3aa6df9`. The [manuscript main](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)
and research submodule pin both resolve to `c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`. All five
writer cards are published. The next item, result tables in runbook §3 item 4, awaits an assigned ID
and released results.

| Task ID | Delivery branch and tip | Research merge | Recorded review |
|---|---|---|---|
| `writer/20261126-01` and `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | `6bc4f0df` | Restructure ACCEPT WITH MINOR, corrections applied. The title and trim had no separate review. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | `4490a0a9` | ACCEPT WITH MINOR, corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | `03a352d9` | Independent re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | `e153df24` | Independent re-check ACCEPTED. |

## Question and evidence

Which decisions leave an automated search with a better final configuration at the same budget?
The Sweep 1 replay counted 3,274 repeats among 4,999 proposals. This measures how often repeat
proposals occurred and motivates testing whether skipping them improves the end of a campaign.
D.3 pairs campaigns on the same instances, caps each arm at 20 worker runs and 80 manager calls,
and measures the final configuration's improvement over its start on ten fresh seeds. A0R versus
A0 measures the effect of skipping repeats and detectable no-ops. A2 versus A0R measures what the
noise-aware rule adds. A3 and A5 versus A2 measure what their proposal-level forecasts add. The
paired estimates, intervals and declared Holm decisions will determine which improvements the
paper can claim. The preregistered offline gate measures whether forecasting improves one-step
decisions on logged proposals. Its verdict is pending. [Sweep 1 replay](https://github.com/dowlingwong/Agent_paper_B/blob/b70cfa01/docs/r1/reports/MAC_M3_DRYRUNS_20261104.md) · [Claim-to-table sheet](https://github.com/dowlingwong/Agent_paper_B/blob/b70cfa01/docs/r1/proposals/PAPER_B_CLAIM_TABLE_SHEET_20261126.md)

Campaign effects and intervals, gate verdict and effects, full C1 audit rates, realised T1 scope,
evidence bindings and pending citation and author wording fields remain placeholders.

## Build verification

| Draft | Build exit | Last main-text page | Total pages | Rebuilt PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `ca4a8df04d67317bfa8e15c93ea06810499de3c1576587c34ee235f1ca48896d` |
| Gate-pass preview | 0 | 8 | 43 | `c1b15e4c07a631d2d94a979f198b9996f8d74d5b6a3af14d922d3f96f94b66c9` |

Both README `latexmk` builds succeeded. Extracted text matched the published pre-migration PDFs
throughout. Pages 1 and 8 were rendered and visually checked in both versions. References begin
on page 8. Each final log has nine existing overfull boxes and zero unresolved citations,
unresolved references or duplicate labels. `FinalPaper` exited 12 at the unset gate switch.
This report adds no manuscript diff requiring a new review. The completed task reviews are
listed above.

| Published record | Verified SHA-256 |
|---|---|
| Claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Frozen D.3 rev 4 | `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745` |
| D.3a P8 host record | `72f2b9bdf65803c7b15f77acec13518bdad2048f7dac943e0eec1e273243ad17` |
| P8 final re-check, ACCEPTED | `e7f6adbcd3a44df11a435575e6676d0096b9f3459176b5dde8622eebbc003218` |
| Partial G.5 P11 rerun record | `910a1395f6598aabf344b7f60e095ee18a8f104ed7a56952f80a4259deaa9c8c` |
| Partial G.5 P11 checksum manifest | `a78f4e7c3ec25b373a33f44c717a2ee5c149ae9f48702ef26935c3f885b3b657` |

## Next checks

- **D.3a.** P8 passed and its final review was accepted. The new queue card `compute/20261128-12`
  routes P7 independently of the P11 hold. Check the TASL-2/Ada GPU layout and recorded job IDs
  for the seven-arm smoke on `openml_climate`, instance seeds 6301 and 6302. The 05:10 UTC
  Compute report predates that dispatch. The campaign then needs launch bindings, P10/P11 re-checks,
  independent review and the P9 author signature. D.3b also needs frozen arms and its own authorization.
  [Queue card](https://github.com/dowlingwong/Agent_paper_B/blob/911e0d93/tasks/compute/20261128-12-order-p7-now.md) · [P8 review](https://github.com/dowlingwong/Agent_paper_B/blob/b70cfa01/docs/r1/reviews/D3A_P8_HOST_RECHECK2_20261128.md)
- **G.5 and the gate.** P11 rerun `g5-p11-20261128T033600Z` passed the primary two-host lease matrix
  and the expected infrastructure STOP 7. Four TASL-7 scenarios await an empty card under the reviewed
  launcher: `-determinism`, `-restart`, `-tar` and `-closeserver`. Compute reported 289/289
  checksum entries matched. The completed matrix needs its own review before Local can finish
  `local/20261126-08` and the coordinator can publish the note. Expansion D6 copy is published.
  The gate still needs G.5 labels, train/dev release, reviewed consumer and preregistration
  bindings, frozen arms, proof checks and explicit test release. [Published P11 record](https://github.com/dowlingwong/Agent_paper_B/blob/b70cfa01/docs/r1/reports/g5_p11_engineering_20261128_rerun/G5_P11_ENGINEERING_RERUN_20261128.md)
- **P.4 and Paper C.** Ada E0 repeat `p5_e0_rep_20261128_ada/e0e` (PID `3548655`) and TASL-7
  repeat `p5_e0_rep_20261128_tasl7/e0e` (PID `2431912`) are closed. The author decision on the E0
  criterion still gates phase 1 and A5 SFT. Paper C E-INT `compute/20261127-28` awaits the
  bound census spec, staged data and an eligible Ada slot. [Compute round](https://github.com/dowlingwong/Agent_paper_B/blob/5ce21eb5/reports/20261128-19-round-status.md)
- **Jobs elsewhere.** Compute recorded zero running Paper B jobs at 05:10 UTC. R2 `760158.0`
  was no longer queued, TOpAS `c03-001-175` had `Start=false`, and the ETP L40S had no ad.
  Compute has the P7 dispatch and four pending P11 scenarios. Confirm any new P7 run ID,
  TASL-7 lease and process state, and current batch slot status in the next Compute receipt.
  The Writer role submitted zero jobs and opened zero sealed partitions.
- **Writer.** Fetch for the next result card and its published evidence. Use a standalone
  manuscript task branch, fill only released estimates and intervals, rebuild both drafts,
  and obtain the card's review. The coordinator owns publication and the pin update.

Decided alone to preserve the 15 modifications in the assigned worktree after confirming their
bytes match published research main. The linked Git directory refused fetch writes, so the round
used temporary writable Git metadata and a clean standalone manuscript clone. The only delivery
this round is this coordination report.
