# D.3 G1/G6 — revision 6c: the replicate-arm driver (FIXR3, EGATE) outside `run_real_campaign`

**Status:** DESIGN REVISION, revision 6c-3 (27 Nov 2026). Level 1: an engineering decision inside the accepted
D.3 arm set and the accepted G1/G6 design revision 5b, requested by `tasks/compute/20261127-09-g1-next.md`
item 2. It changes neither which evidence is collected nor how it is read: the FIXR3/EGATE rules, seeds,
W = 20, LLM cap 80, K = 10 audit and Y_final remain exactly as the pre-declaration and revision 5b state.
No code, no campaign, no audit, no label or evaluation read was made for this revision.

Revision 6c-1 (`ed0ad83b`) was reviewed `CHANGES REQUIRED` (`docs/r1/reviews/D3_G1_G6_REV6C_REVIEW_20261127.md`,
commit file sha256 `041c3c0383f3970b74eed034a2d3b1721117a4734eb8fa3d360c12f29c3e6136`; its self-line content hash is
`c9c136d19d7c8f097199509d7b324b34e8426125b2bec1a3da6f12cdbc443b9a`). Revision 6c-2 (`690e8626`) was re-reviewed
`CHANGES REQUIRED` (`docs/r1/reviews/D3_G1_G6_REV6C_REVIEW_R2_20261127.md`, review file sha256
`686d3277d3c01868149406968e8ac8c38a1e2e497cc47f65266c5f6e7cfaf5d1`). This revision answers B1–B4, M1–M5, m1–m7 and
the 6c-2 N1–N9 in §10. It is stacked on revision 6b
(`D3_G1_G6_DESIGN_REV6_LAUNCHERS_20261126.md`, sha256
`0d696535d94395c85592c7ac9483790483966bbe0bf48961d132c50aa49b922d`, `ACCEPTED FOR CODE`), itself on revision 5b
(`D3_G1_G6_DESIGN_20261126.md`, sha256
`4b95798659c13feeef02af02504d68f138e40cdaf056ded0b89a09fbcc4e3a23`). The D.3 pre-declaration revision 4
is `docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md`, sha256
`bafa10e0bae89565cf9a17d4bed697647f5e4ab0bf6f067c6ccdbad3a9285769` (§5.4 FIXR3, §5.5 EGATE, §4.1 seeds,
§12 G3/G4). The verify-seed row R1-D3-VERIFY-SEED (main `8b01ef6a`) does not affect this route: FIXR3 and
EGATE have no KG verify.

## 1. The gap this revision closes

Revision 5b §3.3 requires a G1 runner-level charged-run hook, and the coordinator's option 1 (task
`compute/20261127-04`) implements it as a worker wrapper around `run_real_campaign`. That route fits A0, A0R,
A1, A2, LADDER and the learned arms because their E2 decision is a harness `Controller.decide` over the
trial's one run (plus verify for A1/A2/A3/A5/A6).

It does not fit FIXR3 and EGATE. Their delivered engines are harness-free state machines
(`r1/c3/d3_replicate.py` on `mac-d3-egate-20261127`, sha256
`554cbb9e6c79a4f9b6b9cb2e1f1da5dbf113e2ae32e7236314261b547e357c60`), because the pinned harness `a3fedbbd`
has no controller action that runs one configuration several times. `Fixr3Engine.step` needs 3 runs on seeds
j = 0, 1, 2; `EgateEngine.step` runs candidate/incumbent pairs on seeds j = 0..7. Neither can be passed to
`run_real_campaign(controller=...)`, and their replicate runs must still be charged singly, snapshotted at
exact w and audited like every other arm.

**Decision.** A replicate arm runs in a G1-owned campaign loop outside `run_real_campaign`, with the same
campaign budget construction, the same exact-w snapshot contract, the same record layout and the same G6
audit as a harness arm. The engines decide E2; G1 owns E1 (execute every validated proposal), the manager
calls, the worker calls, the single W counter, the snapshots and the records.

## 2. One campaign contract for both routes

