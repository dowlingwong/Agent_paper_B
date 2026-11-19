# Track G G.0 U2 isolated-node raw cost — node `mlab_ogbn_arxiv` — RESULT (19 November 2026)

**Status: PASSED — `CHECKLIST_E_PASSED mlab_ogbn_arxiv`; one node only, one smoke, no retry.**
Authority: `R1-TRACKG-G0-GO` (one node per unit, independently reviewed), `R1-HARNESS-ISOLATION`,
`R1-TRACKG-PORT-DECISIONS` (node timeout = 3 × measured B1; a timeout is the proposal's failure, not an
infrastructure retry), port report `docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md` §2/§7, the accepted kit
update `docs/r1/reports/trackg_g0_20261117/TRACKG_ISO_KIT_UPDATE_20261119.md` (sha256
`fe232e2bbf236337e208f11e97c809f8a41d7ef101567eeb0d11153bacb9d026`) with review
`docs/r1/reviews/TRACKG_ISO_KIT_UPDATE_REVIEW_20261119.md` (sha256
`d8c68f9f0463d1aa3e17f82527dfb7ecf7b6070831584cd1024a6d39ed6a21b4`, ACCEPTED), and `R1-TRACKG-LICENCES`. Unit
`docs/r1/proposals/u2_iso_20261119/U2_ISO_MLAB_OGBN_ARXIV_UNIT_20261119.md` (revision 3 **as amended with the R3 pre-execution
conditions mR1/mR7**, mR8b;
current file sha256 `81a3a393731186b89742971a17fe2cb2b4814e543b55892714b867c847ec1bc4`), accepted by review R3
`docs/r1/reviews/TRACKG_U2_ISO_UNITS_REVIEW_R3_20261119.md` (sha256
`99daf16db0b53b807c7796d4d8c8d2812573f2816a42072d7b6dc6f588ca5fb7`; 0 BLOCKING / 0 MAJOR / MINOR,
`ACCEPTED`).
ENGINEERING_ONLY; **not evidence**; no noise floor/D21/D28; no T1 label; no cross-node pooling; no
TASL-7/TASL-2, no HTCondor/deepthought, no other host; no deletion; no commit/push; read-only on Mac records
(only this new result directory is written).

**Kit / environment.**

- Suite **MLAgentBench**, node `mlab_ogbn_arxiv`; kit worktree `/home/dowling/r1_trackg_20261117/harness_iso_mlab`, branch `mac-trackg-iso-mlab-20261117`, **tip `fb6e7d73ddd2d9b962cbb65a85908ce48d25dca9`**; launch
  check `git rev-parse HEAD` = tip and `git status --porcelain --untracked-files=no` empty (only the expected
  untracked runtime `data` symlink(s)) — capture `kit.txt`.
- Python **3.12.16** (`/home/dowling/r1_trackg_20261117/envs/torch312`), torch **2.6.0+cu124 12.4**, CUDA available
  `True 8`; `uv pip freeze` **77 lines**, sha256 **`d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42`** (`env_freeze.txt`,
  `env.txt`).
- Host `ucrtasl`, `Ubuntu 22.04.5 LTS`, kernel `5.15.0-151-generic`, 96 CPUs, driver
  **545.23.08**, boot id `5c90a8fe-5f9b-4914-a2c7-5b864e0a8b8d` (`host.txt`).
