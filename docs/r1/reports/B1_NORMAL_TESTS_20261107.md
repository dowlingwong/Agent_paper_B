# B1 normal pytest evidence — 7 November 2026 (draft; independent review required)

AI-assisted (Codex). This is a Mac development test snapshot, not an acceptance, launch authorization, formal experiment, or target-host validation. No remote connection or live model server was used. Some tests run synthetic subprocesses and a real test-owned audit worker; its training failed at Python import. The synthetic Stage A/B1 recovery test deliberately kills its own parent and resumes within pytest-owned temporary files. No formal B1 run was started.

Paper B full-suite checkout `06ebe67f` (parent `674c79ce`); pinned B1 harness `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`; Python 3.11.11, pytest 9.0.3. The Mac full run used the project venv, disabled plugin autoload/cache provider, unique basetemp, B1 harness and `r1/tests`; loopback socket binding was allowed. It returned **43 failed, 1079 passed, 11 skipped, 10 subtests passed** in 879.17 s. Full log retained at `/private/tmp/paper-b-b1-test-evidence-20261107-1/full-suite.log`, SHA-256 `9f1bdd51c139d3a2686f1622a13bcbacbc7dc7252cf86706db2dc3e2adb1e16a`. Test artifacts are temporary local evidence and must be preserved for review.

Compared with the exact 39 IDs in `MAC_M2_FAILURE_CLASSIFICATION_20261105.md`, 26 remain in the failure set, 13 do not, and 17 are new. The 12 former fake-server failures were absent from the new failure set; their four test files separately passed 51 tests (log `fake-server.log`, SHA-256 `b82bb1665adf80eaa72ed56fdec7873c837f5e84107e9baa92443616423b93bc`). The former end-to-end exam dryrun is now a negative STOP test and does not establish recovery coverage. Separate synthetic Stage A→B1 kill/recovery: 3 passed (`stagea-recovery.log`, SHA-256 `da1f5b99ddb80e6716cb8ba54827de77bc41a332dfa941e7bdebd6d2126f40c7`); Stage A transport, process identity and cooperative lease were mocked. This is not production execution.

The Stage A harness negative-control test passed separately with pin `897d83c8efa364ec2fdd37288241cc42e01d7274` (`stagea-control.log`, SHA-256 `8b7616183803f388822c2547db1299afe734c447dbca03ec4e82e761fce73f31`). Seven new B1 test setup failures were repaired on the test-only branch `f505e502`, parent `63630428` (which restores B2 anchor coverage), parent `06ebe67f`; three affected test files passed 32 tests (`b1-test-r4.log`, SHA-256 `b71d1d1b3920b8f1d92fe015d8e59b6ba02d55687398f42b8978acd13d708a8d`). Tests mock only separately tested earlier gates to reach their intended synthetic assertions. These test changes need independent review and final integrated-HEAD verification; they do not change the result of the full suite above.

## All 43 observed failures

“Old” means the exact ID occurred in the prior 39; “new” means absent there. Categories describe observed failures and scope, not a waiver. Historical different-track tests are not automatically safe exceptions: shared-code relevance and underlying causes remain to be reviewed. No author exception decision is recorded here.

