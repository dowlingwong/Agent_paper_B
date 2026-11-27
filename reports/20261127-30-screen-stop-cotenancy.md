# STOP — screening evidence run, co-tenancy breach (`compute/20261127-30`)

**Result: STOP at the co-tenancy guard; 186 of 10,164 runs written, 0 failed.** The run stopped itself with exit 3
and kept its scene. Nothing is resumed, patched or retried; a new run needs a fresh stamp and a passed strict preflight.
This STOP returns to the author.

- **Task:** `compute/20261127-30` (R1-SCREEN-MEASURE-REISSUE-2, `main` `280c0015`/later).
- **Note:** `docs/r1/authorizations/screen_measure_20261127_reissue_2.md`, `approved: true` (read from published
  `origin/main`; the code checkout `c12136d6` predates the note).
- **Code:** `c12136d664ae588a2539b76b2602e36742979ce8`, clean checkout
  `/work/dwong/screen_measure_20261127/paper_c12136d6`.
- **Host / environment:** deepthought, 16 workers, CPUs only; e1 batch venv and harness `6adf3859…` as the note
  requires; data cache `/work/dwong/screen_fix_20261127/data_cache_20261127T134927Z` (tree `3843b53c…`).
- **Run id / scene:** `SMEAS_EVIDENCE_20261127T1550Z`,
  `/work/dwong/screen_measure_20261127/paper_c12136d6/results/r1/screen_measure/SMEAS_EVIDENCE_20261127T1550Z`;
  tmux `smeas_reissue2`; log `/work/dwong/screen_measure_20261127/smeas_reissue2.log`.
- **STOP:** `cotenancy 9.87 cores left to other users` at `2026-11-27T15:51:53Z` (the note requires at least 10).
  `cotenancy.log`: `cpus 40, free_for_others 9.87, load1 45.13, our_workers 15, ok false`.
- **Progress:** 186 planned runs written, 0 failed, 63.2 s elapsed; manifest written with the reason.

| File | sha256 |
|---|---|
| `design.json` | `29396f5bb4dee22a0937b7587c7a5708a75570706075284bbfb9f4721f8085d0` |
| `lineage_runs.jsonl` | `a21db59335aef35d0185ded39943032a56e1fef0f50917310273ad9683100f9b` |
| `worker_runtime.jsonl` | `5f6ea5477d856e888d64336aa119d826550adf7924281204e9954c623ecad4b5` |
| `cotenancy.log` | `3011a1903188cd2881079b60ca9716f5fa4e890d83c077d85b6ae7d6fcc40b23` |
| `manifest.json` | `39575f58bf0a2d824b6f2e75bab2075230b03e653396bd0e9c73d5dada05c2c9` |

`manifest.json` reports `planned_runs 10,164`, `written_runs 186`, `failed_runs 0`, `stop` as above,
`runs_sha256 a21db593…`.

## Pre-check, not a run

An earlier attempt with stamp `20261127T1548Z` refused in the strict preflight because the fresh clone's
`origin/main` was stale against the remote after the coordinator's new merge. It created **no output directory** and
is not a run or scene. After `git fetch`, `1550Z` passed preflight and started.

## What happens next

The run waits for the author/coordinator. A retry needs a fresh `SMEAS_EVIDENCE_<stamp>` and a strict preflight at a
time when deepthought has at least 10 cores free for others at start and during the run; the 186-run scene stays
untouched. No analysis was run and no manifest statistic is used.
