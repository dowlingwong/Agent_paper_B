# Track G G.0 U2 isolated-node raw cost — node `mlgym_houseprice` (isolated kit, CPU) — RESULT (20 November 2026)

**Status: PASSED — `CHECKLIST_E_PASSED mlgym_houseprice`; one node only, one smoke, no retry.**
Authority: `R1-TRACKG-G0-GO` (one node per unit, independently reviewed), `R1-HARNESS-ISOLATION`,
`R1-TRACKG-PORT-DECISIONS` **(2)** (House Prices must use the user's Kaggle `train.csv` via `--from-file`, its
sha256 recorded, MLGym's copy not used) and (4) (node timeout = census baseline × 3 as the proposal's failure),
`R1-TRACKG-LICENCES`, `R1-TRACKG-G3-EARLY` (20 Nov: `mlgym_houseprice` joins T1 once its U2 passes), port report
`docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md` §2/§7, the accepted kit update
`docs/r1/reports/trackg_g0_20261117/TRACKG_ISO_KIT_UPDATE_20261119.md` (sha256
`fe232e2bbf236337e208f11e97c809f8a41d7ef101567eeb0d11153bacb9d026`) and review (sha256
`d8c68f9f0463d1aa3e17f82527dfb7ecf7b6070831584cd1024a6d39ed6a21b4`, ACCEPTED). Unit
`docs/r1/proposals/u2_iso_20261119/U2_ISO_MLGYM_HOUSEPRICE_UNIT_20261120.md`:
**executed amended bytes sha256 `0f13d2dc5d59bc487658018764d9517148540bc9cfe4b5313ba75435d77f94fe`**; the
R2-reviewed bytes were `397ccfd1d985d8e265a1dc1d6ad687ee8265947ea05282e3c38a1ae3df463551` (`docs/r1/reviews/
TRACKG_U2_ISO_HOUSEPRICE_UNIT_REVIEW_R2_20261120.md`, sha256
`81580eec0afced568a5892c2bab5ff3429eb2e47e559ab19932de8b5e4bc6d51`, **ACCEPTED — 0 BLOCKING, 0 MAJOR, 17 MINOR,
conditional C1–C7**; the amendment applied the one mandatory pre-execution defect — the one-physical-line launch
sentence — and removed the truncated pin literal; the C1–C4 substance is implemented in the launch/result records
while other R2 text residues remain in the executed unit, see H6); round-1 review
`…TRACKG_U2_ISO_HOUSEPRICE_UNIT_REVIEW_20261120.md` sha256
`36774ed52e93fae1e2393de6ce989810603897c91b8d1286b19a691dce505025`, NOT ACCEPTED). This result was corrected
per the accepted MINOR-only result review `docs/r1/reviews/TRACKG_U2_ISO_HOUSEPRICE_RESULT_REVIEW_20261120.md`
(sha256 `b2c463a7941891b115ca2b89037e1f2fef0c760582b65dd709add54641202134`; conditions H1–H10/S1–S5; see
Correction note). ENGINEERING_ONLY;
**not evidence**; no noise floor/D21/D28; no T1 label; no cross-node pooling; no TASL-7/TASL-2,
no HTCondor/deepthought, no other host; no deletion; no push/commit; read-only on Mac records (only this new
result directory is written).

**Input — author-supplied Kaggle `train.csv` (verified on host; no staging copy, no MLGym copy).**

- Path `/home/dowling/house-prices-advanced-regression-techniques/train.csv` (author placement 20 Nov 2026 —
  deliberate path move from the 19 Nov `~/r1_inputs/house-prices/train.csv`; kit update §9 records
  `/home/dowling/r1_inputs` absent then). Kaggle competition
  `house-prices-advanced-regression-techniques` (`train.csv`, the user's Kaggle download/terms).
- **Full sha256 `1e18addf81e5e4d347cc17ee6075bbe4a42b7fa26b9e5b063e8f692a5f929d41`** (prefix `1e18addf`,
  suffix `929d41`); **md5 `80ccab65fb115cbad143dbbd2bcd5577`**; size **460,676 bytes** (450 K);
  **1,461 lines** (1 header + 1,460 rows); `mtime 2019-12-15 21:33:36 -0800`, mode `-rw-rw-r--`
  (`prep/csv_verify.txt`, sha256 `62e8a8af…`; its "no copy made" line refers to the author's placement — no
  staging copy at that step). Hash check **PASS**. The sha256 happens to equal MLGym's copy
  (`same_as_mlgym_copy=True`, informational); setup used the author's file via `--from-file` (the
  `prep/setup.log` and the manifest's `provided_by`/`from_file_name` record that — the run's `AR_DATA` line
  records only sha256/md5/`same_as_mlgym_copy`, not the `--from-file` path, S5).
  - **Prepared-data copy (H4, corrected wording).** The kit's `prepare_data.py` **writes** the prepared file
    `<out>/houseprice.csv` as a byte copy of the `--from-file` source (`prepare_data.py:69`
    `(out / "houseprice.csv").write_bytes(data)`), so a prepared copy of the author's data **does** exist in
    the data root: same sha256 `1e18addf…`/md5 `80ccab65…`, **different inode** from the author file (live
    read-only: author `train.csv` inode `66606474`, prepared `houseprice.csv` inode `78787219`). What is **not**
    made is a separate staging copy of the author file and there is **no MLGym copy**; the author file remains
    the verified source of record. The run logs' `AR_DATA houseprice_sha256=… md5=… same_as_mlgym_copy=True` line
    is informational about the digests, not a record of the `--from-file` path.

