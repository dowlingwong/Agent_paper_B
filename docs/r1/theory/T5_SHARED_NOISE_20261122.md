# T5 re-run with a shared-component error model (`digits_mlp`)

*AI-assisted (Claude, subagent, 22 Nov 2026). Label `ENGINEERING_ONLY`. Every number here comes from a model; none is a measurement of the harness. The author has not checked the code or this note, and nobody has reviewed them. PLAN row R1-THEORY-RHO, decision (4) (branch `author-minsub-20261122`). Background: `P09_T4_PROP9.md` §4, `P04_T2_PROP4.md` §4, `P06_T4_PROP6.md` §4.1 and `check_kernel_e1.py` / `check_kernel_e1_output.txt` (branch `mac-proofpackets-20261122`; AI analysis, unreviewed).*

- **Code:**
  - `r1/theory/simulate_t4.py`: new noise model `shared`, helpers `shared_rho_w`, `effective_rho`, `shared_correlations` and `shared_share_for_partial`, a threshold-correction option (`Policy.ecorr`), a kernel-free-inequality counter (`kfree`) and a `trace` hook. `iid` and `record` are unchanged; the check is in "Reproduction" below.
  - `r1/theory/t5_shared_report.py`: the runner. It reuses T5's part functions unchanged.
  - `r1/theory/t5_shared_tables.py`: the tables.
  - Tests: `r1/tests/test_t5_shared_noise.py` (8 tests, unittest).
- **Output:** `results/r1/engineering/T5_shared_20261122/`:
  - `parts/*.json`: one file per part. The part name is `<T5 part name>__<model>`, and the T5 part name sets the seeds.
  - `tables.md`: all tables (S0–S8), generated.
  - `reproduction.json`: the re-run `iid` / `record` parts compared with the published T5 parts.
  - `manifest.json`: seeds, campaign counts, source SHA-256 and the git head.
  - `manifest.json` was rewritten after the last code change. That change touched only docstrings and added the `part_a1rho` and E1-pattern code. The part files were written by revisions whose simulation code is the same.
  - Total compute was 602 CPU-seconds, single-threaded (Linux, Python 3.13, NumPy 2.5.3).
- **Reproduce:**
  - `python -m r1.theory.t5_shared_report --out <dir>` (resumable, like T5);
  - then `python -m r1.theory.t5_shared_tables --out <dir>`.
- **Units:** 10⁻³ metric unless a column says δ_n. δ_n = 0.002 on `digits_mlp`.
- **Same seeds, policies, W and N as T5:** every re-run part uses the name of the T5 part it replaces, so it gets the same test and development seeds. Within a part, the `record`, control and `shared` runs draw the same main random stream; u comes from a separate generator. Their contrasts are therefore paired, as T5's policy contrasts are.

## 1. Construction

**Model.** In one campaign, each configuration c has the recorded error e(c) = u + w(c).
- u ~ N(0, sσ²) is drawn once per campaign and shared by every configuration. It stands for the common random numbers: every run of a campaign uses the same split and training seeds.
- w(c) is the per-configuration part, with variance (1 − s)σ². It keeps T5's split/training structure: the split share f = 0.59 of the variance is in the split component.
- w(c) also keeps T5's kernel between parent and child, applied per component: w(child) = r w(parent) + √(1 − r²) · fresh noise.

**Kernel coefficient.** The marginal correlation of a child with its unselected parent is s + (1 − s) r. Setting r = r_w(ϱ, s) = (ϱ − s)/(1 − s) makes it equal to the `record` model's ϱ. The following are then the same as in `record`:
- the per-run sd σ;
- the paired sd σ√(2(1 − ϱ));
- every comparison against an unselected incumbent.

This needs s ≤ ϱ. For an edit kind with ϱ < s, the code sets r = 0, so the per-configuration part is fresh. That kind's marginal correlation then becomes s, and the policies are told max(ϱ, s).

**Siblings.** Two children a, b of the same parent have correlation s + (1 − s) r_a r_b. Their partial correlation given the parent is

  p = s (1 − ϱ_a)(1 − ϱ_b) / ((1 − s) √((1 − ϱ_a²)(1 − ϱ_b²))),

which is s(1 − ϱ)/((1 − s)(1 + ϱ)) for two siblings of the same kind. In `record` (s = 0), p = 0: the parent screens off its children, which is the kernel property T4 Proposition 9 uses. The largest p reachable at a given ϱ is ϱ/(1 + ϱ), at s = ϱ, which is P09 §4's pure shared-factor model.

**What changes after a keep.** u cancels in every comparison: Δ̂ = Δ + w(cand) − w(inc). So a keep selects on w alone. After a keep, the law of the next candidate's error given the record's error e = u + w is no longer N(ϱe, σ_c²), and Proposition 9's formula is no longer true by construction. With s = 0, the `shared` code path draws exactly the numbers of `record` (test `test_s_zero_reproduces_record_bit_for_bit`).

**Helpers.**
- `shared_correlations(ϱ_a, ϱ_b, s)` computes, from the generative parameters, (i) the marginal parent–child correlations, and (ii) the sibling correlation and the sibling partial correlation given the parent. It also returns the closed form above.
- `shared_share_for_partial(p, ϱ)` inverts the closed form.

