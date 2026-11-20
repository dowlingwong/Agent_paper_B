# Independent review — Track G G.0 U2 unit `mlgym_houseprice` (isolated kit, CPU) (20 November 2026)

**Reviewer.** Fresh independent reviewer (`u2-houseprice-reviewer`), delegated by the coordinator; no involvement in
drafting the unit, the kit update, the five-node U2 campaign, the Breakout unit or its review. Read-only: the only file
written is this review record (uncommitted). No unit/code edit, no commit/push/delete, no run/GPU/U2/census job, no Ada
login, no HTCondor/deepthought. One **read-only shallow clone of the published harness kit branch** was made under
`/tmp/u2review/harness_mlgym` (network read only; nothing written inside either repository) to verify the kit tip, the
node spec, the frozen files and the pins.

**Object under review.** `docs/r1/proposals/u2_iso_20261119/U2_ISO_MLGYM_HOUSEPRICE_UNIT_20261120.md`, sha256
**`d45b4431277fa870ff40b47a2f6aa20240ed0bc5a3babd2ffdf9ed5890eb9478`**, **61 lines**, untracked at review time
(mtime `2026-11-20T22:29:00`); status "proposed unit; run only after a fresh independent review accepts it".

**Verdict summary: NOT ACCEPTED — 0 BLOCKING, 1 MAJOR, 16 MINOR.** The unit is a largely correct one-node CPU U2
unit at the accepted-pattern level: one node only, ENGINEERING_ONLY, the author Kaggle `train.csv` hash/md5 with the
correct prefix/suffix read directly through `AR_HOUSEPRICE_TRAIN_CSV` and the spec's `--from-file` setup, the kit tip
`f07875de…`, the CPU environment `envs/torch312`, the inside-scope cgroup construction with the
`memory.max=8589934592` / `memory.swap.max=0` probe and a one-line `--memory-limit` value, runs-root outside the
repository, `--provisional-timeout 1800`, B1/B2 `val_rmse` + sealed `test_rmse`, one fit (`steps 1`), 8 executed +
refused `s001`, the 3 × B1 node-timeout and a result/STOP skeleton of the accepted class are all present and
independently checked below. The **MAJOR is one hardcoded value**: the unit asserts the committed-file pin
**`eb60107e…`, which is `mlgym_fmnist`'s committed pin**; at kit tip `f07875de…` this node's committed-file pin is
**`88d359f2…`** (accepted kit update §3/§9/§10.2, `pins/new_mlgym.json`, and my independent recomputation). That is the
round-2 M5 defect class (a hardcoded, wrong pin that the census would commit as this node's code-state identity), and
the unit also contains a hardcoded pin where the accepted convention forbids hardcoding either pin. The MINORs are
record/command-text gaps of the accepted R3/RAWCOST classes: an unrecorded author-file provenance and a path that
differs from the recorded author-instruction path, an over-precise "source path" claim about the data manifest, the
source-wrapped launch command, missing static-test and launch-check requirements, and an incomplete result-field list.
**Do not execute this revision.** Conditions C1–C6 below; C1 is the MAJOR fix, C2–C5 are mandatory pre-execution/record
conditions, C6 is the execution rule. The other conditions change no procedure, scope, measurement identity, STOP set
or kit byte.

## 1. Authority, method and limits

**Authority read** (all read-only; full shas as verified in this session):

- The delegation names published main **`de3de54fd22dcdd86215be0924307e36a64ed08b`** as the authority baseline. The
  worktree's `origin/main` has since advanced by two docs-only commits to
  **`94db94bb5c0f4061cc111fdbfb719f6d18e6e9be`** (`3a6dcf4d` review/prompt; `94db94bb` author decisions 20 Nov); the
  worktree HEAD is **`6bbf4b3e`** (`ops-tasl-20261116`), merge-base with `origin/main` = `94db94bb`. The cited rows are
  unchanged: `R1-TRACKG-G0-GO` (`origin/main:docs/r1/PLAN.md:1258`), `R1-TRACKG-LICENCES` (`:1269`),
  `R1-TRACKG-PORT-DECISIONS` (`:1289`), `R1-HARNESS-ISOLATION` (`:1290`); the 20 November row `R1-TRACKG-G3-EARLY`
  (`:1330`) explicitly expects `mlgym_houseprice` to join T1 "as soon as their U2 passes" — the purpose of this unit.
- Port report `origin/main:docs/r1/reports/TRACKG_PORT_ISOLATION_20261117.md` §2 (how every node runs) and §7 (steps
  for the experiment agent), `origin/main`-present; its review `docs/r1/reviews/TRACKG_PORT_ISOLATION_REVIEW_20261117.md`
  (round 4 ACCEPTED; round-1 M1/M2 fixed in round 2; "House Prices runs without `--gpu-uuid`").
- Accepted kit update report `docs/r1/reports/trackg_g0_20261117/TRACKG_ISO_KIT_UPDATE_20261119.md`, sha256
  **`fe232e2bbf236337e208f11e97c809f8a41d7ef101567eeb0d11153bacb9d026`** (committed at worktree HEAD; reviewed bytes
  `3c3ae74a3788e86f0645e316b7c66392ac8bec45c01b8e0a5f4ed26a01f04bd7`, conditions C-K1…C-K5) and its review
  `docs/r1/reviews/TRACKG_ISO_KIT_UPDATE_REVIEW_20261119.md`, sha256
  **`d8c68f9f0463d1aa3e17f82527dfb7ecf7b6070831584cd1024a6d39ed6a21b4`**, ACCEPTED (0 BLOCKING / 0 MAJOR). Captures:
  `SHA256SUMS` verified **341/341 OK, rc 0**; `pins/new_mlgym.json` sha256 `8974359b…`, `pins/deployed_mlgym.json`
  sha256 `dcfcb080…`.
- Harness-isolation fix review `docs/r1/reviews/HARNESS_ISOLATION_FIX_REVIEW_20261119.md`, sha256 `c8e468c7…` (ACCEPTED;
  C3 keeps the autoresearch U2 GPU run blocked) and host-check report `docs/r1/reports/trackg_g0_20261117/
  HARNESS_ISOLATION_HOST_CHECK_20261119.md`, sha256 `6a700509…` (records the env interpreters as Python 3.12.16).
- Accepted prior U2 pattern and standards: five-node units + R3 review `docs/r1/reviews/
  TRACKG_U2_ISO_UNITS_REVIEW_R3_20261119.md`, sha256 `99daf16d…` (ACCEPTED; mR1–mR10 and the
  `do not hardcode either pin` convention); Breakout unit + review (`docs/r1/reviews/
  TRACKG_U2_ISO_BREAKOUT_UNIT_REVIEW_20261119.md`); and the prior raw-cost review
  `docs/r1/reviews/TRACKG_U2_RAWCOST_REVIEW_20261117.md` whose **MAJOR-5** is the House Prices setup/`--from-file`
  requirement and whose **MINOR-1/3/4/5** are the static-test, B1-basis, timeout-classification and disk-budget
  conditions for this node.

**Method and limits.** Paper review plus independent recomputation from the published kit. I confirmed the kit branch
`mac-trackg-iso-mlgym-20261117` on the harness origin (`github.com/dowlingwong/autoresearch_harness`) at
**`f07875de79a5a57739227b13e0fd52d31646edaf`** by `git ls-remote --heads`, then shallow-cloned it read-only and read the
node spec, `prepare_data.py`, `run_fixed_budget.py`, `LICENCES.md`, `requirements.txt`, the frozen-file list and the
campaign code. I recomputed both pin roles from the tip's own bytes and cross-checked my recomputation method against
the captured `pins/deployed_mlgym.json` and `pins/new_mlgym.json` (it reproduces `817c9034…`/`2d7e533b…` and
`ef804338…`/`eb60107e…` exactly, and the stored houseprice committed pin `88d359f2…`). I did **not** log in to Ada and
claim no live-host state: the author file's presence/bytes on Ada, the Paper A gate, the CPU co-tenancy and the kit
worktree state at launch are not independently verified here; the unit's launch checks and conditions below must
capture them.

## 2. Authority and scope — PASS (MINOR residues)

`unit:3-9` carries the correct authorities (`R1-TRACKG-G0-GO`, `R1-HARNESS-ISOLATION`,
`R1-TRACKG-PORT-DECISIONS` (2), port report §2/§7, the accepted kit-update report + reviewed-bytes convention), and
`unit:3` names **one node only** (`mlgym_houseprice`). ENGINEERING_ONLY census, "no evidence/noise/D21/D28", "no T1",
"no HTCondor/deepthought", "no deletion", "no force push" and "no cross-node pooling" are all present. No U3/unisolated
pre-run baseline is claimed (`unit:47`), and no other node/host is authorised. This matches `R1-TRACKG-G0-GO`, port
report §7 and the accepted five-node/Breakout scope.

Residual MINORs are the accepted mR10/mR13 residues: "no force push" rather than "no push"; no explicit "no other
host" beyond HTCondor/deepthought; no no-resume statement; no explicit exclusion of autoresearch (C3-blocked),
Breakout or the other census nodes; the STOP set lacks "other users would be disturbed" and env-freeze mismatch; and
the authority block does not cite the kit-update **review** path/sha, `R1-TRACKG-LICENCES`, `R1-TRACKG-G3-EARLY`, or
the 19 November follow-up instruction that defines this node's path (unit → independent review → one smoke → result
review) (`docs/r1/prompts/FOLLOWUP_PROMPTS_20261119.md:26`, `docs/r1/prompts/EXPERIMENT_AGENT_PROMPT_20261118.md:55`).
Finding **m13**, **m15**.

