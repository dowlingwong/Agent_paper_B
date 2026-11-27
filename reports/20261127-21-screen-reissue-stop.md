# STOP — screening evidence run under the re-issued note (`compute/20261127-25`)

**Result: STOP after 30 of 10,164 runs (0 failed), at `openml_breast_w` `c3` seed 3301.** Strict preflight
passed; the scene is kept; nothing was resumed, patched or retried. Screening remains unmeasured, so the
seventh-arm decision is not reached.

- **Task:** `compute/20261127-25` (R1-SCREEN-MEASURE-REISSUE). Note
  `docs/r1/authorizations/screen_measure_20261127_reissue.md`, `approved: true`, sha256
  `7c3c8313e90016fa1ff6773bd678e95e5c6ed9457b14d01631897499ee0fdeb0`; companion pre-declaration sha256
  `a380dbf122f17705f29ae0d056a8eafeebe67f2718a6fca09616994c09362585`.
- **Code / host:** `e153df24ee3435bbe0b2fa994297b15250550c30`; deepthought, 16 workers, batch venv
  (Python 3.13.15, sklearn 1.8.0, NumPy 2.4.4, SciPy 1.17.1, pandas 3.0.3), harness
  `6adf3859de66c4814fcf376eed59880fbd8eeaf7` clean; `worker_python` `.../venv/bin/python3` (the re-issue
  interpreter fix). Cotenancy at start `ok` (32.04 cores free for others).
- **STOP:** `data_cache openml_breast_w c3 3301: openml_breast_w's dataset cache changed during the run
  (a download or an edit)`.
- **Cause (confirmed read-only):** the launch-verified cache stores the OpenML download at
  `.../data/v1/download/52350.gz`; scikit-learn 1.8.0's `fetch_openml(data_id=15, data_home=…, as_frame=True,
  parser="auto")` materialises `.../data/v1/download/52350/breast-w.arff.gz` (same 6753 bytes) on load, so the
  node copy's `cache_tree()` gains a file and the M1 integrity check stops. The kept cache was not touched
  (`52350.gz` mtime unchanged). The harness's pilot cache has the `52350/breast-w.arff.gz` layout; the
  `data-cache` output has `52350.gz`.
- **Open point for the coordinator:** the 27 Nov engineering smoke (same code and cache, seed 999, 168/168)
  ran `openml_breast_w c3` without a stop. Reconciling that smoke record with the confirmed load-time write is
  part of the decision; the evidence record stops. I did not edit the cache, code, note or smoke record.
- **Scene:** `/work/dwong/screen_measure_20261127/paper/results/r1/screen_measure/SMEAS_EVIDENCE_20261127T1155Z/`
  (`manifest.json` `33db59d6…`, `design.json` `29396f5b…`, `lineage_runs.jsonl` `a39eaa40…` 30 rows,
  `failed_runs.jsonl` `b41fda81…`, `cotenancy.log` `a67842ef…`, `worker_runtime.jsonl` `e01c51dc…`);
  scratch `/tmp/r1_smeas_EVIDENCE_20261127T1155Z`. Elapsed 48.9 s, CPU only (about 0.22 CPU-h). No GPU, server,
  label, evaluation, test or sealed read.
- **Deliverable:** `compute-screen-measure-reissue-stop-20261127` @
  `2d7f1e9c065b4cd421a43d02f1e6ba549abf829c`; record
  `docs/r1/reports/screen_measure_stop_20261127b/SCREEN_MEASURE_STOP_20261127B.md` sha256 `c85bdc65…`, scene,
  cache diagnosis, `SHA256SUMS`.
- **Decision needed (author):** (1) rebuild/pre-warm the cache so the declared tree contains the file
  `fetch_openml` writes (new cache hash + note revision), (2) a reviewed cache-integrity rule for the benign
  ARFF materialisation (changes what the note binds), or (3) another re-issue naming the route. The frozen
  D.3 revision 4 (`9cd5863c`) was frozen before this result; if a seventh arm is wanted, that freeze must be
  revisited; this report does not change the frozen file.
- **Decided alone:** to stop at the first failed check, keep the scene and scratch unchanged, and run only the
  read-only `/tmp` cache diagnostic; no retry, no cache edit, no code or note change.

**Task id:** `compute/20261127-25`. **Tests:** none (the run stopped at its own integrity check); strict
preflight passed. **Next:** author/coordinator decision on the route above; no launch until then.
