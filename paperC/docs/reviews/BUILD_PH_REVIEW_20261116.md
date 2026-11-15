# Build review — PH headroom census (16 Nov 2026)

**AI-assisted (Claude, independent reviewer; did not write PH). ENGINEERING_ONLY.** Reviewed commit `cb2e837` on
`paperc-build-20261115`. HEAD moved to `b6421d3` (P3) during the review; the census code, test, JSON and report are
byte-identical between the two. No file other than this review was changed.

## What I checked

**Read:** `BUILD_RUNBOOK.md` (PH), reframe proposal §1 and §4, `paperc/census.py`, `tests/test_census.py`,
`census/census_v1.json`, `reports/HEADROOM_CENSUS_20261116.md`, Track S S0.5 summary
(`origin/mac-tracks-s05-summary-both-20261115`, §2–§5), and Track S code `r1/tracks/{a2u,collect}.py` at `fab88fc`.

**Commands:**
- The full test suite: 78 passed.
- `python -m paperc.census` then `git diff --stat`: no diff, at both commits.

**Independent recomputation.** Scratch scripts in `/tmp/phrev/` read the pinned blobs with `git show`.
- **Track S S0.5, E1/E2/budget.** Every number reproduces, and matches the S0.5 summary §2/§4:
  - eligible E1 298 / 330; V\* median 2.702 / 4.149 σ, range 0.036 / 0.018 σ; margin 2.576–2.612 / 4.038–4.056 σ;
    `margin == V* − g` holds;
  - skips are all `rule_duplicate` (429 / 399);
  - E2 actions 148/170/53 and 158/192/51; near 0: 46/298 and 38/330; m̂ p05/p95 −0.108/0.114 and −0.055/0.034;
  - binding share by W as in the summary.
- **S0.4 join.**
  - The decision `index` is the proposal index: skipped proposals consume indices. The rows' `budget_index` uses the
    same index.
  - After the `tracks_` prefix is stripped, rows map one-to-one onto E2 keep/discard decisions with index > 1:
    165 / 165 and 154 / 154, with no unused rows. Trial 1 and the 25 / 9 `failed_invalid` E2 decisions have no row.
  - Independent confirmation: in all 20 campaigns, Σ over keeps of Δ_audit equals y_terminal − y_after_trial1 to
    0.00, because both use the same S0.4 audit seeds.
- **S0.4 keep rule.**
  - S0.4 ran `ExecuteNonRuleController` with prior `None`. That controller keeps by `default/v1`, Δ̂ > 0
    (`a2u.py:761–782` @ `fab88fc`).
  - The logged actions equal (Δ̂ > 0) on every row. The logged m̂ disagrees with the action on 14 / 9 rows.
  - So the census's reference rule is the rule actually used; it is not A2-U's m̂ > 0, which only S0.5 used.
  - False-keep and missed-keep rates reproduce: 0/75 and 15/90 (clear-sign 0.083); 1/68 and 7/86 (clear-sign 0.052).
- **Sweep 1** (own parser, 288 ledgers).
  - All recomputed fields match: comparisons, near-0 and exact-0 shares, keep share, duplicate share, plain and
    robust V\*.
  - Trial 1 is valid and kept, with `delta_vs_best = None`, in every campaign.
  - All 526 invalid trials are `failed_invalid` with a null delta.
  - Every keep has delta > 0, and σ_d is identical in both manifests.
- **Report vs JSON.** Every number in the §2, §3 and §5 tables matches `census_v1.json` up to rounding.
- **Additional sources inspected** (not read by the census):
  - the C1 composite `results/r1/noise/D28_REPAIR_20261027/summary.json` @ `10742f8`;
  - `results/r1/engineering/c3_audit_pilot_20261019T001338Z/`;
  - `results/r1/pilot/E1b_*/` (`audits/`, `leaves/`, `analysis.json`);
  - `results/r1/tracks/*/s11/*.json` @ `fab88fc`.

## Findings

