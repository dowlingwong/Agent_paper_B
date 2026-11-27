# Screening smoke — data-cache STOP (extension classification), 27 November 2026

**Task:** `compute/20261127-07` (the repeat of `compute/20261126-08`). **Result: STOP at the first step (`data-cache`).**
No engineering smoke ran; no 168-run record exists. The scene is kept, moved aside, and not edited. ENGINEERING only.

## Scene

| Field | Value |
|---|---|
| Host | deepthought (`dwong`) |
| Paper checkout | `/work/dwong/screen-smoke-20261127/paper`, clean, `bd406db9d03f3bbdf3471431d1af96748e1f9556` |
| Harness worktree | `/work/dwong/screen-smoke-20261127/harness`, clean, `6adf3859de66c4814fcf376eed59880fbd8eeaf7` |
| Python / libraries | 3.13.15; scikit-learn 1.8.0, NumPy 2.4.4, SciPy 1.17.1, pandas 3.0.3; harness `uv.lock` `dd42d018…` (`uv sync --frozen --extra dev --python 3.13.15`) |
| Cache command | `python -B -m r1.noise.screen_measure data-cache --out /work/dwong/screen_prep_20261126/data_cache_ENG_20261127T004046Z --tmp /tmp/r1_smeas_cache_20261127T004046Z` |
| Partial cache | moved aside to `…/data_cache_ENG_20261127T004046Z_STOP_arff_suffix` (no manifest written) |
| Tests first | `r1/tests/test_screen_measure.py`: **78 passed** in 11.06 s with the pinned environment |

## STOP

```
STOP: openml_breast_w's cache holds 0 ARFF files, not one
```

The cache-building trial succeeded and downloaded the correct dataset:

* `openml_breast_w/data_cache/openml/openml.org/data/v1/download/52350.gz` (stored sha256
  `edeeb3fe…`; capture `captures/52350.gz.sha256`);
* its decompressed content is ARFF and its decompressed sha256 is
  `cb44e7f62f4a962881147264e5f985eacc13256712e7a4b9d1731ced05f3ee9b`
  (`captures/52350.gz.decompressed.sha256`, first lines in `captures/52350.gz.head.txt`), exactly
  `PILOT_ARFF_SHA256["openml_breast_w"]` in `r1/noise/screen_measure.py`.

The defect is the file-name classification, not the data. `check_pilot` (paper `bd406db9`,
`r1/noise/screen_measure.py` lines 233–238) counts a file as the ARFF only when its path ends
`.arff.gz` or `.arff`:

```python
arffs = [v["content_sha256"] for k, v in files.items() if k.endswith(".arff.gz") or k.endswith(".arff")]
if len(arffs) != 1:
    raise RunStop(f"STOP: {node}'s cache holds {len(arffs)} ARFF files, not one")
```

Under the pinned scikit-learn 1.8.0 the OpenML download is stored as `<id>.gz` (`52350.gz`), so the
correct dataset is classified as zero ARFF files. The 26 Nov smoke used scikit-learn 1.5.1; the
evidence environment pin is 1.8.0, so this path must work at 1.8.0.

## What is needed

A local-worker code/test fix (the test owner): identify the ARFF by content (the gzip whose
decompressed bytes begin with an ARFF header, or whose decompressed sha256 is in
`PILOT_ARFF_SHA256`) rather than by file-name suffix; extend `test_screen_measure.py` with the
`<id>.gz` layout. Then the cache build and the engineering smoke can run. Nothing was edited here.

## Captures

| File | sha256 |
|---|---|
| `captures/scene.txt` | `1de68a4df7dc04069ef2c54649a2e15914a441c89bc2b403c2f14fb582b1c836` |
| `captures/data_cache.log` | `d0ff4e3097ec32e95b8ffbf476bcaa677172b68c46284cc716048f60507d6867` |
| `captures/files.txt` | `e440ca14e301cf446151a630a2c9cca01a78162af4daf7ea23ba80288f00ce5e` |
| `captures/52350.gz.sha256` | `edeeb3fe177a6f99328c5e13b97afe4aa3c7508d281723c05fc5d9020cfaaf3d` |
| `captures/52350.gz.decompressed.sha256` | `ed631bac50e5baab2584eef4224efe6dc24fafa5095f509f81f93b68ee5043c3` |
| `captures/52350.gz.head.txt` | `2177bab82ba847104697d6d8d275f4ba14e8154e6fa50a85ca1b85ca2dc6bc40` |
