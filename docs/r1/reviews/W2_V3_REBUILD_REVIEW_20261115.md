Reviewed base: 88575d8b3064a4d06d485f63a7a1f2b4cc91edc9

# W2 v3 rebuild branch: W2-3 check — independent review record (15 November 2026)

Branch `mac-w2-v3-rebuild-20261115`, from `mac-w2-v3-prompt-20261114` @ `90d17fde`. Unit: `r1/scripts/w2_runs_total_check.py`, `r1/tests/test_w2_runs_total_check.py`, `reports/W2_V3_REBUILD_20261115.md`. Author queue item 4 of 15 Nov; the STOP the check defines is proposed, its adoption is a separate author decision. Three rounds by one freshly spawned independent reviewer agent (AI-assisted, Claude).
- Round 1 (`c1d36c4c`): changes requested (2 MAJOR: the STOP read as in force; no completeness check; 6 MINOR).
- Round 2 (`b90e1456`): accepted, with 4 non-blocking MINORs. (The round-2 request first named a wrong hash, `4f15cdd8`, then corrected it to `b90e1456`.)
- Round 3 (`88575d8b`, the 4 MINORs fixed): **accepted**, no findings; one optional wording tweak (paths across a summary with relative paths and recomputed ledgers) left as is.

Accepted commit (round 3, last): 88575d8b3064a4d06d485f63a7a1f2b4cc91edc9

The round texts are reproduced unchanged below.

---

Reviewed base: c1d36c4c442b8159028f755038c85d98db1e7e2c

# Review: W2 v3 rebuild branch, W2-3 check, round 1 (15 November 2026)

**Independent reviewer (Claude, freshly spawned; did not write the unit).**
Unit: worktree `/tmp/pb/wt/w2rb`, branch `mac-w2-v3-rebuild-20261115`, HEAD `c1d36c4c` (one commit on `90d17fde`). It adds three files: `r1/scripts/w2_runs_total_check.py`, `r1/tests/test_w2_runs_total_check.py` and `docs/r1/reports/W2_V3_REBUILD_20261115.md`.
I worked read-only on every repo and worktree. My scratch fixtures and probe script are in `/tmp/pb/rev_w2rb/` and are synthetic only. I read no real ledger, label or seed file. The worktree is still clean (`git status --short --ignored` prints nothing).

VERDICT: REVISE

The check is correct as code. It reads the identity-check summary exactly as `w2_execute_all_identity_check` writes it. The recomputation path uses the same `check_ledger`. On a ledger set that is complete and well-formed, the PASS/STOP decision is correct. I found no false STOP. Two things block acceptance. Both are fixed with a change of wording or a few lines of code:
1. The script's help text treats the proposed STOP as if it were already in force.
2. A PASS is reported as "exact on sweep 1", but the check never confirms that it saw every sweep-1 ledger.

## Findings

### 1. MAJOR: the script's help text applies the proposed STOP; the note contradicts its own header

- **Where:** `r1/scripts/w2_runs_total_check.py` docstring, which is also the argparse `--help` text (l. 16–17). Also `docs/r1/reports/W2_V3_REBUILD_20261115.md` §2 step 1.
- **Evidence:** The docstring says "exit 3 STOP (a ledger differs; report it to the author, do not rebuild that table)". That is an operative instruction, and the cluster agent will see it in `--help`. The note's header says "The STOP is not in force yet … Until then its output is a report to the author". But §2 step 1 says "the differing ledgers go to the author before any table is rebuilt". That is a hold on the whole rebuild, which is wider than the docstring's "that table". The request keeps adoption of this STOP as a separate author decision. The unit therefore needs to say "proposed" consistently in every place, and above all in the text the operator reads.
- **Fix:**
  - Docstring: "exit 3 STOP (proposed; adoption is the author's decision): a ledger differs; report it to the author."
  - §2 step 1: "If not, report the differing ledgers to the author. Whether this holds the rebuild (of those tables or of all tables) is the author's decision on adopting the STOP."
  - Optionally, have the JSON output carry `"stop_rule": "proposed"`.

### 2. MAJOR: a PASS does not establish "every sweep-1 ledger"; the note overclaims

