# Non-RL ladder and sequential-testing comparators on E-SYN (build runbook P4; BUILD_LIST B4 + B18; revised after review rounds 1 and 2)

**AI-assisted (Claude, chat session, 16 Nov 2026). ENGINEERING_ONLY.** E-SYN results are implementation checks and
method behaviour per channel, never evidence about the real loop (plan §5).

- **Data:** `paperC/esyn/ladder_table_v1.json` (schema `paperc_ladder_table/v2`), produced by
  `python -m paperc.runner` (about 25 minutes on two processes). It stores fingerprints of its code (per world as
  well) and of the P3 oracle table it reads.
- **Tests:** `paperC/tests/test_ladder_p4.py`; the full paperC suite has 175 tests, all passing.
- **Revision.** Round 1 of the independent review (`reviews/BUILD_P4_REVIEW_20261116.md`) found three MAJOR issues:
  - N3 lacked Track S's centring;
  - tuning budgets were unequal;
  - three rungs read the raw increment, outside the common belief.

  The fixes are in `reviews/BUILD_P4_RESPONSE_R1_20261116.md`. Several round-1 findings changed.
- **Round 2** found one more MAJOR issue: N2b's budget-world gain came from a budget feature whose sign depends on the
  dev draw, combined with a cut tuned on terminal value. N2b now reads belief outputs only. A tuned shrinkage-refit
  reference row was added. Fixes are in `reviews/BUILD_P4_RESPONSE_R2_20261116.md`.

## 1. What was built

| Module | Content |
|---|---|
| `paperc/policies.py` | **`Policy` Protocol:** name, version, stochastic, `act(obs) -> (action, probability, selected)`; a stochastic policy reads a uniform keyed by its logged `eps_seed`. This is an amendment of the runbook's `act(state, rng)`, recorded in BUILD_RUNBOOK P4.<br>**Ladder (plan §7.1):**<ul><li>N0: execute all, keep iff Δ̂ > 0 (Paper B's default rule);</li><li>N1: static (g, h);</li><li>N2: g tuned, keep iff m̂ > 0;</li><li>N2b: single-step heads on belief outputs only;</li><li>N3: Track S's dynamic family with its centring;</li><li>N4: knapsack DP on a V\* law estimated on dev.</li></ul>**Reference rows:** the P3 oracle member, the exact DP where it applies, random execution at a matched realised budget, and two belief-refit rows (`ShrinkRefit`, `RawKeep`).<br>**B18 comparators:** SPRT-style verify, racing, knowledge-gradient verify, budget-aware keep margin.<br>Tuning under an equal, declared budget |
| `paperc/runner.py` | runs policies on E-SYN worlds (P1 rows on recorded instances); tunes every rung on dev; evaluates rungs and references on paired test campaigns; writes the ladder table |
| `esyn/sim.py` | stochastic policies: per-decision uniforms keyed by the logged `eps_seed` (60002), replayed by `check_campaign`; logged `policy_sha`; a richer `trace` |
| `esyn/dp.py` | `solve_law`: the knapsack recursion for any discrete V\* law |
| `schema.py` | a randomised row (0 < action_prob < 1) must carry `eps_seed` |
| `seeds.py` | claims key 60002 and the index ranges of P3 and P4 under the E-SYN root key (unique claim values, tested) |

**Design (plan §7.0):**
- **One belief for every rung.** Every rung reads the same forecasts: the world's A2-U keyed belief (V\*, τ, m̂).
  It may also read decision-time features that are not forecaster inputs (budget position, slots).
  - **Keep decision.** No rung's keep decision reads the raw increment, which would refit the belief's shrinkage.
    The exception is N0, the declared floor.
  - **Verify epoch.** SPRT and racing read the mean increment there as their test statistic.
  - **Belief-refit references.** Two reference rows measure the effect of refitting the belief:
    - `ShrinkRefit`: a tuned static rule keeping on a + min(λk, 1)(Δ̂ − a); λ = 1 is the belief's m̂;
    - `RawKeep`: its no-shrinkage corner, keeping on Δ̂.
