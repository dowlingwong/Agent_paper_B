# U2 census smoke — Track G kit `mlgym_titanic` (MLGym Titanic), TASL-2, CPU-only — result, 25 November 2026

**Verdict: STOP** (CPU-only U2 census smoke; no PASS). The valid attempt is **attempt B**: the reviewed
kit's own stub-manager smoke `python -m tests.trackg.port_smoke_gpu --node mlgym_titanic` at the node's full
150,000-step budget on the real data, run CPU-only in a delegated 8G/swap0 cgroup scope on TASL-2 on the
**CPUs 8-11 P-cores**, with `CUDA_VISIBLE_DEVICES=""`, no GPU and no GPU lease. It ran and then **stopped**:
five runs are fine and reproduce the kit-accepted checklist-E values to the digit — `s000_baseline`
**val_accuracy 0.775281 / sealed test_accuracy 0.763158** (141.405 s), the frozen-path diff refused
`scope_violation`, the broken diff divergent `non_finite_loss`, `s003` (= E1 through the stub manager)
0.803371/0.772727 (131.545 s), `E3` 0.792135/0.784689 (162.183 s), `E4` 0.792135/0.746411 (143.438 s) —
but `E1` died with **SIGSEGV** after 0.532 s and `E2` with **SIGILL** after 0.660 s
(`infrastructure_failure / killed`, before the determinism shim loaded), and the repeat baseline `B2`
diverged (`nonzero_exit` rc 1 after 1.563 s; worker "connection closed (worker exit 1)") with its repeat
determinism record not loaded. The module's own `check_smoke` then asserted on B2's determinism settings, the
smoke exited **`SMOKE_MAIN_RC=1` without `CHECKLIST_E_PASSED`**, and attempt B is a STOP. Per the lead's
instruction exactly **one** launch of attempt B was made and there was **no retry**. **B1/B2 fixed-seed
determinism is therefore not established** (B1 ok, B2 failed), no census measured-run-time/timeout is claimed,
and review conditions c2/c4 remain open. **Attempt A** — the first launch, pinned to CPUs 16-31, which on
this host are the 16 E-cores — was aborted by lead authorization after its baseline projected far beyond the
G.1b chunk-schema cap; it is preserved unmodified and disclosed in §10.

Captures (89 files, 2,569,042 B on the host, no data copied) are in
`TITANIC_U2_RESULT_20261125_captures/` beside this file, with `SHA256SUMS` sha256
**`a6f35989a1dc11d5e1d1432d1149e7d8bed1b2cfe02c151c35616280b7627554`** (`sha256sum -c` rc 0, verified
on the Mac after transfer); attempt A's curated evidence subset is under `attempt_A_ecores_aborted/`.
AI-assisted (DeepSeek Harness agent `u2-titanic-runner`, delegated by the lead), ENGINEERING_ONLY. Prepared
under `R1-T1-NODE-EXPANSION`; no label campaign, evaluation, evidence or G.1b file was read or written; no
deletion, no push, no GPU lease.

## 1. Inputs and binding

