# Independent review — Track P P.3a probes-only runner (round 3, round-2 fixes), 16 November 2026

**Status: ACCEPTED — 0 BLOCKING, 0 MAJOR, 3 MINOR (all non-blocking, none affecting the delivery decision), plus
2 observations.** Fresh independent reviewer (round 3; no part in drafting the plan, the readiness corrections, the
round-1/round-2 runner or any of its fixes). **Read-only review.** No push, no commit, no merge, no deletion, no GPU
command, no model execution and no TASL-7 contact. The only workspace change made by this review is this
uncommitted review file (two other untracked review artifacts appeared during the review from concurrent
reviewers, §1); transient `/tmp` probe repositories/scripts were used for the adversarial checks below and
removed afterwards. CPU
tests were run from the temporary venv `/tmp/p3a_test_venv`, not from the TASL-7 environment. The tracked tree was
clean before and after the review (only untracked review artifacts, §1).

## 0. Canonical bytes and method

Worktree `/Users/wongdowling/Documents/agent_paper_B/.claude-worktrees/trackp-p3a-code-20261116`, branch
`trackp-p3a-code-20261116` (local, no remote contains it), HEAD = **D**.

| Object | sha / line count |
|---|---|
| **D** (HEAD, delivery-pin/docs child) | `8662e35991659f7a661fb7ed6be4980791d302f3`; parent = C; subject `docs(r1): P.3a runner review-fixes (round 2) record + delivery pin` |
| **C** (reviewed code commit, `D^`) | `5b7ad0cb7fedd083bad457968dc3dd3e920ac154`; subject `fix(r1): Track P … review fixes (round 2)` |
| previous delivery pin (round 2) | `9071f5b228a8e8311ccf7fc96c0e7587832dcdf2` |
| round-1 code commit | `7c9e8b0829450a70c462f2513873a56abcb8efdf` |
| round-1 docs child (stale constant, removed) | `8a3d3eaf048c7dd0a109719175dace72333bbd04` |
| A3-short delta (unchanged) | `3833d93e8f84f19bc20908b111136d9d4a5c0556` |
| paper base pin (ancestor) | `b9ad6f8fe2e771732100f704accd7f2ce7cf20f0` (`merge-base --is-ancestor` = true) |
| `r1/scripts/trackp_p3a_guarded.py` at D | `c045475b458b0112315a04b858c2b2f407b668b64b8651f921441a1a24864e56`, 1505 lines, 86,035 bytes |
| `r1/scripts/trackp_p3a_guarded.py` at C | `44549ca1d84cfd8fd324d3ff5c1bb85c13bacbcc4a73794553e381a4fe1e4c42`, 1505 lines |
| `r1/tests/test_trackp_p3a_probes_only.py` (C and D, identical) | `880172d8a5f29e1bb7f6b7c44b826db2424752aec807d54d44ca3c9ff5eac6c7`, 1267 lines |
| `docs/r1/reports/TRACKP_P3A_CODE_UNITS_20261116.md` | at D `032e1e7aef6d7d282ef55ea774fbe4fe71b8f96ce531f9131ca7ab4936f28558` (385 lines); at C `03854181…` (337 lines) |
| child `r1/scripts/trackp.py` (unchanged) | `d2a30ec2c1b4c2b33387898a4ccafecff3cd7c584a8df68d586c011a07b09e63` |
| `r1/scripts/trackp_p3a_watchdog.py` / `r1/scripts/trackp_p3a_gate.py` | `98a4d0b6…f57858a8` / `234f470e…009f12cf7` |

Author and committer of C and D: `Dowling Wong <wangdowling@gmail.com>` (§1). Authority read-only: accepted Unit A
plan rev 2 `docs/r1/proposals/TRACKP_P3A_ATTEMPT2_20261116.md` (via the accepted Unit A review and the runner's
pins), M13 order record `docs/r1/reviews/TRACKP_P3A_M13_ORDER_RECORD_20261116.md`
(`M13_ORDER_RECORD_SHA256 = 351611c5…`), 4 Nov amendment (`AUTHORIZATION_AMEND_SHA256 = cd867e95…`), round-2 review
`docs/r1/reviews/TRACKP_P3A_RUNNER_REVIEW_R2_20261116.md` (read in full), and the A6 disposition
`R1-TRACKP-A6-DEFER` @ `65d8d5bb` (object present in this repository; cited by the record, §4 below). The M13/plan/
authority documents live on the ops branch; their identity is cited, not re-hashed here.

