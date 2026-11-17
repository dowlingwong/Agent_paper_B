# Independent review — C3 B.1 e1 OpenML offline mechanism audit (16 November 2026)

Reviewer: `reviewer-e1-openml`, independent and read-only (did not write the reviewed unit). This
file is the only write; no execution of e1 or the driver, no job, no server, no B.2, no git write.
Review date 2026-11-16 (Europe/Berlin). Repository checks were read-only git commands; the
preserved-batch checks were read-only SSH commands (`ls`, `stat`, `sha256sum`, `git status`,
read-only Python) as `dwong` on `deepthought.etp.kit.edu`.

## Reviewed unit and authorities

- Branch `e1-openml-20261116` @ `b3b957e64d382264f6bf36e444f05f6d748b948f` (remote ref identical;
  parent `025bfc16477a3911ea461d7a6cfc85f3ea523d66` = base `origin/main`).
- Artifacts in `docs/r1/reports/e1_replay_20261116/`: `OFFLINE_MECHANISM_20261116.md` (20458 B),
  `OFFLINE_MECHANISM_AUDIT.json` (25887 B), `SHA256SUMS.txt` (2 lines).
- Authority: PLAN row **R1-E1-OPENML** @ `025bfc16`, §10 (line 1223, quoted verbatim in the report
  and matching the row I read); basis e1 STOP report `ops-e1-replay-20261116` @ `fc7d8e4e`
  (accepted review in the same commit), STOP commit `fd833c9e`; e1 authorization
  `docs/r1/authorizations/c3_env_replay_20261116.md` @ `4da73306`; row R1-E1-AUTH; predeclared
  protocol `C3_ENV_RECONSTRUCTION_REPLAY_DRAFT_20261028.md`.
- `SHA256SUMS.txt` verifies from the pushed blobs:
  `61a3d02b…ce2369` (report) and `9f14c879…a190b7` (audit JSON) — both OK.

**Bottom line: the report is correct and faithful. "Identity unprovable" is the row's prescribed
STOP branch, established from the records sweep 1 actually left; nothing usable was missed; no
mechanism was fabricated; nothing was executed. Findings are minors (wording/description), no
blockers, no majors.**

## 1. Docs-only, no execution, branch/authority state (report §8.1, §8.2, §8.9)

- `git diff --stat origin/main..e1-openml-20261116`: 3 files added, 818 insertions, 0 deletions —
  exactly the report, the audit JSON and `SHA256SUMS.txt`. `git diff --name-only … -- r1/` is
  empty; no module, wiring, test, driver, PLAN or authorization edit.
- Driver `r1/scripts/c3_env_replay.py` blob `7976fcfb…`, SHA-256
  `a9cad4d544bdf061c42ecb4b4c2d3d10d8bc94342574d9a37489bd4b179aa7d8` at `5ef9db16`,
  `origin/main` and branch HEAD — byte-identical at all three, as claimed.
- Branch/worktree: the reviewed branch worktree is clean at `b3b957e6`; it contains no
  `results/r1/engineering/C3_env_replay_*` output, no e1 cases/plan/summary, and no untracked
  files. The only e1 outputs on the cluster are the operator's 16 Nov 09:44Z dry run under
  `/ceph/dwong/r1_e1_20261116/…` (STOP report), which is not on this branch.
- Remote refs (read-only `git ls-remote`): `main` = `025bfc16`, `author-decisions-20261116b` =
  `025bfc16`, `ops-e1-replay-20261116` = `fc7d8e4e` (accepted-review commit), `e1-openml-20261116`
  = `b3b957e6`. `ops-e1` was not touched (its remote tip is still the 10:56 CET review commit; the
  local ref is a stale `fd833c9e`). `origin/main` is unchanged.
- Audit-window side effects: the preserved batch has no file with a 16 Nov mtime except the
  `.git/` directory metadata of the harness/paper checkout (read-only `git status/ls-files`
  refreshes the index stat cache; no tracked or data file changed), and the e1 deployment
  directory has **zero** files created/modified after 21:00 local (CET) on 16 Nov, i.e. no e1
  artifact
  appeared in the known deployment/branch locations during the audit window (22:10–22:14Z); a run
  elsewhere cannot be excluded by filesystem inspection alone, but there is no positive evidence of
  one. This is consistent with the audit's "no e1 run, no job, no write" claim. (I cannot re-prove the audit's exact remote command list or its 22:10–22:13Z
  timestamps, but its stated hashes of the batch records are exactly reproducible; see §3.)
