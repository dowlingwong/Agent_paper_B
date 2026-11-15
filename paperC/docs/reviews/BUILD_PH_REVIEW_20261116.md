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

---

# Round 2 (16 Nov 2026)

Reviewed `41a9205`: the response table `BUILD_PH_RESPONSE_R1_20261116.md`, `census.py` (schema `paperc_census/v2`),
`test_census.py`, `census_v1.json`, and the rewritten report.

## What I checked

**Commands:**
- The full test suite: 89 passed.
- `python -m paperc.census` then `git diff --stat`: no diff.

**Re-runs.** I re-ran my round-1 scripts on the pinned data. These outputs all equal the v2 JSON:
- `join2` and `s05rule`: 0 logged-action mismatches; false and missed keeps; S0.5-rule flips 0 / 4;
- `curse` and `perkeep`;
- `trial1`: pooled over 60 roots per node, drop medians −41.3 / −63.0 σ and net +1.69 / +0.81 σ;
- `tails`;
- `bymode` and `quant`: per-mode duplicates, comparisons, keeps per campaign and campaigns without keeps; kept-increment
  medians.

**Other sources.** C3 pilot counts, E1b contrasts (`always_verify − rho`, `oracle_naive − rho`, divided by σ_d) and
S1.1 interactions all match the JSON.

**Report vs JSON.** I checked every number in report §1–§5 against `census_v1.json`. All match up to rounding: the
§2 trial-1 table, the §3.1 Track S table, the §3.2 sweep/C1 table, the per-mode table, §3.3, §4 and §5.

**Inputs.** The §7 object ids agree with `git rev-parse` on the files I sampled: digits S0.4 rows, tabular S0.5
roots, tabular S1.1, the C1 composite, the `none` ledger tree, the E1b vary analysis and the C3 pilot audits.

**C1 field definitions.** I read `r1/noise/e1_report.py` @ `10742f8`. I also recomputed ionosphere's five edits from
the C1 common run's `runs.jsonl`: sd(d) equals the logged `sd_joint` (0.01399 for the first edit) while the c0 seed
sd is 0.0410.

**Status of the round-1 findings:**
- **Resolved:** 2, 5, 6, 7, 8, 9, 10, 11 and 12.
- **Resolved in structure:** 1 and 3. The sources are now read, and the band, the misspecified flag and `"inf"` are
  in place. But the C1 numbers are computed in the wrong unit (R2-1).
- **Finding 4:** the stakes part is resolved. The units part rested on my misreading of C1 (R2-1).

**Corrections to my round 1:**
- Finding 6: there are 11 ties among the digits missed keeps, not 10. The census is right.
- Finding 4(a) and my suggested formula sd_joint·√(2(1 − ρ_joint)) were wrong; see R2-1.

## Findings

**R2-1. MAJOR — The C1 "paired sd" double-counts the pairing, so every "paired" number in v2 is in a wrong unit.**
`census.py:18–21, 30–31, 245–256, 378–399`; `test_census.py` (`test_c1_paired_and_node_level_v_star`); report §3.2
(paired columns), §4.3, §4.4, §5 columns 2–3.

*Why it is wrong.*
- In C1, the per-edit `sd_joint` already is the sd of the paired difference d_s = m(c_k, s) − m(c0, s) over 30 joint
  seeds. Its docstring calls it "the noise of one paired comparison" (`e1_report.py`). `rho_joint` is the
  correlation of the two configurations' metrics.
- Multiplying `sd_joint` by √(2(1 − ρ)) therefore applies the pairing a second time. The result has no meaning. For
  ionosphere edit 1 it gives 0.0041, against the true paired sd of 0.0140.
- The executor took this formula from my round 1. The error is mine.
- **σ_d is itself a paired unit.** On all 8 nodes, the sweep's σ_d equals exactly the median `sd_joint` over the
  node's *material* edits. Track S's σ_node equals the median over *all* five edits; this is why tabular has σ_d =
  1.87 σ_node. So the round-1 caveat, that σ_d is a configuration's seed sd, was also wrong.

*What changes.* Taking instead the median `sd_joint` over all five C1 edits, the paired sd in σ_d units is:

| Node | paired sd (σ_d) |
|---|---|
| digits_mlp | 1.00 |
| tabular_mlp | 0.54 |
| openml_climate | 3.72 |
| openml_ionosphere | 0.38 |
| openml_sonar | 0.29 |
| openml_wdbc | 0.09 |
| openml_credit_approval | 0.20 |
| openml_breast_w | 0.037 |