Local CPU evidence (temporary venv `/tmp/p3a_test_venv`, Python 3.13.4 / pytest 9.2.0, macOS, no GPU/model/host):

```
py_compile exam_run.py trackp.py trackp_p3a_guarded.py test_trackp_p3a_a3_short.py test_trackp_p3a_probes_only.py  OK
pytest r1/tests/test_trackp_p3a_probes_only.py -q -rs  ->  45 passed, 2 skipped   (skips: no huggingface_hub;
                                                             no installed kev — both with explicit reasons)
pytest r1/tests/test_trackp_p3a_a3_short.py -q         ->  8 passed
pytest r1/tests/test_trackp_p3a_guarded.py -q          ->  5 passed, 4 failed    (pre-existing macOS prctl
                                                             preexec_fn failures; test file unchanged, see §5)
pytest r1/tests/test_trackp_cli.py -q                  ->  9 skipped             (no transformers/tokenizers)
```

## 1. Diff scope and commit identity (question 1) — PASS

- `git diff 9071f5b2..C --stat` = `r1/scripts/trackp_p3a_guarded.py` (+253/−58) and
  `r1/tests/test_trackp_p3a_probes_only.py` (+243/−62) only. No other path in the round-2 fix.
- `git diff C..D --name-status` = `M docs/r1/reports/TRACKP_P3A_CODE_UNITS_20261116.md`, `M
  r1/scripts/trackp_p3a_guarded.py` only. `git diff -U0 C..D -- r1/` is **exactly** one removed and one added line:

  ```
  -EXPECTED_PAPER_HEAD = "7c9e8b0829450a70c462f2513873a56abcb8efdf"          # reviewed probes-only runner commit
  +EXPECTED_PAPER_HEAD = "5b7ad0cb7fedd083bad457968dc3dd3e920ac154"          # reviewed probes-only runner commit
  ```

- `git rev-list --parents -n 1 D` = `D C` (single parent; `D^ = C`, no merge commits in `9071f5b2..D`).
- Author = committer = `Dowling Wong <wangdowling@gmail.com>` for C and D (C `23:20:07`, D `23:20:31 +0100`).
- `git diff 7ae4d2ea..D --stat` touches exactly the three files of record §0 (record 385+, runner, tests); no
  A3-short file, no config/rule/E0/data/model change, no script outside `r1/`, no deletion, no `main` merge.
- A3-short `3833d93e` untouched: `git diff --stat 3833d93e..D -- r1/c3/train/exam_run.py r1/scripts/trackp.py
  r1/tests/test_trackp_p3a_a3_short.py` is empty.
- Branch is `trackp-p3a-code-20261116`, **local/unpushed** (`git branch -r --contains D` is empty; status
  `…origin/trackp-20261026 [ahead 7]`). Tracked tree clean; `git status --porcelain` shows only untracked review
  artifacts (round-2 file at review start; two further sibling review files — `TRACKP_P3A_RUNNER_REVIEW_20261116.md`
  and `TRACKP_P3A_A3SHORT_REVIEW_20261116.md` — appeared during the review from concurrent reviewers, not from this
  review, which only added this file).
- `b9ad6f8f` is an ancestor of D. The stale `EXPECTED_PAPER_HEAD_DOCS_CHILD` constant is gone (grep: no reference
  outside the round-2 review text); `PAPER_RUNNER_PATH`, `PAPER_CHILD_SCRIPT`, `CODE_UNITS_RECORD` are unchanged.

## 2. Round-2 BLOCKING-1 (mutable global lease log in the M4 unit-start check) — FIXED

Verified from the bytes of C:

- **Immutable half split out.** `attempt1_journal_facts` (runner 982–1015) reads only the pinned attempt-1 journal
  (hash, exactly one STOP, finite GPU seconds, paper commit/branch/dirty, boot id). `build_attempt1_provenance`
  (1017–1034) calls it once at campaign start and adds the **live** global log path+sha as provenance metadata.
  `assert_attempt1_pins` (1073–1084) still pins `lease_log_sha256` to
  `EXPECTED_ATTEMPT1_LEASE_LOG_SHA256 = 695050…` — and `run_probes_only_campaign` calls it before the root exists
  (1380).
- **Snapshot.** `snapshot_attempt1_lease_log` (1038–1071) copies `<attempt1-root>/../gpu_lease_log.jsonl` to
  `<root>/attempt1_provenance/gpu_lease_log.jsonl` with `O_WRONLY|O_CREAT|O_EXCL`, fsync, `chmod 0444` and a
  re-hash + byte-count round-trip. It refuses an existing/dangling destination, refuses when the bytes read differ
  from the campaign-start `lease_log_sha256` ("changed between campaign start and the snapshot"), and records schema
  `trackp_p3a_attempt1_lease_log_snapshot/v1` with `path`, `sha256`, `bytes`, `lines`, `source`,
  `source_sha256_at_snapshot`, `read_only: true`, `mode: "0444"`, `created_utc` and a note. Nothing is written into
  attempt 1 (source is only read; the test asserts attempt-1 tree hashes are unchanged).
- **Ordering.** In `run_probes_only_campaign`: preflight (1378) → provenance/pins/boot/inputs/templates (1379–1402)
  → `args.root.mkdir()` (1404) → **snapshot (1407)** → journal (1409) → campaign_start + marker (1418, 1423) →
  units. The snapshot is created before any journal/marker/child.
- **Verifier never reads the live log.** `make_unit_start_verifier` (1254–1303) now takes `snapshot`, re-runs
  `attempt1_journal_facts`, checks the snapshot file's sha256 and byte count against its recorded values *and*
  against `provenance["lease_log_sha256"]`, re-hashes the loaded attempt-1 files and recomputes the template, and
  records `lease_log_snapshot_path/sha256/bytes` plus an explicit `lease_log_source` note. The live global log is
  not read at unit start (proven by instrumentation, below).
- **Tests are host-shaped, not vacuous.** `_snapshot_campaign` (tests 663–678) puts the attempt-1 root directly
  under the runs dir, so `<attempt1-root>/../gpu_lease_log.jsonl` *is* the live global log;
  `test_blocking1_unit_start_verifies_the_immutable_snapshot_not_the_live_global_log` (681–707) passes DRYRUN start,
  appends a fake lease pair to the live log, passes the EVIDENCE start, asserts snapshot mode 0444 and attempt-1
  immutability, then tampers the snapshot and asserts a STOP. `test_snapshot_refuses_a_live_lease_log_that_changed_
  since_campaign_start` (710–723) covers the campaign-start→snapshot race. `test_campaign_runs_exactly_dryrun_then_
  evidence` (1061+) appends a lease pair to the live log inside the DRYRUN and asserts both unit-start snapshot
  hashes, so the end-to-end sequence is covered.
- **Independent reproduction** (fresh host-shaped synthetic tree, real module; `sha256_file` instrumented to log
  every path re-hashed at unit start):

  ```
  attempt1 root = <runs>/p3a_operator_20261027, parent IS the runs dir = True
  snapshot schema trackp_p3a_attempt1_lease_log_snapshot/v1, required fields all present, mode 0444
  DRYRUN  unit-start: passed
  live global log appended with a start/end pair -> sha changed
  EVIDENCE unit-start: passed;  paths re-hashed include journal.jsonl and the *snapshot* gpu_lease_log.jsonl
  live log re-read at unit start: False
  tampered snapshot -> TrackPStop "attempt-1 lease-log snapshot drift at EVIDENCE/…"
  ```

  (The independent tree carries a synthetic lease hash, so `assert_attempt1_pins` was not exercised there — as in
  the tests, which stub it; the snapshot machinery itself is exercised end-to-end.)

