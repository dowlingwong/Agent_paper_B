# Independent review of W2 budget fields (mac-w2-budget-20261109), 9 Nov 2026

Freshly spawned independent reviewer (Claude subagent; did not write the unit). Status: rounds 1–2 changes requested; round 3 **accepted** at `5db5b67d`. Rounds copied verbatim below.

---

## Round 1

# Independent review — W2 budget fields from worker runs (round 1)

**Reviewer:** independent AI reviewer (Claude). I did not write this unit. Engineering review only.
**Unit:** `/tmp/pb/wt/w2`, branch `mac-w2-budget-20261109`, HEAD `81924e14` on `origin/mac-int-20261107` (`a15300ca`).
**Spec:** proposal `SEQUENTIAL_POLICY_REVISION_20261104.md` (branch `docs/seq-revision-04nov`) §3.6 and §4.2 W2; runbook `MAC_OVERNIGHT_RUNBOOK_20261109.md` §5.
**Harness semantics checked against:** `/tmp/pb/wt/harness-pin` @ `a3fedbbd` (`budget.py` ComputeBudget; `campaign.py` `_skipped_record` l.600, `_run_verify` l.685–813, `_precondition_failure_result` l.912, `_structured_failure_result` l.1007, live loop l.1303–1990, `_record_from_worker_result` l.2308; `snapshot.py` `_complete_captured_trial` l.840–1000, resume l.1095–1135).
No sweep or label table and no seed 7001–7010 file was read. The worktree was not modified (`git status` clean). Scratch files are in `/tmp/pb/scratch_rev_w2/`.

## What I ran

- The listed suite: `test_w2_budget_fields`, `test_c3_featurizer_online`, `test_c3_features`, `test_c3_env`, `test_trackp_serialize`: **49 passed, 14 skipped**. The skips are 13 `test_trackp_serialize` cases (no `huggingface_hub`) and 1 `test_c3_env` case (no `lightgbm`). I ran the 5 skipped serialize tests that need no real tokenizer, `test_reads_only_the_featurizer_inputs` among them, with a whitespace tokenizer (`scratch_rev_w2/run_ser.py`). All 5 pass, so `worker_mode` is covered by `ROW_FIELDS`.
- `test_c3_rule_controller.py`: passes. `test_trackp_exam_synthetic.py`: has 1 failure, the one already known before this unit (`budget_line(b, W)` output is unchanged).
- **Independent byte-identity check against the base commit** (`scratch_rev_w2/cmp.py`). For each of 30 seeds × {`worker_mode` "local", absent} I generated an execute-all ledger. About 15 % of its discarded rows were turned into `failed_invalid` (the worker ran but gave no metric). I then compared the base `r1/` (`git archive HEAD~1`) with HEAD on `features_hash`, on the full `render_text(prompt)` and on `prompt.meta`. **All 1068 views match exactly, 1008 of them with a prompt.** Sanity check: when the invalid rows are marked `local_precheck`, 588 of 1068 views differ. So the comparison really does use the two code versions.
- **Online vs replay with precheck, verify and skip** (`scratch_rev_w2/online.py`). I built harness `TrialRecord`s through `build_control_view` for this sequence: kept, then `local_precheck` failed_invalid, then discarded with verify r = 2, then a `control_plane` skip, then the proposal. Online and replay give the same `features_hash`, with `budget_frac_left = 1 − 6/20 = 0.7` (1 + 0 + 5 + 0 runs).
- Identity script on scratch inputs. A plain execute-all ledger exits 0. A ledger with a gap exits 3. A `.gz` ledger exits 2 (BAD_INPUT). A path under `r1_sealed` gives an **uncaught RuntimeError, exit 1** (see F5).

## Harness charging vs `row_worker_runs` (path by path)

