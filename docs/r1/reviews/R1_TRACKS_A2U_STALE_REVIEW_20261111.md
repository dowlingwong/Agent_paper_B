# R1-TRACKS-A2U-STALE — independent review record (11 November 2026)

Reviewed commit: fe651e589c2d6bafafc3a27e8eb7d8599845a7df (round 3, accepted; Track S paper pin stays `8237fd02b09ef2d28016a1c9f6acac3c35bb768b`)

Three rounds, each by a freshly spawned independent reviewer agent (AI-assisted, Claude). Rounds 1–2 cover the code fix, tests and PLAN row (round 2 accepted pin `8237fd02`); round 3 covers the docs-only commit that records test (c) on the five S0.4 committed-root ledgers. The round texts are reproduced unchanged below.

Open items carried to the operator relay (from rounds 2 and 3, not blocking):
- Run the TASL-2 precondition with `PYTHONDONTWRITEBYTECODE=1` and pytest from a separate scratch location (for example `pip install --target /tmp/pytest_scratch pytest` and `PYTHONPATH=/tmp/pytest_scratch`), never installed into the frozen venv.
- Compare the ledger SHA-256 values the TASL-2 run prints against the table in `docs/r1/reports/TRACKS_A2U_STALE_S04_CHECK_20261111.md`; any difference is a STOP.
- When quoting "40 trials identical", note that only the executed trials carry their run-time proposal (82 of 200 rows across the five roots); skip rows are rebuilt without one.


---

# Independent review: R1-TRACKS-A2U-STALE, round 1 (11 Nov 2026)

Unit: worktree `/tmp/pb/wt/a2u`, branch `mac-tracks-a2u-stale-20261111`, on top of Track S paper pin `d10b05b7`:
`324b7fa1` (fix + tests), `05dd35c0` (test tweak; proposed pin), `abeffd15` (PLAN §10 row + copy file).
Context: STOP 3 report `docs/r1/reports/TRACKS_PHASE3_20261109.md` §4–§11 and STOP scene
`results/r1/tracks/digits_mlp/s04/` on `mac/trackS-ops-20261030` (tip `8ae46a48`); harness pin `a3fedbb`
(`/tmp/pb/wt/harness-pin`). Reviewer: fresh independent reviewer, read-only. Scratch work only under
`/tmp/pb/scratch_rev_a2u/` (a `git clone --shared` of the worktree at `05dd35c0`). Nothing in the worktree was changed.

## What I verified (clean)

- **Commits.** All three by and committed by Dowling Wong <wangdowling@gmail.com>, with the trailers. No file is
  deleted. `git diff --stat d10b05b7 05dd35c0` touches only `r1/tracks/a2u.py` (+45/-8) and the new
  `r1/tests/test_tracks_a2u_stale.py`; `05dd35c0..abeffd15` touches docs only (`docs/r1/PLAN.md` +6, new
  `docs/r1/proposals/R1_TRACKS_A2U_STALE_PLAN_ROW_20261111.md`). The full SHA in the row
  (`05dd35c0c5d2d71a2f73ca9c17cd26e47d8ecb49`) is correct. That commit holds the fix and all tests, and the PLAN row
  is a later docs-only commit, as the row says.
- **Test claims reproduced.** In the scratch clone at `05dd35c0`, all of `r1/tests/test_tracks_*.py` give
  **178 passed, 1 skipped**. With `r1/tracks/a2u.py` replaced by the `d10b05b7` version: **5 failed, 173 passed,
  1 skipped**, and all 5 failures are in the new test file. In the worktree, the three named files give 32 passed,
  1 skipped (the skip is the S0.4 committed-root test).
- **Root cause matches the STOP scene.** I read all 13 `failures/*.json` tracebacks. Every one fails at E2
  (`_e2_detail`) with a stale `HIDDEN_UNITS` edit: 2048 vs 1024 at t11 ×3, t12 ×3 and t13 ×3; 4096 vs 2048 at
  t12 ×2 and t20 ×2. None fails at E1. In the harness pin, a
  precondition failure skips E1 (`campaign.py` ~l.1516–1526: E1 only runs in the `else` branch) but still calls
  the E2 hook (l.1862) with `provisional.delta_vs_best = None`. `keep_prior` is resolved only for VALID records
  (l.1750–1762), and `resolve_keep_prior` catches nothing.
