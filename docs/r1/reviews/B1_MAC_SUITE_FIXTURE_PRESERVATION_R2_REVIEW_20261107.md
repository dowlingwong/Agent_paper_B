# Independent review: second fixture-preservation unit, round 1

**Verdict: NOT ACCEPTED** for candidate `b1603f8e` (changes in `faf6a468` and `b1603f8e`). This review is static: no test, deletion, experiment, model, GPU or host access was performed.

## Finding

In `r1/tests/test_exam_cache_runtime.py`, `inheritance_fixture(..., server_fd='extra')` first creates the lease descriptor symlink under its real acquired FD number, then creates extra links at fixed FD numbers 99 and 98. The helper now asserts the target link is absent. `lease_fixture` acquires an ordinary process FD and provides no upper bound on its number. If the OS assigns FD 98 or 99, one of the supposed extra links collides with the lease link and the assertion fires before `verify_inheritance` exercises its FD-set rejection. The earlier helper replaced an existing link in this situation, so the added assertion introduces a new failure mode on hosts with many open FDs. Select distinct synthetic extra numbers that cannot equal `fd`, preserve the descriptor identity and both negative conditions, and verify the changed fixture without removing existing links.

## Scope checked

The count test constructs the same intended absent B root record and empty failure directory directly; its successful and interrupted-event assertions remain. The guardian wrong-descriptor case uses a separate synthetic proc root with the same PID, start ticks and wrong target, then retains the original tree for later tests. The server missing, extra and wrong cases retain the corresponding refusal strings in independently constructed roots. The helper change affects all call sites, so the higher-FD collision is a real compatibility concern rather than just a report issue.

The candidate report transcribes three passed test cases; the named base and TMPDIR and three fixture roots exist. No saved pytest result log was provided and this reviewer did not rerun them, so the reported result is not independently reproduced. The unit does not establish that pytest internals, process cleanup, transitive functions or the complete suite avoid deletion. In particular `test_trackx_lease_guardian.py`, harness and subprocess cleanup remain out of scope; no full-suite or B1 readiness is implied.

At the reviewed commit, report SHA-256 `055e41f0647b905d0d15dbecc7f6467eb4ff3505977b5bf37414c2bd83707f00`; test file SHA-256 `8f827000875fdebfd446674949d2e3bc65b6adef783c0b69cae2d9741dc34cfa` (cache runtime) and `5e3490f85a84759644e545b14b2d7660b8f05dfed23a63bca72506bdc51bd938` (sweep resume).
