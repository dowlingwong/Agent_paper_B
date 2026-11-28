# Paper B Writer round — drafts verified and D.3a handoff tracked

Research base `c3a484055f717865e4e6826833e405af41771013`. Coordinator queue
`b3d229b94174907aefc2ed08e5db9c87afe033ea`. Incoming Writer report tip
`c6cb9dfa66ddfa6600b21e13f5139e4111e839c2`. Writer is idle. Runbook §3.4 is
pending released evidence and a results-table card. The queue update dispatches
`compute/20261128-22` and leaves the Writer queue unchanged.
[Writer queue](https://github.com/dowlingwong/Agent_paper_B/blob/b3d229b9/STATE.md#writer)

| Task | Published delivery branch and tip | Recorded review |
|---|---|---|
| `writer/20261126-01` with `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` at `e360d425752334c56cfaba8ff9499315ca15ea8e` | Tier D re-check ACCEPT WITH MINOR, corrections applied. A separate verdict for the title and eight-page trim is unrecorded. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` at `acf7d37be0cdddc29f157c311b337807f9cbea0a` | Tier S ACCEPT WITH MINOR, corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` at `e8dc1e36a09b61e9410132f23551064f1661e769` | Tier D re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` at `e3af70a495816c3d107f013b9ee2c17593600bae` | Tier D re-check ACCEPTED. |

All four delivery tips are ancestors of the research base. The restructure includes
the shared-card, proposal-budget and step-order rules from `writer/20261126-02`.
The 15 modified paths in the assigned worktree match the published research tree
byte for byte, and `git diff --check` passed. This round verified published material.
[Restructure delivery](20261126-01-manuscript-restructure.md)

## Question, method, measured result and claim

Which decisions help an automated search improve its final configuration at the
same run and manager-call budgets? In the published sweep-1 replay, 3,274 of 4,999
proposals repeated a configuration already evaluated. That count shows how often
the loop revisited a configuration and motivates testing whether skipping repeated
proposals helps. D.3 compares controllers on the same fresh instances with 20 worker
runs and up to 80 manager calls per campaign. Ten fresh seeds measure how far each
campaign's final configuration improved over its starting configuration. A0R versus
A0 measures the effect of skipping duplicates and detectable no-ops. A2 versus A0R
measures what the noise-aware one-step rule adds when those filters are in place.
A3 and A5 versus A2 measure what learned forecasts add. Campaign claims await
the paired effects, 95% intervals and declared Holm decisions. The preregistered
offline gate separately tests whether the forecasts improve one-step decisions on
logged proposals.
[Sweep-1 counts](https://github.com/dowlingwong/Agent_paper_B/blob/c3a48405/docs/r1/reports/b2_audit_20261119/counts.json) · [Frozen D.3 revision 5](https://github.com/dowlingwong/Agent_paper_B/blob/c3a48405/docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261128_R5.md)

## Draft builds

Standalone manuscript `main` and the research pin both resolve to
`c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`. Both README commands ran from a
clean checkout with the commit timestamp set as `SOURCE_DATE_EPOCH`.
[Published manuscript](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)

| Preview | latexmk exit | Last main-text page | Total pages | Local PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `f75793918397cb6ffed6a257a96c9d24588a3e987fa3b809ca6a7581eebc7e40` |
| Gate pass | 0 | 8 | 43 | `418c310c77d546443db171b94a8a9dc863098ede0a0c93a49a68eaf11967e9fe` |

Ghostscript and LaTeX agreed on page counts. Pages 1 and 8 were rendered and
inspected in both variants. References start on page 8. Each log reports nine
existing overfull boxes, with zero undefined references, undefined citations or
multiply defined labels. `FinalPaper` exited 12 at the unset gate outcome. The
pending macros cover C1 rates, the offline gate outcome and estimates, closed-loop
effects and intervals, realised T1 scope and author wording. The D.3 citation
and related appendix references still await incorporation of frozen revision 5
in the next assigned manuscript edit.

| Source at research base | SHA-256 |
|---|---|
| PLAN containing §10 | `251cb8e4f68e13c14833e93d75b164663d459806f28dd2ded28ea1118407def0` |
| Claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Frozen D.3 revision 5 | `700d93cac277a23f527f20a49f8606987e63f615547b435cf924b2706ec778ad` |
| Published sweep-1 counts | `568c44dd101d57b7efa3b6577a426e4a9dd7a270a6e69a5f7c6eada1e9cb5e85` |

## Active jobs and next checks

The latest Compute sample at 18:49–18:52 UTC recorded zero active Paper B jobs
on TASL-2, TASL-7, Ada, deepthought, deepthought2 and HTCondor. Held jobs
`5045947.0`, `5045949.0` and `5045952.0` belong to Paper A. Screening run
`SMEAS_EVIDENCE_20261128T001405Z` is complete at 10,164 of 10,164 runs.
The two exact-runtime P7 smoke runs `d3a-p7-exact-20261128-c` and
`d3a-p7-exact-20261128-d` are closed.
[Compute ledger](https://github.com/dowlingwong/Agent_paper_B/blob/1aa500ba/reports/20261128-40-round-status.md)

| Lane | Current dependency and next owner |
|---|---|
| D.3a production route | `compute/20261128-22` is dispatched for engineering checks on TASL-2. Compute supplies the reviewed manifest, environment or image binding, canonical endpoint-to-lease UUID proof, resource basis and unused run ID. Local binds and rechecks P10/P11 at that commit before author P9. No production job ID is recorded. |
| D.3 batch and D.3b | HTCondor `760158.0` left the queue. `compute/20261128-21` records the next exact-request pool check at or after 21:16:04 UTC. D.3b awaits frozen arms and its own authorization. |
| G.5 and addenda 1–4 | The published notes await the author's launch-base decision and the coordinator's publication disposition. Accepted launch-base candidates are `2178bc6e`, `88edb84f`, `4ee43037`, `e9441f03` and `f96069d0`. Compute then verifies bindings, previous IDs and leases under `compute/20261128-18`. No campaign job IDs are recorded. |
| P.4 phase 1 | P5 timing passed. P3 awaits the author's project signature on the exact spec bytes at `befb58c8` on parent `0b465954`. Local fills P3 before coordinator publication. No training job ID is recorded. |
| Offline gate and Writer | The gate awaits G.5 labels, eligible train/dev release, reviewed consumer and preregistration bindings, proof checks, frozen arms and explicit test release. Writer checks for a results card and the corresponding published C1, gate or audited D.3 evidence. When dispatched, fill the corresponding placeholders on a standalone task branch, build both drafts and obtain independent review for coordinator publication. |

[D.3a dispatch](https://github.com/dowlingwong/Agent_paper_B/blob/b3d229b9/tasks/compute/20261128-22-d3a-production-route.md) · [Local handoff](https://github.com/dowlingwong/Agent_paper_B/blob/f37ee571/reports/20261128-local-round-b3d229b9.md) · [Pending author decisions](https://github.com/dowlingwong/Agent_paper_B/blob/b3d229b9/AUTHOR.md)

Decided alone to use temporary writable Git metadata after the assigned worktree's
shared `FETCH_HEAD` write failed, and to build from a temporary clone of the
published manuscript pin. This was a report-only round. Writer made zero
manuscript edits, submitted zero jobs and opened zero sealed partitions.
