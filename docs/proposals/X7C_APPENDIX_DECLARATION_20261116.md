# X.7(c) appendix: C3 premises against proposer strength. Declaration before computing (16 November 2026)

**AI-assisted (Claude, Mac agent). Unit S2-M5 of the sweep-2 work plan. Not an author decision.** This file was
committed before the analysis script existed and before any comparison or interval was computed.

**Authority.**
- R1-EXAM-X7 (c) (`author-sweephost-20261116` @ `fd275c53`): "附录 C3 premises vs proposer strength 由 Mac 用 B1/B2 现有
  数据计算，无超出 CI 的差异则报 null" (the Mac computes the C3-premises-vs-proposer-strength appendix from the existing
  B1/B2 data, and reports null if no difference exceeds the CI). Thinking-on results are descriptive only.
- RUNBOOK X.7 (c) names the quantities: "C3 premises (rule-skippable share, increment dispersion, A4 calibration)
  against proposer strength. If the anchors and the finalists do not differ on any C3 quantity beyond CI, the appendix
  reports that null."

**What was seen before this declaration.** While choosing the data sources, I saw per-candidate summary values:
- in the B1 analysis (`07cb62de…`): μ̂ with its cluster interval, `increment_sd`, `a4_brier`, `a4_log_score`, and the
  `diagnostics` counts;
- per-root trial counts in `completion_usage.txt`.

No difference between candidates, and no interval for any quantity below, was computed before this commit.

## 1. Data (existing, read-only)

| Source | Ref and path | sha256 |
|---|---|---|
| B1 manifests, run `7912_20261113_d` (EVIDENCE) | `mac-b1-20261107`: `docs/r1/reports/b1_d_20261113_evidence/b1_manifests.json` | `dc5cd04dfc31758b26bb9ed5ebdec38e80ef06730b304d491c433da18b510e62` |
| B1 per-root trial counts | same dir, `completion_usage.txt` | recorded by the script |
| B1 analysis (cross-check of μ̂ only) | `b1_analysis` of `exam_b2_v2.json` = `complete_batch_verifier.json` | `07cb62de19e0797f197fc658b6043f1ad0fab1aa51e9bb36e054da514f3edffc` |
| B2 manifests, run `8709_20261115_b2` (EVIDENCE) | `ops-b2-exec-20261115`: `docs/r1/reports/b2_exec_20261115/handback/b2_manifests.json` | `1c8d0e575f280262295e999c851ea1ee580b9fdbd4993e5d6e20d05815720213` |
| B2 per-root manifests | same dir, `root_manifests/gemma4_31b/b2/off/*/campaign_manifest.json` (12) | recorded by the script |

## 2. Population and units

- **B1.** All 18 rows:
  - 3 anchors: `random_valid`, `scripted`, `qwen25_coder_7b`;
  - 15 candidates, including the only finalist and pick, `gemma4_31b`.
- **Thinking-off roots only** (mode `off`): 12 roots per row, on nodes `digits_mlp`, `openml_credit_approval`,
  `openml_ionosphere` × instances `s9001`–`s9004`. Every row uses the same 12 instance ids, so clusters pair across
  rows.
- Thinking-on roots are excluded from every quantity (R1-EXAM-X7: descriptive only).
- **B2.** `gemma4_31b` thinking-off roots only: 12 roots on the same nodes × `s9011`–`s9014`. There are no anchors, so
  B2 is a descriptive replication only.

## 3. Quantities (per row)

The "audited" proposals are the manifest's `audited_proposals` with `mode == "off"`. By construction
(`r1/exam/campaign.py`), these are the proposals whose active configuration is neither the incumbent nor already
evaluated.

- **Proposer strength.** μ̂ = mean of `delta_audit` over audited off proposals, as in the B1 analysis. The script
  checks it against the analysis to 1e-12.