- Authority is valid: row R1-E1-OPENML exists at the base commit and prescribes this branch; the
  authorization content is available at `4da73306` and also in the base tree (see Minor 3).

## 2. The absence claim — re-derived independently (report §3–§5)

All values below I recomputed from the pushed objects/batch; every one matches the report/audit.

**Committed sweep-1 corpus (`origin/main`).**

- Index `results/r1/pilot/C3_sweep_index_20261028T033315Z.json` = `812468e2…d835ab` ✔; keys are
  schema/label/written_utc/nodes/excluded_nodes/instances/runs/liveness/harness_commit/sweeps/
  launch_provenance/nodes_pending/noise_source/manager/audit. Only hash-like fields:
  `launch_provenance.config_sha256`, `launch_provenance.model_sha256`, `manager.model_sha256`,
  `noise_source.sha256` — no per-node dataset id or data hash.
- Sidecar `results/r1/evidence/C3_sweep_classification_20261028.json` = `bb6d891c…0c0f1dc` ✔;
  contains only the index hash and the two native-manifest hashes.
- Frozen tree `C3_sweep_append_only_summary_20261027T154834Z` = Git tree `6b1c0c61…` ✔,
  436 blobs, 29,864,821 bytes; `manifest.json` = `f18f8a8b…1af98f` ✔; composition 144 roots +
  288 ledgers + manifest.json + collection_checks.json + temporary_provenance.tar.gz +
  temporary_provenance_index.json.
- Frozen tree `C3_sweep_none_20261027T224356Z` = Git tree `468e57ce…` ✔, 436 blobs, 25,808,052
  bytes; `manifest.json` = `50530673…97d440` ✔.
- `temporary_provenance.tar.gz`: 6,048 members = 2,880 `patch.diff` + 2,880 `run.log` + 144
  `root_events.jsonl` + 144 `root_trials.jsonl`; **no** member path contains
  data_cache/dataset.json/benchmark.py/arff; no member contains an md5/checksum/data_cache/
  dataset_id/arff token; run.log bodies are only metric/status lines (OpenML nodes:
  `NODE=…`, `MODEL=…`, `VAL_AUC=…`, `VAL_ACC=…`, `STATUS=…`; MLP nodes: `val_score:`,
  `train_loss:`).
