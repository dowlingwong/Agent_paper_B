# Review of M2: `x5_rule_v2` and its code (4 Nov 2026)

**Reviewer:** a fresh, independent reviewer subagent (Claude). AI-assisted. I did not write the work under review.
**Scope:** branch `mac-x5v2-20261104`, range `74a07907..8eae4f84`: `4f0fa69b` (code, rule, configs, tests) and `8eae4f84` (hand-off).
**Governing text:** MAC_LOCAL_RUNBOOK_20261104 rev 3.3 §0 and M2 (`mac-int-20261104`); `proposals/X5_RULE_V2_DRAFT_20261104.md`; PLAN §10 rows R1-MAIN-PROPOSER (a), R1-EXAM-ALWAYS-ON-SKIP, R1-EXAM-B1-HARNESS-PIN, R1-EXAM-TEMPLATE-AMENDMENT-IMPLEMENTED, R1-EXAM-STOP9-JOURNAL, R1-TRACKX-HANDOVER-RULING (with its consequences) and R1-EXAM-A1-M1-REQUIREMENTS (1); packet `AUTHOR_DECISIONS_20261104.md` §0 and (d).

## Verdict: **not accepted**

The work is careful and mostly faithful. The rule file is semantically identical to the draft. v1 and Stage A are untouched. The template-repair proof and the harness binding are real. The failure set equals the base's.

Two MAJOR findings block acceptance:
- **F1:** the B2 analysis can still rank v2 manifests under v1 semantics with no error. This is the silent fallback the brief asks about.
- **F2:** the descriptive thinking-on sensitivity runs can change a model's v2 eligibility through `d28_pass`.

Both are small fixes. The remaining findings are MINOR.

## What I verified myself

| Check | Result |
|---|---|
| Base suite at `74a07907`: temporary detached worktree, `AR_HARNESS_ROOT` = harness `897d83c`, CPU, Linux container | **28 failed / 842 passed / 1 skipped** |
| M2 suite at `4f0fa69b` (temporary detached worktree, same environment) | **28 failed / 882 passed / 1 skipped** |
| Failure sets compared (sorted test ids, `diff`) | **Identical.** The hand-off's list of 28 matches exactly. |
| `test_exam_x5_rule_v2.py`, verbose | 40 passed, **0 skipped**. Both harness tests ran: the a3fedbb positive test and the 897d83c negative control. |
| `sha256(x5_rule_v2.yaml)` (working tree and `git show` blob) | `79d8c5cb315d999dcad869afe696dd36c2e0c50e55eb0d9c6a9352510168eb20`. It equals the `.sha256` file, `exam_b1_v2.json`, `exam_b2_v2.json` and the hand-off. |
| `x5_rule_v1.yaml`, its `.sha256`, `exam_portal.json` | Byte-unchanged (`git diff` empty). v1 sha is `0665903b…`. `analyze.RULE` and the `load_rule` default are still v1, and the portal still binds v1. |
| v2 YAML against the draft YAML (`yaml.safe_load` of both) | **Semantically equal.** Only three comments differ. |
| Registry counts in the corrected comment | Confirmed among the 20 candidates: 12 switchable with `off_switch`, 4 non-thinking, 4 always-on. The draft's 14/5/3 is wrong. |
| Files changed in the range | Only `r1/exam/{analyze,campaign,runtime}.py`, `r1/exam/rules/x5_rule_v2.yaml(.sha256)`, `r1/scripts/exam_runner.py`, `r1/scripts/configs/exam_b{1,2}_v2.json`, `r1/tests/{test_exam_x5_rule_v2.py,exam_cache_prompt_driver.py}` and the hand-off. No PLAN, STATUS, RUNBOOK, `c3_label_sweep.py` or harness edits. |
| D22 guard (`exam_runner._evidence_unreviewed`, `free_sensitivity` / PLAN `D22` line check) | Lines unchanged. The only new `free_sensitivity` mentions are in the added v2 B2 branch. `test_d22_guard_unchanged_under_v2` passes. |
| Harness driver, run by me under `/home/claude/wt/harness-a3fedbb` (HEAD `a3fedbb`) | 3 requests, all with `cache_prompt: false`. `cache_prompt_evidence` = `{all_false: True, llm_call_events: 3, trial_llm_call_records: 3}`. |
| Tamper checks on that evidence | One `llm_call` event set to `true` → STOP. One trial `llm_call` record with the field removed → STOP ("MISSING"). |
| M5 claim | Confirmed. No `TRACKX_STAGEA_STOP9_NONGEN_REVIEW_20261104.md` and no A1 code-review file exists on any local or `origin/*` ref. The v17 review hash is `2d86425d…` in `reports/EXAM_TRACKX_STAGEA_STOP9_20261104.md` but `131dad8d…` in PLAN R1-EXAM-STOP9-JOURNAL and STATUS. |
| Commits | Author `Dowling Wong <wangdowling@gmail.com>`; bodies say AI-assisted and carry the attribution lines. The branch is pushed (`origin/mac-x5v2-20261104` = `8eae4f84`). |

