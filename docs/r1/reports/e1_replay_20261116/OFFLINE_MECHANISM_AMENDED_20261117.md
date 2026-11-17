# C3 B.1 e1 offline mechanism — R1-E1-OPENML-AMEND (17 November 2026)

**Label: ENGINEERING_ONLY. Status: reviewed code prepared; NOT run.** No e1 run, no dry run,
no worker, no job, no B.2, no label and no write on deepthought/ceph was performed by this
branch. This note documents the mechanism the author's amended row requires, the code and
tests that implement it, the exact run chain that the operator will execute **only after an
independent review accepts this branch**, and the residual risks that the report and paper
must disclose.

- **Authority:** `origin/main` @ `16185b0b` row **R1-E1-OPENML-AMEND** (`docs/r1/PLAN.md` §10,
  line 1241), amending row **R1-E1-OPENML** (line 1223), under row **R1-E1-AUTH** (line 1211).
  Basis: identity audit `e1-openml-20261116` @ `5d73550a` (report
  `docs/r1/reports/e1_replay_20261116/OFFLINE_MECHANISM_20261116.md`, machine record
  `docs/r1/reports/e1_replay_20261116/OFFLINE_MECHANISM_AUDIT.json`, accepted independent
  review `docs/r1/reviews/E1_OPENML_REVIEW_20261116.md`) and the e1 STOP report
  `ops-e1-replay-20261116` @ `fc7d8e4e` (`docs/r1/reviews/E1_REPLAY_REVIEW_20261116.md`).
  Authorization: `docs/r1/authorizations/c3_env_replay_20261116.md`. Predeclared protocol:
  `docs/r1/proposals/C3_ENV_RECONSTRUCTION_REPLAY_DRAFT_20261028.md`. Driver base: the
  reviewed `r1/scripts/c3_env_replay.py` at `5ef9db16…` (SHA-256
  `a9cad4d544bdf061c42ecb4b4c2d3d10d8bc94342574d9a37489bd4b179aa7d8`).
- **Branch:** `r1-e1-openml-amend-20261117`, from `origin/main` = `16185b0b`. It changes the
  driver and adds two mechanism modules, three test modules, and this report; it also carries
  the accepted audit artifacts byte-identical from `5d73550a` (they were not yet on `main`).
- **No frozen numeric input is changed.** The 16-case selection, seeds, recovered
  configurations, environment pins, thread environment, GPU ban, zero-tolerance pass rule and
  the "emit token exact, no re-rounding" comparison are untouched. The default behaviour with
  no flag is the original OpenML hard STOP, byte-for-byte the same message.

## 1. What the amendment requires

The amended row replaces the original requirement (a) "prove the datasets are identical to
sweep 1 by the identity sweep 1 recorded" — which the audit found **unprovable**, because sweep 1
recorded no dataset file/tree hash — with a composite evidence standard. An OpenML case may run
only if all of the following hold at the same time, on the same preserved cache:

| Clause | Requirement |
|---|---|
| **(i)** | The OpenML data id equals the sweep-1 record. Pinned harness NodeSpecs at `6adf3859…` give 15/59/1510/29/40/1467. |
| **(ii)** | The **loaded-data fingerprint** sweep 1 recorded in the preserved batch `cache_check.json` (SHA-256 `35e76f37…`, mtime `2026-10-27T15:22:39Z`, 26 min before the `15:48:34Z` launch) is recomputed **equal, value by value**, with the same cache. |
| **(iii)** | The cache **ARFF file's md5** equals the OpenML `md5_checksum` carried in the cache's own `api/v1/json/data/<id>.gz` metadata. |
| **(iv)** | Every cache file's **SHA-256**, and the whole cache **tree digest**, is unchanged before and after use and equals the values recorded in `OFFLINE_MECHANISM_AUDIT.json` (per-file map and `tree_digest_driver_algorithm`). |
| **(b)** | Worker subprocesses have **no network** — enforced, not assumed — and cannot download. Until (i)–(iv) and (b) all pass, the original OpenML hard STOP stands. |

## 2. Evidence map

### 2.1 The two sweep-1 anchors

