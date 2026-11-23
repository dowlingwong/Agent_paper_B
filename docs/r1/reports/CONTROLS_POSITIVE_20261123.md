# Positive control per T0 node: does the K = 10 fresh-seed audit detect E1 single edits of known effect? — 23 November 2026

**Label: SUPPORT, tier S (R1-PROCESS-TIERS). AI-assisted (Claude, subagent). Not reviewed.** This is the positive control of PLAN row R1-CONTROLS-ROW. It reads only the accepted 22 Oct E1 runs (R1-E1-PILOT-ACCEPT): `results/r1/pilot/E1_20261022T214606Z/runs.jsonl`, `edits.json` and `summary.json`. It is not a test and changes no gate. It reads no test label, no evaluation value, no sealed partition and no sweep audit output.

**Where the row was read.** R1-CONTROLS-ROW and `docs/r1/inputs/NOVELTY_SWEEP_PART4_20261123.md` are in commit `aaaabba3` on the local branch `author-minsub-20261122`. They are not on `origin/author-minsub-20261122` (`53e2fe41`), the base of this branch. Both were read there with `git show` and are not copied onto this branch.

## 1. The audit statistic, and what "the audit detects an edit" means

This section was written before anything was computed.

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

- **R-δ (magnitude):** s · Δ̄_K > δ_n. The audited mean exceeds the practical target in the direction of the effect. For an improvement this is Δ̄_K > δ_n, i.e. S = 1 for a campaign that keeps only this edit.
- **R-t (test):** s · Δ̄_K / (sd_K/√K) > t_{0.95, K−1}. This is a one-sided paired t-test at α = 0.05 on the K differences. If sd_K = 0, the test counts as a detection whenever s · Δ̄_K > 0.
- **R-δt:** both R-δ and R-t.
- **R-0 (sign; secondary):** s · Δ̄_K > 0, i.e. the audit gets the direction right.

**Two seed counts are evaluated:**
- **K = 10** is Y and the full ten-seed audit. For a campaign whose only kept edit is e, the final configuration is c0 + e and the start is c0, so y_raw is exactly the ten-seed mean paired difference of this pair. Comparing y_raw with δ_n in metric units is the same as comparing Y with δ_n/σ_node.
- **K = 5** is the training label Δ_label (seeds 7001–7005). Under the resampling of §2, the evaluation value on seeds 7006–7010 has the same distribution, so the K = 5 numbers describe either half.

**Which edits are informative.** The paper cares about real improvements of size at least δ_n. The informative cells are therefore edits whose 30-seed effect is clearly above δ_n. For an edit with a negative effect, R-δ and R-t ask whether the audit shows the harm; that is what stops a false keep from looking like a real improvement.

## 2. Method

*(Filled in after the computation.)*

## 3. Results

*(Filled in after the computation.)*

## 4. Reading

*(Filled in after the computation.)*
