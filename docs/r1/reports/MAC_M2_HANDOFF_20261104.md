# M2 hand-off — `x5_rule_v2` and its code (4 Nov 2026)

## Mac continuation, 4 November — NOT ACCEPTED

**20:38 follow-up (AI-assisted, Codex).** The author selected the retained thinking-on descriptive sensitivity and thinking-off-only D28 gate in PLAN R1-EXAM-X5-B1-SENSITIVITY and R1-EXAM-X5-D28-SCOPE (`mac-int-20261104` @ `8c7677a`). The B1 scope review then found that `author_gate` could accept a prose or dirty PLAN mention as a rule decision; code `0437cea` therefore refuses all X5 v2 authorizations until an independently reviewed, trusted published authority is bound. The disabled containment was independently reviewed (`reviews/MAC_B1_SCOPE_REVIEW_20261104.md`); legacy v1 compatibility is not fully established. An authenticated-authority design is a conditional proposal at `320ef6f`, not an implementation or author decision. B1/B2 entry STOPs and the B2 ranking STOP remain.

Full Mac CPU suite on base `bf8b2da` plus the reviewed `0437cea` patch (binary diff SHA-256 `92083f7f4bfe720def1dd6120e84a0a56aeec2f425c632e79123cbf9496cbf90`): **896 passed / 39 failed / 11 skipped**. Its 39 failed test IDs equal those of `5fcea74`; no tests were added to or removed from the failure set. The forced harness configuration and interpreter were the same as the earlier final suite below. Log `reports/mac_m2_tests_20261104/authority_0437cea.log` has SHA-256 `f379057178992d94633e016656598b64809060740b184bf19f85096e6877b218`. The local test operator reports one identified orphan mock server was stopped and exited. This is not an all-passing suite or acceptance of M2.

AI-assisted (Codex). This continuation supersedes the unfinished round-2 test placeholder below. Full CPU suites ran on the Mac with the same harness checkout and compulsory B1 harness checks; no model, GPU or remote host was used. The draft rule file still hashes to `79d8c5cb315d999dcad869afe696dd36c2e0c50e55eb0d9c6a9352510168eb20`; this is not an author freeze.

| Tested code | Passed | Failed | Skipped |
|---|---:|---:|---:|
| Baseline `74a07907` | 821 | 39 | 11 |
| Original M2 `75134796` | 890 | 39 | 11 |
| M2 plus containment and M5 `5fcea745d2d31716a1e016153008465a2cb83442` | 894 | 39 | 11 |

All three have the same 39 failed test IDs; this is an unchanged failure set in this Mac environment, not a passing suite. Full logs and their SHA-256 values are in `reports/mac_m2_tests_20261104/`; final run includes the required a3fedbb positive and 897d83c negative harness checks. The test operator identified and terminated only the local mock servers orphaned by these test suites. Independent review of this handoff is required.

The final suite used Darwin, Python 3.11.11 and pytest 9.0.3, with `AR_HARNESS_ROOT=/Users/wongdowling/Documents/autoresearch_harness`, `AR_HARNESS_B1_ROOT=/private/tmp/paper-b-m2-harness-a3fedbb`, `R1_REQUIRE_B1_HARNESS=1` and `PYTHONDONTWRITEBYTECODE=1`; command: `/Users/wongdowling/Documents/autoresearch_harness/.venv/bin/python -m pytest -q -p no:cacheprovider r1/tests`. The baseline used the same interpreter, root and pytest options; its code has no v2 controls, so the two v2-specific variables were not set. Positive and negative controls were additionally rerun verbosely on `5fcea74`: both PASSED, as `combined_harness_controls.log` records. They use local stand-in servers, not actual inference. The pinned positive checkout was `a3fedbb`, the negative control `897d83c`.

M5 code `d5f7b75` was applied as byte-identical cherry-pick `5fcea74`; the earlier independent review accepts that fix and the M2 reviewer checked the integration. The M2 review discovered duplicate B2 primary candidates and missing complete unique node/instance coverage validation. Commit `1cd2dcc` refuses duplicates and unconditionally STOPs v2 B2 ranking pending an author-bound power-plan grid implementation and independent review; the reviewer accepts only this fail-closed containment. Restore real thinking-on exclusion and GPU-hour tie tests before enabling ranking. M2 remains **NOT ACCEPTED** and B1/B2 code entry STOPs remain.

`workers` controls a process pool for paired audit configurations after collection, not parallel campaigns; the roots and seeds are sequential and worker thread limits are set. The author selected the proposed 20 workers and 80 call cap, but practical resource headroom remains unmeasured. The author-selected digits node variant is recorded in PLAN. Review and the separately committed rule row and authorization remain necessary; TASL-7 paths must be confirmed by the operator.


