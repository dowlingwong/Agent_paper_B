# Track G G.0 U2 isolated-node raw cost — node `mlgym_breakout_minatar` (isolated kit, JAX) — RESULT (19 November 2026)

**Status: PASSED — `CHECKLIST_E_PASSED mlgym_breakout_minatar`; one node only, one smoke, no retry.**
Authority: `R1-TRACKG-G0-GO` (one node per unit, independently reviewed), `R1-HARNESS-ISOLATION`,
`R1-TRACKG-PORT-DECISIONS` (node timeout = 3 × measured B1; a timeout is the proposal's failure, not an
infrastructure retry), `R1-TRACKG-LICENCES`, port report `docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md`
§2/§7, and the accepted kit update `docs/r1/reports/trackg_g0_20261117/TRACKG_ISO_KIT_UPDATE_20261119.md`
(sha256 `fe232e2bbf236337e208f11e97c809f8a41d7ef101567eeb0d11153bacb9d026`) with its review
`docs/r1/reviews/TRACKG_ISO_KIT_UPDATE_REVIEW_20261119.md` (sha256
`d8c68f9f0463d1aa3e17f82527dfb7ecf7b6070831584cd1024a6d39ed6a21b4`, ACCEPTED). Unit
`docs/r1/proposals/u2_iso_20261119/U2_ISO_MLGYM_BREAKOUT_UNIT_20261119.md`, **executed amended bytes sha256
`1b53c3abc4d70b0e31840ecb18b3a4234df8a58e230d3872b6e1f29f8294604e`**, accepted by review
`docs/r1/reviews/TRACKG_U2_ISO_BREAKOUT_UNIT_REVIEW_20261119.md` (sha256
`217822fe8385a3ee29f91ddf4f286b0cb890c4c17704fe10892ef7f47035bfa9`; **ACCEPTED — 0 BLOCKING, 0 MAJOR,
14 MINOR, conditions C1–C7**). The JAX environment fix record
`docs/r1/reports/trackg_g0_20261117/JAX_ENV_FIX_20261119.md` (sha256
`ad2d139a9b891ebdfedb89ef6056f8aac7491a73d965c2aa6ed74cd9afc1f391`) is cited per condition C2, and the
post-fix JAX environment is used — **not** `envs/torch312`. This result was corrected per the accepted
result-review conditions R1–R7/S1–S7 of
`docs/r1/reviews/TRACKG_U2_ISO_BREAKOUT_RESULT_REVIEW_20261119.md` (sha256
`d4cdd9bbd53fd7fceefbca5f41314006b8c824d948e82d56bfadf5818f272ead`, MINOR-only; see Correction note).
ENGINEERING_ONLY; **not evidence**; no noise
floor/D21/D28; no T1 label; no cross-node pooling; no TASL-7/TASL-2, no HTCondor/deepthought, no other host;
no deletion; no push/commit; read-only on Mac records (only this new result directory is written).

**Kit / host / data / licence.**

- Suite **MLGym**, node `mlgym_breakout_minatar` (`rlBreakoutMinAtar`); kit worktree
  `/home/dowling/r1_trackg_20261117/harness_iso_mlgym`, branch `mac-trackg-iso-mlgym-20261117`,
  **tip `f07875de79a5a57739227b13e0fd52d31646edaf`**; launch check `git rev-parse HEAD` = tip and
  `git status --porcelain --untracked-files=no` empty (only the two expected untracked runtime `data`
  symlinks from the earlier MLGym torch nodes) (`kit.txt`).
- Node spec `third_party/mlgym/configs/trackg/nodes/mlgym_breakout_minatar.yaml` sha256
  `b3cedcd6bbb0f306eb6a536037fafbd8e8a374e42f0d30b7b2e104a2ea539f1c`; representative-edit manifest sha256
  `a7fe205a28ee5b3fdc6c6b847ebe6745b3b8dbc4b3260fd72080bb87bf487812`; `LICENCES.md` sha256
  `9767de116925fcf410d789c555344a92a38d838176a34943be65bc6dc27be9bc`; `requirements_gpu.txt` sha256
  `725a25f231f981725b88a699b4962aea9d1f5802a034c1b87f674844aefcae40` (pins `jax[cuda12]==0.4.35`);
  `ar_isolated.py` sha256 `37d99ab0…` (fixed master).
- Host Ada `ucrtasl`, Ubuntu 22.04.5, kernel `5.15.0-151-generic`, 96 CPUs, 503 GiB RAM, driver
  **545.23.08** (NVRM 545.23.08), boot id `5c90a8fe-5f9b-4914-a2c7-5b864e0a8b8d` (`host.txt`).
