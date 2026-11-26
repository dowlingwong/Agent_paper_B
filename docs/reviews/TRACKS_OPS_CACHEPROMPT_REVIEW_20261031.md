# Track S — independent review of the `cache_prompt: false` harness/collector change

**Reviewer:** independent (fresh session; not the operator/author; did not read the operator's draft review).
**Date:** 31 Oct 2026.
**Under review:**
- Harness worktree `.claude-worktrees/harness-cacheprompt`, branch `cacheprompt-20261031`, HEAD
  **`987fb26`**, base **`115df37`**; pushed to `origin/cacheprompt-20261031`; `origin/r1` at
  `897d83c` (untouched).
- Paper worktree `.claude-worktrees/trackS-ops-20261030`, branch `trackS-ops-20261030`, HEAD
  **`5e6a83c6`**, pushed to `origin/trackS-ops-20261030`.
**Environment:** `_harness_venv` (Python 3.11.11; langchain-openai 1.7.3, openai 3.42.0), harness
installed editable at the working clone. Hosts read-only over SSH (`tasl7`).
**Labels:** the harness/collector change is `ENGINEERING_ONLY`; nothing here is evidence.

## 1. Scope

I reviewed, against the author ruling **R1-CACHEPROMPT-FALSE (31 Oct 2026)**:

1. the harness diff `115df37..987fb26` (4 files, +223/−0) and the paper diff `5e6a83c6^..5e6a83c6`
   (3 files, +34/−3);
2. whether `cache_prompt` reaches the HTTP body on every request path — with a real
   `ChatOpenAI` client against a stand-in server, not by reading the test names;
3. the new harness test module `tests/stage2/test_r1_cache_prompt.py`;
4. the "every manifest and `llm_call` record" claim;
5. the A4 observer / `ManagerQuestionPrior` side queries;
6. the full harness suite at `115df37` and at `987fb26`, with counts and failure sets;
7. the paper probe (`r1/tracks/probes/determinism.py`) and its tests;
8. rule discipline (no `r1` merge, no force-push, no unrelated behaviour) and host pin wiring.

I did **not** run a GPU job, did not start a llama-server, and did not modify any reviewed file. I wrote
only this review; the one test-generated artifact I created (the untracked completeness report in the
harness clone) was removed. **Note:** uncommitted modifications appeared in both worktrees *during* this
review (not made by me; see §2.10). They are not part of the commits under review and were not used for
any finding or for the verdict.

## 2. What I re-ran and what it showed

### 2.1 Diff inventory

```
cd .claude-worktrees/harness-cacheprompt
git log --oneline -5                     # 987fb26, 115df37, f8bc222, 6adf385, 897d83c
git diff --stat 115df37..987fb26
#  src/autoresearch/llm/langchain_client.py      |  11 ++
#  src/autoresearch/llm/providers.py             |  21 +++
#  src/autoresearch/manager/langgraph_manager.py |   3 +
#  tests/stage2/test_r1_cache_prompt.py          | 188 ++++++++++++++++++++++++++++++++++
git status --porcelain                   # clean
```

Paper:

```
cd .claude-worktrees/trackS-ops-20261030
git diff 5e6a83c6^..5e6a83c6 --stat
#  r1/tests/test_tracks_probes.py  | 11 ++++++++++-
#  r1/tracks/collect.py            | 17 ++++++++++++++++-
#  r1/tracks/probes/determinism.py |  9 ++++++++-
git status --porcelain                   # clean
```

### 2.2 The value really reaches the wire (not just an object attribute)

The implementation puts the value in `extra_body` (`langchain_client.py:194-197`) and LangChain's
`ChatOpenAI` forwards `extra_body` as a `create()` keyword; the OpenAI SDK merges it into the JSON body.
I proved this twice, with real HTTP:

- The checked-in stand-in test (`tests/stage2/test_r1_cache_prompt.py`) parses the body received by
  `BaseHTTPRequestHandler.do_POST`; run alone:

```
_harness_venv/bin/python -m pytest -q tests/stage2/test_r1_cache_prompt.py
# .......... 10 passed in 2.66s
```

- My own capture of the manager path with the **schema** variant enabled:

```
WIRE BODY KEYS: ['cache_prompt', 'messages', 'model', 'response_format', 'seed', 'stream', 'temperature']
cache_prompt: False <class 'bool'>
llm_call: {..., "seed": 4291946481, "cache_prompt": false, "schema_version": "manager_proposal/v1", ...}
```

- The `model_kwargs` counter-claim is also true, not just asserted in a comment:

```
ChatOpenAI(..., model_kwargs={"cache_prompt": False}).invoke(...)
# TypeError: Completions.create() got an unexpected keyword argument 'cache_prompt'
# requests seen: 0   (fails before any HTTP; `extra_body` is the correct channel)
```

### 2.3 Every harness request path available at this commit

`grep -rn "ChatOpenAI(\|_build_chat_model(\|resolve_llm_config(" src/` shows that
`langchain_client._build_chat_model` (`langchain_client.py:142`, the only `ChatOpenAI(...)` at
`langchain_client.py:209`) is the **only** model constructor in the harness; its only callers are
`LangChainProposalBackend._invoke` (`langchain_client.py:95`) and `LangGraphManager._resolve_llm`
(`langgraph_manager.py:612`). Both harness LLM users therefore go through it, so the routing is
adequate for future **harness** side queries. The transport retry re-invokes the same model object; the checked-in test `drop`→`ok`
shows two POSTs, both with `cache_prompt: false`.

### 2.4 Side queries the author named do **not** exist in the harness at `115df37`

```
grep -rn "ManagerQuestionPrior\|QuestionPrior\|A4" --include=*.py src/    # no matches
```

The harness has only the generic `proposal_observer` hook (`campaign.py`), whose LLM is supplied by the
caller — so the harness itself has no A4 observer or `ManagerQuestionPrior` to instrument at this
commit. **However, both exist in the paper repo at `5e6a83c6` and they send their own hand-built
HTTP body, which does not carry `cache_prompt`** (finding R1).

### 2.5 Paper probe: it now posts exactly the wire shape the harness posts

Before the change, `_get_request_payload()` returns the value nested as `extra_body` (verified:
`raw payload keys: ['extra_body', 'messages', 'model', 'seed', 'stream', 'temperature']`), and the probe
posts the payload itself — so without `determinism.py:63-70` the probe would have sent a nested
`extra_body` that llama-server ignores. The merge is necessary and correct. End-to-end against my own
stand-in server:

```
plain payload:  {"cache_prompt": false, "messages": [...], "model": "r1-manager", "seed": 123, "stream": false, "temperature": 0.2}
WIRE 1:          same dict (no `extra_body` key)
schema payload keys: ['cache_prompt', ..., 'response_format', ...]
WIRE 2 keys:    ['cache_prompt', ..., 'response_format', ...]  | cache_prompt: False | response_format present
nested extra_body on wire: False
```

The key set is identical to the one the real manager sent in §2.2, so the probe and the harness agree
on the body. The probe report records the value, but only implicitly: `request_example` (built by
`chat_payload`, `determinism.py:316`) now contains `cache_prompt: false`; there is no top-level
`cache_prompt` field (R6).

Paper probe tests — Mac and host:

```
AR_HARNESS_ROOT=<harness-cacheprompt> PYTHONPATH=. python -m pytest -q r1/tests/test_tracks_probes.py
# ........ 8 passed in 1.13s
# on TASL-7, paper_cp 5e6a83c + harness_cp 987fb26:
# ........ 8 passed in 0.71s
```

Against the **old** harness the two new assertions fail (`KeyError: 'cache_prompt'`), which confirms the
paper commit is coupled to the new harness pin:

```
AR_HARNESS_ROOT=<115df37 checkout> python -m pytest -q r1/tests/test_tracks_probes.py
# 2 failed, 6 passed
```

### 2.6 Full harness suite before/after (counts)

The base commit was extracted into a real git clone so that the comparison is not confounded by a
missing `.git` (an earlier `git archive` copy produced 5 spurious skips in git-dependent tests; I
discarded that run):

```
git clone --no-hardlinks <harness-cacheprompt> /tmp/harness-base-clone && git -C ... checkout 115df37
cd /tmp/harness-base-clone
PYTHONPATH=/tmp/harness-base-clone/src _harness_venv/bin/python -m pytest -q --ignore=tests/test_legacy_noop_skip.py
cd <harness-cacheprompt>
_harness_venv/bin/python -m pytest -q --ignore=tests/test_legacy_noop_skip.py
```

| run | commit | state | failed | passed | errors | subtests |
|---|---|---|---|---|---|---|
| clean run 1 | `115df37` | fresh clone | **21** | **455** | 2 | 53 |
| rerun in same clone | `115df37` | report file now present | **20** | **456** | 2 | 53 |
| clean run 1 | `987fb26` | working clone, clean | **21** | **465** | 2 | 53 |
| rerun in same clone | `987fb26` | report file now present | **20** | **466** | 2 | 53 |

- **The operator's two numbers reproduce exactly** (21/455 before, 20/466 after) — but they are **not a
  like-for-like comparison**: the `21→20`/`455→466` movement is the pre-existing flaky test plus the 10
  new tests, not a single 1-failure/11-pass change. Clean-to-clean the delta is **+10 passed, 0 new
  failures, same 2 errors, same 53 subtests**.
- **Failure sets are identical**: `diff` of the sorted `FAILED`/`ERROR` lists from the clean base run
  and the clean head run is empty.
- **Flaky test verified**: `tests/test_artifact_completeness_and_manifest.py::TestCompletenessCLI::test_checked_in_report_contains_all_plan_campaigns`
  asserts the existence of the **untracked** `paper/tables/artifact_completeness_report.txt`
  (`git status` shows `??`, so it is not checked in at this commit); a test in the suite regenerates it,
  so the first run in a clean checkout fails it and a rerun passes it. It toggles identically on base
  (21→20) and head (21→20). It is pre-existing and unrelated.
- **Collection error verified**: `pytest -q tests/test_legacy_noop_skip.py` →
  `ModuleNotFoundError: No module named 'src.autoresearch_worker'` (1 error during collection), so
  `--ignore=tests/test_legacy_noop_skip.py` is legitimate and pre-existing.
- The 2 errors (`TestResumedCommitSemantics`) are identical before and after.

### 2.7 Paper side (other than the probe)

```
AR_HARNESS_ROOT=<new harness> PYTHONPATH=. python -m pytest -q \
  r1/tests/test_tracks_collect.py r1/tests/test_tracks_final_review.py \
  r1/tests/test_exam_observer.py r1/tests/test_tracks_ops.py
# 47 passed in 80.22s; paper worktree left clean
```

### 2.8 Rule discipline / host wiring

```
git rev-parse origin/r1                                  # 897d83c  (r1 untouched)
git merge-base --is-ancestor 115df37 origin/r1; echo $?   # 1  (115df37 is NOT on r1 — as stated)
git log --oneline origin/r1..987fb26
# 987fb26 llm: send cache_prompt explicitly on every llamacpp request (default false)
# 115df37 Track S: optional seed_key for the LangGraph manager's D26 seed
# f8bc222 Track S: fork-arm overrides in resume_campaign, controller ledger view, skip displays hidden/v1 and reason/v1
# 6adf385 Apply predeclared D28 start configurations
git rev-parse origin/cacheprompt-20261031                # 987fb26
```

No merge into `r1`, no history rewrite on the reviewed branch (it is a linear descendant of `115df37`),
`origin/r1` unchanged. I cannot see the server-side reflog, so "no force-push" is inferred from the
linear ancestry and the unchanged `origin/r1`, not independently provable from this clone.

Host (read-only):

```
work/autoresearch_harness 115df37   work/Agent_paper_B 9bb64ba
work/harness_cp           987fb26   work/paper_cp       5e6a83c   (both clean, detached)
venv .pth -> work/autoresearch_harness/src
bin/trks: export AR_HARNESS_ROOT=$R/work/autoresearch_harness
r1/tracks/ops/trks-status: PAPER_SHA=9bb64ba  HARNESS_SHA=115df37; checks work/Agent_paper_B, work/autoresearch_harness
```

With `AR_HARNESS_ROOT=harness_cp` the paper `collect._manager_cache_prompt()` returns `False` and
`autoresearch` resolves to `harness_cp`; **without** it, the frozen venv resolves the old harness
(`.../work/autoresearch_harness/src/autoresearch/__init__.py`). That is the pin trap in R2.

### 2.9 Manifest and record sites (the "every manifest and `llm_call` record" claim)

`RunManifest` (`src/autoresearch/reliability/schema/manifest.py`) is referenced only by the generic
`reliability/schema` export/validation modules; `grep` finds no campaign writer for it, so the operator's
statement that the harness has no campaign-manifest writer at `115df37` is correct. For these tracks the
manifest is the paper collector's: `build_manifest` writes `"manager": manager_cfg(args)`
(`r1/tracks/collect.py:1316`, new field at `1361-1363`) and the per-session `provenance` records the
harness commit (`collect.py:2108-2112`). The `llm_call` event is emitted by
`campaign.py:351-366` as `payload=dict(meta)`, so the manager's new `cache_prompt` key reaches the
persisted event unchanged (no whitelist). The `LangChainProposalBackend` path writes its value into the
proposal `extra` (`langchain_client.py:78-90`), not into a `llm_call` event (pre-existing design).

### 2.10 Worktree state at the end of this review (not part of the reviewed commits)

Both worktrees were **clean at `987fb26` / `5e6a83c6`** at the start of the review, and every test count
in §2.6 was measured there. While this review was being written, **uncommitted modifications appeared in
both worktrees** (timestamps 12:03 local; I did not make them): harness
`src/autoresearch/llm/langchain_client.py`, `src/autoresearch/manager/langgraph_manager.py`,
`tests/stage2/test_r1_cache_prompt.py` (two extra tests: schema-on-the-wire and the emitted
`llm_call` event); paper `r1/c3/prior_model.py`, `r1/exam/observer.py`,
`r1/tracks/probes/determinism.py`. Read at a glance, they appear to address R1, R3, R5, R6 and R7.
**They are uncommitted and unreviewed**: the verdict below applies to the commits under review
(`987fb26`, `5e6a83c6`), and every file/line number in this document refers to those commits (the
in-flight edits shift some of them). If they are the operator's response, they need to be committed (new
commits, new pins), the suite re-run, and a fresh review; nothing in this document certifies them.

