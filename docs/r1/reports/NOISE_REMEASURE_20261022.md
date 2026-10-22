# Noise re-measurement (30 seeds) — 22 October 2026

**Label: `PILOT`. AI-assisted (Claude).** Not evidence, and not to be quoted as a result (RUNBOOK §1, rule 3). An AI agent (Claude) produced this as input for the author's D21 / node-pool decision (PLAN §10, rows D21 and "Node pool (22 Oct)"). Nothing here is adopted. The verdicts are proposals.

## What ran

- **Raw data:** `results/r1/pilot/E1_remeasure_20261022T100942Z/` contains:
  - `runs.jsonl` (1,104 runs), `edits.json` and `manifest.json`, the same files E1 writes;
  - `summary.json` and `tables.md` from `e1_report`;
  - `compare.json` and `compare_tables.md` from `make_tables.py`;
  - `environment.json`.
- **Nodes:** `openml_credit_approval` and `openml_diabetes`.
- **Configurations:** the same five edits as E1, so `edits.json` is identical to E1's: C ×0.5, C ×2, model type → random forest, model type → gradient boosting, and `class_weight` balanced → null.
- **Seeds:** 30 per condition. Training seed 1001–1030 (split at 42), split seed 2001–2030 (training at 42), and joint 3001–3030. The default seeds were run twice for the determinism check. Seeds 1–10 of each block are exactly E1's seeds.
- **Split-seed noise is measured directly by the `split` condition.** That is the variation the `"vary"` verify policy draws on (PLAN §10, "Verify split policy").
- **Commands:**
  - `python -m r1.noise.e1_noise_floor --nodes openml_credit_approval openml_diabetes --seeds 30 --workers 4 --out results/r1/pilot/E1_remeasure_20261022T100942Z --deadline 140`, then `--resume results/r1/pilot/E1_remeasure_20261022T100942Z` twice;
  - `python -m r1.noise.e1_report results/r1/pilot/E1_remeasure_20261022T100942Z`;
  - `python results/r1/pilot/E1_remeasure_20261022T100942Z/make_tables.py results/r1/pilot/E1_remeasure_20261022T100942Z`.
- **Code:** no change to `r1/noise/` or to the harness. The only new code is `make_tables.py`, which sits in the run directory. It imports `e1_report.summarise` unchanged, so every definition below (material edit, P(wrong), the proposed D21 rule, the split-policy rule) is E1's.
- **Commits:** the paper repo branch `noise-remeasure-22oct` is based on `main` at `259db53`. The harness is `r1` at `4d68c54`, clean.
- **Environment:** the Linux VM on the author's Mac (aarch64, 4 cores) with `$HOME/venv313`: Python 3.13.16, scikit-learn 1.9.1, numpy 2.5.4, pandas 3.0.6, scipy 1.18.1. `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=1`.
- **Cost:** three resumable chunks of 140.3 s, 140.4 s and 18.9 s, so **300 s wall in total with 4 workers**. The summed per-run wall time is 1,127 s, with a median of 0.98 s per run under 4-way load. A 2-seed timing probe beforehand (96 runs in 25.9 s) predicted this. The probe's data is not kept.
- **Failures:** 0 of 1,104 runs failed, 0 had a missing metric, and every edit applied. All configurations reproduced their metric bit-for-bit at fixed seeds.

### Deviations and things to know

1. **No background job.** The device shell kills child processes when each call ends, so a `nohup … &` start died after 4 runs. Those runs were discarded and the attempt was restarted from scratch. The run then used E1's own `--resume … --deadline` chunking, exactly as the 12 Oct E1 did.
2. **Library versions changed, which affects the tree models only.** E1 ran under Python 3.11.16, and its scikit-learn version was not recorded. This run used Python 3.13.16 with scikit-learn 1.9.1. On E1's seeds, every logistic-regression configuration (c0, c1, c2, c5) reproduces E1 bit-for-bit. The random-forest and gradient-boosting configurations (c3, c4) do not (Table 5). Comparisons with E1 for c3 and c4 therefore mix two causes: more seeds and a changed environment. Table 1 separates them with the row "new, seeds 1–10", which uses E1's seeds in the new environment.
3. **The proposed D21 rule is E1's, applied unchanged.** A node qualifies if it has ≥ 2 material edits (resolved, with |Δ̂_J| > 2 se, and |Δ̂_J| ≥ 0.002) whose mean plug-in P(wrong) = Φ(−|Δ̂_J|/sd(Δ̂)) is ≥ 0.10. This rule is itself still a proposal; the author has not adopted it.