- **Data** `AR_TRACKG_DATA_ROOT=/home/dowling/r1_trackg_20261117/data` (outside the repository); node data
  link `nodes/mlab_ogbn_arxiv/data -> /home/dowling/r1_trackg_20261117/data/mlab_ogbn_arxiv` (`kit.txt`
  `?? nodes/mlab_ogbn_arxiv/data`; deployed pin `data: link:` entry); manifest sha256
  **`9131216213b0950e46d0eae81e691503991c0218627fde56ba88e6ac33cd4c6c`** (6 manifest files, 1 setup_only); 21 files / 299350495 bytes on disk,
  286M (node data tree); whole data root 2.9G; manifest and node data tree `dr-xr-xr-x` / `r--r--r--`.
  **Node data dir not writable** (`data_manifest.txt` tests `[ -w "$BASE/data/mlab_ogbn_arxiv" ]`; `data_root_writable=no`)
  and ro-bound in the worker sandbox; the **top-level `data/` root is operator-writable** (`drwxrwxr-x`) — the claim
  that matters is the node data read-only/ro-bind, not the whole root. The `data_link=` line in `data_manifest.txt`
  prints `readlink -f` and re-prints the absolute target, so the in-kit symlink path is implicit (cosmetic; the
  symlink path above is the in-kit one). **No `synthetic` marker** (`data_manifest.txt`). Setup command
  (accepted kit update §5, not re-run; data link and manifest re-verified now): `cd nodes/mlab_ogbn_arxiv &&
  envs/torch312/bin/python prepare_data.py --out $AR_TRACKG_DATA_ROOT/mlab_ogbn_arxiv` (accepted setup log
  `/home/dowling/r1_engineering/iso_kit_update_20261119/data/setup_mlab_ogbn_arxiv.log`, sha256 `e76ecf0bcfec2f86194a815e745cbc4a8cd14951774bf167aaf31a42a9c9d689`).
- **Static tests** (mlab kit; CPU-masked `taskset -c 0-15`, `CUDA_VISIBLE_DEVICES=`, delegated user
  cgroup, interpreter `envs/torch312/bin/python`, `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1
  -p no:cacheprovider`): `python -m pytest tests/trackg -q -p no:cacheprovider -k "not smoke"` →
  **218 passed, 2 failed, 1 skipped, 5 deselected in 44.40 s**, log `static/static_mlab_20261119T033322Z.log` sha256 `c9e8cbd64b9c4b9199c49d91da1ff120c098e7cc4405222e66eabff952eadf77`. The two failures are the
  accepted kit-update §4 documented environment failures (round-2 child-kill test under `/usr/bin/python3`
  3.10; `langchain-openai` missing for the t0 identity test); same counts as the accepted post-update run; no
  test was skipped or weakened.
- **Licence/provenance.** OGB/arXiv: generic research citation/disclosure (`R1-TRACKG-LICENCES`).

**Pins (both, separately; no interchange).**

- **Committed-file `frozen_pin_sha256`** (accepted kit update §3/§10.2 convention; `pins/new_mlab.json` sha256
  `731b713df0126414f537b69adf28acc47969f11162bcb99fe3524699d1d0c866`): **`bd71fdf4c6b3a66715cb602a41a7a1f5bdeeaa6e23439c558a96c2bda061c9d7`** (16 frozen entries; this is the census value).
- **Deployed run-record pin** (every run record's `frozen_pin_sha256`, which also hashes the
  `data: link:<absolute target>` symlink; matches `pins/deployed_mlab.json` sha256 `388c09f5726f6a0e3f88a6eb756490439dda1c988c05c8b5de4464139e24ea49`):
  **`5ff5824ac22783f05f84b84d6d3222e8f1f4ddbc118e6bb1f657041bfb3285ad`**; expected deployed value `5ff5824ac22783f05f84b84d6d3222e8f1f4ddbc118e6bb1f657041bfb3285ad`, constant across all nine records.

