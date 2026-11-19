# Independent review — Track G G.0 U2 result `mlgym_breakout_minatar` (isolated kit, JAX) (19 November 2026)

**Reviewer.** Fresh independent reviewer (`u2-breakout-result-reviewer`), delegated after the smoke; no involvement
in the unit, its review, the JAX env fix, the kit update, the five-node campaign or the run. Read-only: the **only
file written is this review** (uncommitted). No new GPU/U2 run, no unit/code/record edit, no deletion, no
commit/push, no HTCondor/deepthought. I logged in to Ada (`ssh -o BatchMode=yes experiment_zhixu`) **read-only** to
compare every capture with the live evidence; I ran no smoke, no GPU device initialisation (`jax.devices()` was
deliberately **not** run — it would allocate a client on the cards), no Ada write.

**Objects under review.**
`docs/r1/reports/trackg_g0_20261117/u2_iso_mlgym_breakout_minatar_20261119T045751Z/` (result md
`U2_ISO_MLGYM_BREAKOUT_MINATAR_RESULT_20261119.md`, sha256 **`532513e7799044959e70fae758a42a2d347defca2e2ede4eeecc990fa1a10323`**,
230 lines; `SHA256SUMS` sha256 **`e55aa2827a0e9096b02656adb369440f7f6adeb19296a663ba18297f29ff29ad`**, **1,115 entries**,
1,116 files total incl. `SHA256SUMS`), the live Ada evidence under
`/home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlgym_breakout_minatar_20261119T045751Z/`, the executed unit
`U2_ISO_MLGYM_BREAKOUT_UNIT_20261119.md` (sha256 **`1b53c3abc4d70b0e31840ecb18b3a4234df8a58e230d3872b6e1f29f8294604e`**,
75 lines), its review `docs/r1/reviews/TRACKG_U2_ISO_BREAKOUT_UNIT_REVIEW_20261119.md` (sha256
**`217822fe8385a3ee29f91ddf4f286b0cb890c4c17704fe10892ef7f47035bfa9`**, ACCEPTED, conditions C1–C7), and the JAX fix
record `docs/r1/reports/trackg_g0_20261117/JAX_ENV_FIX_20261119.md` (sha256
**`ad2d139a9b891ebdfedb89ef6056f8aac7491a73d965c2aa6ed74cd9afc1f391`**). Authority: published main
**`de3de54fd22dcdd86215be0924307e36a64ed08b`** (`origin/main`); worktree `ops-tasl-20261116` HEAD
**`af5fa558`** (the unit+review+JAX-fix commit; `de3de54f` is **not** an ancestor; merge-base `45fb94cc`); result dir
untracked. The `R1-TRACKG-G0-GO`/`R1-TRACKG-LICENCES` rows are present at HEAD, and `R1-TRACKG-PORT-DECISIONS`/`R1-HARNESS-ISOLATION`
at `origin/main:docs/r1/PLAN.md:1289/1290` as the unit review cites.

**Verdict summary: ACCEPTED — 0 BLOCKING, 0 MAJOR, 7 result-specific + 7 shared-standard MINOR.** The measurement is
one node, one executed smoke (attempt 1 was a pre-launch gate STOP with **no** smoke), a correct inside-scope cgroup
and JAX-env precheck, a faithful record, and numbers that I recomputed from the records/logs/result channels and from
live Ada: **B1 61.248 s / `val_return` 22.486719 / sealed `test_return` 22.885938; B2 61.781 s identical; derived node
timeout 183.744 s = 3 × B1; 8 executed records + refused `s001`; `CHECKLIST_E_PASSED`; effective isolation on every
executed record; whole-smoke sampler upper bound 634 MiB.** The findings are record-completeness/reconciliation items
of the same class the five-node results were accepted-and-corrected for (S-series in
`TRACKG_U2_ISO_RESULTS_REVIEW_20261119.md` / `U2_ISO_RECORD_CORRECTIONS_20261119.md`), plus three this node needs
because of its JAX/verifier history. **No re-run, second smoke, T1/evidence, cross-node use or additional host is
authorised by this review. Conditions R1–R7/S1–S7 are record corrections applied before the census row or commit.**

## 1. One accepted unit, one smoke, kit, pins, licence, data — PASS

- **Accepted unit / executed bytes.** Unit sha `1b53c3ab…` (75 lines) is committed at `af5fa558`; the pre-execution
  review (`217822fe…`) accepted the 60-line version `433db1bf…` with conditions C1–C7 and explicitly states no further
  review round is needed for the text corrections. The result's `references/U2_ISO_MLGYM_BREAKOUT_UNIT_20261119.md`,
  `references/TRACKG_U2_ISO_BREAKOUT_UNIT_REVIEW_20261119.md` and `references/JAX_ENV_FIX_20261119.md` are
  **byte-identical** to the committed files (shas as above). The result header (`report:3-18`) records both shas.
