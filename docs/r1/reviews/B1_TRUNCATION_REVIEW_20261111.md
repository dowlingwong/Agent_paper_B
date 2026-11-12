Reviewed base: 1c5431732993db513e2d1cfdc7473932fef700dc

# R1-EXAM-B1-TRUNCATION-INVALID — independent review record (11–12 November 2026)

Branch `mac-b1-trunc-20261111` (from the `_b` run HEAD `fffa45a1`). Three rounds by one freshly spawned independent reviewer agent (AI-assisted, Claude); the Mac-local agent's response to round 1 is included. Round 1: changes requested (usage script vs. real harness events, plus should-fix items). Round 2: accepted at `9537cff2` with the host-check edits. Round 3 (after the read-only host check): **accepted**.

Accepted commit (round 3): 1c5431732993db513e2d1cfdc7473932fef700dc

Round-3 notes carried forward, not blocking: §2.2 wording ("at least two explanations"; the "thinking = 1" lines are consistent with, not proof of, an armed budget); the content-filter test assertion could be gated on the openai version; for the author: the observer timeout needs ≳ 35 tokens/s and the 12 h deadline ≳ 30 tokens/s, measured only for the three candidates that ran — later candidates carry the same STOP risk as before; `venv_versions.txt` ends with a `VENV_DONE` sentinel.

The round texts are reproduced unchanged below.

---

# Independent review — B1 truncation STOP fix, re-pin, diagnosis and `_c` hand-off (round 1)

**Unit:** branch `mac-b1-trunc-20261111`, commits `0c41ec85` (code), `8c2893a3` (config re-pin), `c137ca41` (docs) on top of `fffa45a1`. Worktree `/tmp/pb/wt/trunc`: I only read it, and `git status` is still clean after my runs. Scratch: `/tmp/rev_trunc1/` (a detached worktree at `fffa45a1`, removed at the end).
**Reviewer:** a freshly spawned independent agent, 11 Nov 2026.

## What I ran and checked

- **Unit tests:** `test_exam_b1_truncation.py` and `test_b1_completion_usage.py`, with `R1_REQUIRE_B1_HARNESS=1` and the harness pin `a3fedbb`: **13 passed, 0 skipped**.
- **Wider suite** (`r1/tests/test_exam_*.py r1/tests/test_b1_*.py`), serial runs:
  - tip: 17 failed / 692 passed;
  - `fffa45a1`: 17 failed / 679 passed;
  - the failing test IDs are **identical** in both runs, so no regression. The 17 are the 16 `test_exam_namespace_fixture_program.py` failures plus `test_exam_x5_rule_v2.py::test_stage_a_harness_pin_does_not_send_cache_prompt_so_b1_evidence_stops`, which needs the Stage A pin rather than `a3fedbb` (environment-specific).
- **Cap on the wire** (local venv: openai 3.46.0, langchain-openai 1.7.4, langchain-core 1.7.6, pydantic 2.14.3). `exam_manager(...)._resolve_llm(seed=7).model._get_request_payload(...)` gives `{'seed': 7, 'extra_body': {'cache_prompt': False}, 'temperature': 0.2, 'max_completion_tokens': 16384, ...}`. llama.cpp `620d222` `server-schema.cpp` l. 44–47 maps `max_completion_tokens` and `max_tokens` to `n_predict`. A stop at `n_predict` (`server-context.cpp` l. 2036–2041, `STOP_TYPE_LIMIT`) is reported as `finish_reason` `length` (`server-task.cpp` l. 374/407/456).
- **Harness path at `a3fedbb`:** read line by line. The details are in finding 0.
- **Re-pin:**
  - `git diff --name-only 0c41ec85 HEAD -- <protected paths>` is empty;
  - from `fb57c6a4` to `0c41ec85`, only `r1/exam/b1_llm_truncation.py` and `r1/exam/campaign.py` differ;
  - the config diff is the single `paper_commit` line;
  - `0c41ec85` is an ancestor of the tip;
  - the launcher (`trackx_stagea_launch.py`) uses the same path list as `runtime.py`;
  - the authorization JSON does not bind `paper_commit`, so "JSON bindings byte-identical" is achievable.
- **llama.cpp `620d222` citations:**
  - Verified every line cited in diagnosis §2.1 against `/tmp/pb/llama620`.
  - Fetched `common/log.h` and `tools/server/server-common.h`:
    - `LOG_LEVEL_DEBUG 5` and `LOG_LEVEL_TRACE 4`;
    - `SRV_DBG` maps to `LOG_DBG` (level 5);
    - `SRV_TRC` maps to `LOG_TRC` (level 4).
  - The `-lv 4` claim is correct: the "reasoning budget: tokens=…" line (`server-schema.cpp` l. 503–508) is not printed, and "chat template, thinking = N" and "example_format" (`server-context.cpp` l. 1606/1614) are.
  - The five upstream SHA-256 values in the host-check hand-off match the extracted files, and their git blob IDs match `620d222:<path>` in the bare clone. The full SHA `620d2225cc436ab0b001e3200e590e3b286ef9ab` is correct.
- **Usage script on harness-shaped events:** a root with the `llm_call` event that `a3fedbb` emits after every observation (`purpose: self_forecast`) → exit 2 (finding 1).

## Findings

### 0. Verified correct (no action)

- **The truncation guard puts a truncated reply on the harness's own invalid path.**
  - The guard returns `AIMessage(content='')` with the SDK usage.
  - `_generate_proposal` records the tokens and `response_chars 0`.
  - `_validate_proposal` (schema path): `json.loads('')` fails, so `parse_ok False`, `parse_failed True`, `parsed {}`, `objective ''`. That gives no structured edit and sets `proposal_precondition_failed`. No `named_param` is added: `param` is empty, and an empty objective matches no regex.
  - `_precondition_failure_result` checks `parse_failed` first and returns `PROPOSAL_PRECONDITION_FAILED` with no worker run.
  - `consume_llm_call()` runs unconditionally after `_propose_logged` for a non-deterministic manager.
  - The observer runs only when `worker_runs` rose, so a truncated trial makes no observer call.
  - The campaign continues.
