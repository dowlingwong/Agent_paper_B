# D.3 G1/G6 revision 6c — independent review of the replicate-arm driver

**Reviewer.** Fresh, independent reviewer session. I did not write revision 6c, the FIXR3/EGATE engines,
G8 accounting, the G1 snapshot core or the chunk shell. Read-only: no code, campaign, audit, job, label,
evaluation, split, sweep-table or sealed file was run or opened; no branch under review was modified.
The only writes are this review file and scratch worktrees under the session's temporary directory.

**Target.** `origin/compute-d3-g1-design-r6c-20261127` @ `ed0ad83b`, file
`docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_REV6C_REPLICATE_ARMS_20261127.md`,
sha256 `fdf0cf91ebe842c1135bbe85bddd2ea08806d0be7aeaa23802a2ab2ce6271024` (verified with
`git show ... | shasum -a 256`). Stacked on revision 6b
(`D3_G1_G6_DESIGN_REV6_LAUNCHERS_20261126.md`, sha256
`0d696535d94395c85592c7ac9483790483966bbe0bf48961d132c50aa49b922d`,
`origin/compute-d3-launcher-design-20261126` @ `459398f2`, `ACCEPTED FOR CODE`), itself on revision 5b
(`D3_G1_G6_DESIGN_20261126.md`, sha256
`4b95798659c13feeef02af02504d68f138e40cdaf056ded0b89a09fbcc4e3a23`, `ACCEPTED FOR CODE`).

**Authority read.** `canon/README.md`, `canon/COMPUTE.md`, `canon/PAPER_B_PLAN.md`; `docs/r1/PLAN.md`
§10 rows R1-AUTONOMY, R1-NO-TIMEOUT, R1-D3-MIN, R1-D3-DECOMP, R1-D3-OUTCOMES2, R1-D3-ORDER; tasks
`tasks/compute/20261127-09-g1-next.md` (item 2) and `tasks/compute/20261127-04-d3-hook-decision.md`;
`docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md` revision 4 (sha256
`bafa10e0bae89565cf9a17d4bed697647f5e4ab0bf6f067c6ccdbad3a9285769`; §4.1, §5.4, §5.5, §7.1, §10,
§12 G3/G4); revision 5b §2.1, §2.2, §3.3; `r1/c3/d3_replicate.py`, `r1/c3/accounting.py` and the
unit reports on `origin/mac-d3-egate-20261127` @ `871d4712`; `r1/c3/d3/snapshots.py` and
`r1/c3/d3/campaign_chunk.py` on `origin/compute-d3-g1-snapshot-20261127` @ `51cf07f7`.

**Method.** Read the design, the two engine/accounting files and the snapshot/chunk core line by line;
checked the seven cited sha256 values; ran the four delivered unit-test modules in their branch worktrees
(`69 passed` for FIXR3/EGATE/G8; `16 passed` for the snapshot core/chunk); then ran small read-only probes
for the specific integration claims in §8. No integration test exists and none was written.

**Status note (current `main`).** `origin/main` advanced to `8b01ef6a` after this review branch was cut
from `5c901d19`; it adds **R1-D3-VERIFY-SEED** (option A: a reviewed harness pin on top of `a3fedbbd` with
a verify-seed base; the default reproduces today's seeds) and **R1-D3-PREDECL-R4** (the author signs
revision 4, including §13 items 21–31). The design's §7 statements that the verify-seed collision "still
blocks ... until the author's row" and that "the pre-declaration's signature [is] still required" are
therefore stale as of that `main`. The confinement of the blocker to the harness arms is still correct.
This is a status/obsolescence note; it does not change the findings or the verdict.

---

Verdict: CHANGES REQUIRED

---

## Summary

The scientific core of revision 6c is right. The G1-owned loop outside `run_real_campaign` is the correct
answer to the harness gap (G1 unit report §3.2,
`docs/r1/reports/d3_g1_20261127/D3_G1_UNIT_20261127.md`; `r1/c3/d3_replicate.py` is a harness-free
`step(config, run, counter)` state machine), the FIXR3 and EGATE decision rules, constants, seeds and
failure rules match PD §5.4/§5.5, the FIXR3/EGATE `extra.control.replicates` entries match the G8
contract, `table_ended_on` matches the pinned analysis, and the verify-seed collision is correctly left
on the harness arms only.