## 3. Author `train.csv` — PASS on the hash/path/no-copy rule; MINOR record gaps

**Hash values — correct and consistent.** `unit:14-16` gives full sha256
**`1e18addf81e5e4d347cc17ee6075bbe4a42b7fa26b9e5b063e8f692a5f929d41`**, prefix `1e18addf`, suffix `929d41`, and md5
**`80ccab65fb115cbad143dbbd2bcd5577`**. These are exactly the values recorded for the table in the accepted records
(`nodes/mlgym_houseprice/LICENCES.md:36`, `run_fixed_budget.py:34` `MLGYM_COPY_SHA256`, `TRACKG_U3_PORT_MLGYM_20261117.md`,
`TRACKG_U3_PORT_MLGYM_REVIEW_20261117.md`), and the prefix/suffix are correct (the earlier `…5929d41` typo in the U3
report is not repeated). "size 450 K, 1,461 lines" is consistent with 460,676 B and 1,460 rows + header. **Important
identity nuance:** the author file's hash is *identical* to MLGym's forwarded copy; that is expected if the user
downloaded the same Kaggle table, but it means the hash alone cannot prove "no MLGym copy" (port report §2(2): the
`same_as_mlgym_copy=` comparison is "for information only"). The unit should say so and record the proof path (below).