- Identity scans: over both trees (all regular-file bytes and every parsed JSON/JSONL key),
  **zero** keys match `dataset|data_id|cache|md5|checksum`, and **zero** raw occurrences of
  `md5`, `checksum`, `data_cache`, `dataset_id` or `.arff` exist. There is **no 32-hex (md5)
  value anywhere**. Every 64-hex value is one of: ledger `patch_hash`, payload
  `active_config_sha256`/`effective_config_sha256`, manager `context_sha256`/
  `raw_proposal_sha256`, manifest `config_sha256`/`index_sha256`/`model_sha256`/`noise sha256`,
  or provenance-index `references[].sha256`. All are config/patch/proposal/log identity, not data
  identity (Minor 2 only concerns the report's enumeration of these key names).
- Root records: 144 per tree, keys exactly `instance`, `node`, `seed`, `snapshots`, `start_files`;
  **all 288 `snapshots` are empty**, so there is no hidden cache snapshot to miss; OpenML root
  `start_files` are `config.yaml` hyperparameters only (verified for breast_w/ionosphere/climate,
  and no `data_id`/path appears in any tree).
- The provenance-index description is the one place the report is loose: the 5,760 references do
  not have "only fields patch_ref/raw_log_ref" — each reference carries `ledger`, `field`,
  `original_ref`, `member`, `sha256`, with `field` ∈ {patch_ref, raw_log_ref}. The `sha256` are
  hashes of the referenced patch/log members (no data member exists), so the absence conclusion is
  unaffected (Minor 1).
- The index-listed collector commits `224c2483…` (append_only) and `259722cf…` (none) are in repo
  history; their sweep output dirs are the same 436-file trees, and no `cache_check` or
  data-hash-bearing file exists anywhere in those commits either.

**Preserved sweep-1 batch (deepthought, read-only re-check 2026-11-16T22:22Z).**

- `cache_check.json` = `35e76f37…25944f9` ✔, mtime `2026-10-27 16:22:39.992109378 +0100` =
  **15:22:39Z**, i.e. 26 min before the frozen manifests' `started_utc`
  `20261027T154834Z` (15:48:34Z) ✔. Full schema: `harness`, `versions`, `nodes`; per OpenML node
  `node`, `dataset_id`, `cache_source` ("node data_cache"), `cache_path`, `rows`, `features`,
  `categorical_columns`, `missing_values`, `target_name`, `class_counts`, `positive_label`,
  `minority_share`, `problems`, `status` — **no hash key of any kind** ✔. Data ids
  15 / 59 / 1510 / 29 / 40 / 1467 ✔ with the fingerprint values the report records.
- `cache_check.log` = `a9ebd757…396c35e` ✔ (same result in text, no hash; it also records that the
  check process had network disabled); `prepare.json` = `bb47dd26…24d30d3` ✔; `pins_check.sha256`
  = `c3e89aa8…a6b78edc` ✔ and contains exactly c3_config, the GGUF model and the noise summary;
  `c3_config.json` = `2fa891f4…61974b` ✔; `c3_sweep_summary.json` = `4daeedd5…8967` ✔;
  `batch_state.json` = `c8d83012…41d5` ✔.
- All other top-level batch records/logs contain **no** md5/checksum/data_cache/arff token;
  `runner.log`'s only "cache" hits are four `git diff --cached` command lines; `liveness.log`'s
  single hit is the langgraph cache deprecation path. The liveness tree has 53 files and no
  identity token; its manifest has no cache snapshot (keys match the audit list).
- The batch's own harness is at `6adf3859de66c4814fcf376eed59880fbd8eeaf7` ✔, tracked status clean
  (`--untracked-files=no` empty), with 5 untracked entries (four whole `data_cache` dirs and the
  pre-existing `paper/tables/artifact_completeness_report.txt`); `nodes/<node>/dataset.json`
  contains only `node_name`, `dataset_id`, `dataset_name`, `target`; `benchmark.py:176` is
  `fetch_openml(data_id=DATA_ID, as_frame=True, parser="auto", data_home=str(CACHE_DIR))` with
  **no** `download_if_missing` ✔; sonar/climate track only `.gitignore`/`.gitkeep`, the other four
  cache dirs are untracked. No harness NodeSpec/dataset/baseline file carries a data hash ✔.
- Driver (`origin/main`): `check_harness()` computes `data_caches_sha256` at run time and the run
  compares before/after only (lines 422–431, 612–613); `has_cache_files()` is presence-only
  (434–436); `execute_case()` computes `tree_digest` before/after and refuses any `openml_` case
  (482–483, 502, 530); whole-set gate at 578–579. Unchanged from the accepted e1 review.

**Verdict on the central question: justified.** The only dataset-content hashes that exist near
the sweep are (i) OpenML's `md5_checksum` inside the *untracked* cache metadata (it equals the
uncompressed ARFF md5 — I verified all six, e.g. breast-w `88633c06…`, climate `c3d91dc5…`) and
(ii) a shape/class "loaded-data fingerprint" recorded pre-launch in `cache_check.json`. Neither is
a hash written into a sweep-1 record and bound to the six nodes/16 cases, and both are correctly
presented as observation-only. The row's condition ("若 sweep 1 未记录可用于证明身份的数据集哈希")
is met: **identity unprovable by sweep-1 recorded hashes** is the prescribed STOP branch, and the
report uses exactly that term without claiming global impossibility (§7 bounds it to the committed
corpus, the preserved batch and repo history).

## 3. The 2/6 non-sweep-1 records and the history claim (report §5, §8.7)

- Exam-phase-2 (26 Oct, `docs/r1/reports/exam_phase2_20261026/cache_manifest.json` @ `2d52101a`)
  covers only credit_approval + ionosphere; its ARFF sha256 (`b21f0187…`, `40b4580d…`) equal the
  preserved batch, but its metadata `.gz` sha256 (`5229a8b1…`, `2d18f98c…`) differ from the
  preserved batch (`0f0589d9…`, `5e35dd2b…`) — not the same tree, and not a sweep-1 record.
