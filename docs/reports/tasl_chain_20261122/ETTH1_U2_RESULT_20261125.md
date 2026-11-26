# U2 census smoke — Track G kit `gc7rc_etth1` (1GC-7RC ETTh1), TASL-2, CPU-only — result, 25 November 2026

**Verdict: PASS** (CPU-only U2 smoke). The valid smoke is attempt B: the reviewed kit's own stub-manager smoke
`tests/trackg/port_smoke_gpu.py --node gc7rc_etth1` at the node's full 2,000-step budget on the real data, run
CPU-only in a delegated cgroup scope on TASL-2 with no GPU and no GPU lease; it printed
`CHECKLIST_E_PASSED gc7rc_etth1`, and all 29 driver checks are true. **B1 and B2 agree to the digit**
(`val_mse 0.654580`, sealed `test_mse 0.375348`, identical log and result-channel sha256), every executed run has
`isolation.effective: true`, `waivers {}`, `exceptions []`, and the pins, data, environment and worktree are the
accepted ones and were unchanged by the smoke. The smoke does **not** establish the GPU census or GPU
determinism (review condition c2/c4); see §8. Attempt A — an earlier launch of the same smoke that stopped for a
launch-environment defect (the pinned env's `bin` was not exported on `PATH`, so the kit's campaign runs fell
through to `/usr/bin/python3`) — is preserved unmodified and disclosed in §3; on the lead's 25 Nov 12:16Z
authorization exactly **one** corrected launch (attempt B) was made and there was **no further retry**.

Captures (92 files, 656 KiB, no data/out.tar) are in `ETTH1_U2_RESULT_20261125_captures/` beside this file, with
`SHA256SUMS` sha256 **`c943b9f81b3479ddc11db520bd8b50aa073c2911a6cc317b10bcb92b91298800`**
(`sha256sum -c` rc 0); attempt A's preserved evidence (its original capture SHA256SUMS, 47 entries, sha256 `124c1e4f…`) is under
`attempt_A_launch_error/` and attempt B's own 41-file set (sha256 `021712cf…`) is listed by
`SHA256SUMS_attemptB_original.txt`. AI-assisted (DeepSeek Harness agent `u2-etth1-runner`, delegated by the
lead), ENGINEERING_ONLY. Prepared under `R1-T1-NODE-EXPANSION`; no label, evaluation, evidence or G.1b file was
read or written; no deletion, no push, no GPU lease.

## 1. Inputs and binding

| item | value |
|---|---|
| kit review | `docs/r1/reviews/ETTH1_KIT_REVIEW_20261125.md`, sha256 `73df58d5f929d6922223c3b33a926232e5e5189a774cc6a3b7364e5768869202`, verdict ACCEPTED (no BLOCKING/MAJOR) |
| harness branch @ pin | `mac-trackg-etth1-20261125` @ `3a06d86721b0c1826b165b68a9781a561e4993f4` (base `c025f89aeafc2199bf3487b4bcaa16678273c702`) |
| worktree | `/home/dowling/r1_trackg_20261125/harness_etth1`, at the pin, clean except `?? nodes/gc7rc_etth1/data` (the setup link) |
| node / task | `gc7rc_etth1` — 1GC-7RC Task 6, ETTh1 multivariate 336→96 forecasting, DLinear baseline, MSE |
| run id / unit | `systemd-run --user --scope --unit=u2-etth1-census-20261125T1220Z` |
| host | TASL-2, Linux 6.8.0-149-generic x86_64, euid 1008, ptrace_scope 1, Python 3.12.16 |
| env | pinned `torch312` (`/home/dowling/r1_tracks/t1_tasl/envs/torch312`), freeze `d2e70fe4…`, 77 packages, torch 2.6.0+cu124, numpy 2.5.4, uv 0.13.6 |
| data | `/home/dowling/r1_engineering/etth1_port_20261125/data/gc7rc_etth1` (read-only, symlinked into the node), manifest `eacc7e69…` |
| GPU | **none used**: RTX 4090 `GPU-4d623e76-7587-ee15-a633-46f60d220d94` (driver 535.309.01) stayed at 353 MiB / 0 % with no compute apps before and after; `CUDA_VISIBLE_DEVICES=""` and `gpu_uuids []` in every run; `gpu0.lock` not held and not touched |

Transfer of the reviewed kit to TASL-2 was the already-published worktree at the pin; nothing was fetched,
patched, committed or pushed by this task.

## 2. What ran (valid smoke, attempt B)

Delegated scope (verified inside: scope cgroup writable, `memory.max = 8589934592`, `memory.swap.max = 0`), CPU
affinity 16-31 for the driver and `--cpus 16-31` for the runs, no GPU, `PYTHONDONTWRITEBYTECODE=1`, the pinned
env's `bin` first on `PATH` **and** the absolute pinned interpreter:

```
systemd-run --user --scope --unit=u2-etth1-census-20261125T1220Z --collect \
  -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 \
  env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 \
  U2_BASE=/home/dowling/r1_engineering/etth1_port_20261125/u2_census_smoke_20261125B \
  PATH=/home/dowling/r1_tracks/t1_tasl/envs/torch312/bin:$PATH \
  VIRTUAL_ENV=/home/dowling/r1_tracks/t1_tasl/envs/torch312 \
  taskset -c 16-31 /home/dowling/r1_tracks/t1_tasl/envs/torch312/bin/python run_u2_smoke.py
```

`run_u2_smoke.py` (sha256 `ffc9659635b2a0f762edf71cef570fc0e20021429fdacb9486b822c71ca970cd`, captured) calls the
reviewed module's own `tests.trackg.port_smoke_gpu.main()` with the kit's documented flags (`--node`, `--cpus`,
`--memory-limit`, `--runs-root`, `--provisional-timeout 900`) and the real data; the only in-memory deviation is
the CPU-only guard — the reviewed CLI refuses a GPU-less invocation for this GPU-capable torch node
(`--gpu-uuid is required for gc7rc_etth1`; `CPU_ONLY_NODES` unchanged in the kit), so the driver overrides
`port_smoke_gpu.CPU_ONLY_NODES` for this process only. **No repository file was changed** (worktree status before
and after: only the setup data link). Runs root is outside the repository:
`/home/dowling/r1_engineering/etth1_port_20261125/u2_census_smoke_20261125B/runs`.

Smoke wall: **89.951 s** (12:17:33–12:19:03Z), `SMOKE_MAIN_RC=0`, `CHECKLIST_E_PASSED gc7rc_etth1`. Timeout was
the kit's provisional 900 s (`provisional (measuring run)`); no run timed out or was killed.

| run | decision | outcome | val_mse | sealed test_mse | wall (info only) |
|---|---|---|---|---|---|
| `s000_baseline` | baseline (B1) | ok | **0.654580** | 0.375348 | 10.908 s |
| `s001` | not_run_refused (`scope_violation`, frozen path) | — | — | — | — |
| `s002` | discarded_divergent (`non_finite_loss`) | divergent | — | nan | 11.009 s |
| `s003` | kept (E1) | ok | 0.644269 | 0.373813 | 11.071 s |
| `E1` | declared edit | ok | 0.644269 | 0.373813 | 11.026 s |
| `E2` | declared edit | ok | 0.693659 | 0.392145 | 10.870 s |
| `E3` | declared edit | ok | 0.658426 | 0.369918 | 11.392 s |
| `E4` | declared edit | ok | 1.715713 | 1.243953 | 11.506 s |
| `B2` | baseline repeat (B2) | ok | **0.654580** | 0.375348 | 11.028 s |

All values are the run records' `outcome.value` (selection metric `val_mse`, R1-TRACKG-ROLE) and the sealed
`AR_TEST test_mse` channel; the manager never sees the test metric. The E1–E4/B2 values equal the kit's real-data
CPU smoke (kit report §4) to the digit; wall times are ~3 s slower than that run (10.87–11.51 s vs 7.61–8.04 s;
that smoke used CPUs 0-3), so they are INFO ONLY, not a measurement, and reflect the shared host/affinity.

## 3. Attempt A (preserved, disclosed) and the two preparatory aborts

- **Attempt A** (12:12:29–12:13:27Z, tree `…/u2_census_smoke_20261125/`, preserved unmodified): the same smoke
  was launched without the pinned env's `bin` on `PATH`. In the reviewed code the campaign runs are started as
  `python3` resolved from `PATH` — `tests/trackg/port_support.py:run_smoke` passes `interpreter=sys.executable`
  only to the per-edit runs, while `src/autoresearch/trackg/smoke.py:run_smoke_campaign` uses the runner's default
  `"python3"` — so `s000_baseline`/`s002`/`s003` ran `/usr/bin/python3` (3.10.12, no torch), exited 1 with
  `ModuleNotFoundError: No module named 'torch'` (their `determinism.settings` record `torch_absent:
  ModuleNotFoundError`), and `check_baseline_log` raised `loss_regex matched no line of the baseline log`: the
  smoke **STOPped** (`CHECKLIST_E_PASSED` absent). The per-edit runs E1–E4/B2, which got the absolute pinned
  interpreter, all ran ok and reproduced the kit's values (B2 `0.654580`/`0.375348`). Root cause was the launch
  environment, not the kit, host, data, pins or isolation; the accepted Track G smoke template exports
  `PATH=…/envs/torch312/bin:$PATH` (TRACKG_U2_ISO_UNITS_REVIEW_R3_20261119.md §3). Attempt A's full evidence
  (48 files incl. its original SHA256SUMS, `STOP_DIAGNOSIS.txt`, `ssh_env.txt`, all run records/logs) is under
  `attempt_A_launch_error/`; its original capture SHA256SUMS sha256 is
  `124c1e4f886e1a284c0b4583312c083229e03b2aca364b8654314ed0847f8a56`.
