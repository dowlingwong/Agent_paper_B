# Track G G.0 U2 isolated-node raw cost — node `mlab_cifar10` — RESULT (19 November 2026)

**Status: PASSED — `CHECKLIST_E_PASSED mlab_cifar10`; one node only, one smoke, no retry.**
Authority: `R1-TRACKG-G0-GO` (one node per unit, independently reviewed), `R1-HARNESS-ISOLATION`,
`R1-TRACKG-PORT-DECISIONS` (node timeout = 3 × measured B1; a timeout is the proposal's failure, not an
infrastructure retry), port report `docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md` §2/§7, the accepted kit
update `docs/r1/reports/trackg_g0_20261117/TRACKG_ISO_KIT_UPDATE_20261119.md` (sha256
`fe232e2bbf236337e208f11e97c809f8a41d7ef101567eeb0d11153bacb9d026`) with review
`docs/r1/reviews/TRACKG_ISO_KIT_UPDATE_REVIEW_20261119.md` (sha256
`d8c68f9f0463d1aa3e17f82527dfb7ecf7b6070831584cd1024a6d39ed6a21b4`, ACCEPTED). Unit
`docs/r1/proposals/u2_iso_20261119/U2_ISO_MLAB_CIFAR10_UNIT_20261119.md` (revision 3 **as amended with the R3
pre-execution conditions mR1/mR7**; current file sha256
`7278932f1b8898a7690eb935e0dd46172445ddb4c3e41823d725c0b65ca57684`), accepted by review R3
`docs/r1/reviews/TRACKG_U2_ISO_UNITS_REVIEW_R3_20261119.md` (sha256
`99daf16db0b53b807c7796d4d8c8d2812573f2816a42072d7b6dc6f588ca5fb7`; 0 BLOCKING / 0 MAJOR / 10 MINOR,
`ACCEPTED`).
ENGINEERING_ONLY; **not evidence**; no noise floor/D21/D28; no T1 label; no cross-node pooling; no
TASL-7/TASL-2, no HTCondor/deepthought, no other host; no deletion; no commit/push; read-only on Mac records
(only this new result directory is written).

**Kit / environment.**

- Kit worktree `/home/dowling/r1_trackg_20261117/harness_iso_mlab`, branch `mac-trackg-iso-mlab-20261117`,
  **tip `fb6e7d73ddd2d9b962cbb65a85908ce48d25dca9`**; launch check `git rev-parse HEAD` = tip and
  `git status --porcelain --untracked-files=no` empty (only the three expected untracked runtime `data`
  symlinks) — capture `kit.txt`, `logs/run_node.log`.
- Python **3.12.16** (`/home/dowling/r1_trackg_20261117/envs/torch312`), torch **2.6.0+cu124** (CUDA 12.4),
  `torch.cuda.is_available() == True`, 8 devices; `uv pip freeze` **77 lines**, sha256
  **`d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42`** (`env_freeze.txt`, `env.txt`).
- Host Ada `ucrtasl`, Ubuntu 22.04.5, kernel `5.15.0-151-generic`, 96 CPUs, 503 GiB RAM, driver **545.23.08**
  (NVRM 545.23.08), boot id `5c90a8fe-5f9b-4914-a2c7-5b864e0a8b8d` (`host.txt`).
- **Data** `AR_TRACKG_DATA_ROOT=/home/dowling/r1_trackg_20261117/data` (outside the repository); in-kit link
  `nodes/mlab_cifar10/data -> /home/dowling/r1_trackg_20261117/data/mlab_cifar10` (`kit.txt` `?? nodes/mlab_cifar10/data`;
  deployed pin `data: link:` entry); manifest sha256
  **`43fdf860d14167926815428e09cb507f491cc7504fec8fd228bc2d8974f408a3`** (4 manifest files + 1 `setup_only`
  entry; 14 files / 541,513,760 bytes / 517 M on disk); manifest and node data tree `dr-xr-xr-x` / `r--r--r--`.
  **Node data dir not writable** (`data_manifest.txt` tests `[ -w "$BASE/data/mlab_cifar10" ]`; `data_root_writable=no`)
  and ro-bound in the worker sandbox; the **top-level `data/` root is operator-writable** (`drwxrwxr-x`) — the claim
  that matters is the node data read-only/ro-bind, not the whole root. The `data_link=` line in `data_manifest.txt`
  prints `readlink -f` and re-prints the absolute target, so the in-kit symlink path is implicit (cosmetic; the
  symlink path above is the in-kit one). **No `synthetic` marker** (`data_manifest.txt`). Setup command (accepted
  kit update §5, not re-run; data link and manifest re-verified now): `cd nodes/mlab_cifar10 &&
  envs/torch312/bin/python prepare_data.py --out $AR_TRACKG_DATA_ROOT/mlab_cifar10` (accepted setup log
  `/home/dowling/r1_engineering/iso_kit_update_20261119/data/setup_mlab_cifar10.log` sha256
  **`6747f821af7e6b89db3667a2fbd9115b3031b9a6f5446c4d072806fa01c1eb95`**, live).