- **One executed smoke, no retry.** Attempt 1 (`…20261119T045646Z`, `attempt1_prelaunch_gate_stop/`) is a
  **pre-launch gate STOP**: gate JSON sha `90418169…`, `verdict: unknown`, `unidentified_apps: 1`,
  `DONE_PRELAUNCH_STOP 2026-11-19T04:56:52Z` (`attempt1…/gate/gate_check.txt:5,12`,
  `attempt1…/RESULT_STATUS.txt`), and no scope was launched (`attempt1…/runs/` and `attempt1…/sampler/` are empty on
  live Ada). The single executed smoke is attempt 2, launched after a fresh gate (`clear_finished`,
  `unidentified_apps: 0`, gate JSON sha `a7c67f4b…`, `utc 04:57:57Z`).
- **Kit tip / clean.** Live `git -C /home/dowling/r1_trackg_20261117/harness_iso_mlgym rev-parse HEAD` =
  `f07875de79a5a57739227b13e0fd52d31646edaf` (branch `mac-trackg-iso-mlgym-20261117`);
  `git status --porcelain --untracked-files=no` **empty**; untracked = exactly the two expected runtime links
  `third_party/mlgym/nodes/mlgym_cifar10/data` and `…/mlgym_fmnist/data` (`kit.txt:1-9` live-equal). Node spec raw
  sha `b3cedcd6…` and representative-edit manifest `a7fe205a…` are live-equal (`kit.txt:10-16`); I also recomputed
  the canonical `node_spec_sha256` on live Ada with the kit loader formula =
  **`db57b202301e323d4471cf23ef6ad3b822d5f5e0d471f1896ffda3041af2a10a`**, which is exactly the
  `node_spec_sha256` in all nine run records.
- **Both pins, correct convention.** Committed-file pin **`cec562e64eae30c0bed9e492c391beeda449ad6f3154a606620645fc2d6c5fa4`**
  (`pins/new_mlgym.json` sha `8974359b…`, 18 frozen entries): independently recomputed **from the 18 files on the live
  kit** as `sha256(json.dumps(files, sort_keys=True))` = `cec562e6…`, and the 18 file hashes match the pin map exactly;
  live `pins/new_mlgym.json` sha `8974359b…`. Deployed run-record pin = `cec562e6…` in **all nine** records, i.e.
  equal to the committed pin, as expected for a node with `setup_command: ""` (no `data` link hashed); the kit-update
  `pins/deployed_mlgym.json` (sha `dcfcb080…`) predates this node and has no Breakout entry — **disclosed**
  (`report:64-68`, `pins.txt:7-15`, `RESULT_STATUS` note (c)) and the deployed pin is read from the run records
  (which hash the deployed files at run time), so the convention is met without hardcoding.
- **Licence / provenance.** `report:53-57` carries the required line: MLGym `rlBreakoutMinAtar` **CC BY-NC 4.0**
  non-commercial with attribution/changes in `LICENCES.md` (sha `9767de11…`), PPO/evaluation adapted from
  **gymnax/gymnax-blines Apache-2.0** and **used** by this node (unlike the five torch nodes), and no external
  dataset. Live `LICENCES.md` confirms exactly this (CC BY-NC 4.0; gymnax Apache-2.0; simulated `gymnax`
  Breakout-MinAtar); `requirements_gpu.txt` pins `jax[cuda12]==0.4.35`. Node spec `external_benchmark.license:
  CC-BY-NC-4.0` and `data: none (simulated environment gymnax Breakout-MinAtar)`.
- **Data: none.** `setup_command=''`, `data: none`, no in-node `data` link, no `data/<node>` tree, no download
  (`data_manifest.txt:1-10`; `report:34-39`). The kit-update report's stale "MinAtar data" wording is explicitly
  superseded with the data-prep citation (`data_manifest.txt:10`; `report:36-37`).

## 2. JAX environment and C3 prechecks — VERIFIED, with one reconciliation gap

- **Live env.** `/home/dowling/r1_trackg_20261117/envs/jax312`: Python **3.12.16**; `jax` **0.4.35**, `jaxlib`
  **0.4.34**, `jax-cuda12-plugin`/`jax-cuda12-pjrt` **0.4.35**, **pytest 9.2.0**, `nvidia-cuda-nvcc-cu12` **absent**;
  current `uv pip freeze | sort` = **68 lines, sha `80a455c6…`** — i.e. the live environment today is exactly the
  recorded launch freeze. No `envs/torch312` use is recorded; the worker sandbox `ro` list and run argv are the JAX
  env only (`runs/runs_smoke/s000_baseline/run_record.json`).
