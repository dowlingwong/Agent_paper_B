# Track G G.0 U2 isolated-node raw cost — node `mlgym_fmnist` — RESULT (19 November 2026)

**Status: PASSED — `CHECKLIST_E_PASSED mlgym_fmnist`; one node only, one smoke, no retry.**
Authority: `R1-TRACKG-G0-GO` (one node per unit, independently reviewed), `R1-HARNESS-ISOLATION`,
`R1-TRACKG-PORT-DECISIONS` (node timeout = 3 × measured B1; a timeout is the proposal's failure, not an
infrastructure retry), port report `docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md` §2/§7, the accepted kit
update `docs/r1/reports/trackg_g0_20261117/TRACKG_ISO_KIT_UPDATE_20261119.md` (sha256
`fe232e2bbf236337e208f11e97c809f8a41d7ef101567eeb0d11153bacb9d026`) with review
`docs/r1/reviews/TRACKG_ISO_KIT_UPDATE_REVIEW_20261119.md` (sha256
`d8c68f9f0463d1aa3e17f82527dfb7ecf7b6070831584cd1024a6d39ed6a21b4`, ACCEPTED), and `R1-TRACKG-LICENCES`. Unit
`docs/r1/proposals/u2_iso_20261119/U2_ISO_MLGYM_FMNIST_UNIT_20261119.md` (revision 3 **as amended with the R3 pre-execution
conditions mR1/mR7**;
current file sha256 `0f124d107424bc5f0c0c166211beced242d5c599519b91ecbc4623f41f329421`), accepted by review R3
`docs/r1/reviews/TRACKG_U2_ISO_UNITS_REVIEW_R3_20261119.md` (sha256
`99daf16db0b53b807c7796d4d8c8d2812573f2816a42072d7b6dc6f588ca5fb7`; 0 BLOCKING / 0 MAJOR / MINOR,
`ACCEPTED`).
ENGINEERING_ONLY; **not evidence**; no noise floor/D21/D28; no T1 label; no cross-node pooling; no
TASL-7/TASL-2, no HTCondor/deepthought, no other host; no deletion; no commit/push; read-only on Mac records
(only this new result directory is written).

**Kit / environment.**

- Suite **MLGym**, node `mlgym_fmnist`; kit worktree `/home/dowling/r1_trackg_20261117/harness_iso_mlgym`, branch `mac-trackg-iso-mlgym-20261117`, **tip `f07875de79a5a57739227b13e0fd52d31646edaf`**; launch
  check `git rev-parse HEAD` = tip and `git status --porcelain --untracked-files=no` empty (only the expected
  untracked runtime `data` symlink(s)) — capture `kit.txt`.
- Python **3.12.16** (`/home/dowling/r1_trackg_20261117/envs/torch312`), torch **2.6.0+cu124 12.4**, CUDA available
  `True 8`; `uv pip freeze` **77 lines**, sha256 **`d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42`** (`env_freeze.txt`,
  `env.txt`).
- Host `ucrtasl`, `Ubuntu 22.04.5 LTS`, kernel `5.15.0-151-generic`, 96 CPUs, driver
  **545.23.08**, boot id `5c90a8fe-5f9b-4914-a2c7-5b864e0a8b8d` (`host.txt`).
