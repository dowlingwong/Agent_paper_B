# Review: P.4 `sft-select` missing-runs STOP (local/20261127-02)

- **Unit:** `mac-p4-runs-stop-20261127` @ `8720d26b`, base `main` @ `6684e840`.
- **Files:** `r1/scripts/trackp.py` (`cmd_sft_select`) and the new `r1/tests/test_trackp_sft_select_stop.py`.
- **Task:** `tasks/local/20261127-02-p4-missing-runs-stop.md`, raised by compute's report `reports/20261126-05-hostconfig-torch-tests.md`.
- **Reviewer:** an independent tier-E reviewer (Claude subagent) who did not write the unit. It modified, committed and pushed nothing. The local worker transcribed this record from the hand-back.

## Correctness

- **The check runs before `select_lr` reads anything.** It follows the `--runs` presence check and collects every problem into one `TrackPStop`, so the command prints `STOP:` with rc 2.
- **Every failure form STOPs with rc 2** (checked by hand with a filled config):
  - missing directory;
  - no `stage_s`;
  - the report path is a directory;
  - the run path is a file;
  - mode 000;
  - not UTF-8;
  - malformed JSON.
- **Valid runs behave as before.**
- **The race between the check and the read is acceptable.** A report deleted in between would surface as an infrastructure failure.

## Classification in the P.4 job

- `p4_lib.trackp` maps rc 2 with a `STOP:` line to `ProtocolStop`.
- **This cannot misclassify inside `run_job`:**
  - A crashed `sft-dev` is an infrastructure Stop already at that point (an OOM is an ArmStop).
  - If `sft-dev` exits 0 but writes no report, `check_run_protocol` records it as infrastructure.
  - `sft-select` runs only after all nine grid runs passed.
- So the new STOP comes only from a direct call with a bad `--runs` path. That is a refused input, so the protocol class is right.

## Tests

- **Fix tip:** 160 passed (`test_trackp_sft_select_stop.py` and `test_trackp_p4_runner.py`, with torch).
- **Merged with the filled host config `021c4eec`:** 160 passed, including the formerly failing `test_trackp_runs_the_clone_script_from_the_job_directory`.
- **Same merged tree with the fix reverted:** 3 failed (that runner test and two of the new tests).

## Minor findings

1. The malformed-JSON test did not exercise the fix, because `_sft_errors` already turned the JSON error into a STOP. It should assert the new message.
2. The pre-check read the file in the locale's encoding instead of `utf-8`.
3. "OSError: missing" is vague.
4. A report that parses but is not an object (`[]`) passed the pre-check and failed in `select_lr` with rc 1.

Verdict: ACCEPTED WITH MINORS

## Author's response

All four minors are fixed:
- the test asserts "run report missing or unreadable", and adds a `[]` case asserting "not a JSON object";
- the pre-check reads with `encoding="utf-8"`;
- the message is now "not a file";
- the report must be a JSON object.

After the fix: `test_trackp_sft_select_stop.py` and the runner test give 4 passed.
