# U2 census smoke — Track G kit `mlgym_metamaze` (MLGym MetaMaze), TASL-2, CPU-only — result, 25 November 2026

**Verdict: PASS** (CPU-only U2 census smoke; affinity diagnostic disclosed). The reviewed kit's own stub-manager
smoke `tests/trackg/port_smoke_gpu.py --node mlgym_metamaze` at the node's full **2,000,000-step** budget on the
real data, run CPU-only in a delegated **8G/swap0** cgroup scope on TASL-2 with **no GPU and no GPU lease**,
printed **`CHECKLIST_E_PASSED mlgym_metamaze`** after **428.690 s** (`SMOKE_MAIN_RC=0`). **B1 and B2 agree to
the digit**: `val_return **8.703125**`, sealed `test_return **8.703125**`, with **identical `run.log` sha256
`8d85dad1…` and result-channel sha256 `9b083121…`**. Seven of the eight executed runs are `ok` (the eighth,
`s002`, is the intended `non_finite_loss` divergence) and the values are **digit-equal to the kit's accepted
CPU checklist-E smoke**; every executed record has `isolation.effective: true`, `waivers {}`,
`exceptions []`, `frozen_files_checked: 19`, no frozen change, `cpu_list [0,1,2,3]` and no GPU; the accepted
pins/data/environment were recomputed and are equal; the worktree is unchanged.

**Affinity diagnostic — disclosed.** This census ran on **CPUs 0-3** (P-cores; the same P-core set the kit's
own accepted checklist-E smoke used), not on the originally-briefed CPUs 8-11. Two earlier launches of the
*same* reviewed kit, same env/data/pins and the same driver on **CPUs 8-11 both STOPped with native process
signals** — attempt A: baseline **SIGSEGV** (rc −11) after training the full budget, other workers died by
signal; attempt B (the lead-authorised clean retry): baseline **SIGILL** (rc −4) after training the full budget,
other workers died by signal. Both are preserved unmodified here and on the host. The lead authorised **one**
diagnostic U2 census launch on CPUs 0-3 with everything else identical; it passed, and per that authorisation it
is reported as the census with this diagnostic disclosed (§3).

**Evidence-disclosure (post-flight correction).** The reviewed module's own gate passed
(`CHECKLIST_E_PASSED`); two of the U2 driver's *own* 39 post-flight checks were false only because of reporter
defects in the driver (the GPU check included the non-executed `s001`; the repo check used a path suffix that
porcelain lines never match). Both were re-evaluated from the captured records — all executed rows have
`CUDA_VISIBLE_DEVICES=""`/`gpu_uuids []`, and `worktree_unchanged` + `pin_unchanged` are true — and the
corrected verdict is PASS. The attempt-C captures keep the **original `summary.json` with its STOP boolean,
byte-identical**, next to `summary_corrected.json`, `POSTFLIGHT_CORRECTION.txt` and `correct_postflight.py`;
nothing was re-run (§6). This is a runner-side reporting defect only; it is not a kit defect.

Captures — combined set **170 files, 1,217,786 B**, `SHA256SUMS` sha256
**`4817bbf2a463b89c4d0f05fa8f3c72e50ce6ee9cc15af41409b59af294db2f85`** (`shasum -c` rc 0 on the Mac; no data
copied). It holds the three attempts, each with its own preserved checksum set: the census
`attempt C` at the top level (46 files, its original set kept as `SHA256SUMS_attemptC_original.txt`, sha256
`2bc7bc543e4c0cdbb28c9676579fc7c7b2edc09c909f7ceafff7ba8de2fed14c`), `attemptA_cpus8-11_stop/` (49 files, its
original `SHA256SUMS` sha256 `63f2e7805532f4cbab0850285c6acf421cee2c6a60ae0adb1f858a75e2e63c87`) and
`attemptB_cpus8-11_retry_stop/` (49-file retry capture set, its original `SHA256SUMS` sha256
`903856353a292a1b9d7a17096e043aafbe5e578baee924a2b0641e83d77eb775`, plus the retry's own attempt log,
`RETRY_STOP.txt`, commands, launch script and raw console logs). AI-assisted (DeepSeek Harness agent
`u2-metamaze-runner`, delegated by the lead), ENGINEERING_ONLY. Prepared under `R1-T1-NODE-EXPANSION`; no label
campaign, evaluation, evidence or G.1b file was read or written; no deletion, no push, no GPU lease; the kit's
earlier captures and `cpu_smoke_20261125/` run set are preserved untouched.