The integration contract in §3-§4, however, names APIs and a charging layering that the delivered code
does not have. As written, the design cannot be implemented with "the engines unchanged" and "the reviewed
snapshot core unchanged": the engine, not `run`, charges; neither engine has `snapshot_state()`; the
`SnapshotRecorder` has no `on_charge` and cannot write a replicate campaign's snapshots/final; EGATE calls
its gate between worker calls inside a step, which the design's own fail-closed assertion forbids; and the
chunk shell has no replicate path or record writer. These are contract/design defects, not arm-rule
defects, but they are blocking for the "accepted for code" gate in §8.

## Findings

### BLOCKING

**B1. The design assigns the charge to `run`; the delivered engines charge after `run` returns, so
"exactly once, including a call that raises" is not implementable with the engines unchanged.**
Revision 6c §3 step 5 (6c:69-71) says `run` "charges the counter exactly once per actual worker call,
including a call that raises". The engines do the charging themselves, immediately after a successful
return: `out = run(...)` then `counter.charge(...)` at `r1/c3/d3_replicate.py:134-137` (FIXR3
candidate), `:217-220` (EGATE candidate) and `:233-236` (EGATE incumbent). Neither engine catches an
exception from `run`; a raise propagates without any charge. A read-only probe confirms it: a `run` that
raises leaves `counter.used == 0` after one call reached the worker. If G1's `run` also charges, every
normal run is double-charged (engine + `run`); the §5 parity check would then STOP, but condition 1 is
still not met. If G1's `run` does not charge, a raising call is uncharged, contrary to §3 step 5, and
the parity check turns what may be an infrastructure failure into a STOP rather than the §10 recovery
path. The design must settle one layering and accept the consequence: either the engine owns the charge
and is changed to charge a raising call (a reviewed engine change), or G1's `run` owns the charge and the
engines' `counter.charge` calls are removed (also an engine change). It cannot keep both and claim the
engines are unchanged. This is the central condition-1 claim.

**B2. `SnapshotRecorder.on_charge` does not exist, and the recorder cannot produce a replicate
step-start snapshot or `final.json` without an unstated adapter/API.**
Revision 6c §3 step 1 (6c:60) constructs `ChargedRunCounter(W=20, on_charge=recorder.on_charge)`, and
§4 (6c:95-97) says every charge calls `on_charge(ChargedRun)` and "the recorder writes"
`snapshots/w<w>.json`. The reviewed core has no `on_charge` method: `r1/c3/d3/snapshots.py` exposes
`__call__(SnapshotContext)` at `:297-313`, `observe_budget` at `:315-324`, `note_run` at `:334-338`,
`_write_snapshot` at `:402-409` and `write_final` at `:411-426`; `git grep on_charge` over the snapshot
branch returns nothing. The recorder's step state `_trial` is set only by a harness `SnapshotContext` at
`:305-313`, and `start_config` only at E0 (`:300-303`). A read-only probe gives
`hasattr(recorder, "on_charge") == False`, and `write_final(w_final=20, ended_on="worker_runs")` raises
`SnapshotStop: no E1 state recorded before snapshot w=20` on a fresh recorder. The replicate loop has no
`SnapshotContext` (it never calls `run_real_campaign`), so it needs a new recorder API (step-start state
setter and a charge→snapshot adapter), or a documented use of the private `_trial`/`_TrialState` and
`start_config`. The design says the reviewed snapshot core is unchanged (6c:147); that is not compatible
with §2/§4 as written.

**B3. Neither engine has `snapshot_state()`, and the design refuses an engine without it, so both arms
are refused as delivered.**
Revision 6c §4 (6c:92-94) says "`engine.snapshot_state()` returns the projection; an engine without it is
refused, not hashed by fallback." `Fixr3Engine` (`r1/c3/d3_replicate.py:105-159`) and `EgateEngine`
(`:162-258`) have no `snapshot_state`; a probe gives `hasattr(...) == False` for both. The generic
`controller_state_sha256` in the core (`snapshots.py:118-149`) hashes a controller's `snapshot_state` if
present and otherwise a `RuleController`-shaped projection with a `repr` fallback; it does not know the
engines' `incumbent`, `incumbent_metrics`, `steps`, `seeds` or gate. Under the design's own rule the
replicate route cannot start. Adding `snapshot_state()` is a change to the engines, which §3 (6c:57)
says the module is not; the design must either state that change and its review, or define the projection
in G1 from public engine fields and drop the "engine without it is refused" sentence. It must also state
the exact ordered field set; "the engine's deterministic public state" (6c:90) is not a specification.

