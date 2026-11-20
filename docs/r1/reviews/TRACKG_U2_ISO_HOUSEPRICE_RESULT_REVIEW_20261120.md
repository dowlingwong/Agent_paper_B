# Independent review — Track G G.0 U2 result `mlgym_houseprice` (isolated kit, CPU) (20 November 2026)

**Reviewer.** Fresh independent reviewer (`u2-houseprice-result-reviewer`), delegated after the smoke; no involvement
in the unit, its R1/R2 reviews, the kit update, the port kit, the five-node campaign or the run. Read-only: the **only
file written is this review** (uncommitted). No new run or smoke, no unit/code/record edit, no deletion, no
commit/push, no HTCondor/deepthought. I logged in to Ada (`ssh -o BatchMode=yes experiment_zhixu`, host `ucrtasl`,
user `dowling`) **read-only** to compare every capture with the live evidence; I ran no smoke, no GPU device
initialisation, and made no Ada write.

**Objects under review.** Result directory
`docs/r1/reports/trackg_g0_20261117/u2_iso_mlgym_houseprice_20261120T215244Z/` — result md
`U2_ISO_MLGYM_HOUSEPRICE_RESULT_20261120.md`, sha256 **`c043f0dd3bdf3337df6ca25b7cab075dbd92b4c59b6fec3e0d8f5d390369e178`**,
248 lines, 20,029 B; `SHA256SUMS` sha256 **`80a835243830471f3df406478455652cf286c93e991daed5b7b765b826cae84c`**,
**445 entries** and 446 files total incl. `SHA256SUMS`; live Ada evidence under
`/home/dowling/r1_engineering/u2_iso_20261119/u2_iso_mlgym_houseprice_20261120T215244Z/` (417 files) and the
attempt-1 dir `…20261120T215213Z/` (22 files); the executed unit
`docs/r1/proposals/u2_iso_20261119/U2_ISO_MLGYM_HOUSEPRICE_UNIT_20261120.md`, sha256
**`0f13d2dc5d59bc487658018764d9517148540bc9cfe4b5313ba75435d77f94fe`** (78 lines, 6,551 B; the amended bytes), the
R2-reviewed bytes sha256 **`397ccfd1d985d8e265a1dc1d6ad687ee8265947ea05282e3c38a1ae3df463551`** (75 lines, 6,223 B per
the R2 review), the R2 review `TRACKG_U2_ISO_HOUSEPRICE_UNIT_REVIEW_R2_20261120.md` sha256
**`81580eec0afced568a5892c2bab5ff3429eb2e47e559ab19932de8b5e4bc6d51`** (ACCEPTED, conditions C1–C7) and the round-1
review sha256 **`36774ed52e93fae1e2393de6ce989810603897c91b8d1286b19a691dce505025`** (NOT ACCEPTED). Authority: worktree
`ops-tasl-20261116` HEAD **`6bbf4b3e3aa6ec411dc183ea9e5d3f35333e1404`**, `origin/main` **`df58bcd5bdeeb7d1cb1cd1c3beddc29376b3575e`**,
merge-base **`94db94bb5c0f4061cc111fdbfb719f6d18e6e9be`**; only four untracked items (unit, result dir, two reviews);
no commit/push. Kit update report sha256 **`fe232e2bbf236337e208f11e97c809f8a41d7ef101567eeb0d11153bacb9d026`** and its
review sha256 **`d8c68f9f0463d1aa3e17f82527dfb7ecf7b6070831584cd1024a6d39ed6a21b4`**; port report sha256
`78d354b8…`; kit tip `f07875de79a5a57739227b13e0fd52d31646edaf`.

**Verdict summary: ACCEPTED — 0 BLOCKING, 0 MAJOR, 10 result-specific + 5 shared-standard MINOR, conditional on
C1–C15.** I independently verified, from the records and from live Ada, the one executed smoke (attempt 1 was a
pre-launch CPU-idle STOP with no smoke), the inside-scope 8 GiB cgroup and effective isolation, the author CSV
identity and `--from-file` provenance, the kit tip/tracked-clean state, **both pins recomputed from the live kit with
the kit's own loader/isolation code** (`88d359f2…` committed 16 entries; `4cbbc5d6…` deployed 17 entries including
`data: link:/home/dowling/r1_trackg_20261117/data/mlgym_houseprice`), the numbers (**B1 5.059 s / `val_rmse`
23344.767385 / sealed `test_rmse` 30295.671017; B2 4.876 s identical; 3 × B1 = 15.177 s; 8 executed + refused
`s001`; `CHECKLIST_E_PASSED`**), `time -v`, the `SHA256SUMS` (445/445 OK) and the live-Ada fidelity (all 417 live
files byte-identical to the local `SHA256SUMS`; the 22 attempt-1 copies byte-identical to the live attempt-1 dir). The
findings are record-completeness / wording / citation items of the same class the five-node and Breakout results were
accepted-and-corrected for, plus four this node needs (a truncated per-CPU process census, the prepared-data copy
wording, the static-test capture, and the executed-unit-vs-C1–C4 reconciliation). **No re-run, second smoke,
T1/evidence, cross-node use or additional host is authorised by this review. Conditions C1–C15 are record
corrections to be applied before the census row/commit.**

## 1. Authority, method and limits