| Test ID | Prior | Observation and scope |
|---|---|---|
| `r1/tests/test_b1_stop_error_reporting.py::test_b1_entry_reports_original_before_state_save_failure` | New | B1: prior committed-config gate intercepts synthetic test; fixed on f505e502, targeted 32 pass; independent review and integrated-HEAD retest needed. |
| `r1/tests/test_b1_stop_error_reporting.py::test_b1_entry_with_broken_stderr_still_returns_failure[False]` | New | B1: prior committed-config gate intercepts synthetic test; fixed on f505e502, targeted 32 pass; independent review and integrated-HEAD retest needed. |
| `r1/tests/test_b1_stop_error_reporting.py::test_b1_entry_with_broken_stderr_still_returns_failure[True]` | New | B1: prior committed-config gate intercepts synthetic test; fixed on f505e502, targeted 32 pass; independent review and integrated-HEAD retest needed. |
| `r1/tests/test_c3_audit.py::test_real_worker_run_is_seed_deterministic` | Old | B1 shared audit: subprocess missing numpy; retained trial-001/run.log. Target host environment and behavior need verification. |
| `r1/tests/test_c3_control_dryrun.py::test_control_dryrun_end_to_end` | Old | Other track: unmarked temp-directory refusal; underlying test not exercised. |
| `r1/tests/test_c3_dataset.py::test_build_replays_without_violations_and_di_candidates` | New | Other track: replay fixture stale against harness source (C 0.01 versus expected 0.15); root cause not fully established. |
| `r1/tests/test_c3_featurizer_online.py::test_online_features_hash_equal_the_dataset_rows` | New | Other track: replay fixture stale against harness source (C 0.01 versus expected 0.15); root cause not fully established. |
| `r1/tests/test_c3_sweep_dryrun.py::test_c3_sweep_dryrun_retry_and_permanent_failure` | New | Other track: fake sweep incomplete; error/timeout, exact individual underlying causes not fully established; shared watchdog coverage not established. |
| `r1/tests/test_c3_sweep_dryrun.py::test_c3_sweep_dryrun_resumes_after_kill_mid_campaign` | Old | Other track: fake sweep incomplete; error/timeout, exact individual underlying causes not fully established; shared watchdog coverage not established. |
| `r1/tests/test_c3_sweep_dryrun.py::test_c3_sweep_dryrun_watchdog_restarts_a_killed_runner` | New | Other track: fake sweep incomplete; error/timeout, exact individual underlying causes not fully established; shared watchdog coverage not established. |
| `r1/tests/test_c3_sweep_dryrun.py::test_c3_sweep_dryrun_llamacpp_from_the_deepthought_config` | Old | Other track: fake sweep incomplete; error/timeout, exact individual underlying causes not fully established; shared watchdog coverage not established. |
| `r1/tests/test_c3_sweep_dryrun.py::test_c3_sweep_dryrun_llamacpp_resumes_after_kill_mid_campaign` | Old | Other track: fake sweep incomplete; error/timeout, exact individual underlying causes not fully established; shared watchdog coverage not established. |
| `r1/tests/test_c3_sweep_dryrun.py::test_c3_sweep_dryrun_llamacpp_watchdog_restarts_a_killed_server` | Old | Other track: fake sweep incomplete; error/timeout, exact individual underlying causes not fully established; shared watchdog coverage not established. |
| `r1/tests/test_c3_sweep_resume.py::test_orphaned_instance_is_stopped_only_when_it_is_provably_ours` | Old | Environment: Mac lacks Linux /proc process identity; Linux behavior not established. |
| `r1/tests/test_c3_sweep_resume.py::test_resume_refuses_while_an_earlier_runner_process_lives` | Old | Environment: Mac lacks Linux /proc process identity; Linux behavior not established. |
| `r1/tests/test_cooperative_lease.py::test_guardian_witness_validation_accepts_only_the_fixed_method` | Old | Environment: Mac guardian witness values invalid; Linux behavior not established. |
| `r1/tests/test_cooperative_lease.py::test_public_start_requires_authorized_d3_context_but_is_enabled` | New | Shared Stage A/B1 synthetic test: fake object lacks rule attribute after newer B1 check; old B1-stop expectation stale. Fixed in test-only b0738ca5; targeted test passed; independent review required. |
| `r1/tests/test_exam_b1_parent_binding.py::test_start_rejects_old_authority_before_resume_side_effects[False]` | New | B1: prior committed-config gate intercepts synthetic test; fixed on f505e502, targeted 32 pass; independent review and integrated-HEAD retest needed. |
| `r1/tests/test_exam_b1_parent_binding.py::test_start_rejects_old_authority_before_resume_side_effects[True]` | New | B1: prior committed-config gate intercepts synthetic test; fixed on f505e502, targeted 32 pass; independent review and integrated-HEAD retest needed. |
| `r1/tests/test_exam_cache_d3_guard.py::test_b1_cli_refuses_missing_active_note_before_runner` | New | B1: prior committed-config gate intercepts synthetic test; fixed on f505e502, targeted 32 pass; independent review and integrated-HEAD retest needed. |
| `r1/tests/test_exam_cache_d3_guard.py::test_b1_unauthorized_start_stops_before_output` | New | B1: prior committed-config gate intercepts synthetic test; fixed on f505e502, targeted 32 pass; independent review and integrated-HEAD retest needed. |
| `r1/tests/test_exam_namespace_fixture_program.py::test_shared_host_mount_namespace_stops_before_mount` | Old | Historical non-B1 fixture: missing D3_NAMESPACE_CPU_FIXTURE_DRAFT.py; fixture did not run. |
| `r1/tests/test_exam_namespace_fixture_program.py::test_exclusive_fixture_file_never_overwrites` | Old | Historical non-B1 fixture: missing D3_NAMESPACE_CPU_FIXTURE_DRAFT.py; fixture did not run. |
| `r1/tests/test_exam_namespace_fixture_program.py::test_explicit_flag_and_direct_tmp_path_are_required` | Old | Historical non-B1 fixture: missing D3_NAMESPACE_CPU_FIXTURE_DRAFT.py; fixture did not run. |
| `r1/tests/test_exam_namespace_fixture_program.py::test_proc_start_ticks_parses_synthetic_stat` | Old | Historical non-B1 fixture: missing D3_NAMESPACE_CPU_FIXTURE_DRAFT.py; fixture did not run. |
| `r1/tests/test_exam_namespace_fixture_program.py::test_shared_propagation_stops_before_proc_mount` | Old | Historical non-B1 fixture: missing D3_NAMESPACE_CPU_FIXTURE_DRAFT.py; fixture did not run. |
| `r1/tests/test_exam_namespace_fixture_program.py::test_fixture_command_timeout_never_signals_child` | Old | Historical non-B1 fixture: missing D3_NAMESPACE_CPU_FIXTURE_DRAFT.py; fixture did not run. |
| `r1/tests/test_exam_namespace_fixture_program.py::test_host_probe_bind_failure_stops_before_any_connection` | Old | Historical non-B1 fixture: missing D3_NAMESPACE_CPU_FIXTURE_DRAFT.py; fixture did not run. |
| `r1/tests/test_exam_namespace_fixture_program.py::test_inner_failure_waits_for_natural_child_exit_without_signal` | Old | Historical non-B1 fixture: missing D3_NAMESPACE_CPU_FIXTURE_DRAFT.py; fixture did not run. |
| `r1/tests/test_exam_namespace_fixture_program.py::test_setns_stage_must_be_denied_not_command_failure` | Old | Historical non-B1 fixture: missing D3_NAMESPACE_CPU_FIXTURE_DRAFT.py; fixture did not run. |
| `r1/tests/test_exam_namespace_fixture_program.py::test_user_namespace_entry_success_cannot_be_counted_as_denial` | Old | Historical non-B1 fixture: missing D3_NAMESPACE_CPU_FIXTURE_DRAFT.py; fixture did not run. |
| `r1/tests/test_exam_namespace_fixture_program.py::test_dependency_manifest_digest_and_complete_set_are_required` | Old | Historical non-B1 fixture: missing D3_NAMESPACE_CPU_FIXTURE_DRAFT.py; fixture did not run. |
| `r1/tests/test_exam_namespace_fixture_program.py::test_setns_namespace_fd_open_failure_is_not_denial` | Old | Historical non-B1 fixture: missing D3_NAMESPACE_CPU_FIXTURE_DRAFT.py; fixture did not run. |
| `r1/tests/test_exam_namespace_fixture_program.py::test_fixture_event_retries_short_writes_and_fails_on_enospc` | Old | Historical non-B1 fixture: missing D3_NAMESPACE_CPU_FIXTURE_DRAFT.py; fixture did not run. |
| `r1/tests/test_exam_namespace_fixture_program.py::test_final_event_verifier_rejects_truncation_and_out_of_order` | Old | Historical non-B1 fixture: missing D3_NAMESPACE_CPU_FIXTURE_DRAFT.py; fixture did not run. |
| `r1/tests/test_exam_namespace_fixture_program.py::test_made_up_or_missing_fixture_events_do_not_qualify` | Old | Historical non-B1 fixture: missing D3_NAMESPACE_CPU_FIXTURE_DRAFT.py; fixture did not run. |
| `r1/tests/test_exam_namespace_fixture_program.py::test_fixture_event_wrong_argv_or_pid_is_rejected` | Old | Historical non-B1 fixture: missing D3_NAMESPACE_CPU_FIXTURE_DRAFT.py; fixture did not run. |
| `r1/tests/test_exam_x5_rule_v2.py::test_stage_a_harness_pin_does_not_send_cache_prompt_so_b1_evidence_stops` | New | Environment/configuration: suite used B1 harness pin; same test separately passed with Stage A pin 897d83c. |
| `r1/tests/test_rerun2_batch4c.py::test_dryrun_refuses_escaped_batch_root` | New | Other track: marked-temp-directory gate intercepts intended dryrun safety assertion; coverage not established. |
| `r1/tests/test_rerun2_batch4c.py::test_dryrun_start_refuses_external_batch_before_log_write` | New | Other track: marked-temp-directory gate intercepts intended dryrun safety assertion; coverage not established. |
| `r1/tests/test_rerun2_batch4c.py::test_dryrun_refuses_all_effective_push_urls_without_network` | New | Other track: marked-temp-directory gate intercepts intended dryrun safety assertion; coverage not established. |
| `r1/tests/test_rerun2_batch4c.py::test_real_runner_desktop_dryrun` | Old | B1-related unresolved: nested dryrun fixture git commit exited 1; nested exam coverage not established. |
| `r1/tests/test_scripted_live_golden.py::test_live_campaign_sequences_match_the_pre_change_golden` | New | Other track: scripted sequence differs from golden (initial C and max_iter), with B1 pin; compatibility/root cause unresolved. |

