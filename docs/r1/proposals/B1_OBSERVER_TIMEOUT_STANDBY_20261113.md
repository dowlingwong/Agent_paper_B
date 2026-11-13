# B1 observer timeout 60 s → 180 s — standby patch (13 Nov 2026)

AI-assisted (Claude, Mac-local agent). PLAN §10 row `R1-EXAM-B1-OBSERVER-TIMEOUT` (**draft, standby**).

## 0. Status

- **Not for the running `_d`.** `_d` keeps `paper_commit` `02a91494` and its 60 s observer timeout.
- This branch is reviewed and then **kept**. It is delivered as the next D-B1R **only if `_d` stops at M15**, i.e. at an observer request timeout. In every other case it stays unused, and the PLAN row governs nothing.
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
- later commits — documentation and review records only.

From `02a91494` to `239dcd76`, the protected exam paths differ only in `r1/exam/observer.py`.

## 2. Why 180 s

- **What the timeout bounds.** The value is a socket timeout. The observer sends a non-streamed request, and llama-server sends nothing until the whole reply is generated, so the first read waits for the full generation. The timeout is therefore, in practice, a limit on one answer's generation time. Later reads of the body use the same per-read timeout.
- **The longest possible answer.** The observer requests `max_tokens` 4096. A truncated answer (cap reached) is not a STOP: it becomes `query_failed`.
- **Measured rates.**
  - The B1 servers measured so far run at about 33 tokens/s (`olmo31_32b`, from the `_c` STOP capture: proposer calls of 75–108 tokens in 2.1–2.9 s) to 46 tokens/s (`qwen36_27b` / `qwen38_27b` with thinking).
  - At 60 s, an answer of more than about 2,000–2,750 tokens stops the batch.
  - Thinking-on answers measured so far were bounded by the armed budget at about 2,078 tokens, with a longest server time of 44.6 s (`reports/B1_TRUNCATION_DIAGNOSIS_20261111.md` §5).
  - An answer without an armed budget can reach the 4,096 cap: that takes about 124 s at 33 tokens/s.
- **The choice.** 180 s covers the full 4,096 tokens at 23 tokens/s or more, which leaves about 30 % headroom below the slowest server measured. It is well under llama-server's own HTTP read/write timeout: the default is 3,600 s at `620d222` (`common/common.h` l. 632–633), and the exam starts the server without `--timeout`.
- **Cost of a larger value.** A stalled server is noticed later. In the worst case, a root makes 20 observer calls × 180 s = 1 h of its 12 h deadline. A stall still ends as a STOP.

## 3. What does not change

- A timeout is still `B1ObserverFatal` and stops the batch: the observer evidence chain still does not hide a stalled server. Diagnosis §5 argued that this evidence rule is the author's decision, and it is kept.
- The prompt, `max_tokens`, `temperature`, `seed`, `cache_prompt`, journal rows and accounting are unchanged.
- An answer that arrives within 60 s is recorded exactly as before. Only answers that take 60–180 s change, from a STOP to a recorded answer (`ok` or `query_failed`). Observer answers are not decision input.

## 4. Tests

- `test_exam_observer.py::test_observer_request_timeout_is_180_seconds` — the request is sent with timeout 180.0.
- `test_exam_observer.py::test_usage_report_uses_the_observer_timeout` — the usage script uses the same value.
- `test_exam_b1_observer_integration.py::test_observer_timeout_threshold_is_the_constant_and_a_timeout_still_stops` — pinned harness `a3fedbb`, loopback stand-in, timeout replaced by 1 s in the driver:
  - a 0.3 s observer answer completes;
  - a 2.5 s answer stops the batch (`observer_stop`), with a journal `stop` row ("timed out") and no manifest.
- `test_b1_completion_usage.py::test_table_and_cap_check` — updated to use the 180 s value.

Full-suite numbers are in the review record.

## 5. If `_d` stops at M15: delivery checklist

1. **Confirm the STOP is M15.** It is M15 if:
   - the `a4_observer_requests.jsonl` of the stopped root ends with a `stop` row whose error is a timeout ("timed out");
   - the runner log shows `B1ObserverFatal` / "observer transport or response evidence failure".

   It is not M15 if the error is an HTTP status, a connection refusal or a journal failure. Then this patch does not apply.
2. **Check the stopped answer would fit in 180 s.**
   - Find the stopped request in the llama-server log or the server-side record, if available. It must have finished, or the server must have been generating at a normal rate, so that a 4,096-token answer would end within 180 s.
   - If the server was stalled (no progress) or slower than about 23 tokens/s, 180 s is not the right fix. Report to the author instead.
3. **Check the base.**
   - The branch is based on the `_d` run HEAD `7912b7ff`. If `_d` ran from another HEAD, rebase the branch onto it, re-pin `paper_commit` to the rebased code commit, and get a new review.
   - Check that `git diff --name-only 239dcd76 <base> -- r1/exam r1/scripts/exam_runner.py r1/scripts/llama_server_instance.py r1/scripts/llamacpp_probe.py r1/headroom/e1b_collect.py` is empty.
4. **Write the `_e` restart hand-off** from `proposals/B1_RESTART_HANDOFF_D_20261113.md`:
   - a new run ID `<4hex>_<date>_e` and a new output tree;
   - `_d`, `_c`, `_b` and 6835 untouched;
   - retire the `_d` Track X marker at restart, with the receipt in the `_e` handover directory;
   - turn the PLAN row from draft into a rule, with the STOP report reference.

   This needs its own review.
5. **Bundle and register.** Bundle the branch and register it in `READY.txt` as the new D-B1R.
6. **Reuse of `_d`'s completed roots.**
   - Their observer calls all finished within 60 s, so the new threshold would not change them.
   - Reuse is still a separate procedural question, as in the `_c` assessment (diagnosis §6).
   - Assess it only; do not adopt it by default.
