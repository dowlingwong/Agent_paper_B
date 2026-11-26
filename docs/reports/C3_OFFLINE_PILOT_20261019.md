# C3 offline pipeline — engineering pilot, 19 Oct 2026

**ENGINEERING_ONLY. AI-assisted (Claude), overnight agent on branch `overnight/c3-offline`.** Tiny, partly selected sample; engineering check of the pipeline and of the audit cost. **This is not the C3 gate decision** and nothing below is evidence (PLAN §10 C3 gate; RUNBOOK §1 rule 3). The author has not reviewed it.

Run directory: `results/r1/engineering/c3_audit_pilot_20261019T001338Z/` (manifest, proposal table, configs, plan, per-run cache, audits, two offline-evaluation JSONs, DI-candidate audits). Code: `r1/c3/` (see `docs/r1/overnight/C3_OFFLINE_HANDOFF.md`).

## 1. What was run

1. **Proposal table** (`python -m r1.c3.dataset build`) from root ledgers only: DT4 (`E1b_20261013T151857Z`, memory `none`), the PARTIAL memory-on rerun-2 arm A snapshot, and the 14 Oct liveness run (memory on, W = 10). 1,400 ledger rows → **1,323 proposals** (trial 1 has no incumbent comparison and 3 invalid rows have no metric). Every ledger was replayed from its start configuration with the logged structured edits (harness `_apply_edit` regexes). Replay checks: **0** candidates with incumbent-equal active configuration and Δ̂ ≠ 0, **0** re-evaluated active configurations whose metric differs from the first evaluation, 0 stale edits. The 19 DI-changed candidates were located and their replayed incumbents equal the E2 snapshot incumbents.
2. **Audit plan** (`dataset plan --di`, seed 20261019): random non-inert samples of 70 `tabular_mlp` and 54 `openml_breast_w` proposals from the memory-on snapshot (of 168 and 131 non-inert), all 26 non-inert `digits_mlp` DT4 proposals, plus the 19 DI-changed candidates (3 already in the random sample) → **166 proposals**.
3. **Audits** (`python -m r1.c3.audit run`, twice, time-boxed): candidate and incumbent on K = 6 common fresh joint seeds 7001–7006 via the harness `LocalWorker.run_trial_at_seed` (the E1 / E1b-leaf mechanism), 4 CPU workers on the Mac VM. 112 distinct configurations, **672 worker runs, 0 failures**, edits never re-applied (`changed_files` false on every run).
4. **Arms and evaluation** (`python -m r1.c3.offline_eval`): A0 (ρ), A1 (constant prior per node), A2 (A1 + D25/D27 rules), A3 (LightGBM, 12 soft-label bins, same rule override). 3-fold cross-fitting by instance seed and leave-one-node-out; g ∈ {0, 0.02, 0.05, 0.1, 0.2, 0.3} × σ_node; instance-cluster bootstrap (2,000 draws).

## 2. Cost per audited proposal

| Quantity | Value |
|---|---:|
| Mean wall time of one worker run | 1.16 s (process start + copy dominate; tabular, digits and breast-w alike) |
| Run-seconds per audited proposal, amortised (incumbents shared) | 4.7 s |
| Run-seconds per proposal without incumbent sharing (12 runs) | 13.9 s |
| Elapsed wall time, 166 proposals, 4 workers | 216 s (1.3 s per proposal) |

Extrapolation: ≈ 1,000 non-inert proposals of a rerun-2-sized sweep cost ≈ 1.3–3.9 CPU-hours on these cores (C3_DESIGN §4 estimated ≈ 6 CPU-hours). The 8–10k target is ≈ 10–40 CPU-hours: feasible on Ada/Deepthought cores, too slow on the Mac.

## 3. DI-changed candidates (fresh, selection-free audits)

Candidate = root trial at the E2 point; incumbent = the E2 snapshot incumbent. D̄ is the frozen verify response (r = 2, historical **fixed** split) that defined the change; the audit uses fresh joint seeds (train and split varied).