**B4. EGATE calls `gate.decide` between worker calls inside a step; the design's fail-closed "no engine
decision call" assertion would STOP every multi-pair EGATE step.**
Revision 6c §4 (6c:102-103) requires: "G1 asserts that no manager proposal/revision call and no engine
decision call occurs between the step-start capture and any worker call of that step. A violation is a
STOP (fail closed)." EGATE's step loops over pairs and calls `decision, wealth, n = self.gate.decide(diffs)`
at `r1/c3/d3_replicate.py:247`, then the next iteration runs the next candidate/incumbent at `:217`/`:233`.
A read-only spy on the gate shows the order `run(candidate j=0), decide, run(candidate j=1),
run(incumbent j=1), decide, ...` — exactly the forbidden pattern. This is the declared §5.5 sequential
rule (PD:332-373), not a bug. If G1 implements the assertion literally, every EGATE step with more than
one pair is a STOP; if G1 does not, condition 2's stated assertion is false. The design must narrow the
assertion to "no manager call and no step-ending E2 decision" (the per-pair `gate.decide` checks are part
of the step and do not change `self.incumbent`), or drop it for EGATE and rely on the step-start state.

### MAJOR

**M1. The step-start state as specified is insufficient for EGATE's decision and for any replay.**
Revision 6c §4 (6c:88-94) says the state includes "the engine's deterministic public state"; for EGATE it
names "the incumbent config and the pairs already decided". The engine stores only `incumbent`, `steps`,
`seeds` and the (stateless) gate. The incumbent's per-seed run metrics, which the decision needs
(`prior_inc = self._incumbent_run(counter, j)` at `d3_replicate.py:206`; `prior_inc.metric` at `:246`),
live in `ChargedRunCounter.runs` via `lookup` (`accounting.py:219-225`), not in the engine; a
`snapshot_state()` with no counter argument cannot include them. "Pairs already decided" are not stored
either: `diffs` is local to the step (`:200`, `:246`). FIXR3 is fine (`incumbent_metrics` at `:123`,
`:148`, `:157`). The design must define the projection as a function of the engine *and* the counter, or
have the engine retain the incumbent's runs; otherwise a snapshot cannot reproduce EGATE's next decision.

**M2. Exact-w snapshots inside a step are not self-contained and are not replayable from the snapshot
alone.**
Revision 6c §4 (6c:98-101) says an in-step boundary carries `pending_action`, `pending_step`, `pending_j`,
and "the accrued candidate/incumbent differences are part of the in-flight action, not part of the
controller state". The 5b schema (5b:59-69) has no field for those differences, and the core's `_payload`
(`snapshots.py:374-400`) has no such field. At w=6 inside a FIXR3 step, the snapshot has the step-start
state and `pending_j=1` but not the j=0 candidate metric; at an EGATE incumbent charge the diff is
computed only after the charge (`d3_replicate.py:246`) and is not in the payload. Replaying the decision
from the snapshot alone therefore requires re-running the already charged runs. If the design wants
"replayable", it must add a documented `pending_diffs`/`pending_metrics` field (a schema change, which
also contradicts 6c:86 "schema unchanged") or state that replay uses the trial record and deterministic
re-runs. As written, the exact-w snapshot records the step-start controller state, not the in-step state
the decision will use.

