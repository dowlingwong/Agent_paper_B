# Independent review — C3 B.1 amended e1 environment replay **run** (17 November 2026)

Reviewer: `reviewer-e1-run`, independent and read-only (did not write the reviewed unit). This
file is the only **content** write; no execution of e1, no driver run, no e1 dry run, no e1/pytest
run, no job, no server, no B.2, no label, no deepthought/ceph write, no commit, push, branch or ref
change. All checks were read-only: `git show`/`rev-parse`/`merge-base`/`diff` on existing objects,
`sha256sum -c`, JSON/tarfile reads of retained evidence and of the frozen corpus/provenance blobs,
and read-only `git show` of the pinned harness commit. A detached review worktree at the reviewed
report tip was created to hold this file (only that worktree's `.git` administrative metadata was
added; no branch/ref moved). Review date 2026-11-17 (Europe/Berlin).

## Reviewed unit and authorities

- Report branch **`ops-e1-replay-amend-20261117` @ `7f1e09aa883de786abfdfbcc95ac934145a85d06`**
  (pushed; parent `381b0859`, parent `origin/main` @
  `26177d82904e8e72802ddf985ff35ffe0aaea479`). `git diff --name-status 26177d82..7f1e09aa`: **41
  files, all `A`, +4,719, all under `docs/r1/reports/e1_replay_20261117/`**; nothing else and no
  `.gitignore` change. The branch is not merged to `main`.
- Report directory `docs/r1/reports/e1_replay_20261117/` — 41 files (REPORT.md, summary.json,
  cases.jsonl, replay_plan.json, dryrun/replay_plan.json, raw/ ×16, pins.json, commands.txt,
  EVIDENCE_MAP.md, logs/ ×13, scripts/ ×3, SHA256SUMS.txt).
- Authority: `origin/main` @ `26177d82` rows **R1-E1-OPENML-AMEND** (`docs/r1/PLAN.md` line 1241,
  amending R1-E1-OPENML line 1223, under R1-E1-AUTH line 1211), authorization
  `docs/r1/authorizations/c3_env_replay_20261116.md` (SHA-256 `28f5fb08…`), predeclared protocol
  `docs/r1/proposals/C3_ENV_RECONSTRUCTION_REPLAY_DRAFT_20261028.md` (SHA-256 `01902a6e…`),
  basis audit `e1-openml-20261116` @ `5d73550a`, basis e1 STOP `ops-e1-replay-20261116` @
  `fc7d8e4e` (review `E1_REPLAY_REVIEW_20261116.md`, verdict ACCEPTED).
- Amended mechanism: branch `r1-e1-openml-amend-20261117` @ **`bbcfc4a9`** (reviewed code commit
  **`5bddab73`**; `git diff 5bddab73..bbcfc4a9` = `docs/r1/reviews/E1_AMEND_REVIEW_20261117.md`
  only, +133; round 2 **ACCEPTED**). `5bddab73` is an ancestor of `bbcfc4a9`; `bbcfc4a9` is
  `origin/r1-e1-openml-amend-20261117`.
- Deployment (operator-reported): `/ceph/dwong/r1_e1_20261117/agent_paper_B` detached at
  `bbcfc4a9`, clean, `16185b0b` an ancestor, both run dirs retained.

## Bottom line on the question asked

The PASS is **faithful**. The report's verdict matches the retained driver artifacts: 16/16 cases
reproduce the predeclared recorded tokens exactly at `tolerance: 0`, every driver environment check
was present and passed, and the R1-E1-OPENML-AMEND mechanism reached `state = VERIFIED` before the
output directory was created and before the first case. The amended driver/mechanism/audit pins are
the reviewed ones (not the pre-amendment `5ef9db16`/`a9cad4d5`), the authorized gate order was
followed, the `(b)` and `(i)–(iv)` evidence is present and internally consistent with the accepted
audit, and the required disclosures are substantially carried (one residual-risk completeness
minor must be fixed before the PASS is used in the paper). No blocker and no major.

## 1. Pins, authority and no side effects — verified

