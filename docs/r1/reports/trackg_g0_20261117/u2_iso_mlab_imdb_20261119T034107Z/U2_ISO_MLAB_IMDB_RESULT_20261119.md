# Track G G.0 U2 isolated-node raw cost — node `mlab_imdb` — RESULT (19 November 2026)

**Status: PASSED — `CHECKLIST_E_PASSED mlab_imdb`; one node only, one smoke, no retry.**
Authority: `R1-TRACKG-G0-GO` (one node per unit, independently reviewed), `R1-HARNESS-ISOLATION`,
`R1-TRACKG-PORT-DECISIONS` (node timeout = 3 × measured B1; a timeout is the proposal's failure, not an
infrastructure retry), port report `docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md` §2/§7, the accepted kit
update `docs/r1/reports/trackg_g0_20261117/TRACKG_ISO_KIT_UPDATE_20261119.md` (sha256
`fe232e2bbf236337e208f11e97c809f8a41d7ef101567eeb0d11153bacb9d026`) with review
`docs/r1/reviews/TRACKG_ISO_KIT_UPDATE_REVIEW_20261119.md` (sha256
`d8c68f9f0463d1aa3e17f82527dfb7ecf7b6070831584cd1024a6d39ed6a21b4`, ACCEPTED), and `R1-TRACKG-LICENCES`. Unit
`docs/r1/proposals/u2_iso_20261119/U2_ISO_MLAB_IMDB_UNIT_20261119.md` (revision 3 **as amended with the R3 pre-execution
conditions mR1/mR7**, mR8b, mR11;
current file sha256 `bbc02cc55390341ded0ea48d1aae320778b1ee56ea8ab66c42d15d6c78349d9d`), accepted by review R3
`docs/r1/reviews/TRACKG_U2_ISO_UNITS_REVIEW_R3_20261119.md` (sha256
`99daf16db0b53b807c7796d4d8c8d2812573f2816a42072d7b6dc6f588ca5fb7`; 0 BLOCKING / 0 MAJOR / MINOR,
`ACCEPTED`).
ENGINEERING_ONLY; **not evidence**; no noise floor/D21/D28; no T1 label; no cross-node pooling; no
TASL-7/TASL-2, no HTCondor/deepthought, no other host; no deletion; no commit/push; read-only on Mac records
(only this new result directory is written).

**Kit / environment.**

- Suite **MLAgentBench**, node `mlab_imdb`; kit worktree `/home/dowling/r1_trackg_20261117/harness_iso_mlab`, branch `mac-trackg-iso-mlab-20261117`, **tip `fb6e7d73ddd2d9b962cbb65a85908ce48d25dca9`**; launch
  check `git rev-parse HEAD` = tip and `git status --porcelain --untracked-files=no` empty (only the expected
  untracked runtime `data` symlink(s)) — capture `kit.txt`.
- Python **3.12.16** (`/home/dowling/r1_trackg_20261117/envs/torch312`), torch **2.6.0+cu124 12.4**, CUDA available
  `True 8`; `uv pip freeze` **77 lines**, sha256 **`d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42`** (`env_freeze.txt`,
  `env.txt`).
- Host `ucrtasl`, `Ubuntu 22.04.5 LTS`, kernel `5.15.0-151-generic`, 96 CPUs, driver
  **545.23.08**, boot id `5c90a8fe-5f9b-4914-a2c7-5b864e0a8b8d` (`host.txt`).
