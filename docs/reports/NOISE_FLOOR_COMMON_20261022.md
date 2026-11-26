# Common 30-seed noise-floor measurement (E1, ten nodes) — 22 October 2026

**Label: `PILOT`, pending the author's acceptance. AI-assisted (Claude).** This is the measurement that PLAN §10 declares as the C1 noise-floor table (row "D21 common measurement (22 Oct)"). An AI agent (Claude) ran it and applied the adopted D21 rule (row "D21 rule (22 Oct)") exactly as written. Until the coordinating session and the author accept it, it is not evidence and is not to be quoted as a result (RUNBOOK §1, rule 3). `r1/c3/dataset.py` (`E1_SUMMARY`) still points at the 12 Oct E1; repointing it is left to the coordinating session after acceptance.

## What ran

- **Raw data:** `results/r1/pilot/E1_20261022T214606Z/` contains:
  - `runs.jsonl` (5,520 runs), `edits.json` and `manifest.json`, written by `r1.noise.e1_noise_floor`;
  - `summary.json` and `tables.md`, from `r1.noise.e1_report`;
  - `compare.json` and `compare_tables.md`, from `make_tables.py` (in the run directory);
  - `recheck_determinism.json`, from `recheck_determinism.py` (in the run directory);
  - `environment.json`: the full package list of the interpreter, the commands and the timing probe.
- **Nodes (ten, PLAN "D21 common measurement"):** the five 18 Oct D21 nodes `digits_mlp`, `tabular_mlp`, `openml_breast_w`, `openml_ionosphere` and `openml_wdbc`; `openml_credit_approval` (added 22 Oct, re-checked here); and the four candidates `openml_credit_g`, `openml_sonar`, `openml_blood_transfusion` and `openml_qsar_biodeg`.
- **Edits:** the standard E1 edit set, five per node.
  - `edits.json` is identical to the 12 Oct E1's for the seven nodes that E1 listed. That includes `credit_g`: E1 generated its edits but could not run it.
  - The three new OpenML nodes get the same generator's OpenML set: C ×0.5, C ×2, model type → random forest, model type → gradient boosting, and `class_weight` balanced → null.
- **Seeds:** 30 per condition for every node and every configuration (checked in Table 2).
  - Training seed 1001–1030, with the split seed at the node default.
  - Split seed 2001–2030, with the training seed at the node default.
  - Joint seeds 3001–3030.
  - Every configuration also ran twice at the node's default seeds.
  - Seeds 1–10 of each block are exactly the 12 Oct E1's seeds.
- **Environment (declared): the harness-locked venv `$HOME/hvenv`.** It runs Python 3.13.16 with scikit-learn 1.8.0, numpy 2.4.4, scipy 1.17.1 and pandas 3.0.3, built from the harness `uv.lock`.
  - It runs on the Linux VM on the author's Mac (aarch64, 4 cores), with `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=1`.
  - **`manifest.json` records these versions under `host.libraries`**, as the D21 rule row requires.
  - One interpreter ran every chunk.
- **Harness:** the main checkout `autoresearch_harness`, branch `r1` at `4012897`. It was clean (`dirty: false` in the manifest) and was not modified.
- **Paper repo:** branch `e1-common-22oct`, based on `main` at `7d326f7`. The worktree is `.claude-worktrees/e1-common-22oct`.
- **Commands** (also listed in `environment.json`):
  - `python3 -m r1.noise.e1_noise_floor --nodes <ten nodes> --seeds 30 --workers 4 --deadline 140`, then `--resume results/r1/pilot/E1_20261022T214606Z --workers 4 --deadline 140` nine times;
  - `python3 -m r1.noise.e1_report results/r1/pilot/E1_20261022T214606Z`;
  - `python3 results/r1/pilot/E1_20261022T214606Z/recheck_determinism.py results/r1/pilot/E1_20261022T214606Z`;
  - `python3 results/r1/pilot/E1_20261022T214606Z/make_tables.py results/r1/pilot/E1_20261022T214606Z`.
- **Code:** `r1/noise/` and the harness are unchanged. The new code is two scripts in the run directory.
  - `make_tables.py` imports `e1_report.summarise` unchanged for every per-node and per-edit statistic. It applies the adopted D21 rule in its own function, `d21_adopted`, and recomputes the rule's effect criteria independently from the raw joint differences.
  - **Its outputs are byte-identical on re-run**, checked by sha256 together with `summary.json` and `tables.md`. They contain no absolute or temporary paths.
  - The one absolute path in the run directory is the harness root in `manifest.json`, which the generator writes, as in every earlier E1 manifest.
- **Unrelated edit on the same branch:** the `NODE_INFO` comment in `r1/c3/features.py` for the four 22 Oct nodes. It now says that the values were verified against the fetched data on 22 Oct with `r1/noise/check_caches.py`. The values are unchanged, and a re-run of `check_caches` reproduced them.

### Cost

| | runs | wall | note |
|---|---|---|---|
| Timing probe (2 seeds; output outside the repo and deleted) | 480 | 107.0 s | 0 failures; median 0.8 s per run under 4-way load |
| Projection for 30 seeds | 5,520 | 1,230 s (≈ 20.5 min) | 5,520 × 107.0 / 480 |
| **Actual** | **5,520** | **1,298 s (≈ 21.6 min)**, in 10 chunks (9 × ≈ 140 s + 32 s) | Summed per-run wall time 4,908 s; median 0.85 s per run under 4-way load (max 3.8 s) |
| Determinism re-check | 180 | 39 s | see below |

The per-run cost is flat across nodes, with node medians of 0.81–0.91 s. The projection was 5 % low.

### Failures, determinism and checks

- **No run failed.**
  - 0 of 5,520 runs failed, none had a missing metric, every edit applied (`edit_applied` true for all 4,600 edit runs), and there are no duplicate rows.
  - Every node × configuration × condition has exactly 30 seeds.
- **Determinism held in every check.**
  - At the default seeds, all 60 configurations (10 nodes × 6) reproduced their metric bit-for-bit (`default` vs `default_repeat`).
  - In addition, `recheck_determinism.py` re-ran one training-seed, one split-seed and one joint-seed run (seed indices 14, 22 and 29) for every node and configuration. That is 180 runs through the same `run_one`, and **all 180 metrics were bit-identical** to `runs.jsonl`.