| Element | Harness arms (A0, A0R, A1, A2, LADDER, A3, A5, A6) | Replicate arms (FIXR3, EGATE) |
|---|---|---|
| Loop | `run_real_campaign` with the reviewed `wrap(...)` worker/controller wrapper | new `run_replicate_chunk` G1 loop (§3); the existing test-only `run_replicate_campaign` is not used |
| E1 | harness/controller E1 | G1 validates the active keys and executes every validated proposal; no `RuleLayerController` and no `ControlView` are used |
| E2 | harness `Controller.decide` | `Fixr3Engine.step` / `EgateEngine.step` (unchanged rules) |
| Budget | G8 `ChargedRunCounter(W=20, on_charge=...)`; `ParityBudget` also observes the harness `ComputeBudget` and asserts equality | the same `ChargedRunCounter`, plus a `ComputeBudget(max_worker_runs=20, max_llm_calls=80)`; parity is asserted after every run (§5) |
| Charged-run parity | wrapper count == `ComputeBudget.worker_runs` at E0/E1/E2 and at end | `ChargedRunCounter.used` == `ComputeBudget.worker_runs` == the engine's `runs_charged` at every step end and at campaign end |
| Snapshots | `SnapshotRecorder` writes live `w` = 5, 10, 15, 20 and `final.json` | the same recorder, extended by the G1 unit with `begin_step` / `on_charge` / `write_final_from_state` (§4); same schema plus one optional `pending` object |
| LLM cap | 80 per campaign, harness + controller calls | 80 per campaign, manager proposal/revision calls; replicate engines make no LLM call; `ComputeBudget.llm_calls` is charged before every manager call and cross-checked against `campaign_usage` |
| Seeds | instance seed 6201–6218; replicate j = 0 instance seed; j ≥ 1 `6500 + 10i + j` | identical; FIXR3 uses j ≤ 2, EGATE j ≤ 7 (§4.1) |
| Records | one campaign directory per `(stage, arm, instance, repetition)` | identical; `campaign_id` = instance id; record name `stage__arm__instance__r<rep>` |
| Audit (G6) | reads `final.json` and the `w` snapshots | identical; no arm-specific audit path |

`ChargedRunCounter` is the G8 unit (`r1/c3/accounting.py` on `mac-d3-egate-20261127`, sha256
`120f07673448906444dbcb9a3e8b3822fa5147ad863a2af6c016e9a69d45634f`). Its `on_charge(ChargedRun)` hook is the
single place from which a snapshot is written; no arm may write a snapshot from its own state reconstruction.
`ComputeBudget` is the harness class (`src/autoresearch/control_plane/budget.py` at `a3fedbbd`).

## 3. The replicate-arm loop

A new G1 module `r1/c3/d3/replicate_campaign.py` (part of the G1 code unit, not the engines) provides:

```text
run_replicate_chunk(spec, instance_id, repetition, engine, manager, worker, out_dir) -> summary
```

One campaign is one instance (`campaign_id` = instance id) and one repetition.

1. Construct `budget = ComputeBudget(max_worker_runs=20, max_llm_calls=80)` and
   `counter = ChargedRunCounter(W=20, on_charge=recorder.on_charge)`. These two objects are created by one
   factory for every arm; the replicate route has no harness `ComputeBudget` shadow, but the parity check of §5
   makes the counter and the budget equal at every step.
2. Ask the manager for proposal 0 through the normal `manager_proposal/v1` path. `ComputeBudget` is frozen, so the
   loop keeps it in a mutable holder and reassigns the returned object:
   `budget_holder["value"] = budget_holder["value"].consume_llm_call()` before the call; a call that would take
   `llm_calls` past 80 is not made and ends the campaign `llm_call_cap`. Each proposal/revision event
   is recorded so `campaign_usage` counts the same calls. A re-issued call after an infrastructure failure is
   logged `llm_call_reissued` and is not counted (R1-NO-TIMEOUT (1)).
3. Validate the proposal against the node's active keys exactly as E1 does. A control-plane rejection costs no
   worker run and is not a proposal for the arm; it still costs its LLM call.
4. At **step start**, after validation and before the first worker call, call
   `recorder.begin_step(trial_id=..., incumbent_config=incumbent_config, start_config=start_config,
   state=projection(engine, counter), last_kept_trial_index=..., llm_calls=budget_holder["value"].llm_calls,
   step_index=step_index)` (§4). `incumbent_config` is the **config contents** of the last kept trial
   (`start_config` before the first keep); the recorder computes `config_sha256` from those contents, as the
   harness path does. `engine.incumbent` is used only for the EGATE lookup and the projection.
