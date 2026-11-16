# C3 B.1 e1 offline mechanism — sweep-1 dataset identity audit (R1-E1-OPENML)

**Label: ENGINEERING_ONLY. Verdict: STOP — "identity unprovable".** Author row **R1-E1-OPENML**
(`docs/r1/PLAN.md` @ `025bfc16`, §10, line 1223) authorizes an independently reviewed e1 offline
mechanism **only if** the six OpenML datasets can be proven identical to the sweep-1 datasets by the
identity **sweep 1 recorded**. This audit finds that sweep 1 recorded OpenML **data ids** and a
**loaded-data fingerprint** for the six nodes, but **no md5/sha256 of any OpenML data file or cache
tree**. Requirement (a) is therefore unsatisfiable from sweep-1 records: **identity is unprovable.**
No mechanism, module, wiring or test was written (no fabrication); the driver's OpenML hard STOP is
untouched; no e1 run, no B.2, no labels, no job and no write on deepthought/ceph was made.

- **Authority:** row R1-E1-OPENML @ `025bfc16477a3911ea461d7a6cfc85f3ea523d66`; basis e1 STOP report
  `ops-e1-replay-20261116` @ `fc7d8e4e`, independently reviewed **ACCEPTED**
  (`docs/r1/reviews/E1_REPLAY_REVIEW_20261116.md`); e1 authorization
  `docs/r1/authorizations/c3_env_replay_20261116.md` @ `4da73306`; predeclared protocol
  `docs/r1/proposals/C3_ENV_RECONSTRUCTION_REPLAY_DRAFT_20261028.md`.
- **Branch / base:** `e1-openml-20261116` from `origin/main` = `025bfc16` (the check found
  `origin/main` one commit past `9a74bf19`, at the authorization commit itself; `9a74bf19` is its
  parent). Driver `r1/scripts/c3_env_replay.py` is byte-identical at `5ef9db16`, `origin/main` and
  this branch: SHA-256 `a9cad4d544bdf061c42ecb4b4c2d3d10d8bc94342574d9a37489bd4b179aa7d8`.
- **What is delivered:** this report plus the machine-readable evidence record
  `OFFLINE_MECHANISM_AUDIT.json` (same directory). No code change; `git diff origin/main..HEAD` adds
  documentation only.

## 1. What the row requires, and what "provable" means here

The row (verbatim, Chinese):

> **授权补一个独立审查的 e1 离线机制，接入 `r1/scripts/c3_env_replay.py` 的运行路径：(a) 证明六个 OpenML 节点所用数据集与 sweep 1 精确一致（以 sweep 1 记录的身份为准）；(b) worker 子进程无网络、不得下载。** 若 sweep 1 未记录可用于证明身份的数据集哈希，则报告"身份不可证"，由作者另行决定：只重放 4 个非 OpenML case 是否足够，或对 R1-MAIN-PROPOSER (g)2 开例外。e1 的零容忍 pass rule 与离线 STOP 不变。

Reading applied:
- "Provable" means **the identity sweep 1 recorded**, i.e. a hash value written *at sweep-1 time*
  into a sweep-1 artifact (the frozen corpus, its manifests/ledgers, the launch/index provenance, or
  the preserved batch for that launch) and a binding from that record to the six nodes / 16 replay
  cases.
- A hash computed **now** from a surviving cache copy is *not* such a record: it cannot show the
  bytes were the same on 27 October 2026. The row authorizes no weaker standard, and this audit did
  not invent one. (Section 5 lists a weaker route strictly as an author option, not as this
  mechanism.)
- Requirement (b) (worker network denial) is not reached: the mechanism applies only when (a) holds.

## 2. Method

Read-only. No execution of e1, no driver run, no job, no deepthought write. Evidence came from:
1. the committed sweep-1 corpus on `origin/main` (index, sidecar, the two frozen Git trees, root
   records, root ledgers, the archived patch/log provenance, the native manifests);
2. the preserved batch `/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw`
   on deepthought, read one-off over SSH (`dwong@deepthought.etp.kit.edu`) with read-only commands
   only (`ls`, `stat`, `sha256sum`, `git status/ls-files`, a read-only Python tree-digest read);
3. the pinned harness checkout inside that batch at `6adf3859de66c4814fcf376eed59880fbd8eeaf7`
   (NodeSpecs, `dataset.json`, `benchmark.py`, the six `data_cache` trees — read only);