| Item | Claimed / found | Check |
|---|---|---|
| Authority row | `R1-E1-OPENML-AMEND` (amends R1-E1-OPENML, under R1-E1-AUTH) | row present at `origin/main` `26177d82`; plan `openml_offline_mechanism.row` and `pins.authority.row` both say it |
| Amended driver | `r1/scripts/c3_env_replay.py` SHA-256 **`1b1e2fb229e78a82b56f1b8c9e45d6bc36412facf26d89f05bf6acb830a7e7e0`**, blob `db55a2cc` | re-hashed at `5bddab73` **and** `bbcfc4a9`: equal; blob = `db55a2cc…` |
| Pre-amendment driver | `5ef9db16…` / SHA-256 `a9cad4d5…` correctly presented as predating the amendment, **not** run | `git show 5ef9db16:r1/scripts/c3_env_replay.py` hashes to `a9cad4d5…`; report §2 and `pins.paper_code.driver.note` say this explicitly |
| Mechanism module | `r1/c3/e1_openml_offline.py` SHA-256 `6bcc50fe…` | equal at `5bddab73` and `bbcfc4a9` |
| Network module | `r1/c3/e1_offline_network.py` SHA-256 `6c9a95a8…` | equal at `5bddab73` and `bbcfc4a9` |
| Test modules | `faec8865…`, `6ea882cc…`, `2b4d5275…` | re-hashed at `bbcfc4a9`: equal |
| Reviewed audit | `OFFLINE_MECHANISM_AUDIT.json` SHA-256 `9f14c879…` | re-hashed: `9f14c879…`; byte-identical at `5d73550a` and `bbcfc4a9` |
| Reviewed/deployed gap | reviewed `5bddab73` + review file only → deployed `bbcfc4a9` | `git diff --stat 5bddab73..bbcfc4a9` = one file, +133 lines |
| Report branch base | current `main` `26177d82` | `origin/ops-e1-replay-amend-20261117` = `7f1e09aa`; `origin/main` = `26177d82`; branch adds only the report directory |
| Untouched refs | `main` and `ops-e1-replay-20261116` not touched | `origin/main` still `26177d82`; `origin/ops-e1-replay-20261116` still `fc7d8e4e`; branch diff has no file outside the report dir |
| `SHA256SUMS.txt` | hashes every evidence file | `sha256sum -c` = **40/40 OK**; the 40 entries cover exactly the 40 non-manifest files with no extras |
| Corpus pins | index `812468e2…`, sidecar `bb6d891c…`, frozen trees `6b1c0c61…`/`468e57ce…` | re-hashed/matched in the report worktree; all equal the plan's `corpus` block |
| Provenance tarball | `temporary_provenance.tar.gz` SHA-256 `5bcfb4c2…` | re-hashed: equal; 6,048 members |

No run artifact was left in the paper repo by the report branch (only the 41 report files), and the
report branch does not modify code, PLAN, authorization, protocol or any results tree.

## 2. Authorized order — verified

1. **Linux seccomp test FIRST, on deepthought.** `seccomp_attempt1.log` starts 00:46:31Z; the
   specific test then ran at 00:46:53Z and **PASSED** on deepthought
   (`Linux x86_64`, `4.18.0-553.156.1.el8_10.x86_64`, Python 3.13.15, pytest 9.0.3;
   `seccomp_specific_test.log`). The module ran **15 passed / 1 Linux-skip** (exit 0) in
   `seccomp_attempt2.log`; the skip is `test_install_refuses_the_current_non_linux_host` by design.
   All of this precedes the preflight (00:47:09Z), co-tenancy, dry and real steps.
   The **first invocation artifact is non-mechanism**: `seccomp_attempt1.log` is
   `1 failed, 14 passed, 1 skipped` (exit 1) and the traceback is an `ImportError` in the test's
   disposable `/tmp` probe child, because the batch `env.sh` `PYTHONPATH` puts the stale sweep
   checkout `…/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw/agent_paper_B` ahead of the deployed
   checkout; it is raised at `probe.py` line 2 **before** `N.install()` is reached (no seccomp call
   or probe was attempted). Prepending the deployed reviewed checkout for that child
   (`seccomp_attempt2.log`: `PYTHONPATH=/ceph/dwong/r1_e1_20261117/agent_paper_B:…`) reproduces the
   environment the test is written for and the test passes. The real run does not depend on this:
   the driver resolves `r1` through `python -m` from the reviewed checkout cwd, and its own child
   probe is a `python -c` stdlib probe (`e1_offline_network.PROBE`) that imports no `r1` at all.