| Anchor | Path | Binding |
|---|---|---|
| Sweep-1 record | `/ceph/dwong/r1_prepare_20261025/r1_c3_sweep_ENGINEERING_ONLY_20261027_2YSBbw/cache_check.json` | SHA-256 `35e76f37fcc4925a7896f6cf0bc2ab2bbf8647adfc763729da5a8e93325944f9`; mtime `2026-10-27T15:22:39Z`; contains per-node `dataset_id`, `cache_source`, `cache_path` and the loaded-data fingerprint (rows, features, categorical columns, missing values, target, class counts, positive label, minority share) and **no hash field** |
| Reviewed audit | `docs/r1/reports/e1_replay_20261116/OFFLINE_MECHANISM_AUDIT.json` | SHA-256 `9f14c879973ff4080655a2e108e6e7a1aad2b031d96d4f96e914921ddaa190b7`; source commit `5d73550a`; it records the surviving per-file SHA-256 values, the per-node tree digests, the pinned NodeSpecs, the OpenML md5 self-description and the batch record hashes |

The audit's verdict is "identity unprovable by sweep-1 recorded *hashes*", which is exactly why
the author amended the standard. The mechanism **uses the audit only as the byte anchor for
(iv)** and as a cross-check for (i)/(iii). It does **not** claim the audit is a sweep-1 file
hash. `report.identity.anchor_is_sweep1_file_hash = false` is written into every replay plan.

### 2.2 Clause-by-clause implementation

| Clause | What the driver verifies | Code |
|---|---|---|
| (i) data id | `configs/nodes/<node>.yaml` `dataset.dataset_id` and `nodes/<node>/dataset.json` `dataset_id` **read from the pinned commit** (`git show 6adf3859:…`), the sweep-1 `cache_check.json` `dataset_id`, the audit `pinned_harness.node_specs`, and the audit's own `cache_check` copy all equal the pinned id 15/59/1510/29/40/1467; the dataset name and target also match. A missing id anywhere is a STOP. | `e1_openml_offline.verify_dataset_ids` |
| (ii) fingerprint | `cache_check.json` is bound by SHA-256, by mtime equal to the recorded `2026-10-27T15:22:39Z`, and by being strictly before the recorded launch. The exact field set (`dataset_id`, `cache_source`, `rows`, `features`, `categorical_columns`, `missing_values`, `target_name`, `class_counts`, `positive_label`, `minority_share`) is recomputed with the **same loader** the sweep used (`r1.noise.check_caches.check_node`) on the preserved harness cache, and compared value by value; the recorded Python/scikit-learn/NumPy/pandas versions must equal the current ones. The recomputation runs **after** (b) is installed, with the socket module also disabled in-process. | `bind_cache_check`, `verify_fingerprints`, `default_fingerprint_loader` |
| (iii) ARFF md5 | Decompress `api/v1/json/data/<id>.gz`, read `data_set_description.md5_checksum`, `file_id` and `id`; decompress the `data/v1/download/<file_id>/<name>.arff.gz`; require `md5(raw ARFF) == md5_checksum`, the metadata id equal to the node id, the ARFF path consistent with `file_id`, and the audit's OpenML self-description to agree. | `_arff_consistency`, `verify_arff_md5` |
| (iv) unchanged bytes | Walk the whole `nodes/<node>/data_cache` tree rejecting symlinks/irregular entries; require the non-dotfile file set to equal the audit's four files and every SHA-256 to equal the audit; recompute the driver's own tree digest and require the audit's `tree_digest_driver_algorithm` value. Only `.gitignore`/`.gitkeep` may sit outside the four files, and they are covered by the tree digest. Re-verified **before and after** each case's private cache copy (`verify_case_cache(..., 'before'/'after')`) and again on the source cache after the last case. | `snapshot_cache`, `verify_case_cache`, `verify_source_caches` |
| (b) no network | An irreversible Linux x86-64 seccomp filter (`PR_SET_NO_NEW_PRIVS` + `SECCOMP_SET_MODE_FILTER`) installed in the replay driver **before** the identity load and therefore inherited by every worker subprocess: `socket`, `connect`, `sendto/sendmsg`, `bind`, `listen`, `accept*`, `socketpair`, `getsock*`, `io_uring_*` all return `ENETUNREACH`; non-x86-64 and x32-ABI syscalls are killed. Proven in-process and in a fresh worker-representative child (all three probes must fail with errno 101 and the child must report `Seccomp: 2`), and re-proven after the last case. Non-Linux host, single-thread check failure, install error or any unproven probe is a STOP. | `e1_offline_network.install/enforce/reverify` |

