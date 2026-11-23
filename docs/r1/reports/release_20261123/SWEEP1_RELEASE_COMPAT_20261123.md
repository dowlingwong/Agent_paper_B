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
| scratch | local `/tmp` mount (`findmnt`), free space ≥ 2 × table | the same, plus the size of the `ab79b4ce` checkout (`git ls-tree -r -l`; about 174 MB) |
| pin | — | the sealed `build.json` must record `commit = ab79b4ce0e42…` (the B.2 audit commit); any other table is refused |
| harness | found by `r1.harness` in the same process (`$AR_HARNESS_ROOT`, else the release checkout's sibling `autoresearch_harness`) | the same root, resolved by the parent with `r1.harness.harness_root()` and passed explicitly to the child as `AR_HARNESS_ROOT` (nothing inherited); refused before any build if `<root>/src` is missing |
| builder | main's `r1.c3.dataset.build_from_sweep` (featurizer v3) | the builder of `ab79b4ce` (featurizer v2), run in `python -I -B` (no bytecode written, in the harness or anywhere) from a throwaway `git clone --shared` checked out at `ab79b4ce` (objects shared; nothing written to the paper repo); the child refuses unless `FEATURIZER_VERSION` is `c3_features/v2` and every loaded `r1.*` module comes from that checkout, and reports its git head, which must be `ab79b4ce` |
| proposals, configs | byte-identical to the sealed files | the same |
| `build.json` | equal with `commit` dropped | equal with `commit` dropped and `classification.path` normalized: the replay's classification file must be `<paper root>/results/r1/evidence/C3_sweep_classification_20261028.json` (the R1-SWEEP1-CLASSIFY sidecar), the sealed path must be absolute and end with that same repository-relative path, and every other classification field, its `sha256` included, must be equal |

The child runs in the caller's working directory, so a relative index path is recorded as in the sealed `build.json`
(the diagnosis: `sweep_index.path` is relative in both records). It needs `git` and commit `ab79b4ce` in the
release checkout's object store (an ancestor of `main`; a full, not shallow, clone).

The builder of `ab79b4ce` imports the harness: the sweep's noise source makes its sweep sources import
`r1.headroom.e1b_collect`, which needs `$AR_HARNESS_ROOT/src`. The throwaway checkout has no sibling harness, so the
parent passes the root main's own replay would use. The release must therefore run with `AR_HARNESS_ROOT` set to the
audited harness, as on 22 Nov, or from a checkout with the harness as its sibling.

Failures are typed: environment and builder-internal failures (no harness, a failed or unclean checkout, a builder
that crashes or times out, a wrong featurizer or git head, bytecode writing enabled) raise `RuntimeError`; identity
mismatches (tables, `build.json`, classification, pin, scratch capacity, and a `ValueError` from the builder's own
source-data checks, which the child reports with exit code 3) raise `ValueError`. Since `release.py` reports a failing check by
exception type, a STOP shows which kind it is. New time limits: 300 s for each git step of the checkout and 7,200 s for
the child build; the original replay had none.

The steps after the replay (plan comparison, completion, role-block re-derivation) run with main's `audit.py`, which has
changed since `ab79b4ce`, and have not yet run on the sealed sweep-1 table. A further STOP there is possible; it fails
safe and is not caused by this unit.

## Tests (`r1/tests/test_c3_sweep1_release_compat.py`, 12)

On a synthetic builder repository with a v2 and a v3 commit whose `budget_frac_left` differs after a skipped proposal,
a "sealed" table built by v2 at a `/ceph`-like paper root, and a `/work`-like release root:
- **without the fix**, the unchanged `audit._verify_replay` refuses with main's v3 builder ("differs … proposals.jsonl")
  and, with the v2 builder, on `build.json` ("build metadata differs"): the two gates of the diagnosis;
- **with the fix**, the replay passes at the release root and at the audit's own root, and main's builder is never
  called;
- tampered proposals or configs, other classification bytes, the same bytes at another repository path, a
  classification outside the paper root, any other `build.json` field, a table not built at the pinned commit, a builder
  of another featurizer and a missing sidecar are all refused;
- the child gets `AR_HARNESS_ROOT` from the parent's resolution, not by inheritance, and runs with `-B`; a replay
  leaves no bytecode in the (fake) harness or the checkout; with no harness the replay stops with `RuntimeError` before
  any build; the synthetic builder, like the real one, fails without a harness and imports a module from it;
- a source-data refusal inside the builder (its own `ValueError`) stays a `ValueError`;
- the scratch check adds the checkout's size (refused at one byte short, passed at the exact amount);
- the classification path must be the R1-SWEEP1-CLASSIFY sidecar, and the sealed path absolute;
- `sweep1_integrity` installs the replay only for its check and restores it (also on failure); `sweep2_integrity` is
  unchanged and uses the original replay;
- in this repository, `ab79b4ce`'s builder imports in the isolated interpreter with featurizer v2, its own git head,
  and every `r1` module from the throwaway checkout, without writing bytecode; with a harness available (skipped
  otherwise), its `r1.headroom.e1b_collect` imports with the parent's harness root and no `.pyc` file in the harness is
  added or rewritten (paths, sizes and mtimes compared).

`test_c3_release.py` (41) passes unchanged; with this file, 53 passed.

## Then

The change is inert until published: `release.py` refuses a `release_checks.py` that differs from `origin/main`, and
each receipt records its sha256. After the merge, the cluster agent reruns the sweep-1 train/dev release under
R1-S2-LABELS-TRAINDEV-RELEASE, from the same working directory and with the same index and classification arguments
as the refused run, with `AR_HARNESS_ROOT` exported to the audited harness. If the replay still refuses, it is a STOP with the exception type, as before; the diagnosis
predicts a pass (a v2 replay reproduced the sealed proposals and configs byte for byte).
