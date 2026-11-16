# B1 STOP of run `4b31_20261112_c` — diagnosis, inventory of model-output STOPs, fix, and reuse of the 89 roots (13 November 2026)

**Status.** AI-assisted (Claude, Mac-local agent). This answers items (1), (2), (3) and (5) of the author's route for the STOP recorded in `reports/B1_STOP_4B31_20261112.md` (branch `mac-b1-20261107` @ `3b7d5704`). The author's ruling is to handle it as an engineering problem (PLAN §10 `R1-EXAM-B1-MODEL-OUTPUT-INVALID`; not quoted). Code references are to the run checkout `4b312844` (paper) and harness `a3fedbb`. The fixed-prompt replay of item (1) is a read-only host step (`proposals/B1_PROPOSAL_REPLAY_HANDOFF_20261113.md`); §1.4 is filled when it returns. It names the exact reply of trial 020 but does not change the diagnosis or the fix, and it is not a restart precondition.

## 0. Summary

| Question | Answer |
|---|---|
| Why were 018/019 invalid trials and 020 a STOP? | In 018 and 019 the model's free-text `objective` and its structured fields named the **same** edit (`model_type` → `ridge_regression` / `ridge`). The worker executed it, the node rejected the value (`invalid_config`, exit 2), and the trial was invalid. In 020 the two **disagreed**. The B1 worker guard is designed to stop the campaign, not to execute, when they disagree. The value the model wanted (a ridge model with `alpha`) was equally impossible in all three; what differed was whether its two descriptions of the edit agreed (§1). |
| Which B1 STOPs or uncaught exceptions can a model output trigger? | 21 items (§3). Seven were STOPs or uncaught exceptions caused by model output: the worker-guard conditions M5–M9, a prompt that outgrows the context (M19) and a reply carrying a lone surrogate, which makes the next request unencodable (M20). They are now invalid trials. Five STOPs are retained, with the reason given for each: M10 is internal; M15 (observer timeout), M17 (audit-seed failure), M18 (transport) and M21 (the 12 h root deadline) are not decidable as model output, or need an analysis-rule decision. The rest were already invalid trials. |
| Fix | Paper side only; harness pin unchanged; `paper_commit` re-pinned (§4). The model-output checks run on the proposal before the control plane can call the worker. A failing proposal is not executed, is recorded as an invalid trial (`PROPOSAL_PRECONDITION_FAILED`) and is charged its LLM call. Every proposal is journalled to disk before execution. The worker guard keeps its STOP for internal inconsistencies. |
| Can the 89 completed `_c` roots be reused? | **Scientifically yes:** under the fix their trajectories are exactly what the new code would have produced. **Procedurally not without new machinery:** the roots are bound to the `_c` authorization and lack the new journal evidence. Reusing them needs a new reviewed import path and a PLAN row, and saves about 6 h of GPU time. Recommendation: do not reuse by default (§6). |

## 1. Why 018/019 were invalid and 020 stopped

### 1.1 How a proposal reaches the worker

The proposer replies with six strings, `rationale, summary, objective, param, old_value, new_value` (harness `llm/providers.py` l. 23–31). From them:

- the harness builds the **structured edit** from `param` / `old_value` / `new_value` only (`langgraph_manager._extract_structured_edit`, strict mode, l. 199–268; called at l. 333). The control plane's precondition checks, the ledger, the replay and the audits use this edit.
- the pinned `LocalWorker` executes the **objective**: it parses "change SYMBOL from OLD to NEW" from it (`local_worker._CHANGE_RE` l. 54, `_parse_change_directive` l. 322) and applies that (`_apply_edit` l. 353).

So one reply carries the same edit twice, in two forms. The B1 worker guard (`r1/exam/b1_proposal_guard.py::verify_proposal`, l. 23–58 at `4b312844`, called before execution at l. 75) compares them and raises `B1ProposalIntegrityStop`, a `SystemExit` subclass that escapes the harness's exception-to-invalid conversion, whenever they disagree.

### 1.2 Trials 018 and 019 (and 008–017)

Evidence: the committed STOP capture (`reports/b1_stop_4b31_20261112/`).

