# Sweep-2 runtime-error diagnosis (R1-SWEEP2-RTE-DIAG), 21 November 2026

**ENGINEERING_ONLY. Labels remain sealed (R1-BX-D8-CONFIRM).** The four sealed chunk directories were not modified;
all replays ran on copies under `/tmp/rte_diag/`.

- run: `s2ev-20261119-a`, launch commit `4aac5209`, chunks sealed under `/ceph/srv/dwong/paperb/sweep2/s2ev-20261119-a/`.
- worker input reconstructed from each sealed `work.tar` (`roots/<campaign>/node`, including `config.yaml`, `data_cache`)
  plus the trial `art/trial-NNN/patch.diff`; harness `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`, v1 image
  `sha256:69b06b35…`, instance/training/split seed = the campaign seed (`AR_TRAIN_SEED`=`AR_SPLIT_SEED`).
- replay environment: CPU on deepthought, e1-verified venv Python 3.13.15 (`/ceph/dwong/r1_prepare_20261025/venv`),
  `python3 train.py --config config.yaml`, no GPU. Each trial ran **twice**; stdout/stderr/exit/time/memory captured.

## Results (all six classified (i): deterministic, proposal-induced)

| trial | seed | applied config value | exception (twice) | exit | wall / maxRSS | sealed chunk record sha256 |
|---|---|---|---|---|---|---|
| `openml_breast_w__s145` t16 | 145 | `class_weight: {0` | `yaml.parser.ParserError`: flow mapping; expected `,` or `}`, got `:` at `class_weight: {0` | 1 / 1 | 2:57.87 / 135,628 kB | `67510277…f4415` |
| `openml_breast_w__s155` t19 | 155 | `max_depth: null` | `TypeError: float() argument must be a string or a real number, not 'NoneType'` at `benchmark.py:164 _load_config` | 1 / 1 | 0:01.97 / 135,852 kB | `67510277…f4415` |
| `openml_climate__s264` t19 | 264 | `class_weight: {1` | `yaml.parser.ParserError`: flow mapping at `class_weight: {1` | 1 / 1 | 0:02.00 / 135,844 kB | `3b49670e…80c9c` |
| `openml_climate__s264` t20 | 264 | `class_weight: {1` | `yaml.parser.ParserError`: flow mapping at `class_weight: {1` | 1 / 1 | 0:01.91 / 133,876 kB | `3b49670e…80c9c` |
| `openml_credit_approval__s200` t11 | 200 | `class_weight: {0` | `yaml.parser.ParserError`: flow mapping at `class_weight: {0` | 1 / 1 | 0:01.85 / 133,668 kB | `65fb201f…29ab4` |
| `openml_wdbc__s150` t20 | 150 | `class_weight: {0` | `yaml.parser.ParserError`: flow mapping at `class_weight: {0` | 1 / 1 | 0:01.83 / 135,520 kB | `9fcf8936…bc871` |

Full tracebacks, both run logs (`run1.*`, `run2.*`), configs and failures are in `sweep2_rte_diag_20261121/` (per-trial directories) and `summary.json`.

## Classification

Every trial is **(i) deterministic and raised by the proposed configuration values**:

- five trials applied a custom `class_weight` mapping proposal whose first value token (`{0`/`{1`) the worker wrote as the
  whole scalar, producing a malformed YAML flow mapping; the config parser raises `ParserError` before any training.
- `openml_breast_w__s155` t19 applied `max_depth: null` (remove-max_depth proposal); `_load_config` calls `float(None)` and
  raises `TypeError`. Both replays give the identical exception, exit 1 and near-instant wall time (< 3 s; the 2:57 first
  breast run includes the first OpenML cache/Sklearn import).
- No replay showed OOM (maxRSS ~133–136 MB), I/O error, signal, or environment failure; outcomes are reproducible and
  tied to the proposed edit, so they are proposal-induced failures to be treated like `invalid_config`, not STOPs.

## Evidence paths

- replay copies: `/tmp/rte_diag/<chunk>/runs/<campaign>-tNN/` on deepthought (config, patch, run1/2 out/err/rc, traceback).
- committed evidence: `docs/r1/reports/sweep2_20261116/sweep2_rte_diag_20261121/`.
- sealed originals unchanged: `/ceph/srv/dwong/paperb/sweep2/s2ev-20261119-a/`.