## 1. Inputs and binding

| item | value |
|---|---|
| kit review | `docs/r1/reviews/MOUNTAINCAR_KIT_REVIEW_20261125.md`, sha256 `5b867480ed81d3b5ece0f46657333cbb446d173cb0ed79f03bcebcd89d3e9950`, verdict **ACCEPTED** (no BLOCKING/MAJOR) |
| kit report | `docs/r1/reports/tasl_chain_20261122/MOUNTAINCAR_KIT_20261125.md`, 307 lines / 26,439 B, sha256 `0cede51b0dba90af8cc485748d577c2049d3671361f07facff70baabed635e7e`; kit captures `SHA256SUMS` `f5ee03bc1f22d5a7c25097eb3c38909b0c2a92ed93839815a543bd9473203a81` (`sha256sum -c` rc 0, 42 files) |
| harness branch @ pin | `mac-trackg-mountaincar-20261125` @ `aa354485bff6b5746c48ddadcb50d92e9c6f3645` (base `c025f89aeafc2199bf3487b4bcaa16678273c702`) |
| worktree | `/home/dowling/r1_trackg_20261125/harness_metamaze`, at the pin, clean except `?? third_party/mlgym/nodes/mlgym_metamaze/data` (the setup link) before and after |
| node / task | `mlgym_metamaze` — MLGym `rlMetaMazeMisc` (gymnax MetaMaze-misc), fixed **2,000,000 environment-step** budget, selection `val_return`, sealed `test_return` |
| census run id / unit | `systemd-run --user --scope --unit=u2-metamaze-census-diag-20261125T1433Z --collect`; 14:32:32–14:39:40Z |
| host | TASL-2 (`portal_zhixu`), Intel Core i9-14900KF, 32 logical CPUs (CPUs 0-15 = 8 P-cores with SMT, 16-31 = 16 E-cores), Linux 6.8.0-149-generic x86_64, euid 1008, ptrace_scope 1; launch loadavg 0.103/1.460/2.490; no other smoke running |
| CPU set | **CPUs 0-3** (`taskset -c 0-3`, `--cpus 0-3`; P-cores 0-1 with SMT, max 5.8 GHz) — the kit's accepted checklist-E CPU set; see §3 for the affinity diagnostic and the preserved 8-11 attempts |
| env | pinned `venv_jax` `/home/dowling/r1_trackg_20261125/venv_jax`: Python 3.12.16, `pip freeze` sha256 **`630ed6e1b823e0e2183c64ffb09bebd9994f755f518db2867ee538f388f5fdd9`** (56 packages), torch **absent**, jax/jaxlib 0.4.35 (device `TFRT_CPU_0`), numpy 2.5.4, flax 0.10.2, optax 0.2.4, gymnax 0.0.9, tensorflow_probability 0.25.0, dotmap 1.3.30, uv 0.13.6 |
| data | `/home/dowling/r1_engineering/metamaze_20261125/data/mlgym_metamaze` (read-only `dr-xr-xr-x` 0o40555, files `-r--r--r--` 0o100444, outside the repository), manifest sha256 **`e233819526e8214bb898c4f9dd76a8c30be7b0dcabd710b60efb815e99c38000`**, all 9 files re-hashed equal |
| runs root | `/home/dowling/r1_engineering/metamaze_20261125/u2_census_smoke_20261125_DIAG_CPUS_0_3/runs` (outside the repository; preserved, 12,884,856 B) |
| GPU | **none used, none leased**: RTX 4090 `GPU-4d623e76-7587-ee15-a633-46f60d220d94` (driver 535.309.01) idle at 353 MiB static / 0 % with no compute apps before and after; `CUDA_VISIBLE_DEVICES=""` and `gpu_uuids []` in every executed record; `gpu0.lock` not held and its stat unchanged |

Delegation note (no effect on the run): the brief named `/home/dowling/r1_trackg_20261125/envs/torch312/bin`
and called `630ed6e1…` a "torch312 freeze". That path **does not exist** on TASL-2; the reviewed MetaMaze kit's
environment is `venv_jax`, and `630ed6e1…` is its accepted freeze (the torch312 freeze `d2e70fe4…` belongs to the
torch nodes). The kit's own accepted env was used and `python3` on `PATH` resolved to the pinned interpreter
inside the scope (asserted). Transfer of the reviewed kit was the already-published worktree at the pin;
nothing was fetched, patched, committed or pushed by this task.

