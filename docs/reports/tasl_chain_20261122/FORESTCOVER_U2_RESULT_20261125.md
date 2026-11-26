# U2 census smoke — Track G kit `gc7rc_forestcover` (1GC-7RC Forest Cover), TASL-2, CPU-only — result, 25 November 2026

**Verdict: PASS** (CPU-only U2 census smoke). The reviewed kit's own stub-manager census smoke
`tests/trackg/port_smoke_gpu.py --node gc7rc_forestcover` was launched **once**, at the node's full 8,000-step
budget on the real data, CPU-only, in a delegated 8G/swap0 cgroup scope on TASL-2 on the **CPUs 8-11 P-cores**,
with `CUDA_VISIBLE_DEVICES=""`, no GPU and no GPU lease. It printed `CHECKLIST_E_PASSED gc7rc_forestcover`, all
**33 driver checks are true**, smoke `SMOKE_MAIN_RC=0`, wall **913.532 s** (13:41:43–13:56:56Z). **B1 and B2
agree to the digit** — `val_accuracy 0.896439`, sealed `test_accuracy 0.894683`, identical `run.log` sha256
`07c6557e…` and result-channel sha256 `bcfc9b5d…` — every executed run has `isolation.effective: true`,
`waivers {}`, `exceptions []`, 16 frozen entries checked with none changed, and the pins, data, environment and
worktree are the accepted ones and were unchanged by the smoke. No GPU was used or leased. The smoke does
**not** establish the GPU census or GPU determinism (review conditions **c2/c4** remain open); see §7–§8.

Captures (54 checksummed files + `SHA256SUMS` = 55 files on disk, 429,136 B, no data copied) are in
`FORESTCOVER_U2_RESULT_20261125_captures/` beside this file, `SHA256SUMS` sha256
**`057c8128506d128316ece1affc557409e28e5bb7c441f7e1c88411c4d0c731f9`** (`sha256sum -c` rc 0 on TASL-2 and on
the Mac). AI-assisted (DeepSeek Harness agent `u2-forestcover-runner`, delegated by the lead), ENGINEERING_ONLY.
Prepared under `R1-T1-NODE-EXPANSION`; no label campaign, evaluation, evidence or G.1b file was read or written;
no deletion, no push, no GPU lease.

## 1. Inputs and binding

| item | value |
|---|---|
| kit review | `docs/r1/reviews/FORESTCOVER_KIT_REVIEW_20261125.md`, sha256 `8a4412bc307986077af5c8907ec06235fa1dec6901eaf56b29f5976d05e4bed5`, verdict **ACCEPTED** (no BLOCKING/MAJOR) |
| kit report | `docs/r1/reports/tasl_chain_20261122/FORESTCOVER_KIT_20261125.md`, sha256 `ecc3e236cddd8660af73024a9bdf2b255b2cea064dcb81eaac0d0e4d363f12d1` |
| harness branch @ pin | `mac-trackg-forestcover-20261125` @ `85851664679d10889c5af406843c4a3fc38f7a49` (base `c025f89aeafc2199bf3487b4bcaa16678273c702`); `git diff --stat` vs base = 19 files, +2,030/−1, as reviewed |
| worktree | `/home/dowling/r1_trackg_20261125/harness_forestcover`, at the pin, clean except `?? nodes/gc7rc_forestcover/data` (the setup link), before and after |
| node / task | `gc7rc_forestcover` — 1GC-7RC Task 5, Forest Cover Type seven-class tabular classification, 3-layer MLP baseline, accuracy; fixed **8,000 optimizer-step** budget (batch 4,096, ≈71 epochs of 464,810 rows), selection `val_accuracy`, sealed `test_accuracy` |
| run id / unit | `systemd-run --user --scope --unit=u2-forestcover-census-20261125T1341Z --collect` |
| host | TASL-2 (`portal_zhixu`), Intel Core i9-14900KF, 32 logical CPUs (CPUs 0-15 = 8 P-cores with SMT, max 5.8-6.1 GHz; CPUs 16-31 = 16 E-cores, max 4.4 GHz), Linux 6.8.0-149-generic x86_64, euid 1008, ptrace_scope 1; clock PST = UTC−8; preflight loadavg 0.13/0.28/1.71 |
| env | pinned `torch312` `/home/dowling/r1_tracks/t1_tasl/envs/torch312`: Python 3.12.16, torch 2.6.0+cu124, numpy 2.5.4, pandas 3.1.1, uv 0.13.6; `uv pip freeze` sha256 **`d2e70fe4…`** (77 packages) — equal to the accepted census freeze |
| data | `/home/dowling/r1_engineering/forestcover_port_20261125/data/gc7rc_forestcover`, read-only (`dr-xr-xr-x`, files `-r--r--r--`), outside the repository; manifest sha256 **`2b5cfb15…`** |
| runs root | `/home/dowling/r1_engineering/forestcover_port_20261125/u2_census_smoke_20261125U2/runs` (outside the repository; preserved) |
| GPU | **none used, none leased**: RTX 4090 `GPU-4d623e76-7587-ee15-a633-46f60d220d94` (driver 535.309.01) idle at 353 MiB static / 0 % with no compute apps before and after; `gpu0.lock` not held before or after and its stat is unchanged; `CUDA_VISIBLE_DEVICES=""` and `gpu_uuids []` in every run record |

