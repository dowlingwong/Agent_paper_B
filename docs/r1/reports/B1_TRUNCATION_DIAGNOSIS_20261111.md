# B1 STOP of run `fffa_20261111_b` — diagnosis of the truncated proposer reply (11 November 2026)

**Status.** AI-assisted (Claude, Mac-local agent). This is item (1) of the author's route for the STOP recorded in `reports/B1_STOP_FFFA_20261111.md` (branch `mac-b1-20261107` @ `8af27919`). The author ruled the STOP an engineering problem (PLAN §10 `R1-EXAM-B1-TRUNCATION-INVALID`). §§1–2 come from the code and from the llama.cpp source at the pinned commit. §2.3 and §3 come from the read-only host check `proposals/B1_TRUNCATION_HOST_CHECK_HANDOFF_20261111.md`, run by the experiment agent on TASL-7 on 11–12 Nov (capture 23:57:46–23:59:50Z, `ssh.exit` 0). Its outputs are committed under `reports/b1_truncation_hostcheck_20261111/`; `roots.tar` (23 MB) stays in `Claude outputs/b1_fffa_usage_20261111/`.

## 0. Summary

| Question | Answer | Basis |
|---|---|---|
| Why did the truncation stop the batch instead of becoming an invalid proposal? | The OpenAI SDK raised `LengthFinishReasonError` inside the call. The harness's invalid-proposal path only handles a reply that comes back, and nothing above the call catches the exception. | §1 (code at harness `a3fedbb`, paper `fffa45a1`, the retained traceback) |
| Does the pinned llama.cpp support `--reasoning-budget N>0`? | **Yes.** The pinned binary's `--help` says "N>0 for token budget". In the source, the budget is enforced only when the chat-template analysis yields a thinking start tag and an end tag. **In this run it took effect** for both thinking-on models: all 92 other thinking-on proposer calls ended at no more than 2,178 tokens, which is the 2,048-token budget plus the JSON answer. That includes the failed root's first 12 calls, on the same server. Why the 13th call ran to 31,551 tokens is **not established** by the retained evidence (§2.2). | §2, host check |
| Is the cap of 16,384 above the largest completion of every completed root? | **Yes: PASS.** The largest proposer completion over the 64 completed roots is **2,178** tokens (`qwen38_27b` / on), a margin of 14,206. | §3 |

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

Support for N>0 is present in the source, and §3 shows the budget armed in practice. On the two thinking-on servers, 61 of the 92 successful proposer calls used more than 2,048 completion tokens, but none used more than 2,178. That is what an armed 2,048-token budget does: at the budget the sampler forces the end of thinking, and the JSON answer follows (roughly 100–130 tokens). Observer calls behave the same way, with at most 2,078 tokens. The "chat template, thinking = 1" lines of both servers (`server_grep.txt`) agree.

The failed call is therefore the exception, not the rule. Before the host check, one reply of 31,551 completion tokens under `--reasoning-budget 2048` looked consistent with the budget not being armed. Two explanations fit the retained evidence, and it cannot decide between them, because the reply's text was not kept: the budget did not arm for that one request, or the reply was 2,048 thinking tokens followed by a runaway answer. One concrete route to that is the request's JSON-schema `response_format`, which llama.cpp turns into a grammar on the answer; grammar-constrained decoding can run away (for example in unbounded whitespace) once thinking has ended. The first is unlikely, since the same server armed it for the root's 12 earlier calls and the request path is the same. Either way, the fix covers both: such a reply is now cut at 16,384 and recorded as an invalid proposal.

### 2.3 Host confirmation

What was to be confirmed, from `census.txt`, `llama_check.txt`, `server_grep.txt` and `venv_versions.txt` of the host check: binary SHA-256; `--version`; the `--help` text of `--reasoning-budget`; the checkout's HEAD and cleanliness; the five source-file SHA-256 values against upstream; the "chat template, thinking" lines of the `qwen36_27b` and `qwen38_27b` servers; the client library versions in the frozen venv (`openai`, `langchain_openai`, `langchain_core`, `langgraph`, `pydantic`, `httpx`).