- **Preflight-only abort #1** (12:12:01Z): the driver stopped in its own preflight (cgroup path join) before any
  run; `runs/` was absent afterwards. The failed launch's driver logs were overwritten by attempt A's launch log.
- **Preflight-only abort #2** (12:17:12Z): the first corrected launch did not carry `U2_BASE`, so the driver
  refused because attempt A's `runs/` exists; no run was started and attempt B's `runs/` was absent afterwards.
  Fixed by setting `U2_BASE` (the only change), then attempt B.
- After the lead's authorization (12:16Z) exactly **one** corrected launch was made (attempt B). No retry after it.
  The lead's authorization and this accounting are in `commands.txt` / `ATTEMPT_LOG.txt`.

## 4. Determinism (fixed seeds 8001/8001, CPU)

- B2 repeats B1 exactly: `val_mse 0.654580` = B1; sealed `test_mse 0.375348` = B1; **identical**
  `run.log` sha256 `d8bbb0c7…` and result-channel sha256 `8cfc9395…` for both runs.
- `s003` repeats `E1` exactly (`0.644269`/`0.373813`, identical log sha `bfa8f5de…` and channel `d23d2cb7…`).
- `determinism.shim_loaded: true` and `not_forced: ["dataloader_workers"]` in every executed run; forced settings
  `cudnn.benchmark=False`, `torch.use_deterministic_algorithms(True)`, `set_num_threads=4`,
  `CUBLAS_WORKSPACE_CONFIG=:4096:8`, `PYTHONHASHSEED=0`, `AR_DEVICE cpu`, torch 2.6.0+cu124.
- This is a CPU determinism check only; GPU determinism (review c4) remains unmeasured (§8).

## 5. Pins, spec, data, environment — recomputed on TASL-2 and equal to the accepted values

Recomputed in the smoke's preflight with the kit's own frozen-pin helpers
(`isolation.frozen_file_hashes` + `committed_view`), not copied from the report:

| field | value (recomputed) |
|---|---|
| `node_spec_sha256` (loader canonical) | `8f874c50f66273e0655bfc9ccdad24a50c0fdb629f88ba7d4d60b13f2fcf2e0c` |
| spec raw sha256 (YAML bytes) | `9391f718bd7669438189f45b48a920786a6ca5a51854bd861b0f945ea3d00c22` |
| **committed pin** (frozen files, no data link) | `818b8f6e8ec6473f15c33ed58393e7cee8b8e8b0a71645576439929efb20bf27` |
| deployed pin (with the host-specific data link; per-run record field) | `e314858234bb378dce4cad5cf0492cfa1ee76561c231e756b90f301672ddec93` |
| `edits_manifest_sha256` | `ba31fed3bb67c0d78825a0d026058cbeb3a0261971fe8a4766f138687b232306` |
| `data_manifest_sha256` | `eacc7e69f45fed3e7eb0c9bb76cf5c18387bcae4ba226a24812dc409c0b51e1b` |
| `series.npy` (recomputed) | `32a0ad070e7536e7099725098b24b74c775bc897d58f3c5868399a6f86c8d850`, 487,888 B |
| pinned source CSV (recomputed, pinned URL) | `f18de3ad269cef59bb07b5438d79bb3042d3be49bdeecf01c1cd6d29695ee066`, 2,589,657 B |
| node `ar_isolated.py` = harness master | `37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610` |
| env freeze | `d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42` (77 packages) |
| run budget | `steps 2000`, batch 128, no wall-clock key; `frozen_pin_sha256` = deployed pin in every run record (`s001` included) |

Data root is read-only (`dr-xr-xr-x`; files `-r--r--r--`), outside the repository, and no data file is in the
kit tree. `git rev-parse HEAD` = the pin before and after; worktree status unchanged; no new repository file.

## 6. Isolation, resources, no GPU

- **Isolation, every executed row** (`s000_baseline`, `s002`, `s003`, `E1`–`E4`, `B2`): `effective: true`,
  `waivers: {}`, `exceptions: []`; 16 frozen entries checked, none changed (`frozen_files_changed: []`);
  both gate rows pass (`s001` refused `scope_violation`, `s002` divergent `non_finite_loss`); full cgroup per run
  under the smoke scope, `cgroup.kill` cleanup, no leftover processes/timed-out runs, result channel intact.