- **Data: none.** Node `setup_command` is `''` and `external_benchmark.data` is
  `none (simulated environment gymnax Breakout-MinAtar)` (`data_manifest.txt`; node spec §data-prep
  `TRACKG_U2_DATA_PREP_20261117.md` — the kit-update report's stale "MinAtar data" wording is superseded);
  no `data/` link exists in the node directory, no tree under `$AR_TRACKG_DATA_ROOT`, **no dataset download**,
  no synthetic marker applies (no data manifest).
- **JAX environment** `/home/dowling/r1_trackg_20261117/envs/jax312`: Python **3.12.16**, `jax` **0.4.35**,
  `jaxlib` **0.4.34**, `jax-cuda12-plugin`/`jax-cuda12-pjrt` **0.4.35**, `nvidia-cuda-nvcc-cu12` **absent**
  (fix record), `jax.devices()` = **8 GPU devices** (CudaDevice 0–7) without the CUDA mask, `pytest` 9.2.0.
  - **Freeze-method reconciliation:** the fix record's `d33c9612…` is the sha256 of the **sorted**
    `uv pip freeze` output (the pre-pytest 65-line freeze; raw uv order `859b9ff0…`); the pre-add check
    reproduced `d33c9612…` exactly.
  - **Test-only dependency (review condition C3 path):** `envs/jax312` lacked `pytest`, so the pre-launch
    `smoke_entry` dry-run failed. Added offline exactly `pytest==9.2.0` + `iniconfig==2.3.1` + `pluggy==1.7.0`
    (freeze diff is exactly those three lines; before 65 lines sha(raw) `859b9ff0…`/sha(sorted) `d33c9612…`;
    **launch freeze 68 lines sha(raw) `956d0b4fcf28e48451ae4b92a451a2c2db764805378ffbcd6b01a2649caf8d0a`,
    sha(sorted) `80a455c6f46042aa245356050f965a303cf1e1e85f125acc9d6cbde7c08dcac1`**); `jax` versions and
    8-device import re-verified after the add. Evidence: `prechecks_jax_env/` (`env_before`, `env_after`,
    `freeze_before/after`, `freeze_diff.txt`, `pytest_install.log`).
  - **Reconciliation of the executed unit's precheck STOP text (R1).** The executed unit (75 lines, unchanged in
    this correction pass, preserved byte-identically at `references/U2_ISO_MLGYM_BREAKOUT_UNIT_20261119.md`,
    sha256 `1b53c3ab…`) still says the launch freeze sha "equals the fix record's `d33c9612…`" and that
    "pytest is available in the env or record its absence as a STOP" (`unit:34-37`), and lists "JAX
    import/device failure" as a STOP (`unit:67-69`). That text is **superseded by the accepted M-4/C3
    test-only-add path**, and the run did **not** literally meet the unit's old precheck STOP text: the pre-add
    65-line **sorted** freeze is exactly `d33c9612…` (raw `859b9ff0…`), the first `smoke_entry` dry-run failed
    **because pytest was absent** (`prechecks_jax_env/env_before.txt`), and after an offline install of
    **exactly** `pytest==9.2.0` + `iniconfig==2.3.1` + `pluggy==1.7.0` (`pytest_install.log`; `freeze_diff.txt`
    is exactly those three additions) the **launch 68-line sorted freeze is `80a455c6…`** (raw `956d0b4f…`).
    JAX versions (`jax 0.4.35`, `jaxlib 0.4.34`, jax-cuda12 plugin/pjrt `0.4.35`), the 8 devices and the
    absent `nvidia-cuda-nvcc-cu12` are **unchanged** (`env_before`/`env_after` at 04:54:25/04:54:29Z); the live
    env today still freezes to `80a455c6…`/68 lines (re-verified read-only, no GPU initialisation). The add is
    **test-only** — pytest is not imported by the training/evaluation path (`requirements.txt`/
    `requirements_gpu.txt` unchanged) — so the measurement is non-material; no smoke re-run occurred. Since this
    correction pass is record-only (no unit edit permitted), the reconciliation is recorded here, not by
    amending the executed unit bytes.
  - **JAX-fix captures (R7).** The committed fix record `references/JAX_ENV_FIX_20261119.md`
    (sha `ad2d139a…`) carried no captures and did not cite them; the captures are cited in the companion note
    `references/JAX_ENV_FIX_EVIDENCE_COMPANION_20261119.md` added by this correction pass. It points at
    `prechecks_jax_env/` (raw/sorted pre-add and launch freezes, freeze diff, offline install log, env
    before/after) with their full shas, states the live re-verification, and records the residual that the
    exact `uv remove` command/output was not captured. No environment change was made.
- **Licence / provenance.** MLGym task `rlBreakoutMinAtar` is **CC BY-NC 4.0** (non-commercial; attribution and
  changes recorded in the node's `LICENCES.md`, sha `9767de11…`) under `R1-TRACKG-LICENCES` (port decision (1),
  port report §3(1)); the PPO/evaluation code adapted from **gymnax/gymnax-blines carries its Apache-2.0
  notice** and this node **uses** those parts (unlike the five torch nodes); no external dataset is downloaded
  (simulated gymnax Breakout-MinAtar). The census funnel/appendix must carry this licence/provenance line.