2. **Co-tenancy ≥10 of 40 cores free, before both runs.** `cotenancy.log`: 00:47:18Z load 15.79 ⇒
   ≈24.21 free; 00:48:07Z load 16.63 ⇒ ≈23.37 free; `nproc --all = 40`. Both PASS; pre-existing
   unrelated jobs are listed (jepa_noise R2, paperc headroom, other users).
3. **Dry run first, into a new dir.** `dryrun.log`: start 00:47:18Z, exit 0, 16 cases, out
   `…/C3_env_replay_20261117T004900Z_amend_dryrun` (must not have existed: the driver STOPs on an
   existing `--out`, and it returned normally). `dryrun/replay_plan.json` SHA-256
   **`efc22311…`** (matches the copy printed in `postrun_evidence.log` and `dryrun_plan_inspection.log`),
   `label: DRYRUN`, `schema: r1.c3_env_replay/1`, `tolerance: 0`,
   `environment: DEFERRED_TO_HOST`, `openml_offline_mechanism.state: DEFERRED_TO_HOST`, the
   amended token, 16 predeclared cases, `written_utc: 2026-11-17T00:47:39Z`. The plan was inspected
   at 00:47:53Z (`dryrun_plan_inspection.log`) before the real run. Scratch was not created, as the
   dry-run path returns before `scratch.mkdir()`.
4. **Real run second, into a DIFFERENT new dir, with the amended token.** `real.log`: start
   00:48:07Z; out `…/C3_env_replay_20261117T004807Z_amend_real`; argv contains
   `--openml-offline-mechanism r1-e1-openml-amend-20261117`; **exit 0**.

## 3. Result — 16/16 exact recorded tokens, PASS at zero tolerance

- `summary.json`: `label ENGINEERING_ONLY`, `cases_planned 16`, `cases_run 16`,
  `cases_passed 16`, **`verdict PASS`**, **`stop null`**, `tolerance 0`,
  `replay_plan_sha256 23a17665…`, `cases_sha256 ce6ed7b3…`; file SHA-256 `ff7fe3c3…` (also in
  `SHA256SUMS.txt`). Re-hashed files equal the recorded hashes.
- `replay_plan.json` SHA-256 `23a17665…`; 16 cases; `tolerance 0`; comparison "emitted metric token,
  exact; no re-rounding"; label ENGINEERING_ONLY.
- The 16 cases match the predeclared selection in `MAC_M3_DRYRUNS_20261104.md` §1 **exactly**
  (case ids, `append_only_summary` campaign, budget indices 1/2, seeds 104/102/105/103/100/100/105/104,
  metrics `val_score` for the two MLP nodes and `val_auc` for the six OpenML nodes, recorded tokens
  0.718663/0.799443/0.738750/0.909325/0.992351/0.992351/0.941176/0.941176/1.000000/1.000000/
  0.895052/0.895052/0.844538/0.844538/0.889961/0.889961, and kept/discarded decisions). No seed is
  in 7001–7010.
- `cases.jsonl` (16 rows): for every row `replay_token == recorded_token` as a **string**
  (6 decimal places, no re-rounding), `replay_value == recorded_value`, `success: true`, `pass: true`,
  `changed_files: []`, `data_cache_unchanged: true`. The 16 raw worker logs carry the same tokens.
- Independent corroboration of "recorded": every retained `raw/*.log` is **byte-identical** to the
  corresponding archived sweep-1 `run.log` member of the frozen provenance tarball
  (`5bcfb4c2…`): 16/16 `raw` SHA-256 = the plan's `archive.log_sha256`, and all 16
  `archive.log_member`/`patch_member` hashes match the tarball members. The recorded tokens are
  therefore anchored to the preserved sweep-1 run logs, not only to the driver's own copy.
- Environment checks (all present in `replay_plan.json` `environment`, all as the authorization
  requires): host `deepthought`, 40 CPUs; batch wrappers → `/ceph/dwong/r1_prepare_20261025/venv/bin/python`,
  `sys.prefix /ceph/dwong/r1_prepare_20261025/venv`, Python 3.13.15, scikit-learn 1.8.0, NumPy 2.4.4,
  pandas 3.0.3, SciPy 1.17.1; `uv.lock dd42d018…`; 25 Oct freeze `c760b28f…` with only
  `narwhals==2.27.1` added; newest dist-info `2026-10-26T22:09:12.359336Z` (before the 27 Oct
  15:48:34Z launch); package list `c09242ac…` = 28 Oct observation; harness `6adf3859…`
  tracked-clean; /tmp 121.0 GB on verified local XFS, /ceph 380.25 TB free and 1,500,000−421,483 =
  1,078,517 free files ≥ 200; `llm_requests: none`; GPU ban and thread env as declared.
  Because the driver STOPs on any failed check and it did not, "all environment checks passed" is
  supported by the presence of a PASS `summary.json` plus the recorded values.