- **Licence/provenance.** MLAgentBench tasks are used as task assets; CIFAR-10 generic research citation/disclosure
  per `R1-TRACKG-LICENCES` (the same licence line the other four node results carry).
- **Static tests** (CPU-masked `taskset -c 0-15`, `CUDA_VISIBLE_DEVICES=`, delegated scope, interpreter
  `envs/torch312/bin/python`, `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`):
  `python -m pytest tests/trackg -q -p no:cacheprovider -k "not smoke"` → **218 passed, 2 failed, 1 skipped,
  5 deselected in 44.40 s** (log `static/static_mlab_20261119T033322Z.log` in the Ada evidence root). The two
  failures are the accepted kit update §4 documented environment failures (round-2 child-kill test under
  `/usr/bin/python3` 3.10; `langchain-openai` missing for the t0 identity test) — same counts as the accepted
  post-update run; no test was skipped or weakened.

**Pins (both, separately; no interchange).**

- **Committed-file `frozen_pin_sha256`** (kit update §3/§10.2 convention, `pins/new_mlab.json` sha256
  `731b713df0126414f537b69adf28acc47969f11162bcb99fe3524699d1d0c866`):
  **`1f047ad7cc8cb9e7520a9362c578dcfa516cd4e59301c7ff12d915690ca494c2`** (16 frozen entries; this is the census
  value).
