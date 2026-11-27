# Round status — 27 Nov 2026, 11:45–12:45 UTC

`origin/main` moved `9cd5863c` → `ab32029e` (the screening re-issue STOP record was merged). `origin/coord/coordinator`
at `136083a9`; `origin/coord/compute` before this report `977953e2`. No evidence campaign ran to completion, no
GPU job is left running, and no label, evaluation or test partition was read this round.

## 1. Finished

| Task | Result | Branch / tip | Review |
|---|---|---|---|
| `compute/20261127-25` — screening evidence run under the re-issued note | **STOP** after 30 of 10,164 runs (0 failed), `openml_breast_w` `c3` seed 3301: the declared OpenML cache tree changes on load | `compute-screen-measure-reissue-stop-20261127` @ `2d7f1e9c` | record merged `ab32029e` |
| `compute/20261127-24` — P.4 Ada 4B re-probe with checkpointing | **PASS** both 4B arms; no STOP | `compute-p4-4b-reprobe-20261127` @ `a801dc60` | `compute-p4-4b-reprobe-review-20261127` @ `46b6820b`, **ACCEPTED** after one round |

### Screening STOP (`compute/20261127-25`)

- Note `docs/r1/authorizations/screen_measure_20261127_reissue.md` sha256 `7c3c8313…`, `approved: true`;
  code `e153df24`; deepthought, 16 workers, harness `6adf3859` clean, batch venv; `worker_python` `…/python3`.
- Scene kept: `/work/dwong/screen_measure_20261127/paper/results/r1/screen_measure/SMEAS_EVIDENCE_20261127T1155Z/`
  (`manifest.json` `33db59d6…`, `design.json` `29396f5b…`, `lineage_runs.jsonl` `a39eaa40…` 30 rows,
  `failed_runs.jsonl` `b41fda81…`, `cotenancy.log` `a67842ef…`, `worker_runtime.jsonl` `e01c51dc…`). Scratch
  `/tmp/r1_smeas_EVIDENCE_20261127T1155Z`.
- Cause confirmed read-only: the launch-verified cache has `.../data/v1/download/52350.gz`; scikit-learn 1.8.0
  `fetch_openml` materialises `.../52350/breast-w.arff.gz` (same bytes) on load, so the node copy's `cache_tree`
  gains a file and the M1 check stops. A `/tmp` copy reproduced it; the kept cache was not touched. Record
  `docs/r1/reports/screen_measure_stop_20261127b/SCREEN_MEASURE_STOP_20261127B.md` `c85bdc65…`.