**Record identity and preserved bytes (S3/S10).** This result file is
`docs/r1/reports/trackg_g0_20261117/u2_iso_mlab_ogbn_arxiv_20261119T035109Z/U2_ISO_MLAB_OGBN_ARXIV_RESULT_20261119.md`;
its own post-correction sha256 is the `./U2_ISO_MLAB_OGBN_ARXIV_RESULT_20261119.md` entry in this directory's
regenerated `SHA256SUMS` (the `SHA256SUMS` sha256 is recorded in `U2_ISO_RECORD_CORRECTIONS_20261119.md`). Node spec:
raw `configs/trackg/nodes/mlab_ogbn_arxiv.yaml` sha256 `97feff8a52ff0a083239766a2a15eb2ffcdcbe5b8d3fb8450b47b1a8a2c19be3`,
canonical `node_spec_sha256` (kit loader: `sha256(json.dumps(payload, sort_keys=True, separators=(",",":"),
ensure_ascii=False, default=str))`) `e952df6a2f3f9abfdca944805e57a86604770d289101135fe45763b510752c0c` (= every run
record's value; recomputed with the kit's own loader — this spec's `description` is the only one with a non-ASCII
character, so `ensure_ascii=False` matters). Representative-edit manifest sha256
`b2cf5ae6f51fde68acae32e9324306e0b76fb965831cd1cd8037f64dceddfe1a`; representative edits E1/E2/E3/E4 diff sha256
`77c4dbb3…`, `c8d2b67f…`, `ffa1b54a…`, `ed265c61…` (full values in `kit.txt`). Executed unit bytes are preserved at
`unit/U2_ISO_MLAB_OGBN_ARXIV_UNIT_20261119.md` (sha256
`81a3a393731186b89742971a17fe2cb2b4814e543b55892714b867c847ec1bc4`, = the recorded executed unit). Preserved
runner/helper bytes (this directory's `scripts/`): **launch-time/final** `run_node.sh` sha256
`13a45d7baf7dacac6da2ef1455e86fc794c25fd90f5a835511b50aafccc99444` (patch3 was applied at 19:50Z, before this
node's 19:51Z launch, so these are the launch-time bytes), `_patch2_verifier_s002_fix.py`
`681d9f8a2d25eef0d2c1947e7bace55b1ade5c0fe9f6cbf64ae458b4b97b5353`, `_patch3_mid_watcher_fix.py`
`ce2ff3b0ecdb61cdbbad615bef47abd6a34473bb42bc45358eefe00cbb18fc39`, `compute_sampler_max.py`
`7d9f472ec1e24ba879f2edd0fa259612f0c00133abf90309587a43ced312dbed`, `verify_u2_records.py`
`7f40ed1789fb77c29a14022db9908a46c3ca47563cd0ca6030df7aff21dd8418`. Every executed record has
`process.returncode: 0`, `process.killed_with: null` (normal exit), `process.timed_out: false`,
`leftover_processes_killed: false`; the smoke log carries one JSON record line per run (verifier `--smoke-log` check
in `verify_full.json`).

**Paper A gate (captured immediately before launch; three-check).**

- Gate JSON `/home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlab_ogbn_arxiv_20261119T035109Z/gate/gate_20261119T035109Z.json` sha256 **`1d9e8062493d020a5cedbee15513248fb1db4e2844755fdd6f51b174b7a6fef7`** (UTC `2026-11-19T03:51:13Z`; gate script rc 0; config
  `/home/dowling/r1_trackg_20261117/Agent_paper_B_main_16185b0b/r1/scripts/configs/paper_a_status_ada.json`).
- **Three-check PASS**: `verdict: clear_finished`, `paper_a_live_waiting_for_card: false`, `paper_a_processes: []`,
  `unidentified_apps: 0`.
- Newest v4 `live_*` directory == configured run dir (`newest_live_equals_configured=yes`); self-excluded
  `pgrep` for `port_smoke_gpu` empty; `pgrep agent-checkpoint-intervention` empty (`gate/gate_check.txt`).

**GPU gate / co-tenancy (idle card only).**

- Selected **UUID `GPU-3b36edea-1a09-a37e-aa42-8277c7319e77`**: 48427 MiB free, **0 % utilization, no other user's compute app**
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
  `5c09721b2383abf2b33346a48f0721debb5c71ab0f096fbe6f16129e829ac1a0`, 484 app rows) plus a concurrent timestamped
  companion used only to group rows into per-sample sums (`sampler/sampler_timestamped.csv` sha256
  `b5a5b75a3dc70613fd267f0d8bd7d6f6eafe0415a27d72f0eb732faece838a73`); 63.4 s sampled,
  36 samples carried the used card, 8 distinct worker pids
  (all this smoke).
- **Peak reported as a whole-smoke upper bound = 4544 MiB** (max single-row
  `used_memory` 4544 MiB = max per-sample sum 4544 MiB on the
  used card; CSV header not counted). **Label: whole-smoke upper bound over the used GPU, including any
  co-tenant by construction; NOT a per-run peak and NOT attributed to the baseline process tree.** The card
  returned to idle after the smoke (`gpu/gpu_after.txt`).
- Mid-run census (`gpu/gpu_mid.txt`):
  ```
  # gpu mid (used=763 MiB) 2026-11-19T03:51:18Z
index, uuid, memory.total [MiB], memory.used [MiB], memory.free [MiB], utilization.gpu [%]
0, GPU-9be33fd1-8eeb-497d-772a-87362d6720be, 49140 MiB, 12717 MiB, 35715 MiB, 48 %
1, GPU-aa340032-6f94-9783-8f3d-50a15da47a6f, 49140 MiB, 5 MiB, 48427 MiB, 0 %
2, GPU-f439cca8-bd1d-d5c6-d15e-bbfbc02c8154, 49140 MiB, 5 MiB, 48427 MiB, 0 %
3, GPU-5d61f1bc-1a65-f322-6feb-3aeaf6051f94, 49140 MiB, 29376 MiB, 19057 MiB, 0 %
4, GPU-379470db-a02e-893a-57a0-71b119173890, 49140 MiB, 15189 MiB, 33243 MiB, 97 %
5, GPU-5357dc5f-5d1d-af80-a3f4-3eb5aeb38f0d, 49140 MiB, 12344 MiB, 36089 MiB, 50 %
6, GPU-3b36edea-1a09-a37e-aa42-8277c7319e77, 49140 MiB, 763 MiB, 47669 MiB, 6 %
7, GPU-3719bd35-06de-4674-7c7a-e56136fed589, 49140 MiB, 5 MiB, 48427 MiB, 0 %
# compute apps
gpu_uuid, pid, used_gpu_memory [MiB]
  ```

**Run (unit command shape, exactly one smoke).**

- Inside `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c '…'`
  (logged unit line in `logs/run_node.log`): `cd harness_iso_mlab`, `CG=$(cut -d: -f3 /proc/self/cgroup)`,
  `AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG`, `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1`,
  `PATH=…/envs/torch312/bin:$PATH`, `VIRTUAL_ENV=…/envs/torch312`, `CUDA_VISIBLE_DEVICES=""`,
  `AR_TRACKG_DATA_ROOT=…/data`, `taskset -c 0-7 python -m tests.trackg.port_smoke_gpu --node mlab_ogbn_arxiv
  --gpu-uuid GPU-3b36edea-1a09-a37e-aa42-8277c7319e77 --cpus 0-7 --memory-limit "external: systemd-run --user --scope -p MemoryMax=8G
  -p MemorySwapMax=0 (enforced cgroup)" --runs-root <outside repo>/runs --provisional-timeout 1800`
  (one-line `--memory-limit`; resolved invocation `invocation_inner.sh` sha256 `6142ad4690bb51ca36f5d079c64a3c386347cf935d6dd3ba76265d123fa00878`).
- **Cgroup enforcement probe (read from inside the scope)**: `scope_cgroup=/sys/fs/cgroup/user.slice/user-1030.slice/user@1030.service/app.slice/run-rc4b68d2b57e34b30b6beeffa132feae8.scope`,
  **`memory.max=8589934592`**, **`memory.swap.max=0`** (expected 8,589,934,592 and 0; a different value
  was a STOP), `which python` after PATH/VIRTUAL_ENV → `/home/dowling/r1_trackg_20261117/envs/torch312/bin/python`, Python 3.12.16 (`cgroup_probe.txt`).
- **rc 0; `CHECKLIST_E_PASSED mlab_ogbn_arxiv`; `SMOKE_EXIT=0`; `systemd_run_rc=0`** (smoke stdout
  `smoke_stdout_extract.txt` sha256 `908cc79a0070936330b38aebb345762c327e189008435af545c2ee68070e2945`; log `logs/run_node.log` sha256 `f6b3d204f5d6f07361fd6a9fcaf80d4b46fc187aa788b2f34bc419749bbf803e`).
- **`time -v` for the whole smoke (aggregate, not a per-run peak)**: user **56.76 s**, system **11.86 s**,
  wall **1:03.92**, max RSS **1,256,776 kB** (`time_v.txt`).
- Timeout: provisional 1800 s; **node timeout = 3 × measured B1 = 16.953 s**; no 1800 s timeout and no OOM
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
| `s000_baseline` | baseline | true | **0.275982** | 5.651 s | 0.238442 |
| `s001` | frozen-diff refused (`scope_violation`) | **false** | — (null) | — | — |
| `s002` | broken diff `divergent/non_finite_loss` | true | — (divergent) | 5.944 s | 0.0 |
| `s003` | first declared edit (kept) | true | 0.419477 | 5.662 s | 0.396375 |
| `E1` | declared edit | true | 0.419477 | 5.733 s | 0.396375 |
| `E2` | declared edit | true | 0.527769 | 5.713 s | 0.505463 |
| `E3` | declared edit | true | 0.076278 | 6.303 s | 0.058618 |
| `E4` | declared edit | true | 0.698849 | 21.8 s | 0.691233 |
| `B2` | repeat baseline | true | **0.275982** | 5.665 s | 0.238442 |

- 9 `run_record.json`, **8 executed + the refused frozen diff (`s001` `executed:false`)**; `B2` repeats B1
  (value 0.275982 vs 0.275982; sealed 0.238442 vs 0.238442). Baseline record
  `runs/…/s000_baseline/run_record.json` sha256 **`41c542d0a7498ef998d7c38c5c60a170f90d9f77dee56a6396259db35dea30e8`** (run.log sha256 `47f0eb8e6010b71c07a78973bdd8fc9544964ee0f82948d40df13b536d5f1af7`, result-channel
  sha256 `679cb595d08176e346e7f77903e2fe94826c43d20ea95ca17fdc2f05d7a482c5`); every per-run record/log/result-channel hash is in `record_hashes.txt`.
- Pre-run reference only (accepted kit update engineering smoke): `5.702 s / val 0.275982`; this unit recorded its own
  B1/B2 above.
- **Derived-timeout disclosure (O2).** One executed representative edit, **`E4`** (GraphSAGE full-graph edit; table
  row above), took **`elapsed_seconds_info_only = 21.8 s`**, which is **above the derived node timeout 16.953 s**
  (= 3 × B1 5.651 s). This is **not** a timeout in the measuring smoke: the smoke ran under the **provisional
  1800 s** (`limits.provisional_timeout_seconds: 1800.0`; `process.timed_out: false`), and 3×B1 is the derived
  value for later units/label runs, not a mid-smoke kill. For the census/funnel: under a future label run that edit
  would be classified as a **timeout / failed proposal** (per `R1-TRACKG-PORT-DECISIONS` (4)). Non-material to the
  raw-cost measurement, but disclosed so the census reader sees it.

**Isolation record gate (every executed record).**

- Every executed record: `isolation.effective: true`, `isolation.waivers {}`, `isolation.exceptions []`,
  `log_intact: true`, result channel present (`result_channel_overflow: false`, `result_channel_sha256`
  recorded), cgroup kill `method: cgroup.kill` with `empty_after: true` and `removed: true`,
  `determinism.not_forced == ["dataloader_workers"]`, `limits.external_limit` exactly the one-line unit
  string, `gpu_uuids == ["GPU-3b36edea-1a09-a37e-aa42-8277c7319e77"]`, `cpu_list [0..7]`, `memory_method: external`,
  provisional timeout 1800 s, timeout factor 3.0. `s001` is `executed:false`, `outcome:null`,
  `scope_violation`, no isolation fields (by design; not a failure).
- Verifiers: `scripts/verify_u2_records.py` **rc 0, `ok: True`, 9 records /
  8 executed / refused_s001 True** (`verify_full.json`,
  `verify_full.summary.txt`); accepted kit helper `verify_records.py` **rc 0, issues []**
  (`verify_records.json`); `collect_smoke_summary.py` **rc 0, gate_ok True, issues
  []** (`summary.json`). Final run-node status: **PASS**
  (`RESULT_STATUS.txt`); `DONE`: DONE_PASS 2026-11-19T03:52:19Z.

**Disk / footprint.**

- `df -B1 /` (`/dev/md0p3`, mounted `/`) before: **74,610,388,992 B (69.5 GiB) available**; after: 74,605,633,536 B
  (69.5 GiB) — above the 50 GiB STOP floor both before and after. **Post-run footprint:** this node's evidence
  **4.0 M**, runs **3.8 M**, node data 286M, whole data root 2.9G (`disk_after.txt`, `runs_du.txt`). The values
  `evidence 60K, runs 4.0K` in `disk_before.txt` are the **pre-run** sizes and are not the footprint (O1); nothing
  deleted, no push, no commit.

**Deviations.**

- none in the smoke, the record gate or any required capture: no card switch, no co-tenant, no timeout/OOM, no waiver,
  no synthetic marker, no retry.
- **Derived-timeout disclosure (O2):** `E4` measured 21.8 s > derived node timeout 16.953 s while the measuring smoke
  was governed by the provisional 1800 s — disclosed above (non-material; would be a timeout/proposal failure under a
  future label run).
- **Launcher dry-runs (S1, campaign-level).** Two Ada launcher dry-runs for `mlab_cifar10`
  (`dryrun_u2_iso_mlab_cifar10_20261119T033214Z`, `dryrun2_u2_iso_mlab_cifar10_20261119T033708Z`) are preserved in
  the campaign evidence root; the first ran `taskset -c 0-7 … true -m tests.trackg.port_smoke_gpu …` (`true`
  swallows the smoke arguments) and the second a Python/torch-only dry check, each with the same trailing smoke args.
  Neither executed a U2 run nor any GPU work; both correctly went `STOP` on missing `CHECKLIST_E_PASSED`. They are
  **not smokes and not retries**.

**Scope statements.** One node only (`mlab_ogbn_arxiv`); this result is not evidence, has no noise floor / D21 / D28,
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
`/home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlab_ogbn_arxiv_20261119T035109Z/` (live dirs `drwxrwxr-x`,
files `-rw-rw-r--`, hash-matching; not filesystem-read-only) — no deletion.

**Correction note (2026-11-19T04:30Z).** This record was corrected per the accepted MINOR-only conditions of
`docs/r1/reviews/TRACKG_U2_ISO_RESULTS_REVIEW_20261119.md` (node O1–O2 + shared S1–S10), without re-running GPU/U2
and without changing any measured number except where a cited source was wrong. Changes: O1 footprint now the
post-run `runs_du.txt` 3.8 M / `disk_after.txt` evidence 4.0 M (not `evidence 60K, runs 4.0K`), and "run root 4.0K"
corrected; O2 added the `E4` 21.8 s > derived node timeout 16.953 s disclosure (provisional 1800 s governed the
measuring smoke); data-root wording (S7), read-only wording (S8), `data_link=` print (S9), floor basis/mid-run rule
(S5), no-resume (S6), mR6/shas (S3), dry-runs (S1), executed-unit preservation (S10) added; full kit report/review
and R3 shas cited in the header. Full change list and the new record/SHA256SUMS shas are in
`docs/r1/reports/trackg_g0_20261117/U2_ISO_RECORD_CORRECTIONS_20261119.md`.