| Path | Harness charge | Ledger row | `row_worker_runs` | OK |
|---|---|---|---|---|
| Executed trial (success / failed / timeout) | 1 (`campaign.py`:1683) | `worker_mode` = worker mode | 1 | yes |
| Worker raises (crash) | 1 (exception caught, then `consume_worker_run`) | worker mode | 1 | yes |
| E1 controller skip / E1b rescreen skip | 0 | `control_plane` (`_skipped_record`) | 0 | yes |
| D25 inactive-key skip | 0 | `control_plane` | 0 | yes |
| Precheck rejection (before E1, or recheck after revise) | 0 | `<mode>_precheck` | 0 | yes |
| E1 revise and then executed | 1 (the revision costs an LLM call, not a run) | worker mode, `control.revision` | 1 | yes |
| E2 verify | 2 r, charged on the **same row** (`_run_verify`; `control.verify.r`) | `extra.control.verify.r` | +2 r | yes |
| Resumed E1 execute / E2 verify (`snapshot.py`) | as in the live loop | as in the live loop | same | yes |
| **Track S `ghost` / `ctrl_only` E1 arm** (`snapshot.py`:941–983) | **1** (unless precheck) | `_skipped_record` → `control_plane`, `control.arm` = ghost/ctrl_only | **0** | **no (F1)** |
| Ungoverned mode, failed_invalid | 1 | row dropped from the ledger | — | not counted (note F9) |
| `mark_pending_failed` recovery | unknown (process died) | `worker_mode` param (default `unknown_worker`) | 1 | acceptable (F9) |

Leakage: the count is updated only in `_LedgerState.observe` on prefix rows, after `featurize_view`'s `FeatureLeakError` guard (`budget_index < b`). `serialize_view` sums over the same `view.ledger_prefix` after that guard. The harness E1 view holds `existing_records + records`, so the current row is not appended yet and its own verify cannot be seen. **No leak of the current row.**

Other consumers (grep of `r1/`): `env.py`, `arms.py`, `prior_model.py` and `dataset.py` read stored table features and recompute nothing. `control.py` and `r1/controllers.py` use the harness `view.budget["worker_runs_remaining"]`, which is consistent. `e1b_collect.point_features` uses the snapshot `compute_budget_state`, a separate and consistent feature. `exam_synthetic` calls `budget_line(b, W)` with the output unchanged. `accounting.campaign_usage` is unchanged and agrees with the new rule except on rows without `worker_mode` (F7). **No consumer now disagrees on execute-all tables.**

## Findings

### Blocking

None.

### Should-fix

**F1. Ghost / ctrl_only rows are under-counted. The docstring's "harness ComputeBudget semantics" claim is false for them.** `r1/c3/features.py`:300–321; report l.13.
In Track S resume arms `ghost` and `ctrl_only`, the worker runs and the run is debited (`snapshot.py`:952). But the ledger gets `_skipped_record` with `worker_mode="control_plane"`, `action="skip"` and `arm` set (`snapshot.py`:859–866, 971–983). `row_worker_runs` therefore counts 0. This is the exact case the Track S reviews raised against the old feature: rev-3 review mi-3 and Track S runbook H7 found it "identical in skip and ghost". With W2 it is *still* identical in skip and ghost. For `ctrl_only` it is also an online/replay mismatch: online, the controller sees the shadow record with the worker's mode (count 1), while a replay of the ledger counts 0. Track S currently computes its own budget features from `worker_runs_remaining`, so nothing in D.3 is wrong today. But the function claims a property it lacks.
*Fix:* in `row_worker_runs`, treat `control.get("arm") in ("ghost", "ctrl_only")` on a `control_plane` row as 1 run. Document that a ghost whose proposal failed the precheck was debited 0, and that this is visible only in `branch_shadow.jsonl`. Add a test with a ghost row and a ctrl_only row. At minimum, state the exception in the docstring and the report.

**F2. The serialized budget line still says "trial b of W", which is false for skipping arms.** `r1/c3/train/serialize.py`:100–105.
Proposal §3.6 calls the whole line "trial b of W (max(W − (b − 1), 0) worker runs left)" false for every skipping arm. W2 fixes only the parenthesis. Under `c3_budgets` the trial budget is the LLM cap (≥ W), so A5/A6 in D.3 can be shown "Budget: trial 25 of 20 (4 worker runs left before this trial)". That is still wrong information, just less of it.
*Fix (keeps execute-all bytes):* add an optional `trial_budget` to `NodeContext` (default `runs_total`) and render "trial {b} of {trial_budget}". Or keep the text and put the issue in the author question list as an explicit M13 template decision. Either way, the report should say that this part of the §3.6 problem remains.

