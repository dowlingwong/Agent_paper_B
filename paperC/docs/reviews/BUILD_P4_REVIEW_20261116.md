# Build review — P4: policy interface, non-RL ladder and B18 comparators on E-SYN (round 1)

- **Reviewer:** independent reviewer (Claude subagent, AI-assisted). I had not seen this work before the review.
- **Commit:** `2e18837` on branch `paperc-build-20261115`. Diffs read against `241b312` (P3 accepted).
- **Date:** 16 Nov 2026
- **Label:** ENGINEERING_ONLY

## Scope read

- Runbook P4 (`paperC/docs/BUILD_RUNBOOK.md`); plan §7.0–§7.2 (`PAPER_C_SEQUENTIAL_POLICY_PLAN_20261104.md`); reframe §3/§5 and BUILD_LIST B4, B18.
- Code: `paperc/policies.py`, `paperc/runner.py`, and the diff `241b312..2e18837` of `esyn/sim.py` (stochastic policies, `decision_uniform`, `trace`), `esyn/dp.py` (`solve_law`), `esyn/table.py` (`policy_from_name`), `seeds.py`, `seeds/registry_v1.json`. Also the context in `esyn/policies.py`, `esyn/extra.py` and `schema.check_campaign`.
- Tests: `tests/test_ladder_p4.py`.
- Data and report: `esyn/ladder_table_v1.json`, `docs/reports/LADDER_TABLE_20261116.md`; context `ESYN_ORACLE_TABLE_20261116.md`, `BUILD_STATUS.md`.
- Track S original: `r1/tracks/a2u.py` at `fab88fc` (dynamic family, `budget_gap`, rev. 7 centring).

## What I ran

Scratch work is under `/tmp/p4rev/`. Saved scripts are in `/tmp/p4rev/scripts/`; the other checks ran inline. The committed table was not modified: I rebuilt it in a copy of the repository.

1. **Test suite:** 170 passed in 75 s.
2. **Full ladder rebuild** (`python -m paperc.runner` in `/tmp/p4rev/repo`): 77–224 s per world on 2 processes, about 13 min in all. The result is identical to the committed `ladder_table_v1.json` once `seconds` is ignored. The table reproduces from the code.
3. **Oracle table rebuild:** the `241b312 → 2e18837` diff of `oracle_table_v1.json` touches only `code_sha256` and `seconds`. The claim "identical apart from fingerprints" holds.
4. **Report against the JSON:** I parsed all §2 tables. Every policy name, mean-runs value, gain, gap and half-width was compared: 414 cells, 0 mismatches. I checked the §3 numbers by hand. They are transcribed correctly; the interpretation problems are listed below.
5. **Dev/test separation, by instrumentation** (`instrument.py`). I monkeypatched `sim.Draws.__init__` to log every campaign index built during `runner.tune_rungs`. In budget and eval_allocation, the run covered every rung: the dev trace, N1's runs and the random bisection. It touched 1,000 distinct instances, all in 4,000,000 … 4,000,999 and none ≥ `TEST_BASE`. **The guarantee is real.** The test that claims it is weak (finding 8).
6. **Fast path against recorded path, tuned rungs** (same script; budget and eval_allocation). Every tuned rung, including N2b, N4, B18 and the oracle, gave identical Y, decisions and runs on 60 campaigns. `check_campaign` with the registry and replay gave 0 violations on 20 recorded campaigns per rung.
7. **`eps_seed` tamper test** (inline): see finding 4.
8. **Random reference matching** (inline): runs of N1 and of the random rung on the dev block and on the full 10,000-campaign test block (finding 6).
9. **N2b ablation, interaction world** (`n2b_ablation.py`). The refit reproduces the committed head exactly (same name). Finding 3.
10. **N3 centring** (`n3_centring.py`, in 4 worlds). N3 was re-tuned with Track S's rev. 7 centres and the same start, steps and budget, then compared on the test block with N1, the committed N3 and the oracle member (finding 1).
11. **Knowledge gradient:** I derived the formula and checked it by Monte Carlo under the shared-incumbent-error measurement model:
    - KG 3.022e-4 against MC 3.017e-4;
    - KG 5.484e-4 against MC 5.440e-4;
    - KG 2.10e-5 against MC 1.96e-5 (small value; MC noise);
    - the predictive sd of m̂ agrees to 3 digits.

    I also derived the SPRT log-likelihood ratio and its boundaries (finding 11).
