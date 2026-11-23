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

## Check 1 — Unit 1 (`r1/c3/arms_constants.py`)

**Same fit as the existing code, bitwise and in row order: yes.**
- **A2 is `gate_input_builder.fit_a2` itself** (`arms_constants.py:155`). The unit builds `fit_a2`'s item form and calls
  it, so no second implementation of the A2 fit exists.
- **A1 is `arms.ConstantPrior` on `fit_rows(items)`** (`:161`). `fit_rows` (`:138–143`) is a verbatim copy of `fit_a2`'s
  comprehension (`gate_input_builder.py:299–301`); only the iterable's name differs. A test checks that `RulesPrior` on `fit_rows` reproduces
  `fit_a2` bitwise (`test_c3_arms_constants.py:125–126`). This is A§3.1's A1 constant: the weighted mean soft label over
  exactly the rows `fit_a2` passes to `RulesPrior`, with no-ops included and duplicates and divergent labels absent
  (`soft is None`).
- **Row construction.** Rows come from `arms_freeze.training_rows` (`arms_freeze.py:183–246`), which uses the builder's
  `_instance`, `_label_ok` and `_seeds` and the same `soft_label(..., "pooled_node", k_label)` call
  (`arms_freeze.py:236` = `gate_input_builder.py:283`). Weights are 1.0; no-ops get the inert label.
- **Row order.** Items are sorted by `proposal_id` across sources (`arms_constants.py:134`), as `_prepare` sorts
  (`gate_input_builder.py:292`). `arms._wmean` (`arms.py:79–81`) sums in row order, and the test compares the item order
  with the builder's dev rows (`test_c3_arms_constants.py:128–129`).
- **Bitwise equality, under test.** The test compares against `fit_a2` on `_prepare`'s rows, built from the full label
  and evaluation blocks of a synthetic world: the step-6 shape, with partial (k = 4) and divergent labels, no-ops and
  duplicates. It compares raw float64 bytes before the JSON round trip (`:121–122`) and after it (`:320–321`). Shuffled
  input changes no bit (`:135–144`).

**Population: as specified.**
- **Data scope.** Dev label block of the receipted train/dev partitions only, through `load_traindev` →
  `release.traindev_labels` with the receipt sha256 pinned (`open_partition` re-checks the receipt, the release row and
  the P3 membership of every row). Table rows and label rows are filtered to P3 dev instances first (`dev_only`, `:101–114`).
- **Nodes.** Exactly the eight T0 nodes plus the frozen T1 nodes (`:194`). A stray node is refused (`:151–153`); so is
  a required node without an A2 constant, with no pooled fallback (`:158–160`).
- **Memory modes.** Both T0 modes; T1 its declared mode(s). Other modes on dev rows are refused (`:188–191`), as the
  builder refuses them at step 6.

**Refusals: all present.**
- **Test labels, evaluation fields, evaluation seeds.** `check_label_rows` refuses all three. Table rows with label or
  evaluation values are refused by `check_table_rows`. Train and test table rows are dropped, not used.
- **Sweep 1.** Refused three times: CLI `:323–324`, `fit_sources` `:181–182`, `fit_items` `:122–123`.
- **Wrong table.** The table must equal the receipt's `inputs.proposals_sha256` and, for sweep 2,
  `SWEEP2_PROPOSALS_SHA256 = 379b17ca…97d9` (`:333–338`). That pin equals the committed receipt copy's
  `inputs.proposals_sha256` (`RECEIPT_sweep2_traindev_v2.json`; its sha256 is `de95b218…`, as in the runbook).
- **Unreceipted data.** Refused by the receipt pin.
- **Dirty checkout.** `_code_commit` (`:304–310`) requires the committed fitter and no tracked changes. This runs before
  any data is opened.
- **Raw, test and evaluation paths** are refused by name, including the output path.