**Checked by simulation in two ways:**
- in the tests, by direct sampling of u + w, and on the simulator's own draws;
- in `parts/calibration.json`, on 200,000 campaigns of the simulator with no keeps, where the candidates of calls 1 and 2 are siblings:

| s | corr(parent, child): simulated / theory | sibling partial: simulated / theory |
|---|---|---|
| 0.7891 | 0.8209 / 0.8200 | 0.3693 / 0.3700 |
| 0.5500 | 0.8208 / 0.8200 | 0.1200 / 0.1209 |

## 2. Calibration to `digits_mlp`

T5's digits node: σ = 0.0125, ϱ local / structural = 0.82 / 0.55, split share 0.59. The target is the E1 sibling partial correlation +0.37, bootstrap interval [+0.24, +0.51] (`check_kernel_e1_output.txt`). It is applied to two local siblings (ϱ = 0.82): four of the five E1 edits correlate 0.71–0.86 with c0, which is local-like.

| model (column label) | s | r_w local / structural | marginal ϱ local / structural | structural paired sd | sibling partial: local–local / local–structural / structural–structural |
|---|---|---|---|---|---|
| `record` (T5) | 0 | 0.82 / 0.55 | 0.82 / 0.55 | 11.86 | 0 / 0 / 0 |
| `shared s=0.55` | 0.5500 | 0.600 / 0 | 0.82 / 0.55 | 11.86 | 0.121 / 0.207 / 0.355 |
| `shared s=0.71`: **lower end, p = 0.24** | 0.7082 | 0.383 / 0 | 0.82 / 0.708 | 9.55 | 0.240 / 0.315 / 0.415 |
| `shared s=0.79`: **target, p = 0.37** | 0.7891 | 0.147 / 0 | 0.82 / 0.789 | 8.12 | 0.370 / 0.404 / 0.441 |
| `shared s=0.82`: **upper end, p = 0.45 (maximum)** | 0.8200 | 0 / 0 | 0.82 / 0.820 | 7.50 | 0.451 / 0.451 / 0.451 |
| `record, ϱ_struct=0.79` (control) | 0 | 0.82 / 0.789 | 0.82 / 0.789 | 8.12 | 0 / 0 / 0 |

Three facts about this calibration are not optional. Each follows from the construction.

1. **The upper end 0.51 cannot be reached at ϱ_local = 0.82.** The model's maximum is 0.82/1.82 = 0.4505, at s = 0.82, where the per-configuration part is fresh (r_w = 0). That point is run as the upper sensitivity end instead of 0.51.

2. **At the target, structural edits cannot keep T5's ϱ = 0.55.** Every pair of configurations has correlation ≥ s, and s = 0.789 > 0.55. Their marginal correlation becomes 0.789, and their paired sd falls from 11.86 to 8.12 × 10⁻³. Two extra columns separate the shared component from this side effect:
   - **`record, ϱ_struct=0.79`:** the record model with the same marginal correlations as `shared s=0.79`. Comparing `shared s=0.79` with it isolates u at the target.
   - **`shared s=0.55`:** the largest share at which both kinds keep T5's ϱ exactly. Comparing it with `record` isolates u at T5's parameters, but at a sibling partial of only 0.12.

3. **The u + w model cannot reproduce the E1 pattern exactly.** E1's marginal correlations on digits are 0.77, 0.82, 0.60, 0.71 and 0.86. At the largest s compatible with all five (s = 0.60), the model's mean sibling partial over the 10 E1 pairs is 0.206 (0.137 at s = 0.5; `parts/calibration.json`). That is below the observed 0.37 and below the interval's lower end. The observed screening failure on digits is therefore larger than a single shared component with T5's kernel can produce at E1's own marginal correlations. Heterogeneous loadings, or noise in the 30-seed estimate, are possible readings; this run does not decide between them.

## 3. Reproduction check

The `iid` and `record` parts, re-run with the new code and the T5 part names, are identical to the published T5 parts (`results/r1/engineering/T5_20261019T004918Z/parts`) in every stored value, with one exception: s.e. and residual summaries in four parts (P7 dimret iid, P8 iid and record, P9) differ by ≤ 4 × 10⁻¹⁵ relative (`reproduction.json`).

The same last-digit differences appear when the unmodified `simulate_t4.py` (HEAD) is run on this host, so they come from the platform's floating-point summation, not from the change. A direct comparison of the old and new `simulate()` on this host gave identical output in all 96 cases tried:
- three scenarios;
- `iid` and `record`;
- four proposers;
- four policies, including screening and lookahead.

The existing T5 tests (`r1/tests/test_t5_simulate.py`, 14) pass.

## 4. Results by T5 quantity

Columns, in order: iid | record | record, ϱ_struct = 0.79 (control) | shared s = 0.55 | shared s = 0.71 (p = 0.24) | **shared s = 0.79 (p = 0.37)** | shared s = 0.82 (p = 0.45). Full tables are in `tables.md`, sections S1–S8.

### 4.1 Proposition 9: record bias after a keep (T5 T5; digits_on, W = 40, N = 80; `tables.md` S4)

