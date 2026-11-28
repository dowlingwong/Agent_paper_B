# Paper B Writer round — draft verification and evidence dependencies

Writer is idle. At research base `7cd65cfa37cc1ece18d773b662a3f9b8c45917ce`
and queue tip `52fb689281a135032455bca3d73198759d52c1d0`, the five Writer cards are
published. The results-table task in runbook §3.4 awaits released evidence and dispatch.
Incoming Writer tip was `14ca8cf6279aed31140247cbc76085dbbf2e6e2d`.
[Writer queue](https://github.com/dowlingwong/Agent_paper_B/blob/52fb6892/STATE.md#writer)

| Completed task | Published task branch and tip | Recorded review |
|---|---|---|
| `writer/20261126-01` and `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | Tier D independent re-check ACCEPT WITH MINOR. Corrections applied. A separate review of the final title and trim is unrecorded. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | Tier S independent ACCEPT WITH MINOR. Corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | Tier D independent re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | Tier D independent re-check ACCEPTED. |

All four task tips are ancestors of the research base. The restructure incorporated card
`writer/20261126-02` on card sharing, proposal budgets and the order of research stages.
This round had no new manuscript unit, so an independent review verdict does not apply.
[Original restructure report](20261126-01-manuscript-restructure.md)

## Question, method and evidence

Which decisions help an automated search finish with a better configuration on the same budget?
Sweep 1 replay counted 3,274 repeated configurations among 4,999 proposals. This measures how
common repetition was and explains why filtering repeats is worth testing. D.3 compares controllers
on the same fresh instances with caps of 20 worker runs and 80 manager calls per campaign. Ten fresh
seeds measure the change from the starting to the final configuration. A0R versus A0 measures the
effect of skipping repeats and detectable no-ops. A2 versus A0R measures what noise-aware decisions
add with those filters in place. A3 and A5 versus A2 measure what the forecast-based controllers add.
Each claim of improvement awaits its paired estimate, interval and declared Holm decision. The
offline gate separately measures whether forecasts improve individual decisions on logged proposals.
[Published sweep counts](https://github.com/dowlingwong/Agent_paper_B/blob/7cd65cfa/docs/r1/reports/b2_audit_20261119/counts.json) · [Signed D.3 revision 5](https://github.com/dowlingwong/Agent_paper_B/blob/7cd65cfa/docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261128_R5.md)

## Draft builds

The published manuscript pin and standalone main both resolve to
`c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`. Rebuilt this revision with the commit time as
`SOURCE_DATE_EPOCH`. The two requested previews and the extra statistical STOP preview passed.
[Standalone manuscript](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)

| Preview | latexmk exit | Last main-text page | Total pages | Rebuilt PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `99ef69f333f82b434dcc7a436285c85eb2eefa7cd6e230b709ba052c4950589b` |
| Gate pass | 0 | 8 | 43 | `abded004c2f45be2a131b11bddbd94dad9f0c6b13a51e92adce1de53834a138d` |
| Statistical gate STOP | 0 | 8 | 38 | `7512baa9e174c47ae4c4771dc2b6bb3af4b81d2daccfb11f16fe8513984aa047` |

Ghostscript and LaTeX agree on page counts. Visually checked pages 1 and 8 of all three PDFs.
References start on page 8. Each draft log has nine overfull box warnings, zero undefined
references or citations, and zero duplicate labels. `FinalPaper` exited 12 at the unset
gate-outcome guard. Gate and D.3 effects and intervals, C1 rates, realised T1 scope and author
wording remain placeholders. The manuscript's pending reference to D.3 revision 4 needs to cite
frozen revision 5 and its digest on the next assigned manuscript update.

## Job status and next checks

Compute's 15:00 UTC receipt found TASL-2 idle and zero Paper B jobs queued or running in HTCondor.
TASL-7 and Ada were outside that sample. Writer submitted zero jobs and read zero sealed partitions.
[Compute receipt](https://github.com/dowlingwong/Agent_paper_B/blob/b4d2a588/reports/20261128-36-round-status.md)

| Lane | Pending dependency and identifier to check |
|---|---|
| Primary G.5 | Author decision on the clean launch base, then coordinator publication. Check `2178bc6e` and run ID `c3_t1_labels_20261128`. No scheduler job ID recorded. |
| G.5 Titanic, MetaMaze and ETTh1 | The three addenda are published. Check the signing and publication disposition for clean launch bases `88edb84f`, `4ee43037` and `e9441f03`, then the ledger for `c3_t1_labels_20261128_addendum_1`, `_2` and `_3`. No scheduler job IDs recorded. ETTh1 is part of the separate 1GC descriptive output. |
| G.5 Forest Cover | Compute owns C1–7 on TASL-2 at harness `3f7b09febf401a83f3aa881f00eecdd032024416` under `compute/20261128-20`. Check its ledger and the reviewed receipt before Local binds the addendum. No host-check or campaign job ID recorded. |
| D.3 | Engineering runs `d3a-p7-exact-20261128-c` and `-d` are complete. D.3a production awaits runtime and deployment bindings, a fresh run ID, release checks, review and author P9. D.3b awaits frozen arms and its own authorisation. Preflight `760158.0` left the HTCondor queue. ETP L40S and TOpAS A100 last advertised `Start=false`. |
| P.4 phase 1 | P5 timing passed. Check author P3 signature over the reviewed spec bytes at `befb58c8`, Local's final review, coordinator publication and ledger for `trackp-p4-p1-20261122-a`. No training job ID recorded. |
| Offline gate and Writer results | Check G.5 completion, eligible T1 train/dev release, reviewed consumer and preregistration bindings, proof checks, arms freeze and explicit test release. Take the results-table card once dispatched with released evidence. |

[Local launch and Forest Cover handoff](https://github.com/dowlingwong/Agent_paper_B/blob/a3994698/reports/20261128-local-round-forestcover-reconcile.md) · [Author decisions](https://github.com/dowlingwong/Agent_paper_B/blob/52fb6892/AUTHOR.md)

| Verified source | SHA-256 |
|---|---|
| PLAN containing §10 | `251cb8e4f68e13c14833e93d75b164663d459806f28dd2ded28ea1118407def0` |
| Claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Frozen D.3 revision 5 | `700d93cac277a23f527f20a49f8606987e63f615547b435cf924b2706ec778ad` |
| Published ETTh1 addendum | `903eb07a42affdd6f660847388ef3b318da3b50e62d0aed4a4ce8cfe05e1093b` |

Decided alone to fetch via temporary Git metadata after the assigned worktree's linked
`FETCH_HEAD` write failed, and to verify the statistical STOP preview in addition to the two
requested builds. All 15 existing modified paths in the assigned worktree match the published
snapshot byte for byte and were preserved. `git diff --check` passed. This round changes only
this report. Future manuscript changes go on a standalone task branch for independent review
and coordinator publication.