| Source | Instance | b | Direction | Edit | Rule-inert | Logged Δ̂ | Verify D̄ | Fresh audit Δ ± se |
|---|---|---:|---|---|---|---:|---:|---:|
| dt4 | digits_mlp__s104 | 8 | promotion | HIDDEN_UNITS 64→128 | duplicate | −0.008357 | 0.002786 | 0.009285 ± 0.001991 |
| dt4 | digits_mlp__s104 | 12 | promotion | HIDDEN_UNITS 64→128 | duplicate | −0.008357 | 0.002786 | 0.009285 ± 0.001991 |
| dt4 | digits_mlp__s114 | 8 | promotion | BATCH_SIZE 128→256 | duplicate | 0.000000 | 0.002786 | −0.004642 ± 0.001175 |
| dt4 | digits_mlp__s134 | 8 | promotion | HIDDEN_UNITS 128→256 | no | −0.002786 | 0.002786 | 0.002321 ± 0.000856 |
| dt4 | digits_mlp__s144 | 4 | promotion | BATCH_SIZE 64→128 | no | −0.005571 | 0.001393 | 0.000464 ± 0.000464 |
| dt4 | digits_mlp__s144 | 8 | promotion | BATCH_SIZE 64→128 | duplicate | −0.005571 | 0.001393 | 0.000464 ± 0.000464 |
| rerun2A | tabular_mlp__s102 | 12 | promotion | HIDDEN_UNITS 64→128 | duplicate | −0.003375 | 0.001187 | 0.001800 ± 0.001421 |
| rerun2A | tabular_mlp__s112 | 8 | promotion | BATCH_SIZE 64→128 | duplicate | −0.000400 | 0.000562 | −0.002429 ± 0.000758 |
| rerun2A | tabular_mlp__s112 | 12 | promotion | BATCH_SIZE 64→128 | duplicate | −0.000400 | 0.000400 | −0.002429 ± 0.000758 |
| rerun2A | tabular_mlp__s122 | 12 | demotion | ALPHA 1e-5→1e-6 | no | 0.000025 | −0.000125 | 0.000008 ± 0.000018 |
| rerun2A | tabular_mlp__s132 | 8 | promotion | ALPHA 1e-4→1e-3 | duplicate | −0.000100 | 0.000000 | 0.000017 ± 0.000044 |
| rerun2A | tabular_mlp__s152 | 8 | promotion | BATCH_SIZE 128→256 | no | −0.000325 | 0.001512 | −0.003121 ± 0.000919 |
| rerun2A | tabular_mlp__s152 | 12 | promotion | ALPHA 1e-4→1e-3 | no | −0.000050 | 0.000025 | 0.000000 ± 0.000032 |
| rerun2A | tabular_mlp__s182 | 4 | demotion | MAX_ITER 40→60 | no | 0.001500 | −0.000562 | 0.001483 ± 0.000904 |
| rerun2A | tabular_mlp__s182 | 8 | promotion | ALPHA 1e-4→1e-3 | duplicate | −0.000100 | 0.000125 | 0.000121 ± 0.000055 |
| rerun2A | tabular_mlp__s202 | 4 | demotion | HIDDEN_UNITS 128→256 | no | 0.001900 | −0.003400 | 0.000483 ± 0.000857 |
| rerun2A | tabular_mlp__s232 | 4 | demotion | MAX_ITER 40→100 | no | 0.001900 | −0.002713 | −0.002367 ± 0.001082 |
| rerun2A | tabular_mlp__s252 | 8 | promotion | ALPHA 1e-4→1e-3 | no | −0.000050 | 0.000013 | 0.000000 ± 0.000040 |
| rerun2A | tabular_mlp__s252 | 12 | promotion | ALPHA 1e-4→1e-3 | duplicate | −0.000050 | 0.000138 | 0.000000 ± 0.000040 |

**Immediate-value proxy vs fresh audit** (point means, repetitions already averaged in the DI report; immediate = +Δ for a promotion, −Δ for a demotion):

| Dataset | Points | Mean immediate proxy (±D̄) | Mean immediate from fresh audit [point-bootstrap 95 %] | DI-report residual | Residual with the audit substituted |
|---|---:|---:|---:|---:|---:|
| memory on / tabular | 13 | 0.000828 | −0.000435 [−0.00128, 0.00036] | −0.00122 [−0.00222, −0.00026] | **+0.000041** |
| memory off / digits | 6 | 0.00232 | 0.00286 [−0.00093, 0.00665] | 0.00051 [−0.00259, 0.00418] | −0.000031 |

The proxy mean reproduces the DI report's value exactly (0.000827885), so the points are identified correctly. On memory-on tabular the verify direction agrees in sign with the fresh audit at only 7/13 points, and the selected D̄ overstates the immediate value by ≈ 0.0013. **Replacing the selection-biased D̄ with the fresh audit removes the negative value residual (−0.00122 → +0.00004).** This is a point estimate: the audited immediate value has no interval that includes the budget-correction uncertainty, two pairs of points share the same (candidate, incumbent) pair, and 10 of the 19 candidates are rule-detectable duplicates. Read it as: the "violated in value terms" classification of the memory-on DI report is not supported once the proxy is de-biased. It is not evidence that DI holds. The coordinating session should re-run `di_test` with the audited immediate value (`di_candidate_audits.json`) inside the bootstrap.

## 4. Offline evaluation (engineering numbers)

Population: the three audited strata (memory-on `tabular_mlp` 174 inert + 76 audited non-inert, of which 70 random; memory-on `openml_breast_w` 209 + 54; DT4 `digits_mlp` 88 + 26). Randomly audited non-inert rows are weighted by the inverse sampling fraction; DI-only audits are used for training, not evaluation.

**Label/value seed split (default).** Identical (candidate, incumbent) pairs recur across instances (same start configuration): 15/26 digits, 21/76 tabular and 24/54 breast-w audited rows share their pair with another instance. With the same audit seeds, a held-out row then shares its audit error with a training label. The default therefore builds training labels from seeds 7001–7003 and the evaluation value from 7004–7006. Using all six seeds for both (`--no-seed-split`) inflates the A3 − A2 gain (tabular, g = 0.1σ: +0.0040 vs +0.0021) and makes the pilot "gate" pass at g = 0.05σ and 0.1σ. **That pass is an artefact of shared audit noise**, and the seed split is the configuration to use.

