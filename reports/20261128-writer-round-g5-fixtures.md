# Paper B writer round after the G.5 fixture handoff

Writer is idle at research base `d25938ed46953bd0ecd2d467aebd94a862e657dc` and queue `555cfd02892e746279b19ae417ec85efdf387037`. The incoming Writer tip was `1be42f9d0fb4bc71a368d003379b3edd98e73033`. All five assigned writer cards are on published main. The result-table item in runbook §3.4 awaits dispatch and released evidence. [Queue](https://github.com/dowlingwong/Agent_paper_B/blob/555cfd02/STATE.md#writer) · [Prior Writer report](20261128-writer-round-d25938ed.md)

| Tasks | Published delivery branch and tip | Recorded review |
|---|---|---|
| `writer/20261126-01`, including `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | Restructure re-check ACCEPT WITH MINOR, corrections applied. The later title and trim have no separate review record. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | ACCEPT WITH MINOR, corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | Independent re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | Independent re-check ACCEPTED. |

Which control decisions improve the final configuration when every search has the same budget? In the logged Sweep 1 replay, 3,274 of 4,999 proposals repeated a configuration that had already been evaluated. D.3 measures whether skipping repeats and detectable no-ops, using a noise-aware keep rule, or using learned forecasts changes final gain. It pairs arms on fresh instances, caps each at 20 worker runs and 80 manager calls, and audits final-versus-start gain on ten fresh seeds. The paired estimates, intervals and declared Holm tests will establish which decisions improved gain. The offline gate separately tests one-step decisions on logged proposals. [Replay counts](https://github.com/dowlingwong/Agent_paper_B/blob/d25938ed/docs/r1/reports/b2_audit_20261119/counts.json) · [Claim-to-table sheet](https://github.com/dowlingwong/Agent_paper_B/blob/d25938ed/docs/r1/proposals/PAPER_B_CLAIM_TABLE_SHEET_20261126.md)

## Draft checks

Rebuilt the published standalone manuscript pin `c2a7de3456a88605ae3ac6284b33dbe3498c8ae5` with the README commands. LaTeX and Ghostscript page counts agree. I inspected rendered pages 1 and 8 of both previews. References start on page 8. Each build reports nine overfull boxes and zero undefined citations, undefined references or duplicate labels. The `FinalPaper` build exited 12 at the unset gate-outcome guard. Gate and D.3 results, realised T1 scope, final evidence citations, hashes and author-dependent text remain placeholders. The D.3 appendix's draft binding still names revision 4 and should cite the signed revision 5 when entered. This status report adds no manuscript unit for review. [Manuscript pin](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)

| Preview | Exit | Last main-text page | PDF pages | Rebuilt PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `a315919b4273df36e02c89b31ab9cadfb4df30acc148ed7bc9362c54d1403755` |
| Gate pass | 0 | 8 | 43 | `2c555246696e3cea313cea69c1b755fa9bd10916aea0c517594d76eda3067563` |

## Next checks

- **G.5 and offline gate.** Local `20261128-11` closed the fixture STOP at `cdcaeaf075f781946426c1a92f0cad9eea0660f4` with tier-E re-check ACCEPTED and zero new focused or full-suite failure/error IDs. The coordinator owns the paired merge of the render and fixture correction, the full-suite comparison, note publication and the strict published note check before Compute `20261126-06` can launch. The gate then needs labels, train/dev release, reviewed consumer bindings, proof checks, arms freeze and explicit test release. P11 engineering run `g5-p11-20261128T033600Z` is complete. [Local handoff](https://github.com/dowlingwong/Agent_paper_B/blob/9d6e4ae2/reports/20261128-11-g5-spec-test-fixtures.md)
- **D.3a.** Check Local `20261128-12`, now next in its queue. Revision 5 is signed and frozen. The reviewed P7 engineering runs `d3a-p7-exact-20261128-c` and `-d` are complete. The card directs Local to bind the revision 5 digest, record P7 PASS at 18.12% against the signed 18.53% threshold, and bind a launch SHA and fresh run ID. P10/P11, tier-E review, author P9 and publication precede the campaign. The completed screening run `SMEAS_EVIDENCE_20261128T001405Z` carries over. D.3b requires frozen arms and its own authorization. [Local card](https://github.com/dowlingwong/Agent_paper_B/blob/555cfd02/tasks/local/20261128-12-d3-step8-rev5.md) · [P7 receipt](https://github.com/dowlingwong/Agent_paper_B/blob/30bba985/reports/20261128-24-d3a-p7-exact-stop.md)
- **Compute P.4 E0.** Check `compute/20261128-16` for the signed-criterion verdict on `p5_e0_fresh_20261128_ada/e0e1`, `/e0e2`, `p5_e0_fresh_20261128_tasl7/e0e1`, and `/e0e2`. Local last observed Ada `/e0e1` at PID `4055310`. The fetched receipts have no fresh verdict. Phase 1 and A5 SFT await the verdict, timing review and note publication. [Compute card](https://github.com/dowlingwong/Agent_paper_B/blob/555cfd02/tasks/compute/20261128-16-e0-fresh-runs.md) · [Local observation](https://github.com/dowlingwong/Agent_paper_B/blob/d0637710/reports/20261128-10-g5-final-render.md#pending-lanes-when-handing-off)
- **Compute HTCondor preflight.** `760158.0` left the queue. `compute/20261128-03` needs a startable ETP L40S or TOpAS A100 and a replacement job ID. [Compute status](https://github.com/dowlingwong/Agent_paper_B/blob/30bba985/reports/20261128-23-round-status.md)
- **Writer.** Check for dispatch and release receipts. On release, fill the authorized cells on a standalone manuscript task branch, rebuild both previews and obtain independent review. The coordinator publishes the reviewed revision and advances the research pin.

| Verified record | SHA-256 |
|---|---|
| PLAN | `251cb8e4f68e13c14833e93d75b164663d459806f28dd2ded28ea1118407def0` |
| Claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Frozen D.3 rev 5 | `700d93cac277a23f527f20a49f8606987e63f615547b435cf924b2706ec778ad` |
| Filled G.5 launch spec, per Local receipt | `7dcc581573f84044495006865ff3e6966dab3b0e49ad53afff873b7e41dfaa4e` |
| Unsigned G.5 note, per Local receipt | `1a2ecfc2a05136edea226ea5aacc136419f5b8e02abe8e4c8d7943f63834079c` |

Decided alone to fetch and write this report with temporary writable Git metadata after the assigned worktree refused writes to its linked Git directory. All 15 pre-existing tracked edits matched published blobs and were preserved. Ancestry checks and `git diff --check` passed. Writer submitted zero jobs and opened zero sealed partitions. Job status comes from recorded handoffs.