## Prior failures no longer in current failure set

- `r1/tests/test_exam_dryrun.py::test_exam_fake_end_to_end`
- `r1/tests/test_llama_server_instance.py::test_start_records_argv_cmdline_pins_and_identity`
- `r1/tests/test_llama_server_instance.py::test_orphan_is_stopped_only_when_provably_ours`
- `r1/tests/test_llama_server_instance.py::test_a_matching_process_of_another_user_is_never_signalled`
- `r1/tests/test_llamacpp_offload_routes.py::test_fake_v070_log_has_no_offload_line_and_fake_nvidia_smi_lists_the_server`
- `r1/tests/test_llamacpp_offload_routes.py::test_runner_check_passes_by_either_route_and_records_it[silent-5560-gpu_memory]`
- `r1/tests/test_llamacpp_offload_routes.py::test_runner_check_stops_on_low_memory_partial_line_or_fallback[silent-4000-below the pinned footprint]`
- `r1/tests/test_llamacpp_offload_routes.py::test_probe_route_i`
- `r1/tests/test_llamacpp_offload_routes.py::test_probe_route_ii_with_cpu_control`
- `r1/tests/test_llamacpp_offload_routes.py::test_probe_route_ii_failures_exit_nonzero_with_telemetry[env0-extra0-speedup]`
- `r1/tests/test_llamacpp_offload_routes.py::test_probe_route_ii_failures_exit_nonzero_with_telemetry[env2-extra2-below]`
- `r1/tests/test_llamacpp_offload_routes.py::test_probe_route_ii_failures_exit_nonzero_with_telemetry[env3-extra3-below]`
- `r1/tests/test_llamacpp_probe.py::test_full_offload_probe_records_pins_footprint_and_stops_the_server`

Absence from the failure set is not proof of production correctness; see the negative-test limitation above. Host-side tests, final integrated HEAD, independent acceptance, and all author launch conditions remain separate.
