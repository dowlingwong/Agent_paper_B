# Paper B writer round at Compute `8bf88a02`

**Writer idle.** No new writer task ID. Research base `980c66665d78894c3fe8e84baf296231584c7aa8`, coordinator queue `70f8298b39c9ffd524c7b4b225855b2c7b4e5bba`, incoming writer report `9637b9182b72b913e2087b24738386f1798acc0f`. All five writer cards are published on research main. The result-table work in runbook §3 item 4 awaits released results and a task card. Standalone manuscript main and the research pin both resolve to `c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`. [Queue](https://github.com/dowlingwong/Agent_paper_B/blob/70f8298b/STATE.md#writer) · [Manuscript](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)

| Published task | Research delivery branch @ exact tip | Recorded review |
|---|---|---|
| `writer/20261126-01` and `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | Restructure re-check ACCEPT WITH MINOR, with corrections applied. The later title and page trim had no separate review. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | ACCEPT WITH MINOR, with corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | ACCEPTED on independent re-check. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | ACCEPTED on independent re-check. |

## Question, measurement and claim

Which decisions leave the search with a better final configuration under the same budget, and by how much? In the Sweep 1 replay, 3,274 of 4,999 proposals repeated configurations already evaluated. The count measures how often the replay proposed duplicates. D.3 pairs the arms on fresh instances with the same starting configurations and caps each campaign at 20 worker runs and 80 manager calls. It measures the final configuration's improvement over the start on ten fresh audit seeds and scales that gain by the node's noise scale. A0R minus A0 measures what skipping duplicates and detectable no-ops adds. A2 minus A0R measures what the noise-aware index adds with the same rule layer. A3 and A5 versus A2 measure what proposal-level forecasts add. The paired effects, intervals and preregistered Holm decisions determine which gains the paper can claim. The offline gate asks separately whether forecasts improve one-step decisions on logged proposals. [Replay](https://github.com/dowlingwong/Agent_paper_B/blob/980c6666/docs/r1/reports/MAC_M3_DRYRUNS_20261104.md) · [Claim-to-table sheet](https://github.com/dowlingwong/Agent_paper_B/blob/980c6666/docs/r1/proposals/PAPER_B_CLAIM_TABLE_SHEET_20261126.md) · [Frozen D.3 rev 4](https://github.com/dowlingwong/Agent_paper_B/blob/980c6666/docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md)

The campaign and gate effects, intervals and verdicts, full C1 audit rates, realised T1 scope, result bindings and author wording approvals remain placeholders.

## Draft verification

| Draft | Build exit | Last main-text page | Total pages | Rebuilt PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `e32d9fac957a11dc3c6b621ff74fcf5c9af0e0635d87819ec13017b7f9010a0d` |
| Gate-pass preview | 0 | 8 | 43 | `a1c79695303b9cf90ce695e24e706e42d0be0f1314065c6a14bc85a3c67bc8db` |

Both README `latexmk` commands succeeded from the pinned sources. Pages 1 and 8 were rendered and checked in both drafts. The references start on page 8. Each log has nine existing overfull boxes and zero undefined references, undefined citations or duplicate labels. `FinalPaper` returned 12 at the unset gate switch. All four historical delivery tips passed ancestry checks against published research main. This round produced build verification and a status report. The review verdicts in the table apply to the historical deliveries.

| Verified record | SHA-256 |
|---|---|
| Published claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Published frozen D.3 rev 4 | `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745` |
| D.3a P7 engineering receipt | `a73ea6359afd5789ecf2853cf66ca0b25cfe6263eb7da82b56ca0423267d2d72` |
| D.3a P7 capture manifest | `af84ce0d520ffb70e289521c3f11c8bf73f29f61c2a780851edbb8593019a8cf` |
| D.3a P7 independent review R2 | `191f96b85316c3d8dfea42786498d90eadc96cadcbd0ffde9fb1f4b88b6cad59` |
| D.3a P7 independent review R3 | `351de7f64ddc73a28e83421cc104283da16847e110e22a162991b3412dfbd94d` |
| Published partial G.5 P11 record | `910a1395f6598aabf344b7f60e095ee18a8f104ed7a56952f80a4259deaa9c8c` |

## Other work and next checks

- **D.3a P7 complete, publication and launch pending.** Compute cards `compute/20261128-11`, `-13` and `-14` delivered the fully CPU-pinned TASL-2 receipt from `d3p7b_20261128`, run IDs `d3a-p7-20261128-c` and `d3a-p7-20261128-d`. All 14 engineering campaigns completed. The worker gate passed at 33 failures in 271 charged runs (12.18%, limit 12.99%). The `trial-071` YAML parser error was classified as an admitted invalid configuration. Compute recorded 17 focused tests passing. Independent R2 accepted the substantive receipt and R3 accepted the final delivery `compute-d3a-p7-20261128` @ `3c12db25301e89c1dc86946922bfa840f4d7c254`, review `compute-d3a-p7-20261128-review` @ `b86e89661dcf576534630894fc9c47d65448907b`. The smoke supplied engineering checks and no terminal audit. Next check for coordinator publication, D.3a launch bindings, P10/P11 at the exact launch commit, accepted note review and author P9 signature. D.3b also needs frozen arms and its own authorization. [Receipt](https://github.com/dowlingwong/Agent_paper_B/blob/3c12db25/docs/r1/reports/d3a_p7_20261128/D3A_P7_20261128.md) · [Independent review](https://github.com/dowlingwong/Agent_paper_B/blob/b86e8966/docs/r1/reviews/D3A_P7_REVIEW_R3_20261128.md)
- **G.5 and offline gate blocked.** Matrix `g5-p11-20261128T033600Z` passed the primary two-host lease matrix and expected infrastructure STOP 7. Compute card `compute/20261128-12` still needs an empty TASL-7 card for `-determinism`, `-restart`, `-tar` and `-closeserver`. Local card `local/20261126-08` awaits the reviewed two-host record and final `paper.commit` for the render. The coordinator then publishes G.5. The gate still needs G.5 labels, train/dev release, reviewed consumer and preregistration bindings, proof checks, frozen arms and explicit test release. [Partial P11 record](https://github.com/dowlingwong/Agent_paper_B/blob/980c6666/docs/r1/reports/g5_p11_engineering_20261128_rerun/G5_P11_ENGINEERING_RERUN_20261128.md) · [Local handoff](https://github.com/dowlingwong/Agent_paper_B/blob/6916514e/reports/20261128-local-round-8bf88a02.md)
- **Compute idle in its latest recorded snapshot.** Compute reported no active Paper B jobs at 07:30 UTC. HTCondor preflight job `760158.0` had left the queue. Check for a startable ETP L40S or TOpAS A100 before any retry under `compute/20261128-03`. The E0 repeats `p5_e0_rep_20261128_ada/e0e` and `p5_e0_rep_20261128_tasl7/e0e` are complete. P.4 phase 1 and A5 SFT await the author's E0 criterion decision and the phase-1 note. [Compute status](https://github.com/dowlingwong/Agent_paper_B/blob/8bf88a02/reports/20261128-22-round-status.md) · [Author queue](https://github.com/dowlingwong/Agent_paper_B/blob/70f8298b/AUTHOR.md)
- **Writer next.** Fetch for the result-table task and its release record. Fill the authorised cells on a standalone manuscript task branch, build both drafts and obtain fresh review. The coordinator publishes and advances the research pin. [Runbook §3](https://github.com/dowlingwong/Agent_paper_B/blob/980c6666/docs/r1/runbooks/AUTOML_AS_DAC_NEXT_PHASE_20261126.md#3-paper-b-manuscript-and-results)

Decided alone to preserve the 15 pre-existing worktree modifications after verifying each matches published research main. Linked Git metadata refused writes, so the fetch and report used writable temporary Git metadata. Both drafts were rebuilt from a temporary archive of the pinned manuscript. This round submitted zero compute jobs and opened zero sealed partitions.
