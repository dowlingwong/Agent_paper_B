# Harness baseline failing and error IDs

AI-assisted. Exact pytest summary IDs; consult `harness-junit.xml.gz` for diagnostics.

- `ERROR tests/test_legacy_noop_skip.py`
- `ERROR tests/stage2/test_r1_l7_commit_fix.py::TestResumedCommitSemantics::test_continue_commits_like_the_live_loop`
- `ERROR tests/stage2/test_r1_l7_commit_fix.py::TestResumedCommitSemantics::test_verify_records_evidence_and_charges_runs`
- `FAILED tests/stage2/test_exam_proposal_schema.py::test_schema_request_is_structure_only_rationale_first_and_records_usage`
- `FAILED tests/stage2/test_exam_proposal_schema.py::test_malformed_schema_reply_is_recorded_never_heuristic_replaced`
- `FAILED tests/stage2/test_exam_proposal_schema.py::test_free_generation_keeps_request_and_historical_fallback`
- `FAILED tests/stage2/test_exam_proposal_schema.py::test_schema_does_not_validate_or_enumerate_parameter_values`
- `FAILED tests/stage2/test_exam_proposal_schema.py::test_empty_but_structural_strings_are_not_replaced_by_heuristics`
- `FAILED tests/stage2/test_r1_defects.py::TestSeedInjection::test_same_seed_reproduces_and_different_seed_changes`
- `FAILED tests/stage2/test_r1_l5.py::TestDefaultControllerRegression::test_dry_and_local_default_records_match_fixture`
- `FAILED tests/stage2/test_r1_l7.py::TestRestoreAudit::test_replay_reproduces_metric_bit_for_bit`
- `FAILED tests/stage2/test_r1_l7_commit_fix.py::TestResumedE1AndMask::test_forced_verify_without_budget_falls_back_to_continue`
- `FAILED tests/stage2/test_r1_l8.py::TestMLAgentBenchSeed::test_seed_env_reaches_node`
- `FAILED tests/stage2/test_r1_l8b.py::TestNoisyNodes::test_same_seeds_reproduce_and_each_seed_moves_the_metric`
- `FAILED tests/stage2/test_r1_l8b.py::TestNoisyNodes::test_worker_edit_changes_config`
- `FAILED tests/stage2/test_r1_llamacpp_provider.py::TestLlamaCppManagerRequests::test_connection_refused_is_a_transport_error`
- `FAILED tests/stage2/test_r1_llamacpp_provider.py::TestLlamaCppManagerRequests::test_dropped_request_is_retried_once_with_the_same_seed`
- `FAILED tests/stage2/test_r1_llamacpp_provider.py::TestLlamaCppManagerRequests::test_seed_reaches_the_request_and_the_llm_call_record`
- `FAILED tests/stage2/test_r1_llamacpp_provider.py::TestLlamaCppManagerRequests::test_server_5xx_is_a_transport_error`
- `FAILED tests/stage2/test_r1_transport_retry.py::TestRealChatOllamaAgainstDroppingServer::test_server_drop_is_retried_with_the_same_seed`
- `FAILED tests/stage2/test_stage2_control_plane.py::TestClawWorkerExtraction::test_claw_worker_deterministic_constant_patch_runs_without_llm`
- `FAILED tests/test_artifact_completeness_and_manifest.py::TestCompletenessCLI::test_checked_in_report_contains_all_plan_campaigns`
- `FAILED tests/test_artifact_completeness_and_manifest.py::TestCompletenessCLI::test_cli_passes_on_real_campaigns`
- `FAILED tests/test_artifact_completeness_and_manifest.py::TestBuildManifest::test_all_referenced_files_exist`
- `FAILED tests/test_artifact_completeness_and_manifest.py::TestGenerateManifestCLI::test_cli_reports_all_files_exist`
- `FAILED tests/test_kdd_paper_sections.py::test_chunk_4_1_related_work_acceptance`
- `FAILED tests/test_kdd_paper_sections.py::test_chunk_4_2_system_design_acceptance`
- `FAILED tests/test_kdd_paper_sections.py::test_chunk_4_3_experiments_acceptance`
- `FAILED tests/test_kdd_paper_sections.py::test_chunk_4_4_results_order_and_artifact_links`
- `FAILED tests/test_kdd_paper_sections.py::test_chunk_4_5_discussion_acceptance`