- **Data** `AR_TRACKG_DATA_ROOT=/home/dowling/r1_trackg_20261117/data` (outside the repository); node data
  link `nodes/mlab_imdb/data -> /home/dowling/r1_trackg_20261117/data/mlab_imdb` (`kit.txt` `?? nodes/mlab_imdb/data`;
  deployed pin `data: link:` entry); manifest sha256 **`a87254e16dfd13ad606e69ab357d02715773c0a442f5e59de42788c7cbcb935c`** (11 manifest files, 1 setup_only); 23 files / 397056204 bytes on disk,
  379M (node data tree); whole data root 2.9G; manifest and node data tree `dr-xr-xr-x` / `r--r--r--`.
  **Node data dir not writable** (`data_manifest.txt` tests `[ -w "$BASE/data/mlab_imdb" ]`; `data_root_writable=no`)
  and ro-bound in the worker sandbox; the **top-level `data/` root is operator-writable** (`drwxrwxr-x`) — the claim
  that matters is the node data read-only/ro-bind, not the whole root. The `data_link=` line in `data_manifest.txt`
  prints `readlink -f` and re-prints the absolute target, so the in-kit symlink path is implicit (cosmetic; the
  symlink path above is the in-kit one). **No `synthetic` marker** (`data_manifest.txt`). Setup command
  (accepted kit update §5, not re-run; data link and manifest re-verified now): `cd nodes/mlab_imdb &&
  envs/torch312/bin/python prepare_data.py --out $AR_TRACKG_DATA_ROOT/mlab_imdb` (accepted setup log
  `/home/dowling/r1_engineering/iso_kit_update_20261119/data/setup_mlab_imdb.log`, sha256 `7d70455045f5b20a4ea3ab9994c80f7e2bfea98ddd7ba44fceb2d19a8bb4d47a`).
- **Static tests** (mlab kit; CPU-masked `taskset -c 0-15`, `CUDA_VISIBLE_DEVICES=`, delegated user
  cgroup, interpreter `envs/torch312/bin/python`, `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1
  -p no:cacheprovider`): `python -m pytest tests/trackg -q -p no:cacheprovider -k "not smoke"` →
  **218 passed, 2 failed, 1 skipped, 5 deselected in 44.40 s**, log `static/static_mlab_20261119T033322Z.log` sha256 `c9e8cbd64b9c4b9199c49d91da1ff120c098e7cc4405222e66eabff952eadf77`. The two failures are the
  accepted kit-update §4 documented environment failures (round-2 child-kill test under `/usr/bin/python3`
  3.10; `langchain-openai` missing for the t0 identity test); same counts as the accepted post-update run; no
  test was skipped or weakened.
- **Licence/provenance.** IMDb text: generic research citation/disclosure; **port decision (3)**: the mlab_imdb baseline (DistilBERT fine-tuning) was **written by us**; MLAgentBench ships only a skeleton for this task, so this baseline is frozen and independently reviewed before any label run and is disclosed as ours; the census **funnel and appendix must note 'baseline written by us'** (`R1-TRACKG-PORT-DECISIONS`, port report §3(3)).

**Pins (both, separately; no interchange).**

- **Committed-file `frozen_pin_sha256`** (accepted kit update §3/§10.2 convention; `pins/new_mlab.json` sha256
  `731b713df0126414f537b69adf28acc47969f11162bcb99fe3524699d1d0c866`): **`4b1019a60b1ac96028944d1dcc02be582f84e1fab0dbfd11d00011f460fb97fb`** (16 frozen entries; this is the census value).
- **Deployed run-record pin** (every run record's `frozen_pin_sha256`, which also hashes the
  `data: link:<absolute target>` symlink; matches `pins/deployed_mlab.json` sha256 `388c09f5726f6a0e3f88a6eb756490439dda1c988c05c8b5de4464139e24ea49`):
  **`c169a6b875733cdb03d223659d06cc9a6839dd6255a924c420f10982bbefbbb0`**; expected deployed value `c169a6b875733cdb03d223659d06cc9a6839dd6255a924c420f10982bbefbbb0`, constant across all nine records.

