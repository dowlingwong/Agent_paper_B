Reviewed base: dd0aa0da316aeb1cbd0e1d41aa4b9be018ae1256

# R1-EXAM-B1-OBSERVER-TIMEOUT (standby) — independent review record (13/14 November 2026)

Branch `mac-b1-obs180-20261113` (from the `_d` run HEAD `7912b7ff`). Standby patch: delivered only if `_d` stops at M15 (standby note §5). Two rounds by one freshly spawned independent reviewer agent (AI-assisted, Claude).
- Round 1: changes requested. Four should-fix items (usage-report header; exact M15 criteria; base check; delivery and marker details) and five notes.
- Round 2: **accepted** at `dd0aa0da`, which is the reviewed base.

Accepted commit (round 2, last): dd0aa0da316aeb1cbd0e1d41aa4b9be018ae1256

Final pin: `paper_commit` = `239dcd761d6640dde0bb82211456149cfbadbb41` (`832dc796`).

Round-2 notes carried forward, not blocking:
- The exact `TimeoutError: timed out` string assumes Python ≥ 3.10; on an older interpreter the check fails closed (not M15, goes to the author).
- In the runner log, search for the full message as a substring, since a traceback class prefix precedes it.

The round texts are reproduced unchanged below.

---

# Review: B1 observer timeout 60 s -> 180 s, standby (round 1)

Reviewer: independent (Claude subagent). I did not write this change.
Unit: branch `mac-b1-obs180-20261113`, tip `4de28e3012e6b9ff0f57e6c6fd4c04a49fa50ff0`, base `7912b7fffb4c1adeb39688bdb3852a919bdc71c8` (`_d` run HEAD).
Commits reviewed: `239dcd76` (code + tests), `832dc796` (re-pin), `c1d28257`, `4de28e30` (docs).
I did not modify `/tmp/pb/wt/obs` (`git status --porcelain` is empty). I made scratch worktrees under `/tmp/rev_obs1/` and removed them at the end.

## What I ran