**BLOCKING-1 is fixed as required (route (a) of the round-2 review) and the EVIDENCE unit can now start after the
DRYRUN has appended to the global log. No regression found in this area.**

## 3. Round-2 MAJOR-1 (crafted one-line delivery-pin child) — FIXED, byte-exact

Verified from the bytes of C:

- `expected_pin_runner_blob` (302–319) fetches `C:r1/scripts/trackp_p3a_guarded.py`, requires **exactly one** line
  matching `^EXPECTED_PAPER_HEAD = "[0-9a-f]{40}"[ \t]*(?:#.*)?$` (else STOP), and substitutes the canonical
  `PIN_LINE_TEMPLATE` line naming C. In-memory result = the only acceptable pin-child runner blob.
- `_delivery_pin_child` (322–343) requires: a single parent exactly C; the runner path changed; every other changed
  path under `docs/`; and the child's runner blob **byte-identical** to `expected_pin_runner_blob()`. The old
  one-added/one-removed line "contains" rule is gone. The docs-only-child branch is re-based on C
  (`_docs_child_of_reviewed`, 346–358: descendant of C with a byte-identical `r1/` tree) and is documented as a
  function-level identity only; `verify_paper_head` (361–388) accepts exactly C / docs-only child of C / the
  byte-exact pin child, with branch `trackp-p3a-code-20261116` or detached `HEAD` and C an ancestor.
- **Real repository:** `expected_pin_runner_blob()` = `c045475b…` / 86,035 bytes = exactly
  `D:r1/scripts/trackp_p3a_guarded.py` = the on-disk runner; `_delivery_pin_child(D) = True`;
  `verify_paper_head(D) = delivery_pin_child`; `verify_paper_head(C) = exact_reviewed_runner_commit` (with D's own
  module constant); `9071f5b2`, `7c9e8b08`, `3833d93e`, `8a3d3eaf` are all refused.
- **Adversarial probe repository** (throwaway repo carrying the real C/D objects; commits built with plumbing so the
  runner/test bytes are exactly the reviewed ones, then judged by the real functions):

  | child of C | `_delivery_pin_child` |
  |---|---|
  | genuine pin child (byte-identical runner) | **True** |
  | crafted one-line child: `EXPECTED_PAPER_HEAD = "<C>"; __import__("os").system(...)` (executable injection) | **False** |
  | crafted one-line child: canonical line with `…; __import__("os").system(...)` after the trailing `#` comment | **False** |
  | pin + extra `README.evil` outside `r1/`/`docs` | **False** |
  | pin + extra file under `docs/` | **True** (allowed by design; docs never execute) |
  | pin + an `r1/scripts/trackp.py` edit | **False** |
  | merge commit (two parents, one = C) | **False** |
  | descendant of the pin child | **False** |
  | pin + submodule gitlink | **False** |
  | C itself | **False** |

- **Executing bytes (round-2 MINOR-3).** `verify_executing_files` (391–422) requires the executing runner to be the
  checkout's tracked runner (both resolved), requires C to be an ancestor of HEAD, and requires the twelve
  `EXECUTING_FILES` (58–63: runner, child `trackp.py`, watchdog, gate, `run.py`, `types.py`, `model.py`,
  `exam_run.py`, `trainer.py`, `registry.py`, `serialize.py`, `r1/c3/labels.py`) to be byte-identical to their
  `HEAD:` blobs, refusing dirty/untracked/ignored/`assume-unchanged` differences, a foreign copy and a missing file;
  it records path/sha256/bytes per file. It is called in the preflight (1105) and its record is embedded in the pins
  (1175–1176) and therefore in `campaign_start.pins`/top-level `runner_script_path`/`runner_script_sha256`.
  Reproduced against the real worktree: 12/12 files byte-identical to `HEAD:`, runner sha256 `c045475b…`.
- **Accepted set.** With the executing module at the acceptable identity (constant = C, i.e. D's bytes), the only
  runnable clean checkouts are: D (pin child) — C is refused by *C's own* script (its constant still names
  `7c9e8b08`), and a docs-only child of C is likewise refused by a clean checkout (its executing bytes carry the
  previous pin), which I reproduced by running `verify_paper_head` with the constant set to `7c9e8b08`: C refused, a
  docs-only child of C refused. The old delivery pin `9071f5b2` is accepted only by *its own* (now superseded)
  script and is refused by D's preflight. This matches record §5.5/§6 exactly.