Then, on the Mac side: `r1/tests/test_exam_b1_truncation.py` re-run in a scratch venv with exactly those versions (and harness `a3fedbb`), with `R1_REQUIRE_B1_HARNESS=1`; the result (all passed, none skipped) and the request body's cap field name are recorded here. The tests first ran with openai 3.46.0, langchain-openai 1.7.4, langchain-core 1.7.6, pydantic 2.14.3; the harness lock file pins langchain-openai 1.2.1.

**Results.**
- **Census:** no B1/exam process and no GPU compute application. The marker and `batch_state.json` SHA-256 values are as in the STOP report. All 301 copied files verify against the host-side `sha256sum` list (`CAPTURE.txt`).
- **Binary:** SHA-256 `b70f4882…7d8b` (as configured); `--version` `0.7.0-dev (build 1, commit 620d222)`; `--help` lists `--reasoning-budget N` with "N>0 for token budget".
- **Source — deviation, disclosed:** the build directory `/home/dowling/exam-x/work/llama.cpp` now holds only `build-exam/`; its source tree is gone. The experiment agent read the clean `620d222` checkout at `/home/dowling/r1_tracks/opt/llama.cpp` instead. Its HEAD is `620d2225…` with an empty `git status`. All five file SHA-256 values equal the upstream values, and the quoted lines are those of §2.1. What this shows is that the source of commit `620d222` is as analysed. That the binary was built from an unmodified tree rests on its version string and its configured SHA-256, not on a rebuild.
- **Server logs:** both thinking-on servers (`qwen36_27b` r2, `qwen38_27b` r2) and their off-mode servers print "chat template, thinking = 1". Their records carry `--reasoning-budget`.
- **Frozen venv:** openai 2.36.0, langchain_openai 1.2.1, langchain_core 1.3.3, langgraph 1.1.10, pydantic 2.13.4, pydantic_core 2.46.4, httpx 0.28.1.
- **Re-run with exactly those versions** (scratch venv; harness `a3fedbb`; `R1_REQUIRE_B1_HARNESS=1`; freeze list `hostver_scratch_venv_freeze.txt`): `test_exam_b1_truncation.py` and `test_b1_completion_usage.py` **17 passed, 0 skipped**.
  - The request body carries `max_completion_tokens: 16384` (keys: `cache_prompt, max_completion_tokens, messages, model, response_format, seed, stream, temperature`).
  - One difference from openai 3.x: openai 2.36's `ContentFilterFinishReasonError` carries no completion, so such a call records no token usage. The test accepts that. llama.cpp does not emit `content_filter`.

## 3. Per-root completion usage of run `fffa_20261111_b`

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

**Result** (`python -m r1.scripts.b1_completion_usage --roots <copy>`, exit 0; `usage.md` / `usage.json` in `reports/b1_truncation_hostcheck_20261111/`):
- **cap check PASS**: 2,178 < 16,384;
- the largest prompt is 1,862 tokens;
- no completed root had a truncated or failed call;
- the failed root `qwen36_27b/b1/on/openml_credit_approval__s9001` (not completed, outside the check) had 12 calls of at most 2,173 tokens before the 31,551-token failure.

The software anchors (`random_valid`, `scripted`; 24 roots) make no LLM calls and are listed as such in `usage.md`.

batch_state.json SHA-256 `0e0926dafee940b84d19d9d4d793b2d23933dd4ba6e02bf8ac3f9f444e370e85`; completed roots 64 (LLM 40); cap 16384; largest proposer completion over completed roots **2178** → cap check **PASS** (margin 14206).

