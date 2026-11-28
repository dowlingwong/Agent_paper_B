# Paper B writer round — 28 November 2026

**Writer idle.** Research base `980c66665d78894c3fe8e84baf296231584c7aa8`. Coordinator queue `cc3dc9c9d1ff1117479357ddedb9ab3d171d84e5`. Incoming writer report tip `fd7375d755e2103f98afe7b0def99479abed94f3`. All five assigned writer cards are on published research main. The result-table work in runbook §3 item 4 awaits released evidence and a task ID. The standalone manuscript main and research submodule pin both resolve to `c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`. [Queue](https://github.com/dowlingwong/Agent_paper_B/blob/cc3dc9c9/STATE.md#writer) · [Manuscript](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)

| Task | Published research task branch and tip | Recorded review |
|---|---|---|
| `writer/20261126-01` and `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | ACCEPT WITH MINOR for the restructure, with minors applied. The title and eight-page trim had no separate review. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | ACCEPT WITH MINOR, with corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | ACCEPTED on independent re-check. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | ACCEPTED on independent re-check. |

## Question, measurement and claim

Which decisions leave the search with a better final configuration under the same budget? In the Sweep 1 replay, 3,274 of 4,999 proposals repeated an evaluated configuration. That count establishes how common repeats were in the replay. D.3 tests whether skipping them improves the final configuration. It pairs arms on starting configurations and instances, caps each campaign at 20 worker runs and 80 manager calls, and measures final improvement over the start on ten fresh seeds. A0R − A0 measures what skipping duplicates and detectable no-ops adds. A2 − A0R measures what the noise-aware index adds with the same rule layer. A3 and A5 versus A2 measure what proposal-level forecasts add. The paired estimates, intervals and declared Holm decisions determine which gains the paper can claim. The separate offline gate tests whether the forecasts improve one-step decisions on logged proposals. [Sweep 1 replay](https://github.com/dowlingwong/Agent_paper_B/blob/980c6666/docs/r1/reports/MAC_M3_DRYRUNS_20261104.md) · [Claim-to-table sheet](https://github.com/dowlingwong/Agent_paper_B/blob/980c6666/docs/r1/proposals/PAPER_B_CLAIM_TABLE_SHEET_20261126.md) · [Frozen D.3 rev 4](https://github.com/dowlingwong/Agent_paper_B/blob/980c6666/docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md)

Campaign and gate estimates, intervals and verdicts, C1 audit rates, realised T1 scope, result bindings and author wording approvals remain placeholders.

## Draft verification

| Draft | Build exit | Last main-text page | Total pages | Rebuilt PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `b7a2527d049801e397be5a0fe5f70aec55d1ae637a75a7089a2e3e77ab82a2cb` |
| Gate-pass preview | 0 | 8 | 43 | `ed1e5fec188eebb8a126fa88bc1b9a962f8178b78738a1e420b9bdd919517e01` |

Both README `latexmk` variants rebuilt from the pinned manuscript. Pages 1 and 8 rendered and were inspected in both PDFs. References begin on page 8. Each log has nine existing overfull boxes and zero undefined references, undefined citations or duplicate labels. The `FinalPaper` guard returned 12 at the unset gate switch. The four published task tips passed ancestry checks. This round provides a status report and build verification, so the recorded manuscript review verdicts still apply.

| Verified record | SHA-256 |
|---|---|
| Published claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Published frozen D.3 rev 4 | `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745` |
| P7 engineering smoke report at Compute task tip | `00d133fbf7c1403bf78e4dc679af87e16b8789608aa43c51d78fd01924b24551` |
| P7 engineering smoke summary at Compute task tip | `f57e75e16b253d661db0ac45ecd2d1057bc6ba1a6055db795a7f20f271e337c4` |

## Next checks

- **Compute review running, D.3a P7 execution complete.** Under `compute/20261128-13`, TASL-2 run root `d3p7_20261128` contains completed runs `d3a-p7-20261128-a` and `-b`. Compute pushed `compute-d3a-p7-20261128` @ `f838a199ad5a047f054ec4ba234df5b6f0e9745c` with 14/14 campaigns complete, worker gate PASS and zero worker failures. The report discloses the package-path adjustment for the smoke and records that no terminal-gain audit ran. Check the independent P7 verdict and the disposition of that environment before relying on the layout for launch. D.3a still needs the launch-note bindings, P10/P11 checks, review and P9 author signature. D.3b also needs frozen arms and its own authorization. [Dispatch](https://github.com/dowlingwong/Agent_paper_B/blob/cc3dc9c9/tasks/compute/20261128-13-p7-layout-accepted.md) · [Smoke receipt](https://github.com/dowlingwong/Agent_paper_B/blob/f838a199/docs/r1/reports/d3a_p7_20261128/D3A_P7_20261128.md)
- **Blocked, G.5 and offline gate.** P11 run `g5-p11-20261128T033600Z` passed the primary lease matrix and expected infrastructure STOP 7. Compute still needs an empty TASL-7 card for `-determinism`, `-restart`, `-tar` and `-closeserver`. Local's final render and review and the coordinator's publication follow. The gate needs G.5 labels, train/dev release, reviewed consumer and preregistration bindings, frozen arms, proof checks and explicit test release. [P11 record](https://github.com/dowlingwong/Agent_paper_B/blob/980c6666/docs/r1/reports/g5_p11_engineering_20261128_rerun/G5_P11_ENGINEERING_RERUN_20261128.md)
- **Blocked, P.4 and batch.** The same-code E0 repeats have closed. The author owns the E0 criterion decision for P.4 phase 1 and A5 SFT. Compute last reported HTCondor job `760158.0` out of the queue, with no startable ETP L40S or TOpAS A100 for a retry. [Author decision queue](https://github.com/dowlingwong/Agent_paper_B/blob/cc3dc9c9/AUTHOR.md) · [Compute batch record](https://github.com/dowlingwong/Agent_paper_B/blob/8b90626e/reports/20261128-16-d3-preflight-recheck3.md)
- **Writer next.** Fetch for the result-table card and its release record. Use a standalone manuscript task branch, fill the authorised cells, build both drafts and obtain fresh review. The coordinator publishes and advances the research pin. The active writer launcher schedules the next check 30 minutes after this round exits. [Runbook §3 and §7](https://github.com/dowlingwong/Agent_paper_B/blob/980c6666/docs/r1/runbooks/AUTOML_AS_DAC_NEXT_PHASE_20261126.md)

Decided alone to preserve the 15 pre-existing worktree modifications after verifying they all match published research main. The linked Git directory refused fetch writes, so this round used writable temporary Git metadata and rebuilt from a temporary archive of the pinned manuscript. Writer submitted zero compute jobs and opened zero sealed partitions.