**Record identity and preserved bytes (S3/S10).** This result file is
`docs/r1/reports/trackg_g0_20261117/u2_iso_mlab_imdb_20261119T034107Z/U2_ISO_MLAB_IMDB_RESULT_20261119.md`;
its own post-correction sha256 is the `./U2_ISO_MLAB_IMDB_RESULT_20261119.md` entry in this directory's
regenerated `SHA256SUMS` (the `SHA256SUMS` sha256 is recorded in `U2_ISO_RECORD_CORRECTIONS_20261119.md`). Node spec:
raw `configs/trackg/nodes/mlab_imdb.yaml` sha256 `96a79725f08e2630da7a8c92041e94069e789d087ed33162c7e0b2e78148b38b`,
canonical `node_spec_sha256` (kit loader: `sha256(json.dumps(payload, sort_keys=True, separators=(",",":"),
ensure_ascii=False, default=str))`) `0123a8a771f5abc1028dd83fab7afdf67afb053f7bf064c693f081ec13601510` (= every run
record's value). Representative-edit manifest sha256 `09edee58dbe18cf009276bbced98c9d534fef9cf04680a707b118f2f097ad969`;
representative edits E1/E2/E3/E4 diff sha256 `67fa8741…`, `bd23dd4a…`, `09a516ef…`, `fca63fff…` (full values in
`kit.txt`). Executed unit bytes are preserved at `unit/U2_ISO_MLAB_IMDB_UNIT_20261119.md`
(sha256 `bbc02cc55390341ded0ea48d1aae320778b1ee56ea8ab66c42d15d6c78349d9d`, = the recorded executed unit). Preserved
runner/helper bytes (this directory's `scripts/`): final `run_node.sh` sha256
`13a45d7baf7dacac6da2ef1455e86fc794c25fd90f5a835511b50aafccc99444`, `_patch2_verifier_s002_fix.py`
`681d9f8a2d25eef0d2c1947e7bace55b1ade5c0fe9f6cbf64ae458b4b97b5353`, `_patch3_mid_watcher_fix.py`
`ce2ff3b0ecdb61cdbbad615bef47abd6a34473bb42bc45358eefe00cbb18fc39`, `compute_sampler_max.py`
`7d9f472ec1e24ba879f2edd0fa259612f0c00133abf90309587a43ced312dbed`, `verify_u2_records.py`
`7f40ed1789fb77c29a14022db9908a46c3ca47563cd0ca6030df7aff21dd8418`. Every executed record has
`process.returncode: 0`, `process.killed_with: null` (normal exit), `process.timed_out: false`,
`leftover_processes_killed: false`; the smoke log carries one JSON record line per run (verifier `--smoke-log` check
in `verify_full.json`). *Residual (S10):* this node's exact launch-time runner bytes (pre-patch3) were not preserved
as a file; `_patch3_mid_watcher_fix.py` is an exact preserved string replacement, so the derivation is reproducible
but is recorded as a residual, not as a preserved snapshot.

**Paper A gate (captured immediately before launch; three-check).**

- Gate JSON `/home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlab_imdb_20261119T034107Z/gate/gate_20261119T034107Z.json` sha256 **`75a26675a396ad2b4c3b9ec392b4d92f19ed7cabd825b54b48113dc12c1fea43`** (UTC `2026-11-19T03:41:11Z`; gate script rc 0; config
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
  `5c635af0efd41d0ee9e79a95ece3694c9f0723e33684add988e5447e43838889`, 4007 app rows) plus a concurrent timestamped
  companion used only to group rows into per-sample sums (`sampler/sampler_timestamped.csv` sha256
  `2eed21af8c515ff5ae19a18a953af8115b8b386e67060a00f92216fa2ab3ad23`); 508.8 s sampled,
  472 samples carried the used card, 8 distinct worker pids
  (all this smoke).
- **Peak reported as a whole-smoke upper bound = 11292 MiB** (max single-row
  `used_memory` 11292 MiB = max per-sample sum 11292 MiB on the
  used card; CSV header not counted). **Label: whole-smoke upper bound over the used GPU, including any
  co-tenant by construction; NOT a per-run peak and NOT attributed to the baseline process tree.** The card
  returned to idle after the smoke (`gpu/gpu_after.txt`).
- Mid-run census (`gpu/gpu_mid.txt`):
  ```
  # mid-run census derived from the 1 s timestamped compute-app sampler (whole-run sampler).
# The dedicated full mid snapshot was NOT captured for this node because the launcher's mid-run watcher subshell exited on its first iteration (bash resets the special _ loop variable, so the arithmetic test errored); fixed (ordinary i) for later nodes
# derived_at=2026-11-19T03:54:07Z
selected_gpu_uuid=GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154
mid_sample_median_index=236 of 472 samples carrying the used card
compute_app gpu_uuid=GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154 pid=3845485 used_memory=11292 MiB ts=2026-11-18 19:45:27.045000
mid_used_mib_sum_on_card=11292
idle_baseline_used_mib=5 (gpu_before/gpu_after)
memory_total_mib=49140 (gpu_before/gpu_after query)
derived_memory_used_mib_approx=11297 (derived)
derived_memory_free_mib_approx=37843 (derived)
utilization_gpu_pct=NOT_CAPTURED_MID_RUN (deviation; before/after utilization recorded)
  ```

**Run (unit command shape, exactly one smoke).**

- Inside `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c '…'`
  (logged unit line in `logs/run_node.log`): `cd harness_iso_mlab`, `CG=$(cut -d: -f3 /proc/self/cgroup)`,
  `AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG`, `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1`,
  `PATH=…/envs/torch312/bin:$PATH`, `VIRTUAL_ENV=…/envs/torch312`, `CUDA_VISIBLE_DEVICES=""`,
  `AR_TRACKG_DATA_ROOT=…/data`, `taskset -c 0-7 python -m tests.trackg.port_smoke_gpu --node mlab_imdb
  --gpu-uuid GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154 --cpus 0-7 --memory-limit "external: systemd-run --user --scope -p MemoryMax=8G
  -p MemorySwapMax=0 (enforced cgroup)" --runs-root <outside repo>/runs --provisional-timeout 1800`
  (one-line `--memory-limit`; resolved invocation `invocation_inner.sh` sha256 `c747355b05c3c50e9669f3a43b77fab77278548d75042c06161de277a26c8174`).
- **Cgroup enforcement probe (read from inside the scope)**: `scope_cgroup=/sys/fs/cgroup/user.slice/user-1030.slice/user@1030.service/app.slice/run-r4cf689a2c4344e66a9de2ab8b12686ba.scope`,
  **`memory.max=8589934592`**, **`memory.swap.max=0`** (expected 8,589,934,592 and 0; a different value
  was a STOP), `which python` after PATH/VIRTUAL_ENV → `/home/dowling/r1_trackg_20261117/envs/torch312/bin/python`, Python 3.12.16 (`cgroup_probe.txt`).
- **rc 0; `CHECKLIST_E_PASSED mlab_imdb`; `SMOKE_EXIT=0`; `systemd_run_rc=0`** (smoke stdout
  `smoke_stdout_extract.txt` sha256 `68a0c99f91f82a878bb0a1bd34395bd3fb4ca08d2031ff5266b95fd101b4a6b4`; log `logs/run_node.log` sha256 `c1e2c90cea83263429a5d221e0abfbf5f2128de4a75636adf6da66cf04976682`).
- **`time -v` for the whole smoke (aggregate, not a per-run peak)**: user **498.14 s**, system **18.97 s**,
  wall **8:28.85**, max RSS **1,659,008 kB** (`time_v.txt`).
- Timeout: provisional 1800 s; **node timeout = 3 × measured B1 = 192.426 s**; no timeout and no OOM
  occurred; no timeout/OOM retry. **No resume (R3 mR10):** an interrupted unit re-runs wholly from a new
  `<runs-root>`; no resume occurred here.
- `--runs-root` outside the repository: this capture's `runs/`; post-run **run root 3.8 M** (`runs_du.txt`;
  the pre-run `4.0K` in `disk_before.txt` is not the footprint).

**Result — B1/B2 and every edit outcome** (`outcome.value` is the node's **validation** accuracy
(`metric_name: val_accuracy`, `selection_split: validation`, `AR_METRIC val_accuracy=…`), as the kit reports it;
the sealed test metric is `AR_TEST test_accuracy=…` → `sealed.test_accuracy`, and the census row must name
`val_accuracy` for `outcome.value`; these torch nodes have no `val_bpb`).

| run | kind | executed | `outcome.value` | `elapsed_seconds_info_only` | `sealed.test_accuracy` |
|---|---|---|---|---|---|
| `s000_baseline` | baseline | true | **0.9048** | 64.142 s | 0.89924 |
| `s001` | frozen-diff refused (`scope_violation`) | **false** | — (null) | — | — |
| `s002` | broken diff `divergent/non_finite_loss` | true | — (divergent) | 61.606 s | 0.0 |
| `s003` | first declared edit (kept) | true | 0.9072 | 64.987 s | 0.9008 |
| `E1` | declared edit | true | 0.9072 | 65.156 s | 0.9008 |
| `E2` | declared edit | true | 0.9016 | 64.74 s | 0.89668 |
| `E3` | declared edit | true | 0.9032 | 64.165 s | 0.89944 |
| `E4` | declared edit | true | 0.8752 | 58.561 s | 0.87224 |
| `B2` | repeat baseline | true | **0.9048** | 64.133 s | 0.89924 |

- 9 `run_record.json`, **8 executed + the refused frozen diff (`s001` `executed:false`)**; `B2` repeats B1
  (value 0.9048 vs 0.9048; sealed 0.89924 vs 0.89924). Baseline record
  `runs/…/s000_baseline/run_record.json` sha256 **`b18796e0a04149b7c334445d5235fa219b8275fcd55dcac74eea0aa1d935d010`** (run.log sha256 `e7313f954772bb46999e82cc530799e7348ad171b985bc5bd22136130c3e59c3`, result-channel
  sha256 `c3231319fa39ce68ecf91074bce651aade737a8785915c64f42bddc2e576125a`); every per-run record/log/result-channel hash is in `record_hashes.txt`.
- Pre-run reference only (accepted kit update engineering smoke): `61.399 s / val 0.9048`; this unit recorded its own
  B1/B2 above.

**Isolation record gate (every executed record).**

- Every executed record: `isolation.effective: true`, `isolation.waivers {}`, `isolation.exceptions []`,
  `log_intact: true`, result channel present (`result_channel_overflow: false`, `result_channel_sha256`
  recorded), cgroup kill `method: cgroup.kill` with `empty_after: true` and `removed: true`,
  `determinism.not_forced == ["dataloader_workers"]`, `limits.external_limit` exactly the one-line unit
  string, `gpu_uuids == ["GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154"]`, `cpu_list [0..7]`, `memory_method: external`,
  provisional timeout 1800 s, timeout factor 3.0. `s001` is `executed:false`, `outcome:null`,
  `scope_violation`, no isolation fields (by design; not a failure).
- Verifiers: `scripts/verify_u2_records.py` **rc 0, `ok: True`, 9 records /
  8 executed / refused_s001 True** (`verify_full.json`,
  `verify_full.summary.txt`); accepted kit helper `verify_records.py` **rc 0, issues []**
  (`verify_records.json`); `collect_smoke_summary.py` **rc 0, gate_ok True, issues
  []** (`summary.json`). Final run-node status: **PASS**
  (`RESULT_STATUS.txt`); `DONE`: DONE_PASS 2026-11-19T03:49:43Z.

**Disk / footprint.**

- `df -B1 /` (`/dev/md0p3`, mounted `/`) before: **74,629,115,904 B (69.5 GiB) available**; after: 74,609,201,152 B
  (69.5 GiB) — above the 50 GiB STOP floor both before and after. **Post-run footprint:** this node's evidence
  **4.5 M**, runs **3.8 M**, node data 379M, whole data root 2.9G (`disk_after.txt`, `runs_du.txt`). The values
  `evidence 60K, runs 4.0K` in `disk_before.txt` are the **pre-run** sizes and are not the footprint (I2); nothing
  deleted, no push, no commit.

**Deviations.**

- the dedicated full `nvidia-smi` free/used/utilization mid-run snapshot was not captured on this node: the launcher's mid-run watcher subshell exited on its first iteration because bash resets the special `_` loop variable after the command substitution, so the arithmetic test errored. The watcher loop variable was fixed (ordinary `i`) for the later nodes; this node's smoke was not re-run. The mid-run compute-app census is derived from the 1 s sampler at the median sample carrying the card; mid-run utilization % is unavailable (before/after utilization are recorded).
- **Capture fidelity reconciliation (I1).** The earlier local capture of `RESULT_STATUS.txt` differed from live Ada
  in wording only (local v1 sha256 `7bd2f2ff3cb73478950755b4499da6b8d52235320c52f24f14bb29d14bef981d`; live sha256
  `1752f80ca232129d88940a4060f17bb6e541e036c27d35ec9c528b979d25e8fe`). The capture was **refreshed from live Ada**
  (byte-identical copy, now sha256 `1752f80c…`) and `SHA256SUMS` was regenerated; the superseded local copy is
  preserved as `RESULT_STATUS.local_v1.txt` (still hash-listed). This is a capture-fidelity fix, not a measurement
  difference; the result text states the same mid-snapshot deviation in its own words.
- **Launcher dry-runs (S1, campaign-level).** Two Ada launcher dry-runs for `mlab_cifar10`
  (`dryrun_u2_iso_mlab_cifar10_20261119T033214Z`, `dryrun2_u2_iso_mlab_cifar10_20261119T033708Z`) are preserved in
  the campaign evidence root; the first ran the inner command `taskset -c 0-7 … true -m tests.trackg.port_smoke_gpu …`
  (`true` swallows the smoke arguments) and the second ran a Python/torch-only dry check
  (`/usr/bin/env python -c "import sys, torch; …"` with the same trailing smoke args). Neither executed a U2 run nor
  any GPU work; both correctly went `STOP` on missing `CHECKLIST_E_PASSED` (`dryrun_launcher.log` sha256 `24ebcd6f…`,
  `dryrun2_launcher.log` sha256 `9e4abc5e…`). They are **not smokes and not retries** and do not affect the
  one-smoke claim.

**Scope statements.** One node only (`mlab_imdb`); this result is not evidence, has no noise floor / D21 / D28,
no T1 label, no U3/unisolated claim, and is not pooled with any other node. No other user's GPU
process/card was touched or disturbed; no authors' other experiments were run; no autoresearch (C3-blocked),
HousePrice (STOP) or Breakout (not run) node was executed. One smoke only; no retry.

**Evidence index (this directory).** `SHA256SUMS` (every capture below; regenerated after the record corrections
and verified `shasum -a 256 -c` rc 0).
`logs/run_node.log` (outer log with gate/scope/smoke stdout/CHECKLIST), `smoke_stdout_extract.txt`,
`cgroup_probe.txt`, `time_v.txt`, `invocation_inner.sh`, `gate/`, `gpu/` (qualify/before/mid/after),
`sampler/` (required + timestamped CSV, `sampler_max.json`), `host.txt`, `env.txt`, `env_freeze.txt`,
`data_manifest.txt`, `kit.txt`, `pins.txt`, `disk_before.txt`, `disk_after.txt`, `runs_du.txt`,
`record_hashes.txt`, `summary.json`, `verify_records.json`, `verify_full.json`, `RESULT_STATUS.txt` (live-refreshed)
+ `RESULT_STATUS.local_v1.txt` (superseded local capture), `DONE`, `unit/` (the executed unit bytes),
`static/` (the kit static-test log and README), `scripts/` (the final runner/verifier/sampler-max sources, the two
documented fix patches, and a README), and the nine per-run
`runs/…/{run_record.json,run.log,result_channel.txt}` (plus the smoke work trees). Raw run trees and helper logs
are **preserved unaltered** on Ada under
`/home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlab_imdb_20261119T034107Z/` (live dirs `drwxrwxr-x`, files
`-rw-rw-r--`, hash-matching; not filesystem-read-only) — no deletion.

**Correction note (2026-11-19T04:30Z).** This record was corrected per the accepted MINOR-only conditions of
`docs/r1/reviews/TRACKG_U2_ISO_RESULTS_REVIEW_20261119.md` (node I1–I2 + shared S1–S10), without re-running GPU/U2
and without changing any measured number except where a cited source was wrong. Changes: I1 `RESULT_STATUS.txt`
refreshed from live Ada (now sha256 `1752f80c…`; local v1 `7bd2f2ff…` preserved as `RESULT_STATUS.local_v1.txt`) and
`SHA256SUMS` regenerated; I2 footprint now the post-run `runs_du.txt` 3.8 M / `disk_after.txt` evidence 4.5 M (not
`evidence 60K, runs 4.0K`), and "run root 4.0K" corrected; data-root wording (S7), read-only wording (S8),
`data_link=` print (S9), floor basis/mid-run rule (S5), no-resume (S6), mR6/shas (S3), dry-runs (S1), executed-unit
preservation (S10) added; full kit report/review and R3 shas cited in the header. Full change list and the new
record/SHA256SUMS shas are in `docs/r1/reports/trackg_g0_20261117/U2_ISO_RECORD_CORRECTIONS_20261119.md`.
