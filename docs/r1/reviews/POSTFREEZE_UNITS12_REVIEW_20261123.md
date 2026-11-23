# Independent review (tier E): post-freeze reads amendment, code units 1 and 2 (23 November 2026)

**AI-assisted (Claude, independent reviewer subagent, 23 Nov 2026).** The reviewer did not write the code under review.

**Verdict: accepted after minor corrections.**

No MAJOR finding. Unit 1 fits A1 and A2 exactly as the existing code does, bitwise and in row order. Unit 2's fields
and checks are complete against A§9 and leave every existing check unchanged. The MINOR findings are one gap in the
signature check (M1), a CLI that does not fail closed (M2), a missing toolchain record that the bitwise check of unit 3
will depend on (M3), and three runbook or report points about ordering and contingencies (M4–M6). M1–M3 change unit
files, so the sha256s in the unit report §4 change, and A§13 must take the sha256s of the corrected, merged files.

**What was reviewed.** Branch `mac-postfreeze-units12-20261123`, worktree `/home/claude/wt/units12`, head `d808381a`,
base `14f19a09` (an ancestor of `origin/main` @ `577bee4f`; `git merge-tree` shows the branch merges into it with no
conflict). The diff is `git diff 14f19a09 d808381a`: `r1/c3/arms_constants.py` (new), `r1/tests/test_c3_arms_constants.py`
(new), `r1/c3/arms_freeze.py`, `r1/tests/test_c3_arms_freeze.py`, `docs/r1/runbooks/DEEPTHOUGHT_T0_ARMS_RUNBOOK_20261123.md`,
and `docs/r1/reports/postfreeze_units12_20261123/UNITS12_20261123.md`.

**Specification used.**
- The amendment draft (`a8cf7882`): A§3, A§8, A§9, A§11, A§12 items 22–23, A§13.
- The sign-ready copy `C3_SWEEP2_PREREG_AMENDMENT_POSTFREEZE_20261123.md` (`7cf39c74`). This branch exists locally only;
  `git fetch` shows no such remote branch.
- The amendment review's m2 and m3.
- The PLAN rows R1-POSTFREEZE-READS and R1-POSTFREEZE-READS-CHOICES (`280915ee`).
- The D.3 draft (`a24a55bf`): §5.0–§5.3, §10, §12.
- On the base commit: `offline_eval.py`, `arms.py`, `gate_input_builder.py`, `labels.py`, `release.py`, the arms
  readiness report, and the A3 run report (`docs/r1/reports/arms_a3_20261123/`).

## Findings

### MAJOR

None.

### MINOR

**M1. `signed_utc` is not checked.**
- *Where:* `r1/c3/arms_freeze.py:871–873` (`_check_amendment_files`); runbook II-P7 (line 147).
- *Problem:* The sign-ready A§13 adds `signed_utc: <filled when published on main>` as the signature time, separate from
  `frozen_utc`. The check requires only `signed_by` and an ISO `frozen_utc`. I simulated a committed copy of the
  sign-ready file with `frozen: true`, both unit sha256s and a valid `frozen_utc`, leaving `signed_utc` as the
  placeholder. It **passes**. So do `signed_utc: yesterday` and a `signed_utc` later than `frozen_utc`. II-P7 does not
  mention `signed_utc` either.
- *Fix:* Require `signed_utc` in the same `YYYY-MM-DDTHH:MM[:SS]Z` form, with `signed_utc <= frozen_utc`. Add the
  matching test cases. Add `signed_utc` to II-P7 (b).

**M2. The CLI is not "always on"; it does not fail closed.**
- *Where:* `r1/c3/arms_freeze.py:1201`, `:1228`, `:1238–1239`; unit report §2 and §7 ("always on in the CLI").
- *Problem:* `check` takes `constants_root = --constants-root or --artefact-root`. Without both, the constants-file
  comparison is skipped. `--no-git` now also skips the committed-amendment check: before this change it only skipped
  commit ancestry. `render` without `--constants-root` skips the constants comparison. In every case the summary still
  says `"pass": true`, with `constants_files_rehashed: 0` or `amendments_rehashed: 0`. The runbook guards this: it names
  the flags, says "Do not pass `--no-git`", and gives the expected counts. The code does not. The record always carries
  `rule_arms` and `amendments` now, so a CLI pass without both file checks is never a complete pass.
- *Fix (either):*
  - (a) `check` and `render` refuse unless a constants root resolves, and the committed-amendment check gets its own
    opt-out flag, separate from `--no-git`.
  - (b) The CLI exits non-zero, or reports `pass` as partial, when either count is 0.

  Correct the report's wording either way.

