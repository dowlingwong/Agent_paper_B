# Build P1 review: `spt_transition/v1` schema and mechanical checks (15 Nov 2026)

**Independent reviewer (fresh agent; did not write the code).** ENGINEERING_ONLY. Reviewed commit `972cf11` on `paperc-build-20261115`. During the review the branch moved to `bbb40d1` (P2). `schema.py`, `schema_export.py` and `schemas/spt_transition_v1.json` are identical in both commits, so every finding applies to both.

## What I checked

- **Documents.**
  - `paperC/docs/BUILD_RUNBOOK.md` §0 and P1;
  - plan §3.1, §3.2, §3.3, §4.1, §4.2, §6.1, §11.1;
  - `PLAN_ADDENDUM_20261115.md`;
  - `proposals/PAPER_C_REFRAME_AFTER_TRACKS_STOP4_20261115.md`;
  - `BUILD_LIST.md` B1.
- **Code.**
  - `paperC/src/paperc/schema.py`, `schema_export.py`, `schemas/spt_transition_v1.json`, `tests/test_schema.py`;
  - Track S `r1/tracks/schema.py` and `selection_draw` / seed blocks in `r1/tracks/collect.py` at `origin/trackS-ops-20261030` = `fab88fc`.
- **Tests** (runbook §0.4 command):
  - 32 passed at `972cf11` (run from a `git archive` copy under `/tmp`);
  - 38 passed at `bbb40d1`.
  - The committed JSON file equals `json.dumps(to_json_schema(), indent=2, sort_keys=True)` byte for byte.
- **Adversarial probes:** about 60 cases in scratch scripts under `/tmp/p1review/` (not in the repo), run against both commits with identical results.
  - Corruptions the checks should catch.
  - False positives on legitimate data, all of which passed correctly:
    - a fork continuation starting at step 3;
    - a truncated root prefix;
    - rule-forced skips;
    - a final `select` row;
    - a divergent execute followed by a rule-forced discard;
    - ε rows with `eps_seed`;
    - two campaigns interleaved in reverse order;
    - a forced intervention on the root;
    - a terminated fork continuation.
  - Type holes. bool-as-int, bool-as-float, NaN and inf are rejected correctly by `validate`.
- **Diff scope.** Only `paperC/` is touched. `.venv` is not tracked. The `p_select` formula matches Track S `selection_draw`.

**Field coverage (plan §4.1).** Every field in the table is present in some form:
- the ε-randomisation flag is represented by `eps > 0`;
- the GGUF sha sits in `EnvContext`, not `Provenance`.

The gaps are in the rules and checks, not in the field list. Finding 13 lists decision-time state fields from §3.2 and the reframe that are missing.

## Findings

### MAJOR

**1. A divergent candidate can be kept.**
- *Where:* `schema.py:360-365`, `:539-548`.
- *What is wrong:* the rule "a divergent run is not kept" tests `outcome.kept` on the row that carries `divergent`. But divergence is logged on the E1 `execute` row, where `kept` must be null (`:365`). The keep happens on the following E2 row, and `check_campaign` has no rule linking the two rows.
- *Probe:* row 0 `divergent=True, delta_hat=None`, row 1 E2 `keep, kept=True` → `check_campaign` returns `[]`.
- *Why it matters:* plan §3.1 says the keep rule treats divergence as "not improved". The docstring (`:44`) claims the rule is enforced.
- *Fix:*
  - In `check_campaign`: if a row is divergent, the next E2 or verify row with the same `proposal_hash` must be `discard`, `rule_forced=True`, with a declared rule such as `rule_divergent`.
  - Preferably also add a decision-time `State.candidate_divergent` and a matching row rule.
  - Add a test.

**2. A future value is allowed in an E1 state.**
- *Where:* `schema.py:153`, `:175`, `:75-79`, `:332-336`.
- *What is wrong:* `Forecast.m_hat` is "the posterior mean of the increment given the result". It can be non-null on an E1 row, where the result does not exist yet. A row like that passes `validate` and `check_campaign`.
- *Why the existing check misses it:* `no_future` looks only at field names, and the closed `State` already rejects unknown names. So no check ever looks at values.
- *Fix:*
  - Add a row rule: on E1 rows every `forecasts[*].m_hat` is null.
  - Use this corruption as the "only `no_future` catches it" test (see 8).

**3. Budget conservation is incomplete.**
- *Where:* `schema.py:531-545`, `:528`.
- *What is checked:* used + left = cap on each row, and the step-to-step chain.
- *What is not checked:*
  - (a) The last row's consumption. `runs_consumed=5` with `runs_left=0` passes, and so does `calls_consumed=9` with `calls_left=3`.
  - (b) That the root starts at zero. A root whose row 0 has `runs_used=1`, with a consistent chain after it, passes. Then Σ consumed ≠ W − runs_left, which is the plan §4.2 statement.
  - (c) That a fork continuation starts from the root's counters. A fork whose `runs_used` is reset to 0 at step 3 passes.
