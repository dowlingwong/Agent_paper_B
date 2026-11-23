Reviewed base: `1402f466` (published `main`); accepted at `6f5f23a0`, confirmed at `bbf07c2beb0f82893d7457b4424dbb69141c6342`

# Independent review record — the sweep-1 release fix: replay with the table's own builder (R1-SWEEP1-RELEASE-COMPAT, option A)

**Unit.** On `mac-sweep1-release-compat-20261123` over published `main` `1402f466`: `r1/c3/release_checks.py` only (REL-CODE A). Within the sweep-1 integrity check, `audit._verify_replay` is replaced by `_sweep1_compat_replay` and restored on exit: the sealed table (its `build.json` must record `ab79b4ce`) is replayed by the builder of `ab79b4ce` (featurizer v2) in an isolated `python -I -B` child from a throwaway shared clone, with the harness root resolved by the parent and passed explicitly; proposals and configs must be byte-identical; `build.json` is compared with `commit` dropped and `classification.path` normalized to the R1-SWEEP1-CLASSIFY sidecar's repository-relative path (sha256 and every other field equal). Environment and builder failures raise RuntimeError, identity mismatches ValueError. `audit.py`, `release.py` and sweep 2's check are unchanged. Tests: `r1/tests/test_c3_sweep1_release_compat.py` (12, synthetic). Report: `docs/r1/reports/release_20261123/SWEEP1_RELEASE_COMPAT_20261123.md`. Authority: R1-SWEEP1-RELEASE-COMPAT (option A) on `main`, after the reviewed diagnosis `docs/r1/reports/release_20261122/SWEEP1_RELEASE_DIAGNOSIS_20261122.md`; the queue of 23 Nov 2026 (01:39), item 1.