| root | completed | trials | proposer calls | truncated | max completion | max prompt | max latency s | calls > 2,048 | failed calls | observer calls | observer max completion | observer max predicted s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `qwen25_coder_7b/b1/off/digits_mlp__s9001` | yes | 20 | 20 | 0 | 105 | 1780 | 0.8 | 0 | – | 20 | 35 | 0.2 |
| `qwen25_coder_7b/b1/off/digits_mlp__s9002` | yes | 22 | 22 | 0 | 107 | 1862 | 0.8 | 0 | – | 20 | 35 | 0.2 |
| `qwen25_coder_7b/b1/off/digits_mlp__s9003` | yes | 20 | 20 | 0 | 110 | 1846 | 0.8 | 0 | – | 20 | 35 | 0.2 |
| `qwen25_coder_7b/b1/off/digits_mlp__s9004` | yes | 20 | 20 | 0 | 107 | 1769 | 0.8 | 0 | – | 20 | 35 | 0.2 |
| `qwen25_coder_7b/b1/off/openml_credit_approval__s9001` | yes | 20 | 20 | 0 | 118 | 1740 | 0.9 | 0 | – | 20 | 35 | 0.2 |
| `qwen25_coder_7b/b1/off/openml_credit_approval__s9002` | yes | 20 | 20 | 0 | 117 | 1729 | 0.9 | 0 | – | 20 | 35 | 0.2 |
| `qwen25_coder_7b/b1/off/openml_credit_approval__s9003` | yes | 20 | 20 | 0 | 121 | 1606 | 0.9 | 0 | – | 20 | 35 | 0.2 |
| `qwen25_coder_7b/b1/off/openml_credit_approval__s9004` | yes | 20 | 20 | 0 | 122 | 1583 | 0.9 | 0 | – | 20 | 35 | 0.2 |
| `qwen25_coder_7b/b1/off/openml_ionosphere__s9001` | yes | 20 | 20 | 0 | 116 | 1543 | 0.9 | 0 | – | 20 | 35 | 0.2 |
| `qwen25_coder_7b/b1/off/openml_ionosphere__s9002` | yes | 20 | 20 | 0 | 115 | 1509 | 0.8 | 0 | – | 20 | 35 | 0.2 |
| `qwen25_coder_7b/b1/off/openml_ionosphere__s9003` | yes | 20 | 20 | 0 | 119 | 1585 | 0.9 | 0 | – | 20 | 35 | 0.2 |
| `qwen25_coder_7b/b1/off/openml_ionosphere__s9004` | yes | 20 | 20 | 0 | 114 | 1712 | 0.8 | 0 | – | 20 | 35 | 0.2 |
| `qwen36_27b/b1/off/digits_mlp__s9001` | yes | 20 | 20 | 0 | 163 | 1681 | 4.2 | 0 | – | 20 | 37 | 0.8 |
| `qwen36_27b/b1/off/digits_mlp__s9002` | yes | 20 | 20 | 0 | 394 | 1653 | 9.1 | 0 | – | 20 | 37 | 0.8 |
| `qwen36_27b/b1/off/digits_mlp__s9003` | yes | 20 | 20 | 0 | 158 | 1623 | 4.1 | 0 | – | 20 | 37 | 0.8 |
| `qwen36_27b/b1/off/digits_mlp__s9004` | yes | 20 | 20 | 0 | 165 | 1607 | 4.1 | 0 | – | 20 | 37 | 0.8 |
| `qwen36_27b/b1/off/openml_credit_approval__s9001` | yes | 20 | 20 | 0 | 177 | 1773 | 4.5 | 0 | – | 20 | 37 | 0.8 |
| `qwen36_27b/b1/off/openml_credit_approval__s9002` | yes | 20 | 20 | 0 | 513 | 1740 | 11.8 | 0 | – | 20 | 37 | 0.8 |
| `qwen36_27b/b1/off/openml_credit_approval__s9003` | yes | 20 | 20 | 0 | 300 | 1799 | 7.2 | 0 | – | 20 | 37 | 0.8 |
| `qwen36_27b/b1/off/openml_credit_approval__s9004` | yes | 21 | 21 | 0 | 674 | 1599 | 15.3 | 0 | – | 20 | 37 | 0.8 |
| `qwen36_27b/b1/off/openml_ionosphere__s9001` | yes | 20 | 20 | 0 | 708 | 1684 | 15.9 | 0 | – | 20 | 37 | 0.8 |
| `qwen36_27b/b1/off/openml_ionosphere__s9002` | yes | 20 | 20 | 0 | 329 | 1589 | 7.7 | 0 | – | 20 | 37 | 0.8 |
| `qwen36_27b/b1/off/openml_ionosphere__s9003` | yes | 20 | 20 | 0 | 717 | 1665 | 16.0 | 0 | – | 20 | 37 | 0.8 |
| `qwen36_27b/b1/off/openml_ionosphere__s9004` | yes | 20 | 20 | 0 | 144 | 1673 | 3.8 | 0 | – | 20 | 37 | 0.8 |
| `qwen36_27b/b1/on/openml_credit_approval__s9001` | no | 12 | 12 | 0 | 2173 | 1180 | 47.5 | 10 | LengthFinishReasonError (31551 tok) | 12 | 2076 | 44.6 |
| `qwen38_27b/b1/off/digits_mlp__s9001` | yes | 20 | 20 | 0 | 153 | 1722 | 3.9 | 0 | – | 20 | 42 | 0.9 |
| `qwen38_27b/b1/off/digits_mlp__s9002` | yes | 20 | 20 | 0 | 147 | 1710 | 3.8 | 0 | – | 20 | 42 | 0.9 |
| `qwen38_27b/b1/off/digits_mlp__s9003` | yes | 20 | 20 | 0 | 151 | 1690 | 3.9 | 0 | – | 20 | 42 | 0.9 |
| `qwen38_27b/b1/off/digits_mlp__s9004` | yes | 20 | 20 | 0 | 153 | 1706 | 3.8 | 0 | – | 20 | 42 | 0.9 |
| `qwen38_27b/b1/off/openml_credit_approval__s9001` | yes | 20 | 20 | 0 | 512 | 1651 | 11.3 | 0 | – | 20 | 42 | 0.9 |
| `qwen38_27b/b1/off/openml_credit_approval__s9002` | yes | 20 | 20 | 0 | 180 | 1653 | 4.5 | 0 | – | 20 | 42 | 0.9 |
| `qwen38_27b/b1/off/openml_credit_approval__s9003` | yes | 20 | 20 | 0 | 808 | 1711 | 17.8 | 0 | – | 20 | 42 | 0.9 |
| `qwen38_27b/b1/off/openml_credit_approval__s9004` | yes | 20 | 20 | 0 | 163 | 1604 | 4.1 | 0 | – | 20 | 42 | 0.9 |
| `qwen38_27b/b1/off/openml_ionosphere__s9001` | yes | 20 | 20 | 0 | 175 | 1745 | 4.4 | 0 | – | 20 | 42 | 0.9 |
| `qwen38_27b/b1/off/openml_ionosphere__s9002` | yes | 20 | 20 | 0 | 1269 | 1716 | 27.7 | 0 | – | 20 | 42 | 0.9 |
| `qwen38_27b/b1/off/openml_ionosphere__s9003` | yes | 20 | 20 | 0 | 253 | 1704 | 6.1 | 0 | – | 20 | 42 | 0.9 |
| `qwen38_27b/b1/off/openml_ionosphere__s9004` | yes | 20 | 20 | 0 | 183 | 1667 | 4.6 | 0 | – | 20 | 42 | 0.9 |
| `qwen38_27b/b1/on/openml_credit_approval__s9001` | yes | 20 | 20 | 0 | 2164 | 1674 | 46.9 | 15 | – | 20 | 1086 | 23.0 |
| `qwen38_27b/b1/on/openml_credit_approval__s9002` | yes | 20 | 20 | 0 | 2162 | 1663 | 46.9 | 13 | – | 20 | 994 | 21.0 |
| `qwen38_27b/b1/on/openml_credit_approval__s9003` | yes | 20 | 20 | 0 | 2171 | 1615 | 47.0 | 13 | – | 20 | 2078 | 44.0 |
| `qwen38_27b/b1/on/openml_credit_approval__s9004` | yes | 20 | 20 | 0 | 2178 | 1712 | 47.3 | 10 | – | 20 | 1478 | 31.3 |
| `random_valid/b1/off/digits_mlp__s9001` | yes | 29 | software anchor, none | – | – | – | – | – | – | – | – | – |
| `random_valid/b1/off/digits_mlp__s9002` | yes | 24 | software anchor, none | – | – | – | – | – | – | – | – | – |
| `random_valid/b1/off/digits_mlp__s9003` | yes | 25 | software anchor, none | – | – | – | – | – | – | – | – | – |
| `random_valid/b1/off/digits_mlp__s9004` | yes | 27 | software anchor, none | – | – | – | – | – | – | – | – | – |
| `random_valid/b1/off/openml_credit_approval__s9001` | yes | 34 | software anchor, none | – | – | – | – | – | – | – | – | – |
| `random_valid/b1/off/openml_credit_approval__s9002` | yes | 24 | software anchor, none | – | – | – | – | – | – | – | – | – |
| `random_valid/b1/off/openml_credit_approval__s9003` | yes | 37 | software anchor, none | – | – | – | – | – | – | – | – | – |
| `random_valid/b1/off/openml_credit_approval__s9004` | yes | 31 | software anchor, none | – | – | – | – | – | – | – | – | – |
| `random_valid/b1/off/openml_ionosphere__s9001` | yes | 33 | software anchor, none | – | – | – | – | – | – | – | – | – |
| `random_valid/b1/off/openml_ionosphere__s9002` | yes | 27 | software anchor, none | – | – | – | – | – | – | – | – | – |
| `random_valid/b1/off/openml_ionosphere__s9003` | yes | 38 | software anchor, none | – | – | – | – | – | – | – | – | – |
| `random_valid/b1/off/openml_ionosphere__s9004` | yes | 27 | software anchor, none | – | – | – | – | – | – | – | – | – |
| `scripted/b1/off/digits_mlp__s9001` | yes | 20 | software anchor, none | – | – | – | – | – | – | – | – | – |
| `scripted/b1/off/digits_mlp__s9002` | yes | 20 | software anchor, none | – | – | – | – | – | – | – | – | – |
| `scripted/b1/off/digits_mlp__s9003` | yes | 20 | software anchor, none | – | – | – | – | – | – | – | – | – |
| `scripted/b1/off/digits_mlp__s9004` | yes | 20 | software anchor, none | – | – | – | – | – | – | – | – | – |
| `scripted/b1/off/openml_credit_approval__s9001` | yes | 20 | software anchor, none | – | – | – | – | – | – | – | – | – |
| `scripted/b1/off/openml_credit_approval__s9002` | yes | 20 | software anchor, none | – | – | – | – | – | – | – | – | – |
| `scripted/b1/off/openml_credit_approval__s9003` | yes | 20 | software anchor, none | – | – | – | – | – | – | – | – | – |
| `scripted/b1/off/openml_credit_approval__s9004` | yes | 21 | software anchor, none | – | – | – | – | – | – | – | – | – |
| `scripted/b1/off/openml_ionosphere__s9001` | yes | 20 | software anchor, none | – | – | – | – | – | – | – | – | – |
| `scripted/b1/off/openml_ionosphere__s9002` | yes | 20 | software anchor, none | – | – | – | – | – | – | – | – | – |
| `scripted/b1/off/openml_ionosphere__s9003` | yes | 20 | software anchor, none | – | – | – | – | – | – | – | – | – |
| `scripted/b1/off/openml_ionosphere__s9004` | yes | 21 | software anchor, none | – | – | – | – | – | – | – | – | – |

