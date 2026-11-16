# Build review — P3: E-SYN worlds and oracles (round 1)

- **Reviewer:** independent reviewer (Claude subagent, AI-assisted). I had not seen this work before the review.
- **Commit:** `ce4768f` on branch `paperc-build-20261115`. Diffs were read against `e730a91` (PH accepted) and `b6421d3` (P3 steps 1–2).
- **Date:** 16 Nov 2026
- **Label:** ENGINEERING_ONLY

## Scope read

- Runbook §0 and the P3 section of `paperC/docs/BUILD_RUNBOOK.md`.
- BUILD_LIST B3 and B17.
- Code: `paperc/esyn/{worlds,extra,sim,policies,families,dp,oracle,table}.py`.
- The schema diff `e730a91..ce4768f`.
- Tests: `tests/test_esyn_p3.py`, `tests/test_esyn_worlds.py` and the new test in `tests/test_schema.py`.
- Data and report: `esyn/oracle_table_v1.json` and `docs/reports/ESYN_ORACLE_TABLE_20261116.md`.
- Seeds: `seeds/registry_v1.json`.
- Track S originals at `fab88fc`: `r1/tracks/oracle.py`, `simulate_controls.py`, `ANALYSIS_NOTES.md` and `r1/tests/test_tracks_worlds.py`.

## What I ran

All scratch scripts are under `/tmp/p3rev/`. The committed table was not modified: I rebuilt it in a copy of the repository.

1. **Test suite** (runbook §0.4): 122 passed, 1 xfailed, 43 s.
2. **Full table rebuild** (`python -m paperc.esyn.table`, in `/tmp/p3rev/repo`): 7 min 10 s. Every world record is identical to the committed `oracle_table_v1.json` except the `seconds` field. The table reproduces from the code.
3. **Report numbers against the JSON:** every number in §3 matches. In §3/§4 the DP, static and null numbers, "about 5 million" (4.74 M) and "24 members" also match. The exceptions are listed in finding 9.
4. **Exact DP, checked independently** (`dp_check.py`):
   - My own expectimax recursion gives the same budget DP value as `dp.solve`: 0.0113916280032276, a difference of 3e-18. The static values for g ∈ {0, 0.0005, 0.001, 0.002, 0.003} also agree.
   - V\*_s = (0.000278, 0.000771, 0.002827). The static grid therefore covers all four execute-subset classes, and the planted budget gain is exact.
   - Monte Carlo, 60,000 campaigns on a fresh block (3,000,000+):
     - DP policy: mean 0.011392 (se 0.000056) against exact 0.011392;
     - static g = 0.001: 0.009308 (se 0.000054) against 0.009277;
     - paired gain: 0.002084 (se 0.000023) against exact 0.002115.
   - A tiny world (cap 6, W 3, p_rule 0.3): DP 0.0019988, MC 0.001973 ± 0.000018 (se).
5. **Loop-level equivalence with Track S** (`loop_equiv.py`):
   - The pinned `simulate_controls.Sim.run_campaign` (noiseless `y_true`) was loaded from `fab88fc` together with `analyze.py` and `schema.py`.
   - It was compared with `sim.run_campaign` on shared Paper C draws.
   - Setup: worlds N0 (W 40), P1-diffuse (16, W 10), P2+-diffuse and P2+-concentrated (0.012, W 10) and P0-diffuse (0.004, W 10); 4 static rules; 200 instances each.
   - Result: **0 mismatches in 4,000 campaigns**. For E1/E2 increment worlds, Paper C's loop reproduces Track S's campaign values exactly, including W termination and the trial-1 rule.
