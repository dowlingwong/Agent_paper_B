# Harness-defaults check for sweep 2: `6adf385` → `a3fedbb` (20 November 2026)

Written by the coordinating chat (Claude, AI-assisted). Desk check only; nothing was run on a host. Required by R1-MAIN-PROPOSER (c) and (g)3 and by precondition 9 of the S2-M1 v6 draft (`proposals/C3_SWEEP2_AUTHORIZATION_NOTE_DRAFT_20261116.md`); to be cited by the sweep-2 authorization note (`authorizations/c3_sweep2_20261119.md`, its "Evidence to publish before approval" section).

## Question

Sweep 2 runs the harness at `a3fedbb` (`a3fedbbd44309b3fdf99d853ad841b9ec2c299e2`); the sweep-1 B.2 audit pins `6adf385` (`6adf3859de66c4814fcf376eed59880fbd8eeaf7`). Do the harness defaults that the sweep-2 label campaigns use differ between the two, other than the declared `cache_prompt` change?

## Method

`6adf385` is an ancestor of `a3fedbb`. `git log 6adf385..a3fedbb` lists five commits:

| Commit | Subject |
|---|---|
| `f8bc222` | Track S: fork-arm overrides in resume_campaign, controller ledger view, skip displays hidden/v1 and reason/v1 |
| `115df37` | Track S: optional seed_key for the LangGraph manager's D26 seed |
| `987fb26` | llm: send cache_prompt explicitly on every llamacpp request (default false) |
| `382cbab` | llm: omit cache_prompt when the backend does not carry it; cover the event and the schema variant |
| `a3fedbb` | llm: record cache_prompt on the failed-call event too (review R9) |

`git diff --stat 6adf385 a3fedbb -- src` touches six source files (265 insertions, 12 deletions); the remaining changes are two new test files. Every hunk was read.

## Findings, by file

| File | Change | Default behaviour on the sweep path |
|---|---|---|
| `control_plane/campaign.py` | new keyword `controller_ledger_view` (default `None`); `_controller_prefix` returns the prefix unchanged when it is `None`; failed-call event records `cache_prompt` when the backend carries it | unchanged except the added record field |
| `control_plane/snapshot.py` | `resume_campaign` gains optional `arm`, `first_action` and shadow-record handling (Track S fork arms) | not used by label campaigns; defaults (`None`) keep the previous path |
| `manager/langgraph_manager.py` | optional `seed_key` (default `None` = campaign id, the previous D26 seed); records `cache_prompt` per call | D26 seed unchanged by default |
| `memory/summarizer.py` | new opt-in skip displays `hidden/v1`, `reason/v1` next to the existing opt-in `one_line/v1`; with `skip_display=None` the summarizer keeps the historical generic display | unchanged; sweep 2 passes no `skip_display` and has no control-plane skips |
| `llm/providers.py` | `LLMConfig.cache_prompt`; for `llamacpp` it is `False` unless `LLAMACPP_CACHE_PROMPT` says otherwise | **changed by design**: llama-server's default `cache_prompt=true` is replaced by an explicit `false` |
| `llm/langchain_client.py` | sends `cache_prompt` in `extra_body` on every llamacpp request; records it | as above |

## Reachability on the sweep path (sweep-2 wrapper on `main`)

`sweep2/s2_c2_lib.py` runs `r1.headroom.e1b_collect --roots-only --reps 0` with a `llamacpp/` manager (`collector_argv`). `_run_root` passes no controller (always continue, nothing skipped), no `skip_display`, no keep prior and no `controller_ledger_view`; `make_manager` passes no `seed_key`; `resume_campaign` is reached only from `run_leaf`, which `--roots-only --reps 0` never runs; `_worker_env` unsets `LLAMACPP_CACHE_PROMPT` before the collector and liveness runs. None of the new options is reachable.

`cache_prompt` is recorded in the `llm_call` event, in the trial ledger (`extra.manager.llm_call`) and in the failed-call event. Sweep-1 records do not carry the key, so ledger comparisons across the sweeps show this field difference.

## Conclusion

The only change to default behaviour between `6adf385` and `a3fedbb` on the sweep-2 path is that every llama.cpp request now sends `cache_prompt: false` explicitly and the value is recorded. This is the declared R1-CACHEPROMPT-FALSE setting, and R1-MAIN-PROPOSER (c) already lists it as a sweep-1 vs sweep-2 stack difference (sweep 1 ran at the llama-server default). All other changes are opt-in Track S features whose defaults reproduce the earlier behaviour, plus additional record fields. No other harness default used by sweep 2 differs. The wrapper unsets `LLAMACPP_CACHE_PROMPT`, so jobs run with the default `false` that R1-SWEEP2-SETTINGS requires.

Scope: this report, with its independent review (`reviews/HARNESS_DEFAULTS_CHECK_REVIEW_20261120.md`), is the defaults check that R1-MAIN-PROPOSER (c) adds to prerequisite 3 and that S2-M1 v6 precondition 9 asks for. The other two items of (g)3, the reviewed harness pin and the reviewed paper-side sweep change, are separate and are cited in the note's P2 (the sweep-2 integration reviews on `main`).