- **Authority** read at HEAD/`origin/main` as cited (PLAN rows `R1-TRACKG-G0-GO`, `R1-HARNESS-ISOLATION`,
  `R1-TRACKG-PORT-DECISIONS` (2) and (4), `R1-TRACKG-LICENCES`, `R1-TRACKG-G3-EARLY`); port report §2/§7; accepted kit
  update report/review and C-K1…C-K5; R2 review conditions C1–C7. I read the result md, every capture in the result
  dir, the executed unit, both unit reviews, the kit-update report/review and the five-node/Breakout result-review
  precedents (severity calibration).
- **Method.** Paper review plus recomputation from the records and **live, read-only Ada**. On Ada I ran
  `git rev-parse/symbolic-ref/diff-index/diff-files/ls-files`, `sha256sum`/`stat`/`readlink`/`find`/`du`, read the
  kit's own `compute_pins.py` / `node_template.py` / `prepare_data.py` / `run_fixed_budget.py`, and executed (with
  `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1`, no GPU) the kit's own
  `load_trackg_node_spec`/`isolation.frozen_file_hashes` to recompute the two pins and `spec.raw_sha256`; no write on
  Ada.
- **Limits.** I did not re-run anything and claim no host state beyond these read-only results. The consolidated
  result (report + `SHA256SUMS` + `references/` + `scripts/` + the attempt-1 copies) lives in the Mac worktree; the
  live Ada dir holds the 417 raw captures only (all byte-identical to the local `SHA256SUMS`; the live attempt-1
  sibling dir's 22 files are byte-identical to the local copies). No file was deleted; the executed unit copy
  (`references/U2_ISO_MLGYM_HOUSEPRICE_UNIT_20261120.md`, `0f13d2dc…`), the R2 review (`81580eec…`) and the round-1
  review (`36774ed5…`) are byte-identical to their repo sources.

## 2. One accepted unit, one executed smoke, kit, pins, licence, data — PASS

- **Unit / executed bytes.** R2 accepted the 75-line `397ccfd1…` with conditions C1–C7. The executed bytes are
  `0f13d2dc…` (78 lines, 6,551 B), preserved in `references/` and byte-identical to the current proposal file. I
  verified the amendment applied the **one pre-execution defect** the R2 review said would stop a literal launch —
  the "**the launch command must be one physical line** (the block is documentation; join the `&&` parts …)"
  sentence (`unit:56-57`) — and removed the truncated pin literal (`unit:26-29` now says read the full 64-hex from
  the kit at launch; no other node's pin remains). The other R2 MINOR text residues survive (see H6).
- **One executed smoke, no retry.** Attempt 1 (`…20261120T215213Z/`, `attempt1_prelaunch_cpu_idle_stop/`) is a
  **pre-launch CPU-idle STOP**: `logs/run_node.log:2` "STOP: selected CPU set mean idle 70.6% < 80%; no smoke
  launched", `DONE_PRELAUNCH_STOP 2026-11-20T21:52:19Z`, and on live Ada `attempt1…/runs/` and `attempt1…/gate/` are
  **empty** (no run record, no gate capture). Attempt 2 is the single executed smoke (`systemd_run_rc=0`,
  `CHECKLIST_E_PASSED mlgym_houseprice`, `SMOKE_EXIT=0`); the result directory holds exactly 9 `run_record.json` (8
  executed + refused `s001`), no second scope, no retry.
- **Kit tip / tracked-clean — live-equal.** Live `git -C /home/dowling/r1_trackg_20261117/harness_iso_mlgym`
  branch `mac-trackg-iso-mlgym-20261117`, HEAD **`f07875de79a5a57739227b13e0fd52d31646edaf`** =
  `origin/mac-trackg-iso-mlgym-20261117`; `diff-index --quiet HEAD` and `diff-files --quiet` both rc 0; untracked
  exactly the three runtime `data` links (`mlgym_cifar10`, `mlgym_fmnist`, `mlgym_houseprice`) (`kit.txt` sha
  `a883f308…`, live-equal). Live node spec file sha **`1b95447d3d1c0753a11749fc4b11639959e770f1aa10a142b2ff583d5a92a389`**,
  canonical parsed-spec `raw_sha256` **`2f150cded7c846a28fd97113519333a33d9775588a7d6c7bd0d9dcc05e85c049`** (the value
  in all nine records), representative-edit manifest `f26332ff…`, `LICENCES.md` `a8a2c62b…`, `requirements.txt`
  `31b0189a…`; all frozen-file shas in `kit.txt:19-27` live-equal.
- **Both pins — independently recomputed from the live kit.** With the kit's own loader/isolation code:
  committed-file pin (16 frozen entries, `data/` excluded) =
  **`88d359f2c59449a5c49d75d40fedd72436f76154e78b622f8c69b384a1d5a654`** (equals
  `pins/new_mlgym.json` sha `8974359b…`, live-read, 16 entries, and kit-update §3/§9); deployed run-record pin
  (17 entries incl. `data: link:/home/dowling/r1_trackg_20261117/data/mlgym_houseprice`) =
  **`4cbbc5d6673d1e0cff15e1df4ea6dfe6941ac028b68109f1b86849ab9e36a144`** (equals every record's
  `frozen_pin_sha256` and the `pins.txt` recomputation, sha `f9514cf6…`). The two are **not** interchanged; the
  result names the committed pin as the census value and the deployed pin separately — the accepted convention.
- **Author CSV — verified live, `--from-file`, no MLGym copy.** Live
  `/home/dowling/house-prices-advanced-regression-techniques/train.csv`: size **460,676 B**, mode `-rw-rw-r--`,
  mtime `2019-12-15 21:33:36 -0800` (the directory's mtime is 20 Nov 2026 21:11 UTC, consistent with the recorded
  placement), sha256 **`1e18addf81e5e4d347cc17ee6075bbe4a42b7fa26b9e5b063e8f692a5f929d41`**, md5
  **`80ccab65fb115cbad143dbbd2bcd5577`**, **1,461 lines** (header + 1,460 rows); `prep/csv_verify.txt` (sha
  `62e8a8af…`) records the same and passes. Setup (`prep/setup.log`, sha `60289148…`) runs the unit's guarded
  command from the node dir with `envs/torch312/bin` first, `AR_TRACKG_DATA_ROOT=/home/dowling/r1_trackg_20261117/data`,
  `AR_HOUSEPRICE_TRAIN_CSV=<author path>`, `--from-file`, `SETUP_RC=0`; `data_manifest.json` sha
  **`73ee5597…`** with `provided_by = "user download, passed with --from-file"`, `from_file_name = train.csv`,
  `source.sha256 == files.houseprice.csv.sha256`, `md5`, `rows = 1460`, no `synthetic` key; node data link →
  `…/data/mlgym_houseprice` (outside the repo), data dir `555`/files `444` read-only, 2 files / 461,273 B;
  every executed run log carries `AR_DATA houseprice_sha256=1e18addf… md5=80ccab65… same_as_mlgym_copy=True`
  (informational; the kit's `MLGYM_COPY_SHA256` constant — the MLGym copy is not used and no MLGym copy exists in
  the live kit). `same_as_mlgym_copy=True` is correctly labelled informational.
- **Licence / provenance.** Live `LICENCES.md` sha `a8a2c62b…` confirms MLGym task `regressionKaggleHousePrice`
  **CC BY-NC 4.0** (non-commercial, attribution and changes), Kaggle terms for the data, `train.csv` only, no MLGym
  copy, and that the gymnax/gymnax-blines-derived Apache-2.0 parts are not used by this node; `report:211-215` carries
  the required line, citing `R1-TRACKG-LICENCES` and the census funnel/appendix duty.

## 3. Isolation, cgroup, CPU co-tenancy and gate — PASS with one record-quality MINOR (H3)

- **Inside-scope cgroup.** The inner script computes `CG=$(cut -d: -f3 /proc/self/cgroup)` and
  `AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG` **inside** the `systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G
  -p MemorySwapMax=0 -- bash -c …` scope (`scripts/run_node_houseprice.sh:255-321`; `invocation_inner.sh` sha
  `9d258ba3…`), echoes `scope_cgroup=…/run-r3861b8588c684aa6a76ad8d9c53a4c33.scope`, and the probe reads
  `memory.max=8589934592`, `memory.swap.max=0` from the echoed path (`cgroup_probe.txt` sha `188bd0ec…`). The live
  scope path is absent (`removed`), consistent with `cgroup.kill`/`removed: true`.
- **Every executed record effective.** All 8 executed records: `isolation.effective: true`, `waivers {}`,
  `exceptions []`, `log_intact: true`, result channel present (`result_channel_overflow: false`,
  `result_channel_sha256`), `cgroup.kill` `method: cgroup.kill`, `empty_after: true`, `removed: true`, 17 frozen files
  checked, `limits.external_limit` exactly the one-line unit string, `gpu_uuids: []`, `cpu_list
  [79,78,77,76,59,42,34,28]`, `memory_method: external`, provisional 1800 s, `timeout_factor: 3.0`, `run_budget
  {kind: steps, value: 1}`, `determinism.not_forced == ["dataloader_workers"]`, `shim_loaded: true`,
  `process.killed_with: null`, `timed_out: false`, ok runs `returncode: 0`. `s001` is `executed:false`,
  `outcome:null`, `refusal: scope_violation`, no isolation fields by design.
- **Gate.** Gate JSON sha `31082f5b…`, UTC **`2026-11-20T21:52:50Z`**, `verdict: clear_finished`,
  `paper_a_live_waiting_for_card: false`, `paper_a_processes: []`, `unidentified_apps: 0`, rc 0; newest v4 `live_*`
  == configured run dir; self-excluded `pgrep port_smoke_gpu` and `agent-checkpoint-intervention` empty
  (`gate/gate_check.txt`, captured 21:52:52). The launcher runs the gate **before** the `systemd-run` launch
  (`run_node_houseprice.sh:190-238` vs `:321`), so the gate truly precedes the scope/probe (21:52:52) and smoke.
- **CPU co-tenancy (H3).** Loadavg 37.40 / 37.13 / 34.21 (1-min ≤ nproc/2 = 48 PASS), selected-set mean idle 80.0 /
  71.8 / 99.9 %, runner's separate selected-set sample **97.4 %** ≥ 80 % PASS; `taskset` applied; the run was
  confined to the cpuset; no foreign process was signalled/killed/reniced. **However** the per-CPU process census
  (`ps -eLo … | awk … | head -40`, `run_node_houseprice.sh:156`) is **truncated**: `cpu/cpu_mid.txt` and
  `cpu/cpu_after.txt` contain exactly 40 rows, all root kernel threads, and the node's own smoke process (PID in the
  3.6 M range) sorts after the low-PID kernel threads and is cut, so the sentence "Only root kernel threads … no
  other user's process was observed on the selected cpuset" (`report:120-123`) is **not established** by the capture
  (the `cpu_summary` `dowling_proc_rows=0`/`other_user_proc_rows=0` is an artifact of the cap). The preserved
  `cpu/cpu_summary.v1_parse_artifact.txt` (sha `077de1c1…`) shows the v1 parser's
  `foreign_users_on_selected_cpus=['root','the']`, and this corrected-capture artifact is not in the report's
  deviations. The load/mpstat evidence supports the co-tenancy decision; the wording must be narrowed (H3).
- **No GPU / CPU-only.** No `--gpu-uuid`; `CUDA_VISIBLE_DEVICES=""`; `cuda_available_under_mask=False`;
  `gpu_uuids: []`; the host has an NVIDIA driver and other users' GPU apps (the gate's gpu census), but this run
  initialised no card and used no GPU. Correctly recorded.