**Pins (both, separately; no interchange).**

- **Committed-file `frozen_pin_sha256`** (accepted kit update §3/§10.2 convention; `pins/new_mlgym.json` sha256
  `8974359b…`): **`cec562e64eae30c0bed9e492c391beeda449ad6f3154a606620645fc2d6c5fa4`** (18 frozen entries; this
  is the census value).
- **Deployed run-record pin** (every run record's `frozen_pin_sha256`, constant across all nine records):
  **`cec562e64eae30c0bed9e492c391beeda449ad6f3154a606620645fc2d6c5fa4`** — **equal to the committed pin**, as
  expected for this no-data node (`setup_command` empty, so no `data` symlink is hashed). Note: the accepted
  kit-update capture `pins/deployed_mlgym.json` (sha `dcfcb080…`) predates this node and has no
  `mlgym_breakout_minatar` entry; the pin above is read from this run's records (`pins.txt` correction note).

**Record identity and preserved bytes (S1/S7).** This result file is
`docs/r1/reports/trackg_g0_20261117/u2_iso_mlgym_breakout_minatar_20261119T045751Z/U2_ISO_MLGYM_BREAKOUT_MINATAR_RESULT_20261119.md`;
its own post-correction sha256 is the `./U2_ISO_MLGYM_BREAKOUT_MINATAR_RESULT_20261119.md` entry in this
directory's regenerated `SHA256SUMS`, and the post-correction `SHA256SUMS` sha256, the new record sha and the
changed-file list are recorded in `docs/r1/reports/trackg_g0_20261117/U2_ISO_BREAKOUT_RECORD_CORRECTIONS_20261119.md`.
Node spec: raw `third_party/mlgym/configs/trackg/nodes/mlgym_breakout_minatar.yaml` sha256
`b3cedcd6bbb0f306eb6a536037fafbd8e8a374e42f0d30b7b2e104a2ea539f1c`, canonical `node_spec_sha256` (kit loader:
`sha256(json.dumps(payload, sort_keys=True, separators=(",",":"), ensure_ascii=False, default=str))`)
**`db57b202301e323d4471cf23ef6ad3b822d5f5e0d471f1896ffda3041af2a10a`** (= every run record's value; recomputed
with the kit's own loader on live Ada, read-only). Representative-edit manifest sha256
`a7fe205a28ee5b3fdc6c6b847ebe6745b3b8dbc4b3260fd72080bb87bf487812`; representative-edit diff shas:
E1 `8403016b15959aa480e2f0dd1732b81899f009b452bd1bc9e723e44cd79c22bf`,
E2 `e9932b594c9aa78013f5cf248456a6bb760e9e334486f6ccdfafa56f7640b48e`,
E3 `ec73a85a98c0690191e22be3cca97106c7daca51ba773ae484f696c01fb9f918`,
E4 `089624e9af453e56c3f075c8e50ae1a9bca8ee9e9a5eed6d017d1319c6c20cba`. Executed unit bytes are preserved
at `references/U2_ISO_MLGYM_BREAKOUT_UNIT_20261119.md` (sha256 `1b53c3ab…` = the committed/executed unit), with
its accepted review `references/TRACKG_U2_ISO_BREAKOUT_UNIT_REVIEW_20261119.md` (`217822fe…`) and the JAX fix
record `references/JAX_ENV_FIX_20261119.md` (`ad2d139a…`) byte-identical to the committed files. Preserved
campaign script bytes (`scripts/`): `run_node_jax.sh` sha256 `4b5113fe310ac2438b59889d7d71cc2a910ec7d8a1b31e842115d8295a9a1997`,
`verify_u2_records_jax.py` sha256 `8822495f0007de346a6e1aa505003de6b112b8022bf681e01cea933bcbd4e100`,
`compute_sampler_max.py` sha256 `7d9f472ec1e24ba879f2edd0fa259612f0c00133abf90309587a43ced312dbed` (all three
byte-identical to the live campaign sources; see `scripts/README.txt`). The smoke log carries **one JSON record
line per run** (`verify_full.json` `smoke.json_run_lines: 9`, smoke log sha `19678567…`), and every executed
record has `process.killed_with: null`, `timed_out: false`, `returncode 0` except the deliberately divergent
`s002` (see Isolation below).

**C1–C5 unit-vs-launch-notes split (S7).** The pre-execution conditions C1–C5 were to be applied to the
unit/launch notes. The executed unit text was **not amended** in this record-only correction pass (its bytes stay
`1b53c3ab…`), so this record states explicitly that the **launch notes/captures are the operative form** and
records which C-items they implement: **C1** licence/provenance line (this record + `LICENCES.md`); **C2** JAX
fix record cited (§JAX environment, + R7 companion captures); **C3** fresh JAX/device/freeze/smoke-entry checks,
test-only add, one-line command and probe bytes (`prechecks_jax.txt`, `prechecks_jax_env/`,
`invocation_inner.sh`, `cgroup_probe.txt`), with the R1 reconciliation above; **C4** tracked-clean + HEAD==tip
(`kit.txt`), pin equality/no-data expectation (`pins.txt`), data-prep citation (`data_manifest.txt`), exact gate
command/capture (`gate/`); **C5** provisional-vs-derived timeout, floor basis/contamination/no-switch,
no-push/no-other-host/no-resume and the extra STOPs (this record + `logs/run_node.log`; see S3/S4 below). None of
these changes the executed unit bytes or the measurement.

**Paper A gate (captured immediately before launch; three-check).**

- Gate JSON `gate/gate_20261119T045751Z.json` sha256
  **`a7c67f4bd9c75a78d165e71793164c5f29d38ab0aa5a1a98b6bbc1a43d5545f9`** (UTC `2026-11-19T04:57:57Z`;
  script rc 0; config `r1/scripts/configs/paper_a_status_ada.json`).
- **Three-check PASS**: `verdict: clear_finished`, `paper_a_live_waiting_for_card: false`,
  `paper_a_processes: []`, `unidentified_apps: 0`; newest v4 `live_*` == configured run dir; self-excluded
  `pgrep` for `port_smoke_gpu` empty; `pgrep agent-checkpoint-intervention` empty (`gate/gate_check.txt`).
- **Attempt-1 pre-launch STOP (no smoke launched):** at `04:56:46Z` the gate returned `verdict: unknown`
  (`unidentified_apps: 1`, a transient unidentifiable GPU compute app, not ours), so the runner refused to
  launch; **no `port_smoke_gpu` process was started** (no unit smoke consumed). Evidence preserved as
  `attempt1_prelaunch_gate_stop/` (gate JSON sha `90418169…`, `DONE_PRELAUNCH_STOP`). The single executed
  smoke is attempt 2; **timestamps corrected (R3):** `04:57:51Z` is the runner/evidence-dir start (from
  `launch_mlgym_breakout_minatar_attempt2.log` `start=2026-11-19T04:57:51Z`; the same instant as `env.txt` and
  `host.txt`), the **gate JSON `utc` is `04:57:57Z`** (also `gate_check.txt` capture time), the whole-smoke
  sampler started at `04:57:57Z` with first timestamped row `04:57:58.072Z`, the **inside-scope cgroup/probe
  capture is `04:57:59Z`**, and the scope/smoke followed it. So attempt 2 was *launched/prepared* at `04:57:51Z`
  with the gate `04:57:57Z` and the probe `04:57:59Z`, all immediately before the smoke — not a single
  "launched at 04:57:51Z" claim.

**GPU gate / co-tenancy (idle card only).**

- Selected **card 6, UUID `GPU-3b36edea-1a09-a37e-aa42-8277c7319e77`**: 48,427 MiB free of 49,140 MiB, **0 %
  utilization, no other user's compute app** immediately before launch and back to **5 MiB / 0 %** after
  (`gpu/gpu_qualify.txt`, `gpu/gpu_before.txt`, `gpu/gpu_after.txt`); floor = ≥ 8,192 MiB free.
- **Floor basis / co-tenancy rule (S3).** The 8 GiB requirement is a conservative floor: the accepted kit update
  measured a **~2.85 GB (2,853 MiB)** per-run torch GPU peak under the 8 GiB cap (§6), and the prior accepted
  run-1 floor was **24 GiB** (`TRACKG_U2_RAWCOST_REVIEW_R2_20261117.md`); the chosen card had 48,427 MiB free
  (this JAX node's measured whole-smoke bound is 634 MiB). Mid-run contamination rule: a free-VRAM drop below
  the baseline peak + 2 GiB, or a new co-tenant on the used card, is a STOP/recorded; **no card switch from the
  launch card** occurred — the selected UUID `GPU-3b36edea-…` is the only card in `gpu_qualify`/`gpu_before`/
  the precheck-window mid snapshot/`gpu_after` and in every run record.
- Whole-smoke sampler: exact command
  `nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv -l 1` (interval **1 s**), started
  before the `systemd-run` scope and stopped after it; output `sampler/sampler_required.csv` (sha256
  `4bfbc709…`, 5,060 app rows) plus a concurrent timestamped companion used only to group rows into
  per-sample sums (`sampler/sampler_timestamped.csv` sha256 `8575f908…`); 473.9 s sampled, 429 samples carried
  the used card. **Pids corrected (R6):** the sampler saw **10 processes of this run scope**, not 10 worker
  pids — **2 are transient `jax.devices()` precheck clients** (pids `245960` at `04:58:01–04:58:03Z` and
  `246999` at `04:58:06–04:58:07Z`, each reaching 426 MiB once its all-8-card client initialised; the
  **pre-scope** `env.txt` no-mask call at `04:57:51Z` exited before the sampler started and is therefore **not**
  in this list) and the other **8 are the run workers** (pids `247898, 265499, 269241, 278721, 290683, 300852,
  311394, 321566`); the 634 MiB maximum is worker pid `300852` at `05:03:50.8Z`, and the whole-smoke bound covers
  all of them.
- **Peak reported as a whole-smoke upper bound = 634 MiB** (max single-row `used_memory` 634 MiB = max
  per-sample sum 634 MiB on the used card; CSV header not counted). **Label: whole-smoke upper bound over the
  used GPU, including any co-tenant by construction; NOT a per-run peak and NOT attributed to the baseline
  process tree.** The bound also covers the in-scope precheck window (transient ~439 MiB per card when
  `jax.devices()` initialized a client on all 8 devices) as well as the smoke worker.
- **Mid-run census (deviation, recorded):** the dedicated watcher snapshot fired during the inside-scope
  prechecks (the `jax.devices()` allocation on the used card exceeded the trigger), so it is **not** a
  mid-smoke snapshot; it is preserved as `gpu/gpu_mid_precheck_window.txt`. The **mid-smoke census is derived
  from the whole-smoke 1 s timestamped sampler** at the median sample carrying the card:
  `gpu/gpu_mid_smoke_derived.txt` — pid 290683, **432 MiB** used, derived free ≈ 48,708 MiB; mid-smoke
  utilization % is not available (before/after utilization recorded). No other user's app ever appeared on the
  card; every compute-app row on the card was one of this smoke's own worker pids.
- **All-8-card `jax.devices()` initialisation, disclosed (R5).** The required **no-CUDA-mask** `jax.devices()`
  prechecks initialised a JAX client on **all 8 cards** (no `CUDA_VISIBLE_DEVICES` mask): (i) the JAX-fix
  prechecks at `04:54:25Z`/`04:54:29Z` (`prechecks_jax_env/env_before.txt`, `env_after.txt`; two no-mask
  `jax.devices()` calls), (ii) the **pre-scope `env.txt` capture at `04:57:51Z`**
  (`jax_devices_no_mask=8 gpu`; before the whole-smoke sampler started at `04:57:57Z`, so **outside** the sampler
  bound), and (iii) the **inside-scope precheck at `04:57:59Z`**, caught by the mid watcher at `04:58:06Z` as
  pid `246999` with **426 MiB app / 439 MiB used on each of the 8 cards** (`gpu/gpu_mid_precheck_window.txt`).
  This is **minimal JAX-client initialisation** (a few seconds, no GPU compute launched and no other process
  signalled/touched); the smoke itself ran only on card 6, which returned to 5 MiB / 0 %. The earlier report
  wording "no other user's GPU process/card was disturbed" is therefore narrowed: **no process was touched, but
  the required no-mask device probes did transiently allocate a JAX client on all 8 cards** (other cards'
  concurrent usage is other users' own jobs, unchanged by those probes).

**Run (unit command shape, exactly one smoke).**

- Inside `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c '…'`
  (logged unit `run-r9112b3003b284fe0a9e0ed8ffa9b8200.scope`; the launch command is one physical line):
  `cd harness_iso_mlgym`, `CG=$(cut -d: -f3 /proc/self/cgroup)`,
  `AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG`, `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1`,
  `PATH=…/envs/jax312/bin:$PATH`, `VIRTUAL_ENV=…/envs/jax312`, **no `AR_TRACKG_DATA_ROOT`** (no data),
  taskset `8-15`, `python -m tests.trackg.port_smoke_gpu --node mlgym_breakout_minatar --gpu-uuid … --cpus
  8-15 --memory-limit "external: systemd-run --user --scope -p MemoryMax=8G -p MemorySwapMax=0 (enforced
  cgroup)" --runs-root <outside repo>/runs --provisional-timeout 1800`. Resolved invocation
  `invocation_inner.sh` sha256 `4b166ce0899f9df72104e85a4466b9d6558bfea09259c97b9ef00171dad5eb86`.
- **Inside-scope prechecks before the smoke** (`prechecks_jax.txt` sha256 `72f15f10…`): `which python` =
  `…/envs/jax312/bin/python`, Python 3.12.16; `jax.devices()` **8 GPU** without the mask; `nvidia-cuda-nvcc-cu12`
  absent; `pytest 9.2.0`; live launch freeze 68 lines sha(sorted) `80a455c6…` == pre-registered expected;
  `smoke_entry` printed the node entry; `import tests.trackg.test_port_mlgym` OK. All four preconditions passed
  (device count 8, freeze equal, entry found) — a mismatch was a STOP.
- **Cgroup enforcement probe (read inside the scope, from the echoed path)**: `scope_cgroup=…/run-r9112b300…
  scope`, **`memory.max=8589934592`**, **`memory.swap.max=0`** (expected bytes; a different value was a STOP);
  `CUDA_VISIBLE_DEVICES` before the smoke `<unset>` (`cgroup_probe.txt` sha256 `b0942137…`).
- **rc 0; `CHECKLIST_E_PASSED mlgym_breakout_minatar`; `SMOKE_EXIT=0`; `systemd_run_rc=0`** (smoke stdout
  `smoke_stdout_extract.txt` sha256 `d8e00b7f…`; log `logs/run_node.log` sha256 `19678567…`).
- **`time -v` for the whole smoke (aggregate, not a per-run peak)**: user **500.69 s**, system **109.46 s**,
  wall **7:44.38**, max RSS **1,262,488 kB** (`time_v.txt` sha256 `8fb82c44…`), exit status 0.
- Timeout: provisional 1800 s; **node timeout = 3 × measured B1 = 183.744 s**; no timeout and no OOM; no retry.
  **No resume (S4, R3 mR10 class):** an interrupted unit re-runs wholly from a new `<runs-root>`; no resume
  occurred here.
- `--runs-root` outside the repository: this capture's `runs/` (19 M).

**Result — B1/B2 and every edit outcome.** `outcome.value` is the node's validation metric `val_return`
(`AR_METRIC val_return=`); the sealed value is `sealed.test_return` from the run's result channel
(`AR_TEST test_return=`, **not** the manager view).

| run | kind | executed | `val_return` (outcome.value) | `elapsed_seconds_info_only` | sealed `test_return` |
|---|---|---|---|---|---|
| `s000_baseline` **B1** | baseline | true | **22.486719** | **61.248 s** | **22.885938** |
| `s001` | frozen-diff refused (`scope_violation`) | **false** | — (null) | — | — |
| `s002` | broken diff `divergent/non_finite_loss` | true | — (null) | 40.818 s | null |
| `s003` | first declared edit (kept in the record; selection discarded it: 18.74 < baseline) | true | 18.742188 | 62.848 s | 18.716406 |
| `E1` | declared edit | true | 18.742188 | 58.856 s | 18.716406 |
| `E2` | declared edit | true | 16.975781 | 61.065 s | 17.364062 |
| `E3` | declared edit | true | 6.934375 | 58.362 s | 6.940625 |
| `E4` | declared edit | true | 24.753125 | 58.069 s | 24.896875 |
| `B2` | repeat baseline | true | **22.486719** | **61.781 s** | **22.885938** |

- 9 `run_record.json`, **8 executed + the refused frozen diff (`s001` `executed:false`)**; `B2` reproduces
  `B1` exactly (val_return 22.486719 / sealed test_return 22.885938). Baseline record
  `runs/runs_smoke/s000_baseline/run_record.json` sha256
  **`7d1072c7656ea55bc999d158102c79f2a84da5db6afc75d05971aac8edb7513d`** (run.log sha256
  `b71466dffb4ea1f0cf856ead18138060d1a78fc48b4fc95d75bd0e3af67d7155`, result-channel sha256
  `20ddf2fd9a2aa921f97bf75d5cd38b08c9fb9a81598fda993201b3b02dab33be`; B2 record sha
  `687cc9ed4e05ec7a91485165e90915b99f64b13829b54397b4cab2012c703258`). All per-run record/log/result-channel
  hashes: `record_hashes.txt`.
- No accepted pre-run reference exists (the kit update's Breakout smoke was not run because the JAX env was
  broken); this unit is the first measurement, so B1/B2 above are the record.

**Isolation record gate (every executed record).**

- Every executed record: `isolation.effective: true`, `isolation.waivers {}`, `isolation.exceptions []`,
  `log_intact: true`, result channel present (`result_channel_overflow: false`, `result_channel_sha256`),
  cgroup kill `method: cgroup.kill` with `empty_after: true` and `removed: true`, frozen files checked 18,
  `determinism.not_forced` = `['cudnn.benchmark=False','dataloader_workers','torch.set_num_threads',
  'torch.use_deterministic_algorithms(True)']` with the three torch settings carrying
  `torch_absent: ModuleNotFoundError` reasons and `dataloader_workers` its usual advertised-only reason,
  `determinism.shim_loaded: true`; `process.killed_with` **null**, `process.timed_out` false, ok runs
  `returncode 0`; `limits.external_limit` exactly the one-line unit string, `gpu_uuids`
  `[GPU-3b36edea-…]`, `cpu_list [8..15]`, `memory_method: external`, provisional timeout 1800 s, timeout
  factor 3.0; `node_spec_sha256` present; `s001` `executed:false`/`outcome:null`/`scope_violation` (by design).
- **Divergent `s002` process fields, stated explicitly (R2).** The deliberately broken diff is the one
  exception to "ok runs returncode 0": `s002` has `outcome {kind: divergent, reason: non_finite_loss,
  value: null}`, `elapsed_seconds_info_only 40.818 s`, **`process.returncode: 4`**,
  **`process.leftover_processes_killed: true`** (the runner then cgroup-killed the leftovers:
  `cgroup.kill` `empty_after: true`, `removed: true`; `killed_with: null`, `timed_out: false`), and an empty
  result channel (sha256 `e3b0c44…`, the sha256 of empty input). These are expected for the deliberately
  divergent run and differ from the five torch-node s002 records; the fixed verifier correctly requires
  returncode 0 only for ok runs.
- Verifiers: `scripts/verify_u2_records_jax.py` **rc 0, `ok: true`, 9 records / 8 executed / refused_s001
  true, sealed_key `test_return`, deployed pin == committed pin** (`verify_full.json` sha `d395da41…`,
  `verify_full.summary.txt`); accepted kit helper `verify_records.py` **rc 0, issues []**
  (`verify_records.json`); `collect_smoke_summary.py` **rc 0, gate_ok true, issues []** (`summary.json`).
- **Deviation (verifier false negative, not a smoke failure):** the first verifier run flagged the JAX
  `determinism.not_forced` (it wrongly required every setting reason to be `torch_absent`) and the deliberately
  divergent `s002` returncode; the smoke itself passed. The verifier was fixed and re-run on the same records
  (no smoke re-run); original outputs preserved as `verify_full.v1_verifier_bug.json` /
  `verify_full.summary.v1_verifier_bug.txt`, correction recorded in `RESULT_STATUS.txt`/`DONE`.
  **S2 residual:** unlike the five torch-node results, **no v1 verifier source and no fix patch** were preserved
  (the live verifier was edited in place); only the v1 outputs remain, and their check names are the preserved
  description of the v1 rules. `scripts/README.txt` records this and corrects the earlier "documented fix
  patches" claim; a byte-exact v1 source/patch cannot be reconstructed without guessing.

**Disk / footprint.**

- `df -B1 /` (`/dev/md0p3`, mounted `/`) **before: 75,439,427,584 B available (70.3 GiB); after:
  75,401,625,600 B (70.2 GiB)** — above the 50 GiB STOP floor both before and after. These are the
  `disk_before.txt`/`disk_after.txt` values (captured `04:57:56Z`/`05:05:53Z`); the runner's
  `RESULT_STATUS.txt` `disk_avail_before/after_bytes` (`75,439,415,296` / `75,401,555,968`) are a second `df`
  sample at a slightly different instant and are **not** the cited source (R4: one consistent source). Post-run
  footprint: evidence 19 M, runs tree 19 M, data root 2.9 G (`disk_after.txt`, `runs_du.txt`); nothing deleted,
  no push, no commit.

**Deviations (all recorded; no smoke re-run).**

1. **Attempt-1 pre-launch gate STOP** (`04:56:46Z`): gate `unknown` because a transient GPU compute app could
   not be identified (`unidentified_apps: 1`); no smoke launched. The single executed smoke is attempt 2 after
   the gate cleared (`attempt1_prelaunch_gate_stop/`).
2. **Test-only pytest added to `envs/jax312`** per review condition C3 (missing pytest made `smoke_entry`
   fail): exactly `pytest==9.2.0`, `iniconfig==2.3.1`, `pluggy==1.7.0`; pre-add freeze matched the fix
   record (`d33c9612…`, sorted convention); launch freeze 68 lines `80a455c6…` recorded; JAX import/8 devices
   re-verified (`prechecks_jax_env/`).
3. **Mid-run census:** the dedicated watcher snapshot is from the precheck window (JAX 8-device init), not
   mid-smoke; the mid-smoke census is derived from the 1 s sampler (`gpu/gpu_mid_smoke_derived.txt`), mid-smoke
   utilization not captured (before/after 0 % recorded).
4. **Pins capture:** `pins/deployed_mlgym.json` predates this node (no entry); deployed pin read from the run
   records and equals the committed pin, as expected for this no-data node.
5. **First verifier false negative** on the JAX-specific determinism/divergent fields; fixed and re-run on the
   same records (original preserved).
6. **All-card `jax.devices()` initialisation (R5, reworded).** The required no-CUDA-mask `jax.devices()`
   checks initialised a JAX client on **all 8 devices**: the JAX-fix prechecks at `04:54:25Z`/`04:54:29Z`
   (two no-mask calls), the **pre-scope `env.txt` capture at `04:57:51Z`** (outside the whole-smoke sampler,
   which started at `04:57:57Z`), and the inside-scope precheck at `04:57:59Z` (visible at `04:58:06Z` as
   pid `246999`, ~426 MiB app / 439 MiB used per card in `gpu/gpu_mid_precheck_window.txt`). This is minimal
   JAX-client initialisation (seconds; no GPU compute, no other process touched); only card 6 was used for the
   smoke and it returned to 5 MiB / 0 %. No other user's process/card was disturbed — but the transient
   all-8-card allocation is disclosed rather than hidden behind "no other card used".

**Scope statements.** One node only (`mlgym_breakout_minatar`); this is the first measurement of this node (no
accepted pre-run baseline); this result is not evidence, has no noise floor / D21 / D28, no T1 label, no
U3/unisolated claim, and is not pooled with any other node. No other user's GPU process/card was touched or
signalled; the required no-CUDA-mask `jax.devices()` probes did transiently allocate a JAX client on all 8 cards
(~426 MiB per card for seconds; disclosed in the GPU section and Deviation 6), while the smoke used only card 6
and did not run on or disturb any other card; no
authors' other experiments were run; no autoresearch (C3-blocked), HousePrice (STOP) or other node was
executed. One smoke only; no retry.

**Evidence index (this directory).** `SHA256SUMS` (every capture below; regenerated after these record
corrections and verified `shasum -a 256 -c` **rc 0, 1,117/1,117 entries OK**).
`logs/run_node.log` (outer log with gate/scope/prechecks/smoke stdout/CHECKLIST), `smoke_stdout_extract.txt`,
`cgroup_probe.txt`, `prechecks_jax.txt`, `precheck_freeze_live_sorted.txt`, `time_v.txt`,
`invocation_inner.sh`, `gate/`, `gpu/` (`gpu_qualify`, `gpu_before`, `gpu_mid` [precheck window],
`gpu_mid_precheck_window`, `gpu_mid_smoke_derived`, `gpu_after`), `sampler/` (required + timestamped CSV,
`sampler_max.json`), `host.txt`, `env.txt`, `env_freeze.txt`/`env_freeze_sorted.txt`, `data_manifest.txt`,
`kit.txt`, `pins.txt`, `disk_before.txt`, `disk_after.txt`, `runs_du.txt`, `record_hashes.txt`,
`summary.json`, `verify_records.json`, `verify_full.json` (+ preserved v1), `RESULT_STATUS.txt`, `DONE`,
`prechecks_jax_env/` (pre-install/post-install env, freeze before/after, freeze diff, pytest install log),
`attempt1_prelaunch_gate_stop/` (gate JSON/check, qualify, RESULT_STATUS, DONE),
`references/` (executed amended unit sha `1b53c3ab…`, review sha `217822fe…`, JAX fix record sha
`ad2d139a…`, and the correction-pass companion note `JAX_ENV_FIX_EVIDENCE_COMPANION_20261119.md` that cites the
fix captures — R7), `scripts/` (the exact JAX runner/verifier/sampler-max sources, byte-identical to the live
campaign scripts; plus `scripts/README.txt` recording the sources/shas and correcting the earlier "documented
fix patches" claim — S2), and the nine per-run `runs/…/{run_record.json,run.log,result_channel.txt}` plus the
smoke work trees (19 M). Raw evidence is **preserved unaltered** on Ada under
`/home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlgym_breakout_minatar_20261119T045751Z/` (live dirs
`drwxrwxr-x`, files `-rw-rw-r--`, hash-matching; not filesystem-read-only — S5) — no deletion.

**Correction note (2026-11-19T05:30Z).** This record was corrected per the accepted MINOR-only conditions of
`docs/r1/reviews/TRACKG_U2_ISO_BREAKOUT_RESULT_REVIEW_20261119.md` (sha256 `d4cdd9bb…`; R1–R7 + S1–S7), without
re-running any GPU/U2 work, without editing the unit/code, and without changing any measured number. Changes:
R1 executed-unit precheck STOP text reconciled to the accepted M-4/C3 test-only-pytest path (pre-add 65-line
sorted freeze = `d33c9612…`; launch 68-line sorted = `80a455c6…` = + exactly pytest/iniconfig/pluggy; JAX
versions/devices/nvcc unchanged; no rerun); R2 `s002` `returncode 4` + `leftover_processes_killed true` stated;
R3 timestamps corrected (runner start `04:57:51Z`, gate `04:57:57Z`, probe `04:57:59Z`); R4 disk from
`disk_before/after.txt` (75,439,427,584 / 75,401,625,600 B), not the `RESULT_STATUS` samples; R5 all-8-card
`jax.devices()` allocation and pre-scope `env.txt` call disclosed; R6 "10 worker pids" corrected to 2 precheck
clients + 8 run workers; R7 JAX-fix captures cited via the new companion note; S1 record identity/distinct shas
added; S2 `scripts/README.txt` + corrected scripts claim (v1 verifier source/patch not preserved — residual);
S3 8 GiB floor basis/contamination rule/no-switch; S4 no-resume + filesystem; S5 "preserved unaltered"; S6 full
authority/kit-review shas; S7 C1–C5 unit-vs-launch-notes split recorded (executed unit bytes unchanged). The
post-correction record sha256 and `SHA256SUMS` sha256, the changed-file list and the verification results are in
`docs/r1/reports/trackg_g0_20261117/U2_ISO_BREAKOUT_RECORD_CORRECTIONS_20261119.md`; the superseded original
had record sha `532513e7…` and `SHA256SUMS` sha `e55aa282…`.