## Results (all tables generated from the run data by `make_tables.py`)

### Table 1 — re-measured nodes: E1 vs. the 30-seed re-measurement

| Node | data | σ_train | σ_split [95 % CI] | σ_joint | median sd(Δ̂) | δ_n (D18) | material / resolved / all | mean P(wrong), material | regret share | campaign-seed wrong | sd_train/sd_joint | D21 (E1 rule) | split policy (E1 rule) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `openml_credit_approval` | E1 (10 seeds, 12 Oct) | 0.0000 | 0.0080 [0.0055, 0.0146] | 0.0169 | 0.0031 | 0.0020 | 2 / 3 / 5 | 0.09 | 0.09 | 0/3 | 0.15 | more seeds needed | `vary` |
| `openml_credit_approval` | new, seeds 1–10 (= E1 seeds) | 0.0000 | 0.0080 [0.0055, 0.0146] | 0.0169 | 0.0031 | 0.0020 | 2 / 3 / 5 | 0.07 | 0.07 | 0/3 | 0.24 | more seeds needed | `vary` |
| `openml_credit_approval` | new, seeds 11–30 (independent) | 0.0000 | 0.0195 [0.0148, 0.0285] | 0.0323 | 0.0034 | 0.0020 | 2 / 2 / 5 | 0.21 | 0.23 | 1/2 | 0.16 | qualifies | `vary` |
| `openml_credit_approval` | new, all 30 seeds | 0.0000 | 0.0176 [0.0140, 0.0237] | 0.0279 | 0.0030 | 0.0020 | 2 / 3 / 5 | 0.24 | 0.23 | 1/3 | 0.23 | qualifies | `vary` |
| `openml_diabetes` | E1 (10 seeds, 12 Oct) | 0.0000 | 0.0336 [0.0231, 0.0613] | 0.0317 | 0.0024 | 0.0020 | 0 / 0 / 5 | – | – | 0/0 | 0.00 | more seeds needed | `vary` |
| `openml_diabetes` | new, seeds 1–10 (= E1 seeds) | 0.0000 | 0.0336 [0.0231, 0.0613] | 0.0317 | 0.0024 | 0.0020 | 0 / 0 / 5 | – | – | 0/0 | 0.00 | more seeds needed | `vary` |
| `openml_diabetes` | new, seeds 11–30 (independent) | 0.0000 | 0.0378 [0.0287, 0.0551] | 0.0365 | 0.0032 | 0.0020 | 1 / 1 / 5 | 0.31 | 0.31 | 1/1 | 0.06 | more seeds needed | `vary` |
| `openml_diabetes` | new, all 30 seeds | 0.0000 | 0.0359 [0.0286, 0.0482] | 0.0357 | 0.0028 | 0.0020 | 0 / 0 / 5 | – | – | 0/0 | 0.00 | more seeds needed | `vary` |

σ values: sd of the baseline c0 metric over the seeds of one condition; CI is the Gaussian chi-square interval. P(wrong) selection cap Φ(−2/√n): n=10 → 0.26, n=20 → 0.33, n=30 → 0.36.

### Table 2 — per-edit, E1 (10 seeds) vs. new (30 seeds)