## Historical worker handoff — superseded where it conflicts with the continuation above

Sections 1–10 below are preserved as historical context. In particular, the candidate code pin `0e5ce25f`, pending Mac tests, pending M5 review and proposed worker choice are stale; use the continuation and current PLAN. The draft row in §8 has not been adopted.

**Written by a worker subagent of the Mac-local agent (Claude), MAC_LOCAL_RUNBOOK_20261104 rev 3.3, task M2; AI-assisted. This is input to an independent review, not accepted work. Nothing here is a decision.**

- Branch `mac-x5v2-20261104`, base `74a07907` (head of `codex/trackx-stagea-cooperative-20261031`; config binding `74a0790`, code `ab74203`), per the author's 15:44 ruling (packet §0, R1-TRACKX-HANDOVER-RULING).
- M2 code commits: `4f0fa69bf71e3f493b79dee5b627426b447083ca` (round 1), `99a9f566781b8fe9e3c072a834aa355c1ab2a9ba` (round 2: fixes for `reviews/MAC_M2_REVIEW_20261104.md`, §9) and **`0e5ce25f48b97b854faa1678399059cb6529d66e`** (B1/B2 host = TASL-7, §10). **The code to review and to name in R1-EXAM-RULE-X5V2 is `0e5ce25f`.** This hand-off is a separate documentation-only commit.
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
| `r1/scripts/configs/exam_b1_v2.json`, `exam_b2_v2.json` | New. Copies of `exam_portal.json` with: `rule` = v2 path, `rule_sha256` = v2 sha, `harness_commit` = `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`, `cache_prompt: false`, `template_repairs` (the three repair shas), the Stage A inputs filled from the accepted O1 report (round 2, §9); `host`, `gpu_uuid`, `paper_commit`, `authorizations` as `TODO_*`; `d3_policy` dropped (Stage A-only). |
| `r1/scripts/configs/exam_portal.json` | **Unchanged** (still binds v1). |
| `r1/tests/test_exam_x5_rule_v2.py`, `r1/tests/exam_cache_prompt_driver.py` | New tests (40) and the stand-in-server driver. |

### The Stage A pass set (R1-TRACKX-HANDOVER-RULING, packet (d); round-2 status in §9)

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
5. ~~B1 sensitivity rows kept as a decided deviation~~ — round 2: this is **not** decided; it is the draft's open author question and is now listed in §7.
6. ~~`always_on_in_b1` also accepts `run_descriptive`~~ — round 2: the validator accepts only `skip` (review F4); the frozen YAML is unchanged.
7. The draft text's registry counts (14/5/3) are now stale; the frozen rule's comment carries 12/4/4 (review F4.2). The author should know the draft is out of date on this point.

## 7. Open questions

