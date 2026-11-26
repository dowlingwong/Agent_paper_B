# Track S — S0.5 summary, `digits_mlp` part (Mac, 14 November 2026)

**AI-assisted (Claude, Mac-local agent). ENGINEERING_ONLY: these values feed the pre-declaration and are never
quoted as results. Not an author decision.** This is the Mac-side S0.5 summary of Track S operator runbook rev 3.3
(`13badb0d`, sha256 `a93fb84b…`) Phase 4, for `digits_mlp` only. `tabular_mlp` follows; the summary is complete, and
STOP 4 can be sent, only when both nodes are in. Branch `mac-tracks-s05-summary-20261114` from
`trackS-ops-20261030` @ `7593ee5b` (the accepted digits-half record, review `TRACKS_S05_T7_STOP4_REVIEW_20261114.md`).

## 1. Input and command

- Input: `results/r1/tracks/digits_mlp/s05_t7_20261113/` as committed at `7593ee5b`; its `SHA256SUMS` verifies 40/40
  here. `s05_calibration.jsonl` `2e4c9a8c…` (298 rows), `s05b_truncated.jsonl` `cd296fd8…` (200 rows), `roots.jsonl`
  `039b6955…` (50 roots), `manifest.json` `68a0d6e0…`. Seeds are Track S blocks (instances 30500–30519, audits
  200000+), none in 7001–7010 or 9001–9210.
- Code: `r1/tracks/analyze.py` at the run's paper pin `8237fd02` (sha256 `b952af6c…`; the file is identical at
  `7593ee5b`), harness `a3fedbb`, Python 3.13.18 (`/tmp/trackg_venv`). Run with `python -P` so the pin's package is
  imported, not the branch checkout:

  ```
  AR_HARNESS_ROOT=<harness a3fedbb> PYTHONPATH=<paper 8237fd02> python -P -m r1.tracks.analyze s05-summary \
    --node digits_mlp=results/r1/tracks/digits_mlp/s05_t7_20261113 \
    --out results/r1/tracks/s05_summary/s05_summary_digits_20261114.json
  ```
- λ₂: the runbook §11.6 snippet, unchanged, on the same `s05_calibration.jsonl` →
  `results/r1/tracks/s05_summary/lambda2_digits_20261114.json`.

## 2. Values (digits only)

| Quantity | Value |
|---|---|
| Binding share per W (S0.5b; 50 roots) | W 8: 1.00 · W 10: 1.00 · W 12: 0.94 · W 20: 0.04 |
| W (digits alone) | **12**, provisional. W is the largest candidate that binds in ≥ 50 % on **every** primary node; if none does, W = 20 and the budget member is dropped. So `tabular_mlp` can move W down (to 8 or 10) or up (to 20) |
| σ_cmp,vary | 0.008356 (median paired sd over 298 calibration audits) |
| σ_D between the two pilot policies at W = 12 (m = 20) | **0.0, UCL 0.0** (see §4) |
| σ_D between repetitions, `static:0.00198,0` (m = 10) | at W = 12: sd 0.006834, UCL (80 %) **0.008839**; at the other candidates (the joint W decides which applies): W 8 0.007902, W 10 0.007964, W 20 0.006928 (UCLs) |
| `between_policy_sd_at_cap` (W = 40) | **0.0** (see §4) |
| Near band b | 0.008587 (0.5 × median \|margin\|, 596 eligible E1/E2 decisions; median E1 0.01717, E2 0.02208). The E1 margins are almost constant (§5.1), so b inherits the degeneracy of §4 |
| λ (obs_inflation) | 1.0 (manifest = prior metadata; the λ check at S0.5 holds) |
| LLM calls / audit runs per campaign | 40.0 / 35.4 |
| Calibration status | **fail** (§3) |

## 3. Calibration gate: fail (design S0.5 (iii), runbook Phase 4)

The gate requires coverage of the 80 % intervals in [0.70, 0.90] overall and in every stratum with ≥ 20 predictions.
It is evaluated **per node**; for `digits_mlp`:

| Stratum (n_group) | n | covered | coverage | in [0.70, 0.90] | Direction |
|---|---|---|---|---|---|
| 0 | 65 | 35 | **0.5385** | no | too low |
| 1-2 | 89 | 60 | **0.6742** | no | too low |
| ≥ 3 | 144 | 136 | **0.9444** | no | too high |
| overall | 298 | 231 | 0.7752 | yes | — |

