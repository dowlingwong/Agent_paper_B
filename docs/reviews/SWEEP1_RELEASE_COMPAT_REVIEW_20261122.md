# Independent review — R1-SWEEP1-RELEASE-COMPAT option A implementation unit (22 November 2026)

**Round status:** round 1 (below) is NOT ACCEPTED; **round 2 (revised unit @ `9ebd9d90`) is appended at the end and is the final, accepted review** — its final line supersedes the round-1 verdict.

Reviewer: `reviewer-rel-sweep1-compat`, independent and read-only. I did not write the reviewed unit and did not
start or stop a job. This file is the **only** write. deepthought/ceph were accessed read-only over ssh
(`ls`, `stat`, `sha256sum`, `git rev-parse/log/status/diff/show`, JSON metadata parsing). I did **not** modify,
create or delete anything under `/ceph`, `/work` or either worktree; the sealed table/audit mtimes and hashes are
unchanged after this review (checked before and after). One execution was done on deepthought: the reviewed
sweep-1 integrity check itself (`release_checks.sweep1_integrity`) on the real sealed inputs, to reproduce its
PASS. That check establishes the release **integrity carve-out** (`integrity_context`) and, as designed, opens
and re-derives the sealed label/evaluation role blocks; **no label or evaluation value was printed, copied, kept
or is published in this file**, only the returned hashes/counts. This is disclosed because the reviewed report's
wording on that point is one of the findings below (B2). Review date 2026-11-22 (Europe/Berlin).

**Reviewed unit.** Branch **`rel-sweep1-compat-20261122` @ `6f713ede`** (pushed; `origin/main` = `1402f466`,
unchanged; base `1402f466`; 4 commits; worktree clean; `git diff --name-status 1402f466..HEAD` = the report, two
new files and three edited files, nothing else). Implementation worktree on deepthought
`/work/dwong/rel-sweep1-compat-20261122` @ `b2b7489a` — `git diff --stat b2b7489a 6f713ede` is the report
only, so code tested there is the reviewed code. Report
`docs/r1/reports/release_20261122/SWEEP1_RELEASE_COMPAT_20261122.md` (52 lines) reviewed against the accepted
diagnosis (`SWEEP1_RELEASE_DIAGNOSIS_REVIEW_20261122.md`, final VERDICT ACCEPTED) and the author row
`R1-SWEEP1-RELEASE-COMPAT` in PLAN §10 (`docs/r1/PLAN.md:1429`; REL-CODE A at :1366).

## Bottom line

**NOT ACCEPTED — three blockers (B1 code/pinning, B2 report accuracy, B3 authority record), no defect found in the
verification logic itself.** The compatibility replay works: I independently reproduced the byte-identical v2
replay of the sealed sweep-1 table and I reran the full `release_checks.sweep1_integrity` on deepthought — it
**PASSES** (`completion_sha256 e28bee5e…`, proposals `b713c423…`, build `c14a68ae…`). The metadata
normalisation is exactly sufficient (only the two invocation-root path strings and `commit` differ) and is safe
(identity is still carried by the recorded/checked sha256s). The 46-test result reproduces (46 passed, 20.8 s).
Sweep 2, the default path, the proposals/configs byte compare, the completion record and every data/identity
check are unchanged; there is no main push. The blockers are: the new module the release step now executes is
not covered by the release step's own published-code guard; the report states something about label/evaluation
access that the check does not satisfy as written; and the report does not record the authority basis for the
`audit.py` relaxation (and for normalising `sweep_index.path`, which the author row does not name). Each fix is
small; details and required changes below.

## BLOCKERS

### B1. The new module the release step executes is not covered by the release step's published-code guard

`release.py` refuses to run unless HEAD's `PUBLISHED_PATHS` equal `origin/main`'s and the modules it runs are the
plain modules beside it — `PUBLISHED_PATHS` (`r1/c3/release.py:471-472`) contains PLAN, prereg, `release.py`,
`release_checks.py`, gate, builder, split, `p3_split.py`, **`audit.py`, `dataset.py`, `analysis_guard.py`** — and
`_published_clean` (`:475-499`) additionally pins the imported `analysis_guard`/`audit`/`dataset`/`p3_split`
module files. The reviewed change adds **`r1/c3/sweep1_compat.py`**, which `sweep1_integrity`
(`r1/c3/release_checks.py:30,35`) imports and executes inside the integrity carve-out, and it is in **none** of
those lists. So the release's contract ("the code the release runs equals `origin/main`'s", release.py:19-23,
36-38) no longer covers code it runs: a checkout that is `origin/main` + a committed change to `sweep1_compat.py`
only would pass `_published_clean` (uncommitted edits are caught by the dirty check; a *committed, unpublished*
change to the new file is not) and the release would run unpublished logic that chooses the builder commit,
extracts it and normalises the build metadata. The precedent is explicit: `sweep2_batch.py` is handled by a
dedicated `_sweep2_batch_published()` in `release_checks.py` (`:41-56`) for exactly this reason. The omission is
an oversight of the same kind, and it is in the reviewed unit's write scope.

