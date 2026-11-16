# Non-RL ladder and sequential-testing comparators on E-SYN (build runbook P4; BUILD_LIST B4 + B18)

**AI-assisted (Claude, chat session, 16 Nov 2026). ENGINEERING_ONLY.** E-SYN results are implementation checks and
method behaviour per channel, never evidence about the real loop (plan §5).

- **Data:** `paperC/esyn/ladder_table_v1.json` (schema `paperc_ladder_table/v1`), produced by
  `python -m paperc.runner` (about 13 minutes on two processes). It stores fingerprints of its own code and of the
  P3 oracle table it reads.
- **Tests:** `paperC/tests/test_ladder_p4.py`, plus the full paperC suite.

## 1. What was built

| Module | Content |
|---|---|
| `paperc/policies.py` | **Interface:** `name`, `version`, `act(obs) -> (action, probability, selected)`. A stochastic policy reads a replayable uniform (`obs["u"]`).<br>**Ladder (plan §7.1):**<ul><li>N0: execute all, keep iff Δ̂ > 0;</li><li>N1: static (g, h), tuned;</li><li>N2: g tuned, keep iff m̂ > 0;</li><li>N2b: single-step learned heads;</li><li>N3: Track S's dynamic family from `a2u.py` @ `fab88fc`;</li><li>N4: knapsack DP on a V\* law estimated on dev.</li></ul>**Reference rows:** the P3 oracle member; random execution at N1's realised budget.<br>**B18 comparators:** SPRT-style verify, racing, knowledge-gradient verify, budget-aware keep margin.<br>Tuning under a declared budget |
| `paperc/runner.py` | runs policies on E-SYN worlds (writing P1 rows on recorded instances); tunes every rung on dev; evaluates on paired test campaigns; writes the ladder table |
| `esyn/sim.py` | stochastic policies: per-decision uniforms from `SeedSequence([60002, world code, i, step])`, logged as `eps_seed`, so `check_campaign` replays them; a richer `trace` for N2b's labels |
| `esyn/dp.py` | `solve_law`: the knapsack recursion for any discrete V\* law (N4) |
| `seeds.py` | claims key 60002 (decision uniforms) and the P4 index ranges (dev 4,000,000 + j, test 5,000,000 + j) |

**Design (plan §7.0):**
- **One belief for every rung:** the world's A2-U keyed forecaster, computed by the simulator and never refitted.
- **Equal tuning budget:** at most 60 candidate policies per tuned rung, each on the same 1,000 dev campaigns. The
  table records each rung's count and its instance range.
- **Test:** 10,000 campaigns, paired across rungs, never used for tuning.
- **Gaps to the oracle:** paired differences against the P3 oracle member on the same test campaigns. That member is
  a family-best lower bound (exact only in the budget world), so a rung can match or beat it.
- **Records:** 3 recorded campaigns per rung and world pass `check_campaign`, with the seed registry and propensity
  replay.

## 2. Gain tables (test block; ± 95 % half-width of the paired difference)

#### strict_null

| Rung | Policy (tuned on dev) | Mean runs | Gain over N1 ± 95 % hw | Gap to oracle ± 95 % hw |
|---|---|---|---|---|
| N0 | `n0` | 18.6 | -0.00005 ± 0.00004 | +0.00010 ± 0.00006 |
| N1 | `static:0,-0.0001875` | 18.6 | +0.00000 ± 0.00000 | +0.00005 ± 0.00005 |
| N2 | `static:0,0` | 18.6 | +0.00005 ± 0.00005 | -0.00000 ± 0.00000 |
| N2b | `n2b:0.01645,1.164,-0.05581,-0.09289,2.276,0.6…` | 18.6 | +0.00004 ± 0.00005 | +0.00000 ± 0.00002 |
| N3 | `n3:0,0,0,-6.25e-05,0,0,0.004,0` | 18.6 | +0.00006 ± 0.00004 | -0.00001 ± 0.00003 |
| N4 | `n4` | 18.6 | +0.00005 ± 0.00005 | -0.00000 ± 0.00000 |
| margin | `margin:0,-0.0001875,0.0005` | 18.6 | +0.00004 ± 0.00004 | +0.00001 ± 0.00003 |
| random | `random:0.999969` | 18.6 | +0.00005 ± 0.00005 | -0.00000 ± 0.00000 |
| oracle | `schedule:0,0,0,0,0.0005,0;0,0,0;0.02` | 18.6 | +0.00005 ± 0.00005 | +0.00000 ± 0.00000 |