- **Deployed run-record pin** (every run record's `frozen_pin_sha256`, includes the `data: link:<absolute
  target>` symlink; matches `pins/deployed_mlab.json` sha256
  `388c09f5726f6a0e3f88a6eb756490439dda1c988c05c8b5de4464139e24ea49`):
  **`a459b3d823075953d05422594cc97fa743723f22e79e1f8368480007dd041388`** (17 entries, constant across all nine
  records).

**Record identity and preserved bytes (S3/S10).** This result file is
`docs/r1/reports/trackg_g0_20261117/u2_iso_mlab_cifar10_20261119T033747Z/U2_ISO_MLAB_CIFAR10_RESULT_20261119.md`;
its own post-correction sha256 is the `./U2_ISO_MLAB_CIFAR10_RESULT_20261119.md` entry in this directory's
regenerated `SHA256SUMS` (the `SHA256SUMS` sha256 is recorded in `U2_ISO_RECORD_CORRECTIONS_20261119.md`). Node spec:
raw `configs/trackg/nodes/mlab_cifar10.yaml` sha256 `0f9d5d2173b76fb0387456f22548f1c7c8909a6bedffbda460c611c987ff73a5`,
canonical `node_spec_sha256` (kit loader: `sha256(json.dumps(payload, sort_keys=True, separators=(",",":"),
ensure_ascii=False, default=str))`) `90c8364f3c35b276ad97c73ea66b9e31d9f8e128aa9be7db5a013b5eb7b4093f` (= every run
record's value). Representative-edit manifest sha256 `bef79111cf21be264713e04eab2ac13e0f926bb4a6457b93ff32bf540e56b44d`;
representative edits E1/E2/E3/E4 diff sha256 `345f0bcd…`, `39fd85d0…`, `4d25e599…`, `261b474a…` (full values in
`kit.txt`). Executed unit bytes are preserved at `unit/U2_ISO_MLAB_CIFAR10_UNIT_20261119.md`
(sha256 `7278932f1b8898a7690eb935e0dd46172445ddb4c3e41823d725c0b65ca57684`, = the recorded executed unit). Preserved
runner/helper bytes (this directory's `scripts/`): final `run_node.sh` sha256
`13a45d7baf7dacac6da2ef1455e86fc794c25fd90f5a835511b50aafccc99444`, `_patch2_verifier_s002_fix.py`
`681d9f8a2d25eef0d2c1947e7bace55b1ade5c0fe9f6cbf64ae458b4b97b5353`, `_patch3_mid_watcher_fix.py`
`ce2ff3b0ecdb61cdbbad615bef47abd6a34473bb42bc45358eefe00cbb18fc39`, `compute_sampler_max.py`
`7d9f472ec1e24ba879f2edd0fa259612f0c00133abf90309587a43ced312dbed`, `verify_u2_records.py`
`7f40ed1789fb77c29a14022db9908a46c3ca47563cd0ca6030df7aff21dd8418`. Every executed record has
`process.returncode: 0`, `process.killed_with: null` (normal exit), `process.timed_out: false`,
`leftover_processes_killed: false`; the smoke log carries one JSON record line per run (verifier `--smoke-log` check
in `verify_full.json`). *Residual (S10):* this node's exact launch-time runner bytes (pre-patch2/pre-patch3) were not
preserved as a file; the two patches are exact preserved string replacements, so the derivation is reproducible but
is recorded as a residual, not as a preserved snapshot.

**Paper A gate (captured immediately before launch; three-check).**

- Gate JSON `gate/gate_20261119T033747Z.json` sha256
  **`f30799b1332738c17354a8248c36de2dc2a6c86c504980904d5b1c1045f94ef5`**; the gate JSON's own `utc` is
  **`2026-11-19T03:37:51Z`** and `gate/gate_check.txt` was captured at `03:37:51Z` (the `03:37:47Z` in the file/
  evidence-dir name is the runner/evidence-dir start timestamp from `launch_mlab_cifar10.log`, not the gate time);
  gate script rc 0; config
  `/home/dowling/r1_trackg_20261117/Agent_paper_B_main_16185b0b/r1/scripts/configs/paper_a_status_ada.json`.
- **Three-check PASS**: `verdict: clear_finished`, `paper_a_live_waiting_for_card: false`,
  `paper_a_processes: []`, `unidentified_apps: 0`.
- Newest v4 `live_*` directory == configured run dir
  (`/home/dowling/agent-checkpoint-intervention/results/paper_a/replay_panel_v4/live_20261018T234416Z`);
  self-excluded `pgrep` for `port_smoke_gpu` empty; `pgrep agent-checkpoint-intervention` empty
  (`gate/gate_check.txt`).

**GPU gate / co-tenancy (idle card only).**

- Selected **card 1, UUID `GPU-aa340032-6f94-9783-8f3d-50a15da47a6f`**: 48,427 MiB free of 49,140 MiB,
  **0 % utilization, no other user's compute app** immediately before launch (`gpu/gpu_qualify.txt`,
  `gpu/gpu_before.txt`); floor = ≥ 8,192 MiB free (chosen card ≈ 48.4 GiB free).
- **Floor basis / co-tenancy rule (S5).** The 8 GiB requirement is a conservative floor: the accepted kit update
  measured a **~2.85 GB (2,853 MiB)** per-run torch GPU peak under the 8 GiB cap (§6), and the prior accepted run-1
  floor was **24 GiB** (`TRACKG_U2_RAWCOST_REVIEW_R2_20261117.md`); the chosen card had ≈ 48.4 GiB free. Mid-run
  contamination rule: a free-VRAM drop below the baseline peak + 2 GiB, or a new co-tenant on the used card, is a
  STOP/recorded; **no card switch from the launch card** occurred (the selected UUID is the only card in
  `gpu_qualify/before/mid/after` and in every run record).
- Whole-smoke sampler: exact command
  `nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv -l 1` (interval **1 s**), started
  before the `systemd-run` scope and stopped after it; output `sampler/sampler_required.csv` (sha256
  `a74b13a38f22cce71dcceaf01289cb542f46cf0a095cc163a6dd4e7f97660234`, 780 app rows) plus a concurrent
  timestamped companion used only to group rows into per-sample sums
  (`sampler/sampler_timestamped.csv` sha256 `fbc11d5ff855db63b9866c871f1e9c007cfbeca5d25538282cf1c8ee280fad25`);
  100.7 s sampled, 73 samples carried the used card, 8 distinct worker pids (all this smoke's own runs).
- **Peak reported as a whole-smoke upper bound = 836 MiB** (max single-row `used_memory` 836 MiB = max
  per-sample sum 836 MiB on the used card; CSV header not counted). **Label: whole-smoke upper bound over the
  used GPU, including any co-tenant by construction; NOT a per-run peak and NOT attributed to the baseline
  process tree.** No other user's app ever appeared on the card; the card returned to 5 MiB / 0 % after
  (`gpu/gpu_after.txt`, `sampler/sampler_max.json`).
- **Deviation (capture completeness, not measurement):** the dedicated full `nvidia-smi` free/used/utilization
  mid-run snapshot was not captured on this node. Two launcher bugs in the mid-run watcher: (a) the subshell
  exited on its first iteration because bash resets the special `_` loop variable after the command
  substitution, so the arithmetic test errored; (b) even with a working loop the threshold (1,000 MiB) was above
  this node's measured 836 MiB maximum. The mid-run compute-app census is therefore derived from the 1 s sampler
  at the median sample carrying the card: pid 3805498, 834 MiB, ≈839 MiB card used / ≈48,301 MiB free; mid-run
  utilization % unavailable (`gpu/gpu_mid.txt`, labelled). Before/after full snapshots are captured. The watcher
  was fixed (ordinary loop variable, > 100 MiB trigger plus a 60 s fallback) for the remaining nodes; this
  node's smoke was **not** re-run.

**Run (unit command shape, exactly one smoke).**

- Inside `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c '…'`
  (logged unit `run-r5cd39bf10ace44cd8950d39b9809554a.scope`): `cd harness_iso_mlab`, `CG=$(cut -d: -f3
  /proc/self/cgroup)`, `AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG`, `PYTHONPATH=src
  PYTHONDONTWRITEBYTECODE=1`, `PATH=…/envs/torch312/bin:$PATH`, `VIRTUAL_ENV=…/envs/torch312`,
  `CUDA_VISIBLE_DEVICES=""`, `AR_TRACKG_DATA_ROOT=…/data`, `taskset -c 0-7 python -m
  tests.trackg.port_smoke_gpu --node mlab_cifar10 --gpu-uuid GPU-aa340032-… --cpus 0-7 --memory-limit
  "external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 (enforced cgroup)" --runs-root
  <outside repo>/runs --provisional-timeout 1800` (one-line `--memory-limit`; resolved invocation with the
  actual values: `invocation_inner.sh` sha256
  `910d276c95b6d32d26b66accd9fe4a892ed5efd39afe16893ec24a4a332ea5bc`).
- **Cgroup enforcement probe (read from inside the scope)**: `scope_cgroup=/sys/fs/cgroup/user.slice/
  user-1030.slice/user@1030.service/app.slice/run-r5cd39bf10ace44cd8950d39b9809554a.scope`,
  **`memory.max=8589934592`**, **`memory.swap.max=0`** (both equal the expected 8 GiB / 0; wrong value would
  have been a STOP), `which python` after PATH/VIRTUAL_ENV → `…/envs/torch312/bin/python` (before PATH: empty),
  Python 3.12.16 (`cgroup_probe.txt`).
- **rc 0; `CHECKLIST_E_PASSED mlab_cifar10`; `SMOKE_EXIT=0`; `systemd_run_rc=0`** (smoke stdout
  `smoke_stdout_extract.txt`, log `logs/run_node.log`, sha256
  `f92bcd4f86b394fb141b5017e739bbad048563f4fb5344d669c2d2fb626c5f2c`; smoke stdout extract sha256
  `351e10417bc4b22c8c35bca0d2254db54fffa39451b7289d87ea19f9daa61585`).
- **`time -v` for the whole smoke (aggregate, not a per-run peak)**: user **94.21 s**, system **13.77 s**,
  wall **1:41.53**, max RSS **1,402,612 kB** (`time_v.txt`).
- Timeout: provisional 1800 s; **node timeout = 3 × measured B1 = 36.891 s**; no timeout and no OOM
  occurred; no timeout/OOM retry. **No resume (R3 mR10):** an interrupted unit re-runs wholly from a new
  `<runs-root>`; no resume occurred here.
- `--runs-root` outside the repository: `/home/dowling/r1_engineering/u2_iso_20261119/
  u2_iso_mlab_cifar10_20261119T033747Z/runs`; run root 3.8 M.

**Result — B1/B2 and every edit outcome** (`outcome.value` is the node's validation metric as the kit reports
it — here `metric_name: val_accuracy`, `selection_split: validation`, `AR_METRIC val_accuracy=…`; these torch nodes
have no `val_bpb`; the sealed test metric is `AR_TEST test_accuracy=…` → `sealed.test_accuracy`, kept separate and
named `val_accuracy` in the census row for `outcome.value`).

| run | kind | executed | `outcome.value` | `elapsed_seconds_info_only` | `sealed.test_accuracy` |
|---|---|---|---|---|---|
| `s000_baseline` **B1** | baseline | true | **0.5152** | **12.297 s** | 0.5015 |
| `s001` | frozen-diff refused (`scope_violation`) | **false** | — (null) | — | — |
| `s002` | broken diff `divergent/non_finite_loss` | true | — (null) | 12.586 s | 0.0 |
| `s003` | first declared edit (kept) | true | 0.5834 | 12.633 s | 0.5835 |
| `E1` | declared edit | true | 0.5834 | 12.287 s | 0.5835 |
| `E2` | declared edit | true | 0.6002 | 13.347 s | 0.5952 |
| `E3` | declared edit | true | 0.5580 | 12.989 s | 0.5595 |
| `E4` | declared edit | true | 0.1022 | 12.180 s | 0.1000 |
| `B2` | repeat baseline | true | **0.5152** | **11.846 s** | 0.5015 |

- 9 `run_record.json`, **8 executed + the refused frozen diff (`s001` `executed:false`)**; `B2` reproduces
  `B1`'s metric exactly (0.5152 / 0.5015). Baseline record
  `runs/runs_smoke/s000_baseline/run_record.json` sha256
  **`c4d532a781121fe1452a2030470ed597b83628a1a4bbadf47b66aebbeb485e27`** (run.log sha256
  `77f18a64…`, result_channel sha256 `ebb17269…`); all per-run record/log/result-channel hashes:
  `record_hashes.txt`.

**Isolation record gate (every executed record).**

- Every executed record: `isolation.effective: true`, `isolation.waivers {}`, `isolation.exceptions []`,
  `log_intact: true`, result channel present (`result_channel_overflow: false`, `result_channel_sha256`
  recorded), cgroup kill `method: cgroup.kill` with `empty_after: true` and `removed: true`,
  `determinism.not_forced == ["dataloader_workers"]`, `limits.external_limit` exactly the one-line unit string,
  `gpu_uuids == [GPU-aa340032-…]`, `cpu_list [0..7]`, `memory_method: external`, provisional timeout 1800 s,
  timeout factor 3.0. `s001` is `executed:false`, `outcome:null`, `scope_violation`, no isolation fields (by
  design; not a failure).
- Verifiers: `scripts/verify_u2_records.py` (fixed verifier) **rc 0, `ok: true`, 9 records / 8 executed /
  refused_s001 true** (`verify_full.json`, `verify_full.summary.txt`); accepted kit helper
  `verify_records.py` **rc 0, issues []** (`verify_records.json`); `collect_smoke_summary.py` **rc 0,
  gate_ok true, issues []** (`summary.json`).
- **Deviation (verifier bug, not a smoke failure):** the first verifier run false-negatived `s002` by applying
  the generic "outcome ok" check to the deliberately divergent broken diff. The smoke itself passed; the
  verifier was fixed and re-run **on the same records** (no smoke re-run). Original outputs preserved as
  `verify_full.v1_verifier_bug.json` / `verify_full.summary.v1_verifier_bug.txt`; correction recorded in
  `RESULT_STATUS.txt` and `DONE`. Final status: **PASS** (`status_corrected=PASS`).
- **Status reconciliation (C5).** The machine `RESULT_STATUS.txt` still begins with the historical
  `STOP`/`status=STOP` lines from the v1 verifier false-negative and then appends `status_corrected=PASS` and
  `verify_full_rc_corrected=0`; `DONE` carries `DONE_STOP 2026-11-19T03:39:34Z` followed by
  `DONE_PASS_CORRECTED 2026-11-19T03:40:50Z`. This is history, not a smoke failure: the corrected verifier is rc 0
  on the same records and no smoke was re-run. On the record level the final status is **PASS**
  (`status_corrected=PASS`); the capture is left byte-faithful to live Ada (no Ada write was permitted), so the
  STOP-first machine line is preserved as history and disclosed here and in the correction note.
- **Launcher dry-runs (S1, campaign-level).** Two Ada launcher dry-runs for this node
  (`dryrun_u2_iso_mlab_cifar10_20261119T033214Z`, `dryrun2_u2_iso_mlab_cifar10_20261119T033708Z`) are preserved in
  the campaign evidence root; the first ran the inner command `taskset -c 0-7 … true -m tests.trackg.port_smoke_gpu …`
  (`true` swallows the smoke arguments) and the second ran a Python/torch-only dry check
  (`/usr/bin/env python -c "import sys, torch; …"` with the same trailing smoke args). Neither executed a U2 run nor
  any GPU work; both correctly went `STOP` on missing `CHECKLIST_E_PASSED` (`status=STOP`, `DONE_STOP`;
  `dryrun_launcher.log` sha256 `24ebcd6f…`, `dryrun2_launcher.log` sha256 `9e4abc5e…`). They are **not smokes and
  not retries** and are not counted in the one-smoke claim.

**Disk / footprint.**

- `df -B1 / /home /tmp` (all on `/dev/md0p3`, mounted `/`) before: **74,632,835,072 B available (69.5 GiB)**;
  after: **74,630,283,264 B** (69.5 GiB) — above the 50 GiB STOP floor both before and after. These are the
  `disk_before.txt`/`disk_after.txt` `df` values; the earlier `disk_avail_before/after_bytes` in `RESULT_STATUS.txt`
  (74,632,830,976 / 74,630,221,824) are a second `df` sample and are **not** used (C1: cite one consistent source).
  Post-run footprint: evidence root **4.4 M**, this node's evidence **4.0 M**, runs **3.8 M**, node data 517 M,
  whole data root 2.9 G (`disk_after.txt`, `runs_du.txt`); nothing deleted, no push, no commit.

**Scope statements.** One node only (`mlab_cifar10`); this result is not evidence, has no noise floor / D21 /
D28, no T1 label, no U3/unisolated claim, and is not pooled with any other node. No other user's GPU
process/card was touched or disturbed; no authors' other experiments were run; no autoresearch (C3-blocked),
HousePrice (STOP) or Breakout (not run) node was executed. One smoke only; no retry.

**Evidence index (this directory).** `SHA256SUMS` (every capture below; regenerated after the record corrections
and verified `shasum -a 256 -c` rc 0). `logs/run_node.log` (outer log with gate/scope/smoke stdout/CHECKLIST),
`smoke_stdout_extract.txt`, `cgroup_probe.txt`, `time_v.txt`, `invocation_inner.sh`, `gate/`,
`gpu/` (qualify/before/mid/after), `sampler/` (required + timestamped CSV, `sampler_max.json`), `host.txt`,
`env.txt`, `env_freeze.txt`, `data_manifest.txt`, `kit.txt`, `pins.txt`, `disk_before.txt`, `disk_after.txt`,
`runs_du.txt`, `record_hashes.txt`, `summary.json`, `verify_records.json`, `verify_full.json` (+ preserved v1),
`RESULT_STATUS.txt`, `DONE`, `unit/` (the executed unit bytes), `scripts/` (the final runner/verifier/sampler-max
sources, the two documented fix patches, and a README), and the nine per-run
`runs/…/{run_record.json,run.log,result_channel.txt}` (plus the smoke work trees). Raw run trees and helper logs
are **preserved unaltered** on Ada under
`/home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlab_cifar10_20261119T033747Z/` (live dirs `drwxrwxr-x`, files
`-rw-rw-r--`, hash-matching; not filesystem-read-only) — no deletion.

**Correction note (2026-11-19T04:30Z).** This record was corrected per the accepted MINOR-only conditions of
`docs/r1/reviews/TRACKG_U2_ISO_RESULTS_REVIEW_20261119.md` (node C1–C5 + shared S1–S10), without re-running GPU/U2
and without changing any measured number except where a cited source was wrong. Changes: C1 disk `df` numbers now
from `disk_before/after.txt` (74,632,835,072 / 74,630,283,264 B) rather than `RESULT_STATUS.txt`; C2 gate time now
the gate JSON `utc` `03:37:51Z` with the `03:37:47Z` evidence-dir timestamp explained; C3 setup-log sha
`6747f821…` added; C4 licence/provenance line added; C5 STOP→PASS status reconciliation disclosed; data-root
wording (S7), read-only wording (S8), `data_link=` print (S9), floor basis/mid-run rule (S5), no-resume (S6),
mR6/shas (S3), dry-runs (S1), executed-unit preservation (S10) added. Full change list and the new record/SHA256SUMS
shas are in `docs/r1/reports/trackg_g0_20261117/U2_ISO_RECORD_CORRECTIONS_20261119.md`.