- B1 (7 Nov proposal/review/tools) covers the same two nodes only, from the TASL-7/A3 L8 fallback,
  and explicitly says the ARFF md5s match the caches' own metadata, not the sweep-1 launch.
- S2-C3 (`sweep2/s2_c3_declared_inputs.json` @ `c545852c`) records `tree_sha256` only for credit
  (`702a0b3c…`) and ionosphere (`65dfc44c…`), created 16 Nov for a different (L40S) deployment —
  neither equals the preserved-batch tree digests (`05cf63a2…`, `1079cb09…`).
- Repo-wide check (all local/remote refs except this audit branch): the current tree digests,
  the current metadata-file sha256 of breast_w/wdbc/sonar/climate, and the other four nodes'
  ARFF sha256 and OpenML md5 appear **nowhere**; only the credit/ionosphere ARFF sha256 + md5
  appear (exam-phase-2, B1, S2-C3), exactly as the report states. The report's phrase "no record
  anywhere in repository history" is literally self-referential now that this audit records the
  currents (as observation), so "no prior/sweep-1 record" would be more precise (Minor 5).

## 4. Author options and language (report §6, §8.8)

- **(a) Replay the four non-OpenML cases.** Accurate and correctly caveated: the e1 STOP report
  says verbatim "the 4 local MLP cases cannot be replayed on their own under the authorized
  16-case protocol"; the predeclared protocol and the authorization's PASS rule (all 16, zero
  tolerance) and the disclosure text would need amendment. It does not automatically yield B.2
  (e2 is separate) — the report says so.
- **(b) R1-MAIN-PROPOSER (g)2 exception.** Accurate: the row itself offers this, and
  R1-SWEEP2-SETTINGS (3) withholds the exception until e1 → e2 → sweep-1 B.2, revisiting only if
  (g)2 is sweep 2's sole blocker.
- **(c) Amend the identity standard to the weaker route.** Correctly listed, correctly labelled
  weaker/post-hoc and requiring an author row plus independent review with the residual risk stated;
  not this audit's recommendation. This is the only route that could use the surviving caches'
  fingerprint + OpenML md5 self-consistency + pre/post digests, and it still is not a sweep-1-record
  proof.
- **(d) Leave e1 at STOP.** Current state.
- I found no hidden option that changes the outcome, and no option is omitted that could clear the
  OpenML STOP without an author decision. (An author could ask for a prospectively recorded
  per-node data hash in future sweeps, but that affects sweep 2+, not e1; the report does not claim
  otherwise.) The language "identity unprovable" is exactly the row's "身份不可证", and no
  overclaim was found: the report does not say the datasets differed, only that identity cannot be
  proven from sweep-1 records; it explicitly cannot rule out an unreferenced record on another
  host.

## 5. Residual risks and limitations

- The audit's stated limits are honest: committed corpus + preserved batch + repository
  documents/history; the `/tmp` sweep scratch is gone and only patch/log artifacts were archived
  with the provenance; no record binding dataset bytes to nodes/cases exists.
- A later accepted mechanism would still need: a stated identity rule (what counts as the
  anchor), an independently reviewed no-network enforcement in worker subprocesses, and a decision
  record with the residual risk of resting on surviving rather than sweep-1-recorded bytes. The
  report says this. It would be worth adding to the author's record that sweep 2 should record
  per-node data-file hashes at launch to avoid a repeat of this hole (a recommendation, not a
  defect in this audit).
- The report could mislead only on descriptive details, not on the verdict: the provenance-index
  "fields" sentence (Minor 1), the hash-key enumeration (Minor 2), and the authority wording
  (Minor 3). None of them touches a data-hash record or the STOP logic.

## 6. Findings

**Blockers: none.**
**Majors: none.**

**Minors (all descriptive; fix before publication if convenient):**