**Path / `--from-file` — correct in form.** `unit:13, 23-25` uses the path
`/home/dowling/house-prices-advanced-regression-techniques/train.csv` directly in `AR_HOUSEPRICE_TRAIN_CSV` and passes
it to the spec's setup through `prepare_data.py --out "$AR_TRACKG_DATA_ROOT/mlgym_houseprice" --from-file
"$AR_HOUSEPRICE_TRAIN_CSV"`. That matches the kit tip's `setup_command`
(`third_party/mlgym/configs/trackg/nodes/mlgym_houseprice.yaml:33`: `test -n "$AR_TRACKG_DATA_ROOT" && test -n
"$AR_HOUSEPRICE_TRAIN_CSV" && python3 prepare_data.py --out "$AR_TRACKG_DATA_ROOT/mlgym_houseprice" --from-file
"$AR_HOUSEPRICE_TRAIN_CSV"`) and port decision (2) / port report §2(2), §7 step 2. There is **no MLGym copy** in the
setup, and the parent refuses a manifest whose `source.provided_by` is not a user download
(`run_fixed_budget.py:49-52,53-54`); the unit's "hash mismatch STOP" (`unit:15-16`) matches the prior review's
requirement (`TRACKG_U2_RAWCOST_REVIEW_20261117.md` MAJOR-5).

**MINORs.** (a) **m1** `unit:11-16`: "verified" has no provenance/verification record, and the path differs from the
recorded author-instruction path `~/r1_inputs/house-prices/train.csv` (`FOLLOWUP_PROMPTS_20261119.md:26`,
`EXPERIMENT_AGENT_PROMPT_20261118.md:55`; kit update §9 records it absent — `/home/dowling/r1_inputs` did not exist),
so the location change must be recorded (author placement date/quote, host, `sha256sum`/`md5sum`/`stat` output,
bytes and mtime, download date, Kaggle competition URL). (b) **m2** `unit:25-26`: "confirm … the source path/hash
appear" is imprecise — the manifest's `source` records `{kaggle, provided_by: "user download, passed with --from-file",
from_file_name (basename only), sha256, md5, rows}` and **no source path** (`prepare_data.py:88-93`); the required check
is that `source.provided_by` starts with "user download", `source.sha256` equals the file digest, `md5` is present and
no `synthetic` key/marker exists, plus recording the manifest sha256 and the run's
`AR_DATA houseprice_sha256=… md5=… same_as_mlgym_copy=…` line (`run_fixed_budget.py:53-54`) and the exact
`--from-file` path used. (c) **m3** `unit:23-27`: the setup re-statement drops the spec's `test -n` guards, does not
say to run from the node directory with `envs/torch312/bin` first on `PATH` (the shape check imports pandas), and does
not say to move aside an old/other-source `$AR_TRACKG_DATA_ROOT/mlgym_houseprice` (port report §7; port review M1;
prepare_data refuses a non-empty dir without a manifest, `prepare_data.py:70-74`).

## 4. Kit identity, pins, licence, CPU/env/isolation

**Kit identity/tip — correct.** `unit:20-21` gives `mac-trackg-iso-mlgym-20261117` @
`f07875de79a5a57739227b13e0fd52d31646edaf`; the harness origin's branch head is exactly that commit and the shallow
clone's HEAD is it. The tip is the post-fix, post-pin commit ("… frozen pins updated") the accepted kit update §2/§7
names (`mlgym f07875d`), so the unit is on the right bytes.

**Committed-vs-deployed pin convention — present, but the value is wrong (MAJOR M1).** `unit:21-22` states the
convention correctly ("committed-file pin … and deployed run-record pin recorded separately, census uses the
committed one") but then hardcodes **`eb60107e…`** as the committed pin. At tip `f07875de` the node's committed-file
pin is: take its 16 frozen entries from the spec's `frozen_paths` (`run_fixed_budget.py`, `ar_worker.py`,
`ar_parent.py`, `ar_isolated.py`, `ar_data.py`, `prepare_data.py`, `requirements.txt`, `LICENCES.md`,
`representative_edits/**`; `data/` absent), hash each regular file (symlinks by target), then
`sha256(json.dumps(files, sort_keys=True))` =
**`88d359f2c59449a5c49d75d40fedd72436f76154e78b622f8c69b384a1d5a654`**. This equals the accepted kit update §3 table
row `mlgym_houseprice` ("new pin"), §9 ("The node's pin was updated (`88d359f2…`)") and the captured
`pins/new_mlgym.json` houseprice pin. My method reproduces the captured cifar/fmnist committed and deployed pins
exactly, so the recomputation is sound. `eb60107e…` is the **`mlgym_fmnist`** committed pin (kit update §3 row
`mlgym_fmnist`; `pins/new_mlgym.json`; the five-node ISO results table), i.e. the unit copied the wrong node's value
from the template. If followed, the census would commit fmnist's pin as houseprice's code-state identity — the exact
census-integrity failure the round-2 M5 review fixed. It is also a hardcoded pin, which the accepted convention
forbids ("do not hardcode either pin in this unit", kit update §10.2; R3 mR3). The deployed pin for this node will be
the 17-entry value including `data: link:<absolute target>`; with the unit's data root the expected value is
**`4cbbc5d6673d1e0cff15e1df4ea6dfe6941ac028b68109f1b86849ab9e36a144`** (I recomputed it from the tip bytes + the
expected link target `…/data/mlgym_houseprice`); it must be recorded from the actual run records, and only the
committed pin is the census value.

**Licence — PASS with a citation residue (m12).** `unit:28-30` records the MLGym task `regressionKaggleHousePrice`
CC BY-NC 4.0 non-commercial with attribution and changes in `LICENCES.md`, the Kaggle competition terms, "only
`train.csv`", "no MLGym copy" and "record both". This matches the node spec
(`external_benchmark.license: CC-BY-NC-4.0 …`, `yaml:90`) and `LICENCES.md:11-19,30-36`. Residue: it does not cite
`R1-TRACKG-LICENCES` (R3 mR8b) and does not state that the gymnax-derived Apache-2.0 parts are not used by this node
(the accepted MLGym units carry that sentence; true here as well), and the result "licence" field is vague — add the
census row/appendix duty.

**CPU node and environment — correct.** `unit:27, 32, 44` says CPU node, `envs/torch312` (Python 3.12.16,
scikit-learn/pandas), no GPU and no `--gpu-uuid`. The kit agrees: `tests/trackg/port_smoke_gpu.py:27`
`CPU_ONLY_NODES = frozenset({"mlgym_houseprice"})` and `:59-60` makes `--gpu-uuid` optional only for that node; the
spec's `notes.python_env: torch` is "scikit-learn and pandas only; no GPU use" (`yaml:94`), and its
`requirements.txt` pins `numpy==2.5.4 pandas==3.1.1 scikit-learn==1.9.1`, which are exactly the versions in the
accepted `envs/torch312` freeze (Python 3.12.16; `pytest==9.2.0`, `pyyaml==6.0.3` present, so the smoke entry imports).
Residual **m16**: no launch-time import/env check or env-freeze mismatch STOP is required.

**Isolation — requirement correct.** `unit:31, 51` requires every executed record `isolation.effective:true`,
`waivers {}`, `exceptions []`, and its STOP list makes a non-effective record a STOP. The node spec's `isolation`
block has no exception (`yaml:37-39`) and the accepted five-node records show these are achievable on this host; the
unit is right to require them. Residual **m11**: the list omits `log_intact`, the result channel, `cgroup.kill` and
the explicit "any executed record not effective / with waivers or exceptions = STOP" wording.

## 5. Command, cgroup, timeout and record

**Inside-scope cgroup and probe — PASS.** `unit:36-45` is the accepted construction: the outer
`systemd-run --user --scope -p Delegate=yes -p MemoryMax=8G -p MemorySwapMax=0 -- bash -c '…'`, with `CG` and
`AR_TEST_CGROUP_PARENT=/sys/fs/cgroup$CG` computed **inside** the scope, `echo scope_cgroup=…`, `cd <kit worktree
root>`, `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1`, the env `bin` first on `PATH`, `VIRTUAL_ENV`,
`CUDA_VISIBLE_DEVICES=""`, `taskset -c <cpus>`, the `--memory-limit` **value on one physical line** ("external:
systemd-run … (enforced cgroup)"), the expected probe bytes `8589934592` / `0` with "mismatch STOP", and
`--runs-root <outside-repo>/…` with `--provisional-timeout 1800`. This fixes R3 mR1(a)–(e) in substance (the accepted
`smoke_one.sh:26-39` and the accepted records' `limits.external_limit` match). Residual **m4**: the block is
source-wrapped inside the single-quoted `bash -c` script (line breaks after `export`, and between `--cpus`,
`--memory-limit`, `--runs-root`); a literal copy runs `export` alone (so `AR_TEST_CGROUP_PARENT` is not exported →
`no_cgroup` waiver → `effective:false` → STOP) and makes `--memory-limit`/`--runs-root` separate commands. The amended
accepted units state the launch command on one physical line (cifar10 unit `:38`; breakout unit `:53-55`). Residual
**m5**: `$AR_TEST_CGROUP_PARENT` is set only inside the scope, so the probe must be read via the echoed
`scope_cgroup=` path (or inside the scope while the smoke runs); say when/how. Residual **m16** (above) and **m14**:
the launch check should be spelled out (`git rev-parse HEAD` == `f07875de…` **and** `git status --porcelain
--untracked-files=no` empty, the expected untracked runtime `data` link permitted) and recorded (`kit.txt`); the
accepted breakout review's M-5.

**Timeout / B1/B2 — correct basis, MINOR wording (m8).** `unit:47-49` records "pre-run reference: none accepted (this
is the first HousePrice isolated run)" (correct: the kit-update smoke was a STOP, §9), B1/B2, `val_rmse`
(`outcome.value` — the spec's `metric_name: val_rmse`, minimize, `yaml:41-44`) and sealed `test_rmse`
(`test_metric_regex: ^AR_TEST test_rmse=…`, `yaml:47`; `test_scored: true`, `:59`), one fit (`steps 1`; `yaml:50-52`;
`run_fixed_budget.py:39` `read_budget("steps", exact=1)`), and "node timeout = 3 × B1; provisional 1800 s; no
timeout/OOM retry" (port decision (4); the accepted records' `timeout_factor: 3.0`,
`provisional_timeout_seconds: 1800.0`). Residual MINORs: define B1 as `s000_baseline`'s
`elapsed_seconds_info_only`, say B2 is the same-seed repeatability baseline only (prior RAWCOST MINOR-3), state that a
timeout/OOM is reclassified as the proposal's failure (port decision (4); prior RAWCOST MINOR-4), and optionally cite
the U3 unisolated run's informational `AR_TEST test_rmse=30340.111853` (MLGym's copy, not an accepted reference).

**Gate / CPU co-tenancy — present, MINORs (m6, m7).** `unit:31-32` requires the Paper A gate "clear_finished, key
false, no Paper A process" immediately before launch and CPU/load recording without disturbing users. It does not give
the exact command/criteria/capture (accepted pattern `paper_a_status.py --config
r1/scripts/configs/paper_a_status_ada.json`; `paper_a_live_waiting_for_card: false`; `paper_a_processes: []`; JSON
path/sha/UTC; R3 mR5/breakout M-8), nor the idle-CPU-set choice, load threshold, before/mid/after snapshot and a
"disturbed = STOP" rule (the GPU analogue mR9). The unit does correctly require `time -v`, the CPU before/mid/after
snapshot, the memory cap and disk in `unit:46`.

**No pre-recorded static test — MINOR (m9).** Neither the run nor the result list requires the CPU-masked static-test
that the accepted workflow records before a run (cifar10 unit `:26-27`; R3 mR4; prior RAWCOST MINOR-1: per worktree
`pytest tests/trackg/test_port_mlgym.py -k "not smoke"` with the command/result/mask/interpreter/log sha). This node's
synthetic smoke path is exercised by the same module, so the check is cheap and expected.

**Result record — PARTIAL (m10, m12, m17).** `unit:50-55` requires B1/B2 elapsed+rmse+test_rmse, all edit outcomes,
`CHECKLIST_E_PASSED` + 8 executed + refused `s001` (verified from `port_support.run_smoke`/`check_smoke`: baseline,
frozen-diff refused, broken diff, first edit, E1–E4, B2 = 8 executed + refused `s001`), isolation fields, cgroup probe,
CPU/load census, gate JSON+UTC, host/kernel, env freeze, data manifest + source csv sha256/md5, kit tip + both pins,
licence, disk, executed amended unit copy, captures + `SHA256SUMS`. It omits accepted-standard fields: per-run
`run_record.json`/`run.log` paths+sha256, `process.killed_with`/`returncode`/`timed_out`,
`determinism.not_forced`/`shim_loaded`, the node spec path+sha and every record's `node_spec_sha256`,
the representative-edit manifest sha, one JSON line per run / the ledger, the sealed-value source (`AR_TEST
test_rmse` in `result_channel.txt` — the manager view never carries `sealed`), the result-file name/path/sha, the
result directory (`docs/r1/reports/trackg_g0_20261117/u2_iso_mlgym_houseprice_<UTC>/`), host/boot/kernel/driver,
data-manifest file count/size/read-only bit, `du`/`df` before/after, the 100 GiB cap, and the cgroup-kill/log-intact
fields (R3 mR4/mR6; RAWCOST MINOR-5; accepted result layout). The STOP set (`unit:53-55`) is good but is missing the
env-freeze mismatch, "other users would be disturbed", and an explicit "any executed record not effective" item
(m15).

## 6. Findings (file:line against `unit:NN`)

| ID | Severity | Unit lines | Finding |
|---|---|---|---|
| **M1** | **MAJOR** | `unit:21-22` | The committed-file pin is hardcoded **and wrong**: `eb60107e…` is `mlgym_fmnist`'s committed pin; the `mlgym_houseprice` committed-file pin at tip `f07875de` is **`88d359f2c59449a5c49d75d40fedd72436f76154e78b622f8c69b384a1d5a654`** (accepted kit update §3/§9/§10.2; `pins/new_mlgym.json`; independently recomputed from the tip's 16 frozen entries). Hardcoding either pin is forbidden by the accepted convention (kit update §10.2; R3 mR3/C-K5). If followed, the census commits fmnist's pin as this node's code-state identity. Remove the value; require deriving the committed pin from the kit (§3 / `pins/new_mlgym.json`, expected `88d359f2…`) and the deployed pin from the run records (17 entries incl. `data: link:`; expected `4cbbc5d6…` if the unit's data root/link target is used), record both full 64-hex values, census uses the committed one. |
| m1 | MINOR (mandatory before run) | `unit:11-16` | Author-file provenance/verification is not recorded, and the path differs from the recorded author-instruction path `~/r1_inputs/house-prices/train.csv` (19 Nov follow-up; kit update §9 STOP). Record the author placement (date/quote), the host verification (`sha256sum`/`md5sum`/`stat`, bytes, mtime), the download date and the Kaggle competition URL; state that the hash equals MLGym's copy and is informational only (port report §2(2)). |
| m2 | MINOR (mandatory) | `unit:25-26` | "Source path/hash appear" is wrong/imprecise: the manifest has no source path (only `kaggle` URL, `provided_by`, `from_file_name` basename, sha256, md5, rows). Require the `provided_by`-starts-with-"user download" and source-hash checks, the manifest sha256, the `AR_DATA houseprice_sha256=… md5=… same_as_mlgym_copy=…` line and the exact `--from-file` path used. |
| m3 | MINOR (mandatory) | `unit:23-27` | Setup re-statement drops the spec's `test -n` guards and the execution context (node dir; `envs/torch312/bin` first on PATH; setup log path+sha; move aside an old/other-source data dir — port report §7, port review M1). |
| m4 | MINOR (mandatory before run) | `unit:36-43` | The launch command is source-wrapped inside the single-quoted `bash -c` script; a literal copy runs `export` alone (no `AR_TEST_CGROUP_PARENT` export → `no_cgroup` waiver → `effective:false` → STOP) and splits the smoke's argument list. Give it as one physical line (amended accepted units). The `--memory-limit` value itself is one line (good; R3 mR1(e) avoided). |
| m5 | MINOR | `unit:44-45` | The probe read path is ambiguous: `$AR_TEST_CGROUP_PARENT` exists only inside the scope; read via the echoed `scope_cgroup=` path (or inside the scope while the smoke runs) and say when/how. Expected `8589934592`/`0` and mismatch STOP are present. |
| m6 | MINOR (mandatory) | `unit:31-32` | Paper A gate too vague: give the exact command (`paper_a_status.py --config r1/scripts/configs/paper_a_status_ada.json`), the three criteria (`clear_finished`; `paper_a_live_waiting_for_card: false`; `paper_a_processes: []`) and the captured JSON path/sha/UTC immediately before launch (R3 mR5; breakout M-8). |
| m7 | MINOR | `unit:31-32` | CPU co-tenancy too vague: choose/record the idle CPU set (`<cpus>`), a load threshold, before/mid/after snapshots and a "disturbed = STOP" rule; state the 8 GiB cgroup basis (accepted mR9 analogue; the 8 GiB cap is itself fine and is the accepted `MemoryMax=8G`). |
| m8 | MINOR | `unit:47-49` | Define B1 = `s000_baseline`'s `elapsed_seconds_info_only`; say B2 is the same-seed repeatability check only; state a timeout/OOM is reclassified as the proposal's failure (port decision (4); RAWCOST MINOR-3/4); the U3 unisolated `test_rmse=30340.111853` may be cited as informational only. |
| m9 | MINOR (mandatory) | `unit:26-27` vs `unit:50-55` | No CPU-masked static-test requirement before the run (R3 mR4; RAWCOST MINOR-1: per-worktree `pytest tests/trackg/test_port_mlgym.py -k "not smoke"`), with command/result/mask/interpreter/log sha. |
| m10 | MINOR | `unit:50-55` | Result list omits accepted-standard fields: per-run record/log paths+sha256, `killed_with`/`returncode`/`timed_out`, `determinism.not_forced`/`shim_loaded`, node-spec sha (`node_spec_sha256`), representative-edit manifest sha, one JSON line per run/ledger, sealed-value source (`AR_TEST test_rmse` in `result_channel.txt`), result-file name/path/sha, result directory, host/boot/kernel, manifest file count/size/read-only, `du`/`df`, 100 GiB cap (R3 mR4/mR6; accepted result layout). |
| m11 | MINOR | `unit:51` | Isolation field list omits `log_intact`, result channel, `cgroup.kill`; add the explicit "any executed record not `effective:true` / with waivers or exceptions = STOP". |
| m12 | MINOR | `unit:28-30` | Licence line lacks `R1-TRACKG-LICENCES` and the "gymnax-derived Apache-2.0 parts are not used by this node" statement; the result "licence" field is vague; add the census row/appendix duty (R3 mR8b; port decision (1)). |
| m13 | MINOR | `unit:3-9` | Citation gaps: kit-update review path/sha (`d8c68f9f…`) not given; C-K5 omitted (the pin/push convention); no `R1-TRACKG-LICENCES`, `R1-TRACKG-G3-EARLY`, 19 Nov follow-up instruction, or authority main/commit (prior RAWCOST MINOR-2; R3 mR8). |
| m14 | MINOR | `unit:20-21` | Launch check imprecise: state `git rev-parse HEAD` == `f07875de…` **and** `git status --porcelain --untracked-files=no` empty (untracked runtime `data` link permitted) and record it (`kit.txt`) (breakout M-5). |
| m15 | MINOR | `unit:3-9`, `unit:53-55` | Scope/STOP residues: "no push" (not only "no force push"); no other host; no-resume; explicit exclusion of autoresearch (C3-blocked)/Breakout/other nodes; STOPs missing "other users would be disturbed" and env-freeze mismatch; disk stop without the 100 GiB cap/filesystem accounting; no "record the resolved invocation" (R3 mR10). |
| m16 | MINOR | `unit:27`, `unit:36-43` | No launch env/import check or env-freeze mismatch STOP: record `which python`, `python -c "import pandas, sklearn, numpy"` versions against the requirements pins (numpy 2.5.4 / pandas 3.1.1 / scikit-learn 1.9.1), the `uv pip freeze` sha and the comparison (breakout M-3/M-4 analogue; the torch312 freeze already contains those exact versions plus pytest/pyyaml). |

No BLOCKING finding. No other overclaim was found: the kit tip, task/metric/budget values, CPU-only path, isolation
requirement, hash/md5/size and the 8-executed expectation are all correct.

## 7. Conditions

The MAJOR is a text-value correction; it changes no procedure, scope, measurement identity, STOP set or kit byte.
**No execution until C1–C5 are applied to the unit/launch notes; C5–C6 must be satisfied in the result record.**

- **C1 (M1, mandatory; blocks acceptance).** Remove the hardcoded `eb60107e…`. Require the operator to derive the
  **committed-file `frozen_pin_sha256`** from the accepted kit update §3/§10.2 / `pins/new_mlgym.json` — expected
  **`88d359f2c59449a5c49d75d40fedd72436f76154e78b622f8c69b384a1d5a654`** (16 frozen entries at tip `f07875de…`) —
  and the **deployed run-record pin** from the run records after the `data` link (17 entries; expected
  **`4cbbc5d6673d1e0cff15e1df4ea6dfe6941ac028b68109f1b86849ab9e36a144`** with the unit's data root, else the actual
  value), record both as full 64-hex values, and commit the committed one in the census. Do not copy any pin from
  another node or from a truncated string.
- **C2 (m1–m3, mandatory before run).** Add the author-file provenance/verification record (placement date/quote,
  host, `sha256sum`/`md5sum`/`stat`, bytes, mtime, download date, Kaggle competition URL, the change from the 19 Nov
  `~/r1_inputs` path), the exact setup context (node dir; `envs/torch312/bin` first on PATH; the spec's `test -n`
  guards; setup log path+sha; move aside an old/other-source data dir), and the correct manifest/source checks
  (`provided_by` user download, source sha256/md5, no synthetic; record manifest sha256, the `AR_DATA` line incl.
  `same_as_mlgym_copy`, and the exact `--from-file` path).
- **C3 (m4–m6, m14, m16, mandatory before run).** One physical-line launch command (probe read via the echoed
  `scope_cgroup` path, expected `8589934592`/`0`, mismatch STOP); the exact Paper A gate command/criteria/JSON
  capture; the exact tracked-clean `HEAD == f07875de…` launch check recorded in `kit.txt`; and a launch env/import
  check with the freeze sha and a mismatch STOP.
- **C4 (m7–m9, m15, mandatory before run).** CPU co-tenancy rule (idle CPU set, load threshold, before/mid/after,
  disturbed = STOP, no switch); B1 defined as `s000_baseline` with B2 as the repeatability check and the
  timeout-is-a-failed-proposal reclassification; the CPU-masked static-test command/result/mask/interpreter/log sha;
  the scope/STOP additions ("no push", no other host, no resume, explicit node exclusions, env-freeze mismatch,
  other-users STOP, 100 GiB cap, resolved invocation).
- **C5 (m10–m12, m17, satisfied in the result).** The result record must carry the full accepted result/capture
  standard (per-run records/logs + shas, `killed_with`, `determinism.not_forced`, node-spec sha, representative-edit
  manifest sha, one JSON line per run, sealed-value source, result-file path/sha, host/boot/kernel, freeze, both pins,
  gate JSON+UTC, data manifest + `AR_DATA` line, disk before/after with the cap, cgroup probe, CPU census, isolation
  fields incl. `log_intact`/result channel/`cgroup.kill`, `CHECKLIST_E_PASSED` + 8 executed + refused `s001`,
  licence/provenance incl. `R1-TRACKG-LICENCES`, executed amended unit copy, `SHA256SUMS`), under
  `docs/r1/reports/trackg_g0_20261117/u2_iso_mlgym_houseprice_<UTC>/`, preserved (no deletion).
- **C6 (execution rule).** One smoke only for this node, no timeout/OOM retry; one node, no cross-node pooling;
  ENGINEERING_ONLY with no evidence/noise/D21/D28, no T1; no HTCondor/deepthought/other host; no deletion/push; a
  timeout/OOM or any non-effective executed record is a STOP, not an infrastructure re-run. Acceptance of this unit
  does not authorise autoresearch (C3-blocked), Breakout, any other node, a T1 label/sweep or a cross-node comparison.

## 8. Verdict

**NOT ACCEPTED — 0 BLOCKING, 1 MAJOR, 16 MINOR.** The unit's scope/authority, the author CSV hash/md5/prefix/suffix
and the direct `AR_HOUSEPRICE_TRAIN_CSV`/`--from-file` path, the kit tip `f07875de…`, the CPU-only `envs/torch312`
environment, the licence/terms statement, the inside-scope cgroup construction with the 8 GiB/0 probe, the one-line
`--memory-limit` value, runs-root outside the repository, `--provisional-timeout 1800`, the B1/B2 `val_rmse` + sealed
`test_rmse` metric, one fit (`steps 1`), the 3 × B1 rule and the 8-executed/refused-`s001` expectation are all correct
and independently checked. The unit is **not accepted** because the one hardcoded pin is the wrong node's committed
pin (`eb60107e…`, i.e. `mlgym_fmnist`; this node's is `88d359f2…`), which would corrupt the census code-state identity
and violates the accepted no-hardcode convention. C1 must be applied and the corrected unit re-reviewed before
execution; C2–C4 are the mandatory pre-execution text/record corrections and C5–C6 the result/execution rules. Except
for C1 these are the same MINOR condition classes the R3 five-unit and Breakout reviews accepted, so a revised unit
can be accepted quickly.

## 9. Attestation and command record

This review is the only file written (uncommitted). I did not run the smoke or any GPU/U2/census job, did not edit the
unit or any code, did not commit/push or delete any repository, unit, evidence or capture file, did not log in to Ada
and did not touch HTCondor or deepthought. Read-only operations (20 Nov 2026, Europe/Berlin): `pwd`/`git rev-parse
HEAD` (`6bbf4b3e`), `git rev-parse origin/main` (`94db94bb`), `git merge-base` (`94db94bb`), `git status --short`
(only the untracked unit), `git log`/`git show origin/main:docs/r1/PLAN.md` rows `R1-TRACKG-G0-GO:1258`,
`R1-TRACKG-LICENCES:1269`, `R1-TRACKG-PORT-DECISIONS:1289`, `R1-HARNESS-ISOLATION:1290`, `R1-TRACKG-G3-EARLY:1330`;
`sha256sum` of the unit (`d45b4431…`), the kit update report (`fe232e2b…`), its review (`d8c68f9f…`), the fix review
(`c8e468c7…`), the host-check report (`6a700509…`) and the R3 review (`99daf16d…`); `git show`/`grep` of port report
§2/§7 and its review, the kit update §3/§7/§9/§10 and the prior raw-cost review's House Prices MAJOR-5; `shasum -a 256
-c` in the kit-update captures (**341/341 OK, rc 0**) and `sha256sum` of `pins/new_mlgym.json` (`8974359b…`) and
`pins/deployed_mlgym.json` (`dcfcb080…`); `git ls-remote --heads` on `github.com/dowlingwong/autoresearch_harness`
(`mac-trackg-iso-mlgym-20261117` = `f07875de79a5a57739227b13e0fd52d31646edaf`) and a read-only shallow clone under
`/tmp/u2review/harness_mlgym` whose HEAD is that commit; reads of the clone's node spec, `prepare_data.py`,
`run_fixed_budget.py`, `LICENCES.md`, `requirements.txt`, `port_smoke_gpu.py`, `port_support.py` and `test_port_mlgym.py`;
Python recomputation of the `mlgym_houseprice` committed-file pin (`88d359f2…`, 16 entries) and of the expected
deployed pin (`4cbbc5d6…`, 17 entries), with the method validated against the captured cifar10/fmnist committed and
deployed pins; reads of the accepted five-node units, the Breakout unit/review, the prior raw-cost review, and the
accepted `u2_iso_mlgym_cifar10_20261119T035326Z` result/env freeze. No live-host state is claimed beyond what the
accepted records and the published kit branch show.