### 2.3 Builder re-verification of the surviving bytes (read-only, 2026-11-17)

The six preserved caches and the sweep-1 record were re-read over read-only SSH
(`dwong@deepthought.etp.kit.edu`, `ls/stat/sha256sum`-equivalent Python reads only) to confirm
the audit numbers this mechanism pins. Nothing was written; no case ran.

| Node | OpenML id | cache tree digest (driver algorithm) | ARFF md5 = OpenML `md5_checksum` |
|---|---|---|---|
| `openml_breast_w` | 15 | `88f68825a3d93e4724b453346c6bc7c360e9e7594658a13b3761589ec359f487` | `88633c065209e7a57323d3d7f2d00546` |
| `openml_ionosphere` | 59 | `1079cb09c620388b48062855a8849337cd132fcd8cf1c31c4cece6a578cb0c4e` | `23dd3c8b5693e2848901fd1a0248ef42` |
| `openml_wdbc` | 1510 | `075915dc1fa10dc7a3f736a5d297765dd057e767becb38ee59b97bace868ebf3` | `7aa183d3657e364911ced0cbd6b272bd` |
| `openml_credit_approval` | 29 | `05cf63a22a3c4e3a391fac7eb78fe6a36ba6c5b9e9071bee1e05760aef97dcb3` | `a948be968270a823fce432227c1aa36e` |
| `openml_sonar` | 40 | `ccca8605802002e6df8fef3080a6169c32a91ad8b4c401ad0cf173f16137020c` | `3ab630fbbfe25ab48b9bb47ce5759203` |
| `openml_climate` | 1467 | `73c5af1187710d75c717db532b74c287238d97c91d603351c2d865608c6b1f5d` | `c3d91dc521c59323cdfba6336a5d59a0` |

All 24 per-file SHA-256 values and all six tree digests matched
`OFFLINE_MECHANISM_AUDIT.json`; `cache_check.json` matched SHA-256 `35e76f37…` and mtime
`2026-10-27T16:22:39.992 +0100`; the audit file matched its `SHA256SUMS.txt` entry
(`9f14c879…`). This re-verification is an observation, not a new anchor.

## 3. The exact chain (and every STOP)

### 3.1 Behind the flag

The mechanism is opt-in only, through the explicit reviewed value (both forms are pinned to the
same token; anything else is a STOP):

```
--openml-offline-mechanism r1-e1-openml-amend-20261117
R1_E1_OPENML_OFFLINE_MECHANISM=r1-e1-openml-amend-20261117
```

Without it, `run()` raises the original OpenML STOP unchanged:
`STOP: OpenML offline dataset availability and worker network denial are not verified; no replay scheduled`
(and `execute_case` keeps the per-case form of the same STOP). A dry run never needs the flag;
with it, the plan records `openml_offline_mechanism.state = DEFERRED_TO_HOST`.

### 3.2 Order inside `run()` for a real run

1. Output-new and output outside the batch/corpus; no LLM client modules loaded.
2. Token validation. For a real run with the mechanism, **enforce (b) immediately** — the
   seccomp filter is installed before the frozen-corpus check and before any import
   (`numpy`/`scikit-learn`) that could create a thread, so every later child inherits it and the
   single-thread precondition is met by construction. Failure is a STOP before anything is
   written.
3. Frozen corpus, collector binding and the fixed 16 cases (unchanged pre-existing checks). If
   any case is OpenML and no reviewed token was given, the original OpenML STOP fires here.
4. Host = deepthought, `--harness/--batch/--scratch` present, harness = `batch/autoresearch_harness`,
   `AR_HARNESS_ROOT` matches, `PYTHONDONTWRITEBYTECODE=1`.
5. `check_environment` (pins; its probe child inherits the filter and needs no network),
   `check_harness` (clean `6adf3859…`, cache presence), `check_resources`.
6. **Prove (i)–(iv):** `e1_openml_offline.prepare()` — audit pin, harness HEAD, `cache_check`
   hash/mtime/pre-launch, data ids, per-node cache snapshot + ARFF md5, fingerprint recomputation
   (under the already-enforced denial). Failure is a STOP before the output directory exists.
7. Write `replay_plan.json` (declared before the first execution) containing the full identity
   report, the network report, and `state = VERIFIED`.