I removed both temporary worktrees afterwards with `git worktree remove`.

## Findings

### F1: MAJOR. `b2_summary` silently ranks v2 manifests under v1 semantics

**Evidence.**
- `b2_summary(manifests, *, rule_path=None, …)` takes the v2 path only when it is given a rule that loads as v2.
- Without a rule, or with v1, it runs the old summary. That path does not check `rule_sha256` or `rule_version`, and it ranks by final Y regardless of mode.
- `analyze.main` passes `--rule`, but `--rule` defaults to `RULE`, which is v1.

So `python -m r1.exam.analyze b2 <v2 manifests>` without `--rule` silently applies v1. I reproduced this with two v2-stamped primary manifests: `on_model` (mode `on`, Y = 0.9) and `off_model` (mode `off`, Y = 0.5). Both `b2_summary(ms)` and `main(['b2', …])` with the default rule returned the order `['on_model', 'off_model']`, with no error.

This is exactly what R1-MAIN-PROPOSER (a) forbids: a thinking-on row winning B2. Through the default path it also defeats the new `refuses a primary B2 manifest in mode …` guard. `b1_summary` is protected, because it compares each manifest's `rule_sha256` with the loaded rule. `b2_summary` is not.

**Fix.**
- In `b2_summary`, when called without a v2 rule, refuse any manifest that carries `rule_version == 'x5_rule/v2'` or the v2 sha.
- When a rule *is* given (v1 or v2), require every manifest's `rule_sha256` to equal the loaded sha.
- If backward compatibility for the no-rule call is needed, keep the no-rule path only for manifests that carry no `rule_version`.
- Add a test that v2 manifests through `b2_summary(ms)` and through `main(['b2', …])` without `--rule` both raise.

### F2: MAJOR. Descriptive thinking-on sensitivity roots feed `d28_pass`, which is a v2 eligibility condition

**Evidence.**
- In `_evidence_unreviewed`, `d28=all(all(n['pass'] …) for r in root_results)` runs over **all** roots of the model. Under v2, for a switchable model in B1, that includes the thinking-on roots on `b1_sensitivity.node`.
- The manifest's `d28_pass` feeds `choose_finalists` (`r.get('d28_pass')`).
- I ran the B1 body with every off root passing D28 and the thinking-on sensitivity root failing it. The manifest came out with `d28_pass = False`, so the model is excluded from v2 ranking.

Under v2 the thinking-on rows are "descriptive only" (rule comment; draft "Keep the thinking-on sensitivity rows as a separate descriptive field"), and R1-MAIN-PROPOSER (a) selects "on thinking-off performance". Letting a descriptive run remove a model from selection contradicts both. The code is inherited from v1, where the sensitivity mode could become the B2 mode, so including it there was defensible. M2 changed the role of those runs and did not carry the change through here.

**Fix (pick one).**
- (a) Under v2, compute `d28_pass` over the primary-mode (`off`) roots only. Record the sensitivity roots' D28 separately, for example as `thinking_on_sensitivity_d28`. Add a test for the case above.
- (b) If the agent thinks this is the author's call, keep the code as is but list it as an explicit open question in the hand-off and the draft row. Do not leave it implicit.

Option (a) is a consistency edit that follows from the rule's own wording, so I recommend it.

### F3: MINOR. The "descriptive sensitivity node" is an open author question, presented as a decided deviation

**Evidence.**
- The draft's "Open for the author" section asks whether to keep the thinking-on sensitivity node: descriptive under v2, one node per switchable model, about 12 models × 4 instances.
- R1-EXAM-ALWAYS-ON-SKIP rules only on always-on models.
- Hand-off §6 item 5 says the node is "kept", and §7 (open questions) does not mention it.

Keeping it reproduces the draft YAML verbatim, so the frozen file is faithful. But the choice is inside the sha'd file: if the author later drops the node, the rule gets a new sha. Packet (d)'s "Only the sha row remains" does not record a ruling on this point.

**Fix.** Move it to hand-off §7 as a question the author answers before committing R1-EXAM-RULE-X5V2. It can also be stated in the paste-ready message.

### F4: MINOR. Judgement of the declared deviations

