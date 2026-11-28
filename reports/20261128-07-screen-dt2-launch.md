# compute/20261128-06 — screening evidence launched on deepthought2 (third re-issue)

**Result: launched; the strict preflight passed and the run is writing rows. No STOP so far.** Third re-issue,
`R1-SCREEN-DEEPTHOUGHT2`; note `docs/r1/authorizations/screen_measure_20261127_reissue_3.md` (approved, sha256
`55779a6c…`), code `a7c2f8fb`, review `SCREEN_MEASURE_DEEPTHOUGHT2_REVIEW_20261128.md`.

- Task: `compute/20261128-06` with `compute/20261127-38`.
- Host: deepthought2. Launch script `/work/dwong/screen_measure_20261127/launch_dt2_smeas_20261128.sh`, parent
  PID 3697711; job is the detached `taskset` + `python3 -B -m r1.noise.screen_measure run` under it.
- Launch: **2026-11-28T00:27:01Z / 01:27:01 CET** (preflight check timestamp).
- Checkout: `/work/dwong/screen_measure_20261127/paper_dt2_20261128T001405Z` at `a7c2f8fb` (clean worktree add).
- Run directory: `results/r1/screen_measure/SMEAS_EVIDENCE_20261128T001405Z` inside that checkout.
- Cache: `/work/dwong/screen_fix_20261127/data_cache_20261127T134927Z` (`MANIFEST.json` present, tree `3843b53c…`).
- Batch: `/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw` (harness and venv
  present; `python3` resolved to the batch venv as the command requires).

## Preflight and capacity (captured 2026-11-28T00:27:09Z)

- `cotenancy.log`: `{"cpus": 128, "free_for_others": 119.82, "load1": 8.18, "ok": true, "our_workers": 0,
  "utc": "2026-11-28T00:27:01Z"}` — the guard's ≥ 64 + 10 headroom condition holds.
- `hostname -s` = deepthought2; `nproc` = 128; `nproc --all` = 128; affinity 0-127; `/sys/fs/cgroup/cpu.max`
  empty (no cgroup CPU cap).
- `uptime` at capture: load 17.76 / 12.61 / 10.25 with 13 users; still 128 - 17.76 ≈ 110 cores available.
- `nvidia-smi`: card 0 L40S 15,774 MiB used (foreign), card 1 L40S 3 MiB. CPU job only
  (`CUDA_VISIBLE_DEVICES=`); no GPU used.
- `/work/dwong/...` and `/ceph/dwong/...` paths in the command exist.

## First progress

- Workers started at `01:27:02` host time; first `trial-001` worker lines at `01:27:02–01:27:04`.
- `lineage_runs.jsonl`: **277 rows at ~00:28:00Z**, 0 failed so far, of 10,164 planned.
- Files present at launch: `cotenancy.log`, `design.json`, `lineage_runs.jsonl`; `manifest.json` is written at
  the end.

Decided alone: none beyond the card's exact command; the launch used a fresh UTC stamp and a new checkout, and no
attempt was resumed.

**Next round:** check rows/10,164, `failed_runs`, and the co-tenancy guard each round. On completion run the
analysis exactly as the note says, then deliver the analysis outputs and hashes on a branch with a fresh review.
A STOP (statistical or co-tenancy) goes to the coordinator with the scene sealed; D.3 step (8) waits for the
result (R1-D3-STEP8-HOLD).