**Pinnable output: yes.** One JSON file, written once, through `_dump` (sorted keys, `allow_nan=False`); `document`
calls `parse` before returning. It holds no timestamp, so the same inputs at the same commit give the same bytes. CLI
stdout carries only the path, sha256, node names, commit and fitter sha256; no vector is printed.

**"Seven D.3 vectors bitwise unchanged when other nodes are added": confirmed.**
- *Argument.* `ConstantPrior.fit` and `RulesPrior.fit` compute each node's vector as `_wmean(P[idx], w[idx])` over that
  node's rows, in their relative order (`arms.py:93–95`, `:111–113`). The only cross-node quantity, `pooled`, is never
  used here.
- *Unit test.* `test_per_node_vectors_do_not_change_when_other_nodes_are_added` builds a seven-node sweep-2-only world
  (G2's population) and compares it with eight T0 plus two T1 nodes. In that world other nodes' rows sort between a
  node's two memory modes.
- *My own check.* A property check on synthetic rows: 300 random worlds with 2–10 nodes, random interleaving, no-ops,
  and k_label of 3, 4 or 5. The all-node fit and the node-alone fit gave 0 per-node vectors differing in any byte, for
  both priors.

**The drafter's note on D.3 §5.0 (s = σ/√5 vs `k_label`): correct.**
- D.3 §5.0 (draft line 191) says "s = σ̂_node/√5".
- The builder passes each label's `k_label` (`gate_input_builder.py:283`), and `labels.soft_label` uses
  s = σ_pooled/√k_label, with σ_pooled defaulting to the row's σ_node (`labels.py:87–90`). A partial label (k = 4) gets
  σ/√4, and the unit follows `fit_a2`; the synthetic world includes k = 4 labels and equality still holds.
- D.3 §5.0's own required test ("equal `fit_a2`'s") settles the question for `k_label`, so it is a D.3 text fix, not a
  unit fix. For sweep 2 the difference is probably empty: the committed audit report says all 10,640 seed runs
  succeeded (0 bad runs), and the receipt counts only `audit` labels (dev 422, no `divergent`). Both point to
  k_label = 5 throughout. That is an inference; the label rows were not opened.
- The report's other D.3 points also stand: LADDER η is not in this unit, and the D.3 text must name this unit (eight
  T0 plus T1) as G2. See N8 for two more.

## Check 2 — Unit 2 (`r1/c3/arms_freeze.py`)

**Against A§9: complete.**

| A§9 item | Where | Status |
|---|---|---|
| `amendments`: path, sha256 "as frozen (A§13)", PLAN row R1-POSTFREEZE-READS looked up in PLAN | `_check_amendments` (`:697–714`), looked up in the same `author_rows` set as the `REQUIRED_DECISIONS` rows; frozen state checked by `_check_amendment_files` | present |
| `rule_arms.A0`: `r1.c3.offline_eval.rho`, no constants | `:726–727` | present |
| `rule_arms.A1`/`A2`: per-node vectors for eight T0 plus frozen T1 nodes; fitter path, sha256 and commit; constants path and sha256; receipts (sweep 2; G.5); fit population; A1 "no rule layer; no verify offline" | `_check_rule_arms` (`:717–769`); one fit for both (`:759–762`); fitter commit added to `code_commits` | present |
| `rule_arms.d3_constants`: null or path and sha256; the seven D.3 nodes equal it bitwise | `:763–768`, `_check_d3_vectors` (`:819–831`) | present |
| `arms` unchanged; A0 and A1 not arms | `required_arms` untouched; adding `A0` or `A1` to `arms` is refused as undeclared (tested) | present |

A§8 unit 2's required tests are all present:
- a record without the new fields (the parametrized `REQUIRED_TOP` test, 45 cases);
- an absent PLAN row;
- a wrong constants sha256;
- vectors differing from the constants file by one ulp;
- a pinned D.3 file differing for a D.3 node by one ulp, and a D.3 file lacking a D.3 node.