- **Where:** `w2_runs_total_check.py` `evaluate`/`main` and its "every ledger" wording. Also note §2 step 1: "If it passes, the worker-run feature is exact on sweep 1."
- **Evidence:** The precondition in the stop-rule report is "every sweep-1 ledger has `worker_runs_total == 20`", over the 288 ledgers reported. The check verifies only the ledgers it is given. A summary of one ledger gives `PASS, ledgers: 1` (probe 8 in `/tmp/pb/rev_w2rb/probe.py`). `--summary` can be repeated, so a summary from a partial batch, or a missing batch file, also passes silently. Nothing ties the input to the sweep index or to the expected count.
- **Fix:** Add a required `--expect-ledgers N`. A mismatch with `len(results)` is a BAD_INPUT. A stronger option is to take the expected ledger set from the sweep index. Then change step 1 to `--expect-ledgers 288`, and say "PASS means each of the N given ledgers made exactly 20 worker runs". Alternatively, keep the code and make step 1 require the operator to confirm `ledgers == 288` against the sweep index before reading a PASS as the precondition. Add a test for a count mismatch.

### 3. MINOR: within-ledger duplicate rows can give a false PASS

- **Where:** `evaluate` uses only `worker_runs_total`.
- **Evidence:** A ledger whose 10 worker-run rows appear twice (budget indices 1,1,2,2,…,10,10) has `worker_runs_total == 20` and passes (probe 13). The identity summary does record `differences > 0` for it, but with an empty `rows_not_counting_one`. W2-3 ignores both fields. Under the harness this cannot happen: roots start fresh (`e1b_collect.py` l. 254–255) and there is one row per trial. That is why this is MINOR.
- **Fix:** Either option is enough:
  - In both paths, flag a ledger with `differences > 0` but no row that fails to count one. In practice that means `rows_not_counting_one` is empty.
  - In the recomputed path, also require `budget_index` to run exactly 1..rows. This needs a small helper; do not change `check_ledger`.

### 4. MINOR: the kind boundary assumes the sweep-1 trial budget and does not separate impossible rows

- **Where:** `evaluate`: `"short_at_trial_cap" if rows >= 2 * runs_total`.
- **Evidence:**
  - `rows` is the right measure. Each trial writes one row, including precheck and D25 rows, and verify re-runs stay inside their trial (stop-rule report §3–4). `2W = 40` matches `budget=runs * 2` (`e1b_collect.py` l. 261) for sweep 1.
  - The `>=` boundary behaves as intended: 39 rows → `short_before_trial_cap`, 40 → `short_at_trial_cap` (probe 2, test).
  - But `rows > 2W` is impossible under the harness, and the check still labels it `short_at_trial_cap` (49 rows, probe 3). The 2W factor is also specific to `e1b_collect`, while the docstring says "every Track P source ledger".
  - Only the kind label is affected. The status is still STOP, so there is no false PASS.
- **Fix:** Add a kind `rows_over_trial_cap` for `rows > 2W`, in both the short and the equal cases. Alternatively, report `rows > 2W` as a separate anomaly. State in the docstring that the 2W backstop is the sweep-1/`e1b_collect` budget. Optionally add `--trial-budget` with default `2 * runs_total`.

### 5. MINOR: the summary file is not passed through `refuse_sealed`; duplicate detection compares raw strings

- **Where:** `main` / `_results_from_summary`; `evaluate` duplicate test.
- **Evidence:**
  - A summary under `…/r1_sealed/` is read, and the check passes (probe 9). Ledger paths are refused, but the other input file is not.
  - Duplicates are found by comparing exact strings. The same file given as a relative and an absolute path counts as two ledgers: `PASS, ledgers: 2` (probe 1). This also inflates the count that finding 2 depends on.
- **Fix:**
  - Call `refuse_sealed(*map(Path, args.summary))` before reading.
  - Compare recomputed ledgers by `Path(p).resolve()`. Cluster paths taken from a summary cannot be resolved on another machine; say so in the docstring.

### 6. MINOR: W2-3 does not quite give the guarantee the 14 Nov prompt report assigns to it