**Required fix.** Add the analogous guard in `r1/c3/release_checks.py` and call it from `sweep1_integrity` before
the carve-out — module file is `here / "sweep1_compat.py"`, `git diff --quiet refs/remotes/origin/main HEAD -- r1/c3/sweep1_compat.py`
is empty, and no tracked modification (same shape as `_sweep2_batch_published`), plus a test. **Do not** add the
file to `PUBLISHED_PATHS` instead: that edits `release.py`, whose bytes at the row's release-code commit
`a9d8ff5e` bind the release step (`release_row(..., writing=True)`, `release.py:320-352`); `release.py` is
byte-identical at `a9d8ff5e` and at the current main `1402f466`, so editing it would STOP
"the running release.py is not the one the row cites" without a new/amended author row. The `release_checks.py`
route is within REL-CODE A and needs no release-row change.

### B2. The report's label/evaluation-access statement is false as written; the real-check record also lacks the invocation

Report lines 33-36: "**Real-data check (read-only):** … No label or evaluation value was opened by this check; the
table/audit were not modified." The second clause is verified (sealed table/output mtimes and sha256s unchanged;
repository untouched). The first is not: the check this unit runs is
`audit.verify_evidence_completion`, which **opens, parses and compares** `label_block.jsonl` and
`evaluation_block.jsonl` (it re-derives both role blocks from the raw seed results and hashes the blocks —
`r1/c3/audit.py:1435-1439`, `_completion` at `:977-978`), exactly as `release.py`'s own docstring states
(release.py:26-30: "`audit.verify_evidence_completion` opens `runs.jsonl` and `evaluation_block.jsonl`; … only
inside the release step's integrity check"). That is the *authorised* behaviour inside the carve-out — but the
report must not say the blocks were not opened. In this project the PRE-STAGE A label/evaluation discipline is a
governance statement; an inaccurate record of block access must be corrected before publication.

**Required fix (report).** Replace with the exact statement, e.g.: "The check ran inside the release integrity
carve-out and, as designed, opened and re-derived the sealed label and evaluation role blocks; it returns only
pass/fail, counts and hashes — no label or evaluation value was returned, printed, recorded or used, and the
sealed table/audit were not modified." Also record the actual real-check invocation (`cwd`, interpreter,
`AR_HARNESS_ROOT`, absolute `--table/--audit/--paper-root/--index/--classification`, and the returned
`completion_sha256`) so the PASS is reproducible, and state that `index`/`classification` are the published-main
copies under the release paper root (`/work/dwong/s2_audit_20261122/paper`, sha256 `812468e2…`/`bb6d891c…`, equal
to the sealed record's values), not the sealed `/ceph` sidecar paths (which `evidence_classification` refuses
outside its `--paper-root`). Finally, the report should state the sequencing this code implies: the release step
cannot run from this branch — `_published_clean` compares `audit.py`/`release_checks.py` to `origin/main`, so the
release must run from a clean checkout at the merged main after an author main-push decision (`_published_clean`
would STOP "not published" on the branch today). The direct check run is evidence, not the release step.

### B3. Authority basis for the `audit.py` relaxation, and for normalising `sweep_index.path`, is not recorded

The accepted diagnosis review's round-3 text required: "if `r1/c3/audit.py` must change, that is beyond the
literal REL-CODE A text and needs its own explicit authorization basis" (REL-CODE A is defined as "integrity
checks live in `r1/c3/release_checks.py`; a reviewed edit there does not void earlier receipts",
`docs/r1/PLAN.md:1366`). The implementation does edit `audit.py` — an optional `replay_builder` hook in
`_verify_replay`/`evidence_plan`/`verify_evidence_completion` plus a **relaxation of the build-metadata
comparison** (`r1/c3/audit.py:508-556`) — and the report says nothing about authority. The author row
(`PLAN:1429`) is the candidate basis: it says "as a reviewed change in `r1/c3/release_checks.py` (**or its replay
wrapper**) under REL-CODE A" and "compares `build.json` with **the classification path** normalized for
provenance". The first phrase reasonably covers the replay wrapper (`_verify_replay` is that wrapper) — but that
reading must be stated explicitly, not assumed, because REL-CODE A's literal text covers only `release_checks.py`.
The second phrase names only `classification.path`, while the code also normalises **`sweep_index.path`**; that
extension is, as it happens, *necessary* (see the evidence below: the release invocation passes an absolute index
path, so both fields differ from the sealed record), but it is a second provenance path removed from a check and
the author row does not name it.