12. **N4 inputs against the exact DP, budget world:**
    - estimated p_rule 0.5513 against the exact 0.55;
    - E[V\*] 0.0010417 against 0.0010342;
    - over 312 threshold cells, the largest difference between N4's table and the exact table is 1.5e-5 (the exact thresholds range from 0 to 0.00276).

## Checked and found sound (no finding)

- **Reproducibility:** the ladder and the oracle table both rebuild exactly. `dp.solve` refactored into `solve_law` leaves every oracle number unchanged.
- **Decision-time inputs:** every policy reads only `obs_from_state` fields, plus `u` for stochastic policies. No rung touches the simulator's prior or posteriors, and the privileged forecast reaches only the privileged oracle member.
- **Stochastic randomness:** `decision_uniform` is keyed by `[60002, world code, i, step]`. `step` advances identically in the fast and recorded paths, and `_code_of_node` reproduces `ESynWorld.code`. RandomExec logs action_prob ∈ {q, 1 − q}, and replay reproduces both action and probability (subject to finding 4).
- **N0:** "keep iff Δ̂ > 0" is Paper B's harness default (`decide_trial`: keep if the candidate beats the current best). It is a correct reading of the plan's "default rule / execute-all" floor.
- **N3's formulas** match `a2u.py` at `fab88fc`:
  - E1 executes iff V\* + b_info (τ − τ̄) ≥ g0 − b_budget (r − r̄1);
  - E2 keeps iff m̂ > h0 − h_budget (r − r̄2);
  - r = runs_left / W − proposals_left / N_cap, with the current proposal counted as left at both epochs. At E2 the port uses slots_left + 1, which is right because the slot is consumed before E2. `runs_left` at E2 is after the execute run, as in Track S's harness;
  - operators are ≥ and >.

  The centring is not as in Track S (finding 1).
- **N4:** the V\* law (20 quantile bins), the rule share and the first-trial gain are estimated from dev only, and `solve_law` is the same recursion. The budget-world test (|N4 − DP| ≤ hw + 5 % of the exact DP gain of 0.0021) is meaningful: a static or broken N4 fails it by more than 10×.
- **N2-equals-DP test in the null** is meaningful: tuning must find g at or below the smallest V\*, and the test compares decision sequences on 300 test campaigns.
- **Paired statistics:**
  - all rungs run on the same 10,000 test indices;
  - "gain over N1" = rung − N1 and "gap to oracle" = oracle − rung;
  - the half-widths are 1.96 × sd(d) / √n;
  - `share_differing` is recorded.
- **Oracle row:** the P3 best member is rebuilt by name, `dp` from the exact table, and evaluated on the P4 test block.
- **Block disjointness:** dev (4,000,000 + j, n = 1,000), test (5,000,000 + j, n = 10,000) and P3's blocks (1, 2, 3 × 10⁶ + j, all below 2.4 × 10⁶ + j) are disjoint.
- **KG and SPRT formulas** are correct (finding 11 records the derivations).

## Findings

### 1. MAJOR — The N3 port does not use Track S's centring, and with coordinate search this changes the information-world result and a report finding

**Location:**
- `policies.tune_n3`: `make` fixes r̄1 = 0, τ̄ = 0.004, r̄2 = 0;
- report §3.5 and §4 ("N3 port").

**What is wrong.** At the pin, `a2u.py` defines the centres as "r1bar, taubar are m\*'s mean r and tau_pred over its eligible E1 dev decisions, r2bar its mean r over eligible E2 decisions". Centring leaves the set of policies unchanged, since it can be absorbed into g0 and h0. It does change what a fixed-budget coordinate search finds, because uncentred slopes are coupled to the levels.

The mean τ of executed E1 decisions under N1 (300 dev campaigns) is:

| World | Mean τ (executed E1, N1) |
|---|---|
| budget | 0.0102 |
| information | 0.0434 |
| keep_feedback | 0.0063 |
| interaction | 0.0042 |

In the information world, one b_info step (0.1) moves the effective E1 threshold by 0.1 × (0.043 − 0.004) ≈ 0.004. That is 8× the g step and twice N1's whole threshold (0.0018). Every b_info move looks bad, and the search ends at b_info = 0 in exactly the world for which Track S's τ term exists.

**Evidence.** I re-tuned N3 with Track S's convention, taking the centres from N1's eligible dev decisions: r̄1 = −0.0007, τ̄ = 0.02154, r̄2 = −0.1164. Start, steps and budget were the same (52 candidates). On the same 10,000 test campaigns:

| World | Committed N3, gain over N1 | Centred N3, gain over N1 |
|---|---|---|
| information | +0.00199 ± 0.00025 | **+0.00814 ± 0.00080** |
| budget | +0.00206 ± 0.00010 | +0.00201 ± 0.00011 |
| keep_feedback | +0.00165 ± 0.00020 | +0.00167 ± 0.00021 |
| strict_null | +0.00006 ± 0.00004 | +0.00005 ± 0.00004 |

- The centred information member is `n3:0.0010625,0.009,-0.1,0.00025,-0.001,…`. It uses 10.0 runs (N1: 8.3).
- Paired against the P3 oracle member (`schedule:…`) on the test block, it is **better by +0.00239 ± 0.00062**.

**Why it matters.**
- §3.5 ("N3 gains … about a third of the oracle schedule's +0.00575") is a search artefact. A faithful port of Track S's dynamic family exceeds the oracle row by about 40 %.
- The information world's "gap to oracle" column is not an upper reference. The report states in §1 that the oracle is a lower bound, but §3.5 uses it as a target.
- The same artefact would carry into SPT-5 if `tune_n3` is reused.

**Fix:**
- Compute r̄1, τ̄, r̄2 on dev as in `a2u.py`. Declare whose decisions stand in for m\*; N1's eligible E1/E2 dev decisions are the natural analogue.
- Record the centres in the JSON. Re-tune, rebuild and rewrite §3.5.
- Raise the information oracle with the P3 owner: P3's certified family-best there is at least 0.0024 below a member reachable without privileged knowledge. Describe it explicitly as a weak lower bound, or add a centred dynamic member to P3's families.

### 2. MAJOR — Tuning budgets are not equal: warm starts inherit N1's search, and the null result is misreported

**Location:**
- `runner.tune_rungs`: `tune_n3(t3, pols["N1"])`, and margin / SPRT / race / KG start from N1's (g, h);
- `policies.coordinate_search`;
- report §1 ("Equal tuning budget") and §3.1;
- `test_ladder_null_and_budget_facts`.

**What is wrong:**
- **Counts per rung in the JSON.** N1 42–49, N2 10–18, N2b 9, N3 42–55, margin 26–36, SPRT 33–35, race 24–25, KG 21–31, random 14, N4 0.
- **Uncounted dev use.** N2b's weights and N4's law are fitted on 1,000 more dev campaigns that are not counted.
- **Inherited evaluations.** N3, margin and the B18 rungs start at N1's tuned optimum, so their effective search includes N1's 42–49 evaluations, and they cannot be worse than N1 on dev.
- **The plan's rule.** Plan §7.0 asks for "a declared, equal tuning budget"; what is implemented is a cap of 60 with inherited starts.
- **Noise-chasing.** `coordinate_search` accepts any dev improvement above 1e-15.

**Evidence.** In the strict null, no rung can beat the Bayes rule. There, N3 beats N1 by **+0.000057 ± 0.000042, a 95 % interval of [+0.000015, +0.000099] that excludes zero**. It does so by repairing N1's own tuning error (h = −0.0001875), which it can do only because it starts from N1 and searches further. The centred N3 of finding 1 gives the same: +0.000053 ± 0.000041.

§3.1 says "No rung beats N1 by more than +0.00006 (within its interval)", which is false for N3. The null test allows `diff ≤ hw + 1e-4`, a slack twice the null effect sizes, so it cannot catch this. With about 70 intervals in the table and no multiplicity statement, readers will also over-read single intervals.

**Why it matters:**
- "Gain over N1" includes N1's tuning error of about 0.00005, roughly 2 % of the budget world's DP gain.
- Rungs that get more search inherit an advantage that has nothing to do with their form.
- This machinery is the template for SPT-5, where Track S STOP 4 suggests effects will be small.

**Fix:**
- (a) Make budgets equal in total evaluations. Either start warm-started rungs from a fixed declared default instead of N1's tuned point, or charge N1's evaluations to them. Give N1 the same total, for example by continuing its coordinate search until the budget is spent.
- (b) Record total evaluations per rung in the JSON, inherited ones and dev fits included.
- (c) Move only on a dev improvement larger than the paired dev s.e.
- (d) Correct §3.1. N1 is beaten in the null by about 0.00005 through its own tuning error, which is the resolution of 1,000 dev campaigns. Tighten the null test to the interval itself, or compare against the exact Bayes rule.
- (e) Add one sentence on multiplicity.

### 3. MAJOR — "One belief for every arm" is not met by N2b, SPRT or race, and two report findings are belief effects, not control effects

