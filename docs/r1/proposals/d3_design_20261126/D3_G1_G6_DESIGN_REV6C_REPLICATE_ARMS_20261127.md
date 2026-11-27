# D.3 G1/G6 — revision 6c: the replicate-arm driver (FIXR3, EGATE) outside `run_real_campaign`

**Status:** DESIGN REVISION, revision 6c (27 Nov 2026). Level 1: an engineering decision inside the accepted D.3
arm set and the accepted G1/G6 design revision 5b, requested by `tasks/compute/20261127-09-g1-next.md` item 2. It
changes neither which evidence is collected nor how it is read: the FIXR3/EGATE rules, seeds, W = 20, LLM cap 80,
K = 10 audit and Y_final remain exactly as the pre-declaration and revision 5b state. No code, no campaign, no
audit, no label or evaluation read was made for this revision.

This revision is stacked on revision 6b (`D3_G1_G6_DESIGN_REV6_LAUNCHERS_20261126.md`, sha256
`0d696535d94395c85592c7ac9483790483966bbe0bf48961d132c50aa49b922d`, `ACCEPTED FOR CODE`). Revision 5b is
`D3_G1_G6_DESIGN_20261126.md`, sha256 `4b95798659c13feeef02af02504d68f138e40cdaf056ded0b89a09fbcc4e3a23`.
The D.3 pre-declaration revision 4 is `docs/r1/authorizations/D3_PREDECLARATION_DRAFT_20261122.md`, sha256
`bafa10e0bae89565cf9a17d4bed697647f5e4ab0bf6f067c6ccdbad3a9285769` (unsigned draft; §5.4 FIXR3, §5.5 EGATE,
§4.1 seeds, §12 G3/G4).

## 1. The gap this revision closes

Revision 5b §3.3 requires a G1 runner-level charged-run hook, and the coordinator's option 1 (task
`compute/20261127-04`) implements it as a worker wrapper around `run_real_campaign`. That route fits A0, A0R, A1, A2,
LADDER and the learned arms because their E2 decision is a harness `Controller.decide` over the trial's one run (plus
verify for A1/A2/A3/A5/A6).

It does not fit FIXR3 and EGATE. Their delivered engines are harness-free state machines
(`r1/c3/d3_replicate.py` on `mac-d3-egate-20261127`, sha256
`554cbb9e6c79a4f9b6b9cb2e1f1da5dbf113e2ae32e7236314261b547e357c60`), because the pinned harness `a3fedbbd` has no
controller action that runs one configuration several times. `Fixr3Engine.step` needs 3 runs on seeds j = 0, 1, 2;
`EgateEngine.step` runs candidate/incumbent pairs on seeds j = 0..7. Neither can be passed to
`run_real_campaign(controller=...)`, and their replicate runs must still be charged singly, snapshotted at exact w
and audited like every other arm.

**Decision.** A replicate arm runs in a G1-owned campaign loop outside `run_real_campaign`, with the same campaign
budget object, the same exact-w snapshot contract, the same record layout and the same G6 audit as a harness arm.
The engines decide E2; G1 owns E1 (execute every proposal), the manager calls, the worker calls, the single W
counter, the snapshots and the records.

## 2. One campaign contract for both routes

| Element | Harness arms (A0, A0R, A1, A2, LADDER, A3, A5, A6) | Replicate arms (FIXR3, EGATE) |
|---|---|---|
| Loop | `run_real_campaign` with the reviewed `wrap(...)` worker/controller wrapper | G1 `run_replicate_campaign` (§3) |
| E1 | harness/controller E1 | `RuleLayerController(arm=..., rule_layer=False)`: execute every validated proposal, no screen |
| E2 | harness `Controller.decide` | `Fixr3Engine.step` / `EgateEngine.step` |
| Budget object | G8 `ChargedRunCounter(W=20, on_charge=...)`; `ParityBudget` also observes the harness `ComputeBudget` and asserts equality | the same `ChargedRunCounter(W=20, on_charge=...)`; it is the only budget and is authoritative |
| Charged-run parity | wrapper count == `ComputeBudget.worker_runs` at E0/E1/E2 and at end; mismatch is a STOP | counter charges == actual worker-run calls at every step end and at campaign end; mismatch is a STOP |
| Snapshots | `SnapshotRecorder` writes live `w` = 5, 10, 15, 20 and `final.json` | same `SnapshotRecorder`, same schema, same exact-w rule (§4) |
| LLM cap | 80 per campaign, harness + controller calls | 80 per campaign, manager proposal/revision calls; replicate engines make no LLM call |
| Seeds | instance seed 6201–6218; replicate j = 0 instance seed; j ≥ 1 `6500 + 10i + j` | identical; FIXR3 uses j ≤ 2, EGATE j ≤ 7 (§4.1) |
| Records | one campaign directory per `(stage, arm, instance, repetition)` | identical; `campaign_id` = instance id; record name `stage__arm__instance__r<rep>` |
| Audit (G6) | reads `final.json` and the `w` snapshots | identical; no arm-specific audit path |