- **Where:** `docs/r1/reports/W2_V3_PROMPT_20261114.md` l. 41–42: "a ledger that showed k ≥ W before a trial would print 'used 21 of 20' … the W2-3 check should make this impossible".
- **Evidence:** A ledger with 20 worker runs followed by trailing zero-run rows (precheck or D25) passes W2-3 (probe 4). Its trailing views print "used 20 of 20". The harness loop cannot produce this, because it stops as soon as `compute_budget.exhausted`. But neither the summary nor `check_ledger` records it.
- **Fix:** Record the limit in the note: W2-3 with harness semantics, not W2-3 alone, rules this out. Alternatively, in the recomputed path, check that the last row counts at least one run when the total is W.

### 7. MINOR: test gaps

- **Where:** `r1/tests/test_w2_runs_total_check.py`.
- **Evidence:**
  - `test_pass_from_identity_check_summary` does use a `STOP_DIFFERENCE` summary, which is the real sweep-1 shape: ledgers `l1` and `l3` have a leading precheck. It neither asserts that status nor checks the identity exit code 3, so the most important input case is covered only by accident.
  - These cases are not tested:
    - an identity summary with status `BAD_INPUT`, or a summary with non-JSON text around it (both give exit 2; I checked by probe);
    - `rows > 2W`;
    - an over-cap ledger computed through the recomputed path with a verify row (probe 5: STOP, `over_cap`);
    - two `--summary` files without overlap;
    - `--runs-total 0`;
    - a sealed summary path.
- **Fix:** Assert `json.loads(s.read_text())["status"] == "STOP_DIFFERENCE"` in the summary PASS test. Add the cases above, plus the tests that findings 2–5 call for.

### 8. MINOR (wording)

- The docstring says each summary result's "`worker_runs_total` and `runs_total` are read". `rows` is read too.
- The note §1 says ledgers are recomputed "with the same `check_ledger`. It … refuses `r1_sealed` paths before opening any file". The refusal is in `w2_runs_total_check.main`, not in `check_ledger`.

## What I verified

- **Scope.**
  - `git diff --name-status 90d17fde HEAD` shows three files added, none changed. No existing code is touched.
  - `90d17fde` descends from `87f67467` (stop-rule report) and `f21ab320` (accepted prompt unit).
  - On the branch, `FEATURIZER_VERSION = "c3_features/v3"` (`r1/c3/features.py` l. 244) and `PROMPT_VERSION = "trackp_prompt/v2"` (`r1/c3/train/types.py` l. 26).
  - The budget line is `Budget: trial {b}; worker runs used {used} of {runs_total}` (`serialize.py` l. 108). This matches the note and the 14 Nov answers (W2-1, W2-2).
  - The harness pin is at `a3fedbb`, as the note states.
- **Summary format.**
  - `w2_execute_all_identity_check.main` prints `{status: IDENTICAL|STOP_DIFFERENCE, ledgers, ledgers_with_differences, results[]}`. Each result has `ledger, rows, runs_total, differences, first_difference, rows_not_counting_one, worker_runs_total, worker_runs_over_cap`; on refusal the script prints `{status: BAD_INPUT, error}`.
  - The new reader accepts both success statuses. It needs `STOP_DIFFERENCE`, because 14 ledgers differ on sweep 1. It rejects `BAD_INPUT`.
  - It checks `ledgers == len(results)`, that `rows`/`runs_total`/`worker_runs_total` are ints (`type is int`, so bools are refused; I checked by probe), and that `runs_total` equals `--runs-total`.
- **Recompute against the summary.** The recomputed path calls the same `check_ledger(p, runs_total)` and takes the same three fields. It refuses sealed paths and wrong file names before opening, exactly as the identity check does. I compared a real summary with recomputation on the same synthetic ledgers by running both paths together. They agree, and listing a ledger in both is refused as a duplicate (the test covers this).
- **PASS/STOP logic.** `==` W is the stop-rule precondition. `< W` gives one of the two short kinds and `> W` gives `over_cap`, and every kind is STOP. A verify row raising the total over W gives STOP (probe 5). An empty ledger gives a short STOP. A row without `budget_index` gives exit 2.
- **Exit codes.** 0 PASS, 3 STOP, 2 bad input (JSON on stdout); argparse errors also exit 2. The exceptions caught match those of the identity check; `UnicodeDecodeError` is a `ValueError`.
- **Note against sources.**
  - Rebuild steps 2–3 match stop-rule report items 1 and 3 and §3 of the 14 Nov answers: rebuild under v3/v2, `FEATURIZER_VERSION` and prompt version in each manifest, no v1/v2 mixing, disclosure.
  - W2-4 (exam keeps the v1 line) is stated as still open.
  - The "STOP is proposed" header is present, but see finding 1.