- *Fix:*
  - On every row, require `runs_consumed <= runs_left` and `calls_consumed <= calls_left`.
  - Root step 0 has `runs_used == calls_used == 0`.
  - When the parent trajectory is in the batch, the fork's first row has the parent's counters and incumbent at the same `step_index`.
  - One test each.

**4. The next-state check never looks at the keep decision.**
- *Where:* `schema.py:546-548`.
- *What is wrong:* the check compares `incumbent_hash` at t+1 with the logger's own `next_incumbent_hash` at t. Two copies of the same logged value are compared, and neither is related to `kept`.
- *Probes that pass:*
  - an E1 `execute` that changes the incumbent;
  - a `keep` that leaves it unchanged;
  - a last-row `discard` with a different `next_incumbent_hash`, which is never compared because no row follows it.
- *Why it matters:* "an incumbent that changes without a keep" is exactly the logger bug this check exists to catch.
- *Fix:*
  - `next_incumbent_hash == incumbent_hash` unless the row is (E2 and kept), or `final` with `next_incumbent_hash == action.selected`.
  - A kept row changes the hash; flag no-ops.
  - Apply the check across the root→fork boundary too.

**5. Termination vs truncation is self-declared and unconstrained.**
- *Where:* `schema.py:199-201`, `:550-561`.
- *What is wrong:* `reason` is free text. These all pass:
  - `terminated`/`infrastructure`;
  - `terminated`/`whatever`;
  - `truncated`/`divergence`;
  - `terminated`/`W` after 1 of 4 runs, with a `Terminal` attached.
- *Why it matters:*
  - A truncated campaign labelled "terminated" enters return targets as if complete, which plan §3.1 forbids.
  - Divergence as a truncation reason contradicts §3.1.
- *Fix:*
  - Make `reason` a Literal per kind:
    - `terminated` ∈ {`W`, `llm_cap`, `policy_stop`};
    - `truncated` ∈ {`infrastructure`, `protocol_stop`, `parse`, `host`}.
  - Check the label against the ledger:
    - `W` ⇒ `runs_used + runs_consumed == W` on the last row;
    - `llm_cap` ⇒ `calls_used + calls_consumed == llm_cap`;
    - `policy_stop` is rejected until a stop action exists in `EPOCH_ACTIONS`.
  - Add tests.

**6. Forced rows cannot carry a truthful propensity.**
- *Where:* `schema.py:118`, `:373-374`; fixture `test_schema.py:70-77`.
- *What is wrong:* `action_prob` must lie in (0, 1] and be non-null on every row. On a fork arm that goes against a deterministic behaviour component, the probability of the logged action under the behaviour policy is 0, or undefined by plan §6.1 ("a forced action has no defined likelihood ratio"). `validate` rejects both 0 and null. So the fixture logs 1.0 on a forced skip.
- *Why it matters:* any P6/P7 estimator that reads `action_prob` would treat forced arms as on-policy with propensity 1.
- *Fix:*
  - Make `action_prob` Optional and require null when `action.forced`.
  - Keep 1.0 on rule-forced rows (a deterministic rule).
  - Log what the behaviour component itself would have done in separate fields (`behaviour_action`, `behaviour_prob`; Track S `myopic_action`).
  - Add tests.

### MINOR

**7. The A/A replay bullet of plan §4.2 is neither implemented nor listed as deferred.**
- *Where:* docstring `schema.py:27`, which says "one per plan §4.2 bullet".
- The runbook and BUILD_LIST B1 also omit A/A, so this is not MAJOR.
- *Fix:* either list it as deferred to P3/B11 with the reason (it needs A/A fork leaves), or add a data-level check. Under that check, a continuation whose forced action equals the root's action reproduces the root's later rows. Add a marker field (Track S `aa` / `aa_reproduced`).

**8. The `no_future` test does not isolate its check.**
- *Where:* `test_schema.py:199-205`.
- Every case also fires `contiguous` and `next_state`, because the bad row is dropped.
- With the denylist removed, the same corruption is still caught, as `schema`.
- *Fix:*
  - Strip the forbidden names and keep the row in the campaign checks, so that only `no_future` fires.
  - Add the value-level case from 2.

**9. Outcome / action / epoch consistency is not checked.**
- *Where:* `schema.py:186-195`, `:359-368`.
- *Cases that pass:*
  - a skip with `delta_hat`;
  - a divergent skip;
  - `immediate_measured` on a skip;
  - an executed row with neither `delta_hat` nor `divergent`;
  - an `execute` that consumes 0 runs;
  - an E2 row not preceded by an executed row for the same proposal;
  - a `final` row in the middle of a trajectory.
- *Fix:*
  - `delta_hat` / `divergent` appear only on rows with `runs_consumed > 0` and action ∈ {`execute`, `verify`, `reaudit`}, and exactly one of the two is set.
  - Non-executing actions consume 0 runs.
  - An E2 row follows an execute of the same `proposal_hash`.
  - `final` appears at most once, as the last row.
  - Declare where `immediate_measured` lives. Track S uses 0.0 when not kept.