- **Mechanism state VERIFIED before the first case.** `replay_plan.json`
  `openml_offline_mechanism.state = VERIFIED`, token `r1-e1-openml-amend-20261117`, row
  `R1-E1-OPENML-AMEND`; the embedded report has `written_utc 2026-11-17T00:48:32Z`. In the reviewed
  driver `run()` the order is: `(b)` `enforce()` → corpus/collector/case selection → host/batch/
  env/harness/resource checks → `mechanism.prepare()` (= (i)–(iv)) → `out.mkdir()` →
  `write_json(plan)` → case loop. Evidence: out-dir birth `00:48:32.946924Z`, plan-file birth
  `00:48:32.949924Z` (both retained in `postrun_evidence.log`), first raw-log mtime
  `00:48:36.101936Z`, last `00:49:10.912066Z`, `summary.json` mtime `00:49:11.103Z`. So the plan
  carrying `VERIFIED` predates the first case, and the output directory exists only after the
  identity proof returned (a mechanism failure would have raised before `out.mkdir()`).
- Recomputing `sha256(json.dumps(plan.openml_offline_mechanism.report, sort_keys=True))` yields
  **`473bcb6a…`**, exactly `summary.openml_offline_mechanism.report_sha256`; i.e. the summary's
  mechanism hash binds the plan's report itself, not a lookalike.

## 4. Evidence map (b) and (i)–(iv) — verified against the accepted audit

- **(b) enforced, not assumed.** `environment.openml_offline_mechanism.network` (plan) and
  `summary.post_run.network` record: `seccomp_mode: 2`; `socket(AF_INET)`, `socket(AF_INET6)`,
  `connect` all `OSError errno 101 ENETUNREACH`, `denied: true`, in **in_process**,
  **worker_subprocess** and **post_run**; 21 blocked syscalls (`accept, accept4, bind, connect,
  getpeername, getsockname, getsockopt, io_uring_enter/register/setup, listen, recvfrom, recvmmsg,
  recvmsg, sendmmsg, sendmsg, sendto, setsockopt, shutdown, socket, socketpair`); non-x86-64 and
  x32 syscalls `KILL_PROCESS`. Code order confirms `enforce()` runs before any lazy
  numpy/sklearn/harness import (`LocalWorker` and `check_caches` are imported inside functions
  called later), and `install()` refuses a multi-threaded process, so later threads/children
  inherit the filter. The post-run `reverify()` is an extra child proof after the last case.
- **(i) OpenML data id.** Per node the plan's `dataset_identity.sources` has all five equal:
  `harness_node_spec`, `harness_dataset_json`, `sweep1_cache_check`, `audit_cache_check`,
  `audit_node_spec` → `15/59/1510/29/40/1467`. I re-read the pinned harness commit
  `6adf3859…` (local clone `/private/tmp/h_harness`) with `git show`:
  `nodes/<n>/dataset.json` and `configs/nodes/<n>.yaml` give exactly those ids and names/targets,
  matching the audit's `pinned_harness.node_specs` and the audit's `cache_check` copy.
- **(ii) Loaded-data fingerprint.** The loader is the sweep's own
  `r1.noise.check_caches.check_node`; `r1/noise/check_caches.py` and `r1/noise/e1_noise_floor.py`
  are **byte-identical** at `bbcfc4a9` and at the collector commit `ccb47128…` (`git diff` empty),
  so the same loader/`_prepare_node` the sweep used recomputed the ten fields
  (`dataset_id, cache_source, rows, features, categorical_columns, missing_values, target_name,
  class_counts, positive_label, minority_share`) under the installed `(b)` denial. The record is
  bound by SHA-256 `35e76f37…` and mtime `2026-10-27T15:22:39Z`, and the code requires it strictly
  before the recorded launch `2026-10-27T15:48:34Z`; `cache_check.json` hash/mtime are recorded in
  the plan. Versions compared: Python 3.13.15 / sklearn 1.8.0 / NumPy 2.4.4 / pandas 3.0.3. The
  six recomputed fingerprints in the plan equal the audit's transcribed sweep-1 fields (rows,
  features, missing values, class counts, dataset id, cache source) for all six nodes; the other
  four fields are compared by the hash-pinned mechanism at run time (see Limitations).