- **Equal tuning budget.** Every tuned rung runs the same procedure under the same cap of 80 candidates, counted per
  rung, on the same 1,000 dev campaigns:
  - first the same coarse static grid, charged to each rung;
  - then coordinate search from the best coarse static, until the cap or the minimum step is reached.

  A move is accepted only if its paired dev improvement exceeds one standard error. This does not stop every noise
  move: in the strict null, N1 and N3 still move off the Bayes rule (§3.1). No rung starts from N1's tuned point.
  N2b's head weights and N4's law are fitted on the same dev campaigns (dev fits).
- **N3 centring** (Track S's convention). The centres are the mean budget position and τ of the reference static's
  eligible E1 dev decisions, and the mean budget position of its eligible E2 decisions. The reference static is the
  best coarse static, the common start, standing in for Track S's tuned m\*. The centres are stored per world.
- **Test.** 10,000 campaigns, paired across all rows, never used for tuning; tuning is instrumented in a test. The
  table also gives each tuned row's dev gain over N1 with its standard error, so selection optimism can be read
  (dev gain minus test gain).
- **Gaps to the oracle.** Paired differences against the P3 oracle member. That member is a family-best lower bound
  (exact only in the budget world), so a rung can beat it.
- **Multiplicity.** The table holds about 150 intervals without correction, so single intervals near the margin
  should not be over-read.

## 2. Tables (test block; ± 95 % half-width of the paired difference)

"Charged" is the number of candidate policies charged to the row's tuning. Full policy parameters and N3's centres
are in the JSON.

#### strict_null

| Row | Kind | Mean runs | Gain over N1 ± 95 % hw | Gap to oracle ± 95 % hw | Dev gain over N1 (se) | Charged |
|---|---|---|---|---|---|---|
| N0 | rung | 18.5 | -0.00010 ± 0.00006 | +0.00010 ± 0.00006 | -0.00014 (0.00010) | — |
| N1 | rung | 18.5 | +0.00000 ± 0.00000 | -0.00000 ± 0.00002 | +0.00000 (0.00000) | 48 |
| N2 | rung | 18.5 | -0.00000 ± 0.00002 | -0.00000 ± 0.00000 | -0.00007 (0.00003) | 12 |
| N2b | rung | 18.5 | -0.00001 ± 0.00003 | +0.00001 ± 0.00002 | -0.00006 (0.00004) | 21 |
| N3 | rung | 18.5 | -0.00007 ± 0.00004 | +0.00007 ± 0.00004 | +0.00000 (0.00007) | 80 |
| N4 | rung | 18.5 | -0.00000 ± 0.00002 | -0.00000 ± 0.00000 | -0.00007 (0.00003) | — |
| margin | rung | 18.5 | +0.00000 ± 0.00000 | -0.00000 ± 0.00002 | +0.00000 (0.00000) | 61 |
| shrink | reference | 18.5 | +0.00001 ± 0.00002 | -0.00001 ± 0.00003 | -0.00001 (0.00004) | 64 |
| rawkeep | reference | 18.5 | -0.00003 ± 0.00004 | +0.00003 ± 0.00004 | -0.00001 (0.00006) | 51 |
| random_N1 | reference | 18.5 | +0.00000 ± 0.00000 | -0.00000 ± 0.00002 | — | — |
| dp | reference | 18.5 | -0.00000 ± 0.00002 | -0.00000 ± 0.00000 | — | — |
| oracle | reference | 18.5 | -0.00000 ± 0.00002 | +0.00000 ± 0.00000 | — | — |

#### budget

| Row | Kind | Mean runs | Gain over N1 ± 95 % hw | Gap to oracle ± 95 % hw | Dev gain over N1 (se) | Charged |
|---|---|---|---|---|---|---|
| N0 | rung | 8.0 | -0.00267 ± 0.00022 | +0.00490 ± 0.00022 | -0.00332 (0.00036) | — |
| N1 | rung | 4.5 | +0.00000 ± 0.00000 | +0.00223 ± 0.00012 | +0.00000 (0.00000) | 55 |
| N2 | rung | 4.5 | +0.00008 ± 0.00005 | +0.00214 ± 0.00011 | -0.00003 (0.00007) | 18 |
| N2b | rung | 4.5 | +0.00009 ± 0.00005 | +0.00214 ± 0.00011 | -0.00005 (0.00007) | 21 |
| N3 | rung | 7.6 | +0.00224 ± 0.00012 | -0.00002 ± 0.00006 | +0.00189 (0.00019) | 80 |
| N4 | rung | 7.6 | +0.00224 ± 0.00012 | -0.00002 ± 0.00003 | +0.00199 (0.00019) | — |
| margin | rung | 4.5 | +0.00005 ± 0.00002 | +0.00218 ± 0.00012 | +0.00002 (0.00002) | 75 |
| shrink | reference | 4.5 | +0.00003 ± 0.00001 | +0.00220 ± 0.00012 | +0.00001 (0.00002) | 70 |
| rawkeep | reference | 4.5 | +0.00000 ± 0.00000 | +0.00223 ± 0.00012 | +0.00000 (0.00000) | 58 |
| random_N1 | reference | 4.5 | -0.00644 ± 0.00024 | +0.00867 ± 0.00024 | — | — |
| random_N4 | reference | 7.6 | -0.00289 ± 0.00022 | +0.00512 ± 0.00021 | — | — |
| dp | reference | 7.6 | +0.00223 ± 0.00012 | +0.00000 ± 0.00000 | — | — |
| oracle | reference | 7.6 | +0.00223 ± 0.00012 | +0.00000 ± 0.00000 | — | — |

#### interaction

| Row | Kind | Mean runs | Gain over N1 ± 95 % hw | Gap to oracle ± 95 % hw | Dev gain over N1 (se) | Charged |
|---|---|---|---|---|---|---|
| N0 | rung | 18.6 | -0.00144 ± 0.00015 | +0.00254 ± 0.00015 | -0.00154 (0.00024) | — |
| N1 | rung | 18.6 | +0.00000 ± 0.00000 | +0.00110 ± 0.00010 | +0.00000 (0.00000) | 48 |
| N2 | rung | 18.6 | -0.00015 ± 0.00007 | +0.00126 ± 0.00009 | -0.00019 (0.00010) | 12 |
| N2b | rung | 18.6 | -0.00003 ± 0.00006 | +0.00114 ± 0.00010 | -0.00006 (0.00010) | 21 |
| N3 | rung | 18.6 | +0.00004 ± 0.00007 | +0.00106 ± 0.00010 | -0.00001 (0.00011) | 80 |
| N4 | rung | 18.6 | -0.00015 ± 0.00007 | +0.00126 ± 0.00009 | -0.00019 (0.00010) | — |
| margin | rung | 18.6 | +0.00000 ± 0.00000 | +0.00110 ± 0.00010 | +0.00000 (0.00000) | 61 |
| shrink | reference | 18.6 | +0.00044 ± 0.00008 | +0.00066 ± 0.00011 | +0.00043 (0.00013) | 65 |
| rawkeep | reference | 18.6 | -0.00143 ± 0.00015 | +0.00254 ± 0.00015 | -0.00154 (0.00024) | 49 |
| random_N1 | reference | 18.6 | -0.00001 ± 0.00001 | +0.00111 ± 0.00010 | — | — |
| oracle | reference | 18.6 | +0.00110 ± 0.00010 | +0.00000 ± 0.00000 | — | — |

#### shared_error

| Row | Kind | Mean runs | Gain over N1 ± 95 % hw | Gap to oracle ± 95 % hw | Dev gain over N1 (se) | Charged |
|---|---|---|---|---|---|---|
| N0 | rung | 18.6 | -0.00127 ± 0.00011 | +0.00348 ± 0.00014 | -0.00163 (0.00018) | — |
| N1 | rung | 18.6 | +0.00000 ± 0.00000 | +0.00221 ± 0.00013 | +0.00000 (0.00000) | 49 |
| N2 | rung | 18.6 | -0.00231 ± 0.00013 | +0.00452 ± 0.00015 | -0.00264 (0.00022) | 12 |
| N2b | rung | 16.2 | -0.00085 ± 0.00013 | +0.00306 ± 0.00014 | -0.00106 (0.00021) | 21 |
| N3 | rung | 18.6 | +0.00010 ± 0.00007 | +0.00211 ± 0.00013 | +0.00003 (0.00011) | 80 |
| N4 | rung | 18.6 | -0.00231 ± 0.00013 | +0.00452 ± 0.00015 | -0.00264 (0.00022) | — |
| margin | rung | 18.6 | +0.00000 ± 0.00000 | +0.00221 ± 0.00013 | +0.00000 (0.00000) | 62 |
| shrink | reference | 18.6 | +0.00006 ± 0.00004 | +0.00215 ± 0.00013 | -0.00002 (0.00008) | 67 |
| rawkeep | reference | 18.6 | +0.00058 ± 0.00010 | +0.00163 ± 0.00012 | +0.00056 (0.00017) | 52 |
| random_N1 | reference | 18.6 | -0.00000 ± 0.00000 | +0.00221 ± 0.00013 | — | — |
| oracle | reference | 32.7 | +0.00221 ± 0.00013 | +0.00000 ± 0.00000 | — | — |

#### eval_allocation

| Row | Kind | Mean runs | Gain over N1 ± 95 % hw | Gap to oracle ± 95 % hw | Dev gain over N1 (se) | Charged |
|---|---|---|---|---|---|---|
| N0 | rung | 18.5 | -0.00131 ± 0.00012 | +0.00497 ± 0.00016 | -0.00138 (0.00019) | — |
| N1 | rung | 18.5 | +0.00000 ± 0.00000 | +0.00366 ± 0.00014 | +0.00000 (0.00000) | 48 |
| N2 | rung | 18.5 | -0.00236 ± 0.00014 | +0.00602 ± 0.00017 | -0.00245 (0.00022) | 12 |
| N2b | rung | 18.5 | -0.00114 ± 0.00012 | +0.00480 ± 0.00015 | -0.00117 (0.00020) | 21 |
| N3 | rung | 18.5 | +0.00000 ± 0.00000 | +0.00366 ± 0.00014 | +0.00000 (0.00000) | 80 |
| N4 | rung | 18.5 | -0.00236 ± 0.00014 | +0.00602 ± 0.00017 | -0.00245 (0.00022) | — |
| margin | rung | 18.5 | +0.00000 ± 0.00000 | +0.00366 ± 0.00014 | +0.00000 (0.00000) | 61 |
| sprt | rung | 33.3 | +0.00247 ± 0.00015 | +0.00119 ± 0.00014 | +0.00251 (0.00023) | 80 |
| race | rung | 33.3 | +0.00247 ± 0.00014 | +0.00120 ± 0.00013 | +0.00243 (0.00023) | 62 |
| kg | rung | 29.0 | +0.00242 ± 0.00013 | +0.00124 ± 0.00013 | +0.00244 (0.00021) | 64 |
| shrink | reference | 18.5 | +0.00000 ± 0.00000 | +0.00366 ± 0.00014 | +0.00000 (0.00000) | 61 |
| rawkeep | reference | 18.5 | +0.00052 ± 0.00010 | +0.00314 ± 0.00014 | +0.00039 (0.00016) | 52 |
| random_N1 | reference | 18.5 | +0.00000 ± 0.00000 | +0.00366 ± 0.00014 | — | — |
| oracle | reference | 34.6 | +0.00366 ± 0.00014 | +0.00000 ± 0.00000 | — | — |

#### information

| Row | Kind | Mean runs | Gain over N1 ± 95 % hw | Gap to oracle ± 95 % hw | Dev gain over N1 (se) | Charged |
|---|---|---|---|---|---|---|
| N0 | rung | 10.0 | -0.06177 ± 0.00167 | +0.06766 ± 0.00158 | -0.06051 (0.00265) | — |
| N1 | rung | 8.3 | +0.00000 ± 0.00000 | +0.00589 ± 0.00075 | +0.00000 (0.00000) | 53 |
| N2 | rung | 8.3 | +0.00019 ± 0.00015 | +0.00570 ± 0.00075 | -0.00010 (0.00028) | 16 |
| N2b | rung | 8.4 | -0.00013 ± 0.00014 | +0.00602 ± 0.00075 | -0.00027 (0.00027) | 21 |
| N3 | rung | 10.0 | +0.00463 ± 0.00091 | +0.00126 ± 0.00069 | +0.00531 (0.00146) | 80 |
| N4 | rung | 9.1 | +0.00013 ± 0.00046 | +0.00577 ± 0.00081 | -0.00083 (0.00063) | — |
| margin | rung | 8.3 | +0.00000 ± 0.00000 | +0.00589 ± 0.00075 | +0.00000 (0.00000) | 67 |
| shrink | reference | 8.3 | +0.00000 ± 0.00000 | +0.00589 ± 0.00075 | +0.00000 (0.00000) | 67 |
| rawkeep | reference | 8.3 | -0.00605 ± 0.00057 | +0.01194 ± 0.00086 | -0.00508 (0.00093) | 58 |
| random_N1 | reference | 8.3 | -0.06452 ± 0.00184 | +0.07041 ± 0.00175 | — | — |
| oracle | reference | 8.5 | +0.00589 ± 0.00075 | +0.00000 ± 0.00000 | — | — |

#### keep_feedback

| Row | Kind | Mean runs | Gain over N1 ± 95 % hw | Gap to oracle ± 95 % hw | Dev gain over N1 (se) | Charged |
|---|---|---|---|---|---|---|
| N0 | rung | 10.0 | -0.01418 ± 0.00036 | +0.01549 ± 0.00035 | -0.01427 (0.00058) | — |
| N1 | rung | 9.8 | +0.00000 ± 0.00000 | +0.00132 ± 0.00015 | +0.00000 (0.00000) | 57 |
| N2 | rung | 9.7 | -0.01143 ± 0.00030 | +0.01274 ± 0.00031 | -0.01165 (0.00047) | 18 |
| N2b | rung | 9.8 | -0.00418 ± 0.00022 | +0.00549 ± 0.00021 | -0.00373 (0.00034) | 22 |
| N3 | rung | 9.9 | +0.00163 ± 0.00020 | -0.00032 ± 0.00022 | +0.00169 (0.00032) | 80 |
| N4 | rung | 9.6 | -0.01150 ± 0.00037 | +0.01282 ± 0.00038 | -0.01202 (0.00060) | — |
| margin | rung | 9.8 | +0.00111 ± 0.00014 | +0.00020 ± 0.00008 | +0.00121 (0.00023) | 80 |
| shrink | reference | 9.8 | -0.00012 ± 0.00012 | +0.00144 ± 0.00011 | -0.00001 (0.00020) | 76 |
| rawkeep | reference | 9.8 | -0.00050 ± 0.00013 | +0.00182 ± 0.00012 | -0.00039 (0.00021) | 74 |
| random_N1 | reference | 9.8 | -0.01049 ± 0.00037 | +0.01181 ± 0.00036 | — | — |
| oracle | reference | 9.8 | +0.00132 ± 0.00015 | +0.00000 ± 0.00000 | — | — |

## 3. Findings (E-SYN only)

1. **Strict null.** No row beats the exact Bayes rule, the DP, beyond its interval; a test checks every row. N1, N2,
   N4, the margin and the oracle member are within 0.000002 of it. N3 is 0.00007 ± 0.00004 below N1: the one-se move
   rule let its search move on dev noise (dev gain +0.00000).
2. **Budget.**
   - The multi-step rungs reach the exact DP: N3 +0.00224 and N4 +0.00224 over N1, both within ±0.00006 of the DP.
   - N2b, single-step in target and form, does not: +0.00009 ± 0.00005. Its round-2 version, with a budget feature in
     the E1 head and a cut tuned on terminal value, reached +0.0020. The review showed that this came from the dev
     draw: refitted on six dev blocks, the feature's sign flipped, and the gain appeared in only three of them.
   - N2 and the margin tie N1.
3. **Interaction.**
   - No rung gains over N1: N2b −0.00003 ± 0.00006, N3 +0.00004 ± 0.00007.
   - The shrinkage-refit reference gains +0.00044 ± 0.00008 (λ = 1.5), about 40 % of the privileged oracle's +0.00110.
     The belief does not model the interaction term, so trusting the observed increment somewhat more than the belief
     does pays.
   - Fully raw keeping loses (−0.00143).
   - Round 1's N2b gain (+0.0006) was the same belief refit.
4. **Evaluation allocation (B18).** The three sequential-test comparators each recover about two thirds of the oracle
   gain:
   - SPRT +0.00247 ± 0.00015 and racing +0.00247 ± 0.00014 (67 % each);
   - KG verify +0.00242 ± 0.00013 (66 %);
   - all against the oracle's +0.00366.

   They use 29–33 runs, against N1's 18.5. N3 and the margin tie N1.
5. **Shared error.**
   - B18 has no comparator here (no verify epoch), and none re-audits the incumbent, where the oracle's +0.00221 comes
     from.
   - The belief-refit reference `RawKeep` gains +0.00058, by keeping on the raw increment at h = −0.003.
     `ShrinkRefit` stopped at λ = 1.14 (+0.00006): starting from λ = 1 under the one-se move rule, its search did not
     reach the raw corner.
   - N3 gains +0.00010 ± 0.00007.
6. **Winner's-curse compensation in the config worlds.** N1 lowers its keep threshold (h ≈ −0.001). Rows fixed at the
   Bayes threshold (N2, N4) lose about 0.0023 against it. N2b's learned E2 head finds only part of the lowered
   threshold, and loses 0.0009–0.0011.
7. **Information.**
   - N3 with Track S's centring gains +0.00463 ± 0.00091 (round 1, uncentred: +0.00199). Its gap to the oracle
     schedule is +0.00126 ± 0.00069.
   - The review re-tuned the same family from N1's tuned point and without the standard-error move rule, and reached
     +0.0081, beating the P3 oracle member by +0.0024 ± 0.0006. The family can therefore exceed P3's information
     oracle, which is a weak lower bound there. What a search finds depends on its procedure; the equal-budget
     procedure here stops lower.
   - N4 (+0.00013 ± 0.00046) and N2b do not gain.
8. **Keep feedback.**
   - N3 beats the P3 oracle member: gap −0.00032 ± 0.00022, an interval that excludes 0. The margin is just below it
     (gap +0.00020 ± 0.00008).
   - P3's member here is a weak lower bound as well.
   - The Bayes-threshold rows lose about 0.011, because this world rewards keeping liberally (N1: h = −0.0046).
9. **Belief refit** (the better of `ShrinkRefit` and `RawKeep` per world). It helps in three worlds:
   - interaction +0.00044 (partial refit);
   - shared_error +0.00058 and eval_allocation +0.00052 (raw keep, where the shared incumbent error makes m̂'s
     shrinkage too strong).

   It gives nothing elsewhere: the refit rows tie N1 or lose. These gains belong to the belief, not to control.
10. **Floors.**
    - N0 is below N1 in every world.
    - Random execution, matched to N1's realised budget and keeping with N1's threshold:
      - is the worst row in information (−0.065) and the budget world (−0.006);
      - matched to N4 in the budget world, −0.003;
      - in keep feedback (−0.010), N0, N4 and N2 are worse.
    - Where N1 executes everything, its q is near 1 and it ties N1.

## 4. Deviations and choices to review

- **Interface.** `act(obs) -> (action, prob, selected)` with a keyed uniform instead of an rng object (runbook
  amendment, P4).
- **N2b.**
  - Heads on belief outputs only (E1: V\*, τ; E2: m̂), fitted on the world's own dev trace under execute-all with
    the Bayes keep (one measurement per execute).
  - The E1 label is the kept gain under N2b's own E2 head.
  - Labels are the noise-free true increments, more than a real per-proposal audit gives.
  - The head fits are dev fits, not charged candidates. Only the cut is tuned (21–22 candidates, under the same cap;
    N2b is not charged the coarse grid).
- **N4.** The V\* law (20 quantile bins), rule share and first-trial gain are estimated from execute-all dev campaigns
  run with W = llm_cap, so that later proposals are seen. In worlds whose law depends on W (keep feedback through
  runs used / W, and P1's posterior states), the estimate is approximate. The recursion treats proposals as
  independent, which is exact only in the budget world.
- **Budget equality.** It is a cap, not a fixed count: a rung whose steps vanish stops early. N2 uses 12–18
  candidates and N1 48–57; N3 and SPRT use all 80. Each count is in the table.
- **Random reference.**
  - q is calibrated by bisection on the test block's run counts (run counts are not outcomes), to the matched row's
    mean runs.
  - It uses the matched row's keep threshold.
- **B18.**
  - Sequential-test rows exist only in worlds with a verify epoch (eval_allocation); all keep on m̂.
  - OCBA is not implemented; its natural use here would be the final selection among kept configurations.
  - No comparator decides re-audits.
- **Runner versus the runbook's wording.**
  - The tuning and test campaigns are index ranges under the E-SYN root key (claimed), not recorded instance seeds.
  - P1 records are written separately for 3 campaigns per row, all passing `check_campaign`.
  - Y is the exact final value, not the audited terminal value.

## 5. Next

- **P5:** the decision-relevance check (B10).
- **Open from this table:**
  - a re-audit comparator (B18);
  - P3's oracle members for information and keep feedback are weak lower bounds. N3 reaches or exceeds them, so a
    centred dynamic member should be added to P3's families before later phases use those gaps as targets.