**F3. The execute-all test checks one line of the prompt, not prompt bytes.** `r1/tests/test_w2_budget_fields.py`:96–98.
W2 §4.2 asks that "the serialized prompts are byte-identical". The test asserts `old_line(b) in prompt.state.splitlines()` and compares only `budget_frac_left`, not the other features. My scratch comparison against the base commit shows full byte identity, so the code is right, but the committed test would not catch an accidental change elsewhere in the prompt (e.g. from adding `worker_mode` to `ROW_FIELDS`).
*Fix:* compare the whole `render_text(prompt)` and `prompt.meta`, and the whole features dict, with an "old" computation. Either monkeypatch `S.budget_line` to the pre-W2 two-argument form and set `worker_runs_used := b − 1`, or check in a small golden file generated at `a15300ca`. Also add `failed_invalid` rows on which the worker ran (`worker_mode` "local", no metric) to `execute_all`: real execute-all sweeps contain failed runs, and they must count 1.

**F4. Version justification in the report is wrong. `FEATURIZER_VERSION` should be bumped.** `r1/c3/features.py`:239; report l.29.
The report says the versions are kept "so that execute-all tables and prompts stay byte-identical, including their version fields". `FEATURIZER_VERSION` is not in any table: it is recorded only in online `control_decision` details (`control.py`:296, 429). The F2 precedent (`TRACK_H_25OCT_HANDOFF.md`:49) bumped to `c3_features/v2` for a change of the same kind ("recorded in online decision events only, never in tables"; tables byte-identical). Leaving v2 makes any archived online C3 campaign with skips, prechecks or verify impossible to reproduce under its recorded version.
*Fix:* bump to `c3_features/v3`; the table bytes do not change. `PROMPT_VERSION` does sit in `prompt.meta`, so keeping `trackp_prompt/v1` is defensible until the Track P template freeze. Leave it as the author question, and correct the report's wording for both.

**F5. Identity script: a sealed path gives an uncaught traceback and exit 1. Gzipped ledgers are rejected.** `r1/scripts/w2_execute_all_identity_check.py`:57–66, 62, 28.
(a) `refuse_sealed` raises `RuntimeError`, which the `except` tuple does not catch. The path is still refused before it is opened, which is correct, but the exit code (1) is not one of the documented 0/2/3, and there is no test. *Fix:* catch `RuntimeError` and print `{"status": "REFUSED_SEALED"}` with exit 2 (or a distinct code), and add a test.
(b) The table builder globs `*/root_trials.jsonl*` (`dataset.py`:49–52, 201), which includes `.gz`. The script requires `name == "root_trials.jsonl"` and reads plain text, so it cannot check gzipped sources. *Fix:* accept `root_trials.jsonl(.gz)` and read through `r1.c3.features.read_jsonl` (which also calls `refuse_sealed`).
(c) A STOP should say *why* a ledger differs. *Fix:* add to each difference the `worker_mode` / `control` kind of the row that broke identity (precheck, control_plane skip with or without `reason: inactive_key`, verify), so the author can decide per cause.

### Notes

**F6. The changed fixture in `test_c3_featurizer_online.py` is justified.** `r1/tests/test_c3_featurizer_online.py`:198–201.
The harness writes every E1 and D25 skip with `worker_mode="control_plane"` (`campaign.py`:622). The old fixture's "local" on a skip row is impossible in real data, and the assertions are unchanged, so the change hides no real online/offline mismatch. Suggestion: also give the replay-side `_skip_row` (l.177–179) `worker_mode: "control_plane"`. Today the offline side passes only through the missing-mode fallback, so the test does not exercise the real-ledger form on both sides.

**F7. The missing-`worker_mode` fallback differs from `campaign_usage`.** `r1/c3/features.py`:313–314.
For a mode-less skip row with a control record, `row_worker_runs` gives 0 while `campaign_usage` gives 1 (`""` is not `control_plane`). The docstring and report say the rule is "the rule of `campaign_usage`", and the equivalence test avoids mode-less rows. The fallback is safe for real data, because harness `TrialRecord`s always carry `worker_mode`. But a mode-less precheck row counts 1. *Suggestion:* also return 0 when `extra.worker.worker_skipped` is true or `failure_category` is `proposal_precondition_failed` / `effective_config_unchanged`. Reword "the rule of campaign_usage" to "agrees with it on rows with `worker_mode`".

