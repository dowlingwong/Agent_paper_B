# STOP report — screening smoke `data-cache` (task `compute/20261127-07`)

for: local (the test owner)

**Task:** `compute/20261127-07` (= `compute/20261126-08`). **Result: STOP at the first step, `data-cache`.** No
engineering smoke ran; no 168-run record exists. The scene is kept, moved aside, and not edited.

- **Branch (captures + record):** `compute-screen-smoke-stop-20261127`
- **Tip:** `33767535b39d2962d37ea75164b37f609a7d4b9e`
- **Base:** `origin/main` `bd406db9`
- **Checkouts:** paper `bd406db9` clean; harness `6adf3859` clean; Python 3.13.15, scikit-learn 1.8.0 (the harness
  `uv.lock` `dd42d018…`, `uv sync --frozen --extra dev`)
- **Pre-step tests:** `r1/tests/test_screen_measure.py` **78 passed** (11.06 s)

## STOP

```
STOP: openml_breast_w's cache holds 0 ARFF files, not one
```

The cache-building trial succeeded and downloaded the correct data: `…/download/52350.gz`, whose decompressed
content is ARFF and whose decompressed sha256 is
`cb44e7f62f4a962881147264e5f985eacc13256712e7a4b9d1731ced05f3ee9b` — exactly
`PILOT_ARFF_SHA256["openml_breast_w"]`.

The defect is the file-name classification. `check_pilot` (paper `bd406db9`, `r1/noise/screen_measure.py`
lines 233–238) counts a file as the ARFF only when its path ends `.arff.gz` or `.arff`. Under the pinned
scikit-learn 1.8.0, `fetch_openml` stores the download as `<id>.gz` (`52350.gz`), so the correct dataset is
classified as zero ARFF files. The 26 Nov smoke used scikit-learn 1.5.1.

## Scene and captures

- Partial cache moved aside: `/work/dwong/screen_prep_20261126/data_cache_ENG_20261127T004046Z_STOP_arff_suffix`
  (no manifest written; not edited).
- Record: `docs/r1/reports/screen_smoke_20261127/SCREEN_SMOKE_DATACACHE_STOP_20261127.md`; captures under
  `docs/r1/reports/screen_smoke_20261127/captures/` (sha256 in the record).
- Environment/scene file: `/work/dwong/screen-smoke-20261127/` (paper, harness, venv outside both checkouts).

## What is needed

A local-worker code/test fix: identify the ARFF by content (the gzip whose decompressed bytes begin with an ARFF
header, or whose decompressed sha256 is in `PILOT_ARFF_SHA256`) rather than by suffix; add the `<id>.gz` layout to
`test_screen_measure.py`. Then the cache build and the engineering smoke can run. Nothing was edited here.

**Decided alone:** to STOP at the cache build and keep the scene rather than edit the reviewed fix or force the
26 Nov environment; the data itself is proven correct, so the fix is a narrow file-identification change.
