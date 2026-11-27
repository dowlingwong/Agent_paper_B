# D.3 G1/G6 revision 6c-2 — independent re-review of the replicate-arm driver

**Reviewer.** Fresh, independent re-reviewer; I did not write revision 6c-1/6c-2, the FIXR3/EGATE engines,
G8 accounting, the G1 snapshot core or the chunk shell. Read-only: no code, campaign, audit, job, label,
evaluation, split, sweep-table or sealed file was run or opened; the reviewed branch was not modified.
The only writes are this review file and scratch worktrees under the session's temporary directory.

**Target.** `origin/compute-d3-g1-design-r6c-20261127` @ `690e8626`, file
`docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_REV6C_REPLICATE_ARMS_20261127.md`,
sha256 `d262e39ee25ae1f7ebe2a5c80a7e626a146c98f48f9457ccb2409940584d30eb` (verified with
`git show 690e8626:... | shasum -a 256`). This is a new commit on the same branch as revision 6c-1
(`ed0ad83b`), not a force-push.

**Prior review.** `docs/r1/reviews/D3_G1_G6_REV6C_REVIEW_20261127.md` (revision 6c-1; verdict
CHANGES REQUIRED, four BLOCKING, five MAJOR, seven MINOR). The design's §10 answers each finding. The
design's §1/§9 cite `c9c136d19d7c8f097199509d7b324b34e8426125b2bec1a3da6f12cdbc443b9a`, the content
hash recorded in that review's self-line; the review file has since had a status-note follow-up (N8).
Editorial note only.

**Method.** Read revision 6c-2 in full, with §10 against §2-§8; re-checked each prior finding against the
same delivered files (`r1/c3/d3_replicate.py`, `r1/c3/accounting.py`, `r1/c3/d3/snapshots.py`,
`r1/c3/d3/campaign_chunk.py`) and the pinned harness `ComputeBudget`
(`harness_pin/src/autoresearch/control_plane/budget.py` at `a3fedbbd`). Re-ran the same unit modules:
`test_d3_fixr3.py` + `test_d3_egate.py` + `test_d3_g8_accounting.py` → **69 passed**;
`test_d3_g1_snapshots.py` + `test_d3_g1_chunk.py` → **16 passed**. No integration test exists; no code
was changed by 6c-2.

---

Verdict: CHANGES REQUIRED

---

## Summary

All sixteen prior findings are addressed in substance, and the scientific content is unchanged: the
FIXR3/EGATE rules, constants, seeds, W=20, cap 80, K=10 and Y_final remain as before, and no rule or
constant moves. The engine-owned charge (B1), the narrowed EGATE assertion (B4), the G1-built projection
(B3), the EGATE `incumbent_runs` (M1), the `pending` object (M2), the post-decision `final.json` (M3), the
`run_replicate_chunk`/writer/path additions (M4), the `ComputeBudget` LLM cap (M5) and the seven minor items
are the right responses.

Three new **MAJOR** interface issues remain, all small to fix but functional as written:

1. **N1** — `ComputeBudget` is a frozen dataclass; `consume_worker_run()` and `consume_llm_call()` return a
   **new** object. The design calls them without reassigning (`6c-2:75-76`, `:88`), so `budget.worker_runs`
   and `budget.llm_calls` never advance and the §3.6/§5 parity and LLM-cap checks STOP on the first run/call.
2. **N2** — `begin_step(incumbent=engine.incumbent or start_config)` and `write_final_from_state` from
   `engine.incumbent` pass a **config sha string** where the recorder and G6 need the **config contents**
   (a dict). The first step passes `start_config` (a dict), later steps a string; `final.json` would carry a
   sha as `incumbent_config`, so G6 cannot audit the final incumbent.
3. **N3** — the `begin_step` signature lacks `trial_id`, `last_kept_trial_index` and `llm_calls` that the
   5b snapshot/`_TrialState` needs; `write_final_from_state`'s arguments are not specified. The snapshot
   fields would be `None`/stale, not the 5b schema's values.

Conditions 1-4 of §8 therefore still FAIL on these interfaces; condition 5 PASSes (no reads; one wording
issue). The verdict remains CHANGES REQUIRED; this is a request for a short 6c-3 API correction, not a new
scientific design.

## Per-finding resolution