| Check | Result |
|---|---|
| Full suite at tip (`/tmp/trackg_venv`, the author's env, `-k "exam or b1" r1/tests`) | **762 passed / 18 failed / 0 skipped** (4 m 21 s) |
| Same at base `7912b7ff` | **758 / 18 / 0**; `diff` of the FAILED ID lists between base and tip is empty. The +4 are the 4 new tests. |
| `/tmp/hostver_venv` (Python 3.13.18, openai 2.36.0), tip: `test_exam_observer.py`, `test_exam_b1_observer_integration.py`, `test_b1_completion_usage.py`, plus `test_exam_observer_cache.py`, `test_exam_b1_observer_guard.py` | 51 passed (the author's 19 are among them) |
| Mutation: tip tests run against the **base** `observer.py` and `b1_completion_usage.py` | 4 fail: `test_observer_request_timeout_is_180_seconds`, `test_usage_report_uses_the_observer_timeout`, `…timeout_still_stops[2.5-observer_stop]` (with the old literal 60.0 the 2.5 s answer completes), `test_table_and_cap_check`. The new tests do tell the two versions apart. |
| New integration test repeated 5x, then 3x more on 2 cores with 4 busy-loop processes | 8/8 passes (about 7 s each, about 13 s under load). I saw no flakiness. |
| Driver run directly (`slow`, delay 2.5 s, timeout 1 s) | Journal ends with `{"error": "TimeoutError: timed out", "event": "stop", "sequence": 1}`. No `campaign_manifest.json`. Status `observer_stop`. The timeout fires in `getresponse()` before any header, which is the same path a real non-streamed llama-server takes. |
| Re-pin checks | See §4 below. All pass. |
| llama.cpp `620d222` sources (fetched `common/common.h`, `tools/server/server-http.cpp`, `tools/server/server-context.cpp` from raw.githubusercontent.com) | Confirmed `timeout_read = 3600` and `timeout_write = timeout_read` at `common.h` l. 632–633. A non-stream response is built with `res->ok(...)` after all results arrive, then `set_content`. Nothing is sent before generation completes. `sse_ping_interval` applies to streaming only. |
| `_c` STOP capture `docs/r1/reports/b1_stop_4b31_20261112/root_events.jsonl` @ `3b7d5704` | 20 proposer calls: 75–108 tokens in 2.09–2.94 s. Per call that is 33.3–37.4 tokens/s; aggregate 35.0 (wall-clock, including prompt evaluation). The 19 observer calls in the same capture have server `timings.predicted_per_second` of 42.7 (31 tokens, `finish_reason` stop). |

## 1. Code change (`r1/exam/observer.py`)

- `OBSERVER_TIMEOUT_S = 180.0` is a module global (l. 23). It is read at call time in `urlopen(request, timeout=OBSERVER_TIMEOUT_S)` (l. 154). The driver's monkeypatch of the module attribute takes effect, which also shows the call-time lookup.
- Semantics are unchanged:
  - A timeout raises `TimeoutError` (or `URLError` on connect) inside `_request`.
  - That becomes a journal `stop` row, then `D3EvidenceStop('STOP: observer transport or response evidence failure: …')` (l. 190–196).
  - The adapter wraps that in `B1ObserverFatal` (BaseException, l. 240–241), which escapes the pinned harness's `except Exception` around `observe()` (harness `a3fedbb` `campaign.py` l. 1699–1702).
  - Nothing else changed in the module.
- Other references to the old 60 s:
  - Code and tests: none left in `r1/exam`, `r1/tests` or the runner.
  - `r1/scripts/b1_completion_usage.py` still has three stale "60 s" mentions. See S1.
  - The other `60.0` defaults in the repo (`prior_model.chat_client`, `llama_server_instance.build_info`/`gpu_compute_apps`, subprocess timeouts in tests) are unrelated.
- Scope. The observer is built only in `campaign.observer_for_campaign` (`campaign.py` l. 112–116) and wrapped by `B1ObserverAdapter`.
  - `collect` always enters `authorized_b1_observer(job)`, which refuses any phase other than `b1` (`observer.py` l. 52–53).
  - `runtime.author_gate` also refuses v2 B2 ("X5 v2 B2 authority and ranking are not implemented", `runtime.py` l. 425–426).
  - Stage A does not import the observer (its `cache_*` paths use their own 600 s timeouts).
  - So at this commit the change affects B1 only. See N3 on the B2 sentence.

## 2. Factual claims in the PLAN draft row and the standby note

| Claim | Verdict |
|---|---|
| urllib timeout is per blocking operation, not total; later body reads use the same per-read timeout | Correct. The socket timeout applies to connect, send and each recv. `read_chunks` (`cache_io.py` l. 20–29) has no total deadline. |
| llama-server sends nothing until a non-streamed reply is complete | Correct for `620d222` (see above). The observer payload has no `stream` field. |
| `olmo31_32b` about 33 tokens/s; 75–108 tokens in 2.1–2.9 s | Correct as the slowest per-call wall-clock rate (33.3). It is conservative: the same server decodes at 42.7 tokens/s per `timings` (N1). The capture is not reachable from this branch (it is on `3b7d5704`/`c5fbf7de`), and the note gives no commit (N1). |
| 44.6 s / 2,078 tokens, about 46 tokens/s (`qwen36_27b`/`qwen38_27b` on) | Matches `B1_TRUNCATION_DIAGNOSIS_20261111.md` §5. |
| 2,000–2,750 tokens at 60 s | 33×60 = 1,980; 46×60 = 2,760. OK. |
| 180 s covers 4,096 tokens at ≥ 23 tokens/s; about 30 % headroom | 4,096/180 = 22.8; 23/33 = 0.70. OK. The observer prompt evaluation is about 0.13 s and is negligible. |
| Exam starts llama-server without `--timeout` and strips `LLAMA_ARG_*` | Correct. The argv is `llama_server_instance.py` l. 260–263 plus `EXAM_SERVER_ARGS` (`runtime.py` l. 93: `--jinja`, KV q8_0, `-lv 4`), template-repair args and thinking args (`--chat-template-kwargs`, `--reasoning-budget`). There is no `--timeout`/`-to` anywhere in `r1/`. The env strip is at l. 265–275 (`STRIPPED_ENV_PREFIX = 'LLAMA_ARG_'`, l. 69). `-np 1`, and roots run one at a time per server, so an observer request never waits in a slot queue. |
| `620d222` default 3,600 s, `common.h` l. 632–633 | Confirmed from source. |
| Worst case 20 observer calls × 180 s = 1 h per root | Correct. The harness calls the observer only when `worker_runs` advanced (`campaign.py` l. 1694), and `max_worker_runs = W = 20`, so there are at most 20 calls. The 12 h deadline is polled by `runtime.py` l. 859 during the observer wait, so it is not bypassed. Worst case at 33 tokens/s: 60 proposer calls at the 16k cap (about 8.3 h) plus 20 × 124 s (about 0.7 h) is still under 12 h. |
| A truncated or unparseable observer answer is `query_failed`, not a STOP | Correct. `observe()` returns `query_failed` when `parse_typed_answer` raises (l. 214–218). A truncated reply still has `choices[0].message.content` (string, `""`, or `None`, which `str()` turns into `'None'`), so it reaches the parser and does not raise in `_request`. |
| "Observer answers are not decision input" | Correct for the ranking (`mu_hat`, finalists). They do feed the descriptive A4 fields (`a4_log_score`, `a4_brier`, `forecast_summary`; `analyze.py` l. 182–192, 219–227). Under v2 those use thinking-off rows only, where observer calls take under 1 s (N4). |

## 3. Tests

- The unit test pins the value sent to `urlopen` (180.0) and fails on the old code.
- The script-consistency test pins `b1_completion_usage.OBSERVER_TIMEOUT_S == observer.OBSERVER_TIMEOUT_S`.
- The integration test uses the pinned harness and a loopback fake. It shows:
  - the threshold is the module constant;
  - a timeout still ends as `observer_stop`, with the journal kept and no manifest;
  - a faster answer completes.
- Margins: 0.3 s vs 1 s, and 2.5 s vs 1 s. It was stable under 2x CPU oversubscription.
- Minor: the `complete` branch asserts only "no stop row". It would be slightly stronger to assert `response_complete` rows for every `request_attempt`. Optional.

## 4. Re-pin

- `exam_b1_v2.json` `paper_commit` = `239dcd761d6640dde0bb82211456149cfbadbb41` (full SHA of the code commit). `git diff 7912b7ff 4de28e30 -- r1/scripts/configs/` is that one line only.
- `git diff --name-only 239dcd76 4de28e30 -- r1/exam r1/scripts/exam_runner.py r1/scripts/llama_server_instance.py r1/scripts/llamacpp_probe.py r1/headroom/e1b_collect.py` is empty.
- `git diff --name-only 02a91494 239dcd76 -- <same paths>` is `r1/exam/observer.py` only.
- This matches what `runtime.py` l. 570–571 checks: `paper_commit` must be an ancestor of HEAD, with no protected-path diff to HEAD.
- `7912b7ff` vs `999759b7` differs only in `docs/r1/authorizations/trackx_b1_20261105.md`, as the note says.

## 5. Standby status and delivery checklist

- **Inert unless delivered.** Yes.
  - The PLAN row is marked DRAFT/standby.
  - No code reads it: `_x5_author_row` matches only `R1-EXAM-RULE-X5V2`, and `author_gate`'s fallback looks for `R1-EXAM-RULE`.
  - The row is a well-formed two-cell table row.
  - `_d` runs from `7912b7ff` with `02a91494` and 60 s, and `gh/ops-b1-restart-d-20261113` is still at `7912b7ff`.
- **Standing rules.** New run ID and output tree, `_d`/`_c`/`_b`/6835 untouched, marker retired with the receipt in the `_e` handover directory, and its own review are all present.
  - "Retire into `~/r1_locks/_to_delete/`, nothing deleted" is not stated in the note. It is stated in the D hand-off template it points to (`B1_RESTART_HANDOFF_D_20261113.md` l. 59–62). See S4.
- **Condition for "this STOP is M15".** Mostly right, but too loose and partly mis-specified. See S2.
- **Base/rebase.** The intent is sound, but the verification command is wrong as written. See S3.

## 6. Safety and misleading wording

- **Evidence chain.** Journal rows, `request_evidence` and `validate_observer_journal` carry no timing, so nothing in the evidence format changes.
- **Reuse.** No `_d` root can contain an observer answer over 60 s (one would have been a STOP), so a reuse assessment is not affected by the threshold. The note says this correctly (§5.6).
- **Other timeouts.**
  - Watchdog `/health` (2 s × 3) already tolerates 44 s observer calls and multi-minute proposer calls.
  - llama-server's 3,600 s is not binding.
  - The 12 h deadline is covered above.
- **Appendix wording.** Too thin compared with the earlier disclosure rows. See N5.

## Findings

### Blocking

None.

### Should-fix

**S1. Stale "60 s" labels in `r1/scripts/b1_completion_usage.py` make the report contradict itself.**
- l. 219, table header: `observer reply tokens at 60 s`. The column now holds `OBSERVER_TIMEOUT_S * rate` = 180 s. The line just above (l. 218) prints "observer timeout 180 s".
- l. 20 (docstring): "reaches the observer's 60 s timeout".
- l. 148 (comment): "would reach its 60 s timeout".

*Fix:* header `f'… | observer reply tokens at {OBSERVER_TIMEOUT_S:.0f} s | …'`, and docstring/comment say "the observer's timeout (`OBSERVER_TIMEOUT_S`)". Optionally assert the header text in `test_table_and_cap_check`. This file is not a protected path, so `paper_commit` 239dcd76 stays valid (`runtime.py` l. 571). Say in the PLAN row whether you keep 239dcd76 or re-pin.

**S2. The M15 identification (standby note l. 61–65) is too loose.**
- The condition "a `stop` row whose error is a timeout ('timed out')" also matches a **connect** timeout: `URLError: <urlopen error timed out>`. That is a server not accepting connections, which 180 s does not fix.
- The runner-log string "observer transport or response evidence failure" is shared by every non-HTTP failure: `ConnectionResetError`, `RemoteDisconnected`, `IncompleteRead`, a JSON/`KeyError` on a malformed body. The "not M15" list names only HTTP status, refusal and journal failure.

*Fix:* state the positive condition exactly. All of the following must hold:
- (a) the journal's last rows for the final sequence n are `request_attempt` (n), then `stop` (n), with **no** `response_headers` (n);
- (b) the stop error is exactly `TimeoutError: timed out`, a read timeout while waiting for the reply;
- (c) `runner.log` shows `B1ObserverFatal: STOP: B1 observer evidence failed: STOP: observer transport or response evidence failure: TimeoutError: timed out`.

Then say that anything else is not M15, naming `URLError … timed out` (connect), connection reset or remote disconnect, `IncompleteRead`, a malformed body, any HTTP status, journal failure, and a watchdog STOP. Step 2 could name what to read: the llama-server log (`-lv 4`) for that request, i.e. tokens decoded before the cancel and the timings, and compute the rate from it.

**S3. The base check in step 3 (l. 69–71) cannot pass as written.**
- `git diff --name-only 239dcd76 <base> -- r1/exam …`, with `<base>` = the `_d` run HEAD `7912b7ff`, returns `r1/exam/observer.py`. I ran it. It is never empty, so an operator following it literally will either "fail" the check or improvise.

*Fix:* replace it with the two checks the runner actually implies.
- (i) `git diff --name-only <_d run HEAD> <paper_commit> -- <protected paths>` must be exactly `r1/exam/observer.py`.
- (ii) On the eventual `_e` run checkout, `git merge-base --is-ancestor <paper_commit> <_e run HEAD>`, and `git diff --name-only <paper_commit> <_e run HEAD> -- <protected paths>` must be empty.

Also say that the `_e` HEAD will carry the `_d` STOP report and hand-off docs on top of this branch, which is fine as long as they touch no protected path.

**S4. Spell out the governance points the checklist only implies.**
- (a) Step 4: say "retire with `b1_o2_marker.py retire` (renamed into `~/r1_locks/_to_delete/`; nothing is deleted)" instead of just "retire".
- (b) Neither the PLAN row nor the note records on whose instruction the standby exists, or whether delivery under the §5 conditions needs a further author message. Previous rows do this ("as the author ordered … needs no further author message"). Add one sentence such as "Prepared at the author's request (13 Nov 2026, not quoted); delivered under §5 without a further author message only if all §5 conditions hold, otherwise to the author", or the opposite if that is the author's intent. Do not quote the chat.
- (c) If step 3 forces a rebase, the PLAN row's "Code and re-pin" SHAs and base must be updated when the row is turned into a rule.

### Notes

- **N1.** The "33 tokens/s" is the slowest per-call wall-clock proposer rate (completion tokens / latency, including prompt evaluation). The same `olmo31_32b` server decodes observer answers at 42.7 tokens/s (`timings`). Say "wall-clock proposer rate, conservative". Add the capture's location (`docs/r1/reports/b1_stop_4b31_20261112/root_events.jsonl` @ `3b7d5704`), since it is not in this branch. `olmo31_32b` does not run thinking-on in B1, so it bounds a case (long observer answers) it will not itself produce. That is still a valid conservative floor. Decode speed also drops somewhat as the generation grows toward 4k tokens; the 30 % headroom covers that.
- **N2.** "An answer that arrives within 60 s is recorded exactly as before; only answers that take 60–180 s change" is accurate in practice. Strictly, it is the wait for the response headers (one blocking read), not total time, that is bounded. One clause would make it exact.
- **N3.** "If B2 runs on this commit, it inherits the 180 s" (PLAN row). At this commit B2 cannot reach the observer at all (`authorized_b1_observer` refuses non-B1, `observer.py` l. 52–53; v2 B2 authority is unimplemented, `runtime.py` l. 426). Suggest: "B2 does not use the observer at this commit; B2 code built on it would inherit 180 s unless it changes it."
- **N4.** Long observer answers occur only in thinking-on mode. Under `x5_rule_v2`, the A4 summary fields use thinking-off rows only. So the change can alter `forecast_query_failed` counts but not the reported A4 log score or Brier score in practice.
- **N5.** The appendix sentence should match the disclosure style of the earlier rows: post-hoc engineering change, after run `<id>` stopped at it with N completed roots, before any candidate result was used; a timeout is still a STOP; observer answers enter only the descriptive A4 summary, not the ranking.
- **N6.** Commit hygiene is fine. All four commits are by `Dowling Wong <wangdowling@gmail.com>` as author and committer, with the `Co-Authored-By: Claude Opus 5.5` and `Claude-Session` trailers. Each commit touches only what its message says. The new docs do not quote the author's chat; the one quoted sentence is a proposed appendix line.

## Summary

The code change is correct and minimal, the tests are meaningful and not flaky, and the re-pin is right. The factual basis for 180 s checks out against the repo and the llama.cpp `620d222` sources. Changes are requested for documentation and operator-facing items only:
- S1: a self-contradictory table header in the usage script;
- S2: an M15 identification that would also accept a connect timeout;
- S3: a base-check command in the delivery checklist that can never be empty;
- S4: unstated retirement-into-`_to_delete/` and delivery-authority wording.

None of these needs a protected-path change. S1 touches only a non-protected script.

Verdict: changes requested

---

# Review: B1 observer timeout 60 s -> 180 s, standby (round 2)

Reviewer: independent (Claude subagent). I did not write this change.

## Unit

- Branch `mac-b1-obs180-20261113`.
- Tip `dd0aa0da316aeb1cbd0e1d41aa4b9be018ae1256`: one commit on top of the round-1 tip `4de28e30`.
- Base: `7912b7ff` (`_d` run HEAD).
- Round-1 review: `REVIEW_B1_OBS180_round1.md`.
- I did not modify `/tmp/pb/wt/obs` (it is clean, HEAD `dd0aa0da`). I removed my scratch worktrees under `/tmp/rev_obs2/`.

## What I ran

| Check | Result |
|---|---|
| Full suite at tip (`/tmp/trackg_venv`, author's env, `-k "exam or b1" r1/tests`) | **763 passed / 18 failed / 0 skipped** |
| Same at base `7912b7ff` | 758 / 18 / 0. The sorted FAILED-ID lists are identical. The +5 since base are the four round-1 tests plus `test_report_header_names_the_observer_timeout`. |
| `/tmp/hostver_venv`: `test_exam_observer.py`, `test_exam_b1_observer_integration.py`, `test_b1_completion_usage.py` | 20 passed |
| Mutation: tip tests run against the round-1 `b1_completion_usage.py` | `test_report_header_names_the_observer_timeout` fails. The new test detects the S1 regression. |
| Protected paths | `git diff --name-only 239dcd76 dd0aa0da -- r1/exam r1/scripts/exam_runner.py r1/scripts/llama_server_instance.py r1/scripts/llamacpp_probe.py r1/headroom/e1b_collect.py` is empty. `239dcd76` is an ancestor of the tip. `paper_commit` is still `239dcd761d6640dde0bb82211456149cfbadbb41`, and the config is unchanged since round 1. `git diff --name-only 7912b7ff 239dcd76 -- <protected>` is exactly `r1/exam/observer.py`, so the new step-3 check passes for this branch as written. |
| Commit `dd0aa0da` | Touches only `docs/r1/PLAN.md` (that one row), the standby note, `r1/scripts/b1_completion_usage.py` (not protected) and `r1/tests/test_b1_completion_usage.py`. Author and committer are `Dowling Wong <wangdowling@gmail.com>`. The `Co-Authored-By` and `Claude-Session` trailers are present. The PLAN row is still a well-formed two-cell row. |

## Round-1 findings

- **S1: resolved.**
  - The docstring, the comment and the table header now name `OBSERVER_TIMEOUT_S`.
  - The header prints `observer reply tokens at 180 s`, which matches the line above it.
  - The only remaining "60 s" is the historical `was 60 s` comment on l. 42, which is correct.
  - The new test asserts the header text and that `at 60 s` is absent.
- **S2: resolved.** The M15 criteria are now conjunctive and exact:
  - the last request's rows are `request_attempt`, then `stop`, with no `response_headers`;
  - the error is exactly `TimeoutError: timed out`;
  - the runner log shows the full `B1ObserverFatal` message.
  - The message matches `observer.py` l. 194 and l. 241 at the tip. The coordinator's message said l. 197, but the note cites no line numbers, so nothing needs changing.
  - The not-M15 list now covers HTTP status, connect timeout (`URLError … timed out`), refusal or reset, a timeout after headers, `IncompleteRead` or a malformed body, journal failure, and watchdog or deadline STOPs.
  - These match the code paths in `_request` and the round-1 driver capture (`TimeoutError: timed out` raised before any header).
- **S3: resolved.**
  - Check (i): `diff <_d HEAD> <paper_commit>` on protected paths must be exactly `observer.py`. I verified it holds here.
  - Check (ii): on the `_e` checkout, `paper_commit` must be an ancestor of HEAD and the protected diff to HEAD must be empty. This is what `runtime.py` l. 570–571 enforces.
  - The protected paths are listed once and match the runner.
- **S4: resolved.**
  - Marker retirement now goes through `b1_o2_marker.py retire` into `~/r1_locks/_to_delete/`, with nothing deleted. The receipt goes in the `_e` handover directory and names the `_d` creation receipt.
  - "Who decided" is paraphrased, not quoted. It says delivery under §5 needs no further author message, while the `_e` restart keeps its own hand-off, exact-HEAD review and author gate. A failed check goes to the author.
  - On rebase, the hashes are updated in both the note and the PLAN row.
- **N1–N5: addressed.**
  - Rate provenance is given (@ `3b7d5704`, not on this branch). The note says the rate is wall-clock and conservative and cites the 42.7 tokens/s decode figure. It also says `olmo31_32b` acts only as a floor.
  - The wording is now "response headers within 60 s".
  - The A4 point is stated precisely: not ranking input; only the descriptive summary, thinking-off rows under v2.
  - B1-only scope, with correct citations (`observer.py` l. 52–53, `runtime.py` l. 425–426), and corrected B2 wording.
  - The appendix text follows the earlier disclosure style: post-hoc; run id and N roots; before any candidate result; timeout still a STOP; A4 summary only.

I re-checked the factual claims added in this round against what I verified in round 1: per-operation socket timeout, one slot so no queueing, the `620d222` non-stream behaviour, W = 20 bounding observer calls, 33.3–37.4 tokens/s per call and 42.7 tokens/s decode. All hold.

## New findings

### Blocking

None.

### Should-fix

None.

### Notes (no action required)

- **R2-N1.** The exact string `TimeoutError: timed out` assumes Python ≥ 3.10, where `socket.timeout` is `TimeoutError`. On an older interpreter the name would be `timeout`. The check would then fail closed (not M15, so it goes to the author), which is the safe direction. If wanted, step 1 could name the host interpreter version it was derived for.
- **R2-N2.** In `runner.log` the message appears after the traceback's class prefix (`r1.exam.observer.B1ObserverFatal: STOP: …`). "Shows the full message" reads as a substring match, which is correct; an operator should not expect a line-exact match.

## Summary

All round-1 items are resolved. Code, tests and re-pin are unchanged in substance and correct. The delivery checklist is now exact and can be executed as written, and it keeps the standing rules: no deletion, the earlier runs untouched, a new run ID and output tree, the marker retired with a receipt, and a separate review of the `_e` hand-off.

Verdict: accepted
Accepted commit: dd0aa0da316aeb1cbd0e1d41aa4b9be018ae1256

