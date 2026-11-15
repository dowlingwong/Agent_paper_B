# Track S — S0.5 summary, both nodes (Mac, 15 November 2026)

**AI-assisted (Claude, Mac-local agent). ENGINEERING_ONLY: these values feed the pre-declaration and are never
quoted as results. Analysis only: no code, pin, prior or run was changed. Not an author decision.** This is the
two-node S0.5 summary of Track S operator runbook rev 3.3 (`13badb0d`, sha256 `a93fb84b…`) Phase 4. It ends with three
options for the author (§7). Branch `mac-tracks-s05-summary-both-20261115`:
- from `trackS-ops-20261030` @ `fab88fce` (the accepted tabular-half record, review
  `TRACKS_S05_T7_TABULAR_REVIEW_20261114.md`);
- merged with `mac-tracks-s05-summary-20261114` @ `3e0fa203`, the digits summary accepted at `62451900`
  (`reports/TRACKS_S05_SUMMARY_DIGITS_20261114.md`). That report is the reference for the digits diagnostics; this
  report repeats only what the joint decision needs.

## 1. Input and command

- **Inputs.** `results/r1/tracks/digits_mlp/s05_t7_20261113/` (`SHA256SUMS` 40/40 OK) and
  `results/r1/tracks/tabular_mlp/s05_t7_20261114/` (17/17 OK).
  - tabular: `s05_calibration.jsonl` `e05cd54a…` (330 rows), `s05b_truncated.jsonl` `615aa390…`, `roots.jsonl`
    `5e082a58…` (50 roots), `manifest.json` `28e008f6…`; prior `s04_t7_20261114/a2u_prior.json` `ba8f7783…`;
    g0 0.00019, `obs_inflation` 1.0.
  - digits: as in the digits report; prior `a2u_prior_r2_20261111.json` `5c849d15…`.
  - Seeds: Track S blocks only (instances 30500–30519, audits 200000+); none in 7001–7010 or 9001–9210.
- **Code.** `r1/tracks/analyze.py` at the runs' paper pin `8237fd02` (sha256 `b952af6c…`; identical in this branch),
  harness `a3fedbb`, `/tmp/trackg_venv` (Python 3.13). Run with `python -P` so the pin's package is imported:

  ```
  AR_HARNESS_ROOT=<harness a3fedbb> PYTHONPATH=<paper 8237fd02> python -P -m r1.tracks.analyze s05-summary \
    --node digits_mlp=results/r1/tracks/digits_mlp/s05_t7_20261113 \
    --node tabular_mlp=results/r1/tracks/tabular_mlp/s05_t7_20261114 \
    --out results/r1/tracks/s05_summary/s05_summary_20261115.json
  ```
- **λ₂.** The runbook §11.6 snippet, unchanged, on tabular `s05_calibration.jsonl` →
  `results/r1/tracks/s05_summary/lambda2_tabular_20261115.json`. The digits line is `lambda2_digits_20261114.json`.

## 2. Phase 4 values

`s05-summary` gives `W_chosen = 12`, `budget_member = "kept"`, `budget_binds = true` (output sha256 `7a07ccf5…`).

| Quantity | `digits_mlp` | `tabular_mlp` |
|---|---|---|
| Binding share per W (S0.5b, 50 roots) | W 8 1.00 · W 10 1.00 · **W 12 0.94** · W 20 0.04 | W 8 1.00 · W 10 1.00 · **W 12 1.00** · W 20 0.16 |
| **W (joint)** | **12**: the largest candidate binding in ≥ 50 % on every primary node, so the budget member stays | (same) |
| σ_cmp,vary | 0.008356 | 0.005574 |
| σ_D between the two pilot policies, S0.5b at W 12 (m 20) | **0.0, UCL 0.0** (§4) | **0.0, UCL 0.0** (§4) |
| σ_D between repetitions, static, m 10, UCL (80 %) at W 12 | **0.008839** (sd 0.006834) | **0.000799** (sd 0.000618) |
| … at the other candidates (for reference) | W 8 0.007902 · W 10 0.007964 · W 20 0.006928 | W 8 0.009841 · W 10 0.004118 · W 20 0.001374 |
| `between_policy_sd_at_cap` (W 40) | **0.0** | **0.0** |
| Near band b (0.5 × median \|margin\|) | 0.008587 (n 596; median E1 0.01717, E2 0.02208) | 0.003847 (n 660; median E1 0.00769, E2 0.01015) |
| λ (`obs_inflation`; manifest = prior metadata) | 1.0 | 1.0 |
| λ₂ (§11.6; for the record, see §3) | 3.463 (q₉₀ 2.385, n 298) | 3.640 (q₉₀ 2.445, n 330, 0 null) |
| LLM calls / audit runs per campaign | 40.0 / 35.4 | 40.0 / 38.6 |
| **Calibration status** | **fail** | **fail** |
| Projection, rest of node (Phase 1 formula, k = 2) | **34.0 h** | **39.2 h** |
| Fallback (S0.7 + S3e > 4 days drops the node) | does not apply | does not apply |

