# C3 B.1 e1 environment replay — operator report (ENGINEERING_ONLY)

**Verdict: PASS.** All **16 of 16** predeclared cases reproduced their recorded primary metric
**token exactly (tolerance 0, no re-rounding)** on deepthought, and every driver environment
check passed (`summary.json` `verdict: PASS`, `stop: null`). The R1-E1-OPENML-AMEND offline
mechanism proved **(b)** enforced worker network denial and **(i)–(iv)** dataset identity
**before** the output directory was created (`replay_plan.json`
`openml_offline_mechanism.state = VERIFIED`).

- **Label:** ENGINEERING_ONLY. This is **not B.2**: no audit, no labels, no decision record.
- **Run:** one CPU-only replay, 1 worker, thread env `OMP/OPENBLAS/MKL_NUM_THREADS=1`,
  `CUDA_VISIBLE_DEVICES=""`, `PYTHONDONTWRITEBYTECODE=1`, inside the preserved batch environment.
- **Operator:** single operator session on deepthought, 2026-11-17. No other e1 job was started.
- **Authority:** `origin/main` row **R1-E1-OPENML-AMEND** (`docs/r1/PLAN.md`, amending row
  R1-E1-OPENML, under row R1-E1-AUTH), authorization
  `docs/r1/authorizations/c3_env_replay_20261116.md`, predeclared protocol
  `docs/r1/proposals/C3_ENV_RECONSTRUCTION_REPLAY_DRAFT_20261028.md`.
- **Reviewed code:** branch `r1-e1-openml-amend-20261117` @ reviewed code commit
  **`5bddab73`**, independent review `docs/r1/reviews/E1_AMEND_REVIEW_20261117.md`
  (**ACCEPTED**, round 2 at `5bddab73`); deployed branch tip **`bbcfc4a9`** (the reviewed code
  plus the committed round-1/2 review file only — `git diff 5bddab73..bbcfc4a9` is that one
  file, +133 lines).
- **Deployment:** fresh clone `/ceph/dwong/r1_e1_20261117/agent_paper_B`, detached at
  `bbcfc4a9`, `git status --porcelain` empty, `16185b0b` verified an ancestor.

## 0. Result at a glance

| Item | Observed |
|---|---|
| Cases planned / run / passed | 16 / 16 / 16 |
| Zero-tolerance pass rule | `tolerance: 0`, comparison "emitted metric token, exact; no re-rounding" |
| Driver verdict (`summary.json`) | `PASS`, `stop: null` |
| OpenML mechanism state (`replay_plan.json`) | `VERIFIED` (token `r1-e1-openml-amend-20261117`, row R1-E1-OPENML-AMEND) |
| (b) network denial | installed and proven in-process **and** in a worker-representative child; re-proven post-run (`Seccomp: 2`, errno 101 / ENETUNREACH for AF_INET, AF_INET6, connect) |
| (i) data ids | 15 / 59 / 1510 / 29 / 40 / 1467 (five sources agree per node) |
| (ii) loaded-data fingerprints | recomputed on the preserved cache, equal value by value for all six nodes |
| (iii) ARFF md5 = OpenML `md5_checksum` | equal for all six nodes |
| (iv) unchanged audited bytes | 24/24 per-file SHA-256 and 6/6 tree digests equal to `OFFLINE_MECHANISM_AUDIT.json`; re-verified before/after each case, after the last case, and independently by the operator post-run |
| Environment checks | all passed (see §6) |
| Real-run exit code | 0 |
| Workspace changes from the replay | none in the paper code; only the two new output directories under `results/r1/engineering/` |

## 1. What was run, in the authorized order

All commands are verbatim in `commands.txt`; raw output in `logs/`.

1. **Fresh deployment** of the reviewed branch tip (`bbcfc4a9`, code identical to the reviewed
   `5bddab73`) at `/ceph/dwong/r1_e1_20261117/agent_paper_B`, clean tree. Three amended pins
   verified (§2).