**Location:**
- `policies.LearnedHead` / `fit_n2b`: E2 features [1, m̂/s, Δ̂/s]; E1 features [1, V\*/s, τ/s];
- `SPRT.act` and `Race.act` at E2 (keep iff `candidate_delta_hat > h`);
- report §1 ("never refitted"), §3.3 and §3.4.

**What is wrong.**
- m̂ = a + k (Δ̂ − a) with k = A / (A + s²). A linear head on (m̂, Δ̂) therefore spans (a, Δ̂) and can implement any shrinkage factor: it refits the forecaster's E2 posterior mean. Plan §7.0 fixes that for every arm ("the same frozen immediate-value forecaster for V̂\* and m̂").
- SPRT and race do not use m̂ at E2 at all; they keep on the raw mean.

**Evidence.** In the interaction world:

| Variant | Gain over N1 |
|---|---|
| N2b's E1 head with N1's E2 rule | +0.00000 |
| N1's E1 rule with N2b's E2 head | +0.00060 ± 0.00010 (all of the gain) |
| cost-sensitive logistic head on m̂ alone (threshold h = −0.00048) | −0.00003 ± 0.00006 |

- So the "learned single-step head" gain in §3.3 is a re-weighting of Δ̂ against the belief's shrinkage. The belief does not model the interaction term, so trusting Δ̂ more pays. This is not action-head learning.
- In shared_error, where no verify is offered, SPRT and race's +0.00058 is entirely the raw-Δ̂ keep (§3.4 says so).
- In eval_allocation, their gains mix verify allocation with the raw keep. KG keeps on m̂ and is the clean comparator there.

**What is compliant:**
- N4 estimates a law of the common belief's V\*; that is not a refit.
- N0's raw keep is the declared default rule. It is acceptable as the floor but should be named as the one exception.

**Fix.** Choose one of two:
- (a) Restrict N2b to the belief's outputs plus decision-time features that are not forecaster inputs (budget position, slots, keeps; no Δ̂, no a). Make SPRT and race keep on m̂; their LLR and interval can stay on the mean.
- (b) Amend §7.0 explicitly: learned heads may read raw state. Then add a "belief re-fit" reference row to every table (a static rule on Δ̂ and/or a dev-refitted shrinkage), so that control gains are separated from belief gains.

Either way, rewrite §1, §3.3 and §3.4.

### 4. MINOR — Replay ignores the logged `eps_seed`

**Location:** `sim.behaviour_for` (always uses `EPS_KEY` through `decision_uniform`); `schema.check_campaign`.

**Evidence.** I took RandomExec(0.4) records and set `eps_seed` to None, 60003 or 60999 on every row. All three pass `check_campaign` with the registry and replay, with 0 violations. `check_campaign` requires `eps_seed` only when `eps > 0`, and stochastic rows log `eps = 0.0`. The logged seed is decorative, so a record is not self-describing.

**Fix:**
- Take the key from `view.eps_seed` in `behaviour_for`, and fail if it is None for a stochastic policy.
- Require `eps_seed` (a claimed key) on rows with 0 < action_prob < 1.
- Add a tamper test.

### 5. MINOR — The interface deviation is not recorded as an amendment

**Location:** `policies.py` and `sim.Policy`.

**What is wrong.** The runbook asks for `act(state, rng) -> (action, prob)` plus `name` and `version`. The implementation is `act(obs) -> (action, prob, selected)`, with the rng replaced by a keyed uniform `obs["u"]`. The only Protocol is `sim.Policy`, which lacks `version` and `stochastic`, and `policies.py` defines none. The keyed uniform is the better design for replay; it just needs to be recorded.

**Fix:** put a `Policy` Protocol (name, version, stochastic, act) in `policies.py`, and record the signature change as a runbook/plan amendment.

### 6. MINOR — The random reference is matched on dev only, to N1 only, and with a different keep rule

**Location:** `policies.tune_random`; `runner` (mean runs over the first 1,000 test campaigns); report §1 and §3.7.

**Evidence.** q matches N1 exactly on dev (budget world: 4.515 against 4.515), but not on the full test block:

| World | N1 runs (test) | Random runs (test) | Difference |
|---|---|---|---|
| budget | 4.469 | 4.617 | +0.148 (about 6.5 s.e.) |
| information | 8.339 | 8.252 | −0.087 (about 4 s.e.) |