**Process.** One independent reviewer, read-only, synthetic data only (no sealed table, label block, evaluation block or secrets file opened; it checked only that the published sweep-1 index has a `noise_source` key), scratch under `/tmp/relcrev/` moved to its `_to_delete/`. Round 1 found two majors (the child depended on an inherited `AR_HARNESS_ROOT`, which the throwaway clone cannot find as a sibling; the child could write bytecode into the audited harness) and four minors; round 2 accepted with two minors (a ValueError from the builder's own source-data checks surfaced as RuntimeError; the harness bytecode test compared directories, not files), which the confirmation round confirmed fixed.

| Round | Reviewed | Verdict |
|---|---|---|
| 1 | `12bef509` | NOT ACCEPTED (M1–M2; minors m1–m4) |
| 2 | `6f5f23a0` | ACCEPTED (minors m-a, m-b) |
| 3 | `bbf07c2b` | ACCEPTED (confirmation) |

**Open items.** (1) The fix is inert until merged: `release.py` refuses a `release_checks.py` that differs from `origin/main`; merge by a merge commit. (2) The cluster agent then reruns the sweep-1 train/dev release under R1-S2-LABELS-TRAINDEV-RELEASE with `AR_HARNESS_ROOT` exported to the audited harness (or from a checkout with the harness as its sibling), from the same working directory (`/work/dwong/s2_audit_20261122/paper`) and with exactly the same `--index` and `--classification` strings as the refused run; the release checkout must be a full clone containing `ab79b4ce`; `git` and `findmnt` available; `/tmp` local with at least 2× the table plus about 175 MB free. (3) Time limits: 300 s per git step of the checkout, 7,200 s for the child build. (4) The steps after the replay (plan comparison, completion, role-block re-derivation) have not yet run on the sealed sweep-1 table with main's `audit.py`; a further STOP there would fail safe and is not caused by this unit. A RuntimeError STOP is an environment or builder-internal problem; a ValueError STOP is an identity mismatch.

## Round 1 (`12bef509`)

> Reviewed base: 12bef509ed4be1c8a7cfd97d13389eddadc6354d
>
> **Summary**
>
> The design is right and mostly done well. The commit changes only r1/c3/release_checks.py (plus a test and a report). Inside sweep1_integrity only, it swaps audit._verify_replay for _sweep1_compat_replay.
>
> - **Equivalence with the original.** The compat replay keeps every guard and comparison of audit._verify_replay (audit.py l.508–532): refuse_sealed, guard_table, the findmnt local-scratch check, the 2× table capacity check, and byte comparison of proposals.jsonl and configs.json. build.json is compared with `commit` dropped. The only changes are the builder and the classification.path normalization, as the PLAN row allows.
> - **Pin.** Enforced three ways. The sealed build.json `commit` must equal the full 40-hex sha. The parent checks `rev-parse HEAD` in the clone and that it is clean. The child reports `git_head`, which must equal the pin, and refuses unless the featurizer is `c3_features/v2`.
> - **Isolation.** I checked this by running it: an isolated child on a real ab79b4ce clone had neither the empty path entry nor the checkout on sys.path, and loaded no module from /tmp/pb. r1 is a regular package (it has `__init__.py`), so an editable-install `.pth` cannot merge a second copy in. The foreign-module check runs after the build, so it also catches r1 modules imported lazily during the build.
> - **Clone safety.** `git clone --shared --no-checkout` writes nothing to the paper repo.
> - **Swap safety.** The swap is restored in `finally`, nesting is safe, and only audit.py l.896 calls the function, by its global name. The release CLI is single-threaded. It is acceptable under REL-CODE A, since the PLAN row says "release_checks.py (or its replay wrapper)".
> - **Working directory.** Running the child in the caller's working directory is correct. It keeps `sweep_index.path` the same relative string, and `-I` means nothing is imported from the working directory.
> - **Release integration.** This is unchanged. release.py reports only the exception type, the receipt records the new release_checks sha256, and the change does nothing until it is published to origin/main. No code reads the changed `check` string.
> - **Sweep 2.** Its check is untouched.
> - **Tests.** The targeted command passed (49 passed: 8 new, 41 in test_c3_release). The synthetic fixture reproduces both gates (v3 fails on proposals; v2 fails on build metadata). It covers the accept case and the tamper cases (proposals, configs, classification bytes, path, outside the root, other build.json field, pin, featurizer).
>
> Two runtime problems in the child stop me accepting it.
>
> **Findings**
>
> **M1 (major): an undocumented runtime dependency on AR_HARNESS_ROOT, not covered by the tests.**
> - *Where:* `_run_builder` / `_CHILD`; the report's runtime paragraph; `test_the_real_pin_imports_the_v2_builder_in_isolation`.
> - *Problem:* sweep 1's index has a `noise_source`, so ab79b4ce's `sweep_sources` lazily imports `r1.headroom.e1b_collect`. At import that module calls `import_harness()`, which needs `$AR_HARNESS_ROOT` or a sibling folder `REPO.parent/autoresearch_harness`. In the throwaway clone, REPO is `/tmp/r1_c3_sweep1_compat_*/src`, so that sibling never exists. I confirmed this on a real ab79b4ce clone: `RuntimeError harness src not found at /tmp/.../autoresearch_harness/src; set AR_HARNESS_ROOT`. Main's replay in the release checkout can find the sibling; the clone cannot. The probe test only imports dataset and features, so it misses this.
> - *Failure scenario:* if the cluster run does not export AR_HARNESS_ROOT (or found the harness as a sibling last time), the release stops with an unexplained `ValueError`. It works today only because the 22 Nov run happened to export AR_HARNESS_ROOT, which the child inherits (`-I` drops only `PYTHON*` variables).
> - *Fix:* in the parent, resolve `r1.harness.harness_root()`. Refuse early if `<root>/src` is missing, then pass it explicitly with `env={**os.environ, "AR_HARNESS_ROOT": str(root)}`. State the requirement in the report. Add a test that the child gets it, for example a probe that imports `r1.headroom.e1b_collect` when a harness is available and skips otherwise, or a unit test on the env passed.
>
> **M2 (major): the child writes bytecode into the audited harness.**
> - *Where:* `_run_builder`, `[sys.executable, "-I", "-c", ...]`.
> - *Problem:* the operator runs with `python -B` and `PYTHONDONTWRITEBYTECODE=1`. `-I` ignores the variable, and `-B` is not passed on to the child. I checked: the parent has dont_write_bytecode 1, the child 0. With AR_HARNESS_ROOT set, the child imports `autoresearch.*` from the audited harness and writes `__pycache__/*.pyc` there.
> - *Failure scenario:* audit.harness_untracked_state (l.654, used at l.721 and l.1286) stops on any untracked harness file outside the e1 record. If the harness does not gitignore `__pycache__`, later audits on that harness stop. In any case the release step changes an audited tree it is meant to leave alone.
> - *Fix:* run `[sys.executable, "-I", "-B", "-c", ...]`. Have the probe report `sys.flags.dont_write_bytecode` and assert it in the test.
>
> **m1 (minor): the path normalization is a suffix match, not anchored to a root.**
> - *Where:* `normalize_provenance`.
> - *Problem:* it only checks that the sealed path ends with `"/" + rel`, where `rel` is relative to whatever paper root was passed. On its own this accepts a different root depth, which is weaker than the report's "the same repository-relative path". In practice no different classification file can pass: the sha256 must match, all other classification fields must be equal, and main's `evidence_classification`, which runs first in `evidence_plan`, ties the sidecar's path to the R1-SWEEP1-CLASSIFY PLAN row under the same paper root. Other build.json drift is still refused by the full-dict comparison.
> - *Fix (optional hardening):* require `rel` to equal the PLAN-bound sidecar path (`results/r1/evidence/C3_sweep_classification_20261028.json`), and/or pin the sealed prefix to the B.2 audit paper root.
>
> **m2 (minor): the scratch capacity check ignores the clone.**
> - *Where:* `_sweep1_compat_replay`.
> - *Problem:* the check still asks only for 2× the table, but the replay now also checks out ab79b4ce into /tmp (11,226 files, about 174 MB).
> - *Fix:* add a margin for the checkout, or document it.
>
> **m3 (minor): failures are hard to tell apart in a STOP.**
> - *Where:* `_run_builder` and the compat replay.
> - *Problem:* release.py shows only the exception type. A child that fails to start (harness, imports, pin) and a real data or metadata mismatch both surface as `ValueError`, so the cluster agent cannot tell an environment problem from evidence drift.
> - *Fix:* raise a distinct type (for example RuntimeError) for builder or environment failures, and keep ValueError for identity mismatches.
>
> **m4 (minor, informational): new timeouts and an untested downstream path.**
> - The clone has a 300 s timeout and the child a 7200 s timeout; the original replay had neither. Hitting one stops the run as TimeoutExpired. Document this.
> - Separately, the steps after the replay (plan comparison, completion, role-block re-derivation) have never run on the sealed sweep-1 table with main's audit.py, which has changed substantially since ab79b4ce. A further stop is possible. It would fail safe and would not be caused by this unit.
>
> **Cluster runtime notes (for the agent)**
> - Merge to main first; release.py refuses a release_checks.py that differs from origin/main.
> - Export AR_HARNESS_ROOT pointing at the audited harness, as on 22 Nov (until M1 is fixed, this is required).
> - Run from the same working directory (`/work/dwong/s2_audit_20261122/paper`) with exactly the same `--index` and `--classification` strings as the refused run. An absolute index path would change `sweep_index.path` and stop the run.
> - The release checkout must be a full (not shallow) clone containing ab79b4ce.
> - git and findmnt must be available.
> - /tmp must be local xfs, ext4 or btrfs, with free space of at least 2× the table plus about 200 MB.
> - `ls-remote` needs network access, as before.
> - The same 3.13 venv is fine: ab79b4ce's code ran under it at the audit.
>
> **Process**
> - Nothing was modified in /tmp/pb/wt/relc or /tmp/pb/repo; the worktree is clean at 12bef509.
> - I ran only the prescribed targeted tests, plus one read-only isolation demonstration in scratch.
> - Scratch is moved to /tmp/relcrev/_to_delete/.
> - No sealed data, labels or evaluation values were read. I only checked that the published sweep-1 index has a `noise_source` key, and its path.
>
> VERDICT: NOT ACCEPTED (fix M1 and M2: pass AR_HARNESS_ROOT explicitly and add `-B`, with tests; the minors are optional)

## Round 2 (`6f5f23a0`)

> Reviewed base: 6f5f23a0a1741c2b51bb2aa47c1c1367a4736bc5 (round 2; diff 12bef509..6f5f23a0)
>
> **Summary**
>
> All round-1 findings are fixed, and I found no new blocking or major problem. The verdict is ACCEPTED. Two small optional points remain (m-a and m-b below).
>
> **Tests**
> - Without AR_HARNESS_ROOT: 51 passed, 1 skipped (the harness test; there is no sibling harness here).
> - With AR_HARNESS_ROOT=/tmp/pb/wt/t1h: 52 passed.
> - The harness was left untouched. No file in t1h was newer than my timestamp taken before the run, the `.pyc` count stayed at 45, and `git status --ignored` was the same before and after (9 entries).
> - The worktree is still clean at 6f5f23a0.
>
> **Per finding**
>
> - **M1 (fixed).** `child_harness_root()` calls the same `harness_root()` main's replay would use: `r1/harness.py` is unchanged since ab79b4ce. It refuses with RuntimeError if `<root>/src` is missing, before the scratch check and before any checkout or build. The child's environment drops any inherited AR_HARNESS_ROOT and sets only the resolved root.
>   - The tests check all four parts: the explicit root wins over a different inherited value; nothing is inherited when no root is passed; a missing harness stops the run before `_run_builder` is ever called; and the synthetic builder, like the real one, fails without a harness.
>   - The real-pin test imports ab79b4ce's `r1.headroom.e1b_collect` with the resolved root.
> - **M2 (fixed).** The child runs as `-I -B` and reports `sys.flags.dont_write_bytecode`. The parent refuses unless it is true. I confirmed above that the real harness was not modified.
> - **m1 (fixed).** The replay's classification path must now equal `SWEEP1_CLASSIFICATION_REL`. I confirmed that path is in the R1-SWEEP1-CLASSIFY row on the tip's PLAN. The sealed path must be absolute and end with `"/" + rel`. With the sha256 and every other field also required to be equal, this is tight. Tests cover a relative sealed path, a different sealed path and a different sidecar.
> - **m2 (fixed).** `checkout_bytes()` parses `ls-tree -r -l` correctly: it counts blobs only, so submodule `-` sizes are skipped, and paths containing spaces are safe. The test checks the boundary: one byte short is refused, the exact amount passes. File-system block overhead is not counted, which is negligible.
> - **m3 (fixed, with one wording caveat; see m-a).** Git and checkout errors, an unclean checkout, a failed or timed-out child, the featurizer, the git head, the bytecode flag and a missing harness all raise RuntimeError. Table, build.json, classification, pin and capacity mismatches stay ValueError.
> - **m4 (fixed).** The report now documents the time limits, the untested downstream steps, the AR_HARNESS_ROOT requirement and the full (not shallow) clone requirement.
>
> **Remaining minors (optional, non-blocking)**
>
> - **m-a: some data failures will show as RuntimeError.**
>   - *Where:* `_run_builder`, and the "Failures are typed" paragraph in the report.
>   - *Problem:* any exception inside the ab79b4ce builder becomes RuntimeError. That includes its own source-data identity checks, for example "moved sweep differs from original commit blobs" or a manifest hash mismatch. So a RuntimeError STOP does not strictly mean an environment problem. Most of these checks also run earlier as ValueError in main's `evidence_classification`, so this is unlikely to matter in practice.
>   - *Fix:* reword the report ("environment or builder-internal failure"), or have the child exit with a distinct code for ValueError and map it back.
> - **m-b: the harness test is weaker than the hand check.**
>   - *Where:* `_pycache` in `test_the_real_pin_imports_its_harness_module_with_the_resolved_root`.
>   - *Problem:* it compares lists of `__pycache__` directories, not `.pyc` files. New `.pyc` files inside the harness's existing 9 `__pycache__` folders would go unnoticed. `-B` and the parent's flag check already prevent such writes, so this is only a test-strength issue.
>   - *Fix:* compare `rglob("*.pyc")` with sizes and mtimes.
>
> **Cluster notes (unchanged except AR_HARNESS_ROOT)**
> - Merge first.
> - Export AR_HARNESS_ROOT pointing at the audited harness, or run from a checkout that has the harness as its sibling.
> - Use the same working directory and the same `--index` and `--classification` strings as the refused run.
> - The release checkout must be a full clone containing ab79b4ce.
> - git and findmnt are needed. /tmp must be local, with at least 2× the table plus about 175 MB free.
>
> **Process**
> - Read-only throughout; I ran only the targeted tests.
> - Scratch is moved to /tmp/relcrev/_to_delete/ (t2 is from this round).
> - No sealed data, labels or evaluation values were read.
>
> VERDICT: ACCEPTED

## Round 3 (`bbf07c2b`)

> Reviewed base: bbf07c2beb0f82893d7457b4424dbb69141c6342 (confirmation round; diff 6f5f23a0..bbf07c2b)
>
> **Summary**
>
> Both minors from round 2 are fixed correctly, and the change adds no new problem. Verdict: ACCEPTED.
>
> **Tests**
> - With AR_HARNESS_ROOT=/tmp/pb/wt/t1h: 53 passed (test_c3_release.py plus this file).
> - Without the variable: 52 passed, 1 skipped (the harness test).
> - The harness was not modified: the `.pyc` count stayed at 45, `git status --ignored` stayed at 9 entries, and no file was newer than my timestamp taken before the run.
> - The worktree is clean at bbf07c2b.
>
> **m-a (fixed)**
> - In the child, only a ValueError raised by `dataset.build_from_sweep` is turned into exit code 3, with the message on stderr. The parent maps exit code 3 to ValueError, and every other non-zero exit stays RuntimeError.
> - **No unintended collisions.** An uncaught exception in Python exits with 1, `SystemExit("msg")` with 1, an interpreter usage error with 2, and a signal gives a negative code. So the featurizer check, the foreign-module check, a harness import failure, ab79b4ce's own RuntimeErrors (such as the D8 confirmation STOP) and git CalledProcessErrors all stay RuntimeError.
> - **ValueError subclasses also count as data refusals.** JSONDecodeError, UnicodeDecodeError and errors from `relative_to` also exit with code 3. That is the right category, because they come from reading the source data.
> - On the code-3 path the foreign-module check is skipped. That is harmless, since the run fails anyway.
> - The new test exercises the real child path through `_run_builder`.
>
> **m-b (fixed)**
> - `_pycache` now maps each `*.pyc` file to its size and modification time, so an added or rewritten bytecode file inside an existing `__pycache__` folder now shows up. The fake-harness assertions were updated to compare empty dicts.
>
> **Docs**
> - The module docstring and the report's "Failures are typed" paragraph match the code.
> - The test count (12) and the pass count (53) are correct.
>
> **Process**
> - Read-only throughout; I ran only the targeted tests.
> - Scratch is moved to /tmp/relcrev/_to_delete/ (t3 is from this round).
> - No sealed data, labels or evaluation values were read.
>
> VERDICT: ACCEPTED

---

Code-Commit: bbf07c2beb0f82893d7457b4424dbb69141c6342
Verdict: ACCEPTED

Accepted at `6f5f23a0`, confirmed at `bbf07c2b`.
