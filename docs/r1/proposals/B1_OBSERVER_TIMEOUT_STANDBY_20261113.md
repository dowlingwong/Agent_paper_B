# B1 observer timeout 60 s → 180 s — standby patch (13 Nov 2026)

AI-assisted (Claude, Mac-local agent). PLAN §10 row `R1-EXAM-B1-OBSERVER-TIMEOUT` (**draft, standby**).

## 0. Status

- **Not for the running `_d`.** `_d` keeps `paper_commit` `02a91494` and its 60 s observer timeout.
- This branch is reviewed and then **kept**. It is delivered as the next D-B1R **only if `_d` stops at M15**, i.e. at an observer request timeout. In every other case it stays unused, and the PLAN row governs nothing.
- **Who decided.** The author asked on 13 Nov for this standby patch: reviewed, kept, and delivered as the next D-B1R only after a `_d` STOP at M15. Delivery under §5 therefore needs no further author message. The `_e` restart itself still needs its own reviewed hand-off, the exact-HEAD review and the real author gate. If any check in §5 fails, nothing is delivered and the case goes to the author.
- M17 (audit-seed failure) and M14 (`digits_mlp` declared ranges) stay as they are.

## 1. The change

| | before (`_d`) | standby |
|---|---|---|
| `r1/exam/observer.py` request timeout | `urlopen(..., timeout=60.0)` | `urlopen(..., timeout=OBSERVER_TIMEOUT_S)`, `OBSERVER_TIMEOUT_S = 180.0` |
| `r1/scripts/b1_completion_usage.py` | margins against 60 s | margins against 180 s |
| `paper_commit` | `02a91494` | `239dcd76` |

Commits on `mac-b1-obs180-20261113` (based on the `_d` run HEAD `7912b7ff`):
- `239dcd76` — code and tests;
- `832dc796` — re-pin (one line);
- later commits — documentation, the usage report's table header (`r1/scripts/b1_completion_usage.py`, not a protected path) and review records only.

From `02a91494` to `239dcd76`, the protected exam paths differ only in `r1/exam/observer.py`.

## 2. Why 180 s

- **What the timeout bounds.** The value is a socket timeout, applied to each blocking operation (connect, each read), not to the request as a whole. The observer sends a non-streamed request, and llama-server sends nothing until the whole reply is generated (checked in the server source at `620d222`), so the read of the response headers waits for the full generation. The timeout is therefore, in practice, a limit on one answer's generation time. Later reads of the body use the same per-read timeout. The exam server runs one slot, so an observer request never queues behind another request.
- **The longest possible answer.** The observer requests `max_tokens` 4096. A truncated answer (cap reached) is not a STOP: it becomes `query_failed`.
- **Measured rates.**
  - The B1 servers measured so far run at about 33 tokens/s to 46 tokens/s (`qwen36_27b` / `qwen38_27b` with thinking). The 33 tokens/s is the slowest per-call wall-clock proposer rate (completion tokens / latency, including prompt evaluation) of `olmo31_32b` in the `_c` STOP capture (`docs/r1/reports/b1_stop_4b31_20261112/root_events.jsonl` @ `3b7d5704`, not on this branch: calls of 75–108 tokens in 2.1–2.9 s, 33.3–37.4 tokens/s). It is conservative: the same server decodes observer answers at 42.7 tokens/s per llama-server's `timings`. `olmo31_32b` does not run thinking-on in B1, so it bounds long answers it will not itself produce; it serves as a floor.
  - At 60 s, an answer of more than about 2,000–2,750 tokens stops the batch.
  - Thinking-on answers measured so far were bounded by the armed budget at about 2,078 tokens, with a longest server time of 44.6 s (`reports/B1_TRUNCATION_DIAGNOSIS_20261111.md` §5).
  - An answer without an armed budget can reach the 4,096 cap: that takes about 124 s at 33 tokens/s.
- **The choice.** 180 s covers the full 4,096 tokens at 23 tokens/s or more, which leaves about 30 % headroom below the slowest server measured, enough for the decode slowdown as a generation grows towards 4k tokens. It is well under llama-server's own HTTP read/write timeout: the default is 3,600 s at `620d222` (`common/common.h` l. 632–633), and the exam starts the server without `--timeout`.
- **Cost of a larger value.** A stalled server is noticed later. In the worst case, a root makes 20 observer calls (the observer is asked only after a worker run; W = 20) × 180 s = 1 h of its 12 h deadline. A stall still ends as a STOP.

## 3. What does not change

