# Independent STOP 1 review — 26 October 2026

AI-assisted independent reviewer; ENGINEERING_ONLY / DRYRUN. No implementation code or experiment data edited. Review authority: `docs/r1/prompts/PORTAL_EXAM_RUNBOOK.md` §0, Phase 1 gaps 1.1–1.10 and STOP 1; PLAN §10 R1-EXAM-POOL/FIT/CTX/HOST/PROTOCOL/REVIEW/ORNITH/STORAGE/LICENCES/TRANSFER/USER-RUNTIME, R1-SCHEMA and R1-QUANT-SOURCE; RUNBOOK Tracks X and H.

## Initial scope and verdict

Reviewed paper `8304156..e6f42c0` and harness `6afdb0e..897d83c` on `exam-x-20261026`. Paper author decisions `acf0426` / `ef2377a` precede implementation; frozen rule commit `4b9c656` precedes runner/dryrun implementation `e6f42c0`. The effective pool is 21 candidates and three anchors; approved production paths are `/home/dowling/exam-x/{models,work}` with a decimal 100 GB floor. No real inference, weight download, remote mutation or merge was performed.

**Initial verdict: CHANGES REQUIRED.** Three MAJOR findings below require fixes and reviewer recheck. This is not Phase 2 authorization, evidence-run authorization, host acceptance, or merge approval.

## Findings

### MAJOR M1 — A candidate with no auditable proposals aborts all B1 analysis

At initial paper commit `e6f42c0`, `r1/exam/analyze.py` §`b1_summary`, the primary-audit branch says `if not primary: raise ValueError('no primary audited increments')`. A COMPLETE candidate whose attempts are all schema failures, inert edits or duplicates therefore prevents every other candidate's B1 report and finalist selection. X.5 requires failed-proposal diagnostics and eligibility filtering; Phase 1.1 explicitly expects parse failures to be counted. Preserve an unrankable candidate row with its diagnostics and an explicit reason, exclude it from ranking, and continue analyzing other candidates. Retain fail-closed rejection of malformed or inconsistent audit evidence. Regression should mix a valid candidate and an empty-audit candidate, including `d28_pass=True` supplied by a malformed upstream row so a null mean cannot reach ranking.

### MAJOR M2 — B2 re-enables a mode rejected by Stage A grammar qualification

`r1/scripts/exam_runner.py` §`evidence`, initial lines 108–113: B1 suppresses thinking sensitivity when `thinking_disabled_due_grammar` is true; B2 appends the opposite mode for the first three finalists without that check. The runbook Phase 3 step 3 requires thinking off when the grammar cannot constrain only the final answer. A synthetic runner with an accepted Stage A row `{passed: true, thinking_disabled_due_grammar: true}`, a switchable candidate, and B1 selected mode `off` invokes server modes `['off', 'on']` in B2. Reproduction: `/private/tmp/exam-review-counterexamples.py`, output `ATTEMPTED_UNQUALIFIED_THINKING_ON`. Enforce the Stage A restriction in B2, including rejection of an upstream chosen-on mode inconsistent with qualification; record why an unavailable sensitivity was omitted.

### MAJOR M3 — Resume identity does not bind Stage A and B1 source bytes

`r1/exam/runtime.py` §`ExamRunner.__init__`, initial line 140 hashes the config, registry, frozen rule and value grids, but the config contains only paths for `stage_a_table` and `b1_analysis`. `r1/scripts/exam_runner.py` §`evidence` rereads those files on every invocation. Editing their contents at unchanged paths leaves `runner.binding` unchanged, allowing eligibility, footprint, finalists and thinking modes to change between parts of a resumed campaign. Synthetic constructor comparison produced `CHANGED_STAGE_A_AND_B1_CONTENT_RETAINS_BINDING: True` in `/private/tmp/exam-review-counterexamples.py`. Bind the exact upstream artifacts used by the phase into the immutable phase identity, retain their digest provenance, and refuse changed bytes before reusing completed roots. Add positive resume and changed-input rejection checks.

### MINOR m1 — B1 report incompletely summarizes its recorded A4 forecasts

`r1/exam/observer.py` §`SelfForecastObserver.observe` records both `p_no_effect` and `p_delta_positive`; `r1/exam/analyze.py` §`b1_summary` scores only the latter and returns its mean log score and Brier score. X.5 asks for A4 log score and calibration. Expose forecast coverage/query failures and a calibration diagnostic; state the no-effect evaluation convention or explicitly mark its evaluation pending rather than implying both recorded questions have been scored. This does not authorize inventing a new scientific no-effect threshold.

## Independent verification

Both full suites were launched independently, concurrently, in scratch CPython 3.13.4 with the prescribed PATH/PYTHONPATH, thread limits, no bytecode/cacheprovider, and `--continue-on-collection-errors -q -ra`. Synthetic loopback checks ran with socket permission. Exact commands and evidence are in `/private/tmp/exam-review-{paper,harness}.log` and the corresponding JUnit XML files.

