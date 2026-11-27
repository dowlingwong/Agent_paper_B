# D.3 G2 constants fit on the released sweep-2 train/dev rows (task `compute/20261127-17`)

**Result: PASS.** The reviewed fitter ran on deepthought from a clean detached `origin/main` checkout, wrote a new
`d3_constants.json`, and `check` re-parsed it with the same sha256. A second independent fit produced byte-identical
bytes. ENGINEERING/ANALYSIS artifact only: it reads the released sweep-2 train/dev partition, no test label, no
evaluation block and no sealed file.

- **Task:** `compute/20261127-17` (revision 4 waits for this artifact).
- **Base:** `origin/main` `bad59593460a135ddbbf83d7a8c48eb64fc8a97f`.
- **Branch:** `compute-d3-g2-constants-20261127`.
- **Checkout:** `/work/dwong/d3_g2_paper_20261127`, detached at `bad59593`, clean; the fitter commit `6cf882b0`
  (the accepted `mac-d3-g2-constants-20261127` merge) is an ancestor.
- **Fitter:** `r1/c3/d3_constants.py` sha256
  `5ad96059245bf5a65b0f462f73e74028c77fec8d7dabfa5d0e4f74d0c329b027`; `arms_constants.py`
  `fc44e71e53d7724d2f5c467ea4cb22f8010cc901ad0661829e359cd3d603c778`; `gate_input_builder.py`
  `f67ee5e753381991600e91c76f09418f783a9e56517e12ce1203fd0cb5b9f808`.
- **Toolchain:** the arms-freeze venv: Python 3.13.15, NumPy 2.4.4, SciPy 1.17.1,
  interpreter `/work/dwong/screen-smoke-20261127/venv/bin/python`.
- **Artifact:** `docs/r1/reports/d3_g2_20261127/d3_constants.json` sha256
  **`4f5f686be8f0210bcb27dfe0968296d68cf54e7266fb72c9038e741163776a93`**.

## Inputs (released train/dev only)

| Input | sha256 |
|---|---|
| receipt `RECEIPT.json` | `de95b218486e39369f5143637de904d1f73ae18c13d31a9a1aebaa4072ed2d9c` |
| train/dev partition `label_block.traindev.jsonl` | `7487b627e40edae37022f4467a60867b09bdbd395e61caa20302c090d8e5fe82` |
| table `proposals.jsonl` | `379b17ca0783571f87724fc1687d02dfb4084d7ebcec69ab296e855de02197d9` |
| table `configs.json` | `de6d63b5e06e541d97dcb2455f75c27649c6b3698e2a7ab4d7193868f1ab0f4d` |
| table `build.json` | `bbb2a95cef1edfb1e3767eb66b841c54626235b1e3b719529e4b53f37d3dda92` |

Release root `/work/dwong/s2_release_20261122/release_sweep2_traindev_v2`; table
`/work/dwong/s2_audit_20261122/table`. The receipt's `counts` are train 850, dev 422, test 1,228 (released label
rows 1,272, evaluation rows 0); the fit filters to the seven D.3 nodes' P3 dev instances and uses only rows whose
source hashes match. The fitter's input checks passed (rc 0); no refusal/STOP.

## Fit output

```
python -B -m r1.c3.d3_constants fit --release-root <release> --receipt de95b218… --table <table> --out <cap>/d3_constants.json
python -B -m r1.c3.d3_constants check <cap>/d3_constants.json
4f5f686be8f0210bcb27dfe0968296d68cf54e7266fb72c9038e741163776a93  <cap>/d3_constants.json
```

`fit` stdout (full capture in `captures/fit.stdout`):
- `code_commit`: `bad59593460a135ddbbf83d7a8c48eb64fc8a97f`; `fills`:
  `D3_PREDECLARATION_DRAFT_20261122.md §14 constants_file_sha256`.
- LADDER c per node: `digits_mlp -1.3`, `openml_breast_w 0.3`, `openml_climate 2.85`,
  `openml_credit_approval -0.1`, `openml_ionosphere -0.05`, `openml_sonar -0.75`, `tabular_mlp -0.8`.
- `check` (captures/check.stdout) re-parses the file and prints the same sha256; `check.stderr` and `fit.stderr` are
  empty.

**Determinism:** a second fit from the same clean checkout and inputs wrote a byte-identical file
(`cmp` rc 0; `captures/repeat_fit.stdout` prints the same `4f5f686b…` sha256).

## Captures

`captures/SHA256SUMS` covers `fit.stdout`, `fit.stderr`, `check.stdout`, `check.stderr`, `sha256.txt` and
`repeat_fit.stdout`; the artifact hash is in the record and in the report's outer `SHA256SUMS`.

## What remains

A fresh tier-E review must re-run `check`, confirm the inputs are the receipted release, and accept the artifact
before the coordinator fills §14 `constants_file_sha256` in revision 4 (`local/20261127-08`). No test partition,
evaluation value, label value beyond the released train/dev rows, or sealed file was read.

**Decided alone:** to use the clean detached worktree rather than the screening checkout for the fit; to use the
arms-freeze venv (it matches the recorded 3.13.15 / 2.4.4 / 1.17.1 toolchain); to run the fit twice and require
byte identity before reporting; to keep the capture directory and both fit stdout files.