## 4. Numbers, records, captures and live-Ada fidelity — PASS

Numbers recomputed from the run records, run logs and result channels (sealed values from the result channel's
`AR_TEST test_rmse=`, never the manager view):

| run | executed | `val_rmse` (outcome.value) | `elapsed_seconds_info_only` | sealed `test_rmse` |
|---|---|---|---|---|
| `s000_baseline` **B1** | true | **23344.767385** | **5.059 s** | **30295.671017** |
| `s001` | false (refused) | null | — | — |
| `s002` | true (divergent `non_finite_loss`) | null | 5.142 s | nan |
| `s003` | true (discarded: 25212 > baseline) | 25212.233839 | 5.126 s | 31026.614481 |
| `E1` | true | 25212.233839 | 5.291 s | 31026.614481 |
| `E2` | true | 25763.93275 | 5.266 s | 33085.957104 |
| `E3` | true | 19369.761061 | 5.058 s | 23698.247199 |
| `E4` | true | 23241.878689 | 6.794 s | 27813.556114 |
| `B2` | true | **23344.767385** | **4.876 s** | **30295.671017** |

- B2 reproduces B1 exactly in value; the E1–E4 record `diff_sha256` values equal the kit's representative-edit diff
  shas (`3ee108ef…`, `7e4a71a0…`, `81eaa685…`, `e9a1e8e9…`); derived node timeout **3 × 5.059 = 15.177 s**;
  provisional 1800 s; no timeout/OOM; no retry.