- **Data** `AR_TRACKG_DATA_ROOT=/home/dowling/r1_trackg_20261117/data` (outside the repository); node data
  link `third_party/mlgym/nodes/mlgym_fmnist/data -> /home/dowling/r1_trackg_20261117/data/mlgym_fmnist` (`kit.txt`
  `?? third_party/mlgym/nodes/mlgym_fmnist/data`; deployed pin `data: link:` entry); manifest sha256
  **`8d28287b819353ee725561bbeec10a7aa0b53a7b76e08c606167e61edd082b9c`** (4 manifest files, 0 setup_only); 5 files / 55441463 bytes on disk,
  53M (node data tree); whole data root 2.9G; manifest and node data tree `dr-xr-xr-x` / `r--r--r--`.
  **Node data dir not writable** (`data_manifest.txt` tests `[ -w "$BASE/data/mlgym_fmnist" ]`; `data_root_writable=no`)
  and ro-bound in the worker sandbox; the **top-level `data/` root is operator-writable** (`drwxrwxr-x`) — the claim
  that matters is the node data read-only/ro-bind, not the whole root. The `data_link=` line in `data_manifest.txt`
  prints `readlink -f` and re-prints the absolute target, so the in-kit symlink path is implicit (cosmetic; the
  symlink path above is the in-kit one). **No `synthetic` marker** (`data_manifest.txt`). Setup command
  (accepted kit update §5, not re-run; data link and manifest re-verified now): `cd nodes/mlgym_fmnist &&
  envs/torch312/bin/python prepare_data.py --out $AR_TRACKG_DATA_ROOT/mlgym_fmnist` (accepted setup log
  `/home/dowling/r1_engineering/iso_kit_update_20261119/data/setup_mlgym_fmnist.log`, sha256 `7c0b284e221dbc90b360f87786a981ac935f0181c6422ecd2d597793a28fa1a5`).
- **Static tests** (mlgym kit; CPU-masked `taskset -c 0-15`, `CUDA_VISIBLE_DEVICES=`, delegated user
  cgroup, interpreter `envs/torch312/bin/python`, `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1
  -p no:cacheprovider`): `python -m pytest tests/trackg -q -p no:cacheprovider -k "not smoke"` →
  **225 passed, 2 failed, 1 skipped, 6 deselected in 46.06 s**, log `static/static_mlgym_20261119T033511Z.log` sha256 `8d8a0fb591e2c80352f462c4e9322bcbe938236ac87ed7a11fa22d448714ce35`. The two failures are the
  accepted kit-update §4 documented environment failures (round-2 child-kill test under `/usr/bin/python3`
  3.10; `langchain-openai` missing for the t0 identity test); same counts as the accepted post-update run; no
  test was skipped or weakened.
- **Licence/provenance.** MLGym subtree **CC BY-NC 4.0** non-commercial with notice; Fashion-MNIST generic citation; the gymnax-derived Apache-2.0 parts are not used by this node (`R1-TRACKG-LICENCES`).

**Pins (both, separately; no interchange).**

- **Committed-file `frozen_pin_sha256`** (accepted kit update §3/§10.2 convention; `pins/new_mlgym.json` sha256
  `8974359b1fd5c11105dc98b593dcb1c84b33d59896fe3e63bf7cb6c3b1e4a451`): **`eb60107ee2a329ac1f6b919f0d632e1fc84f1e6440b704010891398096c841b3`** (16 frozen entries; this is the census value).
- **Deployed run-record pin** (every run record's `frozen_pin_sha256`, which also hashes the
  `data: link:<absolute target>` symlink; matches `pins/deployed_mlgym.json` sha256 `dcfcb0808445c0af2ee851a27047be89202420f340e815d6f9ad0443b1ea4ee0`):
  **`ef8043389dbd55a9a01d192227f0483daf2a406043b0a1feaf74eba4d858ddee`**; expected deployed value `ef8043389dbd55a9a01d192227f0483daf2a406043b0a1feaf74eba4d858ddee`, constant across all nine records.

