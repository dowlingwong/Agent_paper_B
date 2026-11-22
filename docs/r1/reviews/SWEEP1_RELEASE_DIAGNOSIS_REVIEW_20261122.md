# Independent review — sweep-1 train/dev release refusal diagnosis and fix decision (22 November 2026)

Reviewer `reviewer-sweep1-diag`, independent and read-only (did not write the reviewed unit; this file is the only
write). Reviewed: branch **`sweep1-diag-20261122` @ `70861b81`**, report
`docs/r1/reports/release_20261122/SWEEP1_RELEASE_DIAGNOSIS_20261122.md` (72 lines), against published main
`origin/main` = `dc9ad88a` (= the report's "current remote main"; no movement during the review).

**Method.** Read-only git lineage in the review worktree; read-only `ssh deepthought` (`ls`/`stat`/`sha256sum`/`cat`/
JSON metadata, no writes, no jobs, no git writes); and two **independent rebuilds into `/tmp`** on the reviewer's
machine, using the pinned sweep index (`812468e2…`), classification sidecar (`bb6d891c…`) and the audited harness
(`6adf3859…`): (a) the current checkout's code (v3) and (b) an extracted `git archive ab79b4ce` tree (v2). No
`label_block.jsonl`, `evaluation_block.jsonl` or `runs.jsonl` was opened. I read only the sealed table's three files,
the two sweep source directories/manifests, the B.2 audit's `environment.json`/`evidence_completion.json` (metadata,
no values), the audit-review files, and the diagnosing agent's own replay output left in deepthought `/tmp`.

## Bottom line

