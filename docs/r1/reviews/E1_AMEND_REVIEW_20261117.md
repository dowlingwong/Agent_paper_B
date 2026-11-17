# Independent review — R1-E1-OPENML-AMEND offline mechanism, e1 (17 November 2026)

Reviewer: `reviewer-e1-amend`, independent and read-only (did not write the reviewed unit). This
file is the only write; no execution of e1, no e1 dry run, no driver run, no job, no server, no
B.2, no label, no deepthought/ceph write, no git write. Review date 2026-11-17 (Europe/Berlin).
Repository checks were read-only `git` commands and read-only `git show` of the pinned harness
commit; the three required test modules were run read-only on this review host. No network/SSH
access to deepthought or ceph was used, so the preserved batch/caches themselves were not
re-inspected here (limitation stated where it matters).

## Reviewed unit and authorities

- Branch `r1-e1-openml-amend-20261117` @ **`b58bbb31c734dd59a9ba01399236c0d75cabfc44`**
  (message `feat(r1): R1-E1-OPENML-AMEND offline identity mechanism for e1 (reviewed code; no
  run)`), worktree `.claude-worktrees/e1-openml-amend-20261117`, clean at review start
  (`git status --porcelain` empty).
- Parent **`16185b0b4035a58814bce360780182f0e3c34442`** = the stated base `origin/main`.
  `origin/main` has since advanced twice (`14c47777`, `26177d82`), but the branch base is unchanged
  and the authority row text is unchanged (see below).
- Authority (`git show 16185b0b:docs/r1/PLAN.md`, §10):
  - row **R1-E1-AUTH** (line 1211): e1 environment replay authorized, `--dry-run` first, the
    driver's offline STOP must not be bypassed;
  - row **R1-E1-OPENML** (line 1223): independent offline mechanism may lift the OpenML STOP only
    if (a) the six datasets are shown identical to sweep 1 and (b) workers have no network;
  - row **R1-E1-OPENML-AMEND** (line 1241): revises (a) to the composite evidence standard
    **(i) OpenML data id equals the sweep-1 record; (ii) the sweep-1 loaded-data fingerprint,
    recomputed on the same cache, equals value by value; (iii) cache ARFF md5 equals the cache
    metadata's OpenML `md5_checksum`; (iv) per-file SHA-256 and tree digest unchanged before/after
    use and equal to `OFFLINE_MECHANISM_AUDIT.json`; (b) worker no-network unchanged.** The same
    row text (`shasum` of the row line) is identical at `16185b0b` and current `origin/main`
    `26177d82`.
- Basis: identity audit branch `e1-openml-20261116` @ `5d73550a` (audit + accepted review
  `E1_OPENML_REVIEW_20261116.md`, verdict ACCEPTED); e1 STOP report commit `fd833c9e` on
  `ops-e1-replay-20261116` with accepted review `E1_REPLAY_REVIEW_20261116.md` @ `fc7d8e4e`
  (verdict ACCEPTED); authorization `docs/r1/authorizations/c3_env_replay_20261116.md` (present
  and unmodified in the parent); predeclared protocol
  `C3_ENV_RECONSTRUCTION_REPLAY_DRAFT_20261028.md`.
- **Driver pins.** The authorization's paper/driver pin is `5ef9db16…`; the driver blob there is
  SHA-256 `a9cad4d544bdf061c42ecb4b4c2d3d10d8bc94342574d9a37489bd4b179aa7d8` (the audit records the
  same). That pin **predates the amendment** and cannot authorize the amended driver.
  **Amended/candidate driver pin (this commit): `r1/scripts/c3_env_replay.py` SHA-256
  `1b1e2fb229e78a82b56f1b8c9e45d6bc36412facf26d89f05bf6acb830a7e7e0` (git blob `db55a2cc`),
  cited under row R1-E1-OPENML-AMEND.** Because of Blocker 1 below, this candidate pin is
  recorded here but is **not cleared for the e1 real run**; after the fix, the re-review and the
  operator must record the new hash and the run record must present it as the amended hash (not as
  the 16 Nov `5ef9db16` hash).
- Accepted artifacts carried in this branch are **byte-identical** to their accepted commits:
  `OFFLINE_MECHANISM_20261116.md` `61a3d02b…ce2369`, `OFFLINE_MECHANISM_AUDIT.json`
  **`9f14c879973ff4080655a2e108e6e7a1aad2b031d96d4f96e914921ddaa190b7`**,
  `SHA256SUMS.txt` `f12503ff…d3aef`, `E1_OPENML_REVIEW_20261116.md` `80301e23…4873c` (all
  identical at `5d73550a`); `E1_REPLAY_REVIEW_20261116.md` `26893bbb…f61326` (identical at
  `fc7d8e4e`). `SHA256SUMS.txt` verifies both entries from the worktree blobs.

