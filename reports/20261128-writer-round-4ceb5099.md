# Paper B Writer round — draft verification and Forest Cover addendum handoff

Writer is idle at research base `4ceb5099b65245f10b4c10eab22c7201325799c9` and queue
`3a2bdef8dda5846a736d9179ba50b66954e79969`. The incoming Writer report tip was
`268f45f0ae196df55215d740c4629871dc212632`. All four delivery tips below are
ancestors of the research base. The results-table item in runbook §3.4 awaits released
evidence and dispatch. [Writer queue](https://github.com/dowlingwong/Agent_paper_B/blob/3a2bdef8/STATE.md#writer)

| Published card | Delivery branch @ tip | Recorded independent review |
|---|---|---|
| `writer/20261126-01` with `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | Tier D re-check ACCEPT WITH MINOR, corrections applied. A separate verdict for the final title and trim is unrecorded. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | Tier S ACCEPT WITH MINOR, corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | Tier D re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | Tier D re-check ACCEPTED. |

The published restructure includes the title and eight-page trim and names `writer/20261126-02`
for the approved card-sharing, proposal-budget and stage-order changes. This report records
verification of the published manuscript and adds no unit for independent review.
[Original restructure delivery](20261126-01-manuscript-restructure.md)

## Question, measurement and claim

Which decisions help an automated search find a better configuration on the same budget?
In the sweep-1 replay, 3,274 of 4,999 proposals repeated a configuration already evaluated.
This measures how often proposals repeat and motivates testing the value of filtering them.
D.3 compares controllers on the same fresh instances, with up to 20 worker runs and 80
manager calls per campaign. Ten fresh audit seeds measure the improvement from each starting
configuration to its final configuration. A0R versus A0 measures what skipping duplicates and
detectable no-ops adds. A2 versus A0R measures what noise-aware decisions add with those filters
in place. A3 and A5 versus A2 measure what the learned forecasts add. Those claims await paired
estimates, intervals and the declared Holm decisions. The preregistered offline gate separately
tests whether forecasts improve one-step decisions on logged proposals.
[Published sweep-1 counts](https://github.com/dowlingwong/Agent_paper_B/blob/4ceb5099/docs/r1/reports/b2_audit_20261119/counts.json) · [Frozen D.3 revision 5](https://github.com/dowlingwong/Agent_paper_B/blob/4ceb5099/docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261128_R5.md)

## Draft verification

The standalone main and research manuscript pin both resolve to
`c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`. Both README builds ran from an archive of
that commit, with its timestamp as `SOURCE_DATE_EPOCH`.
[Published manuscript source](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)

| Preview | latexmk exit | Last main-text page | Total PDF pages | Local PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `97790aa66240bca932d5c9ca3bcdcce080fbdf663680db99e25dbc7ebff1d0b3` |
| Gate pass | 0 | 8 | 43 | `10614c5253899ac53bac456e48674023615d590f1ff380ccf32f02cc03f8d7fc` |

Ghostscript and LaTeX agree on the total page counts. Rendered pages 1 and 8 of each
draft and verified that the references start on page 8. Each log shows nine existing
overfull-box warnings, zero undefined citations or references, and zero multiply defined
labels. The `FinalPaper` guard exited 12 at the unset gate outcome. C1 rates, gate and
campaign estimates and intervals, realised T1 scope, and author wording remain placeholders.
The next assigned manuscript edit should cite the frozen revision 5 and digest in the
pre-declaration placeholder and update the accompanying revision references.

| Source at the research base | SHA-256 |
|---|---|
| PLAN containing §10 | `251cb8e4f68e13c14833e93d75b164663d459806f28dd2ded28ea1118407def0` |
| Claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Frozen D.3 revision 5 | `700d93cac277a23f527f20a49f8606987e63f615547b435cf924b2706ec778ad` |
| Sweep-1 counts | `568c44dd101d57b7efa3b6577a426e4a9dd7a270a6e69a5f7c6eada1e9cb5e85` |

## Job ledger and dependencies

Compute's 18:16 UTC sample found no Paper B job running or queued across TASL-2, TASL-7,
Ada and HTCondor. HTCondor held IDs `5045947.0`, `5045949.0` and `5045952.0` belong
to Paper A. Screening `SMEAS_EVIDENCE_20261128T001405Z` is complete (10,164/10,164 runs,
no SHARED decision nodes). The two exact-layout P7 runs `d3a-p7-exact-20261128-c` and
`d3a-p7-exact-20261128-d` are closed. Writer submitted zero jobs and opened zero sealed partitions.
[Compute ledger](https://github.com/dowlingwong/Agent_paper_B/blob/d48047c7/reports/20261128-39-round-status.md) · [Coordinator queue](https://github.com/dowlingwong/Agent_paper_B/blob/3a2bdef8/STATE.md)

| Lane | Status and next check |
|---|---|
| Primary G.5 | Author's clean-launch-base decision for `2178bc6e`, then coordinator publication and Compute's strict checks for `c3_t1_labels_20261128`. No job ID. |
| G.5 addenda 1–3 | Check signing and publication for clean bases `88edb84f` (Titanic), `4ee43037` (MetaMaze), and `e9441f03` (ETTh1), then the ledger for `c3_t1_labels_20261128_addendum_1`, `_2` and `_3`. No job IDs. |
| G.5 Forest Cover | Host checks are published via `942255a3`. Local delivered `local/20261128-16` at `9825ee84` with tier-E ACCEPTED at `8507f061`. The stock draft check waits for the coordinator to publish that review. Approved note publication precedes the clean-base follow-up for `c3_t1_labels_20261128_addendum_4`. No job ID. Forest Cover and ETTh1 are separate descriptive nodes under S9. |
| P.4 phase 1 | P5 timing passed. P3 awaits the author's project signature on the reviewed spec bytes at `befb58c8` with parent `0b465954`. Then Local fills P3 and the coordinator publishes. Check `trackp-p4-p1-20261122-a`. No training job ID. |
| D.3a and D.3b | D.3a production awaits the manifest, environment or image binding, endpoint-to-card proof, fresh run ID, P10/P11 review and author P9. D.3b awaits frozen arms and its own authorization. Batch preflight `760158.0` left the queue. Recheck 6 found no startable ETP L40S or TOpAS A100 and created no replacement. Compute follows `compute/20261128-21`; the TASL-2 D.3a route is independent of that pool watch. |
| Gate and Writer tables | Gate waits for G.5 completion, eligible T1 train/dev release, reviewed consumer and preregistration bindings, proof checks, frozen arms and explicit test release. Check for assigned result work with published C1, gate or D.3 evidence. Update the corresponding placeholders on a standalone task branch, rebuild both drafts and obtain independent review for coordinator publication. |

[Local addendum handoff](https://github.com/dowlingwong/Agent_paper_B/blob/eb59d13c/reports/20261128-16-g5-forestcover-addendum.md) · [Author decisions](https://github.com/dowlingwong/Agent_paper_B/blob/3a2bdef8/AUTHOR.md)

Decided alone to use writable temporary Git metadata after the assigned linked checkout denied the
`FETCH_HEAD` write, then build from an archive of the standalone manuscript pin. All 15 existing
modified paths in the assigned worktree match the published snapshot byte for byte. The original
worktree passed `git diff --check`.