**No behaviour change on existing paths.**
- Every existing check is byte-for-byte unchanged in the diff; the new calls come after the arm loop.
- The intended changes are:
  - the two new required keys;
  - two new summary keys;
  - the fitter commit joining `verify_git`;
  - `render` now requiring the committed signed amendment;
  - `check` now running the amendment check unless `--no-git` (M2).
- No module outside the tests calls `check_record`; `release.py` only re-hashes the record file (`release.py:357`).

**The final-block parser.** `_amendment_block` (`:834–846`) reuses `release._final_block`:
- HTML comments are stripped.
- Exactly one fenced block may hold a line starting `frozen:`, and that block must end the file.
- Every line must match `([a-z_0-9]+): (.*)`, and keys must be unique. Values are stripped.

I confirmed that a blank line inside the block, a duplicate key, and any text after the block are each refused.

**Required values and signature** (`_check_amendment_files`, `:849–875`):
- `frozen` = `true`, exactly;
- `plan_row` = the entry's row;
- `amends` = `docs/r1/authorizations/C3_SWEEP2_ANALYSIS_PREREG_20261121.md sha256 aa1a961b…7cc5` (`PREREG_PATH`,
  `PREREG_SHA256`);
- `constants_fitter_sha256` = the record's fitter sha256;
- `arms_freeze_sha256` = the checkout's `arms_freeze.py` (see N4);
- `signed_by` present and not starting with `<`;
- `frozen_utc` matching `\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?Z`.

The amendment is read with `release._committed`: the working file must equal HEAD, and the record's sha256 must equal
it. `signed_utc` is not checked (M1).

**The sign-ready file's A§13 parses.** I ran `_amendment_block` on `7cf39c74`'s file. It parses, with keys `amends,
plan_row, status, frozen, constants_fitter_sha256, arms_freeze_sha256, descriptive_rows_sha256,
dispersion_estimate_sha256, c1_rates_sha256, open_items, signed_by, signed_utc, frozen_utc`. `amends` matches. As
committed, the check refuses it for `['arms_freeze_sha256', 'constants_fitter_sha256', 'frozen']`, which is correct at
signing. The draft's A§13 also parses and is refused (`frozen: false`).

**What must change in A§13 at freeze time for `check` to pass.** These edits come from a simulation: the sign-ready
file was committed to a temporary git repository and passed through `_check_amendment_files`.
1. `frozen: false (frozen when …)` → `frozen: true`. Nothing may follow `true`; a kept parenthetical is refused.
2. `constants_fitter_sha256: <pending: unit 1>` → the bare 64-hex sha256 of the merged `r1/c3/arms_constants.py`. An
   annotated value is refused.
3. `arms_freeze_sha256: <pending: unit 2>` → the bare 64-hex sha256 of the merged `r1/c3/arms_freeze.py` at `$C2`.
4. `frozen_utc: <pending: …>` → `YYYY-MM-DDTHH:MM[:SS]Z`. `+00:00` and fractional seconds are refused.
5. `signed_utc` should be filled. Today a placeholder passes (M1).

Lines that need no change:
- These pass as they are: `amends`, `plan_row: R1-POSTFREEZE-READS`, and `signed_by: Dowling Wong (author), by
  publishing this file on main`.
- These are not checked: `status`, `open_items`, and the units 3–5 lines, which may stay `<pending: unit n>`.

The block must remain the last thing in the file, with no blank or free-text line inside it.

**Keys the signing step must not rename:** `amends`, `plan_row`, `frozen`, `constants_fitter_sha256`,
`arms_freeze_sha256`, `signed_by`, `frozen_utc`, and `signed_utc` if M1 is adopted. Renaming `frozen_utc` to
`frozen_at` was refused in the simulation. Keys must stay lowercase with a single `: ` separator. No other fenced block
anywhere in the file may contain a line starting `frozen:`.

**Procedural note on R1-POSTFREEZE-READS-CHOICES.** This is not a unit finding. The sign-ready `open_items` line cites
R1-POSTFREEZE-READS-CHOICES, which is on `280915ee` and `09e54139` but **not on `origin/main` @ `577bee4f`** (checked by
grep). By the amendment's own rule (header: cited rows must be on `main` before signing), it must reach `main` first.
R1-POSTFREEZE-READS itself is on `origin/main`.