The residual is the observed new record error e′ minus T4's formula ϱe + σ_c λ(a), with the marginal ϱ. For iid it is Δ̂ − Δ at a keep against σ_d λ((t − Δ)/σ_d). The first table shows the stationary proposer under rule ρ; the range is over all 8 proposer × policy rows.

| quantity | iid | record | ctl | s=0.55 | s=0.71 | **s=0.79** | s=0.82 |
|---|---|---|---|---|---|---|---|
| residual, all keeps (± s.e.) | +0.012 ± 0.016 | −0.004 ± 0.016 | −0.004 ± 0.015 | −1.117 ± 0.017 | −1.586 ± 0.017 | **−1.894 ± 0.016** | −2.020 ± 0.016 |
| range over the 8 rows | −0.011…+0.018 | −0.018…+0.004 | −0.022…+0.007 | −1.386…−0.999 | −1.810…−1.497 | **−1.966…−1.782** | −2.030…−1.894 |
| residual, first keep of a campaign | – | +0.003 | +0.023 | −0.439 | −0.682 | **−0.910** | −1.056 |
| residual, later keeps | – | −0.006 | −0.010 | −1.313 | −1.867 | **−2.211** | −2.337 |
| mean e′ observed / formula | +6.22 / +6.21 | +13.38 / +13.39 | +12.75 / +12.76 | +8.30 / +9.42 | +5.82 / +7.40 | **+4.23 / +6.12** | +3.49 / +5.51 |
| null keeps: mean rise / formula | +10.28 / +10.27 | +9.04 / +9.04 | +8.45 / +8.45 | +8.42 / +8.97 | +7.86 / +8.63 | **+7.45 / +8.40** | +7.25 / +8.29 |
| null-keep rise, range over the 8 rows | +9.27…+12.37 | +7.03…+9.68 | +6.50…+8.65 | +6.05…+8.83 | +5.58…+8.11 | **+5.22…+7.65** | +5.04…+7.45 |
| record bias at the end, range over the 8 rows | +35.86…+65.12 | +18.96…+22.56 | +17.32…+21.25 | +11.81…+13.82 | +8.10…+10.02 | **+5.93…+7.61** | +5.08…+6.56 |

**The formula fails under `shared`, for every proposer.**
- It overstates the new record error, by 1.8–2.0 × 10⁻³ at the target, on observed means of 3.0–4.5 × 10⁻³.
- It is already off at a campaign's first keep. The keep at call n follows n − 1 discarded siblings of the same incumbent. Given e, those siblings are correlated with the candidate (p > 0), and they were selected low. So the past discards lower the candidate's expected error, which a Markov kernel would not allow.

**What survives.**
- A null keep still raises the record in every cell: +5.2 to +7.7 × 10⁻³ at the target.
- The end-of-campaign record bias stays positive but is about a third of the record model's: 5.9–7.6 against 19.0–22.6. Part of the record error, u, is never selected.

**Kernel-free inequality (P09 §4).** It is checked on every keep of the 8 rows above, in every model. It holds as stated on every keep, with no violation:

| model | keeps | violations of e′ > e − Δ + t (any rule) | keeps with t ≥ 0 / violations of e′ > e − Δ | null keeps with t ≥ 0 / violations of e′ > e | keeps with t < 0 / of which e′ ≤ e − Δ |
|---|---|---|---|---|---|
| iid | 1,234,088 | 0 | 874,545 / 0 | 309,612 / 0 | 359,543 / 81,903 |
| record | 930,144 | 0 | 601,649 / 0 | 175,012 / 0 | 328,495 / 91,269 |
| record, ϱ_struct = 0.79 | 1,020,729 | 0 | 696,932 / 0 | 184,972 / 0 | 323,797 / 88,378 |
| shared s = 0.55 | 807,782 | 0 | 491,443 / 0 | 127,734 / 0 | 316,339 / 95,633 |
| shared s = 0.71 | 805,541 | 0 | 501,157 / 0 | 113,856 / 0 | 304,384 / 95,301 |
| shared s = 0.79 | 809,793 | 0 | 513,172 / 0 | 104,968 / 0 | 296,621 / 94,782 |
| shared s = 0.82 | 812,898 | 0 | 519,321 / 0 | 100,433 / 0 | 293,577 / 94,613 |

The inequality is an identity of the decision rule (keep ⇔ e′ − e + Δ > t), so this checks the code, and it holds for every error law, as P09 §4 says.

The last column is not a violation:
- P09's form e′ > e − Δ is for the default rule (t = 0) or t ≥ 0.
- With a negative per-proposal threshold, which the oracle-threshold policy uses for promising types, a keep can have e′ ≤ e − Δ.
- Every keep of rule ρ is in the t ≥ 0 column.

**Route D (debiased display), debiased − raw gain** (memory-reading proposer, W = 40):

| bold edits / policy | iid | record | ctl | s=0.55 | s=0.71 | **s=0.79** | s=0.82 |
|---|---|---|---|---|---|---|---|
| as calibrated / ρ | −2.58 | −2.92 | −3.80 | −2.53 | −3.00 | **−3.14** | −3.15 |
| as calibrated / oracle thr. | −2.27 | −1.93 | −3.37 | −1.35 | −2.65 | **−3.37** | −3.51 |
| harmful bold / ρ | +3.38 | +2.02 | +1.58 | +1.41 | +1.08 | **+0.92** | +0.81 |
| harmful bold / oracle thr. | +3.03 | +3.02 | +2.80 | +2.80 | +2.47 | **+2.20** | +2.12 |