- **Memory:** scope `memory.peak` **851,775,488 B ≈ 812 MiB** (cgroup v2 `memory.peak` covers the cgroup and its
  descendants) against `memory.max` 8,589,934,592 B and `memory.swap.max` 0. Per-run cgroup peak files were not
  readable because enabling the memory controller below the scope returned `EBUSY` (`memory.swap.max`/`memory.max`
  still bound the whole scope); disclosed rather than fabricated — the scope peak is the resource number.
- **Disk:** runs root 3,012,805 B (per-run working copies 101–212 KB); data root 3,086,791 B; home available
  372,946,251,776 B (~346.6 GiB) after; captures 237,813 B at generation (final combined set 656 KiB).
- **CPU:** driver and runs on CPUs 16-31 (`--cpus 16-31`), 32-CPU host, ptrace_scope 1, euid 1008 (non-root).
- **No GPU:** `CUDA_VISIBLE_DEVICES=""` and `gpu_uuids []` in every executed record; `torch.cuda.device_count()
  = 0` in the launching process; the only RTX 4090 was idle (353 MiB static / 0 %, no compute apps) before and
  after; `~/r1_locks/gpu0.lock` was free before and after and its stat is unchanged. No GPU lease was taken.

## 7. What this establishes

For the REVIEW ACCEPTED kit at the accepted pins, on TASL-2, CPU-only: the standard stub-manager census smoke
(baseline, frozen-diff refusal, broken-diff divergence, E1 through the stub manager, every declared edit, a
fixed-seed baseline repeat) passes checklist E on the real data at the full 2,000-step budget, with effective
isolation on every executed row, deterministic repeats, the accepted pins/data/env and no GPU. B1/B2
`val_mse = 0.654580`; sealed test MSE 0.375348 (selection is on validation; the val-vs-test gap is the split
property the review checked, not a bug).

## 8. What this does not establish (limits, for the census record)

- **Not the GPU census.** The review's c2 requires the smoke on TASL-2 with a GPU **by UUID**, recording GPU
  model/UUID/driver/VRAM, and c4 requires GPU determinism. This run is CPU-only by the task's instruction and
  consumes **no** GPU lease; c2/c4 remain open. The measured timeout basis (`3 × slowest measured`, R1-G1B-TIMEOUT)
  is therefore not set: the timeout stayed provisional (900 s).
- **No measurement/noise floor/D21/D28/label/evidence/G.1b** is claimed; the wall times are INFO ONLY on CPU.
- **Kit usability finding (not a defect, paper-side):** the census-smoke entry point starts its campaign runs as
  `python3` from `PATH`, so the launching environment must have the pinned env's `bin` first on `PATH` — the
  accepted Track G smoke template already does this, but the kit note says only "with the node's Python
  environment". Also, a GPU-less invocation of the documented CLI is refused for this node because it is not in
  `CPU_ONLY_NODES`; a future CPU-only census would need a documented flag (a kit change would trigger c8
  re-review). Neither finding changes the accepted pins; flag them in the G.1b launch note.
- The passes are for the smoke run set; they do not establish G.1b-level equivalence between the stub manager and
  a live GPU census run.

## 9. Captures

`ETTH1_U2_RESULT_20261125_captures/` (92 files, 656 KiB; `sha256sum -c SHA256SUMS` rc 0;
`SHA256SUMS` sha256 `c943b9f81b3479ddc11db520bd8b50aa073c2911a6cc317b10bcb92b91298800`):

- attempt B (valid smoke): `preflight.json` (pins/data/env/GPU/affinity/cgroup/launch env), `summary.json` /
  `summary.txt` (29 checks), `smoke_stdout.txt` (JSON lines + `CHECKLIST_E_PASSED`), `run_records/` (9
  `run_record.json`), `run_logs/` and `result_channels/` (8 each; `s001` not executed), `env.txt`,
  `torch312.freeze.txt`, `pins.json`, `gc7rc_etth1.yaml`, `data_manifest.json`, `edits_manifest.json`,
  `git_head.txt`, `git_status.txt`, `git_diffstat_vs_base.txt`, `gpu_state_pre.txt`, `commands.txt`,
  `run_u2_smoke.py`, `SHA256SUMS_attemptB_original.txt` (attempt B's 41-file original set, sha256 `021712cf…`);
- `attempt_A_launch_error/`: attempt A's preserved evidence, including `STOP_DIAGNOSIS.txt`, `ssh_env.txt`,
  `summary.json`/`summary.txt` (STOP), all its run records/logs and its original `SHA256SUMS` (sha256
  `124c1e4f…`);
- `ATTEMPT_LOG.txt`: attempts, aborts, authorization and hashes;
- combined `SHA256SUMS` over all of the above.

AI-assisted: DeepSeek Harness agent `u2-etth1-runner` (delegated by the lead), 25 Nov 2026, ENGINEERING_ONLY.
No push, no deletion, no GPU lease, T1/Track P archives untouched.