- **Freeze-method reconciliation — verified, correct.** The pre-add 65-line freeze (`prechecks_jax_env/freeze_before*`,
  captured 04:54:25Z) has raw sha `859b9ff0…` and **sorted** sha **`d33c9612…`** (65 lines), reproducing the JAX fix
  record exactly; the pytest install added exactly **pytest==9.2.0, iniconfig==2.3.1, pluggy==1.7.0**
  (`freeze_diff.txt:1-7`, `pytest_install.log`), giving the launch 68-line freeze raw `956d0b4f…` / sorted
  **`80a455c6…`**. So the fix record's sha is the sorted-convention sha and the result's reconciliation is factually
  right. The later 4 seconds between `env_before` and `env_after` are consistent with the recorded 14 ms offline install.
- **C3 prechecks executed inside the scope, before the smoke** (`prechecks_jax.txt:1-22`; `invocation_inner.sh:27-57`):
  `which python` = `…/envs/jax312/bin/python`, Python 3.12.16; `jax_devices (no CUDA mask)` = **8 GPU** `CudaDevice
  0–7`; nvcc absent; pytest 9.2.0; live freeze 68 lines raw `956d0b4f…`/sorted `80a455c6…` == expected; `smoke_entry`
  printed the node entry; `import tests.trackg.test_port_mlgym` OK. The launch command is **one physical line**
  (`invocation_inner.sh:59`) and the probe read the echoed path: `memory.max=8589934592`, `memory.swap.max=0`
  (`cgroup_probe.txt:1-5`).
- **Gap (R1).** The executed unit's own launch-precheck text still says the freeze sha "equals the fix record's
  `d33c9612…`" and "pytest is available in the env or record its absence as a STOP" (`unit:34-37`), and lists
  "JAX import/device failure" as a STOP (`unit:67-69`). At launch the freeze was `80a455c6` (not `d33c9612`) and the
  first `smoke_entry` dry-run **failed** before the offline pytest add. The action is authorised by the accepted
  review — M-4 says "if a test-only dependency has to be added, record the new 65+-line freeze and say so", and C3
  lists "any test-only dependency added to the env (with the new freeze sha)" — and the result discloses it
  (`report:43-52`, `:177-181`, `:194-197`; `RESULT_STATUS` note (d)). But the executed unit bytes were not reconciled
  to C3, so the run's own precheck STOP text was not literally met. Non-material to the measurement (pytest is not
  imported by the training/evaluation path; JAX versions, plugins, devices and nvcc state were re-verified after the
  add and are live-confirmed), but it must be reconciled in the record (condition R1).

## 3. Isolation, cgroup, gate and GPU — PASS

- **Inside-scope cgroup.** `scope_cgroup=…/run-r9112b3003b284fe0a9e0ed8ffa9b8200.scope`, `memory.max=8589934592`,
  `memory.swap.max=0` read from the echoed path inside the scope (`cgroup_probe.txt:1-5`; systemd scope advertised
  in `logs/run_node.log:3`). Every executed record's `cgroup_parent` is exactly that scope.
- **Every executed record: effective isolation.** All 8 executed records have `isolation.effective: true`,
  `waivers {}`, `exceptions []`, `log_intact: true`, `result_channel_overflow: false` + `result_channel_sha256`,
  `cgroup.kill` with `empty_after: true` and `removed: true`, 18 frozen files checked, `determinism.not_forced` =
  the 4 JAX settings with the three `torch_absent: ModuleNotFoundError` reasons and `dataloader_workers` its
  advertised-only reason, `process.killed_with: null`, `timed_out: false`, ok runs `returncode 0`,
  `limits.external_limit` exactly the one-line unit string, `gpu_uuids [GPU-3b36edea-…]`, `cpu_list [8..15]`,
  `memory_method external`, `provisional_timeout 1800`, `timeout_factor 3.0`;
  `runs/runs_smoke/s001/run_record.json` is `executed:false`, `outcome:null`, refusal `scope_violation` (by design).
  Both accepted helpers also pass: `verify_records.json` (kit helper) `issues: []`; `summary.json` `gate_ok: true`.
- **Divergent `s002` fields (R2).** `s002` is the deliberately broken diff: `outcome {kind: divergent,
  reason: non_finite_loss, value: null}`, `elapsed 40.818 s`, but its `process.returncode` is **4** and
  `leftover_processes_killed` is **true** (the cgroup kill then reports `empty_after: true`). The report says
  "process.killed_with null, process.timed_out false, ok runs returncode 0" (`report:168-169`) and discloses the
  verifier's earlier wrong rc-0 requirement, but does not state s002's rc=4 / leftover=true explicitly. The
  fixed verifier correctly checks rc 0 only for ok runs; this is a recording omission, not a smoke failure.