The q₉₀ of \|z\| (z = (`delta_audit` − `mu`) / `sd`) is 3.14 in stratum 0, 3.11 in 1-2 and 0.98 in ≥ 3. All
three failures are real (n ≥ 20 in each stratum; no null `delta_audit`).

**What the runbook allows**:
- **Coverage too low in stratum 1-2:** the λ₂ revision applies. λ₂ = max(1, (q₉₀ / 1.2816)²) with q₉₀ over all 298
  rows = 2.385, so **λ₂ = 3.463** (`n 298, n_null_skipped 0`). The steps would be:
  - `set_obs_inflation` to `a2u_prior_l2.json`;
  - re-run S0.5 and S0.5b into new `s05_l2` directories with λ₂;
  - every later command uses that prior;
  - a second failure is a STOP.
- **A failing stratum 0, or coverage too high (stratum ≥ 3):** **STOP for the author.** The runbook gives no other
  action. λ ≥ 1 only widens intervals and does not change stratum-0 intervals (they come from the prior alone), so
  the λ₂ revision cannot fix either failure.

Both cases occur here, so the gate **cannot pass through the runbook's only revision**: λ₂ leaves stratum 0 unchanged
and cannot lower stratum ≥ 3 coverage. **The runbook's action for this node is therefore: STOP for the author.** It has
no rule for a mix of a λ₂-eligible failure (1-2) and STOP failures (0, ≥ 3), so nothing beyond the STOP is a runbook
option. In particular a λ₂ = 3.463 re-run for the low part alone would be an author decision outside the runbook, and
it would be expected to end in the second-failure STOP. Any remedy for the stratum-0 intervals (from the prior) or
the over-covered ≥ 3 intervals is a design change by the author ("anything not covered: STOP and ask", §10). §5.2
evaluates one such option offline, as the author asked, without adopting it.

The Phase 4 **fallback** rule (dropping a node whose projected S0.7 + S3e time exceeds 4 days) concerns the Phase 1
time projection, not calibration. It is not an option for this failure, and no projection is computed here.

## 4. Finding not covered by the runbook: the two pilot policies coincide on digits

The two pilot policies are `a2u` (A2-U, `a2u/v2`, prior `5c849d15…`, g = 0.00066) and `static:0.00198,0`
(0.3 σ_node). On every one of the **20** primary (rep-0) instances they took **identical action sequences**:
- E1 skip/execute and E2 keep/discard/failed_invalid agree decision by decision;
- the margins differ slightly, for example E1 0.0172 vs 0.0159;
- so `runs_used` and `y_terminal` are identical at W = 40 and at every truncation W.

Over the 20 a2u roots the actions were: E1 skip 429, execute 318; E2 discard 170, keep 148, failed_invalid 53.

So the between-policy differences D are exactly 0. **σ_D between policies is 0 and its UCL is 0**, at every
truncation W and at the cap (`between_policy_sd_at_cap` = 0, the S0.6 input). These zeros are not variance estimates.
Where they enter: the S0.6 noise match (`--between-policy-sd`) would start from a zero between-policy sd; the S0.8
sizing takes the larger of the S0.5b and S0.7 UCLs (n fixed at 300), so there the zero is masked rather than used.
The between-repetition UCLs are not affected. §5.1 shows why the two policies coincide.

The runbook has no rule for this, so by §10 it goes to the author, with the calibration STOP. Nothing was changed or
re-run here.

## 5. Diagnostics (descriptive only; no model, prior or pin changed)

Requested by the author on 14 Nov (23:20). Scripts and outputs are in `results/r1/tracks/s05_summary/diag/`
(`diag1.py` → `diag1.json`, `diag2.py` → `diag2.json`). They read only the committed S0.4 and S0.5 files and the
prior `a2u_prior_r2_20261111.json` (`5c849d15…`).

### 5.1 Why a2u and `static:0.00198,0` decide identically

Both policies execute iff V\* ≥ their threshold: g = 0.00066 for a2u, 0.00198 for static. They use the same forecast,
so the margins differ by exactly 0.00132 (the E1 margins 0.0172 vs 0.0159 above). E2 keep is "m̂ > 0" for both.