## 1. Base, diff scope, and no side effects

- `git diff --stat 16185b0b..HEAD`: 12 files, +3,483 / −14. Name-status: **only**
  `r1/scripts/c3_env_replay.py` modified; added
  `r1/c3/e1_openml_offline.py`, `r1/c3/e1_offline_network.py`, the three new test modules, this
  amendment's report, and the five carried accepted artifacts. No PLAN, no authorization, no
  numeric/case/seed/environment/pass-rule file, no pre-existing test file, no `results/` change.
  `git diff --check 16185b0b..HEAD` clean. The authorization file is present in the parent and
  identical in HEAD (no authorization edit).
- Driver diff is wiring only: new module imports, token/env handling, (b) install, mechanism
  prepare, plan/summary fields, per-case before/after hooks and post-run checks. `TOLERANCE = 0`,
  `MEMORY_MODE`, `BUDGET_INDICES`, `SELECTION_RULE`, seeds, `COLLECTOR_*`/`NO_GPU`, host/batch/
  harness/version pins and `case_passes` are untouched (byte-identical lines).
- Default behaviour without the flag is the original OpenML hard STOP; the whole-set string and
  the per-case string are byte-identical to `5ef9db16` (see §6).
- Worktree has no e1/dry-run artifact: no `C3_env_replay_*` directory under `results/r1/`, no
  `replay_plan.json` / `cases.jsonl` / `summary.json` / `STOP.json` from this branch, no untracked
  files except this review. Local refs checked: `e1-openml-20261116` = `5d73550a`,
  `e1-review-20261116` = `fc7d8e4e`, `ops-e1-replay-20261116` = `fd833c9e`; nothing moved by this
  review. (Remote refs were not queried; no network was used.)
- The construction commit itself is docs+code only and everything else in the worktree is
  unchanged; nothing here shows a run, a job, a ceph write or a label/B.2 starting.

## 2. Clause (i) — OpenML data id

Code path (`r1/c3/e1_openml_offline.py:127–193`): `_git_show` runs
`git -C <harness> show 6adf3859…:<rel>` (the pinned **commit**, explicitly not the worktree) for
`configs/nodes/<node>.yaml` and `nodes/<node>/dataset.json`; the five sources (harness config,
harness `dataset.json`, sweep-1 `cache_check.json` row, audit's cache_check copy, audit's
`pinned_harness.node_specs`) must all equal 15/59/1510/29/40/1467; `dataset.json.node_name` and the
config `dataset_name`/`target` are cross-checked. Missing id, missing file, non-JSON spec or any
mismatch raises `MechanismStop`. (The `*.yaml` files are JSON-formatted in this harness —
`r1.noise.check_caches.check_node` also does `json.loads` on them — so the parse is correct, not a
bug.)

I re-read the pinned commit independently with `git show 6adf3859:` from a local harness clone that
contains the pinned object (`/private/tmp/h_harness`; not the paper worktree):

| node | `nodes/<n>/dataset.json` (node_name, dataset_id, dataset_name, target) | `configs/nodes/<n>.yaml` dataset_id |
|---|---|---|
| openml_breast_w | openml_breast_w, 15, breast-w, Class | 15 |
| openml_ionosphere | openml_ionosphere, 59, ionosphere, class | 59 |
| openml_wdbc | openml_wdbc, 1510, wdbc, Class | 1510 |
| openml_credit_approval | openml_credit_approval, 29, credit-approval, class | 29 |
| openml_sonar | openml_sonar, 40, sonar, Class | 40 |
| openml_climate | openml_climate, 1467, climate-model-simulation-crashes, Class | 1467 |

