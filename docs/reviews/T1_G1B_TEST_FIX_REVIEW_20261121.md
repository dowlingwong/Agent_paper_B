# T1 G.1b shipped-spec test fix — independent review (21 November 2026)

**Reviewer.** Fresh independent reviewer (`t1-g1b-test-fix-reviewer`), delegated by the lead; no involvement in writing
the test change, the shipped spec, the G.1b module or the pre-launch package. **Read-only: the only file written is
this review.** No tracked file was edited, nothing was committed/pushed/deleted, and no host, HTCondor, GPU or server
action was taken. The only processes run were the synthetic pytest module (writes only to pytest temp dirs) and
read-only `git`/`sha256sum` inspection.

**Object under review.** Worktree `.claude-worktrees/main_t1_host_reports_20261121`, branch
`main-t1-host-reports-20261121` at HEAD `71e6519b`, baseline `origin/main` = `d47d1008` (branch is 2 commits ahead).
Candidate fix: the **uncommitted, unstaged** working-tree change `M r1/tests/test_t1_tasl_g1b.py` (+16/−4). Nothing is
staged (`git diff --cached` empty).

| object | path | sha256 | state |
|---|---|---|---|
| test file, fixed (worktree) | `r1/tests/test_t1_tasl_g1b.py` | `4e3fe6b1…0450099e` (`4e3fe6b187524a9269c585b2ea95b4bf7b4c848bcc97f0e5731419cf0450099e`) | modified (`M`), unstaged |
| test file, branch HEAD | `r1/tests/test_t1_tasl_g1b.py` | `3ea40bb9…b260bba` (`3ea40bb9b1a88e4f18ba5267fd57dc33a175ad28bf2c06e4a28f9bc48b260bba`) | at `71e6519b` |
| shipped G.1b spec | `sweep2/t1_tasl/g1b_tasl_spec.json` | `2f0bdd70…aeadb` (`2f0bdd70399c7ec24a9f91de1e00e96fba4d8682e666ff51352d09ea5e3aeadb`) | at `71e6519b`, **untouched by the fix** |
| G.1b module | `sweep2/t1_tasl/g1b_tasl.py` | `90bb260e…c8ac6525` (`90bb260eb9be47ad969e64f1d13f3b2344b243b10232222b88c46cb2c8ac6525`) | unchanged vs `origin/main` |
| D21 library | `sweep2/g1b/g1b_lib.py` | `8b1e78c2…b6b73e6e` (`8b1e78c20ca913118fe5f86ac92c95f727fe2f3275dc1cee8688c382b6b73e6e`) | unchanged vs `origin/main` |

**Question.** Is the uncommitted test change an acceptable fix for the failing test
`r1/tests/test_t1_tasl_g1b.py::test_shipped_spec_validates_and_refuses_launch_until_filled`? The old test's premise
was that the *shipped* spec must fail `validate_spec(launch=True)` because its host/decision fields were TODO; the
branch's shipped spec was intentionally filled in `71e6519b`, so that premise is stale. The candidate fix renames the
test, asserts the filled spec passes `validate_spec(launch=True)`, resets one field to TODO on a deep copy and
asserts launch validation still refuses, and asserts `T.launch` still refuses a filled spec whose note is not
byte-identically on `origin/main`.

---

## Verdict

**ACCEPTED.**

No blocking or major findings. The fix is minimal and confined to the test file; it keeps the original intent
(shipped spec launch-validates; a placeholder still refuses launch; the signed-note gate is still required and a
filled spec alone is not launch authority), changes no spec value, and the new test passes. The conditions in §6 are
merge hygiene only.

---

## 1. Intent preserved

1. **Shipped filled spec passes `validate_spec(launch=True)`.** The test calls it on `copy.deepcopy(SPEC)` and keeps
   the original projection assertions (`within_cap`, < 100 GPU-h, exactly the seven `T1_NODES`, `mlgym_houseprice` on
   CPU). Observed directly: passes; projection `total_gpu_hours = 28.262` (cap 100). The spec sha is unchanged, so
   the test is validating the values the branch actually ships.
2. **A deep copy with one field reset to TODO still refuses launch.** `hosts.TASL-2.hostname` reset to
   `"TODO: hostname of TASL-2"` → `Stop: STOP: hosts.TASL-2.hostname must be set (the operator fills it from the host)`.
   It is the launch-only placeholder gate, not a generic field error: the same copy passes
   `validate_spec(..., launch=False)` (`allow = not launch` is the only placeholder tolerance), so the assertion pins
   `launch=True` specifically.
3. **`T.launch` still refuses a filled spec without the signed note byte-identically on `origin/main`.** With the
   real shipped `SPEC_PATH` and a temp note shaped `docs/r1/authorizations/g1b_t1_tasl_20261121.md`, `on_main` is
   injected as `False`; `launch` first validates the filled spec (`launch=True`, passes) and then stops with
   `STOP: the note is not committed byte-identically on origin/main`. The injected stub was observed called with
   exactly `docs/r1/authorizations/g1b_t1_tasl_20261121.md` and 15 raw bytes. `_note_on_main` itself is unchanged
   from `origin/main` (module diff empty) and compares `git show origin/main:<rel>` stdout to the raw bytes; no
   `g1b_t1_tasl_*.md` note exists on `origin/main` or on branch HEAD, so the real gate genuinely refuses today.
