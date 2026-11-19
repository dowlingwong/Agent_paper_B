# Track G G.0 U2 isolated-node raw cost — node `mlgym_cifar10` — RESULT (19 November 2026)

**Status: PASSED — `CHECKLIST_E_PASSED mlgym_cifar10`; one node only, one smoke, no retry.**
Authority: `R1-TRACKG-G0-GO` (one node per unit, independently reviewed), `R1-HARNESS-ISOLATION`,
`R1-TRACKG-PORT-DECISIONS` (node timeout = 3 × measured B1; a timeout is the proposal's failure, not an
infrastructure retry), port report `docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md` §2/§7, the accepted kit
update `docs/r1/reports/trackg_g0_20261117/TRACKG_ISO_KIT_UPDATE_20261119.md` (sha256
`fe232e2bbf236337e208f11e97c809f8a41d7ef101567eeb0d11153bacb9d026`) with review
`docs/r1/reviews/TRACKG_ISO_KIT_UPDATE_REVIEW_20261119.md` (sha256
`d8c68f9f0463d1aa3e17f82527dfb7ecf7b6070831584cd1024a6d39ed6a21b4`, ACCEPTED), and `R1-TRACKG-LICENCES`. Unit
`docs/r1/proposals/u2_iso_20261119/U2_ISO_MLGYM_CIFAR10_UNIT_20261119.md` (revision 3 **as amended with the R3 pre-execution
conditions mR1/mR7**;
current file sha256 `82e90b7ce9668031619689d3e5c10ff966c4ad0120180f8ba99a6ee4b437d7a3`), accepted by review R3
`docs/r1/reviews/TRACKG_U2_ISO_UNITS_REVIEW_R3_20261119.md` (sha256
`99daf16db0b53b807c7796d4d8c8d2812573f2816a42072d7b6dc6f588ca5fb7`; 0 BLOCKING / 0 MAJOR / MINOR,
`ACCEPTED`).
ENGINEERING_ONLY; **not evidence**; no noise floor/D21/D28; no T1 label; no cross-node pooling; no
TASL-7/TASL-2, no HTCondor/deepthought, no other host; no deletion; no commit/push; read-only on Mac records
(only this new result directory is written).

**Kit / environment.**

- Suite **MLGym**, node `mlgym_cifar10`; kit worktree `/home/dowling/r1_trackg_20261117/harness_iso_mlgym`, branch `mac-trackg-iso-mlgym-20261117`, **tip `f07875de79a5a57739227b13e0fd52d31646edaf`**; launch
  check `git rev-parse HEAD` = tip and `git status --porcelain --untracked-files=no` empty (only the expected
  untracked runtime `data` symlink(s)) — capture `kit.txt`.
- Python **3.12.16** (`/home/dowling/r1_trackg_20261117/envs/torch312`), torch **2.6.0+cu124 12.4**, CUDA available
  `True 8`; `uv pip freeze` **77 lines**, sha256 **`d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42`** (`env_freeze.txt`,
  `env.txt`).
- Host `ucrtasl`, `Ubuntu 22.04.5 LTS`, kernel `5.15.0-151-generic`, 96 CPUs, driver
  **545.23.08**, boot id `5c90a8fe-5f9b-4914-a2c7-5b864e0a8b8d` (`host.txt`).
- **Data** `AR_TRACKG_DATA_ROOT=/home/dowling/r1_trackg_20261117/data` (outside the repository); node data
  link `third_party/mlgym/nodes/mlgym_cifar10/data -> /home/dowling/r1_trackg_20261117/data/mlgym_cifar10` (`kit.txt`
  `?? third_party/mlgym/nodes/mlgym_cifar10/data`; deployed pin `data: link:` entry); manifest sha256
  **`c0ef1168e9c575fe367b607fc3c945e021323d307edd674c832bab5dd112ba40`** (4 manifest files, 0 setup_only); 5 files / 184801471 bytes on disk,
  177M (node data tree); whole data root 2.9G; manifest and node data tree `dr-xr-xr-x` / `r--r--r--`.
  **Node data dir not writable** (`data_manifest.txt` tests `[ -w "$BASE/data/mlgym_cifar10" ]`; `data_root_writable=no`)
  and ro-bound in the worker sandbox; the **top-level `data/` root is operator-writable** (`drwxrwxr-x`) — the claim
  that matters is the node data read-only/ro-bind, not the whole root. The `data_link=` line in `data_manifest.txt`
  prints `readlink -f` and re-prints the absolute target, so the in-kit symlink path is implicit (cosmetic; the
  symlink path above is the in-kit one). **No `synthetic` marker** (`data_manifest.txt`). Setup command
  (accepted kit update §5, not re-run; data link and manifest re-verified now): `cd nodes/mlgym_cifar10 &&
  envs/torch312/bin/python prepare_data.py --out $AR_TRACKG_DATA_ROOT/mlgym_cifar10` (accepted setup log
  `/home/dowling/r1_engineering/iso_kit_update_20261119/data/setup_mlgym_cifar10.log`, sha256 `2f2e4bcff7d460e8b95acf9f5da2d5317bf43f4a1e874d79514ac0f816ed5cf2`).
