# Screening on deepthought — retries stopped, eight scenes sealed (28 Nov 2026)

Task `compute/20261127-38` under **R1-SCREEN-DEEPTHOUGHT2**. ENGINEERING record of the stopped deepthought
attempts; the measurement moved to deepthought2 (`compute/20261128-06`). No analysis was run and no scene was
resumed.

- **Host:** deepthought, checkout `/work/dwong/screen_measure_20261127/paper_c12136d6` (code `c12136d6`).
- **Note/code/cache:** `screen_measure_20261127_reissue_2`, cache tree `3843b53c…` (unchanged from the last report).
- **Live process check (2026-11-28T00:17Z):** no `screen_measure` process; the last attempt ended on its own at
  `20261127T212608Z`.
- **Result:** all eight attempts stopped on the co-tenancy guard (0 failed runs each), the last at 444 of 10,164
  planned rows. Every scene is kept with its manifest and a per-scene `SHA256SUMS`. None of their rows enters the
  analysis; there is no `analysis.json` and nothing was resumed.

| Scene | started (UTC) | finished (UTC) | rows | failed | planned | elapsed s | stop | manifest sha256 |
|---|---|---|---:|---:|---:|---:|---|---|
| `SMEAS_EVIDENCE_20261127T1550Z` | 155041 | 155157 | 186 | 0 | 10164 | 63.2 | cotenancy 9.87 cores left to other users | `39575f58…` |
| `SMEAS_EVIDENCE_20261127T1822Z` | 181503 | 181655 | 108 | 0 | 10164 | 63.2 | cotenancy -2.95 cores left to other users | `37670927…` |
| `SMEAS_EVIDENCE_20261127T1837Z` | 183053 | 183303 | 439 | 0 | 10164 | 122.9 | cotenancy 2.11 cores left to other users | `5eede42d…` |
| `SMEAS_EVIDENCE_20261127T1840Z` | 183833 | 184042 | 442 | 0 | 10164 | 123.0 | cotenancy -0.89 cores left to other users | `ecdf2ea0…` |
| `SMEAS_EVIDENCE_20261127T1842Z` | 184152 | 184301 | 223 | 0 | 10164 | 62.7 | cotenancy 2.95 cores left to other users | `d1a36d8b…` |
| `SMEAS_EVIDENCE_20261127T1845Z` | 184502 | 184713 | 440 | 0 | 10164 | 123.7 | cotenancy -4.79 cores left to other users | `95a10740…` |
| `SMEAS_EVIDENCE_20261127T2120Z` | 211812 | 212101 | 365 | 0 | 10164 | 123.7 | cotenancy -5.81 cores left to other users | `5badf0b3…` |
| `SMEAS_EVIDENCE_20261127T2125Z` | 212358 | 212608 | 444 | 0 | 10164 | 124.0 | cotenancy 3.01 cores left to other users | `61f3822e…` |

`ATTEMPTS.tsv` holds the same table with full hashes. Two earlier strict-preflight refusals (`1816Z`, `2118Z`) wrote no
output and are not scenes.

**Why no further attempt on deepthought:** the deepthought2 route gives 128 cores, so the 64-worker guard fits with
headroom; the deepthought retries were stopped by this card.

Decided alone: sealed each existing scene with a `SHA256SUMS` in place (no file of a scene was changed) and did not
resume any scene.