- **Tests.**
  - The given command gives 30 passed (11 in the new file and 19 in `test_w2_budget_fields.py`), as the note states.
  - Each test does exercise what its name claims; the `ledger` helper writes rows that `row_worker_runs` counts as intended (precheck 0, `control_plane` skip 0, local 1).
  - The check also runs without `AR_HARNESS_ROOT`.

## Conditions for acceptance

- Finding 1: wording in the docstring and in note §2 step 1.
- Finding 2: an expected-count check (or an explicit operator step), and the "exact on sweep 1" sentence limited to what the check establishes.
- Findings 3–8 are at the author's discretion. Finding 3 and the `refuse_sealed` call in finding 5 are cheap and recommended.

---

Reviewed base: b90e1456acfe7db6010d4483d0283b67a9b9d077

# Review: W2 v3 rebuild branch, W2-3 check, round 2 (15 November 2026)

**Independent reviewer (Claude, freshly spawned; did not write the unit).**
Unit: worktree `/tmp/pb/wt/w2rb`, branch `mac-w2-v3-rebuild-20261115`, HEAD `b90e1456` (one commit on `c1d36c4c`; diff `git diff c1d36c4c b90e1456`). The coordinator first gave the head as `4f15cdd8`, which does not exist, and then corrected it to `b90e1456`, which is the branch head.

I worked read-only. Synthetic fixtures and probes are in `/tmp/pb/rev_w2rb/` (`probe2.py`, `scratch2/`). I read no real ledger, label or seed file. The worktree is clean (`git status --short --ignored` prints nothing). Against `90d17fde` the unit still only adds the same three files.

VERDICT: ACCEPT

Both round-1 MAJORs are resolved, and so are MINORs 3–8. I found no new BLOCKING or MAJOR problem. Four MINOR points remain (below). None gives a false PASS on a ledger set that the harness can produce.

## Round-1 findings: status

| R1 | Status | Evidence |
|---|---|---|
| 1 MAJOR (STOP in force in `--help`/note) | **Resolved** | The docstring and `--help` say "The STOP is proposed, not in force … until then exit 3 is a report to the author". `--help` no longer contains "do not rebuild". The JSON carries `"stop_rule": "proposed (adoption is a separate author decision)"`, asserted in `test_pass_from_identity_check_summary`. Note §2 step 1 now says a differing ledger would be reported "under the **proposed** W2-3 rule" and "Whether that holds the rebuild is the author's decision". The header is consistent with this. |
| 2 MAJOR (no completeness) | **Resolved** | `--expect-ledgers` is required and must be ≥ 1. A count that differs exits 2 (`test_wrong_ledger_count_is_bad_input`). Step 1 uses `--expect-ledgers 288` and claims only that "each of the 288 ledgers made exactly 20 worker runs, within the 40-trial budget". That holds, because `rows > trial_budget` is now a STOP on both paths (probes: 41 rows with 20 runs gives `rows_over_trial_budget` from both the summary and the recompute path). See residual M1 for the dedup caveat. |
| 3 (duplicate rows) | **Resolved** | Recompute path: `budget_index` must equal 1..rows; a test covers this. Summary path: `differences > 0` with an empty `rows_not_counting_one` is refused; a test covers this. The summary rule cannot be triggered by a legitimate ledger: `check_ledger` records a difference only when the running count ≠ b − 1, which needs either a row that counts ≠ 1 or an index anomaly. A real sweep-1 ledger with prechecks in the middle passes on both paths (probe). See residual M3 for the remaining summary-path case. |
| 4 (kind boundary) | **Resolved** | `--trial-budget` defaults to 2W and is documented as sweep 1's cap (`e1b_collect budget = runs * 2`). `rows_over_trial_budget` is checked before anything else, so a ledger with exactly W runs and too many rows is also a STOP. `short_at_trial_cap` now means `rows == trial_budget` exactly. See M2 for missing validation. |
| 5 (sealed summary; raw-string dedup) | **Resolved for the recompute path; partly for summaries** | `refuse_sealed` covers summaries and ledgers before any file is opened (`test_sealed_summary_refused`). Recomputed paths are `.resolve()`d: relative against absolute, and symlink against target, are both caught (probes). Summary paths are only `normpath`'d. See M1. |
| 6 (trailing rows) | **Resolved** | `rows_after_cap` on the recompute path (test with a precheck after the 20th run). The note's "Limit" paragraph says the summary path cannot detect this case and gives the reason. |
| 7 (tests) | **Resolved** | 19 tests in the file, 38 with `test_w2_budget_fields.py`, all pass with the given command. Each test claimed in note §3 exists and exercises what it says, including the STOP_DIFFERENCE assertion, BAD_INPUT and non-JSON summaries, `--runs-total 0`, two summaries, duplicated indices, verify over the cap (19 + 1 + 2r = 22), rows over the budget and rows after the cap. |
| 8 (wording) | **Resolved** | The docstring lists `rows`, `runs_total`, `worker_runs_total`, `differences` and `rows_not_counting_one`. The note credits the sealed refusal to `main`. |