| Node | Edit | Δ̂_J ± 2se, E1 | Δ̂_J ± 2se, 30 | sd(Δ̂) joint, E1 → 30 | sd split, E1 → 30 | sd train, E1 → 30 | P(wrong), E1 → 30 | material, E1 → 30 | regret |Δ̂|·P, 30 |
|---|---|---|---|---|---|---|---|---|---|
| `openml_credit_approval` | C 0.15 -> 0.075 | -0.0012 ± 0.0019 | -0.0020 ± 0.0010 | 0.0031 → 0.0027 | 0.0019 → 0.0025 | 0.0000 → 0.0000 | 0.35 → 0.24 | no → no | 0.0005 |
| `openml_credit_approval` | C 0.15 -> 0.3 | 0.0003 ± 0.0013 | 0.0006 ± 0.0011 | 0.0020 → 0.0030 | 0.0015 → 0.0023 | 0.0000 → 0.0000 | 0.43 → 0.43 | no → no | 0.0002 |
| `openml_credit_approval` | model_type logistic_regression -> random_forest | 0.0189 ± 0.0084 | 0.0123 ± 0.0047 | 0.0133 → 0.0129 | 0.0125 → 0.0144 | 0.0016 → 0.0037 | 0.08 → 0.17 | yes → yes | 0.0021 |
| `openml_credit_approval` | model_type logistic_regression -> gradient_boosting | 0.0183 ± 0.0093 | 0.0082 ± 0.0059 | 0.0147 → 0.0162 | 0.0202 → 0.0205 | 0.0028 → 0.0028 | 0.11 → 0.31 | yes → yes | 0.0025 |
| `openml_credit_approval` | class_weight balanced -> null | 0.0006 ± 0.0006 | 0.0002 ± 0.0003 | 0.0009 → 0.0008 | 0.0007 → 0.0008 | 0.0000 → 0.0000 | 0.25 → 0.42 | no → no | 0.0001 |
| `openml_diabetes` | C 0.15 -> 0.075 | 0.0009 ± 0.0015 | 0.0005 ± 0.0008 | 0.0024 → 0.0022 | 0.0012 → 0.0018 | 0.0000 → 0.0000 | 0.36 → 0.42 | no → no | 0.0002 |
| `openml_diabetes` | C 0.15 -> 0.3 | -0.0004 ± 0.0010 | -0.0000 ± 0.0006 | 0.0015 → 0.0016 | 0.0010 → 0.0013 | 0.0000 → 0.0000 | 0.40 → 0.49 | no → no | 0.0000 |
| `openml_diabetes` | model_type logistic_regression -> random_forest | 0.0127 ± 0.0168 | 0.0029 ± 0.0088 | 0.0265 → 0.0241 | 0.0196 → 0.0225 | 0.0053 → 0.0048 | 0.32 → 0.45 | no → no | 0.0013 |
| `openml_diabetes` | model_type logistic_regression -> gradient_boosting | -0.0013 ± 0.0155 | -0.0088 ± 0.0092 | 0.0245 → 0.0253 | 0.0206 → 0.0276 | 0.0009 → 0.0012 | 0.48 → 0.36 | no → no | 0.0032 |
| `openml_diabetes` | class_weight balanced -> null | 0.0011 ± 0.0012 | 0.0010 ± 0.0010 | 0.0019 → 0.0028 | 0.0015 → 0.0018 | 0.0000 → 0.0000 | 0.29 → 0.36 | no → no | 0.0004 |

### Table 3 — bootstrap stability of the proposed D21 verdict (joint seeds resampled, paired across configs)