**10. Values that should be constant per trajectory are not checked.**
- `env` (W, cap, proposer), `node`, `instance_id`, seeds and the `ForkDesign` fields can change between rows of one trajectory or fork.
- Fork rows accept `replicate=0` and `fork_id=None`.
- *Fix:* check constancy per trajectory and per `fork_id`; require `replicate >= 1` and a non-null `fork_id` that matches `branch_path`.

**11. The history counters are not checked, and the valid fixture is inconsistent.**
- `keeps_so_far`, `skips_so_far` and `slots_left` are never checked.
- In `test_schema.py:31-32`, `keeps_so_far` stays 0 after the keep at step 1, and `skips_so_far` stays 0 after the skip at step 2.
- *Fix:* check the increments along the chain, fix the fixture, and state whether rule skips count.

**12. The `eligible` / `rule_forced` flags are underdetermined.**
- *Where:* `schema.py:162-163`, `:369-372`.
- `(eligible=False, rule_forced=False)` with rule `policy` passes.
- `duplicate=True` with `rule_forced=False` and an `execute` action also passes.
- *Fix:* forbid or define `(False, False)`; require `rule_forced` ⇔ `action.rule` starting with `rule_`; tie duplicate/no-op to `rule_forced` at E1, or document why not.

**13. State lacks decision-time information that plan §3.2 and the reframe need.**
- *Missing:*
  - the candidate's observed result(s) and divergence at E2 or verify. These exist only in the previous row's `Outcome`, and the names `delta_hat` / `divergent` are on the denylist;
  - the incumbent's recorded value and its number of observations, which re-audit and the winner's curse need;
  - Track S's `key_seen`.
- The `verify` / `reaudit` / `final` epochs exist, but there are no fields for repeated measurements or for the candidate set.
- The docstring (`:23`) says nothing is deferred.
- *Fix:* add the fields (for example `candidate_obs`, `candidate_divergent`, `incumbent_value`, `incumbent_n_obs`, `key_seen`), or list them as deferred to B17/P3 with the reason.

**14. The propensity-replay interface is weak.**
- *Where:* `schema.py:487`, `:575-580`.
- `behaviour` receives the whole `Transition`, including the logged action, outcome and terminal. So the replay is not "on the logged state", and a callable can simply echo the logged answer; the test does so on all but one row (`test_schema.py:164-167`).
- A NaN probability passes. A `None` probability raises `TypeError`.
- *Fix:* pass a decision-time view that matches P4's `act(state, rng)`: identity, env, seeds without audit, policy without `action_prob`, and state. Reject non-finite probabilities.

**15. The seed check covers only (node, instance_seed).**
- *Where:* `schema.py:483`, `:581-585`.
- The P2 registry now contains Paper B audit blocks. But `audit_seed_block`, `terminal.audit_seeds`, `worker_seed` and `eps_seed` are never checked against it.
- *Fix:* check every seed field against the registry.

**16. The JSON schema is looser than `validate`, and its `$id` is not absolute.**
- *Where:* `schema.py:425-469`, `:467`.
- *Gaps:*
  - `schema` is not a `const`;
  - `integer` accepts 1.0 under draft 2020-12, while `validate` rejects it;
  - NaN is accepted;
  - no ranges on `action_prob`, `eps` or `p_select`;
  - `audit_seed_block` is not limited to 2 items;
  - counters have no `minimum: 0`;
  - defaults (`divergent`, `eps`, `branch_path`) are not emitted;
  - `$id: "spt_transition/v1"` is a relative reference.
- *Fix:*
  - Add `const`, `minimum`/`maximum`/`exclusiveMinimum`, `minItems`/`maxItems` and `default`.
  - Use an absolute `$id`, for example `urn:paperc:spt_transition:v1`.
  - Add a `description` saying that row and campaign rules live in `validate` / `check_campaign`.

**17. Robustness.**
- `validate(None)`, `check_campaign([None])` and an `identity` that is a string raise `TypeError` / `AttributeError` (`:510`, `:513`) instead of returning errors.
- Negative `step_index` and other negative counts pass `validate`.
- Schema violations lose their trajectory key (`("?",)`) and set off cascading `contiguous` / `next_state` violations.
- *Fix:* return errors for input that is not a mapping, enforce `>= 0`, and keep the trajectory key whenever `identity` parses.

**18. Track S names are not reused where the meaning is the same (runbook P1 step 1).**
- *Renamed:*
  - `uniform`/`oversample` → `in_uniform`/`in_oversample` (`:131-132`);
  - `prior_skips` → `skips_so_far` (`:171`);
  - `manager_gguf_sha256` → `proposer_gguf_sha256` (`:103`).
- *Moved:* `Forecast.g` now lives in `env.constants`.
- *Missing:* no field for the belief model's version or sha (Track S `controller_version`, `prior_sha256`).
- *Fix:* rename, or put the mapping in the docstring.

**19. Commit message prefix.** The commit message starts with `paperC P1:` rather than `paperC:` (runbook §0.2). Cosmetic.

All six MAJOR findings are small, local changes to `_row_rules` / `check_campaign` / `PolicyInfo`, each with one new test.

Verdict: NOT ACCEPTED