Per candidate and mode (all roots in the copy; time bounds at the measured proposer rate; per-root deadline 12 h, observer timeout 60 s):

| candidate / mode | roots (completed) | proposer calls | truncated | max completion | tokens/s | h if all 80 calls hit the cap | observer reply tokens at 60 s | observer max predicted s |
|---|---|---|---|---|---|---|---|---|
| `qwen25_coder_7b` / off | 12 (12) | 242 | 0 | 122 | 138.4 | 2.6 | 8301.7 | 0.2 |
| `qwen36_27b` / off | 12 (12) | 241 | 0 | 717 | 39.4 | 9.2 | 2366.5 | 0.8 |
| `qwen36_27b` / on | 1 (0) | 12 | 0 | 2173 | 45.9 | 7.9 | 2752.8 | 44.6 |
| `qwen38_27b` / off | 12 (12) | 240 | 0 | 1269 | 40.2 | 9.1 | 2409.2 | 0.9 |
| `qwen38_27b` / on | 4 (4) | 80 | 0 | 2178 | 46.2 | 7.9 | 2770.4 | 44.0 |

## 4. The fix (code)

`r1/exam/b1_llm_truncation.py`, wired in by `r1/exam/campaign.py::exam_manager` (commit `1334c616`; config re-pin `62adc6a3`). See PLAN §10 `R1-EXAM-B1-TRUNCATION-INVALID` for the rule. A reply cut short (SDK error, or a returned `finish_reason` of `length` / `content_filter`) reaches the harness as an empty reply. The harness validator rejects it, and it becomes an invalid trial charged to the LLM budget, through exactly the path of §1's last paragraph. Every proposer call sends `max_completion_tokens = 16384`. Regression tests: `r1/tests/test_exam_b1_truncation.py`, through the pinned harness against a stand-in server. They cover: the crash reproduced with the old proposer; four truncation shapes invalid and charged; an all-truncated root ending normally at the LLM cap (trial budget above the cap); with an A4-shaped observer, no observer call on truncated trials and the charged budget equal to the `llm_call` events; a truncated D25 revision as the invalid final proposal; any other failure still a STOP; valid replies unchanged apart from the cap; and the usage script on these harness-shaped roots.