| Node | data | seeds | P(qualifies) | P(#material = 0/1/2/3+) | mean P(wrong) over material, 5 / 50 / 95 % |
|---|---|---|---|---|---|
| `openml_credit_approval` | E1 (10 seeds) | 10 | 0.39 | 0.00 / 0.01 / 0.80 / 0.18 | 0.01 / 0.09 / 0.17 |
| `openml_diabetes` | E1 (10 seeds) | 10 | 0.09 | 0.56 / 0.33 / 0.10 / 0.00 | 0.06 / 0.19 / 0.26 |
| `openml_credit_approval` | new (30 seeds) | 30 | 0.87 | 0.00 / 0.13 / 0.49 / 0.38 | 0.15 / 0.21 / 0.27 |
| `openml_diabetes` | new (30 seeds) | 30 | 0.03 | 0.43 / 0.55 / 0.03 / 0.00 | 0.22 / 0.31 / 0.35 |

### Table 4 — side by side with the five D21 nodes (E1, 10 seeds) and δ_n per D18

| Node | seeds | σ_train | σ_split | σ_joint | median sd(Δ̂) | δ_n | material / all | mean P(wrong), material | regret share | sd_train/sd_joint | D21 (E1 rule) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `digits_mlp` | 10 | 0.0063 | 0.0075 | 0.0125 | 0.0075 | 0.0020 | 5 / 5 | 0.16 | 0.15 | 0.65 | qualifies |
| `tabular_mlp` | 10 | 0.0032 | 0.0125 | 0.0153 | 0.0019 | 0.0020 | 3 / 5 | 0.10 | 0.08 | 0.56 | qualifies |
| `openml_breast_w` | 10 | 0.0000 | 0.0049 | 0.0030 | 0.0005 | 0.0020 | 2 / 5 | 0.16 | 0.17 | 0.39 | qualifies |
| `openml_ionosphere` | 10 | 0.0000 | 0.0367 | 0.0437 | 0.0162 | 0.0040 | 2 / 5 | 0.16 | 0.14 | 0.06 | qualifies |
| `openml_wdbc` | 10 | 0.0000 | 0.0068 | 0.0080 | 0.0009 | 0.0020 | 2 / 5 | 0.16 | 0.10 | 0.11 | qualifies |
| `openml_credit_approval` | 30 | 0.0000 | 0.0176 | 0.0279 | 0.0030 | 0.0020 | 2 / 5 | 0.24 | 0.23 | 0.23 | qualifies |
| `openml_diabetes` | 30 | 0.0000 | 0.0359 | 0.0357 | 0.0028 | 0.0020 | 0 / 5 | – | – | 0.00 | more seeds needed |

δ_n uses D18 as written: median over all of a node's edits of the joint paired sd(Δ̂) (the E1 'median sd(Δ̂)' column).

### Table 5 — bit-reproducibility of E1's runs (same node, config, condition and seeds)

| Node:config | identical | different |
|---|---|---|
| `openml_credit_approval:c0` | 32 | 0 |
| `openml_credit_approval:c1` | 32 | 0 |
| `openml_credit_approval:c2` | 32 | 0 |
| `openml_credit_approval:c3` | 2 | 30 |
| `openml_credit_approval:c4` | 4 | 28 |
| `openml_credit_approval:c5` | 32 | 0 |
| `openml_diabetes:c0` | 32 | 0 |
| `openml_diabetes:c1` | 32 | 0 |
| `openml_diabetes:c2` | 32 | 0 |
| `openml_diabetes:c3` | 0 | 32 |
| `openml_diabetes:c4` | 5 | 27 |
| `openml_diabetes:c5` | 32 | 0 |


### Table 6 — standard `e1_report` output for the 30-seed run (`tables.md`)

| Node | default m | bit-identical at fixed seed | σ_train | σ_split | σ_joint | median sd(Δ̂) | material / resolved / all edits | mean P(wrong), material | regret share, material | campaign-seed decision wrong | sd_train/sd_joint, material | median s/run | D21 (proposed) | split policy (proposed) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `openml_credit_approval` | 0.9097 | yes | 0.0000 | 0.0176 | 0.0279 | 0.0030 | 2 / 3 / 5 | 0.24 | 0.23 | 1/3 | 0.23 | 1.0 | qualifies | `vary` |
| `openml_diabetes` | 0.8297 | yes | 0.0000 | 0.0359 | 0.0357 | 0.0028 | 0 / 0 / 5 | – | – | 0/0 | 0.00 | 1.0 | more seeds needed | `vary` |

### Per-edit rows

| Node | Edit | Δ̂_J (± 2 se) | material | ϱ_joint | sd(Δ̂) joint | sd train | sd split | P(wrong) | flip rate | campaign Δ̂ | campaign wrong |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `openml_credit_approval` | C 0.15 -> 0.075 | -0.0020 ± 0.0010 | no | 1.00 | 0.0027 | 0.0000 | 0.0025 | 0.24 | 0.30 | 0.0022 | yes |
| `openml_credit_approval` | C 0.15 -> 0.3 | 0.0006 ± 0.0011 | no | 0.99 | 0.0030 | 0.0000 | 0.0023 | 0.43 | – | – | – |
| `openml_credit_approval` | model_type logistic_regression -> random_forest | 0.0123 ± 0.0047 | yes | 0.89 | 0.0129 | 0.0037 | 0.0144 | 0.17 | 0.23 | 0.0135 | no |
| `openml_credit_approval` | model_type logistic_regression -> gradient_boosting | 0.0082 ± 0.0059 | yes | 0.81 | 0.0162 | 0.0028 | 0.0205 | 0.31 | 0.37 | 0.0064 | no |
| `openml_credit_approval` | class_weight balanced -> null | 0.0002 ± 0.0003 | no | 1.00 | 0.0008 | 0.0000 | 0.0008 | 0.42 | – | – | – |
| `openml_diabetes` | C 0.15 -> 0.075 | 0.0005 ± 0.0008 | no | 1.00 | 0.0022 | 0.0000 | 0.0018 | 0.42 | – | – | – |
| `openml_diabetes` | C 0.15 -> 0.3 | -0.0000 ± 0.0006 | no | 1.00 | 0.0016 | 0.0000 | 0.0013 | 0.49 | – | – | – |
| `openml_diabetes` | model_type logistic_regression -> random_forest | 0.0029 ± 0.0088 | no | 0.74 | 0.0241 | 0.0048 | 0.0225 | 0.45 | – | – | – |
| `openml_diabetes` | model_type logistic_regression -> gradient_boosting | -0.0088 ± 0.0092 | no | 0.73 | 0.0253 | 0.0012 | 0.0276 | 0.36 | – | – | – |
| `openml_diabetes` | class_weight balanced -> null | 0.0010 ± 0.0010 | no | 1.00 | 0.0028 | 0.0000 | 0.0018 | 0.36 | – | – | – |

## Reading

### `openml_credit_approval`: now qualifies under E1's rule (proposal: add it to the pool)

- **Mean P(wrong) rises from 0.09 (E1) to 0.24 at 30 seeds**, with 2 material edits out of 5. These are the two model-type switches:
  - random forest: Δ̂_J = +0.0123 ± 0.0047, P(wrong) = 0.17;
  - gradient boosting: Δ̂_J = +0.0082 ± 0.0059, P(wrong) = 0.31.

  The regret share is 0.23. At the campaign's own default seeds, 1 of 3 resolved decisions was wrong: the C ×0.5 edit, which is resolved but sits just below the 0.002 materiality bar.
- **The change comes from the extra seeds, not the environment.** On E1's own seeds in the new environment, mean P(wrong) is 0.07 (verdict "more seeds needed"). Seeds 11–30 alone, which are independent of E1, give 0.21 and "qualifies". With 30 seeds, both tree-switch effects shrank, from about +0.019 to +0.012 and +0.008. That is the expected regression of effects that were *selected* as resolved at n = 10.
- **The baseline split-seed noise roughly doubled**: σ_split went from 0.0080 to 0.0176, and the 95 % CI is now [0.0140, 0.0237]. The spread is broad, with no outlier seeds: on c0, seeds 1–10 have sd 0.0080 and seeds 11–30 have sd 0.0195 (Levene p = 0.06). E1's first ten split seeds were simply on the low side.
- **The verdict is fairly stable.** It qualifies in 87 % of joint-seed bootstrap resamples, against 39 % for the 10-seed E1 data (Table 3). It is also robust to the materiality edge: counting the C ×0.5 edit as material would leave the mean P(wrong) at 0.24.
- **Caveat:** P(wrong) is a plug-in on selected edits. At n = 30 the selection cap is Φ(−2/√30) = 0.36, compared with 0.26 at n = 10. The gradient-boosting edit's 0.31 sits near that cap. The five D21 nodes were judged at n = 10, so a 0.24 at n = 30 and a 0.16 at n = 10 are not strictly comparable figures.

### `openml_diabetes`: does not qualify under E1's rule (proposal: drop it from the pool, no further seeds)

- **The noise is large, but no typical edit has a resolvable consequence.**
  - Baseline: σ_split = 0.0359 [0.0286, 0.0482] and σ_joint = 0.0357; σ_train = 0.
  - Model-type switches: paired sd(Δ̂) of 0.024–0.025.
  - All 5 edits are unresolved at 30 seeds, so there are 0 material edits. The joint-seed bootstrap gives P(qualifies) = 0.03.

  The default rule is close to a coin flip on these edits (P(wrong) 0.36–0.49), but on effects close to zero. The largest single-decision regret |Δ̂|·P is 0.0032.
- **`e1_report` prints "more seeds needed", but more seeds are unlikely to change the verdict.**
  - The gradient-boosting switch (Δ̂_J = −0.0088 ± 0.0092) might resolve at about 35–40 seeds, if its estimate holds.
  - The random-forest switch (Δ̂_J = +0.0029, sd 0.024) would need about (2·0.024/0.0029)² ≈ 270 seeds.
  - The C and `class_weight` edits move J by ≤ 0.001.

  So at most one edit is within reach, short of the rule's minimum of two.
- **For the author:** if D21's wording ("err at a non-trivial rate") is read without the materiality condition, `diabetes` errs very often. It would then serve as a "high-noise, near-null-effect" node, where keeps are mostly noise. That reading differs from the one E1 used for the five current nodes.

### δ_n (D18)

- **Both nodes give δ_n = 0.002, the floor.** D18 as written uses the median over all five edits of the paired sd(Δ̂): 0.0030 for `credit_approval` and 0.0028 for `diabetes`, so 0.25 × median is below 0.002. The same holds at 10 and at 30 seeds.
- **The formula reproduces PLAN's examples**: 0.0020 on `digits_mlp` and 0.0040 on `openml_ionosphere` (Table 4).
- **The median is set by the small logistic-regression edits.** The structural edits alone have sd(Δ̂) of 0.013–0.025 on both nodes. If D18 were meant over structural edits only, δ_n would be about 0.003–0.006.

### Split policy

- Both nodes have σ_train = 0.0000, because logistic regression ignores the training seed.
- The training-seed share of the paired noise on material edits is 0.23 on `credit_approval`. On `diabetes` it is 0.00, measured on the baseline since there are no material edits.
- This confirms the 22 Oct PLAN row (`"vary"` on every node): under `"fixed"`, verify is a no-op on both nodes.

## Qualification proposal (for the author's decision)

| Node | 10-seed E1 verdict | 30-seed verdict (E1 rule) | Proposal |
|---|---|---|---|
| `openml_credit_approval` | more seeds needed (mean P(wrong) 0.09) | qualifies (0.24; bootstrap 0.87) | add to the D21 pool |
| `openml_diabetes` | more seeds needed | 0 material edits (bootstrap 0.03) | do not add; stop re-measuring |

## `openml_credit_g` (and `openml_bank_marketing`): not measured

### No cache exists

Both repos were searched for any `data_cache`, `credit_g`/`credit-g` or `bank_marketing`/`bank-marketing` path.
- **`openml_credit_g`:** `nodes/openml_credit_g/data_cache/` exists in the harness but contains only `.gitkeep` and `.gitignore`. There is no copy under `experiments/r1/pilot/L8_20261009T152916Z/nodes/`, and none in the paper repo.
- **`openml_bank_marketing`:** the situation is the same.
- **Network:** openml.org is blocked from the VM, so nothing was fetched.

### Where E1 looks for a cache

`_prepare_node` copies the node directory. Only if the copy has **no** `data_cache` does it fall back to the L8 pilot cache. Because `nodes/openml_credit_g/data_cache/` exists, even if empty, the L8 fallback is never used for this node. **The cache must therefore be created inside the node directory itself.**

### Commands for the author (Mac terminal, which has network) or the Deepthought/Ada operator

The cache is git-ignored, so it has to be created on each machine that will run the node. The VM shares the Mac folder, so a fetch on the Mac is enough for this VM.

```bash
# 1. Create the cache in the layout benchmark.py uses (fetch_openml(data_home=<node>/data_cache)).
cd <path-to>/autoresearch_harness
python3 -c "from sklearn.datasets import fetch_openml; \
b = fetch_openml(data_id=31, as_frame=True, parser='auto', data_home='nodes/openml_credit_g/data_cache'); \
print(b.data.shape, b.target.value_counts().to_dict())"
#    expected: (1000, 20) {'good': 700, 'bad': 300}
ls nodes/openml_credit_g/data_cache/openml/openml.org/data/v1/download/   # one directory per downloaded file

# 2. Measure it with the same 30-seed procedure (paper repo; the VM has no network, which proves the cache works offline).
cd <path-to>/agent_paper_B
export PATH=$HOME/venv313/bin:$PATH AR_HARNESS_ROOT=<path-to>/autoresearch_harness OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
OUT=results/r1/pilot/E1_remeasure_credit_g_$(date -u +%Y%m%dT%H%M%SZ)
python -m r1.noise.e1_noise_floor --nodes openml_credit_g --seeds 2 --workers 4 --out /tmp/credit_g_probe   # timing probe; check metrics are present
python -m r1.noise.e1_noise_floor --nodes openml_credit_g --seeds 30 --workers 4 --out $OUT --deadline 140
python -m r1.noise.e1_noise_floor --resume $OUT --workers 4 --deadline 140        # repeat until "remaining": 0
python -m r1.noise.e1_report $OUT
```

- On a shell that is not time-boxed, drop `--deadline` and run the job once.
- Expected cost: 552 runs. At about 1 s per run under 4 workers, that is roughly 3 minutes; `credit-g` has 1,000 rows, against 690 in `credit-approval`.
- To bring the 22 Oct comparison tables in, copy `make_tables.py` and add the node to `NEW_NODES`.
- **`openml_bank_marketing`** (ID 1461, 45,211 rows; its config gives 3–15 s per trial) follows the same procedure with `data_id=1461` and its own node directory.
  - Cost: 552 runs at 3–15 s each, so roughly 7–35 min on 4 workers. This is an estimate, not a measurement; gradient boosting on 45k rows may be slower.
  - With a validation split of about 6,800 rows, split noise is likely small, so it is a weaker candidate.

## Pool count

- **Current count:** the five D21 nodes plus `openml_credit_approval` (if accepted) make **6 qualifying nodes, against the PLAN target of ≥ 8**.
- **Even if `openml_credit_g` qualifies, the pool reaches only 7.** At least one further node is needed, and realistically 2–3 should be measured: `diabetes` failed even at 30 seeds, and `credit_approval` qualified only once it had 30 seeds.

### Natural further candidates

These are small, binary, CPU-fast OpenML datasets that the existing `openml_template` handles: a binary target, the frozen LR/RF/GB pipeline, and categorical imputation. **Dataset IDs and sizes are from the agent's memory and must be checked on openml.org before fetching.**

| Candidate (OpenML ID) | Size | Why |
|---|---|---|
| `sonar` (40) | 208 × 60, numeric | Very small, like `ionosphere`; split noise is likely high, and model type is likely to matter. |
| `ilpd` (1480) | 583 × 10, 1 categorical | Hard, noisy medical task, similar to `diabetes`; it carries the same risk of having no material edit. |
| `blood-transfusion-service-center` (1464) | 748 × 4 | Small and noisy; non-linear effects make the model-type switches likely to be material. |
| `qsar-biodeg` (1494) | 1,055 × 41 | Mid-size, and model type matters. |
| `climate-model-simulation-crashes` (1467) | 540 × 20 | Imbalanced, so `class_weight` edits may be material. |

- **Avoid** `australian` (40981), which is the same Statlog credit data as `credit-approval`, and `banknote-authentication` (1462), whose AUC ≈ 1 leaves no material edits.

### What each new candidate needs (harness changes; author or operator, not done here)

The pattern follows L8 (harness commit `b55209f`):
1. `nodes/openml_<name>/` copied from `nodes/openml_template/`, plus a `dataset.json` holding `{node_name, dataset_id, dataset_name, target}`.
2. `configs/nodes/openml_<name>.yaml` copied from `openml_credit_approval.yaml`, with the name, description and dataset fields changed. Set `active_keys.dataset_excluded: ["imputer"]` if the dataset has no categorical columns (D25).
3. A registry entry in `src/autoresearch/nodes/registry.py`. The metric parser is the shared `openml_credit_g.metric_parser:parse_val_auc`.
4. The harness tests that enumerate nodes (`tests/stage2/test_r1_l8.py`, the D25 active-key tests).
5. A data cache fetched on a networked machine into `nodes/openml_<name>/data_cache`, with the command above and the new `data_id`. Unlike `credit_g`, template nodes have no `data_cache/.gitignore`, so add one or the cache shows up as untracked.
6. The same 30-seed E1 run and `e1_report`.

## Caveats

- These are PILOT numbers with hand-specified "typical" edits, not LLM proposals.
- P(wrong) is a plug-in on edits selected by resolution; it is a rough figure, not an estimate with a stated error (see the L14 caveat in the 12 Oct report).
- The proposed D21 rule's threshold behaves differently at n = 10 and n = 30, because the selection cap moves from 0.26 to 0.36. Re-measuring the five D21 nodes at 30 seeds would put all seven on the same footing. At about 1 s per run, that is cheap on CPU.
- The tree-model numbers depend on the scikit-learn version (Table 5). Any later campaign on these nodes should record library versions; the E1 manifest does not.