C3 gate quantity with the seed split, cross-fitting by instance (gain of A3 over A2 scaled to 20 proposals; δ_n = 0.002 on all three nodes):

| g / σ_node | digits_mlp (6 inst.) | tabular_mlp (18) | openml_breast_w (18) | ≥ 2 nodes pass? |
|---:|---|---|---|---|
| 0 | +0.0047 [0.0018, 0.0077] | +0.0003 [0.0001, 0.0007] | +0.0001 [−0.0001, 0.0003] | no |
| 0.05 | +0.0051 [0.0019, 0.0083] | +0.0013 [−0.0000, 0.0023] | −0.0010 [−0.0015, −0.0005] | no |
| 0.1 | +0.0059 [0.0024, 0.0094] | +0.0021 [−0.0002, 0.0040] | −0.0002 [−0.0004, −0.0000] | no |
| 0.2 | +0.0075 [0.0042, 0.0105] | −0.0003 [−0.0016, 0.0013] | 0.0000 | no |

Leave-one-node-out: A3 transfers to `tabular_mlp` at small g (+0.0021 [0.0006, 0.0038] at g = 0.02σ) and loses on `digits_mlp` at g ≤ 0.05σ. One of the 12 (g, mode) cells (LONO, g = 0.2σ: digits and breast-w) meets the two-node criterion. With 6 g values × 2 modes searched, that is what noise produces. No g was pre-declared, and **no gate outcome is claimed**.

Other read-outs (seed split, instance cross-fitting):
- **Log score** (lower is better; all evaluated rows): A1 1.16 / 1.58 / 0.84, A2 0.60 / 0.88 / 0.16, A3 0.42 / 0.76 / 0.14 for digits / tabular / breast-w. Most of the improvement over A1 is the rule layer (inert proposals are 77 %, 51 % and 61 % of these strata's proposal populations).
- **Calibration of P(Δ > 0)** (A3, predicted vs soft-label observed): tabular 0.25 vs 0.23 (n = 30) and 0.46 vs 0.46 (n = 29), with the sparse upper bins off; digits (n = 26) is directionally right but cannot be assessed; breast-w predictions sit at ≈ 0.5 because almost all audited increments fall in the central bin (|z| < 0.15). π is exact by construction (rule layer).
- **T4 checks** (per non-inert proposal, A3's prior as the plug-in law): Proposition 7 exact gap vs realised threshold gain at g = 0 is digits 0.00021 vs 0.00104, tabular 0.000046 vs 0.000034, breast-w ≈ 0 vs ≈ 0. The bounds bracket the exact gap. Proposition 8 screening term vs realised screening gain is tabular 0.00025 vs 0.00023 at g = 0.1σ and digits 0.00016 vs 0.00026, the same order of magnitude.
- **Breast-w:** the audited increments are tiny relative to σ_node (median se 0.00012 vs σ_node 0.0039). No threshold gain is available, and A3 can lose slightly through screening.

## 5. Findings that matter for the design

1. The pipeline runs end to end, the replay is exact on all 1,400 ledger rows, and audits are cheap (≈ 5 run-seconds per proposal with incumbent sharing).
2. **Duplicates are not zero-increment.** Of the 841 rule-inert proposals in the table, 727 are duplicates of an earlier evaluated *non-incumbent* configuration (the other 114 equal the incumbent; all are DT4 ionosphere), and 520 of the duplicates have Δ̂ ≠ 0. T4 §1 sets Δ̂ = 0 on the inert event. That holds for incumbent-equal and inactive-key edits, but not for duplicates: there Δ̂ is *known before the run* (bit-exact seeds), not zero. Skipping is still optimal (zero information value), but the label convention "inert bin = 1, Δ = 0" misstates their increment. It does not affect A3 − A2, since both apply the same rule. It does bias A0/A1 levels and the T4 §1 statement. Suggested fix: a separate "known-Δ̂" category with the cached Δ̂ used in the keep rule.
3. **Seed-split labels are needed** whenever proposals recur across instances (see §4). The full sweep should use disjoint label and value seeds, or K = 10 with a 5/5 split.
4. **De-biasing the DI value residual with fresh audits removes it** on memory-on tabular (§3). This bears directly on C4 and on whether A7 is needed.
5. The DT4 `openml_ionosphere` stratum is 100 % inert (114/114), and memory-on ionosphere was not audited here.

## 6. Limitations

Tiny sample (150 randomly audited non-inert proposals in three strata, plus 6 DI-only non-inert audits used for training; digits has only 6 instances). The memory-on source is the PARTIAL, interrupted rerun-2 arm (fixed split, never accepted by its gate). Liveness and ionosphere were not audited. g was not tuned on development instances. LightGBM hyperparameters are untuned defaults chosen for tiny data. The A1 index policy has no KG-verify component (D23 verify is outside this one-step evaluation). The per-proposal value uses the logged Δ̂ of root campaigns that ran under ρ, so covariate shift under deployed screening is not represented (C3_DESIGN §4 aggregation round).
