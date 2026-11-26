Reviewed base: 74808c0a2ad503254b06957f8508dfe5e8497acc

# Track S — S0.5 summary, both nodes, with three options for the author — independent review record (15 November 2026)

Branch `mac-tracks-s05-summary-both-20261115`, from `trackS-ops-20261030` @ `fab88fce`, merged with `mac-tracks-s05-summary-20261114` @ `3e0fa203` (`6ff456c7`). Report `reports/TRACKS_S05_SUMMARY_20261115.md`: the runbook rev 3.3 Phase 4 values for both nodes, the calibration STOP on both, the tabular policy coincidence, V\* − g, the binding budget, offline diagnostics, and three options with costs and a recommendation for the author. Analysis only. Three rounds by one freshly spawned independent reviewer agent (AI-assisted, Claude).
- Round 1 (`b423d412`): changes requested (1 MAJOR: the tabular out-of-sample support is fragile and the fallback covered only a digits fail; 9 MINOR).
- Round 2 (`1ab43c32`): accepted, with one optional MINOR (asymmetric fallback rule).
- Round 3 (`74808c0a`, symmetric fallback rule): **accepted**, no findings.

Accepted commit (round 3, last): 74808c0a2ad503254b06957f8508dfe5e8497acc

The round texts are reproduced unchanged below.

---

# Independent review R1: `docs/r1/reports/TRACKS_S05_SUMMARY_20261115.md` (Track S two-node S0.5 summary)

Reviewer: independent; I did not write the report. Reviewed base `b423d412` (branch
`mac-tracks-s05-summary-both-20261115`). Read-only: nothing was modified, committed or deleted in any worktree. My
outputs are only in `/tmp/pb/rev_s05both/` (`s05.json`, `indep_cal.py`, this file). No seeds 7001–7010 / 9001–9210
were read. No secrets, network or SSH.

VERDICT: REVISE

One MAJOR finding (the recommendation's fallback plan has a gap, and the tabular out-of-sample support it rests on
is weaker than the report says). Everything else is MINOR. The numbers are otherwise correct and reproduce
independently.

## Findings

### 1. MAJOR: §6 "Tabular" bullet and §7 (a-i) / Recommendation. The out-of-sample support on tabular is fragile, and the pre-declared fallback covers only digits failing

- **What is wrong.**
  - §6 says the S0.4-fitted larger τ0 "reaches the gate on S0.5 in more than half of the S0.4 likelihood region.
    This is the honest test. It passes there." §7 then recommends (a) because it "has out-of-sample support on
    tabular". Step 3 pre-declares only "if digits fails again, Track S continues on tabular alone".
  - The tabular pass is on the edge of the band:
    - At the S0.4 maximum (c 133.35, λ 1.585), stratum 0 coverage is 40/57 = 0.7018. One fewer covered proposal
      (39/57 = 0.684) fails the gate.
    - All 18 failing points in the 2-log-lik region fail on stratum 0 (17 on stratum 0 alone, 1 on 0 and ≥ 3).
      Stratum 0 coverage across the region is 0.63–0.82.
    - With about 57 stratum-0 predictions per S0.5, the binomial SE of a coverage near 0.75–0.80 is about 0.05–0.06.
      So a fresh-seed re-run, which the report rightly recommends, has a substantial chance of failing on tabular
      as well.
    - The 2-log-lik region criterion (`diag2_region.py`) is new in this report and was written after the tabular
      S0.5 data were seen. "26 of 44" is also a count of log-grid points, not a probability mass. It is a
      reasonable descriptive check, but not a pre-declared test.
  - Consequence the author must know: if tabular also fails the re-run, the recommended plan has no declared next
    step. Under the runbook that is a second calibration STOP on the only remaining node, which in practice means
    (c-iii).
