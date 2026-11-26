Reviewed base: 62451900c2863f25ee4572c03022a3b2f48fd821

# Track S — S0.5 summary, `digits_mlp` part, with the author's diagnostics — independent review record (14–15 November 2026)

Branch `mac-tracks-s05-summary-20261114`, from `trackS-ops-20261030` @ `7593ee5b`. The Mac-side S0.5 summary of runbook rev 3.3 Phase 4 for `digits_mlp` (tabular follows), the calibration-gate failure with the options the runbook allows, and the author's descriptive diagnostics of 14 Nov 23:20 (why the two pilot policies coincide; variance decomposition; offline two-parameter recalibration). Four rounds by one freshly spawned independent reviewer agent (AI-assisted, Claude).
- Round 1 (`1101d4a3`): changes requested (the runbook gives only a STOP for this mix of failures, not two options; W can also move up to 20).
- Round 2 (`a4cfbacb`, diagnostics added): changes requested (§5.2 claim limited by its grid edge; λ explanation wrong).
- Round 3 (`adc44d09`, wide grid): changes requested (λ = 1 not a grid point, so the "λ < 1 only" statements were grid artefacts).
- Round 4 (`62451900`, λ = 1 scan): **accepted**.

Accepted commit (round 4, last): 62451900c2863f25ee4572c03022a3b2f48fd821

Notes, not blocking: the in-sample λ = 1 window is about 2–3 % wide in c (a finer scan gives about 2.7 %); the window was found by the reviewer in round 3. Both S0.5 items go to the author after the `tabular_mlp` half (author, 14 Nov).

The round texts are reproduced unchanged below.

---

# Review: Track S S0.5 summary, `digits_mlp` part (round 1)

Reviewed commit: 1101d4a33561ab4c658bb8a5f421978e10f07155
Branch: `mac-tracks-s05-summary-20261114` (worktree `/tmp/pb/wt/s05sum`); base `trackS-ops-20261030` @ `7593ee5b5a06682c98c46b40d39e97932f4baf68` (= `refs/mac/trackS-ops-20261030` in `/tmp/pb/repo`, and = `HEAD^`).
Reviewer: independent AI reviewer (Claude). The target worktree was not modified: `git status --short --ignored` is unchanged. The only entries are the ignored `r1/__pycache__/` and `r1/tracks/__pycache__/`, which were created at 23:17:57, before the commit and before this review (see N5). Scratch work was done on a `git archive` export under `/tmp/rev_s05`, which has been removed.
Authority used: runbook `13badb0d:docs/r1/prompts/TRACK_S_OPERATOR_RUNBOOK_20261030.md`, sha256 `a93fb84bd04f650d726ddb683acb0c6d0a621196d3dd5460d91be89ff4c82a53` (matches). Code: `r1/tracks/analyze.py`, `collect.py` and `a2u.py` at `8237fd02`.

Verdict: changes requested

All numbers reproduce, and the data claims are correct. Two statements need a fix: what the runbook offers the author (B1), and how W depends on tabular (B2). Both are wording fixes and need no re-run.

## 1. Reproduction

| Check | Result |
|---|---|
| `s05-summary` with the report §1 command, run from the archive copy: `AR_HARNESS_ROOT=/tmp/pb/wt/harness-pin PYTHONPATH=/tmp/pb/wt/pin8237 /tmp/trackg_venv/bin/python -P -m r1.tracks.analyze s05-summary --node digits_mlp=results/r1/tracks/digits_mlp/s05_t7_20261113 --out …` | rc 0. `cmp` with the committed `s05_summary_digits_20261114.json`: **byte-identical**. The module came from `/tmp/pb/wt/pin8237/r1/tracks/analyze.py` |
| `analyze.py` | sha256 `b952af6c…` at `8237fd02`, and identical at `7593ee5b`, as stated. Python 3.13.18 |
| λ₂: the runbook §11.6 snippet, extracted verbatim from the runbook and run on `s05_calibration.jsonl` | `{"n": 298, "n_null_skipped": 0, "q90": 2.384938484838408, "lambda2": 3.4629750764976746}`. **Byte-identical** to `lambda2_digits_20261114.json` |

## 2. Independent recomputation from the raw jsonl

My own script (not the analyze code) recomputed every value. Every report value matches.

