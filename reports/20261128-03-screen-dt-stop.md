# compute/20261127-38 — deepthought screening retries stopped; eight scenes sealed

**Result: retries stopped. Eight co-tenancy scenes kept, all 0 failed; last at 444/10,164 rows. No analysis and no
resumed scene; the measurement moved to deepthought2 (`compute/20261128-06`).**

- Task: `compute/20261127-38` (R1-SCREEN-DEEPTHOUGHT2).
- Branch: `compute-screen-dt-stop-20261128` @ `b7cc5f70b626e28c5a4e6d7bdb32e0292e71c6aa` (base `a98d2eff`).
- Host: deepthought, checkout `paper_c12136d6`; note/code/cache unchanged.
- Scene list with rows, stop reasons and manifest sha256 in
  `docs/r1/reports/screen_measure_20261128/DEEPTHOUGHT_SCREEN_ATTEMPTS_STOPPED_20261128.md`
  (`ATTEMPTS.tsv` has the full hashes); each scene has its own `SHA256SUMS`.
- Last scene `SMEAS_EVIDENCE_20261127T2125Z`: 444 rows, 0 failed, manifest
  `61f3822e4109286e57982b3c60152c5a81b914fac85a4ce1b6c1e1e3b7301d18`.
- Live check 2026-11-28T00:17Z: no `screen_measure` process on deepthought.

No review was required for this record (scene inventory only; no verdict). Next: the deepthought2 launch is
`compute/20261128-06`.