**Data setup (guarded, logged; no deletion).**

- Guard: `test -n "$AR_TRACKG_DATA_ROOT" && test -n "$AR_HOUSEPRICE_TRAIN_CSV"` with
  `AR_TRACKG_DATA_ROOT=/home/dowling/r1_trackg_20261117/data`,
  `AR_HOUSEPRICE_TRAIN_CSV=/home/dowling/house-prices-advanced-regression-techniques/train.csv`; run from the
  node dir with `envs/torch312/bin` first on `PATH`; no old/partial `--out` existed
  (`prep/out_guard.txt` sha256 `89e90172…`; `moved_partial_aside=none`); **SETUP_RC=0**
  (`prep/setup.log` sha256 `6028914804cbf1729ac1335461f6e757c4051e8fce9bfe3fa118e33b8effecec`).
- Exact command:
  `cd third_party/mlgym/nodes/mlgym_houseprice && PATH=envs/torch312/bin:$PATH python3 prepare_data.py
  --out $AR_TRACKG_DATA_ROOT/mlgym_houseprice --from-file $AR_HOUSEPRICE_TRAIN_CSV`.
- **`data_manifest.json` sha256 `73ee55972381fd36ee5b3244467d7f05333adfc292ed48089786b366d5c686ff`**
  (`prep/manifest.txt` sha256 `2c7686f2…`); `source.provided_by` = “user download, passed with --from-file”;
  **`from_file_name` = `train.csv`** (the manifest records the name, not the path);
  `source.sha256 == files.houseprice.csv.sha256 == 1e18addf…`, `source.md5 = 80ccab65…`,
  `source.rows = 1460`, `source.kaggle = …/house-prices-advanced-regression-techniques/data (train.csv)`;
  files: `houseprice.csv` 460,676 bytes; **`synthetic` key absent (synthetic false / no marker)**; data tree
  read-only (`dr-xr-xr-x` dir / `r--r--r--` files); node `data` link →
  `/home/dowling/r1_trackg_20261117/data/mlgym_houseprice` (outside the repo); data 460 K, 2 files.
- `AR_DATA` lines: setup `AR_DATA manifest_sha256=73ee5597… files=1`; every run's log carries
  `AR_DATA houseprice_sha256=1e18addf… md5=80ccab65… same_as_mlgym_copy=True` (recorded by the verifier).

**Kit / host / env.**

- Kit `harness_iso_mlgym`, branch `mac-trackg-iso-mlgym-20261117`, **tip `f07875de79a5a57739227b13e0fd52d31646edaf`**;
  launch check `git rev-parse HEAD` = tip and `git status --porcelain --untracked-files=no` empty (only the
  three expected untracked runtime `data` symlinks: cifar10, fmnist, houseprice) (`kit.txt` sha256 `a883f308…`).
- Node spec `third_party/mlgym/configs/trackg/nodes/mlgym_houseprice.yaml` **file sha256
  `1b95447d3d1c0753a11749fc4b11639959e770f1aa10a142b2ff583d5a92a389`**; the run records' canonical
  `node_spec_sha256` = `2f150cded7c846a28fd97113519333a33d9775588a7d6c7bd0d9dcc05e85c049` (kit
  `_canonical_sha256` of the parsed spec = `spec.raw_sha256`, recomputed live read-only with the kit's own
  loader). **S5 correction:** the fixed verifier's rows record only the **canonical** `node_spec_sha256`; the
  spec **file** sha `1b95447d…` is not recorded by the verifier and is cited from `kit.txt:11`.
  Representative-edit manifest sha256
  `f26332ff9e75bbda708f40581a904ba474f849c7b7e0564a1513923b2393e34b`; `LICENCES.md` sha256
  `a8a2c62b048912ebb84ebe14b044fee1ec1e1d7a9a30f55133f02e58b0dea77b`; `requirements.txt` sha256
  `31b0189a57f4a4b233687d2b1edee3f1465ce5511cd63f681c2c2dd37ec67765`.
- Env `/home/dowling/r1_trackg_20261117/envs/torch312`, Python **3.12.16**, numpy **2.5.4**, pandas **3.1.1**,
  scikit-learn **1.9.1**, pytest **9.2.0**, torch **2.6.0+cu124**; `uv pip freeze` **77 lines**, sha256
  **`d2e70fe45ce8db8dcf478c28a89a4d3c40fe448edd83b834c0eb8cd63ad09a42`** (matches the expected torch-env
  freeze; the live in-scope re-check reproduced it) — `env.txt` sha256 `e0ac02ea…`, `env_freeze.txt` sha256
  `d2e70fe4…`. CPU-only node: no `--gpu-uuid`, `CUDA_VISIBLE_DEVICES=""`, torch reports
  `cuda.is_available() = False` under the mask.
- Host `ucrtasl`, Ubuntu 22.04.5, kernel `5.15.0-151-generic`, 96 CPUs, 503 GiB RAM, boot id
  `5c90a8fe-5f9b-4914-a2c7-5b864e0a8b8d` (`host.txt`).