`ChargedRunCounter` is the G8 unit (`r1/c3/accounting.py` on `mac-d3-egate-20261127`, sha256
`120f07673448906444dbcb9a3e8b3822fa5147ad863a2af6c016e9a69d45634f`). Its `on_charge(ChargedRun)` hook is the single
place from which a snapshot is written; no arm may write a snapshot from its own state reconstruction.

## 3. The replicate-arm loop

`run_replicate_campaign(engine, proposals, run, W=20, llm_cap=80, on_charge=..., ...)` is a G1 module, not a change
to the engines. One campaign is one instance (`campaign_id` = instance id) and one repetition.

1. Create `ChargedRunCounter(W=20, on_charge=recorder.on_charge)` and a `SnapshotRecorder` for the campaign directory.
2. Ask the manager for proposal 0 through the normal `manager_proposal/v1` path. Each manager proposal or revision is
   one charged LLM call; at 80 the campaign ends `llm_call_cap`. A re-issued call after an infrastructure failure is
   logged `llm_call_reissued` and is not counted (R1-NO-TIMEOUT (1)).
3. Validate the proposal against the node's active keys exactly as E1 does. A control-plane rejection costs no worker
   run and is not a proposal for the arm; it still costs its LLM call.
4. Capture the **step-start state** (§4) after validation and before the first worker call. Call
   `engine.step(config_sha256, run, counter)`; `run(role=..., config_sha256=..., seed=..., j=...)` executes exactly one
   worker run and returns the engine's `RunOutcome`.
5. `run` charges the counter exactly once per actual worker call, including a call that raises: `kind="trial"` for
   the candidate's j = 0 run, `kind="replicate"` for every other run. A reused incumbent run in EGATE
   (`charged: false`) is not a worker call and charges nothing. A charge beyond W raises `OverBudget` and is a STOP.
6. The engine returns one `StepResult`. G1 writes one trial record for the step with `extra.control.replicates`
   exactly as G8 requires (the candidate j = 0 run is the trial's own worker run; j ≥ 1 candidate and all executed
   incumbent runs are entries; a reused incumbent run is `charged: false`). The step's E2 decision is in the record.
7. Ask for the next proposal while `counter.left` and the LLM cap allow. `UnfundableStep` ends the campaign
   `no_fundable_candidate`; `w = 20` ends it `worker_runs`; an empty proposal stream at the cap ends it
   `llm_call_cap` (an internal error ends it `error`, excluded from the table).
8. Write `snapshots/final.json` at the actual `w_final` (alias of `w=20` when `w_final = 20`; `w = 0` when the
   campaign ends before its first valid trial). Then write `summary.json` and `SHA256SUMS` as the chunk shell does.

The loop never calls `run_real_campaign`; it uses the same `LocalWorker`, node spec, manager, proposal schema and
record writers as the harness route. It does not resume and refuses an existing campaign directory.

## 4. Snapshot semantics for a replicate arm

The snapshot schema is unchanged from revision 5b §2.2. The only difference is the meaning of "the last E1 hook":

- **Step-start state.** At step start (after the proposal is validated, before run 0) G1 records the state that the
  step's E2 decision will see: `incumbent_config` (the kept config before this step), `start_config`,
  `last_kept_trial_index`, `w` at the step start, the engine's deterministic public state, and the step index. For
  FIXR3 this includes the incumbent's three oriented metrics; for EGATE the incumbent config and the pairs already
  decided. `controller_state_sha256` hashes a documented, ordered projection of exactly these fields
  (`json.dumps(..., sort_keys=True)` over plain values; no object ids, times, sets or floats formatted by `repr`).
  `engine.snapshot_state()` returns the projection; an engine without it is refused, not hashed by fallback.
- **Exact w.** Every charge calls `on_charge(ChargedRun)`. If the post-charge `w` is in {5, 10, 15, 20}, the recorder
  writes `snapshots/w<w>.json` immediately, before the next worker call. Because every run is charged singly, a
  boundary is never crossed by a block charge, including inside a 3-run FIXR3 step or an 8-pair EGATE step.
- **In-flight action.** A boundary inside a step carries `pending_action = "fixr3_step"` or `"egate_pair"`, plus
  `pending_step` (the step index) and `pending_j` (the replicate/pair ordinal). The controller state is the
  step-start state, because no E2 decision occurs between step start and the last run of the step; the accrued
  candidate/incumbent differences are part of the in-flight action, not part of the controller state.
- **No controller call in flight.** G1 asserts that no manager proposal/revision call and no engine decision call
  occurs between the step-start capture and any worker call of that step. A violation is a STOP (fail closed).
