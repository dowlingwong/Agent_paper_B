# Build review — P6: fork design and go/no-go statistics (round 1)

- **Reviewer:** independent reviewer (Claude subagent, AI-assisted). I had not seen this work before the review.
- **Commit:** `0727320` on branch `paperc-build-20261115`. Diff read against `9341938` (P5 accepted).
- **Date:** 16 Nov 2026
- **Label:** ENGINEERING_ONLY

## Scope read

- Runbook §0 (scope, determinism, review loop, STOP conditions) and P6, including the amendment of 16 Nov 2026 (P6 build).
- Plan §6 (go/no-go statistics, SPT-3 fork trees), §6.1 (fork data are designed interventions; IPW for population averages, not for fitting N6) and §7.1 (N6).
- Track S originals on `origin/trackS-ops-20261030`, read-only:
  - `r1/tracks/collect.py`: `selection_draw`, `is_near`, `select_forks`, `run_leaf`;
  - `r1/tracks/analyze.py`: `build_fork_table`, `_cont`, `assign_folds`, `crossfit_total_q`, `_flip_value`, `fork_fit`, `refitting_bootstrap`;
  - `r1/tracks/simulate_controls.py`: `Sim.run_leaf` and the leaf loop of `simulate`, the analysis simulator that E-SYN ports.
- Code:
  - `paperc/esyn/sim.py`: `ForkSpec`, `ForkDraws`, `fork_seed`, and the fork handling in `run_campaign`;
  - `paperc/forks.py` and `paperc/forks_validation.py`;
  - `paperc/seeds.py` (claims 60003 and 61001) and `seeds/registry_v1.json`;
  - for context, `paperc/schema.py` (fork-row rules, `check_campaign`), `esyn/worlds.py` (`proposal_sequence` segments), `esyn/policies.py` and `paperc/policies.py` (N1 = `Static`, N0, `Dynamic`, `InteractionAware`).
- Tests: `tests/test_forks_p6.py` and the edited line in `tests/test_esyn_p3.py`.
- Outputs: `docs/reports/FORK_VALIDATION_20261116.md`, `esyn/fork_validation_v1.json` (including the raw per-collection records), the P6 row of `BUILD_STATUS.md`, and B8 in `BUILD_LIST.md`.

## What I ran

Scratch scripts are in `/tmp/p6rev/`. I did not rerun the full validation.

1. **Full suite:** 201 passed in 156 s.
2. **`python -m paperc.forks_validation --report-only`:** `git status` was clean afterwards, so the committed markdown reproduces from the JSON.
3. **Tables:** `git show 9341938:` against the current `oracle_table_v1.json` and `ladder_table_v1.json`. Recursively equal once `code_sha256`, `seconds` and `oracle_table_sha256` are removed. The claim "identical apart from fingerprints" holds, so root campaigns are unchanged.
4. **Determinism:** I rebuilt collection 0 of `information` with the validation's constants (`probe_n6_leak.py`). The N6 point estimate and interval match the committed raw record exactly (−2.359e-3, [−2.878e-3, +1.437e-3]).
5. **Simulator checks** (`probe_sim.py`; 806 fork pairs over 7 worlds × 6 roots × 2 continuation policies, E1 and E2 forks):
   - the trace before the fork trial equals the root's;
   - `CampaignResult.immediate` equals the traced increment when the candidate is kept at t_f, and 0 otherwise;
   - `fork_step` equals the root's step;
   - post-fork proposals executed in both arms have the same key and size (common random numbers inside `run_campaign`, not only in `ForkDraws`).
   No discrepancy.