## 3. Findings

### R1 — BLOCKING — the A4 observer and `ManagerQuestionPrior` queries still send a body with **no** `cache_prompt`

The author required the field on **every** request path, naming the A4 observer and
`ManagerQuestionPrior`. They do not exist in the harness at `115df37` (verified by grep), but they exist
in the paper at this commit and use their own raw HTTP client:

- `r1/c3/prior_model.py:253-267` — `chat_client()` posts
  `{"model", "messages", "max_tokens", "temperature", "seed"}`; **no `cache_prompt`**.
- `r1/exam/observer.py:5,13` — `SelfForecastObserver` is built with `chat_client(...)`; this is the A4
  exam observer used by `r1/exam/campaign.py:82` for every `kind=='llm'` EXAM campaign.
- `r1/scripts/c3_control_dryrun.py:201,222` — the A4 arm passes `chat_client(...)` into
  `ManagerQuestionPrior`; the `llm_self` arm uses the same client.
- Their records do not carry the value either: the observer's `observe()`/`exam_self_forecast` payload
  and `Forecast` have no `cache_prompt`.

Consequence: EXAM and C3-A4 side queries remain subject to the exact non-determinism this ruling is
meant to remove, and — unlike the manager — they are silent, because no test looks at their bodies.
The operator's `test_side_query_backend_carries_it` covers `LangChainProposalBackend`, which is a second
*manager* backend, not a side query; the new test module's docstring ("every request path available at
this commit") therefore overstates the evidence. `resolve_llm_config`/`_build_chat_model` cannot fix
this from the harness: these clients never call it and never read `LLAMACPP_CACHE_PROMPT`.