These equal the audit's `pinned_harness.node_specs`, the audit's cache_check ids and
`OPENML_IDS`. The pin `6adf3859de66c4814fcf376eed59880fbd8eeaf7` ("Apply predeclared D28 start
configurations") differs from its base `897d83c8` only in four `nodes/*/config.yaml` files, so the
identity files read at the pin are the same identities as at the base. Clause (i) is faithful.
Caveat: the live sweep-1 `cache_check.json` (sha-pinned `35e76f37…`) is on the preserved batch and
was not available here; its transcribed id values are in the accepted audit and are re-checked
against the live file at run time.

## 3. Clause (ii) — loaded-data fingerprint — **BLOCKER 1**

What is implemented, and passes inspection:

- `bind_cache_check` (`…:348–383`) requires the live `cache_check.json` to be a regular file under
  the recorded batch, SHA-256 **`35e76f37fcc4925a7896f6cf0bc2ab2bbf8647adfc763729da5a8e93325944f9`**
  (and equal to the audit record), mtime `2026-10-27T15:22:39Z` equal to the audit, and strictly
  before the recorded launch `15:48:34Z`.
- The fingerprint loader is the sweep's own `r1.noise.check_caches.check_node`
  (`…:337–345`); `r1/noise/check_caches.py` and `r1/noise/e1_noise_floor.py` are **byte-identical
  to the sweep's paper pin `ccb47128aad8`** (`git diff ccb47128aad8 HEAD --` empty), so the
  recomputation uses the same loader/`_prepare_node` the sweep used. The loader runs with the
  process network disabled and, in the driver, under the already-installed (b) filter.
- The compared field set (`FINGERPRINT_FIELDS`, `…:66–68`) is exactly ten fields and matches the
  live record schema (`per_node_fields` in the audit: node, dataset_id, cache_source, cache_path,
  rows, features, categorical_columns, missing_values, target_name, class_counts, positive_label,
  minority_share, problems, status). `cache_source`, `cache_path`, recorded `harness` and the four
  recorded library versions are also compared; any missing field, loader exception, version
  difference or value difference is a `MechanismStop`.
- The audit's transcribed `cache_check` node rows are a trimmed subset (dataset_id, cache_source,
  rows, features, class_counts, missing_values), but the runtime comparison uses the hash-pinned
  live file (which `per_node_fields` documents as full), so this is not a code defect.

**Blocker 1 — the real run can never reach `state = VERIFIED`: the pinned audit's `launch_utc` is
an annotated string and `_parse_utc` rejects it.** The audit (byte-identical, sha `9f14c879…`)
stores:

```
"launch_utc": "2026-10-27T15:48:34Z (from the frozen manifests' started_utc)"
```

`bind_cache_check` line 375 parses that field with `_parse_utc` (`…:117–124`), which does
`datetime.fromisoformat(str(text).replace('Z','+00:00'))`. Reproduced on the committed code:

```
>>> M._parse_utc("2026-10-27T15:48:34Z (from the frozen manifests' started_utc)")
MechanismStop: STOP: invalid recorded UTC timestamp "2026-10-27T15:48:34Z
               (from the frozen manifests' started_utc)"
```

I also drove the real `bind_cache_check` with every other check satisfied (synthetic batch record,
record sha/CACHE_CHECK_SHA256 and mtime all matching, real audit dict): it STOPs there, before any
cache byte or fingerprint is checked. Consequence on deepthought: `prepare()` raises
`MechanismStop`, the driver re-raises `Stop('STOP: OpenML offline mechanism: STOP: invalid recorded
UTC timestamp …')`, and the real run aborts before the output directory exists. This is **safe**
(fail-closed; no case scheduled, nothing written) but the mechanism is **not ready for the e1 real
run** — it cannot pass (ii), so it can never write `state = VERIFIED` or lift the STOP. The dry run
is unaffected (the proof is deferred to the host).

Why the fixtures missed it: the fixture audit writes a clean
`LAUNCH.strftime('%Y-%m-%dT%H:%M:%SZ')`, and the committed-audit test
(`test_e1_openml_offline_mechanism.py:503–518`) checks the audit sha/ids/md5s but never exercises
`bind_cache_check`/`_parse_utc` on the **real** record. A one-line regression test on the committed
audit's `launch_utc` would have caught this. The audit must stay byte-identical to `5d73550a`, so
the fix belongs in code: accept the ISO-8601 prefix (e.g. parse the leading token) or compare a
normalised prefix against a new `SWEEP1_LAUNCH_UTC = 2026-10-27T15:48:34Z` constant, and add the
regression test. Re-review is required afterwards.

## 4. Clauses (iii) and (iv)

- **(iii)** `_arff_consistency`/`verify_arff_md5` (`…:214–252`): gzip-decompress
  `api/v1/json/data/<id>.gz`, require `data_set_description.md5_checksum` (32 chars), metadata `id`
  equal to the node id, `file_id` consistent with the ARFF path, and md5 of the decompressed ARFF
  equal to `md5_checksum`; then cross-check the audit's `openml_self_description` (`file_id` and
  `openml_md5_checksum`). The audit records equal OpenML and uncompressed-ARFF md5s for all six
  nodes (table in the amended report §2.3 matches the audit), and the audited cache paths are
  exactly the four expected files per node.