## 5. A related risk this fix does not change: the observer's 60 s timeout

The A4 observer (`r1/exam/observer.py`) sends `max_tokens` 4096 with `urlopen(..., timeout=60.0)`. A truncated observer answer that comes back is already non-fatal (`query_failed`). A **timeout**, however, raises and becomes `B1ObserverFatal`, a STOP. At the 44 tokens/s measured in the STOP, an observer reply of more than about 2,600 tokens takes longer than 60 s. Thinking-on observer calls with an unarmed thinking budget could therefore stop a later run. No completed root stopped this way.

**Measured (§3):**
- Thinking-off observer calls take under 1 s.
- Thinking-on observer calls are bounded by the armed budget: at most 2,078 tokens, with a longest server time of **44.6 s** (`qwen36_27b` / on) and 44.0 s (`qwen38_27b` / on), against the 60 s timeout. That is a margin of about 15 s (≈ 25 %). At those servers' ≈ 46 tokens/s, 60 s corresponds to ≈ 2,750 tokens.
- The margin holds while the budget arms. A thinking-on candidate that is slower, or whose template does not arm the budget, could reach the timeout. That would be a STOP, as before this change.

This is recorded for the author; this route does not change the observer. Changing the observer is outside the author's route; if the margin is small, it goes to the author.