## Residual findings (all MINOR; at the author's discretion)

### M1. MINOR: summary-path duplicates are found only lexically, so the note's dedup claim is broader than the code

- **Where:** `_results_from_summary` uses `os.path.normpath(r["ledger"])`; note §1, "a ledger listed twice, also across summaries and recomputed ledgers".
- **Evidence (`probe2.py`):**
  - A summary that lists one ledger under a relative and an absolute path gives `PASS` with `--expect-ledgers 2`.
  - A summary made with a relative path, plus the same ledger recomputed (which resolves to an absolute path), also gives `PASS` with `--expect-ledgers 2`.
  - In both cases one ledger is counted twice, so the count check can be met by a set that is short one distinct ledger.
- **Why only MINOR:**
  - Producing this needs the identity check, or the operator, to name the same file twice under different spellings.
  - On the intended path (one sweep-1 summary, no recompute) it would take a duplicated argument in the cluster's original identity-check run.
- **Fix, any one of:**
  - refuse relative ledger paths in summaries;
  - resolve summary paths that exist locally;
  - state the limit in the note (summary paths are compared as written, so give the identity check absolute paths).

### M2. MINOR: `--trial-budget` is not validated

- **Where:** `main`.
- **Evidence:** With `--trial-budget 0`, `-5` or `10` (below W = 20), a complete 20-run ledger is reported as `rows_over_trial_budget` (exit 3). The error is in the direction of STOP, never a false PASS.
- **Fix:** Refuse `trial_budget < runs_total` as bad input. There is no test for overriding `--trial-budget` either; one line would cover it.

### M3. MINOR: summary path, prechecks combined with duplicated indices

- **Evidence:** A ledger with one precheck followed by 10 worker-run rows written twice has 20 runs. Its summary entry has a non-empty `rows_not_counting_one`, so the round-2 refusal does not fire, and the summary path passes. The recompute path refuses the same ledger (`budget_index does not run`).
- **Why only MINOR:** The harness cannot produce this (fresh roots, one row per trial).
- **Fix:** Add a sentence to the note's "Limit" paragraph: on the summary path, index anomalies are detected only when no other row kind counts other than one.

### M4. MINOR (note wording)

- §2 step 1 says a differing ledger "would be reported to the author before its table is rebuilt". Under the proposed rule that is fine. The following sentence leaves the hold to the author, so this is consistent and needs no change.
- §1 could say that the `differences`/`rows_not_counting_one` refusal is a heuristic consistency check, not a full index check (see M3).

## What I verified (round 2)

- **Diff.** `git diff c1d36c4c b90e1456` touches only the three unit files. No existing code changed: `git diff --name-status 90d17fde HEAD` shows three files added.
- **Summary reader against the identity-check format.** It now also requires `differences` to be an int. The real identity output always has it (`check_ledger` returns `differences: len(diffs)`), so a genuine summary is never refused. I checked this with real `w2_execute_all_identity_check` output, IDENTICAL and STOP_DIFFERENCE, made on synthetic ledgers.
- **Recompute path.**
  - It calls the same `check_ledger` and takes `rows` and `worker_runs_total` from it.
  - It re-reads the rows through the identity module's `_rows`, so it reads the same four fields.
  - The 1..rows index check runs after sorting.
  - `rows_after_cap` counts the rows that start with `used >= W`. That is correct, including when a verify row crosses W, where `over_cap` takes priority because `n > W`.