**Required fix.** The report must state the authorization basis for the `audit.py` edit (the row's "(or its replay
wrapper)" clause) and the reason the `sweep_index.path` field is normalised as well (absolute index argument at
the release invocation; sha256 identity retained and checked). If the author/lead intends REL-CODE A literally
(only `release_checks.py`), this unit needs a short explicit author decision before merge; the code itself should
not be merged on an unstated basis. No code change is required if the basis is confirmed.

## Verified claims (independent evidence)

| Claim | Verification |
|---|---|
| Sealed sweep-1 B.2 table at `/ceph/srv/dwong/paperb/b2-ab79b4ce-20261119T002306Z/table`, build commit `ab79b4ce`, proposals `b713c423…`, configs `b585b727…`, build `c14a68ae…`, 4,999 proposals; audit `…/output`, completion `e28bee5e…`, classification `bb6d891c…`, index `812468e2…` | `sha256sum`/`stat` on deepthought (mtimes 19 Nov 01:24/01:50, unchanged before/after this review); the report states the proposals/build/classification values, and the completion hash below matches the sealed record |
| `git archive ab79b4ce` is available in the checkout; `ab79b4ce` is an ancestor of `origin/main`; repo not shallow; archive is 185,303,040 B | `git cat-file -t`, `git merge-base --is-ancestor`, `git archive ab79b4ce \| wc -c` |
| A v2-builder replay under the release invocation reproduces the sealed proposals/configs **byte-for-byte** | `/tmp/ab79_replay` (left on deepthought at 22:54 during the author's verification; release-style `/work` root, build `commit: "unknown"` from the extracted tree): proposals `b713c423…`, configs `b585b727…` — exact |
| The rebuilt `build.json` differs from the sealed one only in `commit` and the two path fields (everything else equal) | JSON flatten: 1,832 common keys; differing keys excluding `commit` = exactly `classification.path` and `sweep_index.path`. Sealed: `classification.path=/ceph/…/paper/…`, `sweep_index.path=results/r1/pilot/…` (relative); rebuilt: both absolute `/work/dwong/s2_audit_20261122/paper/…`. So **both** normalisations are required by the actual invocation, and `sweep_index.path` is not a no-op |
| The changed `evidence_plan` gate passes on the real sealed data with the real invocation | I ran `audit.evidence_plan(table, /work/…/paper, absolute index, absolute classification, replay_builder=sweep1_compat.rebuild_v2_table)` from the branch worktree on deepthought: PASS in 22.3 s; `counts={"duplicates":3274,"eligible":1725,"noops":0}`; binding proposals `b713c423…`, configs `b585b727…`, classification `bb6d891c…`, index `812468e2…` |
| **`release_checks.sweep1_integrity` on the sealed B.2 inputs PASSES** | I reran the full check on deepthought (venv python 3.13.15, audited harness, paper root at published main `1402f466`): `check="audit.verify_evidence_completion"`, `pass=true`, `completion_sha256=e28bee5e0aaa1a5bd675cc74eb69ffd65559abda0b8019716c6dfca72f8e43b4`, completion Kept fields proposals `b713c423…`, build `c14a68ae…`, configs `b585b727…`, classification `bb6d891c…`, index `812468e2…`, label/evaluation seeds 7001–7010, `schema=r1.c3_audit_completion/3`; 26.7 s. No value was printed |
| Read-only | Sealed table/audit `stat` mtimes and `sha256sum` identical before and after both my runs; `git status` clean in both worktrees; no file created under `/ceph` or `/work` (the two runs wrote only ephemeral, auto-removed `/tmp` replay directories) |
| 46 tests pass | I reran `pytest -q -p no:cacheprovider r1/tests/test_sweep1_release_compat.py r1/tests/test_c3_release.py` on deepthought: **46 passed in 20.82 s**, worktree clean after (no bytecode/cache writes). The author's `.pytest_cache/v/cache/nodeids` also records exactly 46 ids (5 + 41) with `lastfailed` empty |
| 116/4,999, one field; configs identical; same keys/order | Independent NaN-aware diff of the author's v2 replay (`/tmp/ab79_replay`) against the diagnosis v3 replay (`/tmp/replay_main_s1`): 116 differing rows, leaf diff only `features.budget_frac_left` (116), identical `(node, proposal_id)` order, configs bytes identical. Confirms the unit-2 factual basis and the diagnosis |
| v2→v3 code difference | `git diff ab79b4ce 1402f466 -- r1/c3/features.py`: v2 `FEATURIZER_VERSION="c3_features/v2"`, `budget_frac_left=1-(b-1)/runs_total`; v3 `"c3_features/v3"`, `1-worker_runs_used/runs_total` with `row_worker_runs`/`_LedgerState.worker_runs_used` accumulation; version written only to online decision records, not tables. Other v2→v3 changes in the range do not touch sweep-1 proposal fields |
| No main push, sweep 2 unchanged, no data/identity bypass | `git ls-remote origin refs/heads/main` = `1402f466…`; branch `rel-sweep1-compat-20261122` = `6f713ede` on origin; `r1/c3/audit.py` diff = only the three optional-hook/normalisation hunks; `release_checks.sweep2_integrity` untouched; default `_verify_replay` path (lazy `r1.c3.dataset` import) unchanged semantically; table sha256 check, classification/index sha256 checks, addendum/review/completion/role-block gates unchanged; `r1.c3.dataset` is imported on the sweep-1 release path only for the readers `evidence_classification`/`load_table` (v3), never for the replay build (the replay subprocess runs from the extracted v2 tree with `PYTHONPATH`/`cwd`=tree) |

## Code review

### `r1/c3/sweep1_compat.py` (new, 80 lines)

- **Does what the report says.** `git archive <ab79b4ce>` (pinned, from the checkout's own object DB) is
  extracted to a temp tree; `build_from_sweep` runs in a separate interpreter with `PYTHONPATH=tree`, `cwd=tree`,
  `-B`, `PYTHONDONTWRITEBYTECODE=1`; `AR_HARNESS_ROOT` and the rest of the environment are carried through;
  `out` must not exist; `proposals.jsonl`/`configs.json`/`build.json` are required afterwards. The replay
  subprocess cannot import the running main checkout's v3 `r1.c3.dataset`: `tree` is first on `sys.path` and the
  parent's paths are not inherited (no `PYTHONPATH` pass-through; the parent's import of the v3 readers is a
  separate, intentional reading path).
- **Extraction safety is adequate, and the residual is the right residual.** Before extraction, members whose
  name is absolute or has a `..` component are refused; `extractall(..., filter="data")` then refuses absolute
  paths, escaping/absolute links and special files and accepts the pinned tree's one internal symlink
  (`git ls-tree -r ab79b4ce` shows exactly one `120000` entry, `archive/old_b_…/pi_extensions/node_modules`;
  nothing on the replay's import path). The archive is content-addressed by the commit, so the tree is fixed
  review-published content; the defence-in-depth checks are appropriate. `filter="data"` needs the 3.13 release
  environment (pinned by the audit environment check), which holds.
- **Failure handling fails closed.** Missing commit, git failure, subprocess failure and incomplete output all
  raise `ValueError`; the release step records only the exception type. One residual: if the v2 builder fails, the
  child's traceback goes to the inherited stderr and is not in the raised message (visible in logs, acceptable); a
  stray `fatal: not a git repository` from the v2 `git_head()` fallback (extracted tree has no `.git`, so
  `commit="unknown"` is recorded and popped before comparison) is expected but noisy — see M3.

### `r1/c3/audit.py` diff vs main

- `_verify_replay(..., replay_builder=None)`, `evidence_plan(..., replay_builder=None)`,
  `verify_evidence_completion(..., replay_builder=None)`; `replay_builder` reaches `_verify_replay` only through
  `evidence_plan` (`:922`); the only production caller that passes it is `sweep1_integrity`. `_verify_replay` has
  no other production caller (`grep`); `evidence_run` (`:1228`) and `offline_eval` use the default. Default path
  imports `r1.c3.dataset.build_from_sweep` lazily and otherwise compares exactly as before (bytes, then
  build metadata with only `commit` popped) — unchanged for sweep 2 and every other caller.
- **The normalisation is minimal and exactly sufficient.** On the compat path only, `classification.path` and
  `sweep_index.path` are removed from the rebuilt and sealed metadata before the equality compare; the
  classification `sha256` is additionally re-checked against the sealed record (belt-and-braces; `evidence_plan`
  already checks `expected.sha256 == _digest(classification)` at `:913`). Nothing else in the compare is relaxed:
  the `sweep_index.sha256`, `table_sha256`, label, sources, noise/E1 and all other 1,8xx fields still compare. My
  independent replay diff shows the two path strings are the *only* non-`commit` differences, so this is neither
  over- nor under-normalisation for the observed invocation. Normalising both is **safe**: identity is carried by
  the sha256s, both of which are checked against the actual pinned files, and the classification bytes are also
  re-checked here; a false pass would require forging a preimage, not a path string.
- **Hook scope.** The hook is a general seam in a security-critical verifier; only `release_checks` passes it and
  only the reviewed builder is passed, so no bypass was found. A future caller could pass an arbitrary builder,
  but that is code-level trust, same as any other module; a comment stating "only the reviewed sweep-1 compat
  builder may be passed here" would make the intent durable (M4). No data/identity check is skipped.

### `r1/c3/release_checks.py`

`sweep1_integrity` imports `sweep1_compat` and passes `rebuild_v2_table` inside `integrity_context()`;
`sweep2_integrity` and `INTEGRITY_CHECKS` are otherwise untouched. Except for B1, the wiring is correct.

## Tests (`r1/tests/test_sweep1_release_compat.py`, updated `test_c3_release.py`)

Meaningful, not tautological, but incomplete:

- `test_default_builder_refuses_v3_table` actually exercises the default path with a monkeypatched
  `r1.c3.dataset.build_from_sweep` that emits a changed proposals file and asserts the refusal — it proves the
  default path still uses the in-tree builder (the diagnosis failure class), but it is a synthetic stand-in for
  the real v2/v3 difference (the real difference is the one field, verified separately on real data).
- `test_compat_accepts_v2_table_with_work_root_provenance` reproduces the **real metadata pattern**: sealed-style
  metadata has `classification.path=/ceph/…` and a relative `sweep_index.path`; the fake replay emits the
  `/work/…` form for both. It passes only because both paths are normalised, so it genuinely tests the change.
- `test_compat_refuses_tampered_{proposals,configs,classification_bytes}` genuinely exercise the byte compare and
  the added classification-sha256 check (the classification test exercises the defence-in-depth check directly;
  in the real path `evidence_plan` catches it first).
- The wiring test (`r1/tests/test_c3_release.py:379-395`) asserts `sweep1_integrity` passes exactly
  `sweep1_compat.rebuild_v2_table`; adequate.
- **Gap (M1):** there is no test of `sweep1_compat` itself — `grep` finds only the wiring assertion. The safe
  extraction (absolute/`..` member refusal, escaping symlink refusal, internal symlink acceptance), missing-commit
  failure, `out`-exists refusal, subprocess-failure wrapping and incomplete-output refusal are untested; only the
  happy path is covered, indirectly, by the (verified) real-data run. In a codebase where refusal paths are
  normally pinned by synthetic tests, add these (a crafted `git archive` output via a monkeypatched
  `subprocess.run` is enough) before merge.

## Real check evidence — confirmed, with one wording correction

Confirmed independently (see table): the PASS, the completion hashes and the read-only effect on the sealed
files. The report's line 36 sentence about label/evaluation access is wrong and must be corrected (B2); the
correct statement is that the check opens the blocks only inside the release integrity carve-out and returns
nothing but pass/fail, counts and hashes. Reporting the invocation and returned `completion_sha256` is also
needed to make the claimed PASS reproducible.

## Unit 2 — arms readiness note

The factual basis is confirmed independently (116 of 4,999 sweep-1 proposals, only
`features.budget_frac_left`, configs and all other proposal fields identical; v2 and v3 formulas as stated; the
featurizer version is not stored in tables, so a derived feature view does not touch proposal identity or the
sealed table). The recommendation — one v3 featurizer for both sources, sealed sweep-1 table stays v2, derive a v3
feature view at arms-training time, document it, or exclude/flag the affected proposals if it cannot be produced
— is sound and correctly avoids re-auditing/replacing the sealed B.2 provenance, which would be a provenance
change. Scoping and clarity are good, but the note is not yet fully specified:

- (M7a) It is scoped to "arms trained on both sources"; say what sweep-1-only arms use (the same v3 view is the
  consistent choice; otherwise arms comparisons across sources confound featurizer version). Also say how many of
  the 116 affected proposals are in the arms-training (deduplicated/eligible) population, not only in the 4,999
  table rows.
- (M7b) The derivation is under-specified. Name the mechanism (a reviewed script that rebuilds the sweep-1 table
  from the same pinned ledgers with the current v3 `build_from_sweep` — or recomputes the field from the same
  `row_worker_runs`-based accounting — and emits a **derived-feature artifact** with sha256), assert that all
  other proposal fields/row order/configs match the sealed table, and require the artifact's sha256 in the arms
  record. "Document the derivation" alone is weaker than this project's standard for inputs to training.
- (M7c) Wording: "The only difference between the two sources' proposal features is that one field" is misleading
  — the two sources differ in many designed ways. What is true is that the **only featurizer-version difference**
  in the proposal feature vector is `budget_frac_left`, for 116 of 4,999 sweep-1 rows; reword.
- (M7d) The "exclude/flag the 116" fallback is correctly marked as an author decision to record; it should also
  state that it applies per arm and is disclosed, and that labels/evaluation values are unaffected either way.

## MINORS (non-blocking, should be fixed or explicitly waived)

1. **M1 (tests):** no tests for the new module's safety/failure paths (see Tests above); add before merge.
2. **M2 (relative paths):** `rebuild_v2_table` passes `index`/`paper_root`/`classification` to the subprocess
   unresolved, with `cwd` = the extracted tree. The release CLI accepts relative paths (the S2 release report
   records sweep-1 inputs as `results/r1/…`), but inside the child the v2 `evidence_classification` resolves a
   relative index against the extracted tree and refuses ("classification and index must be inside repository").
   The author's real run used absolute paths (visible in `/tmp/ab79_replay`), so this does not affect the recorded
   evidence, but the unit should `Path(...).resolve()` its inputs in the parent before spawning (the parent's cwd
   is the release cwd) or document that absolute paths are required. This is fail-closed, not a bypass.
3. **M3 (robustness):** `git archive` and the replay subprocess have no timeout (the rest of the release code uses
   20–60 s timeouts); the whole 185 MB archive is buffered in memory twice (`capture_output` + `tarfile` over
   `BytesIO`); the child's stderr is inherited (the expected `fatal: not a git repository` noise from the v2
   `git_head()` fallback appears in the release log). Consider a timeout, writing the archive to disk/`tarfile`
   streaming, and capturing/discarding child stderr unless the replay fails.
4. **M4 (provenance clarity):** `V2_BUILDER_COMMIT` is a hard-coded commit whose value is justified by the sealed
   table's recorded `commit`, but `_verify_replay` pops `commit` before the comparison and nothing asserts
   `existing_meta["commit"] == V2_BUILDER_COMMIT`. The byte compare still establishes equivalence, so there is no
   bypass, but the compat path should assert the recorded commit equals the constant (fail closed, clear message)
   and the hook comment should state that only the reviewed builder may be passed.
5. **M5 (scope wording):** `sweep1_integrity` now always replays with the ab79b4ce v2 builder, so a future
   sweep-1 table built at another code commit would be replayed with v2 and refused. That is in line with option A
   (the sealed table is the only sweep-1 table), but state it; and state that the v3 `r1.c3.dataset` is still
   imported on this path for `evidence_classification`/`load_table` (the report's "never imported by the
   compatibility replay" is true only of the replay subprocess).
6. **M6 (other consumer, scoping note):** `offline_eval._verify_evidence_inputs`
   (`r1/c3/offline_eval.py:116-125`, reached from `offline_eval.assemble`, `env.label_rows`,
   `ni_masking.load_audits`) still calls `verify_evidence_completion` with the default v3 builder. If any T0
   arms/evaluation consumption path re-verifies the sealed sweep-1 EVIDENCE table through it, it will still
   refuse with the same replay mismatch. Confirm the T0 path does not, or schedule the same reviewed
   compatibility route for that consumer. (Not a release blocker: the release itself uses `sweep1_integrity`.)
7. **M7 (unit-2 scoping):** see Unit 2 above (a–d).
8. **M8 (report):** record the exact real-check invocation/environment and returned dict (B2), and note the
   merge-then-release sequencing (the release cannot run from this branch; the branch is pushed and mechanically
   clean, but `_published_clean` will STOP until `audit.py`/`release_checks.py` are on `origin/main`).

## Push readiness

- **Branch:** `6f713ede` is already pushed; clean; base `1402f466`; the diff is 6 files (no `release.py`,
  `dataset.py`, `features.py`, PLAN or data change). Mechanically publishable as-is.
- **Merge/release:** not ready until B1–B3 are fixed/confirmed. B1 is a small `release_checks.py` change (+ test)
  that keeps `release.py` bytes unchanged (required by the release row's `release.py @ a9d8ff5e` binding); B2 is
  a report edit; B3 is a record/authority confirmation (and, if the literal REL-CODE A reading is chosen, a short
  author row on main). None of the three changes the verified verification logic or the sealed artifacts.
- After the fixes and the author's main-push/merge decision, the sweep-1 train/dev release can be rerun from a
  clean checkout at the new published main under R1-S2-LABELS-TRAINDEV-RELEASE; the check that failed on 22 Nov
  now passes on the real sealed inputs (independently reproduced here).

## Disposition

The implementation is technically sound and the real-data result is real: the compatibility replay is
byte-identical, the metadata normalisation is minimal and safe, sweep 2 and the default path are unchanged, and
there is no bypass of data/identity checks. Do not publish/merge yet: close B1 (pin the new executed module
through `release_checks.py`), correct B2 (the label/evaluation-access sentence and the missing reproducible
invocation), and record B3 (the `audit.py`/`sweep_index.path` authorization basis). The minors can be folded into
the same round.

Round-1 verdict: NOT ACCEPTED (superseded by Round 2 below).

---

## Round 2 — revised unit @ `9ebd9d90` (22 November 2026)

Reviewed: branch **`rel-sweep1-compat-20261122` @ `9ebd9d90`** — pushed (`git ls-remote` = `9ebd9d90`,
`origin/main` unchanged at `1402f466`); worktree clean. Round-2 delta `6f713ede..9ebd9d90` is five files:
`r1/c3/release_checks.py`, `r1/c3/sweep1_compat.py`, the two test files and the report; **`r1/c3/audit.py` is
unchanged in round 2**, and the full branch-vs-main diff is still the same 6 files (no `release.py`,
`PUBLISHED_PATHS`, PLAN or data change). Deepthought worktree at `e629472c`, code-identical to `9ebd9d90` (the only
difference is the report's test-count line), so tests/replays there exercise the reviewed code.

Method: read-only ssh; reran the two suites (50 tests); ran the new published-code guard and the report's
documented `sweep1_integrity(...)` invocation against the real sealed inputs (both now refuse pre-merge by
design — expected), and ran the changed compatibility builder through the real-data `evidence_plan` gate; checked
the sealed table/audit mtimes and hashes before/after. No worktree file, `/work` or `/ceph` write (only a
metadata-only `git fetch` of the pushed branch refs); nothing under the sealed trees was created or deleted. The
only write is this appended file. The full-check run in round 1 opened the sealed role
blocks only inside the `integrity_context` carve-out and printed only hashes/counts; the same is true of the
round-1 rerun recorded there.

### Blockers — closed

- **B1 (release-code pinning) — closed.** `release_checks._sweep1_compat_published()`
  (`r1/c3/release_checks.py:21-36`) now pins the module exactly like the sweep-2 precedent
  (`_sweep2_batch_published`, `:66`): module-file identity beside `release_checks.py`, `git diff --quiet
  refs/remotes/origin/main HEAD -- r1/c3/sweep1_compat.py`, and a tracked-status check; it is called **first** in
  `sweep1_integrity` (`:50`), before the sealed `build.json` read, the new commit pin and the §6 carve-out, so a
  failed guard opens no label/evaluation data. `release.py` and `PUBLISHED_PATHS` are untouched, as required (an
  edit there would break the release row's `release.py @ a9d8ff5e` binding). The two new wrapper tests
  (`r1/tests/test_c3_release.py:379-397`) are meaningful — one proves the guard is invoked (sentinel exception
  propagates), one proves a table whose `build.json` commit is not `V2_BUILDER_COMMIT` is refused. Verified live
  on the branch with the real inputs: `_sweep1_compat_published()` and the documented
  `sweep1_integrity(...)` call both raise `ValueError: r1/c3/sweep1_compat.py differs from origin/main or is
  modified` — exactly the intended pre-merge stop; after the merge `HEAD == origin/main` on this file, so the
  guard passes (the release's `_published_clean` already enforces the matching condition for the other modules).
  Residual (non-blocking): there is no repo-fixture test of the guard's *passing* path — it runs only at the
  post-merge release — but the guard is the same shape as the sweep-2 precedent and the failure path is
  demonstrated above.
- **B2 (report accuracy) — core statement fixed; two required docs corrections remain.** The report now states
  truthfully that the check opens and re-derives `label_block.jsonl`/`evaluation_block.jsonl` **inside the §6
  carve-out**, that no value is returned/printed/recorded, and that the sealed blocks were not modified; it adds
  the exact invocation, the release-root index/classification, `completion_sha256 = e28bee5e…` and the
  merge-then-release sequencing. **Required corrections (docs-only, to ride with this push):** (i) the recorded
  PASS is from `6f713ede`/`b2b7489a`, **before** the round-2 guard; on `9ebd9d90` the exact documented invocation
  refuses pre-merge at `_sweep1_compat_published()` (verified above). The report must say the PASS was recorded
  pre-guard and that the full check is reproducible only from the merged published checkout (or by a reviewer
  who deliberately invokes the verifier without the guard) — otherwise "now PASSES" does not reproduce as
  written. (ii) The "What changed" section does not mention `_sweep1_compat_published()` or the new sealed
  `build.json` commit pin, and the test bullet list does not mention the four new tests; add them, and give the
  full absolute `index`/`classification` paths used by the recorded run instead of the ellipses.
- **B3 (authority record) — closed as far as the unit can close it.** The report now records the basis: the row's
  "`release_checks.py` (or its replay wrapper)" covers the audit `replay_builder` seam called from
  `sweep1_integrity`; the `sweep_index.path` normalisation is justified (release invocation passes an absolute
  index while the sealed record holds the relative one; `sweep_index.sha256` is still checked); and it states
  that a short author confirmation/row is needed only if REL-CODE A is read literally as `release_checks.py`-only.
  That is the recorded basis this unit can provide; the literal-reading confirmation remains an author/lead
  decision, not a code defect.

### Minors — addressed, and residual

Addressed in round 2: parent-side `Path(...).resolve()` of `index`/`paper_root`/`classification`/`out`
(`r1/c3/sweep1_compat.py:62-63`, closing round-1 M2); `git archive --output` to a temp file instead of a 185 MB
in-memory buffer, with `timeout=600` for the archive and `timeout=1800` for the replay (`:35-50`, `:77`, part of
M3); sealed `build.json` commit pinned to `V2_BUILDER_COMMIT` (`release_checks.py:53-56`, M4); builder
missing-commit and existing-output refusal tests (`r1/tests/test_sweep1_release_compat.py:117-133`, part of M1);
report invocation/sequencing (M8, partly; see B2 residual).

Residual non-blocking (same dispositions as round 1): no tests for the tar-safety refusals (absolute/`..` member,
escaping symlink) or for incomplete-output/subprocess-failure wrapping (M1 remainder); the guard has no
positive-path test (above); child stderr still carries the expected v2 `git_head()` noise (`fatal: not a git
repository`, observed again in the round-2 real-data run) — cosmetic (M3 remainder); the other production
consumer `offline_eval._verify_evidence_inputs` still uses the default v3 builder on EVIDENCE tables (round-1 M6,
scoping observation only); unit 2's new sentence "Sweep-1-only arms and sweep-2-only arms are unaffected" is
clearer than round 1 but still leaves open whether sweep-1-only arms keep the v2 table as-is and how a
cross-source comparison of separately-trained arms discloses the v2/v3 difference (M7a residual, non-blocking).

### Verified evidence (round 2)

- **Tests:** `pytest -q -p no:cacheprovider r1/tests/test_sweep1_release_compat.py r1/tests/test_c3_release.py`
  on deepthought (code-identical `e629472c`, venv Python 3.13.15, audited harness): **50 passed in 20.96 s**,
  worktree clean after. The author's `.pytest_cache/v/cache/nodeids` also holds exactly 50 ids (7 compat + 43
  release) with `lastfailed` empty. Matches the report's "50 passed".
- **Guard on the branch (real inputs):** `_sweep1_compat_published()` → `ValueError` (message above);
  `release_checks.sweep1_integrity(sealed table, sealed audit, paper_root=/work/…/paper, index, classification)`
  → the same `ValueError`, raised before the carve-out (no block read). This is the expected pre-merge behaviour.
- **Changed compat builder on real data:** `audit.evidence_plan(sealed table, /work paper root, index,
  classification, replay_builder=sweep1_compat.rebuild_v2_table)` → **PASS**; plan length 1,725; proposals
  `b713c423…`, configs `b585b727…`, counts duplicates 3,274 / eligible 1,725 / noops 0. So the round-2 builder
  (resolved paths, tar-to-file, timeouts) still reproduces the sealed table byte-for-byte and the normalised
  metadata compare still passes.
- **Round-1 full-check PASS stands:** the only round-2 code changes on that path are the builder internals
  (verified above), the guard (passes post-merge) and the sealed-commit pin (the sealed `build.json` commit is
  `ab79b4ce`, verified in round 1); `audit.py`, the completion/role-block logic and the sealed artifacts are
  unchanged. The recorded `completion_sha256 = e28bee5e…` remains valid evidence, with the provenance caveat
  required in B2.
- **Repository state:** remote branch `9ebd9d90`; remote main `1402f466` (no main push); worktrees clean; sealed
  table `proposals.jsonl` mtime 19 Nov 01:24 and `evidence_completion.json` mtime 19 Nov 01:50, hashes unchanged
  after the round-2 runs.

### Push readiness

The branch at `9ebd9d90` is pushed and clean; round-2 delta is small and the code blockers are closed. It is
ready to push/merge once (i) the two B2 report corrections above are applied (docs-only) and this appended review
is committed into the branch, and (ii) the author takes the main-push/merge decision. After the merge, the
sweep-1 train/dev release reruns under R1-S2-LABELS-TRAINDEV-RELEASE from a clean checkout at the new published
main; there `_published_clean` and the new `_sweep1_compat_published` guard both pass and the verified check runs
again. No code blockers remain.

Round-2 result: blockers B1–B3 are resolved (B2's factual statement fixed; two docs corrections required with the
push), the 50-test result and the changed builder's real-data behaviour are independently verified, and the
residual items are non-blocking minors. The round-1 NOT ACCEPTED is superseded.

VERDICT: ACCEPTED