- **(iv)** `_walk_cache`/`snapshot_cache` (`…:257–323`) walk the whole `nodes/<node>/data_cache`
  tree with `followlinks=False`, `lstat` every directory and file, and reject symlinks or
  irregular entries; the non-dotfile file set must equal the audit's four files and every SHA-256
  must equal the audit value; only root `.gitignore`/`.gitkeep` are tolerated outside the four
  files; the recomputed tree digest must equal the audit's `tree_digest_driver_algorithm`. The
  `tree_digest` (`…:88–96`) is byte-for-byte the driver's algorithm
  (`r1/scripts/c3_env_replay.py:455–461`), so the audit's "driver algorithm" digests are the right
  target; dotfiles are covered because the digest walks all files. `verify_case_cache` re-checks
  the per-case copy before and after the worker (file set, SHAs, tree digest, ARFF md5) and
  `verify_source_caches` re-checks every source cache after the last case. `prepare` is called
  before `out.mkdir`, so a (i)–(iv) failure is a STOP before output creation.
- I could not recompute the six cache trees/per-file hashes here (no access to the preserved
  batch/caches); the amended report's §2.3 read-only SSH re-verification records all 24 file
  hashes and six tree digests matching the audit, and the accepted audit is byte-identical. The
  run-time mechanism re-verifies the real bytes and STOPs on any difference, so this limitation
  does not weaken the gate.

## 5. Clause (b) — enforced worker network denial

`r1/c3/e1_offline_network.py` installs a classic-BPF seccomp filter on Linux x86-64:
`AUDIT_ARCH_X86_64` guard (other architectures `KILL_PROCESS`), x32 guard (`nr >= 0x40000000`
killed), 19 syscall numbers blocked with `SECCOMP_RET_ERRNO | 101` (`socket`, `connect`, `accept`,
`sendto`, `recvfrom`, `sendmsg`, `recvmsg`, `shutdown`, `bind`, `listen`, `getsockname`,
`getpeername`, `socketpair`, `setsockopt`, `getsockopt`, `accept4`, `recvmmsg`, `sendmmsg`,
`io_uring_setup/enter/register`), default `ALLOW`; then `PR_SET_NO_NEW_PRIVS` and
`SECCOMP_SET_MODE_FILTER` with flags 0. I checked the BPF jump semantics instruction by
instruction and by the tests' BPF interpreter — the guards and per-syscall ERRNO returns are
correct; the filter is additive and cannot be removed (`NO_NEW_PRIVS` also prevents re-privileging),
and seccomp filters are inherited by fork and clone-thread, so the required single-thread
precondition (`/proc/self/task` length == 1, otherwise STOP) covers every later thread and child.

Installation runs at the very start of a real run with the token, before corpus/case selection and
before the fingerprint load; I confirmed empirically that importing the driver loads **no**
`numpy`/`scikit-learn`/`socket`/`ssl`/`http`/`autoresearch` modules, so the filter precedes the first
library import that could create a thread. The `LocalWorker` node command is a subprocess and
inherits the filter. `enforce()` requires an in-process probe (socket(), socket(AF_INET6),
`create_connection`) to fail with errno 101 and `/proc/self/status` `Seccomp: 2`, and the same in a
fresh worker-representative child; `reverify()` re-proves the child denial after the last case.
Non-Linux x86-64, install errors, any unproven probe, missing report or wrong mode are
`NetworkDenialStop` → driver `Stop` before output creation; the connect probe uses TEST-NET-1
(no real traffic). This is genuinely fail-closed for the stated threat model (node code attempting
a download): there is no socket syscall path, no io_uring path, and no way to remove the filter.

Residual (documented in the report §5.5; not a defect): it is network-only, not a mount/PID/user
sandbox, and a separate same-uid process is outside it. A subtlety not spelled out: syscalls that
write to a pre-existing socket fd (`write`/`sendfile`) and fd duplication (`pidfd_getfd`) are not
blocked; since the driver holds no network socket and `subprocess` closes fds, this needs a
same-uid process already holding a socket to matter (out of scope). The Linux-only kernel test
must still be run on deepthought (§7).

## 6. Wiring, default STOP, frozen protocol

- Opt-in only: `--openml-offline-mechanism r1-e1-openml-amend-20261117` or
  `R1_E1_OPENML_OFFLINE_MECHANISM`; any other non-empty value is a STOP before anything runs;
  absent/empty keeps the original OpenML STOP. The whole-set STOP string is byte-identical to
  `5ef9db16` (`… not verified; no replay scheduled`), and the per-case `execute_case` STOP string
  is unchanged; a mechanism-less `execute_case` on an OpenML case still refuses independently.
