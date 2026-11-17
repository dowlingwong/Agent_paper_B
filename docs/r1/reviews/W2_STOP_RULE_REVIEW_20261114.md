Reviewed base: 92c926562e3086a53d0a07c76e3054b4ec8581a2

# W2 stop-rule report — independent review record (14 November 2026)

Branch `mac-w2-stoprule-20261114` (from `mac-w2-budget-20261109` @ `0b62fb03`). Report `reports/W2_STOP_RULE_20261114.md`, written at the author's request after the sweep-1 W2 identity check. Two rounds by one freshly spawned independent reviewer agent (AI-assisted, Claude).
- Round 1: changes requested (one blocking item: the prompt's trial budget; four should-fix items).
- Round 2: **accepted** at `92c92656`, which is the reviewed base.

Accepted commit (round 2, last): 92c926562e3086a53d0a07c76e3054b4ec8581a2

Round-2 notes, not blocking: the D25 skip is set at campaign.py l. 1548–1552 and recorded at l. 1466–1480 (the report cites the comment block l. 1427–1446); "no observer" follows from the whole call at e1b_collect l. 260–272; verify is never allowed on an invalid row or with fewer than 2r worker runs left (`controller.py` l. 264–270).

The round texts are reproduced unchanged below.

---

# Review — W2 stop-rule report, round 1 (14 Nov 2026)

**Independent reviewer (Claude, freshly spawned; did not write the unit).**
Unit: branch `mac-w2-stoprule-20261114`, tip `951dfd96bcddbd6f85b1998bb7eda45750383785` (one commit on `gh/mac-w2-budget-20261109` = `0b62fb03`; it adds only `docs/r1/reports/W2_STOP_RULE_20261114.md`, worktree clean).
Sources: harness `a3fedbbd` (`/tmp/pb/wt/harness-pin`); `r1/headroom/e1b_collect.py` and `r1/scripts/c3_label_sweep.py` at `gh/mac-int-20261107` (`a15300ca`, same bytes as on the W2 branch); `r1/c3/features.py`, `r1/c3/train/serialize.py`, `r1/c3/train/types.py`, `r1/c3/accounting.py`, `r1/scripts/w2_execute_all_identity_check.py` and the 9 Nov W2 report on the W2 branch.
Code reading only. I read no ledger, label table, sweep table, sweep config or seed 7001–7010 file, and nothing on a server. I modified nothing in the reviewed branch or worktree.

## Summary

The main conclusion is right for sweep 1. Each root campaign stops at 20 worker runs. The 40-trial budget is a backstop. A precheck rejection uses one trial and no worker run on every path. W2's `row_worker_runs` matches the harness. Almost every code citation is correct (two small off-by-one ranges are listed below).

The recommendation is not complete yet. It leaves out the `trial_budget` field. Without it, rebuilt sweep-1 prompts for the 14 ledgers will read "trial 21 of 20". The 274-ledger identity claim for prompt sets also depends on how that field is set (B1). Some statements also go further than the code supports: the 40-trial edge case, the reading of Q7, and what the rebuild needs to read (S1–S4).

## Verification of the report's citations

| Report claim | Checked at | Result |
|---|---|---|
| `runs: 20` l. 123; STOP outside DRYRUN l. 213–214; `--runs` passed l. 1462 | `c3_label_sweep.py` | Correct. The module is invoked at l. 1404 and the collect call is l. 1460–1467 (`--roots-only --points --reps 0`). |
| `_run_root` → `run_real_campaign(budget=runs*2, …, ComputeBudget(max_worker_runs=runs), verify_runs=VERIFY_R)` l. 260–265; `--runs` help l. 411 | `e1b_collect.py` | Correct. `VERIFY_R = 2` (l. 130). |
| `BudgetState(total_trials=budget, consumed_trials=len(existing_records))` l. 1258; loop l. 1303 | `campaign.py` | Correct. |
| `ComputeBudget.exhausted` l. 77–80 | `budget.py` | Correct. Worker-run test at l. 79; the seconds and LLM caps are at l. 81–84 and are `None` for sweep 1. |
| `consume_one()` l. 1970, once per pass | `campaign.py` | Correct. The only passes that skip it break out of the loop (l. 1311, l. 1368). |
| executed proposal: `consume_worker_run` l. 1683 | `campaign.py` | Correct. It also debits when `worker.run_trial` raises (l. 1670–1683); W2 counts that row as 1, which is consistent. |
| precheck: `_precondition_failure_result` l. 1516–1531, branch l. 1520, no debit | `campaign.py` | Correct. The block runs to l. 1532. |
| `_structured_failure_result` l. 1006–1031 (`<mode>_precheck`, `worker_skipped: True`) | `campaign.py` | Content correct, range off by one: the `def` is at l. 1007 and the call closes at l. 1033. Fields at l. 1018 and l. 1023. |
| recheck l. 1663–1665: trial 1, run 0 | `campaign.py` | Correct, but the label "after an E1b revision" is too narrow (see N1). |
| control-plane skip `_skipped_record` l. 600, l. 1713 (`worker_mode="control_plane"` l. 622) | `campaign.py` | Correct. |
| verify re-runs l. 731, l. 743 | `campaign.py` | Correct. |
| `_budget_view` l. 238–243 | `campaign.py` | Correct. |
| `ComputeBudget` docstring l. 44–56 | `budget.py` | Correct. The class is at l. 44 and the docstring at l. 45–56. |
| `row_worker_runs`, `_precheck` rows 0, "l. 319–332" | `features.py` @ W2 | Content correct. The function spans l. 312–341, the code rule is at l. 332 and the docstring rule at l. 318–319; cite "l. 312–341 (rule l. 332)". |

Other checks:
- **Launch path.** `c3_label_sweep.py` l. 1460–1462 passes `--runs` to `e1b_collect`. Its `main` stores it in the manifest (`"runs": args.runs`, l. 488). Root jobs, fresh or resumed, take `manifest["runs"]` (l. 528). They are dispatched to `run_root` (l. 553), which calls `_run_root` (l. 217).
- **Fresh trial counter.** `_run_root` deletes any existing root before running (l. 254–255). So `existing_records` is empty and the trial budget is exactly 40.
- **Only other worker-run debits in the harness.** `consume_worker_run` is also called in `run_dry_campaign` (l. 2173) and in `snapshot.py` l. 952 (resume). Neither is on the sweep-1 path.
- **Only producer of `_precheck` rows.** `"_precheck"` and `worker_skipped` appear nowhere else in `src/`.

## Findings

### Blocking

**B1. The recommendation leaves out `trial_budget`. Rebuilt sweep-1 prompts will read "trial 2x of 20", and the 274-identity claim for prompt sets depends on this choice.** Report l. 10, l. 36, l. 39.
- `serialize.budget_line` builds `"Budget: trial {b} of {trials} (…)"`, with `trials = runs_total if trial_budget is None` (`r1/c3/train/serialize.py` l. 100–107). It is called with `node_ctx.trial_budget` (l. 196).
- `NodeContext.trial_budget` defaults to `None` = W (`features.py` l. 266). The 9 Nov report says it exists "so the line need not read 'trial 25 of 20'; no caller sets it yet" (`W2_BUDGET_FIELDS_20261109.md` l. 12).
- On sweep 1 the real trial budget is `runs*2 = 40` (`e1b_collect.py` l. 261), not W. A campaign with k precheck rejections that reaches 20 worker runs has 20 + k rows, so its last k views have b > 20.
- If the rebuild keeps `trial_budget=None`, those views read "trial 21 of 20" and so on.
- If it sets `trial_budget=40` for all sweep-1 campaigns (the honest value, equal to the harness's `trials_total`), the budget line changes on **all 288** campaigns. The "274 … bit-identical" claim then holds for feature tables only, not for prompt sets.
- Setting 40 only on the 14 would give two campaigns with the same budget different prompt text.

**Fix:** add a step to the recommendation that names the `trial_budget` for the sweep-1 (and sweep-2) rebuild and states its effect on identity. My suggestion is `trial_budget = 2W = 40` on every sweep-1 campaign, with the `PROMPT_VERSION` bump this makes unavoidable (see S2). Restrict the 274-identity sentence (l. 36) to feature tables, or to prompts only under `trial_budget=None`. This is an author decision, so list it as one.

### Should-fix

**S1. Edge-case sentence l. 31: "Its worker-run count still drives the feature correctly" is not supported.**
- A campaign that reaches the 40-trial cap with fewer than 20 worker runs ends because of the **trial** counter (`campaign.py` l. 1303; `budget.py` l. 29).
- On its late views `1 − worker_runs_used/W` reports budget left that the campaign can no longer use. In those views the trial count is what binds, which is the author's trial-counting case (options A/B).
- The check summary that already exists can settle this without reading new data: `check_ledger` reports `rows` and `worker_runs_total` per ledger (`w2_execute_all_identity_check.py` l. 71–73). The edge case is exactly `worker_runs_total < 20` (with `rows == 40`). A value below 20 could also show an incomplete root.

**Fix:** replace the sentence with: "If such a campaign exists, its late views overstate the usable budget; the feature is right only for campaigns that end at 20 worker runs." Make "every sweep-1 ledger has `worker_runs_total == 20` in the existing check summary" a precondition of the recommendation, to be confirmed by the author or the cluster agent. If any ledger fails it, those campaigns need option A (both remaining quantities) or must be excluded.

**S2. PROMPT_VERSION, l. 39: "Rebuilding sweep-1 prompts for these 14 ledgers is exactly that event" goes beyond the 13 Nov Q7 answer.**
- The answer reads: "PROMPT_VERSION 暂保持 v1，首次构建含 skip 的 Track P 数据时再升版本。" ("Keep PROMPT_VERSION at v1 for now; bump it when Track P data containing skips is first built.") Its trigger is **skips**.
- A precheck rejection is not a skip in the harness's terms. A skip has `worker_mode == "control_plane"` and decision `skipped` (`campaign.py` l. 600–643). A precheck rejection has `worker_mode` ending in `_precheck` and goes through `_record_from_worker_result` as an invalid, failed trial (l. 1734 and l. 2345–2356). The check script also counts them separately (`w2_execute_all_identity_check.py` l. 38–41).
- What the two have in common is the effect that led to deferring the bump: the prompt text changes under the same version string (`W2_BUDGET_FIELDS_20261109.md` l. 30).

**Fix:** say that literally the Q7 trigger is not met. Then recommend treating precheck-only differences as the same trigger, for the reason above, and ask the author to confirm. If B1 is settled with `trial_budget=40`, every sweep-1 prompt changes, and the bump follows on its own.

**S3. Recommendation 3, l. 38, mixes up what the check reads with what the rebuild reads.**
- The sentence "needs label-free access only for these fields (the check script reads only `budget_index`, `decision`, `worker_mode` and `extra.control`)" suggests the rebuild needs only those four fields. That is wrong.
- Rebuilding features and prompts reads parsed metrics, `delta_vs_best` and structured edits from every row (`serialize.py` l. 188–193; `features.py` `_row_edit` l. 354–355).

**Fix:** "The rebuild reads the full ledger rows (features: metrics, deltas, edits) but no label table and no seed 7001–7010 data. The four-field restriction applies to the identity check only."

**S4. The report does not cover the sweep-1 controller facts the conclusion relies on.** Brief item 2 and item 3 (verify).
- `_run_root` passes no `controller`, so the default is `ContinueController` (`campaign.py` l. 1251; `e1b_collect.py` docstring l. 6–7).
- It passes no `max_llm_calls` or `max_worker_seconds` (l. 265), so the LLM and seconds caps never apply (`budget.py` l. 81–84).
- It passes no `proposal_observer`, so the observer exit at l. 1304–1311 cannot be reached.
- As a result, sweep 1 has no E0 stop (l. 1359–1368), no E1 skip or revise, and no verify. The verify mask also requires a **valid** provisional record and `worker_runs_remaining >= 2r` (`controller.py` l. 264–270). So verify can never run on a precheck row, and the worker-run count can never pass 20.
- `_run_verify` calls `run_trial_at_seed` directly with a no-edit proposal and never calls `_precondition_failure_result` (`campaign.py` l. 722–744). So no precheck happens inside verify.
- The only non-run rows possible in sweep 1 are precheck rejections and D25 inactive-key skips (l. 1431, l. 1547–1551). D25 skips need no controller.
- This is also why the 274 execute-all ledgers count exactly 1 per row.

**Fix:** add these four or five lines, with their line numbers, under Finding §1 or §3. Also add the fresh-counter fact (`e1b_collect.py` l. 254–255) and the manifest step on the launch path (l. 488, l. 528, l. 553).

### Notes

- **N1.** Table row, l. 23: the recheck at l. 1663 runs for every trial that is not skipped, on the `else` path. That includes trials after an E1 `revise` (l. 1600–1625) with or without the E1b rescreen (l. 1626–1656). Write "after an E1 revision (with or without the E1b rescreen)". Also say it cannot be reached on sweep 1 (no revise under `ContinueController`). Without a revision the workspace is unchanged since l. 1516, so the recheck repeats the first result.
- **N2.** Disclosure, l. 37: "14 of 288 sweep-1 campaigns contain precheck rejections". The check records a difference only on rows **after** a row that does not count 1 (`w2_execute_all_identity_check.py` l. 65–70). A precheck in the last row would not show as a difference. Under the harness loop that can only happen at trial 40 or after a crash, so in practice the count is right. Still, take the number of campaigns with precheck rows from `rows_not_counting_one` in the same summary, not from `ledgers_with_differences`. Write "views after the first rejection" as views b > p, where p is the first precheck index.
- **N3.** Recommendation 1, l. 36: tables do not record `FEATURIZER_VERSION`; only online decision records do (`features.py` l. 236–243). Ask the rebuild unit to record the featurizer version and commit (and `trial_budget`) in each rebuilt table's manifest. Otherwise v2-built and v3-rebuilt sweep-1 tables cannot be told apart, and the disclosure in l. 37 cannot be checked.
- **N4.** Disclosure, l. 37: "rebuilt under v3 before any analysis that uses them". This report cannot support that claim, since it does not know whether sweep-1 tables were already used. Keep it as draft wording to be confirmed when the rebuild is done.
- **N5. Not on sweep 1's path, for the record.** The E1b leaf cost counter `run_leaf` counts every row whose decision is not `skipped` as one run (`e1b_collect.py` l. 331–339). So a precheck row in a branch ledger is debited 1, unlike the harness and W2. Sweep 1 runs `--roots-only --points` with no points, so it builds no leaves. Any older E1b `cost_worker_runs` with precheck rows would be overstated by one per such row. Consider a separate ticket.
- **N6.** l. 3 and l. 7: the 14/288 figures, "cluster agent, deepthought" and "every differing row is a precheck rejection" come from the author's message, not from code. Mark them as reported, for example "(reported by the check, 14 Nov)".

## Conditions for acceptance

- B1 resolved: a named `trial_budget` choice and the identity claim limited to what holds.
- S1–S4 fixed as text changes.
- Notes at the author's discretion.
- No data reading is needed for any of these.

Verdict: changes requested

---

# Review — W2 stop-rule report, round 2 (14 Nov 2026)

**Independent reviewer (Claude; did not write the unit).**
Unit: branch `mac-w2-stoprule-20261114`, tip `92c926562e3086a53d0a07c76e3054b4ec8581a2`. That is two commits on `951dfd96`: `1cb9c42a` and `92c92656`. They change only `docs/r1/reports/W2_STOP_RULE_20261114.md` (+15/−10), and the worktree is clean.
Sources are the same as in round 1: harness `a3fedbb` in `/tmp/pb/wt/harness-pin`, and the paper code at `a15300ca` and on the W2 branch.
Code reading only. I read no ledger, label table, check output, sweep config or seed 7001–7010 file, used no server, and modified nothing in the branch or worktree.

## Round-1 findings

| Finding | Status | Check |
|---|---|---|
| B1 `trial_budget` | **Resolved** | Item 2 (report l. 39) cites `serialize.py` l. 100–107, which is correct. It states that no caller sets the field. It frames (a) 40 for all sweep-1 campaigns against (b) "of 20" as an author decision. It states the identity consequence correctly: all 288 prompts change under (a), while feature tables stay identical on execute-all ledgers. It recommends (a) together with the version bump. The 274-identity claim in item 1 (l. 38) is now limited to the feature `budget_frac_left`. |
| S1 edge case | **Resolved** | l. 33 now says the feature "would show runs it could no longer use". It makes `worker_runs_total == 20` on every ledger a precondition, read from the existing check summary (`w2_execute_all_identity_check.py` l. 71–73 records that field). |
| S2 Q7 wording | **Resolved** | l. 42 says the Q7 trigger ("首次构建含 skip 的 Track P 数据", i.e. "when Track P data with skips is first built") is literally not met, because a precheck rejection is a failed, invalid trial with `worker_mode` ending in `_precheck`, not a skip. It gives the reason to bump anyway and leaves confirmation to the author. |
| S3 rebuild data access | **Resolved** | l. 41: the rebuild reads the featurizer fields (metrics, deltas, edits, `worker_mode`, `extra.control`) and no label table or audit seed. |
| S4 sweep-1 exits | **Resolved** | New §4 (l. 27). `ContinueController` default: campaign.py l. 1251, correct. Only `max_worker_runs` is passed (e1b_collect l. 265): correct. Fresh root (l. 254–255): correct. The conclusion that the only non-run rows are precheck rejections and D25 skips is correct. |
| Line ranges | **Resolved** | `_structured_failure_result` l. 1007–1033 and `row_worker_runs` l. 312–341 (rule l. 332): both correct. |
| N1–N6 | **Addressed** | N1 "any E1 revision" (l. 23). N2 `rows_not_counting_one` as the count source (l. 38). N3 `FEATURIZER_VERSION` in table manifests (l. 38). N4 draft disclosure wording (l. 40). N5 leaf-cost side note (l. 46; e1b_collect l. 331–339, correct). N6 "as reported to me; I read no check output" (l. 3). |

## New findings

### Blocking
None.

### Should-fix
None.

### Notes (optional; they do not affect the verdict)

- **R2-N1.** The D25 citation at §4 (l. 27), "campaign.py l. 1427–1446", covers the D25 comment and the start of the revision loop. The rejection is recorded at l. 1466–1480 and the skip itself is set at l. 1548–1552 (`skip_trial = True`, `reason: "inactive_key"`). Consider citing "l. 1427–1480, skip at l. 1548–1552".
- **R2-N2.** "no observer (only `max_worker_runs`, e1b_collect l. 265)": the absence of a `proposal_observer` follows from the whole call at l. 260–272, not from l. 265 alone. This is cosmetic.
- **R2-N3.** For completeness, §4 could add that the E2 verify mask requires a valid provisional record and at least 2r worker runs left (`controller.py` l. 264–270). So even under another controller, verify could never run on a precheck row or push past 20 runs. The conclusion does not depend on it.

## Assessment

The report's code claims hold at `a3fedbb`, `a15300ca` and the W2 branch. Its conclusion for sweep 1 is correct:
- the campaign stops at 20 worker runs, with 40 trials as a backstop;
- a precheck rejection uses one trial and no worker run on every path.

The recommendation is now complete. It leaves to the author the decisions that belong to the author (`trial_budget`, `PROMPT_VERSION`) and makes the 40-trial edge case a stated precondition. It leaves ledgers and labels untouched. It reads no data and states the 14/288 figures as reported.

Verdict: accepted
Accepted commit: 92c926562e3086a53d0a07c76e3054b4ec8581a2

