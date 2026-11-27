# Screening smoke repeat after the content-based ARFF fix (task `compute/20261127-14`)

**Result: PASS.** A clean `origin/main` checkout on deepthought wrote **168/168** engineering-smoke runs with
`failed_runs = 0` and `stop = null`; `failed_runs.jsonl` is absent. ENGINEERING ONLY: this is not the evidence run,
which still waits for the author's signed screening note.

- **Base:** `origin/main` `e153df24ee3435bbe0b2fa994297b15250550c30` (contains the ARFF content fix `03a352d9`)
- **Branch:** `compute-screen-smoke-repeat-20261127`
- **Host:** deepthought, Python 3.13.15, scikit-learn 1.8.0; harness `6adf3859de66c4814fcf376eed59880fbd8eeaf7`
  (clean), paper checkout clean at the base.
- **Cache (new, kept for the evidence run):** `/work/dwong/screen_prep_20261126/data_cache_ENG_20261127T0417Z`
  - `tree_sha256`: `c0c2a3645f3fbcbeed6374e7f1a1b717421ec39985cb875bdc1e4a44f6a9781b`
  - `MANIFEST.json` sha256: `74e688e754346d177cbafbe7e19b4bd984839d37c7808600f20c011602bcbd62`
  - six nodes, 463 KiB, one manifest; the 26 Nov STOP directory
    `..._STOP_arff_suffix` was not touched.
- **Smoke output:** `/work/dwong/screen_prep_20261126/smoke_ENG_20261127T0417Z`
  - `manifest.json` `planned_runs = written_runs = 168`, `failed_runs = 0`, `stop = null`,
    `elapsed_seconds = 48.5`, `finished_utc = 20261127T031457Z`
  - `identity_flags`: 37 entries (recorded in the manifest); `edit_sets` equal for all eight decision nodes
  - `failed_runs.jsonl` absent
- **Co-tenancy:** 40 CPUs, 33.5 free for others, load1 6.5, `ok: true`, our workers 0 at the check
  (`captures/cotenancy.log`).

## Captures

| File | sha256 |
|---|---|
| `captures/smoke_manifest.json` | `20748f42e5792a78d49abb8249c9a8f85c37116067169031c01be99b9b14ddc7` |
| `captures/data_cache_MANIFEST.json` | `74e688e754346d177cbafbe7e19b4bd984839d37c7808600f20c011602bcbd62` |
| `captures/design.json` | `29396f5bb4dee22a0937b7587c7a5708a75570706075284bbfb9f4721f8085d0` |
| `captures/cotenancy.log` | `fe1d450e9e166e1e8c15c0ee8e28ab2754bf559813be14ff1f318189043c0c50` |
| `captures/data_cache.log` | `a2ba90cb2f756106fb11519fe44b1669147d307873e5ea51df6614380fc9b262` |
| `captures/smoke.log` | `137574df9ebfcf5f7837e2372b053c171c34f0dde50a0c70b7c60d56c2281ddf` |
| `captures/SHA256SUMS` | `0d7ad146570f037e6f5ba644645fe7b51c8c90b56a3435ec884227c6ae54a1ec` |

## What was run

```
cd /work/dwong/screen-smoke-20261127/paper          # git checkout --detach e153df24; status clean
AR_HARNESS_ROOT=/work/dwong/screen-smoke-20261127/harness \
  /work/dwong/screen-smoke-20261127/venv/bin/python -m pytest -q r1/tests/test_screen_measure.py
  # 82 passed
python -B -m r1.noise.screen_measure data-cache --out <new cache> --tmp <new tmp>
python -B -m r1.noise.screen_measure run --engineering-smoke --out <new smoke> --workers 16 \
  --tmp <new tmp> --data-cache <new cache>
```

**Decided alone:** to reuse the existing clean paper checkout and the Python 3.13.15/sklearn 1.8.0 venv from the
27 Nov STOP (reset to `origin/main`, status checked), and to keep the new cache directory for the evidence run.
No host setting, checkout, reviewed driver or STOP scene was edited.

**Needs:** a fresh review of this record; the coordinator may then treat the screening smoke condition as met.
The evidence run still waits for the signed screening note.
