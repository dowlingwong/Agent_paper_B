# M11 D8-PASS: search for a calibrated pass rule. Declaration before any run (16 November 2026)

**AI-assisted (Claude, Mac agent). Synthetic simulation only. Not an author decision. `gate.py` is not changed.**

**Authority.**
- R1-BX-D8-V3-A (`author-decisions-20261116` @ `4da73306`) fixes items 1–3: test side V1n; eligibility train + dev
  paired z ≥ 3 with dev denominator ≥ δ_n; split P3 = 1/3 : 1/6 : 1/2. It leaves items 4 (pass rule under D8-SKEW) and
  5 (per-tier test floor) to "a pre-declared unit that looks for the pass rule calibrated under every D8-SKEW scenario
  (per-arm false-pass ≤ 0.035, declared before running) with the highest power. If none qualifies, the default proposal
  is (c) with disclosure."
- The author's request of 16 Nov (10:33) names the candidates and the criterion, and asks for a P3 floor and a draft row
  R1-BX-D8-V3-B (items 4–5).

This file is committed before the script exists and before any run.

## 1. Model (unchanged from D8-SKEW)

The model is that of `M11_D8_SKEW_DECLARATION_20261115.md` §1. Its generator code is imported from
`r1/scripts/d8_skew_sim.py` (`noise`, `split_sizes`, `iqm_weights`, `lower`, `iqm_sorted`); the per-node draw order is
copied unchanged.
- d = μ_j + e.
- Two arms a_k = g·μ_j + h_k, with h_k = √0.5·c + √0.5·f_k (arm correlation 0.5).
- Noise e, c, f: normal, left-skewed (standardised −lognormal(0, 1)) or t3/√3.
- μ_j = μ (homogeneous) or μ·U(0.5, 1.5) (heterogeneous).
- Tiers: T0 is 8 nodes × 18 instances. T1 is 10 nodes × 12 instances (**T1 × 12, primary**) or 10 × 6
  (**T1 × 6, secondary**).
- Split **P3 only** (R1-BX-D8-V3-A (3)): test instances per node are T0 9, T1 6 (× 12) or 3 (× 6).
- Eligibility: train + dev paired z of d ≥ 3. δ_n is non-binding, as in D8-SKEW.
- Test side **V1n**: a nonpositive point test denominator on an eligible node is a STOP for every rule. A STOP and
  "no eligible node" count as not passing.
- Grid: 6 conditions (normal, left-skewed, t3 × hom, het) × 2 layouts × μ ∈ {0.5, 1, 1.5, 2} × g ∈ {0, 0.3}. That is
  96 scenarios.