**1. MAJOR — Sources that are in the clone were neither read nor listed as missing.** Report lines 12–15;
`census.py:5–16`. The runbook done-criterion says "all available sources covered or listed as missing", and these
sources bear directly on the report's claims.
- **C1 30-seed noise floor.** It is a runbook-listed input, at `results/r1/pilot/E1_20261022T214606Z/` +
  `E1_D28_{REPAIR,CLIMATE}_20261027/`. Its composite is the very file the sweep manifest cites for σ_d.
  - It carries per-edit `rho_joint`, `flip_emp` and `decision_regret`.
  - The mean single-seed sign-flip rate on the standard edits is 0.20–0.60 on the OpenML nodes and 0.11–0.14 on
    digits/tabular.
- **C3 audit pilot.** 166 LLM proposals, each audited on 6 fresh seeds. On the random-selection rows, keeping by
  Δ̂ > 0 gives:
  - tabular_mlp: false keeps 7/21, missed keeps 20/48;
  - digits_mlp: false keeps 2/11, missed keeps 4/13;
  - openml_breast_w: false keeps 0/7, missed keeps 29/47.

  These are an older harness, other node versions and a tiny sample. Even so, the result contrasts sharply with
  Track S's 0–1.5 % false keeps.
- **E1b pilots.** They hold incumbent audits plus verify/continue leaves on digits, ionosphere and breast_w. The
  `E1b_vary_ionosphere_20261012` analysis gives verify − continue = −0.0007 (≈ −0.02 σ_d) and an oracle headroom of
  +0.001. That is on a node §6 proposes for the verify-centred confirmatory test.
- **Track S S1.1 factorials.**
  - The digits pairwise interactions are 0.0057, −0.0035 and 0.0082 (≈ 0.9, −0.5, 1.2 σ_node), and every CI excludes 0.
  - On breast_w, `max_iter` has main effect 0, which explains exact zeros.
  - These feed the map's interaction axis and the incumbent channel.

*Fix:* read these sources (C1 at least), or list each one with a reason for excluding it. Then reconcile §4/§6 with
what they show.

**2. MAJOR — The unconditional trial-1 keep is not reported, and it shapes the "heavy-tail regime".** Report lines
68–74; `census.py:211–232`.
- **Track S, all 120 campaigns** (S0.4 + S0.5, both nodes). The audited y_after_trial1 − y_start is −35 to −84 σ_node
  (median −41 on digits, −59 / −65 on tabular). Campaigns end only a median +0.4 to +2.4 σ_node above y_start.
  - So most recorded gains (≈ 40–100 σ) are recoveries.
  - 48–55 % of audited increments are positive.
  - The > 4 σ tail is 14.5 % positive vs 21.8 % negative (digits), and 22.1 % vs 42.9 % (tabular).
  - "Mostly bad … chiefly broken or degraded edits" (line 69) overstates this.
- **Sweep 1.** On digits/tabular, the trial-1 metric is a median ≈ 10–12 σ_d below the C1 default metric, and the
  median recorded gain after trial 1 is 13.5 / 9.4 σ_d. The OpenML nodes show no such drop.
- **Why it matters.**
  - Track S's near-perfect keep quality (corr 0.94 / 0.90) is plausibly a product of large recovery increments
    (cf. finding 1, C3 pilot).
  - Paper B STATUS lists "the trial-1 unconditional-keep item" as open.

*Fix:*
- Report the trial-1 drop per node and source.
- State that the heavy-tail placement and the keep-quality numbers are conditional on it.
- In §6, add guarded trial-1 acceptance (comparing against the start configuration) as a channel candidate and a
  confound for the digits contrast.

**3. MAJOR — The E1 conclusion contradicts the proposed threshold, and the "∞" values are an artefact of the noise
model.** Report lines 58–60, 81, 110–113; `census.py:278–288`.
- **The contradiction.** By the §6.4 rule (price/V\* ≥ 0.3), six OpenML nodes pass: five at ∞ and climate at 0.59.
  Line 113 nevertheless says "none passes for E1".
- **The artefact.** ∞ arises because the measurement sd is fixed at 1 σ_d. That is larger than the observed
  increment sd (0.17–0.66 σ_d) on five of the six OpenML nodes, which forces τ = 0. Observed variance below the
  assumed noise variance means the model is misspecified; it is not a measurement that V\* ≈ 0.
