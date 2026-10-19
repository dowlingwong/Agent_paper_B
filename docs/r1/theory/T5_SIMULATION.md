# T5 — Campaign-level simulation of the T4 theory

*Theory track T5. Run 19 Oct 2026 overnight by an AI agent (Claude) for the author. AI-assisted; label `ENGINEERING_ONLY`. Every number here comes from a model. None is a measurement of the harness. The author has not checked the code or this note, and no human has reviewed them.*

- **Code:** `r1/theory/simulate_t4.py` (the model, the policies and the branch study) and `r1/theory/t5_report.py` (the runner and the tables). Tests: `r1/tests/test_t5_simulate.py` (14 tests).
- **Output:** `results/r1/engineering/T5_20261019T004918Z/`:
  - `parts/*.json`: one file per check cell, with its seeds;
  - `tables.md`: all tables, generated;
  - `manifest.json`: base seed 20261019, campaign counts, source SHA-256 and the git head.
  - Total compute was 396 CPU-seconds on the Mac VM, single-threaded.
- **Reproduce:** `python -m r1.theory.t5_report --out <dir>`. The run is resumable: each part is skipped once its file exists, and `--max-seconds` stops cleanly between parts. `--quick` is a smoke test (about 2 min).
- Table numbers T1–T9 below refer to `tables.md`. Units are 10⁻³ metric. δ_n = max(0.002, 0.25 × paired sd) = 0.002 on both calibrated nodes.

## Setup

**Nodes (PILOT scales).**

| Node | per-run σ | ϱ local / structural | paired sd σ_d local / structural |
|---|---|---|---|
| `digits_mlp` | 0.0125 | 0.82 / 0.55 | 0.0075 (E1b manifest) / 0.0119 |
| `tabular_mlp` | 0.0084 | 0.85 / 0.60 | 0.0046 (rerun-2 manifest) / 0.0075 |

The split share of the paired variance (0.59 for digits, 0.65 for tabular) comes from the manifests' σ_s / σ_t.

**Proposal types** (T1). Each type has its own (π, μ, τ) and edit kind:
- a duplicate/inert type, π = 1;
- a harmful type, e.g. `batch_size`-like, μ = −0.012;
- a promising type, e.g. `hidden_units`-like, μ = +0.002 to +0.004;
- a neutral type;
- a structural, high-τ "bold" type.

The calibrated mixtures are:
- inert share: 0.60 (digits) and 0.70 (tabular) with memory off; 0.45 with memory on;
- share of informative proposals that improve: 0.28–0.30 with memory on, 0.42–0.43 with memory off.

**Noise models.**
- `iid` is T4 (A2): Δ̂ = Δ + σ_d z, so DI holds when the proposer is stationary.
- `record` is T4 §5. Each configuration has an error with a split part and a training part. A local edit inherits ϱ times its incumbent's error, and a keep makes the candidate's error the new record. This record channel makes the future Δ̂ depend on the keep decision, so DI fails here even when the proposer is stationary.

**Proposers.**
- `stationary`.
- `dimret`: μ falls by κ = 0.3 (or 0.8) per unit of true gain.
- `memory`: the share of bold edits among non-inert proposals rises logistically from its base to 0.6 as the displayed gain B − B₀ passes 2σ_d.
- `memory_debiased`: the same law, but it reads B̃ = Σ_keeps E[Δ | Δ̂] under the true per-proposal prior (T4 §5).

**Budget.** W = 20 or 40 runs. The LLM-call cap is N = 2W (N = W in the P10 check). A skip costs a call but no run.

**Policies.** Every policy emits (π̂, μ̂, τ̂) and applies T4 Propositions 6 and 8.
- **ρ:** keep iff Δ̂ > 0.
- **A1:** one constant prior per node, estimated on development campaigns, giving a constant Bayes threshold.
- **A2:** A1 plus perfect detection of rule-inert proposals, which are skipped.
- **"+screen":** E1 screening at price g. g is tuned on separate development seeds over the grid 0–0.5 σ_d.
- **Oracle:** the true per-proposal prior.
- **Imperfect predictors:**
  - calibrated: shrinks μ_n + noise toward the mean and inflates τ̂ accordingly;
  - raw: unshrunk noise;
  - μ̂ dispersion ×0 / 0.5 / 1.5 / 2;
  - τ̂ ×0.5 / ×2.

**Common random numbers.** Call c of campaign m uses the same draws under every policy, so policy contrasts are paired.