**Record identity and preserved bytes (S3/S10).** This result file is
`docs/r1/reports/trackg_g0_20261117/u2_iso_mlgym_fmnist_20261119T035842Z/U2_ISO_MLGYM_FMNIST_RESULT_20261119.md`;
its own post-correction sha256 is the `./U2_ISO_MLGYM_FMNIST_RESULT_20261119.md` entry in this directory's
regenerated `SHA256SUMS` (the `SHA256SUMS` sha256 is recorded in `U2_ISO_RECORD_CORRECTIONS_20261119.md`). Node spec:
raw `third_party/mlgym/configs/trackg/nodes/mlgym_fmnist.yaml` sha256
`a9844f013dfb204b363386e1af68c5f2e5b837e289c83a91ee6babb53d52378b`, canonical `node_spec_sha256` (kit loader:
`sha256(json.dumps(payload, sort_keys=True, separators=(",",":"), ensure_ascii=False, default=str))`)
`65f229affedca7abcc0a78792053cf5fa3c8a1237bf683298faa03e674a152e9` (= every run record's value). Representative-edit
manifest sha256 `de6782b31d529a759176ddc7c8e1b922c37d434a2c379c3ef3143dfe5fa8db37`; representative edits E1/E2/E3/E4
diff sha256 `6d806f90…`, `ecb86f50…`, `5cc131aa…`, `58c33a33…` (full values in `kit.txt`). Executed unit bytes are
preserved at `unit/U2_ISO_MLGYM_FMNIST_UNIT_20261119.md` (sha256
`0f124d107424bc5f0c0c166211beced242d5c599519b91ecbc4623f41f329421`, = the recorded executed unit). Preserved
runner/helper bytes (this directory's `scripts/`): **launch-time/final** `run_node.sh` sha256
`13a45d7baf7dacac6da2ef1455e86fc794c25fd90f5a835511b50aafccc99444` (patch3 was applied at 19:50Z, before this
node's 19:58Z launch, so these are the launch-time bytes), `_patch2_verifier_s002_fix.py`
`681d9f8a2d25eef0d2c1947e7bace55b1ade5c0fe9f6cbf64ae458b4b97b5353`, `_patch3_mid_watcher_fix.py`
`ce2ff3b0ecdb61cdbbad615bef47abd6a34473bb42bc45358eefe00cbb18fc39`, `compute_sampler_max.py`
`7d9f472ec1e24ba879f2edd0fa259612f0c00133abf90309587a43ced312dbed`, `verify_u2_records.py`
`7f40ed1789fb77c29a14022db9908a46c3ca47563cd0ca6030df7aff21dd8418`. Every executed record has
`process.returncode: 0`, `process.killed_with: null` (normal exit), `process.timed_out: false`,
`leftover_processes_killed: false`; the smoke log carries one JSON record line per run (verifier `--smoke-log` check
in `verify_full.json`).

**Paper A gate (captured immediately before launch; three-check).**

- Gate JSON `/home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlgym_fmnist_20261119T035842Z/gate/gate_20261119T035842Z.json` sha256 **`1fc11b9fef3a32d3f135c7f3f6a784e0a831f1e6275398fa0c825af5eb7a6938`** (UTC `2026-11-19T03:58:46Z`; gate script rc 0; config
  `/home/dowling/r1_trackg_20261117/Agent_paper_B_main_16185b0b/r1/scripts/configs/paper_a_status_ada.json`).
- **Three-check PASS**: `verdict: clear_finished`, `paper_a_live_waiting_for_card: false`, `paper_a_processes: []`,
  `unidentified_apps: 0`.
- Newest v4 `live_*` directory == configured run dir (`newest_live_equals_configured=yes`); self-excluded
  `pgrep` for `port_smoke_gpu` empty; `pgrep agent-checkpoint-intervention` empty (`gate/gate_check.txt`).

**GPU gate / co-tenancy (idle card only).**

- Selected **UUID `GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154`**: 48427 MiB free, **0 % utilization, no other user's compute app**
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
  `b34c2d7d8af61570e432847f1007883e5041feec2133893f3b3110c7ff011ca5`, 2270 app rows) plus a concurrent timestamped
  companion used only to group rows into per-sample sums (`sampler/sampler_timestamped.csv` sha256
  `a54dd19b448df2dbef12866c5f685eb9cac436cec7610a33af236132f7332590`); 288.9 s sampled,
  261 samples carried the used card, 8 distinct worker pids
  (all this smoke).
- **Peak reported as a whole-smoke upper bound = 912 MiB** (max single-row
  `used_memory` 912 MiB = max per-sample sum 912 MiB on the
  used card; CSV header not counted). **Label: whole-smoke upper bound over the used GPU, including any
  co-tenant by construction; NOT a per-run peak and NOT attributed to the baseline process tree.** The card
  returned to idle after the smoke (`gpu/gpu_after.txt`).
- Mid-run census (`gpu/gpu_mid.txt`):
  ```
  # gpu mid (used=729 MiB) 2026-11-19T03:58:52Z
index, uuid, memory.total [MiB], memory.used [MiB], memory.free [MiB], utilization.gpu [%]
0, GPU-9be33fd1-8eeb-497d-772a-87362d6720be, 49140 MiB, 12383 MiB, 36050 MiB, 52 %
1, GPU-aa340032-6f94-9783-8f3d-50a15da47a6f, 49140 MiB, 5 MiB, 48427 MiB, 0 %
2, GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154, 49140 MiB, 729 MiB, 47703 MiB, 10 %
3, GPU-5d61f1bc-1a65-f322-6feb-3aeaf6051f94, 49140 MiB, 38918 MiB, 9515 MiB, 35 %
4, GPU-379470db-a02e-893a-57a0-71b119173890, 49140 MiB, 15529 MiB, 32903 MiB, 0 %
5, GPU-5357dc5f-5d1d-af80-a3f4-3eb5aeb38f0d, 49140 MiB, 12283 MiB, 36149 MiB, 49 %
6, GPU-3b36edea-1a09-a37e-aa42-8277c7319e77, 49140 MiB, 5 MiB, 48427 MiB, 0 %
7, GPU-3719bd35-06de-4674-7c7a-e56136fed589, 49140 MiB, 5 MiB, 48427 MiB, 0 %
# compute apps
gpu_uuid, pid, used_gpu_memory [MiB]
  ```

**Run (unit command shape, exactly one smoke).**

- Inside `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c '…'`
  (logged unit line in `logs/run_node.log`): `cd harness_iso_mlgym`, `CG=$(cut -d: -f3 /proc/self/cgroup)`,
  `AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG`, `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1`,
  `PATH=…/envs/torch312/bin:$PATH`, `VIRTUAL_ENV=…/envs/torch312`, `CUDA_VISIBLE_DEVICES=""`,
  `AR_TRACKG_DATA_ROOT=…/data`, `taskset -c 8-15 python -m tests.trackg.port_smoke_gpu --node mlgym_fmnist
  --gpu-uuid GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154 --cpus 8-15 --memory-limit "external: systemd-run --user --scope -p MemoryMax=8G
  -p MemorySwapMax=0 (enforced cgroup)" --runs-root <outside repo>/runs --provisional-timeout 1800`
  (one-line `--memory-limit`; resolved invocation `invocation_inner.sh` sha256 `e4084c5fecbaca9f12486da5553d3ce65f78052be0f395f8eac613cbac92db80`).
- **Cgroup enforcement probe (read from inside the scope)**: `scope_cgroup=/sys/fs/cgroup/user.slice/user-1030.slice/user@1030.service/app.slice/run-r2e20932cd4a8477495f6a98186d4a77a.scope`,
  **`memory.max=8589934592`**, **`memory.swap.max=0`** (expected 8,589,934,592 and 0; a different value
  was a STOP), `which python` after PATH/VIRTUAL_ENV → `/home/dowling/r1_trackg_20261117/envs/torch312/bin/python`, Python 3.12.16 (`cgroup_probe.txt`).
- **rc 0; `CHECKLIST_E_PASSED mlgym_fmnist`; `SMOKE_EXIT=0`; `systemd_run_rc=0`** (smoke stdout
  `smoke_stdout_extract.txt` sha256 `ff27da6e4350f1a4091f991785869ffa69723ca61f4228301506c58f369c37e9`; log `logs/run_node.log` sha256 `ae06733b12991e9d102dff0442c2ee8b8549dc832d224595dd527b6150160358`).
- **`time -v` for the whole smoke (aggregate, not a per-run peak)**: user **280.78 s**, system **14.86 s**,
  wall **4:49.02**, max RSS **1,213,024 kB** (`time_v.txt`).
- Timeout: provisional 1800 s; **node timeout = 3 × measured B1 = 103.128 s**; no timeout and no OOM
  occurred; no timeout/OOM retry. **No resume (R3 mR10):** an interrupted unit re-runs wholly from a new
  `<runs-root>`; no resume occurred here.
- `--runs-root` outside the repository: this capture's `runs/`; post-run **run root 3.9 M** (`runs_du.txt`;
  the pre-run `4.0K` in `disk_before.txt` is not the footprint).

**Result — B1/B2 and every edit outcome** (`outcome.value` is the node's **validation** accuracy
(`metric_name: val_accuracy`, `selection_split: validation`, `AR_METRIC val_accuracy=…`), as the kit reports it;
the sealed test metric is `AR_TEST test_accuracy=…` → `sealed.test_accuracy` (F2: `outcome.value` is **not** "test
accuracy"; the census row must name `val_accuracy` for it and keep `test_accuracy` separate); these torch nodes
have no `val_bpb`).

| run | kind | executed | `outcome.value` | `elapsed_seconds_info_only` | `sealed.test_accuracy` |
|---|---|---|---|---|---|
| `s000_baseline` | baseline | true | **0.861667** | 34.376 s | 0.8515 |
| `s001` | frozen-diff refused (`scope_violation`) | **false** | — (null) | — | — |
| `s002` | broken diff `divergent/non_finite_loss` | true | — (divergent) | 36.9 s | 0.0 |
| `s003` | first declared edit (kept) | true | 0.877833 | 36.759 s | 0.8699 |
| `E1` | declared edit | true | 0.877833 | 36.711 s | 0.8699 |
| `E2` | declared edit | true | 0.927833 | 34.274 s | 0.9181 |
| `E3` | declared edit | true | 0.909333 | 40.795 s | 0.8964 |
| `E4` | declared edit | true | 0.769 | 38.908 s | 0.7657 |
| `B2` | repeat baseline | true | **0.861667** | 28.868 s | 0.8515 |

- 9 `run_record.json`, **8 executed + the refused frozen diff (`s001` `executed:false`)**; `B2` repeats B1
  (value 0.861667 vs 0.861667; sealed 0.8515 vs 0.8515). Baseline record
  `runs/…/s000_baseline/run_record.json` sha256 **`9838015e3a174214396bba612576b41883cc326472f06f33a020e197cff68a34`** (run.log sha256 `7aaf4f69e3849a70650e7bd4edb6f883b565ae1336789e31f244734c3347e8cd`, result-channel
  sha256 `94cb99260e8f01610bc1fb879dbb98324fcdb2ca31a0572e9c7572996a50b801`); every per-run record/log/result-channel hash is in `record_hashes.txt`.
- Pre-run reference only (accepted kit update engineering smoke): `26.702 s / val_accuracy 0.861667`; this unit recorded its own
  B1/B2 above.

**Isolation record gate (every executed record).**

- Every executed record: `isolation.effective: true`, `isolation.waivers {}`, `isolation.exceptions []`,
  `log_intact: true`, result channel present (`result_channel_overflow: false`, `result_channel_sha256`
  recorded), cgroup kill `method: cgroup.kill` with `empty_after: true` and `removed: true`,
  `determinism.not_forced == ["dataloader_workers"]`, `limits.external_limit` exactly the one-line unit
  string, `gpu_uuids == ["GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154"]`, `cpu_list [8..15]`, `memory_method: external`,
  provisional timeout 1800 s, timeout factor 3.0. `s001` is `executed:false`, `outcome:null`,
  `scope_violation`, no isolation fields (by design; not a failure).
- Verifiers: `scripts/verify_u2_records.py` **rc 0, `ok: True`, 9 records /
  8 executed / refused_s001 True** (`verify_full.json`,
  `verify_full.summary.txt`); accepted kit helper `verify_records.py` **rc 0, issues []**
  (`verify_records.json`); `collect_smoke_summary.py` **rc 0, gate_ok True, issues
  []** (`summary.json`). Final run-node status: **PASS**
  (`RESULT_STATUS.txt`); `DONE`: DONE_PASS 2026-11-19T04:03:38Z.

**Disk / footprint.**

- `df -B1 /` (`/dev/md0p3`, mounted `/`) before: **74,596,868,096 B (69.5 GiB) available**; after: 74,548,490,240 B
  (69.4 GiB) — above the 50 GiB STOP floor both before and after. **Post-run footprint:** this node's evidence
  **4.4 M**, runs **3.9 M**, node data 53M, whole data root 2.9G (`disk_after.txt`, `runs_du.txt`). The values
  `evidence 60K, runs 4.0K` in `disk_before.txt` are the **pre-run** sizes and are not the footprint (F1); nothing
  deleted, no push, no commit.

**Deviations.**

- none in the smoke, the record gate or any required capture: no card switch, no co-tenant, no timeout/OOM, no waiver,
  no synthetic marker, no retry.
- **Metric-label correction (F2):** `outcome.value` was previously called "test accuracy"; it is the validation
  accuracy (`val_accuracy`, selection split) and the sealed `test_accuracy` is separate — numbers unchanged, label
  corrected (see the Result heading and `val_accuracy` in the baseline `result_channel.txt`).
- **Wrong-timestamp local directory (S2).** `u2_iso_mlgym_fmnist_20261119T035909Z_WRONG_TS_MOVED_ASIDE/` (in the
  reports tree) was a wrong-timestamp staging copy containing only byte-identical `static/`+`scripts/` duplicates of
  this node and no run evidence. It was **moved, not deleted**, out of the reports tree to
  `docs/r1/reports_moved_aside/u2_iso_mlgym_fmnist_20261119T035909Z_WRONG_TS/` (with a README recording its origin
  and the eight sha256-equal duplicate files); it is not evidence and not a result directory.
- **Launcher dry-runs (S1, campaign-level).** Two Ada launcher dry-runs for `mlab_cifar10`
  (`dryrun_u2_iso_mlab_cifar10_20261119T033214Z`, `dryrun2_u2_iso_mlab_cifar10_20261119T033708Z`) are preserved in
  the campaign evidence root; the first ran `taskset -c 0-7 … true -m tests.trackg.port_smoke_gpu …` (`true`
  swallows the smoke arguments) and the second a Python/torch-only dry check, each with the same trailing smoke args.
  Neither executed a U2 run nor any GPU work; both correctly went `STOP` on missing `CHECKLIST_E_PASSED`. They are
  **not smokes and not retries**.

**Scope statements.** One node only (`mlgym_fmnist`); this result is not evidence, has no noise floor / D21 / D28,
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
`/home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlgym_fmnist_20261119T035842Z/` (live dirs `drwxrwxr-x`, files
`-rw-rw-r--`, hash-matching; not filesystem-read-only) — no deletion. The wrong-timestamp duplicate staging dir was
moved (not deleted) to `docs/r1/reports_moved_aside/u2_iso_mlgym_fmnist_20261119T035909Z_WRONG_TS/` (see Deviations).

**Correction note (2026-11-19T04:30Z).** This record was corrected per the accepted MINOR-only conditions of
`docs/r1/reviews/TRACKG_U2_ISO_RESULTS_REVIEW_20261119.md` (node F1–F2, S2 + shared S1/S3–S10), without re-running
GPU/U2 and without changing any measured number except where a cited source was wrong. Changes: F1 footprint now the
post-run `runs_du.txt` 3.9 M / `disk_after.txt` evidence 4.4 M (not `evidence 60K, runs 4.0K`), and "run root 4.0K"
corrected; F2 `outcome.value` relabelled **validation accuracy** (`AR_METRIC val_accuracy`) with `AR_TEST
test_accuracy` as the sealed metric and the census row directed to `val_accuracy`; S2 wrong-timestamp dir moved out of
the reports tree and documented; data-root wording (S7), read-only wording (S8), `data_link=` print (S9), floor
basis/mid-run rule (S5), no-resume (S6), mR6/shas (S3), dry-runs (S1), executed-unit preservation (S10) added; full
kit report/review and R3 shas cited in the header. Full change list and the new record/SHA256SUMS shas are in
`docs/r1/reports/trackg_g0_20261117/U2_ISO_RECORD_CORRECTIONS_20261119.md`.