- Ledger: 018 has structured edit `model_type: logistic_regression → ridge_regression`, 019 has `→ ridge`. Both are `failed_invalid`, `invalid_config`, worker message `exit code 2`.
- `runner.log`: "trial-018: applied edit model_type: logistic_regression → ridge_regression", "trial-019: applied edit model_type: logistic_regression → ridge". The worker executed exactly the structured edit, so the objective's directive agreed with it and the guard passed.
- The node then rejected the value. `openml_credit_approval/benchmark.py` checks `model_type` against its allowed values (l. 155–166) and emits `FAILURE_CATEGORY=invalid_config` (exit 2). The harness recorded an invalid trial.
- Trials 008, 009, 010, 013, 014 and 017 were the same class: with 018 and 019, eight `model_type` → `ridge`/`ridge_regression` attempts, all invalid (011 changed `scaler`, 012 `class_weight`). The summaries of 014, 017, 018 and 019 also mention an alpha value. By trial 020 the memory context reported `repeated_bad_count` 15.

### 1.3 Trial 020

- Events: `proposal_created` with summary `switch-to-ridge-alpha-0.1`; `llm_call` ok (`finish_reason` stop, 1,318 prompt tokens, 100 completion tokens, 399 characters, seed 836976301); `worker_started`. Then `STOP: B1 worker directive and structured edit differ` (guard l. 36).
- That message is raised when the objective's directive names a symbol that is not editable, or a different symbol, or a different old or new value than the structured edit (l. 33–36). The node's editable symbols do not include `alpha` (`C, class_weight, imputer, learning_rate, max_depth, max_iter, model_type, n_estimators, scaler`). The summaries of 014, 017, 018 and 019 already mention an alpha value. The most likely reading: the objective named `alpha` or put the alpha value into the directive, while the structured fields again named `model_type`.
- The exact reply was not persisted: no ledger row is written before execution, and `llm_call` records only usage. This is the evidence gap the fix closes (§4.3).

**Answer.** The difference between 018/019 and 020 is not the target value; all three asked for something the node cannot do. It is whether the two descriptions of the edit in one reply agreed. When they agreed, the impossible value reached the node, which rejected it (invalid trial). When they disagreed, the guard stopped before execution, as designed in R1-EXAM-B1's integrity rule. That rule treated a disagreement as a reason to stop the batch, although it is a property of the model's output, like an unparseable reply.

### 1.4 Fixed-prompt replay — PENDING (host, optional)

`r1/scripts/b1_proposal_replay.py` rebuilds what the harness gave the proposer at a trial, using the harness's own functions on a **copy** of the root: ledger prefix, memory context, incumbent files, status and incumbent metric. It calls the B1 proposer once with the same seed rule.

It checks reproduction:
- `context_sha256` and `raw_proposal_sha256` against the ledger (018, 019);
- `seed`, `prompt_tokens`, `completion_tokens` and `response_chars` against each trial's `llm_call` event (018–020).

It reports, per trial:
- the six reply fields;
- the directive the worker would parse;
- the run guard's verdict;
- the new check's verdict.

Against the stand-in server it reproduces the recorded calls exactly (`r1/tests/test_b1_proposal_replay.py`). On TASL-7 it needs a llama-server started with the run's recorded argv (`proposals/B1_PROPOSAL_REPLAY_HANDOFF_20261113.md`). Result: ⟨to be filled from `replay.json`: reproduced yes/no; trial 020's objective, fields and failing check⟩.

## 2. Where model output flows in B1

A reply's text reaches:
1. the harness validator (parse; structured edit);
2. the D25 inactive-key loop (revision or skip);
3. the harness precondition checks (path, symbol editable and present, old value current, no-op);
4. the worker guard and the worker (directive, file edit, node run with the new value);
5. the A4 observer prompt, after execution (summary, objective);
6. the memory summary of every later prompt (the summary line);
7. after the campaign, the replay of executed edits and the K = 4 audits of executed configurations.

The inventory follows this path.

## 3. Inventory: STOPs and uncaught exceptions a model output can trigger

"Before" is `_c` (`4b312844` + harness `a3fedbb`). "After" is this fix. "Test" is a test in `r1/tests/test_exam_b1_model_output.py` unless another file is named.