| Report value | Recomputed |
|---|---|
| Roots | 50, all `ok`, 50 distinct ids. (a2u, rep 0) 20, (static:0.00198,0, rep 0) 20, (static, rep 1) 10 |
| Binding shares at W 8 / 10 / 12 / 20 | 1.00 / 1.00 / 0.94 / 0.04 (50 truncated rows per W) |
| σ_cmp,vary | median `sd_paired` = 0.00835616667 (n 298, no nulls) |
| σ_D between policies at W 12 (m 20) | max \|D\| = 0.0 at **every** W (8, 10, 12, 20 and the cap of 40), so sd 0 and UCL 0 |
| σ_D between repetitions at W 12 (m 10) | sd 0.006834, χ² 80 % UCL 0.008839 |
| `between_policy_sd_at_cap` | 0.0 (m 20, W 40) |
| Near band b | 0.5 × median \|margin\| = 0.008587444606. n 596; median E1 0.017174, median E2 0.022084 |
| Coverage by stratum | 0: 35/65 = 0.5385 · 1-2: 60/89 = 0.6742 · ≥3: 136/144 = 0.9444 · overall: 231/298 = 0.7752 |
| q₉₀ \|z\| by stratum | 3.137 / 3.110 / 0.977. Over all rows: 2.3849, so λ₂ = 3.4630 |
| Consistency checks | The `covered` flag agrees with `lo ≤ delta_audit ≤ hi` on 298/298 rows. `lo`/`hi` = `mu` ∓ 1.28155·`sd` on every row. The stratum matches `n_group` on every row. No null `delta_audit` |
| λ | manifest `obs_inflation` 1.0. The prior `a2u_prior_r2_20261111.json` (sha256 `5c849d15…`, = manifest `prior_sha256`) has `meta.obs_inflation` 1.0 |
| LLM calls / audit runs per campaign | 40.0 / (1770 / 50) = 35.4 |
| Input hashes and row counts in §1 | `2e4c9a8c` / `cd296fd8` / `039b6955` / `68a0d6e0`; 298 / 200 / 50 rows |

**a2u vs `static:0.00198,0` on the 20 rep-0 instances:**
- The (index, epoch, action) sequences are identical on 20/20 instances, and so are the eligibility flags.
- `y_terminal` (exact float equality) and `runs_used` are identical on 20/20 at W 40.
- In `s05b_truncated.jsonl`, `y_terminal`, `runs_used` and `binding` are identical on 20/20 at each of W 8, 10, 12 and 20.
- `llm_seed_base` is equal per instance.
- Margins: 298 of the 596 eligible margins differ, all of them E1, by at most 0.00132 = 0.00198 − 0.00066. The E2 margins are identical. The example in the report (E1 0.0172 vs 0.0159) is s30500, index 2: 0.017174 vs 0.015854.

**Action counts** over the 20 a2u roots: E1 skip 429, execute 318; E2 discard 170, keep 148, failed_invalid 53. These match the report, and the static rep-0 counts are identical.

**Seeds.** I scanned every integer field whose path contains "seed", in all six jsonl files and the manifest, plus every `__s<N>` in the strings:
- instances 30500–30519;
- audit seeds 200000–200384;
- `seed` 30500–200384;
- `llm_seed_base` from 0 to 4.1e9;
- selection 35001.

**None of them** falls in 7001–7010 or 9001–9210.

**Input directory.**
- `SHA256SUMS`: `sha256sum -c` gives 40/40 OK, and the file has 40 lines.
- `git diff --quiet 7593ee5b 1101d4a3 -- results/r1/tracks/digits_mlp` is clean: the commit changes only the three added files.

## 3. Reading of the runbook

- **λ₂ versus STOP.** Phase 4 sets the λ₂ revision for coverage **too low** overall or in stratum `1-2` or `>=3`. It sets **STOP for the author** for coverage **too high**, or for a **failing stratum `0`** in either direction.
  - Here, 1-2 is too low, which is the λ₂ branch.
  - Stratum 0 is too low and ≥3 is too high, which are both the STOP branch.
  - The report states this correctly.
- **λ₂ cannot make the gate pass: correct**, and I confirmed it in the code.
  - `a2u.group_posterior` with no observations returns (μ₀, τ₀) whatever λ is.
  - `forecast` uses the predictive sd √(τ_n² + τ_w²), and τ_w is not inflated.
  - `predictive_intervals` adds the audit se.
  - So stratum-0 intervals do not depend on λ, and stratum 0 (0.5385 at n = 65) alone blocks a pass. A re-run would draw a new sample, but its stratum-0 intervals would follow the same λ-free law.
  - λ only widens intervals for n_group ≥ 1, so it cannot bring ≥3 down from 0.944.
- **Fallback: correct.** Phase 4's fallback is the S0.7 + S3e time projection (> 4 days, Phase 1 projection, confirmed by the author). It is not a remedy for calibration.
- **Options: not exactly as the runbook states them.** See B1.
- **W being provisional: incomplete.** See B2.

## BLOCKING

**B1. §3 says "The runbook offers the author two things". The runbook offers none for this case.**

For a failing stratum 0 or for coverage that is too high, Phase 4 says only **"STOP for the author"**. It lists no author options at that STOP. It also has no rule for a mixed failure, where low coverage in 1-2 occurs together with a STOP-branch failure.

