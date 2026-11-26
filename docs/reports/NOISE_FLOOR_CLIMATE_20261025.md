# Climate reserve noise floor — 25 October 2026

AI-assisted by GPT-6 (Codex). **PILOT, not evidence.** This measures the prespecified reserve node; it is not D28 LLM liveness, a C3 gate verdict, or sweep authorization.

## Verdict: qualifies under the adopted D21 rule

The complete fresh attempt contains **552 unique run records, zero failures and zero missing/non-finite metrics**. Every configuration has 30 training-seed, 30 split-seed and 30 joint-seed runs, plus two fixed-default-seed runs. All six configurations' default/repeat metrics match exactly. The result was checked both through the existing E1 summarizer and the common run's independent adopted-rule implementation; they agree.

| D21 condition (PLAN section 10, 22 October) | Observed | Verdict |
|---|---|---|
| 30 seeds per condition on every configuration | 30 / 30 / 30 | pass |
| At least two resolved, material edits | **3** of 5 | pass |
| Mean plug-in P(wrong) over material edits ≥ 0.10 | **0.2907157594** | pass |
| Baseline σ_joint > 0 | **0.0399363099** | pass |

**δ_n = 0.0050897867**, using D18's unchanged `max(0.002, 0.25 × median paired sd)`; median paired sd = 0.0203591469. Baseline σ_split = 0.0665984723; σ_train = 2.26e-16 (numerically near zero). The paired joint-seed bootstrap gives P(qualifies) = **0.9055** over 2,000 resamples, seed 20261022. As declared in PLAN, this bootstrap is reported and is **not** part of the verdict.

| Standard E1 edit | Mean joint paired Δ ± 2 se | Material | Plug-in P(wrong) |
|---|---|---|---|
| `C 0.15 -> 0.075` | 0.0026383 ± 0.0019980 | yes | 0.3148 |
| `C 0.15 -> 0.3` | -0.0029602 ± 0.0019303 | yes | 0.2878 |
| `model_type logistic_regression -> random_forest` | 0.0101672 ± 0.0178993 | no | 0.4178 |
| `model_type logistic_regression -> gradient_boosting` | -0.0487452 ± 0.0289814 | yes | 0.2696 |
| `class_weight balanced -> null` | -0.0008366 ± 0.0074341 | no | 0.4836 |

Material means resolved `|Δ| > 2 se` and `|Δ| ≥ 0.002`, exactly as adopted. The unresolved random-forest switch and class-weight edit are not included in the mean P(wrong) used by the rule. No threshold, edit set, seeds, node, or proposer was changed after seeing outcomes.

## Inputs and execution

`openml_climate` is OpenML 1467, `climate-model-simulation-crashes`. The node's cached loader was checked with network disabled: **540 rows × 20 features**, no missing values or categorical columns, class counts `1: 46`, `2: 494`, minority share 46/540 = 0.085185…, positive label `2`. These match existing NODE_INFO and the node's D25 declaration; no metadata correction was necessary.

Host: `deepthought.etp.kit.edu`, x86_64, 40 CPUs. Paper source: `3d3ec488be5e1cdcb12ee66b8130305fc9c7db26`, tracked-clean. Harness preparation snapshot: `7305434c7506512fca741c91751936fbd099fd81`, tracked-clean; this adds the reserve adapter to the common run's `4012897` and does not change that run's noise protocol. The final sweep pin remains deferred, as explained in [the preparation report](DT_PREPARATION_20261025.md).

Environment: **Python 3.13.15**, scikit-learn **1.8.0**, NumPy **2.4.4**, pandas **3.0.3**, SciPy **1.17.1**. The common manifest records Python 3.13.16, which this host's uv cannot download. The runbook's Python 3.13 requirement is met and all four locked metric-library versions match; the Python patch and architecture differ from the reference. No exact cross-platform/reference bit-reproduction claim is made. Every row of this attempt used one interpreter. `OMP_NUM_THREADS=1` and `OPENBLAS_NUM_THREADS=1` match the reference; `MKL_NUM_THREADS=1` was also set. GPU visibility was disabled. No LLM call was used.