8. Per case (order, seeds and environment unchanged): `execute_case` copies the node directory,
   re-verifies the copy (`before`), edits only the editable config, runs the pinned `LocalWorker`
   (whose node command inherits the filter), re-verifies the copy (`after`) and the recorded
   `data_cache_unchanged`; any mismatch is a STOP that keeps everything.
9. After the last case: re-verify every source cache and re-prove network denial; then the
   pre-existing harness-cache comparison. Then `summary.json` (PASS) or `STOP.json`.

Every STOP retains the plan and partial artifacts, writes no retry, and never substitutes a
later trial or a weaker check.

### 3.3 Outputs of a successful run

- `replay_plan.json` — unchanged protocol fields plus `environment.openml_offline_mechanism`
  (six nodes × data id, four cache file SHA-256, tree digest, ARFF md5/file id, loaded-data
  fingerprint, audit/sweep-1 pins) and `environment.openml_offline_mechanism.network` (filter,
  errno, probe reports).
- `cases.jsonl` — each row now also carries `openml_offline_cache_checks` (the before/after
  audited copy digests) and the unchanged token fields.
- `summary.json` — `openml_offline_mechanism.post_run` (source-cache digests, post-run network
  proof), `report_sha256`, `network_enforced`.
- On any failure: `STOP.json` with the reason; nothing is deleted.

## 4. How to run all 16 cases after independent review

**Only after an independent reviewer has accepted this branch.** That review is the gate; this
document does not authorize execution.

1. Reviewer records the reviewed commit and the driver file SHA-256
   (`sha256sum r1/scripts/c3_env_replay.py`). The e1 authorization's driver pin
   (`5ef9db16…`) predates this amendment; the run record and the review packet must carry the
   amended driver hash and cite **R1-E1-OPENML-AMEND** (see §6, open item 1).
2. Operator checks out the reviewed commit, clean tree, one operator on deepthought, and the
   preserved batch path exactly as in the authorization. Check co-tenancy and disk headroom.
3. Dry run first, new output directory (no flag needed; passing it only records
   `DEFERRED_TO_HOST`):

   ```
   . <batch>/env.sh
   export AR_HARNESS_ROOT=<batch>/autoresearch_harness
   export PYTHONDONTWRITEBYTECODE=1
   python -B -m r1.scripts.c3_env_replay --paper-root <reviewed checkout> \
     --harness "$AR_HARNESS_ROOT" --batch <batch> \
     --scratch /tmp/r1_c3_env_replay_<stamp> --out <new dry-run dir> --min-free-bytes <estimate> \
     --dry-run
   ```

4. Real run, a **different new** output directory, with the reviewed flag (or the environment
   variable):

   ```
   python -B -m r1.scripts.c3_env_replay --paper-root <reviewed checkout> \
     --harness "$AR_HARNESS_ROOT" --batch <batch> \
     --scratch /tmp/r1_c3_env_replay_<stamp2> --out <new run dir> --min-free-bytes <estimate> \
     --openml-offline-mechanism r1-e1-openml-amend-20261117
   ```

5. The **pass rule is unchanged and was declared before execution**: PASS requires all 16 cases
   to reproduce their recorded primary metric token with **zero tolerance** (emitted token
   equal, never re-rounded) and every environment check `PASS`. Anything else is a STOP. The
   OpenML identity proof is a precondition, never a substitute for a numeric match.
6. Report each case (`cases.jsonl`, raw logs, `replay_plan.json`, `summary.json`/`STOP.json`) on
   the `ops-*` branch for independent review. The report and the paper must disclose, in
   substance, the fixed sentence the amendment requires: **identity rests on the amended
   evidence — sweep-1 data id, sweep-1 loaded-data fingerprint, OpenML md5 self-consistency and
   unchanged audited bytes — not on a file hash recorded by sweep 1**; and that the batch
   `.venv` executables were wrappers to the shared venv. A pass remains a bounded reproducibility
   check of these 16 worker evaluations, not proof that every dependency or all 288 roots were
   identical. No B.2 follows from e1 alone (R1-B2-REPLAY-GO / e2).

## 5. Residual risks (must be disclosed, not hidden)

1. **The core residual risk, by construction of the amendment:** the surviving cache bytes are
   **not** anchored by a hash the sweep-1 launch wrote. (iv) anchors them to the audit, which was
   produced read-only on 16 Nov 2026, after the sweep; (i)+(ii) anchor them to the sweep's data
   id and loaded-data fingerprint. A writer who could modify the preserved caches **and** the
   retained `cache_check.json` consistently, before the audit and without detection, is outside
   what this evidence can exclude. The audit was accepted as faithful and the caches are on
   preserved Ceph storage; the operator must not write them and this mechanism never does.
