# M2 hand-off — `x5_rule_v2` and its code (4 Nov 2026)

**Written by a worker subagent of the Mac-local agent (Claude), MAC_LOCAL_RUNBOOK_20261104 rev 3.3, task M2; AI-assisted. This is input to an independent review, not accepted work. Nothing here is a decision.**

- Branch `mac-x5v2-20261104`, base `74a07907` (head of `codex/trackx-stagea-cooperative-20261031`; config binding `74a0790`, code `ab74203`), per the author's 15:44 ruling (packet §0, R1-TRACKX-HANDOVER-RULING).
- M2 code commit: **`4f0fa69bf71e3f493b79dee5b627426b447083ca`** (`4f0fa69b`). This hand-off is a separate, documentation-only follow-up commit on the same branch.
- **`x5_rule_v2.yaml` sha256: `79d8c5cb315d999dcad869afe696dd36c2e0c50e55eb0d9c6a9352510168eb20`**
- `x5_rule_v1.yaml` unchanged: `0665903b276f34eca4cd4d03ac483192cd3ef3b41c24d188e2dd103d65423b6e`.

## 1. M5 check (step 0): independent review of `e996af8` / `ab74203`

What the committed sources say (coordinator `10742f85`, also carried into `mac-int-20261104`):

| Code | Cited review | Where cited | Review file committed? |
|---|---|---|---|
| `e996af8` (A1 amendment; binding `96f1146`) | design review "approval with conditions" `251f18a7…`; scoped code review **ACCEPT with conditions** `90609c9b…`; v16b snapshot `55770d1b…` (64 entries / 62 files; 408 passed / 1 skipped) | PLAN R1-EXAM-TEMPLATE-AMENDMENT-IMPLEMENTED; STATUS; `reports/EXAM_TEMPLATE_AMENDMENT_IMPLEMENTED_20261104.md` | **No.** No review file for A1 exists under `docs/r1/reviews/` on any local or `origin/*` ref. |
| `ab74203` (STOP 9 journal fix; binding `74a0790`) | `reviews/TRACKX_STAGEA_STOP9_NONGEN_REVIEW_20261104.md` **ACCEPT with conditions**, v17; v17b gating fix snapshot `4fef681e…` (410 passed / 1 skipped) | `reports/EXAM_TRACKX_STAGEA_STOP9_20261104.md`; PLAN R1-EXAM-STOP9-JOURNAL; STATUS | **No.** The cited file `TRACKX_STAGEA_STOP9_NONGEN_REVIEW_20261104.md` is not in any ref (checked all local and `origin/*` refs). |

**Inconsistency:** the v17 review hash differs between sources — the STOP 9 report gives `2d86425d…`, while PLAN R1-EXAM-STOP9-JOURNAL and STATUS give `131dad8d…`. Neither hash appears on any committed file.

**Finding.** Independent reviews of `e996af8` and `ab74203` are *claimed* (ACCEPT with conditions, by hash), but the review documents and the conditions are not in the repository, and the v17 hash is inconsistent. Under the 15:44 ruling ("如果 `ab74203` 还缺独立 review，就按 M5 流程补") the integrator/author should decide whether a claimed-but-uncommitted review counts. This worker did not review the code (as instructed). M2 builds on `ab74203` and does not change any A1/STOP 9 code path (`stage_a.py`, `cache_order.py`, `qualify.py`, `template_repair_args` are untouched).

## 2. What changed

