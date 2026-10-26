# Local test-scope incident — 26–27 October 2026


**Author disposition, 27 October:** within scope after clarification. The author subsequently permitted existing CPU repository tests including synthetic/cached sklearn fits and node subprocesses. This disposition does not establish unknown subprocess outcomes or override the remaining exclusions (LLM inference, real-weight downloads, GPU/MPS, evidence or label runs, remote hosts). The historical review and observations below are retained.
AI-assisted operational record. The author allowed CPU unit tests on tiny random-weight or `hf-internal-testing` models, prohibited real Track P base weights, and asked for both repository suites. The earlier general instruction prohibited model training except the stated test exception. The operator and two Track G subagents did not fully identify all existing suite tests that fit node models before running them. No scientific outcome or evidence run is claimed from these tests.

## Confirmed synthetic-data fits

The operator ran the harness L0 baseline and then the L4.4 comparison in disposable harness clones. Both JUnit records show `tests/stage2/test_r1_l8.py::TestOpenmlPool22Oct::test_positive_class_and_inactive_imputer_on_synthetic_frames` passed. That test creates a synthetic frame, replaces the data loader, and calls the existing node benchmark twice for each of four node configurations (`tests/stage2/test_r1_l8.py` in harness `897d83c`). The benchmark invokes `pipeline.fit` (`nodes/openml_template/benchmark.py`). Thus CPU model fitting on synthetic data occurred in each of those suite runs; it was not an LLM or an actual OpenML download. The operator did not pre-identify this fitting before launching the suites.

The MLGym subagent independently reports the same synthetic-data fitting occurred in its broad suite; its [handoff](local_test_scope_20261027/mlgym-handoff.md) and [retained evidence](local_test_scope_20261027/mlgym-retained-evidence.tar.gz) record the commands and limits. These were node tests, not MLGym evidence.

## Other attempted node subprocesses

The L0 paper suite includes `r1/tests/test_c3_audit.py::test_real_worker_run_is_seed_deterministic`; it attempted real node worker calls and failed. The harness suite includes seed-injection, local-worker and resume tests that launch node subprocesses; several failed or errored. The saved [paper JUnit](local_baseline_20261026/paper-junit.xml.gz), [harness JUnit](local_baseline_20261026/harness-junit.xml.gz) and logs contain the available outcomes. The exact point reached by every subprocess is not established by the captured summaries; do not infer all failed before training.

The autoresearch subagent separately ran two existing tests that attempted `lr_synthetic` subprocesses. Both recorded exit 1; the agent's inference that NumPy was missing and fitting did not start is not proved by the retained test output. Its [handoff](local_test_scope_20261027/autoresearch-handoff.md) records commands, test IDs and the evidence gap. The MLGym subagent reports additional attempted subprocess node tests; six retained resume-test logs show failure at NumPy import, while the state of other subprocesses is unknown. See its handoff for IDs and retained evidence.

## Stop and consequences

After identifying this scope issue, the operator stopped the still-running L4.4 paper-suite repeat, using SIGTERM only on its own process group. Its [partial log](local_test_scope_20261027/l44-paper-interrupted.log.gz) ends in termination; it has no final JUnit result and must not be reported as a complete comparison. The completed L4.4 harness [JUnit](local_test_scope_20261027/l44-harness-junit.xml.gz) and [log](local_test_scope_20261027/l44-harness-tests.log.gz) are retained. No additional broad suite or node-training test has been launched since this discovery.

L0's independent review preceded discovery of this issue and must be rechecked with this record. L4.4 remains unaccepted: its focused hash-tool tests passed, but a complete no-new-failure comparison under a test selection demonstrably inside the author's model restrictions is not yet established. This record does not infer permission for any further model fitting, evidence run or remote operation.
