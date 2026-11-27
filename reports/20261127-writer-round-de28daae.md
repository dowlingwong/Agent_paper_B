# Paper B writer round close · 27 November 2026

Writer is idle. The research base is `c80f83bc5bc93356dfacadbcb5b186dfb59d028f` and the coordinator queue is
`de28daae61fc781e3b6a18ca40287f26f558a146`. The new card is the Compute screening retry, `compute/20261127-35`.
The writer result-table fill, runbook §3 item 4, has no assigned task ID and waits for authorized results.
The checked manuscript is [paper_B_manuscript main](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)
at `c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`, the same commit as the published `papers/manuscript` pin.

## Published writer tasks

| Task | Delivery branch and tip | Review on record |
|---|---|---|
| `writer/20261126-01` with `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | Restructure re-check ACCEPT WITH MINOR. Corrections applied. The later title and trim had no separate review. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | ACCEPT WITH MINOR. Corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | Independent re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | Independent re-check ACCEPTED. |

All four delivery tips are ancestors of research main. `writer/20261126-02` is covered in the restructure report.
Its changes include determinism-based eligibility, the withdrawal of calendar cutoffs and the rules for shared cards.
Review verdict for this round is not applicable because the draft was rebuilt from the published source without edits.

## Research question and evidence

At the same cap of 20 worker runs and 80 manager calls, how much does each control decision improve the final
configuration? In the published Sweep 1 replay, 3,274 of 4,999 proposals repeated a configuration that had already
been evaluated. That count motivates testing duplicate skipping. D.3 pairs controllers on the same fresh campaign
instances and uses ten fresh audit seeds to measure how much the final configuration improves over the start, in
units of the node's reference standard deviation. A0R − A0 estimates the gain from skipping duplicates and detectable
no-ops under the default keep rule. A2 − A0R estimates what the noise-aware rule adds after those skips. A3 − A2 and
A5 − A2 estimate what adding either learned forecast buys. The paired estimates, intervals and within-family Holm
decisions determine which gains can be claimed. The separate offline gate tests whether those forecasts improve
one-step decisions on logged proposals. D.3b requires arms freeze and its own authorization under either gate verdict.

The D.3 effects, intervals, budget curves and attribution text remain placeholders. So do the gate verdict and estimates,
C1 audit rates, realized T1 populations, hardware and release references, and the pending citation and author fields.

## Draft verification

| Draft | `latexmk` exit | Last main-text page | Total pages | Rebuilt PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate not passed | 0 | 8 | 44 | `e9d113a9702d20782677ee4e4faf06c6665e1dd2584791e82db31c1c1fe6c7d0` |
| Gate passed | 0 | 8 | 43 | `2e350d2be38a659c66b890905a1014b7164648835d2b922ef36371707ad3c3e6` |

Ghostscript text extraction matched the two PDFs in the published research snapshot. Pages 1, 7 and 8 were rendered
and checked for the opening, result tables and transition to references. References begin on page 8 in both builds.
Each log has nine existing overfull box warnings. The logs show no undefined citations or references and no duplicate
labels. `FinalPaper` stopped on the unset gate-outcome switch, as expected (exit 12). `git diff --check` passed.

| Published record | SHA-256 |
|---|---|
| Sweep 1 replay, `docs/r1/reports/MAC_M3_DRYRUNS_20261104.md` | `f39f112c9687f63c6a8c05013b917af847ff1f03a470404942e4fdfea5ac27ea` |
| Claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Frozen D.3 rev 4 pre-declaration | `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745` |
| Signed second screening re-issue | `85d414763f890762628df60a25bfdd1aa2dd0e2ea81662ce31faa45cf2875db9` |
| Screening STOP manifest, from the Compute receipt | `39575f58bf0a2d824b6f2e75bab2075230b03e653396bd0e9c73d5dada05c2c9` |

Decided alone to use temporary Git metadata after the assigned worktree's `FETCH_HEAD` write was refused. All 15
modified paths in the assigned worktree matched published main byte for byte. The worktree and standalone checkout
were preserved. The verification used a temporary export and public records. No evidence jobs were submitted.

## Running elsewhere and blocked

Status is from the coordinator queue, Compute receipts through `17a20d28`, and Local receipts through `edcc15ab`.

| Lane | Last recorded status and next check |
|---|---|
| Screening | Compute owns `compute/20261127-35`, now authorized as an infrastructure retry under R1-SCREEN-COTENANCY-INFRA. The previous run `SMEAS_EVIDENCE_20261127T1550Z` (deepthought tmux `smeas_reissue2`) stopped at 186 of 10,164 written, zero failed, with 9.87 of the required 10 free cores. Check the strict preflight and fresh run stamp. The stopped scene stays sealed and contributes no rows. |
| Expansion G.1b | `compute/20261126-10`, run `g1b-x-tasl-20261126-a`, was last reported running for Titanic (TASL-2 PID `106578`, 84/150 joint runs at 15:33 UTC). ETTh1, MetaMaze and Forest Cover were sealed. Check Titanic's exit and seal, then the combined summary and per-node determinism. |
| Independent Compute tasks | `compute/20261127-34` orders `-33` (houseprice CPU-set rerun, followed by Ada P5 smoke and E0), `-31` (G6 engineering smoke correction), and `-32` (remaining G.5 P11 checks). Check new rerun IDs in the job ledger. `tasl2-cpuset-mlgym_houseprice-20261127` produced two of three attempts. Ada P5 `-29` stopped at its lease pre-check. P.4 phase 1 waits for accepted P5/E0 records, reviewed timing and the signed spec fill. |
| D.3 | Step (8) and every campaign wait for screening. A SHARED decision node goes to the author before binding. Check the corrected per-arm smoke and signed campaign authorizations. D.3b also needs frozen arms. HTCondor jobs `760148`, `760149` and `760152` were removed unmatched. The new preflight needs an eligible ETP L40S or TOpAS A100. |
| G.5 and the offline gate | G.5 waits for the combined accepted P11 record, final binding, accepted render and published note. Houseprice needs S14 PASS. Eligible expansion nodes need reviewed addenda. The gate is unread and waits for G.5 labels, the T1 train/dev release, reviewed consumer and preregistration bindings, trained and calibrated frozen arms, proof checks and test release. P.4 H200 job `760065` was removed unmatched. |
| Paper C E-INT | `compute/20261127-28` waits for staging and the development smoke on an eligible Ada card under Paper B priority. No job ID is recorded. |

Resume result tables on a standalone manuscript task branch when the coordinator routes released D.3, gate or C1
results. Record the authorized source for each filled cell, rebuild both drafts and get the required independent review.
The coordinator publishes manuscript and research revisions to main.
