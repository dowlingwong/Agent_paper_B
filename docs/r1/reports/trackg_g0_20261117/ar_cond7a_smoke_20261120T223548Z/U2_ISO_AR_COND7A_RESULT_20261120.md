# R1-TRACKG-AR-COND7 option A — isolated Ada GPU smoke of `autoresearch_fixedtokens` — RESULT (20 November 2026)

**Status: STOP — the one isolated smoke was consumed and FAILED at its first run (baseline) with a CUDA
out-of-memory during evaluation, caused by another user's job that started on the launch card mid-run after the
card had been verified idle. No retry (one smoke only). `CHECKLIST_E_PASSED` was not reached, the expected 8
executed records / B2 repeat were not reached, and the logits-transfer slowdown measurement was NOT obtained.**
The option-A code itself showed no CUDA-IPC error, the baseline run's isolation record is `effective:true`,
`waivers {}`, `exceptions []`, private `/dev/shm`, and the result path contains no CUDA-IPC API call — but the
single run was destroyed by GPU co-tenancy at evaluation time. ENGINEERING_ONLY; **not evidence**; no T1; no
noise floor/D21/D28; one node only; no retry; no TASL-7/TASL-2, no HTCondor/deepthought, no other host;
no push/commit; no deletion. Existing Ada worktrees were not modified; a **new** worktree was added for this run.

## 1. Authority and objects

- PLAN row **R1-TRACKG-AR-COND7** (option A: CUDA IPC removed from the result path; worker hands logits to the
  frozen parent through the CPU `memfd` buffer; `torch.cuda.init()` in `cuda_open`; kit pins updated; one isolated
  smoke, then U2; the slowdown measured and disclosed), on published main `df58bcd5…` (`docs/r1/PLAN.md:1317`),
  per the accepted cond7 review `docs/r1/reviews/TRACKG_AR_COND7A_CODE_REVIEW_20261120.md` (sha256
  **`261a03e9afb5921f6afdcc0979e83122d1f8cbaef85d6cf723c21ded8db66cae`**; ACCEPTED code, 0 BLOCKING, 1
  report-only MAJOR + 6 MINOR, conditions C1–C6; C1 fixed at the branch tip used here).
- Harness-isolation fix review `docs/r1/reviews/HARNESS_ISOLATION_FIX_REVIEW_20261119.md` (sha `c8e468c7…`),
  condition **C3** — the logits-transfer design decision + `cuda_open` `torch.cuda.init()` fix; this branch is
  that change.
- Kit branch **`mac-trackg-iso-ar-cond7a-20261120`** @ **`73303380197477df971e865440d0ae11135fe1b3`** (base
  `448f6820…`; 4 commits: `0e0b820` code, `6f235c4` report, `13786d1` captures, `7330338` review-fix report),
  pushed to harness origin (`github.com/dowlingwong/autoresearch_harness`).
- Code-unit report at the branch tip (fixed M1/C1/C4): `docs/r1/reports/trackg_g0_20261117/
  TRACKG_AR_COND7A_CODE_UNIT_20261120.md`, sha256 **`370782abf2c14850c9b56f70789df51bee3e332ac37bcf7a82134366081df0a8`**
  (copy in `references/`); review copy sha `261a03e9…`; `code_change.diff` sha `87d0de73…`; spec copy sha
  `5bdce00a…`.
- **Fresh Ada worktree** `/home/dowling/r1_trackg_20261117/harness_iso_ar_cond7a_20261120` created from
  `origin/mac-trackg-iso-ar-cond7a-20261120` (new local tracking branch, `git worktree add`), HEAD **==
  `7330338`** and `git status --porcelain --untracked-files=no` empty; existing worktrees
  (`harness_iso_ar`, `harness_iso_mlab`, `harness_iso_mlgym`, `harness_iso_core`, `harness_iso_fix_20261119`,
  `harness_ar`, `harness_mlab`, `harness_mlgym`, main checkout) untouched (`worktree.txt`,
  `kit.txt`).

## 2. Data setup (guarded, logged; no copy/deletion)

- Node `autoresearch_fixedtokens`; complete data tree already at
  `/home/dowling/r1_trackg_20261117/data/autoresearch_fixedtokens` (outside the repository); setup command
  re-run from the node dir with `envs/torch312/bin` first on `PATH` and the guard
  `test -n "$AR_TRACKG_DATA_ROOT" && python3 prepare_data.py --out "$AR_TRACKG_DATA_ROOT/autoresearch_fixedtokens"`;
  complete `--out` was only re-checked and re-linked (**SETUP_RC=0**, no download).