- **Sensitivity.** I set the measurement sd to C1's approximate paired sd, sd_joint·√(2(1 − ρ_joint)), median per
  node. That gives price/V\* of:
  - 0.30 on climate, 0.63 on sonar, 1.06–1.08 on wdbc and breast_w, 4.7 on credit_approval;
  - ∞ on ionosphere;
  - unchanged on digits/tabular (0.02 / 0.03).

  So these nodes sit near the band, not in a degenerate corner.
- Exact zeros (33–74 %) are inert edits, which is what a per-proposal screen would act on.

*Fix:*
- Define the E1 criterion as a two-sided band.
- Correct line 113.
- Show ∞ as "misspecified (observed sd < assumed noise)", and report the sensitivity to the measurement sd.
- In the JSON, encode ∞ explicitly. `_r` (`census.py:126–127`) currently writes `null`, which reads as missing.

**4. MAJOR — The "noise-dominated" reading and the choice of confirmatory nodes rest on the wrong unit and ignore
stakes.** Report lines 62, 76–80, 89–98, 104.
- **Units.**
  - σ_d is the seed sd of one configuration. Fixed-seed paired differences are much less noisy on these nodes: C1's
    median paired sd is ≈ 0.05–0.5 σ_d.
  - So "within ±0.5 σ_d" is not "inside the noise". The line 79 claim, "largely a draw on noise … recorded value is
    likely optimistic", goes beyond what the line 62 caveat allows.
  - Conversely, Track S's comparison noise is sd(Δ̂ − Δ_audit) = 3.0 / 9.8 σ_node (robust 1.5 / 2.65). Its ±0.5 σ_node
    band is therefore narrow relative to noise.
  - The §5 near-margin axis compares across scales: tabular_mlp itself has σ_node 0.0019 but σ_d 0.0036.
- **Stakes.** Near-margin mass measures how hard a decision is, not what it is worth.
  - On credit_approval and ionosphere, kept increments are a median 0.08 / 0.11 σ_d.
  - Campaigns make about 1.2–1.7 keeps after trial 1 under memory `append_only_summary`, and 0.06–0.11 under `none`.
  - Under `none`, 89–94 % of campaigns on these two nodes keep nothing after trial 1.

*Fix:*
- Put margins in a paired-noise unit per source (C1 ρ_joint, the audit pilots, or the Track S audits).
- Add a stakes column, for example E|Δ| over near-margin comparisons per campaign, or C1 `decision_regret`.
- Soften §4.2 and §6.2 until the audits in §6.3 exist.

**5. MINOR — The S0.4 and S0.5 keep rules differ, and the report does not say so.** Report line 32;
`census.py:196, 206`.
- Keep quality comes from S0.4, which kept on Δ̂ > 0. The E2 margins come from S0.5, which kept on m̂ > 0.
- Applying the S0.5 prior's Bayes keep to the S0.4 rows flips 0 decisions (digits) and 4 (tabular). Tabular's
  false-keep rate becomes 1.6 % and its missed-keep rate 12.2 % (clear-sign 8.8 %). The conclusion is unchanged.

*Fix:* state the mismatch and the sensitivity, and assert in code that kept == (Δ̂ > 0) for the S0.4 rows.

**6. MINOR — Missed keeps are given as a rate with no magnitude.** Report lines 34, 73–74.
- 10 of the 15 digits missed keeps have Δ̂ exactly 0: ties, discarded by the strict rule.
- Their audited value is a median ≈ 0.4 σ (maximum 2.1 σ).
- Tabular includes one at +41.7 σ (se 12.9 σ).

*Fix:* report magnitudes and the tie share before crediting a verify action with this headroom.

**7. MINOR — The winner's-curse statement overclaims, and the runbook's dependence on keeps is missing.** Report
lines 37, 72; `census.py:211–232`.
- **Overclaim.**
  - The per-campaign standard error is 1.95 σ (digits) and 6.6 σ (tabular), with n = 10; the medians are −3.3 / −7.3 σ.
  - The per-keep mean of (Δ̂ − Δ_audit) is −0.16 ± 0.43 σ (digits) and −0.12 ± 1.34 σ (tabular).
  - So "recorded gains sit about 1 σ below audited ones" is not a supported direction. The supported statement is
    "no winner's curse detected".