4. the repository documents that could reference data identity (B.1 corpus-freeze and offline-loader
   documents, M3 reviews, the e1 STOP report, later per-dataset records).

The exact record set and hashes are in `OFFLINE_MECHANISM_AUDIT.json`.

## 3. What sweep 1 recorded — evidence map

### 3.1 Frozen corpus (committed, `origin/main`)

| Item | Recorded value |
|---|---|
| Index `results/r1/pilot/C3_sweep_index_20261028T033315Z.json` | SHA-256 `812468e26c0901a6cb5b3241f44a46fd4d1d2e498d172b76d63b1e91f6d835ab` |
| Sidecar `results/r1/evidence/C3_sweep_classification_20261028.json` | SHA-256 `bb6d891c499f0fc187726ed7c8c1e1bce107a029b9106ccb95115989c0c0f1dc` |
| Frozen tree `results/r1/evidence/C3_sweep_append_only_summary_20261027T154834Z` | Git tree `6b1c0c6154a604c391f8b7684a2d4ce34ccddd1a`; 436 files, 29,864,821 bytes; native manifest SHA-256 `f18f8a8b47ba17dc1da9e875d500831d6d0d03c69aa7d12b216444aeff1af98f` |
| Frozen tree `results/r1/evidence/C3_sweep_none_20261027T224356Z` | Git tree `468e57ce4871d0d33f08932c6fe13c2cb0d431ce`; 436 files, 25,808,052 bytes; native manifest SHA-256 `5053067331676e1aaefb0c757cac47ec82200ad124ff81f3d2ae074cf197d440` |

Each frozen tree is exactly 436 files: 144 `roots/*.json` root records, 288
`provenance/ledgers/roots/<campaign>/{root_events,root_trials}.jsonl` ledgers, `manifest.json`,
`collection_checks.json`, `temporary_provenance.tar.gz`, `temporary_provenance_index.json`.

What those records contain and do **not** contain (scan run on both trees):

- **Root records** carry `instance`, `node`, `seed`, `snapshots`, `start_files` (the editable
  `config.yaml`/`train.py` bytes). **No dataset identity.**
- **Ledgers/events** carry campaign/trial state, the structured edit, `patch_hash`, manager
  call data, `effective/active_config_sha256`, parsed metrics, time stamps. **No dataset
  identity.** The only JSON keys matching `hash|sha` are `config_sha256`, `index_sha256`,
  `model_sha256`, `sha256` — configuration/index/model/patch identity, not data identity.
- A scan for JSON keys matching `dataset|data_id|cache|md5|checksum` over both trees returns
  **none**. The `openml` string occurs only in node names/paths and LLM proposal rationale text
  (e.g. "imbalanced dataset"); it is not an identity record.
- `temporary_provenance.tar.gz` has **6,048 members**: 2,880 `art/.../patch.diff` + 2,880
  `art/.../run.log` + 144 `root_events.jsonl` + 144 `root_trials.jsonl`. It contains **no**
  `data_cache`, `dataset.json` or `benchmark.py` member. Its index has 5,760 references whose only
  fields are `patch_ref` and `raw_log_ref`. The archived `run.log`s print only
  `NODE/MODEL/VAL_*/STATUS` metrics.
- The index document lists the eight nodes and the harness commit but **no per-node dataset id or
  hash**; the sidecar records only the index hash and the two native-manifest hashes.

So from the committed corpus one can prove *which campaign, which configuration, which patch and
which recorded metric* each of the 16 replay cases came from — the case/collector/config binding the
e1 dry run already verified — but **not which dataset bytes the sweep-1 worker loaded**.

### 3.2 Preserved sweep-1 batch (deepthought, read-only)

The batch is the sweep-1 launch environment and is preserved. Its records:

| File | SHA-256 | Content relevant to dataset identity |
|---|---|---|
| `cache_check.json` | `35e76f37fcc4925a7896f6cf0bc2ab2bbf8647adfc763729da5a8e93325944f9` | mtime `2026-10-27 16:22:39 +0100` = **15:22:39Z**, 26 min before the 15:48:34Z sweep launch. Per OpenML node: `dataset_id`, `cache_source` (`node data_cache`), `cache_path`, and a loaded-data fingerprint (`rows`, `features`, `categorical_columns`, `missing_values`, `target_name`, `class_counts`, `positive_label`, `minority_share`, `status: ok`). **No hash key of any kind.** |
| `cache_check.log` | `a9ebd757179d29e583c5f13c04f9415f0fd21f3cfa82c0c894e518367396c35e` | Same result in text: data id, cache source, shape/class summary per node. No hash. |
| `prepare.json` | `bb47dd267a93329c7aa120b86f7cb47b053dfe17ea0f23cb97e7339af24d30d3` | paper/harness heads and test summaries; no data identity. |
| `pins_check.sha256` | `c3e89aa85f27970b044b5e007b60c0f806a93488d6a277575f952661a6b78edc` | hashes only for `c3_config.json`, the GGUF and the noise summary. |
| `c3_config.json` | `2fa891f43bf26e6ed2ac6c794696428a43568a69a850d6029e3bc8233616974b` | experiment config; no data identity. |
| `c3_sweep_summary.json` | `4daeedd5245f49df2e08a6291f08a38b124ccf20f5bdc75e2d117eafa3398967` | step results; no data identity. |
| `batch_state.json` | `c8d8301234a7e7d39611a29fcf38f87b721a655ac0703bc13345655cf38f41d5` | step/liveness state; no data identity. |
| `runner.log`, `sweep_append_only_summary.log`, `sweep_none.log`, `liveness.log`, `config_check.log` | — | targeted search found no data-cache hash; the only `cache` matches are `git diff --cached` command lines (in `runner.log`) and a langgraph `langgraph/cache/base/__init__.py` path in a deprecation warning (in `liveness.log`). |
| `liveness_c3_20261027T152425Z/` | — | 53 files (per-node liveness JSON/MD, ledgers, manifest, patch/log archive). The liveness manifest schema is `r1.liveness_run/1` with `harness`, `manager`, `nodes`, `launch_provenance`, `local_work_archive`; **no cache snapshot**. |

So the batch record **does** bind the six data ids to the launch (`cache_check.json`, whose schema and
per-node fields are those of the runbook's pre-launch `r1.noise.check_caches --json` output, present
and mtime-stamped 26 minutes before launch) and records a loaded-data fingerprint — but it records
**no file or tree hash**. The data ids themselves
also come from the pinned harness NodeSpecs (`configs/nodes/<node>.yaml` → `dataset.dataset_id`;
`nodes/<node>/dataset.json`), all at `6adf3859…`, i.e. they are bound to the harness commit, not to
file bytes.

### 3.3 The six nodes and what the pinned harness binds

| Node | OpenML id | Harness `dataset.json` name | metric | selected instance | cases |
|---|---|---|---|---|---|
| `openml_breast_w` | 15 | breast-w | val_auc | `__s105` | t001, t002 |
| `openml_ionosphere` | 59 | ionosphere | val_auc | `__s103` | t001, t002 |
| `openml_wdbc` | 1510 | wdbc | val_auc | `__s100` | t001, t002 |
| `openml_credit_approval` | 29 | credit-approval | val_auc | `__s100` | t001, t002 |
| `openml_sonar` | 40 | sonar | val_auc | `__s105` | t001, t002 |
| `openml_climate` | 1467 | climate-model-simulation-crashes | val_auc | `__s104` | t001, t002 |

`benchmark.py` calls `fetch_openml(data_id=DATA_ID, as_frame=True, parser="auto",
data_home=str(CACHE_DIR))` (no `download_if_missing`; the M3 static inventory records this). The
`data_cache` trees are Git-ignored: four are wholly untracked, `openml_sonar`/`openml_climate` have
tracked `.gitignore`/`.gitkeep` plus untracked data files; the harness tracked tree is clean. No
harness commit tracks the cache bytes, so the harness pin does not bind the data.

### 3.4 What the 16 cases are bound to

The driver's `verify_corpus` / `verify_collector_binding` / `select_cases` bind every case to the
frozen corpus (index/sidecar/trees/original blobs), the collector `ccb4712` (seed derivation), the
recovered configuration hashes, the archived patch and the archived log token; the e1 dry-run plan
`replay_plan.json` (SHA-256 `a5f04ef271ba5eab57543f238c2c2b82481a303fb19e5a454ad2accb5f055ba6`)
records that binding and was reproduced/verified in the accepted e1 review. **None of these checks
mentions a dataset byte or hash**, and the dry-run plan contains no such field.

## 4. Verdict: identity unprovable by sweep-1 recorded hashes

**Absent (needed, and searched for everywhere):** a sha256/md5 of any of the six nodes'
OpenML data files or `data_cache` tree, recorded by the sweep-1 launch, and a binding of that hash
to the six nodes / 16 replay cases.