1. **Default rule path stays v1.** Correct: the runbook directs it.
2. **Registry-count comment corrected inside the sha'd file.** Acceptable. It corrects arithmetic (allowed by §0), it has no semantic effect (YAML-equal to the draft), and the rule is not yet frozen by any PLAN row. The hand-off should also tell the author that the draft text (14/5/3) is now stale.
3. **Optional rule argument to `b2_summary`.** The design is fine, but in its current form it is the source of F1.
4. **Descriptive sensitivity node.** See F3. This is the one item that should be put to the author, not decided.
5. **Validator accepts `run_descriptive`.** Harmless, because the frozen file says `skip`. However, the `run_descriptive` path is untested in both `_b1_row_v2` and the runner. Under `run_descriptive` an always-on model would run B1 with primary mode `always_on`; the v2 row would be built with `mu_hat_mode: 'off'` and thinking-off μ̂ over zero `off` observations (so `mu_hat=None`). That is a mislabel, and nothing exercises it. Either reject `run_descriptive` in `_validate_v2` until the author chooses it, or add a test.

None of these is a decision the agent should not have taken, apart from item 4.

### F5: MINOR. Harness test portability and the Mac "Done when"

**Evidence.**
- `_b1_harness_root()` looks for `$AR_HARNESS_B1_ROOT`, then `/home/claude/wt/harness-a3fedbb`, then `<repo parent>/autoresearch_harness_a3fedbb`. It **skips** if none exists. On the Mac none of the defaults exist unless the variable is set, so the step-0 test would silently skip.
- The negative control likewise skips unless `AR_HARNESS_ROOT` is exactly `897d83c`.
- "Done when" requires the tests to pass on the Mac CPU. The hand-off honestly reports a Linux container run.

**Fix.**
- Document the required `AR_HARNESS_B1_ROOT` in the hand-off. Better, make the test fail rather than skip when an opt-in variable (for example `R1_REQUIRE_B1_HARNESS=1`) is set.
- Have the integrator run the suite on the Mac with both harness tests reported as *passed*, not skipped, before accepting the "Done when".

### F6: MINOR. "Recorded in the manifest" is shown for the would-be manifest field, not a real `campaign_manifest.json`

`collect` stays behind its STOP, so the test proves the field that `cache_prompt_evidence` would write. It does not prove a written manifest. The hand-off §4 states this limitation, and the building blocks are the ones `collect` uses (`exam_manager`, `run_real_campaign` with the same arguments), so this is acceptable for M2.

When `collect` is unblocked, add a test that runs `collect` itself in DRYRUN and reads `campaign_manifest.json['cache_prompt']`.

Note also that `LLAMACPP_CACHE_PROMPT=true` in the operator's environment would flip the wire value at a3fedbb. `cache_prompt_evidence` catches this only after the root has run. A pre-flight check in the runner (refuse B1/B2 if `LLAMACPP_CACHE_PROMPT` is set to anything other than false or empty) would fail earlier at no cost.

### F7: MINOR. B2 v2 accepts a finalist with no B1 analysis row

`row=next((r for r in screen['rows'] if …),None)`, and `row is None` passes silently. For the normal (non-`free_sensitivity`) B2, every finalist must have a B1 row. **Fix:** STOP when `row is None and not cfg.get('free_sensitivity')`.

### F8: MINOR. Untested or loosely failing paths

- `runtime.author_gate`'s new clause (the authorization note must bind `stage_a_amendment_table_sha256` and `…_acceptance_sha256`) has no test. Add one positive and one negative case.
- `stage_a_pass_set` on an amendment table row without `candidate` raises `KeyError` instead of `PreparationStop`. It still fails closed, but with an unclear message.
- The amendment rows' shape (`qualification.footprint_mib`, `model_sha256`, `build`, `thinking_disabled_due_grammar`) is assumed. The hand-off flags this for the O1 receiving review, which is correct.
- The digest-mismatch STOP test covers `olmo31_32b` only. The brief asks for all three repaired models. Parametrize `test_b1_b2_repair_digest_mismatch_is_a_stop` over `REPAIRED`.
- The `phase` parametrization in `_served_args` only sets `state['phase']`. `_server` has no B1- or B2-specific branch, so it is nominal. The real B1/B2 proof is the combination with `test_runner_passes_registry_repair_to_server_and_records_sha`, which is adequate. Say so in the test docstring.

### F9: MINOR. Config detail: `gpu_uuid` is TASL-7's while `host` is open