- **(iii) ARFF md5.** For all six nodes `arff.arff_md5 == arff.md5_checksum` in the plan and equal
  the audit's `openml_self_description.uncompressed_arff_md5`: `88633c06…` (15), `23dd3c8b…` (59),
  `7aa183d3…` (1510), `a948be96…` (29), `3ab630fb…` (40), `c3d91dc5…` (1467); metadata
  (`api/v1/json/data/<id>.gz`) and `file_id` are consistent per node.
- **(iv) Unchanged audited bytes.** The plan's 24 non-dotfile per-file SHA-256 and 6/6
  `cache_tree_digest` values equal the audit's `current_cache_observation.per_file_sha256` and
  `tree_digest_driver_algorithm` exactly (I compared all values programmatically; zero mismatches).
  `cases.jsonl` carries 24 `openml_offline_cache_checks` (before+after for all 12 OpenML cases),
  each matching the audit tree digest and ARFF md5. `summary.post_run.source_caches` = the six
  audit tree digests. The operator's independent re-read is retained in
  `postrun_integrity2.log` (`ALL_SIX_CACHES_UNCHANGED_AND_AUDITED = True`; 24/24 audited files,
  tree digests match); `.gitignore`/`.gitkeep` are audit-allowed dotfiles anchored by the tree
  digest, as the report says. The driver also re-checks `check_harness(...)['data_caches_sha256']`
  against the pre-run value after the last case (same audit digests) and would STOP on change.
- **No side effects / no lingerers / nothing deleted (operator record).** Worktree tracked-clean
  with only the two untracked output dirs; both retained; real /tmp scratch retained (164 files
  listed in `scratch_inventory.log`); no lingering replay/worker processes; nothing in
  `_to_delete/`; no B.2/audit/label started. The harness `.git` metadata mtime was refreshed by
  read-only `git` commands (disclosed; `git status --porcelain --untracked-files=no` = 0 dirty
  entries; tracked/cache content unchanged). The two retained output dirs are different paths on
  the real deployment; `postrun_evidence.log` prints the run-dir hashes, which equal the copies in
  the report directory.

## 5. Disclosures

Present and substantially faithful: the amended identity standard (report §9.1;
`report.identity.anchor_is_sweep1_file_hash = false` in the plan), the batch-`.venv` wrapper
disclosure (§9.2), bounded reproducibility of the 16 worker evaluations (§9.3), co-tenancy (§9.4)
and "not B.2" (§9.5). The report does not overclaim a B.2/audit result and qualifies the child
probe as "worker-representative". One completeness gap is recorded as Minor 1.

## 6. Limitations of this review

- No network/SSH to deepthought or ceph was used, so live deployment state (exact deployment tips,
  both run dirs retained, no lingerers, batch read-only) rests on the retained operator logs and
  `postrun_*` captures. Those are internally consistent and print hashes equal to the retained
  copies; the `pins.json` values are consistent with both the logs and the accepted mechanism
  review. They cannot be re-derived from this repository.
- The sweep-1 `cache_check.json` (the (ii) expected ten-field fingerprint) lives on the preserved
  batch and is not in the repository; the packet carries its SHA/mtime and the recomputed
  fingerprints plus the audit's six-field transcription. The equality comparison for the remaining
  fields was enforced at run time by the reviewed, hash-pinned mechanism; it cannot be recomputed
  here.
- (iv) per-file equality covers the 24 audited non-dot files; the four allowed dotfiles are
  anchored only by the driver tree digest (the report states this).
- The dry-run output directory stamp `…T004900Z_amend_dryrun` does not match the recorded dry-run
  start/end (00:47:18–00:47:39Z). Ordering is nevertheless unambiguous from `dryrun.log`
  (start/end), the dry plan `written_utc 00:47:39Z`, the inspection at 00:47:53Z and the real start
  at 00:48:07Z. Naming is cosmetic.