6. **Independent replay of the measurement model** from recorded rows and `Draws` (`mech_check.py`):
   - Quantities checked:
     - execute, verify and re-audit `delta_hat`;
     - E2 `candidate_delta_hat` (the mean of the candidate's measurements minus the incumbent record);
     - E2 comparison sd σ_m √(1/n_c + 1/n_i);
     - `incumbent_recorded` / `incumbent_obs` on every row;
     - the final candidates' recorded values and counts;
     - Y;
     - the interaction term.
   - Campaigns: eval_allocation (2 policies), shared_error and interaction (2 policies), 60 instances each.
   - Result: **0 mismatches** at 1e-12.
7. **Fast path against recorded path, and `check_campaign`** with the registry and behaviour replay (`paths.py`):
   - Policies: every static and every family member built around 3 different "best statics", in all 7 worlds, 3 instances each.
   - Result: 2,469 campaigns, 0 divergences, 0 violations.
8. **Extended static grid** on the selection block (`static_grid.py`): g ∈ 8 values (0 … 0.003) × h ∈ 20 values (−0.016 … 0.004), 2,000 campaigns per world. See finding 1.
9. **Decomposition of the eval_allocation gain** on a fresh block (n = 20,000, `ea_decomp.py`). See finding 3.
10. **Re-run of the §4.3 calibration** at W = 24/32/60 with the committed families (`w_calib.py`). See finding 9.
11. **Forward compatibility of the schema**: rows written now were checked against the P1-accepted `schema.py` (`e730a91`). See finding 12.

## Checked and found sound (no finding)

- **Slot accounting:** one E1 row per slot, with one call and one slot each; rule skips cost no run; verify, re-audit and final rows cost 0 calls. `slots_left == calls_left` throughout.
- **W termination:** the campaign ends at W when fewer than `run_cost` runs remain, checked before each slot, including rule slots (as in Track S). It ends at llm_cap after the last slot. The `for … else` end reason is correct.
- **Trial-1 rule:** slot 1 is never rule-detectable and is executed and kept with `rule_first_trial`. There is no verify on trial 1.
- **Posterior update:** after every executed proposal, with the comparison sd actually used.
- **Interaction mechanism** as documented.
- **DP:**
  - the recursion, the tie rule (">=", as in the simulator) and the indexing (slots_left, runs_left) are correct;
  - E[δ 1{m̂>0}] = V\* holds, because m̂ is the exact posterior mean under a correctly specified prior;
  - in the null, the DP is the optimum over all non-anticipating E1/E2 policies, because the state (t, w, s) is sufficient there. Its exact zero gain over static g = 0 is therefore a strong null result.
- **Paired evaluation:** the selection and evaluation blocks are disjoint, and the paired evaluation on the evaluation block is unbiased for the selected pair.
- **Sequential sizing:** the stopping rule depends only on the sample sd, a standard two-stage argument. At n ≥ 8,000 the coverage effect is negligible, and the one heavy-tailed world (information) is not certified.
- **Information world handled honestly:** positive (lower bound 0.00078 > 0), uncertified, xfail, and the reason is stated.
- **Schema:**
  - `State.candidates` is optional and old rows stay valid (tested);
  - the JSON schema export is current (tested);
  - the addition is the one the P1 docstring deferred to B17;
  - the two row rules are correct.

## Findings

### 1. MAJOR — keep_feedback's oracle gain is inflated by a truncated static grid

**Location:** `families.py` `H_GRID = (-0.003, …, 0.001)`; `oracle_table_v1.json` keep_feedback; report §3 and §4.5.

**What I found:**
- keep_feedback's best static, `static:0.0005,-0.003`, sits on the lower edge of `H_GRID`.
- The selected member, `dynamic:0.0005,-0.002,0,0,0.008,…`, has an effective keep threshold of −0.002 − 0.008·runs_left/W ∈ [−0.010, −0.002]. Most of that range lies outside the static grid.
- With h extended:
  - on the selection block, `static:0.0005,-0.006` beats the committed best static by +0.00146 (se 0.000165);
  - on a fresh block (n = 20,000), member − static(h = −0.006) is **+0.00128 ± 0.00006**, and member − static(h = −0.008) is +0.00146 ± 0.00006;
  - the committed comparison, member − grid static, is +0.00236 ± 0.00010.

**Why it matters:**
- The table overstates the keep-feedback channel gain by about 80 %.
- About 46 % of the reported gain is a level shift of the keep threshold that a static rule captures. Track S's own wording rule calls this "a threshold-level shift" once the matched static recovers half.
- The §4.5 claim "the member's budget-dependent keep threshold adds +0.0024" over-reaches.
- Track S's design had an explicit edge extension of the static grid ("+60 on the edge extension"); P3 dropped it.
- The other worlds are not affected: on the extended grid their best static stays the committed one, or is not significantly better (information: +0.00013, se 0.00038).
- The member grid is also at its edge: b_keep = 0.008 is the largest value.

**Fix:**
- Add an edge rule: extend `G_GRID` / `H_GRID` whenever the selected static is on a non-natural edge (g = 0 counts as natural, because V\* > 0), and test it, i.e. assert that the selected static is interior or at a declared natural bound in every world.
- Do the same for member grids.
- Rebuild the table and rewrite §4.5.

### 2. MAJOR — the "planted gain" of non-DP worlds is the winner's-cursed selection gain, so "certified at 5 %" does not mean what it says

**Location:** `oracle.py` lines 57–65 (`planted_source = "selection"`); report §3 ("Planted gain") and §4.1.

**What I found:**
- For 5 of the 6 channel worlds, the precision target is 5 % of the best member's gain on the same selection block on which that member was chosen from 12–96 candidates. That gain is not planted, and it is biased upward, which loosens the target.
- keep_feedback: selection gain 0.00277, evaluation gain 0.00237 (3 half-widths lower). The half-width 0.000130 is **5.5 % of the evaluated gain**, so 5 % precision is not reached against the measured gain. Against the gain over a correctly searched static (finding 1) it is about 10 %.
- information: the "planted" gain 0.00107 has a selection-block se of 0.0013, so the target is defined by noise.
- Track S's `certify` took `delta_Y` as a **declared** input (0.0033 = 0.5 σ_node). It also checked the half-width of **every** member. P3 checks one member against a data-derived reference. The runbook's "every 95 % half-width ≤ 5 % of the planted gain" is not met as written, and the report does not flag this as a deviation.

**Fix (either option):**
- (a) Declare a reference δ_Y per world before evaluation, e.g. Track S's 0.5 σ_cmp or the DP gain where one exists, and certify against it; or
- (b) define the target on the evaluation block, iterating until hw ≤ tol · (gain_eval − hw).

Then:
- rename "planted" to "reference" wherever it is not planted;
- add an `hw / gain_eval` column to the report;
- state the one-member deviation from Track S;
- re-run the table.

### 3. MAJOR — B17: final selection has no demonstrated value, and per-action values are not reported

**Location:** `families.py` (eval_allocation members); report §2 and §3; BUILD_LIST B17 status "built (verify, re-audit, final)"; runbook step 3 ("verify, re-audit and final selection have a known value").

**What I found:**
- Only the bundle's oracle gain is known. The certified member, `evalloc:0,-0.001,1,2,2,incumbent`, does not use final selection.
- Decomposition on a fresh block (n = 20,000, the same g, h as the best static):

  | Policy | Gain over the static rule (± 95 % hw) |
  |---|---|
  | verify only | +0.00292 ± 0.00010 |
  | re-audit only | +0.00153 ± 0.00009 |
  | bundle, final = incumbent | +0.00356 ± 0.00010 |
  | bundle, final = best | +0.00346 ± 0.00011 |

- `final = best` against `final = incumbent`: **−0.000097 ± 0.000030** (31 % of campaigns differ); with re-audit to 3: −0.000129 ± 0.000040. Over the 48 selection-block pairs the mean is −0.000035.
- Final selection is therefore slightly harmful in the world that is meant to give it a known value. At W = 60 (my calibration re-run) the selection winner does use `final = best`, so its value depends on W, and the report does not show this.
- Also undeclared in the report: re-audit is offered only immediately after a keep. The schema docstring says "anywhere between decisions". Re-audit timing is therefore not a decision, and a post-keep re-audit is effectively a post-keep verify of the new incumbent.

**Fix:**
- Report per-action values (verify-only, re-audit-only, final-only on top of a fixed measurement policy) with CIs in the table.
- Either add a world or variant in which final selection has a declared positive value (e.g. W = 60, or final selection with its own measurements, which matches B17's "among top candidates"), or state that final selection's value is ≤ 0 under this model and mark that part of B17 as not demonstrated.
- Declare the re-audit timing restriction.

### 4. MAJOR — the interaction oracle reads the true M through `oracle_int`; this is undisclosed in the report and recorded in every row

**Location:** `sim.py` lines 308–315 and the docstring; `policies.InteractionAware`; report §2 ("Belief model: A2-U's keyed conjugate model") and §3.

**What I found:**
- Using world knowledge is acceptable for an oracle member. The interaction gain is then the value of an M-aware keep rule.
- However:
  - (i) the report never says that the interaction oracle knows M. §2 describes the belief model as A2-U only, and `oracle_int` appears only in code docstrings;
  - (ii) the M-derived "forecast" is written into `state.forecasts` of **every** E2 row of the interaction world, whatever the policy (checked: 15 of 15 E2 rows of a `Static` campaign carry it);
  - (iii) it is named and typed as a forecast.
- P4's rule (plan §7.0) is that on E-SYN the arms share "the world's own forecaster", and P7/P8 train learners on E-SYN behaviour logs. A privileged, M-derived field sitting among the forecasts is therefore a concrete leakage path into later baselines, learners and OPE validation.

**Fix:**
- State in the report (§2, and a footnote in §3) that the interaction oracle uses privileged knowledge of M, and what the gain then means.
- Write the field only when the acting policy is an oracle member, or move it to a field marked privileged that learner featurisers must exclude.
- Add a test that no non-oracle record carries privileged fields.

### 5. MINOR — the certified null row is vacuous and the null tolerance is loose

**Location:** `oracle.py` (floor = σ_cmp); `test_null_gain_is_zero_within_tolerance`; report §3 (strict_null row "certified: yes", +0.00000 ± 0.00000 at n = 1000).

**What I found:**
- The evaluated member is decision-identical to the static rule, so the certified comparison is the static rule against itself.
- The meaningful check (the 15 distinct members) runs only on the selection block, with a slack of tolerance + 2 se = 0.00052, roughly half of the smallest channel gain (interaction, 0.00116).
- The floor tolerance of 5 % σ_cmp = 0.00033 is twice Track S's null tolerance (5 % of δ_Y = 0.000165).
- The exact DP zero (sound, see above) is the real null evidence, and the report is transparent about this.

**Fix:**
- Certify the best **distinct** member on the evaluation block.
- Tie the null tolerance to the declared δ_Y (finding 2) or to the smallest channel gain.
- Show the null row as "exact (DP) + distinct-member check", not "certified".

### 6. MINOR — test gaps and weak tests

**Location:** `tests/test_esyn_p3.py`; `tests/test_esyn_worlds.py`.

- **(a) A trivially true test.** In `test_mechanisms`, the interaction part asserts only `w.interaction[0][1] > 0`, which is a property of the constant. The shared-error part checks only that `incumbent_obs` reaches 3. No test checks the config measurement model, the verify/re-audit mean updates or the interaction increment directly; my replay (run 6) did, with no mismatch.
- **(b) Runbook step 2 is not met as written.** It asks to compare *campaign values and decisions* with Track S, as Track S's `test_tracks_worlds.py` does. The port test compares components only. My loop-level comparison (run 5) shows exact equality, so the step can be met cheaply.
- **(c) The table tests read the committed JSON.** A code change in `sim`, `policies` or `families` leaves them green as long as the world parameters are unchanged. I verified the rebuild at `ce4768f`.
- **(d) The second assertion of `test_dp_and_oracle_agree_on_budget`** bounds a single mean by "4 × the paired-difference half-width + tolerance". That is the wrong yardstick: the se of the DP mean at n = 11,156 is about 0.00013, not about 0.00005. Report §3 uses the same yardstick.
- **(e) The information xfail is non-strict.** `pytest.xfail(...)` is imperative, so the certification test can never XPASS.
- **(f) The DP policy (`Threshold`) is not in `POLICIES`.** Its records and replay are therefore untested; they pass in my run 7.

**Fix:**
- Commit a replay test like `mech_check.py` and a loop-level equivalence test like `loop_equiv.py`. The latter loads `simulate_controls.py`, `analyze.py` and `schema.py` from the pin; this works with numpy and scipy only.
- Store a fingerprint in the table (e.g. a short certify at n_select = n_pilot = 50, or a hash of the esyn sources) and test it.
- Use the se of the mean in (d).
- Use `@pytest.mark.xfail(strict=True)` in (e).
- Add `Threshold` to the record tests.

### 7. MINOR — seed bookkeeping

**Location:** `sim.py` (RNG key, `Draws`, `INSTANCE_BASE`, `AUDIT_BASE`, `SELECT_BASE`, `EVAL_BASE`); `seeds/registry_v1.json`.

**What I found:**
- **Oracle blocks:** the oracle instance indices 1,000,000 + i and 2,000,000 + i lie numerically inside the registered Paper B blocks `tracks_oracle_select` [1e6, 2e6) and `tracks_oracle_eval` [2e6, 3e6). The separation rests only on the Paper C root key 60001. That is a valid argument (different SeedSequence entropy), but it is not stated where the registry is defined. The registry's own note for `paperc_audits` shows that this range was meant to be avoided.
- **Unclaimed key:** key 60001 is not claimed anywhere in the registry. P4/P6 draw "fork selection, ε draws" from the same `paperc_rng_keys` block.
- **Labels, not seeds:** the recorded `instance_seed` (50000 + i) and `audit_seed_block` / `audit_seeds` are labels.
  - The RNG uses i.
  - The audit noise comes from the campaign generator, not from the recorded audit seeds.
  - A reader cannot regenerate a campaign from its record without knowing the mapping.
- **32-bit seed:** `Stream` receives a 32-bit integer cut from the SeedSequence. About 5 colliding stream pairs are expected among information's 200,000 evaluation campaigns. This is negligible statistically, but unnecessary.

**Fix:**
- Register an E-SYN entry for key 60001 (and the derived index ranges, with the rationale) in the Paper C registry.
- Document the mapping from recorded seed to RNG input, and test that `run_campaign(w, pol, instance_seed - INSTANCE_BASE, record=True)` reproduces the recorded rows.
- Either derive the audit noise from the recorded audit seeds or say that they are nominal.
- Optionally pass a SeedSequence child to `Stream`.

### 8. MINOR — oracle gains are family-best lower bounds, which the report does not say

**Location:** report §3 and §4; `families.py`.

**What I found:**
- **Best members on grid edges:** interaction β = 0.25 (the smallest value), keep_feedback b_keep = 0.008 (the largest), information tau_cut = 0.01 (the smallest).
- **Members that tie:** in information, all b_novel values tie (the bonus is effectively binary).
- **Comparison with Track S:** Track S's 9-threshold schedule reached about 3.8 δ_Y ≈ 0.0126 in P1-diffuse (16) and about 1.9 δ_Y ≈ 0.0064 in P2+-diffuse (0.012) at W 10 (ANALYSIS_NOTES §5.1). P3's members reach 0.00105 and, after finding 1, about 0.0013.

**Why it matters:** "Oracle gain" here is the best member of a small family. Except for the budget world, it is a lower bound on the attainable gain, possibly a loose one. This matters for P4's "gap to the oracle" column.

**Fix:**
- Say so in §3 and §4.
- Extend the member grids to interior optima.
- Note the Track S schedule numbers.
- Keep the information-schedule port as the open item it already is.

### 9. MINOR — factual slips and unreproducible numbers in the report and status

- **Resizing sentence.** §5 says "Budget needed one round, after the pilot-based n fell just short". In `certify`, `resizing_rounds = 1` is the normal pilot-to-n step, and every certified world except the null has it. Only interaction (2 rounds, n = 27,942) needed a re-size after the pilot-based n fell short.
- **World count.** `BUILD_STATUS.md` says "6 of 7 channel worlds certified". There are 6 channel worlds; 5 are certified, plus the null.
- **S0.6 naming.** The world notes in `extra.py` call the information/keep_feedback strengths Track S's "S0.6 calibration / S0.6 grid", and report §2 says "as Track S's S0.6 grid". Report §5 says these are "analysis-grid strengths, not the S0.6 values". They are the §5.1 analysis-grid strengths (P1 16, P2+ 0.012); the wording should be made consistent.
- **Calibration numbers.** The §4.3 calibration numbers are not reproducible from the committed code:

  | World | W | Report | My re-run (n = 1,000 / 1,500) |
  |---|---|---|---|
  | shared_error | 24 | −0.0012 | −0.0007 / −0.0008 |
  | eval_allocation | 32 | +0.0012 | +0.0018 / +0.0016 |
  | eval_allocation | 60 | +0.0053 | +0.0054 / +0.0051 |
  | eval_allocation | 24 | no member beats static | −0.0003 / −0.0004 |

  The signs agree. The report also does not say which block the calibration used. It must not have been the evaluation block.

**Fix:**
- Correct these sentences.
- Commit the calibration script (or label the numbers as coming from an earlier family) and state the block it used.

### 10. MINOR — schema amendment: forward compatibility and candidate consistency

**Location:** `schema.py` (`Candidate`, `State.candidates`, row rules).

**What I found:**
- **Forward compatibility.** `to_dict` (asdict) writes `"candidates": []` on every row. The P1-accepted validator rejects such rows ("row.state.candidates: unknown field"), and so does the old JSON schema (`additionalProperties: false`). Both carry the same `spt_transition/v1` string. Backward compatibility holds; forward compatibility does not, and the amendment is not dated in the schema.
- **Candidate consistency.** There is no check that candidate hashes are unique, or that candidates are configurations kept earlier in the trajectory with matching recorded values and counts.

**Fix:**
- Record the amendment (date, phase) in the schema docstring and the JSON-schema description, or bump to a minor version.
- Add uniqueness and "candidate was an incumbent earlier" checks to `check_campaign`.

### 11. MINOR — the shared_error gain is the value of free re-audits

**Location:** `extra.py` shared_error note (declared there); report §2, §4.3 and §4.4.

**What I found:**
- With W = 60, never binding, a re-audit costs nothing, so a policy that re-audits gains almost by construction. It is more information at zero cost.
- No member exploits the shared incumbent error within E1/E2 alone, e.g. a keep threshold that depends on `incumbent_obs` or on comparisons since the last keep.
- The world therefore certifies "free re-audit pays", not that the shared-error channel can be exploited by keep decisions.

**Fix:**
- Say this in §2 and §4.
- Optionally add an E2-only member, such as a keep threshold as a function of `incumbent_obs`.

### 12. MINOR — code nits

- **Negative key indices.** `sim._key_index` returns key − (llm_cap + 2) for every key. For P1 probe and follow-up keys (key = t), that index is negative. With an interaction matrix on a P1-based world it would silently index M from the end. `ESynWorld.__post_init__` does not forbid this combination. Fix: return None for non-recurring keys, or reject `interaction` on `kind == "P1"`.
- **Inverted naming.** `dp.applicable` returns a list of reasons, so `table.py`'s `if not dp.applicable(w):` and `test_dp_not_applicable_elsewhere` read backwards. Fix: rename it, e.g. `dp.inapplicable_reasons`.

## Summary

The simulator, the budget DP and the oracle machinery are correct where I could check them independently, and the table reproduces exactly from the code:

- the DP agrees with an independent recursion and with Monte Carlo;
- Paper C's loop reproduces Track S's campaign values exactly;
- the measurement model replays exactly;
- the fast and recorded paths agree, and the records pass `check_campaign`.

Four issues block acceptance:

- one table entry is materially inflated by a truncated static grid (keep_feedback);
- the certification target for non-DP worlds rests on a winner's-cursed selection gain, so "certified at 5 %" fails for keep_feedback against its own evaluated gain;
- B17's final selection has no demonstrated value (it is slightly harmful in the B17 world), and per-action values are missing;
- the interaction oracle's privileged knowledge of M is undisclosed and is recorded in every row.

The fixes are cheap: re-run the table after correcting the grids and the target, report the per-action decomposition, and isolate and disclose the privileged field.

Verdict: NOT ACCEPTED
