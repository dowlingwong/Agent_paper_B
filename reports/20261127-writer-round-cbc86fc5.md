# Paper B writer round close · 27 November 2026

Writer is idle. Research base `cbc86fc5b628ed328b1889f42e7b4e0235c004f3`, coordinator queue
`8a545b5868efc34873d772830ffd3adc1798b0ff`. All five writer cards are published. Runbook §3 item 4,
result-table fill, has no issued writer card and still awaits released campaign, gate and C1 results.
The manuscript checked here is [paper_B_manuscript main](https://github.com/dowlingwong/paper_B_manuscript/tree/c2a7de3456a88605ae3ac6284b33dbe3498c8ae5)
at `c2a7de3456a88605ae3ac6284b33dbe3498c8ae5`, the published research submodule pin.
No manuscript change or evidence job was submitted in this round.

| Task | Published delivery branch and tip | Review on record |
|---|---|---|
| `writer/20261126-01` with `writer/20261126-02` | `writer-20261126-01-manuscript-restructure` @ `e360d425752334c56cfaba8ff9499315ca15ea8e` | Restructure re-check ACCEPT WITH MINOR, corrections applied. The later title and trim had no separate review. |
| `writer/20261126-03` | `writer-20261126-03-claim-table-sheet` @ `acf7d37be0cdddc29f157c311b337807f9cbea0a` | ACCEPT WITH MINOR, corrections applied. |
| `writer/20261127-01` | `writer-20261127-01-sources-and-27nov-rows` @ `e8dc1e36a09b61e9410132f23551064f1661e769` | Independent re-check ACCEPTED. |
| `writer/20261127-02` | `writer-20261127-02-codex-manuscript-edits` @ `e3af70a495816c3d107f013b9ee2c17593600bae` | Independent re-check ACCEPTED. |

All four delivery tips are ancestors of research main. The restructure report covers the shared-card, run-budget and
step-order rules in `writer/20261126-02`. This round rebuilt published source without edits and has no new review verdict.

## Question, measurement and claim

At the same cap of 20 worker runs and 80 manager calls, how much does each control decision improve the final
configuration? In the published Sweep 1 replay, 3,274 of 4,999 proposals repeated a previously evaluated configuration.
That observation motivates testing duplicate skipping. D.3 matches controllers on
the same fresh campaign instances and measures the gain from start to final configuration on ten fresh audit seeds,
in units of the node's reference standard deviation. A0R − A0 measures the effect of skipping duplicates and
detectable no-ops under the default keep rule. A2 − A0R measures the additional effect of the noise-aware one-step
rule. A3 − A2 and A5 − A2 measure what either learned forecast adds. The paired estimates, intervals and
within-family Holm decisions will determine the supported claims. The separate offline gate tests one-step utility
on logged proposals. D.3b requires frozen arms and its own authorization under either gate verdict.

The newly published G.1b expansion run `g1b-x-tasl-20261126-a` completed 460/460 runs per node on TASL-2 CPUs.
All four nodes passed determinism and qualify for G.5 addenda. The two MLGym nodes, Titanic and MetaMaze, enter
the arms and primary gate after joining under S9. The two 1GC nodes, ETTh1 and Forest Cover, get separate label
rows. The D21 funnel measured four and qualified zero. The appendix noise-floor and funnel fields can cite the
published expansion result when assembled with the earlier node records. The realized gate input still requires
the G.5 addenda, completed labels and authorized release.

The D.3 effects, intervals, budget curves and attribution text, offline gate verdict and estimates, C1 audit rates,
realized T1 populations, run hardware and release references, and pending citation and author fields remain open.

## Draft verification

| Draft | `latexmk` exit | Last main-text page | Total pages | Rebuilt PDF SHA-256 |
|---|---:|---:|---:|---|
| Gate not passed | 0 | 8 | 44 | `5ca587f53280911bc30705df9318ba2264fcb23cd0d671ef6a5f4fa7b25ef00a` |
| Gate passed | 0 | 8 | 43 | `3df2926b25b51c254d48ea396577e3048dc4878f86e39e005b15cf7dca7293d3` |

Ghostscript text extraction matched both published research-snapshot PDFs. Pages 7 and 8 were rendered and inspected
in both drafts. References start on page 8. The logs show nine existing overfull boxes in each draft and no undefined
citations or references or duplicate labels. `FinalPaper` stopped at the unresolved gate outcome (expected exit 12).
`git diff --check` passed. The 15 modified paths in the assigned research worktree matched published main byte for byte.
Decided alone to use temporary Git metadata after the shared `FETCH_HEAD` write was refused and to build a temporary
export of the pinned manuscript. The verification used the manuscript and public records.

| Published record | SHA-256 |
|---|---|
| Sweep 1 replay, `docs/r1/reports/MAC_M3_DRYRUNS_20261104.md` | `f39f112c9687f63c6a8c05013b917af847ff1f03a470404942e4fdfea5ac27ea` |
| Claim-to-table sheet | `23e9ca0b410c7db1ca46554b9cffbb59f5f6592feef061d56264176ccb6ce9c7` |
| Expansion record, `docs/r1/reports/g1b_x_20261127/G1B_X_RESULT_20261127.md` | `2328994a0dcb4c95bf61715a26124b2dfaec6eaa60de994d46c72daecdee0ebd` |
| Expansion review, round 2 ACCEPTED | `346f079c2fdf6960d5d68fd650706920cf0a96e847d13794279f4578d2f3893a` |
| Frozen D.3 rev 4 pre-declaration | `e091b1b59fafd29ca2f5950d48641611491082a62252268cca2f5c19146b9745` |
| Signed second screening re-issue | `85d414763f890762628df60a25bfdd1aa2dd0e2ea81662ce31faa45cf2875db9` |
| Screening STOP manifest, as recorded in the Compute receipt | `39575f58bf0a2d824b6f2e75bab2075230b03e653396bd0e9c73d5dada05c2c9` |

## Other owners and next checks

Status from the published queue, Compute receipts through `17a20d28` and Local receipts through `edcc15ab`.

| Lane | Recorded status and next check |
|---|---|
| Screening | Compute has `compute/20261127-35` first. Look for the new stamp and strict preflight. The previous attempt `SMEAS_EVIDENCE_20261127T1550Z` (deepthought tmux `smeas_reissue2`) stopped at 186 of 10,164 written, zero failed. Its scene stays sealed under R1-SCREEN-COTENANCY-INFRA. |
| Expansion G.1b and G.5 | `g1b-x-tasl-20261126-a` is complete and sealed, including Titanic PID `106578`. Local owns the G.5 addendum switch and four drafts (`local/20261127-29)). Publication requires the main G.5 note and its checks. Houseprice still needs S14 PASS. |
| Other Compute work | `compute/20261127-34` orders `-33` (houseprice CPU-set rerun, then Ada P5 and E0), `-31` (G6 engineering smoke correction), and `-32` (remaining G.5 P11 checks). Check the new receipts and job IDs. Houseprice attempt `tasl2-cpuset-mlgym_houseprice-20261127` supplied two of the three required attempts. Ada P5 `-29` stopped at its lease pre-check. P.4 phase 1 needs accepted P5/E0 records, reviewed timing and the signed spec fill. H200 job `760065` was removed unmatched. |
| D.3 | Step (8) and the campaigns await the screening result. A SHARED decision node goes to the author before binding. Check the corrected per-arm smoke and signed campaign authorizations. D.3b also waits for arms freeze. HTCondor preflight jobs `760148`, `760149` and `760152` were removed unmatched. Check for an eligible ETP L40S or TOpAS A100. |
| Offline gate and C1 | The gate is unread. It waits for G.5 labels and T1 train/dev release, reviewed target-consumer and preregistration bindings, trained and calibrated frozen arms, proof checks and the signed test release. C1 awaits its applicable release. |
| Paper C E-INT | Compute owns `compute/20261127-28`. Check Ada staging, development smoke and the new job ID under Paper B priority. The published receipts give no launch ID. |

When the coordinator routes a released result, resume from the published manuscript pin on a manuscript task branch.
Record the evidence source for each filled cell, rebuild both variants and obtain independent review. The coordinator
publishes manuscript revisions and updates the research pin.