4. **Non-vacuity of the failure.** `origin/main`'s unfilled spec under `validate_spec(launch=True)` stops with
   `STOP: paper.commit must be a full 40-hex commit`, while the branch's filled spec passes — so the branch really
   does fail the old test, and the change addresses a real stale premise rather than papering over a product bug.
   The new test is also not self-satisfying: with `on_main=True` and the same minimal note, `launch` stops earlier
   with `STOP: note field label must be 'ENGINEERING_ONLY'`, which would **not** match the asserted
   "not committed byte-identically on origin/main"; the exact-message assertion is therefore specific to the
   byte-identity branch.

## 2. Scope and values (no filled spec value changed)

* `git status --short` shows only ` M r1/tests/test_t1_tasl_g1b.py` (plus pre-existing untracked `uv.lock`, an
  environment artifact created at worktree setup, 15:42:30, before this review and unchanged by the test run).
* `git diff --numstat -- r1/tests/test_t1_tasl_g1b.py` = **16 insertions, 4 deletions**, one file; staged diff empty.
* `git diff HEAD -- sweep2/t1_tasl/g1b_tasl_spec.json` is empty and the worktree spec sha equals its HEAD sha
  (`2f0bdd70…`). The only branch-vs-`origin/main` spec change is TODO→filled values from `71e6519b`; the fix does not
  touch it. The G.1b module and `g1b_lib.py` are unchanged vs `origin/main`.
* The new test's note path uses the exact `docs/r1/authorizations/g1b_t1_tasl_<YYYYMMDD>.md` shape (it matches
  `NOTE_DIR`/`NOTE_NAME` and the last three path components), and passes a `False`-returning `on_main`, so the
  byte-identity refusal is the intended sythetic condition, not a path-shape accident.

## 3. Observed test evidence

Command (exactly the node requested, run from the worktree root):

```
UV_CACHE_DIR=$PWD/.uvcache uv run --no-project --with pytest -- python -m pytest -q \
  r1/tests/test_t1_tasl_g1b.py::test_shipped_spec_validates_and_a_todo_still_refuses_launch
```

Result: **`1 passed in 0.05s`** (exit 0).

Supplementary full-module run: `5 failed, 34 passed in 5.67s`. All five failures are in the `job`-fixture / lease /
`run_node_job` tests untouched by this diff and all are the same environment refusal:
`PermissionError: [Errno 1] Operation not permitted: '/Users/wongdowling/r1_locks'` (the session workspace sandbox
denies writes outside the worktree). They are **not evidence** about the fix, consistent with the brief's
macOS/Linux caveat; the changed test is not among them. A real Linux run should confirm them (see §6 condition 3).

## 4. Authority — no overclaim

* A filled spec is **not** launch authority: `launch` loads → `validate_spec(launch=True)` → `check_note`; the note
  must be on published `main` byte-identically, and the enable key, host-record checks and the S2-C5 launch binding
  all still sit behind the note gate. The test observes the note refusal on the real shipped spec.
* The signed-note path is still enforced and its byte-identity comparison is unchanged from `origin/main`
  (`_note_on_main`: `git show origin/main:<rel>` stdout == raw note bytes). The test's docstring/name do not claim
  launch clearance; they claim (truthfully) that the filled spec launch-validates and that launch still refuses
  without the note.
* Limitation carried honestly: the byte-identity comparison is exercised through the injected `on_main` stub, not by
  a real `git show` in the test (the pre-existing `test_launch_needs_the_note_both_keys_and_the_binding` also stubs
  it). The real function was inspected and is unchanged, so this is a coverage observation (O1), not a defect of
  this diff.

---

## 5. Findings

**Blocking:** none. **Major:** none.

* **O1 — minor (coverage, optional).** The real `_note_on_main` git comparison is not asserted by any test (stub
  used in both this test and the pre-existing launch test). Optional follow-up: a hermetic test that runs the real
  `_note_on_main` against a temporary git remote/ref. Not required here because the function is unchanged and the
  gate's byte comparison was inspected.
* **O2 — minor (coverage, optional).** The fix removes the only *positive* `validate_spec(...)` call without
  `launch=True` (the old test's first line), i.e. the placeholder-tolerant CLI validation path (`cpus`, `logdir`,
  etc.) loses its direct positive assertion. Logically subsumed: `launch=True` is strictly stronger
  (`allow = not launch` only relaxes placeholder tolerance), and the TODO-reset copy was observed to pass
  `launch=False` while failing `launch=True`. Optional one-line restore, not a regression.
* **O3 — housekeeping.** Keep the commit scope to the test file: the worktree also has untracked `uv.lock` (and
  ignored `.venv`/`.uvcache`); those are environment artifacts and must not be staged with the fix.