2. **mtime is a filesystem attribute, not a cryptographic binding.** The `cache_check.json`
   mtime check proves the encountered attribute, not an unforgeable timestamp.
3. **The loaded-data fingerprint is a shape/class/label summary**, not a byte hash (for example
   it does not distinguish feature-value permutations that preserve rows/classes). It is compared
   exactly, together with OpenML's ARFF md5 and the audited per-file SHA-256, but it is weaker
   than a file digest by itself.
4. **OpenML md5 self-consistency is OpenML's own archive checksum**, not a sweep-1 record; it
   shows the cache ARFF is the archive file the metadata describes, not that sweep 1 loaded these
   bytes.
5. **Network enforcement is network-only.** The seccomp filter constrains the replay driver and
   its descendants; a separate same-uid process already running on the host is outside it (one
   operator, read-only batch discipline). It is Linux x86-64 only and deliberately denies all
   sockets, including AF_UNIX/loopback, so an unexpected local socket in a case is a STOP rather
   than a silent pass. It is installed at the very start of the real run, before `numpy`
   import, so the single-thread precondition is met by construction; the later environment
   checks run under the filter (they need no network). It is not a full mount/PID/user-namespace
   sandbox; the M3 supervisor components remain unwired and are not needed for (b).
6. **The fingerprint recomputation uses the paper repository's `check_caches.check_node` and the
   pinned harness loader.** It is exact for the compared fields, but `NODE_INFO` "problems" are
   not compared (they are repository metadata checks, not the sweep-1 fingerprint).
7. **The e1 authorization's driver pin text predates the amendment** (see §6, open item 1).
8. **The 4 non-OpenML cases run under the same enforced no-network filter.** That is the point of
   (b); if one of them unexpectedly needed a download it would STOP instead of silently using the
   network.

## 6. What is still open / required from others

1. **Independent review of this branch is still required** — this note is the builder's
   deliverable, not an acceptance. The reviewer must also decide how to record the amended
   driver SHA-256 against the e1 authorization pin (the authorization says the operator records
   the driver file hash; do that explicitly, cite R1-E1-OPENML-AMEND, and do not present the
   amended driver as the 16 Nov hash).
2. **No e1 run and no e1 dry run has been performed here.** The real fingerprint recomputation,
   the real `cache_check.json` binding, the real cache-tree snapshot and the real kernel seccomp
   enforcement are exercised for the first time on deepthought at run time (and in the Linux-only
   integration test during review). Local tests use fixtures, so they cannot prove the host's
   seccomp availability; if the host cannot install the filter, the mechanism STOPs as designed.
3. **No B.2, no labels, no audit outputs, no deletions.** Nothing outside this branch was changed.

## 7. What the independent reviewer must check

1. **Authority/base.** Branch from `origin/main` = `16185b0b`; row R1-E1-OPENML-AMEND present;
   `5ef9db16` an ancestor; the audit/review files byte-identical to `5d73550a` (compare
   `git show 5d73550a:…` hashes; `SHA256SUMS.txt` must verify).
2. **Diff scope.** Only `r1/scripts/c3_env_replay.py` modified; new
   `r1/c3/e1_openml_offline.py`, `r1/c3/e1_offline_network.py`, three test modules and this
   report/audit artifacts; no PLAN/authorization edit; no numeric, case-selection, seed,
   environment or pass-rule change; the default OpenML STOP message unchanged.
3. **Clause (i) code path.** `verify_dataset_ids` reads pinned NodeSpecs from the commit (not the
   worktree), compares five sources, and stops on a missing or mismatched id.
4. **Clause (ii) code path.** `bind_cache_check` pins SHA-256/mtime/pre-launch; `verify_fingerprints`
   compares the exact ten fields and versions; the loader is the sweep's own `check_node`; the
   load is preceded by the enforced denial. Confirm the audited `cache_check.json` was produced
   pre-launch by the runbook's `r1.noise.check_caches`.