Fix (small): add the resolved value to `chat_client`'s body (read it through the harness
`llamacpp_cache_prompt()` so there is one source of truth, or route `chat_client` through
`_build_chat_model`), record it in the forecast/exam payload, and add a stand-in-server test for the A4
and A4-control paths.

*This finding does not affect the S0.1 probe path (see §2.5): the probe and the manager are correct.*

### R2 — MAJOR — the pin/status wiring still points at the old checkout; pins are not updated

`r1/tracks/ops/trks-status:9-10` still pins `PAPER_SHA=9bb64ba` / `HARNESS_SHA=115df37` and checks
`work/Agent_paper_B` / `work/autoresearch_harness`, not the new `paper_cp` / `harness_cp` checkouts.
`bin/trks` **cds to `work/Agent_paper_B` (old paper `9bb64ba`)** and exports
`AR_HARNESS_ROOT=$R/work/autoresearch_harness` (115df37); `bin/trks-diag` exports the same harness path;
the frozen venv's editable `.pth` also resolves that checkout. Any invocation that does not set
`AR_HARNESS_ROOT` explicitly (e.g. the host wrappers `trks`/`trks-diag`, or a bare `python` in
`work/` / `paper_cp`) therefore uses 115df37 and the old paper, and would **silently post the old body**
(no `cache_prompt`, identity ≈ 0.930) while the operator might blame the server; only a run of the new
paper code against the old harness would be loud (`ImportError` on `llamacpp_cache_prompt`). Note also
that `trks-status` checks the **old** checkouts, so it can print `OK` for 115df37/9bb64ba while the
re-run actually uses `harness_cp`/`paper_cp` — a false provenance signal. This is
the author's "update the collector **and pins**" requirement, still pending. It must be part of
pinning: update `trks-status` pins/paths, `bin/trks` `AR_HARNESS_ROOT`, and record the new
paper/harness pair (PLAN/STATUS) — the "paper repo gets a new pin with no other code change" commit does
not exist yet (`5e6a83c6` is the code change). This is a condition on the pin step, not a defect in the
reviewed commits.

