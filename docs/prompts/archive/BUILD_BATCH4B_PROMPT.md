# Build batch 4b: Ada accepted-failure patch for the rerun-2 launcher (14 Oct 2026)

*Written by Claude (coordinating session) at the author's request. A small desktop patch; hand it to the implementation agent on the author's Mac.*

---

You are the implementation agent for Paper B, route R1. Make one change, specified by PLAN §10, row **R1-COMPUTE (Ada environmental test exception 2)**: the rerun-2 launcher's accepted-failure set on Ada gains exactly the harness test

`tests/test_artifact_completeness_and_manifest.py::TestCompletenessCLI::test_checked_in_report_contains_all_plan_campaigns`

in addition to the existing missing-`/bin/zsh` exception. **Nothing else changes.**

## Rules

- No LLM calls, no GPU, no Ada.
- Change only the accepted-failure classification used by `ada_e1b_rerun2_launch.sh` (`--prepare` / `prepare.json`, read again by `--start`) and its tests.
- No other behaviour changes. Do not widen the set by pattern, file or class: add the exact test ID only.
- The exception applies only on the Ada host (`ucrtasl`), just as the zsh exception does. Check how the existing exception is scoped, and scope this one the same way.
- No history rewrite. Label the work AI-assisted.

## Steps

1. **Paper repo.** Run `git pull --ff-only`. `git status --short` must show exactly:
   - ` M docs/r1/PLAN.md`
   - ` M docs/r1/STATUS.md`
   - `?? docs/r1/prompts/BUILD_BATCH4B_PROMPT.md`

   Review the diff, commit it as "Record second Ada test exception; batch-4b prompt", and push.
2. **Tests first (fail before).** Add stub tests in the existing launcher test file:
   - **(a)** On Ada, a `prepare.json` whose only failures are the zsh test and the new test ID is accepted, so `--start` proceeds.
   - **(b)** The same failures off Ada are refused.
   - **(c)** A different test in the same file, `TestCompletenessCLI` or any other, is still refused.
   - **(d)** A non-zero exit with no parsed failures is still refused (the F8 behaviour is kept).

   Show that test (a) fails on the current head `7272d77`.
3. **Implement.** Add the one ID to the accepted set, with a comment that cites the PLAN row. Run `make r1-test` (absolute `AR_HARNESS_ROOT`, venv interpreter) and `make test`. Both must be green, with the previous numbers plus the new tests.
4. **Commit and push.** Commit as "Accept the fresh-checkout report test as Ada-environmental (PLAN §10)" and push. The harness is untouched, so `HARNESS_PIN_RERUN2` stays `411c605`.
5. **STATUS.** Add one entry: the commit, the tests before and after, and confirmation that `ADA_E1B_RERUN2_PROMPT.md` is ready to hand over.

No separate review subagent is needed for this patch. The four tests pin the behaviour; report their names and results.