- **Static tests** (mlgym kit; CPU-masked `taskset -c 0-15`, `CUDA_VISIBLE_DEVICES=`, delegated user
  cgroup, interpreter `envs/torch312/bin/python`, `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1
  -p no:cacheprovider`): `python -m pytest tests/trackg -q -p no:cacheprovider -k "not smoke"` →
  **225 passed, 2 failed, 1 skipped, 6 deselected in 46.06 s**, log `static/static_mlgym_20261119T033511Z.log` sha256 `8d8a0fb591e2c80352f462c4e9322bcbe938236ac87ed7a11fa22d448714ce35`. The two failures are the
  accepted kit-update §4 documented environment failures (round-2 child-kill test under `/usr/bin/python3`
  3.10; `langchain-openai` missing for the t0 identity test); same counts as the accepted post-update run; no
  test was skipped or weakened.
- **Licence/provenance.** MLGym subtree **CC BY-NC 4.0** non-commercial with notice; CIFAR-10 generic citation; the gymnax-derived Apache-2.0 parts are not used by this node (`R1-TRACKG-LICENCES`; port decision (1)).

**Pins (both, separately; no interchange).**

- **Committed-file `frozen_pin_sha256`** (accepted kit update §3/§10.2 convention; `pins/new_mlgym.json` sha256
  `8974359b1fd5c11105dc98b593dcb1c84b33d59896fe3e63bf7cb6c3b1e4a451`): **`2d7e533b2a1075000d15a21445f98b94d7df2cf527baff0264f3ae306f93022e`** (16 frozen entries; this is the census value).
- **Deployed run-record pin** (every run record's `frozen_pin_sha256`, which also hashes the
  `data: link:<absolute target>` symlink; matches `pins/deployed_mlgym.json` sha256 `dcfcb0808445c0af2ee851a27047be89202420f340e815d6f9ad0443b1ea4ee0`):
  **`817c90340e7ae004b7cd7161f899cb159a91ae482febc9a7f9ea2d9969f76e62`**; expected deployed value `817c90340e7ae004b7cd7161f899cb159a91ae482febc9a7f9ea2d9969f76e62`, constant across all nine records.