- **Final.** `final.json` carries `ended_on` and the actual `w_final`; at `w_final = 20` it is the `w=20` snapshot,
  at `w_final = 0` it is the canonical no-audit record (Y_final = 0 by rule).

The harness route keeps its own rule unchanged: the state is the E1 capture before the E1 decision, and verify runs
carry that state with `pending_action = "verify"`.

## 5. Parity, failures and end conditions

- **Parity.** `counter.used` is compared with the number of `run(...)` calls that actually reached the worker at
  every step end and at campaign end. A difference, a trial record whose replicate entries disagree with the
  counter, or a charge without a run is a STOP; nothing is repaired or imputed. For a harness arm the additional
  `ComputeBudget` equality check of the reviewed core still applies.
- **Worker failures.** `RunOutcome.success = false` is the proposal's failure as §5.4/§5.5 say: charged for the runs
  used, classified by G8 `classify_worker_failure`; an infrastructure failure loses the whole attempt (rerun whole in
  a new directory, nothing of the lost attempt charged). No failed run is retried inside a campaign.
- **Budget and cap.** `UnfundableStep` before a step charges nothing and ends `no_fundable_candidate`. A charge beyond
  W is `OverBudget`, a STOP. The LLM cap is checked before each manager call.
- **`ended_on`.** Use G8 `table_ended_on` (the pinned analysis rule): `worker_runs` whenever `w = W`, even if the
  LLM cap is also reached; otherwise `llm_call_cap`; otherwise `no_fundable_candidate`. `stop`/`error` campaigns are
  excluded from the outcome table. This corrects the precedence sentence in revision 5b §3.3, as G8's unit report
  requested; the set of values is unchanged.
- **STOP classes.** The §10 list of revision 5b applies unchanged. A killed or non-clean chunk is recovered whole in
  a new directory and disclosed; it is not a STOP class.

## 6. Records and G6

The campaign directory is the revision-6b layout:
`<run_root>/<stage>/<arm>/r<rep>/<instance_id>/` with `campaign.json`, `ledger.jsonl`, `runs.jsonl`,
`snapshots/w{5,10,15,20}.json`, `snapshots/final.json`, `summary.json` and `SHA256SUMS`; the chunk-level
`chunk.json`, `summary.json` and `SHA256SUMS` are written by `campaign_chunk.py`. `campaign.json` gains one field,
`campaign_kind: "harness" | "replicate"`, and the arm name; the record names and schema do not change.

G6 reads only `snapshots/final.json` and the `w` snapshots, audits the incumbent against the start config on seeds
6700 + 10i + k, K = 10, and writes the same `r1_d3_audit_row` records. It does not know or care which route produced
a snapshot. Y_final is the primary outcome; Y(w) remains the descriptive R1-D3-OUTCOMES2 curve under the
pre-declaration's `y_raw_w` (revision 4), and is not substituted for Y_final.

## 7. What this revision does not change

- The FIXR3 and EGATE rules, constants (r = 3, α = 0.05; PaceStyleGate α = 0.1, clip = 0.05, max_pairs = 8), seeds,
  failure rules and `verify:pace` action version stay exactly as §5.4/§5.5 of the pre-declaration.
- W = 20, LLM cap 80, the 18 instances, the arm list, the seven nodes, the audit seeds, K = 10 and Y_final are
  unchanged.
- The harness arms and the reviewed snapshot core are unchanged. The verify-seed collision (revision 5b report,
  blocker 1) still blocks every verify arm (A1, A2, A3, A5, A6) until the author's row; it does **not** block the
  FIXR3/EGATE route, because FIXR3 and EGATE use no KG verify.
- The A1/A2/LADDER constants file (G2) and the signed revision 4 remain prerequisites for those arms; FIXR3 and
  EGATE need no constants file, but their unit reviews and the pre-declaration's signature are still required
  before any evidence run.
- No Y(w) analysis code, no G7/G6 code and no per-arm smoke is authorized or changed here.

## 8. Conditions for the independent review

The revision is `ACCEPTED FOR CODE` only if the reviewer confirms, with file and test evidence:

1. The replicate loop charges every actual worker call exactly once through the one `ChargedRunCounter`, never
   charges a reused incumbent run, and fails closed on any counter/record/parity difference.
2. The snapshot state is the step-start state captured before the first worker call; no manager or engine decision
   call occurs between that capture and any run of the step; `controller_state_sha256` is documented and
   deterministic; exact `w` = 5, 10, 15, 20 is written live, including inside FIXR3's 3-run step and EGATE's pair
   loop.
3. The same record layout, `campaign_id`, record name, `final.json` and G6 audit path are used as for a harness arm;
   the engine's `extra.control.replicates` is exactly the G8 contract.
4. The loop implements §5.4/§5.5 without changing a rule or constant, and `ended_on` follows `table_ended_on`.
5. No evidence, label, evaluation or sealed read is introduced; the only new field is `campaign_kind`.

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
