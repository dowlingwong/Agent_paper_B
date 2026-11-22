# R1-SWEEP1-RELEASE-COMPAT option A — reviewed implementation unit (22 November 2026)

## What changed (code; sweep-1 release path only)

- `r1/c3/sweep1_compat.py` (new): `rebuild_v2_table()` extracts the **exact ab79b4ce tree** with `git archive` into
  a temporary directory and runs its `dataset.build_from_sweep` in an isolated subprocess
  (`PYTHONPATH=<v2 tree>`, `cwd=<v2 tree>`, current interpreter, inherited `AR_HARNESS_ROOT`). The running main
  checkout's v3 `r1.c3.dataset` is never imported by the compatibility replay. Absolute/`..` archive members are
  refused; the remaining internal symlinks are accepted only through `tarfile`'s `data` filter.
- `r1/c3/audit.py`: `_verify_replay`, `evidence_plan` and `verify_evidence_completion` gain an optional
  `replay_builder` hook used **only** by the sweep-1 release path. Default behaviour (sweep 2 and every other
  caller) is unchanged. On the compatibility path the invocation-root fields `classification.path` and
  `sweep_index.path` are treated as provenance and removed before the build-metadata comparison; their sha256
  values remain, and the classification file is additionally checked byte-for-byte against the sealed
  `classification.sha256`. Proposals/configs bytes, table/binding/identity checks, role blocks, completion record,
  addendum, review and all other gates are unchanged.
- `r1/c3/release_checks.py`: `sweep1_integrity` passes `sweep1_compat.rebuild_v2_table` as the replay builder inside
  `integrity_context`; `sweep2_integrity` is untouched.
- `r1/tests/test_c3_release.py`: the wrapper test now asserts the compatibility builder is wired in.

## Tests (run on deepthought, CPython 3.13 env)

`pytest -q r1/tests/test_sweep1_release_compat.py r1/tests/test_c3_release.py` → **46 passed, 0 failed**.

- `test_default_builder_refuses_v3_table`: without the compatibility hook, a v3-builder replay of the v2 table is
  refused (`evidence table differs from full source replay`) — the refusal reproduces.
- `test_compat_accepts_v2_table_with_work_root_provenance`: the real metadata pattern (v2 table build, `/work`
  invocation root, sealed-style `/ceph` classification path) is accepted when the v2 builder and provenance
  normalization are used.
- `test_compat_refuses_tampered_proposals`, `..._configs`, `..._classification_bytes`: tampered proposals or
  configs, or a classification file whose bytes no longer match the sealed sha256, are refused.

**Real-data check (read-only):** calling `release_checks.sweep1_integrity` on the actual sealed sweep-1 B.2 table
and audit now **PASSES** (before the fix it refused). Exact inputs/invocation:

```
release_checks.sweep1_integrity(
  table_dir="/ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z/table",
  audit_dir="/ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z/output",
  paper_root="/work/dwong/s2_audit_20261122/paper",
  index=".../paper/results/r1/pilot/C3_sweep_index_20261028T033315Z.json",
  classification=".../paper/results/r1/evidence/C3_sweep_classification_20261028.json")
```
completion bindings: proposals `b713c423…`, build `c14a68ae…`, classification `bb6d891c…`, index `812468e2…`;
**returned `completion_sha256 = e28bee5e…`**. The check opens and re-derives the audit's `label_block.jsonl` and
`evaluation_block.jsonl` inside the §6 integrity carve-out (that is the release step's normal behaviour); **no label
or evaluation value is returned, printed or recorded**, and the sealed table/audit/role blocks were not modified.
The release step itself cannot be run from this branch: `release._published_clean` will STOP until `audit.py`,
`release_checks.py` and `sweep1_compat.py` are merged to `origin/main`; the actual release reruns after that merge
under R1-S2-LABELS-TRAINDEV-RELEASE.

## Authority record for the audit.py hook (reviewer B3)

R1-SWEEP1-RELEASE-COMPAT says the reviewed change is "in `r1/c3/release_checks.py` (or its replay wrapper) under
REL-CODE A". The implementation keeps the published release code untouched and puts the compatibility seam in
`r1/c3/audit.py` (`_verify_replay`/`evidence_plan`/`verify_evidence_completion` optional `replay_builder`), called
from `release_checks.sweep1_integrity`; that seam is the "replay wrapper" named by the row. The change also
normalises `sweep_index.path` in addition to `classification.path`: the release invocation passes an absolute index
while the sealed build record holds the relative index, and `sweep_index.sha256` is still checked, so both
invocation roots must be normalised together. The row does not name this second path explicitly. If the author reads
REL-CODE A as limited literally to `release_checks.py`, a short confirmation/row is needed before merge; otherwise
this section is the recorded basis. No `release.py` and no `PUBLISHED_PATHS` entry was changed.

## Unit 2 — arms readiness on both sources with one featurizer

- Sweep-1 release table carries **v2** features (built ab79b4ce): `budget_frac_left = 1 − (b−1)/runs_total`.
- Sweep-2 table carries **v3** features (W2): `budget_frac_left = 1 − worker_runs_used/runs_total`.
- The only difference between the two sources' proposal features is that one field, for **116 of 4,999** sweep-1
  proposals; configs and every other feature field are identical. Sweep-2 has no v2 counterpart.
- **Recommendation for arms trained on both sources: use one featurizer, v3, for both.** Keep the sealed release
  table (v2) untouched; at arms-training time derive the sweep-1 feature view deterministically as v3 by
  recomputing `budget_frac_left` from the source ledger's worker-run accounting, and use it for the 116 affected
  sweep-1 proposals while all other rows/fields pass through unchanged. The derivation must be a named script or
  derived-feature artifact (with sha256) recorded in the arms record, and the count should be stated in the arms
  eligible population (not just 116/4,999). Sweep-1-only arms and sweep-2-only arms are unaffected; labels and
  proposal identities are unchanged.
- Wording note: the statement above is about the two sources' **proposal feature vectors**; the table-level
  `build.json`/release provenance differs for other reasons and is not an arm feature.
- Not recommended: train on a mixture of v2 and v3 budget fields (inconsistent featurizer), or rebuild/re-audit the
  sealed sweep-1 table just to change a feature (it would replace the B.2 provenance). If a single v3 view cannot be
  produced for a particular arm, exclude/flag the 116 affected sweep-1 proposals rather than silently mixing
  versions; this is an author decision to record.
