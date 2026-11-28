# Paper B Writer round — Forest Cover handoff and draft verification

Writer is idle. No Writer card is ready at research base
`7cd65cfa37cc1ece18d773b662a3f9b8c45917ce` and queue
`52fb689281a135032455bca3d73198759d52c1d0`. Incoming reports were Writer `bc3326e0`,
Local `a3994698` and Compute `b4d2a588`. The results card in runbook §3.4 awaits released
evidence and dispatch. [Writer queue](https://github.com/dowlingwong/Agent_paper_B/blob/52fb6892/STATE.md#writer)

The original delivery for the restructure includes `writer/20261126-02` and its approved
changes to sharing, attempt timing and the order of stages. All delivery tips below are ancestors of
the current research base. There was no new manuscript change requiring independent review this round.

| Completed card | Task branch and tip | Recorded review |
|---|---|---|
| `writer/20261126-01` with `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | Tier D independent re-check ACCEPT WITH MINOR, corrections applied. The final title and trim had no separate review. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | Tier S independent ACCEPT WITH MINOR, corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | Tier D independent re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | Tier D independent re-check ACCEPTED. |

## Question and evidence

Which control decisions help an automated search finish with a better configuration at the same
budget? Sweep 1 replay found that 3,274 of 4,999 proposals repeated configurations already evaluated.
The count shows how often the loop proposed repeats and motivates testing the benefit of filtering
them. D.3 pairs controllers on fresh instances, caps each at 20 worker runs and 80 manager calls,
and measures how much its final configuration improves on its starting point using ten fresh audit
seeds. A0R versus A0 isolates the rules for skipping repeats and detectable no-ops. A2 versus A0R
estimates what noise-aware decisions add with those rules in place. A3 and A5 versus A2 test
what the forecast-based controllers add. The paired estimates, intervals and declared Holm
decisions will determine which improvements the paper can claim. The offline gate tests one-step
utility on logged proposals. Both sets of results are pending.
[Sweep 1 counts](https://github.com/dowlingwong/Agent_paper_B/blob/7cd65cfa/docs/r1/reports/b2_audit_20261119/counts.json) · [Frozen declaration](https://github.com/dowlingwong/Agent_paper_B/blob/7cd65cfa/docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261128_R5.md)

## Draft checks

Rebuilt the exact standalone manuscript revision `c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`,
which matches the published research pin and the standalone main. LaTeX and Ghostscript agree on
page counts. Visually checked pages 1 and 8 of both previews. References start on page 8. Each
log has nine overfull-box warnings and zero undefined references, undefined citations or duplicate
labels. The `FinalPaper` command exited 12 at the unset gate-outcome guard as expected.
[Manuscript source](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)

| Preview | Build exit | Last main-text page | Total pages | Rebuilt PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `e5c0c3ef302b29a1fc9a727b688f352a296e1c73d9355f8f48c43d429dde867a` |
| Gate pass | 0 | 8 | 43 | `60ef933ddc04e9589bbe88c2d244a7ff1a9dad15514b1ad0cbdb827879f90c97` |

Gate and D.3 effects and intervals, C1 rates, realised T1 scope and author wording remain
placeholders. The draft's pending reference to D.3 revision 4 needs to cite the frozen revision 5
and its digest in the next assigned manuscript update.

## Job status and next checks

The Compute sample at 15:00 UTC found TASL-2 idle and zero Paper B jobs queued or running in
HTCondor. TASL-7 and Ada were not resampled. Writer submitted zero jobs and opened zero sealed
partitions. [Compute receipt](https://github.com/dowlingwong/Agent_paper_B/blob/b4d2a588/reports/20261128-36-round-status.md)

| Lane | Dependency and job identifier |
|---|---|
| Forest Cover G.5 | Local's handoff is already on `coord/local` at `f9193360`, as reconciled at `a3994698`. Compute checks its ledger and leases for `compute/20261128-20`, then completes C1–7 on TASL-2 at harness `3f7b09febf401a83f3aa881f00eecdd032024416`. Local can bind the addendum after the independently reviewed receipt is published. No host-check or campaign job ID is recorded. |
| Primary G.5 and Titanic/MetaMaze | Check launch-base decision and coordinator publication for `2178bc6e`, `88edb84f` and `4ee43037`. Check the ledger for run IDs `c3_t1_labels_20261128`, `c3_t1_labels_20261128_addendum_1` and `c3_t1_labels_20261128_addendum_2`. No campaign job IDs are recorded. |
| ETTh1 G.5 | Addendum 3 is published. Check the coordinator's exact launch-base and signing disposition for candidate `e9441f03` and run ID `c3_t1_labels_20261128_addendum_3`. No campaign job ID is recorded. ETTh1 goes in the separate 1GC descriptive output. |
| D.3a and D.3b | Exact-layout engineering runs `d3a-p7-exact-20261128-c` and `d3a-p7-exact-20261128-d` are closed. D.3a production waits for manifest and runtime binding, endpoint-to-card proof, unused run ID, review and author P9. D.3b waits for frozen arms and its own authorization. HTCondor preflight `760158.0` left the queue. Check for a startable ETP L40S or TOpAS A100. |
| P.4 phase 1 | P5 timing passed review. The author signs P3 over the reviewed spec bytes at `befb58c8`, then Local fills P3 and obtains final review. Check publication and ledger for `trackp-p4-p1-20261122-a`. No phase-1 training job ID is recorded. |
| Gate and Writer tables | The gate awaits G.5, eligible T1 train/dev release, reviewed consumer and preregistration bindings, proof checks, frozen arms and explicit test release. Check the queue for released C1, gate or D.3 results with an assigned card. Then update the corresponding placeholders on a manuscript task branch, build both previews and obtain an independent review for coordinator publication. |

[Forest Cover handoff](https://github.com/dowlingwong/Agent_paper_B/blob/a3994698/reports/20261128-local-round-forestcover-reconcile.md) · [ETTh1 launch-base receipt](https://github.com/dowlingwong/Agent_paper_B/blob/63ee5931/reports/20261128-15-g5-etth1-clean-launch-base.md) · [Author decisions](https://github.com/dowlingwong/Agent_paper_B/blob/52fb6892/AUTHOR.md)

| Verified source at research base | SHA-256 |
|---|---|
| PLAN containing §10 | `251cb8e4f68e13c14833e93d75b164663d459806f28dd2ded28ea1118407def0` |
| Claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Frozen D.3 revision 5 | `700d93cac277a23f527f20a49f8606987e63f615547b435cf924b2706ec778ad` |
| Approved ETTh1 addendum 3 | `903eb07a42affdd6f660847388ef3b318da3b50e62d0aed4a4ce8cfe05e1093b` |

Decided alone to use writable temporary Git metadata after the assigned worktree's linked
`FETCH_HEAD` write failed and to build from an archive of the published manuscript pin. All 15
existing modified files in the assigned worktree match published main byte for byte and were
preserved. `git diff --check` passed. This round changed only this status report.