**NOT ACCEPTED.** The refusal diagnosis, the sealed-table provenance, the v2/v3 identification and the 116-record
difference are all independently confirmed. But the recommended fix is **incomplete in a way that matters**: the
sweep-1 integrity check has a **second, independent failure gate after the proposal comparison**, which the report
does not mention. Option A as described ("change only `r1/c3/release_checks.py` so the check runs the feature builder
at `ab79b4ce`") will therefore still be refused — now with `ValueError: evidence build metadata differs from full
source replay` — because the rebuilt `build.json` records the release's `classification.path` while the sealed
`build.json` records the B.2 audit root's. I demonstrated this with a v2 builder replay that reproduces the sealed
`proposals.jsonl`/`configs.json` byte-for-byte (`b713c423…`/`b585b727…`) yet fails the next comparison. Minor: the
"15 apparent extra field diffs" figure is not reproducible.

## Major finding (blocking for the fix decision)

`audit._verify_replay` (`r1/c3/audit.py:508-534`; byte-identical at the release run commit `f93264fc` and at
`dc9ad88a` — `git diff f93264fc dc9ad88a -- r1/c3/audit.py r1/c3/release_checks.py r1/c3/dataset.py
r1/c3/features.py` is empty) does two things after a byte mismatch is ruled out:

1. it compares `proposals.jsonl` and `configs.json` bytes (the gate that refused the release);
2. **it then compares the freshly written `build.json` to the table's `build.json`, removing only `commit`**:

```python
rebuilt_meta.pop('commit', None); existing_meta.pop('commit', None)
if rebuilt_meta != existing_meta:
    raise ValueError('evidence build metadata differs from full source replay')
```

The rebuilt `build.json` records `classification.path` as the **absolutised `--classification` argument** and
`sweep_index.path` as the **index argument as passed** (`dataset.build_from_sweep` → `_write_table`; index path only
depends on how the caller passes it). The sealed table was built at the B.2 audit root, so its `build.json` has:

- `classification.path` = `/ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z/paper/results/r1/evidence/C3_sweep_classification_20261028.json`
- `sweep_index.path` = `results/r1/pilot/C3_sweep_index_20261028T033315Z.json` (relative)

The release step was run with the same paper root as sweep 2 (`/work/dwong/s2_audit_20261122/paper`, per
`S2_TRAINDEV_RELEASE_20261122.md` "same paper-root"). The replay output left in deepthought `/tmp` during the
diagnosis (consistent with the report's described replay; `/tmp/replay_main_s1/build.json`, `commit` `dc9ad88a`)
records:

- `classification.path` = `/work/dwong/s2_audit_20261122/paper/results/r1/evidence/C3_sweep_classification_20261028.json`
- `sweep_index.path` = `results/r1/pilot/C3_sweep_index_20261028T033315Z.json`

With a v2 builder under that same invocation the proposals/configs bytes become the sealed ones (verified), but the
metadata comparison differs in exactly one field: **`classification.path`** (`/work/…` vs `/ceph/…`). I checked this
both ways:

- v2 replay (`git archive ab79b4ce`, release-style invocation) → proposals `b713c423…`, configs `b585b727…`; rebuilt
  `build.json` vs sealed `build.json` (commit popped) → 1 differing field, `classification.path`;
- exercising the **unmodified** `audit._verify_replay` with the v2-built table (only the platform-only `findmnt`
  probe in `_local_scratch_mount` patched; no data/identity code touched) → `ValueError | evidence build metadata
  differs from full source replay`.

`dataset.evidence_classification` (`r1/c3/dataset.py:267-274`) requires both the sidecar and the index to be inside
`--paper-root`; so with the release paper root (`/work/…/s2_audit_20261122/paper`) the rebuilt `classification.path`
can never be the sealed `/ceph/…/paper/…` path, and passing the `/ceph` sidecar instead fails the "inside repository"
test. `sweep_index.path` additionally depends on whether the index is passed relative (as in the recorded invocation)
or absolute (as the sweep-2 command line shows).

**Consequence for the decision.** Option A's *direction* is right and the sealed table *can* be reproduced by its
producing code (I verified that; the report only inferred it from `build.json`). But "change only the feature builder"
does not make the release pass: the same check refuses one gate later. Completing A needs an explicit, reviewed
decision on the build metadata — for example (i) run the sweep-1 integrity replay with the B.2 audit root as
`--paper-root` **and** cwd so both recorded path fields reproduce the sealed ones (then `evidence_classification`
and `_verify_published` validate against that root's `origin/main` `de3de54f`, which is itself a decision), or
(ii) have `release_checks.py` derive/override the paper root and cwd, or (iii) normalise the two invocation-path
fields in the metadata comparison — which edits `audit.py`, is outside REL-CODE A ("integrity checks live in
`r1/c3/release_checks.py`") and outside `release.py`'s `PUBLISHED_PATHS`-must-equal-main rule, and is a (small)
relaxation of the check the report says it does not relax. The report must diagnose this second gate and state which
route is chosen; otherwise the author is told a fix will release sweep 1 when it will be refused again.

I could not run the whole `verify_evidence_completion` here without opening the sealed label/evaluation blocks (it
reads them); `_verify_replay` is the gate that refuses today and the one that will refuse next, so the demonstration
is on it. The failure is reproducible on the release host (where `findmnt` exists) with the v2 builder and the same
invocation.

## Minor findings

1. **"15 apparent extra field diffs" is not reproducible.** Under a plain parsed-JSON `!=` comparison the NaN≠NaN
   artefacts are **780 field-level mismatches** (`last_key_delta_z` 491, `last_key_kept` 229,
   `new_num`/`old_num`/`log_ratio`/`direction` 15 each) in 607 records that compare unequal; 491 of those differ
   *only* because of NaN and 116 also carry the real `budget_frac_left` difference. Not 15. The substantive claim —
   with NaN==NaN, the only differing field is `features.budget_frac_left` — is correct. State the comparison used or
   correct the number.
2. **Option C is not merely "weaker".** A field-level exception at the proposal comparison still leaves the
   build-metadata gate; C also fails under the recorded invocation unless the same invocation/metadata decision is
   made. As written the report presents C as a viable-but-weaker alternative.
3. **"Change only `release_checks.py`"** — the replay lives in `audit._verify_replay`, reached through
   `audit.verify_evidence_completion`, so pinning the feature builder needs a compatibility module/monkeypatch (the
   report's parenthetical hints at this) and the metadata gate is not reachable from `release_checks.py` without
   changing the invocation. The wording should say what "only" covers.
4. **Authority wording.** R1-SWEEP2-RELEASE-DECISIONS already records REL-CODE A (a reviewed edit to
   `release_checks.py` does not void earlier receipts); "requires an author row/independent review" should say which
   is needed — an independent review is; a new author row may not be.

## Confirmed claims (evidence)

| Claim | Verification |
|---|---|
| Sealed table `/ceph/…/b2-ab79b4ce-20261119T002306Z/table`, `build.json` `commit` `ab79b4ce`, proposals `b713c423…`, configs `b585b727…`, `n_proposals` 4999, `replay_checks` 288 entries | `sha256sum` on deepthought: `proposals.jsonl` `b713c42338c42cea6991ee8ac8e598183fc79c22aeef6a2e8539c7f971dd57c4` (4,999 lines), `configs.json` `b585b72758668a17c65b842c204e3c08253ee6c7af92c34c9a8bc8b4a53882df`, `build.json` `c14a68ae…`; `replay_checks` dict = 288 ledger entries, totals rows 5,813 / proposals 4,999 / skipped_invalid 526 / zero-delta 0 / repeat-metric 0; `n_configs` 302 |
| B.2 audit commit lineage `ab79b4ce` | The B.2 audit's `output/environment.json` records `paper_code_commit = ab79b4ce…`, harness `6adf3859…`, `paper_code_clean: true`, review `docs/r1/reviews/B2_PACKAGE_ORIGIN_REVIEW_20261118.md`; `output/evidence_completion.json` is schema `r1.c3_audit_completion/3` with `proposals_sha256` `b713c423…` and `build_sha256` `c14a68ae…`; `B2_AUDIT_RUN_REVIEW_20261119.md` independently accepts the run at `ab79b4ce` |
| Code that produced the table is featurizer **v2** | `git show ab79b4ce:r1/c3/features.py`: `FEATURIZER_VERSION = "c3_features/v2"` (l.239), `"budget_frac_left": 1.0 - (b - 1) / ctx.runs_total` (l.387) |
| Main `dc9ad88a` is **v3**, `1 − worker_runs_used/runs_total`; `81924e14`, `6b779fe3`, `5db5b67d`, `3ce2c8b7` ancestors and W2-reviewed | `git show dc9ad88a:r1/c3/features.py`: `FEATURIZER_VERSION = "c3_features/v3"` (l.244), `1.0 - self.worker_runs_used / ctx.runs_total` (l.433); all four commits are ancestors; `git log ab79b4ce..dc9ad88a -- r1/c3/features.py` returns exactly those four; W2 v3 reviews `W2_V3_REBUILD_REVIEW_20261115.md` (ACCEPT) and `W2_V3_PROMPT_REVIEW_20261114.md` (accepted) |
| No other commit in `ab79b4ce..dc9ad88a` changes sweep-1 proposals | Only `6e872386` touches `dataset.py` in that range; a current-code replay (which includes it) reproduces the pre-`6e872386` W2 v3 rebuild table `d0048567…` exactly, so it does not change proposals |
| Same 4,999 keys, same order; **116 records differ, only `features.budget_frac_left`** | v2 replay vs v3 replay (both rebuilt): identical `(node, proposal_id)` sequence; NaN-aware comparison: 116 differing records, one field; 14 ledgers, all `…_append_only_summary`; first differing line 31 = `c3_20261028T033315Z_append_only_summary:digits_mlp__s114:t020` |
| Quoted value pairs, `configs.json` byte-identical, no data difference | The five rounded pairs in the report all occur ((0.05,0.4), (0.05,0.1), (0.15,0.2), (0.30,0.35), (0.35,0.40)); configs `b585b727…` in both; source directories byte-identical between the B.2 root, the `/work` checkout and the diagnosis checkout (sorted file-list sha256 tree hashes `bb29b8db…` and `bc54a2db…`, 436 files each; manifests `f18f8a8b…`/`50530673…`); index `812468e2…` = `analysis_guard.SWEEP1_INDEX_SHA`; classification `bb6d891c…` |
| Refusal genuine and not bypassed | `release.py` catches any exception from the registered check, records only its type and raises `ReleaseStop`; `sweep1_integrity` → `audit.verify_evidence_completion` → `_verify_replay`; my v3 rebuild gives `d0048567…` ≠ sealed `b713c423…` → the same `ValueError`; the relevant modules are byte-identical at the release commit `f93264fc` and at `dc9ad88a`; no sweep-1 output/receipt exists |
| No label/evaluation value opened | `build_from_sweep`/`_verify_replay` never open a label/evaluation block; the diagnosis replay left on deepthought (`/tmp/replay_main_s1`) holds only `proposals.jsonl`, `configs.json`, `build.json`; the report contains only hashes/counts. (I did not open any sealed block either.) |
| Report ready to push | `70861b81` is on `dc9ad88a`, adds **only** the report (72 lines); worktree clean, branch 1 commit ahead of `origin/main` = `dc9ad88a` (no movement during the review) |

## Disposition

Revise the diagnosis to cover the full `_verify_replay` failure path (proposals **and** the build-metadata equality),
then re-issue the fix decision with the metadata/invocation decision explicit and re-review. The remainder of the
report is sound and does not need rework.

**Round-1 verdict: NOT ACCEPTED** (superseded by Round 2 below).

## Round 2 — revised report @ `0be2e93d` (22 November 2026)

**Reviewed:** `sweep1-diag-20261122` @ `0be2e93d` (one commit on top of the reviewed `70861b81`). It changes only
the diagnosis report and adds this review file (`git diff --name-only 70861b81 0be2e93d` = the two `docs/` files);
no `r1/`, PLAN, table, audit or data change; worktree clean; `origin/main` is still `dc9ad88a` (branch 2 commits
ahead). I re-ran the checks the round-1 review asked for and re-verified the new claims.

### Round-1 blockers — all resolved

| Round-1 finding | Status | Evidence in the revision |
|---|---|---|
| Missing second gate (`_verify_replay` build-metadata compare) | **resolved** | The new "Second gate" section states it correctly: after the proposals/configs bytes, `_verify_replay` compares the rebuilt `build.json` to the sealed one with only `commit` removed; sealed `classification.path` is the B.2-root `/ceph/…/paper/…` path; a replay under `/work/…` records the `/work` path; `evidence_classification` forces sidecar/index inside `--paper-root`; a v2 builder replay matches proposals/configs byte-for-byte (`b713c423…`/`b585b727…`) but stops at `ValueError: evidence build metadata differs from full source replay`. This matches my independent reproduction (v2 replay from `git archive ab79b4ce` + unmodified `_verify_replay`; only the macOS `findmnt` probe patched, which the report discloses). |
| Fix decision must include the metadata/rooting decision | **resolved in its primary form** | Option A now = builder at `ab79b4ce` **plus** a reviewed path-normalised build-metadata comparison, with the change in `audit.py` and/or `release_checks.py`, independent review, and no relaxation of the proposals/config identity or recorded sha256 fields. |
| NaN accounting | **resolved exactly** | Revised text matches my measurement: NaN-aware → only `budget_frac_left`; naive `!=` over parsed JSON → 607 records unequal, 491 NaN-only (`last_key_delta_z`, `last_key_kept`, …); substantive set 116 records / one field. |
| Option C second gate | **resolved** | Now says C also needs the metadata gate bypassed/normalised and "by itself it does not pass the second gate". |
| "change only `release_checks.py`" wording | **resolved** | Now `r1/c3/audit.py` and/or `r1/c3/release_checks.py`. |
| REL-CODE A / author-row wording | **resolved** | Now independent review under the existing REL-CODE A mechanism, no new author row necessarily. |

### New finding (blocking): the "or equivalently root the replay at the B.2 audit root" branch is not viable as stated

Option A offers the normalised comparison "or equivalently root the replay at the B.2 audit root so the recorded
paths match". With `--paper-root` = the frozen B.2 attempt root, the check fails **before** `_verify_replay`:

- the B.2 root (`/ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z/paper`) has `HEAD` `ab79b4ce` but its local
  `refs/remotes/origin/main` is `de3de54f`, while the live remote main is `dc9ad88a` (read-only check:
  `git ls-remote origin refs/heads/main` = `dc9ad88a`). `evidence_plan` calls
  `dataset.evidence_classification(index, paper_root, classification)` **before** `_verify_replay`, and
  `evidence_classification` → `_verify_published` requires
  `git rev-parse refs/remotes/origin/main == ls-remote origin refs/heads/main`, else raises
  `origin/main is stale or missing; fetch before evidence use`;
- even after a fetch, `_verify_published` compares the root's working-tree authority bytes against remote main: the
  B.2 working tree's `docs/r1/PLAN.md` is the preserved `de3de54f`-era overlay (the B.2 review verified it
  byte-identical to `de3de54f`), while current main `dc9ad88a` adds 113 lines to `docs/r1/PLAN.md` (the other three
  checked paths — authorization, index, classification sidecar — are unchanged) → mismatch;
- `build_from_sweep` itself calls `sweep_replay_inputs` → `evidence_classification(paper_root)`, so "root only the
  builder at B.2" hits the same published check unless the code bypasses/overrides it. Making the frozen root usable
  would require fetching it **and** updating its docs overlay — altering the preserved audit root (a provenance
  decision the report does not mention).

So the "equivalently" clause should be struck or replaced with "or a reviewed override that supplies the sealed
`classification.path`/`sweep_index.path` to the metadata comparison while keeping the current paper root". The
recommendation (A) itself is unaffected — its primary (normalised-comparison) form is sound and is the only viable
route as written.

### Other minors (non-blocking)

1. `_verify_replay` is lines **508–532**, not 508–534 (line 532 is the metadata raise; 533–534 are blank).
2. `sweep_index.path` is not absolute: it is the index argument as passed. Under the recorded invocation (relative
   index) it is `results/r1/pilot/…` in both the sealed and rebuilt records, so the actual differing field is
   `classification.path` (it would also differ only if an absolute index path were passed). The "invocation-dependent
   absolute paths … (and likewise `sweep_index.path`)" wording should be tightened.
3. An `audit.py` edit is beyond the literal REL-CODE A text (which covers `release_checks.py`); the revision says
   "`audit.py` and/or `release_checks.py`", so if `audit.py` is touched the review of the code change should state the
   authorization basis explicitly and consider whether the audit's own `verify` path should change semantics; the
   normalisation is safer implemented in the release path.
4. Re-verified for the post-gate checks: the B.2 addendum (`e9deba63…`), the B.2 package-origin review
   (`dd31b3d6…`) and the `R1-B2-GO` PLAN row (`ops-e1-replay-amend-20261117`, `52992b22`, `B6 (a)`/`B4 (a)`/`B1 (a)`)
   are all present and byte-identical on current main `dc9ad88a`, so the environment/addendum/review inputs the rest
   of `verify_evidence_completion` needs would be available under the current paper root. (The label/evaluation
   role-block re-derivation still cannot be exercised without opening the sealed blocks.)

### Pushability

`0be2e93d` touches only `docs/` (the report and this review) — no code change was made; `origin/main` is still
`dc9ad88a`; the branch is 2 commits ahead and the worktree is clean. Mechanically it is pushable; content-wise the
B.2-root "equivalent" clause should be corrected first, and this round-2 append needs committing.

VERDICT: NOT ACCEPTED