**M3. The constants file does not record the toolchain, but unit 3's bitwise re-check depends on it.**
- *Where:* `r1/c3/arms_constants.py:199–217` (`document`), `:265–299` (`parse`); runbook step 4b (line 180, `$PY`).
- *Problem:* The vectors are sums of `labels.soft_label` outputs. Those come from `scipy.stats.norm.cdf`
  (`labels.py:23`, `:55`) and NumPy reductions. A§8 unit 3 recomputes `fit_a2` and `ConstantPrior` after step 6 and
  must match the record **bitwise**; a mismatch loses A1's rows and (d), with no fallback. The file records no Python,
  NumPy or SciPy version, whereas each A3 entry carries `toolchain`. Run I did not use the interpreter that the runbook's
  `$PY` (I-P2) names. It used a separate venv, `/work/dwong/arms_t0_20261123/venv` (Python 3.13.15, NumPy 2.4.4, SciPy
  1.17.1; `A3_RUN_20261123.md`). Step 4b does not say which interpreter to use. I did not test whether the bits change
  across SciPy or NumPy versions (see "Not verified"). The point is that nothing records the versions unit 3 would need.
- *Fix:*
  - Add `toolchain: {python, numpy, scipy}` to the constants file, written from the running interpreter and required by
    `parse`.
  - In step 4b, name the interpreter: the Run I arms venv, or the one the author designates.
  - Note that unit 3 must run with the recorded versions.

**M4. Runbook and report: when to freeze A§13, and that the amendment never changes once the record pins it.**
- *Where:* runbook revision note (lines 17–29) and II-P7 (line 147); unit report §6 point 2.
- *Problem:* II-P7 requires the frozen amendment at `$C2`, the commit that Run II's fresh clone takes at II-P1. So A§13
  must be frozen on `main` **before Run II starts**, binding `$C2`'s `arms_freeze.py`. But II-P4 has STOPs whose remedy
  is "a reviewed schema and checker change": ARMS-A5CKPT C changes `a5_pin_binding` in `arms_freeze.py`. If that
  happens after A§13 is frozen, the frozen amendment binds an obsolete `arms_freeze_sha256`, and editing a frozen
  document has no stated procedure. A second consequence is not stated anywhere. `_check_amendment_files` re-hashes the
  amendment at HEAD against the record's pin. So once the record pins it, the amendment file can never change, and any
  later edit makes every re-run of `check` fail. That includes filling the units 3–5 sha256s. The "by the amendment"
  route of R1-POSTFREEZE-READS-CHOICES for units 3–5 is therefore open only until the freeze; after it, only CONFIRM-type
  rows remain.
- *Fix:* Add to the revision note or II-P7, in this order:
  1. The author rows ARMS-A5CKPT, ARMS-A5FOLD and ARMS-SECONDARY are on `main`, and any `arms_freeze.py` change they
     require is merged.
  2. A§13 is filled with the merged sha256s and frozen on `main`.
  3. Run II clones `$C2`.

  Also say that the amendment file is never edited after the record pins it, and that units 3–5 are then bound by
  CONFIRM-type rows.

**M5. Runbook step 4b must stay T0-only, because Run I was.**
- *Where:* runbook lines 183 and 187–188 ("`[--release-root g5=… --t1 $W/t1.json]`", "the same file Run I used").
- *Problem:* Run I (`cfe59c26`) ran without `--t1` (`A3_RUN_20261123.md`: "T0-only, no `--t1`"; "No T1 rows"). The
  record's T1 set drives `required_arms` (`A3@loso:<suite>`) and the A3 entries' `inputs` (`g5`). Neither exists from Run
  I, so a T1 fit in step 4b produces a record the checker refuses, which is a late STOP. "The same file Run I used"
  implies omission only by inference.
- *Fix:* State that the record is T0-only because Run I was (`cfe59c26`), so step 4b omits the bracketed G.5 arguments
  and `t1` is `{"suites": {}, "modes": [], "d3_k6": false, "instances": []}`. A T1 record needs a new Run I and the
  author.

**M6. The A§12 item 22–23 contingency: with unit 2 on `main`, no record can be written without the frozen amendment.**
- *Where:* `r1/c3/arms_freeze.py:554–557` (`REQUIRED_TOP`), `:1228` (`render` always passes `verify_committed=True`);
  runbook lines 20–22 and 147 ("The record is never committed before that (A§12 item 22: …)"); unit report §6 point 1.
