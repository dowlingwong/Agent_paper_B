# B1 STOP of run `fffa_20261111_b` — diagnosis of the truncated proposer reply (11 November 2026)

**Status.** AI-assisted (Claude, Mac-local agent). This is item (1) of the author's route for the STOP recorded in `reports/B1_STOP_FFFA_20261111.md` (branch `mac-b1-20261107` @ `8af27919`). The author ruled the STOP an engineering problem (PLAN §10 `R1-EXAM-B1-TRUNCATION-INVALID`). §§1–2 come from the code and from the upstream llama.cpp source at the pinned commit. §3 (the per-root completion table) and the host confirmations in §2.3 need the read-only host check `proposals/B1_TRUNCATION_HOST_CHECK_HANDOFF_20261111.md`; they are marked **PENDING** until its copies arrive.

## 0. Summary

| Question | Answer | Basis |
|---|---|---|
| Why did the truncation stop the batch instead of becoming an invalid proposal? | The OpenAI SDK raised `LengthFinishReasonError` inside the call. The harness's invalid-proposal path only handles a reply that comes back, and nothing above the call catches the exception. | §1 (code at harness `a3fedbb`, paper `fffa45a1`, the retained traceback) |
| Does the pinned llama.cpp support `--reasoning-budget N>0`? | **In its source, yes.** At `620d222`, N>0 is a token budget for thinking. It is enforced only when the chat-template analysis yields both a thinking start tag and an end tag; otherwise it is silently ignored. Whether it took effect for `qwen36_27b` in this run is **not established**. The 31,551-token reply suggests it did not; the per-call usage of §3 will show it. | §2; host confirmation **PENDING** |
| Is the cap of 16,384 above the largest completion of every completed root? | **PENDING** (§3) | host copies |

## 1. Why the exception bypassed the invalid-proposal path

The call chain, as in the retained `runner.log` traceback (report §4):

1. `r1/exam/campaign.py::exam_manager` builds the harness `LangGraphManager(model='llamacpp/<id>', proposal_schema='manager_proposal/v1', transport_retry=None)`.
2. On the schema path the harness builds `ChatOpenAI(..., model_kwargs={'response_format': <json_schema>})` (`langchain_client._build_chat_model`). With a JSON-schema `response_format`, `langchain_openai` reads the reply through the OpenAI SDK's structured-output parser (`raw_response.parse()` → `openai.lib._parsing._completions.parse_chat_completion`).
3. That parser raises `openai.LengthFinishReasonError` when `finish_reason == "length"`, before returning anything. The server had stopped at the context limit (`n_tokens = 32767, truncated = 1`), so it reported `finish_reason` `length`.
4. Harness `transport_retry.invoke_with_retry` classifies the exception: it is not a transport error, so it gets `non_retryable`, the attempt log is attached, and it is re-raised. `LangGraphManager.propose_next_trial` adds the seed and `cache_prompt` and re-raises. `control_plane.campaign._propose_logged` emits `llm_call_failed` (the retained `stop_event.json`) and re-raises.
5. `run_real_campaign`, `r1/exam/campaign.py::_collect_b1_review` and the worker's `main` do not catch it. The worker exits 1, and the batch records `STOP: root worker exit 1`.

The invalid-proposal path is the harness validator `_validate_proposal`. When the reply content does not parse as `manager_proposal/v1`, it sets `parse_failed` and leaves no structured edit. The control plane then records `failed_invalid` (`PROPOSAL_PRECONDITION_FAILED`) without a worker run and charges the call. That path runs only on a reply that has come back. On the schema path B1 uses, the SDK parser turns truncation into an exception before that path is reached. (On the free path, which B1 does not use, a truncated reply would come back as text; `parse_failed` is not set there and a heuristic edit could still be extracted, so it is not this path.)

## 2. `--reasoning-budget` in the pinned llama.cpp

### 2.1 Source at `620d222` (upstream `ggml-org/llama.cpp`, "llama.cpp : bump version to 0.7.0", 15 Oct 2026)

- `common/arg.cpp` l. 3741: `--reasoning-budget N` — "token budget for thinking: -1 for unrestricted, 0 for immediate end, N>0 for token budget (default: -1)". It sets `params.sampling.reasoning_budget_tokens`. The flag accepts N>0 and it has a meaning.
- `tools/server/server-common.cpp` l. 1441–1452: for each chat request, the budget (request field `reasoning_budget_tokens` / `thinking_budget_tokens`, else the server flag) is passed to sampling **only if `out_session.thinking_end_tags()` is non-empty**. Otherwise no budget fields are set and the request runs without a thinking budget. No warning is logged.
- `common/chat.cpp` l. 1414–1420: the end tag comes from the template analysis (`autoparser.reasoning`). If the analysis finds no reasoning block, or no end tag, the list stays empty. Specialised template handlers return their own parameters.
- `tools/server/server-schema.cpp` l. 339–378 and `common/sampling.cpp` l. 314–322: the start tag is tokenised from `reasoning_budget_start_tag` and the end tags from `reasoning_budget_end_tags`; the budget sampler is created only when start and end sequences are both non-empty. An empty start tag disarms the budget as well.
- `tools/server/server-schema.cpp` l. 44–48: `n_predict` accepts the aliases `max_completion_tokens` and `max_tokens`. This is why the fix's cap is honoured whichever name the client sends.
- The only log line that states the budget actually applied (`server-schema.cpp` l. 503, "reasoning budget: tokens=…, start=… toks, end=… seqs") is at debug level 5. The run's `-lv 4` (trace) does not print it, so the retained server log cannot show whether the budget was armed. At `-lv 4` the log does print "chat template, thinking = N" at startup.

### 2.2 Reading