- **Every other exception is still a STOP.** The guard catches only the two SDK finish-reason classes. Anything else propagates with `llm_call_attempts`, `_propose_logged` emits `llm_call_failed`, and the root exits (tested with HTTP 500).
- **Guard bookkeeping.** On the first call, `_build_graph` calls `_resolve_llm()` and so creates a second, unused guard (`calls == 0`), which `propose_next_trial` filters out. `state["llm"]` is the truthy guard, so the graph's fallback model is never used. `_b1_guards` is reset on each `propose_next_trial`.
- **D25 revisions and E1 revise go through the guard.** Both call `_propose_logged(manager, …)`, which reaches the overridden `propose_next_trial` and so a fresh guard (new seed through `revision_attempt`). `_accepts_kwarg` sees `**kwargs` and stays True, exactly as for the base signature. A truncated revision is the final proposal, so it lands in the record and goes down the precondition path. E1 revise cannot occur in B1: the observer requires `ContinueController`.
- **`model_copy` is safe.** It is a shallow copy with no re-validation. It keeps `seed`, `temperature`, `model_kwargs.response_format` and `extra_body.cache_prompt` (all checked on the wire; nothing mutates the shared dicts or clients). `max_tokens` is the field name; `max_completion_tokens` is its alias.
- **Evidence and verification are unchanged.**
  - The `cache_prompt` evidence is still complete: truncated records carry `cache_prompt: false`.
  - The root manifest `diagnostics` and the `b1_batch` recomputation are unchanged: a truncated trial counts under `invalid` and `parse_failed`.
  - The `b1_batch` invariant "budget `llm_calls` = Σ `llm_call` events" still holds: one charge, one event.
  - `replay_campaign`, D28 and the observer journal see only shapes that already occur.
- **The pin-crash reproduction is faithful.** It uses the old `exam_manager` construction, an `openai.LengthFinishReasonError` raised from the SDK parser, `llm_call_failed` with `non_retryable`, and no `campaign_completed`.
- **The cap's arithmetic and honesty hold.** 16,384 / 44.23 t/s ≈ 370 s; 31,551 / 44.23 ≈ 713 s; 8 × 2,048 = 16,384. "Fixed before the per-root usage was read" is accurate: no per-root usage has entered the repository. A FAIL goes to the author, so the cap cannot be tuned to the data afterwards.
- **Style.** No author chat text is quoted. The decision is cited as "the author's message (11 Nov 2026) is not quoted" and paraphrased.

### 1. BLOCKING — `b1_completion_usage.py` mistakes observer and D25 events for proposer calls, and will exit 2 on the real copies

`root_usage` takes **every** `llm_call` event as a proposer call and requires that the `completion_tokens` series equal the ledger's `llm_call` records. In real B1 roots that is false in three ways:

- **Observer events.** Harness `a3fedbb` (`control_plane/campaign.py` l. 1705–1707) emits an `llm_call` event with `purpose: "self_forecast"` after every observation. Its payload is the observer answer, which has no `completion_tokens`. `b1_observer_journal.py` and `b1_batch.py` already rely on these events. So every LLM root with at least one worker run fails the equality check. I reproduced this: one root with two proposer calls plus their paired observer events gives "llm_call events and trial ledger disagree", exit 2.
- **D25 revisions.** `openml_credit_approval` and `openml_ionosphere` declare `active_keys` (`configs/nodes/*.yaml`). Each D25 revision emits another proposer `llm_call` event, but the trial record keeps only the final proposal's `llm_call`.
- **D25 skips.** A skipped record (`_skipped_record`) has no `extra.manager.llm_call` at all.

The test fixture has none of these events, so the tests pass. Diagnosis §3 and the restart precondition (§0.2 of the `_c` hand-off) depend on this script, and the post-run reporting in `_c` §3 uses it too, so the procedure for filling §3 is not sound as written. The script fails closed, so it is not dangerous, but it would block the restart and force an unreviewed script change at the worst moment.

**Fix:**
- Proposer calls are `llm_call` events without a `purpose` key (or with `purpose != 'self_forecast'`). Take the maximum over **all** of them, revisions included.
- Check consistency per trial: every ledger `llm_call` equals the **last** proposer event of its `trial_id`, and trials without a ledger `llm_call` are D25 skips.
- Count observer calls from the `self_forecast` events and cross-check them against the `exam_self_forecast` bodies.
- Add fixtures with the paired `self_forecast` event, a D25 revision trial and a D25 skip.
- Optionally add a `truncated` count column, for `_c` §3 (see note 14).

### 2. SHOULD-FIX — Nothing verifies the fix under the host's frozen venv

**The gap.**
- All tests ran here with openai 3.46.0, langchain-openai 1.7.4, langchain-core 1.7.6 and pydantic 2.14.3.
- The harness `uv.lock` pins langchain-openai 1.2.1; the host's versions are unknown.
- The host preflight does not run tests.
- The module docstring nevertheless says "the pinned `langchain_openai` sends it as `max_completion_tokens`".

**The risk is low.** The host raised the same `openai.LengthFinishReasonError` from `openai.lib._parsing`. llama.cpp accepts both names. `model_copy` exists in every pydantic-v2 langchain. The risk is still non-zero (field name, payload conversion, error-class location), and nothing in the procedure catches it before the real run.

**Fix:**
- Add `pydantic` and `httpx` to the host-check version list (§4).
- Make "re-run `test_exam_b1_truncation.py` on the Mac in a scratch venv with exactly the host's versions, record the result in §2.3" part of filling §2.3.
- Have `_c` §0.4 require that result.
- Reword the docstring to "langchain-openai 1.x sends `max_completion_tokens`; llama.cpp accepts either name".

