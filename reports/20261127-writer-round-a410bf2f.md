# Paper B writer round at a410bf2f

**Writer idle.** Published research base `f43823dad358a25608fe27013221eba9aaa7d385`.
Queue `a410bf2fa4af5de6bd1ba011cb9a73522e6d3f32`. Published manuscript `main` and the research submodule
both point to [paper_B_manuscript at c2a7de34](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5).
The title trim and all five cards are published. The four branch tips below are ancestors of the research base.
Runbook §3 item 4 is pending a coordinator card and released extracts. This round is a build verification and
handoff. There is no new task ID, manuscript revision or independent review verdict.

| Task | Delivered branch and exact tip | Review on record |
|---|---|---|
| `writer/20261126-01` and `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | Restructure re-check ACCEPT WITH MINOR, corrections applied. The title and trim follow-up had no separate review. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | ACCEPT WITH MINOR, corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | Independent re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | Independent re-check ACCEPTED. |

## Question, method and evidence

Which control decisions leave a campaign with a better final configuration when each arm has at most 20 worker
runs and 80 manager calls? The published Sweep 1 replay found that 3,274 of 4,999 proposals repeated a previously
evaluated configuration. That count motivates the duplicate-skipping arm. D.3 pairs controllers on fresh campaigns
and uses ten fresh seeds to measure how much the final configuration improves on the start. A0R − A0 measures what
skipping duplicates and detectable no-ops adds. A2 − A0R measures the next gain from noise-aware decisions.
A3 − A2 and A5 − A2 measure the gain from each forecasting arm. The paired estimates, intervals and signed
within-family decisions will determine which gains the paper can attribute to each decision. The offline gate
separately tests one-step utility on logged proposals. [Sweep 1 replay](https://github.com/dowlingwong/Agent_paper_B/blob/f43823da/docs/r1/reports/MAC_M3_DRYRUNS_20261104.md)

The D.3 effects and intervals, descriptive outcomes, gate estimates and verdict, full C1 audit rates, realized T1
populations and evidence bindings still use placeholders. The build flags select draft layouts only. No sealed
evidence was read and no job was submitted.

## Build checks

| Draft | Fresh latexmk exit | Last main-text page | Total pages | Rebuilt PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate non-pass | 0 | 8 | 44 | `69297594a63b1d932ee5c73ed095f3d6653073aa81e3baacc8012ee50c0c36b5` |
| Gate pass preview | 0 | 8 | 43 | `6f36748ca7307aabe53a8da8be9427ed99260e9ef230c21892bcaac6d0266b65` |

Every page matched the corresponding published research snapshot in both extracted text and raster output.
Page 8 was inspected in both builds and shows the transition from limitations to references. Both final logs
showed zero undefined references, undefined citations or multiply defined labels and nine existing overfull boxes
each. The `FinalPaper` guard refused the unresolved gate switch with exit 12. `git diff --check` passed.
The claim sheet SHA-256 is `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7`.
The frozen D.3 rev 4 SHA-256 is `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745`.

Decided alone to preserve the assigned worktree. All 15 modified paths match published main byte for byte.
The shared Git metadata refused the `FETCH_HEAD` write, so the fresh fetch and reporting used temporary Git
metadata. The builds used an archive of the published standalone manuscript commit.

## Pending work and next checks

- **Screening.** Compute `20261127-35` is ready under R1-SCREEN-COTENANCY-INFRA. The recorded attempt
  `SMEAS_EVIDENCE_20261127T1550Z` (tmux `smeas_reissue2`) stopped at 186/10,164 written, zero failed.
  Check the next receipt for a fresh stamp and strict preflight with at least ten free deepthought cores.
  The signed note SHA-256 is `85d414763f890762628df60a25bfdd1aa2dd0e2ea81662ce31faa45cf2875db9`.
  The STOP manifest SHA-256 is `39575f58bf0a2d824b6f2e75bab2075230b03e653396bd0e9c73d5dada05c2c9`.
- **D.3.** The independently accepted smoke-audit correction `345f4c97` is published in research main through
  `4f6fea8d`. The TASL-2 engineering smoke is complete. HTCondor jobs `760148`, `760149` and `760152` were removed
  unmatched. Check for an eligible L40S or A100, the screening result and any SHARED author decision, then step (8),
  the required per-arm smoke and the D.3a/b authorizations. D.3b requires the frozen arms under either gate outcome.
- **G.5 and expansion.** The four nodes in `g1b-x-tasl-20261126-a` are sealed with determinism PASS. The four reviewed
  addendum drafts are merged. `local/20261127-30` unit 1 handed off the PRE-SPLIT v2 publication amendment at
  `486d1150bfa41d29f5f065d9eed4cbf53272f7ac`, independently ACCEPTED. Check coordinator publication, the separate
  addendum switch binding and D6 copy `compute/20261127-36`. Main G.5 waits for the remaining P11 checks
  (`compute/20261127-32`), the final render, accepted review and publication.
- **Houseprice and Ada.** `compute/20261127-33` is queued for the houseprice CPU-set rerun and Ada P5/E0.
  `tasl2-cpuset-mlgym_houseprice-20261127` has two of the required three seals. Ada P5 previously stopped at the
  lease check. Check fresh capture IDs, S14 PASS, accepted P5/E0 and timing records and the published phase-1 note.
  H200 job `760065` was removed unmatched. The fetched receipts have no E-INT launch ID for `compute/20261127-28`.
- **Writer.** The gate waits for completed eligible G.5 labels, T1 train/dev release, reviewed consumer and
  preregistration bindings, trained and calibrated frozen arms, proof checks and signed test release. Full C1
  awaits the applicable post-freeze read. Once routed, start a task branch at the published manuscript pin,
  attach the released evidence for each filled result, rebuild both drafts and obtain the required fresh review.
  Publication and advancement of the research pin belong to the coordinator.

Job status is from the coordinator queue and recorded receipts. The most recent Compute branch checked was
`17a20d28dc2e2b2857fbb634b42f54bbfd417ae8` and Local was
`adf969cdc436787952206deaa0dc23aca66a0289`. No fresh launch was recorded for the queued reruns.