(s.e. 0.04–0.11.)

### 4.2 Value of the per-proposal rule vs the default, and oracle headroom (T5 T2; `tables.md` S1, S1b)

Paired contrasts at the T5 seeds, ± paired s.e. (S1b):

| cell | contrast | iid | record | ctl | s=0.55 | s=0.71 | **s=0.79** | s=0.82 |
|---|---|---|---|---|---|---|---|---|
| digits_on W20 | A2 − ρ | +7.50 ± 0.09 | +5.47 ± 0.08 | +6.94 ± 0.08 | +3.99 ± 0.08 | +4.34 ± 0.08 | **+4.64 ± 0.08** | +4.72 ± 0.08 |
| digits_on W40 | A2 − ρ | +15.55 ± 0.13 | +8.40 ± 0.11 | +12.08 ± 0.11 | +5.02 ± 0.10 | +5.96 ± 0.11 | **+7.05 ± 0.11** | +7.60 ± 0.11 |
| digits_off W20 | A2 − ρ | +13.05 ± 0.10 | +11.32 ± 0.09 | +12.32 ± 0.09 | +9.85 ± 0.09 | +9.86 ± 0.09 | **+9.96 ± 0.09** | +10.06 ± 0.09 |
| digits_off W40 | A2 − ρ | +26.44 ± 0.14 | +20.54 ± 0.13 | +23.12 ± 0.13 | +17.17 ± 0.13 | +17.67 ± 0.13 | **+18.33 ± 0.14** | +18.72 ± 0.14 |
| digits_on W20 | A1 − ρ | +1.19 ± 0.05 | +0.01 ± 0.05 | +0.22 ± 0.04 | −0.69 ± 0.05 | −0.81 ± 0.04 | **−0.93 ± 0.04** | −1.03 ± 0.04 |
| digits_on W40 | A1 − ρ | +2.50 ± 0.08 | −1.21 ± 0.07 | −0.49 ± 0.05 | −2.71 ± 0.07 | −2.85 ± 0.06 | **−2.83 ± 0.06** | −2.84 ± 0.06 |
| digits_off W20 | A1 − ρ | −0.04 ± 0.03 | −0.41 ± 0.03 | −0.35 ± 0.03 | −0.73 ± 0.03 | −0.83 ± 0.03 | **−0.94 ± 0.03** | −0.96 ± 0.03 |
| digits_off W40 | A1 − ρ | −0.04 ± 0.05 | −1.32 ± 0.05 | −1.07 ± 0.04 | −2.09 ± 0.05 | −2.24 ± 0.05 | **−2.27 ± 0.05** | −2.28 ± 0.05 |

Oracle-prior control (threshold + screening) − A2+screen, in δ_n per campaign (the C3 headroom, T5 §6):

| cell | iid | record | ctl | s=0.55 | s=0.71 | **s=0.79** | s=0.82 |
|---|---|---|---|---|---|---|---|
| digits_on W20 | +2.41 | +2.71 | +2.66 | +3.03 | +3.18 | **+3.24** | +3.26 |
| digits_on W40 | +4.73 | +5.95 | +5.69 | +6.84 | +7.30 | **+7.34** | +7.30 |
| digits_off W20 | +2.31 | +2.94 | +2.83 | +3.62 | +3.96 | **+4.12** | +4.16 |
| digits_off W40 | +4.52 | +7.05 | +6.62 | +8.94 | +9.44 | **+9.56** | +9.53 |

How large these are, as a ratio to iid:
- **Record:** 1.12, 1.26, 1.27 and 1.56.
- **Shared at the target:** 1.34, 1.55, 1.78 and 2.12.