## 5a. A second time bound: the per-root deadline

`exam_b1_v2.json` sets `root_timeout_seconds` 43,200 (12 h); `runtime.py` raises `STOP: campaign deadline` past it. With truncation no longer a STOP, a candidate that often runs to the cap spends up to about 80 × 16,384 / r seconds on proposer calls in one root: ≈ 8.3 h at 44 tokens/s, but more than 12 h below ≈ 30 tokens/s. That deadline STOP is unchanged and stays a STOP. §3 reports r per candidate and mode, so the margin is known before the restart.

**Measured:** the hours a root would take if all 80 calls ended at the cap are 2.6 h (`qwen25_coder_7b`), 9.1–9.2 h (`qwen38_27b` / `qwen36_27b` off) and 7.9 h (both / on), all under 12 h. These rates include prompt evaluation, so the off-mode figures, from short replies, are conservative. Candidates later in the grid have not run, and their rates are not known. For them the deadline STOP stays a STOP.

## 6. What this report does not establish

It does not establish that thinking-on outputs of other candidates stay below the cap in the restarted run. A capped reply is an invalid proposal by rule; how many there are per candidate and mode is reported with B1, and disclosed. It establishes no scientific result of the 64 completed roots: the restart reruns everything in a new tree. Truncated calls record no `reasoning_tokens` (the synthetic empty reply has no token details); the STOP's server reported none either.