- **Evidence.**
  - `diag_2node/diag2_region_tabular.json` (`tau0_only.loglik_region_2.points`): the top points by S0.4 log-lik
    give stratum 0 = 0.7018, 0.7018, 0.7368, **0.6491 (fail)**, 0.7018.
  - Failure reasons over the 18 failing points: `('0',)` × 17 and `('0','>=3')` × 1.
  - I reproduced the ML point and the 26/44 independently: `/tmp/pb/rev_s05both/indep_cal.py` uses the pin's
    `a2u.group_posterior`, with S0.5 group histories rebuilt from the roots' E2 m̂ rather than from μ. It found 0
    n_group mismatches, and the run-prior μ/sd matched to 3.5e-18.
- **Fix.**
  - In §6, soften "This is the honest test. It passes there" to say that the parameter is fitted out of sample, but
    the pass is marginal: stratum 0 is one prediction from the edge at the maximum, and every failing region point
    fails on stratum 0.
  - In §7 (a) Risk and in the Recommendation, state the probability-relevant facts above.
  - Add a pre-declared action for the case where tabular fails the re-run, e.g., "then (c-iii)", or whatever the
    author prefers. The author should decide this before choosing (a), not after the re-run.

### 2. MINOR: §6, sentence after the decomposition table. "Spread" is used for a variance ratio

- "the realised spread is about 3.5 × the predicted spread". The tabulated ratio is MS residual / predicted
  **variance** (3.51, 3.21, 1.01). The spread (sd) ratio is about √3.5 ≈ 1.9×. The accepted digits report words it
  correctly ("3–4 × the predicted variance").
- Fix: write "the mean squared residual is about 3.5 × the predicted variance", or give the sd ratio (about 1.9×).

### 3. MINOR: §6 counterfactual table. λ and row provenance not stated; "3 % on digits" uses the in-sample c

- `vstar_counterfactual.py` holds λ at the run value 1.0 (docstring: "lam fixed"). But the row "digits 34.8 (5.2,
  S0.4 ML)" names the S0.4 ML point, whose λ is 1.39. The tabular rows "133.2" and "170" carry no label: 133.19 is
  the lower edge of the λ = 1 in-sample window, not the S0.4 ML point (c 133.35, λ 1.585).
- The text's "3 % on digits" is the in-sample c = 114.8 row (10/298 = 3.4 %). At the S0.4 ML c it is 5/298 = 1.7 %.
  On tabular, 32/330 = 9.7 % and 36/330 = 10.9 % ("10–11 %" is fine).
- Fix:
  - State "λ held at 1" in the caveat sentence.
  - Label the tabular rows, e.g. "λ = 1 in-sample window edge" and "inside the window".
  - Either quote 2–3 % for digits, or say which c the 3 % refers to.

### 4. MINOR: §6 recalibration table, row 2, tabular cell. The c range is ambiguous

- "26 of 44 pass, all with λ ≥ 1 (c 100–178)". 100–178 is the c range of the whole region (44 points). The
  **passing** points have c 133.4–177.8 and λ 1.06–2.71. The digits cell's "c 14.7–46.4" is also the region range,
  so the pattern is consistent, but the parenthesis reads as describing the passing points.
- Fix: write "(region c 100–178; passing points c 133–178)".

### 5. MINOR: §2 Projection note. The digits t_run is a TASL-2 value