Notes:
- **Tabular between-repetition UCL at W 12.** It rests on 2 non-zero differences out of 10: 8 pairs are exactly 0,
  the others are −0.00144 and −0.00150. At W 8 there are 6 non-zero pairs. With m = 10 the UCL is coarse.
- **Which σ_D feeds what.** The S0.8 sizing input `sigma_D_ucl_s05b` is the between-*policy* UCL, which is 0 on both
  nodes. `plan_sizing` takes max(that, the S0.7 dev UCL), so the zero is masked there. The between-repetition UCL is
  printed for the record; this report does not trace a downstream use for it.
- **Projection.** The formula is (C·L/k + R·t_run/c)/3600, with C 80 000, R 60 000, k 2 and c = min(free cores, 2k) = 4.
  - L is the mean concurrent latency of each node's TASL-7 S0.1: digits 2.715981 s (review of the digits S0.1,
    `TRKS_S01_RESULT_AND_S05_K2_REVIEW_20261113.md`), tabular mean(2.812054, 2.806924) = 2.809489 s.
  - t_run is the Phase 0 smoke value: digits 0.9091 s, tabular 1.9135 s (successful campaign only, per the Phase 0
    review m7).
  - The formula covers all remaining node work, so it bounds S0.7 + S3e from above. Both nodes are far below 96 h.
  - Cross-check from the measured S0.5 throughput (one collector, one URL): 3,769 LLM calls in 2.46 h (digits) and
    4,594 calls in 2.50 h (tabular). At those rates 80 000 calls take about 52 h and 44 h, still below 4 days
    without sharding.
  - Both nodes now run on TASL-7, so their remaining work runs one after the other: the formula total is about 73 h.
  - (For the record only: the same formula with the serial k = 1 latency would give 22.6 h for digits and 31.5 h
    for tabular. k = 2 was fixed by measurement under the runbook rule, and this report does not revisit it.)
- No failed units, exhausted campaigns or STOPs were recorded in either S0.5 run (manifests; tabular `done` 50/31/99/0/0).

## 3. Calibration gate: both nodes fail, and the runbook's action for both is STOP

The gate (design S0.5 (iii); `analyze.calibration_gate`) requires coverage of the 80 % intervals to lie in [0.70, 0.90],
inclusive, overall and in every stratum with ≥ 20 predictions. It is evaluated per node.

| Stratum (n_group) | digits n | digits coverage | tabular n | tabular coverage | Direction |
|---|---|---|---|---|---|
| 0 | 65 | **0.538** | 57 | **0.368** (21/57) | too low (both) |
| 1-2 | 89 | **0.674** | 95 | **0.653** (62/95) | too low (both) |
| ≥ 3 | 144 | **0.944** | 178 | 0.831 (148/178) | digits too high; tabular in band |
| overall | 298 | 0.775 | 330 | 0.700 (231/330) | both in band; tabular exactly at the lower edge |

Runbook consequences:
- **A failing stratum 0 is a STOP for the author on both nodes.** λ ≥ 1 does not change stratum-0 intervals,
  because they come from the prior alone. Digits also has an over-covered stratum ≥ 3, which is a second STOP reason.
- Stratum 1-2 is too low on both nodes, so the λ₂ revision would be eligible on its own: λ₂ = 3.463 (digits) and
  3.640 (tabular). But the runbook has no rule for a mix of a λ₂-eligible failure and a STOP failure. Nothing beyond
  the STOP is a runbook option (digits report §3). A λ₂ re-run for the low part alone would be an author decision
  outside the runbook.

So **STOP 4 is reached with a calibration STOP on both nodes**, together with the policy coincidence (§4), which no
runbook rule covers (§10: STOP and ask).

