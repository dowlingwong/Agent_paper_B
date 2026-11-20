# Review: harness-defaults check `6adf385` → `a3fedbb` (20 November 2026)

Reviewer: a fresh, independent agent (Claude, AI-assisted). I judged from the code only. I read the harness diff in the clone at `scratchpad/harness` with `git diff`, `git show` and `git log`, without changing its checkout. I read the paper repo at `origin/main` @ `3a6dcf4d` with `git show` and `git grep`. I ran nothing on a host and ran no tests.

Report under review: `docs/r1/reports/sweep2_20261116/HARNESS_DEFAULTS_CHECK_20261120.md` (untracked in the `wt_hdc` worktree, on top of `3a6dcf4d`).

## What I checked and how

1. **Commit list.** `git merge-base --is-ancestor 6adf385 a3fedbb` is true. Both full SHAs match the report. `git log --format='%h %p %s' 6adf385..a3fedbb` gives exactly five commits, each with a single parent, in a linear chain `6adf385 → f8bc222 → 115df37 → 987fb26 → 382cbab → a3fedbb`. The subjects match the report's table. **The list is complete.**
2. **Size.** `git diff --shortstat 6adf385 a3fedbb -- src` gives 6 files, 265 insertions and 12 deletions. Across the whole repo, the only other files are `tests/stage2/test_r1_cache_prompt.py` and `tests/stage2/test_r1_track_s_arms.py`. Nothing in `pyproject.toml`, `uv.lock`, `nodes/` or the configs changes. **This matches the report.**
3. **Every hunk of `git diff 6adf385 a3fedbb -- src`**, checked against the report's table:
   - `control_plane/campaign.py`:
     - The `llm_call_failed` payload gets `cache_prompt` only when the exception carries a non-None value.
     - `run_real_campaign(controller_ledger_view=None)` is new. `_controller_prefix` returns the same list object when the view is `None`.
     - The view is applied at five call sites: the E0 `build_control_view`, two E1 sites, and two E2 sites. One of the E2 sites is the `resolve_keep_prior` view.
     - **Matches.** The report does not mention that the keep-prior view is also wrapped, but that changes nothing by default.
   - `control_plane/snapshot.py`:
     - New: `ArmOverride`, `_as_arm`, `_forced_decision`, `RestoredCampaign.shadow_record=None` and `ResumeResult.shadow_record=None`.
     - `_complete_captured_trial(arm=None)`: every new branch is guarded by `arm is not None`.
     - The `branch_trial_committed` payload is unchanged when `arm is None`.
     - `resume_campaign` changes `first_action` from a required argument to `str | None = None`. It raises if both `first_action` and `arm` are missing. A caller that passes `first_action` gets the old path.
     - **Matches.**
   - `manager/langgraph_manager.py`:
     - `seed_key=None` is new. `manager_seed` uses `status.campaign_id` when `seed_key` is `None`, so the D26 seed is unchanged.
     - `llm_meta["cache_prompt"]` is set only when the value is not None.
     - `exc.llm_call_cache_prompt` is set inside the existing `try/except Exception`.
     - The new `resolve_llm_config` call in `_build_graph` runs right after `_resolve_llm()`, which already calls it. So it adds no new way to fail.
     - **Matches.**
   - `memory/summarizer.py`:
     - New: `hidden/v1` and `reason/v1`, `SKIP_REASON_TEXTS`, `skip_reason_text` and `_skip_reason_line`.
     - When `skip_display` is not `hidden/v1`, `shown` is `records`. `line_of` gains a `reason/v1` branch only.
     - `raw_text` still serialises all records.
     - **The conclusion matches, but the description is wrong (m1 below).**
   - `llm/providers.py`:
     - New: `LLMConfig.cache_prompt: bool | None = None`, `LLAMACPP_CACHE_PROMPT_ENV` and `llamacpp_cache_prompt()`. The function returns `False` for unset, `""`, `0`, `false`, `no` or `off`, returns `True` for the true spellings, and raises otherwise.
     - `resolve_llm_config` sets the value for the `llamacpp` prefix only.
     - **Matches.**
   - `llm/langchain_client.py`:
     - Inside the `provider == "llamacpp"` branch of `_build_chat_model`, `extra_body["cache_prompt"] = bool(config.cache_prompt)` is set whenever the value is not None.
     - `LangChainProposalBackend` records the value only when it builds the model itself (`self._llm is None`).
     - **Matches.**