**M3. `final.json` at `w_final = 20` aliases the w=20 snapshot, whose incumbent is the step-start
incumbent before the last step's decision; a keep on the last step is lost and G6 audits the wrong
config.**
Revision 6c §4 (6c:104-105) says "at `w_final = 20` it is the w=20 snapshot", and §6 (6c:136) says G6
audits "the incumbent" in `final.json`. The engines update `self.incumbent` only after the step's
decision: FIXR3 at `d3_replicate.py:148` (first trial) and `:157` (keep), EGATE at `:230` (first trial)
and `:249` (commit). The w=20 snapshot is written by `on_charge` when the 20th run is charged — before
that decision — from `_trial.incumbent_config` (`snapshots.py:383`), which is the step-start incumbent.
So if the last step keeps a candidate, `final.json` (and the G6 audit, and Y_final) use the previous
incumbent. This is inherited from 5b's alias rule, but 6c repeats it for the replicate route and has a
clean `engine.incumbent` available after the last step. The design must write `final.json` from
`engine.incumbent` (and its worker config) at campaign end, or explicitly define the final incumbent as
the pre-last-step incumbent — which would contradict PD §7.1 ("the configuration of the campaign's last
kept trial"). Either way, Y_final is the primary outcome and this cannot be left implicit.

**M4. `campaign_chunk.py` has no replicate path and no per-campaign record writer; the claimed "chunk
records written by `campaign_chunk.py`" and "same record layout" are not implementable as delivered.**
Revision 6c §3 (6c:81-82) says the loop never calls `run_real_campaign`; §6 (6c:130-134) says the
campaign directory contains `campaign.json`, `ledger.jsonl`, `runs.jsonl`, `snapshots/...`, `summary.json`
and `SHA256SUMS`, and the chunk-level records are written by `campaign_chunk.py`. The delivered
`run_chunk` imports `run_real_campaign` (`r1/c3/d3/campaign_chunk.py:178`), requires the harness kwargs
`controller`, `compute_budget`, `snapshot_hook` (`:157-162`) and calls `run_real_campaign(**kwargs)` at
`:191`; per campaign it writes only `campaign.json` and the SHA tree (`:204-205`). The `CampaignFactory` contract
(`:149-154`) is explicitly a `run_real_campaign` kwargs factory. A replicate chunk therefore needs an
unstated branch in `run_chunk` plus a trial/ledger/runs writer (the harness writes those inside
`run_real_campaign`). Condition 3's "same record layout" is satisfiable only after that new code is
specified.

**M5. The 80-call LLM cap has no counter or budget object in the replicate route; `ChargedRunCounter` is
worker runs only, so "it is the only budget" is false and the cap is not enforced by the named code.**
Revision 6c §2 (6c:43-46) says the replicate route uses "the same `ChargedRunCounter(W=20,
on_charge=...)`; it is the only budget and is authoritative", and separately "80 per campaign, manager
proposal/revision calls". `ChargedRunCounter` (`accounting.py:165-225`) has `W`, `runs`, `used`, `left`,
`can_fund`, `require`, `charge`, `lookup`; it has no LLM-call counter or cap. `c3_budgets` returns a
`ComputeBudget(max_worker_runs=W, max_llm_calls=cap)` (`r1/c3/control.py:351-363`), and `campaign_usage`
counts LLM calls from `proposal_created`/`proposal_revised`/rejection events (`accounting.py:80-86`),
not from the counter. The design must name the LLM-call counter/event store and how each manager call is
charged before the call, or it cannot implement "the LLM cap is checked before each manager call"
(6c:120).

### MINOR

**m1. The `w_final = 0` record is not the canonical start record unless G1 sets `recorder.start_config`
manually, and its `controller_state_sha256` is empty.**
The core's w=0 branch (`snapshots.py:356-372`) uses `self.start_config or {}` and
`self._controller_state_at_hook` (initial `""`); `start_config` is set only at E0 (`:300-303`). A probe
of `write_final(w_final=0, ended_on="llm_call_cap")` gives `start_config == {}` and
`controller_state_sha256 == ""`. The delivered test `test_w_zero_final_uses_start_config`
(`r1/tests/test_d3_g1_chunk.py:167-172`) sets `rec.start_config` by hand; the design does not say G1 does
this for a replicate campaign. The design should also say that a w=0 campaign can only have ended at the
LLM cap (or `error`), because `table_ended_on` (`accounting.py:228-244`) has no other w=0 value.

**m2. "Schema unchanged" and "the only new field is `campaign_kind`" are inconsistent with the new
`pending_step`/`pending_j` fields and with the existing `arm` field.**
Revision 6c says the snapshot schema is unchanged (6c:86) but adds `pending_step` and `pending_j`
(6c:98-99); 5b's field list (5b:62-64) has only `pending_action`. Condition 5 (6c:168) says "the only new
field is `campaign_kind`", while §6 (6c:133-134) says `campaign.json` gains `campaign_kind` "and the arm
name"; `campaign.json` already has `arm` (`campaign_chunk.py:198`). This is editorial but it is exactly
the kind of field-contract statement a code reviewer will rely on.

**m3. The named `run_replicate_campaign` already exists with a different signature and end condition.**
Revision 6c §3 (6c:57) describes `run_replicate_campaign(engine, proposals, run, W=20, llm_cap=80,
on_charge=..., ...)` as a G1 module. `r1/c3/d3_replicate.py:265-285` already has
`run_replicate_campaign(engine, proposals: list[str], run, *, W=20, on_charge=None)`: no `llm_cap`, no
manager, no records, and it ends `proposals_exhausted` (a test-only end). If G1 imports it, it does not
get the declared loop. The design should name the new module/entry point and say whether the reference
loop is superseded.

**m4. The §6 campaign path omits the `campaigns/` segment.**
Revision 6c §6 (6c:130-131) gives `<run_root>/<stage>/<arm>/r<rep>/<instance_id>/`; 5b §2.1 (5b:39-41)
and `campaign_chunk.py:182` write `campaigns/<instance_id>/`. Condition 3's "same layout" is still true
if both routes use the chunk, but the path text is wrong as written.

**m5. `RunOutcome` has no failure cause, but §5 says failures are classified by G8
`classify_worker_failure`.**
`RunOutcome` carries only `success`, `metric`, `seconds` (`d3_replicate.py:42-52`);
`classify_worker_failure(cause, card_other_processes=..., host_other_processes=...)`
(`accounting.py:267-294`) needs a cause and, for `budget_hit`/`oom`, the card counts. G1 can classify in
its `run` wrapper and keep a side record, but the design does not say so; the engine's `StepResult` has
no field for it.

**m6. `RuleLayerController` is a harness controller and cannot be used as the replicate E1 without a
`ControlView`.**
Revision 6c §2 (6c:41) names `RuleLayerController(arm=..., rule_layer=False)` as the replicate E1.
`RuleLayerController.decide(view, mask)` (`r1/c3/d3_controllers.py:94-120`) requires a harness
`ControlView` and calls `featurize_view` (`:99-120`); the replicate loop has no `ControlView`, epoch or mask. G1 can
implement "execute every validated proposal" directly, but then the E1 claim should be reworded, or the
design should say how the controller is driven outside the harness.

**m7. `zero_variance_cases` is not in `StepResult` or the trial record.**
PD §5.4 says zero-variance cases are "counted and reported"; the engine increments
`self.zero_variance_cases` (`d3_replicate.py:124`, `:152`) but `StepResult` (`:71-79`) does not carry it,
and the design's trial-record contract (6c:72-74) does not mention it. G1 can read the engine attribute
at campaign end, but the design should say so if the count is to be reported.

## Conditions of §8

| # | Condition | Result | Evidence |
|---|---|---|---|
| 1 | Every actual worker call charged exactly once through the one `ChargedRunCounter`; reused incumbent never charged; counter/record/parity differences fail closed | **FAIL** | The counter itself is sound: `ChargedRunCounter.charge` (`accounting.py:197-217`) is one charge per call in the engines (`d3_replicate.py:135`, `:218`, `:234`); EGATE reuse is `lookup` with `charged: false` (`:190-191`, `:240-242`); `replicate_entries` validates the G8 record and `campaign_usage` counts it (`accounting.py:100-137`, `:59-97`); the 38 G8 tests pass. But the design puts the charge in `run` "including a call that raises" (6c:69-71), while the engines charge after a successful return and do not catch a raise (B1). The design's parity rule (6c:112-115) is G1-side and has no delivered implementation. The LLM cap has no counter (M5). |
| 2 | Step-start state before the first worker call; no manager/engine decision call between capture and any run; `controller_state_sha256` documented and deterministic; exact w=5,10,15,20 live, including inside FIXR3's 3-run step and EGATE's pair loop | **FAIL** | The counter's per-charge hook can hit exactly 5/10/15/20 (`test_counter_snapshot_hook_sees_every_budget_point_exactly`; 38 G8 tests pass), and FIXR3's loop charges singly. But the recorder has no `on_charge` and no replicate step-start API (B2: probe `hasattr(recorder, "on_charge") == False`; `write_final(20)` raises `SnapshotStop`), neither engine has `snapshot_state()` (B3: probes false), EGATE calls `gate.decide` between runs (B4: probe order), EGATE's state omits the incumbent's per-seed runs (M1), and in-step snapshots omit the accrued metrics/diffs (M2). |
| 3 | Same record layout, `campaign_id`, record name, `final.json` and G6 audit path as a harness arm; `extra.control.replicates` exactly the G8 contract | **FAIL** | `extra.control.replicates` matches: FIXR3 entries are candidate j=1,2 (no j=0), EGATE adds candidate j≥1 and incumbent entries, reuse is `charged:false`, and `replicate_entries` accepts them (`accounting.py:100-137`; FIXR3/EGATE tests pass). `campaign_id` = instance id and the record name are stated (6c:48), but no replicate record/ledger writer or chunk branch exists (M4), and `final.json` at w=20 aliases the pre-decision w=20 incumbent (M3), so the G6 audit can use the wrong config. |
| 4 | Implements §5.4/§5.5 without changing a rule or constant; `ended_on` follows `table_ended_on` | **PASS** | FIXR3 `r=3`, `alpha=0.05`, first-trial keep, failure at any j, zero-variance no-keep, incumbent reuse without a rerun (`d3_replicate.py:105-159`); EGATE `PaceStyleGate` α=0.1/clip=0.05/max_pairs=8, pair order, commit/reject, failed-candidate/incumbent rules (`:162-258`); seeds 6201-6218 and 6500+10i+j (`:59-68`; `d3_analysis.replicate_seeds`). `table_ended_on` (`accounting.py:228-244`) matches `d3_analysis._check_ended_on` (`d3_analysis.py:262-281`) and its six-case test. No rule/constant change found. Caveat: the LLM-cap enforcement is M5 and the reference loop's `proposals_exhausted` is test-only (m3), but neither changes a §5.4/§5.5 rule. |
| 5 | No evidence/label/evaluation/sealed read; only new field `campaign_kind` | **PASS** (no-read requirement) with **MINOR** m2 | The revision is documentation; `accounting._jsonl` calls `refuse_sealed` (`accounting.py:53-56`); the engines import only `d3_analysis` constants and `PaceStyleGate`; no label/evaluation/split/sweep-table read is introduced. The "only new field" clause is inaccurate because `pending_step`/`pending_j` are new snapshot fields and `arm` already exists (m2). |

## Internal-consistency questions

**Is the step-start state sufficient for the FIXR3 and EGATE decisions?**
FIXR3: yes for the decision — `incumbent_metrics` is engine state (`d3_replicate.py:123`, `:148`, `:157`)
and the candidate metrics are the step's runs. EGATE: no — the decision uses `_incumbent_run(counter, j)` /
`prior_inc.metric` (`:190-191`, `:206`, `:246`), which are in `ChargedRunCounter.runs`, not in the engine;
the "pairs already decided" are local `diffs` (`:200`, `:246`). A `snapshot_state()` without the counter
cannot supply them (M1).

**Does an exact-w snapshot inside a step remain replayable?**
No, not from the snapshot alone. The snapshot carries the step-start state and `pending_j`, but not the
already-charged candidate/incumbent metrics or the accrued diffs (M2). Replay requires re-running the
step's earlier runs, which are deterministic but are not part of the snapshot. If "replayable" means
"reconstructible from the snapshot plus the trial record and the deterministic seeds", the design should
say that; if it means "the snapshot records the decision state", it does not.

**Is the `w_final = 0` case coherent?**
Partly. `write_final(0)` is structurally accepted by the core, but only when `_trial is None` and
`start_config` is set (`snapshots.py:356-372`); the replicate route has no E0, so `start_config` is `{}`
and `controller_state_sha256` is `""` unless G1 sets them by hand (m1). `table_ended_on` can yield w=0
only at the LLM cap (or an excluded error), so the design should say "w=0 at the cap", not "before its
first valid trial" in general. Y=0 by rule is fine; the "canonical start record" claim is not, as the
record does not contain the start configuration.

**Does the revision correctly leave the verify-seed blocker on the harness arms only?**
Yes. The blocker is the pinned harness `_run_verify` seeds 1010-1209 colliding with the D21 noise-floor
block (G1 unit report §3.1). FIXR3 and EGATE use no KG verify: their engines take only `run(...)` on
seeds 6201-6218 and 6500+10i+j, and the replicate loop does not call `run_real_campaign` or
`run_trial_at_seed`. The design's statement at 6c:147-149 is correct as to the arms. Its "until the
author's row" clause is now stale: R1-D3-VERIFY-SEED (option A) is on `origin/main` `8b01ef6a`, and
R1-D3-PREDECL-R4 is the author's signature row for revision 4 (the document's freeze/publication still
follows its steps (3) and (5)). The design's "their unit reviews ... are still required" (6c:150-152)
remains true.

**Are the cited sha256 values correct?**
Yes, all seven in 6c §9:
`4b957986...` (5b), `0d696535...` (6b, on the base branch, not yet on `main` — consistent with "stacked"),
`bafa10e0...` (PD r4), `120f0767...` (G8 accounting), `554cbb9e...` (engines), `e93b2435...` (snapshots),
`9d0e2acb...` (chunk). I verified each with `git show <ref>:<path> | shasum -a 256`.

**What does the code not do without an unstated change?**
`recorder.on_charge` (B2); `engine.snapshot_state()` (B3); `run` charging on a raise (B1); a replicate
branch and trial/ledger/runs writer in `campaign_chunk.py` (M4); an LLM-call counter (M5); an EGATE
step-start state that includes the incumbent's runs (M1); a final incumbent at `w_final` after the last
step's decision (M3); a `RuleLayerController` E1 outside the harness (m6); and a `RunOutcome` failure
cause for G8 classification (m5). These are all named in the findings with file:line evidence.

## Scope and limits

**In scope.** The 6c design text, its §8 conditions, the seven cited files, the five internal-consistency
questions, and the interface between the design and the delivered code.

**Out of scope / not decided here.** The scientific arm set, W=20, cap 80, seeds, K=10, Y_final and the
FIXR3/EGATE rules (I found no change); the accepted 5b/6b text except where 6c relies on it; the level-2
verify-seed decision (resolved by R1-D3-VERIFY-SEED after the design was written; not re-litigated here);
the pre-declaration signature row (R1-D3-PREDECL-R4 on `8b01ef6a`; the document's freeze/publication is
separate) and the A1/A2/LADDER constants file; the tier-E review of the engines/accounting/snapshot core themselves; any campaign,
audit, label, evaluation, sealed read, GPU job or smoke. I did not modify `main`, `coord/*`, the reviewed
branch, the engine branch or the snapshot branch.

**Test evidence.** I ran only the delivered unit modules in scratch worktrees:
`r1/tests/test_d3_fixr3.py`, `test_d3_egate.py`, `test_d3_g8_accounting.py` → **69 passed**;
`r1/tests/test_d3_g1_snapshots.py`, `test_d3_g1_chunk.py` → **16 passed**. I did not run the full
`r1/tests` suite. There is **no** integration test for the replicate route + `SnapshotRecorder` +
`campaign_chunk.py`; the probes above are the evidence for the missing interfaces.

## Review record

- Review target: `origin/compute-d3-g1-design-r6c-20261127` @ `ed0ad83b`.
- Reviewed file sha256: `fdf0cf91ebe842c1135bbe85bddd2ea08806d0be7aeaa23802a2ab2ce6271024`.
- Base: `origin/main` @ `5c901d19` (this review branch is based on it; the reviewed branch is not merged).
- Verdict: **CHANGES REQUIRED** (four BLOCKING, five MAJOR, seven MINOR).

**Review file sha256:** `62d4aaae410920d5b4d8e70ffa71d4e522cb997b5de7493f2cf1f352a05453a1` — the sha256 of the review text above this line. The sha256 of the committed file (this line included) is reported in the commit message and in the reviewer's report.

*Prepared by a fresh independent reviewer; no part of the reviewed work was authored by this session.*