| File | Change |
|---|---|
| `r1/exam/rules/x5_rule_v2.yaml` (+ `.sha256`) | New. From `proposals/X5_RULE_V2_DRAFT_20261104.md`; every mode quoted (`"off"`); `always_on_in_b1: skip` (R1-EXAM-ALWAYS-ON-SKIP) written before the sha was computed. |
| `r1/exam/analyze.py` | `load_rule` accepts `x5_rule/v1` and `x5_rule/v2`; **default path stays v1** (`RULE`); new `RULE_V2`, `is_v2`, `_validate_v2` (refuses non-string / non-`off` mode fields, a bad `always_on_in_b1`, a missing `b1_sensitivity.node`), `thinking_off_capable` (non-thinking, or declared `off_switch`; `always_on` never). `choose_finalists`: under v2 ranks only rows with `thinking_off_eligible` and `mu_hat_mode == 'off'`. `b1_summary`: under v2 builds rows with `_b1_row_v2` — μ̂ over `mode == 'off'` observations only; refuses a B1 manifest of an always-on model when `always_on_in_b1 == skip`; refuses a non-off primary for a capable model; reads `thinking_mode.b1_sensitivity.node`; the thinking-on sensitivity is a separate descriptive field; `b2_thinking_mode` always `off`. `b2_summary(manifests, *, rule_path=None, expected=None)`: unchanged without a rule or under v1; under v2 `_b2_summary_v2` ranks only `purpose == 'primary'` and `mode == 'off'` rows by final audited Y, ties to lower GPU-h (None last), **raises on a primary manifest in any other mode**, checks the manifest's `rule_sha256`, and reports top-3 thinking-on reruns under `thinking_on_descriptive`. `main` passes `--rule`/`--rule-sha256` to `b2_summary`. |
| `r1/scripts/exam_runner.py` | New `B1_HARNESS_PIN` (`a3fedbb…`), `stage_a_pass_set`, `template_repair_record`, `check_template_repairs`. In `_evidence_unreviewed` (the B1/B2 body, still unreachable behind the unchanged `evidence` STOP): under v2 — `cache_prompt` must be `False`, the harness pin must be `a3fedbb` outside DRYRUN, the config's `template_repairs` must equal the registry's; the Stage A pass set comes from `stage_a_pass_set`; always-on models are skipped in B1 and listed in `batch_state.b1_skipped_always_on`; B1 primary is the registry's off mode, thinking-on sensitivity on `b1_sensitivity.node`, marked descriptive; **B2 mode is `"off"` for every finalist** (an analysis assigning another mode, or a finalist that cannot run off, is a STOP); the top-3 rerun is thinking-on and the manifest marks it `thinking_on_rerun: descriptive`; each B1/B2 manifest records `rule_version`, `cache_prompt`, `harness_commit`, `template_repair` (file + sha), `stage_a_pass_source`, the amendment table and acceptance shas, and per-root `cache_prompt` evidence (a root without all-false evidence is a STOP). v1 path unchanged. `main`: under a v2 rule the four amendment keys are required phase settings. The free schema-sensitivity (D22) guard is **unchanged**. |
| `r1/exam/campaign.py` | `exam_manager` (the proposer factory `collect` now calls; same arguments as before) and `cache_prompt_evidence` (fails closed unless every `llm_call` / `llm_call_failed` event and trial `llm_call` record carries `cache_prompt: false`); `collect` (still behind its STOP) records it as the root manifest's `cache_prompt`. |
| `r1/exam/runtime.py` | `load_config`: the four amendment keys are "later" settings (may stay placeholders until the phase runs). `author_gate`: when a config carries `stage_a_amendment_table_sha256`, the authorization note must bind it and the acceptance sha. |
| `r1/scripts/configs/exam_b1_v2.json`, `exam_b2_v2.json` | New. Copies of `exam_portal.json` with: `rule` = v2 path, `rule_sha256` = v2 sha, `harness_commit` = `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`, `cache_prompt: false`, `template_repairs` (the three repair shas), the four `stage_a_amendment_*` inputs as `TODO_OPERATOR_O1_*` placeholders; `host`, `paper_commit`, `authorizations` as `TODO_*`; `d3_policy` dropped (Stage A-only). |
| `r1/scripts/configs/exam_portal.json` | **Unchanged** (still binds v1). |
| `r1/tests/test_exam_x5_rule_v2.py`, `r1/tests/exam_cache_prompt_driver.py` | New tests (40) and the stand-in-server driver. |

### The Stage A pass set (draft input; R1-TRACKX-HANDOVER-RULING, packet (d))

