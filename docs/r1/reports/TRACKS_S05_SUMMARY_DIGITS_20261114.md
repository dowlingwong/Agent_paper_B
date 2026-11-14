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
  separate them, since V\* is almost the same for all. The worker budget is slack (no root used more than 27 of 40
  runs) and the binding limit is the 40-proposal LLM cap, so budget pressure never enters. The direct cause is the
  size of τ_w relative to g: with V\* ≫ g for every proposal, the only skips are rule duplicates, which both policies
  share.

### 5.2 Calibration: where the miscalibration sits, and an offline two-parameter recalibration

**Decomposition at the run's prior** (S0.5 rows). The predicted variance is τ_n² + τ_w² + se². The S0.5 group sums are
recovered exactly from (μ, n_group) and the prior; the reconstructed sd matches the recorded sd to 7e-18.

| Stratum | n | mean residual (δ − μ) | MS residual / predicted var | share τ_n² | share τ_w² | share se² | bias² share of MS |
|---|---|---|---|---|---|---|---|
| 0 | 65 | +0.0188 | **3.77** | 0.0004 | 0.946 | 0.053 | 0.04 |
| 1-2 | 89 | −0.0177 | **3.02** | 0.0004 | 0.970 | 0.029 | 0.04 |
| ≥ 3 | 144 | −0.0106 | **0.42** | 0.0004 | 0.994 | 0.005 | 0.11 |

- **The prior/posterior variance of the group mean (τ_n²) is negligible** (0.04 %). **The observation-noise terms are
  small too:** the audit se² is 0.5–5 %, and λ acts only on τ_n through the update. **Almost all predicted variance is
  the within-key spread τ_w², which is the same in every stratum.**
- The realised spread is not the same. It is 3–4 × the prediction for proposals with 0–2 earlier observations in their
  group, and 0.4 × for later ones. The bias is a small part of the error (4–11 %). So the miscalibration is a
  **spread that shrinks with n_group**, which a constant τ_w cannot represent.

**Two-parameter recalibration, offline (not implemented).** The model has a prior scale c and λ.
- c multiplies τ0 and τ_w; the variant `tau0_only` multiplies τ0 alone.
- λ multiplies the update's observation variance, as `obs_inflation` does.
- (c, λ) were fitted on the 165 S0.4 rows the prior came from, by sequential replay per instance and (key, sign)
  group. Two criteria were used: maximum Gaussian predictive log-likelihood, and the smallest worst-stratum coverage
  error.
- The fit was then tested on the 298 S0.5 calibration rows, over a log grid c ∈ [0.1, 10] × λ ∈ [0.1, 30]
  (81 × 81 points). The grid includes λ < 1, which the runbook's λ₂ rule does not allow.

| Variant, criterion | c | λ | S0.5 coverage 0 / 1-2 / ≥ 3 | gate |
|---|---|---|---|---|
| run prior (c = 1, λ = 1) | 1 | 1 | 0.538 / 0.674 / 0.944 | fail |
| both, max log-lik on S0.4 | 1.12 | 0.10 (grid edge) | 0.600 / 0.730 / 0.958 | fail |
| both, min worst-stratum error on S0.4 | 0.94 | 0.10 (grid edge) | 0.492 / 0.629 / 0.938 | fail |
| tau0_only, max log-lik on S0.4 | 10.0 (grid edge) | 0.15 | 0.569 / 0.809 / 0.972 | fail |
| tau0_only, min worst-stratum error | 0.10 (edge) | 0.10 (edge) | 0.538 / 0.674 / 0.944 | fail |

**No (c, λ) on the grid puts all three strata in [0.70, 0.90] on S0.5, even when chosen on S0.5 itself** (0 of
6,561 points, in both variants). The reason follows from the decomposition: c moves every stratum's interval in the
same direction, and λ acts only on the negligible τ_n². So **as an option, the two-parameter recalibration does not
achieve the gate on digits**. A remedy would need a spread that depends on n_group (for example a τ_w that shrinks with
the group's observations); that is a model change for the author and is not evaluated here.

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
- `results/r1/tracks/s05_summary/diag/`: the §5 scripts and their outputs.