2. **Linux-only seccomp test first**, on deepthought, before any co-tenancy/dry/real step:
   `pytest r1/tests/test_e1_offline_network.py` → **15 passed, 1 Linux-skip**, including
   `test_linux_install_denies_sockets` **PASSED** (also run alone, verbose:
   `logs/seccomp_specific_test.log`). See §3 for one test-invocation artifact disclosed in full.
3. **Co-tenancy check** immediately before the dry run and again immediately before the real run:
   load 15.79 and 16.63 on 40 CPUs ⇒ **≈24.2 / 23.4 cores free**, both ≥ the required 10
   (`logs/cotenancy.log`). Pre-existing unrelated jobs (jepa_noise R2 diagnostics, paperc
   headroom audit) are listed there; none is part of this work.
4. **Dry run first, into a new output directory** (`…_amend_dryrun`), exit **0**, 16 cases;
   plan retained and inspected (`openml_offline_mechanism.state = DEFERRED_TO_HOST`,
   `environment: DEFERRED_TO_HOST`, all 16 cases and recorded tokens recovered exactly).
5. **Real run, into a different new output directory** (`…_amend_real`), same amended token,
   exit **0**, `PASS`, 16/16.
6. **Post-run:** every source cache and the network denial re-proven by the driver; operator
   re-read the six cache trees against the audit (6/6 tree digests, 24/24 file hashes), the
   anchors, and the harness (`logs/postrun_integrity.log`, `logs/postrun_integrity2.log`).
   Nothing deleted; the `/tmp` scratch was retained.

**Dry run** (new dir; retained):

```
. <batch>/env.sh
export AR_HARNESS_ROOT=<batch>/autoresearch_harness
export PYTHONDONTWRITEBYTECODE=1
python -B -m r1.scripts.c3_env_replay \
  --paper-root /ceph/dwong/r1_e1_20261117/agent_paper_B \
  --harness <batch>/autoresearch_harness --batch <batch> \
  --scratch /tmp/r1_c3_env_replay_20261117T004900Z_amend_dry \
  --out /ceph/dwong/r1_e1_20261117/agent_paper_B/results/r1/engineering/C3_env_replay_20261117T004900Z_amend_dryrun \
  --min-free-bytes 2147483648 --dry-run \
  --openml-offline-mechanism r1-e1-openml-amend-20261117
```

→ `{"label": "DRYRUN", "cases": 16, "nodes": [digits_mlp, openml_breast_w, openml_climate,
openml_credit_approval, openml_ionosphere, openml_sonar, openml_wdbc, tabular_mlp]}`,
exit 0, plan SHA-256 `efc2231119602b3c74f1f1a9ec82abc550af00f43a8707c933b0b099e7599e23`
(`dryrun/replay_plan.json`). The scratch path was not created, as the dry run specifies.

**Real run** (different new dir; same token):

```
python -B -m r1.scripts.c3_env_replay \
  --paper-root /ceph/dwong/r1_e1_20261117/agent_paper_B \
  --harness <batch>/autoresearch_harness --batch <batch> \
  --scratch /tmp/r1_c3_env_replay_20261117T004807Z_amend_real \
  --out /ceph/dwong/r1_e1_20261117/agent_paper_B/results/r1/engineering/C3_env_replay_20261117T004807Z_amend_real \
  --min-free-bytes 2147483648 \
  --openml-offline-mechanism r1-e1-openml-amend-20261117
```

→ exit 0; final stdout line:

```json
{"label": "ENGINEERING_ONLY", "cases_planned": 16, "cases_run": 16, "cases_passed": 16,
 "stop": null, "tolerance": 0,
 "replay_plan_sha256": "23a17665b8666251bd20d23ef0beccc814550000fbe47843a960f598781b4dcd",
 "cases_sha256": "ce6ed7b38b987d5bb6ed89472ce295ef76223e90935eb758d8d3c168531d6aba",
 "verdict": "PASS", "openml_offline_mechanism": {...}}
```

