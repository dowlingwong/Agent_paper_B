# M11 D8-SKEW: declaration of model, rules, metrics and the calibration decision rule (15 November 2026)

**AI-assisted (Claude, Mac agent). Committed before any simulation result of this unit is computed.** The only code
run before this commit was the 15 Nov D8-TEST unit (accepted at `1d34de18`). Synthetic only; `gate.py` is not
changed; not an author decision. Author's request of 15 Nov 21:37: a D8-SKEW simulation with the D8-TEST model and
layouts, V1n test side, R1 z ≥ 3, splits P2 and P3, normal, left-skewed, heavy-tailed t3 and heterogeneous per-node μ;
compare the false-pass rate at g = 0 (per arm and Holm over two arms) and the power at g = 0.3 of rules (a)–(d), with
the metrics and the "calibrated" rule declared before running.

## 1. Model (as `M11_D8_TEST_SIDE_20261115.md`, changes marked)

- Per node j and test instance: d = μ_j + e, and for **two arms** k = 1, 2: a_k = g·μ_j + h_k. e is independent of the
  arms. **New:** the arm noises are correlated 0.5 through a common factor, h_k = √0.5·c + √0.5·f_k, with c, f_1, f_2
  i.i.d. from the noise distribution. Train and dev instances carry d only (for eligibility).
- **Noise distributions** (each standardised to mean 0, sd 1): normal; left-skewed (−(lognormal(0, 1) − e^0.5)/sd, as
  on 14 and 15 Nov); **new:** Student-t with 3 degrees of freedom divided by √3.
- **Per-node μ.** Homogeneous: μ_j = μ. **New, heterogeneous:** μ_j = μ·u_j, u_j ~ Uniform(0.5, 1.5), drawn
  independently per node and replication. g is common to all nodes, so every per-node gap closed and every pooled
  ratio equals g.
- μ ∈ {0.5, 1, 1.5, 2}; g ∈ {0 (null), 0.3}. At g = 0 every rule's primary null is true: each node's ratio of means,
  each pooled ratio and the numerator mean are 0.
- **Layouts and splits.** T0 = 8 × 18; T1 = 10 × 12, all conditions. T1 = 10 × 6 for normal homogeneous only (cost).
  Splits P2 = 1/2 : 1/6 : 1/3 and P3 = 1/3 : 1/6 : 1/2.
- **Eligibility:** R1, paired z of d on train + dev ≥ 3 (δ_n non-binding). No eligible node is a STOP.
- **Test side:** V1n for every rule. STOP if an eligible node's point test denominator mean(d) ≤ 0. Rule (d) uses its own
  point STOP on the tier denominator instead, see below.
- **Bootstrap:** node-stratified, 2,000 resamples, one shared index draw per node for d, a_1, a_2. Lower bounds at
  level 0.975 (`numpy.quantile`, linear).

## 2. Rules

Every rule passes an arm iff its **primary bound** passes **and** the gate's PoI bound passes: the 97.5 % percentile
lower bound of PoI (mean over all nodes of the share of test instances with a_k > 0) is > 0.5. The primary-bound-only
rates are reported too, because under skew the PoI null is false at g = 0 and the PoI conjunct then does not protect.

- **(a) Current.** IQM across eligible nodes of the per-node ratio of means G_j = mean(a)/mean(d), with the gate's
  fractional weights. Percentile bootstrap. A resampled node denominator ≤ 0 sets that node's G\* to −∞ (V1n).
  Primary: lower bound > 0.
- **(b1) BCa** for the same IQM. Bias correction z0 = Φ⁻¹(share of IQM\* < IQM̂, ties counted one half). Acceleration
  from a stratified jackknife over every test instance of the eligible nodes, with each instance left out in turn:
  a = Σ(θ̄ − θ_(i))³ / (6 (Σ(θ̄ − θ_(i))²)^1.5). The lower bound is the IQM\* quantile at
  Φ(z0 + (z0 + z_α)/(1 − a(z0 + z_α))), with z_α = Φ⁻¹(0.025). If a jackknife denominator is ≤ 0, or z0 or a is not
  finite, the arm **fails**. Such reps are counted and reported.