## Results by check

### 1. Proposition 7: per-proposal vs constant threshold (T3)

- **Stationary proposer, iid noise** (where Corollary 7a applies exactly, because the executions are the same):
  - The realised campaign gain matches the summed exact gap within 1–2 s.e. in all 8 cells, with ratios 0.98–1.02.
  - Example, digits_on at W = 20: realised +3.10 ± 0.04, predicted +3.04. Example, tabular_on at W = 20: +2.00 ± 0.03 vs +2.03.
  - The realised gain lies between the summed lower and upper bounds every time. Upper/realised is about 1.6–1.9 on memory-on nodes.
  - In δ_n per campaign, the threshold part alone is worth 1.0–1.55 at W = 20 and 2.0–3.0 at W = 40 with memory on, and 0.86 (tabular) to 2.2 (digits) at W = 20 with memory off.
- **Outside the scope of the identity:**
  - With feedback proposers, the realised gain is 0.6–0.9 of the gap summed along the oracle trajectory. The trajectories diverge, and with diminishing returns the bound is loose (upper bound about 3–5 × realised).
  - Under the record model, the moment-matched comparison gives realised/predicted 1.15–1.31. Against a dev-tuned constant threshold (shifted down by 0.2–0.4 σ_d, which compensates for the inflated record) it gives 0.36–0.89.

### 2. Proposition 8: screening (T4)

- **Lagrangian check** (no binding run budget, N = 40): the realised J_g gain equals Σ(g − V*)⁺ to within MC error in all iid cells, for g at 0.5, 1 and 2 × the tuned value, in both layers:
  - total, vs always executing;
  - the learned layer above rules. Example: digits_on at tuned g = 1.5 × 10⁻⁴ gives +0.86 ± 0.01 vs +0.86.

  Under the record model the realised gain is 0.1–0.3 × 10⁻³ above the formula.
- **Hard budget:**
  - With memory on, learned screening adds +1.9 (digits) and +0.7 (tabular) at W = 20, and +3.4 and +1.1 at W = 40. That is 1.3–2.3 × the Lagrangian term.
  - With memory off, the tuned g is 0 or nearly 0 (digits_off at W = 20: +0.10). The rules already remove 60–70 % of proposals, so the call cap N = 2W binds and a skip costs a proposal. This is T4 §4's "binding call cap raises the bar", seen here directly.

### 3. Proposition 9: record bias after a keep (T5)

- For every proposer (stationary, dimret, memory, memory_debiased), both policies (ρ and the oracle threshold) and both nodes, the mean observed new record error matches ϱe + σ_c λ(a) within 1–2 s.e. The residuals are ≤ 0.018 × 10⁻³ on means of 9–13 × 10⁻³, over 0.8–2 × 10⁵ keeps per cell.
- The iid analogue, σ_d λ((t − Δ)/σ_d), holds equally well.
- At a null keep the record rises by 5–12 × 10⁻³. At the end of a 40-run campaign it is biased by +15–22 × 10⁻³ (record model) or +21–65 × 10⁻³ (iid display), so the winner's curse holds whatever the proposer.
- **Route D (debiased display):**
  - B̃ removes the display bias: its end bias is ≈ 0 under iid. Under the record model it is negative, because the posterior mean ignores the record's conditional shift.
  - Debiasing lowers the share of bold edits from about 0.24–0.27 to 0.14–0.23.
  - **Whether that helps depends on the bold edits.** With the calibrated high-τ structural type, which has positive value under selection, debiasing *loses* 1.9–4.9 × 10⁻³. If bold edits are harmful (μ lowered by 1.2τ, so V(0) < 0), debiasing *gains* 1.0–3.4 × 10⁻³.
  - So the sign of route D's effect cannot be fixed by theory. It has to be measured (C4).

### 4. Proposition 10: myopic vs lookahead (T6)

The lookahead family is t = t*_n + σ_d(θ₀ + θ₁ · remaining fraction), with (θ₀, θ₁) tuned on development seeds.

- **Under DI** (iid noise, stationary proposer): the tuned lookahead never beats myopic on test seeds. The difference is 0.00 or −0.04 ± 0.01, consistent with Proposition 10(a).
- **Under DI-violating proposers** the loss of myopic within this family is small:
  - diminishing returns: ≤ 0.15 δ_n (κ = 0.8, W = 40);
  - memory-reading proposer under iid noise: ≤ 0.02 δ_n;
  - record channel: 0.03–0.20 δ_n;
  - record channel plus memory with raw B: up to 0.54 δ_n at W = 40, and 0.16–0.26 δ_n with debiased B̃.