- **Variants probed, no runtime bypass:**
  - *symlink runner:* a child whose runner tree entry is a `120000` symlink blob equal to the expected runner text
    is accepted by `_delivery_pin_child` (content-only check), but it can never run: `git checkout` of that commit
    fails outright on the host filesystem ("unable to create symlink …: File name too long"), and a checkout would
    be refused by `verify_executing_files` (`path.is_file()` false → "executing file missing").
  - *exec-bit:* a pin child whose runner entry mode is `100755` with identical bytes is accepted; it executes
    identical reviewed bytes, so this is harmless (see observation O1).
  - *ignored/untracked local file:* cannot be delivered by a commit; force-adding an ignored path makes it a changed
    path (refused unless under `docs/`). A working-tree-only tamper of an *unpinned* imported module is a remaining
    defence-in-depth gap — see MINOR-2 — but it is not reachable by the D delivery.
  - *env vars:* `GIT_*` variables affect the identity calls and the recorded `HEAD` consistently, and the expected
    pin blob is derived from C's content-addressed blob while `verify_executing_files` requires the on-disk bytes to
    equal the accepted `HEAD:` blobs, so environment manipulation cannot make unreviewed runner bytes pass while a
    reviewed identity is recorded. An operator controlling the process environment/filesystem can always run
    arbitrary code before the preflight — outside the commit-delivery threat model.

**MAJOR-1 is fixed as required; the required crafted-child refusal test is present and goes through the real
`_delivery_pin_child` (tests 305–309, 343–345). One test-strength nit: MINOR-1.**

## 4. Retained round-1 fixes and regression scan (question 4) — PASS

`git diff 9071f5b2..C` changes only the functions listed in §2/§3 (+ the constants/comment block at 41–63, 94–99 and
the preflight/`campaign_start` wiring). Everything else is byte-identical, so the round-1 fixes are retained; the
tests that pin them still pass:

- boot-id gate: `verify_attempt1_boot_id` is still called against the attempt-1 journal boot id before root creation
  (1381), plus the live preflight gate and the per-unit boot re-check; `attempt1_boot_id_match` is now the
  **computed** comparison (1355, round-2 MINOR-5 fixed);
- exact two-command sequence (`probes_only_units`, DRYRUN `kev-0.8b` then EVIDENCE `qwen3.5-4b-base`, both
  `--a3-short`/`--budget`/`--load`), unchanged;
- 45-h lease math / 60-h cap / conservative 600 s and 1,800 s projections (`Attempt2Budget`), unchanged; DRYRUN
  `--n-probe 8` deviation now has a recorded rationale (code 77–83, record §2.6; round-2 MINOR-4 addressed);
- marker `begin p3a` before the first unit and `end p3a` in a `finally` on success/STOP, journal events unchanged;
- attempt-1 provenance hashing of the journal/loaded files/template and the M13 template block/per-family ids,
  unchanged (now split into the immutable facts + snapshot described above);
- new-root/attempt-1-root validation (absolute, absent via `l-exists`, UTC name, directly under the runs dir,
  reuse/nesting refused), unchanged;
- atomic sidecar write and finite-JSON re-reads, unchanged; M1 source-level golden vector runs, the two token-id
  vectors skip with explicit reasons (record §3/§6); A6 deferral `R1-TRACKP-A6-DEFER` @ `65d8d5bb` cited in record
  §5.6 with the required disclosure (attempt 2 runs no A6 work; any P.3b order change needs a separately reviewed
  A6 unit).
- No new bug found in the +253/−58 fix beyond the non-blocking items in §6; the old multi-base path
  (`main` without `--probes-only`) is untouched by this diff.

## 5. CPU tests (question 5) — numbers reproduce, new tests are real

