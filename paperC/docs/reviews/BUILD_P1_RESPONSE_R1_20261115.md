# Build P1 — executor response to review round 1 (15 Nov 2026)

ENGINEERING_ONLY. Executor: chat-session Claude. Review: `BUILD_P1_REVIEW_20261115.md` (round 1, NOT ACCEPTED). Tests after the fixes: 59 passed (runbook §0.4 command, P2 tests included).

| # | Finding | Change | Test(s) |
|---|---|---|---|
| 1 | divergent candidate can be kept | `epoch_sequence`: the E2 after a divergent execute must be `discard`; `State.candidate_divergent`; rule `rule_divergent` | `test_m1_divergent_candidate_cannot_be_kept` (also a valid rule-forced discard) |
| 2 | `m_hat` at E1 | `no_future` value rules: E1 forecasts carry no `m_hat`; E1 states carry no candidate result | `test_m2_*` (2) |
| 3 | budget gaps | consumed ≤ left per row; root starts at 0 runs and 0 calls; a fork's first row has its parent's counters at the same step | `test_m3_*` (3) |
| 4 | next state ignores keep | per action: keep → `candidate_hash`, final → `selected`, all else unchanged; fork's first row vs parent incumbent | `test_m4_*` (4) |
| 5 | free-text end reason | `EndReason` Literal; reason must fit the kind; `policy_stop` rejected (no stop action); W / llm_cap must agree with the ledger | `test_m5_*` (3) |
| 6 | forced propensity | `action_prob` null on forced rows; `behaviour_action` / `behaviour_prob` log what the behaviour policy would have done (Track S `myopic_action`) | `test_m6_*` |
| 7 | A/A replay | listed as deferred to B11 in the docstring, with the reason | — |
| 8 | `no_future` isolation | rows with only row-rule or forbidden-name violations stay in the campaign checks, so the name corruption fires only `no_future` | `test_no_future_names`, `test_m2_*` |
| 9 | outcome / epoch consistency | `outcome` rules (consumption, exactly one of `delta_hat` / `divergent` on executing actions, none otherwise, `immediate_measured` only on an E2 keep, E1 consumes its call); `epoch_sequence` (E2 / verify follow their execute and carry its result, root starts at E1, `final` only last, reaudit not between execute and E2) | `test_outcome_rules`, `test_epoch_sequence_rules`, `test_final_select_row_is_valid` |
| 10 | per-trajectory constants | `constant` check (identity fields, env, seeds, fork design); `fork_id` required and matching `branch_path[0]`; `replicate >= 1` | `test_constant_within_trajectory` |
| 11 | history counters | `counters` check (`keeps_so_far`, `prior_skips` counting rule skips, `slots_left` per E1 row); fixture corrected | `test_counters` |
| 12 | flags | `eligible == not rule_forced`; `rule_*` exactly on rule-forced rows; duplicate / no-op ⇒ rule-forced at E1; rule-forced and forced are exclusive | `test_flags` |
| 13 | decision-time fields | `candidate_hash`, `candidate_delta_hat`, `candidate_divergent`, `candidate_obs`, `incumbent_recorded`, `incumbent_obs`, `key_seen`; `Forecast.g`; `Provenance.controller_version` / `prior_sha256`; the candidate list of a final selection deferred to B17 (docstring) | valid fixtures |
| 14 | propensity interface | replay on `DecisionView` (no action, outcome, terminal, audits); non-finite / missing probabilities reported | `test_propensity_*` |
| 15 | seed fields | instance, worker, epsilon, audit block and terminal audit seeds all checked | `test_seed_fields_against_registry` (4) |
| 16 | JSON schema | `schema` const; integers `minimum: 0`; probability and rate ranges; `audit_seed_block` exactly 2; defaults; `$id = urn:paperc:spt_transition:v1`; description says `validate` is authoritative (integer vs 1.0, NaN) | `test_json_schema_validates` |
| 17 | robustness | non-object rows give errors; all ints ≥ 0; trajectory key kept when `identity` parses | `test_non_object_rows_do_not_raise`, `test_negative_and_wrong_types` |
| 18 | Track S names | `uniform` / `oversample`, `prior_skips`, `manager_gguf_sha256`, `Forecast.g`, `controller_version` / `prior_sha256` | — |
| 19 | commit prefix | later commits use `paperC:` | — |