- Option 1 ("order the λ₂ = 3.463 re-run anyway") is something the author may decide at the STOP. It is not an option the runbook provides. Running the λ₂ branch while the STOP branch also applies is a reading of a STOP rule. Runbook §0.6 says: "If a report needs any other reading of a STOP rule, do not adopt it in the report. Flag it to the coordinating session, which changes this runbook."
- Option 2 ("hold Phase 4 at this STOP") is not an option. It is the state the runbook prescribes.

Because the task asked specifically for "the options the runbook allows", this misattribution matters.

**Required fix:** state the two parts of the rule separately.
- For low coverage in 1-2 alone, the runbook's action would be the λ₂ revision (λ₂ = 3.463; steps as listed).
- For stratum 0 and for ≥3, the runbook's action is a STOP for the author, with no further runbook-defined option.
- The runbook has no rule for this combination. Whether to run λ₂ anyway is the author's decision outside the literal rule. It is flagged to the coordinating session under §0.6, not adopted.

The existing sentences on remedies outside the runbook (stratum-0 and ≥3 intervals, §10 "anything not covered: STOP and ask") and on the fallback can stay.

**B2. §2 says W "can be lowered by tabular_mlp". The code can also set W to 20 and drop the budget member.**

`s05_summary` (analyze.py, about l. 2172–2173) works as follows:
- `ok` = the candidates with share ≥ 0.5 on **every** primary node;
- `W = max(ok) if ok else max(Ws)`, that is, 20;
- if `ok` is empty, `budget_binds` is false and the budget member is "dropped".

Digits binds at 8, 10 and 12, so the joint result is one of two cases:
- W ∈ {8, 10, 12}, if tabular binds in ≥ 50 % at some candidate ≤ 12;
- otherwise **W = 20 with the budget member dropped**. This raises W and changes the design.

The report's sentence covers only the first case. In addition, the σ_D values reported "at W = 12" depend on W and are provisional in the same way. The between-repetition UCL is:

| W | Between-repetition UCL |
|---|---|
| 8 | 0.007902 |
| 10 | 0.007964 |
| 12 | 0.008839 |
| 20 | 0.006928 |

The between-policy value is 0 at every W. σ_cmp,vary, b, `between_policy_sd_at_cap`, λ and the calibration status are per node and do not change when tabular is added.

**Required fix:** state both branches of the W rule, and mark the σ_D-at-W row as depending on the joint W.

## NON-BLOCKING

**N1. The data already show why the policies coincide (§4).** The counts in §4 include decisions that were not eligible:
- All 429 E1 skips are `skip_reason: rule_duplicate`, which is not a threshold decision.
- **All 298 eligible E1 decisions were `execute` under both policies.**
- The eligible E1 index values lie in [0.017663, 0.017898]. The minimum E1 margin is 0.01568 under the static (threshold 0.00198) and 0.01700 under a2u (0.00066), so no eligible E1 index came near either threshold.
- The E2 margins are identical under both policies, consistent with h = 0 on the same index.
- So in this pilot, any E1 threshold below about 0.0177 gives the same campaigns.

Adding this (eligible-only counts: E1 execute 298; E2 discard 170, keep 128) would give the design owner the mechanism directly. The question in the report ("whether A2-U's index decisions reduce to the static threshold") can then be narrowed to why the E1 index is nearly constant at about 0.0177. The §4 claims as written are accurate and not overclaimed. They are limited to the 20 rep-0 pilot instances. rep 1 has only the static policy, so it gives no comparison.

**N2. "A zero σ_D … would make any power or size calculation degenerate" is slightly too broad.**
- At S0.8, `plan_sizing` uses σ_D,UCL = max(S0.5b UCL, S0.7 dev UCL), and n is fixed at 300. The S0.7 dev UCL would therefore take over unless it is also 0.
- The place where it is degenerate now is the first S0.6 run: `match_noise(between_policy_sd=0)` bisects σ_campaign towards 0.

Suggest naming those two places instead of "any".

**N3. The near band b inherits the same degeneracy.** The a2u E1 margins span only 0.01700–0.01724, so the E1 half of b's input is effectively one constant: g0 subtracted from the near-constant index. This is worth one sentence next to §4, since b feeds S3a.

**N4. The STOP timing could be clearer.** The header says STOP 4 can be sent only when both nodes are in. The calibration STOP for digits does not depend on tabular. Consider saying that the calibration STOP goes to the author now, and that STOP 4 (W, σ_D, b, λ, projection) waits for tabular.

**N5. Informational: pycache folders.**
- The target worktree has ignored `r1/__pycache__/` and `r1/tracks/__pycache__/` (created 23:17:57, before the commit at 23:19:26). This shows that the branch's own `r1` package was imported in the worktree at some point. It is harmless: `analyze.py` is byte-identical at `7593ee5b` and at the pin, and the committed JSON reproduces from the pin with `-P`.
- Reviewer's disclosure: my reproduction wrote `__pycache__` into `/tmp/pb/wt/pin8237/r1/` and `r1/tracks/`. Their birth time was 23:20:26, after this review started. I removed both, and `git status --short --ignored` there is empty again.