The complete attempt used the existing command with unchanged scientific parameters:

```sh
python -m r1.noise.e1_noise_floor --nodes openml_climate --seeds 30 --workers 4 \
  --out /tmp/r1_prepare_dwong_20261025/E1_CLIMATE_DT_attempt02 \
  --tmp /tmp/r1_prepare_dwong_20261025/climate_work02
python -m r1.noise.e1_report /tmp/r1_prepare_dwong_20261025/E1_CLIMATE_DT_attempt02
```

It ran in tmux `r1_climate02_20261025`, with output teed to a local scratch log. Manifest start: **2026-10-25 00:47:47 UTC**; finish: **00:51:35 UTC**. One session, 552 written, zero remaining, **228.4 s** elapsed; median worker-reported time 1.5238 s/run. Timings are under concurrent engineering load, as in the reference manifest, and are not isolated performance measurements.

The [existing E1 summarizer](../../../r1/noise/e1_report.py) supplies the per-edit statistics. The [common-run table builder](../../../results/r1/pilot/E1_20261022T214606Z/make_tables.py) supplies `seed_counts`, `d21_adopted`, the independent raw-joint-difference rule, D18 δ_n and paired bootstrap. Additional file-only checks enforce exactly 552 unique keys, successful finite metrics, every configuration's seed counts, clean pinned source, locked metric-library versions, and all six deterministic pairs.

## Earlier attempt: STOPPED / PARTIAL, preserved and excluded

The first attempt wrote **348 records** under `/ceph/dwong/r1_prepare_20261025/agent_paper_B/results/r1/pilot/E1_CLIMATE_DT_20261025/`, then a worker failed creating its temporary directory with `OSError: [Errno 122] Disk quota exceeded`. The wrapper could not create its exit marker for the same reason. E1 writes its manifest at normal completion, so that stopped directory has **no manifest**. It is not a complete E1 run and supports no D21 verdict.

The file-count quota was diagnosed independently of outcomes; the exact counters and bounded task-cache cleanup are in the preparation report. The original partial files were not modified, patched, resumed, deleted or merged. A fresh full attempt was run on the same host with the same source, environment, data, edit set, 30-seed sets and four workers, changing only output/scratch storage. Only that fresh 552-row attempt supplies the verdict above. The repeated computation across attempts is disclosed; these attempts are not independent replications.

Original partial `runs.jsonl` SHA-256: `d3173f1085d813d5b3bea8436792c965735ec2dd85c481538250425a72b86455` (71,260 bytes). Its `edits.json` hash equals the complete attempt's edit-set hash below.

## Retained complete artifacts

Host output: `/tmp/r1_prepare_dwong_20261025/E1_CLIMATE_DT_attempt02/`. A durable local copy of all six text artifacts, verified against the original hashes, is at:

`/Users/wongdowling/Documents/agent_paper_B/results/r1/pilot/E1_CLIMATE_DT_20261025_ATTEMPT02/`

| Artifact | SHA-256 |
|---|---|
| `runs.jsonl` | `eefea223059a242da502260ab5e0afcdcac30dae30087745fec25f7de86d904a` |
| `edits.json` | `5331765d1a58204cb0f6b7ba0273691507d8e5dfd2739b95d863feee16e725f2` |
| `manifest.json` | `17dc832630217ff7a721ca9f7993dcdf3acaf89c23a03604f44530a6b2141248` |
| `summary.json` | `6d5f44834bc732ca89cceb4f17d85b8c191ab3fcabb47dd73d9abce3acbcb8a5` |
| `tables.md` | `cdeda3485586256e3a21ee03860cb0179745a262fffdd280c9762dd6458c469f` |

`verification.json` preserves the full accounting, binary D21 criteria, independent-rule agreement, bootstrap and hashes. Raw records remain local/on-host and are not included in the summary-only Git push. The earlier partial record remains on Ceph.

The reserve **qualifies under the adopted noise-node rule**, subject to the explicitly recorded environment difference. No sweep node was substituted, no default E1 summary was replaced, and no live-node/config/pin decision was made. Batch B and the unresolved integration checks still need resolution before later execution. **Stop before Phase 4**, as requested.