#### budget

| Rung | Policy (tuned on dev) | Mean runs | Gain over N1 ± 95 % hw | Gap to oracle ± 95 % hw |
|---|---|---|---|---|
| N0 | `n0` | 8.0 | -0.00275 ± 0.00022 | +0.00490 ± 0.00022 |
| N1 | `static:0.001,-0.000625` | 4.4 | +0.00000 ± 0.00000 | +0.00215 ± 0.00011 |
| N2 | `static:0.001,0` | 4.4 | +0.00001 ± 0.00004 | +0.00214 ± 0.00011 |
| N2b | `n2b:0.01824,1.319,-0.08328,-0.07717,2.127,0.6…` | 4.4 | +0.00001 ± 0.00004 | +0.00214 ± 0.00011 |
| N3 | `n3:0.001,0.002,0.075,-0.000125,-0.0025,0,0.00…` | 7.2 | +0.00205 ± 0.00010 | +0.00010 ± 0.00009 |
| N4 | `n4` | 7.6 | +0.00217 ± 0.00011 | -0.00002 ± 0.00003 |
| margin | `margin:0.001,-0.000625,-0.00025` | 4.4 | -0.00001 ± 0.00001 | +0.00216 ± 0.00012 |
| random | `random:0.207306` | 4.7 | -0.00600 ± 0.00023 | +0.00815 ± 0.00023 |
| oracle | `dp` | 7.6 | +0.00215 ± 0.00011 | +0.00000 ± 0.00000 |

#### interaction

| Rung | Policy (tuned on dev) | Mean runs | Gain over N1 ± 95 % hw | Gap to oracle ± 95 % hw |
|---|---|---|---|---|
| N0 | `n0` | 18.6 | -0.00144 ± 0.00015 | +0.00254 ± 0.00015 |
| N1 | `static:0,-0.00025` | 18.6 | +0.00000 ± 0.00000 | +0.00110 ± 0.00010 |
| N2 | `static:0,0` | 18.6 | -0.00015 ± 0.00007 | +0.00126 ± 0.00009 |
| N2b | `n2b:0.02996,0.4956,0.3127,0.2105,2.848,0.9027…` | 18.6 | +0.00060 ± 0.00009 | +0.00050 ± 0.00011 |
| N3 | `n3:0,0,0,-0.000625,-0.00075,0,0.004,0` | 18.6 | +0.00003 ± 0.00006 | +0.00107 ± 0.00010 |
| N4 | `n4` | 18.6 | -0.00015 ± 0.00007 | +0.00126 ± 0.00009 |
| margin | `margin:0,-0.00025,6.25e-05` | 18.6 | +0.00001 ± 0.00002 | +0.00110 ± 0.00010 |
| random | `random:0.999664` | 18.6 | -0.00016 ± 0.00007 | +0.00126 ± 0.00009 |
| oracle | `interaction:0,0,0.25` | 18.6 | +0.00110 ± 0.00010 | +0.00000 ± 0.00000 |

#### shared_error

