# STOP — screening evidence run (`compute/20261127-22`): worker-runtime `python`/`python3` alias

**Result: STOP at the first worker-runtime probe. 0 of 10,164 runs written.** Strict preflight passed;
the scene is kept; no retry, no patch.

- **Task:** `compute/20261127-22`; note `docs/r1/authorizations/screen_measure_20261127.md`
  (`approved: true`, `main` `840ad01d`), code `e153df24ee3435bbe0b2fa994297b15250550c30`.
- **Host / environment:** deepthought, 16 workers; batch venv `/ceph/dwong/r1_prepare_20261025/venv`
  (Python 3.13.15; sklearn 1.8.0, NumPy 2.4.4, SciPy 1.17.1, pandas 3.0.3); e1 batch harness
  `6adf3859de66c4814fcf376eed59880fbd8eeaf7` tracked-clean.
- **Scene:** `/work/dwong/screen_measure_20261127/paper/results/r1/screen_measure/SMEAS_EVIDENCE_20261127T1032Z/`
  and scratch `/tmp/r1_smeas_EVIDENCE_20261127T1032Z` (empty).
- **STOP record:** `manifest.json` `0e8113898291d6d04b289f84aea8f27b91df96f08d92d1324093dad2f77a7142`;
  `design.json` `29396f5bb4dee22a0937b7587c7a5708a75570706075284bbfb9f4721f8085d0`;
  `lineage_runs.jsonl` empty (`e3b0c442…`); `cotenancy.log` `ca179471…`.
- **Diagnosis (read-only):** expected `worker_python` `/ceph/dwong/r1_prepare_20261025/venv/bin/python`,
  observed `/ceph/dwong/r1_prepare_20261025/venv/bin/python3`. Prefix, four library versions and
  `package_list_sha256` `a089bbf1…` are equal; both are symlinks to the same interpreter. The probe
  compares `sys.executable` literally, so the launch's `python` vs the worker's `python3` is the whole
  mismatch.
- **Deliverable:** `compute-screen-measure-stop-20261127` @ `30781f0b8a65c0653585dbb897a1fde6d3d072eb`
  (STOP record + copied scene + SHA256SUMS, `docs/r1/reports/screen_measure_stop_20261127/`).
- **Decision needed (author/coordinator):** re-issue the note/command with the same interpreter name,
  or a reviewed probe change comparing `worker_python_realpath` (environment checks unchanged), then a
  new `SMEAS_EVIDENCE_<stamp>` run. This is not an operator patch; screening stays unmeasured, so the
  seventh-arm decision is not reached.
- **Not done:** no harness run, no label/evaluation/sealed read, no other job on deepthought; P.4
  re-probe not started pending the coordinator's priority call.

**Task id:** `compute/20261127-22`. **Branch/tip:** `compute-screen-measure-stop-20261127` @ `30781f0b`.
**Tests:** none (the run stopped at the preflight probe); the strict preflight passed. **Next:**
coordinator/author decision; no retry until a re-issued note or reviewed probe fix.