- Decision with the author/coordinator: a cache rebuild/pre-warm, a reviewed cache-integrity rule, or another
  re-issue. The coordinator has `local/20261127-23` for the cache fix; screening stays unmeasured. The frozen
  D.3 revision 4 predates this result (the coordinator's recorded incident); nothing here changes it.

### P.4 4B re-probe (`compute/20261127-24`)

- Spec `p4_probe_spec_ada_b.json` `7181ebc5…` (template at `e92f3c73` + five fills + run id
  `trackp-p4-probe-20261127-b` + `ada_4b_reprobe`); `validate --probe`, `check_probe_template` and
  `check_probe_binding` passed; prior `kev-0.8b` first-arm seal `3d9af7d2…` bound.
- Both arms on empty Ada cards, micro-batch 8, effective batch 16, checkpointing on, 50 steps, synthetic:
  `kev-4b` peak **14,135 MiB**, 10.0458 s/step, charge **0.4474**; `qwen3.5-4b-base` peak **16,959 MiB**,
  9.9981 s/step, charge **0.4833**; both rc 0, no STOP, cards empty at start and end.
- `probe_records.json` `62a92d71…`: `p4_probe_host_class: ada_rtx6000`;
  `p4_estimate_hours` 2.52 / 6.79 / 2.51 / 6.75 for kev-0.8b / kev-4b / qwen0.8 / qwen4b;
  `p4_probe_gpu_hours: 3.10` (2.1603 prior + 0.9307 new = 3.091, T1 0.0); projection 20.57 GPU-h
  (23.67 with the probe), 29.855 slot-h, within 40/64. Charge files `9a1949a1…` (prior) and `fa49096f…` (new).
- Review history: R1 `ce2c6f63` **CHANGES REQUIRED** (the two `p4_run.log` files were skipped by `.gitignore`,
  18/20 `sha256sum -c`); fixed at `a801dc60` (force-added, final `probe_charges.json`, wording nits), re-check
  `46b6820b` **ACCEPTED**, 20/20 OK. The deliverable branch was not otherwise changed.
- Phase-1 note inputs: use `ada_sft_probe` estimates for all four arms and `p4_probe_gpu_hours: 3.10`; the prior
  `harness_commit: none` finding still stands (the synthetic `sft-data` imports harness `897d83c8…`).

## 2. Running elsewhere

| Item | State | Next check |
|---|---|---|
| Expansion G.1b (`compute/20261126-10`) | ETTh1 and MetaMaze sealed. Forest Cover split 150/150, joint **71/150**; Titanic split 150/150, joint **12/150** at 12:41Z; TASL-2 pids **106573** (cpus 4-7) and **106578** (12-15), no STOP. | Seal each on exit; then `assemble`/`summarise` with the note's spec. |
| Screening | STOP scene kept; local/20261127-23 cache fix + a second re-issue are with the coordinator/author. | Do not reuse the stopped scene; a new task names the next launch. |

## 3. Blocked / no match

| Item | Why |
|---|---|
| `compute/20261127-05` G.5 P11 TASL-2 items | TASL-2 CPUs 0-7 are held by Forest Cover (4-7) and were held by MetaMaze (0-3); Titanic holds 12-15. |
| `compute/20261127-15` houseprice CPU-set check | same 0-7 leases; rerun with a new capture after Forest Cover seals. |
| `compute/20261127-12` D.3 HTCondor preflight | the pool advertises no GPU model (`CUDADeviceName` undefined on 661 slots; 22 machines); no L40S/A100 match. Request unchanged. |
| `compute/20261126-06` G.5 campaigns | the G.5 note is not published. |
| `compute/20261126-09` D.3 per-arm smoke | revision 4 is frozen and G1/G6 are merged, but no task file names the arms/authorization yet; the card's "later task file" gate is still open. |

## 4. Capacity (read-only samples)

- **Ada:** cards 0, 2, 6, 7 free (5 MiB); 1/3/4/5 shared by another user's process (33.7 GB each). Our two probe
  jobs released their cards; the two `harness_*_r2` guards are stopped.
- **TASL-2:** expansion pids 106573/106578, CPU-only; load ~8.
- **TASL-7:** card held by another user's python (18,788 MiB); no job of ours.
- **deepthought:** load 7.45, 446 GiB available, no screening process; `condor_q` still shows the Paper A/image
  jobs 5045947/5045949/5045952 and two idle jobs 759624/759625 (not ours).

## 5. Decided alone

To run the two 4B probes concurrently on two different empty Ada cards (one job per card; free placement); to
stop the screening at its first failed integrity check and keep the scene, with only a `/tmp` cache diagnostic;
to stop the Ada guard loops after both jobs finished. No request, spec, seed, assertion or reviewed file was
edited; no wall-clock limit decided anything.

## 6. Next round checks

1. `ssh tasl2 'ps -p 106573,106578'`; on each exit seal the attempt and, when all four nodes are sealed, run
   `assemble`/`summarise` and report the per-node verdicts and summary sha256.
2. After Forest Cover (4-7) seals, rerun the houseprice check with a new capture directory; then the P11
   TASL-2 items.
3. Coordinator merges the P4 re-probe (`a801dc60`) and its re-check (`46b6820b`), then updates the phase-1
   note with the four `p4_estimate_hours`, `p4_probe_gpu_hours: 3.10` and the harness line.
4. Screening: after the local cache fix and second re-issue, a new task names the launch; no retry of the
   stopped scene.
5. Watch `condor_status` for a runnable L40S/A100; do not edit the request.

**Task ids this report covers:** `compute/20261127-24`, `compute/20261127-25`; **rows (g) acknowledged**
(free placement and shared-card rules applied; the two 4B jobs took two empty cards, no request edited, no
wall-clock limit). **Reports:** `20261127-21-screen-reissue-stop.md`, this round status.