- `/usr/bin/time -v` (whole-smoke aggregate, not a per-run peak): user **47.60 s**, sys **8.35 s**, wall
  **0:43.97**, max RSS **599,392 kB**, exit status 0 (`time_v.txt` sha `34f17ab1…`). The `time -v` command line
  records the exact `python -m tests.trackg.port_smoke_gpu … --cpus … --memory-limit "external: systemd-run … (enforced
  cgroup)" --runs-root …/runs --provisional-timeout 1800`.
- `record_hashes.txt`: 25/25 entries recomputed OK. `SHA256SUMS`: **445/445 OK, rc 0**; every one of the 446 files is
  listed or is `SHA256SUMS` itself (the task's "445 files" = the 445 entries; 446 files incl. `SHA256SUMS`).
- **Live-Ada fidelity.** All **417** live files in the executed evidence dir are byte-identical to the local
  `SHA256SUMS` (no live file un-captured; no hash mismatch); the local-only 28 files are the Mac-authored records
  (`U2_ISO_MLGYM_HOUSEPRICE_RESULT_20261120.md`, `SHA256SUMS`, 22 attempt-1 copies, 3 `references/`, 2 `scripts/`) —
  as expected. The live **attempt-1 dir 22 files** are byte-identical to the local `attempt1_prelaunch_cpu_idle_stop/`
  copies. The live `scripts/run_node_houseprice.sh` (sha `360b2053…`) and `verify_u2_records_cpu.py` (sha
  `63a4bdf1…`) are byte-identical to the result-dir copies, and the live run-record mtimes (13:53:02–13:53:40 PST =
  21:53 UTC) are **before** the verifier outputs (13:54:57 PST = 21:54:57 UTC), confirming the verifier fix was
  re-run on the same records with **no smoke re-run**.
- **Verifier history — accurate.** The v1 `verify_full.json` (preserved as `verify_full.v1_verifier_bug.json`, sha
  `7bccb89f…`) failed only the single `node_spec_sha256 expected` check (8/8 executed); all other 27 checks per run
  were true. The kit's own accepted helper `verify_records.py` returned `issues: []` and `collect_smoke_summary.py`
  `gate_ok: true, issues: []` **on the unmodified records**, and the canonical hash is verified live as
  `2f150cde…` = `spec.raw_sha256` (the kit's `runner.py` records `spec.raw_sha256`), so the fixed verifier's
  64-hex canonical check is the correct rule, not a loosened one; the live `verify_full.json` is the fixed one
  (`ok: true`, 9 records / 8 executed / refused_s001 true / sealed_key `test_rmse` / deployed pin == 4cbbc5d6…).

## 5. C1–C7 and the accepted record standard — mostly satisfied

- **C1 (pin record)** — **satisfied**: both pins as full 64-hex, recomputed independently, deployed separate, census =
  committed; no other node's pin. See §2.
- **C2 (author file + setup + manifest)** — **satisfied in the result** (§2); the executed unit still carries the
  R2 m2 phrase "confirm … the source **path/hash** appear" (`unit:36-37`) even though the manifest records no path;
  the result itself uses the correct `provided_by`/`from_file_name`/`source.sha256`/`md5`/no-synthetic checks
  (`report:44-51`). H6.
- **C3 (launch command / probe / gate / launch checks)** — **satisfied**: the launch is a script invocation of the
  unit's one-line command (`scripts/…:319-321`; `invocation_inner.sh`), the probe reads the echoed inside-scope path,
  the gate command/three-check/UTC are captured, `kit.txt` has HEAD==tip and tracked-clean (live-verified), `which
  python`/imports/versions/freeze sha are prechecked with a mismatch STOP. H6 (unit text not reconciled).
- **C4 (CPU co-tenancy, B1/B2, static test, scope/STOPs)** — **satisfied in substance**: cpuset/threshold/snapshots,
  B1/B2 labels, the static test ran with the accepted counts (225 passed / 2 known env failures / 1 skipped / 6
  deselected in 48.33 s; log sha `aec75c45…`), no-push/no-other-host statements (no-resume is S2), 100 GiB cap
  statement, resolved invocation. Residuals: H3 (census truncation), H5 (static-test command/mask not captured),
  H7 (cpuset selection window not captured), unit residues H6.
- **C5 (result standard)** — **mostly satisfied**: B1/B2 elapsed+`val_rmse`+sealed, every edit outcome, per-run
  record/log/result-channel hashes, `returncode`/`timed_out`/`killed_with`, `determinism.not_forced`/`shim_loaded`,
  canonical node-spec and rep-edit shas, sealed source, host/boot/kernel, data manifest + `AR_DATA` + file
  count/size/read-only, disk `du`/`df`, cgroup probe bytes, CPU/load census, gate JSON+UTC, env freeze, both pins,
  isolation fields incl. `log_intact`/result channel/`cgroup.kill`, `CHECKLIST_E_PASSED` + 8 executed + refused
  `s001`, licence/provenance incl. `R1-TRACKG-LICENCES` and the Apache-2.0-not-used sentence and the census duty,
  executed amended unit copy (`0f13d2dc…`), captures + `SHA256SUMS`. Residuals: own/sha and `SHA256SUMS` sha not
  printed, E-diff shas and explicit one-JSON-line-per-run only in captures (S1); no-resume/filesystem (S2);
  abbreviated authority shas (S3); "preserved read-only" wording (S4); "verifier records both"/2.9 G source (S5);
  status-file reconciliation (H10).
- **C6 (assembly/record)** — **satisfied**: reviewed `397ccfd1…` and executed `0f13d2dc…` recorded; the executed
  copy is preserved in `references/`; kit branch at `f07875de…` unchanged.
- **C7 (execution rule)** — **satisfied**: one smoke, one node, no timeout/OOM retry, ENGINEERING_ONLY, no
  evidence/noise/D21/D28/T1, no cross-node pooling, no other host/HTCondor/deepthought, no deletion/push; a
  pre-launch STOP was not treated as a smoke and was not re-used.

## 6. Deviations verified as accurately disclosed and non-material (no condition)

- Attempt-1 pre-launch CPU-idle STOP (mean idle 70.6 % on cpuset 95,94,93,91,84,83,82,80; no smoke launched;
  preserved as `attempt1_prelaunch_cpu_idle_stop/`; live attempt-1 `runs/`/`gate/` empty). Correct and non-material.
- Mid-run snapshot early in the 43.97 s smoke (so it is not a mid-smoke snapshot; before/after and the whole-smoke
  `time -v` are recorded). Disclosed; see also H3/H7 for the wording.
- Verifier false negative on the node-spec canonical-vs-file hash, fixed and re-run on the same records with the
  originals preserved and the correction recorded in `RESULT_STATUS.txt`/`DONE`. Verified (see §4); see H8/H10 for
  the patch/status residuals.
- Cpuset chosen from live load with foreign users' jobs elsewhere on the host (load ~37/96) but none affected —
  consistent with the load/mpstat evidence (see H3 for what the per-CPU list does and does not establish).

## 7. Findings (all MINOR; no BLOCKING, no MAJOR)

| ID | Severity | Evidence | Finding / required correction |
|---|---|---|---|
| **H1** | MINOR | `report:108-109`; `logs/run_node.log:1`; `gate/gate_20261120T215244Z.json` (`utc 21:52:50Z`); `gate/gate_check.txt:1`; `cgroup_probe.txt:13`; `prechecks.txt:1`; `scripts/run_node_houseprice.sh:190-238,321` | "The single executed smoke is attempt 2 (… launched `21:52:44Z`, gate clear `21:52:50Z`)" is imprecise and reads as gate-after-launch: `21:52:44Z` is the runner/evidence-dir start, the gate JSON is `21:52:50Z`, the gate check `21:52:52Z`, the scope/probe/prechecks `21:52:52Z`, and the smoke starts after them. Correct the sentence (gate precedes the launch). |
| **H2** | MINOR | `report:206-208`; `disk_after.txt:4`; `RESULT_STATUS.txt:12`; `scripts/run_node_houseprice.sh:328,361` | The report cites **70,795,313,152 B** as "after" and attributes it to the disk captures, but `disk_after.txt` records **70,795,374,592 B**; the cited value is the runner's separate `df` sample (`RESULT_STATUS` `disk_avail_after_bytes`). Cite the capture value or name `RESULT_STATUS.txt` as the source (both are > 50 GiB; non-material). |
| **H3** | MINOR | `report:111-127`; `cpu/cpu_mid.txt`/`cpu_after.txt` (40 rows, all root); `scripts/run_node_houseprice.sh:156`; `cpu/cpu_summary.txt:5-7`; `cpu/cpu_summary.v1_parse_artifact.txt` (sha `077de1c1…`) | The per-CPU process census is `ps -eLo … | head -40`; mid/after are exactly 40 root-thread rows and the node's own process (row 41+) is cut, so "only root kernel threads … no other user's process was observed" is not established by the capture, and the `dowling_proc_rows=0` line is an artifact. The load/mpstat/idle evidence does support the co-tenancy PASS. Reword to what is captured (load, users, nproc, mpstat/idle; the per-CPU list is capped at 40 rows) and disclose the preserved v1 CPU-summary parse artifact in the deviations. |
| **H4** | MINOR | `report:20-31`; `unit:13-14,36-37`; `prepare_data.py:69` (live); live inodes `78787219` (data `houseprice.csv`) vs `66606474` (author `train.csv`); `prep/setup.log`; `prep/manifest.txt` | "No copy of the input file was made" is contradicted by `prepare_data.py`, which writes `<out>/houseprice.csv` as a byte copy of the author's file (different inode); and "as the run's `AR_DATA` line records" overstates: the `AR_DATA` line records sha256/md5/`same_as_mlgym_copy`, not the `--from-file` path (the setup log and manifest `provided_by`/`from_file_name` record that). Reword: no staging copy and no MLGym copy; the prepared data file is written from the author's `--from-file` source. |
| **H5** | MINOR | `report:75-82`; `prep/static_launcher.log` (0 bytes); `prep/static_mlgym_20261120T214935Z.log:1-2` and failure trace; `scripts/run_node_houseprice.sh` (no static-test block) | The static-test command/mask are stated (`systemd-run --user --scope -p Delegate=yes`, `taskset -c 0-15`, `CUDA_VISIBLE_DEVICES=`, `python -m pytest tests/trackg -q -p no:cacheprovider -k "not smoke"`, interpreter `envs/torch312/bin/python`) but the capture holds only the kit/tip/start header, "Running scope as unit: …scope" and pytest output; the interpreter is visible only in a failure trace and `static_launcher.log` is empty. The counts (225/2/1/6 in 48.33 s) and the two accepted known env failures match the kit-update baseline. Add the static-test command/mask capture (or a launcher note) and reconcile the report to it. |
| **H6** | MINOR | executed unit `0f13d2dc…` (`references/`); `report:10-15`; `unit:9,36-37,41-44,56-57,61-64,70`; `scripts/run_node_houseprice.sh:190-238,301-303` | The result says the R2 "pre-execution fixes C1–C4 [were] applied to the launch notes". The amendment applied the one mandatory pre-execution defect (the one-physical-line sentence, m4) and removed the truncated pin literal (n1), and the launcher/result implement C1–C4's substance, but the executed unit text still carries R2 MINOR residues (m2 "source path/hash appear" `unit:36-37`; m6 no exact gate command; m7 no cpuset/threshold; m8 no B1/B2 definitions; m9 "(or record why not)" `unit:61-62`; m13 citations; m14 exact git checks; m15 "no force push" `unit:9`; m16 no env-freeze STOP). Record which C1–C4 items are implemented in the launch/result records and amend the unit text for the rest (or state explicitly that the launch notes are the operative form). |
| **H7** | MINOR | `report:108-114`; `cpu/cpu_before.txt` tail (97.4 captured); `scripts/run_node_houseprice.sh:174-188` | "cpuset selected from a fresh 3-sample stable-idle window (minimum %idle across samples; all 8 were 94–100 % idle at selection)" is not captured: the harness records the before snapshot (mean idle 80.0 %) and the runner's separate one-sample check (97.4 %), i.e. two 1-s samples, not a 3-sample minimum. Record the selection window or reword to the captured samples. Also "the mid sample … reflects our own 4-thread fit" (`report:123`) is an interpretation — at 21:52:52 the smoke process had just exec'd (its imports/startup), not the fit; reword. |
| **H8** | MINOR | `report:197-202`; `verify_full.v1_verifier_bug.json` (sha `7bccb89f…`); `verify_full.summary.v1_verifier_bug.txt`; `scripts/verify_u2_records_cpu.py` (sha `63a4bdf1…`) | The v1 outputs are preserved and the change is described, but the **v1 source / fix diff is not preserved** as a patch or README (only the fixed script); the v1 check name (`node_spec_sha256 expected`) allows reconstruction. Add the one-line fix diff (or a `scripts/README` stating it) so the correction is reproducible, as the five-node/Breakout precedent does. |
| **H9** | MINOR | `runs/runs_smoke/s002/run_record.json:264`; `report:164` | The deliberately divergent `s002` record writes the bare literal `NaN` for `sealed.test_rmse`, which is not strict JSON (only Python's `json.load` accepts it); the report shows "nan". Label it (e.g. "recorded as `NaN` by the kit's runner; non-finite, not used") or record `null`/string; no measurement impact. |
| **H10** | MINOR | `RESULT_STATUS.txt:1-2,14-20`; `DONE` (`DONE_STOP`, `DONE_PASS_CORRECTED`); `report:14-15,197-202` | The status file still begins `status=STOP` and `DONE` still contains the first `DONE_STOP`, with the corrected `status_corrected=PASS`/`DONE_PASS_CORRECTED` appended. The report discloses the correction and the kit's own verifier already passed, but restate that the corrected block/fixed verifier is authoritative for the census (five-node C5 class) so a reader does not take the first block as the result. |
| **S1** | MINOR | `report:247-248`; `SHA256SUMS:3`; `verify_full.json` (`json_run_lines: 9`); `kit.txt:14-17`; `report:60-63`; `unit:70` | Record-identity residual (R3 mR6 / Breakout S1 class): the result md does not print its own path/sha (`c043f0dd…`), the `SHA256SUMS` sha (`80a83524…`), the E1–E4 diff shas (only in `kit.txt`), an explicit "one JSON line per run" statement, or the canonical `node_spec_sha256` loader formula (value given). Add a short "Record identity and preserved bytes" section (the unit's `result directory path + own/sha` asks for the own sha). |
| **S2** | MINOR | `report:229-232`; `disk_before.txt`/`disk_after.txt` (`/dev/md0p3`) | No explicit no-resume statement (an interrupted unit re-runs whole from a new `<runs-root>`; none occurred), and the disk filesystem is not named in the report (the captures show `/dev/md0p3` on `/`). Add both. |
| **S3** | MINOR | `report:9-10,12,15` | Abbreviated authority shas: kit update `fe232e2b…` (full `fe232e2bbf236337e208f11e97c809f8a41d7ef101567eeb0d11153bacb9d026`), kit update review `d8c68f9f…` (full `d8c68f9f0463d1aa3e17f82527dfb7ecf7b6070831584cd1024a6d39ed6a21b4`), R2-reviewed unit `397ccfd1d985…` (full `397ccfd1d985d8e265a1dc1d6ad687ee8265947ea05282e3c38a1ae3df463551`) and round-1 review `36774ed5…` (full `36774ed52e93fae1e2393de6ce989810603897c91b8d1286b19a691dce505025`). Cite full 64-hex for authority documents. |
| **S4** | MINOR | `report:243-245`; live Ada dir/file modes (`drwxrwxr-x`/`-rw-rw-r--`); live evidence 417 files | "Raw evidence is also preserved read-only on Ada" — the live dirs/files are operator-writable (unaltered and hash-matching, not read-only); say "preserved unaltered" (or make them read-only). Also state that the live dir holds the 417 raw captures only and that the report/`SHA256SUMS`/`references`/`scripts` are Mac-side (the 28 local-only files), with the live attempt-1 dir holding the 22 captured copies. |
| **S5** | MINOR | `report:60-63`; `kit.txt:11`; `report:206-208`; live `du -sh /home/dowling/r1_trackg_20261117/data` = 2.9 G | "the verifier records both" (the spec file sha and the canonical hash) is inaccurate: the fixed verifier's rows record only the canonical `node_spec_sha256`; the file sha is in `kit.txt:11`. And "whole data root 2.9 G" is not in the disk captures (it is true — I verified live — but cite the source or capture it). Reword/cite. |

**Deviations verified as accurately disclosed and non-material (no condition):** the attempt-1 pre-launch CPU-idle
STOP (H1 correction only); the early mid-run snapshot; the verifier false negative with v1 outputs preserved and the
same-records re-run (H8/H10 residuals only); the live-load cpuset choice with foreign jobs elsewhere on the host
(H3 wording only); `same_as_mlgym_copy=True` informational (H4 wording only). The result's claims that matter are
otherwise accurate: one smoke, kit tip/clean, both pins, author CSV identity/`--from-file`, the inside-scope cgroup
and probe bytes, effective isolation on every executed record, the B1/B2/edit numbers, `time -v`, `SHA256SUMS`
445/445, live-Ada fidelity, one-node/no-evidence/no-T1/no-cross-node, and no deletion/push/commit.

## 8. Conditions before the census row / commit (no re-run authorised)

All are record/text corrections; none changes the procedure, measurement identity, isolation result, pins, STOP set or
kit bytes. **No re-run, second smoke, or re-execution is needed or authorised.**

1. **H1** — correct the attempt-2 timing sentence: runner start `21:52:44Z`; gate JSON `21:52:50Z`; gate check and
   scope/probe/prechecks `21:52:52Z`; smoke after; gate precedes launch.
2. **H2** — cite `disk_after.txt`'s **70,795,374,592 B** (and `disk_before`'s 70,644,187,136 B) or name
   `RESULT_STATUS.txt` as the source of 70,795,313,152 B.
3. **H3** — narrow the co-tenancy claim to the load/mpstat/users/nproc evidence; note the per-CPU list is capped at 40
   rows (and why the node's own process is absent); disclose the preserved v1 CPU-summary parse artifact in the
   deviations.
4. **H4** — reword "no copy"/`AR_DATA` to "no staging copy and no MLGym copy; `prepare_data.py` writes the prepared
   `houseprice.csv` from the author's `--from-file` source; the setup log/manifest records `provided_by` and
   `from_file_name`".
5. **H5** — add the static-test command/mask capture (or a launcher note with the exact command, `taskset`,
   `CUDA_VISIBLE_DEVICES=`, interpreter) and reconcile `report:75-82`.
6. **H6** — record which C1–C4 items are implemented in the launch/result records and amend the executed unit text
   for the remaining R2 MINOR residues (m2/m6/m7/m8/m9/m13/m14/m15/m16), or state explicitly that the launch notes
   are the operative form; keep the executed bytes preserved.
7. **H7** — record the cpuset-selection samples or reword to the captured before sample (80.0) and runner sample
   (97.4); reword the mid-sample interpretation.
8. **H8** — add the v1→v2 verifier fix as a patch or `scripts/README` (state the one-line change from the v1
   equality check to the full-64-hex canonical check) alongside the preserved v1 outputs.
9. **H9** — label the `s002` `NaN` sealed value as non-finite/not-used (or record `null`/string).
10. **H10** — restate that the corrected `PASS` block (fixed verifier + kit helper + summary) is authoritative over the
    first `STOP` block in `RESULT_STATUS.txt`/`DONE`.
11. **S1** — add a record-identity section with the result md's own path/sha (`c043f0dd…`), the `SHA256SUMS` sha
    (`80a83524…`), the E1–E4 diff shas, the one-JSON-line-per-run statement, and the canonical `node_spec_sha256`
    loader formula (or an explicit citation to `kit.txt`/`verify_full.json`).
12. **S2** — add the no-resume statement and name the filesystem (`/dev/md0p3` on `/`).
13. **S3** — cite the full 64-hex authority shas.
14. **S4** — reword "preserved read-only on Ada" to "preserved unaltered" and state what the live dir holds.
15. **S5** — correct "the verifier records both" and cite a source/capture for the 2.9 G data-root figure.
16. Recompute `SHA256SUMS` after any record-file edit and re-verify with `shasum -a 256 -c`; the result md's sha will
    change, so the census/commit must use the regenerated value and state it (the current value is `c043f0dd…`).

## 9. Census-row support

The result supplies, for one node only and ENGINEERING_ONLY, what the census row needs: node `mlgym_houseprice`
(MLGym, CPU; `regressionKaggleHousePrice`); **committed-file pin `88d359f2c59449a5c49d75d40fedd72436f76154e78b622f8c69b384a1d5a654`**
(census value) and deployed pin **`4cbbc5d6673d1e0cff15e1df4ea6dfe6941ac028b68109f1b86849ab9e36a144`** (separate);
**B1 5.059 s / `val_rmse` 23344.767385 (`AR_METRIC`) / sealed `test_rmse` 30295.671017 (`AR_TEST`, result channel)**;
B2 4.876 s identical; **derived node timeout 15.177 s**; whole-smoke CPU/RAM aggregate (user 47.60 s, sys 8.35 s,
max RSS 599,392 kB); disk before/after above the 50 GiB floor; gate JSON+UTC; effective isolation on every executed
record; 8 executed + refused `s001`; `CHECKLIST_E_PASSED`; author CSV sha256/md5 + `--from-file`; one-node/
no-evidence/no-noise/T1 statements. The census row must carry the licence/provenance line (CC BY-NC 4.0; Kaggle terms;
no MLGym copy; gymnax-derived Apache-2.0 parts not used), the CPU co-tenancy caveat (H3), and the H1–H10/S1–S5 record
corrections. **The result supports the row; writing/committing the row is outside this review.**

## 10. Attestation and command record

This review is the only file written (uncommitted). I ran no smoke/U2/census job, no GPU work and no re-run; I did not
edit a unit/code/record, did not commit/push/delete anything, did not touch HTCondor/deepthought/TASL-7/TASL-2, and
made no write on Ada. Read-only operations (20 November 2026, Europe/Berlin; Ada clock ~21:59–22:10 UTC):
`pwd`/`git rev-parse` (HEAD `6bbf4b3e`, branch `ops-tasl-20261116`, `origin/main` `df58bcd5`, merge-base `94db94bb`)/
`git status` (only the four untracked items); local `shasum -a 256 -c SHA256SUMS` (445/445 OK, rc 0) and `sha256sum` of
the report/`SHA256SUMS`/unit/reviews; `shasum -a 256` of every capture and `record_hashes.txt` (25/25); reads of the
result md, the executed unit, both unit reviews, the kit-update report/review, the five-node/Breakout result reviews,
`run_node_houseprice.sh`/`verify_u2_records_cpu.py`, `invocation_inner.sh`, and every capture; recomputation from
`runs/…/{run_record.json,run.log,result_channel.txt}` (table in §4), `smoke_ledger.jsonl`, `verify_*.json`,
`summary.json`, `cpu/*` and `disk_*`; live Ada (`ssh -o BatchMode=yes experiment_zhixu`, `ucrtasl`, user `dowling`,
read-only): `hostname/date/uname -r/nproc/boot_id` (kernel `5.15.0-151-generic`, 96 CPUs, boot id
`5c90a8fe-5f9b-4914-a2c7-5b864e0a8b8d` — matching `host.txt`), the kit `git rev-parse/symbolic-ref/diff-index/
diff-files/ls-files` (+`sha256sum` of the node spec, rep-edit manifest, frozen files, `LICENCES.md`,
`requirements.txt`, `pins/new_mlgym.json`), read-only Python with the kit's own loader/isolation
(`load_trackg_node_spec` → `raw_sha256 2f150cde…`; `isolation.frozen_file_hashes` → 16/17-entry pins
`88d359f2…`/`4cbbc5d6…`), the author CSV (`sha256sum`/`md5sum`/`stat`/`wc -l`/head/tail), the prepared data dir
(manifest, perms, inodes, node link), the evidence dirs (417 files; attempt-1 `runs/`/`gate/` empty), the live
`scripts/` shas (`360b2053…`, `63a4bdf1…`), the verifier output shas/mtimes, and a full `find`+`sha256sum` of the live
capture (417/417 byte-identical to the local `SHA256SUMS`) and of the live attempt-1 dir (22/22 byte-identical to the
local copies). No live-host state is claimed beyond these read-only results.
