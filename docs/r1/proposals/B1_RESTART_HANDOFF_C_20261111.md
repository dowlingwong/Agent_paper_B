# B1 restart hand-off `_c` for the experiment agent (11 Nov 2026)

**Status.** AI-assisted (Claude, Mac-local agent). This is item (4) of the author's route for the STOP of run `fffa_20261111_b` (report `reports/B1_STOP_FFFA_20261111.md`, branch `mac-b1-20261107` @ `8af27919`; PLAN §10 `R1-EXAM-B1-TRUNCATION-INVALID`). The Mac-local agent wrote the fix, the configuration re-pin, the diagnosis and this hand-off, and had them independently reviewed (`reviews/B1_TRUNCATION_REVIEW_20261111.md`). It did **not** set `approved: true`, run the author gate or launch anything. This hand-off replaces `proposals/B1_RESTART_HANDOFF_20261109.md` for the next restart. That earlier hand-off described the `_b` restart and is kept as history.

## 0. Preconditions — read first

This hand-off is **armed only when all of these hold**; otherwise do nothing and report:

1. `reports/B1_TRUNCATION_DIAGNOSIS_20261111.md` on the reviewed base has no **PENDING** section left: §2.3 (host confirmations) and §3 (per-root completion table) are filled from the read-only host check `proposals/B1_TRUNCATION_HOST_CHECK_HANDOFF_20261111.md`.
2. Its §3 cap check reads **PASS**: the largest proposer completion over the 64 completed roots of `fffa_20261111_b` is below 16,384. Check the number yourself against the table. FAIL, or a table with fewer than 64 completed roots, goes to the author.
3. PLAN §10 row `R1-EXAM-B1-TRUNCATION-INVALID` is committed on the checkout you restart from, next to `R1-EXAM-B1-ANCHOR-R4` and `R1-EXAM-B1-ANCHOR-R4-H2` (all three are on `mac-b1-trunc-20261111`).
4. Diagnosis §2.3 records that `r1/tests/test_exam_b1_truncation.py` passed (none skipped) in a scratch venv with exactly the frozen venv's versions of `openai`, `langchain_openai`, `langchain_core`, `langgraph`, `pydantic` and `httpx` from the host check. (The capped proposer also refuses to start if the SDK lacks `LengthFinishReasonError` or `ContentFilterFinishReasonError`; that refusal at root start would be a STOP.)

Not covered; go to the author: a cap-check FAIL; a diagnosis §5 observer margin or §5a per-root deadline margin the review calls insufficient (the deadline bound uses a proposer rate that includes prompt evaluation, so it is slightly conservative); any change to the harness pin, server flags, thinking policy, rule or budgets.

## 1. The fix and the checkout

- Branch `mac-b1-trunc-20261111`, based on the `_b` run HEAD `fffa45a1` (= reviewed base `ac32231c` + the run-HEAD note).
- `1334c616`: `r1/exam/b1_llm_truncation.py` (new) and `r1/exam/campaign.py::exam_manager`. Every proposer call sends `max_completion_tokens` = 16,384. A reply cut short becomes an invalid trial, charged to the LLM budget; the campaign continues. Tests: `r1/tests/test_exam_b1_truncation.py`, which needs `AR_HARNESS_B1_ROOT` at harness `a3fedbb`; set `R1_REQUIRE_B1_HARNESS=1` so that it cannot skip. Also added: the read-only usage script `r1/scripts/b1_completion_usage.py` with its test, and the host-check hand-off.
- `62adc6a3`: `r1/scripts/configs/exam_b1_v2.json` `paper_commit` moves from `fb57c6a4` to `1334c616` (one line). From `fb57c6a4` to `1334c616`, only `r1/exam/campaign.py` and `r1/exam/b1_llm_truncation.py` differ in the protected paths. Rule SHA, harness commit `a3fedbb`, value grids, duplicate-rate interval, seeds, nodes, context and budgets are untouched.
- Later commits: documentation only (PLAN row, diagnosis, appendix draft, RUNBOOK X.4 and PORTAL Phase 5 notes, this hand-off, review records).
- **Reviewed base:** the commit named on the `Accepted commit:` line of the last accepted round in `reviews/B1_TRUNCATION_REVIEW_20261111.md`. The `Reviewed base:` line at the top of that file and `Claude outputs/READY.txt` (item D-B1R, truncation) must name the same SHA; if the three disagree, STOP. Commits after the base may only add review records to that file. Check that `git diff --name-only <base> <remote tip>` lists nothing but `docs/r1/reviews/B1_TRUNCATION_REVIEW_20261111.md`, and that `git diff --name-only 1334c616 <base> -- r1/exam r1/scripts/exam_runner.py r1/scripts/llama_server_instance.py r1/scripts/llamacpp_probe.py r1/headroom/e1b_collect.py` is empty. Any other commit after the base needs a new independent review before use.
- **Run HEAD:** one new commit on top of the reviewed base, on a new branch `ops-b1-restart-c-<YYYYMMDD>` that you push (no force). It changes **only the prose** of `docs/r1/authorizations/trackx_b1_20261105.md`: name this restart, the stopped run `fffa_20261111_b`, the reviewed base and this hand-off; the JSON bindings stay byte-identical. That commit gets the exact-HEAD review and the real author gate; its first four hex digits give the run ID; report its SHA back. The note as inherited from `fffa45a1` describes the `_b` restart and must not be used as is.
- Fetch only the remote copy of `mac-b1-trunc-20261111`, at the reviewed base or a later review-record-only commit. The Mac-local agent cannot push; the branch arrives by bundle and is pushed from the Mac.