5. **Clauses (iii)/(iv).** `verify_arff_md5` and `snapshot_cache`/`verify_source_caches`/
   `verify_case_cache`; confirm the tree digest is the driver's algorithm (there is a regression
   test for that), that dotfiles are tree-digest-covered, and that before/after checks surround
   the worker.
6. **Clause (b).** Filter covers socket creation and use, arch/x32 guards, NO_NEW_PRIVS,
   inheritance proof in a fresh child, `Seccomp: 2`, re-verification after the last case; any
   failure is a STOP before output creation. Run the Linux-only integration test on a Linux
   x86-64 host if desired; note the test kills its own child with the filter, never the session.
7. **Tests.** Run `python -m pytest -q r1/tests/test_c3_env_replay.py
   r1/tests/test_e1_openml_offline_mechanism.py r1/tests/test_e1_offline_network.py
   r1/tests/test_e1_openml_offline_wiring.py` against the harness checkout; all new tests must
   pass and the pre-existing driver tests must be unchanged apart from environment-only skips.
8. **No execution/side effects.** Confirm no e1/dry run, no job, no deepthought/ceph write, no
   label/B.2, and that `ops-e1-replay-20261116` and `main` are untouched.

## 8. Files delivered

- `r1/c3/e1_openml_offline.py` — (i)–(iv) identity mechanism and audit pin.
- `r1/c3/e1_offline_network.py` — (b) enforced network denial.
- `r1/scripts/c3_env_replay.py` — opt-in wiring (`--openml-offline-mechanism` /
  `R1_E1_OPENML_OFFLINE_MECHANISM`), default STOP unchanged.
- `r1/tests/test_e1_openml_offline_mechanism.py`, `r1/tests/test_e1_offline_network.py`,
  `r1/tests/test_e1_openml_offline_wiring.py` — good path, every tamper/missing-input STOP,
  before/after SHA checks, network enforced/failure STOP, flag absent/wrong-token STOP.
- `docs/r1/reports/e1_replay_20261116/` — the accepted audit report, audit JSON and
  `SHA256SUMS.txt` carried byte-identical from `5d73550a`, plus this report;
  `docs/r1/reviews/E1_OPENML_REVIEW_20261116.md` — the accepted independent review of the audit
  (carried byte-identical from `5d73550a`); `docs/r1/reviews/E1_REPLAY_REVIEW_20261116.md` — the
  accepted independent review of the e1 STOP (carried byte-identical from `fc7d8e4e`).

## 9. Builder test evidence (fixtures only; no e1)

Run on the construction host (macOS, Python 3.15 test venv; the local harness checkout is at
an unpinned local commit, so pre-existing harness/env tests fail identically here):

```
python -m pytest -q r1/tests/test_e1_openml_offline_mechanism.py \
    r1/tests/test_e1_offline_network.py r1/tests/test_e1_openml_offline_wiring.py
-> 62 passed, 1 skipped   (the skip is the Linux-only real-seccomp integration test)
```

The 62 fixture tests cover: the accepted full (i)–(iv) identity; each data-id, fingerprint,
ARFF-md5, cache-file/tree, cache-path/cache-harness and audit/cache_check pin/mtime tamper or
removal as a STOP; before/after-source and before/after-case-copy SHA checks; the compiled
seccomp program's actual decision for every blocked syscall plus arch/x32 guards through a
small BPF interpreter (so the filter logic is tested on any host); every install/probe failure
as a STOP; the flag absent / wrong-token / environment-token wiring; the mechanism-enabled
OpenML run path, the post-run STOP, and the unchanged default STOP. The Linux-only
`test_linux_install_denies_sockets` installs the real filter in a disposable child process and
must be run on deepthought (or any Linux x86-64 host) during review.

Full-suite cross-check against `origin/main` @ `16185b0b` in the same environment (same Python,
same local harness, both worktrees): final branch run `130 failed, 2317 passed, 160 skipped` vs
baseline `130 failed, 2255 passed, 159 skipped` — the +62 passes are the new fixture tests, the
+1 skip is the Linux-only real-seccomp test, and the failure lists are byte-identical (`diff`
empty: no branch-only and no baseline-only failure). The one early-run artifact was LLM client
modules imported by other suites into `sys.modules`; the wiring tests now use the same autouse
isolation fixture as the pre-existing driver tests. `r1/tests/test_c3_env_replay.py` alone:
32 passed, 1 failure that is the pre-existing "pinned harness commit not present on this Mac"
limitation, not a change in this branch.