Support for N>0 is present in the source. Whether it applied depends on the template analysis of `qwen36_27b`'s vendor template, which is not visible in the retained evidence. The observation in the STOP report — one reply of 31,551 completion tokens with `--reasoning-budget 2048` — is consistent with the budget **not** being armed for that request. A reply that ends in the JSON answer would otherwise stop near 2,048 thinking tokens plus the answer. It is not proof: the reply could also have been 2,048 thinking tokens followed by a runaway answer. One concrete route to that is the request's JSON-schema `response_format`, which llama.cpp turns into a grammar on the answer; grammar-constrained decoding can run away (for example in unbounded whitespace) once thinking has ended. The per-call completion counts of the completed thinking-on roots (`qwen38_27b` / on, 4 roots) and of the 12 recorded trials of the failed `qwen36_27b` / on root, in §3 (column "calls > 2,048"), are the direct evidence. A call well above 2,048 + a few hundred tokens is not compatible with an armed budget.

### 2.3 Host confirmation — PENDING

From `census.txt`, `llama_check.txt`, `server_grep.txt` and `venv_versions.txt` of the host check: binary SHA-256; `--version`; the `--help` text of `--reasoning-budget`; the checkout's HEAD and cleanliness; the five source-file SHA-256 values against upstream; the "chat template, thinking" lines of the `qwen36_27b` and `qwen38_27b` servers; the client library versions in the frozen venv (`openai`, `langchain_openai`, `langchain_core`, `langgraph`, `pydantic`, `httpx`).

Then, on the Mac side: `r1/tests/test_exam_b1_truncation.py` re-run in a scratch venv with exactly those versions (and harness `a3fedbb`), with `R1_REQUIRE_B1_HARNESS=1`; the result (all passed, none skipped) and the request body's cap field name are recorded here. The tests ran so far with openai 3.46.0, langchain-openai 1.7.4, langchain-core 1.7.6, pydantic 2.14.3; the harness lock file pins langchain-openai 1.2.1.

## 3. Per-root completion usage of run `fffa_20261111_b` — PENDING

To be produced by `python -m r1.scripts.b1_completion_usage --roots <copy>` on the host copies. It covers the 64 completed roots; the failed root is listed separately and is outside the check. Its 12 recorded calls and the 31,551-token reply are reported, not checked.

For each root:
- proposer calls (first proposals and D25 revisions; the harness's `self_forecast` `llm_call` events are counted as observer calls);
- truncated calls;
- largest completion and prompt, and longest latency;
- calls above 2,048 completion tokens;
- failed calls;
- the observer's largest completion and longest server time.

Per candidate and mode it gives:
- the proposer rate (tokens/s);
- the hours a root would take if all 80 LLM calls ended at the cap, against the 12 h per-root deadline;
- the observer reply length that would reach the observer's 60 s timeout.

Check: largest proposer completion over the completed roots < 16,384. The largest prompt is reported too: the cap leaves room up to the context only for prompts below 16,384 tokens.

## 4. The fix (code)

`r1/exam/b1_llm_truncation.py`, wired in by `r1/exam/campaign.py::exam_manager` (commit `1334c616`; config re-pin `62adc6a3`). See PLAN §10 `R1-EXAM-B1-TRUNCATION-INVALID` for the rule. A reply cut short (SDK error, or a returned `finish_reason` of `length` / `content_filter`) reaches the harness as an empty reply. The harness validator rejects it, and it becomes an invalid trial charged to the LLM budget, through exactly the path of §1's last paragraph. Every proposer call sends `max_completion_tokens = 16384`. Regression tests: `r1/tests/test_exam_b1_truncation.py`, through the pinned harness against a stand-in server. They cover: the crash reproduced with the old proposer; four truncation shapes invalid and charged; an all-truncated root ending normally at the LLM cap (trial budget above the cap); with an A4-shaped observer, no observer call on truncated trials and the charged budget equal to the `llm_call` events; a truncated D25 revision as the invalid final proposal; any other failure still a STOP; valid replies unchanged apart from the cap; and the usage script on these harness-shaped roots.

## 5. A related risk this fix does not change: the observer's 60 s timeout

The A4 observer (`r1/exam/observer.py`) sends `max_tokens` 4096 with `urlopen(..., timeout=60.0)`. A truncated observer answer that comes back is already non-fatal (`query_failed`). A **timeout**, however, raises and becomes `B1ObserverFatal`, a STOP. At the 44 tokens/s measured in the STOP, an observer reply of more than about 2,600 tokens takes longer than 60 s. Thinking-on observer calls with an unarmed thinking budget could therefore stop a later run. No completed root stopped this way. §3 quantifies the margin per candidate and mode, at each one's own rate (44 tokens/s is `qwen36_27b`'s), from the observer's largest completion and longest server time. Changing the observer is outside the author's route; if the margin is small, it goes to the author.

## 5a. A second time bound: the per-root deadline

`exam_b1_v2.json` sets `root_timeout_seconds` 43,200 (12 h); `runtime.py` raises `STOP: campaign deadline` past it. With truncation no longer a STOP, a candidate that often runs to the cap spends up to about 80 × 16,384 / r seconds on proposer calls in one root: ≈ 8.3 h at 44 tokens/s, but more than 12 h below ≈ 30 tokens/s. That deadline STOP is unchanged and stays a STOP. §3 reports r per candidate and mode, so the margin is known before the restart.

## 6. What this report does not establish

It does not establish that thinking-on outputs of other candidates stay below the cap in the restarted run. A capped reply is an invalid proposal by rule; how many there are per candidate and mode is reported with B1, and disclosed. It establishes no scientific result of the 64 completed roots: the restart reruns everything in a new tree. Truncated calls record no `reasoning_tokens` (the synthetic empty reply has no token details); the STOP's server reported none either.
