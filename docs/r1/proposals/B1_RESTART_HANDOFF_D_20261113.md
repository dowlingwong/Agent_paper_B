# B1 restart hand-off `_d` for the experiment agent (13 Nov 2026)

**Status.** AI-assisted (Claude, Mac-local agent). This is item (4) of the author's route for the STOP of run `4b31_20261112_c` (`reports/B1_STOP_4B31_20261112.md`, `mac-b1-20261107` @ `3b7d5704`; PLAN §10 `R1-EXAM-B1-MODEL-OUTPUT-INVALID`).

- **What the Mac-local agent did:** wrote the fix, the configuration re-pin, the diagnosis and this hand-off, and had them independently reviewed (`reviews/B1_MODEL_OUTPUT_REVIEW_20261113.md`).
- **What it did not do:** set `approved: true`, run the author gate, or launch anything.
- **Relation to earlier hand-offs:** this one replaces `proposals/B1_RESTART_HANDOFF_C_20261111.md` for the next restart. That hand-off and the `_b` one stay as history.

## 0. Preconditions — read first

Armed only when all of these hold; otherwise do nothing and report:

1. PLAN §10 rows `R1-EXAM-B1-ANCHOR-R4`, `R1-EXAM-B1-ANCHOR-R4-H2`, `R1-EXAM-B1-TRUNCATION-INVALID` and `R1-EXAM-B1-MODEL-OUTPUT-INVALID` are committed on the checkout you restart from (all four are on `mac-b1-modelout-20261113`).
2. The reviewed base (§1) is accepted. The diagnosis `reports/B1_MODEL_OUTPUT_DIAGNOSIS_20261113.md` may still show §1.4 (the replay) as PENDING. The replay is optional and not a precondition. If it has been run, it may run before or after the restart, never at the same time as it (one GPU).
3. The frozen venv is the one the truncation fix was checked against (diagnosis `B1_TRUNCATION_DIAGNOSIS_20261111.md` §2.3: openai 2.36.0, langchain_openai 1.2.1, langchain_core 1.3.3, langgraph 1.1.10, pydantic 2.13.4, pydantic_core 2.46.4, httpx 0.28.1). The new tests passed with those versions (diagnosis §4.5). If the venv changed, STOP.

Not covered; go to the author:
- reusing any `_c` root (diagnosis §6; not adopted);
- any decision listed in diagnosis §5 (observer timeout, audit-seed failure, declared ranges);
- any change to harness pin, server flags, thinking policy, rule or budgets.

## 1. The fix and the checkout

- **Branch** `mac-b1-modelout-20261113`, based on the `_c` run HEAD `4b312844`.
- **`3458b672`** — the model-output pre-check, the context-overflow rule and the proposal journal:
  - code: `r1/exam/b1_proposal_precheck.py` and `r1/exam/b1_proposal_journal.py` (new); `r1/exam/b1_llm_truncation.py`, `r1/exam/campaign.py` and `r1/exam/b1_batch.py` (changed); `r1/exam/b1_proposal_guard.py` (docstring only);
  - the replay script `r1/scripts/b1_proposal_replay.py`; `r1/scripts/b1_completion_usage.py` (counts overflow calls);
  - tests: `r1/tests/test_exam_b1_model_output.py`, `r1/tests/test_b1_proposal_replay.py` and additions to `test_b1_completion_usage.py` and `test_exam_b1_batch_verify.py`. They need `AR_HARNESS_B1_ROOT` at `a3fedbb`; set `R1_REQUIRE_B1_HARNESS=1` so they cannot skip.
- **`2eda52e7`** — `paper_commit` moves from `1334c616` to `3458b672` (one line).
- **Later commits:** documentation only (PLAN row, diagnosis, replay hand-off, this hand-off, appendix draft, review records).
- **Reviewed base:** the commit on the `Accepted commit:` line of the last accepted round in `reviews/B1_MODEL_OUTPUT_REVIEW_20261113.md`.
  - The `Reviewed base:` line at the top of that file and `Claude outputs/READY.txt` (item D-B1R, model output) must name the same SHA. If the three disagree, STOP.
  - Commits after the base may only add review records to that file. Check that `git diff --name-only <base> <remote tip>` lists nothing but `docs/r1/reviews/B1_MODEL_OUTPUT_REVIEW_20261113.md`.
  - Check that `git diff --name-only 3458b672 <base> -- r1/exam r1/scripts/exam_runner.py r1/scripts/llama_server_instance.py r1/scripts/llamacpp_probe.py r1/headroom/e1b_collect.py` is empty.
- **Run HEAD:** one new commit on top of the reviewed base, on a new branch `ops-b1-restart-d-<YYYYMMDD>`. Push it without force.
  - It changes **only the prose** of `docs/r1/authorizations/trackx_b1_20261105.md`: name this restart, the stopped run `4b31_20261112_c`, the reviewed base and this hand-off. The JSON bindings stay byte-identical. The note inherited from `4b312844` describes the `_c` restart and must not be used as is.
  - That commit gets the exact-HEAD review and the real author gate.
  - Its first four hex digits give the run ID. Report its SHA back.