- Real-run order: token validation → `enforce()` (b) → corpus/case selection → host/batch/
  `AR_HARNESS_ROOT`/`PYTHONDONTWRITEBYTECODE` checks → `check_environment`/`check_harness`/
  `check_resources` → mechanism `prepare()` (i)–(iv) → `out.mkdir()` → plan with
  `openml_offline_mechanism.state = VERIFIED` written before the first case → per-case before/after
  cache verification and the unchanged worker → post-run source-cache re-verify + network re-prove
  → `summary.json`/`STOP.json`. Failures before `out.mkdir` leave no output directory. Case
  selection, seeds, recovered files, thread/GPU environment, zero-tolerance pass rule and
  emitted-token comparison are untouched; no label/B.2 output is produced.
- Minor: the whole-set STOP now fires before the host check (same message, still a STOP); a
  `MechanismStop` raised inside `execute_case` is reported as `STOP: interrupted:
  MechanismStop: …` in `summary.json` (still a STOP, artifacts retained) — cosmetic.

## 7. Tests (run on this review host)

Environment: `/private/tmp/pb_test_venv/bin/python` (Python 3.15.0, pytest 9.2.0), worktree at
`b58bbb31`, `PYTHONDONTWRITEBYTECODE=1`, `-B`.

```
pytest r1/tests/test_e1_openml_offline_mechanism.py r1/tests/test_e1_offline_network.py \
       r1/tests/test_e1_openml_offline_wiring.py -q
-> 62 passed, 1 skipped in 6.93 s
```

The skip is
`r1/tests/test_e1_offline_network.py::test_linux_install_denies_sockets` ("needs Linux x86-64
seccomp"), as expected on macOS. **On Linux x86-64 (deepthought) this test must be run before the
e1 real run**: it installs the real filter in a disposable child, then requires
`Seccomp: 2` and errno 101 for `socket(AF_INET)`, `socket(AF_INET6)` and `create_connection` both
in-process and in a child; it kills only its own child. The 62 fixture tests cover the good-path
identity, all tamper/missing STOPs, the filter's decisions for every blocked syscall,
the probe/install STOPs, the flag/env wiring, the default STOP and the post-run STOP; **but they do
not bind the real committed audit (Major 1)**.

The pre-existing `r1/tests/test_c3_env_replay.py` is unchanged by this branch and ran
`31 passed, 2 skipped` here (environment-only skips; this review host's harness checkout is not the
pinned `6adf3859`). I did not reproduce the builder's full-suite parity run (the pinned harness /
scikit-learn / autoresearch environment is not installed on this host); that claim is not
independently confirmed here, but the branch changes no pre-existing test or numeric file, and the
three required suites plus the untouched driver suite are consistent with the report.

## 8. Findings

**Blocker 1 (must fix before e1 real run).** The real run always STOPs at `bind_cache_check`:
the pinned audit's `sweep1_batch_records.launch_utc` is
`"2026-10-27T15:48:34Z (from the frozen manifests' started_utc)"`, and `_parse_utc`
(`r1/c3/e1_openml_offline.py:375`) rejects the annotation. Fail-closed and safe (no case is
scheduled, no output is created), but the mechanism can never reach `state = VERIFIED`, so it is
**not ready for the e1 real run**. Fix in code (the audit must remain byte-identical): accept the
ISO-8601 prefix or compare the leading token against a new `SWEEP1_LAUNCH_UTC = 2026-10-27T15:48:34Z`
constant, keep the pre-launch ordering check, add the real-audit regression test, then re-review.

**Major 1 (test gap; root cause of Blocker 1).** `test_the_committed_audit_is_the_reviewed_one`
checks the audit sha, ids, md5s and the mtime constant but never calls `bind_cache_check` /
`_parse_utc` with the **real** committed audit (the fixtures use a clean `launch_utc`). Extend it to
parse the real `launch_utc` and, ideally, to exercise `bind_cache_check` against the committed
audit's record fields (batch-mountable synthetic copy) so the mechanism's own audit-field
assumptions are covered.

**Minors**

1. `bind_cache_check` truncates the live mtime to whole seconds before comparing
   `15:22:39Z`, so an mtime anywhere in `[15:22:39, 15:22:40)` passes (the real
   `15:22:39.992` does). Fine in practice; say "truncated to the recorded second" in the report or
   compare with an explicit tolerance.
2. `MechanismStop` inside `execute_case` surfaces as `STOP: interrupted: MechanismStop: …` (still
   a STOP; wording only).
3. The amended report's residual-risk list could add the inherited/pre-existing-fd nuance of (b)
   (pre-existing socket fd write/sendfile, `pidfd_getfd`) so the network claim is scoped exactly.
