# B1 focused Mac tests at 60ecf1da — 7 November 2026

AI-assisted (Codex). **Evidence for independent review; not acceptance, an experiment launch, or a target-host result.** Isolated clean Paper checkout HEAD `60ecf1dae299ee424aa1bdfe078eab02a881b87e`; local harness checkout HEAD `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`; Mac Python 3.11.11 and pytest 9.0.3. No host, GPU or real model was used. Tests include synthetic owned processes and a real pinned worker on synthetic CPU input. Temporary evidence is retained under `/private/tmp/paper-b-b1-focused-60ec-evidence-20261107/`.

The first invocation used the project venv Python and PATH, `AR_HARNESS_ROOT` pinned above, `PYTHONPATH` pointing to the pinned harness src and this checkout, a new `TMPDIR` and `--basetemp`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `PYTHONDONTWRITEBYTECODE=1`, `-p no:cacheprovider`, and OMP/BLAS thread limits of 1. It ran these selections:

```
r1/tests/test_exam_b1_parent_binding.py
r1/tests/test_b1_stagea_process_stop.py
r1/tests/test_b1_stop_owned_process_integration.py
r1/tests/test_b1_stop_error_reporting.py
r1/tests/test_b1_audit_stop.py
r1/tests/test_b1_audit_worker_artifacts.py
r1/tests/test_b1_audit_synthetic_worker.py
r1/tests/test_b1_committed_config_unittest.py
r1/tests/test_exam_b1_committed_authority.py
r1/tests/test_b1_editable_preservation.py
r1/tests/test_b1_worker_artifact_guard.py
r1/tests/test_b1_node_artifacts.py
r1/tests/test_exam_stagea_b1_crash_recovery.py
r1/tests/test_c3_audit.py::test_real_worker_run_is_seed_deterministic
```

Result **101 passed, 1 skipped**, 12.01 s; exit 0; `pytest.log` SHA-256 `4099ba13886f372fd2bfc27d1e3914cd2577cfa4fcda3e8fb57f12d0f5322796`. The skipped Stage A/B1 crash-recovery case requires `AR_HARNESS_B1_ROOT`, which was not set in this invocation. A pass of the Mac worker test is not the required TASL-7 worker result.

To resolve that omission, a second invocation ran only `test_exam_stagea_b1_crash_recovery.py`, with the same environment plus `AR_HARNESS_B1_ROOT` at the same pinned checkout and `R1_REQUIRE_B1_HARNESS=1`, in a new pytest base. Result **1 failed, 2 passed**, 11.69 s; exit 1; `pytest-recovery.log` SHA-256 `42fd75de806c6e83f58f2b4f7fbf77fd88527e343c6ad5dc67601268e79a5d67`. The failing `test_stagea_to_b1_owned_parent_crash_and_recovery` reports that its synthetic parent exited before the intended crash; retained `SYNTHETIC_parent_first.log` contains only `PreparationStop: [Errno 1] Operation not permitted`. The precise failing operation and cause are **NOT CHECKABLE** from that output; do not assert a sandbox or network cause. No automatic retry was made after this failure. This checkout's synthetic Stage A/B1 parent-crash coverage is therefore not shown to pass by the follow-up; preserve the test scene for diagnosis. The other two tests passed, but their results do not replace the missing case.

The first run's 101 passes and the second run's failure are both retained, and no aggregate pass is claimed. The full suite, final combined HEAD and review, Linux owned-group checks, real host worker/lease/server/author gate, handover and all author launch conditions remain separate.