- **Fetching:** fetch only the remote copy of `mac-b1-modelout-20261113`, at the reviewed base or a later review-record-only commit. The branch arrives by bundle and is pushed from the Mac.

## 2. Restart conditions, in order

1. The fix, the diagnosis and this hand-off are accepted by a freshly spawned independent reviewer (§0, §1).
2. The author's route is in PLAN §10 (`R1-EXAM-B1-MODEL-OUTPUT-INVALID`). The rerun follows review without a further author message; the `paper_commit` re-pin is part of the fix.
3. **Exact new checkout:**
   - Create the run-HEAD note commit of §1 and have that HEAD independently reviewed.
   - Stage it clean on TASL-7 as for `_c`: `b1_paper_final_<FULL_HEAD>/paper`, with the harness at `b1_harness_offline_stage_20261107_a/harness` (`a3fedbb`).
   - Run the real author gate on it.
4. **Fresh checks before the handover.** Each of the following is re-reviewed for the new HEAD and run ID:
   - a TASL-7 read-only occupancy check;
   - the host preflight (`proposals/B1_FINAL_HOST_PREFLIGHT_INVOCATION_20261108.md`), with a new absent `--out` directory and a new capture directory;
   - the handover (`proposals/B1_TASL7_O2_EXECUTABLE_DRAFT_20261107.md` with `reports/B1_TASL7_HANDOVER_COMMAND_BOUNDARY_20261107.md`).

   Publish STATUS on `mac-b1-20261107`. Do not preempt other users' work (R1-TASL7-AGENT-OCCUPANCY-07NOV).

   **Track X marker transition.** Retire the marker in place at restart, as the author has ordered and as at the `_b` and `_c` restarts. The `_c` run's `~/r1_locks/trackx_evidence.active` is still present: content `{"head":"4b312844…","run_id":"4b31_20261112_c"}`, SHA-256 `f8c8624f903b36e99e835f14fa0892e63b5e5a25d1e6ff41f6b1a3b5542a73fe`, creation receipt `/home/dowling/r1_b1_engineering/b1_handover_4b31_20261112_c/marker-receipt.json` (SHA-256 `e0da112f3fdfe3e14a14e0dc1470f2c6b66f5ff1e73e8acc243847037a3762c6`). The procedure:
   - Confirm the P.3a safe pause **before** `retire`. If it cannot be confirmed, do not retire, and STOP.
   - Keep Track P paused throughout.
   - Retire with `b1_o2_marker.py retire` and that receipt. The tool renames the marker into `~/r1_locks/_to_delete/`; nothing is deleted.
   - Write the retirement receipt into the new `_d` handover directory, naming the `_c` creation receipt by path and SHA-256. Write nothing into the `_c` handover directory.
   - Create the new marker and keep its receipt.

   If the marker does not match its receipt, STOP. This is the only change to the `_c` scene that this hand-off allows.

   The `_c` post-run retirement unit (`proposals/B1_C_POSTRUN_RETIREMENT_20261112.md`) does not apply, since `_c` did not complete normally. Track S's `digits_mlp` host move waits for the author either way (STOP report §4).
5. **New run ID and fresh output tree.** The run ID is `⟨first four hex of the new run HEAD⟩_⟨UTC start date YYYYMMDD⟩_d` and the output tree is `/home/dowling/exam-x/work/b1_<run ID>`. Under R1-EXAM-B1-NO-DELETION-07NOV, nothing of the following is moved, overwritten or deleted:
   - run `4b31_20261112_c`: `$B=/home/dowling/exam-x/work/b1_4b31_20261112_c`, its handover directory, its staged checkout and its captures;
   - run `fffa_20261111_b`;
   - run `6835_20261108_a`.

   The only exception is the marker transition in step 4. All roots are rerun; none of the 89 completed `_c` roots is reused (diagnosis §6).
6. Any further STOP in the new run is preserved and reported, not retried. The following no longer stop the run; each becomes an invalid trial:
   - a model-output fault of diagnosis §3 M5–M9;
   - a prompt beyond the context after trial 1 (M19);
   - a reply with a lone surrogate, which would make the next request unencodable (M20);
   - a truncated proposal.

   Everything else in §3 still stops, as before.

B2, X.7 and sweep 2 remain separately gated.

## 3. After the run

As in hand-off `_c` §3: the anchors are descriptive; `b1_candidate_halves` gives the halves table; `b1_completion_usage` gives the usage tables.

In addition, per candidate and mode, the B1 report gives the model-output rejections by check. They are read from each root manifest's `proposal_journal.rejected_by_check`; the same counts are in `b1_proposals.jsonl`. The appendix draft `reports/B1_MODEL_OUTPUT_APPENDIX_DRAFT_20261113.md` gets its ⟨…⟩ fields from them.

## 4. What to send back

The same set as for `_c`:
- the run ID and the checkout SHA you started;
- the review of that HEAD;
- the author-gate receipt;
- the preflight and handover receipts, including the marker-retirement receipt;
- the first monitor capture.