* **O4 — minor (ordering dependency, no action).** The new `launch` assertion assumes the note gate runs before the
  enable-key/host-record/binding checks (it does: note → enable → host records → binding, the same order the existing
  launch test relies on). If a future reorder changes the first Stop, this test's expected message changes. Noted so
  a reorder is noticed; no change requested now.

## 6. Conditions

1. **Commit exactly `r1/tests/test_t1_tasl_g1b.py`** (16+/4−, sha `4e3fe6b1…0450099e`) and nothing else; do not stage
   `uv.lock`, `.venv` or `.uvcache`; keep the shipped spec at `2f0bdd70…aeadb` and the G.1b module unchanged.
2. **Re-run the node before committing** (same uv command or the repo's test runner) and keep `1 passed` for
   `test_shipped_spec_validates_and_a_todo_still_refuses_launch`.
3. *(recommended, not gating)* Run the full module on Linux/CI to confirm the five `~/r1_locks` permission failures
   are environment-only, and optionally add O1's real-git note test as a follow-up.
4. **Do not read this test as launch clearance.** `71e6519b`'s EVIDENCE is blocked on the signed note; no
   `g1b_t1_tasl_*.md` note exists on `origin/main` or branch HEAD, and the gate refuses exactly as asserted — the
   filled spec is launch-valid, not launch-authorized.

---

## 7. Reproducibility

All commands run from the worktree root, read-only on git and synthetic-only (no GPU/host/network):

```
git rev-parse HEAD origin/main
git status --short; git diff --cached --stat
git diff -- r1/tests/test_t1_tasl_g1b.py; git diff --numstat -- r1/tests/test_t1_tasl_g1b.py
git diff HEAD -- sweep2/t1_tasl/g1b_tasl_spec.json
git diff origin/main..HEAD -- sweep2/t1_tasl/g1b_tasl.py sweep2/g1b/g1b_lib.py
git ls-tree -r --name-only origin/main -- docs/r1/authorizations/ | grep -i g1b_t1_tasl
sha256sum r1/tests/test_t1_tasl_g1b.py sweep2/t1_tasl/g1b_tasl.py sweep2/g1b/g1b_lib.py sweep2/t1_tasl/g1b_tasl_spec.json
UV_CACHE_DIR=$PWD/.uvcache uv run --no-project --with pytest -- python -m pytest -q \
  r1/tests/test_t1_tasl_g1b.py::test_shipped_spec_validates_and_a_todo_still_refuses_launch
UV_CACHE_DIR=$PWD/.uvcache uv run --no-project --with pytest -- python -m pytest -q r1/tests/test_t1_tasl_g1b.py
```

Direct in-memory checks (no files written): `origin/main` spec → `validate_spec(launch=True)` stops on
`paper.commit`; branch spec → passes with `total_gpu_hours = 28.262`; TODO-reset copy → `launch=True` stops on
`hosts.TASL-2.hostname`, `launch=False` passes; `T.launch(SPEC_PATH, <temp note>, "mlab_imdb", enable=True,
on_main=False)` stops on `not committed byte-identically on origin/main` and `on_main` receives
`docs/r1/authorizations/g1b_t1_tasl_20261121.md` (15 bytes); the same call with `on_main=True` stops earlier on
`note field label must be 'ENGINEERING_ONLY'`.

---

## Appendix — exact candidate diff (`git diff -- r1/tests/test_t1_tasl_g1b.py`, uncommitted)

```diff
@@ -51,14 +51,26 @@ def launch_spec(tmp_path: Path, **over) -> dict:
     return spec
 
 
-def test_shipped_spec_validates_and_refuses_launch_until_filled():
-    loaded = T.validate_spec(copy.deepcopy(SPEC))
+def test_shipped_spec_validates_and_a_todo_still_refuses_launch(tmp_path):
+    """The shipped spec is filled, so it must pass launch validation; a copy with one TODO field reset must still
+    refuse, and launch must still refuse without the signed note on origin/main (the filled values stay unchanged)."""
+    loaded = T.validate_spec(copy.deepcopy(SPEC), launch=True)
     p = loaded["projection"]
     assert p["within_cap"] and p["estimate"]["total_gpu_hours"] < 100
     assert set(p["estimate"]["per_node"]) == set(T.T1_NODES)
     assert p["estimate"]["per_node"]["mlgym_houseprice"]["device"] == "cpu"
-    with pytest.raises(T.Stop):
-        T.validate_spec(copy.deepcopy(SPEC), launch=True)
+
+    todo = copy.deepcopy(SPEC)
+    todo["hosts"]["TASL-2"]["hostname"] = "TODO: hostname of TASL-2"
+    with pytest.raises(T.Stop, match="hostname"):
+        T.validate_spec(todo, launch=True)
+
+    note = tmp_path / "docs" / "r1" / "authorizations" / "g1b_t1_tasl_20261121.md"
+    note.parent.mkdir(parents=True)
+    note.write_text("approved: true\n")
+    with pytest.raises(T.Stop, match="not committed byte-identically on origin/main"):
+        T.launch(SPEC_PATH, note, "mlab_imdb", enable=True,
+                 on_main=lambda rel, raw: False)
```