1. **Provenance-index field description is wrong.** §3.1 says each of the 5,760 references has
   "only fields `patch_ref` and `raw_log_ref`". Actual reference keys are `ledger`, `field`,
   `original_ref`, `member`, `sha256`; `patch_ref`/`raw_log_ref` are the two `field` values. The
   `sha256` hashes are of patch.diff/run.log members (there are no data members), so the absence
   conclusion stands; the wording would make an independent verifier re-check a non-issue.
2. **Hash-key enumeration incomplete.** §3.1 and audit `identity_scan.json_keys_matching_hash_sha`
   list only `config_sha256`, `index_sha256`, `model_sha256`, `sha256`; the frozen ledgers also
   contain `patch_hash`, `active_config_sha256`, `effective_config_sha256`, `context_sha256`,
   `raw_proposal_sha256`, and provenance-index `references[].sha256`. All are non-data identity, so
   the conclusion is unchanged; list them (or say "keys ending in hash/sha256 are limited to …").
3. **Authority wording.** Report's branch/base parenthetical calls `origin/main` `025bfc16` "the
   authorization commit itself"; it is the R1-E1-OPENML decisions commit (parent `9a74bf19`). The
   authorization commit `4da73306` is an ancestor of `9a74bf19`/`025bfc16`, and the authorization
   blob is present on `origin/main` (identical `0dd0ace5…` at `4da73306`, `9a74bf19`, `025bfc16`).
   The audit JSON's note "The authorization file is not merged to main; read it from the cited
   commit" is therefore false. Authority itself is valid and correctly cited; only this provenance
   wording needs fixing.
4. **Checklist item omits SHA256SUMS.txt.** Report §8.2 says the diff adds "only this report and
   OFFLINE_MECHANISM_AUDIT.json"; it adds three files (the third is `SHA256SUMS.txt`). The audit
   JSON checklist and §9 are correct.
5. **"No record anywhere in repository history" is self-referential.** §5 now records the
   surviving-cache hashes as observation; say "no prior/sweep-1 record" to avoid a literal
   contradiction. (Also audit JSON `pinned_harness.tracked_clean_untracked_files_no: true` is
   ambiguous: the harness has 5 untracked entries; the report text "tracked tree is clean" is
   accurate.)

## 7. Reviewer checklist mapping (report §8)

1. Authority/base — pass (row present at `025bfc16`; `9a74bf19` parent; driver `a9cad4d5…` at
   `5ef9db16`, `origin/main`, HEAD).
2. Diff — pass (3 docs additions; no module/wiring/test/driver/PLAN edit).
3. Committed-corpus scan — pass (trees `6b1c0c61…`/`468e57ce…`, 436 files each, index/sidecar and
   manifests recomputed; identity-key scan empty; provenance archive composition confirmed; see
   Minors 1–2 for wording).
4. Batch records — pass (`35e76f37…`, mtime 15:22:39Z < 15:48:34Z launch, no hash field; other
   records/logs likewise; liveness 53 files, no cache snapshot).
5. Harness — pass (ids 15/59/1510/29/40/1467; `fetch_openml` without `download_if_missing`; caches
   untracked/ignored; tracked tree clean).
6. Surviving bytes — pass (all six tree digests and per-file hashes reproduce; OpenML md5
   self-consistency true for all six; report/audit explicitly do **not** use them as the anchor).
7. Non-sweep-1 records — pass (2/6 nodes; 26 Oct / 7 Nov / 16 Nov; metadata/tree bytes differ; no
   binding to sweep 1).
8. Correct branch/options — pass ("identity unprovable" is the row's branch; options accurate).
9. No execution/side effects — pass to the extent verifiable (branch docs-only and clean worktree;
   no e1 output dirs; no post-21:00Z files in the e1 deployment dir; remote `main`/`ops-e1`/branch
   refs unchanged).

## Verdict

The recorded sweep-1 identity surface is exhaustively and correctly characterised. No sweep-1
record contains a dataset file/tree hash bound to the six OpenML nodes or the 16 cases; the
nearest candidates (untracked cache metadata md5, pre-launch fingerprint) are correctly excluded
from the anchor and offered only as an author-amendment route. The report neither overclaims nor
fabricates a mechanism, and its STOP is the row's prescribed branch. Minor descriptive/citation
inaccuracies should be corrected but do not change the conclusion.

VERDICT: ACCEPTED