- **Test (a) is genuine.** Running the old module under the test's scenario through the real `run_real_campaign`
  gives `ReplayError(" trial 2: stale edit: HIDDEN_UNITS is '2048', edit expects '1024'")` with the frames
  `campaign.py:1862 run_real_campaign → 283 _controller_hook → a2u 632 decide → 686 _e2_detail → 539 forecast →
  313 replay → features 352 featurize → 342 candidate`. Those are the same line numbers as the S0.4 s30000
  traceback. The old module is loaded faithfully: it is `git show d10b05b7:r1/tracks/a2u.py`, and every module it
  imports (`r1/c3/*`, harness) is unchanged between `d10b05b7` and `05dd35c0`.
- **Test (b)** asserts the exact E2 detail dict, using a probe whose `forecast` raises if called. This is correct.
- **Only the current proposal is excused.** The `try` in `replay` (a2u.py:324–329) wraps only the final
  `state.featurize(_proposal_edit(view.proposal), …)`. Prefix-row errors (`state.featurize` or `state.candidate`
  inside the loop) still raise a plain `ReplayError`. `test_an_inconsistent_ledger_prefix_still_raises` catches
  the "catch all `ReplayError`" mutation (below).
- **Valid-trial outputs cannot change (code argument).** The new code differs from the pin in only two places:
  (i) at E2 with Δ̂ None, the pin called `forecast` and then returned
  `{**detail, "reason": "no_features_or_no_comparison", "eligible": False}`. The new code returns the same dict,
  with the same keys in the same order, without the call. The pin's `forecast` has no side effects: `replay`
  builds a fresh `_LedgerState`, `for_group`/`kind` are dict lookups, and `log` is appended only in
  `_decide_e1`. (ii) Every other new branch runs only when `StaleProposalError` is raised, which is exactly where
  the pin raised. So **any trajectory on which the pin did not raise gives identical decisions, keep priors and
  logs**, and that includes the five committed S0.4 roots. `forecast_reason` is reset when `forecast` is entered.
  It is read immediately after the call (a2u.py:671, 719), and `_e2_detail` reads it before `keep_prior`
  calls `forecast` again, so its state cannot leak. The KEYED path runs `replay` first and is covered by the same
  catch. Other callers: `collect.fork_state` (a stale snapshot would now give `Stop("… has no forecast")` instead
  of a `ReplayError`; forks are taken only at eligible decisions, so this cannot happen). `predictive_intervals`
  skips rows without a metric. `simulate_controls` has its own `forecast`. The C3 controllers already catch
  broadly. No code anywhere reads the detail `reason` string.
- **Mutation check of the tests** (scratch copy of `a2u.py`, new test file run each time):

  | mutation | result |
  |---|---|
  | perturb `mu_n` by 1e-12 | 5 fail (all generated-campaign identity tests + S0.4-shape identity) |
  | extra key in E1 log entry | 5 fail |
  | E1 `"no_features"` → `"no_feature"` | 5 fail |
  | extra key in the E2 Δ̂-None dict | 6 fail |
  | catch every `ReplayError` in `forecast` | 1 fail (prefix test) |
  | undo the E2 reorder (keep the forecast catch) | 1 fail (direct probe test) |
  | swap key order of the E2 Δ̂-None dict | **0 fail** (see N1) |

