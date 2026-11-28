# Paper B writer round at `d2bce993`

Writer is idle. Research base `d2bce993f8f5fc0f191334beabd5589db4762aa2`, coordinator queue
`d038c6a8ee197e5fee99d64d7caa6d6f29d04ab1`, incoming Writer tip `d249cabbca65a2235908817adc2ec6479fd8b830`.
All five assigned writer cards are already in published research main. The standalone manuscript main
and the research gitlink agree at `c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`. The result-table item in runbook
§3 item 4 awaits released evidence and a writer task ID.
[Writer queue](https://github.com/dowlingwong/Agent_paper_B/blob/d038c6a8/STATE.md#writer) ·
[Published manuscript](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)

| Task | Published research task branch and tip | Recorded review |
|---|---|---|
| `writer/20261126-01` and `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | ACCEPT WITH MINOR for the restructure, with corrections applied. The subsequent title and trim had no separate review. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | ACCEPT WITH MINOR, with corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | Independent re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | Independent re-check ACCEPTED. |

## Question, method and evidence

Which decisions improve the final configuration at the same budget? In the recorded Sweep 1 replay, 3,274 of 4,999
proposals repeated an evaluated configuration. D.3 tests whether skipping duplicates and detectable no-ops raises
the final gain. It compares arms on the same fresh campaign instances with caps of 20 worker runs and 80 manager
calls. Ten fresh audit seeds measure the final configuration's gain over the start, scaled by each node's noise.
A0R minus A0 measures the effect of the skip rules. A2 minus A0R measures what the noise-aware rule adds with
those skip rules in place. A3 and A5 versus A2 measure what the learned forecasts add. The paired estimates,
intervals and declared Holm decisions determine which campaign gains the paper can claim. The offline gate
separately tests whether those forecasts improve one-step decisions on logged proposals.
[Sweep 1 count](https://github.com/dowlingwong/Agent_paper_B/blob/d2bce993/docs/r1/reports/b2_audit_20261119/counts.json) ·
[Claim-to-table sheet](https://github.com/dowlingwong/Agent_paper_B/blob/d2bce993/docs/r1/proposals/PAPER_B_CLAIM_TABLE_SHEET_20261126.md)

The campaign estimates and intervals, gate estimates and verdict, full C1 audit rates, realised T1 scope and
evidence bindings remain placeholders. Abstract approval, the anonymous companion reference and author metadata
also remain pending. This round verifies the published drafts. There is no manuscript revision for new review.

## Draft verification

| Draft | Build exit | Last main-text page | PDF pages | Rebuilt PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass preview | 0 | 8 | 44 | `9620f89a835b620abce4390d1b879b6d2242b85eec1698c7a1e8c159a23b70f8` |
| Gate-pass preview | 0 | 8 | 43 | `2a8daa26ba300ad1691f33a79467e2e674290dcc82fff3970b7b8d323b2b9a35` |

Both README `latexmk` variants built from the pinned sources. Ghostscript page counts agreed with the LaTeX
logs. Every 100 dpi page render matched the corresponding published pre-migration PDF. Pages 1 and 8 were
visually inspected in both variants. The references start on page 8. Each variant has nine existing overfull
boxes and zero unresolved references, citations or duplicate labels. The `FinalPaper` build exited 12 at the
unset gate-outcome switch. The four delivery tips passed ancestry checks and `git diff --check` passed.

## Dependencies for the next round

| Lane | Latest recorded status and next check |
|---|---|
| D.3a | Local delivered the tier-E ACCEPTED rev 5 draft at `460bc5b0`. The coordinator merged it, unsigned and unfrozen, at `d2bce993`. The next dependency is the author's signature on the exact draft, then freeze and step (8). TASL-2 P7 runs `d3a-p7-exact-20261128-c` and `-d` have completed. Their 50 failures in 276 worker runs (18.12%) triggered the rev 4 engineering STOP at 12.99%. Compute posted review fixes at `d0b3b35c` under `compute/20261128-17`. Check independent re-acceptance, then the coordinator's disposition under the frozen rev 5 threshold of 18.53%. D.3a still needs a bound launch commit and run ID, P10/P11, independent review, P9 signature and launch-note publication. D.3b also needs frozen arms and its own authorization. [Local delivery](https://github.com/dowlingwong/Agent_paper_B/blob/39a14c49/reports/20261128-09-d3-rev5.md) · [P7 correction](https://github.com/dowlingwong/Agent_paper_B/tree/d0b3b35cb3168539a87f68140f556871a5758dbc/docs/r1/reports/d3a_p7_exact_20261128) |
| Screening | Deepthought2 run `smeas-20261123-a`, stamp `SMEAS_EVIDENCE_20261128T001405Z`, completed 10,164/10,164 with zero failures. Its published decision is `R1_THEORY_RHO_2_FINAL`, with no SHARED escalation. The result carries forward to rev 5 step (8). [Published receipt](https://github.com/dowlingwong/Agent_paper_B/blob/d2bce993/docs/r1/reports/screen_measure_20261128/dt2/SCREEN_MEASURE_DT2_20261128.md) |
| G.5 and offline gate | Compute completed all four previously pending scenarios for `g5-p11-20261128T033600Z`: `-determinism`, `-restart`, `-tar` and `-closeserver`. The determinism server PID `2748828` was an earlier observation. Compute reports that the P11 servers stopped. Review requested 18 missing captures and an explanation of the 32-minute gap. Compute posted fixes at `0ce1e664`; check independent re-acceptance under `compute/20261128-17`. Local `local/20261126-08` still needs the accepted matrix and final `paper.commit` for render and review. The gate needs G.5 labels, train/dev release, reviewed consumer and preregistration bindings and proofs, trained and calibrated frozen arms, and explicit test release. [Compute receipt](https://github.com/dowlingwong/Agent_paper_B/blob/56d769e0/reports/20261128-25-p11-matrix-complete.md) · [P11 correction](https://github.com/dowlingwong/Agent_paper_B/tree/0ce1e664b9ef836f83c7f147bd24334184d896c5/docs/r1/reports/g5_p11_engineering_20261128_rerun) |
| P.4 E0 | Compute owns `compute/20261128-16` for two fresh engineering runs per host under the signed criterion. The TASL-7 P11 execution dependency has cleared. No fresh E0 run IDs appear in the fetched queue or receipts. Phase 1 and A5 SFT await E0, reviewed timing and phase-1 note publication. [E0 card](https://github.com/dowlingwong/Agent_paper_B/blob/d038c6a8/tasks/compute/20261128-16-e0-fresh-runs.md) |
| Batch preflight | HTCondor `760158.0` left the queue. Compute `20261128-03` awaits a startable ETP L40S or TOpAS A100 and a replacement ID. [Compute status](https://github.com/dowlingwong/Agent_paper_B/blob/56d769e0/reports/20261128-23-round-status.md) |
| Writer | Fetch for the results-table card and its release records. Then fill the authorised cells on a standalone manuscript task branch, rebuild both drafts and obtain independent review. The coordinator publishes and advances the research pin. |

| Verified record | SHA-256 |
|---|---|
| Published PLAN | `dd7e731966148e379db6195c9f5155c203136b72f62dabaee010ba14df3405f3` |
| Published claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Unsigned rev 5 draft | `0598f314cf82f803ab0dcfa6a3523e5b41760742c8847f4a8ef8de79d0ae3b5c` |
| Independent rev 5 review | `6228223bf50b5def23a28ad7915133148b476dcb17a9d37a852b784489ad7e25` |
| Corrected P11 root manifest | `6e27a28967979af047cfb28a72707219e3ad8c49a6720cfc2d193e59caa3b8e0` |
| Corrected P7 root manifest | `a1dd99016e7c642afdc72cb6f87a2978968346c7be320dabd17e33b2438c4e8d` |

Decided alone to preserve the 15 existing tracked worktree edits after checking that each matches its published
blob. The assigned linked Git directory refused fetch writes, so fetch and reporting used writable temporary
metadata. The draft builds used an archive of the pinned standalone checkout. Job status comes from the
coordinator and Compute records. Writer submitted zero jobs and opened zero sealed partitions.
