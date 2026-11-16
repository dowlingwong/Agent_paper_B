# M2 X5 v2 B1 rule independent review — 5 November 2026

AI-assisted (Codex). Reviewed checkout `cd47229`, rule SHA-256 `79d8c5cb315d999dcad869afe696dd36c2e0c50e55eb0d9c6a9352510168eb20`. Verdict: **NOT ACCEPTED** pending the rule-level repair below. This is a B1-scoped review; B2 ranking remains outside scope and its existing STOP is not lifted.

## Finding F1 — required decisions are not fully expressed in the frozen rule

`r1/exam/rules/x5_rule_v2.yaml:7-8` has `d28_pass: true`, but does not say that only thinking-off results determine that pass. `:16-21` has a descriptive comment and a node and budget, but does not encode the retained thinking-on sensitivity and four-instance design as machine-readable requirements. `r1/exam/analyze.py:24-35` only validates the sensitivity node and does not require these author-selected semantics. The overnight instruction explicitly asks to apply both decisions to the rule and code. Thus code behavior alone cannot establish that a reader of the byte-pinned rule sees and verifies the full frozen choice.

**Unblock:** add explicit machine-readable scope and retained sensitivity fields, validate them and their fixed seed/count relationship, add positive and negative tests, recompute the SHA and update its bindings; same reviewer rechecks. **Who:** Mac primary implementer. **Effort:** bounded code, fixture, and digest updates.

## What does work in the inspected candidate

`r1/scripts/exam_runner.py:350-370,386-407` schedules the switchable eligible model's second mode on `openml_credit_approval`; B1 takes the configured four seeds, and D28 for v2 is calculated from primary roots only with thinking-on D28 separately recorded. `r1/exam/runtime.py:201` enforces B1 instance seeds 9001–9004. `_b1_row_v2` in `r1/exam/analyze.py:165-184` computes primary statistics from off observations and marks sensitivity descriptive. Existing tests include a failed on/passed off D28 and its reverse (`r1/tests/test_exam_x5_rule_v2.py:509-538`). If Stage A grammar disabled thinking-on, the runner omits it and records the reason (`exam_runner.py:350-352,395`); that is an existing mechanical limitation, not a finding that every switchable model will yield a sensitivity result.

Independent local CPU-only run using the harness virtual environment and seven explicitly selected synthetic analysis/fake-runner tests: **7 passed, 65 deselected**. No server, model, GPU, or experiment was run. The B1 public entry remains STOP in the reviewed snapshot (`exam_runner.py:302-304`), so these results do not establish production-path readiness.

## Classification and remaining work

`docs/r1/reports/MAC_M2_FAILURE_CLASSIFICATION_20261105.md` lists all 39 pre-existing failure IDs and marks B1-associated/shared cases and one unresolved nested test as ineligible for exception. Its assertion about prior logs is a separate evidence-analysis acceptance (see `docs/r1/reviews/MAC_M2_FAILURE_CLASSIFICATION_REVIEW_20261105.md` if present); this review does not substitute for fixing or re-running those tests. The classified B1-path failures, production entry, exact code commit, Stage A input/host preflights, and unsigned author decisions remain separate blockers. Rule acceptance would not itself authorize a B1 run.

## Same-reviewer recheck of candidate `839a7b583b7c36f31f383ad203158a79665f08ae`

**ACCEPTED for the frozen B1 rule and the two specified decision semantics only.** The candidate rule bytes hash to `53018aa78357c8ae18aed6b165fa22db7572815694d10f052da4aa186e8816ad`; the checksum file and the two exam v2 configs carry that same hash. The repaired rule explicitly names `d28_scope: thinking_off_only` and an enabled, four-instance, `on`, descriptive-only sensitivity on `openml_credit_approval`. `analyze._validate_v2` refuses other values; `ExamRunner` enforces the four fixed B1 instance seeds. The B1 runner's off-only D28 and separate descriptive on D28 behavior are covered in both directions. If an eligible switchable model's Stage A grammar disallows thinking-on, the candidate stops before any model or root runs, rather than silently omitting the specified sensitivity. The reasoning budget is 2048 in the rule and the runtime's actual server policy.

Independent local CPU-only command (pinned harness virtual environment): `AR_HARNESS_ROOT=/Users/wongdowling/Documents/autoresearch_harness /Users/wongdowling/Documents/autoresearch_harness/.venv/bin/python -m pytest -q r1/tests/test_exam_x5_rule_v2.py -k 'v2_mode_fields or v2_loads_only or v2_with_bare or thinking_on_with_higher or always_on_model or runner_v2_b1_skips or runner_v2_d28_gate or v2_refuses_changed_sensitivity or v2_refuses_d28_scope or b1_stops_before_running or v2_configs_bind_rule'`: **15 passed, 65 deselected**. All executed tests used synthetic inputs; no server, model, GPU or experiment was run.

This acceptance does not accept the candidate's newly enabled production B1 entry or observer integration, resolve the other B1-path test failures, establish the author note or row, or authorize execution. Those remain separate independently reviewed and author-gated work. B2 ranking is explicitly out of scope and remains STOP.