- **Static tests (CPU-masked, before the smoke) — command/mask capture reconciled (H5):** the captured
  `prep/static_mlgym_20261120T214935Z.log` (sha256
  `aec75c45ea579e1c6c6fa088343efae0a2c3fc885ce0c27fee7d647300ba1e5a`) records only the kit/tip/start header,
  `Running scope as unit: …`, the pytest progress/failures, `2 failed, 225 passed, 1 skipped, 6 deselected in
  48.33s`, `PYTEST_EXIT=1`, and the footer `# end=…`; it does **not** echo the exact command, and
  `prep/static_launcher.log` is 0 bytes because the helper redirects the launcher output straight to the static
  log. The command/mask are reconciled in the new `prep/static_command_note.txt` from the accepted kit-update
  helper `run_static_tests.sh` (live sha256
  `7a9d57fa0514997c2b2c7c2887126b1554937c73a58bd6cc0429fab25957c05d`, whose header/footer format and scope
  line match the capture): `systemd-run --user --scope -p Delegate=yes -- bash -c '…'` with
  `taskset -c 0-15`, `CUDA_VISIBLE_DEVICES=`, `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1`, interpreter
  `envs/torch312/bin/python`, `python -m pytest tests/trackg -q -p no:cacheprovider -k "not smoke"` → the
  accepted counts (225 passed, 2 known environment failures, 1 skipped, 6 deselected in 48.33 s; the interpreter
  is also visible in the failure trace's subprocess argv). The static test was **not** re-run.

**Pins (both full 64-hex, separately; census value = committed-file pin).**

- **Committed-file `frozen_pin_sha256`** (read at launch from the accepted kit-update §3/§9 capture
  `pins/new_mlgym.json`, sha256 `8974359b1fd5c11105dc98b593dcb1c84b33d59896fe3e63bf7cb6c3b1e4a451`):
  **`88d359f2c59449a5c49d75d40fedd72436f76154e78b622f8c69b384a1d5a654`** (16 frozen entries).
- **Deployed run-record pin** (every record's `frozen_pin_sha256`; 17 entries incl.
  `data: link:/home/dowling/r1_trackg_20261117/data/mlgym_houseprice`):
  **`4cbbc5d6673d1e0cff15e1df4ea6dfe6941ac028b68109f1b86849ab9e36a144`** — equal to the R2-review C1
  expected value and to an independent recomputation from the kit's own spec with the data link present
  (`pins.txt` sha256 `f9514cf6…`). The two are not interchanged; the census uses the committed pin.

**Record identity and preserved bytes (S1).** This result file is
`docs/r1/reports/trackg_g0_20261117/u2_iso_mlgym_houseprice_20261120T215244Z/U2_ISO_MLGYM_HOUSEPRICE_RESULT_20261120.md`;
its own **post-correction sha256** is the `./U2_ISO_MLGYM_HOUSEPRICE_RESULT_20261120.md` entry in this directory's
regenerated `SHA256SUMS`, and the post-correction record sha, `SHA256SUMS` sha and changed-file list are recorded
in `docs/r1/reports/trackg_g0_20261117/U2_ISO_HOUSEPRICE_RECORD_CORRECTIONS_20261120.md` (the superseded original
values were record sha `c043f0dd3bdf3337df6ca25b7cab075dbd92b4c59b6fec3e0d8f5d390369e178` and `SHA256SUMS` sha
`80a835243830471f3df406478455652cf286c93e991daed5b7b765b826cae84c`). Node spec: raw file sha
`1b95447d3d1c0753a11749fc4b11639959e770f1aa10a142b2ff583d5a92a389` (kit.txt:11), canonical `node_spec_sha256`
`2f150cded7c846a28fd97113519333a33d9775588a7d6c7bd0d9dcc05e85c049` (kit loader:
`sha256(json.dumps(payload, sort_keys=True, separators=(",",":"), ensure_ascii=False, default=str))`, recorded by
the kit's runner as `spec.raw_sha256`; = every run record). Representative-edit manifest sha
`f26332ff9e75bbda708f40581a904ba474f849c7b7e0564a1513923b2393e34b`; representative-edit diff shas E1
`3ee108ef77b9fd406e1151d2bda768fefb156f3e69ac9ddc3cef59e35635b81c`, E2
`7e4a71a00ce7589f12aa4575e9598a83e91dcba14f8ca85d09e41466b5eb51ad`, E3
`81eaa685ca30cf53ee2655852b9af966d61206f15a733d50ae43b0c826878ebe`, E4
`e9a1e8e9d00413b7b9439d8b5543f1c928a26d67388fd9cc938f044eb855f63f`. Executed unit bytes are preserved at
`references/U2_ISO_MLGYM_HOUSEPRICE_UNIT_20261120.md` (sha `0f13d2dc…`), with the R2 review
(`81580eec0afced568a5892c2bab5ff3429eb2e47e559ab19932de8b5e4bc6d51`) and round-1 review
(`36774ed52e93fae1e2393de6ce989810603897c91b8d1286b19a691dce505025`) byte-identical to the repo files.
Preserved script bytes:
`scripts/run_node_houseprice.sh` sha `360b2053…`, `scripts/verify_u2_records_cpu.py` sha `63a4bdf1…` (both
byte-identical to the live campaign scripts) plus the new `scripts/README.txt`. The smoke log carries **one JSON
record line per run** (`verify_full.json` `smoke.json_run_lines: 9`), and every executed record has
`process.killed_with: null`, `timed_out: false`, `returncode 0` (except the deliberately divergent `s002`, see
below).

**C1–C7 unit-vs-launch/result split (H6).** The executed unit text (`0f13d2dc…`, 78 lines, unchanged in this
record-only correction pass) incorporates the one **mandatory pre-execution defect** the R2 review said would
stop a literal launch — the "launch command must be one physical line" sentence — and removed the truncated pin
literal. It still carries the other R2 **MINOR text residues** (m2 source path/hash phrase `unit:36-37`; m6 no
exact gate command; m7 no cpuset/threshold; m8 no B1/B2 definitions; m9 "(or record why not)" `unit:61-62`;
m13 citations; m14 exact git checks; m15 "no force push" `unit:9`; m16 no env-freeze STOP). Recorded here as
required: the **launch/result records are the operative form** and implement the C1–C4 substance —
**C1** both pins (this record's Pins section, `pins.txt`, `prep/pins.txt`); **C2** author file + guarded setup +
manifest (`prep/`, this record's Input/DataSetup sections); **C3** one-line launch command, inside-scope probe,
gate command/three-check/UTC, `which python`/imports/freeze prechecks (`invocation_inner.sh`, `cgroup_probe.txt`,
`gate/`, `prechecks.txt`); **C4** CPU co-tenancy/thresholds/snapshots, B1/B2 labels, static test, scope/STOPs
(`cpu/`, this record, `prep/static_mlgym_…log`). The executed unit bytes are **not amended** in this correction
pass (no unit edit); the remaining residues are recorded, not silently claimed fixed.

**Paper A gate (captured immediately before launch; three-check).**

- Gate JSON `gate/gate_20261120T215244Z.json` sha256
  **`31082f5bcbea772b21b45b1e6caa81f940744effec1559df2ac864cd317c1987`**, UTC
  **`2026-11-20T21:52:50Z`**, command
  `envs/torch312/bin/python r1/scripts/paper_a_status.py --config r1/scripts/configs/paper_a_status_ada.json`
  rc 0.
- **Three-check PASS**: `verdict: clear_finished`, `paper_a_live_waiting_for_card: false`,
  `paper_a_processes: []`, `unidentified_apps: 0`; newest v4 `live_*` == configured run dir; self-excluded
  `pgrep` for `port_smoke_gpu` empty; `pgrep agent-checkpoint-intervention` empty (`gate/gate_check.txt`).
- **Attempt-1 pre-launch STOP (no smoke launched):** the first launch at `21:52:13Z` selected cpus
  `95,94,93,91,84,83,82,80` and was refused by the CPU-idle guard (mean idle 70.6 % < 80 %); **no
  `port_smoke_gpu` was started and no unit smoke was consumed**. Evidence preserved as
  `attempt1_prelaunch_cpu_idle_stop/` (`DONE_PRELAUNCH_STOP` 21:52:19Z). **Attempt-2 timing corrected (H1):**
  `21:52:44Z` is the runner/evidence-dir start (`logs/run_node.log:1` `start=`), the **gate JSON `utc` is
  `21:52:50Z`**, the gate check capture is **`21:52:52Z`**, and the inside-scope cgroup probe and prechecks are
  **`21:52:52Z`** (`cgroup_probe.txt:13`, `prechecks.txt:1`); the smoke starts after them, so the **gate truly
  precedes the launch/scope** (the launcher runs the gate before `systemd-run`). The single executed smoke is
  attempt 2 (cpuset `79,78,77,76,59,42,34,28` chosen from live load; see H7 below).

**CPU co-tenancy (CPU node; no GPU/VRAM fields — the unit does not require them).**

- Idle CPU set recorded: **cpuset `79,78,77,76,59,42,34,28`** (8 of 96 CPUs), selected from live load under the
  threshold check; `taskset -c` used for the smoke and passed as `--cpus`. **Selection-window wording corrected
  (H7):** the claim of a "fresh 3-sample stable-idle window (minimum %idle)" is **not captured** — what is
  captured is the harness before snapshot (`cpu/cpu_before.txt`: selected-set mean idle **80.0 %**, `cpu_summary`)
  and the runner's separate one-sample selected-set check **97.4 %** (`cpu_before.txt` tail); i.e. two 1-s
  samples (both ≥ 80 %), not a 3-sample minimum.
- Thresholds: 1-min load ≤ nproc/2 (48) and selected-set mean idle ≥ 80 % at the before check → PASS
  (1-min load 37.40; the runner's separate selected-set sample mean idle **97.4 %**).
- Snapshots (`cpu/cpu_before.txt` sha `cab8272f…`, `cpu/cpu_mid.txt` sha `f7543283…`, `cpu/cpu_after.txt` sha
  `0cddd6ed…`; summary `cpu/cpu_summary.txt` sha `406908f9…`): loadavg
  **37.40 / 37.13 / 34.21**, selected-set mean idle **80.0 / 71.8 / 99.9 %**. **Mid-sample wording corrected
  (H7):** the mid snapshot is early in the 43.97 s smoke, right after the smoke process exec'd (its interpreter/
  imports), **not** during the fit — it is not a mid-smoke snapshot.
- **CPU co-tenancy claim narrowed (H3).** The co-tenancy PASS rests on the recorded load/mpstat/users/nproc
  evidence: 1-min load 37.40 / 37.13 / 34.21 (≤ 48), the `cpu_before.txt` users census
  (`root, hongkunyang, vla-reasoning, jiachenl, asif, wenqianzhang, zli538, xzhan006, jzhan744, zihaozhao`),
  mpstat selected-set mean idle 80.0 / 71.8 / 99.9 %, the runner's 97.4 % ≥ 80 % check, and `taskset`
  confinement (`disturbed_other_users=no` — no signal/kill/renice/affinity change was sent to any foreign
  process). **What the per-CPU process list does and does not establish:** the list is
  `ps -eLo … | head -40` (the "# foreign processes on the selected cpus" section in `cpu/cpu_mid.txt` /
  `cpu_after.txt` is exactly 40 root-kernel-thread rows); the node's own smoke process sorts after the low-PID
  kernel threads and is **cut by the 40-row cap**, so "only root kernel threads / no other user's process was
  observed on the selected cpuset" is **not established by the capture**, and the summary lines
  `dowling_proc_rows=0` / `other_user_proc_rows=0` are artifacts of the cap. The corrected capture is
  `cpu/cpu_summary.txt`; the preserved v1 parser artifact
  `cpu/cpu_summary.v1_parse_artifact.txt` (sha256
  `077de1c188d99225fc5ff6d2ae4cdfa6852b203edd2a7bedf0573fb59eed0f`) shows the v1 parser's
  `foreign_users_on_selected_cpus=['root','the']` and is **disclosed as a parse artifact, not evidence of a
  foreign job**. The smoke was confined to its taskset affinity.
- 8 GiB delegated scope basis: the accepted R1-HARNESS-ISOLATION construction (host RAM 503 GiB; the node's
  whole smoke max RSS 599,392 kB ≪ 8 GiB; the cap is enforced by the systemd user scope, not needed for
  sizing).

**Run (unit command shape, CPU, exactly one smoke).**

- Inside `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c '…'`
  (logged unit `run-r3861b8588c684aa6a76ad8d9c53a4c33.scope`; the launch command is one physical line):
  `cd harness_iso_mlgym`, `CG=$(cut -d: -f3 /proc/self/cgroup)`,
  `AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG`, `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1`,
  `PATH=…/envs/torch312/bin:$PATH`, `VIRTUAL_ENV=…/envs/torch312`, `CUDA_VISIBLE_DEVICES=""`,
  `taskset -c 79,78,77,76,59,42,34,28 python -m tests.trackg.port_smoke_gpu --node mlgym_houseprice
  --cpus 79,78,77,76,59,42,34,28 --memory-limit "external: systemd-run --user --scope -p MemoryMax=8G
  -p MemorySwapMax=0 (enforced cgroup)" --runs-root <outside repo>/runs --provisional-timeout 1800` —
  **no `--gpu-uuid`** (CPU node). Resolved invocation `invocation_inner.sh` sha256 `9d258ba3…`.
- **Inside-scope prechecks** (`prechecks.txt` sha256 `b29d4e9a…`): `which python` =
  `…/envs/torch312/bin/python`; Python 3.12.16; numpy/pandas/sklearn/pytest/torch versions as above; live
  `uv pip freeze` sha256 `d2e70fe4…` == expected; data manifest sha256 `73ee5597…` == setup manifest; node
  `data` link resolves; `import tests.trackg.port_smoke_gpu` OK; `smoke_entry("mlgym_houseprice")` found
  (budget 1); a mismatch was a STOP.
- **Cgroup enforcement probe (inside the scope, from the echoed path)**: `scope_cgroup=…/run-r3861b858…
  scope`, **`memory.max=8589934592`**, **`memory.swap.max=0`** (expected bytes; mismatch = STOP);
  `which python` after PATH = torch312, `CUDA_VISIBLE_DEVICES=""`, `taskset_cpus=79,78,77,76,59,42,34,28`
  (`cgroup_probe.txt` sha256 `188bd0ec…`).
- **rc 0; `CHECKLIST_E_PASSED mlgym_houseprice`; `SMOKE_EXIT=0`; `systemd_run_rc=0`** (smoke stdout
  `smoke_stdout_extract.txt` sha256 `0e6a11a2…`, sha of `logs/run_node.log` `14a45837…`).
- **`time -v` for the whole smoke (aggregate, not a per-run peak)**: user **47.60 s**, system **8.35 s**,
  wall **0:43.97**, max RSS **599,392 kB**, exit status 0 (`time_v.txt` sha256 `34f17ab1…`).
- Timeout: provisional 1800 s; **node timeout = 3 × measured B1 = 15.177 s**; no timeout/OOM; no retry.
  **No resume (S2):** an interrupted unit re-runs wholly from a new `<runs-root>`; no resume occurred here.
  `--runs-root` outside the repository (3.6 M).

**Result — B1/B2 and every edit outcome.** `outcome.value` is `val_rmse` (`AR_METRIC val_rmse=`);
the sealed value is `sealed.test_rmse` from the run's result channel (`AR_TEST test_rmse=`, not the manager
view). Budget is **one fit (`run_budget {kind: steps, value: 1}`)** for every run.

| run | kind | executed | `val_rmse` (outcome.value) | `elapsed_seconds_info_only` | sealed `test_rmse` |
|---|---|---|---|---|---|
| `s000_baseline` **B1** | baseline | true | **23344.767385** | **5.059 s** | **30295.671017** |
| `s001` | frozen-diff refused (`scope_violation`) | **false** | — (null) | — | — |
| `s002` | broken diff `divergent/non_finite_loss` | true | — (null) | 5.142 s | `NaN` (bare literal; non-finite, not used — H9) |
| `s003` | first declared edit (selection discarded: 25212 > baseline) | true | 25212.233839 | 5.126 s | 31026.614481 |
| `E1` | declared edit | true | 25212.233839 | 5.291 s | 31026.614481 |
| `E2` | declared edit | true | 25763.93275 | 5.266 s | 33085.957104 |
| `E3` | declared edit | true | 19369.761061 | 5.058 s | 23698.247199 |
| `E4` | declared edit | true | 23241.878689 | 6.794 s | 27813.556114 |
| `B2` | repeat baseline | true | **23344.767385** | **4.876 s** | **30295.671017** |

- **`s002` sealed-value labelling (H9).** The deliberately divergent run's record writes the **bare literal
  `NaN`** for `sealed.test_rmse` (`runs/runs_smoke/s002/run_record.json:264`), which is **not strict JSON**
  (only Python's `json.load` accepts it). It is a non-finite value for the broken diff and is **not used** as a
  measurement (the sealed `test_rmse` values in the table for the ok runs come from the result channels'
  `AR_TEST test_rmse=`). No measurement impact; labelled here and in the deviations.
- 9 `run_record.json`, **8 executed + the refused frozen diff (`s001` `executed:false`)**; `B2` reproduces
  `B1` exactly (val_rmse 23344.767385 / sealed test_rmse 30295.671017). Baseline record
  `runs/runs_smoke/s000_baseline/run_record.json` sha256
  **`e2e1c33dd5751359e81522b97c1c6501ed0afc6f921d3cf7da250794c2281fea`** (run.log sha256
  `49ccea84fb90cc51ebd61461e7ffc775fa2a3e840ce5dd547dbaf0f037318d20`, result-channel sha256
  `b95e70242ca1998479a5e1b50219f89b6afcba9513525e474b23a6c95b017e8d`; B2 record sha
  `11b739da55d5a0044be13e4f092252158edcebde2db267a15ecb597dd79e735d`). All per-run
  record/log/result-channel hashes: `record_hashes.txt`.

**Isolation record gate (every executed record).**

- Every executed record: `isolation.effective: true`, `isolation.waivers {}`, `isolation.exceptions []`,
  `log_intact: true`, result channel present (`result_channel_overflow: false`, `result_channel_sha256`),
  cgroup kill `method: cgroup.kill` with `empty_after: true` and `removed: true`; `limits.external_limit`
  exactly the one-line unit string; `gpu_uuids: []` (CPU node), `cpu_list [79,78,77,76,59,42,34,28]`,
  `memory_method: external`, provisional timeout 1800 s, timeout factor 3.0; `run_budget steps 1`;
  `determinism.not_forced == ["dataloader_workers"]`, `shim_loaded: true`, torch 2.6.0+cu124;
  `process.killed_with: null`, `timed_out: false`, ok runs `returncode: 0`; canonical node-spec sha full
  64-hex; deployed pin full 64-hex. `s001` is `executed:false`, `outcome:null`, `scope_violation`,
  no isolation fields (by design).
- Verifiers: `scripts/verify_u2_records_cpu.py` **rc 0, `ok: true`, 9 records / 8 executed / refused_s001
  true, sealed_key `test_rmse`, deployed pin == expected, AR_DATA line sha/md5 match** (`verify_full.json`
  sha256 `553c4079…`, `verify_full.summary.txt`); accepted kit helper `verify_records.py` **rc 0, issues []**
  (`verify_records.json`); `collect_smoke_summary.py` **rc 0, gate_ok true, issues []** (`summary.json`
  sha256 `71198106…`).
- **Deviation (verifier false negative, not a smoke failure):** the first verifier run wrongly required the
  record's `node_spec_sha256` to equal the on-disk spec file sha; the kit's record field is the canonical
  parsed-spec hash (`2f150cde…`) while the file sha is `1b95447d…`. The verifier was fixed (full 64-hex
  canonical check) and re-run **on the same records** (no smoke re-run); originals preserved as
  `verify_full.v1_verifier_bug.json` / `verify_full.summary.v1_verifier_bug.txt`, correction recorded in
  `RESULT_STATUS.txt`/`DONE`.
  - **H8 residual:** the v1 verifier **source/patch was not preserved** (edited in place; only the fixed script
    and the v1 outputs remain). The one-line change is recorded in the new `scripts/README.txt`: v1 compared the
    record to the spec **file** sha (`node_spec_sha256 expected`, 8/8 issues), the fixed rule accepts the full
    64-hex **canonical** value that the kit's runner records (`spec.raw_sha256` = `2f150cde…`, verified live).
    The preserved v1 outputs' check names are the evidence; a byte-exact v1 source is not reconstructed.
  - **Authority of the corrected status (H10):** `RESULT_STATUS.txt` still begins with the historical
    `STOP`/`status=STOP` block and `DONE` still contains the first `DONE_STOP`, with
    `status_corrected=PASS`/`verify_full_rc_corrected=0` appended and `DONE_PASS_CORRECTED` last. The **corrected
    PASS block is authoritative** for the census/commit: the fixed verifier is rc 0 (`ok: true`, 9 records /
    8 executed / refused `s001`), the accepted kit helper `verify_records.py` is `issues: []` and
    `collect_smoke_summary.py` is `gate_ok: true` **on the same records**; the first STOP block is history from
    the verifier false negative, not the result.

**Disk / footprint.**

- `df -B1 /` (`/dev/md0p3`, mounted `/`) available **before `70,644,187,136 B` (65.8 GiB)**, **after
  `70,795,374,592 B` (65.9 GiB)** — the `disk_before.txt`/`disk_after.txt` capture values; both are above the
  50 GiB STOP floor and the footprint is far below the 100 GiB cap. **H2 correction:** the runner's
  `RESULT_STATUS.txt` `disk_avail_after_bytes` sample (`70,795,313,152 B`, a different `df` instant) is **not**
  the cited source; the before values happen to agree. Post-run footprint: evidence 3.8 M, runs 3.6 M, data
  460 K (`disk_after.txt`, `runs_du.txt`); whole data root **2.9 G** (live read-only `du -sh
  /home/dowling/r1_trackg_20261117/data` = 2.9 G, verified in this correction pass; it is not in the run's disk
  captures — S5); nothing deleted, no push, no commit.

**Licence / provenance.** MLGym task `regressionKaggleHousePrice` is **CC BY-NC 4.0** (non-commercial;
attribution and changes recorded in the node's `LICENCES.md`, sha `a8a2c62b…`) under `R1-TRACKG-LICENCES`;
the Kaggle House Prices table is used under the **user's Kaggle terms**, only `train.csv`, and **not**
MLGym's copy (port decision (2)); the gymnax-derived Apache-2.0 parts are **not used by this node**. The
census funnel/appendix must carry this licence/provenance line.

**Deviations (recorded; no smoke re-run).**

1. **Attempt-1 pre-launch CPU-idle STOP** at `21:52:13Z` (mean idle 70.6 % on the first candidate cpuset);
   no smoke launched; preserved as `attempt1_prelaunch_cpu_idle_stop/` (live attempt-1 `runs/`/`gate/` empty).
2. **Mid-run CPU snapshot timing (H7):** the mid snapshot was taken early in the single 43.97 s smoke, right
   after the smoke process exec'd (interpreter/imports), **not** at its midpoint and not during the fit;
   before/after snapshots and the whole-smoke `time -v` are recorded.
3. **First verifier false negative** on the node-spec hash convention (canonical record hash vs spec file sha);
   fixed and re-run on the same records, original outputs preserved; see H8 for the unpreserved v1 source/patch.
4. **Per-CPU process census truncated + v1 parser artifact (H3).** The per-CPU list is `ps -eLo … | head -40`;
   mid/after contain exactly 40 root-kernel-thread rows and the node's own smoke process is cut by the cap, so
   "no other user's process on the selected cpuset" is not established by the list — the co-tenancy PASS rests
   on load/mpstat/users/nproc (see the CPU section). The preserved `cpu/cpu_summary.v1_parse_artifact.txt`
   (sha `077de1c1…`) with `foreign_users_on_selected_cpus=['root','the']` is a **parse artifact**, disclosed
   here and not evidence of a foreign job; the corrected capture is `cpu/cpu_summary.txt`.
5. **Cpuset selection window (H7):** the captured evidence is the harness before snapshot
   (`cpu_before.txt`: selected-set mean idle 80.0 %) plus the runner's separate one-sample check (97.4 %), i.e.
   two 1-s samples both ≥ 80 % — **not** a captured 3-sample minimum window.
6. **Prepared-data copy (H4).** `prepare_data.py` writes the prepared `houseprice.csv` (byte copy of the
   author's `--from-file` source; same sha256/md5, different inode) into the data root; there is no separate
   staging copy and no MLGym copy. The `AR_DATA` line records digests/`same_as_mlgym_copy`, not the
   `--from-file` path — the setup log and manifest `provided_by`/`from_file_name` record the source.
7. **Static-test command not echoed in the capture (H5).** The static log holds the header/scope/pytest output
   only, and `static_launcher.log` is empty because the helper redirects output to the log; the exact
   command/mask are reconciled in `prep/static_command_note.txt` from the accepted kit-update helper
   (`run_static_tests.sh`, sha `7a9d57fa…`) whose log format matches the capture. Not re-run.
8. **`s002` sealed value (H9).** The divergent run's record writes a bare literal `NaN` (non-strict JSON,
   non-finite) for `sealed.test_rmse`; labelled as non-finite/not-used, no measurement impact.
9. **Status history (H10).** The first `STOP` block in `RESULT_STATUS.txt`/`DONE` is the verifier false-negative
   history; the appended corrected `PASS` block (fixed verifier + kit helper + summary) is authoritative.
10. The selected cpuset was chosen from live load; foreign users' jobs were running elsewhere on the host
    (load ~37/96) and none was signalled/killed/reniced; the per-CPU list cap (H3) means its absence from the
    list is not proof, and the load/mpstat evidence supports the co-tenancy PASS.

**Scope statements.** One node only (`mlgym_houseprice`); this is the first HousePrice isolated measurement (no
accepted pre-run baseline); not evidence, no noise floor/D21/D28, no T1 label, no U3/unisolated claim, no
cross-node pooling. No other user's process/card/host was disturbed; no authors' other experiments; no
autoresearch (C3-blocked), Breakout, or other census node executed. One smoke only; no retry.

**Evidence index (this directory).** `SHA256SUMS` (every capture; regenerated after these record corrections and
verified `shasum -a 256 -c` **rc 0, 447/447 entries OK** — the 445 original entries plus the two correction-pass
files below).
`logs/run_node.log` (outer log with gate/CPU snapshots/scope/prechecks/smoke stdout/CHECKLIST),
`smoke_stdout_extract.txt`, `cgroup_probe.txt`, `prechecks.txt`, `invocation_inner.sh`, `time_v.txt`,
`gate/`, `cpu/` (before, mid, after, `cpu_summary.txt`, the disclosed `cpu_summary.v1_parse_artifact.txt`),
`host.txt`, `env.txt`, `env_freeze.txt`, `data_manifest.txt`,
`prep/` (csv_verify, out_guard, setup.log, manifest, pins, env, static-test log, the new `static_command_note.txt`
reconciling the static-test command/mask — H5), `kit.txt`, `pins.txt`, `disk_before.txt`, `disk_after.txt`,
`runs_du.txt`, `record_hashes.txt`, `summary.json`, `verify_records.json`, `verify_full.json` (+ preserved v1),
`RESULT_STATUS.txt`, `DONE`, `attempt1_prelaunch_cpu_idle_stop/` (22 pre-launch copies), `references/` (executed
amended unit sha `0f13d2dc…`, R2 review sha `81580eec0afced568a5892c2bab5ff3429eb2e47e559ab19932de8b5e4bc6d51`,
round-1 review sha `36774ed52e93fae1e2393de6ce989810603897c91b8d1286b19a691dce505025`), `scripts/` (the exact
CPU runner and verifier plus the new `scripts/README.txt` recording the H8 v1→fixed one-line rule change), and
the nine per-run `runs/…/{run_record.json,run.log,result_channel.txt}` plus the smoke work trees (3.6 M).

**Raw-evidence preservation / live-vs-Mac split (S4).** The live Ada evidence dir holds the **417 raw capture
files only** (all byte-identical to this directory's `SHA256SUMS`; verified read-only in this correction pass),
and the live attempt-1 dir holds **22 files** byte-identical to the `attempt1_prelaunch_cpu_idle_stop/` copies.
The **30 local-only entries** (31 files including `SHA256SUMS`) are the Mac-authored records: the result md,
`SHA256SUMS`, the 22 attempt-1 copies, the three `references/` copies, the two `scripts/` sources, and the two
correction-pass files (`scripts/README.txt` for H8 and `prep/static_command_note.txt` for H5). Raw
evidence is **preserved unaltered** on Ada under
`/home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlgym_houseprice_20261120T215244Z/` (live dirs
`drwxrwxr-x`, files `-rw-rw-r--`, hash-matching; **not** filesystem-read-only) — no deletion.

**Correction note (2026-11-20T22:30Z).** This record was corrected per the accepted MINOR-only conditions of
`docs/r1/reviews/TRACKG_U2_ISO_HOUSEPRICE_RESULT_REVIEW_20261120.md` (sha256 `b2c463a7…`; H1–H10/S1–S5) without
re-running any smoke/U2 work, without editing the unit/code, and without changing any measured number. Changes:
H1 attempt-2 timing corrected (runner start `21:52:44Z`, gate JSON `21:52:50Z`, gate check and scope/probe/
prechecks `21:52:52Z`, gate precedes launch); H2 disk-after now `70,795,374,592 B` from `disk_after.txt` (not the
`RESULT_STATUS` sample); H3 per-CPU census truncation narrowed the co-tenancy claim and disclosed the preserved
v1 CPU-summary parse artifact; H4 prepared-data copy/`AR_DATA` wording corrected (no staging copy / no MLGym
copy; `prepare_data.py` writes the prepared `houseprice.csv` from the `--from-file` source); H5 static-test
command/mask reconciled in the new `prep/static_command_note.txt`; H6 executed-unit R2 residues vs the C1–C4
claim recorded (launch/result records are the operative form; unit bytes unchanged); H7 cpuset-selection window
and mid-sample wording corrected to the captured samples; H8 v1 verifier source/patch residual recorded in the
new `scripts/README.txt`; H9 `s002` bare `NaN` labelled non-finite/not-used; H10 corrected PASS status
restated as authoritative; S1 record-identity section added; S2 no-resume + filesystem (`/dev/md0p3` on `/`);
S3 full 64-hex authority shas; S4 "preserved unaltered" + live/Mac split; S5 "verifier records both" corrected
and the 2.9 G data-root figure sourced (live `du -sh`). The new record/`SHA256SUMS` shas and the full changed-file
list are in `docs/r1/reports/trackg_g0_20261117/U2_ISO_HOUSEPRICE_RECORD_CORRECTIONS_20261120.md`; the superseded
original values were record sha `c043f0dd3bdf3337df6ca25b7cab075dbd92b4c59b6fec3e0d8f5d390369e178` and
`SHA256SUMS` sha `80a835243830471f3df406478455652cf286c93e991daed5b7b765b826cae84c`.