## 4. Tabular: the two policies decide identically too, V\* − g is nearly constant, and the LLM cap ends every campaign

Script `diag_2node/policy_diag.py <s05_dir> <static threshold>`. The static threshold is now an argument: 0.00198
for digits, 0.00057 for tabular. On digits it reproduces every number of the accepted `diag1.json`. In addition it
compares the full action sequences and the S0.5b truncations.

| | `digits_mlp` (a2u vs static:0.00198,0) | `tabular_mlp` (a2u vs static:0.00057,0) |
|---|---|---|
| Rep-0 instances with identical action sequences (E1 and E2, incl. skip reasons), `runs_used`, `y_terminal` | **20 / 20** | **20 / 20** |
| … identical `y_terminal` and `runs_used` at each truncation W 8/10/12/20 | 20 / 20 at every W | 20 / 20 at every W |
| E1 execute / skip (each policy) | 318 / 429 (share 0.43; per instance 0.28–0.68) | 350 / 399 (share 0.47; per instance 0.35–0.57) |
| E1 skip reasons | all 429 `rule_duplicate` | all 399 `rule_duplicate` |
| E2 keep / discard / failed_invalid | 148 / 170 / 53 | 158 / 192 / 51 |
| Eligible E1 decisions (a2u) | 298 | 330 |
| **V\* − g** (a2u, g = 0.1 σ_node) | **[0.01700, 0.01724]**, median 0.01717 = **2.58–2.61 σ_node** | **[0.007672, 0.007707]**, median 0.007694 = **4.04–4.06 σ_node** |
| V\* − static threshold | [0.01568, 0.01592] | [0.007292, 0.007327] |
| Range of V\* itself, in σ_node | 0.036 | 0.018 |
| Decisions below g / between the two thresholds / within ±0.5 σ_node of g / of the static threshold | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| E2 margin (m̂, keep iff > 0): p05 … p95; within ±0.5 σ_node of 0 | −0.108 … 0.114; 46 of 298 | −0.055 … 0.034; 38 of 330 |
| Worker runs used at W 40 | 11–27; exhausted in 0 / 20 | 14–22; exhausted in 0 / 20 |
| LLM proposal cap (40) reached | **20 / 20** | **20 / 20** |

**Which budget stops the campaigns.**
- In the W = 40 pilot, every campaign of both policies on both nodes ends at the 40-proposal LLM cap. The worker
  budget is never exhausted.
- At the chosen W = 12, the S0.5b truncations show that the worker budget binds instead: in 94 % (digits) and 100 %
  (tabular) of the 50 roots.
- Neither policy looks at the budget (both are static: b_budget = b_info = 0). The truncated campaigns are therefore
  prefixes of the same identical sequences. The binding W changes where a campaign stops, not any decision.

**Same mechanism as on digits** (digits report §5.1).
- Both policies execute iff V\* ≥ their threshold and keep iff m̂ > 0.
- On both nodes the fitted prior has τ0 at its floor (0.15 σ_node), because τ_A2 < τ_w:
  - digits: τ0 0.00099, τ_w 0.0493, σ_cmp 0.0186, τ_A2 0.0190;
  - tabular: τ0 0.000285, τ_w 0.0253 (13 σ_node), σ_cmp 0.0168, τ_A2 0.00646.
- With τ0 that small, the posterior mean stays at μ0 and the predictive sd is about τ_w. So
  V\* = μΦ(−z) + (τ²/s)φ(z) (`c3.rules.proposal_value`, z at t\* = −μσ²/τ²) is nearly the same for every proposal.
  At μ = 0 it is 0.399·τ_w²/√(τ_w² + σ_cmp²) = 2.8 σ_node (digits) and 4.4 σ_node (tabular). The observed values are
  2.7 and 4.1 σ_node, because μ0 is slightly negative. Both prices, 0.1 and 0.3 σ_node, lie far below that, so every
  non-duplicate proposal is executed.
- The E2 decision is real on both nodes: m̂ varies widely and many keeps are close to 0. E1 screening is inert.

## 5. What the policy coincidence does downstream (read from the pin; nothing was run)

- **S0.6 (first run).** `simulate_controls.match_noise` gives `--between-policy-sd` precedence over `--sigma-D`.
  0.0 is not `None`, so on both nodes the simulator's campaign noise would be matched to a between-policy sd of 0.
  The N0 route-A check (Phase 5) would then run at that matched noise. Separately, the runbook's `--sigma-D <σ_D UCL>`
  does not say which of the two UCLs to pass, and with one of them at 0 the choice now matters.