| Prior finding | Status | Evidence |
|---|---|---|
| **B1** engine vs `run` charge | **Resolved in substance** | The engine owns the charge: `d3_replicate.py:134-137`, `:217-220`, `:233-236`; `run_one` does not charge and converts an exception to `RunOutcome(success=False)` (`6c-2:84-92`), so the engine's `counter.charge` runs once. New N1 is about the separate `ComputeBudget` object, not the counter. |
| **B2** no `recorder.on_charge` | **Partially resolved** | The design now says the G1 unit adds `begin_step`/`on_charge`/`write_final_from_state` and its review covers them (`6c-2:50`, `:63-67`, `:111-123`, `:191-193`); the harness path stays unchanged. But the `begin_step` signature and `incumbent` type do not match the recorder/schema (N2, N3). |
| **B3** no `engine.snapshot_state()` | **Resolved** | The projection is built by G1 from public fields (`arm`, `version`, `instance_seed`, `steps`, `incumbent`, `seeds`; FIXR3 `incumbent_metrics`/`zero_variance_cases`; EGATE `incumbent_runs` from `counter.lookup`), hashed with `json.dumps(..., sort_keys=True, separators=(",", ":"))`, no `repr`/ids/times (`6c-2:114-123`). No engine method is required; the fields exist at `d3_replicate.py:120-125`, `:185-188`. |
| **B4** EGATE `gate.decide` between runs | **Resolved** | The assertion is narrowed to manager calls and the step-ending E2 decision; per-pair `gate.decide` is explicitly allowed (`6c-2:133-136`). `d3_replicate.py:247` is the per-pair call; it does not set `incumbent` (only `:249` on commit, after the last run of the step). |
| **M1** EGATE state needs incumbent runs | **Resolved** | `incumbent_runs` is one `{j, seed, success, metric, charged}` (or `null`) for j = 0..7 from `counter.lookup(engine.incumbent, seed)` (`6c-2:120-121`; `accounting.py:219-225`). This is the state `_incumbent_run`/`prior_inc.metric` uses (`d3_replicate.py:190-191`, `:206`, `:246`). |
| **M2** in-step snapshots not replayable | **Resolved** | The `pending` object `{step, j, candidate_metrics, incumbent_metrics, diffs}` is built from the G1 `RunAttempt` log and carries the in-step metrics/diffs (`6c-2:128-132`); the controller state remains the step-start projection. |
| **M3** w=20 alias loses a last-step keep | **Resolved for the replicate route** | `final.json` is written after the loop from `engine.incumbent`, a separate post-decision record, not an alias of `w20.json` (`6c-2:137-142`, `:103-104`); the engines set `incumbent` after the decision (`d3_replicate.py:148`, `:157`, `:230`, `:249`). N2 affects the config contents; N4 is a wording issue about the harness route. |
| **M4** no replicate chunk path/writers | **Resolved** | `run_replicate_chunk(spec, instance_id, repetition, engine, manager, worker, out_dir)` (`6c-2:63-67`); the G1 unit adds the `run_chunk` replicate branch and the per-campaign writers (`campaign.json`, `ledger.jsonl`, `runs.jsonl`, `summary.json`, `SHA256SUMS`) (`6c-2:171-177`); the path includes `campaigns/<instance_id>/`. |
| **M5** no LLM-call counter | **Resolved in design** | `ComputeBudget(max_worker_runs=20, max_llm_calls=80)`; `consume_llm_call()` before every manager call; cross-check against `campaign_usage` (`6c-2:71-78`, `:150-161`). N1 is the frozen-object API issue. |
| **m1** w=0 start record | **Resolved** | G1 sets `start_config` and the step-start projection explicitly; only `llm_call_cap`/`error` can end at w=0 (`6c-2:142-143`). |
| **m2** field contract | **Resolved** | New fields are `campaign_kind` and the optional `pending`; `arm` already exists (`6c-2:174-175`, `:218-219`). N5 is a wording issue about the trial-record fields. |
| **m3** existing `run_replicate_campaign` | **Resolved** | New entry point `run_replicate_chunk`; the test-only reference loop is not used (`6c-2:45`, `:63-67`). |
| **m4** missing `campaigns/` | **Resolved** | The path is `<run_root>/<stage>/<arm>/r<rep>/campaigns/<instance_id>/` (`6c-2:171-172`). |
| **m5** `RunOutcome` has no cause | **Resolved** | `run_one` keeps a `RunAttempt` side record with the cause and card/host process counts; G8 `classify_worker_failure` classifies it (`6c-2:85-87`, `:154-158`). |
| **m6** `RuleLayerController` outside harness | **Resolved** | E1 is validate-and-execute directly; no `ControlView` or controller object (`6c-2:46`). |
| **m7** zero-variance count not reported | **Resolved (design)** | G1 reads `engine.zero_variance_cases` into the trial record/summary (`6c-2:98-99`, `:124`, `:152`). N5 is the field-contract wording. |