**F8. `budget_frac_left` is unclamped while the line clamps at 0.** `features.py`:412 vs `serialize.py`:105.
The two are equivalent in practice. The harness loop stops at `worker_runs >= W`, so at decision time used ≤ W − 1, and verify is off in Paper B. A verify that overran W would make the feature negative while the line shows 0. Optional: `max(0.0, …)`, which is identical on execute-all.

**F9. Ledger-invisible charges.** Ungoverned mode drops failed_invalid rows that were charged (`campaign.py`:1925–1945). `mark_pending_failed` rows count 1 whatever was charged. Neither applies to C3 or D.3 runs. One sentence in the docstring would be enough.

**F10. Two count paths.** `serialize_view` recomputes `used` (`serialize.py`:193) instead of taking it from the featurizer state. The two are equal by construction (same prefix, after the same guard). Optional: expose `worker_runs_used` on `FeatureResult` so the prompt and the feature cannot drift apart.

**F11. The claim is scoped correctly.** The report says identity on the real sweep-1 tables was not checked, and that sweep 1 will STOP if it holds D25 skips or precheck rejections. That is accurate. Those rows are plausible in LLM-proposer sweeps (`parse_failed`, no-op and old-value-mismatch prechecks; D25), so the proposal's premise ("identical on execute-all tables") may not hold for sweep 1. That is an author decision, correctly routed. The script is read-only: it parses each row but uses only `budget_index`, `decision`, `worker_mode` and `extra.control`. Its exit-3-on-difference behaviour is correct.

**F12. Commit hygiene: OK.** Author `Dowling Wong <wangdowling@gmail.com>`. 6 files, 298 insertions, 8 changed lines, no file deletions. The trailers are present.

## Summary

The core rule is correct for every C3/D.3 path of the live harness loop. The online and replay paths agree. There is no leakage of the current row. I confirmed byte identity on execute-all ledgers against the base commit myself. Changes are requested for:
- the ghost/ctrl_only exception (F1);
- the "trial b of W" remainder of the §3.6 problem (F2, at least as an explicit author question);
- a full-byte identity test (F3);
- a corrected version rationale and a `FEATURIZER_VERSION` bump (F4);
- the identity script's sealed-path exit code, gz support and difference reasons (F5).

VERDICT: changes requested

---

## Round 2

# Independent review — W2 budget fields from worker runs (round 2)

**Reviewer:** independent AI reviewer (Claude); engineering review only.
**Unit:** `/tmp/pb/wt/w2`, branch `mac-w2-budget-20261109`, new HEAD `6b779fe3` on `81924e14` (round 1) on `a15300ca`.
- Author: Dowling Wong <wangdowling@gmail.com>.
- No file deletions since `a15300ca`.
- Worktree clean.
- No sweep or label table and no seed 7001–7010 file was read.
- Scratch files: `/tmp/pb/scratch_rev_w2/`.

## Re-run

- Relevant suite: **64 passed, 14 skipped**. The suite is `test_w2_budget_fields`, `test_c3_featurizer_online`, `test_c3_features`, `test_c3_env`, `test_trackp_serialize` and `test_c3_rule_controller`. The skips are missing `huggingface_hub` / `lightgbm`. I ran the 5 skipped serialize tests that need no real tokenizer with a whitespace tokenizer, and all pass.
- Base-commit comparison (`cmp.py`, base `git archive a15300ca` vs new HEAD): the 1068 execute-all views (1008 prompts, with failed runs) are **still identical** in features hash, full prompt text and meta.
- Online vs replay with a precheck rejection, a verify (r = 2) and a skip (`online.py`): same `features_hash`, `budget_frac_left` = 0.7.
- Identity CLI:
  - a sealed path gives `BAD_INPUT` with exit 2;
  - a `.gz` ledger is read (IDENTICAL, exit 0);
  - a difference gives exit 3 with `rows_not_counting_one`.

## Round-1 findings