5. Call `engine.step(config_sha256, run_one, counter)`. `run_one(role, config_sha256, seed, j)`:
   - calls the worker exactly once;
   - catches any worker exception and records its cause and the card/host process counts in a G1
     `RunAttempt` side record, then returns `RunOutcome(success=False)`;
   - maps `config_sha256` to the current step's validated proposal/config (`config_by_sha`; the worker receives the
     proposal, not the sha) and, if the previous step discarded its candidate, restores the incumbent workspace
     before this call;
   - reassigns the frozen budget in its holder: `budget_holder["value"] =
     budget_holder["value"].consume_worker_run(seconds)` **before** the engine charges the counter, but does **not**
     charge the counter itself; The engine's own `counter.charge(...)` is the single charge, including for the failed
     `RunOutcome` just returned. A reused incumbent run in EGATE is not a `run_one` call and charges neither.
   This is the engine-owned layering (B1): it needs no engine change, and a raising worker call is still
   charged because G1 converts it to a failed `RunOutcome` before the engine's charge.
6. After `engine.step` returns, assert `counter.used == budget.worker_runs == cumulative engine charges` and
   `budget.llm_calls == the proposal/revision event count`; any difference is a STOP. A charge beyond W is
   `OverBudget` and a STOP.
7. Write one trial record for the step with `extra.control.replicates` exactly as G8 requires (the candidate
   j = 0 run is the trial's own worker run; j ≥ 1 candidate and all executed incumbent runs are entries; a
   reused incumbent run is `charged: false`). Record `zero_variance_cases`, `trial_id`,
   `last_kept_trial_index`, `llm_calls` and the G1 `RunAttempt` failure classes in `extra.control` / `summary.json`
   (§5).
8. Ask for the next proposal while `counter.left` and the LLM cap allow. `UnfundableStep` ends the campaign
   `no_fundable_candidate`; `w = 20` ends it `worker_runs`; an empty proposal stream at the cap ends it
   `llm_call_cap` (an internal error ends it `error`, excluded from the table).
9. Write `snapshots/final.json` **after the last step's decision** from the final config contents at the actual
   `w_final` (§4); then write `summary.json` and `SHA256SUMS` as the chunk shell does.

The loop never calls `run_real_campaign`; it uses the same `LocalWorker`, node spec, manager, proposal schema
and record writers as the harness route. It does not resume and refuses an existing campaign directory.

## 4. Snapshot semantics for a replicate arm

The snapshot schema is the revision 5b schema plus one optional `pending` object (§10 m2). The difference from
the harness route is the meaning of "the last E1 hook":

- **Step-start state.** `recorder.begin_step(trial_id, incumbent_config, start_config, state, last_kept_trial_index, llm_calls,
  step_index)` records the state that the step's E2 decision will see: `incumbent_config` (the **config contents
  dict** of the kept configuration before this step, not its sha), `start_config` (contents),
  `last_kept_trial_index`, `llm_calls`, `trial_id`, `w` (read from `recorder.count` at the charge), the step
  index, and the engine projection. The recorder computes `config_sha256 = config_sha256(incumbent_config)`. The projection is built by G1, not by an engine method
  (B3), from the documented ordered fields:
  - common: `arm`, `version`, `instance_seed`, `steps`, `incumbent`, `seeds`;
  - FIXR3: `incumbent_metrics` (three oriented values), `zero_variance_cases`;
  - EGATE: `incumbent_runs`, one `{j, seed, success, metric, charged}` (or `null`) for each j = 0..7, read from
    `counter.lookup(engine.incumbent, seed)` (M1). This is the state EGATE's next pair needs.
  `controller_state_sha256` hashes `json.dumps(projection, sort_keys=True, separators=(",", ":"))`; there is no
  `repr`, object id, time or set iteration. An unknown arm is refused, not hashed by fallback.
- **Exact w.** Every charge calls `recorder.on_charge(ChargedRun)`. If the post-charge `w` is in
  {5, 10, 15, 20}, the recorder writes `snapshots/w<w>.json` immediately, before the next worker call. Because
  every run is charged singly, a boundary is never crossed by a block charge, including inside a 3-run FIXR3
  step or an 8-pair EGATE step.
- **In-flight action.** A boundary inside a step carries `pending_action = "fixr3_step"` or `"egate_pair"` and a
  `pending` object `{step, j, candidate_metrics, incumbent_metrics, diffs}` built by G1 from the `RunAttempt`
  log (all successful metrics so far in the step, oriented differences already formed). The controller state is
  the step-start state; `pending` makes the in-step decision state replayable without re-running the charged
  runs (M2).
- **No step-ending decision in flight.** G1 asserts that no manager proposal/revision call and no step-ending
  E2 decision (the call that sets `engine.incumbent` or returns `StepResult`) occurs between the step-start
  capture and any worker call of that step. EGATE's per-pair `gate.decide` calls are **inside** the step and
  are allowed: they do not change `incumbent` (B4).