- **Paper A gate.** JSON sha `a7c67f4b…`, `utc 2026-11-19T04:57:57Z`, `verdict clear_finished`,
  `paper_a_live_waiting_for_card: false`, `paper_a_processes: []`, `unidentified_apps: 0`; newest v4 `live_*` ==
  configured run dir; self-excluded `pgrep port_smoke_gpu` and `agent-checkpoint-intervention` empty
  (`gate/gate_20261119T045751Z.json`, `gate/gate_check.txt:1-12`). The gate precedes the scope/probe
  (`cgroup_probe.txt:13` utc `04:57:59Z`), i.e. captured immediately before launch.
- **GPU.** Card 6 `GPU-3b36edea-1a09-a37e-aa42-8277c7319e77`, 48,427 MiB free of 49,140, 0 %, no other compute app
  (`gpu/gpu_qualify.txt:9,20-25`; `gpu/gpu_before.txt:9`; all nine records), and back to 5 MiB / 0 % with no app
  after (`gpu/gpu_after.txt:9`). 8 GiB floor checked. The 1 s whole-smoke sampler ran before the scope and stopped
  after it (`sampler/sampler_pids.txt`; first/last timestamped rows 04:57:58.072Z–05:05:51.924Z, 473.852 s).
- **Mid census (disclosed deviation).** The dedicated mid watcher fired during the inside-scope `jax.devices()`
  prechecks (`gpu/gpu_mid_precheck_window.txt` = `gpu/gpu_mid.txt`; pid 246999, 426 MiB app / 439 MiB used on all
  8 cards at 04:58:06Z) and is **not** a mid-smoke snapshot. The mid-smoke census is derived from the sampler:
  median sample 214 of 429 carrying the card, pid 290683, 432 MiB at 05:02:01.7Z
  (`gpu/gpu_mid_smoke_derived.txt`; I recomputed the grouping: 470 one-second samples, 429 carrying card 6, median
  = 05:02:01.7Z, 432 MiB — matches). Mid util is explicitly `NOT_CAPTURED_MID_SMOKE`. Labelled correctly; matches
  the accepted five-node precedent (mR9/sampler-derived mid census).