4. The audit's transcribed `cache_check` rows are a trimmed subset of the live record
   (`per_node_fields`); the run-time code correctly reads the hash-pinned live file, but the
   amended report should say so in one sentence to avoid a reader mistaking the audit copy for the
   full record.
5. The report's "no execution/side effects" claim is consistent with everything visible here; the
   review host cannot see deepthought/ceph, and no remote checks were made.

No evidence of any e1 run, dry run, job, deepthought/ceph write, label or B.2; no numeric, PLAN or
authorization edit; the accepted audit/reviews are byte-identical.

## 9. What the e1 operator must check at first real use (after Blocker 1 is fixed and re-reviewed)

1. Deploy exactly the re-reviewed commit; record the commit and `sha256sum r1/scripts/c3_env_replay.py`.
   The amended pin candidate for `b58bbb31` is
   `1b1e2fb229e78a82b56f1b8c9e45d6bc36412facf26d89f05bf6acb830a7e7e0`; the fixed commit will carry a
   new hash. Record the new hash in the run report/review packet, present it as the amended driver
   hash and cite **R1-E1-OPENML-AMEND** — it must not be presented as the authorization's 16 Nov
   `5ef9db16` hash.
2. Dry run first into a new directory (no flag needed; with the token only `DEFERRED_TO_HOST`), then
   the real run into a **different** new directory with
   `--openml-offline-mechanism r1-e1-openml-amend-20261117`.
3. Host: deepthought, Linux x86-64, one operator, single-threaded start; the (b) install and both
   probes must show `Seccomp: 2` and errno 101 (in-process and child). Run the Linux-only
   `test_linux_install_denies_sockets` first. Any non-Linux/install/probe failure is a STOP.
4. Batch/venv pins: wrappers → `/ceph/dwong/r1_prepare_20261025/venv/bin/python`, Python 3.13.15,
   scikit-learn 1.8.0/NumPy 2.4.4/pandas 3.0.3/SciPy 1.17.1, `uv.lock`, 25 Oct freeze + narwhals,
   dist-info mtime before launch, driver in the batch venv, `AR_HARNESS_ROOT` = batch harness,
   `PYTHONDONTWRITEBYTECODE=1`.
5. Harness clean at `6adf3859…`; `cache_check.json` SHA-256 `35e76f37…` and mtime `15:22:39Z`
   before the `15:48:34Z` launch; the (i) ids via `git show` for all six nodes; (iii) ARFF md5 vs
   metadata (id/file_id consistent); (iv) the four audited files and tree digests per node, only
   root `.gitignore`/`.gitkeep` outside them; (ii) the ten-field fingerprint recomputed under the
   filter, versions and harness/cache path equal.
6. Confirm `replay_plan.json` records `openml_offline_mechanism.state = VERIFIED` **before** the
   first case and the output directory exists only after (i)–(iv) pass; expect per-case
   before/after `openml_offline_cache_checks` and the post-run source-cache + network re-proof in
   `summary.json`. Anything else is a STOP: retain everything, do not retry.
7. PASS remains the unchanged zero-tolerance rule: all 16 cases' emitted metric tokens equal the
   recorded tokens (no re-rounding) and every environment check `PASS`. Identity proof is a
   precondition, never a substitute. Disclose that identity rests on the amended evidence, not on a
   sweep-1 file hash, and that the batch `.venv` executables were wrappers to the shared venv.

## Verdict