- **`evaluate` order.** `rows > trial_budget`, then PASS at exactly W with no rows after the cap, then `rows_after_cap`, then the short kinds, then `over_cap`. Every kind other than PASS is a STOP.
- **Exit codes.** 0, 3 and 2 as documented. The count mismatch is raised after `evaluate`; a duplicate is reported first.
- **Refusals before opening.** `refuse_sealed` runs on all inputs before any summary is read or any ledger is stat'ed or opened.
- **Note.**
  - The rebuild steps still match the stop-rule report and the 14 Nov answers: v3/v2, `FEATURIZER_VERSION` and prompt version in each manifest, no mixing of v1 and v2, disclosure, W2-4 open.
  - Test counts (19 / 38) match my run.

---

Reviewed base: 88575d8b3064a4d06d485f63a7a1f2b4cc91edc9

# Review: W2 v3 rebuild branch, W2-3 check, round 3 (15 November 2026)

**Independent reviewer (Claude, freshly spawned; did not write the unit).**
Unit: worktree `/tmp/pb/wt/w2rb`, branch `mac-w2-v3-rebuild-20261115`, HEAD `88575d8b`. It is one commit on `b90e1456`, reviewed as `git diff b90e1456 88575d8b`.

Against `90d17fde` the unit still only adds the same three files; no existing code changed. I worked read-only and the worktree is clean (`git status --short --ignored` prints nothing). I read no real data.

VERDICT: ACCEPT

## Round-2 residuals: status

| R2 | Status | Evidence |
|---|---|---|
| M2 (`--trial-budget` not validated) | **Resolved** | `main` now refuses `trial_budget < runs_total` with exit 2. The check runs after the default 2W is applied, so the default always passes, and `trial_budget == runs_total` is allowed. The new test `test_trial_budget_override_and_validation` covers both cases. An override of 24 on a 25-row ledger gives a STOP of kind `rows_over_trial_budget`, and the output records `trial_budget: 24`. A value of 19 gives exit 2 with "at least runs_total". |
| M1 (summary dedup is lexical) | **Resolved (stated as a limit)** | The note's "Limits of the summary path" paragraph says ledger paths are compared as written, so the same file under two spellings in a summary counts as two ledgers. It also says the recompute path compares resolved paths. |
| M3 (prechecks plus duplicated indices) | **Resolved (stated as a limit)** | The same paragraph says such a ledger is not detected on the summary path, that the harness cannot produce it, and that the recompute path detects it. |
| M4 (heuristic wording) | **Resolved** | The `differences` test is now called "a consistency heuristic, not a full index check". |

## New findings

None at BLOCKING, MAJOR or MINOR level. One optional wording note:
- The paths limit names only the case of one summary.
- The same lexical comparison applies when a relative summary path and the same ledger recomputed are given together. The recomputed path is resolved to an absolute path, so the two do not match and are not caught as duplicates.
- One clause would cover it: "or across a summary and recomputed ledgers, unless the summary's paths are absolute".

## What I verified (round 3)

- **Diff.** `git diff b90e1456 88575d8b` contains only:
  - the two-line validation in `main`;
  - one new test;
  - the note's limits paragraph and test counts.
- **Tests.** The given command gives 39 passed: 20 in `test_w2_runs_total_check.py` plus 19 in `test_w2_budget_fields.py`. This matches note §3.
- **Validation order.**
  - `runs_total` and `expect_ledgers` must be positive.
  - Then the trial budget is set (default 2W) and refused if below `runs_total`.
  - Then the input-presence check, `refuse_sealed`, and reading.
  - No input file is opened before the arguments are validated.
- **Note.** The limits paragraph matches the code. The STOP is still marked proposed everywhere: header, docstring and `--help`, the JSON `stop_rule` field, and §2 step 1. The rebuild steps and W2-4 are unchanged from round 2.

---