- **Final.** `final.json` is written after the loop from `engine.incumbent` (or `start_config` when no trial was
  kept) at the actual `w_final`, with `ended_on`. At `w_final = 20` it is a **separate post-decision record**,
  not an alias of `snapshots/w20.json`: the w=20 snapshot is the pre-decision exact-w state, while
  `final.json` carries the configuration contents of the campaign's last kept trial (PD §7.1):
  `write_final_from_state(w_final, ended_on, incumbent_config=final_config, state=projection(engine, counter),
  ...)`; the recorder computes `config_sha256` from `final_config`. The harness route keeps its own
  5b rule unchanged; the replicate exact-w snapshot is pre-decision, so its `final.json` is necessarily a separate
  post-decision record (M3). At
  `w_final = 0` G1 sets `start_config` and the step-start projection explicitly; the only legal `ended_on` is
  `llm_call_cap` (or the excluded `error`) (m1).

The harness route keeps its own rule unchanged: the state is the E1 capture before the E1 decision, and verify
runs carry that state with `pending_action = "verify"`.

## 5. Parity, failures and end conditions

- **Parity.** `counter.used == budget.worker_runs` at every step end and at campaign end; `budget.llm_calls`
  equals the proposal/revision event count. A difference, a trial record whose replicate entries disagree with
  the counter, or a charge without a run is a STOP; nothing is repaired or imputed. For a harness arm the
  additional `ComputeBudget` equality check of the reviewed core still applies.
- **Worker failures.** `run_one` turns a worker exception into `RunOutcome(success=False)` and stores its cause
  and the card/host process counts in a `RunAttempt` record; G8 `classify_worker_failure` classifies it. The
  engine charges the failed run and applies §5.4/§5.5: FIXR3 `failed_invalid`, EGATE `failed_invalid` or
  `incumbent_failed`. An infrastructure failure loses the whole attempt (rerun whole in a new directory,
  nothing of the lost attempt charged). No failed run is retried inside a campaign.
- **Budget and cap.** `UnfundableStep` before a step charges nothing and ends `no_fundable_candidate`. A charge
  beyond W is `OverBudget`, a STOP. The LLM cap is charged before each manager call; a call that would exceed
  80 is not made and the campaign ends `llm_call_cap`.
- **`ended_on`.** Use G8 `table_ended_on` (the pinned analysis rule): `worker_runs` whenever `w = W`, even if
  the LLM cap is also reached; otherwise `llm_call_cap`; otherwise `no_fundable_candidate`. `stop`/`error`
  campaigns are excluded from the outcome table. This corrects the precedence sentence in revision 5b §3.3, as
  G8's unit report requested; the set of values is unchanged.
- **STOP classes.** The §10 list of revision 5b applies unchanged. A killed or non-clean chunk is recovered
  whole in a new directory and disclosed; it is not a STOP class.

## 6. Records and G6

The campaign directory is the revision-6b layout with the `campaigns/` segment:
`<run_root>/<stage>/<arm>/r<rep>/campaigns/<instance_id>/` with `campaign.json`, `ledger.jsonl`, `runs.jsonl`,
`snapshots/w{5,10,15,20}.json`, `snapshots/final.json`, `summary.json` and `SHA256SUMS`; the chunk-level
`chunk.json`, `summary.json` and `SHA256SUMS` are written by `campaign_chunk.py`. `campaign.json` gains
`campaign_kind: "harness" | "replicate"`; `arm` is already present. The G1 code unit adds a replicate branch to
`run_chunk` and the per-campaign writer functions (`campaign.json`, `ledger.jsonl`, `runs.jsonl`,
`summary.json`, `SHA256SUMS`) that the harness route gets from `run_real_campaign` (M4).

G6 reads only `snapshots/final.json` and the `w` snapshots, audits the incumbent against the start config on
seeds 6700 + 10i + k, K = 10, and writes the same `r1_d3_audit_row` records. It does not know or care which
route produced a snapshot. Y_final is the primary outcome; Y(w) remains the descriptive R1-D3-OUTCOMES2 curve
under the pre-declaration's `y_raw_w` (revision 4), and is not substituted for Y_final.

## 7. What this revision does not change