## 2. The census run (attempt C, CPUs 0-3)

A preflight gate (no run, no `runs/` created) passed first, then exactly **one** smoke launch:

```
systemd-run --user --scope --unit=u2-metamaze-census-diag-20261125T1433Z --collect \
  -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 \
  env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 \
  U2_BASE=/home/dowling/r1_engineering/metamaze_20261125/u2_census_smoke_20261125_DIAG_CPUS_0_3 \
  PATH=/home/dowling/r1_trackg_20261125/venv_jax/bin:$PATH \
  VIRTUAL_ENV=/home/dowling/r1_trackg_20261125/venv_jax \
  taskset -c 0-3 /home/dowling/r1_trackg_20261125/venv_jax/bin/python \
  /home/dowling/r1_engineering/metamaze_20261125/u2_census_smoke_20261125_DIAG_CPUS_0_3/run_u2_smoke.py
```

The driver (`run_u2_smoke.py`, sha256 `c048222f3e0917ec8144b2fe111720f499ea740a0378ce5d2945aaf96c4da7ac`,
captured) calls the reviewed module's own `tests.trackg.port_smoke_gpu.main()` with the kit's documented flags
(`--node mlgym_metamaze --cpus 0-3 --memory-limit "<scope>" --runs-root <outside the repo>
--provisional-timeout 900`). The only in-memory deviation is the CPU-only guard (the reviewed CLI requires
`--gpu-uuid` for a node not in `port_smoke_gpu.CPU_ONLY_NODES`, so the driver adds `mlgym_metamaze` to that set
for this process only); no repository file was changed. Scope verified inside: cgroup writable,
`memory.max = 8589934592`, `memory.swap.max = 0`, controllers `memory pids`, affinity `[0, 1, 2, 3]`.

Smoke wall **428.690 s**; `SMOKE_MAIN_RC=0`; **`CHECKLIST_E_PASSED mlgym_metamaze`**; no run timed out or was
killed (`killed_with: null`, `timed_out: false`).

| run | executed | outcome | `val_return` (selection) | sealed `test_return` | wall (info only) |
|---|---|---|---|---|---|
| `s000_baseline` (**B1**) | yes | ok | **8.703125** | **8.703125** | 53.721 s |
| `s001` | no | `not_run_refused`, frozen-path diff `scope_violation` (as intended) | — | — | — |
| `s002` | yes | divergent `non_finite_loss` (broken network, as intended) | — | — | 51.620 s |
| `s003` (E1 via stub manager) | yes | ok | 7.0625 | 7.40625 | 53.571 s |
| `E1` | yes | ok | 7.0625 | 7.40625 | 53.690 s |
| `E2` | yes | ok | 8.0625 | 8.617188 | 53.630 s |
| `E3` | yes | ok | 2.929688 | 2.9375 | 53.662 s |
| `E4` | yes | ok | 15.46875 | 14.929688 | 54.626 s |
| `B2` (baseline repeat, **B2**) | yes | ok | **8.703125** | **8.703125** | 53.596 s |

All values are the run records' `outcome.value` (selection metric `val_return`, R1-TRACKG-ROLE) and the sealed
`AR_TEST test_return` channel, which the manager view never shows. The eight executed runs' `val_return` values
are **identical to the kit's accepted CPU checklist-E smoke** (kit report §7: s000 8.703125, s003/E1 7.0625,
E2 8.0625, E3 2.929688, E4 15.46875, B2 8.703125), and the sealed test returns match those kept in the earlier
run records (e.g. E1 7.40625). Wall times are INFO ONLY (they reflect the shared host and the CPU set).

## 3. Affinity diagnostic — and the two preserved failed attempts on CPUs 8-11

The U2 census was first attempted on the briefed CPUs 8-11; it STOPped twice with native process signals
(SIGSEGV, SIGILL), twice at the same point — after the baseline had trained the **full** 2,000,000 env steps and
entered evaluation, with every other executed run's worker dying by signal within seconds:

| attempt | CPUs | when (UTC) | result | signature |
|---|---|---|---|---|
| A | 8-11 | 13:28:32–13:29:55 | STOP | baseline **SIGSEGV** (rc −11) after 2,000,064 steps / 51.934 s, empty result channel; 7 other executed runs' workers died by signal in 3.5–5.6 s |
| B (clean retry) | 8-11 | 14:05:51–14:07:10 | STOP | baseline **SIGILL** (rc −4) after the full budget / 50.674 s, empty result channel; 7 other executed runs rc 1 in 3.691–4.161 s |
| C (this census, diagnostic) | **0-3** | 14:32:32–14:39:40 | **PASS** | all 8 executed runs ok; B1 = B2 = 8.703125; `CHECKLIST_E_PASSED` |

Attempt A and attempt B used the **same reviewed kit, pins, data, env, scope (8G/swap0), driver** (B used the
byte-identical A driver `31eb7bc1…`; C differs only in the CPU list, the evidence root and two check names) and
the host was otherwise idle at each launch. Their records show isolation effective, 19 frozen entries unchanged,
the accepted pins/data/env and no GPU — i.e. the STOPs were native signals in the JAX compute processes, not
kit checks. The kit's own accepted smoke passed on 0-3 at 04:48–04:56 PST (16G scope), and the same host
earlier saw a peer CPU-8-11 smoke stop with SIGSEGV/SIGILL as well. On CPUs 8-11 the host runs the two
**6.1 GHz favoured P-cores**; that is the leading host-side explanation (the mechanism is not proven — uid 1008
cannot read the kernel log and apport captured no coredump; `/proc/sys/kernel/tainted` stayed 4097 =
proprietary + unsigned module bits only, with no MCE/oops bit, and memory pressure was zero both times).

Per the lead's authorisation this **one** diagnostic launch on the kit's own P-core set is reported as the U2
census, with the affinity diagnostic disclosed; there was **no other smoke**. A and B are preserved
unmodified in `attemptA_cpus8-11_stop/` and `attemptB_cpus8-11_retry_stop/` here and on the host at
`/home/dowling/r1_engineering/metamaze_20261125/u2_census_smoke_20261125` and
`…/u2_census_smoke_20261125_RETRY`.

## 4. Determinism (fixed seeds 8001/8001, CPU) — established for this smoke

- **B2 repeats B1 exactly**: `val_return 8.703125` = B1; sealed `test_return 8.703125` = B1; **identical
  `run.log` sha256 `8d85dad1e13ab0f6…` and identical result-channel sha256 `9b08312199b96caf…`**.
- `s003` repeats `E1` exactly (`7.0625`/`7.40625`, identical log `14a6d28e…` and channel `55055cd4…`).
- Every executed record: `determinism.shim_loaded: true`; `not_forced` exactly the accepted four-entry list
  (`cudnn.benchmark=False`, `dataloader_workers`, `torch.set_num_threads`,
  `torch.use_deterministic_algorithms(True)`) with the accepted reasons (`torch_absent: ModuleNotFoundError`
  for the three torch settings, "advertised via AR_NUM_WORKERS only" for dataloader_workers); forced
  environment `PYTHONHASHSEED=0`, `AR_NUM_THREADS=4`, `AR_NUM_WORKERS=0`, `CUBLAS_WORKSPACE_CONFIG=:4096:8`;
  `AR_DEVICE cpu`, jax 0.4.35 on the pinned interpreter.
- This is a CPU determinism check. GPU determinism stays a G.1b measurement (review c4, GPU part).

## 5. Pins, spec, data, environment — recomputed on TASL-2 and equal to the accepted values