---

# Review: Track S S0.5 summary, `digits_mlp` part (round 2)

Reviewed commit: a4cfbacb5e8a7ce4a241877a5fe9a8ad403d0556
Previous round: 1101d4a33561ab4c658bb8a5f421978e10f07155 (round 1: changes requested; B1, B2 and N1–N5).
Branch: `mac-tracks-s05-summary-20261114` (worktree `/tmp/pb/wt/s05sum`).
Reviewer: independent AI reviewer (Claude).
- The target worktree was not modified. `git status --short --ignored` shows only the two ignored `__pycache__` folders that predate round 1.
- All runs used a `git archive` export of a4cfbacb under `/tmp/rev_s05`, with `PYTHONDONTWRITEBYTECODE=1`. That folder has been removed. `/tmp/pb/wt/pin8237` is still clean.

Verdict: changes requested

The round-1 findings are resolved, and both diagnostics reproduce byte for byte. The scripts match `a2u.py` at the pin. The issue is §5.2's conclusion about the recalibration. "No grid point passes even when chosen on S0.5" holds only on the report's grid. The grid stops at c = 10, which is exactly where one of the report's own optima sits. Past that edge there are S0.5 points that pass, and the stated reason (and the "model change needed" inference) is wrong for the `tau0_only` variant (B1).

## Round-1 findings

| Finding | Status | Evidence |
|---|---|---|
| B1: options attributed to the runbook | **Resolved** | §3 now says the runbook's action is STOP for the author. It has no rule for the mixed case, so a λ₂ re-run would be an author decision outside the runbook. |
| B2: W can also go up | **Resolved** | The W row states both branches, including W = 20 with the budget member dropped. The between-repetition UCLs at W 8, 10, 12 and 20 (0.007902, 0.007964, 0.008839, 0.006928) match my round-1 values. |
| N1: mechanism of the coincidence | **Resolved** | §5.1 |
| N2: "any power or size calculation" | **Resolved** | §4 now names the S0.6 noise match and says the zero is masked in the S0.8 max. |
| N3: near band b | **Resolved** | The b row |
| N4: STOP timing | **Answered** | §6 records the author's instruction. I cannot verify the instruction itself; it is stated as the author's. |
| N5 | Informational only | — |

## Reproduction

- **diag1:** `/tmp/np244/bin/python ../s05_summary/diag/diag1.py s05_t7_20261113`, run from the export's `results/r1/tracks/digits_mlp`. The output is **byte-identical** to `diag1.json`.
- **diag2:** `/tmp/trackg_venv/bin/python ../s05_summary/diag/diag2.py s04_rerun20261111/a2u_prior_r2_20261111.json s04_rerun20261111/s04_rows.jsonl s05_t7_20261113/s05_calibration.jsonl` (rc 0). The output is **byte-identical** to `diag2.json`.
- **§5.1 values against `diag1.json`:**
  - 747 E1 decisions, 318 executed and 429 skipped. All 429 skips are `rule_duplicate`.
  - Execute share per instance is 0.275–0.68.
  - Runs used are 11–27. The worker budget was exhausted in 0/20 instances; the LLM cap was reached in 20/20.
  - V*−g lies in [0.017003, 0.017238], median 0.017174.
  - 0 decisions fall between the two thresholds, 0 within ±0.0033 of either threshold, and 0 below g.
  - 0.0157 / 0.0066 = 2.4 σ_node.
- **§5.2 values against `diag2.json`:**
  - Every decomposition row matches: ratios 3.77 / 3.02 / 0.42; τ_w² shares 0.946 / 0.970 / 0.994; se² shares 0.053 / 0.029 / 0.005; bias² shares 0.04 / 0.04 / 0.11.
  - The sd reconstruction error is 6.9e-18.
  - All five recalibration rows match the table.
  - The reported pass count is 0/6561 in both variants.
  - Prior: τ_w 0.04929 (7.5 σ_node), τ0 0.00099, σ_cmp 0.01862.

## Do the scripts match `a2u.py` at 8237fd02?