- **The 12 Oct E1's runs are reproduced bit-for-bit, tree models included.**
  - For the six nodes that E1 measured, every one of E1's 32 runs per configuration (seeds 1–10 × 3 conditions + 2 default runs) is identical in this run (Table 7). That covers all 36 configurations, so 1,152 of 1,152 runs.
  - For those six nodes, this 30-seed run is therefore a strict extension of E1: the "seeds 1–10" rows of Table 5 equal E1's rows exactly.
  - E1's manifest did not record its scikit-learn version. That its random-forest and gradient-boosting runs match scikit-learn 1.8.0 bit-for-bit suggests, but does not prove, that it ran under 1.8.x.
- **The 22 Oct re-measurement is not reproduced for tree models (version effect).**
  - On `openml_credit_approval` with the same 30 seeds, the logistic-regression configurations (c0, c1, c2, c5) are identical in 92 of 92 runs each.
  - Random forest (c3) differs in 90 of 92 runs and gradient boosting (c4) in 84 of 92. That run used scikit-learn 1.9.1 (Table 7).
  - **Tree-model metrics depend on the library version.** Any number in this report for c3 or c4 holds for scikit-learn 1.8.0.

## Rule implementation check (`e1_report` vs. PLAN §10 "D21 rule (22 Oct)")

The PLAN row says that a node is a noise node iff, measured with 30 seeds per condition (training, split and joint seeds; `"vary"` split), it has all of the following:
- ≥ 2 material edits, where material means resolved, |Δ̂_J| > 2 se and |Δ̂_J| ≥ 0.002, on the standard E1 edit set;
- mean plug-in P(wrong) ≥ 0.10 over those edits;
- σ_joint > 0.

### What matches word for word

