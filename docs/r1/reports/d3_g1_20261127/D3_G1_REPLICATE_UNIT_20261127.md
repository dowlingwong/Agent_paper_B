# D.3 G1 — replicate-arm driver for FIXR3/EGATE (unit record)

**Task.** `compute/20261127-16` (after the Ada probe preparation and the D.3 HTCondor preflight were found blocked)
and the code unit of `compute/20261127-09` item 2. **ENGINEERING_ONLY.** No campaign, audit, job, GPU, label,
evaluation, split, sweep table or sealed file was read or run for this unit.

**Base.** `origin/main` `e153df24ee3435bbe0b2fa994297b15250550c30` (the merge of the G1 snapshot core and its
`ACCEPTED` review). **Branch:** `compute-d3-g1-replicate-20261127`.

**Design authority.** `docs/r1/proposals/d3_design_20261126/D3_G1_G6_DESIGN_REV6C_REPLICATE_ARMS_20261127.md`,
sha256 `a9769ba023bd38ede646194bdd805a2376139a780d919fafc571484bccad9521`, `ACCEPTED FOR CODE` by the independent
R3 review (`docs/r1/reviews/D3_G1_G6_REV6C_REVIEW_R3_20261127.md`).

## What the unit adds

1. **`r1/c3/d3/snapshots.py` — public recorder API for a replicate campaign** (the harness path is unchanged):
   - `begin_step(trial_id, incumbent_config, start_config, state, last_kept_trial_index, llm_calls, step_index,
     pending_action)`: records the step-start projection from **config contents**, computes `config_sha256` from
     those contents, and hashes the documented ordered projection with the same canonical JSON rule.
   - `set_pending(step, j, candidate_metrics, incumbent_metrics, diffs)`: the in-step metrics/diffs written into an
     exact-`w` snapshot.
   - `on_charge(ChargedRun)`: the single per-charge hook; it requires the next sequential `w`, writes
     `w{5,10,15,20}.json` immediately, and fails closed on a skipped/block charge (`SnapshotParityStop`).
   - `write_final_from_state(...)`: a **separate post-decision** `final.json` from the last kept config contents at
     the actual `w_final`; it is never an alias of `w20.json` (the replicate w=20 snapshot is pre-decision).
   - `_files_config` now accepts text contents as well as the harness's bytes; the payload stores text unchanged.
2. **`r1/c3/d3/replicate_campaign.py` — the G1 replicate loop** (`run_replicate_campaign`):
   - one `ChargedRunCounter(W=20)` and one `ComputeBudget(max_worker_runs=20, max_llm_calls=80)` held in
     `budget_holder["value"]`; the LLM call is charged before each manager call and the worker run before each
     engine charge;
   - `run_one` maps the engine's `config_sha256` to the validated proposal/config, restores the incumbent workspace
     after a discard when the adapter supplies it, converts a worker exception to `RunOutcome(success=False)` with a
     `RunAttempt` side record, and never charges the counter itself (the engine owns the single charge);
   - parity after every step (`counter.used == budget.worker_runs`) and at the end; LLM-call parity with the number
     of proposal calls; `UnfundableStep` ends `no_fundable_candidate`; `w = 20` ends `worker_runs`; the cap ends
     `llm_call_cap`; a proposal stream that stops before the cap is a STOP, not an imputed end;
   - `projection(engine, counter)` is the documented ordered state (FIXR3: `incumbent_metrics`,
     `zero_variance_cases`; EGATE: `incumbent_runs` from `counter.lookup`); an unknown arm is refused, never hashed
     by fallback;
   - `ReplicateUnit` is the adapter seam (`propose`, `validate`, `run_trial`, `start_config`, optional
     `restore_incumbent`), so the real manager/node/worker adapter remains a separate reviewed unit.
3. **`r1/c3/d3/campaign_chunk.py` — replicate branch** (`run_chunk(..., replicate_factory=...)`):
   the same `campaigns/<instance_id>/` layout, `campaign.json` with `campaign_kind: "replicate"`, `ledger.jsonl`
   (steps), `runs.jsonl` (worker attempts), `summary.json`, `SHA256SUMS`, `chunk.json` and the chunk summary. The
   harness branch now writes `campaign_kind: "harness"`; its API is otherwise unchanged.