| # | Trigger (model output) | Where | Before | After | Test |
|---|---|---|---|---|---|
| M1 | Reply not JSON / not the six-string schema | harness `_validate_proposal` l. 286–313 | invalid (`parse_failed`, precondition) | unchanged | `test_parse_failure_and_truncation_stay_invalid`; `test_exam_observer::test_schema_parse_failure_is_counted_without_worker_or_fallback` |
| M2 | Reply cut at the completion cap or the context | SDK structured-output parser | invalid (`R1-EXAM-B1-TRUNCATION-INVALID`) | unchanged | `test_exam_b1_truncation.py` (all) |
| M3 | `param` names no editable constant / no `new_value` | harness l. 333–339 | invalid (precondition) | unchanged | `test_unresolvable_param_stays_a_harness_precondition_failure` |
| M4 | Edit on a D25-inactive key | harness campaign D25 loop | revision, then skip | unchanged (left to the harness) | `test_d25_inactive_key_is_left_to_the_harness` |
| M5 | Edit present, objective has no executable directive | guard l. 29–30 | **STOP** | invalid, `directive_missing` | `test_model_output_fault_…[no_directive-digits_mlp]`, `test_precheck_and_worker_guard_agree` |
| M6 | Directive names a non-editable symbol (020) or another symbol | guard l. 31–36 | **STOP** | invalid, `directive_symbol_not_editable` / `_differs` | `…[sym_not_editable-*]`, `…[sym_differs-*]`, `test_the_4b31_trial_020_shape` |
| M7 | Directive old or new value ≠ structured edit | guard l. 33–36 | **STOP** | invalid, `directive_old_differs` / `_new_differs` | `…[old_differs-*]`, `…[new_differs-*]` |
| M8 | New value contains a backslash | guard l. 46–47 | **STOP** | invalid, `replacement_escape` | `…[backslash-*]` |
| M9 | `.py` node: value > 256 chars, not a literal, not a finite int/float | guard l. 48–57 | **STOP** | invalid, `python_value_*` | `…[py_long|py_nonliteral|py_nonfinite|py_bool-*]` |
| M10 | Edit path ≠ the node's editable file | guard l. 40–42 | STOP | **STOP retained**: the harness sets the path (`editable_paths[0]`), so a mismatch is internal | `test_worker_guard_path_mismatch_still_stops` |
| M11 | Stale old value, symbol absent, no-op | harness precondition l. 912–1004 | invalid (precondition) | unchanged; a bad directive on such a proposal no longer matters, since the harness rejects it first, exactly as before | `test_harness_rejections_are_left_exactly_as_before`, `test_real_worker_turns_node_rejections_into_invalid_trials` |
| M12 | Value the node rejects at run time (`invalid_config`, runtime error, missing metric): 018/019 | node + worker | invalid | unchanged | `test_real_worker_turns_node_rejections_into_invalid_trials` |
| M13 | Value that makes the run exceed the worker's 3,600 s timeout | `local_worker` l. 97, 309 | invalid (time counts toward the 12 h root deadline) | unchanged | `test_worker_timeout_is_an_invalid_trial` |
| M14 | `digits_mlp` value outside the node's *declared* `allowed_ranges` (e.g. `HIDDEN_UNITS` 300 > 256) | not enforced by harness or node | executes (no STOP; a very large value can also exhaust memory: if the node subprocess fails to allocate, the worker records a runtime failure; under host-wide pressure the OOM killer could instead kill the root worker or llama-server, an unattributable STOP; or it runs into M13) | **unchanged; flagged for the author** (§5) | `test_value_outside_the_declared_range_still_executes` |
| M15 | Observer: unparseable answer / reply slower than the 60 s timeout | `observer.py` l. 148, 192–216 | `query_failed` / **STOP** | unchanged / **STOP retained** (§5) | `test_exam_observer::test_observer_cap_and_failed_query_are_recorded_without_decision_input`; `test_exam_b1_observer_integration::…[fail]` |
| M16 | Post-campaign replay of an executed edit fails | `campaign.py` l. 252 → `features.apply_edit` | uncaught exception (STOP) | **STOP retained, now unreachable from model output**: for an edit that passes the new check, worker and replay apply it identically | `test_worker_and_replay_apply_a_passing_edit_identically` |
| M17 | Executed configuration fails or is non-finite on an audit seed | `audit.run_config` l. 156; `campaign.py` l. 68, 281 | STOP | **STOP retained; needs an analysis-rule decision** (§5) | `test_b1_audit_stop.py` (all) |
| M18 | LLM transport failure / HTTP error | harness `transport_retry` | STOP | **STOP retained**: not model output | `test_other_llm_failures_still_stop` |
| M19 | Prompt longer than the context, because the memory summary repeats earlier model text (summary lines) | llama-server HTTP 400 `exceed_context_size_error` (`620d222` `server-context.cpp` l. 3676–3681) | **STOP** | after trial 1: invalid (`context_overflow`), charged; **at trial 1 STOP retained**: no model text in that prompt | `test_prompt_beyond_the_context_is_an_invalid_trial_after_trial_1` |
| M20 | Reply whose `summary` field holds a lone UTF-16 surrogate (e.g. the JSON escape `\ud800`), also after an inline `<think>` block | the summary is the only reply field that enters later prompts (summary line, best strategy); the HTTP client cannot encode that request (`UnicodeEncodeError`, host versions too) | uncaught exception at the **next** proposer call (STOP) | invalid (`unencodable_reply`), charged; the reply is discarded, so it never enters the memory summary. A surrogate in any other field, or on a reply the harness cannot parse, is left to the harness as before | `test_unencodable_reply_is_an_invalid_trial_and_later_prompts_still_work`, `test_unencodable_summary_after_an_inline_think_block_is_caught`, `test_surrogate_outside_the_summary_is_left_to_the_harness_as_before`, `test_unencodable_check_mirrors_the_harness_parse` |
| M21 | Long completions or slow configurations that, summed over the root, reach the 12 h root deadline | `runtime.py` l. 859 | STOP | **STOP retained**: a wall-clock limit on the whole root, not a property of one proposal; not reached in any B1 run (all 89 `_c` roots together took 6.3 h) | none new; the configured value 43,200 s is checked by `test_b1_committed_config_unittest.py` |