Run timing (UTC, from plan/summary/artifact mtimes): command started 00:48:07; `(b)` installed
first; source + environment + harness + resource checks; `(i)–(iv)` proved → output directory
born **00:48:32.946Z**, plan written **00:48:32.949Z** with `state = VERIFIED`; first case raw
log 00:48:36.102Z; last case raw log 00:49:10.912Z; `summary.json` 00:49:11.103Z. Thus the plan
carrying `VERIFIED` existed before the first case, and the output directory exists only after
the identity proof returned (code order in `r1/scripts/c3_env_replay.py` `run()`: `prepare()` →
`out.mkdir()`).

## 2. Pins (amended — cite R1-E1-OPENML-AMEND)

The e1 authorization's driver pin `5ef9db16…` / driver SHA-256
`a9cad4d544bdf061c42ecb4b4c2d3d10d8bc94342574d9a37489bd4b179aa7d8` **predates the amendment**
and is **not** what ran. Full machine-readable pins: `pins.json`.

| Item | Value |
|---|---|
| Deployed branch / tip | `r1-e1-openml-amend-20261117` @ `bbcfc4a9d337717c6f03ca6e8929fbbbb929cf3d` |
| Reviewed code commit | `5bddab731f6b4fa226e37dd8dc6d7e6f202232e1` (review ACCEPTED) |
| Code delta reviewed→deployed | `docs/r1/reviews/E1_AMEND_REVIEW_20261117.md` only (+133 lines) |
| Amended driver `r1/scripts/c3_env_replay.py` | **SHA-256 `1b1e2fb229e78a82b56f1b8c9e45d6bc36412facf26d89f05bf6acb830a7e7e0`**, git blob `db55a2cc` |
| Mechanism module `r1/c3/e1_openml_offline.py` | **SHA-256 `6bcc50fe2544afd7ae1fdf86f9061eeb037fc3a9f35fdd6d3a9d64213e97efa3`** |
| Network module `r1/c3/e1_offline_network.py` | SHA-256 `6c9a95a84fb4e39fdd6a7a80ddfc8fb32c9b236b4deca77f0f7eb0f217c6a786` |
| Test module `test_e1_openml_offline_mechanism.py` | SHA-256 `faec8865a8f1f69e33474a335aa31688440b8a7ccc53ba012ddde681990ab8d3` |
| Test module `test_e1_offline_network.py` | SHA-256 `6ea882cc8057cacf5d7b9ba22c49a28dc031e2982d73360db1c267c69a99714f` |
| Test module `test_e1_openml_offline_wiring.py` | SHA-256 `2b4d5275df1800f1df9fd034f1ad6bf48b5e202afb51e01e7b3140b6959d0ba1` |
| Reviewed audit `OFFLINE_MECHANISM_AUDIT.json` | SHA-256 `9f14c879973ff4080655a2e108e6e7a1aad2b031d96d4f96e914921ddaa190b7` (byte-identical to `5d73550a`) |
| Harness | `/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw/autoresearch_harness`, HEAD `6adf3859de66c4814fcf376eed59880fbd8eeaf7`, tracked-clean; `uv.lock` `dd42d018…` |
| Sweep-1 record `cache_check.json` | SHA-256 `35e76f37fcc4925a7896f6cf0bc2ab2bbf8647adfc763729da5a8e93325944f9`, mtime `2026-10-27T16:22:39.992+0100` = `15:22:39Z`, before launch `15:48:34Z` |
| Interpreter | batch wrappers → `/ceph/dwong/r1_prepare_20261025/venv/bin/python`; realpath `…/python/cpython-3.13.15-linux-x86_64-gnu/bin/python3.13`; Python 3.13.15; scikit-learn 1.8.0, NumPy 2.4.4, pandas 3.0.3, SciPy 1.17.1; prefix `/ceph/dwong/r1_prepare_20261025/venv` |
| Packages vs 25 Oct freeze | only addition `narwhals==2.27.1`; no removed/changed; package-list SHA-256 `c09242ac…` (= 28 Oct observation) |
| 25 Oct freeze | `/ceph/dwong/r1_prepare_20261025/freeze_with_lightgbm.txt` `c760b28f…` |
| Newest dist-info mtime | `2026-10-26T22:09:12.359336Z` (before launch) |
| Host | deepthought, Linux x86_64 kernel `4.18.0-553.156.1.el8_10.x86_64`, 40 CPUs, workers 1 |

