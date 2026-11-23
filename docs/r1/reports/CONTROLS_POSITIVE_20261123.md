# Positive control per T0 node: does the K = 10 fresh-seed audit detect E1 single edits of known effect? — 23 November 2026

**Label: SUPPORT, tier S (R1-PROCESS-TIERS). AI-assisted (Claude, subagent). Reviewed once** (`docs/r1/reviews/CONTROLS_POSITIVE_REVIEW_20261123.md`, ACCEPT WITH MINOR); its findings were fixed in one correction round, and under tier S no further review follows. This is the positive control of PLAN row R1-CONTROLS-ROW. Every per-edit effect comes from the accepted 22 Oct E1 runs only (R1-E1-PILOT-ACCEPT): `results/r1/pilot/E1_20261022T214606Z/runs.jsonl`, `edits.json` and `summary.json`. For the δ_n and σ_node comparison only, the script also reads the sha256-checked pinned T0 noise source `results/r1/noise/D28_REPAIR_20261027/summary.json` (preregistration PRE-DELTA). That is allowed because it is a pinned noise-floor summary of per-node constants that the preregistration already uses, not effect data. No per-edit effect is read from it; it sets one extra number, R-δ for `openml_sonar` at its pinned δ_n. It is not a test and changes no gate. It reads no test label, no evaluation value, no sealed partition and no sweep audit output.

**Where the row was read.** R1-CONTROLS-ROW and `docs/r1/inputs/NOVELTY_SWEEP_PART4_20261123.md` are in commit `aaaabba3` on the local branch `author-minsub-20261122`. They are not on `origin/author-minsub-20261122` (`53e2fe41`), the base of this branch. Both were read there with `git show` and are not copied onto this branch.

## 1. The audit statistic, and what "the audit detects an edit" means

This section was written before anything was computed. The correction round after the review changed one clause in it (the "S = 1" clause of R-δ, review NOTE 3); nothing else in §1 changed.

### 1.1 What the audit computes