**Found instead:** per-node OpenML data ids (pinned harness NodeSpecs + pre-launch
`cache_check.json`), the cache source/path (`node data_cache`), a pre-launch loaded-data fingerprint
(shape, classes, missingness, target), and a complete case/config/patch/log binding. These are
stronger than nothing and are consistent with a correct sweep, but they are **not hashes of the data
bytes** and cannot satisfy "file/tree sha256 equal to the sweep-1 recorded identity".

Hence: **"identity unprovable" — STOP for the author**, exactly the branch the row provides for.

Note on the accepted M3 offline components: `r1/c3/offline_*` (supervisor/seccomp/namespaces, cache
copy, case preflight) is accepted on `main` but, as the 9 November review records, is *not* wired
into `c3_env_replay.run` and was never given a sweep-1 data anchor. Those components fingerprint a
*given* cache copy and run a guarded loader preflight; they cannot prove that the given copy is the
sweep-1 bytes. (b) is therefore also not implemented here — implementing it without (a) would not
make e1 runnable and could read as clearing the OpenML STOP.

## 5. Observation only: what can and cannot be established from the surviving bytes

Recorded here so the author's decision is informed; **none of it is used as the sweep-1 identity**
and none of it relaxes the row's standard.

Surviving preserved-batch caches (read 2026-11-16, read-only): each node has its four standard files
under `nodes/<node>/data_cache/openml/openml.org/`; file mtimes are `2026-10-25 02:30–02:32 +0200`
(`openml_climate`'s directory `2026-10-26 22:36 +0100`), i.e. before the 27 Oct launch, and the
`openml_*` node caches are not tracked by the harness. Their current bytes hash as
`OFFLINE_MECHANISM_AUDIT.json` records (per-file SHA-256 and a `tree_digest` computed with the
driver's own algorithm: breast_w `88f68825…`, ionosphere `1079cb09…`, wdbc `075915dc…`,
credit_approval `05cf63a2…`, sonar `ccca8605…`, climate `73c5af11…`).

Two properties of the surviving bytes are self-consistent and worth recording:
- Every cached `api/v1/json/data/<id>.gz` carries OpenML's `md5_checksum`, and the **uncompressed
  ARFF md5 matches it for all six nodes** (e.g. ionosphere `23dd3c8b…`, credit_approval
  `a948be96…`). So the surviving caches are internally consistent with the OpenML archive entries
  for ids 15/59/1510/29/40/1467.
- For **two of six** nodes, earlier/later *non-sweep-1* records exist of a copy of the same L8
  fallback cache on TASL-7 (`docs/r1/reports/exam_phase2_20261026/cache_manifest.json`,
  `docs/r1/proposals/B1_TASL7_HARNESS_CACHE_LOCATE_20261107.md`,
  `sweep2/s2_c3_declared_inputs.json` @ `c545852c`): their ARFF payload hashes
  (`b21f0187…` credit, `40b4580d…` ionosphere) equal the preserved-batch ARFFs, but their
  **metadata `.gz` hashes differ** from the preserved-batch metadata — the trees are not the same
  bytes, and none of these documents is a sweep-1 record.
- No record anywhere in the repository history records the other four nodes' cache hashes, and no
  record binds any of these hashes to the sweep-1 launch.

So a *weaker* standard — "same OpenML data id + same pre-launch loaded-data fingerprint + OpenML
metadata md5 self-consistency + unchanged surviving bytes, verified before and after use" — could in
principle be argued for, but it is weaker than the row's declared standard, would still rest on
surviving bytes rather than a sweep-1 anchor, and cannot be substituted without an author amendment
and independent review.

## 6. Decision required from the author

Per R1-E1-OPENML the author decides one of:

1. **Replay only the four non-OpenML cases** (`digits_mlp`, `tabular_mlp` — 4 of 16). This requires
   amending the predeclared 16-case protocol and the e1 authorization/pass rule (both require all 16
   cases and zero tolerance); the e1 STOP report already notes the 4 local cases "cannot be replayed
   on their own under the authorized 16-case protocol". No B.2 consequence follows automatically.
2. **Grant the R1-MAIN-PROPOSER (g)2 exception** (sweep-2 proceeds without completed sweep-1 B.2).
   R1-SWEEP2-SETTINGS (3) currently says no exception is given until e1 → e2 → sweep-1 B.2, to be
   revisited only if (g)2 is the only blocker for sweep 2; that is the author's row to revisit.
3. **Amend the identity standard** (not this audit's recommendation; requires an author row and
   independent review): accept the weaker route in §5 as sufficient, with the residual risk stated
   in the decision record.
4. **Do nothing** and keep e1 at STOP; the current e1 STOP report stands.

Not decided here; this branch only reports. Zero-tolerance pass rule, offline STOP, and the driver's
OpenML hard STOP are unchanged.

## 7. What this does and does not establish

- Establishes: every sweep-1 identity record listed in §3 was inspected; sweep 1 recorded no md5 or
  sha256 of any OpenML data file or cache tree (committed corpus and batch records); consequently the
  row's (a) cannot be met from sweep-1 records; the OpenML hard STOP remains the only correct state.
- Does not establish: any byte identity between the surviving caches and the sweep-1 run; anything
  about worker numerics; any network-denial implementation; any B.1/B.2 result or label.
- Bounded by scope: the audit covers the committed corpus, the preserved batch, and repository
  documents/history. It cannot rule out an unreferenced record on some other host; none is referenced
  by the sweep-1 manifests or authorization. The `/tmp` sweep scratch is gone and was never archived
  with data caches (only patch/log artifacts were).

## 8. What the independent reviewer must check

1. **Authority/base.** `origin/main` at branch time is `025bfc16` (row R1-E1-OPENML present;
   `9a74bf19` its parent); `5ef9db16` is an ancestor; driver SHA-256 `a9cad4d5…` unchanged at
   `5ef9db16`, `origin/main` and branch HEAD.
2. **Diff.** `git diff origin/main..HEAD` adds only this report and `OFFLINE_MECHANISM_AUDIT.json` —
   no module, no wiring, no test, no driver edit, no PLAN/authorization edit.
3. **Committed-corpus scan.** Recompute the tree hashes `6b1c0c61…`/`468e57ce…`, 436 files each,
   index/sidecar hashes, native-manifest hashes; confirm the identity-key scan is empty, that the
   provenance archive has no `data_cache`/`dataset.json`/`benchmark.py` member, and that its index
   has only `patch_ref`/`raw_log_ref` fields.
4. **Batch records.** On deepthought (read-only) confirm `cache_check.json` SHA-256 `35e76f37…`,
   mtime 15:22:39Z (< 15:48:34Z launch), and that it has no hash field; check `cache_check.log`,
   `prepare.json`, `pins_check.sha256`, `c3_config.json`, `c3_sweep_summary.json`,
   `batch_state.json`, the sweep/liveness logs and the liveness tree likewise.
5. **Harness data ids.** Confirm ids 15/59/1510/29/40/1467 in `configs/nodes/*.yaml` and
   `nodes/*/dataset.json` at `6adf3859…`; confirm `fetch_openml(..., data_home=...)` has no
   `download_if_missing`; confirm the caches are untracked/ignored and the harness tracked tree is
   clean.
6. **Surviving bytes (observation only).** Recompute the per-file SHA-256 / `tree_digest` values in
   the audit JSON if desired; verify the report does **not** use them as the anchor.
7. **Non-sweep-1 records.** Confirm the exam-phase-2/B1/S2-C3 records cover 2/6 nodes, are not
   sweep-1 records, and differ in metadata-tree bytes from the preserved batch.
8. **Correct branch of the row.** Confirm "identity unprovable" is the row's prescribed outcome and
   that §6 states the author options accurately (the 4-case option needs a protocol amendment; (g)2
   is the author's exception row).
9. **No execution/side effects.** Confirm no driver run, no e1 case, no B.2, no label, no job, no
   write on deepthought/ceph (read-only commands only), and that branch `ops-e1-replay-20261116` and
   `main` are untouched.

## 9. Evidence inventory

- `OFFLINE_MECHANISM_20261116.md` — this report.
- `OFFLINE_MECHANISM_AUDIT.json` — machine-readable record: authority, inspected artifacts and
  hashes, identity scans and absence results, current-cache observations (explicitly not usable as
  the anchor), non-sweep-1 records, verdict/STOP, author options, reviewer checklist.
- `SHA256SUMS.txt` — hashes of the two files above.

Read-only remote inspection was performed 2026-11-16 22:10–22:13Z (UTC) as `dwong` on
`deepthought.etp.kit.edu`; the endpoint is the preserved batch listed in §3.2 and nothing under it was
written. No B.2, no label, no audit, no e1 run.