Further:
- The rung is matched only to N1, while the rungs of interest in the budget world use 7.2–7.6 runs.
- Its keep rule is the Bayes keep (h = 0), not N1's tuned h. Most of its loss in keep_feedback and in the config worlds is therefore the keep threshold: in keep_feedback, random −0.020 against N2 −0.011.

**Fix:**
- Match per paired campaign: execute a uniformly random subset of the same size as N1's executions in that campaign. Alternatively, calibrate q on the test block; run counts are not outcomes.
- Add random rows matched to N4 and the oracle in the budget world.
- Give the random rung N1's h.
- Report mean runs over the full test block.

### 7. MINOR — Gaps in the staleness guard

**Location:** `runner.main` / `code_sha256`; `test_ladder_is_current`.

**What the fingerprint covers:** `paperc/policies.py`, `runner.py` and all of `table.SOURCES`, so sim.py, dp.py, oracle.py, families.py, esyn policies, worlds and extra are included.

**What it misses:**
- `main(subset)` merges old world records under a new top-level fingerprint. P3's review closed this hole for the oracle table with per-world stamps; the ladder has none.
- `oracle_table_sha256` is stored but not checked.
- `oracle_member` is not compared with the current oracle table's `best_member`.
- `schema.py`, `seeds.py` and `registry_v1.json`, which determine `record_violations`, are outside the fingerprint.

**Fix:**
- Add a per-world `code_sha256` and test it.
- Assert `oracle_table_sha256` equals the oracle table's `code_sha256`, and each `oracle_member` equals its `best_member`.
- Add `schema.py`, `seeds.py` and the registry to the fingerprint.

### 8. MINOR — Tests weaker than they claim

**Location:** `tests/test_ladder_p4.py`.

- **(a) `test_tuning_never_touches_test_seeds`.** `Tuner.seen_instances` is filled with the Tuner's own `(start, stop)`, not with the instances actually run, and the test covers N1 only. It cannot fail, and the JSON field `instances` and the docstring ("records every instance it evaluates") overstate what is recorded. The property does hold (run 5). Replace the test with an instrumented one over `tune_rungs`, monkeypatching `sim.Draws` or `run_campaign`, on a small dev size and covering every rung.
- **(b) The null test's slack** (finding 2).
- **(c) The stochastic replay test** detects a changed q only through the propensity. Add a changed-uniform or `eps_seed` tamper case (finding 4).
- **(d) Fast-against-recorded equality** is tested only for hand-made policies. Add the tuned rungs (N2b, N4, oracle); run 6 found them identical.
- **(e) `test_knowledge_gradient`** checks only monotonicity. Add the closed form against a Monte Carlo (run 11).
- **(f) No test covers the P4 seed claims:** that `EPS_KEY` equals the registry's 60002, that `DEV_BASE` / `TEST_BASE` match the claim text, and that claim values are unique.

### 9. MINOR — Report over-claims (beyond findings 1–3)

- **§3.4, "the B18 comparators recover most of the oracle gain".** SPRT recovers 47 % (0.00171 / 0.00367). Racing (73 %) and KG (68 %) do.
- **§3.6, "the budget-aware margin (+0.00124) match[es] the P3 oracle member".** The margin's gap is +0.00020 ± 0.00008, significantly below the oracle. Only N3 matches it.
- **§4, "N1 better than P3's static, so the oracle gap (0.00575) is smaller than P3's oracle gain (0.00643)".** On the same P4 test block, N1 beats P3's `static:0.0015,0.001` by +0.00032 ± 0.00028, about half of the 0.00068 difference. The rest is variation between blocks: the oracle member's value differs by 0.0012 between P3's evaluation block and the P4 test block.
- **§3.3, "Why the head gains is not analysed here".** Finding 3 gives the reason, and it belongs in the report.

### 10. MINOR — Policy identity cannot be recovered from records or from the JSON

**Location:** `LearnedHead.name` (weights rounded to 4 significant digits); `fit_n4` returns `Threshold(label="n4")`; `PolicyInfo.policy_sha = None` throughout.

**Why it matters.** Neither the records nor the table identify N2b or N4 exactly; they can be rebuilt only by refitting from dev. P7 needs behaviour policies it can reconstruct.

**Fix:** use full-precision parameters, or a content hash in `policy_sha`. Store N2b's weights and N4's law (probs, values, p_rule, first gain) in the JSON.

### 11. MINOR — B18 scope, and the formulas

**Rows that are not sequential tests.** In shared_error, no verify epoch exists, so SPRT, race and KG reduce to static rules: SPRT and race with a raw-Δ̂ keep, and KG equal to N1 exactly. They still appear as rows named `sprt` / `race` / `kg`. Label them "static (no verify epoch)" or omit them.