- **(b2) Studentized bootstrap** for the same IQM.
  - Per node, the delta-method se of the ratio:
    se_j² = [var(a) + G_j² var(d) − 2 G_j cov(a, d)] / (n_j mean(d)²), with ddof 1.
  - se(IQM) = √(Σ_i w_i² se_(i)²), with the IQM weights on the sorted order. This approximation ignores the
    randomness of the trimming.
  - t\* = (IQM\* − IQM̂)/se\*. A resample with a node denominator ≤ 0, or with se\* = 0, gets t\* = +∞. That can only
    lower the bound (conservative).
  - Lower bound = IQM̂ − q_0.975(t\*)·ŝe.
- **(c) Numerator test.** Ā = (1/k) Σ_j mean(a_j) over the k eligible nodes, node-equal as the gate weights nodes.
  - se² = (1/k²) Σ_j s_j²/n_j, with ddof 1.
  - Student-t reference with Welch–Satterthwaite df: df = (Σ v_j)² / Σ (v_j²/(n_j − 1)), v_j = s_j²/(k² n_j).
  - Lower bound = Ā − t_{0.975, df}·se; primary: > 0. If se = 0, the bound is Ā.
  - "The PLAN's Student-t for heavy tails" (R1-BX-REVISIONS (c), E5) concerns soft labels. Here it is read as the
    Student-t reference distribution of the test in every noise condition. This reading is flagged for the author.
  - The gap-closed IQM is computed and reported as an effect size only.
- **(d) Tier-pooled ratio (V2's estimand), point STOP.**
  - G_j = mean(a_j)/D_T, where D_T is the mean of mean(d) over the eligible nodes of node j's tier. IQM across
    eligible nodes; percentile bootstrap.
  - STOP only if a tier's **point** D_T ≤ 0. The per-node point STOP of V1n does not apply to (d).
  - A resampled D_T\* ≤ 0 sets that tier's nodes to −∞, as in V1n.

**Holm over two arms.** The gate ranks an arm that passes at 97.5 % first. So the gate passes iff at least one arm
passes at 97.5 %. The two-arm false-pass rate is P(arm 1 or arm 2 passes) at g = 0; the two-arm power is the same at
g = 0.3 with both arms at g = 0.3.

## 3. Metrics (per scenario: noise × μ structure × layout × split × μ)

- per-arm false-pass rate at g = 0 (arm 1);
- two-arm (Holm) false-pass rate at g = 0;
- per-arm power and two-arm power at g = 0.3;
- the same rates for the primary bound alone;
- P(STOP), split into no-eligible and test-side;
- for (b1), the share of read reps in which BCa could not be computed.

400 replications per scenario. Standard errors: ≈ 0.008 at a rate of 0.025, ≈ 0.011 at 0.05, ≈ 0.025 at 0.5.
Seeds: 20261117 + condition index.

## 4. Decision rule for "calibrated" (declared before running)

- A rule is **calibrated in a condition** (noise × μ structure, on T1 × 12) iff, in every scenario of that condition
  (2 splits × 4 μ = 8 scenarios):
  - the per-arm false-pass rate is ≤ 0.035 (nominal 0.025 + about 1.3 SE), and
  - the two-arm false-pass rate is ≤ 0.065 (nominal family-wise 0.05 + about 1.4 SE).
- A rule is **calibrated** iff it is calibrated in all six T1 × 12 conditions: normal, left-skewed, t3, each
  homogeneous and heterogeneous. The T1 × 6 normal-homogeneous scenarios are reported against the same thresholds,
  as a secondary check.
- **Recommendation rule.** Among the calibrated rules, the recommended one has the highest mean two-arm power at
  g = 0.3 over the T1 × 12 scenarios with μ ≥ 1, averaged over conditions. Ties within 0.02 go to the simpler rule, in
  the order (c), (a), (d), (b2), (b1).
- If no rule is calibrated, the report says which conditions fail and by how much, recommends none, and leaves the
  choice to the author.
- With 8 scenarios per condition, a correctly calibrated rule can exceed a threshold by chance. The report states every
  exceedance with its value.

## 5. Not in scope

- No change to `gate.py`; no real data, labels or seeds.
- Heterogeneous g (where the per-node and pooled estimands differ) is not simulated.
- Track S appendix item 5 stays held.