6. **N6 bootstrap leakage** (`probe_n6_leak.py`, `probe_n6_leak2.py`, `probe_n6_cover.py`): the committed `n6_value` against a variant whose bootstrap copies keep their root's id for fold assignment, as Track S does. Finding 1.
7. **Epoch pooling of τ̂²** (`probe_epoch.py`; 100 roots per world, every eligible decision, r = 2): finding 3.
8. **The null property of `d` with a continuation that reads the budget** (`probe_dyn.py`): finding 4.
9. **shared_error population value on four disjoint 400-root blocks** (`probe_shared.py`): finding 8.
10. **Privileged policies inside forks** (`probe_priv.py`): finding 6.
11. **Inline recomputations from the JSON:**
    - "roots for 80 % power": all 10 values reproduce from n (2.8 sd / τ²_pop)²;
    - raw against summary means;
    - the oracle z with the corrected replicate variance (finding 5).

## What is right

- **Fork continuations are correct.**
  - The root is replayed exactly up to the fork decision, stochastic roots included (the behaviour's uniform is keyed by the unchanged step index; `test_forks_from_a_stochastic_root`).
  - The forced row has `action_prob = null`, `behaviour_action` / `behaviour_prob`, `rule = "fork_arm"`, `branch_path = ["<fork_id>:<arm>:c<c>:r<r>"]`, the root's campaign id and a `ForkDesign` with the replicate.
  - Proposals after t_f come from a stream keyed by (fork point, continuation, replicate), shared by the arms. Measurements after the fork decision are keyed by the arm. At an E2 fork, the trial's execute and verify measurements stay the root's, and its re-audits are the arm's.
  - `immediate` is right (item 5 above).
  - Rule-forced and unreached fork points raise.
  - `check_campaign` accepts root and fork rows.
- **Design.**
  - Poisson sampling with three uniforms per decision point.
  - p_select = 1 − (1 − q_u)(1 − q_o·1{near}), as Track S's `selection_draw`.
  - The near band is centred on the behaviour policy's own g and h, as Track S's `is_near` (review M1).
  - Deterministic, keyed by a claimed seed; `select_all` sets p_select = 1; design weights are 1/p_select.
  - A fixed q_uniform in place of Track S's min(1, forks / n) is a valid design and makes Horvitz-Thompson (HT) exact.
- **`fork_diffs`.** s.e.²_j = (1/C²) Σ_c s²_jc / R is unbiased for Var(D̄_j | root history), because the replicates are i.i.d. given the history (different continuation and measurement streams per replicate and per continuation policy).
- **`tau2_point`.** It is the design-weighted between-fork variance, with the Kish factor k/(k − 1), minus the design-weighted mean s.e.². It targets the population τ² over eligible decisions; the Kish factor's error is O(1/n). It is unbiased on the synthetic tables (test) and covers 0 in the null world for `d`: 0.935 ± 0.034 over 200 collections, bootstrap s.e. / sd 0.98.
- **HT and Hajek means are design-unbiased.** Over 500 redraws the z values are small; the unweighted mean is visibly biased, as it should be.
- **N6 point estimate.**
  - Folds are drawn by root.
  - The ridge is fitted per epoch, unweighted, on q̄ (plan §6.1).
  - The flip value is 1{π′ ≠ b}·(±1)·q̄ against the logged behaviour action, with Hajek weights.
  - The fallback when training data are thin is counted.
  - The point estimate is leak-free: the structural test passes, the B "estimate − oracle" z values lie within ±2, and in my probe mean(estimate − value of the fitted π′ under independent replicates) ≈ 0 in three worlds.
- **The q vs d reasoning is right.**
  - E[q | s] = E[I | s] + E[d | s].
  - In `strict_null` (W = cap = 40, fresh keys, increment comparisons), with N1 and N0 as continuations, E[d | s] = 0 for every state, while E[I | s] varies with the kept increment. τ̂²_q ≈ 22·10⁻⁶ there (τ_q/σ = 0.72).
  - The amendment states this, and the report shows the q row (coverage of 0: 0.000) next to the d rows. Nothing is hidden. The executor reports both statistics and does not choose between them, which respects the author's decision. Finding 4 adds a condition the amendment omits.
- **Seeds.** 60003 lies in `paperc_rng_keys` and 61001 in `paperc_train_seeds`, both inside Paper C blocks; the registry is regenerated and the seed tests pass.
- **Scope.** Every change is under `paperC/`.
- **Reported numbers.** The "roots for 80 % power" numbers are computed as described.

## Findings

### 1. MAJOR — the N6 refitting bootstrap leaks: copies of one root land in different folds

**Location:**
- `forks.py` `_boot_index` (each drawn copy gets its own cluster id `j`);
- `n6_point` (`_assign_folds(clusters, ...)` on those ids) and `n6_value`;
- the `n6_point` docstring ("gives each drawn copy of a root its own id, so that copies never straddle folds");
- `tests/test_forks_p6.py::test_bootstrap_copies_are_separate_clusters`, which asserts this behaviour.

**What happens.** In a bootstrap replicate, a root drawn twice gets two cluster ids, which `_assign_folds` places in folds independently. With 5 folds the two copies fall in different folds with probability 4/5. The held-out copy's forks, identical rows with identical q̄, are then in the training set of the model that predicts them.

The docstring's sentence is literally true: each copy lies in one fold. But it is the wrong property. Track S's `assign_folds` / `refitting_bootstrap` states the right one: "A bootstrap copy of an instance carries its original id, so all copies land in one fold". The port departs from its source on exactly this point.

**Evidence:**
- **Straddling share.** In bootstrap replicates of `information` collection 0, 36 % of the distinct drawn roots straddle folds.
- **The committed intervals sit above the point estimate.** From the raw records, the interval centre minus the point estimate averages +0.3 to +0.9 sd of the estimate in every world, and at least +0.6 in five of seven. In `information` it is +8.0e-4 against an estimate sd of 8.9e-4. The point estimate lies below the lower bound in 1–7 % of collections and above the upper bound in none.
- **Re-run in my probe** (12 collections per world, identical data, only the fold ids changed):

| World | committed: (centre − est) / sd | root-id folds: (centre − est) / sd |
|---|---|---|
| strict_null | +0.70 | −0.88 |
| budget | +0.81 | −0.79 |
| interaction | +0.53 | −0.75 |
| shared_error | +0.65 | −0.53 |
| eval_allocation | +0.82 | −0.71 |
| information | +1.35 | −0.94 |
| keep_feedback | +0.03 | −1.25 |

  Removing the leak reverses the shift. The downward shift that remains has a different cause: a replicate holds only about 63 % distinct roots, so it trains on less information.
- **Coverage of the value of the fitted π′** (30 collections per world; truth from independent replicates 3–10 on the same forks):
  - committed: 0.97 / 0.87 / 0.97 (strict_null / information / eval_allocation), with the interval centred about one conditional sd above the estimate;
  - root-id folds: 1.00 in all three.
  
  Neither interval is calibrated for this estimand, and the committed one is biased upward.

**Why it matters:**
- The N6 value is one of the two go/no-go statistics (plan §6), and its floor will be judged on the interval. A leak-driven upward shift favours "go".
- The validation never checks the N6 interval. Section B tests only the point estimate. Section C reports "CI > 0 / CI < 0" against no truth, and "CI < 0" is 0.000 in every world, including `information`, where the mean estimate is −7.2e-4. The defect was therefore invisible in the committed report.

**Fix:**
- Assign bootstrap folds by the original root id, so all copies of a root share a fold, and change the test to assert that.
- Decide which estimand the interval covers, then validate its coverage on E-SYN and add a row to the report:
  - the value of the fitted π′ (then a bootstrap with π′'s cross-fitted decisions held fixed is the natural interval);
  - or the expected value of the procedure (then compare against a Monte Carlo truth over collections, and use a bias-corrected or basic interval if the percentile interval mis-covers, as my probe suggests it will).
- Regenerate section C's N6 columns.

### 2. MINOR — the measurement-noise convention departs from Track S's analysis simulator, and the docstring says it follows Track S

**Location:** the `sim.py` module docstring ("Randomness after the fork follows Track S's convention …"), `ForkDraws`, and the `forks.py` docstring.

**What differs.** In `simulate_controls.Sim.run_leaf`, the per-replicate `Stream`, and with it every later measurement ε, is shared by the arms. The E1 execute arm reuses the root's own fork-trial measurement (`fork["eps"]`). Only the audit RNG is per arm.

P6 makes every measurement after the fork decision arm-specific, including the execute arm's measurement at t_f. As a result, an arm whose action equals the behaviour's action is not the root's own continuation. The docstring cites `collect.py` only for the proposer seed, which is accurate, but the sentence reads as if the whole convention were Track S's.

**Why it matters:** the convention sets the within-fork variance. It therefore drives the precision of τ̂² and the "roots for 80 % power" figures passed to the author, which would change under Track S's convention.

**Fix:**
- State the departure and its reason: real workers do not share noise between different configurations.
- Optionally report a sensitivity run with shared measurement noise, or say that the power figures are conditional on this convention.

### 3. MINOR — τ̂² pools E1 and E2 forks, so it contains the between-epoch mean difference; per-epoch HT means cannot be computed

**Location:** `forks.py` `tau2` / `tau2_point`, applied to all forks; `fork_means` (N = all eligible decisions); `ForkTable.subset` (`n_eligible`).

**Evidence** (`probe_epoch.py`): pooled τ̂²_d against the share-weighted within-epoch value.
- `keep_feedback`: 25.5 against 16.7 (×10⁻⁶). About 35 % of the pooled value comes from the epoch means (E1 −3.4e-3, E2 +2.7e-3).
- `budget`: 0.35 against 0.27.
- Elsewhere the difference is small.

`fork_means` divides by all eligible decisions of both epochs, so an E1-only HT mean cannot be formed. `ForkTable.subset` keeps `n_eligible` only for roots that still have a selected fork, which changes `n_roots` and the HT denominators of any fork subset. The validation does not hit this; it is a trap for P7 / P9.

**Why it matters:**
- A constant-sign effect that differs between E1 and E2 is not a "state-dependent sign change" (plan §6), yet it raises the pooled τ̂².
- The pooled mean q mixes execute − skip with keep − discard and is not a population contrast of the plan.
- The author's floor needs to know which variance it applies to.

**Fix:**
- Report τ̂² per epoch (or epoch-centred) alongside the pooled value, and document the choice.
- Keep eligible counts per epoch in `n_eligible`.
- Make `subset` either keep every root's eligible count or refuse to be used for HT quantities.

### 4. MINOR — the null property of `d` holds only for continuation policies that ignore the arm's bookkeeping; the docstring and the amendment state it without that condition

**Location:**
- `forks.py` docstring ("in a world without a sequential channel (`strict_null` …) it is exactly 0 in expectation for every state");
- the runbook amendment ("The null-world property of step 4 holds for `d` only");
- the report header of section A.

**Why it matters:**
- After an execute or a keep, the arms differ in `runs_left`, `keeps_so_far` and `incumbent_obs`. A continuation that reads these makes different later decisions in the two arms, even when W never binds.
- In `strict_null`, with a Track S dynamic member as continuation (`Dynamic(g, h + 20σ, b_keep = 40σ)`, 120 roots, every eligible decision forked):
  - mean d at E1 is +4.1e-4 (s.e. 5.4e-5);
  - the τ̂²_d interval is (0.06, 1.01)·10⁻⁶, which excludes 0.
- With N1 on the same roots it is 0 within noise.
- SPT-3's "2 declared continuation policies" may well include N3 members (plan §7.1).

**Fix:** state the condition in all three places: continuation policies whose later decisions do not depend on the budget and keep counters, here N1 and N0.

### 5. MINOR — the oracle-comparison z in section B uses the wrong replicate variance, and the comparison is close to vacuous

**Location:** `forks_validation.py` `oracle()`: `se_or = sqrt(mc² + (R_OR/2 + 1)·mean_se_reps²)`.

**The error.** The estimate's design expectation is the mean of replicates 1–2. The oracle is the mean of replicates 1–16, which contains them. With single-replicate variance σ², Var(ā₁₂ − ā₁…R) = σ²/2 − σ²/R = (R/2 − 1)·σ²/R. The code adds the two variances, giving (R/2 + 1), and drops the positive covariance. For R = 16 that is 9 instead of 7, so every z is too small by a factor √(7/9) ≈ 0.88.

**Corrected values** (my recomputation): still within about ±2. The largest are shared_error d −1.86 → −2.10 and information q +1.69 → +1.90.

**A further weakness.** Replicates 1–2 and 1–16 of the same states agree in expectation by construction, so this column can only catch a replicate-dependent seeding bug. Design-unbiasedness is already shown by the z against the population of the 1–2 differences.

**Fix:**
- Use (R/2 − 1), or compare against replicates 3–R only (independent).
- Describe the column for what it is.

### 6. MINOR — a fork takes `privileged` from the root policy, not from the policy acting

**Location:** `sim.py` `run_campaign`: `privileged = bool(getattr(policy, "privileged", False))` is fixed at the start and used at every E2 after the fork.

**Evidence** (`probe_priv.py`, `interaction` world):
- **Privileged continuation under a non-privileged root.** An oracle member (`InteractionAware`, β = 50) never receives its bonus. Its decisions equal `Static(g, h)` in 30 of 30 forks, against 16 of 30 that differ when both run as roots. `check_campaign` replays it consistently, so nothing flags it.
- **Non-privileged continuation under a privileged root.** `Static` writes `privileged:interaction` forecasts into 17 of its 55 rows, against P3's rule that only privileged policies' rows carry them.

**Why it matters:** none of the validation uses these combinations. But "Q under the oracle continuation" is a natural E-SYN check in P7 / P8, and it would silently be Q under the myopic continuation.

**Fix:**
- Compute the privileged forecast and bonus from the acting policy (`cur`) at each E2 and write them only for it, or reject mismatches in `ForkSpec`.
- Add a test.

### 7. MINOR — test gaps; one test fixes the defect of finding 1

**Location:** `tests/test_forks_p6.py`.

**The gaps:**
- `test_bootstrap_copies_are_separate_clusters` asserts the leaking fold-id convention. It should assert that copies share a fold.
- `test_n6_cross_fitting_never_uses_held_out_outcomes` covers only the point estimate with unique clusters, not bootstrap replicates with duplicates.
- **Untested in the simulator:**
  - `CampaignResult.immediate`;
  - common proposals inside `run_campaign` (the test compares `ForkDraws` arrays only);
  - the E2-fork measurement split (the trial's measurements before E2 are the root's, its re-audits the arm's).
  
  I checked these with `probe_sim.py` and found no error, but nothing pins them.
- **No interval-level test of N6**, for example coverage on a synthetic table with a known value.
- **No staleness check on the validation output.** `fork_validation_v1.json` carries no code fingerprint and no test compares it with the code, unlike the oracle and ladder tables. It can go stale silently.

**Fix:**
- Add tests for the items above.
- Add `code_sha256` (forks, sim, validation) to the JSON and a test that compares it with the code.

### 8. MINOR — the report and the status line understate some limitations

**Location:** `reports/FORK_VALIDATION_20261116.md` (C, C2, notes) and the P6 row of `BUILD_STATUS.md`.

**What is understated:**

- **The shared_error inconsistency is not mentioned.**
  - C2 (160 roots): every one of the 20 τ̂²_d values is ≥ 0.68·10⁻⁶. The median is 1.64, the population value 0.70, coverage 0.80 ± 0.18, bias z +3.46.
  - The table shows this; no sentence does.
  - My probe locates the cause in the "truth", not the estimator. Every eligible decision forked on four disjoint 400-root blocks gives τ̂²_d = 0.70 (block 8000+, the report's population), 1.06 (0+), 1.31 (2000+) and 1.60 (4000+). The design-weighted estimator on the same roots matches each block value: means 0.81 / 1.08 / 1.31 / 1.63 over 20 redraws.
  - The population value is therefore much less precise than its bootstrap interval [0.20, 1.23] suggests (the same fourth-moment problem), and it is the lowest of four blocks.
  - Consequence: shared_error's coverage and bias columns are measured against a value that is probably low by about 40 %. Its "1,235–1,689 roots for 80 %" scales as 1/τ⁴, so with τ² ≈ 1.2 it would be about 0.35 of that.
  - The generic note ("coverage against them is approximate") does not tell the reader that a check failed, or why.
- **"τ² intervals for q run up to 21 % narrow" omits d.** The d intervals are as narrow:
  - bootstrap s.e. / sd = 0.82 for budget (C) and 0.70 for eval_allocation (C2);
  - d coverage of the population is 0.85 in eval_allocation (C2).
- **N6 power is not stated.** At 40 roots the N6 interval excludes 0 from above in 0–7.5 % of collections in every world. The mean value is negative in 5 of 7 worlds (−7.2e-4 per decision in `information`). Beyond finding 1, the report gives no reading of the N6 columns.
- **For the q vs d choice, the report should say plainly** that τ̂²_q is about the same in `strict_null` (22.5·10⁻⁶) and in budget, interaction, shared_error and eval_allocation (23.8–26.5). At these settings, q heterogeneity is dominated by the one-step value and does not separate the null world from four of the six channel worlds. Its lower bound exceeds 0 in 100 % of null collections.
- **"N6 per campaign" needs a description.** It is the HT total of single-decision deviation gains per root. It is not the value of running π′ for a whole campaign, and it should be labelled as such.

**Fix:**
- Add a short limitations paragraph to the report covering these points.
- Correct the status line.
- For shared_error, either estimate the population τ² on more roots (for example the four blocks above together, 1,600 roots) and recompute coverage and the power figure, or mark the shared_error rows as not assessable.

### 9. MINOR — seed claim text and block choice

**Location:** `seeds.py` claim `analysis_resampling` (61001).

**The issues:**
- The claim's use text lists purposes 1 (τ²) and 2 (N6). `forks_validation.oracle()` also draws `default_rng([61001, 3, rep])` for the leakage redraws, which is not listed.
- The block `paperc_train_seeds` is described as "seeds of Paper C's own model training (SPT-5): optimisers and samplers". Analysis resampling fits that description only loosely; `paperc_rng_keys` ("design randomness") would also do.

**Fix:**
- List purpose 3.
- Either justify the block in the claim text or move the claim before anything depends on it. Disjointness from Paper B is not affected.

### Nits

- `fork_validation_v1.json` has wall-clock `seconds` fields (§0.5). This is the same precedent as the oracle and ladder tables, which earlier reviews accepted.
- E-SYN q and d use the noise-free Y and the true increment, whereas recorded rows carry y_terminal with audit noise and no `immediate_measured`. There is not yet a path from P1 records (root and fork rows plus terminals) to a `ForkTable`, so the statistics cannot yet run on SPT-1 records. That belongs to a later phase (B11), but it should be listed as open.
- `select_forks`'s `fork_id` `f{trial:02d}{ep}` is unique only while llm_cap < 100 (it is 40 here).

## Summary

The simulator side of P6 is sound. Fork continuations reproduce the root exactly, the forced-row fields and errors are right, `immediate` is right, proposals are shared by the arms, and root campaigns and the committed tables are unchanged. The design matches Track S's selection rule, and its weights give exactly design-unbiased HT means. The τ̂² estimator and its cluster bootstrap behave as claimed for `d` in the null world. The q vs d amendment is honest, and its core reasoning is correct (finding 4 adds a missing condition).

The blocking problem is the N6 interval. The refitting bootstrap lets copies of a root straddle folds, contrary to the Track S code it ports and to its own docstring. The result is an interval shifted upward by about 0.5–1.4 estimator sds in six of seven worlds, for one of the two go/no-go statistics. A test fixes the convention in place, and the validation never measures N6 coverage (finding 1).

The other findings concern documentation of conventions (2, 4), epoch pooling (3), a section B variance formula (5), a latent privileged-policy bug (6), tests (7), report accuracy (8, including the unexplained shared_error failure, which traces to an imprecise population value) and seed-claim text (9).

Round 2 needs, at minimum:
- finding 1 fixed, with an N6 coverage row in the validation report;
- the report and status corrections of finding 8;
- the conditions of finding 4 stated.

Verdict: NOT ACCEPTED

---

## Round 2 — independent receiving review (16 Nov 2026)

**Reviewer:** independent Codex reviewer. **Label:** ENGINEERING_ONLY.

**Reviewed:** branch `paperc-build-20261115`, HEAD and local `origin/paperc-build-20261115` tracking ref at `ce253416c47b63f667a56ff531b04411b18b0d9f`, using diff `0727320..ce253416`. I read the round-1 response, build runbook §§0 and P6 including the amendment, plan §§6, 6.1 and 7.1, addendum §§B–D, and the pinned Track S fold and refitting code at `fab88fc`.

### Verification

- **Suite.** 207 passed in 154.64 s, with no skips. I used the isolated pinned `paperC/.venv`, one thread for each numerical backend, bytecode writes disabled, and pytest's cache provider disabled.
- **Artifact.** Pure `markdown(res)` applied to the committed JSON reproduces all 12,312 bytes of the committed report. The fingerprint matches, and recalculation from the raw records reproduces the stored N6 coverage and the pooled and per-epoch `d` and pooled `q` coverage summaries. The oracle and ladder tables match both `9341938` and `0727320` field by field after removing timing and fingerprints.
- **Round-1 findings 1 and 7.** The primary refit path now passes original root IDs to the fold assignment in each bootstrap draw. Perturbation tests verify that duplicate copies cannot affect their own held-out actions. The added tests also cover the fixed-decision interval, simulator immediate gains, common proposals, the E2 measurement split, and output freshness. The committed per-decision E-SYN benchmark gives refit coverage 0.900–1.000 for each collection's fitted rules and 0.925–1.000 for the across-collection procedure mean. Fixed-decision coverage is 0.800–0.900. Findings 1, 5 and 6 below concern gaps beyond the original fold leak.
- **Round-1 findings 2, 3 and 4.** The source and report identify independent post-fork measurement noise and qualify its precision and power figures accordingly. The epoch APIs retain the eligible counts and use the requested epoch denominator. Section A gives pooled strict-null `d` mean τ̂² of 0.047 × 10⁻⁶ and coverage of zero of 0.935 under N1/N0. The code, amendment and report tie this property to continuation decisions that ignore the bookkeeping altered by forcing the fork arms. The remaining reporting gap for `q` is in Finding 2 below.
- **Round-1 findings 5 and 6.** The seeding check uses independent replicate sets 1–2 and 3–16 with the variance of both means. The absolute HT z maxima are 1.74 versus the same-replicate design mean and 1.32 for the independent-replicate mean comparison. The N6 diagnostic's reported maximum absolute z is 1.39. After the forced decision, privileged E2 forecasts follow the continuation policy. Finding 3 below concerns the forced E2 row itself.
- **Round-1 findings 8 and 9.** The updated report and status disclose the independent-noise convention, interval-width shortfalls, and the `shared_error` discrepancy. In C2, it has 19/20 coverage against the finite population reference and z of +2.94 with the bootstrap s.e. or +2.47 with the block s.e. The primary N6 interval had zero positive lower bounds in the 40-root collections. Seed claim 61001 documents all three uses and the rationale for the sampler block, and the generated registry passes.

### Findings

1. **MAJOR — the N6 per-root interval drops roots with no selected forks.** `forks.py:353–361, 460–487, 503–518`. The reported HT point estimate divides by all collected roots. Both bootstrap intervals draw only from `np.unique(ft.instance)`, the subset with selected forks, and divide by the original all-root denominator. This removes sampling variation from the number of roots contributing to the numerator. In a valid synthetic Poisson design with 100 eligible roots, one decision per root, inclusion probability 0.1 and ten selected roots with constant gain 1, the point estimate was 1. Both production interval paths returned `[1.0, 1.0]`. Resampling all 100 observed root totals, ten at 10 and 90 at zero, produced `[0.5, 1.6]` with stable fitted decisions. The linked fitted-rule reference also derives its fold shares from roots represented among the selected forks. Resample the complete root roster with zero HT contribution for an empty root, carry the full fold-mixture definition into the per-root truth, and validate the reported per-root interval on a design that produces empty roots. Section C currently validates the per-decision form. The per-root form matters if the author declares the floor in units tied to the terminal-Y margin in plan §§6 and 11.3.

2. **MINOR — the report lacks E1 and E2 results for total `q`.** The amendment states that τ̂² is reported pooled and per epoch, and leaves the author the statistic and pooling choices. `tau2(..., target="q", epoch=...)` is implemented, but `TAU_KEYS`, `_tau_set` and `population` store `q` only pooled. Sections A, P and C and the underlying raw records contain the two epoch strata only for `d`. Supply the corresponding E1/E2 `q` estimates and validation summaries so the declared alternatives are documented.

3. **MINOR — forced E2 rows misidentify the policy that generated privileged forecasts.** `esyn/sim.py:354–378, 482–509`. The E2 forecast state correctly replays the behaviour root, then `fork_here` switches `cur` before `emit` labels that state with the continuation policy. In an `interaction` probe, a privileged root followed by a static continuation produced a forced row with `policy=static:0,-0.00025` and `privileged:interaction`. Reversing the policies produced a row with an oracle policy label and only `a2u`. The first state otherwise matched the root exactly. Record the behaviour policy provenance for the forced row while retaining the separate continuation ID, and test both privilege directions at an E2 fork. The current privilege regression test forks at E1.

4. **MINOR — the design constructor accepts sampling with zero inclusion probability in part of the HT population.** `forks.py:114–118, 161–188, 388–398`. `Design(q_uniform=0, q_oversample=0.5, ...)` accepts a near-only sample. A far decision then has `p_select=0`, although the HT denominator includes it, so the documented full-population design-unbiasedness fails. Require positive uniform inclusion where the target is all eligible decisions, or define and enforce an eligible denominator restricted to a population with positive support. The committed E-SYN validation uses positive inclusion.

5. **MINOR — the refit benchmark masks asymmetric errors relevant to a floor.** All seven fitted-rule misses in the committed per-decision records place the truth above the upper endpoint, including 4/40 for `keep_feedback`. Its procedure mean is above the upper endpoint in 3/40. The wide, downward-shifted intervals support the reported two-sided coverage figures, with weaker calibration for an upper-bound decision. State the two tail miss rates alongside aggregate coverage and identify the benchmark as using a shared finite population reference. The observed 0/40 positive lower bounds in each channel world also carries Monte Carlo uncertainty despite the displayed Wald error of zero.

6. **MINOR — the Section B N6 leakage z omits cross-fold covariance.** `forks_validation.py:198–225`. The diagnostic uses the identity `mean = Σ c_j e_j` and treats the learned coefficients `c_j` as fixed when reporting `sqrt(Σ c_j² Var(e_j))`. A held-out root's own coefficient avoids its outcome, but its noise can affect rules for other folds. Terms can therefore be correlated across folds, even with independent replicate draws for each state. Label this z as a descriptive plug-in diagnostic, or calibrate it over independent realizations of the full check. The structural original-root fold test establishes the fix for the round-1 leakage.

The remaining acceptance blocker is Finding 1. The author retains the SPT-1 choices of `q` or `d`, epoch pooling, the N6 estimand and units, and the floors. B11 remains open for the logged-record loader. The E-SYN results carry the ENGINEERING_ONLY label.

Verdict: NOT ACCEPTED