The implementer's numbers reproduce exactly on this machine (§0). The four `test_trackp_p3a_guarded.py` failures are
the pre-existing real-subprocess tests that reach the pin's `worker_parent_death_guard` `preexec_fn`
(`prctl(PR_SET_PDEATHSIG)`; macOS has no `prctl`); `git diff b9ad6f8f..D -- r1/tests/test_trackp_p3a_guarded.py` is
empty, so they are untouched environmental failures. The two skips carry explicit reasons (no `huggingface_hub`; no
installed `kev`); `test_trackp_cli.py` skips for lack of transformers/tokenizers. No new test needs a GPU, model,
tokenizer or host.

The new tests are not vacuous: the crafted child is judged by the real `_delivery_pin_child` (test 343) and by the
real `verify_paper_head` (tests 344–345); the BLOCKING-1 test builds the host-shaped attempt-1 root
(attempt-1 parent = runs dir), snapshots with the real function, appends two lines to the live log between the two
unit-start checks and asserts both pass plus a tamper STOP; the executing-bytes test really marks a file
`assume-unchanged` (asserting `git status --porcelain` is empty) before expecting the STOP; the end-to-end campaign
test exercises the real snapshot/verifier with a stubbed child.

## 6. MINORs and observations (non-blocking)

**MINOR-1 — the crafted-child test's injected code is inert (test fidelity).** Tests 305–309 build the crafted line
as `canonical_paper_head_line(C) + '; __import__("os").system(...)'`, i.e. the injection is appended *after* the
trailing `# reviewed probes-only runner commit` comment, so the modelled child could not have executed its payload.
The test still catches the old shape-check bypass (the changed line would have passed the round-2 rule) and I
independently confirmed a genuinely executable pre-comment craft is refused (probe row 2), so behaviour is correct.
Fix when the test is next touched: inject before the comment, e.g.
`EXPECTED_PAPER_HEAD = "<C>"; __import__("os").system("touch /tmp/p3a_pwned")` (or move the comment after the
payload), so the test models executable injected code. Not a delivery condition.