- **`group_posterior` form.** `diag2.post` matches it term by term: obs_var = λ(σ_cmp² + τ_w²); var = 1/(1/τ0² + n/obs_var); μ = var(μ0/τ0² + Σ/obs_var). The prior has a single kind, `local`, so using `kinds["local"]` for every row is correct.
- **Predictive sd.** `forecast` uses τ = √(τ_n² + τ_w²), and `predictive_intervals` uses sd = √(τ² + se²). This matches `√(var + tw² + se²)`. Z = Φ⁻¹(0.9).
- **E1 and E2 rules.** For both policies, E1 executes iff V* ≥ g: `static_execute` → `rules.execute(0, μ, τ, σ, g)`, with the margin equal to V* − g. `static:0.00198,0` is `static_price(g = 0.00198, e2_offset = 0)`, so h0 = 0 and `default_keep` is true for both. E2 is therefore the Bayes keep, m̂ > 0, for both. The §5.1 statement is correct.
- **One difference from the code.** `A2UController.__init__` refuses `obs_inflation < 1`. The report notes only that the runbook does not allow λ < 1 (see N2).

## Is the S0.4 replay a fair stand-in for the controller's group observations?

Yes.
- The controller's observations for a group are `replay.deltas[(symbol, sign)]`: the `delta_vs_best` of every earlier executed trial in the campaign that has a metric and is not a noop or a duplicate.
- `s04_rows.jsonl` comes from `collect.dev_rows`. It covers every executed non-noop, non-duplicate proposal of the S0.4 campaigns (`ExecuteNonRuleController`). Its `delta_hat` is `features…outcome["delta_hat"] = row["delta_vs_best"]`.
- In the 165 rows: no null `delta_hat`, `delta_audit` or `se`; no trial-1 row; one kind.
- Grouping by (instance, key, sign) in `budget_index` order therefore reproduces the controller's observation lists.
- Caveats, which the report states or which are harmless:
  - The prior was fitted on these same rows, so S0.4 is in-sample for c = 1.
  - S0.4 executed every non-rule proposal. That matches S0.5 here, because A2-U executed every eligible proposal.
- **S0.5 group sums.** The 6.9e-18 check covers only the sd (n, se, τ), not the sums. I checked the sums separately:
  - The recovered sum is exactly 0 on every n_group = 0 row.
  - The recovered per-observation means for n ≥ 1 lie in [−0.254, 0.245], median 0.0084, which is plausible for Δ̂.
  - Precision is not a concern. The data term is about 1e-2 relative to μ, so double precision recovers the sums to about 1e-13.

## BLOCKING

**B1. §5.2 overclaims. Points that pass exist just outside the grid, and the stated reason is wrong for `tau0_only`.**

The report says no (c, λ) passes "even when chosen on S0.5 itself (0 of 6,561 points, in both variants)". It explains this by saying that c moves every stratum the same way and that "λ acts only on the negligible τ_n²". It concludes that "a remedy would need a spread that depends on n_group … that is a model change".

- **The grid is truncated at the optimum.** The report's own `tau0_only` max-log-lik row sits at **c = 10.0, the grid edge**. I wrote an independent, vectorised version of the same evaluation, with the same formulas, the same S0.4 replay and the same S0.5 sum recovery, and reproduced the report's baseline coverage. On an extended grid, c ∈ [0.01, 1000] × λ ∈ [1e-4, 1000] with 151 × 151 log-spaced points:

  | Variant | S0.4 criterion | c | λ | S0.5 test 0 / 1-2 / ≥3 | Gate |
  |---|---|---|---|---|---|
  | `tau0_only` | max log-lik (interior optimum: S0.4 LL 251.0 vs 235.1 at c = 1) | 34.1 | 1.28 | 0.600 / 0.843 / 0.958 | fail |
  | `tau0_only` | min worst-stratum error | 54.1 | 0.21 | 0.600 / 0.640 / 0.840 | fail |
  | `both` | max log-lik | 1.08 | 0.0016 (edge again) | 0.600 / 0.809 / 0.972 | fail |
  | `both` | min worst-stratum error | 1.00 | 1e-4 (edge) | 0.538 / 0.652 / 0.840 | fail |

  So the **out-of-sample** statement still holds on the wider grid: (c, λ) fitted on S0.4 does not pass on S0.5.
- **The in-sample statement does not hold.** In `tau0_only`, **12 grid points pass on S0.5**. All have c ≈ 86–108 (τ0 ≈ 0.085–0.107, about 13–16 σ_node) and λ ≈ 0.60–0.93. Examples:
  - c 92.6, λ 0.832 → 0.738 / 0.798 / 0.889;
  - c 100, λ 0.747 → 0.785 / 0.742 / 0.875.

  **None has λ ≥ 1**, so none is admissible under the λ₂ rule or the code. The closest admissible point found is c = 100, λ = 1 → 0.785 / 0.820 / **0.903**. In `both`, and in a τ_w-only variant, nothing passes even on the wide grid.
- **The mechanism.** "λ acts only on τ_n" is not correct. λ enters the posterior **mean** as well as τ_n. At the run's prior both effects vanish only because τ0 sits at its floor. Once τ0 is large, the existing conjugate model's predictive variance τ_n² + τ_w² does shrink with n_group, and μ_n follows the group's data. That is exactly the "spread that shrinks with n_group" the report says needs a model change. It is reachable through the prior parameter τ0, at least in-sample.