## New findings

### MAJOR

**N1. `ComputeBudget` is frozen; the design calls `consume_worker_run()`/`consume_llm_call()` without
reassigning the returned object, so the budget never advances and the parity/LLM-cap checks STOP.**
`harness_pin/src/autoresearch/control_plane/budget.py:43` is `@dataclass(frozen=True)`;
`consume_worker_run` (`:87-95`) and `consume_llm_call` (`:97-105`) return a **new** `ComputeBudget`.
Revision 6c-2 says "`run_one` ... calls `budget.consume_worker_run()` **before** the engine charges the
counter" (`6c-2:88`) and "Before the call, `budget.consume_llm_call()`" (`6c-2:75-76`). With no
`budget = budget.consume_...`, `budget.worker_runs` stays 0 and `budget.llm_calls` stays 0; §3.6's
`counter.used == budget.worker_runs` (`6c-2:93-94`) and §5's `budget.llm_calls == the proposal/revision
event count` (`6c-2:150-152`) fail on the first run/call. Fix: state
`budget = budget.consume_worker_run(...)` and `budget = budget.consume_llm_call()` (with `nonlocal` or a
mutable holder if `run_one` is nested), or use a mutable budget wrapper; the counter side is already correct.

**N2. `begin_step` and `write_final_from_state` pass `engine.incumbent` (a config sha string) where the
recorder and G6 need the config contents (a dict).**
`Fixr3Engine.incumbent` and `EgateEngine.incumbent` are `str | None` and are set to `config_sha256`
(`d3_replicate.py:122`, `:148`, `:157`, `:230`, `:249`). The recorder's `_TrialState.incumbent_config` is
`dict[str, Any]` (`snapshots.py:263`), is filled from `ctx.incumbent_snapshot.contents` (`:304-307`), and is
written to the snapshot as `incumbent_config` (`:383`). Revision 6c-2 calls
`recorder.begin_step(..., incumbent=engine.incumbent or start_config, ...)` (`6c-2:82`) and writes
`final.json` "from `engine.incumbent` (or `start_config` ...)" (`6c-2:103`, `:137`). On the first step
`engine.incumbent` is `None`, so `start_config` (a dict) is passed; on later steps it is a string; the
snapshot's `incumbent_config` and `final.json`'s incumbent would be a sha on later steps, and G6 cannot run
the audit from a sha. The `start_config`/`incumbent` union is not a coherent type. Fix: pass
`incumbent_config=read_worker_config(worker, node_spec)` (or the proposal's config) plus
`config_sha256=engine.incumbent`; state how a discarded candidate's workspace is restored before the next
step and how `write_final_from_state` obtains the final config contents.

**N3. The `begin_step` signature lacks `trial_id`, `last_kept_trial_index` and `llm_calls`, so it cannot
populate the 5b snapshot/`_TrialState` fields; `write_final_from_state`'s arguments are undefined.**
`_TrialState` requires `trial_id`, `incumbent_config`, `config_sha256`, `controller_state_sha256`,
`last_kept_trial_index` and `llm_calls` (`snapshots.py:261-269`); the payload writes them at `:383-388`.
Revision 6c-2's call is `begin_step(state=projection(engine, counter), incumbent=..., start_config=...,
step_index=...)` (`6c-2:81-83`); the projection field list (`6c-2:118-121`) does not include
`trial_id`/`last_kept_trial_index`/`llm_calls`. The design says `begin_step` records
`last_kept_trial_index` and `w` at step start (`6c-2:114-116`); `w` is available as `recorder.count`, but
`last_kept_trial_index` (and `llm_calls`/`trial_id`) is not a parameter and is not in the projection.
Consequence: the snapshot's `trial_id`, `last_kept_trial_index` and `llm_calls` are `None`/stale, not the
5b values. Fix:
add these to the `begin_step`/`write_final_from_state` signatures (or to a documented `state` dict), with
`llm_calls` from `budget.llm_calls`, `last_kept_trial_index` from G1's kept-trial log, and `trial_id` from
the step. The step-start `w` is available as `recorder.count`; it needs no new parameter.

### MINOR

**N4. The claim that the harness route's w=20 snapshot is written "at E2 after the decision" is wrong.**
Revision 6c-2 says the replicate final is a deliberate difference "from the harness route, where the w=20
snapshot is written at E2 after the decision" (`6c-2:141`). 5b §2.2 says the snapshot is "taken before the
controller decision triggered by that run" (5b:59-66); the delivered recorder's `__call__` at E2 sets
`_trial` before the controller hook (`snapshots.py:297-313`). The replicate `final.json` is correctly
post-decision; the harness comparison should be removed or corrected. MINOR.

**N5. Condition 5's "only new record fields are `campaign_kind` and the optional `pending` object" conflicts
with §3.7's `zero_variance_cases`/`RunAttempt` failure classes.**
Revision 6c-2 says "Record `zero_variance_cases` and the G1 `RunAttempt` failure classes in the trial
record / summary" (`6c-2:98-99`) but condition 5 says the only new record fields are `campaign_kind` and
`pending` (`6c-2:218-219`). The trial record/summary fields are new too; say which record holds them
(`extra.control`/summary) and include them in the condition. MINOR (field-contract wording).

**N6. "FIXR3 and EGATE need no constants file, but ... the G2 file ... still required" is self-contradictory.**
Revision 6c-2:197-199 says the A1/A2/LADDER constants file (G2) and the signed revision 4 are prerequisites
"for those arms", then "FIXR3 and EGATE need no constants file, but ... the G2 file and the verify-seed check
are still required before any evidence run." The G2 file is not a FIXR3/EGATE prerequisite; remove it from
that sentence. MINOR.

**N7. `run_one` receives only `config_sha256`; the design does not state how the worker gets the proposal /
config or how a discarded candidate's workspace is restored.**
`RunFn` is `(role, config_sha256, seed, j) -> RunOutcome` (`d3_replicate.py:55-56`); a harness worker runs a
`proposal`, not a sha. G1 has the validated proposal and can map it, but the design's §3.5 only says "calls
the worker exactly once" (`6c-2:84-87`). Say that `run_one` uses the current step's proposal/config (or a
`config_sha256 -> config` map) and that a discarded candidate is restored before the next step; otherwise
the worker interface is an unstated adapter. MINOR.

**N8 (note). Prior-review sha citation.** The prior review's 6c-1 commit is
`041c3c0383f3970b74eed034a2d3b1721117a4734eb8fa3d360c12f29c3e6136`; the design cites
`c9c136d1...`, the content hash in that review's self-line. The review file has since had status-note and
final-hash follow-ups (current branch tip `ac92af97...`). Both identify the same 6c-1 review text;
editorial only.

**N9 (note/status). Pre-declaration and verify-seed rows.** The design cites `R1-D3-VERIFY-SEED`
(`main 8b01ef6a`) and still says "the pre-declaration signature ... still required" (`6c-2:197-199`). The
author's `R1-D3-PREDECL-R4` row is on `origin/main`; the document's freeze/publication follows its steps
(3) and (5). The design's "signature still required" is a status nuance, not a design defect; update the
sentence when the document is frozen. NOTE.

## §8 conditions

| # | Condition | Result | Evidence |
|---|---|---|---|
| 1 | Every actual worker call charged exactly once through the one `ChargedRunCounter` (engine-owned, `run_one` exceptions → failed `RunOutcome`); no reused-incumbent charge; fail closed on counter/budget/record/parity differences | **FAIL** | Engine-owned charge is resolved (`d3_replicate.py:134-137`, `:217-220`, `:233-236`; `6c-2:84-92`); reused incumbent is not a `run_one` call; the counter is single. But `ComputeBudget` is frozen and the design does not reassign its `consume_*` returns (`budget.py:43`, `:87-105`; `6c-2:75-76`, `:88`), so `budget.worker_runs`/`llm_calls` do not advance and the §3.6/§5 parity STOPs on the first run/call (N1). |
| 2 | Step-start projection of §4 (including EGATE `incumbent_runs`); no manager/step-ending E2 between capture and any run; deterministic hash; exact w=5,10,15,20 live; `pending` metrics/diffs | **FAIL** | The projection, `incumbent_runs`, narrowed assertion and `pending` are resolved (`6c-2:114-136`). But `begin_step` passes `engine.incumbent` (a sha) where the recorder needs config contents (N2), and its signature lacks `trial_id`/`last_kept_trial_index`/`llm_calls` (N3; `snapshots.py:261-269`, `:383-388`). The state cannot be recorded as the 5b schema requires. |
| 3 | Same record layout (`campaigns/<instance_id>/`), `campaign_id`, record name, `final.json`, G6 path; `extra.control.replicates` exactly G8; `final.json` post-decision | **FAIL** | Layout/writers/path and `extra.control.replicates` are resolved (`6c-2:96-99`, `:171-177`; `replicate_entries` `accounting.py:100-137`). The post-decision `final.json` is resolved (`6c-2:137-142`), but it is built from `engine.incumbent` (a sha) and would not carry the config contents G6 audits (N2). |
| 4 | §5.4/§5.5 unchanged; LLM cap charged through `ComputeBudget` before each manager call; `ended_on` follows `table_ended_on` | **FAIL** | Rules/constants/seeds and `ended_on` are unchanged and correct (`d3_replicate.py:105-258`; `accounting.py:228-244`; `d3_analysis.py:262-281`). The LLM cap is charged through a frozen `ComputeBudget` without reassignment (N1), so the cap does not advance and the cross-check fails as written. |
| 5 | No evidence/label/evaluation/sealed read; only new record fields `campaign_kind` and optional `pending` | **PASS** (no-read) / **MINOR** N5 | The revision is documentation; `accounting._jsonl` calls `refuse_sealed` (`accounting.py:53-56`); the engines read no label/evaluation/split/sweep-table. The field list is incomplete: `zero_variance_cases`/`RunAttempt` failure classes are also new trial-record/summary fields (N5). |

## Scope and limits

**In scope.** Revision 6c-2 §10 and the changed §2-§8 text against the same delivered engine, accounting,
snapshot and chunk files and the pinned `ComputeBudget`; the sixteen prior findings; the five §8 conditions;
new interface issues.

**Out of scope / not decided here.** The FIXR3/EGATE rules, constants, seeds, W=20, cap 80, K=10, Y_final
(I found no change); the accepted 5b/6b text except where 6c-2 relies on it; the level-2 verify-seed and
pre-declaration status (R1-D3-VERIFY-SEED / R1-D3-PREDECL-R4; status note N9); the tier-E review of the
engines/accounting/snapshot core themselves; any campaign, audit, label, evaluation, sealed read, GPU job
or smoke. I did not modify `main`, `coord/*`, the reviewed branch, the engine branch or the snapshot
branch.

**Test evidence.** The code is unchanged from 6c-1; I re-ran the same delivered unit modules in scratch
worktrees: `test_d3_fixr3.py`, `test_d3_egate.py`, `test_d3_g8_accounting.py` → **69 passed**;
`test_d3_g1_snapshots.py`, `test_d3_g1_chunk.py` → **16 passed**. There is still **no** integration test for
the replicate route + `begin_step`/`on_charge`/`write_final_from_state` + `campaign_chunk.py`; the state/
budget API issues above are the reason the design cannot yet be accepted for code.

## Review record

- Review target: `origin/compute-d3-g1-design-r6c-20261127` @ `690e8626`.
- Reviewed file sha256: `d262e39ee25ae1f7ebe2a5c80a7e626a146c98f48f9457ccb2409940584d30eb`.
- Prior review: `D3_G1_G6_REV6C_REVIEW_20261127.md` (6c-1), CHANGES REQUIRED; its 6c-1 commit file sha is
  `041c3c0383f3970b74eed034a2d3b1721117a4734eb8fa3d360c12f29c3e6136`; the design cites the content hash
  `c9c136d1...` (N8). The review file has follow-up commits; the branch tip is `ac92af97...`.
- Verdict: **CHANGES REQUIRED** (three new MAJOR: N1-N3; four MINOR: N4-N7; two notes: N8-N9).
- Base: the review branch `compute-d3-g1-design-r6c-review-20261127` (based on `origin/main` `5c901d19`;
  the reviewed branch is not merged).

**Review file sha256:** `b08ac850b8ecd28c4335c1973bc8dcd362051ae85d30300020ea0ad5dfb16c89` — the sha256 of this review text above this line. The sha256 of the
committed file (this line included) is reported in the commit message and in the reviewer's report.

*Prepared by a fresh independent re-reviewer; no part of the reviewed work was authored by this session.*
