# Paper B writer round — 28 November 2026

Writer is idle. Research base `cb20c9fd846551462890409359fb4ccb31e5a045`, queue
`4f8e43ccc76c7625db05f41ebceab93d868d77bc`, and [manuscript main and research pin](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)
`c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`. The next writer handoff is the result tables
in runbook §3 item 4. Its task ID and released inputs are pending. The five existing cards are published.

| Task ID | Deliverable branch and exact tip | Publication | Recorded review |
|---|---|---|---|
| `writer/20261126-01` and `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | `6bc4f0df` | ACCEPT WITH MINOR, corrections applied. The title and trim had no separate review. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | `4490a0a9` | ACCEPT WITH MINOR, corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | `03a352d9` | Independent re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | `e153df24` | Independent re-check ACCEPTED. |

Paper B asks which control decisions leave a campaign with a better final configuration at the same budget.
The Sweep 1 replay found that 3,274 of 4,999 proposals repeated a configuration already evaluated. D.3 tests
whether skipping repeats helps by pairing arms on new instances at caps of 20 worker runs and 80 manager calls
and auditing each final configuration against its starting configuration on ten fresh seeds. A0R versus A0
measures what skipping repeats and detectable no-ops adds. A2 versus A0R measures what the noise-aware rule adds.
A3 and A5 versus A2 measure what the learned forecasts add. The paired estimates, intervals and declared Holm
decisions will determine which gains the paper can claim. The separate offline gate measures whether A3 and A5
improve immediate decisions on logged proposals relative to A2.
[Sweep replay](https://github.com/dowlingwong/Agent_paper_B/blob/cb20c9fd/docs/r1/reports/MAC_M3_DRYRUNS_20261104.md)
· [Claim-to-table sheet](https://github.com/dowlingwong/Agent_paper_B/blob/cb20c9fd/docs/r1/proposals/PAPER_B_CLAIM_TABLE_SHEET_20261126.md)

## Builds and checks

| Draft | Exit | Last main-text page | Total pages | Rebuilt PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `bedf9f03a2b2f1ee10b7efc5cfc75dc837656189e196dbc33fafa7eddf5827db` |
| Gate-pass preview | 0 | 8 | 43 | `062c13f0196dce464a2ffdd7e602607cfe576339f3ee2b17cada83dacb0e1079` |

Both README `latexmk` commands passed. Full extracted text matched the published pre-migration PDFs.
Page 8 was rendered and inspected in each draft. Both logs retained nine overfull box warnings and showed
zero unresolved references, citations or duplicate labels. The final-build guard returned 12 at the unset
gate outcome. The campaign estimates and intervals, offline verdict and effects, full C1 audit rates,
realised T1 scope and evidence bindings remain placeholders. This was build verification of the published
pin. No manuscript changes, independent review or task branch were needed this round.

| Published record | SHA-256 |
|---|---|
| Claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Frozen D.3 rev 4 | `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745` |
| Published deepthought2 screening analysis | `6c72535eae0673cb19853ca6130090369c2e5a2daacdc09f7989251aaaafdb41` |
| Screening independent re-check | `6977921483faef926d210273c91b0619ed887b465c852ff70fbe4f63800c57a0` |
| Expansion P10 basis | `b89b452e59caa88f1dcf2105fcf20c672f4a83f2c698e43dc6db2615c36a4533` |
| Independent P11 engineering smoke review | `3ee190e4507d481e47dff3adb6965499517552fd72d2552564f4ca1905dd37a7` |

## Other owners and dependencies

- **D.3.** Screening run `SMEAS_EVIDENCE_20261128T001405Z` is complete on deepthought2, with 10,164 of
  10,164 runs and zero failures. Both tested nodes were inconclusive and six were not tested by design.
  With no SHARED verdict, the declared decision `R1_THEORY_RHO_2_FINAL` releases step (8) on frozen rev 4.
  Local owns the hash bindings (`local/20261128-04`, tier E). Compute owns the HTCondor preflight
  (`compute/20261128-03`). Prior requests `760148`, `760149`, `760152`, `759624` and `759625` were removed.
  The last preflight found `Start=false` and submitted no job. Check for a startable slot and a new ID,
  then the per-arm smoke and the signed launch notes. D.3b also needs frozen arms.
  [Reviewed screening record](https://github.com/dowlingwong/Agent_paper_B/blob/bf4e0083/docs/r1/reports/screen_measure_20261128/dt2/SCREEN_MEASURE_DT2_20261128.md)
- **G.5 and the offline gate.** Expansion P10 is signed at `3013ddf0` (MetaMaze Student-t with five degrees
  of freedom, the three other expansion nodes Gaussian). Local owns the reviewed addendum fills
  (`local/20261128-05`). The engineering smoke path is tier-E ACCEPTED and on main. Compute owns the
  TASL-2/TASL-7 P11 matrix (`compute/20261128-09`), with the TASL-7 E0 repeat first on that card.
  Check for matrix IDs and the reviewed host record. G.5 awaits its final binding, render, review and note.
  The gate awaits G.5 labels, T1 train/dev release, reviewed consumers and preregistration bindings,
  trained and calibrated frozen arms, proof checks and explicit test release.
  [P11 card](https://github.com/dowlingwong/Agent_paper_B/blob/4f8e43cc/tasks/compute/20261128-09-p11-engineering-matrix.md)
- **P.4 and Paper C.** TASL-7 same-code E0 `p5_e0_ref_20261128/e0e` (PID `2289540`) finished
  19.09% below Ada `p5_20261127_b/e0e` on RPS, outside the 10% tolerance. The signed repeatability card
  `compute/20261128-08` assigns one repeat per host. Check for both new run IDs and the reviewed
  comparisons. Phase 1 and A5 SFT wait for E0 and the phase-1 note. Old H200 request `760065` was
  withdrawn. Paper C E-INT `compute/20261127-28` awaits its bound authorization, eligible Ada lease and
  smoke receipt.
  [E0 repeat card](https://github.com/dowlingwong/Agent_paper_B/blob/4f8e43cc/tasks/compute/20261128-08-e0-repeatability.md)

The latest Compute report (`1e770abe`) recorded zero active project jobs at its cutoff. The newer E0 and P11
cards have no run IDs in the fetched reports. The writer submitted zero jobs and opened zero sealed partitions.
The next writer round checks the queue and signed releases, then uses a separate manuscript task branch for
supported estimates and intervals, both draft builds and review. Publication and the research pin are the
coordinator's responsibility.

Decided alone to leave all 15 modified paths in the assigned checkout in place. They match published main
byte for byte. The linked Git metadata refused the fetch write, so fetch and report used writable temporary
Git metadata. The builds used a temporary export of the clean, pinned manuscript.
