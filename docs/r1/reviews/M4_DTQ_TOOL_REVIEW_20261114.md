Reviewed base: 0aa4bc00a744099b9a27362c5b779862eed26d8a

# M4 step 4 DTQ tool — independent review record (14 November 2026)

MAC_OVERNIGHT_RUNBOOK_20261113 Unit 8.2. Branch `mac-m4-dtq-20261114` from `mac-m4-20261109` @ `5cd32efc`; the Track S probe copied byte-identically from `d10b05b7` (no merge, no rebase). Two rounds by one freshly spawned independent reviewer agent (AI-assisted, Claude).
- Round 1: changes requested (three blocking: a mid-run co-tenant did not stop the run and a pass was still printed; the projection omitted the CPU term of RUNBOOK B.1b prerequisite 6; instance disjointness from the exam was neither checked nor disclosed).
- Round 2: **accepted** at `0aa4bc00`.

Accepted commit (round 2, last): 0aa4bc00a744099b9a27362c5b779862eed26d8a

Round-2 notes, not blocking (follow-ups): the 50 × 3 test exits through the text-overlap STOP and does not isolate the guard; the unreadable-nvidia-smi-during-run STOP has no test (the code was checked by the reviewer's scratch test); a STOP reports `identity_1: false` for an unmeasured identity; the ledger match is exact-case and one exam row with a ledger suffices; giving only some CPU-term flags is accepted silently; one transient unreadable sample aborts a run; an in-flight call (up to 600 s) finishes before the server stops; the report's §4 omits the `--dry-run` guard, full probe source commit/blob in the JSON and the co-tenant gap during model load.

The round texts are reproduced unchanged below.

---

# Independent review — M4 step 4, DTQ tool (Unit 8.2), round 1

Reviewed commit: 952d20c0fba453a309840053e31f27c4e44ca1d0

Branch `mac-m4-dtq-20261114`, single parent `5cd32efcae6524f8aabfd70dfe95b1d257874d85` (= `gh/mac-m4-20261109`). Read-only review. Scratch was under `/tmp/rev_u82`, now removed. No network, no GPU.

Spec read: MAC_LOCAL_RUNBOOK_20261104 M4 steps 4–5 (5cd32efc); OPERATOR_RUNBOOK_20261104 O5; PLAN R1-BX-PROPOSED-CONFIRM (REVISIONS (f)) and R1-EXAM-OFFLOAD-ROUTE; RUNBOOK B.1b (manager/server settings, prerequisite 6 "Projection"); MAC_M4_PARTIAL_HANDOFF_20261109 §6 and Q3; MAC_OVERNIGHT_RUNBOOK_20261113 §8 item 2 (69b3576b); accepted runbook review S10 / interpretation 9.

## What checks out

- **Byte identity.** `r1/tracks/__init__.py` (9ce553f4), `r1/tracks/probes/__init__.py` (ab8f105b) and `r1/tracks/probes/determinism.py` (f2c1bb79) have the same blob ids at 952d20c0 as at `d10b05b738fc0e0dba54e0e692c248bedf095482`. No other Track S file was brought in. The base had no `r1/tracks/`. The commit has one parent, so there was no merge and no rebase. `d10b05b7` is an ancestor of `gh/mac-tracks-a2u-stale-20261111`.
- **B.1b settings in argv.** These were checked through `LlamaServerInstance`: `-c 16384`, `-np 1`, `--split-mode layer --tensor-split 1,1`, `CUDA_VISIBLE_DEVICES=u1,u2`, `--jinja --cache-type-k q8_0 --cache-type-v q8_0 -lv 4`, and `--chat-template-kwargs {"enable_thinking":false}`. The extra-args order equals the exam's `EXAM_SERVER_ARGS` (R1-EXAM-OFFLOAD-ROUTE).
- **Request body.** Temperature 0.2 and `manager_proposal/v1` match R1-MAIN-PROPOSER (b) and the sweep-1 config. The body comes from the harness through the probe's `chat_payload`, and explicit `cache_prompt: false` is enforced.
- **Seeds.** D26 seeds from the prompt file reach the server; the fake's call log confirms this.
- **Offload and recorded results.** Offload goes through `inst.offload()` → `offload_check_dual` (both routes). An OOM at start and a partial offload are recorded results with exit 0.
- **Co-tenant at start.** It is a STOP before any server starts. An unreadable nvidia-smi is a STOP outside `--dry-run`.
- **Server cleanup.** The server is stopped in `finish()` and again in the outer `finally`.
- **Computations.** Identity, latency mean/p95 and completion-token stats reuse the probe's functions correctly. An errored repeat counts as not identical.
- **Projection inputs.** `DEFAULT_CAMPAIGNS = 288` matches 8 nodes × 18 instances × 2 memory modes (R1-MAIN-PROPOSER (b)).
- **Nothing can feed Track X selection.** The tool writes only into a fresh `--out-dir` with the label `ENGINEERING_ONLY`/`DRYRUN` and `informational: true`. It reads nothing from, and writes nothing to, `r1/exam/` rules, the registry or exam outputs.
- **Fake server change.** The one-token change to `c3_fake_llama_server.py:79` (accept `-lv <n>`) is minimal and needed. The fake is not a B1 protected path (`mac-b1-r4-20261109:r1/exam/runtime.py:571`). `llama_server_instance.py` is untouched, so B1 separation (hand-off §6) is unaffected.
- **Tests.** The requested command at the tip gives **118 passed** (14 new + 104 existing). The same 104 existing tests pass at base `5cd32efc`.
- **Existing tests unchanged.** Broader run `r1/tests -k "llama or fake or probe or dryrun or sweep"` in detached worktrees, same harness pin `a3fedbb`:
  - base: 22 failed, 174 passed, 9 skipped, 690 deselected;
  - tip: 22 failed, 176 passed, 9 skipped, 702 deselected.

  The two failure sets are **identical by test id**. The tip's extra 2 selected and 12 deselected tests are the 14 new ones. No existing test file changed.

## BLOCKING

**B1. A co-tenant that appears during the run is not a STOP, and the run still reports `pass: true`.**
`r1/scripts/dt_dualcard_qualify.py:118-150` and `:306-321`.
- The sampler only collects intruder rows. The replay keeps running to the end, so the server stays loaded on a card that another user now shares. `dtq` is evaluated anyway, and the printed summary shows a pass next to the STOP status.
- **Reproduced** with the fake server and fake nvidia-smi (scratch test): an intruder on card 2 was injected after call 2 of 18. All 18 calls were still served, and the tool printed `{"status": "STOP_co_tenant_during_run", "pass": true}` (exit 2).
- In a non-dry run, an nvidia-smi that becomes unreadable during the run (`sampler.unread`, with `samples == 0`) leaves the co-tenant check and the peak memory vacuous, yet the status is `complete`.
- O5 says "A co-tenant appearing during the run is a STOP". The tool docstring (l. 8) and the report `docs/r1/reports/M4_DTQ_TOOL_20261114.md:29` claim this is implemented.
- There is no end-to-end test of this path. `test_memory_sampler_tracks_the_peak_and_flags_intruders` only unit-tests sampling.

*Fix:*
- Set a `threading.Event` on the first intruder, check it before every call in `replay`, and abort the replay at once. The server is then stopped by `finish`.
- On any `STOP_*` status, do not apply the criterion: `dtq.pass` should be `None` (or the `dtq` block omitted), and so should the printed `pass`.
- Outside `--dry-run`, treat zero readable samples during the run as `STOP_nvidia_smi_unreadable` (or an explicit threshold of unreadable samples).
- Dedupe intruder rows by (pid, uuid), with first and last seen.
- Add an end-to-end test that injects an intruder mid-run. It should assert: fewer calls served than scheduled, the STOP status, `pass` not `True`, and the server stopped.
- Correct report l. 29.

**B2. The projection formula is not the governing one, so the 4-day criterion is evaluated on a lower bound.**
`dt_dualcard_qualify.py:198-211` and `:315-318`; report `:28` and `:53-54`.
- RUNBOOK B.1b prerequisite 6 (`5cd32efc:docs/r1/RUNBOOK.md:175`) defines the projection as "Calls × the pick's thinking-off latency + runs × CPU time / workers". The same 4-day STOP applies to the two-TITAN configuration.
- The tool computes only `campaigns × calls_per_campaign × mean latency` and sets `projection_le_4_days` and `pass` from that. `pass` can therefore be `True` when the defined projection is over 4 days.
- The report's §4 says worker time would need "a definition of the overlap". That is inaccurate: the formula is already defined, and it is additive.

*Fix:*
- Implement the RUNBOOK formula. Add explicit inputs `--runs` (or campaigns × W stated by the operator), `--cpu-seconds-per-run` and `--workers`, and record both terms and their sum.
- Evaluate `projection_le_4_days` on the sum.
- If the CPU term is not supplied, report the LLM term as a lower bound and leave the projection criterion and `pass` as `None` (not evaluated), never `True`.
- Update the docstring (l. 32-34), report §2 row l. 28 and §4 l. 53-54. Add a test for the full formula and for the `None` path.

**B3. Disjointness from the exam's instances is neither checked nor disclosed, and the text check can be silently vacuous.**
`dt_dualcard_qualify.py:69-108`; docstring l. 27-29; report l. 25.
- O5 requires the prompts to be "disjoint from the exam's frozen prompt sets **and instances**". The tool compares only whitespace-normalised prompt text. Each replay row's `source` is free text and is never compared with anything.
- The exam's frozen rows carry `node`, `ledger_path`, `ledger_sha256` and `trial_id` (`r1/exam/stage_a.py:19-38`), so an instance-level check is possible.
- An exclude row with neither `prompt` nor `messages` adds nothing, with no error (`_texts` returns `[]`). A wrong or reshaped file then makes the check vacuous while the report shows `overlap: 0`.
- The docstring states "so the replay set is disjoint from the exam (O5)", and the report drops "and instances".

*Fix:*
- Require structured provenance per replay row: the sweep-1 ledger path/sha and trial id, or node + instance seed + memory mode.
- Refuse any replay row whose instance (ledger / campaign instance) occurs among the exam rows.
- STOP if any exclude row yields no prompt text or no instance key, and record the count of instance keys.
- Add a test for each case.
- If the author must first define "instance", then at minimum remove the O5 disjointness claim from the docstring, list "instance disjointness" as open in report §4, and make the vacuous-file case a STOP.

## NON-BLOCKING

- **N1. No per-call record or contents** (`:165-195`). The spec's intent with `--keep-contents` is that contents are kept; the report is right that the flag does not exist at `d10b05b7`. R1-TRACKS-S01-RERUN also asks that identity be recomputed from the contents. Write `calls.jsonl` with one row per call: prompt index, repeat, seed, latency, prompt and completion tokens, and content (or its sha256). STOP 5 can then recompute identity.
- **N2. Prompt tokens are not recorded** (`:153-162`). B.1b records prompt and completion tokens per call. Keep `usage.prompt_tokens` as well; the projection depends on prompt length.
- **N3. No thinking-content count.** Count per call using M4 2(d) / B.1b's definition (non-empty `reasoning_content`, `<think>` in `content`, `reasoning_tokens > 0`). B.1b makes more than 1 % a STOP, and thinking would also invalidate the latency.
- **N4. Thinking policy and template are hard-coded** (`THINKING_OFF`, `extra`, `:58`, `:287`). B.1b says to use the pick's registry entry, including any declared template repair (the exam passes `EXAM_SERVER_ARGS + template_repair_args(spec)`). Either take `--registry-key` and build both from `r1/exam/registry.yaml`, or refuse a candidate with a declared template repair.
- **N5. The cache_prompt check happens after the model has loaded.** The request bodies are built and checked inside `replay` (`:168-171`), after the server has started. A STOP there writes no `dtq_report.json`, and that path is untested. Build and check the payloads before `inst.start()`, write a report on that STOP, and add a test that monkeypatches `probe.chat_payload` to drop `cache_prompt`.
- **N6. Spec shape is not enforced in a real run** (`:227-228`, `:241`). `--n` and `--repeats` can be lowered and the criterion is still applied. Outside `--dry-run`, require n = 50 and repeats = 3, or set `pass` to `None` when the shape differs.
- **N7. `--dry-run` is not guarded.** It relaxes the exclusion requirement and the nvidia-smi STOP but does not check that the server is the fake. Use `r1/scripts/dryrun_guard` or require `$R1_FAKE_OLLAMA_ROOT/.dryrun`, as other dry-run tools do.
- **N8. Orphaned server on SIGTERM/SIGHUP.** The server is started with `start_new_session=True`. If the tool is killed by SIGTERM or SIGHUP, the `finally` does not run and the server keeps both cards. Install handlers that raise `SystemExit`, or document cleanup through `lsi.stop_orphan(record)` using `out/server/llama_server_<port>.json`.
- **N9. Docstring states a precondition as fact** (l. 4-5): "R1-EXAM-RULE-X5V2 is frozen before any DTQ number exists". It is an O5 precondition that the tool does not check, and this branch has only `x5_rule_v1.yaml`. Reword it as an operator precondition, or add a guard.
- **N10. Provenance (S10).** The report JSON records only `source_commit: 'd10b05b7'`. Record the full commit `d10b05b738fc0e0dba54e0e692c248bedf095482` and the blob `f2c1bb792c4b8bf247c2685bbd4e8b8c674c6318` in the JSON and in report §1.
- **N11. Test gaps.**
  - There is no end-to-end non-identity test (a nondeterministic fake reply giving identity < 1, a populated `non_identical_prompts` and `pass: false`).
  - The complete-run test does not assert `server_stop.stopped` or `-np 1`.
  - `test_exclude_prompts_required_outside_dry_run` accepts any `SystemExit`; assert code 2 and the message.
  - The nvidia-smi-unreadable STOP is untested.
  - The fake prints the offload line whatever the verbosity, so the route (i) test does not show that `-lv 4` is needed. That is acceptable, since it rests on R1-EXAM-OFFLOAD-ROUTE, but note it.
- **N12. Co-tenant gap during load.** A co-tenant that appears during model load or the offload check and is gone before the sampler starts is not seen. The `apps` read inside `offload()` could also be checked for other pids.

## Report accuracy (`docs/r1/reports/M4_DTQ_TOOL_20261114.md`)

These parts are accurate:
- §1: byte identity, no merge, base lacked `r1/tracks/`, the one-token fake change, 14 tests;
- §3: 14 passed, and 104 existing passed unchanged;
- the `--keep-contents` note in §4;
- the B1-separation note.

These parts are inaccurate:
- l. 29 (co-tenant during run, see B1);
- l. 28 and §4 l. 53-54 (projection basis, see B2);
- l. 25 (disjointness omits "and instances", see B3).

Verdict: changes requested

---

# Independent review: M4 step 4 (DTQ tool, Unit 8.2), round 2

Reviewed commit: 0aa4bc00a744099b9a27362c5b779862eed26d8a

Round 2 reviews commit `0aa4bc00` on branch `mac-m4-dtq-20261114`. Its single parent is `952d20c0fba453a309840053e31f27c4e44ca1d0`, the commit reviewed in round 1 (`REVIEW_U82_DTQ_round1.md`). The review was read-only. Scratch worktrees and tests were kept under `/tmp/rev_u82` and have been removed.

## Round-1 findings: status

**B1 (co-tenant during the run): fixed.**
- `MemorySampler.sample` sets `abort` at the first intruder or the first unreadable sample. One sample is taken before the first call. `replay` checks `abort` before every call and records `aborted_at_call` and `planned_calls`.
- After the replay, `sampler.intruders or sampler.unread` gives exit 2 with `STOP_co_tenant_during_run` or `STOP_nvidia_smi_unreadable_during_run`. It also gives `dtq.stop: true` and `pass: false`, and no projection is computed. The STOP still fires if the intruder appears during the last call or at the final sample in `stop()`.
- The STOPs at start now also carry `dtq.stop/pass: false`.
- I checked this end to end with scratch tests against the fake server:
  - An intruder after call 2 gave 2 of 18 calls served, `pass: false`, exit 2, and `server_stop.stopped: true`.
  - An nvidia-smi that became unreadable after call 2 gave `STOP_nvidia_smi_unreadable_during_run` after 2 calls, `pass: false`, exit 2, and the server stopped.
  - Removing the abort check in `replay` makes the new mid-run test fail, so that test is meaningful.

**B2 (projection formula): fixed.**
- `projection()` now computes the RUNBOOK B.1b prerequisite 6 formula: `campaigns × calls_per_campaign × mean latency + campaigns × runs_per_campaign × cpu_s_per_run / workers`. It reports `llm_days`, `cpu_days` and `days`.
- If any CPU-term input is missing, `days`, `projection_le_4_days` and `pass` are all `None`. The LLM term alone is never judged. Non-positive inputs are refused.
- `evaluate` returns True only when all three conditions hold, False on any failure or STOP, and None when only the projection is unevaluated. The arithmetic tests and an end-to-end "unknown CPU term → `pass: null`" test cover this.

**B3 (exam instances, vacuous exclude file): fixed as far as the round-1 fix allowed, with the rest disclosed.**
- Replay rows now need `ledger_sha256` (64 characters) and `trial_id`.
- A replay row whose ledger occurs in an exam row is refused. The exam's frozen rows carry `ledger_sha256` (`r1/exam/stage_a.py:19-38`).
- An exclude file with no prompt text, or with no `ledger_sha256` at all, is a STOP.
- The docstring and the report now say "as far as the ledger identity shows". Report §4 lists any wider meaning of "instance" (node and seed, the exam's 9001–9004 namespace) as open for the author.
- Removing the ledger refusal makes a test fail.

**N6 (50 × 3 outside `--dry-run`): fixed in code.** I checked it separately (scratch test, unrelated exclude file): `--n 6` without `--dry-run` exits 2 with "outside --dry-run the qualification uses --n 50 and --repeats 3 (O5)". The committed test does not discriminate, though; see R2-N1.

**N9 (X5V2 wording): fixed.** The docstring now names it as an O5 precondition that the operator checks and the tool does not.

**Round-1 N1–N5 and N8:** listed as not done in report §4.

## Nothing new broken

- The probe files are still byte-identical to `d10b05b7`: blobs 9ce553f4, ab8f105b and f2c1bb79. Commit `0aa4bc00` does not touch them, `c3_fake_llama_server.py`, or `llama_server_instance.py`.
- The requested test command at the tip gives **122 passed** (18 DTQ + 104 existing). The worktree was clean before and after.
- The broader run `r1/tests -k "llama or fake or probe or dryrun or sweep"` used the same harness pin `a3fedbb`:
  - base `5cd32efc`: 22 failed, 174 passed, 9 skipped, 690 deselected;
  - tip `0aa4bc00`: 22 failed, 176 passed, 9 skipped, 706 deselected.

  The failure sets are **identical by test id**. The 18 extra tests are the new DTQ tests, and no existing test file changed.
- The report (`docs/r1/reports/M4_DTQ_TOOL_20261114.md`) now matches the code: the §2 rows for disjointness, projection, co-tenant and criterion, "18 passed" in §3, and the §4 open and not-done items.

## BLOCKING

None.

## NON-BLOCKING

- **R2-N1. `test_real_run_holds_n_and_repeats_at_50_and_3` is vacuous** (`r1/tests/test_dt_dualcard_qualify.py`, last new test).
  - It passes the replay file itself as `--exclude-prompts`. If the guard is removed, the run still raises `SystemExit`, through the text-overlap STOP. The mutation that deletes the guard survives: 18 passed.
  - *Fix:* use an unrelated exclude file that carries a `ledger_sha256`, and assert exit code 2 and the "--n 50 and --repeats 3" message.
- **R2-N2. The unreadable-during-run path is untested.** Mutations that drop `unread` from the STOP test, or that stop an unreadable sample from setting `abort`, both survive. The code is correct by my scratch test.
  - *Fix:* add a test that replaces the fake `nvidia-smi` with `exit 1` mid-run, and assert `STOP_nvidia_smi_unreadable_during_run`, `pass: false` and an aborted replay.
- **R2-N3. The mid-run intruder test does not assert `server_stop.stopped`.** It is true by my scratch test. Assert it there and in the complete-run test.
- **R2-N4. Unevaluated items are reported as False on a STOP.** `evaluate(offload, None, None, stop=True)` reports `identity_1: false` for an identity that was never evaluated. Report `None` for items not evaluated.
- **R2-N5. Ledger check details.**
  - The comparison is an exact string match. Lower-case it and require hex.
  - One exam row with a ledger is enough to pass the "has ledger_sha256" check. Require every exclude row to carry both text and a ledger.
  - The replay rows' `ledger_sha256` is not checked against the ledger file or `context_sha256`, as `stage_a.load_prompts` does for exam rows.
  - A ledger is narrower than an (node, instance seed) pair: the other memory mode's ledger of the same instance passes. This is disclosed in §4 as needing the author's definition.
- **R2-N6. Optional: an LLM term over 4 days already settles the result.** It is a lower bound, so `llm_days > 4` could set `pass: false` even when the CPU term is unknown.
- **R2-N7. Partial CPU-term inputs are not refused.** Giving one or two of the three CPU-term flags silently yields `None`. `ap.error` would catch the operator slip.
- **R2-N8. Report §4 omits some open round-1 items.** Its not-done list leaves out round-1 N7 (no `--dry-run` guard against a real binary), N10 (the full source commit `d10b05b738fc…` and blob `f2c1bb79…` in the report JSON), the remaining N11 test gaps, and N12 (a co-tenant during load or the offload check).
- **R2-N9. Operator notes.**
  - A single transient unreadable nvidia-smi sample aborts the run. That is conservative and acceptable, but worth a line in the operator notes.
  - The abort takes effect between calls, so an in-flight call (timeout up to 600 s) finishes before the server is stopped.

Verdict: accepted
Accepted commit: 0aa4bc00a744099b9a27362c5b779862eed26d8a