- The FIXR3 and EGATE rules, constants (r = 3, α = 0.05; PaceStyleGate α = 0.1, clip = 0.05, max_pairs = 8),
  seeds, failure rules and `verify:pace` action version stay exactly as §5.4/§5.5 of the pre-declaration. The
  engines are used as delivered; the only interface added is G1's `run_one`/projection around them.
- W = 20, LLM cap 80, the 18 instances, the arm list, the seven nodes, the audit seeds, K = 10 and Y_final are
  unchanged.
- The harness arms and the reviewed snapshot core are unchanged except for the additive
  `begin_step` / `on_charge` / `write_final_from_state` API, which the G1 unit adds and its review covers; the
  existing harness path and its tests are untouched.
- The verify-seed collision blocks every harness verify arm (A1, A2, A3, A5, A6) until the new reviewed harness
  pin of R1-D3-VERIFY-SEED; it does **not** block the FIXR3/EGATE route, because FIXR3 and EGATE use no KG
  verify.
- The A1/A2/LADDER constants file (G2) and the signed revision 4 remain prerequisites for those harness arms.
  FIXR3 and EGATE need no constants file; their unit reviews, the pre-declaration's freeze/publication (its steps
  (3) and (5), including the G2 file and the verify-seed check for the harness arms) are still required before any
  evidence run. R1-D3-PREDECL-R4 is on `main` and is binding in its own order, not yet frozen.
- No Y(w) analysis code, no G7/G6 code and no per-arm smoke is authorized or changed here.

## 8. Conditions for the independent review

The revision is `ACCEPTED FOR CODE` only if the reviewer confirms, with file and test evidence:

1. The replicate loop charges every actual worker call exactly once through the one `ChargedRunCounter`
   (engine-owned, with `run_one` converting exceptions to a failed `RunOutcome`), never charges a reused
   incumbent run, and fails closed on any counter/budget/record/parity difference.