- 400 reps per scenario and 2,000 node-stratified resamples per rep. Seeds 20261118 + condition index (new; not
  D8-SKEW's).

## 2. Candidate rules

Every rule keeps the gate's PoI conjunct: an arm passes only if the rule's primary test passes **and** the PoI lower
bound is > 0.5, as in `gate.py`. Primary-only rates are reported as well. In this section, "eligible nodes" are the k
IQM-eligible nodes; ā_j, s²_j and n_j are node j's test mean, variance and size for the arm.

- **(b2) Studentized IQM bound.** Exactly D8-SKEW's (b2): the delta-method per-node se, se(IQM) = √(Σ w_i² se_(i)²),
  and a resample with a nonpositive eligible-node denominator, a zero se\* or a non-finite t\* gets t\* = +∞. The lower
  bound is IQM̂ − q₀.₉₇₅(t\*)·ŝe.
- **(c) Node-stratified Student-t on the numerator.** Exactly D8-SKEW's (c). θ̂ = (1/k) Σ ā_j and ŝe² = Σ s²_j / (k² n_j).
  The test is a Welch–Satterthwaite Student-t. It passes if θ̂ − t₀.₉₇₅(df)·ŝe > 0; if ŝe = 0, it passes if θ̂ > 0. The
  gap-closed IQM is an effect size only.
- **(c′) Numerator with a node-stratified studentized bootstrap (bootstrap-t).**
  - Use the same resample indices as the other rules: θ\* = (1/k) Σ ā\*_j and se\*² = Σ s\*²_j / (k² n_j).
  - t\* = (θ\* − θ̂)/se\*, with t\* = +∞ if se\* = 0.
  - It passes if θ̂ − q₀.₉₇₅(t\*)·ŝe > 0; if ŝe = 0, it passes if θ̂ > 0.
- **(c″J) Johnson's skewness-corrected t on the numerator** (Johnson 1978, extended to the stratified mean).
  - T = θ̂/ŝe.
  - κ̂₃ = Σ m₃_j / (k³ n_j²), with m₃_j = n_j Σ (a − ā_j)³ / ((n_j − 1)(n_j − 2)).
  - γ̂ = κ̂₃ / ŝe³, and t_J = T + γ̂/6 + γ̂·T²/3.
  - It passes if t_J > t₀.₉₇₅(df), with the Welch–Satterthwaite df of (c). If ŝe = 0, it passes if θ̂ > 0.
- **(c″SR) Stratified signed-rank test on the numerator** (van Elteren weights).
  - W_j = Σ sign(a)·rank(|a|) within node j, with V_j = n_j(n_j + 1)(2n_j + 1)/6.
  - Z = Σ W_j/(n_j + 1) / √(Σ V_j/(n_j + 1)²).
  - It passes if Z > z₀.₉₇₅.
  - Its null is symmetry about 0, not a zero mean. It is included because the request names it as an example, and it
    is expected to be anti-conservative under left skew.

## 3. Metrics

Per scenario, rule and layout:
- false-pass at g = 0, per arm (arm 1) and two-arm ("either arm passes at 97.5 %", the gate's Holm pass), for the full
  rule and for the primary test alone;
- pass rate at g = 0.3, per arm and two-arm;
- P(STOP) and P(no eligible).

Monte Carlo SE at 400 reps: about 0.009 at 0.035.

## 4. Declared decision rule

1. **Calibrated (primary).** A rule is calibrated if its per-arm false-pass (full rule) is ≤ 0.035 in **every** one of
   the 24 T1 × 12 scenarios at g = 0 (6 conditions × 4 μ).
2. **Secondary.** The same check on the 24 T1 × 6 scenarios. Every exceedance, on either layout, is reported with its
   value.
3. **Recommendation.**
   - Among the primary-calibrated rules, those also calibrated on T1 × 6 rank first.
   - Within a group, the rule with the highest mean two-arm pass rate at g = 0.3 over the T1 × 12 scenarios with
     μ ≥ 1 (18 scenarios) is recommended.
   - Ties within 0.02 go to the rule with the lower maximum per-arm false-pass on T1 × 12.
   - Per-arm power and the μ = 0.5 scenarios are reported too.
4. **If no rule is primary-calibrated,** the unit says so and the draft row proposes (c) with its disclosure: its
   largest per-arm and two-arm false-pass and the conditions where they occur (R1-BX-D8-V3-A).
5. **Per-tier test floor for P3 (item 5).**
   - If the recommended rule is calibrated on T1 × 6 (3 test instances per T1 node), the proposed floor is T0 ≥ 9,
     T1 ≥ 3.
   - Otherwise it is T0 ≥ 9, T1 ≥ 6: T1 nodes then need 12 instances, and a T1 node below the floor is reported and
     handled as the author decides in V3-B.
   - Under P3, T0's 18 instances give 9 test instances, so T0 ≥ 9 is the T0 layout itself.
6. **The two-arm false-pass** is reported, but is not part of the per-arm criterion the author set. A two-arm rate above
   0.065 is flagged.

## 5. Outputs

- Script: `r1/scripts/d8_pass_sim.py`, committed before its run.
- Output: `docs/r1/reports/m11_d8_pass_20261116/sim_output.{json,md}`.
- Report: `docs/r1/reports/M11_D8_PASS_20261116.md`.
- Draft row: `docs/r1/proposals/R1_BX_D8_V3_B_DRAFT_20261116.md` (items 4–5), for the author.

Gate v3 waits for V3-B.