The amended mechanism is substantively the right implementation of the author's amended standard:
(i) is verified against the pinned harness commit; (ii) uses the sweep's own unchanged loader and
exact ten-field comparison with hash/mtime/pre-launch binding; (iii)/(iv) rigorously bind the cache
bytes to OpenML's own metadata md5 and to the accepted audit, with whole-tree symlink/regex checks
and before/after verification; (b) is a genuine irreversible fail-closed seccomp denial proven
in-process and in a child and re-proven post-run; the wiring keeps the original STOP, writes the
plan only after verification, and changes no selection, seed, environment or pass rule. However,
**Blocker 1** means the real e1 run would STOP — safely, but unavoidably — at the first identity
binding, because the pinned audit's annotated `launch_utc` is rejected by `_parse_utc`; the test
suite never exercises the real audit, so the defect escaped. The fix is narrow (code-side parse of
the audit's timestamp prefix plus a real-audit regression test) but it changes a reviewed run
input path and therefore needs a new commit, the recorded new driver hash, and a fresh independent
review before the e1 dry-run/real.

VERDICT: NOT ACCEPTED

---

# Round 2 — re-review of the B1 / MAJOR 1 fix at `5bddab73` (17 November 2026)

Reviewer: `reviewer-e1-amend`, same independent read-only reviewer as round 1. This round reviewed
only the delta since round 1; this addendum is the only write. No execution of e1, no e1 dry run, no
driver run, no job, no server, no B.2, no label, no deepthought/ceph write, no git write. Review
date 2026-11-17 (Europe/Berlin).

## R2.1 Reviewed delta and pins

- Branch `r1-e1-openml-amend-20261117` now at **`5bddab731f6b4fa226e37dd8dc6d7e6f202232e1`**:
  `2e842df0` "fix(r1): e1 amended mechanism — parse the reviewed audit's launch_utc ISO prefix …
  add real-audit regression test" and `5bddab73` "test(r1): … test alias typo". Parent chain
  `5bddab73 → 2e842df0 → b58bbb31 (round-1 unit) → 16185b0b (authority base)`;
  `git merge-base --is-ancestor 16185b0b HEAD` holds.
- Delta since `b58bbb31` (`git diff --name-status`): exactly
  `M r1/c3/e1_openml_offline.py` (+8/−1, 9 changed lines: `import re`, `_parse_utc` docstring, leading-ISO-token
  parse), `M r1/tests/test_e1_openml_offline_mechanism.py` (+10: the real-audit regression test),
  and `A docs/r1/reviews/E1_AMEND_REVIEW_20261117.md` (the round-1 review file — see R2.5 note; not
  authored/committed by me). No other file changed: the driver, `e1_offline_network.py`,
  `OFFLINE_MECHANISM_AMENDED_20261117.md`, the accepted audit/report/SHA256SUMS and accepted
  reviews are untouched in the delta.
- Pins at `5bddab73`: **driver `r1/scripts/c3_env_replay.py` SHA-256
  `1b1e2fb229e78a82b56f1b8c9e45d6bc36412facf26d89f05bf6acb830a7e7e0` — unchanged** from round 1
  (the parser fix is in the mechanism module, not the driver; re-hashed at `5bddab73` as
  requested). The changed reviewed-file hashes are the mechanism module `r1/c3/e1_openml_offline.py`
  SHA-256 **`6bcc50fe2544afd7ae1fdf86f9061eeb037fc3a9f35fdd6d3a9d64213e97efa3`** (was `ce0cc005…`)
  and the test module `faec8865…`. **The amended driver pin is therefore cleared at
  `1b1e2fb2…`, cited under row R1-E1-OPENML-AMEND; the authorization's `5ef9db16…` still predates
  the amendment.** (Round 1's "candidate pin not cleared" caveat is superseded by this line.)
- `OFFLINE_MECHANISM_AUDIT.json` is byte-identical to the accepted `5d73550a`:
  SHA-256 `9f14c879973ff4080655a2e108e6e7a1aad2b031d96d4f96e914921ddaa190b7`; the round-1 artifacts
  and their hashes are unchanged (report `61a3d02b…` verified again).

## R2.2 B1 — fixed and fail-closed

`_parse_utc` (`r1/c3/e1_openml_offline.py:117–131`) now extracts the leading ISO-8601 UTC token
`^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z)` and ignores the trailing provenance suffix;
if no leading token matches it falls back to parsing the whole string, so non-conforming input
still raises `MechanismStop`. Reproduced on the fixed tree:

```
audit launch_utc: "2026-10-27T15:48:34Z (from the frozen manifests' started_utc)"
M._parse_utc(launch_utc) -> 2026-10-27 15:48:34+00:00
M._parse_utc(mtime_utc)  -> 2026-10-27 15:22:39+00:00     (clean values unchanged)
STOP (still fail-closed) for: "garbage", "", "2026-10-27T15:48:34 (no tz)",
                              "2026-13-40T99:99:99Z (bad date)", None
```

I also re-drove the **real `bind_cache_check`** with every other pin satisfied (synthetic batch
record, record sha / `CACHE_CHECK_SHA256` / mtime all matching, the real audit dict): it now
passes and returns `mtime_utc = 2026-10-27T15:22:39Z`, `launch_utc = 2026-10-27T15:48:34Z`, i.e.
the pre-launch ordering check is reached and holds (mtime 26 min before launch). The sha /
mtime / batch-path / pre-launch checks still run in the same order (hash and mtime are bound before
the launch parse); the fix only makes the recorded timestamp parseable. The only behavioural
leniency is that an arbitrary suffix (not just the parenthetical) after a valid leading timestamp
is ignored; that is acceptable because the only callers pass the **byte-pinned** audit or
code-owned constants, not untrusted text (minor, cosmetic).

## R2.3 MAJOR 1 — fixed

The new `test_real_audit_launch_utc_suffix_parses` loads the real
`docs/r1/reports/e1_replay_20261116/OFFLINE_MECHANISM_AUDIT.json`, reads
`sweep1_batch_records.launch_utc`, calls `M._parse_utc` and asserts the result starts with
`2026-10-27T15:48:34`; it passes. That directly covers the exact failure round 1 found (the tests
previously only used a clean fixture timestamp). The full `bind_cache_check` path with the real
audit's sha/mtime/launch values was additionally exercised manually above and passes; a future
strengthening could mount a synthetic batch record in the test, but the regression that actually
occurred is now covered by a committed test.

## R2.4 Tests and side effects

```
pytest r1/tests/test_e1_openml_offline_mechanism.py r1/tests/test_e1_offline_network.py \
       r1/tests/test_e1_openml_offline_wiring.py -q
-> 63 passed, 1 skipped in 7.79 s
```

64 collected (round 1: 63 = 62 passed + 1 skipped); the new test passes on its own
(`1 passed`). The skip is unchanged: `test_e1_offline_network.py::test_linux_install_denies_sockets`
(Linux x86-64 seccomp only) and **must be run on deepthought before the e1 real run**, together with
the real kernel install/probe. Worktree clean apart from this addendum; no e1/dry-run/job/ceph
artifact; no git write by me. `docs/r1/reports/` and the accepted reviews are unchanged in the
delta.

## R2.5 Note (not a gate) — the round-1 review file is committed in the branch

The fix commit `2e842df0` also committed the round-1 review file
`docs/r1/reviews/E1_AMEND_REVIEW_20261117.md` (blob `debdb637…`) — I left it uncommitted as
instructed; it appears to have been swept in with the fix. It does not affect the driver, mechanism,
tests or run artifacts, but the operator/review packet should treat it as a review artifact, not as
part of the reviewed mechanism; this round-2 addendum edits the same file (as the reviewer write),
and the lead may commit it. No action is required for the e1 run.

## R2.6 Remaining findings

- **B1: cleared.** The real run can now reach `prepare()` → `state = VERIFIED`; launch/mtime
  binding verified end-to-end with the real audit.
- **MAJOR 1: cleared** by the real-audit regression test (1 new test; 63 passed/1 Linux-skip).
- Round-1 minors remain non-blocking and unchanged: mtime truncated to whole seconds;
  `MechanismStop` in `execute_case` reported as "interrupted"; the (b) inherited-fd nuance could be
  stated; the audit's transcribed cache_check rows are a trimmed subset while the runtime reads the
  hash-pinned live file; no remote/ceph checks from this host. No new blockers or majors.

## R2.7 What still applies to the first real use

The round-1 §9 operator checklist applies unchanged, with the amended pins now cleared:
**driver `1b1e2fb2…` at `5bddab73`** (cite row R1-E1-OPENML-AMEND; not the 16 Nov `5ef9db16…`),
mechanism module `6bcc50fe…` if the packet records module hashes; audit `9f14c879…` byte-identical.
Dry run first into a new directory, then the real run into a different new directory with
`--openml-offline-mechanism r1-e1-openml-amend-20261117`; on deepthought run the Linux-only seccomp
test, then watch the (b) probes (`Seccomp: 2`, errno 101 in-process and child), the batch/venv pins,
harness clean at `6adf3859…`, `cache_check.json` sha `35e76f37…` + mtime `15:22:39Z` before the
`15:48:34Z` launch, (i) ids via `git show`, (iii) ARFF md5 vs metadata, (iv) four files + tree
digests, (ii) ten-field fingerprint/versions/harness-cache path, `state = VERIFIED` in
`replay_plan.json` before the first case, per-case before/after checks, post-run source-cache +
network re-proof, and the unchanged zero-tolerance 16/16 token pass rule. Anything else is a STOP:
retain everything, no retry.

## R2 Verdict

The single round-1 blocker is fixed exactly as recommended and in the right place (the pinned audit
stays byte-identical, the parser is code-side, the pre-launch binding order is preserved), the
regression test now binds the real committed audit, and the fix is fail-closed on malformed
timestamps. The delta touches only the mechanism module and its test module (plus the review file),
the driver hash is unchanged, and the re-run of the three suites gives 63 passed / 1 expected
Linux-only skip. Nothing else in the round-1 verification changed. The e1 dry-run + real run may
proceed on deepthought under a fresh operator with the amended pins above, followed by independent
review of the run report.

VERDICT: ACCEPTED
