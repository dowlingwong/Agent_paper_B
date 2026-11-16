# Independent review — revised legacy exam test, 5 November 2026

**Verdict: ACCEPTED for the narrowly described STOP-boundary tests at `9ddf0e87bc84053d871c0d5cfa7fceb9c52ff993`.** Reviewed the test-only diff from `ee0d8a1`. This is not acceptance of the old combined end-to-end run, B1 readiness, an exception, or an execution authorization. No real model, server, GPU, remote host, or scientific experiment was run.

## Evidence and scope

The historical `test_exam_fake_end_to_end` no longer claims the old two-candidate/three-anchor Stage A-to-B1 kill-and-resume success. Its revised assertions (`r1/tests/test_exam_dryrun.py:15-24`) check that the actual legacy driver exits at the missing D3 lease FD, records the expected STOP, creates no Stage A output or success summary, and makes no fake-server calls. This follows the actual CLI check (`r1/scripts/exam_runner.py:494-497`) and is a meaningful negative boundary test. The driver still contains the former interruption and resume flow (`r1/scripts/exam_dryrun.py:73-87`), which the STOP prevents reaching.

The additional B1 test (`r1/tests/test_exam_b1_parent_binding.py:130-138`) creates a synthetic STOPPED batch, exercises `ExamRunner.start`, and checks the state bytes remain unchanged and no runner lock is created. `runtime.py:79-84,410-413` rejects that state before recovery. The test mocks the separate author gate; it establishes neither author approval nor actual process interruption.

The separately reviewed synthetic parent/child path (`MAC_B1_PARENT_E2E_REVIEW_20261105.md`, R3) covers a fake receipt and pinned harness, but does not reproduce Stage A or the historical kill/resume behavior. **The original failure ID now passes under revised STOP-only semantics; the historical Stage A-to-B1 successful kill/resume scenario remains untested and must not be reported as fixed or passed.** The name `test_exam_fake_end_to_end` is retained for failure-set traceability even though its present assertion tests refusal, so every summary of this ID should state the changed semantics. A clearer test name and explicit old-to-new mapping would also be acceptable.

Independent Mac CPU command, `AR_HARNESS_ROOT=/Users/wongdowling/Documents/autoresearch_harness PYTHONDONTWRITEBYTECODE=1 /Users/wongdowling/Documents/autoresearch_harness/.venv/bin/python -m pytest -q r1/tests/test_exam_dryrun.py r1/tests/test_exam_b1_parent_binding.py`, returned **13 passed in 2.44 s**. The first test exercised only marked temporary fixtures and stopped before a server or worker. The test inherits ambient environment (`test_exam_dryrun.py:16`); explicitly clearing `TRACKX_GPU_LEASE_FD` would make the intended missing-lease precondition deterministic. This is a test-portability recommendation, not evidence of host safety or a waiver of any production guard.

## Same-reviewer recheck — deterministic missing-lease precondition

**ACCEPTED for this one-line test hardening only** at `79d70cc0e2e1d49193355e97af6e3189cd846a0b`: `r1/tests/test_exam_dryrun.py` removes `TRACKX_GPU_LEASE_FD` from the synthetic subprocess environment. The prior STOP-only assertions are unchanged. Independent Mac CPU test with an explicitly set ambient `TRACKX_GPU_LEASE_FD=987` returned **13 passed in 2.60 s** across `test_exam_dryrun.py` and `test_exam_b1_parent_binding.py`. No real model, server, GPU, remote host, or experiment ran.

This recheck does not review or accept the other changes in the same commit. The historical original ID now passes only under revised STOP semantics; the old Stage A-to-B1 kill/resume success remains untested, and author, host, and B1 readiness gates remain open.