With that unit:
- **Near-0 in paired units** becomes 0.58–0.82 on the OpenML nodes. In v2 it is 0.35–0.74, numerically just the
  exact-zero share on four of them.
- **Kept increment in paired units** becomes 0.38 on credit_approval, 0.29 on ionosphere, 0.62 on sonar, 0.24 on
  climate, 1.2 on wdbc and 3.5 on breast_w. In v2 it is 0.45–65.
- **Node-level price/V\*** becomes "misspecified" on credit_approval, ionosphere and climate, and 0.75 / 0.97 / 1.06
  on sonar / wdbc / breast_w.
- In σ_d, the material-edit unit, five OpenML nodes are misspecified.
- So "inside the band on five nodes" (§4.3, §5) does not hold.
- §4.4's withdrawal of "keeps inside the noise" is reversed on the two nodes round 1 proposed: there, kept increments
  are below the paired noise. The low-stakes reading stands.

*The noise is strongly edit-dependent.* On the OpenML nodes other than climate, `sd_joint` / σ_d is about 0.02–0.4
for small C and `class_weight` edits, and about 0.55–2.2 for `model_type` edits. On climate the figures are 1.0–3.7
and 9–15. The observed increments are a zero-inflated
mixture. A single node-level unit, or a normal node-level forecaster, therefore cannot settle E1 there.

*Fix:*
- Use `sd_joint` directly.
- State that σ_d is the median paired sd of material edits, and report the all-edit median as a bracket.
- Regenerate the JSON and the §3.2 and §5 columns.
- Rewrite §4.3 as "E1 on OpenML is not determinable from node-level fits (unit-dependent; zero-inflated
  increments)", and §4.4 accordingly.
- Correct the docstring and the fixture test.
- Add a test that σ_d equals the median material-edit `sd_joint`.

**R2-2. MINOR — "Stakes on the CPU nodes are small" over-generalises to digits and tabular.** Report §4.1 (line 131),
§6.4 (line 181).
- There, the net campaign gain (0.8–1.7 σ_node) is measured on campaigns that spent their budget recovering from
  trial 1. It is confounded, a lower bound for a guarded loop, not a stakes measurement. §6.1 says this correctly.
- "OpenML kept increments 0.08–0.18 σ_d" leaves out climate, at 0.88.

*Fix:* limit "small stakes" to the OpenML nodes other than climate, and call the digits/tabular stakes confounded.

**R2-3. MINOR — The incumbent-interaction priority rests on factorials of standard edits.** Report §4.5 (line 151),
§6.3, §5 interaction column.
- S1.1 shows that 2×2 interactions among standard edits exist (30 seeds) and are comparable to main effects.
- It does not measure campaign-level headroom from exploiting them, so "the one non-myopic channel the census
  measures directly" overstates it.
- Units are mixed in §5. Tabular's interactions are in σ_node (0.0019) but its stakes are in σ_d (0.0036): 2.57 σ_node
  is 1.37 σ_d.

*Fix:* say that "the mechanism exists at main-effect scale; its control value is unmeasured", and use one unit per
row.

**R2-4. MINOR — Caveats missing from the trial-1 table.** Report §2.
- **Independence.** "60 campaigns" per node includes 20 S0.5 static roots. Their action sequences and y_terminal are
  identical to the a2u roots (S0.5 summary §4), so there are at most 40 distinct campaigns per node. The medians are
  unaffected.
- **Seeds.** The sweep row compares the trial-1 metric at instance seeds with the C1 default at the C1 default seed.
  The start configuration's own seed sd is 1.55 σ_d on digits, 3.40 on tabular, and 0.55–7.3 on the OpenML nodes
  (climate 7.3). The digits/tabular drop is still clear. The OpenML row (−1.4 … +2.4 σ_d) is within seed variation
  and cannot show a trial-1 effect either way.

*Fix:* add both caveats.

**R2-5. MINOR — Small number mismatch.** §4.3 gives "0.02–0.03 under every noise assumption" for digits/tabular, but
the A2-U price/V\* on digits is 0.037.

*Fix:* write 0.02–0.04.

## Verdict

Everything else is now sound: the trial-1 artefact, keep-rule consistency, missed-keep magnitudes, the selection-bias
measure, per-mode statistics, budget, inputs, adapters and tests. A round 3 can be narrow: R2-1, plus wording for
R2-2 to R2-5.

Verdict: NOT ACCEPTED