4. **Defaults the report might have missed.** I looked for any path where an unchanged call still behaves differently:
   - **Control view hash.** `ControlView.input_hash` uses `record_digest`: trial_id, budget_index, decision, parsed_metrics and delta_vs_best. It also uses `proposal_digest`, which does not include `llm_call`. So the new record field does not change any controller input hash.
   - **Memory context.** The new field reaches the trial ledger via `extra.manager = proposal_extra` (`campaign.py`, the record builder at about l.2409). `build_memory_context` uses `raw_text` only for `raw_memory_chars` and `compression_ratio`. On the sweep path neither is emitted: `memory_context_built` carries only `compressed_chars`, and the only reader is `evaluation/ablations.py`. The summary lines do not include `extra`. **So the manager prompt is unchanged.**
   - **Skip validation.** `check_skip_display` now also accepts `hidden/v1` and `reason/v1`, which raised before. This is an opt-in widening, not a default change.
   - **Result.** I found no default change on the sweep path besides the declared `cache_prompt: false`.
5. **Can the new options be reached on the sweep path (paper `origin/main`)?**
   - `sweep2/s2_c2_lib.py` `collector_argv` runs `python -m r1.headroom.e1b_collect` with `--manager langgraph --roots-only --points --reps 0 --manager-model llamacpp/<alias> --new-campaign-versions …`. `s2_c2_lib.py` also enforces `B2_HARNESS = a3fedbb…`, and `r1/scripts/HARNESS_PIN_C3` is `a3fedbb…`.
   - `r1/headroom/e1b_collect.py` `_run_root` calls `run_real_campaign` with:
     - no `controller`, so the default is `ContinueController` (`continue/v1`, always continue, hence no control-plane skips);
     - no `skip_display`, no `keep_prior`, no `proposal_observer` and no `controller_ledger_view`;
     - `action_versions` only, through `_versions_kwargs`, which refuses a version that needs a prior.
   - `make_manager` builds `LangGraphManager(model, temperature, repetition, transport_retry[, proposal_schema])`, with no `seed_key`.
   - `resume_campaign` is called only in `run_leaf`. `--roots-only --points --reps 0` creates no leaf jobs, so the fork arms cannot be reached.
   - `_worker_env` pops `LLAMACPP_CACHE_PROMPT` (and `LLAMACACHE_PROMPT`, which the harness does not read) from the environment used for both the liveness run and the collector run.
   - `git grep` over `r1/` and `sweep2/` on `origin/main` finds no use of `seed_key`, `controller_ledger_view`, `ArmOverride`, `hidden/v1` or `reason/v1`. The only `skip_display` user is `r1/c3/control.py` `campaign_kwargs` (`one_line/v1`), which belongs to the C3 arms and is not the label-campaign path.
   - **The report's claims "not used by label campaigns" and "sweep 2 has no control-plane skips" therefore hold.**
6. **Binding rows.**
   - `PLAN.md` R1-MAIN-PROPOSER (c) ends: "a check that the harness defaults used by the sweep are unchanged is part of prerequisite 3". Its first bullet lists `cache_prompt` at the default against explicit false as a stack difference.
   - (g)3 reads: "The harness pin carrying the `cache_prompt` switch, and the paper-side sweep change passing the thinking policy and server flags, both reviewed."
   - R1-SWEEP2-SETTINGS (1) requires `cache_prompt` false on every request.
   - The draft note (v6) has precondition 9, "Harness-defaults check (R1-MAIN-PROPOSER (c)): `<report>`". Its Harness section asks for `<check, report, review>`, and its "Disclosed differences" list includes both "`cache_prompt` at the default against an explicit false" and "the harness pin `6adf385` against `a3fedbb`".
   - The report's conclusion is consistent with all of these.

## Findings

### Blockers

None.

### Major

None.

### Minor

- **m1. The summarizer row misdescribes the default.**
  - The report says `build_memory_context(skip_display=None)` "default keeps the previous one-line display".
  - In fact `None` is the historical generic record line (`_summary_line`). `one_line/v1` is a separate opt-in display that already existed at `6adf385` (R1-SKIP-DISPLAY), and the harness docstring says so: "*skip_display* `None` (default) keeps the historical memory display".
  - The conclusion still holds, because the `None` path is byte-identical. Fix the wording to: "`skip_display=None` keeps the historical display; `one_line/v1` (pre-existing) and the new `hidden/v1` / `reason/v1` are opt-in."
