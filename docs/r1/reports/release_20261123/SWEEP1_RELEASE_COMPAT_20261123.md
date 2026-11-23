# Sweep-1 release fix: replay with the table's own builder (R1-SWEEP1-RELEASE-COMPAT, option A)

**ENGINEERING_ONLY. No sealed table, label block or evaluation block was opened; all tests use synthetic data.**
Authority: R1-SWEEP1-RELEASE-COMPAT (option A) on `main` `1402f466`, after the diagnosis
`reports/release_20261122/SWEEP1_RELEASE_DIAGNOSIS_20261122.md` (review ACCEPTED); REL-CODE A (the change is in
`r1/c3/release_checks.py` only).

## What changes

Only `r1/c3/release_checks.py`. During the sweep-1 integrity check, and only there, `audit._verify_replay` is replaced
by `_sweep1_compat_replay`; it is restored on exit, also on failure. `r1/c3/audit.py`, `r1/c3/release.py`, the sealed
table, the audit and sweep 2's check are unchanged.

`_sweep1_compat_replay(table, paper_root, index, classification)` keeps every step of `audit._verify_replay` and
changes two:

| step | `audit._verify_replay` (main) | compatibility replay |
|---|---|---|
| guards | `refuse_sealed`, `guard_table` | the same |
| scratch | local `/tmp` mount (`findmnt`), free space ≥ 2 × table | the same |
| pin | — | the sealed `build.json` must record `commit = ab79b4ce0e42…` (the B.2 audit commit); any other table is refused |
| builder | main's `r1.c3.dataset.build_from_sweep` (featurizer v3) | the builder of `ab79b4ce` (featurizer v2), run in `python -I` from a throwaway `git clone --shared` checked out at `ab79b4ce` (objects shared; nothing written to the paper repo); the child refuses unless `FEATURIZER_VERSION` is `c3_features/v2` and every loaded `r1.*` module comes from that checkout, and reports its git head, which must be `ab79b4ce` |
| proposals, configs | byte-identical to the sealed files | the same |
| `build.json` | equal with `commit` dropped | equal with `commit` dropped and `classification.path` normalized: the replay's classification file must lie in the paper root, the sealed path must end with the same repository-relative path, and every other classification field, its `sha256` included, must be equal |

The child runs in the caller's working directory, so a relative index path is recorded as in the sealed `build.json`
(the diagnosis: `sweep_index.path` is relative in both records). It needs `git` and commit `ab79b4ce` in the
release checkout's object store (an ancestor of `main`).

## Tests (`r1/tests/test_c3_sweep1_release_compat.py`, 8)

On a synthetic builder repository with a v2 and a v3 commit whose `budget_frac_left` differs after a skipped proposal,
a "sealed" table built by v2 at a `/ceph`-like paper root, and a `/work`-like release root:
- **without the fix**, the unchanged `audit._verify_replay` refuses with main's v3 builder ("differs … proposals.jsonl")
  and, with the v2 builder, on `build.json` ("build metadata differs"): the two gates of the diagnosis;
- **with the fix**, the replay passes at the release root and at the audit's own root, and main's builder is never
  called;
- tampered proposals or configs, other classification bytes, the same bytes at another repository path, a
  classification outside the paper root, any other `build.json` field, a table not built at the pinned commit, a builder
  of another featurizer and a missing sidecar are all refused;
- `sweep1_integrity` installs the replay only for its check and restores it (also on failure); `sweep2_integrity` is
  unchanged and uses the original replay;
- in this repository, `ab79b4ce`'s builder imports in the isolated interpreter with featurizer v2, its own git head,
  and every `r1` module from the throwaway checkout.

`test_c3_release.py` (41) and the sweep-2 integrity test pass unchanged.

## Then

The change is inert until published: `release.py` refuses a `release_checks.py` that differs from `origin/main`, and
each receipt records its sha256. After the merge, the cluster agent reruns the sweep-1 train/dev release under
R1-S2-LABELS-TRAINDEV-RELEASE, from the same working directory and with the same index and classification arguments
as the refused run. If the replay still refuses, it is a STOP with the exception type, as before; the diagnosis
predicts a pass (a v2 replay reproduced the sealed proposals and configs byte for byte).