### R3 — MINOR — `cache_prompt: null` is written into every non-llamacpp `llm_call` record and proposal extra

`langgraph_manager.py:570` adds the key unconditionally (`None` for injected stubs and for
ollama/vllm/deepseek/anthropic), and `langchain_client.py:86` adds it unconditionally to
`LangChainProposalBackend` extras. The stated design says `None` means "the provider does not carry the
setting"; in that case the field should be **omitted** rather than persisted as `null`. As written, the
record schema changes for Track H/X Ollama runs and any DeepSeek run, beyond the intended llama-server
setting. No checked-in harness test asserts the exact `llm_call` payload (the suite's 53 subtests and
the rest pass unchanged), so nothing breaks today, but a reader cannot distinguish "provider does not
carry it" from "the field was not recorded".

### R4 — MINOR — pre-change manifests can no longer be resumed

`manager` is in `MANIFEST_KEYS` (`collect.py:1275-1280`) and the resume guard compares it
(`collect.py:2092`). Every pre-change **llamacpp** langgraph manifest lacks `cache_prompt`, so
resuming it with the new collector exits with `refusing to resume … manager differs` (Ollama/scripted
manifests are unchanged). This is probably the right behaviour
(the run parameters genuinely differ), but it is an unrecorded consequence for any partial Track S/C3
run; state it, and use fresh output directories.

### R5 — MINOR — `LangChainProposalBackend` records a value it did not necessarily send

`langchain_client.py:86` records `self.config.cache_prompt` even when `llm=...` is injected (the manager
correctly records `None` at `langgraph_manager.py:532`). With an injected stub the record claims
`False` although nothing was sent. The new test covers only the manager's injected case.

### R6 — MINOR — the "absent (= true, llama-server default)" label exists only in prose; the probe report has no explicit field

No code reads or summarises `cache_prompt` today, so nothing in code labels old records. The docs say
"absent" (STATUS table) and explain "omitting the field equals `cache_prompt: true`" (D6 report), but
the exact label the author asked for is not used anywhere, and the new probe report records the value
only inside `request_example` (`determinism.py:316`) — a summariser reading `report["cache_prompt"]`
would find nothing. Add a top-level `cache_prompt` to the probe report and write the label wherever a
future summary reads the field.

### R7 — MINOR — two test-coverage gaps (verified by hand, not by the checked-in tests)

- The record assertion is on `proposal.extra["llm_call"]`, not on the persisted `llm_call` event. The
  code path is a pass-through (`campaign.py:357-366`, `payload=dict(meta)`), so it is correct, but the
  checked-in test does not prove the event.
- The `manager_proposal/v1` variant is checked only at the LangChain payload level
  (`test_the_model_carries_the_field_in_extra_body`), not on the wire. I captured that variant on the
  wire myself (§2.2); the test should too, since C3 uses it.

### R8 — MINOR — the operator's before/after counts are reproducible but confounded

The reported `21 failed / 455 passed` and `20 failed / 466 passed` are the **clean** and **second-run**
states of the same flaky test (see §2.6), not a clean before/after. The true change delta is +10 passed
(the 10 new tests) with identical failures. Report it as such; the conclusion ("no new failure") is
nevertheless correct.

### R9 — MINOR — the failed-call record does not carry `cache_prompt`

