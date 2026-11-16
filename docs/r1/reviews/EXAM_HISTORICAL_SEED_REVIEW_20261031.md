# Track X historical seed: final independent review

Date: 2026-10-31

**Verdict: ACCEPT for the scoped historical-seed and source-binding implementation.** This is an engineering review only; it does not establish prompt freeze, authorize Stage A or any model execution, or demonstrate scientific readiness.

## Identity and published branch

- Local checkout: `/private/tmp/paper-b-exam-seed-20261031`, HEAD `1be426fd653e4dcf2f601a678a4b36a83cd228e7`.
- Live read-only `git ls-remote origin refs/heads/codex/trackx-seed-20261031` returned `1be426fd653e4dcf2f601a678a4b36a83cd228e7` for the branch; this also matched the local remote-tracking ref.
- `git diff --binary 4d1c59b HEAD | shasum -a 256` produced `0c9a1e9fc35fecbb94468872bc98880b81fa670a2ef59a0f299284fe1cd3ac0e`, matching the post-review diff recorded in `/Users/wongdowling/Documents/agent_paper_B_ops/TRACKX_SEED_INDEPENDENT_REVIEW_20261031.md`. The published follow-up commit therefore contains that independently reviewed diff on the reviewed base.
- The examined loader binds prompt and source-ledger hashes, constrains resolved ledger paths to the prompt bundle, checks source trial uniqueness, memory mode, node and prompt context, and rejects missing or conflicting historical D26 seed evidence. Replay calls record and use the verified historical seed. The referenced review records the 50/50 independent harness-seed matches on the recovered, explicitly unfrozen candidate.

## Offline validation

The three focused suites `r1/tests/test_exam_historical_seed.py`, `r1/tests/test_exam_core.py`, and `r1/tests/test_exam_dryrun.py`, using the local harness at `897d83c8efa364ec2fdd37288241cc42e01d7274`, returned `1 failed, 45 passed in 5.09s` under the sandbox. The sole failure was `test_exam_fake_end_to_end`, with `PreparationStop: [Errno 1] Operation not permitted`.

After inspecting the fake-test implementation, the single failed test was run outside the sandbox in a fresh isolated temporary directory. It returned **`1 passed in 43.79s`**. Its retained summary is `/private/tmp/paper-b-fake-e2e-independent-20261031-4cb280/test_exam_fake_end_to_end0/exam/summary.json`: `label=DRYRUN`, `synthetic_metrics=true`, `pass=true`, and all nine checks true. These include the expected deliberate termination of a test-owned child process, successful simulated resume, 11 simulated campaign roots, preservation of completed roots, and retention of the partial attempt.

The dry run used synthetic prompt and model placeholder files, a local fake HTTP server, a synthetic CPU fixture worker and simulated GPU readings. It does not test actual model inference, production GPU behavior, real historical prompt loading end-to-end, or scientific performance. It does not remove any author or protocol gate. No actual model jobs or uploads were performed, and recovered prompt and ledger data were not edited during this review.