| # | Status | Check |
|---|---|---|
| F1 ghost/ctrl_only | **Resolved** | `features.py`:306, 329–333. A `control_plane` row with `control.arm ∈ {ghost, ctrl_only}` counts 1, which matches `snapshot.py`:952/971–983. `ctrl_only` online (shadow record, worker mode → 1) now equals the replay of the ledger (1). The precheck-ghost exception is documented in the code and the report. There is a test. |
| F2 "trial b of W" | **Resolved as scoped** | `NodeContext.trial_budget` (default `None` = W) feeds `budget_line(..., trial_budget)`. Execute-all bytes are unchanged (confirmed above). The report states that no caller sets it yet, so D.3 has to set it when C3 arms run with a trial budget ≠ W. The field-set test was updated. |
| F3 full-byte identity test | **Not resolved: the new test is tautological** | See R2-1. |
| F4 versions | **Resolved** | `FEATURIZER_VERSION` = `c3_features/v3`, with a comment that follows the v2 precedent. `PROMPT_VERSION` is kept for a correct reason (it sits in prompt meta) and left as an author question. Report wording corrected. |
| F5 identity script | **Resolved** | A `RuntimeError` from `refuse_sealed` now exits 2. `.jsonl.gz` is accepted, and `refuse_sealed` still runs first in `main`. Row kinds are reported. Tests added. |
| F6–F12 notes | as before | F7 now also applies to ghost rows (R2-3). |

## New findings

### Should-fix

**R2-1. The "full prompt bytes vs pre-W2" test compares the new code with itself.** `r1/tests/test_w2_budget_fields.py`:148–172; report l.20.
`_pre_w2` monkeypatches `row_worker_runs` to `lambda row: 1`. On the test's execute-all ledgers every row (including the `failed_invalid` rows, `worker_mode` "local") already gives `row_worker_runs == 1`, so the patch changes nothing. Both passes run identical HEAD code. I showed this: with an off-by-one bug injected into `S.budget_line` and a `" BUG"` suffix injected into `S.history_line` (`scratch_rev_w2/taut.py`), the test still passes. The older test (`test_execute_all_features_and_budget_line_are_identical`) does catch a budget-line change, because it compares against the literal old line and formula. But no committed test catches a change elsewhere in the prompt relative to the pre-W2 code. The report's sentence "compares … against the pre-W2 computation" therefore overstates the test.
*Fix (small):*
1. Generate a golden file at `a15300ca`: for the four `execute_all(100+seed, failed={4,9,13})` ledgers, and ideally the five plain ones, store per view the `features_hash`, `render_text` and `json.dumps(meta, sort_keys=True)`. Commit it under `r1/tests/data/` with the one-line generator command and the base SHA.
2. Assert HEAD equals it byte for byte.
3. Add a sanity check that the golden differs from HEAD when one row is `local_precheck`, so the comparison is shown to bite.

Otherwise, drop the monkeypatch test and reword the report to say that full-byte identity against the base was shown only by the reviewer's scratch comparison, not by a committed test.

### Notes

**R2-2. `trial_budget` has no validation.** `features.py`:266. A non-positive value, or one below `runs_total`, is accepted silently. Optional: in `__post_init__`, reject `trial_budget is not None and trial_budget < 1`. A value below W is impossible under `c3_budgets` (trials ≥ LLM cap ≥ W).

**R2-3. The report and docstring still say "the rule `campaign_usage` already uses".** `features.py`:310; report l.14. `campaign_usage` counts ghost/ctrl_only rows 0 and mode-less skip rows 1, so the two now differ on both. That does not matter for H.6, because C3 campaigns have no Track S arms. Reword to "agrees with `campaign_usage` on C3 ledgers (rows with `worker_mode`, no Track S arms)".

## Summary