- **`data_manifest.json` sha256 `ab7186d2b6fba9037283a59de9f071c317a98e4f43806368663d6d9e398faf51`** (13 files,
  963 M, read-only); node `data` link →
  `/home/dowling/r1_trackg_20261117/data/autoresearch_fixedtokens`; no `synthetic` marker. Setup log sha
  `60289148…` in `prep/` (`AR_DATA manifest_sha256=ab7186d2… files=13`).
- Env `envs/torch312`: Python **3.12.16**, torch **2.6.0+cu124** (CUDA 12.4); `uv pip freeze` **77 lines**, sha256
  **`d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42`** (live in-scope re-check reproduced it)
  — `env.txt`, `env_freeze.txt`.
- **Pins:** committed-file `frozen_pin_sha256` **`147f0d35d40df54b5902260f07bf25043f515dbc0066991ab05e3b8c64eda0fc`**
  (20 entries, recomputed with the kit loader before the data link; census value); deployed run-record pin
  **`069e987ac71a8ff30db7a28b7410778a4a8211aa3ecff00e23437498f2e9d2ed`** (21 entries incl. `data: link:<abs
  target>`, recomputed after setup and matching the executed baseline record) — `pins.txt`, `prep/pins_*`.
- **Spec:** `autoresearch_fixedtokens.yaml` raw `raw_sha256` **`5c1bdf3d84c0721818adc239186ac30ffa2c2bb3b6b373e56b236e47cbd61192`**
  (node spec version; `setup_command` above; `run_budget {kind: tokens, value: 32768000}`; candidate
  `metric val_bpb`; `selection.test_scored: false`; `isolation.shared_dev_shm: false`).
- **No CUDA IPC in the result path (static):** AST scan of the executed node's `run_fixed_budget.py` and
  `ar_worker.py` for `cuda_share`, `cuda_open`, `_share_cuda_`, `_new_shared_cuda`, `bind_cuda` → **NONE**
  (`prep/cuda_ipc_scan.txt`, repeated in-scope in `prechecks.txt`).

## 3. Gate, GPU selection and launch prechecks

- Paper A gate JSON `gate/gate_20261120T223548Z.json` sha256
  **`4475538d04a14f5ec20d9c0413d566ea8a399390b6e0f2948f4c227447369dc1`**, UTC **2026-11-20T22:35:52Z**;
  **three-check PASS**: `clear_finished`, `paper_a_live_waiting_for_card: false`, `paper_a_processes: []`,
  `unidentified_apps: 0`; newest v4 `live_*` == configured run dir; self-excluded `pgrep` empty.
- **GPU had to wait for a truly idle card:** at 22:32–22:35Z all 8 cards carried other users' live apps
  (hongkunyang 3 cards >1 day, asif 2 cards, vla-reasoning 1 card, zihaozhao 1 card; e.g. card 6 had 33.0 GiB
  free but 2 apps). The bounded watcher (`gpu_wait.log`) records the per-card census each round; card 5
  (`GPU-5357dc5f-5d1d-af80-a3f4-3eb5aeb38f0d`) became **free=48,427 MiB, apps=0, util=0 %** at **22:35:44Z** and
  the smoke was launched at **22:35:48Z** with cpuset `95,87,84,80,79,76,61,58`.
- **Launch qualification (`gpu/gpu_qualify.txt`, `gpu/gpu_before.txt`)**: card 5, **48,427 MiB free, 0 % util,
  no other compute app**; floor ≥ 8,192 MiB.
- **Inside-scope prechecks PASS** (`prechecks.txt`, `cgroup_probe.txt`): `which python` =
  `…/envs/torch312/bin/python`, Python 3.12.16, torch 2.6.0+cu124; live env-freeze sha == expected
  `d2e70fe4…`; data manifest sha == `ab7186d2…`; data link resolves; spec `raw_sha256` == `5c1bdf3d…`;
  committed pin `147f0d35…`; `import tests.trackg.port_smoke_gpu` OK; `smoke_entry` found; **cgroup probe
  `memory.max=8589934592`, `memory.swap.max=0`** from the echoed scope path; `CUDA_VISIBLE_DEVICES=""`;
  `taskset` cpuset as above.
- `--memory-limit "external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 (enforced cgroup)"`
  one line; `--provisional-timeout 1800`; runs-root outside the repo (`runs/`); scope unit
  `run-rbc2bb3769320429692b5031284293585.scope`.

## 4. The single smoke and the concrete failure

- Smoke start **22:35:48Z**; baseline (`s000_baseline`, one fit budget 32,768,000 tokens) started immediately.
  The training phase completed normally: **500/500 steps**, `AR_TOKENS consumed=32768000`,
  `AR_DATA manifest_sha256=ab7186d2… files=13`, `AR_INFO peak_vram_mb=1980.1` (worker training peak) — run.log
  sha `014f86f3…`.
