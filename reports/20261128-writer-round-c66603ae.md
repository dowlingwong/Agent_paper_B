# Paper B Writer round — drafts verified and results pending

Writer is idle at research base `c66603ae8ac5f176ffe6a3b649cdb8b3d87d51de`.
The coordinator queue at `7d55eda6bc309db0c10f062ce45afe09988111da` has no
runnable Writer card. Runbook §3.4 awaits released results and dispatch.
This report starts from `coord/writer` at `f231cc36e47399aa7fa447b07f45aa46fe923a9f`.
[Writer queue](https://github.com/dowlingwong/Agent_paper_B/blob/7d55eda6/STATE.md#writer)

| Task | Published delivery branch and exact tip | Recorded review |
|---|---|---|
| `writer/20261126-01` and `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` at `e360d425752334c56cfaba8ff9499315ca15ea8e` | Tier D re-check ACCEPT WITH MINOR, corrections applied. The final title and trim have no separate review verdict. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` at `acf7d37be0cdddc29f157c311b337807f9cbea0a` | Tier S ACCEPT WITH MINOR, corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` at `e8dc1e36a09b61e9410132f23551064f1661e769` | Tier D re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` at `e3af70a495816c3d107f013b9ee2c17593600bae` | Tier D re-check ACCEPTED. |

All four tips are ancestors of the research base. The restructure includes the
date-rule, shared-card and proposal-budget changes from `writer/20261126-02`.
The 15 modified files in the assigned checkout match the published research
tree byte for byte, and `git diff --check` passed. This round verified the
published pin and produced a status report. The review verdicts above apply
to the previous manuscript deliveries.
[Restructure delivery](20261126-01-manuscript-restructure.md)

## Question, method, measured result and claim

Which control decisions improve the final configuration at the same run and
manager-call budgets? In the published sweep-1 replay, 3,274 of 4,999 proposals
repeated a configuration already evaluated. That count measures how often the
loop revisited a configuration and motivates testing whether skipping repeats
helps. D.3 compares controllers on the same fresh instances with 20 worker
runs and up to 80 manager calls per campaign. An audit on ten fresh seeds
measures how far the final configuration improved over the starting
configuration. A0R versus A0 measures what skipping duplicates and detectable
no-ops buys under the default keep rule. A2 versus A0R measures what the
noise-aware rule adds with the same filters. A3 and A5 versus A2 measure what
learned forecasts add. Campaign claims await the paired effects, 95% intervals
and declared Holm decisions. The preregistered offline gate answers the
one-step question using logged proposals.
[Sweep-1 replay counts](https://github.com/dowlingwong/Agent_paper_B/blob/c66603ae/docs/r1/reports/b2_audit_20261119/counts.json) · [Frozen D.3 revision 5](https://github.com/dowlingwong/Agent_paper_B/blob/c66603ae/docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261128_R5.md)

## Draft builds

Standalone manuscript `main` and the research pin both resolve to
`c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`. The README commands ran from a
clean checkout with the commit timestamp set as `SOURCE_DATE_EPOCH`.
[Published manuscript](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)

| Preview | latexmk exit | Last main-text page | Total pages | Local PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `f60a042c0091f0fa3a2f83d65c8b058696e9af3deacf0bd3d15d008552baf637` |
| Gate pass | 0 | 8 | 43 | `b727284e57c0807620223b3145c2c901601928f955ba0617e40214836809a3df` |

Ghostscript and LaTeX agreed on page counts. Visual checks covered pages 1
and 8 in both previews. References start on page 8. Each log has nine
overfull boxes and zero undefined references, undefined citations or
multiply defined labels. `FinalPaper` exited 12 at the unset gate outcome.
Placeholders remain for C1 rates, the offline gate outcome and estimates,
D.3 effects and intervals, realised T1 scope and author wording. The next
assigned manuscript edit also needs to update the appendix's pre-declaration
citation from revision 4 to the applicable frozen revision.

| Published source | SHA-256 |
|---|---|
| PLAN containing §10 | `251cb8e4f68e13c14833e93d75b164663d459806f28dd2ded28ea1118407def0` |
| Claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Frozen D.3 revision 5 | `700d93cac277a23f527f20a49f8606987e63f615547b435cf924b2706ec778ad` |
| Sweep-1 replay counts | `568c44dd101d57b7efa3b6577a426e4a9dd7a270a6e69a5f7c6eada1e9cb5e85` |
| D.3a route record SHA256SUMS | `9007304fe54bdd25d6a1dc5d5fd1db5febe176218683d9867e64210c6ba7c6ff` |

## Active jobs and next checks

Compute's last recorded check at 19:27–19:29 UTC found zero active Paper B
jobs on TASL-2, TASL-7 and deepthought. The HTCondor submitter queue was
empty at 19:28 UTC. Ada was last reachable at 18:49 UTC. Screening
`SMEAS_EVIDENCE_20261128T001405Z` finished 10,164 of 10,164 runs. The P7
runs `d3a-p7-exact-20261128-c` and `d3a-p7-exact-20261128-d` are closed.
The D.3a production endpoint probe, PID 1673663, ended and released its
leases. Writer has zero active jobs.
[Compute report](https://github.com/dowlingwong/Agent_paper_B/blob/d76e71cd/reports/20261128-41-d3a-production-route.md) · [Local STOP](https://github.com/dowlingwong/Agent_paper_B/blob/1a6a2cf5/reports/20261128-08-d3a-production-binding-stop.md)

| Lane | Dependency and next owner |
|---|---|
| D.3a production | The tier-E route record was accepted with minors applied and published at `c66603ae`. Run ID `d3a-prod-20261128-a` is allocated and unused. The author has the revision 6 environment decision because the direct TASL-2 route differs from frozen revision 5. Compute owns the per-chunk listener, model and lease checks in `compute/20261128-23`. Local then binds the approved route and rechecks P10/P11 at the exact launch commit ahead of P9 and publication. |
| D.3 batch and D.3b | HTCondor `760158.0` left the queue. Compute `20261128-21` records the next exact-request pool check at or after 21:16:04 UTC. D.3b awaits frozen arms and its own authorization. |
| G.5 primary and addenda 1–4 | The author launch-base decision and coordinator publication are pending for `2178bc6e`, `88edb84f`, `4ee43037`, `e9441f03` and `f96069d0`. Compute `20261128-18` then rechecks the bound checkout, previous attempt IDs and leases. Zero campaign job IDs are recorded. |
| P.4 phase 1 | P5 timing passed. P3 awaits the author's project signature on the reviewed spec bytes at `befb58c8` on parent `0b465954`. Local fills P3 before coordinator publication. Zero training job IDs are recorded. |
| Offline gate and Writer | The gate awaits G.5 labels, eligible train/dev release, reviewed consumer and preregistration bindings, proof checks, frozen arms and explicit test release. Writer checks for C1, gate or audited D.3 releases and a results-table card. Upon dispatch, fill the corresponding placeholders on a standalone task branch, build both drafts and obtain the card's review for coordinator publication. |

[D.3a template card](https://github.com/dowlingwong/Agent_paper_B/blob/7d55eda6/tasks/compute/20261128-23-d3a-template-checks.md) · [Pending author decisions](https://github.com/dowlingwong/Agent_paper_B/blob/7d55eda6/AUTHOR.md)

Decided alone to use temporary writable Git metadata after the assigned
worktree's shared FETCH_HEAD write failed. The builds used a scratch clone
of the published manuscript pin. The live `paperb-writer` launcher is
configured for another round after its 30-minute idle interval. Writer
made zero manuscript edits, submitted zero jobs and opened zero sealed
partitions.