- A timeout is still `B1ObserverFatal` and stops the batch: the observer evidence chain still does not hide a stalled server. Diagnosis §5 argued that this evidence rule is the author's decision, and it is kept.
- The prompt, `max_tokens`, `temperature`, `seed`, `cache_prompt`, journal rows and accounting are unchanged.
- An answer whose response headers arrive within 60 s is recorded exactly as before. Only answers whose headers take 60–180 s change, from a STOP to a recorded answer (`ok` or `query_failed`).
- Observer answers are not ranking input (`mu_hat`, finalists). They feed only the descriptive A4 summary (`a4_log_score`, `a4_brier`, `forecast_summary`), which under `x5_rule_v2` uses thinking-off rows only, where observer calls take under 1 s. So the change can alter `forecast_query_failed` counts of thinking-on rows, but in practice not the reported A4 scores.
- **Scope.** At this commit the observer runs only in B1: Stage A does not import it; `authorized_b1_observer` refuses any other phase (`observer.py` l. 52–53), and v2 B2 authority is not implemented (`runtime.py` l. 425–426). B2 code built on this commit would inherit 180 s unless it changes it.

## 4. Tests

- `test_exam_observer.py::test_observer_request_timeout_is_180_seconds` — the request is sent with timeout 180.0.
- `test_exam_observer.py::test_usage_report_uses_the_observer_timeout` — the usage script uses the same value.
- `test_exam_b1_observer_integration.py::test_observer_timeout_threshold_is_the_constant_and_a_timeout_still_stops` — pinned harness `a3fedbb`, loopback stand-in, timeout replaced by 1 s in the driver:
  - a 0.3 s observer answer completes;
  - a 2.5 s answer stops the batch (`observer_stop`), with a journal `stop` row ("timed out") and no manifest.
- `test_b1_completion_usage.py::test_table_and_cap_check` — updated to use the 180 s value.

Full suite (`pytest -k "exam or b1" r1/tests`, `/tmp/trackg_venv`, `AR_HARNESS_ROOT` = Track G harness checkout, `AR_HARNESS_B1_ROOT` = `a3fedbb`, `R1_REQUIRE_B1_HARNESS=1`):
- this branch: 763 passed / 18 failed / 0 skipped;
- the `_d` run HEAD `7912b7ff`: 758 / 18 / 0. Its code is identical to the model-output review's tip, which was measured there.

The 18 failures are the same test IDs. The observer, observer-integration and usage tests (20) also pass in `/tmp/hostver_venv`, which has the host's package versions.

## 5. If `_d` stops at M15: delivery checklist

1. **Confirm the STOP is M15.** All of the following must hold:
   - in the stopped root's `a4_observer_requests.jsonl`, the last request's rows are exactly a `request_attempt` followed by a `stop`, with no `response_headers` row between them (the server never answered);
   - the `stop` row's error is exactly `TimeoutError: timed out` (a read timeout while waiting for the response);
   - the runner log shows the full message `STOP: B1 observer evidence failed: STOP: observer transport or response evidence failure: TimeoutError: timed out`.

   **Not M15**, and this patch does not apply: an HTTP status (a `response_headers` row exists); `URLError: <urlopen error timed out>` (a connect timeout) or a connection refusal or reset; a timeout after `response_headers` (in the middle of the body); `IncompleteRead` or another malformed body; a journal failure; a watchdog or deadline STOP. Report these to the author.
2. **Check the stopped answer would fit in 180 s.**
   - Find the stopped request in the llama-server log or the server-side record, if available. It must have finished, or the server must have been generating at a normal rate, so that a 4,096-token answer would end within 180 s.
   - If the server was stalled (no progress) or slower than about 23 tokens/s, 180 s is not the right fix. Report to the author instead.
3. **Check the base.** Protected paths below mean `r1/exam r1/scripts/exam_runner.py r1/scripts/llama_server_instance.py r1/scripts/llamacpp_probe.py r1/headroom/e1b_collect.py`.
   - The branch is based on the `_d` run HEAD `7912b7ff`. If `_d` ran from another HEAD, rebase the branch onto it, re-pin `paper_commit` to the rebased code commit, update the commit hashes in the PLAN row and in this note, and get a new review.
   - Check that `git diff --name-only <_d run HEAD> <paper_commit> -- <protected paths>` lists exactly `r1/exam/observer.py`.
   - On the `_e` run checkout: `paper_commit` is an ancestor of HEAD, and `git diff --name-only <paper_commit> HEAD -- <protected paths>` is empty.
4. **Write the `_e` restart hand-off** from `proposals/B1_RESTART_HANDOFF_D_20261113.md`:
   - a new run ID `<4hex>_<date>_e` and a new output tree;
   - `_d`, `_c`, `_b` and 6835 untouched;
   - retire the `_d` Track X marker at restart with `b1_o2_marker.py retire`, which renames it into `~/r1_locks/_to_delete/` (nothing is deleted), and write the retirement receipt into the `_e` handover directory, naming the `_d` creation receipt by path and SHA-256;
   - turn the PLAN row from draft into a rule, with the STOP report reference.

   This needs its own review.
5. **Bundle and register.** Bundle the branch and register it in `READY.txt` as the new D-B1R.
6. **Reuse of `_d`'s completed roots.**
   - Their observer calls all finished within 60 s, so the new threshold would not change them.
   - Reuse is still a separate procedural question, as in the `_c` assessment (diagnosis §6).
   - Assess it only; do not adopt it by default.