- **For the author, before R1-EXAM-RULE-X5V2 (review F3): keep the descriptive thinking-on sensitivity node?** The frozen v2 file keeps it (`thinking_mode.b1_sensitivity`, node `openml_credit_approval`, budget 2048), as in the draft YAML. It is descriptive only and never changes the B2 mode, but costs one node × 4 instances per switchable B1 model (about 12 models). Dropping it means a new rule file and a new sha.
- **For the author to confirm (review F2): the v2 D28 gate reads thinking-off roots only.** Under v2, `d28_pass` (a v2 eligibility condition) is computed over the primary thinking-off roots; the thinking-on sensitivity roots' D28 is recorded separately as `thinking_on_d28` (descriptive). This follows the rule's "descriptive only" wording and R1-MAIN-PROPOSER (a)'s selection on thinking-off performance; v1 keeps its all-roots D28. If the author wants the thinking-on D28 to gate eligibility, it is a one-line change.
- M5: the A1 / STOP 9 review documents are cited but not committed, and the v17 hash is inconsistent (`2d86425d…` vs `131dad8d…`).
- `OPS_O1_20261104.md` is bound by its bytes at `ops-20261104` @ `f52db28e` (sha `0cda82fa…`). The O1 reviewer asked for its stale opening/closing lines to be corrected; if the operator edits the report, the sha in the v2 configs must be updated. The report must also be present in the B1 code checkout (it lives on the ops branch now). The O1 report itself says the "separate author acceptance row" remained to be committed; the coordinator reports the author accepted Stage A (t7h8 + t7j10) at 17:54 — the PLAN row recording it is the author's.
- The t7h8 and t7j10 table *paths* in the v2 configs are derived (run directory + `stage_a_table.json`, as `_stage_a_cooperative` writes it); only their shas are recorded in O1. The operator should confirm the paths on TASL-7.
- `olmo31_32b_think` (role `sensitivity`, always-on) is skipped in B1 under v2, together with the four always-on candidates (`muse_glimmer_30b`, `lfm25_24b_a2b`, `gpt_oss_20b`, `rico03_qwen36_27b`); it failed Stage A on grammar in t7h8 anyway. The appendix (R1-EXAM-A1-M1-REQUIREMENTS (3), M8) reports it from Stage A like the others (review F10).
- The Mac run of the suite (runbook "Done when") is the integrator's: set `AR_HARNESS_B1_ROOT` to an `a3fedbb` checkout and `R1_REQUIRE_B1_HARNESS=1`, so that both harness tests must pass rather than skip (review F5).
- `collect` is still behind its STOP, so the harness test proves the value `cache_prompt_evidence` would write into `campaign_manifest.json`, not a written manifest. When `collect` is unblocked, add a DRYRUN test that runs `collect` and reads `campaign_manifest.json['cache_prompt']` (review F6).
- ~~B1 host open~~ — decided by the author at 18:10 (R1-EXAM-HOST-B1B2-TASL7): TASL-7; see §10.
- `workers` for TASL-7 (24 logical CPUs) is still `4` (copied from `exam_portal.json`); the integrator proposes the count in the B1 authorization draft (§10 explains how it is used).
- B1/B2 stay STOP: the runner's B1/B2 entry points (`evidence`, `ExamRunner.start`, `collect`) still raise "reviewed harness pin and observer cache evidence not implemented". Lifting them is a separate, reviewed step after R1-EXAM-RULE-X5V2 and the authorization notes.

## 8. Draft row R1-EXAM-RULE-X5V2 (sha filled; the author commits it after review)

```
| R1-EXAM-RULE-X5V2 (date) | `r1/exam/rules/x5_rule_v2.yaml` sha256 `79d8c5cb315d999dcad869afe696dd36c2e0c50e55eb0d9c6a9352510168eb20` (from `proposals/X5_RULE_V2_DRAFT_20261104.md`; `always_on_in_b1: skip` per R1-EXAM-ALWAYS-ON-SKIP) is frozen for Track X B1/B2, with code `0e5ce25f` and review `reviews/MAC_M2_REVIEW_20261104.md`. The Stage A pass set it reads is the `t7h8` PASS (table `00ab143d…`) ∪ the operator-accepted `t7j10` PASS (table `71525124…`, acceptance `reports/OPS_O1_20261104.md` `0cda82fa…`) (R1-TRACKX-HANDOVER-RULING), supplied to the B1/B2 configs as sha-bound inputs — 8 + 7 candidates and the 3 anchors; the D28 gate reads thinking-off runs only; anchors run as anchors; the D28 and thinking-off conditions of R1-MAIN-PROPOSER (a) apply unchanged. Repaired models are served with their SHA-pinned templates (R1-EXAM-A1-M1-REQUIREMENTS (1)). `x5_rule_v1.yaml` stays as Stage A's rule. |
```

## 9. Review round 2 (fixes for `reviews/MAC_M2_REVIEW_20261104.md`, commit `99a9f566`)