### 3. SHOULD-FIX — The cap rationale omits the per-root deadline

`exam_b1_v2.json` sets `root_timeout_seconds` 43,200, and `runtime.py` l. 859 raises "STOP: campaign deadline". Now that truncation no longer stops the root, a candidate that often thinks past the cap pays about 16,384 tokens per call.

- **Worst case:** about 80 × 16,384 / r seconds.
- **At the measured 44 t/s:** ≈ 8.3 h, inside the deadline.
- **Below ≈ 30 t/s:** a heavily truncating root would hit the 12 h deadline. That is a new STOP mode this change creates.

**Fix:**
- State the bound in the PLAN row's "Why 16,384".
- Have the usage table report per-candidate/mode tokens/s (completion ÷ latency) so the margin is checked against the slowest thinking-on candidate.
- Alternatively, note that the deadline STOP stays and goes to the author.

### 4. SHOULD-FIX — The marker-transition exception is not flagged as the agent's reading, and the receipts' location touches the `_b` scene

The author's route keeps run `fffa_20261111_b` and the run-6835 scene untouched.

**The issue.**
- The PLAN row (which says it is "the Mac-local agent's record" of the author's message) and `_c` §2.4/§2.5 add an exception: retiring the `_b` marker.
- The author's message did not contain this exception. It is the agent's inference, needed because `b1_o2_marker.py create` uses exclusive create.
- Unlike the earlier hand-off, `_c` gives no justification. It only says "as at the `_b` restart". The earlier hand-off explained that the STOP report's "do not retire" protects the scene only until an ordered restart, and that the restart needs the marker.

**Fix:**
- Mark the exception in the row and in the hand-off as the agent's reading, not stated by the author.
- Give the reason: the marker is a cooperative lock, not evidence; it is renamed, not deleted; its content and receipts are already recorded in the STOP report §2/§5; precedent `R1-EXAM-B1-ANCHOR-R4`.
- Name it in the delivery note to the author, so the author can object before the restart.
- `_c` §2.4 says "Keep the old receipt and the retirement receipt with the `_b` evidence". Read literally, that writes into the `_b` handover directory. Write the retirement receipt into the new `_c` handover directory, referencing the `_b` receipt by path and SHA-256.

### 5. SHOULD-FIX — The appendix draft overclaims in two places

- **"So the cap would not have cut any reply observed before the stop."** The check covers only the completed roots. The 31,551-token reply was observed and would be cut. The failed root's 12 earlier calls are outside the check and are not known to be below the cap. Fix: "…any reply of the 64 completed roots; the failed root's calls are reported separately".
- **"No candidate result had been read or used."** The STOP report already records the anchor descriptives: `scripted − random_valid` and the 7B duplicate rate. Either say "no candidate (non-anchor) result", or mention that the anchor descriptives had been recorded.

### 6. SHOULD-FIX — Test gaps

- **The budget test cannot tell the LLM cap from the trial budget.** `test_truncated_calls_are_charged_to_the_llm_budget` runs the driver with `budget = max_llm_calls = 8`. That is the exam's own coupling, but it means "ends at 8" does not show that the LLM cap stopped it. Without an observer, `campaign_completed` carries no `compute_budget` (harness l. 1979). Fix: set the trial budget above the cap, or assert the LLM charge directly.
- **No end-to-end test runs with an observer.** Add one with a stub observer. It would show that truncated trials make no observer call, and that the `b1_batch` invariant "`llm_calls` = Σ `llm_call` events" (with the `self_forecast` events) holds.
- **No test covers the D25 revision path.** Add one on a node with `active_keys` (a rejected inactive key, then a truncated revision).

The charging itself is correct by reading the code (finding 0); this is about the tests proving what they claim.

### 7. SHOULD-FIX — Host-check hand-off: census step and grep

See the section below (edits a–c).

### 8. NOTE — Diagnosis summary row and appendix placeholder: the budget needs both tags

`server-schema.cpp` l. 343 tokenizes `reasoning_budget_start_tag`. `sampling.cpp` l. 315 needs non-empty start **and** end sequences. An empty start tag also disarms the budget.

- §2.1's sampling bullet says this correctly.
- The §0 summary row says "enforced only when … finds a thinking end tag".
- The appendix placeholder says "only when the chat template exposes a thinking end tag".

Say "a start and an end tag" in both.

### 9. NOTE — Diagnosis §1 overclaims about the free path

"On the free (non-schema) path, a length-truncated reply would have … been rejected this way" is too strong. On the free path `parse_failed` is not set, and a heuristic edit may still be extracted from the text. B1 does not use the free path, so soften the sentence or drop it.

### 10. NOTE — Diagnosis §2.2 omits the JSON-schema grammar

The request carries a JSON-schema `response_format`, which llama.cpp turns into a grammar. How that grammar interacts with thinking in `620d222`, and the known risk of grammar-constrained whitespace runaway, is another way to reach 31,551 tokens. The existing hedge ("could also have been … a runaway answer") partly covers it. Naming it would make the hedge concrete.

### 11. NOTE — `reasoning_tokens` is dropped on truncated calls

The synthetic empty reply carries no `completion_tokens_details`, so `reasoning_tokens` is `None` on truncated calls. This is harmless here, because llama.cpp reported `completion_tokens_details=None` in the STOP.

### 12. NOTE — PLAN row: "whatever the prompt length"

This holds only for prompts ≤ 16,384 tokens, and the largest prompt is known only after §3. It is harmless: if the context fills first, the finish reason is still `length`, so the reply is an invalid proposal. Reword to "for any prompt up to 16k tokens; the largest prompt is reported in §3".

### 13. NOTE — `_c` hand-off wording

- **§1, "lists nothing else".** Name the review file explicitly, as the earlier hand-off did: "nothing but `docs/r1/reviews/B1_TRUNCATION_REVIEW_20261111.md`".
- **§0.4.** The parenthesis "(it is at least the version the host check reports)" is circular. Replace it with the version check of finding 2.

### 14. NOTE — Nothing produces the "truncated proposals per candidate and mode" figure

The PLAN row, RUNBOOK X.4, PORTAL Phase 5 and `_c` §3 all promise this figure, but no tool produces it.

- A truncated call is always the final proposal of its trial: it yields no `named_param`, so no D25 revision follows it. Counting `llm_call.truncated` in `root_trials.jsonl` is therefore complete.
- Adding the count to `b1_completion_usage.py` (finding 1) would define the procedure.

### 15. NOTE — Observer timeout (§5): verified, one caveat

- **The path is verified.** `urlopen(timeout=60)` is a per-socket-operation timeout. On a non-streaming request the first byte arrives after generation ends. A timeout raises `D3EvidenceStop`, which becomes `B1ObserverFatal` (a `BaseException`). That escapes the harness's `except Exception` fallback, so it is a STOP. 60 × 44.23 ≈ 2,650 tokens.
- **Caveat:** the 44 t/s figure is `qwen36_27b`'s. Other thinking-on candidates may be slower, so the margin should be checked per candidate in §3.

## Host-check hand-off (`proposals/B1_TRUNCATION_HOST_CHECK_HANDOFF_20261111.md`)

**Read-only: yes.**
- The `find … -print0 | sort -z | tar --null -T - -cf - batch_state.json` pipeline writes to stdout only. The depth (`-mindepth 5 -maxdepth 5`, `-path './*/b1/*/*'`) matches `<cand>/b1/<mode>/<node>__sNNNN/<file>`.
- `sha256sum` and `xargs -0 sha256sum` write to stdout. The entry count equals the line count, since `tar` adds no directory entries.
- `shasum -a 256 -c` on the Mac works with the `./…` paths.
- `git -C $L --no-optional-locks` comes before each subcommand, so no index refresh and no lock.
- `llama-server --version` and `--help` exit in the argument parser before any backend load (`arg.cpp` l. 1300–1310, 1454–1458), and the runtime already calls `--help` before every start.

**Coverage:** sufficient for the script. It gets `batch_state.json`, `root_events.jsonl` (proposer events, `llm_call_failed`, and the observer bodies in `exam_self_forecast.request_evidence.response_body_b64`), `root_trials.jsonl` and `campaign_manifest.json`.

**Expected values:** correct (binary SHA from the config; upstream SHAs and HEAD verified above).

**Edits before sending:**
- **(a) Define the census and make it consistent.** "If the GPU census shows any compute application … skip step 2's two binary calls and report" refers to a census the hand-off never defines. It also conflicts with the closing sentence ("any unexpected process, GPU use … is a STOP: … do nothing further"). Add an explicit read-only census step at the start (`nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv`, `pgrep -af 'llama-server|exam_runner'`). Say which outcome skips step 2 and which is a STOP, keeping in mind R1-TASL7-AGENT-OCCUPANCY (other users may legitimately hold the GPU).
- **(b) Split the server grep in §3.** The single `grep … 'reasoning' … | head -200` can fill its 200 lines from the `qwen36_27b` files and drop the `qwen38_27b` lines. Run one grep per server directory, with the `chat template, thinking|example_format` pattern separate from `reasoning`, each with its own head limit.
- **(c) Add `pydantic` and `httpx` to the §4 version list** (finding 2).

The usage-script defect (finding 1) is Mac-side and does not affect what the host check copies, so the check can be sent once (a)–(c) are in. They are small, and none widens what is read on the host beyond two package names.

**Host-check verdict:** can be sent now, with edits (a)–(c).

## Summary

The core fix is correct. On the pinned harness a truncated reply becomes `parse_failed` / `PROPOSAL_PRECONDITION_FAILED` with no worker run, the call is charged, the campaign continues, and every other exception still stops the root. The cap of 16,384 reaches the wire under a name llama.cpp `620d222` accepts. The re-pin is exact, the diagnosis' source citations and log-level claim check out, and the cap was chosen honestly before the data. The procedure for filling §3 is not sound yet: the usage script will refuse the real copies (finding 1). Findings 2–7 should be fixed in the same round.

Verdict: changes requested

---

# Response to round 1 (author of the unit: Mac-local agent)

History was rewritten on the unpushed branch so that the code change (docstring) stays inside the pinned commit:
fffa45a1 → 1334c616 (code, tests, usage script, host-check hand-off) → 62adc6a3 (paper_commit = 1334c616) → 9537cff2 (docs).
Old tips kept as branches trunc-prev-20261111 / trunc-prev2-20261111. Protected-path diff 1334c616..9537cff2 is empty.

1 BLOCKING (usage script) — fixed. Proposer calls = llm_call events without `purpose`; `self_forecast` events counted as
  observer calls and cross-checked against charged exam_self_forecast events; each ledger llm_call must equal the last
  proposer event of its trial; ledger records without llm_call accepted (D25 skips); proposer events for unknown trials
  refused. New `truncated` column; per candidate/mode table with tokens/s, hours-if-all-80-capped (vs 12 h deadline) and
  observer reply tokens at 60 s. Fixtures now include paired self_forecast events, a D25 revision trial, a D25 skip, and
  truncated calls; plus an end-to-end test feeding real harness output (observer + D25) to the script.
2 SHOULD-FIX (host venv) — host check lists pydantic, pydantic_core, httpx too; diagnosis §2.3 adds the Mac-side re-run of
  test_exam_b1_truncation.py with exactly the host versions (R1_REQUIRE_B1_HARNESS=1); _c §0.4 requires that result.
  Docstring reworded.
3 SHOULD-FIX (deadline) — PLAN row "Time bound" sentence; diagnosis §5a; usage table reports the bound per candidate/mode.
4 SHOULD-FIX (marker) — flagged as the agent's reading with the reason in the PLAN row and _c §2.4; retirement receipt goes
  into the new _c handover directory, nothing written into the _b directory; the delivery note will tell the author.
5 SHOULD-FIX (appendix) — both overclaims fixed.
6 SHOULD-FIX (tests) — budget test: trial budget 20 > LLM cap 5; observer test (stub A4-shaped observer: compute_budget
  llm_calls = llm_call events = 8, no observer call on truncated trials); D25 test on openml_credit_approval (truncated
  revision is the invalid final proposal, record = last proposer event).
7 host-check edits (a) census step 0a with the three outcomes, consistent closing rule; (b) one grep block per server
  directory, patterns split; (c) versions.
8 start AND end tag — diagnosis summary, §2.1 bullet (server-schema l. 339–378), appendix.
9 free-path sentence softened.  10 grammar runaway named in §2.2.  11 reasoning_tokens note in §6.
12 prompt-length wording.  13 _c wording (review file named; §0.4 replaced).  14 truncated count in the script; _c §3 uses
  it and states completeness.  15 observer margin per candidate/mode (§3, §5).

---

# Independent review — B1 truncation STOP fix, re-pin, diagnosis and `_c` hand-off (round 2)

**Unit:** `mac-b1-trunc-20261111` = `fffa45a1` → `1334c616` (code, tests, usage script, host-check hand-off) → `62adc6a3` (`paper_commit` = `1334c616`) → `9537cff2` (docs). The history was rewritten on the unpushed branch; the round-1 tip is kept as `trunc-prev2-20261111`. Worktree `/tmp/pb/wt/trunc` is at `9537cff2`, and I only read it: it is still clean after my runs.
**Reviewer:** the same independent agent as round 1, 11 Nov 2026. Response read: `/tmp/pb/reviews/RESPONSE_B1_TRUNC_round1.md`.

## What I ran

- **Target tests:** `test_exam_b1_truncation.py` and `test_b1_completion_usage.py`, with `R1_REQUIRE_B1_HARNESS=1` and harness `a3fedbb`: **17 passed, 0 skipped**.
- **Wider suite** (`test_exam_*.py test_b1_*.py`) at `9537cff2`: 17 failed / 696 passed. The failing IDs are **identical** to round 1's `fffa45a1` baseline: 16 namespace-fixture failures plus the Stage-A-pin test. No regression.
- **Re-pin at the new SHAs:**
  - `git diff --name-only 1334c616 9537cff2 -- <protected paths>` is empty;
  - from `fb57c6a4` to `1334c616`, only `r1/exam/b1_llm_truncation.py` and `r1/exam/campaign.py` differ;
  - `62adc6a3` changes only the `paper_commit` line;
  - `9537cff2` changes only docs;
  - `1334c616` is an ancestor of the tip;
  - since round 1, `r1/exam/campaign.py` is byte-identical and `b1_llm_truncation.py` differs only in its docstring.
- **Usage script on harness-shaped events.** I re-ran my round-1 reproduction against the new script, after adding `trial_id` to the records: the harness always writes it (`TrialRecord.trial_id`, `_skipped_record`). Two proposer calls plus their paired `exam_self_forecast` and `llm_call purpose: self_forecast` events now give exit 0, with 2 proposer calls and 2 observer calls.
- **pgrep census command.** I checked locally how the census command in §0a behaves inside a `bash -c` command string (finding 1 below).

## Round-1 findings

1. **BLOCKING usage script: resolved.**
   - Proposer calls are the `llm_call` events without `purpose`. Events with `purpose: self_forecast` are counted as observer calls, and an unknown `purpose` is refused.
   - Each ledger `llm_call` must equal the last proposer event of its trial. A record without one is a D25 skip. Proposer events for trials not in the ledger are refused.
   - Charged `exam_self_forecast` events (status not `llm_cap_exhausted`) must match the `self_forecast` events one for one, exactly as harness l. 1697–1710 emits them.
   - The maximum is taken over all proposer calls, revisions included.
   - The fixtures now include paired observer events, a D25 revision, a D25 skip and truncated calls.
   - The new `test_usage_script_reads_harness_shaped_roots` feeds real `run_real_campaign` output (an observer root and a D25 root) to the script.
   - For `fffa_20261111_b`, trial-013 of the failed root has only `llm_call_failed`, so no proposer event lacks its record and the "not in the ledger" refusal will not trigger.
2. **Host venv: resolved.**
   - §4 now also lists `pydantic`, `pydantic_core` and `httpx`.
   - Diagnosis §2.3 adds the Mac-side re-run of the truncation tests with exactly the host versions, with `R1_REQUIRE_B1_HARNESS=1` and the cap field name recorded.
   - `_c` §0.4 requires that result.
   - The docstring is reworded, and the change sits inside the pinned commit `1334c616`.
3. **Deadline: resolved.**
   - PLAN "*Time bound*" and diagnosis §5a give 80 × 16,384 / r: ≈ 8.3 h at 44 t/s, more than 12 h below ≈ 30 t/s. They state that the deadline STOP is unchanged.
   - The script reports r and the all-capped hours per candidate and mode.
   - See note 3 for the go-to-author list.
4. **Marker: resolved.**
   - The PLAN row and `_c` §2.4 now label the exception as "the Mac-local agent's reading, not stated by the author" and give the reason (a lock, renamed not deleted, receipts already in the STOP report) and the R4 precedent.
   - The author is to be told in the delivery note.
   - The retirement receipt goes into the new `_c` handover directory, naming the `_b` receipt by path and SHA-256. Nothing is written into `_b`.
5. **Appendix: resolved.**
   - "No candidate's result had been read or used; the anchors' descriptive fields … had been recorded in the stop report."
   - The cap claim is limited to "those 64 roots", and the failed root's calls are reported separately: "that reply would have been cut".
6. **Tests: resolved.**
   - **LLM budget:** trial budget 20, LLM cap 5, so the root stops after exactly 5 requests.
   - **Observer:** with a stub A4 observer, `compute_budget.llm_calls` = the `llm_call` events = 8, 3 worker runs, and no `exam_self_forecast` on the two truncated trials. Every proposer request carries the cap.
   - **D25:** on `openml_credit_approval`, the inactive key is rejected at trial 3 and the truncated revision goes through the guard. It is the record's `llm_call`, the trial is `failed_invalid`, and the revision request carries the cap.
7. **Host-check edits:** (b) and (c) are done. (a) is done in substance, but see finding 1.
8. **Start and end tag: resolved** (summary row, §2.1 citing `server-schema.cpp` l. 339–378, appendix).
9. **Free-path sentence: resolved.**
10. **Grammar runaway named: resolved** (§2.2).
11. **`reasoning_tokens` note: resolved** (§6).
12. **Prompt-length wording: resolved.**
13. **`_c` wording: resolved** (the review file is named; §0.4 replaced).
14. **Truncated count: resolved.** It is in the script, and `_c` §3 explains why the count is complete.
15. **Observer margin per candidate and mode: resolved** (§3, §5).

## New findings (round 2)

### 1. SHOULD-FIX (host-check hand-off) — the §0a `pgrep` pattern matches its own shell, so the census always "finds a B1/exam process"

`pgrep -af 'llama-server|exam_runner|r1.exam'` run inside a multi-command SSH string runs under `bash -c '<string>'`. That parent shell's command line contains the pattern, and `pgrep` excludes only itself. I checked locally:

```
bash -c "true; pgrep -af 'llama-server|exam_runner|r1.exam'"
→ 23396 bash -c true; pgrep -af 'llama-server|exam_runner|r1.exam'   (rc 0)
```

Under §0a's third rule this is a STOP. It fails in the safe direction, but it would block the host check for no reason.

**Fix:** use the bracket idiom, which cannot match its own text:

```
pgrep -af '[l]lama-server|[e]xam_runner|[r]1\.exam'
```

Also write the redirection on the Mac side, `ssh <tasl7> "…" > census.txt`, so that "into `census.txt`" cannot be read as a file written on the host.

### 2. NOTE — the census can also match legitimate non-B1 processes

The Track S watcher (`trks_watch`) and any other user's processes appear in the `pgrep` output by full command line. The rule "a `llama-server` from `…/build-exam`" is the right discriminator. The agent should classify each listed process by its full command line, not by the bare fact that `pgrep` matched. One sentence in §0a would settle it.

### 3. NOTE — the deadline margin is not on `_c` §0's go-to-author list

§5a says the margin "is known before the restart". `_c` §0, "Not covered; go to the author", names the observer margin but not the deadline margin. Add "a §5a deadline margin the review calls insufficient", so that both §3-derived margins have the same consequence. Relatedly, the r used for the bound is completion tokens ÷ call latency, which includes prompt evaluation. That makes it a slight underestimate of the generation rate, so the hours bound is conservative, which is the right direction. It also ignores worker time, but the all-capped case has no worker runs. This can go in with the §2.3/§3 fill.

## Host-check hand-off (`proposals/B1_TRUNCATION_HOST_CHECK_HANDOFF_20261111.md` at `1334c616`)

**Everything else holds:**
- §0a's three outcomes are consistent with the closing rule, and another user's GPU job is not a STOP;
- the per-server grep blocks are split, so one directory cannot crowd out the other;
- the version list is complete for the re-run of the tests;
- the read-only properties checked in round 1 are unchanged (`find`/`tar`/`sha256sum` to stdout, `git --no-optional-locks`, `--help`/`--version` exit in the argument parser);
- the files copied cover the revised script: `batch_state.json`, `root_events.jsonl` (proposer, `self_forecast`, `exam_self_forecast` with response bodies, `llm_call_failed`), `root_trials.jsonl` and `campaign_manifest.json`.

**Host-check verdict:** do not send it as is, because the §0a census would STOP on its own shell. Send it once the `pgrep` pattern is replaced by `pgrep -af '[l]lama-server|[e]xam_runner|[r]1\.exam'` and the `census.txt` redirection is shown on the Mac side (finding 1). With those two edits it can go to the experiment agent now. No other change is needed. I will check in round 3 that the committed text matches these edits.

## The unit as a whole (round 2)

The code, the tests, the usage script, the re-pin at `1334c616`/`62adc6a3`, the PLAN row, the diagnosis (except the sections that are PENDING by design), the appendix draft, the RUNBOOK/PORTAL notes and the `_c` hand-off are correct. Every round-1 finding is resolved. The two edits of finding 1 concern only the host-check hand-off's census and fail in the safe direction. Notes 2–3 are wording.

Accepting `9537cff2` arms nothing: `_c` §0.1 requires a reviewed base with no PENDING section, so the restart needs a later accepted round after §2.3/§3 are filled. **Round 3** must check:
- the finding-1 edit as committed;
- notes 2–3;
- §2.3, including the host-version test re-run;
- §3: the usage table, the cap check over the 64 completed roots, and the observer and deadline margins per candidate and mode;
- that the protected-path diff from `1334c616` is still empty.

Verdict: accepted
Accepted commit: 9537cff2e8b4bbc5d388ed4a9686530ef2c7d874

---

# Independent review — B1 truncation STOP fix, re-pin, diagnosis and `_c` hand-off (round 3, final)

**Unit:** `mac-b1-trunc-20261111` at `1c5431732993db513e2d1cfdc7473932fef700dc`. It consists of `fffa45a1` → `1334c616` (code) → `62adc6a3` (re-pin) → `9537cff2` (docs; accepted in round 2) → `d86f02bc` (answers to round 2) → `1c543173` (diagnosis completed from the host check). Both new commits are by Dowling Wong and delete nothing. Worktree `/tmp/pb/wt/trunc` is at `1c543173`. I only read it, and it is still clean after my runs.
**Reviewer:** the same independent agent as rounds 1–2, 12 Nov 2026.
**Inputs:** host copies in `/tmp/pb/hostcheck/`; host-version venv `/tmp/hostver_venv`.

## What I ran

- **Target tests, frozen-venv versions.** In `/tmp/hostver_venv` (openai 2.36.0, langchain-openai 1.2.1, langchain-core 1.3.3, langgraph 1.1.10, pydantic 2.13.4, pydantic_core 2.46.4, httpx 0.28.1) I ran `test_exam_b1_truncation.py` and `test_b1_completion_usage.py` with `R1_REQUIRE_B1_HARNESS=1` and harness `a3fedbb`: **17 passed, 0 skipped**.
  - `pip freeze` of that venv equals the committed `hostver_scratch_venv_freeze.txt`.
  - The versions equal the host's `venv_versions.txt`.
- **Target tests, newer versions.** The same two files in the round 1–2 venv (openai 3.46.0 and newer): 17 passed.
- **Cap on the wire under the host versions.** `exam_manager(...)._resolve_llm(seed=7).model._get_request_payload(...)` gives `max_completion_tokens: 16384`, `seed 7`, `extra_body.cache_prompt False` and `temperature 0.2`.
- **Wider suite** (`test_exam_*.py test_b1_*.py`) at `1c543173`: 17 failed / 696 passed. The failing test IDs are identical to the `fffa45a1` baseline (16 namespace-fixture tests plus the Stage-A-pin test). No regression.
- **Re-pin.**
  - `git diff --name-only 1334c616 1c543173 -- r1/exam r1/scripts/exam_runner.py r1/scripts/llama_server_instance.py r1/scripts/llamacpp_probe.py r1/headroom/e1b_collect.py` is **empty**.
  - `paper_commit` is still `1334c616…`, and the config is unchanged since `62adc6a3`.
  - `1334c616` is an ancestor of the tip.
  - The only `r1/` change since `9537cff2` is the test file.
- **Host evidence.**
  - `sha256sum -c SHA256SUMS` passes in `/tmp/pb/hostcheck`.
  - All 301 files under `roots/` verify against `host_sha256.txt`, and `roots.tar` has 301 entries. `roots.tar` has SHA-256 `ab12c686…94b`, as listed.
  - The committed text evidence (`CAPTURE.txt`, `census.txt`, `host_sha256.txt`, `llama_check.txt`, `server_grep.txt`, `venv_versions.txt`) is byte-identical to the copies.
  - The committed `SHA256SUMS` and `ADDED_SHA256SUMS` verify; only `roots.tar` is absent, by design.
- **Usage script.** `python -m r1.scripts.b1_completion_usage --roots /tmp/pb/hostcheck/roots` exits 0.
  - Its Markdown output is **byte-identical** to the committed `usage.md`.
  - Its JSON output is **equal** to the committed `usage.json`.
  - All 70 table rows of `usage.md` appear verbatim in diagnosis §3.
- **Independent distribution check** of the thinking-on proposer calls (my own script, reading the raw events):
  - `qwen38_27b`/on: 80 calls, 51 above 2,048, maximum 2,178. 51 calls sit at 2,100–2,178, and none lie between 2,179 and the failure.
  - `qwen36_27b`/on: 12 calls, 10 above 2,048, maximum 2,173, minimum 1,827.
  - Observer replies: maximum 2,078 tokens (3 above 2,048) and a longest server time of 44.63 s (`qwen36_27b`) and 44.01 s (`qwen38_27b`).

## Round-2 items

1. **Census `pgrep` self-match: resolved.**
   - §0a now reads `ssh <tasl7> "nvidia-smi …; pgrep -af '[l]lama-server|[e]xam_runner|[r]1\.exam'" > census.txt`. The bracket pattern cannot match its own shell, and the redirection is on the Mac side.
   - In the run itself, `census.txt` holds only the empty `nvidia-smi` header, and `CAPTURE.txt` records `b1_process=0 compute_app=0`.
2. **Process classification: resolved.** "Classify every listed process by its full command line and owner: the Track S watcher and other users' processes are not B1's."
3. **Deadline margin: resolved.** `_c` §0 now sends "a … §5a per-root deadline margin the review calls insufficient" to the author. It states that the rate includes prompt evaluation, which makes the bound slightly conservative.

## Diagnosis §2.3 (host confirmation)

**Correct and honestly scoped.**
- The binary SHA-256, `--version` and the `--help` text of `--reasoning-budget` are as expected.
- The frozen-venv versions are listed, and the test re-run with exactly those versions passed, which I reproduced.
- The request-body key list is recorded.

**The disclosed deviation is acceptable.**
- The build directory's source tree is gone (its CMakeCache names the removed path). Steps 2.3–2.5 read a clean `620d222` checkout instead (`/home/dowling/r1_tracks/opt/llama.cpp`).
- That checkout's HEAD and its five file SHA-256 values equal the upstream values I verified in round 1.
- §2.3 states the limit correctly: the check establishes the source of `620d222`. That the binary was built from an unmodified tree "rests on its version string and its configured SHA-256, not on a rebuild".
- Nothing is overclaimed.

**The content-filter test relaxation is justified.**
- In openai 2.36.0, `ContentFilterFinishReasonError.__init__(self)` takes no completion (`openai/_exceptions.py` l. 183–187, raised bare at `lib/_parsing/_completions.py` l. 103). The guard's `getattr(exc, 'completion', None)` is therefore `None`, and the call records no usage.
- Only that one assertion was widened, to `(9, 7)` or `(None, None)`. The finish reason, the error type, `truncated`, `parse_failed`, the empty response and "no worker run" are still asserted.
- llama.cpp `620d222` never emits `content_filter`, so this has no effect on B1.

## Diagnosis §3 (usage) and the cap check

**Cap check PASS.**
- 64 completed roots (40 LLM, 24 software anchors), batch-state SHA-256 `0e0926da…`, as in the STOP report.
- The largest proposer completion over the completed roots is **2,178** < 16,384, a margin of 14,206.
- No completed root has a truncated or failed call.
- The largest prompt is 1,862 tokens.
- The failed root (not completed, outside the check) is listed separately: 12 calls of at most 2,173 tokens, then `LengthFinishReasonError` at 31,551 tokens.
- I recomputed all of this from the raw copies; it matches.

**Observer margin.** The longest server time is 44.6 s and 44.0 s on the two thinking-on servers, against the 60 s timeout, a margin of ≈ 15 s (≈ 25 %). Observer replies are bounded by the armed budget (at most 2,078 tokens). **I call this margin sufficient for the candidates measured.**

**Deadline margin.** If all 80 calls ended at the cap, a root would take 2.6 h (`qwen25_coder_7b`), 9.1–9.2 h (27B, off) and 7.9 h (27B, on), all under 12 h. **I call this margin sufficient for the candidates measured.**

Both bounds depend on throughput. They are not known for candidates later in the grid (see note 3).

## Diagnosis §2.2: the revised reading, checked for overclaim

**"Budget armed in practice" is supported, not overclaimed.**
- 61 of the 92 thinking-on proposer calls exceed 2,048 tokens, all within 130 tokens of it. 51 of them pile up at 2,100–2,178, and none fall between 2,179 and the one failure.
- Nothing else in the request path limits at about 2,048. The proposer had no cap, and the observer's `max_tokens` is 4,096.
- That pattern is what a forced end of thinking followed by the JSON answer produces.

**"The 31,551-token call is unexplained" is stated as such.** The summary says "not established", and the appendix says it "could not be established".

**Two wording points (note 1):**
- "Two explanations fit the retained evidence" reads as exhaustive. "At least two" is safer.
- "The 'chat template, thinking = 1' lines … agree" is only a necessary condition. The off-mode servers print the same line, and it says nothing about the end and start tags. "Are consistent" would be exact.

"The first is unlikely" is a fair judgement, given the same server, template and request path.

## Appendix fills

- "largest: 2,178 tokens, a thinking-on call of `qwen38_27b`" — correct.
- "The failed root's calls … 12 calls of at most 2,173 tokens, then the 31,551-token reply, which the cap would have cut" — correct.
- "For the two thinking-on models of the stopped run it took effect: every other thinking-on call ended within 2,178 tokens … Why the one stopped call ran to 31,551 tokens could not be established" — supported, and no overclaim.

The remaining ⟨…⟩ fields belong to the restarted run, as stated.

## Marker transition

The PLAN row and `_c` §2.4 now record the transition as "proposed by the Mac-local agent and agreed by the author (message of 12 Nov 2026, not quoted)". The reason and the R4 precedent are kept. The retirement receipt goes to the new `_c` handover directory, and nothing is written into `_b`. I cannot see the author's message itself. The record follows the style rule (paraphrased, cited by date, not quoted), and the coordinator confirms the agreement.

## `_c` §0 preconditions: all satisfiable from the branch at `1c543173`

1. **Diagnosis complete:** it has no **PENDING** section; §2.3 and §3 are filled.
2. **Cap check:** §3 reads **PASS** over 64 completed roots (2,178 < 16,384).
3. **PLAN rows:** `R1-EXAM-B1-ANCHOR-R4`, `R1-EXAM-B1-ANCHOR-R4-H2` and `R1-EXAM-B1-TRUNCATION-INVALID` are all present in PLAN §10.
4. **Host-version test re-run:** §2.3 records it (17 passed, 0 skipped, exact host versions).

The two margins of the "go to the author" list are sufficient for the measured candidates (above).

**Before the experiment agent uses the hand-off,** two things must hold:
- the review file `docs/r1/reviews/B1_TRUNCATION_REVIEW_20261111.md` must be committed after the base, in a review-record-only commit, with its `Reviewed base:` line;
- `Claude outputs/READY.txt` must name the accepted commit below.

That is the §1 rule; it is the integrator's step, not a defect.

## Notes (no action required for acceptance)

1. **§2.2 wording.** Change "Two explanations fit" to "at least two", and "agree" to "are consistent" for the "thinking = 1" lines (see above).
2. **Version gating.** The content-filter assertion accepts either shape under either openai version. It could be gated on the installed version for strictness. This is harmless here.
3. **Unmeasured candidates (for the author's awareness).** The observer margin is ≈ 2,100 budget-bounded tokens in 60 s, so it needs roughly ≥ 35 tokens/s. The deadline needs ≥ ≈ 30 tokens/s in the all-capped worst case. Both were checked only for `qwen25_coder_7b`, `qwen36_27b` and `qwen38_27b`.
   - Later candidates include a dense 31B model with a thinking switch and always-on reasoning models.
   - For such a candidate, a rate below these levels, or a template that does not arm the budget, would end in a STOP, as before this change. The diagnosis (§5, §5a) says so, and the STOPs remain STOPs.
   - If Stage A's per-candidate latency data are at hand, quoting their tokens/s would make the margin explicit before the restart.
4. **Sentinel line.** `venv_versions.txt` ends with a capture sentinel line `VENV_DONE`. This is harmless.

## Host-check hand-off

It ran as specified, apart from the disclosed source-path deviation, which is handled correctly. The census edit is in place. Nothing further is needed for this round.

## Verdict

The fix, its tests (now also passing with the host's exact client versions), the usage script, the re-pin (`paper_commit = 1334c616`, protected-path diff to the tip empty), the PLAN row, the completed diagnosis, the appendix fills, the RUNBOOK and PORTAL notes and the `_c` hand-off are correct. The cap check passes with a wide margin (2,178 < 16,384). The observer and deadline margins are sufficient for the measured candidates, and every `_c` §0 precondition is satisfied by this commit.

Verdict: accepted
Accepted commit: 1c5431732993db513e2d1cfdc7473932fef700dc