- The record-channel gains come from *lowering* the threshold (θ₀ = −0.4), i.e. correcting for the inflated record, rather than from foresight about the proposer.
- The closed-form example of Proposition 10(b) is reproduced in the tests and in `parts/calibration.json` (loss 1.61 − α at β = 2, τ = 1).
- **Limit:** this family gives a lower bound on the dynamic-programming gain, not the optimum.

### 5. DI-test artefact and the selection bias of the value proxy (T7)

The branch study reproduces E1b/rerun-2 at W = 20: points 4/8/12, continue vs verify(r = 2) with the frozen response D̄ > 0, rule ρ, two repetitions per action, and decoding coupling q = 0.95.
- The proposer is **stationary, so DI holds for the proposer**.
- Inert share is 3 %, the metric-identical rate in the 19 Oct tables.
- A verify promotion makes the candidate's single-run metric the new record.

**Record-reference effect (T7a).**
- At changed points the record drops by 1.0–2.3 × 10⁻³ (tabular) and 1.5–6.7 × 10⁻³ (digits).
- The incumbent-relative Δ̂ contrast moves up by about (1 − ϱ) × that drop. For example, digits_hom with fixed split at ϱ = 0 gives +4.5 × 10⁻³ at next-1, the same order as the observed +4.7 next-3 shift.
- The absolute-metric contrast takes the remaining ϱ share, plus the incumbent change ±Δ_p. For the next trial the identity is exact: Δ̂ shift = abs shift − record shift. So **the absolute metric is free of the record artefact only when ϱ ≈ 0**. At ϱ = 0.5–0.8 its signed shift is −0.7 to −4.7 × 10⁻³ under DI.

**Distance criterion (T7b).**
- Under DI, the paired-null distance criterion flags the Δ̂ outcome at small-study rates of 0.1–1.0. It also flags the absolute metric (0.14–0.96) and even the true candidate value tv (0.33–0.96).
- These outcomes all contain the incumbent level, which differs by |Δ_p| at a changed point. Same-action repetitions and unchanged points do not carry that difference.
- Only the **audited increment over the branch's own incumbent** (ti) has excess ≈ 0 and a flag rate of 0.00 in every DI cell. It detects a genuine decision-dependent shift of 0.5 σ_d at rates of 0.92–1.00 (tabular) and 0.34–0.54 (digits).
- **Implication for C4:** a DI test needs audited increments, i.e. the C3 audit labels. Neither Δ̂ nor the absolute metric is a valid outcome, and neither is the absolute audited value without subtracting the incumbent.

**Selection bias of the value proxy.**
- Promotion requires D̄ > 0 after Δ̂ ≤ 0, and demotion requires D̄ ≤ 0 after Δ̂ > 0. So ±D̄ overstates the immediate value ±Δ in both directions, and the value residual is negative under DI.
- Expected residual under DI, fixed split, r = 2:

  | Scale / mix | Expected residual (10⁻³) | of which proxy bias | continuation part |
  |---|---|---|---|
  | tabular, homogeneous noise | −1.64 to −1.88 | +1.64 to +1.85 | ≈ 0 (|·| ≤ 0.04) |
  | tabular, "near-null" mix (half the edits are tweaks with Δ ≈ 0 and ϱ = 0.995) | −0.79 to −0.88 | | |
  | tabular, vary split | −1.2 to −2.8 | | |
  | digits, homogeneous noise | −1.2 to −2.4 (vary −2.1 to −4.0) | | +0.3 to +0.9 |

- The proxy bias / proxy ratio is stable at **0.83–0.88 for tabular** across all mixes, splits and ϱ, and 0.65–0.78 for digits.
- **Comparison with the 19 Oct memory-on tabular result:**
  - Observed proxy +0.83 × 10⁻³ × 0.83–0.88 gives an expected proxy-induced residual under DI of **about −0.7 × 10⁻³**, i.e. −0.69 to −0.73. The structural calibrations bracket it between −0.8 and −1.9.
  - The observed residual is −1.22 [−2.22, −0.26].
  - The C3 offline pilot (branch `overnight/c3-offline`, d0b8634, §3) measured the bias directly with selection-free fresh audits. Proxy +0.83 vs audited immediate −0.44 gives a proxy bias of **1.26 × 10⁻³**, and the residual becomes +0.04.
  - That direct estimate lies inside the simulated range (0.77–1.85 × 10⁻³ for tabular) and above the ratio estimate. Both say the negative residual is of the size DI plus selection predicts.
  - **The "violated in value terms" classification is therefore not supported.**
  - The small-study residual under DI has sd 1.7–2.8 × 10⁻³ for 18 tabular instances. That is wider than the reported bootstrap interval, which does not propagate D̄ error or the selection.
  - The digits memory-off residual, +0.51 [−2.59, +4.18], is also compatible: the simulated sd at 6 instances is 5.6–9.5 × 10⁻³.