- **m2. The reachability claims cite no evidence.**
  - "Not used by label campaigns", "sweep 2 has no control-plane skips" and "Sweep-2 jobs must not set `LLAMACPP_CACHE_PROMPT`" are stated without pointing to the code that makes them true.
  - I verified all three (point 5). The report should cite:
    - `sweep2/s2_c2_lib.py` `collector_argv` (`--roots-only --reps 0`, `llamacpp/` manager) and `_worker_env` (pops `LLAMACPP_CACHE_PROMPT`);
    - `r1/headroom/e1b_collect.py` `_run_root` (no `controller`, `skip_display`, `keep_prior` or `controller_ledger_view`; default `ContinueController`) and `make_manager` (no `seed_key`);
    - `resume_campaign` being reached only from `run_leaf`.
  - It should also say that the wrapper enforces "must not set" by unsetting the variable, not just by procedure.
- **m3. Say where the record fields land.**
  - "The value is recorded" and "additional record fields" are correct but vague. `cache_prompt` appears in:
    - the `llm_call` event payload;
    - the trial ledger at `extra.manager.llm_call.cache_prompt` (`root_trials.jsonl`), via `proposal_extra`;
    - the `llm_call_failed` event.
  - It is omitted for non-llamacpp providers and injected LLMs.
  - Sweep-1 records lack the key: R1-CACHEPROMPT-FALSE labels it "absent (= true, llama-server default)". Any byte-level or schema comparison of sweep-1 and sweep-2 ledgers will see this difference.
  - None of this affects the prompt or the controller hash (point 4). One sentence would make that explicit.
- **m4. Scope relative to (g)3 and precondition 9.**
  - The report says it is "required by … (g)3". (g)3 itself requires two reviewed items: the harness pin carrying the switch, and the paper-side sweep change for the thinking policy and server flags. The defaults check is made "part of prerequisite 3" by (c), not by (g)3's own text.
  - The report should say it discharges only the defaults-check part of (g)3. It covers neither the review of the harness pin (that is R1-CACHEPROMPT-FALSE round 2 / R1-EXAM-B1-HARNESS-PIN at `a3fedbb`) nor the paper-side change.
  - The note's Harness section asks for `<check, report, review>`. Precondition 9 is therefore filled by this report together with this review, not by the report alone.
- **m5. A citation cannot be checked on `origin/main`.** The report says it is "cited by the sweep-2 note's 'evidence before approval'". No document on `origin/main` contains the phrase "evidence before approval". The v6 draft refers to the check in its Harness section, precondition 9 and note 6. Either point to the actual section, or name the unpublished note that has that heading.

### Informational (no change required)

- **i1. Recorded value and sent value are resolved at different times.** In `LangGraphManager`, the recorded `cache_prompt` is resolved once, when the graph is built (`_build_graph`). The value actually sent is resolved per call (`_resolve_llm(seed=…)`). The two can differ only if `LLAMACPP_CACHE_PROMPT` changes within a process, which the wrapper rules out by unsetting it.
- **i2. Bad values now raise.** A malformed `LLAMACPP_CACHE_PROMPT` now makes `resolve_llm_config` raise `ValueError` for `llamacpp/` models. This is new, but only for a non-default environment.
- **i3. Latency changes, and the layout already reflects it.** The declared change also changes latency: R1-CACHEPROMPT-FALSE measured +6.06 % (digits) and +6.27 % (tabular). The sweep-2 layout and projection were measured at `a3fedbb` (B2, the S2-C3 replay and the smoke runs), so they already include it. This is not a separate default.

## Assessment

The report's central claim holds. It identifies the five commits and the six source files correctly. Its per-file conclusions match every hunk. Between `6adf385` and `a3fedbb`, the only default-behaviour change on the sweep-2 label-campaign path is the explicit `cache_prompt: false` on llama.cpp requests, plus additional recorded fields. That change is declared (R1-CACHEPROMPT-FALSE, R1-MAIN-PROPOSER (c) first bullet, R1-SWEEP2-SETTINGS (1), and the draft note's disclosed differences).

None of the new options (`controller_ledger_view`, the `resume_campaign` arms, `seed_key`, `hidden/v1` / `reason/v1`, `LLAMACPP_CACHE_PROMPT`) can be reached from `sweep2/s2_c2_lib.py` → `r1.headroom.e1b_collect --roots-only`. The minors are about the precision of one row's wording, citing evidence, and scope relative to (g)3 and precondition 9. None of them changes the conclusion.

Verdict: ACCEPTED WITH MINORS