**Required fix.** Restate §5.2's conclusion as bounded:
- (a) On c ∈ [0.1, 10] × λ ∈ [0.1, 30], no point passes, either fitted on S0.4 or in-sample on S0.5.
- (b) The S0.4-fitted parameters also fail on S0.5 on a wider grid.
- (c) In-sample passes exist only with τ0 ≈ 13–16 σ_node and λ < 1, which the code and the λ₂ rule refuse.
- (d) Drop or correct "λ acts only on τ_n²" and "c moves every stratum the same way" (both true only near the τ0 floor). Change "needs a model change" to say that the n_group dependence is available through a larger τ0, a prior change for the author, and that it is not supported out of sample here.

Either widen the grid in `diag2.py` and regenerate `diag2.json`, or keep the grid and state its limits as above.

## NON-BLOCKING

**N1. One common cause: τ0 is at its floor (worth one sentence in §5.1 and §5.2).** `fit_prior` (a2u.py, about l. 207 and 239) sets τ0² = max(τ_A2² − τ_w², (0.15 σ_node)²). Here τ_A2 = 0.01897 < τ_w = 0.04929, so τ0 = 0.15 × 0.0066 = **0.00099, the floor**. The prior precision 1/τ0² ≈ 1.0e6 swamps the data precision of about 360 per observation, so μ_n and τ_n barely move with the group's history. That is why V* is nearly constant (§5.1). The report's "predictive sd dominated by τ_w" explains only why τ is constant, not why μ_n is. The same cause makes the spread independent of n_group (§5.2). The S0.4 likelihood rises from 235.1 at c = 1 to 251.0 at c ≈ 34 (`tau0_only`, λ ≈ 1.3), so the S0.4 data themselves prefer a much larger τ0.

**N2. λ < 1 is also refused by the code.** `A2UController` raises an error for `obs_inflation < 1`. Mention this next to "which the runbook's λ₂ rule does not allow".

**N3. The `tau0_only` "min worst-stratum error" row is a tie artifact.** For c ≤ 1 the criterion is flat because τ0 is at the floor. The argmin is simply the first grid point (c 0.1, λ 0.1), and its S0.5 coverage is the baseline. Label it as a flat criterion instead of an optimum.

**N4. Wording.**
- "3–4 × the prediction" is a ratio of mean squares (variances). Say "mean-square" or give the sd ratio (about 1.7–1.9 × and 0.65 ×).
- "Budget pressure never enters" holds for the W = 40 pilot. At the candidate W ≤ 12 the budget binds in 94–100 % (S0.5b). Neither policy reads the budget, so the coincidence is unaffected, but "in the W = 40 pilot" would be precise.
- The "recovered exactly" sentence cites only the sd check. Add the sum check (zero at n_group = 0), or say that the sd check does not test the sums.

---

# Review: Track S S0.5 summary, `digits_mlp` part (round 3)

Reviewed commit: adc44d09c66f3b536f3a8e3a58aabc0d9a128e57
Previous round: a4cfbacb5e8a7ce4a241877a5fe9a8ad403d0556 (round 2: changes requested; B1, N1–N4).
Branch: `mac-tracks-s05-summary-20261114` (worktree `/tmp/pb/wt/s05sum`).
Reviewer: independent AI reviewer (Claude). The target worktree was not modified. Runs used a `git archive` export of adc44d09 under `/tmp/rev_s05`, with `PYTHONDONTWRITEBYTECODE=1`. That folder has been removed.

Verdict: changes requested

`diag2.json` reproduces, and every number in the new §5.2 matches it. The new central claim is wrong, however: that the in-sample passes all need λ < 1, so no point with λ ≥ 1 reaches the gate. This is an artefact of the grid. **λ = 1 itself is not a grid point**, and at λ = 1 exactly, a narrow band of τ0 scales passes on S0.5 (B1).

## Reproduction

- **diag2:** `/tmp/trackg_venv/bin/python ../s05_summary/diag/diag2.py s04_rerun20261111/a2u_prior_r2_20261111.json s04_rerun20261111/s04_rows.jsonl s05_t7_20261113/s05_calibration.jsonl`, run from the export's `results/r1/tracks/digits_mlp` (rc 0, about 12 min). The output is **byte-identical** to the committed `diag2.json`.
- **diag1:** `diag1.py` and `diag1.json` are unchanged since a4cfbacb (`git diff --quiet`), so the round-2 reproduction stands.

The §5.2 numbers match `diag2.json`:

| Row | `diag2.json` |
|---|---|
| both, max log-lik | c 1.00, λ 0.00147 → 0.538 / 0.809 / 0.972 |
| both, min worst-stratum error | c 1.00, λ 1e-4 → 0.538 / 0.652 / 0.840 |
| tau0_only, max log-lik | c 34.81, λ 1.386 → 0.600 / 0.854 / 0.972 |
| tau0_only, min worst-stratum error | c 51.09, λ 0.185 → 0.600 / 0.640 / 0.840 |
| In-sample passes | both 0/14641. tau0_only 8/14641, `with_lam_ge_1` = 0, at c ∈ {90.9, 100, 110.1} and λ ∈ [0.619, 0.926] |
| Best grid point with λ ≥ 1 | tau0_only: c 110.07, λ 1.059 → 0.831 / 0.820 / 0.903. both: c 1.62, λ 1.059 → 0.615 / 0.888 / 0.986 |

## Round-2 findings

| Finding | Status | Evidence |
|---|---|---|
| B1: grid truncated; in-sample claim; wrong mechanism | **Partly resolved** | Resolved: the grid is wider; the out-of-sample result is kept and still holds (see N1); the explanation is corrected (τ0 at its floor because τ_A2 < τ_w; λ also moves the posterior mean; a larger τ0 is the direction to look). Not resolved: a new grid-bound overclaim (B1 below). |
| N1: τ0 at the floor as the common cause | **Resolved** | §5.2 "Why" |
| N2: the code refuses λ < 1 | **Resolved** | — |
| N3: tie in the min-worst criterion | **Partly resolved** | The optimum is no longer at the grid edge, but the criterion still ties (N1 below) |
| N4: wording | **Resolved** | "Mean squared residual … predicted variance"; "in this W = 40 pilot"; the sum check is cited |

## BLOCKING

**B1. "Every in-sample pass has λ < 1" and "no point allowed by the current rules reaches the gate" are artefacts of the grid.**

- **The grid skips λ = 1 and the relevant band of c.** The λ grid (121 log-spaced points on [1e-4, 1000]) does not contain λ = 1; its nearest values are 0.926 and 1.059. The c grid steps by a factor of 1.10 near the band that matters: 90.9, 100, 110.1, 121.2.
- **Fine search at λ ≥ 1.** I used the same formulas, the same S0.5 sum recovery and tau0_only, with c ∈ [1, 1000] at 700 points and λ ∈ [1, 1000] at 300 points.
  - Points with λ = 1.0 pass.
  - A scan of c ∈ [100, 125] in steps of 0.01 at λ = 1 passes for every **c ∈ [112.6, 115.6]**: τ0 ≈ 0.111–0.114, about 17 σ_node.
  - Example: c = 114.1, λ = 1 covers 58/65, 68/89 and 129/144 = **0.892 / 0.764 / 0.896**, all in [0.70, 0.90].
  - At λ = 1.02, 1.05 and 1.1, no c in that range passes.
  - For `both`, no point with λ ≥ 1 passes on the fine grid either; the best is 0.615 / 0.888 / 0.986.
- **So these statements are false:**
  - "every one has λ < 1 and the code and the runbook would refuse it" (true only of the 8 grid points);
  - "the best allowed point (λ ≥ 1) … just outside the band";
  - "does not reach the gate on digits within the allowed λ ≥ 1";
  - "passes only with λ < 1";
  - "no point allowed by the current rules reaches the gate".

  In sample, a **change to τ0 alone, at the run's own λ = 1**, reaches the gate. The window is narrow: about 3 % in c. Stratum 0 sits near the top of the band, and stratum ≥ 3 is near its edge.
- **What still holds.** Out of sample, no S0.4-fitted (c, λ) passes. A larger τ0 is the direction to look, and it is a prior change for the author.

**Required fix:** add λ = 1 to the grid, or report a fine scan at λ = 1, and restate the in-sample result. For example: in sample, `tau0_only` passes on a narrow window, c ≈ 113–116 (τ0 ≈ 0.11) at λ = 1, as well as on the λ < 1 points listed. This is an upper bound fitted on S0.5 itself, and the S0.4 fits do not reach it. The `with_lam_ge_1` count and `s05_in_sample_best_with_lam_ge_1` in `diag2.json` should then reflect that grid, or the report should say they are bounded by the grid.

## NON-BLOCKING

**N1. The min-worst-stratum criterion still ties.**
- On the report's grid, **18** tau0_only points share the minimum S0.4 worst-stratum error of 0.0846 (c 51.1–110.1, λ 0.185–0.473), and **15** `both` points share 0.1333 (c 1.0–1.1, λ 1e-4 to 3e-4).
- The table shows the first one in grid order.
- None of the tied points passes on S0.5: the S0.5 worst-stratum error is 0.148–0.200 for tau0_only and 0.200–0.262 for both. The out-of-sample conclusion is therefore unaffected.
- Note the tie in the table, or break it by log-likelihood.