- **Sampler bound.** Required sampler command exactly the unit's (`nvidia-smi --query-compute-apps=gpu_uuid,pid,
  used_memory --format=csv -l 1`), 1 s, output sha `4bfbc709…`; I recomputed from `sampler/sampler_required.csv`:
  **5,060 app rows**, card-6 rows **429**, max single row **634 MiB**, and from the timestamped companion max
  per-sample sum **634 MiB** (worker pid 300852 at 05:03:50.8Z). Label = **whole-smoke upper bound over the used GPU,
  includes co-tenants by construction, NOT a per-run peak / not the baseline process tree**
  (`report:89-99`; `sampler/sampler_max.json:15-34`) — correct and conservative.

## 4. Numbers, captures and live-Ada fidelity — PASS

Numbers recomputed from `runs/…/run_record.json`, `run.log`, `result_channel.txt` (sealed values from the result
channel, never the manager view):

| run | executed | `val_return` (outcome.value) | `elapsed_seconds_info_only` | sealed `test_return` |
|---|---|---|---|---|
| `s000_baseline` B1 | true | **22.486719** | **61.248 s** | **22.885938** |
| `s001` | false (refused) | — | — | — |
| `s002` | true (divergent) | null | 40.818 s | null |
| `s003` | true | 18.742188 | 62.848 s | 18.716406 |
| `E1` | true | 18.742188 | 58.856 s | 18.716406 |
| `E2` | true | 16.975781 | 61.065 s | 17.364062 |
| `E3` | true | 6.934375 | 58.362 s | 6.940625 |
| `E4` | true | 24.753125 | 58.069 s | 24.896875 |
| `B2` | true | **22.486719** | **61.781 s** | **22.885938** |

- B2 reproduces B1 exactly (`result_channel.txt` byte-identical, sha `20ddf2fd…`); derived node timeout
  **3 × 61.248 = 183.744 s**; provisional 1800 s; no timeout/OOM; no retry. `report:134-159` matches all values.
- **CPU/RAM aggregate:** `/usr/bin/time -v` for the whole smoke, user **500.69 s**, sys **109.46 s**, wall
  **7:44.38**, max RSS **1,262,488 kB**, exit 0 (`time_v.txt`), labelled "aggregate, not a per-run peak"
  (`report:129-130`).
- **Record/log shas:** I re-verified `record_hashes.txt` with `shasum -a 256 -c` — all 25 entries OK; baseline
  record `7d1072c7…`, B2 record `687cc9ed…`, s000/B2 log `b71466df…`, result channel `20ddf2fd…` as reported.
- **`SHA256SUMS`:** `shasum -a 256 -c` rc 0, **1,115/1,115 entries OK**; every one of the 1,116 files in the result
  dir is either listed or is `SHA256SUMS` itself. `verify_full.json` sha `d395da41…` `ok:true` (9/8 refused_s001;
  sealed_key `test_return`; deployed == committed pin), `verify_full.v1_verifier_bug.json` sha `75a9fc92…`
  (`ok:false`, the two v1 check errors) preserved, `verify_records.json` issues `[]`, `summary.json` gate_ok true.
- **Live-Ada cross-check.** I piped the local `SHA256SUMS` into `sha256sum -c -` on live Ada: **1,108 entries OK,
  0 mismatches, 7 not present on Ada** — precisely the 7 Mac-authored record files (the result md, the three
  `references/` copies, the three `scripts/` sources). Live Ada has **exactly 1,108 files** in the evidence dir, all
  of which are in the local capture: **no live file is un-captured and every captured evidence file is
  byte-identical to live Ada.** The only live/local differences are the 7 Mac-authored record files (as expected).
- **Verifier false-negative history.** The first verifier run required every `determinism.not_forced` reason to be
  `torch_absent` and required `returncode 0` for the deliberately divergent `s002`; both are false negatives against
  the actual record semantics (`dataloader_workers` is "advertised via AR_NUM_WORKERS only"; the three torch
  settings are `torch_absent`; s002 is deliberately divergent and exits 4). The five-node campaign has the analogous
  s002 special-case precedent (its verifier patch), and the **accepted kit helper** `verify_records.py` independently
  passes on these JAX records with `issues: []`; the rc-0-only-for-ok-runs change is specific to this node's
  divergence exit code. The fixed verifier was
  re-run **on the same records, no smoke re-run**; the v1 outputs are preserved and the live `verify_full.json` is
  the fixed one. Disclosure is accurate (`report:173-181`, `RESULT_STATUS` correction block, `DONE`). The residual
  gap is that the v1 **source** and the fix diff/patch are not preserved (R3/condition S2), and the fixed
  verifier's own docstring still describes the v1 rule (`scripts/verify_u2_records_jax.py:10-12`) — cosmetic.

## 5. C1–C7 and the accepted record standard — mostly satisfied

- **C1 (licence/provenance)** — **satisfied**: `report:53-57` plus census-directed line. Live `LICENCES.md` confirms.
- **C2 (JAX fix record committed and cited)** — **partially satisfied (R7)**: committed at `af5fa558`, cited by
  path+sha (`unit:25-26`, `report:13-15`), and shot-for-shot consistent with the live env; but the 16-line fix
  record itself carries **no captures** (no raw 65-line freeze, no nvcc-removal command, no `jax.devices()` output),
  and does not cite the result's `prechecks_jax_env/` where that post-fix evidence lives. C2 asked for the captures.
- **C3 (fresh JAX/device/freeze check, smoke-entry dry-run, test-only add, one-line command, probe bytes)** —
  **satisfied in substance** (`prechecks_jax.txt`, `prechecks_jax_env/`, `invocation_inner.sh:59`,
  `cgroup_probe.txt`) except the executed unit's freeze/pytest STOP text not being reconciled (R1).
- **C4 (tracked-clean + HEAD==tip, pin equality/STOP, data-prep citation, exact gate command/capture)** —
  **satisfied in the run/captures** (`kit.txt`, `pins.txt`, `data_manifest.txt`, `gate/`), but only partially
  applied to the unit text (`unit:15-16` still says "record both, do not interchange" without the no-data equality
  expectation; `unit:17-18` has no data-prep citation; `unit:19-20` does not spell out
  `git status --porcelain --untracked-files=no` / untracked-link caveat). The launch script implements all four
  (runner lines 108-110, 129, 99, 201-226). See S7.
- **C5 (provisional vs 3×B1, floor basis, no-switch/contamination, no push/no other host/no-resume, extra STOPs,
  disk)** — **partially satisfied**: the result separates provisional 1800 s from the derived 183.744 s and says
  "no TASL-7/TASL-2, no HTCondor/deepthought, no other host; no deletion; no push/commit" (`report:17-18`,
  `:131`), but the **8 GiB floor basis**, **mid-run contamination/no-switch rule**, **no-resume**, **filesystem
  naming**, and the **"other users would be disturbed"/env-freeze** STOP additions are absent (S3, S4); the unit
  text also still carries the un-separated "3 × B1 (provisional 1800 s)" phrasing (`unit:60-61`) and the
  "no force push" rather than "no push" residue (`unit:8`). See S7.
- **C6 (full accepted result/capture standard)** — **partially satisfied**: host/boot/driver, gate JSON+UTC, B1/B2
  and every edit outcome, sealed-value source, both pins, env freeze/data, cgroup probe bytes, three-point GPU
  census + sampler label, `time -v`, disk before/after, isolation fields, `CHECKLIST_E_PASSED` + 8 executed +
  refused diff, one-node/no-evidence/no-noise, no retry, executed amended unit bytes (`references/`), and
  `SHA256SUMS` are present. Missing are the **S3 record-identity fields** (result file's own path/sha and the
  `SHA256SUMS` sha, canonical `node_spec_sha256` + loader formula, E1–E4 diff shas, explicit one-JSON-line-per-run),
  the **S10 `scripts/` README + documented fix patches** claim (the dir has only three files), the **S5** floor
  basis/rule, the **S6** no-resume/filesystem, and the **S8** "read-only" wording — findings S1, S2, S3, S4, S5.
- **C7 (one smoke, no retry, one node, no scope creep)** — **satisfied**: one executed smoke (attempt 1 no smoke),
  one node, no T1/evidence/noise/D21/D28, no other node/host, captures preserved, no deletion; the result dir is
  untracked and nothing was pushed.

## 6. Findings (all MINOR; no BLOCKING, no MAJOR)

| ID | Severity | Evidence | Finding / required correction |
|---|---|---|---|
| R1 | MINOR (mandatory) | `unit:34-37`, `unit:67-69`; `report:43-52`, `:177-181`, `:194-197`; `prechecks_jax_env/freeze_diff.txt:1-7`; `precheck_freeze_live_sorted.txt`; `env.txt:5-10`; `prechecks_jax.txt:14-18` | The executed unit's launch precheck ("freeze sha == `d33c9612…`", "pytest available or absence = STOP") was superseded by the accepted M-4/C3 test-only-add path: pre-add 65-line sorted freeze = `d33c9612…` exactly, launch 68-line sorted = `80a455c6…` = `d33c9612…` + exactly pytest/iniconfig/pluggy; first `smoke_entry` dry-run failed before the add. Disclosed, but the executed-unit STOP text is not reconciled and the unit was not amended to C3. Add an explicit reconciliation paragraph (or amend the unit text) recording that the add is test-only, the pre-add freeze reproduces the fix record, and JAX versions/devices/nvcc are unchanged (no rerun). |
| R2 | MINOR | `runs/runs_smoke/s002/run_record.json`; `report:168-169` | The deliberately divergent `s002` has `process.returncode: 4` and `leftover_processes_killed: true` (then cgroup-killed, `empty_after: true`). The report states only "ok runs returncode 0" and omits these two fields; state them explicitly (they are expected for this node and differ from the five torch-node records). |
| R3 | MINOR | `report:78-82`; `gate/gate_20261119T045751Z.json` (`utc 04:57:57Z`); `cgroup_probe.txt:13` (`04:57:59Z`); `logs/run_node.log:1`; `env.txt:1` | "The single executed smoke is attempt 2, launched at `04:57:51Z`" is imprecise: `04:57:51Z` is the runner/evidence-dir start (host/env captures); the gate JSON is `04:57:57Z`, the scope probe `04:57:59Z`, first sampler row `04:57:58Z`. Correct/explain the two timestamps (C2 class). |
| R4 | MINOR | `report:183-187`; `disk_before.txt`; `disk_after.txt`; `RESULT_STATUS.txt:12-13` | The report cites `75,439,415,296` / `75,401,555,968` B as `disk_before.txt`/`disk_after.txt`, but those captures record **`75,439,427,584` / `75,401,625,600`** B; the cited values are the runner's `RESULT_STATUS` `disk_avail_*` samples at a different instant. Cite the capture values or name `RESULT_STATUS.txt` as the source (C1 class). |
| R5 | MINOR | `report:205-214`; `gpu/gpu_mid_precheck_window.txt:13-26`; `env.txt:15`; `scripts/run_node_jax.sh:81,299-317` | "No other user's GPU process/card was disturbed" is broader than the evidence: the required in-scope `jax.devices()` prechecks created a client on **all 8 cards** (pid 246999, 426 MiB app / 439 MiB used per card at 04:58:06Z), and the **pre-scope** `env.txt:15` `jax_devices_no_mask` call also initialised a client on all 8 cards before the sampler started (so it is outside the whole-smoke sampler bound and not explicitly disclosed). No process was touched and no harm is evidenced (the used card returned idle; other cards' changes are other users' own jobs), but reword and disclose the pre-scope call. |
| R6 | MINOR | `report:93-94`; `sampler/sampler_max.json:2-13`; `sampler/sampler_required.csv` | "10 distinct worker pids (all this smoke)" — 2 of the 10 (`245960`, `246999`) are the `jax.devices()` precheck processes (all-card 426 MiB), the other 8 are run workers; the 634 MiB max is worker pid `300852` at 05:03:50.8Z. Reword to "10 processes of this run scope (2 precheck + 8 run workers)". |
| R7 | MINOR | `JAX_ENV_FIX_20261119.md:1-16`; `prechecks_jax_env/env_before.txt:1-27`; `prechecks_jax_env/freeze_before_sorted.txt` | C2's captures are not in the committed fix record (no raw 65-line freeze, no nvcc-removal command, no `jax.devices()` output), and the fix note does not cite the result's `prechecks_jax_env/`. Append/cite the captures (or a companion note) so the fix evidence is not split between the fix record and the result (no rerun needed). |
| S1 | MINOR | `report:216-230`; `SHA256SUMS`; `verify_full.json:494-501`; `kit.txt:10-16`; records' `node_spec_sha256` | S3 record-identity residual: the result does not print its own file path/sha (it is the `./U2_ISO_MLGYM_BREAKOUT_MINATAR_RESULT_20261119.md` entry, sha `532513e7…`) nor the `SHA256SUMS` sha `e55aa282…`; it gives the raw node-spec sha `b3cedcd6…` but not the canonical `node_spec_sha256` `db57b202…`/loader formula (= every record); it does not give the E1–E4 diff shas (in `kit.txt:13-16`) nor an explicit one-JSON-line-per-run statement (`verify_full.json:496` `json_run_lines: 9`). Add a "Record identity and preserved bytes" section. |
| S2 | MINOR | `report:227`; `scripts/` listing; `SHA256SUMS` entries; Ada `…/scripts/_patch*.py` | The evidence index claims `scripts/` contains "the documented fix patches"; it contains only `compute_sampler_max.py`, `run_node_jax.sh`, `verify_u2_records_jax.py` (all live-byte-identical to Ada, shas `7d9f472e…`, `4b5113fe…`, `8822495f…`). The verifier v1→fixed change has no preserved patch/README (v1 source absent; only v1 outputs), unlike the five-node `_patch2_verifier_s002_fix.py`/README precedent. Add `scripts/README.txt` + the verifier fix as a patch/diff (or reconstruct v1 from the v1 check names), record shas, and correct the claim. |
| S3 | MINOR | `report:86-88`; `unit:56-59` | S5 residual: the 8 GiB floor's basis is unstated and the mid-run contamination rule / "no switch from the launch card" is absent (the report says only "no other user's app ever appeared"). Add the basis (kit-update measured ~2.85 GB per-run torch peak; prior accepted run-1 floor 24 GiB; chosen card 48,427 MiB free), the rule (free VRAM below baseline peak + 2 GiB or a new co-tenant on the used card → STOP/record), and confirm the selected UUID is the only card in qualify/before/mid/after and every record. |
| S4 | MINOR | `report:129-132`; `report:183-187`; `disk_before.txt:2-7` | S6 residual: no "no-resume" statement (an interrupted unit re-runs whole from a new `<runs-root>`; no resume occurred) and the disk filesystem is not named (`/dev/md0p3` on `/`). Add both. |
| S5 | MINOR | `report:229-230`; live Ada dir/file modes | S8 residual: "Raw evidence is also preserved read-only on Ada" — the live evidence dirs are `drwxrwxr-x` and files `-rw-rw-r--`, i.e. operator-writable (unaltered/hash-matching, not read-only). Say "preserved unaltered". |
| S6 | MINOR | `report:8`; `report:11-12` | S4 residual: the kit-update report is cited only as "`sha256 fe232e2b…`" (full `fe232e2bbf236337e208f11e97c809f8a41d7ef101567eeb0d11153bacb9d026`) and the kit-update **review** `d8c68f9f0463d1aa3e17f82527dfb7ecf7b6070831584cd1024a6d39ed6a21b4` is not cited; use full 64-hex authority shas (the record-level shas that matter are otherwise full). |
| S7 | MINOR | `unit:15-16`, `:17-18`, `:19-20`, `:56-59`, `:60-61`, `:67-69`; `scripts/run_node_jax.sh:99,108-110,129,201-226`; `report` C4/C5 sections | C4/C5 were to be applied "to the unit/launch notes"; they are implemented in the launch script and the result captures, but the executed unit text still lacks the pin-equality expectation, data-prep citation, exact tracked-clean/untracked-link wording, floor basis, no-switch/contamination rule, no-push/no-other-host/no-resume wording and the extra STOPs. Record which C1–C5 items are implemented in the launch notes and amend the unit text for the rest (or state explicitly that the launch notes are the operative form). |

**Deviations verified as accurately disclosed and non-material (no condition):** attempt-1 pre-launch gate STOP and
the single executed smoke (R3 correction only); the mid-run watcher precheck-window snapshot + sampler-derived mid
census (`report:100-106`, `:198-200`); the pins `deployed_mlgym.json` pre-dating this node (`report:66-68`);
the verifier false negative with v1 outputs preserved (`report:177-181`); the in-scope `jax.devices()` transient
allocation (`report:205-208`). The result's claims that matter are otherwise accurate: whole-smoke upper-bound label,
`SHA256SUMS` verification, 1,115 entries, 1,108 live-identical evidence files, 7 Mac-only record files, live kit
tip/clean, live pins/pin recomputation, live Python/JAX/pytest/nvcc state and live freeze `80a455c6…`.

## 7. Conditions before the census row / commit (no re-run authorised)

1. **R1** — add the freeze/pytest reconciliation note (executed unit's STOP text superseded by accepted M-4/C3;
   pre-add 65-line sorted freeze = `d33c9612…`; launch 68-line sorted = `80a455c6…` = +3 test-only packages; JAX
   versions/devices/nvcc unchanged and live-verified; no rerun). Optionally amend the unit text to the C3 wording.
2. **R2** — record `s002` `returncode: 4` and `leftover_processes_killed: true` (cgroup kill `empty_after: true`).
3. **R3** — correct the "launched at 04:57:51Z" statement to runner-start `04:57:51Z` / gate `04:57:57Z` /
   scope+smoke after.
4. **R4** — cite the `disk_before.txt`/`disk_after.txt` values (`75,439,427,584` / `75,401,625,600` B) or name
   `RESULT_STATUS.txt` as the source.
5. **R5** — reword the no-disturbance claim and disclose the pre-scope `jax.devices()` all-card allocation.
6. **R6** — reword the sampler pids (2 precheck + 8 run workers).
7. **R7** — append/cite the fix captures in the JAX fix record (or a companion note) without changing the env.
8. **S1–S7** — add the record-identity section (own sha + `SHA256SUMS` sha + canonical `node_spec_sha256`/formula +
   E1–E4 diff shas + one-JSON-line-per-run); add `scripts/README.txt` + the verifier fix patch and correct the
   "documented fix patches" claim; add the floor basis/contamination rule; add no-resume + filesystem; reword
   "read-only" to "preserved unaltered"; cite full authority shas; record the C1–C5 unit-vs-launch-notes split.
9. Recompute `SHA256SUMS` after any record-file edit (and re-verify with `shasum -a 256 -c`); the result md's own
   sha will change, so the census/commit must use the regenerated value and state it.

## 8. Census-row support

The result supplies, for one node only and ENGINEERING_ONLY, everything the census row needs: node
`mlgym_breakout_minatar` (MLGym, JAX; `rlBreakoutMinAtar`); **committed-file pin `cec562e6…`** (census value) and
deployed pin equal; **B1 61.248 s / `val_return` 22.486719 (AR_METRIC) / sealed `test_return` 22.885938
(AR_TEST, result channel)**; B2 61.781 s identical; **derived node timeout 183.744 s**; **whole-smoke GPU upper
bound 634 MiB** (labelled, not a per-run peak); whole-smoke CPU/RAM aggregate (user 500.69 s, sys 109.46 s, max
RSS 1,262,488 kB); disk before/after above the 50 GiB floor; gate JSON+UTC; effective isolation on every executed
record; 8 executed + refused `s001`; one-node/no-evidence/no-noise/T1 statements. The census row must carry the
licence/provenance line (CC BY-NC 4.0 + gymnax-blines Apache-2.0, used), the JAX-env/test-only-pytest note, the
derived-mid-census caveat, and the R1–R7/S1–S7 record corrections. **The result supports the row; writing/committing
the row is outside this review.**

## 9. Attestation and command record

This review is the only file written (uncommitted). I ran no smoke, GPU/U2/census job or `jax.devices()`; I did not
edit a unit/code/record, did not commit/push/delete anything, did not touch HTCondor/deepthought/TASL-7/TASL-2, and
made no write on Ada. Read-only operations (19 November 2026, Europe/Berlin): `pwd`/`git rev-parse` (`HEAD
af5fa558`, `origin/main de3de54f`, merge-base `45fb94cc`)/`git status`; `sha256sum -c SHA256SUMS` locally (1,115
OK) and live on Ada via `sha256sum -c -` (1,108 OK, 7 Mac-only); reads of the unit, the unit review, the JAX fix
record, the result md and every capture in the result dir; recomputation from `runs/…/run_record.json`,
`run.log`, `result_channel.txt`, the sampler CSVs (5,060 required rows, 429 used-card samples, 473.852 s, 634 MiB
max, median-sample 432 MiB), `record_hashes.txt`, `verify_*.json`, `summary.json`; live Ada (`ssh -o BatchMode=yes
experiment_zhixu`, host `ucrtasl`, user `dowling`): `git rev-parse/status` of the kit worktree, `sha256sum` of the
node spec/manifest/pins, read-only Python recomputation of the 18-file committed pin from the live kit
(`cec562e6…`), the canonical `node_spec_sha256` (`db57b202…`) and the env versions, `uv pip freeze | sort |
sha256sum` (`80a455c6…`, 68 lines, no GPU initialisation); `ls/cat/find/stat` of the live evidence and attempt-1 dirs
(attempt-1 runs/sampler empty). No live-host state is claimed beyond these read-only results.