## Findings

**Blockers: none.**

**Majors: none.**

**Minors**

1. **Residual-risk list is a condensed subset; must be completed before the PASS is used in the
   paper.** `REPORT.md` §9.1 carries the core amendment risks (no sweep-1 file-hash anchor, audit
   anchoring, fingerprint is a shape/class/label summary, mtime is a filesystem attribute, OpenML
   md5 is self-description, same-uid process outside the filter), but it omits two items the
   accepted mechanism review asked to be stated and the mechanism report marks "must be disclosed":
   (a) the `(b)` denial is **network-only** (not a mount/PID/user-namespace sandbox), and a
   pre-existing/inherited socket fd (e.g. write/`sendfile`, `pidfd_getfd`) is outside what the
   seccomp filter proves — review round-1 Minor 3 / round-2 §R2.6; and (b) the fingerprint
   recomputation does not compare `NODE_INFO` "problems" (mechanism report §5 item 6). Neither
   changes this run's result (fresh worker subprocesses; no socket fds are passed to them; workers
   succeeded), but the run report is the record that the paper will cite, so add one scoping
   sentence (and/or cite the mechanism report §5 residual list) and carry it into the paper.
2. **The first operator cache recheck reads `False`; only the corrected pass reads `True`.** Both
   logs are retained, but `logs/postrun_integrity.log` ends
   `ALL_SIX_CACHES_UNCHANGED_AND_AUDITED = False`, because its first naive file-set comparison
   treats the audit-allowed `.gitignore`/`.gitkeep` in `openml_climate`/`openml_sonar` as extra
   files; `postrun_integrity2.log` uses the audit's allowed-dotfile semantics and is `True`. §5
   of the report explains the dotfile handling and cites the corrected log, but a reader seeing
   the retained `False` can be misled. Add one sentence naming the first pass's stricter
   comparison and its correction.
3. **`logs/postrun_evidence.log` ends with a failed snippet.** Its last section
   (`## plan header/environment/mechanism state`) aborts with
   `SyntaxError: unexpected character after line continuation character`, so the intended excerpt
   is missing from the log. The facts are recoverable from `replay_plan.json`/`pins.json`/the
   extract log, so this is cosmetic, but the retained evidence log should be repaired or annotated.
4. **Two §3 parentheticals lack a retained log line, and one sentence is imprecise.** "Kernel
   seccomp actions available: `kill_process …`" and "the session itself was not under a
   pre-existing filter (`Seccomp: 0` before install)" are not in
   `seccomp_attempt1/attempt2/specific_test` logs; they are operator observations. Also §3's
   "the driver's own probe children resolve the reviewed `r1`" overstates what that probe does:
   the driver child probe is `python -c` stdlib code that imports no `r1` (it needs no
   PYTHONPATH), although the driver process itself resolves reviewed `r1` via `-m` from the
   reviewed cwd. Non-material; retain the observation or drop the parenthetical.

## Observations (not findings)

- Strong positive evidence beyond the report's claims: all 16 retained raw logs are byte-identical
  to the archived sweep-1 `run.log` members (this includes MLP `train_loss` and OpenML `VAL_ACC`),
  the 16 archived patch members match the plan's `patch_sha256`, and the corpus/tarball/audit pins
  are all resolvable from the repository. The plan/dry-plan/summary/report hashes are mutually
  consistent (`report_sha256` recomputed from the plan = `473bcb6a…` = summary value).
- `git diff --check` flags trailing whitespace/new-blank-line-at-EOF in verbatim evidence logs and
  raw worker logs; these are verbatim captures (the raw logs equal the archived run logs) and are
  not a defect.
- `pins.json` `seccomp.in_run_in_process` is built from `summary.post_run.network` in
  `build_pins.py` rather than from the plan's `environment.openml_offline_mechanism.network`
  `in_process`; the two values are identical here and both are retained, so there is no impact.
- The e1 authorization's `5ef9db16` pin is an ancestor of the deployed `bbcfc4a9`; the run
  correctly presents the amended `1b1e2fb2…` driver as the executed pin under
  R1-E1-OPENML-AMEND rather than as the 16 Nov pin.
- The dry-run invocation also carried the amended token (not required, but harmless: with
  `--dry-run` the token only yields `DEFERRED_TO_HOST`, as recorded).

VERDICT: ACCEPTED