- Harness: **454 passed, 8 failed, 1 collection error**, 95.39 s. The exact FAILED and ERROR ID sets match committed `docs/r1/reports/exam_phase1_20261026/harness_baseline.log`; no added or removed failure IDs. Baseline: 448 passed, 8 failed, 1 collection error.
- Paper: full suite still running when this initial finding record was written; final comparison pending. Baseline: 417 passed, 22 failed, 9 skipped.
- Standalone fake-server dryrun: **PASS**, all eight summary checks true; two fake candidates plus three anchors, Stage A, 1-instance B1 on two nodes, thinking sensitivity, one killed worker, preserved partial attempt, successful resume, completed-root hashes unchanged. Evidence: `/private/tmp/exam-x-review-20261026-independent/summary.json` and phase logs beneath that root. Synthetic metrics are not scientific evidence.
- Source review covered schema/provider/parser opt-in behavior, observer accounting and information isolation, random-valid active-key/grid sampling, namespace refusal, 3 hand-checked fit-test configurations, source/licence/occupancy/frozen-rule guards, runner host/storage/model/build/offload checks, Stage A qualification and analysis. Pending Phase 2 artifact/host placeholders remain intentional; no real host or model acceptance is claimed.

## Acceptance recheck

Pending implementation fixes, focused reviewer reruns, full-paper failure-ID comparison, final handoff review and an explicit independent verdict.

### Fix recheck — paper 930687c, 57f56e5 and df1a6eb

All original findings are resolved at paper `df1a6eb6181eefdd53f80420f5773150f2b594a5` (harness remains `897d83c8efa364ec2fdd37288241cc42e01d7274`):

- **M1 resolved.** Empty-audit candidates retain null mean, unrankable reason and diagnostics; ranking excludes them. My independent mixed-row check retained one valid finalist and excluded the empty candidate even when the latter supplied `d28_pass=True`.
- **M2 resolved.** B2 rejects a chosen-on mode disabled by Stage A and suppresses the unavailable opposite-mode sensitivity. Independent fake runner checked both branches and observed only `['off']` for the qualified path. Manifests record the omission reason.
- **M3 resolved.** Expected Stage A/B1 SHA values are part of config/resume identity and author-bound input scope; the evidence entry point verifies actual bytes before roots execute. My tests independently rejected changed source bytes with unchanged expected digest and confirmed that updating an expected digest changes the resume identity. Manifests retain source SHA provenance. It is correct for the identity to remain unchanged when actual bytes alone are altered, provided the mismatch stops execution before reuse.
- **m1 resolved.** B1 exposes primary forecast coverage, observer query/failure counts and five fixed descriptive calibration bins. Both no-effect probabilities remain recorded; their evaluation is explicitly pending an author outcome definition. Independent endpoint/missing-forecast checks verified 2/3 coverage, one failed query and correct p=0/p=1 bins. This does not adopt a scientific no-effect threshold.

Independent property scripts: `/private/tmp/exam-review-fix-properties.py` and the separate forecast-summary check. Focused reviewer suite including the final fake end-to-end test: **31 passed in 48.86 s**, `/private/tmp/exam-review-final-focused.log`. An earlier independent fix rerun gave 29 passed in 49.88 s. Placeholder config check passes and retains the production host/source/authorization gates. Handoff authorization-field documentation was rechecked after its update.

**Final independent acceptance remains pending only the required full-paper suite comparison.** The initial full-suite run continues; baseline failure IDs must be compared before recording ACCEPTED.

### Final independent verdict — ACCEPTED

The required independent full-paper regression checkpoint completed: **445 passed, 21 failed, 9 skipped in 696.16 s**. Exact failure-ID comparison, preserving spaces within parametrized IDs, finds **zero added failure IDs**, zero added collection errors, and one removed baseline failure: `r1/tests/test_c3_sweep_dryrun.py::test_c3_sweep_dryrun_watchdog_restarts_a_killed_runner`. Its passing observation in this environment is not a proven causal repair. The other 21 failures match baseline IDs. Harness remains **454 passed, 8 failed, 1 collection error**, with exactly the baseline failure/error sets. These are regression comparisons, not all-green suites or Linux host validation.

The two full suites were launched at initial implementation paper `e6f42c0` / harness `897d83c`, before review fixes. They establish that broad regression checkpoint. Final implementation through paper `df1a6eb` was separately checked with **31 passing focused exam tests**, including the final fake-server end-to-end kill/resume test, plus the reviewer's independent counterexample/property reruns described above. Later paper `b3764a3` contains evidence/handoff documentation and strengthened empty-audit test input; it introduces no further implementation changes. This distinction is intentional: no claim is made that the complete broad suites were rerun after every correction.

The concrete handoff `docs/r1/overnight/EXAM_X_CODE_HANDOFF.md` has been reviewed, including scope, source/hash and authorization requirements, synthetic labels, remaining host/model/prompt/evidence gates, and implementation references. The final handoff counts and preserved comparison JSON were read after the executing agent inserted them; they agree with my independent results. The executing agent may now record this verdict in STATUS and commit the review.

**ACCEPTED for Phase 1 code completion and its ENGINEERING_ONLY / DRYRUN checks.** All three MAJOR findings and the MINOR finding are resolved. STOP 1 independent review is satisfied. This verdict does not authorize Phase 2 execution, protected-branch merges, model downloads, scientific evidence runs, author rule adoption, or venue/publication claims. Those actions retain the runbook and author gates.