| Rung | Policy (tuned on dev) | Mean runs | Gain over N1 ± 95 % hw | Gap to oracle ± 95 % hw |
|---|---|---|---|---|
| N0 | `n0` | 18.5 | -0.00127 ± 0.00011 | +0.00348 ± 0.00014 |
| N1 | `static:0,-0.000875` | 18.5 | +0.00000 ± 0.00000 | +0.00221 ± 0.00013 |
| N2 | `static:0,0` | 18.5 | -0.00231 ± 0.00013 | +0.00452 ± 0.00015 |
| N2b | `n2b:0.02979,1.537,-0.1784,1.092,1.239,1.214,-…` | 18.5 | +0.00013 ± 0.00012 | +0.00208 ± 0.00013 |
| N3 | `n3:0,0,0,-0.000875,0.000125,0,0.004,0` | 18.5 | +0.00001 ± 0.00003 | +0.00220 ± 0.00013 |
| N4 | `n4` | 18.5 | -0.00231 ± 0.00013 | +0.00452 ± 0.00015 |
| margin | `margin:0,-0.000875,-0.00025` | 18.5 | +0.00001 ± 0.00003 | +0.00220 ± 0.00013 |
| sprt | `sprt:0,-0.003,0.0033,0.1,3` | 18.5 | +0.00058 ± 0.00010 | +0.00163 ± 0.00012 |
| race | `race:0,-0.003,1,3` | 18.5 | +0.00058 ± 0.00010 | +0.00163 ± 0.00012 |
| kg | `kg:0,-0.000875,0.0001,3` | 18.5 | +0.00000 ± 0.00000 | +0.00221 ± 0.00013 |
| random | `random:0.999908` | 18.5 | -0.00231 ± 0.00013 | +0.00452 ± 0.00015 |
| oracle | `evalloc:0,0,0,1,3,incumbent` | 32.3 | +0.00221 ± 0.00013 | +0.00000 ± 0.00000 |

#### eval_allocation

| Rung | Policy (tuned on dev) | Mean runs | Gain over N1 ± 95 % hw | Gap to oracle ± 95 % hw |
|---|---|---|---|---|
| N0 | `n0` | 18.4 | -0.00130 ± 0.00012 | +0.00497 ± 0.00016 |
| N1 | `static:0,-0.00096875` | 18.4 | +0.00000 ± 0.00000 | +0.00367 ± 0.00014 |
| N2 | `static:0,0` | 18.4 | -0.00235 ± 0.00014 | +0.00602 ± 0.00017 |
| N2b | `n2b:0.1029,2.123,-0.3867,1.088,1.325,1.176,-0…` | 18.4 | +0.00010 ± 0.00011 | +0.00357 ± 0.00014 |
| N3 | `n3:0,0,0,-0.00096875,0,0,0.004,0` | 18.4 | +0.00000 ± 0.00000 | +0.00367 ± 0.00014 |
| N4 | `n4` | 18.4 | -0.00235 ± 0.00014 | +0.00602 ± 0.00017 |
| margin | `margin:0,-0.00096875,-6.25e-05` | 18.4 | +0.00002 ± 0.00002 | +0.00365 ± 0.00014 |
| sprt | `sprt:0.000375,-0.00146875,0.0037125,0.0875,3` | 35.6 | +0.00171 ± 0.00017 | +0.00196 ± 0.00015 |
| race | `race:0,-0.00321875,0.75,3` | 31.1 | +0.00267 ± 0.00013 | +0.00100 ± 0.00013 |
| kg | `kg:0,-0.00146875,2.5e-05,3` | 31.4 | +0.00251 ± 0.00013 | +0.00116 ± 0.00013 |
| random | `random:0.999969` | 18.4 | -0.00235 ± 0.00014 | +0.00602 ± 0.00017 |
| oracle | `evalloc:0,-0.001,0.25,3,2,incumbent` | 34.5 | +0.00367 ± 0.00014 | +0.00000 ± 0.00000 |

#### information

