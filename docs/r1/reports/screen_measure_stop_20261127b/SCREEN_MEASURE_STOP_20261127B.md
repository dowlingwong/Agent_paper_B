# STOP — screening evidence run (`compute/20261127-25`): the declared cache tree is not stable under `fetch_openml`

**Result: STOP after 30 of 10,164 runs (0 failed), at `openml_breast_w` `c3` seed 3301.** The strict
preflight passed; the scene is kept; nothing was resumed, patched or retried.

- **Task:** `compute/20261127-25`; PLAN **R1-SCREEN-MEASURE-REISSUE**. Note
  `docs/r1/authorizations/screen_measure_20261127_reissue.md` (`approved: true`, sha256
  `7c3c8313e90016fa1ff6773bd678e95e5c6ed9457b14d01631897499ee0fdeb0`) on `main` `9cd5863c`; the companion
  pre-declaration sha256 `a380dbf122f17705f29ae0d056a8eafeebe67f2718a6fca09616994c09362585`. Code
  `e153df24ee3435bbe0b2fa994297b15250550c30` (`screen_measure.py` sha256
  `5c04aeeef13afebc6dd2839737691b16b76e4485f546e9789380d6d4a575bd38`), code review
  `docs/r1/reviews/SCREEN_MEASURE_SIGNATURE_REVIEW_20261127.md`.
- **Host / environment:** deepthought, 16 workers, batch venv Python 3.13.15 (scikit-learn 1.8.0, NumPy 2.4.4,
  SciPy 1.17.1, pandas 3.0.3); harness `6adf3859de66c4814fcf376eed59880fbd8eeaf7` clean; `worker_python`
  `/ceph/dwong/r1_prepare_20261025/venv/bin/python3` (the re-issue's interpreter fix). Cotenancy at start: 40 CPUs,
  `free_for_others` 32.04, `load1` 7.96, `ok: true`.
- **Scene:** `/work/dwong/screen_measure_20261127/paper/results/r1/screen_measure/SMEAS_EVIDENCE_20261127T1155Z/`
  (kept as it is) and scratch `/tmp/r1_smeas_EVIDENCE_20261127T1155Z`. Copied verbatim into `scene/` here.
  `manifest.json` `33db59d6…`, `design.json` `29396f5b…`, `lineage_runs.jsonl` 30 rows `a39eaa40…`,
  `failed_runs.jsonl` `b41fda81…`, `cotenancy.log` `a67842ef…`, `worker_runtime.jsonl` `e01c51dc…`;
  the launch script `c78aa242…` and console log `07debe32…` are beside them.
- **Elapsed:** 48.9 s (16 workers, CPU only; about 0.22 CPU-h). No GPU, no server, no label, evaluation, test or
  sealed file was read.

## Diagnosis (read-only)

The launched table was validated (`data_cache.tree_sha256 = c0c2a364…`, `openml_breast_w` tree
`107d25c6…`), then 30 `digits_mlp` runs wrote cleanly. At `openml_breast_w` `c3` seed 3301 the run succeeded
(`VAL_AUC=0.995974`, `VAL_ACC=0.971429`) but the after-run check found the node copy's `data_cache` changed:

```
data_cache openml_breast_w c3 3301: openml_breast_w's dataset cache changed during the run (a download or an edit)
```

The declared cache holds the download response at
`openml/openml.org/data/v1/download/52350.gz` (6753 bytes). On load, scikit-learn 1.8.0's
`fetch_openml(data_id=15, data_home=…, as_frame=True, parser="auto")` materialises the ARFF at
`openml/openml.org/data/v1/download/52350/breast-w.arff.gz` (also 6753 bytes) instead of reading the declared
file name, so `cache_tree()` sees an extra file and the M1 integrity check stops the run. This was confirmed
read-only in a `/tmp` copy of the cache with the same venv (`cache_diagnosis/`); the kept cache was not touched
(its `52350.gz` mtime stayed 2026-11-27 04:12:08 +0100). The harness's own pilot cache carries the
`52350/breast-w.arff.gz` layout; the launch-verified cache built by `data-cache` carries `52350.gz`.

The 27 Nov engineering smoke (same code and cache, seed 999, 168/168) ran `openml_breast_w` `c3` and did not
stop. Reconciling that smoke record with this confirmed load-time write is part of the decision; the evidence
run is the stricter record and it stops. I did not edit the cache, the code, the note or the smoke record.

## What is needed

This is a signed EVIDENCE run: every STOP returns to the author (the note's STOP list). The seventh-arm
decision is not reached, and the screening remains unmeasured. Possible routes (author level, because the
launch-verified cache hash, the note or the cache-integrity rule is bound):

1. rebuild/pre-warm the data cache so the declared tree contains the file `fetch_openml` writes (new cache, new
   `data_cache_sha256`, note revision); or
2. a reviewed change to the cache-integrity rule for the benign ARFF materialisation (changes what the note
   binds); or
3. another re-issue that names the route.

The D.3 pre-declaration revision 4 was frozen at `9cd5863c` before this result (the coordinator recorded the
ordering error); if the author wants a seventh D.3a arm, that freeze must be revisited. Nothing here changes
the frozen file.

## Decided alone

To stop at the first failed check (the note says so), to keep the scene and scratch unchanged, and to run only
the read-only `/tmp` cache diagnostic above; no retry, no cache edit, no code or note change.

**Task id:** `compute/20261127-25`. **Branch/tip:** `compute-screen-measure-reissue-stop-20261127` (the tip is
named in the `coord/compute` report). **Tests:** none (the run stopped at its own integrity check); the strict
preflight passed and the cache diagnostic is captured. **Next:** author/coordinator decision on the route above;
no launch until then.