**OCBA and re-audit.**
- The OCBA omission is acceptable. B18 says "KG/OCBA verify", and KG verify is implemented and correct. One line should note that OCBA's natural use here is the final selection among kept configurations.
- The missing re-audit comparator is acceptable as stated, and BUILD_LIST records it. Note in the report, though, that B18 has no comparator for the shared_error channel, whose whole oracle gain (+0.00221) is re-audit.

**Formulas, verified:**
- **SPRT.** For x̄ ~ N(μ, s²), the LLR of μ = h + δ against μ = h − δ is 2δ (x̄ − h) / s². Here s is the sd of the mean comparison, σ_m √(1/n_c + 1/n_i), and x̄ is sufficient under the compound-symmetric shared incumbent error. The bounds ±log((1 − α)/α) are Wald's with α = β. Caveat: α is nominal, because a kept incumbent's recorded error is selected (winner's curse).
- **KG.** E[max(m′, h)] − max(m, h) = σ̃ (zΦ(z) + φ(z) − max(z, 0)), with z = (m − h)/σ̃ and σ̃² = A s²/(A + s²) − A s′²/(A + s′²). σ_m is recovered as s² / (1/n_c + 1/n_i), with the n_i = 0 start handled. All of this is correct, and run 11 confirms it by Monte Carlo.

### 12. MINOR — N2b details to declare or fix

**Location:** `fit_n2b`, `dev_trace`.

- The E1 head's target is the kept gain under the Bayes keep (δ · 1[m̂ > 0]), not under N2b's own E2 head.
- Training traces come from the W = llm_cap variant. This changes the keep feedback in keep_feedback, which is declared, and the posterior states in information, which is not.
- Labels are the noise-free true Δ, more than a real per-proposal audit gives.
- The 9 counted candidates exclude the weight fit on 1,000 dev campaigns (finding 2).

**Fix:** declare these in §4, and use N2b's own E2 head in the E1 label.

### 13. MINOR — Runner against the runbook wording, and the seed claims

**Location:** `runner.build_world`; seeds claim `esyn_ladder_blocks`.

**What is wrong:**
- **The test block is not recorded.** The runbook says the runner works "for a set of instance seeds from the P2 registry's Paper C block, writes P1 records and returns paired terminal Y". All table numbers come from unrecorded index ranges under key 60001 (4,000,000 + j and 5,000,000 + j). These are not instance seeds in `paperc_instances`, and `MAX_RECORDED` prevents recording them.
- **Records are a separate check.** P1 records exist only for 3 campaigns per rung (instances 0–2).
- **Y is not the terminal value.** The returned Y is the noise-free `y_true`, not `Terminal.y_terminal`. That is reasonable on E-SYN, but it is a deviation and should be declared.
- **Duplicate claim value.** `esyn_ladder_blocks` reuses the value 60001 under a second name, and no uniqueness check exists.

**Fix:**
- State these deviations in §1/§4.
- Make the ladder blocks an amendment of `esyn_rng_root`'s use text, or an explicit index-range field.

### 14. MINOR — No overfitting diagnostics

**Location:** `runner.tune_rungs` / JSON.

The JSON stores no dev value for the selected policies. The optimism of selecting among up to 60 candidates on 1,000 dev campaigns therefore cannot be read from the table.

**Fix:** store each rung's dev mean and its paired dev s.e. against N1.

## Summary

The engineering is sound:
- the table reproduces exactly, and the oracle table is unchanged;
- records pass `check_campaign` and fast and recorded paths agree for every tuned rung;
- dev/test separation holds by instrumentation;
- N2 equals the DP in the null and N4 matches the exact DP in the budget world, with meaningful tests;
- the SPRT and KG formulas are right, and every number in the report is transcribed correctly.

Three findings stop acceptance:
1. **The N3 port's centring.** With Track S's own centring, N3 gains four times as much in the information world and beats the oracle row, so §3.5 is wrong.
2. **Unequal tuning budgets.** Warm starts give some rungs N1's search for free, and the strict null shows the effect, contradicting §3.1.
3. **The "one belief" rule.** It is not met by N2b, SPRT and race, and the interaction and shared_error findings are belief re-weighting, not control.

All three need code changes, a rebuild and report revisions; none needs new infrastructure. The eleven MINOR findings are hygiene, tests and wording.

Verdict: NOT ACCEPTED