Both v2 configs keep `gpu_uuid: GPU-ab72fb4a-…` from `exam_portal.json` (TASL-7). Their own comment says the host is open, with TASL-2 proposed and `collect` TASL-2-only. If B1 runs on TASL-2, this pin is wrong. `host_check` and `gpu_sample` would STOP, but by failing, not by design. **Fix:** set `gpu_uuid` to `TODO_AUTHOR_R1_HOSTS_04NOV_GPU_UUID` until R1-HOSTS-04NOV is decided.

Dropping `d3_policy` is acceptable: it is read only by the Stage A path (`exam_runner.stage_a`, `cache_runtime.authorize_cooperative_stagea`). B1 GPU exclusivity is a later authorization matter.

### F10: MINOR. `olmo31_32b_think` (role `sensitivity`, always-on) is skipped in B1 under v2

The runner's skip covers roles `candidate` and `sensitivity`. This is consistent with R1-EXAM-ALWAYS-ON-SKIP ("always-thinking models do not run B1"), and the model failed Stage A on grammar in `t7h8` anyway. Still, it removes a declared registry sensitivity row from B1. Mention it in the hand-off so the appendix (requirement (3), M8) reports it from Stage A as well.

## Checklist against the brief

1. **"Done when" tests.** Each listed test exists and tests what it claims:
   - YAML mode fields are strings, including a bare-`off` negative test;
   - v2 loads only with its sha;
   - always-on never a finalist, through both a B1 refusal and the finalist filter;
   - thinking-on with higher Y never wins, in both B1 and B2;
   - ties go to lower GPU-h, with None last;
   - B2 refuses a non-off primary for `on`, `always_on`, `False` and `None`;
   - v1 tests still pass (`test_exam_core.py` is not in the failure set).

   The failure set equals the base's. Still open: F1 (the refusal is bypassable through the default path) and F5 (the Mac run).
2. **v1 and portal byte-unchanged; v1 default; sha bound everywhere.** Yes.
3. **v2 faithful to the draft and R1-EXAM-ALWAYS-ON-SKIP.** Yes; the deviations are judged in F4, with F3 to be put to the author.
4. **Harness binding.** Real. `cache_prompt: false` is on the wire, in the `llm_call` events and trial records, and in the evidence field, at `a3fedbb`. The negative control at `897d83c` is meaningful: no field on the wire, and the evidence STOPs. Gaps are F5 and F6.
5. **Stage A pass set.** Implemented as sha-bound config inputs (`stage_a_amendment_table` and `…_acceptance`, both with sha256), refused when missing, placeholder or mismatched. Only registry `candidate` rows enter from the amendment table, so anchors stay anchors. No model list is hardcoded. D28 and thinking-off conditions still apply in `choose_finalists`, subject to F2.
6. **Template repair.** Confirmed by reading the code. Both B1 and B2 start their servers through `ExamRunner.server` → `_server`, which builds `EXAM_SERVER_ARGS + template_repair_args(spec)`. That is the only server construction path; watchdog failures STOP rather than restart. `_evidence_unreviewed` passes the registry spec, including `template_repair`. The tests cover all three repaired models × {b1, b2}, a digest-mismatch STOP (`olmo31_32b` only, see F8), no flag for `qwen38_27b`, and the sha recorded in the manifest with a STOP on a config-registry mismatch. Requirement (1) for B1/B2 is met. The sweep part belongs to M4, and the hand-off §3 guidance for it is sound.
7. **D22 guard and scope.** Unchanged and in scope.
8. **Hand-off accuracy.** Test counts, sha, failure list and the M5 finding are accurate. The open questions need F3 added, and F2 if option (b) is chosen. The draft row R1-EXAM-RULE-X5V2 is well-formed and carries the right sha. Beyond packet (d), it adds only a restatement of R1-EXAM-A1-M1-REQUIREMENTS (1), which is not a new decision. One note: the row names code `4f0fa69b`, so it must be updated to the commit that finally passes review. The YAML sha stays as long as the rule file is not touched.
9. **Code quality and silent fallbacks.** F1 is the one silent fallback that lets B2 be analysed under the wrong rule. The runner side fails closed. Under v2 it requires `cache_prompt is False`, harness `a3fedbb` outside DRYRUN (on top of `ExamRunner.__init__`'s HEAD check), a config-registry template binding, per-root `all_false` evidence, and that the B1 analysis's rule sha equals the runner's.

## Required for acceptance

- F1 fixed, with tests.
- F2 fixed by option (a) with a test, or turned into an explicit open author question by option (b).
- F3 added to the hand-off's open questions.

The MINOR findings may be fixed now or carried as recorded follow-ups. F5's Mac run is the integrator's check before "Done when".
