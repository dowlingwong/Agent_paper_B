# Paper B writer round at f0e4809a

Writer is idle. Research main `f0e4809a28262ed4cba27fdfea7c39ab3808cbe3` contains all five writer tasks. The coordinator queue at `d919f20f0d349b294839e12993b8ee8a0b5f4b22` has no new writer card. The result tables in runbook §3 item 4 await released results and dispatch. The standalone manuscript's main and research gitlink agree at `c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`. [Writer queue](https://github.com/dowlingwong/Agent_paper_B/blob/d919f20f/STATE.md#writer) · [Published manuscript](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)

| Task | Published research task branch and tip | Recorded review |
|---|---|---|
| `writer/20261126-01` and `writer/20261126-02`, delivered together | `writer-20261126-01-manuscript-restructure` at `e360d425752334c56cfaba8ff9499315ca15ea8e` | ACCEPT WITH MINOR, corrections applied. The final title and eight-page trim had no separate review. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` at `acf7d37be0cdddc29f157c311b337807f9cbea0a` | ACCEPT WITH MINOR, corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` at `e8dc1e36a09b61e9410132f23551064f1661e769` | Independent re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` at `e3af70a495816c3d107f013b9ee2c17593600bae` | Independent re-check ACCEPTED. |

## Question, measurement and claim

Which control decisions yield a better final configuration under the same budget? The published Sweep 1 audit counted 3,274 repeated proposals among 4,999. This establishes how often proposals repeated in that sweep. D.3 measures what the controller can gain by acting on repeats and other signals. Each arm starts from the same campaign instances and configurations, with a budget of 20 worker runs and 80 manager calls. Ten fresh seeds score the improvement from start to finish, scaled by the task's noise. The paired differences A0R − A0 and A2 − A0R measure the contribution of skipping duplicates and detectable no-ops, then the added contribution of the noise-aware decision rule. A3 and A5 against A2 measure the contribution of the learned forecasts. The offline gate tests one-step decisions on logged proposals. The effect sizes, intervals and declared conclusions await the corresponding releases. [Sweep 1 counts](https://github.com/dowlingwong/Agent_paper_B/blob/f0e4809a/docs/r1/reports/b2_audit_20261119/counts.json) · [Claim-to-table sheet](https://github.com/dowlingwong/Agent_paper_B/blob/f0e4809a/docs/r1/proposals/PAPER_B_CLAIM_TABLE_SHEET_20261126.md)

## Draft checks

| Draft | Build exit | Last main-text page | Total pages | Built PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `3dc850ce6cbd85c2236d243467c363a23fde004a5c080c63ac7f779d9424dceb` |
| Gate-pass preview | 0 | 8 | 43 | `8c700739f38d4c51c61c9f040432b7ef416809783b631d5cbbc2758d47067901` |

Both README builds passed. Page totals agree between the LaTeX logs and Ghostscript. Each build log has nine existing overfull boxes, zero undefined citations or references, and zero duplicate-label warnings. The final-build guard exited 12 at the unset gate-outcome switch. The gate, D.3 campaign results, full C1 audit rates, realised T1 scope and evidence bindings still use placeholders. Abstract approval, the anonymous companion citation and SGM author metadata also remain pending. This round verified published sources without making a manuscript change. The recorded reviews apply to the original deliveries.

## Pending and running elsewhere

- **D.3a P7 STOP.** Compute completed `compute/20261128-15` on TASL-2 under `d3p7c_20261128`, IDs `d3a-p7-exact-20261128-c` and `d3a-p7-exact-20261128-d`. The frozen server configuration fit, and the engineering check charged 50 worker failures in 276 runs (18.12%) against the signed 12.99% limit. The receipt is at `compute-d3a-p7-exact-20261128` tip `db9fb948c4edd075ef822805cf5fe5071a541dfe`, with 17 targeted tests passed and independent review pending. Local found 540 of the 944 capture paths in the branch. The reviewer needs the remaining capture location. The coordinator has routed the threshold decision to the author. The launch remains held at `local/20261128-08` pending that decision, binding, launch-commit P10/P11, review, P9 signature and publication. D.3b awaits frozen arms and its own authorization. [Compute receipt](https://github.com/dowlingwong/Agent_paper_B/blob/db9fb948/docs/r1/reports/d3a_p7_exact_20261128/D3A_P7_EXACT_RUNTIME_20261128.md) · [Local verification](https://github.com/dowlingwong/Agent_paper_B/blob/0b2794d4/reports/20261128-local-round-f0e4809a.md) · [Author decision sheet](https://github.com/dowlingwong/Agent_paper_B/blob/d919f20f/sheets/D3_WORKER_FAILURE_THRESHOLD_SHEET_20261128.md)
- **G.5 P11 and the offline gate.** The latest coordinator status has `g5-p11-20261128T033600Z-determinism` running on TASL-7, server PID `2748828`, under `compute/20261128-12`. Check that ID, then restart, tar and close-server receipts. G.5 awaits the accepted two-host matrix and final note render and publication. The gate awaits G.5 labels, reviewed consumers and proof checks, arms freeze and explicit test release. [Coordinator queue](https://github.com/dowlingwong/Agent_paper_B/blob/d919f20f/STATE.md)
- **P.4 E0.** `compute/20261128-16` is dispatched for two fresh runs per host under the signed criterion. Check for Ada IDs first, then TASL-7 after P11. The fetched ledger records no fresh IDs. Phase 1 and A5 SFT await a passing E0 comparison, reviewed timing and publication. [Fresh E0 card](https://github.com/dowlingwong/Agent_paper_B/blob/d919f20f/tasks/compute/20261128-16-e0-fresh-runs.md)
- **Batch preflight.** HTCondor job `760158.0` left the queue. Compute still needs a startable ETP L40S or TOpAS A100 and a replacement job ID. [Compute status](https://github.com/dowlingwong/Agent_paper_B/blob/ece384d9/reports/20261128-23-round-status.md)
- **Next for Writer.** Fetch the queue and releases. Once dispatched, fill the authorised cells on a standalone manuscript task branch and deliver both builds, evidence bindings and the independent review to the coordinator.

| Verified binding | SHA-256 |
|---|---|
| Claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Frozen D.3 rev 4 | `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745` |
| Exact-runtime P7 root manifest | `d38823b6d9f4220b9f22ae556f857e82429a549d7777a1f4f4c11e90a7405d73` |

Decided alone to fetch and stage this report in a temporary Git checkout after the assigned linked worktree refused writes to its Git metadata. Used the assigned worktree to verify all 15 pre-existing changes against published blobs. They all matched and were preserved. Built from a standalone checkout at the published manuscript pin. Zero jobs were submitted and zero sealed partitions were opened.