**What the shared component does to the policy contrasts.**
- It lowers the value of the deployed per-proposal rule over the default. A2 − ρ falls, in 10⁻³:
  - by 0.8–2.2 at the target relative to record;
  - by 2.3–5.0 relative to the target's control (u alone);
  - by 1.5–3.4 at s = 0.55 relative to record (u alone at T5's ϱ).
- It makes A1 worse than the default in every cell.
- It raises the gap between the oracle prior and A2.
- In every record-like column the default rule's false-keep rate falls (digits_on W20: 0.377 iid, 0.340 record, 0.263 at the target; S1).

### 4.3 Proposition 7: per-proposal vs constant threshold (T5 T3; W = 20; `tables.md` S2)

| cell | quantity | iid | record | ctl | s=0.55 | s=0.71 | **s=0.79** | s=0.82 |
|---|---|---|---|---|---|---|---|---|
| on, stationary | moment-matched: realised / Σ gap | 1.02 | 1.25 | 1.14 | 1.48 | 1.53 | **1.57** | 1.58 |
| on, stationary | dev-tuned shift (σ_d); realised / Σ gap | 0.0; 1.02 | −0.4; 0.72 | −0.2; 0.92 | −0.6; 0.43 | −0.6; 0.36 | **−0.6; 0.33** | −0.6; 0.32 |
| on, dimret | moment-matched; dev-tuned | 0.67; 0.67 | 0.73; 0.36 | 0.64; 0.46 | 0.87; 0.21 | 0.91; 0.17 | **0.89; 0.15** | 0.88; 0.13 |
| on, memory | moment-matched; dev-tuned | 0.90; 0.90 | 1.31; 0.49 | 1.02; 0.68 | 1.58; 0.20 | 1.65; 0.18 | **1.63; 0.19** | 1.62; 0.19 |
| off, stationary | moment-matched; dev-tuned | 1.01; 1.02 | 1.31; 0.87 | 1.27; 0.91 | 1.61; 0.64 | 1.74; 0.65 | **1.82; 0.66** | 1.84; 0.66 |

Under `shared` the dev-tuned constant shift is −0.6 σ_d in every cell. That is **the lower edge of T5's grid**, so the dev-tuned constant baseline may be stronger than shown, and its ratio smaller than the true one.

### 4.4 Proposition 8: screening (T5 T4; digits_on; `tables.md` S3)

| quantity | iid | record | ctl | s=0.55 | s=0.71 | **s=0.79** | s=0.82 |
|---|---|---|---|---|---|---|---|
| Lagrangian, learned layer, g × 1: realised / Σ(g − V*)⁺ | +0.86 / +0.86 | +0.93 / +0.86 | +0.91 / +0.86 | +1.00 / +0.86 | +1.02 / +0.86 | **+1.03 / +0.86** | +1.04 / +0.86 |
| Lagrangian, learned layer, g × 2 | +2.17 / +2.18 | +2.41 / +2.17 | +2.32 / +2.17 | +2.72 / +2.17 | +2.75 / +2.17 | **+2.73 / +2.17** | +2.74 / +2.17 |
| hard budget W = 20: gain of learned screening | +1.92 ± 0.05 | +1.77 ± 0.04 | +2.04 ± 0.04 | +1.71 ± 0.04 | +1.90 ± 0.04 | **+2.04 ± 0.04** | +2.07 ± 0.04 |
| hard budget W = 40 | +3.37 ± 0.06 | +3.09 ± 0.06 | +3.61 ± 0.06 | +3.04 ± 0.06 | +3.35 ± 0.06 | **+3.57 ± 0.06** | +3.72 ± 0.06 |

The excess of the realised gain over the Lagrangian formula, over all six Lagrangian rows, is:
- 0.07–0.24 × 10⁻³ under record;
- 0.17–0.56 × 10⁻³ at the target.

The hard-budget screening gain at the target equals its control (2.04 vs 2.04; 3.57 vs 3.61). So the change from record comes from the structural paired sd, not from u.

### 4.5 Feedback contrasts: lookahead − myopic (T5 T6; digits_on, N = W; δ_n; `tables.md` S5)

The cells give lookahead − myopic in δ_n, with the tuned (θ0, θ1) in brackets.

| W | case | record | ctl | s=0.55 | s=0.71 | **s=0.79** | s=0.82 |
|---|---|---|---|---|---|---|---|
| 20 | channel only | +0.05 (−0.4, +0.4) | +0.03 | +0.09 | +0.13 | **+0.13 (−0.2, 0.0)** | +0.15 |
| 20 | + memory, raw B | +0.09 | +0.05 | +0.24 | +0.23 | **+0.21 (−0.4, 0.0)** | +0.19 |
| 20 | + memory, debiased B̃ | +0.06 | +0.03 | +0.11 | +0.14 | **+0.14** | +0.15 |
| 40 | channel only | +0.20 (−0.4, +0.4) | +0.12 | +0.58 | +0.59 | **+0.54 (−0.4, 0.0)** | +0.52 |
| 40 | + memory, raw B | +0.54 (−0.4, 0.0) | +0.18 | +1.00 | +0.88 | **+0.75 (−0.4, 0.0)** | +0.68 |
| 40 | + memory, debiased B̃ | +0.26 | +0.16 | +0.73 | +0.66 | **+0.59** | +0.57 |

The iid cases are re-run with the T5 seeds and are identical to T5 (DI holds: −0.02 at W = 20, +0.00 at W = 40).

As under record, the gains come from **lowering** the threshold. θ0 = −0.4 is the lowest value in T5's grid, and it is chosen in every W = 40 shared cell. So these are lower bounds even within the family (§4.8 measures the correction directly).

### 4.6 Decision-independence test artefact and value-proxy bias (T5 T7; digits homogeneous study, ϱ = 0.8; `tables.md` S6)

In the branch study, u is common to both branches of an instance and to both runs of every comparison. It therefore cancels in every contrast and distance, and the shared model is the kernel branch study at the per-configuration kernel coefficient r_w. The partial targets give these shares at ϱ = 0.8:

| p target | s | r_w |
|---|---|---|
| 0.24 | 0.684 | 0.368 |
| 0.37 | 0.769 | 0.134 |
| maximum 0.44 | 0.8 | 0 |

s = 0.5 keeps the structural ϱ = 0.5 of T5's branch study.

| fixed split | record | s=0.5 | s=0.68 | **s=0.77** | s=0.80 |
|---|---|---|---|---|---|
| record shift at changed points | −3.67 | −3.73 | −3.56 | **−3.50** | −3.46 |
| Δ̂ shift, next 1 / 3 | +1.09 / +1.00 | +2.28 / +1.97 | +3.10 / +2.53 | **+3.85 / +2.96** | +4.36 / +3.21 |
| abs-metric shift, next 1 / 3 | −2.59 / −2.30 | −1.45 / −1.05 | −0.46 / −0.09 | **+0.35 / +0.62** | +0.90 / +1.10 |
| true value (tv) shift, next 1 / 3 | +0.76 / +0.77 | +0.91 / +0.99 | +0.98 / +1.12 | **+0.94 / +1.10** | +1.03 / +1.20 |
| audited increment (ti) shift, next 1 / 3 | +0.01 / +0.01 | +0.01 / +0.02 | +0.02 / +0.03 | **+0.01 / +0.02** | +0.05 / +0.04 |
| flag rate Δ̂1 · abs1 · tv1 · ti1 | 0.16 · 0.25 · 0.44 · 0.00 | 0.26 · 0.28 · 0.44 · 0.00 | 0.33 · 0.29 · 0.43 · 0.00 | **0.40 · 0.33 · 0.40 · 0.00** | 0.44 · 0.36 · 0.40 · 0.00 |
| proxy bias; expected residual; bias / proxy | +2.75; −2.41; 0.78 | +2.61; −1.90; 0.74 | +2.37; −1.51; 0.71 | **+2.33; −1.42; 0.71** | +2.25; −1.27; 0.70 |

**Vary split, ϱ = 0.8, record → target (s = 0.77):**
- Δ̂ next-1: +1.97 → +6.99.
- abs next-1: −4.75 → +0.47.
- ti: −0.01 → −0.02.
- Flag rates (Δ̂1, ti1): 0.29 → 0.76 and 0.00 → 0.00.
- Expected residual: −4.03 → −2.19.
- Bias / proxy: 0.77 → 0.71.

**DI-violating control** (fixed split, ϱ = 0.5, feedback +0.5 σ_d; T5's cell and seed; shared at the model's maximum for ϱ = 0.5, s = 0.5, p = 0.33):
- ti next-1 shift: +0.80 (record) → +1.12 (shared).
- ti flag rate: 0.34 → 0.34.

### 4.7 Predictor quality (T5 T9; digits_on, W = 20; vs A2+screen, δ_n; `tables.md` S7)

| predictor | iid | record | ctl | s=0.55 | s=0.71 | **s=0.79** | s=0.82 |
|---|---|---|---|---|---|---|---|
| calibrated, noise 0 (oracle prior) | +2.44 | +2.76 | +2.72 | +3.13 | +3.28 | **+3.34** | +3.35 |
| calibrated, noise 0.5 sd_types | +1.78 | +1.94 | +1.95 | +2.11 | +2.15 | **+2.17** | +2.18 |
| calibrated, noise 1 sd_types | +0.93 | +1.06 | +1.19 | +1.14 | +1.22 | **+1.25** | +1.27 |
| raw (uncalibrated), noise 2 sd_types | −3.16 | −2.27 | −2.31 | −1.54 | −1.15 | **−1.06** | −1.02 |
| μ̂ dispersion × 0 | −2.53 | −2.34 | −2.58 | −2.03 | −2.01 | **−2.12** | −2.17 |
| τ̂ × 0.5 | −1.43 | −0.92 | −0.42 | −0.31 | +0.17 | **+0.49** | +0.63 |
| τ̂ × 2 | +1.71 | +2.47 | +2.30 | +2.83 | +2.88 | **+2.83** | +2.80 |

The paired s.e. of the τ̂ × 0.5 row is 0.075–0.089 × 10⁻³, i.e. about 0.04 δ_n (`parts/predictor_*`).

### 4.8 Threshold correction for a selected incumbent (new; N = 2W, no screening; `tables.md` S8)

Three keep rules are compared:
- **none:** the deployed t* = −μσ_d²/τ² (T4 Proposition 6).
- **known:** an oracle that knows the incumbent's inherited error x. In `record`, x = e; in `shared`, x = w(inc). Given x, Δ̂ ~ N(Δ − (1 − r)x, s_f²), so the Bayes threshold is −(1 − r)x + t*(μ, τ, s_f), where r is the kernel coefficient and s_f the fresh-noise sd. Knowing x is more information than the history, so this is an **upper bound** on what any history-based correction (E[e | history], P06 §4.1) can be worth.
- **table:** a feasible correction, P06's t** with E[x | k] and Var(x | k), where k is the number of keeps so far. It is fitted on development campaigns by two fixed-point passes. It conditions on less than the full history, so it is a **lower bound** on the Bayes correction.

The Bayes correction given the history lies between table and known. In iid, comparisons are fresh and no correction applies.

Corrected − uncorrected gain, in δ_n per campaign:

| cell | base | rule | record | ctl | s=0.55 | s=0.71 | **s=0.79** | s=0.82 |
|---|---|---|---|---|---|---|---|---|
| digits_on W20 | oracle prior | table / known | +0.21 / +0.69 | +0.10 / +0.34 | +0.52 / +1.67 | +0.48 / +1.69 | **+0.47 / +1.84** | +0.44 / +1.93 |
| digits_on W20 | A2 | table / known | +0.59 / +1.18 | +0.28 / +0.64 | +1.24 / +2.68 | +1.32 / +2.94 | **+1.38 / +3.27** | +1.37 / +3.48 |
| digits_on W40 | oracle prior | table / known | +1.01 / +1.96 | +0.51 / +0.97 | +1.82 / +4.17 | +1.63 / +4.08 | **+1.37 / +4.14** | +1.28 / +4.34 |
| digits_on W40 | A2 | table / known | +2.37 / +3.61 | +1.42 / +2.16 | +4.11 / +7.18 | +4.27 / +7.68 | **+4.12 / +8.06** | +4.03 / +8.45 |
| digits_off W20 | oracle prior | table / known | +0.11 / +0.46 | +0.05 / +0.25 | +0.22 / +1.10 | +0.20 / +1.16 | **+0.18 / +1.30** | +0.15 / +1.42 |
| digits_off W20 | A2 | table / known | +0.81 / +1.37 | +0.63 / +1.02 | +1.63 / +2.97 | +1.91 / +3.57 | **+2.10 / +4.17** | +2.17 / +4.55 |
| digits_off W40 | oracle prior | table / known | +0.42 / +1.19 | +0.21 / +0.64 | +0.63 / +2.50 | +0.53 / +2.50 | **+0.46 / +2.73** | +0.41 / +2.98 |
| digits_off W40 | A2 | table / known | +3.08 / +4.21 | +2.46 / +3.27 | +5.22 / +7.96 | +5.63 / +9.02 | **+5.70 / +9.97** | +5.73 / +10.64 |

All contrasts are paired. The s.e. is 0.02–0.12 × 10⁻³, i.e. ≤ 0.06 δ_n (S8).

**The deployed rule is conservative in every record-like model, as PLAN R1-THEORY-RHO (2) states.** Its mean executed threshold is too high, and it keeps too few. Example, digits_on W20, oracle prior, target model, uncorrected → known:
- mean executed threshold: +4.71 → +0.42 × 10⁻³;
- keeps: 3.86 → 5.16;
- false-keep rate: 0.204 → 0.223;
- gain: +3.68 × 10⁻³.

The same direction holds in every cell of S8.

## 5. T5's conclusions under the shared model

"Target" means s = 0.79 (p = 0.37); the range is over the sensitivity ends s = 0.71 and s = 0.82 unless stated. Comparisons are with T5's record model at the same seeds; "attributable to u" compares the target with its control, or s = 0.55 with record.

| T5 conclusion (section of `T5_SIMULATION.md`) | under `shared` | verdict |
|---|---|---|
| §1, §2, §4, "supports" 1: identities exact where their assumptions hold (iid, stationary); under DI the lookahead does not beat myopic | iid cells re-run, identical to T5 | **unchanged** (not affected by the noise model) |
| §1: under record, Prop 7 moment-matched realised/predicted 1.25–1.31 (digits stationary/memory/off) | 1.57 / 1.63 / 1.82 (sensitivity 1.53–1.84); dimret 0.73 → 0.89 | **changed in size** |
| §1: dev-tuned constant shifted down 0.2–0.4 σ_d under record | −0.6 σ_d in every cell (grid edge); ratio 0.72 → 0.33 (stationary) | **changed in size** (lower bound: grid edge) |
| §2: Lagrangian screening formula; record realised 0.1–0.3 above it | 0.17–0.56 above (target) | **changed in size** |
| §2: hard-budget learned screening gain (digits_on: +1.77 / +3.09 record at W20 / 40) | +2.04 / +3.57, equal to the control (2.04 / 3.61) | **unchanged** as far as u is concerned (the shift comes from the structural ϱ) |
| §3, "supports" 2: Prop 9's formula matches the record model within 1–2 s.e. for every proposer | fails for every proposer: residual −1.78 to −1.97 × 10⁻³ (target), already −0.85 to −0.91 at the first keep; the formula overstates e′ | **changed**: the formula no longer holds. The residual moves from 0 to negative; it is not a sign flip of an existing effect. The kernel-free inequality holds on every keep (0 violations in ≈ 0.8–1.2 M keeps per model) |
| §3: null keeps raise the record (+7.0 to +9.7 record); end bias +19 to +23 (record); winner's curse for every proposer | null-keep rise +5.2 to +7.7; end bias +5.9 to +7.6 (target) | **unchanged in sign, smaller in size** |
| §3: route D's sign depends on the bold edits (calibrated: debiasing loses; harmful: it gains) | calibrated −3.14 / −3.37; harmful +0.92 / +2.20 (target) | **unchanged in sign** (sizes change) |
| §4, "supports" 3: under the DI violations, myopic loses ≤ 0.54 δ_n; the record-channel gains come from lowering the threshold | up to +0.75 δ_n at the target and +1.00 δ_n at s = 0.55 (raw B, W = 40); channel only +0.54 (vs +0.20); θ0 at the grid's lowest value | **changed in size** (bound roughly doubles); mechanism (lower threshold) **unchanged** |
| §5 T7a: Δ̂ contrast moves up by about (1 − ϱ) × record drop | moves up by (1 − r_w) × drop: +3.85 vs +1.09 (fixed), +6.99 vs +1.97 (vary) | **changed in size** |
| §5 T7a: absolute metric is free of the record artefact only at ϱ ≈ 0; at ϱ = 0.5–0.8 its signed shift is −0.7 to −4.7 under DI | at ϱ = 0.8 the shift is +0.35 / +0.62 (fixed) and +0.47 / +0.99 (vary) at the target, close to the true-value shift; −0.46 at p = 0.24; −1.45 at s = 0.5 | **changed in sign** at the target and the upper end (what matters is r_w, not ϱ) |
| §5 T7b, "supports" 4: only the audited increment (ti) is clean (flag rate 0.00 under DI) and detects a real shift | ti flag rate 0.00 in every shared DI cell; power 0.34 → 0.34 in the feedback cell | **unchanged** |
| §5: value residual negative under DI; proxy bias / proxy 0.65–0.78 on digits | residual −1.42 (fixed) / −2.19 (vary) at the target, vs −2.41 / −4.03; ratio 0.71 | **unchanged in sign, smaller in magnitude**; ratio inside T5's digits range. Not re-run: the tabular comparison with the 19 Oct result ("supports" 5) |
| §6: oracle − A2+screen headroom; record 10–30 % larger than iid (digits: ×1.12–1.56) | ×1.34–2.12 of iid (target); +3.24 δ_n at digits_on W20 vs +2.71 record | **changed in size** (larger) |
| T2 / value of the per-proposal rule: A2 − ρ > 0 | +4.64 / +7.05 / +9.96 / +18.33 vs +5.47 / +8.40 / +11.32 / +20.54 (record) | **unchanged in sign, smaller** |
| T2: A1 (constant threshold) vs default ρ | −0.93, −2.83, −0.94, −2.27 (target) vs +0.01, −1.21, −0.41, −1.32 (record; iid +1.19, +2.50, −0.04, −0.04) | **changed in size** (more negative everywhere); digits_on W20 goes from 0.01 ± 0.05 (null) to −0.93 ± 0.04 |
| §6 / T9: a calibrated predictor at noise 1 sd_types keeps 38–56 % of the oracle gain; uncalibrated at 2 sd_types is harmful | digits: 37 % (1.25 / 3.34) vs 38 % (record); raw 2 sd −1.06 vs −2.27 | **unchanged** (share), **smaller** (harm) |
| T9: an overconfident τ̂ × 0.5 is harmful (−1.4 δ_n iid; −0.92 record) | +0.49 δ_n at the target (+0.17 / +0.63 at the ends; −0.31 at s = 0.55) | **changed in sign** at s ≥ 0.71 |
| "supports" 6 / T8 headroom map (iid only) | not re-run (iid only) | **unchanged** (not affected) |
| new (PLAN R1-THEORY-RHO (2)): the deployed rule is conservative under a selected incumbent | yes, in every record-like model and cell. On digits_on at W = 20, the oracle correction is worth +1.84 δ_n (oracle prior) and +3.27 δ_n (A2), against +0.69 / +1.18 under record; the feasible keep-count correction is worth +0.47 / +1.38 δ_n | **size of the limitation** at the target: 0.2–5.7 δ_n (feasible) up to 1.3–10.0 δ_n (oracle bound), depending on node, W and base (§4.8) |

## 6. Limits

- **Model only.** All T5 limits apply (Gaussian increments, additive gains, an invented memory proposer, a hand-calibrated type mixture).
- **Calibration** (§2):
  - p = 0.51 is not reachable at ϱ_local = 0.82; the upper sensitivity end is the model's maximum, p = 0.45.
  - At the target the structural ϱ cannot stay at 0.55. The control column separates that effect, but only at the target share.
  - The u + w model cannot reproduce E1's digits pattern at E1's own marginal correlations (mean model partial 0.21 at the largest feasible s).
  - The E1 input is PILOT data that the author has not accepted, and the sibling proxy is not the ancestor–descendant test PLAN R1-THEORY-RHO (5) asks for.
- **Grid edges.** Under `shared`, T5's tuning grids bind:
  - the Proposition 7 dev-tuned shift is at −0.6 σ_d;
  - the Proposition 10 θ0 is at −0.4.

  The policies were kept as T5 had them ("same policies"), so those two rows are bounds, not optima.
- **Threshold correction.** The feasible rule conditions only on the number of keeps. The Bayes rule given the full history is not computed (no closed form: the selected record error is not Gaussian, P06 §4.1). The note gives a bracket, not the value.
- **Not re-run:**
  - tabular nodes;
  - the iid-only headroom maps (T8);
  - the near-null DI mix;
  - any cell that T5 ran only under iid.

  The branch study's shared rows rest on the equivalence stated in §4.6 (u cancels in every contrast and distance); it is argued, not separately simulated with an explicit u.
- **Nothing here changes T4, T2, T5's text, the PLAN or any preregistered constant.** It is an engineering input to the manuscript (PLAN R1-THEORY-RHO (4)), not evidence.