- *Problem:* A§12 item 22 (settled) says that if units 1–2 are not bound by the record, "A1's rows and the record-based
  input of (d) are lost (listed as omissions)". Item 23 (settled) says that if the amendment is not signed before the
  record, "(a)–(d) are not computed". Both describe a record that goes ahead without the amendment. Once unit 2 is merged,
  `amendments` and `rule_arms` are required, and `render` requires a committed, frozen, signed amendment. If the
  amendment misses R1-ARMS-FREEZE-CUTOFF (20 Dec 2026), the arms-frozen record cannot be written, and therefore neither
  can the primary verdict, without a reviewed code change. Waiting fits R1-POSTFREEZE-READS ("signed before the
  arms-frozen record"). But the runbook cites item 22 for a STOP that item 22 does not state, and the dependency is not
  shown to the author.
- *Fix:* In the runbook and the report §6, say plainly that once unit 2 is on `main` the record depends on the frozen
  amendment, and that the item-23 path needs an author row plus a reviewed change to unit 2. Correct the item-22
  citation. No code change is asked for here.

### NIT

**N1.** `AMENDMENT_PATH_RE` (`arms_freeze.py:568`) accepts any `docs/r1/authorizations/*.md`, including the `_DRAFT_`
file. II-P7's glob `C3_SWEEP2_PREREG_AMENDMENT_POSTFREEZE_*.md` matches both the draft and the signed file once both
are on `main`. The draft is refused anyway (`frozen: false`). Name the exact file in II-P7, or refuse `_DRAFT_` in the
path check.

**N2.** Two gaps between the constants file and the record:
- `_check_constants_files` (`arms_freeze.py:782–816`) does not compare the constants file's `gate_input_builder.sha256`
  with the record's builder pin, which the preregistration binds.
- `parse` (`arms_constants.py:265–299`) does not validate `gate_input_builder`, `rules`, `row_order`, `t0_nodes`,
  `d3_nodes`, or the per-node `tier`, `source` and `rows`.

Both are cheap to add.

**N3.** Under `verify_git`, the fitter's `sha256` is not cross-checked against its `code_commit`
(`git show <code_commit>:r1/c3/arms_constants.py`). Today the two are consistent only by construction in `_code_commit`.

**N4.** `arms_freeze_sha256` is compared with the working file `repo/r1/c3/arms_freeze.py` (`arms_freeze.py:866`),
not with the committed bytes (`release._committed`) or the running module. Because of this binding, the record can be
re-checked only at a commit whose `arms_freeze.py` is the bound one. Say so for later reviewers.

**N5.** II-P7 (line 147) should say three more things:
- the exact `frozen_utc` form the checker accepts: `YYYY-MM-DDTHH:MM[:SS]Z`, with no offset and no fraction (a
  simulated `+00:00` and a simulated `.5Z` are both refused);
- that nothing may follow the fenced block;
- that the `status:` line is not checked, but should be updated at the freeze for readers. It currently reads "code
  sha256 fields pending".

**N6.** Runbook lines 204–205: "if it pins this step's file, the same path" cannot happen when D.3 is signed at `$C2`,
because step 4b's file does not exist yet. A pinned D.3 file is an earlier file. The checker compares it by vectors
only, and its bytes differ whenever its `fitter.code_commit` differs. Reword.

**N7.** Unit report §5 gives "575 passed and 7 skipped" for the other `test_c3_*` files. I could not reproduce that
count. My run covers the 35 `r1/tests/test_c3_*.py` files other than the two unit test files and the five `test_c3_*`
neighbours the report names. It gives 362 passed, 6 skipped, 11 failed and 34 errors, of which 6 are collection errors. The report's own "28 errors" plus six uncollectable
files also makes 34. My run on a git clone checked out at `14f19a09` gives exactly the same result and the same
failure set. The report's claim that the failures are pre-existing therefore holds; only the passed and skipped counts
differ. State which files were counted.

**N8.** Two D.3 alignment points to add to the report's three (§1):
- The record checker accepts a D.3 constants file only of the schema family `r1_c3_rule_arm_constants/*`, with
  per-node `A1` and `A2` under `nodes` (`arms_constants.py:241–254`). The D.3 text must require that format, or pin
  unit 1's file itself.
- D.3 §5.0 also pins `configs.json` (`de6d63b5…`). Unit 1 neither reads nor records it, which is harmless for A1 and A2.
  The D.3 text should drop it for G2's A1/A2 part, or unit 1 should record it.
