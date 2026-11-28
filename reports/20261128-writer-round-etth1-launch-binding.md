# Paper B Writer round — 28 November 2026, 17:32 CET

**Writer idle.** Round base `7cd65cfa37cc1ece18d773b662a3f9b8c45917ce`, queue
`52fb689281a135032455bca3d73198759d52c1d0`, incoming Writer report tip
`94150eb01aeb3104783eb8b0e02f8fc007c46a59`. No open Writer card is ready. The pending
results tables are runbook §3.4. The next action is to check for released evidence and a results
assignment. [Queue](https://github.com/dowlingwong/Agent_paper_B/blob/52fb6892/STATE.md#writer)

| Card | Published delivery branch and tip | Review verdict |
|---|---|---|
| `writer/20261126-01` and `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | Tier D independent re-check ACCEPT WITH MINOR, corrections applied. Title and trim had no separate review. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | Tier S independent ACCEPT WITH MINOR, corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | Tier D independent re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | Tier D independent re-check ACCEPTED. |

All four delivery tips are ancestors of the research base. This round produced no new manuscript
unit or task branch, so there is no new independent review verdict.

## Question, method, measurement and claim

Which control decisions help automated search end with a better configuration under the same budget?
In Sweep 1, 3,274 of the 4,999 replayed proposals repeated a configuration already evaluated.
This shows that repeats were common and motivates measuring the effect of skipping them. D.3 pairs
controllers on the same fresh instances with caps of 20 worker runs and 80 manager calls. It measures
how much the final configuration improves on the start on ten fresh audit seeds. A0R − A0 estimates
the benefit of filtering repeats and detectable no-ops. A2 − A0R estimates the added benefit of the
noise-aware decision rule with the same filters. A3/A5 − A2 estimates what the forecast-based arms
add. The paired estimates, intervals and declared Holm decisions determine which gains the paper
can claim. The offline gate tests one-step utility on logged proposals. Both outcome sets are pending.
[Published Sweep 1 counts](https://github.com/dowlingwong/Agent_paper_B/blob/7cd65cfa/docs/r1/reports/b2_audit_20261119/counts.json) · [Frozen D.3 declaration](https://github.com/dowlingwong/Agent_paper_B/blob/7cd65cfa/docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261128_R5.md)

## Draft builds

The standalone manuscript main and research submodule pin agree at
`c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`. Both previews were rebuilt from that exact tree.
LaTeX and Ghostscript agree on page counts. References begin on page 8 in both. Both logs have nine
overfull-box warnings and zero undefined references, undefined citations or duplicate labels.
The `FinalPaper` check exited 12 as expected at the unset gate-outcome guard.
[Manuscript source](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)

| Preview | LaTeX exit | Last main-text page | Total pages | Rebuilt PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `4fcae83dac3ecc6cd2b7fba96eb3978f9b0b8916acbb4cc5396e06609919d96f` |
| Gate pass | 0 | 8 | 43 | `ab48f7e5c4c7bd81408305b020c249682967498eeb09f8c92e9a21385e0be076` |

Gate and D.3 effects and intervals, C1 rates, realised T1 scope and author wording still have
placeholders. The pending D.3 reference in the methods appendix names revision 4. The next
assigned manuscript update should cite the frozen revision 5 and its digest.

## Jobs and dependencies

The last Compute sample at 15:00 UTC showed TASL-2 idle and zero Paper B jobs in HTCondor.
TASL-7 and Ada were not resampled. Writer submitted zero jobs and opened zero sealed
partitions. [Compute receipt](https://github.com/dowlingwong/Agent_paper_B/blob/b4d2a588/reports/20261128-36-round-status.md)

| Work | Next check |
|---|---|
| Primary G.5 and Titanic/MetaMaze addenda | Run IDs `c3_t1_labels_20261128`, `c3_t1_labels_20261128_addendum_1`, `c3_t1_labels_20261128_addendum_2`. Author launch-base decision and coordinator publication pending for candidate tips `2178bc6e`, `88edb84f`, `4ee43037`. No campaign job IDs recorded. |
| ETTh1 addendum | Local delivered tier-E accepted candidate `e9441f03128bf6ed7291b854e70773f4c1dd5fba` for `c3_t1_labels_20261128_addendum_3`. Its verifier hits the publication ancestry STOP. Published `7cd65cfa` passes the verifier for ETTh1. The coordinator chooses the exact checkout and records the signing disposition before Compute checks the ledger and leases. ETTh1's licence line is due before a label table cites it. |
| Forest Cover addendum | Compute owes the exact-pin C1–7 receipt at `3f7b09febf401a83f3aa881f00eecdd032024416`, then Local review, approval and clean launch base. No campaign job ID recorded. |
| D.3a/b | Engineering runs `d3a-p7-exact-20261128-c` and `d3a-p7-exact-20261128-d` are complete. D.3a production waits for runtime and input bindings, endpoint-to-card proof, fresh run ID, review and author P9. D.3b waits for frozen arms and its own authorization. HTCondor preflight `760158.0` left the queue. Compute checks for a startable ETP L40S or TOpAS A100. |
| P.4 phase 1 | P5 timing PASS and reviewed. For `trackp-p4-p1-20261122-a`, author P3 signature on the reviewed spec bytes at `befb58c8` is pending. Local then fills P3 and obtains final review. No training job ID recorded. |
| Offline gate and Writer results | Gate awaits G.5, T1 train/dev release, reviewed consumer and preregistration bindings, proof checks, frozen arms and explicit test release. The Writer takes the results card when dispatched with released evidence. |

[Author decisions](https://github.com/dowlingwong/Agent_paper_B/blob/52fb6892/AUTHOR.md) · [Local launch-base receipt](https://github.com/dowlingwong/Agent_paper_B/blob/63ee5931/reports/20261128-15-g5-etth1-clean-launch-base.md)

| Verified source at research base | SHA-256 |
|---|---|
| PLAN containing §10 | `251cb8e4f68e13c14833e93d75b164663d459806f28dd2ded28ea1118407def0` |
| Claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Frozen D.3 revision 5 | `700d93cac277a23f527f20a49f8606987e63f615547b435cf924b2706ec778ad` |
| Approved ETTh1 addendum | `903eb07a42affdd6f660847388ef3b318da3b50e62d0aed4a4ce8cfe05e1093b` |

Decided alone to use temporary Git metadata for fetch and reporting because the assigned worktree
could not write its linked `FETCH_HEAD`. All 15 existing modifications matched the published files
byte for byte and were preserved. `git diff --check` passed. The Writer launcher is active with its
30-minute queue check between rounds.