F1, F2, F4 and F5 are fixed correctly. The code is correct: my base-commit comparison and the online/replay check both hold on the new HEAD. One should-fix remains. The new full-byte test (F3's answer) is a self-comparison that cannot fail, and the report describes it as a comparison against pre-W2 code. Replace it with a golden file generated at `a15300ca`, or withdraw the claim.

VERDICT: changes requested

---

## Round 3

# Independent review — W2 budget fields from worker runs (round 3)

**Reviewer:** independent AI reviewer (Claude); engineering review only.
**Unit:** `/tmp/pb/wt/w2`, branch `mac-w2-budget-20261109`, HEAD `5db5b67d`. History: `5db5b67d` ← `6b779fe3` ← `81924e14` ← base `a15300ca`.
**Commit hygiene:**
- Author on all three commits: Dowling Wong <wangdowling@gmail.com>.
- No file deletions since `a15300ca`.
- Worktree clean.
**Data rules:** no sweep or label table and no seed 7001–7010 file was read.
**Scratch:** `/tmp/pb/scratch_rev_w2/`.

## R2-1 (tautological test): resolved

**1. The golden file is genuine.** I regenerated it with the coordinator's generator `/tmp/pb/scripts/w2_golden.py`, but on my own base export (`git archive a15300ca` → `scratch_rev_w2/base`). That export imports `r1` from the base: `FEATURIZER_VERSION` = `c3_features/v2`. The output is byte-identical to the committed `r1/tests/data/w2_execute_all_golden_a15300ca.json` (`cmp`). The file holds 4 campaigns (3, 2, 0 and 3 failed worker runs) and 76 views with a prompt.

**2. The test now bites.** I re-ran the injected bugs (`scratch_rev_w2/taut3.py`) against `test_execute_all_matches_golden_generated_at_base_commit`:

| Injection | Result |
|---|---|
| `budget_line` off by one | caught |
| `history_line` + " BUG" (a prompt change outside the budget line) | caught |
| feature-side `row_worker_runs` counts failed runs 0 | caught |
| prompt-side `row_worker_runs` counts failed runs 0 | caught |
| none | passes |

**3. The companion test is a sound sanity check.** `test_golden_comparison_detects_a_non_execute_all_row` marks one failed row as `local_precheck`. It asserts that the views up to and including that row equal the golden, and that every later view with a prompt differs.

## Notes from round 2: resolved

- **R2-2:** `NodeContext.trial_budget` is validated: a positive integer or `None`; `bool`, 0, negative values and 2.5 are rejected. This is tested. A float with an integer value such as 5.0 is accepted, and `budget_line` renders it as `int`. That is harmless.
- **R2-3:** the docstring (`features.py`:315–316) and the report now say the rule extends `campaign_usage` and differs from it on hidden-result arms and on rows without `worker_mode`. Accurate.

## Re-run on HEAD

**Tests:**
- Relevant suite: **62 passed, 14 skipped**. That is the 64 of round 2, minus the 4 removed parametrized self-comparison tests, plus the 2 new golden tests. The suite is `test_w2_budget_fields`, `test_c3_featurizer_online`, `test_c3_features`, `test_c3_env`, `test_trackp_serialize` and `test_c3_rule_controller`. The skips are missing `huggingface_hub` / `lightgbm`.
- The 5 tokenizer-free serialize tests I run by hand pass.
- `test_trackp_exam_synthetic` and `test_trackp_soft_label_v2` each have the one failure already known before this unit. Neither touches the changed code paths: the exam calls `budget_line(b, W)`, whose output is unchanged.

**My own checks:**
- Base-commit comparison (`cmp.py`): 1068 execute-all views are still identical in features hash, full prompt text and meta.
- Online vs replay with a precheck rejection, a verify and a skip (`online.py`): same hash, `budget_frac_left` = 0.7 on both.

## Remaining notes (non-blocking)

**N1.** The generator script is outside the repository (`/tmp/pb/scripts/w2_golden.py`). The test is self-contained, because the golden file holds both the ledgers and the outputs. For provenance, commit the script, or its command line and the base SHA, next to the golden file (e.g. `r1/tests/data/README` or the W2 report).

**N2.** Earlier notes F8–F12 still stand as documentation-level remarks:
- the feature is unclamped while the prompt line clamps at 0;
- ungoverned mode and recovered pending trials can hide charges from the ledger;
- the prompt line and the feature count runs in two separate places;
- sweep-1 identity has not been checked and is an author STOP if it differs.

**N3.** Nothing sets `trial_budget` yet (the report says so). D.3 must set it for C3 arms whose trial budget differs from W, before A5/A6 prompts are generated online.

## Summary

All five round-1 should-fix findings and the round-2 should-fix are resolved:
- The worker-run rule matches the harness on every C3/D.3 path and on Track S hidden-result arms.
- There is no leakage of the current row.
- The online and replay paths agree.
- Execute-all features and prompts are byte-identical to the base commit, now enforced by a golden file generated from the base code that catches injected changes.
- The identity script is read-only, refuses sealed paths with exit 2 and exits 3 on any difference.

VERDICT: accepted