2. The snapshot state is the step-start projection of §4 (including EGATE's incumbent runs from the counter);
   no manager call or step-ending E2 decision occurs between that capture and any run of the step; the
   projection hash is documented and deterministic; exact `w` = 5, 10, 15, 20 is written live, including inside
   FIXR3's 3-run step and EGATE's pair loop; `pending` records the in-step metrics/diffs.
3. The same record layout (with `campaigns/<instance_id>/`), `campaign_id`, record name, `final.json` and G6
   audit path are used as for a harness arm; `extra.control.replicates` is exactly the G8 contract; `final.json`
   is the post-decision incumbent, so a keep on the last step is audited.
4. The loop implements §5.4/§5.5 without changing a rule or constant, the LLM cap is charged through
   `ComputeBudget` before each manager call, and `ended_on` follows `table_ended_on`.
5. No evidence, label, evaluation or sealed read is introduced; the new record fields are `campaign_kind`, the
   optional `pending` object, and the trial/summary `extra.control` fields `zero_variance_cases` and the
   `RunAttempt` failure classes (`replicates` is the existing G8 field).

## 9. References

| File | sha256 |
|---|---|
| revision 5b design | `4b95798659c13feeef02af02504d68f138e40cdaf056ded0b89a09fbcc4e3a23` |
| revision 6b launchers | `0d696535d94395c85592c7ac9483790483966bbe0bf48961d132c50aa49b922d` |
| pre-declaration revision 4 | `bafa10e0bae89565cf9a17d4bed697647f5e4ab0bf6f067c6ccdbad3a9285769` |
| G8 accounting (`mac-d3-egate-20261127`) | `120f07673448906444dbcb9a3e8b3822fa5147ad863a2af6c016e9a69d45634f` |
| replicate engines (`mac-d3-egate-20261127`) | `554cbb9e6c79a4f9b6b9cb2e1f1da5dbf113e2ae32e7236314261b547e357c60` |
| snapshot core (`compute-d3-g1-snapshot-20261127`) | `e93b24356b43ffb54a17141b350a3bab45972e84a5ecb22a1a44eaffc8e29f73` |
| chunk shell (`compute-d3-g1-snapshot-20261127`) | `9d0e2acb4b5e42aeabba1e6989c788f3c66991eb27fbca535dc2b2542c4e55f9` |
| 6c-1 review (CHANGES REQUIRED) | `c9c136d19d7c8f097199509d7b324b34e8426125b2bec1a3da6f12cdbc443b9a` |

## 10. Response to the 6c-1 review

| Finding | Resolution in 6c-2 |
|---|---|
| **B1** charge layering | The engine owns the charge; `run_one` never charges the counter. It catches a worker exception, records the cause and returns `RunOutcome(success=False)`, so the engine's existing `counter.charge` runs exactly once even for a raised call. §3.5. |
| **B2** no `SnapshotRecorder.on_charge` | The G1 unit adds the public `begin_step`, `on_charge` and `write_final_from_state` API to the reviewed recorder, with tests for the replicate path; the harness path is unchanged. §4, §7. |
| **B3** no `engine.snapshot_state()` | G1 builds the documented ordered projection from public engine fields and the counter; no engine method is required and no fallback hash is used. §4. |
| **B4** EGATE `gate.decide` inside a step | The assertion is narrowed to manager calls and the step-ending E2 decision; per-pair `gate.decide` calls are part of the step and do not change `incumbent`. §4. |
| **M1** EGATE state needs incumbent runs | The projection includes `incumbent_runs` read from `counter.lookup` for j = 0..7. §4. |
| **M2** in-step snapshots not replayable | The snapshot carries a `pending` object with the step's candidate/incumbent metrics and diffs, built by G1 from its `RunAttempt` log. §4, §8. |
| **M3** w=20 alias loses a last-step keep | `final.json` is written after the loop from `engine.incumbent`; it is a separate post-decision record, not an alias of `w20.json`. §4. |
| **M4** no replicate path/record writer in the chunk shell | The G1 unit adds `run_replicate_chunk` and the per-campaign record writers; the path includes `campaigns/<instance_id>/`. §6. |
| **M5** no LLM-call counter | `ComputeBudget(max_worker_runs=20, max_llm_calls=80)` is constructed with the counter; `consume_llm_call()` runs before every manager call and is cross-checked against `campaign_usage`. §3.2, §5. |
| **m1** w=0 start record | G1 sets `start_config` and the projection explicitly; only `llm_call_cap`/`error` can end at w=0. §4. |
| **m2** field contract | The new record fields are `campaign_kind` and the optional `pending` object; `arm` already exists. §6, §8. |
| **m3** existing `run_replicate_campaign` | The new entry point is `run_replicate_chunk`; the existing function is a test-only reference loop and is not used. §2, §3. |
| **m4** missing `campaigns/` segment | The path now includes `campaigns/<instance_id>/`. §6. |
| **m5** `RunOutcome` has no cause | `run_one` keeps a `RunAttempt` side record with the cause and card/host counts; G8 classifies it. §5. |
| **m6** `RuleLayerController` outside harness | E1 is implemented directly as validate-and-execute; no `ControlView` or controller object is used. §2. |
| **m7** zero-variance count not reported | G1 reads `engine.zero_variance_cases` into the trial record/summary. §3.7, §5. |

## 11. Response to the 6c-2 re-review

| Finding | Resolution in 6c-3 |
|---|---|
| **N1** frozen `ComputeBudget` not reassigned | The loop keeps the budget in a mutable holder and reassigns every `consume_worker_run` / `consume_llm_call` return; the parity and cap checks read the holder. §3.2, §3.5. |
| **N2** `engine.incumbent` is a sha, not config contents | `begin_step` and `write_final_from_state` take `incumbent_config` / `final_config` (contents dict); the recorder computes `config_sha256`, as in the harness path. G1 keeps the kept config and restores the incumbent workspace after a discard. §3.4, §4. |
| **N3** missing `trial_id`, `last_kept_trial_index`, `llm_calls` | These are explicit `begin_step`/`write_final_from_state` arguments and are written into `extra.control`; `w` comes from `recorder.count`. §3.4, §3.7, §4. |
| **N4** wrong harness w=20 comparison | The harness route is stated unchanged; the replicate `final.json` is separate because its exact-w snapshot is pre-decision. §4. |
| **N5** field list incomplete | Condition 5 now names `campaign_kind`, `pending`, `zero_variance_cases` and the `RunAttempt` failure classes; `replicates` is the existing G8 field. §8. |
| **N6** G2 listed as a FIXR3/EGATE prerequisite | Corrected: G2 is a harness-arm prerequisite; FIXR3/EGATE need no constants file. §7. |
| **N7** worker proposal/config mapping and restore unstated | `run_one` maps `config_sha256` to the validated proposal config and restores the incumbent workspace after a discard. §3.5. |
| **N8** prior-review sha citation | Both the 6c-1 commit file sha and its self-line content hash are cited in the header. |
| **N9** pre-declaration status | The text now says R1-D3-PREDECL-R4 is on `main`, binding in its own order and not yet frozen, rather than "signature still required". §7. |