- The digits t_run = 0.9091 s comes from the Phase 0 smoke test on TASL-2 and was not re-measured on TASL-7. The
  accepted S0.1 review says so explicitly (`TRKS_S01_RESULT_AND_S05_K2_REVIEW_20261113.md:130`, "Phase-0 smoke, not
  re-measured on TASL-7"). Digits' remaining work now runs on TASL-7.
- The measured-throughput cross-check partly covers this, but the caveat should be carried.
- Fix: add "(digits: TASL-2 smoke value, not re-measured on TASL-7)".

### 6. MINOR: §5. Two downstream consequences are missing or understated

- **Near band b.** It is degenerate for E1 on both nodes, and S3a uses it:
  - Every eligible E1 |margin| exceeds b: digits min 0.01700 vs b 0.00859; tabular min 0.00767 vs b 0.00385.
  - So the S3a near-threshold oversampling (`collection.near_band_b` in `predecl_template`) would select no E1
    decision under the current prior. Only E2 decisions can be "near".
  - The accepted digits report flagged that b "inherits the degeneracy". This report lists b in §2 without that
    note.
- **S0.6 `--sigma-D`.** "with one of them at 0 the choice now matters" understates the problem:
  - Passing the between-policy UCL (0.0) as `--sigma-D` sets `Plan.sigma_D = 0`.
  - `Plan.n_planned` → `analyze.campaign_n` then raises `ValueError("sigma_D and delta_Y must be positive")`.
    `n_planned` is evaluated when the S0.6 report is built (`simulate_controls.py:709-712`, `:971`, `:1000`;
    `analyze.py:1572-1576`). So that choice would crash S0.6 rather than silently mis-size it.
- Fix: add one bullet on b, and replace "the choice now matters" with the concrete failure.

### 7. MINOR: §7 (a-i). The change is described as replacing "the τ0 floor rule"; the real locus is τ_A2

- **Where τ0 comes from.** In `fit_prior`, τ0 = √max(τ_A2² − τ_w², floor²), with τ_A2 taken from A2's binned
  soft-label moments (`a2u.py:206-235`).
- **Why it sits at the floor.** `labels.moments` computes the sd over 12 bins in σ_node units with tails at ±4
  (`r1/c3/labels.py:112-125`), so τ_A2 is structurally capped at a few σ_node. It is 2.9 σ_node on digits and
  3.4 σ_node on tabular. The S0.4 Δ_audit sd is 0.0597 (≈ 9 σ_node) on digits and 0.0420 (≈ 22 σ_node) on
  tabular. So τ_A2 < τ_w is close to guaranteed, and that is why τ0 sits at the floor on both nodes.
- **What (a-i) would really change.** It would set τ0 ≈ 20 σ_node on tabular, about 6 × τ_A2 (about 1.8 × on
  digits). That cuts the "A2's prior, updated" link that defines A2-U. It is a design-level change to what A2-U is,
  not only an estimator tweak.
- Fix: one or two sentences in §4 ("Same mechanism") or §7 (a) naming this. It helps the author choose between
  (a-i) and (a-ii), and it explains why the problem recurs on every node.

### 8. MINOR: §5 `budget×1` bullet. A small overstatement and a missing value

- "In the W = 40 pilot, r̄ − r never exceeded 0.09". The tabular maximum is 0.093 (digits 0.082), over a2u rep-0
  eligible E1 decisions. Write "≤ 0.093" or "about 0.09".
- For symmetry, give the digits value if the 0.8 extension wins: ≥ 1.31.
- Optional, and supports the report's conclusion: a prefix replay of the recorded decisions at W = 12 gives
  r̄₁ − r ≤ 0.32 on both nodes (r̄₁ ≈ −0.32, min r ≈ −0.64). That is below even the 0.61 tabular-with-extension
  bound. This uses the recorded r and runs_used, assumes N_cap stays 40, and is approximate.

### 9. MINOR: §7 (b) and §4. Wording nits

- §7 (b) "decides on differences of about 1e-5". The V\* range is 3.5e-5 on tabular but 2.3e-4 on digits. Write
  "1e-5 to 1e-4".
- §4 last bullet, "many keeps are close to 0". The 46 / 38 counts are E2 decisions within ±0.5 σ_node of 0, keeps
  and discards together. Write "many E2 decisions are close to 0".

### 10. MINOR: §7 (a) Cost / Decisions. Digits S0.4 host and duration

- "S0.4 about 0.5 h per node" is tabular-based (0.44 h of session time). The digits S0.4 rows took 0.74 h, on
  TASL-2 at k = 1 (manifest session 23:14:13–23:58:32Z).
- §6 itself raises the untested TASL-2/TASL-7 contributor for digits. Whether to refit digits on new TASL-7 S0.4
  rows is therefore a natural item for "Decisions it needs from the author".
- Fix: add it there, and give the per-node S0.4 times.

## Verified as correct

- **s05-summary.**
  - Re-ran the pin's `s05-summary` (pin 8237fd02, harness a3fedbb, `python -P`).
  - The output sha256 is `7a07ccf5…`, byte-identical to the committed `s05_summary_20261115.json`.
  - `analyze.py` sha256 `b952af6c…` is the same at the pin and in the branch. The runbook file sha256 is
    `a93fb84b…`.
- **§2 values.** All match the JSON: binding shares, joint W = 12 (largest candidate binding in ≥ 50 % on every
  primary node, per code `analyze.py:2172-2174`), σ_cmp,vary, between-policy UCL 0, between-repetition UCLs at every
  W, between_policy_sd_at_cap 0, b and n 596/660, λ 1.0, calls/audits 40.0/35.4 and 40.0/38.6, and calibration
  fail on both nodes.
- **Between-repetition pairs.** Recomputed independently:
  - tabular W 12: 8 of 10 pairs exactly 0, the others −0.00144 and −0.00150;
  - tabular W 8: 6 non-zero pairs;
  - all UCLs reproduce: χ² 80 % one-sided, m = 10.
- **λ₂.** Recomputed with the §11.6 snippet: 3.463 (q₉₀ 2.385, n 298) and 3.640 (q₉₀ 2.445, n 330, 0 null).
- **Calibration counts.**
  - Tabular: 21/57, 62/95, 148/178, 231/330.
  - Digits: 35/65, 60/89, 136/144, 231/298.
- **Input hashes and checksums.** Tabular `e05cd54a`, `615aa390`, `5e082a58`, `28e008f6`; prior `ba8f7783`; digits
  prior `5c849d15`. `SHA256SUMS` verifies 40/40 and 17/17. Instance seeds 30500–30519.
- **Projection.**
  - k = 2: 33.97 h and 39.19 h. Sum 73.2 h.
  - k = 1: 22.6 h and 31.5 h. Serial L 0.675453 and 0.698037 come from the S0.1 records.
  - L and t_run inputs match their sources. c = 4 is valid with about 22 free cores.
  - Measured throughput: 3,769 calls (2,000 root + 1,769 leaf) over sessions totalling 2.46 h, and 4,594 calls over
    2.50 h. These give about 52 h and 44 h for 80,000 calls.
- **Runbook faithfulness.**
  - The gate is inclusive [0.70, 0.90], stratum minimum 20, n ≥ 100.
  - The failing stratum 0 and the over-covered ≥ 3 are correctly treated as STOP.
  - λ₂ is correctly called outside the runbook in the mixed case; no STOP item is presented as a runbook option.
  - The fallback is applied per node, with a bounding projection.
  - STOP 4 contents are not claimed as sent.
- **§4 table.** Every value reproduces: identical sequences 20/20 at W 40 and at every truncation; E1 318/429 and
  350/399; all skips `rule_duplicate`; E2 148/170/53 and 158/192/51; V\* − g ranges and σ_node conversions; V\*
  ranges 0.036 and 0.018 σ_node; 0/0/0/0; E2 margin quantiles and 46/38; runs 11–27 and 14–22; LLM cap 20/20.
  `policy_diag.py` on digits matches `diag1.json` on every common key.
- **§4 mechanism.**
  - τ values come from the prior files.
  - The closed form V\* = μΦ(−z) + (τ²/s)φ(z) matches `c3.rules.proposal_value` and `a2u.forecast`.
  - V\* at μ = 0 is 2.79 and 4.41 σ_node. At μ0 it is 2.702 and 4.149 σ_node, equal to the observed medians to
    machine precision.
- **§5 code claims.**
  - Static policies and A2-U at default have b_budget = b_info = 0 (`as_dynamic`; `_decide_e1` static path).
  - The TUNE_G/TUNE_H values give largest g of 0.00334 / 0.00669 and 0.00223 / 0.00446, all below min V\* (0.01766,
    0.00786).
  - The `budget×1` threshold is g − σ(r − r̄₁), and the bounds 1.714 / 1.010 / 0.610 recompute.
  - `info×0.5` uses b_info = 0.5 unscaled, and τ_pred is essentially constant.
  - `plan_sizing` takes max(between-policy UCL, dev UCL), and `predecl_template` feeds the between-policy UCL.
  - `match_noise` gives between_policy_sd precedence, and 0.0 is not None.
  - The shrinkage factors are 0.875 and 0.692.
- **§6 decomposition and recalibration.**
  - Decomposition table and sd reconstruction (3.5e-18) match.
  - Tabular `tau0_only` ML point and its S0.5 coverage match.
  - Region counts: digits 0/102 (stratum 0 0.57–0.60, ≥ 3 0.95–0.99); tabular 26/44.
  - Ties: 0/18 and 0/17. `both`: 0/27 region and 0/98 ties.
  - λ = 1 windows: digits 112.6–114.8; tabular 133.2–211.9, 48 contiguous points.
  - All confirmed both from the committed JSON and by my independent recomputation.
  - `diag2.py` and `diag2_lambda1.py` are byte-identical to the accepted scripts (`81e041c5…`, `c967edee…`).
- **Counterfactual.** All counterfactual numbers match `vstar_cf_*.json`, and the "direction only" caveat is
  present.
- **Wording and scope.**
  - ENGINEERING_ONLY, "Not an author decision" and "Analysis only" are present.
  - The commit `b423d412` adds only docs and results files; no code or pin is changed.
  - Options are left to the author.
  - The S0.5 and S0.4 host-time figures match the manifests (S0.5b about 15 s).
  - Fresh pilot seeds are feasible without code (`collect --seed-base`, block [30500, 31000)).

---

# Independent review R2: `docs/r1/reports/TRACKS_S05_SUMMARY_20261115.md` (round 2)

Reviewed `1ab43c32`, one commit on top of `b423d412`. I read `git diff b423d412 1ab43c32`, which changes only the
report: 1 file, +54/−28, with no results or code files touched. Everything was read-only, and nothing was written
outside `/tmp/pb/rev_s05both/`.

VERDICT: ACCEPT

No BLOCKING or MAJOR findings remain. One new MINOR finding is listed below; it is optional to fix.

## Round-1 findings: status

1. **MAJOR, tabular fragility and fallback: resolved.**
   - §6 now states: 40/57 = 0.702, one prediction from failing; all 18 failing region points fail on stratum 0;
     stratum 0 spans 0.63–0.82 across the region; the region criterion was chosen post hoc; and "26 of 44" counts
     grid points, not probability mass. It concludes "encouraging, not a demonstration".
   - §7 (a) Risk now says tabular could fail too.
   - The Recommendation pre-declares (c-ii) if digits fails and (c-iii) if tabular fails, and still leaves the
     choice to the author.
   - Check: sampling sd "about 0.05" at n = 57 is √(p(1−p)/57) = 0.053–0.061 for p 0.8–0.7. Acceptable.
2. **"Spread" used for a variance ratio: resolved.** The text now says MS residual ≈ 3.5 × the predicted variance,
   about 1.9 × in sd (√3.51 = 1.87).
3. **Counterfactual provenance: resolved.**
   - λ held at 1 is now bold in the caveat.
   - The row labels are correct:
     - digits 114.8 is the top of the 112.6–114.8 window;
     - tabular 133.2 is the bottom of the 133.2–211.9 window, and ≈ the S0.4 ML c (133.35);
     - 170 is near the log-midpoint of the window (168);
     - the digits 34.8 row is flagged as "at λ 1 instead of its 1.39".
   - The 1.7 % (5/298) to 3.4 % (10/298) range is correct.
4. **Tabular c range: resolved.** The text now gives region c 100–178 and passing points c 133–178 with λ 1.06–2.71.
   This matches `diag2_region_tabular.json`.
5. **Digits t_run caveat: resolved.** The TASL-2 caveat is added, citing the accepted S0.1 review.
6. **§5 downstream effects: resolved.**
   - The near band b degeneracy is flagged in §2 and explained in §5. The minimum E1 margins 0.01700 and 0.00767
     both exceed b (0.00859 and 0.00385), as I verified in round 1.
   - The S0.6 `ValueError` is stated. `s06_node` evaluates `plan.n_planned` before computing any control
     (`simulate_controls.py:1000`); only the noise matching runs before it. "Would not run at all" is accurate in
     effect.
7. **τ_A2 as the structural cause: resolved.**
   - §4 now gives the `fit_prior` formula and the `labels.moments` cap. The figures are right: 2.9 / 3.4 σ_node for
     τ_A2, and S0.4 Δ_audit sd 9.0 / 22.1 σ_node.
   - §7 (a-i) is now called a design-level change. The ratios check: 34.8 × 0.00099 / 0.01897 = 1.82, and about 6 on
     tabular.
8. **`budget×1` values: resolved.**
   - The maxima are now 0.082 and 0.093.
   - The digits 0.8-extension bound of 1.31 is correct: (0.017663 − 0.8 × 0.008356) / 0.008356 = 1.314.
   - My prefix replay is cited as the reviewer's and as approximate. The figure 0.32 is below every bound.
9. **Wording nits: resolved.**
   - "1e-5 to 1e-4", with V\* ranges 2.3e-4 and 3.5e-5.
   - "many E2 decisions are close to 0".
10. **Digits S0.4 host and refit question: resolved.**
    - S0.4 times are given per node: 0.45 h on TASL-7 and 0.74 h on TASL-2.
    - The TASL-7 refit question is now in the author's decision list.

## New findings

### R2-1. MINOR: §7 Recommendation step 3. The digits-passes / tabular-fails case is ambiguous

- Step 3 reads: "if tabular fails (alone or with digits), Track S ends before EVIDENCE (c-iii)". Read literally,
  this ends Track S even when digits passes and tabular fails. Yet the mirror case, digits failing, continues on the
  surviving node via (c-ii).
- The asymmetry may well be intended (on present evidence a digits pass is unlikely, and it would rest on no
  out-of-sample support). But the text neither says so nor states that this is the intended rule.
- Fix (optional): either say "if tabular fails, Track S ends (c-iii) even if digits passes, because a digits pass has
  no offline support", or make the rule symmetric: "a node that passes continues alone via (c-ii); if both fail,
  (c-iii)". Either way it stays the author's choice.

## Checked and found no new error

- Every number added in round 2, as listed under items 1–10 above, against the JSON and the pin code.
- No author decision is recorded as made, and the ENGINEERING_ONLY and "Not an author decision" labels are intact.
- No result file changed between `b423d412` and `1ab43c32`, so the round-1 verifications still hold. These include
  the `s05-summary` sha256 `7a07ccf5…`, every table in §2, §3, §4 and §6, the projections, λ₂, and the
  between-repetition pairs.

---

# Independent review R3: `docs/r1/reports/TRACKS_S05_SUMMARY_20261115.md` (round 3)

Reviewed `74808c0a`, one commit on top of `1ab43c32`. I read `git diff 1ab43c32 74808c0a`: the report is the only
file changed (+6/−5), and no results or code files are touched. Everything was read-only, and nothing was written
outside `/tmp/pb/rev_s05both/`.

VERDICT: ACCEPT

There are no BLOCKING, MAJOR or MINOR findings.

## R2-1 (MINOR, asymmetric fallback): resolved

- **What changed.**
  - The headline now reads "(c-ii) if one node fails, (c-iii) if both fail".
  - Step 3 now reads "a node that passes continues alone (c-ii); if both fail … (c-iii)". It adds that tabular is
    the likely single-node case, but that a digits pass would be "unexpected, not excluded".
  - The headline and step 3 agree with each other.
- **Consistency with the rest of §7.**
  - (c-ii) is still described as "drop a node … helps only together with (a)" (line 291). Its tabular-only example
    is an instance of the symmetric rule and does not contradict it.
  - (c-iii) matches the both-fail branch.
  - (a) Risk ("digits is likely to fail …, and tabular could fail too") supports both branches.
  - The fragility statement is kept and now correctly points to the both-fail case.
- **No new error.**
  - The change introduces no numbers.
  - It records no author decision: the headline still says "for the author to decide".
  - The ENGINEERING_ONLY and "Not an author decision" labels are unchanged.
  - No result file changed, so every earlier numerical verification still holds (R1, R2).