**MINOR-2 — `EXECUTING_FILES` is not the probes child's full import graph (defence-in-depth).** The twelve files
(58–63) cover the runner/child/watchdog/gate and the main `r1/c3/train` modules, but the probes child imports more
repo modules (`r1/c3/train/exam_run.py` → `losses.py`, `exam_synthetic.py`; `serialize.py` → `r1/c3/features.py`;
`r1/harness.py`, `tiny.py`, `spike.py`, `exam_analyze.py`, `budget.py`, …). `R.git_commit` ignores
`assume-unchanged`/`skip-worktree` edits and `verify_executing_files` only compares the twelve, so a local
`assume-unchanged` edit to an unpinned module both leaves `git status --porcelain --untracked-files=no` empty and
passes `verify_executing_files` — I reproduced this with `r1/c3/train/losses.py` (12/12 files passed). This is not a
delivery bypass (a commit cannot carry index flags; D is delivered clean) and the round-2 requirement (the executing
runner plus entry-point files pinned to `HEAD:`) is met, but the docstring/record wording ("an
assume-unchanged/skip-worktree/ignored edit … is refused") is broader than the code. Suggested hardening before/with
Unit B: derive the set from the probes import graph, or additionally refuse any paper-checkout file carrying
`assume-unchanged`/`skip-worktree` (`git ls-files -v`). Not a delivery condition.

**MINOR-3 — record precision, §5.2.** Code-units record line 315 says "`git diff 7c9e8b08..C -- r1/` is confined to
the runner"; the diff is runner **and** the probes-only test file
(`git diff --stat 7c9e8b08..C -- r1/` = runner 313 changed lines, tests 305). Reword to "runner and its probes-only
test file". The record is inside D, so this is a note for a future record revision; not a delivery condition.

**O1 (observation, no action required) — runner tree-entry mode is not constrained.** `_delivery_pin_child` compares
blobs only, so a direct child of C with the byte-exact expected blob but mode `100755` is accepted (harmless: the
executed bytes are the reviewed bytes), and a `120000` symlink entry whose target text equals the expected runner
text is accepted at identity level but cannot be checked out/run (see §3). Optionally require `git ls-tree` mode
`100644` for the runner if strictness is wanted.

**O2 (observation, no action required) — snapshot `lines`** counts `\n` bytes (newline count), not logical lines; it
is informational only (sha256 + bytes are authoritative and verified), and the pinned attempt-1 log ends with a
newline.

## 7. Can D be recorded as the reviewed Unit B runner / delivered? (question 6)

**Yes — accepted.** **D `8662e35991659f7a661fb7ed6be4980791d302f3`** can be recorded as the reviewed Unit B runner and
delivered to TASL-7 as the clean checkout:

- The host must check out **exactly D** (detached `HEAD` or on branch `trackp-p3a-code-20261116`), **clean**. D is
  the only runnable delivery: its only difference from C is the single canonical `EXPECTED_PAPER_HEAD = "<C>"`
  assignment plus the code-units record, and it passes the byte-exact pin-child rule and the executing-bytes rule
  (`verify_paper_head(D) = delivery_pin_child`, 12/12 executing files equal `HEAD:`). **Not** C (C's own script
  refuses it: its constant still names `7c9e8b08`), **not** `9071f5b2`/`7c9e8b08`/`3833d93e`/`8a3d3eaf`.
- The branch is **local/unpushed** (not on any remote branch); delivery requires transferring it to TASL-7
  (push/fetch/bundle). The host paper checkout moves off `trackp-20261026`/`b9ad6f8f` to D (no merge of `main`),
  with `b9ad6f8f` still the ancestor pin.
- Post-review records must go to the ops branch; any commit on top of D (e.g. this review or an acceptance record)
  changes `HEAD` and makes the branch HEAD unacceptable (it would be a docs child of D, which the preflight refuses),
  while D itself remains the runnable checkout.
- **Unit B execution is still blocked on the non-code conditions** of the accepted plan: it needs the Unit A
  execution record, the delivery mapping and the explicit run authorization (a green preflight is **not** a run
  authorization). The A6 prerequisite is now cleared by `R1-TRACKP-A6-DEFER` (author decisions @ `65d8d5bb`; record
  §5.6): attempt 2 does no A6 work, the P.3a report must disclose the A6 deferral and the 2k/8k descriptive-level
  omission, and any P.3b serialization-order change needs a separately reviewed A6 unit.

## 8. Limits

- CPU-only static/dynamic review; the live TASL-7-only paths (`nvidia-smi`, driver snapshot, marker helper, GPU
  lease, real child, tokenizer/Kev golden vectors) were not executed here; their internals are covered by the
  stubbed CPU tests and the runner re-checks them live.
- No TASL-7 access; host facts (boot id, lease-log bytes, driver) are taken from the reviewed inventory/pins and the
  accepted earlier reviews; the runner re-checks them at run time.
- The adversarial probes use throwaway `/tmp` repositories carrying the real C/D objects and the real module; they
  were removed after use. No tracked file was modified (only git-ignored `__pycache__`/`.pytest_cache` artifacts from
  running the tests).
- The plan/M13/amendment/A6 authority documents are on the ops branch; their bytes were not re-read here (only their
  identity/pins as cited by the runner/record; the A6 commit object is present in this repository).
- E0 slopes/RPS/bootstrap bounds were not recomputed (not part of this code-unit review).

**Verdict: accepted — 0 BLOCKING, 0 MAJOR, 3 MINOR (MINOR-1 test fidelity, MINOR-2 `EXECUTING_FILES` import-graph
coverage, MINOR-3 record wording; none affects the delivery decision).** The round-2 BLOCKING-1 (mutable global
lease log at unit start) and MAJOR-1 (crafted pin child) are fixed from the bytes, with real host-shaped/crafted
tests; the round-1 fixes are retained and no regression was introduced. D can be recorded as the reviewed Unit B
runner and delivered as the clean checkout, subject to the plan's remaining Unit A / delivery-mapping / run
authorization requirements (A6 now deferred and disclosed).

*Review artifact: this file (uncommitted). Its sha256 and line count are reported by the reviewer in the completion
message (a file cannot embed its own hash).*