Not model output and unchanged: filesystem, preservation and lease guards (`b1_node_artifacts`, `b1_editable_preserve`, `b1_worker_artifact_guard`, `b1_state_preserve`, `b1_openml_cache_guard`), authority and binding checks, and server start and identity checks. The 12 h root deadline is M21.

## 4. The fix

### 4.1 Model-output check before execution

`r1/exam/b1_proposal_precheck.py::check_model_output` is the guard's model-output conditions (M5–M9), in the guard's order, with stable codes. `B1CappedLangGraphManager.propose_next_trial` (the B1 proposer) applies it to each proposal (first proposals and D25 revisions) in this order:

1. no structured edit, or a parse failure: left to the harness (M1–M3);
2. edit on a D25-inactive key: left to the harness, which revises or skips it and never executes it as is (M4);
3. the harness's own precondition check (`_precondition_failure_result`, called on the same files) would reject it: left untouched, so the harness rejects it **exactly as before** (M11);
4. otherwise `check_model_output`. On failure, the structured edit is removed and `proposal_precondition_failed` is set, with the edit and the reason in `extra['b1_model_output_rejected']`. The harness then records `failed_invalid`, `PROPOSAL_PRECONDITION_FAILED`, with no worker run and no observer call, and the LLM call charged (as for M1–M3).

Without its structured edit, the harness's D25 check would read the key from the objective (`named_edit_key` falls back to the objective). If the objective named an editable but inactive key, the harness would ask for a revision of the rejected proposal. So a rejection also sets `extra['named_param']` to the edit's own (active) symbol, and the manager stops if the D25 check would still fire. A rejection is therefore final: one call, no revision. The journal validator requires a rejected row to be the last row of its trial.

Because of steps 1–3, a proposal that did not STOP under `_c` is recorded exactly as under `_c`. Only formerly-STOPping proposals are affected. The worker guard (`b1_proposal_guard.py`) is unchanged in code; only a docstring paragraph is added. `check_model_output` reproduces its conditions in the same order with the same messages, and a test asserts both agree on every case. A proposal failing the guard at the worker has bypassed the manager check, which is an internal inconsistency, so it keeps its STOP.

When reading a rejected trial in a ledger: the harness's failure message for it is its generic precondition text ("proposal selector could not find a non-no-op structured edit"); the actual reason is in `extra.manager.b1_model_output_rejected` and in the journal.

One case stays on the old path on purpose: a `.py` value for which `ast.literal_eval` raises `TypeError` (e.g. `{[]: 1}`, an unhashable dict key). The guard catches only `ValueError`/`SyntaxError`/`MemoryError`/`RecursionError`, so under `_c` the `TypeError` propagated out of the worker and the harness recorded an invalid trial after the worker started. The pre-check returns no rejection for it, so this case is recorded exactly as under `_c` (`test_typeerror_value_stays_on_the_worker_path_as_before`).

### 4.2 Context overflow (M19)