- **Extra check of the policy-phase path** (not in the unit's tests): an `A2UController` with a real `A2UPrior`
  (g = 0.1σ), comparing `decide` **and `keep_prior`** of old against new on 4 generated campaigns that contain
  stale proposals. Result: 80 decisions and 40 keep priors identical, and the 32 places where the pin raised are
  "not eligible" in the fix. The logs are identical, without `sort_keys`, once the fix's `stale_proposal` entries
  are dropped. Script: `/tmp/pb/scratch_rev_a2u/prior_ident.py`.

## Findings

1. **BLOCKING — the PLAN row overstates the evidence on the five S0.4 committed roots and does not state what
   must happen before the pin is used.** `docs/r1/PLAN.md:615` (and the copy file, line 9) says:
   "…byte-identical to `d10b05b7` (…; the check on the five S0.4 committed-root ledgers runs with
   `TRACKS_S04_ROOTS=<run.work>/roots`)". A reader, in particular the operator who checks the row before the rerun
   (report §11, operator obligations), will take this as done. It was not run: the ledgers are only on TASL-2, and
   the test is skipped here. The author asked for (c) on those ledgers.
   **My assessment:** the evidence is adequate to accept the *code* now. The code argument above shows that a
   trajectory on which the pin did not raise cannot change, and the committed roots are such trajectories. The
   generated campaigns and my prior/keep-prior check back this up. Running the test on the real ledgers is still
   a cheap confirmation and was explicitly requested. It belongs in the record as an open precondition, not as
   evidence already in hand.
   **Fix:** reword the row (both copies) to say plainly:
   - the committed-root check (test (c)) has **not** been run, because the ledgers are on TASL-2 only;
   - byte-identity is currently shown on generated S0.4-configured campaigns plus the code-path argument;
   - **before the S0.4 rerun is launched**, the operator, with the paper clone checked out at `05dd35c0`
     (detached), runs read-only on TASL-2:
     `TRACKS_S04_ROOTS=<S0.4 run.work>/roots AR_HARNESS_ROOT=<harness checkout> PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider -rs r1/tests/test_tracks_a2u_stale.py -k s04_committed_roots`;
   - the required outcome is **5 passed, 0 skipped**, recorded in the rerun report (command, output, and the
     sha256 of the five `root_trials.jsonl`);
   - any failure or skip is a STOP.

   If pytest is not in the frozen TASL-2 venv, do not install it there. Use a separate venv, or a plain
   `python -c` call of `assert_identical_on_ledger` on each ledger. Note that
   the S0.4 work dir must not be written (pytest's tmp dirs go to `/tmp`; bytecode is suppressed).
   Extend report §11's operator obligations to match, or have the Lead relay it.

2. **SHOULD-FIX — an explicitly set `TRACKS_S04_ROOTS` that finds nothing is silently skipped.**
   `r1/tests/test_tracks_a2u_stale.py:34,239–248`: if the variable points at a wrong or non-existent directory,
   or at a directory without the five `<root_id>/root_trials.jsonl`, `_s04_ledgers()` returns `[]` and the test
   is **skipped**. On TASL-2 this looks like a pass to anyone who does not read `-rs`. Partial presence already
   fails, which is good. **Fix:** when `TRACKS_S04_ROOTS` is set in the environment, missing ledgers must fail
   (e.g. `pytest.fail` / an assert in `_s04_ledgers`). Keep the skip only for the default in-repo path.

3. **SHOULD-FIX — the second crash class that the forecast catch closes has no end-to-end test, and the row does
   not describe it.** With the E2 reorder in place, the `StaleProposalError` catch in `forecast`
   (a2u.py:559–565) can fire at runtime only for a proposal the harness precheck **accepted**. The precheck
   compares numerically (`values_equal`: "0.0001" == "1e-4"), while replay's `apply_edit` and the real
   `LocalWorker._apply_edit` compare loose strings. For example, `ALPHA = 1e-4` in `digits_mlp/train.py` with an
   LLM `old_value` of "0.0001". I reproduced this (scratch `/tmp/pb/scratch_rev_a2u/mask.py`):
   - **the pin crashes at E1**: `_decide_e1 → forecast → replay`, "stale edit: ALPHA is '1e-4', edit expects
     '0.0001'";
   - **the fix completes**: E1 `continue`, reason `stale_proposal`, not eligible; the worker then rejects the edit,
     so the row is `failed_invalid`; E2 is not eligible; the next trials replay normally, because invalid rows
     never apply their edit.

   This is a real benefit: it would otherwise be the next STOP of the rerun. But it is outside what the row
   describes (E2 only), and at E1 it means A2-U makes no decision for that trial (it is forced to `continue`) in
   policy phases. **Fix:** (a) add a campaign test of this shape: the pin raises at `_decide_e1`; the fix gives E1
   reason `stale_proposal`, the row is invalid, and the campaign completes. (b) Add one sentence to the row: the
   catch also covers proposals that pass the harness's numeric precondition but that replay and `LocalWorker`
   reject, at E1; such trials get `continue`, not eligible.

4. **SHOULD-FIX — test (c) checks only the S0.4 controller configuration, and never checks `keep_prior`.**
   `assert_identical_on_ledger` (test file l.185–212) uses `ExecuteNonRuleController(None, …)` (g = −∞, default
   keep rule, `keep_prior` unused). The new pin will also serve S0.5/S3/campaign, where `A2UController` with a
   prior and `keep_prior` (the E2 keep threshold the harness applies) are live. The code argument covers them, and
   my ad-hoc check passed. **Fix:** parametrise the helper over an `A2UController` with a non-trivial prior
   (as in `test_tracks_a2u.py` l.23–27) and compare `repr(keep_prior(view))` at E2 as well. Optionally
   use a randomised generator (more seeds, W = 40, mixed fresh/stale/no-op/format-mismatch edits) in place of
   4 rotations of one list.

5. **SHOULD-FIX — the row cites a review file that does not exist.** `PLAN.md:615` names
   "Independent review: `docs/r1/reviews/R1_TRACKS_A2U_STALE_REVIEW_20261111.md`", which is not on the branch.
   **Fix:** commit the accepted review at that path, or cite the actual review record (path + sha256), before the
   row is treated as binding. The commit subject "(draft, pending review)" is correct, so keep the row marked as
   draft until then.

6. **NOTE — key order is not checked** (`_dump` l.180–182 and the log comparison l.211 use `sort_keys=True`; the
   key-swap mutation passes). This is harmless for persisted bytes: the harness `CampaignEventStore` and
   `TrialAppendStore` both write `json.dumps(…, sort_keys=True)`, and `self.log` is record-only. The fix also keeps
   key order by construction. No change is needed. If the row keeps the words "byte-identical", it could say
   "as serialised (sorted keys)".

7. **NOTE — how to strengthen (c) from committed data.** `roots.jsonl` holds per-trial decision summaries
   (`index_value`, `margin`, `eligible`, `r`, `tau_pred`). It holds no edits, and `s04_rows.jsonl` holds only
   key/sign/Δ̂ of audited trials, so neither can be replayed without the ledgers. Nothing committed lets (c) run
   off TASL-2. What the committed data *can* add when (c) runs on TASL-2: also check that the new code's per-trial
   E1 `v_star` / `tau_pred` / `eligible` and E2 `eligible` / `margin`, recomputed from each ledger, equal the
   committed `roots.jsonl` decisions (sha `22c5c936…` in `s04/SHA256SUMS`). Compare only the fields that do not
   depend on the budget view, because `_views` builds a synthetic budget, so `r` differs. That ties the test's
   view reconstruction to what the controller actually returned in the run, rather than only proving old ≡ new.
   Optional; recommended if cheap.

8. **NOTE — placement and wording of the PLAN row.**
   - In this branch's older PLAN, the row sits at l.611–615, between the 28 Oct decisions table and the D1… table.
     The canonical PLAN (`trackS-ops-20261030`) appends R1-CACHEPROMPT-FALSE as a `### … — accepted` subsection
     *after* the D-table, at the end of §10 (l.638–642). The copy file should say where the row goes ("directly
     after the R1-CACHEPROMPT-FALSE subsection") and could use the same heading style.
   - The row refers to R1-CACHEPROMPT-FALSE, which does not exist in this branch's PLAN copy. The copy file
     explains this, which is acceptable.
   - "the manifest are unchanged" is ambiguous, because the rerun manifest's provenance will carry the new
     `paper_commit`. Say "manifest parameters (W, llm_cap, K, σ_node, g0, obs_inflation, memory mode,
     cache_prompt …) unchanged".
   - Correct as written: the cause; the author decision cited as "option (a)" with a pointer to §11, without copying
     the author's words; new directories; all ten instances from the start; the STOP scene untouched; no Phase 4.
     Liveness and fit_prior, which follow under the ruling, could be mentioned for completeness.

9. **NOTE — test (a) could pin the failure location.** It matches the message but not the frames. Asserting
   `_e2_detail` in the traceback of the pin's exception would make "same failure as S0.4" explicit. Optional.

## Before the pin is used (summary)

Fix 1 and 5, and preferably 2–4. Then the Lead or operator relays the TASL-2 read-only run of test (c) described
in finding 1, with the required outcome 5 passed / 0 skipped, recorded in the rerun report, before launching S0.4
into the new directories.

VERDICT: changes requested

---

# Independent review: R1-TRACKS-A2U-STALE, round 2 (11 Nov 2026)

Unit: worktree `/tmp/pb/wt/a2u`, branch `mac-tracks-a2u-stale-20261111` (rebuilt, not pushed):
`324b7fa1` (fix) → `05dd35c0` → `8237fd02` (tests answering round 1; **proposed pin**) → `f82ff376` (PLAN row and
copy file, docs only). The superseded tip is kept as `a2u-stale-prev-20261111` (`645b8aa6`, which contains
`abeffd15`). Same reviewer as round 1, read-only. The scratch clone in `/tmp/pb/scratch_rev_a2u/repo` was moved
to `8237fd02`. Nothing in the worktree was changed. Round 1: `/tmp/pb/reviews/REVIEW_A2U_STALE_round1.md`.

## Re-verified

- **Commits.** All four are authored and committed by Dowling Wong <wangdowling@gmail.com>, with trailers. No
  file is deleted. `r1/tracks/a2u.py` is byte-identical between `324b7fa1` and `8237fd02`, so the code verdict of
  round 1 carries over unchanged. `d10b05b7..8237fd02` touches only `a2u.py` and the test file.
  `8237fd02..f82ff376` touches only docs (`PLAN.md` +6 lines, copy file +9). The row text in `PLAN.md` and in the
  copy file is identical. The full SHA `8237fd02b09ef2d28016a1c9f6acac3c35bb768b` is correct, and that commit
  holds the fix and every test.
- **Test counts** (scratch clone at `8237fd02`, `PYTHONDONTWRITEBYTECODE=1`, harness pin `a3fedbb`):
  - new test file: **12 passed, 1 skipped**. This matches the coordinator's corrected count; the first note said 15.
  - new file together with `test_tracks_a2u.py` and `test_tracks_arm_invariance.py`: **35 passed, 1 skipped**.
  - all `r1/tests/test_tracks_*.py`: **181 passed, 1 skipped**. That is 178 + the 3 new tests.
  - new test file with the `d10b05b7` `a2u.py`: **6 failed**, all in the new file. The new E1-class test is among
    them.
- **Mutation re-run** (same mutations as round 1, plus two new ones):
  - every mutation that changes behaviour is caught;
  - a 1e-12 shift of `mu` in `keep_prior` fails 7 tests;
  - a change only to `keep_prior`'s `source` string fails 7 tests, including both prior-controller tests. That
    string never enters `decide`, so this shows the new `repr(keep_prior)` comparison is load-bearing;
  - swapping key order is still not caught, which is harmless (round-1 N1).

## Round-1 findings

1. **BLOCKING (row overstated the evidence on the S0.4 committed roots): resolved.** `PLAN.md` l.615 now
   separates *Evidence so far* (both crash shapes on the pin through the real harness path; byte-identity on
   generated campaigns for the S0.4 stand-in and for A2-U with a prior, including the served keep prior) from
   **Not yet run** (the five committed-root ledgers, not in the repository). It adds an explicit **precondition
   before the S0.4 rerun**:
   - TASL-2, read-only, clone at the new pin;
   - `TRACKS_S04_ROOTS=<S0.4 run.work>/roots`, `AR_HARNESS_ROOT` at the harness pin;
   - pytest from a separate environment, not installed into the frozen venv;
   - required result **5 passed, 0 skipped**;
   - the output, including the SHA-256 of each ledger, recorded in the rerun report;
   - failure, skip or collection error = STOP.

   The *Effect* sentence is now conditional on the precondition passing. This is honest and sufficient.
   I checked that the exact command works:
   - **5 generated ledgers under the five committed root names:** `-rs -s` prints
     "`<root>: 12 trials identical; ledger sha256 <hex>`" for each, then "5 passed, 12 deselected";
   - **one ledger removed:** collection error;
   - **`TRACKS_S04_ROOTS=/nonexistent`:** collection error.
2. **Should-fix (a set but empty `TRACKS_S04_ROOTS` was skipped): resolved.** When the variable is set, every
   missing ledger is an assertion at collection (test file l.280–286). The skip remains only for the default
   in-repo path.
3. **Should-fix (E1 numeric-equal class untested and undescribed): resolved.**
   `test_numerically_equal_old_value_crashed_the_pin_at_e1_and_now_becomes_an_invalid_trial` covers it:
   - the pin raises "stale edit: ALPHA is '1e-4', edit expects '0.0001'" with `_decide_e1` in the traceback;
   - the fix makes trial 2 invalid, with E1 reason `stale_proposal` and both E1 and E2 not eligible;
   - trial 3 is eligible again.

   The row has the matching sentence. The test's worker is the fixture's `ConfigMetricWorker`, which uses
   replay's `apply_edit`. The real `LocalWorker._apply_edit` (`_values_loosely_equal`) uses the same loose
   string comparison, so "the worker rejects the edit" holds for the real worker too.
4. **Should-fix (no prior, no keep_prior): resolved.** `_a2u_with_prior` builds an `A2UController` with a
   `KindPrior` and g = 0.0004. `assert_identical_on_ledger` compares `repr(keep_prior(view))` on E2 views with a
   comparison, for both controller factories. Two parametrised campaigns.
5. **Should-fix (cited review file did not exist): resolved.** The row now says the file is committed on this
   branch when accepted. The coordinator should commit this review (or both rounds) at
   `docs/r1/reviews/R1_TRACKS_A2U_STALE_REVIEW_20261111.md`, on top of `f82ff376`. This is docs-only, and the pin
   stays `8237fd02`.

Round-1 notes:
- **Placement:** the copy file now says where the row goes (directly after the R1-CACHEPROMPT-FALSE section).
  Done.
- **Manifest wording:** "manifest unchanged" is replaced by "the rerun manifest records the new paper pin". Done.
- **Test (a):** now asserts the `_e2_detail` frame. Done.
- **Key order:** still unchecked, accepted as harmless.
- **Comparing against committed `roots.jsonl`:** not adopted. This was optional and is not required.

## New notes (non-blocking)

1. **"Separate scratch environment" needs a concrete recipe for the operator.** A fresh venv would lack the
   frozen venv's numpy/scipy/scikit-learn and the editable harness, and the test imports them. Old and new code
   would still run in the same environment, so identity is not at risk, but the import would fail and stop the
   run. The simplest recipe leaves the frozen venv untouched:
   `pip install --target /tmp/pytest_scratch pytest`, then
   `PYTHONPATH=/tmp/pytest_scratch <frozen venv>/bin/python -m pytest …`.
   The Lead can put this in the relay; the row does not need to change.
2. **Add `PYTHONDONTWRITEBYTECODE=1` to the precondition command** if "read-only" is meant strictly. Without it,
   pytest writes `__pycache__` (including assertion-rewrite bytecode) into the clone. These files are gitignored
   and the S0.4 ledgers are only read, so this is cosmetic. `-p no:cacheprovider` is already there, and tmp dirs
   go to `/tmp`.
3. **Report §11's operator obligations do not yet list the precondition.** The row carries it, so the Lead should
   relay it with the pin. On TASL-2, `_old_a2u` needs `d10b05b7` in the work clone; it is there, since that was
   the previous pin.

## Verdict

The code is unchanged from round 1 and correct. The tests now cover both crash classes, the prior and keep-prior
path, and a fail-closed TASL-2 ledger check. The PLAN row states the evidence and the open precondition
accurately, and binds pin `8237fd02`. Before the pin is used: commit this review on the branch as the row says,
and relay the TASL-2 precondition (with notes 1–2) to the operator.

VERDICT: accepted

---

# Independent review: R1-TRACKS-A2U-STALE, round 3 (11 Nov 2026)

Unit: the single new commit `fe651e58` (`fe651e589c2d6bafafc3a27e8eb7d8599845a7df`) on branch
`mac-tracks-a2u-stale-20261111` (worktree `/tmp/pb/wt/a2u`, on top of `f82ff376`). It records test (c), the S0.4
committed-root ledger check. Pin under review: `8237fd02`. Harness pin `a3fedbb` (`/tmp/pb/wt/harness-pin`).
Reviewer: a fresh independent reviewer with no involvement in rounds 1 and 2, read-only. Scratch:
- a detached worktree `/tmp/rev3_a2u` at `8237fd02`, created for this review and removed at the end;
- scripts in `/tmp/rev3_scratch/`.

Nothing under `/tmp/pb/wt`, `/tmp/pb/repo` branches or `/tmp/pb/s04roots` was changed. Both worktrees are still
clean, the branch tip is still `fe651e58`, and `SHA256SUMS` still verifies after the run.
Rounds 1 and 2: `/tmp/pb/reviews/REVIEW_A2U_STALE_round1.md` and `/tmp/pb/reviews/REVIEW_A2U_STALE_round2.md`.

## What I verified (clean)

- **Commit.** Authored and committed by Dowling Wong <wangdowling@gmail.com>, with the trailers. Nothing is deleted.
  - `git diff --name-only 8237fd02 fe651e58` lists only `docs/r1/PLAN.md`,
    `docs/r1/proposals/R1_TRACKS_A2U_STALE_PLAN_ROW_20261111.md` and the new
    `docs/r1/reports/TRACKS_A2U_STALE_S04_CHECK_20261111.md`.
  - `git diff 8237fd02 fe651e58 -- r1/` is empty. The test file is identical at both commits.
  - So the pin `8237fd02` stays valid, and the code verdict of rounds 1 and 2 carries over unchanged.
- **Ledger integrity (item 1).** In `/tmp/pb/s04roots`, `sha256sum -c SHA256SUMS` gives OK for all five files.
  The SHA-256 values and byte sizes match the report's table exactly:

  | root | bytes | lines |
  |---|---|---|
  | s30001 | 134,487 | 40 |
  | s30004 | 108,221 | 40 |
  | s30006 | 83,731 | 40 |
  | s30007 | 109,043 | 40 |
  | s30009 | 98,898 | 40 |

  The files are mode `0444`. Every row's `campaign_id` matches its root. The `node_root` paths point into
  `/home/dowling/r1_tracks/scratch/digits_mlp/s04/roots/<root_id>/`, which is consistent with the S0.4 run tree.
  The five root ids are exactly the committed roots in `roots.jsonl` of the STOP scene (`8ae46a48`).
- **Test (c) rerun (item 2).** In the scratch worktree at `8237fd02` I ran the exact command given. Result:
  `collected 17 items / 12 deselected / 5 selected` and **5 passed, 12 deselected, 0 skipped**. Each root prints
  "40 trials identical; ledger sha256 …", and every printed hash equals `SHA256SUMS` and the report. The output
  matches the report's transcript line for line, apart from the timing.
- **What "identical" compares, and whether a skip could look like a pass.** Test file l.183–302.
  - **What is compared.** For each ledger row, `_views` rebuilds an E1 view and an E2 view: the ledger prefix,
    `current_best_before`, the proposal from `_row_edit`, `delta_vs_best` and `decision`. The budget is
    synthetic. Two `ExecuteNonRuleController`s are built, one from `git show d10b05b7:r1/tracks/a2u.py` and
    one from the fix. The test requires `json.dumps(asdict(decision), sort_keys=True)` to be equal for every view.
    At E2 views with a Δ̂ it also requires `repr(keep_prior)` to be equal.
  - **How the logs are compared.** The logs are dumped with `sort_keys` and compared as whole lists.
    `crashed == 0` and `same == 2·len(rows)` are both asserted, so on these ledgers no view relies on the
    "the pin raised, so the fix is not eligible" escape.
  - **No silent skip.** With `TRACKS_S04_ROOTS` set, `_s04_ledgers()` either returns all five paths or fails an
    assertion at collection, which is a collection error and not a skip. So the `skipif` cannot fire. `-rs`
    printed no SKIPPED line.
- **Extra check: provenance of the copies against committed data** (`/tmp/rev3_scratch/xcheck.py`, `dig.py`). The
  repository holds no committed hash of the ledgers, so the SHA-256 values cannot be tied to the run tree from the
  repo. Instead, I recomputed the fixed controller's per-view `v_star` (E1) / `m_hat` (E2), `margin`, `tau_pred`
  and `eligible` from each copied ledger. I compared them with the committed STOP-scene `roots.jsonl`, which was
  written by the run itself.
  - **Executed rows** (`worker_mode` not `control_plane`): **164 of 164 views match** (40/36/22/36/30 per root),
    with a tolerance of 1e-12 relative. Every view that the committed record marks eligible is also eligible in
    the recomputation. The committed `eligible_e1/e2` summaries (19/19, 17/17, 10/10, 17/17, 14/14) are
    reproduced.
  - **Control-plane skip rows:** all the differences are on these rows (see N1).
  - **Conclusion.** The copies are the ledgers of the committed S0.4 run, independently of the experiment agent's
    `SHA256SUMS`, and the test's view reconstruction reproduces what the controller returned in the run for
    every executed trial. This also covers round-1 note 7, which was optional.
- **Extra check: A2-U with a prior on the real ledgers.** I ran `assert_identical_on_ledger(rows,
  factory=_a2u_with_prior)` on all five ledgers. It gives same = 80, crashed = 0 for each, so decisions, log and
  served keep prior are identical with a real prior and g = 0.0004 as well.
- **PLAN row and copy file (item 3).**
  - **Rows match.** The `| R1-TRACKS-A2U-STALE …` row in `PLAN.md` and in the copy file is byte-identical
    (`cmp`).
  - **What changed.** The only change from `f82ff376` replaces "**Not yet run:** the same check on the five S0.4
    committed-root ledgers, which are not in the repository." with the *Committed-root check, run 11 Nov*
    sentence. The root ids, "5 passed, 0 skipped", "40 trials each" and the SHA-256 prefixes (`14d586ee`,
    `a8dbbd98`, `cf384352`, `8ea9e20b`, `71c358c6`) are all correct.
  - **No overclaim.** The sentence says the check used copies, not the run tree, and that "the TASL-2 run below is
    still required". The **Precondition before the S0.4 rerun** is unchanged: TASL-2, read-only, 5 passed /
    0 skipped, output in the rerun report, any failure, skip or collection error = STOP. *Effect* is still
    conditional on the precondition.
  - **Author's words not copied.** The row still cites "option (a) of STOP 3" by pointer, and the copy file's
    preamble still says the ruling is "not copied here".
- **Report.** `TRACKS_A2U_STALE_S04_CHECK_20261111.md`:
  - The opening paragraph and "What this does not cover" both say plainly that the copies are not the run tree
    and that this is not the TASL-2 precondition run.
  - It quotes no author statement.
  - The SHA table, the command (which includes `PYTHONDONTWRITEBYTECODE=1`) and the transcript are accurate.
  - "the test file is identical at the branch tip" is true.

## Findings

No blocking or should-fix findings for `fe651e58`.

1. **NOTE (N1): about 59% of the ledger rows enter test (c) without their run-time proposal.**
   - **What I found.** 118 of the 200 rows (20/22/29/22/25 per root) are `control_plane` skip rows with no
     `structured_edit`, so `_views` builds them with `proposal=None`. In the run, E1 on those rows saw an actual
     proposal: `roots.jsonl` holds a non-null `index_value`/`tau_pred` for them, while the recomputation gives
     `None`. E2 was not called for them in the run, but the test still builds and compares an E2 view.
   - **Effect.** For those rows, "40 trials identical" compares the old and new code on a view that is not the
     run's view. The 82 executed trials (164 views) are the ones that match the run.
   - **Why it does not affect correctness.** By the round-1 code argument, the fix cannot change any view on
     which the pin did not raise. In the run, the pin did not raise on those skip rows.
   - **No change needed.** If the TASL-2 rerun report quotes the result, it could say "40 trials (N executed)".
     Optional.
2. **NOTE (carried over from round 2), still open but not part of this commit:**
   - **Review file not yet committed.** The row cites `docs/r1/reviews/R1_TRACKS_A2U_STALE_REVIEW_20261111.md`
     ("committed on this branch when accepted"). That file is still not in the tree at `fe651e58`. Commit the
     accepted review records (rounds 1–3) there before the row is treated as binding. This is docs-only, and the
     pin stays `8237fd02`.
   - **Precondition command is not strictly read-only.** The row's precondition command still lacks
     `PYTHONDONTWRITEBYTECODE=1` (round-2 note 2), although this commit's report uses it. Add it in the operator
     relay, together with the round-2 pytest-in-`--target` recipe (round-2 note 1).
3. **NOTE: SHA-256 values cannot be traced to the run tree from the repository.** No committed artifact lists the
   ledger hashes, so the report's table rests on the experiment agent's copy plus my content cross-check against
   `roots.jsonl` above. The TASL-2 precondition run, which prints the hashes from the run tree itself, closes
   this. Its printed hashes should be checked against this report's table. If they differ, that is a STOP.

## Verdict

`fe651e58` is docs-only and keeps pin `8237fd02` valid. It records test (c) accurately:
- I reproduced it: 5 passed, 0 skipped, with matching hashes;
- the ledgers verify, and their contents agree with the committed S0.4 `roots.jsonl` on every executed trial;
- the row and the report claim nothing beyond copies, and keep the TASL-2 precondition before the rerun.

Verdict: accepted
Accepted commit: fe651e589c2d6bafafc3a27e8eb7d8599845a7df