## Check 3 — m3, the PLAN fixture row, and opt-in checks

- **The fixture extension is acceptable.** The test diff removes exactly two lines, the end of the `PLAN` string and the
  end of `_record()`, and re-adds them extended. No test body or assertion changed. Adding the R1-POSTFREEZE-READS row
  to the module's `PLAN` fixture is the minimum that lets the new field's required PLAN lookup succeed. It is a
  fixture, like `_record()`, so it fits m3's intent: existing tests unchanged, fixtures extended.
- **The opt-in Python keywords are acceptable for the API.** `constants_root` and `verify_committed` default off. No
  non-test module calls `check_record`, and the drafter's reason holds: existing tests that pass `artefact_root` or
  `release_roots` and edit `label_tables` in their body would otherwise fail.
- **The CLI is not safe as written.** An operator path can skip both file checks, and the result still reads
  `"pass": true`:
  - omit `--artefact-root` and `--constants-root` on `check`;
  - pass `--no-git`;
  - run `render` without `--constants-root`.

  The runbook prevents this (explicit flags, "Do not pass `--no-git`", expected counts), and an independent review of
  the record follows. Still, the code should fail closed (M2).

## Check 4 — Runbook (II-P7, step 4b, step 5)

**Correct.**
- **Commands.** Step 4b's fitter command, its expected output (`code_commit` = `$C2`; `fitter_sha256` = A§13), the seal
  (`SHA256SUMS` before `chmod`), the `postfreeze-fields` command, the step-5 merge snippet (it asserts no key overlap and
  re-dumps floats with Python's round-trip `repr`), and `render --constants-root $A` / `check --artefact-root $A` all
  match the code.
- **Expected counts.** "`constants_files_rehashed` 1 (2 with D.3), `amendments_rehashed` 1" matches the code.
- **Variables.** `$R2`, `$T2`, `$A`, `$AM` and `$D3C` are all defined.
- **Receipt.** The sweep-2 receipt `de95b218…` is the one Run I used. The checker ties the constants file's sources to
  `label_tables.sweep2`, and the A3 entries' `inputs` to the same, so A1/A2 and A3 come from one partition.

**Order relative to the A3 entries already frozen in Run I (`cfe59c26`): no conflict.**
- Run I's A3 entries carry `code_commit` `89899f76`. They are checked by the unchanged A3 branch of `check_record`.
  II-P2 already records an `arms_freeze.py` diff between `$C` and `$C2`.
- A3 was trained before the amendment is signed. A§11 discloses that read, and A§0 leaves arm training unchanged.

**Missing or unclear:**
- the freeze order and the amendment's immutability once pinned (M4);
- that step 4b stays T0-only (M5);
- the contingency of items 22–23 (M6);
- `signed_utc` in II-P7 (M1);
- the interpreter for step 4b and the versions recorded (M3);
- the exact `frozen_utc` form and the trailing-text rule (N5);
- the exact amendment file name (N1);
- the D.3 "same path" wording (N6).

## Check 5 — Tests

Run in this sandbox: Python 3.13.18, NumPy 2.5.3, SciPy 1.18.1, LightGBM 4.7.0, with `pytest -q -p no:cacheprovider`.
- `r1/tests/test_c3_arms_constants.py`: **11 passed**.
- `r1/tests/test_c3_arms_freeze.py`: **54 passed**. Together: 65 passed.
- The neighbours the report names (`test_c3_arms_eval`, `test_gate_input_builder`, `test_fold_analysis`,
  `test_c3_release`, `test_c3_offline_eval_guard_order`, `test_c3_prior_model`, `test_c3_analysis_guard`): **148
  passed, 1 skipped**, as reported.
- The other 35 `test_c3_*` files, with `--continue-on-collection-errors`:
  - On the branch: 11 failed, 362 passed, 6 skipped, 34 errors. Six of the errors are collection errors in the six
    files the report names. The 31 non-collection errors and failures come from `AR_HARNESS_ROOT` missing, or from
    pre-existing dry-run failures.
  - On a `git clone` of the repository checked out at `14f19a09`: the same counts, and an **identical failure set**
    (`diff` of the sorted FAILED/ERROR ids is empty).
  - An earlier `git archive` export of `14f19a09` had no `.git`, so git-dependent tests also failed there. It is not
    used for the comparison.

The worktree stayed clean after the runs.

## Check 6 — What the code reads, and whether an earlier read could satisfy it

**Unit 1 reads:**
- the receipted train/dev partition: train rows are only membership- and format-checked, then dropped;
- the pinned table: test rows' in-campaign fields, membership-checked and dropped; D.3 §5.0 allows this;
- the P3 split file;
- committed code, through git.

It opens no raw label block, test partition, evaluation block or run log, and refuses such paths by name. Its outputs
and error messages carry no label value. The vectors go only into the constants file, as A§9 requires.

**Unit 2 reads:** the constants file(s) and the committed amendment. It reads no label rows.

**Can an earlier read stand in for a declared one? No.**
- The constants file is a deterministic function of the receipted dev labels at a given fitter sha256. A copy produced
  earlier, for example right after merge and before A§13 is frozen, would pass the record check. A§11 explicitly allows
  this: "not a test read; allowed before the record". The runbook still orders step 4b after II-P7.
- Nothing in units 1–2 computes or accepts a test-time quantity.
- The one downstream dependency is unit 3's bitwise re-check, which needs the environment recorded (M3).

## What was verified, and how

- Code read in full: `arms_constants.py`; the `arms_freeze.py` diff, plus `check_record`, `training_rows` and the
  loaders; `arms.py`; `gate_input_builder.py` (`_prepare`, `fit_a2`, `build`); `labels.soft_label`; `release.py`
  (`_committed`, `_final_block`, `prereg_frozen`, `author_rows`, `open_partition`, `traindev_labels`,
  `builder_source`); `dataset.load_table`.
- The test diffs, read line by line. The A§8 required tests were mapped to test functions.
- The unit report's five sha256s: recomputed with `sha256sum`; all equal. The base `arms_freeze.py` is `aaea25fd…c72f`,
  as stated.
- The parser and signature check: run directly on both amendment files (draft `a8cf7882`, sign-ready `7cf39c74`), plus
  12 simulated freeze-time edits in a temporary git repository (scripts outside the repository; results under Check 2).
- Per-node invariance: a property check on 300 random synthetic worlds (Check 1).
- The committed sweep-2 receipt copy: only its `counts`, `inputs` and `outputs` fields were read, and its sha256
  computed.
- The PLAN rows were checked by grep at `14f19a09`, `d808381a`, `09e54139`, `280915ee` and `origin/main`.
- Mergeability: `git merge-tree` against `origin/main` @ `577bee4f`.

## What was not verified

- **Real data.** By rule, the fitter was not run on real data, and no label block, partition, table or evidence
  directory was opened. Whether sweep 2's dev label block contains partial labels (k_label < 5) is inferred from counts
  only.
- **Version stability.** Whether the A1/A2 bits are stable across SciPy or NumPy versions (deepthought: NumPy 2.4.4,
  SciPy 1.17.1; this sandbox: 2.5.3 / 1.18.1) was not tested. M3 asks for the versions to be recorded, not for this
  question to be answered.
- **Harness-dependent tests.** The six harness-dependent test files could not be collected here (`AR_HARNESS_ROOT`
  missing).
- **Deepthought paths.** `$R2`, `$T2`, `$A` and the Run I venv were not checked: no remote host was used.
- **The full CLI run.** The `check` CLI with `verify_git` against a real `origin/main` was exercised only through the
  unit's tests (a temporary repository) and the monkeypatched CLI test.