## 2. Restart conditions, in order

1. The fix, the diagnosis (with §3 filled) and this hand-off are accepted by a freshly spawned independent reviewer (§0, §1).
2. The author's route is in PLAN §10 (`R1-EXAM-B1-TRUNCATION-INVALID`). The rerun follows review without a further author message; the `paper_commit` re-pin is part of the fix.
3. **Exact new checkout:** create the run-HEAD note commit of §1; have that HEAD independently reviewed; stage it clean on TASL-7 as for `_b` (`b1_paper_final_<FULL_HEAD>/paper`, harness `b1_harness_offline_stage_20261107_a/harness` at `a3fedbb`); run the real author gate on it.
4. Fresh TASL-7 read-only occupancy check, host preflight (`proposals/B1_FINAL_HOST_PREFLIGHT_INVOCATION_20261108.md`, with a new absent `--out` directory and a new capture directory) and handover (`proposals/B1_TASL7_O2_EXECUTABLE_DRAFT_20261107.md` with `reports/B1_TASL7_HANDOVER_COMMAND_BOUNDARY_20261107.md`), each re-reviewed for the new HEAD and run ID. Publish STATUS on `mac-b1-20261107` as R1-EXAM-B1-STATUS-FEATURE-07NOV requires. Do not preempt other users' work (R1-TASL7-AGENT-OCCUPANCY-07NOV).
   **Track P marker transition** (the Mac-local agent's reading, not stated by the author; PLAN row `R1-EXAM-B1-TRUNCATION-INVALID` gives the reason: the marker is a cooperative lock, not evidence, renamed not deleted, and its content and receipts are already in the STOP report §2/§5; precedent `R1-EXAM-B1-ANCHOR-R4`). The `_b` run's `~/r1_locks/trackx_evidence.active` is still present (dev 66306, ino 56261610, SHA-256 `23fa767be7346809d087d0a2352241e6042abdd04df2f198e476b8f39eab4c9a`, content naming run `fffa_20261111_b`; creation receipt `…/b1_handover_fffa_20261111_b/marker-receipt.json`, SHA-256 `1cd979aedef534f611963e419a92c02fe385d81f8119d477d4389480459a4405`). `b1_o2_marker.py create` uses exclusive create, so a new handover fails while that marker exists. Procedure, as at the `_b` restart:
   - Confirm the P.3a safe pause **before** `retire`. If it cannot be confirmed, do not retire, and STOP.
   - Keep Track P paused throughout.
   - Retire the old marker with `b1_o2_marker.py retire` and its creation receipt. The reviewed tool renames it into `~/r1_locks/_to_delete/`; nothing is deleted.
   - Write the retirement receipt into the new `_c` handover directory, naming the `_b` creation receipt by path and SHA-256. Write nothing into the `_b` handover directory.
   - Create the new marker in the new handover and keep its receipt.
   If the old marker does not match its receipt, STOP and report. This marker transition is the only change to the `_b` scene that this hand-off allows.
5. **New run ID and fresh output tree.** Run ID `⟨first four hex of the new run HEAD⟩_⟨UTC start date YYYYMMDD⟩_c`, output tree `/home/dowling/exam-x/work/b1_<run ID>`. Nothing of run `fffa_20261111_b` (`/home/dowling/exam-x/work/b1_fffa_20261111_b/`, its handover directory, staged checkout and captures) or of run `6835_20261108_a` is moved, overwritten or deleted (R1-EXAM-B1-NO-DELETION-07NOV). The only exception is the marker transition in step 4.
6. Any further STOP in the new run is preserved and reported, not retried. A truncated proposal is no longer a STOP; any other LLM-call failure still is.

B2, X.7 and sweep 2 remain separately gated.

## 3. After the run

As in the earlier hand-off §3:
- The anchors are shown descriptively, with `scripted_minus_random` read from `batch_state.json`.
- The first- vs second-half table comes from `python -m r1.scripts.b1_candidate_halves --work …`.

In addition, per candidate and mode, the B1 report gives the number of proposer calls, the number of **truncated** proposals, the largest completion and the proposer rate. Read-only: `python -m r1.scripts.b1_completion_usage --roots /home/dowling/exam-x/work/b1_<run ID> --cap 16384` (both tables). In the new run, truncated calls end at the cap by design, so exit 1 (cap check FAIL) is expected there and is not a STOP; exit 2 (inconsistent input) is reported. A truncated call is always the final proposal of its trial (it names no key, so no D25 revision follows), so the per-root counts are complete. Finish reasons of truncated calls are in each `llm_call` record.

The appendix draft `reports/B1_TRUNCATION_APPENDIX_DRAFT_20261111.md` gets its ⟨…⟩ fields from this table and from the diagnosis.

## 4. What to send back

The same set as for `fffa_20261111_b`:
- the run ID and the checkout SHA you started;
- the review of that HEAD;
- the author-gate receipt;
- the preflight and handover receipts, including the marker-retirement receipt;
- the first monitor capture.