In the proposer's model wrapper, llama-server's HTTP 400 `exceed_context_size_error` becomes an empty reply, so the proposal is an invalid trial (record: `context_overflow`, prompt tokens from the error body's `n_prompt_tokens`, else from the message). At trial 1 it remains a STOP.

Overflow is in practice absorbing: the memory summary only grows, so once a root's prompt exceeds the context, its later proposer calls overflow too and the rest of the root's budget becomes invalid trials. That is the intended accounting (the model's own text filled the context); the per-root count is in the record and in `b1_completion_usage.py` (`context_overflow`).

### 4.2a Unencodable reply (M20)

A reply whose `summary` contains a lone surrogate code point (U+D800–DFFF; e.g. the JSON escape `\ud800`) parses, but in B1's memory mode the summary enters every later prompt (the trial's summary line and the best-strategy line), and the HTTP client cannot encode that request. Under `_c` this raised `UnicodeEncodeError` at the next proposer call (also with the host's package versions). The wrapper now discards such a reply (`unencodable_reply`, charged, its completion tokens kept), so the trial is invalid and the text never reaches the memory summary.

The check looks only where the STOP came from. It parses the reply the way the harness's schema path does (`langgraph_manager` l. 562–566 and 288–295 at `a3fedbb`): inline `<think>…</think>` blocks are removed (the exam server runs without `--reasoning-format`, so a reply can carry one), and the rest must be a JSON object of exactly the six string fields. Only then is the stripped `summary` checked. A surrogate in another field (rationale, objective text, edit value) reaches no later prompt and did not stop `_c`; such a trial is recorded exactly as before, possibly executed. A reply the harness cannot parse gets its default summary, so no surrogate reaches memory either. Two cases are still recorded differently from `_c`. In both, the summary never reached a later prompt under `_c`, so nothing stopped; now the reply is an invalid trial, charged, with no revision:
1. a summary surrogate on a root's **last** proposer call (no later call followed);
2. a summary surrogate on a proposal the harness would have replaced through a D25 inactive-key revision (the replaced proposal never became a record, so its summary reached no prompt). This can happen in the middle of a root.

Neither is visible in the committed STOP capture: ledger and events are written with `ensure_ascii`, so a surrogate would appear as a `\ud800`–`\udfff` escape, and none occurs. A scan can find case 1, and case 2 only for a first proposal (its summary is in the `proposal_created` event); a non-final D25 revision leaves no trace in the root, so only the replay could exclude case 2.

### 4.3 Proposal journal before execution

`b1_proposals.jsonl` in each LLM root receives one row per proposer call, appended and fsynced before the proposal is returned, so before any execution. Each row holds:
- trial, revision attempt, summary, rationale and objective;
- the structured edit as built, and as passed on;
- the parsed directive;
- the raw reply and its SHA-256;
- the truncation, context-overflow and unencodable-reply flags, the check outcome and the rejection.

`r1/exam/b1_proposal_journal.py` validates it against events and ledger:
- one row per proposer `llm_call`, in order;
- each ledger record equals the last row of its trial;
- rejections are consistent and final (a rejected row is the last row of its trial).

It runs in the worker (manifest field `proposal_journal`) and again in `b1_batch` verification. The file is in the evidence index (`evidence_hashes`). Software anchors have none.

### 4.4 Re-pin

The code is `3458b672` plus `02a91494` (review round 2: the summary-only unencodable check). `paper_commit` moved from `1334c616` to `3458b672` (`2eda52e7`) and then to `02a91494` (`c5bf524b`). Rule, harness, grids, interval, seeds, nodes, budgets and context are unchanged.

### 4.5 Tests

`r1/tests/test_exam_b1_model_output.py` (one or more tests per inventory item, table above), `r1/tests/test_b1_proposal_replay.py`, `r1/tests/test_b1_completion_usage.py` (overflow calls), two new `b1_batch` STOP tests in `test_exam_b1_batch_verify.py` (journal evidence mismatch; software anchor with a journal), plus updated fixtures there and in the two stand-in drivers. With `R1_REQUIRE_B1_HARNESS=1` the harness-dependent tests fail rather than skip if the pinned harness `a3fedbb` is missing.

Results (Mac VM, `/tmp/trackg_venv`; `AR_HARNESS_ROOT` = Track G harness checkout, `AR_HARNESS_B1_ROOT` = harness `a3fedbb`, `R1_REQUIRE_B1_HARNESS=1`; `pytest -k "exam or b1" r1/tests`):

| Tree | Passed | Failed | Skipped |
|---|---|---|---|
| `_c` run HEAD `4b312844` (baseline) | 699 | 18 | 0 |
| this branch | 758 | 18 | 0 |

The 18 failures are the same 18 test IDs in both trees: 16 namespace-fixture tests that need a file not present in this environment, one test that needs the Stage A harness pin, and `test_actual_pinned_controller_does_not_convert_collision_to_invalid`, which also fails at the baseline. The B1 model-output, truncation, replay, usage and batch-verification tests (112) also pass in `/tmp/hostver_venv`, which has the host's package versions (`openai` 2.36.0 and the host's `langchain-openai`/`langgraph`).

## 5. Retained STOPs and open questions for the author

- **M15, observer timeout.** The client cannot tell a slow reply from a stalled server. Turning a timeout into `query_failed` would also hide server stalls in the observer evidence chain. A dead server would surface at the next proposer call anyway, but the evidence rule is the author's. The measured margin is 44.6 s of 60 s for thinking-on candidates with an armed budget (truncation diagnosis §5).
- **M17, audit-seed failure.** A configuration that ran on the campaign seed but fails, or gives a non-finite metric, on an audit seed was chosen by the model. But the trial was already executed, and "not executed, invalid" does not apply. Treating it as an invalid proposal changes what `x5_rule_v2` ranks: dropping its audit favours candidates with unstable proposals. Treating it as zero increment is another rule. Neither is an engineering choice. It stays a STOP until the author decides. It has not occurred in any B1 run.
- **M14, declared ranges.** `digits_mlp` declares `allowed_ranges` that neither the harness nor the node enforces. Out-of-range values execute. They cause a STOP only indirectly, through time: the 3,600 s worker timeout, counted toward the 12 h deadline. Enforcing the declared ranges would change outcomes of valid trials, so it is the author's decision. It is left unchanged.

## 6. Can the 89 completed `_c` roots be reused? (assessment only)

- **What completed.** 89 roots: the two software anchors (12 each), `qwen25_coder_7b`, `qwen38_27b`, `qwen36_27b` and `gemma4_31b` (12 off each; 4 on each for the three switchable models), and 5 of `olmo31_32b`'s off roots. Their server intervals took about 6.1 h of the 6.3 h run.
- **Scientific identity.** The fix changes only proposals that previously stopped (§4.1 steps 1–3), context overflows and unencodable replies, which also previously stopped. The two exceptions of §4.2a (a summary surrogate on a root's last proposer call, or on a proposal the D25 loop would have replaced) are not fully detectable from the `_c` records: a non-final D25 revision leaves no trace, so a reuse procedure would need the scan plus the replay to exclude them. The journal is evidence only, not decision input. No completed root contains either kind, or it would not have completed. So under the fix each completed root's ledger, events and decisions are what the new code would have produced from the same replies. Seeds, prompts and requests are unchanged; the new request path differs only in the journal write. The replay would not even be needed: the records exist.
- **What blocks reuse in the current code:**
  1. The new `b1_batch` verification requires `b1_proposals.jsonl` and a `proposal_journal` manifest field in every LLM root; `_c` roots have neither.
  2. Every root is bound to the `_c` authorization: `job.authorization_checkout_head` = `4b312844`, the job binding, and the post-check certificate. `b1_batch` refuses roots from another authorization head, and the `_d` run HEAD differs by construction.
  3. The ranking would combine roots from two runs and two code heads. `olmo31_32b`'s 5 roots would be mixed with its rerun roots unless whole candidates only are reused.
- **What reuse would need:**
  - an import procedure that verifies the `_c` roots under the `_c` code and re-certifies them for `_d`;
  - a rule exempting them from the journal requirement;
  - a PLAN row and an independent review of all three;
  - reusing whole candidates only (not `olmo31_32b`'s partial set);
  - disclosure in the appendix.
- **Benefit:** about 6 h of TASL-7 GPU time.
- **Recommendation:** do not reuse. Rerun everything in `_d`. One run, one HEAD, one evidence schema is simpler to verify and to report. The only cost is GPU time. Reuse is feasible if time becomes critical, through the procedure above; it is not part of this delivery and is not adopted.

## 7. What this report does not establish

- The exact text of trial 020's reply (§1.4, replay).
- That no other model output can stop B1. The inventory covers every path where model text enters (§2) as of `4b312844` + `a3fedbb`; any new path would need its own review.