| | a2u | static:0.00198,0 |
|---|---|---|
| E1 decisions (20 instances) | 747 | 747 |
| executed / skipped | 318 / 429 (execute share 0.43; per instance 0.28–0.68) | identical |
| skip reasons | **all 429 `rule_duplicate`** (no `prior_no_gain` skip) | identical |
| worker runs used (W = 40) | 11–27; budget exhausted in **0 / 20** | identical |
| LLM proposal cap (40) reached | **20 / 20** | identical |

- **The threshold never decides.** Over the 298 eligible (non-rule) E1 decisions, V\* − g lies in [0.01700, 0.01724]
  (median 0.01717), so V\* ≈ 0.0177–0.0179. That is 0.0157–0.0159 above the static threshold, about 2.4 σ_node. **0**
  decisions fall between the two thresholds, **0** within ±0.5 σ_node (±0.0033) of g, **0** within ±0.5 σ_node of
  0.00198, and 0 below g.
- **Why V\* is nearly constant.** The predictive sd is dominated by the prior's within-key spread
  τ_w = 0.0493 (≈ 7.5 σ_node; τ0 = 0.00099, σ_cmp = 0.0186). So V\* barely moves with the group's history, and every
  non-duplicate proposal looks worth executing under either price.
- **Which hypothesis.** It is not that A2-U's implicit threshold coincides with 0.00198; the two thresholds differ, but
  both lie far below every V\*. It is also not that the proposals are clearly good or bad; the forecast does not
  separate them, since V\* is almost the same for all. The worker budget is slack in this W = 40 pilot (no root used more than
  27 of 40 runs) and the binding limit is the 40-proposal LLM cap, so budget pressure never enters here (it may at the
  truncated W). The direct cause is the
  size of τ_w relative to g: with V\* ≫ g for every proposal, the only skips are rule duplicates, which both policies
  share.

### 5.2 Calibration: where the miscalibration sits, and an offline two-parameter recalibration

**Decomposition at the run's prior** (S0.5 rows). The predicted variance is τ_n² + τ_w² + se². The S0.5 group sums are
recovered from (μ, n_group) and the prior; the reconstructed sd matches the recorded sd to 7e-18, and the recovered sums are exactly 0 where n_group = 0 (checked by the round-2 reviewer).

| Stratum | n | mean residual (δ − μ) | MS residual / predicted var | share τ_n² | share τ_w² | share se² | bias² share of MS |
|---|---|---|---|---|---|---|---|
| 0 | 65 | +0.0188 | **3.77** | 0.0004 | 0.946 | 0.053 | 0.04 |
| 1-2 | 89 | −0.0177 | **3.02** | 0.0004 | 0.970 | 0.029 | 0.04 |
| ≥ 3 | 144 | −0.0106 | **0.42** | 0.0004 | 0.994 | 0.005 | 0.11 |

- **The prior/posterior variance of the group mean (τ_n²) is negligible** (0.04 %). **The observation-noise terms are
  small too:** the audit se² is 0.5–5 %, and λ acts only through the group update (τ_n and the posterior mean), which barely moves at the run's τ0. **Almost all predicted variance is
  the within-key spread τ_w², which is the same in every stratum.**
- The realised spread is not the same. The mean squared residual is 3–4 × the predicted variance for proposals with 0–2
  earlier observations in their group, and 0.4 × for later ones. The bias is a small part of the error (4–11 %). So the miscalibration is a
  **spread that shrinks with n_group**, which a constant τ_w cannot represent at the floor τ0 (see "Why" below).

**Two-parameter recalibration, offline (not implemented).** The parameters are:
- prior scale c, which multiplies τ0 and τ_w; the variant `tau0_only` multiplies τ0 alone;
- λ, which multiplies the update's observation variance, as `obs_inflation` does.

Method:
- (c, λ) were fitted on the 165 S0.4 rows the prior came from. The fit replays each instance and (key, sign) group in budget order, with the executed Δ̂ as observations. The round-2 reviewer confirmed that this reproduces the controller's observation lists.
- Two criteria were used: maximum Gaussian predictive log-likelihood, and smallest worst-stratum coverage error.
- The fit was then tested on the 298 S0.5 calibration rows. The S0.5 group sums are recovered from (μ, n_group) and the prior. The reviewer checked them separately: they are exactly 0 where n_group = 0.
- Grid: log grid c ∈ [0.01, 1000] × λ ∈ [1e-4, 1000], 121 × 121 points. Note that both the runbook's λ₂ rule and the code (A2UController refuses obs_inflation < 1, per the round-2 reviewer) allow only λ ≥ 1.

