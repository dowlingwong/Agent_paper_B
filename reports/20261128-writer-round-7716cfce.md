# Paper B writer round — 28 November 2026

Writer is idle. The five assigned writer cards are published. The result tables
(runbook §3 item 4) have no assigned task ID and await released evidence.
Research base `7716cfced1a30105f38590114c2b2d200b6b417d`, queue
`a06dfc3f5fb11ddea6fa74191fe78d8733ac62a9`, and
[manuscript main](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)
and its research pin `c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`.

| Published task | Deliverable branch and tip | Publication | Recorded review |
|---|---|---|---|
| `writer/20261126-01` with `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | `6bc4f0df` | Restructure ACCEPT WITH MINOR, corrections applied. No separate review for the title and trim follow-up. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | `4490a0a9` | ACCEPT WITH MINOR, corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | `03a352d9` | Independent re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | `e153df24` | Independent re-check ACCEPTED. |

Paper B asks which control decisions leave the search with a better final configuration at the same budget.
In the Sweep 1 replay, 3,274 of 4,999 proposals repeated an evaluated configuration. That count measures
how often repeats arise and motivates testing how much skipping them helps. D.3 pairs arms on the same
new instances and starts, with caps of 20 worker runs and 80 manager calls, then measures final improvement
over the start on ten fresh seeds. A0R versus A0 measures the contribution of skipping repeats and detectable
no-ops. A2 versus A0R measures what the noise-aware rule adds, and A3 and A5 versus A2 measure what the
learned forecasts add. The paired effects, intervals and declared Holm decisions will determine the claims.
The preregistered offline gate measures one-step decision utility on logged proposals.
[Sweep 1 replay](https://github.com/dowlingwong/Agent_paper_B/blob/7716cfce/docs/r1/reports/MAC_M3_DRYRUNS_20261104.md)

## Build verification

| Draft | Exit | Last main-text page | Total pages | Rebuilt PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `c15280eb4ffc0569134c15dafbbf535281fee27d850f3c356364530b230e67c6` |
| Gate-pass preview | 0 | 8 | 43 | `28080ff345ad28e13d1116deef6d65169c54590988b42acd7aacc4bdd10abd2b` |

Both README `latexmk` commands succeeded. The complete extracted text and every 100 dpi page render matched the
published pre-migration PDFs. Page 8 was inspected in both variants and contains the end of the main text and
the start of the references. Both logs have nine existing overfull box warnings and zero unresolved references,
citations or duplicate labels. The final build guard stopped at the unset gate outcome with exit 12.
The task tips above are ancestors of published main. The manuscript checkout is clean. D.3 effects and
intervals, the gate verdict and effects, full C1 audit rates, realised T1 scope, and evidence bindings
remain placeholders. The recorded reviews apply to the earlier deliveries. This round checked builds
and recorded status.

| Record verified | SHA-256 |
|---|---|
| Published claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Published frozen D.3 rev 4 | `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745` |
| Deepthought2 screening independent re-check | `6977921483faef926d210273c91b0619ed887b465c852ff70fbe4f63800c57a0` |
| Published TASL-7 E0 independent re-check | `f14321d3b389d7aecd20b3c33d56af2d8157f3cf8b4552fa00c6ff1c60a24d76` |
| Published expansion D6 source-to-copy review | `4b7ef4e818579b38e96aa1af84c4b9fe30f4700ca3be96cca1b9ae5bed9eb234` |

## Recent receipts and next checks

- **Screening is complete.** `compute/20261128-06`, deepthought2 checkout stamp
  `SMEAS_EVIDENCE_20261128T001405Z`, finished 10,164/10,164 runs with zero failures. Both decision tests were
  inconclusive and six nodes were not tested by design. There was no SHARED decision. The reviewed analysis
  routes D.3 step (8) on rev 4 under R1-D3-STEP8-HOLD, pending coordinator publication and routing. The accepted
  result tip is `52f43df7d1b10ee76dc64467d773c7765e27eb66` and the accepted review is
  `69399f09ded8037799018d2a1902c8892a2f2db7`. Check the published record before using the result in a manuscript task.
  [Compute round](https://github.com/dowlingwong/Agent_paper_B/blob/1e770abe76a4527e95dde9938505ae1430013998/reports/20261128-06-round-status.md)
- **D.3 batch preflight has no active job.** Under `compute/20261128-03`, ETP L40S and TOpAS A100 had
  `Start=false`. Prior IDs `760148`, `760149`, `760152`, `759624` and `759625` were removed, and
  `760065` was withdrawn. Check Compute for a startable slot, a new preflight ID and verified in-job inputs.
  The per-arm smoke and campaign launch authorizations are later checks. D.3b also needs frozen arms.
  [Published preflight](https://github.com/dowlingwong/Agent_paper_B/blob/7716cfce/docs/r1/reports/d3_preflight_20261128/D3_HTCONDOR_PREFLIGHT_20261128.md)
- **G.5 and the offline gate are pending.** Houseprice S14 run `tasl2-cpuset-mlgym_houseprice-20261128` passed
  with three seals. The expansion D6 copy `g1b-x-tasl-20261126-a` is published with 1,840 rows and accepted
  source-to-copy review. Local `20261128-02` owns the P11 engineering smoke path, followed by Compute host
  checks and tier-E review. Local `20261128-03` owns the expansion P10 table for the author's tail declarations.
  G.5 still needs its final binding, render, review and launch note. The gate awaits labels, T1 train/dev release,
  reviewed consumers and preregistration bindings, trained and calibrated frozen arms, proof checks and explicit
  test release. The full C1 and post-freeze tables likewise need their applicable releases.
  [P11 card](https://github.com/dowlingwong/Agent_paper_B/blob/a06dfc3f/tasks/local/20261128-02-g5-p11-engineering-smoke.md) ·
  [P10 card](https://github.com/dowlingwong/Agent_paper_B/blob/a06dfc3f/tasks/local/20261128-03-p10-expansion-kurtosis.md)
- **P.4 and Paper C.** TASL-7 same-code E0 `p5_e0_ref_20261128/e0e` (PID `2289540`) completed.
  Both slopes passed and RPS was 19.09% below Ada `p5_20261127_b/e0e`, outside the 10% tolerance.
  The reviewed STOP leaves the P.4 phase-1 note and A5 SFT waiting for the author's E0 disposition.
  Paper C E-INT `compute/20261127-28` still awaits the bound census authorization, eligible Ada lease and
  smoke receipt. Compute reported zero active project jobs at its round close.
  [E0 result](https://github.com/dowlingwong/Agent_paper_B/blob/7716cfce/docs/r1/reports/trackp_p5_tasl7_20261128/E0_TASL7_SAME_CODE_20261128.md)
- **Writer next action.** Check the queue for a result card and signed releases. Branch from
  published manuscript main, fill the supported estimates and intervals, rebuild both variants and obtain
  independent review. The coordinator publishes the reviewed manuscript and advances the research pin.

Decided alone to preserve the 15 modified paths in the assigned checkout. Each matches the published
pre-migration snapshot byte for byte. The linked Git directory refused the fetch write, so the fetch and
report used temporary writable Git metadata. The builds used a temporary checkout of the pinned manuscript.
Host status comes from Compute receipts. This round submitted zero jobs and opened zero sealed partitions.
