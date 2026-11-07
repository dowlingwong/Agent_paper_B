# Independent review: integrated B1 preservation and STOP (7 Nov 2026)

**Result: NOT ACCEPTED** for the combined production implementation at `d3066c1b`. This review covers the interaction of the pinned-harness proposal, editable and worker-artifact guards, node output preservation, audit propagation, and non-cgroup STOP. It does not require cgroups, a supervisor, freezer, receipt durability, hostile same-UID protection or GPU completion proof.

## Blocking finding: exited campaign can leave owned worker running

`r1/exam/runtime.py` `ExamRunner.run_job` calls `stop_tree` on failure only if `self.child.poll() is None`. An already exited root is therefore skipped, although its owned descendants can remain alive and have been reparented. An independent local test at `/private/tmp/b1_orphan_worker_review_20261107.py` launched an owned synthetic child from a synthetic campaign root and exited the root with code 7. The actual `run_job` reported STOP, called no `stop_tree`, and the owned child was still alive; the test then killed that test-owned child. **1 passed** as a reproducer, not as acceptance. This fails the author's instruction to stop B1-owned workers at STOP. Fix with the existing owned-process management semantics and review, without introducing a cgroup requirement; verify the real Linux host behavior separately.

## Integrated testing

Against harness `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`, the combined audit, guard, node, stop, and Stage A recovery test selection gave **67 passed, 3 failed, 1 skipped**. The three failures are `test_b1_entry_reports_original_before_state_save_failure` and both `test_b1_entry_with_broken_stderr_still_returns_failure` parameterizations in `test_b1_stop_error_reporting.py`: their `FakeRunner` lacks the `service` attribute now accessed by the integrated entry point. These failures require a reviewed fixture correction and rerun; they are not evidence that production STOP works.

The prior scoped audit guard tests verify the actual pinned worker's partial log write is exclusive and preserved; combined source routes B1 root workers through `B1IntegrityWorker`, wraps pinned editable writes inside the campaign, and passes audit preservation and invalid-result STOP flags. These observations do not supersede the blocking STOP finding. No model, GPU or remote execution was performed; host process census, actual worker determinism, GPU/lease checks, final exact-HEAD review, authorization and preflight remain outside this review.
