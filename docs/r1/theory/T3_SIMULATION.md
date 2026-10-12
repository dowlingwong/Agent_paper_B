# T3 — Campaign-level simulation of the T2 model

*Theory track T3 (RUNBOOK §3). Run on 12 Oct 2026 by an AI agent (Claude); AI-assisted. Label: `ENGINEERING_ONLY`. These are model-based numbers, not measurements of the harness.*

- **Code:** `r1/theory/simulate.py` (model) and `r1/theory/t3_report.py` (runner). Sanity tests are in `r1/tests/test_t3_simulate.py`.
- **Output:** `results/r1/engineering/T3_20261012T161444Z/` (3,000 campaigns per cell, 40 worker runs per campaign, seed 7).
- **Reproduce:** `python -m r1.theory.t3_report --out <dir>`. It ran in the cloud workspace because the VM shell is time-boxed; it needs only numpy.

## Setup

Parameters are set to the scale E1 measured on `digits_mlp`:
- per-run noise σ = 0.0125;
- a local edit's noise correlates with its incumbent's at ϱ = 0.8, and a structural edit at ϱ = 0.5;
- true edit sizes have τ = 0.006–0.012.

Proposals draw Δ ∼ N(μ₀ − κ · gain, τ²); κ > 0 gives diminishing returns. A trial costs 1 run, and verify(2) costs 4 more. All arms share the same 40-run budget.

The four policies:
- **ρ:** never verify;
- **always:** verify every trial while the budget allows;
- **margin:** verify iff |Δ̂| < 0.5 σ_d;
- **KG:** the T2 index with the true parameters and the stationary price g.

Verify uses the harness's frozen response (keep iff D̄ > 0).

## Results

Final true gain J(c_T) − J(c₀) is in units of 10⁻³ metric, ± 1 s.e. "v" is the mean number of verifies per campaign.

| Scenario | ρ (never verify) | always verify | margin-triggered | KG index | false-keep rate under ρ | record bias at end under ρ | acceptance of true improvements under ρ, trials 1–5 / 6–15 / 16–30 |
|---|---|---|---|---|---|---|---|
| CRN, stationary proposals | +102.7 ± 0.7 (v 0.0) | +24.6 ± 0.3 (v 8.0) | +62.0 ± 0.5 (v 4.7) | +102.7 ± 0.7 (v 0.0) | 0.17 | +25.8 | 0.76 / 0.67 / 0.61 |
| CRN, harmful proposals | +27.1 ± 0.4 (v 0.0) | +7.3 ± 0.2 (v 8.0) | +20.4 ± 0.3 (v 4.2) | +27.1 ± 0.4 (v 0.0) | 0.32 | +29.4 | 0.70 / 0.61 / 0.54 |
| CRN, diminishing returns | +19.9 ± 0.1 (v 0.0) | +13.1 ± 0.1 (v 8.0) | +17.9 ± 0.1 (v 4.7) | +19.9 ± 0.1 (v 0.0) | 0.35 | +34.4 | 0.69 / 0.54 / 0.41 |
| CRN, structural edits (ϱ 0.5) | +62.9 ± 0.7 (v 0.0) | +17.3 ± 0.3 (v 8.0) | +45.2 ± 0.5 (v 4.5) | +62.9 ± 0.7 (v 0.0) | 0.23 | +24.7 | 0.65 / 0.50 / 0.42 |
| fresh draws, stationary | +41.0 ± 0.6 (v 0.0) | +16.6 ± 0.3 (v 8.0) | +35.0 ± 0.4 (v 4.9) | +41.0 ± 0.6 (v 0.0) | 0.21 | +22.9 | 0.48 / 0.27 / 0.20 |
| fresh draws, harmful proposals | +6.0 ± 0.3 (v 0.0) | −1.3 ± 0.2 (v 8.0) | +6.3 ± 0.3 (v 4.3) | +4.0 ± 0.3 (v 2.9) | 0.41 | +24.3 | 0.45 / 0.23 / 0.15 |
| fresh draws, diminishing returns | +12.0 ± 0.1 (v 0.0) | +9.3 ± 0.1 (v 8.0) | +12.4 ± 0.1 (v 4.8) | +12.0 ± 0.1 (v 0.0) | 0.31 | +25.3 | 0.41 / 0.18 / 0.10 |

## What the simulation supports

1. **Proposition 4 (stagnation) holds at campaign level.**
   - Under ρ, the acceptance rate of *true* improvements falls over the campaign in every scenario.
   - In the stationary scenarios, where the proposal law does not change, the fall comes from the incumbent's inflated record alone. It is strong with fresh draws (0.48 → 0.20) and damped under CRN (0.76 → 0.61), as (1 − ϱ) predicts.
   - The record ends 0.023–0.034 above the true value, i.e. about 2–3 σ. That is the winner's curse on `current_best`.
2. **Proposition 5 (verification rarely pays at a fixed run budget) holds.**
   - Under CRN, never verifying is best in all four scenarios, often by a wide margin.
   - The KG index correctly never verifies there, so it ties ρ.
   - Margin-triggered verification helps only with fresh draws and poor proposals, and only by about one standard error (+0.3 to +0.4 × 10⁻³).
3. **The harness's frozen verify response is the weak point, not verification as such.**
   - With fresh draws and harmful proposals, the KG index verifies 2.9 times per campaign and *loses* (+4.0 vs +6.0).
   - Its value of information assumes the Bayes response (posterior mean > 0). The frozen response (D̄ > 0) ignores Δ̂ and the prior, and keeps more false candidates (false-keep rate 0.45 vs 0.41).
   - This supports the T2 §3 question to the author about the frozen response rule.
4. **False keeps are common under ρ:** 17–41 % of keeps have no true improvement.

   The control problem therefore exists. These scenarios do not show that *verification at a fixed run budget* fixes it. Fixes that cost no runs are untested here: a Bayes or Ladder threshold, which D4 currently forbids as a keep rule, or a posterior-mean incumbent. They are the natural next arms.

## Limits

- This is a model, checked against itself. Its proposal law is Gaussian and memoryless, unlike an LLM proposer.
- The margin rule's z is not tuned (z = 0.5).
- Verify is the only action simulated. Skip, revise and stop are not.
- The fresh-draw incumbent is re-measured only on verified keeps.