Recomputed in the smoke's preflight with the kit's own frozen-pin helpers (`isolation.frozen_file_hashes` +
`committed_view` + `frozen_pin_sha256`, the loader's canonical `raw_sha256`, `noise_floor.sha256_file`), not
copied from the report:

| field | value (recomputed) |
|---|---|
| `node_spec_sha256` (loader canonical) | `d97bb182a6469cc4381262960bccf58eec984996cb9a8cd89c39083b4679dbb9` |
| spec raw sha256 (YAML bytes) | `d46dee59960f6959587e822c9dd663864006d2b48d7e5a67a2f7022f21cb3c59` |
| **committed pin** (18 frozen files, no data link) | `759d6bf0562a3a9334982b30b3e23c80f222c828e44847b66e743102c87d03db` |
| deployed pin (with the host data link; per-run record field) | `1eaaeac351280e16295eae0f50212f352b1aa0c4c3d26a410b58bb0c3bf9ecb7` |
| `edits_manifest_sha256` | `6de5741f7107d9f924a3686fce85f6509ed7fb0c47ee7cc2c9fc16732d66f0b2` |
| `data_manifest_sha256` | `e233819526e8214bb898c4f9dd76a8c30be7b0dcabd710b60efb815e99c38000` |
| node `ar_isolated.py` = harness master | `37d99ab092c73d885b95daa443d0b145148f0b02a6ff464e055704c39e48b610` |
| env freeze (venv_jax) | `630ed6e1b823e0e2183c64ffb09bebd9994f755f518db2867ee538f388f5fdd9` (56 packages, Python 3.12.16, torch absent) |
| run budget | `steps 2000000`; `frozen_pin_sha256` = deployed pin and `node_spec_sha256` = accepted in **every** run record (`s001` included) |
| data files (recomputed, read-only) | all 9 match the manifest: `rlMetaMaze.yaml` `45104e08…` 4,249 B; `evaluate.py` `00ea0abc…` 4,111 B; `requirements.txt` `6b90179a…` 70 B; `__init__.py` `e3b0c442…` 0 B; `config.yaml` `f91f5586…` 860 B; `helpers.py` `b9e0e07b…` 2,186 B; `networks.py` `bc527dba…` 3,238 B; `policy.py` `755d8ec9…` 15,369 B; `train.py` `22f37c40…` 2,118 B; root 0o40555, files 0o100444 |

`git rev-parse HEAD` = the pin before and after; worktree status unchanged (only the setup `data` link); no new
repository file; no data file in the kit tree (`git ls-tree` checked). This satisfies the recording part of
review c3 on the census host.

## 6. Isolation, resources, no GPU — and the post-flight correction

- **Isolation, every executed row** (`s000_baseline`, `s002`, `s003`, `E1`–`E4`, `B2`): `effective: true`,
  `waivers: {}`, `exceptions: []`; `frozen_files_checked: 19` (18 committed files + the data link), none
  changed (`frozen_files_changed: []`); per-run cgroup v2 under the smoke scope with `cgroup.kill` cleanup
  (`empty_after: true`, `orphans_killed: 0`); `ptrace_scope: 1`, euid 1008, `nsdelegate: true`. Gate rows pass
  as intended (`s001` refused `scope_violation`; `s002` divergent `non_finite_loss`). No run timed out or was
  killed by the runner.
- **Memory:** scope `memory.peak` **870,019,072 B ≈ 830 MiB** against `memory.max` 8,589,934,592 B and
  `memory.swap.max` 0; no OOM (host `/proc/pressure/memory` all zero). Per-run cgroup peaks are absent because
  enabling the memory controller in the scope subtree returned `EBUSY`; the scope peak is the authoritative
  resource number.
- **Disk:** runs root 12,884,856 B; per-run working copies ~1.4 MB; data root 40,523 B; home available
  371,327,811,584 B after; attempt-C capture set 494,457 B on the host (combined set here 1,217,786 B).
- **No GPU:** `CUDA_VISIBLE_DEVICES=""` and `gpu_uuids []` in every executed record; the pinned env has no torch
  and JAX reports only `TFRT_CPU_0`; the only RTX 4090 was idle (353 MiB static / 0 %, no compute apps) before
  and after; `~/r1_locks/gpu0.lock` was free before and after and its stat unchanged. No GPU lease was taken.
- **Post-flight correction (disclosed, no re-run):** 37 of the driver's original 39 checks were true and two
  were false because of reporter defects in the driver — `no_gpu_in_every_run` iterated over the non-executed
  `s001` (which legitimately has no `environment_applied`; on the 8 executed rows the correct check passes:
  `CUDA_VISIBLE_DEVICES=""` and `gpu_uuids []` in all), and `no_new_files_in_repo` compared porcelain lines
  against a `/`-prefixed path suffix that porcelain lines never match (the correct predicate is "status equal to
  preflight": `worktree_unchanged: true`, `pin_unchanged: true`). With both re-evaluated, all 40 checks pass and
  the corrected verdict is PASS (the corrected set has 40 checks, all true, including the new module-level
  `smoke_module_passed`). The **original `summary.json` with its STOP boolean is preserved
  byte-identical**; the correction, its evidence and the code that produced it are in
  `POSTFLIGHT_CORRECTION.txt`, `summary_corrected.json` and `correct_postflight.py` in this capture set.

## 7. What this establishes, and what it does not

**Establishes (U2 census, CPU-only, on TASL-2):** for the REVIEW ACCEPTED MetaMaze kit at the accepted pins and
environment, the standard checklist-E/stub-manager smoke passes on the real data at the full 2,000,000-step
budget with effective isolation on every executed row, the accepted deterministic settings, a **bit-identical
fixed-seed repeat**, the accepted pins/data/env, and no GPU — **B1 = B2 `val_return 8.703125`, sealed
`test_return 8.703125`**, B1/B2 log and result-channel sha256 identical, all B1/B2/E1–E4 values digit-equal to
the kit's accepted smoke. This satisfies the CPU part of review **c2** and the CPU-determinism part of **c4**,
and records **c3** on the census host. The best full-budget record is 54.626 s, so `3 ×` it is 163.878 s — inside
the G.1b chunk schema's `measured_run_seconds` cap of 300 s (R1-G1B-TIMEOUT; the smoke's records are excluded
from setting `measured_run_seconds`, which the coordinator sets from the G.1b census records; the smoke's own
timeout stayed provisional at 900 s).

**Does not establish:** GPU census or GPU determinism (G.1b), a noise floor/D21/D28, any label/evidence/G.1b
result, or that CPUs 8-11 are healthy — the two preserved 8-11 STOPs are a **host CPU-set/runtime finding** with
identical kit/env/data/pins/driver, not a MetaMaze or kit defect, and the mechanism is not proven from this
account (no kernel-log/coredump access). Review **c1** (paper-side m1–m10 corrections applied or explicitly
waived before any census) is outside this runner's remit: at the time of the run the kit report was still the
reviewed file (sha `0cede51b…`); applying/waiving those corrections remains a coordinator step before any G.1b.

## 8. Captures

`METAMAZE_U2_RESULT_20261125_captures/` — combined set of 170 files / 1,217,786 B, `SHA256SUMS` sha256
`4817bbf2a463b89c4d0f05fa8f3c72e50ce6ee9cc15af41409b59af294db2f85`:

- **attempt C (the census)** at the top level, with its original checksum set preserved as
  `SHA256SUMS_attemptC_original.txt` (sha256 `2bc7bc54…`): `preflight.json` (host/git/pins/data/env/GPU/affinity/
  cgroup/launch env), `summary.json` (original, verdict STOP from the two reporter defects), `summary_corrected.json`
  (verdict PASS, 40/40 checks) and `summary.txt`, `smoke_stdout.txt` (the module's run lines + `CHECKLIST_E_PASSED
  mlgym_metamaze`), `POSTFLIGHT_CORRECTION.txt`, `correct_postflight.py`, `host_state_after_run.txt`,
  `gpu_state_pre.txt`, `run_records/` (9), `run_logs/` and `result_channels/` (8 each), `env.txt`,
  `venv_jax.freeze.txt`, `pins.json`, `data_manifest.json`, `edits_manifest.json`, `mlgym_metamaze.yaml`,
  `git_head.txt`, `git_status.txt`, `git_diffstat_vs_base.txt`, `commands.txt`, `run_u2_smoke.py`;
- **`attemptA_cpus8-11_stop/`** (49 files, original `SHA256SUMS` sha256 `63f2e780…`): attempt A's full evidence
  including its preflight-gate logs, run records/logs/channels and diagnosis;
- **`attemptB_cpus8-11_retry_stop/`** (49-file retry capture set, original `SHA256SUMS` sha256 `903856353a…`):
  the lead-authorised clean retry on 8-11, plus its `ATTEMPT_LOG.txt`, `RETRY_STOP.txt`, `commands.txt`,
  `launch_retry.sh`, driver and `raw/` console logs;
- `ATTEMPT_LOG.txt`: the A/B/C sequence, times, authorisation and preserved-set hashes.

AI-assisted: DeepSeek Harness agent `u2-metamaze-runner` (delegated by the lead), 25 Nov 2026,
ENGINEERING_ONLY. No push, no deletion, no GPU lease; T1/Track P archives, the kit's earlier captures and its
`cpu_smoke_20261125/` run set untouched.