**N2. The attribution "log-likelihood 251.0 at c ≈ 35 … from the round-2 reviewer" is imprecise.**
- My round-2 maximum was c ≈ 34.1, λ ≈ 1.28, on a 151 × 151 grid.
- The report's own grid gives c = 34.8, λ = 1.39.
- Quote the report's own grid value and its own log-likelihood instead.

**N3. The `diag2.py` docstring is garbled.** The new grid text was inserted before "(multiplies the update's observation variance, …)". The second parenthesis now sits after the grid sentence.

**N4. Small qualifier.** The decomposition bullet still says the n_group-dependent spread is something "a constant τ_w cannot represent". Add "at the floor τ0" so it agrees with the corrected "Why" paragraph.

---

# Review: Track S S0.5 summary, `digits_mlp` part (round 4)

Reviewed commit: 62451900c2863f25ee4572c03022a3b2f48fd821
Previous round: adc44d09c66f3b536f3a8e3a58aabc0d9a128e57 (round 3: changes requested; B1, N1–N4).
Branch: `mac-tracks-s05-summary-20261114` (worktree `/tmp/pb/wt/s05sum`).
Reviewer: independent AI reviewer (Claude). The target worktree was not modified (`git status --short` is empty). Runs used a `git archive` export of 62451900 under `/tmp/rev_s05`, with `PYTHONDONTWRITEBYTECODE=1`. That folder has been removed.

Verdict: accepted

## Reproduction

- **diag2_lambda1.** Command: `/tmp/trackg_venv/bin/python ../s05_summary/diag/diag2_lambda1.py s04_rerun20261111/a2u_prior_r2_20261111.json s04_rerun20261111/s04_rows.jsonl s05_t7_20261113/s05_calibration.jsonl`, run from the export's `results/r1/tracks/digits_mlp`. It took 18 s, and the output is **byte-identical** to `diag2_lambda1.json`.
- **Verbatim copy.** The block of `diag2_lambda1.py` from its argument line to `cs = …` is identical to `diag2.py` from its argument line to `# ---- decomposition`. The only difference is one trailing blank line. The model, the S0.4 replay, the S0.5 sum recovery, `evaluate`, `gate` and `worst` are therefore the ones checked in rounds 2 and 3.
- **diag2.py.** Only the docstring changed (6 lines, all docstring). `diag2.json`, `diag1.py` and `diag1.json` are unchanged since adc44d09 (`git diff --quiet`). The round-3 byte-for-byte reproduction of `diag2.json` therefore stands.
- **Values in `diag2_lambda1.json`:**

  | Variant | Passes at λ = 1 | Detail |
  |---|---|---|
  | tau0_only | 3 points | c 112.59 → 0.862 / 0.775 / 0.896; c 113.71 → 0.862 / 0.764 / 0.896; c 114.84 → 0.892 / 0.764 / 0.896 |
  | both | 0 | best c 1.61 → 0.615 / 0.888 / 0.986 |

  These agree with my independent round-3 scan at λ = 1, which passed for c ∈ [112.6, 115.6]; c = 114.1 gave the same 0.892 / 0.764 / 0.896. The 700-point log grid steps by about 1 % in c, so its last passing point is 114.8 and the next point, about 115.9, lies outside the window.

## Round-3 findings

| Finding | Status | Evidence |
|---|---|---|
| B1: λ ≥ 1 statements were a grid artefact | **Resolved** | §5.2 now says the 8 grid passes have λ < 1 "(λ = 1 is not a grid point)". It reports the λ = 1 scan (c ≈ 112.6–114.8, τ0 ≈ 0.11, about 17 σ_node, example c 114.8 → 0.892 / 0.764 / 0.896). It concludes that at λ = 1 a change to τ0 alone reaches the gate in sample, in a narrow window, with S0.5 itself as the fitting set, and that the S0.4-fitted recalibration does not reach it. The false statements are gone: `grep` finds no remaining "λ < 1 only", "best allowed point" or "no point allowed" claim. The surviving "cannot pass through the runbook's only revision" (l. 68) is about the λ₂ rule and remains correct. |
| N1: min-worst-stratum ties | **Resolved** | 18 / 15 tied points, their c and λ ranges, and "none passes on S0.5". These match my round-3 values. |
| N2: log-likelihood attribution | **Resolved** | The report now quotes its own grid optimum (c 34.8, λ 1.39) and attributes 251.0 vs 235.1 to my own grid. |
| N3: garbled docstring | **Resolved** | — |
| N4: "at the floor τ0" | **Resolved** | — |

## NON-BLOCKING (no action required)

- §5.2 calls the window "about 2 % wide in c". That figure comes from the 700-point grid (112.6–114.8). A finer scan gives 112.6–115.6, about 2.7 %, so "about 2–3 %" would match both. The report already cites both ranges.
- "The round-2/3 reviewer found the same window" refers to round 3.

Accepted commit: 62451900c2863f25ee4572c03022a3b2f48fd821