**Record identity and preserved bytes (S3/S10).** This result file is
`docs/r1/reports/trackg_g0_20261117/u2_iso_mlgym_cifar10_20261119T035326Z/U2_ISO_MLGYM_CIFAR10_RESULT_20261119.md`;
its own post-correction sha256 is the `./U2_ISO_MLGYM_CIFAR10_RESULT_20261119.md` entry in this directory's
regenerated `SHA256SUMS` (the `SHA256SUMS` sha256 is recorded in `U2_ISO_RECORD_CORRECTIONS_20261119.md`). Node spec:
raw `third_party/mlgym/configs/trackg/nodes/mlgym_cifar10.yaml` sha256
`a03585ff396d579e19e024c80824344fadd52dcfbc92b74292ef76926d6c8d99`, canonical `node_spec_sha256` (kit loader:
`sha256(json.dumps(payload, sort_keys=True, separators=(",",":"), ensure_ascii=False, default=str))`)
`f1360bcd01b0a68b8262360c68a6d5b4adad70cd46d127b539791b1ee3eadad1` (= every run record's value). Representative-edit
manifest sha256 `d0ad0e64ebce12f9d6c5d57ada95c0e7c8c26deedb4ec5479245e2c7e3027d9a`; representative edits E1/E2/E3/E4
diff sha256 `6d806f90…`, `ecb86f50…`, `8b84959a…`, `58c33a33…` (full values in `kit.txt`). Executed unit bytes are
preserved at `unit/U2_ISO_MLGYM_CIFAR10_UNIT_20261119.md` (sha256
`82e90b7ce9668031619689d3e5c10ff966c4ad0120180f8ba99a6ee4b437d7a3`, = the recorded executed unit). Preserved
runner/helper bytes (this directory's `scripts/`): **launch-time/final** `run_node.sh` sha256
`13a45d7baf7dacac6da2ef1455e86fc794c25fd90f5a835511b50aafccc99444` (patch3 was applied at 19:50Z, before this
node's 19:53Z launch, so these are the launch-time bytes), `_patch2_verifier_s002_fix.py`
`681d9f8a2d25eef0d2c1947e7bace55b1ade5c0fe9f6cbf64ae458b4b97b5353`, `_patch3_mid_watcher_fix.py`
`ce2ff3b0ecdb61cdbbad615bef47abd6a34473bb42bc45358eefe00cbb18fc39`, `compute_sampler_max.py`
`7d9f472ec1e24ba879f2edd0fa259612f0c00133abf90309587a43ced312dbed`, `verify_u2_records.py`
`7f40ed1789fb77c29a14022db9908a46c3ca47563cd0ca6030df7aff21dd8418`. Every executed record has
`process.returncode: 0`, `process.killed_with: null` (normal exit), `process.timed_out: false`,
`leftover_processes_killed: false`; the smoke log carries one JSON record line per run (verifier `--smoke-log` check
in `verify_full.json`).

**Paper A gate (captured immediately before launch; three-check).**

- Gate JSON `/home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlgym_cifar10_20261119T035326Z/gate/gate_20261119T035326Z.json` sha256 **`2d0aad26e2aa45e3f37368e222075126299cfd5c2c7aac2b1e8bfc0c4dbc01f5`** (UTC `2026-11-19T03:53:30Z`; gate script rc 0; config
  `/home/dowling/r1_trackg_20261117/Agent_paper_B_main_16185b0b/r1/scripts/configs/paper_a_status_ada.json`).
- **Three-check PASS**: `verdict: clear_finished`, `paper_a_live_waiting_for_card: false`, `paper_a_processes: []`,
  `unidentified_apps: 0`.
- Newest v4 `live_*` directory == configured run dir (`newest_live_equals_configured=yes`); self-excluded
  `pgrep` for `port_smoke_gpu` empty; `pgrep agent-checkpoint-intervention` empty (`gate/gate_check.txt`).

**GPU gate / co-tenancy (idle card only).**

- Selected **UUID `GPU-3719bd35-06de-4674-7c7a-e56136fed589`**: 48427 MiB free, **0 % utilization, no other user's compute app**
  immediately before launch (`gpu/gpu_qualify.txt`, `gpu/gpu_before.txt`); floor = ≥ 8,192 MiB free.
- **Floor basis / co-tenancy rule (S5).** The 8 GiB requirement is a conservative floor: the accepted kit update
  measured a **~2.85 GB (2,853 MiB)** per-run torch GPU peak under the 8 GiB cap (§6), and the prior accepted run-1
  floor was **24 GiB** (`TRACKG_U2_RAWCOST_REVIEW_R2_20261117.md`); this card had 48,427 MiB free. Mid-run
  contamination rule: a free-VRAM drop below the baseline peak + 2 GiB, or a new co-tenant on the used card, is a
  STOP/recorded; **no card switch from the launch card** occurred (the selected UUID is the only card in
  `gpu_qualify/before/mid/after` and in every run record).
- Whole-smoke sampler: exact command
  `nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv -l 1` (interval **1 s**), started
  before the `systemd-run` scope and stopped after it; output `sampler/sampler_required.csv` (sha256
  `e29bcda6c041dfaa406127b3c4cddad7f90bcdeca05cbc01af94b441a72b0483`, 2026 app rows) plus a concurrent timestamped
  companion used only to group rows into per-sample sums (`sampler/sampler_timestamped.csv` sha256
  `9d564c5784d1f7104ed197aa164cb6c12196f98610b7a1810455bd6e7fc48210`); 258.5 s sampled,
  227 samples carried the used card, 8 distinct worker pids
  (all this smoke).
- **Peak reported as a whole-smoke upper bound = 982 MiB** (max single-row
  `used_memory` 982 MiB = max per-sample sum 982 MiB on the
  used card; CSV header not counted). **Label: whole-smoke upper bound over the used GPU, including any
  co-tenant by construction; NOT a per-run peak and NOT attributed to the baseline process tree.** The card
  returned to idle after the smoke (`gpu/gpu_after.txt`).
- Mid-run census (`gpu/gpu_mid.txt`):
  ```
  # gpu mid (used=867 MiB) 2026-11-19T03:53:35Z
index, uuid, memory.total [MiB], memory.used [MiB], memory.free [MiB], utilization.gpu [%]
0, GPU-9be33fd1-8eeb-497d-772a-87362d6720be, 49140 MiB, 11979 MiB, 36453 MiB, 46 %
1, GPU-aa340032-6f94-9783-8f3d-50a15da47a6f, 49140 MiB, 5 MiB, 48427 MiB, 0 %
2, GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154, 49140 MiB, 5 MiB, 48427 MiB, 0 %
3, GPU-5d61f1bc-1a65-f322-6feb-3aeaf6051f94, 49140 MiB, 29376 MiB, 19057 MiB, 0 %
4, GPU-379470db-a02e-893a-57a0-71b119173890, 49140 MiB, 15469 MiB, 32963 MiB, 39 %
5, GPU-5357dc5f-5d1d-af80-a3f4-3eb5aeb38f0d, 49140 MiB, 12226 MiB, 36206 MiB, 49 %
6, GPU-3b36edea-1a09-a37e-aa42-8277c7319e77, 49140 MiB, 5 MiB, 48427 MiB, 0 %
7, GPU-3719bd35-06de-4674-7c7a-e56136fed589, 49140 MiB, 867 MiB, 47565 MiB, 11 %
# compute apps
gpu_uuid, pid, used_gpu_memory [MiB]
  ```

**Run (unit command shape, exactly one smoke).**

- Inside `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c '…'`
  (logged unit line in `logs/run_node.log`): `cd harness_iso_mlgym`, `CG=$(cut -d: -f3 /proc/self/cgroup)`,
  `AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG`, `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1`,
  `PATH=…/envs/torch312/bin:$PATH`, `VIRTUAL_ENV=…/envs/torch312`, `CUDA_VISIBLE_DEVICES=""`,
  `AR_TRACKG_DATA_ROOT=…/data`, `taskset -c 8-15 python -m tests.trackg.port_smoke_gpu --node mlgym_cifar10
  --gpu-uuid GPU-3719bd35-06de-4674-7c7a-e56136fed589 --cpus 8-15 --memory-limit "external: systemd-run --user --scope -p MemoryMax=8G
  -p MemorySwapMax=0 (enforced cgroup)" --runs-root <outside repo>/runs --provisional-timeout 1800`
  (one-line `--memory-limit`; resolved invocation `invocation_inner.sh` sha256 `6cb3e5a06a2f580eecbe4f5fb8c508bda79dfd2956171140f0b54e0077b1afa5`).
- **Cgroup enforcement probe (read from inside the scope)**: `scope_cgroup=/sys/fs/cgroup/user.slice/user-1030.slice/user@1030.service/app.slice/run-rf8361516bc6f4889b4d949bbff23446e.scope`,
  **`memory.max=8589934592`**, **`memory.swap.max=0`** (expected 8,589,934,592 and 0; a different value
  was a STOP), `which python` after PATH/VIRTUAL_ENV → `/home/dowling/r1_trackg_20261117/envs/torch312/bin/python`, Python 3.12.16 (`cgroup_probe.txt`).
- **rc 0; `CHECKLIST_E_PASSED mlgym_cifar10`; `SMOKE_EXIT=0`; `systemd_run_rc=0`** (smoke stdout
  `smoke_stdout_extract.txt` sha256 `1ec869a0c161665139bf7f01e56c58a2a6f22cf1e8206acd6fb57f43114e0ba7`; log `logs/run_node.log` sha256 `ee90f0eec3680fcfe2dca3c547ea37bfccd36164be2b9021e9f5b2ce47017977`).
- **`time -v` for the whole smoke (aggregate, not a per-run peak)**: user **251.05 s**, system **15.32 s**,
  wall **4:18.83**, max RSS **1,493,864 kB** (`time_v.txt`).
- Timeout: provisional 1800 s; **node timeout = 3 × measured B1 = 95.193 s**; no timeout and no OOM
  occurred; no timeout/OOM retry. **No resume (R3 mR10):** an interrupted unit re-runs wholly from a new
  `<runs-root>`; no resume occurred here.
- `--runs-root` outside the repository: this capture's `runs/`; post-run **run root 3.9 M** (`runs_du.txt`;
  the pre-run `4.0K` in `disk_before.txt` is not the footprint).

**Result — B1/B2 and every edit outcome** (`outcome.value` is the node's **validation** accuracy
(`metric_name: val_accuracy`, `selection_split: validation`, `AR_METRIC val_accuracy=…`), as the kit reports it;
the sealed test metric is `AR_TEST test_accuracy=…` → `sealed.test_accuracy` (M2: `outcome.value` is **not** "test
accuracy"; the census row must name `val_accuracy` for it and keep `test_accuracy` separate); these torch nodes
have no `val_bpb`).

| run | kind | executed | `outcome.value` | `elapsed_seconds_info_only` | `sealed.test_accuracy` |
|---|---|---|---|---|---|
| `s000_baseline` | baseline | true | **0.491** | 31.731 s | 0.4926 |
| `s001` | frozen-diff refused (`scope_violation`) | **false** | — (null) | — | — |
| `s002` | broken diff `divergent/non_finite_loss` | true | — (divergent) | 32.977 s | 0.0 |
| `s003` | first declared edit (kept) | true | 0.5486 | 31.27 s | 0.5492 |
| `E1` | declared edit | true | 0.5486 | 28.043 s | 0.5492 |
| `E2` | declared edit | true | 0.7008 | 30.941 s | 0.7077 |
| `E3` | declared edit | true | 0.648 | 35.948 s | 0.6529 |
| `E4` | declared edit | true | 0.4562 | 35.283 s | 0.4585 |
| `B2` | repeat baseline | true | **0.491** | 31.244 s | 0.4926 |

- 9 `run_record.json`, **8 executed + the refused frozen diff (`s001` `executed:false`)**; `B2` repeats B1
  (value 0.491 vs 0.491; sealed 0.4926 vs 0.4926). Baseline record
  `runs/…/s000_baseline/run_record.json` sha256 **`645795caba6760dea6512e0a979d0c9bd74771f283fa364fdebad56c0bcad252`** (run.log sha256 `8f210cd6ff266a23e44d2fb8aa4d861caf7cc0aa9dae0b38e9797f529db0ce18`, result-channel
  sha256 `a3d987ed949385b0f8d738ceca5b0a7bb872f7dec6d26539e8af14e49906f1ae`); every per-run record/log/result-channel hash is in `record_hashes.txt`.
- Pre-run reference only (accepted kit update engineering smoke): `24.07 s / val_accuracy 0.491`; this unit recorded its own
  B1/B2 above.

**Isolation record gate (every executed record).**

- Every executed record: `isolation.effective: true`, `isolation.waivers {}`, `isolation.exceptions []`,
  `log_intact: true`, result channel present (`result_channel_overflow: false`, `result_channel_sha256`
  recorded), cgroup kill `method: cgroup.kill` with `empty_after: true` and `removed: true`,
  `determinism.not_forced == ["dataloader_workers"]`, `limits.external_limit` exactly the one-line unit
  string, `gpu_uuids == ["GPU-3719bd35-06de-4674-7c7a-e56136fed589"]`, `cpu_list [8..15]`, `memory_method: external`,
  provisional timeout 1800 s, timeout factor 3.0. `s001` is `executed:false`, `outcome:null`,
  `scope_violation`, no isolation fields (by design; not a failure).
- Verifiers: `scripts/verify_u2_records.py` **rc 0, `ok: True`, 9 records /
  8 executed / refused_s001 True** (`verify_full.json`,
  `verify_full.summary.txt`); accepted kit helper `verify_records.py` **rc 0, issues []**
  (`verify_records.json`); `collect_smoke_summary.py` **rc 0, gate_ok True, issues
  []** (`summary.json`). Final run-node status: **PASS**
  (`RESULT_STATUS.txt`); `DONE`: DONE_PASS 2026-11-19T03:57:51Z.

**Disk / footprint.**

- `df -B1 /` (`/dev/md0p3`, mounted `/`) before: **74,604,687,360 B (69.5 GiB) available**; after: 74,597,408,768 B
  (69.5 GiB) — above the 50 GiB STOP floor both before and after. **Post-run footprint:** this node's evidence
  **4.3 M**, runs **3.9 M**, node data 177M, whole data root 2.9G (`disk_after.txt`, `runs_du.txt`). The values
  `evidence 60K, runs 4.0K` in `disk_before.txt` are the **pre-run** sizes and are not the footprint (M1); nothing
  deleted, no push, no commit.

**Deviations.**

- none in the smoke, the record gate or any required capture: no card switch, no co-tenant, no timeout/OOM, no waiver,
  no synthetic marker, no retry.
- **Metric-label correction (M2):** `outcome.value` was previously called "test accuracy"; it is the validation
  accuracy (`val_accuracy`, selection split) and the sealed `test_accuracy` is separate — numbers unchanged, label
  corrected (see the Result heading and `val_accuracy` in the baseline `result_channel.txt`).
- **Launcher dry-runs (S1, campaign-level).** Two Ada launcher dry-runs for `mlab_cifar10`
  (`dryrun_u2_iso_mlab_cifar10_20261119T033214Z`, `dryrun2_u2_iso_mlab_cifar10_20261119T033708Z`) are preserved in
  the campaign evidence root; the first ran `taskset -c 0-7 … true -m tests.trackg.port_smoke_gpu …` (`true`
  swallows the smoke arguments) and the second a Python/torch-only dry check, each with the same trailing smoke args.
  Neither executed a U2 run nor any GPU work; both correctly went `STOP` on missing `CHECKLIST_E_PASSED`. They are
  **not smokes and not retries**.

**Scope statements.** One node only (`mlgym_cifar10`); this result is not evidence, has no noise floor / D21 / D28,
no T1 label, no U3/unisolated claim, and is not pooled with any other node. No other user's GPU
process/card was touched or disturbed; no authors' other experiments were run; no autoresearch (C3-blocked),
HousePrice (STOP) or Breakout (not run) node was executed. One smoke only; no retry.

**Evidence index (this directory).** `SHA256SUMS` (every capture below; regenerated after the record corrections
and verified `shasum -a 256 -c` rc 0).
`logs/run_node.log` (outer log with gate/scope/smoke stdout/CHECKLIST), `smoke_stdout_extract.txt`,
`cgroup_probe.txt`, `time_v.txt`, `invocation_inner.sh`, `gate/`, `gpu/` (qualify/before/mid/after),
`sampler/` (required + timestamped CSV, `sampler_max.json`), `host.txt`, `env.txt`, `env_freeze.txt`,
`data_manifest.txt`, `kit.txt`, `pins.txt`, `disk_before.txt`, `disk_after.txt`, `runs_du.txt`,
`record_hashes.txt`, `summary.json`, `verify_records.json`, `verify_full.json`, `RESULT_STATUS.txt`, `DONE`,
`unit/` (the executed unit bytes), `static/` (the kit static-test log and README), `scripts/` (the launch-time
runner/verifier/sampler-max sources, the two documented fix patches, and a README), and the nine per-run
`runs/…/{run_record.json,run.log,result_channel.txt}` (plus the smoke work trees). Raw run trees and helper logs
are **preserved unaltered** on Ada under
`/home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlgym_cifar10_20261119T035326Z/` (live dirs `drwxrwxr-x`,
files `-rw-rw-r--`, hash-matching; not filesystem-read-only) — no deletion.

**Correction note (2026-11-19T04:30Z).** This record was corrected per the accepted MINOR-only conditions of
`docs/r1/reviews/TRACKG_U2_ISO_RESULTS_REVIEW_20261119.md` (node M1–M2 + shared S1–S10), without re-running GPU/U2
and without changing any measured number except where a cited source was wrong. Changes: M1 footprint now the
post-run `runs_du.txt` 3.9 M / `disk_after.txt` evidence 4.3 M (not `evidence 60K, runs 4.0K`), and "run root 4.0K"
corrected; M2 `outcome.value` relabelled **validation accuracy** (`AR_METRIC val_accuracy`) with `AR_TEST
test_accuracy` as the sealed metric and the census row directed to `val_accuracy`; data-root wording (S7), read-only
wording (S8), `data_link=` print (S9), floor basis/mid-run rule (S5), no-resume (S6), mR6/shas (S3), dry-runs (S1),
executed-unit preservation (S10) added; full kit report/review and R3 shas cited in the header. Full change list and
the new record/SHA256SUMS shas are in `docs/r1/reports/trackg_g0_20261117/U2_ISO_RECORD_CORRECTIONS_20261119.md`.
