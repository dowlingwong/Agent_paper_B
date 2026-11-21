# Track G G.0 U2 raw-cost — node `autoresearch_fixedtokens` — RESULT (17 November 2026)

**Status: PASSED (CHECKLIST_E_PASSED); one node only.** Authority: `R1-TRACKG-G0-GO` (main **`50176481`**),
`R1-TRACKG-PORT-OWNER`, `R1-TRACKG-LICENCES`, `R1-TRACKG-PORT-DECISIONS` (main `50176481`),
`R1-TRACKG-G1B-HOST`; unit revision 2 accepted by review R2
(`reviews/TRACKG_U2_RAWCOST_REVIEW_R2_20261117.md`, sha `f827637b…`, 0 BLOCKING/MAJOR, 12 MINOR with M1–M3
command corrections applied). ENGINEERING_ONLY; not evidence; no noise floor/D21/D28 (G.1b L40S); no T1
label run; one node only.

## Kit / environment

- Harness worktree `harness_ar` @ `08d065077d40087114452697d5d596e66a0578be` (`mac-trackg-port-ar-20261117b`,
  base `717ad835`, clean tracked tree; only the untracked `nodes/autoresearch_fixedtokens/data` link).
- Paper `main` `50176481` (kit report `TRACKG_U3_PORT_AUTORESEARCH_20261117.md`, review, checklist F).
- Python **3.12.16** (`envs/torch312`), torch **2.6.0+cu124** (CUDA 12.4), driver **545.23.08**, Ubuntu
  22.04.5/kernel 5.15.0-151, 96 CPUs, 503 GiB RAM; `uv pip freeze` **77 lines, sha
  `dea8a9df3a92f233009d5480921c9685c24ecd1e91e932d9efdfe53fb860eecd`** (`env_freeze.txt`);
  `torch.cuda.is_available() == True`, 8 devices. Static kit test (CPU-masked, `CUDA_VISIBLE_DEVICES=`,
  `PYTHONDONTWRITEBYTECODE=1`): `tests/trackg/test_port_autoresearch.py -k "not smoke"` → **25 passed, 1
  deselected** (log `static_test_prior_25passed.log`). Data: `AR_TRACKG_DATA_ROOT` outside the repo,
  `prepare_data.py` complete; `data_manifest.json` sha **
  `ab7186d2b6fba9037283a59de9f071c317a98e4f43806368663d6d9e398faf51`**, 13 files, 963 M, source revision
  `915333b4…`; node data link to it.

## Paper-A gate and co-tenancy (re-run immediately before launch)

- Gate `clear_finished`, `paper_a_live_waiting_for_card: false`, `unidentified_apps: 0`; newest v4 `live_*`
  = configured run dir; self-excluded pgrep empty; capture `paper_a_gate.json` (UTC 09:48:47Z; the
  `paper_a_status.py` config is the deployed `c75bf9c3…` one).
- Chosen GPU **card 0, UUID `GPU-9be33fd1-8eeb-497d-772a-87362d6720be`**, free 48,427 MiB at launch (run-1
  floor ≥24 GiB), 0 % util; before/after records in `gpu_before.csv`/`gpu_after.csv`; no other user's
  process touched. Memory cap: whole smoke wrapped in `systemd-run --user --scope -p MemoryMax=64G
  -p MemorySwapMax=0` (cap probe rc 0); `--memory-limit` string records that scope.

## Run

- Command: `PYTHONPATH=src python3 -m tests.trackg.port_smoke_gpu --node autoresearch_fixedtokens
  --gpu-uuid GPU-9be33fd1-… --cpus 0-7 --memory-limit "systemd-run --user --scope -p MemoryMax=64G
  -p MemorySwapMax=0 (whole unit)" --runs-root <root>/runs --provisional-timeout 1800`, from `harness_ar`
  with the torch env first on `PATH` and `/usr/bin` for gcc/as, `CC=/usr/bin/gcc`, `CXX=/usr/bin/g++`
  (the gcc/as path/`PATH` ordering and a one-step compile prewarm were operator fixes; recorded below).
- **rc 0; wall 564 s (9:23.68)**; `CHECKLIST_E_PASSED autoresearch_fixedtokens`; 8 executed runs (baseline,
  broken diff, first edit, E1–E4, B2) + 1 refused frozen-path diff; 9 `run_record.json`.
- Baseline **B1** (`runs_smoke/s000_baseline/run_record.json`): `elapsed_seconds_info_only` **67.901 s**,
  `val_bpb **1.291068**`, outcome ok, `peak_vram_mb 5,211.3` (from the run log); B2 repeat **64.096 s**,
  same value (exact determinism check); s002 NaN divergent as expected; s003/E1–E4 all ok
  (E2 110.81 s, others 60.9–71.0 s, values 1.223–1.303). Raw cost: baseline time 67.901 s and baseline
  peak VRAM 5,211.3 MB; the 1 s `nvidia-smi` sampler around the whole smoke maxes card 0 at **32,228 MiB**
  (labelled **upper bound, includes co-tenants**, not the baseline footprint). CPU/RAM of the whole smoke
  (`/usr/bin/time -v`): user 662.47 s, sys 42.78 s, max RSS 2,110,468 kB (whole-smoke aggregate, labelled).
- Timeout: provisional 1800 s; B1 × 3 = 203.7 s would be the per-decision node timeout; no timeout/retry
  occurred. Disk: run root 75 M, data 963 M, host 114 G free before/after; no deletion.

## Operator fixes recorded (no kit change)

1. Static tests must run CPU-masked (`CUDA_VISIBLE_DEVICES=`); GPU-mode fails by construction.
2. Torch 2.6 compile needs a C compiler/assembler: `CC=/usr/bin/gcc`, `CXX=/usr/bin/g++`, and `/usr/bin` must
   stay on PATH before the smoke (a PATH-order regression made `gcc` unable to exec `as` in one attempt).
3. Prewarm one 65,536-token step with the smoke's inductor/triton cache dirs to compile the baseline before
   the smoke (otherwise the first full run can hit the backend compiler).
4. Keep `AR_TRACKG_DATA_ROOT` outside the repo and the deploy venv at 3.12; both recorded above.

## Scope statement

This result is the `autoresearch_fixedtokens` row only. The other seven nodes run under their own reviewed
units (same procedure); U4 compiles the rows. Ada G.0 only; no noise floor/D21/D28 (G.1b L40S); no T1
label/sweep; no evidence; no TASL-7 action; no deletion; no main/exam-x push.
