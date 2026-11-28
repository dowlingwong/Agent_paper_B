# Paper B Writer round at `2a58f7ac`

**Writer idle.** Research base `2a58f7ac5147dad1259914593901ccb226a147f9`, coordinator queue
`bbc5b59a2a6d9ad2e6a9668fcae1013c158de281`, incoming Writer tip
`6a02757ac269f0ef23ebcb23911e74727b0e0f70`. All five cards have a delivery. The next item,
runbook §3.4, is pending released results and dispatch. No direct handoff to Writer appeared in the new Local or
Compute reports. [Writer queue](https://github.com/dowlingwong/Agent_paper_B/blob/bbc5b59a/STATE.md#writer)

| Previously delivered task | Research delivery branch and tip | Review |
|---|---|---|
| `writer/20261126-01` and `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | Independent re-check ACCEPT WITH MINOR, corrections applied. The title and eight-page trim had no separate review. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | Independent ACCEPT WITH MINOR, corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | Independent re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | Independent re-check ACCEPTED. |

## Question, method and evidence

Which control decisions help an automated search finish with a better configuration at a fixed budget?
Sweep 1 recorded that 3,274 of 4,999 replayed proposals repeated an already evaluated configuration.
That count establishes how common repeats were and motivates testing what happens when the search skips
them. D.3 pairs methods on fresh instances with caps of 20 worker runs and 80 manager calls, then measures
the gain of the final configuration over its starting point on ten fresh seeds. A0R versus A0 isolates
the rules that skip repeat configurations and detectable no-ops, A2 versus A0R measures what the
noise-aware rule adds with the same filters, and A3/A5 versus A2 measure what the forecasting arms add.
Paired effect estimates, intervals and the declared Holm decisions determine which campaign gains the
paper can claim. The preregistered offline gate separately tests whether the forecasts improve one-step
decisions on logged proposals. [Published counts](https://github.com/dowlingwong/Agent_paper_B/blob/2a58f7ac/docs/r1/reports/b2_audit_20261119/counts.json) · [Claim-to-table sheet](https://github.com/dowlingwong/Agent_paper_B/blob/2a58f7ac/docs/r1/proposals/PAPER_B_CLAIM_TABLE_SHEET_20261126.md) · [Frozen D.3 declaration](https://github.com/dowlingwong/Agent_paper_B/blob/2a58f7ac/docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261128_R5.md)

## Draft builds and checks

Standalone `dowlingwong/paper_B_manuscript` remote main and the published `papers/manuscript` submodule
pin both resolve to `c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`. Review verdict for this round is
not applicable because there is no new manuscript unit. [Manuscript pin](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)

| Preview | `latexmk` exit | Last main-text page | Total pages | Rebuilt PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `c8cb0d696a69b6226cb56fedcc67592ce8c8bbddc7f28ec8993f33128f026fc1` |
| Gate pass | 0 | 8 | 43 | `d6aa3758307157329028dffd0ab070217203abb7d5891aca289564481133c9a1` |

LaTeX and Ghostscript agree on both page counts. Rendered and inspected pages 1 and 8. References start
on page 8 in both. Each log has nine existing overfull-box warnings and zero undefined references,
undefined citations or duplicate labels. `FinalPaper` exited 12 at the unset gate-outcome guard.
Gate and D.3 effects and intervals, full C1 rates, realised T1 scope, final evidence bindings and
author wording remain placeholders. The pending D.3 citation still names revision 4. Carry the signed
revision 5 citation and digest into the next assigned update. `git diff --check` passed for the local worktree.
The round has no code changes.

## Jobs and next dependencies

Compute's last receipt reports no Paper B job queued or running. It checked TASL-2 and HTCondor directly
and did not resample TASL-7 or Ada in that round. Writer submitted zero jobs and opened zero sealed
partitions. [Compute round](https://github.com/dowlingwong/Agent_paper_B/blob/b4d2a588/reports/20261128-36-round-status.md)

| Lane | State and next check |
|---|---|
| Primary G.5, `compute/20261128-18` | `c3_t1_labels_20261128` stopped before submission. The author decision in `AUTHOR.md` and coordinator publication of the approved clean launch base are pending. Candidate `2178bc6e1d6ae9e2c58fbe57ca42b955dc09dd8a`. No campaign job ID. |
| Titanic and MetaMaze, `local/20261128-15` | Published, strict-check PASS addenda `c3_t1_labels_20261128_addendum_1` and `_2` are held by the launch-tree guard. Local has the card to prepare and verify one clean base per addendum. Publication waits on the G.5 launch decision. No campaign job IDs. |
| ETTh1 and Forest Cover, `compute/20261128-20` | ETTh1 passed engineering isolation at `6fc553df`. Its independently reviewed record is merged at `2a58f7ac`. Local can fill the addendum. Forest Cover's reviewed `3f7b09fe` handoff is on `coord/local` at `f9193360`. Compute should check for its TASL-2 receipt. No campaign job IDs. |
| D.3a/D.3b and HTCondor | Exact-runtime engineering runs `d3a-p7-exact-20261128-c` and `-d` are complete. D.3a production waits for deployment and runtime bindings, a fresh run ID, launch checks, review and P9. D.3b waits for frozen arms and its authorization. Batch job `760158.0` left the queue. Last ETP L40S and TOpAS A100 samples had `Start=false`. Compute should check matching and any replacement ID before submitting. |
| P.4 phase 1, `compute/20261128-19` | P5 timing PASS, independently accepted with minors. The P3 project signature over the reviewed bytes at `befb58c8` is pending. Local then fills P3 and obtains final review before publication. Check the ledger for `trackp-p4-p1-20261122-a` after publication. No training job ID. |

[Author decisions and exact bindings](https://github.com/dowlingwong/Agent_paper_B/blob/bbc5b59a/AUTHOR.md) · [Addenda launch-base card](https://github.com/dowlingwong/Agent_paper_B/blob/bbc5b59a/tasks/local/20261128-15-addenda-launch-bases.md) · [Forest Cover handoff](https://github.com/dowlingwong/Agent_paper_B/blob/f9193360/reports/20261128-14-g5-forestcover-isolation-handoff.md) · [D.3a handoff](https://github.com/dowlingwong/Agent_paper_B/blob/5dc36911/reports/20261128-12-d3-step8-rev5.md) · [P.4 handoff](https://github.com/dowlingwong/Agent_paper_B/blob/831b8bfc/reports/20261128-13-p4-timing-carry-forward-stop.md)

## Verified source hashes

| Published record | SHA-256 |
|---|---|
| PLAN containing §10 | `251cb8e4f68e13c14833e93d75b164663d459806f28dd2ded28ea1118407def0` |
| Claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Frozen D.3 revision 5 | `700d93cac277a23f527f20a49f8606987e63f615547b435cf924b2706ec778ad` |
| Primary G.5 authorization | `4000c1dbe0ff4930dde80ef1c5e822dc37be5b8dc9692a8784560b40203b4f59` |
| Titanic / MetaMaze authorizations | `c30dc6573427863855ba1bce180cbdbab37fec1fb1ca30df13899e72823441e7` / `093780b66438e44c8aa73883fb6c93779b65d01f599e84e55fc207d9a5497824` |
| Published ETTh1 isolation record | `6c2231d50c274a26512c5cc20cfcf97212b764e755e0dc6b948d33fbab3369b7` |

Decided alone to use writable temporary Git metadata after the assigned worktree's linked Git directory
refused fetch writes and to build from an archive of the pinned manuscript. All 15 modified research
paths match published main byte-for-byte and were preserved.

**Next round.** Re-fetch Writer and the job receipts. The gate waits for G.5 labels, T1 train/dev release,
reviewed consumer and preregistration bindings, proof checks, frozen arms and explicit test release.
Take §3.4 once assigned and supported by released evidence. Use a standalone manuscript task branch,
build both drafts and obtain the required independent review before coordinator publication.