- **S0.7 static stage.** The grid is g ∈ {0, 0.05, 0.1, 0.2, 0.4} × σ_cmp,vary (plus 0.8 in the extension) ×
  h ∈ {−0.25, 0, 0.25} × σ_cmp,vary (`collect.TUNE_G`, `TUNE_H`).
  - The largest g is 0.00334 (extension 0.00669) for digits and 0.00223 (0.00446) for tabular. All of these lie below
    the smallest V\*, 0.01766 and 0.00786.
  - Under the current prior, therefore, the 5–6 g values cannot change any E1 decision. The 15 statics act as 3
    (the h axis), and the g of m\* is not identified.
- **S0.7 members.**
  - `info×0.5` adds 0.5·(τ_pred − τ̄). τ_pred is about τ_w for every proposal, so the term is about 0.
  - `budget×1` moves the E1 threshold by −σ_cmp,vary·(r − r̄₁), where r = runs_left/W − proposals_left/N_cap ∈ [−1, 1].
    To flip any E1 decision it needs r̄₁ − r ≥ (min V\* − g\*)/σ_cmp,vary. With g\* ≤ 0.4 σ_cmp,vary that is ≥ 1.71 for
    digits and ≥ 1.01 for tabular (≥ 0.61 for tabular if the 0.8 extension wins).
  - In the W = 40 pilot, r̄ − r never exceeded 0.09. At W = 12, r falls lower, which this report does not test.
  - `keep±×0.5` act on E2, which is a real decision.
- In short: with the current prior, Track S's π\* versus m\* comparison would test the E2 (keep) channel, plus at
  most a budget effect at the edge. It would not test the screening (E1) channel that A2-U is built for.

## 6. Calibration diagnostics for tabular, and a joint look at the larger-τ0 direction (offline, descriptive)

Scripts are in `results/r1/tracks/s05_summary/diag_2node/`:
- `diag2.py` and `diag2_lambda1.py` are byte-identical to the accepted digits scripts (sha256 `81e041c5…`, `c967edee…`).
- `diag2_region.py` is new. It uses `diag2.py`'s set-up and grid unchanged, and adds the S0.4 ties and the S0.4
  likelihood region (below).
- `vstar_counterfactual.py` is new (below).

**Decomposition at the run prior (tabular S0.5 rows).** The reconstructed sd matches the recorded sd to 3.5e-18.

| Stratum | n | mean residual | MS residual / predicted var | share τ_n² | share τ_w² | share se² | bias² share |
|---|---|---|---|---|---|---|---|
| 0 | 57 | +0.0035 | **3.51** | 0.0001 | 0.790 | 0.209 | 0.004 |
| 1-2 | 95 | −0.0143 | **3.21** | 0.0001 | 0.905 | 0.095 | 0.090 |
| ≥ 3 | 178 | −0.0113 | 1.01 | 0.0001 | 0.986 | 0.014 | 0.197 |

The pattern matches digits: the realised spread is about 3.5 × the predicted spread for the first proposals of a
group, and drops with n_group. A constant τ_w cannot represent that. Digits also over-covers at n_group ≥ 3 (ratio
0.42); tabular sits at 1.01 there.

