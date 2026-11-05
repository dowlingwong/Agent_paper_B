# Independent B1 synthetic parent-to-child review — 5 November 2026

**Verdict: NOT ACCEPTED pending the test-process lifecycle fix.** Independent review (AI-assisted, Codex) of `c20d3f1cc24c113eb41fc51f1c3db535300f5dc5` against `6416947`; binary diff SHA-256 `8a7dd01287db179b4f26803aa2ed0efab6662394538176cb4f0e03b5fd7ab47f`. This is synthetic coverage, not a real Stage A receipt, B1 author approval, TASL-7 lock qualification, or repair of the legacy kill/resume test. No remote host, real model, GPU, or scientific experiment was used.

## Finding

`r1/tests/test_exam_b1_v2_parent_e2e.py:42–44` invokes the parent with `subprocess.run(..., timeout=180)`. The runtime launches the fake server in a separate session (`r1/scripts/llama_server_instance.py:351–352`); `subprocess.run` terminates its direct parent on timeout but does not guarantee the independently sessioned fake server exits. Normal `ExamRunner.close` stops its own server, but abrupt timeout can bypass that cleanup and leave a fake process and socket behind. The test must ensure bounded cleanup/observation of its own unique fake processes on abnormal parent loss without signalling unrelated processes. Synthetic parent-death behavior and negative coverage should be checked independently; no existing process should be disturbed.

The required pinned-harness opt-in should also fail rather than skip if `R1_REQUIRE_B1_HARNESS=1` and the harness path is absent, matching the existing pinned-harness controls. Add an explicit assertion equating the retained observer journal digest with both the root manifest evidence hash and observer evidence digest; the current code validates it during generation, but the test itself asserts only that observer calls exist and cache flags are false.

## Checks

- Temporary root creation uses `exam_dryrun.prepare`, a `.dryrun` marker, fake GGUF bytes and a generated local stand-in binary. The amendment table is explicitly `ENGINEERING_ONLY`, while its file name and acceptance text mark the data synthetic; these records are not O1 evidence. The test selects only one anchor, one node and one instance, not the full B1 matrix.
- The fake server's new observer branch emits fixed typed fixture data when the prompt starts with the observer phrase. Ordinary prompts retain `common.proposal_for`; `EXAM_FAKE_MALFORMED` still takes precedence. This scope does not establish behavior for every possible fake-server caller.
- With `AR_HARNESS_B1_ROOT=/private/tmp/paper-b-m2-harness-a3fedbb` at exact `a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`, the independent loopback-only test passed: **1 passed in 5.27 s**. The retained synthetic root manifest showed two observer calls, four `llm_call` events, two trial records, `all_false: true`, and the journal SHA matched its manifest hash. The fake server record showed `stopped_utc` and return code `-15` on this normal path. An attempted OS process listing was unavailable in the sandbox, so that record is not an independent OS process census.
- The test actually exercises the real dryrun runner, subprocess campaign, pinned harness and observer journal, but uses a fixture worker and no real dataset or model. It does not exercise authorized real-mode committed-HEAD checks, actual Linux server/FD behavior, abnormal timeout cleanup, Stage A, or the old kill/resume coverage.

The parent should correct the process-lifetime and explicit-assertion gaps and request same-reviewer recheck against the exact new candidate. This review gives no execution authority.