| Finding | Fix | Test(s) |
|---|---|---|
| F1 MAJOR — B2 analysis could rank v2 manifests under v1 | `analyze.b2_summary`: with a rule, every manifest's `rule_sha256` must equal the loaded rule's; without a rule, a manifest stamped `rule_version: x5_rule/v2` or carrying the v2 sha is refused (`_v2_sha`). The CLI default `--rule` (v1) therefore refuses v2 manifests. | `test_v2_b2_manifests_refused_without_the_v2_rule` (no rule, either stamp alone, explicit v1, CLI default, CLI with v2 → the mode refusal), `test_b2_with_rule_checks_every_manifest_sha`, `test_b2_without_rule_or_under_v1_is_unchanged` |
| F2 MAJOR — descriptive thinking-on runs fed `d28_pass` | `exam_runner._evidence_unreviewed`: under v2, `d28_pass` reads the primary (thinking-off) roots only; manifests carry `d28_scope: thinking_off_roots_only` and `thinking_on_d28 {pass, roots, role: descriptive_never_changes_eligibility}`; v1 unchanged. Listed in §7 for the author to confirm. | `test_runner_v2_d28_gate_reads_thinking_off_roots_only` (failing on-root does not exclude; failing off-root does; v1 still all-roots) |
| F3 — sensitivity node presented as decided | Moved to §7 as an author question. | — |
| F4 — `run_descriptive` accepted, untested | `_validate_v2` accepts only `skip`. Frozen YAML and sha `79d8c5cb…` unchanged. | `test_v2_validator_refuses_run_descriptive` |
| F5 — harness tests skip silently | `R1_REQUIRE_B1_HARNESS=1` turns both skips into failures; §7 tells the integrator how to run it on the Mac. | both harness tests (run here with the variable set: passed) |
| F6 — manifest proof / env override | Noted in §7. Added `exam_runner.refuse_cache_prompt_override` as a B1/B2 pre-flight: `LLAMACPP_CACHE_PROMPT` other than empty/0/false/no/off is a STOP before any server starts. | `test_runner_v2_refuses_cache_prompt_env_override` (7 values) |
| F7 — B2 finalist without a B1 row | STOP `x5_rule/v2 B2 finalist has no B1 analysis row` (except the free-sensitivity run). | `test_runner_v2_b2_refuses_finalist_without_b1_row` |
| F8 — untested / loose paths | Malformed amendment rows (missing or non-string `candidate`, non-bool `passed`, non-dict) → `PreparationStop`; non-JSON table → STOP; the acceptance record must name both the amendment-table and the Stage A-table sha; digest-mismatch STOP parametrized over all three repaired models; `_served_args` docstring says the phase parameter is nominal. | `test_v2_pass_set_malformed_amendment_rows_stop` (5 shapes), `test_v2_pass_set_acceptance_must_name_both_table_shas`, `test_author_gate_binds_amendment_shas` (1 positive, 3 negative), `test_b1_b2_repair_digest_mismatch_is_a_stop` (3 models × 2 phases) |
| F9 — TASL-7 `gpu_uuid` | In `99a9f566` both v2 configs got `gpu_uuid: TODO_AUTHOR_R1_HOSTS_04NOV_GPU_UUID`. **Superseded in `0e5ce25f`** by the author's host ruling: `host: TASL-7` with TASL-7's `gpu_uuid` (§10). | `test_v2_configs_bind_the_o1_accepted_tables` |
| F10 — `olmo31_32b_think` skipped | Noted in §7. | (existing skip test) |

**New facts used (author, 17:54, via the coordinator; ops branch `ops-20261104` @ `f52db28e`, read-only):** the author accepted Stage A — t7h8 (`r1_stagea_20261103_t7h8`) and M1 (`r1_stagea_20261104_t7j10`); the operator's `reports/OPS_O1_20261104.md` and `reviews/OPS_O1_REVIEW_20261104.md` (same reviewer, ACCEPTED on re-check after the author's N/A ruling on the software anchors). B1 candidates = t7h8's 8 PASS + t7j10's 7 PASS + 3 anchors.

**Shape check against the real records.** The t7j10 table is the Stage A table that `_stage_a_cooperative` writes (`{'label': 'ENGINEERING_ONLY', 'rows': [...]}` with `candidate`, `passed`, `software_anchor`, …), confirmed by the operator's `OPS_O1_AUDIT_20261104.py`, which reads `rows`, `candidate`, `passed`, `software_anchor`. It has 10 rows: the 3 anchors and the 7 amendment candidates, all PASS. The loader's rule — candidates enter from the amendment table only if they are registry `candidate` rows not already passing in t7h8; anchors keep their t7h8 rows — gives exactly 8 + 7 candidates + 3 anchors (`test_real_t7j10_shape_and_o1_acceptance_fit_the_loader`, a fixture with the real ids and PASS/FAIL pattern). The acceptance record is the O1 report (Markdown), bound by its sha; it names both table shas in full, which the loader now checks.

**Config values filled (both v2 configs):** `stage_a_table_sha256` `00ab143dc0742b24034e653bfa15acff5183538f85a1179cdbc7802cac22975c` (t7h8), `stage_a_amendment_table_sha256` `71525124fcf973ef7465fee9b0ff99c27b3f21b68f3a0ca55fcb9f7357992103` (t7j10), both from O1; `stage_a_amendment_acceptance` = `docs/r1/reports/OPS_O1_20261104.md`, sha `0cda82fa83eaa3546f272f7e6f834b052acc31dec28485e2b4447f6364a2053e` (the blob at `f52db28e`, computed here). Paths: `/home/dowling/exam-x/work/r1_stagea_20261103_t7h8/stage_a_table.json` and `…/r1_stagea_20261104_t7j10/stage_a_table.json` (derived; see §7).