| Quantity | Definition | Used for | Source |
|---|---|---|---|
| Audit design | Candidate and incumbent run on K = 10 common fresh joint seeds (train seed = split seed = s), seeds 7001–7010. The first 5 seeds give the training label and the last 5 the evaluation value. | every audited proposal (sweeps 1 and 2, T0) | `docs/r1/C3_DESIGN.md:67–68`; `r1/c3/audit.py:3–12`, `:92`; preregistration `docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md:20` (K = 10 on T0; labels 7001–7005, evaluation 7006–7010) |
| Paired increment | d_k = m(candidate, s_k) − m(incumbent, s_k). Δ = mean of the d_k; se = sd(d)/√k with ddof = 1. A failed seed is dropped from both arms. | all of the rows below | `r1/c3/audit.py:391–398` (`paired`) |
| Label / evaluation split | The first half of the recorded seeds is the label part and the second half the evaluation part. | | `r1/c3/audit.py:401–418` (`split_seeds`, `split_audit`) |
| **Training label** `delta_label` (δ_Y in the soft label) | Δ over seeds 7001–7005 (k = 5). `se_label` is recorded beside it. | The soft label is N(Δ_label, s²) on z = Δ/σ_node, with s = σ̂_node/√5. Since R1-SOFT-SIGMA, s uses the pooled node σ̂, not `se_label`. | `r1/c3/audit.py:1013–1017`; `docs/r1/RUNBOOK.md:352`; `r1/c3/gate_input_builder.py:283` |
| **Evaluation value** `delta_evaluation` (gate `y_eval` / `delta_true`) | Δ over seeds 7006–7010 (k = 5) | The gate's one-step utility Σ(Δ_eval · keep − g · execute), with no threshold on Δ_eval | `r1/c3/audit.py:1018–1019`; `r1/c3/gate_input_builder.py:279`; `docs/r1/C3_DESIGN.md:119`; preregistration `:13` |
| **Y** (closed loop, D.3) | y_raw = mean over K = 10 per-instance audit seeds of m(final, a_k) − m(start, a_k), with no label/evaluation split. Y = y_raw/σ_node (this normalisation is marked *proposed* in the draft). | D.3 arm contrasts: paired by instance, two-sided t, Holm, α = 0.05 | `docs/r1/PLAN.md:118`; D.3 pre-declaration draft, branch `mac-d3-predecl-20261122`, `docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md:328–338` (§7.1–7.2) and `:361–366` (§7.3); PLAN R1-D3-CHOICES (2) |
| **δ_n** | D18: max(0.002, 0.25 × median over the node's E1 edits of the joint paired sd(Δ̂)), per node, in metric units. PLAN calls it the "practical target" and "the unit of the C3 gate". | the gate's IQM-eligibility (dev denominator ≥ δ_n) | `docs/r1/PLAN.md:417`; preregistration `:18`, `:131–134` (PRE-DELTA); `r1/c3/dataset.py:84`, `:100–105` (`noise_table`) |

**The δ_n source.** The preregistration pins T0 δ_n to `results/r1/noise/D28_REPAIR_20261027/summary.json` (sha256 `3d12ce05…4310`, verified).
- For `digits_mlp`, `tabular_mlp`, `openml_ionosphere` and `openml_credit_approval`, that file takes its values from the 22 Oct summary itself (its `sources.common_summary`: sha256 `eabc2f5c…`, the sha256 of the 22 Oct `summary.json`).
- For `openml_breast_w`, `openml_sonar` and `openml_wdbc`, it takes them from the R1-D28-REPAIR re-measurement of the repaired start configurations.
- For `openml_climate`, it takes them from that node's own E1 run.

### 1.2 What "the audit detects an edit" means

**Finding: the paper defines no detection decision for a single audited edit.** Each audited quantity enters the paper as a continuous value:
- the soft label's mean (Δ_label);
- the one-step utility (Δ_eval × keep);
- Y, the mean over ten seeds.

No threshold or per-proposal test is applied to an audited increment in the label pipeline, the gate or D.3. The paper does state the following thresholds and levels:

1. **δ_n, the practical target** (`PLAN.md:417`). The problem specification defines a secondary binary outcome S = 1{Y > δ_n} (`docs/r1/inputs/PROBLEM_SPEC_DRAFT_20261009.md:162`). That is a 9 Oct input draft, not a PLAN row.
2. **The sign.**
   - The harm events are defined by the sign of the true difference: a false keep is "kept but J(c_t) ≤ J(c_inc)" (`PROBLEM_SPEC_DRAFT_20261009.md:178–179`).
   - The gate's probability of improvement counts wins (preregistration `:13`).
3. **One-sided α = 0.05.**
   - It is the gate's family-wise one-sided level (preregistration `:13`).
   - The fixed-r replication arm keeps by a one-sided t-test at α = 0.05 (`C3_DESIGN.md:98`; Welch settled in R1-D3-CHOICES (2)).
   - The D.3 arm contrasts are two-sided at α = 0.05 with Holm.
4. **D21's "resolved"**: |Δ̂| > 2 se on 30 seeds (`r1/noise/e1_report.py:104`).

**Readings used by this control.** These are an operationalisation chosen here from the constants above, not a paper rule. Let Δ̄_K and sd_K be the mean and sd (ddof = 1) of the K paired differences of a resampled audit. Let s = sign of the 30-seed estimate Δ̂, with 0 counted as +. The audit **detects** the edit if:

- **R-δ (magnitude):** s · Δ̄_K > δ_n. The audited mean exceeds the practical target in the direction of the effect. For an improvement this is Δ̄_K > δ_n, i.e. S = 1, with δ_n read in metric units on y_raw, for a campaign that keeps only this edit.
- **R-t (test):** s · Δ̄_K / (sd_K/√K) > t_{0.95, K−1}. This is a one-sided paired t-test at α = 0.05 on the K differences. If sd_K = 0, the test counts as a detection whenever s · Δ̄_K > 0.
- **R-δt:** both R-δ and R-t.
- **R-0 (sign; secondary):** s · Δ̄_K > 0, i.e. the audit gets the direction right.

**Two seed counts are evaluated:**
- **K = 10** is Y and the full ten-seed audit. For a campaign whose only kept edit is e, the final configuration is c0 + e and the start is c0, so y_raw is exactly the ten-seed mean paired difference of this pair. Comparing y_raw with δ_n in metric units is the same as comparing Y with δ_n/σ_node.
- **K = 5** is the training label Δ_label (seeds 7001–7005). Under the resampling of §2, the evaluation value on seeds 7006–7010 has the same distribution, so the K = 5 numbers describe either half.

**Which edits are informative.** The paper cares about real improvements of size at least δ_n. The informative cells are therefore edits whose 30-seed effect is clearly above δ_n. For an edit with a negative effect, R-δ and R-t ask whether the audit shows the harm; that is what stops a false keep from looking like a real improvement.

## 2. Method

**Script and outputs.**
- Script: `r1/noise/controls_positive.py`, run as `python3 -m r1.noise.controls_positive`.
- Outputs: `results/r1/engineering/controls_positive_20261123/controls_positive.json` and `tables.md`. Both are byte-identical on re-run and contain no absolute paths.
- Test: `r1/tests/test_controls_positive.py`, 15 unittest cases on synthetic data, all passing. The cases check:
  - the vectorised readings against a naive loop with `scipy.stats.ttest_1samp`;
  - exhaustive subset enumeration;
  - reproducibility of the random subsets;
  - direction symmetry;
  - degenerate (sd = 0) differences;
  - the normal and noncentral-t approximations against simulation;
  - refusal of a wrong sha256, missing seeds and `r1_sealed` paths;
  - the Monte Carlo check against exhaustive enumeration;
  - that the T0 node list equals `gate.T0_NODES` (the test imports `r1.c3.gate` directly).

**Data.**
- **Inputs.** The script reads the accepted run's `runs.jsonl`, `edits.json` and `summary.json`. It checks each against its sha256, and refuses the run otherwise: `03aa9ee1…`, `a37adfa3…`, and `eabc2f5c…` (the last is the same sha256 the pinned noise source records for it).
- **Seeds.** Only the joint condition is used: seeds 3001–3030, with train seed = split seed = s. This is the pairing the audit uses (`audit.py:3–8`).
- **Completeness.** Every node × configuration has exactly these 30 seeds, with no failed run.
- **Effect.** The per-edit effect is the mean of the 30 paired differences m(c0 + e, s) − m(c0, s), with se = sd/√30. The script checks that it reproduces `summary.json`'s `delta_hat_J` and `sd_joint` to 1e-12, i.e. Table 4 of `NOISE_FLOOR_COMMON_20261022.md`.

**Node coverage (T0 = `gate.T0_NODES`, `r1/c3/gate.py:153–154`).**

| T0 node | start configuration in the sweeps vs the 22 Oct c0 | computed here |
|---|---|---|
| `digits_mlp`, `tabular_mlp`, `openml_ionosphere`, `openml_credit_approval` | the same: R1-D28-REPAIR (`PLAN.md:595`) says "the 22 Oct values remain for the four unchanged nodes", and the pinned noise source takes these four from the 22 Oct summary | yes, **current start** |
| `openml_breast_w`, `openml_sonar`, `openml_wdbc` | changed after 22 Oct by R1-D28-REPAIR (PLAN §10, 27 Oct). The pinned noise source takes these from `E1_D28_REPAIR_20261027`, which R1-E1-PILOT-ACCEPT does not cover and which was not read for effects. | yes, but **pre-repair start**: the edits are measured from a start configuration the sweeps no longer use |
| `openml_climate` | replaced `openml_blood_transfusion` (R1-D28-REPAIR) | **no**: not in the accepted run |

`openml_wdbc` is the sensitivity row of PRE-WDBC; the primary T0 set is the other seven nodes.

**δ_n.** δ_n is computed by `r1.c3.dataset.noise_table` on the 22 Oct summary, which matches Table 1 of the 22 Oct report.
- For the four current-start nodes, it equals the pinned source's δ_n exactly.
- Among the pre-repair nodes, it also equals the pinned δ_n for `openml_breast_w` and `openml_wdbc` (0.002, the floor).
- `openml_sonar` is the exception: 0.00319 on 22 Oct against 0.00342 pinned for the repaired configuration. The JSON also gives R-δ at 0.00342 for this node.

**Class of an edit.**
- **above:** the 30-seed interval Δ̂ ± 2 se lies entirely above δ_n in absolute value.
- **below:** the interval lies entirely below δ_n.
- **near:** otherwise.

The class uses |Δ̂|. "Improvement" means Δ̂ > 0 and "harm" means Δ̂ < 0.

**What §1 fixed, and what the script fixed.** §1 fixed the statistic, the readings, the source of δ_n, K, and that the informative cells are edits clearly above δ_n. The operational ±2 se class rule above, and the start-configuration flag (current / pre-repair), were fixed in the script commit `b1d0eb61`. One trial run of the then-uncommitted script (20,000 draws; it printed one `digits_mlp` edit) came before that commit. Neither was changed after it. Reading only the current-start rows as informative follows from that flag; it was written into §3–§4 after the computation.

**Detection probability.** K of the 30 joint seeds are drawn without replacement, and each reading of §1.2 is applied to the subset's paired differences.
- **K = 5:** all C(30, 5) = 142,506 subsets are enumerated. The probability is exact for this resampling scheme; it has no Monte Carlo error.
- **K = 10:** C(30, 10) ≈ 3.0 × 10⁷ is too many to enumerate, so 200,000 uniform random subsets are drawn instead (numpy PCG64, `default_rng(20261123 + 10)`). The same subsets serve every node and edit, as one audit seed set serves every proposal. The Monte Carlo standard error is √(p(1 − p)/200,000), at most 0.0011 over all cells (per cell in the JSON). A cell with p = 0 or 1 has a 95 % bound of 3/200,000.
- **Check (committed; JSON `checks`, `tables.md` header).** The script re-estimates every exhaustive K = 5 cell from 200,000 random subsets (`default_rng(20261123 + 1000 + 5)`).
  - Over 35 edits × 4 readings, the largest absolute difference is 0.0030 (R-t and R-δt).
  - In Monte Carlo standard errors, the largest difference per reading is 1.91 (R-0), 2.54 (R-δ) and 3.40 (R-t, R-δt).
  - With 140 independent comparisons, a maximum this large would occur with probability about 0.09. The comparisons here share one subset draw, so they are not independent.
  - This replaces the ad-hoc check of the first version, which was not saved.
- **Critical values:** t_{0.95, 9} = 1.8331 and t_{0.95, 4} = 2.1318.

**Analytic check** (`tables.md` Table B), at the plug-in effect Δ̂ in its own direction:
- R-δ normal "super" = Φ((|Δ̂| − δ_n)/(sd/√K)). It uses the variance of the mean of a truly fresh K-seed audit.
- R-δ normal "fpc" = the same with sd/√K × √((30 − K)/30). It uses the variance of the resampling scheme, and so checks the resampled number.
- R-t "super" = the power of the one-sided t-test under a noncentral t with noncentrality |Δ̂|/(sd/√K).
- R-δ "super" at |Δ̂| − 2 se and |Δ̂| + 2 se. This shows how much the answer depends on the effect estimate.

**Resampling understates seed-to-seed variance.** Drawing K of 30 seeds without replacement gives the subset mean a variance of (1 − K/30) × sd²/K. That is 2/3 of a fresh audit's variance at K = 10 and 5/6 at K = 5.
- For edits above δ_n, the resampled R-δ and R-0 probabilities are therefore somewhat optimistic, and below δ_n somewhat pessimistic.
- **This does not hold for R-t in general.** The t statistic's sd also comes from the subset, and non-normal differences move the resampled value in either direction. In the weakest informative cell, the resampled R-t is below the noncentral-t value: 0.416 against 0.458 at K = 10, and 0.198 against 0.255 at K = 5.
- For R-δ, the "super" column is the better guide to a real fresh-seed audit.
- Both are reported. For R-δ in the informative cells, they differ by at most 0.042 at K = 10 for the current-start improvements (for example, `openml_credit_approval` gradient boosting: 0.941 resampled against 0.899 super).

## 3. Results

### 3.1 Per node and edit

Δ̂ is the 30-seed mean paired difference (candidate − c0) ± its se. The detection columns give the probability that a K-seed audit detects the edit in the direction of Δ̂, under the readings of §1.2. Rows are ordered with the current-start nodes first, then the pre-repair nodes. The full analytic check is in `tables.md` Table B.

| Node | start config | Edit | Δ̂ (30 seeds) ± se | δ_n | class | K=10 R-δ | K=10 R-t | K=10 R-δt | K=10 R-0 | K=5 R-δ | K=5 R-t | K=5 R-δt | K=5 R-0 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `digits_mlp` | current | LEARNING_RATE_INIT 1e-3 -> 0.002 | +0.0080 ± 0.0012 | 0.0020 | above | 1.000 | 1.000 | 1.000 | 1.000 | 0.993 | 0.752 | 0.751 | 1.000 |
| `digits_mlp` | current | MAX_ITER 40 -> 80 | +0.0085 ± 0.0011 | 0.0020 | above | 1.000 | 1.000 | 1.000 | 1.000 | 0.999 | 0.923 | 0.923 | 1.000 |
| `digits_mlp` | current | HIDDEN_UNITS 32 -> 16 | -0.0159 ± 0.0020 | 0.0020 | above | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.866 | 0.866 | 1.000 |
| `digits_mlp` | current | HIDDEN_UNITS 32 -> 64 | +0.0089 ± 0.0015 | 0.0020 | above | 1.000 | 0.960 | 0.960 | 1.000 | 0.979 | 0.636 | 0.636 | 0.996 |
| `digits_mlp` | current | BATCH_SIZE 64 -> 32 | +0.0068 ± 0.0010 | 0.0020 | above | 1.000 | 1.000 | 1.000 | 1.000 | 0.990 | 0.761 | 0.760 | 1.000 |
| `openml_credit_approval` | current | C 0.15 -> 0.075 | -0.0020 ± 0.0005 | 0.0020 | near | 0.483 | 0.688 | 0.478 | 0.998 | 0.495 | 0.359 | 0.313 | 0.959 |
| `openml_credit_approval` | current | C 0.15 -> 0.3 | +0.0006 ± 0.0005 | 0.0020 | below | 0.029 | 0.091 | 0.029 | 0.761 | 0.124 | 0.070 | 0.061 | 0.671 |
| `openml_credit_approval` | current | model_type logistic_regression -> random_forest | +0.0130 ± 0.0024 | 0.0020 | above | 1.000 | 0.973 | 0.973 | 1.000 | 0.987 | 0.556 | 0.556 | 0.997 |
| `openml_credit_approval` | current | model_type logistic_regression -> gradient_boosting | +0.0085 ± 0.0030 | 0.0020 | above | 0.941 | 0.416 | 0.416 | 0.980 | 0.834 | 0.198 | 0.198 | 0.898 |
| `openml_credit_approval` | current | class_weight balanced -> null | +0.0002 ± 0.0002 | 0.0020 | below | 0.000 | 0.088 | 0.000 | 0.788 | 0.000 | 0.053 | 0.000 | 0.686 |
| `openml_ionosphere` | current | C 0.15 -> 0.075 | -0.0040 ± 0.0026 | 0.0040 | near | 0.501 | 0.169 | 0.166 | 0.867 | 0.493 | 0.106 | 0.105 | 0.756 |
| `openml_ionosphere` | current | C 0.15 -> 0.3 | -0.0023 ± 0.0029 | 0.0040 | near | 0.352 | 0.085 | 0.084 | 0.704 | 0.413 | 0.068 | 0.066 | 0.638 |
| `openml_ionosphere` | current | model_type logistic_regression -> random_forest | +0.0500 ± 0.0073 | 0.0040 | above | 1.000 | 0.999 | 0.999 | 1.000 | 0.999 | 0.743 | 0.743 | 1.000 |
| `openml_ionosphere` | current | model_type logistic_regression -> gradient_boosting | +0.0255 ± 0.0082 | 0.0040 | above | 0.968 | 0.504 | 0.504 | 0.987 | 0.876 | 0.258 | 0.258 | 0.914 |
| `openml_ionosphere` | current | class_weight balanced -> null | +0.0001 ± 0.0010 | 0.0040 | below | 0.003 | 0.026 | 0.003 | 0.519 | 0.051 | 0.031 | 0.024 | 0.502 |
| `tabular_mlp` | current | MAX_ITER 40 -> 20 | -0.0087 ± 0.0007 | 0.0020 | above | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| `tabular_mlp` | current | ALPHA 1e-4 -> 5e-05 | +0.0000 ± 0.0000 | 0.0020 | below | 0.000 | 0.054 | 0.000 | 0.528 | 0.000 | 0.089 | 0.000 | 0.510 |
| `tabular_mlp` | current | BATCH_SIZE 64 -> 32 | +0.0025 ± 0.0004 | 0.0020 | near | 0.838 | 1.000 | 0.838 | 1.000 | 0.720 | 0.884 | 0.668 | 1.000 |
| `tabular_mlp` | current | ALPHA 1e-4 -> 0.0002 | -0.0000 ± 0.0000 | 0.0020 | below | 0.000 | 0.011 | 0.000 | 0.493 | 0.000 | 0.014 | 0.000 | 0.457 |
| `tabular_mlp` | current | HIDDEN_UNITS 32 -> 16 | -0.0038 ± 0.0011 | 0.0020 | near | 0.866 | 0.543 | 0.543 | 0.992 | 0.758 | 0.307 | 0.306 | 0.931 |
| `openml_breast_w` | pre_repair | C 0.15 -> 0.075 | -0.0002 ± 0.0001 | 0.0020 | below | 0.000 | 0.102 | 0.000 | 0.885 | 0.000 | 0.062 | 0.000 | 0.753 |
| `openml_breast_w` | pre_repair | C 0.15 -> 0.3 | -0.0001 ± 0.0001 | 0.0020 | below | 0.000 | 0.017 | 0.000 | 0.644 | 0.000 | 0.025 | 0.000 | 0.556 |
| `openml_breast_w` | pre_repair | model_type logistic_regression -> random_forest | -0.0035 ± 0.0009 | 0.0020 | near | 0.889 | 0.894 | 0.791 | 1.000 | 0.766 | 0.429 | 0.395 | 0.999 |
| `openml_breast_w` | pre_repair | model_type logistic_regression -> gradient_boosting | -0.0057 ± 0.0013 | 0.0020 | above | 0.992 | 0.959 | 0.953 | 1.000 | 0.929 | 0.452 | 0.444 | 0.999 |
| `openml_breast_w` | pre_repair | class_weight balanced -> null | +0.0000 ± 0.0000 | 0.0020 | below | 0.000 | 0.100 | 0.000 | 0.751 | 0.000 | 0.019 | 0.000 | 0.555 |
| `openml_sonar` | pre_repair | C 0.15 -> 0.075 | +0.0062 ± 0.0021 | 0.0032 | near | 0.844 | 0.449 | 0.449 | 0.989 | 0.746 | 0.202 | 0.202 | 0.915 |
| `openml_sonar` | pre_repair | C 0.15 -> 0.3 | -0.0087 ± 0.0023 | 0.0032 | above | 0.954 | 0.648 | 0.648 | 0.997 | 0.863 | 0.303 | 0.303 | 0.955 |
| `openml_sonar` | pre_repair | model_type logistic_regression -> random_forest | +0.0569 ± 0.0082 | 0.0032 | above | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.797 | 0.797 | 1.000 |
| `openml_sonar` | pre_repair | model_type logistic_regression -> gradient_boosting | -0.1041 ± 0.0176 | 0.0032 | above | 1.000 | 0.994 | 0.994 | 1.000 | 0.998 | 0.630 | 0.630 | 0.999 |
| `openml_sonar` | pre_repair | class_weight balanced -> null | +0.0008 ± 0.0007 | 0.0032 | below | 0.009 | 0.109 | 0.009 | 0.771 | 0.093 | 0.086 | 0.069 | 0.648 |
| `openml_wdbc` | pre_repair | C 0.15 -> 0.075 | -0.0003 ± 0.0001 | 0.0020 | below | 0.000 | 0.379 | 0.000 | 0.917 | 0.000 | 0.167 | 0.000 | 0.791 |
| `openml_wdbc` | pre_repair | C 0.15 -> 0.3 | +0.0003 ± 0.0001 | 0.0020 | below | 0.000 | 0.503 | 0.000 | 0.973 | 0.000 | 0.188 | 0.000 | 0.862 |
| `openml_wdbc` | pre_repair | model_type logistic_regression -> random_forest | -0.0061 ± 0.0017 | 0.0020 | above | 0.965 | 0.731 | 0.728 | 1.000 | 0.879 | 0.358 | 0.347 | 0.975 |
| `openml_wdbc` | pre_repair | model_type logistic_regression -> gradient_boosting | -0.0316 ± 0.0044 | 0.0020 | above | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.889 | 0.889 | 1.000 |
| `openml_wdbc` | pre_repair | class_weight balanced -> null | +0.0000 ± 0.0001 | 0.0020 | below | 0.000 | 0.003 | 0.000 | 0.504 | 0.000 | 0.002 | 0.000 | 0.427 |

### 3.2 Summary by class (min / median / max over edits)

Current-start and pre-repair rows are kept apart.

| Class | edits | K=10 R-δ | K=10 R-t | K=10 R-δt | K=5 R-δ | K=5 R-t | K=5 R-δt |
|---|---|---|---|---|---|---|---|
| improvement, clearly above δ_n, current start | 8 | 0.941 / 1.000 / 1.000 | 0.416 / 0.986 / 1.000 | 0.416 / 0.986 / 1.000 | 0.834 / 0.989 / 0.999 | 0.198 / 0.690 / 0.923 | 0.198 / 0.690 / 0.923 |
| harm, clearly above δ_n, current start | 2 | 1.000 / 1.000 / 1.000 | 1.000 / 1.000 / 1.000 | 1.000 / 1.000 / 1.000 | 1.000 / 1.000 / 1.000 | 0.866 / 0.933 / 1.000 | 0.866 / 0.933 / 1.000 |
| near δ_n, current start | 5 | 0.352 / 0.501 / 0.866 | 0.085 / 0.543 / 1.000 | 0.084 / 0.478 / 0.838 | 0.413 / 0.495 / 0.758 | 0.068 / 0.307 / 0.884 | 0.066 / 0.306 / 0.668 |
| clearly below δ_n, current start | 5 | 0.000 / 0.000 / 0.029 | 0.011 / 0.054 / 0.091 | 0.000 / 0.000 / 0.029 | 0.000 / 0.000 / 0.124 | 0.014 / 0.053 / 0.089 | 0.000 / 0.000 / 0.061 |
| improvement, clearly above δ_n, pre-repair start | 1 | 1.000 / 1.000 / 1.000 | 1.000 / 1.000 / 1.000 | 1.000 / 1.000 / 1.000 | 1.000 / 1.000 / 1.000 | 0.797 / 0.797 / 0.797 | 0.797 / 0.797 / 0.797 |
| harm, clearly above δ_n, pre-repair start | 5 | 0.954 / 0.992 / 1.000 | 0.648 / 0.959 / 1.000 | 0.648 / 0.953 / 1.000 | 0.863 / 0.929 / 1.000 | 0.303 / 0.452 / 0.889 | 0.303 / 0.444 / 0.889 |
| near δ_n, pre-repair start | 2 | 0.844 / 0.867 / 0.889 | 0.449 / 0.672 / 0.894 | 0.449 / 0.620 / 0.791 | 0.746 / 0.756 / 0.766 | 0.202 / 0.316 / 0.429 | 0.202 / 0.299 / 0.395 |
| clearly below δ_n, pre-repair start | 7 | 0.000 / 0.000 / 0.009 | 0.003 / 0.102 / 0.503 | 0.000 / 0.000 / 0.009 | 0.000 / 0.000 / 0.093 | 0.002 / 0.062 / 0.188 | 0.000 / 0.000 / 0.069 |

### 3.3 Analytic check for the informative cells

The informative cells are the eight improvements clearly above δ_n at the current start. Minimum over the eight, all at `openml_credit_approval`, model_type → gradient_boosting (Δ̂ = +0.0085 ± 0.0030, paired sd 0.0162):

| | K = 10 | K = 5 |
|---|---|---|
| R-δ resampled | 0.941 | 0.834 |
| R-δ normal, fresh-seed ("super") | 0.899 | 0.817 |
| R-δ normal "super" at Δ̂ − 2 se | 0.548 | 0.534 |
| R-t resampled | 0.416 | 0.198 |
| R-t noncentral t "super" | 0.458 | 0.255 |
| R-0 resampled (sign) | 0.980 | 0.898 |

The next weakest edit is `openml_ionosphere`, model_type → gradient_boosting (Δ̂ = +0.0255 ± 0.0082, paired sd 0.0449): R-δ 0.968 resampled and 0.935 super at K = 10, and R-t 0.504. Every other current-start improvement has R-δ "super" ≥ 0.996 at K = 10 and ≥ 0.969 at K = 5.

**Where the normal approximation is poor.** For edits whose paired differences are few and discrete, the resampled R-t and the noncentral-t value disagree. Examples: `openml_breast_w` C × 0.5 (0.102 against 0.234 at K = 10); `openml_breast_w` random forest (0.894 against 0.631); `openml_wdbc` random forest (0.731 against 0.620). These are all pre-repair nodes. The resampled value uses the observed distribution, and the normal value assumes Gaussian differences.

## 4. Reading

1. **Under the magnitude reading R-δ, the audit reliably detects large improvements (3.4–12.5 δ_n). Detection of effects near δ_n is moderate.**
   - Scope: the four nodes whose start configuration is the one the sweeps use. The eight improvements clearly above δ_n have 30-seed effects of 3.39–12.53 δ_n (JSON `effect_over_delta_n`).
   - K = 10 (Y): detection ≥ 0.941 (median 1.000) by resampling. The fresh-seed normal approximation gives ≥ 0.899.
   - K = 5 (training label; also the evaluation value): detection ≥ 0.834 by resampling and ≥ 0.817 normal.
   - The direction alone (R-0) is right with probability ≥ 0.980 at K = 10 and ≥ 0.898 at K = 5.
   - The two harms clearly above δ_n on these nodes (4.36 and 7.94 δ_n) are detected under R-δ with probability 1.000 at both K.
   - The weak cells are the model-type switches to gradient boosting on `openml_credit_approval` and `openml_ionosphere`. Their effects are 4.27 and 6.39 δ_n, but their paired sd is about 8 and 11 times δ_n respectively.
   - **Effects near δ_n.** At the current start, the near class holds five edits with |Δ̂| = 0.58–1.91 δ_n: one improvement and four harms. Detection is computed in each edit's own direction, so the harms also measure sensitivity at that size.
     - R-δ is 0.352–0.866 at K = 10 and 0.413–0.758 at K = 5.
     - The only near improvement, `tabular_mlp` BATCH_SIZE 64 → 32 (1.25 δ_n), has 0.838 and 0.720.
     - No current-start edit lies between 1.91 and 3.39 δ_n, so detection in that range is not measured here.
2. **Under the test reading R-t, the same audit is often underpowered.**
   - A one-sided t-test at α = 0.05 on the K differences detects these eight improvements with probability 0.416–1.000 at K = 10 (median 0.986) and 0.198–0.923 at K = 5 (median 0.690). R-δt differs from R-t by at most 0.001 in these cells.
   - The paper applies no such test to an audited proposal: its audited quantities enter as continuous values (§1.2). This reading therefore describes a hypothetical per-proposal significance check, not the gate or D.3.
   - R-t also tests a different hypothesis (a nonzero effect, not one of practical size). On near-deterministic differences it flags tiny but real effects below δ_n: for example, `openml_wdbc` C × 2 (+0.0003) has R-t 0.503 at K = 10 while R-δ is 0.000.
3. **Below δ_n, detection is low, as designed.**
   - At the current start (5 edits), R-δ is ≤ 0.029 at K = 10 and ≤ 0.124 at K = 5.
   - At the pre-repair start (7 edits), R-δ is ≤ 0.009 at K = 10 and ≤ 0.093 at K = 5.
   - **Near δ_n, detection is intermediate.** At the current start (5 edits) it is 0.352–0.866 at K = 10 and 0.413–0.758 at K = 5 (item 1). At the pre-repair start (2 edits) it is 0.844–0.889 and 0.746–0.766.
4. **The pre-repair nodes show the same pattern.** On `openml_breast_w`, `openml_sonar` and `openml_wdbc`, the edits clearly above δ_n have R-δ ≥ 0.954 at K = 10. These are 5 harms and 1 improvement. At `openml_sonar`'s pinned δ_n (0.00342, from the repaired configuration), its C × 2 cell falls to 0.940 at K = 10 and 0.823 at K = 5, so the bound becomes ≥ 0.940. Because the start configuration has since changed, these rows describe the audit's sensitivity on those datasets' noise, not on the nodes as the sweeps run them.
5. **What this means for a negative gate result.**
   - The gate reads the five-seed evaluation value as a continuous utility.
   - On the four current-start nodes, a five-seed audit puts each of the eight large improvements (3.4–12.5 δ_n) beyond δ_n in its direction with probability at least 0.817 (fresh-seed normal approximation; 0.834 resampled). It gives the sign with probability at least 0.898 (resampled; 0.881 normal). At Δ̂ − 2 se, the weakest of these cells falls to 0.534 at K = 5 (0.548 at K = 10).
   - For effects near δ_n (0.58–1.91 δ_n at the current start), a five-seed audit detects them with probability 0.413–0.758. This is the gate-relevant figure for proposals of that size.
   - A negative gate read on T0 is therefore **not explained by a per-edit audit that cannot see large improvements**, for edits like these on these nodes. For effects near δ_n, improvements included, the audit is only moderately sensitive.
   - It can still arise from causes this control does not measure:
     - the gate's own power (D8-PASS mean two-arm power 0.36 at effect size 0.3, as R1-SUBMISSION-MIN quotes it). This is a property of the measurement design: finite test instances, and five-seed evaluation noise summed over proposals;
     - proposals whose effects lie near δ_n, where a five-seed audit detects 0.413–0.758 at the current start;
     - arms whose decisions differ mainly on such proposals, which is the regime of T4 Proposition 7's dispersion bound.
   - Within the limits below, the positive control rules out one explanation of a negative gate result: a per-edit audit that cannot see large improvements. The gate's own power, and the audit's moderate sensitivity near δ_n, remain separate explanations.

**Limits.**
- **The readings are an operationalisation.** The paper defines no per-edit detection decision (§1.2).
- **Resampling from 30 seeds understates seed-to-seed variance** (§2). For R-δ, the fresh-seed normal values are lower in the informative cells by up to 0.042 at K = 10. For R-t the resampled value can also be lower than the noncentral-t value.
- **The true effect is a plug-in estimate.** At Δ̂ − 2 se, the weakest informative cell falls to 0.548 at K = 10 and 0.534 at K = 5.
- **The seeds and edits are not the audit's own.**
  - The sweep audits use seeds 7001–7010, and D.3's audit of Y uses per-instance seeds 6701–6880 (D.3 pre-declaration draft §7.2). This control uses 3001–3030. Exchangeability of seed blocks is assumed.
  - The E1 edits are one step from the default configuration (R1-E1-PILOT-ACCEPT's stated limit). Sweep proposals are other edits at other incumbents, and their effect sizes are not known here.
- **Node coverage is incomplete.** Three T0 nodes are measured only at their pre-repair start. `openml_climate` is not determined.
- **Host, environment and harness were not checked.**
  - The 22 Oct runs used the harness at `4012897`, on an aarch64 Linux VM with scikit-learn 1.8.0 and NumPy 2.4.4.
  - The D.3 pre-declaration draft records the same scikit-learn and NumPy versions for the sweep-2 audit environment, on a different host.
  - Tree-model metrics are library-version sensitive (22 Oct report, Table 7). Cross-host equality of the metrics was not checked here.
  - That the four current-start nodes' code is the same in the sweep harness pins is taken from R1-D28-REPAIR (`PLAN.md:595`) and from the pinned noise source's use of the 22 Oct values. Code identity was not checked here.