The success path records it (`langgraph_manager.py:570` → `proposal.extra["llm_call"]` → the
`llm_call` event), but the **failure** path does not: `langgraph_manager.py:485-489` attaches only
`exc.llm_call_seed`, and `campaign.py:333-349` emits `llm_call_failed` with
`error_type/error/transport_attempts/transport_retry_policy/seed` — no `cache_prompt`. Likewise the
paper `failure_details` (`r1/headroom/e1b_collect.py:168-184`) keeps `llm_seed` but not the value. A
failed run therefore cannot be diagnosed for the setting from its own call record (the manifest still
has it). The author said "every … `llm_call` record": add it to the failure record too.

## 4. Checklist against the author's requirements

| # | Requirement | Status |
|---|---|---|
| 1 | `llamacpp` provider sends `cache_prompt` explicitly on every request, on the wire | **Partial** — harness paths yes (wire-verified, incl. retry); paper A4/EXAM/`ManagerQuestionPrior` no (R1) |
| 2 | Default is `false` | **Met** (`llamacpp_cache_prompt()`; test; host run returns `False`) |
| 3 | A config field makes it explicit | **Met** (`LLMConfig.cache_prompt`; `LLAMACPP_CACHE_PROMPT`; non-boolean rejected with `ValueError`) |
| 4 | Every manifest and `llm_call` record stores the value used | **Partial** — Track S manifest `manager` block and successful manager `llm_call` yes; `null` for non-llamacpp (R3); injected backend stub claims a value it did not send (R5); failed-call records no (R9); A4/EXAM records no (R1) |
| 5 | Pre-change records labelled "absent (= true, llama-server default)" wherever read/summarised | **Not met in code** — no reader/label; prose says "absent" (R6) |
| 6 | Works for Track X B1/B2 and future C3, not only Track S | **Partial** — harness manager path yes; C3-A4/EXAM no (R1) |
| 7 | Not merged into `r1` | **Met** — `origin/r1 = 897d83c`; branch separate; no rewrite observed |
| 8 | Fake-server test: field sent on every path (proposal, side query incl. A4/MQP, retry) | **Partial** — proposal, retry, `LangChainProposalBackend` yes; A4/MQP no |
| 9 | Test that the value lands in the records | **Met** (proposal-level; event not asserted, R7) |
| 10 | Full harness suite before and after, with counts | **Met** — 21/455/2/53 vs 21/465/2/53 clean-to-clean; 0 new failures; flaky toggle explained (R8) |
| 11 | Track S collector and pins use the new harness commit | **Partial** — collector yes; pins/status/wrappers not yet (R2) |
| 12 | Paper repo gets a new pin with no other code change | **Not yet** — `5e6a83c6` is the code change; the pin-only commit does not exist (R2) |

## 5. Could not verify

- Remote reflogs / server-side force-push history (no access); inferred from linear ancestry and an
  unchanged `origin/r1`.
- An actual S0.1 run against a real llama-server (no GPU job run, by instruction). The wire behaviour
  was verified against stand-ins and the host import/runtime wiring.
- The operator's exact commands and working directories for their counts; my reproduction shows the
  same numbers, but which state produced each number is inferred from the flaky test's mechanism.