**Tests (round 2):** see the Mac continuation at the top, including the tested commits, full-suite results and limitations.

## 10. B1/B2 host = TASL-7 (R1-EXAM-HOST-B1B2-TASL7, author 4 Nov 18:10; commit `0e5ce25f`)

Author: "我授权 Track X B1 和 B2 在 TASL-7 上运行（修改 R1-EXAM-HOST-TASL7 的"B1/B2 campaign worker 只在 TASL-2"），整场考试在同一台主机上。TASL-7 上 Track X 证据阶段优先于 Track P：B1/B2 运行期间 P.3a 暂停，只在 B1 与 B2 之间或 B2 之后运行。" (Row on `mac-int-20261104` @ `a52aa7b1`.)

**Host pins found on the B1/B2 path and what changed:**

| Place | Before | After |
|---|---|---|
| `r1/exam/campaign.py` `collect` | `platform.node() != 'TASL-2'` → STOP "EXAM workers run only on portal" | `require_worker_host(job)`: the job's `host` must be in `runtime.APPROVED_EXAM_HOSTS` (`{TASL-2, TASL-7}`) and equal the short node name; DRYRUN jobs skip it as before (they check their marked root). |
| `r1/exam/runtime.py` `ExamRunner.root` | job had no host | job carries `'host': cfg['host']`. |
| `runtime.host_check` (runner side) | already `node in APPROVED_EXAM_HOSTS and cfg.host == node` | unchanged. |
| `exam_b1_v2.json`, `exam_b2_v2.json` | `host` TODO, `gpu_uuid` TODO (review F9) | `host: TASL-7`, `gpu_uuid: GPU-ab72fb4a-f3de-6e37-f03b-4b92654babb1` (TASL-7's, as in `exam_portal.json`). |
| `exam_portal.json` (Stage A) | TASL-7 | unchanged. |

Left unchanged: `r1/exam/download_models.py` and `r1/exam/hub_download.py` (portal-only model-download helpers with their own TASL-2 checks; not called on the B1/B2 path); `exam_dryrun.py`'s "development host only" guard and `host_check`'s DRYRUN guard (they refuse DRYRUN on TASL-2/ucrtasl; unrelated to where evidence runs); the comments in `cache_runtime.py` / `cooperative_lease.py` that mention TASL-2 (no host check). The Track P pause during B1/B2 is an operator procedure, not code.

**Tests:** `test_b1_b2_worker_host_follows_cfg_host` (TASL-7 on TASL-7 allowed, FQDN accepted, TASL-2 allowed only when configured; node ≠ cfg.host refused; `deepthought`, a `TODO_` value or None refused as unapproved), `test_worker_host_uses_platform_node` (faked `platform.node()`), `test_collect_no_longer_hardcodes_tasl2_and_root_job_carries_host`, `test_stage_a_host_rules_unchanged` (Stage A `host_check` still refuses a node ≠ cfg.host and the Mac), and `test_v2_configs_bind_the_o1_accepted_tables` (host and gpu_uuid).

**How `workers` is used (for the B1 authorization's TASL-7 count; value left at 4):**
- `workers` is passed into each campaign-root job (`ExamRunner.root`). In `collect`, after the campaign, the B1/B2 paired audits run in a `ProcessPoolExecutor(max_workers=job['workers'])`: one **process** per concurrent configuration audit (`r1.c3.audit.run_config`). Each process runs its seeds sequentially, each seed as one `python3 train.py` subprocess (the harness `LocalWorker`). So there are at most `workers` training processes at once per root. Roots run one at a time per runner, and B1/B2 use one GPU server at a time.
- BLAS/OMP threading **is limited**. `ExamRunner.run_job` starts the root worker with `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1` and `MKL_NUM_THREADS=1`. The pool processes inherit that environment, and so do the training subprocesses, because `seed_environment` copies `os.environ`. Each audit is therefore single-threaded BLAS. NumPy and sklearn may still start a few idle helper threads.
- The campaign's own in-loop trial (W = 20 per root) runs serially in the root worker, also with single-threaded BLAS. While the audit pool runs, there is no campaign trial in flight.
- The CPU load per root is therefore about `workers` busy cores during audits, plus the runner, the root worker and the llama-server's host threads. llama-server is mostly GPU, but `-t` defaults to physical cores for the tokenizer/sampler.
- Note (not decided here): on 24 logical CPUs (likely 12 physical with SMT), leaving headroom for llama-server and the runner suggests at most about 12–16. The author's comparability concerns may favour keeping the number of concurrent audits fixed across B1 and B2.
