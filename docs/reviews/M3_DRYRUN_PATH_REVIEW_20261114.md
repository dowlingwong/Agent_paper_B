Reviewed base: 5ef9db16faf0d43843a5e8110b9181173b49175c

# M3 dry run records sweep_index.path (IT-1 option a) — independent review record (14 November 2026)

Author decision IT-1 (a), 14 Nov. Branch `mac-m3-dryrun-path-20261114` from M3's accepted commit `ec6e30a9`; one commit `5ef9db16` (two files, +9/−1). One round by a freshly spawned independent reviewer agent (AI-assisted, Claude): **accepted**.

Accepted commit (round 1, last): 5ef9db16faf0d43843a5e8110b9181173b49175c

Notes, not blocking: the new test checks the field, not the guard (the guard is not on this branch; after integration the existing dry-run test exercises it end to end); the test expects `(REPO/INDEX).resolve()` while the script writes `REPO.resolve()/INDEX` (differ only under a symlink, failing safe); blank lines around the new test; only path and SHA are recorded under `sweep_index`, which is all the guard and IT-1 (a) need.

The round text is reproduced unchanged below.

---

# Independent review: IT-1 (a), M3 dry run records `sweep_index.path` (round 1)

Reviewed commit: 5ef9db16faf0d43843a5e8110b9181173b49175c
Branch: `mac-m3-dryrun-path-20261114` (worktree /tmp/pb/wt/m3path)
Base: ec6e30a98811fd6502d168361371a084387c135d (M3 accepted commit)
Context: author decision IT-1 (a), 14 Nov; `docs/r1/reports/INTEGRATION_TRIAL_20261114.md` §3 on
`mac-int-trial-20261114`; guard `_index_is_frozen_sweep1` in `r1/c3/analysis_guard.py` at 5d8c0274.
Reviewer: independent; did not write the change. Read-only; scratch worktrees under /tmp/rev_it1 only, removed after.

## What changed

`git diff ec6e30a9 5ef9db16` touches two files and nothing else (one commit, `git diff --check` clean):

- `r1/scripts/c3_audit_dryrun.py` l. 94: `'sweep_index': {'sha256': ...}` becomes
  `'sweep_index': {'path': str(index_path), 'sha256': _sha(index_path)}`.
- `r1/tests/test_c3_audit_dryrun.py`: new `test_dryrun_table_records_the_sweep_index_path_and_sha`.

No guard change, no author row, no other behaviour change. This matches IT-1 (a) as given in §3.

## Checks

### 1. Matches `dataset.build_from_sweep`; guard suffix and is_file checks pass

- `build_from_sweep` writes `"sweep_index": {"path": str(index_path), "sha256": _sha256(index_path), ...}`, where
  `index_path` is whatever `resolve_sweep` returns: absolute or relative, not resolved. The M3 change uses the same
  key and the same `str(path)` form. Its `index_path` is `paper.resolve() / INDEX`, so it is always absolute. Both
  forms are valid input for the guard, and the absolute form does not depend on the cwd.
- I called `_index_is_frozen_sweep1` (5d8c0274) on the M3 build.json shape: it returns True (the suffix
  `results/r1/pilot/C3_sweep_index_20261028T033315Z.json` matches, `is_file` holds, and the bytes hash to `812468e2…`).
  Without `path` (the base behaviour) it returns False, because `Path('')` resolves to the cwd.
- `INDEX_SHA256` in `r1/scripts/c3_env_replay.py`, used by `verify_source_pins`, equals the guard's `SWEEP1_INDEX_SHA`.
  So `build_table` refuses any corpus whose index is not the frozen one before it writes a table.

### 2. No non-frozen table gets through

The change touches only the input that a table produced by `build_table` gives the guard. Every guard condition still
holds. Probe results with `_index_is_frozen_sweep1` at 5d8c0274:

| build.json `sweep_index` | result |
|---|---|
| M3 shape after the change (absolute real path, frozen SHA) | True |
| M3 shape before the change (SHA only) | False |
| correct suffix, different bytes, frozen SHA claimed | False |
| frozen bytes copied to a different filename | False |
| real path, different SHA | False |
| real path, SHA missing | False |
| nonexistent path, frozen SHA | False |
| directory at the correct suffix | False |
| relative path, cwd ≠ paper root | False |

`build_table` can only produce a table from a corpus whose index passes `verify_source_pins` (the frozen SHA, not a
symlink). The table it labels DRYRUN therefore really comes from sweep 1. The guard has never checked the label, and
this change does not touch that. The limit stated in the guard's docstring still applies: a repository writer could
relabel the provenance by hand. That limit is unchanged here, and `build_from_sweep` tables already record the path.

### 3. The new test is not vacuous

- On 5ef9db16: `8 passed in 10.26s` with the given command.
- Scratch worktree of 5ef9db16 with only `r1/scripts/c3_audit_dryrun.py` reverted to ec6e30a9: the new test FAILS
  (`Right contains 1 more item: {'path': '/tmp/rev_it1/neg/results/r1/pilot/C3_sweep_index_20261028T033315Z.json'}`),
  and the other 7 tests pass. So the test detects whether the field is present.

### 4. The claim about integration tip 5d8c0274

Scratch worktree of 5d8c0274. At that tip, `c3_audit_dryrun.py` and its test file are byte-identical to ec6e30a9.

- Unchanged: `1 failed, 6 passed`. The failure is
  `test_dryrun_on_the_frozen_corpus_partitions_the_whole_population` with
  `RuntimeError: STOP: exact affirmative R1-BX-D8-CONFIRM with current gate SHA required` (analysis_guard.py:163),
  as §3 reports.
- With only the one-line script change applied (`git apply` of the script hunk of ec6e30a9..5ef9db16):
  `7 passed in 6.07s`. The claim in the commit message holds.
- With the new test also applied there: `8 passed in 11.08s`.

### 5. Nothing else changed

Confirmed: the diff has 2 files, 9 insertions and 1 deletion, all described above. The commit message states the
decision, the scope and the 5d8c0274 result accurately.

## Findings

- NON-BLOCKING (N1): the new test checks the build.json field but does not run the guard, because
  `r1/c3/analysis_guard.py` does not exist on this branch. After integration,
  `test_dryrun_on_the_frozen_corpus_partitions_the_whole_population` exercises the guard end to end (verified in
  check 4). No action needed now. If wanted, a guard-level assertion could be added on the integration branch later.
- NON-BLOCKING (N2): the test's expected value is `str((REPO / D.INDEX).resolve())`, while the script writes
  `str(REPO.resolve() / D.INDEX)`. The two differ only if `results/` or `results/r1/pilot/` is a symlink inside the
  checkout. Then the test would fail spuriously; it would never pass when it should not. `(REPO.resolve() / D.INDEX)`
  would mirror the script exactly. Cosmetic.
- NON-BLOCKING (N3): whitespace. The new test has three blank lines before it and one after (before `def _rows`),
  where PEP 8 expects two in both places. Cosmetic.
- NON-BLOCKING (N4, information): `build_from_sweep` also records label, nodes, instances, runs, harness_commit and
  audit under `sweep_index`, while the dry run records only path and SHA. The guard needs only path and SHA, and IT-1 (a)
  asks only for the path, so this is within scope.

No BLOCKING findings.

Verdict: accepted
Accepted commit: 5ef9db16faf0d43843a5e8110b9181173b49175c