### 6. Headroom map (T8, T9; C3 gate in δ_n per campaign)

**Oracle-prior control (threshold + screening) − A2+screen at W = 20, calibrated cells:**
- digits_on: +2.4 δ_n;
- tabular_on: +1.35;
- digits_off: +2.3;
- tabular_off: +0.87.

The W = 40 values are about double. The record model gives values 10–30 % larger.

**Map over inert share × dispersion of type means:**
- The gain falls steeply with the inert share. At inert 0.7 it clears 1 δ_n only when the sd of type means is ≥ about 0.8–1 σ_d.
- At inert ≤ 0.55, the default type heterogeneity is enough.
- Some of the gain at ×0 mean dispersion (+1–3.8 δ_n) comes from differences in τ and edit kind across types. It disappears in the homogeneous-τ map. That map clears δ_n only at sd(type means)/σ_d ≥ about 1.1 (inert 0.55) or ≥ 0.5 (inert 0.4).
- The map is non-monotone at ×3 dispersion with high inert share.

**Predictor quality** (T9, W = 20):
- A calibrated predictor with noise of 0.5 sd_types keeps about 70–87 % of the oracle gain. At 1 sd_types it keeps about 38–56 %: digits 0.93–1.06 δ_n, tabular 0.76–0.80 δ_n. At 2 sd_types the gain is ≤ 0.3 δ_n.
- Uncalibrated predictors are worse than A2 once their noise reaches 2 sd_types (−1.3 to −3.2 δ_n). So do a μ̂ with no dispersion that keeps the within-type τ̂ (−0.7 to −2.5 δ_n), and an overconfident τ̂ ×0.5 (−1.4 δ_n, digits).
- An over-dispersed μ̂ (×1.5) and an inflated τ̂ (×2) are nearly harmless.

**Reading for the C3 gate.**
- On memory-on nodes with the pilot-scale heterogeneity, the gate (≥ δ_n per 20-run campaign) is passable in principle.
- It needs a predictor whose μ error is about ≤ 0.5–1 sd of the type means and which is calibrated.
- On memory-off tabular even the oracle falls short of δ_n at W = 20.

## What the simulation supports

1. The T4 identities (Proposition 7's gap, Proposition 8's screening term, Proposition 9's inverse-Mills record bias) hold exactly where their assumptions hold, and the code reproduces them to MC error.
2. Proposition 9 holds for every proposer tested.
3. Under DI, myopic control is not beaten by the lookahead family. Under the DI violations modelled, the loss from staying myopic is ≤ 0.54 δ_n per campaign.
4. Incumbent-relative and absolute-metric DI contrasts are both contaminated under DI. Audited increments are the clean outcome.
5. The 19 Oct negative value residual is of the size that the selection bias of D̄ alone produces under DI.
6. The C3 headroom is mainly set by the inert share left after the rules and by predictor calibration.

## Limits

- **Model only:**
  - Gaussian increments, additive gains, and a hand-calibrated type mixture.
  - The memory proposer's law and its "bold" type are invented.
  - The branch study's verify/record mechanics follow the 19 Oct report description, not the harness code.
- **Calibration gaps:**
  - The simulated change rates (0.08–0.18 promotions) are below the observed rates (0.17 tabular, 0.33 digits).
  - The simulated D_null ≈ D_unchanged, whereas they differ in the data.
- **Simplified tests:**
  - The DI flag rule omits the bootstrap and Holm adjustment.
  - The lookahead family is a lower bound on the dynamic-programming gain.
  - The oracle with tuned g is not hard-budget optimal; for tabular it is sometimes slightly beaten by a lightly-noised calibrated predictor.
- **Not modelled:**
  - Duplicates are modelled as identical to the incumbent (Δ = 0).
  - Re-proposals of discarded configurations, verify actions in the campaign, and heavy tails are not modelled.