| item | value |
|---|---|
| kit review | `docs/r1/reviews/TITANIC_KIT_REVIEW_20261125.md`, sha256 `3c1d98601148485f5b319f1de1b8e5f9a688c9d3207a0aefe4554873a3344574`, verdict **ACCEPTED** (no BLOCKING/MAJOR) |
| kit report | `docs/r1/reports/tasl_chain_20261122/TITANIC_KIT_20261125.md`, sha256 `a1844bfef44e742795e6b74eef1738f70bec228bd4e13d6d58aa2eb13457ed10` |
| harness branch @ pin | `mac-trackg-titanic-20261125` @ `3a67042ba7e4211feb9681524f3879643c8cf635` (base `c025f89aeafc2199bf3487b4bcaa16678273c702`) |
| worktree | `/home/dowling/r1_trackp/wt/titanic-20261125`, at the pin, clean except `?? third_party/mlgym/nodes/mlgym_titanic/data` (the setup link, made by the kit's `setup_command`; unchanged by the smoke) |
| node / task | `mlgym_titanic` — MLGym `titanicSurvival` (Kaggle Titanic tables forwarded by MLGym commit `9d40c1b5…`), CPU-only, fixed 150,000 optimizer-step budget, selection `val_accuracy`, sealed `test_accuracy` |
| host | TASL-2, `Intel Core i9-14900KF`, 32 logical CPUs (CPUs 0-15 = 8 P-cores with SMT, max 5.8-6.1 GHz; CPUs 16-31 = 16 E-cores, max 4.4 GHz), Linux 6.8.0-149-generic x86_64, euid 1008, ptrace_scope 1 |
| env | pinned `torch312` (`/home/dowling/r1_tracks/t1_tasl/envs/torch312`): Python 3.12.16, torch 2.6.0+cu124, numpy 2.5.4, pandas 3.1.1, uv 0.13.6; `uv pip freeze` sha256 `d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42` (77 packages) — equal to the census freeze |
| data | `/home/dowling/r1_engineering/titanic_20261125/data/mlgym_titanic`, read-only (`dr-xr-xr-x`, files `-r--r--r--`), outside the repository; manifest `c8ccedd0eb620fb0d049fef377e3ae29f6c0ff5c04184b9335d5a419821769e4` |
| GPU | **none used**: RTX 4090 `GPU-4d623e76-7587-ee15-a633-46f60d220d94` (driver 535.309.01) idle at 0 % with 353 MiB static, no compute apps before/after; `gpu0.lock` never held and its stat is unchanged; `CUDA_VISIBLE_DEVICES=""` and `gpu_uuids []` in every run |

Transfer of the reviewed kit to TASL-2 was the already-published worktree at the pin; nothing was fetched,
patched, committed or pushed by this task. The `setup_command` was re-run as the deployment step: it
re-verified the three pinned files (no download needed — the manifest was present) and re-linked
`node_dir/data`; the data root stayed read-only.

## 2. What ran (attempt B, the valid attempt)

Delegated scope (verified inside: scope cgroup writable, `memory.max = 8589934592`, `memory.swap.max = 0`,
controllers `memory pids`, the scope's `driver` sub-cgroup used so the memory controller could be enabled for
the per-run cgroups and their `memory.peak` read), CPU affinity **8-11** for the driver and `--cpus 8-11` for
the runs, no GPU, `PYTHONDONTWRITEBYTECODE=1`, the pinned env's `bin` **first on `PATH`** and the absolute
pinned interpreter (the reviewed campaign engine starts its runs as `python3` from `PATH`), and
`AR_TEST_CGROUP_PARENT` exported from the scope:

```
systemd-run --user --scope --unit=u2-titanic-census-20261125T1304Z --collect \
  -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 \
  env PATH=/home/dowling/r1_tracks/t1_tasl/envs/torch312/bin:$PATH \
      VIRTUAL_ENV=/home/dowling/r1_tracks/t1_tasl/envs/torch312 CUDA_VISIBLE_DEVICES= \
      PYTHONDONTWRITEBYTECODE=1 AR_TRACKG_DATA_ROOT=/home/dowling/r1_engineering/titanic_20261125/data \
      U2_BASE=<attempt-B root> U2_CPUS=8-11 \
  taskset -c 8-11 bash <attempt-B root>/scripts/scope_inner.sh
# inside: AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$(cut -d: -f3 /proc/self/cgroup)
taskset -c 8-11 <torch312>/bin/python -m tests.trackg.port_smoke_gpu --node mlgym_titanic --cpus 8-11 \
  --memory-limit "external: systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 (enforced cgroup)" \
  --runs-root /home/dowling/r1_engineering/titanic_20261125/u2_census_smoke_20261125B/runs \
  --provisional-timeout 1800
```

In-scope sanity before any run: `torch 2.6.0+cu124`, `torch.cuda.device_count() == 0`,
`numpy 2.5.4`, `pandas 3.1.1`, `PATH` `python3` = the pinned env's `python3`. The driver ran
**one** module invocation; smoke wall **710.838 s** (13:04:11–13:16:01Z), `SMOKE_MAIN_RC=1`,
`CHECKLIST_E_PASSED` absent.

| run | decision | outcome | val_accuracy | sealed test_accuracy | wall (s) | rc |
|---|---|---|---|---|---|---|
| `s000_baseline` (B1) | baseline | ok | **0.775281** | 0.763158 | 141.405 | 0 |
| `s001` | not_run_refused | `scope_violation` (frozen path) | – | – | – | – |
| `s002` | discarded_divergent | divergent `non_finite_loss` | – | (0.0 recorded) | 128.603 | 0 |
| `s003` | kept (E1 via stub manager) | ok | 0.803371 | 0.772727 | 131.545 | 0 |
| `E1` | applied | **infrastructure_failure / killed** | – | – | **0.532** | **-11 (SIGSEGV)** |
| `E2` | applied | **infrastructure_failure / killed** | – | – | **0.660** | **-4 (SIGILL)** |
| `E3` | applied | ok | 0.792135 | 0.784689 | 162.183 | 0 |
| `E4` | applied | ok | 0.792135 | 0.746411 | 143.438 | 0 |
| `B2` (baseline repeat) | no diff (repeat) | **divergent `nonzero_exit`** | – | – | **1.563** | **1** |

All values are the run records' `outcome.value` (selection metric `val_accuracy`) and the sealed
`AR_TEST test_accuracy` channel, which the manager view never shows. The five completed runs equal the
kit-accepted checklist-E smoke to the digit (kit report §7: s000 0.775281, s003/E1 0.803371, E2 0.775281,
E3 0.792135, E4 0.792135, B2 0.775281; sealed values match the run records) — the kit, the data, the pinned
environment and the isolation behave as accepted at this budget on TASL-2.

## 3. Why attempt B is a STOP

- **`E1` / `E2`** were launched and their declared diffs were applied (records `diff.status: applied`), but the
  run processes died by **SIGSEGV** (0.532 s) and **SIGILL** (0.660 s). They died **before the determinism
  shim loaded** (their records carry `shim_loaded: false` and the "shim_not_loaded" settings) and before any
  node code ran; the repeat baseline record is the only other such run. Their cgroup memory peaks (192,991,232
  B and 208,683,008 B) are consistent with the shim's torch import; the VmHWM sample caught only 13.7 MB.
- **`B2`** (baseline repeat, no diff) started — `AR_SEEDS`, `AR_DATA`, `AR_SPLIT` are in its log — and then its
  worker died: `AR_ERROR worker train: connection closed ([Errno 104] Connection reset by peer) (worker exit 1)`;
  the parent exited rc 1 in 1.563 s and the repeat determinism record was not loaded.
- The reviewed module's `check_smoke` asserts the repeat run's forced determinism (`port_support.py:546`), so it
  raised; the smoke exited **1** and never printed `CHECKLIST_E_PASSED`. Under the kit's own contract that is a
  STOP, not a pass with caveats.
- **No retry**: the lead authorized aborting attempt A and exactly **one** corrected attempt B, with STOP
  reported if B did not pass. No further launch was made.
- The immediate cause cannot be read from the kernel from this account (uid 1008 is not in `adm`, so
  `/var/log/kern.log`/`syslog` are unreadable; apport captured no coredump for this user). What can be said:
  `/proc/sys/kernel/tainted = 4097` = the proprietary + unsigned-module bits only (the NVIDIA driver) — **no
  MCE (bit 3) and no oops (bit 6)**; memory pressure was zero (`/proc/pressure/memory` all 0, no OOM kill, scope
  `memory.events` `oom_kill 0`, peak 641,863,680 B of 8 GiB); and a 5-hour scan of the concurrent agents'
  run records found **no other negative-return-code run**, so it was not a host-wide crash storm. The kit's own
  report already documents one sporadic segfault of an unrelated House Prices pandas test inside a delegated
  scope on this shared host (TITANIC_KIT_20261125.md §9.6). The failure is treated as a sporadic
  host/runtime process crash in this one smoke, not as a kit, pin, data or isolation defect: every executed
  record has `isolation.effective: true`, `waivers {}`, `exceptions []`, 16 frozen entries checked, none
  changed, and the records' `log_sha256`/`result_channel_sha256` match the captured files.

## 4. Determinism (fixed seeds 8001/8001, CPU) — not established

- **`s000_baseline` (B1)** ran under the forced settings (`determinism.shim_loaded: true`,
  `not_forced: ["dataloader_workers"]`, `cudnn.benchmark=False`, `torch.use_deterministic_algorithms(True)`,
  `torch.set_num_threads=4`, `CUBLAS_WORKSPACE_CONFIG=:4096:8`, `PYTHONHASHSEED=0`, torch 2.6.0+cu124,
  `AR_DEVICE cpu`) and is digit-identical to the kit-accepted B1.
- **`s003`** (= E1 through the stub manager) equals the kit-accepted E1 (0.803371/0.772727) and has the forced
  settings; `E3`/`E4` ran with the forced settings too.
- **The fixed-seed repeat `B2` failed**, so the required "B2 equals B1 to the digit" check could not be made.
  **B1/B2 determinism is therefore NOT established by this smoke** (review condition c4 remains open); the
  value-level agreement with the kit-accepted smoke is not a substitute for the repeat.

## 5. Pins, spec, data, environment — recomputed on TASL-2 and equal to the accepted values

Recomputed in the smoke's preflight with the kit's own frozen-pin helpers (`isolation.frozen_file_hashes` +
`noise_floor.committed_view` / `frozen_pin_sha256`, the loader's canonical `raw_sha256`, `sha256_file`), not
copied from the report:

| field | value (recomputed) |
|---|---|
| `node_spec_sha256` (loader canonical) | `059fd0d50059b4627382979fc9064a9f223f79e06b616eba195eefbb3f3380c1` |
| spec raw sha256 (YAML bytes) | `08876175e02d498b10680d3c35b5969b731404c513ec3fffc858374fa484ddac` |
| **committed pin** (15 frozen files, no data link) | `0368a73d86f9cf8d695fe39cc6e4f3aa54f4c882c95ab66ddc146b519af80086` |
| deployed pin (with the host `data` link; per-run record field) | `4c0399d9ab516a72943c0ce17f2c070e8da8219ea7777a7c8e2c7fce58ecd107` |
| `edits_manifest_sha256` | `fd464c6e1bfc1ab13aded048e1feba97b2844f8fe537f3b0b8eaf1ae3e4a9bce` |
| `data_manifest_sha256` | `c8ccedd0eb620fb0d049fef377e3ae29f6c0ff5c04184b9335d5a419821769e4` |
| node `ar_isolated.py` = harness master | `37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610` |
| env freeze (torch312) | `d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42` (77 packages, Python 3.12.16) |
| run budget | `steps 150000`; `frozen_pin_sha256` = deployed pin in every run record (`s001` included) |
| data files (recomputed, read-only) | `train.csv` `4a437fde…` 60,302 B; `test.csv` `5c78320a…` 28,210 B; `ground_truth.csv` `af6609cd…` 2,839 B; root `dr-xr-xr-x`, files `-r--r--r--`, outside the repository |

`git rev-parse HEAD` = the pin before and after; worktree status unchanged (only the setup `data` link); no new
repository file; the CPU-only registration is active (`mlgym_titanic` in `CPU_ONLY_NODES`, `torch_node: true`,
`has_make: true` in the node's SMOKE entry — the reviewed kit's CPU-only path was used, no override).

## 6. Isolation, resources, no GPU

- **Isolation, every executed row** (`s000_baseline`, `s002`, `s003`, `E1`, `E2`, `E3`, `E4`, `B2`):
  `effective: true`, `waivers: {}`, `exceptions: []`; `frozen_files_checked: 16`, `frozen_files_changed: []`;
  per-run cgroup v2 under the smoke scope with `cgroup.kill` cleanup (`kill.empty_after: true`), no leftover
  processes; `ptrace_scope: 1`; the two gate rows pass (`s001` refused `scope_violation`, `s002` divergent
  `non_finite_loss`); no run was timed out or killed by the runner (`killed_with: null`, `timed_out: false`);
  `determinism.not_forced == ["dataloader_workers"]` on the five completed runs; `result_channel` has exactly
  one selection line and one sealed-test line and the log none; the log has 15,000 loss lines and no carriage
  returns on every completed run.
- **Memory:** scope `memory.peak` **641,863,680 B ≈ 612 MiB** against `memory.max` 8,589,934,592 B and
  `memory.swap.max` 0; `per-run cgroup memory.peak` was readable because the memory controller was enabled in
  the scope (597,000,192 B baseline; 596-620 MB range for the completed runs; E1/E2 peaked at 192,991,232 B /
  208,683,008 B, consistent with dying during startup), plus the `/proc/*/VmHWM` sampler (596-620 MB for the
  completed runs). No OOM kill.
- **Disk:** runs root (`…/u2_census_smoke_20261125B/runs`) **4,662,922 B**; data root 97,270 B; home available
  **371,422,564,352 B** after; captures 2,569,042 B on the host; nothing written into the repository.
- **CPU:** host 32 logical CPUs; driver and runs on CPUs 8-11 (P-cores); 4 threads per run; ptrace_scope 1;
  euid 1008 (non-root).
- **No GPU:** `CUDA_VISIBLE_DEVICES=""` and `gpu_uuids []` in every executed record; `torch.cuda.device_count()
  = 0` in the driver; the only RTX 4090 was idle (353 MiB static / 0 %) with no compute apps before and after;
  `~/r1_locks/gpu0.lock` was free before and after and its stat is unchanged. No GPU lease was taken.

## 7. Measured run time and timeout — informational only, NOT claimed

From the five completed census records (B1 = `s000_baseline`, E3, E4; B2/E1/E2 did not complete) the slowest
run is `E3` at **162.183 s**; `ceil` = **measured_run_seconds 163 s**, within the G.1b chunk-schema range
(0, 300], and `3 × 163 = 489.0 s` with `timeout_factor 3.0`, `stop_on_timeout: true`. **This is not claimed as
a census result**: the smoke is a STOP, so no chunk fields (measured timeout, Pins → chunk) are derived or
published from it, and the smoke itself ran with the kit's provisional 1800 s (first measuring run). A future
authorized re-run that passes would set the timeout from its own records.

## 8. What this establishes / does not establish

- **Establishes (engineering evidence, not a census PASS):** on TASL-2 CPU-only, at the reviewed pin, the
  kit's data/env/pins/isolation machinery works at the full 150,000-step budget; the five completed runs are
  digit-identical to the kit-accepted checklist-E values; every executed record has effective isolation with
  no waivers/exceptions and no frozen-file change; the P-core CPU timing of a full run is ~141-162 s (the
  kit-accepted range was 127-156 s on the same CPU set).
- **Does not establish:** the U2 census PASS; a measured-run-time/timeout basis (review c2); B1/B2 fixed-seed
  determinism (c4); any GPU determinism, GPU census, noise floor/D21/D28, label campaign/evidence use, or
  G.1b readiness. No sealed test accuracy was used for selection; the sealed values are recorded from the run
  records only, and the manager view never shows them.

## 9. Attempts (A/B disclosure) and the CPU-set finding

- **Attempt A** (13:55:25Z launch, unit `u2-titanic-census-20261125T1256Z.scope`) was launched per the task
  instruction with `taskset 16-31`. On this host CPUs **0-15 are the 8 P-cores** (5.8-6.1 GHz, SMT) and CPUs
  **16-31 are the 16 E-cores** (4.4 GHz, no SMT). Baseline `s000_baseline` reached only step 97,440/150,000 in
  458 s (~213 steps/s vs the kit's ~1095 steps/s on CPUs 8-11), projecting >300 s per census run — above the
  chunk-schema `measured_run_seconds` cap (0, 300] and review c2's limit. A same-4-thread raw-torch probe on
  the host measured 2,862 steps/s on CPUs 8-11 vs 1,210 steps/s on 16-31 for the same loop (2.4×), and the
  sibling Forest Cover U2 smoke was sharing 16-31 at the time. **The lead authorized aborting A and making one
  corrected attempt B on CPUs 8-11** (13:02Z); A was stopped cleanly (`systemctl --user stop`, stop_rc 0, no
  leftovers) at 13:03:05Z at step 97,440 and **preserved unmodified** at
  `/home/dowling/r1_engineering/titanic_20261125/u2_census_smoke_20261125_attemptA_ecores_aborted`
  (scripts, raw preflight/probe/launch/scope logs, partial `s000_baseline` run tree, `ATTEMPT_A_ABORTED.txt`;
  no run record or result is claimed from it). It is excluded from the U2 record.
- **Attempt B** (13:04:10Z launch, unit `u2-titanic-census-20261125T1304Z.scope`) — the one corrected launch on
  CPUs 8-11 — is the attempt documented above; it ran to its own STOP with no retry.
- Pre-review kit-development attempts (preserved on the host throughout, excluded from this record):
  `cpu_smoke_runs_attempt1_module_not_found/` (PATH interpreter without pandas; a chmod-through-the-data-link
  `PermissionError`), `cpu_smoke_runs_attempt2_e4_nonfinite/` (E4 draft non-finite feature), and the accepted
  kit smoke `cpu_smoke_runs/` (`CHECKLIST_E_PASSED mlgym_titanic`, CPUs 8-11).
- **Recommendation (for the lead, not taken here):** a further authorized re-run of the same command on CPUs
  8-11 when the host is calm (attempt B's five completed runs show the kit is usable: 141-162 s/run,
  measured_run_seconds 163 s ≤ 300, timeout 3× = 489 s), or accept the kit's own accepted checklist-E smoke as
  the census evidence; also consider whether the harness should treat a sporadic `infrastructure_failure`
  (`killed` by a signal before any node code) as retryable under a reviewed rule, since this STOP is not a
  kit/data/pin/isolation defect.

## 10. Captures and evidence roots

`TITANIC_U2_RESULT_20261125_captures/` (89 files, 2,569,042 B on the host; `sha256sum -c SHA256SUMS` rc 0 both
on TASL-2 and on the Mac after transfer; `SHA256SUMS` sha256
`a6f35989a1dc11d5e1d1432d1149e7d8bed1b2cfe02c151c35616280b7627554`):

- attempt B (valid attempt): `preflight.json` (pins/data/env/smoke-entry/GPU/affinity), `pins.json`, `env.txt`,
  `torch312.freeze.txt`, `mlgym_titanic.yaml`, `data_manifest.json`, `edits_manifest.json`, `git_head.txt`,
  `git_status.txt`, `git_diffstat_vs_base.txt`, `gpu_state_pre.txt`, `gpu_state_post.txt`, `setup.log`,
  `scope_probe.log`, `launch_env.txt`, `launch.out`, `scope_inner.log`, `scope_memory_*` (max/swap/peak/
  events/stat), `monitor.json` (per-run cgroup memory peaks and VmHWM), `smoke_stdout.txt` (the JSON lines +
  the `check_smoke` traceback), `summary.json` / `summary.txt` (the check table), `run_records/` (9),
  `run_logs/` and `result_channels/` (8 each; `s001` not executed), `ATTEMPT_LOG.txt`, `ATTEMPT_B_STOP.txt`,
  `commands.txt`, and the driver scripts under `scripts/`;
- `attempt_A_ecores_aborted/`: attempt A's curated evidence, including `ATTEMPT_A_ABORTED.txt`,
  `preflight.json`/`pins.json`/`env.txt`, `scope_probe.log`, `launch_env.txt`/`launch.out`,
  `scope_inner.log`, `monitor.json`, `s000_baseline_partial_run.log` and `preflight_attempt0_overstrict.log`;
  the full attempt-A tree remains on TASL-2 at the path above.

Evidence roots on TASL-2 (outside every repository, no deletion): attempt B
`/home/dowling/r1_engineering/titanic_20261125/u2_census_smoke_20261125B` (raw + runs + captures), attempt A
`/home/dowling/r1_engineering/titanic_20261125/u2_census_smoke_20261125_attemptA_ecores_aborted`, kit captures
`/home/dowling/r1_engineering/titanic_20261125/captures`, data root
`/home/dowling/r1_engineering/titanic_20261125/data` (read-only, unchanged). The worktree is unchanged (only
the setup `data` link); nothing was pushed.

AI-assisted: DeepSeek Harness agent `u2-titanic-runner` (delegated by the lead), 25 Nov 2026, ENGINEERING_ONLY.
No deletion, no push, no GPU lease, T1/Track P archives untouched.