**Recalibration (c multiplies τ0, or τ0 and τ_w; λ multiplies the update's observation variance).** "In sample"
means the point was chosen on S0.5 itself. "Out of sample" means the point was fitted on S0.4 and tested on S0.5.

| | `digits_mlp` | `tabular_mlp` |
|---|---|---|
| `tau0_only`, S0.4 max log-lik → S0.5 | c 34.8, λ 1.39 → 0.600 / 0.854 / 0.972: **fail** | c 133.4, λ 1.58 → **0.702 / 0.811 / 0.854**, overall 0.815: **pass** (stratum 0 just in band) |
| `tau0_only`, S0.4 points within 2 log-lik units of the max → S0.5 | **0 of 102** pass (c 14.7–46.4; stratum 0 stays 0.57–0.60, ≥ 3 0.95–0.99) | **26 of 44** pass, all with λ ≥ 1 (c 100–178) |
| `tau0_only`, S0.4 min worst-stratum ties → S0.5 | 0 of 18 pass | 0 of 17 pass |
| `both` variant (scales τ_w too), any S0.4 fit | fails | fails (0 of 27 in the region, 0 of 98 ties) |
| `tau0_only` at λ = 1, in sample (fine scan, 700 points) | passes only for c 112.6–114.8 (τ0 ≈ 17 σ_node) | passes for c 133.2–211.9 (48 points; τ0 ≈ 20–32 σ_node) |

- **Tabular.** A larger τ0, fitted on S0.4 alone, reaches the gate on S0.5 in more than half of the S0.4 likelihood
  region. This is the honest test. It passes there, though stratum 0 is near the edge at the maximum.
- **Digits.** The τ0 that S0.4 favours (c ≈ 15–46) is several times smaller than what S0.5 needs (c ≈ 113). No
  S0.4-fitted point passes, and over-coverage at n_group ≥ 3 persists across the whole region. One possible
  contributor is that the digits S0.4 rows come from TASL-2 while S0.5 ran on TASL-7. That is untested here. A
  τ0-only change therefore has no out-of-sample support on digits. Its pattern (too narrow early, too wide late)
  points to a within-key spread that depends on n_group, which is a model change.

**Would a larger τ0 make execution a real decision?** `vstar_counterfactual.py` recomputes V\* for the S0.5 eligible
E1 decisions with τ0 = c × the run's value, on the observed group histories. It does not replay the campaigns: a
different prior would have executed different proposals. So it indicates direction only.

| c (τ0 in σ_node) | V\* p05–p95 (σ_node) | V\* < g | within ±0.5 σ_node of g | V\* < g by stratum 0 / 1-2 / ≥ 3 |
|---|---|---|---|---|
| digits 1 (0.15, run) | 2.69–2.71 | 0 / 298 | 0 | 0 / 0 / 0 |
| digits 34.8 (5.2, S0.4 ML) | 0.45–8.61 | 5 | 22 | 0 / 0 / 5 |
| digits 114.8 (17.2, S0.5 in-sample) | 0.15–16.85 | 10 | 44 | 0 / 2 / 8 |
| tabular 1 (0.15, run) | 4.14–4.15 | 0 / 330 | 0 | 0 / 0 / 0 |
| tabular 133.2 (20.0) | 0.02–26.2 | 32 | 60 | 0 / 6 / 26 |
| tabular 170 (25.5) | 0.01–29.4 | 36 | 65 | 0 / 7 / 29 |

With a larger τ0, V\* follows the group's history. Some repeat-key proposals fall below g: 3 % on digits and 10–11 %
on tabular, with many more inside the band. First proposals of a group (n_group = 0) are still always executed. This
is the condition under which the static grid's g and the screening channel would matter.

## 7. Options for the author (each with cost; recommendation at the end)

Common to all three: the runbook's action now is STOP on both nodes (§3), plus a finding no rule covers (§4). Nothing
downstream has started: S0.6, S0.7, the pre-declaration and S3 are all not begun, so no evidence is at stake.

**(a) Change the A2-U prior / variance structure and redo S0.4/S0.5.**
- What it fixes: the common cause of both findings (§4, §6), namely τ0 at the floor with a constant τ_w. It is the
  only option that addresses the calibration STOP, and the only one that brings the E1 screening channel back.
- Two levels:
  - **(a-i) Prior estimator only.** Replace the τ0 floor rule by a declared S0.4 fit of τ0, for example the replay
    maximum likelihood with λ ≥ 1.
    - Evidence: out of sample it passes on tabular (26 of 44 region points) and fails on digits (0 of 102).
    - The existing S0.4 rows can be reused, since this is a fit only.
  - **(a-ii) Model change.** A within-key spread that shrinks with n_group, or is estimated separately for first
    and repeat proposals. This targets digits' pattern. There is no offline evidence for it yet.
- Cost:
  - Code: `a2u.py` `fit_prior`, and for (a-ii) also the predictive, with tests and an independent code review.
  - A new paper pin and a runbook revision for the Phase 3/4 commands and pins.
  - Host time on TASL-7, run one node after the other:
    - S0.5 + S0.5b about 2.5 h per node (measured), so about 5 h for both;
    - plus S0.4 about 0.5 h per node if new rows are wanted (tabular S0.4 took 0.45 h).
  - Each step goes through the review loop. Rough total: 2–4 days.
  - Risk: the new S0.5 is the test, and a fail is a second STOP. On present evidence, digits is likely to fail
    under (a-i) alone.
- Decisions it needs from the author:
  - which level, (a-i) or (a-ii);
  - whether the new S0.5 uses fresh pilot seeds inside the Track S block. The current S0.5 has informed this
    analysis, so reusing it would make the test in-sample.
  - which pass criterion is declared before the re-run.

**(b) Change the price g or the budget so that executing becomes a real decision.**
- What it can do under the current prior: little.
  - V\* varies across proposals by only 0.036 σ_node (digits) and 0.018 σ_node (tabular). Any g below
    min V\* executes everything; any g above max V\* skips every non-duplicate proposal. A g inside that window decides
    on differences of about 1e-5, which is a knife edge.
  - Moving the declared pilot g or the S0.7 grid (code constants `TUNE_G`, so a pin change) does not create
    variation in V\*.
  - The static policies ignore the budget. Changing W or the LLM cap moves where campaigns stop (§4), not what they
    decide. The `budget×1` member can only bite at extreme budget gaps (§5).
- It does not touch calibration, so the STOP stands.
- Cost: low (declarations; a pin change only if the grid constants move). Benefit for the core problem: none.
- Its use is as a follow-up to (a): after a prior change, check that the declared g and the S0.7 grid straddle the
  new V\* distribution (§6 suggests they would at least partly).

**(c) Narrow Track S.**
- Variants:
  - **(c-i)** Declare the comparison as the E2 (keep) channel plus the budget member, since E1 screening is inert.
    E2 is a real decision on both nodes (§4). But the calibration gate still fails and would have to be waived or
    redefined. m̂ also depends on the prior: the shrinkage τ²/(τ² + σ_cmp²) is about 0.88 (digits) and 0.69
    (tabular) at the run prior.
  - **(c-ii)** Drop a node. Both nodes show the same failure, so this helps only together with (a). If (a-i) works on
    tabular and not on digits, a tabular-only Track S is the cheapest route with out-of-sample support.
  - **(c-iii)** End Track S before EVIDENCE, and keep the S0.5 findings as an engineering record. No claim about π\*
    would be made.
- Cost: least compute. But the design and pre-declaration must be amended, and (c-i) and (c-iii) give up the primary
  question, whether a tuned dynamic threshold beats the tuned static one. Track S's "no gain found" already bounds π\*
  only; under (c-i) it would bound an E2-only π\*.

**Recommendation (for the author to decide): (a), with (c-ii) declared in advance as the fallback for digits.**
- (b) alone cannot make execution a real decision while V\* is constant.
- (c) gives up the question Track S exists to answer, and does not remove the calibration failure.
- (a) addresses the common cause. It is cheap in host time (about 5 h of S0.5 for both nodes) and has
  out-of-sample support on tabular.
- Concretely:
  1. Declare the prior change and fit it on S0.4 only: (a-i), or (a-ii) if the author wants to give digits a
     chance.
  2. Re-run S0.5/S0.5b on both nodes with fresh pilot seeds.
  3. Declare beforehand that if digits fails again, Track S continues on tabular alone (c-ii) rather than starting
     another revision.
  4. After the re-run, re-check the S0.7 grid against the new V\* distribution (the useful part of (b)).

## 8. Not done here

- No STOP 4 message was sent: the operator sends the author W, σ_D, b, λ and the projection. No STATUS entry was
  written, so that the operator branch is untouched. No code, pin, prior or run was changed.

## 9. Files

- `results/r1/tracks/s05_summary/s05_summary_20261115.json`: `tracks_s05_summary/v2`, both nodes; `out_dir` is
  repo-relative.
- `results/r1/tracks/s05_summary/lambda2_tabular_20261115.json`: the §11.6 line for tabular.
- `results/r1/tracks/s05_summary/diag_2node/`:
  - `policy_diag.py` → `policy_diag_{digits,tabular}.json`;
  - `diag2.py` → `diag2_tabular.json`;
  - `diag2_lambda1.py` → `diag2_lambda1_tabular.json`;
  - `diag2_region.py` → `diag2_region_{digits,tabular}.json`;
  - `vstar_counterfactual.py` → `vstar_cf_{digits,tabular}.json`.
- Digits files from the merged branch: `s05_summary_digits_20261114.json`, `lambda2_digits_20261114.json`, `diag/`.