| Rung | Policy (tuned on dev) | Mean runs | Gain over N1 ± 95 % hw | Gap to oracle ± 95 % hw |
|---|---|---|---|---|
| N0 | `n0` | 10.0 | -0.06191 ± 0.00167 | +0.06766 ± 0.00158 |
| N1 | `static:0.0018125,0.00025` | 8.3 | +0.00000 ± 0.00000 | +0.00575 ± 0.00075 |
| N2 | `static:0.0018125,0` | 8.3 | +0.00005 ± 0.00007 | +0.00570 ± 0.00075 |
| N2b | `n2b:0.007168,1.003,-0.004709,-0.01874,1.517,0…` | 8.0 | -0.00016 ± 0.00018 | +0.00591 ± 0.00075 |
| N3 | `n3:0.0015625,0.004,0,0.0005,0,0,0.004,0` | 9.3 | +0.00199 ± 0.00025 | +0.00376 ± 0.00075 |
| N4 | `n4` | 9.1 | -0.00002 ± 0.00045 | +0.00577 ± 0.00081 |
| margin | `margin:0.0018125,0.00021875,0` | 8.3 | +0.00001 ± 0.00003 | +0.00574 ± 0.00075 |
| random | `random:0.345367` | 8.2 | -0.06496 ± 0.00185 | +0.07071 ± 0.00175 |
| oracle | `schedule:0,0.0015,0.003,0.0005,0.002,0.005;0,…` | 8.6 | +0.00575 ± 0.00075 | +0.00000 ± 0.00000 |

#### keep_feedback

| Rung | Policy (tuned on dev) | Mean runs | Gain over N1 ± 95 % hw | Gap to oracle ± 95 % hw |
|---|---|---|---|---|
| N0 | `n0` | 10.0 | -0.01406 ± 0.00035 | +0.01549 ± 0.00035 |
| N1 | `static:0.0005,-0.00575` | 9.8 | +0.00000 ± 0.00000 | +0.00144 ± 0.00011 |
| N2 | `static:0.0005625,0` | 9.7 | -0.01131 ± 0.00031 | +0.01274 ± 0.00031 |
| N2b | `n2b:-0.8292,-4.248,3.322,1.903,3.264,0.7309,0…` | 10.0 | -0.00496 ± 0.00028 | +0.00640 ± 0.00027 |
| N3 | `n3:0.0005,0.00125,-0.0625,-0.00575,0,0,0.004,0` | 9.9 | +0.00165 ± 0.00020 | -0.00021 ± 0.00022 |
| N4 | `n4` | 9.6 | -0.01138 ± 0.00038 | +0.01282 ± 0.00038 |
| margin | `margin:0.0005,-0.00825,0.007` | 9.8 | +0.00124 ± 0.00009 | +0.00020 ± 0.00008 |
| random | `random:0.710541` | 9.9 | -0.02035 ± 0.00040 | +0.02178 ± 0.00040 |
| oracle | `dynamic:0.0005,0,0,0,0.016,0,inf` | 9.8 | +0.00144 ± 0.00011 | +0.00000 ± 0.00000 |


**Column meanings:**
- **Mean runs:** the average runs used over the first 1,000 test campaigns.
- **Policy:** names are truncated where long; the full parameters are in the JSON.
- **Oracle:** the oracle row is the P3 certified member, re-evaluated on this test block.

## 3. Findings (E-SYN only)

1. **Strict null.** No rung beats N1 by more than +0.00006 (within its interval), and N2 is exactly the DP policy
   (test). N1's dev tuning chose h = −0.00019, a hair below the Bayes threshold. This costs 0.00005 against N2 and is
   the tuning noise of a 60-candidate search on 1,000 campaigns.
