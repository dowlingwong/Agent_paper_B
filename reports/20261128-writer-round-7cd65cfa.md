# Paper B Writer round at `7cd65cfa`

**Writer idle.** Research base `7cd65cfa37cc1ece18d773b662a3f9b8c45917ce`, coordinator queue
`52fb689281a135032455bca3d73198759d52c1d0`, incoming Writer tip
`c016d33f8543796b59c5745b315d9c5c917f13a5`. All five Writer cards are published. The
queue and handoffs supply no ready Writer card. Runbook §3.4 awaits released evidence and dispatch.
[Writer queue](https://github.com/dowlingwong/Agent_paper_B/blob/52fb6892/STATE.md#writer)

| Completed card | Published delivery branch and tip | Review |
|---|---|---|
| `writer/20261126-01` and `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | Independent re-check ACCEPT WITH MINOR, corrections applied. The title and trim had no separate review. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | Independent ACCEPT WITH MINOR, corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | Independent re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | Independent re-check ACCEPTED. |

## Question, method and evidence

Which control decisions help an automated search finish with a better configuration at a fixed budget?
In Sweep 1, 3,274 of 4,999 replayed proposals repeated a configuration that had already been evaluated.
That count shows how common repetition was and motivates measuring the gain from skipping repeats.
D.3 pairs controllers on the same fresh instances, with caps of 20 worker runs and 80 manager calls.
Ten fresh audit seeds measure how much the final configuration improves on the start. A0R versus A0
measures the effect of skipping repeats and detectable no-ops. A2 versus A0R measures what the
noise-aware rule adds with the same filters. A3 and A5 versus A2 measure what the forecast-based
controllers add. The paired estimates, intervals and declared Holm decisions will determine which gains
the paper can claim. The offline gate separately tests whether the forecasts improve one-step decisions
on logged proposals. [Published sweep counts](https://github.com/dowlingwong/Agent_paper_B/blob/7cd65cfa/docs/r1/reports/b2_audit_20261119/counts.json) · [Frozen D.3 declaration](https://github.com/dowlingwong/Agent_paper_B/blob/7cd65cfa/docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261128_R5.md)

## Draft builds

The standalone manuscript main and the published research pin both point to
`c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`.
[Manuscript source](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)

| Preview | LaTeX exit | Last main-text page | Total pages | Rebuilt PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `773512c893bd64d8f0a92bdba2d8e7dcaaba457b8c92c2d4b483afb4b74e6c09` |
| Gate pass | 0 | 8 | 43 | `1ebeba3a5b980cf8bf6eb974f90f5bf926dc7757229e8652a09e5f65cfe95ca4` |

LaTeX and Ghostscript agree on page counts. Pages 1 and 8 were rendered and checked. References begin
on page 8 in both previews. Each log has nine overfull-box warnings and zero undefined references,
undefined citations or duplicate labels. `FinalPaper` exits 12 at the unset gate-outcome guard.
Gate and D.3 effects and intervals, C1 rates, realised T1 scope and author wording remain placeholders.
The pending D.3 citation still names revision 4. The next assigned update should cite revision 5 and its digest.
Review verdict for this round is not applicable because the round has no new manuscript unit.

## Jobs and dependencies

Compute's last receipt found zero Paper B jobs queued or running on the sampled TASL-2 and HTCondor
surfaces. TASL-7 and Ada were not resampled. Writer submitted zero jobs and accessed zero sealed partitions.
[Compute receipt](https://github.com/dowlingwong/Agent_paper_B/blob/b4d2a588/reports/20261128-36-round-status.md)

| Work | Latest state and next check |
|---|---|
| Primary G.5 | Run ID `c3_t1_labels_20261128` is blocked before submission. Author decision and coordinator publication of the clean launch base `2178bc6e1d6ae9e2c58fbe57ca42b955dc09dd8a` are pending. |
| G.5 Titanic and MetaMaze | Local delivered reviewed clean-base candidates `88edb84f` and `4ee43037` for run IDs `c3_t1_labels_20261128_addendum_1` and `c3_t1_labels_20261128_addendum_2`. Signing and publication ancestry are pending. |
| G.5 ETTh1 and Forest Cover | ETTh1 addendum 3 is now approved on main for the separate 1GC descriptive output. For `c3_t1_labels_20261128_addendum_3`, check Local's clean-base delivery, signing disposition and Compute's run ledger and leases. The latest Forest Cover receipt still awaits the exact-pin host check at `3f7b09fe`. No campaign job IDs are recorded. |
| D.3a and D.3b | Exact-runtime engineering runs `d3a-p7-exact-20261128-c` and `d3a-p7-exact-20261128-d` are complete. D.3a production needs deployment and runtime bindings, a fresh run ID, launch checks, review and author P9. D.3b waits for frozen arms and its own authorization. HTCondor preflight `760158.0` left the queue. The last ETP L40S and TOpAS A100 samples had `Start=false`. |
| P.4 phase 1 | P5 timing PASS, independently accepted with minors. P3 awaits the author signature on the reviewed spec bytes at `befb58c8`. Local fills P3 and obtains final review before publication. Check the ledger for `trackp-p4-p1-20261122-a` after publication. No training job is recorded. |

[Author decisions](https://github.com/dowlingwong/Agent_paper_B/blob/52fb6892/AUTHOR.md) · [Local clean-base receipt](https://github.com/dowlingwong/Agent_paper_B/blob/02461657/reports/20261128-15-g5-clean-launch-bases.md) · [Published ETTh1 note](https://github.com/dowlingwong/Agent_paper_B/blob/7cd65cfa/docs/r1/authorizations/c3_t1_labels_20261128_addendum_3.md)

| Verified source at research base | SHA-256 |
|---|---|
| PLAN containing §10 | `251cb8e4f68e13c14833e93d75b164663d459806f28dd2ded28ea1118407def0` |
| Claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Frozen D.3 revision 5 | `700d93cac277a23f527f20a49f8606987e63f615547b435cf924b2706ec778ad` |
| Approved ETTh1 addendum | `903eb07a42affdd6f660847388ef3b318da3b50e62d0aed4a4ce8cfe05e1093b` |

Decided alone to use writable temporary Git metadata after the assigned worktree's linked Git directory
refused fetch writes and to rebuild from an archive of the exact manuscript pin. All 15 modified paths
in the assigned worktree match published main and were preserved. `git diff --check` passed.

**Next round.** Re-fetch the queue and launch receipts. The offline gate awaits G.5 labels, T1 train/dev
release, reviewed consumer and preregistration bindings, proof checks, frozen arms and explicit test release.
Take the results card when dispatched and supported by released evidence. Update the placeholders on a standalone
manuscript task branch, build both drafts and obtain independent review before coordinator publication.