- **Q1, rule-skippable share.**
  - Definition: Σ_r (trials_r − audited_r) / Σ_r trials_r over the 12 off roots.
  - trials_r comes from `completion_usage.txt`. audited_r is the count of audited off proposals with that instance
    id.
  - These are the proposals the A2 rule layer skips: a configuration hash already evaluated, or equal to the
    incumbent (C3_DESIGN §3, §5 A2).
  - If an off root is missing from the usage table, or the Σ trials_r differ from the manifest's off-root trial count
    when no on roots exist, that is a STOP.
- **Q2, increment dispersion.**
  - Primary: the sample sd (ddof 1) of `delta_audit` over audited off proposals, pooled over nodes, as the B1
    analysis's `increment_sd`.
  - Secondary, descriptive: the per-node sd.
- **Q3, A4 calibration.**
  - Primary: the Brier score of `p_delta_positive` against 1[`delta_audit` > 0], over audited off proposals with a
    forecast.
  - Secondary: the log score, as in the B1 analysis.
  - Q3 is defined only for rows with forecasts. `random_valid` and `scripted` have none, so Q3 is not applicable to
    them. The forecast coverage is reported per row.

## 4. Intervals and the null decision

- **Bootstrap.** A paired cluster bootstrap over the 12 instance ids. Each resample draws 12 ids with replacement,
  and every row is evaluated on the same draw. Each quantity is recomputed from the resampled clusters' proposals and
  trials. B = 10,000 resamples; `numpy.random.default_rng(20261116)`; percentile intervals (`numpy.quantile`,
  linear). The quantity's value on a resample with no eligible proposal is NaN, and NaN resamples are dropped and
  counted.
- **Comparisons for the null decision (X.7 (c)).** The finalist `gemma4_31b` minus each anchor, on each applicable
  quantity:
  - Q1 × 3 anchors;
  - Q2 × 3 anchors;
  - Q3 × `qwen25_coder_7b` only.

  That is 7 comparisons.
- **Decision rule.** A comparison "differs beyond CI" if the 95 % percentile interval of the paired difference
  excludes 0.
  - If no comparison differs, the appendix reports the null: "the finalist and the anchors do not differ on any C3
    quantity beyond CI".
  - Otherwise it lists each differing comparison, with its point difference and interval.
- **Multiplicity, descriptive only.** Intervals at level 1 − 0.05/7 (Bonferroni over the 7 comparisons) are also
  reported. They do not change the decision.

## 5. Descriptive parts (not part of the decision)

- **Against proposer strength.** For all 18 rows: Q1, Q2 and Q3 with their 95 % cluster intervals, next to μ̂ and its
  interval. The table is ordered by μ̂, and gives the Spearman ρ between each quantity and μ̂ (Q3 over rows with
  forecasts only). With n = 18, and 16 for Q3, ρ is descriptive, with no test.
- **B2 replication.** `gemma4_31b`'s Q1, Q2 and Q3 on B2, with 95 % cluster intervals (B2's own 12 instance ids,
  same bootstrap settings), next to its B1 values.
  - Q1's trials come from each root manifest's `diagnostics.trials`.
  - B2's audits use K = 10 seeds (9201–9210) against B1's K = 4 (9101–9104), so Q2 and Q3 are not on the same audit
    noise. This is stated, not corrected.

## 6. Limits declared in advance

- Twelve clusters per row: the percentile intervals are wide and may undercover.
- The instances are shared across rows, which the pairing uses. The nodes are three D21 nodes only.
- Q1 counts trials of all kinds, including invalid ones. The share depends on how many trials a root used (W = 20
  runs, invalid trials included), as recorded.
- Q2 pools nodes with different metric scales. The per-node sds are given for that reason.
- The finalist was selected on B1/B2 data (winner's curse, R1-MAIN-PROPOSER (i)). The appendix describes premises and
  claims nothing about strength.

## 7. Outputs

- Script: `r1/scripts/x7c_appendix.py`, committed before its run.
- Output: `docs/r1/reports/x7c_appendix_20261116/x7c_output.{json,md}`.
- Report: `docs/r1/reports/X7C_APPENDIX_20261116.md`, with the decision stated by the rule above.