The reviewed kit was already published in the worktree at the pin; this task fetched, patched, committed and
pushed nothing. The node's data link (`setup_command` output) already existed and was re-verified, not re-run.

## 2. What ran

Delegated scope (verified inside: scope cgroup writable, `memory.max = 8,589,934,592`, `memory.swap.max = 0`,
affinity `[8,9,10,11]`), no GPU, `PYTHONDONTWRITEBYTECODE=1`, the pinned env's `bin` **first on `PATH`** and the
absolute pinned interpreter:

```
systemd-run --user --scope --unit=u2-forestcover-census-20261125T1341Z --collect \
  -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 \
  env PATH=/home/dowling/r1_tracks/t1_tasl/envs/torch312/bin:$PATH \
      VIRTUAL_ENV=/home/dowling/r1_tracks/t1_tasl/envs/torch312 \
      CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 \
      U2_BASE=/home/dowling/r1_engineering/forestcover_port_20261125/u2_census_smoke_20261125U2 \
  taskset -c 8-11 /home/dowling/r1_tracks/t1_tasl/envs/torch312/bin/python \
      /home/dowling/r1_engineering/forestcover_port_20261125/u2_census_smoke_20261125U2/run_u2_smoke.py
```

`run_u2_smoke.py` (sha256 `3cee930e…`, 40,845 B, captured) calls the reviewed module's own
`tests.trackg.port_smoke_gpu.main()` **once** with the kit's documented flags — `--node gc7rc_forestcover
--cpus 8-11 --memory-limit "<the enforcing systemd scope>" --runs-root <outside the repo> --provisional-timeout
900`. The only in-memory deviation is the CPU-only guard: the reviewed CLI refuses a GPU-less invocation for
this GPU-capable torch node (`--gpu-uuid is required for gc7rc_forestcover`; `CPU_ONLY_NODES` unchanged in the
kit), so the driver adds `gc7rc_forestcover` to `port_smoke_gpu.CPU_ONLY_NODES` for this process only — the same
mechanism the kit's own checklist-E CPU smoke used (kit report §5). **No repository file was changed** (worktree
status before and after: only the setup data link). The runs root is outside the repository.

A read-only **preflight gate** ran first in its own delegated scope (`u2-forestcover-preflight-20261125T1341Z`,
13:41:30Z): **PASS**, no run launched and `runs/` absent afterwards — head = the pin, committed pin
`78b48db9…`, deployed pin `ec5c7791…`, spec `ff2a585b…`, data manifest `2b5cfb15…`, `X.npy` `3c950339…`,
freeze `d2e70fe4…`, GPU visible 0, affinity `[8,9,10,11]`, `memory.max` 8 GiB, `swap.max` 0.

| run | decision | outcome | val_accuracy | sealed test_accuracy | wall (info only) |
|---|---|---|---|---|---|
| `s000_baseline` (B1) | baseline | ok | **0.896439** | 0.894683 | 93.406 s |
| `s001` | not_run_refused (`scope_violation`, frozen path) | — | — | — | — |
| `s002` | discarded_divergent (`non_finite_loss`) | divergent | — | (0.0 recorded) | 93.688 s |
| `s003` | discarded (E1 through the stub manager) | ok | 0.883083 | 0.881689 | 93.605 s |
| `E1` | declared edit (lr 1e-3→4e-4) | ok | 0.883083 | 0.881689 | 93.520 s |
| `E2` | declared edit (lr 1e-3→5e-3) | ok | 0.899262 | 0.898849 | 93.131 s |
| `E3` | declared edit (label smoothing 0.1 + grad clip 1.0) | ok | 0.891895 | 0.890329 | 96.023 s |
| `E4` | declared edit (128/256/128→256/512/256) | ok | 0.927213 | 0.927919 | 255.723 s |
| `B2` | baseline repeat | ok | **0.896439** | 0.894683 | 93.734 s |

Every value is the run record's `outcome.value` (selection metric `val_accuracy`, R1-TRACKG-ROLE) and the
sealed `AR_TEST test_accuracy` channel, which the manager view never shows. **All eight executed values are
digit-identical to the kit's own accepted checklist-E CPU smoke** (kit report §5: B1/B2 0.896439/0.894683,
s003/E1 0.883083/0.881689, E2 0.899262/0.898849, E3 0.891895/0.890329, E4 0.927213/0.927919), so neither the
8-11 P-core CPU set nor the U2 launch changed a measurement. Wall times are INFO ONLY: on CPUs 8-11 the smoke
took 913.532 s for B1–B2 (E4, the 3.8×-wider edit, 255.723 s; all other runs 93.1–96.0 s), versus 1,268.791 s
for the kit's smoke on the 16 E-cores (CPUs 16-31), i.e. ≈26–28 % faster per run (whole smoke 913.5 s vs 1,268.8 s) on the P-cores — expected
per-core speed, not a measurement.

The reviewed module's own gate rows behave as intended: `s001` reproduces the frozen-path diff and is refused
`scope_violation: run_fixed_budget.py is outside editable_paths; run_fixed_budget.py matches frozen_paths`
(`executed: false`, no run); `s002` applies the NaN diff and is discarded `divergent / non_finite_loss` with the
token `nan`. The baseline log holds 800 step/loss lines, `AR_STEPS completed=8000`, `AR_DATA manifest_sha256=
2b5cfb15… files=2`, `AR_SPLIT train=464810 val=58101 test=58101 features=54 classes=7 split_seed=42 (fixed;
AR_SPLIT_SEED=8001 unused) standardised_on=train`, and **no `AR_METRIC` or `AR_TEST` line** (the sealed test
metric is only in the result channel: exactly one selection line and one sealed line, 63 B).

## 3. One smoke, no retry, and what the pre-existing roots are

Exactly **one** smoke launch was made (unit above), with a preflight gate before it and **no retry** after it.
The run set was complete (9 records: 8 executed, `s001` refused) and the module passed, so no STOP handling was
triggered. The run tree, logs, result channels and captures are preserved unmodified.

For the record, three **pre-existing** roots under `/home/dowling/r1_engineering/forestcover_port_20261125/`
carry "u2_census_smoke_20261125" in their names but are **not** a U2 census smoke:
`u2_census_smoke_20261125_attemptA_preflight_abort`, `…_attemptB_import_abort` and `…_20261125C` are the **kit
setup's own** checklist-E CPU smoke attempts (raw preflight at 12:55:10Z and 12:55:27Z; accepted kit smoke
12:56:45Z–13:17:54Z on CPUs 16-31), exactly the records the kit report §5 and the independent review §5/m2
describe. They were checked read-only before this launch and left untouched. This run uses a **new** root,
`u2_census_smoke_20261125U2`. (A sibling report's phrase "the FORESTCOVER … U2 smoke on CPUs 16-31 passed"
refers to that kit smoke; it is not a U2 census record and should not be counted as one.)

## 4. Determinism (fixed seeds 8001/8001, CPU)

- **B2 repeats B1 exactly**: `val_accuracy 0.896439` = B1; sealed `test_accuracy 0.894683` = B1; **identical**
  `run.log` sha256 `07c6557e5a662c6009e8ff572c53d11865a96d5632c0ba1cce75b95a105444c7` and result-channel sha256
  `bcfc9b5d296a07335f46ec467c68ca7e282355882fccd44f9ea7f68cd628140a` for both runs.
- `s003` (E1 through the stub manager) repeats `E1` exactly: 0.883083/0.881689, identical log sha256
  `c1e7d434…` and channel `5a119acc…` (also the kit smoke's E1 hashes).
- `determinism.shim_loaded: true` and `not_forced: ["dataloader_workers"]` in every executed run; forced
  settings `cudnn.benchmark=False`, `torch.use_deterministic_algorithms(True)`, `set_num_threads=4`,
  `CUBLAS_WORKSPACE_CONFIG=:4096:8`, `PYTHONHASHSEED=0`, `AR_NUM_WORKERS=0`, `AR_DEVICE cpu`,
  torch 2.6.0+cu124; seeds train=split=8001; `AR_SPLIT_SEED` is recorded but the split is fixed at seed 42.
- This is a **CPU** determinism check only; GPU fixed-seed determinism (review c4) remains unmeasured (§8).

## 5. Pins, spec, data, environment — recomputed on TASL-2 and equal to the accepted values

Recomputed in preflight with the kit's own frozen-pin helpers (`isolation.frozen_file_hashes`,
`noise_floor.committed_view` / `frozen_pin_sha256`, the loader's canonical `raw_sha256`, `sha256_file`), not
copied from the report:

| field | value (recomputed) |
|---|---|
| `node_spec_sha256` (loader canonical; in every run record) | `ff2a585b69b51b51d0649e7f57b4713c650c46a27c981982dbeb2d09badf0beb` |
| spec raw sha256 (YAML bytes) | `edd1a076aab8b2cc1f45192860b3555a844400c211581888b9edbcc4e5104e02` |
| **committed pin** (clean tree, 15 frozen files, no data link) | `78b48db9d36c5c67e55a4cc65495821e39f70b9d5bf01bb35410037e1b017a33` |
| deployed pin (with the host `data` link; per-run record field) | `ec5c779161be56665bf7ae6d45adee140fde6e47cb46cb08bd583f8a0d4d5a5f` |
| `edits_manifest_sha256` | `0219deb80aab3f839d52a186a6bdedca8d754c111cd964566439af457a83b6ed` |
| `data_manifest_sha256` | `2b5cfb15f3c91e865df0e42c37099a335360df457005d455f6127b217c62c66d` |
| node `ar_isolated.py` = harness master | `37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610` |
| env freeze (torch312) | `d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42` (77 packages) |
| run budget | `steps 8,000`, batch 4,096, no wall-clock key; `frozen_pin_sha256` = deployed pin in **every** run record (`s001` included); `limits.measured_run_seconds = null` (provisional) |

Data (recomputed, read-only, outside the repository; the frozen parent re-checked the manifest before and after
the worker and the worker verified it again):

| file | value |
|---|---|
| `X.npy` | `3c9503390b527ce0cc5d1713772db126e754d12f312f3581b3f15fe6f834bfa7`, 125,498,720 B |
| `y.npy` | `35e11486262e974a249c66474dc624fe29d88f690d9819612239fb4dd34768a7`, 581,140 B |
| `data_manifest.json` | `2b5cfb15f3c91e865df0e42c37099a335360df457005d455f6127b217c62c66d`; schema `trackg_node_data/v1` |
| pinned source `raw/covertype.zip` (setup-only) | `89a975c2457cd48e824238ae43c5a3cb762e42c4b4078d9b44a4514055105f6d`, 11,251,206 B |
| source member `covtype.data.gz` (pinned in manifest) | `614360d0257557dd1792834a85a1cdebfadc3c4f30b011d56afee7ffb5b15771`, 11,240,707 B |
| source (UCI dataset 31, CC BY 4.0, DOI 10.24432/C50K5N) | 581,012 rows, 54 features, 7 classes; class counts 211,840 / 283,301 / 35,754 / 2,747 / 9,493 / 17,367 / 20,510 |

`git rev-parse HEAD` = the pin before and after; worktree status unchanged (only the setup data link); no new
repository file; the `data/` link points outside the repository. No data file was copied into the captures.

## 6. Isolation, resources, no GPU

- **Isolation, every executed row** (`s000_baseline`, `s002`, `s003`, `E1`–`E4`, `B2`): `effective: true`,
  `waivers: {}`, `exceptions: []`; `frozen_files_checked: 16`, `frozen_files_changed: []`; the worker sandbox
  present (`ro`/`rw`/`ro_flat`/`dev`, private `HOME`/cache dirs, `shared_dev_shm: false`); per-run cgroup v2
  under the smoke scope with `cgroup.kill` cleanup (`kill.empty_after: true`, `removed: true`, no leftovers);
  `ptrace_scope: 1`, `nsdelegate: true`, `euid: 1008`; no run was timed out or killed (`killed_with: null`,
  `timed_out: false`); the result channel is intact (`log_intact: true`, `result_channel_overflow: false`).
- **Memory:** scope `memory.peak` **1,417,728,000 B ≈ 1.32 GiB** (16.5 %) against `memory.max`
  8,589,934,592 B and `memory.swap.max 0`; no OOM and no swap use. Per-run cgroup `memory.peak` files were not
  readable because enabling the memory controller below the scope returned `EBUSY` (`[Errno 16] Device or
  resource busy`; the kit's own smoke hit the same limit), so the scope peak is the resource number — disclosed
  rather than fabricated.
- **Disk:** runs root 3,136,008 B (per-run working copies 101–212 KB); data root 137,340,815 B; home available
  371,386,810,368 B (~345.9 GiB) after; captures 429,136 B final; nothing written into the repository.
- **CPU:** driver and runs on CPUs **8-11** (the 6.1 GHz P-core siblings, not the 16-31 E-cores); 4 threads per
  run (`AR_NUM_THREADS=4`, `AR_NUM_WORKERS=0`); `limits.cpu_list [8,9,10,11]`.
- **No GPU:** `CUDA_VISIBLE_DEVICES=""` and `gpu_uuids []` in every executed record; `torch.cuda.device_count()
  = 0` in the driver; the only RTX 4090 stayed idle (353 MiB static / 0 %) with no compute apps before and
  after; `gpu0.lock` was not held and its stat (`0 bytes, mtime 1795359532.3914983`) is unchanged. No GPU lease
  was taken.
- **Host state after the run:** no leftover `run_u2_smoke`/`run_fixed_budget`/`ar_worker` processes, no
  forestcover scope left (`u2-forestcover-census-20261125T1341Z` inactive/collected), memory pressure zero,
  `/proc/sys/kernel/tainted = 4097` (the pre-existing proprietary + unsigned NVIDIA module bits only; no MCE
  or oops bit — this is the host's pre-existing taint, not caused by the run), `/var/crash` empty. Evidence:
  `host_state_after_run.txt`.

## 7. Measured run time and timeout — informational only, NOT claimed

The smoke ran with the kit's **provisional** timeout (900 s per run; every record carries
`provisional_timeout_seconds: 900.0`, `timeout_factor: 3.0`, `measured_run_seconds: null`), and **no run timed
out or was killed**. Per-run walls are CPU INFO ONLY: slowest = `E4` **255.723 s**; the other seven executed
runs 93.131–96.023 s; whole smoke 913.532 s. A timeout basis (`3 × slowest measured`, R1-G1B-TIMEOUT) is a
GPU-census field and is **not set from this CPU smoke**: review c2 asks for the GPU stub-manager run with the
GPU by UUID and its measured wall/VRAM, so this record leaves the timeout provisional and claims no census
run-time or chunk fields.

## 8. What this establishes / does not establish

- **Establishes, for the REVIEW-ACCEPTED kit at the accepted pins, on TASL-2, CPU-only:** the standard
  stub-manager census smoke (baseline, frozen-diff refusal, broken-diff divergence, E1 through the stub
  manager, every declared edit, a fixed-seed baseline repeat) passes checklist E on the real data at the full
  8,000-step budget on a fresh run set, with effective isolation and no waivers/exceptions on every executed
  row, deterministic repeats (B2 = B1 to the digit and by identical log/channel hashes; s003 = E1), the accepted
  pins/data/env and no GPU. **B1/B2 `val_accuracy = 0.896439`; sealed test accuracy 0.894683** (selection is on
  validation; the manager view never sees the test metric).
- **CPU-set note:** unlike the TITANIC and METAMAZE U2 smokes on this same CPUs 8-11 set earlier today (native
  SIGSEGV/SIGILL deaths), this torch/tabular smoke completed all eight executed runs with no crash, and its
  per-run walls (93–256 s) are faster than the kit's own smoke on the 16 E-cores (128–344 s). That is useful
  engineering evidence that CPUs 8-11 are not intrinsically broken for these CPU runs, but one smoke cannot
  settle the sporadic-crash hypothesis for the other nodes; the report records it without a verdict.
- **Does not establish:** the GPU census (review c2: GPU by UUID, GPU model/UUID/driver/VRAM, GPU wall time) or
  GPU determinism (c4) — this run is CPU-only by the task's instruction and consumes **no** GPU lease, so c2/c4
  remain open; `measured_run_seconds`/timeout basis; any noise floor, D21/D28, label campaign/evidence use,
  G.1b chunk or Track G readiness. No test-based selection was done; the sealed test values are recorded from
  the run records only.
- **Kit usability finding (not a defect, paper-side; repeated from the sibling record):** the census-smoke entry
  point starts its campaign runs as `python3` from `PATH` (the run records' command is
  `["python3","-s","run_fixed_budget.py","--steps","8000"]`), so the launching environment must have the pinned
  env's `bin` first on `PATH` and the absolute interpreter — which this launch did (the records' determinism
  shows torch 2.6.0+cu124 and the worker sandbox lists the pinned interpreter). A GPU-less invocation of the
  documented CLI is still refused for this node because it is not in `CPU_ONLY_NODES`; adding a documented
  CPU-only flag would be a kit change and trigger review condition c8. Neither finding changes the accepted
  pins; include them in the G.1b launch note if a CPU-only path is ever used there.

## 9. Captures

`FORESTCOVER_U2_RESULT_20261125_captures/` (54 checksummed files + `SHA256SUMS` = 55 files on disk, 429,136 B;
`sha256sum -c SHA256SUMS` rc 0 on TASL-2 and on the Mac; `SHA256SUMS` sha256
`057c8128506d128316ece1affc557409e28e5bb7c441f7e1c88411c4d0c731f9`):

- `preflight_gate/`: the preflight-gate console (`PREFLIGHT_PASS`), `preflight.json`, `launch_record.txt`,
  `env.txt`, `pins.json`, `git_head.txt`, `git_status.txt`, `gpu_state_pre.txt`, `torch312.freeze.txt`;
- valid smoke: `preflight.json` (host/git/pins/data/env/GPU/affinity/cgroup/launch env), `summary.json` /
  `summary.txt` (33 checks, all true; verdict PASS), `smoke_stdout.txt` (JSON lines + `CHECKLIST_E_PASSED`),
  `console_smoke.log` (launch + driver console incl. `SMOKE_MAIN_RC=0`), `run_records/` (9 `run_record.json`),
  `run_logs/` and `result_channels/` (8 each; `s001` not executed), `smoke_ledger.jsonl`, `env.txt`,
  `torch312.freeze.txt`, `pins.json`, `gc7rc_forestcover.yaml`, `data_manifest.json`, `edits_manifest.json`,
  `git_head.txt`, `git_status.txt`, `git_diffstat_vs_base.txt`, `gpu_state_pre.txt`,
  `host_state_after_run.txt`, `commands.txt`, `ATTEMPT_LOG.txt`, `run_u2_smoke.py` (the driver, sha256
  `3cee930e…`);
- **capture-set note (disclosed):** after the smoke the driver wrote its capture set (50 checksummed files,
  sha256 `0e70763b1824f800f30d7888c9025c5ae5d6dd22917e7b7cb92a7604211feaa9`); capture finalisation then added
  the full `console_smoke.log`, `preflight_gate/launch_record.txt`, `commands.txt`, `ATTEMPT_LOG.txt` and
  `host_state_after_run.txt`, and regenerated `SHA256SUMS` over the complete set (the cited sha). No run record,
  run log, result channel, summary or driver file was modified by that step.

AI-assisted: DeepSeek Harness agent `u2-forestcover-runner` (delegated by the lead), 25 Nov 2026,
ENGINEERING_ONLY. No push, no deletion, no GPU lease, no GPU use; T1/Track P archives, the kit's earlier
captures and its `u2_census_smoke_20261125C` run set are untouched.