- **Failure:** evaluation then died with
  `torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 256.00 MiB. GPU 0 has a total capacity of
  47.30 GiB of which 157.00 MiB is free` at `run_fixed_budget.py:165 → causality_probe → :109`, with the OOM
  message listing **our parent 4.21 GiB + worker 3.42 GiB** and **nine zihaozhao processes on the same card
  (≈42.6 GiB: 3×4566 + 3×6862 + 3×2762 MiB)**. The failure-time census (`failure_time_census.txt`, 22:54:14Z)
  shows card 5 at **46,878 MiB used / 1,554 MiB free / 92 % util**, with those co-tenant processes (ethe 15:07–15:32,
  i.e. started ≈22:38:42–22:39:07 — **≈3 minutes after our launch**, when the card had been verified idle).
- **Baseline record** `runs/runs_smoke/s000_baseline/run_record.json` sha
  **`bf41cc7c948c13f7e7fc5b7685f7e71611eea0014dcba8dc88374e7193388ceb`**: `elapsed_seconds_info_only`
  **748.79 s**, `outcome {kind: divergent, reason: nonzero_exit, value: null,
  detail: {metric_reported: false, returncode: 1}}`, `process.returncode 1`, `killed_with: null`,
  `timed_out: false`, `leftover_processes_killed: true`; `result_channel.txt` empty (sha `e3b0c44…`).
  The 748.79 s includes the OOM and the runner's teardown/cleanup (cgroup kill with 11 processes); it is **not**
  a completed evaluation and **not** a transfer-time measurement.
- **Isolation gate on that executed record PASSED:** `isolation.effective: true`, `waivers {}`,
  `exceptions []`, `log_intact: true`, `worker_sandbox.shared_dev_shm: false` (**private `/dev/shm`**),
  `cgroup.kill` with `empty_after: true` / `removed: true` (11 processes), result-channel present (empty),
  `limits.gpu_uuids [GPU-5357dc5f…]`, `cpu_list [95,87,84,80,79,76,61,58]`, one-line external limit,
  `memory_method: external`, provisional 1800 s, timeout factor 3.0.
- **No CUDA IPC error occurred anywhere** (AST scan NONE; no run log contains `invalid resource handle`,
  `cuda_open`, `bind_cuda`, `_share_cuda_`, CUDA-IPC error markers; `verify_full.json no_cuda_ipc_error: true`).
- The smoke continued into `s002` (broken diff) because `port_smoke_gpu` only checks the checklist at the end;
  after the baseline failure was confirmed, the smoke was **stopped deliberately** (`cgroup.kill`) at
  **22:54:22Z** to stop further GPU contention against the other user's job (`systemd_run_rc=137`; smoke output
  has no `CHECKLIST_E_PASSED`; no JSON lines printed). `s001` refused frozen diff was already recorded
  (`executed:false`); `s002` is partial (run.log sha `02310512…`, no record).
- **Expected checks outcome:** `CHECKLIST_E_PASSED` **NOT reached**; **1 executed record + refused `s001`
  (not 8 executed)**; **B2 repeat NOT reached**; baseline non-ok → STOP for the unit; **no retry**.

## 5. Measured numbers (what is and is not usable)

- **Slowdown measurement: NOT OBTAINED.** The run failed in the first evaluation phase (causality probe) before
  any metric was reported, so no per-run and no per-request logits-transfer timing exists.
  - `elapsed_seconds_info_only` of the failed baseline **748.79 s** (11.03× the 17 Nov B1 `67.901 s`) is the
    start→record wall for a **failed** run including OOM and cleanup; it must **not** be used as the transfer
    slowdown. The derived "per-request surrogate" in `slowdown.json` (1.057 s = (748.79−67.901)/644) is
    therefore **invalid as a transfer measurement** and is kept only as provenance of the failed record.
  - Smoke wall to deliberate termination **22:35:48→22:54:22Z ≈ 1,114 s** (vs 17 Nov whole smoke 564 s) — also
    not a valid comparison: the smoke was stopped after one failed run (no 9-run smoke completed).
  - What is comparable: the **training phase is unchanged** (500 steps / 32,768,000 tokens, `AR_INFO
    peak_vram_mb=1980.1` MB, training log ends ≈73 s after start), consistent with option A changing only the
    result path, not training.
- **Peak host RSS:** not captured — `/usr/bin/time -v` had not flushed when the scope was killed (`time_v.txt`
  0 bytes), and `memory_cgroup.txt` was not written because the in-scope script was killed before its
  post-smoke capture. At failure the scope's `memory.current` was **5,136,302,080 B (4.78 GiB)** against
  `memory.max=8589934592`; `memory.events` `max 0 / oom 0 / oom_kill 0` → the host 8 GiB cgroup cap was **not**
  the failure.
