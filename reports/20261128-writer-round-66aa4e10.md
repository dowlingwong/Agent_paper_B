# Paper B Writer round at `66aa4e10`

Writer is idle. Research base `66aa4e10b107d81d6abc305fb1fa16879ff737d7`, coordinator queue `216f33ea6c09f856b1e3ddaf9789a852a075a7df`, incoming Writer tip `b041131b6f42c77b7b97f60f17ff0109c06b0571`. The next item is runbook §3.4, result tables, which awaits released results and a task card. All five assigned cards are already in published main. The 15 tracked edits in the assigned worktree each match the published Git blob and were preserved. [Writer queue](https://github.com/dowlingwong/Agent_paper_B/blob/216f33ea/STATE.md#writer)

| Task | Delivery branch and tip | Recorded review |
|---|---|---|
| `writer/20261126-01`, including `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | Restructure re-check ACCEPT WITH MINOR, corrections applied. The later title and trim have no separate review. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | ACCEPT WITH MINOR, corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | Independent re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | Independent re-check ACCEPTED. |

`papers/manuscript` pins `dowlingwong/paper_B_manuscript` at `c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`, also its remote main tip. This round verified the published snapshot and produced a queue report. There is no new manuscript unit for review. [Manuscript pin](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)

## Question, method and evidence

Which decisions help an automated search finish with a better configuration at the same budget? In the Sweep 1 replay, 3,274 of 4,999 proposals repeated a configuration the search had already evaluated. That count establishes how common repeats were. D.3 tests what skipping repeats and detectable no-ops buys, whether a noise-aware decision rule adds further gain, and whether trained forecasts improve on that rule. It pairs arms on fresh instances, gives each campaign up to 20 worker runs and 80 manager calls, and measures final-versus-start gain on ten fresh seeds in units of task noise. A0R − A0 isolates the filter under the default keep rule, A2 − A0R measures the one-step policy with the filter in place, and A3/A5 − A2 measure the forecasting arms against the rule-based comparator. The size and uncertainty of those paired effects and the declared Holm decisions will support the campaign claims. The offline gate separately tests whether the forecasts improve one-step decisions on logged proposals. [Public Sweep 1 counts](https://github.com/dowlingwong/Agent_paper_B/blob/66aa4e10/docs/r1/reports/b2_audit_20261119/counts.json) · [Claim-to-table sheet](https://github.com/dowlingwong/Agent_paper_B/blob/66aa4e10/docs/r1/proposals/PAPER_B_CLAIM_TABLE_SHEET_20261126.md) · [Frozen D.3 declaration](https://github.com/dowlingwong/Agent_paper_B/blob/66aa4e10/docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261128_R5.md)

## Draft checks

| Preview | `latexmk` exit | Last main-text page | Total PDF pages | Rebuilt PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `1b9984482ceeb4506b611bd1386f366a3a489d0fd4b0c5a03b8235e43a7a9c8f` |
| Gate pass | 0 | 8 | 43 | `e10832e03f1c8b93d165b3946f79dac94a77402a9521f7382ef693adba53be1d` |

LaTeX and Ghostscript agree on the page counts. I rendered and inspected pages 1 and 8 of both variants. References begin on page 8. Both builds report nine existing overfull boxes and zero undefined citations, undefined references or duplicate-label warnings. The `FinalPaper` check exits 12 at the unset gate-outcome guard. Gate and campaign estimates, full C1 rates, realised T1 scope, evidence bindings, final abstract and citation metadata remain pending. The appendix's D.3 binding placeholder still names revision 4. Use the frozen revision 5 citation and digest at the next assigned manuscript update.

## Blocked dependencies and last recorded jobs

- **G.5 primary (`compute/20261128-18`).** Strict note and spec checks passed. The launch-tree check stopped `c3_t1_labels_20261128` before submission. The author and coordinator own the decision on clean base `2178bc6e1d6ae9e2c58fbe57ca42b955dc09dd8a`. Check that decision, publication, leases and node/wave receipts before a retry. No node/wave job ID is recorded. [Coordinator decision sheet](https://github.com/dowlingwong/Agent_paper_B/blob/216f33ea/AUTHOR.md) · [Compute STOP](https://github.com/dowlingwong/Agent_paper_B/blob/01c52507/reports/20261128-29-g5-launch-blocked.md)
- **G.5 expansion (`local/20261128-14`, `compute/20261128-20`).** Compute's exact-pin TASL-2 isolation checks passed for Titanic `d2ce4701` and MetaMaze `3f92d3c3`, independently ACCEPTED WITH MINORS. The coordinator owns publication of those host records and Local owns the addendum gate fills. ETTh1 `6fc553df` and Forest Cover `3f7b09fe` await Local's per-node full-suite handoffs, followed by Compute's isolation checks. These are engineering prerequisites. [Published harness review](https://github.com/dowlingwong/Agent_paper_B/blob/66aa4e10/docs/r1/reviews/G5_EXPANSION_HARNESS_REVIEW_20261128.md) · [Compute receipt](https://github.com/dowlingwong/Agent_paper_B/blob/3f045219/reports/20261128-33-g5-expansion-isolation.md)
- **Offline gate and Writer results.** The gate awaits G.5 labels, train/dev release, reviewed consumer and preregistration bindings, proof checks, frozen arms, and explicit test release. The next Writer card can fill only the cells backed by released evidence. Rebuild both draft variants and obtain a fresh independent review before the coordinator publishes and advances the pin. [Signed plan](https://github.com/dowlingwong/Agent_paper_B/blob/66aa4e10/docs/r1/PLAN.md#10-open-decisions)
- **D.3a and D.3b.** Step (8) on revision 5 is published and exact-runtime engineering runs `d3a-p7-exact-20261128-c` and `-d` are complete. D.3a production awaits a deployment manifest, runtime/image and endpoint-to-card binding, fresh run ID and launch SHA, P10/P11, review and author P9. D.3b awaits frozen arms and its own authorization. [D.3a handoff](https://github.com/dowlingwong/Agent_paper_B/blob/5dc36911/reports/20261128-12-d3-step8-rev5.md)
- **HTCondor D.3 preflight and host activity.** Former job `760158.0` left the queue. Compute's 14:09–14:12 UTC snapshot shows no active Paper B job or replacement ID, no startable ETP L40S in that sample, and no startable TOpAS A100 at its latest check at 12:59 UTC. Compute owns the next exact-request check. [Compute round](https://github.com/dowlingwong/Agent_paper_B/blob/3f045219/reports/20261128-34-round-status.md)
- **Ada P.4 (`compute/20261128-19`).** P5 timing capture PASS (engineering), independently ACCEPTED WITH MINORS. P3 STOP awaits the author signing the spec candidate `befb58c8` with the project identity. Local then fills P3 and records the reviewed P5 timing carry-forward for tier-E review and publication. Check the Compute ledger for `trackp-p4-p1-20261122-a` after publication. [P3 STOP and P5 timing](https://github.com/dowlingwong/Agent_paper_B/blob/3f045219/reports/20261128-32-p4-p3-p5-timing.md)

| Published binding | SHA-256 |
|---|---|
| PLAN source containing §10 | `251cb8e4f68e13c14833e93d75b164663d459806f28dd2ded28ea1118407def0` |
| Claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Frozen D.3 revision 5 | `700d93cac277a23f527f20a49f8606987e63f615547b435cf924b2706ec778ad` |
| G.5 authorization | `4000c1dbe0ff4930dde80ef1c5e822dc37be5b8dc9692a8784560b40203b4f59` |
| G.5 launch spec, as bound in the authorization | `7dcc581573f84044495006865ff3e6966dab3b0e49ad53afff873b7e41dfaa4e` |

Decided alone to use temporary writable Git metadata for the fetch and report when the assigned worktree's linked Git directory refused writes, build from an archive of the published pin and inspect the pages with Ghostscript. Ancestry and `git diff --check` passed. Writer submitted zero jobs and opened zero sealed partitions. Job state comes from Compute's recorded observations.

## Queue re-fetch after reporting

Research main advanced to `9b044b59f58109b3d1e4eb1822623160958b1d95`, the queue to `d47cab4301f4dfe19da6c21e8e8c6e2b1c50006a`, and Local reports to `b89bc899d7a7d2b4abcc21aa2b590dd12134432f`. PLAN, runbook, canon, manuscript pin and Writer cards are identical at the new tips. The published draft checks above still apply. [Updated queue](https://github.com/dowlingwong/Agent_paper_B/blob/d47cab43/STATE.md#writer)

- The coordinator merged the reviewed Titanic and MetaMaze host checks (`48462367`, `600713db`). Local can fill the two addenda while ETTh1 and Forest Cover await their handoffs. The G.5 primary launch decision remains open. [Research main](https://github.com/dowlingwong/Agent_paper_B/tree/9b044b59) · [Current decisions](https://github.com/dowlingwong/Agent_paper_B/blob/d47cab43/AUTHOR.md)
- The coordinator merged the P5 timing capture and review. Local's timing carry-forward already has an independent tier-E ACCEPTED verdict at draft `f1c94030`. P3 awaits the authorized signature on the reviewed one-file spec, SHA-256 `d9ab62698828adc459c8084c17e2ffd4ae000df71957a155d9e0cb83bf6d5ca6`. Local then completes the P3/P5 fields and final review before publication. [Local handoff](https://github.com/dowlingwong/Agent_paper_B/blob/b89bc899/reports/20261128-13-p4-timing-carry-forward-stop.md) · [Current decisions](https://github.com/dowlingwong/Agent_paper_B/blob/d47cab43/AUTHOR.md)

The queue re-fetch found no runnable Writer card and no direct handoff to Writer. The next round checks runbook §3.4 dispatch, evidence releases and the job receipts above.