- **Missing.** The runbook asks how the curse depends on the number of keeps. It is not computed: the correlation is
  0.19 (digits) and 0.69 (tabular), n = 10.
- **What the measure is.** It equals Σ over keeps of (Δ̂ − Δ_audit) exactly, a differenced, gain-level measure. It
  cancels any shared offset in the recorded trial-1 value, so it is not the incumbent-value curse the runbook names.

*Fix:* report standard errors and the per-keep measure, add the keeps dependence, and state what the measure is.

**8. MINOR — Pooling the two memory modes hides a first-order effect, and the duplicate claim is mis-stated.**
Report lines 84, 114; `census.py:252–262`.
- Duplicates are 80–85 % under `none` and 33–55 % under `append_only_summary`. "About 60 % on every node" is a mix of
  the two.
- Under `none`, the OpenML campaigns yield 1.4–2.8 non-duplicate comparisons each.
- Track S's rule layer already skips all duplicates at no run cost: every one of its 429 / 399 E1 skips is a rule
  duplicate. So "not something a gate can exploit" is wrong.
- The census counts patch-level duplicates, whereas Track S counts configuration-level duplicates.

*Fix:* add per-mode columns, reword the duplicate claims, and name the duplicate definition.

**9. MINOR — Budget: no shadow price is given, and the "remaining headroom" wording conflicts with the S0.5
summary.** Report line 74.
- The S0.5 summary §4 found that a binding W changes where campaigns stop, not any decision.
- Under a constant V\*, the shadow price is undefined.

*Fix:* say that the budget matters here only as the price of verify runs, and state that the shadow price is
undefined.

**10. MINOR — The inputs table lacks per-file paths and hashes** (runbook PH step 1). Report lines 7–10.
- The exact directories appear only in the code: `s04_rerun20261111` (not the `s04/` STOP scene),
  `s04_t7_20261114` and `s05_t7_*`.
- The digits S0.4 rows have sha256 `d0f7dae7…`, which matches the prior's `s04_rows_sha256`. That is worth stating.
- The digits S0.4 rows come from TASL-2, while S0.5 ran on TASL-7. The host effect is untested (S0.5 summary §6).

*Fix:* add the input table with paths, blob ids or sha256, and the host note.

**11. MINOR — Tests and structure deviate from the runbook.** `tests/test_census.py:21–23`; runbook step 3.
- Every data test is skipped silently when the pins are absent.
- There are no fixture tests for the adapters: duplicate detection, first-trial exclusion, the S0.4 join, and
  `keeps_without_row > 0`.
- The census reads raw dictionaries rather than P1 records via adapters.

*Fix:* add small synthetic fixtures, and record the P1-adapter deviation in BUILD_STATUS.

**12. MINOR — Smaller precision issues.**
- The robust sd and robust V\* are degenerate (MAD = 0) on nodes with more than 50 % exact zeros. Label them as such
  rather than showing 0.0 / ∞.
- `openml_wdbc` also has 4 `proposal_precondition_failed` failures (report line 61).
- The OpenML nodes entered the pool through D21's P(wrong) ≥ 0.10 rule, so the noise-dominated regime is partly true
  by construction. Say so.

## Answers to the specific questions

- **Is "keep iff Δ̂ > 0" the right reference rule?** Yes for S0.4: it is the rule those campaigns used. A2-U's
  m̂ > 0 applied only in S0.5, and using it would not change the conclusion (finding 5).
- **Is the S0.4 join correct?** Yes: instance naming, index alignment, trial 1 and `failed_invalid` are all handled
  correctly (see the checks above).
- **Is "recorded − audited gain" a meaningful winner's-curse measure?** It is meaningful as a summed per-keep
  selection bias, but it is underpowered and is not an incumbent-value measure (finding 7).
- **Is the sweep parsing correct?** Yes.
- **Are V\* and the exact-zero handling sound?** The computation matches its stated assumptions, but the
  measurement sd of 1 σ_d is the wrong unit for fixed-seed paired differences (findings 3 and 4).

Verdict: NOT ACCEPTED