- **Memory-cap mechanism (documented):** external `systemd-run --user --scope -p MemoryMax=8G
  -p MemorySwapMax=0` (recorded `limits.memory_method: external`, `external_limit` one-line string); this
  cgroup cap **does** count the file-backed 1 GiB memfd shmem and the parent's anonymous 1 GiB snapshot, unlike
  a `rlimit_data` cap. The failure was **GPU VRAM** exhaustion by co-tenant processes, not the host cap.
- **Peak VRAM:** worker training peak from the run log `AR_INFO peak_vram_mb=1980.1` MB; the whole-smoke 1 s
  compute-app sampler maximum is **48,128 MiB** (max single row 6,862 MiB; 1,106 s sampled) — this is a
  **whole-smoke upper bound that includes the co-tenant by construction, not a per-run peak and not attributable
  to this node** (17 Nov worker baseline was 5,211.3 MB).

## 6. Deviations / attribution

1. **External co-tenancy destroyed the single smoke.** The launch card was verified idle (48,427 MiB free, no
   app, 0 %); ≈3 minutes after launch another user's job (zihaozhao, 9 GPU processes, ≈42.6 GiB) started on the
   same card and filled it (1,554 MiB free at failure), so the baseline evaluation hit CUDA OOM. The island
   evidence: launch census `gpu/gpu_qualify.txt` / `gpu_before.txt` vs failure census
   `failure_time_census.txt` vs whole-smoke sampler rows (co-tenant pids 4093944…4099263, and our pids
   4053360/4057387). No card switch was made; no other user's process was signalled or restricted.
2. **No transfer-slowdown measurement** (failure before metric); the option-A evaluation design was not
   exercised to completion. This is a failure of the **one smoke**, not evidence against option A's static
   correctness (no-CUDA-IPC/private-shm/isolation checks passed on the executed baseline).
3. **Missing post-smoke captures** (`time_v.txt` empty, `memory_cgroup.txt` absent) because the failed smoke was
   deliberately stopped with `cgroup.kill`; preserved as-is and recorded here.
4. Waiting time: ≈7 minutes of polling were needed before a genuinely idle card appeared; the whole per-card
   census is preserved in `gpu_wait.log`.
5. No retry was performed (one smoke only). A new isolated smoke would need fresh coordinator authorization and
   a card guaranteed idle for the whole run.

## 7. Scope / attestation

One node only (`autoresearch_fixedtokens`), one isolated smoke attempted and stopped after failure; no retry; no
T1/evidence/noise/D21/D28; no other node or host; no TASL-7/TASL-2, no HTCondor/deepthought; **no push or commit**
(worktree HEAD remains the pushed branch tip `7330338`; only this new result dir is added on the Mac side); **no
deletion** (the new Ada worktree, data, and all partial run outputs are preserved). The option-A code report,
review, diff and spec are preserved in `references/`; the executed worktree/kit/pins/data are captured in
`kit.txt`, `pins.txt`, `data_manifest.txt`, `prep/`.

## 8. Evidence index (this directory)

`SHA256SUMS` (every file below, `shasum -a 256 -c` verified). `logs/run_node.log` (outer log; STOP lines),
`DONE`, `RESULT_STATUS.txt`; `gate/` (JSON + check; sha `4475538d…`, UTC 22:35:52Z); `gpu/`
(`gpu_qualify`, `gpu_before`, `gpu_mid` [22:36:01Z, our run only], `gpu_after` [co-tenant present]);
`failure_time_census.txt` (22:54:14Z); `sampler/` (1 s compute-app CSV, `sampler_max.json`); `prechecks.txt`,
`cgroup_probe.txt`, `env.txt`, `env_freeze.txt`, `data_manifest.txt`, `kit.txt`, `pins.txt`, `prep/` (setup log,
manifest capture, pins recomputed, env, CUDA-IPC scan, worktree log), `gpu_wait.log` (idle-card search; card 5
freed 22:35:44Z), `launch_ar_cond7a_attempt1.log`, `runs/` (baseline record/log/channel, `s001` record, partial
`s002` log), `record_hashes.txt`, `verify_full.json`/`summary` (STOP: 2 records, 1 executed, missing 7 runs),
`verify_records.json`, `summary.json`, `slowdown.json` (failed-run numbers, invalid as measurement),
`disk_before.txt`, `disk_after.txt`, `runs_du.txt`, `host.txt`, `invocation_inner.sh`, `references/` (fixed code
report sha `370782ab…`, review sha `261a03e9…`, `code_change.diff` sha `87d0de73…`, spec copy sha `5bdce00a…`,
branch log), `scripts/` (the exact runner, verifier, watcher and analysis script), `REFERENCES` copies.
Raw evidence preserved read-only on Ada at
`/home/dowling/r1_engineering/u2_iso_20261119/ar_cond7a_smoke_20261120T223548Z/` (no deletion).