2. **Budget.** The multi-step rungs recover the oracle gain:
   - N4 (DP on a law estimated on dev): +0.00217, gap −0.00002 ± 0.00003;
   - N3 (Track S's dynamic thresholds): +0.00205, gap +0.00010 ± 0.00009.

   The single-step rungs (N2, N2b) and the budget-aware keep margin tie N1. N4 also matches the exact DP within 5 %
   of the DP gain (test).
3. **Interaction.** Only N2b gains: +0.00060 ± 0.00009, about half of the privileged oracle's +0.00110. On E-SYN, a
   learned single-step head captures part of the interaction gain, and the threshold rules (N3, margin) capture
   none. Why the head gains is not analysed here.
4. **Config worlds** (shared incumbent error, evaluation allocation).
   - **Winner's-curse compensation.** N1 compensates with a lowered keep threshold (h ≈ −0.0009). Rules fixed at the
     Bayes threshold (N2, N4, random) lose 0.0023 against it.
   - **eval_allocation:** the B18 comparators recover most of the oracle gain. Racing gets +0.00267, knowledge-gradient
     verify +0.00251 and SPRT +0.00171, against the oracle's +0.00367. All of them use about 31–36 runs, against
     N1's 18.
   - **shared_error:**
     - no verify is offered, and none of the comparators re-audits the incumbent, which is where the oracle's
       +0.00221 comes from;
     - SPRT and racing gain +0.00058 there by keeping on the raw increment at h = −0.003;
     - KG verify equals N1.
   - **Gap:** a re-audit-aware comparator is missing (§4).
5. **Information.** N3 gains +0.00199 ± 0.00025, about a third of the oracle schedule's +0.00575. Its tuned budget
   slope (b_budget = 0.004) makes its execute threshold depend on the budget position. N4's knapsack DP also depends
   on the budget position, but it treats proposals as independent, and it does not gain (−0.00002 ± 0.00045).
6. **Keep feedback.** N3 (+0.00165) and the budget-aware margin (+0.00124) match the P3 oracle member (+0.00144); N3's
   gap is −0.00021 ± 0.00022. The oracle is a family-best lower bound, and N3 reaches it. The Bayes-threshold rungs
   lose about 0.011, because this world rewards keeping liberally (N1: h = −0.00575).
7. **Floors.**
   - N0 (execute all, keep on Δ̂ > 0) is below N1 in every world.
   - Random execution at N1's realised budget is the worst rung where E1 selection matters: information −0.065,
     keep feedback −0.020, budget −0.006.
   - Where N1 executes everything, the random rung's q ends near 1, so it equals execute-all with the Bayes keep.

## 4. Deviations and choices to review

- **N1 tuning and the P3 caveat.** N1 is tuned by a coarse grid followed by coordinate refinement with step halving.
  This addresses P3's coarse-grid caveat (P3 review R2-2) for the P4 baseline. In information, N1 =
  `static:0.0018125,0.00025`, better than P3's `static:0.0015,0.001`, so the oracle gap there (0.00575) is smaller
  than P3's oracle gain (0.00643).
- **N2b.**
  - The E1 head is a least-squares regression of the immediate kept gain on (V\*, τ), with its cut tuned on dev.
  - The E2 head is a cost-sensitive logistic regression on (m̂, Δ̂).
  - Labels come from execute-all dev campaigns run with W = llm_cap. In keep_feedback, whose feedback depends on
    runs used / W, these labels are a poor guide, and N2b loses 0.005.
- **N4.** The V\* law, rule share and first-trial gain are estimated from the same execute-all dev campaigns (20
  quantile bins). The recursion treats proposals as independent; that is exact only in the budget world.
- **N3 port.** Track S's budget gap r = runs_left / W − proposals_left / llm_cap. At E2, the current proposal is
  counted as left, mirroring its E1 definition. The centres r̄1 = r̄2 = 0 and τ̄ = 0.004 are fixed; five slopes and
  levels are tuned.
- **B18.**
  - OCBA is not implemented: for one candidate against one incumbent, it allocates measurements between the two, and
    the simulator offers incumbent re-measurement only after a keep.
  - No comparator decides re-audits.
  - SPRT and racing keep on the raw mean increment; KG and the margin keep on m̂.
- **Random reference.** q is fitted by 14 bisection steps on dev so that its mean runs match N1's. These count against
  its tuning budget.
- **Seeds.** Dev and test blocks are index ranges under the E-SYN root key 60001, claimed in the registry. Records use
  instances 0–2 per rung (instance seeds 50000 + i).

## 5. Next

- **P5:** the decision-relevance check (B10).
- **Open from this table:** a re-audit-aware comparator (B18), and the information schedule's remaining gap for
  the learned rungs (P7/P8).