| Criterion | PLAN | `r1/noise/e1_report.py` |
|---|---|---|
| Resolved | \|Δ̂_J\| > 2 se | `abs(delta) > 2 * se` (if se = 0: `delta != 0`, the same inequality) |
| Material | resolved and \|Δ̂_J\| ≥ 0.002 | `resolved and abs(delta) >= MIN_EFFECT`, `MIN_EFFECT = 0.002` |
| Count | ≥ 2 | `n_material >= MIN_EDITS`, `MIN_EDITS = 2` |
| Error rate | mean plug-in P(wrong) ≥ 0.10 over the material edits | `mean(p_model over material) >= QUALIFY_P`, `QUALIFY_P = 0.10`, with `p_model = Φ(−\|Δ̂_J\|/sd_joint)` |
| Noise | σ_joint > 0 | `sigma_joint > 0` (the sd of the baseline over joint seeds, E1's σ_joint) |

### What differs, and what this report did

The two points below are not differences in any criterion, but they would change the reported verdict if `e1_report`'s labels were used unchanged. This report applies the PLAN row; Tables 1, 2 and 8 use `make_tables.py`'s `d21_adopted`.

1. **The seed requirement is not checked by `e1_report`.** The PLAN rule requires 30 seeds per condition; `e1_report` judges any seed count.
   - `make_tables.py` checks it explicitly: 30/30/30 on every node, for every configuration.
2. **`e1_report` has a third label, "more seeds needed", that is not part of the adopted rule.** It prints that label when a node fails and has an unresolved edit with sd(Δ̂) ≥ 0.002.
   - Under the adopted rule, the seed count is fixed at 30, so the outcome is binary.
   - `openml_credit_g` and `openml_qsar_biodeg`, labelled "more seeds needed" by `e1_report`, are **"does not qualify"** here.

Two smaller points:
- `e1_report`'s column headers and comments still call the rule "proposed". This is cosmetic, and the code was not changed.
- The independent recomputation in `make_tables.py`, from raw joint differences, gives the same #material, mean P(wrong) and verdict on all ten nodes (Table 2).

## Results (all tables generated from the run data by `make_tables.py`; copied from `compare_tables.md`)

### Table 1 — C1 noise-floor table: ten nodes, 30 seeds per condition, adopted D21 rule

| Node | seeds train/split/joint | default m | σ_train [95 % CI] | σ_split [95 % CI] | σ_joint [95 % CI] | median sd(Δ̂) | δ_n (D18) | material / resolved / all | mean P(wrong), material | regret share | campaign-seed wrong | split policy (E1 rule) | **D21 verdict (adopted rule)** | bootstrap P(qualifies) (not decisive) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `digits_mlp` | 30/30/30 | 0.9554 | 0.0068 [0.0054, 0.0092] | 0.0073 [0.0058, 0.0099] | 0.0102 [0.0081, 0.0137] | 0.0066 | 0.0020 | 5 / 5 / 5 | 0.101 | 0.10 | 0/5 | `fixed` | **qualifies** | 0.48 |
| `tabular_mlp` | 30/30/30 | 0.9141 | 0.0029 [0.0023, 0.0039] | 0.0123 [0.0098, 0.0165] | 0.0121 [0.0096, 0.0163] | 0.0019 | 0.0020 | 3 / 3 / 5 | 0.125 | 0.09 | 0/3 | `fixed` | **qualifies** | 0.75 |
| `openml_breast_w` | 30/30/30 | 0.9932 | 0.0000 [0.0000, 0.0000] | 0.0050 [0.0040, 0.0067] | 0.0038 [0.0031, 0.0051] | 0.0007 | 0.0020 | 2 / 2 / 5 | 0.233 | 0.23 | 0/2 | `vary` | **qualifies** | 0.97 |
| `openml_ionosphere` | 30/30/30 | 0.9845 | 0.0000 [0.0000, 0.0000] | 0.0485 [0.0386, 0.0651] | 0.0410 [0.0327, 0.0551] | 0.0160 | 0.0040 | 2 / 2 / 5 | 0.195 | 0.17 | 1/2 | `vary` | **qualifies** | 0.92 |
| `openml_wdbc` | 30/30/30 | 0.9976 | 0.0000 [0.0000, 0.0000] | 0.0061 [0.0048, 0.0082] | 0.0079 [0.0063, 0.0106] | 0.0007 | 0.0020 | 2 / 4 / 5 | 0.174 | 0.12 | 2/4 | `vary` | **qualifies** | 0.99 |
| `openml_credit_approval` | 30/30/30 | 0.9097 | 0.0000 [0.0000, 0.0000] | 0.0176 [0.0140, 0.0237] | 0.0279 [0.0222, 0.0375] | 0.0030 | 0.0020 | 2 / 3 / 5 | 0.229 | 0.22 | 1/3 | `vary` | **qualifies** | 0.90 |
| `openml_credit_g` | 30/30/30 | 0.7691 | 0.0000 [0.0000, 0.0000] | 0.0482 [0.0384, 0.0648] | 0.0335 [0.0267, 0.0450] | 0.0038 | 0.0020 | 1 / 4 / 5 | 0.294 | 0.29 | 2/4 | `vary` | does not qualify | 0.52 |
| `openml_sonar` | 30/30/30 | 0.7563 | 0.0000 [0.0000, 0.0000] | 0.0603 [0.0480, 0.0810] | 0.0597 [0.0475, 0.0802] | 0.0128 | 0.0032 | 4 / 4 / 5 | 0.196 | 0.14 | 2/4 | `vary` | **qualifies** | 1.00 |
| `openml_blood_transfusion` | 30/30/30 | 0.7845 | 0.0000 [0.0000, 0.0000] | 0.0556 [0.0443, 0.0747] | 0.0564 [0.0449, 0.0758] | 0.0030 | 0.0020 | 2 / 2 / 5 | 0.103 | 0.09 | 0/2 | `vary` | **qualifies** | 0.48 |
| `openml_qsar_biodeg` | 30/30/30 | 0.9389 | 0.0000 [0.0000, 0.0000] | 0.0217 [0.0173, 0.0292] | 0.0180 [0.0143, 0.0241] | 0.0023 | 0.0020 | 0 / 2 / 5 | – | – | 0/2 | `vary` | does not qualify | 0.10 |

σ: sd of the baseline c0 metric over the 30 seeds of one condition; CI is the Gaussian chi-square interval. δ_n = max(0.002, 0.25 × median over all five edits of the joint paired sd(Δ̂)). Mean P(wrong) is shown to three decimals because two nodes sit within 0.004 of the 0.10 threshold. P(wrong) selection cap at n = 30: Φ(−2/√30) = 0.36.

### Table 2 — the adopted rule, criterion by criterion, and an independent recomputation

| Node | 30 seeds per condition | ≥ 2 material edits | mean P(wrong) ≥ 0.10 | σ_joint > 0 | verdict | recomputed from raw joint differences (#material, mean P(wrong), verdict) | e1_report label |
|---|---|---|---|---|---|---|---|
| `digits_mlp` | yes | yes | yes | yes | **qualifies** | 5, 0.101, qualifies | qualifies |
| `tabular_mlp` | yes | yes | yes | yes | **qualifies** | 3, 0.125, qualifies | qualifies |
| `openml_breast_w` | yes | yes | yes | yes | **qualifies** | 2, 0.233, qualifies | qualifies |
| `openml_ionosphere` | yes | yes | yes | yes | **qualifies** | 2, 0.195, qualifies | qualifies |
| `openml_wdbc` | yes | yes | yes | yes | **qualifies** | 2, 0.174, qualifies | qualifies |
| `openml_credit_approval` | yes | yes | yes | yes | **qualifies** | 2, 0.229, qualifies | qualifies |
| `openml_credit_g` | yes | no | yes | yes | does not qualify | 1, 0.294, does not qualify | more seeds needed |
| `openml_sonar` | yes | yes | yes | yes | **qualifies** | 4, 0.196, qualifies | qualifies |
| `openml_blood_transfusion` | yes | yes | yes | yes | **qualifies** | 2, 0.103, qualifies | qualifies |
| `openml_qsar_biodeg` | yes | no | no | yes | does not qualify | 0, –, does not qualify | more seeds needed |

### Table 3 — seed-bootstrap of the rule's outcome (joint seeds resampled, paired across configs; reported, not decisive)

| Node | seeds | P(qualifies) | P(#material = 0 / 1 / 2 / 3+) | mean P(wrong) over material, 5 / 50 / 95 % |
|---|---|---|---|---|
| `digits_mlp` | 30 | 0.48 | 0.00 / 0.00 / 0.00 / 1.00 | 0.07 / 0.10 / 0.13 |
| `tabular_mlp` | 30 | 0.75 | 0.00 / 0.00 / 0.17 / 0.83 | 0.04 / 0.12 / 0.15 |
| `openml_breast_w` | 30 | 0.97 | 0.00 / 0.03 / 0.97 / 0.00 | 0.15 / 0.22 / 0.27 |
| `openml_ionosphere` | 30 | 0.92 | 0.00 / 0.06 / 0.52 / 0.42 | 0.11 / 0.21 / 0.27 |
| `openml_wdbc` | 30 | 0.99 | 0.00 / 0.01 / 0.99 / 0.00 | 0.13 / 0.17 / 0.21 |
| `openml_credit_approval` | 30 | 0.90 | 0.00 / 0.09 / 0.49 / 0.42 | 0.14 / 0.21 / 0.26 |
| `openml_credit_g` | 30 | 0.52 | 0.10 / 0.38 / 0.35 / 0.18 | 0.17 / 0.26 / 0.33 |
| `openml_sonar` | 30 | 1.00 | 0.00 / 0.00 / 0.01 / 0.99 | 0.14 / 0.18 / 0.23 |
| `openml_blood_transfusion` | 30 | 0.48 | 0.00 / 0.00 / 1.00 / 0.00 | 0.04 / 0.10 / 0.16 |
| `openml_qsar_biodeg` | 30 | 0.10 | 0.63 / 0.27 / 0.09 / 0.01 | 0.12 / 0.24 / 0.35 |

B = 2000 resamples, numpy default_rng(20261022). The bootstrap applies the rule's effect criteria and σ_joint > 0 to each resample.

### Table 4 — per-edit rows (30 seeds), with the 12 Oct E1 (10 seeds) where it measured the node

| Node | Edit | Δ̂_J ± 2se | material | sd(Δ̂) joint | sd train | sd split | ϱ_joint | P(wrong) | regret \|Δ̂\|·P | 12 Oct: Δ̂_J ± 2se | 12 Oct: sd(Δ̂) joint | 12 Oct: P(wrong) | 12 Oct: material |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `digits_mlp` | LEARNING_RATE_INIT 1e-3 -> 0.002 | 0.0080 ± 0.0024 | yes | 0.0066 | 0.0050 | 0.0054 | 0.77 | 0.11 | 0.0009 | 0.0089 ± 0.0048 | 0.0075 | 0.12 | yes |
| `digits_mlp` | MAX_ITER 40 -> 80 | 0.0085 ± 0.0022 | yes | 0.0059 | 0.0043 | 0.0048 | 0.82 | 0.07 | 0.0006 | 0.0089 ± 0.0041 | 0.0064 | 0.08 | yes |
| `digits_mlp` | HIDDEN_UNITS 32 -> 16 | -0.0159 ± 0.0040 | yes | 0.0110 | 0.0121 | 0.0095 | 0.60 | 0.07 | 0.0012 | -0.0134 ± 0.0091 | 0.0143 | 0.18 | yes |
| `digits_mlp` | HIDDEN_UNITS 32 -> 64 | 0.0089 ± 0.0030 | yes | 0.0083 | 0.0077 | 0.0078 | 0.71 | 0.14 | 0.0012 | 0.0067 ± 0.0060 | 0.0095 | 0.24 | yes |
| `digits_mlp` | BATCH_SIZE 64 -> 32 | 0.0068 ± 0.0019 | yes | 0.0053 | 0.0044 | 0.0049 | 0.86 | 0.10 | 0.0007 | 0.0067 ± 0.0043 | 0.0068 | 0.16 | yes |
| `tabular_mlp` | MAX_ITER 40 -> 20 | -0.0087 ± 0.0013 | yes | 0.0036 | 0.0021 | 0.0034 | 0.97 | 0.01 | 0.0001 | -0.0097 ± 0.0029 | 0.0046 | 0.02 | yes |
| `tabular_mlp` | ALPHA 1e-4 -> 5e-05 | 0.0000 ± 0.0000 | no | 0.0000 | 0.0001 | 0.0001 | 1.00 | 0.49 | 0.0000 | -0.0000 ± 0.0000 | 0.0001 | 0.48 | no |
| `tabular_mlp` | BATCH_SIZE 64 -> 32 | 0.0025 ± 0.0007 | yes | 0.0019 | 0.0012 | 0.0013 | 0.99 | 0.10 | 0.0002 | 0.0022 ± 0.0012 | 0.0019 | 0.12 | yes |
| `tabular_mlp` | ALPHA 1e-4 -> 0.0002 | -0.0000 ± 0.0000 | no | 0.0001 | 0.0000 | 0.0001 | 1.00 | 0.49 | 0.0000 | -0.0000 ± 0.0000 | 0.0000 | 0.40 | no |
| `tabular_mlp` | HIDDEN_UNITS 32 -> 16 | -0.0038 ± 0.0023 | yes | 0.0062 | 0.0062 | 0.0044 | 0.88 | 0.27 | 0.0010 | -0.0059 ± 0.0039 | 0.0061 | 0.17 | yes |
| `openml_breast_w` | C 0.15 -> 0.075 | -0.0002 ± 0.0002 | no | 0.0007 | 0.0000 | 0.0005 | 0.98 | 0.38 | 0.0001 | -0.0001 ± 0.0002 | 0.0004 | 0.41 | no |
| `openml_breast_w` | C 0.15 -> 0.3 | -0.0001 ± 0.0002 | no | 0.0006 | 0.0000 | 0.0005 | 0.99 | 0.46 | 0.0000 | -0.0002 ± 0.0003 | 0.0005 | 0.33 | no |
| `openml_breast_w` | model_type logistic_regression -> random_forest | -0.0035 ± 0.0019 | yes | 0.0052 | 0.0021 | 0.0043 | 0.72 | 0.25 | 0.0009 | -0.0025 ± 0.0015 | 0.0024 | 0.15 | yes |
| `openml_breast_w` | model_type logistic_regression -> gradient_boosting | -0.0057 ± 0.0027 | yes | 0.0073 | 0.0017 | 0.0184 | 0.48 | 0.22 | 0.0012 | -0.0050 ± 0.0034 | 0.0054 | 0.17 | yes |
| `openml_breast_w` | class_weight balanced -> null | 0.0000 ± 0.0001 | no | 0.0002 | 0.0000 | 0.0004 | 1.00 | 0.42 | 0.0000 | 0.0001 ± 0.0001 | 0.0002 | 0.32 | no |
| `openml_ionosphere` | C 0.15 -> 0.075 | -0.0040 ± 0.0051 | no | 0.0140 | 0.0000 | 0.0085 | 0.96 | 0.39 | 0.0016 | -0.0014 ± 0.0086 | 0.0135 | 0.46 | no |
| `openml_ionosphere` | C 0.15 -> 0.3 | -0.0023 ± 0.0058 | no | 0.0160 | 0.0000 | 0.0122 | 0.92 | 0.44 | 0.0010 | -0.0025 ± 0.0102 | 0.0162 | 0.44 | no |
| `openml_ionosphere` | model_type logistic_regression -> random_forest | 0.0500 ± 0.0146 | yes | 0.0399 | 0.0022 | 0.0449 | 0.34 | 0.11 | 0.0053 | 0.0502 ± 0.0245 | 0.0387 | 0.10 | yes |
| `openml_ionosphere` | model_type logistic_regression -> gradient_boosting | 0.0255 ± 0.0164 | yes | 0.0449 | 0.0022 | 0.0616 | 0.28 | 0.28 | 0.0073 | 0.0291 ± 0.0242 | 0.0382 | 0.22 | yes |
| `openml_ionosphere` | class_weight balanced -> null | 0.0001 ± 0.0021 | no | 0.0057 | 0.0000 | 0.0047 | 0.99 | 0.49 | 0.0001 | 0.0003 ± 0.0034 | 0.0054 | 0.48 | no |
| `openml_wdbc` | C 0.15 -> 0.075 | -0.0003 ± 0.0002 | no | 0.0007 | 0.0000 | 0.0007 | 1.00 | 0.34 | 0.0001 | -0.0002 ± 0.0006 | 0.0009 | 0.40 | no |
| `openml_wdbc` | C 0.15 -> 0.3 | 0.0003 ± 0.0002 | no | 0.0007 | 0.0000 | 0.0009 | 1.00 | 0.32 | 0.0001 | 0.0002 ± 0.0005 | 0.0008 | 0.42 | no |
| `openml_wdbc` | model_type logistic_regression -> random_forest | -0.0061 ± 0.0033 | yes | 0.0091 | 0.0015 | 0.0059 | 0.68 | 0.25 | 0.0015 | -0.0075 ± 0.0073 | 0.0115 | 0.26 | yes |
| `openml_wdbc` | model_type logistic_regression -> gradient_boosting | -0.0316 ± 0.0088 | yes | 0.0242 | 0.0007 | 0.0246 | 0.59 | 0.10 | 0.0030 | -0.0325 ± 0.0134 | 0.0212 | 0.06 | yes |
| `openml_wdbc` | class_weight balanced -> null | 0.0000 ± 0.0002 | no | 0.0006 | 0.0000 | 0.0004 | 1.00 | 0.50 | 0.0000 | 0.0000 ± 0.0004 | 0.0007 | 0.50 | no |
| `openml_credit_approval` | C 0.15 -> 0.075 | -0.0020 ± 0.0010 | no | 0.0027 | 0.0000 | 0.0025 | 1.00 | 0.24 | 0.0005 | -0.0012 ± 0.0019 | 0.0031 | 0.35 | no |
| `openml_credit_approval` | C 0.15 -> 0.3 | 0.0006 ± 0.0011 | no | 0.0030 | 0.0000 | 0.0023 | 0.99 | 0.43 | 0.0002 | 0.0003 ± 0.0013 | 0.0020 | 0.43 | no |
| `openml_credit_approval` | model_type logistic_regression -> random_forest | 0.0130 ± 0.0048 | yes | 0.0130 | 0.0035 | 0.0141 | 0.88 | 0.16 | 0.0021 | 0.0189 ± 0.0084 | 0.0133 | 0.08 | yes |
| `openml_credit_approval` | model_type logistic_regression -> gradient_boosting | 0.0085 ± 0.0059 | yes | 0.0162 | 0.0026 | 0.0199 | 0.81 | 0.30 | 0.0026 | 0.0183 ± 0.0093 | 0.0147 | 0.11 | yes |
| `openml_credit_approval` | class_weight balanced -> null | 0.0002 ± 0.0003 | no | 0.0008 | 0.0000 | 0.0008 | 1.00 | 0.42 | 0.0001 | 0.0006 ± 0.0006 | 0.0009 | 0.25 | no |
| `openml_credit_g` | C 0.15 -> 0.075 | 0.0019 ± 0.0014 | no | 0.0038 | 0.0000 | 0.0040 | 0.99 | 0.30 | 0.0006 | – | – | – | – |
| `openml_credit_g` | C 0.15 -> 0.3 | -0.0014 ± 0.0012 | no | 0.0032 | 0.0000 | 0.0042 | 1.00 | 0.33 | 0.0005 | – | – | – | – |
| `openml_credit_g` | model_type logistic_regression -> random_forest | -0.0029 ± 0.0074 | no | 0.0203 | 0.0083 | 0.0161 | 0.83 | 0.44 | 0.0013 | – | – | – | – |
| `openml_credit_g` | model_type logistic_regression -> gradient_boosting | -0.0150 ± 0.0101 | yes | 0.0277 | 0.0026 | 0.0262 | 0.66 | 0.29 | 0.0044 | – | – | – | – |
| `openml_credit_g` | class_weight balanced -> null | 0.0011 ± 0.0011 | no | 0.0031 | 0.0000 | 0.0037 | 1.00 | 0.36 | 0.0004 | – | – | – | – |
| `openml_sonar` | C 0.15 -> 0.075 | 0.0062 ± 0.0041 | yes | 0.0113 | 0.0000 | 0.0117 | 0.98 | 0.29 | 0.0018 | – | – | – | – |
| `openml_sonar` | C 0.15 -> 0.3 | -0.0087 ± 0.0047 | yes | 0.0128 | 0.0000 | 0.0098 | 0.98 | 0.25 | 0.0022 | – | – | – | – |
| `openml_sonar` | model_type logistic_regression -> random_forest | 0.0569 ± 0.0163 | yes | 0.0447 | 0.0211 | 0.0581 | 0.67 | 0.10 | 0.0058 | – | – | – | – |
| `openml_sonar` | model_type logistic_regression -> gradient_boosting | -0.1041 ± 0.0352 | yes | 0.0964 | 0.0467 | 0.1051 | 0.24 | 0.14 | 0.0146 | – | – | – | – |
| `openml_sonar` | class_weight balanced -> null | 0.0008 ± 0.0014 | no | 0.0039 | 0.0000 | 0.0033 | 1.00 | 0.41 | 0.0003 | – | – | – | – |
| `openml_blood_transfusion` | C 0.15 -> 0.075 | 0.0006 ± 0.0010 | no | 0.0027 | 0.0000 | 0.0037 | 1.00 | 0.42 | 0.0002 | – | – | – | – |
| `openml_blood_transfusion` | C 0.15 -> 0.3 | -0.0004 ± 0.0007 | no | 0.0018 | 0.0000 | 0.0019 | 1.00 | 0.42 | 0.0002 | – | – | – | – |
| `openml_blood_transfusion` | model_type logistic_regression -> random_forest | -0.0260 ± 0.0087 | yes | 0.0240 | 0.0060 | 0.0338 | 0.91 | 0.14 | 0.0036 | – | – | – | – |
| `openml_blood_transfusion` | model_type logistic_regression -> gradient_boosting | -0.0664 ± 0.0163 | yes | 0.0446 | 0.0042 | 0.0439 | 0.76 | 0.07 | 0.0045 | – | – | – | – |
| `openml_blood_transfusion` | class_weight balanced -> null | 0.0004 ± 0.0011 | no | 0.0030 | 0.0000 | 0.0017 | 1.00 | 0.45 | 0.0002 | – | – | – | – |
| `openml_qsar_biodeg` | C 0.15 -> 0.075 | -0.0017 ± 0.0008 | no | 0.0023 | 0.0000 | 0.0021 | 0.99 | 0.23 | 0.0004 | – | – | – | – |
| `openml_qsar_biodeg` | C 0.15 -> 0.3 | 0.0010 ± 0.0007 | no | 0.0020 | 0.0000 | 0.0026 | 0.99 | 0.30 | 0.0003 | – | – | – | – |
| `openml_qsar_biodeg` | model_type logistic_regression -> random_forest | -0.0029 ± 0.0055 | no | 0.0151 | 0.0042 | 0.0159 | 0.68 | 0.42 | 0.0012 | – | – | – | – |
| `openml_qsar_biodeg` | model_type logistic_regression -> gradient_boosting | -0.0005 ± 0.0061 | no | 0.0166 | 0.0026 | 0.0147 | 0.64 | 0.49 | 0.0002 | – | – | – | – |
| `openml_qsar_biodeg` | class_weight balanced -> null | 0.0005 ± 0.0005 | no | 0.0015 | 0.0000 | 0.0020 | 1.00 | 0.37 | 0.0002 | – | – | – | – |

### Table 5 — node level: 12 Oct E1 (10 seeds) vs. this run, for the six nodes E1 measured

| Node | data | seeds | σ_train | σ_split | σ_joint | median sd(Δ̂) | δ_n | material / resolved / all | mean P(wrong), material | effect criteria of the rule met (at the n shown) |
|---|---|---|---|---|---|---|---|---|---|---|
| `digits_mlp` | 12 Oct E1 (Py 3.11, sklearn unrecorded) | 10 | 0.0063 | 0.0075 | 0.0125 | 0.0075 | 0.0020 | 5 / 5 / 5 | 0.156 | yes |
| `digits_mlp` | this run, seeds 1–10 (= E1's seeds) | 10 | 0.0063 | 0.0075 | 0.0125 | 0.0075 | 0.0020 | 5 / 5 / 5 | 0.156 | yes |
| `digits_mlp` | this run, seeds 11–30 (independent) | 20 | 0.0072 | 0.0074 | 0.0088 | 0.0063 | 0.0020 | 5 / 5 / 5 | 0.076 | no |
| `digits_mlp` | this run, all 30 seeds | 30 | 0.0068 | 0.0073 | 0.0102 | 0.0066 | 0.0020 | 5 / 5 / 5 | 0.101 | yes |
| `tabular_mlp` | 12 Oct E1 (Py 3.11, sklearn unrecorded) | 10 | 0.0032 | 0.0125 | 0.0153 | 0.0019 | 0.0020 | 3 / 3 / 5 | 0.103 | yes |
| `tabular_mlp` | this run, seeds 1–10 (= E1's seeds) | 10 | 0.0032 | 0.0125 | 0.0153 | 0.0019 | 0.0020 | 3 / 3 / 5 | 0.103 | yes |
| `tabular_mlp` | this run, seeds 11–30 (independent) | 20 | 0.0028 | 0.0125 | 0.0105 | 0.0020 | 0.0020 | 3 / 3 / 5 | 0.140 | yes |
| `tabular_mlp` | this run, all 30 seeds | 30 | 0.0029 | 0.0123 | 0.0121 | 0.0019 | 0.0020 | 3 / 3 / 5 | 0.125 | yes |
| `openml_breast_w` | 12 Oct E1 (Py 3.11, sklearn unrecorded) | 10 | 0.0000 | 0.0049 | 0.0030 | 0.0005 | 0.0020 | 2 / 2 / 5 | 0.162 | yes |
| `openml_breast_w` | this run, seeds 1–10 (= E1's seeds) | 10 | 0.0000 | 0.0049 | 0.0030 | 0.0005 | 0.0020 | 2 / 2 / 5 | 0.162 | yes |
| `openml_breast_w` | this run, seeds 11–30 (independent) | 20 | 0.0000 | 0.0051 | 0.0042 | 0.0008 | 0.0020 | 2 / 2 / 5 | 0.244 | yes |
| `openml_breast_w` | this run, all 30 seeds | 30 | 0.0000 | 0.0050 | 0.0038 | 0.0007 | 0.0020 | 2 / 2 / 5 | 0.233 | yes |
| `openml_ionosphere` | 12 Oct E1 (Py 3.11, sklearn unrecorded) | 10 | 0.0000 | 0.0367 | 0.0437 | 0.0162 | 0.0040 | 2 / 2 / 5 | 0.160 | yes |
| `openml_ionosphere` | this run, seeds 1–10 (= E1's seeds) | 10 | 0.0000 | 0.0367 | 0.0437 | 0.0162 | 0.0040 | 2 / 2 / 5 | 0.160 | yes |
| `openml_ionosphere` | this run, seeds 11–30 (independent) | 20 | 0.0000 | 0.0539 | 0.0403 | 0.0163 | 0.0041 | 2 / 2 / 5 | 0.214 | yes |
| `openml_ionosphere` | this run, all 30 seeds | 30 | 0.0000 | 0.0485 | 0.0410 | 0.0160 | 0.0040 | 2 / 2 / 5 | 0.195 | yes |
| `openml_wdbc` | 12 Oct E1 (Py 3.11, sklearn unrecorded) | 10 | 0.0000 | 0.0068 | 0.0080 | 0.0009 | 0.0020 | 2 / 2 / 5 | 0.160 | yes |
| `openml_wdbc` | this run, seeds 1–10 (= E1's seeds) | 10 | 0.0000 | 0.0068 | 0.0080 | 0.0009 | 0.0020 | 2 / 2 / 5 | 0.160 | yes |
| `openml_wdbc` | this run, seeds 11–30 (independent) | 20 | 0.0000 | 0.0057 | 0.0080 | 0.0006 | 0.0020 | 2 / 4 / 5 | 0.182 | yes |
| `openml_wdbc` | this run, all 30 seeds | 30 | 0.0000 | 0.0061 | 0.0079 | 0.0007 | 0.0020 | 2 / 4 / 5 | 0.174 | yes |
| `openml_credit_approval` | 12 Oct E1 (Py 3.11, sklearn unrecorded) | 10 | 0.0000 | 0.0080 | 0.0169 | 0.0031 | 0.0020 | 2 / 3 / 5 | 0.092 | no |
| `openml_credit_approval` | this run, seeds 1–10 (= E1's seeds) | 10 | 0.0000 | 0.0080 | 0.0169 | 0.0031 | 0.0020 | 2 / 3 / 5 | 0.092 | no |
| `openml_credit_approval` | this run, seeds 11–30 (independent) | 20 | 0.0000 | 0.0195 | 0.0323 | 0.0034 | 0.0020 | 2 / 2 / 5 | 0.192 | yes |
| `openml_credit_approval` | this run, all 30 seeds | 30 | 0.0000 | 0.0176 | 0.0279 | 0.0030 | 0.0020 | 2 / 3 / 5 | 0.229 | yes |

Only the 30-seed row is a verdict under the adopted rule; the 10- and 20-seed rows show the same criteria at other n for comparison.

### Table 6 — `openml_credit_approval`: 22 Oct re-measurement (sklearn 1.9.1) vs. this run (sklearn 1.8.0), same 30 seeds

| data | σ_split | σ_joint | median sd(Δ̂) | material / resolved / all | mean P(wrong), material | effect criteria met |
|---|---|---|---|---|---|---|
| 22 Oct re-measurement (venv313: sklearn 1.9.1, numpy 2.5.4) | 0.0176 | 0.0279 | 0.0030 | 2 / 3 / 5 | 0.239 | yes |
| this run (hvenv: sklearn 1.8.0, numpy 2.4.4) | 0.0176 | 0.0279 | 0.0030 | 2 / 3 / 5 | 0.229 | yes |

| Edit | Δ̂_J ± 2se, 22 Oct | Δ̂_J ± 2se, this run | sd(Δ̂) joint, 22 Oct → this run | P(wrong), 22 Oct → this run | material, 22 Oct → this run |
|---|---|---|---|---|---|
| C 0.15 -> 0.075 | -0.0020 ± 0.0010 | -0.0020 ± 0.0010 | 0.0027 → 0.0027 | 0.24 → 0.24 | no → no |
| C 0.15 -> 0.3 | 0.0006 ± 0.0011 | 0.0006 ± 0.0011 | 0.0030 → 0.0030 | 0.43 → 0.43 | no → no |
| model_type logistic_regression -> random_forest | 0.0123 ± 0.0047 | 0.0130 ± 0.0048 | 0.0129 → 0.0130 | 0.17 → 0.16 | yes → yes |
| model_type logistic_regression -> gradient_boosting | 0.0082 ± 0.0059 | 0.0085 ± 0.0059 | 0.0162 → 0.0162 | 0.31 → 0.30 | yes → yes |
| class_weight balanced -> null | 0.0002 ± 0.0003 | 0.0002 ± 0.0003 | 0.0008 → 0.0008 | 0.42 → 0.42 | no → no |

### Table 7 — bit-reproducibility of earlier runs at identical node, config, condition and seeds

c0–c2 and c5 are the logistic-regression / small-edit configs on OpenML nodes; c3 = random forest, c4 = gradient boosting.

| Node:config | vs 12 Oct E1: identical | different | vs 22 Oct re-measurement: identical | different |
|---|---|---|---|---|
| `digits_mlp:c0` | 32 | 0 | – | – |
| `digits_mlp:c1` | 32 | 0 | – | – |
| `digits_mlp:c2` | 32 | 0 | – | – |
| `digits_mlp:c3` | 32 | 0 | – | – |
| `digits_mlp:c4` | 32 | 0 | – | – |
| `digits_mlp:c5` | 32 | 0 | – | – |
| `openml_breast_w:c0` | 32 | 0 | – | – |
| `openml_breast_w:c1` | 32 | 0 | – | – |
| `openml_breast_w:c2` | 32 | 0 | – | – |
| `openml_breast_w:c3` | 32 | 0 | – | – |
| `openml_breast_w:c4` | 32 | 0 | – | – |
| `openml_breast_w:c5` | 32 | 0 | – | – |
| `openml_credit_approval:c0` | 32 | 0 | 92 | 0 |
| `openml_credit_approval:c1` | 32 | 0 | 92 | 0 |
| `openml_credit_approval:c2` | 32 | 0 | 92 | 0 |
| `openml_credit_approval:c3` | 32 | 0 | 2 | 90 |
| `openml_credit_approval:c4` | 32 | 0 | 8 | 84 |
| `openml_credit_approval:c5` | 32 | 0 | 92 | 0 |
| `openml_ionosphere:c0` | 32 | 0 | – | – |
| `openml_ionosphere:c1` | 32 | 0 | – | – |
| `openml_ionosphere:c2` | 32 | 0 | – | – |
| `openml_ionosphere:c3` | 32 | 0 | – | – |
| `openml_ionosphere:c4` | 32 | 0 | – | – |
| `openml_ionosphere:c5` | 32 | 0 | – | – |
| `openml_wdbc:c0` | 32 | 0 | – | – |
| `openml_wdbc:c1` | 32 | 0 | – | – |
| `openml_wdbc:c2` | 32 | 0 | – | – |
| `openml_wdbc:c3` | 32 | 0 | – | – |
| `openml_wdbc:c4` | 32 | 0 | – | – |
| `openml_wdbc:c5` | 32 | 0 | – | – |
| `tabular_mlp:c0` | 32 | 0 | – | – |
| `tabular_mlp:c1` | 32 | 0 | – | – |
| `tabular_mlp:c2` | 32 | 0 | – | – |
| `tabular_mlp:c3` | 32 | 0 | – | – |
| `tabular_mlp:c4` | 32 | 0 | – | – |
| `tabular_mlp:c5` | 32 | 0 | – | – |

### Table 8 — noise-node pool under the adopted rule

| | nodes | count |
|---|---|---|
| qualify | `digits_mlp`, `tabular_mlp`, `openml_breast_w`, `openml_ionosphere`, `openml_wdbc`, `openml_credit_approval`, `openml_sonar`, `openml_blood_transfusion` | 8 |
| do not qualify | `openml_credit_g`, `openml_qsar_biodeg` | 2 |
| PLAN target | ≥ 8 | met |

## Reading

### Pool count: 8 qualifying nodes, which meets the PLAN target of ≥ 8 exactly, with no margin

| Group | Nodes | Count |
|---|---|---|
| Qualify | `digits_mlp`, `tabular_mlp`, `openml_breast_w`, `openml_ionosphere`, `openml_wdbc`, `openml_credit_approval`, `openml_sonar`, `openml_blood_transfusion` | 8 |
| Do not qualify | `openml_credit_g`, `openml_qsar_biodeg` | 2 |

- All five 18 Oct D21 nodes pass the uniform re-measurement, and `credit_approval` passes its re-check.
- Two of the four candidates pass: `sonar` and `blood_transfusion`.
- Under PLAN "D21 uniform application", the two failing nodes do not count towards the target and do not enter the C3 gate. They may remain engineering nodes.

### Two qualifying nodes sit on the 0.10 threshold

| Node | mean P(wrong), material | bootstrap P(qualifies) |
|---|---|---|
| `digits_mlp` | 0.101 | 0.48 |
| `openml_blood_transfusion` | 0.103 | 0.48 |

- Both pass the rule as written. Per PLAN, the bootstrap is reported but not decisive, so the verdict stands.
- **The pool's eighth place rests on these two margins.**
  - Summed over the ten nodes, the bootstrap probabilities give an expected 7.1 qualifying nodes per resample.
  - The author should know this before the pool is used for leave-one-node-out. It is not a reason to change any verdict: PLAN says "No exception after the results are seen".
- Every other qualifying node has a bootstrap P(qualifies) of 0.75 or higher, and four of them have 0.92 or higher.

### Node by node

- **`digits_mlp` qualifies, at the edge.**
  - All 5 edits are material and well resolved; for example, HIDDEN_UNITS 32 → 16 has Δ̂_J = −0.0159 ± 0.0040.
  - Precisely because the edits are well resolved, the plug-in P(wrong) is low: 0.07–0.14, mean 0.101.
  - The 12 Oct E1 gave 0.156 on seeds 1–10, which this run reproduces exactly. The 20 independent seeds 11–30 alone give 0.076.
  - The effects changed little, but the 10-seed paired sds were larger (median sd(Δ̂) 0.0075 → 0.0066). That is ordinary sampling variation at n = 10, not a version effect: the runs are bit-identical.
  - The bootstrap shows #material = 5 in every resample. Only the mean-P(wrong) criterion is at risk.
- **`tabular_mlp` qualifies** (3 material edits, mean 0.125, bootstrap 0.75).
  - At 10 seeds it was borderline (0.103); at 30 it is a little clearer.
  - The two ALPHA edits are no-ops in effect: |Δ̂_J| < 0.0001.
- **`openml_breast_w`, `openml_ionosphere`, `openml_wdbc` qualify clearly**, with means 0.17–0.23 and bootstrap 0.92–0.99.
  - On each, the two model-type switches are the material edits, as at 10 seeds.
  - `ionosphere`'s gradient-boosting switch is again wrong at the campaign's default seeds: Δ̂_J = +0.0255 ± 0.0164, but the campaign Δ̂ is −0.0139.
- **`openml_credit_approval` qualifies again** (mean 0.229, bootstrap 0.90).
  - The 22 Oct re-measurement (scikit-learn 1.9.1) gave 0.239. The two random-forest / gradient-boosting Δ̂_J moved by +0.0007 and +0.0003 with the library version (Table 6). The logistic-regression edits are identical.
- **`openml_sonar` qualifies clearly**: 4 material edits, mean 0.196, bootstrap 1.00.
  - It is the only OpenML node where the C edits are material: C ×0.5 gives +0.0062 ± 0.0041 and C ×2 gives −0.0087 ± 0.0047. Its 208 rows make the logistic-regression fit sensitive to regularisation.
  - It has the largest noise in the pool: σ_split = 0.060, and the gradient-boosting switch has a paired sd of 0.096.
  - Its tree switches carry the largest training-seed noise among the OpenML nodes: sd_train is 0.021 (random forest) and 0.047 (gradient boosting), against ≤ 0.0083 elsewhere.
  - Its δ_n is 0.0032.
- **`openml_blood_transfusion` qualifies, at the edge** (mean 0.103, bootstrap 0.48).
  - Only the two model-type switches are material, and both are large and negative: random forest −0.0260 ± 0.0087 (P(wrong) 0.14), gradient boosting −0.0664 ± 0.0163 (0.07).
  - With four features, the C and `class_weight` edits move J by ≤ 0.0006.
- **`openml_credit_g` does not qualify:** 1 material edit (gradient boosting, −0.0150 ± 0.0101, P(wrong) 0.29).
  - The random-forest switch is unresolved (−0.0029 ± 0.0074).
  - **Materiality edge:** C ×0.5 is resolved, with Δ̂_J = +0.00195 ± 0.00138. That is 0.00005 below the 0.002 bar.
  - Counting that edit would give 2 material edits with a mean P(wrong) near 0.30. This is reported for transparency only; under the adopted rule the edit is not material and the verdict is "does not qualify".
  - The bootstrap (0.52) reflects this edge.
- **`openml_qsar_biodeg` does not qualify:** 0 material edits, bootstrap 0.10.
  - The two C edits are resolved but below 0.002 (−0.0017 and +0.0010).
  - Both model-type switches are near zero and unresolved (−0.0029 ± 0.0055, −0.0005 ± 0.0061).
  - The noise is real (σ_split = 0.022, paired sd 0.015–0.017 on the tree switches), but no typical edit has a resolvable, material consequence. This is the same pattern as `diabetes` on 22 Oct.

### δ_n (D18)

- δ_n = 0.002 (the floor) on eight nodes, 0.0040 on `ionosphere` and 0.0032 on `sonar`.
- PLAN's examples (≈ 0.002 on `digits_mlp`, ≈ 0.004 on `ionosphere`) are reproduced at 30 seeds.
- As noted on 22 Oct, the median over all five edits is set by the small logistic-regression edits on most OpenML nodes. The structural edits alone have paired sds of 0.005–0.096.

### Comparison with the 12 Oct E1 (Table 5)

- Bit-identity on seeds 1–10 means that every difference between E1 and this run comes from the 20 added seeds. No difference comes from the environment.
- The five 18 Oct D21 nodes keep their verdicts.
- The mean P(wrong) moves in both directions:
  - `breast_w` 0.16 → 0.23, `ionosphere` 0.16 → 0.19, `wdbc` 0.16 → 0.17, `tabular_mlp` 0.10 → 0.13;
  - `digits_mlp` 0.16 → 0.10.
- Some of the rise on the OpenML nodes is the selection cap: Φ(−2/√n) is 0.26 at n = 10 and 0.36 at n = 30.
- All ten nodes are now judged at the same n, which was the purpose of PLAN "D21 uniform application".

### Split policy (reported; PLAN already sets `"vary"` on every node)

- σ_train = 0 on all eight OpenML nodes, because logistic regression ignores the training seed.
- The training-seed share over the material edits is:
  - 0.05–0.32 on the OpenML nodes (0.00 on `qsar_biodeg`, which is measured on the baseline);
  - 0.64 on `tabular_mlp` and 0.82 on `digits_mlp`.
- E1's proposed split rule would say `fixed` for the two MLP nodes and `vary` for the rest. This does not affect the 22 Oct PLAN row.

## Caveats

- P(wrong) is a plug-in on edits selected by resolution, so it is a rough figure, not an estimate with a stated error (see the 12 Oct report's L14 caveat). Two verdicts in the pool sit within 0.004 of the threshold.
- The edits are the hand-specified "typical" E1 edits, not LLM proposals. On the eight OpenML nodes they share one template edit space; the material edits there are almost all the two model-type switches.
- **Tree-model numbers hold for scikit-learn 1.8.0.** They were bit-identical with the 12 Oct E1 but not with the 22 Oct re-measurement under 1.9.1.
  - Later campaigns on these nodes must run in the same locked environment, or re-measure.
  - Whether a version change would flip a verdict was not tested, except on `credit_approval`, where it did not flip.
- **After merging, this run directory becomes the newest `E1_[0-9]*T*Z` run.** `r1/headroom/e1b_collect.py` uses that pattern to pick its default E1 summary when `--e1-summary` is not given. `r1/c3/dataset.py` (`E1_SUMMARY`) is unchanged.