## 3. Linux-only seccomp test — result, and one disclosed test-invocation artifact

**Result on deepthought:** `test_linux_install_denies_sockets` **PASSED** in the batch venv
(Python 3.13.15, pytest 9.0.3):
`r1/tests/test_e1_offline_network.py::test_linux_install_denies_sockets PASSED [100%]`
(`logs/seccomp_specific_test.log`); the full module ran **15 passed, 1 skipped** (the skip is
`test_install_refuses_the_current_non_linux_host`, which is Linux-skipped by design)
(`logs/seccomp_attempt2.log`). Kernel seccomp actions available: `kill_process kill_thread trap
errno trace log allow`; the session itself was **not** under a pre-existing filter (`Seccomp: 0`
before install), so the test installed and proved its own.

**Disclosed artifact (both invocations retained, verbatim):** the *first* invocation
(`logs/seccomp_attempt1.log`) failed — **not** in the mechanism and **not** in a seccomp call.
The test spawns a disposable child script; the batch `env.sh` exports
`PYTHONPATH=<batch>/agent_paper_B`, the **stale sweep paper checkout** (`22cc8936`, which has no
`r1/c3/e1_offline_network.py`). Because a child script's `sys.path[0]` is its own `/tmp`
directory, that `PYTHONPATH` entry won over the deployed checkout and the child raised
`ImportError: cannot import name 'e1_offline_network' from 'r1.c3'` **before any filter install**.
The parent (`python -m pytest`, cwd = reviewed checkout) resolved the reviewed module correctly;
14 fixture tests passed in that same failed invocation. The corrected invocation prepends the
deployed reviewed checkout to `PYTHONPATH` so the disposable child imports the reviewed module —
the environment the test is written for — and it passes. **No STOP condition is implicated: no
seccomp install or probe was attempted in the failed invocation.** The real run itself does not
depend on this: the driver is started with cwd = the reviewed checkout (so `python -m` and the
driver's own probe children resolve the reviewed `r1`), and its in-run (b) proof is recorded in
`replay_plan.json`/`summary.json` (§5).

## 4. Dry-run inspection

`dryrun/replay_plan.json` (SHA-256 `efc22311…`): `label DRYRUN`, schema `r1.c3_env_replay/1`,
`tolerance 0`, comparison "emitted metric token, exact; no re-rounding", `environment:
DEFERRED_TO_HOST`, `harness_commit 6adf3859…`, thread env `OMP/OPENBLAS/MKL_NUM_THREADS=1`,
`llm_requests: none`, `openml_offline_mechanism.state = DEFERRED_TO_HOST`, **16 cases** matching
the predeclared list (4 MLP + 12 OpenML; per node the smallest-seed `append_only_summary` campaign,
budget indices 1 and 2), corpus binds index `812468e2…`/sidecar `bb6d891c…`/frozen trees
`6b1c0c61…`+`468e57ce…` and collector `ccb4712`. `logs/dryrun_plan_inspection.log`.

## 5. Identity + no-network evidence map (b)/(i)–(iv)

The mechanism (`r1/c3/e1_openml_offline.py`) ran **before** `out.mkdir()` and **after** the
seccomp filter was installed; its full report is inside `replay_plan.json`
`environment.openml_offline_mechanism`. Machine-readable clause-by-clause mapping:
`EVIDENCE_MAP.md`. Summary:

- **(b) no network — enforced, not assumed.** Irreversible Linux x86-64 seccomp filter
  (`PR_SET_NO_NEW_PRIVS` + `SECCOMP_SET_MODE_FILTER`, default allow, 21 syscalls returning
  `ERRNO|101`, non-x86-64 and x32 killed), installed at the very start of `run()` **before any
  numpy/sklearn import**, so every later thread/child inherits it. Proven in-process **and** in a
  fresh worker-representative child (`seccomp_mode: 2`; `socket(AF_INET)`, `socket(AF_INET6)`,
  `connect` → errno 101 ENETUNREACH), and re-proven after the last case. All 16 workers ran under
  the filter; no download occurred and no `paperc`/network fallback was used.
- **(i) data id.** Pinned harness specs read from **commit `6adf3859`** (`git show`, not the
  worktree), harness `dataset.json`, sweep-1 `cache_check.json`, the audit's cache_check copy and
  the audit's `node_specs` all agree, per node: `openml_breast_w 15`, `openml_ionosphere 59`,
  `openml_wdbc 1510`, `openml_credit_approval 29`, `openml_sonar 40`, `openml_climate 1467`;
  dataset name and target cross-checked.
- **(ii) loaded-data fingerprint.** Recomputed on the preserved cache with the sweep's own
  `r1.noise.check_caches.check_node` under the already-installed (b) denial; the exact ten-field
  fingerprint equals the sweep-1 record value by value for all six nodes (rows/features/
  categorical/missing/target/class counts/positive label/minority share/dataset id/cache source),
  with the sweep-1 Python 3.13.15 / scikit-learn 1.8.0 / NumPy 2.4.4 / pandas 3.0.3. Record
  bound by SHA-256 `35e76f37…`, mtime `15:22:39Z` (truncated to the recorded second) and strictly
  before the `15:48:34Z` launch.
- **(iii) ARFF md5.** Each cache ARFF's md5 equals the OpenML `md5_checksum` in the cache's own
  `api/v1/json/data/<id>.gz` metadata, with metadata `id` and `file_id` consistent:
  `88633c06…` (15), `23dd3c8b…` (59), `7aa183d3…` (1510), `a948be96…` (29), `3ab630fb…` (40),
  `c3d91dc5…` (1467).
- **(iv) unchanged audited bytes.** All 24 non-dotfile cache files' SHA-256 and all six
  driver-algorithm tree digests equal `OFFLINE_MECHANISM_AUDIT.json` (`88f68825…`, `1079cb09…`,
  `075915dc…`, `05cf63a2…`, `ccca8605…`, `73c5af11…`); `.gitignore`/`.gitkeep` are
  audit-allowed dotfiles covered by the tree digest. Re-verified on a per-case private copy
  **before and after** each of the 12 OpenML cases (`cases.jsonl`
  `openml_offline_cache_checks`: `before`,`after`), on the source caches after the last case
  (`summary.json` `post_run.source_caches` = the audit digests), and independently re-read by the
  operator post-run (`logs/postrun_integrity2.log`: `ALL_SIX_CACHES_UNCHANGED_AND_AUDITED = True`).

## 6. Driver environment checks (all passed; the driver STOPs otherwise)

From `replay_plan.json` `environment` (see `pins.json` for the full values): batch wrappers exec
the recorded shared venv (`python` and `python3` identical); driver ran in the batch venv
(`sys.prefix == /ceph/dwong/r1_prepare_20261025/venv`); Python 3.13.15 and scikit-learn 1.8.0 /
NumPy 2.4.4 / pandas 3.0.3 / SciPy 1.17.1; `uv.lock` `dd42d018…`; 25 Oct freeze `c760b28f…`
with only addition `narwhals==2.27.1`; newest dist-info `2026-10-26T22:09:12Z` < launch; package
list `c09242ac…` = 28 Oct observation; worker `python3` on the replay PATH is the batch wrapper;
harness clean at `6adf3859…` with the six OpenML caches present; scratch on verified local XFS
`/tmp`, free 121.0 GB ≥ 2 GiB estimate; `/ceph` free 380.25 TB ≥ 50 GiB and file-count headroom
1,500,000 − 421,483 = 1,078,517 files ≥ 200 reserve; host `deepthought`.

## 7. Per-case results (zero tolerance: emitted token == recorded token)

`cases.jsonl` rows, 16/16 `pass: true`, `changed_files: []` for every case,
`data_cache_unchanged: true`, success true. Metric: `val_score` for the two MLP nodes, `val_auc`
for the six OpenML nodes.

| case | recorded token | replayed token | exact | pass |
|---|---|---|---|---|
| digits_mlp__s104:t001 | 0.718663 | 0.718663 | yes | yes |
| digits_mlp__s104:t002 | 0.799443 | 0.799443 | yes | yes |
| tabular_mlp__s102:t001 | 0.738750 | 0.738750 | yes | yes |
| tabular_mlp__s102:t002 | 0.909325 | 0.909325 | yes | yes |
| openml_breast_w__s105:t001 | 0.992351 | 0.992351 | yes | yes |
| openml_breast_w__s105:t002 | 0.992351 | 0.992351 | yes | yes |
| openml_ionosphere__s103:t001 | 0.941176 | 0.941176 | yes | yes |
| openml_ionosphere__s103:t002 | 0.941176 | 0.941176 | yes | yes |
| openml_wdbc__s100:t001 | 1.000000 | 1.000000 | yes | yes |
| openml_wdbc__s100:t002 | 1.000000 | 1.000000 | yes | yes |
| openml_credit_approval__s100:t001 | 0.895052 | 0.895052 | yes | yes |
| openml_credit_approval__s100:t002 | 0.895052 | 0.895052 | yes | yes |
| openml_sonar__s105:t001 | 0.844538 | 0.844538 | yes | yes |
| openml_sonar__s105:t002 | 0.844538 | 0.844538 | yes | yes |
| openml_climate__s104:t001 | 0.889961 | 0.889961 | yes | yes |
| openml_climate__s104:t002 | 0.889961 | 0.889961 | yes | yes |

Seeds: the campaign instance seed is reused as `train_seed = split_seed` (digits_mlp 104,
tabular_mlp 102, breast_w 105, ionosphere 103, wdbc 100, credit_approval 100, sonar 105,
climate 104); none is in 7001–7010. Raw worker logs: `raw/*.log`.

## 8. State left behind (nothing deleted, nothing reused)

| Item | State |
|---|---|
| Deployment checkout | `/ceph/dwong/r1_e1_20261117/agent_paper_B` @ `bbcfc4a9`, tracked-clean; only two untracked output dirs (below) |
| Dry-run out (retained) | `.../results/r1/engineering/C3_env_replay_20261117T004900Z_amend_dryrun/` |
| Real out (retained) | `.../results/r1/engineering/C3_env_replay_20261117T004807Z_amend_real/` |
| Scratch (retained) | `/tmp/r1_c3_env_replay_20261117T004807Z_amend_real` |
| Preserved batch | read-only; `cache_check.json` SHA/mtime unchanged; harness tracked-clean at `6adf3859…`, `uv.lock` unchanged; no tracked/cache content changed (the driver's own read-only `git` commands may refresh transient `.git` metadata; `logs/postrun_integrity2.log` records 0 dirty entries) |
| Processes | no replay/worker processes left running |
| Deletions | none; nothing moved to `_to_delete/` |
| B.2 / audit / labels | none started |

## 9. Disclosures and residual risks (must carry into the paper/report if this PASS is used)

1. **Identity standard.** Identity rests on the **amended** evidence — sweep-1 **data id**,
   sweep-1 **loaded-data fingerprint**, OpenML **md5 self-consistency**, and **unchanged audited
   bytes** — **not** on a file hash recorded by sweep 1. `report.identity.anchor_is_sweep1_file_hash
   = false`. The amendment's residual risks stand: the surviving cache bytes are not anchored by
   a hash the sweep-1 launch wrote; (iv) anchors them to the 16 Nov audit; the fingerprint is a
   shape/class/label summary; mtime is a filesystem attribute; OpenML md5 is OpenML's own archive
   checksum. A same-uid process outside the replay is outside the (b) filter (one-operator
   discipline; no other e1 job was started).
2. **Batch venv.** The batch `.venv` executables were **wrappers to the shared venv**
   `/ceph/dwong/r1_prepare_20261025/venv`, not a separately built venv; the driver checks this and
   ran inside that venv.
3. **Scope.** A passed replay is a **bounded reproducibility check of these 16 worker
   evaluations**, reconstructed from `uv.lock` + the batch venv and confirmed by replay; no freeze
   snapshot was taken at launch. It is not proof that every original dependency or all 288 roots
   were identical, and it says nothing about LLM seed replay (R1-SWEEP1-CACHE-DISCLOSURE).
4. **Co-tenancy.** Pre-existing unrelated deepthought work (jepa_noise R2 diagnostics, paperc
   headroom audit, other users) was running; the required ≥10-of-40-free floor held at both
   checks, and the exact-token result is unaffected. This is disclosed so the reviewer can judge
   it; the authorization's co-tenancy requirement was met.
5. **Not B.2.** This run does not start B.2, authorizes no audit, and produces no labels; the
   decision-record sentence for a confirmed replay only becomes usable **after independent review
   accepts this report**.

## 10. What the independent review must verify

1. **Authority/pins.** Branch `ops-e1-replay-amend-20261117` from current `main` (`26177d82`);
   the amended driver/mechanism/test SHA-256 values in §2 match the run code; the
   authorization's `5ef9db16`/`a9cad4d5` is correctly presented as predating the amendment (not
   as the executed driver); the deployed tip is `bbcfc4a9` with code equal to reviewed `5bddab73`.
2. **The three gate steps and their order.** Linux-only seccomp test **before** the dry/real runs,
   with the disclosed first-invocation `PYTHONPATH` artifact assessed as non-mechanism; co-tenancy
   ≥10 free cores at both checks; dry run first into a new dir; real run into a **different** new
   dir with the amended token.
3. **Identity/no-network evidence.** (b) seccomp filter installed before library import, proven
   in-process and in a child, re-proven post-run (`Seccomp: 2`, errno 101); (i) five-source id
   agreement from `git show 6adf3859`; (ii) exact ten-field fingerprint recomputation with the
   sweep's loader and versions, record hash/mtime/pre-launch binding; (iii) ARFF md5 vs OpenML
   metadata; (iv) 24 file hashes + 6 tree digests vs the audit, before/after per case and
   post-run source re-verify; `state = VERIFIED` in the plan **before** the first case and the
   output dir created only after the proof.
4. **Pass rule.** 16/16 emitted tokens exactly equal the recorded tokens (no re-rounding,
   `tolerance 0`), `changed_files` empty, `data_cache_unchanged` true, `summary.json`
   `verdict: PASS`, every environment check passed.
5. **No side effects.** No B.2/audit/label; `main` and `ops-e1-replay-20261116` untouched; nothing
   deleted; batch/caches unchanged; `/tmp` scratch and both output dirs retained; the operator's
   `postrun_integrity` re-reads reproduce the audit digests.
6. **Disclosures.** §9 items are present in the run record and must be carried verbatim in
   substance into the paper if the PASS is used.

## 11. Evidence inventory (this directory)

- `REPORT.md` — this report; `summary.json` — driver PASS (real run).
- `cases.jsonl` — 16 case rows; `replay_plan.json` — real-run plan with the full (i)–(iv)+(b)
  report and `state = VERIFIED`; `raw/` — 16 raw worker logs.
- `dryrun/replay_plan.json` — retained dry-run plan.
- `pins.json` — all pins (code, harness, batch, venv/freeze, host, co-tenancy, seccomp, run).
- `commands.txt` — exact commands and exit codes.
- `EVIDENCE_MAP.md` — clause → code path → runtime evidence mapping.
- `logs/` — real/stdout logs, dry-run log, co-tenancy, preflight, post-run integrity, seccomp
  (attempt 1, attempt 2, specific test), dry-run plan inspection, scratch inventory.
- `SHA256SUMS.txt` — hashes of every evidence file here.