| Variant, criterion (fitted on S0.4) | c | λ | S0.5 coverage 0 / 1-2 / ≥ 3 | gate |
|---|---|---|---|---|
| run prior | 1 | 1 | 0.538 / 0.674 / 0.944 | fail |
| both, max log-lik | 1.00 | 0.0015 | 0.538 / 0.809 / 0.972 | fail |
| both, min worst-stratum error | 1.00 | 0.0001 (grid edge) | 0.538 / 0.652 / 0.840 | fail |
| tau0_only, max log-lik | 34.8 | 1.39 | 0.600 / 0.854 / 0.972 | fail |
| tau0_only, min worst-stratum error | 51.1 | 0.18 | 0.600 / 0.640 / 0.840 | fail |

The min-worst-stratum criterion ties on the grid: 18 `tau0_only` points share the minimum S0.4 error (c 51.1–110.1, λ 0.185–0.473), and 15 `both` points do (c 1.0–1.1, λ 1e-4 to 3e-4). The table shows the first in grid order. Per the round-3 reviewer, none of the tied points passes on S0.5.

- **Out of sample, the recalibration fails.** No (c, λ) fitted on S0.4 puts all three strata in [0.70, 0.90] on S0.5.
- **In sample** (points chosen on S0.5 itself, so an upper bound on what is reachable):
  - in the `both` variant no point passes, neither on the grid nor in a fine scan at λ = 1;
  - in `tau0_only`, 8 of the 14,641 grid points pass. All of them have τ0 ≈ 91–110 × the run's value and λ between 0.62 and 0.93 (λ = 1 is not a grid point);
  - a fine scan at **λ = 1 exactly** (`diag2_lambda1.py`, c ∈ [1, 1000], 700 points) finds `tau0_only` passes for c ≈ 112.6–114.8 only. That is τ0 ≈ 0.11, about 17 σ_node. For example, c = 114.8 gives 0.892 / 0.764 / 0.896. The round-2/3 reviewer found the same window (c ∈ [112.6, 115.6]) independently;
  - so **at the run's own λ = 1, changing τ0 alone reaches the gate in sample**, but only in a narrow window, and with S0.5 itself as the fitting set.
- **As an option:** a recalibration fitted on S0.4, the honest test, does not reach the gate on S0.5 in either variant. An in-sample τ0 near 0.11 does, at λ = 1, in a window about 2 % wide in c.

**Why.** (Corrected after round 2.)
- The prior fit set τ0 to its floor (0.15 σ_node = 0.00099), because the A2 prior sd τ_A2 (0.019) is smaller than τ_w (0.049).
- With τ0 that small the posterior mean barely moves with the group's history, and the predictive spread is almost all τ_w. That spread does not depend on n_group. The same cause makes V\* nearly constant (§5.1).
- λ is not confined to τ_n²: it also sets how far the posterior mean follows the observations.
- With a much larger τ0, the existing model's spread does shrink with n_group. The S0.4 data favour a larger τ0: the best log-likelihood on the report's grid is at c 34.8, λ 1.39 (the round-2 reviewer found log-likelihood 251.0 vs 235.1 at c = 1, on their own grid). In sample this reaches the band at λ = 1 in the narrow window above.

So the direction is a **prior change (a larger τ0)**, possibly together with a model change for the within-key spread. It is supported in sample only; out of sample (fitted on S0.4) it does not reach the gate. Either way it is for the author.

## 6. When this goes to the author

The author's instruction (14 Nov, 23:20): both items, the calibration STOP and the policy coincidence, go to the
author for a decision after the `tabular_mlp` half is complete.

## 7. Not done here

- `tabular_mlp` S0.5 (TASL-2 was unreachable on 12–14 Nov); the joint W; STOP 4 itself (the operator sends the author
  W, σ_D, b, λ and the projection).
- No STATUS entry, so that the operator branch is not touched; this report and the two JSON files are the record.

## 8. Files

- `results/r1/tracks/s05_summary/s05_summary_digits_20261114.json`: `tracks_s05_summary/v2`, the full
  `s05-summary` output; `out_dir` is repo-relative.
- `results/r1/tracks/s05_summary/lambda2_digits_20261114.json`: the §11.6 line.
- `results/r1/tracks/s05_summary/diag/`: the §5 scripts and their outputs (`diag1`, `diag2`, `diag2_lambda1`).