4. **Tests** (`r1/tests/test_d3_g1_snapshots.py`, `test_d3_g1_chunk.py`, new `test_d3_g1_replicate.py`): 31 unit
   tests for the new API and both branches, including a real `Fixr3Engine`/`EgateEngine` with a synthetic worker,
   exact `w = 5/15` snapshots inside a 3-run step, the separate final, a charged failed worker call, the EGATE
   reuse entries, the unknown-arm refusal, the declared-budget refusal and the exclusive factory selection.

## Tests run

- New and changed modules: **34 passed** (`test_d3_g1_snapshots.py` 18, `test_d3_g1_chunk.py` 9,
  `test_d3_g1_replicate.py` 7) at the branch tip, Python 3.11.13, pytest 9.2.0, `AR_HARNESS_ROOT` at the pinned
  harness checkout.
- The related delivered modules (`test_d3_fixr3.py`, `test_d3_egate.py`, `test_d3_g8_accounting.py`) pass too:
  **109 passed** together.
- Full `r1/tests` with `--continue-on-collection-errors`: see the report on `coord/compute` for the final counts
  and the identical failing-id comparison against the base.

## File hashes

| File | sha256 |
|---|---|
| `r1/c3/d3/snapshots.py` | `0347b02f3f343356976f8ddfa6d5484f797adf2726425233cf454835ada8f750` |
| `r1/c3/d3/campaign_chunk.py` | `8b84000cfd42918fa315f6d9bb9471086be6aa57dcd5693548bed1bf291b3c69` |
| `r1/c3/d3/replicate_campaign.py` | `7606cfebdc842ddb0d69b2e31166f81916422ac7d2792de8c6911c2ade1c72e7` |
| `r1/tests/test_d3_g1_snapshots.py` | `c2be8fffafdaf9d6d6b639aca1903445c46617f756c05432dc3e7c8fb1c81047` |
| `r1/tests/test_d3_g1_chunk.py` | `873c78cc4f18aad34b3f18f3950b4ca53e619d76b43fff7ba6517d6f642012b5` |
| `r1/tests/test_d3_g1_replicate.py` | `db517fe2cdf972051fc33d05789abeaa8c243125e7d1ff4b33613ca0e3e3ee2d` |

## Review round 1 corrections

The fresh tier-E review of `fb101386` (`CHANGES REQUIRED`) found: a missing `runs_charged`/entry parity check (B1);
no G8-compatible `extra.control.replicates`/events in the ledger (M1); cumulative `zero_variance_cases`
overcount (M2); `RunAttempt` lacking a classifiable failure class and card/host counts (M3); plus minors. This
revision adds: the step charge/entry parity assertions; G8 trial rows and `events.jsonl`; per-step
`zero_variance_cases`; `RunAttempt.failure_class` and card/host counts (the adapter may return a 4th detail
element or raise an exception carrying them); `table_ended_on` for the unfundable and empty-stream ends; the
`engine.arm == spec.arm` and harness-vs-replicate refusals; and the `w_final = 0` end restriction. The review
branch is `compute-d3-g1-replicate-review-20261127` @ `cb987e2e`.

## What is still outside this unit

The real D.3 adapter (node specs, the gemma4_31b manager, the seven arms and their pinned constants) is the next
G1 unit at harness `9bb416805175149eb87b71f28d77530572aa4bce` with `verify_seed_base=20000`, `verify_runs=2`,
`verify_split_policy="vary"`; then G6. The G2 constants remain a harness-arm prerequisite, not a FIXR3/EGATE one.
A fresh tier-E review is required before the coordinator merges this branch.

**Decided alone:** to keep the adapter seam explicit (`ReplicateUnit`) rather than import the real manager/node
construction into the G1 unit; to make a manager stream that stops before the cap a STOP instead of an imputed end;
to write the replicate steps to `ledger.jsonl` and the worker attempts to `runs.jsonl` (G6 reads only snapshots).