v2 reads **t7h8 PASS ∪ operator-accepted t7j10 PASS**. This is implemented as an explicit, sha-bound config input, not a model list: `stage_a_amendment_table` + `stage_a_amendment_table_sha256` (the `t7j10` table) and `stage_a_amendment_acceptance` + `stage_a_amendment_acceptance_sha256` (the operator's O1 acceptance record). `stage_a_pass_set` refuses B1/B2 under v2 unless all four are supplied and their digests match. Only registry `candidate` rows enter from the amendment table (anchors keep their `t7h8` rows and run as anchors). D28 and thinking-off conditions apply later, unchanged. **This rests on a draft row** (packet (d) / R1-EXAM-RULE-X5V2 draft) and on the shape of the `t7j10` table, which is not yet on any branch: the code assumes it has the Stage A table shape (`label: ENGINEERING_ONLY`, `rows[].candidate/passed`). The receiving review in O1 should confirm or the reader be adapted.

## 3. Template repairs in B1/B2 (R1-EXAM-A1-M1-REQUIREMENTS (1), author 16:39)

**Check: does the B1/B2 launcher already read the registry's `template_repair`?** Yes. B1 and B2 start their servers through `ExamRunner.server` → `ExamRunner._server` (`r1/exam/runtime.py`), which builds `extra_args = EXAM_SERVER_ARGS + template_repair_args(spec)` for every phase — the same function the Stage A replay server and `qualify.py` use. `_evidence_unreviewed` passes the registry spec (deep copy, `template_repair` included) to `runner.server`. No launcher code change was needed.

**Tests added (prove it for B1 and B2):**
- `test_b1_b2_server_serves_the_pinned_repair_template` — for each of `olmo31_32b`, `devstral_small2_24b`, `ministral3_14b`, in phase `b1` and `b2`, the real `ExamRunner.server` path constructs the llama-server with `--chat-template-file <repo>/r1/exam/templates/repairs/<id>.jinja`, whose digest equals the registry sha.
- `test_b1_b2_repair_digest_mismatch_is_a_stop` — a wrong sha is a `PreparationStop` ("template repair digest mismatch") in both phases.
- `test_b1_b2_unrepaired_model_gets_no_template_flag` — `qwen38_27b` gets no `--chat-template-file`.
- `test_runner_passes_registry_repair_to_server_and_records_sha` — the B1/B2 body hands the repaired spec to the server, records `template_repair {file, sha256}` in the B1/B2 manifest (None for an unrepaired model), and a config `template_repairs` binding that differs from the registry is a STOP.

**Recorded for later sweeps:** the v2 configs carry `template_repairs` = `{olmo31_32b: 5d275f78…4820466, devstral_small2_24b: a0c0ed8a…4de5209a, ministral3_14b: 2f545122…4d8b1e8970}` (full values in the JSON), checked against the registry by `check_template_repairs`; each B1/B2 manifest records its model's `template_repair`.

**What the sweep-2 code (`c3_label_sweep.py`, M4; not edited here) must do to carry the same template** if the pick is a repaired model:
1. Read the pick's `template_repair` from the frozen exam registry (or the X.7 pick record), and pin `file` + `sha256` in the sweep config (e.g. `manager_template_repair`), refusing to start if the file's digest differs.
2. Start the sweep's llama-server with `--chat-template-file <that file>` in addition to `--jinja` and the thinking flags — preferably by calling `r1.exam.runtime.template_repair_args` (or an equivalent with the same STOP semantics), not by re-implementing it.
3. Record the template sha in the sweep manifest and per-campaign server records, and add a test like the ones above (repaired → flag + sha; mismatch → STOP; unrepaired → no flag).
4. List "served chat template (repair sha)" in the cross-proposer difference table (R1-MAIN-PROPOSER (c)) when it applies.

## 4. Harness binding (step 0)

`test_exam_campaign_request_manifest_and_llm_call_carry_cache_prompt_false` runs `r1/tests/exam_cache_prompt_driver.py` in a subprocess under the `a3fedbb` checkout (`AR_HARNESS_B1_ROOT`, default `/home/claude/wt/harness-a3fedbb`; it asserts HEAD is `a3fedbb`). The driver builds the proposer with `campaign.exam_manager`, runs the harness `run_real_campaign` with `collect`'s arguments (manager_proposal/v1 schema, append-only memory, `vary`, fixture worker) against a stand-in OpenAI-compatible server, and checks: every request body has `cache_prompt: false`; every `llm_call` event and trial `llm_call` record has `cache_prompt: false`; and the root manifest field from `campaign.cache_prompt_evidence` is `all_false`. A negative control (`test_stage_a_harness_pin_does_not_send_cache_prompt_so_b1_evidence_stops`) runs the same driver at the Stage A pin `897d83c` and shows no `cache_prompt` on the wire and the evidence STOP. Limitation: `collect` itself stays behind its "B1/B2 … not implemented" STOP, so the test drives the same building blocks rather than `collect`; the A4 observer already sends `cache_prompt: false` (existing tests).

## 5. Tests before / after

Full suite `python -m pytest -q -p no:cacheprovider r1/tests`, `AR_HARNESS_ROOT` = harness `897d83c`, on CPU (Linux container, not the Mac):

| | passed | failed | skipped |
|---|---|---|---|
| Base `74a07907` | 842 | 28 | 1 |
| After M2 (tree = `4f0fa69b`) | 882 | 28 | 1 |

The failure set after M2 is **identical** to the base's (28 tests; same names). They are environment failures unrelated to M2: the D3 cooperative-lease FD absent in this container (`test_exam_dryrun`, `test_rerun2_batch4c`), namespace/kcmp/`setns` privileges (`test_exam_namespace_fixture_program`, `test_cooperative_lease`), broken-stdout guardian tests, and the C3 sweep/control dry runs. The difference is the 40 new tests in `test_exam_x5_rule_v2.py`, all passing. `diff` of the two sorted failure lists is empty. Base failures (= after-M2 failures):

- `r1/tests/test_c3_control_dryrun.py::test_control_dryrun_end_to_end`
- `r1/tests/test_c3_sweep_dryrun.py::test_c3_sweep_dryrun_llamacpp_from_the_deepthought_config`
- `r1/tests/test_c3_sweep_dryrun.py::test_c3_sweep_dryrun_llamacpp_resumes_after_kill_mid_campaign`
- `r1/tests/test_c3_sweep_dryrun.py::test_c3_sweep_dryrun_llamacpp_watchdog_restarts_a_killed_server`
- `r1/tests/test_c3_sweep_dryrun.py::test_c3_sweep_dryrun_resumes_after_kill_mid_campaign`
- `r1/tests/test_c3_sweep_dryrun.py::test_c3_sweep_dryrun_retry_and_permanent_failure`
- `r1/tests/test_c3_sweep_dryrun.py::test_c3_sweep_dryrun_watchdog_restarts_a_killed_runner`
- `r1/tests/test_cooperative_lease.py::test_real_kcmp_proves_shared_ofd_with_a_synthetic_child`
- `r1/tests/test_exam_dryrun.py::test_exam_fake_end_to_end`
- `r1/tests/test_exam_namespace_fixture_program.py::test_dependency_manifest_digest_and_complete_set_are_required`
- `r1/tests/test_exam_namespace_fixture_program.py::test_exclusive_fixture_file_never_overwrites`
- `r1/tests/test_exam_namespace_fixture_program.py::test_explicit_flag_and_direct_tmp_path_are_required`
- `r1/tests/test_exam_namespace_fixture_program.py::test_final_event_verifier_rejects_truncation_and_out_of_order`
- `r1/tests/test_exam_namespace_fixture_program.py::test_fixture_command_timeout_never_signals_child`
- `r1/tests/test_exam_namespace_fixture_program.py::test_fixture_event_retries_short_writes_and_fails_on_enospc`
- `r1/tests/test_exam_namespace_fixture_program.py::test_fixture_event_wrong_argv_or_pid_is_rejected`
- `r1/tests/test_exam_namespace_fixture_program.py::test_host_probe_bind_failure_stops_before_any_connection`
- `r1/tests/test_exam_namespace_fixture_program.py::test_inner_failure_waits_for_natural_child_exit_without_signal`
- `r1/tests/test_exam_namespace_fixture_program.py::test_made_up_or_missing_fixture_events_do_not_qualify`
- `r1/tests/test_exam_namespace_fixture_program.py::test_proc_start_ticks_parses_synthetic_stat`
- `r1/tests/test_exam_namespace_fixture_program.py::test_setns_namespace_fd_open_failure_is_not_denial`
- `r1/tests/test_exam_namespace_fixture_program.py::test_setns_stage_must_be_denied_not_command_failure`
- `r1/tests/test_exam_namespace_fixture_program.py::test_shared_host_mount_namespace_stops_before_mount`
- `r1/tests/test_exam_namespace_fixture_program.py::test_shared_propagation_stops_before_proc_mount`
- `r1/tests/test_exam_namespace_fixture_program.py::test_user_namespace_entry_success_cannot_be_counted_as_denial`
- `r1/tests/test_rerun2_batch4c.py::test_real_runner_desktop_dryrun`
- `r1/tests/test_trackx_lease_guardian.py::test_closed_stdout_and_unwritable_evidence_still_hold`
- `r1/tests/test_trackx_lease_guardian.py::test_hold_forever_survives_broken_stdout_without_evidence`

## 6. Deviations from the draft, and why

1. **Default rule path stays v1** (draft: point it at v2). Runbook M2 step 2: keeps Stage A (`exam_portal.json`, binds v1) unchanged.
2. **The rule comment on registry counts** says "20 candidates = 12 switchable with off_switch, 4 non-thinking, 4 always_on" (draft: "14 switchable, 5 non-thinking, 3 always_on"). The draft's counts do not match the registry at `74a0790` (12/4/4 among the 20 candidates; plus the 7B anchor, non-thinking, and the `olmo31_32b_think` sensitivity, always-on). Comment only; no semantic effect, but it is inside the sha.
3. **`eligibility.stage_a_pass` comment** notes that the pass set is a sha-bound config input (the ruling postdates the draft).
4. **`b2_summary` takes an optional rule** instead of always switching: called without a rule it is byte-for-byte the v1 behaviour, so existing callers/tests are unchanged.
5. **B1 sensitivity rows for switchable models are kept** (draft "open for the author": whether to keep the node). Kept as descriptive, as the v2 YAML says.
6. `always_on_in_b1` also accepts `run_descriptive` in the validator (the draft's alternative), but the frozen file says `skip`.

## 7. Open questions

- M5: the A1 / STOP 9 review documents are cited but not committed, and the v17 hash is inconsistent (`2d86425d…` vs `131dad8d…`).
- The `t7j10` table's exact shape and the form of the operator's O1 acceptance record (the code binds both by sha but assumes the Stage A table shape).
- B1 host (`TODO_AUTHOR_R1_HOSTS_04NOV`): `collect` is TASL-2-only and `APPROVED_EXAM_HOSTS` = TASL-2/TASL-7; R1-HOSTS-04NOV is open.
- B1/B2 stay STOP: the runner's B1/B2 entry points (`evidence`, `ExamRunner.start`, `collect`) still raise "reviewed harness pin and observer cache evidence not implemented". Lifting them is a separate, reviewed step after R1-EXAM-RULE-X5V2 and the authorization notes.

## 8. Draft row R1-EXAM-RULE-X5V2 (sha filled; the author commits it after review)

```
| R1-EXAM-RULE-X5V2 (date) | `r1/exam/rules/x5_rule_v2.yaml` sha256 `79d8c5cb315d999dcad869afe696dd36c2e0c50e55eb0d9c6a9352510168eb20` (from `proposals/X5_RULE_V2_DRAFT_20261104.md`; `always_on_in_b1: skip` per R1-EXAM-ALWAYS-ON-SKIP) is frozen for Track X B1/B2, with code `4f0fa69b` and review `reviews/MAC_M2_REVIEW_<date>.md`. The Stage A pass set it reads is the `t7h8` PASS ∪ the operator-accepted `t7j10` PASS (R1-TRACKX-HANDOVER-RULING), supplied to the B1/B2 configs as the sha-bound `stage_a_amendment_table` and `stage_a_amendment_acceptance`; anchors run as anchors; the D28 and thinking-off conditions of R1-MAIN-PROPOSER (a) apply unchanged. Repaired models are served with their SHA-pinned templates (R1-EXAM-A1-M1-REQUIREMENTS (1)). `x5_rule_v1.yaml` stays as Stage A's rule. |
```