- The full harness suite on the frozen host venv (pytest is not part of that venv's purpose); I ran the
  suite with `_harness_venv` on the Mac and the paper tests on both.

## 6. Verdict

The harness change itself is correct, minimal and well targeted: `cache_prompt` is in the wire body on
the real client, on the retry path, and on the schema path; the default is `false`; a non-boolean env
value is rejected; `model_kwargs` would indeed have raised; the record lands in the manager's
`llm_call` metadata and in the Track S manifest; the paper probe now posts the same shape; the suite
shows no new failure and the operator's counts reproduce (clean-to-clean: +10 passed, 0 new failures).
The S0.1 probe path in particular is verified end-to-end and is safe to run.

I cannot accept the change as complete, because the author's explicit side-query requirement is unmet:
the A4 observer (`r1/exam/observer.py`) and `ManagerQuestionPrior` (`r1/c3/prior_model.py`) send their
own hand-built bodies with no `cache_prompt`, are not covered by any test, and do not record the value —
so EXAM and C3-A4 runs under this pin would still see the non-determinism the ruling is meant to
remove, silently. The fix is small and local to the paper repo, and does not touch the verified harness
path. The pin/status wiring (R2) and the pin-only paper commit must also be completed as part of
pinning; the remaining findings are minor and should be recorded or fixed before the next use.

REVIEW VERDICT: NOT ACCEPTED

---

## Round 2

**Reviewer:** fresh independent reviewer (round 2; did not write the round-1 text and did not take the
operator's claims on trust). **Date:** 31 Oct 2026.
**Under review:** harness worktree `.claude-worktrees/harness-cacheprompt`, branch
`cacheprompt-20261031`, HEAD **`a3fedbb`**, base **`115df37`** (round 1 reviewed `987fb26`); paper
worktree `.claude-worktrees/trackS-ops-20261030`, branch `trackS-ops-20261030`, HEAD **`d10b05b7`**
(round 1 reviewed `5e6a83c6`). Both branches pushed: `origin/cacheprompt-20261031 = a3fedbb`,
`origin/trackS-ops-20261030 = d10b05b7`.
**Environment:** Mac `_harness_venv` (Python 3.11.11; harness editable at `harness-cacheprompt`), and
host `tasl7` frozen venv (Python 3.11.18) at `/home/dowling/r1_tracks/venv`.
**Labels:** ENGINEERING_ONLY; nothing here is evidence.

### 1. What changed since round 1

```
# harness, 987fb26..a3fedbb
src/autoresearch/control_plane/campaign.py   |  3 ++
src/autoresearch/llm/langchain_client.py     |  4 ++-
src/autoresearch/manager/langgraph_manager.py|  8 ++++-
tests/stage2/test_r1_cache_prompt.py         | 42 +++++++++++++++++++--
# paper, 5e6a83c6..d10b05b7
r1/c3/prior_model.py            | 26 +++++++++--
r1/exam/observer.py             |  4 +-
r1/tests/test_cache_prompt.py   | 99 +++++++++++++++++++++++++++
r1/tracks/probes/determinism.py |  7 +++
```

I re-read the incremental diffs and the surrounding code, then re-ran everything below. I did not
accept the new tests' names as evidence: I wrote my own stand-in HTTP server capture for the harness
manager/retry/schema/failure paths and a separate capture for the paper A4/EXAM paths.

### 2. Wire and record verification (my own captures, not the checked-in tests)

#### 2.1 Harness paths

With a real `ChatOpenAI` client against a stand-in `BaseHTTPRequestHandler` (my `/tmp/wire.py`), the
body received by the server was:

| path | body `cache_prompt` | record |
|---|---|---|
| `LangGraphManager` proposal, `llamacpp/qwen-manager` | `False` (`bool`) | `proposal.extra["llm_call"]["cache_prompt"]` is `False` |
| same manager, transport `drop`→`ok` retry (2 POSTs) | `[False, False]` | record `False` |
| same manager, `proposal_schema="manager_proposal/v1"` | `False`; `response_format.json_schema.name == "manager_proposal_v1"` | record `False` |
| `LangChainProposalBackend`, real client | `False` | extra carries `False` |
| injected stub manager | nothing sent | `llm_call` **omits** the key (not `null`) |
| injected stub `LangChainProposalBackend` | nothing sent | extra **omits** the key |
| 500-server, retry exhausted, through `_propose_logged` | 2 POSTs | `llm_call_failed` event payload contains `"cache_prompt": False` |

The failure-event check is important because no checked-in test covers it (N3 below). The value comes
from `langgraph_manager.py:485-491` (`exc.llm_call_cache_prompt = resolve_llm_config(self._model).cache_prompt`
only when no injected LLM) and `campaign.py:339-349`, which adds the key conditionally. The captured
event payload was:
`{'error_type': 'OpenAIAPIError', ..., 'seed': 2154865196, 'cache_prompt': False}`.

The successful `llm_call` event is now asserted in `test_the_llm_call_event_persists_the_value`, which
calls the real `_emit_llm_call` with a proposal whose `extra["llm_call"]` carries the value (R7). The
schema variant is now on the wire in `test_manager_proposal_schema_variant_carries_it_on_the_wire`.

#### 2.2 Paper A4 / EXAM paths

`r1/c3/prior_model.py:255-287` now resolves the value through the harness
(`from autoresearch.llm.providers import llamacpp_cache_prompt`) — one source of truth, not a second
default — posts it in `chat_client`'s hand-built body, and exposes it as `call.cache_prompt`.
`ManagerQuestionPrior` records it on both the success forecast (`prior_model.py:327`) and the
fallback forecast (`:321`); `SelfForecastObserver.observe` records it in its payload
(`r1/exam/observer.py:30`). My capture:

```
A4 WIRE body: {'model': 'r1-manager', 'max_tokens': 8, 'temperature': 0.0, 'seed': 0, 'cache_prompt': False} | False bool
A4 env-true WIRE cache_prompt: True
A4 Forecast cache_prompt: False  llm_calls: 1  wire: False
EXAM payload cache_prompt: False  wire: False
INJECTED A4 Forecast cache_prompt: None
```

`r1/scripts/c3_control_dryrun.py:201` builds one `llm = chat_client(runtime["llama_url"], ALIAS)` and
passes it to both the A4 arm (`:222`) and the `llm_self` arm (`:228`), so both share the fixed client;
no further code change was needed there. **Coverage caveat:** the dryrun arms are *not* directly
asserted by any test: the checked-in end-to-end dryrun test fails before reaching an arm in this
environment because `lightgbm` is absent (`ModuleNotFoundError: No module named 'lightgbm'`, confirmed
in the runner log; the host venv also lacks it). The underlying client/prior/observer are covered by
the 5 new paper tests. This is environment-only, not a regression.

**Residual record gap (N1):** the C3-A4 `Forecast.cache_prompt` is not carried into the controller's
persisted decision detail — `r1/c3/control.py:227-232` (`_fill`) builds the detail dict without it, and
`_decide_e1` (`:315-320`) persists that dict. The EXAM observer payload is persisted in the
`exam_self_forecast` event, but after a completed C3-A4 run the durable `control`/E1 record does not
state the setting; `LLMSelfController.log` does not either. The wire is correct; only the C3-side
record is incomplete.

#### 2.3 R6 probe report

I ran the probe itself (`determinism.main`, not just the unit tests) against my stand-in, once with
the new harness and once with the old `115df37` checkout:

```
new harness: cache_prompt: False  label: explicit  request_example.cache_prompt: False
old harness: cache_prompt: None   label: absent (= true, llama-server default)  request_example.cache_prompt: <absent>
```

So `r1/tracks/probes/determinism.py:323-329` produces the top-level field and the author's exact label.
Caveat (N5): the label is written only when a report is generated against a pre-change harness; old
report files already on disk are not retro-labelled. That is a summariser/documentation limitation,
not a wire defect, and it does not affect the pinned S0.1 run (which will record `False`/`explicit`).

### 3. Test counts I measured

| suite | command | result |
|---|---|---|
| new harness module | `pytest -q tests/stage2/test_r1_cache_prompt.py` | **12 passed** (3.27 s) |
| new paper tests | `pytest -q r1/tests/test_cache_prompt.py` (with `AR_HARNESS_ROOT=harness-cacheprompt`) | **5 passed** (2.67 s) |
| paper probe tests | `pytest -q r1/tests/test_tracks_probes.py` | **8 passed** (0.96 s) |
| full harness, clean base `115df37` | fresh `git clone`, `PYTHONPATH=.../src pytest -q --ignore=tests/test_legacy_noop_skip.py` | **21 failed, 455 passed, 2 errors, 53 subtests** |
| full harness, clean head `a3fedbb` | same, working clone | **21 failed, 467 passed, 2 errors, 53 subtests** |
| Track S suite on host `tasl7` | `AR_HARNESS_ROOT=work/harness_cp pytest -q r1/tests/test_tracks_*.py` in `work/paper_cp` | **169 passed** (264 s) |
| related C3/observer tests | `pytest -q r1/tests/test_c3_prior_model.py r1/tests/test_c3_rule_controller.py r1/tests/test_exam_observer.py` | **16 passed, 3 skipped** |

The full-suite failure sets are **identical** (sorted `FAILED`/`ERROR` lines diff empty); the delta is
**+12 passed**, exactly the 12 new harness tests (the 10 that existed at `987fb26` plus the 2 added at
`a3fedbb`). The 2 errors are the same `TestResumedCommitSemantics` tests; the 53 subtests are
unchanged. This is the corrected R8 statement: clean-to-clean the true delta at round 1 was +10
passed, and it is +12 now, not a `21/455 → 20/466` before/after. The operator's earlier numbers
reproduce only as clean-run vs same-clone rerun of the pre-existing flaky
`test_checked_in_report_contains_all_plan_campaigns`; I did not accept them as a clean comparison.

Environment-only failures observed: the C3 control-dryrun test fails on the Mac venv (and on the host
venv) at `import lightgbm`, before any arm runs; this is not caused by the change and is excluded
from the counts above. No other environment-only failures appeared in the measured suites.

Pin coupling re-confirmed: the new paper tests fail against the old harness (`test_cache_prompt.py`
4 failed/1 passed, `test_tracks_probes.py` 2 failed/6 passed on `115df37`), so the paper commits do
depend on the new harness pin.

### 4. R4 / R8 record checks

- **R4 confirmed.** `manager` is in `MANIFEST_KEYS` (`r1/tracks/collect.py:1275-1280`) and the resume
  guard compares it (`:2092-2094`). A pre-change llamacpp manifest has no `cache_prompt` in its
  `manager` block, so the new manifest differs and `collect` exits with `refusing to resume … manager
  differs`. The 5e6a83c6 commit message states this ("a resume under a different setting is refused by
  the existing manifest diff"). The explicit "use fresh output directories" wording is not yet in
  STATUS/PLAN (N-footnote; recommend the pin-step record add it).
- **R8 confirmed.** Round 1's correction is right: the true clean delta was +10 passed with identical
  failures, not a 21/455 → 20/466 clean before/after; at `a3fedbb` it is +12 with identical failures.
  No operator record restates the wrong numbers now.

### 5. Disposition R1–R9

| # | Round-1 severity | Round-2 disposition | Evidence |
|---|---|---|---|
| R1 | BLOCKING | **FIXED** | A4 `chat_client` posts `cache_prompt` from the harness (wire-captured `False`, env-true `True`); `ManagerQuestionPrior` forecast and `SelfForecastObserver` payload record it; `c3_control_dryrun` A4/`llm_self` share the same client; 5 new stand-in-server tests pass. Residual persisted-record gap N1. |
| R2 | MAJOR | **STILL OPEN (pin step)** | `trks-status` still `PAPER_SHA=9bb64ba` / `HARNESS_SHA=115df37` and checks `work/Agent_paper_B` / `work/autoresearch_harness`; `r1/tracks/ops/trks:4-5` and `r1/tracks/ops/diag/trks-diag:6,9` export the old `AR_HARNESS_ROOT` and cd to the old paper; host `bin/trks`/`bin/trks-diag` likewise; host old checkouts are `115df37`/`9bb64ba`, new `harness_cp`=`a3fedbb`/`paper_cp`=`d10b05b7`; frozen venv `.pth` → old harness. No pin-only paper commit exists; HEAD `d10b05b7` is the code change. |
| R3 | MINOR | **FIXED** | `langgraph_manager.py:570-577` adds the key only when `llm_cache_prompt is not None`; `langchain_client.py:87-88` only when no injected LLM and a non-None config. Captured: injected manager `llm_call` has no key; injected backend has no key; `resolve_llm_config("ollama/…").cache_prompt is None` and the graph carries none. |
| R4 | MINOR | **FIXED (record confirmed)** | `manager` in `MANIFEST_KEYS`; resume diff at `collect.py:2092-2094`; commit 5e6a83c6 records the refusal. Add the "fresh output directories" sentence to the pin-step STATUS entry. |
| R5 | MINOR | **FIXED** | `LangChainProposalBackend` now records the value only when `self._llm is None`; injected stub extra contains no `cache_prompt`. |
| R6 | MINOR | **FIXED** | Probe run against the new harness gives top-level `cache_prompt: False` + `cache_prompt_label: "explicit"`; against old `115df37` gives `None` + the exact `"absent (= true, llama-server default)"` label. N5 caveat on old report files only. |
| R7 | MINOR | **FIXED** | `test_the_llm_call_event_persists_the_value` asserts the real `_emit_llm_call` event payload; `test_manager_proposal_schema_variant_carries_it_on_the_wire` asserts the `manager_proposal/v1` body on the stand-in wire. 12/12 pass. |
| R8 | MINOR | **FIXED (record confirmed)** | Clean base 21/455/2/53 vs clean head 21/467/2/53; failure sets identical; true delta +12 (was +10 at round 1). |
| R9 | MINOR | **FIXED (event); paper residual N2** | My 500-server run through `_propose_logged` produced `llm_call_failed` with `"cache_prompt": False`; `campaign.py:339-349` adds it conditionally. The paper `failure_details` records still omit it (N2), and no checked-in test asserts the failed event (N3). |

### 6. New findings

- **N1 — MINOR (C3 record, not wire).** The C3-A4 forecast value is in the `Forecast` object and tests,
  but is not persisted in the controller decision detail (`r1/c3/control.py:227-232`, persisted at
  `:315-320`), and `LLMSelfController.log` does not carry it either. A completed C3-A4/`llm_self` run
  therefore cannot state the setting from its own durable record. One-line fix in `_fill` (and
  optionally a dryrun check); does not affect the S0.1/Track S manager path.
- **N2 — MINOR (paper failure records).** `r1/headroom/e1b_collect.py:168-184` still keeps
  `llm_seed` but not `cache_prompt`; `r1/tracks/collect.py:244-247` has neither. The harness
  `llm_call_failed` event is fixed, but a paper-level failure JSON still omits the value.
- **N3 — MINOR (test gap).** No checked-in test drives a failed call and asserts
  `llm_call_failed.cache_prompt`; I verified it by hand. Add the case to
  `tests/stage2/test_r1_cache_prompt.py` (the existing transport-retry test asserts the event but not
  this field).
- **N4 — INFO (coverage).** `r1/tests/test_c3_control_dryrun.py` cannot execute in the supplied
  environments (missing `lightgbm`), so the A4/`llm_self` dryrun arms are not exercised end-to-end;
  the shared client is covered directly. Environment-only.
- **N5 — INFO (R6 wording).** The `"absent (= true, llama-server default)"` label is emitted when a
  report is generated against a pre-change harness; existing report files are not rewritten. No
  summariser currently reads old records, so this is documentation-only.

### 7. Scope and safety

- No merge into `r1`: harness `origin/r1 = 897d83c`; `115df37` is not an ancestor of `origin/r1`;
  `origin/cacheprompt-20261031 = a3fedbb`; the reviewed branch is a linear descendant of `115df37`
  (3 commits: `987fb26`, `382cbab`, `a3fedbb`). Paper branch pushed at `d10b05b7`; `origin/r1` is a
  harness ref, not a paper ref.
- No force-push is claimed: I can see only linear ancestry and unchanged refs, not the server reflog.
- The diffs change only the intended setting and its records: the harness edits are the provider
  config/body, the manager's success/failure records, the event payload and tests; the paper edits are
  the A4 client/forecast, the EXAM payload, the probe report and tests. `git diff --check` passes on
  both ranges.
- The default really is `false` (`llamacpp_cache_prompt()` with `NO_KEYS`; wire-captured `False`), and
  the value is on the wire for the manager, the retry, the schema variant and the A4 client.

### 8. Could not verify

- A real llama-server/GPU S0.1 re-run (not run, by instruction); all wire evidence is against
  stand-ins and the host import/runtime wiring.
- Server-side reflog / force-push history (no access); inferred from linear ancestry and unchanged
  refs.
- The `c3_control_dryrun` A4/`llm_self` arms end-to-end (missing `lightgbm` on both the Mac and host
  venvs).
- A full paper-suite run; I ran the required Track S/probe/cache suites plus the related C3/observer
  tests and the full harness suite.

### 9. Verdict

The blocking round-1 finding is genuinely fixed and independently wire-verified: the A4 observer,
`ManagerQuestionPrior` and both dryrun arms that receive `chat_client(...)` now send
`cache_prompt` resolved from the harness, and the EXAM/forecast records carry it. R3/R5/R6/R7/R9 are
fixed in code and by the measured tests; R4/R8 are accurately stated; the harness suite is clean
(21/455/2/53 → 21/467/2/53, identical failure sets, +12 passed). The only substantive item still
outstanding is R2: the pin/status wiring still points at `115df37`/`9bb64ba` and there is no
pin-only paper commit. That is the pin step the acceptance authorises, not a defect in the reviewed
commits, but it must be completed — and the `trks`/`trks-status` wrappers and host checkouts moved to
`a3fedbb`/`d10b05b7` — before the S0.1 re-run is launched, or the operator would silently run the old
code. The residual N1–N3 record/test gaps are minor, concern C3/paper failure records rather than
the S0.1 path, and do not withhold acceptance.

REVIEW VERDICT: ACCEPTED
